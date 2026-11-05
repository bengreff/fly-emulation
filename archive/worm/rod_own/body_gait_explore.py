"""POST-HOC exploration after the v1 gait test (BODY_TESTS.md): how the guessed moment-radius exponent and the
water head-curvature target move speed and the curvature profile. Not a test; nothing here is a pass.

    PYTHONPATH=src python scripts/worm/body_gait_explore.py
"""
import json
from pathlib import Path

from wormemu.body import Body, BodyConfig, BodyLedger
from wormemu.body.gait import calibrate_a0

OUT = Path(__file__).resolve().parents[2] / "data/worm/body_runs/gait_explore_posthoc.json"


def main():
    base = BodyLedger.load()
    rows = []
    for p in (2.0, 3.0, 4.0):
        led = base.override(wb6_moment_radius_exponent=p)
        for gait, targets in (("crawl", (8.5,)), ("swim", (4.5, 6.07))):
            for tgt in targets:
                a0, o = calibrate_a0(lambda m: Body(led, BodyConfig(medium=m)), gait, target=tgt)
                prof = o["amp_profile_per_mm"]
                r = {"moment_exp": p, "gait": gait, "head_target": tgt, "a0": a0,
                     "speed_mm_s": o["speed_mm_s"], "wavelength_L": o["wavelength_L"],
                     "tail_head": o["tail_head_ratio"], "tip_amp": float(prof[0]),
                     "mid_amp": float(prof[len(prof) // 2])}
                rows.append(r)
                print({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}, flush=True)
    OUT.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
