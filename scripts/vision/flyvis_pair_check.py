"""Per-class size check of the flyvis pair-strength arm against measured ranges (fly2, s14).

Ben's condition (DECISIONS 13 Oct 22:53): each pair strength x synapse count must give a PSP inside the
measured range for its class; flag outliers, never clip. For graded synapses the PSP-equivalent is the
voltage gain: postsynaptic mV per presynaptic mV on the linear part of release. Per type pair and per
postsynaptic cell this sums alpha x count over the presynaptic cells of that type (nominal; tonic
conductance shunts it in the network) and sets it beside the shared scale's gain (count x efficacy x
gains, same conversion). Measured comparisons (only those a primary source gave, s14 literature pass):
  R1-R6 -> L1/L2 summed: LMC/photoreceptor peak response ratio 15-45 mV / 35-40 mV ~ 0.4-1.3 (Zheng et al.
  2006 J Gen Physiol 127:495, Drosophila, in vivo, bright stimuli; derived). Saturating peaks, so only a
  lower bound (0.4) on the small-signal gain is checked, sign inverting. Every other class: no measured range found, reported
  as unchecked. A summed gain x presynaptic release range above 60 mV (more than the span between the
  reversal potentials around rest, guessed ceiling) is flagged.

    FLYEMU_EXTRA_PARAMS=data/params/candidates/candidates_s13_v0r.csv \
        .venv/bin/python scripts/vision/flyvis_pair_check.py --out docs/media/s14_fly2_flyvis_pairs.png
    (add --ct1 for CT1 as per-column compartments, so the CT1(M10)/CT1(Lo1) rows are checked too)
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import lif, profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402

V0R = {"cell_type:all|mode_from_recordings": 1.0, "cell_type:ol_graded|release_at_rest": 0.5,
       "cell_type:all|conductance_based": 1.0, "cell_type:all|graded_range_from_recordings": 2.0,
       "photoreceptor:all|luminance_gain": 78.0, "cell_type:all|leak_from_network_rest": 1.0,
       "cell_type:all|release_at_rest_per_type": 1.0, "cell_type:all|optic_lobe_flyvis": 1.0}
KEY = "cell_type:all|optic_lobe_flyvis_pair_strength"
CT1_KEY = "cell_type:CT1|compartments_by_column"
CEIL_MV = 60.0
LMC = (0.4, 1.3)


def edge_w(net):
    """Current-basis weight per edge; graded cells' weights live in W_graded (net.w is zeroed there)."""
    c = net.conn
    pre = np.repeat(np.arange(c.n), np.diff(c.indptr))
    w = net.w.astype(np.float64).copy()
    gpos = np.full(c.n, -1)
    gpos[net.g_idx] = np.arange(net.g_idx.size)
    m = gpos[pre] >= 0
    w[m] = np.asarray(net.W_graded.T.tocsr()[gpos[pre[m]], c.indices[m]]).ravel()
    return w


