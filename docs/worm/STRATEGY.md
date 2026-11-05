# Worm strategy (Ben + Director, live session 2026-11-05)

Status: **agreed direction**, refined live with Ben. Binding answers are in `~/director/goals.md` (fly-emulation section). PLAN.md's ledger, adoption and fitting sections stay; this file sets the order of attack and the method.

## The problem
Underdetermination. The worm's structure is well measured (cells, wiring, gene expression); most numbers that set its dynamics are not (channel densities, synapse strengths, peptide kinetics). Fitting thousands of free numbers against data that cannot pin them gives many wrong worms that fit equally well. Machine-learning fitting does not escape this; it finds one of the wrong worms faster. That is the pattern of earlier efforts (`research/OPENWORM_AND_NOVELTY.md`: OpenWorm single-neuron evolutionary fits; BAAIWorm 136 neurons against one imaging dataset with no held-out test; EP-GAN one neuron at a time, not recovering ground truth).

## The bar (Ben, 5 Nov)
A worm inside the region of parameter space real worms occupy, shown by held-out perturbations (mutants, ablations, new stimuli) predicted with no refit, within real animal-to-animal spread. Exact recovery of each parameter is NOT required (biological models are "sloppy" and real circuits are degenerate: Gutenkunst/Sethna; Marder). The "it IS feeling" bar: internal states carried by the same cells and molecules, with the same causes, driving the same behaviour under perturbation.

## The method: five moves
1. **Build every mechanism first, then fit real data with a synthetic-twin control (Ben, revised 5 Nov).** Complete before search: the template worm has every mechanism layer, every unknown bounded and labelled in the ledger. Then each real circuit fit is paired with a **synthetic twin**: a worm with random known parameters filling the same mechanisms, fitted by the same pipeline on data of exactly the same shapes (same neurons observed, same stimuli, same sampling and GCaMP-style noise, same animal counts). If the pipeline cannot recover the twin's held-out behaviour and its stiff parameter combinations, the real fit is not trusted. This is a must-pass control, the mirror of the must-fail controls, run alongside the real fits (about 2x compute), not before them. It also yields the identifiability map and the precision-needed column. Scale: one well-measured circuit first (locomotion or Randi's head circuit), then the whole worm. Pass: held-out predictions within the twin population's spread (>= 80%) plus recovery of the stiff combinations; sloppy single parameters are reported, not required. **The full information-sufficiency study (how much scan data recovers an individual) stays where Ben placed it: after a real worm is reconstructed behaviourally.**
2. **Fewer free numbers, from biology's own rules.**
   - Channel densities from one shared, hierarchical **expression-to-physiology map** (gene family > terminal-selector battery > class), fitted on recorded neurons and tested on held-out recorded neurons (`research/GENES_TO_PHYSIOLOGY.md`).
   - **Homeostatic self-tuning**: activity-dependent rules set densities from a few targets, possibly run as a developmental process over the invariant lineage.
   - Peptides by gene family (`research/NEUROPEPTIDES.md`).
3. **Mechanisms first, then reduce (replaces "coarse to fine", after the Astra review).** An effective coupling can absorb excitability, filtering, hidden relays and feedback, and mechanism replacement has no fit-preservation guarantee. So every mechanism is built in full and carries NESTED simpler forms whose limits are explicit (fast gates instantaneous, receptor kinetics at equilibrium occupancy, poorly resolved conductances as their identifiable combination; Transtrum and Qiu 2014). These are the registry toggles, each with the fly's neutral-equivalence test. Refinement refits intrinsic, coupling and observation parameters jointly, across amplitudes, durations, initial states and interventions.
4. **Circuit by circuit, closed loop with the body.** Locomotion (AVA/AVB, motor cord), touch avoidance, chemotaxis (ASE, AWC, AIY), roaming/dwelling (serotonin, PDF). Each passes held-out tests before the next joins.
5. **Judge only on perturbations** (`SCOREBOARD.md`): unc-31, tph-1, cat-2, tdc-1, eat-4, unc-7/unc-9, ablations, plus the genome-wide perturbation corpus (`research/PERTURBATION_CORPUS.md`). Every test names a deliberately wrong model that must fail it.

## Convergence (Ben's intuition, made testable)
Each independent constraint (genome and expression, terminal-selector code, lineage and development, homeostasis, energetics, wiring, the functional atlas, whole-brain activity, behaviour, thousands of genetic perturbations) cuts the set of possible worms. With enough of them the inverse problem becomes well posed and the fit converges on what biology found. The recovery test measures whether, and where, that point is reached.

## When a layer cannot be pinned down (Ben)
Keep the alternative worms that differ there, show which behaviours depend on it, and write the exact experiment a lab would need (a worm MEASUREMENT_LIST, as for the fly).

## Untapped data sources to bring in
Genome-wide perturbation phenotypes (WormBase, screens, natural isolates); the terminal-selector code (Hobert lab); homologue and AlphaFold priors for unrecorded channels; related nematodes (Pristionchus, C. briggsae); the invariant lineage plus embryonic single-cell expression; peptidomics.

## The ledger format (Ben)
The fly's format (`docs/CONSTRUCTION.md` "The data model"; `docs/BLANKS_AUDIT.md`): one row per unknown with bio_min/bio_max, prior, label, source, owning mechanism and grain; slots counted per grain; plus a **precision-needed** column from the recovery test and sensitivity analysis. Shown in a browser.

## Speed bars (Ben)
Full model including a 3D body: never slower than 100x real time (hard cap). Fitting configuration: under 10x. Measured 5 Nov: whole-worm-sized network at 4 compartments 2.4x on one core. MetaWorm's 3D body (~1x real time as reported) is the lead 3D candidate.

## Changes from the Astra review (5 Nov; full text `research/ASTRA_REVIEW_2026-11-05.md`)
- **The measurement is part of the model.** Indicator kinetics (GCaMP), optogenetic stimulation strength and the preparation (immobilised for Randi 2023, freely moving for Atanas 2023) are explicit, fitted, condition-labelled parts of the model, never absorbed into physiology.
- **Disagreement search** is the core identifiability tool and the source of the precision-needed column: search for two admissible worms that fit all training data but disagree most on a target intervention; the parameters they differ on, and by how much, are what that prediction needs. Profile likelihoods and multistart fits back it up; local sensitivity is triage only.
- **Interventions are defined mechanistically**, per gene, with timing (acute vs chronic, developmental compensation): e.g. unc-7 is not "remove gap junctions" (it also forms mechanosensory hemichannels). Phenotype databases are used to find experiments, not as a uniform likelihood.
- **Opponents are plausible, refitted alternatives**, not hand-picked bad models; a **locked holdout** is never looked at during design.
- **Expression and homeostasis are priors, not measurements.** CeNGEN is L4, not adult, with documented threshold and dissociation artefacts. The expression map's held-out test leaves out whole neuron classes. Homeostatic tuning stays a toggle and a hypothesis.
- **Synthetic twins come as populations and from structurally different generators** (alternative kinetics, compartments, peptide transport, hidden feedback), so shared-assumption bias is tested, not assumed away.
- **Body:** passive mechanics and muscle responses are constrained separately before any behavioural fit; a 3D rod with validated low-Reynolds drag is the first physics body; a full 3D/fluid body must show a scientific benefit for its cost.
- **Benchmarks now, not later:** fitting throughput (gradient steps per hour), gradient memory, long-horizon stability, coupled brain-body speed.
- Astra's suggested narrow first milestone (an identifiability study of dense-core-vesicle-dependent propagation, unc-31 vs wild type) is kept as a parallel science track once the template exists; Ben's order (build the full worm and see it) stands.
