"""Session 12 (F-FLIGHT-3): score hover_blade_trace outputs against the robotic fly of
Muijres et al. 2014 (Database S1 robotForcesTorques) for the roll and pitch sets.

Model torques in the trace files are about the hinge midpoint, robot frame (x forward,
y right, z down), normalized by m g l. "cg" moves them to the centre of mass of the
Database S1 body model: the hinge midpoint sits at R_strk @ mean(Joint_left,
Joint_right) = (0.087, 0, -0.783) mm from it (derived), so M_cg = M + r/l x F.
Which point the robot's torques are about is not stated in open sources (inferred).

Force correction (as registered, DECISIONS s12 20:43): model torque x (robot steady
vertical force / model steady vertical force).

    uv run python scripts/probes/score_robot_sets.py --set roll --dir runs/s12/flight/planform
    uv run python scripts/probes/score_robot_sets.py --set pitch --dir runs/s12/flight/am --prefix _pitch_am
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_measured_kinematics import DB, robot_pitch, robot_roll  # noqa: E402

AX = ("Fx", "Fy", "Fz", "Mx", "My", "Mz")


def cg_offset_over_l() -> np.ndarray:
    d = sio.loadmat(DB, squeeze_me=True, struct_as_record=False)
    bm = d["body_model"]
    j = 0.5 * (np.asarray(bm.Joint_left, float) + np.asarray(bm.Joint_right, float))
    return np.asarray(bm.R_strk, float) @ j / float(d["wing_model"].length)


def to_cg(v: dict, r: np.ndarray) -> dict:
    F, M = np.array([v[k] for k in AX[:3]]), np.array([v[k] for k in AX[3:]])
    Mc = M + np.cross(r, F)
    return {**{k: v[k] for k in AX[:3]}, **dict(zip(AX[3:], Mc.tolist()))}


def load(dirpath: Path, tag: str) -> dict:
    return json.loads((dirpath / f"hover_blade_trace{tag}.json").read_text())["robot_frame_norm"]


def score(kind: str, dirpath: Path, prefix: str, thr: float = 0.03, tol: float = 0.2) -> dict:
    r = cg_offset_over_l()
    if kind == "roll":
        levels, steady, comp = range(13), 2, "Mx"
        tag = lambda k: f"{prefix or '_roll'}{k}_all"            # noqa: E731
        ref = lambda k: robot_roll(k, "all")[3]                  # noqa: E731
    else:
        levels, steady, comp = range(21), 10, "My"
        tag = lambda k: f"{prefix or '_pitch'}{k}"               # noqa: E731
        ref = lambda k: robot_pitch(k)[3]                        # noqa: E731
    mod = {k: load(dirpath, tag(k)) for k in levels}
    rob = {k: ref(k) for k in levels}
    corr = rob[steady]["Fz"] / mod[steady]["Fz"]
    rows = []
    for k in levels:
        m_h, m_c, rb = mod[k], to_cg(mod[k], r), rob[k]
        row = {"level": k, "robot": round(rb[comp], 4), "robot_Fx": round(rb["Fx"], 4), "robot_Fz": round(rb["Fz"], 4),
               "model_hinge": round(m_h[comp] * corr, 4), "model_cg": round(m_c[comp] * corr, 4),
               "model_Fx": round(m_h["Fx"] * corr, 4), "model_Fz": round(m_h["Fz"] * corr, 4)}
        if kind == "pitch":            # change from the steady beat (the absolute level depends on the reference point)
            row["d_robot"] = round(rb[comp] - rob[steady][comp], 4)
            row["d_model_hinge"] = round((m_h[comp] - mod[steady][comp]) * corr, 4)
            row["d_model_cg"] = round((m_c[comp] - to_cg(mod[steady], r)[comp]) * corr, 4)
        rows.append(row)
    key_r, keys_m = ("robot", ("model_hinge", "model_cg")) if kind == "roll" else ("d_robot", ("d_model_hinge", "d_model_cg"))
    out = {"set": kind, "dir": str(dirpath), "prefix": prefix, "component": comp, "steady_level": steady,
           "force_correction": round(corr, 4), "threshold": thr, "tolerance": tol, "rows": rows}
    for km in keys_m:
        q = [(x["level"], x[km] / x[key_r]) for x in rows if abs(x[key_r]) >= thr]
        ratios = [v for _, v in q]
        mags = [abs(v) for v in ratios]
        signs = {int(np.sign(v)) for v in ratios}
        out[km] = {"qualifying_levels": [lv for lv, _ in q],
                   "ratio": [round(v, 3) for v in ratios],
                   "abs_ratio_range": [round(min(mags), 3), round(max(mags), 3)] if mags else None,
                   "median_abs_log_ratio": round(float(np.median(np.abs(np.log(mags)))), 3) if mags else None,
                   "all_within_tol": bool(mags) and all(abs(v - 1) <= tol for v in mags),
                   "sign": "same" if signs == {1} else "opposite" if signs == {-1} else "mixed"}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=("roll", "pitch"), required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--prefix", default="", help="trace tag before the level number (default _roll / _pitch)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    res = score(a.set, Path(a.dir), a.prefix)
    for km in ("model_hinge", "model_cg", "d_model_hinge", "d_model_cg"):
        if km in res:
            print(km, json.dumps(res[km]))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
