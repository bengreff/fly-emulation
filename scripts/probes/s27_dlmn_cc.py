"""s27 (fly2): DLM motoneuron coupling coefficients in the network, by Hurkey et al. 2023's protocol.

Hurkey 2023 (Nature 618:118, Fig 2f, 2h; Methods): CC = postsynaptic peak voltage / presynaptic peak voltage for
20 ms subthreshold current pulses into one MN (dual patch), and separately for the AHP of an evoked spike.
Here, in the full organism: a 20 ms depolarising pulse (negative kicks never land in lif.step) into each DLMn c-f (MN1-4) in turn, then one spike in
each, with every voltage taken relative to an identical unstimulated run (same seed, deterministic). CC is the
mean over same-side DLMn c-f pairs, both directions. Writes runs/s27/dlmn_cc_<tag>.json.

    .venv/bin/python scripts/probes/s27_dlmn_cc.py --tag c0p02 --coupling 0.02
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402

ROW = "electrical:DLMn c-f->DLMn c-f"
SETTLE, PULSE, GAP = 1000, 200, 800          # steps of 0.1 ms: 100 ms settle, 20 ms pulse, 80 ms recovery


def run(profile: str, seed: int, coupling: float | None, stim: bool, pulse_mv: float, extra: dict,
        reverse: bool = False) -> dict:
    ov = dict(extra)
    if coupling is not None:
        ov[f"{ROW}|gap_coupling"] = coupling
    org = Organism(policy="minimal", profile=profile, min_synapses=profiles.WORKING_MIN_SYNAPSES, seed=seed,
                   overrides=ov)
    net = org.net
    t = org.conn.neurons.type.fillna("").to_numpy().astype(str)
    side = org.conn.neurons.somaSide.fillna("?").to_numpy().astype(str)
    cf = np.flatnonzero(t == "DLMn c-f")
    if reverse:                     # stimulate in reverse order: each clean pair is then read in the other direction
        cf = cf[::-1]
    ab = np.flatnonzero(t == "DLMn a, b")
    watch = np.r_[cf, ab]
    n_cells = len(cf)
    total = SETTLE + 2 * n_cells * (PULSE + GAP)
    trace = np.zeros((total, len(watch)), np.float32)
    spikes = []
    for s in range(total):
        kick = None
        if stim and s >= SETTLE:
            j, r = divmod(s - SETTLE, PULSE + GAP)
            if j < n_cells and r < PULSE:                       # phase 1: pulses
                kick = (cf[j:j + 1], pulse_mv)
            elif j >= n_cells and r == 0:                       # phase 2: one spike each
                kick = (cf[j - n_cells:j - n_cells + 1], 100.0)
        sp = np.asarray(net.step(kick=kick))
        trace[s] = net.v[watch]
        for i in sp[np.isin(sp, watch)]:
            spikes.append((s, int(i)))
    out = {"cf": cf.tolist(), "ab": ab.tolist(), "side_cf": side[cf].tolist(),
           "v_rest": float(np.mean(net.v_rest[cf])), "v_th": float(np.mean(net.v_th[cf])),
           "v_reset": float(np.mean(net.v_reset[cf])), "tau_m": float(np.mean(net.tau_m[cf])),
           "gap_pairs": 0 if net.gap is None else int(len(net.gap["a"])), "spikes": spikes}
    del org, net
    gc.collect()
    return out, trace


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--coupling", type=float, default=None)
    ap.add_argument("--pulse-mv", type=float, default=0.035, help="per-step depolarising kick during the pulse")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--set", action="append", default=[], help="override key=value")
    ap.add_argument("--reverse", action="store_true", help="stimulate the DLMn c-f in reverse index order")
    a = ap.parse_args()
    extra = {k: float(v) for k, v in (s.rsplit("=", 1) for s in a.set)}
    meta, ctl = run(a.profile, a.seed, a.coupling, False, a.pulse_mv, extra, a.reverse)
    meta2, stm = run(a.profile, a.seed, a.coupling, True, a.pulse_mv, extra, a.reverse)
    dv = stm - ctl
    cf, side = meta["cf"], np.array(meta["side_cf"])
    n = len(cf)
    pulse_cc, ahp_cc, pre_pk, pre_ahp, ab_cc = [], [], [], [], []
    for j in range(n):
        s0 = SETTLE + j * (PULSE + GAP)
        w = dv[s0:s0 + PULSE + GAP, :n]
        pk = w.max(axis=0)                                   # depolarising pulse: largest excursion
        pre_pk.append(float(pk[j]))
        for i in range(n):
            if i != j and side[i] == side[j]:
                pulse_cc.append(float(pk[i] / pk[j]))
        wab = dv[s0:s0 + PULSE + GAP, n:]
        ab_cc += [float(wab[:, k].min() / pk[j]) for k in range(wab.shape[1])]
        s1 = SETTLE + (n + j) * (PULSE + GAP)
        w2 = dv[s1 + 1:s1 + PULSE + GAP, :n]                 # after the spike step
        # presynaptic AHP: the spiking cell's lowest potential after its spike, relative to its control trace
        ahp = w2.min(axis=0)
        pre_ahp.append(float(ahp[j]))
        for i in range(n):
            if i != j and side[i] == side[j] and ahp[j] < 0:
                ahp_cc.append(float(ahp[i] / ahp[j]))
    res = {"probe": "s27_dlmn_cc", "profile": a.profile, "tag": a.tag, "coupling": a.coupling, "seed": a.seed,
           "overrides": extra, "pulse_mv_per_step": a.pulse_mv, "meta": {k: v for k, v in meta2.items()
                                                                       if k != "spikes"},
           "stim_spikes": meta2["spikes"], "ctl_spikes": meta["spikes"],
           "pre_pulse_peak_mv": pre_pk, "pulse_cc_pairs": pulse_cc,
           "pulse_cc_mean": float(np.mean(pulse_cc)) if pulse_cc else None,
           "pulse_cc_ab_mean": float(np.mean(ab_cc)) if ab_cc else None,
           "pre_ahp_mv": pre_ahp, "ahp_cc_pairs": ahp_cc,
           "ahp_cc_mean": float(np.mean(ahp_cc)) if ahp_cc else None}
    d = REPO / "runs" / "s27"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"dlmn_cc_{a.tag}.json").write_text(json.dumps(res, indent=1))
    np.save(d / f"dlmn_cc_{a.tag}_dv.npy", dv)
    print(json.dumps({k: res[k] for k in ("tag", "coupling", "pulse_cc_mean", "pulse_cc_ab_mean", "ahp_cc_mean",
                                          "pre_pulse_peak_mv", "pre_ahp_mv")}))
    print(json.dumps(res["meta"]), "stim spikes", len(res["stim_spikes"]), "ctl spikes", len(res["ctl_spikes"]))


if __name__ == "__main__":
    main()
