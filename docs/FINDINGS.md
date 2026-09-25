# Findings

What session 1 established, restated at the level that matters: **which fields
the model needs, which are filled, and whether what fills them is trustworthy.**

The original session-1 numbering (F1 to F15) was organised around one isolated
subsystem. That framing was wrong and is retired. The findings themselves are
kept, re-sorted into the categories the inventory uses, with the fragment-scoped
results demoted to their own section and their claims narrowed.

Every number below is reproducible from a provenance record in `runs/`, which is
untracked but retained on disk. The code that produced them was deleted in the
session-2 cleanup and is recoverable from git history at commit `1f7f5a4` or
earlier.

| ID | What it says about a field | Status |
|---|---|---|
| **F-RETRACTED-1** | **"A units bug in the published analysis code"** | **withdrawn; the error was mine** |
| F-DATA-1 | Motor-neuron to muscle mapping exists and is complete for the legs | stands |
| F-DATA-2 | The whole-CNS connectome is the better primary graph: brain included, 1,454 proprioceptors, 673 of 708 motor neurons cross-referenced | stands; the traced-percentage framing is withdrawn |
| F-SIGN-1 | 40.8% of modelled inhibition rests on a convention the connectome cannot settle | stands |
| F-SIGN-2 | The sign field is wrong for most leg proprioceptors | stands |
| F-SIGN-3 | The sign field's uncertainty is large enough to flip the outcome, and four cells dominate | stands |
| F-EXCITE-1 | The excitability field is derived from a proxy that is invalid for input populations | stands |
| F-GAP-1 | Afferent firing rates have no published calibration at all | stands |
| F-BODY-1 | The best body model can receive 68% of one leg's motor output and resolves no motor units | stands |
| F-FRAG-* | Results from an isolated open-loop fragment | **scope narrowed, see below** |

---

## F-RETRACTED-1. There was no units bug. The error was mine.

Session 1 reported that the reference repository's oscillation-frequency helper
returns cycles per sample rather than hertz, and presented this as a defect in
published analysis code. It was the opening finding and the opening of the
report.

**It is wrong.** The helper returns cycles per sample by design, and the
published notebooks convert correctly. `Extended Data Figure 3`,
`Extended Data Figure 9` and `Figure 2` all divide by `overallParams.sim.dt`
before plotting; the behavioural notebook computes `freq = 1/period * fps`. I
verified this directly in the clone at commit `faee4b0`.

What actually happened: I called the helper from my own runner without reading
how its authors call it, got a nonsensical 0.01 "Hz", corrected my own code, and
then wrote my mistake up as their defect. Nobody's published result was affected.

The lesson is precisely the one I was claiming to enforce on everyone else. I
published a claim about someone else's work without checking the caller. A
verification discipline that does not apply to my own accusations is not a
discipline. Every finding below has been re-read against this standard.

---

## F-DATA-1. The motor-neuron to muscle mapping is complete and externally corroborated

All 144 front-leg motor neurons in the reference network matched a nerve-cord
annotation on exact integer `bodyId`, each with a named target muscle and traced
status. No silent losses, no name matching.

The corroboration matters more than the completeness. The tibia flexor pool
contains exactly **15 motor neurons per side**. An electrophysiology study that
never touched this connectome reports tibia flexion controlled by
"approximately 15 motor neurons", and cell body size across the pool spans
13-fold, matching the size gradient that study describes.

**For the inventory:** motor-neuron identity, muscle target and pool membership
are *filled* fields with independent support. 20 distinct front-leg muscles.

## F-DATA-2. The whole-CNS connectome should be the source, not the nerve cord alone

| | Nerve cord only | Whole central nervous system |
|---|---|---|
| `:Neuron` nodes | 102,158 | 176,422 |
| Of those, status `Traced` | 23,665 | 165,122 |
| Of those, status absent entirely | **75,643** | 4,214 |
| `:Segment` nodes in the volume | 21,455,359 | 88,404,403 |
| Distinct `type` labels | 4,076 | **11,751** |
| Nerve-cord motor neurons | 731 with a named target | 708, `superclass = vnc_motor` |
| Cross-reference | n/a | **673 of 708 carry a `mancBodyid`** |
| Proprioceptive sensory neurons | 102 in the subset used | **1,454** |
| Brain | absent | present |

**Read those fractions carefully.** Session 1 quoted "94% traced against 23%" as
though it were anatomical completeness. It is not. It is the fraction of nodes
carrying the `:Neuron` label whose `status` field reads `Traced`, and the
`:Neuron` label is itself a threshold-based inclusion decision. The dominant
category in the nerve-cord dataset is not "untraced" but **status absent**,
75,643 nodes with no value in the field at all, which is a different statement.
The segment counts differ fourfold, reflecting the imaged volume rather than
reconstruction quality. Annotation-status fractions must not silently become
completeness percentages.

What does survive without interpretation is the practical case: the whole-CNS
dataset carries the brain, has 1,454 neurons labelled
`mechanosensory_proprioceptive` against 102 in the subset used, and 673 of its
708 `vnc_motor` neurons carry a `mancBodyid` cross-reference. That is enough to
make it the default primary graph. It does not settle whole-CNS against BANC,
which was never compared.

A trap worth recording: the annotations live in different fields. Muscle is in
`type`, not `target`, and the class marker is `superclass = vnc_motor`, not
`class = 'motor neuron'`. A query written against the nerve-cord field names
returns nothing and looks like missing annotation.

**For the inventory:** build identity and connectivity rows from the whole-CNS
graph, carrying nerve-cord work across by `mancBodyid`.

---

## F-SIGN-1. Two fifths of modelled inhibition rests on a convention

| Predicted transmitter | Neurons | Outgoing synapses | Sign as modelled |
|---|---|---|---|
| Acetylcholine | 2,419 | 2,015,846 | excitatory |
| GABA | 1,077 | 1,067,547 | inhibitory |
| Glutamate | 1,095 | 734,379 | inhibitory **by assumption** |

Glutamatergic cells are 23.8% of the reference network and supply **40.8% of its
inhibition**. Excitation and inhibition onto motor neurons are nearly balanced
at a ratio of **1.02**, so the assumption is load-bearing rather than marginal.

In *Drosophila*, glutamate is inhibitory where a glutamate-gated chloride
channel is expressed postsynaptically and excitatory where it is not. **Sign is
a property of the receptor, not the transmitter**, and the connectome does not
contain receptor identity.

Measured sensitivity, sweeping the glutamate multiplier:

| Glutamate treated as | Rhythmicity | Active motor neurons | Median peak rate |
|---|---|---|---|
| Inhibitory, as published | 0.828 | 3.0 | 2.0 Hz |
| Weakened by two thirds | 0.764 | 3.1 | 3.2 Hz |
| Silenced | 0.323 | 54.5 | 37.8 Hz |
| Excitatory (single draw) | 0.003 | 137 of 144 | 198.6 Hz |

**What this does and does not show.** It shows the result is highly sensitive to
the assumption. It does **not** show that either uniform sign assignment is
biologically correct, and session 1's framing implied otherwise. Flipping a large
population's sign and watching activity collapse demonstrates leverage, not
error. Resolving which sign is right requires postsynaptic receptor evidence,
which no connectome contains.

The 23.8% and 40.8% figures are my own computation over the bundled nerve-cord
extract and have not been independently reproduced.

**For the inventory:** the sign field for every glutamatergic cell type is an
*assumption* with a large instance count and demonstrated leverage. Receptor
expression is the field that would settle it, and single-cell transcriptomes
exist. Note that transcriptomic evidence would establish receptor *presence*
while leaving density, localisation, conductance and modulation unresolved, so
it moves these rows to partially constrained, not filled.

## F-SIGN-2. The sign field is wrong for most leg proprioceptors

The transmitter classifier is markedly less confident about sensory neurons, and
on those uncertain calls it labels most leg afferents glutamatergic, which the
reference model renders inhibitory.

| Population | n | Mean confidence | Predicted glutamate |
|---|---|---|---|
| Chordotonal organ | 36 | 0.691 | 69% |
| Hair plate | 61 | 0.705 | 46% |
| Campaniform sensilla | 5 | 0.600 | 80% |
| Mechanosensory bristle | 146 | 0.658 | 68% |
| All sensory | 285 | 0.674 | — |
| Everything else | 4,319 | 0.826 | — |

Published physiology describes the femoral chordotonal organ, the fly's
principal leg proprioceptor, as roughly 150 **excitatory cholinergic** neurons
in claw, hook and club subtypes. Insect mechanosensory afferents are cholinergic
as a class.

So the model assigns an inhibitory sign to the majority of the neurons that
should be the excitatory sensory drive into the leg motor circuit, on calls whose
own confidence is below 0.7. Forcing them excitatory flips 57 of 102 cells.

**For the inventory:** these rows are *filled with a wrong value*. Correcting
them is a literature-based override, not a measurement of these specific cells,
and must be recorded as such.

## F-SIGN-3. The sign field's uncertainty flips the outcome, and four cells dominate

The classifier reports a probability per neuron, not a label. Redrawing each
neuron's transmitter from its own probabilities flips the sign of **436 neurons
on average, 9.5% of the network**, per draw.

| | Draws | Rhythmicity | Active motor neurons |
|---|---|---|---|
| Most-likely labels, as published | 16 | 0.836 +/- 0.119 | 2.6 |
| Sign redrawn from the classifier | 24 | 0.555 +/- 0.406 | 5.2 |

The shape matters, not the mean. Published labels give a tight distribution,
every draw rhythmic. Redrawing gives a bimodal one, with **6 of 24 draws
producing no rhythm at all**.

The failures are traceable. The reference paper's own configuration names a
minimal core of four cells, and that core alone does reproduce a rhythm.
Reconstructing each draw from its seed:

| | Rhythm lost | Rhythm survived |
|---|---|---|
| A core neuron flipped | **4** | **0** |
| No core neuron flipped | 4 | 16 |

Every draw that flipped a core neuron lost the rhythm. Classifier confidence in
those four is 0.90, 0.92, 0.95 and 0.96, giving a 21% chance at least one flips
on any draw. Observed 17%.

