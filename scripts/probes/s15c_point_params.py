"""s15c (fly, 21 Oct): the point-model parameters of the 106 T1 walking cells at a profile (m10f0), saved for the
single-cell gate 1 of the morphological hybrid (DECISIONS 21 Oct 01:38). Also records which point mechanisms touch
these cells, since the hybrid refuses or spreads them.

    .venv/bin/python scripts/probes/s15c_point_params.py [--profile m10f0] --out runs/s15/morph/point_params.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "connectome"))
from flyemu.gpu.equivalence import build_brain  # noqa: E402
import premotor_mn_geometry as pg  # noqa: E402


def cells() -> pd.DataFrame:
    n = pd.read_parquet(ROOT / "data" / "cache" / "male_cns_neurons.parquet")
    t1 = n.somaNeuromere.fillna("").str.startswith("T1")
    c = n[t1 & (n.type.isin(pg.LEG_TYPES) | n.type.isin(pg.CORE_TYPES))][["bodyId", "type", "instance"]].copy()
    c["cls"] = np.where(c.type.isin(pg.CORE_TYPES), "core_premotor", "leg_MN")
    return c.sort_values(["cls", "type", "instance"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    reg, conn, p, _ = build_brain({}, profile=a.profile, min_synapses=5)
    c = cells()
    idx = conn.index_of(c.bodyId.to_numpy())
    n = conn.n

    def arr(x):
        return np.broadcast_to(np.asarray(x, np.float64), (n,)) if np.ndim(x) == 0 else np.asarray(x, np.float64)
    cols = {k: arr(getattr(p, k)) for k in ("tau_m", "v_rest", "v_th", "v_reset", "t_ref", "tau_s", "spont_mv")}
    cols["v_leak"] = arr(p.v_leak) if p.v_leak is not None else cols["v_rest"]
    noise = np.sqrt(float(p.noise_mv) ** 2 + (arr(p.noise_class_mv) ** 2 if p.noise_class_mv is not None else 0.0))
    rows = []
    for k, r in c.iterrows():
        i = int(idx[k])
        row = dict(bodyId=int(r.bodyId), type=r.type, instance=r.instance, cls=r.cls, model_idx=i)
        if i >= 0:
            row.update({k2: float(v[i]) for k2, v in cols.items()})
            row["graded"] = bool(p.graded[i]) if p.graded is not None else False
            row["noise"] = float(arr(noise)[i])
        rows.append(row)
    mech = {"cond": bool(p.cond), "intrinsic": p.intrinsic is not None, "gap": getattr(p, "gap", None) is not None,
            "two_comp": p.two_comp is not None}
    Path(a.out).write_text(json.dumps(dict(profile=a.profile, mechanisms=mech, cells=rows), indent=1))
    df = pd.DataFrame(rows)
    print(mech, (df.model_idx < 0).sum(), "cells absent")
    print(df.groupby("cls")[["tau_m", "v_rest", "v_leak", "v_th", "tau_s", "spont_mv"]].describe().T.to_string())


if __name__ == "__main__":
    main()
