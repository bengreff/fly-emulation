# Decision log

Short records of user decisions and major implementation choices. Newest last.

## 2026-09-14 Session 1 setup

- **Compute:** backhouse GPU (RTX 4070 Ti SUPER, WSL2 Ubuntu 24.04) may be used freely. Set up direct SSH into WSL for long jobs. Existing `/home/greff` content belongs to another project; do not modify.
- **Data access:** user has no neuPrint/Janelia or FlyWire/CAVE account yet and will register on request. Proceed with open releases first (Pugliese code/data, Azevedo Dryad, Zenodo, Caltech Data) and list exactly which registration unblocks which dataset.
- **Budget:** overnight unattended GPU jobs are acceptable. Raw data up to ~200 GB on the WSL disk. Mac keeps no raw data (56 GB free).
- **Repository:** private GitHub repo as canonical remote; checkouts on both the Mac and WSL. Raw data stays out of git.
- **Hardware correction:** README's "RTX 4070 Super" is actually a 4070 Ti SUPER with 16 GB (see ENVIRONMENT.md).
- **Router:** backhouse internet was paused at the eero router on first contact (apt/curl returned an eero "Device Paused" page). User is unpausing it; no tunneling workaround was used.
- **Reporting style:** user has little neuroscience background. Define fly-specific terms on first use; lead with milestone meaning.
- **Cadence:** run autonomously to a first measured result, then report with a run command and the next discriminating test.
- **Git identity:** Ben Greff <ben@thegreffs.com>; applied to new commits only; the first four commits keep the earlier author.
- **Reference code licensing:** Pugliese repo declares MIT in pyproject.toml but ships no LICENSE file; treat as MIT-intended, do not redistribute its bundled data until confirmed.

## 2026-09-14 Session 1, during work

- **CUDA skipped on the PC.** The workload parallelises across cores and the PC has 28.
  Measured CPU throughput there matches the Mac. Building CUDA offline would have added
  ~2.5 GB of transfers and version risk for no gain on this experiment class.
- **High synaptic-scale runs stopped early.** Scales 0.13, 0.2 and 0.3 were killed
  mid-sweep. The trend across 0.03, 0.045 and 0.09 already showed the transition to
  hyperactive and arrhythmic, those runs cost 500+ s per replicate and rising, and they
  were starving the phasic-versus-tonic experiment, which is the discriminating one.
  Rerun them if the transition point itself becomes the question.
- **Reimplemented the rate equation rather than patching the external repo.** Keeps the
  pinned upstream clone clean for provenance. The reimplementation was verified to
  reproduce the external solver path exactly at matched settings before use.
- **Glutamate sweep stopped after four of six points.** 0.03, 0.02, 0.01 and 0.0 complete
  at eight draws, which already show the monotonic collapse; the excitatory points run in a
  hyperactive regime and are very slow, and they were blocking the transmitter-uncertainty
  experiment, which is the more important one. The -0.03 row is a single draw.
- **Two sweeps at a time on the laptop, not three.** Three concurrent sweeps drove load to
  25 on ten cores and slowed everything proportionally.
- **Matched fixed-label control for the transmitter experiment dropped.** The resampled
  24 draws are compared against the existing 16-draw baseline (0.836 +/- 0.119) rather
  than a fresh 24-draw fixed-label run. The comparison is between a bimodal distribution
  and a tight one, so the extra draws would not have changed the conclusion, and the
  capacity went to the corrected-model window sweep, which was producing the more
  interesting result.
- **Proprioceptor-sign comparison and E/I balance sweep not run.** Both were queued and
  released for capacity. The sign question is already answered qualitatively by F10 and
  F12; the E/I question is largely superseded by the corrected-model sweep, which varies
  excitability rather than the excitation/inhibition ratio.
- **Bristle drive at amplitude 12.5 abandoned.** No replicate completed in 24 minutes. The
  mechanosensory bristle population carries a 12.9x gain multiplier under the model's size
  rule (F11), so driving it hard makes the network so active that the adaptive solver
  crawls. The A=5 bristle condition completed and already answers the question
  (rhythmicity 0.039). The intractability is itself a symptom of F11.

## 2026-09-14 Strategy questions, decided by me

Ben asked six framing questions before the session and then said to work from my own
judgement. These are the answers I acted on, recorded so they can be overridden.

1. **Evidence ranking: interventions first, then neural recordings, then behaviour.**
   Acted on throughout. The session spent its compute on controls and perturbations, not
   on making anything look good. The degree-matched shuffle, the drive-target control and
   the threshold-matched control are all intervention-style evidence.
2. **Specimen: the male nerve cord (MANC), by inheritance.** Chosen because the strongest
   executable precedent uses it and because its motor-neuron muscle annotations are the
   best available. Not a considered cross-specimen decision; revisit when the brain is
   needed, since the best brain data is female.
3. **Grain: rate-based, single-compartment, as published.** Kept deliberately. Nothing
   found tonight implicates the neuron model. The problems are sign, strength and
   excitability, which sit above the choice of neuron equation.
4. **Behavioural fitting: not reached, and not needed yet.** There is no behaviour to fit
   to until a leg moves. The physiology-only path has not been exhausted.
5. **End state: unchanged.** Not a live question until a leg works.
6. **Explainers: written.** The session report defines every fly-specific term on first
   use and leads with what each result means for the milestone.

The hypotheses I stated before starting, and what happened to them:

| Hypothesis | Outcome |
|---|---|
| Count-weighted synapses reproduce the rhythm under descending drive | **Confirmed** (F3), robust across 16 draws |
| That rhythm, through muscles with feedback, produces a step | **Untested.** F3 and F6 show the motor output is roughly 13x too weak and a third of it has no muscle to drive |
| Synapse count alone is insufficient; cell-type-specific gains are needed | **Supported indirectly.** F9 and F13 show the result turns on sign assignments, which is the same class of missing parameter |
| A physiology-only model predicts new interventions | **Untested** |
| Dopamine-gated plasticity produces odour learning | **Untested**, belongs to a later milestone |

The prediction I made about the workflow was that the biggest risks would fail early and
visibly on one leg. That is what happened, though not where expected: the failures were in
the model's parameter conventions rather than in the biomechanics.

## 2026-09-15 Session 2: the approach inverted

Ben rejected the session-1 strategy. His argument, which I accept: this is emergent
complexity, not incremental software. You either replicate the organism or you tack
fixes onto an incomplete brain, and an isolated sensorimotor loop is the latter. You
cannot isolate the part of a brain that walks forward, because walking is under
voluntary control and continuously corrected by systems that are not the walking
circuit. A fly is simpler, not different in kind.

This also explains session 1's central negative result better than session 1 did. The
fragment could not set its own operating point because descending drive, sensory
context and neuromodulator state were all absent. Finding F-FRAG has had its scope
narrowed accordingly, and the session-1 report's headline was over-claimed.

- **New first task: a whole-organism field inventory.** Enumerate every quantity the
  organism needs and mark its provenance, before simulating anything. Plan in
  `docs/PLAN.md`.
- **Grain:** per cell type for physiology, per neuron for structure. Roughly 9,000
  annotated types against 176,000 neurons. Chosen because measurements are published
  per type, so rows are fillable and rankable.
- **Boundary:** core loop plus neuromodulator systems, energy and hunger state, and
  circadian and arousal. All four, not a subset.
- **Counting:** one row per shared parameter group with an instance count, and the
  sharing itself recorded as a challengeable assumption. Per-instance counting was
  rejected as unrankable at millions of rows.
- **Run horizon:** hours. This makes every slow-state field load-bearing rather than
  optional, and most of those rows will be empty.
- **Primary graph moves to the whole-CNS male connectome** (F-DATA-2), carrying
  nerve-cord work across by `mancBodyid`.
- **Codebase cleaned.** About 40 fragment-specific files deleted: the runner, eleven
  sweep scripts, the figure and analysis scripts, the fragment result tables, the
  isolated-leg milestone plan and the session-1 report. All in git history at
  `1f7f5a4` or earlier. Kept: the provenance recorder and audit, data-validation
  tests, the queried motor-neuron extraction, the data manifest, and the findings
  restated at field level. Tracked files went from 61 to 21.
- **`runs/` retained on disk though untracked.** It holds the 53 provenance records
  that are the evidence for the surviving findings. Deleting the code that made them
  is fine; deleting the evidence is not.

## 2026-09-15 Session 2: the pack author's response, and three corrections to me

The agent that wrote the starter pack answered the questions in full. It accepted the
ordering error and supplied the precise version of it, plus corrections to three of my
own claims. The plan was rewritten around its schema.

- **F-RETRACTED-1. There was no frequency units bug.** I reported one, made it the
  opening finding and the opening of the session-1 report. The helper returns cycles
  per sample by design and the published notebooks convert correctly: I verified
  `mnFreq/overallParams.sim.dt` in Extended Data Figures 3 and 9 and Figure 2, and
  `freq = 1/period * fps` in the behavioural notebook, at commit `faee4b0`. I called
  their helper without reading their callers, got a nonsensical number, fixed my own
  code, and published my error as their defect. Withdrawn in full.
- **The traced-percentage framing is withdrawn.** "94% against 23%" is the fraction of
  `:Neuron` nodes whose `status` reads `Traced`, and `:Neuron` is itself a
  threshold-based inclusion. The dominant nerve-cord category is status *absent*,
  75,643 nodes, which is a different statement. Segment counts differ fourfold on
  imaged volume. Verified directly. The practical case for the whole-CNS graph stands
  on the brain, 1,454 proprioceptors and 673 of 708 cross-references.
- **Sensitivity is not correctness.** Flipping the glutamate population's sign and
  watching activity collapse shows leverage, not that either uniform assignment is
  right. Session 1's framing implied otherwise. Resolving it needs postsynaptic
  receptor evidence.
- **Electron microscopy is not categorically unable to resolve gap junctions.** The
  limitation is that these chemical-connectome releases provide no comparable
  electrical reconstruction. Unknown electrical coupling must not become measured
  absence.
- **Type count corrected to 11,751** distinct `type` labels in `male-cns:v1.0`, over
  164,506 typed neurons, verified by query. My "~9,000" was recalled, not checked.
  Any grouping below that number now needs a recorded rationale.
- **The Melis finding is a limitation for causal reuse, not a defect in its original
  science.** Future fluorescence can legitimately inform retrospective reconstruction.

Adopted into `docs/PLAN.md`:

- **Requirement schema of eight columns** with seven status values, replacing my five.
  Observations and model parameters are separate objects; partially constrained is not
  filled; shared inference dependencies are counted as rows, or propagating one assumed
  conductance to 5,000 neurons makes the inventory look complete while adding nothing.
- **Identifiability as the governing frame.** Some quantities are recoverable only in
  combination, so the inventory must record which rows are only jointly identifiable
  under a stated observation set.
- **Competing causal hypotheses before parameter changes**, each naming a distinguishing
  observation. Missing context masquerades as missing physiology, which is precisely
  session 1's error.
- **A minimum behaviour set of six capability rows** defining which fields are required,
  with courtship, reproduction and sleep behaviour marked later scope rather than
  omitted.
- **Separate replication from endorsement**, and **"not implemented" never means
  "biologically inactive."**
- **Five meaning-based sanity checks** now in `tests/test_source_data.py`, since
  ordinary tests encode the same assumptions as the implementation. Twelve tests pass.
- **Cloud budget reasoning corrected.** Hours of simulated time does not itself demand
  more resident memory than seconds; runtime, retained recordings and differentiating
  through long trajectories are the separate costs.

## 2026-09-15 Session 2: sanity review of the plan, seven changes

Reviewed the plan for soundness rather than re-reading it approvingly. Seven problems,
all fixed.

- **The circularity was unaddressed.** `model_use` cannot be filled without choosing
  equations, and the equations determine the requirement list. Added step 0: declare
  the model family M explicitly, with its omissions listed, before enumerating. The
  inventory is indexed by M, which is why the output form is always "for model family
  M and assay set A".
- **The horizon was untiered and unaffordable.** Queried the real graph:
  `male-cns:v1.0` has 25,862,574 neuron-to-neuron edges over 125,024,863 synapses. At
  a generous 10^10 edge-updates/s that is ~2.6 wall-hours per simulated hour at 1 ms
  and ~26 at the 0.1 ms a 200 Hz wingbeat needs. A single long demonstration is
  affordable; a replicate-heavy sweep at that horizon is not. Now tiered: seconds with
  hundreds of replicates for sensitivity, minutes for assays, hours once or twice.
- **The measured-only control cannot run, and the plan promised it anyway.** With over
  80% of type-specific physiology unresolved there are no time constants, thresholds or
  efficacies to integrate. Redefined as three controls reported together: C0 strict
  refuses to run and the row list it refuses on is the result; C1 fills one declared
  default per subsystem; C2 uses what the precedents assume. C0 against C1 measures how
  much of the model is convention.
- **The scaffold step conflated two jobs.** Split into 5a, instantiate and let it fail
  loudly with no integration, which is cheap and is the actual completeness test, and
  5b, integrate once 5a passes.
- **Sensitivity was a hope, not a step.** Ten tier-A sensitivity experiments are now
  budgeted against the top of the ranking, with results written back into the
  uncertainty column.
- **Five subsystems were missing from the table.** Glia, which are annotated in the
  primary graph, absent from every model here, and do potassium buffering plus sleep
  and circadian roles that sit inside the chosen boundary. Also humoral and hemolymph
  signalling, sensory organ mechanics as distinct from transduction, wing hinge
  mechanics, and efferent modulation of sense organs.
- **The type count needed a policy, not a number.** 11,751 distinct `type` labels over
  164,506 typed neurons. Any grouping below that is an assumption and now requires a
  recorded rationale. Step 0b.

## 2026-09-15 Session 3: build the simulation, emit the inventory from it

Ben rejected the plan's ordering a second time, and more sharply: *"I do not
understand. You should be building a simulation of a fly, just with currently
unknown parameters. If that is how you build a simulation, do it."* Then, on the
goal: *"a fly in a full MuJoCo sim with mostly guessed parameters, probably
randomly flailing around."*

That settles a question two sessions had circled. The deliverable is a running
embodied organism; unknown parameters are simply unknown, and flailing is the
expected outcome rather than a failure. The hand-written requirement skeleton
(plan steps 1-3) is not a prerequisite for it and was not built.

- **The inventory is emitted by the model, not maintained beside it.** Every
  biological quantity is read through `flyemu.registry`, which records entity,
  property, units, the equation that needs it, status, evidence and instance
  count. The requirement list is a byproduct of a run, so it cannot be
  incomplete relative to the code. This replaces plan step 1 and makes step 5a
  ("fail loudly on missing fields") the default rather than a later check.
- **Model family M v1 declared** in `docs/MODEL_M.md` before anything was
  built, with its omissions listed explicitly. Spiking LIF, single compartment,
  current-based synapses, per-neuron structure, per-cell-type physiology.
- **Neuron model: spiking LIF**, chosen by Ben over rate-based. It makes
  membrane time constants and thresholds explicit required fields instead of
  hiding them in a gain, which is the field F-EXCITE-1 showed being set by an
  artefact.
- **Primary graph: `male-cns:v1.0`**, whole CNS, male. Cached locally by
  chunked live query: 176,422 neurons, 25,862,574 edges, 125,024,863 synapses,
  reproducing the numbers `docs/PLAN.md` derived independently.
- **Register for FlyWire/CAVE.** Agreed with Ben, not yet done; it is what
  unblocks the female datasets for physiology transfer and a BANC comparison.
  Not blocking, so session 3 did not wait on it.
- **Body: NeuroMechFly via flygym 2.1.0**, all 126 joint degrees of freedom,
  **torque actuators rather than position servos**, because a position servo is
  a controller the fly does not have. Ground-contact sensors are disabled: in
  flygym 2.1.0 they are emitted with unprefixed object names and the model fails
  to compile. Contact is read per body segment instead.
- **Model units established by measurement, not assumption:** mm, s, g, so
  force is µN and torque µN·mm. A test pins it, because every torque number in
  the project is meaningless if this drifts.
- **Three fill policies, not one model.** C0 strict enumerates every unresolved
  requirement and refuses to integrate; C1 fills one declared default per
  subsystem; C2 should use published precedents. Strict was changed to enumerate
  all refusals rather than raise on the first, since the refusal list is the
  result.
- **C2 was not populated.** Its values currently equal C1's, so the two runs are
  identical and C1-versus-C2 says nothing. Recorded as an open item rather than
  presented as a control.
- **Swept parameters are recorded as `assumed` with the override noted**, never
  promoted to evidence. A test enforces it.
- **Fetch stalled once and was rewritten.** A single query over a wide bodyId
  range hung for 65 minutes with no data and 1.3 s of CPU. bodyIds are strongly
  skewed (90% below 8.1e5, then a jump to 1.5e9), so chunks are now by quantile
  with per-chunk parquet checkpoints and retries. The whole graph then arrived in
  205 s.

## 2026-09-15 Session 3: fidelity direction set

