"""Row 21, the body as layers: cuticle, hypodermis, muscle and a pressurised core, plus shear-thinning internal
damping. Both ride on the MetaWorm FEM through two driver extensions (third_party/metaworm/UPSTREAM.md):
--tet_youngs (a Young's modulus per tetrahedron) and --damping backholm2013.

Layers (body_layers = "frontiers2024", the default): the three-compartment neo-Hookean FE model of the young adult
fitted to AFM indentation (Frontiers Bioeng Biotechnol 2024, 12:1335788, read 6 Nov 2026; equations as
published: one modulus per compartment, the compartments concentric shells). The BDM-control fit is the template:
cuticle 150, muscle 1200, pseudocoelom 840 kPa. Thicknesses from the paper's geometry (cuticle 0.6, hypodermis 0.1,
muscle 1.0 um on a 13.15 um core radius) become fractions of the local body radius (derived), so the mesh's radius
carries them. The hypodermis takes the cuticle's modulus (inferred; it is 0.7 % of the radius, at most 3 % of the
section's bending stiffness, derived). The muscle layer is a full annulus, as in the paper; the real quadrants
leave the lateral cords out (inferred validity: bending stiffness to a few %).

Each tetrahedron gets the modulus that keeps its share of the bending stiffness, E_tet = int E(r) r^2 dV /
int r^2 dV over the tet (35 interior sample points), r the distance from the slice centroid and r / R(z) the
layer coordinate, R(z) the largest vertex radius of the tet's z-slice (40 slices) (inferred: the r^2 weight is
the section's second moment averaged over bending directions).

Pressure: the pseudocoelom's stiffness is mostly turgor (BODY.md: the bulk response is pressure-dominated, Worms
under Pressure 2015). The hyperosmotic-shock fit of the same paper (core 76 kPa) is the depressurised end, so the
core modulus is E_core(P) = E_depr + (E_ctrl - E_depr) * P / P_ctrl (inferred structure, linear between the two
measured states). The worm has one pressure: pressure_link sets P to organs_other's body-fluid pressure at
start-up (osmo_p_set_kPa in the template medium; the steady state in another medium) and P_ctrl to its set point,
so body_pressure_kPa and body_pressure_ctrl_kPa are derived (params.LINKED) and E_core = body_E_core_kPa in the
template medium (the same as the two old 100 kPa constants: only the ratio enters). The driver's FEM is
factorised once, so a pressure that changes during a run needs a refactorisation (Open).

Damping (body_damping = "backholm2013", the default): the worm is viscoelastic with a damping coefficient that
falls as bending speed^-1 over two decades (Backholm, Ryu & Dalnoki-Veress 2013 PNAS 110:4528, measured). Here the
internal viscosity is a corotational Kelvin-Voigt dashpot on each tetrahedron: energy (tau / h) w_e |F - R S_n|^2,
F the deformation gradient, R its rotation and S_n the stretch at the previous step, so the dashpot resists the
rate of stretch and not the element's rotation (in a corotated FEM bending is mostly rotation; a constant
tau L dashpot froze the body, checked 6 Nov 2026). It adds (tau / h) L to the implicit solve's matrix and its
targets to the right-hand side (World::SetCorotDamping, inferred structure). tau(w) = tau_ref
* clip((w / w_ref)^-alpha, 1/clip, clip), w the RMS rate of the body's slice tangents (rad/s). tau_ref = 2 ms at
w_ref = 10 rad/s (guessed, under the 5.3 ms bound derived from Fang-Yen et al. 2010 PNAS 107:20323: internal
viscosity < 5e-16 N m^2 s over bending stiffness 9.5e-14 N m^2). Backholm gives the exponent, not the prefactor.
Needs an RFT fluid (worm_1mm scale).

Stiffness rule (8 Nov 2026, Ben's approved fittable rule parameter; DEBUG_TRIAGE line 10): rule_body_modulus_scale
multiplies every layer modulus (template 1 = the Frontiers values as published, so neutral). Its range is bounded
by the two sources, which do not overlap: the Frontiers layer ranges give a mesh section modulus of 776-1157 kPa for
the pressurised worm (scale 0.91-1.35), Backholm 2013's whole-worm bending 110 +- 30 kPa (2 sd 50-170) gives scale
0.058-0.199 (all derived on worm_mesh_4). body_layers = "backholm2013" is the second alternative: the Frontiers
profile scaled so the mesh section modulus is body_E_bending_kPa (Backholm's measured whole-worm value; the rule
parameter is then unused). The fit runs both ways.

Nested forms: body_layers = "published" (every tetrahedron the constructor's 2e5 Pa, upstream MetaWorm) and
body_damping = "none" (upstream). Both nested together pass no flag, so the driver runs as upstream (test:
bit-identical frames, scripts/worm/body_layers_check.py). The upstream (non-SI) scale gets neither.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from wormemu.mech.senses_base import spec

MECHANISMS = [
    ("body_layers", "Body: cuticle / hypodermis / muscle / pressurised core moduli per tetrahedron (Frontiers 2024)",
     "body", "frontiers2024"),
    ("body_damping", "Body: shear-thinning internal damping (Backholm 2013), corotational Kelvin-Voigt", "body",
     "backholm2013"),
]
FORMS = {"body_layers": ("frontiers2024", "published", "backholm2013"), "body_damping": ("backholm2013", "none")}
DEFAULTS = {k: v[0] for k, v in FORMS.items()}
NESTED = {k: v[1] for k, v in FORMS.items()}

FR = "Frontiers Bioeng Biotechnol 2024 12:1335788 (three-compartment FE fit to AFM indentation, young adults; read 6 Nov 2026)"
BH = "Backholm, Ryu & Dalnoki-Veress 2013 PNAS 110:4528"
R_PAPER = 0.6 + 0.1 + 1.0 + 13.15  # um, the paper's outer radius (derived from its geometry)
SPECS = [
    spec("body_E_cuticle_kPa", "body_layers", "kPa", 150.0, 75.0, 200.0, "published_fit",
         FR + ": BDM control 150 (100-200); hyperosmotic 90 (75-140)", applies_to="cuticle and hypodermis"),
    spec("body_E_muscle_kPa", "body_layers", "kPa", 1200.0, 280.0, 2350.0, "published_fit",
         FR + ": BDM control 1200 (280-2350)", applies_to="body-wall muscle layer"),
    spec("body_E_core_kPa", "body_layers", "kPa", 840.0, 800.0, 1100.0, "published_fit",
         FR + ": BDM control 840 (800-1100); the pressurised pseudocoelom", applies_to="pseudocoelom core"),
    spec("body_E_core_depressurised_kPa", "body_layers", "kPa", 76.0, 48.0, 185.0, "published_fit",
         FR + ": hyperosmotic shock 76 (48-185), the core with its turgor lost", applies_to="pseudocoelom core"),
    spec("body_frac_cuticle", "body_layers", "1", 0.6 / R_PAPER, 0.02, 0.07, "derived",
         FR + ": cuticle 0.6 um of a 14.85 um radius", notes="range: adult cuticle 0.5-1 um on 15-35 um radii"),
    spec("body_frac_hypodermis", "body_layers", "1", 0.1 / R_PAPER, 0.003, 0.03, "derived",
         FR + ": hypodermis 0.1 um of 14.85 um"),
    spec("body_frac_muscle", "body_layers", "1", 1.0 / R_PAPER, 0.04, 0.12, "derived",
         FR + ": muscle 1.0 um of 14.85 um", notes="range: body-wall muscle 1-3 um thick in adults"),
    spec("body_pressure_ctrl_kPa", "body_layers", "kPa", 100.0, 50.0, 200.0, "guessed",
         "BODY.md: 50-100 kPa (older estimates, Park et al. 2007 PNAS) to 150-200 kPa (FE estimates), unreconciled",
         notes="the pressure of the BDM-control worm the core modulus belongs to; the paper that would pin it: a "
               "direct pressure-probe measurement in C. elegans"),
    spec("body_pressure_kPa", "body_layers", "kPa", 100.0, 0.0, 200.0, "guessed",
         "the run's body pressure; template = the control's, so E_core = body_E_core_kPa",
         notes="to be read from B2's out['pressure_kPa'] at start-up when it lands"),
    spec("rule_body_modulus_scale", "body_layers", "1", 1.0, 0.058, 1.35, "guessed",
         FR + " (upper: every layer at its published high end, 1157 kPa over the template's 856, mesh); " + BH +
         " (lower: 50 kPa, the 2 sd low edge of 110 +- 30, over 856)", applies_to="every layer modulus",
         notes="the fittable rule parameter (Ben, 8 Nov); template 1 = the Frontiers moduli as published (neutral); "
               "the sources' own bands do not overlap: Frontiers 0.91-1.35, Backholm 0.058-0.199 (derived)"),
    spec("body_E_bending_kPa", "body_layers", "kPa", 110.0, 50.0, 170.0, "measured",
         BH + ": whole-worm bending modulus 110 +- 30 kPa (range 2 sd)", applies_to="whole body (backholm2013 form)",
         notes="body_layers = backholm2013 scales the Frontiers profile so the mesh section modulus equals this"),
    spec("body_damp_tau_ms", "body_damping", "ms", 2.0, 0.2, 5.3, "guessed",
         "upper bound derived from Fang-Yen et al. 2010 PNAS 107:20323 (internal viscosity < 5e-16 N m^2 s over "
         "bending stiffness 9.5e-14 N m^2 = 5.3 ms)", notes="Backholm 2013 gives no prefactor in this form"),
    spec("body_damp_alpha", "body_damping", "1", 1.0, 0.7, 1.2, "measured",
         BH + ": damping coefficient ~ bending speed^-1 over two decades (shear-thinning)"),
    spec("body_damp_w_ref_rad_s", "body_damping", "rad/s", 10.0, 2.0, 30.0, "guessed",
         "the slice-tangent rate of a 2 Hz undulation with ~1 rad tangent swing (~9 rad/s, derived)"),
    spec("body_damp_clip", "body_damping", "1", 10.0, 3.0, 100.0, "guessed",
         BH + ": two decades measured, so tau stays within one decade either side of tau_ref"),
]
P = {s.id: s.template for s in SPECS}

MESH = Path(__file__).resolve().parents[3] / "third_party" / "metaworm" / "data" / "worm_mesh_4.mesh"
N_ZBINS = 40


def read_mesh(path: Path = MESH) -> tuple[np.ndarray, np.ndarray]:
    """Vertices (mesh units) and tetrahedra (0-based, file order = the driver's constraint order)."""
    lines = Path(path).read_text().split("\n")
    i = next(k for k, s in enumerate(lines) if s.strip() == "Vertices")
    nv = int(lines[i + 1])
    V = np.array([[float(x) for x in lines[i + 2 + k].split()[:3]] for k in range(nv)])
    j = next(k for k, s in enumerate(lines) if s.strip() == "Tetrahedra")
    nt = int(lines[j + 1])
    T = np.array([[int(x) for x in lines[j + 2 + k].split()[:4]] for k in range(nt)]) - 1
    return V, T


def _barycentric(n: int = 4) -> np.ndarray:
    """Interior sample points of a tetrahedron: the (n+1)(n+2)(n+3)/6 lattice of step 1/(n+1), interior only."""
    pts = [(a, b, c, n + 1 - a - b - c) for a in range(1, n + 1) for b in range(1, n + 1) for c in range(1, n + 1)
           if n + 1 - a - b - c >= 1]
    return np.array(pts, float) / (n + 1)


def profile(rho: np.ndarray, p: dict) -> np.ndarray:
    """Young's modulus (kPa) at normalised radius rho = r / R."""
    P_ratio = p["body_pressure_kPa"] / p["body_pressure_ctrl_kPa"]
    E_core = p["body_E_core_depressurised_kPa"] + (p["body_E_core_kPa"] - p["body_E_core_depressurised_kPa"]) * P_ratio
    c, h, m = p["body_frac_cuticle"], p["body_frac_hypodermis"], p["body_frac_muscle"]
    E = np.where(rho > 1 - c - h, p["body_E_cuticle_kPa"], np.where(rho > 1 - c - h - m, p["body_E_muscle_kPa"], E_core))
    return E * p.get("rule_body_modulus_scale", 1.0)


def tet_moduli(p: dict | None = None, mesh: Path = MESH) -> tuple[np.ndarray, dict]:
    """Young's modulus per tetrahedron (Pa, mesh order) and a summary."""
    p = {**P, **(p or {})}
    V, T = read_mesh(mesh)
    z = V[:, 2]
    edges = np.linspace(z.min(), z.max(), N_ZBINS + 1)
    vb = np.clip(np.digitize(z, edges) - 1, 0, N_ZBINS - 1)
    cen = np.array([V[vb == b, :2].mean(0) for b in range(N_ZBINS)])
    R = np.array([np.linalg.norm(V[vb == b, :2] - cen[b], axis=1).max() for b in range(N_ZBINS)])
    lam = _barycentric()
    pts = np.einsum("sk,tkd->tsd", lam, V[T])                       # (n_tet, n_sample, 3)
    pb = np.clip(np.digitize(pts[..., 2], edges) - 1, 0, N_ZBINS - 1)
    r = np.linalg.norm(pts[..., :2] - cen[pb], axis=-1)
    rho = np.clip(r / R[pb], 0, 1)
    w = r ** 2 + 1e-12
    E = (profile(rho, p) * w).sum(1) / w.sum(1) * 1e3              # Pa
    vol = np.abs(np.einsum("tij,tij->t", np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])[:, None, :],
                           (V[T[:, 3]] - V[T[:, 0]])[:, None, :])) / 6
    # section bending modulus of the mesh: sum E_tet int r^2 dV / sum int r^2 dV (derived)
    I = vol * (r ** 2).mean(1)
    summary = {"n_tet": len(T), "E_min_kPa": float(E.min() / 1e3), "E_max_kPa": float(E.max() / 1e3),
               "E_volume_mean_kPa": float((E * vol).sum() / vol.sum() / 1e3),
               "E_bending_kPa": float((E * I).sum() / I.sum() / 1e3),
               "E_bending_ideal_kPa": float(ideal_bending_modulus(p)),
               "mesh_radius_units": float(np.median(R))}
    return E, summary


