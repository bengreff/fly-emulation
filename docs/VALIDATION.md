# Evidence, fitting and validation

## Evidence ledger

Each model quantity or shared parameter group needs a machine-readable record. Start with a simple format, not a database project. Fields should include:

| Field | Required content |
|---|---|
| Identity | Quantity, biological cell/type/component, source specimen IDs and model IDs |
| Provenance | Paper/dataset URL or DOI, version, file, relevant figure/table/protocol, license |
| Evidence category | Direct observation; derived measurement; fitted parameter; cross-cell/specimen inference; assumption; unresolved |
| Conditions | Species, sex, genotype, age/stage, temperature, preparation, stimulus and state where known |
| Representation | Units, coordinate system, equation/observation model, sampling and alignment |
| Uncertainty | Bounds/distribution, uncertainty type, dependencies/covariance, plausible alternatives |
| Model assignment | Transformation, parameter-sharing rule, limitations and evidence supporting transfer |
| Evaluation use | Training, model selection or final test; whether the value changed after viewing behavior |

“Derived” does not mean exact. A precisely measured fluorescence trace can weakly constrain spike timing. One shared measured value assigned to thousands of cells is not thousands of independent measurements. Track uncertain anatomical matches and competing studies rather than hiding them in comments.

## Measurement consistency

Use explicit observation models and uncertainty-aware losses. Distinguish anatomical contact count, functional efficacy, expression and causal influence. Reconcile contradictory studies by preparation and biological variability before concluding one is wrong. A model should explain a coherent set of conditions; it need not equal incompatible population averages simultaneously.

Record calibration information already embedded in imported components. A pretrained body or visual model may have used some of the intended test data. Treat that as prior exposure. Citation alone is not independence.

## Evaluation split

Partition by animal and recording/session when possible, then reserve entire stimulus regimes or perturbations. Avoid adjacent video frames crossing the split as if they were independent evidence. Maintain separate component, integration and final holdouts.

Because agents can access the entire public literature, do not claim perfect blindness by default. Record prior knowledge. Where feasible, have an independent evaluator own the final manifest and run it after a model freeze. If results drive revisions, they become development evidence and stronger claims need fresh evaluation.

## Progressive assay matrix

| Domain | Fit/characterize | Withheld validation |
|---|---|---|
| Cell and synapse | Current/voltage response, adaptation, kinetics and transmission | New stimulation patterns, response statistics and timing |
| Isolated muscle/body | Force, passive mechanics, recruitment and geometry | Loads/activation regimes not used in fitting |
| Proprioceptive loop | Sensory response to joint motion/strain | Perturbation recovery and afferent ablations |
| Walking | Support, initiation, displacement, turning, foot contact and kinematics | Different conditions plus specific circuit perturbations |
| Flight | Muscle/hinge and aerodynamic response, steering and stability | Disturbances, sensory removal and motor-pathway interventions |
| Transitions | Takeoff, landing and coordinated behavior switching | New stimulus timing and mechanical conditions |
| Learning | Acquisition, timing and retention of supported associations | New associations learned without outer optimization; extinction/reversal where supported |
| State dependence | Adaptation and state-conditioned response differences | Cross-condition predictions and mechanistic interventions |
| Individuality | Stable traits and experience-dependent variation | Repeated/cross-context consistency; donor-specific tests only with suitable evidence |

Choose quantitative tolerances from independent assay variability when possible. State exactly which behavior, preparation and time horizon were tested. Use neural observables and intervention effects in addition to movement. A visual demo is a communication artifact, not the primary metric.

## Controls that matter

- Test the effect of removing the modeled sensory feedback and of intervening on anatomically relevant pathways.
- Compare anatomical wiring to carefully matched alternatives when asking whether the graph matters. Preserve relevant degree/weight distributions; do not use an obviously crippled control.
- Keep an optional independent-physiology-only baseline to measure the added value of behavioral fitting. This baseline is not a restriction on the main model.
- Distinguish frozen efficacy from enabled lifetime learning, and learned individuality from fixed parameter differences.
- Evaluate multiple admissible fitted candidates to reveal non-identifiability and sensitivity to priors.
- Label any scaffold control, imposed stimulation or externally supplied wing rhythm in the run metadata and figures.

## Numerical verification

Prioritize tests for anatomical ID joins, units, coordinate transformations, signs, delays, causality and reproducible checkpoint continuation. Compare small numerical cases against a trusted implementation. Check step-size and precision convergence on scientific readouts. Gradients should be checked on small smooth cases before large fitting jobs.

Track physics consistency and stability separately from biological fit. Contact models can dissipate energy; neural/muscle models consume energy. Do not impose inappropriate mechanical conservation on the powered organism. Do investigate unphysical energy sources, explosive states and simulator artifacts.

## Experiment record

Every substantial run should retain code commit, environment/dependency lock, data hashes, model and parameter versions, priors, fitted/free/fixed groups, RNG state, stimulus/initialization protocol, losses and individual metrics, wall/simulated time, peak RAM/VRAM and outputs. Save failures as well as successes. A short conclusion should state what was learned and the next discriminating test.

Checkpoint all state needed for continuation, including plasticity, dynamic connectivity, delays/event queues, body state and RNG where applicable. Do not optimize a private initial state for every target episode and then describe the outcome as autonomous.

## Synthetic-scan extension

Freeze a reference model and its state. Reveal different information subsets and precision levels. Reconstruct repeatedly using distinct assumptions/algorithms and compare on hidden reference behavior and memory. Include different reference model families to probe inverse-crime bias. Common success under a common behavioral training target is not proof the scan supplied that behavior.

Report storage bytes separately from independent measured information. An executable checkpoint can contain many redundant/shared values; counting populated fields does not measure identity recovery.
