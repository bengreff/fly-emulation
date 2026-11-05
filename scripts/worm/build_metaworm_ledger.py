"""Body ledger for the ported MetaWorm body: every number the running body uses, every number it still lacks.

Outputs
  data/worm/ledger/metaworm_parameters.csv   one row per number (fly parameters.csv columns + lit_check + used)
  data/worm/ledger/metaworm_mechanisms.json  body mechanisms, status and toggles (neutral = the published body)
  viewer/worm/data/mechanisms.json, viewer/worm/data/catalog.json   viewer copies (catalog also merges
                                             docs/worm/ledger.json from the brain worker when it exists)
Labels: published = taken from the ported code as published (Ben 5 Nov: published values count as known);
measured / derived / inferred / guessed / absent as in the fly ledger. lit_check compares the published value with
the worm literature: inside / outside / not comparable (sim units) / no literature value.
Literature values come from the literature pass in docs/worm/research/BODY_PARAMS.md and BODY.md (same sources as
the archived rod ledger, archive/worm/rod_own/). Sim units: MetaWorm's length unit is not stated; read as SI the
body is 0.628 m long, so every dimensional check below says what it assumes.
Run: .venv/bin/python scripts/worm/build_metaworm_ledger.py
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "worm" / "ledger"
VIEW = ROOT / "viewer" / "worm" / "data"

MW = "MetaWorm, BAAIWorm b99ca5ab (third_party/metaworm/sim)"
SZ = "Sznitman et al. 2010 Biophys J 98:617 (PMC2820645)"
BH = "Backholm, Ryu & Dalnoki-Veress 2013 PNAS 110:4528 (PMC3607018)"
FY = "Fang-Yen et al. 2010 PNAS 107:20323 (PMC2996704)"
BBC = "Boyle, Berri & Cohen 2012 Front Comput Neurosci 6:10 (PMC3296079)"
RB = "Rabets, Backholm, Dalnoki-Veress & Ryu 2014 Biophys J 107:1980 (PMC4213666)"
WA = "WormAtlas, Somatic muscle (hermaphrodite)"
COOK = "Cook et al. 2019 Nature 571:63"
FR24 = "Frontiers Bioeng Biotechnol 2024 (BODY.md s1)"
RE = "Reina et al. 2013 PLOS ONE 8:e69651 (BODY.md s1, measured 1.07-1.08 g/cm^3)"
GL = "Gray & Lissmann 1964 J Exp Biol 41:135; Shen et al. 2012 Biophys J 102:2772 (arXiv 1112.1118)"

# measured in this repo from the vendored mesh (driver stdout and scripts/worm/build_viewer_data.py)
VOLUME = 4.90778e-4  # sim units^3, upstream print at construction
LENGTH = 0.6276  # sim units, rest length along the long axis
MASS = 10.0
RADIUS_OVER_L = 0.0338

R = []


SI = {"kPa": 1e3, "mPa s": 1e-3}


def prior(value, lo, hi, label):
    """Fixed for published / measured / derived numbers; otherwise a guessed prior over the literature range
    (lognormal when the range spans more than 3x, centred on the geometric mean with the range = +-2 sd; else
    uniform). BodyLedger.sample(seed) draws from it, truncated to [bio_min, bio_max]."""
    num = all(isinstance(x, (int, float)) for x in (lo, hi))
    if label in ("published", "measured", "derived") or not num:
        return ("fixed", "", "", "") if label != "absent" else ("", "", "", "")
    if hi / lo > 3:
        return "lognormal", (lo * hi) ** 0.5, round(math.log(hi / lo) / 4, 4), "guessed: lognormal over the range"
    return "uniform", lo, hi, "guessed: uniform over the range"


def row(pid, mech, unit, value, lo, hi, label, source, lit_check, notes="", used=True, bound_source="",
        grain="global", applies="whole body"):
    dist, a, b, basis = prior(value, lo, hi, label)
    R.append({"param_id": pid, "mechanism_id": mech, "grain": grain, "applies_to": applies, "unit": unit,
              "bio_min": lo, "bio_max": hi, "bound_basis": "literature range" if lo != "" else "",
              "bound_source": bound_source, "prior_dist": dist, "prior_a": a, "prior_b": b, "prior_basis": basis,
              "prior_source": "", "value_fixed": value if dist == "fixed" else "", "value_used": value,
              "si_factor": SI.get(unit, 1), "label": label, "precision_needed": "",
              "precision_basis": "not computed yet (sensitivity pass pending)", "notes": notes,
              "source": source, "lit_check": lit_check, "used_in_body": "yes" if used else "no"})


# ---- MB1 geometry
row("mw_mesh_scale", "MB1", "sim units per mesh unit", 0.004, "", "", "published", MW + " Worm.cpp (worm.meta)",
    "not comparable", "body rest length 0.628 sim units (measured from the mesh); read as SI = 628 mm vs 0.9-1.2 mm")
row("mw_length", "MB1", "sim units", LENGTH, 0.9e-3, 1.2e-3, "derived", MW, "outside if SI (523x to 697x)",
    "rest length of the mesh along its long axis; literature L in m", bound_source="WormAtlas (measured, young adult)")
row("mw_radius_over_length", "MB1", "1", RADIUS_OVER_L, 0.025, 0.044, "derived", MW, "inside",
    "max radius / length of the mesh; literature: radius 30-40 um over L 0.9-1.2 mm (derived)",
    bound_source="WormAtlas; " + BBC)
row("mw_n_vertices", "MB1", "count", 984, "", "", "published", MW, "numerical", "984 vertices, 735 on the surface")
row("mw_n_tets", "MB1", "count", 3341, "", "", "published", MW, "numerical")
row("mw_n_surface_triangles", "MB1", "count", 1466, "", "", "published", MW, "numerical")

# ---- MB2 elasticity (one homogeneous material)
row("mw_youngs_modulus", "MB2", "sim units (Pa if SI)", 2e5, 3.77e3, 1.3e7, "published", MW + " Environment.cpp",
    "inside if SI", "literature spread: 3.77 kPa (Sznitman 2010), 110 kPa (Backholm 2013), ~13 MPa (derived from "
    "Fang-Yen 2010 EI = 9.5e-14 N m^2 at r = 40 um)", bound_source=f"{SZ}; {BH}; {FY}")
row("mw_poisson_ratio", "MB2", "1", 0.4, 0.45, 0.5, "published", MW + " Environment.cpp", "outside (guessed bound)",
    "no worm measurement found; a pressurised, water-filled body suggests near-incompressible (bound guessed)")
row("mw_cuticle_modulus", "MB2", "kPa", 102, 75, 140, "guessed", "placeholder inside the measured range",
    "absent in the port", "needed for a layered body (toggle body.material); value = midpoint (guessed)",
    used=False, bound_source=FR24)
row("mw_muscle_layer_modulus", "MB2", "kPa", 1120, 600, 2100, "guessed", "placeholder inside the measured range",
    "absent in the port", "geometric mean of the range (guessed)", used=False, bound_source=FR24)
row("mw_pseudocoelom_modulus", "MB2", "kPa", 108, 42, 275, "guessed", "placeholder inside the measured range",
    "absent in the port", "geometric mean of the range (guessed)", used=False, bound_source=FR24)
row("mw_internal_pressure", "MB10", "kPa", 100, 50, 200, "guessed", "placeholder inside the measured range",
    "absent in the port", "hydrostatic pressure; toggle body.pressure (geometric mean, guessed)", used=False,
    bound_source="Park 2007 PNAS; " + FR24)

# ---- MB3 muscles
row("mw_muscle_stiffness", "MB3", "sim units", 5e5, "", "", "published", MW + " Muscle.cpp", "not comparable",
    "LinearMuscleConstraint stiffness per tet, times weight exp(-d/0.005); the comparable quantity is the bend "
    "it makes: published key t0_fast gives head kappa*L 22 (measured in the sim, BODY_TESTS.md)")
row("mw_muscle_attach_length", "MB3", "sim units", 0.005, "", "", "published", MW + " Muscle.cpp",
    "not comparable", "tets within this distance of a fibre segment are driven by it (0.8% of L)")
row("mw_n_muscle_segments", "MB3", "count", 96, 95, 95, "published", MW + " worm_nerve_cord_highResCord.obj",
    "outside by one", "4 strings x 24; Cook 2019 has 95 body-wall muscles (vBWML24 does not exist): MVL segment 23 "
    "has no counterpart", bound_source=COOK + " (measured)")
row("mw_muscle_span_start", "MB3", "fraction of L", 0.033, 0.0, 0.05, "derived", MW, "inside",
    "centre of the most anterior fibre segment", bound_source=WA + " (inferred)")
row("mw_muscle_span_end", "MB3", "fraction of L", 0.957, 0.85, 0.97, "derived", MW, "inside",
    "centre of the most posterior fibre segment", bound_source=WA + " (inferred)")
row("mw_key_gain", "MB3", "1", 20, "", "", "published", MW + " Worm::SetKey", "numerical",
    "the key files are multiplied by 20 and clipped to [0, 1]")
row("mw_key_period", "MB3", "Hz", 1.5, 1.76, 1.99, "derived", MW + " (20 key rows at 30 Hz)",
    "outside (15% below the swim range)", "published keys t0_fast and turn2", bound_source="Sibernetic 2018 "
    "experimental swim table (measured), " + FY)
row("mw_key_transport_alpha", "MB3", "1", 0.3, "", "", "published", MW + " KeyWorm", "numerical",
    "head-to-tail transport of the key activation, 2 sub-steps per control step")
row("mw_force_length_width", "MB3", "strain", 0.3, 0.1, 1.0, "guessed", "placeholder", "absent in the port",
    "toggle muscle.force_model: active force x exp(-(strain/width)^2)", used=False)
row("mw_force_velocity", "MB3", "1", "", "", "", "absent", "", "absent in the port",
    "no measured C. elegans body-wall force-velocity curve found yet", used=False)

# ---- MB4 inertia
row("mw_mass", "MB4", "sim units (kg if SI)", MASS, "", "", "published", MW + " Worm.cpp", "not comparable",
    "split equally over the 984 vertices")
row("mw_density", "MB4", "kg/m^3 if SI", round(MASS / VOLUME), 1070, 1080, "derived", MW,
    "outside if SI (19x)", f"mass 10 / mesh volume {VOLUME:.4g} sim units^3", bound_source="PLOS ONE 2013 "
    "(BODY.md s1, measured)")
row("mw_damping_per_step", "MB4", "velocity factor per step", 0.9999, "", "", "published", MW + " Environment.cpp",
    "numerical", "equivalent decay rate -ln(0.9999) x 240 = 0.024 /s (derived)")
row("mw_worm_length", "MB4", "mm", 1.0, 0.9, 1.2, "published", BBC + " (model worm length)", "inside",
    "toggle body.scale = worm_1mm: 1 sim unit = 1 mm / 0.6276 = 1.593 mm (derived)", used=False)
row("mw_worm_density", "MB4", "kg/m^3", 1074, 1070, 1080, "guessed", "placeholder inside the measured range",
    "inside", "toggle body.scale = worm_1mm", used=False, bound_source=RE)
row("mw_worm_mass", "MB4", "ug", 2.13, "", "", "derived", "density x mesh volume (4.908e-4 units^3 at 1.593 mm)",
    "no literature value", "toggle body.scale = worm_1mm; spread evenly over the 984 vertices; the mass unit is "
    "1.593e-3 kg so stress and drag per length stay numerically SI", used=False)

# ---- MB5 fluid
row("mw_fluid_density", "MB5", "kg/m^3", 1000, 997, 999, "published", MW + " Worm.cpp",
    "near: 0.1-0.3% above pure water (negligible)", "bound is pure water at 20-25 C; M9 buffer not checked",
    bound_source="standard tables (measured)")
row("mw_drag_model", "MB5", "model", "quadratic: 0.5 rho A Cd(aoa) |v|^2, Cd = sin^2(aoa), plus a lift table",
    "", "", "published", MW + " Worm::SetExternalForce", "outside (wrong regime)",
    "a swimming worm is at Reynolds 0.1-0.5 (viscous, linear drag); the port runs at Re ~7,300 (measured, P3)")
row("mw_drag_force_cap", "MB5", "sim units per face", 1e3, "", "", "published", MW, "numerical")
row("mw_lift_table_x", "MB5", "deg", "-90,-10,-5,15,90", "", "", "published", MW, "no literature value")
row("mw_lift_table_y", "MB5", "1", "-0.5,-1.26,0,1.8,0.5", "", "", "published", MW, "no literature value")
row("mw_water_viscosity", "MB5", "mPa s", 1.1, 1.0, 1.1, "measured", SZ, "absent in the port",
    "M9 buffer; for toggle env.fluid = viscous_rft_water", used=False)
row("mw_water_Ct", "MB5", "Pa s", 0.00357, "", "", "derived", "Lighthill slender body (as in " + BBC + ")",
    "absent in the port", "2 pi mu / ln(2 q / a), mu 1.1 mPa s, q = 0.09 x 1.54 mm, a = 40 um", used=False)
row("mw_water_Cn", "MB5", "Pa s", 0.005675, "", "", "derived", "Lighthill slender body (as in " + BBC + ")",
    "absent in the port", "4 pi mu / (ln(2 q / a) + 0.5); Cn/Ct = 1.59", used=False)
row("mw_agar_Ct", "MB5", "Pa s", 3.2, 1.0, 10.0, "inferred", BBC, "absent in the port",
    "for toggle env.fluid = agar_rft; BBC quote kg/s, read per body length", used=False)
row("mw_agar_Cn", "MB5", "Pa s", 128.0, 14.0, 352.0, "inferred", BBC, "absent in the port",
    "K = Cn/Ct = 40 (BBC); Rabets 2014 measure K 1.4 in gels (row mw_agar_K_rabets)", used=False)
row("mw_agar_K_rabets", "MB5", "1", 1.4, 1.2, 1.6, "measured", RB, "absent in the port",
    "alternative agar anisotropy", used=False)

# ---- MB6 gravity and substrate
row("mw_gravity", "MB6", "m/s^2", 9.81, 9.78, 9.83, "measured", "standard", "absent in the port",
    "no gravity in the published world (the body floats and tumbles in 3D); toggle env.substrate = agar_plate|"
    "agar_film: toward the plate, about 1000x weaker than the elastic forces (derived)", used=False)
row("mw_side_down", "MB6", "side", "right", "", "", "guessed", "worms crawl on either side", "no literature value",
    "toggle env.substrate: which side lies on the plate (--side_down right|left)", used=False)
row("mw_plate_contact", "MB6", "model", "one-sided plane at the rest body's lowest point; vertices put back on it, "
    "velocity into it zeroed", "", "", "guessed", "this repo", "no literature value",
    "toggle env.substrate = agar_plate; no friction beyond the agar drag. Alone it fails gate A2: the body pitches "
    "up and lifts off (BODY_TESTS.md)", used=False)
row("mw_film_surface", "MB6", "fraction of L", 0.0601, "", "", "derived", "rest mesh thickness across the plate",
    "60 um at 1 mm; adult diameter about 50-80 um", "toggle env.substrate = agar_film: the water film's surface as a "
    "hard wall at this height (form guessed); stands for the meniscus that holds a worm on agar", used=False,
    bound_source=GL)
row("mw_surface_tension", "MB6", "N/m", 0.072, 0.070, 0.073, "measured", "standard tables (water, 20-35 C)",
    "no value in the port", "only sets the order of the hold-down force: 0.072 N/m x 1 mm is about 7e-5 N, about "
    "3000x the weight (derived); the film wall treats it as infinite", used=False, bound_source=GL)

# ---- MB9 numerics
row("mw_dt", "MB9", "s", 1 / 240, "", "", "published", MW + " Environment.cpp", "numerical",
    "hard-coded 240 Hz; a time-step check needs an upstream edit")
row("mw_iterations", "MB9", "count", 50, "", "", "published", MW, "numerical", "local/global iterations per step")
row("mw_convergence_eps", "MB9", "1", 5e-7, "", "", "published", MW + " fem/World.cpp", "numerical")
row("mw_control_hz", "MB9", "Hz", 30, "", "", "published", MW + " Environment.cpp", "numerical",
    "muscle input rate; 8 physics steps per control step")

SW = lambda name, options, available, neutral, by_mode=None: {  # noqa: E731
    "name": name, "options": options, "available": available, "neutral": neutral,
    **({"current_by_mode": by_mode} if by_mode else {})}

MECH = {
    "title": "Body mechanisms of the ported MetaWorm body (data/worm/ledger/metaworm_mechanisms.json)",
    "mechanisms": [
        {"id": "MB1", "name": "3D tetrahedral body (984 vertices, 3341 tets), MetaWorm mesh", "status": "have",
         "source": MW, "switch": []},
        {"id": "MB2", "name": "elastic tissue: corotated linear FEM, one homogeneous material", "status": "partial",
         "notes": "E inside the literature range if SI; Poisson 0.4; no cuticle / muscle / pseudocoelom layers",
         "source": MW, "switch": [SW("body.material", ["homogeneous_published", "layered"], ["homogeneous_published"],
                                     "homogeneous_published")]},
        {"id": "MB3", "name": "body-wall muscles: 96 linear fibre segments in 4 quadrants", "status": "partial",
         "notes": "95 Cook muscles + one extra (MVL24); no force-length or force-velocity", "source": MW,
         "switch": [SW("muscle.force_model", ["linear_published", "force_length"], ["linear_published"],
                       "linear_published")]},
        {"id": "MB4", "name": "inertia: mass 10 over the 0.63-unit body, numerical damping", "status": "partial",
         "notes": "density 19x a worm if read as SI; metre-scale world. worm_1mm (built, 5 Nov): 1 mm body, "
                  "density 1074 kg/m^3, mass 2.13 ug; needs an RFT fluid", "source": MW + "; this repo",
         "switch": [SW("body.scale", ["published", "worm_1mm"], ["published", "worm_1mm"], "published")]},
        {"id": "MB5", "name": "fluid: quadratic drag and lift per surface triangle", "status": "partial",
         "notes": "inertial regime (Re ~7,300) vs a worm's 0.1-0.5; viscous resistive-force drag is the "
                  "literature replacement. Built 5 Nov: RFT drag in the implicit solve (World::SetDragMatrix), "
                  "agar K 40 (BBC 2012) stable at the published step; water RFT built, not scored",
         "source": MW + "; " + BBC,
         "switch": [SW("env.fluid", ["quadratic_published", "viscous_rft_water", "agar_rft"],
                       ["quadratic_published", "viscous_rft_water", "agar_rft"], "quadratic_published")]},
        {"id": "MB6", "name": "gravity and substrate contact (agar plate)", "status": "partial",
         "notes": "the published world has neither. agar_plate (gravity only) fails gate A2: the body lifts off. "
                  "agar_film (the water film's surface as a wall) passes A1f and A2f; not adopted (BODY_TESTS.md)",
         "source": "this repo; " + GL,
         "switch": [SW("env.substrate", ["none_published", "agar_plate", "agar_film"],
                       ["none_published", "agar_plate", "agar_film"], "none_published")]},
        {"id": "MB7", "name": "drive source", "status": "have",
         "notes": "closed loop with brain.py runs (src/wormemu/body/loop.py, pipe mode; 5 Nov: 3 s, bounded, "
                  "drive 4.4e-6 so the body does not move)", "source": MW + "; this repo",
         "switch": [SW("drive.source", ["key_published", "prescribed_wave", "dead", "brain_closed_loop"],
                       ["key_published", "prescribed_wave", "dead", "brain_closed_loop"], "key_published",
                       {"key": "key_published", "wave": "prescribed_wave", "dead": "dead",
                        "pipe": "brain_closed_loop"})]},
        {"id": "MB8", "name": "proprioceptive outputs to the brain (curvature, rate, strain)", "status": "partial",
         "notes": "curvature and its rate at 49 points streamed to the brain every exchange (loop.py); "
                  "strain, contact and nose force sent as 0",
         "source": "this repo", "switch": []},
        {"id": "MB9", "name": "numerics: projective dynamics, 240 Hz, 50 iterations", "status": "have",
         "notes": "published exit returns the iterate before the converged solve: drive below ~0.05 does not "
                  "move a body at rest (BODY_TESTS.md); 'latest' keeps the converged solve, not yet adopted",
         "source": MW, "switch": [SW("body.solver_exit", ["published", "latest"], ["published", "latest"],
                                     "published")]},
        {"id": "MB10", "name": "hydrostatic pressure", "status": "missing", "source": "",
         "switch": [SW("body.pressure", ["none_published", "pressurised"], ["none_published"], "none_published")]},
        {"id": "MB11", "name": "chemical gradient scene (BAAIWorm chemotaxis)", "status": "partial",
         "notes": "field sampled at the nose and tail (src/wormemu/body/scene.py); plate physics is the MB6 toggle "
                  "(agar_film passes its gates, not adopted, not yet run with the field); "
                  "values in docs/worm/research/CHEMOTAXIS_PLATE.md", "source": "BAAIWorm b99ca5ab; literature",
         "switch": [SW("env.chemical_field", ["none", "cone_published", "exp_spot"],
                       ["none", "cone_published", "exp_spot"], "none"),
                    SW("env.chemical_target", ["published_3d", "plate_projected"],
                       ["published_3d", "plate_projected"], "plate_projected")]},
        {"id": "MB12", "name": "pharynx, egg-laying and defecation body parts", "status": "missing",
         "notes": "the interface carries their activations; the body has no parts for them yet", "source": "",
         "switch": []},
    ],
}


def catalog_rows():
    rows = [{"id": r["param_id"], "mechanism": r["mechanism_id"], "value": r["value_used"], "unit": r["unit"],
             "min": r["bio_min"], "max": r["bio_max"], "label": r["label"], "precision": r["precision_needed"],
             "source": "; ".join(x for x in (r["source"], r["bound_source"]) if x),
             "lit_check": r["lit_check"],
             "notes": " ".join(x for x in ("" if r["used_in_body"] == "yes" else "(not used by the running body)",
                                           r["notes"]) if x), "origin": "body"} for r in R]
    brain = ROOT / "docs" / "worm" / "ledger.json"
    if brain.exists():  # the brain worker's export; field names mapped best effort
        led = json.load(open(brain))
        for p in led.get("parameters", led.get("rows", [])):
            rows.append({"id": p.get("param_id", p.get("id")), "mechanism": p.get("mechanism_id", p.get("mechanism")),
                         "value": p.get("value_used", p.get("value")), "unit": p.get("unit"),
                         "min": p.get("bio_min", p.get("min")), "max": p.get("bio_max", p.get("max")),
                         "label": p.get("label"), "precision": p.get("precision_needed", ""),
                         "source": p.get("bound_source", p.get("source", "")), "notes": p.get("notes", ""),
                         "lit_check": p.get("lit_check", ""),
                         "origin": "brain"})
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    VIEW.mkdir(parents=True, exist_ok=True)
    with open(OUT / "metaworm_parameters.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    json.dump(MECH, open(OUT / "metaworm_mechanisms.json", "w"), indent=1)
    json.dump(MECH, open(VIEW / "mechanisms.json", "w"), indent=1)
    rows = catalog_rows()
    json.dump({"rows": rows}, open(VIEW / "catalog.json", "w"), indent=1)
    n_used = sum(r["used_in_body"] == "yes" for r in R)
    print(f"{len(R)} body rows ({n_used} used by the running body), {len(MECH['mechanisms'])} mechanisms, "
          f"catalog {len(rows)} rows")


if __name__ == "__main__":
    main()
