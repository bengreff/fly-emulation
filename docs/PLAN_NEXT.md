# Plan: next work

**Forward-looking only; rewritten each session.** The plan is the construction programme, `docs/CONSTRUCTION.md`. State after session 9 is in `docs/HANDOFF.md`. The order below deliberately pulls part of task 11 forward (DECISIONS, "End-of-session judgement calls").

1. **Brain mechanisms needed for a stable template (task 11, first part).** The target is to make the full template (`closed_loop_check.py --template`) silent after input removal on 3/3 seeds, with sugar→MN9_L > 5 Hz (the adoption rule).
   - **N3 per-class background drive:** rows per circuit class (`data/model/classes.csv`) with bounds, prior at 0 (neutral) or at a measured spontaneous rate where one exists.
   - **N5 per-class synaptic strength:** release/postsynaptic gain per circuit class, bounds 0.1–10, prior 1 (neutral); include the ORN→uPN measured 10.9x as that class's prior.
   - Each gets a neutral-equivalence test (all at prior = m4, exactly).
   - Diagnose which classes carry the Mi18/DNge019/DNg12 loop (F-STAB-2); record which bounded class parameters could quench it without touching sugar→MN9. That is a declared, pre-registered search, not hand-tuning (WORKFLOW §4.3).
   - Global adaptation is ruled out as the fix (F-STAB-3).
2. **Task 5 remainder.**
   - Coxa muscles with moment arms on all three coxa axes (FlyMimic-style vectors; F-MUSCLE-2, F-COXA-1), so no coxa direction is muscle-less.
   - Fatigue for fast/intermediate units (force per spike saturates by ~10 spikes).
   - A Hill-mode readout for `standing.py`.
   - A standing drive from the Hill model, then the decaying-activation dead-fly variant (τ ≈ 100 ms).
3. **Task 4 remainder.**
   - Relabel the joints.py coxa DOFs and range envelopes by function (F-COXA-1), then redo the rest fit so the middle leg stops pressing envelopes.
   - Pin down the gamma convention.
   - Constrain leg damping.
4. **Task 6:** test the adhesion gate in stance and swing; constrain the peel ratio (stance shear/normal ~0.8 is near the guess).
5. **Task 7:**
   - dead fly and leg battery with the template body;
   - the sharper fall test (fall onset vs standing height, eLife Fig 5/6);
   - adopt the template body as the working default if the adoption rule passes.
6. Tasks 8–14 as listed in CONSTRUCTION.md.

Then the search: GPU simulator, target library, class-level search within bounds, gradient refinement, ensembles, held-out judgement, mechanism ablation.

The session prompt is `docs/NEXT_SESSION_PROMPT.md`. Completed plans are in `docs/archive/`.
