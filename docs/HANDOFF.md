# Handoff: current state

**Rewritten each session; do not append.** State as of 2026-11-05 16:52 CST, end of the worm BRAIN + LEDGER
worker's afternoon block (Director session director-20 relays Ben). A second worker, the BODY worker, owns body,
viewer and video in worktree `.claude/worktrees/wormbody` (branch `worktree-wormbody`); its state is in its own
commits, not here.

- **Direction (Ben, 5 Nov; Director 15:05 and 16:25).** Port BAAIWorm and c302 wholesale and run them as published
  first; extend to all 302 neurons; add every missing layer at guessed values with toggles for the uncertain ones;
  build the ledger FROM the ported code; literature wins over ported values, labelled. **Thursday 12 Nov bar:
  known values implemented, everything labelled, everything else guessed as a placeholder; physiology "absent"
  goes to zero.** Day plan: `~/director/logs/day-2026-11-05/WEEK.md` (Fri 6 CeNGEN channels, synapses, gaps,
  peptides, monoamines, closed loop; Sat 7 remaining layers; Sun 8 `sample_worm(seed)` draws and guardrails).
- **Read first:** `docs/worm/STRATEGY.md`, `docs/worm/BRAIN_PORT.md` (sections 1-3: every port run and its bars),
  `docs/worm/INTERFACE.md` (brain-body contract, cost, muscle map, toggles), `docs/worm/ADOPTED.md` (credits and
  licences), `docs/worm/ledger.json` (the catalogue of numbers), `docs/worm/SCOREBOARD.md`.
- **The fly is paused.** Its HANDOFF is archived in `docs/archive/HANDOFF_fly_2026-11-04.md`; its register is carried
  below unchanged.
- **The W1 track (Jaxley RIM/AFD fits) is parked** by the port direction; see "Parked" below.

## Report for Ben (brain and ledger, 5 Nov afternoon)

- **The ledger is built from the ported code and has one absent physiology number left** (measured counts, `docs/worm/ledger.json`):
  89,020 numbers; physiology 18,033: published fit 7,058, guessed 10,668, derived 282, inferred 11, measured 13,
  absent 1 (`gap_innexin_unitary`, mechanism `innexin_identity`, not implemented yet). Every row carries
  `source_project` (BAAIWorm / c302 / ChannelWorm / Sibernetic / literature / ours) and `fill_kind` (measured /
  published fit / derived / guessed). Every per-pair synapse and gap strength has a guessed placeholder inside a
  cited range.
- **`src/wormemu/brain.py` is the brain the closed loop will use:** `sample_worm(seed)` and `Brain(spec, toggles)`
  with `reset()`, `step(obs, dt_ms=1.0)`, `cell_names` (302 neurons + 95 muscles). With literature overrides off it
  reproduces BAAIWorm's own construction (port302a) to **0.0 mV** in every cell at every 1 ms sample (run `ref`).
  Cost **3.75-4.10 s of wall per biological second**, one thread, about 0.2 GB (measured, backhouse).
- **Ca units fix** (BAAIWorm reads uM as mM; E_Ca about +42 mV instead of about +130): fixed inside
  `literature_overrides`, E_Ca +133.8 mV at rest (derived, measured in the smoke test).
- **Wiring answer:** BAAIWorm's neuron-neuron counts are Cook 2019 exactly (not c302's deprecated sheet), but its
  construction places sites on only 2306 of 3709 chemical and 599 of 1091 gap pairs, uses its own 552-pair NMJ
  table (337 are Cook edges, Cook has 956) and adds 175 non-anatomical muscle-to-neuron synapses. `wiring=cook`
  (every Cook pair, labelled with its source) passed its pre-registered bars and **is now the default**.
- **Muscle map verified:** `MCDL01` -> `dBWML1` etc., `MCVL24` dropped (the worm has 95). 337 Cook edges under this
  map against 309 / 278 / 26 for shifted or swapped maps (measured).
- **The network still saturates.** Neurons above -20 mV at 6 s: 180 as published, 141 with literature overrides
  (the pre-registered falsifier line was 150, so not triggered), 188 with Cook wiring. The touch input reaches at
  most 9 other neurons by 1 mV and no muscle. Under Cook wiring it follows the anatomical path (PLM to PVC, LUA,
  PVR, PDE). **G3 as first written passes by drift alone** (no-input controls "move" 146-180 neurons); the scores
  stand under the stricter stim-minus-no-stim reading. Figures `data/worm/brain_runs/bw_*/traces.png` (viewed).
- **Caveats:** the gap override is about 27x the ported per-EM value and rests on a guessed range (C4); the
  receptor-sign rule (off) would flip 1125 of 3709 pairs; every `syn_strength_per_pair` template value sits at
  the 0.1 nS lower bound, so lognormal draws clip about half the time; `muscle_active` and `gap_rectification`
  raise NotImplementedError if switched on.

