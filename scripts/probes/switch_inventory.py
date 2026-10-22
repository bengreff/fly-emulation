"""Switch inventory (fly2, 21 Oct night, mechanism-complete brief): for every registry switch named in
data/model/mechanisms.yaml, its value under a profile, its neutral value as written in the yaml, and
whether the profile sets it.

    PYTHONPATH=src .venv/bin/python scripts/probes/switch_inventory.py --profile m10f0 --out x.csv
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import PROFILES  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, seed=12)
    inv = org.reg.inventory()
    inv["key"] = inv["entity"] + "|" + inv["property"]
    val = dict(zip(inv["key"], inv["value"]))
    basis = dict(zip(inv["key"], inv["basis"]))
    prof = PROFILES[a.profile]["values"]
    rows = []
    for m in yaml.safe_load(open(REPO / "data/model/mechanisms.yaml")):
        for k in m.get("switch") or []:
            rows.append({"id": m["id"], "status": m["status"], "switch": k,
                         "value": val.get(k, "NOT REQUIRED"), "basis": basis.get(k),
                         "set_by_profile": k in prof, "neutral": m.get("neutral")})
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print(pd.DataFrame(rows)[["id", "switch", "value", "set_by_profile"]].to_string())


if __name__ == "__main__":
    main()
