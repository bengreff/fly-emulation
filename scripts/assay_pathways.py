"""Pathway assays: does activity follow the wiring, or the noise term?

Open loop, brain only, no body: identified sensory neurons are driven with
Poisson input as in Shiu et al. 2024, background noise is off, and the readout
is an identified motor neuron. Each assay is repeated on a degree-preserving
shuffled graph (connectome.shuffled). If the real graph responds and the
shuffled one does not, the anatomy is carrying the result (F-GAIN-2).

    uv run python scripts/assay_pathways.py --assay sugar_mn9
    uv run python scripts/assay_pathways.py --assay sugar_mn9 --shuffles 2 \\
        --rates 0,20,50,100,150,200

Assays are defined below by cell type, with the evidence for each selector.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from flyemu import connectome, lif, profiles
from flyemu.provenance import RunRecord
from flyemu.registry import Policy, Registry

REPO = Path(__file__).resolve().parents[1]

# stim/readout by male-cns `type`. `silence` removes those cells' output.
ASSAYS = {
    "sugar_mn9": dict(
        stim=["LB3b", "LB3c"], readout=["MN9"],
        evidence="LB3b/LB3c match Gr64f-GAL4 sweet lbGRN projections (male-CNS "
                 "taste connectome, bioRxiv 10.1101/2025.08.25.671814); MN9 "
                 "drives the rostrum protractor (McKellar 2020). Predicted and "
                 "confirmed: sugar GRN activation drives MN9 (Shiu 2024 Fig 2)",
    ),
    "water_mn9": dict(
        stim=["LB3a"], readout=["MN9"],
        evidence="LB3a matches ppk28-GAL4 water lbGRNs; water GRNs also drive "
                 "MN9 in Shiu 2024",
    ),
    "bitter_mn9": dict(
        stim=["LB1a", "LB1b", "LB1c", "LB1d"], readout=["MN9"],
        evidence="LB1a-d match Gr33a-GAL4 bitter lbGRNs; bitter alone should "
                 "not drive MN9 (Shiu 2024)",
    ),
    "sugar_bitter_mn9": dict(
        stim=["LB1a", "LB1b", "LB1c", "LB1d"], readout=["MN9"],
        co_stim=(["LB3b", "LB3c"], 100.0),
        evidence="bitter GRNs suppress sugar-evoked MN9 activity (Shiu 2024, "
                 "predicted and confirmed); sugar held at 100 Hz, bitter swept",
    ),
    "dng100_legs": dict(
        stim=["DNg100"], readout_sel=("vnc_motor", "fl"),
        evidence="DNg100 activation drives rhythmic front-leg motor output in "
                 "VNC connectome simulations, confirmed optogenetically "
                 "(Pugliese et al. 2025, bioRxiv 10.1101/2025.09.12.675944); "
                 "walking step frequency ~7-15 Hz",
    ),
    # Fresh held-out assays, pre-registered in DECISIONS.md (F-SENS-1).
    "joce_adn": dict(
        stim=["^JO-(C|E)"], readout=["DNg62", "DNge078"],
        evidence="JO-C/E activation elicits antennal grooming via aBN1 -> "
                 "aDN1/aDN2 (Hampel 2015, 2020); expect > 5 Hz",
    ),
    "jof_adn": dict(
        stim=["^JO-F"], readout=["DNg62", "DNge078"],
        evidence="JO-F activation also elicits antennal grooming (Hampel "
                 "2020); expect > 5 Hz",
    ),
    "jof_mdn": dict(
        stim=["^JO-F"], readout=["MDN"],
        evidence="JO-F activation elicits backward walking, attributed to MDN "
                 "(Hampel 2020; Bidaye 2014); inferred readout; expect > 5 Hz",
    ),
    "joce_mdn": dict(
        stim=["^JO-(C|E)"], readout=["MDN"],
        evidence="null: JO-C/E gives grooming, no backward walking (Hampel "
                 "2020); expect < 2 Hz",
    ),
    "lplc2_gf": dict(
        stim=["LPLC2"], readout=["DNp01"],
        evidence="LPLC2 looming detectors drive the giant fibre (Ache et al. "
                 "2019); expect > 5 Hz",
    ),
    "gf_ttm": dict(
        stim=["DNp01"], readout=["TTMn"],
        evidence="DNp01 is the giant fibre; GF -> TTMn is the escape jump "
                 "pathway (King & Wyman 1980; Cheong 2024)",
    ),
}


def select(neurons: pd.DataFrame, types: list[str]) -> np.ndarray:
    """Cells whose `type` is in `types`; an entry starting '^' is a regex."""
    t = neurons.type.fillna("")
    m = t.isin([x for x in types if not x.startswith("^")])
    for x in types:
        if x.startswith("^"):
            m |= t.str.match(x)
    return np.flatnonzero(m.to_numpy())


def rhythmicity(raster: np.ndarray, dt_ms: float) -> tuple[float, float]:
    """Autocorrelation rhythm score of one spike train, and its frequency.

    Binned at 1 ms, smoothed with a 5 ms boxcar, mean-subtracted. The score is
    the first autocorrelation peak within 40-250 ms lag (4-25 Hz) minus the
    trough before it, on a correlation scale; 0 for an aperiodic train.
    """
    per = int(round(1.0 / dt_ms))
    b = raster[: len(raster) // per * per].reshape(-1, per).sum(1).astype(float)
    if b.sum() < 5:
        return 0.0, np.nan
    b = np.convolve(b, np.ones(5) / 5, mode="same")[100:]   # drop onset
    b = b - b.mean()
    ac = np.correlate(b, b, mode="full")[len(b) - 1:]
    if ac[0] <= 0:
        return 0.0, np.nan
    ac = ac / ac[0]
    seg = ac[40:251]
    k = int(np.argmax(seg))
    trough = ac[1:40 + k + 1].min()
    return float(max(seg[k] - trough, 0.0)), 1000.0 / (40 + k)


def run_trial(conn, params, dt, stim_idx, rate_hz, kick_mv, duration_ms,
              seed, silence_idx=None, co=None, record=None):
    net = lif.Network(conn, params, dt, rng=np.random.default_rng(seed))
    if silence_idx is not None and len(silence_idx):
        net.silence(silence_idx)
    rng = np.random.default_rng(seed + 10_000)
    counts = np.zeros(conn.n, dtype=np.int32)
    n_steps = int(round(duration_ms / dt))
    raster = None
    if record is not None:
        raster = np.zeros((n_steps, len(record)), dtype=bool)
        pos = np.full(conn.n, -1)
        pos[record] = np.arange(len(record))
    idx = stim_idx
    prob = np.full(len(stim_idx), rate_hz * dt / 1000.0)
    if co is not None:
        idx = np.concatenate([stim_idx, co[0]])
        prob = np.concatenate([prob, np.full(len(co[0]), co[1] * dt / 1000.0)])
    for step in range(n_steps):
        kick = None
        if prob.any():
            kick = (idx[rng.random(len(idx)) < prob], kick_mv)
        spk = net.step(kick=kick)
        if spk.size:
            counts[spk] += 1
            if raster is not None:
                q = pos[spk]
                raster[step, q[q >= 0]] = True
    return counts, raster


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assay", default="sugar_mn9", choices=sorted(ASSAYS))
    ap.add_argument("--profile", default="shiu2024",
                    choices=sorted(profiles.PROFILES))
    ap.add_argument("--rates", default="0,100")
    ap.add_argument("--duration-ms", type=float, default=1000.0)
    ap.add_argument("--timestep-ms", type=float, default=0.1)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--shuffles", type=int, default=1)
    ap.add_argument("--min-synapses", type=int, default=5)
    ap.add_argument("--set", action="append", default=[], metavar="ENTITY|PROP=V")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    a = ASSAYS[args.assay]
    rates = [float(r) for r in args.rates.split(",")]
    run_id = f"assay-{args.assay}-{args.profile}" + (f"-{args.tag}" if args.tag else "")
    out = REPO / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    rec = RunRecord(run_id, out, description=f"pathway assay {args.assay}, "
                    "open loop, brain only, noise per profile")
    rec.add_config(vars(args))
    rec.add_config({"assay_evidence": a["evidence"]})

    reg = Registry(Policy.MINIMAL)
    for s in args.set:
        k, v = s.split("=")
        reg.overrides[k] = float(v)
    prof = profiles.apply(reg, args.profile)
    conn = connectome.build(reg, min_synapses=args.min_synapses)
    params = lif.default_params(reg, conn, timestep_ms=args.timestep_ms)
    reg.write(out / "inventory.csv")

    nrn = conn.neurons
    stim_idx = select(nrn, a["stim"])
    if "readout_sel" in a:
        sc, sub = a["readout_sel"]
        read_idx = np.flatnonzero(((nrn.superclass == sc) & (nrn.subclass == sub)).to_numpy())
        a["readout"] = [f"{sc}/{sub}"]
    else:
        read_idx = select(nrn, a["readout"])
    want_rhythm = "readout_sel" in a
    co = None
    if "co_stim" in a:
        co = (select(nrn, a["co_stim"][0]), a["co_stim"][1])
        print(f"co-stim {len(co[0])} ({', '.join(a['co_stim'][0])}) at "
              f"{co[1]:g} Hz")
    print(f"{conn.n:,} neurons, {conn.n_edges:,} edges; stim {len(stim_idx)} "
          f"({', '.join(a['stim'])}), readout {len(read_idx)} "
          f"({', '.join(a['readout'])})")
    if not len(stim_idx) or not len(read_idx):
        raise SystemExit("selector matched nothing")

    graphs = [("real", conn)] + [
        (f"shuffled{k}", connectome.shuffled(conn, np.random.default_rng(100 + k)))
        for k in range(args.shuffles)
    ]
    rows, rate_store = [], {}
    for gname, g in graphs:
        for r in rates:
            for t in range(args.trials):
                t0 = time.time()
                c, raster = run_trial(
                    g, params, args.timestep_ms, stim_idx, r, prof["kick_mv"],
                    args.duration_ms, seed=t, co=co,
                    record=read_idx if want_rhythm else None)
                hz = c / (args.duration_ms / 1000.0)
                rate_store[f"{gname}_{r:g}_{t}"] = hz.astype(np.float32)
                row = dict(
                    graph=gname, stim_hz=r, trial=t,
                    stim_hz_obs=float(hz[stim_idx].mean()),
                    readout_hz=float(hz[read_idx].mean()),
                    readout_max_hz=float(hz[read_idx].max()),
                    n_active=int((c > 0).sum()),
                    frac_active=float((c > 0).mean()),
                    mean_hz=float(hz.mean()),
                    wall_s=round(time.time() - t0, 1),
                )
                if want_rhythm:
                    act = np.flatnonzero(c[read_idx] >= 5)
                    sc = [rhythmicity(raster[:, j], args.timestep_ms) for j in act]
                    row["n_readout_active"] = len(act)
                    row["rhythmicity_median"] = float(np.median([x[0] for x in sc])) if sc else 0.0
                    row["rhythm_hz_median"] = float(np.nanmedian([x[1] for x in sc])) if sc else np.nan
                    row["readout_active_median_hz"] = float(np.median(hz[read_idx][act])) if len(act) else 0.0
                else:
                    for i in read_idx:
                        row[f"hz_{nrn.instance.iat[i] or nrn.bodyId.iat[i]}"] = float(hz[i])
                rows.append(row)
                print({k: (round(v, 3) if isinstance(v, float) else v)
                       for k, v in row.items()}, flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(out / "trials.csv", index=False)
    np.savez_compressed(out / "rates.npz", body_id=nrn.bodyId.to_numpy(),
                        **rate_store)
    summ = df.groupby(["graph", "stim_hz"])[
        ["readout_hz", "n_active", "mean_hz"]].agg(["mean", "std"]).round(3)
    print(summ.to_string())
    summ.to_csv(out / "summary.csv")
    rec.result("summary", summ.reset_index().to_dict(orient="records").__repr__())
    print("record:", rec.finish())


if __name__ == "__main__":
    main()