## Running now

Nothing of mine, on the Mac or backhouse (checked 16:51). Other projects' jobs on backhouse (crucible, a worm-data
download): leave them alone.

## Next (this order)

1. **Saturation is the brain's top open question before the closed loop.** Pre-register a diagnosis in
   BRAIN_PORT.md section 4: which of synapse strength scale, graded-synapse thresholds (`syn_*_Vth`), missing slow
   K+ / homeostasis, or the BAAIWorm densities drives about 190 neurons to a flat -20 to +10 mV. One factor at a
   time, neural only, same 6 s protocol, matched no-stim controls. Measure the touch effect as stim minus no-stim,
   not G3 as first written.
2. **Implement `innexin_identity`** (gap rectification and innexin-specific unitary conductance) so the last
   absent number gets a guessed value; wire `gap_rectification` and `muscle_active` (c302 C2 muscle channels) into
   NEURON.
3. Friday's list (WEEK.md): test `expression_map` on the full brain; peptides and monoamines on; the closed loop
   with the body worker's body through `INTERFACE.md`.
4. Sunday: `sample_worm(seed)` guardrails (draw many worms, reject non-physiological ones by a pre-registered rule).

## Parked: W1 (Jaxley RIM and AFD fits)

`w1m1` (M1 passive fits) ran on backhouse in the night of 4-5 Nov and was never collected: outputs in
`~/worm-spike/runs/w1m1/` (`rim_m1/fit.json`, `afd_m1/fit.json`, logs). Collect with the base64 loop in git
history (this file at commit a8275f3). Do not score M1 alone. The held fits wait for `kcnl2` (Q3 failed: KCNL Ca
pool, Jaxley vs NEURON 1.95 mV RMS on a cable against a 0.01 mV bar; `docs/worm/W1_RIM_AFD.md`). The RIM and AFD
held-out sweeps are still unspent (register below).

## Where things are

- **Brain code.** `src/wormemu/brain.py` (NEURON brain, sampling), `brain_layers.py` (specs and lumped dynamics of
  every layer no project has), `brain_structure.py` (Cook, CeNGEN, transmitters, muscle names), `interface.py`
  (the brain-body contract types). `src/bioemu/ledger.py` (organism-agnostic ledger: labels, priors, `draw`).
  Tests `tests/test_worm_brain.py`, `tests/test_worm_ledger.py` (11 pass, 3.2 s).
- **Ledger.** `scripts/worm/build_ledger.py` writes `data/worm/model/{mechanisms.yaml, parameters.csv,
  values/*.csv}` and `docs/worm/ledger.json`. Rebuild after any change to its sources.
- **Runs.** `scripts/worm/port/brain_runs.py` (`--run ref|port302b|port302c [--no_stim]`) and
  `plot_brain_runs.py`; summaries, figures and touch effects in `data/worm/brain_runs/bw_*/`. Traces (`run.npz`)
  are git-ignored; copies on the Mac under `data/worm/brain_runs/` and on backhouse under `~/worm-port/runs/`.
- **backhouse (WSL, user greff).** `~/worm-port/` (venv `.venv`: NEURON 9.0.2; `repo/` synced code, ship with
  `COPYFILE_DISABLE=1 tar czf - --no-xattrs <paths> | ssh backhouse "wsl -d Ubuntu -- tar xzf - -C
  /home/greff/worm-port/repo"`; `runs/`; `BAAIWorm/` and `c302/` clones; job scripts `brainruns_job.sh`,
  `brainruns_nostim.sh`). Compiled mods at `~/.cache/wormemu/nrnmech/x86_64`. Launch detached with setsid nohup
  and `sleep 5` before the SSH session closes, or the job dies. The Jaxley track lives in `~/worm-spike/`.

## Sealed and held-out data register

### Worm

