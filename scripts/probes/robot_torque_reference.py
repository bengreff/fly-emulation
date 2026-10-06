"""Session 12 (F-FLIGHT-3 diagnostic, after the 22:15 result): compare the model's force
and torque within the beat with the robotic fly's time-resolved record (Muijres 2014
Database S1 robotForcesTorques, `*_norm_all_butterfilt`, the authors' filtered series),
and ask which reference point and scale would carry the model's torque onto the robot's.

The model's torques are about the hinge midpoint (hover_blade_trace `*_series.npz`,
robot frame, m g l units). If the robot's are about a point P, then
M_robot(t) = s M_hinge(t) + d x F(t), with d the hinge midpoint relative to P over l.
Fitted per set by least squares on the robot's own forces (F_robot) and the model's
hinge torque: pitch My = s My_h + dz Fx - dx Fz; roll Mx = s Mx_h + dy Fz - dz Fy.
s is free (sign included) or fixed at +-1. A fitted d is a diagnostic about the robot's
data reduction (inferred), never a model quantity.

    uv run python scripts/probes/robot_torque_reference.py --dir runs/s12/flight/series
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import scipy.io as sio

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DB = REPO / "data/raw/flight_kinematics/muijres2014/FRUITFLY_LOOMINGRESPONSE_DATABASE.mat"
AX = ("Fx", "Fy", "Fz", "Mx", "My", "Mz")


def robot_series(kind: str, k: int, suffix: str = "_butterfilt") -> tuple[np.ndarray, dict]:
    rft = sio.loadmat(DB, squeeze_me=True, struct_as_record=False)["robotForcesTorques"]
    s = rft.PitchModulations if kind == "pitch" else rft.RollModulations
    t = np.asarray(s.t, float)
    T = t[-1] + (t[1] - t[0])
    return t / T, {c: np.asarray(getattr(s, f"{c}_norm_all{suffix}"), float)[:, k] for c in AX}


def model_series(path: Path, ph: np.ndarray) -> dict:
    z = np.load(path)
    o = np.argsort(z["phase"])
    p, v = z["phase"][o], z["robot_frame_norm"][o]
    return {c: np.interp(ph, p, v[:, i], period=1.0) for i, c in enumerate(AX)}


def fit(kind: str, rob: dict, mod: dict, s_fixed: float | None) -> dict:
    if kind == "pitch":          # My = s My_h + dz Fx - dx Fz
        y, mh, cols, names = rob["My"], mod["My"], [rob["Fx"], -rob["Fz"]], ("dz", "dx")
    else:                        # Mx = s Mx_h + dy Fz - dz Fy
        y, mh, cols, names = rob["Mx"], mod["Mx"], [rob["Fz"], -rob["Fy"]], ("dy", "dz")
    ok = np.isfinite(y) & np.all(np.isfinite(cols), 0)
    if s_fixed is None:
        A = np.column_stack([mh] + cols)[ok]
        c, *_ = np.linalg.lstsq(A, y[ok], rcond=None)
        s, d = c[0], c[1:]
    else:
        A = np.column_stack(cols)[ok]
        d, *_ = np.linalg.lstsq(A, (y - s_fixed * mh)[ok], rcond=None)
        s = s_fixed
    pred = s * mh + d[0] * cols[0] + d[1] * cols[1]
    r2 = 1 - np.nansum((y - pred)[ok] ** 2) / np.nansum((y[ok] - y[ok].mean()) ** 2)
    return {"s": round(float(s), 3), **{n: round(float(v), 3) for n, v in zip(names, d)}, "r2": round(float(r2), 3),
            "mean_pred": round(float(np.nanmean(pred)), 4), "mean_robot": round(float(np.nanmean(y)), 4)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(REPO / "runs/s12/flight/series"))
    ap.add_argument("--cases", default="pitch:10,pitch:0,pitch:20,roll:2,roll:12")
    ap.add_argument("--plot", default=str(REPO / "docs/media/s12_robot_torque_series.png"))
    ap.add_argument("--raw", action="store_true", help="the robot's unfiltered series instead of *_butterfilt")
    a = ap.parse_args()
    d = Path(a.dir)
    out, series = {}, {}
    for case in a.cases.split(","):
        kind, k = case.split(":"); k = int(k)
        ph, rob = robot_series(kind, k, "" if a.raw else "_butterfilt")
        tag = f"_pitch{k}" if kind == "pitch" else f"_roll{k}_all"
        mod = model_series(d / f"hover_blade_trace{tag}_series.npz", ph)
        corr = {c: round(float(np.corrcoef(rob[c][np.isfinite(rob[c])], mod[c][np.isfinite(rob[c])])[0, 1]), 3) for c in AX}
        rms = {c: round(float(np.sqrt(np.nanmean(mod[c] ** 2) / np.nanmean(rob[c] ** 2))), 3) for c in AX}
        out[case] = {"corr_model_robot": corr, "rms_model_over_robot": rms,
                     "fit_free_s": fit(kind, rob, mod, None), "fit_s_plus1": fit(kind, rob, mod, 1.0),
                     "fit_s_minus1": fit(kind, rob, mod, -1.0)}
        series[case] = (ph, rob, mod)
        print(case, json.dumps(out[case]))
    Path(a.dir, f"robot_torque_reference{'_raw' if a.raw else ''}.json").write_text(json.dumps(out, indent=1))
    cases = list(series)
    fig, axs = plt.subplots(len(cases), 4, figsize=(15, 2.6 * len(cases)), sharex=True)
    for i, case in enumerate(cases):
        ph, rob, mod = series[case]
        for j, c in enumerate(("Fx", "Fz", "Mx" if case.startswith("roll") else "My", "Mz")):
            ax = axs[i, j]
            ax.plot(ph, rob[c], "k", lw=1, label=f"robot ({'unfiltered' if a.raw else 'filtered'})")
            ax.plot(ph, mod[c], "C3--", lw=1, label="model, about hinge midpoint")
            ax.set_title(f"{case} {c}  r={out[case]['corr_model_robot'][c]}", fontsize=8)
            if j == 0:
                ax.legend(fontsize=6)
    for ax in axs[-1]:
        ax.set_xlabel("wingbeat phase (t/T)")
    fig.suptitle("Model (blade element + added mass) vs robotic fly within the beat, robot frame, m g l units", fontsize=10)
    fig.tight_layout(); fig.savefig(a.plot, dpi=100)


if __name__ == "__main__":
    main()
