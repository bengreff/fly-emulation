# Findings

Measured results with their conditions and limits. Every entry is reproducible
from a provenance record in `runs/`. Entries are appended in the order they were
established, so corrections sit after the claims they overturn. Read the index.

| # | Claim | Status |
|---|---|---|
| F1 | The external frequency metric returns cycles per sample, not hertz | stands |
| F2 | All 144 motor neurons join to muscle targets; tibia flexor pool is 15/side, matching independent electrophysiology | stands |
| F3 | The ~10 Hz rhythm reproduces, but peak motor output is ~13x below a measured resting rate | stands |
| F4 | The specific wiring, not its degree structure, keeps the network sparse and rhythmic | stands, with a caveat on the null |
| F5 | The full front-leg sensory apparatus is present and entirely undriven; no rate calibration exists for it | stands |
| F6 | The best available body model can receive 68% of front-leg motor output and cannot resolve motor units | stands |
| F7 | Rhythm and motor recruitment trade off across every manipulation tried | stands |
| F8 | "Any added excitation breaks the rhythm, not the sensory pathway" | **retracted** — one replicate, one amplitude |
| F8a | "The proprioceptive pathway is privileged" | **superseded by F8b** — confounded by cell size |
| F8b | The apparent pathway specificity is an artefact of size-scaled excitability; the same current makes proprioceptors emit 18x more output | stands, with the matching definition stated |
| F9 | 40.8% of the model's inhibition rests on treating glutamate as inhibitory, which is a receptor property the connectome does not contain | stands |
| F10 | The model assigns an inhibitory sign to most of the fly's main leg proprioceptor, against published physiology | stands |
| F11 | Excitability is derived from a volume that measures a whole cell for some classes and only an axon arbor for others | stands |
| F12 | Rhythmic sensory drive does not rescue the rhythm at any frequency, and the motor output does not even entrain to it | stands, open loop only |
| F13 | Respecting the transmitter classifier's own uncertainty destroys the rhythm in a third of draws; every draw that flipped one of four core neurons lost it | stands |
| F14 | The whole-CNS male connectome is the better primary specimen: 94% traced against 23%, the brain included, 1454 proprioceptors, and a 95% motor-neuron cross-reference back to MANC | stands |
| F15 | Across all 303 simulations of the session, none produced both a rhythm and physiological motor rates; correcting excitability moves the operating point but keeps the same two regimes | stands, for this model class |

## F1. Units bug in the external oscillation-frequency metric (2026-09-14)

`src/utils/sim_utils.neuron_oscillation_score` in the Pugliese repository builds
its reference time axis as `jnp.arange(n_samples)`. Its returned "frequency" is
therefore **cycles per sample, not Hz**. With the default `dt = 1 ms` the reported
value must be multiplied by 1000 to obtain Hz.

Detected because a reproduced rhythm was reported as 0.01 "Hz" while the traces
visibly oscillated about ten times per second. Confirmed against two independent
estimators computed on the saved traces over 0.5-1.9 s:

| Estimator | Frequency |
|---|---|
| Library value x sampling rate | 9.47 Hz |
| Periodogram peak | 11.43 Hz |
| Threshold-crossing count | 10.7-11.4 Hz |

`scripts/pugliese_conditions.py` now converts to Hz and reports an independent
periodogram estimate alongside, as a permanent cross-check. The residual 5-15%
disagreement between estimators is genuine estimator disagreement on a short
window, not a units error, and is carried as uncertainty.

**Consequence:** any frequency quoted from this library elsewhere needs the same
check. This is the class of error `docs/VALIDATION.md` requires unit tests for.

## F2. Anatomical identity join, Pugliese T1 network to MANC muscle targets (2026-09-14)

Joined the 144 motor neurons of the bundled Pugliese T1 network to MANC v1.2.1
motor-neuron annotations on `bodyId`, queried live from neuPrint.

| Check | Result |
|---|---|
| Motor neurons in bundled T1 table | 144 |
| MANC front-leg (`subclass = fl`) motor neurons | 144 |
| Joined on exact integer `bodyId` | 144 / 144 |
| Distinct target muscles | 20 |
| All `status` | Traced |
| Left/right symmetry | near-exact (see below) |

The front-leg pool is left/right symmetric for every muscle except tarsus levator
(2 left, 3 right), which is a tracing or annotation asymmetry to keep flagged
rather than silently average.

**Independent corroboration.** The tibia flexor pool (`Ti flexor` +
`Acc. ti flexor`) contains exactly **15 motor neurons per side**. Azevedo et al.
2020 (eLife 56754), an electrophysiology study that did not use this connectome,
state that tibia flexion is controlled by "approximately 15 motor neurons". Two
independent methods agree on the size of this pool. Soma size within the left
pool spans **13.1x**, consistent with the size principle that paper reports.

This join is the anatomical bridge required for Milestone A and it passes.

## F3. The connectome VNC rhythm reproduces, but its motor output is far below physiological (2026-09-14)

Reproduction of the Pugliese descending-neuron stimulation experiment. Left
DNg100 driven with a tonic 250 current step from 0.02 to 1.999 s, 4604-neuron
MANC T1 network, 16 independent biophysical parameter draws, solver tolerances
`rtol = 2e-6`, `atol = 5e-9` as in the paper. Mac M2 Pro, CPU, 276 s.

