"""Feasibility probes for failing checks whose inputs include gaps (wtriage, 8 Nov 2026). Never adopted.

Pre-registered here before any of these ran (8 Nov 14:00 CST). Each probe: the ids the check reads (traced in the
code), the box (bio = the params API's bounds; hard = hard_min/hard_max where wider), the sample count, the bar
(the check's own, unchanged), and the companion checks re-run at the best point.

  glia   row 11, scripts/worm/organs/check_glia.py; bar = its score.pass (peak 0.2-12 mM, recovery tau 0.7-6.3 s,
         Kir null >= 1.2x slower, right side < 10% of left). ids: glia_k_volume_um3, glia_k_leak_frac, glia_kir_tau_s,
         glia_k_diff_tau_s, glia_gap_nS_per_contact, glia_g_leak_nS. 64 bio points.
  canal  row 16, scripts/worm/organs/check_other.py; bar = score.pass (ablation t90 12-24 h, wild type holds within
         1%, tracer). ids: osmo_lp_per_kPa_s, osmo_e_vol_kPa, osmo_dosm_mOsm, osmo_canal_gain. 128 bio points.
  gaba   row 24, the GABA part of scripts/worm/stp_unit_check.py; bar: plateaus > 0.8 at 1 and 5 Hz and 20 Hz
         second/first > 1 (Liu et al. 2009 'no or only slight depression at 1 and 5 Hz', facilitation at 20 Hz).
         ids: the 8 stp_gaba_* gaps. 256 bio points.
  opto   row 23, the opto sanity of scripts/worm/observation_checks.py (AVAL dv at the end of a 0.5 s pulse > 1 mV,
         whole 302-neuron brain at the ledger values, 2 s, dt 4 ms). ids: obs_opto_g_nS, obs_opto_e_mV,
         obs_opto_tau_on_ms. 32 bio points (each point is two whole-brain runs).

Usage (backhouse): python probes.py NAME [--n=N] [--workers=W] [--box=bio]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

from probe_lib import Box, joint_bad, save
from probe_run import run_points

PROBES = {
    "glia": dict(script="scripts/worm/organs/check_glia.py", n=64,
                 ids=["glia_k_volume_um3", "glia_k_leak_frac", "glia_kir_tau_s", "glia_k_diff_tau_s",
                      "glia_gap_nS_per_contact", "glia_g_leak_nS"],
                 ok=lambda r: bool(r.get("score", {}).get("pass")),
                 keep=lambda r: dict(score=r.get("score"), tau=r.get("wt", {}).get("tau_recovery_s"),
                                     peak=r.get("wt", {}).get("peak_dk_left_mM"),
                                     right=r.get("wt", {}).get("peak_dk_right_mM"),
                                     null_tau=r.get("null", {}).get("tau_recovery_s"))),
    "canal": dict(script="scripts/worm/organs/check_other.py", n=128,
                  ids=["osmo_lp_per_kPa_s", "osmo_e_vol_kPa", "osmo_dosm_mOsm", "osmo_canal_gain"],
                  ok=lambda r: bool(r.get("score", {}).get("pass")),
                  keep=lambda r: dict(score=r.get("score"), t90=r.get("t90_null_h"), dev=r.get("wt_P_max_rel_dev"),
                                      P_inf=r.get("null_P_inf_kPa"))),
}

GABA_IDS = ["stp_gaba_beta_per_ms", "stp_gaba_k0_per_s", "stp_gaba_kmax_per_s", "stp_gaba_tauD_ms", "stp_gaba_KD_ms",
            "stp_gaba_F1", "stp_gaba_tauF_ms", "stp_gaba_KF_ms"]
OPTO_IDS = ["obs_opto_g_nS", "obs_opto_e_mV", "obs_opto_tau_on_ms"]


def gaba_point(x):
    """GABA trains at one point (in a pool worker: patch, import, run)."""
    import at_ledger
    at_ledger.patch()
    sys.argv = ["stp"]
    import stp_unit_check as S
    S.T.update(dict(zip(GABA_IDS, map(float, x))))
    g = {}
    for hz in (1.0, 5.0, 20.0):
        v, per = S.F.train(hz)
        a = S.per_pulse(S.run(v, "gabacl"), per)
        g[hz] = a / a[0]
    r = dict(p1=float(g[1.0][-5:].mean()), p5=float(g[5.0][-5:].mean()), r20=float(g[20.0][1]))
    r["pass"] = bool(r["p1"] > 0.8 and r["p5"] > 0.8 and r["r20"] > 1)
    # companion: the ACh grain's held-out and the numpy reference are not GABA's, so unaffected by these ids
    return r


def opto_point(x):
    import at_ledger
    at_ledger.patch()
    from probe_run import override
    override(dict(zip(OPTO_IDS, map(float, x))))
    import observation_checks as O
    from wormemu.mech import observation as ob  # noqa: F401
    res = {}
    for key, cfg in (("base", dict(registry=O.WBODY, toggles={}, schedule=[], seconds=1.0)),
                     ("pulse", dict(registry=O.WBODY + ["observation"], toggles={},
                                    schedule=[["AVAL", 500.0, 500.0, 1.0]], seconds=1.0))):
        import io
        import pickle
        buf = io.BytesIO()

        class W:
            buffer = buf
        so = sys.stdout
        sys.stdout = W()
        try:
            O._child(cfg)
        finally:
            sys.stdout = so
        res[key] = pickle.loads(buf.getvalue())
    i = res["base"]["names"].index("AVAL")
    k_end = int(1000 / 4.0) - 1
    dv = float(res["pulse"]["V"][k_end, i] - res["base"]["V"][k_end, i])
    return dict(dv=dv, g_peak=float(res["pulse"]["opto"].max()), pass_=bool(dv > 1.0))


def _pool(fn, X, workers):
    import multiprocessing as mp
    with mp.get_context("fork").Pool(workers, maxtasksperchild=1) as pool:
        return pool.map(fn, list(X), chunksize=1)


def main():
    name = sys.argv[1]
    n = next((int(a[4:]) for a in sys.argv if a.startswith("--n=")), None)
    workers = next((int(a[10:]) for a in sys.argv if a.startswith("--workers=")), 8)
    which = next((a[6:] for a in sys.argv if a.startswith("--box=")), "bio")
    t0 = time.time()
    if name in PROBES:
        p = PROBES[name]
        box = Box(p["ids"])
        X = box.design(n or p["n"], which=which, seed=0)
        rows = run_points(p["script"], p["ids"], X, workers=workers)
        ok = np.array([p["ok"](r) for r in rows])
        kept = [dict(p["keep"](r), error=r.get("error")) for r in rows]
        ids = p["ids"]
    elif name == "gaba":
        ids = GABA_IDS
        box = Box(ids)
        X = box.design(n or 256, which=which, seed=0)
        kept = _pool(gaba_point, X, workers)
        ok = np.array([r["pass"] for r in kept])
    elif name == "opto":
        ids = OPTO_IDS
        box = Box(ids)
        X = box.design(n or 32, which=which, seed=0)
        kept = _pool(opto_point, X, workers)
        ok = np.array([r["pass_"] for r in kept])
    else:
        raise SystemExit(f"unknown probe {name}")
    jb = np.array([len(joint_bad(dict(zip(ids, x)))) for x in X])
    ok = ok & (jb == 0)
    res = dict(probe=name, box=which, n=len(X), n_pass=int(ok.sum()), pass_fraction=float(ok.mean()),
               n_joint_bad=int((jb > 0).sum()), wall_s=time.time() - t0, bounds=box.describe(),
               points=[dict(x=dict(zip(ids, map(float, x))), passed=bool(o), edges=box.at_edge(x, which=which),
                            **k) for x, o, k in zip(X, ok, kept)])
    print(save(f"probe_{name}_{which}", res))
    print(name, which, "pass", res["n_pass"], "of", res["n"], f"wall {res['wall_s']:.0f} s", flush=True)


if __name__ == "__main__":
    main()
