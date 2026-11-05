"""Write the body rows of the worm ledger and the body mechanism list.

Outputs data/worm/ledger/body_parameters.csv (fly parameters.csv columns + si_factor + precision_needed) and
data/worm/ledger/body_mechanisms.json. Every body number in src/wormemu/body comes from here. Derived rows show
their arithmetic in `notes`. Sources: docs/worm/research/BODY_PARAMS.md (literature pass 2026-11-05) and
docs/worm/research/BODY.md. precision_needed is filled by scripts/worm/body_sensitivity.py (kept on rebuild).
Run: .venv/bin/python scripts/worm/build_body_ledger.py
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "worm" / "ledger"
OUT.mkdir(parents=True, exist_ok=True)

BBC = "Boyle, Berri & Cohen 2012 Front Comput Neurosci 6:10 (PMC3296079)"
FY = "Fang-Yen et al. 2010 PNAS 107:20323 (PMC2996704)"
BH = "Backholm, Ryu & Dalnoki-Veress 2013 PNAS 110:4528 (PMC3607018)"
SZ = "Sznitman et al. 2010 Biophys J 98:617 (PMC2820645)"
RB = "Rabets, Backholm, Dalnoki-Veress & Ryu 2014 Biophys J 107:1980 (PMC4213666)"
WA = "WormAtlas, Somatic muscle (hermaphrodite)"
WEN = "Wen et al. 2012 Neuron 76:750"

# derived numbers, arithmetic kept here and echoed into notes
r_max = 40e-6
I_mid = math.pi * r_max ** 4 / 4  # 2.01e-18 m^4
EI_backholm = 110e3 * I_mid  # 2.21e-13 N m^2
EI_backholm_hi = 140e3 * I_mid
mu_m9 = 1.1e-3
q_frac, lam_swim = 0.09, 1.54e-3
lg = math.log(2 * q_frac * lam_swim / r_max)
Ct_w = 2 * math.pi * mu_m9 / lg
Cn_w = 4 * math.pi * mu_m9 / (lg + 0.5)
EI_fy = 9.5e-14
kappa_deep = 15e3  # 1/m, deep body bends kappa*L ~ 15 (guessed)
M0 = EI_fy * kappa_deep

R = []


def row(pid, mech, unit, value, lo, hi, label, bound_basis, bound_source, prior=("fixed", "", ""), fixed=True,
        si=1.0, grain="global", applies="whole body", prior_basis="", prior_source="", notes=""):
    R.append({
        "param_id": pid, "mechanism_id": mech, "grain": grain, "applies_to": applies, "unit": unit,
        "bio_min": lo, "bio_max": hi, "bound_basis": bound_basis, "bound_source": bound_source,
        "prior_dist": prior[0], "prior_a": prior[1], "prior_b": prior[2], "prior_basis": prior_basis,
        "prior_source": prior_source, "value_fixed": value if fixed else "", "value_used": value,
        "si_factor": si, "label": label, "precision_needed": "", "precision_basis": "", "notes": notes})


# ---- WB1 geometry and bending elasticity
row("wb1_length", "WB1", "mm", 1.0, 0.9, 1.2, "measured", "measured range, young adult hermaphrodite",
    "WormAtlas introduction; BODY.md s1 (about 1 mm)", si=1e-3, prior=("normal", 1.0, 0.07), fixed=False,
    prior_basis="centre of the young-adult range", notes="BBC 2012 also use L = 1 mm")
row("wb1_radius_max", "WB1", "um", 40, 30, 40, "measured", "mid-body diameter 60-80 um", "WormAtlas; BBC 2012",
    si=1e-6, prior=("uniform", 30, 40), fixed=False, prior_basis="measured diameter range")
row("wb1_radius_end_offset", "WB1", "BBC segments", 0.2, 0.0, 1.0, "inferred", "shape constant of BBC eq. 2",
    BBC, notes="R(s) = Rmax sin(acos((s - L/2)/(L/2 + e))), e in units of L/48; taper to a point at head and tail")
row("wb1_bending_stiffness", "WB1", "N m^2", EI_fy, 4.19e-16, round(EI_backholm_hi, 16), "measured",
    "spread of whole-body methods: Sznitman 2010 swim fit (4.19e-16) to Backholm 2013 cantilever 140 kPa (derived)",
    f"{FY} (b = 9.5 +/- 1.0 e-14, gait vs viscosity fit); {SZ}; {BH}",
    prior=("lognormal", EI_fy, 0.5), fixed=False, prior_basis="Fang-Yen 2010 is the locomotion-matched method",
    prior_source=FY,
    notes=(f"EI at mid-body. Backholm E = 110 kPa at r = 40 um gives EI = E pi r^4/4 = {EI_backholm:.3g} N m^2 "
           f"(derived); Fang-Yen b corresponds to E = {EI_fy / I_mid / 1e3:.0f} kPa (derived). Sources disagree by "
           "~500x (method-dependent, BODY_PARAMS.md s3, s7): unreconciled"))
row("wb1_EI_radius_exponent", "WB1", "1", 4.0, 3.8, 4.2, "measured", "fit exponent 4.02 of EI vs diameter",
    f"{BH} Fig. 4", notes="EI(s) = EI_mid (r(s)/r_max)^4")

# ---- WB2 internal damping
row("wb2_bending_viscosity", "WB2", "N m^2 s", 2.5e-16, 0.0, 5e-16, "guessed",
    "measured upper bound: internal viscous forces >= 100x below elastic", f"{FY}",
    prior=("uniform", 0.0, 5e-16), fixed=False, prior_basis="no value, only an upper bound; centre of [0, bound]",
    notes="Kelvin-Voigt bending viscosity at mid-body, scaled like EI. Backholm 2013 measured shear-thinning "
          "(power-law) damping on anaesthetised worms: not represented (mechanism WB15 absent)")

# ---- WB3 environment drag
row("wb3_water_viscosity", "WB3", "mPa s", 1.1, 1.0, 1.1, "measured", "M9 buffer", SZ, si=1e-3)
row("wb3_lighthill_q_fraction", "WB3", "1", q_frac, 0.05, 0.15, "inferred", "Lighthill 1976 slender-body length scale",
    BBC + " eq. 1")
row("wb3_swim_wavelength_ref", "WB3", "mm", 1.54, 1.50, 1.58, "measured", "swim wavelength (for the log term)",
    FY + " Table 1", si=1e-3)
row("wb3_water_Ct", "WB3", "Pa s", round(Ct_w, 6), "", "", "derived", "", "",
    notes=f"2 pi mu / ln(2 q / a), mu = 1.1 mPa s, q = 0.09 x 1.54 mm, a = 40 um: ln = {lg:.3f}. Computed in code "
          "from the rows above; listed for reference")
row("wb3_water_Cn", "WB3", "Pa s", round(Cn_w, 6), "", "", "derived", "", "",
    notes=f"4 pi mu / (ln(2 q / a) + 0.5); K = Cn/Ct = {Cn_w / Ct_w:.2f}. Computed in code")
row("wb3_agar_Ct", "WB3", "Pa s", 3.2, 1.0, 10.0, "inferred", "order-of-magnitude spread, guessed",
    f"{BBC} (C_par = 3.2e-3 kg/s, from Wallace 1968 via Niebur & Erdos 1991)",
    notes="BBC quote kg/s; read as per body length (1 mm), so 3.2 Pa s per unit length (inferred, unit convention "
          "under check). Rabets 2014 found agar drag is a power law in speed, not linear")
row("wb3_agar_Cn", "WB3", "Pa s", 128.0, 14.0, 352.0, "inferred",
    "anisotropy K spread 1.5-110 across studies (BODY.md s2) times C_t; Rabets 2014 direct K 1.4",
    f"{BBC} (C_perp = 128e-3 kg/s, estimated from Berri 2009)", notes="K = 40 with the C_t row")
row("wb3_agar_K_rabets", "WB3", "1", 1.4, 1.2, 1.6, "measured", "direct cantilever drag, high speed (> 500 um/s)",
    RB + " Fig. 2 inset (1.4 +/- 0.2)",
    notes="toggle env.agar_drag = rabets_K1p4. At crawl speeds their power-law fits give an effective K ~ 5 at "
          "1.7% agar (derived from their alpha, gamma; units of alpha unresolved)")

# ---- WB4 muscle layout
row("wb4_muscle_s_start", "WB4", "fraction of L", 0.02, 0.0, 0.05, "inferred",
    "head muscles start just behind the lips", WA, applies="95 body-wall muscles")
row("wb4_muscle_s_end", "WB4", "fraction of L", 0.92, 0.85, 0.97, "inferred",
    "most posterior body-wall muscles in the tail, behind the anus", WA, applies="95 body-wall muscles")
row("wb4_edge_taper", "WB4", "1", 0.3, 0.0, 1.0, "guessed", "shape of each cell's coverage", "",
    applies="95 body-wall muscles", notes="cosine taper over the outer 30% of each cell's half-length")

# ---- WB5 excitation-contraction
row("wb5_tau_activation", "WB5", "ms", 100, 30, 300, "inferred", "guessed bounds around the modelled value",
    BBC + " Table 3 (tau_M = 100 ms)", si=1e-3, prior=("lognormal", 100, 0.4), fixed=False,
    applies="95 body-wall muscles", notes="first-order activation and relaxation, same constant (a simplification)")
row("wb5_ca_half_activation", "WB5", "uM", 0.5, 0.1, 5.0, "guessed", "typical striated-muscle troponin range", "",
    si=1e-6, applies="95 body-wall muscles", notes="only with toggle muscle.input = calcium_hill")
row("wb5_ca_hill_n", "WB5", "1", 2.0, 1.0, 4.0, "guessed", "typical Hill coefficients", "",
    applies="95 body-wall muscles", notes="only with toggle muscle.input = calcium_hill")

# ---- WB6 muscle force
row("wb6_max_moment", "WB6", "N m", f"{M0:.3g}", 3e-10, 5e-9, "guessed",
    "no absolute muscle force found (BODY_PARAMS.md s6); bounds guessed", "",
    prior=("lognormal", M0, 0.5), fixed=False, applies="95 body-wall muscles",
    notes=f"full dorsal contraction bends mid-body to kappa = M0/EI = 15 /mm (kappa L ~ 15, deep bends; "
          f"guessed): M0 = 9.5e-14 x 1.5e4 = {M0:.3g}")
row("wb6_moment_radius_exponent", "WB6", "1", 4.0, 2.0, 4.0, "guessed",
    "neutral: equal to the EI exponent, so a given drive gives the same curvature everywhere; any head-to-tail "
    "profile then comes from the drive or the muscle.force_gradient toggle", "", applies="95 body-wall muscles",
    notes="Mmax(s) = M0 (r(s)/r_max)^p. Revised 2026-11-05 from 2 (force ~ cross-section, lever ~ r) after "
          "gait test v1: p = 2 gave a head-tip curvature of 42 /mm (bend radius 24 um, about one body radius). "
          "Not fitted to speed; BODY_TESTS.md v1/v2")
row("wb6_bbc_head_tail_ratio", "WB6", "1", 2.5, 1.0, 3.0, "inferred", "BBC model choice", BBC,
    applies="95 body-wall muscles", notes="toggle muscle.force_gradient = bbc_head_to_tail")
row("wb6_force_length_width", "WB6", "strain", 0.3, 0.1, 1.0, "guessed", "", "", applies="95 body-wall muscles",
    notes="toggle muscle.force_length = gaussian: force x exp(-(strain/width)^2)")

# ---- WB7 proprioceptive readout
row("wb7_muscle_radius_fraction", "WB7", "1", 0.9, 0.8, 1.0, "inferred", "muscles lie just under the hypodermis",
    WA, notes="fibre strain = -kappa x 0.9 r(s) on the dorsal side")
row("wb7_proprio_field_length", "WB7", "um", 200, 100, 300, "inferred", "", WEN + " (l ~ 200 um, Fig. 3D)",
    si=1e-6, applies="B-type motor neurons", notes="for the brain side: receptive field posterior to each "
          "B-type neuron. Listed here because it is a body-coordinate quantity; the brain worker owns its use")
row("wb7_atlas_y_nose", "WB7", "um", -330, -340, -315, "inferred", "nose tip in OpenWorm atlas coordinates",
    "OpenWorm CElegansNeuroML soma positions (most anterior soma I2L at -311.65)", applies="neuron placement",
    notes="maps neuron atlas y onto body arclength for drawing and for sensory/proprioceptive sampling")
row("wb7_atlas_y_tail", "WB7", "um", 480, 430, 520, "inferred", "tail tip in OpenWorm atlas coordinates",
    "most posterior soma PLMR at 410.15", applies="neuron placement")

# ---- reported, not used by the overdamped rod
row("wb12_mass_density", "WB12", "g/cm^3", 1.07, 1.07, 1.08, "measured", "density-gradient centrifugation",
    "PLOS ONE 2013 (BODY.md s1)", notes="unused: Re << 1 so inertia is dropped (validity check only)")
row("wb10_internal_pressure", "WB10", "kPa", "", 50, 200, "absent", "sources unreconciled (BODY.md s1)",
    "Park 2007 PNAS; Frontiers 2024", notes="needed by the 3D body; not in the rod")
row("wb10_cuticle_modulus", "WB10", "kPa", "", 75, 140, "absent", "layer-resolved FE inversion",
    "Frontiers Bioeng Biotechnol 2024 (BODY.md s1)", notes="needed by the 3D body")
row("wb10_muscle_layer_modulus", "WB10", "kPa", "", 600, 2100, "absent", "layer-resolved FE inversion",
    "Frontiers Bioeng Biotechnol 2024", notes="needed by the 3D body")
row("wb10_pseudocoelom_modulus", "WB10", "kPa", "", 42, 275, "absent", "layer-resolved FE inversion",
    "Frontiers Bioeng Biotechnol 2024", notes="needed by the 3D body")

# keep precision columns from a previous sensitivity run
path = OUT / "body_parameters.csv"
old = {}
if path.exists():
    with open(path) as fh:
        old = {r["param_id"]: r for r in csv.DictReader(fh)}
for r in R:
    o = old.get(r["param_id"])
    if o and o.get("precision_needed"):
        r["precision_needed"], r["precision_basis"] = o["precision_needed"], o["precision_basis"]

cols = list(R[0].keys())
with open(path, "w", newline="") as fh:
    w = csv.DictWriter(fh, cols)
    w.writeheader()
    w.writerows(R)

MECH = [
    {"id": "WB1", "name": "planar inextensible rod, bending elasticity EI(s) ~ r^4, BBC radius taper",
     "status": "have", "switch": [], "neutral": None, "test": ["tests/worm/test_body.py::test_dead_worm"]},
    {"id": "WB2", "name": "internal bending viscosity (Kelvin-Voigt)", "status": "have",
     "switch": ["body.internal_damping"], "neutral": "kelvin_voigt", "options": ["kelvin_voigt", "off"],
     "test": []},
    {"id": "WB3", "name": "resistive-force drag: water/buffer (Lighthill), any Newtonian viscosity, agar",
     "status": "have", "switch": ["env.agar_drag"], "neutral": "wallace_K40",
     "options": ["wallace_K40", "rabets_K1p4"], "test": ["tests/worm/test_body.py::test_gait"],
     "notes": "agar anisotropy is a live disagreement (K 40 vs 1.4): kept as two possible worlds"},
    {"id": "WB4", "name": "95 body-wall muscles in 4 quadrants (24/24/23/24), overlapping cells", "status": "have",
     "switch": [], "neutral": None, "test": ["tests/worm/test_body.py::test_muscle_count"]},
    {"id": "WB5", "name": "excitation-contraction: first-order activation; optional Ca -> force Hill",
     "status": "partial", "switch": ["muscle.input"], "neutral": "activation",
     "options": ["activation", "calcium_hill"], "test": []},
    {"id": "WB6", "name": "muscle force: max moment, head-to-tail profile, optional force-length",
     "status": "partial", "switch": ["muscle.force_gradient", "muscle.force_length"],
     "neutral": "radius_scaled / off", "options": ["radius_scaled|bbc_head_to_tail", "off|gaussian"], "test": [],
     "notes": "absolute force unmeasured (guessed); no force-velocity"},
    {"id": "WB7", "name": "proprioceptive readout: per-muscle fibre strain, per-joint curvature", "status": "have",
     "switch": [], "neutral": None, "test": ["tests/worm/test_body.py::test_stretch_sign"]},
    {"id": "WB8", "name": "3D Cosserat rod (twist, roll, out-of-plane bends; Denham-Ranner-Cohen 2018)",
     "status": "absent", "switch": [], "neutral": None, "test": [],
     "notes": "needed for 3D burrowing and roll manoeuvres (PNAS 2017)"},
    {"id": "WB9", "name": "3D continuum body (MetaWorm projective dynamics tet mesh / Sibernetic SPH)",
     "status": "partial", "switch": [], "neutral": None, "test": [],
     "notes": "3D surface is drawn from the rod (visual only); continuum physics not built"},
    {"id": "WB10", "name": "hydrostatic skeleton: internal pressure, layered cuticle/muscle/pseudocoelom",
     "status": "absent", "switch": [], "neutral": None, "test": []},
    {"id": "WB11", "name": "self-contact (omega turns, coiling)", "status": "absent", "switch": [],
     "neutral": None, "test": []},
    {"id": "WB12", "name": "inertia", "status": "absent", "switch": [], "neutral": None, "test": [],
     "notes": "dropped on purpose: Re 0.1-0.4 in water, far lower on agar"},
    {"id": "WB13", "name": "sensory world: chemical and thermal fields at the nose, touch, food lawn, O2/CO2",
     "status": "partial", "switch": [], "neutral": None, "test": [],
     "notes": "head position/heading and touch events exported; fields not built"},
    {"id": "WB14", "name": "nonlinear (power-law) substrate drag on agar (Rabets 2014)", "status": "absent",
     "switch": [], "neutral": None, "test": [], "notes": "units of the published fit prefactors unresolved"},
    {"id": "WB15", "name": "shear-thinning viscoelastic body (Backholm 2013 power-law damping)",
     "status": "absent", "switch": [], "neutral": None, "test": []},
    {"id": "WB16", "name": "non-locomotor mechanics: pharyngeal pumping, egg-laying, defecation (pBoc/aBoc/Exp)",
     "status": "absent", "switch": [], "neutral": None, "test": []},
]
json.dump({"numerics": {"n_seg": 48, "dt_s": 1e-3, "dt_fluid_s": 1.25e-4,
                        "n_seg_basis": "BBC 2012 use 48 segments (numerical choice)",
                        "dt_basis": "first-order linearly implicit step. Agar: 1 ms vs 0.25 ms changes speed 0.2%. "
                                    "Water relaxes in ~0.2 ms, so 1 ms is 8% off the converged swim speed; "
                                    "0.125 ms is ~1% off (BODY_TESTS.md numerics)"},
           "mechanisms": MECH}, open(OUT / "body_mechanisms.json", "w"), indent=1)
print(f"{len(R)} body rows, {len(MECH)} body mechanisms")
print(f"water Ct {Ct_w:.3g} Cn {Cn_w:.3g} Pa s; EI Backholm {EI_backholm:.3g}; M0 {M0:.3g}")