Ben, after seeing a ball-and-stick render: *"First goal is full body biological
fidelity, both visual and underlying."* Then, as standing direction:
*"In general, tend towards a higher fidelity model, including all relevant
physics, the brain body interface must be complete."*

This settles three things that were previously open.

- **Default to higher fidelity.** Where a choice exists between a cheaper
  abstraction and a more faithful mechanism, take the faithful one and record
  the cost. Reductions are still allowed but each now needs a reason beyond
  convenience. This reverses the implicit bias of M v1, which chose the cheapest
  defensible option at nearly every point.
- **All relevant physics is in scope.** Rigid-body contact alone is not the
  target. Tarsal adhesion and claw mechanics, unsteady aerodynamics, air flow
  for wind sensing, acoustic near-field for hearing, light transport for vision,
  odour advection and diffusion, and humoral transport are all inside the
  boundary, to be added or explicitly deferred with a recorded gap. "Not
  implemented" still never means "biologically inactive".
- **The brain-body interface must be COMPLETE.** Completeness here means every
  channel the animal has is either implemented or recorded as a known gap with
  its instance count. The current state is far from that: 328 of 708 motor
  neurons drive anything, 3,246 of roughly 20,000 sensory neurons receive
  anything, and vision, olfaction, taste, hearing, wind, gravity, temperature
  and all hormonal signalling have no channel at all.

Also decided:

- **Agent discipline.** Ben: *"NO SUB SUB AGENTS! max 3 agents!"* I had launched
  four `general-purpose` research agents, which fanned out to 22 live agents in
  three minutes. All were killed; none of their output was used. The limit is
  now in `CLAUDE.md`: at most three subagents, counted recursively, and never an
  agent type that can spawn its own. `Explore` cannot spawn and is the default
  choice. Ben then authorised one additional agent specifically for the
  brain-body interface enumeration, making four Explore agents for this round.

### Body-model defects found while fixing the render

- **`colorize()` was never called**, so all 70 geoms carried MuJoCo's default
  grey in the physics model, not merely in the viewer. Now applied: 13 materials,
  graded cuticle browns per leg segment, dark red eyes, translucent wings.
  NeuroMechFly stores these colours in procedural *textures* with material rgba
  left at [1,1,1,a], so reading `mat_rgba` alone yields a uniform grey fly; the
  exporter averages the texture and multiplies it in.
- **Eye joints are actuated.** The `ALL_BIOLOGICAL` joint preset plus
  `ActuatedDOFPreset.ALL` gives 126 powered degrees of freedom including three
  per compound eye. Fly compound eyes do not articulate on the head capsule, so
  those are rigging artifacts turned into muscles. Pending the joint audit,
  several others are suspect: the individual tarsal joints and the
  funiculus-arista joint. Every such DOF lets the model move in a way no fly can.

## 2026-09-15 Session 3: body model switched to flybody, and the physics filled in

Ben asked whether the body's physics were realistic and implemented, and
observed legs clipping through the body and each other in the visualiser. They
were not, and he was right about the cause.

**Verified, not assumed:** every one of the 70 geoms had `contype=0` and
`conaffinity=0`, and the only contacts in the model were 55 explicit pairs, all
of them with the ground plane. There was no leg-to-leg, leg-to-body or
wing-to-body collision of any kind.

### Body model: flybody, decided on measurement

Ben declined to pick and asked for a careful decision, noting NeuroMechFly might
hold more brain-body interface data. Checked directly; it does not.

| | NeuroMechFly | flybody |
|---|---|---|
| Segment masses | another lab's fractions x an assumed 1 mg | 52 flies weighed part by part |
| `boundmass` floor | yes: 32 of 69 bodies floored, 2.45% of mass is solver artefact | none |
| Joint ranges | **0 of 127** | **102**, fitted to real annotated poses |
| Passive joint parameters | one global stiffness and damping for every joint | 8 differentiated groups |
| Actuator parameters | one global force range | per-class force ranges and affine gains |
| Aerodynamics | absent | quasi-steady fluid model, air density and viscosity set |
| Adhesion | absent | 8 adhesion actuators |
| Tendons | none | 8 |
| Vision config | 721 ommatidia per eye | **identical file** |
| Non-joints in the rigging | eyes, arista, 3-axis halteres | **none of them** |

The last row decided it. flybody's rigging independently omits exactly the
degrees of freedom the joint audit identified as not being joints, from a
different method: it has no eye DOF, no arista DOF and one haltere axis. Two
approaches reaching the same answer is better evidence than either alone.

The port was cheap because **leg joint names are identical between the models**,
so the muscle map and the sign calibration carried across. NeuroMechFly remains
selectable as `Body(model="neuromechfly")` for comparison.

Measured after the switch: 0.9846 mg total, none of it a solver floor; 98 motor
actuators; 8 tendons; 6 adhesion; 103 joints all with ranges; 1.3x slower than
real time WITH self-collision enabled.

### Signs are now derived from measurement, per body model

The switch exposed a latent error in the design: `FTi pitch +` FLEXES the leg in
NeuroMechFly and EXTENDS it in flybody. Hard-coded signs invert silently the
moment the body changes.

So the muscle table now declares the anatomical ACTION (flexion, levation,
protraction, adduction, rotation), from Azevedo et al. 2024 Table A1, and the
SIGN is resolved at build time against `data/derived/joint_signs_<model>.csv`,
measured by `scripts/calibrate_joint_signs.py`. 16 of 18 muscle rows are now
`derived` rather than `assumed`; the two remaining assumptions are the rotation
directions, which the sources genuinely do not settle.

### Physics implemented

- **Self-collision.** Two bugs had to be fixed to get it working. Setting geom
  `contype`/`conaffinity` alone changes nothing, because **MuJoCo prunes
  candidate pairs at the BODY level first** using masks aggregated at compile
  time, which were zero. And colliding everything creates permanent contacts
  between segments that nest at their joints - a convex hull of the rostrum
  overlaps the haustellum it sits in - which fight their own joints. Resolved
  with one collision bit per anatomical region, colliding across regions and
  not within them. `spec.add_exclude` was tried first and hard-crashed the
  compiler with no traceback.
- **Adhesion**, driven by the long tendon motor pool, since that muscle's real
  target is the pretarsal claw. Declared as a scaffold: adhesion is a substitute
  mechanism, not claw and pulvillus mechanics.
- **Aerodynamics**, MuJoCo's quasi-steady fluid model in air (1.204e-6 g/mm^3,
  1.825e-5 g/mm/s) with ellipsoid fluid interaction on wings and halteres.
  Recorded for what it is: it does NOT capture delayed stall and the
  leading-edge vortex, rotational circulation, or wake capture, which dominate
  insect flight at Reynolds number ~100.
- **Cuticular strain proxy.** Campaniform afferents now read the load
  transmitted through each leg segment (`cfrc_int`) instead of ground contact
  force. A loaded leg need not touch the ground at all, so contact force was
  the wrong physical quantity. The segments are still rigid, so this is a proxy
  and not a strain field; that limitation stays in the inventory.
- **Tendons**, real MuJoCo tendons for the tarsal chain, replacing the emulated
  coupling.

### Known limitation introduced, recorded rather than hidden

flybody's thorax-coxa Euler axes are not aligned with the anatomical action
axes, so one actuator can serve two actions: positive roll both protracts and
adducts. The resolver picks the axis with the largest component, which means the
sternal adductor and the pleural promotor currently share an axis and a sign.
The better treatment is to project each muscle's action across all three axes by
least squares, giving genuinely multi-axis muscles. Not done.

## Session 4 (24 September 2026)

- **Inclusion policy: `Traced` or typed** (F-COUNT-2). `connectome.build(statuses=None)` restores all nodes for comparison.
- **Promote "predict a published result" ahead of per-type biophysics.** Per-type values exist for few of the 11,751 types; differentiating the rest would multiply guesses without adding anatomy. The discriminating test for F-GAIN-1 is whether noise-free, sensory-driven activity follows identified pathways, scored against published interventions (Shiu et al. 2024; flybench task set). See `docs/PLAN_NEXT.md`.
- **Community reproductions are evidence, not ground truth.** Several unreviewed GitHub projects run Shiu-style LIF on MaleCNS in closed loop with flybody. Use their reported numbers only as cross-checks we re-derive.

### Pre-registration: adaptation test (session 4, before any scoring)

- Mechanism: spike-triggered adaptation current, identical for every neuron. Each spike adds `a` mV to an adaptation variable that decays with `tau_a` and is subtracted from the membrane's steady-state drive.
- Values: `a = 2 mV`, `tau_a = 200 ms`, borrowed unchanged from flybench's adaptation model (recorded `assumed`; not tuned here). Fly neurons show adaptation on ~100 ms-1 s scales, but no per-type measurement is used.
- Scale: re-set by the same return-to-rest rule (`scripts/calibrate_gain.py`, sugar GRNs only, largest passing scale on the same grid plus 1.2, 1.5, 2.0).
- Scored held out, unchanged from F-GAIN-2: water→MN9, bitter→MN9 (and whether it ignites), sugar+bitter suppression, GF→TTMn, DNg100→leg rhythm.
- Success means: no ignition in any held-out assay at the calibrated scale, and water→MN9 and bitter suppression appear. GF→TTMn is expected to still fail (gap junction).

**Result (session 4):** adaptation test failed its pre-registered criteria (bitter still ignites ~9,000 neurons at the calibrated 0.7x; water→MN9 still 0; bitter now drives MN9 at 5.6 Hz). Not adopted. Recorded as F-SFA-1.

### Pre-registration: sensory terminals do not generate spikes (session 4, before scoring)

- Change: synapses onto sensory neurons (every `superclass` containing "sensory"; 17,896 neurons, 1.4% of synapses) get zero efficacy. Rationale: sensory spikes start in the periphery; central synapses onto sensory axon terminals are presynaptic modulation, which a single-compartment neuron cannot represent without wrongly making the terminal fire. Registry key `connection_class:onto_sensory_terminals|included` (1 = old behaviour). Adaptation off.
- Found by a diagnostic probe on bitter ignition, so bitter-, sugar-, water-, GF- and DNg100-assay outcomes are **no longer held out** and are reported as "seen".
- Scale: re-set by the same return-to-rest rule on sugar GRNs.
- Fresh held-out assays, never run before this entry: JO-C/E→aDN (DNg62, DNge078) >5 Hz; JO-F→aDN >5 Hz; JO-F→MDN >5 Hz (inferred from behaviour); JO-C/E→MDN <2 Hz (null); LPLC2→DNp01 >5 Hz. Sources: Hampel et al. 2015, 2020; Bidaye et al. 2014; Ache et al. 2019. Thresholds follow flybench conventions. Stimulus 100 Hz. Each also runs on shuffled graphs.

**Result:** fresh held-out 2/5 (F-SENS-1). Adopted as profile `m1`.

### Pre-registration: size-scaled input resistance (session 4, before scoring)

- Change: each synapse's efficacy is multiplied by `(median size / postsynaptic size)^alpha`, with size the neuPrint voxel volume of the traced body. This stands in for input resistance falling with cell size. Primary alpha = 1, following Pugliese et al. 2025 (gain divided by and threshold multiplied by median-normalised size). alpha = 0.5 is exploratory only. No clipping. Registry key `cell_type:all|size_scaling_exponent` (0 = m1).
- Motivation seen before scoring: pIP1 (125x median size, 21k inputs) carries JO-C/E→MDN. That null is therefore no longer blind and is reported as "seen".
- Scale: the same return-to-rest rule.
- Primary held-out scorer: flybench v0.2.1 (MIT, commit 3052ce5) on its own male-cns build (neuPrint, >= 5 synapses), with our changes applied inside an adapter. Scored tasks are those this project has **not** examined: 07, 08, 09, 10, 11, 13, 14, 16, 17, 18, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31. m1 and m1+size are each scored at their own calibrated gain.
- Adopt size scaling if it passes more of those tasks than m1 and does not lose JO-C/E→aDN or LPLC2→GF. Report per-task results either way.

### Independent review (session 4) and resulting fixes

A read-only reviewer agent audited session 4. Accepted and fixed:
- **Bug: rewired controls carried the old target's postsynaptic efficacy.** Since F-SENS-1, shuffled graphs gave sensory neurons central input again (and would have mis-applied size factors). Efficacy is now `psp_mv * post_gain[post]` and every control recomputes it. All earlier m1 "shuffled" columns are superseded.
- Delay was D-1 steps (1.7 ms, not 1.8). Now exactly D, with a test.
- A Poisson kick during refractory was dropped; it is now held and lands on the first free step, as Brian2 PoissonInput does.
- Calibration now takes the last passing scale before the first failure, not the largest passing one.
- Findings text overstated "load-bearing": a global shuffle shows only that SOME wiring structure matters.

Not yet acted on: the rhythmicity metric needs ISI-shuffled surrogates and antagonist cross-correlation. Removing input onto sensory terminals also removes real presynaptic inhibition (e.g. GABAergic suppression of sugar GRNs, Chu et al. 2014); a multiplicative output-gain treatment would be better. Size scaling as implemented scales efficacy only, not Pugliese's threshold form, and it mostly amplifies optic-lobe columnar cells.

### Pre-registration: type-level vs neuron-level wiring (session 4)

- Nulls: global rewiring and cell-type block-preserving rewiring (`connectome.type_shuffled`), each recalibrated by the same return-to-rest rule, plus each at the real graph's scale.
- Readouts: the full 11-assay battery under m1 (fixed code).
- If type-shuffled graphs reproduce the real graph's passes (JO-C/E→aDN, LPLC2→GF, sugar→MN9) and its failures (JO-C/E→MDN, ignition), the claim is "type-level wiring is load-bearing" and neuron-level identity is not yet tested by these assays. If they do not, neuron-level anatomy matters for that assay.
- Also scored: the five F-SENS-1 fresh assays on the pre-change model (sensory input kept, same scale), to test whether the change helped at all.

**Results:** size scaling rejected (F-SIZE-1). Type-block null behaves like the real graph in calibration (sugar→MN9 survives, ignition at the same scale); the full battery is running.

### Pre-registration: short-term synaptic depression (session 4, before scoring)

- Mechanism: Tsodyks-Markram depression per presynaptic neuron (all its output synapses share one resource `x`). A spike's efficacy is multiplied by `x`, then `x -= U*x`; `x` recovers toward 1 with `tau_rec`. A rested synapse has its old efficacy, so feedforward onset is unchanged and sustained high-rate firing is attenuated.
- Values: `U = 0.5`, `tau_rec = 500 ms`, uniform, recorded `assumed`. Motivation: strong depression at fly ORN→PN synapses (Kazama & Wilson 2008) on 100 ms-1 s recovery scales; not a per-synapse measurement, not tuned here.
- Scale: the same return-to-rest rule (stop at the first failure), on m1.
- Scored on a fixed set declared now: our 11 assays (all seen, reported as such), plus flybench tasks 07-31 as run for m1 in F-FB-1 (also seen for m1). There is no fresh held-out set left for this family, so this comparison is **exploratory**, not confirmatory.
- Considered an improvement if, at its calibrated scale, it passes water→MN9 or JO-F→aDN (both failing everywhere so far) without losing sugar→MN9, JO-C/E→aDN or LPLC2→GF, and does not fall below m1's flybench pass count.

**Result:** STD rejected (F-STD-1).

### Calibration rule v2 (session 4)

Return to rest after sugar alone did not guarantee stability for other inputs (F-TYPE-1). v2 requires return to rest after each of: sugar GRNs, and 4 random populations of 40 sensory neurons drawn (fixed seed) from sensory types used in **no** assay (JO, LB, LPLC2 and GRN types excluded). It stays non-behavioural, and no assay stimulus is used except sugar. Chosen scale: the last passing one before the first failure.

### Pre-registration: conductance-based synapses (session 4, before scoring)

- tau_m dV/dt = -(V - V_rest) - g_e (V - E_e) - g_i (V - E_i). g_e and g_i are dimensionless (relative to leak) and decay with tau_s. An excitatory synapse adds eff/(E_e - V_rest), an inhibitory one |eff|/(V_rest - E_i), so a single PSP at rest matches the current-based model. E_e = 0 mV, E_i = -70 mV (chloride-type GABA_A/GluCl; assumed, not per type). Everything else as m1.
- Compared with m1, both under calibration rule v2, on the 11-assay battery with 2 type shuffles and 1 global shuffle. All assays are seen, so this is **exploratory**. An improvement means more assays passing (criteria as in F-SENS-1/F-GAIN-2) with none lost.

**Results:** rule v2 fails at every scale for current- and conductance-based m1 (F-LN-2). The conductance variant is not adopted: sugar-stable to 0.8x, but no calibratable scale under v2.

### Pre-registration: identified electrical synapses of the giant fibre system (session 4)