| Readout | Value (mean +/- sd over 16 draws) |
|---|---|
| Motor-neuron oscillation score | 0.836 +/- 0.119 |
| Motor-neuron rhythm frequency | 10.04 Hz (periodogram 10.58 Hz) |
| Active motor neurons | 2.6 of 144 |
| Motor-neuron peak rate, median | 2.25 Hz |
| Motor-neuron peak rate, maximum | 6.52 Hz |

**The rhythm reproduces and is robust.** A strongly rhythmic motor output near
10 Hz appears across every parameter draw. That is the paper's qualitative claim
and it survives independent reimplementation of the analysis.

**The amplitude does not reach physiological range.** Azevedo et al. 2020 report
that the slow tibia-flexor motor neuron sits at approximately **30 Hz at rest**,
before any movement, and that force per spike is <0.1 uN for slow units, ~1 uN
for intermediate and ~10 uN for fast units, the last roughly one fly body weight.

> **Provenance of the 30 Hz reference.** This is the paper's description of the
> slow neuron's resting rate, quoted from its Figure 3D, not a population mean
> with a dispersion. It is used here as an order-of-magnitude reference for what
> a real leg motor neuron does when the animal is doing nothing, which is the
> comparison the model fails by a factor of thirteen. It should not be treated
> as a fitting target or a tolerance. The fast and intermediate units, which
> produce the force that moves a leg, are reported as silent at rest, so there
> is no resting-rate reference for them at all.
The model's *peak* motor-neuron rate, 2.25 Hz median, is about **13x below the
resting rate of a real slow motor neuron**, and the fast and intermediate units
that generate usable force never approach their recruitment thresholds.

**Interpretation, with its limits.** This is not evidence that the model is
wrong. It is evidence about what the model is: a deafferented preparation. The
network contains 283 sensory neurons that receive zero input, because there is no
body, no leg, and no proprioceptive feedback. Real motor-neuron firing rates are
sustained substantially by that missing input. The finding therefore sets a
concrete quantitative target for Milestone A rather than a defect to patch:
closing the sensory loop must raise motor-neuron rates by roughly an order of
magnitude, and if it does not, the synaptic scaling assumption is implicated.

**What this result cannot claim.** Rhythmic motor-neuron activity under imposed
tonic descending drive is not walking, not stepping, and not spontaneous
behavior. It reproduces an optogenetic stimulation experiment.

## F4. The specific connectome, not its degree structure, holds the network in a rhythmic low-activity regime (2026-09-14)

Control demanded by `docs/VALIDATION.md`: compare the anatomical wiring against a
carefully matched alternative rather than a crippled one. The external
`full_shuffle` permutes postsynaptic targets **within** transmitter and class
groups, so every presynaptic neuron keeps its exact out-degree and weight
multiset and the excitatory/inhibitory composition of each class is preserved.
Only the identity of the postsynaptic partner changes.

Identical stimulus, 16 parameter draws each, paper tolerances:

| Readout | Real connectome | Degree-matched shuffle |
|---|---|---|
| Active neurons | 97 | 1760-2029 |
| Active motor neurons (of 144) | 2.6 | 77-101 |
| Motor-neuron rhythmicity | 0.836 +/- 0.119 | 0.03-0.28 |
| Rhythm frequency | 10.0 Hz | 1.2-2.5 Hz |

Shuffling produces a network that is simultaneously **hyperactive and
arrhythmic**: roughly twenty times more neurons active and the rhythm largely
destroyed. The specific pattern of connections, not merely how many connections
each cell has or the balance of transmitters, is what keeps this circuit sparse
and oscillating. This is the strongest evidence in this session that the
anatomy is carrying real functional information.

Caveat: this shuffle preserves out-degree exactly but reassigns in-degree
patterns across cells of a class, so it is not a perfect degree-preserving null.
A stricter null that preserves both in- and out-degree should be run before this
is quoted as a headline number.

## F5. The network contains the full front-leg sensory apparatus and drives none of it (2026-09-14)

The 4604-neuron T1 network includes 285 sensory neurons:

| Sensory class | Count | What it measures |
|---|---|---|
| Mechanosensory bristle | 146 | cuticle touch |
| Hair plate | 61 | joint angle at limb joints |
| Chordotonal organ | 36 | tibia position, movement, vibration |
| Campaniform sensilla | 5 | cuticular load and strain |

All four classes that report leg state are present, and **every one of them
receives zero input** in the published stimulation protocol. 102 of these are
proprioceptors, the afferents whose firing during stepping is the main sensory
drive to leg motor circuits in insects. The model as published is a deafferented
preparation with its sensory periphery intact but silent.

**A data gap found while trying to drive them.** Mamiya, Gurung and Tuthill
(PMC6481666) characterise these afferents with calcium imaging and report which
subgroup encodes position, direction and vibration, along with joint-angle
ranges (roughly 18 to 180 degrees) and vibration tuning. They report no spike
rates. `docs/ARCHITECTURE.md` already warns that a calcium trace is not a spike
train. There is therefore **no published firing-rate calibration** with which to
drive these neurons. Any sensory input amplitude used here is a swept unknown,
not a measurement, and is declared as a scaffold in every run record.

## F6. The best available fly body can receive only two thirds of the connectome's front-leg motor output (2026-09-14)

Verified against `flygym` 2.1.0, which now bundles NeuroMechFly, the Turaga-lab
flybody, and a musculoskeletal model, with MuJoCo Warp GPU support. This
supersedes the roadmap's open question about which body platform to adopt: one
package now carries the walking body, the flight body and muscles.

