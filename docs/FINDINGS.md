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
- **Status.** Gate passed on all 8 seeds (12-19); adopted as m9d with the TTMn exclusion (DECISIONS 18:53, result 19:13). Whole-brain rate excluding ORNs rose from about 0.08 to 0.14 Hz on 7 of 8 seeds, source not yet identified (DECISIONS 19:13).

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
