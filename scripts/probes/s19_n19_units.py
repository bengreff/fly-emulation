"""N19 unit checks (s19; pre-registered DECISIONS 21 Oct 21:56). Isolated CNS, no body.

    map    receptor-map coverage; s per pool for the U2/U3/Dacks cell types (a = 1); no simulation
    u2     Mi4 response to L5 kicks, OA occupancy held at 1 against 0, for one receptor gain a
           (Strother 2018 Fig. 6F/H: dF/F ratio 2.66 at 0.2 mW/mm2, read from the figure, s19)
    dacks  held out: PN response to DM2/DL1/DM3 ORN kicks, 5-HT occupancy held at 1 against 0
           (Dacks 2009: about +15%; pass +5% to +30%)
    u1     one kick to every cell of a pool (oa or 5ht); the pool trace, kicked minus control
    u1h    held out: 50 kicks at 100 Hz to every OA cell; the OA pool trace
    off    receptor_map 0: spike hash of a short run (old-vs-new code identity)

Each copy is a deepcopy of one settled network; kicked and control copies share the random state, so
the difference is evoked activity only. Responses are spike counts in the stimulus window (graded cells:
their summed rate-equivalent). The dF/F-to-rate map is taken as proportional (inferred: GCaMP6s near-linear
at low rates); it is the main validity limit of U2.

    .venv/bin/python scripts/probes/s19_n19_units.py u2 --a 1.0 --out runs/s19/n19/u2_a1.0.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
U3_TYPES = ("Mi1", "Tm3", "Mi4", "Mi9", "T4a", "T4b", "T4c", "T4d")
DACKS_GLOMERULI = ("DM2", "DL1", "DM3")


def build(profile: str, receptor_map: int, a: float, seed: int = 1):
    reg = Registry(Policy.MINIMAL)
    if receptor_map:   # off: no overrides at all, so the same call runs on code without N19 (identity check)
        reg.overrides["neuromodulation:all|receptor_map"] = 1.0
        reg.overrides["neuromodulation:all|receptor_gain"] = float(a)
    prof = profiles.apply(reg, profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(seed))
    net.elec = el if len(el[0]) else None
    return reg, prof, conn, params, net


def cells(conn, pattern: str) -> np.ndarray:
    t = conn.neurons.type.fillna("")
    return np.flatnonzero(t.str.fullmatch(pattern).to_numpy())


def pn_cells(conn, glomeruli) -> np.ndarray:
    """Uniglomerular PNs of the listed glomeruli (type starts with the glomerulus, class ALPN)."""
    t = conn.neurons.type.fillna("")
    cls = conn.neurons["class"].fillna("") if "class" in conn.neurons else t * 0
    m = np.zeros(conn.n, bool)
    for g in glomeruli:
        m |= t.str.match(rf"^{g}_.*PN").to_numpy() | (t.str.startswith(g + "_").to_numpy()
                                                       & cls.str.contains("ALPN").to_numpy())
    return np.flatnonzero(m)


def response(net, kick_cells, read_cells, kick_mv, rate_hz, stim_ms, seed):
    """Spike count of read_cells during a Poisson kick train to kick_cells (plus graded rate-equivalent)."""
    rng = np.random.default_rng(seed)
    n_steps = int(stim_ms / DT)
    p = rate_hz * DT / 1000.0
    count = 0.0
    graded = net.params.graded is not None and np.asarray(net.params.graded)[read_cells].any()
    gsum = 0.0
    for _ in range(n_steps):
        kick = None
        if kick_cells is not None and kick_cells.size:
            hit = kick_cells[rng.random(kick_cells.size) < p]
            kick = (hit, kick_mv) if hit.size else None
        sp = net.step(kick=kick)
        count += np.isin(sp, read_cells).sum()
        if graded:
            gsum += float(np.clip((net.v[read_cells] - net.v_rest[read_cells])
                                  / (net.v_th[read_cells] - net.v_rest[read_cells]), 0, 1).sum())
    return count, gsum * DT / 1000.0


def bath(net0, memo, pool, occ, kick_cells, read_cells, kick_mv, rate_hz, stim_ms, seed):
    """Evoked response (stim minus no-stim, same random state) with one pool's occupancy held."""
    out = {}
    for name, kc in (("stim", kick_cells), ("ctrl", None)):
        net = copy.deepcopy(net0, dict(memo))
        net.hold_modulator(pool, occ)
        out[name] = response(net, kc, read_cells, kick_mv, rate_hz, stim_ms, seed)
        del net
    return {"spikes": out["stim"][0] - out["ctrl"][0], "graded": out["stim"][1] - out["ctrl"][1],
            "stim_spikes": out["stim"][0], "ctrl_spikes": out["ctrl"][0]}


