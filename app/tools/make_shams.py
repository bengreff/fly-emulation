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

--onset-step-ms S (second set, rule seed 20261005) also moves sham k's onset to
500 + (k + 1) * S ms and excludes cells already used in --out. Added after the
first 8 shams were scored: at one onset, every sham's forced spikes fall on the
same steps (the kick stream depends on the seed and rate, not the target), and
the 9 shams gave 6 distinct outcomes, so the onset is varied as well as the cell.
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
    ap.add_argument("--onset-step-ms", type=float, default=0.0)
    a = ap.parse_args()
    base = json.loads(a.base.read_text())
    orig = set(base["events"][0]["target"]["bodyId"])
    seed = RULE_SEED
    if a.onset_step_ms:
        seed = RULE_SEED + 1
        for f in a.out.glob("sham-*.json"):
            orig |= set(json.loads(f.read_text())["events"][0]["target"]["bodyId"])
    t = atlas_table()
    kc = t[t["type"].astype(str).str.startswith("KC") & ~t["bodyId"].isin(orig)]
    pick = np.random.default_rng(seed).choice(len(kc), size=a.n, replace=False)
    a.out.mkdir(parents=True, exist_ok=True)
    for j, k in enumerate(sorted(pick)):
        bid, typ = int(kc["bodyId"].iloc[k]), str(kc["type"].iloc[k])
        p = copy.deepcopy(base)
        t0 = base["events"][0]["t_ms"] + (j + 1) * a.onset_step_ms
        p["title"] = f"Sham: a few forced spikes in one Kenyon cell ({typ} {bid}) at {t0:g} ms (noise floor)"
        p["events"][0]["t_ms"] = t0
        p["events"][0]["target"] = {"bodyId": [bid]}
        p["events"][0]["label"] = f"about 3 forced spikes in one {typ} (bodyId {bid})"
        p["sham_rule"] = (f"app/tools/make_shams.py: uniform draw from {len(kc)} model Kenyon cells, "
                          f"default_rng({seed}), excluding the original sham cell"
                          + (f" and earlier shams; onset 500 + {j + 1} x {a.onset_step_ms:g} ms" if a.onset_step_ms else ""))
        name = f"sham-kc-{bid}" + (f"-t{t0:g}" if a.onset_step_ms else "")
        (a.out / f"{name}.json").write_text(json.dumps(p, indent=1) + "\n")
        print(f"{name}: {typ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
