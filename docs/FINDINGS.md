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
