"""Write the graded-medulla variant runs: the watched visual-pathway control with the
T4/T5 inputs and T4/T5 graded (a labelled variant, not the profile), and moving bars
injected as current, to ask whether T4/T5 respond and whether they are direction
selective.

    .venv/bin/python app/tools/eye_sweep.py

Reads app/protocols/eye/control-watch-visual-m9r-s0.json (same seed, watch list and
patch) and writes, beside it:

  A  variant control: graded rows from app/protocols/eye/variant_graded_medulla.csv
     (whole-cell recordings only; Behnia et al. 2014, Groschner et al. 2022,
     Gruntman et al. 2018, 2019)
  A  medulla bars in 4 directions: an ON bar is current into the T4 inputs under it
     (Mi1, Tm3, Mi4, C3 +4 mV; Mi9 -4 mV), an OFF bar into the T5 inputs (Tm1, Tm2
     +4 mV). Tm4 and Tm9 have only calcium-imaging evidence, so they stay spiking in
     this variant and are not driven. Polarities: Behnia et al. 2014; Strother et al.
     2017 (calcium); the 4 mV is guessed, within the 7 mV graded range.
  B  variant control plus a tonic +7 mV into every L1, L2, L3 (guessed operating
     point): under the model's graded rule a cell transmits only above rest, and in
     the m9r control L1-L3 never rise above rest (light hyperpolarises them), so no
     light signal leaves the lamina. The bias is a probe of that rule, not a claim.
  B  photoreceptor ON bars in 4 directions: R1-R6, R7, R8 of the ommatidia under the
     bar +3 mV (guessed).

A bar covers cells within 3 column spacings of the sweep line across it and steps one
spacing every 50 ms, holding each cell 100 ms (so 2 columns wide), from 5 spacings
before the patch centre to 5 after; two sweeps per run, at 300 and 1100 ms. Cells are
placed by app/data/body/flybody/columns.json (derived); photoreceptors at their
ommatidium (eye.json, inferred alignment). Directions are mosaic axes; on the left
eye -x is front-to-back and -y is upward (fit of retinotopy.csv azimuth and elevation
near the patch: -10.1 deg azimuth and -9.2 deg elevation per spacing; inferred).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np

APP = Path(__file__).resolve().parents[1]
EYE = APP / "protocols" / "eye"
CONTROL = EYE / "control-watch-visual-m9r-s0.json"
ROWS = "app/protocols/eye/variant_graded_medulla.csv"
VARIANT = "graded medulla (T4/T5 inputs and T4/T5 graded; whole-cell evidence)"
DIRS = {"+x": (1, 0), "-x": (-1, 0), "+y": (0, 1), "-y": (0, -1)}
DIR_NOTE = {"+x": "back-to-front", "-x": "front-to-back", "+y": "downward", "-y": "upward"}
ON = {"Mi1": 4.0, "Tm3": 4.0, "Mi4": 4.0, "C3": 4.0, "Mi9": -4.0}
OFF = {"Tm1": 4.0, "Tm2": 4.0}
PR_MV = 3.0
L_BIAS = 7.0
SWEEPS_MS = (300.0, 1100.0)
STEP_MS, HOLD_MS, REACH, HALF_WIDTH = 50.0, 100.0, 5, 3.0


def bar_events(pos: np.ndarray, ids: np.ndarray, mv: np.ndarray, d: str, centre: np.ndarray,
               sp: float, what: str) -> list[dict]:
    """Current events for one moving bar over cells at `pos` (px), two sweeps."""
    u = np.asarray(DIRS[d], float)
    rel = (pos - centre) / sp
    along, across = rel @ u, rel @ np.array([-u[1], u[0]])
    k = np.rint(along).astype(int)
    under = (np.abs(k) <= REACH) & (np.abs(across) <= HALF_WIDTH)
    ev = []
    for s, t0 in enumerate(SWEEPS_MS):
        for step in range(-REACH, REACH + 1):
            for m in sorted(set(mv[under & (k == step)])):
                sel = under & (k == step) & (mv == m)
                ev.append({"t_ms": t0 + (step + REACH) * STEP_MS, "dur_ms": HOLD_MS, "effector": "current",
                           "mv": float(m), "target": {"bodyId": sorted(int(i) for i in ids[sel])},
                           "label": f"{what} {d} sweep {s + 1}, step {step:+d} ({int(sel.sum())} cells {m:+g} mV)"})
    return ev


def main() -> int:
    ctl = json.loads(CONTROL.read_text())
    body = APP / "data" / "body" / "flybody"
    eye, cols = json.loads((body / "eye.json").read_text()), json.loads((body / "columns.json").read_text())
    omm = np.c_[eye["centroid"]["x"], eye["centroid"]["y"]]
    sp = cols["spacing_px"]
    centre = omm[ctl["watch_note"]["patch_centre_ommatidium"]]
    c = cols["cells"]
    names = np.asarray(cols["types"])[np.asarray(c["type"])]
    left = np.asarray(c["eye"]) == 0
    cpos = np.c_[c["x"], c["y"]]
    cid = np.asarray(c["bodyId"], np.int64)
    pr = eye["photoreceptors"]["L"]
    ppos, pid = omm[np.asarray(pr["ommatidium"])], np.asarray(pr["bodyId"], np.int64)

    def base(arm: str, title: str, expect: str) -> dict:
        p = copy.deepcopy(ctl)
        p["title"] = title
        p["config"]["extra_params"] = ROWS
        p["variant"] = {"name": VARIANT, "arm": arm, "rows": ROWS,
                        "note": "a labelled variant of the profile for a discriminating run; not adopted"}
        p["expect"] = {"text": expect, "source": None, "status": "prediction"}
        p["events"] = []
        return p

    out = {}
    out["A-control"] = base("A", "Graded-medulla variant: control with the visual pathway watched, m9r seed 0",
                            "Prediction (written before the run): T4/T5 stay flat. L1-L3 never rise above "
                            "rest in the m9r control, so the graded rule passes no light signal to the medulla "
                            "whatever the medulla's mode.")
    for d in DIRS:
        for name, pat, what in (("on", ON, "ON bar into T4 inputs"), ("off", OFF, "OFF bar into T5 inputs")):
            m = left & np.isin(names, list(pat))
            p = base("A", f"Graded-medulla variant: {what} moving {d} ({DIR_NOTE[d]}), m9r seed 0",
                     "Prediction (written before the run): T4 (ON) or T5 (OFF) cells under the bar "
                     "depolarise; direction selectivity weak or absent (|DSI| < 0.2), because the injected "
                     "bar lacks the inputs' measured temporal filters; Maisak et al. 2013: T4a/T5a prefer "
                     "front-to-back, b back-to-front, c upward, d downward.")
            p["events"] = bar_events(cpos[m], cid[m], np.array([pat[t] for t in names[m]]), d, centre, sp, what)
            out[f"A-{name}{d}"] = p
    bias = [{"t_ms": 0.0, "dur_ms": ctl["duration_ms"], "effector": "current", "mv": L_BIAS,
             "target": {"type": t}, "label": f"tonic bias {t} +{L_BIAS:g} mV (guessed operating point)"}
            for t in ("L1", "L2", "L3")]
    p = base("B", "Graded-medulla variant with L1-L3 biased +7 mV: control, m9r seed 0",
             "Prediction (written before the run): L1-L3 now transmit and their light-driven "
             "hyperpolarisation reaches the medulla; whether T4/T5 move is the question.")
    p["events"] = copy.deepcopy(bias)
    out["B-control"] = p
    for d in DIRS:
        p = base("B", f"Graded-medulla variant with L1-L3 biased: photoreceptor ON bar moving {d} "
                      f"({DIR_NOTE[d]}), m9r seed 0",
                 "Prediction (written before the run): T4 respond more than T5 to an ON bar; "
                 "direction selectivity weak or absent (|DSI| < 0.2).")
        p["events"] = copy.deepcopy(bias) + bar_events(ppos, pid, np.full(len(pid), PR_MV), d, centre, sp,
                                                       "photoreceptor ON bar")
        out[f"B-pr{d}"] = p
    for k, p in out.items():
        path = EYE / f"graded-{k}-m9r-s0.json"
        path.write_text(json.dumps(p, indent=1) + "\n")
        n = sum(len(e["target"].get("bodyId", [])) for e in p["events"])
        print(f"{path.relative_to(APP.parent)}: {len(p['events'])} events, {n} cell-events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
