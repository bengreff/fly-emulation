"""Feasibility-probe helpers (wtriage, 8 Nov 2026; DEBUG_PASS_PLAN phase 1). Nothing here is adopted.

A probe asks one question: is there a value of the gap/rule numbers a failing check depends on, inside their allowed
ranges, at which the check passes? It never writes the ledger, the catalog, templates or src/.

Two boxes per id, both through the params API's transform kind (log when lo > 0, else linear):
  bio   the API's own bounds (ledger bio_min/bio_max, else the Spec's lo/hi): what params.Theta searches
  hard  the ledger's hard_min/hard_max where they exist (physics or definition), else the bio box
Points are scrambled Sobol in the unit cube. Every point is also run through the joint constraints
(scripts/worm/ranges/joint.check); a point that breaks a hard constraint does not count as a pass.

Usage from a probe script:
    from probe_lib import Box, ledger_values, joint_bad, summarise
    box = Box(["rec_tmax_gaba_uM", "rec_gabacl_tau_rise_ms"])
    X = box.design(128, which="bio", seed=0)     # (n, d) natural units
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "ranges"))

OUT = ROOT / "runs" / "worm" / "triage"


def _f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def ledger_rows():
    return {r["param_id"]: r for r in csv.DictReader(open(ROOT / "data/worm/model/parameters.csv"))}


def ledger_values():
    """id -> ledger value_template (float) for scalar rows; the values the brain runs."""
    return {k: _f(r["value_template"]) for k, r in ledger_rows().items() if _f(r["value_template"]) is not None}


class Box:
    def __init__(self, ids):
        from wormemu import params
        cat = params.catalog().set_index("id")
        led = ledger_rows()
        self.ids = list(ids)
        self.rows = []
        for i in self.ids:
            r = cat.loc[i]
            assert r.role in ("rule", "gap"), f"{i} is {r.role}: a scan number is never probed"
            lo, hi = float(r.lo), float(r.hi)
            pid = r.pid
            hmin = _f(led.get(pid, {}).get("hard_min")) if pid in led else None
            hmax = _f(led.get(pid, {}).get("hard_max")) if pid in led else None
            hlo = min(lo, hmin) if hmin is not None else lo
            hhi = max(hi, hmax) if hmax is not None else hi
            kind = "log" if lo > 0 else "lin"
            if kind == "log" and hlo <= 0:
                hlo = lo                      # a log axis cannot reach 0; keep the bio lower end there
            self.rows.append(dict(id=i, pid=pid, role=r.role, active=bool(r.active), label=r.label,
                                  template=float(r.template), lo=lo, hi=hi, hard_lo=hlo, hard_hi=hhi, kind=kind,
                                  unit=r.unit))

    def from_unit(self, U, which="bio"):
        U = np.atleast_2d(U)
        X = np.empty_like(U, dtype=float)
        for j, r in enumerate(self.rows):
            lo, hi = (r["lo"], r["hi"]) if which == "bio" else (r["hard_lo"], r["hard_hi"])
            if r["kind"] == "log":
                X[:, j] = np.exp(np.log(lo) + U[:, j] * (np.log(hi) - np.log(lo)))
            else:
                X[:, j] = lo + U[:, j] * (hi - lo)
        return X

    def design(self, n, which="bio", seed=0):
        from scipy.stats import qmc
        U = qmc.Sobol(len(self.ids), scramble=True, seed=seed).random(n)
        return self.from_unit(U, which)

    def in_bio(self, x):
        return all(r["lo"] <= v <= r["hi"] for r, v in zip(self.rows, x))

    def at_edge(self, x, frac=0.05, which="bio"):
        """ids whose value sits within frac of either end of the box (in the transform's coordinate)."""
        out = []
        for r, v in zip(self.rows, x):
            lo, hi = (r["lo"], r["hi"]) if which == "bio" else (r["hard_lo"], r["hard_hi"])
            if r["kind"] == "log":
                u = (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo))
            else:
                u = (v - lo) / (hi - lo)
            if u < frac or u > 1 - frac:
                out.append(f"{r['id']} ({'low' if u < frac else 'high'} end, u={u:.3f})")
        return out

    def describe(self):
        return [{k: r[k] for k in ("id", "role", "label", "template", "lo", "hi", "hard_lo", "hard_hi", "kind",
                                   "unit")} for r in self.rows]


_JOINT = {}


def joint_bad(updates: dict, ids=None):
    """Hard joint-constraint violations at the ledger worm with these scalar values replaced (only those that name
    one of `ids`, default the updated ids)."""
    import joint
    from bioemu import ledger
    from wormemu import brain as B
    if "base" not in _JOINT:
        led = ledger.load(B.MODEL)
        _JOINT["led"] = led
        _JOINT["cons"] = [c for c in joint.constraints(led) if c.get("strength") == "hard"]
        _JOINT["base"] = B.sample_worm(None).values
    vals = dict(_JOINT["base"])
    vals.update({k: float(v) for k, v in updates.items()})
    ids = set(ids or updates)
    cons = [c for c in _JOINT["cons"] if ids & set(json.dumps(c).replace('"', " ").split())]
    return joint.check(vals, _JOINT["led"], cons=cons)


def summarise(box, X, score, passed, which, bar, extra=None):
    """One probe's result: pass fraction, best point (smallest margin-normalised miss), edges, bio-box membership."""
    score = np.asarray(score, float)
    passed = np.asarray(passed, bool)
    ok = np.isfinite(score)
    res = dict(box=which, n=int(len(X)), n_finite=int(ok.sum()), n_pass=int(passed.sum()),
               pass_fraction=float(passed.mean()) if len(X) else 0.0, bar=bar, ids=box.ids,
               bounds=box.describe())
    if extra:
        res.update(extra)
    return res


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(obj, indent=1, default=float))
    return p
