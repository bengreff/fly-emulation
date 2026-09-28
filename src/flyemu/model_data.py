"""The construction data model: mechanisms, unknowns and their biological bounds.

docs/CONSTRUCTION.md ("The data model"). Three hand-edited tables under
data/model/ are authoritative:

    mechanisms.yaml       one entry per mechanism of the complete-fly template
    parameters.csv        one row per numeric unknown, with hard bounds
                          [bio_min, bio_max], their basis and source, a prior
                          inside them and a release stage
    structural_keys.csv   registry keys that are data, discrete assignments,
                          policies, switches or registered absences

The registry (registry.py) and profiles stay the way the model reads values;
this module is the table they must agree with. `coverage()` maps every live
registry key to the rows that own it, and `validate()` enforces the rules the
search depends on: every unknown has bounds, a basis, a prior and a label, and
belongs to exactly one mechanism; nothing (prior centre, fixed value, current
m4 value) lies outside its bounds.

`sample(seed, stage)` draws every parameter released at or before `stage`
from its prior truncated to its bounds; the rest stay at their current value.
It is the numeric core of sample_fly (task 13), not yet wired into Organism.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

MODEL = Path(__file__).resolve().parents[2] / "data" / "model"

# The construction template's body configuration: every body switch built so
# far, on. m4 keeps them all at 0 (legacy). One definition, used by probes
# (`closed_loop_check.py --template`) so the set cannot be mistyped.
TEMPLATE_SWITCHES = {
    "joint:leg|passive_stiffness_source": 2.0,   # B3 coupled projected springs (F-PASSIVE-2)
    "joint:leg|spring_reference": 1.0,           # B3 fitted rest angles (F-REST-2)
    "joint:wing|spring_reference": 1.0,          # B14 folded wings
    "muscle:leg|model": 1.0,                     # B4/B5 Hill pairs (rotators by action)
    "adhesion:leg|detachment": 1.0,              # B7 load/shear gate
    # session 10
    "muscle:leg|coxa_model": 1.0,                # B4 anatomical coxa muscles, 3-axis moment arms
    "joint:wing|range_by_function": 1.0,         # B14 wing envelopes by function (F-WING-1)
    "sense:antenna|oscillator": 1.0,             # B20 antenna oscillator + JO-A/B
    "jump:ttm|model": 1.0,                       # B15 TTM jump twitch
    "state:organs|model": 1.0,                   # S1-S4, N20, N25, N26 internal state
    "state:crop|pump_gated": 1.0,                # B17 ingestion gated by the pump MNs
}
# Not in the walking template: flight:wings|generator (needs timestep <= 0.05 ms;
# flight is run as its own configuration, tethered_lift.py / phase_lock.py).

TIERS = {"A", "B", "C"}
STATUSES = {"have", "partial", "absent"}
BOUND_BASES = {"measured_this_class", "measured_related", "insect_wide",
               "physical_limit", "guessed"}
BOUND_FROM_DATA = BOUND_BASES - {"guessed"}
PRIOR_DISTS = {"uniform", "loguniform", "normal", "lognormal", "fixed", "bernoulli"}
LABELS = {"measured", "derived", "inferred", "guessed"}
STRUCT_KINDS = {"data", "assignment", "policy", "switch", "absent"}
GRAINS = {"global", "region", "class", "type", "cell", "joint", "muscle", "compartment"}


@dataclass
class ModelData:
    mechanisms: pd.DataFrame
    parameters: pd.DataFrame
    structural: pd.DataFrame


def load(root: Path = MODEL) -> ModelData:
    mech = pd.DataFrame(yaml.safe_load((root / "mechanisms.yaml").read_text()))
    for col in ("switch", "test"):
        mech[col] = mech[col].apply(lambda v: list(v) if isinstance(v, list) else [])
    for col in ("absent_reason", "infrastructure", "notes", "neutral"):
        if col not in mech:
            mech[col] = None
    mech["infrastructure"] = mech.infrastructure.fillna(False).astype(bool)
    par = pd.read_csv(root / "parameters.csv", dtype={"registry_key": str},
                      keep_default_na=False, na_values={
                          c: [""] for c in ("bio_min", "bio_max", "prior_a", "prior_b",
                                            "value_fixed", "current_m4", "release_stage")})
    st = pd.read_csv(root / "structural_keys.csv", comment="#", keep_default_na=False)
    return ModelData(mech, par, st)


# --- key matching --------------------------------------------------------------

def _pattern(p: str) -> re.Pattern:
    """entity|property with `*` as the only wildcard (keys contain regex text)."""
    return re.compile("^" + ".*".join(re.escape(s) for s in p.split("*")) + "$")


def owners(md: ModelData, key: str) -> list[tuple[str, str, str]]:
    """(source, row id, mechanism_id) of every row whose pattern matches `key`."""
    out = []
    for r in md.parameters.itertuples():
        if r.registry_key and _pattern(r.registry_key).match(key):
            out.append(("parameters", r.param_id, r.mechanism_id))
    for r in md.structural.itertuples():
        if _pattern(r.key_pattern).match(key):
            out.append(("structural", r.key_pattern, r.mechanism_id))
    for r in md.mechanisms.itertuples():
        for s in r.switch:
            if _pattern(s).match(key):
                out.append(("switch", s, r.id))
    return out


def coverage(md: ModelData, keys) -> pd.DataFrame:
    """One row per registry key: its owning mechanism(s); empty = orphan key."""
    rows = []
    for k in keys:
        o = owners(md, k)
        rows.append(dict(key=k, n_rows=len(o),
                         mechanisms=";".join(sorted({m for *_, m in o}))))
    return pd.DataFrame(rows)


# --- validation ----------------------------------------------------------------

def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and np.isnan(v)) or not str(v).strip()


def _prior_centre(r) -> float | None:
    if r.prior_dist in ("normal", "lognormal", "fixed"):
        return r.prior_a
    return None


def validate(md: ModelData) -> list[str]:
    """Every rule the search depends on. Returns the problems; [] = valid."""
    bad: list[str] = []
    m, p, s = md.mechanisms, md.parameters, md.structural
    ids = set(m.id)
    if m.id.duplicated().any():
        bad.append(f"duplicate mechanism ids {sorted(m.id[m.id.duplicated()])}")
    for r in m.itertuples():
        if r.tier not in TIERS:
            bad.append(f"{r.id}: tier {r.tier!r}")
        if r.status not in STATUSES:
            bad.append(f"{r.id}: status {r.status!r}")
        if r.tier == "C" and r.status == "absent" and _blank(r.absent_reason):
            bad.append(f"{r.id}: tier C absent without absent_reason")
    if p.param_id.duplicated().any():
        bad.append(f"duplicate param ids {sorted(p.param_id[p.param_id.duplicated()])}")
    for r in p.itertuples():
        w = f"{r.param_id}:"
        if r.mechanism_id not in ids:
            bad.append(f"{w} unknown mechanism {r.mechanism_id!r}")
        if r.grain not in GRAINS:
            bad.append(f"{w} grain {r.grain!r}")
        if not r.unit:
            bad.append(f"{w} no unit")
        if pd.isna(r.bio_min) or pd.isna(r.bio_max):
            bad.append(f"{w} missing bound")
            continue
        if not r.bio_min < r.bio_max:
            bad.append(f"{w} bio_min {r.bio_min} >= bio_max {r.bio_max}")
        if r.bound_basis not in BOUND_BASES:
            bad.append(f"{w} bound_basis {r.bound_basis!r}")
        if not r.bound_source:
            bad.append(f"{w} bound without a source")
        if r.bound_verified not in ("verified", "unverified"):
            bad.append(f"{w} bound_verified {r.bound_verified!r}")
        if r.prior_dist not in PRIOR_DISTS:
            bad.append(f"{w} prior_dist {r.prior_dist!r}")
        if r.prior_dist in ("normal", "lognormal") and (pd.isna(r.prior_a) or pd.isna(r.prior_b)):
            bad.append(f"{w} {r.prior_dist} prior needs prior_a and prior_b")
        if r.prior_dist == "bernoulli" and not (r.bio_min == 0 and r.bio_max == 1
                                                 and 0 <= r.prior_a <= 1):
            bad.append(f"{w} bernoulli needs bounds [0, 1] and prior_a = P(1) in [0, 1]")
        if r.prior_dist == "fixed" and pd.isna(r.prior_a):
            bad.append(f"{w} fixed prior needs prior_a")
        if r.prior_dist == "loguniform" and r.bio_min <= 0:
            bad.append(f"{w} loguniform needs bio_min > 0")
        if not r.prior_basis:
            bad.append(f"{w} no prior_basis")
        if r.label not in LABELS:
            bad.append(f"{w} label {r.label!r}")
        if r.release_stage not in (0, 1, 2):
            bad.append(f"{w} release_stage {r.release_stage!r}")
        # current_m4 must lie inside the bounds where the table governs the value
        # (wired rows); legacy values of unwired rows are reported by
        # legacy_outside_bounds() instead, never hidden by widening a bound
        cur = r.current_m4 if r.registry_key else None
        for name, v in (("prior centre", _prior_centre(r)), ("value_fixed", r.value_fixed),
                        ("current_m4", cur)):
            if v is not None and not pd.isna(v) and not r.bio_min <= v <= r.bio_max:
                bad.append(f"{w} {name} {v} outside [{r.bio_min}, {r.bio_max}]")
        if not pd.isna(r.value_fixed) and r.label not in ("measured", "derived"):
            bad.append(f"{w} value_fixed must be measured or derived (label {r.label})")
    for r in s.itertuples():
        if r.mechanism_id not in ids:
            bad.append(f"structural {r.key_pattern}: unknown mechanism {r.mechanism_id!r}")
        if r.kind not in STRUCT_KINDS:
            bad.append(f"structural {r.key_pattern}: kind {r.kind!r}")
    # no orphan mechanisms: each one owns at least one unknown or structural key
    owned = set(p.mechanism_id) | set(s.mechanism_id) | {
        r.id for r in m.itertuples() if r.switch}
    for r in m.itertuples():
        if r.id not in owned:
            bad.append(f"{r.id}: orphan mechanism (no parameter, structural key or switch)")
    return bad


def legacy_outside_bounds(md: ModelData) -> list[str]:
    """Unwired rows whose legacy (m4) body value lies outside the biological
    bounds: places where the legacy model is known to be unbiological."""
    p = md.parameters
    bad = p[(p.registry_key == "") & p.current_m4.notna()
            & ((p.current_m4 < p.bio_min) | (p.current_m4 > p.bio_max))]
    return [f"{r.param_id}: m4 {r.current_m4} outside [{r.bio_min}, {r.bio_max}]"
            for r in bad.itertuples()]


def ambiguous_keys(md: ModelData, keys) -> list[str]:
    """Registry keys owned by more than one mechanism (principle 4)."""
    cov = coverage(md, keys)
    return [f"{k} -> {m}" for k, m in zip(cov.key, cov.mechanisms) if ";" in m]


# --- sampling ------------------------------------------------------------------

def _draw(rng: np.random.Generator, r, n_try: int = 1000) -> float:
    lo, hi = float(r.bio_min), float(r.bio_max)
    d = r.prior_dist
    if d == "fixed":
        return float(r.prior_a)
    if d == "uniform":
        return float(rng.uniform(lo, hi))
    if d == "bernoulli":                       # a discrete unknown (e.g. graded mode)
        return float(rng.random() < r.prior_a)
    if d == "loguniform":
        return float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
    for _ in range(n_try):                    # truncated to the bounds by rejection
        if d == "normal":
            x = rng.normal(r.prior_a, r.prior_b)
        else:
            x = float(np.exp(rng.normal(np.log(r.prior_a), r.prior_b)))
        if lo <= x <= hi:
            return float(x)
    raise RuntimeError(f"{r.param_id}: prior has almost no mass inside its bounds")


def sample(md: ModelData, seed: int, stage: int = 1) -> pd.Series:
    """Values for every parameter: released ones (release_stage <= stage, >0)
    drawn from their truncated priors; measured fixed values fixed; others at
    their current m4 value, else at the prior centre, else the bound midpoint."""
    rng = np.random.default_rng(seed)
    out = {}
    for r in md.parameters.itertuples():
        if not pd.isna(r.value_fixed):
            out[r.param_id] = float(r.value_fixed)
        elif 0 < r.release_stage <= stage:
            out[r.param_id] = _draw(rng, r)
        elif not pd.isna(r.current_m4):
            out[r.param_id] = float(r.current_m4)
        elif _prior_centre(r) is not None:
            out[r.param_id] = float(_prior_centre(r))
        else:
            out[r.param_id] = 0.5 * (float(r.bio_min) + float(r.bio_max))
    return pd.Series(out, name=f"seed{seed}_stage{stage}")


def registry_overrides(md: ModelData, values: pd.Series) -> dict[str, float]:
    """The sampled values as registry overrides, for rows with one concrete key.
    Wildcard rows (per-type/per-class tables) and unwired rows are not included."""
    p = md.parameters.set_index("param_id")
    return {p.at[i, "registry_key"]: float(v) for i, v in values.items()
            if p.at[i, "registry_key"] and "*" not in p.at[i, "registry_key"]}


# joint constraints between parameters that the per-row bounds cannot express
# (s10): a threshold must lie above rest, the reset at or below threshold
JOINT_CONSTRAINTS = (
    ("n2_v_th", "n2_v_rest", 2.0),        # v_th - v_rest >= 2 mV
    ("n2_v_th", "n2_v_reset", 0.5),       # v_th - v_reset >= 0.5 mV
)


def sample_fly(md: ModelData, seed: int, stage: int = 1, max_tries: int = 1000) -> dict[str, float]:
    """Task 13: one complete template fly. The template body switches plus every
    released parameter drawn from its prior inside its bounds (rejection on the
    joint constraints), as registry overrides. stage 0 = the template body with
    the m4 brain."""
    ids = set(md.parameters.param_id)
    for k in range(max_tries):
        v = sample(md, seed * 100_003 + k if k else seed, stage)
        if all(a not in ids or b not in ids or v[a] - v[b] >= gap for a, b, gap in JOINT_CONSTRAINTS):
            return {**TEMPLATE_SWITCHES, **registry_overrides(md, v)}
    raise RuntimeError(f"seed {seed}: no draw satisfies the joint constraints")


# --- ledger --------------------------------------------------------------------

def construction_state(md: ModelData) -> dict:
    m = md.mechanisms[~md.mechanisms.infrastructure]
    p = md.parameters
    return dict(
        mechanisms=m.pivot_table(index="tier", columns="status", values="id",
                                 aggfunc="count", fill_value=0),
        n_mechanisms=len(m),
        n_unknowns=len(p),
        bounded_by_data=int(p.bound_basis.isin(BOUND_FROM_DATA).sum()),
        bounds_verified=int((p.bound_verified == "verified").sum()),
        fixed_by_measurement=int(p.value_fixed.notna().sum()),
        wired=int((p.registry_key != "").sum()),
        legacy_outside_bounds=legacy_outside_bounds(md),
        by_stage=p.release_stage.value_counts().sort_index(),
        by_label=p.label.value_counts(),
        absent_c_without_reason=[r.id for r in m.itertuples() if r.tier == "C"
                                 and r.status == "absent" and _blank(r.absent_reason)],
    )