- Mechanism: spike-triggered, rectifying electrical transmission. A presynaptic spike adds `k` mV to the postsynaptic membrane on the next step (held through refractory). There is no subthreshold coupling. It stands in for shakB gap junctions, which carry the presynaptic action potential that a LIF model does not represent.
- Pairs: DNp01 (GF) → TTMn and DNp01 → PSI (Tanouye & Wyman 1980; Phelan et al. 1996; Allen et al. 2006). Each GF couples to the TTMn and the PSI it makes most chemical contacts with.
- `k = 20 mV` (a coupling coefficient of ~0.25 times an ~80 mV spike), assumed. Chosen so a single GF spike fires TTMn, which the animal does 1:1. So GF→TTMn is now a **fitted** assay, not a test.
- Held out: GF→PSI→DLMn. PSI→DLMn is chemical, ~225 synapses per PSI, sign by Shiu profile. Published: GF activation drives DLMn at short latency, following 1:1 at low rates. Pass: DLMn mean rate ≥ 50% of GF rate at 50 Hz GF drive, and > 5 Hz at 100 Hz.

**Result:** held-out GF→DLMn failed (F-GJ-1; originally cited as F-GAP-1). The electrical step works; PSI→DLMn chemical efficacy is subthreshold. Kept as an option, default off.

### Pre-registration: input-count normalisation (session 4, before scoring)

- Efficacy onto neuron j multiplied by `(median N / N_j)^beta`, where N_j is j's total input synapse count in the modelled graph (>= 5-synapse edges). This is homeostatic scaling, the reviewer's alternative to volume. Primary beta = 1; no clipping. Registry `cell_type:all|input_normalisation_exponent`.
- Written expectation, before running: it will fail like F-SIZE-1, because N_j correlates with size (factors: pIP1 ~0.02, GF ~0.02, MN9_L ~0.06).
- Calibration rule v1 (sugar return-to-rest, first failure); battery: sugar→MN9, JO-C/E→aDN, LPLC2→GF, JO-C/E→MDN, water→MN9, JO-F→aDN, GF→DLMn (electrical on). Adopt only if it keeps sugar, JO-C/E→aDN and LPLC2→GF and newly passes at least one of water, JO-F, GF→DLMn or the JO-C/E→MDN null.

### Pre-registration: m2, antennal-lobe corrections (session 4, before scoring)

Derived from ignition diagnostics (F-LN-1, F-LN-2, `scripts/probes/al_*.py`), not from any olfactory physiology assay:
- (i) Chemical output of cholinergic AL local neurons onto PNs and onto other cholinergic AL LNs set to 0. eLN→PN is electrical in the animal (Yaksi & Wilson 2010); eLN→eLN is unmeasured. Their output onto other LNs is kept.
- (ii) AL local neurons whose predicted NT is 'unclear' (89 of 420) are treated as inhibitory. Literature: AL LNs are predominantly GABAergic or glutamatergic (Chou et al. 2010; Das et al. 2011). Shiu's default was unknown → excitatory.
- m2 = m1 + (i) + (ii). Scale by calibration rule v2 (odour-containing generic populations included).
- Scored: rule v2 passes at all (m1: fails everywhere). flybench olfactory physiology tasks 08, 17, 18, 26, 27 (graded, vs m1 in F-FB-1). The full 11-assay battery, reported as seen.
- Adopt m2 if rule v2 is satisfiable at a scale where sugar→MN9_L > 5 Hz, and mean graded score on 08/17/18/26/27 does not fall below m1's.

**Result:** m2 meets both criteria. Rule v2 is satisfied at 0.165 mV, with sugar→MN9_L 7.5/93.5 Hz. Mean graded score on flybench 08/17/18/26/27 is 0.80 vs m1's 0.54, with two new passes. **m2 adopted** (F-AL-1). Input-count normalisation rejected (F-NORM-1). GF electrical synapses kept as an option (F-GJ-1).

## Session 5 (25 September 2026)

- **Evidence labelling rule (user requirement):** every quantity, in code, inventory and reports, is labelled **measured**, **derived** or **inferred** (plus **unknown** when no value exists). The registry's `basis` column implements it. Measured means observed directly. Derived means computed from measurements by a stated transformation. Inferred covers fitted values, assumed guesses, borrowed precedents and priors; `status` keeps that finer distinction. Reports label numbers the same way.
- **Strategy (agreed):** constrained ensemble fitting at cell-type grain with hierarchical priors, against a frozen, split library of measurements; the type-preserving null is a standard control. See PLAN_NEXT.
- **Blank-ledger grain (declared):** see `scripts/blank_ledger.py`. Neuron biophysics per cell type; synaptic strength factorised as presynaptic release x postsynaptic gain (not per type pair, which would be ~millions of slots with no constraining data); glutamate sign per postsynaptic type; monoamine action per modulatory type; transduction per sensory group. Changing a grain is a recorded decision.

## Session 6 (25 September 2026)

### Pre-registration: morphological conduction delays and Hallem ORN rates (before any scoring)

**Delays (1a).** Per presynaptic cell type: `delay = t_syn + L / v`.
- `L` is the median geodesic distance from the soma to the cell's own presynaptic sites. It is sampled (300 sites) on one neuPrint skeleton per type (`scripts/skeleton_lengths.py` → `data/derived/skeleton_lengths.csv`). Derived.
- `v = 0.5 m/s` for all types except the giant fibre. Inferred: central axons are 0.3–1 µm across. Scaling √d from the GF (7 µm, 2.07 m/s; Kadas et al. 2019) gives 0.4–0.8 m/s; larval axons (0.4 µm) give 0.2 m/s (Kottmeier 2020).
- Giant fibre (DNp01): `v = 2.07 m/s`, measured in adults 24 h after eclosion.
- `t_syn = 0.5 ms`. Inferred: a typical chemical synaptic delay; a model estimate for the GF NMJ is 0.35 ms. No central fly measurement was found.
- Types without a skeleton (untyped cells) keep the shared default.
- The switch is `cell_type:all|morphological_delays` (1 = on).
- Peripheral conduction of sensory axons outside the CNS volume is not included. It is recorded as absent.

**ORN rates (1b).** ORNs fire as Poisson processes at SFR in clean air and at up to Rmax with odour. Values are from Hallem & Carlson 2006, heterologous (`data/params/orn_rates.csv`). This replaces the 15 mV scale.

**Criteria, fixed now. These are regression checks, not tests of a biological hypothesis; no held-out assay is involved.**
1. `sugar_mn9 --profile m2 --rates 100,200`: MN9_L > 5 Hz at 100 Hz and at 200 Hz. The old values were 7.5 and 93.5 Hz; the new values are reported whatever they are.
2. Closed loop, 1 s at `force_per_spike=10`:
   - no runaway, and the brain is quiet again within 300 ms of silencing all sensory input;
   - excluding ORNs, the whole-brain mean stays < ~1 Hz;
   - uniglomerular PN mean rate in clean air lies within 1–20 Hz. The range is inferred from PN spontaneous rates of a few Hz (Wilson et al. 2004; Bhandawat et al. 2007).

A change that fails a criterion stays in the code as an option but is turned off by default, and the failure is reported.

### Pre-registration: standing (session 6, before any scoring)

**Reference heights, derived from the body model.**
- Neutral pose (flygym FLYBODY_NEUTRAL spring rest, legs rigid): thorax 1.235 mm above the tarsal tips.
- Limp body (zero torque): 0.665–0.708 mm over 0.1–1 s, still sinking.
- Session-6 closed loop at `force_per_spike=10`: 0.64–0.70 mm, indistinguishable from limp.

**"Stands"** means all four of the following. The fly is dropped from the spawn pose and lands at about 0.1 s.
1. Thorax z ≥ 0.90 mm throughout t = 0.5–1.5 s. 0.90 mm is about 73% of the neutral-pose height and 0.2 mm above limp.
2. With all motor output silenced (motor-neuron spikes not delivered), the same run falls below 0.80 mm. This rules out passive support.
3. The body is upright: thorax roll and pitch magnitudes < 45°.
4. No self-sustaining network state (the closed-loop criterion 2 above).

**Resistance reflex test, reported separately and not part of "stands".**
- Stimulus: impose a 30° flexion of one middle-leg femur-tibia joint for 200 ms by an external torque, with the fly standing or not.
- Readout: the summed signed torque from that leg's FTi motor units during the push, compared with no push.
- Resistance means the torque opposes the imposed movement, i.e. is extensor for a flexion push.

**Changes to be tried in this order.** Each is scored on the criteria above and reported whether it passes or fails.
- (a) Measured-form proprioceptors, following SENSORS_MECHANO:
  - claw cells: position sigmoids with thresholds spread across the measured ranges;
  - hook cells: direction;
  - club cells: movement;
  - hair plates: ThC/CTr limits.
  The claw/hook/club assignment of cells is guessed.
- (b) Slow tibia-flexor MNs given their measured resting rate, ~30 Hz (Azevedo 2020 Fig 3D), as tonic drive.

No parameter is tuned against the standing criterion. If it fails, the report names the failing layer.

### Pre-registration: re-test of Hallem ORN rates under the post-fix model (session 6, 22:31)

The model has changed since F-ORN-2 failed:
- the joint range and proprioceptor index are fixed;
- measured-form proprioceptors are in;
- slow MNs fire tonically;
- the joint signs were re-measured.

Seeds 0–5 have been seen: all six return to rest with ORN rates on. **Fresh seeds 6–11** are scored on the unchanged criterion 2:
- non-tonic spikes in the last 100 ms after sensory silencing = 0 in every seed;
- whole brain excluding ORNs < 1 Hz;
- uPN mean 1–20 Hz.

`orn:all|rate_calibration` becomes default 1 only if all 6 pass.

## Session 6b (26 September 2026)

### Pre-registration: slow flexor MN fitted to intrinsic data, reflex held out

**Data.** Azevedo et al. 2020 Dryad cell 180111_F2_C1: an R35C09 slow tibia flexor MN in whole-cell current clamp (`scripts/azevedo_slow_mn.py`). Only the authors' spike detections are used, and only non-excluded trials.

**Fit set: intrinsic properties only.**
- Spontaneous rate: 24.8 ± 7.7 Hz.
- Rin: 1,041 MΩ (measured).
- τm: 16 ms (fit to hyperpolarising steps; measured).
- f-I: −31.6 / 0 / +31.6 / +62.9 pA gives 0.5 / 24.8 / 69.2 / 95.8 Hz.

With injected current converted to mV by Rin, an LIF with reset = rest fits all four points:
- θ (threshold − reset) = 32.6 mV;
- t_ref = 4.27 ms;
- tonic drive = 36.45 mV.

All three are fitted (inferred). They are applied to the 60 flexor MNs classed slow by size rank (inferred matching). τm is transferred from one cell to the class, also inferred.

**Held out: the leg-movement responses of the same cell.** None of these data were used in the fit. The model protocol is `scripts/probes/reflex_gain.py`, extended as follows:
- the thorax is tethered;
- the left middle FTi is held by the PD probe at θ0 = 90° anatomical (Azevedo: tibia about 90° to the femur at rest);
- flexion steps of 0.8, 2.4 and 8° start at θ0;
- extension steps start at θ0 − 8° (the measured 8° flexed offset) and move by 0.8, 2.4 and 8°;
- 8° extension ramps run at 40, 80 and 120°/s;
- the readout is the mean rate of the model's left-middle slow flexor MNs (7 cells), with windows as in the data.

**Criteria.**
- C1, sign: Δhold > +5 Hz for the 8° and 2.4° extension steps, and Δhold ≤ 0 for the 8° flexion step.
- C2, magnitude: Δhold for the 8° extension step lies within [10, 40] Hz. The measured value is +20.3.
- C3, velocity: the extension-ramp transient Δ rises from 40 to 120°/s. The measured values are +36 → +49.
- Pass = C1 and C2. C3 is reported either way.

**Written expectation.** The fitted cell responds about 1.35 Hz per mV, against about 7 for the old guessed cell. Unless the circuit delivers about 15 mV of net depolarisation for 8° of extension, C2 fails. Nothing in the reflex arc is tuned on these data.

**Result, 06:40.** Fail. For the 8° extension step, Δhold is +1.0 Hz against +20.3 measured; all conditions fall within ±3 Hz. The fitted resting rate of 24 Hz is reproduced, and the clamp is within 1°.

**Diagnosis.** Every left-middle claw and hook afferent fires at 0 Hz, both at 82–90° and after the step. The guessed mV transduction (2 mV baseline + 8 mV × signal against a 7 mV threshold) leaves the whole population subthreshold near the resting knee angle. The motor neuron's synaptic input changes by less than 0.3 mV.

### Pre-registration: rate-coded leg proprioceptors, one scale fitted, fresh split (06:45)

**Change.** Leg chordotonal and hair-plate afferents become Poisson rate generators, as the ORNs are:
- rate = r_max × signal, with signal ∈ [0, 1] from the existing claw/hook/club/hair-plate forms (unchanged);
- dead time equals the cell's t_ref;
- r_max is one scalar for all of these cells: **fitted** (inferred).

No FeCO spike rates exist for the adult fly. Registry switch: `afferent:leg_proprioceptors|rate_mode`.

**Fit set:** the 8° extension-step Δhold of cell 180111_F2_C1 (+20.3 Hz) only. Grid: r_max ∈ {50, 100, 200, 400} Hz. Pick the value closest to 20.3.

**Held out, fixed now:**
- extension steps of 2.4° (+20.0) and 0.8° (+3.1);
- flexion steps of 0.8° (−5.9), 2.4° (−9.3) and 8° (−4.1);
- extension ramps at 40/80/120°/s (transient Δ +36/+46/+49; hold +22/+28/+27);
- flexion ramps (transient about −8).

**Criteria:**
- H1: sign right in ≥ 6 of 8 step and ramp hold values, excluding the 0.8° conditions, which lie within the measured noise;
- H2: 2.4° extension step Δhold within a factor of 2 of +20;
- H3: extension-ramp transient > extension-ramp hold at every speed. This is the measured phasic component.

**Also reported:** closed-loop stability over 6 seeds, and standing (secondary, not a criterion).

**Result, 06:49.** The fit fails. The 8° extension Δhold at r_max 50/100/200/400 is −0.6/+0.6/+1.6/−1.4 Hz, against +20.3 Hz. Afferents now fire and respond: at 200 Hz, flexion-claw cells go from 18.9 to 10.5 Hz and hook cells respond. But the MN's synaptic input changes by ≤ 0.3 mV. Not adopted as it stands, and the held-out set was not run. The limiting layer is now afferent→MN transmission.

### Pre-registration: VNC sensorimotor efficacy, fitted on the same single target (06:51)

r_max is fixed at the grid-best 200 Hz. Fit `connection_class:vnc_sensorimotor|efficacy_scale` ∈ {1.5, 2, 3, 5, 8} on the 8° extension-step Δhold (+20.3 Hz) only. Pick the value closest to 20.3.

This is a second parameter fitted after a failure, recorded as such. Held-out set and criteria H1–H3 are unchanged from above.

**Adoption** as the default requires all of:
- H1 and H2 pass;
- stability holds over 6 seeds;
- sugar→MN9_L stays > 5 Hz (the brain edges are untouched, so this is expected).

**Result, 06:54.** The fit fails. The MN's net synaptic input at the pre-step position is −0.3, −3.4, −19.5, −46 and −94 mV at scales 1.5, 2, 3, 5 and 8. Slow MNs are silenced from 3× up, and Δhold never exceeds +1 Hz. Scaling the VNC uniformly amplifies a tonic net inhibition, not the reflex. Not adopted.

### Pre-registration: glutamate onto tibia flexor MNs is excitatory (hypothesis; 06:58)

**Motivation (post-hoc, from anatomy after the failures above).**
- 453 of 1,568 input synapses onto the left-middle slow flexor MNs are glutamatergic.
- The largest inputs are IN21A002 (168) and IN21A006 (~90 per cell). IN21A006 receives mainly extension-direction afferents.
- Under the uniform inhibitory-glutamate convention, passive extension then inhibits the flexor, which is the wrong sign for the measured resistance reflex.
- Glutamate's sign is set by the postsynaptic receptor (GluCl vs iGluR). No measurement for these MNs was found. Label: **guessed hypothesis**.

**Change.** `glutamate_receptor_sign` = +1 for postsynaptic types "Ti flexor MN" and "Acc. ti flexor MN" (cell_types.csv rows). Everything else as in the last fit: r_max 200 Hz, VNC scale 1.

**Test.** Held-out set and criteria H1–H3 unchanged. The fit-set value (8° extension Δhold) is reported, but not tuned.

**Adoption requires:**
- H1 and H2;
- stability over 6 seeds;
- sugar→MN9_L > 5 Hz.

Otherwise the row stays in the table with a scope switch off, and the result is reported.

### Pre-registration: VNC transmission fitted to interneuron position tuning (07:40)

**Seen held-out comparison (F-VNC-2).** Across 73 model T1-left IN13B cells, the median Vm-angle slope is 0.000 mV/deg (p90 0.0013). Agrawal 13Bα, 15 cells: 0.012–0.083, median 0.046.

