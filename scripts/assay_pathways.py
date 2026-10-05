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

from flyemu import connectome, electrical, lif, profiles
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
    "legsugar_mn9": dict(
        stim=["LgLG4", "LgAG2"], readout=["MN9"],
        evidence="LgLG4 (Gr64f+/Ir56b+) and LgAG2 (Gr61a+) match tarsal sweet GRN "
                 "projections (male-CNS taste connectome, bioRxiv 10.1101/2025.08.25.671814); "
                 "tarsal sugar evokes proboscis extension (Dethier 1976). F-TASTE-LEG-1 trace (s12)",
    ),
    "ascsugar_mn9": dict(
        stim=["LgAG2"], readout=["MN9"],
        evidence="LgAG2 (sensory_ascending, Gr61a+) inferred to be the ascending tarsal sweet GRNs "
                 "that project to the GNG and start feeding (Thoma et al. 2016 Nat Commun 7:10678); "
                 "F-TASTE-LEG-1 (s12)",
    ),
    "legsugar3_mn9": dict(
        stim=["LgLG3", "LgLG4", "LgAG2"], readout=["MN9"],
        evidence="LgLG3 proposed as a sugar (Gr5a) type because its top partner is Dandelion "
                 "(AN13B002), a key partner of sugar GRNs (Tastekin et al. bioRxiv "
                 "10.1101/2025.08.25.671814 v2, Fig 6; proposal, secondary read). Diagnostic (s12)",
    ),
    "legsugar_labsugar_mn9": dict(
        stim=["LgLG4", "LgAG2"], readout=["MN9"],
        co_stim=(["LB3b", "LB3c"], 100.0),
        evidence="convergence test (s12): does leg sugar add to labellar sugar at MN9? "
                 "Labellar sugar held at 100 Hz, leg sugar swept; compare with sugar_mn9 at 100 Hz",
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
    "gf_dlm": dict(
        stim=["DNp01"], readout=["^DLMn"],
        evidence="held out for the GF electrical pre-registration: GF -> PSI "
                 "(electrical) -> DLMn (chemical); DLMn follows GF at low rates "
                 "(Tanouye & Wyman 1980)",
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


def rhythm_excess(raster: np.ndarray, dt_ms: float, n_surr: int = 10,
                  seed: int = 0) -> tuple[float, float, float]:
    """Rhythmicity above ISI-shuffled surrogates of the same train.

    Shuffling inter-spike intervals keeps the rate and ISI distribution
    (so tonic regular firing keeps its harmonics) but destroys slow
    periodic modulation. Returns (score - surrogate mean, surrogate sd,
    frequency of the real peak).
    """
    sc, hz = rhythmicity(raster, dt_ms)
    t = np.flatnonzero(raster)
    if len(t) < 5:
        return 0.0, 0.0, np.nan
    isi = np.diff(t)
    rng = np.random.default_rng(seed)
    surr = []
    for _ in range(n_surr):
        tt = t[0] + np.r_[0, np.cumsum(rng.permutation(isi))]
        r = np.zeros_like(raster)
        r[tt[tt < len(r)]] = True
        surr.append(rhythmicity(r, dt_ms)[0])
    return sc - float(np.mean(surr)), float(np.std(surr)), hz


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


ELEC: dict = {}


def run_trial(conn, params, dt, stim_idx, rate_hz, kick_mv, duration_ms,
              seed, silence_idx=None, co=None, record=None):
    net = lif.Network(conn, params, dt, rng=np.random.default_rng(seed))
    net.elec = ELEC.get(id(conn))
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
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE,
                    choices=sorted(profiles.PROFILES))
    ap.add_argument("--rates", default="0,100")
    ap.add_argument("--duration-ms", type=float, default=1000.0)
    ap.add_argument("--timestep-ms", type=float, default=0.1)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--shuffles", type=int, default=1,
                    help="number of global rewired controls")
    ap.add_argument("--type-shuffles", type=int, default=0,
                    help="number of cell-type block-preserving controls")
    ap.add_argument("--min-synapses", type=int, default=profiles.WORKING_MIN_SYNAPSES)
    ap.add_argument("--set", action="append", default=[], metavar="ENTITY|PROP=V")
    ap.add_argument("--tag", default="")
    ap.add_argument("--release-gain", action="append", default=[], metavar="TYPE[,TYPE]=G",
                    help="diagnostic: multiply the presynaptic release gain of these types (s12)")
    ap.add_argument("--silence-ids", default="", metavar="FILE",
                    help="diagnostic: silence the output of these bodyIds, one per line (s12)")
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
    for s in args.release_gain:
        tys, g = s.split("=")
        m = conn.neurons.type.isin(tys.split(",")).to_numpy()
        params.release_gain = np.broadcast_to(np.asarray(params.release_gain, np.float32), (conn.n,)).copy()
        params.release_gain[m] *= float(g)
        print(f"release gain x{float(g):g} on {int(m.sum())} cells ({tys}); diagnostic")
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
    # Readout cells the reconstructors flag as incompletely traced are
    # dropped and listed (F-DATA-3: MN9_R has 633 inputs vs MN9_L's 6,358).
    extra = REPO / "data" / "cache" / "male_cns_extra.parquet"
    if extra.exists():
        lab = (pd.read_parquet(extra, columns=["bodyId", "statusLabel"])
               .set_index("bodyId").statusLabel.reindex(nrn.bodyId).fillna("").to_numpy())
        bad = np.array(["Hard to trace" in x or "Partially" in x for x in lab[read_idx]], bool)
        if bad.any():
            dropped = [str(nrn.instance.iat[i]) for i in read_idx[bad]]
            print("readout excludes incompletely traced:", dropped)
            rec.add_config({"readout_excluded_incomplete": dropped})
            read_idx = read_idx[~bad]
    sil = None
    if args.silence_ids:
        ids = np.loadtxt(args.silence_ids, dtype=np.int64, ndmin=1)
        sil = conn.index_of(ids)
        sil = sil[sil >= 0]
        print(f"silenced {len(sil)} of {len(ids)} listed cells; diagnostic")
        rec.add_config({"silenced_bodyids": ids.tolist()})
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
    ] + [
        (f"typeshuf{k}", connectome.type_shuffled(conn, np.random.default_rng(200 + k)))
        for k in range(args.type_shuffles)
    ]
    # Identified electrical pairs are fixed by identity, so every control keeps
    # them (they are not part of the rewired chemical graph).
    el = electrical.build(reg, conn)
    for _, g in graphs:
        ELEC[id(g)] = el if len(el[0]) else None
    if len(el[0]):
        print(f"electrical pairs: {len(el[0])}")
    reg.write(out / "inventory.csv")
    rows, rate_store = [], {}
    for gname, g in graphs:
        for r in rates:
            for t in range(args.trials):
                t0 = time.time()
                c, raster = run_trial(
                    g, params, args.timestep_ms, stim_idx, r, prof["kick_mv"],
                    args.duration_ms, seed=t, co=co, silence_idx=sil,
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
                    ex = [rhythm_excess(raster[:, j], args.timestep_ms) for j in act]
                    row["n_readout_active"] = len(act)
                    row["rhythmicity_median"] = float(np.median([x[0] for x in sc])) if sc else 0.0
                    row["rhythm_excess_median"] = float(np.median([x[0] for x in ex])) if ex else 0.0
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
