"""Rules on measured structure (mech/structure_rules.py): at their templates the rules reproduce the ledger's
per-element values exactly (neutral equivalence, the whole brain's point processes and sections), each rule moves
the values it should when its parameter moves, and a residual acts on its one element. NEURON is one simulator per
process, so each brain runs in a subprocess."""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from bioemu import ledger
from wormemu.brain import MODEL
from wormemu.brain_structure import cengen_class, load_structure
from wormemu.mech import channels
from wormemu.mech import structure_rules as R

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = '''
import json, sys
import pandas as pd
from wormemu.brain import Brain, sample_worm
toggles, extra = json.loads(sys.argv[1]), json.loads(sys.argv[2])
spec = sample_worm(None)
for k, v in extra.items():
    spec.values[k] = pd.Series(v) if isinstance(v, dict) else v
b = Brain(spec, toggles=toggles)
h = b.h
pp = []
for p in b.conn:
    seg = p.get_segment()
    pp.append([p.hname().split("[")[0], seg.sec.name(), round(seg.x, 4)] +
              [float(getattr(p, q)) if hasattr(p, q) else None for q in ("gmax", "weight", "erev", "mode")])
sec = []
for c in b.cells:
    for s in c.all:
        sec.append([s.name(), s.cm, s(0.5).pas.e] + [getattr(s(0.5), ch).gbar if h.ismembrane(ch, sec=s) else None
                                                    for ch in ("kqt1", "unc103", "exp2", "slo1iso", "slo2iso")])
print(json.dumps(dict(pp=pp, sec=sec, placed=dict(b.placed))))
'''


def _build(toggles, extra=None):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(toggles), json.dumps(extra or {})],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _num(rows, k):
    return np.array([np.nan if r[k] is None else r[k] for r in rows], float)


def test_templates_match_the_ledger():
    led = ledger.load(MODEL)
    P = led.parameters.set_index("param_id")
    assert math.isclose(P.loc["syn_strength_per_pair", "value_template"], R.G_CONTACT_NS)
    assert math.isclose(P.loc["nmj_strength_per_pair", "value_template"], R.G_CONTACT_NS)
    assert math.isclose(P.loc["rec_lacr_gamma_pS", "value_template"], R.GAMMA_LACR_PS)
    assert math.isclose(R.N_TEMPLATE * R.GAMMA_LACR_PS / 1000.0, R.G_CONTACT_NS)
    assert math.isclose(P.loc["gap_innexin_unitary", "value_template"], R.GAP_UNITARY_PS)
    # each per-element row the rules replace holds one value today (the rule's template) on its guessed elements
    for pid, x in (("syn_strength_per_pair", R.G_CONTACT_NS), ("nmj_strength_per_pair", R.G_CONTACT_NS),
                   ("pas_soma_cm", 1.5), ("pas_neurite_cm", 1.5), ("pas_soma_epas", -45.0),
                   ("pas_neurite_epas", -45.0)):
        t = led.values(pid)
        g = t[t.label == "guessed"]
        assert len(g) and np.allclose(g.value, x), pid
    # the unfit-leak cells are exactly BAAIWorm's cells above the range (the table's guessed elements)
    t = led.values("pas_soma_epas")
    st = load_structure()
    from wormemu.brain import BAAI
    raw = {n: json.loads((BAAI / "cell_param" / f"{n}.json").read_text())["soma"]["epas"] for n in t.element}
    assert {n for n, v in raw.items() if v > R.UNFIT_EPAS_ABOVE_MV} == set(t.element[t.label == "guessed"])
    # the innexins are build_ledger's INX
    assert set(R.INNEXINS) == {g for g in st.genes if g in ("unc-7", "unc-9", "eat-5") or g.startswith("inx-")}


def test_sign_rule_reproduces_the_table():
    st = load_structure()
    led = ledger.load(MODEL)
    t = led.values("syn_sign_receptor")
    cls = set(st.cengen_classes)
    g = t[t.rule.isin(["cengen", "transmitter"])]
    assert len(g) == (t.label == "guessed").sum() == 1997
    for e, v, rule in zip(g.element, g.value, g.rule):
        a, b = e.split(">")
        assert R.receptor_sign(st, a, cengen_class(b, cls), 1.0) == (int(v), rule), e
    # the ratio moves the CeNGEN-signed pairs only
    pairs = [e.split(">") for e in g.element]
    flips = sum(R.receptor_sign(st, a, cengen_class(b, cls), 4.0)[0] != int(v) for (a, b), v in zip(pairs, g.value))
    assert flips > 0


