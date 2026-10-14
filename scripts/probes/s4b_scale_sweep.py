"""S4b: premotor-to-leg-MN synaptic scale, swept on the GPU batch (s13; DECISIONS 14 Oct, S4b pre-registration).

The bypass harness (bypass_s2_descending.py: m10f0, seed 12, brain off, senses off, DNg100 driven 300-1300 ms of
1500 ms) feeds nothing from the body back into the network, so the network alone reproduces its MN rasters. Each
batch member is one (scale, drive) pair. The scale multiplies the input gain of every leg MN, as the CPU switch
`cell_type:leg_motor|synaptic_input_scale` does (percell.py). Outputs per member are harness-format traces
(pool_rate, pool_names; read by bypass_moddepth.py), per-MN 1 ms counts, and the tibia-flexor class of each MN
(motor_forces.py convention: volume rank 1 fast, 2-4 intermediate, the rest slow) for the recruitment-order check.

    python scripts/probes/s4b_scale_sweep.py check      # CPU switch at scale 4 vs GPU member, 300 ms
    python scripts/probes/s4b_scale_sweep.py sweep      # scales x drives, writes runs/s13/bypass/s4b/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

KEY = "cell_type:leg_motor|synaptic_input_scale"
VNC_SUPER = ("ascending_neuron", "descending_neuron", "descending_neuron_tbc", "sensory_ascending",
             "sensory_ascending_tbc", "efferent_ascending")     # as bypass_s2_descending.py


def vnc_mask(conn) -> np.ndarray:
    sc = conn.neurons.superclass.fillna("").to_numpy().astype(str)
    return np.char.startswith(sc, "vnc_") | np.isin(sc, VNC_SUPER)


def stim_rows(conn, types: str) -> np.ndarray:
    typ = conn.neurons.type.fillna("").to_numpy().astype(str)
    return np.flatnonzero(np.isin(typ, types.split(",")))


def harness_pools(org):
    """Pools exactly as bypass_s2_descending.py builds them: (names, pool index of each row of nm.mn_index)."""
    h, nm = org.hill, org.nm
    pool_of_mn = np.full(len(nm.mn_index), -1)
    names = []
    for i, (j, s) in enumerate(zip(h.p.joint, h.p.direction)):
        names.append(f"{j} {s:+g}")
        pool_of_mn[h.mn_muscle == i] = len(names) - 1
    if h.coxa is not None:
        inv = {}
        for k in range(len(h.coxa.F0)):
            g = h.coxa_group[k]
            if g >= 0 and g not in inv:
                inv[g] = (h.coxa.leg[k], h.coxa.mn_type[k])
        for g, (leg, t) in sorted(inv.items()):
            names.append(f"{leg} coxa {t}")
            pool_of_mn[h.mn_group == g] = len(names) - 1
    return names, pool_of_mn


def tibia_class(conn, rows: np.ndarray) -> np.ndarray:
    """fast / intermediate / slow for tibia-flexor MNs among `rows` (motor_forces.py convention), '' otherwise."""
    from flyemu.neuromuscular import NEUROMERE_TO_LEG
    n = conn.neurons.reset_index(drop=True)
    m = n[(n.superclass == "vnc_motor") & n.somaNeuromere.isin(list(NEUROMERE_TO_LEG))].copy()
    m = m[m.type.fillna("").str.replace(r" MN$", "", regex=True).isin(["Ti flexor", "Acc. ti flexor"])]
    cls = np.full(conn.n, "", dtype=object)
    for _, g in m.groupby(["somaNeuromere", "somaSide"]):
        order = g.sort_values("size", ascending=False).index.to_numpy()
        cls[order[:1]] = "fast"
        cls[order[1:4]] = "intermediate"
        cls[order[4:]] = "slow"
    return cls[rows].astype(str)


def gains(net, leg: np.ndarray, scales) -> np.ndarray:
    base = np.broadcast_to(np.asarray(net.input_gain, np.float32), (net.conn.n,))
    return np.stack([np.where(leg, base * np.float32(s), base) for s in scales]).astype(np.float32)


def cmd_check(a) -> None:
    """CPU reference first: lif.Network with the CPU switch at scale s against a GPU member, same schedule."""
    from flyemu import lif, percell
    from flyemu.gpu.batched import BatchedNetwork
    from flyemu.gpu.equivalence import build_brain, compare, unpack
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    _, conn, p1, _ = build_brain({}, profile=a.profile, min_synapses=5)
    _, conn_s, ps, _ = build_brain({KEY: a.scale}, profile=a.profile, min_synapses=5)
    leg = percell.leg_motor_mask(conn)
    off = np.flatnonzero(~vnc_mask(conn))
    ext = np.zeros(conn.n, np.float32); ext[stim_rows(conn, a.type)] = a.drive_mv
    T0, T1 = int(round(a.rest_ms / a.dt)), int(round(a.drive_ms / a.dt))
    cpu_net = lif.Network(conn_s, ps, a.dt)
    cpu_net.silence(off)
    zero = np.zeros(conn.n, np.float32)
    t0 = time.time()
    cpu = [cpu_net.step(external_mv=zero if s < T0 else ext).copy() for s in range(T0 + T1)]
    cpu_s = time.time() - t0
    ref = lif.Network(conn, p1, a.dt)
    gain_match = bool(np.array_equal(gains(ref, leg, [a.scale])[0], np.asarray(cpu_net.input_gain, np.float32)))
    g = BatchedNetwork(ref, B=1, member={"input_gain": gains(ref, leg, [a.scale])})
    g.silence(off)
    r0 = g.run(T0, external_mv=None, record="packed")["raster"]
    r1 = g.run(T1, external_mv=ext, record="packed")["raster"]
    res = compare(cpu, unpack(np.concatenate([r0, r1]), conn.n, 0), conn.n, a.dt)
    lm = np.flatnonzero(leg)
    gl = unpack(np.concatenate([r0, r1]), conn.n, 0)
    res.update(scale=a.scale, drive_mv=a.drive_mv, cpu_wall_s=round(cpu_s, 1), input_gain_identical=gain_match,
               leg_mn_spikes_cpu=int(sum(np.isin(x, lm).sum() for x in cpu)),
               leg_mn_spikes_gpu=int(sum(np.isin(x, lm).sum() for x in gl)))
    (out / "gpu_check.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, default=str), flush=True)


def cmd_sweep(a) -> None:
    from flyemu import percell
    from flyemu.gpu.batched import BatchedNetwork
    from flyemu.organism import Organism
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides={}, seed=a.seed)
    conn, net, dt = org.conn, org.net, org.timestep_ms
    names, pool_of_mn = harness_pools(org)
    rows = np.asarray(org.nm.mn_index)
    cls = tibia_class(conn, rows)
    nrow = conn.neurons.reset_index(drop=True)
    som = nrow.somaNeuromere.fillna("").to_numpy().astype(str)[rows]
    side = nrow.somaSide.fillna("").to_numpy().astype(str)[rows]
    leg = percell.leg_motor_mask(conn)
    vnc = vnc_mask(conn)
    stim = stim_rows(conn, a.type)
    steps, per = int(round(a.ms / dt)), int(round(1.0 / dt))
    on_steps = np.array([a.on_ms <= s * dt < a.off_ms for s in range(steps)])    # the harness's own test
    s_on, s_off = int(np.argmax(on_steps)), int(steps - np.argmax(on_steps[::-1]))
    assert on_steps[s_on:s_off].all() and s_on % a.seg == 0 and s_off % a.seg == 0 and steps % a.seg == 0
    scales = [float(x) for x in a.scales.split(",")]
    drives = [float(x) for x in a.drives.split(",")]
    members = [(s, d) for s in scales for d in drives]
    meta = dict(diagnostic="forced drive (DN input set by hand); not emergent walking; no body (it does not feed "
                "back in the harness)", profile=a.profile, seed=a.seed, type=a.type, on_ms=a.on_ms, off_ms=a.off_ms,
                ms=a.ms, key=KEY, n_leg_mn=int(leg.sum()), n_mapped_mn=int((pool_of_mn >= 0).sum()),
                n_stim=int(stim.size), steps_on=[s_on, s_off], members=members)
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    vidx = np.flatnonzero(vnc)
    for c0 in range(0, len(members), a.chunk):
        mem = members[c0:c0 + a.chunk]
        B = len(mem)
        t0 = time.time()
        g = BatchedNetwork(net, B=B, member={"input_gain": gains(net, leg, [s for s, _ in mem])})
        g.silence(np.flatnonzero(~vnc))
        ext = np.zeros((B, conn.n), np.float32)
        for b, (_, d) in enumerate(mem):
            ext[b, stim] = d
        mn = np.zeros((steps // per, B, rows.size), np.uint8)
        tot = np.zeros((steps, B), np.int32)
        win_counts, prev = [], np.zeros((B, conn.n), np.int64)
        for k0 in range(0, steps, a.seg):
            r = g.run(a.seg, external_mv=ext if s_on <= k0 < s_off else None, record=rows)
            mn[k0 // per:(k0 + a.seg) // per] = r["raster"].reshape(a.seg // per, per, B, rows.size).sum(1)
            tot[k0:k0 + a.seg] = r["n_spikes"]
            if k0 + a.seg in (s_on, s_off, steps):
                c = g.spike_counts().astype(np.int64)
                win_counts.append((c - prev)[:, vidx].astype(np.int32)); prev = c
        for b, (s, d) in enumerate(mem):
            pr = np.zeros((steps // per, len(names)), np.int32)
            for p in range(len(names)):
                pr[:, p] = mn[:, b, pool_of_mn == p].sum(1)
            np.savez_compressed(out / f"s4b_s{s:g}_{d:g}mv_traces.npz", pool_rate=pr, pool_names=np.array(names),
                                mn_counts=mn[:, b], mn_rows=rows, mn_pool=pool_of_mn, mn_cls=cls, mn_neuromere=som,
                                mn_side=side, mn_bodyId=nrow.bodyId.to_numpy()[rows], total_spikes=tot[:, b],
                                vnc_rows=vidx, window_counts=np.stack([w[b] for w in win_counts]),
                                windows_ms=np.array([[0, a.on_ms], [a.on_ms, a.off_ms], [a.off_ms, a.ms]]),
                                scale=s, drive_mv=d)
        print(f"chunk {c0 // a.chunk}: {B} members, {time.time() - t0:.0f} s", flush=True)
        del g


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "sweep"):
        s = sub.add_parser(name)
        s.add_argument("--profile", default="m10f0")
        s.add_argument("--type", default="DNg100")
        s.add_argument("--out", default=str(REPO / "runs" / "s13" / "bypass" / "s4b"))
    c = sub.choices["check"]
    c.add_argument("--scale", type=float, default=4.0)
    c.add_argument("--drive-mv", type=float, default=25.0)
    c.add_argument("--rest-ms", type=float, default=100.0)
    c.add_argument("--drive-ms", type=float, default=200.0)
    c.add_argument("--dt", type=float, default=0.1)
    w = sub.choices["sweep"]
    w.add_argument("--seed", type=int, default=12)
    w.add_argument("--scales", default="1,1.5,2,3,4,6,8,12,16,25")
    w.add_argument("--drives", default="15,25,40")
    w.add_argument("--ms", type=float, default=1500.0)
    w.add_argument("--on-ms", type=float, default=300.0)
    w.add_argument("--off-ms", type=float, default=1300.0)
    w.add_argument("--seg", type=int, default=1000, help="steps per GPU call (drive changes on segment edges)")
    w.add_argument("--chunk", type=int, default=30, help="members per batch")
    a = ap.parse_args()
    {"check": cmd_check, "sweep": cmd_sweep}[a.cmd](a)


if __name__ == "__main__":
    main()
