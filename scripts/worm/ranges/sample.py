"""Sampling check of the ranges (wranges, 7 Nov 2026): do worms drawn from the priors obey the joint constraints, and
does a drawn worm run without leaving physics? Checks the ranges; it scores nothing against behaviour and fits
nothing.

    python scripts/worm/ranges/sample.py joint N           N draws (seeds 1..N), constraints only, no simulation
    python scripts/worm/ranges/sample.py one SEED SECONDS [toggle=form ...]   one worm (a diagnosis may change forms)
    python scripts/worm/ranges/sample.py diag SEED SECONDS  one worm: the cell, step and injected currents of its
                                                           lowest and highest voltage, and the most-moved draws
    python scripts/worm/ranges/sample.py run N SECONDS     seeds 1..N, each redrawn (seed + 1000 k) until it obeys
                                                           data/worm/model/constraints.yaml, then the brain runs
                                                           SECONDS with the code's default toggles (everything on),
                                                           no injected current, default observation (no body)

Pass, per worm and every 0.5 ms step read at 1 ms: every voltage and Ca finite; every voltage inside the hard
reversal envelope [lowest hard E_K, highest hard E_Ca] (no cell can leave it without injected current; the senses'
transduction currents are the only currents added); Ca >= 0; every mechanism output finite, and >= 0 where it is a
concentration, count, store or activation; activations in [0, 1].
Writes runs/worm/wranges/sample_<mode>.json.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

import joint  # noqa: E402
from bioemu import ledger  # noqa: E402
from wormemu.brain import MODEL, sample_worm  # noqa: E402

OUT = ROOT / "runs" / "worm" / "wranges"
SIGNED = ("dff", "delta", "_dv", "current", "i_pa", "drive")      # may be negative: dF/F below rest, currents
NONNEG = ("conc", "_um", "_nm", "_mm", "ca", "store", "energy", "count", "n_", "act", "frac", "occup", "level")


def _flat(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _flat(v, f"{pre}{k}.")
        return
    try:
        a = np.asarray(x, float)
    except (TypeError, ValueError):
        return
    yield pre.rstrip("."), a


def envelope(led) -> tuple[float, float]:
    p = led.parameters
    rev = p[p.hard_class.astype(str).str.startswith("reversal_")]
    return float(rev.hard_min.min()), float(rev.hard_max.max())


def default_breaks(bad, led):
    """The broken constraints the default worm feels: those naming no row it leaves unread (fit_role inactive)."""
    p = led.parameters
    off = set(p.param_id[p.fit_role == "inactive"])
    return [b for b in bad if not off & set(re.findall(r"[a-z][a-z0-9_]+", b.split(":", 1)[1]))]


def draw(seed, led, cons, tries=50):
    """sample_worm(seed + 1000 k) for the first k that obeys every constraint the default worm feels; the broken ones
    are recorded."""
    rejected = []
    for k in range(tries):
        s = seed + 1000 * k
        spec = sample_worm(s)
        bad = default_breaks(joint.check(spec.values, led, cons), led)
        if not bad:
            return spec, rejected
        rejected.append(dict(seed=s, broken=[b.split(":")[0] for b in bad]))
    raise RuntimeError(f"seed {seed}: no draw in {tries} obeys the constraints")


def mode_joint(n):
    led = ledger.load(MODEL)
    cons = joint.constraints(led)
    per, per_d = Counter(), Counter()
    nbad = nbad_d = 0
    for s in range(1, n + 1):
        bad = joint.check(sample_worm(s).values, led, cons)
        d = default_breaks(bad, led)
        nbad, nbad_d = nbad + bool(bad), nbad_d + bool(d)
        per.update(b.split(":")[0] for b in bad)
        per_d.update(b.split(":", 1)[0] + ":" + b.split(":", 1)[1].split()[0] for b in d)
    res = dict(mode="joint", draws=n, draws_breaking_any=nbad, draws_breaking_default_worm=nbad_d,
               by_constraint=dict(per.most_common()), default_worm_by_row=dict(per_d.most_common()))
    return res


def one(s, seconds, toggles=None):
    """One worm in this process (NEURON keeps every cell it built, so each worm gets a fresh process). toggles: forms
    that differ from the code's defaults (a diagnosis, e.g. glia_kbuffer=fixed)."""
    from wormemu.brain import Brain
    led = ledger.load(MODEL)
    cons = joint.constraints(led)
    vlo, vhi = envelope(led)
    t0 = time.time()
    spec, rejected = draw(s, led, cons)
    b = Brain(spec, toggles=toggles)
    o = b.reset()
    fail = Counter()
    vmin, vmax, camin = np.inf, -np.inf, np.inf
    omin = {}
    for _ in range(int(round(seconds * 1000))):
        o = b.step(None, 1.0)
        v, ca = o.v_mV, o.ca_uM
        if not (np.isfinite(v).all() and np.isfinite(ca).all()):
            fail["nonfinite_v_or_ca"] += 1
        vmin, vmax = min(vmin, float(np.nanmin(v))), max(vmax, float(np.nanmax(v)))
        camin = min(camin, float(np.nanmin(ca)))
        for name in ("muscle_activation", "pharynx_activation", "enteric_activation", "sex_muscle_activation"):
            a = np.asarray(getattr(o, name), float)
            if a.size and not (np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1):
                fail[f"{name}_outside_0_1"] += 1
        for k, a in _flat(b.mech_out):
            if a.size == 0:
                continue
            if not np.isfinite(a).all():
                fail[f"nonfinite:{k}"] += 1
                continue
            omin[k] = min(omin.get(k, np.inf), float(a.min()))
    if vmin < vlo or vmax > vhi:
        fail["v_outside_reversal_envelope"] += 1
    if camin < 0:
        fail["negative_ca"] += 1
    neg = {k: m for k, m in omin.items() if m < 0 and any(t in k.lower() for t in NONNEG)
           and not any(t in k.lower() for t in SIGNED)}
    for k in neg:
        fail[f"negative:{k}"] += 1
    return dict(seed=s, used_seed=spec.seed, rejected=rejected, wall_s=round(time.time() - t0, 1),
                v_min=round(vmin, 2), v_max=round(vmax, 2), ca_min_uM=camin, negative_outputs=neg,
                fail=dict(fail), ok=not fail, envelope_mV=[vlo, vhi], toggles=toggles or {})