**For the inventory:** this is the template for ranking. A field whose
uncertainty changes the qualitative outcome, and which is shared by only a few
instances, is the cheapest thing to go and measure. Four named cells.

Caveat: the annotation exposes only three of the classifier's transmitter
classes, summing to about 0.98 on average and as little as 0.49, so resampling
renormalises over three and redistributes the missing mass proportionally.

---

## F-EXCITE-1. Excitability is derived from a proxy that is invalid for input populations

The reference model sets gain and spike threshold from soma size, normalised to
the network median. But `size` is a segmentation volume measured *inside the
nerve cord*, and not every class has its cell body there.

| Class | n | Relative size | Gain multiplier | Where the soma is |
|---|---|---|---|---|
| Sensory neuron | 283 | 0.108 | **x9.24** | in the leg; only the arbor is in this volume |
| Descending neuron | 1,318 | 0.751 | x1.33 | in the brain; only the arbor is in this volume |
| Intrinsic neuron | 2,471 | 1.031 | x0.97 | in the nerve cord |
| Motor neuron | 144 | 1.668 | x0.60 | in the nerve cord |
| Ascending neuron | 375 | 2.885 | x0.35 | in the nerve cord |

By subclass it is starker: mechanosensory bristles come out at 0.078 of the
median, a **12.9x gain multiplier**.

The two populations that carry input into the circuit are exactly the two whose
measured volume is an arbor rather than a cell. They are handed an
order-of-magnitude excitability advantage that is an artefact of where the
microscope volume was cropped.

**Consequences measured.** An equal injected current produces an eighteen-fold
difference in emitted output between proprioceptors (14.4 Hz) and random
interneurons (0.79 Hz). This generated a confident wrong conclusion twice before
a threshold-matched control settled it. Separately, driving the bristle
population hard made the network so active that no replicate completed in 24
minutes.

**For the inventory:** excitability rows must not be derived from in-volume
segmentation size across classes. Either normalise within class, use a quantity
that means the same thing everywhere, or fit per cell type against physiology.
All three are defensible; the current rule is not.

---

## F-GAP-1. Afferent firing rates have no published calibration

The reference network contains 285 sensory neurons and every class that reports
leg state is present: 146 mechanosensory bristles, 61 hair plates, 36 chordotonal
organ, 5 campaniform sensilla. In the published protocol all of them sit at
exactly zero.

The definitive study of the fly's main leg proprioceptor characterises it with
calcium imaging. It reports which subgroup encodes position, direction and
vibration, and over what joint-angle range, roughly 18 to 180 degrees. It reports
**no firing rates**.

**For the inventory:** the encoding-role rows are filled. The rate-scale rows are
**empty with no source**. Any value used is a fitted parameter and must be
recorded that way, never as a measurement.

---

## F-BODY-1. The best available body receives two thirds of one leg's motor output

`flygym` 2.1.0 bundles the walking body, the flight body and a musculoskeletal
model with GPU physics, which closes the platform question. But the muscle model
exposes **15 tendon actuators on the left front leg only**, with the other leg's
joints locked.

| | Motor neurons |
|---|---|
| Have a corresponding actuator | 49 of 72 (68%) |
| Have no actuator at all | 23 of 72 (32%) |
| Mean motor neurons per actuator | 3.3 |

Absent entirely: the femur reductor, **all tarsus muscles**, meaning no active
foot, and the long tendon muscles. The 15-neuron tibia flexor pool, the one group
with good published physiology, **collapses onto a single actuator**, so the size
principle that grades force cannot be expressed.

**For the inventory:** muscle rows exist for 15 of 20 front-leg muscles at
whole-muscle grain, and motor-unit rows do not exist at all. Extending the muscle
model is prerequisite work for any embodied claim.

---

## F-FRAG. Results from the isolated fragment, with their scope narrowed

Session 1 ran 333 simulations of a 4,604-neuron front-leg premotor network with
no brain, no body, no sensory input from anything physical, driven by a constant
injected current into one descending neuron.

**What it showed.** A rhythm near 10 Hz reproduced in every one of 16 parameter
draws, with rhythmicity 0.836 +/- 0.119. Scrambling the wiring while preserving
out-degree, weights and transmitter composition per class destroyed it, dropping
rhythmicity to 0.139 and raising active neurons from 97 to about 1,900. That
control is the session's strongest evidence that the anatomy carries real
functional information, and it transfers.

Across all 333 simulations, no run produced both clear rhythmicity above 0.5 and
median peak motor-neuron rate above 10 Hz. Rhythmic runs topped out at 8.5 Hz
against a measured 30 Hz resting rate for a real slow tibia-flexor unit. Runs
reaching physiological rates never exceeded 0.31 rhythmicity, and the single one
that came closest was the scrambled control.

**What it does not show, and what session 1 wrongly implied.** This was
originally reported as a property of the model class. It is not. Every run was
an isolated, deafferented, open-loop fragment. The things that normally set a
premotor circuit's operating point were all absent: descending drive from the
central complex, visual and mechanosensory context, and neuromodulator state.
Demanding that the fragment produce both a rhythm and physiological force was
demanding that a part do a whole animal's job, and its failure to do so is weak
evidence about anything.

Two corollaries survive as facts about the fragment, and only about it. Sensory
modulation at any frequency from 2 to 20 Hz did not restore the rhythm, with the
motor output failing even to entrain to the drive. And correcting the
excitability artefact moved the operating point without creating a regime that
had both, while also silently rescaling what counts as a meaningful sensory
input, because raising afferent thresholds ninefold put small drives entirely
below threshold.

**For the inventory:** treat F-FRAG as a demonstration that the parameter
conventions are fragile, which the F-SIGN and F-EXCITE rows capture directly. Do
not treat it as a bound on what a whole organism can do.

---

## The methodological lessons, which cost the most to learn

**A mean can average across two regimes.** One run reported mean rhythmicity
0.405 with 25 Hz output, which read as a useful compromise between rhythm and
force. The per-draw values were four draws near 0.5 with 1 to 4 Hz and two near
0.1 with 48 to 92 Hz. The mean described no simulation that ran. Checking the
distribution took two minutes and reversed the conclusion.

**Equal input is not equal perturbation.** See F-EXCITE-1. A drive comparison
across populations produced a confident wrong answer, then its own reversal, then
a third answer, before a threshold-matched control settled it.

Both produced publishable-looking findings that survived one round of scrutiny
and died on the second. Any perturbation result in any model built here needs
both checks before it is believed.

---

# Session 3: the whole organism, built and run

Session 3 built the thing rather than enumerating what it would need. The
inventory is emitted by the model as a byproduct of running it, so it cannot
drift from what the code actually reads. Model family M v1 is declared in
`docs/MODEL_M.md`.

| ID | What it says about a field | Status |
|---|---|---|
| F-LOOP-1 | The closed loop runs: 176,422 neurons and 25.8M edges driving 126 MuJoCo joint torques | stands |
| F-COUNT-1 | The model is short of 18 distinct inferences, propagated to 27.3M model elements | stands |
| F-GAIN-1 | Activity is set by background drive, not by synaptic efficacy | stands |
| F-TORQUE-1 | The torque per spike this body needs matches the measured force per spike of real motor units | stands, with an assumed moment arm |
| F-BODY-2 | 380 of 708 motor neurons have no actuator to drive | stands |
| F-NOISE-1 | A dimensional error in the noise term silenced the whole brain | fixed; recorded as a lesson |
| F-C2-1 | C1 and C2 are currently the same run | not a control yet |

## F-LOOP-1. The loop closes, and the fly flails

`male-cns:v1.0`, queried live and cached: **176,422 neurons, 25,862,574
neuron-to-neuron edges, 125,024,863 synapses**, which reproduces the figures
`docs/PLAN.md` derived independently. On the body side, NeuroMechFly compiles to
70 segments and **126 torque-actuated joint degrees of freedom**.

The loop is `body state -> afferent drive -> CNS -> motor spikes -> torque ->
body`, at a 0.1 ms timestep, with nothing crossing except through those
channels. No prescribed gait, no descending command, no controller.

Cost, measured: about 2 s of compute per 50 ms of simulated fly on an M2 Pro,
peak 2.0 GB. Roughly 40x slower than real time, which makes tier A cheap and
tier C affordable. Propagation is event-driven, so cost scales with spikes times
out-degree rather than with the 25.8M edges; at 0.8 Hz mean rate that is about
13,000 edge updates per step instead of 25.8 million.

It falls, lands on its side and thrashes. It cannot right itself.

## F-COUNT-1. Eighteen numbers, twenty-seven million places

The strict control C0 refuses to integrate and enumerates what it lacks. The
result is the shape of the gap rather than its size:

| Unresolved requirement | Model elements |
|---|---|
| `connection_class:all.efficacy_per_synapse` | 25,862,574 |
| eight `cell_type:all` biophysics rows (tau_m, v_rest, v_th, v_reset, t_ref, tau_s, delay, noise) | 176,422 each |
| `transmitter:glutamate.sign` | 28,199 |
| `transmitter:unclear.sign` | 25,159 |
| `transmitter:dopamine/serotonin/octopamine.sign` | 4,447 / 483 / 126 |
| `afferent:all.rate_gain`, `afferent:all.resting_drive` | 3,246 each |
| `motor_unit:all.force_per_spike` | 328 |
| `muscle:all.activation_tau` | 48 |
| **18 requirements** | **27,339,232 elements** |

**That ratio is the finding.** The model is not missing 27 million measurements;
it is missing eighteen, each propagated to millions of places. A completeness
percentage over model elements would read as catastrophic and a percentage over
requirement rows would read as almost fine, and neither would describe the
situation. What the number says is that the model's physiology is currently
**one shared guess per quantity for the entire animal** - every neuron in the
brain has the same membrane time constant - so the inventory's next job is not
to find 27 million values but to find out how many genuinely distinct ones there
are. `tests/test_organism.py` pins this: one shared guess must stay one row.

The full run inventory is 60 rows over 53.9M elements: 25.9M measured (the
connectivity and the identity annotations), 27.5M assumed, 188k unresolved with
no default at all.

## F-GAIN-1. Activity is set by background drive, not by synaptic efficacy

