"""F-STAND-3: thorax height against time for live, dead and silenced-at-T runs
of `standing_rest.py`, with Wang et al. 2025's motor-silencing reference
(fall onset 40-300 ms after light-on, median fall rate 1.3 mm/s; measured,
e49-Gal4 > GtACR1, held out). Fall metrics after T: onset is the first sample
1 % of body length (0.025 mm) below z(T); rate is the 10-90 % drop over its time.

    uv run python scripts/probes/stand_fall_plot.py [--dir runs/s12/stand3] [--seeds 12 13 14]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
ONSET_DROP_MM = 0.025


def fall_metrics(t: np.ndarray, z: np.ndarray, t_off: float) -> dict:
    k = t >= t_off
    t, z = t[k], z[k]
    z0, zmin = float(z[0]), float(z.min())
    drop = z0 - zmin
    below = np.nonzero(z < z0 - ONSET_DROP_MM)[0]
    res = dict(z_at_silence_mm=round(z0, 3), z_min_after_mm=round(zmin, 3), drop_mm=round(drop, 3),
               onset_ms=round(float(t[below[0]] - t_off), 1) if len(below) else None)
    if len(below) and drop > ONSET_DROP_MM:
        i10 = np.nonzero(z <= z0 - 0.1 * drop)[0][0]
        i90 = np.nonzero(z <= z0 - 0.9 * drop)[0][0]
        dt = (t[i90] - t[i10]) / 1e3
        res["rate_10_90_mm_s"] = round(float(0.8 * drop / dt), 2) if dt > 0 else None
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(REPO / "runs" / "s12" / "stand3"))
    ap.add_argument("--seeds", type=int, nargs="+", default=[12, 13, 14])
    ap.add_argument("--silence-tag", default="silence500")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = Path(a.dir)
    fig, ax = plt.subplots(1, len(a.seeds), figsize=(5 * len(a.seeds), 4), sharey=True, squeeze=False)
    out = {}
    for a_, s in zip(ax[0], a.seeds):
        res = {}
        for tag, col in (("live", "k"), ("dead", "tab:red"), (a.silence_tag, "tab:blue")):
            f = d / f"standing_{tag}_s{s}.json"
            if not f.exists():
                continue
            J = json.loads(f.read_text())
            tr = J["trace"]
            t = np.array([r["t_ms"] for r in tr]); z = np.array([r["z_mm"] for r in tr])
            tf = np.array([r["trunk_floor"] for r in tr])
            a_.plot(t, z, color=col, label=tag)
            if tf.any():
                a_.plot(t[tf], np.full(tf.sum(), z.min() - 0.02 if tag == "live" else z.min() - 0.03),
                        "|", color=col, ms=3)
            summ = J["summary"]
            res[tag] = dict(z_end_mm=summ["z_end_mm"], trunk_floor_first_ms=summ["trunk_floor_first_ms"],
                            trunk_floor_frac=summ["trunk_floor_frac"], load_hz_by_leg=summ.get("load_hz_by_leg"),
                            mn_hz_by_group=summ["mn_hz_by_group"])
            if tag == a.silence_tag and summ.get("silence_at_ms") is not None:
                T = float(summ["silence_at_ms"])
                res[tag]["fall"] = fall_metrics(t, z, T)
                a_.axvline(T, color="tab:blue", ls=":", lw=1)
                a_.axvspan(T + 40, T + 300, color="tab:green", alpha=0.12, label="Wang 2025 onset 40-300 ms")
                zT = float(np.interp(T, t, z))
                tt = np.array([T + 40, T + 40 + 1e3 * 0.5 / 1.3])
                a_.plot(tt, zT - 1.3 * (tt - tt[0]) / 1e3, color="tab:green", lw=1,
                        label="1.3 mm/s (Wang median)")
            if tag == "dead":
                res[tag]["fall_from_placement"] = fall_metrics(t, z, 0.0)
        out[s] = res
        a_.set_title(f"seed {s}"); a_.set_xlabel("t (ms)")
        a_.legend(fontsize=7)
    ax[0][0].set_ylabel("thorax z (mm); ticks: trunk on floor")
    fig.suptitle("m9f standing: live, dead, motor output silenced at 500 ms")
    fig.tight_layout(); fig.savefig(d / "fall_curves.png", dpi=90); plt.close(fig)
    (d / "fall_summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
