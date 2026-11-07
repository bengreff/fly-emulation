"""Everything-on closed-loop check for the brain-signalling mechanisms (night of 6 Nov 2026, wbrain).

Runs the template worm (sample_worm(None), the code's default toggles unless overridden) closed loop on the published
body (AGAR_FILM, diacetyl cone) for N seconds and writes one JSON summary: wall time per biological second, NaN or
blow-up, neurons above -20 mV, and each registered mechanism's outputs at the end. It checks that a mechanism runs
inside the whole model; it scores nothing against behaviour.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/brain_loop_check.py SECONDS LABEL ['{"toggle": "value"}']
Output: runs/worm/night_wbrain/LABEL.json (and the body's files next to it)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wormemu.brain import Brain, sample_worm  # noqa: E402
from wormemu.body.loop import Body, run  # noqa: E402
from wormemu.body.metaworm import AGAR_FILM  # noqa: E402
from wormemu.body.scene import ChemotaxisScene  # noqa: E402


def _summ(x):
    if isinstance(x, dict):
        return {k: _summ(v) for k, v in list(x.items())[:40]}
    a = np.asarray(x, float)
    if a.size == 1:
        return float(a)
    return dict(n=int(a.size), mean=float(np.nanmean(a)), min=float(np.nanmin(a)), max=float(np.nanmax(a)))


class Recorder:
    """The brain, with per-step statistics on the side."""

    def __init__(self, brain):
        self.b, self.cell_names = brain, brain.cell_names
        self.neur = ~brain.is_muscle
        self.k, self.above, self.vmax, self.finite, self.mo = 0, [], -1e9, True, []

    def reset(self):
        return self.b.reset()

    def step(self, obs, dt_ms):
        o = self.b.step(obs, dt_ms)
        v = o.v_mV
        self.finite &= bool(np.isfinite(v).all())
        self.vmax = max(self.vmax, float(np.nanmax(np.abs(v))))
        self.k += 1
        if self.k % 20 == 0:
            self.above.append((self.b.t, int((v[self.neur] > -20).sum())))
        if self.k % 500 == 0:
            self.mo.append((self.b.t, _summ(self.b.mech_out)))
        return o


def main():
    seconds, label = float(sys.argv[1]), sys.argv[2]
    tog = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    out = ROOT / "runs" / "worm" / "night_wbrain" / label
    out.parent.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    t0 = time.time()
    brain = Brain(sample_worm(None), toggles=tog)
    build_s = time.time() - t0
    rec = Recorder(brain)
    body = Body(out, scene=ChemotaxisScene(field="cone_published"), frame_every=8, world=AGAR_FILM)
    meta = run(rec, body, seconds, brain_config={"seed": None, "toggles": dict(brain.toggles), "commit": commit},
               log_every_s=max(1.0, seconds / 5))
    ab = np.array(rec.above, float)
    last = ab[ab[:, 0] >= ab[-1, 0] - 2000.0, 1] if len(ab) else np.array([np.nan])
    res = dict(label=label, commit=commit, seconds=seconds, build_s=round(build_s, 1),
               loop_wall_s=round(meta["loop_wall_s"], 1), wall_per_bio_s=round(meta["loop_wall_s"] / seconds, 2),
               finite=rec.finite, max_abs_v_mV=round(rec.vmax, 1), max_activation=meta["max_activation"],
               neurons_above_m20_last2s=float(np.mean(last)), mechs=[type(m).__module__ for m in brain.mechs],
               toggles_on=sorted(k for k, v in brain.toggles.items() if v not in ("off", "none", False)),
               toggles_off=sorted(k for k, v in brain.toggles.items() if v in ("off", "none", False)),
               mech_out_trace=rec.mo[-3:], mech_out_end=_summ(brain.mech_out))
    (out.parent / f"{label}.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: res[k] for k in ("label", "wall_per_bio_s", "finite", "max_abs_v_mV",
                                          "neurons_above_m20_last2s", "max_activation", "mechs")}, default=float))


if __name__ == "__main__":
    main()
