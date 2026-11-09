"""Unit and sanity checks of the sensory transduction ports (audit row 17, wbody, night of 6 Nov 2026).

Bars are written in docs/worm/night/2026-11-06_wbody.md before running. Each check writes a JSON of its numbers and a
figure to docs/worm/night/wbody/.

    PYTHONPATH=src python scripts/worm/senses_checks.py awc      # Usuyama 2012 AWC cascade on the published protocol
    PYTHONPATH=src python scripts/worm/senses_checks.py awa      # Liu 2018 AWA spike: scipy reference and NEURON mod
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[2] / "docs" / "worm" / "night" / "wbody"


def _save(name, res, fig=None):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(res, indent=1))
    if fig is not None:
        fig.savefig(OUT / f"{name}.png", dpi=110)
    print(json.dumps(res, indent=1))


# --- AWC: Usuyama 2012 -------------------------------------------------------------------------------------------
def awc():
    from scipy.integrate import solve_ivp
    from wormemu.mech import senses_cgmp as C
    p = {s.id: s.template for s in C.network_specs("AWC")}
    pulses = [(10.0, 70.0), (280.0, 460.0), (670.0, 970.0)]
    T, dt = 1000.0, 0.01

    def odor(t):
        return 1000.0 if any(a < t <= b for a, b in pulses) else 0.001

    cas = C.Cascade(p, 1)
    ica = cas.i["Ca"]
    t0 = time.time()
    ts = np.arange(0.0, T + dt / 2, dt)
    ca = np.empty(len(ts)); po = np.empty(len(ts))
    ca[0], po[0] = cas.x[ica, 0], cas.po()[0]
    for k in range(1, len(ts)):
        po[k] = cas.advance(dt, odor(ts[k] - dt / 2), 1.0, h_s=2.5e-4)[0]
        ca[k] = cas.x[ica, 0]
    wall_semi = time.time() - t0
    # scipy LSODA, piecewise between the odour switches
    cas.reset()
    y = np.concatenate([cas.x[:, 0], cas.V])
    edges = sorted({0.0, T} | {e for p_ in pulses for e in p_})
    ca_ref = np.empty(len(ts)); ca_ref[0] = y[ica]
    t0 = time.time()
    for a, b in zip(edges[:-1], edges[1:]):
        o = odor((a + b) / 2)
        sel = (ts > a + 1e-9) & (ts <= b + 1e-9)
        sol = solve_ivp(cas.rhs, (a, b), y, method="LSODA", t_eval=ts[sel], args=(lambda t, o=o: o,),
                        rtol=1e-8, atol=1e-12)
        ca_ref[sel] = sol.y[ica]
        y = sol.y[:, -1]
    wall_ref = time.time() - t0
    rows = []
    for a, b in pulses:
        pre = ca[(ts > a - 5) & (ts <= a)].mean()
        during = ca[(ts > a) & (ts <= b)]
        win = (ts > b) & (ts <= b + 60)
        kp = np.argmax(np.where(win, ca, -np.inf))
        kr = np.argmax(np.where(win, ca_ref, -np.inf))
        rows.append(dict(pulse_s=[a, b], pre_uM=round(float(pre), 5), min_during_uM=round(float(during.min()), 5),
                         peak_uM=round(float(ca[kp]), 5), peak_after_off_s=round(float(ts[kp] - b), 2),
                         peak_lsoda_uM=round(float(ca_ref[kr]), 5),
                         peak_rel_diff=round(float(abs(ca[kp] - ca_ref[kr]) / ca_ref[kr]), 5)))
    a_ = all(r["min_during_uM"] < r["pre_uM"] for r in rows)
    b_ = all(0 < r["peak_after_off_s"] <= 10 and r["peak_uM"] > r["pre_uM"] for r in rows)
    c_ = rows[2]["peak_uM"] > rows[0]["peak_uM"]
    d_ = all(r["peak_rel_diff"] < 0.02 for r in rows)
    res = dict(check="AWC Usuyama 2012 published protocol", pulses=rows, a_falls_during=a_,
               b_peak_within_10s_above_pre=b_, c_peak_300s_gt_60s=c_, d_semi_implicit_vs_lsoda_2pct=d_,
               verdict="pass" if (a_ and b_ and c_ and d_) else "fail",
               wall_s=dict(semi_implicit=round(wall_semi, 1), lsoda=round(wall_ref, 1)))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    for a, b in pulses:
        for x in ax:
            x.axvspan(a, b, color="0.9")
    ax[0].plot(ts, ca, lw=1, label="semi-implicit, h 0.25 ms")
    ax[0].plot(ts, ca_ref, lw=1, ls="--", label="scipy LSODA")
    ax[0].set_ylabel("Ca (uM)"); ax[0].legend(fontsize=8)
    ax[0].set_title(f"AWC cascade (Usuyama 2012 File S1), odorant on in grey: {res['verdict']}")
    ax[1].plot(ts, po, lw=1, color="C2"); ax[1].set_ylabel("CNG open probability"); ax[1].set_xlabel("time (s)")
    fig.tight_layout()
    _save("awc_usuyama2012", res, fig)


# --- AWA: Liu 2018 -----------------------------------------------------------------------------------------------
LIU = dict(C=1.5, gCa=0.1, vCa=120.0, f=0.4, tc1=1.0, tc2=160.0, vc1=-21.6, dvc1=9.17, vc2=16.2, dvc2=-16.1,
           vc3=23.0, dvc3=24.0, c0=0.55, vK=-84.0, gK1=1.5, vK1=2.0, dvK1=10.0, tK1=30.0, gK2=1.0, vK2=13.0,
           dvK2=20.0, tK2=1000.0, gK3=0.1, vK3=-25.0, dvK3=5.0, tK3=1000.0, gKr=0.39, vKr1=-42.0, dvKr1=5.0,
           vKr2=-42.0, dvKr2=5.0, tKr=1800.0, gKs=0.91, vKs1=-52.0, dvKs1=20.0, vKs2=-32.0, dvKs2=4.0, tKs1=27000.0,
           tKs2=3000.0, gKir=0.8, I0=5.0, beta=5.0, gL=0.25, vL=-65.0)    # Table S4, WT (nS, pF, mV, ms)


def _hinf(v, vh, dv):
    return 0.5 * (np.tanh((v - vh) / dv) + 1.0)


def liu_kir(v, P=LIU):
    """Liu's inward rectifier (pA). Default (P["kir"] absent or "smooth_min"): gKir times the smooth minimum of
    (v - vK) and I0 (mV), scale beta (mV), as in the authors' code (qiangstoch3c.py: ohmic below E_K, saturating at
    gKir I0 = 4 pA above it); "as_printed": the equation as printed, inward at every voltage (DEBUG_TRIAGE line 7).
    mech/senses_chem's awa_kir toggle, same forms."""
    if P.get("kir", "smooth_min") == "as_printed":
        return -P["gKir"] * (P["beta"] * np.log1p(np.exp(-(v - P["vK"] + P["I0"]) / P["beta"])) + P["I0"])
    return P["gKir"] * (P["I0"] - P["beta"] * np.logaddexp(0.0, -(v - P["vK"] - P["I0"]) / P["beta"]))


