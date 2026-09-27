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

1. **CX ring: from discrete to continuous.** Under T, adaptation + Delta7 ×4 (candidate files `candidates_s8_adapt_d7x4.csv`) gives a persistent localised bump at physiological PEN rates, but it lands in ~3 preferred positions. Next:
   - find what sets the basins (per-heading input asymmetry near the ring seam; EPGt; uneven heading spacing);
   - combine with per-class normalisation or Delta7-output scaling (s8 ring6 results in DECISIONS);
   - then pre-register on fresh seeds (4–6): bump criteria plus "bump within 45° of a strong kick at 4 headings".
   - Also test in the default config: the default ring is silent, and a bump needs a living ring without T's drive.
2. **T with a working ring:** standing (3 seeds, fresh), stability, command direction with a gait criterion, and the reflex on a sealed spare after a dev pass.
3. **Neuromodulator pools:** the receptor-signed sensitivities (`candidates_s8_modsens.csv`, 68 types) pass in the default config but sustain a ~9 Hz brain under T. Calibrate the pool magnitude (`mod_increment`, sensitivity 0.2, τ 1 s: all guessed) against stability under both configs before re-adopting. Also re-test adaptation + Delta7 ×4 under T without MS (its B1 passes happened with MS on).
4. **More transcriptome-matched types:** VNC (Allen 2020 / Cachero 2026 hemilineage-level); MB (Crocker 2016). See `docs/research/transcriptome_sources_s8.md`.
5. **Extension pathway (F-XFER-1):** FANC production access (Ben) or NBLAST bridging.
6. **Per-class operating points** (resting potentials −55 to −68 mV, KC gap), one class at a time.
7. **Abdomen and wing motor calibration.**

## Later milestones (dependency order)

- Flight: needs a wing hinge driven by steering muscles, and power-muscle and thorax dynamics.
- Neuromodulation and internal state: pools exist but are inert; receptor data per type is needed. M0 shows the fast-sign placeholder must go first.
- Learning: KC→MBON depression exists, off. Needs an odour-shock assay held out from all fitting.
