"""Current-step features of the Azevedo 2020 slow tibia-flexor MNs for the rung-1 fit (session 11).

Per cell (R35C09; Dryad CurrentStep2T trials with the authors' `spikes`, excluded == 0),
per step amplitude: measured current change dI (pA), spontaneous rate before the step
(0-0.5 s), rate over the step (0.55-1.0 s, as scripts/azevedo_slow_mn.py), early (0.5-0.6 s)
and late (0.9-1.0 s) rates and their ratio (adaptation), and for hyperpolarising steps
the sag fraction (peak minus steady deflection over the steady deflection; spikes absent).
Rin and tau_m come from data/derived/azevedo2020_slow_mn_<cell>[_intrinsic].json.
All measured (single cells); ratios derived.

    uv run python scripts/azevedo_current_step_features.py
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/azevedo2020"
OUT = ROOT / "data/derived/azevedo2020_current_step_features.csv"
CELLS = ["180111_F2_C1", "181021_F1_C1", "180621_F1_C1", "181127_F1_C1"]


def rate(s, a, b):
    return float(((s >= a) & (s < b)).sum() / (b - a))


rows = []
for cell in CELLS:
    base = RAW / cell if (RAW / cell).is_dir() else RAW
    tag = cell.split("_")[0]
    js = sorted(ROOT.glob(f"data/derived/azevedo2020_slow_mn_{tag}*.json"))[0]
    meta = json.loads(js.read_text())
    for f in sorted(glob.glob(str(base / f"CurrentStep2T_Raw_{cell}_*.mat"))):
        d = sio.loadmat(f, squeeze_me=True, struct_as_record=False)
        if d.get("excluded", 0) or "spikes" not in d:
            continue
        p = d["params"]
        fs = float(p.sampratein)
        s = np.atleast_1d(d["spikes"]).astype(float) / fs
        v, c = d["voltage_1"], d["current_1"]
        t = np.arange(len(v)) / fs
        pre, on = (t >= 0.2) & (t < 0.5), (t >= 0.7) & (t < 1.0)
        dI = float(np.median(c[on]) - np.median(c[pre]))
        sag = np.nan
        if p.step < 0:
            steady = np.median(v[(t >= 0.9) & (t < 1.0)]) - np.median(v[pre])
            peak = np.min(np.convolve(v[(t >= 0.5) & (t < 0.7)], np.ones(50) / 50, "valid")) - np.median(v[pre])
            sag = float((peak - steady) / steady) if steady < -1 else np.nan
        early, late = rate(s, 0.5, 0.6), rate(s, 0.9, 1.0)
        rows.append(dict(cell=cell, trial=int(p.trial), step_pA=float(p.step), dI_pA=dI,
                         rin_MOhm=meta["input_resistance_MOhm"][0], tau_m_ms=meta["tau_m_ms"][0],
                         spont_hz=rate(s, 0.0, 0.5), on_hz=rate(s, 0.55, 1.0), early_hz=early, late_hz=late,
                         sag_frac=sag))
df = pd.DataFrame(rows)
agg = (df.groupby(["cell", "step_pA"])
       .agg(n=("trial", "size"), dI_pA=("dI_pA", "mean"), rin_MOhm=("rin_MOhm", "first"),
            tau_m_ms=("tau_m_ms", "first"), spont_hz=("spont_hz", "mean"), on_hz=("on_hz", "mean"),
            on_sd=("on_hz", "std"), early_hz=("early_hz", "mean"), late_hz=("late_hz", "mean"),
            sag_frac=("sag_frac", "mean")).reset_index())
agg["adapt_late_over_early"] = agg.late_hz / agg.early_hz.where(agg.early_hz > 0)
agg["label"] = "measured (Azevedo 2020 Dryad, authors' spike detections); ratios derived"
agg.round(4).to_csv(OUT, index=False)
pd.set_option("display.width", 220)
print(agg.drop(columns="label").round(2).to_string(index=False))
