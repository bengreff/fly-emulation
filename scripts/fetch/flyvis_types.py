"""Tabulate the flyvis (Lappalainen et al. 2024) ensemble's fitted per-type parameters.

Each of the 50 published networks (task: optical flow on Sintel; connectome fib25-fib19_v2.2) has
65 cell types with a fitted membrane time constant and resting potential, and 604 source→target type
pairs with a fitted synapse-count scale. The parameters are stored grouped in the order the
connectome builder first meets each group (pandas groupby sort=False over the node and edge
tables), so this rebuilds that order from the connectome spec shipped in the wheel: node types in
spec order; edge types in spec order, dropping any spec edge that creates no edge on the extent-15
hexagonal lattice.

Model (flyvis PPNeuronIGRSynapses): tau_t dV/dt = -V + V_rest,t + sum_j sign*n_syn*alpha_st*relu(V_j) + x,
with tau floored at the integration step (20 ms in training). Voltages are in arbitrary units.

    uv run python scripts/fetch/flyvis_types.py --out data/derived/flyvis_lappalainen2024_types.csv
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flyvis_checkpoint import load  # noqa: E402

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "flyvis_lappalainen2024"
EXTENT = 15
TRAIN_DT_S = 0.02   # MultiTaskSintel dt in every model's _meta.yaml (checked on model 000)


def spec() -> dict:
    with zipfile.ZipFile(RAW / "flyvis-1.2.0-py3-none-any.whl") as z:
        return json.loads(z.read("flyvis/connectome/fib25-fib19_v2.2.json"))


def lattice(typ_pattern) -> set[tuple[int, int]]:
    pattern, args = typ_pattern
    if pattern == "single":
        return {(0, 0)}
    us, vs = (args, args) if pattern == "tile" else args
    n = EXTENT
    return {(u, v) for u in range(-n, n + 1) for v in range(max(-n, -n - u), min(n, n - u) + 1)
            if u % us == 0 and v % vs == 0}


def edge_types(s: dict) -> list[tuple[str, str, int]]:
    """(source, target, sign) per fitted syn_strength entry, in parameter order."""
    cols = {n["name"]: lattice(n["pattern"]) for n in s["nodes"]}
    out = []
    for e in s["edges"]:
        src, tar = cols[e["src"]], cols[e["tar"]]
        offs = [o[0] for o in e["offsets"]]
        # fill_hull only adds offsets inside the hull of the listed ones; it cannot create the
        # first edge of a pair that has none, so the listed offsets decide existence
        if any((u + du, v + dv) in tar for (du, dv) in offs for (u, v) in src):
            out.append((e["src"], e["tar"], int(e["alpha"])))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/derived/flyvis_lappalainen2024_types.csv")
    ap.add_argument("--edges-out", default="data/derived/flyvis_lappalainen2024_edges.csv")
    a = ap.parse_args()
    s = spec()
    types = [n["name"] for n in s["nodes"]]
    et = edge_types(s)
    root = RAW / "results" / "flow" / "0000"
    models = sorted(p for p in root.iterdir() if (p / "best_chkpt").exists())
    tau, bias, strength, loss = [], [], [], []
    for m in models:
        d = load(m / "best_chkpt")["network"]
        assert len(d["nodes_time_const"]) == len(types), m
        assert len(d["edges_syn_strength"]) == len(et), (m, len(d["edges_syn_strength"]), len(et))
        sign = d["edges_sign"]
        assert np.array_equal(np.sign(sign), [x[2] for x in et]), f"{m}: edge order mismatch"
        tau.append(d["nodes_time_const"]); bias.append(d["nodes_bias"])
        strength.append(d["edges_syn_strength"])
        import h5py
        with h5py.File(m / "validation_loss.h5") as f:
            loss.append(float(np.min(f[list(f.keys())[0]][()])))
    tau, bias, strength, loss = map(np.asarray, (tau, bias, strength, loss))
    order = np.argsort(loss)
    eff = np.maximum(tau, TRAIN_DT_S)
    rows = []
    for i, t in enumerate(types):
        rows.append(dict(
            flyvis_type=t,
            tau_ms_median=1000 * np.median(tau[:, i]),
            tau_ms_q25=1000 * np.quantile(tau[:, i], 0.25), tau_ms_q75=1000 * np.quantile(tau[:, i], 0.75),
            tau_eff_ms_median=1000 * np.median(eff[:, i]),
            tau_ms_best10_median=1000 * np.median(tau[order[:10], i]),
            frac_models_tau_below_dt=float(np.mean(tau[:, i] < TRAIN_DT_S)),
            v_rest_au_median=np.median(bias[:, i]),
            v_rest_au_q25=np.quantile(bias[:, i], 0.25), v_rest_au_q75=np.quantile(bias[:, i], 0.75),
            v_rest_au_best10_median=np.median(bias[order[:10], i]),
            n_models=len(models),
        ))
    pd.DataFrame(rows).to_csv(a.out, index=False, float_format="%.5g")
    erows = [dict(source=s_, target=t_, sign=g, alpha_median=np.median(strength[:, k]),
                  alpha_q25=np.quantile(strength[:, k], 0.25), alpha_q75=np.quantile(strength[:, k], 0.75),
                  alpha_best10_median=np.median(strength[order[:10], k]))
             for k, (s_, t_, g) in enumerate(et)]
    pd.DataFrame(erows).to_csv(a.edges_out, index=False, float_format="%.5g")
    print(f"{len(models)} models, {len(types)} types, {len(et)} edge types; "
          f"validation loss {loss.min():.4f}-{loss.max():.4f}")


if __name__ == "__main__":
    main()