def ideal_bending_modulus(p: dict) -> float:
    """The section's bending modulus (kPa) for perfect concentric shells: int E r^3 dr / int r^3 dr (derived)."""
    c, h, m = p["body_frac_cuticle"], p["body_frac_hypodermis"], p["body_frac_muscle"]
    rho = np.linspace(0, 1, 200001)
    return float(np.trapezoid(profile(rho, p) * rho ** 3, rho) / np.trapezoid(rho ** 3, rho))


LINKED = {"body_pressure_kPa": "organs_other's start-up pressure (osmo_p_set_kPa and the medium)",
          "body_pressure_ctrl_kPa": "osmo_p_set_kPa (the control worm's pressure is the set point)"}


def pressure_link(spec=None, osmo_form="canal", extra_mosm=0.0) -> dict:
    """body_pressure_kPa and body_pressure_ctrl_kPa from organs_other's body fluid, for world_flags' p. The linear
    volume-pressure law is valid while P >= 0 (the depressurised end is E_depr); below that P is held at 0."""
    from wormemu import mech
    from wormemu.mech import organs_other
    q = mech.params_for(organs_other, spec) if spec is not None else {s.id: s.template for s in organs_other.SPECS}
    return {"body_pressure_kPa": max(0.0, organs_other.steady_pressure_kPa(q, osmo_form, extra_mosm)),
            "body_pressure_ctrl_kPa": float(q["osmo_p_set_kPa"])}


