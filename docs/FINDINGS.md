# Findings (construction programme, session 9 onward)

Append-only, newest last. Each result is one section: ID, the claim, the numbers, the evidence and its label. Sessions 1–8 are archived in `docs/archive/FINDINGS_s1-8.md`; their directly applicable results are distilled in `docs/LESSONS.md`. The programme is in `docs/CONSTRUCTION.md`.

| ID | Session | Claim | Status |
|---|---|---|---|
| F-MODEL-1 | 9 | The construction data model covers every registry key the m4 organism reads (280 keys, each owned by exactly one mechanism) | tested |
| F-TAXON-1 | 9 | 52% of modelled cells (86,541; optic columnar, AL LNs, VNC locals) have an unknown spiking/graded mode; now explicit Bernoulli unknowns | derived |
| F-HARNESS-1 | 9 | MuJoCo silently resets a diverging state; a probe that ignores it reads the spawn pose as a result | verified |
| F-DEADFLY-1 | 9 | The current body's dead fly collapses like a real one (onset 19 ms) but pins its wings on a stop because their spring reference lies outside the joint range | measured (model) |
| F-PASSIVE-1 | 9 | eLife 2025 leg stiffness is in mN*m/deg (0.11-3.2 uN*mm/rad); in our body the legs must be ~50-70x stiffer to stand, matching the paper's "70x" | verified |
| F-HARNESS-2 | 9 | Probes with their own stepping loop silently bypassed Hill mode; the recorded stability pass was for the passive changes only (corrected) | verified |
| F-TWITCH-1 | 9 | Leg motor-unit kinetics from Azevedo 2020 (read): fast/intermediate half-max ~8.5 ms; slow rate steps unpeaked at 500 ms; 2 spikes ~1.6x 1 spike (little facilitation) | verified (source); inferred (model constants) |
| F-REST-1 | 9 | Replicating the eLife weighted protocol, neutral spring references miss the loaded leg equilibria by up to 52 deg; a fit reaches <=13 deg but the middle leg needs rest angles beyond the assumed coxa-pitch and CTr envelopes | inferred |
| F-COXA-1 | 9 | flybody's coxa axes do not map one-to-one onto anatomical actions: the calibrated foot action of coxa yaw/roll differs between legs, and joints.py labels (yaw = long-axis rotation) contradict the axis geometry (roll = long axis) | derived |
| F-PASSIVE-2 | 9 | Projecting the eLife stiffness through the Jacobian of the paper's angles: FTi maps cleanly, but coxa/CTr joint stiffness differs from the name mapping by up to 9x and is strongly coupled; the 'legacy outside bounds' flag for front protraction was an artefact of the name mapping | derived |
| F-REST-2 | 9 | With coupled springs, fitted rest angles pass every dead-fly criterion; left/right fits agree in sign (flybody mirrors its joints); the front coxa solution is not unique | inferred |
| F-STAB-2 | 9 | The full template body ignites the known Mi18/DNge019/DNg12 latent loop on 2 of 3 seeds (brain keeps firing after silencing) | measured (model) |
| F-MUSCLE-2 | 9 | Mapping the sternal rotators by their action (Cheong 2024, read) leaves flybody's front/middle coxa-yaw directions with no muscle: under a function-based map, 30 of 84 antagonist muscles are undriven | derived |
| F-STAB-3 | 9 | Uniform adaptation (1 mV) silences the F-STAB-2 loop on 3/3 seeds but kills sugar->MN9 (0.7 vs 8.9 Hz): the stability/function trade-off of a global knob recurs with the physical body | measured (model) |
| F-MUSCLE-1 | 9 | FlyMimic front-leg muscles are in uN (F0 10.6-304) with 8-114 um arms; 20 of 84 flybody antagonist muscles get no MN under the legacy map, whose coxa assignments disagree with axis geometry | derived |

## Session 9 (27 September 2026): construction tasks 1-5

### F-MODEL-1: the data model covers the live model
`data/model/` holds 56 template mechanisms (+2 infrastructure), 120 numeric unknowns (`parameters.csv`) and the structural keys. Every key the m4 organism's registry reads (280 in total) matches exactly one mechanism (`tests/test_model_data.py`, built live). m4's wired values equal the table's `current_m4` column and lie inside their bounds. Bounds: 62 of 120 have a data basis, but only 22 sources have been read (`bound_verified`); the rest are leads. The validator also flags legacy body values outside biological bounds instead of widening the bounds: front-leg protraction stiffness (m4 1.0 vs measured 0.109 uN*mm/rad) and hind-leg protraction (1.0 vs 3.2).

### F-TAXON-1: spiking vs graded is mostly unknown
`data/model/classes.csv` (from neuPrint male-cns v1.0 itoleeHl/trumanHl, fetched s9) assigns every one of 167,111 modelled cells to 11,770 type rows, 34 circuit classes and (VNC locals) 37 hemilineages. Mode: graded 14,977 cells (photoreceptors measured; LMCs, APL inferred); spiking 65,593 (default, inferred from broad Para expression [abstract]); **unknown 86,541** (optic columnar incl. T4/T5, AL LNs, VNC local interneurons). Each unknown class has a Bernoulli prior row (P(graded) 0.7 / 0.3 / 0.5, guessed). The fidelity note calls the VNC share the most consequential Tier A unknown.

### F-HARNESS-1: diverging runs look like results
The first stiff-leg control (leg stiffness x10^4) "held the fly at 3.34 mm". That was the spawn height: MuJoCo hit BADQACC at 3 ms and reset the state silently. `deadfly.score()` now fails any run with a BADQACC/QPOS/QVEL warning (`test_a_diverged_run_is_flagged_invalid`). At x300 (stable) the control stands at 1.31 mm and the collapse metric correctly says "no fall".

### F-DEADFLY-1: the dead-fly baseline
Harness: every actuator at zero, standing neutral pose lowered to first ground contact, 1 s (`runs/s9_deadfly_baseline`). Current body (m4): collapse **pass**, fall onset 19 ms (real flies: within ~40 ms; the paper's OpenSim fly falls "within 20 ms"), trunk down at 58 ms, thorax 1.32 -> 0.70 mm; energy **pass** (never rises; hinge velocity rms 0.065 rad/s at the end); range limits **fail**: both wing-yaw joints at a limit 98.8% of the time; non-leg rest **fail**: wing pitch swings 54 deg. Cause: flybody's wing spring reference (yaw 86, roll 40, pitch -57 deg from neutral) is a spread pose whose yaw lies outside the +-15 deg range, so the passive spring holds the wing on its stop. With the springs referenced to the folded neutral pose (wing pointing back over the abdomen) and measured leg stiffness, every criterion passes: collapse at 19 ms, 0 joints at limits, energy decays, wings move 5 deg, head 4, abdomen 13.5. The leg rest-posture criterion is pending (see F-PASSIVE-1).

### F-PASSIVE-1: measured passive leg stiffness, units reconciled
Source: Wang et al. 2025 eLife (PMC12324252), full text and Figure 3 read. Table 1 prints "mN/deg", the methods "mN*m/deg", the discussion "Nm/deg"; Figure 3B's axis is "Torque (mN.m)". Under N*m/deg the springs would be ~570 uN*mm/rad and would hold the fly up easily, contradicting the paper's central claim; under mN*m/deg they are 0.109-3.21 uN*mm/rad. **Test in our body:** with the measured springs (DOF mapping by joint-axis geometry: coxa yaw = protraction-retraction, coxa roll = pronation-supination, CTr pitch = levation-depression, FTi pitch = extension-flexion) the dead fly falls; scaled x10 it still falls; x30 the trunk stays up but sags; x70 no fall. The paper: "torques at least 70 times larger are necessary". Verified. Recorded discrepancy: the methods list mesothoracic ext-flex 1.202e-8 and pro-sup 9.873e-8, Table 1 gives 2.5e-8 and 1e-8 (Table 1 used). **Rest angles are not entered:** Figure 3C's medians are equilibria with weights (>20x leg mass) hung on the tarsi, not spring rest angles. The Figure 3B example fly's fitted rest angles (85/97/139/142 deg) differ from the Figure 3C mesothoracic medians (~110/90/60/120). Next: replicate the tethered, weighted protocol in the model.

### F-MUSCLE-1: FlyMimic muscles in flybody units
flygym ships FlyMimic's front-leg model (15 MTUs; `data/params/flymimic_mtu.csv`). The file is in g, mm, s (thorax 0.76 mg), so F0 is in uN: 10.6-304 uN. Compiled without its (absent) meshes, its moment arms are 8-114 um. Pooled per flybody DOF and direction (`data/params/leg_muscles.csv`), the peak tibia torques are ~1.0 uN*mm (flexor) and ~10 uN*mm (extensor). FlyMimic's fitted activation time constants (0.1/0.4 ms) are far faster than measured twitches, so activation comes from the motor-unit twitch states instead (B5). Under the legacy MN->muscle->joint map, 20 of 84 antagonist muscles receive no motor neuron: one direction of coxa pitch on every leg (both on the front legs), femur roll on 5 of 6 legs, hind coxa yaw, and mid/hind tarsus. The legacy map assigns the promotors to coxa roll and the sternal rotators to coxa yaw. That is **not an error** (corrected in the extension hour; see F-COXA-1): the legacy map assigns each muscle by its foot action from the joint-sign calibration, and in flybody coxa roll moves the middle/hind foot forward. Only the two sternal rotators are placed by a rule (the coxa joint that moves the foot least, with an assumed sign). The literature read by the subagent (Cheong et al.; unverified by me) gives them swing roles instead: the anterior rotator "rotates the leg forwards", the posterior "rotates the coxa posteriorly". The orphan coxa-pitch directions move the foot up or down at the ThC, an action no named ThC muscle has; that DOF may be largely passive in the real fly.

### F-HARNESS-2: probes that step the loop themselves bypass new mechanisms
`closed_loop_check.py` (and 13 other scripts) called `Neuromuscular.step` directly. The first template-body stability check therefore ran without the Hill muscles it claimed to test. It was caught because a second run, after a kinetics change, reproduced every number exactly. A zero-force control showed the muscles do change the dynamics. Now `Organism.motor_step()` is the only motor path; 10 scripts use it, and the 4 that edit torque themselves raise under Hill mode (`test_bypassing_the_motor_path_in_hill_mode_raises`). Corrected result (DECISIONS): stable on 3 seeds; brain excluding ORNs 0.11–0.12 Hz vs m4 0.22–0.38.

### F-TWITCH-1: motor-unit twitch kinetics (Azevedo 2020, read)
Azevedo et al. 2020 eLife 9:e56754 (PMC7347388, full text read):
- a fast or intermediate tibia-flexor spike reaches half-maximal probe displacement in ~8.5 ms (Fig 4H);
- two spikes give ~1.6x the force of one, and force per spike saturates by ~10 spikes (Fig 4D/E; the authors suggest fatigue);
- a rate increase in slow units "did not reach its peak within 500 ms";
- hyperpolarising slow units took ~100 ms to take full effect.

The s9 fidelity note's "slow twitches do not peak within 500 ms" misreads this: the statement is about rate steps, not single twitches. Model constants chosen to satisfy the measurements (inferred): fast/intermediate rise 15 ms and decay 40 ms (force half-max 5.2 ms, leaving ~3 ms for conduction and mechanics); slow rise 200 ms and decay 100 ms (a 50 Hz step reaches 85% of steady state at 500 ms). NMJ facilitation defaults to 0 and is bounded at 0.5. A linear twitch model cannot give the slow units both a >500 ms rise and a ~100 ms relaxation; the paper leaves the cause of the relaxation open.

### F-REST-1: the eLife weighted protocol in the model
`scripts/passive_rest_protocol.py` reproduces the eLife setup:
- dead fly, thorax fixed;
- 0.19 mg weight at the distal tarsus (their wire);
- body rolled through -30, -15, 0, 15, 30 deg (rotation axis not stated; roll assumed);
- static equilibrium by minimising spring + gravity + weight potential, with measured stiffness;
- leg measured with the paper's angle definitions (tested on known geometry).

Against the Fig 3C medians (right legs, digitised by eye, +-10 deg; theta/phi/psi), the neutral spring references miss by:
- front 10/25/21 deg;
- middle 29/-6/4 deg;
- hind 52/19/-22 deg.

gamma is off by 50-75 deg on every leg, which suggests a convention mismatch in my reading of Eq. 11; it is not fitted.

Fitting the spring references of the three coxa joints, CTr and FTi (penalised toward neutral) gives residuals of:
- front 10/5/7 deg;
- middle 13/-1/8 deg;
- hind 1/0/1 deg.

The fit wants CTr references 39-100 deg from neutral. The middle leg presses two assumed range envelopes (coxa pitch +45 deg, CTr -100 deg): the envelopes, the DOF mapping or the roll assumption is wrong, not only the rest angles. The fit is stored (`data/params/passive_leg_rest_fit.csv`, inferred) but not wired: left-leg sign mirroring is unverified, and the fit set is the only data (no held-out check). Extra measured numbers read in the paper: on the tether, active forces take ~350 ms to decay; ~80x stiffer springs match normal standing height and 40x "barely" holds the body up (read). MN inactivation 52-114 ms plus a ~40 ms muscle delay (agent report; not found in my copy; unverified).

### F-COXA-1: coxa joint actions are coupled and leg-dependent
The joint-sign calibration (`data/derived/joint_signs_flybody.csv`) gives the dominant foot action of each coxa joint:
- coxa roll: protraction in the middle and hind legs, adduction in the front leg;
- coxa yaw: protraction in the middle leg, retraction in the front, adduction in the hind;
- coxa pitch: levation in all legs.

`joints.py` labels the coxa DOFs by NeuroMechFly conventions (yaw = long-axis rotation, pitch = promotion/remotion, roll = ad/abduction), but in flybody roll is the long axis. The range envelopes are therefore attached to the wrong motions (all labelled assumed). The literature agrees that the coxa motions are coupled (subagent report, read in Cheong et al. eLife PMC13384506, Azevedo 2024 PMC11348827 and Lesser 2024 PMC11356479):
- the promotors and the sternal anterior rotator are anterior/swing muscles;
- the pleural remotor/abductor and sternal posterior rotator are posterior/stance muscles;
- the rotators "rotate the leg forwards" and "rotate the coxa posteriorly";
- the femur reductor's function is unknown.

The legacy MN map (promotor -> roll, rotators -> yaw) and the s9 axis-geometry mapping of the eLife stiffness (ret-pro -> yaw, pro-sup -> roll) are both inferences that this questions. A principled fix projects the measured stiffness through the Jacobian of the paper's angles with respect to the flybody joints (K_joint = J^T K J). The FlyMimic middle/hind MTUs are not public; only the 15 front-leg muscles are in the repo (github.com/gizemozd/FlyMimic). FlyMimic's passive damping is c/k = 0.05 s (a model choice). No measured Drosophila leg damping was found.

### F-PASSIVE-2: project the measured stiffness, don't map it by name
`scripts/project_passive_stiffness.py` computes J, the Jacobian of the paper's four angles with respect to flybody's leg hinges at the neutral pose (right legs), and K_joint = J^T diag(K) J (`data/derived/passive_leg_stiffness_projected.csv`).
- **FTi matches the name mapping exactly** (0.974/1.432/0.974 uN*mm/rad), with off-diagonal share <= 0.07.
- **Coxa and CTr differ by up to ~9x.** Front coxa yaw is 0.96 by projection vs 0.109 by name; hind coxa roll is 5.15 vs 2.69.
- **Coxa and CTr coupling is strong:** the off-diagonal share is 0.9-3.1 times the diagonal. One stiffness per joint is a poor approximation there.
- **Front-leg coxa pitch and CTr pitch project identically,** because their axes are antiparallel at the neutral pose (a redundant pair of joints in flybody).
- **Tibia-tarsus gets 0,** because the paper's angles do not involve it; it stays a guess.

Consequences:
- the passive.py mapping is valid for FTi only;
- the "legacy m4 outside bounds" report for front protraction (F-MODEL-1) came from the name mapping, and by projection m4's 1.0 is close;
- the 70x collapse check (F-PASSIVE-1) used the name-mapped values; its conclusion (units) does not depend on the mapping, since every leg value moves by less than 10x and the needed scale was 30-70x, but it should be re-run with the projected, coupled springs.

Next: apply the full J^T K J matrix as a coupled passive torque on the leg joints (a registry switch), re-run the dead fly, the 70x check and the rest-angle fit.

### F-REST-2: coupled springs and fitted rest angles (extension hour)
- **Coupled springs.** `passive.apply_coupled` applies K = J^T K_eLife J per leg as a joint torque (switch value 2). The two null directions of each leg get the leg's median stiffness (guessed), so every direction has a spring. The hook's energy is counted in the dead-fly energy check. Neutral equivalence: a diagonal K reproduces MuJoCo's springs exactly (test).
- **70x check with coupled springs.** 1x and 10x fall; at 30-50x the thorax stays up (~1.2 mm) but the abdomen or head touches; at 70-100x the trunk stays off the ground. The paper reports 40x as "barely supported" and ~80x for a normal posture (read).
- **Rest-angle refit.** Coupled springs; energy scaled so the static solver converges (probe test: the equilibrium responds to the reference); left legs multi-started from the mirror solution. Residuals are <= 9/11/6 deg (theta/phi/psi) on all six legs. Left and right agree in sign (middle/hind within ~2 deg), so flybody's left/right joint conventions are already mirrored. The front-leg coxa yaw/roll split is not unique (CTr -64 to -71 deg and FTi +63 to +67 deg agree). The middle legs still press the assumed coxa yaw/roll envelopes (F-COXA-1).
- **Dead fly with the full template body** (coupled springs + fitted rest + folded wings): every criterion passes. Collapse onset is 11 ms (real flies: within ~40 ms; the paper's OpenSim fly ~20 ms). Final leg phi (front < middle < hind on both sides) passes, but that criterion is weak: the m4 body passes it too. The final posture is left/right asymmetric (front phi 50 vs 3 deg).

### F-STAB-2: the new body ignites a known brain loop
The full template body (coupled springs, fitted rest, folded wings, Hill muscles) with the m4 brain does not return to silence on seeds 0 and 2 (43-47 spikes/ms after all input is removed); seed 1 does. The persistent activity is the Mi18 -> DNge019/DNg12 -> leg MN loop (F-STAB-1 in LESSONS), which the uniform-strength brain holds latent; the new body's feedback ignites it. This is expected under the construction programme: once the body is physical, the missing brain mechanisms (N5 per-class strength, N3 background drive, N4 adaptation at class priors) must carry stability.

### F-MUSCLE-2: rotators by action
Cheong et al. (eLife, PMC13384506; read): sternal anterior rotator MNs "rotate the leg forwards during the swing phase"; sternal posterior rotator MNs "rotate the coxa posteriorly" (stance). In Hill mode (`muscle:leg|rotator_map=1`, default within Hill mode) they now drive the coxa joint and sign that the calibration says protract or retract that leg: coxa roll on the front/middle legs, coxa yaw on the hind (test). Consequence: 54 of 84 antagonist muscles have MNs (64 under the legacy rule). The rotators had been the only drive for several coxa-yaw directions, so under a function-based map flybody's front/middle coxa yaw has no muscle. Together with the orphan coxa-pitch directions, this suggests two of flybody's three coxa axes are passive in practice, or that coxa muscles should act on several axes at once (FlyMimic-style moment arms). Next: define coxa muscles by moment arms on all three axes.

### B7 adhesion gate (task 6 started)
`adhesion.gate` (switch `adhesion:leg|detachment`, off in m4): a leg's neural grip applies only when its tarsi carry normal load above `contact_min` (guessed 0.1 uN, bounds 0.01-5), and is released when shear exceeds `peel_ratio` x normal load (guessed 1.0, bounds 0.3-5). Tests cover the gate logic and that m4 is untouched. In the standing pose a foot's shear/normal is ~0.8, near the guessed peel ratio, so the gate will be sensitive to it. Not yet evaluated in behaviour.

### F-STAB-3: a global knob again trades function for stability
With the full template body, uniform spike-frequency adaptation of 1 mV per spike (tau 200 ms; inside bounds) quenches the Mi18/DNge019/DNg12 loop on all three seeds (0 spikes after silencing; brain excluding ORNs 0.09-0.11 Hz). The same setting drops sugar->MN9_L to 0.7 +- 1.1 Hz over 10 trials (baseline 8.9 +- 5.9 Hz). This repeats F-SFA-1 under the physical body. It supports the plan: class-level brain mechanisms fitted within bounds (task 11 and the search), not a global setting.

## Session 10 (27 September 2026): the complete template (every mechanism at least partial), class-level search, GPU port

### F-CONSTRUCT-1: every mechanism in the inventory now exists in the model
Ledger (`data/model/mechanisms.yaml`): 17 have, 39 partial, 0 absent (session start: 11 / 24 / 21). Built this session, each as a switch or neutral-valued parameter so m4 is unchanged (neutral-equivalence tests):
- brain: N1 mode per class group (3 Bernoulli switches), N2 class threshold offset and tau_m scale, N3 class tonic drive and noise, N5 class release and input scale (70 circuit classes, 420 rows), N7 mGluR/mAChR slow components, N8 NMDA-type with Mg block, N12 curated gap junctions wired into the organism (they were assay-only), N15 per-class transducer adaptation, N21 timing-dependent bidirectional KC->MBON plasticity, N22 forgetting, N23 compartmental APL, N24 ER->EPG plasticity, N27 lumped glial K+;
- body: B4/B5 anatomical coxa muscles with 3-axis moment arms and motor-unit fatigue (subagent), B10 wingbeat generator driven by power MNs, B11 steering map (guessed), B13 antiphase halteres, B15 TTM jump twitch, B17 pump-gated ingestion, B20 antenna oscillator with a sound field and JO-A/B, B23 convergence;
- state: S1-S4 lumped organs, N20 minimal peptide couplings, N25 sleep homeostat, N26 clock (subagent).
Most new parameters are guessed with guessed bounds (644 unknowns; 79 bounds from data). "Partial" mostly means one abstraction level below the CONSTRUCTION row, or parameters not yet constrained.

### F-WING-1: flybody's wing joints are mislabelled in joints.py
Measured on the model geometry at flybody's spread pose: `wing-yaw` sweeps the wing fore-aft (stroke), `wing-roll` raises/lowers it (deviation), `wing-pitch` turns it about the span (rotation). joints.py treats pitch as stroke (±80°) and yaw as deviation (±15°), which is why the legacy wings pinned on a stop (s8). Switch `joint:wing|range_by_function` (template on) sets envelopes by function. The wing campaniform proxy still reads wing-roll (deviation); it should read the stroke.

### F-FLIGHT-1: quasi-steady aerodynamics gives ~0.65 of body weight at hover kinematics
Tethered, horizontal body, exact imposed kinematics (218 Hz, 140° stroke, figure-of-eight deviation, rotation flipping at reversal): lift/weight 0.30-0.65 over rotation amplitudes 25-65° (sign calibrated: the opposite rotation sign gives -0.69). MuJoCo's default ellipsoid coefficients miss delayed stall and rotational lift; body angle and stroke-plane tilt are also untuned. PD tracking at 3 kHz bandwidth follows within 4° (p95) and gives 0.62 W at 0.05 ms; 5 kHz diverges. Converged in timestep (0.649 vs 0.644 W at 0.05 vs 0.025 ms). Next: fluid coefficients as bounded unknowns fitted to the hover lift, then body pitch.

### F-STAB-4: a declared class-level search finds stable, feeding templates; the held-out water criterion fails for a reason that predates it
Pre-registered search (DECISIONS s10) over N5/N3 scales of the classes carrying the Mi18/DNge019/DNg12 loop plus the MN9 path. 80 candidates, ~290 closed-loop and assay runs:
- single knobs are seed-fragile (a value silent on two seeds fails on the third);
- silence on all seeds needs DN release <= 0.70; that alone costs the feeding pathway (sugar->MN9 4.1 Hz at 0.6), because sugar->MN9 runs through DNs (DN release 2.0 gives 47.8 Hz);
- best by the objective: DN release 0.70 + MN_other input 1.30 (silent 3/3, sugar->MN9 7.3 Hz); the margin is narrow (DN 0.72 fails).
Held out, run once: template seeds 3/4/5 and m4-body seeds 0-2 silent, bitter->MN9 0 Hz (pass), water->MN9 0 Hz (fail, > 0 required). The unmodified m4 also gives water->MN9 0 Hz (100 and 200 Hz stimulus), so the failed criterion was already failed by the base model: my pre-registration chose a criterion without checking the baseline. By the rule, not adopted at first (hypotheses_not_adopted.csv). Repair 1 (post-hoc attempt 1 of 2, pre-registered, candidate unchanged, criteria checked on m4 first) on fresh evidence passed all four: template seeds 6-8 and m4-body seeds 3-5 silent, bitter suppression of sugar->MN9 kept (7.5 -> 0.0 Hz), sugar dose response kept (7.3 -> 96.4 Hz at 100 -> 200 Hz). **Adopted as m5**; then **m6** = m5 + sensory latency (below). m5/m6 are silent on seeds 0-11 with exact coupling.

### F-GPU-1: the batched GPU brain is exact and 30-90x faster per parameter set
`src/flyemu/gpu/batched.py` (subagent): JAX/CUDA, shared weights, per-member per-neuron parameters, delays by gathering a ring buffer of presynaptic outputs, event-driven sparse input. Whole CNS, noise off: spike rasters identical to `lif.Network` at every step for 500 and 2000 ms, also for a member with different class gains. 0.37-0.45 s wall per simulated second per member at B = 32-64 (CPU 11-39 s). Used on the real search: 810 sugar->MN9 trials (81 candidates x 10) in 362 s; all 70 candidates that had CPU scores agree to 0.1 Hz. Not bitwise reproducible run to run in busy regimes (spikes still matched). Plasticity mechanisms are refused, not ignored.

### F-SAMPLE-1: prior draws give brains from silent to epileptic
Task 13 acceptance (`sample_fly(seed, 1)`, template body, 3 s closed loop, 10 seeds): no runaway (> 20k spikes/step), NaN or MuJoCo divergence on the seeds scored, thorax 0.49-0.78 mm; but the brain's mean rate ranges 0.08-106 Hz (EPG up to 273 Hz). The priors bound each parameter but not the population: the search has to supply that. Joint constraints were needed (v_th > v_rest + 2 mV). The closed-loop probe's "tonic" exclusion treats every cell as tonic when the global drive is sampled > 0, so its silence number is meaningless for sampled flies.

### F-JUMP-1, N16/N17 and B23
- One GF volley (with GF->TTMn coupling) spikes TTMn within 0.1 ms and, with the TTM twitch (peak 100 uN·mm, guessed), lifts the thorax 0.63 mm in 20 ms; the legacy capped path lifts it by 0.
- Haltere Coriolis component: linear in rotation rate and antisymmetric between sides when demodulated by stroke direction (test).
- Tethered phase locking: haltere CS vector strength 0.95-1.00 (but ~20 Hz, not one spike per cycle); b1 MN locking 0.40 -> 0.55 with haltere->b1 electrical coupling 10 mV.
- Convergence: dead fly 0.1 vs 0.025 ms differ by <= 7 µm and <= 0.33°.

### F-STAB-5: the adopted stability survives realistic sensory latency but not a 1 ms sample-and-hold
- Holding each organism's sensory drive for 10 steps (the GPU loop's k = 10 exchange) breaks m5's return to silence on 5/12 seeds (3, 5, 9, 10, 11: 18-22 spikes/ms), and shifts brain rates by up to ~50% even where silence holds. The CPU loop with the same hold gives the same numbers, so this is the scheme, not the GPU.
- A pure transduction delay per sensory class at the prior centres (photoreceptors 12 ms, olfactory 25, gustatory 20, mechano/proprio 1, other 5) keeps silence on 12/12 seeds: adopted as m6 (pre-registered).
- So the stability depends on the fine timing structure of sensory input, not on its latency. The search engine must use exact coupling (k = 1), and the stability margin should be a search target.

### F-GPU-2: the GPU closed loop is exact; its speed is limited by per-step overhead
`scripts/gpu_closed_loop.py`: B organisms, brain as BatchedNetwork members on the GPU, bodies in worker processes (fork before JAX, shared-memory drive and raster blocks). With a k-step exchange it equals the CPU loop run with `closed_loop_check.py --hold-k k` on every metric (seeds 0-2, and m5 seed 3 at k = 10: 18.65 spikes/ms on both). Throughput: B = 12, k = 10: 10 s wall per member-second; k = 1: 20 s (CPU ~70 s). Bodies cost ~2.5 ms per 0.1 ms step (proprioceptive afferents 0.75, motor path 1.1, rendering ~0.2 at one render per 100 steps; the first render costs 1.8 s), so at k = 1 most time is per-step overhead; sending sensory rows only (17,966 rows, checked each window, no fallbacks) was built but gave no measurable gain (m6, B = 8, k = 1: 23.5 s wall per member-second; not a controlled comparison). The overhead is per-step Python, dispatch and pipe round trips; fusing the loop (MJX bodies, or several members per worker with batched messaging) is the next step.

### F-VAR-1: within-type variation is modest for most types, large and structured where it matters
Connectome only (male-cns, typed cells in types with >= 4 cells: 151,946 cells, 5,566 types; edges >= 5 synapses). Cell type explains 91% of the variance of log cell size, 86% of log input synapses, 83% of log output synapses and 87% of log input partners. Median within-type CV: size 0.12, input 0.27. But ~10% of types spread > 3x in input (p90/p10), concentrated in motor pools (59% of motor types; tibia/trochanter flexor and femur reductor pools 49-77x) and sensory types (cb_sensory 74%, vnc_sensory 67%). The spread is structured: within types, log size and log input correlate (median r = 0.67; > 0.5 in 70% of types); body segment (neuromere) explains 36% of within-type input variance in VNC types and soma side 12%. Per-cell wiring is already in the model; what the model lacks is per-cell physiology that follows this structure (e.g. the motor pool size principle, Azevedo 2020, measured; synapse number co-varying with dendrite size so total conductance is tuned to excitability, Tobin, Wilson & Lee 2017, lead). Implication: infer per-cell values from morphology, position and developmental rules with class-level rule parameters, rather than searching them or setting them to the type mean.

### F-GPU-3: where the body time goes, and whether MuJoCo's GPU backends can take this fly
Per 0.1 ms step for one m6 fly (Mac): MuJoCo physics 0.81 ms (108 DOF, self-collision, 85 mesh geoms, 69 contact pairs, fluid); our Python 1.8 ms (sensing 1.5, motor path 0.25, observe 0.07). MJX 3.9 (probe on JAX CPU; backhouse unreachable) refuses the model: (1) mesh-floor contact pairs carry a margin (69 pairs; used for tarsal adhesion) and MJX does not implement margins for meshes; (2) the adhesion actuators use body transmission, not supported. mujoco-warp (3.14) needs MuJoCo 3.14; the project pins 3.9 (flygym 2.1), so it could not be tested in this environment. Probe packages were removed again.

## Session 11 (30 Sep 2026, Mac only)

### F-LEDGER-3: by source level, the model uses data for 1.9% of the fly's information slots
Ledger v3 (`scripts/blank_ledger.py`; every ontology row names its mechanism and the grain its value varies at). Of 374 M slots: measured and used 1.89%, derived 0.01%, rule 0.00%, prior 1.81%, guessed 0.20%, absent 72.1% (per-synapse ultrastructure), measured but unused 24.0% (per-synapse locations). Outside the synapse grain: measured 47.2%, prior 45.1%, guessed 5.1%, absent 2.1%. Per quantity (91, equal weight): guessed 41.7%, absent 16.5%, prior 13.2%, measured 6.6%, derived 6.6%. Session 10's "26% filled" counted the unused synapse locations.

### F-PERCELL-1: the size principle holds for motor pools; the central rule breaks a fitted threshold pathway
Per-cell input gain x (type geometric-mean volume / cell volume)^alpha (`src/flyemu/percell.py`). Motor alpha 1.49 = slope of log Rin (Azevedo 2020: 150/300/700 MOhm fast/intermediate/slow) on log EM volume of the flexor classes (inferred). Within-type slope of log input count on log volume 0.87 (connectome). Motor pools only (m7): all guardrails and held-out checks pass (sugar->MN9_L 6.9 ± 2.3 Hz; seeds 0-11 silent; bitter and sugar+bitter 0 Hz); adopted. Central alpha 1.0 cuts sugar->MN9_L to 1.8 Hz while staying stable: the s10 class values were fitted on the old per-cell gains, so central per-cell rules need a joint class re-search.
Reconstruction incompleteness propagates into within-type rules: MN9_R has 633 input synapses vs 6,358 for MN9_L (volume 1.89e9 vs 4.35e9 voxels), which also explains session 4's unexplained left/right MN9 asymmetry. A guard (< 0.25x the type's median input count) flags 1,081 cells.

### F-NT-2: hemilineage predicts fast transmitter; 817 unclear cells can be filled
Leave-one-type-out over typed cells with a known transmitter: majority of the other types in the same hemilineage predicts consensusNt with accuracy 0.989 (cells) at hemilineage purity >= 0.9, baseline 0.584 (Lacin 2019 rule; `scripts/infer_nt_hemilineage.py`). Fill: 817 unclear cells (glutamate 447, GABA 263, ACh 107), including unclear VNC motor neurons as glutamate. Built as a switch (connectome:unclear|nt_by_development, neutral 0; 710 sign changes in the model); not adopted (needs its own pre-registration).

### F-RNA-2: optic-lobe receptor calls from Özel 2021 disagree with Davis 2020 on calls, agree on GluCl
Özel 2021 adult mixture-model calls crosswalk to 65 male-cns types. Type-gene ON/OFF agreement with Davis 2020 is 0.556 over 52 shared types (758 Davis-ON/Özel-OFF): ON thresholds do not transfer across platforms. GluClalpha is ON in 35/39 Davis GluCl-dominated types that Özel profiles. 12 new live glutamate-sign rows (-1).

### F-RHYTHM-1: no DNg100-driven front-leg rhythm with spiking, graded, or graded + adapting VNC cells
Assay dng100_legs (DNg100 0/100/200 Hz, readout 135 front-leg MNs, 5 trials, m6; rhythm = autocorrelation score above ISI-shuffled surrogates). Spiking: excess 0.000-0.003, MN rate 3.7 -> 4.4 Hz. Graded VNC local cells (2,778 types): DNg100 recruits ~600 cells and doubles MN output (6.2-6.8 Hz), excess <= 0.041. + adaptation 3 mV / 150 ms: driven excess <= 0.059, undriven 0.178 (tonic MNs wax and wane). Criterion was > 0.10. DNg100's 2-hop paths into front-leg MNs run 46% via ACh, 36% via GABA and 18% via glutamate interneurons (synapse-weighted, connectome). A rate model of the same VNC makes the rhythm (Pugliese 2025), so the missing ingredient is in our cell or synapse model (glutamate sign, graded rate map, rebound), or in proprioceptive feedback.

### F-RNA-3: VNC hemilineages co-express GluCl and ionotropic glutamate receptors; the atlas cannot sign VNC glutamate by hemilineage
Allen, Neville et al. 2020 adult VNC atlas (GEO GSE141807; `scripts/receptors_allen2020_vnc.py`, Sonnet agent). The authors' per-cell cluster labels are not deposited, so cells (26,777 after the paper's QC cutoffs; paper 26,768) were assigned to the 120 published clusters by marker scoring (per-cluster counts vs published: Pearson 0.72; a proxy, inferred). 21 hemilineages (16,343 cells) map to 24 male-cns trumanHl values. At the declared >= 30% expressing-cells threshold, every hemilineage expresses both GluClalpha (39-70% of cells) and GluRIA and/or GluRIB, so all 21 are "mixed" (20%: 21 mixed; 50%: 6 GluCl-only, 4 iGluR-only, 11 mixed; sensitivity only, not used). A hemilineage pools transcriptomic types, so the VNC glutamate sign needs per-type data (a VNC atlas with type labels, or physiology); no rows filled.

### F-BODY-1: body transfer at 10 Hz: damping and femur-tibia muscle balance, not the body, limit joint motion
Synthetic tripod replay and body-only probes (`scripts/probes/command_walk.py`, `scripts/probes/joint_impedance.py`; DECISIONS s11 18:44-20:00; all measured in the model):
- flybody's default leg damping (1, femur-tibia 0.4; c/k ~1 s) low-passes 10 Hz; at 0.043 the bare femur-tibia swings 1.8 rad p2p for 1.5 µN·mm. The muscles add no stiffness (impedance 2.5 µN·mm/rad). Ground contact is not the clamp.
- Coxa-trochanter (front/hind) already swings 0.58-0.91 rad at 10 Hz with low damping and force-velocity off.
- Femur-tibia does not, because its antagonists are 10:1 unequal (FlyMimic extensor F0·r 10.1 µN·mm vs flexor 1.04; fitted, and balanced inside FlyMimic by a 3.2·F0 passive flexor that `leg_muscles.csv` drops). Under any open-loop pattern that drives both comparably (symmetric, low-rate, size-ordered), the joint runs to the stronger muscle's end.
- Azevedo et al. 2020 (read: ~100 µN at a 417 µm lever, underestimated) puts the flexor at ≥ 42 µN·mm, ≥ 40x the model. With that scale (key `muscle:leg|ft_flexor_scale`, neutral 1) the 10 Hz torque is 12-16 µN·mm, but the joint pins at flexion. Moving the force-length optimum to FlyMimic's anatomy (`muscle:leg|optimum_join`, neutral 0) raises the extensor's gain 0.30 -> 0.44 and changes little. Both failed their pre-registered checks; neither is adopted.
Information gaps exposed (inferred): leg damping is unmeasured; FlyMimic's femur-tibia F0 split is fitted and contradicts the measured flexor force; its passive flexor element was dropped; muscle optimum angles were joined across skeletons by joint coordinate. The two switches stay neutral.

### F-REFLEX-1: no femur-tibia resistance reflex; the chordotonal signal reaches relay interneurons and stops at the motor neurons
`scripts/probes/resistance_reflex.py` (m7 closed loop, joint clamped, 0.4 rad 2 Hz) and `scripts/probes/feco_paths.py`:
- left front leg: only 4 claw + 4 hook FeCO afferents are assigned (rf 1 + 6; middle/hind 21-30 claw, 11-18 hook, 41-53 club). Front-leg proprioception is under-assigned.
- left middle leg: hook afferents fire strictly in phase (24 Hz in mV mode, 150-160 Hz in rate mode 200), and 45 relay interneurons are phase-modulated (e.g. excitatory IN21A022 onto the flexor pool, 0 / 68 Hz flexing / extending). But the tibia pools do not change (flexor 14-19 Hz per MN, ratio ≤ 1.08, same with afferents zeroed; extensor silent).
- per MN: 7 of 11 flexor MNs are slow units on the measured-rest-rate tonic drive with few weak inputs; the 4 large flexor and 2 extensor MNs get the strong relay input but sit under tonic inhibition (IN13A006, IN13A014, IN08A005, IN19A005; IN21A002, DNg105).
Reading (inferred): the resting leg circuit is "slow flexors on, the rest held off". Pool sizes (2 extensor, 11-15 flexor) match the anatomy. Information gaps exposed: front-leg FeCO afferent assignment; FeCO firing rates (mV mode caps hook cells at 24 Hz); resting activity of the tonic VNC inhibitors and the sign of glutamatergic 21A cells.

### F-RNA-4: ion-channel and innexin mRNA per type cover 47% of neurons; levels vary 2-10x between types for T-type Ca, KCNQ, Irk, Shab, eag, shakB, little for para, Shal, cac

`scripts/build_channel_expression.py` -> `data/derived/channel_expression_by_type.csv` (29 genes: Nav, Kv1-4, Kv7, Kv10-11, BK, SK, HCN, Cav1-3, Irk1-3, two-pore K, Kv beta, innexins). Measured (mRNA): Davis 2020 TPM (69 male-cns types) and Özel 2021 adult cluster means (65 types); 82 types, 73,253 of 176,422 male-cns neurons, mostly optic lobe. `scripts/channels_allen2020_vnc.py` (subagent) -> `channel_expression_allen2020_vnc.csv`: 21 VNC hemilineages (Allen 2020, proxy cluster labels: inferred), adding 10,498 VNC neurons at hemilineage grain. Inx6 and zpg absent from Davis; Inx6 from Özel.
- Relative level (type / median of profiled types), 10th-90th percentile across types: para 0.66-1.64, Shal 0.76-1.63, cac 0.75-1.34, Ih 0.46-1.39; Ca-alpha1T 0.10-3.5, KCNQ 0.33-4.7, Irk1 0.02-6.0, Shab 0.14-2.3, eag 0.07-2.0, shakB 0.19-2.8 (measured, derived normalisation).
- The two atlases agree weakly on relative levels: log r = 0.29 over 1,300 shared type-gene pairs (derived). On/off calls are near 1 for the core channels everywhere, so levels, not calls, carry the type differences.
Reading (inferred): mRNA level is a weak proxy for functional density; the rung-1 rule uses rel_level^beta with beta 0.5 (guessed, searchable 0-1.5). 52% of neurons (central brain outside the profiled types, most VNC) still take the class prior.

### F-RUNG1-1: intrinsic conductances at guessed priors silence the motor output; the cause is the spike-to-SK coupling, not the transcriptome densities

Rung 1 (`src/flyemu/channels.py`, all channels at priors, densities from F-RNA-4) is not adopted (DECISIONS 2026-09-30 21:12).
- Measured in the model:
  - sugar -> MN9_L falls to 1.7 ± 1.1 Hz (m7 6.9);
  - VNC motor spikes fall from 421 to 0 under the same brain-only sugar stimulus;
  - the Mac step costs 8.9x the LIF step.
- Derived from the gate curves: subthreshold channels move the median rheobase only 0.95-1.11x.
- Single-cell f-I: the cell fires 50 Hz leak-only at 12 mV of drive and 13 Hz with all channels on. It recovers to 35 Hz without SK; removing BK or Kv2 leaves it at 13 Hz.

Reading (inferred): the guessed Ca pool (1 per spike, tau 80 ms, K_d 2) opens SK ~30% at 10 Hz and ~60% at 40 Hz. That is a 3-4x per-cell rate cut, which compounds along multi-synapse paths. The coupling needs recorded current-step physiology (Azevedo 2020 MNs; central-neuron f-I from the literature) before any whole-CNS use. Probes: `scripts/probes/intrinsic_cost.py`, `intrinsic_rheobase.py`, `intrinsic_fi.py`; outputs in `runs/s11/rung1/`.

### F-RUNG1-2: recorded slow-MN current steps fix a strong fast AHP (BK) and a lower threshold, but not SK or the Ca pool
Fit of the rung-1 spike-triggered channels to 3 Azevedo 2020 slow flexor MNs (current steps, measured features in `data/derived/azevedo2020_current_step_features.csv`), 4 seeds (DECISIONS 2026-09-30 21:47).
- Identified (derived): BK is strong (6.8-8.9x g_L0 in the 3 lowest-loss seeds), and the effective threshold sits 19-26 mV above rest (LIF only: 33-35 mV). The best fit (loss 1.03) beats LIF only (2.1-2.4) and the guessed priors (2.9-3.8).
- Not identified: SK ranges 0.001-2.8 and Ca per spike 0.11-1.3 across seeds with similar losses. Recorded adaptation is mild (late/early 0.74-0.92), so any SK/Ca combination giving little adaptation fits. Seed 2 found a second basin (θ 34 mV, almost no BK, loss 1.47).
- The F-RUNG1-1 cause is confirmed: the measured cells adapt far less than the guessed SK coupling implied. The best fit has SK near zero (0.027).
- Held-out cell 181127: 3% rel RMS. Weak evidence: LIF only also gets 10%.
- With these values in the whole CNS (m8): G1 silence passes, sugar -> MN9_L 2.7 Hz (m7 6.9), GPU equals CPU per cell.
- Next discriminating data: recordings with stronger adaptation, or Ca imaging during trains, to pin SK/Ca; central-neuron current steps (none found in machine-readable form, inferred from MNs for now).

### F-RS-1: on the rung-1 membrane, silence no longer needs DN suppression, and MN_other input gain sets the sugar-to-MN9 rate
Joint re-search of the class gains on m8: 42 candidates, fit seeds 14-16 plus sugar (DECISIONS 2026-09-30 22:01 pre-registration; result 2026-10-01 00:27).
- All 42 candidates were silent in the closed loop, including DN release at 1.0 (m5 needed 0.70). The rung-1 channels (strong BK, fitted threshold) supply the stability that the DN gain used to provide.
- MN_other input gain is the dominant lever on sugar -> MN9_L. Gustatory release adds about 1 Hz per 0.25. MN_other release does nothing on this readout.
- The central size rule (exponent 1.0, its prior centre) survives. The MN9 rate is insensitive to it, since motor neurons use their own fitted exponent.
- The chosen point (DN 0.85, MN_other input 1.6, gust 1.25) passed all four held-out tests:
  - silence on seeds 17-19;
  - sugar+bitter 0.0 Hz vs sugar 4.8 ± 1.7;
  - sugar 200 Hz 15.7 vs 100 Hz 5.7;
  - bitter 0.0.
- Caveat: the fit bar (5 Hz) sits on a noisy slope. The trial SD is about 1.5-2 Hz, and the sugar-at-100 replicate inside the bitter assay gave 4.8. The class gains are inferred fit values, not measurements.

### F-R2-1: conductance synapses block the sugar-to-MN9 pathway two synapses in; slow receptor shares must be defined by charge
Rung 2 is built and equivalence-tested, but not adopted (DECISIONS 2026-10-01 00:45, 01:06, 01:18, 02:44).

What was built:
- Conductance-based synapses, including on the GPU, which matches the CPU exactly on toy networks and per cell on the whole CNS.
- Slow-receptor shares per postsynaptic cell from receptor mRNA (`src/flyemu/receptors.py`): 73k cells by type, 10k by VNC hemilineage, the rest from the population prior.

What was learned:
- **The basis of a slow share matters by about 60x.** Copying 3% of the fast *peak* into a 300 ms muscarinic pool adds about 2x the fast cholinergic charge. That ran the closed loop away (81-98 spikes/ms on seeds 20-22). Defining the share by charge (repair 1) restored silence.
- **Conductance synapses alone cut sugar -> MN9_L from 6.7 to 1 Hz** (3 trials each; a 10 ms inhibitory decay takes it to 0).
  - The loss sits at hops 1-2. MN9_L's main excitatory input, GNG108, falls from 11 to 1.3 Hz.
  - Raising the gustatory, MN_other and DN gains (up to 4x, 30 candidates) does not restore it.
- Inferred cause: inhibition gets stronger under conductance synapses. The scaling that keeps resting PSPs equal gives inhibitory synapses about 3x the conductance of excitatory ones at v_rest -52 and e_inh -70, so they shunt. The two reversal tests were not discriminating at 3 trials.
- Interpretation: the m4-m9 class gains were fitted with current synapses. They cannot carry over to conductance synapses without re-fitting the inhibitory side. The single borrowed v_rest (-52) and e_inh (-70) set how much inhibition grows, and are the next information gaps to fill.
- **Fill from recordings (m10q, DECISIONS 2026-10-01 02:49 and 03:01):**
  - Fly GABA reverses at about -56 mV, only about 4 mV below the model's rest, so fly inhibition is mostly shunting.
  - Keeping resting PSPs equal is then the wrong conversion. Referencing the weights to threshold, plus the recorded reversal, keeps the loop silent (seeds 26-28) and brings sugar -> MN9_L back to 2.4 ± 1.6 Hz (bar 5.5; m9 5.7).
  - The remaining gap is a class-gain question on a now physically grounded membrane, not a missing mechanism.

### F-BLANKS-1: the blanks audit finds 52 unslotted quantities and 5 tier A/B mechanisms with no owner
Session 12, docs/BLANKS_AUDIT.md (grain-by-grain walk of what is measurable in a fly against the ledger and the inventory).
- The ledger grows from 91 to 143 measurable quantities. Every quantity now names an owning mechanism; 22 are owned by 14 new registered stubs (status absent, switch read at neutral, any other value refused).
- Five stubs are tier A or B: N29 per-synapse parameters, N30 multi-compartment neurons, S6 hemolymph ions (A); B24 efferent sense gain, B26 cuticle compliance (B). Session 10's "0 absent mechanisms in tiers A and B" no longer holds. Nothing regressed; the quantities had no owner before.
- Per synapse (12 quantities), nothing in the model varies at its own grain; 6 run on class or global values. The model holds 0 % measured synapse-grain numbers. 13 % of synapse slots are measured but unused (synapse positions, polyadic structure, weak synapses).
- The slot total grows from 374.4 M to 1,701.7 M, mostly per-synapse STP and receptor mix. The headline "data in the model" share therefore falls from 1.90 % to 0.42 % with no change to the model. Outside the synapse grain: 50.0 M slots, 14.1 % measured.
- Ledger corrections: 8 rows had no carrier (`mech: none`); two channel rows were labelled absent although rung 1 simulates them; about 50,000 glial-cell slots were counted as body parts (grain mapping bug); 4 receptor fills were inconsistent.

### F-WING-2: the resting wings were lifted by body weight read as wing strain, then moved by a wing map written for the mislabelled joints
Session 12 B. m9, seed 12, 1.5 s, minimal policy, `scripts/probes/wing_drive.py`; outputs, logs and contact sheets in `runs/s12/wings/`. All numbers are model measurements.
- **The passive body is not the cause.** With all wing torques zeroed, the wings stay folded (end angles within 7°, peak 11°). The left wing motor neurons still fire tonically at 17-23 Hz (b1, b2, iii1, MNwm35), and the right ones do not.
- **Source of the drive.** Trace by `scripts/probes/wing_premotor_trace.py`, signed synapses × presynaptic rate, 3 levels up:
  1. SNpp30-33 are wing-nerve (ADMN) campaniforms with about 4.5 % of their synapses in leg neuropil.
  2. The legacy rule assigned them to the hind legs and drove them as leg load at 16.7 Hz.
  3. The drive passes through INXXX038, AN17A003 and AN17A031 to left IN17A039/027/034/035/064, then to the wing motor neurons.
  4. In short, body weight on the legs was read as wing strain. F-SENSE-NERVE-1 has the general rule.
- **The wing map was wrong in three places.** The legacy `motor_targets.csv` rows predate F-WING-1.
  - The basalar muscles b1-b3 drove wing-roll, which is deviation on this body, not stroke.
  - iii1 drove wing-pitch in the opening direction.
  - DLM and DVM got direct hinge torques, though they have no wing insertion.
- **Two fixes, each behind a switch with the legacy behaviour as neutral:**
  - `motor_map:wing|roles` uses `data/params/wing_muscle_roles.csv`:
    - basalars on +stroke (yaw), labelled inferred (Whitehead 2022; Tu & Dickinson 1996; Snodgrass 1935);
    - iii1 on -stroke toward the fold stop, labelled inferred (Melis 2024: likely homolog of the ancestral retractor that folds the wing; Snodgrass 1935);
    - DLM and DVM act only through the B10 flight generator, labelled measured anatomy (Dickinson & Tu 1997; Melis 2024).
  - `sense:mechano|assign_by_nerve`, see F-SENSE-NERVE-1.

| arm | non-leg torque/spike (µN·mm) | wing MNs > 5 Hz | end stroke L/R (°) | end rotation L/R (°) | peak \|angle\| (°) |
|---|---|---|---|---|---|
| m9 (legacy map and rule) | 10 | 4 | -10/-10 (fold stop) | 40/40 (stop) | 71 (deviation stop) |
| torques zeroed | 10 | 4 | 5/7 | -7/-6 | 11 |
| roles only | 10 | 4 | 160/0 | 41/-10 | 178 |
| roles + nerve | 10 | 0 (max 2.7 Hz) | 140/122 | -131/-83 | 177 |
| m9, legacy | 1 | 5 | 29/11 | 39/7 | 40 |
| **roles + nerve** | **1** | **0 (max 2.0 Hz)** | **8/10** | **-7/-3** | **18** |

- **Result.** With both switches at the declared default of 1 µN·mm per spike, the resting wings stay folded over the abdomen and are left-right symmetric. The contact sheet `docs/media/s12_wings_rest_roles_nerve.png` shows them folded throughout. The legacy arm at the same force holds the left wing raised (`docs/media/s12_wings_rest_legacy.png`).
- **The remaining cause is the 10× torque, not the wiring.**
  - Every run since session 5 has set the shared non-leg torque per spike to 10. That value is guessed, has no wing basis, and only reaches non-leg motor neurons, because the leg motor neurons use the per-neuron table.
  - At 10, sporadic 2-3 Hz spikes throw the wings to their stops. Each spike adds 10 µN·mm against a 1 µN·mm/rad hinge spring.
  - A rough estimate of one steering-muscle twitch is about 1 µN·mm (guessed: cross-section × specific tension × moment arm × twitch fraction).
  - Bergou 2010 measured the in-flight rotation-axis stiffness at about 5.2 µN·mm/rad, which is stiffer than the 1 µN·mm/rad spring used here.
  - Open: a wing torque per spike, and the resting stroke-axis stiffness.
- **Not fixed here.** In both arms m9 lies on its belly at rest. That is m9's live leg output on the template body, a separate open item. The wing-strain proxy still reads wing-roll velocity instead of the stroke (F-WING-1).

### F-SENSE-NERVE-1: 198 afferents that enter by wing, haltere, neck or other non-leg nerves were driven as leg sensors
- **The legacy rule.** `sensory.leg_from_roiinfo` makes any mechanosensory afferent with leg-neuropil synapses a sensor of its dominant leg.
- **The census check.** The male-cns census gives each type's entry nerve (`data/derived/sensory_census.csv`; leg nerves ProLN, MesoLN, MetaLN; Court et al. 2020 nerve names). By that census, the m9 organism drove 198 of 2,482 leg afferents that do not enter by a leg nerve (measured on the model, seed 0):

| organ | nerve | cells |
|---|---|---|
| campaniform sensilla | ADMN (wing) | 48 |
| campaniform sensilla | DMetaN (haltere) | 4 |
| hair plate | PrN (prosternal, neck) | 35 |
| chordotonal organ (census: leg) | ProCN | 30 |
| mechanosensory bristle | ADMN / DMetaN / PDMN | 20 / 39 / 22 |

- **Under `sense:mechano|assign_by_nerve`=1:**
  - A cell is a leg sensor only if its type enters by a leg nerve.
  - Campaniforms from ADMN join the wing-strain channel, which grows from 19 to 211 cells. This includes ADMN campaniforms that had no drive at all before.
  - Campaniforms from DMetaN join haltere strain (213 to 288 cells).
  - PrN hair plates join neck proprioception (3 to 38 cells).
  - No cell is in two channels.
  - The 110 leg afferents whose type has no census nerve keep the legacy rule.
  - The ProCN chordotonal cells and non-leg bristles now have no drive. They are a recorded gap, not a model of their organ. ProCN's identity is uncertain.
- **What it costs.** The m9 class gains were fitted under the legacy rule. With both s12 switches on, m9's silence gate still passes on seeds 12-19, so m9w was adopted (DECISIONS s12 17:50). The sugar gate is unaffected: that assay is brain-only with no body.

### F-COXA-2: flybody's leg-specific coxa ranges admit the measured rest angles, but the fly still lies on its belly, alive or dead
- **The switch.** `joint:coxa|range_source` (neutral 0) replaces the assumed joints.py coxa envelopes (±45/25/30° about the spawn pose, on mislabelled axes; F-COXA-1) with flybody's own leg-specific ranges (`data/params/coxa_ranges_flybody.csv`, flygym 2.1.0 joints.yaml; 18 joints). Label inferred: Vaxenburg et al. 2025 set those ranges to admit grooming inverse kinematics, not from measured joint limits.
- **Rest angles refitted inside them** (`data/params/passive_leg_rest_fit_coxa_flybody.csv`, `joint:leg|spring_reference` 2), same eLife weighted protocol as F-REST-1/2.
  - trf stalls at the neutral start (the neutral equilibrium sits on a coxa limit, every step rejected). Adding dogbox and a start from the s9 fit clipped into range fixes it.
  - Residuals (theta/phi/psi, deg): front 2.5/-10.5/5.2 and 0.0/-12.4/3.0; middle 6.9/0.4/4.9 and 6.8/0.4/4.7; hind under 0.3. Similar to s9.
  - Middle legs press flybody's coxa yaw and roll lower limits.
  - The front solution moves coxa pitch to about +90° (s9: -45°) at a similar residual. Three measured angles cannot pin five spring references, so the front split is not unique (as F-REST-2).
- **Dead-fly test with both** (`runs/s12/s12_deadfly_template_coxa`): all criteria pass. Fall onset 10 ms, thorax 1.32 to 0.77 mm, no joint at a limit, energy falls, wings move 4.8°.
- **Standing, m9w, seed 12, 1.5 s** (`scripts/probes/standing_rest.py`):

| body | thorax end (mm) | trunk on floor | legs carrying load at the end |
|---|---|---|---|
| legacy ranges, live | 0.54 | 96% of the run | rm, lh |
| legacy ranges, dead | 0.54 | 97% | lm, lh |
| flybody ranges + refit, live | 0.77 | 97% | lf, rf |
| flybody ranges + refit, dead | 0.77 | 97% | lf, rf |

- **Reading.** The coxa ranges raise the resting thorax by 0.23 mm, but the trunk still rests on the floor, and live equals dead to 0.2 µm. The contact sheet (`runs/s12/standing/standing_coxa_live_s12.png`) shows the front legs propped forward and up on the +90° coxa solution. That is not a resting posture. The switch stays at 0.
- **Also found.** flybody's native ranges exist for CTr and FTi too (e.g. CTr pitch about -9° to +115°). The s9 CTr rest angles (-60 to -71°) and the sunk CTr poses (-12 to -41°) lie below that native lower limit. The body uses the joints.py envelopes there, so CTr ranges are a further open item of the same kind. Both sources are inferred (grooming IK; a passive-posture fit through an assumed paper-to-hinge mapping), so neither overrides the other. Discriminating test, not started: map measured 3D walking and grooming joint angles (Karashchuk et al. 2021 Anipose; Haustein et al. 2024) through the same mapping. Angles below -8.6° mean flybody's range is too narrow; none below it means the rest mapping is wrong.

- **Measured CTr angles (19:39; agent extraction, `runs/s12/body/ctr_angles_lit.md`; table `data/derived/leg_angles_walking_haustein2024_karashchuk2021.csv`; figure-read).**
  - Source: Haustein et al. 2024 (Front. Bioeng. Biotechnol. 12:1357598), 12 flies walking tethered on a ball. The CxTr flexion angle is from inverse kinematics on motion-captured joint positions: 0° fully flexed, 180° colinear. That is the same definition as `scripts/probes/ctr_flexion_map.py`.
  - Mean ± SD trajectory envelopes over the step cycle: front 10-160°, middle 70-140°, hind 70-180°. These are not frame-level extremes, and no standing or grooming angles were found. Karashchuk et al. 2021 report coxa and femur rotation, not CTr flexion.
- **Mapped onto the model's hinge** (physical branch only, hinge above the fold):

  | leg | fold (femur flat on coxa) | measured walking envelope | flybody range |
  |---|---|---|---|
  | front | −30° | about −20° to 130° | −8.6° to 114.6° |
  | middle | −15° | about 55° to 125° | −8.6° to 114.6° |
  | hind | −67° | about 2° to 129° | −40° to 86° |

  - The upper ends are extrapolated past the map's 120° hinge limit at slope about 1.
  - The s9 front and middle rest references (−64/−71° and −60/−61°) lie below the fold. There the femur has passed through the coxa: the map's flexion rises again on that branch, to 34-45°. They are unphysical and cannot be rest targets.
- **Reading.** flybody's lower bounds hold the measured envelope. Its upper bounds cut about 15° (front, middle) and about 40° (hind) of measured walking extension. That is within figure-read uncertainty for front and middle, but not for hind.
  - Candidate, behind a switch, not built: CTr lower bound at the fold (physical_limit, derived from model geometry); upper bound at the measured envelope (measured_this_class, figure-read); s9 front and middle rest references dropped.
  - Discriminating test: Haustein's Dataverse tracking data give frame-level extremes. Then rerun the dead-fly and standing checks (F-STAND-3) unchanged.
- **Built, behind switches (20:09).** `joint:ctr|range_source` 1 (`passive.apply_ctr_ranges`, `data/params/ctr_ranges.csv`, written by `ctr_flexion_map.py --table` on a 0.5° grid):

  | leg | lower bound (fold) | upper bound | basis of the upper bound |
  |---|---|---|---|
  | lf / rf | −29.0 / −30.5° | 130.8 / 129.7° | measured envelope max (160°) mapped onto the hinge |
  | lm / rm | −14.5 / −15.5° | 125.3 / 124.6° | measured envelope max (140°) |
  | lh / rh | −68.0 / −67.0° | 112.0 / 113.0° | the model's straightest reach (flexion 170.6 / 171.0°), short of the measured 180° |

  - Correction to the table above: the hind upper end is not about 129°. The hind map peaks at a flexion of about 171° at hinge 112-113° and then bends back, so the model's hind leg cannot reach the measured colinear 180°. The linear extrapolation was wrong. The 9° shortfall is within the figure-read uncertainty of an envelope that touches 180°.
  - Tests (`tests/test_coxa_ranges.py`): switch off keeps −100..100°; the lower bound is a flexion minimum on every leg; the s9 front and middle references lie below it and the hind ones do not; the refit references below lie inside the ranges.
- **Rest references refitted inside the CTr ranges** (`data/params/passive_leg_rest_fit_ctr.csv`, `joint:leg|spring_reference` 3; `passive_rest_protocol.py --fit --ctr`; coxa ranges left at the joints.py envelopes):
  - Front and middle CTr references sit on the fold bound (−29 to −30.5° front, −14.5 to −15.5° middle). Coxa yaw (−30°) and roll (±25°) sit on the joints.py limits, which are assumed.
  - Residuals (theta/phi/psi, deg): rf 13.0/−4.2/9.0, lf 10.3/−1.6/7.4, rm 12.0/−0.5/7.2, lm 12.0/−0.6/7.3; hind under 0.3 and unchanged. s9 had rf 6.7/−11/2.0 and rm 8.9/−0.5/5.9.
  - So with the CTr held physical, the eLife equilibria are matched to about the ±10° digitisation, but only by pressing every front and middle leg against three bounds. Two of those bounds are assumed. The fit is consistent with the data, but it does not identify the references.
- **Dead fly and standing with the CTr switch** (20:13; `runs/s12/deadfly_template_ctr*`, `runs/s12/standing/standing_ctr_{dead,live}_s12.*`; m9d profile with `joint:ctr|range_source` 1 and `joint:leg|spring_reference` 3, seed 12, 1.5 s):
  - Dead-fly test (template body): range limits fail, lf and lm CTr on the fold bound 50-59% of the time (F-DAMP-2 table). This is by construction: the refit puts those references on the bound.
  - Standing: thorax ends at 0.635 mm dead and 0.634 mm live, with the trunk on the floor 98% of the run; at the end the load is mostly on rm (about 5.5-6 µN). Contact sheet (`standing_ctr_live_s12.png`, viewed): the fly lies on its belly with the left front leg raised in the air. That is not a resting posture.
  - The switch stays at 0. The CTr ranges themselves are physical (the fold) and measured (the upper bounds); what fails is that the references refitted inside them do not hold the fly up, as with every other passive configuration (F-STAND-3).

### F-STAND-3: the fly cannot stand because the model has no resting support drive, and no measurement fixes one
Target (held out; `data/measurements/targets_session6.csv`): Wang et al. 2025 measure a median standing head height of 0.5 mm above the motor-silenced collapse. For this body that is a thorax origin near 1.0 mm (inferred). Pratt et al. 2024 put the dorsal thorax at 0.51 body lengths, about 1.04 mm, at the slowest walking speed. The model's dorsal thorax is the origin plus 0.54 mm. The model ends at 0.54-0.77 mm with the trunk on the floor.

- **The brain contributes nothing at rest.** On m9w the only leg motor neurons with tonic firing are the slow tibia flexors, 12.6-15.6 Hz per leg. Their spontaneous drive (36.45 mV) is inferred, fitted to a measured 24.8 Hz. ThC, CTr and TiTa motor neurons are silent, so the live and dead runs end within 0.2 µm of each other.
- **What holding the pose would take** (`scripts/probes/stand_budget.py`, thorax held at spawn by a stiff spring, joint torques read off). Units µN·mm.
  - CTr needs 0.94-2.90 of hold torque per leg. The passive springs push the wrong way, by -0.42 to -0.83.
  - ThC pitch needs about 2.0-2.4 on the front and hind legs.
  - The CTr extensor Hill unit's capacity is r·F0 = 8.9 (F0 324 µN, r 0.027 mm; FlyMimic front leg, copied to mid/hind). Holding therefore needs a resting extensor activation of about 11-32%.
- **Tonic slow units are two orders short.** Suppose every leg pool got the slow tibia flexor's resting rate (each pool's slow units capped at the slow class's EM-volume maximum). Hill activation is the force-weighted mean of unit activations, and slow units give 0.05 µN each (Azevedo 2020 class value; measured class, model use inferred). The result is about 0.3% activation, against the 11-32% needed.
- **Real flies use active force at rest** (Wang 2025, read). Silencing the leg motor neurons (e49-Gal4 > GtACR1) makes standing flies fall:
  - fall onset 40-300 ms after light-on;
  - median fall rate 1.3 mm/s, against 37 mm/s for their passive-only simulation;
  - their model reproduces the slow fall only if active force decays with τ ≈ 100 ms (MN inactivation onset about 30 ms, 90% by 52-114 ms, plus about 40 ms muscle delay);
  - holding the median 0.5 mm stance needs about 90× the passive torque.
  - Adhesion is not what fails. The silenced flies fall with their feet intact. In the model, the feet slide at the friction limit (traction/normal force 1.0 at μ = 1). That follows the collapse; it does not cause it.
- **The reflex route is sparse and lopsided.** The leg load sensors (campaniform sensilla; `scripts/probes/load_reflex_paths.py`) number, per leg: lf 6, lm 2, lh 15, rf 2, rm 0, rh 9.
  - Direct synapses from them onto support motor pools exist only on the front legs: lf sternotrochanter 46 and tergotrochanter 159; rf tergotrochanter 27.
  - Two-hop paths are below 2 synapse-equivalents per pool.
  - A left-right asymmetry of 6:2 and 2:0 is an assignment or annotation gap, not anatomy. It ties standing to the sensor-assignment item of B.
- **The missing value.** The resting firing rate (or recruitment) of the trochanter-depressor pools (tergotrochanter, sternotrochanter) and the coxa promotor/remotor pools. No Drosophila recording of resting rates for these pools was found (subagent search plus own reading). Azevedo 2020 and 2024 record tibia motor neurons only.
- **What would not be honest.** Filling that value so the fly stands at 1.0 mm would be a behavioural fit, which the Director's instruction rules out. Possible routes are listed in DECISIONS s12 (18:23).
- **Resolved for now as option (a)** (Director 5 Oct 02:05; DECISIONS 02:41, result 02:50). Option (c), the connectome's own load reflex on m9f with nothing fitted, fails on seeds 12-14. Live and dead both lie down by 40 ms and end within 6 µm of each other. The only tonic leg motor neurons are the slow tibia flexors (12.6-16.1 Hz). The load afferents fire at 21-23 Hz on five legs and are silent on lh. The homolog search found no resting rate for any coxa or trochanter support pool in any insect, so there is nothing to fill. The blank stays open and the fly lies down.
  - Fall after silencing at 500 ms: 2-4 µm, because there is no standing state to fall from. The model's only fall is passive, from placement at 1.32 mm: onset within 10 ms, 15 mm/s. Real silenced flies fall at 1.3 mm/s after 40-300 ms; Wang's passive-only model falls at 37 mm/s.
  - Side note: the lh load afferents never fire at rest, while every other leg's fire. **Answered 5 October 03:30** (DECISIONS 03:25; `scripts/probes/load_afferent_legs.py`, `scripts/probes/mirror_audit.py`). It is that leg's load, not assignment. The dead fly lies rolled onto its right side with lm and lh in the air. lh's strain proxy is 0.83 against 1.7-6.4 on the other legs, so its drive (2 mV + 8 mV × tanh(load)) sits at 5.1 mV, under the 7 mV threshold. The load channel saturates above about 2 load units, so it reports little more than "loaded or not".
  - The roll started in mid-air (0.9° at 10 ms) from a left/right difference in the fitted leg rest angles. The F-REST-1 targets are right legs only; the left legs were fitted to the same targets and reached another solution of a non-unique fit (front coxa roll 23.2° against 5.0°, yaw −29.4° against −19.7°, CTr −63.6° against −71.1°). `joint:leg|rest_mirror` 1 gives the left legs the right legs' values (bilateral symmetry inferred). Results: roll at 30 ms −0.2° (was 1.9°); final roll 16.2° (was 25.3°), still onto the right side; gate PASS. Adopted as **m9r**. Sheet `docs/media/s12_rest_mirror_dead.png` (viewed).
  - The tip-over remains, smaller and in the same direction. The splayed lying pose looks sideways-unstable, and residual body asymmetry picks the side. Residual asymmetries after mirroring (audit): leg damping up to 10% (lf coxa yaw 0.049 against 0.053; it is derived from each leg's own stiffness projection), FTi ranges under 1°, segment origins up to 0.15 mm (flybody scan), and the left wing lying on top (guessed). lh still carries no load, so its load afferents stay silent. That is posture under option (a), not a sensor fault.
  - The damping and stiffness residual is specimen geometry (`scripts/probes/mirror_legs_geometry.py`, `runs/s12/stand3/mirror_legs_geometry.json`). flybody's neutral hinge angles are identical left and right. The scanned legs differ: keypoints by up to 25 µm on the front legs and up to 14 µm on the others, and segment lengths by up to 1.6% (front tibia-tarsus 553 against 544 µm; mid femur 830 against 840 µm). The coupled stiffness built from that geometry (JᵀKJ) differs by 6.6% (front), 2.5% (mid) and 3.2% (hind); the damping follows it. This is measured geometry of one specimen, within scan uncertainty, so it stays.
- **Is the gap upstream of the legs? Director leads (5 Oct 03:00), checked 03:45-03:52.** Recorded either way.
  - **The model's descending drive at rest** (`scripts/probes/dn_rest_rates.py`; m9r, seeds 12-14; senses on 200-1200 ms, then 300 ms with all afferent drive removed; `runs/s12/dnrest/`, backhouse):
    - No descending neuron (DN) has its own tonic drive. Only 60 cells in the whole model do, the slow tibia flexor motor neurons (`Ti flexor MN`, `Acc. ti flexor MN`; inferred, fitted to Azevedo 2020's resting rate).
    - With the afferent drive removed, all 1318 DNs are silent (0 spikes in the last 200 ms, every seed).
    - With senses on, 91-93 of the 1318 DNs fire (6.9-7.1%): 12.3-12.7 Hz among those active, 0.87 Hz averaged over all DNs, median 0.
    - The firing DNs are mostly gnathal-ganglion types (DNge, DNg, including the DNg12 types). On seed 12, the largest excitatory input to 57 of the 91 is head bristle mechanoreceptors (BM, BM_InOm, BM_Taste, BM_Vib by type).
    - The head-touch channel drives every head bristle cell with the total head contact force (`extrasenses.py`; gain guessed), and the lying fly's head is on the floor (F-DAMP-2). The model's resting DN activity is therefore a by-product of option (a)'s posture, not a tonic descending drive.
    - DNs with published recordings are silent: DNa01, DNa02, the giant fiber DNp01, DNp02, DNp07, DNp09, DNp10, DNb02, DNa05, DNg11, DNp42, MDN, DNb06, DNa15 and DNg13. One DNb05 fires at 7-9 Hz. DNg02 and DNp50 are not type names in this connectome.
  - **What real flies show** (`docs/research/s12_resting_dn_activity.md`; one source agent plus my own read):
    - No paper found gives a resting DN rate in Hz.
    - DNa02 "hyperpolarized whenever the fly stopped walking" (Rayshubskiy et al. 2025 eLife, Fig 6A-B, text read); the text gives no number.
    - Calcium imaging of about 100 DNs per fly: "Only a very small fraction of DNs encode resting"; about 60% encode walking, about 15% head grooming (Aymanns, Chen & Ramdya 2022 eLife 11:e81527, read). The authors propose, without testing it, that the rest-encoding DNs "could actively drive the tonic muscle tone required to maintain a natural posture". Their cell types are not identified.
    - VNC imaging (Chen et al. 2018 Nat Commun) and whole-brain imaging (Aimon et al. 2019 PLoS Biol) give no resting level that converts to a rate.
    - In Azevedo 2020, a nicotinic antagonist lowers the slow flexor's resting rate and resting force (about 1.5 µN). So part of that pool's resting drive is cholinergic synaptic input (inferred), from central premotor neurons or cholinergic leg afferents; the paper does not say which. In the model, all of it is the cell's own drive.
  - **Reading.**
    - Mostly silent DNs at rest agree qualitatively with the imaging. No measurement shows the model's DNs to be too quiet, so the gap is not shown to be upstream of the legs.
    - A small rest-encoding DN population exists in real flies. Its types and rates are unknown. It is a brain blank with no fill value, and it already has an owner: the per-type `spontaneous_drive` (`lif.py`, declared default 0, "no tonic drive"). No new mechanism is needed, only a value nobody has measured.
    - Where the support drive originates (descending, VNC premotor, or sensory feedback) is unresolved.
    - Side defect found: one head-contact scalar drives all head bristle types, including interommatidial and taste-peg bristles. Head touch has no spatial specificity (recorded, not changed).
  - **Next discriminating experiment:** identify the Aymanns 2022 rest-encoding DNs by their stated positions (medial, near the giant fibers; lateral) against the connectome's DN somata or axon tracts in the neck connective. Then check whether those types reach the support pools within two synapses. If they do, the blank has a named location, though still no rate.
  - **Done (Director item 2, 03:56-04:05; matches inferred, no drive set):** details in `docs/research/s12_resting_dn_activity.md`, scripts `neck_rest_dn_match.py` and `rest_dn_reach.py`.
    - Method: every BANC DN axon was placed in the BANC neck cross-section (Dataverse 8.1, plane y = 92500). Types with SEZ somata were excluded because Aymanns' driver "lacks expression in the subesophageal zone".
    - Candidates graded low (none higher): 21 brain DN types within 5 µm of a giant fiber (for example DNp07, DNa13, MDN, DNb01, DNb07) and 5 at the lateral extremities (DNa02, DNa06, DNb06, DNp20, DNp33). 156 of the 182 lateral types are SEZ cells and drop out.
    - Leg reach: DNp07 and DNa02 rank above the 90th percentile of all DNs for two-hop reach onto leg motor neurons. Both make over 100 direct synapses per cell onto leg motor neurons.
    - All low candidates are silent in the model at rest.
    - Caveat: DNa02 hyperpolarizes when the fly stops (Rayshubskiy 2025), so if it is a rest-encoder its rest signal is a decrease.
    - The blank now has candidate locations, still no rate.

### F-SENSE-NERVE-2: each leg sensor on its own entry nerve; the connectome annotates only 2 load sensors per leg
- **What option 1 still got wrong** (`sense:mechano|assign_by_nerve` 1, F-SENSE-NERVE-1):
  - It looked up combined type names whole. "SNpp29,SNpp63" and "SApp06,SApp15" have no census nerve, so 23 wing- and haltere-nerve campaniforms stayed in the leg load channel, and 29 notum- and wing-nerve bristles stayed in leg contact.
  - It gave each type one leg from its dominant neuropil. For the 12 annotated leg campaniforms (SNpp53) that agrees with the cell's own nerve and side in only 2 of 12. These cells project bilaterally and across segments, so the neuropil rule mislabels them. For the other leg afferents the two rules agree for 98.7%.
- **Option 2** (`assign_by_nerve` 2; `sensory.entry_nerve_per_cell`): the cell's own male-cns entry nerve and root side (measured) give its leg. ProLN gives front, MesoLN mid and MetaLN hind. The prothoracic DProN, VProN and ProAN nerves, where the front hair plates enter, keep the type rule. Combined names are split into their parts. Test: `tests/test_sense_nerve2.py`.

| channel (seed 0, m9w) | option 1 | option 2 |
|---|---|---|
| leg load (campaniform) | 34: lf 6, lm 2, lh 15, rf 2, rm 0, rh 9 | 13: 2 per leg (lh 3); all SNpp53 |
| leg contact | 1793 | 1764 |
| leg joint angle / velocity | 78 / 379 | 78 / 392 |
| wing strain / haltere strain | 211 / 288 | 237 / 408 |

- **Silence gate.** It passes on all 8 seeds, 12-19: 0 spikes/ms in the last 100 ms, thorax 0.535-0.55 mm, no MuJoCo warnings, no NaN. Adopted as m9n (DECISIONS 18:28).
- **Load reflex under option 2** (`scripts/probes/load_reflex_paths.py --set ...=2`). Same-leg direct synapses from the campaniforms onto support pools are nearly gone: lh tergotrochanter 7, lh tibia flexor 6, rh tibia flexor 5. Two-hop paths are below 1 synapse-equivalent per pool. The front-leg paths in F-STAND-3 came from misassigned cells, so route (c) of DECISIONS 18:23 has almost no annotated substrate.
- **The real gap is annotation, not assignment.** Counts in male-cns leg nerves, against the literature (agent report `docs/research/s12_leg_sensor_counts.md`):
  - Campaniforms: 12 annotated (2 per leg). The femoral field alone has 11 numbered sensilla (Saltin 2025, quoting Dinges 2021; secondary). Dinges' per-leg table was not readable. Annotated load sensors are at most about a fifth of the real count.
  - Hair plates: 96 in the leg nerves, plus front-leg plates via DProN/VProN. Pratt 2026 counts 214 hair-plate neurons in 42 plates on the six legs (read), about 36 per leg.
  - Chordotonal: 372 in the leg nerves, about 62 per leg. Mamiya 2018 counts 135 front-leg FeCO neurons labelled by iav-Gal4, which is 80% of the population (read), so about 170 in one front-leg FeCO (derived).
  - Unlabelled: about 180 leg-nerve cells annotated "leg proprioceptor, organ unassigned" (SNppxx 80, untyped 66, SNpp40 32, SNpp55 7), and 442 "unknown sensory" leg-nerve cells (262 on the front legs). None of them is driven. They are the likely home of the missing campaniforms and chordotonal neurons.
- **Next discriminating step.** Assign organs to the unlabelled leg-nerve cells by an outside annotation (FANC/BANC leg-sensor labels via the existing crosswalk, `data/derived/banc_proprio_crosswalk.csv`). Keep the match uncertainty explicit. Then re-count the campaniform-to-support-pool paths. Until then the load channel is 2 cells per leg, which is a recorded under-count.

### F-MUSCLE-MH-1: mid and hind leg muscles derived from measured segment size, not copied; the TTM torque from fibre data
- **Before.** Every mid- and hind-leg Hill muscle was a copy of FlyMimic's front leg (guessed). FlyMimic (arXiv 2509.06426) built mid/hind muscle paths from micro-CT but fitted forces for the front leg only (agent report `docs/research/s12_leg_muscle_anatomy.md`).
- **Measured input.** `scripts/probes/leg_segment_geometry.py` measures each leg segment of the flybody mesh: length, mid-third cross-section, and the width at the proximal and distal ends (`data/derived/leg_segment_geometry_flybody.csv`). The mesh comes from one confocal-scanned female, so these are one-specimen numbers. Ratios to the front leg (left/right mean):

| ratio to front leg | coxa area | coxa distal width | coxa proximal width | femur area | femur distal width |
|---|---|---|---|---|---|
| mid | 0.579 | 1.106 | 1.227 | 0.770 | 1.014 |
| hind | 0.932 | 1.072 | 1.442 | 1.058 | 1.016 |

- **Rules** (inferred; `scripts/build_midhind_muscles.py`; switch `muscle:leg|midhind_source` 1). Each front-leg FlyMimic member is scaled by the segment that houses it. Force scales with that segment's cross-section, and moment arm and optimal length scale with the width of the joint it works on:
  - muscles inside the coxa (trochanter flexors and extensor) follow the coxa;
  - the tibia flexor and extensor inside the femur follow the femur;
  - the 7 thorax-to-coxa muscles take force × (coxal opening)² and arms × the opening;
  - the two sterno-tergo-trochanter extensors take force × (coxal opening)², with arms × the coxa distal width.
  - The assumptions are the same fill fraction, pennation and specific tension as the front leg, and one strain per radian. Tibia-tarsus muscles stay placeholders (guessed).
  - Kept as bounds in `data/params/leg_muscle_midhind_scale.csv`: the copy (all factors 1) and a volume rule (area × length / width).
- **Effect on torque capacity** (F0·r, against the copy):

  | joint | mid | hind |
  |---|---|---|
  | thorax-coxa | 1.85 | 3.0 |
  | CTr flexor | 0.64 | 1.0 |
  | CTr extensor | 1.62 | 2.17 |
  | femur-tibia | 0.78 | 1.07 |

  The thorax-coxa rule is the weakest assumption: the coxal opening is the only thoracic dimension measured per segment.
- **TTM (B15).** Peak torque is 90 µN·mm (inferred; 5-95% 53-134), replacing the guessed 100.
  - Force: 27 fibres (Jaramillo 2009) × 71.2 × 40.7 µm (Jarvis 2021) × 34.7 mN/mm² (Jarvis 2021) = 2.7 mN.
  - Arm: 0.033 mm, FlyMimic's front sterno-tergo arm × the measured mid/front coxa distal width.
  - Cross-check: about 60 µN per leg at the tarsus over a 1.5 mm lever, about 120 µN for both legs. Zumstein measured 101 µN and derived 274 µN from kinematics (abstract level).
  - **Double count, checked** (`scripts/probes/ttm_double_count.py`, measured on m9w). Yes, it was counted twice. TTMn_L and TTMn_R each join the mid CTr-extensor Hill muscle (F0 324 µN, arm 0.027 mm), an 8-MN pool. Their activation-weight shares are 0.042 (L) and 0.055 (R), alongside STTMm, the sternotrochanter, tergotrochanter and Tr extensor MNs.
  - The hook adds the TTM again. A giant-fibre volley therefore drives both the hook and about 5% of the mid CTr extensor. The second path is small, but it is the same muscle counted twice.
  - Switch `jump:ttm|exclude_from_hill` 1 removes TTMn from the Hill pool, so the TTM acts only through the hook. Test: `tests/test_ttm_exclusion.py`. It is part of m9d, adopted after all 8 gate seeds passed (DECISIONS 18:53, result 19:13).
- **Standing** (seed 12, m9w, 1.5 s; `runs/s12/standing/standing_midhind_live_s12.png`, viewed). Thorax ends at 0.542 mm, against 0.542 mm with copied muscles. Legs carry 0.3 µN at the end, against 3.6 µN. The trunk is on the floor 97% of the time in both runs. As pre-registered, the muscles do not lift the fly, because at rest only the slow tibia flexors fire (F-STAND-3).
- **Gate** (m9m = m9n + this switch + TTM 90). All 8 seeds (12-19) pass: 0 spikes/ms in the last 100 ms, no MuJoCo warnings, no NaN, thorax 0.537-0.551 mm, whole brain 0.24-0.26 Hz. Adopted as m9m (DECISIONS 18:38, result 19:07).
- **For Ben's list.** Ask the FlyMimic authors for their mid/hind muscle models, the actual values this derivation stands in for.

### F-FTI-2: the measured maximal flexion torque sits at the femur's geometric ceiling; no data fix the flexor:extensor split
- **Question** (B, extensor:flexor). FlyMimic's front-leg tibia flexor gives 1.04 µN·mm (F0 68.1 µN × arm 0.0152 mm) and its extensor 10.1 µN·mm. Azevedo et al. 2020 measured about 100 µN at a 417 µm lever, so the flexor makes at least 42 µN·mm. Scaling the flexor ×40 and moving the force-length optimum both failed their s11 checks (F-BODY-1). Per the two-fixes rule, this item gets a write-up with new data, not a third fix.
- **New data** (agent report `docs/research/s12_tibia_flexor_extensor.md`; read unless marked):
  - The whole front femur has 97 muscle fibres (Kuan et al. 2020, X-ray holographic nano-tomography). The older fluorescence count was 33-40 (Soler 2004, secondary).
  - Leg muscle fibres are 8-16 µm in diameter (Kuan 2020).
  - No published adult split of fibres between the flexor (tidm) and the extensor (tilm) was found. Soler 2004 probably has it, but it is paywalled.
  - **No tibia extensor force has been measured.** Azevedo's authors call it unresolvable with their method.
  - The flexor motor pool (about 15 MNs) is larger than the extensor's. That is a qualitative constraint only.
- **The ceiling** (derived):
  - All 97 fibres at 8-16 µm give 0.0049-0.0195 mm² of fibre cross-section. At 34.7 mN/mm² that is 170-680 µN for every femur muscle together. The specific tension is Jarvis 2021's jump-muscle value, so its use on leg muscle is inferred.
  - The measured femur cross-section (0.0113 mm², flybody mesh) gives 392 µN at full fill.
  - To make 42 µN·mm with all of that force needs an arm of at least 0.06-0.11 mm. The femur's distal half-width is 0.059 mm (measured on the mesh).
  - So Azevedo's flexion torque is reachable only if the flexor takes nearly every femur fibre on an arm of nearly the whole joint radius, or if leg muscle has a higher specific tension than the jump muscle. FlyMimic's arm (0.0152 mm) and flexor force sit about 40× below it.
- **What is fixed and what is not.** The flexor's torque capacity is bounded, 1-42 µN·mm (inferred), and the measurement sits at the top. The extensor has no measurement, so the ratio is free within the ceiling.
- **Decision.** No new switch. The FlyMimic split stays, labelled fitted-by-FlyMimic. `muscle:leg|ft_flexor_scale` stays 1, with bounds 1-40 recorded.
- **Next discriminating data.**
  - The tidm/tilm fibre split (Soler 2004, or the Kuan 2020 XNH volumes, which are public EM-like data);
  - the flexor tendon's insertion distance from the femur-tibia joint on the XNH volume;
  - leg-muscle specific tension.
  Each would collapse one factor of the 40× range.

### F-DAMP-1: flybody's leg damping is about ten times the bound the data allow, and it was hiding the speed of the collapse
- **The bound** (inferred). Wang et al. 2025 (eLife, PMC12324252; full text searched) give no damping value. Their motor-silenced standing flies reach the passive posture about 350 ms after light-on. That interval is already taken by MN inactivation (about 30-110 ms), muscle delay (about 40 ms) and active-force decay (τ ≈ 100 ms, their model). So passive relaxation can add at most about 0.1 s: c/k ≲ 0.1 s.
- **The model.** flybody's damping is 1 µN·mm·s/rad (femur-tibia 0.4), guessed. Against the measured springs that gives c/k ≈ 1.2 s. FlyMimic uses c/k 0.05 s, a model choice.
- **Option** (`joint:leg|damping_source` 1; `passive.set_damping_from_stiffness`). Each leg joint gets c = τ × its own measured stiffness: the diagonal of J^T K J when the springs are coupled, with off-diagonal damping dropped (inferred). τ = 0.05 s (`joint:leg|damping_tau_s`; bounds 0.005-0.1 s). It is applied as MuJoCo DOF damping, so the integrator treats it implicitly; the tarsal chain is unchanged. Test: `tests/test_leg_damping.py`.
- **Dead and live fly** (seed 12, 1.5 s; numbers in DECISIONS s12 18:53).
  - The passive collapse goes from 410 ms to 50 ms for 90% of the drop. The trunk touches the floor at 20 ms instead of 50 ms.
  - The end height hardly moves: 0.544 → 0.565 mm dead, 0.542 → 0.555 mm live.
  - Wang's passive-only simulation falls at about 37 mm/s (their model, not a measurement). With option 1 this model falls about 31 mm/s over the first 20 ms (1.32 → 0.70 mm); with flybody damping, 5 mm/s.
- **Reading.** Damping sets how fast the fly falls, not whether it stands. The old slow sink (hundreds of ms) looked like a real silenced fly's slow fall, but for the wrong reason: viscous creep at a damping the data rule out, where the real fly has decaying active force. With realistic damping the missing resting drive (F-STAND-3) shows as a fast collapse.
- **Status.** Gate passed on all 8 seeds (12-19); adopted as m9d with the TTMn exclusion (DECISIONS 18:53, result 19:13). Whole-brain rate excluding ORNs rose from about 0.08 to 0.14 Hz on 7 of 8 seeds (DECISIONS 19:13). Source found in F-DAMP-2: the collapsed fly's head lies on the floor instead of on its right front tibia, and the head-bristle channel reads total head contact force. Not leg motion.

### F-DAMP-2: m9d's extra resting motion is MuJoCo's unconverged noslip pass; its brain-rate rise is the head lying on the floor; and under instant release its dead fly lands on range limits
- **Status (20:49): noslip off adopted as m9s** (DECISIONS s12 20:33 pre-registration, result 20:49). Gate silent on seeds 12-19; template dead fly keeps every verdict. Resting leg speed is step-converged on seeds 12 and 14 (12.9/12.2 and 12.8/12.6 deg/s at k = 1/2, against 17.0/24.5 and 16.6/25.8 at 3 iterations). Feet move about half as much (0.32-0.37 against 0.75-0.84 mm summed over 0.8 s). The head-floor contact and the collapsed posture are unchanged.
- **Question** (F-DAMP-1 status line). On m9d the whole-brain rate at rest rose from 0.086 to 0.143 Hz, mostly in the head bristles (summed BM_InOm 3725 → 8381 Hz). The first guess was that they reported more leg motion. Is that motion physical or numerical?
- **Probe** (`scripts/probes/resting_joint_speed.py`). It runs the gate's closed loop (or the body alone) for 1 s and reports the RMS speed of the leg hinges after 200 ms. `--substeps k` divides the physics step by k and holds the muscle torques over the extra steps. The brain, muscles and sensing stay at 0.1 ms. A physical result does not change with k; a numerical one does.
- **Results, closed loop, RMS leg speed (deg/s; peak in brackets):**

  | profile, noslip iterations | k = 1 (0.1 ms) | k = 2 | k = 4 | k = 8 |
  |---|---|---|---|---|
  | m9m, 3 (flybody) | 14.9 (540) | 15.0 (536) | 16.9 (884) | |
  | m9d, 3, seeds 12/13/14 | 17.0 / 16.8 / 16.6 | 24.5 / 24.3 / 25.8 | 9.5 / 5.7 / 9.4 | 7.5 (seed 13) |
  | m9d, 0, seed 13 | 13.6 (142) | 12.0 (142) | 12.3 (131) | |
  | m9d, 20, seed 13 | 15.6 (724) | 14.5 (440) | | |
  | m9m, 0, seed 13 | 17.2 (759) | 17.5 (792) | | |

  - With flybody's 3 noslip iterations, m9d's resting motion changes non-monotonically with the step, by up to 4×, with peaks up to 1800 deg/s. The three seeds agree closely at each step, so this is not chaotic divergence; it is set by the step.
  - With noslip off, the same loop converges: 12-13.6 deg/s, peaks about 140 deg/s.
  - With 20 iterations it is nearly converged (15.6 against 14.5, a 7% step change).
  - m9m with noslip off moves more than m9d (17.2-17.5 against 12-13.6 deg/s), with peaks near 780 deg/s; why is not checked (m9m keeps flybody's damping and the TTMn in the Hill pool).
  - The body alone (no spikes, noslip 3) is quiet on both: m9m 13.2, m9d 3.3-3.6 deg/s.
- **Reading.** MuJoCo's noslip pass (a per-step projection that removes contact slip, run for a fixed 3 iterations) is not converged at this step when the legs are lightly damped. Its leftover depends on the step. The extra motion under 3 iterations is therefore numerical. With the solver converged (noslip off), m9d's legs move less than m9m's, yet m9d's brain still spikes more (41.5-43k against 33.4k spikes after 200 ms, seed 13). So the rate rise does not come from leg motion. F-DAMP-1's explanation ("lower damping lets the resting body move more and the bristles report it") is withdrawn.
- **What the head bristles read** (same probe, now also logging head contact; seed 13, closed loop, `runs/s12/head/*.json` on backhouse). The head-touch channel (extrasenses) drives every head bristle, taste-peg and pharyngeal mechanosensor with gain × tanh(total normal contact force on the head, antennae, rostrum, haustellum and labra):

  | profile, noslip | head in contact | mean head force (µN) | main contact partner (share of samples) | spikes after 200 ms |
  |---|---|---|---|---|
  | m9m, 3 | 84% | 1.20 | right front tibia 81%, floor 35% | 34.4k |
  | m9m, 0 | 83% | 1.14 | right front tibia 78%, floor 27% | 33.4k |
  | m9d, 3 | 92% | 2.37 | floor 92%, right front tibia 9% | 41.4k |
  | m9d, 0 | 94% | 2.44 | floor 94% | 41.5k |

  - The rate rise is the head resting on the floor. In m9m the collapsed fly's head mostly lies on its own right front tibia; in m9d it lies on the floor with twice the force. The noslip setting does not change this.
  - A standing fly's head does not touch the floor. Both profiles therefore carry head-bristle drive that exists only because the fly is not standing (F-STAND-3). The resting whole-brain rate is not a clean baseline until it stands.
  - The channel is coarse: interommatidial bristles fire for contact anywhere on the head region, including the mouthparts. A per-region map would need the bristle field (B18, absent).
- **Dead fly under m9d's damping** (`scripts/dead_fly.py --template`, 1 s instant release; `runs/s12/deadfly_template_*`):

  | body | end height | range limits | posture order |
  |---|---|---|---|
  | template (flybody damping) | 0.549 mm | pass | pass |
  | + damping from stiffness (m9d's body) | 0.566 | **fail**: lf, rf, lm coxa roll on the assumed ±25° limit 78-95% of the time | pass |
  | + damping + flybody coxa ranges and refit | 0.588 | **fail**: 7 coxa joints | **fail** |
  | + CTr ranges and refit (flybody damping) | 0.606 | **fail**: lf, lm CTr on the fold bound 50-59% | pass |
  | + CTr + damping | 0.635 | **fail**: 6 joints | **fail** |

  - With realistic damping the instant-release fall is fast (peak kinetic energy 1.2-2.9 against 0.05). The legs are thrown against their limits and friction holds them there. The springs alone no longer set where the fly comes to rest.
  - The CTr failure is built in: the refit puts the front and middle CTr references on the fold (F-COXA-2).
  - The m9d adoption test (DECISIONS 18:53) did not include the dead-fly test. This failure is new information, not a regression the gate missed. The battery's dead-fly test uses flybody damping.
- **Reading.** Instant release is not Wang et al.'s protocol. Their silenced flies start standing, and lose active force over about 100 ms (their model; MN inactivation measured). With flybody's damping the two protocols looked alike, because viscous creep slowed the fall. With damping from the measured stiffness they do not.
- **Wang's protocol as a probe** (`scripts/probes/deadfly_decay.py`; criteria unchanged). The placed fly first gets the joint torques that hold it there (read off stiff instrument springs, as `stand_budget.py`; 32.2 µN·mm summed). Those torques then decay as exp(−t/100 ms). τ is Wang's model value (inferred). The hold torque is not a model quantity: it stands in for the active force the model lacks (F-STAND-3).

  | body | range limits | posture order | 90% of drop |
  |---|---|---|---|
  | template (flybody damping) | pass | pass | 458 ms (collapse criterion fails: onset 52 ms) |
  | + damping from stiffness (m9d's body) | **fail**: lf, rf coxa roll on the assumed limit 87-90% of the time | pass | 98 ms |

  - The slower protocol restores the posture order under m9d's damping, but the front coxa roll still ends on the assumed ±25° joints.py limit (F-COXA-1: assumed envelope, mislabelled axes). So with realistic damping the dead fly's rest pose depends on the path of the fall and on an assumed limit, not on the springs alone.
  - **Held-out caution.** This run reads the fall time course, which DECISIONS 18:23 reserves as the held-out check for standing option (b). To keep it usable, no switch is chosen on it. The damping choice stays on its own evidence (F-DAMP-1), and the comparison with Wang's measured fall is left for option (b). Register updated: seen in an s12 diagnostic, not used for selection.

### F-FLIGHT-3: the fitted wing reproduces hover lift at one condition; against the robotic fly its lift is 1.7× too high and its drag has the wrong shape
- **Test** (B, flight coefficients beyond one condition). `scripts/probes/wing_coefficients.py` holds the fly still with gravity off and blows a uniform wind (1000 mm/s) over the left wing membrane at angles of attack 0-90°. It reads the fluid force on the wing alone, after subtracting the drag on the rest of the body in the same wind. It then compares the result with the translational coefficients of the dynamically scaled robotic Drosophila wing (Dickinson, Lehmann & Sane 1999, Science 284:1954, Re ≈ 136; measured): CL = 0.225 + 1.58 sin(2.13α − 7.2°), CD = 1.92 − 1.55 cos(2.04α − 9.82°). Area is the membrane planform, π × 0.589 × 1.401 mm = 2.59 mm². Plot: `docs/media/s12_wing_coefficients.png`, viewed.
- **Lift.** The model gives exactly CL = C_K sin 2α. At the adopted Kutta coefficient 3.1 (inferred: fitted so hover lift = weight, F-FLIGHT-2), CL peaks at 3.1 at 45°, against the robofly's 1.81. That is 1.72× at every angle. At MuJoCo's default of 1 it is 0.55×.
- **Drag.** CD is 0.5 at α = 0 and then exactly 1.0 from α ≈ 2° to 90°. The robofly gives 0.39 at low angles, 1.70 at 45° and 3.46 at 90°. Split by coefficient:
  - The slender term (0.25) gives the 0.5 at α = 0.
  - The blunt term (0.5) gives 2 × 0.5 = 1.0 at any angle above about 1°. MuJoCo's projected area, π·sqrt(Σ(d_j d_k)⁴v_i² / Σ(d_j d_k)²v_i²), saturates for a plate this thin: by hand at 1° it is 98.5% of the planform, matching the probe's 0.985.
  - So the model wing has 2.5× the robofly drag at 5-20° and 0.29× at 90°.
- **Rest of the body.** MuJoCo also applies its inertia-box drag to every body that has no ellipsoid geom. In this wind the rest of the fly takes a force coefficient of 2.7-3.3, on the wing's reference area, which the probe subtracts. In flight the legs, head and thorax therefore carry inertia-box drag. Nothing here checks that drag against data.
- **Reading.** F-FLIGHT-2 made hover lift match weight at one condition by inflating translational lift. That one number stands in for delayed stall, rotational lift and wake capture. The shape is wrong in ways the hover average hides:
  - lift-to-drag at 45° is 3.1, against the robofly's 1.06, so aerodynamic power and the drag-based yaw torques are too low by about 3×;
  - any condition with a different angle of attack (steering, forward flight, a changed stroke) gets the wrong force.
- **Option, behind a switch** (`aero:wing|model` 1; `flight.BladeElementWing`; read only with `membrane_only` 1). A blade-element quasi-steady wing:
  - 20 spanwise strips of the membrane ellipse, with velocities taken on the pitch axis;
  - the robofly's translational coefficients (measured), with α folded to 0-90°;
  - rotational force C_rot ρ|w| α̇ c² dr with C_rot = π(0.75 − x̂₀) (Sane & Dickinson 2002). x̂₀ = 0.20 is the pitch axis' chord position at mid-span on the model wing (derived), giving C_rot 1.74;
  - α̇ is the pitch-joint rate. The conical stroke (span 40° out of the stroke plane) spins the wing about its span by about 1000 rad/s without changing α. A first version used the total spin and gave a spurious −0.59 W.
  - MuJoCo's drag, lift and angular drag on the membrane are off, and its added-mass terms stay.
  - Not modelled: acceleration added mass, wake capture, pitching moment, flexion.
  - Tests: `tests/test_flight.py` (steady wind equals the robofly to 1e-6; the rotational term follows the pitch joint only).
- **Bugs found on the way.** `mj_objectVelocity` with a body ID returns the centre-of-mass velocity, not the frame origin's, which gave 2.6 W. The strip width was shared between wings (a 1e-5 area error). Both are fixed and covered by the tests.
- **Hover, no fitted number** (`scripts/probes/tethered_lift.py --blade`, `scripts/probes/hover_blade_trace.py`; 218 Hz, 140°, rotation −57 ± 55°; `docs/media/s12_hover_blade_trace.png`, viewed):

  | aero | imposed kinematics | PD-tracked |
  |---|---|---|
  | ellipsoid, Kutta 3.1 (fitted) | 0.99 W | 0.89 W (s10) |
  | blade element | 0.72 W (translational lift 0.81, rotational −0.10, drag 0.01) | 0.55 W, tracking p95 9.4° |

  - The guessed kinematics give a mid-stroke α at 70% span of 29° on the upstroke and 47° on the downstroke. The rotation mean is guessed, and this asymmetry costs lift.
  - The PD thorax tracks worse because the wing now carries robofly drag at high α, about 3.5× MuJoCo's.
  - The hook costs 52 µs per step, about 5% of a body step.
- **Reading.** With measured force coefficients and no fitted number, the guessed hover kinematics lift 0.72 of the weight. The fitted Kutta number was hiding errors in the kinematics as well as in the aerodynamics. The next test that can tell them apart: impose measured Drosophila hover kinematics (stroke, deviation and rotation over the beat, stroke-plane angle) and compare lift with weight. A source search is running (`runs/s12/flight/kinematics_lit.md`). The model wing is also larger than a typical female wing (2.59 mm² planform, 2.8 mm span ellipse), which is not checked against data yet.

- **Pre-registered test with measured kinematics (19:35; DECISIONS s12 19:08): FAIL, high.** Muijres et al. 2014 steady-flight kinematics (D. hydei, Table S1; measured) were imposed at 218 Hz with the thorax at 47.6° pitch (`scripts/probes/build_measured_kinematics.py`, `hover_blade_trace.py --table`; pose-fit error 0.0°). Plot: `docs/media/s12_hover_blade_trace_measured.png`, viewed.
  - Mean vertical force is 1.53 W: translational lift 1.35, drag 0.07, rotational 0.11. The pass band was 0.8-1.2 W.
  - α at 70% span is 44° at mid-downstroke and 34° at mid-upstroke.
- **A bug found by this test, fixed before the verdict.** The first run gave 0.29 W, with a rotational term of −1.14 W. The hook used the pitch-joint rate as α̇. That is right only if the other two hinges sweep the stroke frame, and in this model they do not (F-WING-3).
  - Fix: α̇ is now the wing's spin about its span relative to the stroke frame (span and stroke-plane normal): ω·ŝ minus the frame's own spin (derived; `flight.stroke_frame_spin`).
  - On the measured beat it equals the measured dα/dt at every phase. For example, at τ 0.2 it is 37 rad/s, where the pitch joint gives 2002 and the measured value is 37.
  - Tests: a cone about the stroke normal gives zero; the spin equals the stroke-frame rotation rate; rotation that raises α adds force on the lift side.
  - The old rate is kept as `rot_rate="pitch_joint"` to reproduce the 0.29.
  - This is a correctness fix (the code did not compute its own documented quantity). No coefficient changed. Both numbers are reported.
- **Mechanism of the excess (derived estimate, not a run).** At fixed kinematics, force scales roughly as R⁴. The model wing reaches 2.65 mm from hinge to tip, against 2.39 ± 0.08 mm measured in melanogaster free flight (Fry et al. 2005). (2.39/2.65)⁴ = 0.66, which takes 1.53 to 1.01. The model's planform (2.59 mm², ellipse span 2.80 mm) is also larger than typical melanogaster values. Other terms are smaller:
  - hydei amplitude 131.6° against melanogaster 140° (+13% if melanogaster's were used);
  - missing wake capture and acceleration added mass;
  - the stroke-plane and α conventions are inferred.
- **Reading.** With measured kinematics and no fitted number, the blade-element wing gives the right order of force. The remaining 53% excess is most plausibly the model's wing size. Per the pre-registration, the fail is recorded, nothing is refitted, and option 1 does not become the default.
  - All guessed-kinematics numbers above (0.72 W, 0.55 W, the Kutta fit) used a generator that crosses the wings (F-WING-3), and are superseded.
- **Pre-registered size check (20:04; DECISIONS s12 19:58): PASS.** The blade-element strips were scaled about the hinge to the measured female wing length, 2.47 mm (Lehmann & Dickinson 1997, n = 27, the same cohort weighed 1.05 mg). This is `aero:wing|size_source` 1; mesh, inertia and added mass are unchanged.
  - Same test as 19:35: 1.153 W (translational lift 1.016, drag 0.056, rotational 0.082), against a predicted 1.15 W and a band of 0.8-1.2 W.
  - Fry's 2.39 mm gives 1.011 W.
  - Reading: the 53% excess was the scanned wing's length relative to the measured population mass. With measured kinematics, measured coefficients, measured mass and a measured wing length, hover force is within 15% of weight and nothing is fitted.
  - Validity: one condition (hover, hydei kinematics on a melanogaster-sized wing), and the length was chosen after seeing the fail. It is a consistency check, not held-out validation.
  - Still open: the mesh and inertia are the scan's, so wing inertial power and the passive pitch response are for the larger wing.
  - Discriminating test: measure the flybody wing against the body it came from (wing length / thorax length against female melanogaster morphometrics). If the wing is oversized, scale the membrane to measured length and area, behind a switch, and rerun this same test unchanged.

- **Second condition: 13 measured force levels against the robotic fly (20:36; DECISIONS s12 20:31 pre-registration and result).**
  - Data: Muijres et al. 2014 Database S1, `robotForcesTorques.ForceModulations` (open): 13 beats built from the measured kinematic change per unit force (F/mg 0.85-1.76, 182-220 Hz; D. hydei), and the force a dynamically scaled robotic wing measured with each (measured). The robot's steady beat is Table S1 with stroke and rotation negated; that map is applied to all levels (`build_measured_kinematics.py --robot-level`).
  - Model: blade-element wing, no coefficient changed, scaled to the database's wing (R 2.99 mm, planform R × c̄ = 2.83 mm², flybody ellipse shape kept; `aero:wing|size_source`-style strip scaling plus `area_mm2`), normalized by 1.8 mg.

  | F/mg (flies) | 0.85 | 1.00 | 1.15 | 1.30 | 1.45 | 1.60 | 1.76 |
  |---|---|---|---|---|---|---|---|
  | robot, ratio to steady | 0.91 | 1 | 1.14 | 1.30 | 1.48 | 1.71 | 1.99 |
  | model, ratio to steady | 0.88 | 1 | 1.13 | 1.29 | 1.45 | 1.62 | 1.82 |

  - Pre-registered rule (ratios within 0.10 at every level): fails at the top two levels (−0.11, −0.17). Steady level 0.865 W, 0.85 of the robot's 1.02 (secondary, pass).
  - Split (`docs/media/s12_robot_force_levels.png`, viewed): the angle changes alone agree with the robot to about 1% (1.34 against 1.33 at the top). The gap is the frequency term. The model scales as f² exactly; the robot's frequency-only record rises 1.50× for a change that gives 1.36× under f². How the robot runs were scaled in frequency is not stated in the SM. Unresolved.
  - The free-flying flies' own F/mg rises more slowly than the robot's (1.76 against 1.99 at the top). The model sits between, close to the flies (1.82).
  - Reading: with measured coefficients and no fitted number, the wing's response to measured kinematic changes is right within about 3% up to 1.45 W. Its absolute force at the steady hydei beat is 15% below the robot's. That fits the known shortfall of a quasi-steady model without wake capture or added-mass acceleration terms. The planform shape is flybody's ellipse, not the hydei wing; the database holds the hydei chord distribution (`wing_model.chords_L`, 20 sections), which would remove that difference. Not done.
  - Next discriminating test: the robot's roll and pitch modulation sets (same database) give left-right and fore-aft force and torque at fixed frequency, so they test the wing without the frequency question.
- **Third condition: roll torque at 13 measured roll conditions (20:49; DECISIONS s12 20:43 pre-registration and result). FAIL.**
  - Data: Database S1 `RollModulations` (open): per-side kinematics built from the flies' measured kinematic change per unit roll acceleration (−0.72 to 3.61 deg per beat², steady frequency), and the robot's forces and torques for all changes and for each angle alone (measured). The torque normalization m g l is sourced in Dickinson & Muijres 2016 (PMC4992712, Fig. 2 caption).
  - Model: the same wing and scaling as the force test. Torque about the hinge midpoint, robot frame (`hover_blade_trace.py` now reports it).
  - Result: the model's roll torque is 0.42-0.52 of the robot's (force-corrected; 0.36-0.47 uncorrected) at levels 6-12, against a ±20% rule. The sign is opposite at every level. Yaw torque also flips sign, while side and vertical forces agree, so the robot's torque sign convention is probably the reverse of the force frame; unresolved, and not counted against the wing.
  - The summed lift is right: vertical force over steady 1.232 against 1.260 at the top, and the stroke-only rise 1.224 against 1.242. The deficit is in the left-right difference: stroke-only torque 0.59 of the robot's, rotation-only 0.44, deviation-only 1.01. The model's parts are strongly non-additive (sum 1.44 of the all-changes torque, robot 0.89).
  - A hand estimate from the stroke-amplitude difference alone gives about the model's value (0.026 against 0.023 m g l). The robot's is 1.7× larger. The model's narrower hinge spacing (0.43 against 0.71 mm off the midline) accounts for about 11%.
  - Reading: a quasi-steady wing with measured coefficients gets lift and its symmetric modulation right, but gives about half the measured roll torque for measured asymmetric kinematics. The leading candidate is unsteady terms it lacks (wake capture, added mass), mainly through the rotation component. Plot `docs/media/s12_robot_roll_torque.png` (viewed).
  - Consequence: steering torques from this wing would need about twice the measured kinematic asymmetry. For flight control the wing needs either an unsteady term with measured support or a torque check against a second robot dataset. No coefficient was changed.
  - Next discriminating test: a wake-capture or added-mass term from the literature, behind a switch, scored on this same pre-registered roll set (now not held out) and on the untouched pitch set (21 levels) as the held-out check.
- **Fourth check: the measured hydei planform (21:21; DECISIONS s12 21:17 pre-registration and result).** Muijres 2014 Database S1 `wing_model.chords_L` gives the robot wing's measured chord in 20 strips (`data/derived/muijres2014_wing_chords.csv`; r2/L 0.584, r3/L 0.622 against the ellipse's 0.539, 0.587). Used in place of the ellipse at the same length and area (`hover_blade_trace.py --planform hydei`):
  - Steady force 1.011 W, 0.99 of the robot's (ellipse 0.85). The 15% deficit was the planform.
  - Force ratios and roll are unchanged within 1-3%: still failing at levels 11-12 (frequency term), roll still 0.42-0.54 of the robot's with the sign opposite.
  - The spanwise shape is ruled out as the cause of the roll gap. Robot comparisons use the hydei planform from now on; the organism keeps the scanned wing.
- **Diagnostic after the result (21:40): the torque reference point.** The model's torques are about the hinge midpoint. Database S1 `body_model` puts the hinges 0.636 mm forward of and 0.465 mm above the centre of mass in the body frame, which is 0.087 mm forward and 0.783 mm above in the robot frame (`R_strk`).
  - If the robot's torques are about the centre of mass, the model's become Mx + 0.262 Fy (normalized). The model's side force agrees with the robot's in sign and size (−0.031 against −0.029 at the top level).
  - The force-corrected ratio then rises from 0.42-0.57 to 0.50-0.67 at levels 3-12. It still fails ±20%, and the side-force term has the model's sign, not the robot's.
  - So the reference point accounts for part of the magnitude gap at most. The sign stays unexplained, and the robot's main text (paywalled) would settle both.
- **Fifth check: flat-plate added mass (22:15; DECISIONS s12 22:08 pre-registration and result).** `aero:wing|added_mass` 1 adds −ρπc²/4 dr dv_n/dt per strip, at mid-chord, along the normal (Sane & Dickinson 2001; derived, no fitted constant). It matches an independent stroke-frame calculation (correlation 0.97-0.995, RMS 0.91-0.94; `scripts/probes/added_mass_check.py`).
  - Roll: 0.464-0.554 of the robot's, against 0.425-0.534 without it. Still FAIL. This is the second fix to fail on roll, so no third is tried.
  - **Held-out pitch set** (21 levels of Database S1 `PitchModulations`; first look, both arms): force-corrected ΔMy about the CoM is 0.61-0.70 of the robot's, with and without added mass, and the sign is the same at all 13 scored levels. FAIL ±20%. About the hinge midpoint: 0.71-0.81 without, 0.67-0.76 with. Plot `docs/media/s12_robot_pitch_torque.png`, viewed.
  - Steady force is 1.11 of the robot's. The force-level response now departs at levels 9-12 instead of 11-12, because the added-mass mean (+0.12 W at steady, +0.09 W at the top) does not grow with the level.
  - That mean is non-zero because the strip form keeps only the normal component. The full inviscid impulse, −d(m_a v_n n)/dt, has zero mean over a beat. The in-plane remainder corresponds to leading-edge suction, which separated flow loses. The literature's quasi-steady models use the normal-only form (derived; kept, labelled).
  - Adopted for robot comparisons and flight under the registered rule. No walking profile uses it.
- **Diagnostic (22:18): within-beat comparison with the robot's time-resolved record.** Database S1 also stores each robot beat's force and torque over time (1145 samples, filtered and unfiltered). `hover_blade_trace.py` now saves the model's per-step series (`*_series.npz`). Compared at pitch levels 0, 10 and 20 and roll levels 2 and 12 by `scripts/probes/robot_torque_reference.py`; plot `docs/media/s12_robot_torque_series.png`, viewed.
  - **The opposite roll and yaw sign is a left-right labelling convention in Database S1, not physics (derived).**
    - At roll level 12, the robot's Fy, Mx and Mz anticorrelate with the model's (r −0.90, −0.74, −0.89; filtered). Its Fx, Fz and My correlate (0.96, 0.96, 0.82). Only a left-right reflection flips exactly Fy, Mx and Mz.
    - Each single-angle part (stroke, rotation, deviation) is mirrored in Mx.
    - At positive roll acceleration the database's `R` wing has the larger stroke (150.0° against 145.8°). More stroke on the right wing raises the right side, which is negative Mx in the robot's x-forward, z-down frame if `R` is the fly's right. The robot reports positive Mx. So its labels or its y axis are mirrored relative to that reading, and the model's sign is the physically consistent one.
    - Robot comparisons should mirror Fy, Mx and Mz (or swap the sides). The magnitudes above are unaffected.
  - **The magnitude gap is not the reference point.** Fitting the robot's Mx(t) as ±(model Mx) plus d × F_robot gives a lateral offset dy ≈ 0 at the steady roll level and −0.032 l at level 12. No single point satisfies both. For pitch, the best reference point explains under 40% of the within-beat variance (r² −0.26 to 0.39).
  - **Where the model departs.**
    - Within the beat, Fz agrees in shape and size: r 0.94-0.98, RMS 0.90-1.11 of the robot's.
    - Fx agrees in shape (r 0.93-0.98) but its size is 0.68-0.72 of the robot's at all five conditions, filtered or unfiltered. The model's force along the stroke direction is about 30% low, and the steady force hides this.
    - The model also has sharp Fz dips at both stroke reversals (phase 0.15 and 0.7) that the robot does not show. Its My peaks at 1.5 near phase 0.7, against the robot's 0.3.
    - Both features sit where the rotational and added-mass terms act.
  - **Next discriminating step.** The robofly drag and rotational coefficients (Dickinson 1999, melanogaster wing, Re ≈ 136) applied to the hydei robot wing: is the Fx shortfall the drag coefficient? Split the model's Fx by term and check which term would have to change. Any change must come from a measured coefficient set for this wing, not a fit to Fx.
  - **Fx split by term (22:20; pitch level 10 and roll level 12; per-term series in `*_series.npz`).**
    - The drag term carries Fx: its Fx correlates 0.93-0.97 with the robot's, against 0.10-0.16 for lift, 0.44-0.48 for rotational and about 0 for added mass.
    - A least-squares weighting of the four terms that would reproduce the robot's Fx gives drag 1.47-1.48 at both conditions, with lift 0.82-0.90, rotational 0.96-1.03 and added mass 1.1-2.0, the last poorly constrained. This is a diagnostic; nothing is changed.
    - Reading: the robofly drag coefficient (Dickinson 1999; melanogaster wing, Re ≈ 136) is about 2/3 of what the hydei robot wing gives. Drag adds little to the mean vertical force (−0.05 to −0.09 W), so the steady-force pass does not test it.
    - Database S1 holds geometry and scaling only (stroke-plane angle −47.5°, Lwing 2.99 mm, cwing 0.95 mm, AR 3.16), and no coefficient set. A source search for measured coefficients on this wing is running.
- **Free-flight record, for the next held-out test (22:23; conventions only, no outcome looked at).** Database S1 `wing_data` and `body_data` hold 92 free-flight looming-escape sequences at 7500 fps: per-side stroke, deviation and pitch (rad), body position, velocity, acceleration, quaternion and angular velocity, and each fly's wing length (2.7-3.1 mm). There are 153,101 tracked frames, 403-4321 per sequence.
  - The robot's steady beat is the mean of the free-flight pre-trigger beats. 3354 beats were cut stroke maximum to stroke maximum, giving r = 1.000 and an RMS difference of 0.3-0.5° on each angle, with no phase shift.
  - The angle map is robot stroke = −free stroke, robot rotation = 90° − free pitch, deviation unchanged. In this project's convention that is (free stroke, deviation, free pitch − 90°) (derived).
  - Sides are labelled as in the robot set, so they carry the same left-right mirror question.
  - Frames (derived from the record itself):
    - `qbody` is scalar-last and rotates body to world, with world z up. The body axes are x forward, y right and z down. Before the trigger, body x sits 47.3° nose-up (IQR 44.4-50.2°), body y is level (−0.4°) and body z is −41.7°.
    - `vel` is the time derivative of `pos` (ratio 1.005-1.007), both in m.
    - `accel` excludes gravity: its pre-trigger mean is under 0.06 m/s² on each axis.
    - `omega` is in the body frame (inferred): it tracks finite-differenced body-frame rates (r 0.77-0.85) better than world-frame rates (r 0.41-0.56).
- **Source search for a measured drag coefficient on the hydei robot wing (22:26): none found in open sources.**
  - The Science 2014 supplementary text cites Dickinson, Lehmann & Sane 1999 for coefficients and gives none of its own.
  - Its robot reference is Dickson, Polidoro, Tanner & Dickinson 2010 (JEB 213:3047, yaw dynamics of a scaled insect model). That paper is the most likely place for the robot wing's own coefficients but was not reached.
  - Dickson & Dickinson 2004 (advance ratio) and Lentink & Dickinson 2009 (revolving wings) use melanogaster wings and give no α table for this wing. The Melis 2024 robofly code has analysis only. Kamimizu 2025 is fitted to CFD, not measured.
  - So the 1999 set stays. The 0.70 drag-direction shortfall stays open.
- **Held-out yaw test, Dickson et al. 2010 robot (s12, 5 Oct 02:52; DECISIONS 02:45).** The blade-element wing, with chords rescaled to the robot's c̄/R, on its baseline kinematics. Yaw damping C*_ω is −856 against the robot's −640: right sign, linear, 1.34× too strong, so it fails ±20%. Added mass changes nothing. Actuation magnitudes: pa 1.13 and pd 0.93 pass; pr 1.35 and pv 0.46 fail. The signs of pa, pd and pr are opposite to the robot's, under conventions the probe does not establish. The prediction (0.6-0.8) was wrong in direction.
  - Split by term (03:21; DECISIONS 03:15): translational drag carries all of the damping (−858 of −856); rotational +1.9, added mass −0.1, lift 0, as a symmetry argument predicted (lift stays vertical; the rotational change is odd about mid-stroke). The rotational coefficient is cleared. At the robot's larger hinge offset the model's excess would be about 1.5× (strip-theory estimate, derived). Since the model's stroke-direction force is 0.70 of the hydei robot's, the two robot tests pull the drag in opposite directions; a measured drag polar at Re about 100 run through both is the next test.

### F-WING-3: the s10 wingbeat generator and wing ranges swing each wing over the back to the other side
- **Test.** `flight.wing_span_sign` gives the membrane's hinge-to-tip direction. The left wing alone was posed at the generator's mid-downstroke and viewed from above: `docs/media/s12_wing3_crossed_stroke.png`, viewed.
- **Result.** At generator pose (stroke 86°, deviation 40°, rotation −12°) the left wing's centre is at y = −0.82 mm, on the right side of the fly (the hinge is at +0.43).
  - The model's stroke (yaw) hinge axis is (0, 0.74, 0.68) in the thorax frame, which lies in the transverse plane. A stroke plane needs a normal in the sagittal plane, measured at (0.74, 0, 0.68) for a 47.5° tilt.
  - Positive yaw therefore swings the folded wing up over the dorsum.
  - `WING_RANGE_DEG` (yaw −10..175°) was sized around this crossed stroke.
  - The measured hover beat needs yaw −121..37°, roll −62..4° and pitch −60..121° (exact fit with open ranges).
- **Consequences.** Every s10-s12 generator-driven flight number used crossed wings: the Kutta fit (F-FLIGHT-2), the 0.72/0.55 W blade-element hover, and the PD tracking figures. The rotational-rate proxy in F-FLIGHT-3 also failed because of these axes. Walking profiles are unaffected: the generator is off, and the folded rest pose (F-WING-2) is not part of the stroke.
- **Fix, built behind switches (19:44; no profile sets them).**
  - `flight:wings|kinematics` 1 (`flight.StrokeFrameKinematics`) reads the measured beat in stroke-frame angles from `data/derived/muijres2014_hover_kinematics.csv` and fits hinge angles by `wing_pose_ik` at each phase. The build takes 2 s, the fit error is 0.0°, and it matches the npz table exactly.
  - B11 steering acts on the stroke-frame angles through the pose Jacobian. Amplitude +10° gives +20.2° peak-to-peak, and mean +5° gives +5.0°. That is linear to 1%.
  - `joint:wing|range_by_function` 2 (`WING_RANGE_MEASURED_DEG`) is the measured hinge envelope plus the folded pose, with a 20° margin (guessed).
  - Test (`test_measured_beat_keeps_each_wing_on_its_side_and_steers`): PD-tracked through `motor_step`, the stroke is 131.6 ± 10° peak-to-peak. Each wing stays on its own side throughout, there are no MuJoCo warnings, and a left b2 burst widens only the left stroke.
  - Contact sheet `docs/media/s12_wing_beat_views.png`, viewed: generator against measured beat, top and front views, thorax level. The measured beat reverses above and behind the hinge at τ 0 and in front and below at τ 0.5. The chord stands near vertical on the upstroke when the thorax is level, as expected for a 47.5° stroke plane.
  - The s10 generator stays as switch value 0 (legacy fixture). `test_s10_generator_crosses_the_wings_and_measured_poses_do_not` pins its crossing.

### F-NONLEG-1: a shared 10 µN·mm per spike pinned the head, rostrum and antennae at their stops; a per-part derivation frees them, and the wings then rise over the back
- **Census** (`scripts/probes/nonleg_motor_census.py`, m9s gate values, seed 12, 200-600 ms; `runs/s12/nonleg/census_s12.json`). Every non-leg motor neuron used the shared `motor_unit:all|force_per_spike` 10 µN·mm (guessed). Against flybody's non-leg springs (head, antenna, proboscis 3 µN·mm/rad, abdomen 5, wing 1, haltere 400; all unsourced), a few Hz of resting drive held the head yaw, head pitch, rostrum and both antennae within 1° of a joint limit 97-100% of the time. On the contact sheet the head was pitched down onto the floor.
- **No measurement.** The literature search (`docs/research/s12_nonleg_muscle_sources.md`) found no measured force, cross-section or moment arm for any fly neck, proboscis, antennal, abdominal or wing-steering muscle in open sources. The candidates are paywalled: Strausfeld 1987, Rajashekhar & Singh 1994, Tu & Dickinson 1994/96, Zanker 1988, Chan 1998.
- **Derivation** (inferred; `scripts/build_nonleg_forces.py` → `data/params/nonleg_motor_forces.csv`; switch `motor_unit:nonleg|torque_source` 1).
  - Torque per spike = force per motor unit × lever.
  - Force: 1.035 µN, the mean per unit of the tibia-flexor pool (Azevedo 2020's measured classes, 10/1/0.05 µN × 1/3/9 units; derived).
  - Lever: the length of the moved part on the flybody mesh, joint to far end (`scripts/probes/nonleg_joint_geometry.py`; derived).
  - Bounds are the measured unit range, 0.05-10 µN, times the same lever.
  - Interpretation: one average leg-sized motor unit acting at the far end of the part it moves.
  - Validity: resting posture and slow movements. The real insertion is nearer the joint, so the lever overstates the torque. The wing is the worst case, because its steering muscles act on the hinge sclerites, not the blade.

  | part | lever (mm) | torque per spike (µN·mm) | upper bound |
  |---|---|---|---|
  | head | 0.476 | 0.49 | 4.8 |
  | rostrum, haustellum, labrum | 0.385, 0.246, 0.20 | 0.40, 0.25, 0.21 | 3.9, 2.5, 2.0 |
  | antenna | 0.42 | 0.44 | 4.2 |
  | abdomen 1-7 | 0.42-0.75 | 0.43-0.77 | 4.2-7.5 |
  | wing | 2.64 | 2.73 | 26 |
  | haltere | 0.30 | 0.31 | 3.0 |

  The old 10 lies above the upper bound for the head, proboscis, antennae and halteres.
- **Result** (DECISIONS s12 21:12, result 21:21).
  - Gate silent on seeds 12-19.
  - Time within 1° of a limit is now 0 for every head, proboscis and antenna joint.
  - Mean angles: head yaw −0.4°, head pitch 0.3°, rostrum −12°, antennae 5-6°.
  - On the sheet the head is upright and the proboscis is off its stop.
  - Adopted as m9t.
- **The wings now rise.** Both wings rise in a V over the thorax at 300 ms, and the left at 600 ms.
  - The wing motor neurons fire about twice as often at rest as on m9s (left yaw 2.5 → 5 Hz, left pitch 7.5 → 15 Hz; the right side now fires too).
  - The first-axillary neurons (i1, i2) map to wing yaw with sign +1 (guessed, `data/params/motor_targets.csv`).
  - In flybody's hinge, positive yaw lifts the folded wing over the dorsum (F-WING-3).
  - So any resting first-axillary drive raises the wing against a 1 µN·mm/rad spring. Steady state: 2.73 µN·mm × 5 Hz × 30 ms ÷ 1 µN·mm/rad = 0.41 rad, about 23°, against the measured mean left yaw of 20.3°.
  - Three unsourced quantities meet here: the wing lever, the wing spring, and the yaw mapping. They are not changed after this result; the wing rest needs its own pre-registration.
- **Still copied or guessed in this path** (recorded, not changed):
  - Neck and antenna drive signs: +1 on both sides with no antagonists. ADNM2 (TH2) turns the head the same way from either side, which is anatomically wrong for a bilateral pair. Gorko et al. 2024 may give per-neuron directions.
  - The actuator clip of ±30 µN·mm is a NeuroMechFly copy (`body.NMF_FORCERANGE`). It also applies to the Hill leg torques. On m9t it never binds:
    - At rest (census, seeds 12 and 13, `runs/s12/nonleg/census_m9t_s1{2,3}.json`), the peak leg torque is 0.32 µN·mm and the time at the limit is 0.
    - At full activation, the largest single-muscle torque F0 × arm is 19.3 µN·mm (hind trochanter-femur). Each coxa hinge sums to at most 10.9 µN·mm across its anatomical muscles. So no leg actuator can reach 30.
    - It would bind if the femur-tibia flexor took its measured strength. The model's flexor gives 1.04 µN·mm against at least 42 µN·mm measured (F-FTI-2; `muscle:leg|ft_flexor_scale` is off). So the clip has to be sourced or lifted before that flexor is.
  - The non-leg springs listed above.

### F-WING-4: with flybody's 1 µN·mm/rad hinge spring a steering spike held the folded wing up; the measured stiffness turns it into a flick (s12, 21:54)
- **The issue.** On m9t both wings rose in a V at rest (F-NONLEG-1). The plain body under m9t wing settings (`scripts/probes/wing_spike_response.py`) shows why: one 2.73 µN·mm spike with a 30 ms decay lifts the folded left wing to +40° yaw or −41° pitch at 38 ms, and 17° is still left at 100 ms. A 4-spike burst lifts it to +169° yaw, with 149° left at 100 ms. The hinge spring was flybody's 1 µN·mm/rad, unsourced.
- **The source** (`docs/research/s12_wing_hinge_sources.md`). The one Drosophila hinge stiffness in open sources is the wing-pitch value fitted by Bergou et al. 2010 to free-flight kinematics: 91 ± 9 pN·m/deg = 5.21 µN·mm/rad. No source gives the yaw or roll axis or the folded hinge, so those take the same value (inferred). No source gives a steering-muscle moment arm or force, so the torque per spike is unchanged.
- **The change** (`joint:wing|stiffness_source` 1, pre-registered DECISIONS 21:44) **passed:**
  - gate silent on seeds 12-19;
  - seed-12 mean wing angles within 3° of the fold (m9t: up to 20°);
  - wings folded on the sheet;
  - adopted as m9u.
- **Behaviour now.** A single spike peaks at 15-17° at 16 ms and has 1-6° left at 100 ms. A 4-spike burst peaks at +70° yaw or −72° pitch and is back within 6° by 100 ms. So a resting burst shows as a flick of about 50 ms, not a raised wing.
- **What the result does not show.**
  - On seed 12 the wing motor neurons happened not to fire in the scored window. Across 8 seeds their rate is unchanged (0.16 against 0.19 Hz).
  - How often the wings flick at rest is set by how often the wing motor neurons burst at rest. No source says whether real ones do. A multi-seed census (seeds 14-19, 800 ms) is queued.
- **Still guessed or inferred:**
  - yaw and roll stiffness (transfer from pitch);
  - the folded-hinge stiffness (the real fold may be a separate locked state of the hinge sclerites);
  - flybody's hinge damping (0.05 µN·mm·s/rad; Bergou's fitted pitch damping is 2.2 × 10⁻³, but with the model's 10⁻⁴ armature it would leave the hinge ringing);
  - the wing torque per spike (wing-length lever);
  - the i1/i2 yaw mapping.
- **Six more seeds** (m9u, seeds 14-19, 200-1000 ms, `runs/s12/wing/census_m9u_s{14..19}.json`): no wing hinge spent any time within 1° of a limit. The right wing sits at the undriven fold (yaw +2.8°, roll −2.8°, pitch −2.4°) on every seed. The left wing, which draws most of the steering spikes (up to 15 Hz summed on pitch), averages at most 4° further out (yaw +6.8°, pitch −6.2° on seed 15). Why the left steering pool fires more than the right is not checked.

### F-NONLEG-2: every neck motor neuron pushed the head one way on both sides; the mirror-image sign makes bilateral yaw drive cancel (s12, 21:58)
- **Before.** In `data/params/motor_targets.csv`, head yaw (10 left, 10 right) and head roll (7 left, 8 right) motor neurons all mapped +1 (guessed). A pair firing together turned the head one way: about 0.33 µN·mm of standing yaw torque at rest (seeds 12 and 13).
- **Change.** `motor_map:neck|mirror_sides` 1 (DECISIONS s12 21:50). Right-side neurons take the opposite yaw and roll sign of their mirror image. The basis is bilateral symmetry (derived). Each left-side type's absolute direction stays guessed.
- **Result** (DECISIONS s12 21:58).
  - Yaw torque falls about 40-fold (0.33 → 0.008 µN·mm).
  - Gate silent on 8 seeds.
  - Head never within 1° of a limit; upright on the sheet.
- **Not tested.** No roll motor neuron fired at rest on seeds 12 and 13, in either profile.
- **Side observation.** With its drive cancelled, closed-loop head yaw sits at −6°, while on the plain body with zero drive it stays within 0.3° of zero. So the closed-loop head angle is set by the posture of the body lying on its belly (inferred, F-STAND-3), not by neck drive.
- **Still unknown.**
  - The per-neuron target pose. Gorko et al. 2024 show that neck motor neurons drive the head toward a pose, so a fixed sign is an approximation. The paper is paywalled and is on Ben's list.
  - The neck spring: flybody's 3 µN·mm/rad, unsourced.
  - The antennal elevator/depressor split (`docs/research/s12_neck_antenna_sources.md`).

### F-WING-5: the folded wings cut 40-150 µm into the abdomen, both on screen and in the contact model; lifting them 12.5° about the hinge line lays them on it (s12, 5 Oct 02:31)
- **Report.** Ben: the wings visually clip through the body when pointing straight back. Probe `scripts/probes/wing_clip.py` (plain body, standing, m9v wing settings; `runs/s12/wingclip/`).
- **It was both, visual and physical, with one cause: the folded pose.**
  - flybody's folded pose (all wing hinge angles 0) holds each wing flat at hinge height. That is 40-150 µm below the dorsal surface of abdominal segments 1-4 (cross-sections, `sections_baseline.png`).
  - **Visual.** About 24% of the vein-mesh vertices are inside the abdomen meshes, the deepest 123 µm. Seen from above, the abdomen covers the wing bases (`zoom_hinge.png`, top row).
  - **Physical.** Wing-abdomen contacts are live: the bitmasks allow them, and the abdomen is not the wing's parent body. At t = 0 they penetrate 54-144 µm, plus about 20 µm into each haltere.
    - flybody's XML excludes the wing-abdomen 1-3 and wing-wing pairs; flygym's port drops those excludes.
    - The contacts push each wing up about 4°. They leave it 51-80 µm inside after 300 ms, because the spring reference sits inside the abdomen.
  - **Wing-thorax is never checked.** The wing is a child of the thorax, so MuJoCo's parent-child filter drops the pair. At rest only the root overlaps the thorax mesh, the articulation of a rigid flat wing: vein vertices within 0.24 mm of the hinge, membrane within 0.6 mm.
    - In motion, only the hinge ranges keep a wing out of the thorax. No contact does.
- **Change.** `joint:wing|folded_pose` 1 (`passive.rest_wings_on_abdomen`; DECISIONS 5 Oct 02:31). Each wing is rotated about the thorax transverse axis through both hinges.
  - The right wing by 12.5°: derived, the smallest angle with no wing vertex inside the abdomen and no wing-body contact.
  - The left wing by 14.0°: derived, so that it clears the right wing by at least 2 µm where they overlap.
  - Left over right is guessed. Real flies differ: each fly folds with a persistent individual preference for one wing on top, unrelated to its turning bias (Buchanan, Kain & de Bivort 2015 PNAS 112:6700; abstract and a search summary read, s12). Selection lines in Purnell & Thompson 1973 (Heredity 31:401; abstract) reached a 6-10% bias and then lost it. So left on top is one valid individual; the population split was not read.
  - The pose sets the keyframes, the start state and the folded spring reference. qpos0 stays 0, because MuJoCo measures hinge angles from qpos0.
- **Result, plain body.**
  - t = 0: no wing vertex inside the abdomen and no wing contact.
  - After 300 ms passive: the wings sag 0.3-0.6° under their own weight onto the tergites. Contact penetration is 3-12 µm (soft contact) and vein vertices sit up to 19 µm in, against 51-80 µm and 84 µm on flybody's pose.
  - Sheets (`rest_on_abdomen.png`, `rest_on_abdomen_settled.png`, `zoom_hinge.png`, viewed): from the side the wings rise from the hinge and lie along the top of the abdomen. From above they cover it, with no abdomen showing through.
- **Result, closed loop and gate** (m9f, DECISIONS 02:31 result).
  - Gate on seeds 12-19: silent, thorax change under 0.01 mm.
  - Closed-loop sheet, seed 12 (`organism_m9f_s12.png`, viewed): at most 4 µm of wing-abdomen contact and 9 µm of vein overlap from 150 to 600 ms. The fly lies rolled 15-19° on its belly (F-STAND-3), so in fixed cameras the wings look shifted off the abdomen while still resting on it.
  - Root inside the thorax mesh: 1400 vein vertices up to 67 µm at rest, and 4256 up to 80 µm when spikes drive the left wing out (yaw 26°, pitch −15°). Not visible on the sheets.
- **Still open.**
  - Which wing lies on top.
  - A real wing base folds along its basal lines; this one is rigid and flat.
  - The wing-thorax pair stays filtered. A stroke that drives the wing into the thorax would pass through, and nothing reports it.

### F-TASTE-LEG-1: leg taste never crossed threshold because every type was weakly tuned to everything; receptor-line weights fix the drive, but the lying fly touches the sugar with only two tarsi (s12, 5 Oct 03:03)
- **Report** (flyapp relay). Leg taste peaks at about 2.9 mV at 1 M sugar, below the 7 mV threshold. Cause: every leg/wing taste type had a guessed weight of 0.2 to each of five tastants, so 15 mV × 0.95 × 0.2 = 2.86 mV.
- **Data** (`docs/research/s12_tarsal_grn_physiology.md`, secondary reads through a fetch-and-summarise pass). The gustatory connectome preprint (bioRxiv 2025.08.25.671814; Cell 2026) matches four census types to receptor lines by projection: LgLG4 Gr64f+/Ir56b+ (sugar, also low salt), LgAG2 Gr61a+ (sugar), WG2 (likely sugar), LgAG1 Gr33a+ (bitter). Ten types are contact-pheromone lines. LgLG3 and LgAG3-9 are not found. Ling et al. 2014 give about 50-55 Hz for tarsal sugar GRNs at 100 mM sucrose and under 3 Hz spontaneous. No leg dose-response exists in open sources, so K stays guessed.
- **Change.** `sense:taste_leg|modality_source` 1 (`extrasenses.leg_taste_weights`): matched types 1 for their modality and 0 otherwise (the labellar rule), pheromone types 0, unmatched types 0.2 (guessed). Gain and K unchanged.
- **Result** (DECISIONS 02:57; `docs/media/s12_leg_taste.png`, viewed). Drive at 1 M: 14.3 mV for the sugar types. Specificity passes (bitter and pheromone types 0 Hz on sucrose). The held-out rate fails: LgLG4 4.5 Hz mean at 100 mM, 18.5 Hz per second of contact. Only the rm (44%) and rh (92-97%) tarsi touch the floor; the fly lies down (F-STAND-3). At steady contact the cell's own LIF constants give 38 Hz at 100 mM (derived). Gate identical. Switch off under the registered rule.
- **Open.** Wing taste cells (WG1-4) have no leg and take the mean of six legs' contact (guessed; should be wing contact). MN9 stays at 0 Hz with tarsal sugar GRNs firing; real flies extend the proboscis to tarsal sugar.
- **Trace, leg sugar GRNs to MN9** (Director, 5 Oct 04:08-04:30; `scripts/probes/legsugar_mn9_trace.py`, `runs/s12/legsugar/trace_s12.json`; seed 12, m9r, switch on). Real flies extend the proboscis when a tarsus touches sugar (tarsal PER, a classic measured behaviour).
  - **Hops: 3** (GRN → layer 1 → layer 2 → MN9) in the model connectome (min 5 synapses per edge), also 3 using excitatory cells only. 54 sugar GRNs (LgLG4 43, LgAG2 11); 50 lie on a shortest path, from all six legs. The full male-cns table has a 2-hop route only through two DNd02 cells with 2-3 synapses in and 1-4 out, so the working route is 3 hops.
  - **Synapses per hop** on the shortest paths: 2092 (123 edges, none inhibitory), 1942 (86 edges, 52% inhibitory), 1716 (39 edges, 23% inhibitory). Layer 1 is 27 cells (AN01B004 ×5, GNG147 ×3 inhibitory, GNG353, AN13B002 inhibitory and others); layer 2 is 32 GNG and DNge cells. Widest path: LgLG4 → AN01B004 30889 → GNG134 36316 → MN9_L, 58, 25 and 30 synapses.
  - **Where it dies: between layer 1 and layer 2, in every test** (figure `docs/media/s12_legsugar_mn9_trace.png`, viewed; `scripts/probes/legsugar_mn9_plot.py`).
    - Sugar patch, 1 M, closed loop: only the lm and lh GRNs fire (23 and 33 Hz; the lying fly's other tarsi do not touch). 3 of 27 layer-1 cells respond (one excitatory AN01B004 at 13 Hz, two inhibitory AN13B002 at 30 Hz). No layer-2 cell changes. MN9 never leaves rest.
    - Every leg sugar GRN driven at its 1 M drive (14.3 mV, no contact needed): 4 excitatory layer-1 cells fire (AN01B004 ×3 at 13-37 Hz, GNG353 at 17 Hz). No layer-2 cell responds; MN9 0 Hz. The best-fed layer-2 cells (GNG538, GNG134) get 41-42 synapses from the firing layer-1 cells, 1-2% of their 2140-3588 input synapses, and peak at 12-26% of the way to threshold. Foreleg GRNs alone recruit no layer-1 cell. Those five layer-2 cells take 77-92% of their input from central-brain intrinsic cells (top types GNG542, GNG241, GNG211, SMP604), 5-15% from ascending and 3-9% from descending neurons, and none directly from labellar sugar GRNs: an integrating layer in which leg sugar is a small minority.
    - Shiu et al. 2024 parameters (m2, open loop, Poisson 100 and 200 Hz into the 54 GRNs, 2 trials): up to 9 layer-1 cells fire (GNG353 up to 99 Hz, AN01B004 up to 73 Hz), no layer-2 cell, MN9_L 0 Hz. The working profile open loop (m9r) also gives 0 Hz at 100 and 200 Hz.
  - **Controls.** Labellar sugar (34 LB3b/c cells at 14.3 mV, closed loop, m9r): MN9 0 Hz, held below rest; the MN9 inputs that respond are mostly inhibitory (GNG043, DNge051, GNG130), consistent with the known conductance-synapse block (F-R2-1). Under m2 the same labellar path works: MN9_L 26 Hz at 100 Hz input (21 and 31 Hz in 2 trials). Adding leg sugar at 200 Hz raises it to 40 Hz (37, 43); at 100 Hz, 21 Hz (19, 23), within trial spread.
  - **Reading.** The block is in the wiring as modelled, not only in the parameters or the posture. Leg sugar converges on MN9's premotor cells, but too weakly to drive them alone: it adds to labellar sugar under Shiu parameters and does nothing by itself under either parameter set. Posture is a second, smaller block (the forelegs do not touch the patch). In real flies tarsal sugar alone evokes PER, so something that carries leg sugar to the GNG layer is missing or too weak. Connections under the 5-synapse cut are ruled out: with every edge of 1 synapse or more (25.6 million edges), m2, leg sugar at 200 Hz still gives MN9_L 0 Hz (2 trials; `runs/s12/legsugar/assay_leg_m2_min1.log`, backhouse). Remaining candidates: hunger-state modulation downstream of the GRNs (the model applies hunger only to labellar GRN drive, and a higher GRN rate alone does not help, since 200 Hz input already fails); neuromodulatory or electrical routes not in the graph; a sensory or interneuron population missing from the male-cns leg taste types.
  - **Next discriminating experiment.** A sourced search for the tarsal PER pathway in real flies (which cells carry leg sugar to the SEZ, and whether any is identified in male-cns). If an identified cell exists and is on the model's path, its measured response to tarsal sugar tests the layer-1 → 2 gain directly.
  - **Labellar control, open loop, working profile** (m9r, Poisson into LB3b/c, 2 trials; `runs/s12/legsugar/assay_lab_m9r.log`, backhouse): MN9_L 0 Hz at 0 Hz, 6-7 Hz at 100 Hz, 13-14 Hz at 200 Hz. So under m9r the labellar path reaches MN9 open loop but not in the closed-loop lying fly; leg sugar reaches it in neither.
  - **Search result** (5 Oct 04:38; `docs/research/s12_tarsal_per_pathway.md`, secondary). Thoma et al. 2016 split tarsal sweet GRNs into segmental cells (9-10 per leg, end in the VNC, slow walking) and ascending cells (2-4 per leg, project straight to the GNG, start feeding). Male-cns has both (inferred match): LgAG2 (11, `sensory_ascending`, 1-3 per leg, 37-62% of output onto brain cells) and LgLG4 (43, `vnc_sensory`, none onto central-brain intrinsic cells). With all leg sugar GRNs injected, LgAG2 fire at 37 Hz; 4 of their 39 brain partners fire (GNG353, GNG141, two GNG266) and most of the rest peak at 0.4-0.96 of the threshold gap. No firing or calcium data exist in open sources for any second-order leg taste cell. Named cells (Dandelion, DNg103) have no male-cns label. Hunger in real flies raises sweet GRN presynaptic calcium (summary level), and the model applies hunger only to labellar GRNs. Next: drive LgAG2 alone with a bounded presynaptic gain behind a switch, pre-registered, reading layer 2 and MN9.
  - **Two rescues fail** (DECISIONS 04:40 and 04:50, diagnostics, m2 open loop unless stated, LgAG2 at 100 Hz, 2 trials). (1) Presynaptic gain on LgAG2 (a hunger-like terminal gain): MN9_L 0 Hz at ×1 and ×3, 3 Hz at ×10, 5-7 Hz at ×30 (post hoc); all 54 leg sugar GRNs at ×10, 10-13 Hz (post hoc); under m9r 0 Hz up to ×10. At ×10, 15 of 16 layer-1 cells fire but only 3 of 26 layer-2 cells. (2) Disinhibition: silencing the 8 inhibitory cells on the paths, or those plus all 43 inhibitory inputs to MN9_L, leaves MN9_L at 0 Hz.
  - **Mechanism, as far as it is known.** In the model connectome, leg sugar reaches the GNG through the ascending GRNs (LgAG2) and their first relays, but the premotor layer that drives MN9 takes nearly all its excitation from other brain cells (77-92% central-brain intrinsic input; leg sugar 1-2%). Neither a stronger first synapse nor removing inhibition lets leg sugar through, so the missing piece is excitation into layer 2: an unidentified excitatory route, a state that raises layer-2 excitability (hunger acting downstream of the GRNs, not measured), or cells missing from the traced leg taste types (LgAG2 has 1-3 per leg against Thoma's 2-4; LgLG4 5-9 against 9-10). Tarsal PER is normally measured in starved flies (assay practice; not sourced this session), and the model has no measured hunger effect on central taste cells. No further fix this session.
  - **Dandelion and LgLG3** (DECISIONS 04:59, diagnostic; `docs/research/s12_tarsal_per_pathway.md`). The taste connectome (v2, secondary) identifies Dandelion, a key partner of labellar and leg sugar GRNs, as male-cns AN13B002, and proposes LgLG3 (162 cells, 23-31 per leg; the model gives it the unmatched weight 0.2) as a sugar type because Dandelion is its top partner (8770 synapses). AN13B002 is a layer-1 cell on the model's path and is predicted GABAergic (confidence 0.89), so the model makes it inhibitory. Driving LgLG3 + LgLG4 + LgAG2 (216 cells) at 100 Hz: Dandelion fires at 310-320 Hz under m2, MN9_L 0 Hz under m2 and m9r. Transmitter evidence (05:04): GABA by both EM classifiers (male-cns 0.89; BANC 0.96-0.97), and BANC's `neurotransmitter_verified` says gaba. That label's basis is undocumented and it covers 431 of 440 hemilineage-13B cells, so it is probably lineage-level (inferred). No measurement of this cell type was found. Its sign decides whether leg sugar excites or suppresses the feeding premotor layer in the model; HANDOFF item 1.
  - **Dandelion sign bracket** (5 Oct 21:56; DECISIONS 21:30, diagnostic, neither sign adopted). Tonight's search found no cell-type measurement: the best direct evidence is GABA transcripts in hemilineage 13B (Lacin et al. 2019 FISH, ground-truth confidence 3; measured for the lineage, inferred for this cell), and the classifiers' GABA call is not independent of it. Running Dandelion as acetylcholine instead of GABA leaves MN9_L at 0 Hz under leg drive (m2 and m9r, 3 trials each) while 537-782 more VNC cells become active (its partners AN09B004, ANXXX027, IN01B065, leucokinin LK, abdominal motor neurons). Labellar sugar changes by +5% (m2) and −25% (m9r, 6.7 vs 5.0 Hz); sugar + bitter stays 0 Hz. So the sign does not decide leg PER in the model, which supersedes the line above that it does. The block stays between layer 1 and layer 2 whichever sign Dandelion has. The settling experiment for the sign is on HANDOFF's list for Ben.
  - **Next discriminating evidence.** The taste-feeding connectome paper (Tastekin et al., Cell 2026) states LgLG4 reaches MN9 "in a few hops" with "high connectivity" (search snippet, unverified). Reading its path analysis by eye, and matching its "Dandelion" second-order cell to a male-cns type, would show whether the paper's route is the model's 3-hop route or one the model lacks. Dandelion is now matched (AN13B002); a measured transmitter for it (FlyWire AN_GNG_68) was thought the most discriminating single fact; the 21:56 bracket shows it is not, for PER. Reading the paper's path analysis is now first.
  - **The paper's route, read by eye, and feedforward inhibition** (5 Oct 22:04-22:45; DECISIONS 22:04, diagnostic). Tastekin et al. (bioRxiv v2, Fig. 9B) route leg sugar LgLG4 → AN01B004 → Bract I/II → Roundup → MN9, with a side branch through S&S. In male-cns these are DNge174, DNge173, GNG108 (measured synonyms) and GNG159 for S&S (inferred from its edges); the male-cns synapse counts match the figure, so the model has the paper's route. It stops at Bract 2, which gets 9-10 mV of excitation from AN01B004 and 4-9 mV of inhibition from GNG093 and GNG250 (GABA predicted), which AN01B004 also drives: feedforward inhibition (derived mean-drive split). Silencing those 4 cells at 200 Hz input: Bract 2 rises from 0-2 to 10-22 Hz under m2, Roundup to 1-3 Hz, MN9_L to 0-2 Hz with the 54 matched sugar GRNs; with LgLG3 added (216 cells), Roundup 4-10 Hz and MN9_L 15, 3, 6 Hz. Under m9r Roundup stays at 0-1.3 Hz even with Bract 2 at 16-25 Hz, and MN9_L at 0-3 Hz. So feedforward inhibition at Bract 2 is a necessary block in the model and, under m9r, Bract 2 → Roundup is a second. Both sit on predicted or fitted values (GNG093/GNG250 transmitter; m9r per-cell excitability), not on wiring. Nothing adopted. Next facts: whether GNG093 and GNG250 inhibit in the animal, whether LgLG3 is a sugar type, and why m9r's Roundup needs more drive than m2's.
  - **Why m9r blocks it: a profile ladder** (5 Oct 23:14; DECISIONS 23:05 and its result, diagnostic). With the feedforward inhibition at Bract 2 silenced and 200 Hz into the 3-type leg sugar set, Roundup passes under m4 (82 Hz) and m7 (78), is blocked under m8 (0) and m9r (1.2), and passes under m9r with the rung-1 intrinsic currents switched off (77; MN9_L 131). So the intrinsic currents alone cause the second block (H1 as pre-registered; class gains, size rules, consensusNt and psp rejected). They attenuate a GNG cluster that co-excites Roundup (AN17A002 → GNG588/GNG578 → GNG143/GNG167 → Roundup) at every hop. With the feedforward inhibition left on, m7 and m9r without intrinsic currents still block (MN9_L 0 and 0.3), because GNG093 and GNG250 also inhibit that cluster (430 synapses onto GNG588). The route needs both blocks lifted. Both rest on inferred values: a predicted GABA sign, and a central intrinsic-current prior fitted only on slow leg motor neurons. Seen, not scored: once the route ignites MN9_L runs at 120-130 Hz. Channel knockouts under m9r are running (DECISIONS 23:12).
  - **The channel is BK** (5 Oct 23:26; DECISIONS 23:12 and its result, diagnostic; figures `docs/media/s12_legsugar_chko.png` and `docs/media/s12_central_fi.png`, viewed). Under m9r with the feedforward inhibition silenced, BK off alone lets the route through (Roundup 31.5 Hz, MN9_L 48), and BK, Kv2 and SK off together almost restore it (69.5, 120). A, M, h, SK or Kv2 alone leave it blocked (Roundup 0.7-2.0); A and M together are marginal (4.2). In a single cell with the same constants, BK leaves rheobase alone but halves the gain above it (95 against 167 Hz at 40 mV of drive). Its value is the slow tibia flexor fit (8.69 × g_L0, 3 of 4 seeds) carried unscaled to every central cell without a transcriptome row (inferred). The expectation I wrote (A-type) was wrong.
  - **But central BK is not too strong** (5 Oct 23:58; F-FI-1). The one central cell with a recorded f-I (MBON-α3, which carries the same class prior) has 2-5× less gain than the model's version with BK on. So BK off is not a biological fix. The remaining candidate is resting excitability: the recorded cell sits near threshold, the model's route cells sit 7 mV below it.
  - **Nearer threshold, the route opens** (6 Oct 00:22; DECISIONS 00:05 and its result, diagnostic, nothing adopted; figure `docs/media/s12_legsugar_rest.png`, viewed). The 43 route cells (17 types: the paper's route, the GNG cluster and the feedforward inhibitors) were given a fixed drive (`scripts/probes/route_rest.py`, guessed, per cell from its own isolated rheobase). BK and the inhibition were left on, under m9c, 3 trials.
    - **1 mV below each cell's rheobase** (silent at rest): Roundup goes from 0 to 33-35 Hz and MN9_L from 0 to 34-39 Hz at 200 Hz input. MN9_L stays at 0 Hz with no input. This holds for both the 54 matched sugar GRNs and the 216-cell set.
    - **At rheobase, or at 12 Hz in isolation:** the route fires with no input (MN9_L 41-42 Hz). The cells excite one another, so cells set to 2 Hz alone run at 30-40 Hz together.
    - **Unchanged (base):** blocked.
    - My prediction (MN9_L under 5 Hz with the cells 1 mV below rheobase) was wrong.
    - **Reading.** Resting excitability on the route is enough to open it, with the class-prior BK and the predicted inhibition intact. Once open, the route switches rather than grades: 100 and 200 Hz input give nearly the same output. The measurable fact is a GNG route cell's resting potential against threshold, or its spontaneous rate (Roundup or Bract patch); it goes on Ben's list.
    - **Without noise, the low resting rates are a knife-edge.** In a single generic cell, membrane noise of 0.75-1.5 mV/√ms gives 0.1-7.6 Hz at rest with a 2-4 mV membrane SD (derived; `scripts/probes/noise_rest.py`).
    - **Next** (to pre-register): under the same raised excitability, test specificity (leg bitter, and labellar controls), dose response and offset; then a noise version.
  - **1 mV is a hair trigger; 3-4 mV passes every route check** (6 Oct 01:28; DECISIONS 00:26 and 00:41 and their results, diagnostic, m9c open loop, 3 trials; figure `docs/media/s12_route_margin.png`, viewed).
    - **At 1 mV (`near`)** the route fails specificity. Leg bitter alone at 100 Hz drives MN9_L at 6-9 Hz, through AN05B106 (316 synapses from LgAG1). The spontaneous GRN rate (3 Hz, Ling 2014) drives it at 13-17 Hz. Single GRN spikes fire the entry cells alone on 12 of 25 and 8 of 32 connections (`scripts/probes/unitary_psp.py`). The route grades logarithmically (MN9_L 15 to 39 Hz from 3 to 200 Hz input) and never latches (0-2 Hz in the second after).
    - **At 3 and 4 mV below rheobase** all four checks pass: 3 Hz silent (0-1 Hz), 50 Hz open (k = 3: 16-18 Hz; k = 4: 8-9), leg bitter at 100-200 Hz 0 Hz, labellar bitter still silences labellar sugar, and 0-1 Hz in the second after. Input that brings MN9_L to 5 Hz: about 10 Hz (k = 3) and 25 Hz (k = 4), under the real 50-55 Hz (derived). 2 mV still fires at 3 Hz.
    - **The margin acts downstream of the entry cells**, which grade alike at every margin. The paper's Bract branch (DNge174, DNge173, with GNG093 and GNG250) opens first and carries MN9_L to 8 Hz at k = 4 alone. The GNG578/GNG143 → Roundup–DNge059 branch opens later (between 10 and 25 Hz input at k = 3). Silencing DNge059 changes MN9_L little at k = 1 (13 against 15 Hz at 3 Hz), so the Roundup–DNge059 loop is not the trigger.
    - **The leg bitter leak is cured by the margin.** Presynaptic inhibition of sugar GRN terminals is not needed for it; its evidence is recorded in `docs/research/s12_presyn_inhibition.md` (GABA-A and GABA-B at ORN terminals; Root et al. 2008 implies about halving of gain at strong input; no taste numbers).
    - **Seen, not scored.** Labellar sugar at 100 Hz gives MN9_L 24-47 Hz at k = 2-4, against 4-6 Hz under m9c: the route cells are shared, so any margin fit for the leg route also amplifies the labellar route about 5-8×.
    - **Reading.** A 3-4 mV margin on the route cells is a one-number fit to one route (guessed margin, derived rheobase). It does not stand as a model value until a whole-brain version passes the gate.
  - **The whole-brain version fails the gate** (6 Oct 01:38; F-STAB-6). The same margin as a class drive on central_other, AN and DN, or on central_other and AN alone, leaves the brain firing after input stops, held by the reciprocally wired GNG117 pair. The leg sugar route stays open only with its own 43 cells near threshold, which is a route-specific fit.

### F-STP-1: measured short-term depression at ORN synapses silences m9r's PNs, and the LN-more-transient ordering does not appear (s12, 5 Oct 22:45)
- **Data.** Two adult connections have published depression fits from 10 Hz antennal-nerve trains: ORN→PN f 0.78, τ_rec 893 ms (Nagel, Hong & Wilson 2015, n 19) and ORN→LN f 0.75, τ_rec 1566 ms (Nagel & Wilson 2016, n 9). LN→LN facilitation is reported without a number. No other adult connection had a usable number (search list in `data/params/stp_connections.csv`).
- **Change** (built, off). `synapse:all|per_synapse_parameters` = 1 reads `data/params/stp_connections.csv` and applies Tsodyks-Markram depression per edge (`lif._stp_connections`; 56,261 ORN edges; values derived as U = 1 − f). Tests in `tests/test_stp_connections.py`. Values above 1 raise NotImplementedError; the GPU port refuses the switch.
- **Result** (DECISIONS 22:20 and its result). Gate passes on seeds 12-19, but uPN mean falls from 3.7-4.0 to 0.80-0.88 Hz, AL_PN by 78-80% and AL_LN by 67-72%. Under an odour step uPN and LN responses become transient (transience 0.93-0.95 → 0.02-0.05 for uPN; 0.96-0.99 → 0.07-0.11 for LN; figure `docs/media/s12_stp_al_step.png`, viewed). The held-out ordering, LNs more transient than PNs (Nagel & Wilson 2016), fails on all 3 seeds, and uPN rates are in the 1-5 Hz range on 0 of 8 seeds. The switch stays off.
- **Reading.** m9r's ORN→PN weight was fitted without depression, so adding measured depression removes about two thirds of the resting drive (derived steady state 0.32 of resting strength at 11 Hz). The measured depression belongs with the measured unitary EPSP (11× the current weight), which overdrove PNs in session 7 without fitted per-class inhibition (LESSONS: one global efficacy). The depression package, the unitary strength and LN→PN inhibition have to be fitted together. Why LNs stay less transient than PNs when their edges depress more is untested (candidates: loss of LN→LN inhibition, undepressed PN→LN input).
- **N29 is now partial**: per-connection STP for the two measured connections. Per-synapse weight, release probability, receptor mix and latency are not built.

### F-LEGK-1: the passive model leg is 3-5× softer than a living leg under compression, with the compliance in the femur-tibia joint; after unloading it wedges against the thorax (s12, 5 Oct 22:49)
- **Data** (held out from B3). Oeftger, Moussian & Lehmann 2026 (iScience 29:116404, PMC full text read): decapitated living flies, left middle leg pushed against a force wire to 1.0 mm. Wild-type stiffness is 13.1 ± 7.97 µN/mm (slope over 0.2-0.9 mm, n 11). Femur-tibia changes −3.3 to −5.3 °/µN; 72% of the loading work is lost per cycle (measured).
- **Probe** (`scripts/probes/leg_compression.py`; body only, m9r body switches, thorax fixed, actuators 0, force on lm_tarsus5 toward the thorax-coxa joint). Arms with the tarsus free or locked, with or without other legs. The coupled leg springs are applied by Python hooks in `Body.step`; a probe that calls `mj_step` directly loses them (the first run collapsed at 0.25 µN for that reason).
- **Result** (DECISIONS 22:37 and its result; figure `docs/media/s12_leg_compression.png`, viewed). Over the paper's 0.2-0.9 mm range the model's slope is 2.4 µN/mm (tarsus free) to 4.0 (locked); the secant at 4 µN is 3.7-4.2. Femur-tibia carries the change, at −19 to −21 °/µN (4-6× more compliant than measured). Above about 1 mm joints reach their limits. 0 warnings, no NaN.
- **Reading.** Consistent with B3: a passive leg should be softer than a living one with tone and chordotonal control (the authors name the femoral chordotonal organ). The measured stiffness and femur-tibia slope are targets for resting tone in a closed-loop arm, which would also show whether the femur-tibia springs themselves are too soft. B26 (cuticle compliance) is not needed for this experiment: the angles change, so the compliance is in the joints.
- **Seen, not scored.** After unloading the coxa-trochanter stays at −71 to −89° (−39° at the start), with lm_tibia and lm_trochanterfemur in contact with `c_thorax`: the leg is wedged against the body by contact. Any posture that flexes the coxa-trochanter strongly may stick the same way. Not yet checked in the closed-loop fly.

### F-CLOCK-1: the clock drive never made a clock cell fire; fitted to DN1p day-night firing it is a 0.25 mV knife edge (s12, 5 Oct 23:40)
- **Data** (held out until the fit; `docs/research/s12_central_fi.md`). Wild-type DN1p "fire at ∼10Hz in the morning (Zeitgeber Time, ZT0-4) and are nearly silent in the evening (ZT8–12)"; *per*⁰¹ DN1p fire 2.2 ± 1.1 Hz (ZT0-4) and 3.9 ± 1.5 Hz (ZT8-12) (Flourakis et al. 2015 Cell, brain explant, read).
- **Probe** (`scripts/probes/clock_phase_rates.py`; brain only, open loop, clock phase set by hand, ZT = CT). Under m9r every clock cell is silent at CT 2 and CT 10: the 3 mV drive (guessed) is under the 7.5 mV onset. All 12 DN1p cells fire identically, because no noise and no network input of note reach them. s-LNv and l-LNv follow the same curve.
- **Fit** (DECISIONS 23:34 and its result; figure `docs/media/s12_clock_dn1p_grid.png`, viewed). `g_clock_mv` 7.75 gives DN1p 11 Hz at CT 2 and 0 Hz at CT 10 (held out, passes). The onset is steep: 7.5 mV gives 1 Hz and 7.75 mV gives 11 Hz (derived), so the fitted rate holds only while nothing else changes their input. Any later change to central excitability must re-run the probe.
- **Start phase.** Runs began at CT 0, where the fitted drive is 6.7 mV, still below onset. The new key `state:clock|initial_ct` (default 0) is set to 1.5 in the candidate m9c. That is the male-cns specimen's dissection time, ZT 1.5 in 12:12 LD (Nern et al. 2024 Methods, read). In the closed loop the morning cells then fire at about 4 Hz (derived from the clock class mean, 1.0-1.25 Hz over 32 cells across 8 seeds).
- **Mismatch kept.** The model's clock-less DN1p (gain 0) is silent; *per*⁰¹ DN1p fire 2-4 Hz. A baseline drive plus a smaller daily swing would fit all three numbers, but that is a two-number fit and was not pre-registered.

### F-FI-1: the one recorded central f-I (MBON-α3) is 2-5× shallower than the model's central cell, so switching off BK moves the model away from the data (s12, 5 Oct 23:58)
- **Data** (Hafez et al. 2023 eLife, Fig. 1 supp. 1C, figure estimate; Rm and τm read). Three MBON-α3 cells under 400 ms steps start firing at −6 to +2 pA and reach 20-50 Hz at +32 pA (0.67-1.32 Hz/pA). The cell is described as spike-frequency adapting. A steady soma step reaches the spike initiation zone at about 40-70% (Gouwens & Wilson 2009, PN model, read; transfer to MBONs inferred).
- **Probe** (`scripts/probes/central_fi.py --cell-type MBON14`; DECISIONS 23:56 and its result; figure `docs/media/s12_mbon14_fi.png`, viewed). The model's own MBON14 cells (generic constants, class-prior channels) under the same protocol, calibrated to the measured passive deflection.
  - Under m9c: onset +8 pA, 77.5 Hz at +32 pA, 3.23 Hz/pA (FAIL high).
  - BK off: 5.31 Hz/pA. Rung 1 off: 5.52 Hz/pA.
  - Across the mapping corners, BK off stays 3.5-7.1 Hz/pA. Onset-matched (post hoc), the model is still 2-3× steeper with BK at the corner most favourable to it.
  - The model cell does not adapt; it sits 7 mV below threshold and jumps to 12-23 Hz at onset.
- **Reading.** The class-prior BK is not too strong for this central cell: the cell's gain is already too high with it. The leg sugar block that BK-off removes (F-TASTE-LEG-1) is therefore not explained by central BK. The mismatch that does relate to it is resting excitability: the recorded cell relays from near threshold, the model's from 7 mV below. The next experiment is a route bracket nearer threshold (pre-register first). One cell type, ex vivo, soma recording, figure estimates; nothing adopted.

### F-STAB-6: a whole-brain resting level 4 mV below rheobase turns the reciprocally wired GNG117 pair into a switch; no class-level drive at the leg sugar route's margin is gate-safe (s12, 6 Oct 01:38)
- **Test** (DECISIONS 01:16 and 01:24 with results; diagnostic). The route-only margin that passes the leg sugar checks (3-4 mV below rheobase, F-TASTE-LEG-1) applied as a class tonic drive (`class:<class>|tonic_drive`, guessed) to central_other, AN and DN, or subsets, under m9c, gate seeds 12 and 13.
- **Result.** All three classes at 3.7 or 4.7 mV: the brain keeps firing after input is removed on both seeds (1.4-24.5 spikes/ms; rule 0). Without the DN class (noDN): 10 and 11 spikes/ms. DN class alone: 0 and 1.06. central_other stays within the held-out ≤ 1.4 Hz (0.63-1.0 Hz). At 4.7 mV the central complex lights up (P-EN 22-26 Hz; Turner-Evans 2017 standing 3.9 ± 2.6, not scored). Open loop, noDN with leg sugar at 50 Hz latched on 1 of 3 trials (MN9_L 81 Hz during, 105 Hz after).
- **Mechanism** (male-cns counts measured; transmitters predicted). The highest-rate cells in every failing run are the same: GNG117 (both cells, 110-155 Hz), its targets GNG153, GNG186 and DNge022, and GNG031. GNG117_L and GNG117_R excite each other with 914 and 973 synapses (22-23% of each cell's input, predicted acetylcholine). Without adaptation or depression that pair is bistable, and 4 mV of extra excitability lets body afferents (closed loop) or leg sugar (open loop) switch it on. With no body and no stimulus the same brain sits at 0.01 Hz.
- **Correction.** The stage 1 write-up named this the DNge019 / DNg12 loop of F-STAB-1/2. DNge019 joins at lower rates; the core is the GNG117 pair.
- **Reading.** The leg sugar route needs its cells near threshold, and this brain cannot rest near threshold everywhere until something holds the GNG117 pair: central adaptation (N4), depression at its reciprocal synapse, inhibition from DNg98 / AN05B007 (GABA, 546 and 497 synapses), or a non-excitatory GNG117. Two fixes failed; nothing adopted. For Ben's list: GNG117's transmitter, and whether GNG117 fires persistently after a brief stimulus.

### F-VISION-4: L2's low photoreceptor count is R7/R8 input to L1 in the medulla, not a missing L2 input; the real lamina blank is truncation (s12, 6 Oct 01:45)
- **Relay** (flyapp, fly's-eye view): L2 gets a median of 2 photoreceptor synapses against 16 for L1.
- **Check** (male-cns edges, every synapse count, which reproduces the relay's 16 and 2; the model's 5-synapse threshold removes under 0.1% of the R1-R6 → L1/L2 weight). The medians count every photoreceptor type. L1 gets a median of 7-8 synapses from R7/R8 in the medulla; L2 gets 0. From R1-R6 in the lamina, L1 and L2 are nearly equal: total weight 103,405 against 107,646, with matching per-cell distributions. That is the tetrad arrangement of the lamina, where each R1-R6 release site faces an L1 and an L2 element.
- **The real blank is truncation.** 66% of left and 43% of right L1/L2 cells get no R1-R6 synapse. Where present, the right-side median is about 34-36 and the maximum about 320, the value of a complete cartridge: Rivera-Alba et al. 2011 (read, one reconstructed cartridge) count 42 synapses from each photoreceptor terminal onto each of L1 and L2, about 250 per cartridge. So even the cartridges that have input mostly carry about one terminal's worth. L3 gets 23,510 in total and at most 203 per cell. The scan types 3,377 R1-R6 (right 2,265, left 1,112; 1,394 traced) against about 9,600 in a fly; their median is 38 T-bars and 79 output synapses per cell.
- **Reading.** The L1/L2 asymmetry in the relay is real biology (R7/R8 reach L1's medulla arbor) and needs no change. Half the cartridges have no photoreceptor input in the model, which will thin and patch the visual input to the medulla. Completing them would be a derivation (per-cartridge R1-R6 → L counts from the complete cartridges or the lamina EM literature) and needs pre-registration before it enters the model.

### F-VISION-5: vision stops after the lamina because graded release starts at rest; recorded modes plus tonic release move T4/T5 by only 0.1-0.2 mV and make HS and CT1 fire tonically (s12, 6 Oct 02:40)
- **Test** (DECISIONS pre-registration and results 02:08 and 02:40; figure `docs/media/s12_vision_grating.png`, viewed). A drifting sine grating (30°, 1 Hz, full contrast) goes straight onto the photoreceptors: no body, open loop, m9c. There are four arms: B (m9c), T (tonic release r0 0.5, guessed), R (recorded modes) and RT (both). Each is scored on per-cell F1 at 1 Hz against the static grating.
- **Mechanism, stage 1.** Graded release is `clip((v − v_rest)/(v_th − v_rest), 0, 1)`, which is zero at and below rest. L1 and L2 receive only histamine inhibition from R1-R6, so they swing 1.5-1.6 mV below rest and release nothing at any light level. Everything below the lamina sits at exactly −52 mV in B and R.
- **Stage 2.** Tonic release at rest (T) gives the medulla the right signs: Mi1 is hyperpolarised by L1's glutamate and Tm1 depolarised by L2's acetylcholine. The modulation reaches the medulla at 0.4-0.65 mV per cell, 5-9 mV under the spiking threshold of medulla types whose mode is guessed spiking. T4/T5 stay at −52.00.
- **Stage 3.** Making the recorded types graded as well (RT; Mi1, Tm1-3 from Behnia et al. 2014, T4/T5 from Gruntman et al. 2018/2019, all measured; L4/L5 inferred) lets T4/T5 follow the grating at 0.1-0.2 mV per cell above static. That fails the 0.5 mV criterion on all 8 subtypes, and it has three side effects:
  - At mean luminance, HS fires 104-140 Hz, VS 59 Hz and CT1 335 Hz. All three are spiking in the model by guess.
  - 111 spiking-mode cells in 21 types fall below −100 mV within 20-90 ms (Am1 to −668 mV, H2 −227 mV). This is current-based inhibition with no reversal potential.
  - Under T, the gate's dark silent window fires 16 spikes/ms, because L1/L2 rest in the dark and release tonically.
- **Reading.**
  - The remaining block is gain. Full contrast moves R1-R6 by 2.95 mV, the LMCs by 1.5 mV, the medulla by 0.6 mV and T4/T5 by 0.2 mV, inside a guessed 7 mV graded range.
  - The release rule needs a sign-correct LMC transfer: hyperpolarisation must signal to ON and OFF targets.
  - The type means hide a skew. The 90th-percentile cell swings 4.5-4.8 mV in L1/L2, 1.7-1.9 mV in Mi1/Tm and 0.4-0.7 mV in T4/T5.
    - Truncation halves the mean.
    - Each graded stage after the lamina passes on about 1/2.6 of its input's swing. That factor is set by the guessed `graded_rmax` (100 Hz) and the per-synapse efficacy.
  - Recorded Mi1, Tm1, Tm2 and Tm3 swing 15-20 mV to full-field flashes (Behnia et al. 2014 Fig. 2, figure estimate), and T5 5-11 mV to moving bars (Gruntman et al. 2019 Fig. 1). That is 3× the model's whole 7 mV graded range (guessed), and about 10× what the model's medulla does.
  - Tonic release cannot be adopted without bounded inhibition (conductance mode).
  - The mode rows still missing are CT1 (2 cells, 109-138k output synapses each, a median 8-17% of each T4/T5's input; physiologically compartmentalised, from memory, to verify), Am1, HS/VS/H2 and the LPi cells.
  - The relay's 13 Hz Am1 rhythm did not appear open loop. In RT, Am1 runs away instead.
  - No change adopted. The next block is a pre-registered photoreceptor-to-LMC gain arm with conductance-mode inhibition.

### F-VISION-6: the medulla's ON response is capped by disinhibition from a leak reversal set to the recorded dark potential; more LMC gain lowers the dark state instead (s12, 6 Oct 03:14)
- **Corrected by F-VISION-7 (03:29).** m9c leaves `rest_from_recordings` off, so the leak was −52 mV, not the recorded −55. The measured conductances show that the leak is not the binding limit. The result and the side effect below stand; the mechanism and the reading do not.
- **Test** (DECISIONS: gain block pre-registered 03:04, result 03:14; figure `docs/media/s12_vision_gain.png`, viewed). Full-field flash from darkness (Behnia et al. 2014 Fig. 2 stimulus), open loop, m9c plus:
  - conductance-mode synapses (bounded inhibition);
  - recorded modes and tonic release at rest (r0 0.5, guessed);
  - graded spans from recorded amplitudes (`graded_range_from_recordings` 2: R1-R6 60 mV, LMCs 45, Mi1/Tm 20);
  - photoreceptor gain 78 (fitted by linear scaling).
  The LMC output scale is 1, 3 and 10. Scores are medians over cells whose cartridge has photoreceptor input (`visual_flash_score.py`).
- **Result.**
  - Mi1 ON is +1.5, +2.7 and +3.1 mV against a recorded +20; Tm3 is +2.8 to +3.8 against +15; Tm1/Tm2 OFF is under 0.7 against +15-20.
  - L1 hyperpolarises 17-23 mV against 45, L2 10-14.
  - R1-R6 peaks at +46.8 against 60: sublinear, with a sag and an OFF undershoot. These are network effects in the model; their source has not been traced.
  - No cell leaves [−90, 20] mV.
- **Mechanism.**
  - Mi1's ON response is disinhibition: light hyperpolarises L1, which cuts L1's tonic glutamate onto Mi1. A disinhibited cell can only return toward its uninhibited potential.
  - In the model that potential is the leak reversal, −55 mV, which is the recorded resting potential, plus weak acetylcholine from L5 and L3.
  - In light, connected Mi1 reaches −57 to −58.5 mV and never −55. Raising the LMC scale tenfold lowers the dark baseline (−58.7 to −61.6) about as much as it raises the light peak.
  - The recorded response reaches about −35 mV from a dark −55. So the recorded rest is a dark potential held down by tonic inhibition, not a leak reversal. Using it as the leak reversal counts the inhibition twice (inferred).
- **Side effect.** Mode 2 keeps transfer per mV, so tonic release grows with the span. Tm1/Tm2 depolarise in darkness to −36/−38 mV at LMC ×3 and to −18/−23 at ×10 under L2's tonic acetylcholine. L1 climbs to −26 through L5 → L1 excitation. The dark potentials bound the LMC scale before Mi1 does.
- **Reading.**
  - Recorded medulla amplitudes need two things: an uninhibited potential well above the dark potential, and a tonic synaptic conductance comparable to or larger than the leak (about 1.3× leak, derived for Mi1 from a 20 mV swing between −55 and −35 with a −70 mV reversal).
  - Recorded dark potentials then become targets for the in-network dark state. For cells with tonic excitation (Tm1, Tm2), the leak reversal must stay physiological (bounded by the potassium reversal), so a larger conductance there needs a balancing tonic inhibition. 22% of Tm1's input synapses are from Pm2a/b GABAergic cells.
  - Discriminating recordings for Ben's list: Mi1 input resistance (or conductance) in dark and light, and the GluClα reversal in Mi1.
  - Nothing adopted.

### F-VISION-7: Mi1's ON swing is limited by modulation depth and by tonic inhibition from non-graded inputs, not by its leak reversal (s12, 6 Oct 03:29; corrects F-VISION-6)
- **Test** (DECISIONS, correction at 03:29). `scripts/probes/visual_conductance_state.py` on the gain block base, LMC ×1 and ×10. Connected cells, 600 ms dark then 300 ms of full-field light. Conductances are split by presynaptic type and are model outputs (derived).
- **Result at LMC ×1.**
  - Mi1 goes from −58.7 to −57.6 mV. Its inhibitory conductance falls from 2.00 to 1.72 leak units: L1's share from 1.27 to 0.94, while the 0.73-0.78 from non-graded inputs stays put.
  - With every inhibitory input removed, Mi1 would sit at −41 mV.
  - L1's release falls 27% because L1 hyperpolarises 14 mV (−46 to −60) of a 45 mV release span with r0 0.5. L1 is floored by the −70 mV reversal, 24 mV below its dark potential.
- **Mechanism (inferred).** Two factors multiply:
  - Modulation depth. Light cuts L1's tonic release by a quarter to a third, and at most about half even with unlimited photoreceptor drive.
  - Tonic inhibition. Mi1's other inhibitory inputs are Pm1/Pm2a/Pm2b/Pm3 (GABA) and Dm1 and Mi13 (glutamate), 34% of its synapses, all non-graded in this configuration. Their tonic inhibition balances the L5/L3 excitation, so a complete L1 shutoff would reach only −52 mV, a 6.7 mV swing.
  - More LMC gain raises the tonic and modulated conductances together (×10: G 22), so the dark potential falls toward −70 and the swing stays near 3 mV.
- **Reading.**
  - The parameters that set Mi1's swing are the release rule's r0 (guessed) and span (inferred), the inhibitory reversal (declared default −70; M10Q has −56), and the modes of the Pm/Dm1/Mi13 inputs (guessed).
  - The recorded leak or rest is not one of them. Fitting any one of them alone will not reach 20 mV.
  - Discriminating recordings:
    - Mi1's input conductance in dark and light;
    - the light responses and spiking/graded mode of Pm and Dm1 cells;
    - the ort/HisCl reversal in LMCs, measured against the lamina's local extracellular potential. Zheng et al. 2006 report the lamina intercellular space at −20 to −40 mV relative to the retina, and LMC potentials of −40 to −70 mV on the same reference, so the recorded 45 mV LMC swing includes any light-evoked change in the lamina field and is not directly a transmembrane amplitude (inferred).

### F-VISION-8: the photoreceptor→LMC synapse is about 10× below the recorded small-signal gain, and in a single-compartment conductance cell no release scale can close it; the limit is driving force times release-curve steepness (s12, 6 Oct 03:59)
- **Test** (DECISIONS, pre-registration 03:42, addendum 03:53, result 03:59; figure `docs/media/s12_vision_first_synapse.png`, viewed).
  - Gain block base set; `visual_flash.py` dim flash (500 ms at 0.01 and 0.05 of the full flash) and full flash (1 s).
  - Photoreceptor release scaled by k 1, 10, 30 on R1-R8 (`class:photoreceptor|release_scale`), then 30 on R1-R6 alone (per-type `release_gain` row, diagnostic).
  - Conductances from `visual_conductance_state.py`, split by presynaptic type, graded and spiking (split residual about 0).
- **Result.**
  - The R1-R6→L1 small-signal gain is 1.24 at k 1 (L2 0.66). Recorded in *Calliphora*: about 13 at a dim background, 1.5-4.5 in bright light (Juusola, Uusitalo & Weckström 1995). Transfer to *Drosophila* is inferred.
  - The gain saturates at 6.1-6.2 from k 10.
  - L1's dark potential falls with k (−46.1, then −58.2 at k 30), because tonic dark release scales too. At k 30 it is 2 s.d. below Pantazis et al. 2008 (−43 ± 7.3 mV).
  - With R1-R8 scaled, Mi1's full-flash ON response vanished (+0.003 mV), because R7/R8 histamine onto Mi1 (595 of 795 connected cells, about 11 synapses each) grew with light. With R1-R6 alone Mi1 returns to +1.13 mV (k 1: +1.51), and its inhibitory conductance falls in light.
  - Tm1/Tm2 OFF grew from 0.35/0.53 to about 1.8 mV with either arm. Mi1, Tm3 and L1/L2 stay 4-18× short of their recordings.
- **Mechanism (derived).** In a one-compartment cell with leak, excitation and a histamine-gated chloride conductance g_i (reversal E), let v₀ be the potential with g_i = 0 and a = 1 + g_e. If g_i is proportional to release r(V_R), the small-signal gain is
  - gain = (E − v₀) · a · g_i / (a + g_i)² · (d ln r / dV_R) ≤ (E − v₀)/(4s),
  - where 1/s is the release curve's logarithmic slope at the dark potential: the distance to the foot for a linear rule, the e-fold for an exponential one.
  - In the model, E − v₀ = 25.2 mV (−70 against L1's −44.8) and s ≈ 0.65 mV, so the ceiling is about 9.7. Scaling release only slides g_i along the a·g_i/(a + g_i)² curve, which k 30 already sits on top of (g_i 1.17 against a 1.16).
- **Sources on the two factors (measured unless marked).**
  - Release extent: in *Calliphora* photoreceptor release falls steeply about 12 mV below the dark resting potential (Uusitalo et al. 1995, J Neurophysiol, abstract). With a linear rule that foot gives a ceiling near 0.5. So the recorded gain needs a curved release with e-fold s of about 0.5-1 mV (inferred).
  - Driving force: the lamina space is −20 to −40 mV against the retina in darkness, with LMCs at −40 to −70 on the same reference (Zheng et al. 2006, *Drosophila*). In *Calliphora* the space sits 30 mV below the retina in the dark and depolarises in light (Weckström & Laughlin 2010). The LMC transmembrane dark potential may therefore be 20-30 mV less negative than the recorded one (inferred). The ort reversal against that transmembrane potential is not measured.
  - At s = 1 mV, 13 needs E − v₀ ≈ 52 mV; at s = 2 mV, about 104 mV (derived).
- **Reading.**
  - The first-synapse shortfall is a model-form limit: a linear release rule with a near-zero foot plus a recorded-potential operating point. It is not a missing gain.
  - The R7/R8 inputs to L1 and Mi1 in the medulla are large enough to reverse Mi1's light response when overdriven, so any photoreceptor-level scale must be per type.
  - Next discriminating experiment: a curved release rule (bounded s) together with an LMC transmembrane offset from the lamina field (bounded 0-30 mV). Train on the dim gain; hold out L1's dark potential and the full-flash medulla responses.
  - Recordings that would settle it:
    - a *Drosophila* R→LMC gain or release curve;
    - LMC transmembrane potential and ort reversal against the lamina space;
    - the sign and strength of R8→Mi1.
- **Refinement (04:02; derived from the 03:59 conductance states, `cstate2_kR1`, `cstate2_R16kR30`).** The two factors above are not independent.
  - With D = v₀ − v_dark, the tonic histamine hyperpolarisation of the dark LMC, and p = D/(E − v₀), the small-signal gain is D(1 − p)/s. So it is below D/s however much driving force there is; driving force helps only through (1 − p), at most 2×.
  - The model's s is 0.6 mV. That is the photoreceptor's dark offset above the release foot, set by `photoreceptor:all|dark_drive` 1.0 mV (guessed). The release curve is already steep enough; its extent is wrong: zero 0.6 mV below dark, against about 12 mV (Uusitalo).
  - D is 0.8 mV at k 1 (small-signal gain 1.3) and 12.7 mV at k 30 (small-signal gain 10.6).
  - The dim flash moves R1-R6 0.64 mV, about one s, so it doubles release. Its gains are large-signal: the conductance arithmetic gives 1.20 and 6.6, against 1.24 and 6.2 measured. The saturation "near 6" is this large-signal value, not the small-signal ceiling.
  - The binding conflict is between D and L1's dark potential. A gain of 13 at s 0.6 needs D of about 8-13 mV. With L1's histamine-free potential at v₀ −44.8 mV (global leak −52 guessed, plus L5/Mi1/Tm3 excitation), that puts the dark potential at −53 to −58, below Pantazis's −43 ± 7.3.
  - So the levers are v₀ (L1's leak and non-histamine inputs) together with a release curve that keeps s near 1 mV but extends about 12 mV below dark. The lamina-field driving force is secondary.
  - The measurement that pins v₀ directly is the LMC dark potential with histamine transmission removed (ort or hdc mutants, or a block).

### F-VISION-9: the photoreceptor→LMC synapse meets the recorded dark potential and small-signal gain together when L1/L2's histamine-free potential is about −32 mV; the medulla deficit then sits in Mi1's tonic inhibition and L1's release floor (s12, 6 Oct 04:11)
- **Test** (DECISIONS pre-registration 04:05, result 04:11; figure `docs/media/s12_vision_first_synapse.png`, viewed). F-VISION-8's arithmetic was solved for the two targets, L1 dark −43 mV (Pantazis 2008, *Drosophila*) and gain 13 (Juusola 1995, *Calliphora*). The solve gives an L1/L2 leak shift of +15.1 mV (leak −36.9; v₀ −31.8) and R1-R6 release ×12.5, set as diagnostic rows (derived). Dim flashes at 0.001 and 0.01, a full flash, and the conductance state.
- **Result.**
  - L1 dark −43.7 mV. Small-signal gain 11.8 (i 0.001), 9.6 at i 0.01.
  - L1 full-flash ON −25.1 mV (0.56 of the recorded 45; k 1 gave 0.37); L2 −18.2.
  - Mi1 +2.3 mV (recorded 20), Tm3 +4.2 (15), Tm1/Tm2 OFF +1.6/+1.9 (17.5), T4a +1.0. Every prediction landed within its tolerance.
- **Mechanism (derived from the conductance state).**
  - Lamina: one compartment with tonic histamine conductance g_i ≈ 0.49 leak units (p 0.30) and release e-fold s 0.61 mV gives gain D(1 − p)/s with D 11.9 mV.
  - Mi1: L1's inhibition falls 1.34 → 0.74 in light, while 0.7 leak units of spiking Pm2b/Dm1/Pm2a/Pm1 inhibition stays constant. That caps Mi1 at about 6.9 mV.
  - Tm3: L1 inhibition 1.17 → 0.68, with little else. L1's release floor (0.30 at −70 mV with r0 0.5) caps Tm3 at about 4.3 mV, which it already reaches. Without the floor the cap is about 12 mV.
- **Reading.**
  - The first synapse can be made consistent with both recordings, but only by predicting an LMC histamine-free potential of about −32 mV (unmeasured).
  - The two other readings are an LMC transmembrane offset from the lamina field, or a steeper release curve. Neither is excluded: s is set by the guessed photoreceptor dark drive.
  - Downstream, the next limits are named parameters: the Pm/Dm1 modes and the GluClα reversal for Mi1, and L1's release r0 and span for Tm3.
  - Discriminating recordings:
    - an ort or hdc LMC dark potential (v₀);
    - Laughlin, Howard & Blakeslee 1987's transfer curve (s; an unverified secondary quotes an e-fold of 1.5-1.9 mV, which would contradict the model's 0.61);
    - Pm/Dm1 light responses.

### F-VISION-10: LMC output release reaching zero at the LMC's light-saturated potential lifts Tm3 to 0.62 and Mi1 to 0.27 of recorded, as predicted; Mi1 is now at its tonic-inhibition ceiling (s12, 6 Oct 04:32)
- **Test** (DECISIONS pre-registration 04:19, result 04:32; figure `docs/media/s12_vision_release_floor.png`, viewed). On the v0 arm (F-VISION-9), L1/L2 release at rest was lowered from 0.5 (guessed, class value) to 0.26 (inferred), so that release reaches zero at the LMC's light-saturated potential, −68 mV. The principle is that a graded synapse uses its presynaptic cell's whole range (Juusola et al. 1996). The new switch is `cell_type:all|release_at_rest_per_type` (off by default, CPU only; battery 229 passed).
- **Result.** Every pre-registered readout passed:
  - Tm3 ON +9.3 mV (predicted +7 to +11; recorded +15), up from +4.2.
  - Mi1 ON +5.5 (predicted +4 to +6.5; recorded +20), up from +2.3.
  - Tm1/Tm2 OFF +2.8/+3.4 (recorded +17.5), up from +1.6/+1.9. Their ON dips are −8.7/−7.3. T4a ON +2.0.
  - The lamina is unchanged: L1 dark −43.7, gain 11.8.
  - Steady-state potentials were within 0.5 mV of the one-compartment predictions.
- **Mechanism.**
  - Mi1: L1's inhibition now falls to zero in light. The 0.80 leak units of spiking Pm2b/Dm1/Pm2a/Pm1 inhibition left are Mi1's ceiling.
  - Tm3: 0.27 leak units of tonic inhibition remain. Its no-inhibition ceiling is about 6 mV above its light potential.
  - Tm1/Tm2: OFF depends on L2's overshoot after light-off, against 0.78 leak units of tonic Pm2a/Pm2b inhibition.
- **Reading.**
  - The lamina-to-medulla handoff is now quantitatively understood. The remaining medulla deficit is tonic inhibition from spiking Pm/Dm cells whose modes and light responses are guessed.
  - r0 0.26 rests on a principle, not on a measured LMC release curve. A recorded LMC→Mi1/Tm3 transfer curve would test it.
- **Correction to F-VISION-9's DECISIONS entry.** L1 does have a depolarising OFF transient in the v0 arm (connected median +10.7 mV). The 04:11 entry misread the diluted type mean.

### F-VISION-11: on v0r, T4/T5 modulate 3-4× more but stay below the 0.5 mV criterion with no direction selectivity; their inhibition is a tonic CT1 shunt and Mi4/Mi9 carry no signal (s12, 6 Oct 04:46)
- **Test** (DECISIONS pre-registration 04:33, result 04:46; `docs/media/s12_vision_grating_v0r.png`, viewed). `motion_grating.py` (30°, 1 Hz, contrast 1) on v0r against RTc.
- **Result.** Per-cell F1: Mi1 0.70-1.07 mV (predicted 1.5-3.5), Tm3 0.89-1.55 (2.5-5.5), T4 0.14-0.29 (0.4-1.2), T5 0.15-0.30. V passes for 0 of 8 subtypes; the direction index is 0.00-0.03. All predictions failed low.
- **Mechanism (conductance probe, diagnostic).** T4/T5 inhibition is mostly CT1 at a tonic 400 Hz (T4a 0.24 of 0.37 leak units; T5a 0.45 of 0.56). Mi4 and Mi9 sit in spiking mode near −49 mV and are barely modulated by light, so no slow, offset arm reaches T4. With only fast excitation and a constant shunt, the model cannot be direction selective.
- **Reading.** This confirms the Director's 02:10 diagnosis for vision: the gap is cell modes and dynamics (rungs 4 and 5), not a gain number. Mi4, Mi9, C3, Tm4, Tm9 and CT1 need sourced mode rows, and Mi1/Tm3 against Mi4/Mi9 need sourced kinetics, before DS can be tested.

### F-BYPASS-1: with the CNS bypassed, the legs can lift the fly but no constant activation holds a standing posture; the failure sits in distal muscle capacity at the placed pose, a flat force-length curve, abdomen sag, and unmapped muscles (s13, 13 Oct 21:58)
- **Test** (DECISIONS pre-registration 21:36 and addendum 21:50; `docs/media/s13_bypass_s1.png`, viewed). `bypass_s1_actuation.py`, m10f0, adhesion 1, 3 s, activations set by hand (DIAGNOSTIC, forced drive). Patterns: support (hold-direction muscles only), coact (all), need (each muscle at its measured static hold torque × k).
- **Verdict: FAIL as pre-registered.** No level of any pattern holds (z ≥ 0.9 mm, sink < 0.05 mm, no trunk contact, foot force 0.8-1.2 W).
- **Capacity is there in total.** Support 0.3 lifts the thorax from 1.32 to 1.38 mm; at support 0.5 the feet carry 0.99 W net of adhesion. Adhesion alone presses 0.61 W (measured in the model).
- **Localisation.**
  - Distal capacity: at the placed pose, the static hold needs 6.1× the hind tibia-tarsus muscle's capacity and 1.3-1.5× the femur-tibia flexors'; the coxa needs 0.96 of capacity (derived, need pattern). At k = 1 the fly sinks 1.29 to 0.84 mm.
  - No open-loop stability: moment arm over optimal length is about 0.09 per rad, so force-length gain stays ≥ 0.93 over ±1 rad (derived). Constant activation gives near-constant torque, so the fly either lies down (support ≤ 0.2), rears 45° nose-up (0.3-0.5) or flips over (1.0). Holding a height needs feedback (S4) or a steeper force-length curve.
  - The abdomen tip drags whenever the fly is up (no abdominal tone).
  - Interface gaps (audit): the 12 mid and hind coxa promotor muscles have no MN (MN type name likely differs on T2/T3); Tr-roll −1 has no MN on any leg, TiTa −1 none on mid and hind legs; 187 of 505 leg MNs reach no muscle (mostly long-tendon MNs).
- **Measurement fix** (addendum): the coxa had counted as foot and adhesion inflated foot force; both corrected before the need runs.
- **Reading.** The placed pose (1.32 mm, against about 1.0 mm inferred from Wang 2025) may itself be too tall for the distal muscles. Next body check: the need pattern at a lower placed pose, and the MN type names for T2/T3 coxa promotors.

### F-BYPASS-2: DNg100 drive with the brain off recruits E1 and E2 of Pugliese's oscillator but not its inhibitor I1; leg MNs stay tonic and nothing alternates (s13, 13 Oct 21:58)
- **Test** (DECISIONS pre-registration 21:41; `docs/media/s13_bypass_s2_dng100.png`, viewed). `bypass_s2_descending.py`, m10f0, brain silenced, senses off, tethered; DNg100 at 10/15/25/40 mV, 300-1300 ms (DIAGNOSTIC, forced drive).
- **Verdict: FAIL** at every level. DNg100 fires 27/48/73/104 Hz; premotor mean 0/0.05/0.13/0.38 Hz; leg MN 4.4-5.4 Hz (mostly the 60 tonic tibia flexors at 15 Hz); peak activation 0.01-0.19. At 40 mV one hind tibia-tarsus pool reaches rhythm excess 0.14 at 5.6 Hz, but with no antagonist or left-right anti-correlation. Legs barely move in the frames; at 25-40 mV the wings open and flick.
- **Chain** (40 mV, Mac rerun, 600 ms): 235 VNC interneurons fire, mostly GABAergic. E1 (IN17A001) fires at 13-18 Hz in 5 of 6 cells, and so does E2 (INXXX466). I1 (IN16B036, glutamate, inhibitory here as in Pugliese) is silent in all 6.
- **Why I1 is silent** (derived from the weights): E2→I1 sums to 69 mV of weight, about 1.8 mV peak per E2 spike against a 7 mV threshold gap. GABAergic IN19A004 (active at 15 Hz, −52 mV) and IN19A002 (−180 mV) inhibit it.
- **Also:** a 22 mV LIF weight gives a peak depolarisation of only about 0.16× that (synaptic current filtered by 5 and 16-20 ms time constants). At 12 mV drive, DNg100 at 36 Hz lifts E1 by 3-5 mV only.
- **Reading.** Pugliese's rate model passes graded signals through every cell. In our spiking model the oscillator's inhibitory arm is never recruited, which points to S3 (graded release in nonspiking VNC interneurons) before any weight change. DNb08, DNg97 and DNa02 runs are in progress.
- **Addendum, 22:09: DNb08, DNg97 and DNa02 also fail** (frames `docs/media/s13_bypass_s2_other.png`; rasters `docs/media/s13_bypass_s2_rasters.png`; both viewed). At 15 and 40 mV these DNs fire 38-40 and 92-96 Hz and the leg MNs fire 3.8-4.7 Hz. The top pools are always the tonic tibia flexors (15 → 17.5 Hz). A single pool turns rhythmic twice, DNb08 15 mV (left-middle tibia flexor) and DNg97 40 mV (left-middle coxa anterior rotator), but neither has an anti-correlated partner. Peak activation is 0.01-0.21. In the frames the legs only fold passively. So S2 fails for all four candidate walking DNs, and the break is not specific to DNg100.

### F-BYPASS-3: Pugliese's own spiking model doesn't recruit I1 on the male-CNS connectome either; their oscillator needs graded transmission or MANC's stronger E2→I1 (s13, 13 Oct 22:11)
- **Test** (DIAGNOSTIC). Their published LIF code (`src/lif_model/lif_dynamics.py`, Extended Data Fig. 4, Shiu parameters: 0.275 mV per synapse, 7 mV threshold gap, τm 20 ms, τs 5 ms), run unchanged on the Mac on two inputs from their repository: (a) their MANC T1L mini-circuit; (b) the left T1 cells of their male-CNS extract (`W_20260210_vncRoisOnly.csv`), with DNg100 driven at 10, 15 and 25 mV. Scratch scripts are in `/tmp/pug_ref` (not kept).
- **MANC reproduces.** BDN2 (MANC's DNg100) at 67 Hz drives E1 and E2 in 4 bursts in 300 ms (13.5 Hz, 3 spikes each). I1 (IN16B007) fires one spike per cycle, about 33 ms after E1 has started. One of 25 MNs (a pleural promotor) bursts twice per cycle; the other 24 stay silent (Vmax −48.7 to −52 mV). So even in their spiking reference the MN read-out of the rhythm is sparse.
- **The male CNS doesn't.** I1 (IN16B036, bodyId 801884; the MANC→male-CNS mapping goes through `mancBodyid` and is correct) never fires at any drive or with any subset of the inhibitory cells. Its Vmax is −46.9 to −50.1 mV against the −45 mV threshold.
  - With E1, E2 and I1 only: E1 and E2 fire tonically (20-76 Hz).
  - Adding IN19A007 (GABA) produces a cycle at 12.7/22.6/32 Hz with one E1, E2 and A007 spike per cycle. Our m10f0 network shows this same mode (smoke chain: E1 16 Hz, E2 12 Hz, A007 12 Hz, I1 silent, Vmax −49.6 mV).
- **Why** (derived from counts):
  - In T1L the male-CNS E2→I1 count is 38 synapses against 71 in MANC (0.54×). E1→I1 is small in both.
  - I1 also receives GABA from IN19A002 (−28 mV of model weight in T1L) and IN19A004.
  - Our per-synapse efficacy (0.157 mV, fitted brain-stability ceiling) is 0.57× Shiu's 0.275 mV.
  - Pugliese's rate model avoids the threshold altogether, because every cell passes graded signals.
- **Literature** (Sonnet sweep, 13 Oct):
  - Measured: 13Bα cells are nonspiking (all recorded cells, Agrawal 2020 eLife); 10Bα are largely nonspiking; 9Aα spike.
  - 16B (I1's hemilineage), 17A and 19A have never been recorded. Whether I1 spikes is unknown.
  - Nobody has measured input resistance, resting potential or threshold for any VNC premotor interneuron. The 7 mV gap is Shiu's brain-wide guess, not a measured value for these cells.
  - Glutamate→leg MN: MN clusters co-express GluClα with NMDA and kainate subunits (Allen 2020), so the sign is inferred, not measured.
- **Reading.** I1's silence is a property of the male-CNS counts under a spiking threshold, not an implementation bug. The biological questions are whether I1 releases graded (unknown) and how strong VNC synapses are (unmeasured). S3 tests both with existing class-level switches (DECISIONS 22:09); no per-synapse knob.

### F-STAND-4: placed at Wang's median head height, the fly collapses at every constant activation; a passive-fold pose splays the legs, and their torques lift the legs instead of the body (s13 fly2, 13 Oct 23:25) [renumbered from the fly2 branch's F-BYPASS-4 at the 13 Oct rebase; main's F-BYPASS-4/5 are the nerve-cord findings]
- **Test** (DECISIONS pre-registration 23:16; `docs/media/s13_bypass_s1fix1.png`, viewed). `bypass_s1_actuation.py --head-mm 0.929` on backhouse, m10f0, seed 12, adhesion 1, 3 s (DIAGNOSTIC, forced drive). The head is placed 0.5 mm above this body's collapse (Wang 2025 median, measured; the zero is inferred). The pinned root is lowered and the unpowered legs fold where the floor pushes them (pose inferred, passive fold). Need k = 0.5-2; support 0.1-0.5.
- **Verdict: FAIL, 0 of 10, as predicted.** Every run ends with the thorax origin at 0.47-0.56 mm (placed 0.96) and the head at 0.43-0.48 mm, which is the collapse. Trunk touch fraction 0.997-1.0 (head, abdomen 4-6, coxae; in support runs, the thorax too). Net foot support −0.24 to −0.50 W: adhesion pulls harder than the floor pushes, so the trunk carries the weight. Pitch change 10-12°, head down.
- **Viewed:**
  - At t = 0 the legs splay sideways and the abdomen almost touches the floor.
  - From 250 ms on, the fly lies on its belly at every level. The active legs (two to four, mostly front and middle) rotate upward into the air.
  - At this pose the pitch-joint torques swing the legs, not the body. At the old 1.32 mm pose, support 0.3 lifted the fly; here no level does. Lowering the fly made standing worse.
- **The hold-need numbers here are unverified.** At the placed pose only the feet touch (checked 23:27 with `--place-only`; an earlier draft wrongly said the trunk already touched). The trunk is down within the first 10 ms of every run. Whether it also touched during the 300 ms hold-need measurement was not recorded; `hold_need` now records it from fix 1b on. The hind TiTa 1.50× (pair max; was 6.1×) and the pair mean of 0.086 may understate the need, so they are not evidence that height closes the gap.
- **Reading:** height alone is not the variable. The pose the legs take to reach that height decides whether the muscles can bear weight. A passive fold is not a standing pose, and measured standing joint angles are a blank: Wang 2025 has none, and Karashchuk 2021 and Haustein 2024 give tethered envelopes. Wang's height is spent as a setting (register).
- **Next (pre-registered separately):** fix 1b holds the roll and yaw hinges at the neutral pose while lowering, so the legs fold in their pitch planes under the body. Then fix 2, the LTM Hill muscle.

### F-STAND-5: folding the legs only in their pitch planes changes nothing, so pose and height are not the bottleneck; the original placement is already inside Wang's measured height range, and the hold-need instrument is invalid at lowered poses (s13 fly2, 13 Oct 23:35)
- **Test** (DECISIONS pre-registration 23:26; `docs/media/s13_bypass_s1fix1b.png`, viewed). Same as F-STAND-4, plus `--pitch-only`: during the lowering, instrument springs hold the coxa yaw and roll and the trochanter-femur roll. Gate 1 passed: only the feet touch at the placed pose.
- **Verdict: FAIL, 0 of 10, as predicted.** The thorax origin ends at 0.50-0.54 mm and the head at 0.43 mm (the collapse; support 0.5 ends at 0.58 with the fly rolled). Trunk touch fraction 0.997-1.0; net foot support −0.27 to +0.09 W; pitch change 9-10°.
- **Viewed:** the same as fix 1. The fly is belly-down by 250 ms, two to four legs rise into the air at every level, and support 0.5 rolls the fly onto its side. At t = 0 the pitch-plane fold looks almost the same as the passive fold: flybody's neutral legs already spread sideways, so lowering the body splays them whichever hinges fold.
- **The hold-need instrument fails at the lowered pose** (now recorded): during its 300 ms hold, the abdomen and the left front femur reach the floor, and the floor carries 0.93 W. The need pattern (pair max 3.1×, coxa 2.8×) therefore measures the floor, not the legs, and the need runs drove muscles in proportion to that. The fix 1 needs were presumably affected the same way (not recorded). Whether the original 6.1× at 1.32 mm was clean is unchecked.
- **The original placement is inside the measured range.** Thorax origin 1.32 mm gives a head of 1.29 mm, 0.86 mm above this body's collapse (0.429). Wang 2025's digitised range is about 0.15-1.35 mm (n = 92; `targets_session6.csv` row 61). By the per-value bar ("consistent with some fly"), the 1.32 mm pose was never too tall. Lowering it to the median made standing worse (F-BYPASS-1: support 0.3 lifted the fly at 1.32 mm).
- **Reading:** height and fold are not the bottleneck, so the pose hypothesis from F-BYPASS-1 is dropped. What remains, in order of evidence:
  1. The TiTa pair at the 6.1× joint is a guessed placeholder (F0 20 µN, r 0.01 mm; `leg_muscles*.csv`). No Drosophila source gives a tibia-muscle or LTM force (research note addendum 23:30; FlyMimic excludes the tibia muscles).
  2. Constant activation with a flat force-length curve gives no restoring force once a foot leaves the floor; the legs that lift swing freely (F-BYPASS-1).
  3. The abdomen still has no tone (a blank).

### F-STAND-6: a tibia-tarsus pair at the measured specific-tension range does not let constant activation hold a stance; more strength moves the runaway, it does not remove it, so stability, not capacity, is the break (s13 fly2, 13 Oct 23:47)
- **Test** (DECISIONS pre-registration 23:36, addendum 23:40, step 0 and predictions 23:43; `docs/media/s13_bypass_s1fix2.png`, viewed). `bypass_s1_actuation.py --set muscle:leg|tita_specific_tension={9,28,37} --k-hold-mult 25` on the Mac, m10f0, seed 12, adhesion 1, 3 s, original placement (thorax origin 1.32 mm, inside Wang 2025's range) (DIAGNOSTIC, forced drive). The switch sets each TiTa muscle to flybody tibia mid-third cross-section × specific tension, r = half the distal tibia width, L0 travelling with r (inferred upper bound; 11-31× the placeholder's capacity at 28). Need k = 0.5, 0.75, 1, 1.5; support 0.1, 0.2, 0.3, 0.5.
- **Step 0 (instrument):** only the feet touch at every K_HOLD; sag < 0.01 mm first at ×25. The need does not converge (pair max 6.1/8.0/10.0/4.9× at ×1/5/25/125): six feet under one weight is statically indeterminate, and a stiffer instrument puts the load on fewer legs (a diagonal pair at ×125). Robust part: some TiTa muscle needs 4.8-10× the placeholder at every valid stiffness, and the femur-tibia flexors need up to 1.1-2.8× theirs.
- **Verdict: FAIL, 0 of 24, as predicted** (both predictions).
  - Need runs are identical at all three tensions: the need activation is need ÷ capacity, so the torque delivered is the same; the femur-tibia flexors clip at 1 at every k. They end crouched with trunk contact (0.65-0.99) and wings opened.
  - Support 0.1-0.2: collapse onto the belly at every tension.
  - **Support 0.3 at 9 mN/mm² comes closest:** legs under the body, no trunk contact for the whole 3 s, but it sinks 1.32 → 1.235 mm (0.16 mm over the last 2 s) and pitches 10.6°. At 28-37 the same level lets the abdomen touch half the time (z 1.19).
  - **Support 0.5:** at 9 the fly pushes itself up to 1.61 mm (+0.29 mm, pitch 15°); at 28 and 37 it flips onto its back by 1000 ms.
- **Reading:** under constant activation, the stance has no stable height. Low support sinks, high support rises or flips, and stronger TiTa moves where that happens without creating a level that holds. With a flat force-length curve (r/L0 ≈ 0.1 per rad, kept as shipped here), a constant activation gives near-constant torque, so nothing pulls the body back when it moves. This is the pre-registered falsifier branch: capacity is not the break (the 9 mN/mm² bound already carries the weight for 3 s without trunk contact); stability is.
- **Not adopted.** The switch stays neutral (0 = placeholder). It is an inferred upper bound with no non-standing held-out check, so it can only be "consistent".
- **Interpretation (Director, 13 Oct):** a standing fly does not use constant activation. It uses tonic drive plus resistance reflexes (FeCO and campaniform sensilla → MNs). The next body step is a minimal measured proprioceptive loop through the real connectome with the bypass drive held constant (fly2's; separate pre-registration).

### F-GJ-2: no identified Drosophila gap junction has a coupling number in readable primary text, and the s10 JO-B→GF site contradicts the source that measured JO→GF coupling (s13 fly2, 13 Oct 22:19)
- **Coupling magnitudes.** Read in full text (Sonnet sweep, 13 Oct):
  - eLN–PN: Yaksi & Wilson 2010. Coupling coefficients appear only in Fig 4C (n = 37 control pairs, 19 shakB2). Depolarisation passes better than hyperpolarisation.
  - Sister PNs: Kazama & Wilson 2009. Values appear only in Fig 7d; coupling is larger for depolarising steps.
  - JO→GF: Pézier et al. 2016 gives no coupling coefficient.
  - Not accessible: VS–VS (Haag & Borst 2004, Cuntz 2003), Ammer 2022, Thomas & Wyman 1984. Tanouye & Wyman 1980 was not found.
  - So every DC coupling in `data/params/gap_junctions.csv` stays blank (registered unresolved, not simulated) until a figure is digitised.
- **GF rows carry spikes, not DC.** TTMn follows each GF spike 1:1, so the GF→TTMn and GF→PSI rows use a spike step of safety (2, guessed) × the partner's threshold distance. The step is delivered after the GF conduction time only. It is rectifying, with the reverse direction 0: ShakB(N+16)/ShakB(L) rectifies in oocyte pairs (Phelan 2008).
- **JO-B contradiction.** Pézier 2016: "the GF is NB-coupled only to the A group of JON axons". The JO-B1_a/JO-B1_c→DNp01 kicks in `electrical.CURATED_PAIRS` (s10) name the wrong subgroup. Their strength is 0 in every profile, so no run is affected.
  - male-cns has no JO-A→DNp01 chemical synapse at the working threshold, so the JO-A row is registered with partners `none`. It is not simulated.
- **Validity.** Point cells, so a junction sees the somatic potential. The DC coupling is explicit, from start-of-step potentials, and is stable only while c·dt/τm ≪ 1.

### F-GJ-3: with the GF gap junctions on, TTM latency is 1.10 ms (inside the Augustin 2017 WT band) and TTMn follows every GF spike; DLM never responds, because male-cns gives PSI no transmitter (s13 fly2, 13 Oct 22:24)
- **Run.** `scripts/probes/gf_latency.py --profile m10f --trials 20`, pre-registered 22:18. Output: `runs/s13/fly2/gf_latency_m10f.{json,png}` (figure viewed).
- **Gaps off.** TTMn, PSI and both DLMn types follow 0 of 20 GF spikes (control 0). One GF spike's chemical input does not fire them. This matches shakB2 losing the short-latency response (Thomas & Wyman 1984).
- **Gaps on.** TTMn and PSI follow 20 of 20 (control 0), central latency 0.3 ms in every trial. Latency to muscle: TTM 1.099 ms, PSI 1.097 ms, against the band 0.866-1.216 ms (WT young 0.926 to old 1.216). The pre-registered TTM prediction holds; the falsifier did not fire.
- **What this shows, and what it doesn't.** It is a consistency check, not a validation of the junction:
  - 1:1 following is built in, since the spike step is 2 × the threshold distance.
  - The latency is the sum of delay rows: GF conduction 0.27 ms (v measured), plus TTMn axon 0.30 ms (v inferred), plus 0.5 ms neuromuscular (inferred).
  - The stimulus-to-GF time in the recordings is not modelled.
- **DLM: the prediction failed.** I predicted "above the band, about 2 ms". In fact DLMn never fired within 10 ms in either arm (follow 0.00).
  - Measured reason: PSI is `unclear` in both predictedNt and consensusNt, and the hemilineage fill (`connectome:unclear|nt_by_development`, on in m10f) has no row for PSI. So PSI has sign 0 and transmits nothing to DLMn (406 synapses onto DLMn c-f, 43 onto DLMn a, b).
  - Physiology: PSI→DLMn is "an identified cholinergic synapse", and TTMn and PSI "are connected via electrical synapses to the giant fiber" (Fayyazuddin et al. 2006 PLoS Biol 4:e63, open text). The same paper reports a WT synaptic potential of 4.71 ± 0.35 mV (n = 10) at the soma; the cell is not checked. Lead, not adopted.
- **Spent.** The DLM latency (Augustin 2017 S1 Table) is now seen on m10f. A later PSI-transmitter fix can only report DLM as a consistency check.
- **Next (not done).** Give identified types their transmitter from physiology (PSI = acetylcholine), under a neutral switch with the source per row. Then check whether one PSI spike fires DLMn under the shared synapse scale.

### F-GJ-4: with PSI cholinergic, PSI fires on every GF spike but DLMn still never fires; one PSI spike gives DLMn 0.5-1.6 mV, against 4.71 mV measured at the MN5 soma and a 7 mV threshold gap (s13 fly2, 13 Oct 22:48)
- **Run.** `gf_latency.py --profile m10f --trials 20 --set connectome:identified|nt_from_physiology=1` (pre-registered 22:35; `runs/s13/fly2/gf_latency_m10f_psiach.json`). Then `scripts/probes/gf_psi_dlm_path.py` (same build, gaps on; `runs/s13/fly2/gf_psi_dlm_path.json`) for the edges and the DLMn voltage after one GF spike.
- **Result.** Gaps on: TTMn and PSI follow 20/20 (TTM 1.099 ms, as F-GJ-3); DLMn a, b and c-f follow 0/20 (control 0). Gaps off: all 0/20, as predicted. The conditional DLM latency prediction (2.1-2.3 ms if DLMn fires) is untestable.
- **Measured reason.** PSI is now acetylcholine, sign +1, and each PSI contacts 5 ipsilateral DLMns (17-68 synapses per pair). One PSI spike raises DLMn by 0.47-1.65 mV (peak at about 10 ms; the 17- and 26-synapse a, b pairs 0.47 and 0.61 mV). DLMn rests at -52 with threshold -45 (shared defaults), so the gap is 7 mV.
- **Physiology** (Fayyazuddin et al. 2006 PLoS Biol 4:e63, Fig 5, open text): GF stimulation at 1 Hz, MN5 soma held at -74 mV, "the synaptic potential underlying the spike measured at the soma ... was 4.71 ± 0.35 mV (n = 10)"; and "The PSI bypasses the entire dendritic structure of MN5 and makes multiple synaptic contacts that span 50 μm and follow the axons out into the posterior dorsal motor nerve." MN5 drives DLM fibres a, b (so `DLMn a, b`; inferred from memory of Ikeda & Koenig 1988, not checked).
- **What it means.** Two gaps, both at the value level. (1) The shared per-synapse scale gives an EPSP 3-10× below the measured soma potential. (2) Even 4.71 mV at the soma is subthreshold in a point neuron. In the fly the synapse sits on the axon near spike initiation and the soma sees an attenuated copy, so a point neuron cannot carry this relay (outside its N30 validity range: single-site input near the SIZ). Possible remedies are a measured unitary EPSP for this identified pair, or two compartments (N30). Either is a value rather than a free knob only if it comes from a recording.
- **Also.** Part of the PSI-DLMn contact runs in the nerve, where male-cns may not reconstruct it, so the 406 + 43 synapses may undercount (inferred). The per-type point delays also count the PSI path in series with the DLMn axon, as the 22:35 entry warned.
- **Next (not done).** Ask Ben whether a measured soma EPSP per identified pair is an acceptable value (it would override the shared scale for one connection), or whether this waits for N30. Nothing adopted.

### F-VISION-12: on v0r + the flyvis per-type rows, T4/T5 are not direction selective in either flyapp set (0 of 8, as pre-registered); medulla inputs now respond with the right polarity, but T4 sums them without a direction preference and the lamina passes almost nothing (s13 fly2, 13 Oct 22:48)
- **Test** (pre-registration DECISIONS 13 Oct 22:05; held out, run once). flyapp `app/tools/t4t5_ds.py` at app commit 80bc01c, seed 0, both sets, m9c + the 7 v0r switches + `cell_type:all|optic_lobe_flyvis=1` + `candidates_s13_v0r.csv`, model from fly2 commit 18d6f8f. Output `runs/s13/fly2/t4t5/v0rfv/ds.{json,png}`; sheet `docs/media/s13_fly2_t4t5_v0rfv.png`, viewed.
- **Verdict: FAIL in both sets, 0 of 8 subtypes**, as predicted; the falsifier (all 8 selective) did not fire. Medulla bars: T4a-d rise 0.63-0.79 mV to every direction (DSI −0.02 to +0.01, "not selective"); T5a-d 0.24-0.42 mV ("no response"). Photoreceptor bars: T4/T5 0.04-0.29 mV, DSI −0.09 to +0.04 (T4a −0.09 is the wrong sign for flies).
- **Where the signal is.** Medulla bars: ON cells Mi1 +2.05, Tm3 +2.90, Mi4 +3.59, C3 +2.87 mV; Mi9 −3.34 to ON; OFF cells Tm1 +2.14, Tm2 +2.05 to OFF. So the inputs have the recorded polarity and Mi4/Mi9 now carry signal (on v0r with motion_grating they did not, F-VISION-11; a different stimulus, so not a like-for-like attribution). Photoreceptor bars: R1-R6 swing about 1-2 mV but L1-L5 only 0.04-0.35 mV and the medulla 0.1-0.4, so little reaches T4/T5 (the F-VISION-8/9 lamina gap, still open on this base).
- **Measured reason** (before the call, `runs/vision/flyvis_ablate_ds_{0-4,5-9}.csv`). In the 50 flyvis networks themselves, DS needs their per-type-pair synapse strengths: median DSI 0.40 medulla / 0.49 photoreceptor as published, 0.32 / 0.32 with tau set to 20 ms, 0.02 / 0.06 with per-type product strengths. The import carries per-type mode, tau and release at rest only, so the connectome synapse counts times one shared scale set the T4 input balance. Here that gives a direction-blind sum. CT1 was also saturated at −11 mV in the flash run.
- **Reading.** Task 1 is done with a measured reason, not a pass. The next step would be flyvis per-type-pair strengths (fitted, 604 type-pair edges in `flyvis_lappalainen2024_edges.csv`). Each is a fitted value per connection class: shared by type pair, not per synapse, but fitted to a task, not to physiology. Whether that passes the bar is for Ben. Spent: the flyapp T4/T5 call on v0r + flyvis. Nothing adopted.

### F-BYPASS-4: S3 fails. Graded release or Shiu's synapse strength in the VNC doesn't make the leg MNs alternate. Our core already oscillates at Pugliese's frequency, but its output reaches the MNs at about one spike per cycle (s13, 13 Oct 23:10)
- **Test** (DECISIONS pre-registration 22:09, calibration note 22:18). `bypass_s2_descending.py` unchanged, DNg100 at 15/25/40 mV, brain off, in four arms:
  - A: 13B and 10B types graded (687 cells);
  - B: every VNC local type of unknown mode graded (13,128 cells);
  - C: VNC per-synapse efficacy ×1.754, Shiu's value;
  - D: A + C.
  - Viewed: rasters `docs/media/s13_bypass_s3_rasters.png`, frames `docs/media/s13_bypass_s3_frames.png`, oscillator cells `docs/media/s13_bypass_s3_chain.png` (T1L, 25 mV).
- **Verdict: FAIL** for all arms.

  | Arm | DNg100 | Leg MNs | Scorer | On viewing |
  |---|---|---|---|---|
  | A | 48-104 Hz | 4.4-5.1 Hz, act ≤ 0.12 | fail | Like S2: tonic tibia flexors, legs passive, wings open at 25-40 mV |
  | C | 48-102 Hz | 4.5-6.4 Hz, act ≤ 0.32 | fail | Same as A |
  | D | 48-78 Hz | up to 20 Hz at 40 mV, act ≤ 0.39 | fail | At 40 mV the abdomen curls and the wings rise; no alternation |
  | B | 3-22 Hz (suppressed) | 26-27 Hz, act 0.91 | "passes" (1-3 pools, r_ant −0.30 to −0.46) | Fail (see below) |

  B is a false positive. DNg100 is suppressed, so it isn't driving anything. MN activity is the same after the drive stops (3.7 against 3.6 pool spikes/ms), which makes it a VNC-wide runaway. In the oscillator cells, graded V swings between −120 and −10 mV with no reversal potential to bound it (current-based synapses). The frames show a whole-body convulsion (abdomen curled, wings vertical, legs held extended), and the raster shows dense irregular activity in every leg, not alternation. Lagged readout (secondary): no pairs except B (1-3 pairs, part of the same runaway).
- **Chain (25 mV, T1L)** in m10f0, A, C and D:
  - E1 integrates to threshold and fires; E2 and IN19A007 follow within milliseconds; IN19A007's GABA resets E1. That gives a cycle of about 11-12 Hz with one spike per cell per cycle.
  - I1 gets a 2-4 mV EPSP per cycle and peaks at −45.4 mV (C). It fires once in all of D (T2L).
  - IN19A007 is Pugliese's own I2 in the male CNS (their Extended Data Fig. 3 male-CNS mini-circuit is DNg100, E1, E2, E3 IN19B012, I1, I2 IN19A007). Our cycle is therefore a version of theirs, without I1.
- **The core's output reaches the right MNs, too weakly.**
  - In S2 DNg100 25 mV, the left-front coxa promotor pool rises from 0 to 3.1 Hz, and both it and the trochanter flexor pool show a pooled spectral peak at 12.2 Hz (11 spikes in 0.9 s across each pool).
  - Pugliese's model recruits the same MN types: coxa swing promotors, stance remotor, trochanter flexors.
  - So the rhythm gets through, at about one spike per cycle per pool. No muscle can follow that, and the antagonist (remotor) stays silent.
  - The rest of the "tonic" output is the tibia flexor pools in every leg, firing regularly from before the drive starts (a 23.3 Hz spectral line, independent of the drive).
- **Pugliese reference** (their code; Mac CPU, relaxed tolerances; DECISIONS 22:18). Their MNs also run at low rates: active MN peaks of 2-16 (their rate units), I1 peaking at 5.9, IN19A007 at 15.8. Swing and stance lag each other by 12-17 ms of an 83 ms cycle instead of alternating. So "alternating MN output" as we score it is not what the reference produces either. The GPU run at paper tolerances, with both DNg100s at I 250/400, is running on backhouse.
- **Sign audit.** Leg MNs: 318, receiving 980k input synapses (edges ≥ 5).
  - Premotor VNC-intrinsic input: 55% ACh (+), 26% GABA (−), 19% glutamate (−, because no leg MN type has a receptor-sign row).
  - The core loop's edges have the expected signs (E1→E2 +, I1→E1 −, IN19A007→E1 −) and counts that match the connectome. ID mapping verified (F-BYPASS-3).
  - Glutamate onto leg MNs is still inferred (Allen 2020 co-expression), not measured.
- **Localisation** (the pre-registered falsifier fired). Making the 13B/10B types graded (as literature reports) doesn't change the core, and neither does Shiu's VNC synapse strength. Making every VNC local graded destabilises the whole VNC, with or without drive. So neither mode assignment nor per-synapse scale is the break. The break sits between the oscillator and the MNs:
  - the core fires one spike per cycle, against bursts of 3 in Pugliese's MANC LIF;
  - premotor→MN gain is low;
  - the stance antagonist never gets the rhythm (I1 is the cell that would carry it).
  - The tonic tibia-flexor drive is a separate MN-layer issue.
- **What this does not show.** It says nothing about whether I1 is graded in a real fly (never recorded); only that making every unknown-mode cell graded is unstable in this model. Behavioural failure here is not evidence about internal physiology.
- **Addendum, 23:13: the GPU reference at the paper's tolerances** (Pugliese commit 10e7661, backhouse; outputs copied to `runs/s13/bypass/pugliese_ref/`; figure `docs/media/s13_pugliese_ref_mn.png`, viewed).
  - MANC, I 250: 3 of 144 MNs active, oscillation score 0.93 at 11.4 Hz, the same as the CPU smoke.
  - Male CNS, either DNg100 at I 250: nothing oscillates. DNg100 sits at 7 rate units; the only other core cell above zero is E1 at 0.1. I 250 is below threshold in the male CNS.
  - Male CNS, I 400:
    - DNg100 R: 7 MNs at 12.0 Hz, score 1.00. Their peaks are 2.7-16 units, and every pool is modulated from near 0 to its peak on every cycle.
    - DNg100 L: 4 MNs at 10.4 Hz. The stance remotor peaks about 25 ms before the swing promotors, and one pair, promotor against remotor, reaches r −0.31 at zero lag. That just passes our −0.3 bar. The R run has 0 pairs.
  - Core cells reaching 3-16 units: E1, E2, I1 (3.1-7.8) and IN19A007 (2-16). I1 is active in every oscillating run, as it is in Pugliese's paper.
  - **Reading:** with this model class on this connectome, a stimulated core does give a deep, cycle-locked MN rhythm with a swing-stance phase offset. Our MNs get roughly one spike per cycle per pool. That gap is the target for the next step. In the rate model, any input above a size-normalised threshold gives I1 a graded rate (inferred to be why it is recruited); our LIF I1 needs a 7 mV crossing before it does anything. Whether a real I1 is graded remains unmeasured.

### F-BYPASS-5: at the same synapse counts, our MNs need 14-25× more presynaptic input than Pugliese's to reach threshold and have 0.17-0.22× the gain above it; the core's one spike per cycle cannot cross that gap (s13, 13 Oct 23:31; derived, no model change)
- **Method.** This is a code and single-cell analysis, not a network run. Ours is m10f0 as built by the bypass probes. Theirs is `/tmp/pugliese_cpg` at 10e7661, with the male-CNS extract (`rate_equation_half_tanh`, `set_sizes`, `configs/neuron_params/default.yaml`). Left T1. Synapse counts are identical in both builds.
- **Equations.**
  - Ours: w = sign × 0.15675 mV × n × input_gain; τs 5 ms; τm 20 ms; gap 7 mV. One spike peaks at 0.1575·w after 9.2 ms, and the mean depolarisation is w·r·τs.
  - Theirs: dR/dt = (max(200·tanh((a/200)(I + W·R − θ)), 0) − R)/τ, with W = 0.03·n, θ = 7.5·sz, a = 1/sz, τ 20 ms. sz is the cell's voxel volume over the network median.
- **Threshold in synapse·Hz** (ours = 8,932/g; theirs = 250·sz):

  | MN pool | Ours | Theirs | Ratio |
  |---|---|---|---|
  | Promotor 801173 | 11,750 | 857 | 13.7× |
  | Promotor 800061 | 16,120 | 1,060 | 15.2× |
  | Remotor 802509 | 11,320 | 783 | 14.5× |
  | Trochanter flexors | 6,100-7,600 | 333-385 | 18-20× |
  | Tibia flexor 807165 | 20,530 | 805 | 25.5× |

- **Gain above threshold:** ours/theirs 0.17-0.22. Spike-triggered Kv2/BK/SK set our f-I slope at 3.3 Hz/mV; leak only would give 6.1.
- **Per spike** (peak PSP from one E2 spike, against the 7 mV gap):

  | Promotor 801173 | Other promotor, remotor, TrF | Tibia flexor |
  |---|---|---|
  | 3.47 mV | 0.86-1.62 mV | 0.06 mV |

  Into 801173, an E2 burst of 1 or 2 spikes gives 0 MN spikes (peak −45.3 mV at 2). A burst of 3-5 gives 1 spike, and 10 give 2-3. For 801173 to reach threshold in steady state, E2 must fire at about 65 Hz in ours, against R 4.8 in theirs.
- **Synapses:** I1 makes no synapse onto any of these pools in either build. The core reaches the MNs through E2 (+) and IN19A007 (−).
- **Size:** our non-slow MNs share one set of membrane values. Input gain varies only within type (0.36-2.96, the m7 size law). Theirs scale threshold and gain with absolute size (0.68-4.24× the median).
- **Azevedo 2020** (read by a Sonnet agent, 13 Oct). Rin is fast 150 MΩ (n 15), intermediate 300 (11), slow 700 (14), measured. Fast and intermediate MNs have no f-I curve: current injection "failed to reliably trigger action potentials". The slow-MN f-I curve is spent (F-AZ-2/3, F-RUNG1-2). The recruitment order (slow, then intermediate, then fast) is measured and has never been fitted.
- **Reading.** The model differs at the oscillator→MN step mainly in scale and in the core's output (one spike per cycle). Neither has a measured value for VNC cells. The one measured quantity that bears on the step is MN Rin by class, and it redistributes gain between types rather than setting the scale. S4a (DECISIONS 23:31) tests Rin and the glutamate sign as shared arms before anything unmeasured is considered.

### F-REFLEX-2: with the brain off, leg proprioception does not reach the leg MNs (0 of 8 runs); at the default gain the signal stops at the first hop, and at a gain that drives the hook afferents to ~77 Hz the path it opens is net inhibitory onto the tibia extensors. F-REFLEX-1's tonic inhibitors are silent with the brain off, so they are not the block here. The CS load signal is saturated with the leg in air (s13 fly2, 14 Oct 00:07)
Step R of fly2's proprioceptive stance loop (pre-registration DECISIONS 13 Oct 23:58). `scripts/probes/proprio_reach.py`, scored by `proprio_reach_score.py`; runs `runs/s13/proprio/reach/` (8, scored) and `reach_loc/` (lm clamp at 8 and 40 mV again, with the localisation readout added after scoring). Figure `docs/media/s13_fly2_reach.png` (viewed). m10f0, seed 12, brain off, leg proprioceptors only, thorax tethered 1 mm up.
- **Gate (measured in the model): NO REACH in all 8 runs** (clamp lm/lf at 8 and 40 mV; CS load step lm at 8 and 40 mV). The one tibia pool that fires is the 11 slow lm flexors, tonic at 14-17 Hz with or without afferents (flexing/extending ratio 1.02 at 8 mV, 1.15 at 40). Every other lm and lf pool is silent in every arm, including the 2 tibia extensors. The largest ratio, lf coxa posterior rotator at 40 mV, is a 0.5 Hz change.
- **Afferents fire, measured in the model:**
  - 8 mV (profile default, guessed): hook 16 Hz per cell, phase-locked and direction-correct. Claw 1.3-1.6 Hz on lm, 9-11 on lf. Club 0. CS 22 Hz.
  - 40 mV: hook 76-78 Hz, claw 10-11 Hz (lm) and 50 Hz (lf), club 44-46 Hz, CS 89-100 Hz.
  - Physiological bound: no adult Drosophila FeCO or CS spike rate exists (Mamiya 2018 and Chen 2021 are calcium only). The only Drosophila chordotonal spike rates are larval lch5, 1.5-78.4 Hz (Warren & Göpfert 2024, *J Exp Biol* 227:jeb246197, primary). The 40 mV hook rates sit at the top of that range, so 40 mV counts as physiological, at its edge. Locust CS up to 650 Hz is secondary only.
- **Where it stops, lm clamp (localisation readout, measured in the model):**
  - **8 mV:** 3 of 178 first-order targets (≥ 20 synapses from the lm claw/hook afferents) fire, all inhibitory IN14A, 8-16 Hz in extension. Premotor cells of the extensor pool: 0 of 172 active. Of the flexor pool: 1 of 177, unmodulated. The extensor MNs sit at their resting gap, 7.0 mV below threshold, unchanged. **The signal stops at the first hop.**
  - **40 mV:** 32 first-order targets are active and 22 modulated, almost all inhibitory (IN14A085/038/086, IN09A021/024/027, IN19A005, IN13A006, IN26X001). Premotor active: 5 of 172 (extensor pool), 8 of 177 (flexor pool). The excitatory ones that fire are IN21A022 (28 Hz in extension), IN19A012 and IN21A004. The extensor MNs move further from threshold: 6.9 → 8-11 mV, in both phases. **The path the FeCO opens is net inhibitory onto the extensors and too weak onto the flexors.** IN19A005 and IN13A006 (F-REFLEX-1's inhibitors) are among the cells the FeCO itself recruits, phase-modulated.
- **F-REFLEX-1's tonic inhibition is absent with the brain off:** IN13A006, IN13A014, IN08A005, IN19A005, IN21A002 and DNg105 are all 0 Hz at 8 mV and in the zero-afferent controls. F-REFLEX-1 (m7, brain on) had them tonic, so that inhibition was brain-driven or state-driven. The pre-registered prediction (no reach at 8 mV) was right, but its stated reason (tonic VNC inhibition) was wrong.
- **CS transduction is saturated (derived):** `tanh` of the transmitted segment load reads 0.936-0.94 on the lm CS with the leg hanging in air (gravity on the leg segments alone). A load step can move it only 0.94 → 1, so the load test tests nothing, and the CS channel cannot encode stance load. Each leg also has only 2-3 CS rows assigned (count, m10f0).
- **Reading (inferred):** the stance loop cannot close through the connectome in m10f0, for two reasons.
  1. **Transmission.** The afferent → interneuron → MN chain loses the signal by the first or second hop. This is the same gap as F-BYPASS-5 (our MNs need 14-25× more presynaptic input than Pugliese's) and fly's S4a/S4b question (MN input scale, glutamate sign onto MNs). Many of the recruited first-order cells are hemilineages whose sign depends on the glutamate rule (14A, 21A; F-REFLEX-1's open item).
  2. **Transduction.** The CS load channel is saturated, and the front-leg FeCO is under-assigned (4 claw + 4 hook on lf).

  Per the brief, fly2 stops the stance loop here. No gain was tuned to force a reach. Rerun step R (one command per arm, about 3 min each) on whichever S4a/S4b arm fly adopts. That is the test of whether fly's MN-level fix opens the reflex path.
- **Afferent delay (for when the loop is built), from the literature search (Sonnet, quotes checked by the agent in the primary text, not by me):** about 3 ms from a peripheral femur bristle afferent spike to the EPSP onset in a VNC neuron. Drosophila, in vivo whole-cell (Tuthill & Wilson 2016, *Cell* 164:1046, doi:10.1016/j.cell.2016.01.029). That is an exteroceptive afferent on the same leg nerve, so for FeCO/CS it is **inferred**. Locust FeCO afferent → flexor tibiae MN central latency is about 1.5 ms (Burrows 1987, *J Neurosci* 7:1064). No Drosophila FeCO/CS latency was found.

### F-BYPASS-6: S4a fails on every arm. Neither between-type MN input resistance (R) nor excitatory glutamate onto leg MNs (G) gets the core's rhythm into the MNs (s13, 13 Oct 23:57; DIAGNOSTIC, forced drive; no adoption)
- **Runs:** R, G and RG × DNg100 15/25/40 mV, as pre-registered (DECISIONS 23:31), on backhouse (`~/fly-m10f/runs/s13/bypass/s4a/`, Mac copy `runs/s13/bypass/s4a/`). All 9 exited 0. GPU check of the R+G build (`gpu_bench.py equiv --stim broad --ms 300`): reference member bit-exact over 3000 steps (33,399 spikes each); the class-gain member differs on 34 steps from step 2337, with equal spike totals (float32 order).
- **Transfer pass (`bypass_moddepth.py`):** 0 pools in all 9 runs (baseline 0/0/1). Best drive-dependent pools: G 40 mV, rh coxa-trochanter +1, depth 0.42 (3.6 spikes per cycle, floor on 0.88 of cycles), and lf promotor, depth 0.33. Both are below the 0.5 bar. Lag readout: no lagged pairs (G 40: 3 rhythmic pools; RG 40: 1; R 40: 0). No antagonist pair, so S4a fails and the post-drive check doesn't arise.
- **Viewed** (`docs/media/s13_bypass_s4a_rasters.png`, `..._s4a_frames.png`): the synchronous tonic tibia-flexor pulses from before the drive dominate every arm. G adds sparse, scattered MN spikes after drive onset, with no bursts. R thins MN output; R at 15 mV leaves no drive-dependent pool at all, because the promotor and remotor gains fall to 0.42-0.46. Legs hang without stepping in every arm. The wings open at 25-40 mV, as in S2.
- **Predictions:** G, "more MN drive, tonic not rhythmic": confirmed (leg MN 6.2 Hz at 40 mV, against 4.7 in R). R: the promotor and remotor loss was right; the trochanter-flexor gain was wrong before the run (0.88, not ~2×).
- **Held-out recruitment order: not computed, not spent.** The harness saves pool rates, not per-MN spikes, and no arm passed the primary criterion. It stays held out for S4b.
- **Reading (the falsifier, as registered):** per-type MN properties and the glutamate sign are not the break. What remains is the premotor→MN scale (14-25×, F-BYPASS-5) and the core's single-spike output; neither has a measured value. S4b (Director decision, as Ben, 13 Oct) fits the scale only, as a bounded shared quantity. Burstiness stays unfitted.


### F-GJ-5: PSI→DLMn at the measured 4.71 mV still does not fire DLMn (0 of 20). A soma-measured EPSP of an axonal synapse cannot cross a point neuron's 7 mV gap, and the model's EPSP peaks about 10 ms after the GF spike, where the fly's DLM responds within about 1.5 ms (s14 fly2, 14 Oct 00:25)
- **Value.** `connectome:identified|unitary_psp_from_recordings` (neutral 0, CPU only), table `data/params/unitary_psp.csv`: PSI→DLMn a, b 4.71 mV, **measured** (Fayyazuddin et al. 2006 PLoS Biol 4:e63; whole-cell at the MN5 soma held at −74 mV, GF at 1 Hz, 4.71 ± 0.35 mV SEM, n = 10, from three methods: spike failure, inflection point, forced refractoriness; checked in PMC1382016 by a Sonnet subagent and by fly2). PSI→DLMn c-f 4.71 mV, **inferred** (same cell, no MN1-4 recording). Scan-gap fill: part of the contact lies in the PDMN outside the volume, and the synapse is axonal. Pre-registered DECISIONS 14 Oct 00:21.
- **Mechanism gate: pass.** After one GF spike every DLMn rises 4.78 mV (`runs/s13/fly2/gf_psi_dlm_path_psp.json`); the shared scale gives 0.6 mV (`docs/media/s14_fly2_psi_dlm.json`).
- **GF escape (Director's pass): FAIL, as predicted.** `gf_latency.py` m10f, 20 trials (`runs/s13/fly2/gf_latency_m10f_psp471.json`). Gaps on: TTMn and PSI follow 20/20 (TTM 1.099 ms, unchanged), DLMn a, b and c-f 0/20 (control 0). Gaps off: all 0/20. Viewed `docs/media/s14_fly2_psi_dlm.png`: DLMn a, b peaks at −47.2 mV about 10 ms after the GF spike, 2.2 mV below the −45 threshold.
- **Measured reason.** By construction, a 4.71 mV peak cannot cross the shared 7 mV rest-to-threshold gap (−52 to −45, guessed). The time course is also off: at the shared tau_m 20 ms and tau_s 5 ms the EPSP peaks 9 ms after it starts, while the fly's whole GF→DLM path takes 1.4-1.8 ms (Augustin 2017, spent). The recording's own methods say the EPSP *at the soma* is what the spike takes off from (inflection point), while the spike starts on the axon. So the soma value and the point neuron's threshold describe different places. This is outside the point neuron's validity range (N30: single-site input near the spike initiation zone).
- **Blanks this exposes (none filled, none tuned):**
  1. DLMn passive values. The same paper gives MN5 Rin 102 ± 12 MΩ and Cm 43 ± 2 pF (n = 22, in situ, whole-cell; measured), so tau_m = 4.4 ms (derived) against the shared 20 ms. That changes the timing, not the peak.
  2. MN5 rest and threshold are not in this paper. The cell was held at −74 mV to reduce spontaneous firing, so rest is above −74.
  3. A two-compartment MN (N30) with the PSI input at the axon.
- **Spent:** nothing new. DLM latency was already spent (F-GJ-3), and the 4.71 mV now sets a value, so it can no longer validate. Nothing adopted.

### F-VISION-13: the flyvis type-pair strengths, converted to our graded synapses, are a median 2.3× the shared scale's gain; 25 of 489 pairs exceed a 60 mV full-range ceiling and only R1-R6→LMC has a measured range to check against (s14 fly2, 14 Oct 00:41)
- **What.** `cell_type:all|optic_lobe_flyvis_pair_strength` (neutral 0, CPU only). The table `data/params/flyvis_pair_strength.csv` (`scripts/vision/flyvis_pair_rows.py`) holds 543 pairs: the ensemble median alpha with quartiles, mapped to male-cns types. R1..R6 are collapsed to the median over the collapsed pairs (derived). Mi3, Mi11, Mi12 and Tm28 are dropped (no male-cns type). The 26 CT1 compartment rows are held back (`use = 0`). In flyvis, a type-t cell gets sign × n_syn × alpha × relu(V_pre) from a type-s cell, so alpha is a voltage gain per synapse. `Network._flyvis_pair_weights` gives each edge from a graded cell the weight w = alpha·n·range·(1 − e^(−dt/τ_s)) / (g_k·(1 − r0)·rmax·dt), so the steady-state gain on the linear part of release equals alpha × n. Tested to 0.2% (current synapses) and 1% (conductance synapses, small signals at rest). Spiking presynaptic cells and edges with no flyvis pair keep the shared scale. Our sign is kept.
- **Check** (`scripts/vision/flyvis_pair_check.py` on m9c + v0r + optic_lobe_flyvis + `candidates_s13_v0r.csv`; `docs/media/s14_fly2_flyvis_pairs.{png,csv,json}`, figure viewed). 627,657 edges set, 0 from spiking cells. 489 of 517 read pairs have edges; the other 28 have none at this threshold. Per post cell, the summed flyvis gain is a median 2.3× the shared scale's (quartiles 1.0× and 4.4×). It spreads over 3e-4 to 5 mV/mV, where the shared scale sits at 0.02 to 0.5.
- **Against measured ranges.** The s14 literature pass (Sonnet subagent, primary text only) found one usable comparison: Drosophila photoreceptor and LMC peak responses (Zheng et al. 2006 J Gen Physiol 127:495: PR > 35-40 mV, LMC up to 45 mV, criterion > 15 mV). The derived saturating ratio of about 0.4 to 1.3 is a lower bound on the small-signal gain. flyvis gives R1-R6→L1 −0.78 and →L2 −0.41, both above 0.4. The shared scale with the v0r R1-R6 release candidate gives −14. No primary-text mV value was found for Mi1/Mi4/Mi9→T4, T4/T5→LPTC, L3→Tm9 or CT1 (paywalled). Those classes are **unchecked**, not passed. A remembered "T4 PSP 18 mV" figure from a search summary could not be found in the primary text and was discarded.
- **Flags, not clipped.** 25 pairs would move their most-driven post cell more than 60 mV if one presynaptic type swept its release range (linear extrapolation; guessed ceiling). Examples: R1-R6→T1 577 mV, L1→Tm3 382, Tm3→Mi14 202, R1-R6→L1 116 (the R1-R6 release range from recordings is wide). Conductance synapses saturate at the reversal potentials, so these are flags on the linear reading, not predicted voltages. Separately, 25 pairs carry a sign other than flyvis's: C2/C3→L1/L2, R8→Mi1/Mi4/Mi9/Mi15, Mi10→Lawf1/Mi9/T4a-d and others, T1→L2/L5, TmY14→C3/Mi13/Tm16. They come from our transmitter and receptor tables (e.g. C2 GluCl-dominated) and are kept.
- **Not done.** CT1 compartments: male-cns has 2 CT1 cells and our data assigns no columns, so flyvis's per-column CT1(M10)/CT1(Lo1) cannot be built yet. Needs a column assignment per cell (neuPrint optic-lobe column ROIs, or hex coordinates). Nothing adopted.

### F-VISION-14: CT1 built as 3,398 independent per-column compartments from male-cns column ROIs; the 24 flyvis CT1 pairs with edges are inside the size check and none is flagged (s14 fly2, 14 Oct 01:04)
- **Data.** Male-cns v1.0 ConnectsTo `roiInfo` gives synapse counts per optic-lobe column ROI (`<neuropil>_<side>_col_<hex1>_<hex2>`, Nern et al. 2025 hex grid; a Sonnet survey of neuPrint, and a direct query: CT1→LT33 288 synapses over 242 columns, summing to the weight). Raw pull `data/raw/ct1_columns_s14` (`scripts/vision/fetch_ct1_columns.py`, manifest with sha256; outside git, copied to backhouse and checked): 19,043 outgoing and 22,746 incoming CT1 connections. At ≥ 5 synapses, 98.2% of CT1's 375,873 synapses lie in ME or LO column ROIs, in layers ME 10 and LO 1-2. Lobula-plate columns hold 18.
- **Build.** `cell_type:CT1|compartments_by_column` (neutral 0; `connectome.ct1_compartments`): one graded compartment per (CT1 cell, M10 or Lo1, column), not coupled to each other. Each connection that passes the cell-level threshold is split by its column counts. The remainder stays on the original node (the trunk): synapses outside ME/LO column ROIs, and CT1→CT1. Compartments copy the CT1 row (type, transmitter, per-type parameters), get synthetic negative bodyIds and instance `<cell>/<M10|Lo1>/<column ROI>`, and take a size by synapse share (derived). On the working graph: 1,669 M10 and 1,729 Lo1 compartments, 167,111 → 170,509 cells, 6,241,231 → 6,301,014 edges. CT1 synapses in and out, all other synapses, total CT1 size and sign are unchanged. Basis: independent terminals are inferred from Meier & Borst 2019 (calcium imaging, abstract only) and flyvis's per-column CT1(M10)/CT1(Lo1). Validity: no spread between neighbouring terminals or between M10 and Lo1. A graph transform with no new dynamics, so both CPU and GPU paths simulate it unchanged; the flyvis pair arm itself stays CPU-only.
- **Pair rows.** The 26 flyvis CT1 rows now select compartments by an `instance:` selector (new in `lif._stp_cells`). With the compartment switch at 0 they match no cell; the other 517 rows' gains are identical (checked).
- **Size check with compartments** (`flyvis_pair_check.py --ct1`; `docs/media/s14_fly2_flyvis_pairs_ct1.{png,csv,json}`, figure viewed). 24 of the 26 CT1 pairs have edges. C3→CT1(M10) and CT1(M10)→C3 have none at 5 synapses. Gains per post cell: CT1→T4/T5 −0.12 to −0.62 mV/mV (shared scale −0.05 to −0.11); T4/T5/Mi1/Tm1/Tm9→CT1 +0.03 to +0.25. The largest full-range response is 8.9 mV (CT1(Lo1)→T5d), so none is flagged. No measured CT1 PSP range was found; **unchecked**, not passed.
- **Smoke** (m9c + v0r + optic_lobe_flyvis + pair strengths + compartments, `candidates_s13_v0r.csv`, 100 ms, Mac). It builds in 10 s with 3,400 CT1 rows, all graded and none spiking presynaptic. No NaN; at most 91 spikes per step. CT1 voltages run −57.7 to −41.4 mV (rest median −52.0). Tests: `tests/test_ct1_compartments.py` (3) and `test_flyvis_pairs.py`, `test_unitary_psp.py`, `test_model_data.py` pass. Nothing adopted.
- **Also found and fixed:** 9423fd6 had left `src/flyemu/gpu/batched.py` failing to compile (an indent in the refusal block); fixed in 609b238. The Mac battery skips `test_gpu_batched.py` without JAX. The running T4/T5 test does not import it.

### F-BYPASS-7: S4b is falsified. No premotor→leg-MN scale in 1-25 carries the core's rhythm as alternation, and the scales that match MN rates imply implausibly large unitary PSPs (s13, 14 Oct 00:21-00:33; DIAGNOSTIC, forced drive; no adoption)
- **Runs:** 10 scales × 3 drives on the backhouse GPU (`runs/s13/bypass/s4b/`).
  - GPU check exact: bit-identical gains, 957 = 957 spikes.
  - The s1/25 mV member equals the CPU harness exactly; so does s25/25 mV with the body.
- **Fit** (25 mV only; `s4b_score.py fit`, `fit.json`): **s\* = none.**
  - Intermediate and fast are silent at rest at every s.
  - Rates come within ×3 only at s 16-25 (intermediate 3.8-5.8 Hz, fast 2.3-4.4 Hz). Slow stays at the tonic 21-23 Hz tibia-flexor line at every s.
  - Transfer-pass pools rise from 0 to 14, but there is **no antagonist pair at any s**. The candidate pairs fire in phase (r0 +0.03 to +0.82).
- **Viewed:**
  - Rasters `docs/media/s13_bypass_s4b_rasters_25mv.png`: one co-active ~12 Hz volley per cycle, clear at s ≥ 12, which stops at drive-off.
  - Frames `docs/media/s13_bypass_s4b_frames.png`: the thorax is on the floor; at s 25 the legs splay without stepping.
- **PSP check:** `s4b_unitary_psp.py`; table in DECISIONS 14 Oct 00:33; literature `docs/research/s13_s4b_unitary_psp.md` (Sonnet, unchecked).
  - At s 1: 0.021 mV per synapse; a median connection gives 0.25 mV and a q90 connection 1.1 mV. Consistent with measured insect values, at the leaky end.
  - At s 16-25: 0.34-0.53 mV per synapse; a q90 connection gives 18-29 mV; one premotor spike fires 41-54% of sampled MNs. Not consistent: above the 0.1-0.3 mV per synapse of small high-Rin Drosophila central cells, and above every measured interneuron→MN PSP (≤ ~5 mV, locust; larval −2.8 mV).
- **Reading:**
  - The MN-side gain is not the break. A biologically sized scale gives near-silent MNs.
  - A rate-matching scale compensates for a premotor layer that is nearly silent: 0.13 Hz mean during drive, with the core giving one spike per cycle.
  - Alternation is absent at every gain, because the stance antagonists get no rhythmic inhibition (I1 silent, F-BYPASS-3/4).
  - The break is the core's burst output and I1's recruitment. Neither has a measured range yet (Ben's list: an E1/E2 burst recording; a unitary premotor→MN PSP).
- **Held-out recruitment order: still unspent.**

### F-XCONN-1: the male-CNS E2→I1 deficit is part of a prothoracic (T1) input deficit against MANC, not an E2→I1-specific gap; BANC sits between, nearer MANC (s13, 14 Oct 00:43; count audit, no simulation, no fitting)
- **Test** (pre-registered, DECISIONS 14 Oct 00:39). `scripts/probes/xconn_counts.py`. MANC counts from Pugliese's full-MANC matrix (`W_20260522_allSynapses`, rows pre; checked: their T1L minicircuit gives E2→I1 71, I1→E2 −172, and the full matrix matches). Matched through the dataset's `mancBodyid`, one-to-one only: 17,645 VNC-set cells; 4.16M MANC edges among them. BANC from Pugliese's T1 premotor extract (2026-02-17; it uses the male-CNS type names). FANC's extract labels interneurons by hemilineage only, so E2 and I1 can't be identified there; it is not used. Output `runs/s13/xconn/audit.json` (Mac, gitignored).
- **Core edges, synapses** (T1L / T1R; male CNS · MANC · BANC):
  - E2→I1: 38/27 · 71/60 · 50/53. In T2 the male CNS has 121/129 against MANC's 192/202; in T3, 65/65 against 72 (T3R).
  - E1→E2: 465/328 · 539/456 · 336/190. I1→E1: 526/439 · 531/580 · 379/357.
  - Relative to its own core (E2→I1 ÷ I1→E1): male CNS 0.07/0.06, MANC 0.13/0.10, BANC 0.13/0.15. So BANC sits with MANC, and the male CNS is about half.
- **Dataset-wide ratio.**
  - Pre-registered normaliser: the median male-CNS/MANC ratio over matched edges with ≥ 10 MANC synapses is 0.538 (562k edges). It is pulled down by matched edges absent in the male CNS.
  - On that normaliser, T1L E2→I1 is typical: normalised log ratio ≈ 0, inside the 5-95% band for 30-150-synapse edges (−3.2 to +1.0). **So the outlier call is "not an outlier".**
  - Secondary, not pre-registered: over edges present in both (≥ 10 each) the ratio is 0.875 (288k edges). On that, T1 E2→I1 (0.54, 0.45) is low.
- **Where the deficit sits** (per-cell matched-input ratio, male CNS/MANC, cells with ≥ 500 MANC matched inputs; median, 5-95%):
  - T1 0.58 (0.22-0.95; 3,002 cells); T2 0.69; T3 0.82; A1-A3 0.86-1.02.
  - **The whole male-CNS prothoracic neuromere has less matched input than MANC's, about 0.7× of T3's ratio.** That fits a reconstruction or synapse-detection difference across the T1 volume better than biology of one connection (inferred; counts can't prove it).
  - I1 sits low inside its neuromere: T1L 0.40 (20th percentile of T1 cells), T1R 0.33 (12th), T2 0.71/0.54, T3 0.81/0.84 (median).
- **I1 totals.**
  - Male-CNS I1 has 1,176 (T1L) and 836 (T1R) postsynapses against 2,110-2,509 in its own T2/T3 homologs. MANC's I1 is uniform across segments: 2,489-2,932 inputs from neurons.
  - 96% of the male-CNS T1L I1's postsynapses come from Traced bodies (T1R 95%). So the input it lacks isn't sitting on orphan fragments. It's absent: missing branches or undetected synapses.
  - Across I1's own inputs with ≥ 10 MANC synapses, the male-CNS T1 counts are 0.38× (T1L) and 0.34× (T1R) of MANC's. That is whole-cell, not E2-specific.
- **Proofreading status.** All 36 core interneurons (E1, E2, I1, A007, A004, A002 in six neuromeres) are Traced, with statusLabel "Reviewed". Both DNg100 are "Prelim Roughly traced". There is no per-connection proofreading flag in the dataset.
- **Reading** (as pre-registered):
  - The other animal (BANC) sits with MANC on the within-animal ratio. The male CNS alone is low, and it's low across its T1 neuromere and across all of I1's inputs.
  - So the deficit is male-CNS-specific. The neuromere-wide pattern makes **reconstruction** (T1 completeness or synapse detection) the more likely reading. **Individual variation** isn't excluded. Labelled inferred.
  - Under the per-value bar, the male-CNS T1 counts are not obviously "some fly's" values. They are plausibly an undercount. MANC and BANC would both be admissible.
  - The simulation half of X1 (does our model recruit I1 and alternate on MANC counts?) is running on backhouse; see HANDOFF.

### F-XCONN-2: on MANC's counts our model still doesn't recruit I1 or alternate. The male-CNS counts are not the break (s13, 14 Oct 02:21; DIAGNOSTIC, forced drive; no fitting, nothing adopted)
- **Runs** (pre-registered, DECISIONS 14 Oct 00:39; `xconn_swap.py`, backhouse, 18 runs, all exit 0).
  - Three arms: M0 (male CNS), Xc (MANC counts among the 36 core cells: 182 edges with 17,774 synapses → 199 edges with 20,652) and Xv (MANC counts among 17,645 matched VNC-set cells: 3.05M edges, 20.0M synapses → 4.16M edges, 25.1M).
  - Each × DNg100 15/25/40 mV, chain and MN harness.
  - The swap reached the model. T1L model weights went E2→I1 6.88 → 12.86 mV (×1.87 = 71/38), E1→I1 1.09 → 3.08, E1→E2 70.3 → 81.5, A007→E1 −50 → −59, A004→I1 −4.2 → −7.3.
  - A002→I1 in T1L stays −28.3 mV, because that A002 has no one-to-one MANC match. In the other neuromeres A002 was swapped, and I1 failed there too.
  - Outputs `runs/s13/xconn/{chain,s2,s2_score.json}` (Mac, gitignored).
- **I1 recruited (≥ 0.5 × the E1 cycle frequency, T1L): no, in any arm at any drive.**
  - T1L I1 Vmax against a −45 mV threshold: M0 −49.6/−48.4 mV (25/40 mV drive); Xc −48.4/−47.5; Xv −52.0/−48.5.
  - In all six neuromeres, the only I1 spikes are stray ones: T2R 1.4 Hz (Xc 25), T2L 1.4 Hz (Xv 25), T2R 2.9 Hz (Xv 40), each against E1 cycles of 4-22 Hz.
- **Alternation (S4b's admissibility pass, `s4b_score.rhythm`): fail in all 9 runs.**
  - 0 transfer-pass pools and no antagonist pair. Post-drive ÷ pre-drive 0.87-0.98.
  - The only active antagonist pair anywhere is Xv 40 mV, right-hind femur-tibia ±1, at r −0.21. It doesn't pass.
- **Viewed** (`docs/media/s13_xconn_rasters_{25,40}mv.png`; panels M0, Xc, Xv, then T1L oscillator V; titles say "no overrides" because the swap is outside the registry):
  - MN rasters: the three arms are indistinguishable. In each, the synchronous tonic pulse train from before the drive dominates, with sparse scattered spikes after onset and no alternation.
  - Oscillator: under M0 and Xc, E1, E2 and A007 fire once per cycle (Xc slower, 8.8 Hz against 12.3 Hz at 25 mV, with E1 hyperpolarised more deeply by the stronger A007→E1). I1 gets one 2-4 mV bump per cycle and never crosses threshold.
  - Under Xv at 25 mV the T1L core falls silent after about 400 ms: E2 and A007 stop, and E1 sits just below threshold.
- **Reading (as pre-registered: "neither"):**
  - Doubling E2→I1 to MANC's count doesn't recruit I1 in our model. Neither does swapping the whole matched VNC wiring.
  - So the male-CNS T1 undercount (F-XCONN-1) is real but is not what stops the circuit. The break is in our spiking model's handling of this circuit on either animal's wiring: single-spike core output, and an I1 that reaches −47.5 mV at best behind strong GABA input.
  - This matches F-BYPASS-3: Pugliese's own LIF, at 1.75× our per-synapse efficacy, gets I1 to only one spike per cycle on MANC.
  - It points at the questions on Ben's list: whether I1 spikes or passes graded signals (16B has never been recorded); unitary PSP size; E1/E2 burst output.
  - The prediction on record was right; if anything it erred toward success.

### F-XCONN-3: an inferred T1 fill from MANC and BANC closes only part of the male-CNS T1 deficit and changes no motor result (fly2, s20, 20 Oct 22:30; inferred, development mode; switch neutral, nothing adopted)
- **What was built** (rule pre-registered DECISIONS 20 Oct 22:02; unit amended 22:08 from the count audit, before any run):
  - Switch `connectome:T1|fill_from_other_animals` (neutral 0, label inferred, cross-animal), `connectome.t1_fill`.
  - Table `data/params/t1_fill.csv.gz` from `scripts/connectome/t1_fill_table.py`, sources pinned by sha256 in `t1_fill.json`.
  - Rule: per (presynaptic type, T1 postsynaptic type, side), synapses per connected cell pair. The target is the median over male CNS, MANC and (where its cell counts match) BANC. Kept male-CNS edges are scaled up to it only where MANC also has the pair and the male CNS sits below the target. No edge is added or removed, so no partner is invented.
  - Tests `tests/test_t1_fill.py`: neutral changes nothing, and only the T1 pair is scaled.
- **Count audit** (`scripts/connectome/t1_fill_audit.py`; `docs/media/s20_fly2_t1fill_audit.png`, viewed):
  - Kept edges onto T1: 73,741 of 216,006 scaled, 3.60M → 4.00M synapses (+11%).
  - Per-cell matched-input ratio against MANC: T1 0.578 → 0.669. T2 is 0.694 and T3 0.821. **Expected 0.8-0.95: missed.**
  - About a quarter of MANC's input lands on connections the male CNS lacks entirely, in every neuromere (T1 24.6%, T2 22.1%, T3 21.8%). A no-invention rule cannot fill that part.
  - I1 (IN16B036) inputs: T1L 1,125 → 1,225 and T1R 797 → 938. Expected 1,700-2,300: missed.
  - E2→I1: T1L 38 → 50 and T1R 27 → 53. Expected 50-60 / 40-55: met.
- **H1, bypass S2, DNg100 at 15/25/40 mV, brain off** (backhouse snapshot `~/fly2_t1` at 8524459; fill on vs off on the same code):
  - **FAIL in all 3 with the fill on, the same as off.** No alternating pool. The rhythmic pools went from 0/1/1 (off) to 0/0/0 (on).
  - Model weights moved as intended. T1L E2→I1 6.88 → 9.06 mV and T1R 4.84 → 9.5. T1L A007→E2 −8.5 → −13.9 and E2→E1 1.7 → 2.9.
  - **I1 not recruited** (chain harness, X1's settings): T1L Vmax −48.2 mV at 25 and 40 mV with the fill, against −49.6 and −48.4 without. Threshold is −45. T1R stays at rest.
  - The fill-off chain runs reproduce X1's M0 numbers exactly, so the snapshot matches.
  - Viewed `docs/media/s20_fly2_t1fill_rasters_{25,40}mv.png`. The MN rasters are the same synchronous tonic pulse train. In T1L the core cycles faster with the fill (E1 15.7 vs 12.9 Hz at 25 mV), and I1's bump per cycle grows by about 1 mV but stays under threshold.
- **H2, step R reach gate, 8 runs:** **NO REACH, 0 of 8 with the fill on**, as predicted (`runs/s20/t1fill/reach_on`).
  - The fill-off rerun on the same snapshot (`reach_off`) is also 0 of 8. The MN pool rates are identical on and off in all 8 arms, to 0.01 Hz.
  - In the lf arms the fill moves the tibia MNs' subthreshold gap to threshold by 0.2 mV at most.
  - The lf arms (the T1 leg, inside the fill) match F-REFLEX-2. The tibia flexors are tonic at 17-19 Hz with a ratio of 1.00-1.03, the same with the afferents zeroed.
  - Viewed `docs/media/s20_fly2_t1fill_reach_on.png` (the lm leg, the panel layout of F-REFLEX-2's figure). The afferents fire, the premotor hop is nearly silent (at most 8 of 177 flexor-premotor cells active at 40 mV), and the tibia MNs sit 6-12 mV below threshold.
- **Reading:**
  - The pre-registered falsifier holds: H1 and H2 are unchanged. So the male-CNS T1 undercount, at the size a no-invention fill can repair, is not what stops either motor test. This agrees with F-XCONN-2, where MANC counts across the whole VNC didn't help.
  - As a fly_brain.zip member, the fill is a labelled inferred table for a known reconstruction deficit (F-XCONN-1). It stays neutral: it moves T1 to the male CNS's own T2 level, not to MANC's.
  - The remaining gap is absent connections. Filling them would mean inventing partners from MANC by type, which this rule forbids and which would be a separate pre-registered step.

### F-XCONN-4: adding the T1 connections the male CNS lacks, where both MANC and BANC have them, adds 0.8% and changes no motor result (fly2, s20, 20 Oct 22:54; inferred, cross-connectome; level 2 of the fill switch, not adopted)
- **What was built** (Ben's rule via the Director; pre-registered DECISIONS 20 Oct 22:44, before code):
  - Level 2 of `connectome:T1|fill_from_other_animals` (level 1 is T1F, unchanged).
  - Table `data/params/t1_add.csv.gz` (`scripts/connectome/t1_fill_table.py add`, provenance `t1_add.json`): 25,218 (presynaptic type, T1 type, side) keys with no male-CNS synapse that both MANC and count-matched BANC have, out of 83,798 keys the two share.
  - Counts: the median of MANC and BANC for synapses per connected pair and for partners per post cell. Which A cells connect is guessed: same-side cells first, round-robin. The model's 5-synapse cut applies, so 1,986 keys add edges.
  - Test `tests/test_t1_fill.py::test_level2_adds_only_table_pairs_above_the_cut`.
- **Count audit** (`scripts/connectome/t1_add_audit.py`, `runs/s20/t1fill/audit_add.json`):
  - At the model cut: +3,115 edges and +30.6k synapses onto T1 (4.00M → 4.03M, +0.8%). At cut 1: +42,027 edges and +99.7k synapses.
  - The T1 matched-input ratio against MANC goes from 0.669 to 0.680. Predicted 0.67-0.72: met. Predicted under 10% added: met.
  - I1 input changes by +16 synapses at the cut; E2→I1 is unchanged.
  - Only 18% of the added edges (573 of 3,115) land on cell pairs that MANC's body-matched graph also connects. The guessed partner identity mostly picks other cells of the right types.
- **Reading of the audit:** MANC's input on connections absent from the male CNS (about 25% in every neuromere, F-XCONN-3) is mostly spread over weak type pairs. Where BANC confirms the type pair, the median counts are mostly under 5 synapses per pair, so the model cut drops them.
- **H1, bypass S2 at DNg100 15/25/40 mV, brain off** (Mac, this checkout; the level-0 runs at 25 mV reproduce backhouse's T1F snapshot exactly: I1 T1L −49.62 mV, E1 12.9 Hz, 1 rhythmic pool):
  - **FAIL in all 3**, as predicted. Rhythmic pools 0/0/0, as at level 1.
  - I1 T1L Vmax −48.17 mV at 25 mV and −47.81 at 40 (threshold −45): not recruited.
  - Viewed `docs/media/s20_fly2_t1add_rasters_40mv.png` (level 1 vs 2): the same synchronous tonic pulse train (MN 5.38 vs 5.34 Hz), and the T1L core cycles the same.
- **H2, step R, 8 arms: NO REACH, 0 of 8**, as predicted (`runs/s20/t1add/reach`). The tibia MN rates equal level 1 in every arm, including the T1 (lf) arms. Viewed `docs/media/s20_fly2_t1add_reach.png`.
- **Reading:** completeness only, as Ben expected. Level 2 is the most the cross-connectome rule allows without inventing type pairs. It moves T1 by about 0.01 and changes neither motor check. With F-XCONN-2 and F-XCONN-3, the T1 reconstruction deficit is ruled out as the cause of the missing VNC rhythm and reach at every size we can repair. The switch stays neutral as a labelled inferred member of fly_brain.zip.

### F-VISION-15: flyvis pair strengths do not make T4/T5 direction selective. Seed 1 (CT1 a point cell) gives 1 of 8 in the medulla set and seed 2 (CT1 per-column compartments) 0 of 8. Every T4/T5 response sits at the 0.5 mV floor with |DSI| ≤ 0.04 (fly2, s14/s20, 20 Oct 23:23; diagnostic, nothing adopted)
- **Arms** (pre-registered DECISIONS 14 Oct 00:41 and 01:05/01:07, before any run):
  - Setup common to both: m9c + the 7 v0r switches + `optic_lobe_flyvis=1` + `optic_lobe_flyvis_pair_strength=1` (F-VISION-13), with `candidates_s13_v0r.csv`. Tool: flyapp `t4t5_ds.py`.
  - Seed 1: both stimulus sets, CT1 a point cell. Seed 2: medulla set only, plus `cell_type:CT1|compartments_by_column=1` (F-VISION-14).
  - Different seeds, so the two are two draws, not a paired test of CT1.
- **Provenance of seed 1:**
  - The 16 Oct backhouse reboot truncated six protocols (control, med-off ±x ±y, med-on+x). They were re-recorded on 20 Oct, 22:44-23:21, about 1,090 s each, from the same snapshot (`~/fly2`, COMMIT 9423fd6, the commit carrying the 00:41 entry; no file changed after 14 Oct 00:41).
  - The decompressed static arrays of the 20 Oct and 14 Oct recordings are identical (md5 f00d685a…), and the tool reports every protocol paired with the control (identical before the first bar).
  - The 11 protocols recorded on 14 Oct were reused.
- **Seed 1, medulla set: FAIL, 1 of 8.**
  - T4a counts as "selective as in flies" only formally: DSI +0.04, Holm p 0.021. Its peaks are 0.51 mV in the fly's preferred direction (−x) and 0.48 mV against.
  - T4b and T4c are not selective (DSI 0.00). T4d and all four T5s are "no response": peaks 0.24-0.43 mV, under the tool's 0.5 mV floor, with |DSI| ≤ 0.03.
  - The ON input pathway responds (Mi1 0.80, Tm3 1.05, Mi4 2.48, C3 2.63 mV; Mi9 −1.96), and so does the OFF one (Tm1 2.18, Tm2 2.04 mV). T4 still sums them to 0.50 mV and T5 to 0.37 mV, the same in every direction.
  - **Photoreceptor set: FAIL, 0 of 8.** Peaks are 0.05-0.27 mV. L1-L5 carry 0.07-0.55 mV, the lamina gap of F-VISION-8/9/12.
- **Seed 2** (recovered 20 Oct, F-VISION-14 arm; HANDOFF): FAIL, 0 of 8. T4 peaks are 0.38-0.51 mV, T5 0.18-0.40, |DSI| ≤ 0.08.
- **Predictions:**
  - Seed 1 FAIL with some but fewer than 8 selective: met (1).
  - Seed 1 "|DSI| above F-VISION-12's ≤ 0.02": met only at the extremes. The largest is 0.04, but 6 of 8 subtypes are at ≤ 0.01, so DSI stays at the F-VISION-12 level.
  - Seed 1 photoreceptor set FAIL: met.
  - Seed 2 FAIL within ±2 of seed 1: met (0 vs 1).
  - The falsifier (8 of 8) did not fire on either seed.
- **Reading:**
  - With flyvis's task-trained type-pair strengths, our medulla carries direction-blind signals into T4/T5. Those signals are small (≤ 0.5 mV against the ON and OFF inputs' 1-2.6 mV). Adding CT1 column compartments doesn't change that.
  - In flyvis the same strengths give median DSI 0.40, so they are not enough on their own. What still differs is listed in the 00:41 reasons: conductance synapses with tonic release (shunting), and spatial offsets from the connectome rather than a hex lattice.
  - Next blanks, none tuned: the T4/T5 dendritic input (they are point cells here, while T4's direction selectivity in the fly relies on where on the dendrite its inputs sit, the N30 question in the optic lobe), and the per-type rest and release levels at the T4/T5 input synapses.
  - The pair-strength arm stays neutral and is not continued as is. The sealed Behnia 2014 temporal check is still unspent.
- **Figures** (viewed): `docs/media/s14_fly2_t4t5_v0rfvp_s1.png` (seed 1, both sets) and `docs/media/s14_fly2_t4t5_v0rfvpct1_s2.png` (seed 2). Data: `runs/s14/fly2/t4t5/v0rfvp_s1/ds.json`, `v0rfvpct1_s2/ds.json`.

### F-GJ-6: a two-compartment DLMn with the PSI input on its axon follows the GF 20/20 at a 2.20 ms muscle latency, inside the held-out Ryglewski 2014 range (PASS). The pass holds only for soma-axon coupling ρ < about 4, and the registered bracket spans that boundary. Each GF spike gives a DLMn doublet (fly2, s20, 21 Oct 00:01; pre-registered DECISIONS 20 Oct 23:30 and the 23:48 build note; seed 1; nothing adopted)
**Build.** N30 first build, `cell_type:all|two_compartments_where_point_fails` (neutral 0, CPU only; N30 now partial; `tests/test_two_compartment.py`, 8 tests).
- **Cells:** DLMn a, b (measured site) and DLMn c-f (inferred) get an axon compartment. The PSI inputs land on it and spikes start only there.
- **Class values (class MN, derived from guessed geometry):** q 0.07 and ρ 1.6, from `data/params/two_compartment_classes.csv`.
- **Calibration:** the PSI→DLMn weight is recalibrated so the passive pair's soma peak is the measured 4.71 mV.

**Runs.** Isolated CNS, m10f + `nt_from_physiology` + `unitary_psp_from_recordings` + the switch, seed 1. Outputs in `runs/s20/fly2/` (`gate_passive`, `gate_spiking`, `latency`, `corner_*`, `.json` and `.log`).

**1. Gate: PASS.** With the axon spike disabled, one GF spike gives a soma peak of 4.78 mV against 4.71 ± 0.5.
- The point model at seed 0 also gave 4.78, so the 0.07 mV excess is not from the compartment.
- The axon peaks at 13.8 mV, 3.1 ms after the kick. The same value comes from the pair's equations, a cross-check.
- With spiking on, the soma rises only 1.0-1.7 mV, because each axon reset pulls it back.

**2. GF escape, 20 trials.**

| Arm | Cells | Follow | Central latency | Median muscle latency |
|---|---|---|---|---|
| Gaps on | DLMn a, b | 20/20 (control 0) | 1.4 ms, every trial | **2.196 ms** |
| Gaps on | DLMn c-f | 20/20 | | 2.249 ms |
| Gaps on | TTMn, PSI | 20/20 | 0.3 ms | |
| Gaps off | all | 0/20 | | |

**Scored against the registration:**
- **(b) Ryglewski et al. 2014, 1.43-2.27 ms (held out): PASS.**
- (a) Augustin 2017, 1.36-1.849 ms (spent, consistency only): outside, as predicted.
- Prediction:
  - 20/20, 2.0-2.3 ms, FAIL (a), PASS (b), gaps off 0/20: **all met.**
  - Falsifiers (follow < 90%, latency < 1.9 ms): not triggered.

**3. Sensitivity, gaps on, reported and not scored.**

| q | ρ | DLMn a, b follow | Muscle latency | Spikes per GF |
|---|---|---|---|---|
| 0.012 | 0.13 | 20/20 | 1.896 ms | 4 |
| 0.15 | 0.13 | 20/20 | 2.096 ms | 3 |
| 0.012 | 25 | 0/20 | | |
| 0.15 | 25 | 0/20 | | |

The registered sensitivity prediction ("follows except at low ρ with high q") is **wrong**. Both tight-coupling corners fail: at ρ 25 the axon tracks the soma and the cell is a point neuron again (F-GJ-5).

**Derived boundary** (passive pair at tau_m 20 and tau_s 5): with the soma peak held at 4.71 mV, the axon peak crosses the 7 mV gap only for ρ < 3.6-4.2 at any q in the bracket. ρ decides following; q moves latency and spike count.

**Caveats** (stated, not corrected):
- **Latency margin.** 2.196 ms sits 0.07 ms under Ryglewski's upper bound. The model omits the stimulus-to-GF-spike time, which is inside the measured delay ("between giant fiber stimulation and muscle potential"). The TTM consistency check in F-GJ-3 used the same convention.
- **The ± reading.** Ryglewski's ± is undefined in the paper; reading it as SD was registered before the run.
- **Step quantisation.** Latency is quantised at the 0.1 ms step.
- **Doublet.** Every DLMn fires **2 spikes per GF spike** (3-4 at the low-ρ corners); the fly's DLM gives one. The 5 ms PSI→DLMn current outlasts the 2 ms axon refractory period. This is a blank (the axon refractory period, or the PSI→DLMn decay), not tuned.
- **Not evidence of physiology.** Behavioural success is not evidence that the internal values are right; q and ρ are guessed geometry.

**Spent:** Ryglewski 2014 GF→DLM latency, and seed 1 of this test.

**Viewed figure:** `docs/media/s20_fly2_two_comp_dlmn.png` (gate traces, spiking traces, latency per corner).

**What would pin q and ρ:** `docs/research/s20_n30_pin_q_rho.md`. In short:
- (B) the MN5 EM geometry (axon radius and path to the PSI contacts) gives q and narrows ρ to Ri's 3× range;
- (C) one MN5 soma recording (a two-exponential step response or capacitive transient) gives both, measured;
- (A) the soma amplitude of the "small and broad" axon spike in Fayyazuddin 2006 is a quick read of ρ < 4.

**Not adopted.** That needs a battery run, and the doublet and the tau_m blank should be addressed first.

### F-GJ-7: the male-CNS MN5 skeletons put class MN at q 0.104 and ρ 3.80, on the follow boundary (ρ* 3.78; UNDECIDED). At these derived values DLMn fires once per GF spike but late (3.2 ms), or not at all. The doublet at the guessed values is the synaptic tail, not soma-axon ping-pong (fly2, s21, 21 Oct 00:21; pre-registered DECISIONS 21 Oct 00:07; results entry 00:18; nothing adopted)
**What was derived.** Option B of `docs/research/s20_n30_pin_q_rho.md`: the coupling ρ and the axon membrane share q from the two DLMn a, b (MN5) skeletons in male-cns v1.0 and their PSI synapses (`scripts/connectome/mn_axon_geometry.py`).
- **Geometry:** derived from EM (skeleton radii and path lengths).
- **Rin:** 102 MΩ, measured (Fayyazuddin 2006).
- **Axial resistivity Ri:** 200 Ω·cm, range 102-311, fitted (Gouwens & Wilson 2009).

| MN5 | ℓ base → median contact | q | ρ at Ri 200 (102-311) | ρ* |
|---|---|---|---|---|
| L (801970) | 76 µm | 0.156 | 2.03 (1.31-3.98) | 3.51 |
| R (801295) | 23 µm | 0.052 | 5.57 (3.58-10.9) | 4.03 |
| Class mean | 49 µm | **0.104** | **3.80 (2.44-7.45)** | **3.78** |

- **Verdict: UNDECIDED.** The Ri range spans the boundary, and the two MN5s of one fly sit on opposite sides of it. Any shrinkage correction would push the class value to FAIL.
- **Table.** `two_compartment_classes.csv` class MN now holds these derived values, with brackets that span both cells and the Ri range. The switch stays neutral (off).
- **DLMn c-f.** Reported, not used. The base rule fails or is fragile in 3 of 8 cells, where the PSI contacts spread over several branches.

**Consistency runs** (seed 1, gaps on, 20 trials; not scored, because Ryglewski 2014 is spent):

| Values | DLMn a, b follow | Spikes per GF | Muscle latency |
|---|---|---|---|
| Class (0.104, 3.80) | 19/20 | 1 | 3.20 ms |
| MN5 L (0.156, 2.03) | 20/20 | 1 | 2.80 ms |
| MN5 R (0.052, 5.57) | 0/20 | 0 | |
| s20 guessed (0.07, 1.6) | 20/20 | 2 | 2.20 ms |

**Doublet mechanism** (`scripts/probes/n30_doublet_mechanism.py`, an exact replica of the pair update; figure `docs/media/s21_fly2_n30_doublet.png`, viewed):
- When the 2 ms refractory period ends, the axon's target potential is 11.5 mV from the PSI current and 0.11 mV from the soma, against a 7 mV threshold.
- Removing the soma-to-axon term keeps both spikes; cutting the synaptic current after the first spike leaves one. **The 5 ms synaptic tail causes it.** The reset to rest, with no afterhyperpolarisation, lets the tail act.
- Any one of these alone removes it at the s20 values:
  - a refractory period ≥ 3.0 ms;
  - an AHP ≥ 7.5 mV;
  - tau_s ≤ 1.8 ms;
  - tau_m 4.4 ms.

**Synaptic decay, from the replica** (corrected 00:25, DECISIONS 21 Oct 00:25).
- The measured adult nicotinic bracket is 1.1-6.73 ms (Gu & O'Dowd 2006 in situ: 4.45-6.73 ms), not the 1.1-4 ms first written here.
- At tau_m 20 and the class values, decays up to 3 ms give one spike within 0.5 ms, and 4 ms gives one at 0.9 ms. The shared 5 ms and 6.73 ms give none. At tau_m 12.3 (Herrera-Valdez 2012 Rin × Cm), class values fire only for decays ≤ 3 ms.
- The bracket spans the flip, and no PSI→MN5 decay is published in readable text. So the MN5 recording decides, not a literature value.

**The MN5 tau_m of 4.4 ms is suspect.**
- It is Rin × 43 pF, but the skeleton membrane is about 25,000 µm² (about 250 pF). A second lab's Rin × Cm gives 12.3 ms (97 MΩ × 127 pF, n 52; Herrera-Valdez et al. 2012).
- Rin × that area gives Rm of about 25 kΩ·cm² (inside the fitted Drosophila range) and tau_m of about 25 ms.
- The blank stays open. It is not applied.

**Ben's measurement list.** `docs/MEASUREMENT_LIST.md` item 1, a single MN5 whole-cell recording, would measure q, ρ, tau_m, threshold, AHP and refractory period, and the PSI EPSP decay in one cell.

**Spent:** nothing new. The option-B runs reuse the spent Ryglewski 2014 seed 1 as consistency checks.

### F-S14-1: no class-level option alternates. Neither 16B graded release nor E1/E2 ADP, alone or together, inside measured bounds; the core's output can't cross the point-model hand-off to the leg MNs (s14, 21 Oct 01:16; DIAGNOSTIC, forced drive; pre-registered DECISIONS 20 Oct 22:28; nothing adopted)
**Primary.** 6 arms × DNg100 15/25/40 mV = 18 S2 runs, all exit 0. **0 pass:** every one has 0 transfer-pass pools and 0 antagonist pairs, and stops at drive-off (post/pre 0.90-0.98). M0 fails as required. Viewed:
- rasters: `docs/media/s14_arms_rasters_{15,25,40}mv.png`. No leg alternates. Every panel shows the tonic ~23 Hz tibia-flexor line (present before drive) plus co-active flecks, more of them at higher drive;
- frames: `docs/media/s14_arms_frames_all.png`. The thorax is on the floor with legs splayed and no stepping, in every arm at every drive. The wings open more with drive (from 700 ms at 25 mV, from 500 ms at 40) in M0 too, so that comes from DNg100, not an arm.
- **Falsifier hit for every arm:** neither class property, alone or with the other, inside these bounds, fixes the break.

**Secondary (chain runs, network only; `docs/media/s14_arms_chain_T1L.png`, viewed; spike times from the S arrays).**
- **The B arms don't make E1/E2 burst inside the network.** In M0, T1L E1 fires one spike per cycle, 81 ms apart (12.3 Hz at 25 mV). With B4 or B2 it fires 17-23 spikes in 700 ms at irregular 20-60 ms intervals, with no quiet gap between groups. That is a near-continuous 24-33 Hz train, not bursts, and the 12 Hz cycle is lost. The scorer's "3-5 spikes per cycle" (B4 25 mV: 3.2 at f0 7.5 Hz) is this train folded at a lower f0 the detector found. Isolated, the same ADP gives 4 spikes in 92 ms (calibration). In the network, IN19A007's inhibition and the E1/E2 loop chop it into single spikes. C4/C2 (with 16B graded) are in between: 7-14 spikes, at most 1.6 per group.
- **I1 is never recruited in T1L.** Spiking I1 Vmax is −47.6 to −52 mV against −45. The one listed "recruitment" (B2 40 mV, T2R) is an artefact of f0 dropping to 4.3 Hz (2 I1 spikes in 700 ms). Graded I1 (A, C4, C2) sits at most 1.54 mV above rest in any neuromere, with a T1L swing of 0.6-1.8 mV, below the pre-registered 2 mV release threshold.
- **More core spikes don't move the MNs.** Leg-MN rate during drive: M0 4.43/4.81/5.37 Hz (15/25/40 mV); B4 4.44/4.76/5.26; B2 4.49/4.72/5.17. The B arms add premotor spikes (mean premotor 0.13 → 0.28 Hz at 25 mV). The A arms lower MN output (4.2-4.3 Hz at every drive).

**Hand-off size** (`scripts/probes/s14_handoff.py`, `runs/s14/handoff.json`; connectome counts × the model's mV per synapse at scale 1, 0.0212 (q10-q90 0.0094-0.0349), derived in S4b; linear summation, so a lower bound):

| core role | leg-MN edges (MNs) | synapses median (max) | PSP per spike, median (max) mV | coincident spikes to threshold, median (min) |
|---|---|---|---|---|
| E1 (exc) | 28 (22) | 8 (78) | 0.17 (1.65) | 41 (4.2) |
| E2 (exc) | 92 (52) | 22 (275) | 0.47 (5.8) | 15 (1.2) |
| I1 (inh) | 15 (9) | 10 (44) | 0.21 (0.93) | — |
| IN19A007 (inh) | 86 (42) | 18 (298) | 0.38 (6.3) | — |

The leg-MN threshold gap is 7 mV. The core delivers about one spike per cycle, so most of its targets can't follow. Only E2's few heavy edges can fire an MN on a single spike, which is the "about one spike per cycle in a few pools" of F-BYPASS-4.

**Reading (inferred).** The break has two hand-offs of the same kind, both in point neurons at somatic-range PSPs:
- core → leg MN: confirmed as a bottleneck here. Extra core spikes, spread out, don't sum to MN output. A uniform scale (S4b) matches rates only at implausible somatic PSPs and still doesn't alternate.
- E2 → I1 inside the core: still unrecruited on either animal's counts (F-XCONN-2) and with graded release.

Insect leg MNs and interneurons are unipolar. Their premotor synapses sit on neuropil neurites near the spike-initiation zone, and the recorded soma is electrically remote. So a PSP measured at the soma can understate the depolarisation where spikes start. A point model can't hold both at once (the measured somatic PSP, and the local drive needed to cross threshold). That makes it the case Ben approved a two-compartment arm for. The next suspects named by the s14 falsifier (the slow-MN BK the E1/E2 cells inherited; MN transfer) stay open; the second is what the two-compartment arm tests.

**Measurement for Ben's list (the hand-off).** A somatic whole-cell recording from a front-leg MN, made in the same session as single-type premotor activation: optogenetic or a paired patch of E2 (INXXX466 = MANC IN15A001) or E1 (IN17A001). It would give:
- the unitary PSP at the soma, in mV per presynaptic spike;
- the MN's input resistance;
- ideally, the soma-to-neurite attenuation (dual-site recording or calcium/voltage imaging of the neurite).

The somatic PSP bounds the point model. With the attenuation, it fixes the two-compartment coupling.

### F-S15-1: fly2's option-B geometry rule doesn't define a spike-zone compartment for cells whose inputs cover the arbor (T1 leg MNs, oscillator core), so the s15 two-compartment arms don't run at option-B values (s15, 21 Oct 01:25; pre-registered DECISIONS 21 Oct 01:16 and 01:22; nothing adopted, no row written)
- **Method:** `scripts/connectome/premotor_mn_geometry.py` runs fly2's `mn_axon_geometry.reduce()` unchanged on 94 T1 leg MNs (tibia and coxa/trochanter types) and the 12 T1 core cells. The contacts are every postsynaptic site. Skeletons and synapses are from male-cns v1.0 and are kept as raw data.
- **Rule failures:** no qualifying branch point for 27/94 leg MNs and 4/12 core cells at FRAC 0.05 (similar at 0.01 and 0.20). The input site nearest the soma is close to the soma.
- **Where values come out**, they describe a twig, not the input arbor:

  | class | cells derived | q mean (q10-q90) | input sites distal to the base, median |
  |---|---|---|---|
  | leg_MN | 67 | 0.085 (0.002-0.18) | 2.1% |
  | core_premotor | 8 | 0.0024 | 0.1% |

  ρ at the stated Rin is reported, not used: leg_MN 1.30, core 3.10.
- **Reading:** the rule is built for one compact input zone on the axon (PSI → MN5). With distributed inputs it has no well-defined answer, so the class "can't be derived" (pre-registered stop).
- **Rin:** for leg MNs it is measured, 150/300/700 MΩ fast/intermediate/slow (Azevedo 2020 Fig. 3E). The same paper reports the soma as electrically isolated from the spike zone (soma current injection fails to fire fast and intermediate MNs; qualitative, measured). No adult VNC interneuron Rin was found.
- **Next:** s15b (pre-registered 01:25), a soma–arbor split along the primary neurite.

### F-S15-2: a soma–arbor split (two compartments at the derived class values) doesn't make the leg-MN pools alternate. 0/12 S2 tries pass; in the leg-MN arms the fitted tonic drive, left on the soma, reaches the spike zone at 0.24× and silences the tonic tibia flexors (s15b, 21 Oct 02:03; pre-registered DECISIONS 21 Oct 01:16, 01:22, 01:25; gate 01:34; DIAGNOSTIC, forced drive; nothing adopted)
- **Arms:** M0 (m10f0), TM (leg_MN q 0.725, ρ 1.38), TP (core_premotor q 0.933, ρ 1.58), TPM (both); every arm keeps the DLMn (MN) rows off. DNg100 15/25/40 mV, seed 12, S2 and chain harnesses.
- **Score:** 0 transfer-pass pairs and 0 antagonist pairs in all 12 S2 runs; activity stops at drive-off where it exists. Viewing agrees (`docs/media/s15b_arms_rasters_{15,25,40}mv.png`, `s15b_arms_frames_all.png`).

  | arm | leg MN before drive (Hz) | leg MN during drive, 15/25/40 mV (Hz) | premotor during drive, 25 mV (Hz) |
  |---|---|---|---|
  | M0 | 3.77 | 4.43 / 4.81 / 5.37 | 0.13 |
  | TM | 0 | 0.06 / 0.52 / 1.32 | 0.13 |
  | TP | 3.77 | 4.43 / 4.90 / 5.34 | 0.22 |
  | TPM | 0 | 0.06 / 0.71 / 1.35 | 0.22 |
- **Why TM silences the MNs:** `spontaneous_drive` (fitted, 35.55 mV for the slow tibia flexors; a stand-in for tonic premotor excitation) is a soma input in fly2's N30 mechanism, while every synaptic edge goes to the spike zone. At the leg_MN values a soma DC input reaches the spike zone at 0.24× (derived), 8.5 mV against the 26.2 mV gap. The registration didn't say where the tonic drive goes; this is an arm-design confound, not a hand-off effect.
- **Core:** TP/TPM at 40 mV turn T1L E1/E2 from ~20 Hz single spikes into ~3-spike bursts at ~6 Hz (`s15b_arms_chain_T1L_40mv.png`), a mode M0 already shows in T2. I1 is recruited only in T2R at 40 mV, never in T1.
- **Reading:** the hand-off gain from the split is about 1 (gate), and no arm alternates. With the tonic line gone (TM), the drive-locked MN activity is still co-active. The two-compartment reduction, at derived values, is not what's missing.
- **For s15c:** the morphological hybrid spreads the tonic drive by membrane area, which keeps the spike zone at the point cell's full tonic drive; gate 1(b) checks that.

### F-S15-3: the morphological walking cells pass gate 1. The custom cable solver matches NEURON to about 10⁻⁵, reduces exactly to the point cell as Ri → 0, and gives the T1 tibia flexors a somatic Rin of 582 MΩ, inside Azevedo's 150-700. The leg-MN skeletons contain no motor axon, so the registered spike-zone rule is undefined for leg MNs (s15c, 21 Oct 02:12; pre-registered DECISIONS 21 Oct 01:38 and addendum; locator note 02:10; nothing adopted)
- **Solver** (`src/flyemu/morph.py`, CPU reference): 106 cells, 434,567 nodes, backward Euler, factorised once. Against NEURON 9.0.2 on 6 cells: Rin within 2×10⁻⁵, PSP peaks within 3×10⁻⁵, traces within 8×10⁻⁶ mV.
- **Isopotential limit:** max 0.0065 mV off the point trace, or 0.047 mV for the slow flexors with a 35.55 mV tonic drive. The latter is the backward-Euler vs exponential-Euler difference (derived 0.041 mV), not the cable.
- **Rin, measured check:** tibia flexors (n 29) median 582 MΩ (369-959) at Rm 20 kΩ·cm² and Ri 200; Azevedo 2020 class means are 150/300/700. With radii ×0.8 or Günay's Rm/Cm, the median goes over 700.
- **Spike zone, leg MNs:** the male-CNS v1.0 skeletons end in LegNp(T1). No node is more than 94 µm from an input site, and there is no thick axon. The longest synapse-free terminal run is median 40 µm; 89/94 cells fall back, and 13/94 pick a twig at the soma. A choice (arbor base = s15b split, or the end of the trunk) must be written down before gate 2. The measurement that would settle it is the spike-initiation site in an adult leg MN.
- **Per-synapse gain preview:** 1 mV of point weight gives 0.11-0.20 mV at the soma and 0.13-0.19 mV at the spike zone, against 0.157 mV in the point cell. The passive morphology at the point model's synaptic charge changes the hand-off little (gate 2 will measure it).

### F-S15-4: a passive EM morphology doesn't change the core → leg-MN hand-off. Every edge's spike-zone gain is 1.01 (inhibitory/excitatory 0.997), so the stop rule applies and the morphology path is parked (s15c gate 2, 21 Oct 02:20; pre-registered DECISIONS 21 Oct 01:38, operational form and spike-zone decision 02:17; nothing adopted)
- **Method:** all 11,417 network edges onto the 106 T1 walking cells, each at its EM synapse sites, at the point model's synaptic charge. The cells are passive and linear, so one reciprocal cable run per recording node gives every edge (checked to 10⁻¹⁰).
- **Admissible:** 0.021 mV per synapse at the soma, and a q90 of 1.0-1.4 mV per spike (band ≤ 0.3 mV and 0.4-10 mV).
- **Gain vs the isopotential cell** at the arbor-base spike zone (the leg-MN primary site, Director 02:17):
  - core → leg MN 1.015, E2 → I1 0.974;
  - excitatory 1.016 vs inhibitory 1.012 onto leg MNs;
  - edge-to-edge q10-q90 0.94-1.10.
  - The trunk-end site, Ri 102-311 and radius ×0.8-1.25 all stay within 0.91-1.03.
- **Against the 7 mV gap:** E2 → I1 gives 0.75-1.07 mV per spike at the spike zone.
- **Meaning:** at these measured-range membrane values (Rin checked against Azevedo, F-S15-3), dendritic position doesn't re-weight inputs. Together with s14/S4b (uniform strength) and s15/s15b (two compartments), shape and transmission strength are ruled out as the single cause of the hand-off failure. Gate 3 and the hybrid network weren't built. Tools: `src/flyemu/morph.py` (`spike_zone` kinds `arbor_base`, `trunk_end`), `scripts/probes/s15c_gate2.py`.

### F-S16-1: an octopamine-high state, as a sustained depolarisation of the 33 Octβ-expressing premotor classes (+2 or +4 mV, plus +4 mV on the leg MNs), doesn't make the leg MNs alternate. 0/9 S2 tries pass. OA4 brings I1 into firing in most neuromeres for the first time, but the leg-MN pools stay co-active (s16, 21 Oct 03:12; pre-registered DECISIONS 21 Oct 02:28, operational form 02:35; DIAGNOSTIC, forced drive; nothing adopted)
- **Arms:** M0 (m10f0); OA2 / OA4 put +2 / +4 mV of `class:<c>|tonic_drive` on 33 vnc_local classes (11,294 cells); OA4M is OA4 plus +4 mV on MN_leg (11,676 cells). Values are in `data/params/octopamine_state.csv`: magnitude guessed, direction inferred. Bound check (`scripts/probes/s16_oa.py check`, both forms): 0 breaches in every arm, smallest gap to threshold 3.0 mV. DNg100 15/25/40 mV, seed 12, S2 and chain, plus a 0 mV brain-off S2 run per arm. 28 runs on backhouse, all exit 0.
- **Score** (`s14_score.py --arms M0,OA2,OA4,OA4M`, unchanged; `runs/s16/oa/score.json`): **0 antagonist pairs in all 12 S2 runs.** Transfer-pass pools 0, except one each in OA4 40 mV and OA4M 15 mV. Activity stops at drive-off (post/pre 0.91-0.99). M0 fails as required. Viewing agrees:
  - rasters `docs/media/s16_oa_rasters_{15,25,40}mv.png`: no leg alternates. The ~23 Hz tibia-flexor line is there before drive, and the co-active flecks get denser from M0 to OA4M;
  - frames `docs/media/s16_oa_frames_all.png`: thorax down, legs splayed, no stepping in any arm at any drive. The wings open with drive, and at a lower drive under OA: from 15 mV in OA2/OA4/OA4M, from 25 mV in M0. Wing motor output isn't scored here.

  | arm | premotor during drive, 15/25/40 mV (Hz) | leg MN before drive (Hz) | leg MN during drive, 15/25/40 mV (Hz) | MNs active, 25 mV | neuromeres with I1 spiking (any), 15/25/40 mV |
  |---|---|---|---|---|---|
  | M0 | 0.05 / 0.13 / 0.38 | 3.77 | 4.43 / 4.81 / 5.37 | 68 | 0 / 0 / 0 |
  | OA2 | 0.16 / 0.36 / 0.63 | 3.77 | 4.82 / 5.17 / 5.63 | 83 | 0 / 2 / 3 |
  | OA4 | 0.54 / 0.82 / 1.17 | 3.77 | 5.05 / 5.29 / 5.46 | 96 | 5 / 4 / 5 |
  | OA4M | 0.54 / 0.82 / 1.16 | 6.60 | 7.78 / 8.45 / 8.84 | 141 | 5 / 4 / 5 |
- **Secondary (chain; `docs/media/s16_oa_chain_T1L_{25,40}mv.png`, viewed):**
  - **I1 (IN16B036) spikes for the first time in any arm since s13.** Under OA4 it fires at 1.4-14.3 Hz (1-10 spikes in 700 ms) in most neuromeres; T1R never fires. The scorer's "recruited" (≥ 0.5 × the E1 cycle) holds in 0-5 of 6 neuromeres in OA4/OA4M (OA4 1/1/5, OA4M 0/3/4 at 15/25/40 mV). Most of those calls come where the core cycle has dropped to 4-7 Hz. That is the folding artefact noted in F-S14-1, so the count overstates real per-cycle recruitment; T2R at OA4M 25 mV (12.9 Hz against an 18.9 Hz cycle) is a clean case. In T1L, I1 sits at −46 to −48 mV and only touches threshold.
  - **The core loses its regular cycle as the shift grows.** T1L E1 at 40 mV: M0 one spike per cycle at 20 Hz. OA2/OA4: an irregular train that the detector folds at 4.3-4.6 Hz (4.4-4.7 "spikes per cycle"). E1 also shows deeper IPSPs, down to −80 mV in OA4, as IN19A007 fires more.
  - **Brain-off, no drive (0 mV; `s16_oa_rasters_0mv.png`, viewed):** premotor 0.0 Hz in every arm. Leg MNs carry only the tonic tibia-flexor line (3.77 Hz mean; 6.60 Hz in OA4M). No rhythm without DN drive in any arm: the model gives no analogue of Yellman's OA-induced walking in brain-off flies. This comparison is spent.
- **Prediction check:** no pass (right). OA4 recruits I1 in some legs (right, more widely than predicted). OA4M brings the tonic line back stronger (right: 6.6 vs 3.8 Hz). "Sparse tonic firing at OA4 with brain off" was wrong: premotor stays silent, since +4 mV leaves a 3 mV gap and nothing else drives it.
- **Reading:** raising premotor excitability raises premotor output about sixfold (0.13 → 0.82 Hz at 25 mV) and switches I1 on. The MN layer still gets only denser co-active flecks. Even a firing I1 reaches the leg MNs through 15 edges at a median 0.21 mV per spike (F-S14-1 hand-off table). So more core activity, including the missing stance inhibitor, still can't pattern the MNs through the point-model hand-off. The class-level state isn't the single missing piece. The falsifier is hit for every arm.
- **Held-out:** the S4b recruitment order is still unspent (no passing arm).

### F-S17-1: closing the leg proprioceptive loop through the tethered body and the connectome doesn't make the leg MNs alternate, under M0 or under the OA4 state where I1 fires. 0/24 S2 tries pass, with no antagonist pair in any run. The loop is self-limiting: the legs barely move, so the chordotonal afferents fire at only 0.3-12 Hz per cell, far below the 76-78 Hz a joint clamp gives at the same gain (s17, 21 Oct 03:55; pre-registered DECISIONS 21 Oct 03:18; DIAGNOSTIC, forced drive; nothing adopted)
- **Arms:** {M0, OA4} × afferent gain {g8, g40} × delay {d3, d1.5 ms} × DNg100 15/25/40 mV = 24 tries. `bypass_s2_descending.py --proprio` drives all leg proprioceptor rows of `sensory.Afferents` (claw, hook, club, CS, hair plates; six legs) from `body.observe()` each step, through a FIFO delay. Plus the open-loop repro (M0 25 mV, no `--proprio`) and feedback without drive (M0g40d3, OA4g40d3 at 0 mV). m10f0, seed 12, brain off, thorax tethered. 27 runs on backhouse, all exit 0 (`~/fly-m10f/runs/s17/loop/`; Mac copy `runs/s17/loop/`).
- **Repro control: pass.** The edited harness without `--proprio` equals `runs/s16/oa/s2/s2_M0_25mv.json` exactly (rates, MN counts, every pool; `s17_loop_summary.py`). The batch is valid.
- **Score** (`s14_score.py`, unchanged; `runs/s17/loop/score.json`): **0 antagonist pairs in all 24 runs.** Transfer-pass pools: 0, except one each in OA4g8d3 40 mV and OA4g40d3 40 mV (lh coxa-trochanter +1) and OA4g40d1p5 40 mV (rm pleural remotor). Open-loop OA4 40 mV had one as well (rh coxa-trochanter +1). Activity stops at drive-off in every run (post/pre 0.89-0.97), so feedback sustains nothing. Viewing agrees:
  - rasters `docs/media/s17_loop_rasters_{15,25,40}mv.png` (each: s16 open-loop M0, the four M0 loop arms, s16 open-loop OA4, the four OA4 loop arms): no leg alternates in any panel. The tonic tick line (39 ms period by autocorrelation here; earlier entries call it ~23 Hz) is there before drive, with co-active flecks after onset, denser under OA4, as in s16;
  - `docs/media/s17_loop_rasters_0mv.png`: no rhythm without drive in any arm;
  - frames `docs/media/s17_loop_frames.png` (8 runs: M0 open, M0g8/g40 at 25 mV, M0g40 at 40 mV, OA4g8/g40 at 25 mV, OA4g40 d3 and d1.5 at 40 mV): thorax low, legs splayed by 300 ms, wings opening from 500-700 ms, no stepping. Indistinguishable from the open-loop run.

  | arm (d3 / d1.5 pooled where equal) | premotor during drive, 15/25/40 mV (Hz) | leg MN during drive, 15/25/40 mV (Hz) | first-order targets active, 15/25/40 mV (of 1,730) | MNs active, 25 mV | neuromeres with I1 spiking, 15/25/40 mV |
  |---|---|---|---|---|---|
  | M0 open (s16) | 0.05 / 0.13 / 0.38 | 4.43 / 4.81 / 5.37 | not computed | 68 | 0 / 0 / 0 |
  | M0g8 | 0.05 / 0.14 / 0.37-0.40 | 4.43 / 4.81 / 5.32-5.38 | 20 / 30 / 91-94 | 68 | 0 / 0 / 0 |
  | M0g40 | 0.07 / 0.16 / 0.41-0.43 | 4.44 / 4.80-4.82 / 5.55-5.60 | 24-26 / 39-53 / 200 | 67-69 | 0 / 0 / 0 |
  | OA4 open (s16) | 0.54 / 0.82 / 1.17 | 5.05 / 5.29 / 5.46 | not computed | 96 | 5 / 4 / 5 |
  | OA4g8 | 0.51 / 0.86-0.88 / 1.10-1.18 | 5.05-5.16 / 5.33-5.36 / 5.47-5.63 | 186-191 / 223-244 / 246-247 | 97-101 | 5 / 4-5 / 5 |
  | OA4g40 | 0.62-0.68 / 0.90-0.94 / 1.19-1.24 | 5.07-5.22 / 5.48-5.59 / 5.78-5.85 | 349-367 / 352-371 / 427-442 | 103-111 | 4 / 4-5 / 3-5 |

  Under OA4 the first-order count also includes cells that the OA4 shift itself drives: the first-order set overlaps the 33 OA classes, and the open-loop runs have no first-order readout. So the OA4 rows overstate what feedback adds (inferred).
- **Afferent rates (measured in the model; bound inside, but never approached):**
  - The chordotonal mean per run is 0.3-0.7 Hz at g8 and 2.9-10.6 Hz at g40. The highest single subtype in any run is 11.8 Hz (hook_flex or club under OA4g40). Every run is inside the 78.4 Hz bound, so no pass would have been void.
  - The club (220 cells) and hook_flex (21) are silent under M0 and fire at about 10 Hz under OA4g40 during drive. OA4 sets only VNC-local classes, so this comes back through the body: OA4's motor output moves the legs differently (inferred).
  - CS reads 13-15 Hz at g8 and 58-74 Hz at g40. That is the saturated in-air channel of F-REFLEX-2, so load is not tested.
  - F-REFLEX-2's clamp gave hook 16 Hz at g8 and 76-78 Hz at g40. In the loop the legs move only as far as the weak MN output moves them (max joint-angle SD 6-12°), so the position and velocity afferents stay near rest. The loop can't bootstrap: closing it needs the movement that the missing hand-off would produce.
- **Feedback does one visible thing at the MN layer, before and without drive.** At g40 it breaks up the synchronous tonic tick line on lf, lm and rm. The fold peak-to-mean of each leg's summed pool rate over 0-300 ms falls from 8.6 (open loop) to 4.5 / 3.3 / 2.9 on lf / lm / rm. On lh, rf and rh it stays at 8.4 / 7.5 / 8.6. The leg MNs keep firing at the same rate (pre-drive 3.77 → 4.10 Hz), just less in unison. At g8 the effect is smaller (lm 5.6, rf 5.8). Why the hind legs are spared isn't checked (afferent assignment per leg, F-REFLEX-2, is the first suspect).
- **Delay:** d1.5 and d3 differ by at most 0.16 Hz in leg-MN rate and 0.08 Hz in premotor rate at any matched arm. The 1.5-3 ms band doesn't matter here.
- **Prediction check:**
  - No pass: right.
  - g8 matches open loop: right (leg MN 4.81 vs 4.81 Hz at 25 mV).
  - OA4g40 gives the most premotor activity and the first MN-layer change, co-active: right, though the change is small (+0.3-0.4 Hz at 25-40 mV).
  - The delay edges don't differ: right.
  - The 0 mV runs show only the tonic line: right, but the line is desynchronised at g40, which I didn't predict.
  - "The FeCO recruits mostly inhibitory first-order cells": not checked this time, since the harness doesn't save cell identities.
  - Not predicted: the afferents stay far below their clamp rates.
- **Reading (the falsifier, as registered):** closed-loop leg proprioception, at gains up to the one that puts a clamped hook afferent at the top of the measured chordotonal range, across the inferred delay band, with or without the state where I1 fires, doesn't restore alternation. It adds at most 0.4 Hz to the leg MNs and decorrelates the tonic line. Proprioception isn't the single missing piece. Two limits on that statement:
  1. The test covers the gain, not the rate. In the loop the afferents never got above 12 Hz.
  2. The replay half of S4 (imposing a walking-like joint trajectory under DNg100 and OA4, so the afferents fire at walking rates whatever the MN output) was not run. F-REFLEX-2's clamp did this with brain off, no drive and M0, and the signal stopped at the first hop.

  If Sapkal et al. 2026 holds (unchecked, `docs/research/s17_premotor_hemilineages.md`), the fly's own rhythm survives deafferentation, so a missing feedback loop isn't expected to be the cause anyway. Two candidates remain: connection-specific strength (measurement list item 4) and a premotor driver outside the 106-cell core (connectome query, next session).
- **Held-out:** the S4b recruitment order is still unspent (no passing arm).
### F-ZIP-1: the first fly_brain.zip (species layer, 134.7 MB, 467 members) runs a 1 s m10f0 smoke run that is spike-for-spike identical to the same run from the repo tree (fly2, s22, 21 Oct 00:52; registered in the Director's brief; DECISIONS 21 Oct 00:50)
**The zip.** `python -m flyemu.pack` at commit 1cbccff (clean tree), kept with the run outputs and job scripts in `runs/s22/fly2_zip/`.
- Size: 134,741,559 bytes zipped, 271.4 MB unpacked, 467 members. sha256 `f846617ce72e49f5…`.
- Unpacked size by group:
  - body 144.7 MB (flygym 2.1.0 vendored plus the 85 fullsize flybody meshes);
  - connectome 102.3 MB;
  - derived 7.1 MB;
  - annotations 6.8 MB;
  - params 5.0 MB;
  - model 2.9 MB;
  - inferred 1.4 MB;
  - code 0.7 MB;
  - profiles 0.3 MB;
  - tests 0.2 MB;
  - ledger, measurements, datasets, world and register under 0.1 MB each.
- The spec's 5 MB body estimate left out the fullsize meshes; the spec now says 145 MB.
- Dataset pins: the male-cns v1.0 neuron and edge hashes (they match the `t1_fill.json` pin), plus the MANC and BANC extract hashes.
- Runtime pins: Python 3.12.14, darwin arm64, numpy 2.5.3, MuJoCo 3.9.0 and six more packages.
- Declared `todo`: three arenas, nine stimuli, `variation/`, `individual/`, `flyemu.check` and slot addresses.

**The test.** m10f0, seed 12, ≥ 5 synapses, flat floor, no stimulus, 0.1 ms steps, 1000 ms.
- Run (a), from the zip: run in a fresh temp dir holding only the zip, with `PYTHONPATH=fly_brain.zip/code`. Every hash was verified, the zip was extracted there, and `--deny /Users/ben/fly-emulation` was set.
- Run (b), from the tree: `--tree .` in the fly2 worktree at the same commit.
- Both runs ran on the Mac through the slot limiter.

| | zip | tree |
|---|---|---|
| steps | 10,000 | 10,000 |
| spikes | 53,314 | 53,314 |
| spikes sha256 (step and neuron arrays) | 77080785… | 77080785… |
| final body qpos sha256 | 3ec293ba… | 3ec293ba… |
| registry reads (rows; whole table) | 1085 | 1085, equal |
| NaN, runaway, MuJoCo warnings | none | none |
| build / 1 s run wall time | 8.5 s / 121.5 s | 8.8 s / 117.8 s |

**PASS: identical spike for spike.** The spike arrays (step, neuron, bodyId), the final body pose and the whole registry-reads table are equal.
- **Sources in the zip run.** Profile from `profiles/m10f0.json`, arena from `world/arenas/flat_floor.json`. The flygym package, its assets and all 85 meshes came from the extracted root.
- **Read guard.** Nothing was denied. The only reads outside the root and the Python install were matplotlib's font cache (`~/.matplotlib/fontlist-v3.11.0.json`) and the system UTC zone file.
- **The test can fail.** The same zip run at seed 13 gives 52,597 spikes, a different spike hash and a different final pose.
- **Refusals work end to end.** `--set made_up|nonsense_key=1` from the zip exits with code 2 before any build ("no mechanism in mechanisms.yaml / parameters.csv / structural_keys.csv").
- **Unit tests.** `tests/test_flyzip.py` (5 pass) covers:
  - tampered, unlisted and escaping members;
  - non-empty roots;
  - deterministic packing;
  - the guard;
  - orphan `--set` keys.

**What this does and does not show.**
- It shows that the zip holds everything this run reads, and that nothing outside the zip changes the result.
- It does not show that every switch or profile runs from the zip. Only m10f0 at its defaults was run.
- It does not show portability to another machine or another runtime. The runtime pins are refused on mismatch unless `--allow-runtime-mismatch` is given.
- The guard sees Python opens, pyarrow parquet reads and MuJoCo mesh paths. A native read by another path would be missed; the identity result is the backstop for this run.
- The Python runtime (`/Users/ben/fly-emulation/.venv`) sits inside the denied repo directory but is allowed as `sys.prefix`. It holds no model data: the trace found none, and its only `.pth` is virtualenv's.

### F-ZIP-2: the scoreboard runs from the zip alone. Labellar sugar PER PASSES (MN9_L 5.7 Hz, bar > 5) and giant-fibre escape FAILS (no motor neuron follows); both are spike-for-spike identical zip vs tree and equal their reference scripts exactly. flyemu.check from the zip matches the tree (fly2, s22, 21 Oct 01:57; DECISIONS 21 Oct 01:10)

**What was built.**
- `flyemu.check`: runs the zip's tests, rebuilds the blank ledger from the zip's own tables, prints the fill fraction, and lists the scoreboard.
- `flyemu.score`: plays one protocol.
- `data/world/` (the zip's `world/`): the scoreboard, 2 protocols and 2 stimuli.
- Format and harnesses: DECISIONS 21 Oct 01:10, and `docs/FLY_BRAIN_ZIP.md`, "Check and scoreboard".

**The zip.** `runs/s22/fly2_zip/s2/fly_brain.zip`. It is a build artifact and is not in git (it is over 50 MB); the packer is committed.
- 134,765,680 bytes, 476 members, 271.5 MB unpacked.
- sha256 65892c89…, packed from clean commit c248318.
- The first pack at 089022c (sha256 c32b7d3a…, 134,765,506 bytes) differs only in `tests/test_repo_hygiene.py`; see the check below.

**Identity runs.** Each zip run was made from a scratch directory, with `/Users/ben/fly-emulation` denied and only the zip's code on the path.

| | reference script | tree | zip |
|---|---|---|---|
| `per_labellar_sugar`, MN9_L Hz, seeds 0-9 | 7 6 7 5 7 7 5 6 4 3 | the same | the same |
| its spikes over all 167,111 neurons, per seed | (not hashed) | 7040 … 7096 | equal hashes, all 10 seeds |
| `gf_escape`: GF spikes / TTMn, PSI, DLMn follow | 20 of 20 / 0, 0, 0 | the same | the same; equal spike hash (1720 spikes) |

- **Reference scripts.** `assay_pathways.py --assay sugar_mn9 --rates 100 --shuffles 0 --trials 10` and `gf_latency.py --arms gaps_off --trials 20 --seed 0`, both at m10f0. Every compared field is exactly equal: the per-seed rate, and for GF every type's follow, control, median and spike fields.
- **Labellar sugar PER: PASS.** MN9_L mean 5.7 Hz against a bar of > 5 Hz. The margin is thin: 3 of 10 seeds are at or below 5 Hz (seed 9: 3 Hz).
- **Giant-fibre escape: FAIL.**
  - The giant fibre spikes on every kick, but none of TTMn, PSI or DLMn spikes within 10 ms; the controls are silent too.
  - This is the model default, with gap junctions off (`electrical:all|gap_conductance` 0, not adopted).
  - F-GJ-6 passed only with switches that are not adopted. This run agrees.
- **Read guard.**
  - Nothing was denied.
  - Outside the root and the Python install, the zip runs read only matplotlib's font cache and the system timezone file.
  - Tree runs read the connectome cache through the worktree's link to the main repo, which is expected in tree mode.
- **Run time on the Mac.** About 60 s per sugar seed; 76 s for the GF run, including its Organism build.

**flyemu.check, zip vs tree** (tree at 089022c; tests 15 min each way).
- **The first zip (089022c) failed 2 tests**, both repo-layout checks:
  - `test_scripts_default_to_the_working_model` runs `scripts/run_organism.py --help`;
  - `test_docs_cited_in_code_exist` needs `docs/`.
- The zip ships no `docs/` and only two scripts. Those tests check the repo, not the fly.
- They now skip only inside an extracted zip (the root holds `.flybrain_manifest.json`), so the repo still fails them if a script or doc goes missing (c248318).
- All other 269 outcomes, 12 skips, the ledger numbers and the scoreboard were equal between zip and tree.
- At c248318, the zip check passes (exit 0): 269 passed and 14 skipped in 849 s. The two repo-layout tests skip in the zip; every other test id and outcome, the rebuilt ledger and the scoreboard equal the tree's at 089022c (889 s). In the tree at c248318, `tests/test_repo_hygiene.py` still passes all 12, including those two.
- Read guard in the zip check: nothing denied. Outside the root and the Python install it read only the system version file, matplotlib's font cache, the timezone file, `/dev/null` and pytest's temp directories.

**Ledger fill fraction, rebuilt from the zip's own tables.** The rebuilt ledger equals the packed one in both modes.
- 145 quantities and 1,701,664,723 slots.
- Data (measured + derived): 0.42% of slots. With rule-inferred added: also 0.42%.
- Per quantity: 9.66% from data, 12.42% with rule-inferred.
- Outside the synapse grain (50.0 M slots): 14.18% / 14.19%.

**Correction to commit 793c3eb.** Its message says the ledger rebuild left the fill fractions "unchanged to 0.01%". That is true by slot (0.4171% / 0.4173%) but not per quantity. The 6 Oct ontology rows add 2 quantities (143 → 145) and move the per-quantity fill from 9.79% to 9.66% (data) and from 12.60% to 12.42% (with rule). The commit is not rewritten; this entry is the record.

**What this does and does not show.**
- Two of the eight scoreboard items now run from the zip alone, with results equal to the scripts that defined them. That makes them regression checks for any later zip.
- Both protocols score spent evidence, so neither verdict is a held-out test.
- Both step the brain only. PER is read as MN9 firing, and escape as motor neuron latency; no body moves in either.
- The two protocols build the brain the way their scripts do, which is not quite the same way. The sugar build skips the stubs, the body and Q10. Moving to one harness would mean re-scoring both gates.
- Leg sugar is the next protocol that needs no new code. It needs one decision first: a single number for "the route opens".

### F-ZIP-3: stands and walks now run from the zip in closed loop, identical to the tree and to their reference runs; both have no bar yet (verdict NO BAR), and neither stands nor walks (fly2, s22, 21 Oct 02:25; DECISIONS 21 Oct 02:16)

**What was built.**
- A `closed_loop` harness in `flyemu.score`: the body is stepped and every sense reaches the brain (observe, sense, network step with the kick, motor step).
- Two readouts: `leg_oscillation`, which is command_walk.py's per-leg summary, and `posture`.
- Two protocols in `data/world/`: `stands_flat_floor` and `walks_dng100`.
- Neither protocol has a pass condition. Each carries a `bar_todo` naming the missing number, so its verdict is NO BAR.

**The zip.** `runs/s22/fly2_zip/s3/fly_brain.zip`: 134,771,271 bytes, 479 members, sha256 8cc81b45…, packed from b7e6fc9. It is a build artifact and is not in git.
- **The first pack of this step was defective** (ef54015). It held two members named `world/stimuli/none.json`: the packer's generated null stimulus and the new tracked file. zipfile's duplicate-name warning caught it.
  - Fix (b7e6fc9): the packer refuses any member path packed twice, and the generated file gives way to the tracked one.
  - The defective zip was replaced before either zip run began; both zip manifests record b7e6fc9. It is not preserved.
- The tree runs started at ef54015 and finished after b7e6fc9 was committed, so their manifests read b7e6fc9. The two commits differ only in `pack.py`, which the runs never import.

**Identity (all pre-registered checks pass;** `compare_loop.txt` **in the run directory).**

| | reference | tree | zip |
|---|---|---|---|
| `walks_dng100`, seed 0: every field command_walk.py prints (6 legs × frequency, band share, amplitude; thorax dx, dy; leg MN rate; DNg100 rate; MuJoCo warnings) | `FLYEMU_PROFILE=m10f0 command_walk.py --type DNg100 --hz 100 --seed 0` | equal at the script's rounding | spike hash (79,030 spikes), final pose hash and every field equal to tree |
| `stands_flat_floor`, seed 12: spikes and final pose | the F-ZIP-1 tree run of `flyemu.run` | 53,314 spikes; spike hash 770807… and pose hash 3ec293… equal | equal to tree |

- **Read guard (zip runs).** Nothing denied. Outside the root, they read only matplotlib's font cache and the timezone file.

**What the model does (m10f0; recorded, not scored).**
- **Walks, DNg100 at 100 Hz (observed 92 Hz):** no stepping.
  - Each leg's dominant tarsal-tip frequency in 3-25 Hz is 3-4 Hz, the band's lower edge.
  - The band holds only 10-30% of the tip's power, and amplitudes are 0.04-0.25 mm.
  - The thorax moves 0.04 mm backwards. Leg motor neurons average 2.6 Hz.
  - This is the known walking failure (F-BYPASS-7, F-XCONN-2), now as a regression number.
- **Stands, no stimulus:** the thorax origin sits at 0.55 mm (median; minimum 0.546) and drifts 0.24 mm in 1 s. This is the lying posture of F-STAND-3; no standing bar exists to judge it against.

**What this does and does not show.**
- Four of the eight scoreboard items now run from the zip alone: labellar sugar PASS, GF escape FAIL, stands NO BAR, walks NO BAR.
- The closed loop is identical zip vs tree, and identical to both `flyemu.run` and command_walk.py. The full sensing and body path reproduces from one file.
- NO BAR is not a pass or a fail: the scoreboard still passes 1 of 8. Writing the bars is the Director's or Ben's call; the report proposes them.
- `flyemu.check` was not rerun on the b7e6fc9 zip. The c248318 zip's check passed, and the protocol test changes since then passed in the tree (20 of 20).

### F-ZIP-4: with bars written, the scoreboard has real verdicts: stands FAIL, walks FAIL, PER to leg sugar FAIL (MN9_L 0 Hz); 1 of 8 items passes, 5 of 8 are scored, all five from the zip alone, identical zip vs tree (fly2, s22, 21 Oct 03:06; DECISIONS 21 Oct 02:33)

**What was built** (8f1ad74; bars decided by the Director as Ben, reversible).
- `stands_flat_floor`: pass if no body other than a tarsal segment is pushed by the floor in any 1-ms sample of 500-1000 ms, and the head point is at least 0.1 mm above this body's motor-silenced collapse (0.429 mm, derived) over that window. Wang 2025 tracked a head point, so the bar reads the head, not the thorax. 0.1 mm is the lowest standing start height in Wang Fig 5C; no population maximum is published, so there is no upper bound.
- `walks_dng100`: pass if at least 4 of 6 legs have the dominant tip frequency in 7-15 Hz and at least half the tip power in 7-15 Hz, and the thorax moves forward along its heading.
- `per_leg_sugar` (new): LgLG4 + LgAG2 at 50 Hz, pass if MN9_L > 5 Hz (mean of seeds 0-9).
- The scorer refuses a closed-loop run unless only the network's motor spikes move the body, and records the check (`drive_check`): 106 actuators, none a servo; no mocap body; no active equality constraint; no wingbeat generator; no stimulated motor neuron.
- New readouts: floor contact per body, head height, thorax heading, 7-15 Hz share; judge op `count_where`. Reading contacts does not change the run: both closed-loop protocols reproduce their F-ZIP-3 spike and final-pose hashes.

**Results (m10f0).**
- **Stands: FAIL** on both conditions. Over 500-1000 ms a non-foot body is on the floor in every sample (head 496 of 500 samples, right-mid coxa 478, left-hind coxa 457, abdomen segments 4 and 6 about 455, left-mid coxa 450). The head sits at the collapse height (median −0.001 mm above it), and a median of 2 legs have a tarsus on the floor. Frames at 0, 250, 500, 750 and 1000 ms (`docs/media/s22_fly2_stands_frames.png`, viewed): placed standing at 0 ms; by 250 ms the fly lies on its belly and head with the legs splayed sideways and one leg raised in the air, and it stays there. The live fly ends where the motor-silenced fly ends (F-STAND-3).
- **Walks: FAIL** on both conditions. No leg counts: every dominant frequency is 3-4 Hz (the search band's lower edge) and the 7-15 Hz share is 0.035-0.053 per leg. The thorax moves 0.041 mm backwards along its heading. Leg motor neurons average 2.6 Hz while DNg100 fires at 92 Hz. Tip traces (`docs/media/s22_fly2_walk_tips.png`, viewed): the tips drift backwards over the drive with small irregular wiggles; only the right hind leg makes 3-4 slow, uneven swings of about 0.2 mm.
- **PER to leg sugar: FAIL.** MN9_L is at 0 Hz on all 10 seeds (bar > 5 Hz; MN9_R is dropped as incompletely traced, as in the labellar protocol). The 54 LgLG4 and LgAG2 cells fire at 47-51 Hz, but only about 164 of 167,111 neurons fire at all (the 54 driven cells plus about 110 others; network mean 0.029 Hz). The route stays blocked at rest, as F-TASTE-LEG-1 found at an earlier profile; this is the first measurement at m10f0.
- All three predictions written at 02:33 held, and the scoreboard count is as predicted.

**The scoreboard (m10f0, every scored item played from the zip at 8f1ad74).**

| item | protocol | verdict | measured (bar) |
|---|---|---|---|
| stands | `stands_flat_floor` | FAIL | non-foot body on the floor in 100% of samples (bar 0%); head 0.001 mm below the collapse height (bar ≥ 0.1 mm above) |
| walks | `walks_dng100` | FAIL | 0 of 6 legs at 7-15 Hz with share ≥ 0.5 (bar ≥ 4); thorax −0.041 mm (bar > 0) |
| grooms | none | not scored | a protocol spec went to the Director (DECISIONS 02:44); not built, not adopted |
| PER to labellar sugar | `per_labellar_sugar` | PASS | MN9_L 5.7 Hz (bar > 5); per seed 7 6 7 5 7 7 5 6 4 3, so 4 of 10 at or below 5 Hz (F-ZIP-2 said 3; it miscounted) |
| PER to leg sugar | `per_leg_sugar` | FAIL | MN9_L 0.0 Hz (bar > 5) |
| optomotor turning | none | not scored | needs code: vision bypasses the World, and there is no turning readout |
| giant-fibre escape | `gf_escape` | FAIL | GF spikes on 20 of 20 kicks; no TTMn or DLMn spike (bar: TTMn follows ≥ 90% at 0.87-1.22 ms, both DLMn groups at 1.36-1.85 ms) |
| stable flight | none | not scored | needs code: flight kinematics are imposed and the tether is set in code |

**1 of 8 passes; 5 of 8 are scored.** Every scored item scores spent or seen evidence (register rows for the zip protocols), so these verdicts are regression checks, not held-out tests.

**The zip.** `runs/s22/fly2_zip/s5/fly_brain.zip`, packed from clean commit 8f1ad74.
- 134,776,816 bytes, 481 members (2 more than F-ZIP-3's: the leg-sugar protocol and its stimulus), 271.5 MB unpacked, sha256 dbb16195….
- It is not in git (over 50 MB).
- Its manifest still lists `world/stimuli/leg_sugar.yaml` as TODO, which is stale; the packer's list is corrected after this check, so the next pack drops the line.

**Identity** (`compare.py`, written before the runs; verdict ACCEPT).
- The stands and walks tree runs at 8f1ad74 reproduce every F-ZIP-3 field, including the spike and final-pose hashes. Reading floor contacts doesn't change the run.
- Zip equals tree for stands (17 fields), walks (37 fields) and leg sugar (8 fields per seed, 10 seeds, equal spike hashes). The pass conditions are equal, and the read guard denied nothing.
- The leg-sugar tree run equals `assay_pathways.py --assay legsugar_mn9 --rates 50 --trials 10 --profile m10f0` per trial.
- Labellar sugar and GF escape from the new zip equal the F-ZIP-2 zip runs field for field, including verdicts.
- The walk figure's replay, made outside the scorer, reproduces the scored final-pose hash.

**flyemu.check on the 8f1ad74 zip.**
- Tests: 273 passed, 14 skipped, in 14.6 min. The 4 tests added since the c248318 zip are the new protocol tests (`test_world_protocols`: completeness of the 3 new or changed protocols, and the stand-window test). No earlier outcome changed.
- The ledger rebuilt from the zip's tables equals the packed ledger. The numbers are unchanged: 0.42% of slots from data, also 0.42% with rule-inferred; 9.66% / 12.42% per quantity; 145 quantities.
- The read guard denied nothing. Outside the root and the Python install, the check read only the macOS version file, matplotlib's font cache, `/dev/null` and the timezone file.
- Tree check at 8f1ad74: 275 passed, 12 skipped. Zip and tree have the same test ids and equal outcomes except the 2 repo-layout tests (`test_docs_cited_in_code_exist`, `test_scripts_default_to_the_working_model`), which pass in the tree and skip only inside an extracted zip, by design (F-ZIP-2). The ledger and the scoreboard listing are equal.


### F-S18-1: the 12-cell rhythm core supplies only 0.8% of the synaptic input to the T1 leg MNs; nearly all of it comes from outside the core, mostly hemilineages 20A/22A, 04B, 03A, 13A and 21A (s18, 21 Oct 21:41; connectome query, no simulation; walking parked after this; nothing adopted)
- **Query** (`scripts/connectome/premotor_outside_core.py`, Sonnet agent, unchecked by me row by row; write-up `docs/research/s18_premotor_outside_core.md`; CSV `runs/s18/premotor_outside_core.csv`). Local cache, synapses ≥ 5 per connection.
  - The T1 core is 12 cells (six `CORE_TYPES` × L/R); the T1 leg MNs are 94 cells of 13 `LEG_TYPES`, so 106 in all, as before.
- **Shares (derived):**
  - The core provides 0.8% of all input to the T1 leg MNs, between 0.2% and 5.5% depending on the pool.
  - Out-of-core input by hemilineage: 20A/22A 10.7%, 04B 9.4%, 03A 8.5%, 13A 8.5%, 21A 7.2%, 16B 6.1%, 19A 5.4%. TBD (no hemilineage) is 4.7%.
- **Reachability (derived):**
  - All of the top-20 out-of-core types are within two hops of DNg100: 7 directly, 13 through one cell.
  - 13 of the 20 also get direct input from the core.
  - Six get no core input: IN21A001, IN19A005, IN04B015, IN16B034, DNg105 and IN03A046.
- **Reciprocal inhibition (derived):** there are GABA and glutamate connections of at least 5 synapses in both directions between the candidates that feed flexors and those that feed extensors. Examples: DNg105 (GABA) onto four types that feed extensors; IN19A005 (GABA) ↔ IN16B016 (glutamate). These are a small fraction of each type's output, and glutamate's sign is unresolved.
- **What this says (inferred):** the s13-s17 arms drove a population that is a small minority of the leg MNs' input. A rhythm can reach the MNs only through the 20A/22A, 04B, 03A and 13A premotor layer, and that layer is near-silent in our runs (s4b: 0.13 Hz mean). This fits the "premotor driver outside the core" branch of the ruled-out paragraph.
- **Limits:**
  - The pool mapping reuses the repo test-file names.
  - The non-axis MN types (adductor, sternotrochanter, tergotrochanter) are excluded.
  - Results depend on the threshold.
- Walking is parked (Ben, 21 Oct). The next test, when it resumes: per-cell activity of these types in the s16/s17 runs, which needs a neutral per-cell spike save.

### F-S24-1: frontier stages m10f1-m10f3 all pass their gate and their unit checks; `m10f` now points at m10f3 (STP per connection, receptor decay per connection, identified gap junctions, PSI cholinergic). DLMn still never follow the giant fibre (fly2, s24, 22 Oct 01:49; DECISIONS 21 Oct 21:35 and 22 Oct 01:41)
- **Gate (measured, backhouse, `runs/s23/fc/`):**
  - G: 0.0 non-eye spikes/ms in the last 100 ms of silence on seeds 12-15 for every stage. No NaN, 0 MuJoCo warnings, top class 11.0 Hz (sensory_olfactory).
  - S, 60 s, seed 12: whole brain 0.303 / 0.304 / 0.304 Hz for m10f1 / m10f2 / m10f3 (m10f0 0.324; bound ±50%). Active fraction 0.027 for all three (m10f0 0.0281). No runaway.
  - m10f1 is 6.5% below m10f0, which is the ORN→PN depression. m10f3 is bit-identical to m10f2 at rest in G and S. The coupled cells (GF, TTMn, DLMn, PSI) are silent at rest, so neither the gap current nor PSI's sign reaches a spike.
- **Unit checks (measured in the model; `scripts/probes/m10f_unit_checks.py`, `gf_latency.py`; `runs/s24/unit/`):**
  - **Stage 1, STP: pass.** All 58 ORN_DM6 cells were kicked together at 10 Hz, and the summed input to the 7 DM6 PNs was recorded. The normalised per-pulse peaks equal Nagel 2015 Eq 1 to 1e-7 (0.803, 0.666 … 0.375). This is an implementation check, not held out.
  - Caveat for stage 1: in the isolated CNS the ORNs are silent (0 spontaneous spikes; resting resource x = 1.0), so the check runs from rest. In closed loop the ORNs fire about 11 Hz at rest. At that rate the derived resting x on these edges is about 1/(1 + U r τ) ≈ 0.32, so the synapse sits about two-thirds depressed. No measurement of in-vivo resting ORN→PN depression is in hand to check this.
  - **Stage 2, receptor decay: pass.** The fitted decay of the evoked current was 1.100 ms (row 1.1, ORN_DP1m→DP1m_adPN), 1.383 ms (row 1.4, DM2_lPN→KCab-s, −1.2%) and 3.700 ms (row 3.7, VP3+_vPN→KCg-s2). This is an implementation check of the measured or fitted rows.
  - **Stage 3, gaps and PSI: pass** (20 trials, isolated CNS). With gaps on, TTMn and PSI follow every GF spike (1.00, control 0.00). Latency to muscle is 1.099 ms for TTMn, inside the Augustin 2017 band 0.866-1.216 (spent, consistency only), and 1.097 ms for PSI.
  - With gaps off, nothing follows (0.00), so the switch acts.
  - **DLMn a,b and c-f follow 0.00 in both arms.** The DLM latency (band 1.36-1.85 ms) is unmet, so GF→PSI→DLMn does not transmit even with PSI cholinergic. This is the open part of N18.
- **Adopted:** `PROFILES["m10f"] = PROFILES["m10f3"]`. fly's scripts that default to m10f (s16_oa, proprio_reach, etc.) now run with the four synaptic switches on. fly_brain.zip v1 is unchanged.

### F-S24-2: KC->MBON depression fitted to Hige 2015 at one shared rate (0.430) passes the Handler 2019 held-out forward and +6 s checks and fails the backward one, as pre-registered (no LTP); m10f4 waits only on its 60 s smoke (fly2, s24, 22 Oct 03:33; DECISIONS 22 Oct 01:55, 01:57, 02:00)
- **Probe:** `scripts/probes/kc_mbon_pairing.py` (isolated CNS; KCs and DANs driven by kicks; `runs/s24/kc/` on backhouse, copied to the Mac). KC drive is Turner 2008: 6% of KCs, Poisson spikes per odour (α/β 2.2, α'/β' 4.9, γ 2.2 guessed). Readout: the KC-spike-weighted KC->MBON weight after over before, over the odour's KCs.
- **Fit (fitted, shared by all compartments):** one forward pairing (1 s odour, PPL1-γ1pedc pulses at 0.2/0.7/1.2/1.7 s), target CS+ charge 0.10 on MBON-γ1pedc>α/β (Hige 2015 Fig 3D, −90 ± 3.7%).
  - Per-seed solutions: 0.424, 0.442, 0.450 and 0.404 (seeds 12-15). The shared rate is the mean, **0.430 per DAN spike per unit KC eligibility**.
  - In network at the shared rate, the CS+ ratio is 0.097 / 0.106 / 0.110 / 0.087. **Pass** (band 0.06-0.14). PPL101 contacts both MBON11 cells in the compartment proxy.
  - The sensitivity run with γ KCs silent (Turner literal) gives 0.408, within 2×, so no flag. Only 32% of MBON11's KC synapses are from α/β KCs, but the ratio is a per-KC average, so the fitted rate barely depends on which KCs carry it.
- **Reported, not scored:**
  - CS− ratio is 1.0 at every seed; Hige measured about −25% in spikes. This is a known miss: the rule has no non-associative change.
  - Hige backward pairing: no change by construction, since LTP is off. Not evidence.
- **Held out, spent (Handler 2019 Fig 2D-E; MBON-γ4>γ1γ2 with PAM-γ4; KCs 500 ms, DAN 3 pulses at 2 Hz; mean of seeds 12-15):**
  - ISI −1.2 s: 1.000 at every seed. **H3 fails, as predicted**; there is no potentiation without LTP.
  - ISI 0: 0.095 (0.090-0.100). ISI +0.5 s: 0.077 (0.072-0.082). **H1 passes.**
  - ISI +6 s: 0.991 (0.990-0.991). **H2 passes** (bound: ratio ≥ 0.769).
  - The model's depression is about 90% at both forward ISIs. Handler's magnitudes are plot-only, so the size is not checked.
- Figure (viewed): `runs/s24/kc/fig_kc_mbon.png` (`scripts/probes/kc_mbon_figure.py`).
- **N22 unit check (implementation):** with forgetting on and tau overridden to 1 s, the mean CS+ deviation decays with tau 1000.0 ms (300 points). **Pass.** At the adopted 3 h, the derived recovery is 20% at 40 min and essentially complete by 24 h.
- **Gate (m10f4; G seeds 12-15, S 60 s):** G 0.0 non-eye spikes/ms, no NaN, 0 warnings, and identical to m10f3 in every JSON value at every seed. S (the pre-registered 60 s smoke, seed 12) was still running at 03:33 and finishes about 07:00, so it is not scored here and `m10f` stays m10f3. Its 10.5 s checkpoint (0.3054 Hz, 0.0268 active) equals the m10f3 10.5 s checkpoint in all 244 recorded values; only the profile name, build time and wall time differ. That is consistent with the prediction but is not the pre-registered test.
  - Why identical: in the m10f3 60 s smoke, all 4064 KCs, all 340 PAM/PPL DANs and all 97 MBONs are silent (0 Hz). So the rule never fires at rest, and the gate says nothing about it. The KC resting rate in vivo is about 0.1 Hz (HANDOFF register), so the silent mushroom body at rest is itself a miss of the resting state, not of this mechanism.
  - **S scored (s26, 22 Oct 22:18):** 0.3037 Hz, active fraction 0.0273, no runaway, no NaN, 0 warnings, identical to m10f3. **Pass**; `m10f` = m10f4 (F-S26-1, with the resting-DAN validity range).
- **Limits:**
  - Compartments are proxied by DAN->MBON contacts.
  - One rate for all compartments, though Hige finds that α2 needs a much longer protocol.
  - The 3 h tau disagrees with Berry 2018 for γ2α'1.
  - γ-KC odour spiking is in tension with Turner 2008.
  - The eligibility tau (1 s) and DA tau are guessed.
  - LTP is off, so N21 stays partial.

### F-S25-1: a dopamine-only restoration of KC->MBON weights is built behind a neutral switch and passes U1-U4; fitted to Hattori 2017 at 0.00289 per DAN spike it reproduces Hattori Fig 6F in network, inside ± 2 SEM at every n (3 of 4 seeds in at the park), keeps the Hige forward fit (0.089-0.112), but it fails the pre-registered resting check, so it is not adopted (fly2, s25, 22 Oct 05:09; DECISIONS 22 Oct 04:11, amendment 04:22)
- **Rule (`lif.py`, `kc_mbon_dan_restore_rate`, neutral 0, CPU only):** in each step where a DAN spikes, the KC->MBON weights in its compartments (DAN->MBON contact proxy) move toward baseline, `w <- w + r (w0 - w)`, whatever the KCs do. It is applied before the depression term. The form comes from Cohn 2015 Fig 7I, Hattori 2017 Fig 6F and Berry 2018 Fig 5H-I (figure check: `docs/research/s25_restoration_figcheck.md`, by a Sonnet subagent in the foreground).
- **Unit checks:**
  - U1: at r 0 the model is bit-identical to the pre-s25 `lif.py` under m10f4's KC overrides (170 steps, 5073 spikes, 4895 of 33496 edges depressed; `scripts/probes/s25_restore_u1.py`).
  - U2: from a halved state, weights approach baseline as (1 - r)^k per counted compartment spike-step (relative error ≤ 1e-5).
  - U3: naive weights are exactly unchanged.
  - U4: edges outside the spiking DANs' compartments are exactly unchanged.
  - U5: the GPU path refuses (code inspection). All pass.
- **Fit (fitted, analytic, provisional; `scripts/probes/s25_restore_fit.py`):** r 0.00289 per DAN spike-step, from weighted least squares on Hattori Fig 6F at S = 20 spike-steps per stimulation (10 light pulses × 2 spikes, guessed). Predicted recovery is 5.6/16/29/44% against 8/18/33/40% after 1/3/6/10 stimulations, chi2 1.12 (3 dof). S = 10 or 40 gives r 0.00578 or 0.00145.
- **In-network confirm (implementation check, not evidence; MBON16/17 = MBON-α'3ap/m with PPL104 = PPL1-α'3, inferred mapping; seeds 12-15):** S counted 20 spike-steps per stimulation at every seed, as assumed. There were no KC spikes during the stimulations. PPL104 is the only DAN type contacting MBON16/17, and it contacts all four cells. Recovery after 1/3/6/10 stimulations is 0.056/0.160/0.294/0.440 at seeds 12, 13, 15, identical to 3 decimals (depressed CS+ ratio 0.014-0.018), against the bands -0.02..0.18, 0.04..0.32, 0.21..0.45 and 0.28..0.52: inside at every n. The network reproduces the analytic fit, so this checks the implementation and the counted S, not the rule. **Seed 14 (scored s26, 22 Oct):** the same 0.056/0.160/0.294/0.440 (S counted 20, depressed ratio 0.0099). The pre-registered 4-seed mean is inside every band: **HATTORI CONFIRM (4 seeds): PASS** (`scripts/probes/s25_restore_summary.py`).
- **Regression (seen, not evidence):** the Hige 2015 Fig 3D forward CS+ ratio with r on is 0.099/0.108/0.112/0.089 at seeds 12-15, a pass (band 0.06-0.14 at every seed; m10f4 alone gave 0.097/0.106/0.110/0.087).
- **Resting check (pre-registered): FAIL.**
  - At PPL1-α'2α2's measured resting rate (6-10 Hz, Huang 2018), a memory would last tau = -1/(f ln(1 - r)) = 58/43/35 s, against the 2.3-10.4 h bracket.
  - Only resting DAN rates below 0.04 Hz are compatible.
  - Hattori's own unstimulated controls are flat, so in the fly resting dopamine does not restore at this rate. A linear per-spike rule can't be the whole mechanism.
  - Not adopted: no m10f5. `kc_mbon_dan_restore_rate` stays 0 in every profile.
- **Derived, not pre-registered (same script):** m10f4's own depression has the same problem. At rest (KCs 0.1 Hz, so a mean eligibility of 0.1), DANs at 6-10 Hz would drive every KC->MBON weight to 0 with tau about 3 s (2.2-3.6 s with restoration on; steady state 6% of baseline). Today this is invisible, because the mushroom body is silent at rest in every profile (F-S24-2). It matters as soon as fly fits the DAN resting rates (HANDOFF, fly section). Both N21 terms need a form that ignores resting dopamine (for example a low-affinity receptor threshold or burst-only gating, inferred) before DANs fire at rest.
- **Hige 2015 backward pairing stays unspent.** The brief named it as the falsifier, but under a baseline target a naive synapse can't move, so it passes by construction. It is kept for a potentiation variant (cap target or timing LTP).
- **Berry 2018 Fig 5H-I stays sealed and unspent.** Its arm (about 450 s simulated per run) is next. The model value is computed first; then a scorer opens `docs/research/sealed/s25_restoration_heldout_sealed.md`.
- **Known misses:**
  - DA alone doesn't potentiate naive synapses (Cohn 2015 Figs 6A-C and 7D do).
  - CS- doesn't change (Hige: about -25%).
  - One rate for all compartments.
  - Spikes per light pulse guessed.
- Figure (viewed): `runs/s25/restore/fig_s25_restore.png` (`scripts/probes/s25_restore_figure.py`).

### F-S26-1: no sourced form of KC->MBON plasticity tested here keeps a memory for hours at measured resting rates (KCs 0.1 Hz, DANs 6-10 Hz); m10f4's depression is safe only while its DANs rest below about 0.0015 Hz, and m10f moves to m10f4 with that validity range (fly2, s26, 22 Oct 22:34; DECISIONS 22 Oct 22:28, amendment 22:31)
- **Smoke S (m10f4, seed 12, 60 s, backhouse):** whole brain 0.3037 Hz (band 0.162-0.486), active fraction 0.0273 (band 0.014-0.042), no runaway, no NaN, 0 MuJoCo warnings, identical to m10f3. **Pass.** `m10f` = m10f4 (`src/flyemu/profiles.py`). This closes F-S24-2's open S.
- **Test R harness:** `scripts/probes/s26_retention.py` -> `runs/s26/retention.json` (about 30 s on the Mac). It is event-driven, one compartment, using the lif.py N21/N22 update order. Harness check: the Hige pairing at r 0.430 gives a CS+ ratio of 0.067 (band 0.06-0.14). **Pass**, after the pre-registered amendment, which set 2.86 spikes per CS+ KC and charge weighting as in the network.
- **Results at 2.3 h** (M = memory index, M(0) 0.90, pass needs M ≥ 0.331; W = naive weight / w0, pass needs W ≥ 0.5; DANs at 6 / 8 / 10 Hz):

  | rule | uniform KCs W | heterogeneous KCs W | M | verdict |
  |---|---|---|---|---|
  | R0, m10f4 (depression 0.430) | 0.001 / 0.001 / 0.001 | 0.20 / 0.22 / 0.23 | -0.03 to 0.52 (meaningless with W near 0) | **fail** |
  | R1, R0 + s25 restoration 0.00289 | 0.15 / 0.17 / 0.19 | 0.42 / 0.44 / 0.46 | -0.08 to 0.20 | **fail** |
  | C1, KC coincidence e^4 (rate re-solved to Hige: 0.223) | 0.002 at every rate | 0.20-0.23 | | **fail** |
  | C2, burst dependence d^2 (rate re-solved: 0.177) | 0.001 at every rate | 0.20-0.23 | | **fail** |
  | C3, Berry restoration only (1.16e-5 per DAN spike, N22 off) | 1.0 | 1.0 | 0.51 / 0.42 / 0.34 | **pass R**, by construction |
  | C3 with N22 on | 1.0 | 1.0 | 0.24 / 0.19 / 0.16 | **fail** |

  - In the heterogeneous variant, W stays near 0.2 only because 20% of KCs never fire at rest and keep their weights.
  - C3 has no depression, so it cannot form a memory. It also predicts 0.23% recovery after 10 Hattori 2017 stimulations, against a measured 40 ± 6%, so it misses Hattori by about 170×. It is a forgetting term, not a plasticity rule.
  - Every result matches the analytic prediction written before the runs.
- **Validity bound (derived):** R0 passes R only when the compartment's DANs rest below **0.0015 Hz**. At 6-10 Hz, its depression is about 4000-7000× too strong. In m10f4, 0 of 340 DANs fire at rest, so the adopted rule is inside this bound today.
- **Why the sourced forms fail (derived):**
  - Every pairing protocol used (Hige 2 Hz, Handler 2 Hz) or held out (Hattori about 7 Hz) drives the DAN at or below the measured resting rate.
  - So any per-spike rule that increases with DAN rate or DAN bursting (C2) rewards rest at least as much as it rewards pairing.
  - A spontaneous KC spike leaves an eligibility of about 1 at the next DAN spike, close to the odour-evoked mean of about 1.4. So KC-side cooperativity (C1) buys little; 4 forming DAN spikes against about 70,000 resting ones in 2.3 h cannot be bridged by a power of e.
  - The rule needs something that makes a spontaneous DAN spike far less effective than a stimulated one, by a factor of about 10^3 to 10^4.
- **Inferred candidates, none sourced in hand; for the Director:**
  - (a) Stimulated DAN activity releases or signals much more dopamine per spike than spontaneous spikes. Needs a source.
  - (b) DANs in the plastic compartments rest far below 6-10 Hz. The 6-10 Hz figure is PPL1-α'2α2 (Huang 2018); PPL1-γ1pedc and PAM-γ4 may differ. Huang 2024 is held out (fly's data).
  - (c) A state gate on plasticity.
  - (d) A fitted threshold, which the brief rejects.
- **Consequence:** fly's resting-rate fit must run with N21 off (`cell_type:all|kc_mbon_ltd_timing_rate` 0 in the run, or m10f3). Otherwise every KC->MBON weight goes to 0 within seconds once DANs fire. N22 alone is passive and resting-safe.
- **Limits:**
  - One compartment, with one DAN spike = 1 unit of dopamine.
  - Poisson KCs and DANs; no MBON->DAN feedback.
  - Eligibility and DA trace taus are guessed, as in lif.py.
  - The 6-10 Hz rate is from one compartment's DAN.

### F-S26-2: candidate (e), Handler 2019's two-receptor timing rule, fails test R in every form (fly2, s26b, 22 Oct 22:42; DECISIONS 22 Oct 22:40)
- **Is s25's restoration already the Dop1R2 side? No.**
  - s25 restoration is KC-independent and non-associative.
  - Handler's Dop1R2 side, DA before KC, is lif.py's `kc_mbon_ltp_timing_rate`, built in s10 and neutral 0. It is the timing-dependent term, and what it lacks is a sourced magnitude.
- **Harness:** `scripts/probes/s26_retention.py --e` writes `runs/s26/retention_e.json` (about 2 min on the Mac). The per-KC-spike potentiation was added, and the R0 regression is unchanged (W 0.0008 at 8 Hz). The Hige pairing band is met by construction: CS+ 0.100 for E1a (r_d 0.541, r_p 1.082) and for E2 (a_d 0.706, a_p 1.411).
- **Results at 2.3 h, DANs at 6 / 8 / 10 Hz.** W = naive weight / w0, which must be ≥ 0.5 to pass. With uniform KCs, M is meaningless because CS+ and CS- weights are both near 0.

  | rule | W, uniform KCs | W, heterogeneous KCs | M, heterogeneous | verdict |
  |---|---|---|---|---|
  | E1a, soft-bound, windows balanced (r_p = 2 r_d) | 0.085 / 0.025 / 0.036 | 0.27 / 0.24 / 0.26 | 0.36 / 0.52 / 0.56, only the silent KCs | **fail** |
  | E1b, r_p chosen for W = 1 | unattainable: W is 0.018 at r_p 100 | | | **fail** |
  | E2, additive, balanced (a_p = 2 a_d) | 0.059 / 0.011 / 0.031 | 0.25 / 0.23 / 0.25 | 0.40 / 0.55 / 0.59 | **fail** |

  - Hattori 2017: DA-only stimulation with no KC spikes gives 0 recovery under every E rule, against a measured 40 ± 6%. **Fail.**
- **Against the prediction written beforehand:**
  - Held:
    - "Every E rule fails R".
    - E1a's W far from 1, because the linear balance breaks at rest.
  - Wrong:
    - E1b was predicted attainable, but it is not.
    - E2's W was predicted at 0.7-1.3 but came out 0.01-0.06.
    - In the uniform case, M can't be assessed.
  - Why the details were wrong: both rules hit their bounds at rest.
    - A KC spike at 8 Hz rest sees a DA trace of about 4. That potentiates to the cap at once (E1: r_p d clips at 1; E2: +5.6 w0 is clipped to +2 w0).
    - The roughly 8 DAN spikes inside the same KC spike's 1 s eligibility window then take the weight to 0 within about 0.25 s. It stays there until the KC's next spike, about 10 s later.
    - The linear balance assumes small steps. The Hige fit requires steps of order w0 per event (90% depression from 4 DAN spikes).
- **Mechanism-level statement (derived):**
  - Signed timing windows cancel only the mean drift, and only when steps are small next to the weight range.
  - At 6-10 Hz rest, every spontaneous KC spike falls inside both windows at once, about 4 DA units before it and about 8 DAN spikes after it. With steps large enough to learn from one pairing, both sides saturate and depression has the last word.
  - Even with exact cancellation, erasure would remain: soft-bound weights relax to the fixed point with a 1-2 s tau, and additive weights diffuse across the range in about a minute. Rest supplies about 6600 KC-DAN coincidence units in 2.3 h, against about 5 in a pairing.
  - A rule that keeps memories for hours must either see far fewer coincidences at rest (DANs much quieter there, or spontaneous spikes much less effective), or depend on something rest lacks.
- **Limits:**
  - This is the harness, not the network.
  - Handler's window shapes are taken as exponentials with lif.py's guessed taus (eligibility 1 s, DA 0.5 s); its amplitudes are plot-only and spent.
  - The cap of 2 is guessed.
  - Hige 2015 backward pairing is still unspent.

### F-S26-3: candidate (b) finds no source placing any MB compartment's DANs near the 0.0015 Hz bound; KC->MBON plasticity's resting stability is an OPEN MECHANISM (fly2, s26b, 22 Oct 22:45)
- **Table:** `docs/research/s26_mb_dan_rest_rates.md`, from one read-only search agent; fly2 has not re-checked it. Huang 2024 was not opened, nor Berry 2018 Fig 5.
- **Measured resting spike rate:** only PPL1-α'2α2 has one, about 6-10 Hz (Huang 2018, voltage imaging). PPL1-α'3 is "stationary", with no Hz read.
- **Other compartments:** calcium only. Berry 2012 Fig 5C (GCaMP3) shows ongoing activity in PPL1-γ1pedc and PPL1-γ2α'1, with no number. Plaçais 2012 reports slow oscillations at about 0.1-0.3 Hz (unverified). Cohn 2015, Siju 2020 and Zolin 2021 report state-dependent fluctuation. Aimon 2019 reports "surprisingly little activity during resting or grooming".
- **Calcium can't settle it (derived):** Berry 2012's GCaMP3 reads PPL1-α'2α2 as not different from zero, while voltage imaging finds the same type at 6-10 Hz. So calcium quiet is consistent with tonic Hz-rate spiking, and no unheld source can put a compartment below about 0.01 Hz, let alone 0.0015 Hz.
- **Outcome of the Director's 22 Oct ladder:** (e) fails (F-S26-2), and (b) finds no source. **MB plasticity's resting stability is an open mechanism.**
  - N21 stays in m10f with its validity range (DANs silent at rest).
  - fly's resting fit runs with `cell_type:all|kc_mbon_ltd_timing_rate` 0.
  - The decisive recording is item 5 in `docs/MEASUREMENT_LIST.md`.
  - Huang 2024 (held out) would answer the PPL1 resting rates when the Director releases it.

### F-S27-2: C1 failed because about 4-5% of resting KC coincidences (200-440 per KC in 2.3 h) are as strong as the pairing's; a rutabaga/dunce cAMP-PKA cascade at ceiling cooperativity still misses test R by 55x, so it is ruled out as the resting-safety factor and not built (fly2, s27, 22 Oct 23:32; DECISIONS same time)
- **Harness:** `scripts/probes/s27_cascade_predict.py` -> `runs/s27/cascade_predict.json`. s26 test R conditions: KCs 0.1 Hz, DANs 6-10 Hz, 2.3 h, the Hige charge-weighted target 0.10, pass at W >= 0.5 with N22.
- **C1, per KC in 2.3 h at DANs 6 / 8 / 10 Hz (derived):**
  - Coincidences (e >= 1/e): 5166 / 7004 / 8949.
  - Crossing C1's criterion (e >= the pairing's median, about 1.14): **3.9 / 4.9 / 4.9%**, i.e. 202 / 340 / 442 events against 1.6 per pairing. These carry 85-89% of the resting depression.
  - Saturating events (r e^4 >= 1): 68 / 89 / 160 against 1.2 per pairing.
  - The power removes single-spike coincidences, but not the about 80 resting KC spike pairs, each seen by about 8 resting DAN spikes (4 in the pairing).
- **Cascade (Ca^n x D, cAMP low-pass tau_c, PKA c^h, k solved per KC to the Hige target):**
  - 108 combinations: tau_ca 0.1-1 s; tau_d 0.5 s / 15 s (Tomchik 2009 window); n 1-4 (calmodulin ceiling); tau_c 1-60 s; h 1-2. All brackets are inferred; no Hill coefficient or tau is sourced in hand.
  - **0 of 108 pass.** Best W is 0.013. Rest must be **55x** less effective at the ceiling (n 4, h 2), and 55-552x across the grid.
  - The ratio of mean drives (0.18-0.6 at n 4, h 2) is misleading. The charge-weighted target forces KCs with 2-3 odour spikes down (w 0.35 / 0.04), and resting spike pairs repeat that dozens of times.
- **Meaning:**
  - KC-side cooperativity, of any sourced form, cannot make N21 resting-safe. The missing factor is on the dopamine side:
    - (a) stimulated DAN spikes far more effective than resting ones (no source yet);
    - (b) plastic-compartment DANs rest far below 6-10 Hz (Huang 2024, after fly scores it).
  - The pure product over-discriminates relative to Tomchik's measured synergy (each input alone raises cAMP). The real cascade is further from passing.

### F-S27-1: DLM motoneuron (MN1-4) electrical coupling fitted to Hurkey 2023 in the full network (c 0.0266 gives CC 0.0143); G and the 60 s smoke S pass, identical to m10f4; `m10f` = m10f5 (fly2, s27, 22 Oct 23:53, adopted 23 Oct 03:13; DECISIONS s27 N12 entry 23:08 and amendment 23:32)
- **Switch (neutral, bit-identical; commit 120e0f6):** per-row `electrical:<pre>-><post>|gap_coupling` / `|gap_spike`, read only when set. The DLMn row is split into MN1-4 (`DLMn c-f,DLMn c-f`) and MN5 (`^DLMn a,DLMn c-f`, registered, inert). A negative `gap_spike` is refused, because `lif.step` lands only positive held kicks.
- **Value (inferred, fitted; one value for the class):** `electrical:DLMn c-f->DLMn c-f|gap_coupling` **0.0266** (junction / partner leak conductance), 12 same-side pairs.
  - Target: the pair-count mean of Hurkey 2023 Fig 2f, (2 x 0.023 + 4 x 0.010) / 6 = 0.0143; band 0.0073-0.026 (s.d.).
  - Protocol: `scripts/probes/s27_dlmn_cc.py` (m10f, seed 12). A 20 ms depolarising pulse into each cell in turn (pre peak 4.38 mV), with an unstimulated twin subtracted. Scored by `s27_dlmn_cc_baseline.py` (onset baseline, clean pairs; post hoc, see the amendment).
  - Fit: CC 0.01081 / 0.01613 / 0.01792 at c 0.02 / 0.03 / 0.0334, linear. **Confirm at 0.0266: 0.01433** (0.01362-0.01498). No spike from any pulse.
- **Implementation check:**
  - CC within 5% of target: **pass** (+0.2%).
  - No pulse spike: **pass**.
  - "Both directions within 5%" **fails as written** (reversed-order run `c0.0266r`; max 9.5%, mean 5.8%; `runs/s27/dlmn_cc_directions.json`). The cause is protocol history, not the junction:
    - The clean CC takes three values set by the presynaptic cell's place in its side's stimulation order: first 0.01498, second 0.01362, third 0.01378.
    - Pairs read at the same order position in both runs agree to every digit (31456/54469, 36444/36447, 36445/36446).
    - The junction is symmetric by construction (r 1, one c, identical DLMn parameters).
    - The history-free (first-pulse) CC is 0.01498, +4.8% on target.
- **AHP (seen, consistency only):**
  - The model DLMn have a -5.4 mV spike AHP (the s27 pre-registration wrongly said none, from a run whose negative kicks never landed).
  - AHP CC at 0.0266: 0.0155 (0.0113-0.0300), against 0.042 +- 0.04. Inside one s.d.
- **Gate G (m10f5, seeds 12-15, backhouse):** whole brain 0.308-0.310 Hz, motor 2.01-2.02 Hz, silent window 0.0 non-eye spikes/ms, 0 MuJoCo warnings, no NaN. All values equal m10f4's to the printed precision. **Pass.**
- **Smoke S (m10f5, seed 12, 60 s, backhouse, done 23 Oct 03:10):** whole brain 0.3037 Hz (band 0.162-0.486), active fraction 0.0273 (band 0.014-0.042), no runaway, no NaN, 0 MuJoCo warnings. Identical to m10f4, as is every one of the 167,111 cells' 60 s rates (`runs/s27/fc/smoke_m10f5_s12_rates.npz` vs s24's). The DLMn c-f fire at 0 Hz in both, so the junction joins silent cells at rest. **Pass.** `m10f` = m10f5 (`src/flyemu/profiles.py`).
- **Battery:** full pytest on the Mac with the s27 code (23 Oct 00:04-00:18, `runs/s27/pytest_full_s27.log`): 277 passed, 12 skipped, 0 failed; the usual MuJoCo QACC warning.
- **Figure (viewed):** `runs/s27/dlmn_cc_fig.png` (`scripts/probes/s27_dlmn_cc_fig.py`). Left: the 4.38 mV pulse in 31456 gives a 0.066 mV partner peak about 11 ms later in all three same-side partners; the opposite-side cell and the c = 0 run stay flat. Right: CC is linear in c through about the origin, and the fitted c sits on the target inside Hurkey's s.d. band.
- **Validity range:**
  - Subthreshold DC coupling of MN1-4 only. The spike step stays blank (spike amplitude unreported), so overshoot is not carried. The AHP is carried only as the model's own AHP through the junction.
  - The 2:1 strong/weak pair structure can't be placed, since the type label can't say which cell is MN1-4.
  - MN5 coupling is unmeasured.
  - Hurkey's functional result (the splay gap around phase 0, which shakB RNAi removes, Fig. 2b and Extended Data Fig. 6) is not tested here; it is the second check registered in DECISIONS 23 Oct 03:34. Correction (23 Oct 03:34): the "sync index 0.56 vs 0.61" quoted here before was the Shab knock-down, not shakB.

### F-S27-3: N21 candidate (b) is ruled out for every recorded PPL1 compartment: Huang 2024's PPL1 DANs rest at 5-27 Hz per fly, about 3,400x or more above the 0.0015 Hz test R needs (fly2, s27, 23 Oct 03:37)
- **Data (measured).** Huang et al. 2024 Fig. 1 voltage imaging (`data/raw/huang2024/Figure1.zip`), released to fly2 by the Director at 03:25 after fly spent it once as a held-out test of resting rates (F-S21-1). Using it here as a bound on a model assumption spends nothing new: the rates are already training context for the MB and nothing is fitted to them. Readout as fly's (`scripts/probes/s21_mb_huang_score.py`): trial spikes / duration, then the mean of the trials within each fly. Script `scripts/probes/s27_huang_ppl1_rest.py`, output `runs/s27/huang_ppl1_rest.json`.

  | type | flies | min (Hz) | P10 | median | max | flies < 0.1 Hz | min / 0.0015 Hz |
  |---|---|---|---|---|---|---|---|
  | PPL1-γ1 | 20 | 12.3 | 12.8 | 20.4 | 26.6 | 0 | 8,200 |
  | PPL1-γ2 | 20 | 7.8 | 8.8 | 11.7 | 18.1 | 0 | 5,200 |
  | PPL1-α′3 | 20 | 5.0 | 6.1 | 7.7 | 24.3 | 0 | 3,400 |
  | PPL1-α3 | 20 | 8.4 | 10.9 | 14.0 | 23.4 | 0 | 5,600 |
  | PPL1-α2 | 20 | 7.1 | 7.4 | 8.5 | 13.0 | 0 | 4,800 |

- **Verdict (derived).** Not one of the 100 flies has a PPL1 DAN at rest within three orders of magnitude of the bound, so N21's resting safety can't come from silent DANs in these compartments. Huang 2024 records no PAM types, so the PAM compartments are still open. Calcium imaging shows ongoing, state-dependent DAN activity (F-S26-3) and gives no hint that any compartment is near silent, but that is not a PAM rate measurement.
- **What is left on the Director's 22 Oct ladder:** (a), a dopamine-side gate. Ueno 2017 doesn't supply it: there's no magnitude or timing, and its NMDA requirement conflicts with Hige 2015's in-vivo depression from DAN activity alone (HANDOFF s27). (b) and (e) are ruled out, and the cAMP-PKA cascade is ruled out by prediction (F-S27-2). N21 stays in m10f with its validity range. fly's note (01:10) agrees: the model DANs fire at 6-15 Hz at fitted noise, so any run with σ*_DAN on must set `cell_type:all|kc_mbon_ltd_timing_rate` 0.

### F-S27-4: N12's second check FAILS. The fitted DLMn junction gives no splay gap, the falsifier fires in condition B, and the DLMn entry stays partial with no refit (fly2, s27, 23 Oct 03:59; pre-registered DECISIONS 23 Oct 03:34)
- **Protocol as registered.** `scripts/probes/s27_dlmn_splay.py`: m10f5, seed 12, 20 s with 2 s skipped, DC 0.026 plus 0.5 mV Poisson kicks (guessed drive). Scored by `s27_dlmn_splay_score.py`; output in `runs/s27/dlmn_splay_{A,B}_{fit,c0}.json` and `dlmn_splay_score.json`. All four runs went through `slot.py` at 1 thread, about 21 min each.
- **Readout note.** The registration called the 12 same-side and 16 cross-side pairs "ordered", but those are the unordered counts. The committed probe averages the 24 and 32 ordered pairs. The means are identical either way, since each unordered pair's value is the average of its two directions; only the SEM differs.
- **Rates:** 8.2-10.5 Hz in every arm, inside Hurkey's 3-12 Hz. ISI CV is 0.43-0.52.

  | condition | arm | same-side | cross-side (uncoupled control) | rule | result |
  |---|---|---|---|---|---|
  | A (independent 200 Hz) | fitted c 0.0266 | 0.192 ± 0.005 | 0.191 | < 0.18, >= 0.02 below c0, cross 0.17-0.23 | **fail** (only the cross rule passes) |
  | A | c = 0 | 0.198 ± 0.006 | 0.206 | | |
  | B (shared 50 + independent 150 Hz) | fitted | 0.251 ± 0.006 | 0.261 | < 0.20, >= 0.02 below c0 | **fail** |
  | B | c = 0 | 0.245 ± 0.006 | 0.249 | | |

- **Verdict: FAIL, falsified.**
  - In B the fitted arm's same-side fraction is above the c = 0 arm's (0.251 vs 0.245), the registered falsifier.
  - In A the fitted arm sits 0.005 below c = 0, about one SEM, and its coupled pairs read the same as its uncoupled pairs (0.192 vs 0.191).
  - The junction at c 0.0266, with the current DLMn intrinsics, does not reproduce Hurkey's splay gap. Hurkey Fig. 2b / Extended Data Fig. 6 is now **spent**.
- **Figure (viewed):** `runs/s27/dlmn_splay_fig.png` (`s27_dlmn_splay_fig.py`).
  - A: both arms' same-side phase histograms are flat within ±15% of uniform. The fitted arm has a mild bump at phase 0.5-0.6 and no dip at 0.
  - B: the shared input puts an in-phase peak (phase near 0 and 1, density about 1.6) in every pair, coupled or not, and the fitted arm doesn't lower it.
- **Post hoc, untested (why; no refit was made).** These are three candidate reasons, all outside the junction value:
  - (1) The spike itself is not passed through the junction (the spike step is blank; Hurkey's spike amplitude is unreported). Per partner spike the model passes only the subthreshold and AHP parts, about 0.07-0.08 mV (F-S27-1).
  - (2) Against that, the guessed drive gives each cell about 22 kicks of 0.5 mV per ISI, a count SD of about 2.3 mV (derived). So the coupling signal from 3 partners is about a tenth of the noise.
  - (3) Hurkey's model needs a PRC that falls around phase 0.5 (excitability near the SNL point). The model DLMn are LIF plus rung-1 channels, with a type-I-like PRC (not measured here).
  - So the miss goes to the excitability side (fly's N2/N4 DLMn intrinsics) and to the missing spike step, as registered, as well as to the junction.
- **Consequence:**
  - The `gap_junctions.csv` DLMn c-f row is **not** proposed as done. It stays partial: fitted to the CC (F-S27-1), with the functional check failed.
  - N12 as a whole couldn't be done in any case: 6 of the 9 rows in `data/params/gap_junctions.csv` carry no value (JO-A->GF, VS-VS, LN->PN, PN-PN, APL-DPM, MN5->MN1-4).
  - `m10f` stays m10f5. The coupling is inside Hurkey's measured CC band and the DLMn are silent at rest, so the failure doesn't affect resting runs.
  - A retry needs a sourced DLMn spike amplitude (for the spike step) and a DLMn PRC or excitability source, then a new held-out functional measurement. Candidate: Hurkey Fig. 3d's synchronization index under ShakB overexpression, unspent, but its formula isn't in the text.
### F-S19-2: N19's receptor map, calibrated on Mi4 (a* = 0.0649), gives the antennal-lobe PNs −0.3% under 5-HT against Dacks' +15%: the held-out magnitude test fails and N19 stays built-off (s19, 22 Oct 05:23; pre-registered DECISIONS 21 Oct 21:56, 22 Oct 01:56, 02:05, 02:25, 04:42)
- **Calibration (fitted).** Strother 2018 Fig. 6F, Mi4 ×2.66 to L5 photoactivation under CDM (read from the figure
  pixels, derived). Refined grid: Mi4 output a = 0.02 ×1.36, 0.04 ×1.82, 0.06 ×2.50, 0.08 ×3.16; a* = 0.0649.
  Mi4's own input gain at a* is only ×1.13 (L5 is modulated too). The ×2.66 output is network amplification
  of a near-threshold Mi4.
- **Held-out test (spent).** Dacks 2009, PN odour response +15% under bath 5-HT (n = 8). In the model: DM2/DL1/DM3
  ORNs kicked (Poisson 100 Hz), 12 PNs read (DL1_adPN, DM2_lPN, DM3_adPN, DM3_vPN), u_5HT 1 against 0 at a*: 297 → 296 evoked spikes, **−0.34%**, band +5% to +30%. **FAIL.**
- **Why.** All 12 PNs are on the population prior (no type or hemilineage transcript row), with net 5-HT
  +0.0556 under the sign rule. Their input gain is therefore about +0.4%. Mi4's type row gives net OA 2.0, about 36 times the
  receptor weight per unit a (`runs/s19/n19/map.json`).
- **Caveat.** A first Dacks run at a wrong a* (0.0458, a driver bug that let a voided grid point in) leaked a
  "fail" before this score (DECISIONS 04:42). The registered run fails the same way.
- **Also held (s19):** U3 sign test passes 5 of 5, weak by construction; the off-path spike hash is identical.
  U1/U1h are unscored (their runs at the wrong a* are void and unread).
- **Reading.** The mechanism runs and is neutral when off, but one shared gain over a population prior can't place
  a sensitivity where the prior has none. The next step is data: PN 5-HT receptor expression (Davie 2018 brain atlas,
  fetched tonight, has annotated PN clusters), then a re-registered test on unspent evidence. Dacks can't be reused.

### F-S19-1: the lumped metabolism, given values read from sources, predicts male starvation survival (28.4 h) and CAFE intake (1.85 µl/day) inside their held-out bands. This holds only at the measured group metabolic rate: at Burggren's single-fly extrapolation, both fail (s19, 22 Oct 02:31; pre-registered DECISIONS 22 Oct 02:06 and 02:30; switch `state:organs|values_from_sources` built, neutral 0; nothing adopted)
- **What was run.** The `internal_state.Organs` ODE alone, with no nervous system, from six values read from
  sources: basal use, the fat store, hemolymph volume, body water, and the crop and gut τ. The other parameters
  keep their s10 guesses. Probe: `scripts/probes/s19_metabolism_checks.py --sourced`.
- **Results.**
  - S2 starvation on water: 28.4 h against a 24-112 h band, from secondary reports. Pass.
  - S3 CAFE: 1.85 µl/fly/day against 1.0-2.25, from Ja 2007 (single Canton-S males at 25 °C, read). Pass.
  - S4 desiccation: not scored, because two of its inputs were not found. Its values are unspent.
  - S1 rest sugar after 6 h of fasting: 39.2 mM. This is consistency only.
- **What the passes rest on.** The fly burns 0.00626 nmol glucose-eq/s. That comes from Burggren 2017's group
  respirometry: 6 µl O2/mg/h × 0.505 mg, with RQ 1 and STPD assumed. The authors extrapolate a single fly to
  14 µl/mg/h; at that rate starvation is 12.2 h and CAFE 4.3 µl/day, and both fail. CAFE also counts only the
  food's sucrose. With the yeast extract's energy counted (guessed 3.3 kcal/g), CAFE lands at 1.00, the band's
  edge. The store is TAG only, with glycogen missing.
- **Reading.** The model's energy budget can be consistent with some fly of this species from read values
  alone. The model was not fitted to either held-out value. The agreement is still fragile to one unresolved
  measured quantity: the single fly's metabolic rate.
- **Validity.** A resting, lumped single store; no starvation-induced change in metabolic rate or activity;
  no protein pool.
- **Needed (Ben's list).**
  - Adult male hemolymph trehalose and glucose.
  - A water-loss rate at low RH, and a lethal water-loss fraction.
  - A primary male starvation survival time.
  - A single-fly respirometry value.

## Session 20 (22 October 2026)

### F-S20-1: the lumped clock's light input (one pull towards ct_light, saturating only in intensity) cannot fit the light-pulse sources: in 12:12 LD lights-on lands at CT 19-22. The k that gives Kistenpfennig's 60 min delay (k ≈ 1) gives a 5 min shift of 0.26 h (flies 3.1 h). The k that gives about 3.5 h for 5 min gives 9.2 h for 60 min (flies 4.05 h). the registered fit is void and Lamba ZT21 stays unspent (s20, 22 Oct 22:43; DECISIONS same time)
- k scan (ct_light 6.5, l50 10, `s19_n26_prc.shift_h`, `s20_n26_fit.ld_assay_shift`):

  | k (/h) | lights-on CT | DD CT15, 5 min 1500 lux | DD CT15, 60 min 1000 lux |
  |---|---|---|---|
  | 0.3 | 21.8 | −0.08 | −0.94 |
  | 1 | 19.8 | −0.26 | −4.00 |
  | 10 | 18.7 | −3.51 | −9.22 |
  | 100 | 18.5 | −8.26 | −9.46 |

  The LD ZT15 shift at the same k values: −0.09 / −0.28 / −1.49 / −2.90.
- Measured comparisons: Lamba 2014 −3.1 h (5 min, LD ZT15) and Kistenpfennig 2012 −4.05 ± 0.18 h (60 min, DD CT15). Different strains and
  temperatures, so the ratio is approximate. Real flies are near saturation by 5 min; this model is not.
- Status: inferred (model structure), measured inputs. N26 doesn't move. Next: a TIM-like light-labile input (DECISIONS).

### F-S20-2 (corrected 22:51, see the last bullet): Davie 2018 rows give the PNs a negative net 5-HT sensitivity (adPN −0.29, lPN −0.11; the prior gave +0.056), so postsynaptic N19 predicts PN inhibition, while Dacks 2009 measured facilitation; the s19 failure is structural (no presynaptic path), not only the prior (s20, 22 Oct 22:43)
- Rows: 122 types / 2,447 cells, N19 mode 2 (neutral default 0; mode 1 identical outside those cells).
- Scale check against Davis/Ozel on 11 overlapping types: r = 0.63, Davie lower (10x dropout).
- Not a score (Dacks spent). Labels: p derived, crosswalk inferred.
- **Correction (22 Oct 22:51).** The sign isn't robust to 10x dropout. A per-gene scale (Davis p / Davie p, means over the
  143 overlap pairs: 5-HT2A ×2.5, 2B ×8.9, 7 ×4.6, 1A ×1.4, 1B ×3.4; derived, thin, from KC/PAM/L2/T1 only) turns PN net
  5-HT to **+0.06 (adPN) and +0.26 (lPN)**. Davie therefore doesn't settle the PN sign. What holds in both readings is the
  magnitude: at a* = 0.0649 the direct PN input gain is between −1.9% and +1.7%, against Dacks' +15%. Reaching +15% directly
  would need net ≈ +2.3, i.e. near-full expression of every excitatory 5-HT receptor and none of the inhibitory ones. So the
  "route, not the prior" reading rests on magnitude, not on sign. The title's "structural" claim is downgraded to likely.

### F-S20-3: a CRY-dependent TIM light input (night-gated, saturating within minutes) fits all four light-pulse training targets with two fitted values and predicts Lamba's held-out ZT21 advance (+2.89 h against +3.21 ± 0.23 h measured; pass, spent) (s20, 23 Oct 00:09; DECISIONS 22 Oct 23:02, 23:55; 23 Oct 00:09)
- Mechanism (`state:clock|light_input` 1, neutral 0):
  - light activates CRY, and active CRY degrades TIM;
  - the TIM removed pushes the oscillator towards `ct_tim`.
- Values and labels:
  - TIM's DD profile: measured (Shafer 2002 Fig. 6D, s-LNv, pixel read).
  - τ_rec 0.86 h: derived.
  - k_d 13.8/h (half-life 3 min under full CRY): inferred, by rule from Tang 2010.
  - a 10.3/(lux·h): inferred, by rule from Vinayak 2013.
  - τ_c 0.5 h: guessed.
  - k_tim 0.789 and ct_tim 7.59 h: fitted.
- Training (registered bands):

  | target | model | measured |
  |---|---|---|
  | PRC zero crossing | CT 18.80 | CT 18.5 |
  | DD CT15 delay, 60 min | −3.86 h | −4.05 |
  | LD ZT15 delay, 5 min | −2.36 h | −3.1, low side in every variant |
  | lights-on in 12:12 LD | CT −0.54 | CT 0 |

  The s10 pull failed this set (F-S20-1). This input clears it because T is used up, so the response
  saturates by about 1 min of pulse: CT15 delays are −2.86 / −2.93 / −3.86 h for 1 / 5 / 60 min.
- Held out: ZT21, 5 min, 1500 lux, LD assay. Predicted +2.89 h, measured +3.21 ± 0.23 (blind pixel read).
  Ratio 1.11: **pass**.
- Consistency only:
  - The saturating 10 min CT20 advance is +2.11 h, against Vinayak's ~2.4 h.
  - The dead zone (|shift| < 0.25 h) spans CT 3-9.
  - Misses, recorded as limits:
    - The 120 min IRC half-max is 0.014 lux against 0.0025 (the model integrates dose; the fly is 6× more
      sensitive to long dim light).
    - TIM loss right after a threshold pulse is 38% against ≥ 60%.
- Dependence: the result needs active CRY to clear within about 1 h of lights-off. At τ_c 2 h the clock no
  longer entrains, and τ_c is guessed (no in vivo lifetime found).
- The LD TIM waveform has two night peaks. That shape comes from the single Shafer CT20 point; dropping it (V4)
  still passes.
- Validity:
  - s-LNv TIM stands in for the network's light-labile TIM (Tang: DN/LNd TIM, not s-LNv, is degraded at ZT15).
  - One lumped oscillator.
  - Strains and temperatures differ (w1118 at 20 °C, y w at 25 °C).
  - No eye input (the CRY-only route stands in for both).
- Status: N26 stays **partial**. The switch is off in m10f. Adoption needs a stage gate on fly2's current
  frontier plus an organism LD check (DECISIONS 00:09).
- Figures: `docs/media/s20_n26_tim_prc.png` and `docs/media/s20_n26_tim_tim.png`. Runs: `runs/s20/n26/tim/`.

### F-S20-4: N25's s10 sleep values sleep too little (411 min/day), and the published fly two-process set does not reproduce its own stated output or say where its day starts (s20, 23 Oct 00:30; DECISIONS 23 Oct 00:27, 00:30)
- **Reduced loop.** Activity is 0 while the dFB switch is on and 1 while it is off. Steps are 1 min, the clock runs at 24 h, and sleep is scored like DAM (runs ≥ 5 min). Probe: `scripts/probes/s20_n25_sleep.py`; output `runs/s20/n25/checks.json`.
- **Mode 0 (s10 guesses, on in m10f): 411 min/day (28.5 %).** That is below every cited wild-type male value (618-1100 min/day; `docs/research/s20_n25_reads.md` A).
  - The cause is tau_sleep 3 h against tau_wake 12 h, with thresholds 0.6 / 0.3: about 6.7 h awake for every 2.1 h asleep.
  - This holds whatever the brain does, because the homeostat itself switches the dFB on only about 30 % of the time.
- **Abhilash & Shafer 2024 set (mode 1): 1092 min/day (75.8 %),** inside the range. But:
  - **(i) It does not reproduce its own number.** Implemented as published, the discrete rule gives 75.56 % against their stated 74.36 %. τ, update order, transients and step size don't close the gap. Our registered ±1 pp check fails, so nothing was scored.
  - **(ii) The time origin is not stated.** With the thresholds peaking at CT 0, the model sleeps through the day (day 576 > night 516 min). With CT 12 it is night-biased, as their figure is.
- Their thresholds are fixed from a human model (Daan 1984). Only the two taus carry fly data, and they come from a single fitted number (% sleep per day, no errors).
- **Rebound in the reduced loop barely depends on time awake.** The mode-1 gain over the recovery day is 142 / 139 / 138 min after 6 / 12 / 24 h of deprivation (φ = CT 0), or 175-212 min (φ = CT 12). The long, circadian-gated day episode caps it. That conflicts with the dose dependence Huber's abstract states (direction seen, magnitudes not; predictions fixed in DECISIONS 00:34).
- **Held out and unspent:** Huber et al. 2004 rebound (full text not reachable). Nothing was adopted. The switch `state:sleep|values_from_sources` stays neutral (0).
- **Status:** N25 stays **partial**.

### F-S21-1: MB resting rates with plasticity off: one noise level per class passes Huang 2024 by the minimum (6 of 9), and compresses the per-type spread (s21, 23 Oct 01:00; DECISIONS 22 Oct 22:23, 23 Oct 01:01)
- **Fit (labelled fitted).** m10f3, isolated CNS, no stimulus, N21 absent and N22 forgetting 0; grid seed 12 (`scripts/probes/s20_mb_rest.py`).
  - σ*_DAN = 1.477 mV/√ms puts PPL105 at 8 Hz (Huang 2018: 6-10 Hz).
  - σ*_MBON = 2.287 mV/√ms puts MBON14 at 12.1 Hz (Hafez 2023).
  - Both lie inside the 0-3 row bounds (guessed). Output: `runs/s20/mb/sigma_star.json`.
- **Confirm (not held out), seeds 12 / 13.** Pass on both seeds:
  - PPL105 7.63 / 7.63 Hz (band 6-10);
  - MBON14 12.31 / 11.69 Hz (band 9.7-15.1).
  - Class means: DAN 8.0 Hz and MBON 13.2-13.4 Hz. KC, APL and DPM stay at 0 Hz.
  - Whole brain: 0.034 Hz with 0.38 % of cells active, against 0.008 Hz and 0.04 % at σ = 0.5. There was no σ = 0 run, although the registration asked for one.
- **Held-out Huang et al. 2024 Fig. 1 voltage imaging (spent once).** 20 flies per type, from trial spike counts (`scripts/probes/s21_mb_huang_score.py`, `runs/s20/mb/huang_score.json`). Model readout locked first (`runs/s20/mb/model_readout.json`, 01:00).

  | type | model (Hz) | data median [P10, P90] | model / median | result |
  |---|---|---|---|---|
  | PPL1-γ1 (PPL101) | 7.0 | 20.4 [12.8, 25.6] | 0.34 | fail |
  | PPL1-γ2 (PPL103) | 6.5 | 11.7 [8.8, 15.6] | 0.56 | pass |
  | PPL1-α′3 (PPL104) | 14.9 | 7.7 [6.1, 19.4] | 1.92 | pass |
  | PPL1-α3 (PPL106) | 6.2 | 14.0 [10.9, 20.3] | 0.44 | fail |
  | MBON-γ1 (MBON11) | 7.9 | 34.8 [26.2, 49.8] | 0.23 | fail |
  | MBON-γ2 (MBON12) | 11.2 | 20.9 [19.1, 25.3] | 0.53 | pass |
  | MBON-α′2 (MBON13) | 12.1 | 15.6 [11.5, 23.1] | 0.78 | pass |
  | MBON-α′3m (MBON17) | 14.0 | 13.1 [10.1, 16.3] | 1.07 | pass |
  | MBON-α2sc (MBON18) | 11.0 | 9.8 [6.6, 18.0] | 1.13 | pass |
  | fit: PPL1-α2 (PPL105) | 7.6 | 8.5 [7.4, 12.7] | 0.89 | pass (cross-study) |
  | fit: MBON-α3 (MBON14) | 12.0 | 15.2 [11.9, 20.8] | 0.79 | pass (cross-study) |

- **Verdict: PASS, 6 of 9 (the registered minimum).**
  - Two of the passes sit near the band edge: MBON-γ2 at 0.53 and PPL1-γ2 at 0.56.
  - The fit types agree across studies: Huang's PPL1-α2 and MBON-α3 medians lie within ×1.3 of the Huang 2018 and Hafez 2023 targets.
- **What it shows.** One noise level per class carries the order of magnitude, but not the per-type spread.
  - The model spans 6-15 Hz; the data span 8-35 Hz.
  - The γ1 pair (PPL1-γ1, MBON-γ1) and PPL1-α3 fire 2-4× faster in vivo.
  - Huang's flies were on a ball, with walking and rest mixed, so part of the γ-lobe gap may be behavioural state. The model is an isolated CNS.
  - Huang is spent and is not used for a refit. A per-type account would need its own mechanism (intrinsic rows, or input from walking state) and a new held-out source.
- **Leak note.** One PPL1-α′3 trial's spike count was seen in fly2's listing (recorded beforehand). The array shape of one trial was seen while the keys were inspected, after the model readout was locked.
- **Bearing on N21.** At these noise levels, DANs fire at about 6-15 Hz at rest, and Huang's DAN medians are 8-20 Hz. KC → MBON rules must be stable at those DAN rates (fly2's memory-wipe finding).
- **Status:** N3 stays **partial**. Adoption needs a stage on m10f3 with N21 off, the gate, a battery run and a viewed figure (DECISIONS 22 Oct 22:23).

### F-S22-1: N25 homeostat mode 1 (ER5 need, 8 stochastic dFB cells) fits the training data and gives a rebound that grows with deprivation, but only by consolidating nights more than measured flies do (s22, 23 Oct 03:32; DECISIONS 23 Oct 02:58, 03:24, 03:32)
- **Built** behind `state:sleep|homeostat` (neutral 0, the s10 process S). CPU reference path in `src/flyemu/internal_state.py`; the reduced loop in `scripts/probes/s21_n25_homeostat.py`. Implementation checks U1-U3 pass. In organism runs each dFB cell is driven by its own state.
- **Training fit** (4 fitted, shared values on a 14,256-set grid): 140 sets pass the primary checks (Abhilash 2024 total band, night > day, the Liu 2016 BRP anchors, the Liu firing ratio). The falsifier is not hit.
- **Locked prediction for Chowdhury 2023** (held out, unopened): day-1 rebound 99.7 / 150.2 / 174.3 min after 6 / 12 / 24 h (± 3.0 model SEM). Accepted-set spread: 19-157, 22-219, 26-257. Mode 0 and the s20 Abhilash set give a flat rebound (F-S20-4); mode 1 does not.
- **Night bouts (Garbe et al. 2015, SB DAM, iso31 males, own figure read; training).** About 7.0 ± 4.2 bouts per night of 113 ± 70 min, per-fly means up to about 335 min.
  - Accepted model sets: 0.43-4.6 bouts per night of 130-729 min.
  - Locked candidate: 0.64 bouts of 556 min. Outside every measured fly.
- **The prediction depends on that structure.** Sets with mean night bouts ≤ 335 min (32 of 140) predict 82 / 114 / 134 min at the median; ≤ 250 min (17) predict 34 / 61 / 68 min.
  - A fragmented night is reached only with small γ (weak need coupling). With k_r fixed at the measured 1/26 min, the model cannot have both fragmented nights and a strong homeostat.
  - So a Chowdhury score on the locked candidate would test a model whose nights are wrong.
- **Bearing.** Behavioural fit is not evidence for the dFB mechanism: no dFB ON fraction or spontaneous OFF rate has been measured (Pimentel 2016 measured the restart only).
- **Status.** Not adopted, switch 0, N25 stays **partial**. Whether to amend before scoring (T5 night bout ≤ 335 min; its candidate predicts 70.3 / 111.3 / 131.1 min), or to revise the structure first, is for the Director (DECISIONS 03:32).

### F-S22-2: N25 mode 1 cannot match measured day and night bout structure together, even with k_r anywhere in its measured range (s22, 23 Oct 04:09; DECISIONS 03:32, 03:45, 04:09)
- At k_r = 1/25.86 min⁻¹ (measured mean): the best night is 4.6 bouts of 130 min (F-S22-1).
- At k_r = 0.094 min⁻¹ (the measured upper end): 6 of 38 accepted sets reach Garbe-like nights (≥ 2.8 bouts per night, ≤ 183 min; γ 1-4).
  - Every one of them breaks the day into 16-23 bouts of 18-30 min, against Garbe's 8.7 ± 3.3 of 57 ± 25.
  - No set is inside Garbe's mean ± 1 s.d. for both day and night.
- The trade-off comes from one ON → OFF rate whose only light dependence raises it in the day. Day/night bout structure is training data (Garbe 2015, SB DAM, iso31 males), so it can enter the next registration as a check.
- The rebound grows with deprivation in every variant; its size depends on the bout structure (6 h about 50-100 min, 24 h about 90-190 min).
- N25 stays **partial**. The Director chooses between scoring now (locked or T5) and a revision with a night-specific element.

### F-S23-1: frontier stages m10f6 (N26 light input) and m10f7 (MB class noise, N21 off) pass the gate and their unit checks; m10f8 (sourced organ values) passes the gate (s23, 23 Oct 23:33; DECISIONS 23 Oct 22:58, 23:20, 23:31)
- **Gate G, seeds 12-15:** all three stages pass every check: 0.0 non-eye spikes/ms in the silent window, no NaN,
  0 MuJoCo warnings, no class above 200 Hz.
  - m10f6 is spike-identical to m10f3 (0.310 / 0.308 / 0.309 / 0.309 Hz), as predicted. The default world is
    dark, so only the clock's start state differs.
  - m10f7 is 0.337 / 0.336 / 0.337 / 0.337 Hz, up 0.028 as predicted (+0.03). DANs run at 7.8-8.0 Hz and MBONs
    at 12.7-13.9 Hz.
  - m10f8 is identical to m10f7 on every seed. In a 1.3 s dark run with no food, the organ values do not reach
    the spiking network.
- **m10f6 LD check (registered):** the clock read through the stage's registry entrains to 12:12 LD at 1000 lux.
  At the last lights-on the model is at CT −0.54 h, inside ±2 h. Pass.
  - Reported, not scored: after a 6 h phase jump the model re-entrains in one day (CT 0.0 on day 1, −0.54 from
    day 3). Kistenpfennig 2012 is quoted (secondary, not verified) as "within 1 or 2 days". If that holds, the
    model is at the fast edge. Re-entrainment speed is a candidate independent check for the guessed `mu`.
- **m10f7 MB unit check (training targets, isolated CNS):** PPL105 7.6 Hz on both seeds (band 6-10). MBON14 12.3
  and 11.7 Hz (band 9.7-15.1). Pass. This only shows that the stage carries the fitted state. Huang 2024 is spent
  and was not rescored.
- **Test battery (merged tree, before the stage edits):** 299 passed, 0 failed.
- The 60 s smokes for m10f6-m10f8 were still running at this entry. Figure: `docs/media/s23_frontier.png`.

### F-S23-2: at m10f3 rest, glutamatergic MBON inputs give most of the inhibition on MBON11 and the PPL1 DANs, so the MBON→MBON glutamate sign decides the MB output layer's rest state (s23, 23 Oct; `scripts/probes/s23_mb_glu_split.py`, `runs/s20/mb/glu_split.json`)
- Rest drive from MBON inputs, split by the presynaptic transmitter (male-cns `predictedNt`; m10f3 with the s21
  class noise):
  - MBON11: glutamate −988, GABA −158, ACh +32 (net −1,115).
  - MBON12: glutamate −500 (net −487). MBON14: glutamate −336 (net −299).
  - PPL105: glutamate −166, ACh +104 (net −94).
- Glutamate is inhibitory in the model (GluClα), which is the standard reading for MBON→MBON. If it were
  excitatory at these links, MBON11 would flip to about +860, MBON12 to about +510, MBON14 to about +370 and
  PPL105 to about +240. `docs/MEASUREMENT_LIST.md` entry 6 lists the experiments that would decide it.

### F-S23-3: no usable Drosophila value found for body temperature excess, a thermal time constant, a neural Q10, adult hemolymph trehalose, or a walking metabolic multiplier; the metabolic Q10 is now measured (s23, 23 Oct; Sonnet reader, full texts where stated)
- **S5:** no absolute Drosophila body-minus-ambient difference and no thermal time constant. Freoa et al. 2023
  (Sci Rep 13:3513, full text) gives only genotype differences under a lamp (0.6 °C between pigment lines, a
  difference visible within 15 s). S5's required level (body temperature = ambient for a 1 mg fly) stays a
  question for Ben.
- **N28:** no Drosophila neural Q10 with a citable number. The larval NMJ temperature paper (PMID 105927) was not
  reachable. N28 stays partial.
- **S1:** no absolute adult fed trehalose or glucose in mM (Haselton & Fridell 2010 gives relative changes only).
  Flight at 10-15× rest is secondary, and there is no walking multiplier. **Metabolic Q10: Klepsatel, Wildridge &
  Gáliková 2019 (Sci Rep 9:5239, full text), adult males, 13-33 °C, 2.0 Oregon R and 2.3 Canton S.** That is now
  the sourced `q10_met` (2.0, the basal-rate strain). The value is unchanged, so no run changes.

### F-S23-4: the two dry-air water-loss sources in hand cannot set S4's evaporation rate; desiccation stays unscored and unspent (s23, 23 Oct; metabolism reader round 2)
- Lighton & Schilman 2007 (PLoS ONE 2:e1267, full text), as quoted: 0.0617 ± 0.0034 mg/h, Oregon-R males, dry
  air, 25 °C, active. Per fly, that would empty a male's 344 nL of body water (Burggren 2017, derived) in 5.6 h.
  So the number is either not per resting fly or misquoted. This conclusion comes from the body water content
  alone, not from any survival value. Not used.
- Telonis-Scott et al. 2006 state that their 3 h weight loss "may also reflect weight lost through metabolism".
  Not a water-only rate.
- Nayal et al. 2024 Fig. 4B is in ppt per fly per minute at 30 °C and 50 % RH, the denominator is not stated, and
  the value was not extracted.
- S4 stays partial. The held-out desiccation band stays unspent.

### F-S23-5: two of the 23:20 S3 values were mis-sourced and are corrected; N28 gets a measured Drosophila Q10 range but no independent check; no recorded adaptation ratio exists in open full text, so N4 stays blocked (s23, 23 Oct 23:59; `docs/research/s23_crop_pump_q10_adaptation.md`, DECISIONS 23 Oct 23:59)
- **Ingest rate:** the 23:20 derivation (1.05 nL × a 6-7.7 Hz sip rate) took the sip rate from sip duration alone.
  With Itskov's 0.08 s inter-sip interval the rate is 5.0 nL/s (4.4 on sucrose). Pool et al. 2014 gives 6.7-8.8
  nL/s in deprived females at 30 °C. `ingest_nl_s` is now 5.0, derived.
- **Crop capacity:** Edgecomb et al. 1994, cited for 250 nL via a secondary, reports an ordinal crop score, not a
  volume. Measured meals after deprivation are 150 nL (Pool 2014) to 0.27-0.32 µL (Qi 2015), both in females.
  250 nL stays, inferred, inside 150-320.
- **Pump:** measured cibarial pumping is 5-7 Hz (Manzo 2012 ≈6 Hz; Sui 2026 5, 6 or 7 Hz by method), and pump MNs
  burst at 25-90 Hz within each cycle. fly2's `pump_full_rate_hz` (10, guessed) is the last guessed term S3 waits on.
- **N28:** Juusola & Hardie 2001, adult photoreceptor kinetics, Q10 2.3-3.5 (time-to-peak 2.5 ± 0.2, n 3). The
  model's 2.0 lay below it; m10f8 now uses 2.5 (inferred: one cell type stands for all). There is no independent
  check, because every value in that paper comes from the cells that set the value.
- **N4:** no sustained-step early/late rates in any open full text read (PNs, LNs, KCs, LHNs, leg MNs, MN5). Only
  qualitative "adapting" statements exist (MBON-α3, MN5). Seki et al. 2010 defines an adaptation rate for AL LNs
  but is paywalled.

### F-S23-6: the N25 night-input candidate fails Chowdhury 2023 on the 6 h arm; measured rebound does not grow with deprivation length, the model's does (s23, 24 Oct 00:15; DECISIONS 23 Oct 23:30, 23:49, 23:52, 24 Oct 00:15; `docs/research/s23_chowdhury_fig1_read.md`)
- **Fit (training data only).** With the clock's late-night DN1 drive added to the dFB OFF rate (peak CT 19, the
  DN1 Ca2+ peak of Liang 2016, inferred as a firing peak), 2 of 32,340 sets pass the training checks and Garbe's day
  and night bouts. Against expectation, one of the two has the night term at 0; inside Garbe's ± 1 s.d. band the
  night term is not needed, and both sets reach only about 3 night bouts against Garbe's mean 7. The scored set (B,
  night_arousal 8) was chosen by the registered tie-break and survived a 512-fly repeat that the other set failed.
- **Score (blind figure read; Dryad raw data unread).** B predicted 69.3 / 114.4 / 139.9 min of day-1 rebound for
  6 / 12 / 24 h of 20 s-trigger deprivation. The 6 h point is low in every reading (span lower bound 82-110 min);
  12 h is inside; the 24 h primary is inside for panels I and K (148 or 163 min, spans from about 106) and outside,
  high, for panel J (44 min, span 14-75). B fails the pass rule.
- **The published figure disagrees with itself** for the 20 s, 24 h arm: panel I median 196 min, panel J 101,
  while the 220 s boxes agree between the same panels within 1 min. Panel K agrees with I; the Results text agrees
  with J. The J 6 h box also differs from C's although their whiskers match, so the J box reads may be the weaker
  ones, but this read cannot decide. The Dryad raw data would.
- **Shape.** Measured rebound is flat across 6, 12 and 24 h (I reading: 127 / 107 / 148, differences inside 2 SEM)
  or falls with length (J reading and the paper's own test: 6 h significantly above 12 h and 24 h). Every mode 1
  candidate grows with length, because need accumulates with time awake. The only prediction inside all three
  I-reading spans is the flat 00:34 mode 1 φ CT 0 (142 / 139 / 138), which was reported, not scored.
- **What it means.** The rebound magnitude near 24 h is reachable; the dependence on deprivation length is wrong.
  Rebound after only 6 h at night (ZT 18-24) is as large as after 24 h, which a single need variable rising with
  time awake does not give. Chowdhury is spent and N25 stays partial (built, off by default, failed its held-out
  check). No held-out deprivation-length series remains.

### F-S23-7: making the recorded non-spiking VNC hemilineages graded sets off a self-sustaining VNC runaway at rest (s23, 24 Oct 00:29; DECISIONS 24 Oct 00:29)
- **Result.** m10f9 (m10f8 + per-type recorded modes, with IN13B and IN10B graded) fails the silence gate on seed 12:
  7.03 non-eye spikes/ms in the last 100 ms of the silent window (m10f8: 0). Motor neurons outside the leg set
  (0.51 → 8.43 Hz), unassigned VNC locals (0 → 3.20), endocrine (0 → 3.29) and efferent cells (0 → 2.41) start
  and keep firing. The optic recorded modes change nothing in the dark.
- **Why it is not lost spikes.** As spiking cells in m10f8, IN13B fires 0.055 Hz and IN10B 0 Hz.
- **Inferred mechanism (not yet tested).** The model's graded synapse releases from the resting potential upward,
  reaching the guessed 100 Hz-equivalent at threshold. A graded excitatory interneuron sitting a few mV above rest
  therefore excites its targets continuously. IN10B is 254 cholinergic cells. s13 S3 arm A showed the same runaway
  under drive.
- **What it means.** A cell type's recorded mode cannot simply be switched ON while the graded release law is
  guessed. The release curve of VNC nonspiking interneurons is unmeasured in the model's sources. m10f9b (IN10B
  back to spiking, as the 00:20 rule already required for graded-with-spikelets types) tests whether IN10B alone
  is the trigger.
