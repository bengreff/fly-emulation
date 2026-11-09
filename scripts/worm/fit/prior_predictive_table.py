"""Summary of the prior predictive (weki, 8 Nov 2026; pre-registration in prior_predictive.sh): per sign the draws'
values, how many sit inside the band (all draws, and the admissible ones), the template's value beside them; per draw
physical, activity (neurons whose V range P95 - P5 after the settle is above 5 mV, of 302) and joint.check.

Usage: python scripts/worm/fit/prior_predictive_table.py PRIOR_DIR TEMPLATE_DIR   (the dirs hold seedK/food.json,
seedK/food.npz and food.json, food.npz)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "ranges"))
import joint  # noqa: E402
from wormemu.brain import sample_worm  # noqa: E402
from wormemu.fit import vitals  # noqa: E402


ATANAS_NOISE = 0.0417                   # atanas_noise.py (derived); kept here so the table runs on the run's own code
ATANAS_DT_S = 0.600


def signal_sd(npz):
    """GCaMP signal SD (median over neurons) on F / mean F of the stored traces resampled at 0.600 s after the settle:
    total^2 - (2 D1 - D2), as vitals.noise_sd (amendment 23:24 in prior_predictive.sh)."""
    d = np.load(npz)
    w = d["t"] >= vitals.SETTLE_S
    t, g = d["t"][w], np.asarray(d["gcamp"][w], float)
    tt = np.arange(t[0], t[-1] + 1e-9, ATANAS_DT_S)
    x = 1.0 + np.stack([np.interp(tt, t, g[:, j]) for j in range(g.shape[1])], axis=1)
    x = x / x.mean(axis=0)
    d1 = np.var(np.diff(x, axis=0), axis=0) / 2.0
    d2 = np.var(x[2:] - x[:-2], axis=0) / 2.0
    s2 = np.clip(x.var(axis=0) - np.clip(2.0 * d1 - d2, 0.0, None), 0.0, None)
    return float(np.median(np.sqrt(s2)))


def activity(npz):
    d = np.load(npz)
    w = d["t"] >= vitals.SETTLE_S
    neur = [j for j, c in enumerate(d["cells"]) if not str(c).startswith(("dBWM", "vBWM"))]
    v = d["v"][w][:, neur]
    return int(((np.percentile(v, 95, 0) - np.percentile(v, 5, 0)) > 5.0).sum())


def main(prior, template):
    prior, template = Path(prior), Path(template)
    led = sample_worm(None).led
    cons = joint.constraints(led)
    runs = {}
    for d in sorted(prior.glob("seed*"), key=lambda p: int(p.name[4:])):
        if (d / "food.json").exists():
            k = int(d.name[4:])
            vals = sample_worm(k).values
            runs[k] = dict(r=json.loads((d / "food.json").read_text()), act=activity(d / "food.npz"),
                           adm=not joint.check(vals, led, cons), noise=float(vals["obs_noise_dff"]),
                           sig=signal_sd(d / "food.npz"))
    tpl = json.loads((template / "food.json").read_text())
    tsc = vitals.score(tpl["readouts"], "food")
    ks = sorted(runs)
    print(f"draws {ks}; admissible {[k for k in ks if runs[k]['adm']]}")
    print("| Sign | Band | template | " + " | ".join(f"seed {k}{'' if runs[k]['adm'] else ' (x)'}" for k in ks)
          + " | in band: all | admissible |")
    print("|" + "---|" * (5 + len(ks)))
    for s in vitals.SIGNS:
        b = s.band()
        if b is None or "food" not in s.cond:
            continue
        vals, nin, nadm = [], 0, 0
        for k in ks:
            r = runs[k]["r"]
            sc = vitals.score(r["readouts"], "food").get(s.id) or {}
            v, st = sc.get("value"), sc.get("status")
            ok = st == "in" and r["physicality"]["physical"]
            nin += ok
            nadm += ok and runs[k]["adm"]
            vals.append("none" if v is None else f"{v:.3g}")
        tv = (tsc.get(s.id) or {}).get("value")
        note = ""
        if s.id == "gcamp_range":              # amendment 23:24: an in-band draw whose noise alone reaches the band
            nr = [k for k in ks if 3.29 * runs[k]["noise"] >= b[0]]
            bi = [k for k in ks if (vitals.score(runs[k]["r"]["readouts"], "food").get(s.id) or {}).get("status") == "in"
                  and runs[k]["r"]["physicality"]["physical"] and k not in nr]
            note = (f" from the brain: {len(bi)} of {len(ks)} (seeds {bi}); noise alone reaches the band: seeds {nr}")
        print(f"| {s.id} | {b[0]:.3g} to {b[1]:.3g} | {'none' if tv is None else f'{tv:.3g}'} | " + " | ".join(vals)
              + f" | {nin} of {len(ks)}{note} | {nadm} of {sum(runs[k]['adm'] for k in ks)} |")
    print("| physical | | " + ("yes" if tpl["physicality"]["physical"] else "no") + " | "
          + " | ".join("yes" if runs[k]["r"]["physicality"]["physical"] else "no" for k in ks) + " | | |")
    tnoise = float(sample_worm(None).values["obs_noise_dff"])
    tsig = signal_sd(template / "food.npz")
    print(f"| obs_noise_dff (drawn) | | {tnoise:.3g} | " + " | ".join(f"{runs[k]['noise']:.3g}" for k in ks) + " | | |")
    print(f"| noise-only range 3.29 x noise | | {3.29 * tnoise:.3g} | "
          + " | ".join(f"{3.29 * runs[k]['noise']:.3g}" for k in ks) + " | | |")
    print(f"| GCaMP signal SD (F / mean F) | | {tsig:.3g} | " + " | ".join(f"{runs[k]['sig']:.3g}" for k in ks) + " | | |")
    print(f"| range under Atanas's noise, 3.29 sqrt(sig^2 + {ATANAS_NOISE}^2) | | "
          f"{3.29 * np.hypot(tsig, ATANAS_NOISE):.3g} | "
          + " | ".join(f"{3.29 * np.hypot(runs[k]['sig'], ATANAS_NOISE):.3g}" for k in ks) + " | | |")
    print(f"| neurons with V range > 5 mV (of 302) | | {activity(template / 'food.npz')} | "
          + " | ".join(str(runs[k]["act"]) for k in ks) + " | | |")
    print("| wall per bio-s (s) | | " + f"{tpl['wall_per_bio_s']:.1f} | "
          + " | ".join(f"{runs[k]['r']['wall_per_bio_s']:.1f}" for k in ks) + " | | |")


if __name__ == "__main__":
    main(*sys.argv[1:3])
