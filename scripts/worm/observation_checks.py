"""Row 23 checks (src/wormemu/mech/observation.py). Bars written before running (6 Nov 2026, 21:44):

1. GCaMP, sanity (the parameters are the measurements, so no independent isolated measurement is reproduced):
   for each variant, (a) the steady state at Ca = Kd is B = 0.5 within 1e-9; (b) after Ca is held at 10 uM for 50 ms
   and returned to rest, dF/F falls from its value at the return to half of it in t_half within 5 %.
2. Opto, neutral: with SCHEDULE empty, and with a schedule at intensity 0, every cell's v equals the run without
   the module (registry without observation, gcamp lumped) to 0.0 mV over 2 s. Sanity: a 0.5 s pulse on AVAL at
   0.5 s raises AVAL's v by > 1 mV at the end of the pulse.
3. NeuroPAL, sanity: at the template, the unlabelled fraction is 0.3 +/- 0.06 and the correct fraction of
   labelled neurons 0.9 +/- 0.05 (302 neurons, binomial 2 SD).
4. Gait features, sanity against metaworm.gait on the published travelling wave (row 21's upstream run): bend
   frequency within one FFT bin of the drive (1.76 Hz), wavelength within 10 % of gait()'s, speed the same sign
   and within 25 % (different definitions: instantaneous midbody velocity vs whole-period centroid displacement).
Writes docs/worm/night/wbody/observation_row23.json.
"""
from __future__ import annotations

import json
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.mech import observation as ob  # noqa: E402

DOC = ROOT / "docs" / "worm" / "night" / "wbody" / "observation_row23.json"
WBODY = ["temperature", "senses_chem", "senses_touch", "senses_proprio"]


def gcamp_checks():
    res = {}
    dt = 0.5
    for v in ob.VARIANTS:
        kd, n, R, th = (ob.P[f"obs_{v}_{k}"] for k in ("kd_nM", "hill", "range", "thalf_ms"))
        a = ob.binding_step(0.0, kd, kd, n, th, 1e7)
        B0 = ob.hill(ob.P["obs_ca_rest_nM"], kd, n)
        B, t, tr = B0, 0.0, []
        while t < 50 + 6 * th:
            c = 1e4 if t < 50 else ob.P["obs_ca_rest_nM"]
            B = ob.binding_step(B, c, kd, n, th, dt)
            t += dt
            tr.append((t, ob.dff(B, B0, R)))
        tr = np.array(tr)
        i0 = np.searchsorted(tr[:, 0], 50.0)
        y0 = tr[i0, 1]
        k = i0 + np.argmax(tr[i0:, 1] <= y0 / 2)
        t_half = tr[k, 0] - tr[i0, 0]
        res[v] = {"B_at_kd": float(a), "dff_peak": float(tr[:, 1].max()), "t_half_ms": float(t_half),
                  "t_half_spec_ms": th, "pass": bool(abs(a - 0.5) < 1e-9 and abs(t_half / th - 1) < 0.05)}
    return res


def _child(cfg):
    from wormemu import mech
    from wormemu.brain import Brain, sample_worm
    from wormemu.interface import default_observation
    mech.REGISTRY[:] = [m for m in mech.REGISTRY if m not in WBODY + ["observation"]] + cfg["registry"]
    ob.SCHEDULE[:] = [tuple(s) for s in cfg["schedule"]]
    b = Brain(sample_worm(None), toggles=cfg["toggles"])
    b.reset()
    V, G, opto = [], [], []
    n = int(cfg["seconds"] * 1000 / 4.0)
    for _ in range(n):
        out = b.step(default_observation(b.t), 4.0)
        V.append(out.v_mV.copy())
        G.append(np.asarray(out.gcamp_dff if out.gcamp_dff is not None else np.zeros(len(b.cell_names))).copy())
        opto.append(float(b.mech_out.get("opto_g_nS", 0.0)))
    ids = b.mech_out.get("neuropal_id")
    r = dict(V=np.array(V), G=np.array(G), opto=np.array(opto), names=b.cell_names,
             ids=None if ids is None else np.asarray(ids), is_muscle=np.asarray(b.is_muscle))
    sys.stdout.buffer.write(pickle.dumps(r))