A tier-A sweep, 24 conditions at 50 ms, over the two guesses with the largest
reach: per-synapse efficacy (25.8M edges) and background noise (176,422
neurons).

| | efficacy 0.05 mV | efficacy 0.8 mV | factor |
|---|---|---|---|
| noise 1.0 | 0.013 Hz | 0.047 Hz | 3.6x |
| noise 2.5 | 5.07 Hz | 8.31 Hz | 1.6x |
| **factor across noise** | **399x** | **178x** | |

A sixteenfold change in every synapse in the animal moves the mean rate by less
than a factor of four. A 2.5-fold change in the background term moves it by more
than two orders of magnitude. No condition ran away.

**What this does and does not show.** It does not show that synaptic strength
does not matter in a fly. It shows that *in this model as currently built*, the
network is driven by the term that stands in for everything M omits, not by the
connectome. The recurrent gain is too low for the anatomy to be doing the work,
which is what one would expect when every neuron shares one threshold and one
time constant. Two competing explanations, both preserved: the efficacy default
is far too small for the anatomy to matter, or the uniform biophysics prevents
any recurrent amplification regardless of efficacy. The distinguishing
observation is whether per-cell-type thresholds change the ratio, which requires
the biophysics rows to be differentiated first.

This is a direct warning about what would happen if the model were fitted now.
Any optimiser pointed at behaviour would tune the noise term, because that is
where the leverage is, and would be compensating for the omitted subsystems by
corrupting a parameter that has no biological referent at all.

## F-TORQUE-1. The torque this body needs is the torque a real fly delivers

Model units, measured from the compiled body rather than assumed: length mm,
time s, mass g, so force is µN and joint torque µN·mm. The fly weighs 1.02 mg,
about 10 µN.

Applying constant torque to one femur-tibia joint: below about 0.1 µN·mm the
joint's own passive spring dominates and nothing moves; at 1.0 µN·mm the joint
swings 0.058 rad against gravity. So **the body model's passive joint stiffness,
a NeuroMechFly default rather than a fly measurement, sets the scale of what
counts as a motor command at all.**

Sweeping torque per motor spike, 200 ms per point, at 7.7 Hz mean motor rate:

| Torque per spike (µN·mm) | Mean torque | Displacement | Thorax height |
|---|---|---|---|
| 0 | 0 | 0.69 mm | 0.71 mm |
| 0.1 | 0.027 | 0.69 mm | 0.70 mm |
| 1.0 | 0.263 | 0.68 mm | 0.95 mm |
| 3.0 | 0.791 | 0.50 mm | **1.50 mm** |
| 10.0 | 2.53 | 1.50 mm | 0.53 mm |
| 30.0 | 7.89 | **3.61 mm** | 0.40 mm |

Below 1 µN·mm the body is indistinguishable from a dead one: displacement
0.69 mm is gravity settling, identical to the zero-torque row. At 3 µN·mm it
holds itself measurably higher. At 10 and above it displaces itself and breaks
foot contact.

**The cross-check.** Azevedo et al. 2020 measured force per spike in the tibia
flexor pool: slow units below 0.1 µN, intermediate about 1 µN, fast about 10 µN.
Through a moment arm of order 0.1 to 1 mm, that is 0.01 to 10 µN·mm of joint
torque per spike - the same range in which this body model starts to move. Two
independent quantities, a published electrophysiological measurement and the
mechanical requirement of a body model built from anatomy, agree to within the
uncertainty of the moment arm.

**What it does not establish.** The moment arm is assumed, not measured, and one
shared value stands for every motor unit, so the size principle that spans that
whole two-order range cannot be expressed. The agreement is a consistency check
on the units and the scale, not evidence that the neuromuscular model is right.

## F-BODY-2. Over half the motor output has nowhere to go

Of 708 `vnc_motor` neurons, **328 are mapped to 48 joint actuators and 380 are
not**. The unmapped ones are registered as unresolved rows rather than dropped,
because discarding them silently would make the interface look complete.

| Not mapped | Why |
|---|---|
| wing (67), abdominal (214), neck (24), haltere (16) motor neurons | the muscle-to-joint map covers legs only |
| `MNxx##` leg types | the connectome names no muscle for them |
| leg motor neurons in pools whose muscle has no matching actuator | the body model has no such degree of freedom |

Every one of the 20 muscle-to-joint assignments that *was* made is a guess about
this body model's coordinate conventions, and **the sign is not known to match
flexion and extension**. A wrong sign inverts that muscle's entire action. These
are recorded as assumed with instance counts, and settling them needs either the
body model's own documentation or a per-joint calibration experiment.

This is F-BODY-1 restated at whole-body scale, and it is worse than the one-leg
version suggested: the limit is not only the musculoskeletal model's coverage
but the absence of any wing, neck or abdominal muscle map.

## F-NOISE-1. A dimensional error silenced the entire brain

The first closed-loop run produced **zero spikes in 176,422 neurons**. The cause
was mine, not biology: the noise term was specified in mV per sqrt(ms) but
applied as a steady-state depolarisation, so the exponential-Euler update scaled
it by `1 - exp(-dt/tau_m)` and a 1.5 mV noise amplitude became 0.0024 mV per
step. Noise now enters as a membrane increment, with stationary standard
deviation `sigma * sqrt(tau_m / 2)`.

Worth recording because of how it would have read. A silent whole-brain model is
exactly the result this project would be tempted to interpret: "the measured
parameters cannot sustain activity" is a publishable-sounding finding, and it
would have been a unit error in nine lines of my own code. The
`test_the_fly_weighs_about_ten_micronewtons` check exists for the same reason on
the body side.

## F-C2-1. C1 and C2 are the same run, so C2 is not a control yet

C1 (one declared default per subsystem) and C2 (what published precedents
assume) returned **identical numbers**, because step 3 of the plan - walking the
published precedents and recording what each puts in the unresolved rows - was
not done. The `conventional` values currently equal the `minimal` ones.

So this session measured C0 against C1 and nothing else. C0 against C1 says how
much of the model is convention rather than measurement: all of its physiology.
C1 against C2, which would say whether the specific conventions in current use
are doing real work, is untested and its value is not yet populated.

---

## F-BODY-3. The body model has no joint limits, and one passive stiffness for every joint

Measured directly on the compiled model, not read from documentation.

| Property | Value | What it means |
|---|---|---|
| Joints with `jnt_limited` set | **0 of 127** | no joint has an anatomical range of motion |
| Actuators with `ctrllimited` | 0 of 126 | no command bound |
| Actuators with `forcelimited` | 126 of 126 | torque is capped at +/-30 uN*mm |
| Distinct joint stiffness values | **{0, 10}** | one value for every actuated joint |
| Distinct damping values | {0, 0.5} | one value for every actuated joint |
| Distinct armature values | {0, 1e-6} | one value for every actuated joint |

**No joint limits** means the femur-tibia joint can rotate through the femur,
the head can rotate through the thorax, and a leg can fold through itself. The
only thing resisting a joint is its linear spring, which never stops anything,
it only pulls back proportionally. So every posture is reachable, including
anatomically impossible ones, and any "behaviour" the model produces may pass
through configurations the animal cannot adopt. For a model whose stated goal
is full-body biological fidelity this is a first-order defect.

**One stiffness for every joint** means the three-degree-of-freedom thorax-coxa
articulation and the smallest tarsal joint have identical passive mechanics.
Measured consequence: driving any single actuator with 3 uN*mm for 60 ms
deflects its joint by **12.018 degrees, identical to three decimal places for
all 126 actuators**. That uniformity is the signature of a shared default, not
of a body. It also means the passive spring, a body-model default rather than a
fly measurement, is what sets the operating point of every joint, which is
F-TORQUE-1 restated: the stiffness decides what counts as a motor command.

## F-SIGN-4. Measured actuator-to-foot calibration overturns several muscle sign assignments

The muscle map needs a sign per muscle, and anatomy cannot supply it: anatomy
says a muscle flexes a joint, not which direction "flex" is in this model's
coordinate frame. So it was measured. With gravity off, from the neutral pose,
each actuator was driven alone at +3 uN*mm and the tarsal tip displacement
recorded in the thorax frame. Left front leg:

| Actuator, driven positive | Foot fore | Foot lateral | Foot up | Leg length | Reads as |
|---|---|---|---|---|---|
| ThC pitch | **-0.194** | 0.000 | -0.190 | 0.000 | retraction, foot backward |
| ThC roll | -0.177 | **+0.246** | +0.094 | 0.000 | abduction, foot outward |
| ThC yaw | +0.002 | +0.045 | **+0.050** | 0.000 | axial rotation, small |
| CTr pitch | -0.101 | -0.087 | **-0.289** | +0.074 | **depression**, foot down |
| CTr roll | +0.125 | **-0.182** | -0.013 | +0.005 | adduction, foot inward |
| FTi pitch | -0.160 | -0.090 | -0.150 | **-0.055** | **flexion**, leg shortens |
| TiTa pitch | -0.080 | -0.040 | -0.096 | -0.017 | tarsal flexion and depression |
| tarsal 1-2 to 4-5 | small, monotonically decreasing | | | | tarsal curl |

All displacements in mm. A first version of this measurement used the angle
between body origins and returned zero for every joint, because a child body's
origin sits AT its own joint, so rotating the joint does not move it. The
readout has to be a distal point; it is now the tarsal geom centre.

**Against my assignments in F-BODY-2, at least three are inverted:**

| Muscle | I assigned | Measurement says | Motor neurons affected |
|---|---|---|---|
| Pleural remotor/abductor | ThC pitch, negative | positive ThC pitch retracts, so remotion is **positive** | 14 |
| Tergopleural/Pleural promotor | ThC pitch, positive | promotion is **negative** | 8 |
| Sternal adductor | ThC roll, positive | positive roll abducts, so adduction is **negative** | 6 |

and one is mislabelled rather than merely wrong in sign: the **coxa-trochanter
joint is a levator/depressor**, not a flexor/extensor. Positive drive lowers the
foot by 0.289 mm while lengthening the leg by 0.074 mm. The connectome's
"Tr flexor" and "Tr extensor" names therefore need an anatomical reading before
a sign can be assigned to them at all, and that covers a further **80 motor
neurons** (Tr flexor 35, Acc. tr flexor 22, Tr extensor 11, Tergotr. 12).

