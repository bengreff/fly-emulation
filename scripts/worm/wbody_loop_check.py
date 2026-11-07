"""Everything-on closed loop with wbody's modules registered (night of 6 Nov 2026, wbody).

brain_loop_check.py (wbrain's) with the senses_* modules (and later wbody modules) appended to mech.REGISTRY in
this process, since REGISTRY itself is wbrain's file. Same summary, in runs/worm/night_wbody/LABEL.summary.json
(LABEL.json is the body's own run record, read by metaworm.load and the viewer; before 21:50 on 6 Nov the summary
overwrote it).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/wbody_loop_check.py SECONDS LABEL ['{"toggle": "value"}']
       [--modules=temperature,senses_chem,senses_touch,senses_proprio] [--env=standard|none]
--env=standard: the row 22 plate (body/environment.py, every field on) with environment.standard_events() (tap,
eyelash anterior and posterior, nose); none (the default) = the INTERFACE.md plate.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))

from brain_loop_check import Recorder, _summ  # noqa: E402
from wormemu import mech  # noqa: E402
from wormemu.brain import Brain, sample_worm  # noqa: E402
from wormemu.body import environment  # noqa: E402
from wormemu.body.loop import Body, run  # noqa: E402
from wormemu.body.metaworm import AGAR_FILM  # noqa: E402
from wormemu.body.scene import ChemotaxisScene  # noqa: E402

WBODY = ["temperature", "senses_chem", "senses_touch", "senses_proprio"]
HEAD = ("o2_pct", "co2_pct", "food_OD", "nacl_mM", "temperature_C", "diacetyl_uM")
PO = ("ALML", "AVM", "PLML", "PVDL", "ASHL", "DVA", "VB05", "URXL", "BAGL", "ASEL", "AFDL", "AWAL")


class Trace(Recorder):
    """Recorder plus what the world sent and a few sensory open probabilities, every step (row 22 exercise)."""

    def __init__(self, brain):
        super().__init__(brain)
        self.tr = []

    def step(self, obs, dt_ms):
        o = super().step(obs, dt_ms)
        mo = self.b.mech_out
        po = {**mo.get("sens_cng_po", {}), **mo.get("sens_trpv_po", {}), **mo.get("sens_touch_po", {}),
              **mo.get("sens_proprio_po", {})}
        self.tr.append([self.b.t, float(obs.tap), float(np.sum(obs.contact_force_uN)), float(obs.nose_force_uN)]
                       + [float(obs.head.get(c, np.nan)) for c in HEAD] + [float(po.get(c, np.nan)) for c in PO]
                       + [float(mo.get("temperature_C", np.nan))])
        return o


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mods = next((a.split("=", 1)[1].split(",") for a in sys.argv[1:] if a.startswith("--modules=")), WBODY)
    env_name = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--env=")), "none")
    env = environment.Environment(events=environment.standard_events()) if env_name == "standard" else None
    seconds, label = float(args[0]), args[1]
    tog = json.loads(args[2]) if len(args) > 2 else {}
    mech.REGISTRY[:] = [m for m in mech.REGISTRY if m not in mods] + mods
    out = ROOT / "runs" / "worm" / "night_wbody" / label
    out.parent.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    t0 = time.time()
    brain = Brain(sample_worm(None), toggles=tog)
    build_s = time.time() - t0
    rec = Trace(brain)
    body = Body(out, scene=ChemotaxisScene(field="cone_published"), frame_every=8, world=AGAR_FILM, env=env)
    meta = run(rec, body, seconds, brain_config={"seed": None, "toggles": dict(brain.toggles), "commit": commit},
               log_every_s=max(1.0, seconds / 5))
    ab = np.array(rec.above, float)
    last = ab[ab[:, 0] >= ab[-1, 0] - 2000.0, 1] if len(ab) else np.array([np.nan])
    res = dict(label=label, commit=commit, seconds=seconds, registry=list(mech.REGISTRY), env=env_name,
               head_end=body.obs.head, build_s=round(build_s, 1),
               loop_wall_s=round(meta["loop_wall_s"], 1), wall_per_bio_s=round(meta["loop_wall_s"] / seconds, 2),
               finite=rec.finite, max_abs_v_mV=round(rec.vmax, 1), max_activation=meta["max_activation"],
               neurons_above_m20_last2s=float(np.mean(last)), mechs=[type(m).__module__ for m in brain.mechs],
               toggles_on=sorted(k for k, v in brain.toggles.items() if v not in ("off", "none", False)),
               toggles_off=sorted(k for k, v in brain.toggles.items() if v in ("off", "none", False)),
               mech_out_trace=rec.mo[-3:], mech_out_end=_summ(brain.mech_out))
    tr = np.array(rec.tr)
    cols = ["t_ms", "tap", "contact_uN", "nose_uN"] + list(HEAD) + [f"po_{c}" for c in PO] + ["worm_T_C"]
    res["trace_cols"], res["trace_every_10"] = cols, tr[::10].round(5).tolist()
    np.save(out.parent / f"{label}.trace.npy", tr)
    (out.parent / f"{label}.summary.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: res[k] for k in ("label", "wall_per_bio_s", "finite", "max_abs_v_mV",
                                          "neurons_above_m20_last2s", "max_activation", "mechs")}, default=float))


if __name__ == "__main__":
    main()
