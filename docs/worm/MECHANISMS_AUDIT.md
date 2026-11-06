# Worm mechanisms audit: PLAN.md rows 1-23 (2026-11-05 18:08 CST)

Written for Thursday's bar. One line per row of the PLAN.md layer table. It records what the code does today, not
what the ledger rows or plans say. Brain code is on main at ce5abe7. Body code is on the body worker's branch
(`worktree-wormbody` at a12ded3, `.claude/worktrees/wormbody/src/wormemu/body/`) and is not merged to main yet.

**The four categories (strict):**

- **full**: the mechanism runs in the model at the level PLAN.md asks for, as a published mechanistic model.
  Parameter quality is a separate question (the ledger's labels answer it).
- **lumped**: real dynamics that act on a run, but simpler than PLAN.md asks: fewer states, a timer in place of a
  circuit, one value shared where the plan wants one per class.
- **spec only**: ledger rows, or code that holds a state, but nothing with dynamics changes a run. A constant
  multiplier counts as spec only, and so does a state that nothing reads.
- **missing**: nothing in the code.

"Exercised" means a test or a run had the mechanism switched on. "Checked" means that run or test scored its
output against a bar. Most layers ran in some closed loop without anyone checking what they did; the column says so.

Short names used below: `layers` = `src/wormemu/brain_layers.py`, class `Layers`; `brain` = `src/wormemu/brain.py`,
class `Brain`; `body/` = the body worker's `src/wormemu/body/`. "Port runs" = BRAIN_PORT sections 1-8 (ref,
port302a-c, D0-D8, S01-S19, M1-M4, R1-R3, C1, C2, the section 8 screen). The D and S runs had every lumped layer
off (`scripts/worm/port/brain_runs.py`); the closed loops C1, C2 and section 8 ran with the ledger defaults plus
receptor_sign on, on the published body with the diacetyl cone field.

Ledger counts come from `docs/worm/ledger.json` (368 brain rows, 90,112 numbers) and the body ledger
`data/worm/ledger/metaworm_parameters.csv` on the body branch (48 rows, one number each). All counts measured
from those files today. Label splits are per element, as the ledger counts them (corrected 18:23: rows 5, 7 and
12 first gave the row labels, which hide the elements that literature clipping or a per-pair source relabels).

## The table

