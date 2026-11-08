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
| 5 | Egg-laying pattern | 15 | >= 3 clusters, intracluster 5-60 s, intercluster 10-60 min (Collins et al. 2016 eLife; Zhang et al. 2010) | no eggs; HSN -53.6 mV, 0.65% of time above -30 mV; vulval 5-HT 0.33 nM vs SER-7 EC50 30 nM | B | Zhang, Schafer & Breitling 2010 (PMC2887794): HSN is an autonomous two-state oscillator gated by VC (~20 s) and uv1 (~20 min). Ours is BAAIWorm's HSN membrane, silent alone. Even full HSN drive gives 15 nM 5-HT (derived) | not run: 2.6 h per point (measured), 17 h for 64; phase-2 spec | body | large |
| 6 | Excretory canal swelling | 16 | canal-null t90 12-24 h (Nelson & Riddle) | 10.66 h | D | analytic band Lp x E = 2.75e-5 to 5.33e-5 /s | 17/128 (13%), 13 off edges | body | small |
| 7 | AWA spike and rest | 17 | rest -75.3 +- 4.7 mV, amplitude 25.8 +- 0.8 mV (Liu et al. 2018, bioRxiv 359935) | rest -64.6 mV; first spike 39.8 mV | A | the ported Kir (awa_liu2018.mod:108, senses_checks.py:115) is inward at every voltage (-4.0 pA at -50 mV), impossible for K+ above E_K. Read as an outward smooth minimum: rest -76.1 mV. Amplitude stays high after the fix (Open) | | brain | small |
| 8 | DVA stretch response | 17 | DVA > 0.5 at a half-body bend (sanity bar, no source) | 0.483 | D | DVA reads mean abs curvature over the whole body; half bent gives strain 0.098, on eps_half 0.1 | 23/128 (18%), 19 off edges; passes need eps_half < 0.097 | brain | small |
| 9 | Body damping | 21 | mean tau <= 5.3 ms (Fang-Yen et al. 2010, derived) | 16.70 ms | D | w_ref 10 rad/s was derived for ~1 rad of swing the stiff body never makes | 27/64 (42%), 20 off edges | body | small |
| 10 | Bending stiffness | 21 | 50-170 kPa (Backholm et al. 2013, 110 +- 30 kPa whole worm) | 856 kPa | C | layer moduli are Frontiers 2024 indentation values; Backholm is whole-worm bending. Two measurements of one body | | body | medium |
| 11 | Mac run_body binary | 21 | (tooling) | ignores --damping | A | `third_party/metaworm/driver/run_body` built 6 Nov 20:29, before the damping commit a6f75cf (21:46). Fix: rebuild; metaworm.run refuses a binary older than run_body.cpp | | body | small |
| 12 | Opto actuator | 23 | AVAL dv > 1 mV after a 0.5 s pulse (no source) | fails at the ledger | D | the real calibration is Randi 2023's autoresponse (item 4b) | 20/32 (62%), 14 off edges | body | small |
| 13 | GABA short-term plasticity | 24 | plateaus > 0.8 at 1 and 5 Hz, 20 Hz second/first > 1 (Liu et al. 2009) | fails at the ledger | D | 8 guessed stp_gaba gaps | 24/256 (9%), 10 off edges; best 1.13 / 1.75 / 1.25. The bar accepts 5 Hz facilitation Liu did not report | brain | small |
| 14 | RIS Gi without DMSR-1 | 28 | Gi == 0 with dmsr-1 removed | 0.062 | E | 25 other peptide GPCRs CeNGEN puts on RIS (largest nlp-13, Gi) still see peptides. Rossi et al. 2025 (PMC7617803) does not say DMSR-1 is RIS's only Gi route. Fix: bar on the DMSR-1 share | | brain | small |
| 15 | Own ephys, AIY / AFD / AWA (item 3) | 5 | FIT2 features on the training sweeps (Naudin 2022, Liu 2018); RMSE, FIT2 best 16.6 / 10.5 / 13.7 mV | AIYL 113.8, AFDL 26.8, AWAL 16.3 mV | A | brain.py:427-433: the CeNGEN mask deletes 8 of BAAIWorm's fitted AIYL channels (egl2, shl1, kqt3, kvs1, irk, egl36, cca1, shk1). Mask off: AIYL 9.3 mV. Fix: leave BAAIWorm-fitted cells unmasked until FIT2's map or a refit replaces them | | brain | medium |
| 16 | 121 unphysical single cells (4a) | 3, 5 | upper/lower voltage bars at +-20 pA (wexcite) | 74 upper, 47 below -150 mV | A | 61 of the 74 come from the same mask (13 with it off, all BAAIWorm's own cells at 5.6-7.8 GOhm). The bars are not laws: recorded AIY reaches -125.6 mV at -15 pA, RIM +75 mV at +35 pA | | brain | medium |
| 17 | ~30x deficit vs Randi (4b) | 23 | autoresponse 30 s mean dF/F, training median 0.43 (Randi 2023) | 0.014-0.018 | C | the response peaks (0.24-0.31) but decays in ~3 s: the readout's decay (line 19), not excitability. Gaps at their tops give 0.08-0.11; adding capool tca 150 and f 0.003 gives 0.64-1.09. AVAL stays 0.048 (1.19 pA Ca current into 129 um3) | | body | small |
| 18 | Saturated vs silent network (4c) | 2, 8 | no published bar for a fraction of neurons above -20 mV | open loop 0%, median -50.3 mV; synapses x4: 7% | E | the "swing" (197, 94, 0, 16% of 302) compared different builds and drives. Same build, every synapse x0.5 / x2 / x4 gives 0 / 0 / 7%: not a knife edge | | brain | small |
| 19 | GCaMP decay (4d) | 23 | GCaMP6s half-fall 8.4 +- 5.0 s in vivo (Ding et al. 2023 G3, PMC10542313, Table 1) | 0.64 s (13x fast; 2.06 s at both range tops) | C | Nicoletti 2019's tau_Ca 50 ms is a submembrane pool fitted to AWC currents; Ding's is in-vivo bulk decay. Both inputs are scan values; not reachable in range. Toggle: a slow bulk pool the indicator reads | | body | medium |
| 20 | Compartment convergence | 3 | segments <= 0.1 lambda_AC at 100 Hz (NEURON d_lambda rule) | 97 of 2,253 sections short, none in neurons | B | hypodermis one 5,093 um compartment (needs 35, 34x), excretory cell (needs 5), BWM somata 1.45x | | body | small |
| 21 | Viewer 8/20 vs audit 13/15 (item 6) | 4, 6, 14, 19, 24 | the two counts | 8 vs 13 full | E | the viewer calls a split row "simplified" if any part is lumped; the audit files it under its main category. The 5 split rows explain 13 - 5 = 8 | | brain | small |

Class counts (table lines 1-21): A 5 (lines 3, 7, 11, 15, 16); B 2 (5, 20); C 5 (1, 2, 10, 17, 19); D 5 (6, 8, 9,
12, 13); E 4 (4, 14, 18, 21). Lines 15 and 16 share one cause (the mask). Only line 5 (HSN) is large.

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
  than Ding's 8.4 +- 5.0 s, not 4x. The best inside the ranges is 2.06 s, below Ding's -1 SD (3.4 s). C.

## Item 5: vital signs

(filled after the two 120 s runs; see below)

## Item 6: viewer vs audit

The viewer marks a split row "simplified" when any part is lumped or missing; the audit files it under its main
category. Rows 4, 6, 14, 19 and 24 are split: full in the audit, simplified in the viewer, so 13 - 5 = 8.

## Open

- AWA amplitude after the Kir fix (39.8 mV vs 25.8): Liu 2018's Ca gating forms are images in the preprint;
  Table S4 matches the port value for value.
- AFD under FIT2's map; FIT2's true map losing to shuffled maps.
- Why backhouse ran the egg-laying check 4-7x slower than the Mac did on 7 Nov (525 s wall per 10 bio-min).
- The 13 BAAIWorm cells at 5.6-7.8 GOhm: BAAIWorm's own fits or a unit issue in its leak (AIYL leak 0.012 nS vs
  Nicoletti's 0.14 nS).

## Questions for Ben

(see the night file's last entry and the final reply)
