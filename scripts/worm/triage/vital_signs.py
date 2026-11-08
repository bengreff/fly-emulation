"""Item 5 (wtriage, 8 Nov 2026; current values, no generator, nothing tuned): the whole brain's vital signs as built.

Pre-registered (before the first run): the template worm at the ledger values (at_ledger.patch, sample_worm(None)),
the code's default toggles (every registered module, organs included), brain only (no body, no food, no odour:
step(None), dt 1 ms), 120 bio s from reset. Recorded and reported against the published range, not scored:
  pumping        completed pumps (organs_pharynx's own count) -> Hz. On food 3.46 +- 0.19 Hz after a 2 h fast
                 (Hiebert et al. 2017, PMC7255878); this run has no food, so lower is expected.
  defecation     expulsions (organs_intestine's own count) and int9's Ca peaks (> 0.3 uM, >= 10 s apart) -> period.
                 45-50 s at 20 C (PMC2409367).
  body wall      the 95 BWM somata: median voltage over the run, and spikes (upward crossings of -10 mV, the
                 threshold Gao & Zhen 2011 give) per muscle per s. Dissected muscle: rest -25.0 +- 1.0 mV, spontaneous
                 APs 0.73 +- 0.14 Hz in about half the recordings (Gao & Zhen 2011 PNAS 108:2557).
                 [corrected 14:38, the bar unchanged: rest n = 27; spontaneous APs in ~80% of preparations, not half
                 (PMC3038695, opened 14:37)]
  egg-laying     eggs laid (needs hours; row 15 says HSN is silent, so 0 is expected in 2 min).
  neurons        the fraction of the 302 above -20 mV and the median voltage, every 50 ms (no published bar).
Conditions: default, and mask_off (expression_map off) as the item-3 cause diagnostic.

Usage (backhouse): python vital_signs.py CONDITION [SECONDS]
Output: runs/worm/triage/vital_signs/CONDITION.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402
from wormemu.interface import BWM_NAMES  # noqa: E402


def peaks(t, x, thr, gap_s):
    out, last = [], -1e9
    for k in range(1, len(x) - 1):
        if x[k] > thr and x[k] >= x[k - 1] and x[k] > x[k + 1] and t[k] - last >= gap_s:
            out.append(float(t[k]))
            last = t[k]
    return out


def main():
    cond = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    tog = {"expression_map": "off"} if cond == "mask_off" else {}
    b = B.Brain(B.sample_worm(None), toggles=tog)
    neur = ~b.is_muscle
    bwm = np.array([b.idx[n] for n in BWM_NAMES if n in b.idx])
    b.reset()
    n = int(round(secs * 1000))
    pumps = eggs = exps = 0
    spikes = np.zeros(len(bwm))
    prev = None
    ts, hi, med, int9, bwm_v, act = [], [], [], [], [], []
    t0 = time.time()
    for k in range(n):
        o = b.step(None, 1.0)
        pumps += int(o.pumps)
        eggs += int(o.eggs_laid)
        exps += int(o.expulsions)
        vb = o.v_mV[bwm]
        if prev is not None:
            spikes += (prev < -10.0) & (vb >= -10.0)
        prev = vb
        if k % 50 == 0:
            v = o.v_mV[neur]
            ts.append(k / 1000.0)
            hi.append(float((v > -20).mean()))
            med.append(float(np.median(v)))
            c = b.mech_out.get("intestine_ca_uM")
            int9.append(float(np.max(c)) if c is not None else np.nan)
            bwm_v.append(float(np.median(vb)))
            act.append(float(np.mean(o.muscle_activation)))
    ts = np.array(ts)
    pk = peaks(ts, np.array(int9), 0.3, 10.0)
    out = dict(condition=cond, seconds=secs, wall_per_bio_s=(time.time() - t0) / secs,
               pumps=pumps, pump_hz=pumps / secs, eggs=eggs, expulsions=exps,
               int_ca_peaks_s=pk, dmp_period_s=float(np.mean(np.diff(pk))) if len(pk) > 1 else None,
               int_ca_max_uM=float(np.nanmax(int9)), int_ca_min_uM=float(np.nanmin(int9)),
               bwm_median_v=float(np.median(bwm_v)), bwm_spike_hz_mean=float(spikes.mean() / secs),
               bwm_frac_spiking=float((spikes > 0).mean()), bwm_act_mean=float(np.mean(act)),
               neur_frac_above_m20_mean=float(np.mean(hi)), neur_frac_above_m20_max=float(np.max(hi)),
               neur_median_v=float(np.median(med)),
               trace=dict(t=ts[::20].tolist(), frac_hi=hi[::20], int_ca=int9[::20], bwm_v=bwm_v[::20]))
    p = ROOT / "runs/worm/triage/vital_signs" / f"{cond}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v for k, v in out.items() if k != "trace"}, default=float), flush=True)


if __name__ == "__main__":
    main()
