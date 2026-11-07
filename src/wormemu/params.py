"""The one parameter API (Ben, 7 Nov 2026): every number the worm uses has a role, and the optimisable vector is the
rule and gap numbers only.

    scan      a number from the scan of the worm (labels measured, published_fit, derived, inferred): fixed, part of
              the built-in mechanism, labelled with its origin only for debugging. Not settable here.
    rule      a shared unknown that generates per-element values from measured structure (mech/structure_rules)
    gap       a genuinely unknown scalar (labels guessed, absent), or one guessed element of a table whose other
              elements are scan (id "param[element]")
    residual  a per-element correction on a rule's output, frozen at 0 (structure_rules.RESIDUALS); exists so the
              true worm is representable, not in the vector until a decision releases it

A number is in the vector (active) when its role is rule or gap and the default model reads it: used_by_code "yes"
in the catalog (other forms, slots and the body's own numbers are counted but left out), not one of the per-element
rows the rules replace (structure_rules.REPLACED, dens_replaced) and not absorbed into a rule's product
(structure_rules.ABSORBED, when guessed). Bounds are the ledger's bio_min / bio_max (wranges' ranges, from
param_ranges.csv and constraints.yaml), else the Spec's. Transform onto the bounds: log-logit (logit of the log
position) when lo > 0, logit otherwise, bernoulli for a 0/1 flag; z = 0 is the bounds' log-midpoint (or midpoint).

    th = Theta()                      # the vector (th.table: id, role, unit, grain, bounds, transform, plan row)
    x = th.get(spec)                  # natural units, from a WormSpec (the template where it carries none)
    spec2 = th.set(spec, x)           # a new WormSpec; Brain(spec2) builds that worm (one Brain per process)
    z = th.to_z(x); x = th.from_z(z)  # the optimiser's unbounded coordinates
    set_value(spec, "pas_cm_uF_cm2", 1.2)        # one number by id; raises ScanValue for a scan number
"""
from __future__ import annotations

import copy
import math
from functools import lru_cache

import numpy as np
import pandas as pd

ROLES = ("scan", "rule", "gap", "residual")
SCAN_LABELS = ("measured", "published_fit", "derived", "inferred")
EPS = 1e-6                                   # a template on a bound sits this far inside it in unit coordinates
RES_N = {"res_epas_cell": 51, "res_dens_class": 189}      # the elements a residual block covers (rest = the row)


class ScanValue(KeyError):
    """A scan number was set through the parameter API."""


def role_of(label: str, explicit: str = "") -> str:
    if explicit:
        assert explicit in ROLES, explicit
        return explicit
    return "scan" if label in SCAN_LABELS else "gap"


def _code_specs():
    from wormemu import brain_layers, mech
    return {s.id: s for s in list(brain_layers.SPECS) + mech.all_specs()}


def _transform(lo, hi, prior):
    if prior in ("bernoulli", "categorical") or (lo == 0 and hi == 1 and prior == "fixed"):
        return "bernoulli"
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi <= lo:
        return "fixed"
    return "log" if lo > 0 else "logit"


