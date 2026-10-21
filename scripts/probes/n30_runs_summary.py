"""Summarise gf_latency.py outputs for the N30 runs: per type, follow fraction, median muscle latency and spikes
per GF window, per arm.

    .venv/bin/python scripts/probes/n30_runs_summary.py runs/s21/optB_*.json
"""
import json
import sys

for f in sys.argv[1:]:
    d = json.load(open(f))
    for arm, a in d["arms"].items():
        for k in ("DLMn a, b", "DLMn c-f", "PSI"):
            v = a["types"][k]
            print(f"{f.split('/')[-1]:22s} {arm:8s} {k:10s} follow {v['follow_fraction']:.2f} "
                  f"muscle {v['muscle_ms_median']} ms spikes/window {v['spikes_per_window_mean']} "
                  f"per cell {v['per_cell_follow']}")
