"""Inbox 01:45 (weki) check: the organ conductances integrated implicitly (A, numerical).

Spec: docs/worm/night/wbody2/implicit_g_spec.md (9 Nov 2026 01:52). Three terms put g (E - V) on a cell as a current
from V at the step's start (explicit in V): egg_laying's LGC-55 on HSN ('lgc55') and its vm cation term on the 8 vm
muscles ('vmcat'), and intestine's PBO-5/6 on the posterior body-wall muscles ('pbo5'). The fix sets each as a wgc
point process (implicit in NEURON); toggles egg_g_solver and pboc_g_solver, implicit | explicit (the old code).

Setup: Brain of HSNL and HSNR (lgc55, vmcat; the module builds the 16 sex muscles) or of HSNL, dBWML22 and vBWMR22
(pbo5; the targets the two muscles, HSNL there because neuromod's step fails on a brain with no neuron, 01:57),
default toggles except quantal_noise and channel_noise off. The term's g is driven directly (occupancy, stretch or
p_open forced to 1, the term's other conductances 0), on at T_ON 999 ms for 300 exchange steps of 4.5 ms. Recorded:
the target cells' V on the 4.5 ms grid. One case per process (NEURON keeps what a Brain builds).

Bars (written 9 Nov 01:52 before the first run; the spec's three):
  1 neutral  explicit reproduces the pre-fix code (9e84fa1's src, run with this script's 'run' and --base) exactly on
             every recorded trace.
  2 small g  g 0.1 and 0.5 nS: with dV = V(g) - V(0) at the same exchange step, RMS over the pulse of (dV_impl,4.5 -
             dV_ref) <= 1.1 x RMS(dV_expl,4.5 - dV_ref) + 0.05 mV, the reference being explicit at a 0.5 ms exchange
             step (1.1 and 0.05 mV guessed).
  3 stable   g at the top of the term's range and 2x (lgc55 5, 10; vmcat 7, 14; pbo5 10, 20 nS): under implicit every
             target cell's V finite and its alternation (fit/vitals.alternation) < ALT_STEPS. Explicit reported.
Reported, not barred: RMS(dV_impl - dV_ref) at the top g.

Usage: python implicit_g_check.py run OUTDIR [--base]     (--base: explicit cases only, for the pre-fix src)
       python implicit_g_check.py score OUTDIR BASEDIR OUT.json
       python implicit_g_check.py case TERM G FORM DT OUT.json   (one case; used by run)
The src imported is $PYTHONPATH's (run passes its own PYTHONPATH on to each case).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

T_ON, N_STEPS, DT = 999.0, 300, 4.5
TERMS = {"lgc55": (["HSNL", "HSNR"], (0.1, 0.5, 5.0, 10.0)),
         "vmcat": (["HSNL", "HSNR"], (0.1, 0.5, 7.0, 14.0)),
         "pbo5": (["HSNL", "dBWML22", "vBWMR22"], (0.1, 0.5, 10.0, 20.0))}   # a neuron: neuromod needs one
TOGGLE = {"lgc55": ("organs_egglaying", "egg_g_solver"), "vmcat": ("organs_egglaying", "egg_g_solver"),
          "pbo5": ("organs_intestine", "pboc_g_solver")}


def case(term, g, form, dt, out):
    import importlib
    from wormemu.brain import Brain
    modname, tname = TOGGLE[term]
    mod = importlib.import_module(f"wormemu.mech.{modname}")
    tg = {"quantal_noise": "off", "channel_noise": "off"}
    if any(t[0] == tname for t in mod.MECHANISMS):
        tg[tname] = form
    else:
        assert form == "explicit", f"{tname} not in this src: only the explicit (pre-fix) form runs"
    b = Brain(cells=TERMS[term][0], toggles=tg)
    b.reset()
    m = next(x for x in b.mechs if isinstance(x, mod.Mech))
    q = m.q
    if term in ("lgc55", "vmcat"):
        for k in ("egg_stretch_g_nS", "egg_5ht_g_nS", "egg_nlp3_g_nS", "egg_lgc55_g_nS"):
            q[k] = 0.0
        key = "egg_lgc55_g_nS" if term == "lgc55" else "egg_stretch_g_nS"
        cells = (lambda: b._read(b._pv)[[b.idx["HSNL"], b.idx["HSNR"]]]) if term == "lgc55" else \
            (lambda: m._read(m._pv)[m.is_vm])
    else:
        key = "pbo5_g_nS"
        m.cleft.p_open = lambda: 1.0
        assert len(m.post_cells) == 2, m.post_cells
        cells = lambda: b._read(b._pv)[m.post_cells]
    t_end = T_ON + N_STEPS * DT
    t, V, w0 = [], [], time.time()
    grid = DT / dt
    k = 0
    while b.t < t_end - 1e-9:
        q[key] = g if b.t >= T_ON - 1e-9 else 0.0
        if term == "lgc55":
            m.tyr = 1e12                                   # occupancy 1 - EC50 / 1e12
        elif term == "vmcat":
            m.U = 1e9                                      # stretch Hill 1
        b.step(None, dt)
        k += 1
        if abs(k / grid - round(k / grid)) < 1e-9:
            t.append(b.t)
            V.append(np.asarray(cells(), float).tolist())
    Path(out).write_text(json.dumps({"term": term, "g_nS": g, "form": form, "dt_ms": dt, "t_ms": t, "v_mV": V,
                                     "wall_s": time.time() - w0}))


def cases(base):
    for term, (_, gs) in TERMS.items():
        for g in (0.0,) + gs:
            for form, dt in (("explicit", DT), ("explicit", 0.5), ("implicit", DT)):
                if base and form != "explicit":
                    continue
                yield term, g, form, dt


def label(term, g, form, dt):
    return f"{term}_g{g:g}_{form}_dt{dt:g}"


def run(outdir, base):
    d = Path(outdir)
    d.mkdir(parents=True, exist_ok=True)
    for c in cases(base):
        o = d / f"{label(*c)}.json"
        if o.exists():
            continue
        w0 = time.time()
        r = subprocess.run([sys.executable, __file__, "case", c[0], str(c[1]), c[2], str(c[3]), str(o)],
                           capture_output=True, text=True, env=dict(os.environ))
        if r.returncode:
            (d / f"{label(*c)}.err").write_text(r.stderr[-5000:])
        print(label(*c), "ok" if r.returncode == 0 else "FAILED", f"{time.time() - w0:.1f} s", flush=True)


def _load(d, *c):
    p = Path(d) / f"{label(*c)}.json"
    return json.loads(p.read_text()) if p.exists() else None


def score(outdir, basedir, out):
    from wormemu.fit import vitals
    res = {"neutral": {}, "small_g": {}, "stable": {}, "top_g_rms": {}}
    for c in cases(True):
        a, b = _load(outdir, *c), _load(basedir, *c)
        res["neutral"][label(*c)] = bool(a and b and a["v_mV"] == b["v_mV"] and a["t_ms"] == b["t_ms"])

    def dv(term, g, form, dt):
        x, z = _load(outdir, term, g, form, dt), _load(outdir, term, 0.0, form, dt)
        t = np.array(x["t_ms"])
        on = t > T_ON + 1e-9
        return (np.array(x["v_mV"]) - np.array(z["v_mV"]))[on]

    for term, (_, gs) in TERMS.items():
        for g in gs:
            ref, ex, im = dv(term, g, "explicit", 0.5), dv(term, g, "explicit", DT), dv(term, g, "implicit", DT)
            r_ex = float(np.sqrt(np.mean((ex - ref) ** 2)))
            r_im = float(np.sqrt(np.mean((im - ref) ** 2)))
            row = {"rms_expl_mV": r_ex, "rms_impl_mV": r_im, "peak_abs_dV_ref_mV": float(np.abs(ref).max())}
            if g in gs[:2]:
                row["pass"] = r_im <= 1.1 * r_ex + 0.05
                res["small_g"][f"{term}_g{g:g}"] = row
            else:
                res["top_g_rms"][f"{term}_g{g:g}"] = row
                st = {}
                for form in ("implicit", "explicit"):
                    x = _load(outdir, term, g, form, DT)
                    V = np.array(x["v_mV"], float)
                    on = np.array(x["t_ms"]) > T_ON + 1e-9
                    alt = vitals.alternation(V[on])
                    st[form] = {"finite": bool(np.isfinite(V).all()), "alternation_max": int(alt.max()),
                                "v_range_mV": [float(np.nanmin(V[on])), float(np.nanmax(V[on]))]}
                st["pass"] = st["implicit"]["finite"] and st["implicit"]["alternation_max"] < vitals.ALT_STEPS
                res["stable"][f"{term}_g{g:g}"] = st
    res["pass"] = {"neutral": all(res["neutral"].values()),
                   "small_g": all(r["pass"] for r in res["small_g"].values()),
                   "stable": all(r["pass"] for r in res["stable"].values())}
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "case":
        case(a[1], float(a[2]), a[3], float(a[4]), a[5])
    elif a[0] == "run":
        run(a[1], "--base" in a)
    elif a[0] == "score":
        score(a[1], a[2], a[3])
