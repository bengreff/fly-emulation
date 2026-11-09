"""Inbox item 3 / DEBUG_TRIAGE lines 19 and 17: checks of mech/capool's ca_bulk (NEURON's cadifpmp as a readout pool).
Pre-registered in docs/worm/night/2026-11-08_wbrain2.md (22:58) before any run.

    python ca_bulk_check.py port    OUT.json   one soma (PLML's diameter) with EGL-19 under voltage clamp: mass balance,
                                               linear-range decay against the derived time constant, and the readout
                                               chain's GCaMP6s half-fall after a 3 s step near 1 uM (check 3a)
    python ca_bulk_check.py neutral OUT.json   12-cell sub-brain, 300 ms, off vs cadifpmp: v and cai bit for bit
    python ca_bulk_check.py floor   OUT.json   AIYL, AFDL, AWAL alone, DC steps: Eq. 28's Ca vs the bulk pool's
    python ca_bulk_check.py touch   OUT.json CELL FORM   whole brain at the ledger, 20 pA for 1 s into CELL, GCaMP6s
                                               half-fall from the evoked peak (check 3b)
    python ca_bulk_check.py restat  IN.json OUT.json   recompute a touch run's statistics from its saved trace
    python ca_bulk_check.py randi   OUT.json TARGET FORM  FIT1 2b row 1 (template, obs_opto_g_nS 1, h_dt 2, mech_dt
                                               10, warm 5 s, 0.5 s pulse, 30 s mean dF/F against the control child)
FORM is off or cadifpmp. Every number printed is measured from the run; the bars are the pre-registration's.
"""
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np

from wormemu import brain as wb
from wormemu.mech import capool, observation as obs

FARADAY = 96485.33212                                # C/mol (NEURON's FARADAY unit, close enough at 1e-6)
ROOT = Path(__file__).resolve().parents[3]


_SPEC = []


def led(pid):
    """The ledger's value (the template worm), as the brain reads it; the Spec template where the ledger has no row."""
    if not _SPEC:
        _SPEC.append(wb.sample_worm(None))
    S = _SPEC[0]
    if pid in S.values:
        return S.v(pid)
    return {**obs.P, **{x.id: x.template for x in capool.SPECS}}[pid]


def kd():
    return (led("obs_gcamp6s_kd_nM"), led("obs_gcamp6s_hill"), led("obs_gcamp6s_range"),
            led("obs_gcamp6s_thalf_ms"))


def half_fall(t, y, i0):
    """Time from sample i0 to the first sample at or below half of (y[i0] - baseline), baseline = y[-1]."""
    base = y[-1]
    thr = base + 0.5 * (y[i0] - base)
    after = np.flatnonzero(y[i0:] <= thr)
    return float(t[i0 + after[0]] - t[i0]) if after.size else float("nan")


def gcamp_trace(c_nM, dt_ms, B0=None):
    K, n, R, th = kd()
    B = obs.hill(led("obs_ca_rest_nM"), K, n) if B0 is None else B0
    B0r = obs.hill(led("obs_ca_rest_nM"), K, n)
    out = np.empty(len(c_nM))
    for k, c in enumerate(c_nM):
        B = obs.binding_step(B, c, K, n, th, dt_ms)
        out[k] = obs.dff(B, B0r, R)
    return out


