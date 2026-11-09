"""Naudin's E_L below E_K (docs/worm/night/2026-11-08_wbrain2.md, "Naudin's E_L below E_K", written before this ran;
wbrain2, 9 Nov 2026). Embedded AFDL alone under afd_membrane naudin22 and sens_thermo off, n22_e_L at the published
-89.43 mV and at its range top -79.43: rest after 3 s at 0 pA and FIT2's six training sweeps. Each value runs in its
own process.

  python scripts/worm/debug2/naudin22_el.py FEATURES.npz OUT.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

EL = (-89.43, -79.43)
EX = {"afd_membrane": "naudin22", "sens_thermo": "off"}


def one(feats, el):
    sys.argv = [sys.argv[0], feats]                      # ephys_score reads its features path from argv[1]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))
    import ephys_score as E
    orig = E.S.B.sample_worm

    def worm(seed):
        w = orig(seed)
        w.values["n22_e_L"] = el
        return w

    E.S.B.sample_worm = worm
    br = E.S.build(cells=["AFDL"], extra=EX)
    br.reset()
    br.extra_pA[:] = 0.0
    for _ in range(3000):
        v = float(br.step(None, 1.0).v_mV[0])
    r = E.score(EX, ["AFD"])["AFD"]
    print(json.dumps(dict(e_L=el, v_rest_mV=v, rmse_mV=r["rmse_mV"], steady=r["model"]["steady"],
                          baseline=r["model"]["baseline"])))


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2], float(sys.argv[3]))
        sys.exit()
    feats, out = sys.argv[1], sys.argv[2]
    root = Path(__file__).resolve().parents[3]
    res = {}
    for el in EL:
        p = subprocess.run([sys.executable, __file__, "one", feats, str(el)], capture_output=True, text=True,
                           cwd=root, env=dict(os.environ, PYTHONPATH=str(root / "src")), timeout=1800)
        assert p.returncode == 0, p.stderr[-3000:]
        res[str(el)] = json.loads(p.stdout.strip().splitlines()[-1])
        print(res[str(el)], flush=True)
    a, b = res[str(EL[0])], res[str(EL[1])]
    res["d_rest_mV"] = b["v_rest_mV"] - a["v_rest_mV"]
    res["d_rmse_mV"] = b["rmse_mV"] - a["rmse_mV"]
    res["d_steady_mV"] = [round(y - x, 3) for x, y in zip(a["steady"], b["steady"])]
    res["D"] = abs(res["d_rest_mV"]) <= 1.0 and abs(res["d_rmse_mV"]) <= 0.5
    print({k: res[k] for k in ("d_rest_mV", "d_rmse_mV", "d_steady_mV", "D")})
    Path(out).write_text(json.dumps(res, indent=1))