The musculoskeletal model exposes **15 tendon actuators on the left front leg
only**, with the right leg's joints locked, that is, a tethered single-leg
preparation. This independently confirms the caveat recorded in
`docs/RESEARCH.md` against the current release.

Mapping the 72 left front-leg motor neurons in MANC onto those actuators:

| | Motor neurons |
|---|---|
| Have a corresponding actuator | 49 of 72 (68%) |
| Have no actuator at all | 23 of 72 (32%) |
| Mean motor neurons per actuator | 3.3 |

Entirely absent from the body model: the **femur reductor** (6 motor neurons),
**all tarsus muscles** (7 motor neurons, so no active foot control), and the
**long tendon muscles** (9 motor neurons). Additionally the tibia flexor and
accessory tibia flexor, the 15-motor-neuron pool whose slow-to-fast gradient
Azevedo et al. measured, **collapse onto a single actuator**, so the size
principle that governs force recruitment cannot be expressed at all.

**Consequence for Milestone A.** Closing the leg loop is not a matter of wiring
existing components together. A third of the front-leg motor output has nowhere
to go, and the one muscle group with good published physiology cannot resolve
its own motor units in the available body. Extending the muscle model is
prerequisite work, and the tibia flexor is the right place to start because it
is the only pool with measured per-unit forces.

## F7. Rhythm and motor recruitment trade off against each other, across four independent manipulations (2026-09-14)

The central result of this session. Four unrelated ways of pushing the model
toward physiological firing rates all cost the rhythm, and the published
parameter setting sits at the rhythmic extreme with almost no motor output.

**Manipulation 1: global synaptic scale.** Both excitatory and inhibitory
multipliers scaled together, 8 draws per point, paper tolerances.

| Synaptic scale | Active neurons | Active motor neurons | Rhythmicity | Frequency |
|---|---|---|---|---|
| 0.010 | 2 | 0 | 0.000 | silent |
| 0.015 | 12 | 0 | 0.000 | silent |
| 0.020 | 23 | 0 | 0.000 | silent |
| **0.030 (published)** | 93 | 3.3 | **0.807** | 10.4 Hz |
| 0.045 | 176 | 8.0 | 0.563 | 10.1 Hz |
| 0.090 | 1740 | 83 | 0.153 | 0.77 Hz |

Rhythmicity peaks at the published value and decays monotonically as motor
recruitment rises. Points at 0.13, 0.2 and 0.3 were abandoned, see
`docs/DECISIONS.md`.

**Manipulation 2: tonic proprioceptive drive.** Driving the 102 leg
proprioceptors that the published protocol leaves silent lifts median peak
motor-neuron rate from 2.3 Hz to 82.6 Hz, above the measured 30 Hz resting rate
of a slow tibia flexor unit, and raises active motor neurons from 3 to 67. The
rhythm falls from 0.836 to 0.281 and its frequency from 10.0 Hz to 4.1 Hz.

> **Read the amplitude with F11 in hand.** Proprioceptors are small cells, so the
> model's size-derived threshold makes a nominal current of 5 into a
> proprioceptor roughly as potent as a much larger current elsewhere: the driven
> cells reach 14.4 Hz where random interneurons reach 0.79 Hz on the same input
> (F8b). The direction of this manipulation is real, and its *nominal* amplitude
> badly understates how hard the population is being pushed. Nothing here says
> what a physiologically realistic afferent drive would be, because no rate
> calibration exists (F5).

**Manipulation 3: a different descending neuron.** Stimulating DNa02, a turning
command neuron, instead of DNg100 gives 8 active motor neurons with peak rates
to 44.8 Hz, above the physiological reference, and **no rhythm at all**
(0.004 +/- 0.008).

**Manipulation 4: destroying the wiring.** The degree-matched shuffle gives 83.5
active motor neurons at peak rates to 224 Hz with rhythmicity 0.139 (F4).

Plotted together, every route to physiological firing rates lands in the
arrhythmic regime, and the only strongly rhythmic condition produces motor
output roughly an order of magnitude too weak to drive a muscle.

### What this does and does not license

It is **not** a claim that the fly cannot do both, nor that this model is
refuted. It is a measured property of this model class, a deafferented
connectome network driven by a constant current with one global synaptic scale,
and it is a sharp constraint on what has to change next.

Three candidate explanations, in the order I would test them:

1. **Sensory feedback is not tonic.** Real proprioceptors are modulated by the
   leg's own movement. Uniform tonic drive is the worst possible caricature of
   that input. The phasic-versus-tonic experiment, matched for mean amplitude,
   tests this directly and is the cheapest discriminator available without a body.
2. **One global synaptic scale is too crude.** Weight equal to synapse count
   times a single multiplier is the field's standard starting assumption, not a
   measurement. Cell-type-specific gains fitted against physiology are the next
   step if explanation 1 fails.
3. **The network has no background activity.** With no stimulus the model is
   *exactly* silent, all 4604 neurons at zero. Real nervous systems are not.
   Whatever supplies that baseline in the animal is absent here, and it is
   plausibly part of what sets resting motor-neuron rates.

The discriminating experiment is Milestone A4: body-generated, phase-locked
proprioceptive feedback. This session can only approximate it open loop.

## F8. CORRECTED BELOW — see F8a. The rhythm is fragile to added excitation from any source, not to sensory input specifically (2026-09-14)