**Fit set:** the 13Bα static-tuning median slope, 0.046 mV/deg. The model statistic is the median slope over all T1-left IN13B cells. This is conservative, since 13Bα is a subset of 13B.

**Grid:**
- afferent rate mode r_max ∈ {0 (mV mode), 200, 400} Hz;
- VNC sensorimotor efficacy scale ∈ {1, 2, 3}.

Pick the grid point closest to 0.046 in log ratio.

**Held out:**
- the same slope for T1-left IN10B cells, measured slopes to be extracted from 10Bα swings by the same binning, after the fit is chosen;
- 6-seed stability;
- sugar→MN9_L > 5 Hz.

The Azevedo cell 180111 reflex is reported but is not a test (seen).

**Adopt only if** all hold:
- the fitted slope is within a factor of 2 of 0.046;
- the IN10B slope sign matches;
- stability and sugar pass.

**Result, 07:57.** Fail. The T1-left IN13B median slope is −0.0005 to 0.000 mV/deg at every grid point (r_max 0/200/400 × VNC scale 1/2/3). Nothing is adopted, and the held-out 10Bα slope was not extracted.

**Confound found after scoring.** male-cns reconstructs only 3 (left) and 2 (right) claw axons for the front legs, against 25–32 per middle and hind leg. T1-left 13B cells receive no claw synapses; 408 of 24,149 input synapses come from FeCO or hair plates. The recorded preparation (T1) therefore cannot be matched in this connectome.

**Exploratory addendum, not pre-registered.** Left-middle-leg 13B cells (72), fraction with slope > 0.012 mV/deg:
- mV mode: 3%;
- r_max 200: 11%;
- r_max 200 with VNC ×2: 46%, but of both signs, with p10/p90 ±0.3 mV/deg (too steep).

Measured 13Bα is uniformly positive, 0.012–0.083.

## Session 6c (26 September 2026, late morning)

### Pre-registration: do the slow-MN parameters transfer to a second cell? (intrinsic data only)

Cell 181021_F1_C1 is a second R35C09 slow tibia flexor MN. Its Piezo (reflex) trials are **sealed** as the fresh held-out reflex test; only CurrentStep trials are analysed here.

**Predictions** from the 180111 fit (θ 32.62 mV, t_ref 4.27 ms, drive 36.45 mV, τ 16 ms):
- P1: spontaneous rate within ±30% of 24.8 Hz, i.e. 17.4–32.2 Hz.
- P2: τm within ±30% of 16 ms.
- P3: f-I. At each tested current, the LIF with the fitted θ, t_ref and drive, and current converted by **this cell's measured Rin**, predicts its rate within max(30%, 5 Hz).

**Pass** = P1–P3. A pass supports transferring one cell's fit to the 60-cell class. A fail means the class needs a distribution, not a point value.

**Result.** Pass on all three.
- P1: spontaneous rate 23.5 ± 3.2 Hz.
- P2: τ 15.5 ms.
- P3: f-I at −55/−28/+27/+54/+105 pA, measured 0/0.6/62.6/80.8/106.7 Hz against predicted 0/0/51.5/69.4/95.3 Hz, all within tolerance. The model is systematically ~11 Hz low above rest.

Cell 2 has Rin 617 MΩ against cell 1's 1,041, so input resistance varies 1.7× within the class. Class transfer of the point fit is supported, with the caveat that Rin is not in the LIF: synaptic mV are not scaled by it.

### Pre-registration: leg proprioceptor subtypes from the BANC crosswalk (11:02)

**Data.** BANC v888 metadata (Harvard Dataverse doi:10.7910/DVN/7WTH1N, CC BY 4.0, `banc_888_meta.feather`) gives, per neuron:
- `cell_sub_class`: leg claw, hook or club chordotonal; leg hair plate; neck chordotonal; prosternal hair plate;
- a reviewed `malecns_cell_type` match. Rows prefixed "auto:" are NBLAST matches of lower confidence.

Each male-cns type takes the majority subclass over reviewed matches. Auto matches are used only where no reviewed match exists. Label: **derived** (annotation plus cross-dataset match).

This replaces the session-6 guessed assignment, which was wrong for SNpp47 (club, not claw), SNpp51 (claw, not hook), SNpp39/41 (hook, not club), SNpp56–60 (club, not hook), SNpp19 (prosternal hair plate) and SNpp17/18/22 (neck chordotonal). Non-leg types stop being driven as leg afferents.

**Direction.** Flexion vs extension tuning is not in BANC. It is re-derived with the unchanged wiring rule (`scripts/proprio_direction.py`, resistance-reflex prior) on the corrected subtypes. Still inferred.

**Protocol.**
1. Dev: score the candidate on the already-seen cell 180111 with `score_reflex.py`, in two configurations: defaults, and rate mode 200 Hz (the earlier grid best, not refit).
2. The sealed cell 181021 is opened only if a configuration passes H1 and H2 on the dev cell. That configuration is then scored once on 181021, and the result decides adoption.
3. The subtype correction itself is adopted regardless, because it replaces guesses with data. Standing and stability are re-run and reported.

### Pre-registration: AL spontaneous state vs measured PN rates (11:06)

**Target (measured).** "In the absence of odors, PNs fire spontaneously (typically 1–5 spikes/sec)" (Kazama & Wilson 2009 Nat Neurosci, Discussion; DOI unverified).

**Current model (F-AL-2):** uPN median 0 Hz, mean 6 Hz, 30% active.

**Mechanism.** Much LN inhibition is presynaptic on ORN terminals (GABA-B, Olsen & Wilson 2008), with an unmeasured postsynaptic share. Knobs:
- `connection_class:inhibitory_AL_LN_to_PN|postsynaptic_scale` s ∈ {1, 0.5, 0.25};
- `presynaptic_inhibition_gain` k ∈ {0, 0.1}.

**Fit statistic:** the uPN median rate. Pick the grid point with median in [1, 5] Hz and the largest active fraction. That point is **fitted**.

**Criteria and held-out checks:**
- A1: ≥ 70% of uPNs active (> 0.5 Hz).
- A2: mean uPN rate ≤ 10 Hz.
- Stability over 3 seeds.
- sugar→MN9_L > 5 Hz.

Odour-response tasks (flybench 08/17/18/26/27) are the proper held-out test; they are too slow for this session and are deferred. Until then, adoption is **provisional**, labelled "fitted to spontaneous rate only".

**Result, BANC subtypes (11:13).** On the dev cell 180111, both configurations fail:
- defaults: H1 0.50;
- rate mode 200 Hz: H1 0.40;
- every Δ is within ±3 Hz. H2 and H3 fail.

**The sealed cell 181021 stays sealed.** The subtype correction is adopted as data. With correct sensor identities the failure remains at the premotor operating point (F-AZ-2).

**Result, AL grid (11:22).** Fail. Over s ∈ {1, 0.5, 0.25} × k ∈ {0, 0.1}:
- the uPN median rate is 0 Hz at every point;
- the active fraction is 0.25–0.45;
- the mean rises from 4.9 to 14.1 Hz as postsynaptic inhibition is removed, because already-active PNs fire harder.

Nothing adopted; the knob stays at neutral 1.

Silent PNs are under-excited rather than over-inhibited. Their ORN input is ~5 mV against a 7 mV threshold, in a noise-free LIF.

Next, a measured constraint on ORN→PN transmission:
- the spontaneous EPSC rate of 74.9 ± 8.6 Hz per DM4 PN (Kazama & Wilson 2009);
- unitary ORN→PN EPSP amplitude and reliability (Kazama & Wilson 2008);
- then an AL-specific efficacy fitted to those, with odour responses held out.

## Session 6d (26 September 2026): workflow and documentation

- **Procedure is written down.** `docs/WORKFLOW.md` owns the procedure:
  - session lifecycle; evidence labels; the pre-registration template;
  - fit / dev / held-out / sealed data splits; a post-hoc budget of 2 repairs per target;
  - the unverified-foundations rule; controls; data acquisition; process hygiene;
  - which document owns which content; Ben's review checklist.
- **The six evidence labels, recorded retrospectively.** measured / derived / inferred / guessed / unknown / absent. Fitted, borrowed and cross-cell-transferred values are inferred. This scheme has been in force since session 5 (enforced by `Registry.validate()`), but no DECISIONS entry stated it. The session-5 bullet above lists only four labels.
- **Model family M2, recorded retrospectively.** Per-type LIF from `data/params/cell_types.csv`, with graded transmission, neuromodulator pools, short-term plasticity, Q10 and the session-6 switches. It was adopted in session 5 (F-LEDGER-3) without an entry here.
  - This superseded the session-4 bullet "promote predicting a published result ahead of per-type biophysics". The per-type machinery was built, but it is filled only where data exists.
  - `docs/MODEL.md` now documents M2.
  - Naming: M2 is the family, m2 the profile. The working model is `profiles.WORKING_PROFILE` / `WORKING_MIN_SYNAPSES`, and the run scripts default to it (they previously defaulted to no profile and 1-synapse edges).
- **Documentation restructure.**
  - Superseded plans, the original brief, the multi-session handoff and the session-6 log moved to `docs/archive/`.
  - HANDOFF and PLAN_NEXT are rewritten each session rather than appended to.
  - The FINDINGS index was added.
  - The duplicate ID F-GAP-1 was split: the GF electrical-synapse finding is now F-GJ-1.
- **Unused dependencies removed** (jax, diffrax, hydra, omegaconf, sparse, seaborn, scikit-learn, natsort, tqdm, psutil, jupyter). Provenance now records the versions of the packages actually used. The removal broke `RunRecord` while the suite stayed green; a test now covers it.

### Corrections to the record (entries above are not edited)

- "Result, BANC subtypes (11:13)" sits under the AL pre-registration heading. It belongs to "Pre-registration: leg proprioceptor subtypes from the BANC crosswalk (11:02)".
- "Pre-registration: glutamate onto tibia flexor MNs is excitatory (06:58)" has no result line. Its result: fit-target Δhold −0.3 Hz against +20.3; not adopted. The row is in `data/params/hypotheses_not_adopted.csv` (F-AZ-2). Later evidence also argues against it: GluCl dominates in MNs (Lesser 2024).
- In session 4, "Results: size scaling rejected (F-SIZE-1)" sits under the type-level pre-registration. It belongs to "Pre-registration: size-scaled input resistance".

## Session 7 (26 September 2026)

### Pre-registration: ORN→uPN transmission set from measured unitary EPSP and depression (13:28)

**Change.** Two measured constraints, neither fitted to PN firing rates:
1. `connection_class:ORN_to_uPN|efficacy_scale` = **10.9**. The measured unitary EPSP is 6.19 ± 0.45 mV (Kazama & Wilson 2008 Neuron 58:401, Results, n = 23 PNs, minimal nerve stimulation at 0.033 Hz, so undepressed). The male-cns median ORN→uPN connection (edges ≥ 5 synapses) has 22 synapses, matching Tobin et al. 2017 EM (~23). The model PSP kernel (τm 20, τs 5 ms; peak 0.156 × weight) gives 0.57 mV there at efficacy 0.165 mV/synapse. 6.19 / 0.57 = 10.9. Label **inferred**: the input is measured, but the kernel is borrowed.
2. `afferent:ORN|measured_depression` = 1. Every ORN output synapse depresses to 0.78× per spike and recovers with τ = 893 ms (Nagel, Hong & Wilson 2015, Fig 1c single-component fit, DM6/VM2). The model's depression rule has the same form. Label **inferred** (a published fit, applied to all ORN targets).

Variant **M** adds `connection_class:ORN_to_uPN|homeostatic_matching` = 1. It normalises each uPN's ORN edges so that its median ORN connection has the same uEPSP, because KW2008 Fig 4B finds uEPSP similar across glomeruli (p > 0.43) although uEPSC differs.

**Motivation.** F-AL-3: silent PNs are under-excited (ORN input ~5 mV against a 7 mV threshold). The measured unitary EPSP is 11× the model's.

**Fit set.** None for PN rates. The values come from the uEPSP (KW2008) and the depression fit (Nagel 2015), which are not PN spontaneous rates.

**Held out.**
- The uPN spontaneous rate: "typically 1–5 spikes/s" (KW2009 Discussion, qualitative), plus the F-AL-2 target of ≥ 70% active.
- flybench olfactory tasks 08/17/18/26/27, run only if the rate criteria pass (m2 baseline 0.80).

**Criteria (probe `pn_silence.py`, clean air, 2 s runs, rates over 1–2 s, 3 seeds):**
- A0 (median uPN rate in 1–5 Hz): primary.
- A1: ≥ 70% of uPNs > 0.5 Hz.
- A2: mean ≤ 10 Hz.
- Stability over 3 seeds; sugar→MN9_L > 5 Hz.

**Adoption.** The configuration (base or M) that passes A0–A2 and the regression checks becomes the default. If both pass, M is adopted, because it is supported by the Fig 4B measurement. If neither passes, both stay as options, off.

**Expectation (written now).** PNs are **over**-driven. At Hallem SFR (median ~12 Hz), steady-state depression leaves ~20–40% of the resource. The mean ORN drive is then ~2–4× the threshold gap for most uPNs, and the median rate is > 10 Hz. If so, the borrowed operating point (V_rest −52, threshold −45) becomes the suspect. GW2009 estimates rest with ORN input at −55 to −60 mV. The next unverified item would be PN threshold or rest, not the synapse.

**Seed-0 result (13:33, provisional; seeds 1–2 running).**

| Config | active | median | mean |
|---|---|---|---|
| base | 0.32 | 0 Hz | 6.3 |
| P | 0.68 | 9.0 Hz | 23.3 |
| M | 0.64 | 5.0 Hz | 28.5 |

In P, silent uPNs have a median of 99 ORN synapses, against 1,414 for active ones: they have little ORN input. Well-innervated PNs are overdriven, as expected.

### Pre-registration: post-hoc repair 1 of 2 for the AL target, uPN resting potential (13:34)

**Motivation (post-hoc, from the seed-0 overdrive).** A shot-noise estimate from measured quantities:
- the DM4 ORN rate is 3.4 Hz (KW2009);
- depressed EPSPs are ~4 mV at that rate (Nagel 2015 parameters);
- the EPSC rate is ~75 Hz.

These give a mean PN depolarisation of ~9 mV with SD ~3.7 mV. Firing at 1–5 Hz then needs threshold − rest ≈ 15 mV, but the borrowed gap is 7 mV. Gouwens & Wilson 2009 (J Neurosci; PMC2709801, Discussion) measured whole-cell rest at −47.8 ± 1.6 mV (n = 12, antennae removed). They estimate that −57.8 mV is needed to match cell-attached firing, i.e. the seal-leak-corrected rest.

**Change.** uPN `v_rest` = `v_reset` = −57.8 mV. Label **inferred** (a model-based correction by GW2009 of a measured value). `v_th` stays at −45 (borrowed), so the gap is 12.8 mV. Tested through a candidate-rows file (`FLYEMU_EXTRA_PARAMS`), not the live table.

**Configs:** P and M, each with the rest change. The criteria (A0–A2, 3 seeds) and the adoption rule are unchanged. Nothing is tuned: −57.8 is used as published.

**Result, P and M (3 seeds, 13:37). Fail; neither adopted.**
- P: active 0.68 / 0.67 / 0.64; median 9 / 10 / 8 Hz; mean 23.3 / 23.0 / 23.2. Fails A0, A1 and A2.
- M: active 0.64 / 0.62 / 0.63; median 5 / 5 / 5 Hz (A0 passes at the boundary); mean 28.5 / 28.3 / 28.6. Fails A1 and A2.
- The expectation of overdrive was right for the mean. The median rose less than predicted (9 rather than > 10 Hz).

### Pre-registration: VNC premotor operating point from the synaptically set MN rest rate (13:37)

**Motivation.**
- Azevedo 2020: the slow flexor MN's ~25 Hz resting rate is set synaptically, so the real premotor network is tonically active at rest.
- Agrawal 2020: 13Bα rest in a graded range of −57 to −39 mV.
- The model's premotor cells are silent (F-AZ-2), and the slow MN fires only because of a fitted intrinsic drive (36.45 mV; unverified-foundations list).
- The rest rate belongs to the network. Moving it there sets the premotor operating point from a measurement rather than a guess.

**Change.**
1. Slow flexor MN `spontaneous_drive` = 0 (its intrinsic drive is removed).
2. VNC intrinsic neurons (type regex `^IN`; 12,775 cells) get one tonic `spontaneous_drive` d (mV), standing for unmodelled tonic input (descending, background). Label **inferred** (fitted).
3. Leg proprioceptors are in rate mode at r_max = 200 Hz (the session-6b grid best, not refit). In mV mode the afferents are silent near 90°, so no reflex is possible.

**Fit set.** The resting rate of the left-middle slow MNs at θ0 = 90°, tethered, equals the Azevedo cell-1 spontaneous rate of 24.8 Hz (seen). Grid d ∈ {2, 3, 4, 5, 6} mV; pick the value closest to 24.8. If none is within ±50%, stop: the mechanism cannot set the rest rate.

