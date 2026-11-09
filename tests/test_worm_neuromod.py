"""Rows 9, 10, 28 (mech/neuromod.py): the lumped form is brain_layers' old layer exactly (neutral equivalence), the
compartment form runs inside the brain and scales conductances, and the module's unit checks hold. NEURON is one
simulator per process, so each brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from wormemu.brain_structure import load_structure
from wormemu.mech import neuromod as N

ROOT = Path(__file__).resolve().parents[1]
CELLS = ["AVAL", "AVAR", "AVBL", "ASHL", "RIS", "ALA", "NSML", "ADFL", "CEPDL", "RIML", "RICL", "PVCL", "DA01",
         "VB01", "dBWML6"]

SCRIPT = '''
import json, sys, numpy as np
from wormemu import mech
cells, toggles, reg = json.loads(sys.argv[1]), json.loads(sys.argv[2]), json.loads(sys.argv[3])
mech.REGISTRY[:] = reg
from wormemu.brain import Brain
b = Brain(toggles=toggles, cells=cells)
b.reset()
for c, a in (("AVBL", 40.0), ("ASHL", 30.0), ("RIS", 10.0), ("CEPDL", 10.0)):
    b.extra_pA[b.idx[c]] = a
V = []
for k in range(300):
    V.append(b.step().v_mV)
nm = b.mech_out.get("neuromod", {})
print(json.dumps(dict(V=np.array(V).tolist(), mechs=[type(m).__module__ for m in b.mechs], neuromod=nm,
                 noise=b.mech_out.get("quantal_noise", {}), chnoise=b.mech_out.get("channel_noise", {}))))
'''


def _run(toggles, reg=("receptors", "neuromod")):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(CELLS), json.dumps(toggles), json.dumps(list(reg))],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_lumped_is_old_layer():
    old = _run(dict(peptides="on", monoamines="on"), reg=("receptors",))
    none = _run(dict(peptides="off", monoamines="off"), reg=("receptors",))
    new = _run(dict(peptides="lumped", monoamines="lumped"))
    V, V0, V1 = (np.array(x["V"]) for x in (old, none, new))
    assert np.abs(V - V0).max() > 1e-6                     # the old layer does something here
    assert np.abs(V - V1).max() < 1e-9                     # and the lumped form is it
    assert "wormemu.mech.neuromod" in new["mechs"] and new["neuromod"] == {}


def test_compartments_run_in_brain():
    for f in ("compartments", "well_mixed"):
        r = _run(dict(peptides=f, monoamines=f))
        V = np.array(r["V"])
        assert np.isfinite(V).all() and np.abs(V).max() < 200
        nm = r["neuromod"]
        assert nm["pep_total_molecules"] > 0 and nm["ma_serotonin_max_nM"] > 0 and nm["pep_n_receptor_sites"] > 0
        assert np.isfinite(list(nm.values())).all()


def test_tables():
    st = load_structure()
    assert len(N.PAIRS) == 147 and len(N.PRECURSORS) == 53
    for s in N.SPECS:
        assert s.lo <= s.template <= s.hi, s.id
        assert s.label in ("measured", "derived", "inferred", "guessed", "published_fit"), s.id
    for rg, (f, _, label, _) in N.GPCR_COUPLING.items():
        assert f in "qisu" and label in ("measured", "inferred", "guessed"), rg
    assert all(g in st.gene_index for g in N.G_ALPHA + tuple(N.TRANSPORTERS.values()))
    assert st.expr("dmsr-1", "RIS") == 0 and ("RIS", "dmsr-1") in N.EXPR_ADD      # the added autoreceptor
    assert N.form("on") == "compartments" and N.form(False) == "off"


def test_unit_checks():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "worm" / "neuromod_unit_check.py")],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    res = json.loads(r.stdout[r.stdout.index("{"):])
    for k in ("code_checks", "bolus", "limit_well_mixed"):
        assert res[k]["passed"], (k, res[k])
    w = res["ris_self_limit"]                              # reported; the feedback itself is asserted
    assert w["with"]["flp11_head_nM_end"] < w["without"]["flp11_head_nM_end"] and w["with"]["ris_gi"] > 0.1


SITE = '''
import json, sys, numpy as np
from wormemu import mech
cells, toggles = json.loads(sys.argv[1]), json.loads(sys.argv[2])
mech.REGISTRY[:] = ["receptors", "neuromod"]
from wormemu.brain import Brain
b = Brain(toggles=toggles, cells=cells)
nm = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.neuromod")
b.reset()
b.extra_pA[b.idx[cells[0]]] = 30.0
V = [b.step().v_mV for k in range(200)]
print(json.dumps(dict(W=nm.pep_W.tolist(), Wa=nm.ma_W.tolist(), comp=nm.pep_comp.tolist(), V=np.array(V).tolist(),
                 names=list(b.cell_names), named=nm.pep.named.tolist())))
'''


def _site(cells, site, grid="four"):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    tg = dict(peptides="compartments", monoamines="compartments", neuromod_site=site, pc_grid=grid)
    r = subprocess.run([sys.executable, "-c", SITE, json.dumps(cells), json.dumps(tg)], capture_output=True, text=True,
                       env=env, cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_site_weights():
    """neuromod_site: the soma form is one-hot on the soma's compartment; the membrane form's rows are area shares
    (sum 1); a brain whose cells each lie inside one compartment is the same under both (limit test). On the four
    named compartments (the limit test needs them); under pc_grid=bins (the default) the bin weights regrouped by named
    compartment are the four's."""
    cells = ["AVL", "DVB", "ASHL", "CEPDL", "RIML", "ADFL"]
    soma, memb = _site(cells, "soma"), _site(cells, "membrane")
    Ws, Wm = np.array(soma["W"]), np.array(memb["W"])
    assert (Ws == np.eye(4)[soma["comp"]]).all() and (np.array(soma["Wa"]) == Ws).all()
    assert np.allclose(Wm.sum(1), 1.0) and (Wm >= 0).all() and np.allclose(memb["Wa"], Wm)
    names = memb["names"]                                          # the brain's own cell order
    avl, dvb = names.index("AVL"), names.index("DVB")
    assert soma["comp"][avl] == 0 and Wm[avl, 0] < 0.5              # AVL: head soma, most membrane behind it
    assert soma["comp"][dvb] == 3 and Wm[dvb, 2] > 0.5              # DVB: tail soma, most membrane in the body
    head = [c for c in cells if c not in ("AVL", "DVB")]
    assert all(Wm[names.index(c), 0] == 1.0 for c in head)
    a, b = _site(head, "soma"), _site(head, "membrane")
    assert np.array_equal(np.array(a["V"]), np.array(b["V"]))
    fine = _site(cells, "membrane", "bins")
    Wb = np.array(fine["W"])
    assert Wb.shape[1] > 50 and np.allclose(Wb.sum(1), 1.0) and fine["names"] == names
    assert np.allclose(Wb @ np.eye(4)[fine["named"]], Wm, atol=1e-12)


