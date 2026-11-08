"""Probe, line vi (row 15's second cause): can HSN's 5-HT reach SER-7's EC50 at the vulva inside the bio box?

Pre-registered (8 Nov 2026, written before the probe ran; the Mac smoke at the ledger, below, ran first and only
chose the injection):
  question  with HSN at full drive, does the vulval 5-HT the egg module reads reach the vulval receptor's measured
            EC50? Even full drive at the ledger gives 15.4 nM at steady state (derived: 2 x 1e5 molecules/s x 5 s over
            the 1.08e5 um3 compartment), and less in practice because the store drains.
  bar       max over the 60 s drive window of the vulval 5-HT >= 30 nM, SER-7's EC50 (Hobson et al. 2006 Genetics
            172:159, PMC1456143: 30 +- 3 nM, cAMP in COS-7; the ledger's measured fill). Reported, not scored: seconds
            above 30 nM, peak SER-1/SER-7 occupancy (the module's mean of the two), HSN's store at the end.
  protocol  hsn_5ht_point.py: the row 15 brain (check_egglaying.CELLS), ledger values, default toggles, both HSNs
            given +40 pA from 2 s to 62 s, dt 5 ms. 40 pA is the smallest of {20, 40, 80} pA giving HSN's mean amine
            drive q >= 0.9 at the ledger (Mac smoke 14:43: 20 pA q 0.62, 40 pA q 0.98 at -8.4 mV, 80 pA q 1.00).
            So HSN's own silence (line 5) is outside this question.
  ids       the gaps on the HSN -> vulva amine path (mech/neuromod.py:470-495): ma_release_per_s, ma_degrade_tau_s,
            ma_store_molecules, ma_synth_tau_s, ma_tau_ms. Fixed: ma_diffusion_um2_per_s (scan), the receptor EC50s
            (measured / guessed fills), the compartment volume (geometry). This brain has no MOD-5 cells, so no
            reuptake: a pass here is an upper bound for the whole worm (reported as a caveat).
  design    64 scrambled Sobol points in the bio box, seed 0; joint constraints checked.
  also      at the best point, neuromod_unit_check.py (the module's own checks) re-run.

Usage (backhouse): python probe_5ht.py [WORKERS]
Output: runs/worm/triage/probe_5ht.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from probe_lib import Box, joint_bad, save
from probe_run import run_points

IDS = ["ma_release_per_s", "ma_degrade_tau_s", "ma_store_molecules", "ma_synth_tau_s", "ma_tau_ms"]
BAR_NM = 30.0
SCRIPT = "scripts/worm/triage/hsn_5ht_point.py"


def score(r):
    if "error" in r:
        return dict(error=r["error"]), False
    want = r.get("_point", {})
    bad = [i for i, x in want.items() if abs(r["p_used"].get(i, float("nan")) - x) > 1e-9 * abs(x)]
    assert not bad, f"override did not reach neuromod: {bad}"
    t, c = np.array(r["t"]), np.array(r["c5_nM"])
    on = t >= 2.0
    dt = float(np.median(np.diff(t)))
    d = dict(c5_max=float(c[on].max()), s_above=float((c[on] >= BAR_NM).sum() * dt), occ_max=float(max(r["occ"])),
             store_end=float(r["store"][-1]), q_on=float(np.mean(np.array(r["q"])[t >= 3.0])))
    return d, d["c5_max"] >= BAR_NM


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    box = Box(IDS)
    X = box.design(64, which="bio", seed=0)
    rows = run_points(SCRIPT, IDS, [[r["template"] for r in box.rows]] + list(X), workers=workers, args=["40", "62"])
    save("probe_5ht_raw", dict(ids=IDS, X=X.tolist(), rows=rows))       # kept before scoring
    base, rows = rows[0], rows[1:]
    sc = [score(r) for r in rows]
    jb = np.array([len(joint_bad(dict(zip(IDS, x)))) for x in X])
    ok = np.array([p for _, p in sc]) & (jb == 0)
    m = np.array([d.get("c5_max", -1.0) for d, _ in sc])
    k = int(np.argmax(m))
    kp = [i for i in np.flatnonzero(ok)]
    away = [int(i) for i in kp if not box.at_edge(X[i])]
    res = dict(check="line vi: vulval 5-HT vs SER-7 EC50 at full HSN drive", bar_nM=BAR_NM, at_template=score(base)[0],
               n=len(X), n_pass=int(ok.sum()), pass_fraction=float(ok.mean()), n_pass_off_edges=len(away),
               joint_bad=int((jb > 0).sum()), errors=int(sum("error" in d for d, _ in sc)),
               best=dict(zip(IDS, X[k].tolist())), best_detail=sc[k][0], best_edges=box.at_edge(X[k]),
               points=[dict(zip(IDS, x.tolist()), **d) for x, (d, _) in zip(X, sc)], bounds=box.describe())
    if ok.any():
        from probe_run import run_one
        kb = max(kp, key=lambda i: m[i])
        chk = run_one(str(Path(__file__).resolve().parents[3] / "scripts/worm/neuromod_unit_check.py"),
                      dict(zip(IDS, X[kb].tolist())))
        res["best_pass"] = dict(zip(IDS, X[kb].tolist()))
        res["best_pass_neuromod_unit_check"] = chk
    print(save("probe_5ht", res))
    print({k_: v for k_, v in res.items() if k_ not in ("bounds", "points")})


if __name__ == "__main__":
    main()
