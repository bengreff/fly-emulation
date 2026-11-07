"""Rows 24b, 18, 19 unit checks on the modules alone (bars in docs/worm/night/2026-11-06_wbrain.md, written before
running): mech.learning (associative states) and mech.slow_signalling (slow states, homeostasis), on a stub brain
whose cells sit at -50 mV and Ca 0.1 uM except the one driven. 1 s steps.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/slow_unit_check.py [out.json]
"""
from __future__ import annotations

import json
import math
import sys
from types import SimpleNamespace

import numpy as np

from wormemu import mech
from wormemu.mech import learning as LN
from wormemu.mech import slow_signalling as SS

CELLS = ["ASER", "AFDL", "AFDR", "AWCL", "AWCR", "ADFL", "ADFR", "ASIL", "ASIR", "AVAL"]
DT = 1000.0
V0, C0 = -50.0, 0.1
T = {s.id: s.template for s in LN.SPECS + SS.SPECS}


def stub():
    return SimpleNamespace(cell_names=CELLS, idx={c: i for i, c in enumerate(CELLS)},
                           layers=SimpleNamespace(pos=np.zeros(len(CELLS))), wsyn=[])


class Run:
    def __init__(self, ss="states", homeo="oleary", assoc=True):
        b = stub()
        self.ss = SS.Mech(b, T, dict(slow_signalling=ss, homeostasis=homeo))
        self.ln = LN.Mech(b, T, dict(associative="on")) if assoc else None
        self.t, self.out, self.last = 0.0, {}, {}

    def go(self, seconds, dv=None, dca=None, outputs=None, use_ss=True):
        for _ in range(int(round(seconds * 1000 / DT))):
            v, ca = np.full(len(CELLS), V0), np.full(len(CELLS), C0)
            for c, x in (dv or {}).items():
                v[CELLS.index(c)] += x
            for c, x in (dca or {}).items():
                ca[CELLS.index(c)] *= x
            ctx = mech.Ctx(self.t, {}, v, ca, CELLS, np.zeros(len(CELLS), bool), outputs=dict(self.out))
            ctx.outputs.update(outputs or {})
            outs = {}
            for m in ([self.ss] if use_ss else []) + ([self.ln] if self.ln else []):
                r = m.step(ctx, DT)
                self.last[type(m).__module__] = r
                if "out" in r:
                    mech.merge(outs, r["out"])
                    ctx.outputs.update(r["out"])
            self.out = outs
            self.t += DT


def i(c):
    return CELLS.index(c)