def gains(net, w):
    """Linear voltage gain per edge (post mV per pre mV) of current-basis weights w from graded cells."""
    p, n, dt, c = net.params, net.conn.n, net.timestep_ms, net.conn
    pre = np.repeat(np.arange(n), np.diff(c.indptr))
    rng = (net.v_th - net.v_rest if p.graded_range is None else lif._arr(p.graded_range, n)).astype(np.float64)
    r0 = np.zeros(n) if p.graded_r0 is None else lif._arr(p.graded_r0, n, np.float64)
    gk = np.ones(n) if p.graded_k is None else lif._arr(p.graded_k, n, np.float64)
    ds = np.exp(-dt / lif._arr(p.tau_s, n, np.float64))
    g = w * gk[pre] * (1 - r0[pre]) / rng[pre] * (p.graded_rmax_hz * dt / 1000.0) / (1 - ds[c.indices])
    return g, rng


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m9c")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ct1", action="store_true", help="CT1 per-column compartments on (CT1 rows then select)")
    a = ap.parse_args()
    ov = {**V0R, KEY: 1.0, **({CT1_KEY: 1.0} if a.ct1 else {})}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=profiles.WORKING_MIN_SYNAPSES, seed=0,
                   overrides=ov)
    c, p = org.conn, org.net.params
    flat = lambda q: lif.Network(c, dataclasses.replace(q, cond=False), org.timestep_ms)
    on, off = flat(p), flat(dataclasses.replace(p, fv_edge=None))
    g_fv, rng = gains(on, edge_w(on))
    g_sh, _ = gains(off, edge_w(off))
    pre = np.repeat(np.arange(c.n), np.diff(c.indptr))
    fe = p.fv_edge
    tab = pd.read_csv(REPO / "data" / "params" / lif.FV_PAIR_TABLE, comment="#")
    tab = tab[tab.use == 1]
    graded = on.graded
    rows = []
    for r in tab.itertuples():
        mp, mq = lif._stp_cells(c.neurons, r.pre), lif._stp_cells(c.neurons, r.post)
        e = np.flatnonzero(mp[pre] & mq[c.indices])
        if not e.size:
            rows.append(dict(pair=r.flyvis_pair, edges=0))
            continue
        gr = graded[pre[e]]
        eg = e[gr]
        post = c.indices[eg]
        s_fv = pd.Series(g_fv[eg]).groupby(post).sum()
        s_sh = pd.Series(g_sh[eg]).groupby(post).sum()
        dv = pd.Series(np.abs(g_fv[eg]) * rng[pre[eg]]).groupby(post).sum()
        flip = int((np.sign(c.sign[pre[e]]) != r.flyvis_sign).sum())
        rows.append(dict(pair=r.flyvis_pair, edges=int(e.size), spiking_pre_edges=int((~gr).sum()),
                         alpha=r.alpha, sign_flips=flip, post_cells=int(s_fv.size),
                         gain_fv_median=float(s_fv.median()) if s_fv.size else np.nan,
                         gain_fv_max=float(s_fv.abs().max()) if s_fv.size else np.nan,
                         gain_shared_median=float(s_sh.median()) if s_sh.size else np.nan,
                         dv_full_range_max_mv=float(dv.max()) if dv.size else np.nan))
    df = pd.DataFrame(rows)
    df["flag"] = ""
    df.loc[df.edges == 0, "flag"] = "no edges in male-cns at this threshold"
    df.loc[df.dv_full_range_max_mv > CEIL_MV, "flag"] = f"full-range response > {CEIL_MV:g} mV (guessed ceiling)"
    df.loc[(df.spiking_pre_edges > 0) & (df.flag == ""), "flag"] = "spiking presynaptic cells keep the shared scale"
    lm = df.pair.isin(["R1-R6->L1", "R1-R6->L2"])
    df["measured"] = np.where(lm, "LMC/PR >= 0.4, inverting (Zheng 2006, derived lower bound)", "no measured range found")
    for i in df.index[lm]:
        if abs(df.gain_fv_median[i]) < LMC[0] or df.gain_fv_median[i] > 0:
            df.loc[i, "flag"] = (df.flag[i] + "; " if df.flag[i] else "") + "below the measured LMC lower bound"
    df.to_csv(a.out.with_suffix(".csv"), index=False)
    summ = {"pairs_read": int(len(df)), "edges_set": int(len(fe["idx"])), "edges_kept_spiking_pre":
            int(on.fv_spiking_pre), "pairs_with_edges": int((df.edges > 0).sum()),
            "flags": df.flag[df.flag != ""].value_counts().to_dict(),
            "lmc": df.loc[lm, ["pair", "gain_fv_median", "gain_shared_median"]].to_dict("records"),
            "ratio_fv_to_shared_median": float(np.nanmedian(np.abs(df.gain_fv_median / df.gain_shared_median))),
            "sign_flip_pairs": df.pair[df.sign_flips > 0].tolist()}
    a.out.with_suffix(".json").write_text(json.dumps(summ, indent=1, default=float) + "\n")
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ok = df.edges > 0
    x, y = df.gain_shared_median[ok].abs(), df.gain_fv_median[ok].abs()
    ax.scatter(x, y, s=8, c=np.where(df.flag[ok] != "", "tab:red", "tab:blue"), alpha=0.7)
    for i in df.index[lm]:
        ax.annotate(df.pair[i], (abs(df.gain_shared_median[i]), abs(df.gain_fv_median[i])), fontsize=7)
    ax.plot([5, 50], [LMC[0]] * 2, color="tab:green", lw=2,
            label="R1-R6 -> LMC measured lower bound, those two rows only (Zheng 2006, derived)")
    lim = [1e-4, 1e2]
    ax.plot(lim, lim, color="0.6", lw=0.8, ls=":", label="equal")
    ax.set(xscale="log", yscale="log", xlim=lim, ylim=lim, xlabel="shared scale: |gain| per post cell (mV/mV)",
           ylabel="flyvis (fitted, task-trained): |gain| per post cell (mV/mV)")
    ax.set_title(f"flyvis pair strengths vs the shared scale, {int(ok.sum())} type pairs (median post cell)"
                 + (", CT1 per column" if a.ct1 else "") + "\n"
                 "red: flagged (no clipping)", fontsize=9)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(a.out, dpi=130)
    print(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()
