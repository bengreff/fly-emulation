"""Build the worm ledger from the code and data the model runs on, not by hand.

Sources, each parsed here:
  third_party/baaiworm/   BAAIWorm (Zhao et al. 2024, Apache 2.0): per-cell passive values and channel densities
                          (cell_param/*.json), channel kinetics, Ca pool and synapse constants (mod/*.mod PARAMETER
                          blocks), construction constants (config.json cnt_info), morphology (model/*.hoc pt3d points).
                          Their numbers are published fits: label inferred, template_source "published fit".
  data/worm/ported/c302/  c302 C2 muscle channels (Boyle and Cohen 2008 style; MIT), a toggle (off).
  data/worm/structure/    Cook 2019 wiring counts, CeNGEN expression, transmitter identity, peptide/monoamine pairs.
  docs/worm/research/param_ranges.csv  literature ranges. Literature wins: a ported value outside its literature
                          range is clipped to the nearest bound and that element is relabelled guessed.
  src/wormemu/brain_layers.py  the specs of every layer no project has (sensory, organs, neuromodulation, ...).
  data/worm/brain_runs/port302a/connections.csv  the synapses the ported construction placed (for NMJ pairs).

Writes data/worm/model/{mechanisms.yaml, parameters.csv, values/*.csv} and docs/worm/ledger.json.
Run: PYTHONPATH=src uv run python scripts/worm/build_ledger.py
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from bioemu import ledger
from wormemu import brain_layers
from wormemu.brain_structure import cengen_class, load_structure

ROOT = Path(__file__).resolve().parents[2]
BAAI = ROOT / "third_party" / "baaiworm"
OUT = ROOT / "data" / "worm" / "model"
BAAI_SRC = "BAAIWorm b99ca5a (Zhao et al. 2024 Nat Comput Sci)"
LIT = {r["quantity_id"]: r for r in csv.DictReader(open(ROOT / "docs/worm/research/param_ranges.csv"))}

# channel mechanism (BAAIWorm density name) -> CeNGEN genes (expressed if any is above threshold 2)
CHANNELS = {"shl1": ["shl-1"], "shk1": ["shk-1"], "kvs1": ["kvs-1"], "egl2": ["egl-2"], "egl36": ["egl-36"],
            "kqt3": ["kqt-3"], "egl19": ["egl-19"], "unc2": ["unc-2"], "cca1": ["cca-1"],
            "slo1_egl19": ["slo-1"], "slo1_unc2": ["slo-1"], "slo2_egl19": ["slo-2"], "slo2_unc2": ["slo-2"],
            "kcnl": ["kcnl-1", "kcnl-2", "kcnl-3", "kcnl-4"], "nca": ["nca-1", "nca-2"],
            "irk": ["irk-1", "irk-2", "irk-3"]}
NANODOMAIN = {"gsc", "r", "dca", "kb", "btot", "canci"}   # shared by the four slo mods: one row each
CONSTANTS = {"FARADAY"}
STRUCTURE_ROWS = ("morph_", "wire_")

rows: list[dict] = []
mechs: list[dict] = []
values: dict[str, pd.DataFrame] = {}


def lit(qid):
    r = LIT[qid]
    basis = r["bound_basis"]
    if basis == "nematode_wide":                    # range across nematodes / generic, not this species
        basis = "guessed" if r["label"] == "guessed" else "measured_related"
    return float(r["bio_min"]), float(r["bio_max"]), r["label"], basis, f"{r['source']} (param_ranges {qid})"


def prior_for(t, lo, hi):
    if lo > 0 and hi / lo >= 10:
        return "loguniform", "", "", "guessed: log-uniform over the range"
    return "uniform", "", "", "guessed: uniform over the range"


def mech(id, name, layer, status, source, toggle="", neutral="", default=None, notes="", absent_reason=""):
    if default is None:
        default = "" if status == "absent" else "on"
    mechs.append(dict(id=id, name=name, layer=layer, status=status, toggle=toggle, neutral=neutral,
                      default=default, source=source, notes=notes, absent_reason=absent_reason))


def row(pid, mid, unit, template, lo, hi, *, grain="global", applies_to="whole worm", n=1, tsrc="", label="guessed",
        basis="guessed", bsrc="guessed", prior=None, notes="", toggle="", table=None):
    pd_, pa, pb, pbasis = prior or prior_for(template, lo, hi)
    rows.append(dict(param_id=pid, mechanism_id=mid, grain=grain, applies_to=applies_to, unit=unit, n_values=n,
                     value_template=template, template_source=tsrc, bio_min=lo, bio_max=hi, bound_basis=basis,
                     bound_source=bsrc, bound_verified="unverified", prior_dist=pd_, prior_a=pa, prior_b=pb,
                     prior_basis=pbasis, label=label, precision_needed="not yet estimated", precision_method="",
                     toggle=toggle, notes=notes))
    if table is not None:
        assert len(table) == n, (pid, len(table), n)
        values[pid] = table


def absent(pid, mid, unit, n, grain, applies_to, notes, lo="", hi="", bsrc=""):
    rows.append(dict(param_id=pid, mechanism_id=mid, grain=grain, applies_to=applies_to, unit=unit, n_values=n,
                     value_template="", template_source="", bio_min=lo, bio_max=hi, bound_basis="",
                     bound_source=bsrc, bound_verified="", prior_dist="", prior_a="", prior_b="", prior_basis="",
                     label="absent", precision_needed="not yet estimated", precision_method="", toggle="",
                     notes=notes))


def kin_bounds(name, unit, t):
    """Guessed bounds for a published kinetic constant: shifts of +-20 mV for half-activations (vh*, b*),
    factor 2 for other mV quantities (slopes), factor 3 for everything else; sign kept."""
    if unit == "mV" and (name.startswith("vh") or name.startswith("b")):
        return t - 20.0, t + 20.0, "guessed: +-20 mV around the published value"
    f = 2.0 if unit == "mV" else 3.0
    if t == 0:
        return -1.0, 1.0, "guessed"
    lo, hi = sorted((t / f, t * f))
    return lo, hi, f"guessed: factor {f:g} either side of the published value"


def parse_mod(path):
    out, inside = [], False
    for line in path.read_text().splitlines():
        if line.strip().startswith("PARAMETER"):
            inside = True
            continue
        if inside and line.strip().startswith("}"):
            break
        if inside:
            m = re.match(r"\s*(\w+)\s*=\s*([-+0-9.eE]+)\s*(\(([^)]*)\))?", line)
            if m:
                out.append((m.group(1), float(m.group(2)), (m.group(4) or "1").strip()))
    return out


# ================================================================================================================
def ported_cells():
    neurons, muscles = {}, {}
    for f in sorted((BAAI / "cell_param").glob("*.json")):
        n = f.stem
        if n in ("template", "MuscleCell"):
            continue
        d = json.loads(f.read_text())
        (muscles if n.startswith("MC") and n not in ("MCL", "MCR") else neurons)[n] = d
    assert len(neurons) == 302 and len(muscles) == 96, (len(neurons), len(muscles))
    return neurons, muscles


def build_passive_and_channels(neurons, muscles, st):
    names = sorted(neurons)
    sets = {}
    for n in names:
        sets.setdefault(json.dumps(neurons[n], sort_keys=True), []).append(n)
    set_of = {n: i for i, (_, ms) in enumerate(sorted(sets.items(), key=lambda kv: -len(kv[1]))) for n in ms}
    note_sets = (f"BAAIWorm assigns one of {len(sets)} parameter sets to every neuron (sizes "
                 f"{sorted((len(v) for v in sets.values()), reverse=True)}); values/<id>.csv column set_id")
    mech("literature_overrides", "Literature wins: ported values outside a literature range are clipped to it",
         "policy", "have", "docs/worm/research/param_ranges.csv", toggle="literature_overrides",
         neutral="off = BAAIWorm values as published", default="on",
         notes="clips neuron cm (A1), leak reversal (A5), Ra (A6), muscle leak reversal (F1), excitatory synapse "
               "reversal (B5), synaptic decay (B3) and gap conductance (C4); clipped elements are labelled guessed")
    mech("passive", "Passive membrane (soma and neurite)", "cell", "have", BAAI_SRC, notes=note_sets)
    overrides = {"cm": "A1", "epas": "A5", "Ra": "A6"}
    units = {"cm": "uF/cm2", "epas": "mV", "Ra": "ohm cm", "gpas": "S/cm2"}
    for sec in ("soma", "neurite"):
        for q in ("Ra", "cm", "gpas", "epas"):
            v = np.array([neurons[n][sec][q] for n in names], float)
            if q in overrides:
                lo, hi, _, basis, bsrc = lit(overrides[q])
            else:
                lo, hi, basis, bsrc = 1e-6, 1e-3, "guessed", "guessed (input resistance 0.2-5 GOhm, param_ranges A3, " \
                                                             "is the check, not a bound)"
            clipped = np.clip(v, lo, hi)
            lab = np.where(clipped != v, "guessed", "inferred")
            src = [f"published fit, {BAAI_SRC}" if c == p else f"BAAIWorm {p:g} clipped to the literature range "
                   f"[{lo:g}, {hi:g}] ({overrides[q]})" for c, p in zip(clipped, v)]
            t = pd.DataFrame(dict(element=names, value=clipped, label=lab, source=src, ported=v,
                                  set_id=[set_of[n] for n in names]))
            sd = ("normal", float(np.median(clipped)), 5.0, "guessed: each element normal around its own value, "
                  "sd 5 mV, truncated") if q == "epas" else (
                "lognormal", float(np.median(clipped)), 0.35, "guessed: each element log-normal around its own "
                "value, sd 0.35 (factor 1.4), truncated")
            row(f"pas_{sec}_{q}", "passive", units[q], float(np.median(clipped)), lo, hi, grain="cell",
                applies_to=f"every neuron, {sec}", n=302, tsrc="median of the per-cell values (values table)",
                label="inferred", basis=basis, bsrc=bsrc, prior=sd, table=t,
                notes=f"{int((lab == 'guessed').sum())} of 302 ported values outside the literature range, clipped"
                if (lab == "guessed").any() else "")

    # muscles: BAAIWorm's passive muscle set; F1 (rest) bounds the leak reversal of a passive cell
    mn = sorted(muscles)
    mech("muscle_passive", "Body-wall muscle passive membrane (BAAIWorm muscle set)", "muscle", "have", BAAI_SRC,
         notes="BAAIWorm muscles are passive (all channel densities 0); 96 cells, the interface uses 95 (MCVL24 is "
               "dropped: the real worm has no VL24)")
    for q, code in (("Ra", "A6"), ("cm", "A1"), ("gpas", None), ("epas", "F1")):
        v = np.array([muscles[n]["soma"][q] for n in mn], float)
        lo, hi, _, basis, bsrc = lit(code) if code else (1e-6, 1e-3, None, "guessed", "guessed")
        c = np.clip(v, lo, hi)
        lab = np.where(c != v, "guessed", "inferred")
        src = [f"published fit, {BAAI_SRC}" if a == b else f"BAAIWorm {b:g} clipped to [{lo:g}, {hi:g}] ({code})"
               for a, b in zip(c, v)]
        row(f"mpas_{q}", "muscle_passive", units[q], float(np.median(c)), lo, hi, grain="muscle",
            applies_to="every body-wall muscle", n=96, tsrc="median of the per-muscle values", label="inferred",
            basis=basis, bsrc=bsrc, table=pd.DataFrame(dict(element=mn, value=c, label=lab, source=src, ported=v)))

    # channel densities, one mechanism per channel; CeNGEN expression recorded beside each value
    classes = set(st.cengen_classes)
    cls = {n: cengen_class(n, classes) for n in names}
    for ch, genes in CHANNELS.items():
        mid = f"ch_{ch}"
        v = np.array([neurons[n]["soma"][f"gb{ch}"] for n in names], float)
        expr = np.array([max(st.expr(g, cls[n]) for g in genes) for n in names])
        has = np.array([cls[n] is not None for n in names])
        conflict = int(((v > 0) & (expr == 0) & has).sum())
        missing = int(((v == 0) & (expr > 0)).sum())
        mech(mid, f"{ch} channel ({', '.join(genes)})", "channel", "have", BAAI_SRC,
             notes=f"soma only (BAAIWorm neurites are passive). CeNGEN: {conflict} neurons have a ported density "
                   f"but no detected {'/'.join(genes)}; {missing} express it with ported density 0")
        hi = float(max(10 * v.max(), 1e-4))
        t = pd.DataFrame(dict(element=names, value=v, label="inferred", source=f"published fit, {BAAI_SRC}",
                              cengen_class=[cls[n] or "" for n in names], cengen_tpm=expr.round(2),
                              set_id=[set_of[n] for n in names]))
        row(f"dens_{ch}", mid, "nS/um2", float(np.median(v)), 0.0, hi, grain="cell", applies_to="every neuron, soma",
            n=302, tsrc="median of the per-cell values (values table)", label="inferred", basis="guessed",
            bsrc="guessed: 0 to 10x the largest ported density",
            prior=("lognormal", float(np.median(v)), 0.5, "guessed: each nonzero element log-normal around its own "
                   "value, sd 0.5; zero stays zero unless expression_map adds it"), table=t)
    mech("expression_map", "CeNGEN expression gates channel presence (zero density where no gene is detected; "
         "a class-median density where the gene is detected but the ported density is 0)", "channel", "have",
         "CeNGEN threshold 2 (Taylor et al. 2021)", toggle="expression_map", neutral="off", default="off")


def build_kinetics():
    mods = {p.stem: parse_mod(p) for p in sorted((BAAI / "mod").glob("*.mod"))}
    base = {k: dict((n, v) for n, v, _ in mods[k]) for k in ("egl19", "unc2")}
    tied, nano = [], {}
    for mod, params in mods.items():
        if mod not in CHANNELS:
            continue
        partner = mod.split("_")[1] if "_" in mod else None
        for name, val, unit in params:
            if name.startswith("gb") or name in CONSTANTS:
                continue
            if partner and name in NANODOMAIN:
                nano.setdefault(name, set()).add((val, unit))
                continue
            if partner and name in base[partner]:
                if base[partner][name] == val:
                    tied.append(f"{mod}.{name}")
                    continue
            lo, hi, b = kin_bounds(name, unit, val)
            row(f"kin_{mod}_{name}", f"ch_{mod}", unit, val, lo, hi, grain="channel",
                applies_to=f"every cell with {mod}", tsrc=f"published fit, {BAAI_SRC} mod/{mod}.mod", label="inferred",
                basis="guessed", bsrc=b, prior=("normal", val, (hi - lo) / 4, "guessed: normal around the published "
                                                 "value, sd a quarter of the range, truncated"))
    mech("ca_nanodomain", "Ca nanodomain at the channel mouth driving SLO-1/SLO-2 (Nicoletti et al. 2024)",
         "channel", "have", BAAI_SRC, notes=f"{len(tied)} Ca-channel constants inside the slo mods equal the "
                                            "egl19/unc2 values and are tied to those rows, not counted twice")
    for name, s in sorted(nano.items()):
        assert len(s) == 1, (name, s)
        (val, unit), = s
        lo, hi, b = kin_bounds(name, unit, val)
        row(f"nano_{name}", "ca_nanodomain", unit, val, lo, hi, tsrc=f"{BAAI_SRC} slo*.mod",
            label="guessed" if name == "gsc" else "inferred", basis="guessed", bsrc=b,
            notes="the mod says 'assumed equal to 40 pS'" if name == "gsc" else "")
    mech("ca_pool", "Intracellular Ca pool (cainternm)", "cell", "have", BAAI_SRC,
         notes="cai is in uM in the mod but NEURON's Nernst treats cai as mM, so eca sits near +44 mV at rest instead "
               "of about +130 mV (measured on backhouse: eca 41.2 mV at cai 0.065). Ported as is; the ions row cao "
               "records the outside concentration")
    for name, val, unit in mods["cainternm"]:
        lo, hi, b = kin_bounds(name, unit, val)
        row(f"capool_{name}", "ca_pool", unit, val, lo, hi, tsrc=f"published fit, {BAAI_SRC} mod/cainternm.mod",
            label="inferred", basis="guessed", bsrc=b)
    mech("ions", "Ion reversal potentials and outside Ca", "cell", "have", "NEURON defaults (BAAIWorm never sets them)")
    for pid, unit, val, lo, hi, note in (("ion_ek", "mV", -77.0, -100.0, -60.0, "NEURON default; BAAIWorm never sets it"),
                                         ("ion_ena", "mV", 50.0, 20.0, 70.0, "NEURON default, read by nca"),
                                         ("ion_cao", "mM", 2.0, 1.0, 5.0, "NEURON default; worm salines use 1-5 mM")):
        row(pid, "ions", unit, val, lo, hi, tsrc="NEURON default", label="guessed", notes=note)
    return mods


def build_synapses(mods, st, conns):
    nn = [i for i, k in enumerate(st.kind) if k == "neuron"]
    nset = {st.names[i] for i in nn}
    chem_nn = [(st.names[a], st.names[b], k) for a, b, k in st.chem if st.names[a] in nset and st.names[b] in nset]
    gap_nn = [(st.names[a], st.names[b], k) for a, b, k in st.gap if st.names[a] in nset and st.names[b] in nset]
    # synapse kinetics: B-rows bound them; k sets the decay (tau = (1 - s_inf)/k, so 1/k is the longest decay)
    bounds = {"erev": {"exc": "B5", "inh": "B8"}, "Vth": "B1", "delta": "B2"}
    for kind in ("exc", "inh"):
        mid = f"syn_{kind}"
        mech(mid, f"Graded chemical synapse, {'excitatory' if kind == 'exc' else 'inhibitory'} "
                  f"(neuron_to_neuron_{kind}_syn; also NMJ and muscle-to-neuron)", "synapse", "have", BAAI_SRC)
        for name, val, unit in parse_mod(BAAI / "mod" / f"neuron_to_neuron_{kind}_syn.mod"):
            if name == "weight":
                continue
            if name == "k":
                lo3, hi3, lab, basis, bsrc = lit("B3")
                lo, hi = 1.0 / hi3, 1.0 / lo3
                bsrc = f"1/decay, decay {lo3:g}-{hi3:g} ms: {bsrc}"
            elif name == "conductance":
                lo4, hi4, lab, basis, bsrc = lit("B4")
                lo, hi = lo4 / 1000.0, hi4 / 1000.0
            else:
                code = bounds[name][kind] if isinstance(bounds[name], dict) else bounds[name]
                lo, hi, lab, basis, bsrc = lit(code)
            t = float(np.clip(val, lo, hi))
            row(f"{mid}_{name}", mid, unit, t, lo, hi, tsrc=f"published fit, {BAAI_SRC}" if t == val else
                f"BAAIWorm {val:g} clipped to the literature range", label="inferred" if t == val else "guessed",
                basis=basis, bsrc=bsrc, applies_to=f"every {kind} synapse",
                notes="" if t == val else f"ported value {val:g} {unit}")
    mech("gap", "Gap junctions (ohmic, symmetric)", "gap", "have", BAAI_SRC)
    lo, hi, lab, basis, bsrc = lit("C4")
    row("gap_weight", "gap", "uS", float(np.clip(1e-5, lo / 1000, hi / 1000)), lo / 1000, hi / 1000,
        tsrc="BAAIWorm 1e-5 uS (transform.py) clipped to the literature range", label="guessed", basis=basis,
        bsrc=bsrc, applies_to="every placed gap junction", notes="ported value 1e-5 uS = 0.01 nS per placed junction")
    mech("wiring", "Connectome and BAAIWorm's construction (contact counts -> placed synapses on segments)",
         "synapse", "have", f"Cook et al. 2019 SI 5 via {BAAI_SRC} config2detailed")
    for pid, val, lo, hi, note in (("syn_weight_nn", 0.5, 0.1, 1.0, "every neuron-neuron synapse (transform.py); "
                                    "bounds = BAAIWorm's own weight_range"),
                                   ("syn_weight_nmj", 1.0, 0.1, 2.0, "every neuron-to-muscle synapse"),
                                   ("syn_weight_mn", 0.1, 0.01, 1.0, "every muscle-to-neuron synapse")):
        row(pid, "wiring", "1", val, lo, hi, tsrc=f"{BAAI_SRC} transform.py", label="guessed", notes=note)
    cnt = json.loads((BAAI / "config.json").read_text())["cnt_info"]
    for k, v in cnt.items():
        if isinstance(v, dict) or k == "inh_prob":
            continue
        lo, hi = sorted((v / 3, v * 3))
        row(f"build_{k}", "wiring", "1" if k != "length_per_seg" else "um", float(v), lo, hi,
            tsrc=f"{BAAI_SRC} config.json cnt_info", label="guessed",
            notes="construction constant; how BAAIWorm chose it is not checked")
    t = pd.DataFrame([dict(element=f"{a}>{b}", value=k, label="measured", source="Cook et al. 2019 SI 5")
                      for a, b, k in chem_nn])
    row("wire_chem_contacts", "wiring", "EM synapses", float(t.value.median()), 1, 1000, grain="connection",
        applies_to="neuron-neuron chemical pairs", n=len(t), tsrc="per pair (values table)", label="measured",
        basis="physical_limit", bsrc="counts", prior=("fixed", float(t.value.median()), "", "measured"), table=t)
    t = pd.DataFrame([dict(element=f"{a}-{b}", value=k, label="measured", source="Cook et al. 2019 SI 5")
                      for a, b, k in gap_nn])
    row("wire_gap_contacts", "wiring", "EM gap junctions", float(t.value.median()), 1, 1000, grain="connection",
        applies_to="neuron-neuron gap pairs", n=len(t), tsrc="per pair (values table)", label="measured",
        basis="physical_limit", bsrc="counts", prior=("fixed", float(t.value.median()), "", "measured"), table=t)
    mus = {r for r in conns.post.unique() if r.startswith("MC") and r not in ("MCL", "MCR")}
    nmj = sorted({(a, b) for a, b in zip(conns.pre, conns.post) if b in mus and a not in mus})
    mn = sorted({(a, b) for a, b in zip(conns.pre, conns.post) if a in mus and b not in mus})
    t = pd.DataFrame([dict(element=f"{a}>{b}", value=1, label="measured", source="BAAIWorm neuron_muscle.xlsx")
                      for a, b in nmj])
    row("wire_nmj_pairs", "wiring", "flag", 1, 0, 1, grain="connection", applies_to="neuron-to-muscle pairs",
        n=len(t), tsrc="pairs placed by the port (port302a connections.csv)", label="measured",
        basis="physical_limit", bsrc="flag", prior=("fixed", 1, "", "measured"), table=t)
    t = pd.DataFrame([dict(element=f"{a}>{b}", value=1, label="guessed", source="BAAIWorm muscle_neuron.xlsx")
                      for a, b in mn])
    row("wire_mn_pairs", "wiring", "flag", 1, 0, 1, grain="connection", applies_to="muscle-to-neuron pairs",
        n=len(t), tsrc="pairs placed by the port", label="guessed", basis="guessed", bsrc="flag",
        prior=("fixed", 1, "", "as ported"), table=t,
        notes="BAAIWorm's muscle-to-neuron feedback synapses; the source of this table is not checked")
    absent("syn_strength_per_pair", "wiring", "nS", len(chem_nn), "connection", "neuron-neuron chemical pairs",
           "the real strength of each connection is unmeasured; the template uses one conductance x weight x the "
           "placed-synapse count (no per-synapse free knobs)", 0.1, 2, lit("B4")[4])
    absent("gap_strength_per_pair", "gap", "nS", len(gap_nn), "connection", "neuron-neuron gap pairs",
           "per-pair coupling unmeasured except a few pairs (param_ranges C2, C5, C6)", 0.05, 20, lit("C2")[4])
    # sign per presynaptic neuron (transmitter rule) and the receptor-level sign that is still absent
    names = sorted(nset)
    sgn = []
    for n in names:
        tr, src = st.transmitter.get(n, set()), st.transmitter_source.get(n, "none")
        inh = tr == {"gaba"}
        lab = {"wang2024": "derived", "cengen": "inferred"}.get(src, "guessed")
        sgn.append(dict(element=n, value=int(inh), label=lab, source=f"{src}: {', '.join(sorted(tr)) or 'none'}"))
    t = pd.DataFrame(sgn)
    mech("syn_sign", "Synapse sign by presynaptic transmitter (GABA-only presynaptic neuron -> inhibitory)",
         "synapse", "have", "Wang et al. 2024 transmitter atlas, CeNGEN markers as fallback", toggle="sign_rule",
         neutral="allexc = BAAIWorm as published (every synapse excitatory)", default="transmitter")
    row("syn_inhibitory", "syn_sign", "flag", 0, 0, 1, grain="cell", applies_to="every neuron as presynaptic cell",
        n=302, tsrc="transmitter rule (values table)", label="derived", basis="physical_limit", bsrc="flag",
        prior=("bernoulli", round(float(t.value.mean()), 3), "", "fraction inhibitory under the rule; only "
               "guessed elements are drawn"), table=t)
    mech("receptor_sign", "Synapse sign by postsynaptic receptor (GluCl, ACC, LGC chloride channels inhibitory)",
         "synapse", "absent", "planned: CeNGEN receptor expression per postsynaptic class", toggle="receptor_sign",
         neutral="off", default="off", absent_reason="needs a receptor-to-synapse map; next toggle after port302b")
    absent("syn_sign_receptor", "receptor_sign", "flag", len(chem_nn), "connection", "neuron-neuron chemical pairs",
           "sign per connection from postsynaptic receptors; not built")
    mech("innexin_identity", "Gap junction conductance and rectification by innexin pair", "gap", "absent",
         "Bhattacharya et al. 2019 innexin atlas (not extracted)", absent_reason="per-pair innexin identity not mapped")
    lo, hi, _, _, bsrc = lit("C1")
    absent("gap_innexin_unitary", "innexin_identity", "pS", 1, "family", "each innexin", "C1 range", lo, hi, bsrc)
    return len(chem_nn), len(gap_nn), len(nmj)


def build_morphology():
    pts = 0
    for f in (BAAI / "model").glob("*.hoc"):
        if f.stem == "MuscleCell":
            continue
        pts += f.read_text().count("pt3dadd(")
    mech("morphology", "Cell morphologies (NEURON hoc, 3D points with diameters)", "cell", "have",
         f"{BAAI_SRC} model/*.hoc (from the OpenWorm / Virtual Worm NeuroML cells)")
    row("morph_xyz", "morphology", "um", 0.0, -1000.0, 1000.0, grain="compartment",
        applies_to="every 3D point of every cell", n=3 * pts, tsrc="per point in third_party/baaiworm/model/*.hoc",
        label="derived", basis="physical_limit", bsrc="body length about 1 mm", prior=("fixed", 0.0, "", "as ported"),
        notes="from the Virtual Worm 3D atlas, not an EM reconstruction of one animal")
    row("morph_diam", "morphology", "um", 0.5, 0.01, 20.0, grain="compartment", applies_to="every 3D point",
        n=pts, tsrc="per point in model/*.hoc", label="derived", basis="physical_limit", bsrc="guessed",
        prior=("fixed", 0.5, "", "as ported"))
    return pts


def build_c302_muscle():
    mech("muscle_active", "Body-wall muscle K and Ca channels (c302 C2, Boyle and Cohen 2008 style)", "muscle",
         "partial", "c302 parameters_C2 (OpenWorm, MIT)", toggle="muscle_active", neutral="off", default="off",
         notes="parameters ported; not yet inserted into the NEURON muscles (BAAIWorm muscles are passive)")
    keep = re.compile(r"^(muscle_(leak|k_slow|k_fast|ca_boyle)_\w+|(k_slow|k_fast|ca_boyle)_gate_\w+|"
                      r"ca_conc_(decay_time|rho)_muscle)$")
    n = 0
    for r in csv.DictReader(open(ROOT / "data/worm/ported/c302/c302_parameters.csv")):
        p = r["param_name"]
        if not keep.match(p) or p.endswith("_instances"):
            continue
        v = float(r["value"])
        lo, hi, b = kin_bounds("b" if p.endswith(("midpoint", "erev")) else p, r["unit"], v)
        row(f"c302_{p}", "muscle_active", r["unit"], v, lo, hi, tsrc="published fit, c302 parameters_C2",
            label="inferred", basis="guessed", bsrc=b, applies_to=r["applies_to"])
        n += 1
    lo, hi, _, basis, bsrc = lit("F11")
    absent("bwm_gap", "muscle_passive", "nS", 1, "global", "neighbouring body-wall muscles",
           "muscle-muscle coupling (UNC-9) is not in the port (c302 sets it to 0)", lo, hi, bsrc)
    return n


def build_layers(st):
    for mid, name, layer, default in brain_layers.MECHANISMS:
        mech(mid, name, layer, "partial", "lumped model in src/wormemu/brain_layers.py", toggle=mid,
             neutral="off", default=default)
    lig = sorted({a for a, _ in st.peptide_pairs})
    rec = sorted({b for _, b in st.peptide_pairs})
    pairs = [f"{a}>{b}" for a, b in st.peptide_pairs]
    ma_fam = sorted({a for a, _ in st.monoamine_pairs})
    ma_rec = sorted({b for _, b in st.monoamine_pairs})
    ma_pairs = [f"{a}>{b}" for a, b in st.monoamine_pairs]
    elements = {("peptides", "family"): lig, ("peptides", "pairing"): pairs, ("peptides", "gene"): rec,
                ("monoamines", "family"): ma_fam, ("monoamines", "pairing"): ma_pairs, ("monoamines", "gene"): ma_rec}
    measured_ec50 = {"mod-1": "D6", "lgc-55": "D7"}
    for s in brain_layers.SPECS:
        if s.lit:
            lo, hi, lab, basis, bsrc = lit(s.lit)
        else:
            lo, hi, lab, basis, bsrc = s.lo, s.hi, s.label, "guessed", "guessed (src/wormemu/brain_layers.py)"
        assert lo <= s.template <= hi, s
        el = elements.get((s.mechanism, s.grain))
        tab = None
        if el:
            recs = []
            for e in el:
                code = measured_ec50.get(e.split(">")[-1]) if s.id == "ma_ec50_nM" else None
                if code:
                    l2, h2, lab2, _, src2 = lit(code)
                    recs.append(dict(element=e, value=float(LIT[code]["prior_centre"]) * 1000, label=lab2,
                                     source=src2))
                else:
                    recs.append(dict(element=e, value=s.template, label=lab, source="template guess"))
            tab = pd.DataFrame(recs)
        row(s.id, s.mechanism, s.unit, s.template, lo, hi, grain=s.grain, applies_to=s.applies_to,
            n=len(el) if el else 1, tsrc=bsrc if s.lit and lab != "guessed" else "guessed (brain_layers.py)",
            label=lab, basis=basis, bsrc=bsrc, notes=s.notes, table=tab)
    mech("other_cells", "Hypodermis, seam, excretory canal, coelomocytes, other glia", "organ", "absent",
         "none", absent_reason="no lumped model yet; no INTERFACE channel needs them this week")


def export(led, extra):
    c = ledger.counts(led)
    by = c["by_label"]
    known = sum(by.get(k, 0) for k in ("measured", "derived", "inferred"))
    mrows, prow = [], []
    bym = c["by_mechanism"]
    for r in led.mechanisms.to_dict("records"):
        r = {k: ("" if v is None or (isinstance(v, float) and np.isnan(v)) else v) for k, v in r.items()}
        labs = bym.get(r["id"], {})
        r["numbers"] = int(sum(labs.values()))
        r["by_label"] = labs
        mrows.append(r)
    for r in led.parameters.to_dict("records"):
        r = {k: ("" if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()}
        t = led.values(r["param_id"])
        if t is not None:
            v = pd.to_numeric(t.value, errors="coerce")
            r["values_file"] = f"data/worm/model/values/{r['param_id']}.csv"
            r["element_stats"] = dict(min=float(v.min()), median=float(v.median()), max=float(v.max()),
                                      by_label={k: int(x) for k, x in t.label.value_counts().items()})
        r["kind"] = "structure" if r["param_id"].startswith(STRUCTURE_ROWS) else "physiology"
        prow.append(r)
    phys = Counter()
    for r in prow:
        if r["kind"] == "physiology":
            for k, x in (r["element_stats"]["by_label"] if "element_stats" in r else {r["label"]: r["n_values"]}).items():
                phys[k] += int(x)
    pk = sum(phys.get(k, 0) for k in ("measured", "derived", "inferred"))
    out = dict(
        generated_by="scripts/worm/build_ledger.py",
        generated_at=subprocess.run(["date", "+%Y-%m-%d %H:%M %Z"], capture_output=True, text=True).stdout.strip(),
        definitions=dict(
            known="measured + derived + inferred (inferred includes published fits such as BAAIWorm's)",
            placeholder="guessed: a number the model runs on, inside a stated range, not from data",
            gap="absent: a number the real worm has that the model does not use yet",
            must_fill="placeholder + gap",
            precision_needed="'not yet estimated' everywhere until a sensitivity run gives a value with its method"),
        totals=dict(numbers=c["total_numbers"], rows=c["rows"], mechanisms=len(mrows), by_label=by, known=known,
                    placeholder=by.get("guessed", 0), gap=by.get("absent", 0),
                    used_by_model=c["total_numbers"] - by.get("absent", 0),
                    must_fill=by.get("guessed", 0) + by.get("absent", 0)),
        totals_physiology=dict(note="excluding structure rows (morphology points, connectome counts and pair lists)",
                               numbers=sum(phys.values()), by_label=dict(phys), known=pk,
                               placeholder=phys.get("guessed", 0), gap=phys.get("absent", 0),
                               must_fill=phys.get("guessed", 0) + phys.get("absent", 0)),
        by_grain=c["by_grain"], mechanisms=mrows, parameters=prow, build_notes=extra)
    (ROOT / "docs/worm/ledger.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def main():
    st = load_structure()
    conns = pd.read_csv(ROOT / "data/worm/brain_runs/port302a/connections.csv")
    neurons, muscles = ported_cells()
    build_passive_and_channels(neurons, muscles, st)
    mods = build_kinetics()
    n_chem, n_gap, n_nmj = build_synapses(mods, st, conns)
    pts = build_morphology()
    n_c302 = build_c302_muscle()
    build_layers(st)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "values").mkdir(parents=True)
    (OUT / "mechanisms.yaml").write_text(yaml.safe_dump(mechs, sort_keys=False, width=200))
    pd.DataFrame(rows, columns=ledger.PARAM_COLUMNS).to_csv(OUT / "parameters.csv", index=False)
    for pid, t in values.items():
        t.to_csv(OUT / "values" / f"{pid}.csv", index=False)
    led = ledger.load(OUT)
    bad = ledger.validate(led)
    assert not bad, "\n".join(bad[:30])
    extra = dict(neuron_chem_pairs=n_chem, neuron_gap_pairs=n_gap, nmj_pairs=n_nmj, morph_points=pts,
                 c302_muscle_rows=n_c302)
    out = export(led, extra)
    print(json.dumps(out["totals"], indent=1))
    print(json.dumps(out["totals_physiology"], indent=1))
    print(json.dumps(extra))


if __name__ == "__main__":
    main()
