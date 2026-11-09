"""Item 8 (line 4) glia port check: the amphid neurons' K+ load from their own gated K+ currents (B).

Spec: docs/worm/night/wbody2/glia_port_spec.md (9 Nov 2026 01:09). Source: Sibille, Dao Duc, Holcman & Rouach 2015
PLoS Comput Biol 11:e1004137 (PMC4380507, full text; docs/worm/night/wbody2/lit_glia_port.md): d K0 / dt = iK -
2 ipumpN - 2 ipumpA + iKir (eq. 25), with iK the neuron's gated K+ current against an E_K that follows K0 (eq. 8).
Forms: glia_k_load leak (nested, the code before the port) | channels; glia_v0_window first (0-1 s, as before) |
settled (1-2 s). Brain: check_glia's (44 cells, BAAIWorm membranes, Cook wiring, default toggles, dt 5 ms).

Bars (written 9 Nov before the first run; the spec's four):
  1 neutral   leak + first reproduces the pre-port check_glia output exactly (every recorded quantity, wt and
              null; runs/worm/wbody2/glia_port_base.json, run on 2bae382's src before glia.py changed).
  2 identity  channels form, AWCL clamped 20 mV above its window mean for 1 s from 3 s, 6 s: at every step after
              the window closes, the module's load equals this script's own sum over each side's amphid neurons of
              (summed ik x area - its window mean) x 1e6 / F / volume to 1e-9 of that side's scale (the same sum
              of |ik| + |mean|, a float tolerance: the difference itself crosses 0), and every K+ section of every
              amphid neuron carries ek = its base + (RT/F) ln(Ko / Ko_bath) of its side to 1e-9 mV. Both windows.
  3 zero      no clamp, 22 s: both endings' K+ within 0.05 mM of the bath over the 20 s after the window closes.
              Reported for all 4 forms; the bar applies to each form adopted as a candidate.
  4 check     check_glia's run() under each of the 4 forms, its bars unchanged: ceiling (peak <= 10.2 mM, rise
              over the pre-clamp base >= 0.01 mM), tau 3.4-4.0 s, null (glia_kbuffer=null) >= 1.24x slower.
Expected (guessed, from the spec): settled removes most of the false sink; channels moves tau, direction unknown.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/wbody2/glia_port_check.py OUT.json [part ...]
parts: neutral identity zero check (default all)
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
_sp = importlib.util.spec_from_file_location("check_glia", ROOT / "scripts/worm/organs/check_glia.py")
cg = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(cg)

from wormemu.brain import Brain  # noqa: E402
from wormemu.brain_layers import AMPHID  # noqa: E402
from wormemu.mech import glia as gl  # noqa: E402

FORMS = [(k, w) for k in ("leak", "channels") for w in ("first", "settled")]
BASE = ROOT / "runs/worm/wbody2/glia_port_base.json"


def tog(k, w, **extra):
    return {"glia_k_load": k, "glia_v0_window": w, **extra}


def _strip(d):
    return {k: (_strip(v) if isinstance(v, dict) else v) for k, v in d.items() if k != "wall_s"}


def neutral():
    base = json.loads(BASE.read_text())
    res = {}
    for lab, t in (("wt", tog("leak", "first")), ("null", tog("leak", "first", glia_kbuffer="null"))):
        new = cg.run(t, lab)
        diff = [k for k in _strip(base[lab]) if _strip(base[lab])[k] != _strip(new).get(k)]
        res[lab] = {"identical": not diff, "differs": diff}
    res["pass"] = all(r["identical"] for r in res.values())
    return res


def _ik_sums(b, m):
    out = []
    for i in m.amph:
        secs = [s for s in b.cells[i].all if b.h.ismembrane("k_ion", sec=s)]
        out.append(10.0 * sum(seg.ik * seg.area() for s in secs for seg in s))
    return np.array(out)


def identity(win):
    b = Brain(cells=cg.CELLS, toggles=tog("channels", win))
    b.reset()
    m = next(x for x in b.mechs if isinstance(x, gl.Mech))
    q, t1 = m.q, gl.GLIA_V0_WINDOWS[win][1]
    k_secs = [[s for s in b.cells[i].all if b.h.ismembrane("k_ion", sec=s)] for i in m.amph]
    ek_base = [[s.ek for s in ss] for ss in k_secs]
    j = list(m.amph).index(b.idx["AWCL"])
    rec = {"ik": [], "worst_load_rel": 0.0, "worst_load_abs": 0.0, "worst_ek_mV": 0.0, "n": 0, "v": []}
    orig = m.step

    def wrapped(ctx, dt_ms):
        ik = _ik_sums(b, m)
        win_on = gl.GLIA_V0_WINDOWS[win][0] <= ctx.t_ms + 0.5 * dt_ms and m.v0 is None
        r = orig(ctx, dt_ms)
        if win_on:
            rec["ik"].append(ik)
        elif m.v0 is not None and len(rec["ik"]) and ctx.t_ms >= t1:
            ref = np.mean(rec["ik"], axis=0)
            exp = np.bincount(m.amph_side, ik - ref, minlength=2) * 1e6 / gl.F_C_PER_MOL / q["glia_k_volume_um3"]
            got = m.load_last
            d = np.abs(got - exp)
            scale = np.bincount(m.amph_side, np.abs(ik) + np.abs(ref), minlength=2) * 1e6 / gl.F_C_PER_MOL \
                / q["glia_k_volume_um3"]
            rec["worst_load_abs"] = max(rec["worst_load_abs"], float(d.max()))
            rec["worst_load_rel"] = max(rec["worst_load_rel"], float((d / scale).max()))
            dek = q["glia_rt_f_mV"] * np.log(m.ko / q["glia_k_bath_mM"])
            for ss, e0, sd in zip(k_secs, ek_base, m.amph_side):
                for s, e in zip(ss, e0):
                    rec["worst_ek_mV"] = max(rec["worst_ek_mV"], abs(s.ek - (e + dek[sd])))
            rec["n"] += 1
        return r

    m.step = wrapped
    clamp = None
    w0 = time.time()
    while b.t < 6000.0:
        if clamp is None and b.t >= cg.T_ON and m.v0 is not None:
            v_rest = float(np.mean(rec["v"]))
            clamp = b.h.SEClamp(b.soma[b.idx["AWCL"]](0.5))
            clamp.dur1, clamp.amp1, clamp.rs = 1e9, v_rest + 20.0, 0.01
        if clamp is not None and b.t >= cg.T_OFF:
            clamp.rs = cg.OFF_RS
        o = b.step(None, cg.DT)
        if m.v0 is None and b.t - cg.DT + 0.5 * cg.DT >= gl.GLIA_V0_WINDOWS[win][0]:
            rec["v"].append(float(o.v_mV[b.idx["AWCL"]]))
    ok = rec["n"] > 0 and rec["worst_load_rel"] <= 1e-9 and rec["worst_ek_mV"] <= 1e-9
    return {"steps_compared": rec["n"], "worst_load_rel": rec["worst_load_rel"],
            "worst_load_abs_mM_s": rec["worst_load_abs"], "worst_ek_mV": rec["worst_ek_mV"],
            "ko_end_mM": m.ko.tolist(), "awcl_index": j, "pass": bool(ok), "wall_s": time.time() - w0}


def zero(k, w):
    b = Brain(cells=cg.CELLS, toggles=tog(k, w))
    b.reset()
    m = next(x for x in b.mechs if isinstance(x, gl.Mech))
    t1 = gl.GLIA_V0_WINDOWS[w][1]
    kb, rows, w0 = m.q["glia_k_bath_mM"], [], time.time()
    while b.t < t1 + 20000.0:
        b.step(None, cg.DT)
        if b.t > t1:
            rows.append((b.t, *b.mech_out["amphid_k_mM"]))
    r = np.array(rows)
    dev = r[:, 1:] - kb
    i = int(np.argmax(np.abs(dev).max(axis=1)))
    return {"max_abs_dev_mM": float(np.abs(dev).max()), "at_s": float(r[i, 0] / 1000.0),
            "end_dev_mM": dev[-1].tolist(), "pass": bool(np.abs(dev).max() <= 0.05), "wall_s": time.time() - w0,
            "trace": {"t_s": (r[::10, 0] / 1000.0).tolist(), "k_left_mM": r[::10, 1].tolist(),
                      "k_right_mM": r[::10, 2].tolist()}}


def check(k, w):
    wt = cg.run(tog(k, w), f"{k}/{w} wt")
    z = cg.run(tog(k, w, glia_kbuffer="null"), f"{k}/{w} null")
    s = {"ceiling": wt["peak_k_left_mM"] <= 10.2 and wt["rise_over_base_left_mM"] >= 0.01,
         "tau": wt["tau_recovery_s"] is not None and 3.4 <= wt["tau_recovery_s"] <= 4.0,
         "null_slower": bool(wt["tau_recovery_s"] and z["tau_recovery_s"]
                             and z["tau_recovery_s"] >= 1.24 * wt["tau_recovery_s"])}
    s["pass"] = all(s.values())
    keys = ("peak_k_left_mM", "base_k_left_mM", "rise_over_base_left_mM", "tau_recovery_s", "t_peak_s",
            "left_v_pre_mV", "left_v_clamp_mV", "ek_shift_max_mV")
    return {"score": s, "wt": {x: wt[x] for x in keys}, "null": {x: z[x] for x in keys},
            "null_over_wt": (z["tau_recovery_s"] / wt["tau_recovery_s"]) if wt["tau_recovery_s"] and
            z["tau_recovery_s"] else None, "trace_wt": wt["trace"], "trace_null": z["trace"]}


def main():
    out = Path(sys.argv[1])
    parts = sys.argv[2:] or ["neutral", "identity", "zero", "check"]
    res = json.loads(out.read_text()) if out.exists() else {}
    for p in parts:
        if p == "neutral":
            res["neutral"] = neutral()
        elif p == "identity":
            res["identity"] = {w: identity(w) for w in ("first", "settled")}
        elif p in ("zero", "check"):
            res[p] = {}
            for k, w in FORMS:
                res[p][f"{k}/{w}"] = (zero if p == "zero" else check)(k, w)
                out.write_text(json.dumps(res, indent=1))
        out.write_text(json.dumps(res, indent=1))
        show = {k: ({kk: vv for kk, vv in v.items() if not kk.startswith("trace")} if isinstance(v, dict) else v)
                for k, v in res[p].items()} if isinstance(res[p], dict) else res[p]
        print(p, json.dumps(show, indent=1, default=str)[:3000], flush=True)


if __name__ == "__main__":
    main()
