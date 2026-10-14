"""Which fitted flyvis quantities carry T4/T5 direction selectivity under flyapp's bars?

Ablations of each published network, scored as in flyvis_medulla_ds.py (median DSI per subtype):
  full       the network as published
  tau20      every time constant at 20 ms (the training floor; removes the slow C2, C3, Tm2, Mi15 ...)
  rank1      type-pair strengths alpha_st replaced by their best per-type product a_s * b_t
             (least squares in log space): what per-type release and input gains can express
  const      one strength for every type pair: synapse counts and signs alone
  rank1_tau20, const_tau20
  *_rest     as the arm, with each type's bias reset so its grey steady state equals the published
             network's (the per-type operating point our release_at_rest rows carry over)
  t4in_rank1_rest   rank1 only on the edges into T4/T5, published strengths elsewhere, rest kept
  t4in_full_rest    published strengths only on the edges into T4/T5, rank1 elsewhere, rest kept

Our LIF model has per-type release_gain and input_gain but no per-type-pair strength, so 'rank1'
is the most a per-type mapping can carry over from flyvis.

    uv run python scripts/vision/flyvis_ablate_ds.py --models 0-9
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyvis_medulla_ds import INJECT, T4, T5, bar_frames, dsi_table  # noqa: E402
from flyvis_sim import RAW, FlyvisNet  # noqa: E402

ARMS = ["full", "tau20", "rank1", "rank1_rest", "const_rest", "t4in_rank1_rest", "t4in_full_rest"]


def rank1(alpha: np.ndarray, pairs: list[tuple[int, int]], n_types: int) -> np.ndarray:
    """Least-squares fit of log alpha_st = log a_s + log b_t over the pairs that exist."""
    ok = alpha > 0
    rows = [k for k in range(len(pairs)) if ok[k]]
    A = np.zeros((len(rows), 2 * n_types))
    for r, k in enumerate(rows):
        s, t = pairs[k]
        A[r, s] = 1.0
        A[r, n_types + t] = 1.0
    x, *_ = np.linalg.lstsq(A, np.log(alpha[rows]), rcond=None)
    return np.array([np.exp(x[s] + x[n_types + t]) for s, t in pairs])


def set_arm(net: FlyvisNet, arm: str, v_target: np.ndarray | None = None) -> None:
    d = net.ckpt
    full = d["edges_syn_strength"].astype(float)
    r1 = rank1(full, net.pair_types, len(net.types))
    into_t = np.array([net.types[t].startswith(("T4", "T5")) for _, t in net.pair_types])
    if arm.startswith("rank1"):
        alpha = r1
    elif arm.startswith("const"):
        alpha = np.full_like(full, np.median(full[full > 0]))
    elif arm.startswith("t4in_rank1"):
        alpha = np.where(into_t, r1, full)
    elif arm.startswith("t4in_full"):
        alpha = np.where(into_t, full, r1)
    else:
        alpha = full
    w = net.sign * net.nsyn_ckpt[net.grp] * alpha[net.pair]
    net.W = sparse.csr_matrix((w, (net.tgt, net.src)), shape=(net.n, net.n))
    tau = d["nodes_time_const"].astype(float)
    net.tau = (np.full_like(tau, 0.02) if "tau20" in arm else tau)[net.node_type]
    net.bias = d["nodes_bias"][net.node_type].astype(float)
    if arm.endswith("_rest") and v_target is not None:
        # per-type bias that makes the published grey state a fixed point of the ablated network:
        # 0 = -v + b + W relu(v) + x at v = v_target, so b_t = median over type t of v - W relu(v) - x
        # (exact for interior cells; an iterative correction diverges through the recurrent gain)
        nt = len(net.types)
        x = np.zeros(net.n)
        x[net.input_nodes] = 0.5
        need = v_target - net.W @ np.maximum(v_target, 0.0) - x
        b = np.array([np.median(need[net.node_type == t]) for t in range(nt)])
        net.bias = b[net.node_type]
        v = net.steady(t=1.0)
        err = np.bincount(net.node_type, v_target - v, nt) / np.bincount(net.node_type, None, nt)
        net.rest_err = float(np.abs(err).max())   # large if the fixed point is unstable


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="0-9")
    ap.add_argument("--amp", type=float, default=0.5)
    ap.add_argument("--out", default="runs/vision/flyvis_ablate_ds.csv")
    ap.add_argument("--arms", default=",".join(ARMS))
    a = ap.parse_args()
    arms = a.arms.split(",")
    lo, _, hi = a.models.partition("-")
    net = FlyvisNet()
    angles = np.arange(0, 360, 30)
    dt = 0.005
    masks = {ang: bar_frames(net, ang, dt=dt) for ang in angles}
    rows = []
    for m in range(int(lo), int(hi or lo) + 1):
        net.set_model(RAW / "results" / "flow" / "0000" / f"{m:03d}" / "best_chkpt")
        set_arm(net, "full")
        v_full = net.steady(dt=dt)
        for arm in arms:
            net.rest_err = 0.0
            set_arm(net, arm, v_target=v_full)
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
                        mask = masks[ang]
                        if stim == "photoreceptor":
                            V = net.run(0.5 + (0.5 if pol == "on" else -0.5) * mask, dt, v0=v0, record=rec)
                        else:
                            V = net.run(np.full_like(mask, 0.5), dt, v0=v0, record=rec, inject=mask)
                        peaks.append(np.maximum(V - v0[rec], 0).max(0))
                    for typ, (pd_, dsi, pk) in zip(cells, dsi_table(np.array(peaks), angles)):
                        rows.append(dict(model=m, arm=arm, stimulus=stim, type=typ, preferred_deg=pd_,
                                         dsi=dsi, peak_au=pk, v_rest_au=float(v0[rec[cells.index(typ)]]),
                                         rest_err=net.rest_err))
        df = pd.DataFrame(rows)
        print(f"model {m:03d}\n" + df[df.model == m].pivot_table(index=["stimulus", "arm"], columns="type",
                                                                   values="dsi").round(2).to_string(), flush=True)
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(a.out, index=False, float_format="%.4g")
    df = pd.DataFrame(rows)
    print("\nmedian DSI over models\n" + df.pivot_table(index=["stimulus", "arm"], columns="type", values="dsi",
                                                       aggfunc="median").round(2).to_string())


if __name__ == "__main__":
    main()