def liu_currents(v, s, P=LIU):
    """Total membrane current (pA, outward positive) and the gate steady states / rates at v; s = gates."""
    c1, c2, k1, k2, k3, kr, ks = s
    iCa = P["gCa"] * (c1 + P["f"] * c2) * (v - P["vCa"])
    iKir = liu_kir(v, P)
    iK = (P["gK1"] * k1 + P["gK2"] * k2 + P["gK3"] * k3 + P["gKr"] * kr * _hinf(v, P["vKr1"], P["dvKr1"])
          + P["gKs"] * ks) * (v - P["vK"])
    iL = P["gL"] * (v - P["vL"])
    return iCa + iK + iKir + iL


def liu_gates_inf(v, P=LIU):
    A = 0.5 * (np.tanh((v - P["vc1"]) / P["dvc1"]) + 1) * (np.tanh((v - P["vc2"]) / P["dvc2"]) + 1) / P["c0"]
    c2 = A / (1 + A)
    return np.array([c2, c2, _hinf(v, P["vK1"], P["dvK1"]), _hinf(v, P["vK2"], P["dvK2"]),
                     _hinf(v, P["vK3"], P["dvK3"]), _hinf(v, P["vKr2"], P["dvKr2"]), _hinf(v, P["vKs1"], P["dvKs1"])])


def liu_rhs(t, y, I_fn, P=LIU):
    v, s = y[0], y[1:]
    c1, c2, k1, k2, k3, kr, ks = s
    A = 0.5 * (np.tanh((v - P["vc1"]) / P["dvc1"]) + 1) * (np.tanh((v - P["vc2"]) / P["dvc2"]) + 1) / P["c0"]
    t2 = P["tc2"] / np.cosh((v - P["vc3"]) / P["dvc3"])
    tks = P["tKs1"] + 0.5 * (P["tKs2"] - P["tKs1"]) * (np.tanh((v - P["vKs2"]) / P["dvKs2"]) + 1)
    return np.array([
        (-liu_currents(v, s, P) + I_fn(t)) / P["C"],
        (A * (1 - c2) - c1) / P["tc1"] - (c1 - c2) / t2,
        (c1 - c2) / t2,
        (_hinf(v, P["vK1"], P["dvK1"]) - k1) / P["tK1"],
        (_hinf(v, P["vK2"], P["dvK2"]) - k2) / P["tK2"],
        (_hinf(v, P["vK3"], P["dvK3"]) - k3) / P["tK3"],
        (_hinf(v, P["vKr2"], P["dvKr2"]) - kr) / P["tKr"],
        (_hinf(v, P["vKs1"], P["dvKs1"]) - ks) / tks])