**Dev test (no held-out claim).** `score_reflex.py --cell 180111_F2_C1` with H1 and H2 as before.

**Sealed test.** Only if H1 and H2 pass on dev: score 181021_F1_C1 **once**; this decides adoption.

**Also required for adoption:** closed-loop stability over 3 seeds (0 non-tonic spikes after silencing, with the tonic population excluded from "non-tonic") and sugar→MN9_L > 5 Hz.

**Expectation.** The whole-VNC drive either leaves the MN below 24.8 Hz at every d ≤ 6, or tips the VNC into runaway near threshold (d ≈ 5–7). If a d fits, the reflex gain rises but its sign is uncertain: the net premotor input is inhibitory-dominated (F-AZ-2), so H1 is likely to fail.

**Result, AL repair 1 (3 seeds, 13:38). Fail; not adopted.** The rows stay in `data/params/candidates_s7_pn_rest.csv` (not live).
- PR (P + rest −57.8): active 0.60 / 0.60 / 0.59; median 7 / 6 / 6 Hz; mean 18.0 / 17.7 / 18.1.
- MR (M + rest −57.8): active 0.60 / 0.59 / 0.59; median 3 / 2 / 3 Hz (A0 passes); mean 20.0 / 19.9 / 20.0.
- A1 and A2 fail in both. The population is bimodal: silent PNs receive ~−21 mV of mean LN inhibition, while active ones fire at ~20 Hz.
- **Structural ceiling found after scoring:** 67 of 329 uPNs have fewer than 100 ORN synapses (40 are thermo- or hygrosensory PNs, driven by HRN/TRN). No ORN-side change can activate more than ~80%.

Post-hoc budget for this target: 1 of 2 used.

**Result, VNC operating point (13:40). Stop rule met; not adopted.** Left-middle slow MN rest rate (step:-8 pre-window) with the intrinsic drive removed:

| d (mV) | 0 (control) | 2 | 3 | 4 | 6 |
|---|---|---|---|---|---|
| MN rate (Hz) | 0 | 0 | 0 | 0 | 0 |
| MN mean synaptic input (mV) | −0.2 | −0.3 | −1.1 | −1.0 | −2.2 |

Raising VNC excitability recruits inhibitory premotor cells first: IN13A005/009 (GABA) at 30–56 Hz, and glutamatergic IN21A002 at 60 Hz by d = 6. Cholinergic premotor cells (IN21A004, IN03A004) stay near silent. No d is within ±50% of 24.8 Hz, so the net premotor input to the slow MN is inhibitory at every operating point. Depolarising the whole VNC uniformly cannot produce the synaptically set rest rate. Candidate rows stay in `data/params/candidates_s7_vnc_d*.csv` (not live).

**Identification (2a), derived from male-cns wiring plus BANC.**
- 13Bα candidate: **IN13B013**. It has the largest claw share of input among T2/T3 IN13B types (8.6%) and the BANC `cell_function` "proprioception"; it is GABAergic, 1 cell per hemisegment. It projects to interneurons (IN14A005, IN23B009, ...), not to MNs.
- 10Bα candidates: **IN10B041 / IN10B058** (club input 26% / 21%; IN10B058 is BANC-proprioception).
- Label: inferred. Agrawal's genetic lines are not matched to male-cns types in any source found.

### Pre-registration: 13Bα static tuning, layer check (13:40)

**Question.** Does the model's IN13B013 (T2L) reproduce the 13Bα Vm–angle slope? This is a check of the sensor→interneuron layer; nothing is fitted.

**Protocol.** `azevedo_reflex.py` with the tethered PD hold at θ0 ∈ {50, 90, 130}°. Readout: IN13B013 T2L ΔVm from rest in the pre window. Two configs: default (mV-mode sensors) and rate mode r_max 200.

**Criterion.** A least-squares slope over the 3 angles of +0.012 to +0.083 mV/deg (the measured 13Bα range, depolarising with extension; median 0.046).

**Also reported, not scored:** IN10B041 / IN10B058 slopes. The 10Bα data are not yet extracted, so no comparison is made.

**If the check fails,** fitting a graded operating point (2b) cannot fix the slope. The failing layer is then afferent→IN transmission.

**Result, 13Bα layer check (13:42). Fail.** IN13B013 T2L ΔVm at 50 / 90 / 130°:
- mV mode: −0.57 / −0.50 / −0.51 mV, slope +0.001 mV/deg;
- rate mode 200: +1.44 / +1.89 / +1.73 mV (at 56 / 91 / 127°), slope +0.004.

Measured 13Bα: 0.012–0.083. Claw afferents do respond in rate mode (79–94 Hz at their preferred extreme), but the interneuron moves ~0.3 mV over 70°, about 10× short. That is the same shortfall as ORN→PN. Graded operating-point fitting (2b) cannot fix a slope, so it is not attempted.

### Pre-registration: transfer the measured first-order sensory synapse to leg proprioceptors (13:43)

**Motivation.** Both first-order sensory synapses tested this session fall short by the same factor:
- ORN→PN: measured unitary EPSP 11× the model's;
- claw→13Bα: tuning slope ~10× too small.

No leg-afferent unitary PSP was found. The one measured first-order synapse in the fly CNS is transferred, **not fitted**.

**Change (config T).**
- `connection_class:leg_proprioceptor_output|efficacy_scale` = 10.9, applied to all output edges of the 21 driven leg-proprioceptor types (`proprio_assignment.csv`, non-empty subtype).
- `afferent:leg_proprioceptors|transferred_depression` = 1 (U 0.22, τ_rec 893 ms).
- Rate mode r_max 200 Hz. This was not refit; it is the session-6b grid point, labelled inferred. In mV mode the afferents are silent.
- Labels: inferred (cross-class transfer). Nothing is tuned on any leg datum.

**Tests, criteria fixed now.**
1. **Held out:** 13Bα layer check, the same protocol; IN13B013 T2L slope in [+0.012, +0.083] mV/deg.
2. **Dev:** `score_reflex.py --cell 180111_F2_C1 --tag s7-transfer`, H1 and H2.
3. **Sealed:** only if 2 passes, score 181021_F1_C1 once.
4. **Adoption** needs 1 and 3, plus stability (3 seeds) and sugar→MN9_L > 5 Hz.

**Expectation.** 13Bα may reach the range, since the slope scales roughly with efficacy. The reflex is less likely to pass: amplified afferents also drive the inhibitory premotor cells (VNC result above), so the sign is uncertain.

**Result, config T (13:49). Fail; not adopted; the sealed cell stays sealed.**
- **Held-out 13Bα check:** IN13B013 T2L +1.15 / +2.10 / +0.99 mV at 55 / 91 / 128°. Non-monotonic, slope ≈ −0.002 mV/deg; fail.
- **Dev reflex:** H1 sign agreement 0.70 (the best so far; 0.40–0.50 before), H1 fails at < 0.75. Hold Δ is within ±1.3 Hz against +20 Hz measured, so H2 fails. H3 fails.
- **Diagnosis (arithmetic, after scoring).** With U 0.22 and τ 893 ms, steady-state delivered drive ∝ r/(1 + U·r·τ). It saturates at 1/(U·τ) ≈ 5 spikes/s once r ≫ 5 Hz. Rate-mode claw cells run at 80–95 Hz at their preferred angles, so a depressing synapse there transmits **changes, not static position**. The static 13Bα tuning therefore needs one of: low tonic afferent rates (≲ 5–10 Hz), non-depressing afferent synapses, or a non-synaptic route. In the model these are unconstrained, because leg-afferent rates and depression are both unmeasured.

### Pre-registration: post-hoc repair 1 of 2 for the 13Bα target, transfer the efficacy without depression (13:49)

**Change (config T′).** As config T, with `afferent:leg_proprioceptors|transferred_depression` = 0. Motivation: the saturation diagnosis above (post-hoc).

**Criterion (unchanged).** IN13B013 T2L slope in [+0.012, +0.083] mV/deg over 50 / 90 / 130°.

**Also run:** the dev reflex, **reported only**. The dev target has had more than two post-hoc attempts across sessions 6b–7, so it no longer gates anything by itself. The sealed cell is opened only if the 13Bα check passes **and** H1 and H2 pass on dev.

**Result, config T′ (13:58). 13Bα check fails:** IN13B013 −2.73 / −6.66 / −3.61 mV at 68 / 90 / 114°, non-monotonic. **The probe also failed to hold:** 50° and 130° became 68° and 114°. Dev reflex H1 = 0.40, but the stimulus was not delivered (next entry). Post-hoc budget for the 13Bα target: 1 of 2 used.

### Protocol correction: the reflex probe must deliver the stimulus (13:56)

In T′ (and partly in T), the leg generated enough torque to beat the PD probe (kp 3 µN·mm/deg):
- T′ starts at 87.5° instead of 82°;
- T at 85.5°;
- holds drift back toward 89°.

Azevedo's piezo imposes the position. Earlier configs held within 0.5° only because the leg produced almost no torque. A probe that yields to the leg changes the stimulus, so these scores are not valid tests.

**Changes.**
1. `score_reflex.py` now refuses to score, **with the cell unopened**, if any condition misses its start or end angle by > 1.5°.
2. The probe stiffness for all scoring from now on is kp = 100, kd = 0.133. A gain test under T′ gave errors of 3.0 / 1.1 / 0.3° at kp 10 / 30 / 100, with no instability.

This is a stimulus correction, not a model change. T and T′ are re-scored on dev with the stiff probe; their 13Bα checks are unaffected (static holds, reported as achieved). The criteria (H1, H2) are unchanged.

**Results with the stiff probe, standing and stability (14:08).**

Dev reflex, kp 100 (clamp error ≤ 0.5°):

| Config | H1 | H2 | H3 | Notes |
|---|---|---|---|---|
| T | 0.60 (fail) | fail | fail | extension holds +1.1 to +2.1 Hz: right sign, 10× small |
| T′ | **0.80 (pass)** | fail | pass | flexion close to measured (8° −4.0 vs −4.1; ramps −3.7 to −5.7); extension +0.6 / +1.0 vs +20 Hz |

Neither passes H2, so **181021 stays sealed**. The dev target is exhausted for fitting: across sessions 6b–7 it has had more than 2 post-hoc attempts.

Standing (session-6 criterion: min z ≥ 0.90 mm over 0.5–1.5 s):

| Config | min z by seed (mm) | mean z (mm) | motor silenced |
|---|---|---|---|
| default | 0.54 | 0.64 (roll 76°) | |
| T | 0.75 / 0.78 / 0.87 | 0.98 / 0.80 / 1.06 | 0.68 |
| T′ | 0.64 | | 0.68 |

T is the highest the model has stood (previous best: min 0.77, mean 0.79). Still **fail**.

Stability (0 non-tonic spikes in the last 100 ms after sensory silencing): **T and T′ both fail**, with 64–78 spikes/ms on 3 seeds each. The sustained cells are mainly the **central-complex head-direction ring**: EPG (37–40 cells, ~100 Hz), PEN_a/b, Delta7, PFNv, EL. Accessory tibia flexor MNs also persist. Extra ascending leg activity kicks the ring into a saturated, whole-ring persistent state. The real ring holds a localised bump that persists in darkness (Seelig & Jayaraman 2015), not a saturated ring.

**Consequences.**
1. T and T′ are not adopted.
2. The stability criterion cannot tell legitimate persistence (a bump) from runaway (a saturated ring). A future criterion should score the CX separately: bump width, fraction of EPGs active.
3. **Hypothesis:** the brain-wide efficacy ceiling (0.165 mV, "largest stable") is set by the CX ring's saturation threshold. Tested next, exploratory.

### Exploratory (no adoption possible): CX ring kick; global measured strength with depression (14:08, written at launch)

**E2, the CX kick** (`scripts/probes/cx_kick.py`, default model). Kick the first 2 or 6 EPGs by 3 mV per step for 50 ms, silence all sensory input, and count ring activity 200–400 ms later. A no-kick control runs alongside. The prediction under the hypothesis: the kick leaves a saturated ring (most EPGs active), not a bump (≤ ~1/4 of EPGs).

**E1, global strength.** Every synapse at 1.8 mV (the 0.165 × 10.9 ORN→PN transfer) with the Nagel depression (U 0.22, τ 893 ms) on every presynaptic cell. The question is whether measured-strength synapses plus measured-form depression give a stable brain with a working sugar→MN9 path.
- Readouts: closed-loop stability (2 seeds) and sugar→MN9_L at 100 and 200 Hz.
- This is a feasibility probe, so there are no criteria. Transfer of one synapse class's depression to all classes is a guess.

**Result, E1 and E2 (14:10).**
- **E1, global 1.8 mV plus depression: unstable.**
  - Whole brain 9.5 Hz; uPN mean 47 Hz (87% active); MNs 32 Hz.
  - 350–560 non-tonic spikes/ms persist after silencing (2 seeds). The persistence is carried mainly by optic-lobe recurrent loops (Tm1/2/4, T1, Dm15).
  - Sugar→MN9_L still works: 52 / 45 / 37 Hz at 100 Hz, 57 Hz at 200 Hz.
  - Measured-strength synapses with ORN-type depression everywhere are not viable. Stability at measured strength needs cell-class-specific inhibition, thresholds or depression that the model does not have.
- **E2, EPG kick (default model).** After 6 or 2 EPGs were kicked (15 mV, 50 ms) and all sensory input silenced, 0 of 50 EPGs were active at 200–400 ms; the no-kick control is the same. Under E1 the same kick saturates the ring: 50/50 EPG at 27 Hz, PEN at 84 Hz.
- **Conclusion.** The hypothesis is not supported. At default efficacy the ring cannot sustain itself. In T and T′ the persistent state must be started by the heavy leg-afferent drive and held by VNC and ascending loops (accessory flexor MNs and IN09A005 persist). The default network has latent self-sustaining states that strong activity can enter; compare F-ORN-2.

**Diagnostic (14:14): why extension does not excite the flexor under T′.** An 8° extension step (82→90°, stiff probe), left-middle premotor rates pre→hold:
- IN21A004 (ACh) 0→30 Hz;
- IN13A005 (GABA) 116→25 Hz, i.e. disinhibition;
- **IN21A006 (glutamate) 4→55 Hz.** It is the second-largest input to the slow MNs (93 synapses).

Under uniform inhibitory glutamate, IN21A006 cancels the cholinergic excitation and the disinhibition; the MN changes by −0.9 Hz. The reflex sign therefore hinges on two unverified foundations: glutamate's sign at leg MNs, and the inferred direction tuning of the afferents that drive IN21A006.

### Exploratory (over the post-hoc budget, not adoptable): glutamate excitatory onto tibia flexor MNs, under T′ and T (14:14)

The row is the session-6b hypothesis (`hypotheses_not_adopted.csv`), loaded via `candidates_s7_glu_flexor.csv`. The run is the dev reflex with the stiff probe. The dev target is over budget, so a "pass" here can **only** motivate a pre-registered test on a fresh sealed cell next session. Lesser 2024 (transcriptomic; GluCl dominant in MNs) argues against the hypothesis.

### Pre-registration: monoamines are not fast transmitters (14:15)

**Finding (post-hoc, from the T persistent state).** DNg33 (ACh) drives the serotonergic AN09A005, IN09A005 and AN27X013 (2,939 / 1,321 / 1,619 synapses). They project back onto DNg33 (69 / 113 / 62) and onto themselves (AN09A005→AN09A005, 52). m2 signs serotonin, octopamine and dopamine as **fast excitation**, a guessed placeholder (Shiu convention; `profiles.py`), which makes this a positive-feedback loop. The EL ring neurons (octopaminergic) also persist.

**Evidence.** Every Drosophila receptor for serotonin (5-HT1A, 1B, 2A, 2B, 7), octopamine (OAMB/Octα1R, Octα2R, Octβ1–3R) and dopamine (Dop1R1, Dop1R2, DopEcR, D2R) is a GPCR. No ionotropic 5-HT3-type receptor is known in insects. Label **inferred**, from receptor genomics; no fast monoaminergic synaptic current has been measured centrally.

**Change (config M0).** `transmitter:{serotonin,octopamine,dopamine}|sign` = 0. Monoaminergic cells then act only through the neuromodulator pools (unchanged, currently inert).

**Tests.**
1. Default + M0:
   - sugar→MN9_L > 5 Hz at 100 and 200 Hz;
   - closed-loop stability, 3 seeds (0 non-tonic spikes);
   - the brain rate is reported.
2. T + M0:
   - stability, 3 seeds;
   - standing, 3 seeds (≥ 0.90 mm criterion);
   - the stiff-probe dev reflex, reported.

**Adoption.** M0 becomes the default if test 1 passes. It is a correction of a guessed convention toward receptor evidence, not a fit, so passing its regression checks suffices. M0's effect on the flybench olfactory tasks is deferred (held out).

