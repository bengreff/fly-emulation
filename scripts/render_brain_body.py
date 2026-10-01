"""Render the closed loop to a side-by-side video: body camera + brain activity panel.

For a non-specialist viewer: the left panel is the same tracking-camera render as
scripts/render_organism.py. The right panel is per-class population firing rate
(spikes/s, averaged over 1 ms bins) for five coarse groups (sensory, central,
ascending, descending, motor), with a moving cursor marking the current instant.
The two panels share the same simulated clock; nothing here re-simulates or
reorders anything the organism loop produced.

    uv run python scripts/render_brain_body.py --duration-ms 3000 --seed 12 \
        --set "motor_unit:all|force_per_spike=10" \
        --out docs/media/m9_closed_loop.mp4

Uses the working model (profiles.WORKING_PROFILE, WORKING_MIN_SYNAPSES), same as
render_organism.py. A video is a communication artifact, not evidence
(docs/VALIDATION.md); the numbers come from the run records, not from this script.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from flyemu import profiles
from flyemu.organism import Organism

REPO = Path(__file__).resolve().parents[1]

# Coarse groups covering every superclass in the connectome table, for a legend
# a non-specialist can read at a glance.
GROUPS = {
    "sensory": ["ol_sensory", "vnc_sensory", "cb_sensory", "sensory_ascending",
                "sensory_descending", "vnc_sensory_tbc", "cb_sensory_tbc",
                "sensory_ascending_tbc"],
    "central": ["ol_intrinsic", "cb_intrinsic", "vnc_intrinsic",
                "visual_projection", "visual_centrifugal", "visual_projection_tbc",
                "vnc_tbc"],
    "ascending": ["ascending_neuron", "efferent_ascending"],
    "descending": ["descending_neuron", "efferent_descending"],
    "motor": ["vnc_motor", "cb_motor", "vnc_efferent", "vnc_endocrine",
              "cb_endocrine", "ENS", "cb_efferent"],
}
COLORS = {"sensory": "#1b9e77", "central": "#7570b3", "ascending": "#e6ab02",
          "descending": "#d95f02", "motor": "#e7298a"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration-ms", type=float, default=1500.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", action="append",
                    default=None)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--playback-speed", type=float, default=1.0,
                    help="1.0 = output video plays at the same rate as simulated time")
    ap.add_argument("--camera-res", default="240x320", help="HxW pixels for the body panel")
    ap.add_argument("--panel-width", type=int, default=416,
                    help="pixel width of the brain panel (416 + 320 cam = 736, a multiple of 16, "
                         "so the ffmpeg writer does not resize/stretch the frame)")
    ap.add_argument("--out", default="docs/media/m9_closed_loop.mp4")
    args = ap.parse_args()

    overrides = {}
    for item in args.set or ["motor_unit:all|force_per_spike=10"]:
        k, _, v = item.partition("=")
        overrides[k] = float(v)
    for k, v in overrides.items():
        print(f"override: {k} = {v}")

    cam_h, cam_w = (int(x) for x in args.camera_res.lower().split("x"))

    org = Organism(policy="minimal", seed=args.seed, overrides=overrides, with_camera=True,
                   profile=profiles.WORKING_PROFILE, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    renderer = org.body.sim.set_renderer(
        f"{org.body.fly.name}/trackcam", camera_res=(cam_h, cam_w),
        playback_speed=args.playback_speed, output_fps=args.fps,
    )
    cam_name = next(iter(renderer._cameras_names2id))

    sc = org.conn.neurons.superclass.fillna("").to_numpy()
    group_id = np.full(org.conn.n, -1, dtype=np.int8)
    group_names = list(GROUPS)
    group_n = np.zeros(len(group_names), dtype=np.int64)
    for gi, (name, supers) in enumerate(GROUPS.items()):
        mask = np.isin(sc, supers)
        group_id[mask] = gi
        group_n[gi] = int(mask.sum())
    uncovered = int((group_id < 0).sum())
    if uncovered:
        print(f"warning: {uncovered} neurons not covered by any brain-panel group "
              f"(superclasses: {sorted(set(sc[group_id < 0]))})")

    print(f"network: {org.conn.n:,} neurons, {org.conn.n_edges:,} edges")
    for name, n in zip(group_names, group_n):
        print(f"  group {name:<10} {n:,} neurons")
    print(f"rendering {args.duration_ms:g} ms ...")

    n_steps = int(round(args.duration_ms / org.timestep_ms))
    ms_stride = max(1, int(round(1.0 / org.timestep_ms)))  # 1 ms bins
    n_bins = int(np.ceil(n_steps / ms_stride))
    bin_counts = np.zeros((n_bins, len(group_names)), dtype=np.int64)
    cur_bin = np.zeros(len(group_names), dtype=np.int64)

    frame_times_ms: list[float] = []
    bin_i = 0
    for step in range(n_steps):
        obs = org.body.observe()
        spiked = org.net.step(external_mv=org.sense(step, obs))
        org.motor_step(spiked)

        if spiked.size:
            g = group_id[spiked]
            g = g[g >= 0]
            if g.size:
                cur_bin += np.bincount(g, minlength=len(group_names))

        if (step + 1) % ms_stride == 0 or step == n_steps - 1:
            bin_counts[bin_i] = cur_bin
            cur_bin[:] = 0
            bin_i += 1

        if org.body.sim.render_as_needed():
            frame_times_ms.append((step + 1) * org.timestep_ms)

        if step % 5000 == 0:
            print(f"  {step * org.timestep_ms:7.1f} ms", flush=True)

    bin_width_s = ms_stride * org.timestep_ms / 1000.0
    hz = bin_counts / np.maximum(group_n, 1) / bin_width_s  # (n_bins, n_groups)
    t_bins_ms = (np.arange(n_bins) + 1) * ms_stride * org.timestep_ms

    body_frames = renderer.frames[cam_name]
    print(f"body frames: {len(body_frames)}  brain bins: {n_bins}")

    panel = make_brain_panel(t_bins_ms, hz, group_names, cam_h, args.panel_width)
    frames = []
    for t, body_img in zip(frame_times_ms, body_frames):
        cursor_x = int(round(t / args.duration_ms * args.panel_width))
        cursor_x = min(max(cursor_x, 0), args.panel_width - 2)
        brain_img = panel.copy()
        brain_img[:, cursor_x:cursor_x + 2] = (220, 30, 30)
        frames.append(np.hstack([body_img, brain_img]))

    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    import imageio.v3 as iio
    iio.imwrite(out, np.stack(frames), fps=args.fps, codec="libx264", quality=8)
    print(f"video: {out}  ({out.stat().st_size / 1e6:.2f} MB, {len(frames)} frames)")
    return 0


def make_brain_panel(t_ms: np.ndarray, hz: np.ndarray, group_names: list[str],
                      height_px: int, width_px: int) -> np.ndarray:
    """A static line chart of per-group firing rate vs. time, rendered once to
    an RGB array. The moving cursor is drawn later by overwriting a column."""
    dpi = 100
    fig = plt.figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    ax = fig.add_axes([0.16, 0.2, 0.8, 0.72])
    for gi, name in enumerate(group_names):
        ax.plot(t_ms, hz[:, gi], lw=1.0, color=COLORS[name], label=name)
    ax.set_xlim(t_ms[0] if len(t_ms) else 0, t_ms[-1] if len(t_ms) else 1)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("time (ms)", fontsize=7)
    ax.set_ylabel("firing rate (Hz, 1 ms bins)", fontsize=7)
    ax.set_title("m9 brain activity by class", fontsize=8)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=5.5, loc="upper right", framealpha=0.6)
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    img = buf[:, :, :3].copy()
    plt.close(fig)
    if img.shape[0] != height_px or img.shape[1] != width_px:
        img = img[:height_px, :width_px]
    return img


if __name__ == "__main__":
    sys.exit(main())
