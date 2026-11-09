"""The EKI battery forward end to end, on the template (weki, 9 Nov 2026; fit/vector.py). NO FIT.

Runs vector.battery_forward on the template's own z (its numbers through the z round trip and the --theta=FILE dict
path, each condition in its own process) and the plain battery (`vitals run`, no theta) at the same length, then
compares the observations. Pass: every observation equal within 1e-6 relative, or both NaN, and both physical. The z
round trip moves numbers by about 1e-12 relative (tests/test_worm_fit_vector.py), so a larger gap means the dict
path builds a different worm.

Usage: python scripts/worm/fit/forward_smoke.py SECONDS OUTDIR
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.fit import vector as VC  # noqa: E402
from wormemu.fit import vitals  # noqa: E402

secs, out = float(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
v = VC.Vector()
names, y, sig = VC.targets()
t0 = time.time()
g, ok = VC.battery_forward(v.z(v.base), 0, None, seconds=secs, workdir=str(out))
w_fwd = time.time() - t0
t0 = time.time()
res = {}
for c in VC.CONDS:
    subprocess.run([sys.executable, "-m", "wormemu.fit.vitals", "run", c, str(secs), str(out / "plain")], check=True,
                   capture_output=True)
    res[c] = json.loads((out / "plain" / f"{c}.json").read_text())
w_plain = time.time() - t0
_, g0, _, _ = vitals.observations(res, ids=VC.BATTERY_IDS)
ok0 = all(r["physicality"]["physical"] for r in res.values())
same = [(np.isnan(a) and np.isnan(b)) or abs(a - b) <= 1e-6 * max(1.0, abs(b)) for a, b in zip(g, g0)]
rep = {"seconds": secs, "names": names, "forward": g.tolist(), "plain": g0.tolist(), "ok_forward": ok, "ok_plain": ok0,
       "same": same, "passed": bool(all(same) and ok and ok0), "wall_forward_s": w_fwd, "wall_plain_s": w_plain}
(out / "forward_smoke.json").write_text(json.dumps(rep, indent=1, default=float))
for n, a, b, s in zip(names, g, g0, same):
    print(f"{n:24s} forward {a:10.4f}  plain {b:10.4f}  {'same' if s else 'DIFF'}")
print("passed", rep["passed"], "ok", ok, ok0, "wall", round(w_fwd), round(w_plain), "s")
