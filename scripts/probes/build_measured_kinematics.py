"""Session 12 B (F-FLIGHT-3, pre-registered test DECISIONS s12 19:08): turn the
measured steady-flight wing kinematics of Muijres et al. 2014 (Science 344:172,
Table S1 Fourier fits, D. hydei; data/derived/muijres2014_hover_kinematics.csv)
into model hinge angles per phase, for hover_blade_trace.py --table.

Conventions (inferred; DECISIONS s12 19:08, "Kinematics fixed before the run"):
stroke plane tilted 47.5 deg nose-up from the body axis; phi positive = posterior;
deviation positive toward the stroke-plane normal; alpha = 0 with the chord normal
to the stroke plane (leading edge up), positive = leading edge toward anterior.
Thorax frame: x head, y left, z up. Span and leading-edge vectors are built in the
thorax frame and fitted with flight.wing_pose_ik (bounded by the joint ranges).

    uv run python scripts/probes/build_measured_kinematics.py [--f-hz 218] [--out runs/s12/flight/muijres2014_hover.npz]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import flight  # noqa: E402
from flyemu.body import Body  # noqa: E402

SRC = REPO / "data/derived/muijres2014_hover_kinematics.csv"     # copy of data/raw/flight_kinematics/hover_kinematics_muijres2014.csv


open_wing_ranges = flight.open_wing_ranges


def wing_vectors(phi, dev, alpha, side: str, tilt_deg: float = flight.STROKE_PLANE_DEG):
    """Unit span and leading-edge vectors (thorax frame) for one wing pose (deg)."""
    return flight.stroke_frame_vectors(phi, dev, alpha, side, tilt_deg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--f-hz", type=float, default=218.0, help="Fry et al. 2005 D. melanogaster free flight (measured)")
    ap.add_argument("--body-pitch", type=float, default=47.6, help="Muijres 2014 steady flight (measured)")
    ap.add_argument("--out", default=str(REPO / "runs/s12/flight/muijres2014_hover.npz"))
    a = ap.parse_args()
    import pandas as pd
    t = pd.read_csv(SRC, comment="#")
    ph, phi, dev, rot = (t[c].to_numpy(float) for c in ("phase", "stroke_deg", "deviation_deg", "rotation_deg"))
    if ph[-1] >= 1.0:
        ph, phi, dev, rot = ph[:-1], phi[:-1], dev[:-1], rot[:-1]
    body = Body(vision=False)
    open_wing_ranges(body)          # WING_RANGE_DEG holds a crossed-wing stroke (F-WING-3); fit unbounded
    res, errs = {}, {}
    for side in ("l", "r"):
        qs, es, q0 = [], [], None
        for i in range(len(ph)):
            s, le = wing_vectors(phi[i], dev[i], rot[i], side)
            q, e = flight.wing_pose_ik(body, side, s, le, q_start=q0)
            qs.append(q); es.append(e); q0 = q
        res[side], errs[side] = np.array(qs), np.array(es)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, phase=ph, q_l=res["l"], q_r=res["r"], f_hz=a.f_hz, body_pitch_deg=a.body_pitch,
             err_l_deg=errs["l"], err_r_deg=errs["r"])
    summ = {"out": str(out), "n": int(len(ph)), "f_hz": a.f_hz, "body_pitch_deg": a.body_pitch,
            "max_pose_err_deg": {k: round(float(v.max()), 2) for k, v in errs.items()},
            "hinge_range_deg": {k: {fn: [round(float(np.degrees(v[:, i]).min()), 1), round(float(np.degrees(v[:, i]).max()), 1)]
                                    for i, fn in enumerate(("stroke", "deviation", "rotation"))} for k, v in res.items()}}
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
