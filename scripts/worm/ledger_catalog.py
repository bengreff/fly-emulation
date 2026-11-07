"""The worm's one parameter catalog (C wcatalog, 6 Nov): every number the model uses and every number a PLAN row's
published model needs, in one table, each row audited. Called by build_ledger.py; not run on its own.

Inputs, beside what build_ledger already parses:
  src/wormemu/mech/        the mechanism registry (REGISTRY; each module's MECHANISMS and SPECS), when it exists
  data/worm/ledger/        the body ledger (metaworm_parameters.csv, metaworm_mechanisms.json, built from the body code)
  data/worm/catalog/slots.csv  hand list: the parameters each PLAN row's published model needs (PORT_SOURCES_*.md,
                           PLAN.md), with the best value our research files give; used_by_code = slot only until a
                           builder's Spec replaces the slot (same id, or the id is in the slot's `match` column)
  data/worm/catalog/fills.csv  literature fills of guessed rows (literature wins): the new value, label and citation
  data/worm/catalog/audit_notes.csv  the read audit: per-row findings that the scripted checks cannot see

Outputs: data/worm/model/catalog.csv (every row), viewer/worm/catalog_data.json (the catalog page's data),
docs/worm/CATALOG.md (the summary). The model's own ledger (data/worm/model/parameters.csv, what the brain samples)
keeps only rows the code reads: brain, layers and registry rows. Body rows and slots live in the catalog only.
"""
from __future__ import annotations

import fnmatch
import importlib
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CAT = ROOT / "data" / "worm" / "catalog"
BODY = ROOT / "data" / "worm" / "ledger"

PLAN_ROWS = {
    1: "Cell inventory", 2: "Morphology and compartments", 3: "Channel presence per class (CeNGEN)",
    4: "Channel kinetics", 5: "Channel densities, Cm, leak, Ra", 6: "Calcium handling", 7: "Chemical synapses",
    8: "Gap junctions per innexin", 9: "Neuropeptides", 10: "Monoamines", 11: "Glia",
    12: "Body-wall muscle and excitation-contraction", 13: "Pharynx", 14: "Intestine and defecation",
    15: "Egg-laying", 16: "Other non-neural cells", 17: "Sensory transduction", 18: "Slow intracellular signalling",
    19: "Activity-dependent gene expression and homeostatic tuning", 20: "Metabolism", 21: "Body (3D soft body)",
    22: "Environment", 23: "Observation models", 24: "Synaptic plasticity and learning substrates",
    25: "Temperature dependence of rates", 26: "Noise", 27: "Ion pumps and concentration homeostasis",
    28: "Sleep neurons",
}
# mechanism id -> PLAN row (MECHANISMS_AUDIT.md rows 1-23; rows 24-28 added 6 Nov). homeostasis is N7 (row 19), not
# row 18 as the audit of 5 Nov grouped it
MECH_ROW = {
    "literature_overrides": 5, "passive": 5, "expression_map": 3, "ca_nanodomain": 6, "ca_pool": 6, "ions": 5,
    "syn_exc": 7, "syn_inh": 7, "wiring": 7, "syn_sign": 7, "receptor_sign": 7, "gap": 8, "innexin_identity": 8,
    "gap_rectification": 8, "morphology": 2, "muscle_passive": 12, "muscle_active": 12, "bwm_coupling": 12,
    "muscle_ca": 12, "muscle_activation": 12, "peptides": 9, "monoamines": 10, "glia": 11, "pharynx": 13,
    "defecation": 14, "egg_laying": 15, "metabolism": 20, "gcamp": 23, "homeostasis": 19, "slow_signalling": 18,
    "other_cells": 16,
    "MB1": 21, "MB2": 21, "MB3": 12, "MB4": 21, "MB5": 22, "MB6": 22, "MB7": 22, "MB8": 22, "MB9": 21, "MB10": 21,
    "MB11": 23, "MB12": 13,
}
PARAM_ROW = {"ion_celsius": 25}
# for registry modules that do not say: keyword in the module or mechanism id -> row (first match wins)
KEYWORD_ROW = [("sleep", 28), ("pump", 27), ("atpase", 27), ("noise", 26), ("temperature", 25), ("q10", 25),
               ("plastic", 24), ("stp", 24), ("habituat", 24), ("learn", 24), ("peptide", 9), ("monoamine", 10),
               ("glia", 11), ("muscle", 12), ("pharyn", 13), ("intestin", 14), ("defecat", 14), ("egg", 15),
               ("vulva", 15), ("hypoderm", 16), ("excretory", 16), ("coelomocyte", 16), ("other_cells", 16),
               ("senses", 17), ("sens_", 17), ("slow", 18), ("homeost", 19), ("gene", 19), ("metabol", 20),
               ("body", 21), ("environment", 22), ("observ", 23), ("gcamp", 23), ("receptor", 7), ("syn", 7),
               ("gap", 8), ("innexin", 8)]
CATALOG_ONLY = ("body", "slot", "hidden", "scene")   # rows the model ledger does not carry
LABEL_MAP = {"published": "published_fit"}           # the body ledger's word for a published fit


def plan_row(pid: str, mid: str) -> int:
    if pid in PARAM_ROW:
        return PARAM_ROW[pid]
    if pid.startswith("kin_"):
        return 4
    if mid in MECH_ROW:
        return MECH_ROW[mid]
    if mid.startswith(("ch_",)):
        return 5
    if mid.startswith("sens_"):
        return 17
    return guess_row(mid) or 0


def guess_row(name: str) -> int | None:
    n = name.lower()
    return next((r for k, r in KEYWORD_ROW if k in n), None)


# ---------------------------------------------------------------------------------------------------------- registry
def registry():
    """(module name, module) for every registered mechanism module; [] until B1's registry lands."""
    try:
        reg = importlib.import_module("wormemu.mech")
    except ImportError:
        return []
    names = list(getattr(reg, "REGISTRY", []))
    return [(n.rsplit(".", 1)[-1], m) for n, m in zip(names, reg.modules(names))]