def diag(s, seconds):
    """Where a worm leaves the envelope: the cell and step of its lowest and highest voltage, the injected currents
    into that cell then (each layer and each mechanism's I_pA), and the drawn numbers that differ most from the
    template worm."""
    from wormemu.brain import Brain
    led = ledger.load(MODEL)
    cons = joint.constraints(led)
    spec, _ = draw(s, led, cons)
    b = Brain(spec)
    b.reset()
    L, parts = b.layers, {}
    for name in ("sensory_current", "modulator_current", "homeostatic_current"):
        f = getattr(L, name)
        setattr(L, name, lambda *a, _f=f, _n=name: parts.__setitem__(_n, np.asarray(_f(*a), float)) or parts[_n])
    for m in b.mechs:
        f = m.step
        def wrapped(ctx, dt, _f=f, _m=m):
            r = _f(ctx, dt)
            if "I_pA" in r:
                parts[f"mech:{type(_m).__module__.rsplit('.', 1)[-1]}"] = np.broadcast_to(
                    np.asarray(r["I_pA"], float), (len(b.cell_names),)).copy()
            return r
        m.step = wrapped
    worst = {"min": (np.inf, None), "max": (-np.inf, None)}
    for k in range(int(round(seconds * 1000))):
        parts.clear()
        o = b.step(None, 1.0)
        v = np.asarray(o.v_mV, float)
        i, j = int(np.nanargmin(v)), int(np.nanargmax(v))
        for key, idx, better in (("min", i, v[i] < worst["min"][0]), ("max", j, v[j] > worst["max"][0])):
            if better:
                worst[key] = (float(v[idx]), dict(t_ms=k + 1, cell=b.cell_names[idx] if idx < len(b.cell_names)
                                                  else idx, currents_pA={n: round(float(a[idx]), 2)
                                                                         for n, a in parts.items() if a[idx]}))
    tv = joint._template_values(led)
    moved = []
    for pid, x in spec.values.items():
        t = tv.get(pid)
        try:
            a, c = np.asarray(x, float).ravel(), np.asarray(t, float).ravel()
        except (TypeError, ValueError):
            continue
        if a.shape == c.shape and a.size and (c != 0).all():
            r = np.abs(np.log(np.abs(a / c) + 1e-300)).max()
            if np.isfinite(r) and r > 0:
                moved.append((round(float(r), 2), pid))
    return dict(seed=s, used_seed=spec.seed, v_min=worst["min"], v_max=worst["max"],
                most_moved=sorted(moved, reverse=True)[:25])


def mode_run(n, seconds):
    import subprocess
    worms = []
    for s in range(1, n + 1):
        r = subprocess.run([sys.executable, __file__, "one", str(s), str(seconds)], capture_output=True, text=True)
        if r.returncode:
            w = dict(seed=s, ok=False, fail={"crash": 1}, stderr=r.stderr[-2000:], rejected=[])
        else:
            w = json.loads(r.stdout.strip().splitlines()[-1])
        worms.append(w)
        print(json.dumps({k: w.get(k) for k in ("seed", "used_seed", "wall_s", "v_min", "v_max", "ok", "fail")}
                         | dict(n_rejected=len(w["rejected"]))), flush=True)
    vlo, vhi = envelope(ledger.load(MODEL))
    return dict(mode="run", seconds=seconds, envelope_mV=[vlo, vhi], worms=worms,
                passed=sum(w["ok"] for w in worms), draws_rejected=sum(len(w["rejected"]) for w in worms))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "one":
        tg = dict(a.split("=", 1) for a in sys.argv[4:])
        print(json.dumps(one(int(sys.argv[2]), float(sys.argv[3]), tg or None), default=float))
        sys.exit()
    if mode == "diag":
        print(json.dumps(diag(int(sys.argv[2]), float(sys.argv[3])), default=float))
        sys.exit()
    res = mode_joint(int(sys.argv[2])) if mode == "joint" else mode_run(int(sys.argv[2]), float(sys.argv[3]))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"sample_{mode}.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "worms"}, default=float))
