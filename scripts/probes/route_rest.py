"""Resting excitability of the leg sugar route cells, one unconnected cell at a time (diagnostic).

Built for the route bracket (DECISIONS 6 October 00:1x): under m9c the route cells sit about 7 mV below
threshold with no noise, while recorded central cells rest near threshold (MBON-alpha3 fires at 12.1 Hz
at rest, Hafez 2023; LH output, LH local and projection neurons at 0.1, 1 and 1.4 Hz, Frechter 2019).
For every cell of the route types this takes the cell's own constants and rung-1 channels from the model
build, sweeps a constant drive (mV, leak units, the same units as `spontaneous_drive`), and reports the
rheobase (lowest drive that fires in 1 s) and the drive for each target rate. With --extra-dir it writes
one FLYEMU_EXTRA_PARAMS file per arm, a `spontaneous_drive` row per cell (labelled guessed, diagnostic).

    uv run python scripts/probes/route_rest.py --profile m9c --out runs/s12/rest/route_rest_m9c.json \
        --extra-dir runs/s12/rest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import channels, connectome, lif, profiles  # noqa: E402
from flyemu.connectome import Connectome  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
# The paper's route (Tastekin et al. Fig. 9B: AN01B004 -> Bract I/II -> Roundup, side branch S&S), the
# co-exciting GNG cluster found in the profile ladder (DECISIONS 23:05), and the feedforward inhibitors.
ROUTE = ["AN01B004", "DNge174", "DNge173", "GNG108", "GNG159",
         "AN17A002", "GNG588", "GNG578", "GNG468", "AN05B106", "GNG421", "GNG318", "GNG167", "GNG143",
         "DNge059", "GNG093", "GNG250"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--types", default=",".join(ROUTE))
    ap.add_argument("--drives", default="0:16:0.05", help="start:stop:step (mV)")
    ap.add_argument("--duration-ms", type=float, default=1000.0)
    ap.add_argument("--settle-ms", type=float, default=300.0)
    ap.add_argument("--below-mv", type=float, default=1.0, help="'near' arm: this far below rheobase")
    ap.add_argument("--targets-hz", default="4,12", help="tonic arms: lowest drive reaching each rate")
    ap.add_argument("--out", default="")
    ap.add_argument("--extra-dir", default="")
    a = ap.parse_args()

    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, a.profile)
    full = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    p = lif.default_params(reg, full, timestep_ms=DT)
    types = a.types.split(",")
    idx = np.flatnonzero(full.neurons.type.isin(types).to_numpy())
    cells = full.neurons.iloc[idx][["bodyId", "type"]].reset_index(drop=True)
    b = lambda x: np.broadcast_to(np.asarray(x, np.float32), (full.n,))[idx]
    const = {k: b(getattr(p, k)) for k in ("tau_m", "v_rest", "v_th", "v_reset", "t_ref", "spont_mv",
                                           "adapt_mv", "tau_adapt")}
    assert not np.any(const["spont_mv"]), "route cells already carry a tonic drive"
    lo, hi, st = (float(x) for x in a.drives.split(":"))
    drives = np.arange(lo, hi + st / 2, st, dtype=np.float32)
    nc, nd = len(cells), len(drives)
    rep = lambda x: np.repeat(np.asarray(x, np.float32), nd)
    nrn = pd.DataFrame({"bodyId": np.repeat(cells.bodyId.to_numpy(), nd), "type": np.repeat(cells.type.to_numpy(), nd),
                        "predictedNt": "acetylcholine", "superclass": "x", "class": "x"})
    n = nc * nd
    conn = Connectome(nrn, np.zeros(n + 1, np.int64), np.zeros(0, np.int32), np.zeros(0, np.float32),
                      np.zeros(n, np.float32), np.zeros(0, np.float32))
    ich = channels.from_registry(reg, conn, timestep_ms=DT)
    q = lif.LIFParams(rep(const["tau_m"]), rep(const["v_rest"]), rep(const["v_th"]), rep(const["v_reset"]),
                      rep(const["t_ref"]), 5.0, np.ones(n, np.int64), 0.0, True, graded=np.zeros(n, bool),
                      intrinsic=ich, adapt_mv=rep(const["adapt_mv"]), tau_adapt=rep(const["tau_adapt"]))
    net = lif.Network(conn, q, DT)
    ext = np.tile(drives, nc)
    cnt = np.zeros(n)
    for s in range(int((a.settle_ms + a.duration_ms) / DT)):
        sp = net.step(external_mv=ext)
        if sp.size and s * DT >= a.settle_ms:
            cnt[sp] += 1
    hz = (cnt / (a.duration_ms / 1000.0)).reshape(nc, nd)
    targets = [float(x) for x in a.targets_hz.split(",")]
    rows = []
    for k in range(nc):
        on = np.flatnonzero(hz[k] > 0)
        rheo = float(drives[on[0]]) if len(on) else None
        r = {"bodyId": int(cells.bodyId[k]), "type": cells.type[k],
             "tau_m": float(const["tau_m"][k]), "v_rest": float(const["v_rest"][k]),
             "gap_mv": float(const["v_th"][k] - const["v_rest"][k]), "t_ref": float(const["t_ref"][k]),
             "channel_source": int(ich.source[k * nd]) if ich is not None and ich.source is not None else None,
             "rheobase_mv": rheo, "hz_at_rheobase": float(hz[k, on[0]]) if len(on) else None}
        for t in targets:
            j = np.flatnonzero(hz[k] >= t)
            r[f"drive_for_{t:g}hz"] = float(drives[j[0]]) if len(j) else None
            r[f"hz_at_drive_for_{t:g}hz"] = float(hz[k, j[0]]) if len(j) else None
        rows.append(r)
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(df.drop(columns=["bodyId"]).groupby("type", sort=False).agg(["min", "max"]).round(2).to_string())
    res = {"profile": a.profile, "drives": [float(drives[0]), float(drives[-1]), st],
           "below_mv": a.below_mv, "targets_hz": targets, "cells": rows}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))
    if a.extra_dir:
        d = Path(a.extra_dir)
        d.mkdir(parents=True, exist_ok=True)
        arms = {"near": ("rheobase_mv", -a.below_mv, f"{a.below_mv:g} mV below the cell's own rheobase "
                         "(silent in isolation; stands for central cells resting at 0.1-1.4 Hz, Frechter 2019)")}
        for t in targets:
            arms[f"tonic{t:g}"] = (f"drive_for_{t:g}hz", 0.0, f"lowest drive giving >= {t:g} Hz in isolation "
                                   "(measured central resting rates up to 12.1 Hz, MBON-alpha3, Hafez 2023)")
        for arm, (col, off, why) in arms.items():
            ok = df[col].notna()
            out = pd.DataFrame({"type": "bodyId:" + df.bodyId[ok].astype(str), "param": "spontaneous_drive",
                                "value": (df[col][ok] + off).clip(lower=0.0).round(3), "units": "mV",
                                "basis": "guessed", "source": "s12 route bracket (diagnostic, not adopted)",
                                "justification": [f"{t} route cell; {why}" for t in df.type[ok]]})
            out.to_csv(d / f"route_{arm}.csv", index=False)
            print(f"{arm}: {ok.sum()} of {len(df)} cells -> {d / f'route_{arm}.csv'}")


if __name__ == "__main__":
    main()
