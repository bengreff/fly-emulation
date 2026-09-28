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
