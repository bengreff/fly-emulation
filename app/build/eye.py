"""Eye geometry for the fly's-eye view (M3): where each ommatidium sits in the hex
mosaic, its spectral type per eye, and which photoreceptor cells look through it.

    .venv/bin/python app/build/eye.py               # -> app/data/body/flybody/eye.json

Sources, read only:
- flygym's Retina (the renderer the model uses): `ommatidia_id_map` assigns each
  pixel of the 512 x 450 eye render to one of 721 ommatidia; an ommatidium's place
  in the mosaic is the centroid of its pixels (derived). Recorded eye frames have
  shape (2 eyes, 721, 2 channels), eyes in (left, right) order, one channel filled.
- the model's per-eye pale/yellow masks, `flyemu.vision.connectome_pale_masks`
  (derived from the R7/R8 subtype assignment; ties keep flygym's mask).
- `data/derived/retinotopy.csv`: photoreceptor bodyId -> eye and ommatidium (derived
  topology, inferred global alignment; the basis column is copied per cell).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(REPO / "src"))


def main() -> int:
    from flygym.vision.retina import Retina
    from flyemu import vision

    r = Retina()
    idm = r.ommatidia_id_map.astype(np.int64)          # 0 = outside the lattice, k = ommatidium k-1
    n = int(idm.max())
    rows, cols = np.nonzero(idm)
    ids = idm[rows, cols] - 1
    count = np.bincount(ids, minlength=n)
    cy = np.bincount(ids, rows, minlength=n) / count
    cx = np.bincount(ids, cols, minlength=n) / count
    left, right, n_assigned = vision.connectome_pale_masks(r.pale_type_mask.copy())
    rt = pd.read_csv(REPO / "data" / "derived" / "retinotopy.csv")
    rt = rt[rt.ommatidium >= 0]
    cells = {eye: rt[rt.eye == eye] for eye in ("L", "R")}
    doc = {
        "format": "flyemu-eye/1",
        "body": "flybody",
        "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "n_ommatidia": n,
        "eyes": ["left", "right"],
        "image": {"rows": int(idm.shape[0]), "cols": int(idm.shape[1]),
                  "desc": "the renderer's raw eye image; centroids are in its pixel units"},
        "centroid": {"x": np.round(cx, 2).tolist(), "y": np.round(cy, 2).tolist(),
                     "basis": "derived: mean pixel of each ommatidium in flygym's ommatidia_id_map"},
        "pixels": count.astype(int).tolist(),
        "pale": {"left": left.astype(int).tolist(), "right": right.astype(int).tolist(),
                 "flygym": r.pale_type_mask.astype(int).tolist(), "n_assigned_from_connectome": int(n_assigned),
                 "basis": "derived: majority of R7p/R8p vs R7y/R8y cells per ommatidium "
                          "(flyemu.vision.connectome_pale_masks); else flygym's canonical mask"},
        "photoreceptors": {
            eye: {"bodyId": c.bodyId.astype(int).tolist(), "type": c.type.tolist(),
                  "ommatidium": c.ommatidium.astype(int).tolist()} for eye, c in cells.items()},
        "photoreceptor_basis": sorted(set(rt.basis.astype(str))),
        "sources": ["flygym.vision.retina.Retina (compound_eye.npz)", "flyemu.vision.connectome_pale_masks",
                    "data/derived/retinotopy.csv"],
    }
    out = APP / "data" / "body" / "flybody" / "eye.json"
    out.write_text(json.dumps(doc, separators=(",", ":")) + "\n")
    n_cells = sum(len(c) for c in cells.values())
    print(f"{out.relative_to(REPO)}: {n} ommatidia per eye, {n_cells} photoreceptors with an ommatidium, "
          f"{n_assigned} ommatidia typed from the connectome, {out.stat().st_size / 1e3:.0f} kB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
