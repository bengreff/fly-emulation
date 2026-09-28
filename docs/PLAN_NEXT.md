# Plan: next work

**Forward-looking only; rewritten each session.** The plan is `docs/CONSTRUCTION.md`; the state after session 10 is in `docs/HANDOFF.md`.

Every mechanism in the inventory now exists (0 absent), and the working model is m6 (the template body with two searched class values and sensory latency). The programme moves from construction to **search**, with the remaining construction items done where they block a target.

0. **Per-cell physiology from biology, not search (F-VAR-1; Ben, 28 Sep).** Per-cell values are inferred by rules whose few parameters are searched at class level:
   - morphology: per-cell input gain from cell size within type, g_i = (size_i / type median)^(-alpha_class) (Azevedo 2020 size principle; Tobin 2017 conductance tuned to dendrite size); alpha bounded [0, 1];
   - wiring normalisation within type: w_i scaled by (N_in,i / type median)^(-beta_class) (Tobin 2017 compensation);
   - position: segment (neuromere) and side offsets for serial homologs as class-level unknowns;
   - developmental order: temporal cohort within hemilineage (published temporal TF code and a lineage/birth-order atlas: leads) as a grain once cells can be mapped;
   - a simulated development phase: homeostatic intrinsic and synaptic plasticity toward class target rates sets per-cell gains before any evaluation; its rule rates and set points are the unknowns.
   Tests: (a) the rules must reproduce measured within-type gradients (tibia flexor pool: input resistance, rest rate and recruitment order vs size; Azevedo 2020, seen data as dev, sealed spares untouched); (b) ablation: in a fitted fly, replace rule values by type means and measure what changes; (c) random per-cell spread (degeneracy) as ensembles, not search.
1. **Search engine v1 on the GPU (the priority).**
   - Exact closed loop: `scripts/gpu_closed_loop.py --k 1` with worker bodies; make it the evaluator (k > 1 changes the dynamics, F-STAB-5).
   - **Batching vs porting the body (F-GPU-3), decided by measurement:**
     1. Batch our Python sensing and motor code across members (one numpy call for all flies; several members per worker; fewer pipe round trips). Needed either way; it removes ~70% of body time. Measure fly-seconds per wall-second at B = 16-64 on 8 workers.
     2. GPU-physics feasibility (half a day, scratch venv on backhouse, MuJoCo 3.14 + mujoco-warp; MJX as a second option): rebuild the fly; list unsupported features (mesh contact margins, body-transmission adhesion, fluid, tendons); where needed, reimplement adhesion as an applied-force hook.
     3. Equivalence before speed: dead fly 1 s and 300 ms of m6 closed loop vs CPU MuJoCo (collapse onset within 1 ms, thorax trajectory within 20 um, same silence verdicts).
     4. Decision rule (fixed now): port only if the GPU physics passes (3) without changing a body mechanism's behaviour and gives >= 5x the batched-CPU throughput at the batch size the search needs; otherwise stay batched. Rough need: class-level CMA-ES, population 64 x 3 seeds x 1.3 s per generation; at ~1 fly-second per wall-second (plausible after batching) that is ~4 min per generation, which is enough for class level; type-level search and ensembles are what would require the port.
   - Target library v1, split by dataset, each target baseline-checked on m4/m5 before it is registered: stability (silence after input removal, seeds), sugar->MN9 and its dose response, bitter suppression, water->MN9 (currently 0 Hz in m4 and m5: a fit target, not a held-out one), PN/KC spontaneous rates (spent: dev only), Azevedo slow-MN rest rate (seen), flybench olfactory tasks (held out for AL changes).
   - Pre-registered class-level CMA-ES over N5 release/input scales of all 70 classes (140 dims) plus N3 tonic drive, within bounds; brain-only targets on `gpu_assay.py`, closed-loop targets on the GPU loop. Report bound hits and margins.
2. **Switch on the neutral mechanisms at their priors, one group at a time, re-testing m6 each time:** (N15 latency done: m6) N15 adaptation, N7/N8 slow components, N12 gap junctions, N21-N24 plasticity, N27 glia. Principle 2 says "mechanisms always on at their prior"; m6 still has them at neutral.
3. **Body battery (task 7):** leg isometric force per unit class vs Azevedo 2020; leg resistance to imposed movement vs eLife stiffness; fall onset vs standing height with decaying activation (`deadfly.run(activation=..., activation_tau_ms=100)` needs a standing torque vector first); adhesion gate in stance and swing.
4. **Flight:** fluid coefficients as fitted unknowns (Kutta 3.1 inferred); body pitch; free (untethered) hover attempt at 0.05 ms; b1 locking one spike per cycle (currently ~0.55 vector strength); wing campaniform proxy should read the stroke (yaw), not deviation.
5. **Open items carried:** coxa DOF labels by function and the rest refit (F-COXA-1), mid/hind muscle parameters, B18 bristle map, N19 receptor maps live, peptide receptor tables, eLN->PN gap junctions (types unidentified).

The session prompt is `docs/NEXT_SESSION_PROMPT.md`.