**One assignment is confirmed.** Positive femur-tibia drive shortens the leg, so
Ti flexor positive and Ti extensor negative are correct. That is the pool with
the published physiology, which is some luck.

So of 328 mapped motor neurons, **28 carry a measurably inverted sign and 80
more cannot be signed without anatomy**. A wrong sign does not degrade a muscle,
it reverses it, so these are not small errors. This is the concrete value of
measuring the interface instead of assuming it.

Reproduce with `uv run python scripts/calibrate_joint_signs.py`; the full table
for all 126 actuators is `data/derived/joint_sign_calibration.csv`.

---

# Session 3, part 2: the body audited against the literature

Four `Explore` agents researched body morphometrics and model provenance, which
joints are real, leg muscle anatomy, and the complete brain-body interface.
Their citations are leads I have **not** independently verified except where
stated; several of their sources were reachable only at title level. What I did
verify myself is marked.

| ID | What it says | Status |
|---|---|---|
| F-JOINT-1 | 33 of 126 powered degrees of freedom are not joints; now locked | fixed |
| F-MASS-1 | The model's mass is measured fractions on an assumed total, and 2.45% of it is a solver floor | stands |
| F-STIFF-1 | The passive joint parameters are documented guesses, changed 200-fold between releases | stands |
| F-SIGN-5 | Anatomy plus calibration corrects five muscle assignments; two must be unmapped | fixed |
| F-LTM-1 | The long tendon muscle is one muscle on one tendon, not three muscles on three joints | fixed |

## F-JOINT-1. A third of the powered joints were not joints

The rigging supplies 126 rotational degrees of freedom and session 3 powered
every one. The audit in `src/flyemu/joints.py` now classifies each as powered,
passive or locked, with a source per rule. **126 actuators became 91**, 33
joints are pinned and 2 are passive, and **all 126 hinges have a range of
motion where previously none did.**

| Locked | n | Why |
|---|---|---|
| head to eye, 3 axes each side | 6 | the compound eye "attaches rigidly to the head capsule"; what moves is the retina sliding beneath a stationary lens array, ~15 deg peak, via two muscles inserting on the retina (Fenk et al. 2022, Nature 612:116-122). A rigid eye rotation swings the lenses and the head silhouette, which is the wrong mechanism |
| funiculus to arista, 3 axes each side | 6 | the arista is a cuticular process, not an articulation. NeuroMechFly's own authors: these degrees of freedom exist "to emulate the compliance of the arista" |
| haltere roll and yaw | 4 | the haltere beats in one plane, driven by a single asynchronous muscle with a passive downstroke |
| abdominal axial twist, 5 joints | 5 | segments bend and telescope; no evidence of independent twist |
| pedicel-funiculus roll and yaw | 4 | the receiver rotates about one axis |
| head-pedicel roll and yaw | 4 | the scape-pedicel joint is the only actively controlled antennal joint; its measured active movement is one rostro-caudal rotation of 5-15 deg |
| rostrum-haustellum roll and yaw | 2 | a single extension/flexion axis |
| head-rostrum roll and yaw | 2 | protraction/retraction about one axis |

Both independently built whole-body fly models exclude eye degrees of freedom,
which is corroboration rather than one paper's opinion.

**Ranges are almost all assumed, and the inventory says so.** Only four carry a
real anatomical measurement: femur-tibia **18 to 180 deg** (Mamiya et al. 2018),
head yaw **+/-15 deg** (Cellini & Mongeau 2020/2022), scape-pedicel **5-15 deg
caudal** (Mamiya et al. 2011), and wing stroke amplitude **140 +/- 10 deg** with
deviation ~25 deg peak-to-peak (Fry et al. 2005). Everything else is an envelope
around walking kinematics, and **behavioural range is not an anatomical limit**;
it is a validation target. Recorded as assumed.

Two judgement calls left open rather than settled. The seventh leg degree of
freedom is needed by both published models to fit 3D kinematics, but one places
it at coxa-trochanter and the other at trochanter-femur, front legs only; both
are inverse-kinematics inferences. And **trochanter-femur fusion is contested**,
not established: asserted in one model paper, challenged by the other and by the
connectome's documentation of a large trochanter flexor with 8 motor neurons.

## F-MASS-1. The fly's mass is a fraction table on an assumed total, and 2.45% of it is a solver floor

I reported earlier that the model weighs 1.02 mg, "the right order for a real
fly", and treated that as reassurance. It is weaker than that.

- The per-segment masses are **another laboratory's measured mass fractions**
  (head 12.5%, thorax 31%, abdomen 45%, legs 11%, wings 0.5%, n=30; Szczecinski
  et al. 2018) multiplied by an **assumed** 1 mg total. Szczecinski et al.
  report only percentages, so the 1 mg denominator is not theirs.
- **No density is stated anywhere** in either model paper or the model files.
- `mujoco_globals.yaml` sets `boundmass: 1e-6` with the comment "some tarsal
  segments have their masses increased to this". **32 of 69 bodies** have
  nominal masses below that floor and are raised to it, which is what turns
  0.99978 mg into the 1.02431 mg the compiled model reports. So **about 2.45% of
  the model's mass is a solver floor rather than biology, concentrated distally
  in the tarsi, aristae, pedicels and halteres** - exactly where it inflates leg
  inertia and contact dynamics most.

For comparison, the other published model's inertial properties are traceable to
**52 flies weighed part by part** (0.983 mg total), converted to per-part
densities. The two independent specimens also disagree on the head/thorax/
abdomen split (12.5/31/45% against 15.3/34.6/38.7%) and by threefold on wings.
Published female wet masses span 0.91 to 1.16 mg across studies; they should not
be averaged.

**My test `test_the_fly_weighs_about_ten_micronewtons` still passes and is still
worth having**, but it verifies unit consistency, not that the mass distribution
is measured. That distinction is now in the inventory.

## F-STIFF-1. The passive joint parameters are documented guesses

F-BODY-3 measured that every joint shares one stiffness, and inferred that this
was a default rather than a body. The provenance confirms it outright.

- Stiffness 10, damping 0.5, armature 1e-6, force range +/-30 are **not in
  either model paper**. They exist only in code. Only the armature carries a
  rationale and it is explicitly numerical: "Should be small enough to not
  affect dynamics."
- The values **changed by up to 200-fold between releases** (actuated stiffness
  0.05 to 10, damping 0.06 to 0.5, force range +/-65 to +/-30) with no
  justification recorded. Quantities derived from measurement do not move like
  that across a refactor.
- The authors say so themselves in the project's own tutorial: "it's not always
  possible to experimentally calibrate every single one of them, but we have to
  somehow make an educated guess."
- The earlier release differentiated actuated, non-actuated, neck and tarsal
  joints; the version in use here applies **one global value to all**, so its
  passive mechanics are coarser than its predecessor's, not finer.

Since F-TORQUE-1 showed the passive spring decides what counts as a motor
command, the operating point of this whole organism currently rests on an
admitted guess that moved 200-fold between two releases of somebody else's
library.

## F-SIGN-5. Anatomy plus calibration: five corrections, two muscles unmapped

The muscle labels in the connectome turn out to originate from one source's
supplementary tables, which carry an explicit Action column. Combining that with
the measured calibration of F-SIGN-4 gives a sign per muscle that rests on two
independent things: anatomy for the action, measurement for which sign produces
it in this body.

| Muscle | Was | Now | Why |
|---|---|---|---|
| Sternotrochanter | flexion | **extension** | it is the sternotrochanter *extensor*; it inserts on the same trochanter extensor tendon as Tr extensor and Tergotrochanter. A plain inverted-action error, 14 motor neurons |
| Tr flexor, Acc. tr flexor | + | **-** | anatomy: they flex the coxa-trochanter joint. Calibration: positive drive *extends* it. 57 motor neurons |
| Tr extensor, Tergotr. | - | **+** | same axis, opposite sense, 23 motor neurons |
| Ta depressor / Ta levator | depressor +, levator - | **swapped** | the names read backwards: the tarsus *depressor* EXTENDS the tibia-tarsus joint and the *levator* FLEXES it. Levator/depressor does not map onto flexor/extensor |
| promotor / remotor / adductor | inverted | **corrected** | as measured in F-SIGN-4, 28 motor neurons |
| **Fe reductor** | CTr roll | **unmapped** | its function is recorded as "Unknown" three separate times in the source; the trochanter-femur joint it would serve is thought to be fused, and the only supporting idea is a cross-species hypothesis that it acts as a spring. 20 motor neurons had a signed torque hung on nothing |

One further trap worth recording: "levator/depressor" is not a sign. In the same
animal the trochanter levator *flexes* its joint while the tibia levator
*extends* its joint. Any pipeline that reads those names as directions will
invert some muscles and not others.

The tergotrochanter's direction is right but its mechanics are not a graded
walking muscle: it is the giant-fibre escape **jump** muscle, and it is
**biarticular**, crossing the thorax-coxa joint before extending the trochanter.
A single-joint assignment is an approximation, now recorded as one.

## F-LTM-1. The long tendon muscle is one muscle, one tendon, four joints

The three labels `ltm`, `ltm1-tibia` and `ltm2-femur` are **fibre populations of
one muscle** whose fibres sit in the femur and the tibia and pull a single
tendon, the retractor unguis, which runs to the pretarsal claw. My first map put
them on two different joints, which made them antagonists of themselves.

This dovetails with the tarsal finding: there are **no muscles inside the tarsal
segments** (Soler et al. 2004), and the tarsus is "moved together by muscle
tension on the long tendon" (Haustein et al. 2024). So four independently
torqued inter-tarsal joints per leg was wrong in kind. They are now **one
tendon-coupled group per leg**, driven by the long tendon motor pool, which is
also the largest coherent motor pool in the leg.

What remains wrong: the tendon's real target is the **claw**, and the body model
has no claw or grip degree of freedom, so tarsal flexion is standing in for claw
retraction. Recorded as the gap it is.

**Net effect on the interface:** 434 motor neurons now drive something, against
328 before, and they drive 56 actuator targets rather than 48 - while 20 motor
neurons were correctly *removed* from a mapping that was not supported.

