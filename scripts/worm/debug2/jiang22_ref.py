"""CPU reference for Jiang et al. 2022's AVL model (Nat Commun 13:2783, PMC9120479; code github.com/taolab302/AVL-Modeling
@ d8303f3, MATLAB, no license file; read 9 Nov 2026). A line-by-line transcription of base/AVLModel.m with the 'wt' and
'exp-2(lf)' parameter sets of base/AVLParameters.m: one compartment, C 5 pF, conductances in nS, V in mV, t in ms,
I in pA. Their protocol (PlotWholeCellVoltage.m, set_constant_current_sequence.m): each sweep starts fresh from
V -60 mV with every gate 0 except EXP-2 in C1, the step runs from 1 s to the last 1 s.

  python scripts/worm/debug2/jiang22_ref.py [--set wt|exp-2(lf)|dvb] [--amps -4,-2,...] [--secs 7] [--out f.json]

--set dvb is wt with EXP-2 removed (g_EXP2 0, no compensation): Jiang's text, "no EXP-2 currents were detected in DVB"
(Discussion). A probe of the nearest published model, not a DVB fit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

WT = dict(C=5, g_L=0.27, v_Ca=100, v_K=-84, v_L=-60, g_NCA=0.02, v_Na=30,
          g_UNC2=1, m_a=0.1, m_b=25, m_c=10, m_d=0.4, m_e=-25, m_f=18,
          h_a=0.01, h_b=-50, h_c=10, h_d=0.03, h_e=-17, h_f=17,
          g_EGL19=0.75, s_1=2.9, s_2=-4.8, s_3=6.0, s_4=1.9, s_5=-8.6, s_6=30.0, s_7=2.3,
          s_8=0.4, s_9=44.6, s_10=-33.0, s_11=5.0, s_12=36.4, s_13=18.7, s_14=3.7, s_15=43.1,
          q_1=-4.4, q_2=7.5, q_3=1.43, q_4=14.9, q_5=12, q_6=0.14, q_7=5.96, q_8=-20.5, q_9=8.1, q_10=0.6,
          g_CCA1=0.25, c_1=-43.32, c_2=7.6, c_3=40.0, c_4=-62.5, c_5=-12.6, c_6=0.7,
          d_1=-58, d_2=7.0, d_3=280, d_4=-60.7, d_5=8.5, d_6=19.8,
          g_SHL1=4, v_1=-6.8, v_2=14.1, a_m=1.4, b_m=-17.5, c_m=12.9, d_m=-3.7, e_m=6.5, f_m=0.2,
          v_3=-33.1, v_4=8.3, a_hf=5.9, b_hf=-8.2, c_hf=2.9, d_hf=2.73, a_hs=84.2, b_hs=-7.7, c_hs=2.4, d_hs=11.9,
          g_EGL36=1.35, e_1=63, e_2=28.5, t_f=13, t_m=63, t_s=355,
          g_EXP2=3.1, p_1=0.0241, p_2=0.0408, p_3=0.0091, p_4=0.030, p_5=0.0372, p_6=0.31, p_7=0.0376,
          p_8=0.0472, p_9=0.0015, p_10=0.0703, p_11=0.2177, p_12=0.03, p_13=0.0313, p_14=0.1418,
          p_15=8.7204e-06, p_16=1.4011e-06)
SETS = {"wt": WT, "exp-2(lf)": {**WT, "g_SHL1": 4 * 1.35, "g_EGL36": 1.35 * 1.35, "g_EXP2": 0},
        "dvb": {**WT, "g_EXP2": 0}}
Y0 = [-60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]


def currents(V, y, p):
    """Each current (pA, + = outward) at state y."""
    (_, mU, hU, mE, hE, mC, hC, mS, hfS, hsS, mf36, mm36, ms36, _, _, _, O) = y
    return dict(unc2=p["g_UNC2"] * mU ** 2 * hU * (V - p["v_Ca"]),
                egl19=p["g_EGL19"] * mE * hE * (V - p["v_Ca"]),
                cca1=p["g_CCA1"] * mC ** 2 * hC * (V - p["v_Ca"]),
                shl1=p["g_SHL1"] * mS ** 3 * (0.7 * hfS + 0.3 * hsS) * (V - p["v_K"]),
                egl36=p["g_EGL36"] * (0.31 * mf36 + 0.36 * mm36 + 0.39 * ms36) * (V - p["v_K"]),
                exp2=p["g_EXP2"] * O * (V - p["v_K"]),
                nca=p["g_NCA"] * (V - p["v_Na"]), leak=p["g_L"] * (V - p["v_L"]))


def rhs(t, y, p, amp, t_on, t_off):
    V = y[0]
    E = np.exp
    I = amp if t_on <= t < t_off else 0.0
    dv = (I - sum(currents(V, y, p).values())) / p["C"]
    mU, hU, mE, hE, mC, hC, mS, hfS, hsS, mf36, mm36, ms36, C1, C2, C3, O = y[1:]
    Ii = 1 - C1 - C2 - C3 - O
    x = V - p["m_b"]
    ma = p["m_a"] * x / (1 - E(-x / p["m_c"])) if abs(x) > 1e-9 else p["m_a"] * p["m_c"]
    mb = p["m_d"] * E(-(V - p["m_e"]) / p["m_f"])
    ha = p["h_a"] * E(-(V - p["h_b"]) / p["h_c"])
    hb = p["h_d"] / (1 + E(-(V - p["h_e"]) / p["h_f"]))
    tmE = p["s_1"] * E(-((V - p["s_2"]) / p["s_3"]) ** 2) + p["s_4"] * E(-((V - p["s_5"]) / p["s_6"]) ** 2) + p["s_7"]
    thE = p["s_8"] * (p["s_9"] / (1 + E((V - p["s_10"]) / p["s_11"])) + p["s_12"] / (1 + E((V - p["s_13"]) / p["s_14"]))
                      + p["s_15"])
    miE = 1 / (1 + E(-(V - p["q_1"]) / p["q_2"]))
    hiE = (p["q_3"] / (1 + E(-(V - p["q_4"]) / p["q_5"])) + p["q_6"]) * \
          (p["q_7"] / (1 + E((V - p["q_8"]) / p["q_9"])) + p["q_10"])
    miC = 1 / (1 + E(-(V - p["c_1"]) / p["c_2"]))
    hiC = 1 / (1 + E((V - p["d_1"]) / p["d_2"]))
    tmC = p["c_3"] / (1 + E(-(V - p["c_4"]) / p["c_5"])) + p["c_6"]
    thC = p["d_3"] / (1 + E((V - p["d_4"]) / p["d_5"])) + p["d_6"]
    tmS = p["a_m"] / (E(-(V - p["b_m"]) / p["c_m"]) + E((V - p["d_m"]) / p["e_m"])) + p["f_m"]
    thf = p["a_hf"] / (1 + E((V - p["b_hf"]) / p["c_hf"])) + p["d_hf"]
    ths = p["a_hs"] / (1 + E((V - p["b_hs"]) / p["c_hs"])) + p["d_hs"]
    miS = 1 / (1 + E(-(V - p["v_1"]) / p["v_2"]))
    hiS = 1 / (1 + E((V - p["v_3"]) / p["v_4"]))
    mi36 = 1 / (1 + E(-(V - p["e_1"]) / p["e_2"]))
    a1, b1 = p["p_1"] * E(p["p_2"] * V), p["p_3"] * E(-p["p_4"] * V)
    Kf, Kb = p["p_5"], p["p_6"]
    a2, b2 = p["p_7"] * E(p["p_8"] * V), p["p_9"] * E(-p["p_10"] * V)
    ai, bi = p["p_11"] * E(p["p_12"] * V), p["p_13"] * E(-p["p_14"] * V)
    ai2 = p["p_15"] * E(p["p_16"] * V)
    psi = b2 * bi * ai2 / (a2 * ai)
    return [dv,
            ma * (1 - mU) - mb * mU, ha * (1 - hU) - hb * hU,
            (miE - mE) / tmE, (hiE - hE) / thE,
            (miC - mC) / tmC, (hiC - hC) / thC,
            (miS - mS) / tmS, (hiS - hfS) / thf, (hiS - hsS) / ths,
            (mi36 - mf36) / p["t_f"], (mi36 - mm36) / p["t_m"], (mi36 - ms36) / p["t_s"],
            b1 * C2 - a1 * C1, a1 * C1 + Kb * C3 - (b1 + Kf) * C2,
            Kf * C2 + psi * Ii + b2 * O - (Kb + ai2 + a2) * C3,
            bi * Ii + a2 * C3 - (b2 + ai) * O]


def sweep(p, amp, secs=7.0):
    """One of their sweeps: fresh start, step from 1 s to secs - 1 s. V sampled every 1 ms."""
    T = secs * 1000.0
    t = np.arange(0.0, T, 1.0)
    s = solve_ivp(rhs, (0, T), Y0, method="LSODA", t_eval=t, args=(p, amp, 1000.0, T - 1000.0), max_step=0.5,
                  rtol=1e-7, atol=1e-9)
    return t, s.y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="wt", choices=tuple(SETS))
    ap.add_argument("--amps", default="-4,-2,0,2,4,6,8,10,12")
    ap.add_argument("--secs", type=float, default=7.0)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from probe_dvb import event
    p = SETS[a.set]
    rows = []
    for amp in (float(x) for x in a.amps.split(",")):
        t, y = sweep(p, amp, a.secs)
        v = y[0]
        on = v[1000:int(a.secs * 1000) - 1000]
        e = event(on)
        rows.append(dict(pA=amp, rest=float(v[500:1000].mean()), peak=float(on.max()), min=float(on.min()),
                         plateau=float(on[-1000:].mean()), event=e, v=np.round(v, 2).tolist()))
        print(f"{a.set:9s} {amp:5.1f} pA  rest {rows[-1]['rest']:6.1f}  peak {on.max():6.1f}  min {on.min():6.1f}  "
              f"plateau {rows[-1]['plateau']:6.1f}  event {e and round(e['peak'], 1)} thr {e and round(e['threshold'], 1)}"
              f" hw {e and e['half_width_ms']} ahp {e and round(e['ahp'], 1)}", flush=True)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(dict(set=a.set, params=p, rows=rows)))


if __name__ == "__main__":
    main()