| # | PLAN row | Implemented | File and function | Toggle (default) | Ledger rows, numbers (labels) | Exercised by | Main simplification |
|---|---|---|---|---|---|---|---|
| 1 | Cell inventory | **full** for 302 neurons and 95 body-wall muscles; **missing** for the other 37 muscles (pharyngeal, vulval, uterine, anal), 26 end organs and 56 glia | `brain_structure.load_structure` (Cook 2019 cell list); `brain.Brain.__init__` builds 397 cells | none (always on) | no rows of its own (structure files) | every test and port run | 397 of the 460 Cook nodes are cells (derived: 302 + 95). The rest exist only as names in the wiring. |
| 2 | Morphology and compartments | **full** | `brain.Brain.__init__`, `brain._segments` (BAAIWorm hoc cells, segments by length) | none (on) | 2 rows, 64,408 (derived) | every test and port run; section 3 R1: our reference run matched the BAAIWorm port within 0.0 mV | One BAAIWorm reconstruction per cell, not EM skeletons. Compartments are one segment per 2 um, BAAIWorm's setting; BRAIN_PORT records no convergence check. |
| 3 | Channel presence per class (CeNGEN) | **full**, off by default | `brain.Brain._density` with the `expression_map` mask (CeNGEN threshold 2) | expression_map (off) | 0 rows (reads the CeNGEN table) | section 8 runs E1, E2 (more neurons tonic, 137 vs 109 above -20 mV; no rhythm) | A channel is removed where CeNGEN does not detect its gene, and given the class-median density where the gene is detected but BAAIWorm had none. Only BAAIWorm's 16 channel models (14 genes) can be switched; CeNGEN genes outside that set have no model. Threshold 2 is a choice (inferred). |
| 4 | Channel kinetics | **full** | `brain.Brain._kinetics`, `_biophysics` (BAAIWorm .mod files) | none (on) | 171 rows, 171 (published fit), one set per gene | every test and port run | BAAIWorm's 16 channel models (14 genes), not PLAN's Nicoletti 22-channel library. The Nicoletti ports (`src/wormemu/nicoletti.py`) are used only by the parked W1 RIM/AFD fit, not by the 302-cell brain. |
| 5 | Channel densities, Cm, leak, Ra | **full** (values as published, not refit) | `brain.Brain._density`, `_cell_param`, `_biophysics`, `_ions` | literature_overrides (on): clips BAAIWorm values that fall outside a literature range (cm, leak reversal, Ra and others) | 16 density rows, 4,832 (published fit) + 8 passive rows, 2,416 (1,710 published fit, 706 guessed where the literature range clipped them) + 4 ion rows, 4 (guessed) | every test and port run; section 5 S01-S19 moved the range ends | BAAIWorm's per-cell fit used as is. PLAN wants one fitted value per class, checked against our ephys; no class has been refit yet (W1 is parked). |
| 6 | Calcium handling | **full** | BAAIWorm nanodomain and pool .mod files, set in `brain.Brain._biophysics` | none (on) | 10 rows, 10 (9 published fit, 1 guessed) | every test and port run | One bulk pool per compartment; buffering is folded into the pool's time constant. |
| 7 | Chemical synapses | **lumped** (counts and graded release are full; receptor kinetics are not) | `brain.Brain._wire_cook`, `_syn`, `_inhibitory`, `_g_syn` | wiring (cook); sign_rule (transmitter); receptor_sign (off) | 36 rows, 15,281: wiring 24 rows, 11,260 (5,852 measured EM counts, 743 published fit, 4,665 guessed per-pair strengths); syn_sign 302 (282 derived, 15 guessed, 5 inferred); receptor_sign 3,709 (1,703 derived from Fenyves, 1,997 guessed, 9 measured since BRAIN_PORT 9); release 10 | every port run; D0-D8 diagnosed the saturation (wiring, scaling, sign rules); receptor_sign on in D5, D8, C1, C2 and section 8 | Two synapse types only (one excitatory, one inhibitory), not one per receptor class. Every pair's strength is the same guessed template (0.447 nS per EM synapse, the range log-midpoint) times its EM count, not a fitted unit conductance per transmitter and receptor class. |
| 8 | Gap junctions per innexin | **full** for the plan's parts, but those parts are off by default | `brain.Brain._wire_cook`, `_gap`; our `src/wormemu/nmodl/rectgap.mod` | innexin_identity (off); gap_rectification (off) | 6 rows, 2,186: gap 1,092 (guessed); innexin_identity 1,093 (1,091 derived, 2 guessed); rectification 1 (inferred). The 1,091 measured gap counts sit in row 7's wiring | every port run (plain gaps); test_gap_rectification, R1-R3, C2; innexin_identity in test_small_brain | The default run gives every junction one guessed conductance times its count. Innexin conductances are guessed. Rectification covers only the 86 AVA/AVB/AVD/AVE/PVC to motor neuron pairs, as a fixed direction ratio with no voltage gating. |
| 9 | Neuropeptides | **lumped**, never run | `layers.modulator_current` | peptides (off) | 5 rows, 194 (guessed) | none. No test, no port run | One well-mixed concentration per peptide for the whole body (PLAN: per body region). Release is a sigmoid of voltage, clearance first order, and the receptor injects a current directly, with no G-protein or channel coupling. |
| 10 | Monoamines | **lumped**, never run | `layers.modulator_current` | monoamines (off) | 5 rows, 34 (guessed) | none | As row 9: one well-mixed pool per amine, receptor occupancy turned straight into a current. |
| 11 | Glia | **spec only** | `layers.sensory_current` multiplies amphid sensory currents by `glia_gain` | glia (off) | 1 row, 1 (guessed) | none in the worm (the glia tests in `tests/` are the fly's) | A constant multiplier with no state: no glial cells, no K+ or Cl- handling. |
| 12 | Body-wall muscle and excitation-contraction | **lumped** (Ca and force); the active membrane is **full** (c302) but off | `brain.Brain._c302_muscle`; `layers.muscle_activation`; body muscle fibres in `body/loop.py` (`Body`, `muscle_map`) | muscle_active (off); bwm_coupling (off); muscle_ca, muscle_activation (on) | brain 40 rows, 511: passive 380 (285 published fit, 95 guessed where clipped) and c302 membrane 28 (published fit), coupling 96 (guessed), Ca and activation 7 (guessed); body fibres 10 rows | test_muscle_active, M1-M4, C1 (muscle_active); test_small_brain (bwm_coupling); Ca and activation in every closed loop | By default the muscle membrane is passive. Voltage becomes Ca through a sigmoid and Ca becomes activation through a Hill curve; the c302 Ca pool is not used for force. The body's fibres pull linearly, with no force-length curve. PLAN's model is Du/Crodelle 2024; that is not ported. |
| 13 | Pharynx | **lumped** | `layers.pharynx` | pharynx (on) | 4 rows, 4 (2 measured, 1 inferred, 1 guessed) | ran in every default test and closed loop; nothing checked its output | A pump clock whose rate depends on food, with a fixed pump waveform. The 20 pharyngeal neurons are in the brain but do not drive it, and there is no pharyngeal muscle. Its output goes to the output record only; the body has no pharynx (body row MB12 missing). |
| 14 | Intestine and defecation | **lumped** | `layers.defecation` | defecation (on) | 8 rows, 8 (1 measured, 7 guessed) | C1 and the section 8 run S14, where its posterior contraction showed up as a step in muscle activation (BRAIN_PORT sections 6 and 8); no test checks the period | A fixed 45 s timer that adds two contraction boosts to the body-wall muscles. No intestinal cells, no IP3/Ca oscillator, no peptide output to AVL/DVB. Use `defecation=off` for rhythm tests. |
| 15 | Egg-laying | **lumped** | `layers.egg_laying` | egg_laying (on) | 4 rows, 4 (2 measured, 2 guessed) | ran in every default test and closed loop; nothing checked its output | A two-state active/inactive timer with a random laying rate. HSN, VC and the vulval muscles do not take part; the vulval output goes nowhere (no body part). |
| 16 | Other non-neural cells | **missing** | none | none | ledger mechanism other_cells, status absent, 0 rows | none | Hypodermis, seam, excretory canal and coelomocytes are not modelled. |
| 17 | Sensory transduction (12 modalities) | **lumped** | `layers.sensory_current` | sens_salt, sens_odor_attract, sens_repellent, sens_thermo, sens_o2, sens_co2, sens_light, sens_food, sens_touch_gentle, sens_touch_harsh, sens_tap, sens_proprio (all on) | 32 rows, 32 (26 guessed, 3 inferred, 3 measured) | test_proprio_senses_anterior (proprioception). Closed loops C1, C2 and section 8 fed proprioception and the diacetyl odour; the other modalities got constant plate values or zero. The D-run touch input was a direct 20 pA injection with this layer off | Each modality is one transform (log, threshold or linear) plus one adaptation filter, injected as current into named cells. No cGMP/TAX-2/4 cascade, no MEC-4 channel, no dose-response checked against data. |
| 18 | Slow intracellular signalling | **lumped** for one pathway, never run; **missing** for the rest | `layers.slow_gain`; also `layers.homeostatic_current` (homeostasis) | slow_signalling (off); homeostasis (off) | 7 rows, 7 (2 measured, 1 inferred, 4 guessed): slow_signalling 3, homeostasis 4 | none | Only an AWC odour gain that drifts over hours stands in for EGL-4/CMK-1. cGMP/PKG, CaMK translocation, GLR-1 trafficking, insulin/DAF-16, TGF-beta and CREB are not there. Homeostasis is a slow bias current that pulls each neuron's voltage to a target. |
| 19 | Gene expression beyond row 18 | **missing** as a dynamic layer | none (CeNGEN read once, through row 3) | none | 0 rows | none | PLAN allows a fixed parameter source here; that is all it is. |
| 20 | Metabolism | **spec only** | `layers.metabolism` | metabolism (off) | 2 rows, 2 (guessed) | none | An energy store that integrates pumps, but nothing reads it and it is not in the output. No fat, no energy charge, no insulin/TGF-beta output. |
| 21 | Body (3D soft body) | **lumped** (published 3D body, simpler than PLAN) | `body/metaworm.py` `run`; `body/loop.py` `Body`, `run` (MetaWorm FEM, BAAIWorm b99ca5ab) | body.material (homogeneous_published), body.scale (published), body.solver_exit (published), body.pressure (none) | body ledger 22 rows, 22 (MB1, MB2, MB4, MB9, MB10) | body tests P0-P3, A1/A2, A1f/A2f, S1-S4 (BODY_TESTS.md). Fails: P1 (slow settling), P2 head frequency, P3 speed (16-24x too slow) and P3 frequency; the latest-solver gate failed, so the published solver stays | One homogeneous elastic material (no separate cuticle) and no internal pressure (MB10 missing). No Cosserat rod path; the own rod was archived on 5 Nov when Ben chose to port published bodies. |
| 22 | Environment | **lumped** for fluid, agar and one odour field; **missing** for the rest | `body/scene.py` `ChemotaxisScene`; fluid and substrate in `body/metaworm.py` (`AGAR_PLATE`, `AGAR_FILM`) | env.fluid (quadratic_published), env.substrate (none_published), env.chemical_field (none) | body ledger 16 rows, 16 (MB5 fluid 11, MB6 substrate 5); the chemical scene has no rows | agar plate A1 pass, A2 fail (the body lifts off); agar film A1f, A2f pass; the cone field in the closed loops and the agar-film demo | Drag is a quadratic or resistive-force rule per surface triangle; agar is a plate or a thin film. Temperature, O2/CO2, food lawn, salt, touch and tap are constants or zero in `interface.HEAD_CHANNELS`, not fields. No viscoelastic fluid. |
| 23 | Observation models | **lumped** for GCaMP and gait readouts; **missing** for NeuroPAL identity | `layers.gcamp`; `body/metaworm.py` `gait`, `zigzag` | gcamp (on) | 7 rows, 7 (3 measured, 4 guessed) | GCaMP ran in every default test and closed loop, never checked against data; gait readouts used in the body tests | GCaMP is a Hill curve of Ca with rise and decay times plus noise, one setting for all cells. Gait readouts are frequency, wavelength, head curvature and speed, not the Tierpsy feature set. No NeuroPAL identity uncertainty. |

## Counts (derived from the table)

| Category | Rows | Which |
|---|---|---|
| full | 7 | 1 (neurons and BWM only), 2, 3, 4, 5, 6, 8 |
| lumped | 12 | 7, 9, 10, 12, 13, 14, 15, 17, 18, 21, 22, 23 |
| spec only | 2 | 11, 20 |
| missing | 2 | 16, 19 |

Every brain ledger row appears once above: 368 rows and 90,112 numbers in total (summed from the table). The 48
body rows split 22 / 10 / 16 over rows 21, 12 and 22.

Four rows are split (1, 18, 22, 23): part is in the row's category and part is missing. Rows 3 and 8 are full but
off by default, so a default run uses the simpler version.

**Never checked by any test or scored run: 8 rows** (9, 10, 11, 13, 15, 18, 20, and GCaMP in 23). Rows 9, 10, 11,
18 and 20 have never been switched on in any worm test or run.

## What this means for Thursday

- The cell model (rows 2-6) is BAAIWorm's published model, ported and checked against BAAIWorm's own run. That
  is the solid part.
- The connectome (rows 7-8) has the measured counts, but every per-pair strength is one guessed template value,
  and only two synapse types exist. Section 8 found no rhythm; whether the cause is these strengths or a missing
  rhythm generator is the open strategy question.
- Everything outside neurons and the body wall (rows 9-20) is lumped, spec only or missing. None of it has been
  checked against data, and five rows have never run.
- The ledger marks the mechanisms of rows 9-23 `partial`. That is true but loose: it covers a working timer (row
  14) and a constant multiplier (row 11) alike. This table is the stricter view. Whether the ledger should gain a
  `spec` status is a call for the Director.