> **This finding was wrong and is superseded by F8a.** It was written from a
> single replicate at one amplitude. The replicated eight-draw run at a lower
> amplitude shows the opposite: the proprioceptive pathway is specifically
> potent, and matched drive into random interneurons leaves the rhythm intact.
> The original text is kept below so the error is visible rather than quietly
> edited away.

F7 showed that switching the silent proprioceptors on destroys the rhythm. The
obvious reading is that the model is deafferented and sensory feedback is the
missing ingredient. That reading is wrong, and the control that shows it is
cheap.

Driving **102 randomly chosen intrinsic neurons** with the same per-neuron
amplitude, rather than the 102 proprioceptors, collapses the rhythm just as
thoroughly:

| Drive target, amplitude 12.5 | Rhythmicity | Active motor neurons | Median peak rate |
|---|---|---|---|
| Nothing (baseline) | 0.836 | 2.6 | 2.3 Hz |
| 102 proprioceptors | 0.041 | 68.9 | 81.4 Hz |
| 102 random intrinsic neurons | 0.092 | 54.0 | 64.7 Hz |

So it is not the sensory pathway. It is **total added excitation**, wherever it
enters. The rhythmic state exists only in a narrow low-activity regime and is
destroyed by roughly any additional drive.

Both framings of the amplitude should be stated, because they sound different:
per neuron, 12.5 is 5% of the 250 injected into the descending neuron; summed
over 102 afferents it is 1275, which is **5.1 times** the total descending
drive. The honest summary is that the rhythm requires the proprioceptors to be
close to silent, and nobody knows whether real afferent drive sits above or
below that threshold, because the rate calibration does not exist (F5).

## F9. Forty-one percent of the model's inhibition rests on an assumption the connectome cannot settle (2026-09-14)

Composition of the 4604-neuron network, from the bundled annotation table:

| Predicted transmitter | Neurons | Outgoing synapses | Sign in the model |
|---|---|---|---|
| Acetylcholine | 2419 | 2,015,846 | excitatory |
| GABA | 1077 | 1,067,547 | inhibitory |
| Glutamate | 1095 | 734,379 | inhibitory |

Glutamatergic cells are **23.8%** of the network and supply **40.8%** of its
inhibitory synapse budget. Excitation and inhibition are very nearly balanced:
the ratio of excitatory to inhibitory synapses onto motor neurons is **1.02**.

Treating glutamate as inhibitory is a modelling convention, not a measurement of
these cells. In *Drosophila*, glutamate is inhibitory where the glutamate-gated
chloride channel GluCl is expressed postsynaptically, which was demonstrated in
the olfactory system, and excitatory where it is not. **The sign is a property
of the postsynaptic receptor, not of the transmitter**, and the connectome does
not contain receptor identity. `docs/ARCHITECTURE.md` states this requirement;
the model in hand cannot meet it.

The result depends on the assumption almost completely. Sweeping the glutamate
multiplier from fully inhibitory through silent to excitatory, eight draws per
point at paper tolerances except where noted:

| Glutamate multiplier | Meaning | Rhythmicity | Active motor neurons | Median peak rate |
|---|---|---|---|---|
| 0.03 | inhibitory, as published | 0.828 +/- 0.138 | 3.0 | 2.0 Hz |
| 0.02 | weaker inhibition | 0.829 +/- 0.175 | 2.8 | 2.9 Hz |
| 0.01 | weaker still | 0.764 +/- 0.152 | 3.1 | 3.2 Hz |
| 0.00 | silenced | **0.323 +/- 0.354** | 54.5 | 37.8 Hz |
| -0.03 | excitatory (single draw) | **0.003** | 137 of 144 | 198.6 Hz |

The rhythm tolerates glutamate inhibition being weakened by two thirds, then
falls apart once those cells stop inhibiting. With the sign reversed the network
runs away and nearly every motor neuron saturates. Points at -0.01 and -0.03
were abandoned at eight draws for capacity; the -0.03 row is a single draw.

With the sign flipped the network runs away: nearly every motor neuron saturates
and the rhythm is gone. Given that the network sits at E:I balance of 1.02, this
is not surprising, and that is the point. A load-bearing assumption sits under
the headline result, and it is an assumption about receptors that has not been
measured for these cells.

**The constructive next step** is to constrain it with expression data. The Fly
Cell Atlas carries adult single-cell transcriptomes; GluCl expression in VNC
motor neurons and premotor interneurons would turn a convention into a prior
with real uncertainty. That is a well-defined piece of work and it was not
attempted tonight.

## F10. The model gives the fly's main leg proprioceptor the wrong sign (2026-09-14)

Following the drive-target control led to a specific, checkable error.

The EM transmitter classifier is markedly less confident about sensory neurons
than about the rest of the network:

| Population | Mean confidence | Below 0.8 | Below 0.6 |
|---|---|---|---|
| Leg proprioceptors (102) | 0.695 | 71% | 25% |
| All sensory neurons (285) | 0.674 | 81% | 29% |
| Non-sensory (4319) | 0.826 | 30% | 11% |

And on those low-confidence calls it labels most leg afferents glutamatergic,
which this model renders as **inhibitory**:

| Subclass | n | Predicted glutamate | Mean confidence |
|---|---|---|---|
| Chordotonal organ | 36 | 69% | 0.691 |
| Hair plate | 61 | 46% | 0.705 |
| Campaniform sensilla | 5 | 80% | 0.600 |
| Mechanosensory bristle | 146 | 68% | 0.658 |

