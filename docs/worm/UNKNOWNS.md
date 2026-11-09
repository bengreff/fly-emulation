# The worm's unknown numbers

Status 7 Nov 2026 (wmodel), counts updated 9 Nov 01:10 (wbrain2). Source: `wormemu.params` (`counts()`, `Theta().table`, `catalog()`), all measured
from the code today.

**Verdict.** 362 numbers are genuinely unknown (measured 9 Nov 01:10; 368 on 7 Nov 19:00). That is the whole fit
vector: 43 shared rules plus 319 gaps (15 of them discrete). It is well under Ben's 1,000-2,000 target. Everything else is fixed and labelled with
its origin (1,475 scan rows covering 80,147 elements), or taken out of the vector for a stated reason (331 rows). The
per-element residuals (6,298 slots) are frozen at 0. The count went from 340 at 13:00 to 347 at 18:10 (wiring) and to
368 at 19:00: the 21 drug numbers (mech/drugs, all guessed; read whenever an experiment schedules a drug). The
KNOWLEDGE_GAPS section C mechanisms added 10 numbers, all outside the vector because their switches are off by
default (8 guessed, 2 inferred). Fitting has not started.
8 Nov 22:08 (wbrain2): scan rows 1,272 to 1,329 and elements 79,944 to 80,001 (measured), the 57 constants of mech/channel_forms (Nicoletti 2024's EGL-19 and SHL-1 forms, published fits, both toggles off by default); the vector is unchanged at 368.
8 Nov 23:43 (wbrain2, after the wbody2, weki and wneuro merges): the vector is 370 (43 rules, 327 gaps, 15 discrete; measured): +1 `rule_body_modulus_scale` (wbody2, guessed) and +1 `unc2_gs_gain` (wneuro, guessed). Scan rows 1,329 to 1,339 and elements 80,001 to 80,011: the 7 `cabulk_*` numbers of the bulk Ca readout pool (mech/capool `ca_bulk`, off by default; 6 inferred, 1 derived), `pep_ec50_nlp-40_aex-2_wang2013_nM` (wneuro, measured, its toggle off), `body_E_bending_kPa` (wbody2, measured) and `obs_gcamp7f_range` (guessed -> measured, Dana 2019's preprint, so it leaves the inactive unknowns: 325 -> 324).
9 Nov 00:39 (wbrain2): scan rows 1,339 to 1,452 and elements 80,011 to 80,124 (measured), the 113 constants of mech/cell_models (Jiang et al. 2022's AVL model as the avl_membrane toggle and its DVB borrow, dvb_membrane jiang22_noexp2; 105 published fits, 8 inferred DVB conductances; every toggle off by default); the vector is unchanged at 370 and the inactive unknowns at 324.
9 Nov 01:00 (wbrain2, after the 3300581 wneuro merge): the vector is 369 (43 rules, 326 gaps, 15 discrete; measured): -1 `ma_ec50_serotonin_ser-1_nM` (wneuro: guessed -> measured, 1340 nM, Xie 2005 via Dernovici 2006), which moves to the scan. Scan rows 1,452 to 1,475 and elements 80,124 to 80,147: that row, wneuro's `ma_store_molecules_serotonin` and `_dopamine` (derived) and `pep_ec50_flp-25_dmsr-1_isoA_nM` (measured, its toggle off), and the 19 `n22_*` constants of Naudin et al. 2022's AFD model (mech/cell_models, `afd_membrane` naudin22, off by default; published fits). Inactive unknowns unchanged at 324.
9 Nov 01:10 (wbrain2, inbox item 6): the vector is 362 (43 rules, 319 gaps, 15 discrete; measured): -7 numbers that describe the experiment, not the worm, now marked experiment settings in `params` (SETTING_PREFIX `scene_`, SETTINGS `obs_noise_dff`): the 6 guessed `scene_*` plate-field numbers (body/scene.py; set through `Experiment.scene`) and `obs_noise_dff` (the imaging noise of the dataset scored). Inactive unknowns 324 -> 331 (those 7). Scan unchanged at 1,475 rows and 80,147 elements.

## What the roles mean

| role | n | in the fit? | what it is |
|---|---|---|---|
| rule | 43 | yes | a shared rule on structure (`structure_rules`): a few numbers that set many per-cell values from CeNGEN, EM counts and transmitter identity |
| gap | 319 | yes | a guessed or absent value the code reads, with a cited range (`lo`, `hi`) where wranges has one |
| scan | 1,475 rows, 80,147 elements | no, fixed | measured, published fit, derived or inferred; labelled with its origin for debugging |
| residual | 6,298 slots | no, frozen at 0 | a per-element correction on top of a rule; frozen until the rules alone fail held-out data |
| inactive unknown | 331 | no | guessed or absent, but out of the vector for the reason below |

## Why 331 unknowns are out of the vector (measured 9 Nov 01:10)

| reason | n | meaning |
|---|---|---|
| replaced by structure_rules | 197 | per-cell or per-class values now set by a rule. The rule's numbers are in the vector instead |
| other form only | 83 | read only by a mechanism form or switch that is off by default (for example c302's 10, muscle_active's 4, the section C switches glia_gaba, unc58_na_leak, pathogen_sickness). It enters if that form is adopted |
| experiment setting | 7 | a number about the experiment, not the worm (`params.SETTINGS`, `SETTING_PREFIX`): the 6 guessed `scene_*` plate-field numbers, set by `Experiment.scene`, and `obs_noise_dff`, the imaging noise of the dataset scored |
| slot only | 29 | a ledger slot with no code reading it yet (monoamine uptake 4, sleep_ris_ala 3, ...) |
| absorbed | 8 | the receptor unitary conductances: only gamma x syn_nchan_per_em_* enters, so the product is the gap |
| linked | 4 | set by another quantity: `ion_celsius` and `env_default_temperature_C` (the experiment's temperature), `body_pressure_kPa` and `body_pressure_ctrl_kPa` (organs_other's steady pressure) |
| not read | 3 | `ion_ena` (nca uses its own +30 mV), `ion_cao` (sets only NEURON's Nernst eca; every Ca current uses +60 mV), `glia_k_gleak_nS` (replaced by `glia_k_leak_frac`, the K+ share of each amphid neuron's own leak) |

## The 368 by grain (7 Nov 19:00, not re-measured since)

| grain | n |
|---|---|
| class | 189 |
| global | 126 |
| gene | 20 |
| cell | 19 |
| channel | 11 |
| pairing | 3 |

The 19 per-cell numbers are the 15 discrete synapse signs (`syn_inhibitory[cell]`, the cells whose sign CeNGEN
cannot settle), three cell areas in other_cells and `osmo_canal_gain`. Nothing in the vector is per synapse.

## The 368 by PLAN row (7 Nov 19:00, not re-measured since)

| row | | n | row | | n |
|---|---|---|---|---|---|
| 5 | channel densities, Cm, leak | 8 | 17 | sensory transduction | 33 |
| 6 | calcium | 1 | 18 | slow signalling | 14 |
| 7 | chemical synapses | 86 | 19 | homeostatic tuning | 5 |
| 8 | gap junctions | 19 | 20 | metabolism | 4 |
| 9 | neuropeptides | 17 | 22 | environment | 6 |
| 10 | monoamines | 12 | 23 | observation | 7 |
| 11 | glia | 14 | 24 | plasticity and learning | 22 |
| 12 | body-wall muscle | 7 | 25 | temperature | 5 |
| 13 | pharynx | 5 | 26 | noise | 12 |
| 14 | intestine and defecation | 30 | 27 | ion pumps | 6 |
| 15 | egg-laying | 14 | | | |
| 16 | other non-neural cells | 17 | 21 | body (damping) | 3 |
| | drugs (rows 7, 10, 22) | 21 | | | |

The 21 drug numbers and eight others are code Specs with no ledger row yet, so no PLAN row in `params.catalog()` (`rec_des_recover_ratio` in 7, DAF-7,
CREB and the two AFD T* fractions in 18, the three damping numbers in 21); wranges has the list. Rows 1-4 (inventory,
morphology, channel presence, kinetics) and 28 (sleep, through row 9) have no gaps: they are scan.

## The largest mechanisms

receptor_kinetics 48; structure_rules 44 (43 rules plus 1 gap); drugs 21; defecation 19; peptides 17; syn_sign 15;
egg_laying 14; slow_signalling 14; monoamines 12; channel_noise 11; stp 11. The other mechanisms have 9 or fewer
each. The body has 3 (`body_damp_tau_ms`, `body_damp_w_ref_rad_s`, `body_damp_clip`).

## Degeneracies the fit will meet

These are pairs or groups the data cannot tell apart. They are not removed yet; the fit should constrain them
jointly (wranges' 177 joint constraints cover some) or fix one side.

- `gap_open_channels` x each innexin's unitary conductance: only the product sets a gap junction's conductance.
- `cmk1_*_effect` and the AFD T* fractions (`afd_tstar_fast_frac`, `afd_tstar_slow_frac`): both scale how far T*
  moves, so a check on T* alone cannot split them.
- The receptor unitary conductances x `syn_nchan_per_em_*` are already merged (the 8 "absorbed" rows).

## The failing unit checks: values, not bugs

11 of the audit's unit checks fail today (MECHANISMS_AUDIT.md, counts; 13 lines below, as rows 17 and 21 each fail
two ways). None is a code bug.

| row | check | fails | why |
|---|---|---|---|
| 7 | NMJ IPSC | 29.2 ms against 24.8 +/- 2.7 | gap values: the UNC-49 and release kinetics together (UNC-49 alone passes) |
| 11 | glia | recovery 0.525 s; right side 26% (before the 7 Nov K+ leak fix; not re-run) | gap values: the K leak's reversal feedback sets recovery |
| 15 | egg-laying | no egg in 3 h | gap values: HSN's resting 5-HT release is low against nM EC50s |
| 16 | other cells | canal 10.7 h against 12-24 h | gap value: the canal time constant |
| 17 | proprioception | DVA Po 0.483 against > 0.5 | gap value: the gain |
| 21 | body damping | 16.7 ms | gap value |
| 23 | opto | AVAL +0.39 mV against > 1 | gap value: the sign is right, the conductance is guessed |
| 24 | GABA | plateaus 0.76, 0.57 against > 0.8 | gap value: GABA short-term plasticity borrows ACh's numbers |
| 4 | channel W | 3.8 mV against 2 | scan: two published kinetic models differ (BAAIWorm's mods at Nicoletti's AIY densities); the Nicoletti form of egl19, slo1_egl19, nca, shl1 is a switch still to build (mods not on the Mac) |
| 6 | Ca volume | AIYL 3.05x, RIML 2.21x, VA05 2.05x | scan: BAAIWorm's hoc morphology against Nicoletti's NeuroMorpho cells, two reconstructions; the alternative is now a switch (`ca_pool_volume neuromorpho`) |
| 17 | AWA | 39.8 mV against 25.8 +/- 6 (8 Nov: rest -76.2 mV after the Kir fix, was 33.9 mV at rest -64.6) | published fit: the transcription matches the printed equations and Table S4, but the authors' code differs from them in five places (the Kir now follows the code, `awa_kir`); the code's own form does not spike in Liu's 2-12 pA window (wbrain2 night file, 8 Nov); the alternative is a switch (`awa_membrane baaiworm`) |
| 21 | body bending | 856 kPa, 7.8x the measurement | scan: the layer moduli are a published fit (frontiers2024). Audited 7 Nov: no error in how the layers combine (the core carries about 65%; the FEM's effective modulus is 676 kPa, 6.1x); muscle stiffness is not counted twice |
| 28 | RIS Gi | 0.034 against 0 | the bar is probably wrong: it assumes DMSR-1 is RIS's only Gi input, and CeNGEN gives RIS others. Rossi et al. 2025 Curr Biol 35:2183 (the EXPR_ADD source) is the held-out source for a better bar (quiescence) |

The 8 value failures are the fit's job. The 4 scan and published-fit rows (4, 6, 17 AWA, 21 bending) need a decision,
not a fit. Ben's rule for 4, 6 and 17 AWA ("possible worms"): keep both published sources as a switch, default the
simplest that passes, never a fitted number. Rows 6 and 17 have their switch; neither alternative is known to pass, so
the defaults stay (whole_cell, liu2018) pending Ben. Row 21 has no representation error, so the choice left is
Ben's: keep the published moduli or make them gaps with the published value as the prior. Row 21 is the one most
likely to matter for behaviour.

## Slots (documented, no code reads them yet)

- EM synapse size: every synapse rule uses the Cook 2019 serial-section count as the EM measure; a per-pair size or
  contact area (Witvliet et al. 2021; Brittin et al. 2021, the copy on backhouse unchecked) would replace it
  (`mech/structure_rules` docstring).
- The 34 TWK genes other than unc-58; the odorant arm of AMsh sensing; the PA14 sickness pathways (ALA peptides,
  ASI DAF-7, FLP-13 through DMSR-1; `mech/pathogen` docstring); row 4's Nicoletti kinetics switch.

The single-cell excitability sanity check (wexcite: 74 cells over the upper bar, 47 below -150 mV) traces to
expression-map values, which are rules and gaps in the vector. It is a value failure too.

## How to use this

- The vector: `params.Theta()` (ids, bounds, transforms, origins); `params.set_value(spec, id, x)` sets one and
  raises on a scan number.
- The model the fit calls: `wormemu.simulate(theta, experiment)` (DATA_MODEL.md).
- Where each number acts: INTERCONNECT.md (who reads whom) and MECHANISMS_AUDIT.md (per PLAN row).
