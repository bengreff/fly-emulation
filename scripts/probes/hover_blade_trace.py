"""Session 12 B (F-FLIGHT-3): one tethered hover run with the blade-element wing
(aero:wing|model 1) at exact imposed kinematics; traces the left wing's angle of
attack at 70% span and the vertical lift, drag and rotational forces over the
last wingbeats, against stroke phase.

    uv run python scripts/probes/hover_blade_trace.py [--rot-amp 55] [--out runs/s12/flight]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import mujoco as mj
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import flight  # noqa: E402
from flyemu.body import Body  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rot-amp", type=float, default=55.0)
    ap.add_argument("--rot-mean", type=float, default=None)
    ap.add_argument("--beats", type=int, default=6)
    ap.add_argument("--dt-ms", type=float, default=0.05)
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "flight"))
    a = ap.parse_args()
    b = Body(vision=False, timestep=a.dt_ms / 1000.0, spawn_height=5.0)
    m, d = b.sim.mj_model, b.sim.mj_data
    flight.apply_wing_ranges(b)
    kin = flight.WingKinematics(rot_amp_deg=a.rot_amp)
    if a.rot_mean is not None:
        kin.rot_mean_deg = a.rot_mean
    wb = flight.WingBeat(b, kin, ramp_ms=0.0)
    wb.power[:] = 1.0
    b.passive_hooks = [wb]
    be = flight.apply_blade_element(b)
    mj.mj_forward(m, d)
    q0 = d.qpos[:7].copy()
    per = int(round(1000.0 / kin.f_hz / a.dt_ms))
    n = per * a.beats
    j70 = int(0.7 * be.alpha.shape[1])
    rec = []
    for _ in range(n):
        tq, tqd = kin.targets(wb.t_s)
        d.qpos[wb.q_adr] = np.tile(tq, 2); d.qvel[wb.v_adr] = np.tile(tqd, 2)
        b.step()
        d.qpos[:7] = q0; d.qvel[:6] = 0.0
        rec.append([wb.t_s * kin.f_hz % 1.0, np.degrees(tq[0]), np.degrees(tq[2]), be.alpha[0, j70],
                    *be.parts.sum(0)[:, 2], be.force.sum(0)[2] + d.qfrc_fluid[2]])
    r = np.array(rec[-per * 2:])
    W = mj.mj_getTotalmass(m) * 9810.0
    names = ["lift", "drag", "rotational", "total incl. body"]
    out = dict(rot_amp_deg=a.rot_amp, rot_mean_deg=kin.rot_mean_deg, weight_uN=W,
               mean_over_weight={k: round(float(r[:, 4 + i].mean() / W), 3) for i, k in enumerate(names)},
               alpha70_deg_at_midstroke=[round(float(r[np.argmin(abs(r[:per, 0] - p)), 3]), 1) for p in (0.25, 0.75)])
    out_dir = Path(a.out); out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"hover_blade_trace{a.tag}"
    (out_dir / f"{stem}.json").write_text(json.dumps(out, indent=1))
    o = np.argsort(r[:per, 0])
    ph = r[:per, 0][o]
    fig, ax = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    ax[0].plot(ph, r[:per, 1][o], label="stroke (yaw)"); ax[0].plot(ph, r[:per, 2][o], label="rotation (pitch)")
    ax[0].set_ylabel("joint angle (deg)"); ax[0].legend(fontsize=8)
    ax[1].plot(ph, r[:per, 3][o], "k"); ax[1].set_ylabel("left wing alpha at 70% span (deg)")
    for i, k in enumerate(names):
        ax[2].plot(ph, r[:per, 4 + i][o] / W, label=f"{k} (mean {out['mean_over_weight'][k]:+.2f})")
    ax[2].axhline(1.0, color="gray", ls=":"); ax[2].set_ylabel("vertical force / weight"); ax[2].legend(fontsize=8)
    ax[2].set_xlabel("wingbeat phase (0 = stroke at max yaw)")
    fig.suptitle(f"blade-element hover, imposed kinematics, rotation {kin.rot_mean_deg:.0f} +- {a.rot_amp:.0f} deg")
    fig.tight_layout(); fig.savefig(out_dir / f"{stem}.png", dpi=100)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
