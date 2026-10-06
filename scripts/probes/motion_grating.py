"""Open-loop motion responses of the visual pathway to a drifting grating (diagnostic, s12 vision blank).

The flyapp relay (6 October) found T4/T5 silent under m9r/m9c: the medulla cells spike by default (the
optic columnar mode group, guessed) and the lamina moves them by under 1.5 mV. This drives the
photoreceptors directly with a sine grating drifting in four directions, through the same drive rule as
the eye (vision.Vision: dark_drive + luminance_gain x luminance, per photoreceptor through its derived
ommatidium direction, data/derived/retinotopy.csv az_pred/el_pred), with no body. For each
type it reports the mean membrane potential and spike rate during the grating minus the static grating
at mean luminance, and a direction index for the T4/T5 subtypes:
DSI = (R_pref - R_null) / (R_pref + R_null) over opposite directions.

Directions are in each eye's derived az/el frame, so +az is not the same world direction on both eyes;
the subtype comparison (T4a against T4b, T4c against T4d) does not need the convention.

    uv run python scripts/probes/motion_grating.py --profile m9c --set cell_type:all|mode_from_recordings=1 \
        --out runs/s12/vision/grating_rec.json
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
         "Tm9", "CT1", "T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d", "LPi1-2", "LPi2-1", "Am1",
         "HSN", "HSE", "HSS", "H2", "HST", "VS", "LC4", "LPLC2", "LC11"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--wavelength-deg", type=float, default=30.0)
    ap.add_argument("--tf-hz", type=float, default=1.0, help="temporal frequency")
    ap.add_argument("--contrast", type=float, default=1.0)
    ap.add_argument("--settle-ms", type=float, default=300.0)
    ap.add_argument("--ms", type=float, default=1000.0, help="per direction")
    ap.add_argument("--sample-hz", type=float, default=100.0, help="eye update rate, as the organism")
    ap.add_argument("--seed", type=int, default=1)
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
    az = rt.az_pred.reindex(bid).to_numpy()
    elv = rt.el_pred.reindex(bid).to_numpy()
    has = np.isfinite(az) & np.isfinite(elv)
    rows = vis.rows[has]
    az, elv = az[has], elv[has]
    print(f"photoreceptors driven {has.sum()} of {len(vis.rows)} (with a derived direction)", flush=True)

    t = conn.neurons.type.fillna("").to_numpy()
    groups = {ty: np.flatnonzero(np.char.startswith(t.astype(str), ty) if ty == "VS" else t == ty)
              for ty in TYPES}
    groups = {k: v for k, v in groups.items() if v.size}
    graded = np.asarray(params.graded, bool)
    sel = np.concatenate(list(groups.values()))
    off = dict(zip(groups, np.cumsum([0] + [v.size for v in groups.values()])[:-1]))
    every = max(1, int(round(1000.0 / a.sample_hz / DT)))

    net = lif.Network(conn, params, DT, rng=np.random.default_rng(a.seed))
    net.elec = el if len(el[0]) else None
    drive = np.zeros(conn.n, np.float32)

    def lum(coord: np.ndarray, sign: float, t_ms: float) -> np.ndarray:
        ph = 2 * np.pi * (coord / a.wavelength_deg - sign * a.tf_hz * t_ms / 1000.0)
        return 0.5 + 0.5 * a.contrast * np.sin(ph)

    def run(name: str, coord: np.ndarray | None, sign: float, ms: float, record: bool) -> dict:
        n_steps = int(ms / DT)
        vsum = np.zeros(conn.n, np.float64)
        cnt = np.zeros(conn.n, np.int64)
        trace = np.zeros((n_steps, len(groups)), np.float32)   # type-mean v per step
        acc = np.zeros(sel.size, np.complex128)                # per-cell sum of v exp(-i w t)
        w = 2 * np.pi * a.tf_hz * DT / 1000.0
        for s in range(n_steps):
            if s % every == 0:
                L = np.full(rows.size, 0.5) if coord is None else lum(coord, sign, s * DT)
                drive[rows] = vis.baseline_mv + vis.gain_mv * L
            sp = net.step(external_mv=drive)
            if record:
                vsum += net.v
                np.add.at(cnt, sp, 1)
                trace[s] = [net.v[idx].mean() for idx in groups.values()]
                acc += net.v[sel] * np.exp(-1j * w * s)
        if not record:
            return {}
        sec = ms / 1000.0
        tt = np.arange(n_steps) * DT / 1000.0
        ref = np.exp(-2j * np.pi * a.tf_hz * tt)
        # per-cell F1 = 2|mean((v - mean v) exp(-i w t))|; the type-mean F1 cancels across columns because
        # a 30 deg grating puts the columns of one type at every phase
        f1c = 2 * np.abs(acc / n_steps - (vsum[sel] / n_steps) * ref.mean())
        out = {}
        for k, (ty, idx) in enumerate(groups.items()):
            x = trace[:, k] - trace[:, k].mean()
            fc = f1c[off[ty]:off[ty] + idx.size]
            out[ty] = {"v_mv": round(float((vsum[idx] / n_steps).mean()), 3),
                       "f1_mv": round(float(2 * abs((x * ref).mean())), 4),   # type-mean modulation
                       "f1_cell_mv": round(float(fc.mean()), 4),               # per-cell modulation
                       "f1_cell_p90_mv": round(float(np.percentile(fc, 90)), 4),
                       "rate_hz": round(float(cnt[idx].sum() / idx.size / sec), 3),
                       "graded": bool(graded[idx].all()), "n": int(idx.size)}
        print(f"{name:8s} " + "  ".join(f"{ty} {o['v_mv']:.2f}/{o['rate_hz']:.1f}" for ty, o in out.items()
                                        if ty.startswith(("L1", "Mi1", "Tm1", "T4", "T5", "HS", "Am1"))),
              flush=True)
        return out

    run("settle", None, 0, a.settle_ms, False)
    res = {"static": run("static", None, 0, a.ms, True)}
    for name, coord, sign in [("az+", az, 1.0), ("az-", az, -1.0), ("el+", elv, 1.0), ("el-", elv, -1.0)]:
        run("reset", None, 0, 300.0, False)
        res[name] = run(name, coord, sign, a.ms, True)

    def resp(d: str, ty: str, key: str) -> float:
        return res[d][ty][key] - res["static"][ty][key]

    dsi = {}
    for ty in [x for x in groups if x[:2] in ("T4", "T5")]:
        key = "v_mv" if res["static"][ty]["graded"] else "rate_hz"
        r = {d: resp(d, ty, key) for d in ("az+", "az-", "el+", "el-")}
        pref = max(r, key=r.get)
        null = {"az+": "az-", "az-": "az+", "el+": "el-", "el-": "el+"}[pref]
        num, den = r[pref] - r[null], abs(r[pref]) + abs(r[null])
        dsi[ty] = {"measure": key, "resp": {k: round(v, 3) for k, v in r.items()}, "pref": pref,
                   "dsi": round(num / den, 3) if den > 0 else None}
        print(f"{ty}: {key} {dsi[ty]['resp']} pref {pref} DSI {dsi[ty]['dsi']}", flush=True)
    meta = {"profile": a.profile, "set": a.set, "wavelength_deg": a.wavelength_deg, "tf_hz": a.tf_hz,
            "contrast": a.contrast, "ms": a.ms, "sample_hz": a.sample_hz, "seed": a.seed,
            "gain_mv": vis.gain_mv, "dark_mv": vis.baseline_mv, "driven": int(has.sum()),
            "wall_s": round(time.time() - t0)}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps({"meta": meta, "res": res, "dsi": dsi}, indent=1))


if __name__ == "__main__":
    main()
