# Plan: next work

**Forward-looking only; rewritten each session.** The plan is the construction programme, `docs/CONSTRUCTION.md`. State after session 9 is in `docs/HANDOFF.md`.

1. **Finish task 4 (B3).**
   - Relabel the joints.py coxa DOFs and range envelopes by function (F-COXA-1), then redo the rest fit (`scripts/passive_rest_protocol.py --fit`) so the middle leg stops pressing envelopes.
   - Pin down the gamma convention.
   - Constrain leg damping.
   - Add a sharper posture test: the paper's free-standing fall heights and times.
2. **Finish task 5 (B4/B5).**
   - Resolve the MN→muscle→DOF map for the coxa and femur-roll pools, so no antagonist muscle is orphaned. The s9 literature read (FINDINGS F-COXA-1) says the coxa muscles act on coupled motions: define coxa muscles by their action on the paper's angles (via the Jacobian), not by joint name. FlyMimic mid/hind MTUs are not public; ask the authors or build them from anatomy.
   - Mid/hind muscle parameters: FlyMimic anatomical MTUs, scaled and labelled.
   - Fatigue for fast/intermediate units (force per spike saturates by ~10 spikes).
   - Give `standing.py` a Hill-mode readout (it still reads legacy unit torques).
   - Compute a standing drive from the Hill model and run the decaying-activation dead-fly variant (τ ≈ 100 ms) against the measured fall.
3. **Task 6 (B7 adhesion)** with load/shear detachment.
4. **Task 7:** dead fly passes with the template body; body physical battery for the legs.
5. Tasks 8–14 as listed in CONSTRUCTION.md: flight apparatus, jump, feeding/grooming/antenna, neural mechanisms, state and learning, `sample_fly` with acceptance tests, ledger report.

Note F-STAB-2: the full template body ignites the Mi18/DNge019/DNg12 loop on 2 of 3 seeds. Task 11's class-level strengths, background drive and adaptation are needed for the template to be stable. Consider moving part of task 11 earlier if it blocks body work.

Then the search: GPU simulator, target library, class-level search within bounds, gradient refinement, ensembles, held-out judgement, mechanism ablation.

The session prompt is `docs/NEXT_SESSION_PROMPT.md`. Completed plans are in `docs/archive/`.
