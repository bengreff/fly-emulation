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