---

# Session 3, part 3: the physics

## F-COLLIDE-1. The fly could pass through itself, and two separate bugs hid it

Ben saw legs clipping through the body and through each other in the
visualiser. Verified on the model rather than inferred: **every one of the 70
geoms had `contype = 0` and `conaffinity = 0`**, and the model's only contacts
were 55 explicit pairs, **all 55 with the ground plane**. There was no
leg-to-leg, leg-to-body or wing-to-body collision of any kind. The fly was a
set of rigid bodies that could only touch the floor.

Fixing it took two corrections, and the first one is a trap worth recording.

**Setting the geom masks does nothing on its own.** MuJoCo prunes candidate
pairs at the **body** level before it looks at geoms, using masks it aggregates
from the geoms at compile time. Those had compiled to zero, so enabling
`geom_contype` and `geom_conaffinity` left `body_contype` at zero and the
broadphase discarded every pair. Measured: 0 fly-on-fly contacts before setting
the body masks, 30 after, with the foot sitting 0.57 mm inside the thorax in
both cases beforehand.

**Colliding everything is also wrong.** With all geoms colliding, the contacts
that appeared were between segments that NEST at their articulations - head
against haustellum, rostrum against labrum, abdomen against haltere. A convex
hull of the rostrum overlaps the haustellum it sits inside, so those contacts
are permanent and fight their own joints. MuJoCo excludes a body from its
parent but not from its grandparent.

Resolved with one collision bit per anatomical region - six legs, head complex,
thorax, abdomen, wings, halteres - colliding **across** regions and not within
them, which is what MuJoCo's `(contype1 & conaffinity2)` rule is for. After
that the contacts are the right ones:

| | fly-on-fly contacts | example pairs |
|---|---|---|
| self-collision off | **0** | - |
| all geoms colliding | 30 | head/haustellum, rostrum/labrum, **nested pairs** |
| by region | **12** | thorax/trochanterfemur, wing/tarsus, abdomen/haltere |

`spec.add_exclude` was tried first and **hard-crashed the compiler with no
traceback**, which is why the bitmask approach was used instead.

Cost: none worth measuring. The body still runs at **1.3x slower than real
time** with 85 colliding mesh geoms.

Known limitation: collision is disabled *within* a region, so a leg cannot
collide with itself. Joint limits constrain intra-leg folding instead.

## F-PHYS-1. What is now implemented, and what each approximation costs

| Physics | State | The approximation, stated |
|---|---|---|
| Self-collision | implemented | convex hulls, so concave parts such as the claw and wing edge are slightly fattened; no within-region collision |
| Joint ranges | implemented | 102 ranges, fitted to real poses by the body model's authors; only four rest on a published anatomical measurement |
| Passive joint mechanics | improved | 8 differentiated parameter groups instead of one global value, but still the body model's numbers, not measurements |
| Tarsal tendons | implemented | 8 real MuJoCo tendons; the tarsus has no muscles of its own and is moved by the long tendon |
| Adhesion | implemented | **a substitute mechanism**: adhesion actuators stand in for claw and pulvillus mechanics, driven by the long tendon motor pool. Declared as a scaffold |
| Aerodynamics | implemented | MuJoCo's **quasi-steady** fluid model: added mass, blunt and slender drag, angular drag, Kutta and Magnus lift. It does **not** capture delayed stall and the leading-edge vortex, rotational circulation, or wake capture - the mechanisms that dominate insect flight at Reynolds number ~100 |
| Cuticular strain | proxy | campaniform afferents read the load transmitted through each segment rather than ground contact force. A loaded leg need not touch the ground, so contact force was the wrong quantity. **The segments are still rigid**, so there is no strain field |
| Muscle model | absent | torque is proportional to activation; no force-length, no force-velocity, no Hill-type mechanics, no motor units |
| Air flow, acoustics, light transport, odour advection | absent | the channels that need them have no transduction model either |
| Hemolymph, tracheal gas exchange | absent | |

So the honest answer to "are the physics fully realistic" remains **no**, but
the list of what is missing is now explicit, sized, and in the inventory rather
than in my head.

## F-AXIS-1. A body swap silently inverts hard-coded signs

Switching body models exposed a latent design error. **`FTi pitch +` flexes the
leg in NeuroMechFly and extends it in flybody**, because the two models use
different Euler decompositions (`pitch_roll_yaw` against `yaw_roll_pitch`). Every
hard-coded muscle sign would have inverted silently, and nothing in the model
would have complained.

The muscle table now declares the anatomical **action** - flexion, levation,
protraction, adduction, rotation - and the **sign is resolved at build time
against the measured calibration for whichever body is in use**. 16 of 18
muscle rows are now `derived` instead of `assumed`; the two that remain assumed
are the rotation directions, which the sources do not settle.

A limitation this exposed, recorded rather than hidden: flybody's thorax-coxa
Euler axes are not aligned with the anatomical action axes, so **one actuator
serves two actions** - positive roll both protracts and adducts. The resolver
picks the axis with the largest component, so the sternal adductor and the
pleural promotor currently share an axis and a sign. The correct treatment is a
least-squares projection of each muscle's action across all three axes, giving
genuinely multi-axis muscles. Not done.

---

## F-COLLIDE-2. The collision fix had dropped the feet

Fixing the wings exposed that my own suffix rule - collide geoms ending `_body`
or `_lower` - had also silently excluded **all six `tarsus5` segments**, whose
geoms are named `_brown`. Those are the feet: the surfaces that touch the
ground, carry the claw, and do the gripping. Ground contact still worked,
because that runs through explicit pairs, so nothing looked wrong.

The rule is now per body rather than per name: a body's collision surface is
its designated physical geom where it has one, and otherwise **the simplest
geom that spans the segment**. The wing membrane spans the same extent as its
venation overlay with 1,500 vertices against 18,684, so collision costs
963 us per step instead of 4,656.

A test now pins it: every body must have a collision surface, the wing
membranes and all six feet must collide, and the colour overlays must not.

## F-VISION-1. The graph has photoreceptors and no map for them

The optic lobe is now driven, and what it can and cannot do is set by an
absence in the data rather than by the model.

**What is there.** `male-cns:v1.0` carries real photoreceptor identities:
3,377 R1-R6, the pale and yellow R7/R8 subtypes, the dorsal-rim R7d and R8d,
and the seven-cell Hofbauer-Buchner eyelet. The body renders 721 ommatidia per
eye in two spectral channels, measured at **11.5 ms per readout**, two 512x450
renders plus the hex conversion, so eyes at 100 Hz are entirely affordable.

**What is missing is the map.** A photoreceptor in this dataset has no column,
no hex coordinate and no position: its only spatial annotation is the lamina
ROI. `optic-lobe:v1.1` carries no `olHex` coordinates either. So **which
ommatidium a given photoreceptor looks through cannot be established from these
releases at all.**

That leaves two options and only one of them is honest. Assigning ommatidia
arbitrarily would give the network spatially structured input through a
scrambled map, which would look like working vision while being nothing of the
kind, and would make any motion or looming result meaningless in a way that is
hard to detect downstream. So the channel is deliberately **non-retinotopic**:
each photoreceptor is driven by the mean luminance of the ommatidia matching
its spectral type and eye. That is real visual information - per-eye
brightness, which is what phototaxis needs - and it carries no spatial claim.

Registered as unresolved, with instance counts: retinotopy for all 6,091
photoreceptors; polarisation sensitivity for the dorsal rim, since the renderer
produces luminance only; and the HB eyelet, which is extraretinal and circadian
and does not look through an ommatidium at all.

**A count worth keeping.** A fly has roughly 800 ommatidia per eye and six
R1-R6 in each, about 9,600 R1-R6 in total. This graph holds 3,377. The primary
graph does not contain one photoreceptor per ommatidium per eye, so any vision
model built on it is built on a subset.

**Measured effect.** Before: the optic lobe's 6,098 receptor neurons received
nothing and fired at 0 Hz. After: 6,091 are driven, firing at **4.24 Hz mean
with 20.8% active**. Half the neurons in the graph sit in the optic lobe, so
this is the largest single change to what the network is doing.

M v1's standing falsehood applies here and is worth restating: fly
photoreceptors are **graded, not spiking**. Making them spike is wrong for the
optic lobe, which is half the animal's neurons.

---

# Session 4

## F-COUNT-2. 9,311 of the simulated "neurons" were fragments

`male-cns:v1.0` returns 176,422 `:Neuron` nodes. The male CNS paper (Cell, September
2026) reports 166,691 neurons. The difference is proofreading status, which the
loader read but never used:

| status | bodies | median presynapses |
|---|---|---|
| Traced | 165,122 | 145 |
| Orphan / Anchor / Assign / unset | 11,300 | 23 |

Of the 11,300, 9,311 have no cell type at all; they are unattached fragments,
and each was being simulated as a whole neuron with its own soma threshold and
noise. The other 1,989 are typed, and 1,983 of those are R1-R6 photoreceptors
with no status set, so a status-only filter would silently have cut the
retina's R1-R6 from 3,377 to 1,394.

**Policy now:** `Traced` or typed. **167,111 neurons, 25,578,757 edges,
124,162,592 synapses** (0.7% of synapses dropped). The 420-neuron gap to the
published count remains unexplained and is recorded, not closed.
`test_fragments_are_not_simulated_as_neurons` pins both halves: untyped
non-traced bodies out, every R1-R6 in.

Earlier counts in this file (176,422; 25,862,574 edges; the F-COUNT-1 instance
counts) were under the old all-nodes policy and are left as recorded.

## F-GAIN-2. The anatomy is load-bearing, and it ignites

Answers F-GAIN-1. Open loop, brain only, noise off, Shiu 2024 parameters
borrowed as `assumed` (`--profile shiu2024`), edges with >= 5 synapses (6.24M
edges), Poisson kicks into identified sensory types. Each assay is also run on
three degree-preserving shuffled graphs. Runs: `runs/assay-*-shiu2024*`,
`runs/calibrate-gain-shiu2024`.

