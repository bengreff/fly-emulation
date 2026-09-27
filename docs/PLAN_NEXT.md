# Plan: next work

**Forward-looking only; rewritten each session.** The plan is the construction programme, `docs/CONSTRUCTION.md`. State after session 9 is in `docs/HANDOFF.md`.

1. **Finish task 4 (B3 rest angles).** Replicate the eLife 2025 tethered, weighted protocol in the model (dead fly, body fixed, weights at the tarsi, body rotated), using their angle definitions (methods Eqs. 5–11). Fit the spring references so the model's equilibria match Figure 3C, and damping to the fall time course. Then adopt measured B3 + B14 into the template's leg rest-posture criterion.
2. **Finish task 5 (B4/B5).**
   - Resolve the MN→muscle→DOF map for the coxa and femur-roll pools (FANC/MANC atlas), so no antagonist muscle is orphaned and the coxa directions are no longer guessed.
   - Mid/hind muscle parameters: FlyMimic anatomical MTUs, scaled and labelled.
   - Fatigue for fast/intermediate units (force per spike saturates by ~10 spikes).
   - Give `standing.py` a Hill-mode readout (it still reads legacy unit torques).
   - Compute a standing drive from the Hill model and run the decaying-activation dead-fly variant (τ ≈ 100 ms) against the measured fall.
3. **Task 6 (B7 adhesion)** with load/shear detachment.
4. **Task 7:** dead fly passes with the template body; body physical battery for the legs.
5. Tasks 8–14 as listed in CONSTRUCTION.md: flight apparatus, jump, feeding/grooming/antenna, neural mechanisms, state and learning, `sample_fly` with acceptance tests, ledger report.

Then the search: GPU simulator, target library, class-level search within bounds, gradient refinement, ensembles, held-out judgement, mechanism ablation.

The session prompt is `docs/NEXT_SESSION_PROMPT.md`. Completed plans are in `docs/archive/`.