def liu_rest(P=LIU):
    from scipy.optimize import brentq
    f = lambda v: liu_currents(v, liu_gates_inf(v, P), P)
    vs = np.linspace(-120, 40, 1601)
    fs = np.array([f(v) for v in vs])
    roots = [brentq(f, vs[k], vs[k + 1]) for k in range(len(vs) - 1) if np.sign(fs[k]) != np.sign(fs[k + 1])]
    return roots[0]


def spike_features(t, v, detect=5.0):
    """First spike: an upstroke with dv/dt > `detect` mV/ms after a step's passive charging has passed; threshold =
    v where dv/dt rose through 1 mV/ms before it, or at dv/dt's minimum if it never fell below 1 mV/ms; peak,
    amplitude, half-width (at threshold + amplitude/2). None if no spike. t, v start at the step's onset."""
    dv = np.gradient(v, t)
    k = 1                                               # skip a step's passive charging: wait for dv/dt to peak and
    while k < len(v) - 1 and dv[k + 1] <= dv[k] and dv[k] > 1.0:      # fall (to a minimum or below 1 mV/ms)
        k += 1
    up = np.nonzero(dv[k:] > detect)[0]
    if not len(up):
        return None
    k0 = k + int(up[0])
    while k0 > k and dv[k0 - 1] > 1.0:
        k0 -= 1
    k = k0
    while k + 1 < len(v) and v[k + 1] >= v[k]:
        k += 1
    thr, pk = float(v[k0]), float(v[k])
    half = thr + (pk - thr) / 2
    a = k0 + int(np.nonzero(v[k0:] >= half)[0][0])
    b = k
    while b + 1 < len(v) and v[b + 1] >= half:
        b += 1
    return dict(threshold_mV=round(thr, 2), peak_mV=round(pk, 2), amplitude_mV=round(pk - thr, 2),
                half_width_ms=round(float(t[b] - t[a]), 2), t_peak_ms=round(float(t[k]), 2),
                max_dvdt=round(float(dv[k0:k + 1].max()), 2))


def awa_cpu(steps, P=LIU, T=1000.0, t_on=100.0):
    from scipy.integrate import solve_ivp
    v0 = liu_rest(P)
    out = {}
    traces = {}
    for I in steps:
        y0 = np.concatenate([[v0], liu_gates_inf(v0, P)])
        I_fn = lambda t, I=I: I if t_on <= t < t_on + T else 0.0
        ts = np.arange(0, t_on + T + 0.01, 0.05)
        sol = solve_ivp(liu_rhs, (0, ts[-1]), y0, method="LSODA", t_eval=ts, args=(I_fn, P), rtol=1e-8,
                        atol=1e-10, max_step=0.5)
        traces[I] = (sol.t, sol.y[0])
        out[I] = spike_features(sol.t[sol.t >= t_on], sol.y[0][sol.t >= t_on])
    return v0, out, traces


def awa_neuron(steps, T=1000.0, t_on=100.0, v0=-70.0, kir="smooth_min"):
    from wormemu.brain import _neuron
    h = _neuron()
    s = h.Section(name="awa")
    s.L = s.diam = float(np.sqrt(150.0 / np.pi))        # area 150 um2 -> C = 1.5 pF at cm 1
    s.cm, s.nseg = 1.0, 1
    s.insert("awa_liu")
    s.kir_form_awa_liu = 1 if kir == "as_printed" else 0
    stim = h.IClamp(s(0.5))
    stim.delay, stim.dur = t_on, T
    vv, tt = h.Vector().record(s(0.5)._ref_v), h.Vector().record(h._ref_t)
    h.dt, h.secondorder = 0.025, 0
    h.cvode_active(0)
    out, traces = {}, {}
    for I in steps:
        stim.amp = I * 1e-3
        h.finitialize(v0)
        h.continuerun(t_on + T)
        t, v = np.array(tt), np.array(vv)
        traces[I] = (t, v)
        out[I] = spike_features(t[t >= t_on], v[t >= t_on])
    return out, traces


