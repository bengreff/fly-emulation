"""Calibrate the one global synaptic scale by a physiological criterion.

Criterion, declared before any pathway assay is scored: after a 400 ms sugar
GRN stimulus ends, activity must return to rest within 200 ms, as it does in
the animal. The chosen scale is the largest tested value that meets it. Only
sugar GRNs are used; every other assay stays held out.

    uv run python scripts/calibrate_gain.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.provenance import RunRecord
from flyemu.registry import Policy, Registry

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scales", default="0.3,0.4,0.5,0.6,0.7,0.8,1.0")
    ap.add_argument("--rates", default="50,150")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--set", action="append", default=[], metavar="ENTITY|PROP=V")
    ap.add_argument("--tag", default="")
    ap.add_argument("--profile", default="m2")
    ap.add_argument("--generic", type=int, default=0,
                    help="rule v2: also require return to rest after this many "
                         "random 40-cell sensory populations outside every assay")
    ap.add_argument("--graph", default="real", choices=["real", "shuffled", "typeshuf"],
                    help="calibrate a control graph by the same rule")
    args = ap.parse_args()
    out = REPO / "runs" / (f"calibrate-gain-{args.profile}" + (f"-{args.tag}" if args.tag else ""))
    out.mkdir(parents=True, exist_ok=True)
    rec = RunRecord(out.name, out, description="global synaptic scale by "
                    "return-to-rest after sugar GRN stimulation")
    rec.add_config(vars(args))

    reg = Registry(Policy.MINIMAL)
    for item in args.set:
        k, v = item.split("=")
        reg.overrides[k] = float(v)
    prof = profiles.apply(reg, args.profile)
    conn = connectome.build(reg, min_synapses=5)
    if args.graph == "shuffled":
        conn = connectome.shuffled(conn, np.random.default_rng(100))
    elif args.graph == "typeshuf":
        conn = connectome.type_shuffled(conn, np.random.default_rng(200))
    params = lif.default_params(reg, conn, timestep_ms=0.1)
    nrn = conn.neurons
    stim = select(nrn, ["LB3b", "LB3c"])
    stims = [("sugar", stim)]
    if args.generic:
        t = nrn.type.fillna("")
        pool = np.flatnonzero((nrn.superclass.fillna("").str.contains("sensory")
                               & ~t.str.match(r"^(JO-|LB|LPLC2|Lg|PhG|WG|claw_|dorsal_tp)")
                               & (t != "")).to_numpy())
        grng = np.random.default_rng(12345)
        for k in range(args.generic):
            stims.append((f"generic{k}", grng.choice(pool, 40, replace=False)))
    mn9 = select(nrn, ["MN9"])
    base_w = None
    rows = []
    for scale in [float(s) for s in args.scales.split(",")]:
        for (sname, stim), rate, seed in [
                (st, float(r), sd) for st in stims
                for r in args.rates.split(",") for sd in range(args.seeds)
                if st[0] == "sugar" or float(r) == max(map(float, args.rates.split(",")))]:
            if True:
                net = lif.Network(conn, params, 0.1, rng=np.random.default_rng(seed))
                if base_w is None:
                    base_w = net.w.copy()
                net.w = base_w * scale
                rng = np.random.default_rng(seed + 10_000)
                on = np.zeros(conn.n); late = np.zeros(conn.n)
                for s in range(8000):          # 0-400 on, 400-600 grace, 600-800 test
                    k = (stim[rng.random(len(stim)) < rate * 1e-4],
                         prof["kick_mv"]) if s < 4000 else None
                    spk = net.step(kick=k)
                    if s < 4000:
                        on[spk] += 1
                    elif s >= 6000:
                        late[spk] += 1
                # cells with intrinsic tonic drive (e.g. slow MNs at their
                # measured rest rate) fire without input by design
                late[np.broadcast_to(np.asarray(params.spont_mv), (conn.n,)) > 0] = 0
                row = dict(scale=scale, stim=sname, stim_hz=rate, seed=seed,
                           mn9_hz=float(on[mn9].mean() / 0.4),
                           active_on=int((on > 0).sum()),
                           active_600_800=int((late > 0).sum()),
                           mean_hz_on=float(on.mean() / 0.4))
                rows.append(row)
                print(row, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / "calibration.csv", index=False)
    # The last passing scale BEFORE the first failure: a noisy pass above a
    # failure near the tipping point is not accepted.
    ok = (df.groupby("scale").active_600_800.max() == 0).sort_index()
    chosen = None
    for sc, passed in ok.items():
        if not passed:
            break
        chosen = float(sc)
    print(df.groupby(["scale", "stim", "stim_hz"]).mean(numeric_only=True).round(2).to_string())
    print("scale meeting return-to-rest:", chosen)
    rec.result("chosen_scale", chosen)
    base_mv = float(conn.psp_mv)
    rec.result("chosen_efficacy_mv", None if chosen is None else base_mv * chosen)
    print("chosen efficacy mV:", None if chosen is None else round(base_mv * chosen, 4))
    rec.finish()


if __name__ == "__main__":
    main()
