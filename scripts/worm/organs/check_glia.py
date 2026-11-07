"""Row 11 unit check: amphid K+ buffering against the mammalian Kir4.1 recovery (bar in the worgans night file).

A brain of the 24 amphid neurons, the RMEs, CEPs, RIPR and the 11 head muscles GLR touches (BAAIWorm membranes,
Cook wiring, the code's default toggles) with wormemu.mech.glia registered; the default observation; dt 5 ms.
3 s free, the 12 left amphid somas voltage-clamped to -40 mV for 1 s (SEClamp, released by a huge series
resistance), 20 s free. Wild type, then glia_kbuffer=null.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/organs/check_glia.py OUT.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from wormemu import mech  # noqa: E402

if "glia" not in mech.REGISTRY:
    mech.REGISTRY.append("glia")

from wormemu.brain import Brain  # noqa: E402
from wormemu.brain_layers import AMPHID  # noqa: E402
from wormemu.mech import glia as gl  # noqa: E402

MUSCLES = ["dBWML1", "dBWML2", "dBWML4", "dBWML5", "dBWML6", "dBWMR1", "dBWMR4", "dBWMR5", "dBWMR6", "dBWMR7",
           "vBWML1"]
CELLS = sorted(AMPHID) + ["RMEL", "RMER", "RMED", "RMEV", "CEPDL", "CEPDR", "CEPVL", "CEPVR", "RIPR"] + MUSCLES
DT = 5.0
T_ON, T_OFF, T_END = 3000.0, 4000.0, 24000.0
OFF_RS = 1e9                                            # MOhm: the clamp passes < 1e-7 nA


def run(toggles, label):
    b = Brain(cells=CELLS, toggles=toggles)
    b.reset()
    m = next(x for x in b.mechs if isinstance(x, gl.Mech))
    left = [b.idx[c] for c in sorted(AMPHID) if c.endswith("L") and c in b.idx]
    cl = []
    for i in left:
        c = b.h.SEClamp(b.soma[i](0.5))
        c.dur1, c.amp1, c.rs = 1e9, -40.0, OFF_RS
        cl.append(c)
    rows, vdep, w0 = [], [], time.time()
    while b.t < T_END:
        on = T_ON <= b.t < T_OFF
        for c in cl:
            c.rs = 0.01 if on else OFF_RS
        o = b.step(None, DT)
        mo = b.mech_out
        rows.append((b.t, *mo["amphid_k_mM"], *mo["amphid_ek_shift_mV"],
                     min(mo["afd_gc_scale"].values()), max(mo["afd_gc_scale"].values())))
        vdep.append(float(np.mean(o.v_mV[left])))
    r = np.array(rows)
    t, kl, kr = r[:, 0], r[:, 1] - m.q["glia_k_bath_mM"], r[:, 2] - m.q["glia_k_bath_mM"]
    i = int(np.argmax(kl))
    after = kl[i:] / kl[i] if kl[i] > 0 else np.zeros(1)
    j = int(np.argmax(after < np.exp(-1.0))) if (after < np.exp(-1.0)).any() else None
    vdep = np.array(vdep)
    pre = vdep[(t > T_ON - 1000) & (t <= T_ON)].mean()
    dur = vdep[(t > T_ON + 100) & (t <= T_OFF)].mean()
    print(f"  {label}: peak dK_L {kl[i]:.3f} mM at {t[i] / 1000:.2f} s, wall {time.time() - w0:.0f} s", flush=True)
    return {"peak_dk_left_mM": float(kl[i]), "t_peak_s": float(t[i] / 1000.0),
            "tau_recovery_s": float((t[i + j] - t[i]) / 1000.0) if j else None,
            "peak_dk_right_mM": float(kr.max()), "ek_shift_max_mV": float(r[:, 3].max()),
            "left_v_pre_mV": float(pre), "left_v_clamp_mV": float(dur),
            "afd_gc_scale_min": float(r[:, 5].min()), "afd_gc_scale_max": float(r[:, 6].max()),
            "glia_v_mV": [float(x) for x in b.mech_out.get("glia_v_mV", [])], "n_gap_glia": m.n_gap,
            "wall_s": time.time() - w0}


def main():
    out = Path(sys.argv[1])
    res = {"dt_ms": DT, "wt": run({}, "wt")}
    out.write_text(json.dumps(res, indent=1))
    res["null"] = run({"glia_kbuffer": "null"}, "null")
    w, z = res["wt"], res["null"]
    s = {"peak": 0.2 <= w["peak_dk_left_mM"] <= 12.0,
         "tau": w["tau_recovery_s"] is not None and 0.7 <= w["tau_recovery_s"] <= 6.3,
         "null_slower": bool(w["tau_recovery_s"] and z["tau_recovery_s"]
                             and z["tau_recovery_s"] >= 1.2 * w["tau_recovery_s"]),
         "sides": w["peak_dk_right_mM"] < 0.1 * w["peak_dk_left_mM"]}
    s["pass"] = all(s.values())
    res["score"] = s
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
