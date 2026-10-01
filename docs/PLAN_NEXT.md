# Plan: next work

**Forward-looking only; rewritten each session.** The programme is `docs/CONSTRUCTION.md`; the state after session 11 is in `docs/HANDOFF.md`; ranked fidelity upgrades are in `docs/FIDELITY_LADDER.md`.

## The goal (Ben, 28 September 2026)

Fill in **100% of the fly's information at the highest fidelity that could plausibly matter**, finish the entire brain-body build, run many copies in parallel, and run experiments that fill in data. **Not** tweaking things until a little behaviour appears. Stability and behaviour checks are guardrails and validation; they are never the objective a change is tuned toward.

**Progress metric: the ledger.** `scripts/blank_ledger.py` today: 96.9 M of 367 M per-element slots filled by data (26%); 13.8 k of 824 k parameter slots filled; 435 k running on shared defaults; 655 data-model unknowns, 79 with bounds from data. Every session reports how many slots moved from absent / default / guessed to data, derived or biology-inferred, per mechanism and per grain (global, class, type, cell, synapse).

## 1. Make the ledger measure what we want (first, small)

- Report fill by source level: measured > derived > inferred by a biological rule (per cell) > class prior > guessed default > absent; per mechanism and grain, for `data/model/` and the per-element registry slots.
- Reconcile the registry ledger with `mechanisms.yaml` (the registry still counts ~270 M per-element slots as "mechanism absent" for mechanisms that now exist at a lumped level; say which fidelity each slot has).

## 2. Fill per-cell and per-synapse information from biology (the core)

Per-cell values cannot be measured one by one; infer them by rules with few class-level parameters (F-VAR-1: type explains 83-91% of within-connectome variation; the rest is structured by size, segment, side and development):
- **Per-cell physiology from morphology:** input gain / input resistance from cell size within type (motor size principle, Azevedo 2020); synaptic strength compensating input number (Tobin, Wilson & Lee 2017); per-cell conduction delay (exists).
- **Position:** segment and side offsets for serial homologs.
- **Development:** hemilineage and temporal cohort (birth order) as grains; a simulated development phase with homeostatic intrinsic and synaptic plasticity that sets per-cell gains toward class set points.
- **Per-synapse identity from transcriptomes:** receptor subtype and sign per postsynaptic type (extend `scripts/infer_receptors.py`: iGluR vs GluCl, nAChR subunits, GABA-A vs GABA-B, NMDA, mGluR, mAChR), so N6/N7/N8 fractions become type-specific data, not uniform priors; innexins (shakB etc.) for gap-junction sites; monoamine and peptide receptor maps (N19, N20); ion-channel genes for spiking vs graded mode and adaptation (N1, N2, N4).
- **Data acquisition:** single-cell atlases matched to male-cns types (Fly Cell Atlas; Davis 2020; optic lobe atlases; VNC atlas; Epiney 2025), lineage/birth-order atlases (leads in FINDINGS F-VAR-1 sources). Up to ~200 GB on backhouse is approved.
- **Validation of the rules:** they must reproduce measured within-type gradients (tibia flexor pool: input resistance, rest rate, recruitment order vs size; dev data only, sealed cells untouched); an ablation shows what per-cell information changes.

## 3. Finish the body at the fidelity that could plausibly matter

Coxa DOFs and ranges by function and the rest refit (F-COXA-1); mid/hind muscle parameters; neck and abdomen muscles with MN maps; proprioceptor periphery (FeCO claw/hook/club dynamics, campaniform fields, hair plates); bristle map (B18); wing hinge (Melis 2024 model if obtainable), wing campaniforms reading the stroke; standing drive and the decaying-activation fall test; the body battery (force per unit class, leg resistance, jump impulse, wingbeat and lift).

## 4. Many copies in parallel

- Batch our Python sensing and motor code across flies (~70% of body time; F-GPU-3), several flies per worker, fewer round trips. Exact coupling (k = 1).
- GPU-physics feasibility on backhouse (scratch venv, MuJoCo 3.14 + mujoco-warp; MJX second): list unsupported features (mesh contact margins, body-transmission adhesion, fluid, tendons), reimplement adhesion as a force hook if needed.
- Equivalence first (dead fly 1 s, 300 ms of m6 closed loop vs CPU MuJoCo), then the fixed decision rule: port only if equivalent and >= 5x the batched-CPU throughput at the needed batch size.
- Include the per-cell rules and the new per-synapse data in the GPU brain (per-member arrays; slow channels and plasticity are refused today).

## 5. Experiments that fill in data

- **Sensitivity and ablation over ensembles:** sample many complete flies within bounds (sample_fly) and measure which unknowns change the model's physiology; fill the most consequential first.
- **Fit remaining unknowns to recorded physiology** (target library v1, each target checked on the base model before registration, split fit / dev / held out). A fitted value is inferred; searching is how unknowns without direct data get filled, bounded by biology, never to tune a behaviour.
- **Held-out judgement** on physiology and interventions the fit never saw.

## 6. Planned study (later; not started): reconstructing the original individual

Ben's final question, part two (verbatim in `docs/CONSTRUCTION.md`, Mission): how much scan information reconstructs the ORIGINAL INDIVIDUAL? The planned design is in `docs/FIDELITY_LADDER.md`, "Planned study":
- a fully specified synthetic fly as ground truth, with siblings drawn from an individual-variation model;
- a simulated scan of it;
- reconstruction from subsets of that information by our own pipeline;
- identity recovered when the reconstruction is closer to its original than the siblings are to each other.
It needs the first part answered first (a model that carries species behaviour) and an individual-variation model from cross-specimen connectome data.

The session prompt is `docs/NEXT_SESSION_PROMPT.md`.
