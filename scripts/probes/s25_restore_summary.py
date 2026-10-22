"""s25 scorer for the DA-only restoration runs (DECISIONS 22 Oct 04:11 and amendment 04:22).

Hattori confirm: mean recovery over seeds at n = 1, 3, 6, 10 inside Hattori 2017 Fig 6F +- 2 SEM, and
PPL1-a'3 contacting MBON-a'3. Also prints the counted S (compartment DAN spike-steps per stimulation).
Hige regression: forward CS+ ratio inside 0.06-0.14 at every seed.

    .venv/bin/python scripts/probes/s25_restore_summary.py [--dir runs/s25/restore]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

BAND = {1: (-0.02, 0.18), 3: (0.04, 0.32), 6: (0.21, 0.45), 10: (0.28, 0.52)}
HIGE = (0.06, 0.14)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=Path("runs/s25/restore"))
    a = ap.parse_args()
    hat = {int(p.stem.split("_s")[1]): json.loads(p.read_text()) for p in sorted(a.dir.glob("hattori_s*.json"))}
    hig = {int(p.stem.split("_s")[1]): json.loads(p.read_text()) for p in sorted(a.dir.glob("hige_fwd_s*.json"))}
    if hat:
        rec = {n: [] for n in BAND}
        for s, d in hat.items():
            r = d["restore"]
            rows = {row["n"]: row for row in r["rows"]}
            steps = [rows[n]["compartment_dan_spike_steps"] for n in BAND]
            print(f"hattori seed {s}: contact {d['dan_contacts_mbon']} {r['contact_dans']}, suppressed ratio "
                  f"{r['ratio_suppressed']:.4f}, kicks/stim {r['kicks_per_stim']}, S counted "
                  f"{[round(k / n, 2) for k, n in zip(steps, BAND)]}, KC spikes during stims "
                  f"{rows[10]['kc_spikes']}, recovery "
                  + ", ".join(f"n{n} {rows[n]['recovery']:.3f}" for n in BAND))
            for n in BAND:
                rec[n].append(rows[n]["recovery"])
        ok = all(d["dan_contacts_mbon"] for d in hat.values())
        for n, (lo, hi) in BAND.items():
            m = float(np.mean(rec[n]))
            ok &= lo <= m <= hi
            print(f"  n {n}: mean recovery {m:.3f} (range {min(rec[n]):.3f}-{max(rec[n]):.3f}), band {lo}..{hi}, "
                  f"{'inside' if lo <= m <= hi else 'OUTSIDE'}")
        print(f"HATTORI CONFIRM ({len(hat)} seeds): {'PASS' if ok else 'FAIL'}")
    if hig:
        ok = True
        for s, d in hig.items():
            cp = next(x for x in d["result"] if x["set"] == "cs_plus")["charge_ratio"]
            cm = next(x for x in d["result"] if x["set"] == "cs_minus")["charge_ratio"]
            ok &= HIGE[0] <= cp <= HIGE[1]
            print(f"hige forward seed {s}: CS+ {cp:.4f}, CS- {cm:.4f}")
        print(f"HIGE REGRESSION ({len(hig)} seeds): {'PASS' if ok else 'FAIL'} (band {HIGE[0]}-{HIGE[1]} every seed)")


if __name__ == "__main__":
    main()
