"""Everything-on closed loop with worker B2's mechanisms registered (night of 6 Nov 2026, worgans).

Adds B2's modules (WORGANS below, in order) to wormemu.mech.REGISTRY for this process (until the Director adds them
to the registry itself), then runs scripts/worm/brain_loop_check.py's loop: the template worm, the code's default
toggles, the published body (AGAR_FILM, diacetyl cone). It checks that each mechanism runs inside the whole model
(finite, bounded) and records its outputs; it scores nothing against behaviour.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/organs/organs_loop_check.py SECONDS LABEL ['{"toggle": "value"}']
Output: runs/worm/night_wbrain/LABEL.json (brain_loop_check's place for it)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))

from wormemu import mech  # noqa: E402

WORGANS = ["muscle_bwm"]
for m in WORGANS:
    if m not in mech.REGISTRY:
        mech.REGISTRY.append(m)

import brain_loop_check  # noqa: E402

if __name__ == "__main__":
    brain_loop_check.main()
