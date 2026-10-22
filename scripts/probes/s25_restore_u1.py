"""U1 (s25, DECISIONS 22 Oct 04:11): with kc_mbon_dan_restore_rate at 0, lif.py is bit-identical to
a reference lif.py (default: the commit before the s25 rule) under the m10f4 KC overrides.
Compares every weight and every step's spikes over a KC-then-DAN pairing and 50 free steps.

    .venv/bin/python scripts/probes/s25_restore_u1.py [--ref c0b2f78]
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OV = {"cell_type:all|kc_mbon_ltd_timing_rate": 0.42991, "cell_type:all|kc_mbon_forgetting": 1.0,
      "cell_type:all|kc_mbon_memory_tau_h": 3.0}


def run(org, mod):
    org.lif = mod
    o = org.Organism(policy="minimal", profile="m4", min_synapses=5, overrides=OV)
    n = o.net
    t = o.conn.neurons.type.fillna("")
    dan = np.flatnonzero(t.str.match(r"^(PAM|PPL1)").to_numpy())
    kc = np.flatnonzero(n.is_kc)[:600]
    spikes = []
    for grp in (kc, dan, kc, dan):
        for _ in range(30):
            spikes.append(n.step(kick=(grp, 50.0)).copy())
    for _ in range(50):
        spikes.append(n.step().copy())
    return n.w.copy(), n.kc_e.copy(), n.kc_w0.copy(), spikes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="c0b2f78")
    a = ap.parse_args()
    src = subprocess.run(["git", "-C", str(REPO), "show", f"{a.ref}:src/flyemu/lif.py"],
                         capture_output=True, text=True, check=True).stdout
    ref_path = REPO / "src/flyemu/_lif_ref_u1.py"   # beside lif.py: it finds data/ from __file__
    ref_path.write_text(src)
    import flyemu.lif as lif_new
    import flyemu.organism as org
    spec = importlib.util.spec_from_file_location("flyemu.lif_ref", ref_path)
    lif_ref = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = lif_ref         # dataclasses look their module up here
    spec.loader.exec_module(lif_ref)
    wa, ea, w0a, sa = run(org, lif_new)
    try:
        wb, eb, w0b, sb = run(org, lif_ref)
    finally:
        ref_path.unlink()
    org.lif = lif_new
    same_sp = len(sa) == len(sb) and all(np.array_equal(x, y) for x, y in zip(sa, sb))
    depressed = int(np.sum(wa[ea] < w0a))
    print(f"ref {a.ref}: weights identical {np.array_equal(wa, wb)}, spikes identical {same_sp}, "
          f"steps {len(sa)}, spikes {sum(x.size for x in sa)}, "
          f"KC->MBON edges depressed {depressed} of {ea.size}")


if __name__ == "__main__":
    main()