| Data | Status | Rule |
|---|---|---|
| Naudin 2022 AIY current clamp (`Fig1A_AIY_CC.txt`, one cell), steps -15, -5, +5, +15, +25, +35 pA | seen (W0 spike training set) | training only |
| Naudin 2022 AIY current clamp, steps -10, 0, +10, +20, +30 pA | **spent** (W0 spike `fit1`, 5 Nov; also scored first on the 2-iteration pipeline test while `fit1` ran with frozen settings) | consistency only from now on; the same cell, so never a cross-cell test |
| Naudin 2022 AIY population voltage-clamp I-V (n 5-7; steady state and peak; `Fig1_IVcurves_AFD_RIM_AIY.xlsx`) | **spent** (W0 spike `fit1`; pipeline test before it). The table was read while writing the pre-registration (n per voltage, windows) | consistency only; the 2 SD band does not discriminate (F-W0-6) |
| Naudin 2022 RIM and AFD current clamp and I-V (same deposit) | file headers and the voltage-clamp `n` columns viewed. **Training sweeps 0, 2, 4, 6, 8, 10 now in use** (5 Nov 02:14 on: `fit_w1.py` smoke test `w1smoke`, then M1 run `w1m1`; training RMSEs printed). The held-out sweeps are dropped at load (`Vd = Vd[TRAIN]`) and no held-out or voltage-clamp value has been printed, plotted or used. The AIY loader read the whole I-V sheet into memory but used only AIY columns | **held out for W1**, split and bars pre-registered in `docs/worm/W1_RIM_AFD.md` (5 Nov 01:13): train sweeps 0, 2, 4, 6, 8, 10; held out 1, 3, 5, 7, 9 and all voltage clamp. Score once, all models together (see Next) |
| Nicoletti 2024 published AIY and RIM models (densities, kinetics, code) | seen; kinetics SET the channel library (22 channels); AIY densities SET one start of the spike fit and its baseline; RIM densities used as a port-check configuration (`port2`, 5 Nov) and, as registered, SET one start of `w1rim1` and its published-model baseline | can't validate the library |
| Randi 2023 functional atlas; Atanas 2023 whole-brain data; Witvliet 2021; Cook 2019; CeNGEN; the neuropeptide connectome | downloaded (`~/worm-data`, MANIFEST); Cook 2019 used as structure (the brain's default wiring since 5 Nov, the ledger's pair counts) and CeNGEN as expression (channel presence, receptor signs, modulator matrices); no activity data read | seed the held-out split (PLAN c.4) before the first fit that uses them |
| Behaviour corpus (`docs/worm/STATE_OF_THE_ART.md`, about 90 items) | read as a list of items; no outcome scored | seal about a third by seed before any behaviour fit (PLAN c.4, W2) |

### Fly (paused; carried unchanged from `docs/archive/HANDOFF_fly_2026-11-04.md`)

No sealed data was opened in session 11. Spent as held out for m7: closed-loop seeds 9-11, bitter->MN9_L, sugar+bitter (these had been spent in s10 for m5 too; seeds 9-11 were new). Seeds 12+ are fresh (12-13 reserved for the rung-1 G1 check, still unspent).