**Published physiology disagrees.** The femoral chordotonal organ, the fly's
principal leg proprioceptor, is described in the primary literature as roughly
150 **excitatory cholinergic** sensory neurons, separable into claw, hook and
club subtypes encoding tibia position, movement direction and vibration. Insect
mechanosensory afferents are cholinergic as a class.

So the model assigns an inhibitory sign to the majority of the very neurons that
should be the excitatory sensory drive into the leg motor circuit. It does so on
classifier calls whose own confidence is below 0.7.

**Consequence.** Every sensory-drive result in this session, and any future work
that switches these afferents on, runs through signs that are probably inverted
for most of the population. A `--proprio-cholinergic` override now forces them
excitatory on the published evidence, recorded as a literature-based correction
rather than a measurement of these specific cells, and the comparison is running.

A first probe at drive amplitude 12.5 shows the correction does **not** by itself
restore the rhythm (0.021 corrected against 0.041 uncorrected), so this is not
the explanation for F7. It is a separate defect, and it is the one a reader can
act on immediately.

**Note on scope.** This T1 network contains 36 chordotonal-organ neurons; the
real organ has about 150. The simulated network is a connectivity-filtered subset
of the leg's sensory apparatus, not the whole of it.

## F8a. CORRECTS F8, AND IS ITSELF SUPERSEDED BY F8b. The proprioceptive pathway is a privileged lever on this circuit (2026-09-14)

> **The dissociation reported here is real as measured but misattributed.** It is
> explained by the model's size-scaled excitability (F11), not by pathway
> privilege: proprioceptors are 0.44x the median cell size and therefore have a
> 2.1x lower spike threshold, so identical injected current is a much larger
> perturbation to them. With drive matched to each cell's own threshold the
> difference largely disappears. See F8b. Text kept as written.

Replicated at eight draws per condition, paper tolerances, drive amplitude 5 per
neuron into 102 neurons:

| Drive target | Rhythmicity | Active motor neurons | Median peak rate |
|---|---|---|---|
| Nothing (baseline) | 0.836 +/- 0.119 | 2.6 | 2.3 Hz |
| 102 leg proprioceptors | **0.095 +/- 0.070** | 76.6 | 93.4 Hz |
| 102 random intrinsic neurons | **0.830 +/- 0.124** | 3.0 | 2.0 Hz |

Driving random interneurons at this amplitude does **essentially nothing**: the
rhythm, the motor recruitment and the firing rates are all indistinguishable
from the undriven baseline. The identical drive delivered through the
proprioceptors collapses the rhythm and recruits 77 motor neurons at
physiological rates.

This is not explained by how much signal each population injects. The random
interneurons have roughly **twice** the outgoing synapse budget (90,101 against
46,691 synapses), **2.7 times** as many synapses directly onto motor neurons,
and a nearly identical excitatory fraction (45% against 44%). The proprioceptors
do more with less because of **where they project**, not how much they project.

> **Why F8 said the opposite.** F8 rested on a single replicate at amplitude
> 12.5, where both targets happen to have collapsed the rhythm. At that
> amplitude everything saturates and the dissociation is invisible. The lesson
> is the obvious one: one replicate at one operating point is not a control.

**This makes the sensory pathway more important, not less.** Combined with F10,
which shows the model inverts the sign of most of those same afferents, the
position is that the single most influential input to the leg motor circuit is
the one the model most likely gets backwards.

## F11. The model derives excitability from a volume that does not mean the same thing for every cell class (2026-09-14)

The model scales each neuron's gain and spike threshold by its soma size,
normalised to the network median: `gain = gain / size`, `threshold = threshold *
size`. Larger cells therefore need more input and respond less steeply, which is
a defensible heuristic for current injected into a larger membrane.

The `size` column is a **segmentation volume measured inside the nerve cord**.
That is not the same quantity for every class, because not every class has its
cell body there:

| Class | n | Relative size | Threshold | Gain | Where the soma actually is |
|---|---|---|---|---|---|
| Sensory neuron | 283 | 0.108 | x0.11 | **x9.24** | in the leg, only the axon arbor is in this volume |
| Descending neuron | 1318 | 0.751 | x0.75 | x1.33 | in the brain, only the axon arbor is in this volume |
| Intrinsic neuron | 2471 | 1.031 | x1.03 | x0.97 | in the nerve cord |
| Motor neuron | 144 | 1.668 | x1.67 | x0.60 | in the nerve cord |
| Ascending neuron | 375 | 2.885 | x2.89 | x0.35 | in the nerve cord |

By sensory subclass the effect is more extreme still: mechanosensory bristles
come out at 0.078 of the median, a **12.9x gain multiplier**, and chordotonal
organ neurons at 0.213, a **4.7x multiplier**.

So the two populations that carry input into this circuit, sensory afferents and
descending neurons, are exactly the two whose measured volume is an axon arbor
rather than a cell. Using it as a proxy for electrical size hands the sensory
population an order-of-magnitude excitability advantage that is an artefact of
where the electron-microscope volume was cropped.

**This is not a minor calibration issue.** It means a flat injected current is a
wildly different perturbation depending on which class you inject into, which
makes any perturbation experiment in this model class hard to interpret unless
the drive is normalised. Finding F8b is a worked example of exactly that trap.

**Fix.** Either normalise size within class, or use a quantity that means the
same thing everywhere, such as the neuron's synapse count inside the volume, or
drop the size scaling and fit gain and threshold per cell type against
physiology. All three are defensible; the current rule is not.

## F12. Rhythmic sensory drive does not rescue the rhythm at any frequency (2026-09-14)

