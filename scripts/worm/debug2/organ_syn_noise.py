"""Bars of "Organ synapses and quantal noise" (docs/worm/night/2026-11-08_wbrain2.md, written before this ran;
wbrain2, 9 Nov 2026): noise.Quantal binds brain.wsyn at the first reset, so the organ modules' synapses (post -1)
get quantal noise. Each brain runs in its own subprocess.

  python scripts/worm/debug2/organ_syn_noise.py OUT.json            # all bars
  python scripts/worm/debug2/organ_syn_noise.py one cells|full old|new   # one brain, JSON on stdout's last line

`old` swaps in the Quantal of noise.py at git HEAD (the code before the edit, read with git show into /tmp; run it
before the edit is committed).
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OLD = Path("/tmp/wb2_noise_old.py")


def one(which, code):
    from wormemu.mech import noise
    if code == "old":
        spec = importlib.util.spec_from_file_location("wb2_noise_old", OLD)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        noise.Quantal = old.Quantal
    from wormemu.brain import Brain
    sys.path.insert(0, str(ROOT / "tests"))
    from test_worm_neuromod import CELLS
    b = Brain(cells=CELLS if which == "cells" else None)
    n_build = len(b.wsyn)
    b.reset()
    q = next(m.q for m in b.mechs if type(m).__module__ == "wormemu.mech.noise")
    n_q = 0 if q.shot is None else len(q.shot.gq)
    post = np.array([j for _, _, j, _ in b.wsyn])
    organ = {type(m).__module__.split(".")[-1]: len(m.wsyn) for m in b.mechs
             if type(m).__module__.split(".")[-1].startswith("organs_") and hasattr(m, "wsyn")}
    V, outs = [], []
    if which == "cells":
        for c, a in (("AVBL", 40.0), ("ASHL", 30.0)):
            b.extra_pA[b.idx[c]] = a
    for _ in range(300):
        o = b.step(None, 1.0)
        V.append(o.v_mV.copy())
        outs.append(b.mech_out.get("quantal_noise"))
    r = dict(n_wsyn_build=n_build, n_wsyn_reset=len(b.wsyn), n_quantal=n_q, n_organ=int((post < 0).sum()),
             organ_by_module=organ, V=np.array(V).tolist(), noise_out=outs)
    if q.shot is not None:
        org = np.flatnonzero(post < 0)
        gd = np.array([float(b.wsyn[i][0].gd) for i in range(len(b.wsyn))])
        qn = np.array([float(b.wsyn[i][0].qn) for i in range(len(b.wsyn))])
        r.update(organ_gd_pos=int((gd[org] > 0).sum()), organ_qn_not1=int(((gd[org] > 0) & (qn[org] != 1.0)).sum()))
        old_mask = np.asarray(b.is_muscle)[post]                  # the mask before the edit
        r["old_mask_organ_true"] = int(old_mask[post < 0].sum())
        if n_q == len(b.wsyn):                                    # the new code: every synapse is in the noise
            lam = gd / (q.shot.gq * q.shot.tau)
            r.update(organ_vesicle_share=float(lam[org].sum() / lam.sum()) if lam.sum() > 0 else None,
                     mask_brain_equal=bool(np.array_equal(q.to_muscle[post >= 0], old_mask[post >= 0])),
                     mask_organ_false=bool(not q.to_muscle[post < 0].any()))
    print(json.dumps(r))


def sub(which, code):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    p = subprocess.run([sys.executable, __file__, "one", which, code], capture_output=True, text=True, env=env,
                       cwd=ROOT, timeout=1800)
    assert p.returncode == 0, p.stderr[-3000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2], sys.argv[3])
        sys.exit()
    OLD.write_text(subprocess.run(["git", "show", "HEAD:src/wormemu/mech/noise.py"], capture_output=True, text=True,
                                  cwd=ROOT, check=True, env=dict(os.environ, DEVELOPER_DIR="/Library/Developer/"
                                                                 "CommandLineTools")).stdout)
    res = {}
    o, n = sub("cells", "old"), sub("cells", "new")
    res["bar1"] = dict(n_organ=n["n_organ"], n_wsyn=n["n_wsyn_build"], n_quantal=(o["n_quantal"], n["n_quantal"]),
                       max_abs_dV_mV=float(np.abs(np.array(o["V"]) - np.array(n["V"])).max()),
                       noise_out_equal=o["noise_out"] == n["noise_out"])
    res["bar1"]["passed"] = bool(n["n_organ"] == 0 and res["bar1"]["max_abs_dV_mV"] == 0.0
                                 and res["bar1"]["noise_out_equal"])
    print("bar1", res["bar1"], flush=True)
    f_old, f = sub("full", "old"), sub("full", "new")
    keep = ("n_wsyn_build", "n_wsyn_reset", "n_quantal", "n_organ", "organ_by_module", "organ_gd_pos",
            "organ_qn_not1", "organ_vesicle_share", "mask_brain_equal", "mask_organ_false", "old_mask_organ_true")
    res["full_new"] = {k: f.get(k) for k in keep}
    res["full_old"] = {k: f_old.get(k) for k in keep}
    res["bar2"] = dict(passed=bool(f["n_quantal"] == f["n_wsyn_reset"] and f["n_organ"] > 0
                                   and f["organ_qn_not1"] >= 1))
    res["bar3"] = dict(passed=bool(f["mask_brain_equal"] and f["mask_organ_false"]))
    res["full_max_abs_dV_mV_old_vs_new"] = float(np.abs(np.array(f_old["V"]) - np.array(f["V"])).max())
    print("full", res["full_new"], "old", res["full_old"], "bar2", res["bar2"], "bar3", res["bar3"], flush=True)
    Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