@lru_cache(maxsize=4)
def catalog(rules: bool = True) -> pd.DataFrame:
    """Every number the catalog lists (and every code Spec it does not have yet), one row per number or, for a table
    mixing scan and guessed elements, one row per guessed element. Columns: id, pid, element, role, active,
    inactive_why, mechanism, plan_row, unit, grain, n_elements, template, lo, hi, transform, label, origin,
    used_by_code."""
    from bioemu import ledger
    from wormemu.brain import MODEL
    from wormemu.mech import structure_rules as sr
    led = ledger.load(MODEL)
    cat = pd.read_csv(MODEL / "catalog.csv")
    par = led.parameters.set_index("param_id")
    specs = _code_specs()
    replaced = set(sr.REPLACED) | sr.dens_replaced() if rules else set()
    rows = []

    def add(**r):
        rows.append(r)

    for c in cat.itertuples():
        s = specs.get(c.id)
        prior = par.prior_dist.get(c.id, "") if c.id in par.index else ""
        lo = float(c.bio_min) if pd.notna(c.bio_min) else (s.lo if s else np.nan)
        hi = float(c.bio_max) if pd.notna(c.bio_max) else (s.hi if s else np.nan)
        base = dict(pid=c.id, mechanism=c.mechanism, plan_row=c.plan_row, unit=c.units, grain=c.grain,
                    n_elements=int(c.n_elements) if pd.notna(c.n_elements) else 1, lo=lo, hi=hi,
                    transform=_transform(lo, hi, prior), origin=c.origin, used_by_code=str(c.used_by_code))
        why = ("" if base["used_by_code"] == "yes" else base["used_by_code"].split(":")[0])
        if c.id in replaced:
            why = "replaced by structure_rules"
        elif rules and c.id in sr.ABSORBED and c.label not in SCAN_LABELS:
            why = f"absorbed into {sr.ABSORBED[c.id]} (only the product enters)"
        t = led.values(c.id) if c.id in par.index else None
        if t is not None and base["n_elements"] > 1 and why == "":
            gl = t[~t.label.isin(SCAN_LABELS)]
            if len(gl) and len(gl) < len(t):          # a mixed table: its guessed elements are gaps one by one
                add(id=c.id, element=None, role="scan", active=False, inactive_why="scan elements", label=c.label,
                    template=np.nan, **base)
                for e, v, lab in zip(gl.element, gl.value, gl.label):
                    add(id=f"{c.id}[{e}]", element=e, role="gap", active=True, inactive_why="", label=lab,
                        template=float(v), **dict(base, n_elements=1))
                continue
        # the ledger's or the code's full-precision template (the catalog's is rounded for reading)
        tmpl = (float(par.value_template[c.id]) if c.id in par.index and pd.notna(par.value_template[c.id]) else
                float(s.template) if s else pd.to_numeric(c.template, errors="coerce"))
        role = role_of(c.label, s.role if s else "")
        if role == "gap" and t is not None and (t.label.isin(SCAN_LABELS)).all():
            role = "scan"                             # a row label of guessed over a table that is all scan
        add(id=c.id, element=None, role=role, active=role in ("rule", "gap") and why == "", inactive_why=why,
            label=c.label, template=tmpl, **base)
    have = set(cat.id)
    from wormemu import mech
    on = {t[0]: t[3] for m in mech.modules() for t in m.MECHANISMS}
    for s in specs.values():                          # code Specs the catalog has not caught up with yet
        if s.id in have:
            continue
        role = role_of(s.label, s.role)
        why = "" if mech.is_on(on.get(s.mechanism, "on")) else f"toggle {s.mechanism} off by default"
        if not rules and s.mechanism == sr.M:
            why = "structure_rules off"
        add(id=s.id, pid=s.id, element=None, role=role, active=role in ("rule", "gap") and why == "",
            inactive_why=why, mechanism=s.mechanism, plan_row=np.nan, unit=s.unit, grain=s.grain, n_elements=1,
            template=float(s.template), lo=float(s.lo), hi=float(s.hi), transform=_transform(s.lo, s.hi, ""),
            label=s.label, origin="code (not in the catalog yet)", used_by_code="yes")
    for rid, (old, grain, what) in sr.RESIDUALS.items():
        add(id=rid, pid=rid, element=None, role="residual", active=False, inactive_why="frozen at 0",
            mechanism=sr.M, plan_row=np.nan, unit="log factor" if not rid.startswith("res_epas") else "mV",
            grain=grain, n_elements=RES_N.get(rid) or int(par.n_values.get(old, 0)),
            template=0.0, lo=-np.inf, hi=np.inf, transform="fixed", label="guessed", origin="structure_rules",
            used_by_code="yes")
    df = pd.DataFrame(rows)
    df.loc[~df.active & df.inactive_why.eq("") & df.role.isin(["rule", "gap"]), "inactive_why"] = "not read"
    return df