def awa(kir="smooth_min"):
    """Liu 2018's isolated AWA. kir: the inward rectifier's form ("as_printed" saves as awa_liu2018_as_printed)."""
    P = dict(LIU, kir=kir)
    name = "awa_liu2018" + ("" if kir == "smooth_min" else f"_{kir}")
    steps = list(range(1, 21))
    v0, cpu, tr = awa_cpu(steps, P)
    first = next((I for I in steps if cpu[I]), None)
    res = dict(check="AWA Liu 2018 isolated WT cell, 1 s steps from rest", rest_mV=round(v0, 2),
               first_step_pA=first)
    if first is None:
        res["verdict"] = "fail (no spike for 1-20 pA)"
        _save(name, res)
        return
    f1 = cpu[first]
    f2 = cpu.get(2 * first) or awa_cpu([2 * first], P)[1][2 * first]
    nrn, ntr = awa_neuron([first, 2 * first], v0=v0, kir=kir)
    res.update(cpu_first=f1, cpu_double=f2, neuron_first=nrn[first], neuron_double=nrn[2 * first])
    ok = dict(threshold=abs(f1["threshold_mV"] + 34.0) <= 5, amplitude=abs(f1["amplitude_mV"] - 25.8) <= 6,
              half_width=abs(f1["half_width_ms"] - 18.0) <= 6,
              all_or_none=abs(f2["amplitude_mV"] - f1["amplitude_mV"]) <= 0.2 * f1["amplitude_mV"],
              neuron_matches_cpu=bool(nrn[first]) and abs(nrn[first]["peak_mV"] - f1["peak_mV"]) <= 1.0)
    res["bars"] = ok
    res["verdict"] = "pass" if all(ok.values()) else "fail: " + ", ".join(k for k, x in ok.items() if not x)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for I in (first, 2 * first):
        t, v = tr[I] if I in tr else (None, None)
        if t is not None:
            ax[0].plot(t, v, lw=1, label=f"scipy {I} pA")
        tn, vn = ntr[I]
        ax[0].plot(tn, vn, lw=1, ls="--", label=f"NEURON {I} pA")
    ax[0].set_xlabel("ms"); ax[0].set_ylabel("mV"); ax[0].legend(fontsize=8)
    ax[0].set_title(f"AWA (Liu 2018 Table S4 WT, Kir {kir}): {res['verdict']}", fontsize=9)
    t, v = tr[first]
    sel = (t > f1["t_peak_ms"] - 80) & (t < f1["t_peak_ms"] + 80)
    ax[1].plot(t[sel], v[sel]); ax[1].axhline(f1["threshold_mV"], ls=":", c="k")
    ax[1].set_title("first spike, threshold dotted", fontsize=9); ax[1].set_xlabel("ms")
    fig.tight_layout()
    _save(name, res, fig)


# --- in the brain: the nested lumped form and the stimulus signs -------------------------------------------------
def _brain_run(registry, toggles, seconds, stim=None, rec_cells=(), rec_out=()):
    """One brain (open loop, default observation plus `stim` [(t0_s, t1_s, {side: {channel: value}})]); returns v
    of every cell each step and the mechanisms' outputs for rec_cells. Runs in its own process (NEURON)."""
    from wormemu import mech
    from wormemu.brain import Brain, sample_worm
    from wormemu.interface import default_observation
    mine = {"temperature", "senses_chem", "senses_touch", "senses_proprio"}
    mech.REGISTRY[:] = [m for m in mech.REGISTRY if m not in mine] + registry    # wbrain's modules stay (receptors)
    t0 = time.time()
    b = Brain(sample_worm(None), toggles=toggles)
    build = time.time() - t0
    b.reset()
    V, po, g, outs = [], [], [], {k: [] for k in rec_out}
    t0 = time.time()
    n = int(seconds * 1000 / 4.0)
    for k in range(n):
        o = default_observation(b.t)
        for a, z, d in (stim or []):
            if a * 1000 <= b.t < z * 1000:
                for side, chans in d.items():
                    if side == "set":                    # other BodyToBrain fields (contact force, tap, ...)
                        for k_, v_ in chans.items():
                            setattr(o, k_, np.asarray(v_, float) if isinstance(v_, list) else v_)
                    else:
                        getattr(o, side).update(chans)
        out = b.step(o, 4.0)
        V.append(out.v_mV.copy())
        mo = b.mech_out
        po.append({c: mo.get("sens_cng_po", {}).get(c, mo.get("sens_trpv_po", {}).get(
            c, mo.get("sens_touch_po", {}).get(c, mo.get("sens_proprio_po", {}).get(c, np.nan)))) for c in rec_cells})
        g.append(np.asarray(mo.get("sens_g_nS", np.zeros(len(b.cell_names)))).copy())
        for k in rec_out:
            outs[k].append(mo.get(k, np.nan))
    return dict(V=np.array(V), po=po, g=np.array(g), outs=outs, names=b.cell_names, build_s=build,
                wall_per_bio_s=(time.time() - t0) / seconds)


