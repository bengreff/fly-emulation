1. **A — The stated inverse problem is not well posed with existing data.**

You can identify some response functions and parameter combinations. You cannot currently establish that the fitted organism occupies the biological parameter region, particularly for molecular state storage. **Biologically bounded parameters do not establish biological correctness.** Matching NEURON verifies implementation; the AIY fit demonstrates predictive voltage fitting under the tested protocols, not recovery of its conductances.

Identifiability will fail first at the measurement–mechanism interface: optical stimulation strength, membrane excitability, calcium handling, indicator kinetics, and recurrent input can compensate for one another. Peptide release, extracellular clearance, receptor abundance, and downstream amplification introduce further tradeoffs. For example, without calibrated injected current, scaling capacitance, conductances, and input amplitude together can preserve voltage dynamics.

[Randi et al. (2023)](https://www.nature.com/articles/s41586-023-06683-4) measure **network signal propagation**, including indirect and extrasynaptic routes—not individual synaptic transfer functions. Their measurements use immobilized, genetically instrumented animals. [Atanas et al. (2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10836760/) measure activity and behavior in moving animals. Treating these as observations of one stationary parameter vector risks fitting preparation differences as physiology.

Your recovery test is necessary but insufficient. Change it as follows:

- Reproduce actual sampling, missing neurons, animal counts, stimulus protocols, indicator dynamics, and preparation differences—not merely “data of the same kinds.”
- Generate populations, including correlated biological variation, rather than one synthetic worm.
- Use structurally different generators: alternative channel kinetics, compartmentalization, peptide transport, hidden feedback, and developmental compensation. NEURON versus Jaxley with identical equations tests software, not shared-assumption bias.
- Search explicitly for **two admissible models that fit all training data but maximally disagree on a target intervention**. Finding such a pair disproves identification of that prediction; failing to find one does not prove identification.

Measure coverage, prior sensitivity, identifiable combinations, and intervention uncertainty. Local sensitivity spectra are useful triage, but supplement them with profile likelihoods and multistart searches; sloppiness is not equivalent to nonidentifiability. See [Raue et al. (2009)](https://pubmed.ncbi.nlm.nih.gov/19505944/).

“Within animal variability” also needs a statistical definition: held-out animals, matched conditions, predictive calibration **and sharpness**, and comparison against empirical repeatability. Otherwise broad predictions pass trivially.

2. **B — Coarse-to-fine is useful initialization, but mechanism replacement has no fit-preservation guarantee.**

An effective coupling can absorb presynaptic excitability, postsynaptic filtering, hidden relays, feedback, and calcium dynamics. Several apparent edges may encode the same omitted process. Replacing them independently can double-count that process or destroy the network dynamics.

Even locally, an observed transfer function has the form \(H(s)=C(sI-A)^{-1}B\). Its factorization into input drive, network dynamics, and observation dynamics need not be unique. Anatomical constraints help; they do not automatically resolve this ambiguity.

“One bounded coupling per real link” therefore provides less interpretability than it appears to. Peptide–receptor expression establishes a possible interaction, not an active edge with known sign, strength, or operating regime.

Instead, **start with mechanisms and reduce them**. Construct nested mechanistic families whose simplified limits are explicit: fast gates become instantaneous; receptor kinetics become equilibrium occupancy where justified; poorly resolved conductances become identifiable combinations. [Transtrum and Qiu (2014)](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.113.098701) provide a relevant reduction framework.

During refinement, jointly refit intrinsic, coupling, and observation parameters. Require agreement across stimulus amplitudes, durations, initial states, and interventions—not just one impulse response. Treat failed refinement as evidence that the effective fit lacks a realization within your proposed mechanisms.

Circuit-by-circuit integration has the same problem: modules share neurons, modulators, mechanics, and feedback. Their boundary conditions must be identified and tested explicitly.

3. **C — Expression and homeostasis are priors and hypotheses, not missing measurements.**

The foundational [CeNGEN dataset, Taylor et al. (2021)](https://www.cengen.org/l4/), profiles L4 animals, not your target adult condition. Its documentation explicitly identifies expression-threshold errors, transgene-related overexpression, and dissociation-associated stress. Transcript counts do not uniquely determine membrane protein abundance, localization, subunit assembly, phosphorylation, or functional conductance.

Terminal-selector batteries justify structured sharing of information. They do not establish a universal quantitative map from expression to density. Use uncertain channel-presence probabilities and hierarchical density priors with cell-specific deviations. Validate by leaving out entire neuron classes; interpolation among closely related recorded cells is an easier test.

[Bernaerts et al. (2025)](https://doi.org/10.1016/j.patter.2025.101323) used paired mouse Patch-seq measurements, biophysical inference, and sparse regression. The transferable precedent is the methodology. Neither fitted coefficients nor the adequacy of the mouse model transfers to worm neurons. Your sparse, largely unpaired expression/ephys data remove a central advantage of that study.

[O’Leary et al. (2014)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4109293/) demonstrate a possible regulatory mechanism, not an established worm-wide developmental rule. Graded signaling does not invalidate calcium-based regulation, but setpoints, sensing variables, regulation rates, and targets become additional unknowns. Homeostasis can also restore average calcium while producing pathological physiology.

Invariant lineage supplies cell identity, not developmental dynamics. Defer developmental simulation until adult adaptation measurements constrain it.

Finally, [Beets et al. (2023)](https://pubmed.ncbi.nlm.nih.gov/37656621/) identify 461 peptide–GPCR pairs through reverse pharmacology. Those are not 461 calibrated in-vivo signaling mechanisms. Gene-family pooling should be soft: processing, release, receptor coupling, and clearance can differ substantially.

4. **D — The three most likely failures are causal ambiguity, invalid intervention semantics, and integration without constraint.**

**First: observational success with the wrong molecular explanation.** Hunger, sleep, and learning cannot be validated merely by naming latent variables after molecules. You need cell-specific necessity, sufficiency, rescue, and temporal recovery predictions. Maintain competing mechanistic families and design experiments where their predictions separate: paired pulses, multiple amplitudes, simultaneous voltage/calcium measurements, and acute release or receptor perturbations. Optimize information about competing mechanisms, not just parameter precision; [Liepe et al. (2013)](https://doi.org/10.1371/journal.pcbi.1002888) provide a Bayesian experimental-design precedent.

SBI can quantify uncertainty, but cannot create information. If your prohibition covers learned inference networks as well as simulator dynamics, use sequential Monte Carlo/ABC or explicit likelihood methods. Bayesian model reduction remains conditional on the candidate family and priors.

**Second: treating mutations as clean parameter deletions.** Chronic mutants can change development, compensation, metabolism, and baseline state. An `unc-7` mutation is particularly unsuitable as “remove electrical edges”: UNC-7 also has mechanosensory hemichannel functions ([Walker and Schafer, 2020](https://pubmed.ncbi.nlm.nih.gov/31995033/)). Define each intervention mechanistically, including its timing. Prioritize matched acute/chronic perturbations, cell-specific rescue, and quantitative recordings. Use WormBase phenotype annotations to discover experiments; do not treat heterogeneous phenotype labels as a uniform likelihood.

Replace “one deliberately wrong model must fail” with several **plausible, refitted alternatives**. A handpicked bad model is an easy opponent. Keep a final lockbox: repeatedly redesigning models against a nominal holdout turns it into training data.

**Third: integration consumes the budget while unconstrained organs and mechanics absorb errors.** Muscle force, body stiffness, drag, and proprioceptive gain can trade off. Constrain passive mechanics and muscle responses separately before fitting behavior.

Your neural forward benchmark does not establish fitting throughput, gradient memory, long-horizon stability, or coupled-body speed. Benchmark those immediately. A 3D rod with validated low-Reynolds-number hydrodynamics is a reasonable initial body approximation; full fluid simulation needs an demonstrated scientific benefit.

5. **E — A realistic 4–8-week milestone is an intervention-identifiability study, not a whole-worm emulation.**

Target one well-sampled signaling question: **which aspects of dense-core-vesicle-dependent propagation can existing measurements distinguish from recurrent wired pathways and altered cellular gain?** Randi already established the broad contribution of extrasynaptic signaling; reproducing that finding is insufficient novelty.

- **Weeks 1–2:** Extract trial-level data for a small module selected using training-data coverage. Specify boundary inputs, observation dynamics, biological bounds, and splits by animal and intervention. Benchmark complete fitting steps.
- **Weeks 3–4:** Fit several bounded mechanistic families. Run matched-family and mismatched-family recovery tests. Construct equally fitting models with maximally divergent intervention predictions.
- **Weeks 5–6:** Freeze models and evaluate reserved mutant responses without genotype-specific refitting. Report which conclusions survive uncertainty in indicators, stimulation, and boundary inputs.
- **Weeks 7–8:** Identify the cheapest feasible experiment that separates surviving explanations; release data processing, fitted ensembles, and a reproducible benchmark.

The potential new science is a **specific demonstrated ambiguity or robust mechanistic prediction, plus a quantitatively justified experiment that resolves the ambiguity**. A negative identification result is valuable if it names the competing mechanisms and the missing measurement.

Keep a minimal 3D-body speed test as a separate engineering deliverable. Making embodiment a prerequisite for this first scientific result would add cost without resolving its central uncertainty.