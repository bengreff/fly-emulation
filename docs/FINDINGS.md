# Findings

Measured results with their conditions and limits. Newest last. Every entry must
be reproducible from a provenance JSON in `runs/`.

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