def test_aex2_ec50_source():
    """aex2_ec50_source: the default reads Beets 2023's NLP-40 EC50 on AEX-2; wang2013 changes only those entries."""
    from types import SimpleNamespace
    st = load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    brain = SimpleNamespace(st=st, cell_names=neurons, is_muscle=np.zeros(len(neurons), bool),
                            spec=SimpleNamespace(values={}), layers=None)
    T = {s.id: s.template for s in N.SPECS}
    tg = {"peptides": "compartments", "monoamines": "off"}
    a = N.Mech(brain, T, tg)
    b = N.Mech(brain, T, {**tg, "aex2_ec50_source": "wang2013"})
    row = N.PRECURSORS.index("nlp-40")
    aex2 = np.array([e[1] == row and e[2] == T["pep_ec50_nlp-40_aex-2_nM"] for e in a.entries])
    assert aex2.any() and np.array_equal(a.e_cell, b.e_cell)
    assert np.all(a.e_ec50[aex2] == T["pep_ec50_nlp-40_aex-2_nM"])
    assert np.all(b.e_ec50[aex2] == T["pep_ec50_nlp-40_aex-2_wang2013_nM"])
    assert np.array_equal(a.e_ec50[~aex2], b.e_ec50[~aex2])


def test_amine_stores():
    """5-HT and DA cells read their own store rows (derived from Weishaupt et al. 2023), OA and TA the shared guessed
    one; with every row equal to the shared value the stores run exactly as the one shared store did (neutral
    equivalence)."""
    from types import SimpleNamespace
    st = load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    brain = SimpleNamespace(st=st, cell_names=neurons, is_muscle=np.zeros(len(neurons), bool),
                            spec=SimpleNamespace(values={}), layers=None)
    T = {s.id: s.template for s in N.SPECS}
    tg = {"peptides": "off", "monoamines": "compartments"}
    a = N.Mech(brain, T, tg)
    assert list(a.ma_cap) == [T["ma_store_molecules_serotonin"], T["ma_store_molecules_dopamine"],
                              T["ma_store_molecules"], T["ma_store_molecules"]]
    same = {**T, "ma_store_molecules_serotonin": T["ma_store_molecules"],
            "ma_store_molecules_dopamine": T["ma_store_molecules"]}
    old = {k: v for k, v in same.items() if not k.startswith("ma_store_molecules_")}
    b, c = N.Mech(brain, same, tg), N.Mech(brain, old, tg)
    v = np.where(b.ma_rel.sum(1) > 0, 0.0, -80.0)
    ctx = SimpleNamespace(v=v, outputs={})
    for m in (a, b, c):
        for _ in range(500):
            m.step(ctx, 10.0)
    assert np.array_equal(b.store, c.store) and np.array_equal(b.ma.N, c.ma.N)
    s5 = N.AMINES.index("serotonin")
    assert a.store[a.ma_rel[:, s5] > 0, s5].min() > b.store[b.ma_rel[:, s5] > 0, s5].max()   # bigger store drains less


