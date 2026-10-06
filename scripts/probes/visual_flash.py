"""Open-loop responses of the visual pathway to full-field light flashes from darkness (diagnostic, s12 vision blank).

Reproduces the stimulus of Behnia et al. 2014 Nature 512:427, Fig. 2 (whole-cell, Mi1, Tm1, Tm2, Tm3): the
whole field steps from dark (intensity 0) to full intensity (1) and back, for 200 ms and for 1 s (the paper
also uses 4 x 500 ms), through the eye's own drive rule (vision.Vision: dark_drive + luminance_gain x luminance) with
no body. Every photoreceptor with a derived direction is driven; a full field puts every column in phase, so
type means do not cancel. Per type it reports the dark baseline, the peak depolarisation and
hyperpolarisation from that baseline during each flash (ON window: flash; OFF window: 500 ms after it), the
same for the 90th-percentile cell (cells without photoreceptor input dilute the mean, F-VISION-4), and the
type-mean trace for plotting.

    uv run python scripts/probes/visual_flash.py --profile m9c --set cell_type:all|mode_from_recordings=1 \
        --out runs/s12/vision/flash_R.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles, vision  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
REPO = Path(__file__).resolve().parents[2]
TYPES = ["R1-R6", "L1", "L2", "L3", "L4", "L5", "C2", "C3", "Mi1", "Tm3", "Mi4", "Mi9", "Tm1", "Tm2", "Tm4",
         "Tm9", "CT1", "T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d", "Am1", "HSN", "HSE", "HSS",
         "H2", "VS"]
# (onset ms, duration ms) after the dark settle; two of Behnia et al. 2014 Fig. 2's blocks, 2 s dark between
FLASHES = [(500, 200), (2700, 1000)]
# per-cell peak deflections saved for these (scoring on cells whose cartridge has photoreceptor input)
CELL_TYPES = ["R1-R6", "L1", "L2", "Mi1", "Tm3", "Tm1", "Tm2", "T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d"]
TAIL_MS = 1500.0
BOUNDS = [-90.0, 20.0]          # mV, whole network, sampled every 1 ms during the recorded part (as vm_extremes.py)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--settle-ms", type=float, default=1000.0, help="dark before the first flash")
    ap.add_argument("--sample-hz", type=float, default=100.0, help="eye update rate, as the organism")
    ap.add_argument("--record-ms", type=float, default=5.0, help="trace sampling interval")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--flash", action="append", default=[],
                    help="onset_ms:dur_ms after the settle, repeatable (default: two Behnia blocks)")
    ap.add_argument("--tail-ms", type=float, default=TAIL_MS, help="dark after the last flash")
    ap.add_argument("--intensity", type=float, default=1.0,
                    help="flash intensity, 0-1 (below 1: small-signal gain, as Juusola et al. 1995)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    t0 = time.time()

    reg = Registry(Policy.MINIMAL)
    for s in a.set:
        k, v = s.split("=")
        reg.overrides[k] = float(v)
    profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    vis = vision.build(reg, conn, timestep_ms=DT, sample_hz=a.sample_hz)
    rt = pd.read_csv(REPO / "data/derived/retinotopy.csv").set_index("bodyId")
    bid = conn.neurons.bodyId.to_numpy()[vis.rows]
    has = np.isfinite(rt.az_pred.reindex(bid).to_numpy()) & np.isfinite(rt.el_pred.reindex(bid).to_numpy())
    rows = vis.rows[has]
    print(f"photoreceptors driven {has.sum()} of {len(vis.rows)} (with a derived direction)", flush=True)

    t = conn.neurons.type.fillna("").to_numpy()
    groups = {ty: np.flatnonzero(np.char.startswith(t.astype(str), ty) if ty == "VS" else t == ty)
              for ty in TYPES}
    groups = {k: v for k, v in groups.items() if v.size}
    graded = np.asarray(params.graded, bool)
    sel = np.concatenate(list(groups.values()))
    off = dict(zip(groups, np.cumsum([0] + [v.size for v in groups.values()])[:-1]))
    every = max(1, int(round(1000.0 / a.sample_hz / DT)))
    rec = max(1, int(round(a.record_ms / DT)))

    net = lif.Network(conn, params, DT, rng=np.random.default_rng(a.seed))
    net.elec = el if len(el[0]) else None
    drive = np.zeros(conn.n, np.float32)
    vmin = np.full(conn.n, np.inf, np.float32)
    vmax = np.full(conn.n, -np.inf, np.float32)

    def run(ms: float, lum_at, record: bool):
        n_steps = int(round(ms / DT))
        trace = np.zeros(((n_steps + rec - 1) // rec, sel.size), np.float32) if record else None   # per cell
        spikes = np.zeros(conn.n, np.int64)
        for s in range(n_steps):
            if record and s % 10 == 0:                                # whole-network bounds, every 1 ms
                np.minimum(vmin, net.v, out=vmin)
                np.maximum(vmax, net.v, out=vmax)
            if s % every == 0:
                drive[rows] = vis.baseline_mv + vis.gain_mv * lum_at(s * DT)
            if record and s % rec == 0:
                trace[s // rec] = net.v[sel]
            sp = net.step(external_mv=drive)
            np.add.at(spikes, sp, 1)
        return trace, spikes

    flashes = [tuple(float(x) for x in f.split(":")) for f in a.flash] or FLASHES
    run(a.settle_ms, lambda _t: 0.0, False)
    total = flashes[-1][0] + flashes[-1][1] + a.tail_ms

    def lum(t_ms: float) -> float:
        return a.intensity if any(on <= t_ms < on + d for on, d in flashes) else 0.0

    trace, spikes = run(total, lum, True)
    tt = np.arange(trace.shape[0]) * rec * DT                     # ms after the settle
    # dark baseline: the 200 ms before each flash, per cell
    res, traces, cells = {}, {}, {}
    for ty, idx in groups.items():
        cols = slice(off[ty], off[ty] + idx.size)
        x = trace[:, cols]
        per = []
        for on, d in flashes:
            b = x[(tt >= on - 200) & (tt < on)].mean(axis=0)
            w_on = (tt >= on) & (tt < on + d)
            w_off = (tt >= on + d) & (tt < on + d + 500)
            dx_on, dx_off = x[w_on] - b, x[w_off] - b
            m_on, m_off = dx_on.mean(axis=1), dx_off.mean(axis=1)              # type-mean deflection
            per.append({"onset_ms": on, "dur_ms": d, "base_mv": round(float(b.mean()), 3),
                        "on_max": round(float(m_on.max()), 3), "on_min": round(float(m_on.min()), 3),
                        "off_max": round(float(m_off.max()), 3), "off_min": round(float(m_off.min()), 3),
                        "on_max_p90": round(float(np.percentile(dx_on.max(axis=0), 90)), 3),
                        "off_max_p90": round(float(np.percentile(dx_off.max(axis=0), 90)), 3),
                        "on_min_p10": round(float(np.percentile(dx_on.min(axis=0), 10)), 3)})
        if ty in CELL_TYPES:   # last flash, per cell
            cells[ty] = {"bodyId": conn.neurons.bodyId.to_numpy()[idx].tolist(),
                         "on_max": np.round(dx_on.max(axis=0), 3).tolist(),
                         "on_min": np.round(dx_on.min(axis=0), 3).tolist(),
                         "off_max": np.round(dx_off.max(axis=0), 3).tolist(),
                         "off_min": np.round(dx_off.min(axis=0), 3).tolist()}
        res[ty] = {"flashes": per, "n": int(idx.size), "graded": bool(graded[idx].all()),
                   "rate_hz": round(float(spikes[idx].sum() / idx.size / (total / 1000.0)), 3)}
        traces[ty] = np.round(x.mean(axis=1), 3).tolist()
        f = per[-1]
        print(f"{ty:6s} base {f['base_mv']:7.2f}  1 s flash: ON {f['on_min']:+6.2f}/{f['on_max']:+6.2f}  "
              f"OFF {f['off_min']:+6.2f}/{f['off_max']:+6.2f}  p90 ON {f['on_max_p90']:+6.2f} "
              f"OFF {f['off_max_p90']:+6.2f}  {res[ty]['rate_hz']:.1f} Hz", flush=True)
    out_cells = (vmin < BOUNDS[0]) | (vmax > BOUNDS[1])
    tt_all = conn.neurons.type.fillna("untyped").to_numpy()[out_cells]
    bounds = {"range_mv": BOUNDS, "n_outside": int(out_cells.sum()), "n": int(conn.n),
              "types": pd.Series(tt_all).value_counts().head(20).to_dict(),
              "vmin": round(float(vmin.min()), 2), "vmax": round(float(vmax.max()), 2)}
    print(f"cells outside {BOUNDS} mV during the flashes: {bounds['n_outside']} of {conn.n}; "
          f"extremes {bounds['vmin']} / {bounds['vmax']}; {bounds['types']}", flush=True)
    meta = {"profile": a.profile, "set": a.set, "flashes_ms": flashes, "settle_ms": a.settle_ms,
            "sample_hz": a.sample_hz, "record_ms": a.record_ms, "intensity": a.intensity, "seed": a.seed, "gain_mv": vis.gain_mv, "dark_mv": vis.baseline_mv,
            "driven": int(has.sum()), "wall_s": round(time.time() - t0), "bounds": bounds}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps({"meta": meta, "res": res, "t_ms": tt.tolist(), "trace": traces,
                                              "cells": cells}))


if __name__ == "__main__":
    main()
