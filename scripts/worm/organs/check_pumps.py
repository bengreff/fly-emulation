"""Row 27 unit check: Na+ recovery after a depolarisation, one neuron and one muscle, numpy (bar in the night file).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/organs/check_pumps.py OUT.json
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from wormemu.mech import metabolism as me  # noqa: E402
from wormemu.mech import pumps as pu  # noqa: E402

DT = 5.0
V_REST = np.array([-60.0, -31.0])                   # neuron, body-wall muscle (Du 2025 rest)
T_ON, T_OFF, T_END = 2000.0, 12000.0, 72000.0


def run(form):
    m = pu.Mech(None, {}, {"na_k_pump": form})
    t, na, I, atp = [], [], [], []
    k = 0
    while k * DT < T_END:
        tt = k * DT
        v = V_REST + (20.0 if T_ON <= tt < T_OFF else 0.0)
        r = m.step(SimpleNamespace(v=v, is_muscle=np.array([False, True])), DT)
        o = r["out"]
        t.append(tt + DT)
        na.append(o["na_i_mM"].copy())
        I.append(np.asarray(o["pump_current_pA"]).copy())
        atp.append(o["pump_atp_J_per_d"])
        k += 1
    return np.array(t), np.array(na), np.array(I), np.array(atp), m


def tau(t, x, t_from):
    i = int(np.searchsorted(t, t_from))
    ex = x[i:] - x[0]
    j = int(np.argmax(ex))
    after = ex[j:] / ex[j]
    k = int(np.argmax(after < np.exp(-1.0))) if (after < np.exp(-1.0)).any() else None
    return (float(t[i + j + k] - t[i + j]) / 1000.0 if k else None), float(ex[j])


def main():
    out = Path(sys.argv[1])
    q = pu.defaults()
    t, na, I, atp, m = run("on")
    tn, nan_, In, _, mn = run("null")
    rest = (t > q["pump_v0_ms"]) & (t <= T_ON)
    tau_n, pk_n = tau(t, na[:, 0], T_OFF - DT)
    tau_m, pk_m = tau(t, na[:, 1], T_OFF - DT)
    after = (t > T_OFF) & (t <= T_OFF + 10000.0)
    ip_rest = m.ip_rest
    # whole-worm cost at rest: 302 neurons, 95 body-wall muscles at these resting levels, vs the DEB day-1 adult
    p = pu.Pump(q, np.r_[np.zeros(302, bool), np.ones(95, bool)])
    ip_all = p.i_p(np.full(397, q["pump_na_rest_mM"]), np.r_[np.full(302, -60.0), np.full(95, -31.0)])
    met = me.Mech(SimpleNamespace(layers=None), {}, {"met_feeding": "fixed"})
    _, fl = met.deb.fluxes(met.y, 1.0)
    res = {"ip_rest_pA": [float(x) for x in ip_rest], "tau_na_neuron_s": tau_n, "tau_na_muscle_s": tau_m,
           "peak_dna_neuron_mM": pk_n, "peak_dna_muscle_mM": pk_m,
           "rest_I_max_abs_pA": float(np.abs(I[rest]).max()),
           "ahp_current_min_pA": [float(x) for x in I[after].min(axis=0)],
           "null_rest_I_pA": [float(x) for x in In[rest & (tn > q["pump_v0_ms"] + DT)].mean(axis=0)],
           "null_na_end_mM": [float(x) for x in nan_[-1]],
           "null_na_at_off_mM": [float(x) for x in nan_[int(np.searchsorted(tn, T_OFF)) - 1]],
           "worm_rest_atp_J_per_d": p.atp_J_per_d(ip_all), "deb_somatic_maint_J_per_d": float(fl["pS"]),
           "worm_rest_atp_fraction_of_maint": p.atp_J_per_d(ip_all) / float(fl["pS"])}
    s = {"tau_5_60": tau_n is not None and 5.0 <= tau_n <= 60.0, "rest_zero": res["rest_I_max_abs_pA"] < 1e-9,
         "null": bool(np.allclose(res["null_rest_I_pA"], ip_rest, rtol=1e-9)
                      and all(e > o for e, o in zip(res["null_na_end_mM"], res["null_na_at_off_mM"])))}
    s["pass"] = all(s.values())
    res["score"] = {k: bool(x) for k, x in s.items()}
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