# ---------------------------------------------------------------------------------------------------------- the body
def body_rows():
    """The body ledger's rows in catalog form (catalog only: the body code reads its own numbers)."""
    mj = json.loads((BODY / "metaworm_mechanisms.json").read_text())["mechanisms"]
    mechs = []
    for m in mj:
        sw = "; ".join(f"{s['name']} ({'/'.join(s.get('available', []))} of {'/'.join(s.get('options', []))})"
                       for s in m.get("switch", []))
        mechs.append(dict(id=m["id"], name=m["name"], layer="body", status=m.get("status", "partial"),
                          toggle=sw, neutral="; ".join(s.get("neutral", "") for s in m.get("switch", [])),
                          default="on", source=m.get("source", ""), notes=m.get("notes", ""),
                          absent_reason=m.get("absent_reason", "")))
    out = []
    p = pd.read_csv(BODY / "metaworm_parameters.csv", keep_default_na=False)
    for r in p.to_dict("records"):
        lab = LABEL_MAP.get(r["label"], r["label"])
        v = pd.to_numeric(pd.Series([r["value_used"]]), errors="coerce")[0]
        src = r["source"]
        proj = "BAAIWorm" if "MetaWorm" in src or "BAAIWorm" in src else ("ours" if lab == "guessed" else
                                                                            "literature")
        notes = r["notes"]
        if pd.isna(v) and r["value_used"]:
            notes = f"value: {r['value_used']}. {notes}"
        out.append(dict(
            param_id=r["param_id"], mechanism_id=r["mechanism_id"], grain=r["grain"] or "global",
            applies_to=r["applies_to"], unit=r["unit"], n_values=1, value_template=v,
            template_source=src, bio_min=_num(r["bio_min"]), bio_max=_num(r["bio_max"]),
            bound_basis=r["bound_basis"], bound_source=r["bound_source"], bound_verified="unverified",
            prior_dist=r["prior_dist"], prior_a=r["prior_a"], prior_b=r["prior_b"], prior_basis=r["prior_basis"],
            label=lab, source_project=proj, precision_needed="not yet estimated",
            precision_method="", toggle="", notes=notes, plan_row=plan_row(r["param_id"], r["mechanism_id"]),
            used_by_code="yes" if r["used_in_body"] == "yes" else "slot only", source_url="", source_quote="",
            audit="", origin="body", body_lit_check=r["lit_check"], si_factor=r["si_factor"]))
    return mechs, out


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


# ----------------------------------------------------------------------------------------------------------- slots
SLOT_COLUMNS = ["param_id", "plan_row", "mechanism_id", "mechanism_name", "grain", "applies_to", "n_values", "unit",
                "value_template", "bio_min", "bio_max", "label", "bound_basis", "source", "source_url",
                "source_quote", "source_project", "notes", "match", "used"]


def slots(used_ids: set[str], live_mechs: set[str], known_mechs: set[str]):
    """Slot rows (scripts/worm/catalog_slots.py, copied to data/worm/catalog/slots.csv) not yet replaced by a row the
    code reads. A slot is replaced when a used row has its id, or one of the ids in its `match` column
    (space-separated; a mechanism id there matches any row of a mechanism that has code)."""
    import catalog_slots
    s = pd.DataFrame(catalog_slots.SLOTS, columns=SLOT_COLUMNS)
    CAT.mkdir(parents=True, exist_ok=True)
    s.to_csv(CAT / "slots.csv", index=False)
    s = pd.DataFrame(catalog_slots.SLOTS + catalog_slots.HIDDEN + scene_slots(), columns=SLOT_COLUMNS)
    rows, replaced, mechs = [], [], {}
    for r in s.to_dict("records"):
        keys = {r["param_id"], *str(r["match"]).split()}
        hit = sorted(k for k in keys if k in used_ids or k in live_mechs)
        if hit:
            replaced.append((r["param_id"], " ".join(hit)))
            continue
        lab = r["label"] or "absent"
        v, lo, hi = _num(r["value_template"]), _num(r["bio_min"]), _num(r["bio_max"])
        if r["mechanism_id"] == "scene_field":
            mechs.setdefault("scene_field", dict(
                id="scene_field", name=r["mechanism_name"], layer="body", status="have", toggle="", neutral="",
                default="", source="src/wormemu/body/scene.py", notes="plate field presets the body's scene "
                "computes; each Param carries value, unit, label, range and source", absent_reason=""))
        elif r["mechanism_id"] not in known_mechs:
            mechs.setdefault(r["mechanism_id"], dict(
                id=r["mechanism_id"], name=r["mechanism_name"], layer="slot", status="absent", toggle="", neutral="",
                default="", source=r["source"].split(";")[0], notes="slot mechanism: the published model the PLAN "
                "row needs; no code yet", absent_reason="not built yet (slot)"))
        rows.append(dict(
            param_id=r["param_id"], mechanism_id=r["mechanism_id"], grain=r["grain"] or "global",
            applies_to=r["applies_to"], unit=r["unit"], n_values=int(r["n_values"] or 1), value_template=v,
            template_source=r["source"], bio_min=lo, bio_max=hi,
            bound_basis=r["bound_basis"] or ("guessed" if lab == "guessed" else ""),
            bound_source=r["source"] if not np.isnan(lo) else "", bound_verified="unverified", prior_dist="",
            prior_a="", prior_b="", prior_basis="", label=lab,
            source_project=r["source_project"] or ("none" if lab == "absent" else "literature"),
            precision_needed="not yet estimated", precision_method="", toggle="", notes=r["notes"],
            plan_row=int(r["plan_row"]), used_by_code=r["used"] or "slot only", source_url=r["source_url"],
            source_quote=r["source_quote"], audit="",
            origin="hidden" if str(r["used"]).startswith("hard-coded") else "scene" if r["param_id"].startswith(
                "scene_") else "slot"))
    return rows, replaced, list(mechs.values())


SCENE_LABEL = {"published": "measured"}    # scene.py's "published" = a protocol value from a paper (assay setting)


def scene_slots() -> list[dict]:
    """The chemotaxis plate presets (src/wormemu/body/scene.py PRESETS, PARAMS): each Param carries its own value,
    unit, label, range and source, chosen per run. Catalog rows scene_<preset>_<name>, used when that field runs."""
    try:
        from wormemu.body import scene
    except Exception:  # noqa: BLE001 (no body code in this checkout: no scene rows)
        return []
    out = []
    items = [(f"{k}_{n}", k, p) for k, d in scene.PRESETS.items() for n, p in d.items()]
    items += [(n, "plate", p) for n, p in scene.PARAMS.items()]
    for name, preset, p in items:
        lab = SCENE_LABEL.get(p.label, p.label)
        out.append(dict(
            param_id=f"scene_{name}", plan_row=22, mechanism_id="scene_field",
            mechanism_name="Chemotaxis plate field presets (src/wormemu/body/scene.py)", grain="global",
            applies_to=f"{preset} field preset" if preset != "plate" else "the plate (all fields)", n_values=1,
            unit=p.unit, value_template=p.value, bio_min="" if p.low is None else p.low,
            bio_max="" if p.high is None else p.high, label=lab,
            bound_basis="" if p.low is None else ("guessed" if lab == "guessed" else "measured_related"),
            source=p.source, source_url="", source_quote="", source_project="ours" if lab == "guessed" else "literature",
            notes=f"scene.py Param (label there: {p.label}); used when the run picks this preset", match="",
            used="yes"))
    return out


