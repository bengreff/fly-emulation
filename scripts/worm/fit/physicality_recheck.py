"""One battery condition on the code on PYTHONPATH, scored by THIS checkout's vitals.physicality (weki, 9 Nov 2026).

For checking a new physicality rule on a worm an older commit built (the prior draws were run on f8e7699, and
sample_worm(seed) draws differently once the ledger gains specs). Writes OUTDIR/physicality.json with both verdicts.

Usage: PYTHONPATH=<old code>/src python scripts/worm/fit/physicality_recheck.py COND SECONDS OUTDIR [SEED]
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("_weki_vitals_new", ROOT / "src" / "wormemu" / "fit" / "vitals.py")
new = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = new                       # dataclasses look the module up
spec.loader.exec_module(new)

from wormemu.fit import vitals  # noqa: E402  (the code under test, from PYTHONPATH)

cond, secs, out = sys.argv[1], float(sys.argv[2]), Path(sys.argv[3])
seed = int(sys.argv[4]) if len(sys.argv) > 4 else None
got = {}
_old = vitals.physicality


def both(res, bounds, *a, **k):
    got["old"], got["new"] = _old(res, bounds, *a, **k), new.physicality(res, bounds, *a, **k)
    return got["old"]


vitals.physicality = both
vitals.run(None, cond, secs, out, seed=seed)
(out / "physicality.json").write_text(json.dumps({"code": vitals.__file__, "checker": spec.origin, "seed": seed,
                                                  **got}, indent=1, default=float))
for k in ("old", "new"):
    p = got[k]
    print(k, "physical", p["physical"], "v_out_cells", p["v_out_cells"], "alt_cells", p.get("alt_cells"),
          "alt_worst", p.get("alt_worst"), "v_out_worst", [w[:2] for w in p["v_out_worst"]])
