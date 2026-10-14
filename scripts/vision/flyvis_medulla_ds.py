"""Does the published flyvis ensemble stay direction selective under flyapp's T4/T5 stimuli?

flyapp's test (app/tools/t4t5_ds.py) moves a 2-column bar one column per 50 ms either through the
photoreceptors or by injecting current straight into the T4 inputs (Mi1, Tm3, Mi4, C3 up, Mi9 down)
or the T5 inputs (Tm1, Tm2 up), all at once in each column the bar covers. The injection set skips
the lamina and the hops that delay Mi4/Mi9 behind Mi1/Tm3 in a moving edge. If the fitted networks
lose direction selectivity under the injection set, a model built from their per-type values can't
be expected to pass it, whatever else is right.

Bars run at 12 angles; DSI = (P - N) / (P + N) of the peak depolarisation of the central cell above
its grey steady state, P at the preferred angle and N at the opposite one.

    uv run python scripts/vision/flyvis_medulla_ds.py --models 0-9 --amp 0.5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyvis_sim import RAW, FlyvisNet  # noqa: E402

T4 = ["T4a", "T4b", "T4c", "T4d"]
T5 = ["T5a", "T5b", "T5c", "T5d"]
INJECT = {"on": {"Mi1": 1, "Tm3": 1, "Mi4": 1, "C3": 1, "Mi9": -1}, "off": {"Tm1": 1, "Tm2": 1}}


def bar_frames(net: FlyvisNet, angle: float, width=2.0, speed=20.0, dt=0.005, pad_s=0.3):
    """(T, n_cols) mask of the columns a bar covers; width in column spacings, speed in columns/s."""
    xy = net.col_xy() / np.sqrt(3)          # unit = distance between neighbouring columns
    d = np.array([np.cos(np.radians(angle)), np.sin(np.radians(angle))])
    proj = xy @ d
    span = proj.max() - proj.min() + width
    T = int(span / speed / dt) + int(pad_s / dt)
    front = proj.min() + speed * np.arange(T) * dt
    return ((proj[None, :] <= front[:, None]) & (proj[None, :] > front[:, None] - width)).astype(float)


def dsi_table(peaks: np.ndarray, angles: np.ndarray) -> list[tuple[int, float, float]]:
    out = []
    for k in range(peaks.shape[1]):
        p = peaks[:, k]
        i = int(np.argmax(p))
        n = p[(i + len(angles) // 2) % len(angles)]
        out.append((int(angles[i]), float((p[i] - n) / (p[i] + n + 1e-12)), float(p[i])))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="0-4")
    ap.add_argument("--amp", type=float, default=0.5, help="injected current, flyvis units (R input step is 0.5)")
    ap.add_argument("--out", default="runs/vision/flyvis_medulla_ds.csv")
    a = ap.parse_args()
    lo, _, hi = a.models.partition("-")
    models = range(int(lo), int(hi or lo) + 1)
    net = FlyvisNet()
    angles = np.arange(0, 360, 30)
    dt = 0.005
    rows = []
    for m in models:
        net.set_model(RAW / "results" / "flow" / "0000" / f"{m:03d}" / "best_chkpt")
        v0 = net.steady(dt=dt)
        for pol, cells in (("on", T4), ("off", T5)):
            rec = np.array([net.central(t) for t in cells])
            gain = np.zeros(net.n)
            for typ, s in INJECT[pol].items():
                gain[net.node_type == net.tid[typ]] = s * a.amp
            net.inject_gain = gain
            for stim in ("photoreceptor", "medulla"):
                peaks = []
                for ang in angles:
                    mask = bar_frames(net, ang, dt=dt)
                    if stim == "photoreceptor":
                        lum = 0.5 + (0.5 if pol == "on" else -0.5) * mask
                        V = net.run(lum, dt, v0=v0, record=rec)
                    else:
                        V = net.run(np.full_like(mask, 0.5), dt, v0=v0, record=rec, inject=mask)
                    peaks.append(np.maximum(V - v0[rec], 0).max(0))
                for typ, (pd_, dsi, pk) in zip(cells, dsi_table(np.array(peaks), angles)):
                    rows.append(dict(model=m, stimulus=stim, type=typ, preferred_deg=pd_, dsi=dsi, peak_au=pk))
        df = pd.DataFrame(rows)
        cur = df[df.model == m].pivot(index="type", columns="stimulus", values="dsi")
        print(f"model {m:03d} DSI\n{cur.round(2).T.to_string()}", flush=True)
    df = pd.DataFrame(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, float_format="%.4g")
    print("\nmedian DSI over models\n", df.pivot_table(index="type", columns="stimulus", values="dsi",
                                                      aggfunc="median").round(2).T.to_string())


if __name__ == "__main__":
    main()
