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
