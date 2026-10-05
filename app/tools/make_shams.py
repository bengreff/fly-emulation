"""Write sham protocols: the noise floor as a distribution, not one sample.

    .venv/bin/python app/tools/make_shams.py [--n 8] [--out app/protocols/sham]

Each sham is the library's sham (app/protocols/sham-one-cell.json: about three
forced spikes in one Kenyon cell at 500 ms, same configuration as the tests)
with a different cell. The rule is fixed before any sham is recorded: cells
drawn uniformly, without replacement, from the model's Kenyon cells (atlas
rows in the model whose type starts with "KC"), excluding the original sham's
cell, with numpy default_rng(20261004). Kenyon cells are used because they sit
in the mushroom body, away from the taste, descending and motor pathways the
tests read; any single cell would do as a minimal perturbation.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
from sessions import atlas_table  # noqa: E402

RULE_SEED = 20261004


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--base", type=Path, default=APP / "protocols" / "sham-one-cell.json")
    ap.add_argument("--out", type=Path, default=APP / "protocols" / "sham")
    a = ap.parse_args()
    base = json.loads(a.base.read_text())
    orig = set(base["events"][0]["target"]["bodyId"])
    t = atlas_table()
    kc = t[t["type"].astype(str).str.startswith("KC") & ~t["bodyId"].isin(orig)]
    pick = np.random.default_rng(RULE_SEED).choice(len(kc), size=a.n, replace=False)
    a.out.mkdir(parents=True, exist_ok=True)
    for k in sorted(pick):
        bid, typ = int(kc["bodyId"].iloc[k]), str(kc["type"].iloc[k])
        p = copy.deepcopy(base)
        p["title"] = f"Sham: a few forced spikes in one Kenyon cell ({typ} {bid}) at 500 ms (noise floor)"
        p["events"][0]["target"] = {"bodyId": [bid]}
        p["events"][0]["label"] = f"about 3 forced spikes in one {typ} (bodyId {bid})"
        p["sham_rule"] = (f"app/tools/make_shams.py: uniform draw from {len(kc)} model Kenyon cells, "
                          f"default_rng({RULE_SEED}), excluding the original sham cell")
        (a.out / f"sham-kc-{bid}.json").write_text(json.dumps(p, indent=1) + "\n")
        print(f"sham-kc-{bid}: {typ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