class Theta:
    """The optimisable vector: active rule and gap numbers, in catalog order."""

    def __init__(self, rules: bool = True, table: pd.DataFrame | None = None):
        cat = catalog(rules) if table is None else table
        self.table = cat[cat.active & cat.role.isin(["rule", "gap"])].reset_index(drop=True)
        t = self.table
        self.ids = list(t.id)
        self.n = len(t)
        self.lo, self.hi = t.lo.to_numpy(float), t.hi.to_numpy(float)
        self.kind = t["transform"].to_numpy()
        self.x0 = t.template.to_numpy(float)

    # --- coordinates -------------------------------------------------------------------------------------------
    def to_unit(self, x):
        x = np.asarray(x, float)
        u = np.full(self.n, 0.5)
        lg = self.kind == "log"
        li = (self.kind == "logit") | (self.kind == "bernoulli")
        with np.errstate(divide="ignore", invalid="ignore"):
            u[lg] = (np.log(x[lg]) - np.log(self.lo[lg])) / (np.log(self.hi[lg]) - np.log(self.lo[lg]))
        u[li] = (x[li] - self.lo[li]) / (self.hi[li] - self.lo[li])
        return np.clip(u, EPS, 1 - EPS)

    def from_unit(self, u):
        u = np.asarray(u, float)
        x = self.x0.copy()
        lg, li, bn = self.kind == "log", self.kind == "logit", self.kind == "bernoulli"
        x[lg] = np.exp(np.log(self.lo[lg]) + u[lg] * (np.log(self.hi[lg]) - np.log(self.lo[lg])))
        x[li] = self.lo[li] + u[li] * (self.hi[li] - self.lo[li])
        x[bn] = (u[bn] >= 0.5).astype(float)
        lo_, hi_ = u <= EPS * 1.001, u >= 1 - EPS * 1.001                     # a bound is reachable exactly
        x = np.where(lo_, self.lo, np.where(hi_, self.hi, x))
        return np.where(self.kind == "fixed", self.x0, x)

    def to_z(self, x):
        u = self.to_unit(x)
        return np.log(u / (1 - u))

    def from_z(self, z):
        return self.from_unit(1.0 / (1.0 + np.exp(-np.asarray(z, float))))

    # --- a worm's values ---------------------------------------------------------------------------------------
    def get(self, spec):
        out = np.empty(self.n)
        for k, r in enumerate(self.table.itertuples()):
            v = spec.values.get(r.pid)
            if v is None:
                out[k] = r.template
            elif r.element is not None and isinstance(r.element, str):
                out[k] = float(v[r.element])
            else:
                out[k] = float(v)
        return out

    def set(self, spec, x):
        """A copy of the WormSpec with the vector's numbers replaced (tables copied before an element is set)."""
        x = np.asarray(x, float)
        assert x.shape == (self.n,), x.shape
        vals = dict(spec.values)
        copied = set()
        for k, r in enumerate(self.table.itertuples()):
            if isinstance(r.element, str):
                if r.pid not in copied:
                    vals[r.pid] = vals[r.pid].copy()
                    copied.add(r.pid)
                vals[r.pid][r.element] = x[k]
            else:
                vals[r.pid] = float(x[k])
        out = copy.copy(spec)
        out.values = vals
        return out

    def summary(self):
        """Counts of the vector by role, mechanism and grain."""
        return self.table.groupby(["role", "mechanism", "grain"]).size().rename("n").reset_index()


def set_value(spec, pid, x, element=None, rules: bool = True):
    """Set one number by id (a rule or gap, or a residual's element); a scan number raises ScanValue."""
    cat = catalog(rules)
    key = f"{pid}[{element}]" if element is not None and f"{pid}[{element}]" in set(cat.id) else pid
    r = cat[cat.id == key]
    if not len(r):
        raise KeyError(pid)
    r = r.iloc[0]
    if r.role == "scan":
        raise ScanValue(f"{key} is a scan number ({r.label}); it is fixed")
    vals = dict(spec.values)
    if r.role == "residual":
        s = vals.get(pid)
        s = pd.Series(dtype=float) if s is None else s.copy()
        s[element] = float(x)
        vals[pid] = s
    elif element is not None:
        vals[pid] = vals[pid].copy()
        vals[pid][element] = float(x)
    else:
        vals[pid] = float(x)
    out = copy.copy(spec)
    out.values = vals
    return out


def counts(rules: bool = True) -> dict:
    """The headline numbers: vector size by role, scan numbers and elements, residual slots, inactive unknowns."""
    cat = catalog(rules)
    act = cat[cat.active]
    sc = cat[cat.role == "scan"]
    return dict(vector=int(len(act)), rule=int((act.role == "rule").sum()), gap=int((act.role == "gap").sum()),
                gap_discrete=int(((act.role == "gap") & (act["transform"] == "bernoulli")).sum()),
                scan_rows=int(len(sc)), scan_elements=int(sc.n_elements.sum()),
                residual_slots=int(cat[cat.role == "residual"].n_elements.sum()),
                unknown_inactive=int((~cat.active & cat.role.isin(["rule", "gap"])).sum()))