# ----------------------------------------------------------------------------------------------------------- links
BAAI = "https://github.com/Jessie940611/BAAIWorm/blob/b99ca5ab9c00aef739fceb1cf007bc50b06f2ccc/"
# where a vendored file sits upstream (third_party/baaiworm/NOTICE.md, third_party/metaworm/UPSTREAM.md)
BAAI_FILES = [(r"mod/([a-z0-9_]+\.mod)", "eworm/components/mechanism/modfile/{}"),
              (r"\b(slo\*\.mod|[a-z0-9_]+\.mod)", "eworm/components/mechanism/modfile"),
              (r"config\.json", "eworm/network/config.json"), (r"transform\.py", "eworm/network/transform.py"),
              (r"\.hoc", "eworm_learn/components/model"), (r"cell_param", "eworm/components/param/cell"),
              (r"fem/World\.cpp", "Metaworm/sim/fem/World.cpp"), (r"Worm(::[A-Za-z]+|\.cpp)", "Metaworm/sim/Worm.cpp"),
              (r"Muscle\.cpp", "Metaworm/sim/Muscle.cpp"), (r"Environment\.cpp", "Metaworm/sim/Environment.cpp"),
              (r"KeyWorm", "Metaworm/sim/KeyWorm.cpp"), (r"worm_nerve_cord", "Metaworm/data/worm_nerve_cord.muscle"),
              (r"neuron_muscle|connection", "eworm/components/param/connection")]
