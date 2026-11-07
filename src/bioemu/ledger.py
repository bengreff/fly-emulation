"""The parameter ledger, organism-generic (the worm uses it first; the fly's own copy is flyemu/model_data.py).

Same data model as the fly (docs/CONSTRUCTION.md "The data model"): one hand-checked mechanism list and one row per
numeric unknown with hard bounds [bio_min, bio_max], their basis and source, a prior inside them and an evidence
label. Two additions the fly does not have:

- A row can stand for many numbers (a per-cell channel density over 302 neurons is one row, 302 values). `n_values`
  says how many; the per-element values live in `values/<param_id>.csv` (element, value, label, source) when they
  differ by element. Counts per label are taken from those tables, so "how many numbers are measured" is a count
  of numbers, not of rows.
- `value_template` is the number the template organism runs on (the ported value, a literature value or a guess),
  `template_source` where it came from, and `precision_needed` how close to right it has to be (with the method;
  "not yet estimated" until a sensitivity run says otherwise).
- The catalog columns (worm, 6 Nov): `plan_row` (the PLAN.md section a row, 1-28, the number belongs to),
  `used_by_code` ("yes" = the code reads it; "slot only" = a number the row's published model needs that no code
  uses yet; "other form only" = read only when a toggle picks a non-default form, e.g. neuromod's lumped), `source_url` and `source_quote` (where the number is, so an audit can open it) and `audit` ("ok" or
  the problems the scripted and read audit found).
- `source_project` says whose number it is (BAAIWorm, c302, literature, ours, ...) and `fill_kind` is the label in
  words (measured, published fit, derived, inferred (ours), guessed, absent). `published_fit` is a value another
  project fitted or chose and published (BAAIWorm's tuned densities, c302's muscle channels); `inferred` is kept for
  what this project inferred itself. A values table may carry its own `source_project` column per element.

Layout under the model root (e.g. data/worm/model/):
    mechanisms.yaml   id, name, layer, status (have/partial/absent), toggle, neutral, source, notes
    parameters.csv    the columns in PARAM_COLUMNS
    values/*.csv      per-element tables, one per row whose elements differ
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

STATUSES = {"have", "partial", "absent"}
LABELS = {"measured", "published_fit", "derived", "inferred", "guessed", "absent"}
FILL_KIND = {"measured": "measured", "published_fit": "published fit", "derived": "derived",
             "inferred": "inferred (ours)", "guessed": "guessed", "absent": "absent"}
SOURCE_PROJECTS = {"BAAIWorm", "c302", "ChannelWorm", "Sibernetic", "NEURON", "literature", "ours", "none"}
BOUND_BASES = {"measured_this_class", "measured_related", "organism_wide", "physical_limit", "guessed"}
PRIOR_DISTS = {"uniform", "loguniform", "normal", "lognormal", "fixed", "bernoulli", "categorical"}
GRAINS = {"global", "region", "class", "cell", "muscle", "connection", "synapse", "compartment", "gene",
          "family", "pairing", "channel"}
PARAM_COLUMNS = [
    "param_id", "mechanism_id", "grain", "applies_to", "unit", "n_values",
    "value_template", "template_source", "bio_min", "bio_max", "bound_basis", "bound_source", "bound_verified",
    "prior_dist", "prior_a", "prior_b", "prior_basis", "label", "fill_kind", "source_project", "precision_needed",
    "precision_method",
    "toggle", "notes",
    "plan_row", "used_by_code", "source_url", "source_quote", "audit",
]
USED_BY_CODE = {"yes", "slot only", "other form only"}
NUMERIC = ("n_values", "value_template", "bio_min", "bio_max", "prior_a", "prior_b", "plan_row")


@dataclass
class Ledger:
    root: Path
    mechanisms: pd.DataFrame
    parameters: pd.DataFrame

    def values(self, param_id: str) -> pd.DataFrame | None:
        """The per-element table of a row (element, value, label, source), or None if every element takes
        value_template."""
        f = self.root / "values" / f"{param_id}.csv"
        return pd.read_csv(f, keep_default_na=False) if f.exists() else None


def load(root: Path) -> Ledger:
    root = Path(root)
    mech = pd.DataFrame(yaml.safe_load((root / "mechanisms.yaml").read_text()))
    for col in ("toggle", "neutral", "source", "notes", "absent_reason"):
        if col not in mech:
            mech[col] = None
    par = pd.read_csv(root / "parameters.csv", keep_default_na=False,
                      na_values={c: [""] for c in NUMERIC})
    return Ledger(root, mech, par)


def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and np.isnan(v)) or not str(v).strip()


def validate(led: Ledger) -> list[str]:
    """Every rule the sampler and the fitting depend on. [] = valid."""
    bad: list[str] = []
    m, p = led.mechanisms, led.parameters
    ids = set(m.id)
    if missing := [c for c in PARAM_COLUMNS if c not in p.columns]:
        return [f"parameters.csv lacks columns {missing}"]
    if m.id.duplicated().any():
        bad.append(f"duplicate mechanism ids {sorted(m.id[m.id.duplicated()])}")
    for r in m.itertuples():
        if r.status not in STATUSES:
            bad.append(f"{r.id}: status {r.status!r}")
        if not _blank(r.toggle) and _blank(r.neutral):
            bad.append(f"{r.id}: toggle {r.toggle!r} without a neutral setting")
        if r.status == "absent" and _blank(r.absent_reason):
            bad.append(f"{r.id}: absent without absent_reason")
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
        if pd.isna(r.n_values) or r.n_values < 1 or r.n_values != int(r.n_values):
            bad.append(f"{w} n_values {r.n_values!r}")
        if r.label not in LABELS:
            bad.append(f"{w} label {r.label!r}")
        elif r.fill_kind != FILL_KIND[r.label]:
            bad.append(f"{w} fill_kind {r.fill_kind!r} does not match label {r.label!r}")
        if r.source_project not in SOURCE_PROJECTS:
            bad.append(f"{w} source_project {r.source_project!r}")
        if pd.isna(r.plan_row) or not 1 <= int(r.plan_row) <= 28:
            bad.append(f"{w} plan_row {r.plan_row!r}")
        if r.used_by_code not in USED_BY_CODE:
            bad.append(f"{w} used_by_code {r.used_by_code!r}")
        if not r.audit:
            bad.append(f"{w} no audit")
        if not r.precision_needed:
            bad.append(f"{w} no precision_needed (write 'not yet estimated')")
        elif r.precision_needed != "not yet estimated" and not r.precision_method:
            bad.append(f"{w} precision_needed without precision_method")
        if r.label == "absent":                      # a registered gap: no number yet, nothing to check
            continue
        if pd.isna(r.bio_min) or pd.isna(r.bio_max):
            bad.append(f"{w} missing bound")
            continue
        if not r.bio_min <= r.bio_max or (r.prior_dist != "fixed" and r.bio_min == r.bio_max):
            bad.append(f"{w} bio_min {r.bio_min} vs bio_max {r.bio_max}")
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
        if r.prior_dist == "bernoulli" and not (r.bio_min == 0 and r.bio_max == 1 and 0 <= r.prior_a <= 1):
            bad.append(f"{w} bernoulli needs bounds [0, 1] and prior_a = P(1)")
        if r.prior_dist == "loguniform" and r.bio_min <= 0:
            bad.append(f"{w} loguniform needs bio_min > 0")
        if not r.prior_basis:
            bad.append(f"{w} no prior_basis")
        if pd.isna(r.value_template):
            bad.append(f"{w} no value_template")
        elif not r.bio_min <= r.value_template <= r.bio_max:
            bad.append(f"{w} value_template {r.value_template} outside [{r.bio_min}, {r.bio_max}]")
        if not r.template_source:
            bad.append(f"{w} no template_source")
        t = led.values(r.param_id)
        if t is not None:
            if len(t) != int(r.n_values):
                bad.append(f"{w} values table has {len(t)} rows, n_values {int(r.n_values)}")
            if (bl := set(t.label) - LABELS):
                bad.append(f"{w} values table labels {sorted(bl)}")
            if "source_project" in t and (bs := set(t.source_project) - SOURCE_PROJECTS):
                bad.append(f"{w} values table source_project {sorted(bs)}")
            v = pd.to_numeric(t.value, errors="coerce")
            live = t.label != "absent"
            if v[live].isna().any():
                bad.append(f"{w} values table has non-numeric values")
            elif ((v[live] < r.bio_min) | (v[live] > r.bio_max)).any():
                bad.append(f"{w} values table has values outside [{r.bio_min}, {r.bio_max}]")
    owned = set(p.mechanism_id) | {r.id for r in m.itertuples() if not _blank(r.toggle)}
    for r in m.itertuples():
        if r.id not in owned and r.status != "absent":
            bad.append(f"{r.id}: orphan mechanism (no parameter and no toggle)")
    return bad


def draw(rng: np.random.Generator, r, n: int = 1, n_try: int = 1000) -> np.ndarray:
    """n draws from a row's prior truncated to its bounds."""
    lo, hi, d = float(r.bio_min), float(r.bio_max), r.prior_dist
    if d == "fixed":
        return np.full(n, float(r.prior_a))
    if d == "uniform":
        return rng.uniform(lo, hi, n)
    if d == "bernoulli":
        return (rng.random(n) < r.prior_a).astype(float)
    if d == "categorical":                          # integer codes lo..hi, equal weight
        return rng.integers(int(lo), int(hi) + 1, n).astype(float)
    if d == "loguniform":
        return np.exp(rng.uniform(np.log(lo), np.log(hi), n))
    out = np.empty(0)
    for _ in range(n_try):                          # truncated by rejection
        x = rng.normal(r.prior_a, r.prior_b, 4 * n) if d == "normal" else \
            np.exp(rng.normal(np.log(r.prior_a), r.prior_b, 4 * n))
        out = np.concatenate([out, x[(x >= lo) & (x <= hi)]])
        if len(out) >= n:
            return out[:n]
    raise RuntimeError(f"{r.param_id}: prior has almost no mass inside its bounds")


def counts(led: Ledger) -> dict:
    """The hard quantity: numbers (not rows) per label, per grain, per mechanism and per source project."""
    rows = []
    for r in led.parameters.itertuples():
        t = led.values(r.param_id)
        if t is None:
            labs = {(r.label, r.source_project): int(r.n_values)}
        else:
            sp = t.source_project if "source_project" in t else pd.Series(r.source_project, index=t.index)
            labs = pd.DataFrame(dict(l=t.label, s=sp)).value_counts().to_dict()
        for (lab, src), k in labs.items():
            rows.append((r.param_id, r.mechanism_id, r.grain, lab, src, int(k)))
    df = pd.DataFrame(rows, columns=["param_id", "mechanism_id", "grain", "label", "source_project", "n"])
    piv = lambda by: {k: {lab: int(x) for lab, x in g.groupby("label").n.sum().items()}
                      for k, g in df.groupby(by)}
    return {"total_numbers": int(df.n.sum()), "rows": int(len(led.parameters)),
            "by_label": {k: int(v) for k, v in df.groupby("label").n.sum().items()},
            "by_grain": piv("grain"), "by_mechanism": piv("mechanism_id"), "by_source": piv("source_project"),
            "by_param": piv("param_id")}
