"""Closed-loop regression check (DECISIONS session 6, criterion 2).

Runs the organism for --ms with all senses, then --silent-ms with all
afferent drive removed, and reports rates by group and the return to rest.

    uv run python scripts/probes/closed_loop_check.py [--set K=V ...] [--ms 1000]
"""
import argparse
import json
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

EYE_CLASSES = ("photoreceptor", "ocellar_photoreceptor", "LMC", "T4T5", "optic_columnar", "optic_other",
               "optic_projection")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--silent-ms", type=float, default=300.0)
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--template", action="store_true",
                    help="all construction-template body switches on (model_data.TEMPLATE_SWITCHES)")
    ap.add_argument("--sample-fly", type=int, default=None, metavar="SEED",
                    help="task 13: a complete template fly drawn by model_data.sample_fly(SEED, --stage)")
    ap.add_argument("--stage", type=int, default=1)
    ap.add_argument("--hold-k", type=int, default=1,
                    help="sense every k steps and hold the drive in between (GPU closed-loop scheme, docs/GPU.md)")
    ap.add_argument("--out", default="", help="also write the result (with per-class silent spikes) to this JSON")
    ap.add_argument("--profile", default=WORKING_PROFILE)
    ap.add_argument("--silent-noise-on", action="store_true",
                    help="keep membrane noise in the silent window (default: noise, which stands for unmodelled "
                         "input to the CNS, is removed with the afferent drive; s13)")
    ap.add_argument("--graded-k-scale", default="", metavar="GROUP=F",
                    help="diagnostic (DECISIONS 24 Oct 01:40): scale the graded release multiplier of the graded "
                         "cells in GROUP (photo: the photoreceptor classes; nonphoto: the rest) by F after the build")
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    if a.template:
        from flyemu.model_data import TEMPLATE_SWITCHES
        ov = {**TEMPLATE_SWITCHES, **ov}
    if a.sample_fly is not None:
        from flyemu import model_data as M
        ov = {**M.sample_fly(M.load(), a.sample_fly, a.stage), **ov}
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, overrides=ov, seed=a.seed)
    n = org.conn.neurons
    from flyemu.lif import circuit_classes
    cls = circuit_classes(org.conn)
    if a.graded_k_scale:
        grp, f = a.graded_k_scale.split("=")
        assert org.net.params.fv_edge is None, "flyvis pair weights are normalised by g_k at build"
        photo = np.isin(cls[org.net.g_idx], ["photoreceptor", "ocellar_photoreceptor"])
        sel = {"photo": photo, "nonphoto": ~photo}[grp]
        gk = np.ones(org.net.g_idx.size, np.float32) if org.net.g_k is None else org.net.g_k.copy()
        gk[sel] *= np.float32(f)
        org.net.g_k = gk
    t = n.type.fillna("").to_numpy()
    orn = np.char.startswith(t.astype(str), "ORN_")
    upn = (n["class"].fillna("") == "ALPN").to_numpy() & np.char.endswith(t.astype(str), "PN")
    mn = (n.superclass.fillna("") == "vnc_motor").to_numpy()
    steps = int(a.ms / org.timestep_ms)
    cnt = np.zeros(org.conn.n)
    z, t0 = [], time.time()
    ext = None
    for s in range(steps):
        obs = org.body.observe()
        if s % a.hold_k == 0 or ext is None:
            ext = org.sense(s, obs)
        sp = org.net.step(external_mv=ext)
        if s * org.timestep_ms >= 200:          # skip the opening transient
            cnt[sp] += 1
        org.motor_step(sp)
        if s % 100 == 0:
            z.append(float(obs["body_positions"][0, 2]))
        if sp.size > 20000:
            r = {"runaway_at_ms": s * org.timestep_ms, "overrides": ov}
            print(json.dumps(r))
            if a.out:
                with open(a.out, "w") as f:
                    json.dump(r, f)
            return
    dur = (a.ms - 200) / 1000
    hz = cnt / dur
    silent = []
    # cells with intrinsic tonic drive (e.g. slow MNs at their measured rest rate)
    # fire without input by design; the criterion concerns the network
    # (per-type rows only: a class tonic drive (N3, s10) is part of the network under test)
    spont = np.broadcast_to(np.asarray(org.net.params.spont_mv, np.float32), (org.conn.n,))
    if org.net.params.tonic_class_mv is not None:
        spont = spont - org.net.params.tonic_class_mv
    tonic = spont > 0
    scnt = np.zeros(org.conn.n)
    # F-VISION-5 option (a) (Director, s13): eye cells are reported apart from the silent-window count
    eye = np.isin(cls, list(EYE_CLASSES))
    silent_eye = []
    if not a.silent_noise_on:
        org.net.params.noise_mv = 0.0
        org.net.params.noise_class_mv = None
    nsil = int(a.silent_ms / org.timestep_ms)
    lcnt = np.zeros(org.conn.n)   # the window's last 100 ms
    for s in range(nsil):
        obs = org.body.observe()
        sp = org.net.step(external_mv=np.zeros(org.conn.n, np.float32))
        org.motor_step(sp)
        silent.append(int((~tonic[sp]).sum()))
        silent_eye.append(int((~tonic[sp] & eye[sp]).sum()))
        scnt[sp] += 1
        if s >= nsil - int(100 / org.timestep_ms):
            lcnt[sp] += 1
    k100 = int(100 / org.timestep_ms)
    # G is defined on the first 300 ms of the silent window; a longer window (G2, DECISIONS 24 Oct 01:31)
    # leaves G's verdict unchanged and adds per-100-ms bins
    k300 = min(len(silent), 3 * k100)
    last = np.array(silent[k300 - k100:k300])
    last_eye = np.array(silent_eye[k300 - k100:k300])
    prev_eye = np.array(silent_eye[k300 - 2 * k100:k300 - k100])
    # F-VISION-5 option (a), second half (Ben, 13 Oct): eye activity in darkness may persist (tonic lamina
    # release) but must not grow; growth from the previous 100 ms to the last 100 ms beyond 3 Poisson SDs fails
    pe, le = float(prev_eye.sum()), float(last_eye.sum())
    eye_stationary = bool(le - pe <= 3.0 * np.sqrt(pe + le))
    nb = len(silent) // k100
    bin_eye = [int(sum(silent_eye[b * k100:(b + 1) * k100])) for b in range(nb)]
    bin_non = [int(sum(silent[b * k100:(b + 1) * k100])) - e for b, e in enumerate(bin_eye)]

    def no_growth(c):   # every consecutive 100 ms pair: rise <= 3 Poisson SDs (Ben's 13 Oct eye rule, extended)
        return all(b - a <= 3.0 * np.sqrt(a + b) for a, b in zip(c[:-1], c[1:]))
    gv = org.net.g_idx
    g_dv = (org.net.v[gv] - org.net.v_rest[gv]) if gv.size else np.zeros(0)
    out = {
        "whole_brain_hz": round(float(hz.mean()), 3),
        "whole_brain_excl_orn_hz": round(float(hz[~orn].mean()), 3),
        "orn_hz": round(float(hz[orn].mean()), 2),
        "upn_hz_mean": round(float(hz[upn].mean()), 2),
        "upn_hz_median": round(float(np.median(hz[upn])), 2),
        "upn_frac_active": round(float((hz[upn] > 0).mean()), 2),
        "motor_hz": round(float(hz[mn].mean()), 2),
        "cx_hz": {g: round(float(hz[np.char.startswith(t.astype(str), g)].mean()), 2)
                  for g in ("EPG", "PEN_", "PEG", "Delta7", "ER")},
        "silent_last100ms_spikes_per_ms": round(float(last.sum() / 100), 2),
        "silent_last100ms_noneye_spikes_per_ms": round(float((last.sum() - last_eye.sum()) / 100), 2),
        "silent_eye_spikes_per_ms_prev_last": [round(float(prev_eye.sum() / 100), 2), round(float(last_eye.sum() / 100), 2)],
        "silent_eye_stationary": eye_stationary,
        "silent_pass": bool(last.sum() - last_eye.sum() == 0 and eye_stationary),
        "silent_noise_removed": not a.silent_noise_on,
        "silent_ms": a.silent_ms,
        "silent_bins_100ms_eye": bin_eye,
        "silent_bins_100ms_noneye": bin_non,
        "g2_no_growth_eye": no_growth(bin_eye),
        "g2_no_growth_noneye": no_growth(bin_non),
        "g2_noneye_last100ms": bin_non[-1] if bin_non else None,
        "g2_pass": bool(a.silent_ms >= 1000 and no_growth(bin_eye) and no_growth(bin_non) and bin_non[-1] == 0),
        "silent_end_graded_frac_above_rest": round(float((g_dv > 0.01).mean()), 4) if g_dv.size else None,
        "silent_end_graded_mean_dv_mv": round(float(g_dv.mean()), 4) if g_dv.size else None,
        "thorax_z_mm_final": round(z[-1], 3), "thorax_z_mm_min": round(min(z), 3),
        "wall_s": round(time.time() - t0), "overrides": ov,
        "mujoco_warnings": int(sum(w.number for w in org.body.sim.mj_data.warning)),
        "nan_state": bool(not np.isfinite(org.body.sim.mj_data.qpos).all()
                          or not np.isfinite(org.net.v).all()),
    }
    ns = (scnt * ~tonic)
    out["silent_spikes_by_class"] = {c: int(ns[cls == c].sum()) for c in np.unique(cls[ns > 0])}
    nl = lcnt * ~tonic
    out["silent_last100ms_by_class"] = {c: int(nl[cls == c].sum()) for c in np.unique(cls[nl > 0])}
    if gv.size:
        gt = pd.DataFrame({"type": n.type.fillna("untyped").to_numpy()[gv], "dv": g_dv})
        up = gt[gt.dv > 0.01].groupby("type").dv.agg(["size", "mean"]).sort_values("size", ascending=False)
        out["silent_end_graded_above_rest_by_type"] = {k: [int(r["size"]), round(float(r["mean"]), 3)]
                                                        for k, r in up.head(20).iterrows()}
    out["graded_k_scale"] = a.graded_k_scale
    out["hz_by_class"] = {c: round(float(hz[cls == c].mean()), 4) for c in np.unique(cls)}
    ty = n.type.fillna("untyped").to_numpy().astype(str)
    tot = {}
    for t_, h_ in zip(ty, hz):
        if h_ > 0:
            tot[t_] = tot.get(t_, 0.0) + float(h_)
    out["top_types_summed_hz"] = {k: round(v, 1) for k, v in sorted(tot.items(), key=lambda kv: -kv[1])[:15]}
    print(json.dumps(out))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f)
    if last.sum() > 0:
        df = pd.DataFrame({"type": n.type.fillna("untyped"), "sc": n.superclass.fillna(""),
                           "nt": n.predictedNt.fillna(""), "spk": scnt})
        g = df[df.spk > 0].groupby(["type", "sc", "nt"]).agg(cells=("spk", "size"), spikes=("spk", "sum"))
        print("SUSTAINED", int((scnt > 0).sum()), "cells")
        print(g.sort_values("spikes", ascending=False).head(25).to_string())


if __name__ == "__main__":
    main()
