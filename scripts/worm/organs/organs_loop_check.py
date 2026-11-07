"""Everything-on closed loop with worker B2's mechanisms registered (night of 6 Nov 2026, worgans).

Adds B2's modules (WORGANS below, in order) to wormemu.mech.REGISTRY for this process (until the Director adds them
to the registry itself), then runs scripts/worm/brain_loop_check.py's loop: the template worm, the code's default
toggles, the published body (AGAR_FILM, diacetyl cone). It checks that each mechanism runs inside the whole model
(finite, bounded) and records its outputs; it scores nothing against behaviour.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/organs/organs_loop_check.py SECONDS LABEL ['{"toggle": "value"}']
Output: runs/worm/night_wbrain/LABEL.json (brain_loop_check's place for it), and LABEL.organs.npz: every step's
scalar mechanism outputs and the arrays of up to 40 values (e.g. the 20 pharyngeal muscles' V), keyed by name, with t.
"""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))

from wormemu import mech  # noqa: E402

WORGANS = ["muscle_bwm", "organs_pharynx", "organs_intestine", "organs_egglaying", "glia", "organs_other", "pumps",
           "metabolism"]
for m in WORGANS:
    if m not in mech.REGISTRY:
        mech.REGISTRY.append(m)

import brain_loop_check  # noqa: E402


class OrganRecorder(brain_loop_check.Recorder):
    """brain_loop_check's recorder, also keeping every step's small mechanism outputs."""
    last = None

    def __init__(self, brain):
        super().__init__(brain)
        self.trace = defaultdict(list)
        OrganRecorder.last = self

    def step(self, obs, dt_ms):
        o = super().step(obs, dt_ms)
        self.trace["t"].append(self.b.t)
        for k, x in self.b.mech_out.items():
            if isinstance(x, dict):                              # dicts of scalars (deb, afd_gc_scale, ...): k.kk
                for kk, xx in x.items():
                    if np.isscalar(xx):
                        self.trace[f"{k}.{kk}"].append(np.float32(xx))
                continue
            a = np.asarray(x, float)
            if a.size <= 40:
                self.trace[k].append(a.astype(np.float32))
        return o


if __name__ == "__main__":
    brain_loop_check.Recorder = OrganRecorder
    brain_loop_check.main()
    r = OrganRecorder.last
    n = len(r.trace["t"])
    out = ROOT / "runs" / "worm" / "night_wbrain" / f"{sys.argv[2]}.organs.npz"
    np.savez_compressed(out, **{k: np.stack(v) for k, v in r.trace.items() if len(v) == n})
    print("organ trace:", out, sorted(k for k, v in r.trace.items() if len(v) == n))