# papers the ledger cites without a link, resolved through Europe PMC (6 Nov, wcatalog); first match wins
PAPERS = [
    (r"Tanimoto et al\.? 2017", "https://elifesciences.org/articles/21629"),
    (r"Kunitomo (and|&) Iino 2013", "https://doi.org/10.1038/ncomms3210"),
    (r"Luo et al\.? 2014 Neuron", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4082684/"),
    (r"Ramot.{0,40}2008", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2587641/"),
    (r"Kimura.{0,40}2004", "https://doi.org/10.1016/j.cub.2004.06.060"),
    (r"Clark.{0,40}2006", "https://pmc.ncbi.nlm.nih.gov/articles/PMC6674189/"),
    (r"Zimmer.{0,20}2009", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2760494/"),
    (r"Busch.{0,20}2012", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3564487/"),
    (r"Wen.{0,20}2012", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3508473/"),
    (r"Raizen.{0,20}1994", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4460247/"),
    (r"Avery & Horvitz 1990", "https://doi.org/10.1002/jez.1402530305"),
    (r"Thomas 1990", "https://pmc.ncbi.nlm.nih.gov/articles/PMC1203977/"),
    (r"Collins.{0,20}2016", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5142809/"),
    (r"Waggoner.{0,40}1998", "https://doi.org/10.1016/s0896-6273(00)80527-9"),
    (r"Goodman, Hall, Avery & Lockery 1998", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4444786/"),
    (r"L'Etoile.{0,20}2002", "https://doi.org/10.1016/s0896-6273(02)01066-8"),
    (r"Chen et al\. 2013", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3777791/"),
    (r"Chalasani.{0,20}2007", "https://doi.org/10.1038/nature06292"),
    (r"Suzuki et al\. 2008", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2984562/"),
    (r"O'Hagan.{0,30}2005", "https://doi.org/10.1038/nn1362"),
    (r"Starich.{0,20}2009", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2694797/"),
    (r"Kawano.{0,20}2011", "https://doi.org/10.1016/j.neuron.2011.09.005"),
    (r"Liu et al\. 2017", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5364397/"),
    (r"Liu et al\. 2013", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3793928/"),
    (r"Wicks.{0,30}1996", "https://pmc.ncbi.nlm.nih.gov/articles/PMC6578605/"),
    (r"Boyle, Berri & Cohen 2012", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3296079/"),
    (r"Fang-Yen.{0,20}2010", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2996704/"),
    (r"Fenyves", "https://pmc.ncbi.nlm.nih.gov/articles/PMC7785220/"),
    (r"CeNGEN|Taylor et al\. 2021", "https://doi.org/10.1016/j.cell.2021.06.023"),
    (r"Cook et al\.? 2019|Cook 2019", "https://doi.org/10.1038/s41586-019-1352-7"),
    (r"Ripoll-Sanchez", "https://pmc.ncbi.nlm.nih.gov/articles/PMC7615469/"),
    (r"wang2024|Wang et al\.? 2024", "https://doi.org/10.7554/eLife.95402"),
    (r"Richmond (and|&) Jorgensen 1999|RJ99", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2585773/"),
    (r"Jahr (and|&) Stevens 1990", "https://pmc.ncbi.nlm.nih.gov/articles/PMC6570236/"),
    (r"Lindsay, Thiele (and|&) Lockery 2011", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3935721/"),
    (r"Liu, Hollopeter (and|&) Jorgensen 2009", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2705609/"),
    (r"Pirri.{0,60}2009", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2804440/"),
    (r"Ringstad.{0,30}2009", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2963310/"),
    (r"Boulin et al\.? 2008", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2587545/"),
    (r"Bamber et al\.? 1999", "https://pmc.ncbi.nlm.nih.gov/articles/PMC6782323/"),
    (r"Brockie et al\.? 2001", "https://doi.org/10.1016/s0896-6273(01)00394-4"),
    (r"Beg (and|&) Jorgensen 2003", "https://doi.org/10.1038/nn1136"),
    (r"Ranganathan.{0,30}2000", "https://doi.org/10.1038/35044083"),
    (r"Mellem et al\.? 2002", "https://doi.org/10.1016/s0896-6273(02)01088-7"),
    (r"Rayes et al\.? 2007", "https://doi.org/10.1124/mol.106.033514"),
    (r"surface tension|standard tables \(water, 20-35 C\)", "https://iapws.org/technical-guidance/release/Surf-H2O"),
]


def link_for(r: dict, t: pd.DataFrame | None = None) -> str:
    """A URL to open for a row that has none: a PMC id or DOI named in its sources, the upstream file of a BAAIWorm,
    MetaWorm or c302 number at the pinned commit, or a paper from PAPERS. A per-element row is linked by its
    elements' most common source. '' if nothing fits."""
    if t is not None and "source" in t and len(t):
        r = {**r, "template_source": f"{t.source.value_counts().index[0]} ({r['template_source']})"}
    if r.get("param_id", "").startswith(("pas_", "mpas_", "dens_")) and "BAAIWorm" in str(r["template_source"]):
        return BAAI + "eworm/components/param/cell"
    text = " ".join(str(r.get(k, "")) for k in ("template_source", "bound_source", "notes"))
    m = re.search(r"PMC\d{5,}", text)
    if m:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{m.group(0)}/"
    m = re.search(r"\b(10\.\d{4,}/[^\s;,)]+)", text)
    if m:
        return "https://doi.org/" + m.group(1).rstrip(".")
    src = str(r.get("template_source", ""))
    if re.search(r"BAAIWorm|MetaWorm", src):
        for pat, path in BAAI_FILES:
            m = re.search(pat, src)
            if m:
                return BAAI + (path.format(m.group(1)) if "{}" in path else path)
        return BAAI.replace("/blob/", "/tree/")
    if "c302" in src:
        return "https://github.com/openworm/c302/blob/master/c302/parameters_C2.py"
    if r.get("param_id", "").startswith("morph_"):
        return BAAI + "eworm_learn/components/model"
    return next((u for pat, u in PAPERS if re.search(pat, text)), "")


# ----------------------------------------------------------------------------------------------------------- fills
FILL_COLUMNS = ["param_id", "kind", "value_template", "bio_min", "bio_max", "label", "bound_basis", "source",
                "source_url", "source_quote", "reason"]
# kind: fill (a literature value replaces a guess), relabel (the label was wrong for its source), range (the range
# or its basis was wrong), source (citation, link or quote corrected; numbers unchanged). Blank cells: unchanged


def fills(ids=None):
    """The fill log, one record per row. A param_id with a * is a pattern (fnmatch) over `ids`: one cited fill for a
    family of rows from the same table (e.g. pep_ec50_*_nM, one row per Beets 2023 pair); each match is logged."""
    f = CAT / "fills.csv"
    out = []
    for r in (pd.read_csv(f, keep_default_na=False).to_dict("records") if f.exists() else []):
        if "*" in r["param_id"] and ids is not None:
            hit = sorted(fnmatch.filter(ids, r["param_id"]))
            out += [dict(r, param_id=i, pattern=r["param_id"]) for i in hit] or [r]
        else:
            out.append(r)
    return out


def apply_fills(rows: list[dict], values: dict, fill_kind: dict) -> list[dict]:
    """Literature wins: set each filled row's template (and bounds, when given), label and source. A per-element
    table gets the new value on every element that was guessed. Body and slot rows change in the catalog only (the
    body code reads its own numbers; tell its owner). Returns the change log."""
    by = {r["param_id"]: r for r in rows}
    log = []
    for f in fills(list(by)):
        r = by.get(f["param_id"])
        if r is None:
            log.append(dict(param_id=f["param_id"], change="fill not applied: no such row", reason=f["reason"]))
            continue
        was = dict(value=_num(r["value_template"]), lo=_num(r["bio_min"]), hi=_num(r["bio_max"]), label=r["label"])
        kind = f.get("kind") or "fill"
        if f["bio_min"] != "":
            r["bio_min"], r["bio_max"] = float(f["bio_min"]), float(f["bio_max"])
            r["bound_source"] = f["source"] or r["bound_source"]
        if f["bound_basis"]:
            r["bound_basis"] = f["bound_basis"]
        if f["value_template"] != "":
            r["value_template"] = float(f["value_template"])
        if f["label"]:
            r["label"], r["fill_kind"] = f["label"], fill_kind[f["label"]]
        if kind == "fill":
            r["source_project"] = "literature"
        if f["source"] and kind != "range":
            if f["bio_min"] == "" and r.get("bound_source") == r["template_source"]:
                if kind == "source":
                    r["bound_source"] = f["source"]      # a corrected citation is the range's too when it was the same
                elif kind == "fill":                     # the range did not come from the new value's paper
                    r["bound_source"] = f"kept from before the value fill: {r['bound_source']}"
            r["template_source"] = f["source"]
        r["source_url"] = f["source_url"] or r.get("source_url", "")
        r["source_quote"] = f["source_quote"] or r.get("source_quote", "")
        r["notes"] = (r["notes"] + "; " if r["notes"] else "") + (
            f"{kind} 6 Nov (catalog audit): was {was['value']:g} {r['unit']}, label {was['label']}, range "
            f"[{was['lo']:g}, {was['hi']:g}]; {f['reason']}")
        if r["prior_dist"] in ("normal", "lognormal"):
            r["prior_a"] = r["value_template"]
        t = values.get(r["param_id"]) if r.get("origin") not in CATALOG_ONLY else None
        if t is not None and f["value_template"] != "":
            g = t.label == "guessed"
            t.loc[g, "value"] = r["value_template"]
            t.loc[g, "label"] = r["label"]
            t.loc[g, "source"] = f["source"] or r["template_source"]
            if "source_project" in t:
                t.loc[g, "source_project"] = "literature"
        n_changed = int((t.label == r["label"]).sum()) if t is not None else int(_num(r["n_values"]))
        log.append(dict(param_id=r["param_id"], kind=kind, origin=r.get("origin", ""), n=n_changed,
                        pattern=f.get("pattern", ""),
                        was_label=was["label"], new_label=r["label"],
                        change=f"{was['value']:g} -> {_num(r['value_template']):g} {r['unit']}; "
                        f"{was['label']} -> {r['label']}; range [{was['lo']:g}, {was['hi']:g}] -> "
                        f"[{_num(r['bio_min']):g}, {_num(r['bio_max']):g}]", reason=f["reason"],
                        source=f["source"] or r["template_source"], url=r["source_url"]))
    return log


# ----------------------------------------------------------------------------------------------------------- audit
CITE = re.compile(r"((et al\.?|[A-Z][A-Za-z-]+ (and|&) [A-Z][A-Za-z-]+|[A-Z][A-Za-z-]+),? \(?(19|20)\d\d)|PMC\d+|"
                  r"doi|https?://|WormAtlas|WormBook|CeNGEN|Cook et al|Fenyves|Wang et al|AmP|BAAIWorm|c302|NASA|NOAA|NIST")
NOT_A_CITATION = re.compile(r"guess|template guess|placeholder|assumed", re.I)
STRUCTURE = ("morph_", "wire_")
# solver and mesh settings and the keyframe driver's own constants: no biological range applies; what they need is a
# convergence or sensitivity check, not a citation
NUMERICS = {"mw_dt", "mw_iterations", "mw_convergence_eps", "mw_control_hz", "mw_n_vertices", "mw_n_tets",
            "mw_n_surface_triangles", "mw_mesh_scale", "mw_drag_force_cap", "mw_damping_per_step", "mw_key_gain",
            "mw_key_transport_alpha"}
# an audit note whose action starts with one of these explains the row's remaining problems: the row is a documented
# finding (kept on purpose, or waiting for the code's owner), not an unexplained problem. "fixed" and "read" (read
# against the source, nothing wrong) only add to the trail; any other action ("open") is a problem until resolved
EXPLAINED = ("accepted", "owner", "kept")


def kind_of(pid: str) -> str:
    return "structure" if pid.startswith(STRUCTURE) else "numerics" if pid in NUMERICS else "physiology"


def audit_notes():
    f = CAT / "audit_notes.csv"
    return pd.read_csv(f, keep_default_na=False).to_dict("records") if f.exists() else []


DEAD_LINK = {"404", "410", "000"}


def link_checks() -> dict:
    """url -> (status, checked_at) from scripts/worm/catalog_links.py (data/worm/catalog/link_check.csv)."""
    f = CAT / "link_check.csv"
    if not f.exists():
        return {}
    return {r["url"]: (str(r["status"]), r["checked_at"]) for r in
            pd.read_csv(f, keep_default_na=False, dtype=str).to_dict("records")}


QUOTE = re.compile(r"^([A-Za-z0-9_.-]+\.(md|csv))\b[^:]*: (.+)$", re.S)
_texts: dict[str, str] = {}


def _norm(x: str) -> str:
    return re.sub(r"\s+", " ", x).strip()


def quote_problem(q: str) -> str:
    """A quote "FILE SECTION: text" must have its text (parts joined by ' ... ') verbatim in FILE (docs/worm/research
    or docs/worm), whitespace aside. Quotes in other forms are not checked here."""
    m = QUOTE.match(q.strip())
    if not m:
        return ""
    name = m.group(1)
    if name not in _texts:
        f = next((d / name for d in (ROOT / "docs/worm/research", ROOT / "docs/worm") if (d / name).exists()), None)
        _texts[name] = _norm(f.read_text()) if f else ""
    if not _texts[name]:
        return f"quoted file {name} not found"
    missing = [part for part in m.group(3).split(" ... ") if _norm(part) not in _texts[name]]
    return f"quote not found verbatim in {name}: {missing[0][:60]}" if missing else ""


def audit(r: dict, t: pd.DataFrame | None) -> list[str]:
    """The scripted checks for one catalog row (the read audit is added from audit_notes.csv)."""
    p = []
    lab, lo, hi, v = r["label"], _num(r["bio_min"]), _num(r["bio_max"]), _num(r["value_template"])
    srcs = " ".join(str(r.get(k, "")) for k in ("template_source", "bound_source", "source_url"))
    if not str(r["unit"]).strip():
        p.append("no unit")
    if "UNVERIFIED" in srcs + str(r.get("notes", "")):
        p.append("source marked UNVERIFIED")
    qp = quote_problem(str(r.get("source_quote", "")))
    if qp:
        p.append(qp)
    if lab == "absent":
        if r["used_by_code"] == "yes":
            p.append("labelled absent but the code reads it")
        if not str(r.get("source_url", "")).strip() and not CITE.search(srcs + str(r.get("notes", ""))):
            p.append("gap without a named source that would fill it")
        return p
    if np.isnan(lo) or np.isnan(hi):
        if kind_of(r["param_id"]) != "numerics":
            p.append("no range")
    elif not np.isnan(v) and not lo <= v <= hi:
        p.append(f"template {v:g} outside [{lo:g}, {hi:g}]")
    elif lo == hi and not str(r["unit"]).startswith("count"):
        p.append("range is one point: the source's spread was not recorded")
    if not np.isnan(lo) and r["bound_basis"] in ("measured_this_class", "measured_related") and \
            not CITE.search(str(r["bound_source"])):
        p.append("range basis says measured but the range source names no citation")
    if lab in ("measured", "derived"):
        if NOT_A_CITATION.search(str(r["template_source"])) and not CITE.search(str(r["template_source"])):
            p.append(f"labelled {lab} but the template source reads as a guess")
        if t is None and not CITE.search(srcs):
            p.append(f"labelled {lab} without a citation")
    if lab != "guessed" and not str(r.get("source_url", "")).strip():
        p.append("no URL to open")
    if lab == "published_fit" and r["source_project"] not in ("BAAIWorm", "c302", "ChannelWorm", "Sibernetic",
                                                             "literature"):
        p.append(f"published_fit from source_project {r['source_project']}")
    if lab == "guessed" and not np.isnan(v) and not np.isnan(lo) and hi > lo and r["unit"] != "flag" and \
            (np.isclose(v, lo) or np.isclose(v, hi)) and r["prior_dist"] not in ("fixed", "bernoulli"):
        p.append("guessed template sits on a bound")
    if t is not None:
        n = int(_num(r["n_values"]))
        if len(t) != n:
            p.append(f"values table {len(t)} elements, n_values {n}")
        vv = pd.to_numeric(t.value, errors="coerce")
        live = t.label != "absent"
        if not np.isnan(lo) and ((vv[live] < lo) | (vv[live] > hi)).any():
            p.append("element values outside the range")
        labs = t.label.value_counts()
        if lab == "measured" and labs.get("measured", 0) < len(t) / 2:
            p.append(f"row label measured but {labs.get('measured', 0)} of {len(t)} elements are")
        if lab == "guessed" and labs.get("guessed", 0) == 0:
            p.append("row label guessed but no element is")
    return p


def label_split(r: dict, t: pd.DataFrame | None) -> dict:
    if t is None:
        return {r["label"]: int(_num(r["n_values"]))}
    return {k: int(x) for k, x in t.label.value_counts().items()}


def label_tally(rows: list[dict], values: dict) -> dict:
    """Rows and numbers by label (for the before / after report of the fills)."""
    rc, nc = Counter(), Counter()
    for r in rows:
        rc[r["label"]] += 1
        for k, n in label_split(r, values.get(r["param_id"]) if r.get("origin") not in CATALOG_ONLY else None
                                ).items():
            nc[k] += n
    return dict(rows=dict(rc), numbers=dict(nc))


def template_text(r: dict, t: pd.DataFrame | None) -> str:
    v = _num(r["value_template"])
    if t is None:
        return "" if np.isnan(v) else f"{v:.4g}"
    x = pd.to_numeric(t.value, errors="coerce")
    return f"median {x.median():.4g} (min {x.min():.4g}, max {x.max():.4g}, {len(t)} elements)"


# ---------------------------------------------------------------------------------------------------- the catalog
CATALOG_COLUMNS = ["id", "plan_row", "plan_row_name", "mechanism", "mechanism_name", "grain", "n_elements",
                   "template", "bio_min", "bio_max", "units", "label", "labels_by_element", "source", "source_url",
                   "source_quote", "source_project", "fill_kind", "used_by_code", "toggle", "precision_needed",
                   "audit", "audit_status", "audit_trail", "quote_checked", "link_status", "notes", "origin", "kind", "applies_to",
                   "range_source", "range_basis", "values_file"]


def quote_status(q: str) -> str:
    if not str(q).strip():
        return ""
    return "research file (scripted check)" if QUOTE.match(str(q).strip()) else "paper text (read audit, 6 Nov)"


def build(model_rows, values, mechs, body_mechs, body, slot_rows, slot_mechs, fill_kind):
    mname = {m["id"]: m for m in [*mechs, *body_mechs, *slot_mechs]}
    open_, trail, explained = defaultdict(list), defaultdict(list), set()
    for a in audit_notes():
        act = str(a.get("action", "")).strip()
        text = a["finding"] + (f" [{act}]" if act else "")
        trail[a["param_id"]].append(text)
        if act.startswith(EXPLAINED):
            explained.add(a["param_id"])
        elif not act.startswith(("fixed", "read")):
            open_[a["param_id"]].append(text)
    out, links = [], link_checks()
    for r in [*model_rows, *body, *slot_rows]:
        t = values.get(r["param_id"]) if r["origin"] not in CATALOG_ONLY else None
        if not str(r.get("source_url", "")).strip():
            r["source_url"] = link_for(r, t)
        probs = audit(r, t) + open_.get(r["param_id"], [])
        url = str(r.get("source_url", "")).strip()
        link = links.get(url, ("unchecked", ""))[0] if url else ""
        if link in DEAD_LINK:
            probs.append(f"source link answered {link}")
        lc = str(r.get("body_lit_check", ""))
        if r["origin"] == "body" and lc and lc not in ("ok", "inside"):
            explained.add(r["param_id"])
            trail[r["param_id"]].append(f"body ledger lit_check: {lc}")
        status = "ok" if not probs else "finding" if r["param_id"] in explained else "problem"
        m = mname.get(r["mechanism_id"], {})
        split = label_split(r, t)
        out.append(dict(
            id=r["param_id"], plan_row=int(r["plan_row"]), plan_row_name=PLAN_ROWS.get(int(r["plan_row"]), "?"),
            mechanism=r["mechanism_id"], mechanism_name=m.get("name", ""), grain=r["grain"],
            n_elements=int(_num(r["n_values"])), template=template_text(r, t), bio_min=r["bio_min"],
            bio_max=r["bio_max"], units=r["unit"], label=r["label"],
            labels_by_element="; ".join(f"{k} {n}" for k, n in sorted(split.items(), key=lambda kv: -kv[1])),
            source=r["template_source"], source_url=r.get("source_url", ""), source_quote=r.get("source_quote", ""),
            source_project=r["source_project"], fill_kind=fill_kind.get(r["label"], r["label"]),
            used_by_code=r["used_by_code"], toggle=r.get("toggle", "") or m.get("toggle", ""),
            precision_needed=r["precision_needed"] + (f" ({r['precision_method']})" if r.get("precision_method")
                                                      else ""),
            audit="ok" if not probs else "; ".join(probs), audit_status=status,
            audit_trail="; ".join(trail.get(r["param_id"], [])), quote_checked=quote_status(r.get("source_quote", "")),
            link_status=link, notes=r.get("notes", ""), origin=r["origin"], kind=kind_of(r["param_id"]),
            applies_to=r["applies_to"], range_source=r.get("bound_source", ""), range_basis=r.get("bound_basis", ""),
            values_file=f"data/worm/model/values/{r['param_id']}.csv" if t is not None else "",
            _split=split, _probs=probs))
    return out


def summary(cat_rows, replaced, fill_log, hidden, before=None):
    """Rows and numbers by label, PLAN row, grain, used vs slot; the biggest unknown blocks; the audit."""
    def tally(key):
        d = defaultdict(lambda: dict(rows=Counter(), numbers=Counter()))
        for r in cat_rows:
            k = r[key] if not callable(key) else key(r)
            d[k]["rows"][r["label"]] += 1
            for lab, n in r["_split"].items():
                d[k]["numbers"][lab] += n
        return {k: dict(rows=dict(v["rows"]), numbers=dict(v["numbers"]),
                        n_rows=sum(v["rows"].values()), n_numbers=sum(v["numbers"].values()))
                for k, v in sorted(d.items(), key=lambda kv: str(kv[0]).zfill(3))}
    all_ = tally(lambda r: "all")["all"]
    blocks = []
    for r in cat_rows:
        unk = r["_split"].get("guessed", 0) + r["_split"].get("absent", 0)
        if unk:
            blocks.append(dict(id=r["id"], plan_row=r["plan_row"], mechanism=r["mechanism"], grain=r["grain"],
                               unknown=unk, of=r["n_elements"], used_by_code=r["used_by_code"],
                               fit_target=int(r["grain"] == "connection" and r["kind"] == "physiology")))
    blocks.sort(key=lambda b: -b["unknown"])
    audit_ok = sum(1 for r in cat_rows if r["audit"] == "ok")
    status = Counter(r["audit_status"] for r in cat_rows)
    probs = Counter()
    for r in cat_rows:
        for p in r["_probs"]:
            probs[re.sub(r"-?\d[\d.e+-]*", "#", p.split(" [")[0])[:90]] += 1
    return dict(
        totals=all_, by_label_rows=all_["rows"], by_label_numbers=all_["numbers"],
        by_plan_row=tally("plan_row"), by_grain=tally("grain"), by_used=tally(lambda r: str(r["used_by_code"]).split(":")[0]),
        by_origin=tally("origin"), by_kind=tally("kind"),
        biggest_unknown_blocks=blocks[:25], slots_replaced=[dict(slot=a, by=b) for a, b in replaced],
        audit=dict(rows_ok=audit_ok, rows_with_problems=len(cat_rows) - audit_ok, by_status=dict(status),
                   rows_read=sum(1 for r in cat_rows if r["audit_trail"]),
                   quotes=dict(Counter(r["quote_checked"] or "none" for r in cat_rows)),
                   with_url=sum(1 for r in cat_rows if r["source_url"]),
                   links=dict(distinct=len({r["source_url"] for r in cat_rows if r["source_url"]}),
                              by_status=dict(Counter(s for s in {r["source_url"]: r["link_status"]
                                                                  for r in cat_rows if r["source_url"]}.values())),
                              checked_at=max((v[1] for v in link_checks().values()), default="")),
                   problem_kinds=dict(probs.most_common()),
                   # a read-audit note or fill on an id no row has (a typo, or a row renamed by its owner)
                   orphan_notes=sorted({a["param_id"] for a in audit_notes()} - {r["id"] for r in cat_rows}),
                   orphan_fills=sorted({f["param_id"] for f in fill_log if f.get("change", "").startswith(
                       "fill not applied")})),
        fills=fill_log, hidden_constants=hidden,
        before_fills=before or {}, after_fills=dict(rows=all_["rows"], numbers=all_["numbers"]))


# ---------------------------------------------------------------------------------------------------------- outputs
def hidden_summary():
    f = CAT / "hidden_constants.json"
    if not f.exists():
        return {}
    d = json.loads(f.read_text())
    return {k: d[k] for k in ("generated_at", "scanned", "total", "by_file", "by_kind", "by_verdict", "unreviewed",
                              "catalog_rows_added", "code_side", "skipped") if k in d}


def _clean(v):
    if isinstance(v, float) and np.isnan(v):
        return ""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def write(cat_rows, summ, mechs):
    rows = [{k: _clean(r[k]) for k in CATALOG_COLUMNS} for r in cat_rows]
    pd.DataFrame(rows, columns=CATALOG_COLUMNS).to_csv(ROOT / "data/worm/model/catalog.csv", index=False)
    for r, c in zip(rows, cat_rows):
        r["split"] = c["_split"]
    mrows = [{k: _clean(m.get(k, "")) for k in ("id", "name", "layer", "status", "toggle", "default", "source")}
             for m in mechs]
    for m in mrows:
        m["plan_row"] = MECH_ROW.get(m["id"], 0)
    (ROOT / "viewer/worm/catalog_data.json").write_text(json.dumps(
        dict(generated_by="scripts/worm/build_ledger.py", generated_at=summ.get("generated_at") or time.strftime("%Y-%m-%d %H:%M %Z"),
             plan_rows=PLAN_ROWS, summary={k: v for k, v in summ.items() if k != "fills"}, fills=summ["fills"],
             mechanisms=mrows, rows=rows), default=float))
    write_markdown(cat_rows, summ)


LAB_ORDER = ["measured", "published_fit", "derived", "inferred", "guessed", "absent"]


def _labs(d):
    return " | ".join(f"{d.get(k, 0):,}" for k in LAB_ORDER)


def write_markdown(cat_rows, s):
    import subprocess
    now = subprocess.run(["date", "+%Y-%m-%d %H:%M %Z"], capture_output=True, text=True).stdout.strip()
    t = s["totals"]
    L = [f"# Worm parameter catalog ({now})", "",
         "Generated by `scripts/worm/build_ledger.py` (one command; do not edit by hand). One row per unknown: every "
         "number the model's code reads (brain, lumped layers, registry mechanisms, the body) and every number a "
         "PLAN row's published model needs that no code reads yet (**slots**, `used_by_code = slot only`). Rows are "
         "in `data/worm/model/catalog.csv`; the browser page is `viewer/worm/catalog.html` (served by "
         "`viewer/worm/serve.py`, port 8781). Counts of **numbers** count elements (a per-cell row over 302 neurons "
         "is 302 numbers); counts of **rows** count catalog rows.", "",
         "Labels: **measured** (read off a cited primary source), **published_fit** (a value another project fitted "
         "or chose and published: BAAIWorm, c302, MetaWorm), **derived** (arithmetic on measured values, shown), "
         "**inferred** (reasoned from a source, ours), **guessed** (bounded placeholder, not from data), **absent** "
         "(the real worm has it; no value yet).", "",
         "## Totals", "",
         "| | measured | published_fit | derived | inferred | guessed | absent | total |", "|---|---|---|---|---|---|---|---|",
         f"| rows | {_labs(t['rows'])} | {t['n_rows']:,} |",
         f"| numbers | {_labs(t['numbers'])} | {t['n_numbers']:,} |"]
    if s.get("before_fills"):
        L += ["", "### Before and after the fills (`data/worm/catalog/fills.csv`)", "",
              "| | measured | published_fit | derived | inferred | guessed | absent | total |",
              "|---|---|---|---|---|---|---|---|"]
        for when, d in (("before", s["before_fills"]), ("after", s["after_fills"])):
            for unit in ("rows", "numbers"):
                L.append(f"| {unit} {when} | {_labs(d[unit])} | {sum(d[unit].values()):,} |")
    for key, title in (("by_kind", "Structure vs physiology"), ("by_used", "Used by code vs slots"),
                       ("by_origin", "By origin")):
        L += ["", f"### {title} (numbers)", "", "| | measured | published_fit | derived | inferred | guessed | absent "
              "| total numbers | rows |", "|---|---|---|---|---|---|---|---|---|"]
        for k, v in s[key].items():
            L.append(f"| {k} | {_labs(v['numbers'])} | {v['n_numbers']:,} | {v['n_rows']:,} |")
    L += ["", "## By PLAN row (numbers; rows in the last column)", "",
          "| # | PLAN row | measured | published_fit | derived | inferred | guessed | absent | numbers | rows | "
          "slot rows |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    slot_rows = Counter(r["plan_row"] for r in cat_rows if r["used_by_code"] == "slot only")
    for k, v in s["by_plan_row"].items():
        L.append(f"| {k} | {PLAN_ROWS.get(int(k), '?')} | {_labs(v['numbers'])} | {v['n_numbers']:,} | "
                 f"{v['n_rows']} | {slot_rows.get(int(k), 0)} |")
    L += ["", "## By grain (numbers)", "", "| grain | measured | published_fit | derived | inferred | guessed | "
          "absent | numbers | rows |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in s["by_grain"].items():
        L.append(f"| {k} | {_labs(v['numbers'])} | {v['n_numbers']:,} | {v['n_rows']} |")
    L += ["", "## The biggest unknown blocks (guessed + absent numbers)", "",
          "`fit target` = a per-connection physiology row: a number to fit later against physiology (per-pair "
          "synapse strengths stay guessed templates; nothing in the literature gives them pair by pair).", "",
          "| row | PLAN | mechanism | grain | unknown | of | used | fit target |", "|---|---|---|---|---|---|---|---|"]
    for b in s["biggest_unknown_blocks"][:20]:
        L.append(f"| `{b['id']}` | {b['plan_row']} | {b['mechanism']} | {b['grain']} | {b['unknown']:,} | "
                 f"{b['of']:,} | {b['used_by_code']} | {'yes' if b['fit_target'] else ''} |")
    a = s["audit"]
    st = a.get("by_status", {})
    L += ["", "## Audit", "", f"{a['rows_ok']} rows pass every check; {a['rows_with_problems']} carry at least one "
          f"problem (text in the `audit` column): {st.get('finding', 0)} are **findings** (explained in the read "
          f"audit or the body ledger's lit_check, with an owner) and {st.get('problem', 0)} are open **problems**. "
          "Scripted checks: label vs source (a measured or derived row must cite a source and link it; a guess "
          "cannot be labelled measured), range present and cited, template and every element inside the range, "
          "element labels add up to n_values, units present, UNVERIFIED sources flagged, research-file quotes found "
          "verbatim. The read audit (`data/worm/catalog/audit_notes.csv`, one line per finding with its action: "
          "fixed / read / accepted / owner / kept / open) adds what a script cannot see: whether the paper says it.",
          "", f"Rows with a URL to open: {a.get('with_url', 0)} of {t['n_rows']} (every row not labelled guessed "
          f"has one unless listed below). Rows read against their source: {a.get('rows_read', 0)}. Quotes: "
          + ", ".join(f"{k} {n}" for k, n in a.get("quotes", {}).items()) + ". Audit notes on ids no row has: "
          + (", ".join(f"`{x}`" for x in a.get("orphan_notes", [])) or "none") + "; fills on ids no row has: "
          + (", ".join(f"`{x}`" for x in a.get("orphan_fills", [])) or "none") + ".", "",
          f"Links: {a.get('links', {}).get('distinct', 0)} distinct URLs, checked "
          f"{a.get('links', {}).get('checked_at', '') or 'never'} by `scripts/worm/catalog_links.py` (status: "
          + ", ".join(f"{k} {n}" for k, n in a.get("links", {}).get("by_status", {}).items()) + "; a 404, 410 or no "
          "answer is a problem; 401/403/406/429 are publisher pages that refuse scripted requests but open in a "
          "browser).", "",
          "| problem | rows |", "|---|---|"]
    for k, n in a["problem_kinds"].items():
        L.append(f"| {k} | {n} |")
    flagged = [r for r in cat_rows if r["audit_status"] != "ok"]
    if flagged:
        L += ["", "### Rows not ok", "", "| row | status | problems | read audit |", "|---|---|---|---|"]
        for r in sorted(flagged, key=lambda r: (r["audit_status"] != "problem", r["origin"], r["id"])):
            L.append(f"| `{r['id']}` | {r['audit_status']} | {r['audit']} | {r['audit_trail']} |")
    notes = audit_notes()
    if notes:
        L += ["", "### Read-audit log", "", "| row | finding | action |", "|---|---|---|"]
        L += [f"| `{n['param_id']}` | {n['finding']} | {n['action']} |" for n in notes]
    L += ["", "## What the catalog changed (fills: literature wins)", ""]
    if s["fills"]:
        moved = Counter()
        for f in s["fills"]:
            if "n" in f:
                moved[(f["was_label"], f["new_label"])] += f["n"]
        L.append("Numbers relabelled: " + "; ".join(f"{a_} -> {b_}: {n:,}" for (a_, b_), n in moved.items()) + ".")
        L += ["", "| row | change | source | why |", "|---|---|---|---|"]
        seen = Counter(f.get("pattern", "") for f in s["fills"])
        for f in s["fills"]:
            pat = f.get("pattern", "")
            if not pat:
                L.append(f"| `{f['param_id']}` | {f['change']} | {f.get('source', '')} | {f['reason']} |")
            elif seen[pat]:
                L.append(f"| `{pat}` ({seen[pat]} rows) | {f['kind']}: first match `{f['param_id']}` {f['change']} | "
                         f"{f.get('source', '')} | {f['reason']} |")
                seen[pat] = 0
    else:
        L.append("No fills yet.")
    if s["slots_replaced"]:
        L += ["", "## Slots replaced by code", "", "| slot | replaced by |", "|---|---|"]
        L += [f"| `{x['slot']}` | {x['by']} |" for x in s["slots_replaced"]]
    h = s.get("hidden_constants") or {}
    L += ["", "## Hidden constants (numeric literals in the model code not read from the ledger)", ""]
    if h:
        L.append(f"`scripts/worm/hidden_constants.py` ({h.get('generated_at', '')}): {h.get('total', 0)} literals "
                 f"in {len(h.get('by_file', {}))} files, each with a verdict from the hand review "
                 f"(`data/worm/catalog/hidden_review.csv`; {h.get('unreviewed', 0)} unreviewed). File:line list in "
                 "`data/worm/catalog/hidden_constants.json`. Not counted: "
                 + ", ".join(f"{v} {k}" for k, v in (h.get("skipped") or {}).items()) + ".")
        L += ["", "| verdict | literals |", "|---|---|"] + [f"| {k} | {v} |" for k, v in h.get("by_verdict", {}).items()]
        if h.get("catalog_rows_added"):
            L += ["", "Catalog rows added for them (origin `hidden`, `used_by_code` names the file:line): "
                  + ", ".join(f"`{r}`" for r in h["catalog_rows_added"]) + "."]
        if h.get("code_side"):
            L += ["", "Code side (the owner's code should read the catalog row instead of the literal):", "",
                  "| file:line | value | row | owner |", "|---|---|---|---|"]
            L += [f"| `{x['file']}:{x['line']}` | {x['value']:g} | `{x['row']}` | {x['owner']} |" for x in h["code_side"]]
        L += ["", "| file | literals |", "|---|---|"] + [f"| `{k}` | {v} |" for k, v in h.get("by_file", {}).items()]
    else:
        L.append("Not scanned yet.")
    L += ["", "## Precision needed", "", "Only rows with a range-end sensitivity run (BRAIN_PORT section 5, runs "
          "S01-S19, measured, report-only) carry a precision note, and it is a sensitivity (what each range end "
          "does to the count of neurons above -20 mV), not a precision: there is no correctness target yet. "
          f"{sum(1 for r in cat_rows if r['precision_needed'] != 'not yet estimated')} rows have it; every other "
          "row says 'not yet estimated'.", ""]
    (ROOT / "docs/worm/CATALOG.md").write_text("\n".join(L) + "\n")
