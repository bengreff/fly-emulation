"""Extract physiology targets from Azevedo et al. 2020 Dryad cell 180111_F2_C1
(slow tibia flexor MN, R35C09-Gal4; whole-cell current clamp, 10 kHz).

Uses the authors' own spike detections (`spikes`, sample indices) and only
trials with excluded == 0. Units: piezo command in V; 1 V = 6 um of probe
travel (Azevedo Methods: 60 um = 8 deg), so 0.8 deg per V; positive
displacement = flexion (Methods: "flexion (+) and extension (-)"), confirmed
by the probe monitor (sgsmonitor) and by the resistance-reflex sign.

Outputs data/derived/azevedo2020_slow_mn_180111.csv (one row per condition)
and a JSON summary. All values measured (single cell); derived where a
transformation is stated (deg from V; Rin from dV/dI).

    uv run python scripts/azevedo_slow_mn.py [--cell 181021_F1_C1]

The cell's zip must be unpacked in data/raw/azevedo2020/<cell>/ or directly in
data/raw/azevedo2020/ (the session-6b layout for 180111_F2_C1).
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/azevedo2020"
FS = 1e4
DEG_PER_V = 0.8


CELL = "180111_F2_C1"


def load(pattern):
    out = []
    base = RAW / CELL if (RAW / CELL).is_dir() else RAW
    for f in sorted(glob.glob(str(base / pattern.replace("*.mat", f"{CELL}_*.mat")))):
        d = sio.loadmat(f, squeeze_me=True, struct_as_record=False)
        if d.get("excluded", 0):
            continue
        out.append(d)
    return out


def rate(spk, a, b, fs=None):
    s = np.atleast_1d(spk) / (fs or FS)
    return ((s >= a) & (s < b)).sum() / (b - a)


def main():
    import argparse
    global CELL
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", default=CELL)
    ap.add_argument("--intrinsic-only", action="store_true",
                    help="skip Piezo (reflex) trials, e.g. while they are sealed as held-out")
    args = ap.parse_args()
    CELL = args.cell
    rows = []
    spont = []
    # --- steps: pre 1.0 s, step 0.5 s, post 1.0 s ---------------------------
    for d in ([] if args.intrinsic_only else load("PiezoStep2T_Raw_*.mat")):
        p, s = d["params"], d["spikes"]
        fs = float(p.sampratein)
        r_ = lambda a, b: rate(s, a, b, fs)  # noqa: E731
        pre = r_(0.5, 1.0); spont.append(r_(0.0, 1.0))
        rows.append(dict(protocol="step", disp_deg=float(p.displacement) * DEG_PER_V,
                         start_deg=float(p.displacementOffset) * DEG_PER_V, speed_dps=np.nan,
                         pre_hz=pre, transient_hz=r_(1.0, 1.1), hold_hz=r_(1.1, 1.5),
                         post_hz=r_(1.6, 2.0)))
    # --- ramps: pre 0.5, stim 0.5 (ramp then hold), post 0.5 ----------------
    for d in ([] if args.intrinsic_only else load("PiezoRamp2T_Raw_*.mat")):
        p, s = d["params"], d["spikes"]
        fs = float(p.sampratein)
        r_ = lambda a, b: rate(s, a, b, fs)  # noqa: E731
        dur = abs(float(p.displacement)) / float(p.speed)       # s
        spont.append(r_(0.0, 0.5))
        rows.append(dict(protocol="ramp", disp_deg=float(p.displacement) * DEG_PER_V,
                         start_deg=float(p.displacementOffset) * DEG_PER_V,
                         speed_dps=float(p.speed) * DEG_PER_V, pre_hz=r_(0.25, 0.5),
                         transient_hz=r_(0.5, 0.5 + max(dur, 0.05)),
                         hold_hz=r_(0.5 + dur + 0.05, 1.0), post_hz=r_(1.1, 1.5)))
    df = pd.DataFrame(rows, columns=["protocol", "disp_deg", "start_deg", "speed_dps", "pre_hz",
                                     "transient_hz", "hold_hz", "post_hz"])
    cond = (df.groupby(["protocol", "disp_deg", "start_deg", "speed_dps"], dropna=False)
            .agg(n=("pre_hz", "size"), pre_hz=("pre_hz", "mean"),
                 transient_hz=("transient_hz", "mean"), hold_hz=("hold_hz", "mean"),
                 post_hz=("post_hz", "mean"), hold_sd=("hold_hz", "std")).reset_index())
    cond["d_transient_hz"] = cond.transient_hz - cond.pre_hz
    cond["d_hold_hz"] = cond.hold_hz - cond.pre_hz
    # --- current steps: pre 0.5 s, step 0.5-1.0 s ----------------------------
    fi, rin, spont_cs, taus = [], [], [], []
    for d in load("CurrentStep2T_Raw_*.mat"):
        p = d["params"]
        if "spikes" not in d:
            continue
        stim = float(p.stimDurInSec)
        fs = float(p.sampratein)
        v, c = d["voltage_1"], d["current_1"]
        t = np.arange(len(v)) / fs
        pre, on = (t >= 0.2) & (t < 0.5), (t >= 0.7) & (t < 0.5 + stim)
        dI = np.median(c[on]) - np.median(c[pre])
        spont_cs.append(rate(d["spikes"], 0, 0.5, fs))
        fi.append(dict(step_pA=float(p.step), dI_pA=dI, rate_pre=rate(d["spikes"], 0, 0.5, fs),
                       rate_on=rate(d["spikes"], 0.55, 0.5 + stim, fs)))
        if p.step < 0:
            rin.append((np.median(v[on]) - np.median(v[pre])) / dI * 1000.0)   # mV/pA -> GOhm*1000
            from scipy.optimize import curve_fit
            k = int(fs / FS)
            i0 = int(0.5 * fs); seg = v[i0 + 10 * k:i0 + 800 * k:k]; tt = np.arange(len(seg)) / FS + 10 / FS
            try:
                pp, _ = curve_fit(lambda x, a, b, tau: a + (b - a) * np.exp(-x / tau), tt, seg,
                                  p0=(seg[-1], seg[0], 0.02), maxfev=5000)
                if 0.001 < pp[2] < 0.2:
                    taus.append(pp[2] * 1000)
            except Exception:  # noqa: BLE001
                pass
    fi = pd.DataFrame(fi)
    fic = fi.groupby("step_pA").agg(n=("rate_on", "size"), dI_pA=("dI_pA", "mean"),
                                     rate_pre=("rate_pre", "mean"), rate_on=("rate_on", "mean"),
                                     sd=("rate_on", "std")).reset_index()
    tag = CELL.split("_")[0]
    out = ROOT / f"data/derived/azevedo2020_slow_mn_{tag}{'_intrinsic' if args.intrinsic_only else ''}.csv"
    cond.round(3).to_csv(out, index=False)
    summary = {
        "cell": f"{CELL} (R35C09 slow tibia flexor MN)",
        "spontaneous_hz": [round(float(np.mean(spont or spont_cs)), 1), round(float(np.std(spont or spont_cs)), 1),
                           len(spont or spont_cs)],
        "spontaneous_source": "piezo pre-windows" if spont else "current-step pre-windows",
        "tau_m_ms": [round(float(np.median(taus)), 1) if taus else None, len(taus)],
        "input_resistance_MOhm": [round(float(np.median(rin)), 0), round(float(np.std(rin)), 0), len(rin)],
        "f_I": fic.round(2).to_dict("records"),
    }
    (ROOT / f"data/derived/azevedo2020_slow_mn_{tag}{'_intrinsic' if args.intrinsic_only else ''}.json").write_text(json.dumps(summary, indent=1))
    pd.set_option("display.width", 200)
    print(cond.round(1).to_string(index=False))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