**1. At Shiu's own synaptic scale the real brain ignites; shuffled brains never do.**
Any sugar input from 25 Hz recruits ~16,000 neurons at ~6 Hz mean, and the
state outlives the stimulus: 14,401 neurons still active 200-600 ms after it
ends. Shuffled graphs at the same scale recruit 70-460 neurons and never drive
MN9. So the network's behaviour is now set by *who connects to whom*, which is
what F-GAIN-1 could not show, but the real wiring contains self-sustaining
excitatory loops that the model does not contain.

**2. Calibration by return to rest.** Criterion declared before any held-out
assay was scored: activity must be gone 200-400 ms after a 400 ms sugar
stimulus. The transition is sharp: 0.6x Shiu passes, 0.7x fails. Chosen
**0.165 mV per synapse** (fitted, not measured), close to flybench's
independently reported 0.40-0.45x window. At 0.6x, sugar at 150 Hz recruits
~420-670 neurons, in the range of Shiu's 431 on FlyWire. That count was not
the calibration target.

**3. Held-out battery at 0.6x** (4 trials, 3 shuffles; readout mean Hz):

| Assay | Real | Shuffled | Published expectation | Verdict |
|---|---|---|---|---|
| sugar (LB3b/c) → MN9, 50/100/150/200 Hz | 0.1 / 1.6 / 15.9 / 30.0 | 0 | dose-dependent activation (Shiu 2024) | pass, but weak (Shiu ~90 Hz); calibration assay, not held out |
| water (LB3a) → MN9 | 0 at all rates | 0 | activates MN9 (Shiu 2024) | **fail** |
| bitter (LB1a-d) → MN9 | 0 | 0 | no activation | right answer, wrong reason: ≥50 Hz ignites ~9,400 neurons |
| sugar 100 Hz + bitter → MN9 | 1.9 → 0 | 0 | suppression | uninterpretable: baseline tiny, and suppression coincides with ignition |
| DNp01 (giant fibre) → TTMn | 0.1 / 3 / 6 / 10 | 0 | ~1:1 short-latency following | **fail**, as predicted by M v1: GF→TTMn is predominantly electrical (shakB), and M has no gap junctions. Chemical GF→TTMn is 70 synapses right, 20 left |
| DNg100 → front-leg MNs | 3-9 of 135 active, rhythmicity 0.21-0.29 | none active | 7-15 Hz rhythm (Pugliese 2025) | recruitment specific; **no rhythm** (Poisson floor of the metric is 0.21) |

MN9 responses are strongly left/right asymmetric (e.g. 25 vs 0 Hz) under
bilateral stimulation; unexplained.

**4. The ignition core.** In the bitter-evoked state (KCs, the whole EPG/PEN/
Delta7 ring, APL at ~750 Hz), silencing all 4,064 KCs or the 434-cell CX ring
barely changes it (9,325 → 8,382 / 8,696 active). Silencing **30 lLN1_bc**
antennal-lobe local neurons collapses it to 827. These are predicted
cholinergic (type confidence 0.75) and make 86,864 synapses onto each other,
40% of their output: a self-exciting clique. Removing KC→KC edges (21.5% of
KC output, likely axo-axonic) did not stop ignition either.

Sensitivity only, **not adopted**: making lLN1_bc inhibitory removes the
bitter storm at 0.6x (9,263 → 831) but 554 neurons still self-sustain, and at
1.0x ignition persists. There are several such loops; lLN1_bc is the most
excitable. Their transmitter is genuinely uncertain (Schlegel 2021 calls
lineage-based assignment "far from definitive").

**What this means.** The model's failure is now specific: excitatory
recurrent cliques with nothing to stop them. The animal limits these with
mechanisms M v1 omits: spike-frequency adaptation, synaptic depression,
graded transmission (APL is non-spiking in the animal) and electrical coupling.
The next discriminating experiment is adaptation, applied uniformly and
declared before scoring, then the same held-out battery at the scale re-set by
the same return-to-rest rule. If adaptation lets the gain rise without
ignition, and water→MN9 and bitter suppression appear, the omission was the
cause. Reproducible probes: `scripts/probes/`.

## F-SFA-1. Uniform adaptation does not stop ignition