The experiment designed to be the discriminator for F7, and it came back
negative, which is the useful kind of result.

If the rhythm dies under sensory drive because uniform tonic input is an
unrealistic caricature of what a moving leg supplies, then giving the same
*mean* drive a temporal structure should help. Holding mean amplitude fixed at 5
per neuron into the 102 proprioceptors and varying only the modulation:

| Sensory modulation | Draws | Rhythmicity | Active motor neurons | Motor output frequency |
|---|---|---|---|---|
| none (undriven baseline) | 16 | **0.836** | 2.6 | 10.0 Hz |
| tonic, same mean | 8 | 0.041 | 68.9 | 1.5 Hz |
| 2 Hz | 7 | 0.088 | 63.1 | 1.3 Hz |
| 5 Hz | 7 | 0.061 | 72.0 | 2.3 Hz |
| 8 Hz | 7 | 0.059 | 70.3 | 2.0 Hz |
| 10 Hz | 8 | 0.050 | 69.5 | 2.0 Hz |
| 12 Hz | 8 | 0.045 | 70.0 | 1.8 Hz |
| 15 Hz | 8 | 0.040 | 66.9 | 1.7 Hz |
| 20 Hz | 8 | 0.042 | 68.3 | 1.7 Hz |

No modulation frequency restores the rhythm. Driving at 10 Hz, the network's own
preferred frequency, does not help either. Two further variants change nothing.

Splitting the afferents into antagonist groups driven in **antiphase**, as
flexion- and extension-tuned position sensors actually are, gives 0.055 against
0.049 in phase.

Applying the F10 sign correction, so that 57 of the 102 afferents become
excitatory as published physiology says they should be, also changes nothing.
Re-running the sweep at drive amplitude 5 with the correction applied, 3 draws
per point:

| Sensory modulation, signs corrected | Rhythmicity | Active motor neurons |
|---|---|---|
| tonic | 0.072 | 54.7 |
| 5 Hz | 0.057 | 46.7 |
| 10 Hz | 0.083 | 50.3 |
| 20 Hz | 0.054 | 50.7 |

So the negative result is not an artefact of the inverted afferent signs either.

Note the last column. The motor output does not even **entrain** to the sensory
drive: it sits near 1.5-2.4 Hz regardless of whether the input is modulated at 2
or 20 Hz. Whatever the network is doing under this much excitation, it is not
following the input.

### What this rules out and what it does not

**Rules out:** the simplest version of "the model is deafferented, so add sensory
input and the rhythm will hold". Temporal structure in a prescribed, uniform,
open-loop sensory drive does not rescue it.

**Does not rule out:** a genuinely embodied loop. Every variant here shares one
waveform across all afferents, prescribed rather than generated by the leg's own
movement, and with no coupling from motor output back to sensory input. Real
proprioceptive feedback is phase-distributed across sensors that measure
different variables at different joints, and it is *closed*. This experiment is
the closest approximation available without a body, and its negative result
should transfer to embodiment only with that caveat stated.

**Shifts weight toward** the second candidate explanation in F7: the synaptic
weight and excitability model, rather than the sensory input, is where the
problem lives. Findings F9, F10 and F11 all point the same way.

## F8b. CORRECTS F8a. The apparent pathway specificity is an excitability artefact (2026-09-14)

F8a reported that identical injected current collapses the rhythm through the
proprioceptors and does nothing through random interneurons, and attributed it
to where the sensory pathway projects. That attribution is wrong. The two
conditions were never delivering the same perturbation.

**The driven populations do not respond alike to the same current.** Measuring
what the driven cells themselves emit, at injected current 5:

| Driven population | Cells firing | Mean output rate |
|---|---|---|
| 102 leg proprioceptors | 67 of 102 | **14.42 Hz** |
| 102 random intrinsic neurons | 28 of 102 | **0.79 Hz** |

An eighteen-fold difference in emitted output for the same input. The cause is
finding F11: the model sets spike threshold from soma size, proprioceptors are
0.44x the median size and bristles 0.078x, so the same current pushes them far
harder. A comparison at equal input current is not a controlled comparison in
this model.

**Matching the drive removes the effect.** Scaling each cell's current by its own
threshold, so every driven cell is pushed the same fraction above it, eight draws
per condition at amplitude 5:

| Amplitude | Condition | Rhythmicity | Active motor neurons |
|---|---|---|---|
| - | Undriven baseline | 0.836 +/- 0.119 | 2.6 |
| 5 | Proprioceptors, flat current | 0.095 +/- 0.070 | 76.6 |
| 5 | Random interneurons, flat current | 0.830 +/- 0.124 | 3.0 |
| 5 | Proprioceptors, threshold-matched | **0.828 +/- 0.138** | 3.0 |
| 5 | Random interneurons, threshold-matched | **0.828 +/- 0.138** | 3.0 |
| 12.5 | Proprioceptors, threshold-matched | **0.104 +/- 0.078** | 79.8 |
| 12.5 | Random interneurons, threshold-matched | **0.040 +/- 0.018** | 58.6 |

The dissociation disappears in both directions. At amplitude 5 both matched
conditions return the undriven result exactly. At 12.5 both collapse the rhythm,
and if anything the proprioceptors now look slightly *less* disruptive than the
interneurons, the reverse of the flat-current picture. There is no residual
pathway effect to explain once excitability is controlled.

### The honest caveat on this correction

