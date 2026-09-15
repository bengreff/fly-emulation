"""Which sign flips break the rhythm?

The transmitter classifier reports a probability per neuron. Resampling sign
from those probabilities flips about 9.5% of the network per draw and destroys
the rhythm in a substantial fraction of draws. This asks whether the failures
are explained by flips in the small circuit the original authors identified as
the rhythm's core.

Reproduces the draw for each replicate from its seed, so no extra simulation is
needed. Usage:

    uv run python scripts/analyze_sign_flips.py runs/<ntsample run dir>
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
WTABLE = (REPO / "external" / "Pugliese_cpg_2025" / "data" /
          "manc t1 connectome data" / "wTable_20250813_DNtoMN_unsorted_withModules.csv")
# DNg100 plus the three interneurons named in the authors' own CoreCPG config
CORE = [31, 277, 617, 1167]
SEED_BASE = 10_000
WORKED = 0.3   # rhythmicity above this counts as the circuit still working


def transmitter_probs(wt: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    P = wt[["ntAcetylcholineProb", "ntGabaProb", "ntGlutamateProb"]].to_numpy(float)
    P = np.where(np.isfinite(P), P, 0.0)
    rowsum = P.sum(axis=1, keepdims=True)
    P = np.where(rowsum > 0, P / np.maximum(rowsum, 1e-12), np.array([1.0, 0.0, 0.0]))
    return P, P.argmax(axis=1) == 0     # True where the most likely label is excitatory


def main() -> None:
    run = Path(sys.argv[1])
    m = run / "metrics.csv"
    if not m.exists():
        m = run / "metrics_partial.csv"
    d = pd.read_csv(m)
    wt = pd.read_csv(WTABLE, index_col=0, low_memory=False)
    P, argmax_exc = transmitter_probs(wt)

    print("Core circuit neurons and the chance the classifier's uncertainty flips each:")
    p_any_stays = 1.0
    for c in CORE:
        p_flip = (1 - P[c, 0]) if argmax_exc[c] else P[c, 0]
        p_any_stays *= (1 - p_flip)
        print(f"  index {c:5d}  {str(wt.loc[c,'type']):10s} {str(wt.loc[c,'predictedNt']):14s} "
              f"confidence {wt.loc[c,'predictedNtProb']:.3f}   P(flip) = {p_flip:.3f}")
    print(f"\nExpected fraction of draws with at least one core flip: {1 - p_any_stays:.3f}")

    rows = []
    for i in d.replicate:
        rng = np.random.default_rng(SEED_BASE + int(i))
        draw = (rng.random((P.shape[0], 1)) < P.cumsum(axis=1)).argmax(axis=1)
        flip = (draw == 0) != argmax_exc
        rows.append({"replicate": int(i), "total_flips": int(flip.sum()),
                     "core_flipped": int(flip[CORE].sum()),
                     "which_core": [c for c in CORE if flip[c]]})
    f = pd.DataFrame(rows).merge(
        d[["replicate", "oscillation_score_mn", "n_active_mn"]], on="replicate")
    f["worked"] = f.oscillation_score_mn > WORKED

    print(f"\nSign flips per draw: mean {f.total_flips.mean():.0f} of {len(wt)} neurons "
          f"({f.total_flips.mean()/len(wt)*100:.1f}%)")
    print(f"Draws where the rhythm survived: {f.worked.sum()} of {len(f)}")
    print("\nDid a core neuron flip, against whether the rhythm survived:")
    print(pd.crosstab(f.core_flipped > 0, f.worked,
                      rownames=["core neuron flipped"],
                      colnames=["rhythm survived"]).to_string())
    bad = f[f.core_flipped > 0]
    if len(bad):
        print(f"\nOf the {len(bad)} draws that flipped a core neuron, "
              f"{int((~bad.worked).sum())} lost the rhythm.")
    out = run / "sign_flip_analysis.csv"
    f.to_csv(out, index=False)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
