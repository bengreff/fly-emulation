"""Item 3 stage (2) probe (wbody2, 8 Nov 2026): if AVL and DVB fire, does the model make an expulsion? Diagnostic
only: a diagnostic current stands in for AVL's and DVB's activity (they never fire at the ledger values: brain-owned,
Requests); nothing here is adopted.

Bar (written before running): AVL and DVB activity once per cycle triggers the expulsion step (Thomas 1990; Wang et
al. 2013: DVB Ca transient once per cycle, before the expulsion; McIntire et al. 1993: AVL and DVB ablation removes
the expulsion). Pass: one drive event gives exactly 1 expulsion (mean mu_intL/mu_intR/mu_anal activation above
ent_exp_on 0.5, then below ent_exp_off 0.2) at some drive in the grid; report the smallest.
Grid: step current into AVL and DVB of 10, 20, 40, 80 pA for 0.2, 0.5, 1, 2 s, from 8 s (after the enteric
muscles' start-up event at about 6 s), 4 s observed after the step. Pharynx-style subprocess per point.
Usage: python enteric_probe.py [toggle=value ...]   -> runs/worm/wbody2/enteric_probe[_tag].json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PAS = [10.0, 20.0, 40.0, 80.0]
DURS = [0.2, 0.5, 1.0, 2.0]
T_ON, T_AFTER = 8.0, 4.0


def one(pa, dur, tog):
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm" / "wbody2"))
    import at_ledger
    at_ledger.patch()
    from dmp_trace import DMP
    from wormemu import brain as B
    from wormemu.interface import ENTERIC_MUSCLES
    b = B.Brain(B.sample_worm(None), toggles=dict(tog), cells=DMP)
    inj = [b.idx[n] for n in ("AVL", "DVB")]
    b.reset()
    secs = T_ON + dur + T_AFTER
    exps, t_exp = 0, []
    vmax = {n: -1e9 for n in ("AVL", "DVB")}
    ev_max = np.full(len(ENTERIC_MUSCLES), -1e9)
    act_max, ca_max, n_spk = 0.0, 0.0, 0
    prev = None
    for k in range(int(secs * 1000)):
        b.extra_pA[:] = 0.0
        on = T_ON * 1000 <= k < (T_ON + dur) * 1000
        if on:
            b.extra_pA[inj] = pa
        o = b.step(None, 1.0)
        if k < T_ON * 1000:
            continue
        if o.expulsions:
            exps += int(o.expulsions)
            t_exp.append(k / 1000.0)
        for n, j in zip(("AVL", "DVB"), inj):
            vmax[n] = max(vmax[n], float(o.v_mV[j]))
        mo = b.mech_out
        ev = np.asarray(mo["enteric_v_mV"])
        ev_max = np.maximum(ev_max, ev)
        if prev is not None:
            n_spk += int(prev < 0.0 <= ev[0])
        prev = ev[0]
        act_max = max(act_max, float(np.mean(mo["enteric_activation"][:3])))
        ca_max = max(ca_max, float(np.max(mo["enteric_ca_mM"])))
    return dict(pA=pa, dur_s=dur, expulsions=exps, t_exp_s=t_exp, AVL_vmax=vmax["AVL"], DVB_vmax=vmax["DVB"],
                enteric_vmax=dict(zip(ENTERIC_MUSCLES, ev_max.tolist())), mu_intL_spikes=n_spk,
                act3_max=act_max, ca_max_mM=ca_max)


def main():
    if len(sys.argv) >= 3 and "=" not in sys.argv[1]:
        tog = dict(a.split("=", 1) for a in sys.argv[3:])
        print(json.dumps(one(float(sys.argv[1]), float(sys.argv[2]), tog)))
        return
    tog_args = [a for a in sys.argv[1:] if "=" in a]
    tag = "_".join(a.replace("=", "-") for a in tog_args)
    rows, t0 = [], time.time()
    for pa in PAS:
        for d in DURS:
            r = subprocess.run([sys.executable, __file__, str(pa), str(d)] + tog_args, capture_output=True, text=True)
            if r.returncode:
                rows.append(dict(pA=pa, dur_s=d, error=r.stderr[-800:]))
            else:
                rows.append(json.loads(r.stdout.strip().splitlines()[-1]))
            print(rows[-1], flush=True)
    ok = [r for r in rows if r.get("expulsions") == 1]
    res = dict(bar="one AVL+DVB drive event gives exactly 1 expulsion at some (pA, duration)", toggles=tog_args,
               grid=dict(pA=PAS, dur_s=DURS, t_on_s=T_ON, t_after_s=T_AFTER), rows=rows, passing=ok,
               smallest=min(ok, key=lambda r: r["pA"] * r["dur_s"]) if ok else None,
               verdict="a drive passes" if ok else "no drive in the grid passes", wall_s=time.time() - t0)
    out = ROOT / f"runs/worm/wbody2/enteric_probe{'_' + tag if tag else ''}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(res["verdict"], f"{res['wall_s']:.0f} s")


if __name__ == "__main__":
    main()