**Result, M0 (14:18). Fails test 1; not adopted.** The rows stay as overrides only.
- **Default + M0.** Stability fails on 2 of 3 seeds: 49.7 and 51.7 non-tonic spikes/ms (optic-lobe Mi18, DNge019, DNg12_c); seed 2 gives 0. Sugar→MN9_L 7.7 Hz at 100 Hz (26.3 without M0) and 69.7 Hz at 200 Hz. Brain excluding ORNs: 0.32–0.41 Hz. Removing placeholder monoamine excitation unmasks other latent loops, so the placeholder had been part of what kept the calibrated brain quiet.
- **T + M0.** Stability fails (31–33 spikes/ms; the CX ring persists, while the serotonergic loop is gone). Standing min z 0.78 / 0.69 / **0.92** mm; seed 2 meets the height criterion, the **first run ever to do so**, but in an unstable, non-adoptable configuration.
- **Reading.** The monoamine fast-sign convention is biologically wrong (GPCR-only receptors), but the network's calibration depends on it. Correcting it needs a recalibration, pre-registered with fresh seeds, not a swap.

**Result, exploratory glutamate+ (14:25). Stiff probe valid.**
- **T′ + glu+:** H1 0.70. The 8° extension hold is **+3.4 Hz** (was +0.6), ramps +2.2 to +4.7, against +20 to +28 measured; flexion hold −1.9 against −4.1. The response moves in the right direction but stays about 5× short.
- **T + glu+:** H1 0.70; all holds within ±2 Hz.
- The glutamate sign at the flexor MN is not sufficient by itself. Not carried forward as a candidate without new evidence; Lesser 2024 argues against it.

**Result, E2b (14:29): the default CX ring is bistable.** Kicking all EPG and PEN cells (15 mV, 200 ms) and then silencing all sensory input leaves, at 200–400 ms:
- EPG 40/50 active at 75 Hz;
- PEN 42/42 at 187 Hz;
- Delta7 27/42 at 40 Hz.

This is a saturated attractor, not a bump. A 6-EPG, 50 ms kick does not trigger it (E2). The persistent state that fails T, T′ and T + M0 is this attractor, entered when ascending drive is high.

### Exploratory: Delta7 release gain ×2 / ×4 / ×8 (14:29)

Does stronger global ring inhibition turn saturation into a bump? Runs: a full-ring kick, and a local 6-EPG 200 ms kick, per gain, plus the ×1 local control. Rows are in `candidates_s7_d7_x*.csv` (guessed; not adoptable). The criterion for a future pre-registration is written here: after a local kick, a persistent bump with ≤ 1/4 of EPGs active; after a full-ring kick, no saturation.

**Result, Delta7 grid (14:30).**
- Local 6-EPG kicks leave nothing persistent at any gain, including ×1: no bump forms.
- Full-ring kicks still saturate:

| Delta7 gain | EPG active | PEN rate | Delta7 active |
|---|---|---|---|
| ×2 | 38/50 | 184 Hz | 20/42 |
| ×4 | 33/50 | 173 Hz | 14/42 |
| ×8 | 28/50 | 166 Hz | 8/42 |

- Delta7 self-inhibition silences the inhibitors themselves. The attractor lives in the PEN↔EPG excitatory loop; PENs are refractory-limited against a measured spontaneous rate of 3.9 Hz (Turner-Evans 2017).
- Not a one-knob fix. It is a CX modelling task for a future session, with the bump criterion above.

### Pre-registration: descending-command direction, MDN backward and DNg100 forward (14:35)

**Seen (exploratory, seed 0).** Thorax dx over the stimulation run:
- default: no stim +0.08, MDN −0.37, DNg100 +0.26 mm;
- T: no stim −0.29, MDN 50 Hz −0.56, MDN 100 Hz −0.87, DNg100 −0.16 mm.

**Biology.**
- MDN activation drives backward walking (Bah et al. 2014 / Bidaye et al. 2014, "moonwalker").
- DNg100 (BDN2) activation drives forward walking (Bidaye et al. 2020; Sapkal et al. 2024).

**Test.** `command_walk.py` at 100 Hz on fresh **seeds 1–4**, conditions no-stim / MDN / DNg100, for the default model and for T.

**Criteria, per model, paired by seed:**
- **C-MDN:** mean(dx_MDN − dx_nostim) < −0.2 mm, and negative in ≥ 3 of 4 seeds.
- **C-DNg:** mean(dx_DNg100 − dx_nostim) > +0.2 mm, and positive in ≥ 3 of 4 seeds.

Displacement direction only; this is not a claim of stepping (no gait criterion). Nothing is tuned. The default model is the working model; T is not adoptable (stability).

**Result (14:42), seeds 1–4.** Thorax dx (mm) per seed:

| Model | no stim | MDN | DNg100 |
|---|---|---|---|
| default | −0.72 / 0.00 / −0.04 / +0.15 | +0.17 / +1.06 / −0.36 / +0.17 | −0.47 / −0.09 / −0.04 / +0.10 |
| T | −0.22 / −1.31 / −0.23 / −1.02 | −0.28 / −1.30 / −1.03 / −0.12 | +0.40 / −0.44 / −0.13 / −0.01 |

Differences from no-stim (mean; sign count):

| Model | C-MDN | C-DNg |
|---|---|---|
| default | +0.41; 1/4 negative. **Fail** (wrong direction) | +0.03; 1/4 positive. **Fail** |
| T | +0.01; 2/4 negative. **Fail** | **+0.65; 4/4 positive. Pass** |

- The seed-0 MDN "backward" result was noise; the no-stim drift has an SD of ~0.5 mm.
- Under the transferred leg-afferent synapse, the forward command DNg100 moves the fly forward on every seed. The working model does not.
- This is displacement, not a gait. T is not adoptable (stability; F-STAB-1).

**Diagnostic (14:45): T without CX ring output is stable.** Ring types (EPG, PEN, PEG, Delta7, PFNv, EL, GLNO, FR1) had release gain 0 (diagnostic only). T gives 0 non-tonic spikes/ms after silencing on 3 seeds (brain 0.55–0.72 Hz), and T + M0 the same. The serotonergic loop was being driven through the ring. **The only stability blocker for T is the CX saturated attractor.**

### Exploratory CX screen (14:45)

Ring types (EPG, PEN, PEG, Delta7) are given, each separately:
- (a) Nagel depression;
- (b) adaptation of 3 mV per spike, τ 300 ms;
- (c) threshold gap 21.5 mV (the Kenyon-cell measurement, transferred).

Each gets a full-ring kick and a local 6-EPG kick. The criterion is as above. All guessed; these screen for what to pre-register next session.

**Result, CX screen (14:51).**
- Local kicks: nothing persists under any variant; no bump.
- Full-ring kicks: saturation is removed by all three variants.
- T stability:
  - with (c), the threshold gap: 3/3 seeds stable, but only because the ring **never fires** (rates identical to the ring-silenced diagnostic);
  - with (a), depression: 2/3 stable; seed 2 holds the serotonergic loop, 6.8 spikes/ms.
- **CX resting rates** (closed loop, seed 0):

| Config | EPG | PEN | PEG | Delta7 |
|---|---|---|---|---|
| default | 0 | 0 | 0 | 0 |
| default + (a) | 0 | 0 | 0 | 0 |
| default + (b) | 0 | 0 | 0 | 0 |
| T | 77 Hz | 189 Hz | 30 Hz | 39 Hz |

Measured: PEN spontaneous 3.9 ± 2.6 Hz while standing, and a persistent EPG bump. **The model ring has two states, silent and saturated, and the real ring's operating state is neither.** A CX ring model is a prerequisite for adopting any change that raises ascending drive.

### Exploratory (over the post-hoc budget, not adoptable): swapped claw directions (14:52)

**Foundation under test.** The flexion vs extension tuning of claw types is inferred from a wiring rule with a resistance prior. BANC has no direction field; checked this session.

**Candidate.** `candidates_s7_claw_swapped.csv`: SNpp46/48/49/50/51 directions flipped; loaded via `FLYEMU_PROPRIO_ASSIGNMENT`, a new env override analogous to `FLYEMU_EXTRA_PARAMS`.

**Run.** The dev reflex under T′ (stiff probe). A large extension response would name this as the foundation to settle with data, for example the morphological claw-extension/flexion classes of Lesser et al. 2024 via FANC↔male-cns matching.

**Result, claw swap (15:00).** H1 **0.10**: nearly every sign inverts (8° extension −5.7, ramps −4 to −8 Hz; flexion +2.6 to +4.7). H3 passes. Standing under T + swap: min z 0.51 / 0.51 / 0.69 mm, and the fly rolls over (90–142°). On the seen dev data, the inferred claw directions are strongly favoured over their mirror image, and the claw pathway dominates the reflex sign. This is supporting evidence for the inferred foundation, not a measurement.

**Check (15:01): ORN→uPN crosstalk is not the cause.** 93% of ORN→uPN synapses (87% of edges) are cognate; the median non-cognate edge has 10 synapses, against 24 for cognate. DM4 PNs receive 30–32 cognate ORNs, against 17.4 per antenna × 2 in KW2009. One DM4 PN (body 10613) has 37 non-cognate edges (833 synapses); possibly an annotation issue.

### Pre-registration: post-hoc repair 2 of 2 for the AL target, PN threshold gap from the one measured central gap (15:01)

**Motivation (post-hoc).** With measured uEPSP, depression and convergence, the predicted mean PN depolarisation is ~9 mV with SD ~4 mV. That is inconsistent with spontaneous firing of a few Hz unless threshold − rest ≫ 7 mV. The only measured central gap is 21.5 ± 5.6 mV in Kenyon cells (Turner, Bazhenov & Laurent 2008, Fig 3G, n = 17).

**Change.** On top of PR / MR (rest −57.8): uPN `v_th` = −36.3 mV, a gap of 21.5 mV. Label inferred (cross-class transfer); nothing fitted.

**Criteria.** A0–A2 unchanged, 3 seeds.

**Expectation.** The high-rate tail is suppressed (mean ≤ 10 Hz likely), but the active fraction falls further and A1 fails. This is the last repair for the AL target in this form.

**Result, AL repair 2 (15:04). Fail; not adopted.**
- PRG: active 0.53 / 0.54 / 0.53; median 1 / 2 / 2 Hz (A0 passes); mean 13.1 / 12.9 / 13.1. A1 and A2 fail.
- MRG: active 0.50 / 0.48 / 0.49; median 0 Hz; mean ~12.8.
- The high-rate tail survives even a 21.5 mV gap, so it is driven by convergence and the operating point does not explain it.
- **Post-hoc budget for the AL target: 2 of 2 used. Stop fitting this target.** The measured transmission values stay as options, all off.

**CX wiring analysis (15:10, male-cns, edges ≥ 5).** Synapses per postsynaptic cell:
- **Delta7→Delta7 626**, Delta7→EPG 86, Delta7→PEN 165, EPG→Delta7 448;
- PEN→EPG 517, PEN→PEN 420, EPG→PEN 287, EPG→EPG 233.

Two consequences:
- Under inhibitory glutamate, Delta7s mainly inhibit each other, which weakens the ring's global inhibition.
- EPGs get 147k synapses from outside the ring, mostly GABAergic ER ring neurons (ER4m, ER2_c, ER4d, ER3w_b).

**ER rates in closed loop:** default 0 Hz; T 11 Hz. Real ER neurons are visually and tonically driven. Their silence in the model removes the EPGs' main external inhibition, which is a candidate cause of the saturated state.

**Measured ring physiology (agent, full text; 15:11):**
- EPG bump FWHM ~100° (Turner-Evans 2017, n = 5 + 6 flies);
- the bump persists in darkness, sometimes for > 30 s (Seelig & Jayaraman 2015);
- P-ENs spike at rest; rate modulation 5.6 ± 3.7 Hz (n = 12);
- Delta7 activation inhibits EPG, picrotoxin-sensitive (Franconville 2018);
- Delta7 block lowers bump amplitude without widening it: "other sources of inhibition must act to shape the E-PG activity into one bump" (Turner-Evans 2020);
- no intrinsic properties or PSPs for ring cells found.

The bump criterion is set from these: an EPG active fraction of 15–40% (~100° of 360°), persisting ≥ 200 ms.

### Exploratory screen: tonic ER ring-neuron activity (15:11)

ER types get `spontaneous_drive` d ∈ {5, 7.5, 10} mV (guessed; ER spontaneous rates not found). Runs: local and full-ring kicks, plus T stability. Screening only.

**Result, ER screen (15:13).** Tonic ER drive of 5 / 7.5 / 10 mV gives ER at 0–18 Hz.
- Full-ring kicks still saturate: EPG 40–44/50 at 51–65 Hz; PEN 190–192 Hz.
- Local kicks: nothing persists.
- T stability still fails (64–72 spikes/ms).

ER inhibition acts on EPGs, but the runaway core is the PENs:
- PEN→PEN is 420 synapses per cell (ACh), plus PEN↔EPG;
- PENs are refractory-limited at ~190 Hz under every ring manipulation tried (Delta7 ×8, ER tonic).

**Lead for next session.** EPGs express Nmdar1/2 (Turner-Evans 2020 RNA-seq). Slow NMDA-type recurrent excitation is the standard route to a persistent low-rate bump. That needs per-receptor synaptic kinetics (`tau_s` is per postsynaptic type now), plus a check of whether PEN→PEN contacts are real or an artefact of within-PB proximity.

Session-7 CX conclusion: measured targets exist (bump FWHM ~100°, persistence in darkness, PENs spike at rest). No single-knob change screened (Delta7 gain, ring depression, adaptation, threshold gap, ER tonic) gives a bump. Saturation can be removed only by silencing or damping the ring.

### Pre-registration: recalibrate the global efficacy under M0, rule v2 (15:14)

**Motivation.** M0 (monoamines not fast transmitters; receptor genomics) is biologically correct but destabilises the default at 0.165 mV. The existing calibration rule decides whether a lower efficacy restores stability.

**Procedure.** `calibrate_gain.py --generic 4` (rule v2: return to rest after sugar and after 4 fixed random sensory populations) with M0, at scales {0.7, 0.8, 0.9, 1.0} × 0.165 mV. The chosen scale is the last passing before the first failure.

**Adoption (M0 + recalibrated efficacy as the new working model).** All of the following, at the chosen scale:
- closed-loop stability on 3 **fresh** seeds (3, 4, 5): 0 non-tonic spikes after silencing;
- sugar→MN9_L > 5 Hz at 100 and 200 Hz;
- the brain rate excluding ORNs < 1 Hz.

A change of this size is reported with the regression-reference move. The flybench olfactory held-out is deferred and must be run before any AL claim.

**Rule v2 under M0 (15:17).** Every tested scale passes (0.7–1.0; no activity at 600–800 ms). Chosen: 1.0, i.e. 0.165 mV unchanged. Rule v2 is open-loop and does not detect the closed-loop persistence M0 showed. Adoption test per the pre-registration: M0 at 0.165 mV on fresh seeds 3–5. Declared now, before results: scales 0.9 and 0.8 are also run on seeds 3–5 as exploratory information only.

**Result, M0 adoption test (15:19).** At 0.165 mV on fresh seeds 3 / 4 / 5: 0 / 0 / 0 non-tonic spikes; brain excluding ORNs 0.43 / 0.29 / 0.35 Hz. Sugar was already > 5 Hz. **The pre-registered letter is met. M0 is still not adopted.** Seeds 0 and 1 (seen earlier) hold a persistent state, so M0 is stable on 4 of 6 seeds. The pre-registration was flawed in counting only fresh seeds when failures were already known. The default is stable on seeds 0–2 and 6–11 (F-ORN-3).

Exploratory: 0.9 and 0.8 × 0.165 are stable on seeds 3–5 (brain 0.37–0.43 and 0.21–0.24 Hz).

Next session: pre-register M0 at a scale ≤ 0.9, with **all** seeds 0–5 plus 3 fresh, the olfactory held-out, and the full battery.

**Claw/hook direction search (15:20).** No publication maps flexion or extension onto male-cns / MANC SNpp types. Ground truth exists only as FANC T1L root-ID labels (Lee, Azevedo et al. 2025 Nat Commun; github sagrawal/Lee_2024, now in `data/raw/lee2025/`): claw_flx 13, claw_ext 8, hook_flx 13, hook_ext 9. BANC's `fanc_match` uses short FANC ids, so the join needs FANC CAVE access (an account; Ben) or NBLAST bridging.

The agent also reports that VFB types MANC SNpp39 as club and SNpp41 as claw, against our BANC-derived "hook". The BANC reviewed matches (agreement 0.91 / 1.0) remain the basis; the conflict is recorded as an open question. Directions stay **inferred**.

**M0 at lower scales, exploratory (15:22).**
- Seeds 0 and 1, which failed at 1.0, are stable at 0.9× and 0.8× (brain 0.32–0.38 and 0.21–0.24 Hz).
- **Sugar→MN9_L at 0.9× under M0: 0.3 Hz at 100 Hz** (fails > 5) and 32 Hz at 200 Hz.
- The monoamine fast-excitation placeholder both creates latent persistent loops and carries real pathway transmission. No scalar recalibration restores both. A proper fix needs the neuromodulator pools to take over the monoamines' function (receptor data per type). Not adopted.

