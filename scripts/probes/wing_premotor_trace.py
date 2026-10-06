"""Session 12 B: trace the tonic drive of the resting wing motor neurons upstream.

Reads the per-neuron rates saved by wing_drive.py (npz `all_rate_hz`), rebuilds
the same organism's connectome, and walks back from the active wing motor
neurons: at each level, the presynaptic cells carrying the most chemical drive
(signed synapse count x rate, synapse*Hz). Reports each traced cell's own
external (sensory) drive flag, so a tonic source can be told from a loop.

    uv run python scripts/probes/wing_premotor_trace.py runs/s12/wings/wing_drive_roles_seed12.npz
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402


def main() -> None:
    npz = Path(sys.argv[1])
    rate = np.load(npz)["all_rate_hz"]
    org = Organism(policy="minimal", seed=12, overrides={"motor_unit:all|force_per_spike": 10.0},
                   profile=profiles.WORKING_PROFILE, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    conn = org.conn
    nrn = conn.neurons.reset_index(drop=True)
    pre_of = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    lab = lambda i: f"{nrn.type.iloc[i]} {nrn.instance.iloc[i]}"  # noqa: E731
    wing = np.flatnonzero(nrn.type.fillna("").str.match(r"^(b[123]|i[12]|iii[13]|hg[1-4]) MN$|^MNwm35$").to_numpy()
                          & (rate > 5.0))
    seen, frontier, levels = set(wing.tolist()), list(wing), []
    for depth in range(3):
        nxt, level = [], {}
        for tgt in frontier:
            e = np.flatnonzero(conn.indices == tgt)
            pre = pre_of[e]
            drive = conn.sign[pre] * conn.weight_syn[e] * rate[pre]
            order = np.argsort(-np.abs(drive))[:6]
            level[f"{lab(tgt)} ({rate[tgt]:.1f} Hz)"] = [
                f"{lab(pre[k])} ({rate[pre[k]]:.1f} Hz, {int(conn.weight_syn[e][k])} syn, {drive[k]:+.0f})"
                for k in order if drive[k]]
            for k in order[:3]:
                if drive[k] > 0 and pre[k] not in seen:
                    seen.add(int(pre[k])); nxt.append(int(pre[k]))
        levels.append(level)
        frontier = nxt
    # left/right symmetry of the traced cells' types
    traced = sorted(seen)
    sym = {}
    for i in traced:
        t = nrn.type.iloc[i]
        same = np.flatnonzero(nrn.type.to_numpy() == t)
        sym[t] = {str(nrn.instance.iloc[j]): round(float(rate[j]), 1) for j in same}
    sc = nrn.superclass.fillna("?").to_numpy()
    side_rate = {s: {sup: round(float(rate[(nrn.instance.fillna("").str.endswith("_" + s).to_numpy()) & (sc == sup)].mean()), 2)
                     for sup in ("vnc_intrinsic", "vnc_sensory", "ascending_neuron", "descending_neuron", "vnc_motor")}
                 for s in ("L", "R")}
    out = dict(source=str(npz), levels=levels, type_rates_by_instance=sym, mean_rate_by_side=side_rate)
    p = npz.with_name(npz.stem + "_trace.json")
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
