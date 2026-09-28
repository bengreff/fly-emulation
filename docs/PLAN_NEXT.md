# Plan: next work

**Forward-looking only; rewritten each session.** The plan is `docs/CONSTRUCTION.md`; the state after session 10 is in `docs/HANDOFF.md`.

Every mechanism in the inventory now exists (0 absent), and the working model is m6 (the template body with two searched class values and sensory latency). The programme moves from construction to **search**, with the remaining construction items done where they block a target.

1. **Search engine v1 on the GPU (the priority).**
   - Exact closed loop: `scripts/gpu_closed_loop.py --k 1` with worker bodies; measure throughput at B = 12-24 and make it the evaluator (k > 1 changes the dynamics, F-STAB-5).
   - Target library v1, split by dataset, each target baseline-checked on m4/m5 before it is registered: stability (silence after input removal, seeds), sugar->MN9 and its dose response, bitter suppression, water->MN9 (currently 0 Hz in m4 and m5: a fit target, not a held-out one), PN/KC spontaneous rates (spent: dev only), Azevedo slow-MN rest rate (seen), flybench olfactory tasks (held out for AL changes).
   - Pre-registered class-level CMA-ES over N5 release/input scales of all 70 classes (140 dims) plus N3 tonic drive, within bounds; brain-only targets on `gpu_assay.py`, closed-loop targets on the GPU loop. Report bound hits and margins.
2. **Switch on the neutral mechanisms at their priors, one group at a time, re-testing m6 each time:** (N15 latency done: m6) N15 adaptation, N7/N8 slow components, N12 gap junctions, N21-N24 plasticity, N27 glia. Principle 2 says "mechanisms always on at their prior"; m6 still has them at neutral.
3. **Body battery (task 7):** leg isometric force per unit class vs Azevedo 2020; leg resistance to imposed movement vs eLife stiffness; fall onset vs standing height with decaying activation (`deadfly.run(activation=..., activation_tau_ms=100)` needs a standing torque vector first); adhesion gate in stance and swing.
4. **Flight:** fluid coefficients as fitted unknowns (Kutta 3.1 inferred); body pitch; free (untethered) hover attempt at 0.05 ms; b1 locking one spike per cycle (currently ~0.55 vector strength); wing campaniform proxy should read the stroke (yaw), not deviation.
5. **Open items carried:** coxa DOF labels by function and the rest refit (F-COXA-1), mid/hind muscle parameters, B18 bristle map, N19 receptor maps live, peptide receptor tables, eLN->PN gap junctions (types unidentified).

The session prompt is `docs/NEXT_SESSION_PROMPT.md`.
