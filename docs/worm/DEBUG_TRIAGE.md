# Debug pass, phase 1: triage (wtriage, 8 Nov 2026)

No fixes in this phase. Every number below is from a run or a source opened today unless marked. Labels:
measured (a run of our model, or a recording), derived (arithmetic on those), source (a published value, opened).
Probe values live only in `runs/worm/triage/` (untracked); nothing was written to the ledger, catalog, parameter
tables, templates, constraints or `src/`, and no bound was widened. Scripts: `scripts/worm/triage/`. Night log:
`docs/worm/night/2026-11-08_wtriage.md`.

Classes: A code or representation bug; B mechanism simpler than its published model, or wrong; C published sources
disagree (both become toggles); D a gap value fixes it, found by a probe inside the bio box; E the check is wrong.

## Table

| # | Item | Row | Check and bar (source) | Model value (measured) | Class | Evidence | Probe (D only) | Owner | Size |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Channel forms, AIY current clamp | 4 | BAAIWorm mods vs Nicoletti's at AIY densities agree within 2 mV (channels_unit_check) | 3.8 mV | C | EGL-19 2nd inactivation V1/2 -20.5 (BAAIWorm, = Nicoletti 2019) vs -10.54 mV (Nicoletti 2024), slow tau 44.6 vs 81.1 ms, +10 mV shift; SHL-1 slope 14.1 vs 16.25 mV, inactivation V1/2 -33.1 vs -40 mV. Both files opened | | brain | medium |
| 2 | Ca pool volumes | 6 | BAAIWorm volume / Nicoletti 2024 NeuroMorpho volume in 0.5-2x | AIYL 3.05x (22.6 vs 7.42 um3), RIML 2.21x, VA05 2.05x | C | two reconstructions of the same cells; toggle `ca_pool_volume neuromorpho` exists and passes by construction | | brain | small |
| 3 | NMJ GABA IPSC decay | 7 | 24.8 +- 2.7 ms, bar 22.1-27.5 (Liu, Hollopeter & Jorgensen 2009) | 29.16 ms | A | receptors.py:153 uses the evoked IPSC decay (24.8 ms, a composite) as the receptor's own close rate, then the release state (8.6 ms tail) adds on top. Bio-box probe 0/128 (best 28.5 ms); instant release gives 24.23 ms. Fix: fit the receptor tau so the composite gives 24.8 | | brain | small |
| 4 | Glial K+ buffering | 11 | peak 0.2-12 mM, recovery 0.7-6.3 s, Kir null >= 1.2x slower, right < 10% of left (worgans pre-reg, PORT_SOURCES_ORGANS O5) | fails | E | probe 0/64; 7 points pass all but the sides bar. Sides bar has no source; tau and null bars are mammalian Kir4.1; the 12 mM ceiling is "from memory, not opened". Right side rises through the network, not the glia | | body | small |
| 5 | Egg-laying pattern | 15 | >= 3 clusters, intracluster 5-60 s, intercluster 10-60 min (Collins et al. 2016 eLife; Zhang et al. 2010) | no eggs; HSN -53.6 mV, 0.65% of time above -30 mV; vulval 5-HT 0.33 nM vs SER-7 EC50 30 nM | B | Zhang, Schafer & Breitling 2010 (PMC2887794): HSN is an autonomous two-state oscillator gated by VC (~20 s) and uv1 (~20 min). Ours is BAAIWorm's HSN membrane, silent alone. The 5-HT shortfall at the vulva is its own line (22, D); HSN's silence stays B | overnight on backhouse from 22:00 (PID 82978; 20 ids incl. line 22's; 64 points, about 10.5 h); a pass would make this D | body | large |
| 6 | Excretory canal swelling | 16 | canal-null t90 12-24 h (Nelson & Riddle) | 10.66 h | D | analytic band Lp x E = 2.75e-5 to 5.33e-5 /s | 17/128 (13%), 13 off edges | body | small |
| 7 | AWA spike and rest | 17 | rest -75.3 +- 4.7 mV, amplitude 25.8 +- 0.8 mV (Liu et al. 2018, bioRxiv 359935) | rest -64.6 mV; first spike 39.8 mV | A | the ported Kir (awa_liu2018.mod:108, senses_checks.py:115) is inward at every voltage (-4.0 pA at -50 mV), impossible for K+ above E_K. Read as an outward smooth minimum: rest -76.1 mV. Amplitude stays high after the fix (Open) | | brain | small |
| 8 | DVA stretch response | 17 | DVA > 0.5 at a half-body bend (sanity bar, no source) | 0.483 | D | DVA reads mean abs curvature over the whole body; half bent gives strain 0.098, on eps_half 0.1 | 23/128 (18%), 19 off edges; passes need eps_half < 0.097 | brain | small |
| 9 | Body damping | 21 | mean tau <= 5.3 ms (Fang-Yen et al. 2010, derived) | 16.70 ms | D | w_ref 10 rad/s was derived for ~1 rad of swing the stiff body never makes | 27/64 (42%), 20 off edges | body | small |
| 10 | Bending stiffness | 21 | 50-170 kPa (Backholm et al. 2013, 110 +- 30 kPa whole worm) | 856 kPa (mesh); 794 kPa ideal shells | C | layer moduli are Frontiers 2024 indentation values; Backholm is whole-worm bending; the composite-beam formula (body/layers.py:158) links the two, and they disagree 5-8x. Challenge iv: Ben's approved fitted rule parameter does not exist yet (phase-2 build). The only non-scan lever, body pressure (gap, linked to organs_other), gives 324 kPa at zero pressure; only every scan modulus at its low end reaches the band (101 kPa), and scans cannot make a D | | body | medium |
| 11 | Mac run_body binary | 21 | (tooling) | ignores --damping | A | `third_party/metaworm/driver/run_body` built 6 Nov 20:29, before the damping commit a6f75cf (21:46). Fix: rebuild; metaworm.run refuses a binary older than run_body.cpp | | body | small |
| 12 | Opto actuator | 23 | AVAL dv > 1 mV after a 0.5 s pulse (no source) | fails at the ledger | D | the real calibration is Randi 2023's autoresponse (item 4b) | 20/32 (62%), 14 off edges | body | small |
| 13 | GABA short-term plasticity | 24 | plateaus > 0.8 at 1 and 5 Hz, 20 Hz second/first > 1 (Liu et al. 2009) | fails at the ledger | D | 8 guessed stp_gaba gaps | 24/256 (9%), 10 off edges; best 1.13 / 1.75 / 1.25. The bar accepts 5 Hz facilitation Liu did not report | brain | small |
| 14 | RIS Gi without DMSR-1 | 28 | Gi == 0 with dmsr-1 removed | 0.062 | E | 25 other peptide GPCRs CeNGEN puts on RIS (largest nlp-13, Gi) still see peptides. Rossi et al. 2025 (PMC7617803) does not say DMSR-1 is RIS's only Gi route. Fix: bar on the DMSR-1 share | | brain | small |
| 15 | Own ephys, AIY / AFD / AWA (item 3) | 5 | FIT2 features on the training sweeps (Naudin 2022, Liu 2018); RMSE, FIT2 best 16.6 / 10.5 / 13.7 mV | AIYL 113.8, AFDL 26.8, AWAL 16.3 mV | A | brain.py:427-433: the CeNGEN mask deletes 8 of BAAIWorm's fitted AIYL channels (egl2, shl1, kqt3, kvs1, irk, egl36, cca1, shk1). Mask off: AIYL 9.3 mV. Fix: leave BAAIWorm-fitted cells unmasked until FIT2's map or a refit replaces them | | brain | medium |
| 16 | 121 unphysical single cells (4a) | 3, 5 | upper/lower voltage bars at +-20 pA (wexcite) | 74 upper, 47 below -150 mV | A | 61 of the 74 come from the same mask (13 with it off, all BAAIWorm's own cells at 5.6-7.8 GOhm; their leak is ported exactly, challenge v). The bars are not laws: recorded AIY reaches -125.6 mV at -15 pA, RIM +75 mV at +35 pA | | brain | medium |
| 17 | ~30x deficit vs Randi (4b) | 23 | autoresponse 30 s mean dF/F, training median 0.43 (Randi 2023) | 0.014-0.018 | B (was C; challenge ii) | follows from line 19. The response peaks (0.24-0.31) but decays in ~3 s: the readout's decay (line 19), not excitability. Gaps at their tops give 0.08-0.11; adding capool tca 150 and f 0.003 gives 0.64-1.09. AVAL stays 0.048 (1.19 pA Ca current into 129 um3) | | body | small |
| 18 | Saturated vs silent network (4c) | 2, 8 | no published bar for a fraction of neurons above -20 mV | open loop 0%, median -50.3 mV; synapses x4: 7% | E | the "swing" (197, 94, 0, 16% of 302) compared different builds and drives. Same build, every synapse x0.5 / x2 / x4 gives 0 / 0 / 7%: not a knife edge | | brain | small |
| 19 | GCaMP decay (4d) | 23 | GCaMP6s half-fall 8.4 +- 5.0 s in vivo (Ding et al. 2023 G3, PMC10542313, Table 1) | 0.64 s (13x fast; 2.06 s at both range tops) | B (was C; challenge ii) | GCaMP reads the only Ca pool there is, Nicoletti 2019 Eq. 28 (opened): "[Ca]_micro", the microdomain around the SK channels, tau_Ca 33 ms with no source (BAAIWorm's cainternm.mod: 50 ms). Ding measures bulk cytosolic Ca through GCaMP. Different compartments, both can be true, so not C. Missing: a bulk cytosolic compartment (shell-to-core exchange, buffering, extrusion) for the indicator; the shell-plus-core form already exists in our port of Sherman & Harel 2024 (sh_pharynx.mod) | | body | medium |
| 20 | Compartment convergence | 3 | segments <= 0.1 lambda_AC at 100 Hz (NEURON d_lambda rule) | 97 of 2,253 sections short, none in neurons | B | hypodermis one 5,093 um compartment (needs 35, 34x), excretory cell (needs 5), BWM somata 1.45x | | body | small |
| 21 | Viewer 8/20 vs audit 13/15 (item 6) | 4, 6, 14, 19, 24 | the two counts | 8 vs 13 full | E | the viewer calls a split row "simplified" if any part is lumped; the audit files it under its main category. The 5 split rows explain 13 - 5 = 8 | | brain | small |
| 22 | 5-HT at the vulva (line 5's second cause, challenge vi) | 15 | peak vulval 5-HT over 60 s at full HSN drive (+40 pA, q 0.99) >= 30 nM, SER-7's EC50 (Hobson et al. 2006, PMC1456143: 30 +- 3 nM) | 9.0 nM at the ledger (the store drains to 9%; 15.4 nM steady state, derived) | D | the five guessed amine-release gaps (neuromod.py:225-250: release rate, degradation tau, store, synthesis tau, release tau). Every pass has a store >= 2x the template (1.97e6 to 8.7e7 molecules); release in passes spans 3.7e4 to 7.4e6 /s. Caveat: the row 15 brain (8 cells) has no MOD-5 cells, so no reuptake; a pass is an upper bound | 13/64 (20%), 6 off edges; best 570 nM (19x; release 3.5e6 /s, store 3.3e7, degrade 13.9 s, synthesis 14.5 s, tau 192 ms), no id at an edge. neuromod_unit_check at the best: every check passes but ris_self_limit, line 14's failure at the same 0.062 | body | small |

Class counts (table lines 1-22): A 5 (lines 3, 7, 11, 15, 16); B 4 (5, 17, 19, 20); C 3 (1, 2, 10); D 6 (6, 8, 9,
12, 13, 22); E 4 (4, 14, 18, 21). Lines 15 and 16 share one cause (the mask); 17 follows from 19. Only line 5 (HSN) is
large.

## Never-checked items (item 2): measurement, bar, and what was done

| Row | Item | Published measurement and bar (opened) | Done |
|---|---|---|---|
| 3 | expression-map effect | our own recordings (FIT2 training sweeps) | measured: table row 15 (A) and 4c: the mask makes 8 cells depolarise alone (URXR, ADEL/R, IL2s, RIPL) |
| 3 | compartment convergence | NEURON d_lambda rule | measured: table row 20 |
| 5 | densities vs our ephys | AIY, AFD, AWA recordings (Naudin 2022, Liu 2018) | measured: table row 15; RIM sealed |
| 8 | gap conductances | no nS value exists in free sources. Liu, Chen & Wang 2017 (PMC5364397, opened): VA5 current depolarises AVA, AVA current barely moves VA5; the coupling coefficients are only in Fig. 6c | spec: digitise Fig. 6c (CC-BY), then measure our AVA-VA5 coupling both ways (gap_rect_ratio 4 already encodes the direction) |
| 10 | amine levels | whole-worm octopamine 5 +- 2, tyramine 0.3 +- 0.1 pmol/mg (Alkema et al. 2005; snippet only, the free PDF failed to load) | no opened measurement; and whole-worm tissue content is not our free pseudocoelomic nM without a free fraction we do not have. Explained, not run |
| 17 | dose-response by modality | AWA Ca EC50 to diacetyl 30 nM in one experiment, per-animal EC50s over two orders of magnitude; EGL-19 block (nemadipine) moves it ~100x to 2.5 uM (Larsch et al. 2013 PNAS, PMC3831453, opened) | spec, after the AWA Kir fix: our AWA Ca dose-response (front-end K 1 uM, inferred) vs that spread, with the EGL-19-block shift as the held-out mechanism test |
| 18 | DAF-7 / CREB | no quantitative fold change found; Myers & Rothman 2012 (PMC3394784, opened) is qualitative | no measurement exists in free sources; nothing to run |
| 22 | food / salt / temperature fields | thermotaxis plates 17-25 C radially on a 9 cm plate (PMC1449549, opened; 0.9-1.8 C/cm derived, if linear); salt plate 35-95 mM (Kunitomo et al. 2013, snippet only) | read: our 0.5 C/cm (0.1-2.0) and 50 mM background plus a 50 mM plug are consistent. The 0.5 C/cm is labelled measured but cites secondary sources: a label fix |
| 23 | GCaMP vs recorded traces | Ding et al. 2023 Table 1 | measured: table row 19 (C) |
| 25 | Q10 | defecation period temperature-compensated 19-30 C (Liu & Thomas 1994, snippet only: the journal PDF sat behind a bot check) | no opened Q10; spec: open Liu & Thomas 1994 and check our dmp_clock factor (temperature.py) keeps the period within its SD across 19-30 C |
| 28 | quiescence | nose immobility 48% in wild-type lethargus, < 14% in flp-11 (Turek et al. 2016 eLife, PMC4805538, opened and spot-checked) | not runnable: lethargus is an L4 state and the model is an adult. Goes with Ben's step 2 (development) |

## Item 3: our own single cells through the recorded protocol

`ephys_score.py` (backhouse). FIT2's protocol and features unchanged, training sweeps -15 to +35 pA only; RIM is
sealed and was not opened. RMSE over the 24 features, mV (measured):

| Cell | Default (mask on) | Mask off (diagnostic) | FIT2 best (its map) | Rest, model vs recorded |
|---|---|---|---|---|
| AIYL | 113.8 (swings -308 to +257 mV) | 9.3 | 16.61 | -35.3 vs -54 mV (mask off -51.3) |
| AFDL | 26.8 (+37 mV steady at +35 pA vs +2.9) | 43.4 (-227 mV at -15 pA) | 10.53 | -72 vs -79 mV |
| AWAL | 16.3 (liu2018); 18.3 (BAAIWorm membrane) | 16.3 | 13.71 | -64.3 vs -78 mV (the Kir bug, row 7) |

The mask is the AIY problem (class A, table row 15). AFD is wrong either way: the mask deletes its large kqt3
(0.022) and adds 10 median densities; without the mask its input resistance at hyperpolarised voltages is far too
high. That is FIT2's job (Open). FIT2's true map trains worse than its four shuffled maps (8.4-10.8 vs 13.72 mV);
not explained today (Open).

## Item 4: whole-worm physiology along its causal chain

- (a) 121 unphysical cells: 61 of the 74 upper violators are the CeNGEN mask on BAAIWorm's per-cell fits (A). The 13
  left are BAAIWorm's own cells at 5.6-7.8 GOhm. The 47 below -150 mV are high input resistance at hyperpolarised
  voltages (AIYL 13.7 GOhm vs the recorded 4.8). The bars are not physiological laws (recorded AIY -125.6 mV at
  -15 pA).
- (b) ~30x deficit vs Randi: not excitability. The autoresponse reaches dF/F 0.24-0.31 and decays in ~3 s, so the
  30 s mean is 0.014-0.018. The chain is opto actuator (gap) -> V -> Ca pool (tca 50 ms, scan) -> GCaMP6s (thalf
  619 ms, scan). Lengthening the Ca pool's clearance is what closes it (0.64-1.09), which is (d).
- (c) Saturated vs silent: the current build, open loop, sits at 0% above -20 mV (median -50.3 mV) and needs every
  synapse x4 to reach 7%. The 197 -> 94 -> 0 -> 16% history is four different builds and drives: STP's release
  factor (mean 0.34) and neuromod's (0.51-1.80) each multiplied every synapse, and v1 is closed loop with the body.
  The network's absolute level is what FIT1 (Randi) and then Atanas set; there is no voltage bar for it.
- (d) GCaMP decay: 0.64 s half-fall at the ledger (derived from `binding_step`, a 1 uM, 3 s Ca step), 13x faster
  than Ding's 8.4 +- 5.0 s, not 4x. The best inside the ranges is 2.06 s, below Ding's -1 SD (3.4 s). B (challenge
  ii, Director 14:45, accepted): the indicator reads Nicoletti's channel microdomain pool because no bulk cytosolic
  compartment exists. Phase-2 build: a bulk compartment fed from the shell (exchange, buffer, extrusion), with the
  indicator reading it and the Ca-dependent channels keeping the shell; Ding 2023 is the check, not the fit target.

## Item 5: vital signs

Every default form is a mechanism; the clocks and timers survive only as nested, non-default toggle values
(pharynx `clock`, defecation `timer`, egg_laying `timer`). So nothing is SET by default and no sign is class B for
being set; whether each one actually emerges is the current value.

Two runs, both pre-registered in their scripts:
- Preliminary, brain only (`vital_signs.py`, backhouse, 14:27-15:06): no body, food or odour; default toggles;
  120 bio s from reset. mask_off is the item-3 diagnostic.
- The entire worm (challenge i, `vital_loop.py`, backhouse, from 15:05): closed loop with the MetaWorm body, wbody's
  sense modules and every plate field, food on and off. Its numbers are below the table.

All values are measured.

| Sign | Published range (opened) | Mechanisms that must produce it | EMERGES / SET | Brain only, default (mask off) |
|---|---|---|---|---|
| Pharyngeal pumping | 3.46 +- 0.19 Hz on food after a 2 h fast (Hiebert et al. 2017, PMC7255878); no food here, so lower is expected | MC and the pharyngeal neurons on Cook's wiring -> Sherman & Harel 2024 muscle APs -> Ca -> pm4 activation crossings | EMERGES | 0 pumps in 120 s (0) |
| Defecation cycle | 45-50 s at 20 C on food (Kwan et al. 2008, PMC2409367; controls 46.4 s) | Li-Rinzel IP3R Ca oscillator in 20 intestinal cells, int9 pacemaker, INX-16 wave -> pBoc protons and NLP-40/AEX-2 -> enteric muscles -> expulsion | EMERGES, but its period was fitted to Espelt 2005's 49 s on the isolated intestine, so the period is not an independent test | 0 expulsions. Intestinal Ca peaks (0.67 uM max) at 34.8, 47.4, 86.9, 98.7, 114.9 s: intervals 12.6-39.5 s, mean 20.0 s, irregular (identical with mask off) |
| Egg-laying | clustered, intercluster 10-60 min (Collins et al. 2016; Zhang et al. 2010) | HSN membrane -> 5-HT/NLP-3 -> vulval muscles, uv1 tyramine feedback, uterine stretch | EMERGES in form; does not occur (lines 5 B, 22 D) | 0 eggs (0); 2 min is too short to judge |
| Body-wall muscle | dissected: rest -25.0 +- 1.0 mV (n = 27), spontaneous APs 0.73 +- 0.14 Hz in ~80% of preparations (Gao & Zhen 2011, PMC3038695) | Du/Crodelle 2025 BWM membrane, Cook NMJ drive, Liu 2006 BWM gaps | EMERGES | median -30.8 mV (-30.3); 1.83 Hz per muscle (1.97), 81% of the 95 muscles fire (82%). Rest is 5.8 mV below Gao & Zhen's mean and the rate is 2.5x theirs, though their preparation is dissected and ours is driven by the network |
| Neuron state | no published voltage bar (line 18); phase-2 bar under challenge iii | the whole network | EMERGES | 0.10% of neurons above -20 mV on average, peak 23%; median -51.0 mV (0.01%, 18%, -54.0 mV) |
| Quiescence | 48% nose immobility in L4 lethargus (Turek et al. 2016, PMC4805538) | needs an L4 state | not modelled (development, Ben's step 2) | n/a |

The entire worm (challenge i), measured. Closed loop on backhouse, 150 bio s per condition, 15:05-15:34, about
11.4 s of wall per bio-s. 64 toggles on; finite; the body moved up to 0.11 mm from rest.

| Sign | Food on (food_OD 1.02 at the head) | Food off |
|---|---|---|
| Pharyngeal pumping | 0 pumps (published 3.46 +- 0.19 Hz) | 0 pumps |
| Defecation | 0 expulsions; intestinal Ca peaks at 34.9, 47.4, 86.9, 98.7, 115.0, 136.7 s (mean interval 20.4 s; published 45-50 s) | identical peak times |
| Egg-laying | 0 eggs (150 s is too short; lines 5 and 22) | 0 |
| Body-wall muscle | median -30.2 mV, 1.96 Hz per muscle, 82% fire | -30.9 mV, 1.83 Hz, 81% |
| Neuron state | 0.15% above -20 mV on average, peak 25% | 0.12%, peak 20% |

Verdict: the entire worm has no vital signs that match yet, and food changes nothing.
- Nothing is SET, so no sign is B for being set.
- Of the four rhythms, only the body-wall muscle runs, and it runs 2.7x fast and 5 mV low against a dissected
  preparation.
- The pharynx never pumps: 0 pumps on and off food, in the brain-only and the entire-worm runs alike.
- The intestine's Ca cycles irregularly at about 20 s, with the same peak times in every run, and it never
  completes an expulsion.
- Food reaches the head and the four food sensors (about 3.4 pA into ADF, ASI, ASJ and NSM, derived from
  `brain_layers.py:310`), but leaves every sign within 0.8 mV and 0.13 Hz (BWM -30.2 vs -30.9 mV).

Inferred, not traced: the likely route for the missing pumps is a silent MC. The pump needs MC to drive pm4
through the marginal cells (organs_pharynx), and the network sits at 0.1% of neurons above -20 mV (line 18).

Phase 2 (spec, not run today):
- Trace MC, then the marginal cells, then pm4 voltage in this loop (about 2 min of wall per 10 bio-s).
- Find why the intestinal Ca peaks fall at the same times with and without food, and why no expulsion follows.
- Run the loop for 1 bio-h overnight for eggs, after line 5's HSN build.

Behaviour was not fitted or grafted. The brain-only numbers above are the preliminary and agree with these within
1 mV and 0.15 Hz.

## Item 6: viewer vs audit

The viewer marks a split row "simplified" when any part is lumped or missing; the audit files it under its main
category. Rows 4, 6, 14, 19 and 24 are split: full in the audit, simplified in the viewer, so 13 - 5 = 8.

## The Director's challenges (14:45)

- ii. Lines 17 and 19: reclassified B (was C). There is no bulk Ca compartment for the indicator (line 19 evidence).
- v. The 13 cells at 5.6-7.8 GOhm: not a units slip (Open has the source lines), so line 16's remainder is not A.
- vi. Line 5's second cause is now line 22: D, 13/64 inside the bio box (probe_5ht.py, pre-registered).
- iv. Stiffness: the approved fitted rule parameter does not exist, so it is a phase-2 build item; line 10 stays C.
- i. Item 5 is now the entire worm: one everything-on closed loop with the body on backhouse, food on and off
  (item 5 section). The brain-only runs are kept as the preliminary.
- iii. Neuron state, the phase-2 bar. HELDOUT.md read first. Statistic: the fraction of variance in the first three
  principal components of the z-scored GCaMP traces of the identified neurons, one value per animal over the whole
  recording. Ours goes through `mech/observation` (the same readout lines 17 and 19 test), on the cells the
  recording identified. Source and range:
  - Kato et al. 2015 is scoreboard entry 95, marked HELD-OUT, so its numbers were not opened.
  - Uzel, Kato & Zimmer 2022 (Curr Biol 32:3443, CC BY) is not locked. A literature pass (Sonnet, 14:52-14:58)
    found it free (Cell Press OA, Vienna repository, data on OSF 3vkxn), but every fetch was blocked (403 or a
    JavaScript gate), so it read no numbers. Whether its recordings reuse Kato 2015's animals is also not known.
  - Atanas et al. 2023's own aggregates include the 20 locked animals of atanas2023_main.

  So the range is not filled today. Phase-2 bar: the 5th to 95th percentile of this statistic over the 60 open
  atanas2023_main animals (CC BY 3.0 US, Zenodo 8185377, on backhouse, not yet extracted). A committed script
  computes it before any model run is scored, and `heldout.exclude` drops the locked ids. Atanas is freely moving,
  so the comparison needs the closed-loop worm (challenge i), not the brain-only run.
  Uzel 2022 (immobilised) is the brain-only cross-check, if Ben or a browser can fetch it, once it is confirmed
  not to reuse Kato's animals.

## Backhouse speed (question 3, report only, 14:46-14:50)

Verdict: the build and the WSL configuration match the Mac; the slowdown is contention on a shared machine.
Nothing on Windows or the throttle was changed.

- NEURON 9.0.2 in both venvs. The mod compile flags are the same: `nrnmech_makefile` lines 62 and 67 give
  `CXXFLAGS = -O2 -std=c++17` and `CFLAGS = -O2 -std=c17` in `~/worm-port/.venv` and in the Mac's `.venv`.
- `.wslconfig`: memory 48GB, vmIdleTimeout -1, no `processors` line; `nproc` in WSL is 28.
- vmmemWSL: ProcessorAffinity 0xFFFFFFF (all 28 logical CPUs), priority Normal (outside the 17:00-22:00 window).
  Power plan High performance; i7-14700K, 20 cores and 28 threads (8 P-cores with hyperthreads, 12 E-cores).
- The same point (hsn_5ht_point.py, 40 pA, 8 bio-s, identical outputs): Mac 3.85 s, backhouse 8.38 s at load
  11.8 (2.2x, measured). The probe_5ht template point (62 bio-s, one process, load about 16) took about 3.7 min
  from process start to the pool start (derived from ps etimes), about 7x the Mac rate.
- At 14:49 Windows reported 99% CPU load, with Roblox running and another project's job (crucible, 3 days old) in
  WSL beside mine. Past 8 busy processes, extra ones share a P-core's hyperthread or land on an E-core.
- For phase 5's EKI cost: plan on 2-7x the Mac's single-process time per process on backhouse when it is shared
  (measured range today). An idle-machine figure was not measured today.

## Open

- AWA amplitude after the Kir fix (39.8 mV vs 25.8): Liu 2018's Ca gating forms are images in the preprint;
  Table S4 matches the port value for value.
- AFD under FIT2's map; FIT2's true map losing to shuffled maps.
- Backhouse's 4-7x slowdown: contention, not configuration (section above).
- The 13 BAAIWorm cells at 5.6-7.8 GOhm (challenge v, settled 14:41, a few minutes): not a units slip in our port.
  Upstream applies the JSON's gpas as `seg.pas.g = params[2]  # Passive conductance in S/cm2` on every section
  (BAAIWorm clone on backhouse, `eworm/single_nrn_tune/neuron_model.py:76-79`); brain.py:445-447 does the same, on
  byte-identical morphologies (NOTICE.md). AIYL's gpas is 1.4e-5 S/cm2 in BAAIWorm's own file. So their high input
  resistance is BAAIWorm's fit, and line 16's remainder stays E (bar not a law), not A. Side finding, open: the same
  upstream tuner inserts `cainternn` (Nicoletti's nanodomain Ca, `neuron_model.py:84`; `cainternm` commented out),
  while upstream's network (`eworm/network/detailed_circuit.py:262`) and our port run `cainternm`. If the cell fits
  were made with the nanodomain pool, the Ca-activated K channels at rest saw a different Ca than they see in the
  network. Relevant to line 19's build; not checked further today.

## Questions for Ben (answered by the Director from Ben's standing direction, 14:45)

1. Egg-laying (line 5): (b). Phase-2 spec: port HSN's published biophysics from free sources (its channels, at
   CeNGEN expression, with its Ca and the feedback the circuit already has: VC cholinergic input, uv1 tyramine and
   NLP-7/FLP-11, uterine stretch). Zhang 2010 and Collins 2016 are the check, never the mechanism; no state machine.
2. Nicoletti 2024's forms (line 1): (a). Phase-2: write the EGL-19 and SHL-1 mods from the CC-BY paper's equations,
   with a check that the mods reproduce one of the paper's figures. Contacting the authors stays Ben's call.
3. backhouse speed: (a), done in under 10 minutes (section above): contention, not configuration. The egg probe is
   set up as a detached backhouse job (PID 82978, `~/worm-night/wtriage/runs/egg_night.sh`): it sleeps until 22:00,
   then 16 single-thread workers over 64 points with the 20 ids (line vi's 5-HT gaps added), a 16 h timeout, and
   `runs/egg_night.done`. Expected about 10.5 h (4 rounds of about 2.6 h, derived from the 14:10 rate), so it ends
   Monday morning; the timeout stops it by 14:00 Monday, before the 17:00 cap.

## Phase 2 status

One line per triage line, by the worker that owns it. Night files hold the detail.

- Line 15 and 16 (wbrain2, A): `expression_map=on` keeps published-fit densities whole (old form `cengen_all`). AIYL training RMSE 113.8 -> 9.28 mV (bar < 16.6: pass); cells above the highest reversal 70 -> 16 (bar 13: missed by 3, AUAL, AUAR, ADAL at +40 pA only, E like the 13); rest above -30 mV 8 -> 0. AFDL 26.8 -> 43.4 mV (FIT2's job).
- Line 3 (wbrain2, A): UNC-49's own closing time derived, 19.16 ms (was the composite 24.8). Composite IPSC 29.2 -> 24.8 ms (bar 22.1-27.5: pass). New, open: the NMJ ACh current decays in 12.2 / 17.6 ms (ACR-16 / L-AChR) against 5.6-7.4 ms, 9.3 / 15.3 ms even with a 0.5 ms receptor: the shared release state is too slow there.
- Line 7 (wbrain2, A for the Kir, D for the rest): `awa_kir smooth_min` (default) is the Kir in the authors' code (github.com/wormwhisperer/CElegansAWAActionPotentialAnalysis), gKir times the smooth minimum of (v - vK) and I0; `as_printed` kept. Rest -64.56 -> -76.16 mV (bar -75.3 +- 4.7: pass); amplitude 33.9 -> 39.8 mV (bar 25.8: fail). What remains is the published model's own: the code differs from the printed equations in four more places, and its whole form does not spike in Liu's window, deterministic or with its channel noise. Candidate C (the code's form as an `awa_liu_form` toggle) recorded in the night file, not ported: it makes AWA silent.
- Lines 19 and 17 (wbrain2, item 4; C for the tuner's Ca, B blocked for the bulk pool): the cainternn question is not a bulk-pool question. BAAIWorm's tuner (`neuron_model.py:63-108`) fitted every cell with `cainternn` (Metaworm `modfile_d`: Nicoletti's nanodomain with gbcav = the cell's summed SLO density in nS/um2 where the 40 pS single-channel conductance belongs) read by the SLO mods, and without KCNL; the network's SLO mods (ours) each use gsc 40 pS. Over the 220 cells with SLO the tuner's SLO Ca was 0.104x to 1.5x the network's (median 0.147x, derived). New toggle `slo_ca_source`, default `single_channel`, form `tuner_gbar` (cainternn reproduced exactly). FIT2 training sweeps: AIYL RMSE 9.28 -> 10.68 mV under `tuner_gbar` (bar: a change of 0.5 mV or more means the densities depend on the form; it does, and the network's form fits better); AFDL and AWAL identical (no SLO). Default kept. KCNL: 88 network cells at two values (0.00063, 0.005 nS/um2) that the tuner never fitted; recorded. Bulk pool: no published C. elegans neuron form with a slow clearance in the sources opened (Nicoletti 2019; Mirzakhalili 2018 S1 Table: cytosol clears in about 40 ms, derived; Kuramochi and Doi 2017: soma 3.7 s, a fit to the imaging signal itself, not Ca; Sherman and Harel 2024 as ported: pharyngeal muscle, both pools 50 ms). Building one would set its clearance from Ding's check, so line 19 stays B, blocked on a source; line 17 follows it. Night file `docs/worm/night/2026-11-08_wbrain2.md`.
- Line 1 (wbrain2, B as switches; the figure bar failed, cause found): no new mod file was needed. Nicoletti 2024's
  printed EGL-19 and SHL-1 equations (S1 File, CC-BY) are BAAIWorm's forms term for term with other constants, so
  `mech/channel_forms` adds `egl19_kinetics` / `shl1_kinetics` = off (BAAIWorm, default) / n24_printed / n24_code,
  and `brain.patch_shl1_form` makes SHL-1's exponent, weights and tau factors GLOBALs (off is bit for bit). The
  row's EGL-19 entries were the code's raw numbers before its 10 mV shift and pds2 factor: -10.54 + 10 shift = -20.54
  mV, 0.55 x 81.1 = 44.6 ms, the same as BAAIWorm. Measured: n24_code equals the authors' channels alone in voltage
  clamp (EGL-19 1.8e-16, SHL-1 1e-7 relative); ref vs digitised Fig 3C 0.12 mV; n24_code vs Fig 3C 4.08 mV against
  the pre-registered 2 mV: **fail**. Cause: the authors' model runs at E_Ca 127.6 mV (NEURON's Nernst value at
  finitialize overwrites the script's eca = 60) and BAAIWorm's SLO-1 nanodomain hard-codes 60 mV; with E_Ca held at
  60 in both, n24_code plus the authors' unrounded SLO-1 constants reproduces their AIY model to 0.004 mV. Default
  unchanged. Detail: docs/worm/night/2026-11-08_wbrain2.md, "Line 1".
## Phase 2 status (wbody2)

- Line 11 (A), fixed 20:22 8 Nov: driver rebuilt; `metaworm.ensure_driver` refuses a binary older than its sources.
  Line 9's damping re-run on the Mac: 16.70 ms (bar <= 5.3; unchanged from backhouse, line 9 stays D).
- Pumping (vital sign; wbody2 item 2), 20:53 8 Nov: two stops in series. (1) MC never fires (MCL -70.1 mV median
  over 3 bio s, whole brain; brain-owned, request to wbrain2). (2) Downstream is B: brief MC events (4 Hz) make no
  pump at any in-range value of the marginal gap, marginal area or NMJ per-contact conductance (probe, 24 points);
  the model's MC step is a generic graded synapse onto passive marginal cells where the published step is the EAT-2
  nicotinic synapse (McKay et al. 2004), and the muscle's CCA-1 does not recover between events at its in-situ rest.
  Fixed on the way (A): the muscle read 5-HT from a pool that is 0 under neuromod. Off-food bar: about 50 pumps per
  minute in the first 2 h off food (Dallière et al. 2016, PMC4714553).
- Defecation (vital sign; wbody2 item 3), 21:26 8 Nov. "~20 s, irregular, same with and without food": the loop's
  int9 is the max over 20 cells (E, request to wtriage), and the oscillator has no food input (B; published: off food
  the program is "rarely activated", Liu & Thomas 1994). check_intestine scored the first wave only (E, fixed); at the
  defaults 1 of 11 waves reaches int2 (D: 1 of 1000 in-range sets passes, not adopted). No expulsion: NLP-40 tonic at
  DVB and AEX-2 with no Ca route (neuromod, request to wbrain2); the enteric muscles fire at about 4 Hz on the Du BWM
  membrane, so no AVL/DVB drive makes an expulsion (B, 0 of 16 drives). Q10 per-temperature data not free (row 25).
- Food changes nothing (wbody2 item 4), 21:35 8 Nov. Traced on the pharyngeal sub-brain (20 s, food_OD 1.02 vs 0):
  NSM depolarises 25 mV, the head 5-HT rises 70-fold to 1.05 nM, MC's SER-7 Gs 0.0005 -> 0.033 (the published route,
  Song & Avery 2012), pumps 0 -> 0 because MC is silent (item 2). NSM's soma Ca does not rise (brain, request). Basal
  slowing (dopamine, a mechanical attribute of bacteria, Sawin 2000): the lawn has none, B. DMP has no food input, B.
  No class A of mine. Food enters by senses_chem's TRPV conductance, not brain_layers:310's current (text above).
- BWM rate and rest (wbody2 item 5), 21:45 8 Nov. The loop's 1.96 Hz against Gao & Zhen's dissected 0.73 +- 0.14 Hz
  is not like for like: those APs are mostly driven by the kept cord (ACh block removes about 88 %; unc-13(lf) 0.04 Hz).
  Scored at the cell instead (E): the row 12 check held the cell at rest for only 57 ms; with 20 s of zero input the
  default Du cell fires 4.27 Hz at -21.5 mV (fail). 68 of 4000 in-range sets pass the steps and stay silent, at fixed
  points of -35.6 to -24.4 mV (20 saved): D, not adopted. Rest -30.2 vs -25.0 mV is inside that span (no separate fail).
- Line 20 compartments (wbody2 item 6), 21:54 8 Nov. organs_other now segments by NEURON's d_lambda rule (hyp 35,
  exc_cell 5). DC neutral: 69 gap partners move at most 0.32 mV, organ cells 0.02 mV (bar 0.5 mV); hyp's input
  resistance rises 1.29x as derived, swamped by its own 160 nS. BWM somata (brain.py's sections, nseg 1): nseg 3
  moves no Du spike by more than 0.1 ms, so the 1.45x shortfall has no effect; optional request to wbrain2.
- Line 10 stiffness (wbody2 item 7), 21:59 8 Nov. The approved rule parameter exists: rule_body_modulus_scale
  (template 1, neutral; range 0.058-1.35). 0.061-0.194 gives 50-170 kPa (D, not adopted). The sources alone do not
  overlap (Frontiers 776-1157 kPa vs Backholm 50-170), so C stays for the template; the fit runs both ways
  (body_layers frontiers2024 / backholm2013). Found: the mesh quadrature misses the outer layers (4.6 % vs 38.5 % of
  the bending weight), A, mine, open.
- 8 Nov 22:21 (wbody2, line 4, E done + A found): check_glia's bars re-cited from opened sources (ceiling 10.2 mM
  absolute, Heinemann & Lux 1977 abstract; tau 3.4-4.0 s and null >= 1.24x, Sibille et al. 2015 Fig. 4B, F, simulated
  mouse [K+]o; sides dropped, no source, replaced by tests/test_worm_glia_sides.py). No C. elegans K+ measurement
  exists (Ray et al. 2024 Cell Rep, PMC11296322). Defaults: ceiling pass, tau 1.25 s and null 1.11x fail (measured).
  Cause: glia.py's rest reference v0 (first 1 s) lets the drifting network make a steady false K+ sink, 0.36 mM below
  the bath by 24 s (A, wbody2, open); the post-release undershoot to -66.7 mV speeds the fall. D not decidable until
  the A is fixed. wtriage's 64 points under the new bars: 0 pass (from-bath taus).
- 8 Nov 22:50 (wbody2, line 10, A fixed): layers.tet_moduli's quadrature now carries the outer layers. The layer
  coordinate is r / R(z, theta) with R ray cast from the body axis to the mesh surface, and each tet is sampled at its
  512 equal-volume sub-tet centroids (was 4 points per tet and R the slice's largest vertex radius). Bar (mesh section
  modulus within 5 % of the ideal shells): 791.1 vs 794.2 kPa at the template, 323.6 vs 324.4 depressurised (was +7.8 %
  and -60.7 %): pass (measured). The default body is 7.6 % softer in bending. Frontiers 561-1199 kPa vs Backholm 50-170:
  still no overlap (C stays); rule range re-derived 0.0632-1.515; 0.067-0.214 reaches Backholm (D, not adopted).
  Line 9 damping re-run on the fixed body: 16.46 ms vs <= 5.3 (still D).
- 8-9 Nov 23:52-00:39 (wbody2, items 2, 3, 15). Organ chemical synapses (A, 9a67a6f): the pharynx, enteric and
  egg-laying synapses from brain neurons were always BAAIWorm's graded synapse, so no wsyn gain reached them; they now
  take the brain's receptor form and are listed in brain.wsyn (off bit-identical, graded within 3.3e-10 mV; release
  gains reach them only once the brain builds its synapse gains after the mechanisms: request to wbrain2). NLP-40
  site (A, 7daea89, wneuro's request): each intestinal ring releases into the neuromod compartment it lies in (was all
  20 cells next to DVB); total unchanged to 8.9e-16; the tonic part and nlp40_tau_s are D. DMP trace on the merged
  code (150 s, backhouse): int9 peaks 34.82 / 86.85 / 136.62 s, AVL / DVB max -33.4 / -32.2 mV, 0 expulsions,
  enteric activation max 0.272 vs the 0.5 detector (measured; unchanged from before the merge). Item 3 chain stays B.
- 9 Nov 00:30-00:56 (wbody2, item 2 stage 2, MC -> muscle). Ported EAT-2 as the toggle `ph_mc_route` (cook default =
  Cook's MC -> mc2 synapses; eat2 = those contacts on the pm5 cells each mc2 borders, nicotinic at the ledger NMJ;
  both). Not adopted: `pharynx_stage2_check.py` (bars written before the port) passes neutral (max dV 0) and muscle
  alone (400 pA x 40 ms per pm5 cell, 1 pm4 AP per input), fails effect (0 of 10 MC pulses pump; pm5 EPSP 13-17 mV
  from -65 mV), latency (9.0 ms vs 5.0-8.4, no AP) and the eat-2 null (1.62 mV vs 1 mV, through MC's partner
  neurons); whole brain 1 of 10 (all measured). No NMJ in range passes: 1 and 2 nS raise the rest to -37 and +4 mV
  before any pulse. The coupled pharynx rests at -65 mV (measured -73, Steger 2005) because MC's plateau on main
  (-42 mV, wbrain2: D) and M4 and M2 release onto it all the time; with the old mask (MC at -67.5 mV, a
  counterfactual) the EPSP is still subthreshold. Stopped and written down: the MC -> muscle strength has no
  published conductance, so it is a fit after the gate.
- 9 Nov 01:09-01:42 (wbody2, item 8 / line 4, the glia K+ load port). Ported Sibille et al. 2015 eq. 25 as the
  toggle `glia_k_load` (leak default | channels: the amphid neurons' gated K+ currents load the ending, E_K follows
  its K+ on their K+ channels) and `glia_v0_window` (first default | settled, 1-2 s). `glia_port_check.py`: neutral
  and identity exact; zero-input drift over 20 s 0.316 / 0.038 / 1.03 / 0.223 mM (only leak/settled inside 0.05);
  check_glia fails in every form (tau 1.24-1.76 s vs 3.4-4.0, null 1.11-1.23x vs 1.24, channels peak 12.4-13 mM vs
  10.2; all measured). Stopped and written down: the clamped neurons take K+ back after release, so recovery runs
  2-3x faster than the guessed clearance constants; the passing value is a fit after the gate. Defaults unchanged.
- 9 Nov 01:47 (wbody2) the vitals battery on 7daea89 (organ synapses and NLP-40 site in): food / nofood pumps 0 / 0,
  expulsions 0 / 0 (int9 every 50.9 s), eggs 0 / 0, BWM -30.5 / -31.1 mV at 1.90 / 1.84 Hz over all muscles,
  physical yes; against the fbf1c91 loop no vital sign moved (all measured).
- 9 Nov 01:47-02:01 (wbody2, inbox 01:45 from weki, A numerical). egg_laying's LGC-55 on HSN and vm cation term, and
  intestine's PBO-5/6, were g (E - V_start) held as a current over the 4-4.5 ms exchange step (explicit in V). Each is
  now a wgc point process solved implicitly by NEURON (toggles `egg_g_solver`, `pboc_g_solver`: implicit default,
  explicit nested). `implicit_g_check.py`: explicit identical to the code before; at 0.1-0.5 nS implicit is closer to
  a 0.5 ms reference than explicit (6 of 6); at each range's top and 2x implicit is stable, explicit goes to NaN on
  HSN at 5 nS and alternates at vm cation 14 and PBO-5 20 nS (all measured). Battery on the new default next.

## Phase 2 status (wneuro)

- Item 1, the defecation chain (wneuro): (c) A, fixed: `neuromod_site=membrane` reads receptors over each cell's
  membrane by area per compartment (AVL has 79% of its membrane behind its head soma, DVB 71% in the posterior body;
  measured), release stays at the soma; AVL's NLP-40 read rose from 0.86 to 104.4 nM (max) and its AEX-2 occupancy
  from 0.10 to 0.63 (measured, 150 s). (b) B: Gs now also raises UNC-2 (Wang and Sieburth 2013), `gs_ca_channels`
  with `egl19` nested; the rest is blocked: the third PKA target is unnamed in the source, and DVB's membrane cannot
  fire (Gs clamped at 1: no spike; 20 pA: plateau at -19 mV against Jiang 2022's +26.3 mV peak), a request to
  wbrain2. (a) D at the bottom of the clearance range only (tau 10 s, with a release shape at the corner of wbody2's
  ranges); in the brain it fails at every probed point because the intestine's release is tonic (8% of maximum at
  basal Ca, derived) and follows the 20-cell mean, not int9: a request to wbody2. Wang 2013's bar (one DVB spike per
  cycle) still fails: 0 spikes. Line 13 (E): the GABA bar now rejects 5 Hz facilitation (Liu 2009); the D proof
  stands (2 of 256 triage points pass the corrected bar, measured). Night file `docs/worm/night/2026-11-08_wneuro.md`.
- Item 6, amines against receptor potency (wneuro): every amine pair is near off at rest and on food (highest
  occupancy SER-7's 0.028 on food, measured). Store: the template's shared 1e6 molecules per cell was 11x (5-HT) and
  43x (DA) below whole-worm LC-MS/MS content (Weishaupt 2023, derived); ported per amine (B), which leaves rest levels
  within 5% (measured). Release rate per cell (guessed 1e5 per s): D, a probe finds MC's SER-7 at EC50 at 8 of 256
  in-range points, all with release >= 1.35e6 per s; not adopted. SER-1, SER-4 and SER-5 EC50s are guessed (1000 nM)
  and no probed point reaches SER-1 at the vulva (at most 160 nM, derived), so egg-laying cannot answer 5-HT through
  SER-1 from the pool. Pool geometry is outside its well-mixed range (compartments 2-5 length constants long) but a
  1D bound puts the near-source excess at 1.9-2.5x, not the 35x gap: A, open. SER-7's EC50 (30 vs 32 nM) is not C.
- Session 3 (wneuro, 9 Nov): SER-1's EC50 found and ported, 1340 nM measured (Xie 2005 via Dernovici 2006), so it is
  no longer a gap value; the vulval pool's box maximum is 0.12 of it (derived) and HSN's synaptic release onto vm2 is
  the deciding unknown. Open 5 as a C toggle `dmsr1_isoform` (FLP-25 on DMSR-1: isoform B 0.6 pM, the default, or A
  1.6 uM): line 14 passes under both, but under the default DMSR-1 is saturated in every head cell that expresses it
  (head FLP-25 30x B's EC50), and the choice moves resting Gi by more than 0.1 in 198 cells (measured). Not adopted.
- Session 4 (wneuro, 9 Nov): Open 7 far field as an A toggle `pc_grid=bins` (pool bins of 8 um inside each named
  compartment, chosen by convergence): within 3.7% of the exact 1D solution where the four compartments read 0.39x at
  HSN's source (measured, pre-registered). Live, the vulval 5-HT read rises 3.2x (0.38 -> 1.20 nM off food) and MC's
  SER-7 Gs 1.7x on food; still 0.04 of SER-7's EC50 at the vulva. Default four until the Director adopts. HSN's
  synaptic near field onto vm2 is B blocked on geometry sources (Nicholson's form exists; derived bound in the night file).
