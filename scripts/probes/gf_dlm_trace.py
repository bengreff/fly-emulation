"""DLMn membrane potential after one giant-fibre spike, per arm (fly2, s14 figure for F-GJ-5).

Builds the gf_latency organism (gaps on) once per arm, settles 200 ms, kicks both GFs once and records
PSI and DLMn a, b for 30 ms. Arms: the shared per-synapse scale (PSI cholinergic) and the measured
unitary PSP (Fayyazuddin 2006, 4.71 mV). Measures; not an objective.

    .venv/bin/python scripts/probes/gf_dlm_trace.py --out docs/media/s14_fly2_psi_dlm.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402

PSI = {"connectome:identified|nt_from_physiology": 1.0}
ARMS = {"shared scale (count x efficacy)": PSI,
        "measured unitary PSP 4.71 mV": {**PSI, "connectome:identified|unitary_psp_from_recordings": 1.0}}


def trace(profile: str, extra: dict, ms: float = 30.0) -> dict:
    org = Organism(policy="minimal", profile=profile, min_synapses=profiles.WORKING_MIN_SYNAPSES, seed=0,
                   overrides={**extra, "electrical:all|gap_conductance": 1.0})
    net, conn, dt = org.net, org.conn, org.timestep_ms
    t = conn.neurons.type.fillna("").to_numpy()
    gf, psi, dlm = (np.flatnonzero(t == x) for x in ("DNp01", "PSI", "DLMn a, b"))
    for _ in range(int(200 / dt)):
        net.step()
    v, spk = [], {"PSI": [], "DLMn a, b": []}
    for s in range(int(ms / dt)):
        out = net.step(kick=(gf, 100.0) if s == 0 else None)
        v.append(net.v[np.concatenate([psi, dlm])].copy())
        for name, ix in (("PSI", psi), ("DLMn a, b", dlm)):
            if np.isin(out, ix).any():
                spk[name].append(round(s * dt, 2))
    v = np.array(v)
    return {"t_ms": (np.arange(len(v)) * dt).tolist(), "psi": v[:, :len(psi)].tolist(),
            "dlm": v[:, len(psi):].tolist(), "v_th": float(np.broadcast_to(net.v_th, (conn.n,))[dlm[0]]),
            "spikes_ms": spk}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    res = {name: trace(a.profile, extra) for name, extra in ARMS.items()}
    a.out.with_suffix(".json").write_text(json.dumps(
        {k: {"dlm_peak_mv": float(np.max(r["dlm"])), "dlm_start_mv": float(r["dlm"][0][0]),
             "spikes_ms": r["spikes_ms"], "v_th": r["v_th"]} for k, r in res.items()}, indent=1) + "\n")
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for (name, r), c in zip(res.items(), ("tab:gray", "tab:blue")):
        d = np.array(r["dlm"])
        ax.plot(r["t_ms"], d[:, 0], color=c, lw=2, label=f"DLMn a, b: {name}")
        if d.shape[1] > 1:
            ax.plot(r["t_ms"], d[:, 1], color=c, lw=1, ls="--")
    ax.axhline(res[next(iter(res))]["v_th"], color="tab:red", lw=1, label="DLMn threshold (shared default, guessed)")
    ax.axhline(-52 + 4.71, color="tab:blue", lw=0.8, ls=":", label="rest + 4.71 mV (Fayyazuddin 2006, MN5 soma)")
    ax.axvline(0.3, color="0.6", lw=0.8, ls=":", label="PSI spike (0.3 ms, via GF gap junction)")
    ax.set_xlabel("time after GF spike (ms)")
    ax.set_ylabel("membrane potential (mV)")
    ax.set_title("One GF spike: DLMn a, b (MN5) stays below threshold in both arms", fontsize=10)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(a.out, dpi=130)
    print(json.dumps(json.loads(a.out.with_suffix(".json").read_text()), indent=1))


if __name__ == "__main__":
    main()
