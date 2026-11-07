"""Row 16 unit check: excretory canal ablation and coelomocyte uptake, numpy (bar in the worgans night file).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/organs/check_other.py OUT.json
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from wormemu.mech import organs_other as oo  # noqa: E402

DT_S = 1.0


def fluid(form, hours=24.0):
    m = oo.Mech(SimpleNamespace(idx={}, spec=None), {}, {"other_cells": "off", "excretory_osmo": form})
    ctx = SimpleNamespace(obs=None, outputs={})
    t, v, P = [], [], []
    for k in range(int(hours * 3600 / DT_S)):
        o = m.step(ctx, DT_S * 1000.0)["out"]
        t.append((k + 1) * DT_S / 3600.0)
        v.append(o["body_fluid_volume_rel"])
        P.append(o["pressure_kPa"])
    return np.array(t), np.array(v), np.array(P), m


def tracer(form, minutes=10.0):
    m = oo.Mech(SimpleNamespace(idx={}, spec=None), {}, {"other_cells": "off", "coelomocytes": form})
    k = m.step(SimpleNamespace(obs=None, outputs={}), 1000.0)["out"]["coelomocyte_uptake_per_s"]
    c, taken = 1.0, 0.0
    for _ in range(int(minutes * 60 / DT_S)):
        d = c * (1.0 - np.exp(-k * DT_S))
        c, taken = c - d, taken + d
    return taken, k


def main():
    out = Path(sys.argv[1])
    tw, vw, Pw, m = fluid("canal")
    tn, vn, Pn, _ = fluid("null")
    q = m.q
    dpi = oo.RT_KPA_PER_MOSM * q["osmo_dosm_mOsm"]
    v_inf = 1.0 + (dpi - q["osmo_p_set_kPa"]) / q["osmo_e_vol_kPa"]
    frac = (vn - 1.0) / (v_inf - 1.0)
    i90 = int(np.argmax(frac >= 0.9)) if (frac >= 0.9).any() else None
    t90 = float(tn[i90]) if i90 is not None else None
    wt_dev = float(np.max(np.abs(Pw - q["osmo_p_set_kPa"])) / q["osmo_p_set_kPa"])
    up_wt, k = tracer("on")
    up_null, _ = tracer("null")
    res = {"t90_null_h": t90, "null_v_24h": float(vn[-1]), "null_P_24h_kPa": float(Pn[-1]),
           "null_v_inf": float(v_inf), "null_P_inf_kPa": float(dpi), "wt_P_max_rel_dev": wt_dev,
           "tracer_10min_wt": float(up_wt), "tracer_10min_null": float(up_null), "uptake_per_s": float(k),
           "analytic_t90_h": float(np.log(10.0) / (q["osmo_lp_per_kPa_s"] * q["osmo_e_vol_kPa"]) / 3600.0)}
    s = {"ablation_12_24h": t90 is not None and 12.0 <= t90 <= 24.0, "wt_holds": wt_dev <= 0.01,
         "tracer": up_wt >= 0.05 and up_null == 0.0}
    s = {k: bool(x) for k, x in s.items()}
    s["pass"] = all(s.values())
    res["score"] = s
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
