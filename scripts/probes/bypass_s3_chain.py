"""Bypass assay S3 helper: the Pugliese 2025 minimal oscillator, cell by cell, brain off (s13, 13 Oct).

DIAGNOSTIC, forced drive. Network only (no body, no senses): the brain's output is removed as in
bypass_s2_descending.py, DNg100 (or --type) gets a constant drive during [--on-ms, --off-ms), and the membrane
potential and spikes of the oscillator cells are recorded in every leg neuromere:
  E1 IN17A001, E2 INXXX466 (MANC IN15A001), I1 IN16B036 (MANC IN16B007; mapping by mancBodyid, s13 audit),
  and the GABAergic cells that also close or block the loop in the male CNS: IN19A007, IN19A004, IN19A002.
Also prints the model's own weights on the loop edges (mV of LIF weight, after every profile mechanism), so a
gap between connectome counts and model weights shows up here and not in a hand calculation.

    uv run python scripts/probes/bypass_s3_chain.py --drive-mv 25 [--set mode:n1_p_graded_vnc_local|graded=1]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyemu.organism import Organism  # noqa: E402
from assay_pathways import rhythm_excess  # noqa: E402
from bypass_s2_descending import VNC_SUPER  # noqa: E402

ROLE = {"IN17A001": "E1", "INXXX466": "E2", "IN16B036": "I1", "IN19A007": "A007", "IN19A004": "A004",
        "IN19A002": "A002"}
EDGES = (("E1", "E2"), ("E2", "I1"), ("E1", "I1"), ("I1", "E1"), ("I1", "E2"), ("E2", "A007"), ("E1", "A007"),
         ("A007", "E1"), ("A002", "I1"), ("A004", "I1"), ("E1", "A004"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--type", default="DNg100")
    ap.add_argument("--drive-mv", type=float, default=25.0)
    ap.add_argument("--ms", type=float, default=900.0)
    ap.add_argument("--on-ms", type=float, default=100.0)
    ap.add_argument("--off-ms", type=float, default=900.0)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=str(REPO / "runs" / "s13" / "bypass" / "s3"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tag = a.tag or f"chain_{a.type}_{a.drive_mv:g}mv"
    t0 = time.time()
    ov = {k: float(v) for k, v in (x.rsplit("=", 1) for x in a.set)}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides=ov, seed=a.seed, with_camera=False)
    net, conn, dt = org.net, org.conn, org.timestep_ms
    n = conn.neurons
    sc = n.superclass.fillna("").to_numpy().astype(str)
    typ = n.type.fillna("").to_numpy().astype(str)
    vnc = np.char.startswith(sc, "vnc_") | np.isin(sc, VNC_SUPER)
    net.silence(np.flatnonzero(~vnc))
    stim = np.flatnonzero(np.isin(typ, a.type.split(",")))
    seg = (n["somaNeuromere"].fillna("") if "somaNeuromere" in n else n.get("soma_neuromere", "")).astype(str)
    side = n["somaSide"].fillna("").astype(str)
    cells = np.flatnonzero(np.isin(typ, list(ROLE)))
    label = [f"{ROLE[typ[i]]} {seg.iloc[i]}{side.iloc[i]}" for i in cells]
    graded = net.graded[cells]
    # model weights on the loop edges, per neuromere and side (pre row -> post column, CSR by pre)
    pos = {i: k for k, i in enumerate(cells)}
    wtab = {}
    for i in cells:
        lo, hi = conn.indptr[i], conn.indptr[i + 1]
        for e in range(lo, hi):
            j = conn.indices[e]
            if j in pos and label[pos[j]].split()[1] == label[pos[i]].split()[1]:
                key = f"{label[pos[i]].split()[0]}>{label[pos[j]].split()[0]}"
                wtab.setdefault(label[pos[i]].split()[1], {})[key] = round(float(net.w[e]), 2)
    steps = int(round(a.ms / dt)); per = int(round(1.0 / dt)); nb = steps // per
    V = np.zeros((nb, cells.size), np.float32)
    S = np.zeros((nb, cells.size), np.uint8)
    stim_c = np.zeros(nb)
    zero = np.zeros(conn.n, np.float32)
    on = zero.copy(); on[stim] = a.drive_mv
    row = np.full(conn.n, -1); row[cells] = np.arange(cells.size)
    is_stim = np.zeros(conn.n, bool); is_stim[stim] = True
    vnc_c = np.zeros(conn.n, np.int32)
    w0, w1 = int(a.on_ms) + 100, int(a.off_ms)
    for s in range(steps):
        t = s * dt
        sp = net.step(external_mv=on if a.on_ms <= t < a.off_ms else zero)
        k = s // per
        if sp.size:
            r = row[sp]; r = r[r >= 0]; S[k, r] += 1
            stim_c[k] += is_stim[sp].sum()
            if w0 <= t < w1:
                vnc_c[sp] += 1
        V[k] += net.v[cells] / per
    drv = slice(w0, w1)
    sec = (w1 - w0) / 1000.0
    vrest = net.v_rest[cells]; vth = net.v_th[cells]
    rows = []
    for c in range(cells.size):
        tr = S[drv, c] > 0
        e, _, f = rhythm_excess(tr, 1.0) if tr.sum() >= 5 else (None, None, None)
        vm = V[drv, c]
        rows.append(dict(cell=label[c], bodyId=int(n.bodyId.iloc[cells[c]]) if "bodyId" in n else None,
                         graded=bool(graded[c]), rate_hz=round(float(S[drv, c].sum() / sec), 1),
                         v_mean=round(float(vm.mean()), 2), v_max=round(float(vm.max()), 2),
                         v_sd=round(float(vm.std()), 2), v_rest=round(float(vrest[c]), 2), v_th=round(float(vth[c]), 2),
                         rhythm_excess=None if e is None else round(float(e), 3),
                         rhythm_hz=None if f is None or not np.isfinite(f) else round(float(f), 1)))
    rows.sort(key=lambda r: (r["cell"].split()[1], r["cell"]))
    act_vnc = int((vnc_c[vnc] > 0).sum())
    res = dict(diagnostic="forced drive (DN input set by hand); network only, brain off, senses off",
               profile=a.profile, seed=a.seed, type=a.type, drive_mv=a.drive_mv, overrides=ov,
               stim_hz=round(float(stim_c[drv].sum() / max(stim.size, 1) / sec), 1), vnc_cells_active=act_vnc,
               n_graded_vnc=int(net.graded[vnc].sum()), cells=rows, model_weights_mv=wtab, wall_s=round(time.time() - t0))
    (out / f"{tag}.json").write_text(json.dumps(res, indent=1))
    np.savez_compressed(out / f"{tag}_traces.npz", V=V, S=S, labels=np.array(label))
    print(json.dumps({k: v for k, v in res.items() if k not in ("cells", "model_weights_mv")}, indent=1))
    for r in rows:
        print(f"{r['cell']:10s} graded={int(r['graded'])} {r['rate_hz']:6.1f} Hz  V {r['v_mean']:7.2f} max {r['v_max']:7.2f} "
              f"sd {r['v_sd']:5.2f}  rest {r['v_rest']:6.1f} th {r['v_th']:6.1f}  rx {r['rhythm_excess']} @ {r['rhythm_hz']}")
    for sg, d in sorted(wtab.items()):
        print(sg, {k: d.get(k) for k in (f"{x}>{y}" for x, y in EDGES)})


if __name__ == "__main__":
    main()
