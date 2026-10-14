"""Impulse-response peak times of Mi1, Tm3, Tm1 and Tm2 in the published flyvis networks, against
Behnia et al. 2014 Nature 512:427 (in vivo linear filter peaks: Mi1 71, Tm3 53, Tm1 56, Tm2 43 ms).

Each network sits at grey (0.5); a 20 ms full-field flash to 1 (ON cells Mi1, Tm3) or 0 (OFF cells Tm1,
Tm2) follows, and the central cell's peak time after flash onset is read. The recorded numbers are
whole-pathway filter peaks (photoreceptor to the cell), so this compares whole pathways, not one
cell's time constant. Used to decide which tau_m_flyvis rows conflict with a recording
(flyvis_rows.py CONFLICT).

    uv run python scripts/vision/flyvis_impulse.py --models 50
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyvis_sim import RAW, FlyvisNet  # noqa: E402

RECORDED_MS = {"Mi1": 71.0, "Tm3": 53.0, "Tm1": 56.0, "Tm2": 43.0}   # Behnia 2014, measured
ON_CELLS = {"Mi1", "Tm3"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", type=int, default=50)
    ap.add_argument("--out", default="data/derived/flyvis_lappalainen2024_impulse_peaks.csv")
    a = ap.parse_args()
    net = FlyvisNet()
    dt = 0.005
    cells = list(RECORDED_MS)
    rec = np.array([net.central(t) for t in cells])
    rows = []
    for m in range(a.models):
        net.set_model(RAW / "results" / "flow" / "0000" / f"{m:03d}" / "best_chkpt")
        v0 = net.steady(dt=dt)
        for on, lum in ((True, 1.0), (False, 0.0)):
            L = np.full((int(0.5 / dt), len(net.cols)), 0.5)
            L[: int(0.02 / dt)] = lum
            V = net.run(L, dt, v0=v0, record=rec) - v0[rec]
            for k, c in enumerate(cells):
                if (c in ON_CELLS) != on:
                    continue
                tau = 1000 * max(float(net.ckpt["nodes_time_const"][net.tid[c]]), 0.02)
                rows.append(dict(model=m, type=c, tau_eff_ms=tau, peak_ms=1000 * dt * (1 + int(np.argmax(V[:, k]))),
                                 peak_au=float(V[:, k].max()), recorded_peak_ms=RECORDED_MS[c]))
    df = pd.DataFrame(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, float_format="%.4g")
    print(df.groupby("type")[["peak_ms", "recorded_peak_ms", "tau_eff_ms"]].median().round(1).to_string())
    w = df.pivot(index="model", columns="type", values="peak_ms")
    print(f"networks with Tm2 faster than Tm1: {(w.Tm2 < w.Tm1).mean():.2f} (recorded: faster)")
    print(f"networks with Tm3 faster than Mi1: {(w.Tm3 < w.Mi1).mean():.2f} (recorded: faster)")


if __name__ == "__main__":
    main()