def pool_trace(net0, memo, kick_cells, pulses, isi_ms, k, total_ms, every_ms=10.0):
    ctrl, kick = copy.deepcopy(net0, dict(memo)), copy.deepcopy(net0, dict(memo))
    n_steps, isi, ev = int(total_ms / DT), max(1, int(isi_ms / DT)), int(every_ms / DT)
    tr, n_sp = [], 0
    for s in range(n_steps):
        ctrl.step()
        on = s % isi == 0 and s // isi < pulses
        sp = kick.step(kick=(kick_cells, 40.0) if on else None)
        if on:
            n_sp += int(np.isin(sp, kick_cells).sum())
        if s % ev == 0:
            tr.append(float(kick.modmap["m"][k] - ctrl.modmap["m"][k]))
    return np.array(tr), n_sp


def fit_rise_decay(tr, every_ms, onset_ms=0.0):
    """Single-exponential fits, as a GRAB trace is fitted (inferred method): tau_on from y = A(1 - exp(-t/tau))
    on [onset, peak] (least squares over a tau grid, A free); tau_off from a log-linear fit of the decay from
    the peak to 10% of it. Also the impulse-kernel tau_on implied by the peak time given tau_off (secondary)."""
    t = np.arange(tr.size) * every_ms
    i_pk = int(np.argmax(tr))
    pk = float(tr[i_pk])
    i1 = i_pk
    while i1 < tr.size and tr[i1] > 0.1 * pk:
        i1 += 1
    toff = float(-1.0 / np.polyfit(t[i_pk:i1], np.log(np.maximum(tr[i_pk:i1], 1e-12)), 1)[0])
    i0 = int(np.searchsorted(t, onset_ms))
    tt, yy = t[i0:i_pk + 1] - t[i0], tr[i0:i_pk + 1]
    best = (np.inf, None)
    for tau in np.geomspace(5.0, 20000.0, 4000):
        b = 1.0 - np.exp(-tt / tau)
        amp = float(b @ yy / max(b @ b, 1e-30))
        err = float(((yy - amp * b) ** 2).sum())
        if err < best[0]:
            best = (err, tau)
    tpk = float(t[i_pk])
    lo, hi = 1e-3, toff * 0.999
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f = mid * toff / (toff - mid) * np.log(toff / mid)
        lo, hi = (mid, hi) if f < tpk else (lo, mid)
    return {"tau_on_ms": round(float(best[1]), 1), "tau_off_ms": round(toff, 1), "t_peak_ms": tpk,
            "peak": pk, "decay_fit_ms": [tpk, float(t[min(i1, tr.size - 1)])],
            "tau_on_kernel_ms": round(0.5 * (lo + hi), 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["map", "u2", "dacks", "u1", "u1h", "off"])
    ap.add_argument("--profile", default="m10f3")
    ap.add_argument("--a", type=float, default=1.0)
    ap.add_argument("--pool", default="oa")
    ap.add_argument("--rate-hz", type=float, default=100.0)
    ap.add_argument("--stim-ms", type=float, default=1000.0)
    ap.add_argument("--settle-ms", type=float, default=500.0)
    ap.add_argument("--total-ms", type=float, default=20000.0)
    ap.add_argument("--off-ms", type=float, default=300.0)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    t0 = time.time()
    out = {"mode": a.mode, "profile": a.profile, "a": a.a}
    if a.mode == "off":
        reg, prof, conn, params, net = build(a.profile, 0, 0.0)
        h = hashlib.sha256()
        n_sp = 0
        for _ in range(int(a.off_ms / DT)):
            sp = net.step()
            h.update(np.asarray(sp, np.int64).tobytes() + b"|")
            n_sp += sp.size
        out.update(spikes=n_sp, sha256=h.hexdigest(), modmap=getattr(net, "modmap", None) is not None)
    else:
        from flyemu import neuromod   # here, so `off` also runs on code without N19
        reg, prof, conn, params, net = build(a.profile, 1, a.a)
        mm = params.mod_map
        out["coverage"] = mm["coverage"]
        out["n_release"] = dict(zip(neuromod.POOLS, map(int, mm["n_release"])))
        kick_mv = float(prof["kick_mv"])
        out["kick_mv"] = kick_mv
        if a.mode == "map":
            t = conn.neurons.type.fillna("")
            rows = {}
            for ty in U3_TYPES + ("L5",):
                idx = cells(conn, ty)
                if idx.size:
                    rows[ty] = {"n": int(idx.size), "source": int(np.bincount(mm["source"][idx]).argmax()),
                                "net": [round(float(x), 4) for x in mm["net"][idx].mean(0)]}
            pn = pn_cells(conn, DACKS_GLOMERULI)
            rows["PN_DM2_DL1_DM3"] = {"n": int(pn.size), "types": sorted(set(t.iloc[pn])),
                                      "source": np.bincount(mm["source"][pn], minlength=3).tolist(),
                                      "net": [round(float(x), 4) for x in mm["net"][pn].mean(0)]}
            prior = mm["source"] == 0
            rows["prior"] = {"n": int(prior.sum()), "net": [round(float(x), 4) for x in mm["net"][prior].mean(0)]}
            out["types"] = rows
            out["graded"] = {ty: bool(np.asarray(params.graded)[cells(conn, ty)].any()) for ty in ("Mi4", "L5")}
            out["net_quantiles"] = {p_: [round(float(np.quantile(mm["net"][:, k], q)), 4)
                                         for q in (0.05, 0.5, 0.95)] for k, p_ in enumerate(neuromod.POOLS)}
        else:
            for _ in range(int(a.settle_ms / DT)):
                net.step()
            memo = {id(conn): conn, id(params): params}
            if a.mode == "u2":
                l5, mi4 = cells(conn, "L5"), cells(conn, "Mi4")
                r0 = bath(net, memo, "octopamine", 0.0, l5, mi4, kick_mv, a.rate_hz, a.stim_ms, 7)
                r1 = bath(net, memo, "octopamine", 1.0, l5, mi4, kick_mv, a.rate_hz, a.stim_ms, 7)
                out.update(n_l5=int(l5.size), n_mi4=int(mi4.size), u0=r0, u1=r1,
                           ratio_spikes=(r1["spikes"] / r0["spikes"]) if r0["spikes"] else None,
                           ratio_graded=(r1["graded"] / r0["graded"]) if r0["graded"] else None)
            elif a.mode == "dacks":
                t = conn.neurons.type.fillna("")
                orn = np.flatnonzero(t.isin([f"ORN_{g}" for g in DACKS_GLOMERULI]).to_numpy())
                pn = pn_cells(conn, DACKS_GLOMERULI)
                r0 = bath(net, memo, "serotonin", 0.0, orn, pn, kick_mv, a.rate_hz, a.stim_ms, 7)
                r1 = bath(net, memo, "serotonin", 1.0, orn, pn, kick_mv, a.rate_hz, a.stim_ms, 7)
                out.update(n_orn=int(orn.size), n_pn=int(pn.size), u0=r0, u1=r1,
                           change=(r1["spikes"] / r0["spikes"] - 1.0) if r0["spikes"] else None)
            else:
                pool = {"oa": "octopamine", "5ht": "serotonin"}[a.pool]
                k = neuromod.POOLS.index(pool)
                src = np.flatnonzero(mm["release"] == k)
                pulses, isi = (1, 10.0) if a.mode == "u1" else (50, 10.0)
                tr, n_sp = pool_trace(net, memo, src, pulses, isi, k, a.total_ms)
                fit = fit_rise_decay(tr, 10.0)
                out.update(pool=pool, n_cells=int(src.size), kicked_spikes=n_sp, fit=fit, trace=tr.tolist())
    out["wall_s"] = round(time.time() - t0, 1)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    print(json.dumps({k: v for k, v in out.items() if k != "trace"}, default=str)[:2000], flush=True)


if __name__ == "__main__":
    main()