def main():
    res = {}
    # 1. neutral: fed, no pathogen, cells off their set points for 2 h
    r = Run()
    r.go(2.0)
    r.go(7200, dv={"ASER": 10, "AFDL": 10, "AWCL": -10})
    lg = r.last["wormemu.mech.learning"]
    res["neutral"] = dict(assoc=dict(r.ln.A), release_max_dev=float(np.abs(lg["g_scale"]["release"] - 1).max()),
                          passed=bool(max(r.ln.A.values()) == 0.0 and np.all(lg["g_scale"]["release"] == 1.0)))
    # 2. salt pairing, then forgetting (energy_fraction 0, slow_signalling not running: the energy path)
    tl, tf = T["assoc_salt_learn_tau_min"], T["assoc_salt_forget_tau_min"]
    teff, ass = 1 / (1 / tl + 1 / tf), tf / (tl + tf)
    r = Run(assoc=True)
    r.go(2.0, use_ss=False)
    r.go(3600, dv={"ASER": 10}, outputs={"energy_fraction": 0.0}, use_ss=False)
    a60, want60 = r.ln.A["salt"], ass * (1 - math.exp(-60 / teff))
    f60 = float(r.last["wormemu.mech.learning"]["g_scale"]["release"][i("ASER")])
    r.go(7200, outputs={"energy_fraction": 1.0}, use_ss=False)
    a180, want180 = r.ln.A["salt"], want60 * math.exp(-120 / tf)
    rp = Run()
    rp.go(2.0, use_ss=False)
    rp.go(4 * 3600, outputs={"pathogen_exposure": 1.0}, use_ss=False)
    tl, tf = T["assoc_pathogen_learn_tau_min"], T["assoc_pathogen_forget_tau_min"]
    wantp = tf / (tl + tf) * (1 - math.exp(-240 * (1 / tl + 1 / tf)))
    msp = float(rp.out["ma_release_scale"][i("ADFL")])
    res["learning_closed_form"] = dict(
        salt_60min=(a60, want60), aser_release=(f60, 1 - 0.6 * a60), salt_after_120min_fed=(a180, want180),
        pathogen_4h=(rp.ln.A["pathogen"], wantp), adf_ma_scale=(msp, 1 + wantp),
        passed=bool(abs(a60 / want60 - 1) < 0.01 and abs(f60 - (1 - 0.6 * a60)) < 1e-9
                    and abs(a180 / want180 - 1) < 0.01 and abs(rp.ln.A["pathogen"] / wantp - 1) < 0.01
                    and abs(msp / (1 + wantp) - 1) < 0.01))
    # 2b. slow states under a constant input: u (1 - exp(-t/tau))
    r = Run(homeo="off", assoc=False)
    r.go(2.0)
    r.go(1800, dv={"AWCL": -5, "AFDL": 5}, outputs={"energy_fraction": 0.25})
    t = 1800 * 1000
    tau = {"egl4": 6e4 * T["egl4_tau_min"], "cmk1_fast": 6e4 * T["cmk1_fast_tau_min"],
           "cmk1_slow": 3.6e6 * T["cmk1_slow_tau_h"], "daf16": 3.6e6 * T["daf16_tau_h"],
           "daf7": 3.6e6 * T["daf7_tau_h"], "creb": 3.6e6 * T["creb_tau_h"]}
    got = {"egl4": r.ss.S["egl4"][i("AWCL")], "cmk1_fast": r.ss.S["cmk1_fast"][i("AFDL")],
           "cmk1_slow": r.ss.S["cmk1_slow"][i("AFDL")], "daf16": r.ss.S["daf16"][i("AVAL")],
           "daf7": r.ss.S["daf7"][i("ASIL")], "creb": r.ss.S["creb"][i("AFDL")]}
    u = {"egl4": 0.5, "cmk1_fast": 0.5, "cmk1_slow": 0.5, "daf16": 0.75, "daf7": 0.25, "creb": 0.5}
    # the activity states start at 0; daf16 and daf7 start at their context's steady state and stay there
    want = {k: (u[k] if k in ("daf16", "daf7") else u[k] * (1 - math.exp(-t / tau[k]))) for k in got}
    err = max(abs(got[k] - want[k]) for k in got)
    res["slow_closed_form"] = dict(max_abs_err=float(err), passed=bool(err < 1e-6))
    # 3. timescale separation; EGL-4 half time
    r = Run(homeo="off", assoc=False)
    r.go(2.0)
    r.go(600, dv={"AFDL": 10})
    fast, slow = float(r.ss.S["cmk1_fast"][i("AFDL")]), float(r.ss.S["cmk1_slow"][i("AFDL")])
    r = Run(homeo="off", assoc=False)
    r.go(2.0)
    half = None
    for k in range(1, 241):
        r.go(60, dv={"AWCL": -10})
        if half is None and r.ss.S["egl4"][i("AWCL")] >= 0.5:
            half = k
    res["timescales"] = dict(cmk1_fast_10min=fast, cmk1_slow_10min=slow, egl4_half_min=half,
                             passed=bool(fast > 0.95 and slow < 0.05 and half is not None and 30 <= half <= 120))
    # 4. homeostasis
    r = Run(ss="off", assoc=False)
    r.go(2.0)
    r.go(3600, dca={"AVAL": 2.0})
    d1 = float(r.ss.d["unc2"][i("AVAL")])
    ti, tg = T["homeo_unc2_tau_h"], T["homeo_tau_g_h"]
    want = 1 - (1 - tg * (1 - math.exp(-1 / tg))) / ti
    r.go(3600, dca={"AVAL": 2.0})
    d2 = float(r.ss.d["unc2"][i("AVAL")])
    rb = Run(ss="off", assoc=False)
    rb.go(2.0)
    rb.go(24 * 3600, dca={"AVAL": 10.0})
    lo = min(float(rb.ss.d[c].min()) for c in SS.HOMEO_CHANNELS)
    hi = max(float(rb.ss.d[c].max()) for c in SS.HOMEO_CHANNELS)
    rb2 = Run(ss="off", assoc=False)
    rb2.go(2.0)
    rb2.go(24 * 3600, dca={"AVAL": 0.1})
    lo, hi = min(lo, min(float(rb2.ss.d[c].min()) for c in SS.HOMEO_CHANNELS)), \
        max(hi, max(float(rb2.ss.d[c].max()) for c in SS.HOMEO_CHANNELS))
    res["homeostasis"] = dict(unc2_1h=(d1, want), unc2_2h=d2, density_range_24h=(lo, hi),
                              passed=dict(code=bool(abs(d1 / want - 1) < 0.01),
                                          timing=bool(1 - d1 < 0.15 and 1 - d2 > 0.20),
                                          bounds=bool(lo >= T["homeo_d_lo"] - 1e-12 and hi <= T["homeo_d_hi"] + 1e-12)))
    print(json.dumps(res, indent=1, default=float))
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
