"""Lagged MN readout for the bypass assay (s13; DECISIONS 13 Oct 22:18). Secondary readout, never a pass.

Pugliese's own model drives swing and stance coxa MNs at about 12 Hz, 12-17 ms apart. At zero lag the two pools
correlate positively, so S2's alternation test (r <= -0.3) misses them. This readout reports pairs of rhythmic MN
pools of one leg whose cross-correlation peaks (lags within +-45 ms) at |lag| >= 10 ms with r >= 0.5. A pool counts
as rhythmic when it is in the run's `rhythmic_pools` (rhythm excess > 0.10 at 4-25 Hz, S2's definition).

    uv run python scripts/probes/bypass_lag_readout.py runs/s13/bypass/s3/s2_A_25mv.json ...
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def smooth(x: np.ndarray, w: int) -> np.ndarray:
    return np.convolve(x, np.ones(w) / w, mode="same")


def lagged(a: np.ndarray, b: np.ndarray, maxlag: int = 45) -> tuple[int, float]:
    a = a - a.mean(); b = b - b.mean()
    best = (0, -2.0)
    for lag in range(-maxlag, maxlag + 1):
        x, y = (a[lag:], b[:len(b) - lag]) if lag >= 0 else (a[:lag], b[-lag:])
        d = np.sqrt((x * x).sum() * (y * y).sum())
        r = float((x * y).sum() / d) if d > 0 else 0.0
        if r > best[1]:
            best = (lag, r)
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--t0", type=int, default=400, help="start of the scored window, ms (S2: drive onset + 100)")
    ap.add_argument("--t1", type=int, default=1300)
    a = ap.parse_args()
    for f in a.runs:
        r = json.loads(Path(f).read_text())
        z = np.load(f.replace(".json", "_traces.npz"))
        names = [str(x) for x in z["pool_names"]]
        rhythmic = {p["pool"] for p in r["pools"] if (p["best_mn_rhythm_excess"] or 0) > 0.10
                    and p["best_mn_rhythm_hz"] is not None and 4 <= p["best_mn_rhythm_hz"] <= 25}
        sm = {nm: smooth(z["pool_rate"][:, i].astype(float), 20)[a.t0:a.t1] for i, nm in enumerate(names)}
        legs = {}
        for nm in rhythmic:
            legs.setdefault(nm[:2], []).append(nm)
        hits = []
        for leg, ps in legs.items():
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    lag, rr = lagged(sm[ps[i]], sm[ps[j]])
                    if abs(lag) >= 10 and rr >= 0.5:
                        hits.append((ps[i], ps[j], lag, round(rr, 2)))
        print(f"{Path(f).stem}: rhythmic pools {len(rhythmic)}, lagged pairs {len(hits)}"
              + "".join(f"\n   {x} | {y}: lag {l} ms, r {v}" for x, y, l, v in hits))


if __name__ == "__main__":
    main()