# --- port: one soma ------------------------------------------------------------------------------------------------
def port(out):
    h = wb._neuron()
    h.celsius = 6.3
    s = h.Section(name="plml_like")
    s.L = s.diam = 2.82                              # PLML's soma in the BAAIWorm morphology (measured, 8 Nov)
    s.insert("pas")
    s.insert("egl19")
    s.insert("cabulk")
    seg = s(0.5)
    seg.pas.g, seg.pas.e = 5e-5, -90.0
    seg.egl19.gbegl19 = 0.01                         # nS/um2; the mod's default 1 out-runs the pump at rest
    for pid, g in capool.GLOBALS.items():
        setattr(h, g, led(pid))
    h.caom_cabulk = 2.0
    seg.cabulk.ca0 = 0.05
    clamp = h.SEClamp(seg)
    clamp.rs = 1e-3
    h.dt, h.secondorder = 0.5, 0
    res = {}

    def run(steps):
        """steps: [(v_mV, dur_ms)]; returns t, cab (uM), ica (mA/cm2), jpump (mA/cm2), pumpca (mol/cm2)."""
        T, C, I, J, P = [], [], [], [], []
        clamp.dur1, clamp.amp1 = 1e9, steps[0][0]
        h.finitialize(-90.0)
        t = 0.0
        for v, dur in steps:
            clamp.amp1 = v
            for _ in range(int(round(dur / h.dt))):
                h.fadvance()
                t += h.dt
                T.append(t)
                C.append(seg.cabulk.cab)
                I.append(seg.ica)
                J.append(seg.cabulk.jpump)
                P.append(seg.cabulk.pumpca)
        return [np.array(x) for x in (T, C, I, J, P)]

    def content(cab_uM, pumpca):
        """Ca per um of cylinder in mol: free + buffered (cab is the volume mean) + pump-bound."""
        beta = h.beta_cabulk
        vol_um3 = np.pi * s.diam ** 2 / 4.0          # per um length
        return (1 + beta) * cab_uM * 1e-6 * vol_um3 * 1e-15 + pumpca * np.pi * s.diam * 1e-8

    # 1. mass balance: 200 ms at -20 mV, then 1 s at -90 mV (EGL-19 closed)
    T, C, I, J, P = run([(-20.0, 200.0), (-90.0, 1000.0)])
    circ_cm = np.pi * s.diam * 1e-4
    influx = np.cumsum(-I * 1e-3 * circ_cm * 1e-4 / (2 * FARADAY) * h.dt * 1e-3)    # mol per um length
    extr = np.cumsum(J * 1e-3 * circ_cm * 1e-4 / (2 * FARADAY) * h.dt * 1e-3)
    h.finitialize(-90.0)
    c_init = content(seg.cabulk.cab, seg.cabulk.pumpca)
    bal = content(C, P) - c_init - (influx - extr)
    res["mass_balance"] = dict(influx_mol_per_um=float(influx[-1]), extruded_mol_per_um=float(extr[-1]),
                               max_abs_residual_rel=float(np.abs(bal).max() / influx[-1]),
                               bar_rel=1e-6, pass_=bool(np.abs(bal).max() / influx[-1] <= 1e-6))
    # 2. linear-range decay: a small load (60 ms at -40 mV), then the late decay of cab above its floor
    T, C, I, J, P = run([(-90.0, 2000.0), (-40.0, 60.0), (-90.0, 3000.0)])
    floor = C[-1]
    k0 = np.searchsorted(T, 2060.0 + 200.0)          # after radial equilibration (29-80 ms, derived)
    k1 = np.searchsorted(T, 2060.0 + 700.0)
    y = np.log(np.maximum(C[k0:k1] - floor, 1e-12))
    tau = -1.0 / np.polyfit(T[k0:k1], y, 1)[0]
    Km = (h.k2_cabulk + h.k3_cabulk) / h.k1_cabulk                       # mM
    k_free = h.k3_cabulk * h.pump0_cabulk / (Km * 1e-6) * 1e4 * 4.0 / s.diam   # /s: cm/s -> um/s, x 4/d
    tau_d = (1 + h.beta_cabulk) / k_free * 1e3
    res["linear_decay"] = dict(linear_range=bool(C[np.searchsorted(T, 2060.0)] < 0.2 * Km * 1e3), peak_uM=float(C[np.searchsorted(T, 2060.0)]), floor_uM=float(floor),
                               tau_fit_ms=float(tau), tau_derived_ms=float(tau_d),
                               rel_err=float(abs(tau - tau_d) / tau_d), bar=0.25,
                               pass_=bool(abs(tau - tau_d) / tau_d <= 0.25))
    # 3a. readout chain: clamp level giving bulk Ca near 1 uM over 3 s, then release; GCaMP6s on 1 ms samples
    best = None
    for v in np.arange(-60.0, -19.0, 1.0):
        T, C, I, J, P = run([(-90.0, 1000.0), (float(v), 3000.0)])
        if best is None or abs(C[-1] - 1.0) < abs(best[1] - 1.0):
            best = (float(v), float(C[-1]))
    v = best[0]
    T, C, I, J, P = run([(-90.0, 1000.0), (v, 3000.0), (-90.0, 15000.0)])
    c_end = float(C[np.searchsorted(T, 4000.0)])
    c_ms = C[1::2] * 1e3                              # 0.5 ms -> 1 ms samples, nM
    t_ms = T[1::2]
    d = gcamp_trace(c_ms, 1.0)
    k_end = np.searchsorted(t_ms, 4000.0)
    hf_chain = half_fall(t_ms, d, k_end) / 1e3
    hf_ca = half_fall(t_ms, c_ms, k_end) / 1e3
    # the triage's reference: the indicator alone, Ca held at the same level 3 s then back to rest at once
    c_step = np.where((t_ms > 1000.0) & (t_ms <= 4000.0), c_end * 1e3, led("obs_ca_rest_nM"))
    hf_ind = half_fall(t_ms, gcamp_trace(c_step, 1.0), k_end) / 1e3
    res["chain_3a"] = dict(clamp_mV=v, bulk_at_end_uM=c_end, ica_end_pA=float(-I[np.searchsorted(T, 4000.0)] * 10.0
                                                                                 * seg.area()),
                           half_fall_dff_s=hf_chain, half_fall_bulk_ca_s=hf_ca, half_fall_indicator_only_s=hf_ind,
                           bar_s=[3.4, 13.4], pass_=bool(3.4 <= hf_chain <= 13.4))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


