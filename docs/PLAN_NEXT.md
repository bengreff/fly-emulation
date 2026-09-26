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

## Where session 7 left things

- Measured first-order synaptic strength (T) moves the embodied behaviour toward biology: reflex sign, standing height, and the DNg100 forward shift.
- It is blocked by the **CX ring**, which is bistable (silent or saturated) instead of holding a bump.
- The reflex's missing piece is extension→flexor excitation. It is cancelled by glutamatergic IN21A006.
- The AL target's post-hoc budget is spent. The measured values stay as options.

## Ranked next steps

1. **Central-complex ring operating point (F-STAB-1).** Pre-register the targets before any change:
   - (i) a local EPG kick leaves a persistent bump, with ≤ 1/4 of EPGs active for ≥ 200 ms after input stops;
   - (ii) a full-ring kick does not saturate (PEN < 50 Hz);
   - (iii) the resting PEN rate, held out: 3.9 ± 2.6 Hz (Turner-Evans 2017).

   Tools: `scripts/probes/cx_kick.py`; `cx_hz` in `closed_loop_check.py`.

   Candidates to screen first, then pre-register one:
   - ring depression (removes saturation, 2/3 seeds stable under T);
   - adaptation;
   - measured PEN input resistance, through per-type input gain;
   - wedge-structured Delta7 inhibition. Uniform Delta7 ×8 was not enough.

   Measured ring targets are gathered (F-CX-1). The single-knob screens failed. Next candidate: slow (NMDA-like) recurrent excitation, since EPGs express NMDA receptors.
2. **Re-test T with a working ring, on fresh held-out data.**
   - Standing (≥ 0.90 mm, 3 seeds) and stability (the CX scored by the new criterion).
   - The command direction on fresh seeds, **plus a gait criterion** (alternating tarsal stepping).
   - The reflex on a **sealed spare** (180621 or 181127), only after a dev H1 + H2 pass. The dev target itself is over budget and cannot gate by itself.
3. **Extension pathway (F-XFER-1).** Settle claw and hook directions from data: the FANC T1L labels of Lee et al. 2025 (`data/raw/lee2025/`), joined to male-cns through FANC CAVE (needs an account from Ben) or NBLAST bridging. Look for any physiology of IN21A→MN glutamate. Then re-derive, rather than fit.
4. **Per-class operating points from the targets table.** Resting potentials of −55 to −68 mV; KC gap 21.5 mV; MN rests −48 / −60 / −68 mV. Apply them one class at a time with the regression checks, never globally: a global measured strength (E1) is unstable.
5. **Abdomen and wing motor layer** (s7 diagnostic): in the video the abdomen curls dorsally. Zeroing its torque raises the default fly but tips T over. Calibrate abdominal MN signs and forces, as for the legs, before reading standing as VNC evidence.
6. **Background:**
   - M0 recalibration: monoamines as fast excitation is wrong but load-bearing;
   - flybench re-score with Hallem rates (needs a port into flybench's LIF);
   - multi-axis muscle action; muscle co-contraction stiffness, since the torque actuators have none.

## Later milestones (dependency order)

- Flight: needs a wing hinge driven by steering muscles, and power-muscle and thorax dynamics.
- Neuromodulation and internal state: pools exist but are inert; receptor data per type is needed. M0 shows the fast-sign placeholder must go first.
- Learning: KC→MBON depression exists, off. Needs an odour-shock assay held out from all fitting.
