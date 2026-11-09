"""Row 11 unit check: amphid K+ buffering against the mammalian Kir4.1 recovery (bar in the worgans night file).

A brain of the 24 amphid neurons, the RMEs, CEPs, RIPR and the 11 head muscles GLR touches (BAAIWorm membranes,
Cook wiring, the code's default toggles) with wormemu.mech.glia registered; the default observation; dt 5 ms.
3 s free, the 12 left amphid somas voltage-clamped to -40 mV for 1 s (SEClamp, released by a huge series
resistance), 20 s free. Wild type, then glia_kbuffer=null.

8 Nov 2026 (wbody2 item 8, E; DEBUG_TRIAGE line 4). No C. elegans measurement of K+ at the amphid endings or of
glial K+ clearance exists: Ray et al. 2024 Cell Rep (PMC11296322, opened): "direct assessment of K+ or Cl- levels or
dynamic cell volume at these glia-NRE subcompartments is currently technically limited"; searches in
docs/worm/night/wbody2/lit_glia_k.md. So every bar is cross-species, and each now cites what its opened source says.
Bars (written before re-running; the old four are still reported as score_old):
  ceiling  the left endings' peak K+ (absolute) <= 10.2 mM: Heinemann & Lux 1977 Brain Res 120:231 (PMID 832122,
           abstract opened), maximal extracellular K+ activity 10.2 mequiv/l in cat somatosensory cortex under
           repetitive stimulation; a level, not a rise (the old bar read it as a 12 mM rise "from memory"); and a
           rise over the pre-clamp baseline of at least 0.01 mM so the recovery is defined (a readout floor: the old
           0.2 mM floor had no source).
  tau      1/e recovery of the excess over the pre-clamp baseline (mean K+ over the 1 s before the clamp; the old
           check measured from the bath, which counts any drift of the baseline as recovery) within 3.4-4.0 s:
           Sibille, Dao Duc, Holcman & Rouach 2015 PLoS Comput Biol 11:e1004137 (PMC4380507, opened), single
           exponential fits to the [K+]o decay of a mouse hippocampal neuron-astrocyte model, 3.4 s after a single
           stimulus and 4 s after a tetanus (Fig. 4B, F; simulated, not recorded).
  null     the null recovers at least 1.24x slower: the same figure, Kir4.1 inhibited 4.2 s and 6 s (ratios 1.24
           and 1.5; the old 6.3 / 4.2 pair is not in the paper).
  sides    dropped from the pass (no source). The left and right amphids are separate organs, each with its own
           sheath (WormAtlas, after Perkins et al. 1986); the module holds one K+ compartment per side with no term
           between them (tests/test_worm_glia_sides.py), so a right-side rise here is the right neurons' own
           depolarisation through the network. right/left is reported.
Reported, not barred: the K+ baseline at the clamp against the bath, the clearance the constants alone give
(1 / (1/kir + 1/diff)) and the K+ trace (every 50 ms).

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
    kb = m.q["glia_k_bath_mM"]
    t, kl, kr = r[:, 0], r[:, 1] - kb, r[:, 2] - kb
    pre_w = (t > T_ON - 1000) & (t <= T_ON)
    base_l, base_r = float(r[pre_w, 1].mean()), float(r[pre_w, 2].mean())
    i = int(np.argmax(kl))
    ex = r[i:, 1] - base_l
    j = int(np.argmax(ex < np.exp(-1.0) * ex[0])) if ex[0] > 0 and (ex < np.exp(-1.0) * ex[0]).any() else None
    after = kl[i:] / kl[i] if kl[i] > 0 else np.zeros(1)
    j_old = int(np.argmax(after < np.exp(-1.0))) if (after < np.exp(-1.0)).any() else None
    vdep = np.array(vdep)
    pre = vdep[pre_w].mean()
    dur = vdep[(t > T_ON + 100) & (t <= T_OFF)].mean()
    q = m.q
    kk = 1.0 / q["glia_k_diff_tau_s"] + (1.0 / q["glia_kir_tau_s"] if m.kb == "kir" else 0.0)
    print(f"  {label}: peak K_L {r[i, 1]:.3f} mM (base {base_l:.3f}) at {t[i] / 1000:.2f} s, wall {time.time() - w0:.0f} s",
          flush=True)
    keep = slice(None, None, max(1, int(round(50.0 / DT))))
    return {"peak_k_left_mM": float(r[i, 1]), "peak_dk_left_mM": float(kl[i]), "t_peak_s": float(t[i] / 1000.0),
            "base_k_left_mM": base_l, "base_k_right_mM": base_r, "bath_mM": kb,
            "rise_over_base_left_mM": float(r[i, 1] - base_l),
            "tau_recovery_s": float((t[i + j] - t[i]) / 1000.0) if j else None,
            "tau_recovery_from_bath_s": float((t[i + j_old] - t[i]) / 1000.0) if j_old else None,
            "tau_constants_alone_s": 1.0 / kk,
            "peak_dk_right_mM": float(kr.max()), "rise_over_base_right_mM": float(r[:, 2].max() - base_r),
            "ek_shift_max_mV": float(r[:, 3].max()),
            "left_v_pre_mV": float(pre), "left_v_clamp_mV": float(dur),
            "afd_gc_scale_min": float(r[:, 5].min()), "afd_gc_scale_max": float(r[:, 6].max()),
            "glia_v_mV": [float(x) for x in b.mech_out.get("glia_v_mV", [])], "n_gap_glia": m.n_gap,
            "trace": {"t_s": (t[keep] / 1000.0).tolist(), "k_left_mM": r[keep, 1].tolist(),
                      "k_right_mM": r[keep, 2].tolist(), "v_left_mean_mV": vdep[keep].tolist()},
            "wall_s": time.time() - w0}


def main():
    out = Path(sys.argv[1])
    res = {"dt_ms": DT, "wt": run({}, "wt")}
    out.write_text(json.dumps(res, indent=1))
    res["null"] = run({"glia_kbuffer": "null"}, "null")
    w, z = res["wt"], res["null"]
    so = {"peak": 0.2 <= w["peak_dk_left_mM"] <= 12.0,
          "tau": w["tau_recovery_from_bath_s"] is not None and 0.7 <= w["tau_recovery_from_bath_s"] <= 6.3,
          "null_slower": bool(w["tau_recovery_from_bath_s"] and z["tau_recovery_from_bath_s"]
                              and z["tau_recovery_from_bath_s"] >= 1.2 * w["tau_recovery_from_bath_s"]),
          "sides": w["peak_dk_right_mM"] < 0.1 * w["peak_dk_left_mM"]}
    so["pass"] = all(so.values())
    s = {"ceiling": w["peak_k_left_mM"] <= 10.2 and w["rise_over_base_left_mM"] >= 0.01,
         "tau": w["tau_recovery_s"] is not None and 3.4 <= w["tau_recovery_s"] <= 4.0,
         "null_slower": bool(w["tau_recovery_s"] and z["tau_recovery_s"]
                             and z["tau_recovery_s"] >= 1.24 * w["tau_recovery_s"])}
    s["pass"] = all(s.values())
    res["score"], res["score_old"] = s, so
    res["right_over_left"] = w["rise_over_base_right_mM"] / w["rise_over_base_left_mM"] \
        if w["rise_over_base_left_mM"] > 0 else None
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "trace"} if isinstance(v, dict) else v)
                      for k, v in res.items()}, indent=1))


if __name__ == "__main__":
    main()
