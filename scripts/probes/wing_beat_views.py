"""Session 12 (F-WING-3): contact sheet of the wing poses over one beat, top and
front views, for the s10 joint-space generator and the measured stroke-frame beat
(flight.StrokeFrameKinematics, Muijres 2014). Poses are set kinematically (no
dynamics), thorax level.

    uv run python scripts/probes/wing_beat_views.py [--out docs/media/s12_wing_beat_views.png]
"""
from __future__ import annotations

import argparse
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
    ap.add_argument("--out", default=str(REPO / "docs" / "media" / "s12_wing_beat_views.png"))
    a = ap.parse_args()
    b = Body(vision=False)
    m = b.sim.mj_model
    flight.open_wing_ranges(b)
    kins = {"s10 generator (joint space)": flight.WingKinematics(),
            "measured beat (Muijres 2014, stroke frame)": flight.StrokeFrameKinematics(b)}
    adr = [m.jnt_qposadr[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"{b.fly.name}/c_thorax-{s}_wing-{flight.FN[f]}")]
           for s in flight.SIDES for f in ("stroke", "deviation", "rotation")]
    th = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{b.fly.name}/c_thorax")
    phases = (0.0, 0.15, 0.3, 0.45, 0.6, 0.8)
    views = {"top": (-90.0, 90.0), "front": (0.0, 180.0)}
    d = mj.MjData(m)
    r = mj.Renderer(m, 240, 240)
    cam = mj.MjvCamera()
    rows = [(k, v) for k in kins for v in views]
    fig, ax = plt.subplots(len(rows), len(phases), figsize=(2.0 * len(phases), 2.1 * len(rows)))
    for i, (kname, vname) in enumerate(rows):
        kin = kins[kname]
        for j, p in enumerate(phases):
            q, _ = kin.targets(p / kin.f_hz)
            d.qpos[:] = m.qpos0
            d.qpos[adr] = np.tile(q, 2)
            mj.mj_forward(m, d)
            cam.lookat[:] = d.xpos[th]
            cam.distance = 7.0
            cam.elevation, cam.azimuth = views[vname]
            r.update_scene(d, cam)
            ax[i, j].imshow(r.render())
            ax[i, j].set_xticks([]); ax[i, j].set_yticks([])
            if i == 0:
                ax[i, j].set_title(f"phase {p:.2f}", fontsize=9)
            if j == 0:
                ax[i, j].set_ylabel(f"{kname.split(' (')[0]}\n{vname}", fontsize=8)
    fig.suptitle("wing poses over one beat: s10 generator (rows 1-2) vs measured beat (rows 3-4); "
                 "top view head up, front view head toward viewer", fontsize=9)
    fig.tight_layout()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=90)
    print(out)


if __name__ == "__main__":
    main()