| Data | Status | Rule |
|---|---|---|
| Azevedo cell 180111_F2_C1 (slow MN) | seen (fit and dev) | dev only |
| Azevedo cell 181021_F1_C1, Piezo trials | **sealed** (unopened) | open only via `scripts/score_reflex.py` after a dev pass |
| Azevedo cells 180621_F1_C1, 181127_F1_C1, Piezo trials | **sealed spares** | as above |
| Azevedo CurrentStep trials (181021, 180621, 181127) | seen | none |
| Azevedo 2020 Fig. 3C/E per-type MN V_rest and R_in (fast 150, intermediate 300, slow 700 MΩ) | seen (s23 N2 reader, 24 Oct) | none while the recruitment order is held out: setting MN parameters from them would make that test circular |
| Agrawal 2020 13Bα static tuning | seen | none |
| Agrawal 2020 10Bα / 9Aα recordings | held out; not extracted. The papers' text statement that 13Bα/10Bα are nonspiking set the s13 S3 arm A `graded_rec` rows (mode only). The tuning recordings are untouched | don't use the spiking-mode statement as a check of arm A |
| PN spontaneous rate; PEN 3.9 Hz; KC 0.1 Hz | spent | none |
| flybench olfactory tasks 08/17/18/26/27 | held out for AL changes (m2 baseline 0.80); not run | m5 changes no AL class, but check before use |
| Command direction (MDN back, DNg100 forward) | spent on seeds 1-4 (s7) | new seeds and a gait criterion |
| eLife 2025 passive stiffness, fall onset | seen (s9) | rest-posture data (Fig 3C) unused |
| Wang 2025 silenced-fly fall time course (onset 40-300 ms, median 1.3 mm/s) | held out for standing option (b) (DECISIONS s12 18:23); model fall curves computed in an s12 diagnostic (F-DAMP-2), not compared for selection | choose nothing on it before option (b) |
| Azevedo 2020 twitch-kinetics text/figures | seen (s9) | raw recordings keep their status |
| Session 10 search fit set: template seeds 0-2, sugar->MN9 100 Hz | seen (fit) | none |
| Session 10 held out: template seeds 3-8, m4 body seeds 0-5, bitter, sugar+bitter, sugar 200 Hz | spent (m5 candidate) | new candidates need new held-out evidence |
| Wang 2025 standing head height (median 0.5 mm above collapse) | spent as a SETTING (s13 fly2, S1 fix 1 places the head at 0.929 mm) | can no longer validate standing height |
| Augustin 2017 S1 Table, GF→TTM latency (WT, brain stimulation) | seen (it set fly2's no-chemical-delay rule; F-GJ-3 used it only as a consistency check) | none |
| Augustin 2017 S1 Table, GF→DLM latency | spent on m10f + gaps (s13 fly2, F-GJ-3); DLMn silent | consistency check only from now on |
| Fayyazuddin 2006 MN5 soma potential 4.71 mV | SET a value (s14 fly2, F-GJ-5: PSI→DLMn unitary PSP, switch neutral) | can no longer validate |
| Ryglewski et al. 2014 GF→DLM delay 1.85 ± 0.21 ms (n 10; read as SD, 1.43-2.27) | spent (s20 fly2, F-GJ-6, pre-registered DECISIONS 20 Oct 23:30): two-compartment DLMn PASS at 2.196 ms | consistency check only from now on |
| `gf_latency.py` + `gf_psi_dlm_path.py` on m10f + measured NT + measured PSP + N30 two compartments, seed 1 (central values and the four corners) | spent (s20 fly2, F-GJ-6) | a changed DLMn (doublet fix, tau_m, measured q/ρ) needs seed 2+ and a new held-out range |
| `gf_latency.py` on m10f + measured NT + measured PSP + N30 at the option-B values (class, MN5 L, MN5 R), seed 1 | consistency only (s21 fly2, F-GJ-7; Ryglewski already spent) | none; a build at measured values needs seed 2+ |
| `docs/research/sealed/s21_gf_dlm_sealed.md` (GF→DLM 1:1 vs doublet, paired-pulse refractory period, following frequency, soma amplitude of the axon spike; sources Ryglewski et al. 2014 PNAS, Fayyazuddin 2006 and others) | **sealed, unread** (written by fly2's literature agent, 21 Oct). One header line ("Source 1 — Ryglewski S, Kadas D, … (2014)") was seen in a grep; no value. Value-free summary from the agent: Ryglewski 2014 states two following-frequency pairs, plots the refractory period without stating it, and gives 1:1 qualitatively; Fayyazuddin 2006 gives 1:1 and the spike shape qualitatively only | open once, for the DLMn build at measured values, after its pre-registration |
| fly_brain.zip identity runs (s22 fly2, F-ZIP-1): m10f0, flat floor, no stimulus, 1 s, seeds 12 and 13 | seen as engineering output only (spike totals and hashes; no observation compared, nothing scored or selected) | seeds 12-13 were noted as reserved for the rung-1 G1 check; seed 12 has long been the smoke default. If G1 needs unseen seeds, use 14+ |
| fly_brain.zip scoreboard protocols (s22 fly2, F-ZIP-2): `per_labellar_sugar` (LB3b/LB3c 100 Hz → MN9_L, seeds 0-9, bar > 5 Hz) and `gf_escape` (DNp01 kick train, seed 0, Augustin 2017 latency ranges) | regression checks on spent evidence: the sugar gate is the session 10 fit and class-search gate, and the Augustin ranges are seen or spent (rows above). Results: PASS 5.7 Hz; FAIL, no motor neuron follows | a PASS or FAIL here is not a held-out test; a changed model needs its own held-out check elsewhere |
| fly_brain.zip closed-loop protocols (s22 fly2, F-ZIP-3, scored in F-ZIP-4): `stands_flat_floor` (seed 12, 1 s, no stimulus) and `walks_dng100` (DNg100 100 Hz, seed 0) | seen in F-ZIP-3 before their bars were written (DECISIONS 21 Oct 02:33), then scored under those bars as regression checks: both FAIL. Seed 12 is the F-ZIP-1 engineering seed; seed 0 is command_walk's exploratory seed | a held-out standing or walking test needs new seeds |
| fly_brain.zip `per_leg_sugar` (s22 fly2, F-ZIP-4): LgLG4 + LgAG2 50 Hz → MN9_L, seeds 0-9, bar > 5 Hz | regression check on spent evidence (leg sugar at 50 Hz was the target of the s12 margin diagnostics, F-TASTE-LEG-1, F-STAB-6). Result: FAIL, 0 Hz on every seed | not a held-out test; a changed model needs its own held-out check |
| flyapp `t4t5_ds.py` on v0r + flyvis rows (seed 0, both sets) | spent (s13 fly2, F-VISION-12: 0 of 8) | a new optic-lobe candidate needs a new seed or a new test |
| flyapp `t4t5_ds.py` on v0r + flyvis rows + flyvis pair strengths (seed 1, both sets) | spent (s14/s20 fly2, pre-registered DECISIONS 14 Oct 00:41; F-VISION-15): medulla FAIL 1 of 8, photoreceptor FAIL 0 of 8 | the next candidate needs seed 3 or a new test |
| flyapp `t4t5_ds.py` on the same + CT1 per-column compartments (seed 2, medulla set) | spent (s14/s20 fly2, pre-registered DECISIONS 14 Oct 01:05/01:07): FAIL 0 of 8, responses under the 0.5 mV floor | the next candidate needs seed 3 or a new test |
| Bypass S2 DNg100 15/25/40 mV and step R (8 arms) on the T1 fill | spent twice (s20 fly2): level 1 F-XCONN-3 (DECISIONS 20 Oct 22:02) and level 2 F-XCONN-4 (22:44); FAIL 3 of 3 and NO REACH 0 of 8 both times | a new VNC candidate needs a fresh check |
| Behnia 2014 step offset/onset ratios and filter peaks (Mi1, Tm3, Tm1, Tm2) | unspent; reserved as the flyvis pair arm's held-out recordings check (Ben, 13 Oct 22:53) | their amplitudes already set graded_range_rec |
| Azevedo 2020 Fig 5—fig supp 1A class rates (fast ≈1, int ≈10, slow ≈60 Hz, read off the plot) | seen (S4b fit target, 14 Oct) | none |
| Azevedo 2020 Fig 3E Rin class means (150/300/700 MΩ) | **spent as a check** in s15c gate 1(c), 21 Oct 02:12 (pass; it had been an input to ρ in s15/s15b) | don't reuse as a held-out target |
| Azevedo 2020 recruitment order slow→intermediate→fast (Fig 5G text) | **held out, unspent** (S4b falsified with no s*, 14 Oct 00:21; its 15/40 mV members unviewed) | score once, against a future pre-registered MN-layer fit, after its chosen value is written down |
| Hige 2015 Fig 3D, MBON-γ1pedc>α/β CS+ charge after one forward pairing (−90 ± 3.7%) | seen; **fit target** for m10f4's shared `kc_mbon_ltd_timing_rate` 0.430 (F-S24-2). Its CS− (about −25%) is reported, not scored | don't reuse Fig 3D as a check of N21 |
| Hige 2015 Fig 1H/1J backward pairing (odour 0.5 s after the last DAN pulse: no change at γ1pedc, n 7) | **unspent** (F-S24-2 reported it without scoring; LTP was off) | spend once, as the falsifier of a future potentiation rule |
| Hattori 2017 Fig 6F, PPL1-α'3 restores depressed MBON-α'3 responses (8, 18, 33, 40% after 1, 3, 6, 10 DAN stimulations; flat controls; n 10 cells) | seen; **fit target** for `kc_mbon_dan_restore_rate` (provisional 0.00289, s25; `docs/research/s25_restoration_figcheck.md`). The in-network confirm (DECISIONS 22 Oct 04:11, 04:22) is a check of the implementation, not evidence | don't reuse Fig 6F as a check of the restoration rule |
| Cohn 2015 Figs 6-7 (DA alone potentiates naive KC->MBON-γ1pedc EPSCs; unpaired DA restores depressed ones, Fig 7I) | seen; **form only** (the rule's shape, no value fitted). DA-alone potentiation of naive synapses is a known miss of the s25 rule | not usable as a held-out check of the s25 rule |
| Berry 2018 Fig 5H-I, unpaired DAN activity after learning erases the MBON-γ2α'1 memory trace (Paired>Unpaired vs Paired>Decay) | **SEALED** (values in `docs/research/sealed/s25_restoration_heldout_sealed.md`, written by a figure-check agent, never read by fly2). Held out for the s25 restoration rule; score F = (R_post2 - R_post1)/(R_pre - R_post1) from the model first, then open | spend once, as the held-out test of `kc_mbon_dan_restore_rate` |
| Handler 2019 Fig 2D-E, ISI dependence of KC->MBON plasticity (γ4 signs: −1.2 s potentiation, 0 and +0.5 s depression, +6 s minimal) | **spent** on m10f4 (F-S24-2, 22 Oct): H1 and H2 pass, H3 fails (no LTP) | don't reuse as held out; a future LTP rule needs a new held-out set |
| Huang et al. 2018 PPL1-α'2α2 resting rate (6-10 Hz) and Turner 2008 KC rest (0.1 Hz) | fly's resting-fit targets; used by fly2 s26 as the rest CONDITION of test R (F-S26-1), not fitted to and not scored against | none |
| Turner 2008 KC odour responses (6 ± 5% respond; α/β 2.2, α'/β' 4.9 spikes per odour) | seen; set the KC drive in `kc_mbon_pairing.py` (F-S24-2) | none |
| Hurkey 2023 Fig 2f, MN1-4 subthreshold coupling coefficients (0.023 ± 0.003 s.d. strong pairs, 0.01 ± 0.0027 weak) | seen; **fit target** for m10f5's `electrical:DLMn c-f->DLMn c-f\|gap_coupling` 0.0266 (pair-count mean 0.0143; fly2 s27, F-S27-1) | none |
| Hurkey 2023 Fig 2h, spike AHP CC 0.042 ± 0.04 and overshoot 0.01 ± 0.004 | **seen**: the AHP CC was computed in the s27 fit runs (0.0123-0.0188) before any band was written (DECISIONS s27 amendment) | consistency only, never held out |
| Hurkey 2023 Fig 2b and Extended Data Fig. 6, MN phase histograms (gap around phase 0 in controls, absent under shakB KD; near-zero-phase fraction in (-0.1, 0.1)) | **spent** 23 Oct 03:59 on N12's second check: FAIL, falsified (F-S27-4; registered DECISIONS 03:34) | consistency only from now. Unspent: Fig 3d synchronization index under ShakB overexpression (formula not in the text). Correction: the '0.56 vs 0.61' pair is Shab KD, not shakB |
| Strother 2018 Fig. 4E-F (in vivo CDM raises Mi1, Tm3, Mi4, Mi9, T4) | **spent** (s19 U3, pass 5 of 5; DECISIONS 22 Oct 02:05) | sign consistency only from now |
| Strother 2018 Fig. 6F Mi4 ×2.66 under CDM | SETS the shared receptor gain a (s19 U2 calibration) | can't validate N19 |
| Dacks 2009 PN +15% under bath 5-HT | **SPENT (s19, 22 Oct 05:23): FAIL**, −0.34% at a* = 0.0649 (F-S19-2). Weakened beforehand: a fail at the wrong a* = 0.0458 had leaked (DECISIONS 04:42) | none; can't be reused |
| Lv 2024 Fig. 2E 50-pulse OA τ 0.6/9.4 s | **held out, unspent** for U1h (s19). The run at the wrong a* is void and unread | score once, at the registered a* = 0.0649 |
| Lamba 2014 Fig. 1C y w ZT21 advance (5 min, 1,500 lux) | **spent** 23 Oct 00:09: +3.21 ± 0.23 h (blind pixel read) against +2.89 predicted, **pass** (F-S20-3) | can't validate N26 again |
| Lamba 2014 Fig. 1C y w ZT15 delay −3.1 ± 0.35 h; Kistenpfennig 2012 zero crossing CT 18.5 and CT15 delay −4.05 h | training targets of the s20 CRY-TIM fit (k_tim, ct_tim fitted) | can't validate N26 |
| Vinayak 2013 10 min IRC half-max; Tang 2010 ZT15 TIM loss; Shafer 2002 Fig. 6D TIM profile | SET a, k_d (by rule) and TIM_DD (s20) | can't validate N26 |
| Vinayak 2013 120 min half-max, TIM loss at threshold, 2.4 h max advance | consistency only (seen); the first two miss (F-S20-3) | none |
| Vinayak 2013 CT20-21 advance 2.4 h (1 h pulse) | seen in an agent report; never used to set a value | consistency only (seen before registration) |
| Huber et al. 2004 Sleep 27:628 rebound after 6/12/24 h deprivation | **training context** (Director, 23 Oct 00:45: its direction "dependent on prior time awake" leaked through the s20 round-3 reader). Magnitudes still unread; no full text reachable | may set or train N25 values if Ben supplies the full text; never a held-out test |
| Chowdhury et al. 2023 eLife 12:e91355 Fig. 1 (Canton-S males, vortexer 20 s arm, 6/12/24 h ending ZT 0, day-1 normalised rebound); raw data Dryad doi:10.5061/dryad.qnk98sfpp | **SPENT 24 Oct 00:15** (DECISIONS; F-S23-6): s23 candidate B fails (6 h low; 24 h inside for panels I and K, outside for J; the figure's 20 s 24 h box disagrees between I and J). Scored from a blind figure read (`docs/research/s23_chowdhury_fig1_read.md`); Dryad raw data unread, needs a browser login; it can refine the recorded score, not re-open it. Before: held out, weakened (registered DECISIONS 23 Oct 00:53). Protocol read (Methods only). Results/Discussion subsection titles seen (stimulus-frequency effect, yoked low-frequency rebound, little debt repaid over cycles, short bouts mask rebound, 5-HT candidate); magnitudes and the deprivation-length dependence unseen. Dryad not downloaded | score once, on the first new-structure homeostat that passes its implementation and training checks; the 00:34 mode 0/1 predictions are reported at the same read. s22: mode 1 passes; locked 99.7 / 150.2 / 174.3 min (DECISIONS 03:24); T5 amendment 70.3 / 111.3 / 131.1 proposed (03:32); the Director names the one scored; s23: the Director chose (c) (23 Oct 04:50), a new structure first; the night-input refit is registered (DECISIONS 23 Oct 23:30) and running. Dryad still not downloaded |
| Brown et al. 2020 PLoS Genet 16:e1008270 (PMC7089559) | protocol read only (one 24 h duration, mainly females); no outcome seen | unused; not a dose series |
| Huang et al. 2024 Nature Fig. 1 voltage imaging (PPL1 and MBON resting rates, Zenodo 10998457, `data/raw/huang2024/`) | **spent** 23 Oct 01:00 on the s20 MB noise fit: PASS 6 of 9 (F-S21-1) | consistency only from now; a per-type MB rate mechanism needs another held-out source. Released to fly2 23 Oct 03:25: used as a bound (nothing fitted) to rule out N21 candidate (b) for PPL1 (F-S27-3) |
| Abhilash & Shafer 2024 two-process fit (taus 8.76 / 9.51 h, 74.36 % sleep) | model source (s20 `SLEEP_SOURCED`, neutral). C1 implementation check FAILED by 1.2 pp (F-S20-4) | not evidence for N25 |
| Abhilash & Shafer 2024 Fig. 1E: CS, w1118, yw males "~70 % to 80 %" of 24 h asleep (DAM, LD) | training: the s22 primary band 1008-1100 min/day (`docs/research/s22_n25_reads.md`) | can't validate N25 baseline |
| Liu et al. 2016 Cell 165:1347: R2 (= ER5, inferred) BRP raised at +2 h, back at +24 h; firing about 3× ZT13-15 vs ZT0-2 | SET τ_decay bracket (s21) and training checks T3, T4 of the s22 fit | can't validate N25 |
| Pimentel et al. 2016 Nature 536:333: dFB restart 25.86 ± 7.61 min (7 of 15, after > 12 h SD) | SET k_r (s22, the rate at full need) | can't validate N25 |
| Garbe et al. 2015 Biol Open 4:1558 Fig. 2 (iso31 males, SB/MB DAM bouts; own figure read) | training (s22 night check; s23 T5: day and night bouts within mean ± 1 s.d.) | can't validate N25 bouts |
| Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734: KC spontaneous 0.1 ± 0.4 Hz (71 KCs, Canton-S females; text) | seen (s22, Sonnet reader; MBON/DAN rates barred, unseen): SET candidate for a KC rest rate; the same 0.1 Hz was already spent as a check (row "PN spontaneous rate; PEN 3.9 Hz; KC 0.1 Hz") | can't validate MB rest rates |
| Felsenberg et al. 2018 Cell (M4β′/M6 → PAM-γ5 excitation, CsChrimson + GCaMP6f); Aso et al. 2014 eLife (MBON transmitters); Liu & Wilson 2013 PNAS (GluClα in the AL) | seen (s22, Sonnet reader, text only; MBON/DAN rates barred, unseen): MBON link signs | can't validate an MBON link-sign switch's rates |
| Male daily sleep 618-1100 min/day (Cirelli 2008, Harbison 2013, Buchert 2022, Geissmann 2019) | seen (s20 N25 category A); C2 consistency check | consistency only |
| Lv 2024 Fig. 2J and Wan 2021 single-pulse τ | SET the pool kinetics; U1 is a consistency check | none |
| Burggren 2017 respirometry and male mass; PMC8774106 TAG; PMC4335172 crop and gut | SET the s19 sourced values (`internal_state.SOURCED`) | can't validate S1-S4 |
| Male starvation survival 24-112 h (secondary reports) | **spent** (s19 S2, pass 28.4 h; F-S19-1) | consistency only |
| Ja 2007 CAFE, single males 1.5 µl/day | **spent** (s19 S3, pass 1.85; F-S19-1) | consistency only |
| Male desiccation survival 16.1-34.5 h (secondary) | **held out, unspent**; seen in an agent report and never used to set a value (S4 not scored) | score once when the loss rate and lethal fraction are sourced |
| Card & Dickinson 2008 J Exp Biol 211:341 Table 1 (take-off COM speed over the first 2 ms, middle-leg extension, peak acceleration; N 27) | **spent** 23 Oct 23:55 (fly2 s29 B15: FAIL on both criteria, F-S29-3) | consistency only; a B15 retest needs von Reyn 2014 or Zabala 2012 (unread) |
| Göpfert & Robert 2002 J Exp Biol 205:1199 (arista f0 426 ± 16 Hz, Q 1.2 ± 0.1, 8 living flies) | SET B20 f0 and Q (fly2 s29) | can't validate B20 |
| Göpfert & Robert 2003 PNAS 100:5514 (living best frequency 395 ± 46 Hz at 1e-5 m/s, n 10) | **spent** 23 Oct 23:56 (fly2 s29 B20 PASS, a replicate with values seen first; F-S29-4) | consistency only |
| Wilson & Laurent 2005 J Neurosci Fig 2 (PN picrotoxin 46 ± 5 %, CGP 97 ± 2 % of the rest; LN picrotoxin 98 ± 3 %) | SET N7 recorded shares (fly2 s29, PN 0.54 derived, LN 0 inferred) | can't validate N7 |
| Inada, Tsuchimoto & Kazama 2017 Fig 5C (KC GABA-B share about 32 % of the blockable response, figure read) | seen (fly2 s29 reader); not used to set a value; an unregistered Davie-scale prediction (0.30) was made after it was read | consistency only |
| Engel & Wu 1996 J Neurosci Table 2 (GF-pathway habituation: median 42 / 85 / 39 stimuli to 5 failures at 2 / 5 / 10 Hz, n 26 / 90 / 13; 85 checked on the table image 24 Oct 00:13; Fig 4B (log-mean ± SEM, the band source) viewed at page resolution then, not used) | **held out, unspent**; Fig 5 recovery read to SET the N34 GF tau (fly2 s29) | N34 fit target: fit one frequency, hold out the other two |
| Apostolopoulou & Lin 2020 PNAS 117:16606 (APL chronic activation and APL>TNT; KC compensation over about 4 d) | SET N32 directions and tau (fly2 s29); effect sizes in figures not read | the APL arm can't validate N32; the TNT arm is a weak same-paper prediction |
| Bushey 2011 Science 332:1576; Gilestro 2009 Science 324:109 (secondary); Das 2011 (AL habituation half-life) | SET N31 taus and gain, N34 AL tau (fly2 s29) | can't validate N31 or N34-AL |
| Fontaine 2009 J Exp Biol 212:1307; Riabinina 2011; Jang, Goodman & von Reyn 2022 preprint | seen (fly2 s29 reader, take-off and antenna context); not used | not blind for B15 or B20 |
| Male desiccation survival 16.1-34.5 h (secondary) | **held out, unspent**; seen in an agent report and never used to set a value (S4 not scored; s23: the two dry-air water-loss sources in hand can't set the rate, F-S23-4; readers barred from survival times) | score once when the loss rate and lethal fraction are sourced |
| Klepsatel, Wildridge & Gáliková 2019 Sci Rep 9:5239, metabolic Q10 2.0 (Oregon R) / 2.3 (Canton S), adult males | SETS `q10_met` (s23, measured) | can't validate S1 |
| Itskov et al. 2014 sip volume and duration; Manzo et al. 2012 pumping rate; Edgecomb et al. 1994 (via a secondary) crop capacity; Qi et al. 2015 first meal 0.32 µL | SET `ingest_nl_s` (derived) and `crop_max_nl` (inferred, Qi the upper bound) for m10f8 (s23) | Qi's meal volume is circular for S3 |
| Liang, Holy & Taghert 2016 Fig. 1G DN1 Ca2+ peak CT 18.8-19; Kunst et al. 2014 DH31+ DN1 late-night wake (abstract and secondary) | SET `ct_dn1_h` 19 (inferred) and the sign and window of the N25 night term (s23) | can't validate N25 |
| Gate G seeds 12-15 and smoke S seed 12 on m10f6-m10f10, m10f9 (seed 12) and m10f9c (seeds 12-13); G2 (1000 ms window, registered 24 Oct 01:31) seeds 12-15 on m10f9b, m10f9c, m10f10, and the seed-12 localisation diagnostic (P/Q) on m10f9c (s23) | engineering checks under fly2's stage rule; nothing fitted on them | none |
| Digby 1955 J Exp Biol 32:279, small *D. melanogaster* radiant warming 2.5 K (10 cm/s air, 1.0 cal/cm²/min; wing-beat thermometer) | **spent** 24 Oct 00:57 on S5 Check D: PASS, 2.36 K predicted (F-S23-9; registered DECISIONS 00:51) | consistency only from now; S5 needs another measurement for any further check |
| Laughlin, Howard & Blakeslee 1987 (240 vesicles/s per active zone, via de Ruyter van Steveninck & Bialek 2002) and Kazama & Wilson 2008 (p 0.79) | SET `graded_rmax` 300 Hz (derived, s23) | can't validate N1 |
| B27 / N27 / N33 reads (Wolf 2006, Wasserthal 2007, Armstrong 2011, Spong 2016, MacNamee 2016; `docs/research/s23_b27_n27_n33_reads.md`) | seen; candidate SET values (none used yet) | a check for those rows needs a source not used to set them |
| Lamina dark-rest reads (Laughlin 1989; Weckström & Laughlin 2010; Rusanen & Weckström 2016; Dau 2016; Laughlin & Osorio 1989; Zheng 2006; Juusola 1995 and Uusitalo 1995 abstracts) and graded-synapse voltage reads (Simmons & de Ruyter van Steveninck 2005; Burrows & Siegler 1978); `docs/research/s23_gate_silent_window.md` | seen; candidate SET values for `release_at_rest` (none used) | a check for N1 only if not used to set r0 |
