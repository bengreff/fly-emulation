"""The battery's noise-only spread (weki, 9 Nov 2026; pre-registered in the night file 03:03): the template worm at
several noise seeds, per condition and sign the values, mean, SD, min-max and in how many the sign is in its bar, and
FLIPS where the in/out status changes with the noise seed alone. The SDs are FIT_GENERAL section 7's simulation-noise
term for Gamma; nothing is fitted.

Usage: python scripts/worm/fit/noise_spread_table.py SEED0_DIR NOISE_DIR   (SEED0_DIR holds the battery's food.json and
nofood.json at the default noise, seed 0; NOISE_DIR holds nsN/food.json and nsN/nofood.json from `vitals run
--noise-seed=N`)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from wormemu.fit import vitals


def load(seed0, noise):
    runs = {0: Path(seed0)}
    for d in sorted(Path(noise).glob("ns*"), key=lambda p: int(p.name[2:])):
        runs[int(d.name[2:])] = d
    out = {}
    for c in ("food", "nofood"):
        out[c] = {n: json.loads((d / f"{c}.json").read_text()) for n, d in runs.items() if (d / f"{c}.json").exists()}
    return out


def main(seed0, noise):
    runs = load(seed0, noise)
    flips = []
    for c, rs in runs.items():
        ns = sorted(rs)
        if not ns:
            continue
        print(f"\n{c}: noise seeds {ns}; physical {sum(bool(rs[n]['physicality']['physical']) for n in ns)} of {len(ns)}")
        print("| Sign | Bar | " + " | ".join(f"ns {n}" for n in ns) + " | mean | SD | min to max | in bar |")
        print("|" + "---|" * (6 + len(ns)))
        for s in vitals.SIGNS:
            if c not in s.cond:
                continue
            sc = [vitals.score(rs[n]["readouts"], c).get(s.id) or {} for n in ns]
            st = [x.get("status") for x in sc]
            v = np.array([np.nan if x.get("value") is None else float(x["value"]) for x in sc])
            b = s.band()
            ok = ~np.isnan(v)
            m, sd = (float(np.mean(v[ok])), float(np.std(v[ok], ddof=1))) if ok.sum() > 1 else (np.nan, np.nan)
            nin = sum(x == "in" for x in st)
            scored = sum(x in ("in", "miss") for x in st)
            flip = b is not None and 0 < nin < len(ns)
            if flip:
                flips.append(f"{c}:{s.id}")
            cells = ["none" if np.isnan(x) else f"{x:.3g}" for x in v]
            rng = f"{np.nanmin(v):.3g} to {np.nanmax(v):.3g}" if ok.any() else "none"
            inb = "no bar" if b is None else f"{nin} of {len(ns)}" + (" FLIPS" if flip else "") + (
                f" ({len(ns) - scored} not produced or too short)" if scored < len(ns) else "")
            print(f"| {s.id} | {'none' if b is None else f'{b[0]:.3g} to {b[1]:.3g}'} | " + " | ".join(cells)
                  + f" | {m:.3g} | {sd:.3g} | {rng} | {inb} |")
        print("| wall per bio-s (s) | | " + " | ".join(f"{rs[n]['wall_per_bio_s']:.1f}" for n in ns) + " | | | | |")
    print(f"\nsigns whose in/out changes with the noise seed alone: {flips if flips else 'none'}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
