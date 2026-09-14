# Model and inference architecture

This is a proposed design, not a tested implementation. Choose numerical detail through component evidence and benchmark results.

## State and modules

Represent the organism using anatomy G, biological parameters theta, dynamic state x, and an environment. With structural plasticity, G can itself evolve under specified mechanisms. State includes membrane/channel variables, synaptic resources, modulators, learned changes, muscle activation and body pose/velocity. A fixed random seed makes stochastic implementations reproducible; biological noise should not be removed merely to make trajectories deterministic.

| Module | Inputs | State/output | Evidence needed |
|---|---|---|---|
| Receptors | Light, odor concentration, local strain, joint motion, contact, other supported stimuli | Receptor voltage/spikes and adaptation | Receptor identities, geometry, causal response measurements |
| CNS | Sensory input, recurrent neural signals, modulatory input | Voltage, spikes/graded release, channel/adaptation states | Connectivity, physiology, receptor/sign evidence, delays |
| Synapses/modulation | Presynaptic activity, postsynaptic state, relevant modulators | Conductances, short-term resources, persistent changes | Release/receptor dynamics and plasticity measurements |
| Neuromuscular system | Identified motor-neuron signals | Muscle activation and force | MN-to-muscle identities and measured dynamics |
| Body/environment | Muscle forces and external loads | Pose, velocity, strain, contacts, sensory scene | Morphology, mechanics, aerodynamics and environment models |
| Slow internal state | Relevant physiological inputs/history | State-dependent effects on the above | Evidence for the modeled hunger/arousal/circadian/etc. mechanisms |

Every interface needs units, coordinate conventions, timing, anatomical identity, uncertainty and operating range. A low-dimensional interface is acceptable when it is an evidence-supported reduction of a biological component. A DN-to-“walk” decoder substituting for unmodeled motor circuitry is a scaffold, not the main scientific model.

## Neural detail

Begin with reduced conductance-based models or justified graded/spiking formulations. Use Shiu/Pugliese models as reproduction references, not universal physiology. Increase detail for specific failed physiological tests: dendritic compartments, channel dynamics, receptor kinetics, electrical coupling or modulation. Support histaminergic visual transmission explicitly where relevant; a six-class transmitter table is not a complete synaptic model.

Do not equate anatomical contact count with exact functional weight. A useful initialization is a contact-count-dependent prior with transmitter/receptor and cell-type structure. The fitted mapping and deviations need evidence and regularization.

Import chemical and electrical connectivity separately. Record unobserved versus observed-absent connections. Keep original dataset IDs as exact integers/strings and maintain stable internal identities. Do not infer conservation merely from matching names.

## Fitting methods

The objective combines physiological observations, behavioral observations and priors, with trusted constraints enforced explicitly. Store separate loss components; a good total can hide catastrophic failure of one modality.

| Method | Intended use | Limitation |
|---|---|---|
| JAX/Jaxley automatic differentiation with Adam; optional L-BFGS refinement | Cell and circuit parameter fitting; appropriate differentiable portions of the coupled model | Memory, stiffness, nonconvexity, recurrent credit assignment and contact discontinuities |
| Multiple shooting with continuity constraints | Estimate latent states in short observation windows and shared dynamics, then enforce consistent continuation | Independent window initial states must not become hidden assistance in final rollouts |
| CMA-ES or related evolutionary fitting | Modest-dimensional nonsmooth parameter groups or alternative component hypotheses | Poor fit for brute-force search over millions of unrelated synapses |
| Block-coordinate and curriculum fitting | Fit components, alternate unresolved parameter blocks, then jointly reconcile and lengthen trials | Local fits can become incompatible in the closed loop |
| HMC/NUTS on tractable differentiable subsystems | Explore data-compatible parameter uncertainty | Not proposed as a full-brain million-dimensional posterior solution |
| Sequential neural posterior estimation via sbi | Reduced parameter groups with expensive or likelihood-free observations | Requires many simulations and careful posterior checks; no automatic whole-organism solution |
| Sensitivity/Jacobian analysis; expected information gain | Find influential ambiguities and discriminating existing/synthetic tests | Local sensitivity is not global identifiability |

Start with the smallest method that answers the current inference question. Compare a few scientifically distinct model families, not thousands of arbitrary mechanisms. Hierarchical parameter sharing can shrink the search but is itself an assumption. Allow cell-specific deviations when justified.

Use explicit observation models: a calcium trace is not voltage or a spike train; fluorescence delay and filtering affect inference. Fit measurement noise and preparation effects where necessary. Compare spontaneous behavior using appropriate distributions and temporal structure; require aligned timing for controlled perturbation trials. Do not let time-warped fits conceal incorrect latency.

## Learning

Introduce plasticity based on the circuit and experimental evidence, not a universal reward rule applied everywhere. Fit its timing, sign, dependence on modulators and retention against actual protocols. The biological learning mechanism operates during the lifetime; the outer optimizer is absent during held-out learning evaluation. Save both transient and long-lived states in checkpoints.

Initially use published circuit physiology to choose candidate learning mechanisms. Explicitly model the sensory routes for reward/punishment. Artificially stimulating identified modulatory neurons can reproduce an experimental intervention, but is not equivalent to natural sensory transduction.

## Flight implementation

Inspect flybody assets and current FlyGym muscle/sensory components before selecting one final body. Keep walking as milestone one but audit flight early. The power-muscle/thorax oscillator, steering hinge, aerodynamic forces and fast mechanosensory feedback are separate coupled components.

Distinguish replayed-wing debugging, supported airborne steering, autonomous stabilization, and takeoff/landing. Prescribing wing frequency or supplying stabilization is allowed for isolated tests but must be disclosed and removed for stronger claims. A myogenic oscillator derived from muscle/thorax biology is legitimate; it is not a neural policy.

The Melis wing-hinge CNN requires a causal audit before live use (see RESEARCH.md). Its retrospective calcium window must not give the simulator access to future activity. Refit causal dynamics or a justified latent activation/measurement model, and quantify the unresolved spike-phase information.

## Numerical and resource plan

Inspect GPU memory, RAM, disk, driver and backend compatibility. Use Windows/WSL2 or another supported NVIDIA environment if warranted; Mac is useful for orchestration and small CPU work. Do not assume a package works on a given OS without checking its current documentation.

Benchmark import, neural forward simulation, gradients, mechanics, rendering and synchronization separately and together. Forward memory fit is not gradient memory fit. Checkpointing and multirate integration may help, but fast pathways and causality must be preserved. Test step-size convergence against physical readouts. For scale, a 0.1 ms interval corresponds to 7.2 degrees at an illustrative 200 Hz wingbeat.

Avoid raw-EM download initially. Fetch metadata and relevant physiology subsets first. Keep raw data outside git, with checksums, versions and licenses. Render sparse diagnostics, not full videos for every candidate. Do not schedule dozens of full-graph jobs simultaneously on one consumer GPU.

No fixed architecture promises 1–10 GB or real-time operation at the required fidelity. Measure candidate costs and select scientifically defensible reductions before optimizing kernels.