def test_dmsr1_isoform():
    """dmsr1_isoform: the default reads the most potent Table S6 row (DMSR-1B for FLP-25); dmsr-1a changes only the
    FLP-25 on DMSR-1 entries, to isoform A's measured 1.6 uM."""
    from types import SimpleNamespace
    st = load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    brain = SimpleNamespace(st=st, cell_names=neurons, is_muscle=np.zeros(len(neurons), bool),
                            spec=SimpleNamespace(values={}), layers=None)
    T = {s.id: s.template for s in N.SPECS}
    tg = {"peptides": "compartments", "monoamines": "off"}
    a = N.Mech(brain, T, tg)
    b = N.Mech(brain, T, {**tg, "dmsr1_isoform": "dmsr-1a"})
    row = N.PRECURSORS.index("flp-25")
    hit = np.array([e[1] == row and e[2] == T["pep_ec50_flp-25_dmsr-1_nM"] for e in a.entries])
    assert hit.any() and np.array_equal(a.e_cell, b.e_cell)
    assert T["pep_ec50_flp-25_dmsr-1_isoA_nM"] / T["pep_ec50_flp-25_dmsr-1_nM"] > 1e5
    assert np.all(b.e_ec50[hit] == T["pep_ec50_flp-25_dmsr-1_isoA_nM"])
    assert np.array_equal(a.e_ec50[~hit], b.e_ec50[~hit])


def test_pc_grid():
    """pc_grid: bins as wide as the widest compartment are the four compartments (limit test: same edges, same pool,
    the regrouped occupancy within 1e-12); at the template bin size every cell's bin lies inside its named compartment,
    `gene@compartment` release is conserved and spread by volume, and the named views are the volume-weighted means."""
    from types import SimpleNamespace
    st = load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    brain = SimpleNamespace(st=st, cell_names=neurons, is_muscle=np.zeros(len(neurons), bool),
                            spec=SimpleNamespace(values={}), layers=None)
    T = {s.id: s.template for s in N.SPECS}
    tg = {"peptides": "compartments", "monoamines": "compartments"}
    four = N.Mech(brain, T, {**tg, "pc_grid": "four"})
    assert N.Mech(brain, T, tg).grid == "bins"           # the default (Director, 9 Nov 2026)
    wide = N.Mech(brain, {**T, "pc_bin_um": 1e4}, {**tg, "pc_grid": "bins"})
    fine = N.Mech(brain, T, {**tg, "pc_grid": "bins"})
    assert np.array_equal(four.edges, wide.edges) and np.array_equal(four.edges, four.cuts)
    assert len(fine.edges) - 1 > 50 and np.diff(fine.edges).max() <= T["pc_bin_um"] + 1e-9
    assert np.array_equal(fine.ma.named[fine.ma_comp], four.ma_comp)
    assert np.array_equal(fine.pep.named[fine.pep_comp], four.pep_comp)
    rng = np.random.default_rng(0)
    v = rng.uniform(-60.0, -10.0, len(neurons))
    ext = {"nlp-40@posterior_body": 1e4, "flp-11": 2e3}
    ctx = SimpleNamespace(v=v, outputs={"peptide_release": ext})
    for m in (four, wide, fine):
        for _ in range(200):
            m.step(ctx, 10.0)
    for x, y in ((four.pep.N, wide.pep.N), (four.ma.N, wide.ma.N), (four.G, wide.G)):
        assert np.allclose(x, y, rtol=1e-12, atol=1e-300)
    assert np.allclose(fine.pep.named_nM(), fine.pep.N @ np.eye(4)[fine.pep.named] /
                       (N.NA_PL * fine.pep.V @ np.eye(4)[fine.pep.named] / 1000.0))
    assert np.array_equal(four.pep.named_nM(), four.pep.nM())
    one = N.Mech(brain, {**T, "dcv_rate_per_s": 0.0}, {"peptides": "compartments", "monoamines": "off",
                                                       "pc_grid": "bins"})       # the external release alone
    zero = SimpleNamespace(v=np.full(len(neurons), -90.0), outputs={"peptide_release": {"nlp-40@posterior_body": 1e4}})
    one.step(zero, 10.0)
    row, pb = N.PRECURSORS.index("nlp-40"), N.COMPARTMENTS.index("posterior_body")
    sel = one.pep.named == pb
    assert one.pep.N[row, ~sel].max() < one.pep.N[row, sel].min()
    assert np.isclose(one.pep.N[row].sum() / np.exp(-0.01 / T["pep_degrade_tau_s"] - 0.01 * T["pc_coelomocyte_uptake_per_s"]),
                      1e4 * 0.01, rtol=1e-12)


