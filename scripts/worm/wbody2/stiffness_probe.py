"""Item 7 probe (wbody2, 8 Nov 2026; DEBUG_TRIAGE line 10): does a value of the new stiffness rule parameter inside
its range give the whole-worm bending modulus Backholm et al. 2013 measured? Diagnostic only, nothing adopted (the
template stays 1, the Frontiers moduli as published).

Bar (written before running). rule_body_modulus_scale on 61 log-spaced values over its registered range
[0.058, 1.35] (body/layers.py), every other value at its template; the section bending modulus of worm_mesh_4
(tet_moduli's E_bending_kPa, the r^2-weighted mean the FEM's tetrahedra carry). D if some in-range value gives
50-170 kPa (Backholm 2013 PNAS 110:4528, 110 +- 30 kPa, 2 sd). Also reported, not barred: the ideal-shell modulus
at the same values; each source's own band (Frontiers: every layer at its published low / high end, pressurised;
Backholm: 50-170 kPa) as a scale interval and whether the two overlap; the backholm2013 form's scale; and, as a
check of the mesh against the ideal shells, the share of the r^2 weight the mesh puts outside the core (ideal: 1 -
(1 - c - h - m)^4).

Usage: python stiffness_probe.py   -> runs/worm/wbody2/stiffness_probe.json
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


def mesh_outer_share(p):
    """Share of the mesh's r^2 weight at rho above the core edge, against the ideal concentric shells."""
    V, T = L.read_mesh()
    z = V[:, 2]
    edges = np.linspace(z.min(), z.max(), L.N_ZBINS + 1)
    vb = np.clip(np.digitize(z, edges) - 1, 0, L.N_ZBINS - 1)
    cen = np.array([V[vb == b, :2].mean(0) for b in range(L.N_ZBINS)])
    R = np.array([np.linalg.norm(V[vb == b, :2] - cen[b], axis=1).max() for b in range(L.N_ZBINS)])
    pts = np.einsum("sk,tkd->tsd", L._barycentric(), V[T])
    pb = np.clip(np.digitize(pts[..., 2], edges) - 1, 0, L.N_ZBINS - 1)
    r = np.linalg.norm(pts[..., :2] - cen[pb], axis=-1)
    rho = np.clip(r / R[pb], 0, 1)
    vol = np.abs(np.einsum("tij,tij->t", np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])[:, None, :],
                           (V[T[:, 3]] - V[T[:, 0]])[:, None, :])) / 6
    w = vol[:, None] * r ** 2
    edge = 1 - p["body_frac_cuticle"] - p["body_frac_hypodermis"] - p["body_frac_muscle"]
    return dict(mesh=float(w[rho > edge].sum() / w.sum()), ideal=float(1 - edge ** 4), core_edge_rho=float(edge),
                rho_p99=float(np.quantile(rho, 0.99)), n_tet=int(len(T)))


def main():
    S = {s.id: s for s in L.SPECS}
    rs = S["rule_body_modulus_scale"]
    xs = np.exp(np.linspace(np.log(rs.lo), np.log(rs.hi), 61))
    rows = []
    for x in xs:
        _, sm = L.tet_moduli({"rule_body_modulus_scale": float(x)})
        rows.append(dict(scale=float(x), mesh_kPa=sm["E_bending_kPa"], ideal_kPa=sm["E_bending_ideal_kPa"]))
    ok = [r for r in rows if 50.0 <= r["mesh_kPa"] <= 170.0]
    _, t0 = L.tet_moduli({})
    _, lo = L.tet_moduli({k: S[k].lo for k in LAYER})
    _, hi = L.tet_moduli({k: S[k].hi for k in LAYER})
    _, p0 = L.tet_moduli({"body_pressure_kPa": 0.0})
    fr = (lo["E_bending_kPa"] / t0["E_bending_kPa"], hi["E_bending_kPa"] / t0["E_bending_kPa"])
    bh = (50.0 / t0["E_bending_kPa"], 170.0 / t0["E_bending_kPa"])
    w, info = L.world_flags({"body_layers": "backholm2013", "body_damping": "none"}, "/tmp/wb2_stiff",
                            {"scale": "worm_1mm"})
    res = dict(bar=__doc__.split("Bar (written before running). ")[1].split("\n\nUsage")[0],
               range=[rs.lo, rs.hi], template_mesh_kPa=t0["E_bending_kPa"], template_ideal_kPa=t0["E_bending_ideal_kPa"],
               n_in_band=len(ok), scale_in_band=[ok[0]["scale"], ok[-1]["scale"]] if ok else None,
               verdict="D: an in-range value gives 50-170 kPa" if ok else "no in-range value gives 50-170 kPa",
               frontiers_band_scale=fr, frontiers_band_kPa=[lo["E_bending_kPa"], hi["E_bending_kPa"]],
               backholm_band_scale=bh, sources_overlap=bool(fr[0] <= bh[1] and bh[0] <= fr[1]),
               backholm_form=dict(scale=info.get("rule_body_modulus_scale"), mesh_kPa=info.get("E_bending_kPa"),
                                  ideal_kPa=info.get("E_bending_ideal_kPa")),
               depressurised_template=dict(mesh_kPa=p0["E_bending_kPa"], ideal_kPa=p0["E_bending_ideal_kPa"]),
               mesh_outer_share=mesh_outer_share({**L.P}), rows=rows)
    out = ROOT / "runs/worm/wbody2/stiffness_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("bar", "rows")}, indent=1))


if __name__ == "__main__":
    main()
