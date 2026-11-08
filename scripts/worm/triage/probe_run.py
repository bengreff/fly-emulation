"""Run an unchanged unit-check script at the ledger values with some gap values overridden, one fresh forked process
per point (wtriage, 8 Nov 2026). Nothing is written outside runs/worm/triage.

    from probe_run import run_points
    rows = run_points("scripts/worm/organs/check_other.py", ids, X, workers=8, args=[])   # list of the checks' JSON

Each point: at_ledger.patch() (every mech module's Spec templates set to the ledger value), then the point's ids set
as Spec templates (dataclasses.replace), then the script runs as __main__ with argv [script, OUT.json, *args].
"""
from __future__ import annotations

import dataclasses
import importlib
import json
import multiprocessing as mp
import os
import runpy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))


def override(values: dict) -> list[str]:
    """Set these ids as Spec templates in every registry module (and brain_layers, body layers)."""
    from wormemu import brain_layers, mech
    from wormemu.body import layers
    mods = [importlib.import_module(f"wormemu.mech.{n}") for n in mech.REGISTRY] + [brain_layers, layers]
    done = []
    for m in mods:
        specs = getattr(m, "SPECS", None)
        for i, s in enumerate(specs or []):
            if s.id in values:
                specs[i] = dataclasses.replace(s, template=float(values[s.id]))
                done.append(s.id)
    missing = set(values) - set(done)
    assert not missing, f"no Spec for {missing}"
    # the brain reads spec.values (the ledger) before the template (mech.params_for): set them there too
    from wormemu import brain as B
    if not getattr(B.sample_worm, "_wtriage", False):
        orig = B.sample_worm

        def sw(*a, **k):
            s = orig(*a, **k)
            s.values = dict(s.values)
            s.values.update({i: float(x) for i, x in _OVER.items()})
            return s
        sw._wtriage = True
        B.sample_worm = sw
    _OVER.clear()
    _OVER.update(values)
    return done


_OVER = {}


def _child(script, values, args, out, q):
    try:
        import at_ledger
        at_ledger.patch()
        override(values)
        sys.argv = [script, out, *args]
        with open(os.devnull, "w") as dn:
            so = sys.stdout
            sys.stdout = dn
            try:
                runpy.run_path(script, run_name="__main__")
            finally:
                sys.stdout = so
        q.put(json.loads(Path(out).read_text()))
    except BaseException as e:            # a check that crashes or asserts is a non-pass, recorded
        q.put({"error": f"{type(e).__name__}: {e}"[:300]})


def run_one(script, values, args=(), timeout=1800):
    ctx = mp.get_context("fork")
    q = ctx.Queue()
    with tempfile.TemporaryDirectory() as d:
        out = str(Path(d) / "out.json")
        p = ctx.Process(target=_child, args=(script, values, list(args), out, q))
        p.start()
        try:
            r = q.get(timeout=timeout)
        except Exception as e:
            r = {"error": f"timeout or no result: {e}"}
        p.join(5)
        if p.is_alive():
            p.kill()
    return r


def _direct(a):
    """In a fresh pool worker (maxtasksperchild=1, forked from an unpatched parent): patch, run, return the JSON."""
    script, values, args, _ = a

    class Q:
        def put(self, x):
            self.x = x
    q = Q()
    with tempfile.TemporaryDirectory() as d:
        _child(script, values, list(args), str(Path(d) / "out.json"), q)
    r = q.x
    r["_point"] = values
    return r


def run_points(script, ids, X, workers=8, args=(), timeout=1800):
    script = str(ROOT / script) if not os.path.isabs(script) else script
    jobs = [(script, dict(zip(ids, map(float, x))), tuple(args), timeout) for x in X]
    with mp.get_context("fork").Pool(workers, maxtasksperchild=1) as pool:
        return pool.map(_direct, jobs, chunksize=1)