def _spawn(cfg):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, __file__, "_child", json.dumps(cfg)], capture_output=True, env=env)
    assert r.returncode == 0, r.stderr.decode()[-3000:]
    return pickle.loads(r.stdout)


def brain_checks():
    res = {}
    base = _spawn(dict(registry=WBODY, toggles={}, schedule=[], seconds=2.0))
    empty = _spawn(dict(registry=WBODY + ["observation"], toggles={"gcamp": "lumped"}, schedule=[], seconds=2.0))
    zero = _spawn(dict(registry=WBODY + ["observation"], toggles={"gcamp": "lumped"},
                       schedule=[["AVAL", 500.0, 500.0, 0.0]], seconds=2.0))
    pulse = _spawn(dict(registry=WBODY + ["observation"], toggles={}, schedule=[["AVAL", 500.0, 500.0, 1.0]],
                        seconds=2.0))
    i = base["names"].index("AVAL")
    k_end = int(1000 / 4.0) - 1
    res["opto_neutral_empty_max_dv"] = float(np.abs(empty["V"] - base["V"]).max())
    res["opto_neutral_zero_max_dv"] = float(np.abs(zero["V"] - base["V"]).max())
    res["opto_aval_dv_end_of_pulse_mV"] = float(pulse["V"][k_end, i] - base["V"][k_end, i])
    res["opto_aval_g_peak_nS"] = float(pulse["opto"].max())
    res["gcamp6s_aval_dff_end_of_pulse"] = float(pulse["G"][k_end, i])
    res["gcamp6s_aval_dff_pre"] = float(pulse["G"][int(500 / 4.0) - 1, i])
    res["gcamp_lumped_vs_brain_layers_max_diff_shifted"] = None   # noise draws interleave with other layers
    res["opto_pass"] = bool(res["opto_neutral_empty_max_dv"] == 0.0 and res["opto_neutral_zero_max_dv"] == 0.0
                            and res["opto_aval_dv_end_of_pulse_mV"] > 1.0)
    neur = ~pulse["is_muscle"]
    ids = pulse["ids"][neur]
    own = np.flatnonzero(neur)
    lab = ids >= 0
    res["neuropal_unlabelled_frac"] = float(1 - lab.mean())
    res["neuropal_correct_frac_of_labelled"] = float((ids[lab] == own[lab]).mean())
    res["neuropal_pass"] = bool(abs(res["neuropal_unlabelled_frac"] - 0.3) <= 0.06
                                and abs(res["neuropal_correct_frac_of_labelled"] - 0.9) <= 0.05)
    res["finite"] = bool(all(np.isfinite(r["V"]).all() and np.isfinite(r["G"]).all() for r in (empty, zero, pulse)))
    return res


def gait_checks():
    from wormemu.body import metaworm as mw
    rec = mw.load(str(ROOT / "runs" / "worm" / "night_wbody" / "layers_upstream"))
    fr = mw.Frame(rec["meta"], rec["X"][0])
    w = rec["t"] >= 1.0
    sub = {**rec, "X": rec["X"][w], "t": rec["t"][w]}
    f = ob.gait_features(sub, fr)
    g = mw.gait(rec, 1.76, 1.0, fr)
    df = 1.0 / (sub["t"][-1] - sub["t"][0])
    res = {"features": f, "gait": {k: g[k] for k in ("f_body_hz", "wavelength_L", "speed_L_s")}, "fft_bin_hz": df}
    res["pass"] = bool(abs(f["bend_freq_hz"] - 1.76) <= df and abs(f["wavelength_L"] / g["wavelength_L"] - 1) <= 0.1
                       and np.sign(f["speed_mean_L_s"]) == np.sign(g["speed_L_s"])
                       and abs(f["speed_mean_L_s"] / g["speed_L_s"] - 1) <= 0.25)
    return res


def main(which):
    res = json.load(open(DOC)) if DOC.exists() else {}
    t = time.time()
    if "gcamp" in which:
        res["gcamp"] = gcamp_checks()
    if "gait" in which:
        res["gait"] = gait_checks()
    if "brain" in which:
        res["brain"] = brain_checks()
    res["wall_s_last"] = time.time() - t
    DOC.parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(DOC, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "_child":
        _child(json.loads(sys.argv[2]))
    else:
        main(sys.argv[1:] or ["gcamp", "gait", "brain"])
