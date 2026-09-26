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

- Working model m3: curated transmitters (consensusNt) + efficacy recalibrated by a closed-loop rule. Sugar→MN9 is marginal (6.3 Hz).
- Receptor transcripts (Davis 2020) exist for 69 types, including EPG and Delta7. Wiring cannot predict sign-critical receptors.
- CX ring: warm start fails; NMDA lead withdrawn; Delta7 +1 gives a localised persistent state under T, but at a fixed heading.

## Ranked next steps

1. **CX ring: movable bump.** The s8 bump-move test shows that the Delta7 +1 bump is **pinned** to ~350° or ~70°. Find the asymmetry:
   - per-glomerulus PEN→EPG and EPG→PEN offset structure;
   - the distribution of ER/ExR input around the ring. The ER neurons that give EPG 61% of its input are silent in the model.

   Then pre-register on fresh seeds, with the bump criteria plus "the bump follows the kick".
2. **Recheck m3 consequences:**
   - redo M0 (monoamines as sign 0) under m3, since the s7 result was confounded by KCs;
   - re-test T under m3 (standing, stability, command direction on fresh seeds with a gait criterion);
   - check the marginal sugar pathway over more trials.
3. **Fill blanks with transcriptomes matched to types.** Wiring cannot infer receptor signs (F-RCPT-1). Candidate sources: the Fly Cell Atlas head, T2-lineage snRNA-seq (Epiney 2025, CX), and VNC atlases (Allen 2020). The algorithm is a type-matching step (marker genes ↔ connectome type, with confidence), then receptor calls → glutamate sign, GABA-B share, and modulator receptors (the 57k guessed slots).
4. **Make the ledger count per-type rows** so fills show in the totals.
5. **Extension pathway (F-XFER-1):** FANC production access (Ben) or NBLAST bridging.
6. **Per-class operating points** (resting potentials −55 to −68 mV, KC gap), one class at a time.
7. **Abdomen and wing motor calibration.**

## Later milestones (dependency order)

- Flight: needs a wing hinge driven by steering muscles, and power-muscle and thorax dynamics.
- Neuromodulation and internal state: pools exist but are inert; receptor data per type is needed. M0 shows the fast-sign placeholder must go first.
- Learning: KC→MBON depression exists, off. Needs an odour-shock assay held out from all fitting.
