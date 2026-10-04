"""Session 12 B (standing): does the connectome carry a load reflex from the
leg campaniform sensilla to the leg's support motor pools?

Structure only, no simulation. Builds the working-profile Organism (m9w:
afferents assigned by nerve), takes each leg's load afferents
(sense channel 'load') and sums signed synapse counts (sign of the
presynaptic neuron x synapse count) onto the same leg's motor neurons,
grouped by male-cns type: direct (CS -> MN) and two-hop (CS -> one
interneuron -> MN, sum over paths of w1 * w2 / input synapses of the
interneuron, i.e. the interneuron's share of its input that is load).

    uv run python scripts/probes/load_reflex_paths.py [--out runs/s12/standing] [--set KEY=V]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import neuromuscular  # noqa: E402
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

LEG_KEY = {"fl": "lf", "ml": "lm", "hl": "lh", "fr": "rf", "mr": "rm", "hr": "rh"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "standing"))
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V",
                    help="registry override, e.g. sense:mechano|assign_by_nerve=2")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (x.split("=", 1) for x in a.set)}
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, seed=0, with_camera=False,
                   overrides=ov)
    c, aff = org.conn, org.aff
    n = c.n
    pre = np.repeat(np.arange(n), np.diff(c.indptr))
    w = c.sign[pre] * c.weight_syn                               # signed synapse count per edge
    in_tot = np.bincount(c.indices, weights=c.weight_syn, minlength=n)
    mf = pd.read_csv(neuromuscular.FORCE_TABLE, comment="#")
    mf["row"] = c.index_of(mf.bodyId.to_numpy())
    mf["leg"] = mf.leg.map(lambda s: LEG_KEY.get(s, s))
    mf = mf[mf.row >= 0]
    res = {}
    for L in ("lf", "lm", "lh", "rf", "rm", "rh"):
        cs = aff.rows[(aff.leg == L) & (aff.channel == "load")]
        src = np.zeros(n, bool); src[cs] = True
        e1 = src[pre]
        # direct CS -> anything, as a dense vector over targets
        d1 = np.bincount(c.indices[e1], weights=w[e1], minlength=n)
        # two-hop through non-afferent interneurons, normalised by the interneuron's input
        share = np.where(in_tot > 0, d1 / np.maximum(in_tot, 1), 0.0)
        share[cs] = 0.0
        d2 = np.bincount(c.indices, weights=share[pre] * w, minlength=n)
        mn = mf[mf.leg == L]
        g = mn.assign(direct=d1[mn.row], two_hop=d2[mn.row]).groupby(["joint", "type"]).agg(
            n=("row", "size"), direct=("direct", "sum"), two_hop=("two_hop", "sum"))
        res[L] = dict(n_load_afferents=int(len(cs)),
                      by_pool={f"{j}|{t}": dict(n=int(r.n), direct=round(float(r.direct), 1),
                                                two_hop=round(float(r.two_hop), 2))
                               for (j, t), r in g.iterrows()})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tag = "".join(f"_{k.split('|')[-1]}{v:g}" for k, v in ov.items())
    (out / f"load_reflex_paths{tag}.json").write_text(json.dumps(res, indent=1))
    pools = sorted({p for r in res.values() for p in r["by_pool"]})
    print("n load afferents:", {L: r["n_load_afferents"] for L, r in res.items()})
    print(f"{'pool':44s} " + " ".join(f"{L:>14s}" for L in res))
    for p in pools:
        cells = []
        for L in res:
            v = res[L]["by_pool"].get(p)
            cells.append(f"{v['direct']:6.0f}/{v['two_hop']:6.1f}" if v else f"{'-':>14s}")
        print(f"{p:44s} " + " ".join(f"{x:>14s}" for x in cells))


if __name__ == "__main__":
    main()
