"""X1 cross-connectome control (s13, 14 Oct; DECISIONS 14 Oct 00:39): run a bypass harness with MANC counts swapped in.

DIAGNOSTIC, forced drive; no fitting, no new switch. Replaces `flyemu.connectome.load_tables` so the edge table seen by
`connectome.build` has MANC counts (runs/s13/xconn/manc_on_mcns_edges.parquet, from xconn_counts.py build) on every
edge between two swap-set cells; edges absent in MANC are removed and MANC-only edges added. Everything else (signs
from the male-CNS cell, thresholds, every profile mechanism, the min_synapses cut) is unchanged.
  --swap none  male CNS as is (M0)
  --swap core  DNg100, E1, E2, I1, IN19A007/A004/A002 with a one-to-one mancBodyid (Xc)
  --swap vnc   every VNC-set cell with a one-to-one mancBodyid (Xv)

    uv run python scripts/probes/xconn_swap.py --swap core --harness chain -- --drive-mv 25 --tag Xc_25mv --out ...
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(HERE))
from flyemu import connectome  # noqa: E402
from xconn_counts import CORE_MCNS, OUT, vnc_matched  # noqa: E402


def swapped(neurons: pd.DataFrame, edges: pd.DataFrame, mode: str) -> pd.DataFrame:
    m = vnc_matched(neurons)
    if mode == "core":
        m = m[m.type.isin(CORE_MCNS)]
    manc = pd.read_parquet(OUT / "manc_on_mcns_edges.parquet")
    S = set(m.bodyId) & (set(manc.pre) | set(manc.post))  # only cells whose MANC body is in the MANC table
    manc = manc[manc.pre.isin(S) & manc.post.isin(S)]
    inside = edges.pre.isin(S) & edges.post.isin(S)
    old = edges[inside]
    print(f"[xconn] swap {mode}: {len(S)} cells; male-CNS edges replaced {len(old)} ({int(old.weight.sum())} syn) "
          f"-> MANC {len(manc)} ({int(manc.weight.sum())} syn)", flush=True)
    return pd.concat([edges[~inside], manc.astype(edges.dtypes.to_dict())], ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--swap", choices=("none", "core", "vnc"), required=True)
    ap.add_argument("--harness", choices=("chain", "s2"), required=True)
    a, rest = ap.parse_known_args()
    rest = [x for x in rest if x != "--"]
    if a.swap != "none":
        orig = connectome.load_tables

        def load_tables():
            n, e = orig()
            return n, swapped(n, e, a.swap)
        connectome.load_tables = load_tables
    if a.harness == "chain":
        import bypass_s3_chain as h
    else:
        import bypass_s2_descending as h
    sys.argv = [h.__file__] + rest
    h.main()


if __name__ == "__main__":
    main()
