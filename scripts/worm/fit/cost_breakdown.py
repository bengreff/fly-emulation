"""Where the battery's wall time goes (FIT_GENERAL section 10's cost table): one short food run under cProfile.

Usage: cost_breakdown.py SECONDS OUTDIR

Runs the battery's food condition (vitals.experiment, body on) for SECONDS bio-s and prints the wall per bio-s and
the cumulative time in: the brain's exchange step (Brain.step), NEURON's integration inside it (fadvance /
h.continuerun / psolve, whichever the brain calls), waiting on the body driver's pipe (Body.recv; the body steps in
its own process while the brain steps, so this is only the part not hidden behind the brain), and the rest.
The battery's own wall_per_bio_s also counts Brain construction and the readouts; this splits the loop only.
"""
import cProfile, io, os, pstats, sys, time
from pathlib import Path

from wormemu import datamodel
from wormemu.fit import vitals

seconds, outdir = float(sys.argv[1]), Path(sys.argv[2])
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "food_body").mkdir(exist_ok=True)
ex = vitals.experiment("food", seconds, body_out=str(outdir / "food_body"))
theta = vitals.battery_theta({})
pr = cProfile.Profile()
t0 = time.time()
pr.enable()
res = datamodel.simulate(theta, ex)
pr.disable()
wall = time.time() - t0
bio = float(res["t_ms"][-1]) / 1000.0
st = pstats.Stats(pr)
cum = {}
for (f, line, fn), (cc, nc, tt, ct, callers) in st.stats.items():
    cum.setdefault(fn, [0.0, 0.0, 0])
    cum[fn][0] += ct
    cum[fn][1] += tt
    cum[fn][2] += nc
print(f"bio_s {bio:.3f}  wall {wall:.1f} s  wall per bio-s {wall / bio:.2f}")
for fn in ("simulate", "run", "step", "recv", "_read", "fadvance", "continuerun", "psolve", "send", "__init__"):
    if fn in cum:
        c, t, n = cum[fn]
        print(f"  {fn:12s} cumulative {c:8.1f} s  own {t:8.1f} s  calls {n}")
s = io.StringIO()
pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(30)
print(s.getvalue()[:6000])
s = io.StringIO()
pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(40)
print(s.getvalue()[:8000])