### Pre-registration: slow-MN parameter transfer to spare cells 180621 and 181127, intrinsic trials only (15:22)

This repeats the session-6c protocol exactly: CurrentStep trials only, via `azevedo_slow_mn.py --intrinsic-only`. **The Piezo trials stay sealed.**

Predictions from the 180111 fit (θ 32.62 mV, t_ref 4.27 ms, drive 36.45 mV, τ 16 ms), per cell:
- P1: spontaneous rate within ±30% of 24.8 Hz;
- P2: τm within ±30% of 16 ms;
- P3: at each tested current, the LIF with this cell's measured Rin predicts the rate within max(30%, 5 Hz).

Pass means P1–P3 for a cell. If both pass, class transfer is supported on 4 cells. A failure means the class needs a distribution.

**Result, spare-cell transfer (15:22). Fail for the point fit; τm transfers.** The scorer reproduces the 6c numbers for 181021 exactly.

| Cell | P1 spontaneous | P2 τm | P3 f-I | Rin |
|---|---|---|---|---|
| 180621 | 20.1 Hz ✓ | 16.3 ms ✓ | ✗ (−29 pA: 5.1 measured vs 0 predicted; +29 pA: 34.7 vs 49.6) | 532 MΩ |
| 181127 | **46.5 Hz ✗** | 16.6 ms ✓ | ✗ (−23 pA: 12.4 vs 0) | 1,021 MΩ |

Across the 4 recorded R35C09 slow MNs:
- τm is 15.5–16.6 ms (**transfers**);
- the resting rate is 20–47 Hz, consistent with Azevedo's class mean of ~30 Hz;
- Rin is 532–1,041 MΩ.

**Decision.** Keep the point fit as the class default for now, but record it as one draw. The next MN refit should use the across-cell distribution (drive and θ per cell). The Piezo trials of both spares remain sealed; only `--intrinsic-only` was run. Data: `data/derived/azevedo2020_slow_mn_{180621,181127}_intrinsic.*`.

### Diagnostic: is the curled abdomen holding standing down? (15:28)

**Observation (video, after fixing `render_organism.py`).** The render had used 1-synapse edges, no profile, rebuilt interfaces and no adhesion. After the fix:
- the default fly slumps;
- the T fly stays up on its legs;
- in both, the abdomen curls dorsally like a scorpion's, and the wings sit open.

Abdominal and wing MNs use the guessed force_per_spike = 10 and guessed pitch/yaw signs.

**Test.** `standing.py --zero-joints 'abdomen|wing'` zeroes abdominal and wing actuator torque (diagnostic only), for default and T, seeds 0–2. Reported against the same seeds without zeroing.

**Reading.** If min z rises substantially, the guessed abdominal and wing motor layer is a standing confound to fix before the VNC is judged.

**Result (15:31).** min z 0.5–1.5 s (mm), seeds 0 / 1 / 2:

| Config | normal | abdomen + wing zeroed |
|---|---|---|
| default | 0.54 / 0.48 / 0.46 (roll 76–90°) | **0.64 / 0.55 / 0.70** (roll 25–60°) |
| T | 0.75 / 0.78 / 0.87 | 0.49 / 0.77 / 0.49 (2/3 roll over, 178°) |

- **Default:** the guessed abdominal and wing motor layer lowers the fly and makes it roll.
- **T:** removing it destabilises balance.
- The abdominal and wing motor layer (guessed force 10, guessed pitch/yaw alternation) is a real confound for standing. It must be given data (abdominal MN forces, sign calibration) before standing results are read as VNC evidence. Not a model change.

### Decisions by Ben after session 7 (16:15)

1. **Priority:** the navigation (CX) ring comes first; abdomen/wing calibration follows.
2. **Stability criterion, changed by Ben.** The CX heading ring is scored by its own bump test: EPG active fraction 15–40%, persisting ≥ 200 ms without input, and PEN < 50 Hz after a full-ring kick. Persistence there is not a stability failure. **Every other cell must still go quiet** after sensory silencing (0 non-tonic spikes in the last 100 ms, CX ring types excluded). Applies from session 8, with the CX type list declared in the pre-registration.
3. **FANC access.** Ben provided a CAVE token, stored at `~/.config/flyemu/cave_token` (mode 600, never committed). It authenticates, but grants only `FANC_sandbox` and `banc_public` view. The `fanc_production_mar2021` and `brain_and_nerve_cord` datastacks return 403. The Lee et al. 2025 labels need FANC production access, which Ben must request.
4. **Session length:** unattended sessions stop at a natural end rather than starting multi-hour items they cannot finish.

## Session 8 (26 September 2026, attended)

### Pre-registration: warm start ("not from brain death") and the CX bump test (16:47)

**Change (option, off by default).** Every run so far starts the CNS exactly at rest, noise-free, with every sense switched on as a step at t = 0 (`state:all_neurons|initial_condition`, still the minimal placeholder). Ben's question: is the ring's bistability an artefact of starting the fly from brain death? The warm-start protocol W, identical for every run and never tuned per episode:
- background membrane noise σ (`cell_type:all|background_noise`, mV/√ms) on every neuron, standing in for unmodelled ongoing input (guessed; a single scalar);
- noise and all senses ramp linearly from 0 to 1 over 500 ms; scoring starts after 1,000 ms;
- then a 50 ms, 10 mV EPG kick: **local** (EPGs within ±45° of a heading drawn from the seed; heading from the PB glomerulus, inferred, ±22.5°) or **full** (all 50 EPGs); then all afferent drive is removed for 500 ms (noise stays on).

Probe: `scripts/probes/warm_start.py`. **Correction to s7:** `cx_kick.py` kicked the first N EPGs in table order (glomeruli L3, L5, L5, L3, R3, R7), which is not a local kick. The s7 "local kick leaves no bump" rows are therefore not bump tests.

**Motivation.** Ben's question (not post-hoc from a failed run). Mechanistic lead: the 147k GABAergic ER→EPG synapses come from ring neurons that are silent in the noise-free model, so the ring has no ongoing inhibition.

**Fit set: σ.** A sweep σ ∈ {0.25, 0.5, 0.75, 1.0, 1.5}, default config, senses on, no kick, seed 0. σ is *admissible* if, in the warm window (500–1,000 ms): no runaway; uPN mean ≤ 8.8 Hz (Turner 2008, 4.6 + 1 SD, seen/spent); non-CX brain mean ≤ 5 Hz (guessed ceiling). σ is not fitted to any CX quantity.