LUMPED_ALL = {t: "lumped" for t in ("sens_salt", "sens_odor_attract", "sens_repellent", "sens_thermo", "sens_o2",
                                    "sens_co2", "sens_light", "sens_food")}


def _child(cfg):
    import pickle
    r = _brain_run(**cfg)
    sys.stdout.buffer.write(pickle.dumps(r))


def _spawn(cfg):
    import os
    import pickle
    import subprocess
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"))
    r = subprocess.run([sys.executable, __file__, "_child", json.dumps(cfg)], capture_output=True, env=env)
    assert r.returncode == 0, r.stderr.decode()[-3000:]
    return pickle.loads(r.stdout)


def chem():
    """(1) Nested form: senses_chem with every toggle 'lumped' and awa_membrane 'baaiworm' reproduces the brain
    without the module (brain_layers' lumped layer) to 1e-6 mV over 1 s, with stimuli on. (2) Template (cascade):
    stimulus signs per cell over 6 s, everything finite."""
    d = {"head": {"diacetyl_uM": 10.0, "isoamyl_alcohol_uM": 920.0, "octanol_uM": 6300.0, "nacl_mM": 0.0,
                  "temperature_C": 22.0, "o2_pct": 5.0, "co2_pct": 5.0, "light_mW_mm2": 1.0, "food_OD": 1.0},
         "tail": {"sds_mM": 1.0}}
    stim = [(0.2, 0.8, d)]
    a = _spawn(dict(registry=[], toggles={}, seconds=1.0, stim=stim))
    b = _spawn(dict(registry=["senses_chem"], toggles=dict(LUMPED_ALL, awa_membrane="baaiworm"), seconds=1.0,
                    stim=stim))
    dv = float(np.nanmax(np.abs(a["V"] - b["V"])))
    cells = ["AWCL", "AWBL", "ASEL", "ASER", "AFDL", "URXL", "BAGL", "ASJL", "ASHL", "ADLL", "PHAL", "AWAL", "NSML"]
    stim2 = [(2.0, 4.0, d)]
    c = _spawn(dict(registry=["senses_chem"], toggles={}, seconds=6.0, stim=stim2, rec_cells=cells))
    names = c["names"]
    t = (np.arange(len(c["V"])) + 1) * 4.0
    pre, dur, post = (t > 1500) & (t <= 2000), (t > 2000) & (t <= 4000), (t > 4000) & (t <= 6000)
    sig = {}
    for cell in cells:
        p = np.array([x[cell] for x in c["po"]], float)
        v = c["V"][:, names.index(cell)]
        sig[cell] = dict(po_pre=round(float(np.nanmean(p[pre])), 4), po_during_max=round(float(np.nanmax(p[dur])), 4),
                         po_during_min=round(float(np.nanmin(p[dur])), 4), po_after_max=round(float(np.nanmax(p[post])), 4),
                         v_pre=round(float(v[pre].mean()), 1), v_during_max=round(float(v[dur].max()), 1),
                         v_during_min=round(float(v[dur].min()), 1))
    res = dict(check="senses_chem in the brain", lumped_vs_no_module_max_dv_mV=dv,
               lumped_equivalent=dv <= 1e-6, cascade_finite=bool(np.isfinite(c["V"]).all()),
               wall_per_bio_s=dict(no_module=round(a["wall_per_bio_s"], 2), lumped=round(b["wall_per_bio_s"], 2),
                                   cascade=round(c["wall_per_bio_s"], 2)), signs=sig)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(len(cells), 2, figsize=(11, 1.3 * len(cells)), sharex=True)
    for k, cell in enumerate(cells):
        ax[k, 0].plot(t / 1000, [x[cell] for x in c["po"]], lw=1); ax[k, 0].set_ylabel(cell, fontsize=8)
        ax[k, 1].plot(t / 1000, c["V"][:, names.index(cell)], lw=0.8)
        for x in ax[k]:
            x.axvspan(2, 4, color="0.9"); x.tick_params(labelsize=7)
    ax[0, 0].set_title("channel open probability (CNG or TRPV template)", fontsize=9)
    ax[0, 1].set_title("soma v (mV), whole brain, open loop", fontsize=9)
    ax[-1, 0].set_xlabel("s"); ax[-1, 1].set_xlabel("s")
    fig.tight_layout()
    _save("senses_chem_brain", res, fig)


def _force(k=49, at=(), uN=0.0):
    f = np.zeros(k)
    f[list(at)] = uN
    return f.tolist()


