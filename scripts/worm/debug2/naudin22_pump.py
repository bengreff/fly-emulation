"""AFDL's untraced 1.9 mV: the pump? (docs/worm/night/2026-11-08_wbrain2.md, written before this ran; wbrain2, 9 Nov
2026). Embedded AFDL alone, afd_membrane naudin22, sens_thermo off, n22_C_pF 4.008 (the published nS whole; a
diagnostic), FIT2's training sweeps as built and with na_k_pump off; each form in its own process. The CPU reference
at -15 pA is -89.97 mV (naudin22_afd_check.py, 01:00).

  python scripts/worm/debug2/naudin22_pump.py FEATURES.npz OUT.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

FORMS = {"as_built": {}, "pump_off": {"na_k_pump": "off"}}
BASE = {"afd_membrane": "naudin22", "sens_thermo": "off"}
CPU_REF_M15 = -89.97


def one(feats, form):
    sys.argv = [sys.argv[0], feats]                      # ephys_score reads its features path from argv[1]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))
    import ephys_score as E
    orig = E.S.B.sample_worm

    def worm(seed):
        w = orig(seed)
        w.values["n22_C_pF"] = 4.008
        return w

    E.S.B.sample_worm = worm
    ex = dict(BASE, **FORMS[form])
    br = E.S.build(cells=["AFDL"], extra=ex)
    mechs = [type(m).__module__.split(".")[-1] for m in br.mechs]
    r = E.score(ex, ["AFD"])["AFD"]
    print(json.dumps(dict(form=form, mechs=mechs, rmse_mV=r["rmse_mV"], steady=r["model"]["steady"],
                          baseline=r["model"]["baseline"], data_steady=r["data"]["steady"])))


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2], sys.argv[3])
        sys.exit()
    feats, out = sys.argv[1], sys.argv[2]
    root = Path(__file__).resolve().parents[3]
    res = {}
    for f in FORMS:
        p = subprocess.run([sys.executable, __file__, "one", feats, f], capture_output=True, text=True, cwd=root,
                           env=dict(os.environ, PYTHONPATH=str(root / "src")), timeout=1800)
        assert p.returncode == 0, p.stderr[-3000:]
        res[f] = json.loads(p.stdout.strip().splitlines()[-1])
        res[f]["m15_minus_cpu_mV"] = res[f]["steady"][0] - CPU_REF_M15
        print({k: v for k, v in res[f].items() if k != "mechs"}, flush=True)
    print("mechs", res["as_built"]["mechs"])
    Path(out).write_text(json.dumps(res, indent=1))
