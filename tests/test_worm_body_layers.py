"""Body layers quadrature (wbody2, 8 Nov 2026): the mesh's section bending modulus must match the concentric shells
it stands for (scripts/worm/wbody2/layers_quadrature_check.py; the old rule was +7.8 % at the template and -60.7 %
depressurised)."""
import numpy as np

from wormemu.body import layers


def test_subtet_points_equal_volume_centroids():
    lam = layers._subtet_points(2)
    assert lam.shape == (64, 4) and np.allclose(lam.sum(1), 1) and np.allclose(lam.mean(0), 0.25)
    assert (lam > 0).all()


def test_mesh_section_modulus_matches_shells():
    for q in ({}, {"body_pressure_kPa": 0.0}):
        _, s = layers.tet_moduli(q)
        assert abs(s["E_bending_kPa"] / s["E_bending_ideal_kPa"] - 1) <= 0.05, (q, s)
    g = layers.mesh_geometry()
    p = layers.P
    edge = 1 - p["body_frac_cuticle"] - p["body_frac_hypodermis"] - p["body_frac_muscle"]
    w = g["vol"][:, None] * g["r"] ** 2
    assert abs(w[g["rho"] > edge].sum() / w.sum() - (1 - edge ** 4)) <= 0.02
    assert g["ray_miss_frac"] < 0.05
