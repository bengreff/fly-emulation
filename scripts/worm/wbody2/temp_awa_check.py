"""Temperature's conductance Q10 on AWA's Liu membrane (wbody2, 9 Nov 2026; wbrain2's Request): temperature.Mech
scaled G_SCALE_NAMES only, so Liu's eight conductances (g_scale dens_awa_<c>, mech.AWA_G_SCALE) kept their 20 C
values at any plate temperature, while every BAAIWorm channel in the other cells took the factor.

Bars (written 04:4x in the night file, before the edit): (1) at 20 C (T_ref, the default experiment) the q10 and off
toggles give bit-identical voltages over 300 steps, 8 pA into AWAL, cells AWAL and AIYL; (2) at 30 C every AWA
segment's eight Liu conductances are base x temp_q10_conductance (1.5) within 1e-12. Also printed (no bar): AWAL's
mean V over the last 100 steps at 30 C with and without the AWA names (the old rule, emulated here by dropping them
from temperature's g_scale).

    python temp_awa_check.py -> runs/worm/wbody2/temp_awa_check.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu import brain as B  # noqa: E402
from wormemu.interface import default_observation  # noqa: E402
from wormemu.mech import AWA_G_SCALE, AWA_G_SCALE_NAMES, temperature  # noqa: E402


def run(T, toggle="q10", old=False):
    b = B.Brain(cells=["AWAL", "AIYL"], toggles={"temperature": toggle})
    tm = next((m for m in b.mechs if isinstance(m, temperature.Mech)), None)
    if old and tm is not None:
        step = tm.step

        def old_step(ctx, dt_ms):
            r = step(ctx, dt_ms)
            return dict(r, g_scale={k: x for k, x in r["g_scale"].items() if k not in AWA_G_SCALE_NAMES})
        tm.step = old_step
    b.reset()
    a = b.idx["AWAL"]
    b.extra_pA[a] = 8.0
    vs = []
    for i in range(300):
        o = default_observation(b.t)
        o.head = {**o.head, "temperature_C": float(T)}
        vs.append(b.step(o).v_mV)
    segs = [seg for s in b.cells[a].all for seg in s]
    g = {c: [getattr(seg.awa_liu, mod) for seg in segs] for c, mod in AWA_G_SCALE.items()}
    return np.array(vs), a, g, b


def main():
    v_q, a, g20, b = run(20.0, "q10")
    v_off, _, _, _ = run(20.0, "off")
    base = {c: b._gt[f"dens_awa_{c}"][2].copy() for c in AWA_G_SCALE}
    v30, _, g30, _ = run(30.0, "q10")
    v30_old, _, g30_old, _ = run(30.0, "q10", old=True)
    phi = next(m for m in b.mechs if isinstance(m, temperature.Mech)).p["temp_q10_conductance"]
    err = {c: float(max(abs(x / y - phi) for x, y in zip(g30[c], base[c]) if y != 0) if any(base[c]) else 0.0)
           for c in AWA_G_SCALE}
    old_err = {c: float(max(abs(x / y - 1.0) for x, y in zip(g30_old[c], base[c]) if y != 0) if any(base[c]) else 0.0)
               for c in AWA_G_SCALE}
    res = dict(bar1_dv_20C_q10_vs_off=float(np.abs(v_q - v_off).max()), bar2_rel_err_30C=err, phi=phi,
               n_segs=len(g20["kir"]), old_rule_unscaled_err=old_err,
               awal_meanV_last100_30C=float(v30[-100:, a].mean()), awal_meanV_last100_30C_old=float(v30_old[-100:, a].mean()),
               awal_meanV_last100_20C=float(v_q[-100:, a].mean()),
               zero_base=[c for c in AWA_G_SCALE if not any(base[c])])
    res["PASS"] = bool(res["bar1_dv_20C_q10_vs_off"] == 0.0 and max(err.values()) < 1e-12)
    (ROOT / "runs/worm/wbody2/temp_awa_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
