"""Resting rate of one unconnected central model cell against membrane noise and tonic drive (diagnostic).

Built for the route bracket (DECISIONS 6 October 00:05): without noise a model cell cannot rest at the
0.1-4 Hz measured in central neurons except on a 0.05 mV knife-edge (route_rest.py). This sweeps the
voltage noise (mV per sqrt(ms), the model's `background_noise` units) and a constant drive (mV) for a
generic central cell under m9c (tau_m 20 ms, rest -52 mV, gap 7 mV, t_ref 2.2 ms, class-prior channels),
10 s per point, and prints the rate and the membrane SD.

    uv run python scripts/probes/noise_rest.py > runs/s12/rest/noise_rest_m9c.txt
"""
import sys, numpy as np
from pathlib import Path
HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "src")); sys.path.insert(0, str(HERE.parent))
from flyemu import channels, lif, profiles
from flyemu.registry import Policy, Registry
from central_fi import fake_conn
DT = 0.1
reg = Registry(Policy.MINIMAL); profiles.apply(reg, "m9c")
sig = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5]; drv = [0.0, 2.0, 4.0, 5.0, 6.0, 7.0]
grid = [(s, d) for s in sig for d in drv]; n = len(grid)
conn = fake_conn(n); ich = channels.from_registry(reg, conn, timestep_ms=DT)
f = lambda v: np.full(n, v, np.float32)
res = {}
for s in sig:
    m = np.array([g[0] == s for g in grid])
    p = lif.LIFParams(f(20.0), f(-52.0), f(-45.0), f(-52.0), f(2.2), 5.0, np.ones(n, np.int64), float(s), True,
                      graded=np.zeros(n, bool), intrinsic=ich)
    net = lif.Network(conn, p, DT, rng=np.random.default_rng(1))
    ext = np.array([g[1] for g in grid], np.float32); cnt = np.zeros(n); vs = []
    for k in range(int(10500 / DT)):
        sp = net.step(external_mv=ext)
        if k * DT >= 500:
            if sp.size: cnt[sp] += 1
            if k % 10 == 0: vs.append(net.v.copy())
    sd = np.std(np.array(vs), axis=0)
    for j in np.flatnonzero(m):
        res[grid[j]] = (cnt[j] / 10.0, sd[j])
print("noise sigma (mV/sqrt ms) x drive (mV): rate Hz [membrane SD mV]")
print("sigma \\ drive " + "".join(f"{d:>14g}" for d in drv))
for s in sig:
    print(f"{s:>12g} " + "".join(f"{res[(s,d)][0]:>8.2f} [{res[(s,d)][1]:.1f}]" for d in drv))