**CX ring types (Ben's decision 2, declared list):** EPG, EPGt, PEN_a, PEN_b, PEG, Delta7, ER*, EL*. PFNs count as ordinary cells.

**Criteria, per config (default, T), at each admissible σ, seeds 1, 2, 3:**
- B1 local kick → in the window 200–500 ms after the kick ends, EPG active fraction (≥ 10 Hz) 15–40%, population-vector strength ≥ 0.5, and the bump within 45° of the kicked heading;
- B2 full kick → PEN mean < 50 Hz in the same window;
- Q every other cell goes quiet → the non-CX, non-tonic rate in the last 100 ms is ≤ 1.2 × the rate of a matched control (same σ and seed, senses off throughout, no kick) + 0.05 Hz.
A config passes if B1, B2 and Q hold on 3/3 seeds.

**Held out (reported only at admissible σ; not used to choose it):** resting PEN rate 3.9 ± 2.6 Hz (Turner-Evans 2017) in the warm window; KC 0.1 ± 0.4 Hz (Turner 2008).

**Adoption.** If a config passes, W becomes the default initial condition for scored runs, σ is registered as guessed with this entry as its basis, and T is re-tested on the embodied criteria (PLAN_NEXT 2). Otherwise W stays an option, off, and the brain-death hypothesis is rejected for the ring at these σ.

**Expectation.** Noise will activate ER ring neurons and Delta7, which may remove full-kick saturation (B2). I expect no persistent local bump (B1) at σ ≤ 1, because the ring's recurrent excitation is uniform rather than wedge-structured. I would be glad to be wrong.

**Result, warm start (17:05). Fail: 0/3 seeds in every condition. The brain-death hypothesis is rejected for the ring.** Data: `runs/s8_warm/{sweep,batch_default,batch_T}.jsonl`; scorer `scripts/probes/score_warm.py`.

| Config | σ 0.25 | σ 0.5 | σ 0.75 |
|---|---|---|---|
| default | ring silent; local and full kicks both die (B1 ✗, B2 ✓ trivially) | 2 seeds as at 0.25; seed 1 **ignites by itself** during warm-up (PEN 112 Hz) | ring saturated before any kick (PEN 176–186 Hz) |
| T | **saturated during the gentle ramp**, before any kick (PEN 188–189 Hz) | the same | the same |

- The ring has no intermediate state under any start: PEN is ~0 or 110–190 Hz. A properly localised 12-EPG kick never leaves a bump (EPG active fraction 0 or 0.76–0.78; vector strength ≤ 0.36).
- Background activity **lowers** the ignition threshold rather than stabilising the ring. The ER and Delta7 inhibition it recruits (ER 7–17 Hz, Delta7 23–39 Hz) does not hold EPGs back.
- Under T, the ring is ignited by the steady leg-afferent drive itself, not by the t = 0 step: ramping senses over 500 ms makes no difference.
- Q (every other cell goes quiet) fails only where the ring is saturated at σ ≤ 0.5, which is the ring's output driving the rest of the brain. At σ 0.75 everything (control included) sits at the same ~1.25 Hz, so Q passes.
- **Held out, now spent:** resting PEN 3.9 ± 2.6 Hz → model 0 or 112–190 Hz (fail). KC 0.1 ± 0.4 Hz → 0–0.45 Hz (within 1 SD at every admissible σ).

**Decision.** W stays an option (`scripts/probes/warm_start.py`), off; σ is not registered. The initial condition is not the cause of the bistability. It is intrinsic to the ring's parameters: strong uniform recurrent excitation with no working wedge-structured inhibition. This moves the next CX step to a structural mechanism (slow NMDA-like EPG excitation and/or wedge-structured inhibition), tested with the corrected local-kick probe.

### Fill: receptor calls from transcriptomes; glutamate sign for 18 types (18:03)

**Data.** Davis, Nern et al. 2020 (GEO GSE116969), per-cell-type expression probabilities for 77 genetically targeted populations. Crosswalked to 69 male-cns types (`scripts/infer_receptors.py`, `data/derived/davis2020_crosswalk.csv`). Identities of the CX drivers come from Wolff & Rubin names in Davis Supp file 1A: PB_2 = EPG (SS00090), PB_1 = Delta7 (SS00116), PB_3 = PEN_a (SS02268; contaminated, recorded only). Transmitter genes validate the crosswalk: EPG ChAT+, Delta7 VGlut+, PAM ple+, L1 VGlut+.

**Adopted (live, `cell_types.csv`).** `glutamate_receptor_sign = −1` for the 18 types that express GluClα and no AMPA-like iGluR (EPG, PAM02/04/07/08/10, Dm4, Dm8a/b, Dm11, L2, LPC1, Lawf1/2, Tm1/2/3/29). Basis **inferred** (mRNA presence, not synaptic localisation). This agrees with the transmitter default, so it converts guesses into data-backed values: **0 of 6,241,231 weights change** (checked by building both networks).

**Candidate, not live.** Dm9 and T1 express iGluR and not GluClα → +1 (`data/params/candidates_s8_glu_igluR.csv`). This changes behaviour and needs the regression checks first.

**Ambiguous, no row.** 36 types express both (Delta7, KCs, Mi1, T4/T5, LCs…); 5 express neither (photoreceptors, L1, Tm9).

**Inference algorithm test.** Can wiring predict receptors for the ~14k unprofiled types? Leave-one-type-out logistic regression on connectome features (input-transmitter shares, own transmitter, superclass, log input count), 57 training populations (9 central). It is usable only where the balanced accuracy is ≥ 0.70 and ≥ baseline + 0.15. **The sign-critical genes are at chance:** GluRIA 0.48, GluRIB 0.52, Nmdar1 0.62, GABA-B-R3 0.50, 5-HT1A 0.47, Dop1R2 0.59. Usable: HisCl1 0.87, ort 0.78 (histamine input), plus near-universal genes (Rdl, Lcch3, Nmdar2) and Oamb, 5-HT2A/2B/7 (0.72–0.79). **Conclusion:** synapse signs and receptor kinetics for unprofiled types cannot be inferred from wiring. They need a transcriptomic atlas matched to connectome types. No connectome-predicted values are written to live tables.

**NMDA lead withdrawn.** EPG expresses Nmdar1 at the highest level of all profiled cells (126 TPM). But EPG's input is 61% GABA (ER ring neurons), 26% ACh and 10% glutamate (ExR6, ExR5, Delta7). The ring's recurrent excitation is cholinergic, so EPG NMDA receptors cannot supply slow recurrent excitation. The s7 lead ("EPGs express NMDA → slow recurrent excitation") is mechanistically wrong, and no NMDA test was run.

### Screen (exploratory): Delta7 glutamate sign (18:03)

Delta7 expresses both GluClα and iGluR (measured), and most glutamate onto Delta7 comes from Delta7 (626 synapses/cell), so the model's all-inhibitory Delta7→Delta7 is not supported by the data. Two candidates: +1 (`candidates_s8_d7_glu_pos.csv`) and ≈0 (`candidates_s8_d7_glu_zero.csv`). Screen with `warm_start.py`: σ 0 and 0.5, default and T, seeds 1–3, local/full/control. Scored with the s8 bump criteria, but as a screen only; any adoption needs a fresh pre-registration on new seeds.

**Dm9 / T1 iGluR rows: adopted (18:06).** Regression with the rows: sugar→MN9_L 26.3 / 87.3 Hz (unchanged); closed loop seeds 0–2: 0 non-tonic spikes after silencing; brain excluding ORNs 0.412 / 0.414 / 0.292 Hz (baseline 0.389 / 0.388 / 0.314). Appended to `cell_types.csv` (basis inferred); `candidates_s8_glu_igluR.csv` kept as the record. 20 of ~14k types now have a transcript-based glutamate sign.

### Fill: conduction delay for untyped cells (18:13)

**Blank.** 11,916 untyped cells (no `type`, so no skeleton-derived delay) used the borrowed shared default of 1.8 ms (Shiu 2024). That is inconsistent with the rule for typed cells: 0.5 ms + L / 0.5 m/s, median ≈ 1.0 ms.

**Algorithm** (`scripts/infer_delays.py`). Ridge regression of log L (median soma→presynapse path) on log volume, log pre/post synapse counts and superclass, trained on 11,711 skeletons. Predictions are clipped to the training 5–95% range, because untyped cells are often fragments (a distribution shift). **10-fold CV delay error (median / p90):** model 0.136 / 0.382 ms; median-L baseline 0.129 / 0.440 ms; **borrowed 1.8 ms default 0.838 / 1.076 ms**. Morphology explains little (R² 0.17), but any L-based value is ~6× closer than the default. Written for 10,809 cells (median 0.70 ms, range 0.56–1.65 ms) to `data/params/conduction_delays_untyped.csv`, basis inferred.

**Adopted** as `cell_type:untyped|inferred_conduction_delay = 1` (0 restores the default). **Regression moves (reported):** sugar→MN9_L 20.3 ± 9.0 Hz at 100 Hz (trials 26 / 25 / 10; was 26.3 ± 1.5) and 89.3 Hz at 200 Hz (was 87.3). Both pass (> 5 Hz), but the 100 Hz trial spread grew: the sugar pathway runs through untyped cells whose delays fell from 1.8 to ~0.7 ms. Closed loop seeds 0–2: 0 non-tonic spikes; brain excluding ORNs 0.387 / 0.393 / 0.282 Hz.

**Test change.** `test_session6_mechanisms_are_inert_by_default_and_act_when_enabled` assumed that no type had its own glutamate-sign row. It now excludes the targets with transcript rows from the global-override check and asserts that those rows win.

### Pre-registration: transmitter identity from consensusNt (18:14)

**Finding that motivates it** (not post-hoc from a failed run). The model takes transmitter identity from `predictedNt`, the per-neuron EM classifier call. The dataset's curated `consensusNt` (98.7% coverage) disagrees on 20,169 neurons:
- all 4,058 Kenyon cells are predictedNt dopamine but consensusNt acetylcholine. Davis 2020 transcripts agree with consensus: KCs are ChAT+ and lack ple. Transcripts agree with the consensus/type call on 62 of 68 crosswalked types (`data/derived/nt_transcript_vs_em.csv`);
- 1,827 "unclear" cells are glutamate and 1,490 are GABA in consensus. The model currently wires them as excitatory ("unclear" placeholder +1);
- 5,822 "unclear" are histamine (mostly photoreceptors).

At m2 / ≥ 5 synapses: 14.9k more inhibitory and 16.4k fewer excitatory edges. **Consequence for s7 M0:** monoamines at sign 0 also silenced every KC, so the M0 result is confounded.

**Change.** `connectome:all|nt_source_consensus = 1` (option; 0 = old behaviour). Basis of each transmitter call: derived (dataset consensus).
**Criteria.** Sugar→MN9_L > 5 Hz at 100 Hz stimulation; closed loop seeds 0, 1, 2: 0 non-tonic spikes in the last 100 ms after silencing (CX ring types excluded per Ben's s7 decision; the list is in `warm_start.py`).
**Adoption.** It is a data-quality correction (a curated call replacing a classifier call), not a fit, so it is adopted as the default if both criteria hold. Report every regression number that moves.
**Secondary (exploratory, not gating).** The warm-start ring screen under C.

**Result, consensusNt (18:17). Fail on stability (2/3 seeds); not adopted, kept as an option.**
- Sugar→MN9_L 16.7 ± 5.0 Hz at 100 Hz (pass > 5) and 128.7 Hz at 200 Hz (was 87–89).
- Closed loop: seed 0 **fails** (53.5 non-tonic spikes/ms after silencing, 1,488 cells: Mi18, Lawf2, DNge019, DNg12_a/c/e, Pm8/12, leg MNs). Seeds 1 and 2 pass (0; brain excluding ORNs 0.238 / 0.316 Hz).
- The persistent state is the **same Mi18 / DNge019 / DNg12 loop that M0 exposed in s7**. With transmitter labels closer to the data, the global efficacy (0.165 mV, fitted for stability under the *old* labels) no longer keeps this latent loop closed on every seed.
- **Reading.** The calibration is entangled with wrong transmitter labels. The correct next step is not a post-hoc tweak: recalibrate efficacy under consensusNt with calibration rule v2, as a model-construction step, then re-run the regression. Until then, all results carry the known label errors (KCs as dopamine; ~3.3k inhibitory cells wired excitatory).

### Pre-registration: efficacy recalibration under consensusNt (calibration rule v3) (18:18)

**Why.** The efficacy 0.165 mV was fitted for stability under the wrong transmitter labels (F-NT-1). Rule v2 is open-loop and cannot see the closed-loop latent loop (s7 M0).
**Rule v3** (construction, not a test): with `nt_source_consensus = 1` and the s8 live rows (delays, glutamate signs), scan the efficacy scale ∈ {0.95, 0.9, 0.85} × 0.165 mV (plus the 1.0 result above). Take the largest scale at which closed loop (`closed_loop_check.py`, 1 s senses + 300 ms silenced) has 0 non-tonic spikes in the last 100 ms on seeds 0, 1 and 2 (CX ring types excluded; the default ring is silent anyway).
**Checks at the chosen scale (not used to choose it).** Sugar→MN9_L > 5 Hz at 100 Hz stimulation (the M0 lesson: 0.9× gave 0.3 Hz). The old-label reference is 20–26 Hz.
**Adoption.** If a scale passes v3 and the sugar check, consensusNt plus that efficacy become the working model (profile m3), and all reference numbers are re-reported. Otherwise both stay options and the entanglement is recorded.

**Result, Delta7 glutamate-sign screen (18:20; `runs/s8_warm/d7_{pos,zero}.jsonl`).** 0/3 in every condition, but qualitatively informative:
- **+1 (Delta7→Delta7 excitatory), config T:** the ring stops saturating uniformly and forms a **localised bump**: EPG active fraction 0.28–0.36, vector strength 0.62–0.83, PEN ~100 Hz (was 190). But the bump is **pinned**: it sits at ~348° (or ~103°) whatever the kicked heading and seed (errors 74–153°). Delta7 runs at ~200+ Hz as a self-exciting global inhibitor.
- **≈0:** intermediate (EPG ~60% active, vector ≤ 0.37, PEN ~178 Hz).
- Default config: the ring stays silent at σ 0, as before.
- **Reading.** Strong global inhibition plus raw synapse-count heterogeneity gives a pinned attractor. A movable bump needs near rotational symmetry of the effective ring weights, which raw counts do not have. The next ring candidate is per-connection normalisation of the ring (inferred), not another global knob. Delta7's measured iGluR co-expression makes the all-inhibitory Delta7→Delta7 an open question, not a supported value.

**Result, rule v3 (18:24; `runs/s8_v3/`). Adopted: profile m3 = m2 + consensusNt + efficacy 0.15675 mV (0.95 × 0.165).**

| Scale | seed 0 | seed 1 | seed 2 | sugar→MN9_L at 100 / 200 Hz |
|---|---|---|---|---|
| 1.0 | **53.5** | 0 | 0 | 16.7 / 128.7 |
| 0.95 | 0 (brain ex-ORN 0.358) | 0 (0.213) | 0 (0.309) | **6.3 ± 2.1** / 96.7 |
| 0.9 | 0 | 0 | 0 | 2.7 / 78.3 (fails the check) |
| 0.85 | 0 | **32.2** | 0 | 0.3 / 51.7 |

- 0.95 is the largest scale with 3/3 return to rest, and it passes the sugar check (> 5 Hz), but only just.
- **Stability is not monotonic in scale** (0.85 fails on seed 1). The latent loop is partly a seed lottery, and three seeds are the minimum evidence, not proof.
- `WORKING_PROFILE` is now m3 (`FLYEMU_PROFILE=m2` reproduces sessions 5–8). The probes use `WORKING_PROFILE`, and m3 through the profile reproduces the scan (seed 0: 0.358).
- **New regression references (m3):** sugar→MN9_L 6.3 / 96.7 Hz; closed loop seeds 0–2: 0 non-tonic spikes, brain excluding ORNs 0.21–0.36 Hz.
- **The sugar pathway is now marginal** (6.3 Hz at 100 Hz stimulation). Any further change that lowers it below 5 Hz must be reported as a regression failure.

**Result, ring-normalisation screen (18:40; m3, σ 0.5, `runs/s8_norm/`).** 0/3 everywhere.
- m3 baseline: as m2 (default silent; T saturated, PEN ~180 Hz).
- Per-cell normalisation of ring-internal input: no change (T EPG 82% active, PEN ~180 Hz).
- Normalisation + Delta7 +1: as Delta7 +1 alone (localised, EPG 0.36–0.40 active, vector 0.62–0.64 on 2 seeds; the bump misplaced).
- Count heterogeneity in total input is not what places the bump. Under Delta7 +1 with T, a localised state **persists after the senses are removed**; only its position fails B1.
- Open question: pinned by wiring, or a weak kick? **Exploratory follow-up:** kick 20 mV for 200 ms at headings 0/90/180/270°, T + Delta7 +1, seeds 1–3.

**Result, bump-move test (18:45; `runs/s8_move/move.jsonl`, 12 runs). The bump is pinned.**
- With a 20 mV, 200 ms kick under T + Delta7 +1, the state after the kick sits near **~350°** or **~60–85°** whatever the kicked heading.
- Kicks at 0° land on target (errors 4–5°). Kicks at 180° and 270° end 78–169° away.
- The localised states persist in darkness (EPG 0.30–0.46 active, vector 0.5–0.73, when at ~350°), but with PEN 80–106 Hz and Delta7 ~190–200 Hz.
- **Reading.** The ring has two preferred locations set by its effective wiring and input, not a continuous attractor. Per-cell input normalisation does not remove them. Next: find the source of the asymmetry (per-glomerulus PEN→EPG / EPG→PEN offset structure, ER/ExR input distribution) before any adoption. Delta7 +1 stays a candidate.

### Pre-registration: m3 consequences (18:51)

1. **M0 under m3** (`transmitter:{dopamine,serotonin,octopamine}|sign = 0`). Under m3 this touches only the ~540 consensus monoamine cells, no longer the KCs. Same test as s7 M0 test 1: closed loop seeds 0–2 with 0 non-tonic spikes, and sugar→MN9_L > 5 Hz at 100 Hz (10 trials). Adoption as in s7: if both pass, M0 becomes the default (profile m3 + M0 = m4).
2. **Sugar under m3, 10 trials** (characterisation of the marginal pathway; no criterion).
3. **Standing under m3**, default and T, seeds 0–2 (`standing.py`), plus closed loop T seeds 0–2. Characterisation only: T stays blocked by the ring (F-CX-2).

### Correction: EPG heading map (18:54)

`warm_start.py` gave L_k and R_k the same heading (+22.5° on the right). A connectivity embedding (`scripts/infer_epg_heading.py`: spectral embedding of each EPG's input+output profile; inferred) shows **L1→L8 and R1→R8 run in opposite directions round the ring**, with R_k near L_(9−k) (e.g. L3 102°, R6 111°; L6 242°, R3 252°; spread within a glomerulus 1–9°).

Under the old map, one true bump reads as two clusters, and "local" kicks hit cells on opposite sides of the true ring. **Therefore the bump-position results of s8 are unreliable:** the B1 location/vector numbers in the warm-start batch, the Delta7 screen, the normalisation screen, the bump-move test and F-CX-2's "pinned at two headings".

Results that do not depend on position stand: silent vs saturated; PEN rates; the persistence of activity; Q. The probe now defaults to `--heading-map embed` and records per-EPG rates, so runs can be re-analysed later. The key conditions are being re-run.

### Fill revision: glutamate sign by receptor balance (19:02)

The first rule ("GluCl only" = −1; "both expressed" = no row) treated any detectable iGluR as "mixed". By level, Delta7 is **GluCl-dominated in both datasets**:
- Davis: GluClα 2,255 TPM against GluRIA+B 67 (ratio 0.03);
- Turner-Evans 2020 (GSE155329, sorted CX populations): GluClα 64–110 against iGluR at or below the whole-brain level.

**Rule v2.** GluClα expressed and (GluRIA+GluRIB)/GluClα TPM < 0.1 → −1. GluClα absent and iGluR present → +1. Otherwise no row. The 0.1 threshold is guessed.

**Result:** 49 types at −1 (Delta7, EPG, PAMs, most OL types; plus PEN_b and PEG from Turner-Evans) and Dm9/T1 at +1. The 14 truly mixed types (KCs, Mi1, L3–L5, …; ratio 0.12–2.5) get no row. Only Dm9/T1 change behaviour, and they were adopted earlier.

**Consequence.** The Delta7 +1 ring candidate is **not supported** by receptor levels. Together with the heading-map error, F-CX-2 is withdrawn. Research report: `docs/research/transcriptome_sources_s8.md`.

**Result, m3 consequences (19:07; `runs/s8_m3c/`).**
1. **M0 under m3: passes; adopted as profile m4** (= m3 + monoamine fast sign 0). Closed loop seeds 0–2: 0 non-tonic spikes (brain excluding ORNs 0.349 / 0.223 / 0.297 Hz). Sugar→MN9_L over 10 trials: 8.9 ± 5.9 Hz at 100 Hz and 96.0 at 200 Hz. The s7 failure of M0 came from the KC mislabel and the old calibration. `WORKING_PROFILE` = m4.
2. **Sugar under m3, 10 trials:** 8.9 ± 5.9 / 97.7 ± 5.0 Hz. The 3-trial 6.3 Hz was a noisy estimate. Individual trials can fall below 5 Hz.
3. **Standing under m3** (min z 0.5–1.5 s, mm; criterion 0.90):
   - default 0.59 / 0.68 / 0.67;
   - **T 1.03 / 0.74 / 0.97**, which meets the height criterion on 2 of 3 seeds (roll ≤ 29° on those).
   - Closed loop T: 55–58 spikes/ms after silencing, all in the saturated ring (EPG 72, PEN 180 Hz). T stays blocked by the ring alone.

### Screen: s7 ring candidates re-tested with correct headings, under m4 (19:17)

s7's CX screens judged the local-kick bump with EPGs in table order (not local), and s8's with a wrong heading map. So "no bump" was never tested properly for any single-knob candidate. Re-screen under m4, σ 0.5, local kick = the 12 EPGs nearest a seeded heading (inferred map), 10 mV for 50 ms.
- **Candidates:** ring STD (U 0.22, τ 893 ms); ring adaptation (3 mV, 300 ms); Delta7 release ×4; ER tonic 10 mV; ring gap 21.5 mV; STD + Delta7 ×4; adaptation + Delta7 ×4.
- **Configs:** default, T. Seeds 1–3.
- **Scoring:** the s8 bump criteria (B1, B2, Q).
- **Status:** a screen, not an adoption test. A candidate that passes gets a fresh pre-registration on new seeds, plus a bump-follows-kick test.

**Result, per-class ring normalisation (`runs/s8_ring3/`).** T stays saturated (EPG 62–78% active, PEN ~175 Hz, Delta7 ~34 Hz) with a weak tilt to ~22° that kicks do not move. Default stays silent. Not useful.

### Fill: Epiney 2025 CX snRNA-seq (19:19)

- Downloaded the 10 GB T2-lineage neuron atlas (GSE294658) on backhouse. Micromamba R + SeuratObject extracted per-cluster receptor fraction and cp10k for 51 genes and 161 clusters (`data/derived/epiney2025_cluster_receptors.csv`).
- Authors' identities (Supp Table 12) are validated by transmitter markers: DOPA ple+, SER SerT+, OCTA Tbh+, EPG ChAT+.
- **Cross-dataset check of the iGluR/GluClα ratio:**
  - EPG agrees in all three datasets (0.007);
  - PEN agrees with Turner-Evans (0.12 vs 0.13);
  - PEG (0.39 vs ~0.05) and PAM/DOPA (0.73 vs ~0 in Davis) do not.
- snRNA ratios are biased upward (ambient RNA or doublets), so the bulk threshold does not transfer. Only ratio < 0.1 is used (conservative): **vDeltaC, vDeltaE and hDeltaE → −1** (inert rows, matching the default). The other ~25 CX identities sit at 0.12–1.7, recorded, no row.
- Total transcript-based glutamate sign rows: 54.

### Pre-registration: receptor-based neuromodulator sensitivities (MS) (19:20)

**Why.** In m4 the monoamines act only through the pools, and every pool sensitivity is 0, so dopamine, octopamine and serotonin currently have no effect.
**Change.** `candidates_s8_modsens.csv`: 149 rows for 68 Davis-profiled types. Each sign comes from the G-protein coupling of the expressed receptors: Dop1R1/2, Octβ1–3R, Oamb, 5-HT7 and 5-HT2A/B count +; Dop2R, Octα2R and 5-HT1A/B count −. s = 0.2 × net (magnitude guessed). Other types stay at 0.
**Criteria (Mac; m4 baseline run alongside):** closed loop seeds 0–2 with 0 non-tonic spikes; sugar→MN9_L > 5 Hz (10 trials).
**Adoption.** If both pass, the rows go live (basis guessed for magnitude, inferred for sign). Report the change in rates.

**Result, MS (19:25; Mac). Passes; adopted (149 rows live).**
- Closed loop seeds 0–2: 0 non-tonic spikes. Brain excluding ORNs 0.383 / 0.223 / 0.192 Hz (m4 baseline on the Mac: 0.380 / 0.223 / 0.297).
- Sugar→MN9_L 8.9 ± 5.9 / 96.3 ± 3.5 Hz; active cells at 200 Hz 1,070 (vs 850 on backhouse m4 + M0).
- The monoamines now act in the model: 68 types gain receptor-signed pool sensitivities. The other ~14k types stay at 0 (guessed). Magnitude 0.2 is a guess.

**Result, s7-candidate re-screen (19:48; m4 without MS, `runs/s8_ring4/`, 126 runs).** 0/3 everywhere on B1. Default: the ring is silent under every candidate.
- **Under T:** depression, adaptation and their combinations with Delta7 ×4 remove saturation (PEN at rest 0–20 Hz; STD 1–7 Hz). **Adaptation + Delta7 ×4 passes B2 and Q on 3/3 seeds**, but no candidate holds activity after the kick (EPG active ≤ 4%).
- Delta7 ×4 alone and ER tonic 10 mV stay saturated (PEN 166–186 Hz). The gap is mostly silent.
- **Reading.** With correct headings, s7's conclusion holds: the single knobs trade saturation for silence, and no persistent localised state appears. Next check: whether a stronger kick (20 mV, 200 ms, 12 cells) can start a bump in the adaptation + Delta7 ×4 and STD rings.
- ER ring neurons get 73% of their input from other ER neurons (GABA) and ~5% from TuBu. As with Delta7, uniform efficacy lets their mutual inhibition silence them.

### Screen: Delta7 output-only strengthening (19:49)

"Delta7 release ×4" also strengthens Delta7→Delta7 (626 synapses/cell), so the added inhibition mostly silences Delta7 itself. The new candidate-only mechanism `FLYEMU_EDGE_SCALES` (CSV of pre regex, post regex, scale) scales only Delta7→EPG/PEN/PEG (715 edges): ×4, ×8, and ×4 + ring STD. Config T under m4 + MS, σ 0.5, seeds 1–3, standard and strong (20 mV, 200 ms, headings 0/180°) kicks. Screen only.