Threshold matching is one definition of "same perturbation" and it is not
obviously the best one. It gives low-threshold cells *less* current, so at
amplitude 5 the proprioceptors end up receiving very little and the null result
partly reflects that. The cleaner functional match is to equalise the **output
rate of the driven population** and compare downstream effects from there. The
metric to do that is now recorded on every run; the experiment was not run.

So the defensible claim is narrow and worth stating precisely: **the F8a
dissociation is not evidence of pathway specificity, because the comparison was
confounded by a large excitability difference.** Whether the proprioceptive
pathway is genuinely privileged once that is controlled remains open.

### Why this sequence is in the record

Three passes, two retractions, on a question that looked settled after the
first. The first answer was right by accident, the second was wrong for a reason
that looked like biology and was arithmetic, and the third is a control. Any
perturbation result in this model class needs the same treatment before it is
believed, including the ones in the paper this session started from.

## F13. One third of admissible sign assignments destroy the rhythm, and the failures trace to four neurons (2026-09-14)

The electron-microscope transmitter classifier does not output a label, it
outputs a probability per neuron. The published model takes the most likely one.
This asks what happens if you respect the classifier's own uncertainty: on each
replicate, redraw every neuron's transmitter from its reported probabilities,
map acetylcholine to excitatory and everything else to inhibitory, and run the
same experiment.

Redrawing flips the excitatory or inhibitory sign of **436 neurons on average,
9.5% of the network**, per draw.

| | Draws | Rhythmicity | Active motor neurons |
|---|---|---|---|
| Most-likely labels, as published | 16 | **0.836 +/- 0.119** | 2.6 |
| Sign redrawn from the classifier | 24 | **0.555 +/- 0.406** | 5.2 |

The mean is not the story; the shape is. The published labels give a tight
distribution, every draw rhythmic. Redrawing gives a **bimodal** one: 15 of 24
draws above 0.5, and **6 of 24 with no rhythm at all**, the circuit simply
failing to produce oscillating motor output. Eight of 24 fall below 0.3.

### The failures trace to four cells

The source paper's own configuration names a minimal core circuit: the
stimulated descending neuron DNg100 plus three interneurons, indices 31, 277,
617 and 1167. Running that configuration alone, with everything else masked,
does reproduce a rhythm (0.430 at 9.9 Hz, 3 draws), so the core is load-bearing.

Reconstructing each draw from its seed and asking whether any of those four
flipped:

| | Rhythm lost | Rhythm survived |
|---|---|---|
| A core neuron flipped | **4** | **0** |
| No core neuron flipped | 4 | 16 |

**Every draw that flipped a core neuron lost the rhythm, four out of four.** The
classifier's confidence in those four cells is 0.90, 0.92, 0.95 and 0.96, which
gives a 20.8% chance that at least one flips on any given draw. Observed: 4 of
24, or 17%.

Core flips explain half the failures. The other four came from elsewhere in the
436 flipped cells, so the circuit has more than one fragile point.

### What this means

The headline result of a connectome-constrained model rests on the excitatory or
inhibitory identity of roughly four neurons, assigned by a classifier that is
about 90% confident in each. That is not a criticism of the classifier, which
reports its uncertainty honestly. It is a statement about what the model
inherits: **sign is not in the connectome**, it is predicted, and the prediction
carries enough uncertainty to change the qualitative outcome a third of the time.

The constructive response is not to distrust the result but to report it as a
distribution over admissible sign assignments rather than a single run, and to
spend measurement effort on the handful of cells the outcome actually depends
on. Those four are identified and named. Determining their transmitters
experimentally is a small, well-posed piece of work with a large payoff.

### Caveats

The annotation table exposes only three of the classifier's transmitter classes.
They sum to about 0.98 on average and as little as 0.49, so resampling
renormalises over three and redistributes the missing mass proportionally. The
excitatory/inhibitory mapping is the same blanket one the model uses, so F9's
objection to treating all glutamate as inhibitory applies here too. And the
comparison is against the 16-draw baseline rather than a fresh matched
fixed-label run, which was dropped for capacity.

## F14. The primary-specimen question has a clear answer, and it is not the dataset this session used (2026-09-14)

`docs/ROADMAP.md` leaves the choice of primary connectome open and asks for a
comparison of anatomical coverage, motor mappings, body compatibility and actual
access. This session inherited MANC by using the Pugliese model. Queried
directly, the comparison is not close.

| | MANC v1.2.1 | male-cns v1.0 |
|---|---|---|
| Coverage | nerve cord only | **whole central nervous system** |
| Neuron nodes | 102,158 | 176,422 |
| Status `Traced` | 23,665 (**23%**) | 165,122 (**94%**) |
| Nerve-cord motor neurons | 731 with a named target muscle | 708 (`superclass = vnc_motor`) |
| Motor neurons named by muscle | yes, in a `target` field | yes, in the `type` field |
| Cross-reference to MANC | n/a | **673 of 708 motor neurons carry a `mancBodyid`** |
| Proprioceptive sensory neurons | 102 in the T1 subset used here | **1,454** labelled `mechanosensory_proprioceptive` |
| Descending neurons | 1,328 | 1,314 |
| Brain | absent | present, with olfactory, gustatory and visual classes |

**male-cns is the better primary specimen on every axis that matters here**, and
the 95% motor-neuron cross-reference means the work built on MANC transfers
rather than being thrown away. Front-leg motor neurons are named by the same
muscle vocabulary: `Acc. ti flexor MN`, `Ti flexor MN`, `Fe reductor MN`,
`Ta depressor MN` and so on.

