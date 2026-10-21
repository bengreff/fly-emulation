# Handoff: current state

**Rewritten each session; do not append.** State as of Wed 21 October 2026, 02:13 CDT. Session 15, after a Director /clear: score s15b, then s15c gate 1. The night runs until about 05:30, and usage is near tonight's cap, so stop at a clean commit by about 04:30. Ben's notes: two compartments are allowed where a point model provably fails; "we are trying to discover the minimum for functional behavior". Take clean fidelity steps, and don't go to a fitted synaptic scale.

**s15b DONE: 0/12 pass (F-S15-2; DECISIONS 21 Oct 02:03; commit 7f1ed6a).** Viewed: `docs/media/s15b_arms_rasters_{15,25,40}mv.png`, `s15b_arms_frames_all.png`, `s15b_arms_chain_T1L_40mv.png`.
- No arm alternates; M0 fails as required. TP looks like M0.
- TM/TPM silence the leg MNs (3.77 → 0 Hz before drive). The cause is the fitted `spontaneous_drive` (35.55 mV, slow flexors), which sits on the soma compartment and reaches the spike zone at 0.24× (derived). That's an arm-design confound, recorded and not re-run.
- Runs: Mac `runs/s15/arms/{s2,chain}` with `score.json`; backhouse `~/fly-m10f/runs/s15/arms/`. Nothing is running on backhouse; the Mac keep-alive has exited.

**s15c gate 1 DONE: all pass (F-S15-3; DECISIONS 02:10 locator note, 02:12 results; commit 333b213).** Outputs are in `runs/s15/morph/` (gitignored): gate1_{a,b,c}.json, point_params.json, axon_search.csv.
- **(a)** `src/flyemu/morph.py` against NEURON 9.0.2 (`uv pip install --python .venv/bin/python neuron==9.0.2`; .venv has no pip; check-only, not in pyproject): Rin and PSP peaks agree to about 10⁻⁵ on 6 cells.
- **(b)** Isopotential limit, all 106 cells: max error 0.0065 mV, or 0.047 mV for the 21 slow flexors with the 35.55 mV tonic drive. The second is the backward-Euler vs exponential-Euler difference (derived 0.041). The fix, if ever needed, is a capacitance matched to exponential Euler.
- **(c)** Tibia flexor somatic Rin median 582 MΩ (n 29), inside Azevedo's 150-700. Radius ×0.8 and Günay's Rm/Cm go over 700.
- **Gate-2 preview:** the spike-zone gain per synapse is about 1 (0.8-1.3×), so the stop rule will probably apply.
- **Tools:** `scripts/probes/s15c_point_params.py` (point parameters of the 106 cells at m10f0; builds the brain, ~1 min on the Mac) and `scripts/probes/s15c_gate1.py {a,b,c}` (a ~1 min, b ~90 s, c ~7 s). `morph.py` now also has `split_node` (reproduces the s15b CSV exactly) and `spike_zone(cell, syn_nodes, kind)`.

**s15c NEXT, in order** (pre-registration DECISIONS 21 Oct 01:38 + addendum; the cable values are in `docs/research/s15c_cable_params.md`):
1. **DECISION before gate 2 (mine to make; write it in DECISIONS before any gate-2 output): the leg-MN spike-zone site.** The male-CNS v1.0 T1 leg-MN skeletons have no motor axon: they end in LegNp(T1), and no node is more than 94 µm from an input site. The registered rule falls back for 89/94 cells, and for 13/94 it lands on a twig at the soma. Options:
   - the registered sensitivity alternative, the s15b split + 20 µm (arbor base, soma side; same rule as the core);
   - the trunk end: follow the thickest child from the soma; the segment is the last 20 µm before the leaf where the trunk leaves the arbor.
   My lean: make the split primary and the trunk end the sensitivity, since the split is defined in every cell and the trunk end isn't checked yet. Ben's list gains "spike-initiation site in an adult leg MN".
2. **Synapse-site map:** `syn_in.parquet` (bodyId_pre, positions; 318,230 sites; gitignored, regenerate with `scripts/connectome/walking_morph_fetch.py`) mapped onto the `lif` network edges onto the 106 cells (min_synapses 5). Report the weight share with no EM site.
3. **The `lif.Network` hybrid** behind `cell_type:all|morphological_walking_cells` (neutral 0; GPU refuses; CPU only).
   - **Isopotential-limit rule:** synaptic current = weight × kernel × G_total, split over the edge's sites. `spontaneous_drive`, noise and intrinsic currents are spread by area.
   - **The cells have intrinsic channels ON at m10f0** (slow-flexor rung-1). Either spread them by area at the soma voltage, or refuse them, and say which in DECISIONS. Spike rule: threshold at the segment's middle node; reset and hold only the segment.
   - **Check:** at Ri → 0 the hybrid network run must equal the point network (extend gate 1b to a network step).
4. **Gate 2** (unitary, with the stop rule), then **gate 3** arms H0/HM/HP/HPM × 15/25/40 on backhouse, rule 16, done-files.

**s15 step 1 (F-S15-1) and s14 (F-S14-1): done; see FINDINGS.**
- fly2's option-B rule has no spike zone for distributed-input cells.
- s14: 0/18 pass. The hand-off probe gives 0.17-0.47 mV per core spike against the 7 mV gap.
- Measurement for Ben's list: a front-leg MN somatic recording with E2 (INXXX466) or E1 (IN17A001) activation. It gives the unitary PSP, Rin, and the soma-to-neurite attenuation.
- The S4b recruitment order is still unspent.

**Session 13 (14 Oct 02:21; kept for reference).** Ben's 13 Oct order: the motor-pathway bypass assay (S0-S4) comes before more mechanism work. Its output is a failure-localisation report. Forced drive is a DIAGNOSTIC, not emergent walking. fly owns the nerve-cord side (S2-S4). fly2 owns the body side (S1 follow-up, its section below), the optic lobe and gap junctions; stay out of its files.

**X1, cross-connectome control of the E2→I1 deficit: DONE (s13, 14 Oct 00:39-02:21; F-XCONN-1, F-XCONN-2; DECISIONS 00:39 pre-registration, 00:45 audit, 02:21 results).** No fitting; nothing adopted. Parked for the night after this (Director).
- **Count audit (F-XCONN-1):**
  - The male-CNS E2→I1 deficit is part of a T1-wide input deficit against MANC: the per-cell matched-input ratio is 0.58 in T1, 0.69 T2, 0.82 T3.
  - Male-CNS T1 I1 has 1,176/836 postsynapses against 2,100-2,500 for its own T2/T3 copies and about 2,500-2,900 for MANC's I1.
  - BANC sits with MANC; FANC can't be used.
  - All core cells are Traced/"Reviewed".
  - Reading: male-CNS-specific, more likely reconstruction (inferred).
- **Simulation (F-XCONN-2):**
  - MANC counts on the core (Xc) or on the whole matched VNC (Xv), in our model, at DNg100 15/25/40 mV.
  - I1 is never recruited (T1L Vmax ≤ −47.5 mV against −45), and there is no alternation in any of 9 runs.
  - Viewed `docs/media/s13_xconn_rasters_{25,40}mv.png`; the arms are indistinguishable at the MN layer.
  - **The male-CNS counts are not the break.** Our spiking model can't run this circuit on either animal's wiring. The open questions are Ben's list: whether I1 spikes or passes graded signals, the unitary PSP, and E1/E2 bursts.
- **Tools:** `scripts/probes/xconn_counts.py` (`build` on backhouse, which needs the dense MANC matrix at `~/pugliese_cpg/data`; `audit` on the Mac, which needs `/tmp/pugliese_cpg/data`, a scratch copy that may vanish, so re-copy from backhouse) and `xconn_swap.py` (MANC counts into `connectome.load_tables`; `--swap none|core|vnc`, `--harness chain|s2`). Outputs `runs/s13/xconn/` (Mac, gitignored; the backhouse copy is in `~/fly-m10f/runs/s13/xconn/`). Nothing is running; tmux `xconn` has exited.
- **Rule 16 (Director, 14 Oct):** on backhouse, cap OMP/MKL/OPENBLAS/JAX CPU threads at 4 per job (`OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 XLA_FLAGS=--xla_cpu_multi_thread_eigen=false`, or the JAX equivalent) and check `uptime` before launching. The machine was at load 49-67 on 28 threads tonight, and our jobs were slowing CRUCIBLE.
- **Next: S4 proper at s 1** (does proprioceptive feedback produce alternation?). Read fly2's F-REFLEX-2 first: the afferent path stops at the first hop. Pre-register, run on backhouse with done-files under rule 16, view, commit. Not started.