def test_density_rule_at_template_is_the_spec():
    st = load_structure()
    rep = R.dens_replaced()
    assert len(rep) == 189
    for pid in rep:
        _, ch, cls = pid.split("_", 2)
        s = channels.DENSITY[pid]
        gene = channels.CHANNELS[ch]
        g = R.nic_density(R.P0, ch, s.template, st.expr(gene, cls), R.tpm_ref(st, gene))
        assert math.isclose(g, s.template), pid
    # the slope makes it follow expression
    p = dict(R.P0, dens_map_tpm_slope=1.0)
    hi = R.nic_density(p, "kqt1", 1.0, 1000.0, 10.0)
    lo = R.nic_density(p, "kqt1", 1.0, 1.0, 10.0)
    assert hi > 1.0 > lo


def test_gap_unitary_rule():
    p = dict(R.P0)
    assert math.isclose(R.gap_unitary_pS(p, {"unc-7": 5.0}, {"unc-9": 3.0, "inx-1": 1.0}), R.GAP_UNITARY_PS)
    assert math.isclose(R.gap_unitary_pS(p, None, None), R.GAP_UNITARY_PS)
    p["gap_unitary_unc_7_pS"] = 4 * R.GAP_UNITARY_PS
    # a homotypic UNC-7 junction 4x; heterotypic UNC-7/UNC-9 the geometric mean, 2x
    assert math.isclose(R.gap_unitary_pS(p, {"unc-7": 1.0}, {"unc-7": 1.0}), 4 * R.GAP_UNITARY_PS)
    assert math.isclose(R.gap_unitary_pS(p, {"unc-7": 1.0}, {"unc-9": 1.0}), 2 * R.GAP_UNITARY_PS)


def test_whole_brain_rules_on_equals_off():
    """Neutral equivalence on the whole brain: every point process and every section the same with the rules on."""
    on, off = _build({"structure_rules": "on"}), _build({"structure_rules": "off"})
    assert on["placed"] == off["placed"]
    assert [r[:3] for r in on["pp"]] == [r[:3] for r in off["pp"]]
    for k in range(3, 7):
        a, b = _num(on["pp"], k), _num(off["pp"], k)
        assert np.array_equal(np.isnan(a), np.isnan(b))
        assert np.allclose(a[~np.isnan(a)], b[~np.isnan(b)], rtol=1e-12, atol=0)
    for k in range(1, 8):
        a, b = _num(on["sec"], k), _num(off["sec"], k)
        assert np.array_equal(np.isnan(a), np.isnan(b))
        assert np.allclose(a[~np.isnan(a)], b[~np.isnan(b)], rtol=1e-12, atol=0)


def test_rules_and_residuals_act():
    """Moving a rule parameter moves its whole class; a residual moves its one element."""
    base = _build({})
    led = ledger.load(MODEL)
    pair = led.values("syn_strength_per_pair").element.iloc[0]
    moved = _build({}, {"syn_nchan_per_em_lacr": 2 * R.N_TEMPLATE, "pas_cm_uF_cm2": 1.0,
                        "res_gap_pair": {led.values("gap_strength_per_pair").element.iloc[0]: math.log(3.0)},
                        "res_syn_pair": {pair: math.log(5.0)}})
    assert [r[:3] for r in base["pp"]] == [r[:3] for r in moved["pp"]]
    g0, g1 = _num(base["pp"], 3), _num(moved["pp"], 3)
    ratio = g1 / g0
    ratio = ratio[np.isfinite(ratio)]
    assert np.isclose(ratio, 2.0).sum() > 100           # the L-AChR sites doubled
    assert np.isclose(ratio, 5.0).sum() + np.isclose(ratio, 10.0).sum() >= 1      # the one pair's residual
    assert np.isclose(ratio, 1.0).sum() > 100           # the other classes unchanged
    w0, w1 = _num(base["pp"], 4), _num(moved["pp"], 4)
    r = w1 / w0
    r = r[np.isfinite(r)]
    assert np.isclose(r, 3.0).sum() >= 2 and np.isclose(r, 1.0).sum() > 100    # one gap pair (both halves)
    cm0, cm1 = _num(base["sec"], 1), _num(moved["sec"], 1)
    assert np.isclose(cm1[np.isclose(cm0, 1.5)], 1.0).all()
