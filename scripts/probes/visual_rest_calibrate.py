"""Fit per-type leak reversals so that recorded resting potentials hold in the network, eye dark (s12 vision).

F-VISION-6: a recorded resting potential is the cell's potential in the network, tonic synaptic input
included, not its leak reversal. With `cell_type:all|leak_from_network_rest` 1, a `v_leak_shift_fit` row
moves a type's leak reversal alone. This script finds one shift per type (Mi1, Tm1, Tm2, Tm3 by default:
the types with a recorded rest, Behnia et al. 2014) such that the type's mean potential in darkness, after
the settle, equals its rest (`v_rest`, which carries the recorded value). Each iteration settles the dark
network and moves each shift by the residual times the type's mean total conductance (leak = 1), the
inverse of the steady-state sensitivity in conductance mode. Leak reversals are clipped to [--lo, --hi].

Optionally it first writes `input_gain` rows (one shared value, fitted elsewhere) for the same types, so
the calibration is done at that synaptic conductance. Output: candidate rows for `FLYEMU_EXTRA_PARAMS`
(basis derived: fitted in the network), and a JSON report.

    uv run python scripts/probes/visual_rest_calibrate.py --profile m9c --set ... \
        --set 'cell_type:all|rest_from_recordings=1' --set 'cell_type:all|leak_from_network_rest=1' \
        --input-gain 3 --out runs/s12/vision/rest_S3.csv
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles, vision  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
HEADER = "type,param,value,units,basis,source,justification\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--types", default="Mi1,Tm1,Tm2,Tm3")
    ap.add_argument("--input-gain", type=float, default=0.0, help="input_gain rows for --types (0: none)")
    ap.add_argument("--first-ms", type=float, default=500.0)
    ap.add_argument("--iter-ms", type=float, default=300.0)
    ap.add_argument("--iters", type=int, default=6)
    ap.add_argument("--tol-mv", type=float, default=0.2)
    ap.add_argument("--lo", type=float, default=-85.0, help="lowest leak reversal, mV")
    ap.add_argument("--hi", type=float, default=-25.0, help="highest leak reversal, mV")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    types = a.types.split(",")
    gain_rows = ""
    if a.input_gain:
        gain_rows = "".join(
            f"{ty},input_gain,{a.input_gain},dimensionless,derived,fitted to Mi1 ON amplitude "
            f"(DECISIONS 6 Oct operating-point block),\"candidate: synaptic conductance relative to leak, "
            f"shared by {'/'.join(types)}\"\n" for ty in types)
        tmp = Path(tempfile.mkstemp(suffix=".csv")[1])
        tmp.write_text(HEADER + gain_rows)
        os.environ["FLYEMU_EXTRA_PARAMS"] = str(tmp)

    reg = Registry(Policy.MINIMAL)
    for s in a.set:
        k, v = s.split("=")
        reg.overrides[k] = float(v)
    if not reg.overrides.get("cell_type:all|leak_from_network_rest"):
        raise SystemExit("needs --set 'cell_type:all|leak_from_network_rest=1'")
    # the targets are the recorded rests (v_rest_shift_rec rows); without this switch they are the global
    # -52 mV, which m9c uses for every type (correction to F-VISION-6, 6 Oct)
    if not reg.overrides.get("cell_type:all|rest_from_recordings"):
        raise SystemExit("needs --set 'cell_type:all|rest_from_recordings=1' (targets are the recorded rests)")
    profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    vis = vision.build(reg, conn, timestep_ms=DT, sample_hz=100.0)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(1))
    net.elec = el if len(el[0]) else None
    assert net.v_leak is not net.v_rest
    drive = np.zeros(conn.n, np.float32)
    drive[vis.rows] = vis.baseline_mv                      # dark eye
    t = conn.neurons.type.fillna("").to_numpy()
    groups = {ty: np.flatnonzero(t == ty) for ty in types}
    shift = {ty: 0.0 for ty in types}

    def settle(ms: float) -> tuple[dict, dict]:
        n_steps = int(round(ms / DT))
        acc = {ty: 0.0 for ty in types}
        k = 0
        for s in range(n_steps):
            net.step(external_mv=drive)
            if s >= n_steps - int(100 / DT) and s % 10 == 0:
                for ty, idx in groups.items():
                    acc[ty] += float(net.v[idx].mean())
                k += 1
        g = {ty: float((1.0 + net.i_syn[idx] + (net.g_i[idx] if params.cond else 0.0)).mean())
             for ty, idx in groups.items()}
        return {ty: acc[ty] / k for ty in types}, g

    hist = []
    for it in range(a.iters + 1):
        v, g = settle(a.first_ms if it == 0 else a.iter_ms)
        err = {ty: float(net.v_rest[groups[ty]].mean() - v[ty]) for ty in types}
        hist.append({"iter": it, "v": {k: round(x, 3) for k, x in v.items()},
                     "err": {k: round(x, 3) for k, x in err.items()}, "G": {k: round(x, 3) for k, x in g.items()},
                     "shift": dict(shift)})
        print(f"iter {it}: " + "  ".join(f"{ty} v {v[ty]:.2f} err {err[ty]:+.2f} G {g[ty]:.2f} "
                                         f"shift {shift[ty]:+.2f}" for ty in types), flush=True)
        if it == a.iters or all(abs(e) < a.tol_mv for e in err.values()):
            break
        for ty, idx in groups.items():
            rest = float(net.v_rest[idx].mean())
            new = shift[ty] + 0.9 * err[ty] * g[ty]
            shift[ty] = float(np.clip(rest + new, a.lo, a.hi) - rest)
            net.v_leak[idx] = net.v_rest[idx] + np.float32(shift[ty])
    at_bound = [ty for ty in types
                if not (a.lo < float(net.v_rest[groups[ty]].mean()) + shift[ty] < a.hi)]
    src = f"fitted in the network by scripts/probes/visual_rest_calibrate.py (DECISIONS 6 Oct operating-point block)"
    rows = "".join(
        f"{ty},v_leak_shift_fit,{shift[ty]:.3f},mV,derived,{src},\"leak reversal minus rest putting the type's "
        f"dark in-network mean at its recorded rest {float(net.v_rest[groups[ty]].mean()):.1f} mV (Behnia et al. "
        f"2014); fitted under {' '.join(a.set)} input_gain {a.input_gain or 1}; residual {hist[-1]['err'][ty]:+.2f} mV"
        f"{'; AT THE BOUND' if ty in at_bound else ''}\"\n" for ty in types)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(HEADER + gain_rows + rows)
    Path(a.out).with_suffix(".json").write_text(json.dumps(
        {"set": a.set, "profile": a.profile, "input_gain": a.input_gain, "types": types, "bounds": [a.lo, a.hi],
         "shift": shift, "at_bound": at_bound, "history": hist, "wall_s": round(time.time() - t0)}, indent=1))
    print(f"shifts {shift}; at bound {at_bound}; wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
