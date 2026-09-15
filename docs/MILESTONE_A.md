# Milestone A: a causal front-leg interface

Grounded in the measurements of session 1 (`docs/FINDINGS.md`), not in the
aspirational sketch in `docs/ROADMAP.md`. Every step names the evidence it rests
on and what it would take to falsify it.

## Why the front-left leg, and why the tibia flexor inside it

The front leg is the only place where every link of the sensorimotor loop has
independent data:

| Link | Evidence available | Verified this session |
|---|---|---|
| Descending input to VNC | MANC connectome, 1328 descending neurons | yes, queried live |
| Premotor circuit | 4604-neuron T1 network, reproducible dynamics | yes, F3 |
| Motor neuron to muscle | MANC target annotations, 20 muscles, 144 motor neurons | yes, F2, join is 144/144 |
| Per-motor-unit force | Azevedo et al. 2020, tibia flexor, 0.1 to 10 uN per spike | numbers extracted |
| Muscle and limb mechanics | flygym musculoskeletal model, 15 actuators | yes, F6, covers 68% |
| Proprioceptive feedback | FeCO subgroups characterised, spike rates absent | yes, F5, gap found |

The tibia flexor pool is the single best-instrumented muscle in the fly: 15
motor neurons per side in the connectome, matching the ~15 counted
electrophysiologically, spanning a 13x soma-size range, with measured force per
spike at three points along that gradient. Nothing else in the animal is this
well constrained.

## The four gaps that actually block the loop

1. **Motor output has nowhere to go for a third of the leg.** 23 of 72 left
   front-leg motor neurons drive muscles absent from the body model: femur
   reductor, both tarsus muscles, and the long tendon muscles. Without tarsus
   actuators there is no active foot, so ground contact and adhesion cannot be
   controlled by the circuit that really controls them.
2. **Motor units are not resolved.** The 15-neuron tibia flexor pool collapses
   onto one actuator, so the size principle, the mechanism the fly actually uses
   to grade force, cannot be represented. This is the gap most worth closing
   first because the measurements to close it exist.
3. **Afferents have no rate calibration.** The 102 proprioceptors are in the
   graph, their encoding roles are known, and their firing rates are not
   published. Sensory drive is currently a swept unknown.
4. **Motor output is far below physiological without sensory drive.** Peak
   motor-neuron rate is 2.25 Hz against a measured 30 Hz resting rate for a slow
   tibia flexor unit (F3). Tonic proprioceptive drive raises rates into range but
   costs the rhythm, which is the tension the sweep in progress is measuring.

## Plan, in dependency order

**A1. Resolve the tibia flexor motor pool.** Replace the single
`LFTibia_flex` actuator with 15 parallel motor units sharing one tendon, each
with a force scale drawn from the soma-size gradient and anchored to the three
measured points (slow <0.1 uN, intermediate ~1 uN, fast ~10 uN per spike).
Fit the size-to-force mapping, do not assume linearity. Reproduce Azevedo's
force-per-spike saturation curve, force from two spikes about 1.6x one spike,
saturating near ten spikes, as the acceptance test. **Falsified if** no
monotonic size-to-force mapping reproduces the measured summation.

**A2. Add the missing muscles.** Femur reductor, tarsus levator and depressor,
and the long tendon muscles, using published leg anatomy for attachment points.
Every attachment must be anatomically justified; `docs/PROJECT.md` explicitly
forbids placing a muscle where it is convenient rather than where it is.
**Falsified if** passive joint mechanics no longer match measured passive
stiffness after the additions.

**A3. Build afferent transducers with declared uncertainty.** Map joint angle,
angular velocity and vibration onto firing rates for the claw, hook and club
subgroups, using the measured encoding roles and angle ranges, with the overall
rate scale left as a fitted parameter carrying explicit bounds. Record it as
fitted, never as measured. **Falsified if** no rate scale reproduces both the
directional selectivity and the position tuning reported in the imaging data.

**A4. Close the loop and test what the open loop could not.** With A1 to A3 in
place, run the circuit against the body and ask the question this session could
only pose: does phase-locked, body-generated proprioceptive feedback produce
both physiological motor-neuron rates and a stable rhythm, where uniform tonic
drive produced only one or the other? This is the discriminating experiment.

**A5. Hold out an intervention.** Reserve a published perturbation, an afferent
ablation or an identified interneuron silencing, that is used in no fitting step.
Predicting it correctly is the first real evidence of causal organisation.

## What would make me abandon this route

If A4 shows that no biologically admissible afferent model produces both
physiological rates and a stable rhythm, the count-proportional synaptic weight
assumption is the prime suspect, and the next step is per-cell-type synaptic
gains fitted against physiology rather than more body engineering.
