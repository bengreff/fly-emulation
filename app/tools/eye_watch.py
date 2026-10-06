"""Write a control protocol that also records the membrane potential of one patch of
visual columns, from photoreceptor to T4/T5, and of every lobula plate tangential cell.

    .venv/bin/python app/tools/eye_watch.py --profile m9r --seed 0 \
        --out app/protocols/eye/control-watch-visual-m9r-s0.json

Spikes alone cannot show the visual pathway: photoreceptors and L1-L3 are graded in
the model, so they never spike. The patch is a left-eye ommatidium and 2 rings around
it (up to 19 ommatidia), with one placed cell per type per ommatidium, the patch chosen
to cover the most (type, ommatidium) pairs; placements from
app/data/body/flybody/columns.json (derived). Every photoreceptor assigned to the
patch is watched too. The library control's own watch list (the readout and stimulated types) is
kept, by bodyId, so the run is the library control plus more watched rows; watching
does not change the dynamics, which the recording can be checked against.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
LPTC = ["HSE", "HSN", "HSS", "H1", "H2", "VS", "VSm", "HST", "VST1", "VST2"]
CONTROL_WATCH = ["MN9", "MDN", "DNa02", "DNg100", "LB3b", "LB3c"]     # app/protocols/control.json


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--rings", type=int, default=2)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    body = APP / "data" / "body" / "flybody"
    eye, cols = json.loads((body / "eye.json").read_text()), json.loads((body / "columns.json").read_text())
    omm = np.c_[eye["centroid"]["x"], eye["centroid"]["y"]]
    sp = cols["spacing_px"]
    c = cols["cells"]
    left = np.asarray(c["eye"]) == 0
    col = np.asarray(c["column"])
    radius = (a.rings + 0.25) * sp
    patches = cKDTree(omm).query_ball_point(omm, radius)
    # one cell per type per ommatidium, the nearest to its centre; the patch is the one
    # covering the most (type, ommatidium) pairs, so it avoids the pile-ups at the
    # mosaic's edge (several cells of a type on one ommatidium)
    ty, x, y = np.asarray(c["type"]), np.asarray(c["x"]), np.asarray(c["y"])
    pick = {}
    for i in np.flatnonzero(left):
        k, d = (int(ty[i]), int(col[i])), np.hypot(x[i] - omm[col[i], 0], y[i] - omm[col[i], 1])
        if k not in pick or d < pick[k][1]:
            pick[k] = (i, d)
    has = np.zeros(len(omm))
    for (_, o) in pick:
        has[o] += 1
    centre = int(np.argmax([has[p].sum() - 1e-3 * len(p) for p in patches]))
    patch = sorted(patches[centre])
    chosen = [i for (t, o), (i, _) in pick.items() if o in patch]
    in_patch = np.zeros(len(left), bool); in_patch[chosen] = True
    ids = np.asarray(c["bodyId"])[in_patch].tolist()
    pr = eye["photoreceptors"]["L"]
    ids += [b for b, o in zip(pr["bodyId"], pr["ommatidium"]) if o in patch]
    nr = pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet", columns=["bodyId", "type"])
    extra = nr[nr["type"].isin(LPTC + CONTROL_WATCH)]["bodyId"].astype(int).tolist()
    ids = sorted(set(int(i) for i in ids) | set(extra))
    doc = {
        "format": "flyemu-protocol/1",
        "title": f"Control with the visual pathway watched: {a.profile}, seed {a.seed}, no stimulus",
        "config": {"scan": "male-cns:v1.0", "body": "flybody", "profile": a.profile, "seed": a.seed,
                   "min_synapses": 5, "overrides": {}},
        "duration_ms": 2000, "genotype": [], "events": [],
        "expect": {"text": "The library control at this model and seed, with more rows watched; its spikes "
                           "should match the library control's exactly.", "source": None, "status": "control"},
        "record": {"watch": {"bodyId": ids}},
        "watch_note": {"patch_eye": "left", "patch_centre_ommatidium": centre, "patch_ommatidia": patch,
                       "patch_cells": int(in_patch.sum()), "lptc_and_control_watch": len(extra),
                       "basis": "derived: app/data/body/flybody/columns.json (built " + cols["created"] + ")"},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"{a.out}: {len(ids)} watched cells; patch of {len(patch)} ommatidia around {centre} "
          f"({int(in_patch.sum())} columnar cells), plus {len(extra)} tangential and control-watch cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
