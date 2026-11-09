"""Glia rest reference (wbody2, 8 Nov 2026; item 8's A): what moves the amphid neurons off glia.py's v0 (their mean
over the first GLIA_V0_MS of a run) at zero input? Diagnostic only, nothing changed.

Both glia.py and pumps.py take their rest reference from the first 1000 ms after Brain.reset(), which starts every
cell at V_INIT -65 mV, and both start acting at 1 s (pumps: I = -(I_p(Na, V) - I_p(Na_rest, V0)); glia: a K+ load
g_K (V - V0) and the E_K shift current). check_glia's sub-brain (its CELLS, DT 5 ms, no clamp), 60 bio s, four
builds: defaults; na_k_pump off; glia_kbuffer fixed (no K+ load, no E_K current); both off.

Bar (written before running). Per build, the drift of each left and right amphid neuron = its mean V over a window
minus its mean V over 0-1 s, at 2-3, 9-10, 19-20, 29-30 and 59-60 s; and the settle time, the first t after which
the mean of every amphid neuron moves by at most 0.05 mV between consecutive 1 s windows up to 60 s. Verdict rule:
if the both-off build's largest |drift| at 19-20 s is <= 0.1 mV while the defaults' is >= 0.4 mV, the drift comes
from the two modules' own references (A, a reference rule fixes it); if the both-off build also drifts >= 0.4 mV, the
network itself is still settling at 1 s (the reference needs a settled window, or a slowly tracking term, B). Also
reported: the ending K+ against the bath at 20 s and 60 s (defaults), and each neuron's mean V over 59-60 s.
Added after a partial run of the defaults build on the pre-merge tree (largest drift 4.6-5.2 mV, no settle time;
the run was stopped when main was merged), reported only, bar and verdict rule unchanged: the median |drift| over
neurons; the left amphid mean drift (check_glia's statistic); the drift against the 1-2 s mean (past the start-up
transient from V_INIT -65 mV); and the noise floor, each neuron's SD of its 1 s means over 40-60 s.

Usage: python glia_v0_probe.py [build]   -> runs/worm/wbody2/glia_v0_probe.json (no argument runs all four)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "organs"))
BUILDS = {"defaults": {}, "pump_off": {"na_k_pump": "off"}, "glia_fixed": {"glia_kbuffer": "fixed"},
          "both_off": {"na_k_pump": "off", "glia_kbuffer": "fixed"}}
T_END, DT = 60000.0, 5.0
WINDOWS = [(2, 3), (9, 10), (19, 20), (29, 30), (59, 60)]


def run(name):
    import check_glia as cg
    from wormemu.brain import Brain
    from wormemu.brain_layers import AMPHID
    b = Brain(cells=cg.CELLS, toggles=BUILDS[name])
    b.reset()
    amph = [c for c in sorted(AMPHID) if c in b.idx]
    ix = [b.idx[c] for c in amph]
    vs, ks, ts = [], [], []
    while b.t < T_END:
        o = b.step(None, DT)
        vs.append(np.asarray(o.v_mV)[ix])
        ts.append(b.t)
        ko = b.mech_out.get("amphid_k_mM")
        ks.append(list(ko) if ko is not None else [np.nan, np.nan])
    vs, ks, t = np.array(vs), np.array(ks), np.array(ts) / 1000.0

    def wmean(a, lo, hi):
        return a[(t > lo) & (t <= hi)].mean(0)

    v0 = wmean(vs, 0, 1)
    drift = {f"{lo}-{hi}s": (wmean(vs, lo, hi) - v0).tolist() for lo, hi in WINDOWS}
    sec = np.array([wmean(vs, s, s + 1) for s in range(60)])
    moves = np.abs(np.diff(sec, axis=0)).max(1)                     # largest move of any neuron, 1 s to the next
    ok = [s + 1 for s in range(len(moves)) if (moves[s:] <= 0.05).all()]
    v1 = wmean(vs, 1, 2)
    left = np.array([c.endswith("L") for c in amph])
    late = {f"{lo}-{hi}s": wmean(vs, lo, hi) - v1 for lo, hi in WINDOWS}
    return dict(cells=amph, v0=v0.tolist(), drift=drift,
                max_abs_drift={k: float(np.abs(v).max()) for k, v in drift.items()},
                median_abs_drift={k: float(np.median(np.abs(v))) for k, v in drift.items()},
                left_mean_drift={k: float(np.mean(np.array(v)[left])) for k, v in drift.items()},
                max_abs_drift_from_1s={k: float(np.abs(v).max()) for k, v in late.items()},
                median_abs_drift_from_1s={k: float(np.median(np.abs(v))) for k, v in late.items()},
                noise_sd_1s_means=dict(median=float(np.median(sec[40:].std(0))), max=float(sec[40:].std(0).max())),
                settle_s=ok[0] if ok else None, moves_mV=moves.tolist(), v_59_60=wmean(vs, 59, 60).tolist(),
                k_20s=wmean(ks, 19, 20).tolist(), k_60s=wmean(ks, 59, 60).tolist())


def main():
    if len(sys.argv) > 1:
        print(json.dumps(run(sys.argv[1])))
        return
    res = {"bar": __doc__.split("Bar (written before running). ")[1].split("\n\nUsage")[0]}
    for name in BUILDS:
        p = subprocess.run([sys.executable, __file__, name], capture_output=True, text=True)
        if p.returncode:
            raise SystemExit(p.stderr[-2000:])
        res[name] = json.loads(p.stdout.strip().splitlines()[-1])
        r = res[name]
        print(name, "max", r["max_abs_drift"], "median", r["median_abs_drift"], "left", r["left_mean_drift"],
              "from_1s", r["max_abs_drift_from_1s"], "noise", r["noise_sd_1s_means"], "settle", r["settle_s"],
              flush=True)
    d, z = res["defaults"]["max_abs_drift"]["19-20s"], res["both_off"]["max_abs_drift"]["19-20s"]
    res["verdict"] = ("A: the modules' references drive the drift" if z <= 0.1 and d >= 0.4 else
                      "network still settling at 1 s" if z >= 0.4 else "neither rule met")
    out = ROOT / "runs/worm/wbody2/glia_v0_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(res["verdict"])


if __name__ == "__main__":
    main()
