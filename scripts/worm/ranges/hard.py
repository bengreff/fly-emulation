"""Hard bounds and the bound-basis vocabulary for every worm ledger row (wranges, 7 Nov 2026).

A row's HARD bounds (hard_min, hard_max) are what physics and chemistry allow any animal cell; its BIOLOGICAL range
(bio_min, bio_max) is the measured or guessed box a fitter searches, and must sit inside the hard bounds. The rules
are in rules.yaml next to this file. `apply(rows)` fills the fields on the build's row dicts in place and returns a
report; `python scripts/worm/ranges/hard.py` runs it over the current data/worm/model/catalog.csv and prints the
report without writing anything.

Fields written on each row:
  hard_min, hard_max   in the row's unit
  hard_class           the rules.yaml class (or "row" for a per-row bound)
  hard_basis           physics | guessed_physical
  hard_source          why, then the source
  bound_basis          physics | measured_spread | homology | guessed_physical (the basis of the biological range)
  bound_basis_detail   the old, finer basis (measured_this_class, measured_related, organism_wide, physical_limit,
                       guessed) and any clip made here
  span_decades         log10(bio_max / bio_min) when both are positive, else blank
  span_reason          why a range is wider than one decade (blank when it is not, or when no reason is written)
  fit_role             free (has unknown numbers: a fitter moves those inside the biological range) | static (every
                       number known: measured, derived, published_fit or inferred; part of the built worm, its hard
                       bounds kept only for residuals and debugging; Ben, 7 Nov 12:42) | fixed (structure, constants,
                       recording conditions, numerics) | derived (follows from other rows) | inactive (has unknown
                       numbers but the default worm does not read it: another form, or a catalog slot)
  n_unknown            the row's guessed or absent numbers (its elements labelled so, or all n_values if the row is)
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gates  # noqa: E402
RULES = yaml.safe_load((HERE / "rules.yaml").read_text())
for _c in [*RULES["classes"].values(), *RULES["rules"]]:     # PyYAML reads 1.0e7 (no exponent sign) as a string
    for _k in ("hard", "hard_row_unit"):
        if _k in _c:
            _c[_k] = [float(x) for x in _c[_k]]
BASES = ("physics", "measured_spread", "homology", "guessed_physical")
FIELDS = ["hard_min", "hard_max", "hard_class", "hard_basis", "hard_source", "bound_basis_detail", "span_decades",
          "span_reason", "fit_role", "n_unknown"]

# row unit -> (dimension, factor): value in the class's canonical unit = value in the row unit x factor
UNITS = {
    "mV": ("voltage", 1), "mV (model)": ("voltage", 1), "mV/e": ("voltage", 1),
    "1/mV": ("inv_voltage", 1), "/mV": ("inv_voltage", 1),
    "S/cm2": ("cond_density", 1), "mS/cm2": ("cond_density", 1e-3), "nS/um2": ("cond_density", 0.1),
    "kOhm cm2": ("spec_resistance", 1),
    "pS": ("conductance", 1e-3), "nS": ("conductance", 1), "uS": ("conductance", 1e3),
    "nS per pair": ("conductance", 1), "nS per EM synapse": ("conductance", 1),
    "nS per EM gap junction": ("conductance", 1),
    "pF": ("capacitance", 1), "uF/cm2": ("cap_specific", 1), "ohm cm": ("resistivity", 1), "pA": ("current", 1),
    "ms": ("time", 1), "s": ("time", 1e3), "min": ("time", 6e4), "h": ("time", 3.6e6), "d": ("time", 8.64e7),
    "1/s": ("rate", 1), "Hz": ("rate", 1), "1/ms": ("rate", 1e3), "/ms": ("rate", 1e3), "kHz": ("rate", 1e3),
    "1/d": ("rate", 1 / 86400),
    "1/(uM s)": ("rate2", 1), "1/uM/s": ("rate2", 1),
    "nM": ("conc", 1e-3), "uM": ("conc", 1), "mM": ("conc", 1e3), "M": ("conc", 1e6),
    "um2/s": ("diffusion", 1), "cm2/s": ("diffusion", 1e8),
    "um": ("length", 1), "mm": ("length", 1e3), "um2": ("area", 1), "um3": ("volume", 1),
    # BAAIWorm's mods write uM/um2 or uM/um3 for Ca constants their formulas use as uM (cainternm, kcnl, slo*)
    "uM/um2": ("conc", 1), "uM/um3": ("conc", 1),
}
F_C = 96485.33212        # C/mol
R_GAS = 8.314462618      # J/(mol K)
WORM = re.compile(r"elegans|nematode|worm|Ascaris|BAAIWorm|c302|WormAtlas|CeNGEN|Nicoletti|Beets|AmP |Sanzeni|"
                  r"Goodman|Lockery|Jorgensen|Bamber|Richmond|Wicks|Kunert|Hilliard|Chalasani|O'Hagan|L'Etoile|"
                  r"Usuyama|Du, Crodelle|Sherman|Yu et al|Lindsay|Brockie|Boulin|Liu, Hollopeter|Liu, Chen|"
                  r"param_ranges|Atif|Hernando|Narayan|Wen et al|Collins|Zimmer|Taylor et al", re.I)
OTHER = re.compile(r"vertebrate|mammal|\brat\b|mouse|murine|HEK|oocyte|Xenopus|cardiac|Luo & Rudy|Jahr|Gentet|"
                   r"generic|astrocyte|Kir4\.1|Drosophila|human|squid|Aplysia|Hansen, Wollmuth|Cys-loop review", re.I)


def nernst(ions: list[str]) -> tuple[float, float]:
    """Most negative and most positive Nernst potential (mV) of the ions over the env windows and temperatures."""
    t = [RULES["env"]["temperature_C"][0] + 273.15, RULES["env"]["temperature_C"][1] + 273.15]
    out = []
    for ion in ions:
        w = RULES["env"]["ions"][ion]
        for T in t:
            for ci in w["inside"]:
                for co in w["outside"]:
                    out.append(1e3 * R_GAS * T / (w["z"] * F_C) * math.log(co / ci))
    return min(out), max(out)


def family(pid: str) -> str:
    fam = RULES["family_of"]
    for tok in re.split(r"[_]", pid):
        if tok in fam:
            return fam[tok]
        base = re.sub(r"(iso|_.*)$", "", tok)
        if base in fam:
            return fam[base]
    return fam["default"]


def _num(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


ROLE_CLASS = {"midpoint": "voltage_midpoint", "slope": "voltage_slope", "sensitivity": "voltage_sensitivity"}


def rule_for(pid: str, unit: str) -> dict | None:
    """The first rule whose regex (and unit list, if any) matches. A role_dispatch rule matches a kin_ row only when
    the constant's place in its mod's formulas says it is a voltage midpoint, slope or sensitivity."""
    for r in RULES["rules"]:
        if "unit" in r and unit not in r["unit"]:
            continue
        if re.search(r["re"], pid):
            if r.get("role_dispatch"):
                role = gates.role(pid)
                if role not in ROLE_CLASS:
                    continue
                return dict(r, cls=ROLE_CLASS[role], sign="template" if role == "slope" else None,
                            why_role=f"{role} in its mod's formulas")
            return r
    return None


def resolve(r: dict, rule: dict) -> dict:
    """hard_min, hard_max (row unit), class, basis, source for one row under its rule; 'error' if it cannot."""
    pid, unit = r["param_id"], str(r["unit"])
    t, lo, hi = _num(r.get("value_template")), _num(r.get("bio_min")), _num(r.get("bio_max"))
    cls_name = rule.get("cls", "row")
    cls = dict(RULES["classes"].get(cls_name, {}))
    cls.update({k: v for k, v in rule.items() if k in ("basis", "why", "source", "sign") and v is not None})
    out = dict(hard_class=cls_name, hard_basis=cls.get("basis", "physics"),
               hard_source=f"{cls.get('why', '')}; {cls.get('source', '')}".strip("; "), fit_role=rule.get("role", "free"))
    if "hard_row_unit" in rule:
        h0, h1 = rule["hard_row_unit"]
    elif cls.get("structure"):
        h0, h1 = lo, hi
    elif cls_name == "numerics" or (cls.get("model_units") and np.isnan(hi)):
        h0, h1 = (t, t) if not np.isnan(t) else (lo, hi)      # fixed: the range may be in other units (mw_*)
        out.update(hard_basis="guessed_physical", fit_role="fixed",
                   hard_source="a numerical or simulator setting, not biology: fixed at its value")
    elif cls.get("model_units"):
        h0 = min(0.0, 100 * lo) if not np.isnan(lo) else 0.0
        h1 = 100 * max(hi, 0.0) if not np.isnan(hi) else float("nan")
    else:
        if "nernst" in cls:
            h0, h1 = nernst(cls["nernst"])
            h0, h1 = math.floor(h0), math.ceil(h1)
        elif cls.get("packing"):
            g = RULES["families"]["leak" if "_g_l" in pid else family(pid)]
            h0, h1 = 0.0, RULES["packing_per_um2"] * g * 1e-4      # n/um2 x pS -> S/cm2
            out["hard_source"] += f" (family gamma {g} pS x {RULES['packing_per_um2']:g} per um2 = {h1:g} S/cm2)"
        else:
            h0, h1 = cls["hard"]
        dim = cls.get("dim", "none")
        if dim in ("voltage", "inv_voltage") and unit in ("1", "") and pid.startswith("kin_"):
            out["hard_source"] += " (the mod gives no unit: mV)"
        elif dim != "none":
            if unit not in UNITS or UNITS[unit][0] != dim:
                return dict(out, error=f"unit {unit!r} is not a {dim}")
            f = UNITS[unit][1]
            h0, h1 = h0 / f, h1 / f
            if unit in ("uM/um2", "uM/um3"):
                out["hard_source"] += f" (the mod's unit string {unit!r} is read as uM, as its formula uses it)"
    if cls.get("sign") == "template":
        s = t if not np.isnan(t) and t != 0 else (hi if not np.isnan(hi) and hi != 0 else lo)
        if not np.isnan(s) and s < 0:
            h0, h1 = -h1, -h0
    out.update(hard_min=float(h0), hard_max=float(h1))
    return out


def new_basis(r: dict, old: str) -> str:
    if old in ("", None):
        return ""
    if old == "guessed":
        return "guessed_physical"
    if old == "physical_limit":
        return "physics"
    if old in ("measured_this_class", "organism_wide"):
        return "measured_spread"
    src = str(r.get("bound_source", "")) + " " + str(r.get("source", ""))
    if old == "measured_related":
        return "homology" if OTHER.search(src) and not WORM.search(src.split(";")[0]) else "measured_spread"
    if old in BASES:
        return old
    return "homology" if OTHER.search(src) else ("measured_spread" if WORM.search(src) else "guessed_physical")


# classes on a shift scale (a decade count means nothing for them)
LINEAR = {"temperature_C", "temperature_K", "temperature_dC", "position", "body_fraction", "rt_over_f", "ph",
          "atp_free_energy", "oxycaloric", "gas_constant", "arrhenius_K", "density_tissue", "density_water", "gravity",
          "surface_tension", "structure", "numerics", "angle_deg", "poisson"}


def span_reason(pid: str) -> str:
    for s in RULES["span_reasons"]:
        if re.search(s["re"], pid):
            return s["why"]
    return ""


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-15)


def apply(rows: list[dict], values: dict | None = None) -> dict:
    """Fill the hard fields on every row (in place); clip guessed ranges to the hard bounds; return the report."""
    rep = {k: [] for k in ("unmatched", "errors", "clipped", "measured_outside_hard", "template_outside_hard",
                           "values_outside_hard", "wide_no_reason")}
    for r in rows:
        pid = r["param_id"]
        old = r.get("bound_basis_detail") or r.get("bound_basis", "")
        rule = rule_for(pid, str(r["unit"]))
        if rule is None:
            rep["unmatched"].append(f"{pid} [{r['unit']}]")
            continue
        h = resolve(r, rule)
        if "error" in h:
            rep["errors"].append(f"{pid}: {h['error']}")
            continue
        r.update({k: v for k, v in h.items() if k in FIELDS})
        lo, hi, t = _num(r.get("bio_min")), _num(r.get("bio_max")), _num(r.get("value_template"))
        h0, h1 = h["hard_min"], h["hard_max"]
        basis = new_basis(r, old)
        detail = str(old or "")
        if not np.isnan(t) and not (h0 - 1e-12 * abs(h0) <= t <= h1 + 1e-12 * abs(h1)):
            rep["template_outside_hard"].append(f"{pid}: template {t:g} outside hard [{h0:g}, {h1:g}] {r['unit']}")
        if values is not None and pid in values and "value" in values[pid]:
            v = np.asarray([_num(x) for x in values[pid].value])
            v = v[~np.isnan(v)]
            if len(v) and ((v < h0 - 1e-12 * abs(h0)) | (v > h1 + 1e-12 * abs(h1))).any():
                rep["values_outside_hard"].append(f"{pid}: per-element values {v.min():g}..{v.max():g} outside hard "
                                                  f"[{h0:g}, {h1:g}]")
        numerics = h["hard_class"] == "numerics"      # fixed at its value; its range is documentation (other units)
        if not numerics and not np.isnan(lo) and not np.isnan(hi) and (lo < h0 or hi > h1):
            if basis in ("guessed_physical", "physics") or r.get("label") in ("guessed", "published_fit", "inferred"):
                nlo, nhi = max(lo, h0), min(hi, h1)
                if not np.isnan(t):                  # the code's value stays inside (reported above if it is not)
                    nlo, nhi = min(nlo, t), max(nhi, t)
                if values is not None and pid in values and "value" in values[pid]:
                    v = np.asarray([_num(x) for x in values[pid].value])
                    v = v[~np.isnan(v)]
                    if len(v):
                        nlo, nhi = min(nlo, v.min()), max(nhi, v.max())
                if nlo == nhi and r.get("prior_dist") != "fixed":
                    nlo, nhi = lo, hi                # cannot clip without collapsing the range: report only
                    rep["template_outside_hard"].append(f"{pid}: range [{lo:g}, {hi:g}] cannot be clipped")
                else:
                    rep["clipped"].append(f"{pid}: [{lo:g}, {hi:g}] -> [{nlo:g}, {nhi:g}] {r['unit']} ({h['hard_class']})")
                    detail += f"; clipped from [{lo:g}, {hi:g}] to the hard bounds (wranges 7 Nov)"
                    r["bio_min"], r["bio_max"] = nlo, nhi
                    lo, hi = nlo, nhi
                    _clip_prior(r)
            else:
                rep["measured_outside_hard"].append(f"{pid}: measured [{lo:g}, {hi:g}] vs hard [{h0:g}, {h1:g}] "
                                                    f"{r['unit']} ({h['hard_class']}, {old})")
        if not basis:                                # no range of its own (body rows): its hard bounds' basis
            basis = h["hard_basis"]
            detail += "; no range of its own: the basis of its hard bounds"
        if basis == "guessed_physical" and not np.isnan(lo) and _close(lo, h0) and _close(hi, h1):
            basis = "physics"
        r["bound_basis"] = basis
        r["bound_basis_detail"] = detail.strip("; ")
        linear = RULES["classes"].get(h["hard_class"], {}).get("dim") in ("voltage", "inv_voltage") or \
            h["hard_class"] in LINEAR or str(r["unit"]) in ("mV", "mV (model)", "C", "degC", "K")
        sd = math.log10(hi / lo) if not linear and not np.isnan(lo) and lo > 0 and hi > 0 else float("nan")
        r["span_decades"] = round(sd, 3) if not np.isnan(sd) else float("nan")
        why = ""
        if not np.isnan(sd) and sd > 1:
            why = span_reason(pid)
            if not why and basis == "measured_spread":
                why = "measured spread: " + str(r.get("bound_source", ""))[:160]
            if not why and basis == "physics":
                why = "the physical limits themselves"
            src = str(r.get("bound_source", ""))
            if not why and src and not re.match(r"(guessed|not retrieved|this model|kept from before|as |none)", src):
                why = "range source: " + src[:160]
            if not why:
                rep["wide_no_reason"].append(f"{pid}: {sd:.2f} decades [{lo:g}, {hi:g}] {r['unit']}")
        r["span_reason"] = why
        n_unk = _n_unknown(r, values)
        r["n_unknown"] = n_unk
        if r["fit_role"] == "free" and n_unk == 0:
            r["fit_role"] = "static"
        elif r["fit_role"] == "free" and not str(r.get("used_by_code", "yes")).startswith("yes"):
            r["fit_role"] = "inactive"               # unknown, but only another form or a catalog slot reads it
    return rep


UNKNOWN = ("guessed", "absent")


def _n_unknown(r: dict, values: dict | None) -> int:
    """Guessed or absent numbers in a row: its per-element labels if it has a values table, else the row label."""
    t = values.get(r["param_id"]) if values else None
    if t is not None and "label" in t:
        return int(t.label.isin(UNKNOWN).sum())
    n = _num(r.get("n_values"))
    return int(n if not np.isnan(n) else 1) if r.get("label") in UNKNOWN else 0


def _clip_prior(r: dict):
    """Keep the prior consistent with a clipped range."""
    lo, hi = float(r["bio_min"]), float(r["bio_max"])
    d = r.get("prior_dist")
    if d == "loguniform" and lo <= 0:
        r["prior_dist"] = "uniform"
        r["prior_basis"] = str(r.get("prior_basis", "")) + "; uniform after the clip to the hard bounds (a loguniform needs bio_min > 0)"
    if d == "normal" and not lo <= _num(r.get("prior_a")) <= hi:
        r["prior_a"] = min(max(_num(r["prior_a"]), lo), hi)


def report_text(rep: dict) -> str:
    lines = []
    for k, v in rep.items():
        lines.append(f"{k}: {len(v)}")
        lines += [f"  {x}" for x in v[:400]]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    import pandas as pd
    root = Path(__file__).resolve().parents[3]
    p = pd.read_csv(root / "data/worm/model/parameters.csv", keep_default_na=False,
                    na_values={c: [""] for c in ("value_template", "bio_min", "bio_max", "prior_a", "prior_b")})
    rows = p.to_dict("records")
    c = pd.read_csv(root / "data/worm/model/catalog.csv", keep_default_na=False)
    extra = c[~c.id.isin(p.param_id)]
    for x in extra.to_dict("records"):
        rows.append(dict(param_id=x["id"], unit=x["units"], value_template=_num(x["template"]), bio_min=_num(x["bio_min"]),
                         bio_max=_num(x["bio_max"]), bound_basis=x["range_basis"], bound_source=x["range_source"],
                         label=x["label"], prior_dist=""))
    values = {f.stem: pd.read_csv(f, keep_default_na=False) for f in (root / "data/worm/model/values").glob("*.csv")}
    rep = apply(rows, values)
    print(report_text(rep))
    from collections import Counter
    print(Counter(r.get("hard_class") for r in rows).most_common())
    print(Counter(r.get("bound_basis") for r in rows).most_common())
    sys.exit(0)
