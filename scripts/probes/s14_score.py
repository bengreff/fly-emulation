"""s14 scoring (DECISIONS 20 Oct 22:28, s14 pre-registration). Written before any s14 network output existed.

Pass, per arm and drive, on the S2 run: `s4b_score.rhythm` -> rhythm_pass (two antagonist pools of one leg at depth
>= 0.5 and drive-locked, out of phase, leg-MN rate stops at drive-off). It is confirmed only by viewing the raster.
Secondary, on the chain run (drive window 200-900 ms), per leg neuromere:
  - E1/E2 spikes per cycle (rate / E1 rhythm frequency);
  - I1 recruited: spiking I1 fires at >= 0.5 x the E1 cycle frequency (X1's criterion); graded I1 sits >= 2 mV above
    rest on average and swings >= 2 mV when folded at the E1 period (12 bins).

    python scripts/probes/s14_score.py runs/s14/arms [--out runs/s14/arms/score.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4b_score import rhythm  # noqa: E402

ARMS = ("M0", "A", "B4", "B2", "C4", "C2")
DRIVES = (15, 25, 40)
W = (200, 900)          # chain drive window scored, ms (on 100 + 100 settling, off 900)


def folded_swing(v: np.ndarray, f_hz: float, nb: int = 12) -> float:
    ph = ((np.arange(v.size) / 1000.0 * f_hz) % 1.0 * nb).astype(int)
    m = np.array([v[ph == b].mean() for b in range(nb) if (ph == b).any()])
    return float(m.max() - m.min())


def chain_summary(d: Path, arm: str, mv: int) -> dict | None:
    js, tr = d / f"{arm}_{mv}mv.json", d / f"{arm}_{mv}mv_traces.npz"
    if not js.exists() or not tr.exists():
        return None
    res, z = json.loads(js.read_text()), np.load(tr, allow_pickle=False)
    V, S, lab = z["V"], z["S"], [str(x) for x in z["labels"]]
    cells = {r["cell"]: r for r in res["cells"]}
    out = {}
    for seg in sorted({c.split()[1] for c in cells}):
        e1 = cells.get(f"E1 {seg}")
        f0 = e1 and e1["rhythm_hz"]
        row = {"f0_hz": f0}
        for role in ("E1", "E2"):
            c = cells.get(f"{role} {seg}")
            row[f"{role}_spk_per_cycle"] = round(c["rate_hz"] / f0, 2) if c and f0 else None
        c = cells.get(f"I1 {seg}")
        if c is not None:
            v = V[W[0]:W[1], lab.index(f"I1 {seg}")]
            if c["graded"]:
                dv = float(v.mean()) - c["v_rest"]
                sw = folded_swing(v, f0) if f0 else 0.0
                row.update(I1_graded=True, I1_dv_mean=round(dv, 2), I1_swing=round(sw, 2),
                           I1_recruited=bool(f0 and dv >= 2.0 and sw >= 2.0))
            else:
                row.update(I1_graded=False, I1_rate=c["rate_hz"], I1_vmax=c["v_max"],
                           I1_recruited=bool(f0 and c["rate_hz"] >= 0.5 * f0))
        out[seg] = row
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    root = Path(a.root)
    res = {}
    for arm in ARMS:
        for mv in DRIVES:
            k = f"{arm}_{mv}mv"
            s2 = root / "s2" / f"s2_{k}_traces.npz"
            r = {"s2": rhythm(np.load(s2, allow_pickle=False)) if s2.exists() else None,
                 "chain": chain_summary(root / "chain", arm, mv)}
            res[k] = r
            s, c = r["s2"], r["chain"] or {}
            t1 = c.get("T1L", {})
            n_rec = sum(bool(x.get("I1_recruited")) for x in c.values())
            print(f"{k:8s} pass {None if s is None else s['rhythm_pass']!s:5s} "
                  f"transfer {0 if s is None else len(s['transfer_pass']):2d} pairs {0 if s is None else len(s['antagonist_pairs'])} "
                  f"post/pre {None if s is None else s['post_over_pre']} | T1L f0 {t1.get('f0_hz')} "
                  f"E1 {t1.get('E1_spk_per_cycle')} E2 {t1.get('E2_spk_per_cycle')} I1 rec {t1.get('I1_recruited')} "
                  f"(rate {t1.get('I1_rate')}, vmax {t1.get('I1_vmax')}, dV {t1.get('I1_dv_mean')}, swing {t1.get('I1_swing')}) "
                  f"| I1 recruited in {n_rec}/{len(c)} neuromeres")
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
