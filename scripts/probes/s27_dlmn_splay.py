"""s27 (fly2): do the fitted DLMn c-f junctions desynchronise tonic MN1-4 firing (Hurkey 2023 splay), without refitting?

Hurkey et al. 2023 (Nature 618:118; PMC10232364): in tethered flight MN1-5 fire tonically (3-12 Hz) with a gap
around phase 0 in pairwise phase histograms (Fig. 2b control); after shakB RNAi the gap is absent, with a slight
in-phase preference (Fig. 2b middle). Measure (Extended Data Fig. 6): the fraction of partner spikes whose phase in
the reference cell's ISI falls within (-0.1, 0.1); a uniform phase distribution gives 0.2.

Here, in the full m10f network (`Organism`, policy minimal, as s27_dlmn_cc.py): every DLMn c-f gets the same DC
drive plus excitatory Poisson kicks, one train shared by all eight (Hurkey Extended Data Fig. 4c: shared synaptic
input) and one independent train per cell. Arms: the profile's fitted coupling and `--coupling 0` (shakB KD
analogue). Same-side pairs are coupled; cross-side pairs are not, and serve as the in-run common-input control.
Writes runs/s27/dlmn_splay_<tag>.json.

    .venv/bin/python scripts/probes/s27_dlmn_splay.py --tag fit --ms 30000
    .venv/bin/python scripts/probes/s27_dlmn_splay.py --tag c0 --coupling 0 --ms 30000
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from flyemu import profiles  # noqa: E402
from flyemu.organism import Organism  # noqa: E402

ROW = "electrical:DLMn c-f->DLMn c-f"
DT_MS = 0.1


def phase_fraction(ref: np.ndarray, par: np.ndarray, win: float = 0.1) -> tuple[float, int]:
    """Fraction of partner spikes inside the reference cell's ISIs whose phase is < win or > 1 - win."""
    if len(ref) < 2 or len(par) == 0:
        return float("nan"), 0
    k = np.searchsorted(ref, par, side="right") - 1
    ok = (k >= 0) & (k < len(ref) - 1)
    ph = (par[ok] - ref[k[ok]]) / (ref[k[ok] + 1] - ref[k[ok]])
    return (float(np.mean((ph < win) | (ph > 1 - win))) if len(ph) else float("nan")), int(len(ph))


def score(spk: dict, side: list[str], skip_ms: float) -> dict:
    ids = sorted(spk)
    t = {i: np.asarray([s for s in spk[i] if s >= skip_ms], float) for i in ids}
    same, cross = [], []
    for a in range(len(ids)):
        for b in range(len(ids)):
            if a == b:
                continue
            f, n = phase_fraction(t[ids[a]], t[ids[b]])
            (same if side[a] == side[b] else cross).append((ids[a], ids[b], f, n))
    fs = [x[2] for x in same if np.isfinite(x[2])]
    fc = [x[2] for x in cross if np.isfinite(x[2])]
    hist = np.zeros(20)
    for a in range(len(ids)):
        for b in range(len(ids)):
            if a != b and side[a] == side[b]:
                r, p = t[ids[a]], t[ids[b]]
                k = np.searchsorted(r, p, side="right") - 1
                ok = (k >= 0) & (k < len(r) - 1)
                ph = (p[ok] - r[k[ok]]) / (r[k[ok] + 1] - r[k[ok]])
                hist += np.histogram(ph, bins=20, range=(0, 1))[0]
    dur_s = None
    rates = {str(i): len(t[i]) for i in ids}
    isi_cv = [float(np.std(np.diff(t[i])) / np.mean(np.diff(t[i]))) for i in ids if len(t[i]) > 2]
    return {"same_side_frac_mean": float(np.mean(fs)) if fs else None,
            "same_side_frac_sem": float(np.std(fs) / np.sqrt(len(fs))) if fs else None,
            "cross_side_frac_mean": float(np.mean(fc)) if fc else None,
            "cross_side_frac_sem": float(np.std(fc) / np.sqrt(len(fc))) if fc else None,
            "same_pairs": same, "cross_pairs": cross, "same_side_phase_hist20": hist.tolist(),
            "spike_counts_after_skip": rates, "isi_cv": isi_cv, "dur_s": dur_s}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--profile", default="m10f")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--coupling", type=float, default=None, help="override the DLMn c-f coupling (0 = shakB KD)")
    ap.add_argument("--ms", type=float, default=30000.0)
    ap.add_argument("--skip-ms", type=float, default=2000.0)
    ap.add_argument("--dc", type=float, default=0.036, help="DC drive, mV per 0.1 ms step, every DLMn c-f")
    ap.add_argument("--epsp", type=float, default=0.5, help="Poisson kick size, mV")
    ap.add_argument("--rate-common", type=float, default=100.0, help="shared Poisson train, Hz")
    ap.add_argument("--rate-indep", type=float, default=100.0, help="independent Poisson train per cell, Hz")
    a = ap.parse_args()
    ov = {}
    if a.coupling is not None:
        ov[f"{ROW}|gap_coupling"] = a.coupling
    t0 = time.time()
    org = Organism(policy="minimal", profile=a.profile, min_synapses=profiles.WORKING_MIN_SYNAPSES, seed=a.seed,
                   overrides=ov)
    net = org.net
    typ = org.conn.neurons.type.fillna("").to_numpy().astype(str)
    sd = org.conn.neurons.somaSide.fillna("?").to_numpy().astype(str)
    bid = org.conn.neurons.bodyId.to_numpy()
    cf = np.flatnonzero(typ == "DLMn c-f")
    rng = np.random.default_rng(1000 + a.seed)
    steps = int(a.ms / DT_MS)
    pc, pi = a.rate_common * DT_MS / 1000.0, a.rate_indep * DT_MS / 1000.0
    spk = {int(i): [] for i in cf}
    build_s = time.time() - t0
    for s in range(steps):
        mv = np.full(len(cf), a.dc, np.float32)
        if rng.random() < pc:
            mv += a.epsp
        mv += a.epsp * (rng.random(len(cf)) < pi)
        sp = np.asarray(net.step(kick=(cf, mv)))
        for i in sp[np.isin(sp, cf)]:
            spk[int(i)].append(s * DT_MS)
    res = score(spk, sd[cf].tolist(), a.skip_ms)
    res["dur_s"] = (a.ms - a.skip_ms) / 1000.0
    res["rate_hz"] = {str(bid[i]): len([x for x in spk[int(i)] if x >= a.skip_ms]) / res["dur_s"] for i in cf}
    out = {"probe": "s27_dlmn_splay", "tag": a.tag, "profile": a.profile, "seed": a.seed, "overrides": ov,
           "args": vars(a), "cf_body_ids": bid[cf].tolist(), "side": sd[cf].tolist(),
           "gap_pairs": 0 if net.gap is None else int(len(net.gap["a"])), "build_s": round(build_s, 1),
           "wall_s": round(time.time() - t0, 1), "spikes_ms": {str(bid[i]): spk[int(i)] for i in cf}, **res}
    d = REPO / "runs" / "s27"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"dlmn_splay_{a.tag}.json").write_text(json.dumps(out))
    print(a.tag, "rates", {k: round(v, 2) for k, v in out["rate_hz"].items()}, "same", out["same_side_frac_mean"],
          "cross", out["cross_side_frac_mean"], "cv", np.round(out["isi_cv"], 2).tolist(), "wall", out["wall_s"])


if __name__ == "__main__":
    main()
