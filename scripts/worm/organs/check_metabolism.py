"""Row 20 unit check: the AmP C. elegans DEB, isolated, at f = 1 and 20 C (bar in the worgans night file).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/organs/check_metabolism.py OUT.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from wormemu.mech import metabolism as me  # noqa: E402

AMP_PRED = {"a_b_d": 0.3257, "t_p_d": 2.934, "R_i_per_d": 170.4}
DATA = {"t_p_d": 2.708, "R_i_per_d": 218.0}                    # Byerly, Cassada & Russell 1976 (AmP data table)


def main():
    out = Path(sys.argv[1])
    q = me.defaults()
    d = me.Deb(q)
    E0, yb, ab = d.solve_e0(1.0)
    yp, tp = d.integrate(yb, 10.0, 1.0, until=lambda y: y[2] >= q["deb_e_hp_J"])
    # day-1 adult: 3.5 d after hatching
    d.L_j = None
    d.L_b = yb[1]
    y35, _ = d.integrate(yb, 3.5, 1.0)
    _, fl35 = d.fluxes(y35, 1.0)
    o2 = d.heat_J_per_d(fl35) / (q["met_oxycal_kJ_per_mol"] * 1e3) * 1e12 / 1440.0
    parts = {k: float(x / (q["met_oxycal_kJ_per_mol"] * 1e3) * 1e12 / 1440.0) for k, x in (
        ("maintenance", fl35["pS"]), ("maturity_maint", fl35["pJ"]),
        ("assimilation_overhead", (1 - q["deb_kap_x"] - q["deb_kap_p"]) / q["deb_kap_x"] * fl35["pA"]),
        ("growth_overhead", (1 - me.KAP_G) * fl35["pG"]),
        ("reproduction_overhead", (1 - q["deb_kap_r"]) * max(fl35["pR"], 0.0)))}
    y, R = y35.copy(), []
    for day in range(60):
        y, _ = d.integrate(y, 1.0, 1.0)
        R.append(d.eggs_per_d(d.fluxes(y, 1.0)[1]))
    Ri = float(R[-1])
    res = {"E_0_J": E0, "a_b_d": float(ab), "L_b_total_cm": float(yb[1] / q["deb_del_m"]), "t_p_d": float(tp),
           "L_p_total_cm": float(yp[1] / q["deb_del_m"]), "s_M": float(d.L_j / d.L_b),
           "R_i_per_d": Ri, "R_day1_adult_per_d": float(d.eggs_per_d(fl35)),
           "L_i_total_cm": float(y[1] / q["deb_del_m"]), "e_day1_adult": float(y35[0] / y35[1] ** 3 / d.E_m),
           "o2_day1_adult_pmol_per_min": float(o2), "o2_parts": parts, "R_by_day": [float(r) for r in R[:10]]}
    fid = {k: abs(res[k] / v - 1.0) for k, v in AMP_PRED.items()}
    dat = {k: abs(res[k] / v - 1.0) for k, v in DATA.items()}
    s = {"fidelity_5pct": all(x <= 0.05 for x in fid.values()), "data_30pct": all(x <= 0.30 for x in dat.values()),
         "o2_1_16": 1.0 <= o2 <= 16.0}
    s["pass"] = all(s.values())
    res.update(fidelity_rel_err=fid, data_rel_err=dat, score={k: bool(x) for k, x in s.items()})
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