def params_for(spec=None, osmo_form="canal", extra_mosm=0.0) -> dict:
    """This worm's body-tissue numbers: its values over the templates, with the pressures linked."""
    v = {} if spec is None else spec.values
    return {**{s.id: float(v.get(s.id, s.template)) for s in SPECS},
            **pressure_link(spec, osmo_form, extra_mosm)}


def world_flags(toggles: dict | None, out_prefix: str, world: dict | None, p: dict | None = None) -> tuple[dict, dict]:
    """Driver flags for these toggles (merged into world) and a summary. Only the SI body scale takes them."""
    t = {**DEFAULTS, **(toggles or {})}
    for k, v in t.items():
        assert v in FORMS[k], (k, v)
    world = dict(world or {})
    if world.get("scale") != "worm_1mm":
        return world, {"applied": False}
    p = {**P, **(p or {})}
    info = {"applied": True, **t}
    if t["body_layers"] == "backholm2013":
        _, s0 = tet_moduli({**p, "rule_body_modulus_scale": 1.0})
        p = {**p, "rule_body_modulus_scale": p["body_E_bending_kPa"] / s0["E_bending_kPa"]}
    if t["body_layers"] in ("frontiers2024", "backholm2013"):
        E, s = tet_moduli(p)
        s["rule_body_modulus_scale"] = float(p.get("rule_body_modulus_scale", 1.0))
        path = str(out_prefix) + ".tet_youngs.f64"
        E.astype(np.float64).tofile(path)
        world["tet_youngs"] = path
        info.update(s)
    if t["body_damping"] == "backholm2013":
        world.update({"damping": "backholm2013", "damp_tau_ms": p["body_damp_tau_ms"],
                      "damp_w_ref": p["body_damp_w_ref_rad_s"], "damp_alpha": p["body_damp_alpha"],
                      "damp_clip": p["body_damp_clip"]})
    return world, info
