"""Resting Vm, Vm vs tibia angle, and spike-event rate of VNC interneurons,
from Agrawal et al. 2020 raw data (Zenodo 4307018, CC0; only the members
fetched to data/raw/agrawal2020/).

Raw Vm is NOT corrected for the 12 mV liquid junction potential (the paper
corrects post hoc); both raw and corrected (raw - 12) are reported.
Leg angle: 0 = fully flexed, 180 = fully extended (dataset description).
Spike events: peaks of Vm minus its 10 ms running median exceeding 1.0 mV and
0.5 ms wide or more, counted as a crude detector (label: derived, detector guessed).

    uv run python scripts/agrawal_vnc_ins.py
"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio
from scipy.ndimage import median_filter
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parents[1]
BINS = [0, 60, 90, 120, 150, 181]


def main():
    rows = []
    for f in sorted(glob.glob(str(ROOT / "data/raw/agrawal2020/*.mat"))):
        d = sio.loadmat(f, squeeze_me=True, struct_as_record=False)
        cls = Path(f).stem.split("_")[0]
        for k in range(len(np.atleast_1d(d["fly"]))):
            v = np.asarray(d["VoltageData"][k], float); fs = float(np.atleast_1d(d["samplerate"])[k])
            fr = np.asarray(d["FrametoSample"][k]); ang = np.asarray(d["LegAngles"][k], float)
            m = min(len(fr), len(ang)); fr, ang = fr[:m], ang[:m]
            ds = int(fs / 2000)                       # work at 2 kHz
            v2 = v[::ds]
            hp = v2 - median_filter(v2, size=21)
            pk, _ = find_peaks(hp, height=1.0, width=1)
            a_s = np.interp(np.arange(len(v2)) * ds, fr, ang, left=np.nan, right=np.nan)
            ok = np.isfinite(a_s)
            rec = dict(cls=cls, file=Path(f).name, cell=k, dur_s=round(len(v) / fs, 1),
                       vm_raw_median=round(float(np.median(v2)), 1),
                       vm_corr_median=round(float(np.median(v2)) - 12, 1),
                       vm_raw_p10_p90=[round(float(x), 1) for x in np.percentile(v2, [10, 90])],
                       spike_events_hz=round(len(pk) / (len(v2) / 2000), 1))
            for lo, hi in zip(BINS[:-1], BINS[1:]):
                sel = ok & (a_s >= lo) & (a_s < hi)
                rec[f"vm_{lo}-{hi}"] = round(float(np.median(v2[sel])), 1) if sel.sum() > 2000 else np.nan
                rec[f"ev_{lo}-{hi}"] = (round(float(np.isin(np.flatnonzero(sel), pk).sum() / (sel.sum() / 2000)), 1)
                                        if sel.sum() > 2000 else np.nan)
            rows.append(rec)
    df = pd.DataFrame(rows)
    out = ROOT / "data/derived/agrawal2020_vnc_interneurons.csv"
    df.to_csv(out, index=False)
    pd.set_option("display.width", 250)
    print(df.drop(columns=["file"]).to_string(index=False))


if __name__ == "__main__":
    main()