def test_amine_synaptic():
    """amine_synaptic: off (default) returns 0 and nicholson moves no molecules (a read: both step bit-identically);
    limit tests against the closed form: one site in free volume, C = J share / (4 pi D r) exp(-r / l); two sites add
    the second at sqrt(r^2 + s^2)."""
    from types import SimpleNamespace
    st = load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    brain = SimpleNamespace(st=st, cell_names=neurons, is_muscle=np.zeros(len(neurons), bool),
                            spec=SimpleNamespace(values={}), layers=None)
    T = {s.id: s.template for s in N.SPECS}
    tg = {"peptides": "off", "monoamines": "compartments"}
    off, on = N.Mech(brain, T, tg), N.Mech(brain, T, {**tg, "amine_synaptic": "nicholson"})
    assert off.synaptic == "off"
    hsn = [neurons.index("HSNL"), neurons.index("HSNR")]
    v = np.full(len(neurons), -80.0)
    v[hsn] = -20.0
    ctx = SimpleNamespace(v=v, outputs={})
    for _ in range(300):
        off.step(ctx, 10.0)
        on.step(ctx, 10.0)
    assert np.array_equal(off.ma.N, on.ma.N) and np.array_equal(off.G, on.G)
    assert off.near_nM("serotonin", hsn) == 0.0 and on.near_nM("serotonin", hsn) > 0.0
    J = on.ma_J[hsn, N.AMINES.index("serotonin")]
    assert (J > 0).all()
    r, D, tau, share = 0.05, T["ma_diffusion_um2_per_s"], T["ma_degrade_tau_s"], 0.5
    one = N.Mech(brain, {**T, "hsn_vm2_sites": 1, "ecs_alpha": 1.0, "ecs_tortuosity": 1.0, "syn_half_space": 1.0,
                         "hsn_vm2_site_receptor_um": r, "hsn_vm2_release_share": share},
                 {**tg, "amine_synaptic": "nicholson"})
    want = share * 1e4 / (4 * np.pi * D * r) * np.exp(-r / np.sqrt(D * tau)) / 0.602214
    assert np.isclose(one.near_nM("serotonin", [hsn[0]], J=[1e4]), want, rtol=1e-9)
    L = 3.0                                                       # two pre cells, one site each: spacing L / 2
    d2 = np.hypot(r, L / 2)
    one.p = {**one.p, "hsn_vm2_region_um": L}
    two = one.near_nM("serotonin", hsn, J=[1e4, 1e4])
    want2 = share * 1e4 / (4 * np.pi * D) * (np.exp(-r / np.sqrt(D * tau)) / r + np.exp(-d2 / np.sqrt(D * tau)) / d2) \
        / 0.602214
    assert np.isclose(two, want2, rtol=1e-9)


def test_no_neuron_brain():
    """An organ-only brain (no neuron; wbody2, 9 Nov 2026) steps without raising and reports finite, neutral
    neuron summaries (G means 0, release factor 1)."""
    import warnings
    from types import SimpleNamespace
    st = load_structure()
    cells = ["dBWML22", "vBWMR22"]
    brain = SimpleNamespace(st=st, cell_names=cells, is_muscle=np.ones(2, bool), spec=SimpleNamespace(values={}),
                            layers=None)
    m = N.Mech(brain, {s.id: s.template for s in N.SPECS}, {"peptides": "compartments", "monoamines": "compartments"})
    m.reset()
    ctx = SimpleNamespace(v=np.full(2, -30.0), outputs={})
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        for _ in range(100):
            r = m.step(ctx, 10.0)
    o = r["out"]["neuromod"]
    assert all(np.isfinite(v) for v in o.values() if isinstance(v, float))
    assert (o["gq_mean"], o["gi_mean"], o["gs_mean"]) == (0.0, 0.0, 0.0)
    assert o["release_factor_min"] == o["release_factor_max"] == 1.0
    assert np.isfinite(r["I_pA"]).all() and all(np.isfinite(np.asarray(g)).all() for g in r["g_scale"].values())