def touch():
    """(1) Nested form: senses_touch with all three toggles 'lumped' reproduces the brain without the module to
    1e-6 mV over 1 s with touch, nose touch and a tap applied. (2) Template (Sanzeni channels), open loop, 5 s:
    10 uN anterior touch 1-2 s, 10 uN posterior touch 2.5-3 s, 200 uN harsh press at mid body 3.5-3.8 s, 50 uN
    nose press 4-4.3 s, tap (10 uN-equivalent, one step) at 4.6 s. Sanity bar (no isolated published measurement
    reachable here): ALM conductance has an ON peak within 50 ms of touch onset and an OFF peak within 50 ms of
    removal, it adapts (value 0.5 s into the touch < 30% of the ON peak), the current depolarises (ALML v rises),
    harsh touch opens PVD, nose touch opens ASH, tap opens every TRN, everything finite."""
    st = [(0.2, 0.6, {"set": {"contact_force_uN": _force(at=(10, 11), uN=10.0)}}),
          (0.3, 0.5, {"set": {"nose_force_uN": 50.0}}), (0.7, 0.704, {"set": {"tap": 10.0}})]
    lumped = {t_: "lumped" for t_ in ("sens_touch_gentle", "sens_touch_harsh", "sens_tap")}
    a = _spawn(dict(registry=[], toggles={}, seconds=1.0, stim=st))
    b = _spawn(dict(registry=["senses_touch"], toggles=lumped, seconds=1.0, stim=st))
    dv = float(np.nanmax(np.abs(a["V"] - b["V"])))
    cells = ["ALML", "AVM", "PLML", "PVM", "PVDL", "FLPL", "ASHL", "OLQDL", "IL1L"]
    st2 = [(1.0, 2.0, {"set": {"contact_force_uN": _force(at=(10, 11), uN=10.0)}}),
           (2.5, 3.0, {"set": {"contact_force_uN": _force(at=(36, 37), uN=10.0)}}),
           (3.5, 3.8, {"set": {"contact_force_uN": _force(at=(30,), uN=200.0)}}),
           (4.0, 4.3, {"set": {"nose_force_uN": 50.0}}), (4.6, 4.604, {"set": {"tap": 10.0}})]
    c = _spawn(dict(registry=["senses_touch"], toggles={}, seconds=5.0, stim=st2, rec_cells=cells))
    names, t = c["names"], (np.arange(len(c["V"])) + 1) * 4.0
    g = {cell: c["g"][:, names.index(cell)] for cell in cells}
    v = {cell: c["V"][:, names.index(cell)] for cell in cells}

    def win(x, a_, z_):
        return x[(t > a_) & (t <= z_)]
    ga = g["ALML"]
    on_pk, off_pk, base = win(ga, 1000, 1050).max(), win(ga, 2000, 2050).max(), win(ga, 800, 1000).mean()
    late = win(ga, 1500, 1504).mean()
    res = dict(check="senses_touch in the brain (Sanzeni 2019 channels)", lumped_vs_no_module_max_dv_mV=dv,
               lumped_equivalent=dv <= 1e-6, cascade_finite=bool(np.isfinite(c["V"]).all()),
               wall_per_bio_s=dict(no_module=round(a["wall_per_bio_s"], 2), lumped=round(b["wall_per_bio_s"], 2),
                                   cascade=round(c["wall_per_bio_s"], 2)),
               ALML_g_nS=dict(rest=round(float(base), 4), on_peak=round(float(on_pk), 4),
                              at_0p5s=round(float(late), 4), off_peak=round(float(off_pk), 4)),
               ALML_v_mV=dict(rest=round(float(win(v["ALML"], 800, 1000).mean()), 2),
                              on_max=round(float(win(v["ALML"], 1000, 1100).max()), 2)),
               peaks_g_nS={cell: dict(rest=round(float(win(g[cell], 800, 1000).mean()), 4),
                                      gentle_ant=round(float(win(g[cell], 1000, 2100).max()), 4),
                                      gentle_post=round(float(win(g[cell], 2500, 3100).max()), 4),
                                      harsh=round(float(win(g[cell], 3500, 3900).max()), 4),
                                      nose=round(float(win(g[cell], 4000, 4400).max()), 4),
                                      tap=round(float(win(g[cell], 4600, 4800).max()), 4)) for cell in cells})
    pk = res["peaks_g_nS"]
    res["bars"] = dict(on=bool(on_pk > 2 * base + 1e-6), off=bool(off_pk > 2 * base + 1e-6),
                       adapts=bool(late < 0.3 * on_pk), depolarises=res["ALML_v_mV"]["on_max"] > res["ALML_v_mV"]["rest"],
                       harsh_pvd=pk["PVDL"]["harsh"] > 2 * pk["PVDL"]["rest"] + 1e-6,
                       nose_ash=pk["ASHL"]["nose"] > 2 * pk["ASHL"]["rest"] + 1e-6,
                       tap_trn=all(pk[x]["tap"] > 2 * pk[x]["rest"] + 1e-6 for x in ("ALML", "AVM", "PLML", "PVM")),
                       finite=res["cascade_finite"])
    res["verdict"] = "pass" if all(res["bars"].values()) else "fail: " + ", ".join(k for k, x in res["bars"].items() if not x)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(len(cells), 2, figsize=(11, 1.3 * len(cells)), sharex=True)
    for k, cell in enumerate(cells):
        ax[k, 0].plot(t / 1000, g[cell], lw=0.8); ax[k, 0].set_ylabel(cell, fontsize=8)
        ax[k, 1].plot(t / 1000, v[cell], lw=0.8)
        for x in ax[k]:
            for a_, z_ in ((1, 2), (2.5, 3), (3.5, 3.8), (4, 4.3)):
                x.axvspan(a_, z_, color="0.9")
            x.axvline(4.6, color="0.7", lw=0.6); x.tick_params(labelsize=7)
    ax[0, 0].set_title("MeT conductance (nS): ant 10 uN, post 10 uN, harsh 200 uN, nose 50 uN, tap", fontsize=9)
    ax[0, 1].set_title("soma v (mV), whole brain, open loop", fontsize=9)
    ax[-1, 0].set_xlabel("s"); ax[-1, 1].set_xlabel("s")
    fig.tight_layout()
    _save("senses_touch_brain", res, fig)


