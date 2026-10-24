"""s23 stage m10f6 unit check (DECISIONS 23 Oct 22:58): the N26 clock read through the stage's registry entrains to
12:12 LD. 3 days at 1000 lux from the default start state; the model CT at the last lights-on must be CT 0 +- 2 h.
Reported, not scored: the same after a 6 h phase jump (start at CT 6), day by day.

    PYTHONPATH=src .venv/bin/python scripts/probes/s23_n26_ld_check.py --profile m10f6 --out runs/s23/n26_ld.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import profiles  # noqa: E402
from flyemu.internal_state import Organs, read_params  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402


def wrap(x: float) -> float:
    return (x + 12.0) % 24.0 - 12.0


def ld_days(p: dict, ct0: float, days: int, lux: float = 1000.0) -> list[float]:
    """CT at each lights-on, starting at lights-on with the clock at ct0 (start state from Organs' default rule)."""
    o = Organs(p=p, z=complex(np.exp(1j * 2 * np.pi * ct0 / 24.0)))
    out = [float(o.ct_h)]
    for _ in range(days):
        for _ in range(12):
            o.step(3600.0, light_lux=lux)
        for _ in range(12):
            o.step(3600.0, light_lux=0.0)
        out.append(float(o.ct_h))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f6")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, a.profile)
    p = read_params(reg)
    keys = ("light_input", "k_tim", "ct_tim_h", "cry_rate_per_lux_h", "tim_kdeg_per_h", "period_h")
    scored = ld_days(p, 0.0, 3)
    jump = ld_days(p, 6.0, 10)
    res = {"profile": a.profile, "params": {k: p.get(k) for k in keys},
           "registered": {"ct_at_lights_on_by_day": scored, "last": wrap(scored[-1]),
                          "pass": abs(wrap(scored[-1])) <= 2.0},
           "reported_jump_ct6": {"ct_at_lights_on_by_day": [wrap(c) for c in jump]}}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