Two practical notes. First, the annotation lives in different fields in the two
datasets: MANC puts the muscle in `target` and the class in `class`, while
male-cns puts the muscle in `type` and uses `superclass = vnc_motor`. A first
query against male-cns for `class = 'motor neuron'` returns nothing, which is
easy to mistake for the annotation being absent. It is not; it is elsewhere.
Second, the traced fractions are not comparable as quality scores without
checking each dataset's inclusion policy, which is exactly the caution
`CLAUDE.md` gives about neuron counts.

**Recommendation.** Move to male-cns as the primary graph, carrying the MANC
work across by `mancBodyid`, before building anything further on the nerve cord
alone. The immediate gains are the brain, a far larger and better-traced
proprioceptor population, and descending neurons with their cell bodies in the
same volume as their arbors, which is directly relevant to the excitability
problem in F11.

## F15. Across 303 simulations, not one produced both a rhythm and physiological motor rates (2026-09-14)

The strongest single statement this session can make, and it needed the whole
night's runs to make it.

Pooling **every replicate simulation of the session**, 303 in total, across all
five conditions, the synaptic-scale sweep, the sensory-drive sweeps, the
drive-target controls, the threshold-matched controls, the glutamate sweep, the
transmitter-resampling draws, the phasic sweeps and the corrected-excitability
sweep:

| Selection | n | The other readout |
|---|---|---|
| Draws that were rhythmic (score > 0.5) | 121 | median peak motor rate **2.28 Hz**, maximum **8.50 Hz** |
| Draws with physiological rates (> 20 Hz) | 121 | median rhythmicity **0.051**, maximum **0.308** |
| Draws with **both** rhythmicity > 0.5 and peak rate > 10 Hz | **0** | — |

One simulation in 303 cleared rhythmicity 0.3 with rates above 20 Hz. It came
from the **degree-matched shuffle**, that is, from a deliberately scrambled
connectome used as a negative control, not from any model of the fly.

### The boundary is sharp, and does not depend on where the thresholds are drawn

Pooling all 305 simulations with both readouts and asking, for each floor on one
axis, the best value any simulation reached on the other:

| Motor-rate floor | Simulations above it | Best rhythmicity reached |
|---|---|---|
| > 2 Hz | 230 | 0.966 |
| > 5 Hz | 139 | 0.949 |
| **> 10 Hz** | 123 | **0.308** (the shuffled control) |
| > 30 Hz | 121 | 0.308 (the same control) |

| Rhythmicity floor | Simulations above it | Best motor rate reached |
|---|---|---|
| > 0.3 | 133 | 69.2 Hz (the shuffled control) |
| **> 0.4** | 129 | **8.50 Hz** |
| > 0.8 | 74 | 5.45 Hz |

The wall sits between 8.5 and 10 Hz on the rate axis and between 0.31 and 0.4 on
the rhythmicity axis, and the only thing that ever crossed it was a scrambled
connectome. Move either threshold and the conclusion does not move.

### Fixing the excitability artefact does not create a middle ground

The most direct test. Correcting the F11 size artefact by normalising
excitability within cell class and re-sweeping the descending stimulus, six
draws per point:

| Stimulus | Rhythmicity | Active motor neurons | Median peak rate |
|---|---|---|---|
| 250 (the published value) | 0.000 | 2.7 | 1.0 Hz |
| 300 | 0.405 +/- 0.251 | 35.2 | 25.3 Hz |
| 350 | 0.144 +/- 0.234 | 66.3 | 47.8 Hz |
| 400 | 0.046 +/- 0.021 | 76.8 | 63.3 Hz |
| 450 | 0.063 +/- 0.060 | 79.5 | 70.6 Hz |

The 300 row looks like a useful compromise. It is not. Per draw:

| Stimulus | Rhythmicity, each draw | Median peak rate, each draw |
|---|---|---|
| 300 | 0.055, 0.127, **0.509, 0.511, 0.564, 0.664** | 48.2, 92.1, **2.7, 1.4, 4.0, 3.4** |
| 350 | 0.020, 0.032, 0.050, 0.054, 0.090, **0.618** | 49.3, 57.6, 62.0, 59.5, 55.2, **3.1** |

Every individual simulation lands in one of two states: **rhythmic and weak**,
at 1 to 4 Hz, or **strong and arrhythmic**, at 39 to 92 Hz. The mean of 0.405
with 25 Hz describes no simulation that actually ran. The corrected model has
the same two regimes as the uncontrolled one, only at a different stimulus.

> **Methodological note.** This was nearly reported as a positive result. The
> mean at stimulus 300 reads as a rhythm-preserving regime with eleven times the
> motor output, which would have been the most encouraging finding of the
> session. Looking at the per-draw values took two minutes and reversed it. The
> session summary tool now flags any group whose values separate into two bands.

### What this licenses

For **this model class**, a deafferented connectome network with rate-based
units, weight proportional to synapse count times a global scale, sign from a
transmitter prediction and excitability from soma size: rhythm and physiological
motor output are mutually exclusive across every setting tried. That is 303
simulations, not a proof, and the space is not exhausted.

It does **not** license a claim about the fly, or about connectome-constrained
modelling in general. What it does is locate the problem. Since F12 rules out
sensory timing as the fix and F15 rules out excitability recalibration, the
remaining candidates are the ones F9, F11 and F13 point at: **the synaptic
weight rule and the sign assignment**, neither of which is measured, both of
which the connectome cannot supply.