# --- sub-brain and whole-brain runs ------------------------------------------------------------------------------
def neutral(out):
    cells = ["AIYL", "AIYR", "AWAL", "AFDL", "ASHL", "AVAL", "AVAR", "PLML", "ALML", "RIML", "NSML", "MCL"]
    tr = {}
    for form in ("off", "cadifpmp"):
        b = wb.Brain(cells=cells, toggles={"ca_bulk": form, "channel_noise": "off"})
        b.reset()
        V, C = [], []
        for k in range(300):
            b.extra_pA[:] = 10.0 if 100 <= k < 200 else 0.0
            o = b.step(dt_ms=1.0)
            V.append(b._read(b._pv).copy())
            C.append(b._read(b._pc).copy())
        tr[form] = (np.array(V), np.array(C))
        del b
    dv = float(np.abs(tr["off"][0] - tr["cadifpmp"][0]).max())
    dc = float(np.abs(tr["off"][1] - tr["cadifpmp"][1]).max())
    res = dict(cells=cells, max_abs_dv_mV=dv, max_abs_dcai_uM=dc, pass_=bool(dv == 0.0 and dc == 0.0))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


def floor(out):
    sys.path.insert(0, str(ROOT / "scripts" / "worm"))
    import single_cell_sanity as scs
    res = {}
    for cell in ("AIYL", "AFDL", "AWAL"):
        b = scs.build(cells=[cell], extra={"ca_bulk": "cadifpmp"})
        cp = next(m for m in b.mechs if type(m).__module__ == "wormemu.mech.capool")
        rows = []
        for amp in (-10.0, -6.0, -4.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0):
            b.reset()
            b.extra_pA[:] = amp
            for _ in range(4000):
                b.step(dt_ms=1.0)
            rows.append(dict(I_pA=amp, v_mV=float(b._read(b._pv)[0]), eq28_nM=float(b._read(b._pc)[0] * 1e3),
                             bulk_nM=float(cp.read_bulk()[0] * 1e3),
                             ica_pA=float(-b.soma[0](0.5).ica * 10.0 * b.soma[0](0.5).area())))
        res[cell] = rows
        print(cell, json.dumps(rows))
        del b
    json.dump(res, open(out, "w"), indent=1)


def touch(out, cell, form):
    b = wb.Brain(toggles={"ca_bulk": form, "gcamp": "gcamp6s"})
    om = next(m for m in b.mechs if type(m).__module__ == obs.__name__)
    i = b.idx[cell]
    b.reset()
    t, d, c, v = [], [], [], []
    for k in range(14000):                            # 3 s rest, 1 s at 20 pA, 10 s after
        b.extra_pA[i] = 20.0 if 3000 <= k < 4000 else 0.0
        b.step(dt_ms=1.0)
        if k % 10 == 9:
            t.append(b.t)
            d.append(float(obs.dff(om.B[i], om.B0, om.R)))
            cb = b.mech_out.get("ca_bulk_uM")
            c.append(float(cb[i]) if cb is not None else float(b._read(b._pc)[i]))
            v.append(float(b._read(b._pv)[i]))
    res = touch_stats(dict(cell=cell, form=form, t=t, dff=d, ca_uM=c, v_mV=v))
    json.dump(res, open(out, "w"))
    print(json.dumps({k: x for k, x in res.items() if k not in ("t", "dff", "ca_uM", "v_mV")}))


