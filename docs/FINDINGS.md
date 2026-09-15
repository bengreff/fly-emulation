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