def _kappa(k=49, s0=0.0, s1=1.0, per_mm=0.0):
    s = np.linspace(0, 1, k)
    return np.where((s >= s0) & (s < s1), per_mm, 0.0).tolist()


def proprio():
    """(1) Nested form: senses_proprio 'lumped' reproduces the brain without the module to 1e-6 mV over 1 s with a
    bend applied. (2) Template (stretch channels), open loop, 5 s: ventral bend (-8 /mm) over s 0-0.5 at 1-2 s,
    dorsal bend (+8 /mm) over the same span at 2.5-3.5 s, dorsal head bend (+8 /mm, s < 0.1) at 4-4.5 s. Sanity
    bar: a VB whose anterior field lies in the bent span opens in the ventral bend and not the dorsal, a DB the
    reverse; DVA opens in both; SMDD opens in the dorsal head bend and SMDV does not; all finite."""
    st = [(0.2, 0.7, {"set": {"curvature_per_mm": _kappa(s1=0.5, per_mm=-8.0)}})]
    a = _spawn(dict(registry=[], toggles={}, seconds=1.0, stim=st))
    b = _spawn(dict(registry=["senses_proprio"], toggles={"sens_proprio": "lumped"}, seconds=1.0, stim=st))
    dv = float(np.nanmax(np.abs(a["V"] - b["V"])))
    cells = ["VB03", "VB05", "DB03", "DB04", "DVA", "SMDDL", "SMDVL"]
    st2 = [(1.0, 2.0, {"set": {"curvature_per_mm": _kappa(s1=0.5, per_mm=-8.0)}}),
           (2.5, 3.5, {"set": {"curvature_per_mm": _kappa(s1=0.5, per_mm=8.0)}}),
           (4.0, 4.5, {"set": {"curvature_per_mm": _kappa(s1=0.1, per_mm=8.0)}})]
    c = _spawn(dict(registry=["senses_proprio"], toggles={}, seconds=5.0, stim=st2, rec_cells=cells))
    names, t = c["names"], (np.arange(len(c["V"])) + 1) * 4.0
    po = {cell: np.array([x[cell] for x in c["po"]], float) for cell in cells}
    v = {cell: c["V"][:, names.index(cell)] for cell in cells}

    def mx(x, a_, z_):
        return round(float(np.nanmax(x[(t > a_) & (t <= z_)])), 4)
    tab = {cell: dict(rest=mx(po[cell], 500, 1000), ventral=mx(po[cell], 1000, 2000), dorsal=mx(po[cell], 2500, 3500),
                      head_dorsal=mx(po[cell], 4000, 4500)) for cell in cells}
    res = dict(check="senses_proprio in the brain (stretch channels)", lumped_vs_no_module_max_dv_mV=dv,
               lumped_equivalent=dv <= 1e-6, cascade_finite=bool(np.isfinite(c["V"]).all()),
               wall_per_bio_s=dict(no_module=round(a["wall_per_bio_s"], 2), lumped=round(b["wall_per_bio_s"], 2),
                                   cascade=round(c["wall_per_bio_s"], 2)), po=tab)
    hi = lambda c_, k_: tab[c_][k_] > 0.5
    lo = lambda c_, k_: tab[c_][k_] < 0.1
    res["bars"] = dict(vb=hi("VB03", "ventral") and lo("VB03", "dorsal"), db=hi("DB03", "dorsal") and lo("DB03", "ventral"),
                       dva=hi("DVA", "ventral") and hi("DVA", "dorsal"), smd=hi("SMDDL", "head_dorsal") and lo("SMDVL", "head_dorsal"),
                       finite=res["cascade_finite"])
    res["verdict"] = "pass" if all(res["bars"].values()) else "fail: " + ", ".join(k for k, x in res["bars"].items() if not x)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(len(cells), 2, figsize=(11, 1.3 * len(cells)), sharex=True)
    for k, cell in enumerate(cells):
        ax[k, 0].plot(t / 1000, po[cell], lw=0.8); ax[k, 0].set_ylabel(cell, fontsize=8); ax[k, 0].set_ylim(-0.05, 1.05)
        ax[k, 1].plot(t / 1000, v[cell], lw=0.8)
        for x in ax[k]:
            for (a_, z_), col in (((1, 2), "#dde"), ((2.5, 3.5), "#edd"), ((4, 4.5), "#ded")):
                x.axvspan(a_, z_, color=col)
            x.tick_params(labelsize=7)
    ax[0, 0].set_title("stretch channel Po: ventral bend (blue), dorsal bend (red), dorsal head bend (green)", fontsize=9)
    ax[0, 1].set_title("soma v (mV), whole brain, open loop", fontsize=9)
    ax[-1, 0].set_xlabel("s"); ax[-1, 1].set_xlabel("s")
    fig.tight_layout()
    _save("senses_proprio_brain", res, fig)


