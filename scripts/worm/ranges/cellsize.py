"""Soma and neurite membrane area and volume of every BAAIWorm cell, from the 3D points of its hoc file (wranges,
7 Nov 2026). Derived, no new number: each pair of consecutive points is a frustum (lateral area
pi (r1 + r2) sqrt((r1 - r2)^2 + L^2), volume pi L (r1^2 + r1 r2 + r2^2) / 3), as NEURON computes area from 3D points
(no end caps). The joint constraints use it (Ca pool volume <= cell volume; passive input resistance).

    python scripts/worm/ranges/cellsize.py      writes scripts/worm/ranges/cell_sizes.csv and checks the total area
                                                against data/worm/structure/geometry.csv (NEURON's own area)
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
HOC = ROOT / "third_party/baaiworm/model"
OUT = Path(__file__).resolve().parent / "cell_sizes.csv"
PT = re.compile(r"^\s*(\w+)(?:\[\d+\])?\s*\{\s*pt3dadd\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,"
                r"\s*([-\d.eE+]+)\s*\)", re.M)


def sizes(path: Path) -> dict:
    secs: dict[str, list] = {}
    for m in PT.finditer(path.read_text()):
        secs.setdefault(m.group(1), []).append(tuple(float(m.group(i)) for i in range(2, 6)))
    out = dict(soma_area_um2=0.0, neurite_area_um2=0.0, soma_volume_um3=0.0, neurite_volume_um3=0.0)
    for name, pts in secs.items():
        part = "soma" if name.lower().startswith("soma") else "neurite"
        for (x1, y1, z1, d1), (x2, y2, z2, d2) in zip(pts, pts[1:]):
            L = math.dist((x1, y1, z1), (x2, y2, z2))
            r1, r2 = d1 / 2, d2 / 2
            out[f"{part}_area_um2"] += math.pi * (r1 + r2) * math.hypot(r1 - r2, L)
            out[f"{part}_volume_um3"] += math.pi * L * (r1 * r1 + r1 * r2 + r2 * r2) / 3
    return out


def table() -> pd.DataFrame:
    rows = [dict(name=f.stem, **sizes(f)) for f in sorted(HOC.glob("*.hoc"))]
    t = pd.DataFrame(rows)
    t["area_um2"] = t.soma_area_um2 + t.neurite_area_um2
    t["volume_um3"] = t.soma_volume_um3 + t.neurite_volume_um3
    return t


def load() -> pd.DataFrame:
    return pd.read_csv(OUT).set_index("name")


if __name__ == "__main__":
    t = table()
    t.round(4).to_csv(OUT, index=False)
    g = pd.read_csv(ROOT / "data/worm/structure/geometry.csv").set_index("name")
    j = t.set_index("name").join(g[["area_um2"]], rsuffix="_neuron", how="inner")
    rel = (j.area_um2 / j.area_um2_neuron - 1).abs()
    print(f"{len(t)} cells; {len(j)} in geometry.csv; area vs NEURON: median {rel.median():.2%}, max {rel.max():.2%}")
    print(t.describe().loc[["min", "50%", "max"]].round(2).to_string())
