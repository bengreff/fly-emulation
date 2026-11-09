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
            runs[k] = dict(r=json.loads((d / "food.json").read_text()), act=activity(d / "food.npz"),
                           adm=not joint.check(sample_worm(k).values, led, cons))
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
        print(f"| {s.id} | {b[0]:.3g} to {b[1]:.3g} | {'none' if tv is None else f'{tv:.3g}'} | " + " | ".join(vals)
              + f" | {nin} of {len(ks)} | {nadm} of {sum(runs[k]['adm'] for k in ks)} |")
    print("| physical | | " + ("yes" if tpl["physicality"]["physical"] else "no") + " | "
          + " | ".join("yes" if runs[k]["r"]["physicality"]["physical"] else "no" for k in ks) + " | | |")
    print(f"| neurons with V range > 5 mV (of 302) | | {activity(template / 'food.npz')} | "
          + " | ".join(str(runs[k]["act"]) for k in ks) + " | | |")
    print("| wall per bio-s (s) | | " + f"{tpl['wall_per_bio_s']:.1f} | "
          + " | ".join(f"{runs[k]['r']['wall_per_bio_s']:.1f}" for k in ks) + " | | |")


if __name__ == "__main__":
    main(*sys.argv[1:3])