def touch_stats(res, t_on_ms=3000.0):
    """Half-fall from the evoked peak: the largest dF/F at or after the step's onset (the pool's start-up transient,
    before the step, is not the response), to half of its height above the run's last sample."""
    t, d = np.array(res["t"]), np.array(res["dff"])
    after = np.flatnonzero(t > t_on_ms)
    kp = int(after[np.argmax(d[after])])
    res.update(peak_dff=float(d[kp]), t_peak_ms=float(t[kp]), dff_end=float(d[-1]), dff_pre=float(d[after[0] - 1]),
               half_fall_s=half_fall(t, d, kp) / 1e3, bar_s=[3.4, 13.4], ca_peak_uM=float(np.max(res["ca_uM"])),
               ca_peak_evoked_uM=float(np.max(np.array(res["ca_uM"])[after])), v_peak_mV=float(np.max(res["v_mV"])),
               t=list(map(float, t)), dff=list(map(float, d)))
    res["pass_"] = bool(3.4 <= res["half_fall_s"] <= 13.4)
    return res


def randi(out, target, form):
    sys.path.insert(0, str(ROOT / "scripts" / "worm" / "fit1"))
    import fit1_core as fc

    class BulkExperiment(fc.Experiment):
        """FIT1's experiment; the child reads F from the observation module's own GCaMP6s (B), which reads the bulk
        pool under ca_bulk and the Eq. 28 pool otherwise, so both forms go through the same readout."""

        def _child(self, target, window_s, pulse_ms, w):
            b, om = self.b, self.om
            om.sched = [(target, b.t, float(pulse_ms), 1.0)] if target is not None else []
            per_vol = int(round(fc.VOL_S * 1000 / self.mech_dt))
            t_on, F = b.t, []
            for k in range(int(round(window_s * 1000 / self.mech_dt))):
                b.step(dt_ms=self.mech_dt)
                if (k + 1) % per_vol == 0:
                    F.append(1.0 + (om.R - 1.0) * om.B)
            F = np.array(F).T
            tv, F1 = self._readout(0)                    # FIT1's own readout of the Eq. 28 pool, for comparison
            keep = tv > t_on / 1000.0 + 1e-9            # the same 60 volumes as F
            os.write(w, pickle.dumps(((np.arange(F.shape[1]) + 1) * fc.VOL_S,
                                      np.concatenate([F, F1[:, keep]], axis=0).astype(np.float32))))

    targets = target.split(",")
    cells = [c for c in os.environ.get("CABULK_CELLS", "").split(",") if c] or None     # smoke tests only
    E = BulkExperiment({"obs_opto_g_nS": 1.0}, targets, h_dt=2.0, mech_dt=10.0, warm_s=5.0, cells=cells,
                       toggles={"ca_bulk": form, "gcamp": "gcamp6s", "channel_noise": "off"})
    import time
    tv, Fc_all = E.run_one(None, 30.0, 500.0)          # FIT1's run(), keeping both readouts' rows
    r = {"t": tv, "ctrl": Fc_all, "F": {}, "wall": {}}
    for tg in targets:
        t1 = time.time()
        r["F"][tg] = E.run_one(tg, 30.0, 500.0)[1]
        r["wall"][tg] = time.time() - t1
    n, res = len(E.b.cell_names), {}
    for tg in targets:
        k = E.b.idx[tg]
        Fs, Fc = r["F"][tg][k], r["ctrl"][k]              # the observation module's GCaMP6s (bulk pool if on)
        Gs, Gc = r["F"][tg][n + k], r["ctrl"][n + k]      # FIT1's readout of the Eq. 28 pool
        dff, dg = (Fs - Fc) / Fc, (Gs - Gc) / Gc
        res[tg] = dict(target=tg, form=form, stat_30s=float(dff.mean()), peak=float(dff.max()),
                       t_peak_s=float(r["t"][int(dff.argmax())]), fit1_readout_stat_30s=float(dg.mean()),
                       dff=dff.tolist(), F0_ctrl_mean=float(Fc.mean()), training_median=0.43, wall=r["wall"][tg])
        print(json.dumps({k: x for k, x in res[tg].items() if k != "dff"}))
    json.dump(res, open(out, "w"))


if __name__ == "__main__":
    what, outp = sys.argv[1], sys.argv[2]
    {"port": lambda: port(outp), "neutral": lambda: neutral(outp), "floor": lambda: floor(outp),
     "touch": lambda: touch(outp, sys.argv[3], sys.argv[4]),
     "randi": lambda: randi(outp, sys.argv[3], sys.argv[4]),
     "restat": lambda: json.dump(touch_stats(json.load(open(outp))), open(sys.argv[3], "w"))}[what]()
