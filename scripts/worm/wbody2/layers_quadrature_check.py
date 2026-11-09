"""Body-mesh quadrature fix (wbody2, 8 Nov 2026; found in item 7, class A): layers.tet_moduli put 4.6 % of the
mesh's r^2 weight outside the core edge, against 38.5 % for the concentric shells it stands for. Two causes: 4
interior sample points per tetrahedron (the text said 35), and R(z) taken as the largest vertex radius of a
40-slice, so most surface points sat at rho < 0.886 (the core edge). The fix: the layer coordinate is r / R(z,
theta), R the distance from the body axis to the mesh surface along the same radial ray, and each tetrahedron is
sampled at the centroids of its 8^3 equal-volume sub-tetrahedra (Bey 1995 red refinement).

Bar (written before running). On worm_mesh_4, the mesh section modulus (tet_moduli's E_bending_kPa) within 5 % of
the ideal concentric shells' (E_bending_ideal_kPa) at (a) the template and (b) depressurised (body_pressure_kPa 0).
Reported, not barred: the same with every layer at its published low and at its high end; the share of the r^2
weight outside the core edge against 1 - edge^4 (the two are equal for any star-shaped section, derived); the
refinement at 2 levels and 4 levels (convergence); the per-tet modulus bounds (inside the cuticle-muscle range); the
Backholm band as a scale on the fixed mesh; and the before values (old rule, runs/worm/wbody2/stiffness_probe.json:
template 856.4 vs 794.2 kPa, +7.8 %; depressurised 127.6 vs 324.4 kPa, -60.7 %).

Usage: python layers_quadrature_check.py   -> runs/worm/wbody2/layers_quadrature_check.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.body import layers as L  # noqa: E402

LAYER = ("body_E_cuticle_kPa", "body_E_muscle_kPa", "body_E_core_kPa", "body_E_core_depressurised_kPa")


def rel(s):
    return s["E_bending_kPa"] / s["E_bending_ideal_kPa"] - 1


def main():
    S = {s.id: s for s in L.SPECS}
    p = dict(L.P)
    cases = {"template": {}, "depressurised": {"body_pressure_kPa": 0.0},
             "layers_low": {k: S[k].lo for k in LAYER}, "layers_high": {k: S[k].hi for k in LAYER}}
    out = {}
    for name, q in cases.items():
        E, s = L.tet_moduli(q)
        lay = L.profile(np.array([0.0, 0.92, 0.99]), {**p, **q})          # core (at this pressure), muscle, cuticle
        out[name] = dict(mesh_kPa=s["E_bending_kPa"], ideal_kPa=s["E_bending_ideal_kPa"], rel=rel(s),
                         E_tet_min_kPa=float(E.min() / 1e3), E_tet_max_kPa=float(E.max() / 1e3),
                         inside_layer_range=bool(lay.min() - 1e-6 <= E.min() / 1e3 <= E.max() / 1e3
                                                 <= lay.max() + 1e-6))
    conv = {}
    for k in (2, 4):
        _, s = L.tet_moduli({}, refine=k)
        _, s0 = L.tet_moduli({"body_pressure_kPa": 0.0}, refine=k)
        conv[f"refine_{k}"] = dict(template_kPa=s["E_bending_kPa"], depressurised_kPa=s0["E_bending_kPa"])
    g = L.mesh_geometry()
    edge = 1 - p["body_frac_cuticle"] - p["body_frac_hypodermis"] - p["body_frac_muscle"]
    w = g["vol"][:, None] * g["r"] ** 2
    share = dict(mesh=float(w[g["rho"] > edge].sum() / w.sum()), ideal=float(1 - edge ** 4), core_edge_rho=edge,
                 rho_p99=float(np.quantile(g["rho"], 0.99)), rho_max=float(g["rho"].max()),
                 n_points_per_tet=int(g["r"].shape[1]), ray_miss_frac=g["ray_miss_frac"])
    t0 = out["template"]["mesh_kPa"]
    res = dict(bar=__doc__.split("Bar (written before running). ")[1].split("\n\nUsage")[0], cases=out,
               convergence=conv, outer_share=share,
               backholm_band_scale=[50.0 / t0, 170.0 / t0],
               frontiers_band_scale=[out["layers_low"]["mesh_kPa"] / t0, out["layers_high"]["mesh_kPa"] / t0],
               before=dict(template=[856.37, 794.23], depressurised=[127.65, 324.45], outer_share=[0.0462, 0.3851]))
    res["bar_pass"] = bool(abs(out["template"]["rel"]) <= 0.05 and abs(out["depressurised"]["rel"]) <= 0.05)
    o = ROOT / "runs/worm/wbody2/layers_quadrature_check.json"
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "bar"}, indent=1))


if __name__ == "__main__":
    main()
