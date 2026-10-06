"""Conductance state of medulla cells in dark and steady light, split by presynaptic type (s12 vision).

What limits Mi1's ON swing (DECISIONS 6 Oct, gain block)? In conductance mode a cell sits at
    v = (v_leak + extra + g_e E_exc + g_i E_inh) / (1 + g_e + g_i)
(leak conductance = 1). For each type, on cells whose cartridge has photoreceptor input (visual_flash_score),
this reports v, g_e, g_i and G in the dark after a settle and after --light-ms of full-field light, and the
ceiling the cell would reach if every graded inhibitory input vanished with g_e as in the light. If the light
potential is near that ceiling, the leak/excitation sets the limit; if far below, inhibition is not removed
(modulation depth). The graded part of g_e and g_i is split by presynaptic type from W_graded and each
presynaptic cell's release fraction (steady state: arrival / (1 - decay)); the spiking part is split the same
way from each presynaptic cell's spike count over the last --window-ms of the phase times its edge weights (times
its current depression factor when short-term depression is on; facilitation and presynaptic inhibition are
ignored, so this is an estimate). `split_residual` is the measured g minus the two splits.

    uv run python scripts/probes/visual_conductance_state.py --profile m9c --set ... --out runs/s12/vision/cstate.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu import connectome, electrical, lif, profiles, vision  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402
from visual_flash_score import connected  # noqa: E402

DT = 0.1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--types", default="L1,L2,Mi1,Tm3,Tm1,Tm2")
    ap.add_argument("--settle-ms", type=float, default=600.0)
    ap.add_argument("--light-ms", type=float, default=300.0)
    ap.add_argument("--window-ms", type=float, default=200.0, help="spike-count window at the end of each phase")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    reg = Registry(Policy.MINIMAL)
    for s in a.set:
        k, v = s.split("=")
        reg.overrides[k] = float(v)
    profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    assert params.cond, "needs cell_type:all|conductance_based=1"
    el = electrical.build(reg, conn)
    vis = vision.build(reg, conn, timestep_ms=DT, sample_hz=100.0)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(1))
    net.elec = el if len(el[0]) else None
    t = conn.neurons.type.fillna("").to_numpy()
    bid = conn.neurons.bodyId.to_numpy()
    con = connected(pd.Series(t, index=bid))
    types = a.types.split(",")
    groups = {ty: np.flatnonzero((t == ty) & np.isin(bid, list(con.get(ty, set(bid[t == ty])))))
              for ty in types}
    g_idx = net.g_idx
    ptypes, pcode = np.unique(t[g_idx], return_inverse=True)
    onehot = sp.csr_matrix((np.ones(g_idx.size), (np.arange(g_idx.size), pcode)), shape=(g_idx.size, ptypes.size))
    p = params
    atypes, acode = np.unique(t, return_inverse=True)
    onehot_all = sp.csr_matrix((np.ones(conn.n), (np.arange(conn.n), acode)), shape=(conn.n, atypes.size))
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    w = np.asarray(net.w)
    Wsp = {sign: sp.csr_matrix((np.abs(w[m]), (conn.indices[m], pre[m])), shape=(conn.n, conn.n))
           for sign, m in (("e", w > 0), ("i", w < 0))}
    counts = np.zeros(conn.n)

    def release() -> np.ndarray:
        g = g_idx
        r = (net.v[g] - net.v_rest[g]) / (net.v_th[g] - net.v_rest[g] if net.g_range is None else net.g_range)
        if net.g_r0 is not None:
            r = net.g_r0 + (1.0 - net.g_r0) * r
        r = np.clip(r, 0.0, 1.0)
        return r * net.g_k if net.g_k is not None else r

    def state(label: str) -> dict:
        r = release()
        out = {}
        for ty, idx in groups.items():
            ge, gi = net.i_syn[idx], net.g_i[idx]
            v_leak = net.v_leak[idx]
            ceil = (v_leak + ge * p.e_exc) / (1.0 + ge)   # medulla types get no external drive
            row = {"v": float(np.median(net.v[idx])), "g_e": float(np.median(ge)), "g_i": float(np.median(gi)),
                   "G": float(np.median(1 + ge + gi)), "v_leak": float(np.median(v_leak)),
                   "ceiling_no_inh": float(np.median(ceil)), "n": int(idx.size)}
            # graded split by presynaptic type: steady-state conductance = arrival / (1 - decay)
            se, si = {}, {}
            for W, decay, dst in ((net.W_graded, net.decay_s, se), (net.W_graded_i, net.decay_si, si)):
                if W is None:
                    continue
                g_by = (W[idx] @ sp.diags(r * net.graded_scale) @ onehot).toarray()   # (cells, pre types)
                g_by /= (1 - decay[idx])[:, None]
                for j in np.flatnonzero(g_by.any(axis=0)):
                    dst[ptypes[j] or "untyped"] = round(float(np.median(g_by[:, j])), 4)
            row["graded_g_e_by_pre"] = dict(sorted(se.items(), key=lambda kv: -kv[1])[:8])
            row["graded_g_i_by_pre"] = dict(sorted(si.items(), key=lambda kv: -kv[1])[:8])
            per_step = counts / (a.window_ms / DT)
            if getattr(net, "_any_std", False):
                per_step = per_step * net.x_res
            spl = {}
            for sign, decay in (("e", net.decay_s), ("i", net.decay_si if p.cond else net.decay_s)):
                g_by = (Wsp[sign][idx] @ sp.diags(per_step) @ onehot_all).toarray() / (1 - decay[idx])[:, None]
                med = np.median(g_by, axis=0)
                top = np.argsort(-g_by.mean(axis=0))[:8]
                spl[sign] = {(atypes[j] or "untyped"): [round(float(med[j]), 4), round(float(g_by[:, j].mean()), 4),
                             round(float(counts[acode == j].sum() / max((acode == j).sum(), 1) / (a.window_ms / 1000)), 1)]
                             for j in top if g_by[:, j].any()}
                tot_split = g_by.sum(axis=1) + sum(
                    (W[idx] @ (r * net.graded_scale)) / (1 - dcy[idx])
                    for W, dcy in ((net.W_graded, net.decay_s) if sign == "e" else (net.W_graded_i, net.decay_si),)
                    if W is not None)
                meas = ge if sign == "e" else gi
                row[f"split_residual_{sign}"] = round(float(np.median(meas - tot_split)), 4)
            row["spk_g_e_by_pre"] = spl["e"]   # type: [median, mean, presynaptic rate Hz]
            row["spk_g_i_by_pre"] = spl["i"]
            if ty in ("L1", "L2", "L3"):
                m = np.isin(g_idx, idx)
                row["release"] = float(np.median(r[m]))
            out[ty] = {k: (round(x, 3) if isinstance(x, float) else x) for k, x in row.items()}
            print(f"{label:5s} {ty:4s} v {row['v']:7.2f} g_e {row['g_e']:.3f} g_i {row['g_i']:.3f} "
                  f"G {row['G']:.2f} leak {row['v_leak']:.1f} ceiling(no inh) {row['ceiling_no_inh']:.2f} "
                  f"{'release ' + format(row['release'], '.3f') if 'release' in row else ''}", flush=True)
            print(f"       e by pre {row['graded_g_e_by_pre']}  i by pre {row['graded_g_i_by_pre']}", flush=True)
            print(f"       spiking e {row['spk_g_e_by_pre']}  i {row['spk_g_i_by_pre']}  residual e "
                  f"{row['split_residual_e']} i {row['split_residual_i']}", flush=True)
        return out

    drive = np.zeros(conn.n, np.float32)

    def run(ms: float, lum: float) -> None:
        drive[vis.rows] = vis.baseline_mv + vis.gain_mv * lum
        n_steps = int(round(ms / DT))
        start = n_steps - int(round(a.window_ms / DT))
        counts[:] = 0
        for s_ in range(n_steps):
            spiked = net.step(external_mv=drive)
            if s_ >= start and spiked.size:
                counts[spiked] += 1

    run(a.settle_ms, 0.0)
    dark = state("dark")
    run(a.light_ms, 1.0)
    light = state("light")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"set": a.set, "profile": a.profile, "settle_ms": a.settle_ms,
                                       "light_ms": a.light_ms, "e_exc": p.e_exc, "e_inh": p.e_inh,
                                       "dark": dark, "light": light, "wall_s": round(time.time() - t0)}, indent=1))


if __name__ == "__main__":
    main()
