"""Phase-2 re-run of the triage's ephys score (wbrain2, 8 Nov 2026): the same cells, protocol, features and training
sweeps as scripts/worm/triage/ephys_score.py (RIM sealed, never scored), for named toggle sets.

Usage (backhouse): python ephys_rescore.py OUT.json FORM=tog:val,tog:val ... (FORM=- for the defaults)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "triage"))
import ephys_score as E  # noqa: E402  (applies at_ledger.patch on import)

E.FEATS = Path.home() / "worm-night/wexcite/fit2/train_features.npz"   # FIT2's training features (E reads argv[1])


def main():
    out, res = Path(sys.argv[1]), {}
    for arg in sys.argv[2:]:
        name, spec = arg.split("=", 1)
        extra = {} if spec == "-" else dict(kv.split(":", 1) for kv in spec.split(","))
        res[name] = E.score(extra, ["AIY", "AFD", "AWA"])
        for cls, x in res[name].items():
            print(name, cls, "rmse %.2f mV" % x.get("rmse_mV", float("nan")), "base",
                  x.get("model", {}).get("baseline", [None])[0], "data", x.get("data", {}).get("baseline", [None])[0],
                  flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