def temp():
    """Row 25. (1) Neutral: with the worm at T_ref (20 C) the temperature module changes nothing (registry with and
    without it, the sensory modules on, max |dv| <= 1e-9 mV over 1 s). (2) Arithmetic: at 30 C the factors are the
    Q10s themselves and the DMP clock factor is 1. (3) Sanity: 3 s with the plate stepping 20 -> 25 C at 1 s:
    finite; the worm's temperature reaches 25 C within 50 ms; conductance factor 1.5 ** 0.5."""
    from wormemu.mech import temperature as tm
    sen = ["senses_chem", "senses_touch", "senses_proprio"]
    a = _spawn(dict(registry=sen, toggles={}, seconds=1.0))
    b = _spawn(dict(registry=["temperature"] + sen, toggles={}, seconds=1.0))
    dv = float(np.nanmax(np.abs(a["V"] - b["V"])))
    p = {s.id: s.template for s in tm.SPECS}
    f30 = tm.factors(30.0, p)
    arith = all(abs(f30[c] - p[f"temp_q10_{c}"]) < 1e-12 for c in tm.CLASSES) and f30["dmp_clock"] == 1.0
    c = _spawn(dict(registry=["temperature"] + sen, toggles={}, seconds=3.0,
                    stim=[(1.0, 3.0, {"head": {"temperature_C": 25.0}})], rec_cells=["AWCL", "AFDL", "ALML", "DVA"],
                    rec_out=["temperature_C"]))
    T = np.array(c["outs"]["temperature_C"], float)
    t = (np.arange(len(T)) + 1) * 4.0
    t25 = float(t[np.flatnonzero((t > 1000) & (T > 24.99))[0]] - 1000) if (T > 24.99).any() else None
    names = c["names"]
    above = lambda V, a_, z_: float(np.mean([(V[k][~np.isnan(V[k])] > -20).sum() for k in range(len(V))
                                              if a_ < t[k] <= z_]))
    res = dict(check="temperature (row 25)", neutral_max_dv_mV=dv, neutral=dv <= 1e-9, factors_30C=f30,
               arithmetic=arith, finite=bool(np.isfinite(c["V"]).all()), t_to_25C_ms=t25,
               cells_above_m20_mV=dict(at_20C=above(c["V"], 500, 1000), at_25C=above(c["V"], 2500, 3000)),
               wall_per_bio_s=dict(without=round(a["wall_per_bio_s"], 2), with_=round(b["wall_per_bio_s"], 2)))
    res["bars"] = dict(neutral=res["neutral"], arithmetic=arith, finite=res["finite"],
                       tracks=t25 is not None and t25 <= 50)
    res["verdict"] = "pass" if all(res["bars"].values()) else "fail: " + ", ".join(k for k, x in res["bars"].items() if not x)
    _save("temperature_row25", res, None)


if __name__ == "__main__":
    if sys.argv[1] == "_child":
        _child(json.loads(sys.argv[2]))
    else:
        {"awc": awc, "awa": awa, "chem": chem, "touch": touch, "proprio": proprio, "temp": temp}[sys.argv[1]](*sys.argv[2:])
