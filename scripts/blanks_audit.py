"""Blanks audit (session 12): ledger coverage per grain, before vs after.

Compares the measurable-quantity ledger (data/ontology/fly_information.yaml) and
the mechanism inventory (data/model/mechanisms.yaml) at a git ref against the
working tree. For every measurable quantity it asks:
  slot      the ledger has a row for it
  carrier   the row names a mechanism that exists (built or a registered stub)
  simulated the model uses a value for it (fidelity != none)
  own grain the model's value varies at the quantity's own grain (fidelity element)
and, from data/derived/ledger_levels.csv, the share of slots at each source level.

    uv run python scripts/blanks_audit.py [--ref 80836db]
Run scripts/blank_ledger.py first so ledger_levels.csv is current.
Writes data/derived/blanks_audit_coverage.csv.
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from blank_ledger import GRAIN_GROUP  # noqa: E402

ORDER = ["synapse", "edge", "cell", "type", "class", "body part", "organism/world"]


def at(ref: str | None, path: str) -> str:
    if ref is None:
        return (REPO / path).read_text()
    return subprocess.run(["git", "show", f"{ref}:{path}"], cwd=REPO, check=True,
                          capture_output=True, text=True).stdout


def table(ref: str | None) -> pd.DataFrame:
    onto = yaml.safe_load(at(ref, "data/ontology/fly_information.yaml"))
    mech = {m["id"]: m for m in yaml.safe_load(at(ref, "data/model/mechanisms.yaml"))}
    rows = []
    for e in onto:
        m = mech.get(e["mech"])
        rows.append(dict(quantity=e["quantity"], grain=e["grain"],
                         grain_group=GRAIN_GROUP.get(e["grain"], "body part"),
                         slot=True, carrier=m is not None,
                         stub=bool(m and m["status"] == "absent"),
                         simulated=e["fidelity"] != "none", own_grain=e["fidelity"] == "element",
                         mech=e["mech"], upgrade=e.get("upgrade", ""), audit=e.get("audit", "")))
    return pd.DataFrame(rows).set_index("quantity")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="80836db", help="git ref of the state before the audit")
    a = ap.parse_args()
    before, after = table(a.ref), table(None)
    allq = after.index.union(before.index)
    b = before.reindex(allq)
    b["grain_group"] = b.grain_group.fillna(after.grain_group)
    for c in ("slot", "carrier", "simulated", "own_grain"):
        b[c] = b[c].astype("boolean").fillna(False).astype(bool)
    out = []
    for g in ORDER:
        bb, aa = b[b.grain_group == g], after[after.grain_group == g]
        n = len(aa)
        out.append(dict(grain=g, quantities=n,
                        slot_before=int(bb.slot.sum()), slot_after=int(aa.slot.sum()),
                        carrier_before=int(bb.carrier.sum()), carrier_after=int(aa.carrier.sum()),
                        stub_carried_after=int(aa.stub.sum()),
                        simulated_before=int(bb.simulated.sum()), simulated_after=int(aa.simulated.sum()),
                        own_grain_before=int(bb.own_grain.sum()), own_grain_after=int(aa.own_grain.sum())))
    cov = pd.DataFrame(out).set_index("grain")
    cov.loc["all"] = cov.sum()
    cov.to_csv(REPO / "data" / "derived" / "blanks_audit_coverage.csv")
    print(f"measurable quantities: {len(after)} (before {len(before)}; "
          f"{(after.audit == 's12').sum()} added by the s12 audit)\n")
    print("coverage per grain (counts of measurable quantities):")
    print(cov.to_string())
    gone = before.index.difference(after.index)
    if len(gone):
        print(f"\nrows removed or renamed since {a.ref}: {list(gone)}")
    # slot shares per grain, before vs after
    lv_b = pd.read_csv(io.StringIO(at(a.ref, "data/derived/ledger_levels.csv")))
    lv_a = pd.read_csv(REPO / "data" / "derived" / "ledger_levels.csv")
    for name, lv in (("before", lv_b), ("after", lv_a)):
        t = lv.pivot_table(index="grain_group", columns="level", values="slots", aggfunc="sum",
                           fill_value=0).reindex(ORDER).fillna(0)
        pct = (100 * t.div(t.sum(axis=1), axis=0)).round(1)
        pct.insert(0, "slots", t.sum(axis=1).astype(int))
        print(f"\nslot shares per grain, {name} (%):")
        print(pct.to_string())


if __name__ == "__main__":
    main()
