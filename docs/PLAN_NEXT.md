# Plan: next experiments

**Forward-looking only; rewritten each session.** Completed plans are in `docs/archive/`. The ranked list below is also the basis of `docs/NEXT_SESSION_PROMPT.md`.

## Goal and layers

The male-CNS connectome controls an accurately simulated fly body. Each layer is checked separately, because a good-looking behaviour can hide a wrong layer.

| Layer | "Accurate" means |
|---|---|
| Neural | predicts held-out published interventions better than a shuffled-wiring control; resting and driven rates within measured ranges |
| Neuromuscular | per-spike force and twitch within Azevedo 2020 ranges |
| Body | mass-, range- and collision-checked |
| Behaviour | kinematics match measured data under the same stimulus protocol |

## Ranked next steps

1. **AL transmission from measurements (F-AL-3).** Set an ORN→uPN efficacy from the measured unitary PSP, EPSC rate and reliability (Kazama & Wilson 2008, 2009).
   - Target: PN spontaneous 1–5 Hz, ≥ 70% active.
   - Held out: flybench olfactory tasks.
2. **Leg VNC operating point (F-AZ-2, F-VNC-1/2).**
   - Identify 13Bα/10Bα among male-cns IN13B/IN10B types, in T2/T3.
   - Make them graded, with an operating point fitted to the 13Bα Vm–angle tuning.
   - Hold out the 10Bα/9Aα data.
   - Then run `scripts/score_reflex.py` on the dev cell, and on the sealed cell only after a dev pass.
3. **Replace the slow MN's intrinsic tonic drive with synaptic drive** once premotor excitation exists. Azevedo: the rest rate is synaptically set.
4. **Standing, then walking,** once the reflex passes. Criteria are pre-registered in DECISIONS: thorax ≥ 0.90 mm over 0.5–1.5 s; the DNg100/MDN command experiments.
5. **Background:**
   - re-score flybench with Hallem rates on;
   - find measured resting potentials for central neurons to replace the borrowed −52 mV;
   - least-squares multi-axis muscle action (hind-leg thorax-coxa signs are fragile).

## Later milestones (dependency order)

- Flight: needs a wing hinge driven by steering muscles, and power-muscle and thorax dynamics.
- Neuromodulation and internal state: pools exist but are inert; receptor data per type is needed.
- Learning: KC→MBON depression exists, off. Needs an odour-shock assay held out from all fitting.
