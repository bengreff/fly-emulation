"""Per-type optic-lobe rows from the flyvis ensemble (Lappalainen et al. 2024), for our model.

For each of the 50 published networks (scripts/vision/flyvis_sim.py) this reads, per cell type,
the central cell's voltage at the grey steady state (luminance 0.5) and its peak depolarisation to
full-field ON (0.5 -> 1) and OFF (0.5 -> 0) steps of 0.5 s. flyvis cells release relu(V), so the
release at grey as a fraction of the release at the peak of the stronger step response is

    r0 = relu(V_grey) / relu(V_grey + dV_peak)

which is what our graded synapses call release_at_rest (fraction of graded_rmax at rest, with the
release range spanning the response). Ensemble medians over the 50 networks become rows of
data/params/cell_types_flyvis.csv, read only by cell_type:all|optic_lobe_flyvis:

  graded_flyvis            1 for every mapped type (the flyvis model class; recorded rows win)
  tau_m_flyvis             median effective time constant max(tau, 20 ms), ms
  release_at_rest_flyvis   median r0

Photoreceptors (R1-R8) are not mapped: our eye has its own photoreceptor model. Mi3, Mi11, Mi12
and Tm28 have no male-cns type. Rows that conflict with a recording are left out (CONFLICT): the
recorded value wins over the fitted one.

    uv run python scripts/vision/flyvis_rows.py              # 50 networks, then the rows
    uv run python scripts/vision/flyvis_rows.py --rows-only  # rows from the saved readouts
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyvis_sim import RAW, FlyvisNet  # noqa: E402

TRAIN_DT_S = 0.02
CITE = "Lappalainen et al. 2024 Nature 634:1132 (doi 10.1038/s41586-024-07939-3); flyvis 1.2.0 ensemble flow/0000, 50 networks"
# flyvis type -> male-cns type label(s) in our table (regex when it starts with ^)
MAP = {"Am": "Am1", "CT1(Lo1)": "CT1", "CT1(M10)": "CT1", "T5a": "^T5a(_unclear)?$",
       "Tm3": "^Tm3(_unclear)?$", "TmY9": "^TmY9[ab]$"}
SKIP = {"R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "Mi3", "Mi11", "Mi12", "Tm28"}
# (male-cns type, row param) left out because a recording contradicts the fitted value
CONFLICT = {
    ("Tm2", "tau_m_flyvis"): "flyvis Tm2 tau median 136 ms (24% of networks at the 20 ms floor) makes Tm2 slow: "
                             "its 20 ms full-field OFF flash response peaks at 110 ms (50-network median) and is "
                             "faster than Tm1's in only 36% of networks, while Behnia et al. 2014 Nature 512:427 "
                             "recorded Tm2 as the fastest of Mi1/Tm3/Tm1/Tm2 (linear filter peak 43 ms, SEM 2.7; "
                             "Tm1 56); scripts/vision/flyvis_impulse.py",
}


def readouts(net: FlyvisNet, dt=0.005, t_step=0.5) -> pd.DataFrame:
    v0 = net.steady(dt=dt)
    rec = np.array([net.central(t) for t in net.types])
    out = {"v_grey": v0[rec]}
    n = int(t_step / dt)
    for name, lum in (("on", 1.0), ("off", 0.0)):
        V = net.run(np.full((n, len(net.cols)), lum), dt, v0=v0, record=rec)
        dv = V - v0[rec]
        out[f"dv_{name}_peak"] = dv.max(0)
        out[f"dv_{name}_trough"] = dv.min(0)
        out[f"t_{name}_peak_ms"] = 1000 * dt * (1 + dv.argmax(0))
    df = pd.DataFrame(out, index=net.types)
    pref_on = df.dv_on_peak >= df.dv_off_peak
    df["preferred"] = np.where(pref_on, "ON", "OFF")
    peak = np.where(pref_on, df.dv_on_peak, df.dv_off_peak)
    df["r0"] = np.maximum(df.v_grey, 0) / np.maximum(df.v_grey + peak, 1e-9)
    df.loc[df.v_grey <= 0, "r0"] = 0.0
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", type=int, default=50)
    ap.add_argument("--readouts", default="data/derived/flyvis_lappalainen2024_readouts.csv")
    ap.add_argument("--rows", default="data/params/cell_types_flyvis.csv")
    ap.add_argument("--rows-only", action="store_true", help="write the rows from the saved readouts")
    a = ap.parse_args()
    if a.rows_only:
        write_rows(pd.read_csv(a.readouts, index_col=0), a.rows)
        return
    net = FlyvisNet()
    root = RAW / "results" / "flow" / "0000"
    per = []
    taus = []
    for m in range(a.models):
        net.set_model(root / f"{m:03d}" / "best_chkpt")
        df = readouts(net)
        df["model"] = m
        per.append(df)
        taus.append(net.ckpt["nodes_time_const"].astype(float))
        print(f"model {m:03d} done", flush=True)
    allr = pd.concat(per).rename_axis("flyvis_type").reset_index()
    tau = np.array(taus)
    med = allr.groupby("flyvis_type", sort=False).agg(
        v_grey_au=("v_grey", "median"), dv_on_peak_au=("dv_on_peak", "median"),
        dv_off_peak_au=("dv_off_peak", "median"), t_on_peak_ms=("t_on_peak_ms", "median"),
        t_off_peak_ms=("t_off_peak_ms", "median"), r0_median=("r0", "median"),
        r0_q25=("r0", lambda x: x.quantile(0.25)), r0_q75=("r0", lambda x: x.quantile(0.75)),
        frac_on_preferred=("preferred", lambda x: float(np.mean(x == "ON"))))
    med["tau_eff_ms_median"] = [1000 * np.median(np.maximum(tau[:, i], TRAIN_DT_S)) for i in range(len(net.types))]
    med["frac_tau_at_floor"] = [float(np.mean(tau[:, i] < TRAIN_DT_S)) for i in range(len(net.types))]
    med["n_models"] = a.models
    Path(a.readouts).parent.mkdir(parents=True, exist_ok=True)
    med.to_csv(a.readouts, float_format="%.4g")
    allr.to_csv(Path(a.readouts).with_name("flyvis_lappalainen2024_readouts_per_model.csv"), index=False,
                float_format="%.4g")
    write_rows(med, a.rows)
    print(med[["v_grey_au", "r0_median", "r0_q25", "r0_q75", "tau_eff_ms_median", "frac_on_preferred",
               "t_on_peak_ms", "t_off_peak_ms"]].round(3).to_string())


def write_rows(med: pd.DataFrame, path: str) -> None:
    rows = []
    for fv, r in med.groupby(lambda t: MAP.get(t, t)):   # CT1's two compartments share one row
        srcs = [t for t in med.index if MAP.get(t, t) == fv]
        if set(srcs) <= SKIP:
            continue
        tau_ms = float(r.tau_eff_ms_median.mean())
        floor = float(r.frac_tau_at_floor.mean())
        r0 = float(r.r0_median.mean())
        q = f"{r.r0_q25.mean():.2f}-{r.r0_q75.mean():.2f}"
        what = " and ".join(srcs)
        rows.append(dict(type=fv, param="graded_flyvis", value=1.0, units="boolean", basis="inferred", source=CITE,
                         justification=f"fitted model class (Lappalainen 2024): every type graded with relu release; "
                                       f"flyvis {what}; this type's mode unrecorded unless a graded_rec row says so "
                                       f"(recorded rows win)"))
        rows.append(dict(type=fv, param="tau_m_flyvis", value=round(tau_ms, 1), units="ms", basis="inferred",
                         source=CITE,
                         justification=f"fitted (Lappalainen 2024): ensemble median of max(tau, 20 ms) for flyvis "
                                       f"{what}; {floor:.0%} of networks at the 20 ms training floor, where the fit "
                                       f"gives only an upper bound; a whole-cell effective time constant of a "
                                       f"task-trained model, not a membrane measurement"))
        rows.append(dict(type=fv, param="release_at_rest_flyvis", value=round(r0, 3), units="fraction of graded_rmax",
                         basis="inferred", source=CITE,
                         justification=f"derived from fitted (Lappalainen 2024): relu(V_grey)/relu(V_grey + peak "
                                       f"step response), ensemble median (IQR {q}) for flyvis {what}; "
                                       f"scripts/vision/flyvis_rows.py"))
    out = pd.DataFrame(rows)
    drop = out.apply(lambda r: (r.type, r.param) in CONFLICT, axis=1)
    for (t, p), why in CONFLICT.items():
        print(f"left out {t} {p}: {why}")
    out[~drop].to_csv(path, index=False)
    print(f"{out.type.nunique()} types, {int((~drop).sum())} rows -> {path}")


if __name__ == "__main__":
    main()