Pre-registered in DECISIONS.md: every neuron adds 2 mV per spike to an
adaptation variable decaying over 200 ms (flybench's values, borrowed). The
return-to-rest scale rose one grid step (0.6x → 0.7x); at 0.8x one of four
calibration trials still self-sustained. At 0.7x: sugar→MN9 weaker (6 Hz at
200 Hz), water→MN9 still 0, bitter still ignites ~9,000 neurons and now drives
MN9 at 5.6 Hz. **Failed its criteria; not adopted.** Adaptation does act
(`scripts/probes/sfa_check.py`: persisting cells 11,716 → 39 in one trial),
but near the tipping point outcomes vary between trials.

## F-SENS-1. Sensory neurons were being fired from inside the brain

Tracing recruitment during bitter ignition (`scripts/probes/ignition_route.py`)
showed other *sensory* neurons (pharyngeal PhG13/14/16, LB1e, LgAG3) firing
within 20 ms, driven by central synapses onto their axon terminals. The
ignition hub lLN1_bc is only reached at 75 ms. Sensory spikes start in the
periphery; central input onto sensory terminals is presynaptic modulation. A
single compartment cannot represent that, so it wrongly made the terminal
fire. Dropping these edges (17,896 neurons, 1.4% of synapses;
`connection_class:onto_sensory_terminals|included = 0`) removes bitter-evoked
ignition at 0.6x (9,325 active → 167, none persisting) and leaves sugar→MN9
unchanged. It does not stop ignition at 1.0x, where central loops suffice.
Return-to-rest scale unchanged at 0.6x.

Pre-registered fresh held-out assays, 100 Hz, 3 trials, 2 shuffles
(`runs/assay-*-shiu2024-sens06`):

| Assay | Criterion | Real | Shuffled | |
|---|---|---|---|---|
| JO-C/E → aDN (DNg62, DNge078) | > 5 Hz | 136.8 | 0 | pass |
| JO-F → aDN | > 5 Hz | 0 | 0 | fail |
| JO-F → MDN | > 5 Hz | 0 | 0 | fail |
| JO-C/E → MDN (null) | < 2 Hz | 58.6 | 0 | fail |
| LPLC2 → DNp01 | > 5 Hz | 282.7 | 0 | pass (saturated) |

**2 of 5.** All positive responses are wiring-specific. The JO-C/E → MDN
failure was flagged in advance by flybench: in male-cns the JO-C/E → pIP1
route is ~3x stronger than in FlyWire. So this is either a real
specimen/sex difference or evidence against uniform efficacy. It is the
sharpest discriminating question the battery has produced. JO-F reaches ~600
neurons but neither readout; only 78 JO-F neurons exist in this graph.

Seen assays under the change: bitter ignites only at 200 Hz (was ≥ 50);
sugar 100 Hz + bitter 50 Hz drives MN9 2.0 → 0 Hz (right direction, tiny
baseline); water→MN9 still 0; GF→TTMn and DNg100 unchanged.

Adopted as profile `m1` = Shiu 2024 values + 0.165 mV + no input onto sensory
terminals. Every element is recorded `assumed`.

**Addendum after independent review.** The five fresh assays run on the
pre-change model (input onto sensory terminals kept, same 0.165 mV) give the
same outcomes: JO-C/E→aDN 139 Hz, JO-F→aDN 0, JO-F→MDN 0, JO-C/E→MDN 56 Hz,
LPLC2→GF 296 Hz (`runs/assay-*-shiu2024-presens06`). **So F-SENS-1 did not
change any held-out result.** Its only measured benefit, removing
bitter-evoked ignition at moderate rates, is on an assay seen before the
change. It was adopted without a pre-registered adoption rule. It also
removes real presynaptic inhibition at sensory terminals. Keep it as an
option, not as settled. The shuffled columns in this finding were computed
with the rewired-efficacy bug (DECISIONS, "Independent review") and are
superseded by the fixed-code runs.

## F-SIZE-1. Volume-scaled input resistance: rejected by its pre-registration

Efficacy x (median size / postsynaptic size), alpha = 1 (Pugliese-style, but
efficacy-only; see DECISIONS). Return-to-rest calibration: alpha = 1 at 2.0x
Shiu (0.55 mV), alpha = 0.5 at 1.0x. At the calibrated scales sugar→MN9 is
0 Hz and fewer than 100 neurons respond, and one grid step higher the network
ignites. The factor spans 0.002x (giant fibre) to 2,896x. The reviewer found
that 1,472 of the 1,580 non-sensory cells with factor > 3 are optic-lobe
columnar types (L4, L5, Dm2, T5, Tm9), so scaling moves the ignition core into
the optic lobe rather than taming it.

Pre-registered criteria:
- (a) More flybench passes than m1 on the unseen task set: **4 vs 1 of 15**
  (crosstalk, looming DN ensemble, flash ≠ loom, wiring robustness), graded
  0.69 vs 0.65. On the three male-CNS-only tasks m1 is better (song chain
  0.88 vs 0.25).
- (b) Keep JO-C/E→aDN and LPLC2→GF: **lost both** (0 Hz each at 100 and
  200 Hz; `runs/assay-*-m1-size1g2`).

**Not adopted.** Its flybench advantage comes from tasks that reward
quiescence, which a model that barely transmits passes by default.

## F-FB-1. m1 on flybench: 1 of 18 unseen tasks, graded 0.65

flybench v0.2.1's reference LIF, on our export of male-cns (fingerprint does
not match flybench's pin; unpinned), with m1's graph changes applied
(`scripts/flybench_variants.py`), gain 0.6 (`runs/flybench/` on backhouse).
Pass: flash ≠ loom. Near-misses: LC→DN matrix 0.94 (LPLC1 also reaches
MDN), courtship song chain 0.88 (pIP10 also drives leg MNs), DA1 sparseness
0.78, crosstalk 0.75 (loom reaches MN9). Worst: EPG ring attractor 0.29 (no
held bump), steering DNa02/DNa01 0.17, leg MN size principle 0.33, optic
flow 0.67. flybench's simulator has no synaptic reset on spike, so it runs
hotter than ours at equal gain. Its per-task numbers are an independent
implementation's, which is a useful cross-check on ours.

## F-TYPE-1. The pathway results are carried by type-level wiring

Fixed code (DECISIONS, "Independent review"), m1 recalibrated by
return-to-rest: 0.7x → **0.1925 mV** (was 0.6x; the delay fix and held kicks
shifted it). Battery at that scale on backhouse, 3 trials, 2 global shuffles,
2 cell-type block-preserving shuffles (`runs/assay-*-m1-fixA`). Readout
excludes MN9_R (F-DATA-3). Stimulus 100 Hz (200 Hz in brackets):

| Assay | Real | Type-shuffled | Globally shuffled |
|---|---|---|---|
| JO-C/E → aDN | 126 (138) | 104 (135) | 0 (0) |
| LPLC2 → DNp01 | 310 (354) | 304 (353) | 5 (11) |
| DNp01 → TTMn | 7.3 (21) | 7.4 (21) | 0 (0) |
| JO-C/E → MDN (null) | 7.5 (3.8) | 7.9 (4.9) | 0.2 (2.0) |
| **sugar → MN9_L** | **63 (131)** | **16.5 (54)** | 0 (0) |
| water → MN9_L, JO-F → aDN/MDN | 0 | 0 | 0 |
| bitter, sugar+bitter, DNg100 | ignite ~8-11k | ignite ~7-11k | ≤ 800 active |

Calibration agrees: the type-shuffled graph returns to rest up to 0.6x and
ignites at 0.65-0.7x, like the real graph. The global shuffle stays quiet to
1.3x.

**Conclusion.** Rewiring individual neurons within their types leaves almost
every result intact, including the ignition and the failures. So these
assays test **type-level connectivity**, not the scanned individual's
neuron-level wiring. Sugar→MN9 is the exception: real wiring drives MN9_L
2.4-3.8x harder than its type-shuffled versions, so it carries some
neuron-level information. "The anatomy is load-bearing" (F-GAIN-2) should
read "type-level wiring is load-bearing; neuron-level identity mostly is
not yet probed". Also, at the recalibrated 0.7x most non-sugar stimuli
ignite: the sugar-only calibration does not guarantee stability for other
inputs. DNg100: the ISI-surrogate rhythm excess is 0.00-0.01 everywhere,
so there is no rhythm.

## F-STD-1. Uniform short-term depression trades transmission for stability

Pre-registered (DECISIONS): U = 0.5, tau_rec = 500 ms per presynaptic neuron.
Return-to-rest now holds up to 1.6x (0.44 mV; without STD, 0.7x). At that
scale (`runs/assay-*-m1-std16`, 2 trials, 1 shuffle): water→MN9_L 4.5 Hz
(first non-zero, still below 5), JO-F→aDN 4.1 Hz at 200 Hz (below 5),
sugar→MN9_L 2.0 Hz and JO-C/E→aDN 4.3 Hz (**both passes lost**),
LPLC2→GF 82 Hz, JO-C/E→MDN 4.4 Hz (null still fails). Broad transient
recruitment of 5,000-13,000 neurons. **Criteria not met; not adopted.**
Sustained 150 Hz sensory input depletes the sensory synapses themselves
(steady-state x ≈ 1/(1 + U·r·tau) ≈ 0.03), so depression silences exactly
the feedforward drive it was meant to spare. A depression confined to
recurrent central synapses, or a weaker U, would be a different, new
hypothesis.

## F-LN-1. The ignition core is the antennal lobe's excitatory LNs

Screen at m1, 0.1925 mV (`scripts/probes/ignition_core_screen.py`,
`runs/probes/ignition_core_screen.csv`): bitter GRNs at 100 Hz leave 9,885
cells firing 200-400 ms after the stimulus. Silencing each of the 28 most
common persisting types one at a time: **only lLN1_bc matters** (30 cells;
9,885 → 121). Every other type, including all KC classes, EPG, PEN,
Delta7 and PAM, changes it by < 5%.

lLN1_bc's transmitter is **measured, not only predicted**. FlyWire v783
annotations give `known_nt = acetylcholine` from immunostaining (Shang et
al. 2007), so the +1 sign is right. They are the excitatory LNs (eLNs).
Their physiology is also measured: eLN→PN transmission is unaffected by
blocking chemical transmission and abolished by a shakB gap-junction mutation
(Yaksi & Wilson 2010, Neuron 67:1034). Their lateral excitation of PNs is
**electrical**, and eLNs also drive inhibitory LNs. The connectome shows
86,864 eLN→eLN chemical synapses (40% of their output). Whether those act
as excitation is not measured.

So the model's runaway comes from converting a measured-electrical,
possibly weak chemical output into strong chemical excitation. It is not a
sign error. Next discriminating experiment, to pre-register:
- (a) eLN→PN chemical efficacy 0, as measured, with eLN-PN gap junctions
  added (conductance unknown, assumed) so lateral excitation is kept;
- (b) eLN→eLN treated as the same unknown, tested both ways.

Score (a) on whether ignition disappears under calibration rule v2 and
whether the stable scale then rises high enough for water→MN9 and JO-F→aDN.

Diagnostic (`scripts/probes/eln_outputs.py`): zeroing eLN→PN (34.5% of
eLN output) and eLN→eLN (40.6%) together does not stop ignition (9,885 →
6,923 persisting). Silencing all eLN output does (→ 121). The remaining 25%,
mostly onto other AL LN types, is enough to sustain it. So hypothesis (a)
alone will not fix it; the loop runs through eLN→LN→… partners. The next
step is to trace that loop. Also, at 0.1925 mV sugar at 150 Hz ignites on
this seed: 0.7x sits on the edge.

## F-LN-2. Odour input ignites the model at every usable scale

Calibration rule v2 (sugar plus 4 random 40-cell sensory populations outside
every assay) **fails at every scale tested**, for both m1 (from 0.3x, i.e.
0.083 mV) and the conductance-based variant (from 0.4x). Sugar alone returns
to rest up to 0.7x (current-based) and 0.8x (conductance). The failing
populations are the ones containing ORNs. A single glomerulus (ORN_DM4, 32
cells, 150 Hz for 400 ms) leaves ~2,240 cells firing 200-400 ms after the
stimulus at 0.083 mV, and ~8,000 at 0.165 mV. It also drives MN9_L to
120-145 Hz through the ignited state.

Probes (`scripts/probes/orn_*.py`, `aln_*.py`, `runs/probes/*.csv`):
- Silencing all 131 cholinergic AL local neurons (30 types; lLN1_bc
  immuno-confirmed cholinergic, the rest predicted) abolishes odour ignition at
  0.083 mV and cuts it to 1,342 cells at 0.1925 mV.
- Removing only their chemical output onto PNs and onto each other (70% of
  their output, per the measured electrical eLN→PN coupling; Yaksi & Wilson
  2010) raises the ignition-free ceiling from < 0.05 to ~0.08-0.1 mV of m1's
  scale. sugar→MN9 needs ~0.165 mV, so a ~2x gap remains.
- Restoring central input onto ORN terminals (presynaptic inhibition,
  Olsen & Wilson 2008) changes nothing. As an additive current it cannot
  compete with a 69 mV kick, and the persistence outlives the ORN drive.

**This is now the blocking problem.** Under this model family, the antennal
lobe cannot be both stable to odour input and transmissive for gustatory
pathways at any single synaptic scale. The measured physiology the model gets
wrong is concentrated there: eLN→PN is electrical, LN transmitter
predictions are unreliable, and gain control is presynaptic and divisive.
Neither conductance synapses nor uniform adaptation or depression close the
gap. Also, since F-TYPE-1 found type-level wiring suffices, per-region
synaptic scales (at least AL vs rest) would not destroy what the anatomy
currently carries. That makes them a legitimate next hypothesis, provided
they are fitted to AL physiology (PN transfer function, Olsen et al. 2010;
flybench task 17) and not to behaviour.

## F-GAP-1. GF electrical synapses: the electrical link works, the chemical one after it fails

Pre-registered (DECISIONS): spike-triggered rectifying kick k = 20 mV for
GF→TTMn and GF→PSI (`src/flyemu/electrical.py`), m1 at 0.1925 mV,
`runs/assay-gf_*-m1-elec{0,20}`.
- GF→TTMn (**fitted**, not held out): 0.0/1.2/7.3 Hz → 20/45/93 Hz at
  25/50/100 Hz GF drive. It now follows ~1:1.
- GF→DLMn (held out): 0.47 Hz at 50 Hz (criterion ≥ 25) and 2.9 Hz at
  100 Hz (criterion > 5). **Fail.**

Mechanism: PSI_L follows GF_L exactly (49/49 Hz, 91/91 Hz), so the electrical
step works. The failing step is chemical: each PSI's ~225 synapses are split
across 5 DLMn (~45 each), which at uniform 0.1925 mV per synapse is
subthreshold per spike. In the animal PSI→DLMn transmits reliably, so
uniform per-synapse efficacy is wrong at this connection. Also, only 3 of 4
pairs were made: GF_R has no ≥ 5-synapse chemical contact with either PSI, so
the contact proxy for apposition fails there (GF→PSI chemical counts are
2, 3, 2 and 9). Kept as an option, default off; not validated.

## F-NORM-1. Input-count normalisation fails like size scaling, as predicted

Pre-registered (DECISIONS), with the expected failure written down first.
Efficacy x (median input count / N_j), beta = 1. Rule v1 calibration: stable
up to 4x (1.1 mV), with sugar→MN9 at 0 Hz; ignition at 6-8x. It fails the
adoption rule at calibration, so the battery was not run. Normalising by any
quantity that grows with cell size suppresses exactly the large integrating
neurons (MN9, GF, DNs, pIP1) that the known pathways end on. Rejected.

## F-AL-1. m2: two antennal-lobe corrections make the model stable and improve olfactory physiology

Pre-registered (DECISIONS, "m2"). The changes come from the ignition
diagnostics and literature only:
- (i) no chemical output from cholinergic AL LNs onto PNs or other
  cholinergic AL LNs (eLN→PN is electrical; Yaksi & Wilson 2010);
- (ii) AL LNs with unclear predicted NT treated as inhibitory.

**Calibration rule v2 is satisfiable for the first time.** Every stimulus,
including random populations containing ORNs, returns to rest up to 1.0x
m1's scale (0.165 mV). m1 failed at every scale.

**Held-out olfactory physiology** (flybench v0.2.1's own simulator, gain 0.6
= 0.165 mV, tasks never used in design; `runs/flybench/{m1n,m2n}_g06_olf.json`):

| Task (graded) | m1 | m2 |
|---|---|---|
| 08 olfactory sparse coding | 0.57 | 0.83 |
| 17 PN transfer function | 0.45 | 0.75 |
| 18 DA1 sparseness | 0.64 | **0.95 pass** |
| 26 KC sparseness / APL | 0.46 | **0.89 pass** |
| 27 CO2 specificity | 0.57 | 0.60 |
| mean | 0.54 | **0.80** |

Remaining olfactory failures: the CVA odour still reaches too many cells;
the PN response at 100 vs 30 Hz ORN drive is less than doubled (too
saturated); CO2 does not reach its own PNs (PNm1 < 5 Hz).

**The battery at 0.165 mV** (`runs/assay-*-m2-v2mac`, 2 trials, 1 global and
1 type shuffle; GF→TTMn, DNg100 and JO-F→MDN not rerun):
- No ignition anywhere. Bitter recruits 789 cells (m1: ~9,000-11,000).
- Sugar→MN9_L 7.5 / 93.5 Hz at 100 / 200 Hz (type-shuffled 1.5 / 43;
  global 0).
- **Bitter suppression is now clean:** sugar 100 Hz alone 7.5 Hz; with bitter
  0 Hz; bitter alone 0 Hz, without ignition. This is its first
  interpretable pass.
- JO-C/E→aDN 139 Hz and LPLC2→GF 296 Hz, as before; type-shuffled nearly
  identical (F-TYPE-1 holds).
- Still failing: water→MN9 0, JO-F→aDN 0, and the JO-C/E→MDN null
  (56 Hz).

**Adopted as the working model (profile `m2`).** The closed-loop body run
(`runs/organism-record-3000ms-m2`, in the viewer) stays at 0.10-0.26 Hz
whole-brain with 4,992 motor spikes in 3 s.

Caveats:
- (ii) is a class-level prior applied to 89 cells whose individual
  transmitters are unknown.
- (i) extends a measurement for eLN→PN to eLN→eLN, which is unmeasured.
- No electrical eLN-PN coupling was added to replace the removed chemical
  excitation, so lateral excitation is currently absent. That is a known
  omission and a likely cause of the saturated PN transfer function.

---

# Session 5

## F-CENSUS-1. Every sensory neuron assigned; 768 taste neurons were being driven as touch

`scripts/sensory_census.py` → `data/derived/sensory_census.csv`: all
**17,896** sensory neurons of the modelled graph, in 388 groups (cell types,
or class/subclass for untyped cells). Each group has a modality, organ,
sensed physical variable, transduction model family and parameter source.
Assignments come from male-cns annotation by a rule table (derived), from
naming or homology (inferred), or not at all (unknown).

| Modality | Cells | Driven now |
|---|---|---|
| vision | 6,091 | 6,091 (luminance only, non-retinotopic) |
| touch | 4,057 | 2,153 (leg/body bristles; head BM_* not) |
| olfaction | 2,639 | 0 |
| proprioception | 1,448 | 962 (tanh-of-angle placeholders) |
| taste | 1,423 | 0 |
| unknown | 1,220 | 0 |
| other mechanosensation (JO, TPMN, pharyngeal) | 801 | 0 |
| chemo / hygro / thermo | 126 / 66 / 25 | 0 |

Basis of the sensed-variable assignment, in cells: derived 16,266, inferred
410, unknown 1,220. Most of the unknowns are the abdominal SNxx types (~1,040)
plus about 170 cells with no class or subclass at all.

**Bug found and fixed.** `sensory.py` drove the subclass "leg bristle" as a
contact (touch) sensor. In male-cns that subclass is class *gustatory*: 768
LgLG/LgAG leg taste neurons. They are no longer driven. Leg touch comes from
"mechanosensory bristle" (2,130 cells), which is unchanged.

## F-LEDGER-1. A definite count: ~250,000 blank slots

`scripts/blank_ledger.py` → `data/derived/blank_ledger.csv`. It counts every
parameter a complete possible fly needs, at declared grains (see the script
docstring): cell type for neurons (14,356 including untyped singletons);
factorised pre/post type for synaptic strength; postsynaptic type for
glutamate sign; sensory group; motor neuron; muscle; joint.

| Subsystem | Measured | Derived | Inferred | Unknown |
|---|---|---|---|---|
| structure | 6,408,342 | 10,207 | 0 | 0 |
| neuron biophysics | 0 | 0 | 129,204 | 0 |
| synapse | 0 | 0 | 57,249 | 58,445 |
| sensory | 0 | 0 | 1,176 | 342 |
| motor | 0 | 348 | 3,405 | 467 |
| body | 0 | 173 | 206 | 0 |

**Blank slots: 250,494** (inferred 191,240, unknown 59,254). Filled by data:
6.42 million, almost all measured connectivity. The biggest blanks are
per-type biophysics (9 x 14,356), per-type release strength and input gain,
short-term plasticity, and electrical coupling (both unknown per type). This
number depends on the declared grain and is recomputed by the script. It
falls as data are attached and as justified sharing collapses slots, and the
ledger records which.

## F-VISION-2. Retinotopy derived from the connectome: every photoreceptor has an ommatidium

F-VISION-1 said retinotopy "cannot be established from these releases". It
can, from geometry. `scripts/retinotopy.py` → `data/derived/retinotopy.csv`,
6,026 photoreceptors:
- terminal presynapse centroids (neuPrint);
- volume axes derived from landmarks: anterior = -z (antennal lobe vs calyx),
  dorsal = -y (dorsal-rim terminals sit 15,000 voxels dorsal in both eyes),
  fly's left = larger x (median soma x of somaSide-L cells 74,016 vs R 22,662);
- each eye's lamina and medulla sheet in its own plane, with the medulla's
  A-P flipped at the first optic chiasm (standard anatomy, inferred);
- ommatidium viewing directions from flygym's retina map and the eye camera
  poses (derived);
- a moment-matched global alignment (inferred);
- one-to-one R7→ommatidium and R8→ommatidium assignment (one of each per
  ommatidium is measured biology).

**Independent check:** within an assigned ommatidium, R7 and R8 pale/yellow
subtypes agree **0.73** of the time, against 0.52 by chance. The raw 3D
nearest-neighbour agreement is 0.77, the ceiling for this data. The first
attempt (volume-axis projection, many-to-one) scored 0.54, no better than
chance, and was replaced. Dorsal-rim cells land at +62° elevation. Median
mismatch to the assigned ommatidium: ~9° in the medulla, ~4° in the lamina.
The alignment has no local distortion model, which is the remaining inferred
step.

`vision.py` now drives each photoreceptor from its own ommatidium's
luminance, so the eyes carry spatial information. The registry records
retinotopy as **derived**, with the alignment caveat. Spectral matching is
still coarse (the renderer's pale/yellow mask is its own). The R7/R8
assignments could now set that mask from the connectome.

## F-OLF-1. Smell, CO2 and humidity wired to a world; recordings had been blind

`src/flyemu/world.py`: a minimal environment with static Gaussian odour
plumes, temperature, humidity and CO2. All scenario choices, inferred.
`src/flyemu/olfaction.py`: 2,592 ORNs are driven by concentration at their
own antenna (derived from body pose) x DoOR relative tuning (measured, 48 of
53 types) x an inferred saturating dose-response. ORN_V reads CO2 with K = 5%
(derived from qualitative dose-response). Dry and moist hygroreceptors are
tonic in RH. Temperature cells are phasic (dT/dt), so a static world leaves
them at baseline. ORN adaptation dynamics are recorded as unresolved. The
absolute scale (max drive 15 mV, K = 10^-3) is inferred.

Closed-loop check (m2, 300 ms; `scripts/probes/odour_closed_loop.py`):
ethyl acetate (10^-2 at the antenna) raises active PNs from 20 to 36 and PN
mean rate from 0.46 to 1.28 Hz. Whole-brain rate goes 0.95 → 1.00 Hz; no
ignition. KCs are not recruited in 300 ms.

**Bug fixed:** `record_organism.py` had its own copy of the loop that never
added visual drive, so every viewer recording so far was of a blind fly.
Sensing now goes through one method, `Organism.sense()`, used by both.

Census: 11,903 of 17,896 sensory neurons driven (66%). Before this session it
was ~9,300, of which 768 were wrong.

## F-LEDGER-2. The complete blank ontology: 79 measurable quantities, 824,230 parameter slots

`data/ontology/fly_information.yaml` lists everything about a fly that could
in principle be measured, across 16 domains: connectome, neuron, synapse,
neuromodulation, neuroendocrine, internal state, glia, molecular,
metabolism, sensory, motor, muscle, body, other organs, environment. Each
entry has its grain, how to measure it, whether the model simulates it (with
evidence), runs it on a default, or omits it, and its basis label.
Estimated instance counts are labelled with their source.
`scripts/blank_ledger.py` counts:

| Scale | Slots | Filled (measured/derived) | Blank, on a default | Blank, mechanism absent |
|---|---|---|---|---|
| parameters | 824,230 | 548 | 306,761 | 501,334 |
| per-element structural data | 366.5 M | 96.9 M | 0 | 269.6 M |

The per-element blanks are mostly synapse ultrastructure (unknown, 3 per
synapse) and synapse locations. The locations are measured but unused by
point neurons. **Of the parameter blanks, 61% have no default because the
mechanism is not simulated.** The largest absent mechanisms: ion-channel
complement (172k), per-target receptor subtypes (57k), dendritic
integration, short-term plasticity (43k), electrical coupling (29k per-type
partners plus 29k conductances), neuromodulation (59k), and co-transmitters
(14k). That is the work list for "everything simulated, even if guessed".

The labelling itself was made strict (DECISIONS, session 5):
measured / derived / inferred / guessed / unknown / absent, with required
fields enforced by `Registry.validate()` and tested on the whole organism.
