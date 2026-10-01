"""Where along sugar -> MN9 does activity stop? Compares per-cell rates of two
sugar_mn9 assay runs (rates.npz, same trials) by synaptic hop distance from the
stimulated LB3b/LB3c cells, and lists MN9_L's active presynaptic partners.
Diagnostic for rung 2 (DECISIONS 2026-10-01): m9 vs m9 + conductance synapses.

    uv run python scripts/probes/sugar_cond_trace.py runs/assay-sugar_mn9-m9-A runs/assay-sugar_mn9-m9-B
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402


def mean_rates(run: Path) -> tuple[np.ndarray, np.ndarray]:
    z = np.load(run / "rates.npz")
    keys = [k for k in z.files if k.startswith("real_100_")]
    return z["body_id"], np.mean([z[k] for k in keys], axis=0)


def main() -> None:
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, "m9")
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    nrn = conn.neurons
    ida, ra = mean_rates(a)
    idb, rb = mean_rates(b)
    assert np.array_equal(ida, nrn.bodyId.to_numpy()) and np.array_equal(idb, ida)
    n = conn.n
    pre = np.repeat(np.arange(n), np.diff(conn.indptr))
    post = conn.indices
    stim = np.flatnonzero(nrn.type.isin(["LB3b", "LB3c"]).to_numpy())
    hop = np.full(n, -1)
    hop[stim] = 0
    front = stim
    for h in range(1, 6):
        m = np.isin(pre, front)
        nxt = np.unique(post[m])
        nxt = nxt[hop[nxt] < 0]
        hop[nxt] = h
        front = nxt
    rows = []
    for h in range(0, 6):
        m = hop == h
        rows.append(dict(hop=h, cells=int(m.sum()), active_a=int((ra[m] > 0).sum()),
                         active_b=int((rb[m] > 0).sum()), hz_sum_a=round(float(ra[m].sum()), 1),
                         hz_sum_b=round(float(rb[m].sum()), 1)))
    print(pd.DataFrame(rows).to_string(index=False))
    mn9 = np.flatnonzero((nrn.instance.fillna("") == "MN9_L").to_numpy())
    inp = pd.DataFrame({"pre": pre[np.isin(post, mn9)], "w": conn.weight_syn[np.isin(post, mn9)]
                        * conn.sign[pre[np.isin(post, mn9)]]})
    inp = inp.groupby("pre").w.sum()
    t = pd.DataFrame({"type": nrn.type.to_numpy()[inp.index], "syn_signed": inp.to_numpy(),
                      "hop": hop[inp.index], "hz_a": ra[inp.index].round(1), "hz_b": rb[inp.index].round(1)})
    t = t[(t.hz_a > 0) | (t.hz_b > 0)].sort_values("syn_signed", key=abs, ascending=False)
    print("\nactive inputs to MN9_L (synapses x sign):")
    print(t.head(25).to_string(index=False))
    lost = (ra > 1) & (rb == 0)
    print(f"\ncells >1 Hz in A and silent in B: {lost.sum()}; by hop:",
          np.bincount(hop[lost] + 1, minlength=7)[1:].tolist())
    print("top lost types:", nrn.type[lost].value_counts().head(12).to_dict())


if __name__ == "__main__":
    main()
