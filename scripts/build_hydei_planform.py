"""Extract the measured wing planform of Muijres et al. 2014 (Science 344:172,
Database S1 `wing_model`): chord per spanwise strip of the D. hydei wing used for
their robotic wing and quasi-steady model (20 strips, hinge to tip, wing length
2.986 mm). Output data/derived/muijres2014_wing_chords.csv; read by
flight.BladeElementWing(planform="hydei").

    uv run python scripts/build_hydei_planform.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "data" / "raw" / "flight_kinematics" / "muijres2014" / "FRUITFLY_LOOMINGRESPONSE_DATABASE.mat"
OUT = REPO / "data" / "derived" / "muijres2014_wing_chords.csv"


def main() -> None:
    wm = sio.loadmat(DB, squeeze_me=True, struct_as_record=False)["wing_model"]
    L = float(wm.length)
    r = -np.asarray(wm.y_sect_L)[1]                 # row 2 is minus the strip radius (left wing)
    c = np.asarray(wm.chords_L, float)
    assert np.allclose(c, wm.chords_R) and np.allclose(r, np.asarray(wm.y_sect_R)[1])
    df = pd.DataFrame(dict(strip=np.arange(1, len(c) + 1), r_mm=r.round(4), chord_mm=c.round(4),
                           r_over_L=(r / L).round(5), chord_over_L=(c / L).round(5)))
    dr = float(np.diff(r).mean())
    S = float(c.sum() * dr)
    r2 = float(np.sqrt((c * r ** 2).sum() * dr / S) / L)
    r3 = float(np.cbrt((c * r ** 3).sum() * dr / S) / L)
    head = (f"# D. hydei wing planform, Muijres et al. 2014 Science 344:172, Database S1 wing_model (measured; "
            f"left = right). Wing length {L:.3f} mm, strip width {dr:.4f} mm, strip-sum area {S:.4f} mm^2 "
            f"(settings_variables.ARwing_fly 3.1579 gives {L ** 2 / 3.1579:.3f}), r2/L {r2:.4f}, r3/L {r3:.4f}. "
            f"Built by scripts/build_hydei_planform.py.\n")
    OUT.write_text(head + df.to_csv(index=False))
    print(head)


if __name__ == "__main__":
    main()
