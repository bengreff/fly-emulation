"""Build the worm ledger from the code and data the model runs on, not by hand.

Sources, each parsed here:
  third_party/baaiworm/   BAAIWorm (Zhao et al. 2024, Apache 2.0): per-cell passive values and channel densities
                          (cell_param/*.json), channel kinetics, Ca pool and synapse constants (mod/*.mod PARAMETER
                          blocks), construction constants (config.json cnt_info), morphology (model/*.hoc pt3d points).
                          Their numbers are published fits: label published_fit, source_project BAAIWorm.
  data/worm/ported/c302/  c302 C2 muscle channels (Boyle and Cohen 2008 style; MIT), a toggle (off).
  data/worm/structure/    Cook 2019 wiring counts, CeNGEN expression, transmitter identity, peptide/monoamine pairs;
                          fenyves2020/ synapse polarity predictions (Fenyves et al. 2020 S1 Data, CC BY; the xlsx
                          as downloaded and sign_prediction.csv, sheet 5 columns pre, post, synapses, polarity).
  docs/worm/research/param_ranges.csv  literature ranges. Literature wins: a ported value outside its literature
                          range is clipped to the nearest bound and that element is relabelled guessed.
  src/wormemu/brain_layers.py  the specs of every layer no project has (sensory, organs, neuromodulation, ...).
  data/worm/brain_runs/port302a/connections.csv  the synapses BAAIWorm's construction placed (wiring=baaiworm).

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

import ledger_catalog as cat
from bioemu import ledger
from wormemu import brain_layers
from wormemu.brain_structure import bwm_name, cengen_class, load_structure

ROOT = Path(__file__).resolve().parents[2]
BAAI = ROOT / "third_party" / "baaiworm"
FENYVES = ROOT / "data" / "worm" / "structure" / "fenyves2020" / "sign_prediction.csv"
OUT = ROOT / "data" / "worm" / "model"
BAAI_SRC = "BAAIWorm b99ca5a (Zhao et al. 2024 Nat Comput Sci)"
LIT = {r["quantity_id"]: r for r in csv.DictReader(open(ROOT / "docs/worm/research/param_ranges.csv"))}

# channel mechanism (BAAIWorm density name) -> CeNGEN genes (expressed if any is above threshold 2)
CHANNELS = {"shl1": ["shl-1"], "shk1": ["shk-1"], "kvs1": ["kvs-1"], "egl2": ["egl-2"], "egl36": ["egl-36"],
            "kqt3": ["kqt-3"], "egl19": ["egl-19"], "unc2": ["unc-2"], "cca1": ["cca-1"],
            "slo1_egl19": ["slo-1"], "slo1_unc2": ["slo-1"], "slo2_egl19": ["slo-2"], "slo2_unc2": ["slo-2"],
            "kcnl": ["kcnl-1", "kcnl-2", "kcnl-3", "kcnl-4"], "nca": ["nca-1", "nca-2"],
            "irk": ["irk-1", "irk-2", "irk-3"]}
# fast receptors per transmitter, excitatory (cation) vs inhibitory (chloride); CeNGEN lacks deg-3, des-2, eat-2, lgc-48
RECEPTORS = {
    "acetylcholine": (["acr-2", "acr-3", "acr-5", "acr-8", "acr-9", "acr-12", "acr-14", "acr-15", "acr-16", "acr-18",
                       "acr-19", "acr-21", "acr-23", "unc-29", "unc-38", "unc-63", "lev-1", "lev-8"],
                      ["acc-1", "acc-2", "acc-3", "acc-4", "lgc-46", "lgc-47", "lgc-49"]),
    "glutamate": (["glr-1", "glr-2", "glr-3", "glr-4", "glr-5", "glr-6", "glr-7", "glr-8", "nmr-1", "nmr-2"],
                  ["glc-1", "glc-2", "glc-3", "glc-4", "avr-14", "avr-15"]),
    "gaba": (["exp-1", "lgc-35"], ["unc-49", "lgc-37", "lgc-38"]),
}
NANODOMAIN = {"gsc", "r", "dca", "kb", "btot", "canci"}   # shared by the four slo mods: one row each
CONSTANTS = {"FARADAY"}
STRUCTURE_ROWS = ("morph_", "wire_")
OPEN_QUESTIONS = [
    dict(id="saturation", since="2026-11-05", where="docs/worm/BRAIN_PORT.md sections 4-4c",
         question="Why does the neural-only network settle into a fixed depolarised state? At the ledger defaults "
                  "(wiring=cook, strengths at the range log-midpoint) 206 of 302 neurons sit above -20 mV at 6 s with "
                  "transmitter signs (D7) and 100 with receptor_sign on (D8, Fenyves first). Localised to recurrent "
                  "chemical excitation (isolated cells rest at -53 to -56 mV); receptor-level inhibition halves it "
                  "but does not remove it.",
         candidates="per-EM synapse strength (range B4 is inferred from circuit models, not measured); the graded "
                    "release curve (Vth -20 mV, delta 5 mV, BAAIWorm's fit); per-EM gap strength (range C4 guessed); "
                    "missing extrasynaptic and neuromodulatory inhibition (layers off in these runs)",
         status="open; nothing tuned. The closed loop runs on D8's configuration, labelled. Section 5: four single "
                "range ends each bring it under 30 (chemical strength 0.1 nS, excitatory reversal -10 mV, excitatory "
                "release slope 2 mV, inhibitory release threshold -45 mV); none has a measured value for or against "
                "it (RANGE_ENDS_LIT.md, section 6a). With the excitatory reversal range widened to +11 mV (measured) "
                "the template is +0.5 mV and the count is 105 (D8b)"),
]

rows: list[dict] = []
mechs: list[dict] = []
values: dict[str, pd.DataFrame] = {}


# a research-file range whose own note says the number was not read (not retrieved, not explicit in the snippet,
# widened past the data to cover what was not measured) is a guess, whatever its bound_basis column says (7 Nov)
WEAK_LIT = re.compile(r"(?i)not retrieved|not explicit|not present in the retrieved|needs primary|widened to [^.]* to cover")

WEAK_QID = {
    "B11": "the search summary credits Richmond & Jorgensen 1999 with a light-evoked decay, but light-evoked worm NMJ "
           "currents came about ten years later (Liewald et al. 2008 Nat Methods), so the attribution is wrong; free "
           "papers give the evoked decay only in figures (Hu, Tong & Kaplan 2013 eLife, PMC3743133; Bhattacharya et "
           "al. 2014 PLoS Genet, PMC4148232), and an evoked decay also includes release duration (Takayanagi-Kiya, "
           "Zhou & Jin 2016 eLife, PMC5102579), so it bounds a receptor's off-rate from above (7 Nov)",
}


def lit(qid):
    r = LIT[qid]
    basis = r["bound_basis"]
    if basis == "nematode_wide":                    # range across nematodes / generic, not this species
        basis = "guessed" if r["label"] == "guessed" else "measured_related"
    src = f"{r['source']} (param_ranges {qid})"
    if basis != "guessed" and weak_lit(qid):
        basis, src = "guessed", src + "; range basis guessed: " + weak_lit(qid)
    return float(r["bio_min"]), float(r["bio_max"]), r["label"], basis, src


def weak_lit(qid):
    """Why a research-file range is a guess, or "" when it is not weak (see WEAK_LIT, WEAK_QID)."""
    r = LIT.get(qid)
    if r is None:
        return ""
    if WEAK_LIT.search(f"{r['source']} {r['note']}"):
        return "the research file says its number was not read"
    return WEAK_QID.get(qid, "")


def centre(qid):
    """The literature range's log-midpoint, sqrt(min x max): the template when a ported value is outside the range
    and no source gives a value (Director, 5 Nov: a template at a bound is clipped by half its draws)."""
    return float(np.sqrt(float(LIT[qid]["bio_min"]) * float(LIT[qid]["bio_max"])))


def prior_for(t, lo, hi):
    if lo == hi:                                    # one value, e.g. a recording condition (noise_hold_mV)
        return "fixed", "", "", "one-point range: nothing to draw"
    if lo > 0 and hi / lo >= 10:
        return "loguniform", "", "", "guessed: log-uniform over the range"
    return "uniform", "", "", "guessed: uniform over the range"


def mech(id, name, layer, status, source, toggle="", neutral="", default=None, notes="", absent_reason=""):
    if default is None:
        default = "" if status == "absent" else "on"
    mechs.append(dict(id=id, name=name, layer=layer, status=status, toggle=toggle, neutral=neutral,
                      default=default, source=source, notes=notes, absent_reason=absent_reason))


def row(pid, mid, unit, template, lo, hi, *, proj, grain="global", applies_to="whole worm", n=1, tsrc="",
        label="guessed", basis="guessed", bsrc="guessed", prior=None, notes="", toggle="", table=None, url="",
        quote="", origin="brain"):
    pd_, pa, pb, pbasis = prior or prior_for(template, lo, hi)
    if label == "guessed" and unit != "flag" and hi > lo and (np.isclose(template, lo) or np.isclose(template, hi)):
        was, template = template, float(np.sqrt(lo * hi) if pd_ == "loguniform" else (lo + hi) / 2)
        tsrc += f"; at a bound ({was:g}), so moved to the range's {'log-' if pd_ == 'loguniform' else ''}midpoint"
    rows.append(dict(param_id=pid, mechanism_id=mid, grain=grain, applies_to=applies_to, unit=unit, n_values=n,
                     value_template=template, template_source=tsrc, bio_min=lo, bio_max=hi, bound_basis=basis,
                     bound_source=bsrc, bound_verified="unverified", prior_dist=pd_, prior_a=pa, prior_b=pb,
                     prior_basis=pbasis, label=label, fill_kind=ledger.FILL_KIND[label], source_project=proj,
                     precision_needed="not yet estimated", precision_method="", toggle=toggle, notes=notes,
                     plan_row=cat.plan_row(pid, mid), used_by_code="yes", source_url=url, source_quote=quote,
                     audit="", origin=origin))
    if table is not None:
        assert len(table) == n, (pid, len(table), n)
        values[pid] = table


def absent(pid, mid, unit, n, grain, applies_to, notes, lo="", hi="", bsrc=""):
    rows.append(dict(param_id=pid, mechanism_id=mid, grain=grain, applies_to=applies_to, unit=unit, n_values=n,
                     value_template="", template_source="", bio_min=lo, bio_max=hi, bound_basis="",
                     bound_source=bsrc, bound_verified="", prior_dist="", prior_a="", prior_b="", prior_basis="",
                     label="absent", fill_kind="absent", source_project="none",
                     precision_needed="not yet estimated", precision_method="", toggle="",
                     notes=notes, plan_row=cat.plan_row(pid, mid), used_by_code="yes", source_url="",
                     source_quote="", audit="", origin="brain"))


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
               "reversal (B5), synaptic decay (B3), conductance per EM synapse (B4) and per EM gap junction (C4; "
               "C4 itself is guessed, checked against the measured pair coupling C2); clipped elements are labelled "
               "guessed. Also fixes the Ca units bug (ca_pool notes) and sets celsius 20")
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
            lab = np.where(clipped != v, "guessed", "published_fit")
            src = [f"published fit, {BAAI_SRC}" if c == p else f"BAAIWorm {p:g} clipped to the literature range "
                   f"[{lo:g}, {hi:g}] ({overrides[q]})" for c, p in zip(clipped, v)]
            t = pd.DataFrame(dict(element=names, value=clipped, label=lab, source=src,
                                  source_project=np.where(clipped != v, "literature", "BAAIWorm"), ported=v,
                                  set_id=[set_of[n] for n in names]))
            sd = ("normal", float(np.median(clipped)), 5.0, "guessed: each element normal around its own value, "
                  "sd 5 mV, truncated") if q == "epas" else (
                "lognormal", float(np.median(clipped)), 0.35, "guessed: each element log-normal around its own "
                "value, sd 0.35 (factor 1.4), truncated")
            row(f"pas_{sec}_{q}", "passive", units[q], float(np.median(clipped)), lo, hi, grain="cell",
                applies_to=f"every neuron, {sec}", n=302, tsrc="median of the per-cell values (values table)",
                label="published_fit", proj="BAAIWorm", basis=basis, bsrc=bsrc, prior=sd, table=t,
                notes=f"{int((lab == 'guessed').sum())} of 302 ported values outside the literature range, clipped"
                if (lab == "guessed").any() else "")

    # muscles: BAAIWorm's passive muscle set; F1 (rest) bounds the leak reversal of a passive cell
    mn = sorted(m for m in muscles if bwm_name(m))
    mech("muscle_passive", "Body-wall muscle passive membrane (BAAIWorm muscle set)", "muscle", "have", BAAI_SRC,
         notes="BAAIWorm muscles are passive (all channel densities 0). BAAIWorm builds 96 cells; the model uses 95 "
               "(MCVL24 dropped: the worm has no ventral-left 24). Element names are interface.BWM_NAMES "
               "(brain_structure.bwm_name: MCDL01 -> dBWML1, checked against Cook 2019 NMJ edges)")
    for q, code in (("Ra", "A6"), ("cm", "A1"), ("gpas", None), ("epas", "F1")):
        v = np.array([muscles[n]["soma"][q] for n in mn], float)
        lo, hi, _, basis, bsrc = lit(code) if code else (1e-6, 1e-3, None, "guessed", "guessed")
        c = np.clip(v, lo, hi)
        lab = np.where(c != v, "guessed", "published_fit")
        src = [f"published fit, {BAAI_SRC}" if a == b else f"BAAIWorm {b:g} clipped to [{lo:g}, {hi:g}] ({code})"
               for a, b in zip(c, v)]
        row(f"mpas_{q}", "muscle_passive", units[q], float(np.median(c)), lo, hi, grain="muscle",
            applies_to="every body-wall muscle", n=len(mn), tsrc="median of the per-muscle values",
            label="published_fit", proj="BAAIWorm", basis=basis, bsrc=bsrc,
            table=pd.DataFrame(dict(element=[bwm_name(m) for m in mn], value=c, label=lab, source=src,
                                    source_project=np.where(c != v, "literature", "BAAIWorm"), ported=v,
                                    baaiworm_cell=mn)))

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
        t = pd.DataFrame(dict(element=names, value=v, label="published_fit", source=f"published fit, {BAAI_SRC}",
                              cengen_class=[cls[n] or "" for n in names], cengen_tpm=expr.round(2),
                              set_id=[set_of[n] for n in names]))
        row(f"dens_{ch}", mid, "nS/um2", float(np.median(v)), 0.0, hi, grain="cell", applies_to="every neuron, soma",
            n=302, tsrc="median of the per-cell values (values table)", label="published_fit", proj="BAAIWorm",
            basis="guessed",
            bsrc="guessed: 0 to 10x the largest ported density",
            prior=("lognormal", float(np.median(v)), 0.5, "guessed: each nonzero element log-normal around its own "
                   "value, sd 0.5; zero stays zero unless expression_map adds it"), table=t)
    mech("expression_map", "CeNGEN expression gates channel presence (zero density where no gene is detected; "
         "a class-median density where the gene is detected but the ported density is 0)", "channel", "have",
         "CeNGEN threshold 2 (Taylor et al. 2021)", toggle="expression_map", neutral="off", default="on")


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
                applies_to=f"every cell with {mod}", tsrc=f"published fit, {BAAI_SRC} mod/{mod}.mod",
                label="published_fit", proj="BAAIWorm", basis="guessed", bsrc=b, prior=("normal", val, (hi - lo) / 4, "guessed: normal around the published "
                                                 "value, sd a quarter of the range, truncated"))
    mech("ca_nanodomain", "Ca nanodomain at the channel mouth driving SLO-1/SLO-2 (Nicoletti et al. 2024)",
         "channel", "have", BAAI_SRC, notes=f"{len(tied)} Ca-channel constants inside the slo mods equal the "
                                            "egl19/unc2 values and are tied to those rows, not counted twice")
    for name, s in sorted(nano.items()):
        assert len(s) == 1, (name, s)
        (val, unit), = s
        lo, hi, b = kin_bounds(name, unit, val)
        row(f"nano_{name}", "ca_nanodomain", unit, val, lo, hi, tsrc=f"{BAAI_SRC} slo*.mod",
            label="guessed" if name == "gsc" else "published_fit", proj="BAAIWorm", basis="guessed", bsrc=b,
            notes="the mod says 'assumed equal to 40 pS'" if name == "gsc" else "")
    mech("ca_pool", "Intracellular Ca pool (cainternm)", "cell", "have", BAAI_SRC,
         notes="units bug as published: cai is in uM in the mod but NEURON's Nernst reads it as mM against cao 2 mM, "
               "so eca sits near +41 mV at rest instead of about +130 mV (measured on backhouse: eca 41.2 mV at cai "
               "0.065). Fixed under literature_overrides (known value, literature wins): the outside Ca is entered "
               "as 2000 (uM, the same units as cai), cai starts at caeq 0.05 uM, celsius 20; eca then follows Nernst "
               "at about +130 mV at rest (derived). literature_overrides off = as published")
    for name, val, unit in mods["cainternm"]:
        lo, hi, b = kin_bounds(name, unit, val)
        row(f"capool_{name}", "ca_pool", unit, val, lo, hi, tsrc=f"published fit, {BAAI_SRC} mod/cainternm.mod",
            label="published_fit", proj="BAAIWorm", basis="guessed", bsrc=b)
    mech("ions", "Ion reversal potentials, outside Ca, temperature", "cell", "have",
         "NEURON defaults (BAAIWorm never sets them)")
    for pid, unit, val, lo, hi, note in (
            ("ion_ek", "mV", -77.0, -100.0, -60.0, "NEURON default; BAAIWorm never sets it. Only kqt3 reads it: the other 11 "
             "K mods compute against a fixed -80 (baai_ek_mV; checked 6 Nov)"),
            ("ion_ena", "mV", 50.0, 20.0, 70.0, "NEURON default; set on every soma but no current reads it: nca declares "
             "READ ena and computes (v - 30) (baai_ena_nca_mV; checked 6 Nov)"),
            ("ion_cao", "mM", 2.0, 1.0, 5.0, "NEURON default; worm salines use 1-5 mM (guessed). With "
             "literature_overrides on it is entered as 2000 because cainternm keeps cai in uM. It sets only NEURON's Nernst "
             "eca, which no current reads (every Ca current uses a fixed +60, baai_eca_mV; checked 6 Nov)"),
            ("ion_celsius", "degC", 20.0, 15.0, 25.0, "NEURON default 6.3 as ported (literature_overrides off); 20 "
             "is a usual worm culture temperature (guessed). Here it only enters the Ca Nernst potential (no mod "
             "reads celsius; checked 5 Nov), and no current reads that eca (baai_eca_mV; checked 6 Nov)")):
        row(pid, "ions", unit, val, lo, hi, tsrc="NEURON default" if pid != "ion_celsius" else "guessed",
            label="guessed", proj="NEURON" if pid != "ion_celsius" else "ours", notes=note)
    return mods


def build_synapses(mods, st, conns):
    kind = dict(zip(st.names, st.kind))
    nset = {n for n, k in kind.items() if k == "neuron"}
    bwm = {n for n, k in kind.items() if k == "bwm"}
    chem_nn = [(st.names[a], st.names[b], k) for a, b, k in st.chem if st.names[a] in nset and st.names[b] in nset]
    gap_nn = [(st.names[a], st.names[b], k) for a, b, k in st.gap if st.names[a] in nset and st.names[b] in nset]
    nmj = [(st.names[a], st.names[b], k) for a, b, k in st.chem if st.names[a] in nset and st.names[b] in bwm]
    gap_bb = [(st.names[a], st.names[b], k) for a, b, k in st.gap if st.names[a] in bwm and st.names[b] in bwm]
    inh_pre = {n for n in nset if st.transmitter.get(n, set()) == {"gaba"}}
    # synapse kinetics: B-rows bound them; k sets the decay (tau = (1 - s_inf)/k, so 1/k is the longest decay)
    bounds = {"erev": {"exc": "B5", "inh": "B8"}, "Vth": "B1", "delta": "B2"}
    g_mod = {}
    for sk in ("exc", "inh"):
        mid = f"syn_{sk}"
        mech(mid, f"Graded chemical synapse, {'excitatory' if sk == 'exc' else 'inhibitory'} "
                  f"(neuron_to_neuron_{sk}_syn; also NMJ and muscle-to-neuron)", "synapse", "have", BAAI_SRC)
        for name, val, unit in parse_mod(BAAI / "mod" / f"neuron_to_neuron_{sk}_syn.mod"):
            if name == "weight":
                continue
            if name == "k":
                lo3, hi3, lab, basis, bsrc = lit("B3")
                lo, hi = 1.0 / hi3, 1.0 / lo3
                bsrc = f"1/decay, decay {lo3:g}-{hi3:g} ms: {bsrc}"
            elif name == "conductance":
                g_mod[sk] = val
                lo4, hi4, lab, basis, bsrc = lit("B4")
                lo, hi = lo4 / 1000.0, hi4 / 1000.0
            else:
                code = bounds[name][sk] if isinstance(bounds[name], dict) else bounds[name]
                lo, hi, lab, basis, bsrc = lit(code)
            t = float(np.clip(val, lo, hi))
            row(f"{mid}_{name}", mid, unit, t, lo, hi, tsrc=f"published fit, {BAAI_SRC}" if t == val else
                f"BAAIWorm {val:g} clipped to the literature range", label="published_fit" if t == val else "guessed",
                proj="BAAIWorm" if t == val else "literature", basis=basis, bsrc=bsrc,
                applies_to=f"every {sk} synapse" + (" placed by wiring=baaiworm" if name == "conductance" else ""),
                notes="" if t == val else f"ported value {val:g} {unit}")
    mech("gap", "Gap junctions (ohmic, symmetric)", "gap", "have", BAAI_SRC)
    lo, hi, lab, basis, bsrc = lit("C4")
    row("gap_weight", "gap", "uS", float(np.clip(1e-5, lo / 1000, hi / 1000)), lo / 1000, hi / 1000,
        tsrc="BAAIWorm 1e-5 uS (transform.py) clipped to the literature range", label="guessed", proj="ours",
        basis=basis, bsrc=bsrc, applies_to="every gap junction placed by wiring=baaiworm",
        notes="ported value 1e-5 uS = 0.01 nS per placed junction, below range C4; the template is 22x it. Range C4 "
              "is itself guessed (no measurement found), so the override is ours, not a cited value")
    mech("wiring", "Connectome: Cook et al. 2019, every pair (wiring=cook), or BAAIWorm's construction as published "
         "(wiring=baaiworm: tanh-compressed counts placed on segments in contact)", "synapse", "have",
         f"Cook et al. 2019 SI 5 (data/worm/structure); {BAAI_SRC} config2detailed", toggle="wiring",
         neutral="baaiworm = as published (port302a)", default="cook",
         notes="Default cook since 5 Nov (port302c passed G1-G3 as pre-registered, docs/worm/BRAIN_PORT.md section "
               "3; it saturated more than baaiworm on the old templates: 188 vs 141 neurons above -20 mV at 6 s; see "
               "open_questions: saturation). "
               "BAAIWorm's neuron-neuron counts (SI5-302.xlsx) equal Cook 2019 exactly (3709 chemical pairs, 20965 "
               "synapses; 1091 gap pairs; checked 5 Nov), but its construction places a site on only 2306 chemical "
               "and 599 gap pairs (single-synapse pairs round to 0 sites; other pairs have no neurite contact within "
               "1 um). Its neuron-muscle table is its own (552 binary pairs, 76 motor neurons; 337 are Cook edges, "
               "Cook has 956 pairs from 162 neurons) and it adds 175 muscle-to-neuron feedback synapses that are not "
               "anatomical (Cook has none; the sens_proprio layer covers proprioception). wiring=cook uses Cook for "
               "all of it: BAAIWorm's sites where it placed any, else one site on the nearest segment pair")
    for pid, val, lo, hi, note in (("syn_weight_nn", 0.5, 0.1, 1.0, "every neuron-neuron synapse (transform.py); "
                                    "bounds = BAAIWorm's own weight_range"),
                                   ("syn_weight_nmj", 1.0, 0.1, 2.0, "every neuron-to-muscle synapse"),
                                   ("syn_weight_mn", 0.1, 0.01, 1.0, "every muscle-to-neuron synapse")):
        row(pid, "wiring", "1", val, lo, hi, tsrc=f"{BAAI_SRC} transform.py", label="published_fit", proj="BAAIWorm",
            applies_to="wiring=baaiworm", notes=note)
    cnt = json.loads((BAAI / "config.json").read_text())["cnt_info"]
    for k, v in cnt.items():
        if isinstance(v, dict) or k == "inh_prob":
            continue
        lo, hi = sorted((v / 3, v * 3))
        row(f"build_{k}", "wiring", "1" if k != "length_per_seg" else "um", float(v), lo, hi,
            tsrc=f"{BAAI_SRC} config.json cnt_info", label="published_fit", proj="BAAIWorm",
            applies_to="wiring=baaiworm", notes="construction constant; how BAAIWorm chose it is not checked")

    # structure: Cook 2019 counts (measured) and BAAIWorm's own muscle tables (as published)
    def structure(pid, unit, recs, applies, label="measured", proj="literature", src="Cook et al. 2019 SI 5",
                  notes=""):
        t = pd.DataFrame([dict(element=e, value=k, label=label, source=src) for e, k in recs])
        row(pid, "wiring", unit, float(t.value.median()), 0 if unit == "flag" else 1, 1 if unit == "flag" else 1000,
            grain="connection", applies_to=applies, n=len(t), tsrc="per pair (values table)", label=label,
            proj=proj, basis="physical_limit", bsrc="counts", prior=("fixed", float(t.value.median()), "", "as built"),
            table=t, notes=notes)
    structure("wire_chem_contacts", "EM synapses", [(f"{a}>{b}", k) for a, b, k in chem_nn],
              "neuron-neuron chemical pairs")
    structure("wire_gap_contacts", "EM gap junctions", [(f"{a}-{b}", k) for a, b, k in gap_nn],
              "neuron-neuron gap pairs", notes="BAAIWorm's sheet also has 14 self pairs (a cell to itself); not used")
    structure("wire_nmj_contacts", "EM synapses", [(f"{a}>{b}", k) for a, b, k in nmj], "neuron-to-muscle pairs")
    structure("wire_bwm_gap_contacts", "EM gap junctions", [(f"{a}-{b}", k) for a, b, k in gap_bb],
              "muscle-muscle gap pairs")
    mus = {r for r in conns.post.unique() if r.startswith("MC") and r not in ("MCL", "MCR")}
    b_nmj = sorted({(a, b) for a, b in zip(conns.pre, conns.post) if b in mus and a not in mus})
    b_mn = sorted({(a, b) for a, b in zip(conns.pre, conns.post) if a in mus and b not in mus})
    structure("wire_nmj_baaiworm", "flag", [(f"{a}>{b}", 1) for a, b in b_nmj], "neuron-to-muscle pairs, "
              "wiring=baaiworm", label="published_fit", proj="BAAIWorm", src="BAAIWorm neuron_muscle.xlsx",
              notes="BAAIWorm muscle names; 6 pairs go to MCVL24, which the worm does not have")
    structure("wire_mn_baaiworm", "flag", [(f"{a}>{b}", 1) for a, b in b_mn], "muscle-to-neuron pairs, "
              "wiring=baaiworm", label="published_fit", proj="BAAIWorm", src="BAAIWorm muscle_neuron.xlsx",
              notes="BAAIWorm's proprioceptive feedback stand-in (its sheet cites Wen 2012, Krieg 2022); not anatomical")

    # per-pair strengths: a shared default per pair (guessed placeholder), BAAIWorm's network average where it
    # exists, clipped to the literature range. The pair's total is this x its Cook count (wiring=cook).
    nn_syn = conns[(conns.category == "syn") & conns.pre.isin(nset) & conns.post.isin(nset)]
    sites = Counter(zip(nn_syn.pre, nn_syn.post))
    em = {s: sum(k for a, _, k in chem_nn if (a in inh_pre) == (s == "inh")) for s in ("exc", "inh")}
    tot = {"exc": nn_syn.weight[nn_syn.weight > 0].sum() * g_mod["exc"] * 1000,
           "inh": -nn_syn.weight[nn_syn.weight < 0].sum() * g_mod["inh"] * 1000}
    per_em = {s: tot[s] / em[s] for s in tot}
    lp = ("lognormal", None, 0.5, "guessed: a shared factor per row, log-normal sd 0.5 around the default, "
          "truncated (the spread across pairs is unknown)")

    def pair_row(pid, mid, unit, pairs, ported_of, qid, applies, notes, toggle="", extra=None):
        """Ported value where it is inside the literature range, else the range's log-midpoint (not its bound,
        so a shared draw is not clipped half the time). A range that is itself guessed makes the value ours."""
        lo, hi, lab, basis, bsrc = lit(qid)
        c, own = centre(qid), lab == "guessed"
        recs = []
        for i, (a, b, k) in enumerate(pairs):
            pv = ported_of(a, b)
            inside = lo <= pv <= hi
            v = float(pv if inside else c)
            recs.append(dict(element=f"{a}>{b}" if mid != "gap" and "gap" not in pid else f"{a}-{b}", value=v,
                             label="guessed", source=f"shared default: {pv:.3g} {unit}" if inside else
                             f"shared default: log-midpoint {c:.3g} of range {qid} [{lo:g}, {hi:g}]; BAAIWorm's "
                             f"ported {pv:.3g} is outside ({c / pv:.0f}x)",
                             source_project="BAAIWorm" if inside else ("ours" if own else "literature"), ported=pv,
                             n_em=k, **(extra(a, b) if extra else {})))
        t = pd.DataFrame(recs)
        if own:
            notes += f". Range {qid} is itself guessed (no measurement found), so this value is ours"
        row(pid, mid, unit, float(t.value.median()), lo, hi, grain="connection", applies_to=applies, n=len(t),
            tsrc="shared default per pair (values table)", label="guessed",
            proj=t.source_project.mode()[0], basis=basis, bsrc=bsrc,
            prior=(lp[0], float(t.value.median()), lp[2], lp[3]), notes=notes, toggle=toggle, table=t)
        return t

    pair_row("syn_strength_per_pair", "wiring", "nS per EM synapse", chem_nn,
             lambda a, b: per_em["inh" if a in inh_pre else "exc"], "B4",
             "neuron-neuron chemical pairs (wiring=cook)",
             f"ported = BAAIWorm's network average, placed |weight| x conductance / Cook count: "
             f"{per_em['exc']:.3g} nS (excitatory), {per_em['inh']:.3g} nS (inhibitory) per EM synapse",
             extra=lambda a, b: dict(baaiworm_sites=sites.get((a, b), 0), inhibitory_by_transmitter=int(a in inh_pre)))
    gj = conns[(conns.category == "gj") & conns.pre.isin(nset) & conns.post.isin(nset)]
    gsites = Counter(tuple(sorted(p)) for p in zip(gj.pre, gj.post))
    g_per_em = (gj.weight.abs().sum() / 2) * 1000 / sum(k for _, _, k in gap_nn)   # two halves per junction, nS
    pair_row("gap_strength_per_pair", "gap", "nS per EM gap junction", gap_nn, lambda a, b: g_per_em, "C4",
             "neuron-neuron gap pairs (wiring=cook)",
             f"ported = BAAIWorm's network average, placed junctions x 0.01 nS / Cook count = {g_per_em:.3g} nS",
             extra=lambda a, b: dict(baaiworm_sites=gsites.get(tuple(sorted((a, b))), 0) // 2))
    b_nmj_w = conns[conns.post.isin(mus) & ~conns.pre.isin(mus)]
    nmj_tot = (b_nmj_w.weight.clip(lower=0).sum() * g_mod["exc"] - b_nmj_w.weight.clip(upper=0).sum()
               * g_mod["inh"]) * 1000
    nmj_per_em = nmj_tot / sum(k for _, _, k in nmj)
    pair_row("nmj_strength_per_pair", "wiring", "nS per EM synapse", nmj, lambda a, b: nmj_per_em, "B4",
             "neuron-to-muscle pairs (wiring=cook)",
             f"ported = BAAIWorm's total neuron-to-muscle conductance / Cook's NMJ count = {nmj_per_em:.3g} nS")
    # Liu, Chen, Gaier, Joshi & Wang 2006 measured the pair's whole junctional conductance by dual whole-cell clamp;
    # param_ranges F11 (1 to 20 nS) was a guess with no number retrieved, so it is not used (7 Nov, wcatalog)
    lo, hi, basis = 0.05, 0.35, "measured_this_class"
    bsrc = ("Liu, Chen, Gaier, Joshi & Wang 2006 J Biol Chem 281:7881 (PMID 16434400), abstract: dual whole-cell "
            "clamp of neighbouring body-wall muscle cells; upper end measured (350 pS), lower end guessed")
    mech("bwm_coupling", "Gap junctions between neighbouring body-wall muscles (UNC-9), Cook 2019 pairs", "muscle",
         "have", "Cook et al. 2019 pairs; strength guessed inside Liu et al. 2006's <= 350 pS", toggle="bwm_coupling",
         neutral="off (BAAIWorm and c302 have no muscle coupling)", default="off")
    t = pd.DataFrame([dict(element=f"{a}-{b}", value=0.2, label="guessed", source="guessed inside Liu 2006",
                           source_project="ours", n_em=k) for a, b, k in gap_bb])
    row("bwm_gap", "bwm_coupling", "nS per pair", 0.2, lo, hi, grain="connection",
        applies_to="muscle-muscle gap pairs (Cook 2019)", n=len(t), tsrc="guessed inside the measured range, one "
        "value for every pair (the same 0.2 nS as muscle_bwm's bwm_gap_liu_nS, the default form)",
        label="guessed", proj="ours", basis=basis, bsrc=bsrc, prior=("uniform", "", "", "guessed: uniform"),
        url="https://pubmed.ncbi.nlm.nih.gov/16434400/",
        quote="The coupling was characterized by small (350 pS or less) junctional conductance (G(j))",
        notes="macroscopic coupling per neighbouring pair; not scaled by the EM count; was 5 nS in a guessed "
        "[1, 20] nS (param_ranges F11, whose number was never retrieved) until 7 Nov", table=t)

    # sign per presynaptic neuron (transmitter rule)
    names = sorted(nset)
    sgn = []
    for n in names:
        tr, src = st.transmitter.get(n, set()), st.transmitter_source.get(n, "none")
        lab = {"wang2024": "derived", "cengen": "inferred"}.get(src, "guessed")
        sgn.append(dict(element=n, value=int(tr == {"gaba"}), label=lab, source=f"{src}: {', '.join(sorted(tr)) or 'none'}",
                        source_project="literature" if src == "wang2024" else "ours"))
    t = pd.DataFrame(sgn)
    mech("syn_sign", "Synapse sign by presynaptic transmitter (GABA-only presynaptic neuron -> inhibitory)",
         "synapse", "have", "Wang et al. 2024 transmitter atlas, CeNGEN markers as fallback", toggle="sign_rule",
         neutral="allexc = BAAIWorm as published (every synapse excitatory)", default="transmitter")
    row("syn_inhibitory", "syn_sign", "flag", 0, 0, 1, grain="cell", applies_to="every neuron as presynaptic cell",
        n=302, tsrc="transmitter rule (values table)", label="derived", proj="literature", basis="physical_limit",
        bsrc="flag", prior=("bernoulli", round(float(t.value.mean()), 3), "", "fraction inhibitory under the rule; "
                            "only guessed elements are drawn"), table=t)
    # sign per pair, behind receptor_sign: Fenyves et al. 2020's published prediction where it gives + or -, else
    # our rule from the postsynaptic class's fast receptors in CeNGEN (guessed), else the transmitter rule
    fen = pd.read_csv(FENYVES)
    fen = dict(zip(fen.pre + ">" + fen.post, fen.polarity))
    # measured signs win over both (BRAIN_PORT 9): Roberts et al. 2016 photoactivated one cell while patching the
    # other; the evoked current reverses negative of the zero-current potential. "Likely monosynaptic" is the
    # authors' inference; their 6-7x AVB->AVA asymmetry is a model fit, so the strength template stays symmetric
    rob = "Roberts et al. 2016 eLife 5:e12572 (PMC4798983)"
    measured = {**{f"{a}>{b}": f"{rob} Fig. 6B-D: AVA and AVB inhibit each other (photoactivation plus patch, "
                               f"n = 9 and 17 for the two directions)"
                   for a in ("AVAL", "AVAR", "AVBL", "AVBR") for b in ("AVAL", "AVAR", "AVBL", "AVBR")
                   if a[:3] != b[:3]},
                **{f"ASH{x}>AVB{y}": f"{rob} Fig. 9C-D: ASH to AVB inhibitory" for x in "LR" for y in "LR"}}
    classes = set(st.cengen_classes)
    recs = []
    for a, b, k in chem_nn:
        cls = cengen_class(b, classes)
        tr = st.transmitter.get(a, set()) & set(RECEPTORS)
        ex = sum(st.expr(g, cls) for t_ in tr for g in RECEPTORS[t_][0]) if cls else 0.0
        ih = sum(st.expr(g, cls) for t_ in tr for g in RECEPTORS[t_][1]) if cls else 0.0
        if ex + ih > 0:
            v, src = int(ih > ex), f"CeNGEN {cls}: excitatory receptors {ex:.0f}, inhibitory {ih:.0f} TPM"
        else:
            v, src = int(st.transmitter.get(a, set()) == {"gaba"}), "transmitter rule (no receptor expression)"
        f = fen.get(f"{a}>{b}", "not in Fenyves")
        r = dict(element=f"{a}>{b}", value=v, label="guessed", source=src, source_project="ours",
                 rule="cengen" if ex + ih > 0 else "transmitter", fenyves=f, ours=v)
        if f in ("+", "-"):
            r.update(value=int(f == "-"), label="derived", source=f"Fenyves et al. 2020 S1 Data (NT+R): {f}",
                     source_project="literature", rule="fenyves")
        if f"{a}>{b}" in measured:
            r.update(value=1, label="measured", source_project="literature", rule="measured",
                     source=measured[f"{a}>{b}"] + (f"; overrides Fenyves 2020 ({f})" if f in ("+", "-") else
                                                    f"; Fenyves 2020: {f}"))
        r.update(disagree=int(f in ("+", "-") and int(f == "-") != v), flips=int(r["value"] != int(a in inh_pre)))
        recs.append(r)
    t = pd.DataFrame(recs)
    mech("receptor_sign", "Synapse sign by postsynaptic receptor: Fenyves et al. 2020's published prediction (NT+R) "
         "where it is + or -; else inhibitory where the postsynaptic class expresses more chloride-channel receptors "
         "(GluCl, ACC, UNC-49) for the presynaptic transmitter than cation-channel ones, in summed CeNGEN TPM (our "
         "guessed rule); the transmitter rule where it expresses neither", "synapse",
         "have", "Fenyves et al. 2020 PLoS Comput Biol 16:e1007974 S1 Data (CC BY); CeNGEN threshold 2 (Taylor et "
         "al. 2021), receptor families from WormBase", toggle="receptor_sign",
         neutral="off = the presynaptic transmitter rule", default="on",
         notes=f"{int((t.rule == 'measured').sum())} of {len(t)} pairs carry a measured sign (Roberts et al. 2016: "
               f"AVA<->AVB and ASH->AVB inhibitory; BRAIN_PORT 9), "
               f"{int((t.rule == 'fenyves').sum())} from Fenyves (+ or -), "
               f"{int((t.rule == 'cengen').sum())} from our CeNGEN rule, {int((t.rule == 'transmitter').sum())} from "
               f"the transmitter rule; Fenyves and our rule disagree on {int(t.disagree.sum())} of the "
               f"{int((t.rule == 'fenyves').sum())} (Fenyves used); {int(t.flips.sum())} pairs differ from the "
               f"transmitter rule. Fenyves calls {sum(1 for x in t.fenyves if x == 'complex')} pairs complex "
               f"(both signs; our rule used)")
    row("syn_sign_receptor", "receptor_sign", "flag", float(t.value.median()), 0, 1, grain="connection",
        applies_to="neuron-neuron chemical pairs", n=len(t),
        tsrc="measured (Roberts 2016) first, else Fenyves 2020, else receptor rule (values table)",
        label="guessed", proj="ours", basis="physical_limit", bsrc="flag",
        prior=("bernoulli", round(float(t.value.mean()), 3), "", "fraction inhibitory under the rule"), table=t)
    # innexin channels: per-EM gap conductance = open channels per EM contact x unitary conductance, and no junction
    # where a partner expresses no innexin in CeNGEN. At the templates it equals gap_strength_per_pair (neutral)
    INX = [g for g in st.genes if g in ("unc-7", "unc-9", "eat-5") or g.startswith("inx-")]
    lo1, hi1, _, basis1, bsrc1 = lit("C1")
    lo4, hi4 = lit("C4")[:2]
    gu = float(np.sqrt(lo1 * hi1))
    no = centre("C4") * 1000 / gu
    mech("innexin_identity", "Gap junctions as innexin channels: conductance per EM contact = open channels x innexin "
         "unitary conductance (one shared value; no per-innexin measurement found); no junction where a partner "
         "expresses no innexin in CeNGEN. wiring=cook neuron-neuron gaps only. Rectification by innexin pair is not "
         "modelled: 923 of 1091 pairs could pair UNC-7 with UNC-9 by expression, so expression does not pick out the "
         "rectifying ones", "gap", "have", f"CeNGEN threshold 2 (Taylor et al. 2021), {len(INX)} innexin genes; "
         "Bhattacharya et al. 2019 innexin atlas not yet used", toggle="innexin_identity",
         neutral="off = gap_strength_per_pair for every pair", default="on")
    row("gap_innexin_unitary", "innexin_identity", "pS", gu, lo1, hi1, grain="family",
        applies_to="every innexin (one shared value)", tsrc="log-midpoint of range C1", label="guessed", proj="ours",
        basis=basis1, bsrc=bsrc1, notes="Range C1 is itself guessed (no direct UNC-7/UNC-9 single-channel value "
        "found), so this value is ours")
    row("gap_open_channels_per_em", "innexin_identity", "channels", no, lo4 * 1000 / hi1, hi4 * 1000 / lo1,
        tsrc="C4 log-midpoint / C1 log-midpoint, so the toggle is neutral at the templates", label="guessed",
        proj="ours", basis="guessed", bsrc="range C4 / range C1 (both guessed)",
        notes="open innexin channels per EM-visible gap contact; no count found")
    recs, cmap = [], {n: cengen_class(n, set(st.cengen_classes)) for p_ in gap_nn for n in p_[:2]}
    for a, b, _ in gap_nn:
        ea, eb = ([g for g in INX if st.expr(g, cmap[n]) > 0] if cmap[n] else None for n in (a, b))
        ok = ea is None or eb is None or (bool(ea) and bool(eb))
        recs.append(dict(element=f"{a}-{b}", value=int(ok), label="derived", source="CeNGEN threshold 2 (1 = both "
                         "partners express an innexin, or a partner has no CeNGEN class)", source_project="literature",
                         innexins_a=" ".join(ea or []), innexins_b=" ".join(eb or [])))
    ti = pd.DataFrame(recs)
    row("gap_innexin_pair", "innexin_identity", "flag", 1.0, 0, 1, grain="connection",
        applies_to="neuron-neuron gap pairs (wiring=cook)", n=len(ti), tsrc="CeNGEN (values table)", label="derived",
        proj="literature", basis="physical_limit", bsrc="flag", prior=("fixed", "", "", "derived from expression"),
        notes=f"{int((ti.value == 0).sum())} of {len(ti)} pairs have a partner with no innexin detected", table=ti)
    return dict(neuron_chem_pairs=len(chem_nn), neuron_gap_pairs=len(gap_nn), nmj_pairs_cook=len(nmj),
                nmj_pairs_baaiworm=len(b_nmj), bwm_gap_pairs=len(gap_bb),
                chem_pairs_with_baaiworm_site=sum(1 for a, b, _ in chem_nn if sites.get((a, b))),
                gap_pairs_with_baaiworm_site=sum(1 for a, b, _ in gap_nn if gsites.get(tuple(sorted((a, b))))),
                receptor_sign_from_fenyves=int((t.rule == "fenyves").sum()),
                receptor_sign_from_cengen=int((t.rule == "cengen").sum()), receptor_sign_flips=int(t.flips.sum()),
                receptor_sign_fenyves_disagree=int(t.disagree.sum()),
                ported_nS_per_em=dict(syn_exc=per_em["exc"], syn_inh=per_em["inh"], gap=g_per_em, nmj=nmj_per_em))


def build_morphology():
    pts = 0
    for f in (BAAI / "model").glob("*.hoc"):
        if f.stem == "MuscleCell":
            continue
        pts += f.read_text().count("pt3dadd(")
    mech("morphology", "Cell morphologies (NEURON hoc, 3D points with diameters)", "cell", "have",
         f"{BAAI_SRC} model/*.hoc (from the OpenWorm / Virtual Worm NeuroML cells)")
    row("morph_xyz", "morphology", "um", 0.0, -1000.0, 1000.0, grain="compartment",
        applies_to="every 3D point of every cell", n=3 * pts, tsrc="BAAIWorm b99ca5a (Zhao et al. 2024 Nat Comput Sci 4:978), per point in third_party/baaiworm/model/*.hoc",
        label="derived", proj="BAAIWorm", basis="physical_limit", bsrc="body length about 1 mm",
        prior=("fixed", 0.0, "", "as ported"),
        notes="from the Virtual Worm 3D atlas, not an EM reconstruction of one animal")
    row("morph_diam", "morphology", "um", 0.5, 0.01, 20.0, grain="compartment", applies_to="every 3D point",
        n=pts, tsrc="BAAIWorm b99ca5a (Zhao et al. 2024 Nat Comput Sci 4:978), per point in model/*.hoc", label="derived", proj="BAAIWorm", basis="physical_limit",
        bsrc="guessed",
        prior=("fixed", 0.5, "", "as ported"))
    return pts


def build_c302_muscle():
    mech("muscle_active", "Body-wall muscle K and Ca channels (c302 C2, Boyle and Cohen 2008 style)", "muscle",
         "have", "c302 parameters_C2 (OpenWorm, MIT); third_party/c302", toggle="muscle_active", neutral="off",
         default="off", notes="on: c302's generated NEURON mods (gate ODEs in exact form for the 0.5 ms step, "
         "BRAIN_PORT section 6 M2) replace BAAIWorm's passive muscle membrane, values from these rows; reversals "
         "are fixed in the mods. As published the muscle is graded (rests at -28.6 mV, plateaus under current, no "
         "repetitive spikes), unlike real body-wall muscle's Ca action potentials (Gao and Zhen 2011)")
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
            label="published_fit", proj="c302", basis="guessed", bsrc=b, applies_to=r["applies_to"])
        n += 1
    return n


def build_layers(st):
    for mid, name, layer, default in brain_layers.MECHANISMS:
        if mid == "gap_rectification":                   # in the NEURON build, not a lumped layer
            mech(mid, name, layer, "have", "src/wormemu/nmodl/rectgap.mod (ours; BAAIWorm's junction with a "
                 "direction)", toggle=mid, neutral="off", default=default,
                 notes="on: the 86 Cook pairs between AVA, AVB, AVD, AVE, PVC and DA, VA, DB, VB pass current from "
                 "the motor neuron into the interneuron at the template conductance and the other way at template / "
                 "gap_rect_ratio. Direction measured for AVA-VA5 (Liu et al. 2017 Nat Commun 8:14818, paired "
                 "recording); the other classes by the class rule, inferred. Checks: BRAIN_PORT section 7")
            continue
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
                                     source=src2, source_project="literature"))
                else:
                    recs.append(dict(element=e, value=s.template, label=lab, source="template guess",
                                     source_project="literature" if s.lit and lab != "guessed" else "ours"))
            tab = pd.DataFrame(recs)
        row(s.id, s.mechanism, s.unit, s.template, lo, hi, grain=s.grain, applies_to=s.applies_to,
            n=len(el) if el else 1, tsrc=bsrc if s.lit and lab != "guessed" else "guessed (brain_layers.py)",
            label=lab, proj="literature" if s.lit and lab != "guessed" else "ours", basis=basis, bsrc=bsrc,
            notes=s.notes, table=tab, origin="layers")
    mech("other_cells", "Hypodermis, seam, excretory canal, coelomocytes, other glia", "organ", "absent",
         "none", absent_reason="no lumped model yet; no INTERFACE channel needs them this week")


RANGE_GUESSED = re.compile(r"(?i)\b(bounds?|range)\b[^;.]{0,80}\bguessed\b")


def off_by_default():
    """A brain or layer row whose mechanism is off by default (bwm_coupling, muscle_active, the lumped glia gain) is
    read only when a run turns that toggle on, so it is not a number the default model uses (7 Nov, wcatalog)."""
    off = {m["id"] for m in mechs if str(m.get("default", "")).strip() == "off"}
    for r in rows:
        if r["used_by_code"] == "yes" and r["mechanism_id"] in off and r["origin"] in ("brain", "layers"):
            r["used_by_code"] = "other form only"
            r["notes"] = (r["notes"] + "; " if r["notes"] else "") + (
                f"read only with toggle {r['mechanism_id']} = on (default off)")
        elif r["used_by_code"] == "yes" and (r["param_id"] in OVERWRITTEN or r["param_id"] in FORM_ONLY):
            r["used_by_code"] = "other form only"
            r["notes"] = (r["notes"] + "; " if r["notes"] else "") + (OVERWRITTEN.get(r["param_id"]) or
                                                                       FORM_ONLY[r["param_id"]])


# brain rows a default-on module overwrites before the first step, so the default model never uses their numbers
_DU = "mech/muscle_bwm.py (bwm_membrane = du2025, the default) "
OVERWRITTEN = {
    "mpas_gpas": _DU + "sets every muscle's pas.g to 0 (Du's leak replaces it); acts only with bwm_membrane = off",
    "mpas_epas": _DU + "zeroes the leak it belongs to; acts only with bwm_membrane = off",
    "mpas_cm": _DU + "sets cm from bwm_du_c_pF over the area; acts only with bwm_membrane = off",
}
# module rows read only by a named form that is not the default (checked in the module code, 7 Nov)
FORM_ONLY = {
    "met_f_fixed": "read only with met_feeding = fixed (default pumps; mech/metabolism.py)",
    "aex2_ec50_nM": "read only with nlp40_aex2 = direct (default release_only; mech/organs_intestine.py:465)",
    "aex2_gain_pA": "read only with nlp40_aex2 = direct (default release_only; mech/organs_intestine.py:465)",
    **{f"obs_{v}_{q}": f"read only with gcamp = {v} (default gcamp6s; mech/observation.py:145)"
       for v in ("gcamp6f", "gcamp7f") for q in ("kd_nM", "hill", "range", "thalf_ms")},
}


def build_registry():
    """Every registered mechanism module (src/wormemu/mech, B1's registry): its MECHANISMS and SPECS. A module
    mechanism with a layer's id takes it over; a Spec with an existing row's id replaces that row. The Spec's own
    label is the value's label (a `lit` code gives only the bounds); optional Spec fields: url, quote,
    source_project, n and values (element -> value)."""
    notes = []
    for name, mod in cat.registry():
        prow = getattr(mod, "PLAN_ROW", None)
        neutral = getattr(mod, "NEUTRAL", {})
        for t in getattr(mod, "MECHANISMS", []):
            mid, mname, layer, default = t[:4]
            if any(m["id"] == mid for m in mechs):
                mechs[:] = [m for m in mechs if m["id"] != mid]
                notes.append(f"{mid}: taken over by mech/{name}")
                # brain.py switches a taken-over layer off while the module is registered; its rows run only if the
                # module calls the old layer (a form "lumped", as neuromod's and homeostasis's) or a run leaves the
                # module out of the registry, so they are not numbers the default model uses.
                # FORMS is one tuple for the module or a dict per mechanism id
                forms = getattr(mod, "FORMS", ())
                forms = forms.get(mid, ()) if isinstance(forms, dict) else forms
                when = (f"toggle {mid} = lumped, or a registry without mech/{name}" if "lumped" in forms else
                        f"a registry without mech/{name} (the old layer then runs)")
                for r in rows:
                    if r["mechanism_id"] == mid and r["origin"] == "layers":
                        r["used_by_code"] = "other form only"
                        r["notes"] = (r["notes"] + "; " if r["notes"] else "") + (
                            f"read only with {when}; the default runs mech/{name}'s rows")
            r_ = prow.get(mid) if isinstance(prow, dict) else prow
            # the module's PLAN_ROW, else the catalog's own MECH_ROW entry, else a guess from the name
            mapped = cat.MECH_ROW.get(mid)
            cat.MECH_ROW[mid] = int(r_ or mapped or cat.guess_row(f"{name} {mid}") or 0)
            mech(mid, mname, layer, "have", f"src/wormemu/mech/{name}.py", toggle=mid,
                 neutral=neutral.get(mid, "off") if isinstance(neutral, dict) else str(neutral), default=default,
                 notes=f"registry module {name}" + ("" if r_ else "; PLAN row set by the catalog (MECH_ROW)" if mapped
                                                    else "; PLAN row guessed from the name by the catalog"))
        for s_ in getattr(mod, "SPECS", []):
            if s_.lit:
                lo, hi, _, basis, bsrc = lit(s_.lit)
            else:
                # the range basis is the Spec's own when it gives one; else guessed when the Spec's notes say its
                # range is ("range guessed", "bounds guessed: factor 3", "range x/2 to x2 (guessed)": a cited value
                # with a made-up spread; 7 Nov, 256 rows); else measured_related only when the source names a
                # citation, otherwise guessed (a range with no cited source is a guess)
                basis = getattr(s_, "bound_basis", "") or (
                    "guessed" if RANGE_GUESSED.search(s_.notes or "") else
                    "measured_related" if s_.label != "guessed" and cat.CITE.search(s_.source) else "guessed")
                lo, hi, bsrc = s_.lo, s_.hi, s_.source
                # a Spec that cites a weak research-file range in its source text inherits the weakness
                weak = [w for w in map(weak_lit, re.findall(r"param_ranges ([A-Z]\d+)", s_.source)) if w]
                if weak and basis != "guessed":
                    basis, bsrc = "guessed", f"{bsrc}; range basis guessed: {weak[0]}"
            lab = s_.label
            proj = getattr(s_, "source_project", "") or ("ours" if lab in ("guessed", "inferred") else "literature")
            el = getattr(s_, "values", None)
            n = len(el) if el else int(getattr(s_, "n", 1) or 1)
            tab = None if not el else pd.DataFrame(dict(element=list(el), value=[float(x) for x in el.values()],
                                                        label=lab, source=s_.source, source_project=proj))
            if any(r["param_id"] == s_.id for r in rows):
                rows[:] = [r for r in rows if r["param_id"] != s_.id]
                values.pop(s_.id, None)
                notes.append(f"{s_.id}: row replaced by mech/{name}")
            grain, snotes = s_.grain, s_.notes
            if grain not in ledger.GRAINS:
                # a grain outside the ledger's vocabulary (e.g. "transmitter (ach)", "touch cells") is a class of
                # cells or synapses; applies_to already names which, the Spec's own word is kept in the notes
                snotes = f"{snotes}; Spec grain {grain!r} read as class".lstrip("; ")
                notes.append(f"{s_.id}: grain {grain!r} read as class")
                grain = "class"
            row(s_.id, s_.mechanism, s_.unit, float(s_.template), lo, hi, grain=grain, applies_to=s_.applies_to,
                n=n, tsrc=s_.source, label=lab, proj=proj, basis=basis, bsrc=bsrc, notes=snotes, table=tab,
                url=getattr(s_, "url", ""), quote=getattr(s_, "quote", ""), origin=f"mech:{name}")
    return notes


def honest_row_labels():
    """A row with a values table is labelled no stronger than its weakest element (absent elements aside), in the
    order cat.LABEL_RANK. The literature clip (pas_*, mpas_*) relabels the elements it moves guessed and the mirror
    used the commonest element label, so a row could claim published_fit with every element guessed (pas_soma_cm,
    found by the independent audit, 7 Nov). The split stays in labels_by_element. Returns fill-log entries, kind
    element_labels."""
    log = []
    for r in rows:
        t = values.get(r["param_id"])
        if t is None or "label" not in t:
            continue
        labs = Counter(x for x in t.label if x != "absent")
        weak = cat.weakest_label(labs)
        if not weak or cat.LABEL_RANK.get(r["label"], 0) <= cat.LABEL_RANK[weak]:
            continue
        was, split = r["label"], ", ".join(f"{k} {v}" for k, v in labs.most_common())
        why = (f"row label {was} was stronger than its elements ({split}): a row is labelled as its weakest element, "
               f"the split is per element")
        r["label"], r["fill_kind"] = weak, ledger.FILL_KIND[weak]
        r["notes"] = (r["notes"] + "; " if r["notes"] else "") + f"relabel 7 Nov (independent audit): {why}"
        log.append(dict(param_id=r["param_id"], kind="element_labels", origin=r["origin"], n=1, pattern="",
                        was_label=was, new_label=weak, change=f"row label {was} -> {weak}", reason=why,
                        source="the row's own values table", url=""))
    return log


LUMPED_MIRROR = {"pep_ec50_nM": "pep_ec50", "ma_ec50_nM": "ma_ec50"}     # layer table -> mech/neuromod row prefix


def mirror_lumped():
    """The lumped neuromodulation form (brain_layers' per-pair table) and mech/neuromod's one-row-per-pair Specs
    hold the same EC50s. After the fills, a guessed table element takes its pair row's value and label when that
    row is not guessed. A mixed table's row takes its commonest element label; honest_row_labels then lowers it to
    the weakest. Returns
    fill-log entries, kind mirror."""
    by = {r["param_id"]: r for r in rows}
    log = []
    for pid, pre in LUMPED_MIRROR.items():
        t, r = values.get(pid), by.get(pid)
        if t is None or r is None:
            continue
        t["value"] = t["value"].astype(float)
        moved = Counter()
        for i, e in t.element.items():
            src = by.get(f"{pre}_{e.replace('>', '_')}_nM")
            if t.at[i, "label"] != "guessed" or src is None or src["label"] == "guessed":
                continue
            t.at[i, "value"] = float(src["value_template"])
            t.at[i, "label"], t.at[i, "source_project"] = src["label"], src["source_project"]
            t.at[i, "source"] = f"same pair as row {src['param_id']}: {src['template_source']}"
            moved[src["label"]] += 1
        if not moved:
            continue
        was = r["label"]
        r["label"] = t.label.value_counts().idxmax()
        r["fill_kind"] = ledger.FILL_KIND[r["label"]]
        keys = [k for e, lab in zip(t.element, t.label)
                if lab != "guessed" and (k := f"{pre}_{e.replace('>', '_')}_nM") in by]
        url, nu = Counter(by[k].get("source_url", "") for k in keys).most_common(1)[0]
        src = next(by[k]["template_source"] for k in keys if by[k].get("source_url", "") == url)
        r["notes"] = (r["notes"] + "; " if r["notes"] else "") + f"row source before the mirror: {r['template_source']}"
        r["template_source"] = (f"per element: the mech/neuromod pair rows {pre}_<ligand>_<receptor>_nM, each with "
                                f"its own source (values file); {nu} of {sum(moved.values())} cite the URL, e.g. {src}")
        r["source_url"] = url
        why = (f"the lumped form reads one EC50 per pair from this table; mech/neuromod's {pre}_<ligand>_<receptor>_nM "
               "rows are the same pairs with the literature values, so a guessed element takes its pair row's value")
        lo, hi = float(t.value.min()), float(t.value.max())
        if lo < r["bio_min"] or hi > r["bio_max"]:            # the old guessed range did not cover the measurements
            why += (f"; range [{r['bio_min']:g}, {r['bio_max']:g}] widened to [{min(lo, r['bio_min']):g}, "
                    f"{max(hi, r['bio_max']):g}] to cover them")
            r["bio_min"], r["bio_max"] = min(lo, r["bio_min"]), max(hi, r["bio_max"])
            r["bound_source"] = f"{r['bound_source']}, widened to the mirrored values"
        r["notes"] = (r["notes"] + "; " if r["notes"] else "") + f"mirror 6 Nov (catalog audit): {why}"
        for lab, n in moved.items():
            log.append(dict(param_id=pid, kind="mirror", origin=r["origin"], n=n, pattern="", was_label="guessed",
                            new_label=lab, change=f"{n} of {len(t)} elements guessed -> {lab}; row label {was} -> "
                            f"{r['label']}", reason=why, source=f"mech/neuromod rows {pre}_*_nM", url=""))
    return log


def sensitivity():
    """The range-end runs (docs/worm/BRAIN_PORT.md section 5) into precision_method: what each end does to the count of
    neurons above -20 mV (D8 base). A sensitivity, not a precision: there is no correctness target yet."""
    f = ROOT / "data/worm/brain_runs/sens_summary.json"
    if not f.exists():
        return
    runs = json.loads(f.read_text())
    base = next(r["above"] for r in runs if r["run"] == "D8")
    by = defaultdict(list)
    for r in runs:
        for kv in r["set"]:
            k, v = kv.split("=")
            by[k].append((float(v), r["above"], r["run"]))
    for r in rows:
        if r["param_id"] in by:
            got = sorted(by[r["param_id"]])
            n = [x[1] for x in got] + [base]
            r["precision_method"] = ("range-end sensitivity at D8, BRAIN_PORT.md section 5 (measured, report-only): "
                                     f"neurons above -20 mV at 6 s, {base} at the template; "
                                     + "; ".join(f"{v:g} gives {k} ({run})" for v, k, run in got)
                                     + f"; swing {max(n) - min(n)}")


def export(led, extra, csum=None):
    c = ledger.counts(led)
    by = c["by_label"]
    known = sum(by.get(k, 0) for k in ("measured", "published_fit", "derived", "inferred"))
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
    src_fill = {"all": defaultdict(Counter), "physiology": defaultdict(Counter)}
    for r in prow:
        for lab, n in c["by_param"][r["param_id"]].items():
            if r["kind"] == "physiology":
                phys[lab] += n
    for r in led.parameters.itertuples():
        t = led.values(r.param_id)
        if t is None:
            cells = {(r.source_project, r.fill_kind): int(r.n_values)}
        else:
            sp = t.source_project if "source_project" in t else pd.Series(r.source_project, index=t.index)
            cells = pd.DataFrame(dict(s=sp, f=t.label.map(ledger.FILL_KIND))).value_counts().to_dict()
        for (sp, fk), n in cells.items():
            src_fill["all"][sp][fk] += int(n)
            if not r.param_id.startswith(STRUCTURE_ROWS):
                src_fill["physiology"][sp][fk] += int(n)
    pk = sum(phys.get(k, 0) for k in ("measured", "published_fit", "derived", "inferred"))
    out = dict(
        generated_by="scripts/worm/build_ledger.py",
        generated_at=subprocess.run(["date", "+%Y-%m-%d %H:%M %Z"], capture_output=True, text=True).stdout.strip(),
        definitions=dict(
            known="measured + published_fit + derived + inferred (published_fit: a value another project fitted "
                  "or chose and published, e.g. BAAIWorm's densities; inferred: inferred by this project)",
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
        source_by_fill_kind={k: {sp: dict(v) for sp, v in d.items()} for k, d in src_fill.items()},
        open_questions=OPEN_QUESTIONS, by_grain=c["by_grain"], mechanisms=mrows, parameters=prow, build_notes=extra,
        catalog=dict(note="the one catalog (data/worm/model/catalog.csv): model rows above plus the body ledger and "
                          "the slots (numbers a PLAN row's published model needs that no code reads yet). Counts are "
                          "numbers (elements), not rows, unless the key says rows", **(csum or {})))
    (ROOT / "docs/worm/ledger.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def main():
    st = load_structure()
    conns = pd.read_csv(ROOT / "data/worm/brain_runs/port302a/connections.csv")
    neurons, muscles = ported_cells()
    build_passive_and_channels(neurons, muscles, st)
    mods = build_kinetics()
    wiring = build_synapses(mods, st, conns)
    pts = build_morphology()
    n_c302 = build_c302_muscle()
    build_layers(st)
    reg_notes = build_registry()
    off_by_default()
    sensitivity()
    body_mechs, body = cat.body_rows()
    used = {r["param_id"] for r in rows} | {r["param_id"] for r in body if r["used_by_code"] == "yes"}
    live = {m["id"] for m in mechs if m["status"] != "absent"}
    slot_rows, replaced, slot_mechs = cat.slots(used, live, {m["id"] for m in [*mechs, *body_mechs]})
    for r in [*body, *slot_rows]:
        r["fill_kind"] = ledger.FILL_KIND.get(r["label"], r["label"])
    before = cat.label_tally([*rows, *body, *slot_rows], values)
    fill_log = cat.apply_fills([*rows, *body, *slot_rows], values, ledger.FILL_KIND)
    fill_log += mirror_lumped()
    fill_log += honest_row_labels()
    crows = cat.build(rows, values, mechs, body_mechs, body, slot_rows, slot_mechs, ledger.FILL_KIND)
    audit_of = {c["id"]: c["audit"] for c in crows}
    for r in rows:
        r["audit"] = audit_of[r["param_id"]]
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
    extra = dict(**wiring, morph_points=pts, c302_muscle_rows=n_c302, registry=reg_notes)
    hidden = cat.hidden_summary()
    csum = cat.summary(crows, replaced, fill_log, hidden, before)
    cat.write(crows, csum, [*mechs, *body_mechs, *slot_mechs])
    out = export(led, extra, csum)
    print(json.dumps(csum["totals"], indent=1))
    print("audit:", json.dumps(csum["audit"]["rows_ok"]), "ok,", csum["audit"]["rows_with_problems"], "with problems;",
          "orphan notes", csum["audit"]["orphan_notes"], "orphan fills", csum["audit"]["orphan_fills"])
    print(json.dumps(out["totals"], indent=1))
    print(json.dumps(out["totals_physiology"], indent=1))
    print(json.dumps(out["source_by_fill_kind"]["physiology"], indent=1))
    print(json.dumps(extra, default=float))


if __name__ == "__main__":
    main()
