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

## Where session 8 left things

- **Working model m4:** curated transmitters (consensusNt), efficacy recalibrated by a closed-loop rule, monoamines without fast sign. Sugar→MN9 is marginal (8.9 ± 5.9 Hz over 10 trials).
- **Config T under m3 stands on 2/3 seeds** (min z 1.03 / 0.97 mm). T's only failure is the saturated CX ring.
- **Receptor transcripts for ~95 types** (Davis 2020, Turner-Evans 2020, Epiney 2025) give glutamate sign rows for 54 types.
  - Wiring cannot predict receptor signs.
  - snRNA iGluR/GluCl ratios are biased upward relative to bulk.
- **EPG headings are inferred from connectivity.** All ring position results before that fix are unreliable, including s7's single-knob screens. Those were re-screened under m4 (DECISIONS s8).

## Ranked next steps

The strategy is set out in `docs/NEXT_SESSION_PROMPT.md` and the reassessment at the end of `docs/SESSION8_LOG.md`.

1. **Honest body at rest:** passive, not guessed, wing/abdomen/head/haltere/mouthpart actuators, labelled absent. Joint-limit occupancy as a metric.
2. **Scoped locomotion configuration L** = T + passive non-leg actuators + CX ring output clamped (labelled). Stability, standing over 0.5–3 s, DNg100/MDN command direction and a gait criterion on fresh seeds.
3. **Calibration engine:** CMA-ES over ≤ 20 interpretable class-level parameters against a declared fit-set battery; held-out data judged only after dev criteria pass; resumable on backhouse. It replaces one-knob hand-tuning.
4. **Keep filling blanks with type-matched data:**
   - transcriptomes (VNC, MB);
   - FANC access for leg sensors;
   - neuromodulator pool magnitudes (MS rows stable under default but not under T).
5. Re-test adaptation + Delta7 ×4 without MS; check whether VNC premotor classes should be graded.

## Later milestones (dependency order)

- Flight: needs a wing hinge driven by steering muscles, and power-muscle and thorax dynamics.
- Neuromodulation and internal state: pools exist but are inert; receptor data per type is needed. M0 shows the fast-sign placeholder must go first.
- Learning: KC→MBON depression exists, off. Needs an odour-shock assay held out from all fitting.