**Bypass assay, nerve-cord side (s13, 13 Oct 21:30-23:14).** All results are committed. Read F-BYPASS-1 to F-BYPASS-4 and the DECISIONS entries from 21:41 onward (pre-registrations S2 21:41 and S3 22:09, calibration note 22:18, results 22:09 and 23:10, reference 23:13).
- **S0 done:** `rest_vs_reference.py`. MBON14, P-EN and DN1a are low at rest. Queued behind the assay.
- **S1 FAIL** (F-BYPASS-1): constant activation can't hold a stance. That is now fly2's body block.
- **S2 FAIL, all four DNs** (F-BYPASS-2 and its addendum): DNg100, DNb08, DNg97 and DNa02, brain off, 15-40 mV. MNs stay tonic, with no alternation. Sheets: `docs/media/s13_bypass_s2_*.png`.
- **F-BYPASS-3:** Pugliese's own spiking model (their `lif_dynamics.py`) gets I1 (IN16B036) to only one spike per cycle on MANC. On the male CNS, I1 never fires there either. E2→I1 is 38 synapses here against 71 in MANC.
- **S3 FAIL, all arms** (F-BYPASS-4; rasters `docs/media/s13_bypass_s3_rasters.png`, frames `..._s3_frames.png`, oscillator cells `..._s3_chain.png`, all viewed):
  - A: 13B/10B graded;
  - C: VNC efficacy ×1.754 (Shiu's);
  - D: A + C;
  - B: every unknown-mode VNC local graded. B "passes" the scorer but is a VNC-wide runaway: DNg100 is suppressed, the activity continues after drive-off, and the body convulses. Fail on viewing, per the pre-registration.
  - Nothing adopted; m10f0 unchanged. The 13B/10B `graded_rec` rows are in cell_types.csv but read only under `cell_type:all|mode_from_recordings=1` (neutral 0).
- **Where the break is now** (falsifier hit): our core already oscillates at 11-12 Hz, as Pugliese's does. E1, E2 and IN19A007 (their I2) fire once per cycle, and IN19A007 resets E1. The rhythm reaches the same left-front MN types as theirs (coxa promotor, trochanter flexor), but at about one spike per cycle per pool. In the reference, every active pool is modulated deeply on every cycle (`docs/media/s13_pugliese_ref_mn.png`). The stance antagonist gets no rhythm, because I1 stays silent. The tibia flexors are tonic and independent of the drive (23 Hz line, present before drive). Sign audit (`bypass_sign_audit.py`, `runs/s13/bypass/s3/sign_audit.json`): the loop edges have the expected signs. Glutamate is 19% of the premotor input to leg MNs and is treated as inhibitory (inferred).
- **Pugliese reference reproduced** on backhouse: repo `smpuglie/Pugliese_cpg_2025` at 10e7661, clone at `~/pugliese_cpg` with its own venv (JAX 0.9.2 CUDA, diffrax 0.7.0). Runner `fly_ref_run.py`; outputs copied to `runs/s13/bypass/pugliese_ref/`.
  - MANC, I 250: 11.4 Hz.
  - Male CNS: I 400 is needed (I 250 gives nothing). DNg100 R gives 12.0 Hz with 7 MNs and 0 anti pairs; DNg100 L gives 10.4 Hz with 4 MNs and one zero-lag pair at r −0.31.
  - Mac scratch copies `/tmp/pugliese_cpg` and `/tmp/pug_ref` may vanish. The backhouse clone is the durable one.
- **Tools:** `scripts/probes/bypass_s2_descending.py`, `bypass_s3_chain.py` (network-only oscillator traces), `bypass_rasters.py` (repeat `--chain` for one V panel each), `bypass_sign_audit.py`, `bypass_lag_readout.py` (secondary lagged readout, never a pass), `bypass_sheet.py`. Runs are in `runs/s13/bypass/{s2,s3,pugliese_ref}` (Mac, gitignored). The backhouse S3 run is in `~/fly-m10f/runs/s13/bypass/s3/` (run.sh, done-files, ALL.done).
- **S4 step 1 (F-BYPASS-5, DECISIONS 13 Oct 23:31).** At equal synapse counts our MNs need 14-25× more input than Pugliese's to reach threshold. Above threshold they have 0.17-0.22× the gain. Neither scale is measured. Azevedo 2020 has no fast or intermediate f-I curve, so the recruitment order (slow, then intermediate, then fast; measured, never fitted, **still unspent**) is the held-out check. Readout `scripts/probes/bypass_moddepth.py` (per-cycle depth, drive-dependence; `hi` band edge, default 15, S4b uses 16).
- **S4a FAIL, all arms (F-BYPASS-6, DECISIONS 13 Oct 23:57; commit f86cc8a; viewed `docs/media/s13_bypass_s4a_{rasters,frames}.png`).** R `cell_type:leg_motor|between_type_size_exponent` 1.49 and G `cell_type:leg_motor|glutamate_receptor_sign` +1, plus RG: 0 transfer-pass pools in 9 runs, no antagonist pair. R and G stay neutral switches (0). GPU R+G equivalence: reference member exact over 3000 steps.
- **S4b FALSIFIED (F-BYPASS-7; DECISIONS 14 Oct 00:21 fit, 00:33 diagnostics; pre-registration 00:12).** It fitted one shared quantity, `cell_type:leg_motor|synaptic_input_scale` (neutral 1; owner row `n5p_leg_mn_synaptic_input_scale`), over 1-25. **s\* = none:**
  - No scale gives an antagonist pair; candidate pairs fire in phase.
  - Rates are within ×3 only at s 16-25.
  - Nothing adopted; the scale stays neutral 1.
  - **Recruitment order still unspent** (it is spent at s\* only). The 15/40 mV members were never looked at.
  - Checks:
    - GPU check exact;
    - s1/25 mV member = CPU harness, exact;
    - s25 body run = GPU member, exact.
  - Viewed:
    - `docs/media/s13_bypass_s4b_rasters_25mv.png`: one co-active ~12 Hz volley, no alternation, stops at drive-off;
    - `..._s4b_frames.png`: thorax on the floor; legs splay at s 25 without stepping.
  - **PSP check (Director):**
    - `scripts/probes/s4b_unitary_psp.py`; literature `docs/research/s13_s4b_unitary_psp.md` (Sonnet, unchecked).
    - The model gives 0.021 mV per synapse at s 1, linear in s.
    - s 1 is consistent with measured insect unitary PSPs. s 16-25 is not: 0.34-0.53 mV per synapse, q90 connections at 18-29 mV, and one premotor spike fires about half the MNs.
    - So rate-matching compensates for a near-silent premotor layer (0.13 Hz mean during drive). Proposed evidence bound s ≤ ~14 (inferred; not adopted).
  - Scripts: `s4b_scale_sweep.py`, `s4b_score.py`, `s4b_unitary_psp.py`. Runs: `runs/s13/bypass/s4b/{,body,psp}` (Mac copy; backhouse `~/fly-m10f/runs/s13/bypass/s4b/`).
- **Where the break is now:**
  - The core's output: one spike per cycle; the premotor layer is near-silent.
  - I1 never fires, so the stance antagonists get no rhythmic inhibition.
  - The MN-side gain is ruled out: R, G and the scale all failed.
- **Next, in order:**
  1. **I1 recruitment: done as X1 (above).** The male-CNS T1 undercount is real, but on MANC counts our model still doesn't recruit I1 or alternate (F-XCONN-2).
  2. **S4 proper: proprioceptive replay and closed loop.** Insect antagonist switching depends on load and position feedback (Büschges; needs a cited range). Pre-register whether feedback produces alternation at s 1.
  3. **Ben's list (unchanged by S4b):**
     - (a) a unitary premotor→leg-MN PSP recording, which would bound the scale by measurement;
     - (b) an E1/E2 (core) burst recording during walking, which would give burstiness a range;
     - also Seki 2010 and Choi 2004 (paywalled).
  4. The tonic tibia-flexor drive (fitted spontaneous drive of 35.55 mV against a 26.2 mV gap, 23 Hz) is a separate MN-layer issue. It is the "slow" class in every S4b row.
  5. Then the queued mechanism work (session 13 list below).

**Session 13: where it stopped (13 Oct 21:31).** Brief (Thu 8 Oct): build the frontier profile m10f, with every built mechanism ON at an in-range value. Adoption needs a 60 s smoke (no runaway, no NaN, resting rates in range) plus the silence gate with eye cells excluded. m9c stays the reference. Mechanisms in order: (1) per-type intrinsic dynamics from a range table, (2) membrane noise, (3) neuromodulation with receptor effects, (4) standing via one fitted shared support drive, with the fall after silencing held out.
- **Committed 13 Oct:** bfc5751 class-grain adaptation (N4, neutral); 258b502 m10f0 profile and gate changes; fabdabb probes `smoke_live.py` and `adapt_fit.py`; 7fa4fb1 research tables `docs/research/s13_intrinsic_ranges.csv` (118 rows) and `s13_neuromodulation_effects.csv` (63 rows), both agent-gathered and not yet checked row by row. `tests/test_class_mechanisms.py` 14 passed, `tests/test_repo_hygiene.py` 12 passed. Nothing in the tree was fly2's.
- **Left uncommitted (broken):** `docs/research/s13_resting_rates_reference.csv`, 61 rows from agent C (published spontaneous rates by class); 21 rows have unquoted commas in free-text fields (agent C died before checking). Fix the quoting by hand before using it.
- **m10f0 (= `m10f`)** = m9c + `sense:taste_leg|modality_source` 1.0 + `connectome:unclear|nt_by_development` 1.0. These are the only built switches that were off in m9c and are in range. It is not adopted; the brief's adoption bar also needs resting rates in range, which fails (see below).
- **Gate** (`closed_loop_check.py --profile m10f0`, eye classes excluded, noise removed in the silent window): seeds 12-15 all 0.0 non-eye spikes/ms in the last 100 ms (eye cells too). Results in `runs/s13/gates/` (Mac copy, gitignored).
- **"Does it live" smoke** (`smoke_live.py`, 60 s, seed 12; m9c also seed 13; results in `runs/s13/smoke/`): m10f0 and m9c match to rounding.
  - Whole brain 0.32 Hz; 2.8% of cells active; median active cell 10.8 Hz; max 221 Hz.
  - Movement in the first 10 s: 20.5 rad/s summed hinge speed (m9c 20.3 and 20.1), moving in 100% of bins (head 13.5, wing 3.8, leg 2.9 rad/s). Thorax path 2.3 mm in 60 s; thorax height 0.55 mm.
  - Dead control (m9c, no brain drive): 0.39 rad/s, 7% of bins moving.
  - No runaway, no NaN, 0 MuJoCo warnings. Wall time about 6500 s per 60 s run on backhouse (8 jobs in parallel).
  - **Resting rates fail for the mushroom body:** MBON, KC, DAN, APL and DPM (and LMC) are 0 Hz at rest in both m9c and m10f0. Published spontaneous rates for MBONs and DANs are nonzero (agent C's table has rows). This is the first target for mechanism 2.
- **Noise sweep** (3 s, m10f0 seed 12, `class:<c>|noise` set to σ on all 55 central and VNC classes, eye and sensory classes untouched; `runs/s13/noise/`). These are open-loop facts, not a fit:

  | σ (mV/√ms) | whole brain (Hz) | cells active | summed hinge speed, first 10 s (rad/s) | thorax |
  |---|---|---|---|---|
  | 0.25 | 0.33 | 3.0% | 23 | |
  | 0.5 | 0.37 | 4.4% | 21 | |
  | 0.75 | 0.53 | 23% | 70 | path 11.8 mm, final height 1.9 mm (left the floor) |
  | 1.0 | 1.08 | 30% | 110 | |

  Single-cell reference (s12): σ 1.0 → 1.8 Hz and σ 1.5 → 7.6 Hz for an undriven cell. Not yet run with the gate's noise-on option.
- **Class adaptation (N4):** built and neutral, not ON anywhere. `adapt_fit.py` on the generic central cell (τ_adapt 200 ms): the late/early ratio falls from 0.983 to 0.396 over 0-6 mV; a recorded ratio of 0.5 gives 3.05 mV (inferred). There is no class with a numeric recorded ratio yet; the MBON data are qualitative only (weak within 400 ms).
- **Mechanism 1 candidates** (`s13_intrinsic_ranges.csv`):
  - MBON τ_m 16 ms measured (13.8-18.4), against model 20 ms, so `class:MBON|tau_m_scale` 0.8 is a candidate;
  - uPN τ 20 ms is already in range;
  - HS τ 4.3-4.9 ms (Cuntz 2013) is a per-type candidate;
  - VNC 13B and 10B non-spiking are mode candidates.
  - Most classes have no measured value.
- **Mechanism 3** (`s13_neuromodulation_effects.csv`): the plan is sign from receptor coupling weighted by expression probability (`receptors.gene_probabilities`), with magnitude bounded by a measured effect (e.g. OA flight gain on HS). The validity limit is global modulator pools.
- **Next, in order:**
  0. (Queued behind the bypass assay, Ben 13 Oct. Steps 1-2 below are done: S0.)
  1. Fix the resting-rates CSV quoting.
  2. Score per-class rest against it (MB classes are at zero).
  3. Mechanism 1: MBON tau_m_scale 0.8, then HS per-type τ; smoke and gate after each.
  4. Mechanism 2: per-class σ fitted to spontaneous rates. Pre-register first, holding out P-EN, DN1p and VUM.
  5. Mechanism 3, then mechanism 4.
- **Backhouse:**
  - Private checkout `~/fly-m10f` (data/raw, cache and .venv symlinked to `~/fly-emulation`). Sync with `COPYFILE_DISABLE=1 tar --no-xattrs -cf - src scripts tests data/model | ssh backhouse 'wsl -d Ubuntu -- bash -c "tar -x -C ~/fly-m10f"'`.
  - WSL needs a keep-alive (`ssh backhouse 'wsl -d Ubuntu -- bash -c "exec sleep infinity"'`) or tmux jobs die.
  - Bypass jobs: none running (S2, S3, S4a, S4b, X1 and the Pugliese reference are all collected). No keep-alive is open. `/home/greff` holds Ben's other project; don't touch it. Keep memory headroom: each probe process takes about 2.4 GB, others use about 24 GB.

**Session 12 (4 October 16:36 to 22:31, then 5 October from 02:05):** Ben's order is blanks, then an accurate body, then the ladder to synapse-specific fidelity (A, B, C), and nothing else. Development models, many flies and the reconstruction study come after. Timeline in `docs/SESSION12_LOG.md`. The m10q search on backhouse stays uncollected. Below this block, the file is still the session 11 state, except the working model.
- **Working profile: m9c** (adopted 5 October 23:53; m9r before it, adopted 03:31; m9f 02:51). m9c = m9r + the N26 clock drive fitted to DN1p day-night firing (`state:coupling|clock_gain` 7.75, fitted) + the run starting at the specimen's ZT 1.5 (`state:clock|initial_ct`, sourced); F-CLOCK-1, DECISIONS 23:34-23:53. Gate, battery and sheet are unchanged from m9r; the clock cells now fire (DN1p about 4 Hz) and reach no motor neuron. flyapp's library runs m9r (differs only in the clock; Director's call). m9r's lineage: m9 → m9w (wing motor roles, nerve-based afferents) → m9n (each sensor on its own nerve) → m9m (mid/hind muscles derived from segment size; TTM 90 µN·mm) → m9d (leg damping 0.05 s × measured stiffness; TTMn out of the Hill pool) → m9s (MuJoCo noslip off) → m9t (non-leg torque per spike from the leg motor-unit anchor × moved-part length, inferred; F-NONLEG-1) → m9u (wing hinge stiffness from Bergou et al. 2010; F-WING-4) → m9v (mirror-image neck motor neurons; F-NONLEG-2) → m9f (folded wings resting on the abdomen; F-WING-5) → m9r (left leg rest angles mirrored from the right legs, the measured side; F-STAND-3 side note). Each step passed the silence gate (seeds 12-19; DECISIONS s12). None is fitted. Since 5 October 21:40 m9r itself carries `motor_unit:all|force_per_spike` 10 (guessed), the value every gate ran with by `--set`; the name now means the gated model (DECISIONS 21:27, battery passed). Earlier profiles still need the `--set`.
  - m9s: flybody's 3 noslip iterations did not converge at the 0.1 ms step, so resting motion depended on the step; with noslip off the loop is step-converged and matches the MJWarp GPU path (F-DAMP-2).
  - m9r: the fitted leg rest angles differed left from right (front coxa roll 23.2° against 5.0°), a non-unique fit to right-leg-only data. They seeded a mid-air roll in the dead drop. Mirrored, the roll at 30 ms falls from 1.9° to −0.2°. The lying fly still tips 16° onto its right side (25° before). With leg damping also mirrored (`joint:leg|damping_mirror` 1, diagnostic, not adopted; DECISIONS 04:13) it tips −25.5° onto its left side instead: the lying pose is bistable and small left/right differences pick the side. Residual asymmetries: leg damping up to 10% (switch exists), hinge axes (lf tarsus chain 13°, lf coxa 3-4°), FTi ranges under 1°, scan segment origins up to 0.15 mm, and the upper wing. `scripts/probes/mirror_audit.py` lists them. The damping and stiffness residual is specimen geometry: neutral angles agree, but scanned keypoints differ up to 25 µm and segment lengths up to 1.6%, so the projected stiffness differs 2.5-6.6% (`scripts/probes/mirror_legs_geometry.py`); kept. Backhouse gate scripts that list keys by hand must add `--set 'joint:leg|rest_mirror=1'` to match m9r (`runs/s12/gates/run_wm.sh` does).
  - The fly lies down at rest (F-STAND-3, option (a) below). The head lies on the floor and the head-bristle channel reads it, so resting rates are not a clean standing baseline.
- **A** (blanks) done: `docs/BLANKS_AUDIT.md`. **C** (synapse-specific ladder) done: `docs/FIDELITY_LADDER.md`, rungs 8-13.
- **B done** (each behind a switch, sourced, gate run): wings at rest (F-WING-2); sensor assignment by nerve (F-SENSE-NERVE-2); mid/hind muscles as a labelled derivation (F-MUSCLE-MH-1); TTM double count; leg damping (F-DAMP-1); contact solver (F-DAMP-2); non-leg torque per spike (F-NONLEG-1); extensor:flexor as a data conflict (F-FTI-2); wing hinge stiffness (F-WING-4); neck signs (F-NONLEG-2); and on 5 October:
  - **Wing clipping (Ben's report, F-WING-5).** It was both visual and physical, from one cause: flybody's folded pose put the wings 40-150 µm inside abdomen segments 1-4, and the spring held them there against live contacts. `joint:wing|folded_pose` 1 lifts each wing about its hinge line onto the abdomen (12.5°, plus 1.5° so one wing lies on the other; left on top is guessed, but real flies each keep a persistent preference for one side, Buchanan et al. 2015 PNAS, so it is one valid individual). Closed loop: wing-abdomen contact at most 4 µm, vein overlap at most 9 µm (side and top sheets viewed: `docs/media/s12_wing_rest_zoom_hinge.png`). Open: the wing root sits up to 67-80 µm inside the thorax mesh. It is hidden by MuJoCo's parent-child contact filter and not visible from outside.
- **B built, kept off:**
  - Coxa ranges and CTr ranges (F-COXA-2): the instant-release dead fly lands on the new range limits.
  - Leg and wing taste modality per type (`sense:taste_leg|modality_source` 1; DECISIONS 5 October 02:57). The flyapp relay said leg taste peaks at 2.9 mV at 1 M sugar, below the 7 mV threshold, because every leg taste type had a guessed 0.2 weight to every tastant. The switch gives types matched to receptor lines (LgLG4, LgAG2, WG2 sugar; LgAG1 bitter; gustatory connectome preprint, secondary read) the labellar rule, sets pheromone types to 0, and keeps 0.2 for the 237 unmatched cells. Drive at 1 M is now 14.3 mV. Held-out rate (Ling 2014, about 50-55 Hz at 100 mM) FAIL: LgLG4 4.5 Hz, because only the rm and rh tarsi touch the patch while the fly lies down. Steady contact would give 38 Hz (derived from the cell's LIF constants). Specificity passes; the gate is identical. Off per the registered rule. Gain 15 mV and K 0.05 M are still guesses (no leg dose-response found). Wing taste cells take leg contact (guessed). MN9 stays silent to leg sugar.
- **Standing (F-STAND-3): resolved for now as option (a).** (c), the connectome's own campaniform → motor neuron load reflex with nerve-based assignment, nothing fitted, FAIL on seeds 12-14: live and dead flies are on the floor by 40 ms and end 6 µm apart. Load afferents fire at 21-23 Hz on five legs and 0 Hz on lh (lh carries no load because the lying fly tips onto its right side; see m9r above). The homolog resting-rate search found one number, the Drosophila slow tibia flexor at about 30 Hz (Azevedo 2020), and none for coxa or trochanter pools in any insect (`docs/research/s12_resting_mn_rates.md`), so there is nothing to fill. The blank stays open and the fly lies down. Fall curve (`docs/media/s12_stand3_fall_curves.png`): silencing at 500 ms drops the thorax 2-4 µm because it is already down; the passive fall from placement starts within 10 ms at about 15 mm/s, against Wang 2025's silenced real flies at 1.3 mm/s (onset 40-300 ms). Option (b) was not approved. Director leads checked 03:52 (F-STAND-3): the model has no tonic descending drive. With afferents removed every DN is silent. At rest 7% fire, and those are driven by head bristles because the head lies on the floor. No paper found gives a resting DN rate in Hz, and DN imaging says few DNs encode rest (Aymanns 2022). So the gap is not shown to be upstream. A small rest-encoding DN population is a brain blank with no value (`docs/research/s12_resting_dn_activity.md`).
- **Flight (F-FLIGHT-3, F-WING-3):**
  - The blade-element wing (`aero:wing|model` 1) at measured hover kinematics and wing size gives 1.15 W (pre-registered, PASS).
  - Against the robotic fly (Muijres 2014 Database S1): force response within 0.03 up to F/mg 1.45; roll torque about half the robot's (FAIL, two fixes tried, roll fixes stopped); stroke-direction force Fx about 0.70 of the robot's while Fz agrees; no measured drag coefficient set exists for the hydei robot wing.
  - **Dickson et al. 2010 yaw test** (pre-registered 5 October 02:45; `scripts/probes/yaw_damping_dickson2010.py`, `docs/media/s12_dickson2010_yaw.png`): yaw damping C*_ω −856 against the robot's −640, 1.34× (FAIL high, linear, right sign). Prediction 0.6-0.8 missed. Actuation slopes pa 1.13 and pd 0.93 pass, pr 1.35 and pv 0.46 fail; three signs are opposite to the robot's (conventions unknown, not scored). Added mass changes nothing. Nothing in the model changed.
  - The s10 generator crosses the wings over the back (F-WING-3). The measured-table drive and the measured wing ranges are built behind switches that no profile sets.
- **Next, in order:**
  0. **FIRST, next session: the fidelity-rung plan (Director order 02:10; DECISIONS 04:36; parked 04:46 on usage budget, WIP).** Leg sugar's per-route margin, GNG117's latch and T4/T5's missing direction selectivity share one root: the model lacks neuron and synapse dynamics. Route tuning has stopped. Five rungs; each is a switch that already exists in `lif.py` but has no fill. Fill measured rows first, then class priors with bounds, all labelled:
     1. spike-frequency adaptation (`adaptation_increment`/`adaptation_tau`; rung-1 channels);
     2. short-term depression/facilitation (`std_release_fraction`/`std_tau_rec`; per-connection `stp_connections.csv`);
     3. membrane noise (`background_noise`, global today, needs per type);
     4. graded against spiking per type (`mode_from_recordings`, 7 recorded rows; Mi4, Mi9, C3, Tm4, Tm9 and CT1 have none, F-VISION-11);
     5. per-type membrane time constant (`tau_m`, 1 row).
     - **Step 1, data survey (WIP).** `docs/research/s12_dynamics_survey.md` first pass committed. It covers HS τ_m 4.3-4.9 ms (Cuntz 2013, re-read), Behnia 2014 filter peaks (Mi1 71, Tm3 53, Tm1 56, Tm2 43 ms), Nagel 2015 STP (re-read) and Kazama & Wilson 2008. Rungs 1 and 3 have no measured values. **Not done:** the optic-lobe kinetics sources. A second agent was stopped at park before reporting. To do: Arenz et al. 2017 Curr Biol (Mi1/Tm3/Mi4/Mi9 filter time constants), Groschner et al. 2022, Strother et al. 2017, and Gruntman 2018/2019 (local copies in `data/raw/vision_mode_s12/` and `vision_rest_s12/`). Also Azevedo 2020 via api.elifesciences.org. Re-read every number before use.
     - **Step 2.** One pre-registration per rung: fill rule, predicted effect on each held-out test, falsifier. Rungs 5 and 4 come first; they decide T4/T5 DS through Mi1/Tm3 against Mi4/Mi9. Rung 5 likely needs a switch `cell_type:all|tau_m_from_recordings` with `tau_m_rec` rows, like `rest_from_recordings` (proposal).
     - **Held-out tests, fixed before any fill:**
       - the silence check (gate silent window and no-runaway);
       - leg sugar (DECISIONS 00:41 checks);
       - labellar sugar plus bitter (`assay_pathways.py`);
       - **T4/T5 direction selectivity via flyapp's eye harness**, run by the flyapp worker through the Director (do not touch the flyapp worktree), with `motion_grating.py` as the in-repo check (v0r baseline: F1 0.14-0.30, DSI 0.00-0.03; F-VISION-11).
     - GNG117 persistence is reported, not targeted.
     - Step 3: gate, battery and a viewed contact sheet before any adoption.
  1. **Done 21:56: Dandelion's transmitter and sign bracket** (Director 21:30 order 1; DECISIONS 21:30; F-TASTE-LEG-1; `docs/research/s12_tarsal_per_pathway.md`). Dandelion is male-cns AN13B002 (FlyWire AN_GNG_68 left, AN_GNG_193 right; hemilineage 13B), named by the taste connectome paper (Tastekin et al., Cell 2026; secondary read).
     - **Measured:** GABA transcripts in hemilineage 13B (Lacin et al. 2019, FISH; ground-truth table `flyconnectome/drosophila_neurotransmitters` `gt_data.csv`, commit a9417412, confidence 3 of 5, the row that feeds BANC's `neurotransmitter_verified`). 96 of the table's 98 13B rows cite the same source.
     - **Inferred for this cell:** GABA, by lineage. **Predicted:** GABA by both EM classifiers (male-cns 0.89; BANC 0.96-0.97), which are trained on such lineage labels, so not independent.
     - **Measured for this cell type:** none found (no immunostaining, transmitter-specific driver or physiology).
     - **Bracket** (diagnostic, `--nt AN13B002=acetylcholine`, m2 and m9r, 3 trials): leg sugar gives MN9_L 0 Hz with either sign, labellar sugar changes +5% (m2) and −25% (m9r), sugar + bitter stays 0 Hz. With acetylcholine 537-782 more VNC cells fire (its partners). So the sign does not decide leg PER in the model. **Neither sign adopted**; the model keeps GABA. Settling experiment: For Ben's list below.
     - Next for leg PER: done 22:45, item 1b.
  1b. **Done 22:45: the taste connectome paper's leg sugar route, read by eye** (Director 22:00; DECISIONS 22:04 and result; F-TASTE-LEG-1; `docs/research/s12_tarsal_per_pathway.md`, last section). Figure 9B: LgLG4 → AN01B004 → Bract 1 and 2 → Roundup → MN9, plus S&S. In male-cns Bract 1 = DNge174, Bract 2 = DNge173, Roundup = GNG108 (synonyms, measured annotation), S&S = GNG159 (inferred). The weights match the figure, so the model has the route. It stops at Bract 2: AN01B004 also drives GNG093 and GNG250 (GABA predicted), whose inhibition nearly cancels Bract 2's excitation. Silencing those 4 cells (diagnostic) lifts Bract 2 to 10-25 Hz; MN9_L reaches 8 Hz mean under m2 only with LgLG3 added (216 GRNs), 1 Hz with the 54 matched sugar GRNs, and under m9r Roundup stays at 0-1.3 Hz. Two blocks, both in guessed or fitted values. Next facts: GNG093/GNG250 transmitter evidence (as for Dandelion), whether LgLG3 senses sugar, and why m9r's Roundup needs more drive than m2's (per-cell threshold, tau_m, GABA-B load). A Bract 2 or Roundup recording under tarsal sugar would be the held-out test.
  1c. **Done 22:56: BLANKS_AUDIT stubs, data first** (Director order 3; `docs/BLANKS_AUDIT.md` section "Data-first pass on the stubs"). N29 became **partial**: Tsodyks-Markram STP per connection for ORN → PN and ORN → LN (Nagel 2015, Nagel & Wilson 2016; derived) behind `synapse:all|per_synapse_parameters` 1, CPU only, off (resting LN and PN rates fell 67-80%; held-out ordering failed; F-STP-1). Next for N29: STP together with the measured unitary ORN → PN strength and a fitted LN → PN inhibition (Olsen & Wilson 2008), held out on Bhandawat 2007. N30, S6, B24, B26, N31-N34 and B25 stay absent with data recorded (`docs/research/s12_compartments.md`, `s12_hemolymph_ions.md`, `s12_b24_b26.md`, `s12_tierC_stubs.md`). B26's one Drosophila measurement became a held-out check: the model's passive middle leg is 3-5× softer in compression than the living leg (Oeftger 2026; F-LEGK-1), mostly at femur-tibia; a B3 tone target, nothing changed. **23:24: every stub is now searched.** B27, S7, S8 and D1 stay absent with data recorded (`docs/research/s12_b27_s7_s8_d1.md`): the spiracle motor neurons are in male-cns as ENXXX226 (inferred) and are simulated, only the aperture effector is missing (B27); axenic flies walk faster through octopamine, so the model is a healthy conventionally reared fly and validation data must record rearing (S7); courtship matures by 72 h (S8). D1's specimen record is read: the male-cns fly was a 5-day-old Canton S G1 × w1118 male, 12:12 LD, dissected at ZT 1.5 (the ZT 1.5 start is now `state:clock|initial_ct` 1.5 in m9c, item 1e). Counts unchanged.
  1d. **Done 23:26: why m9r blocks the leg sugar route** (live lead; DECISIONS 23:05 and 23:12 with results; F-TASTE-LEG-1; figures `docs/media/s12_legsugar_ladder.png`, `s12_legsugar_chko.png`, `s12_central_fi.png`, viewed). Two independent blocks, each enough alone. (1) Feedforward inhibition from GNG093/GNG250 (GABA predicted) onto Bract 2 and onto a cholinergic GNG cluster that co-excites Roundup (430 synapses onto GNG588). (2) Rung-1 intrinsic currents, and within them **BK**: with the inhibition silenced, a profile ladder passes at m4 and m7, blocks at m8 and m9r, and passes with rung 1 off. Per-channel knockouts pass only with BK off (Roundup 31.5 Hz, MN9_L 48; BK+Kv2+SK off 69.5 and 120). The route's central cells have no transcriptome row, so they carry the slow tibia flexor BK fit (7.87 × g_L0) unscaled. In a single cell it halves gain above rheobase, and that compounds over 5-7 hops. Inferred, not measured. Diagnostic only; nothing changed. A Sonnet search for adult central-neuron current-step data (f-I, AHP) was running at 23:28; its result decides whether central BK gets its own sourced value (pre-register, switch, battery). Also seen: m2 → m3 alone raises the route from Roundup 7 to 84 Hz (consensusNt or psp, not separated); MN9_L saturates at 120-130 Hz once the route ignites.
  1e. **Done 23:53: the clock checked against recordings, m9c adopted** (F-CLOCK-1; DECISIONS 23:34, its result, the m9c addendum and result; `scripts/probes/clock_phase_rates.py`; figure `docs/media/s12_clock_dn1p_grid.png`, viewed). The central f-I search (`docs/research/s12_central_fi.md`) turned up DN1p firing: about 10 Hz at ZT0-4 and nearly silent at ZT8-12 (Flourakis 2015, read). Under m9r every clock cell was silent at every phase, because the 3 mV drive (guessed) was under the 7.5 mV onset. One number was fitted: `g_clock_mv` 7.75 gives 11 Hz at CT 2 and 0 Hz at CT 10 (held out, passes). A new key starts the run at the specimen's ZT 1.5 (Nern 2024 Methods, read); without it the fitted drive would still be below onset at CT 0. Open: *per*⁰¹ DN1p fire 2-4 Hz but the model's clock-less cell is silent (needs a baseline plus a swing, two numbers). The onset is a 0.25 mV knife edge: re-run the probe after any central excitability change.
  1f. **Done 23:58: MBON-α3 f-I against the class-prior BK** (F-FI-1; DECISIONS 23:56 and its result; figure `docs/media/s12_mbon14_fi.png`, viewed; `scripts/probes/central_fi.py --cell-type`). The one adult central cell with a recorded current-step f-I (Hafez 2023; figure estimate) carries the same class prior as the leg sugar route cells.
     - With the protocol and passive deflection matched, the model's MBON14 is 3.23 Hz/pA under m9c against a recorded 0.67-1.32 (FAIL high, as predicted). BK off gives 5.31, and 3.5-7.1 across the mapping corners.
     - So switching off central BK is not a biological fix for the leg sugar block.
     - The model cell also lacks adaptation, and it sits 7 mV below threshold, while the recorded cell fires near rest.
     - **Next, pre-register first:** the leg sugar route with route cells nearer threshold, bracketed by measured central resting rates (BK on, feedforward inhibition intact). Pre-registered 00:05 6 October, item 1g.
  1g. **Done (6 October 00:22): nearer threshold, the leg sugar route opens** (DECISIONS 00:05 and its result; FINDINGS F-TASTE-LEG-1, last bullet; `docs/media/s12_legsugar_rest.png`, viewed). 43 route cells were given a fixed drive (`scripts/probes/route_rest.py`, guessed, diagnostic), with m9c, BK and the inhibition on, 3 trials.
     - **1 mV below each cell's own rheobase:** Roundup 0 to 33-35 Hz and MN9_L 0 to 34-39 Hz at 200 Hz input, with MN9_L at 0 Hz at rest, on both leg sugar assays.
     - **At rheobase or at 12 Hz alone:** the route fires at rest (MN9_L 41-42 Hz).
     - **Base:** blocked.
     - The route switches rather than grades: 100 and 200 Hz give nearly the same output.
     - Nothing adopted.
     - **For Ben's list:** the resting potential against threshold, or the spontaneous rate, of a GNG route cell (Roundup or Bract patch).
     - **Next, pre-register first:** under the near arm, specificity (new assays `legbitter_mn9` and `legsugar_legbitter_mn9`, plus labellar controls), dose (3-50 Hz) and offset; then a membrane-noise version (`scripts/probes/noise_rest.py`: 0.75-1.5 mV/√ms gives 0.1-7.6 Hz at rest in one cell).
  1h. **Done 01:02: the `near` arm fails** (DECISIONS 00:26 and its result; `docs/media/s12_route_spec.png`, viewed). Leg bitter alone at 100 Hz drives MN9_L at 6-9 Hz, and 3 Hz of leg sugar (spontaneous level) at 13-17 Hz. It does not latch (0-2 Hz after the stimulus) and grades logarithmically (15, 23, 25, 31, 35, 39 Hz at 3, 10, 25, 50, 100, 200 Hz). Labellar bitter still silences labellar sugar; `near` raises labellar sugar 8-fold. Leg bitter at 200 Hz cuts leg-sugar MN9_L by 73%. Cause of the hair trigger (`scripts/probes/unitary_psp.py`, derived): entry cells rest 1.1 mV below threshold and one GRN spike gives 0.1-1.2 mV, so about half the single GRN → AN01B004 connections fire it alone. D1 completed 01:28.
  1i. **Done 01:28: a 3-4 mV margin passes every route check** (DECISIONS 00:41 and its result; F-TASTE-LEG-1; `docs/media/s12_route_margin.png`, viewed). Route cells at k mV below their own rheobase, m9c open loop, 3 trials.
     - k = 3 and k = 4 pass all four checks: 3 Hz silent, 50 Hz open (MN9_L 16-18 and 8-9 Hz), leg bitter 0 Hz, labellar bitter still silences labellar sugar, 0-1 Hz in the second after. k = 2 still fires at 3 Hz (3-9 Hz). Input for MN9_L 5 Hz: about 10 Hz (k = 3), 25 Hz (k = 4); real rate 50-55 Hz.
     - The entry cells grade alike at every margin; the margin acts downstream. The Bract branch (DNge174/DNge173 with GNG093/GNG250) opens first; the GNG578/GNG143 → Roundup–DNge059 branch later. Silencing DNge059 barely changes MN9_L, so that loop is not the trigger.
     - At k = 3 one GRN spike no longer fires an entry cell alone (1 of 57 connections; `runs/s12/margin/unitary_near3.json`).
     - The leg bitter leak is cured by the margin, so the presynaptic inhibition switch is not needed for it (`docs/research/s12_presyn_inhibition.md`: GABA-A/B at ORN terminals, Root 2008 about halves gain at strong input; no taste numbers).
     - Seen, not scored: the margin also amplifies labellar sugar 5-8× (shared route cells).
     - One-number fit to one route; nothing adopted.
     - Lead kept for the presynaptic inhibition bracket (connectome, derived, 00:50): each GRN class has its own GABA feedback loop. Leg sugar GRNs → DNg103, AN27X021, IN01B080 → about 4,500 GABA synapses back onto them; leg bitter → AN05B023a → leg bitter. Stimulated GRNs are forced to spike (68.75 mV kick), so this feedback can act only through the release switch (`cell_type:all|presynaptic_inhibition_gain`, off).
  1j. **Done 01:38: the whole-brain version of the margin fails the gate** (DECISIONS 01:16 and 01:24 with results; F-STAB-6). A class tonic drive at 3.7 or 4.7 mV on central_other, AN and DN leaves the brain firing after input stops (1.4-24.5 spikes/ms, rule 0) on seeds 12 and 13; central_other alone with AN (noDN) also fails (10, 11); DN alone fails narrowly on seed 13 (1.06). Under noDN the leg sugar route opens at 50 Hz (MN9_L 11-15 Hz) but latched on 1 of 3 trials (105 Hz after the stimulus).
     - The cell that holds it is the GNG117 pair: GNG117_L and GNG117_R excite each other with 914 and 973 synapses (22-23% of their input, predicted acetylcholine) and run at 110-155 Hz with GNG153, GNG186 and DNge022. Near threshold, a strong input switches the pair on and nothing switches it off. The stage 1 text called this the DNge019/DNg12 loop; corrected.
     - Two fixes failed (route-only margin is a one-route fit; class drive fails the gate), so I stopped and wrote up the mechanism. Nothing adopted.
     - **Superseded 04:36 by item 1l (Director order 02:10):** no more route or class-drive tuning. GNG117's persistence becomes a readout of the model-wide rungs (adaptation, short-term depression), not a target; the leg sugar margin stays a recorded diagnostic.
     - **For Ben's list:** GNG117's transmitter, and whether GNG117 fires persistently after a brief stimulus.
  1k. **Done 04:34 (partly; the lamina meets its recordings, Tm3 is at 0.62 and Mi1 at 0.27 of recorded): the vision blank (flyapp relay: the visual pathway dies after the lamina in m9r).** See DECISIONS (pre-registration plus results at 02:08 and 02:40), F-VISION-4 and F-VISION-5, and `docs/media/s12_vision_grating.png` (viewed). The probe drives a grating onto the photoreceptors open loop: `scripts/probes/motion_grating.py`, with per-cell F1.
     - **Cause.** Graded release is zero at and below rest. L1 and L2 are only ever hyperpolarised (histamine), so they release nothing, and everything below the lamina sits at −52 mV.
     - **Arms.**
       - T, release at rest (r0 0.5, guessed): the medulla follows at 0.4-0.65 mV with the right signs, but T4/T5 still sit at rest. It also fails the gate's dark silent window (16 spikes/ms).
       - R, recorded modes (`graded_rec` rows: Mi1, Tm1-3, T4, T5 measured; L4/L5 inferred): identical to m9c upstream of T4/T5.
       - RT, both: T4/T5 follow at 0.1-0.2 mV (V needs 0.5; FAIL on all 8 subtypes). At mean luminance HS fires 104-140 Hz and CT1 335 Hz, and 111 spiking cells run below −100 mV (Am1 −668 mV) because current-based inhibition has no reversal potential.
     - Nothing adopted; two switches (`cell_type:all|mode_from_recordings`, `cell_type:ol_graded|release_at_rest`) stay off.
     - L2's low photoreceptor count is R7/R8 input to L1 (real biology). The real lamina blank is truncation: half the cartridges get no R1-R6 synapse (F-VISION-4).
     - **Continued 02:44-03:14 (DECISIONS; F-VISION-6; figures `docs/media/s12_vision_flash.png` and `s12_vision_gain.png`, both viewed):**
       - RTc adds conductance-mode synapses (`cell_type:all|conductance_based` 1). It removes the runaway (0 of 167,111 cells outside [−90, 20] mV) but halves the chain gain. V still fails (T4 0.08-0.09 mV), and HS and CT1 still fire tonically.
       - Flash baseline (Behnia 2014 Fig. 2 stimulus, `scripts/probes/visual_flash.py`): RTc gets every recorded sign right (Mi1/Tm3 ON, Tm1/Tm2 ON dip and OFF). Stage ratios are within 2× of the recordings, but the photoreceptor swings 7.7 mV against 60, so every stage is 10-100× short.
       - Gain block (pre-registered 03:04): sourced graded spans (`cell_type:all|graded_range_from_recordings`, new switch, neutral, CPU-only), photoreceptor gain 78, LMC output ×1/3/10.
         - Mi1 ON 1.5-3.1 mV against 20, saturating. That is the pre-registered disinhibition ceiling, so the mechanism is written up and nothing is tried further.
         - Side effect: mode 2's tonic release drives Tm1/Tm2 to −18/−23 mV in the dark at ×10.
       - **Correction 03:29 (DECISIONS; F-VISION-7, which corrects F-VISION-6).**
         - The 03:14 mechanism assumed a −55 mV recorded leak. m9c leaves `rest_from_recordings` off, so the leak was −52.
         - Measured conductances (`scripts/probes/visual_conductance_state.py`, `runs/s12/vision/cstate_k{1,10}.json`) show the limit is modulation depth plus tonic inhibition, not the leak:
           - Light cuts Mi1's inhibitory conductance by only 14% (2.00 to 1.72 leak units). L1's release falls 27%: L1 swings 14 mV of a 45 mV span with r0 0.5, floored by the −70 mV reversal.
           - 0.75 of Mi1's g_i is tonic, from non-graded Pm/Dm1/Mi13 inputs (34% of its synapses). Even full L1 shutoff would reach only −52 mV, a 6.7 mV swing.
           - With no inhibition at all, Mi1 would sit at −41 mV, 18 mV above dark.
         - The leak-calibration switch (`cell_type:all|leak_from_network_rest`, neutral, CPU-only; `scripts/probes/visual_rest_calibrate.py`) is kept as tested infrastructure. It does not address this limit.
       - The leak switch is committed (0d8724a, off by default; battery 228 passed).
     - **Continued 03:42-04:02: the first synapse** (DECISIONS pre-registration 03:42, addendum 03:53, result 03:59 and refinement 04:02; F-VISION-8; `docs/media/s12_vision_first_synapse.png`, viewed; conductance probe now splits spiking input by presynaptic type).
       - R1-R6→L1 small-signal gain 1.24 against about 13 recorded (*Calliphora*, dim background; Juusola et al. 1995). Scaling photoreceptor release (k 10, 30) saturates the dim-flash gain at 6.1-6.2. L1's dark potential falls to −58 (2 s.d. below Pantazis −43 ± 7.3, held out). Mi1 stays at 1.1-1.5 mV.
       - Derived: gain = D(1 − p)/s ≤ D/s.
         - D is how far tonic histamine holds the dark LMC below its histamine-free potential v₀ (−44.8 mV in the model).
         - s is the release e-fold at the dark potential. It is 0.6 mV in the model, set by the guessed `photoreceptor:all|dark_drive`, so the dim flash doubles release and its 6.2 is a large-signal gain (small-signal 10.6 at k 30).
         - Gain 13 needs D of about 8-13 mV, which with v₀ −44.8 contradicts L1's recorded dark potential. So the lever is v₀ (L1's leak and non-histamine inputs) plus a release curve that extends about 12 mV below dark (Uusitalo et al. 1995). Driving force from the lamina field buys at most 2×.
       - The R1-R8 class switch also scales R7/R8 synapses onto Mi1 (595 of 795 cells) and L1 in the medulla; at k 30 that flipped Mi1's light response. The R1-R6-only arm restores Mi1 (+1.13 mV; addendum passed, L1 moved 0.57 mV against a 0.5 tolerance). Any photoreceptor-level scale must be per type.
       - Correction: the lamina field does not add driving force in light. Zheng 2006's values are dark rests; in *Calliphora* the space depolarises in light (Weckström & Laughlin 2010). The ledger row was corrected.
       - Nothing adopted. Staged, not applied (to keep the series comparable): HS graded-mode rows at `runs/s12/vision/hs_rows_staged.csv` (local, not committed; HSN graded measured, Kim et al. 2015; HSE/HSS inferred).
     - **Continued 04:05-04:14: the v0 arm** (DECISIONS pre-registration 04:05 and result 04:11; F-VISION-9; figure updated and viewed).
       - Rows (via `FLYEMU_EXTRA_PARAMS`, not in the CSV): L1/L2 `v_leak_shift_fit` 15.1 mV (leak −36.9, derived) and R1-R6 `release_gain` 12.5 (derived), with `leak_from_network_rest` 1. Backhouse `/tmp/v0_params.csv`, `/tmp/v0_run.sh`.
       - Pre-registered and met: L1 dark −43.7 (Pantazis −43 ± 7.3) and small-signal gain 11.8 (target 13 ± 2.5). L1 ON is −25.1 mV, 0.56 of the recorded −45. It implies an LMC histamine-free potential near −32 mV (unmeasured prediction).
       - Downstream still short: Mi1 +2.3 against +20, Tm3 +4.2 against +15, Tm1/Tm2 OFF +1.6/+1.9 against +17.5.
         - Mi1 is capped near 6.9 mV (derived) by tonic spiking Pm/Dm1 inhibition.
         - Tm3 is already at its 4.3 mV ceiling, set by L1's release floor (r 0.30 at −70 mV with r0 0.5 and span 45). Without the floor it would reach about 12 mV (derived).
         - L2's dark potential is −50.4, held down by spiking Dm6/Dm17/Dm1 inhibition (*Calliphora* L1/2 −38.4).
       - Seen, not scored: no L1 OFF transient in this arm.
       - **Decided (Ben, 13 Oct):** v0r, not v0, is the vision diagnostic base. The question was: should the v0 arm become the vision base? Recommendation: yes for vision diagnostics, no for the working profile until the Mi1 block, gate and battery have run.
     - **Continued 04:19-04:34: the LMC output release floor** (DECISIONS pre-registration 04:19 and result 04:32; F-VISION-10; `docs/media/s12_vision_release_floor.png`, viewed).
       - New switch `cell_type:all|release_at_rest_per_type` (off by default, CPU only; per-type `release_at_rest` rows; commit f0194bd, battery 229 passed).
       - v0r = v0 plus L1/L2 `release_at_rest` 0.26 (inferred: release reaches zero at the LMC's light-saturated −68 mV). Backhouse `/tmp/v0r_params.csv`, `/tmp/v0r_run.sh`, `/tmp/v0r_cs.sh`.
       - Every pre-registered readout passed. Tm3 ON +9.3 (recorded 15), Mi1 +5.5 (20), Tm1/Tm2 OFF +2.8/+3.4 (17.5), T4a +2.0. The lamina is unchanged.
       - Mi1 is now at its tonic-inhibition ceiling: 0.80 leak units of spiking Pm2b/Dm1/Pm2a/Pm1 inhibition, with L1's share zero in light.
       - Correction: L1 does have an OFF transient in v0/v0r (connected median +10.7 mV); the 04:11 entry misread the diluted type mean.
       - **Decided (Ben, 13 Oct): yes, for diagnostics only.** The question was: should v0r become the vision diagnostic base? Recommendation: yes for diagnostics, not for the working profile.
     - **Done 04:46: the T4/T5 grating on v0r FAILED as registered** (DECISIONS 04:33 and result 04:46; F-VISION-11; `docs/media/s12_vision_grating_v0r.png`, viewed). Per-cell F1 Mi1 0.70-1.07, Tm3 0.89-1.55, T4 0.14-0.29, T5 0.15-0.30 mV; V 0 of 8; DSI 0.00-0.03. T4/T5 inhibition is a tonic CT1 shunt (400 Hz); Mi4/Mi9 carry no signal. Next is rung 4/5 work (item 0), not more gain.
     - **Next, pre-register first:**
       - The Mi1 block: Pm/Dm1 modes (graded against spiking) and the GluClα reversal (M10Q −56 against −70).
       - The Tm1/Tm2 OFF limit: L2's OFF overshoot and Pm2a/Pm2b tonic inhibition (0.78 leak units).
       - Hold out L2, the T4/T5 grating and the flash amplitudes not trained on.
       - Later: per-receptor-class reversals (Rdl −41.5, Lee et al. 2003; GluCl), which need per-class conductances in `lif.py` and `gpu/batched.py`.
       - The 13 Hz Am1 rhythm the relay saw did not appear open loop; it needs the closed loop.
     - **For Ben's list:**
       - Strother et al. 2017 Neuron full text (whether Mi4/Mi9 were whole-cell recorded);
       - Schnell et al. 2010 J Neurophysiol (HS/VS mode);
       - Serbe et al. 2016 Neuron (Tm4/Tm9);
       - a Drosophila LMC response amplitude per contrast (patch or sharp electrode);
       - Mi1 input resistance in dark and light, and the GluClα reversal (F-VISION-6, F-VISION-7);
       - whether Pm1-3 and Dm1 cells are graded or spiking, and their light responses (F-VISION-7);
       - the ort reversal in LMCs against the lamina's local extracellular potential (Zheng et al. 2006: lamina space −20 to −40 mV against the retina in darkness);
       - a *Drosophila* R→LMC small-signal gain or photoreceptor release curve (F-VISION-8);
       - the LMC dark potential with histamine transmission removed (ort or hdc mutant, or a block), which measures v₀ (F-VISION-8);
       - the sign and strength of R8→Mi1 (595 of 795 Mi1 cells receive R7/R8 synapses);
       - CT1 compartment physiology (Meier & Borst 2019);
       - any recording of Am1 or the LPi cells.
  1l. Director order 02:10 (fill dynamics model-wide): moved to item 0 above.
  1a. **Done 21:40: force_per_spike 10 folded into m9r** (DECISIONS 21:27). Under m9r it reaches 71 of 732 mapped motor neurons (leg cells without a force-table row). Static arrays identical with and without `--set`; gate seed 12 identical to the archived m9r gate; battery 204 passed, 1 known failure. flyapp's m9r library started at 21:30:45 from its own copy before the fold reached main, so it runs those 71 cells at 1: restart it after merging main, or label it pre-fold (Director's call; not touched). Later fidelity step (B5, behind a switch): per-neuron values for the 71 cells from `scripts/motor_forces.py`'s size rule.
  2. Dickson damping: the split by term (DECISIONS 03:15, result 03:21) puts all of it in translational drag (−858 of −856; rotational, lift and added mass about 0, as the symmetry argument predicted). The model's drag polar is already the measured robofly polar (Dickinson, Lehmann & Sane 1999, Re about 136; `flight.robofly_coefficients`), so swapping in Sane & Dickinson's polar is not a new test (checked 03:22). Candidates that are: the advance-ratio dependence of the coefficients (Dickson & Dickinson 2004), and induced inflow, which a quasi-steady model leaves out. Both are model-form changes; pre-register before building. The two tests pull the drag in opposite directions (damping 1.34× too high, Fx 0.70 of the robot's), so a single coefficient scale cannot satisfy both.
  3. Free-flight held-out force test (Database S1, 92 sequences): per-beat wing force against m(a − g). Script to build: `freeflight_force_check.py`; pre-register first.
  4. Resting support drive, location only: done 04:05 (F-STAND-3; `docs/research/s12_resting_dn_activity.md`).
     - From BANC neck positions, minus the SEZ cells the Aymanns driver never labelled, 21 medial brain DN types near the giant fibers and 5 lateral types are low-confidence candidates (inferred).
     - DNp07 and DNa02 have the strongest leg reach (above the 90th percentile of DNs).
     - All candidates are silent in the model at rest.
     - No drive set. Next: resting recordings of DNp07 and DNa13 would discriminate.
  4b. Leg sugar → MN9 traced and two rescues tried (04:08-04:51; F-TASTE-LEG-1; `scripts/probes/legsugar_mn9_trace.py`, figure `docs/media/s12_legsugar_mn9_trace.png`). 3 hops; 2092 / 1942 / 1716 synapses per hop. Activity dies between layer 1 and layer 2 in every test: the 1 M patch (only lm and lh touch), all 54 leg sugar GRNs injected without contact, Shiu parameters (m2) open loop at 200 Hz, and every edge down to 1 synapse. Literature (`docs/research/s12_tarsal_per_pathway.md`, secondary): Thoma et al. 2016 put tarsal PER on a few ascending sweet GRNs per leg that reach the GNG directly; male-cns has them (LgAG2, 11 cells, inferred match) and they reach 39 brain cells at one synapse. Rescues (diagnostics, DECISIONS 04:40 and 04:50): a presynaptic gain on LgAG2 gives MN9_L 3 Hz at ×10 and 5-7 Hz at ×30 under m2 (0 Hz under m9r), against 21-31 Hz for labellar sugar; silencing every inhibitory input to MN9_L gives 0 Hz. Layer 2 lacks excitation from leg sugar (leg sugar is 1-2% of its input). Two rescues failed, so the mechanism is written up and no fix is tried. The paper's 'Dandelion' is male-cns AN13B002 (v2 text), a layer-1 cell predicted GABAergic, so inhibitory in the model; LgLG3 (162 cells, proposed sugar by the authors, weight 0.2 in the model) sends it 8770 synapses. Driving LgLG3 + LgLG4 + LgAG2 at 100 Hz: Dandelion 310-320 Hz, MN9_L 0 Hz (m2 and m9r; DECISIONS 04:59). Next: item 1 (Dandelion's transmitter), and the paper's own LgLG4 → MN9 path analysis read by eye. The assay now has `--release-gain` and `--silence-ids` (diagnostic).
  5. Remaining unsourced wing-rest quantities (F-WING-4): steering motor neuron activity at rest, folded-hinge yaw and roll stiffness, wing damping 0.05, the 2.64 mm wing lever, the +1 i1/i2 yaw mapping. None can be fixed from open sources today.
  6. Neck target pose (Gorko 2024, paywalled) and the antennal elevator/depressor split (`docs/research/s12_neck_antenna_sources.md`).
- **Open, needs Ben:**
  - **Decided (Ben, 13 Oct): option (a), with the stationarity check now in `closed_loop_check.py`.** The question was what the silence gate means for the eye (F-VISION-5).
    - The gate makes the eye dark and requires 0 spikes/ms in the last 100 ms.
    - Real lamina cells release transmitter tonically, and most in darkness (Juusola et al. 1996). With that release on, the OFF pathway fires in the dark window (gate seed 12 under arm T: 16 spikes/ms). That is biology, not runaway.
    - Options:
      - (a) count only non-optic spikes in the silent window, and require optic activity in darkness to be stationary (no growth across the window);
      - (b) gate at a constant mean-luminance eye instead of darkness;
      - (c) keep the gate as it is, which rules out tonic visual release.
    - Recommendation: (a). It keeps the gate's purpose, catching reverberation once input stops, without forbidding a measured property of the eye.
    - Nothing is waiting on this until a vision arm passes V.
  - **Standing.** Option (a) is in place: the fly lies down. A standing fly needs a resting support drive that no open data supplies (only the slow tibia flexor has a measured resting rate). Any further route ((b), or a new data source) is Ben's call.
  - **For Ben's list:** the FlyMimic author request for mid/hind leg models; Lehmann & Dickinson 1997/1998 (paywalled force-vs-kinematics data); Seki et al. 2010 J Neurophysiol 104(2) and Choi, Park & Griffith 2004 J Neurophysiol 91:2353 (central-interneuron adaptation/after-depolarisation numbers; they would give S4b's unfitted burstiness a measured range); the Science 2014 main text (Muijres et al.) for the robot's torque frame and sign; the paywalled non-leg muscle papers (Strausfeld 1987, Rajashekhar & Singh 1994, Tu & Dickinson 1994/96, Zanker 1988, Chan 1998); Gorko et al. 2024 (Nature 628:596) main text and supplement; Lindsay, Sustar & Dickinson 2017 and Beatus & Cohen 2015; a tarsal GRN dose-response (none found in open sources). Dandelion's transmitter (5 Oct 21:56): a split-GAL4 line for AN13B002 / AN_GNG_68 (search the Janelia VNC and SEZ split collections), then anti-GABA or anti-GAD1 immunostaining, or an intersection with Gad1, ChAT and VGlut T2A reporters; optionally optogenetic activation while recording GNG297 or AN09B004, with and without picrotoxin. The model's leg PER does not hinge on it, so it is not urgent. Added 5 October night: current steps (f-I curve and AHP) in one central GNG cell type, ideally Roundup (GNG108) or a cell of its co-exciting cluster, which settles whether central cells carry the slow-MN BK; spiracle aperture against SpMN rate for B27; transmitter evidence for GNG093 and GNG250 (the feedforward inhibition at Bract 2), and calcium imaging of LgLG3 GRNs to sucrose; paired soma and axon-terminal recordings with the cell's EM skeleton, one cell type per class, to fix λ for N30; force-displacement of an excised adult thorax at flight frequency for B26. Added 6 October: the resting potential against threshold, or the cell-attached spontaneous rate, of Roundup (GNG108) or Bract (DNge173/DNge174), fed and starved (no GNG resting rate exists in open sources, `docs/research/s12_gng_rest.md`; the leg sugar route opens only when its cells sit within about 1 mV of threshold); an open copy of Sui et al. 2026 Nat Neurosci (feeding MN cell-attached rates). Added 6 October 02:40 (F-VISION-5): Strother 2017 full text (Mi4/Mi9 mode), Schnell 2010 (HS/VS mode), Serbe 2016 (Tm4/Tm9), a Drosophila LMC contrast response amplitude, CT1 compartment physiology (Meier & Borst 2019), any Am1 or LPi recording. Added 6 October 03:14 (F-VISION-6): Mi1 input resistance (or whole-cell conductance) in dark and in light, and the GluClα reversal in Mi1 or Tm3; these decide whether the medulla's recorded 15-20 mV responses come from a large tonic synaptic conductance. Added 6 October 01:40 (F-STAB-6): GNG117's transmitter (the pair excites itself with about 950 synapses each way if cholinergic), and whether GNG117 fires persistently after a brief stimulus; this decides what holds the brain stable when central cells rest near threshold. The leg sugar route margin result also sharpens the earlier item: the route works when its cells rest 3-4 mV below threshold (not 7, not 1).
- **Tools added in s12:** `build_measured_kinematics.py`, `score_robot_sets.py`, `robot_torque_reference.py`, `added_mass_check.py`, `hover_blade_trace.py`, `resting_joint_speed.py`, `deadfly_decay.py`, `nonleg_motor_census.py`, `wing_spike_response.py`, `yaw_damping_dickson2010.py`; on 5 October `wing_clip.py --organism` (closed-loop wing contact sheet), `standing_rest.py --silence-at-ms`, `stand_fall_plot.py`, `leg_taste_dose.py` and `leg_taste_plot.py`; on 6 October `motion_grating.py` (grating onto the photoreceptors, per-cell F1), `motion_grating_plot.py` and `vm_extremes.py` (cells outside a voltage range), `visual_flash.py` (full-field flashes as Behnia et al. 2014 Fig. 2, per-cell peaks and whole-network voltage bounds), `visual_flash_plot.py` and `visual_flash_score.py` (median over cells whose cartridge has photoreceptor input, against recorded amplitudes) (all in `scripts/probes/`).
- **Battery:** m9c plus the vision switches (graded_rec rows, `mode_from_recordings`, `release_at_rest`, all neutral), Mac (6 Oct 02:53, `runs/s12/vision/pytest_battery_m9c_vision.log`): 226 passed, 0 failed, 0 skipped in 11 min; one MuJoCo QACC warning, which has appeared in every battery since m9f. No regressions. Before that, m9c, backhouse (23:52, `runs/s12/clock/pytest_battery_m9c.log`): 211 passed, 12 skipped, 1 known failure (backhouse raw-data path check); no regressions. Before that, m9r with force_per_spike folded in, backhouse (21:40, `runs/s12/fpsfold/pytest_battery_m9r_fold.log` plus `pytest_rerun_steering.log`): 204 passed, 12 skipped, 1 known failure (backhouse raw-data path check); no regressions. Before that, m9r plus the damping switch code on backhouse (04:57, `runs/s12/pytest_battery_m9r_dm2.log`): 203 passed, 12 skipped, 1 failed (the backhouse-only raw-data path check). No regressions. The run before it (04:47) also failed the key-owner test because `joint:leg|damping_mirror` had no row in `data/model/structural_keys.csv`; added. Any new switch needs that row. m9r on backhouse (03:41, `runs/s12/pytest_battery_m9r.log`): 202 passed, 12 skipped, 1 failed (same path check). No regressions. Earlier, m9f on backhouse: 196 passed, 12 skipped, 3 failed; two were the new folded-pose key missing an owner in `data/model/structural_keys.csv` (fixed 02:57), one is the known backhouse-only raw-data path check. Rerun 03:13 with the taste switch code: 201 passed, 12 skipped, 1 failed (the backhouse-only path check, which passes on the Mac) (`runs/s12/pytest_battery_m9f_b.log`). No regressions.

Session 11 was Director-run, from 30 September about 17:00 to 1 October about 03:00, mostly on the Mac. Its results are in `docs/FINDINGS.md` (Session 11), decisions in `docs/DECISIONS.md`, the timeline in `docs/SESSION11_LOG.md`, the plan in `docs/PLAN_NEXT.md`, and ranked fidelity upgrades in `docs/FIDELITY_LADDER.md`.

## fly2: N30 option B, the MN5 skeletons put class MN on the follow boundary (UNDECIDED, F-GJ-7); the doublet is the synaptic tail; no fix from measurement exists yet, so the MN5 recording decides (21 Oct 00:30)

**From fly (21 Oct 01:22; Director as Ben):** fly is cleared to append leg_MN and core_premotor rows to `data/params/two_compartment.csv` and `two_compartment_classes.csv`. Your DLMn/MN rows and the option-B method are unchanged; `scripts/connectome/premotor_mn_geometry.py` imports your `reduce()` as is. Turning on `two_compartments_where_point_fails` will then also turn on those rows, so DLMn-only runs need them neutralised (see fly s15). fly2 works in `.claude/worktrees/fly2` (branch `worktree-fly2`). Brief: the Director's 21 Oct night brief (N30 option B, then the doublet's mechanism, then the MN5 recording onto Ben's list). Every switch below is neutral by default and **none is adopted**.
- **Merging:** `main` (26f6976, fly's s14 25 mV results) was merged into worktree-fly2 at 8d722b6. DECISIONS conflicted only because both sides appended; both kept. **`main` can fast-forward to worktree-fly2.** The guard refuses commands aimed at the main checkout, so someone there runs the merge.
- **N30 option B done: class MN q and ρ from EM geometry (F-GJ-7).** Pre-registered DECISIONS 21 Oct 00:07; results 00:18; literature 00:25.
  - **Method.** `scripts/connectome/mn_axon_geometry.py` (male-cns v1.0 healed skeletons and PSI synapses, saved under `data/derived/mn_axon_geometry_skel/`; `--offline` reruns from them).
    - The axon base is the first branch point proximal to the PSI contacts with ≥ 5% of the cable off the path. The contact site is the median PSI synapse.
    - Coupling is a frustum axial resistance with Ri 200 Ω·cm (102-311, fitted), against Rin 102 MΩ (measured). q is the axon-side area over the whole area plus the soma sphere.
  - **Result.**

    | | q | ρ at Ri 200 (102-311) | ρ* |
    |---|---|---|---|
    | MN5 L | 0.156 | 2.03 | 3.51 |
    | MN5 R | 0.052 | 5.57 | 4.03 |
    | Class | 0.104 | 3.80 (2.44-7.45) | 3.78 |

    UNDECIDED, as registered. `two_compartment_classes.csv` and the `parameters.csv` rows now hold the derived values ("derived from EM geometry, measured Rin, fitted Ri"). `tests/test_two_compartment.py` pins the s20 pair (0.07, 1.6) by override for the mechanism tests (8 pass).
  - **Consistency runs, seed 1** (`scripts/probes/n30_optB_runs.sh`; `runs/s21/optB_*.json`; not scored, Ryglewski is spent):
    - class: 19/20, 1 spike, 3.20 ms;
    - L: 20/20, 1 spike, 2.80 ms;
    - R: 0/20.

    At the derived geometry the doublet is gone, but the spike comes late or not at all.
  - **DLMn c-f** (reported, not used): the base rule fails or is fragile in 3 of 8 cells (PSI contacts on several branches).
- **Doublet mechanism (at the guessed s20 pair):** the 5 ms PSI current's tail, not soma-axon ping-pong.
  - The script is `scripts/probes/n30_doublet_mechanism.py`, an exact replica of the pair update; figure `docs/media/s21_fly2_n30_doublet.png`, viewed.
  - Any one of these alone removes it: refractory ≥ 3 ms, AHP ≥ 7.5 mV, tau_s ≤ 1.8 ms.
- **Literature** (`docs/research/s21_mn5_literature.md`, Sonnet agent, A-D read):
  - **No readable PSI→MN5 decay, MN5 threshold, AHP or refractory value exists.**
  - The adult nicotinic decay bracket is 1.1-6.73 ms (Gu & O'Dowd 2006 in situ: 4.45-6.73). It spans the flip: the class values give one early spike only for tau_s ≤ 3 ms (tau_m ≥ 20), and none at the shared 5 ms.
  - The MN5 Cm of 127 pF is from Herrera-Valdez et al. 2012 (not "Kadas"), which gives tau_m 12.3 ms against Fayyazuddin's 4.4. The skeleton-area bound is about 25 ms. The DLMn tau_m blank is open.
- **Decision (DECISIONS 00:25): no fix adopted; the decider is Ben's measurement.** `docs/MEASUREMENT_LIST.md` item 1 is one MN5 whole-cell recording. Its four protocols give q, ρ, tau_m, threshold/AHP/refractory and the PSI EPSP decay, with a table of what each answer decides.
- **Next, for fly2:**
  1. If Ben's recording comes (or someone reads Ryglewski, Kilo & Duch 2014 EJN, or Ryglewski & Duch 2009, behind paywalls), set the measured values and pre-register the GF escape at seed 2. Score it against the sealed GF→DLM file (see the register).
  2. If ρ is measured above ρ*, the next candidate is a spike-initiation zone with a lower threshold, as its own registration.
  3. Building a per-edge decay on an axon or unitary-PSP edge (N29) is refused today. A measured PSI→DLMn decay would need that build first, CPU path and tests.
- **Done earlier in this worktree (20 Oct; details in FINDINGS and DECISIONS):**
  - The T1 fill, levels 1 and 2 (F-XCONN-3, F-XCONN-4): switch `connectome:T1|fill_from_other_animals`, neutral. Every T1 deficit we can repair is ruled out as the cause of the missing VNC rhythm and reach.
  - `docs/FLY_BRAIN_ZIP.md` rev 2: brain + body + world, species and individual layers, the scan file, scan → reconstruct → compare. The variation model is next to build.
  - Two-compartment DLMn first build (F-GJ-6): switch `cell_type:all|two_compartments_where_point_fails`, CPU only. PASS at the guessed pair, Ryglewski 2014 spent.
  - T4/T5 seeds 1 and 2: FAIL (F-VISION-15). The pair-strength arm is not continued as is.
- **Backhouse lessons:**
  - The WSL distro stops when no wsl client is attached. Hold a keep-alive from the Mac while anything runs: `ssh backhouse wsl -d Ubuntu -- bash -c "'exec sleep infinity'"`.
  - Send remote commands as a script (`… bash -s < /tmp/x.sh`).
  - Use at most 4 threads per job, and queue if the load is over 24.
- **Mac lessons:**
  - Detach long jobs with `nohup … > log 2>&1 & disown` and write the done-file from the job.
  - The worktree guard refuses heredocs that pipe into nohup or git, and `cd … && git …` chains with redirects. Use the Write tool plus plain commands.
  - `runs/` is a symlink into the shared checkout, so the Write tool refuses paths under it. Stage temp files in `/tmp`.
  - `timeout` doesn't exist on macOS.
- **Carried:**
  - **Body hook:** fly owns the premotor→MN transmission fix. When it lands on main, rerun step R as the held-out test on backhouse (`scripts/probes/run_proprio_reach.sh`, then `proprio_reach_score.py` and `proprio_reach_fig.py`).
  - **Stance loop (F-REFLEX-2):** three transduction blanks that fly2 can fill without touching the VNC: the CS load normalisation, CS rows per leg, and the front-leg FeCO assignment.
  - **Optic lobe:** the next candidates are T4/T5 dendritic input position (N30 in the optic lobe) and the input synapses' rest and release levels. Behnia 2014 stays sealed until an arm passes T4/T5.
  - **GPU:** `pytest tests/test_gpu_batched.py` still needs a run under JAX on backhouse (fix 609b238).
- **Stay out of:** lif.py graded release, the VNC files and fly's switches. Don't touch the flyapp worktree; run its tool from the copy `~/fly2-app` on backhouse.

## Where the project stands

- **Direction (Ben, locked 2026-09-28, re-stated 2026-09-30):** fill 100% of the fly's information at the highest plausible fidelity; the ledger fill fraction is the metric. Missing data is inferred with development models (size rule, lineage/hemilineage, birth order, wiring compensation, segment/side) and transcriptome tables, every built mechanism runs at its prior, then the bounded search of CONSTRUCTION.md / PLAN_NEXT.md. Behaviour and stability are guardrails, never objectives: do not fit to recorded walking or tune for walking (that was tried; see DECISIONS 2026-09-30 20:35).
- **Working model: m9c** since 2026-10-05 23:53 (m9r + fitted clock drive; m9r 03:31, m9f 02:51, m9v 2026-10-04 21:58, m9w 17:50, m9n 18:46, m9m 19:07, m9d 19:13, m9s 20:49, m9t 21:21, m9u 21:49): m9 plus the s12 body, sensor and contact switches above, none of them fitted. Below, **m9** (`profiles.M9`, the default from 2026-10-01 00:27 to 2026-10-04 17:50) = m8 + class gains re-searched on the rung-1 membrane (DN release 0.85, MN_other input 1.6, gustatory release 1.25, central size exponent 1.0; held out seeds 17-19 silent, bitter suppression, sugar dose response, bitter alone all pass; sugar -> MN9_L 5.7 Hz; F-RS-1). m8 kept (`FLYEMU_PROFILE=m8`).
- **Rung 2 (synapse receptor mix and kinetics): built, tested, not adopted** (F-R2-1; DECISIONS 2026-10-01 00:45 to 02:44).
  - What exists:
    - conductance synapses, with a GPU port equal to the CPU (`gpu/batched.py`; tests in `tests/test_gpu_batched.py`);
    - slow-receptor shares per cell from mRNA (`src/flyemu/receptors.py`);
    - `tau_s_inh`;
    - a charge-basis switch for slow shares (`cell_type:all|slow_share_basis`).
    All are neutral by default; the candidate profile is `m10p`.
  - Gates:
    - Gate A (equivalence) passed.
    - At priors the loop ran away, because muscarinic peak shares tripled cholinergic charge. Repair 1 (charge basis) restored silence on seeds 20-22.
    - Sugar -> MN9_L fell to 0 Hz, and 30 pre-registered class-gain candidates (best 0.7 Hz) did not restore it.
  - The cause is the conductance synapses themselves. The block sits 2 synapses in, at GNG108, and the inferred mechanism is inhibitory shunting.
  - **Fill from recordings and repair 2 (m10q, 03:01):**
    - e_inh is now -56 mV, recorded (Rohrbough & Broadie 2002; Wilson & Laurent 2005).
    - Conductance weights are referenced to threshold (`cell_type:all|cond_reference`).
    - Mi1/Tm1/Tm2/Tm4 rest at -55 mV, recorded (Behnia 2014), via `cell_type:all|rest_from_recordings` and `v_rest_shift_rec` rows in cell_types.csv.
    - Result: silent on seeds 26-28, sugar -> MN9_L 2.4 ± 1.6 Hz against a 5.5 bar. Not adopted; both rung-2 repairs are used.
  - **Class-gain search on m10q (pre-registered 03:23, running):** 24 candidates, new lever `cell_type:all|inh_cond_scale`. 12 are scored (DECISIONS 04:33):
    - every one clears sugar >= 5.5 Hz;
    - 3 are silent on seeds 29-31;
    - the leader is c008 (J 3.68, MN9 8.1 Hz).
  - **Detached job to collect:** the backhouse tmux session `s11_m10q_gs` (4 jobs, about 8 GB) is running the sugar stage for c012-c023, roughly 20 min per 4 candidates.
    - Check it with `uv run python scripts/search/class_search.py collect s11_m10q_gs`.
    - When it ends, run closed loops on seeds 29-31 for each new candidate with MN9 >= 5.5. Use `launch s11_m10q_gs runs/s11_m10q_gs/cands.json --no-sugar --seeds 29,30,31 --profile m10q --par 4`; it is resumable and skips the 36 finished c000-c011 loops, which are already copied in. Drop the sub-5.5 candidates from the job list first.
    - Then pick the lowest J that is silent on all three seeds and run the held-out test once (seeds 23-25 plus the held-out assays, `--heldout`). Adopt m10 if it passes.
    - The Mac copies of the c000-c011 loops are in `runs/s11_m10q_gs_cl/`.
- **Recording:** `docs/media/m9_closed_loop.mp4` shows 3 s of m9 in closed loop, body beside brain activity by class. The caption, `docs/media/m9_closed_loop.md`, says what it shows. It is a communication artifact, not evidence.
- **m8** (`profiles.M8`, the default from 2026-09-30 21:47 to 00:27) = m7 + rung-1 intrinsic conductances (A, M, Ih, T, NaP, Kv2, BK, SK + Ca pool) per type. SK/BK/Kv2/Ih/Ca fitted to Azevedo 2020 slow-MN current steps (`scripts/fit_spike_channels.py`; derived at that class, inferred elsewhere by channel mRNA); slow-MN θ/t_ref/drive from `*_rung1` rows. Gates passed: G1 silent on seeds 12-13; GPU (`gpu/batched.py`) equals CPU per cell on 300 ms whole CNS. Sugar -> MN9_L 2.7 Hz (m7 6.9), so the class gains were re-searched, giving m9. Mac brain cost 8.4x m7; use the GPU path for many runs. m7 kept (`FLYEMU_PROFILE=m7`).
- **Previous working model: m7** (`profiles.M7`, the default) = m6 + the motor size principle: per-cell input gain x (type geometric-mean volume / cell volume)^1.49 for 757 motor neurons (`src/flyemu/percell.py`, table `data/derived/percell_motor_factors.csv`). Adopted after a pre-registered held-out test: seeds 9-11 silent, bitter and sugar+bitter -> MN9_L 0 Hz, sugar -> MN9_L 6.9 ± 2.3 Hz. The same rule for central neurons (alpha 1.0) is built but neutral: it cuts sugar -> MN9 to 1.8 Hz because the m5 class values were fitted on the old gains (F-PERCELL-1).
- **Ledger v3** (`scripts/blank_ledger.py`, per source level): data used for 1.9% of 374 M slots; outside per-synapse grain 47% measured, 45% class prior (F-LEDGER-3). Rule-filled slots 3,282 after m7 (`runs/s11/ledger_after_m7.txt`).
- **Built, neutral, awaiting pre-registration:** hemilineage transmitter rule for 817 unclear cells (`connectome:unclear|nt_by_development`, LOTO 0.989, F-NT-2); leg joint damping (`joint:leg|damping`, neutral 1; 0.043 failed its mechanism check); muscle optimum join (`muscle:leg|optimum_join`, neutral 0) and femur-tibia flexor scale (`muscle:leg|ft_flexor_scale`, neutral 1), both failed their mechanism checks.
- **Fidelity rung 1 (intrinsic conductances per type): adopted in m8 at 21:47 after repair 1 (fit to recorded current steps; first scoring at priors failed)** (`src/flyemu/channels.py`, switch `cell_type:all|intrinsic_channels`, neutral 0, 6 single-cell tests). Channel and innexin mRNA per type: Davis + Özel (82 types, 73,253 neurons) and Allen VNC hemilineages (10,498 neurons); the rest take the class prior (F-RNA-4). At the guessed priors:
  - Mac step cost 8.9x;
  - sugar -> MN9_L 1.7 Hz;
  - VNC motor output silent.
  The cause was the guessed spike-to-SK coupling (F-RUNG1-1). The repair (fit to recorded current steps) gave m8.
- **Receptor data:** Özel 2021 optic-lobe calls (+12 glutamate-sign rows, F-RNA-2); Allen 2020 VNC atlas: every hemilineage co-expresses GluCl and iGluR, so VNC glutamate cannot be signed by lineage (F-RNA-3).
- **Session 11 diagnostics, kept as findings, all switches neutral** (F-RHYTHM-1, F-WALK-1, F-BODY-1, F-REFLEX-1): no VNC rhythm with spiking, graded or adapting local cells; DNg100 at 92 Hz adds ~0.7 Hz to leg MNs; joints follow imposed torque at 2 Hz but not 10 Hz (damping); FlyMimic femur-tibia extensor:flexor F0·r is 10:1 against Azevedo's measured flexor force; no femur-tibia resistance reflex (front-leg FeCO under-assigned, tibia pools under tonic VNC inhibition). These are information gaps for the ledger, not targets.
- **Template dead fly, flight configuration, GPU brain:** unchanged from session 10 (dead fly passes; tethered hover lift 0.99 with exact kinematics; batched GPU brain 0.37-0.45 s per member-second). Backhouse came back late in the session and ran rung 2's equivalence and Gate B runs. At 01:30 its WSL VM was about 95% full from another distro, and 16 parallel fly jobs were OOM-killed, so check `free -g` before launching there (each whole-CNS job needs about 2 GB).

## Regressions (Mac, session 11 end)

- Tests: the full suite passed (171) on 1 October at 03:10, after the m10q code.
- m9's guardrails passed at adoption:
  - seeds 12-19 silent;
  - sugar 5.7 ± 1.4 Hz, and 15.7 Hz at 200 Hz;
  - bitter and sugar+bitter at 0.
- An m9 sugar replicate at 3 trials gave 7, 6 and 7 Hz.

## Open items (carried)

- **Information gaps from session 11:** front-leg FeCO afferent assignment; FeCO rate model; resting activity of tonic VNC inhibitors; VNC glutamate sign per type (needs per-cell Allen labels); FlyMimic passive flexor element (dropped from leg_muscles.csv).
- **Per-cell rules:** the central size rule needs a joint class re-search (GPU); the hemilineage transmitter rule needs its own pre-registration.
- **B3/B4:** coxa DOF labels and envelopes (F-COXA-1); mid/hind muscle parameters are copies; leg damping unmeasured (FlyMimic c/k 0.05 s is a fit).
- **B5:** fused rate and facilitation guessed; fatigue built (guessed).
- **Flight:** fluid coefficients fitted to one condition; body pitch untuned.
- **Brain:** peptide receptor tables minimal; eLN->PN gap junctions absent.
- **State:** organ and clock parameters mostly guessed; ingestion path never exercised.
- **For Ben (optional, outward-facing):** raw data requests as in session 9 (eLife per-trial angles; FlyMimic mid/hind MTUs); per-cell cluster labels for Allen 2020 would let VNC glutamate be signed by cell type.

## Unverified foundations

| Item | Label | What would settle it |
|---|---|---|
| m5 class values (DN release 0.70, MN_other input 1.30) | inferred (search) | a broader search with margins; more held-out behaviours |
| Spring rest angles (fitted) and coxa labels | inferred / assumed (F-COXA-1) | coxa DOFs by function, refit |
| Coxa moment arms (front leg derived; mid/hind copied) | derived / guessed | FlyMimic mid/hind MTUs |
| Wing kinematics and Kutta lift 3.1 | guessed / inferred | measured hover kinematics; lift vs a blade-element model |
| Steering map coefficients (B11) | guessed | Melis et al. 2024 hinge model or data |
| Internal-state couplings (ISN, IPC, clock, dFB types) | inferred / guessed | per-population physiology |
| Haltere afferent identity SNpp25/SNpp34 (census) | inferred | haltere nerve labels (FANC/BANC) |
| Spiking vs graded mode for 2,969 unknown types | Bernoulli priors | per-class physiology |
| Motor size exponent 1.49 (Rin vs volume, 3 classes) | inferred | per-cell Rin and volume in one pool |
| Allen 2020 cluster assignment by marker scoring | inferred (proxy, r 0.72) | deposited per-cell labels |
| Everything in LESSONS labelled guessed/inferred | as recorded | see entries |

## Sealed and held-out data register

No sealed data was opened in session 11. Spent as held out for m7: closed-loop seeds 9-11, bitter->MN9_L, sugar+bitter (these had been spent in s10 for m5 too; seeds 9-11 were new). Seeds 12+ are fresh (12-13 reserved for the rung-1 G1 check, still unspent).

| Data | Status | Rule |
|---|---|---|
| Azevedo cell 180111_F2_C1 (slow MN) | seen (fit and dev) | dev only |
| Azevedo cell 181021_F1_C1, Piezo trials | **sealed** (unopened) | open only via `scripts/score_reflex.py` after a dev pass |
| Azevedo cells 180621_F1_C1, 181127_F1_C1, Piezo trials | **sealed spares** | as above |
| Azevedo CurrentStep trials (181021, 180621, 181127) | seen | none |
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
| flyapp `t4t5_ds.py` on v0r + flyvis rows (seed 0, both sets) | spent (s13 fly2, F-VISION-12: 0 of 8) | a new optic-lobe candidate needs a new seed or a new test |
| flyapp `t4t5_ds.py` on v0r + flyvis rows + flyvis pair strengths (seed 1, both sets) | spent (s14/s20 fly2, pre-registered DECISIONS 14 Oct 00:41; F-VISION-15): medulla FAIL 1 of 8, photoreceptor FAIL 0 of 8 | the next candidate needs seed 3 or a new test |
| flyapp `t4t5_ds.py` on the same + CT1 per-column compartments (seed 2, medulla set) | spent (s14/s20 fly2, pre-registered DECISIONS 14 Oct 01:05/01:07): FAIL 0 of 8, responses under the 0.5 mV floor | the next candidate needs seed 3 or a new test |
| Bypass S2 DNg100 15/25/40 mV and step R (8 arms) on the T1 fill | spent twice (s20 fly2): level 1 F-XCONN-3 (DECISIONS 20 Oct 22:02) and level 2 F-XCONN-4 (22:44); FAIL 3 of 3 and NO REACH 0 of 8 both times | a new VNC candidate needs a fresh check |
| Behnia 2014 step offset/onset ratios and filter peaks (Mi1, Tm3, Tm1, Tm2) | unspent; reserved as the flyvis pair arm's held-out recordings check (Ben, 13 Oct 22:53) | their amplitudes already set graded_range_rec |
| Azevedo 2020 Fig 5—fig supp 1A class rates (fast ≈1, int ≈10, slow ≈60 Hz, read off the plot) | seen (S4b fit target, 14 Oct) | none |
| Azevedo 2020 recruitment order slow→intermediate→fast (Fig 5G text) | **held out, unspent** (S4b falsified with no s*, 14 Oct 00:21; its 15/40 mV members unviewed) | score once, against a future pre-registered MN-layer fit, after its chosen value is written down |

## Things that will bite you

- **The default profile is now m7** (m6 + motor size principle). Regression commands need `FLYEMU_PROFILE=m4`. `standing.py` reads legacy per-unit torque states and fails under Hill mode: run it with m4. `scripts/model_keys.py` always dumps the m4 inventory.
- **Never sync code to backhouse while a battery runs there** (5 Oct 21:30): a test read a CSV mid-overwrite (`EOF inside string`) and failed spuriously. Wait for the battery, or sync to a separate directory.
- **Probes must step the motor path with `Organism.motor_step()`** and check `d.warning` (F-HARNESS-1/2).
- **closed_loop_check's "tonic" exclusion** uses per-type spontaneous drive; a sampled global drive makes every cell tonic (F-SAMPLE-1). Class tonic drive is counted as network activity.
- **GPU:** `.venv-gpu` sees the main venv through a `.pth`; XLA prints out-of-memory retries at start (shared GPU) and continues; runs are not bitwise reproducible in busy regimes; plasticity mechanisms (N21-N24, N27 glia, conductance, presynaptic inhibition) are refused, not ported; k > 1 in the closed loop is an approximation.
- **Flight needs a 0.05 ms step** (FlightMotor raises otherwise); halteres and wings are PD-imposed at 3 kHz bandwidth (5 kHz diverges).
- **parameters.csv:** append rows or rewrite with pandas `dtype=str, keep_default_na=False`; `build_class_params.py` rewrites the class rows (n2c_/n3c_/n5c_) and keeps the others. Retired placeholders are in `data/params/retired_placeholder_rows_s10.csv`.
- **backhouse was offline for session 11** (Director's note); it may need waking. A sync can fail silently inside a compound command: check `synced` before launching jobs.
- **GPU physics:** MJX 3.9 refuses this fly (mesh-contact margins on 69 adhesion pairs; body-transmission adhesion actuators); mujoco-warp needs MuJoCo 3.14 while flygym pins 3.9 (F-GPU-3). Body time is 30% physics, 70% our Python.
- From earlier sessions, still true: eLife stiffness units mN·m/° (F-PASSIVE-1); FlyMimic in g, mm, s; Hill mode replaces leg torques only; `date` is the only clock; `runs/` and `data/cache/` hold evidence (untracked); ≤ 8 model processes on backhouse; re-run `calibrate_joint_signs.py` after an adopted body change (not re-run for m5; the signs should depend on joint geometry, not on the springs m5 changes, but that is unverified).
- **Diagnostic probes** (`scripts/probes/command_walk.py`, `resistance_reflex.py`, `feco_paths.py`) measure; they are not objectives. In command_walk the whole-spectrum joint share includes the slow posture shift at replay onset, so read the 3-50 Hz share.
- **`FLYEMU_EXTRA_PARAMS`** adds candidate per-type rows for probes without editing cell_types.csv.
