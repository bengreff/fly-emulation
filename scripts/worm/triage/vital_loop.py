"""Item 5, challenge i (wtriage, 8 Nov 2026): the vital signs of the entire worm, closed loop, food on and off.

Pre-registered (8 Nov 15:00 CST, before the first run). Nothing is tuned and nothing is scored; the values are
reported against the same published ranges as vital_signs.py (the brain-only runs, now the preliminary):
  worm      the template worm at the ledger values (at_ledger.patch, sample_worm(None)), the code's default toggles
            (every registered module, organs included) plus wbody's modules as wbody_loop_check.py appends them
            (temperature, senses_chem, senses_touch, senses_proprio); the MetaWorm FEM body on the agar film
            (body.loop.run, the brain on its 0.5 ms grid).
  world     body/environment.py with every field at its default (lawn, O2, CO2, salt, temperature) and no events
            (no taps or touches). Conditions: food = env_food lawn (the worm starts 2 mm inside the lawn edge, the
            template); nofood = env_food off. Pumping is expected higher on food (Hiebert 2017: 3.46 +- 0.19 Hz).
  measures  as vital_signs.py: completed pumps, expulsions and int9 Ca peaks (> 0.3 uM, >= 10 s apart), eggs, the
            BWM somata's median voltage and -10 mV upward crossings per muscle per s, the fraction of the 302
            neurons above -20 mV; plus the body's centroid path length (mm), so the loop is seen to move.
  length    up to 150 bio s; the record is rewritten every 5 bio s, so a timeout keeps what ran.

Usage (backhouse): python vital_loop.py food|nofood [SECONDS]
Output: runs/worm/triage/vital_loop/COND.json
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
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "triage"))
import at_ledger  # noqa: E402

at_ledger.patch()
from brain_loop_check import Recorder  # noqa: E402
from vital_signs import peaks  # noqa: E402
from wormemu import mech  # noqa: E402
from wormemu.body import environment  # noqa: E402
from wormemu.body.loop import Body, run  # noqa: E402
from wormemu.body.metaworm import AGAR_FILM  # noqa: E402
from wormemu.body.scene import ChemotaxisScene  # noqa: E402
from wormemu.brain import Brain, sample_worm  # noqa: E402
from wormemu.interface import BWM_NAMES  # noqa: E402

WBODY = ["temperature", "senses_chem", "senses_touch", "senses_proprio"]


class Vitals(Recorder):
    def __init__(self, brain, cond, out_p):
        super().__init__(brain)
        self.cond, self.out_p, self.t0 = cond, out_p, time.time()
        self.bwm = np.array([brain.idx[n] for n in BWM_NAMES if n in brain.idx])
        self.pumps = self.eggs = self.exps = 0
        self.spikes = np.zeros(len(self.bwm))
        self.prev = None
        self.ts, self.hi, self.int9, self.bwm_v, self.head = [], [], [], [], []
        self.next_ms, self.next_dump = 0.0, 5000.0

    def step(self, obs, dt_ms):
        o = super().step(obs, dt_ms)
        self.pumps += int(o.pumps)
        self.eggs += int(o.eggs_laid)
        self.exps += int(o.expulsions)
        vb = o.v_mV[self.bwm]
        if self.prev is not None:
            self.spikes += (self.prev < -10.0) & (vb >= -10.0)
        self.prev = vb
        t = self.b.t
        if t >= self.next_ms:
            self.next_ms += 50.0
            self.ts.append(t / 1000.0)
            self.hi.append(float((o.v_mV[self.neur] > -20).mean()))
            c = self.b.mech_out.get("intestine_ca_uM")
            self.int9.append(float(np.max(c)) if c is not None else np.nan)
            self.bwm_v.append(float(np.median(vb)))
            if obs is not None:
                self.head.append([float(obs.head.get("food_OD", np.nan))])
        if t >= self.next_dump:
            self.next_dump += 5000.0
            self.dump()
        return o

    def dump(self):
        ts = np.array(self.ts)
        secs = float(ts[-1]) if len(ts) else 0.0
        pk = peaks(ts, np.array(self.int9), 0.3, 10.0)
        out = dict(condition=self.cond, bio_s=secs, wall_s=time.time() - self.t0, pumps=self.pumps,
                   pump_hz=self.pumps / secs if secs else None, eggs=self.eggs, expulsions=self.exps,
                   int_ca_peaks_s=pk, dmp_period_s=float(np.mean(np.diff(pk))) if len(pk) > 1 else None,
                   int_ca_max_uM=float(np.nanmax(self.int9)), bwm_median_v=float(np.median(self.bwm_v)),
                   bwm_spike_hz_mean=float(self.spikes.mean() / secs) if secs else None,
                   bwm_frac_spiking=float((self.spikes > 0).mean()),
                   neur_frac_above_m20_mean=float(np.mean(self.hi)), neur_frac_above_m20_max=float(np.max(self.hi)),
                   food_od_head_mean=float(np.nanmean(self.head)) if self.head else None,
                   finite=self.finite, toggles_on=sorted(k for k, v in self.b.toggles.items()
                                                         if v not in ("off", "none", False)),
                   trace=dict(t=ts[::20].tolist(), frac_hi=self.hi[::20], int_ca=self.int9[::20],
                              bwm_v=self.bwm_v[::20]))
        self.out_p.write_text(json.dumps(out, indent=1, default=float))
        return out


def main():
    cond = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
    mech.REGISTRY[:] = [m for m in mech.REGISTRY if m not in WBODY] + WBODY
    at_ledger.patch(WBODY)                              # wbody's modules at their ledger values too
    out = ROOT / "runs/worm/triage/vital_loop"
    out.mkdir(parents=True, exist_ok=True)
    env = environment.Environment(toggles={"env_food": "lawn" if cond == "food" else "off"}, events=[])
    brain = Brain(sample_worm(None), toggles={})
    rec = Vitals(brain, cond, out / f"{cond}.json")
    body = Body(out / cond, scene=ChemotaxisScene(field="cone_published"), frame_every=8, world=AGAR_FILM, env=env)
    meta = run(rec, body, secs, brain_config={"seed": None, "toggles": dict(brain.toggles), "commit": "wtriage"},
               log_every_s=max(1.0, secs / 10))
    res = rec.dump()
    res["path_mm"] = meta.get("path_mm")
    res["meta"] = {k: v for k, v in meta.items() if isinstance(v, (int, float, str, bool))}
    rec.out_p.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ("trace", "toggles_on")}, default=float), flush=True)


if __name__ == "__main__":
    main()
