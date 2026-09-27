# Minimum neural and sensory-transduction fidelity per target behaviour (session 9 research note)

Question: assume every parameter could be measured. What is the least neural and sensory-transduction detail needed to reproduce each Tier 1–2 behaviour, and what evidence supports that level? The answer decides how many physical mechanisms to build.

**Evidence labels in this note:**
- **[verified]**: I read the source's methods or full text in this session.
- **[abstract]**: I read only the abstract or publisher summary in this session.
- **[unverified]**: from prior knowledge, not re-checked here. Check it before relying on it.

"Sufficient" means a computational study reproduced the phenomenon at that level of abstraction. "Necessary" means an experiment showed the mechanism is required. Neither kind of evidence covers our full closed loop. This note gives reasoned recommendations, not results.

---

## 0. Five conclusions first

1. **Point neurons are enough wherever the connectome carries the computation, but only if each cell class has its own biophysical parameters.** Three connectome models reached behaviour-level or activity-level agreement with point neurons and no dendrites:
   - Lappalainen 2024: a graded, passive optic lobe with 734 fitted parameters reproduced direction selectivity and ON/OFF channels.
   - Shiu 2024: a uniform LIF model got 91 % of 164 feeding and grooming predictions right.
   - Pugliese 2025: a rate model of the VNC produced a walking rhythm.

   Each of them fitted or chose per-class resting potential, time constant or gain, or unitary strength. Our uniform efficacy with borrowed V_rest and V_th is below that level.
2. **Graded (non-spiking) transmission is a first-class requirement, not an option.**
   - The optic lobe front end is graded.
   - Pugliese chose a rate model because insect premotor interneurons that are active during walking are non-spiking.
   - Arthropod sensorimotor loops rely on graded premotor interneurons (Burrows; the antennal APN2 cell, Nunn et al. 2026).

   A noise-free LIF with cells sitting exactly at rest cannot carry a small graded signal. That fits our silent-relay diagnosis.
3. **Dendritic compartments are needed in only a few places**, and a point-neuron equivalent can often stand in:
   - T4/T5 multiplication through shunting (conductance-based) synapses;
   - APL's local inhibition in the mushroom body;
   - LPTC (lobula plate tangential cell) dendritic integration and gap-junction coupling.

   No evidence found says walking, posture, feeding or grooming need multi-compartment neurons.
4. **Flight is the one behaviour that sets hard timing and electrical-synapse requirements.**
   - Steering motor neurons fire one phase-locked spike per wingbeat (~4.5 ms cycle).
   - The phase of that spike is set by haltere and wing afferents through fast electrical plus chemical synapses (Calliphora).
   - Escape uses the gap-junctional giant fibre (GF) system.

   The model needs spiking at sub-millisecond precision, a 0.1 ms or finer step, gap junctions at identified sites, and phase-resolved mechanosensory transduction.
5. **Internal state and learning cannot be reproduced from the synaptic connectome at any neural fidelity.** They need things that EM does not show:
   - GPCR neuromodulation (volume transmission) and neuropeptides/hormones. C. elegans shows that extrasynaptic signalling breaks connectome predictions (Randi 2023).
   - Plasticity with explicit timing rules (Handler 2019; Aso & Rubin 2016).
   - Slow state variables: sleep pressure, satiety, the circadian phase.

   These can be phenomenological. Their receptor maps and time constants matter more than their biochemistry.

---

## 1. Summary table

"Ours" is the current model (docs/MODEL.md, docs/HANDOFF.md, end of session 8).

| Mechanism | Minimal level required | Behaviours that need it | Key evidence | Ours now |
|---|---|---|---|---|
| **Neuron dynamics: spiking vs rate** | Point neuron with both modes by cell class: LIF (or rate with a threshold) for spiking classes, graded leaky integrator for non-spiking classes. Hodgkin–Huxley is not needed for behaviour-level output. | All | Sufficient: Shiu 2024 LIF, sensorimotor feeding and grooming, 91 % of 164 predictions ([bioRxiv](https://www.biorxiv.org/content/10.1101/2023.05.02.539144v1.full)) [verified]. Lappalainen 2024 graded optic lobe ([Nature](https://www.nature.com/articles/s41586-024-07939-3); [preprint](https://www.biorxiv.org/content/10.1101/2023.03.11.532232v1.full)) [verified]. Pugliese 2025 VNC rate model ([bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.12.675944v1)) [verified] | LIF per type; graded only for photoreceptors, L1–L3 and APL |
| **Which cells are non-spiking** | Graded mode for R1–8, LMCs (L1–L5), probably most Mi/Tm/Dm input cells, AL local neurons (some), APL, and an unknown share of VNC local premotor interneurons. Decide per class. | Vision (all), walking, posture, reflexes, antennal control | Lappalainen used non-spiking cells for the optic-lobe front end [verified]. Pugliese: "some neurons in the insect VNC, including premotor neurons active during walking, are nonspiking" [verified]. APN2 non-spiking ([Nunn 2026](https://www.biorxiv.org/content/10.64898/2026.04.16.718965v1)) [abstract]. Locust/cockroach non-spiking local INs: Burrows; Pearson & Fourtner 1975 ([J Neurophysiol](https://journals.physiology.org/doi/abs/10.1152/jn.1975.38.1.33)) [abstract]. Para (Na<sub>V</sub>) is broadly expressed in the adult CNS at distal spike-initiation zones ([J Neurosci 2020](https://www.jneurosci.org/content/40/42/7999)) [abstract], so "spiking" is the default. Whether Mi1/Tm3 spike is contested [unverified] | Graded for few types; VNC fully LIF |
| **Per-class intrinsic parameters** (V_rest, τm, threshold gap, gain) | Per class, fitted or measured; spontaneous/background rate per class | All; critical for relays and rings | Lappalainen fitted 65 V_rest and 65 τ [verified]. Pugliese drew τ ~ N(20 ms, 2 ms) with gain and threshold per neuron [verified]. Shiu's uniform parameters work only for strong feed-forward sensorimotor chains, and note that "inhibitory connections to an inactive neuron have no effect" with 0 Hz baseline [verified] | Borrowed uniform (−52/−45 mV); slow MNs fitted; no background |
| **Spike-frequency adaptation / A-type K** | Phenomenological adaptation current per class; no explicit channels | Walking rhythm (optional), CX bump stability, ORN→PN transients, flight saccade timing | Pugliese: rhythm with no intrinsic adaptation ("no neuron had intrinsic bursting or other longer-timescale membrane properties") [verified]. So walking does not need it. Our s8 ring bump appeared only with adaptation (F-CX-3, internal) | Option, off |
| **Plateau / bursting / pacemaking** | Needed only for identified slow systems: clock neurons (Na leak / K bicycle), R5 slow waves (NMDA), MN rhythmic tonic firing | Sleep, circadian, arousal | Flourakis 2015 ([Cell](https://pubmed.ncbi.nlm.nih.gov/26276633)) [abstract]. Raccuglia 2019: R5 compound slow-wave oscillations need NMDAR coincidence detection, and sleep is disrupted without it ([Curr Biol](https://pubmed.ncbi.nlm.nih.gov/31630955/)) [abstract] | Absent |
| **Multi-compartment dendrites** | Point neurons, except: (a) T4/T5 either as a conductance-based point neuron with shunting, or as a fitted threshold-linear point neuron; (b) APL as a local, many-compartment inhibitor; (c) LPTC dendrites (optional); (d) PN spike initiation distal to the soma (point OK) | Optomotor and looming (T4/T5 → LPTC, LPLC2); olfactory learning specificity (APL) | Necessary biophysics: Groschner 2022, passive supralinear interaction of excitation and release from glutamatergic inhibition on the T4 dendrite ([Nature](https://www.nature.com/articles/s41586-022-04428-3)) [abstract]. Gruntman 2018 T5 ([Nat Neurosci](https://www.nature.com/articles/s41593-018-0098-3)) [unverified]. But Lappalainen's point neurons gave direction selectivity (three alternative T4 solutions in the ensemble) [verified]. PNs are electrotonically extensive, spikes start in the proximal axon, and a single-branch input cannot match a unitary EPSP ([Gouwens & Wilson 2009](https://www.jneurosci.org/content/29/19/6239)) [abstract]. APL local inhibition: Amin et al. 2020 [unverified] | None; APL graded point |
| **Synapse: current- vs conductance-based** | Current-based is adequate for most excitatory paths. Shunting (conductance) inhibition is needed where division or multiplication is the computation (T4/T5, possibly AL gain control) | Motion vision, looming, olfactory gain control | Groschner 2022 [abstract]. Lappalainen got by with a threshold-linear transfer instead [verified] | Option, off |
| **Sign and receptor identity** (nAChR +, GABA-A −, GluCl − vs iGluR +, histamine Cl⁻) | Per postsynaptic type. It cannot be inferred from wiring. | All | Our F-RCPT-1: leave-one-type-out prediction at chance (internal). Lappalainen took sign from transmitter [verified]. Shiu admits monoaminergic cells are handled poorly [verified] | consensusNt + 51–54 transcript rows |
| **Receptor kinetics** (fast nAChR/GABA-A ~ms; GABA-B/mGluR/GPCR 100 ms–s; NMDA) | Two time constants per class (fast, slow) suffice; NMDA voltage dependence only in the ring/R-neuron system | AL temporal coding, CX persistence, sleep | GABA-B presynaptic inhibition of ORNs (Olsen & Wilson 2008) [unverified]. NMDA in R5 (Raccuglia 2019) [abstract] | Single τs 5 ms; GABA-B share option off |
| **Short-term plasticity** | Depression at sensory first synapses (ORN→PN, probably proprioceptor→IN, photoreceptor→LMC); phenomenological Tsodyks–Markram | Odour tracking in plumes, reflex gain, visual adaptation | ORN→PN depression (Kazama & Wilson 2008) [unverified]. Our s7 depression options (internal) | Options, off |
| **Release probability / stochasticity** | Not needed deterministically; needed as a noise source for variability, bump diffusion and exploration | CX drift, behavioural variability, sleep/wake | Noorman 2024: small rings can be continuous but are "sensitive to noise and variations in tuning" ([Nat Neurosci](https://www.nature.com/articles/s41593-024-01766-5)) [abstract] | Noise-free |
| **Presynaptic (axo-axonic) inhibition** | Gain term on afferent terminals: GABA-B on ORNs; GABAergic onto proprioceptor terminals in the VNC | Olfactory gain control; reflex gating during active movement | Olsen & Wilson 2008 [unverified]. VNC proprioceptor terminals receive many axo-axonic synapses in FANC/MANC [unverified] | Option, off; chemical input onto sensory terminals removed (m1 rule) |
| **Gap junctions** | At an identified list only: GF→TTMn/PSI, JO→GF, eLN–PN (AL), LPTC HS/VS coupling, haltere/wing afferent→steering MN. Rectifying where known | Escape takeoff, flight steering, looming, optomotor (LPTC), olfaction | Electrical synapses dominate the Drosophila giant-fibre system; ShakB is heterotypic and rectifying; age-related latency rise is tied to smaller ShakB plaques ([computational model, eNeuro 2019](https://www.eneuro.org/content/6/2/ENEURO.0423-18.2019); [Pézier 2016 PLoS One](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0152211)) [abstract]. Blowfly steering MN: afferent inputs have "fast electrical and slow Ca²⁺-sensitive components" ([Fayyazuddin & Dickinson 1996](https://www.jneurosci.org/content/16/16/5225.long); [1999](https://pubmed.ncbi.nlm.nih.gov/10515981/)) [abstract]. Not in EM: Shiu "cannot identify" them [verified] | GF only, off |
| **Axonal delays** | Per-type conduction delay; sub-ms precision only for flight and escape | Flight, escape, fast reflexes | Sensorimotor delays constrain walking robustness ([eLife RP 99005](https://elifesciences.org/reviewed-preprints/99005v2)) [unverified content] | Present (morphological) |
| **Neuromodulation (DA, OA, 5-HT, TA), volume transmission, GPCR** | Pools with per-type receptor sensitivity and s–min kinetics, acting on gain, threshold and plasticity | Arousal and flight-state visual gain, locomotor vigour, hunger-gated feeding, learning | OA mediates the flight-induced gain boost in VS cells ([Suver 2012](https://pubmed.ncbi.nlm.nih.gov/23142045/)) [abstract]. Hunger raises sugar-GRN sensitivity through dopamine (Inagaki 2012) [abstract]. Shiu: "We do not account for … neuromodulation" [verified]. Lappalainen: cannot account for "electrical synapses, complex chemical synapse dynamics, and neuromodulation" [verified] | Pools present, sensitivities 0 |
| **Neuropeptides / hormones** | Slow global or regional signals with receptor maps: sNPF, AKH, DILPs, Hugin/AstA, DH44, tachykinin, PDF | Hunger/satiety, sleep, circadian, aggression/courtship (outside tier) | Hugin–AstA regulates sweet sensing ([eLife](https://elifesciences.org/articles/108551)) [abstract]. C. elegans: the connectome failed to predict signal flow, and responses fell in neuropeptide-release mutants ([Randi 2023](https://pubmed.ncbi.nlm.nih.gov/37914938/)) [abstract] | Absent |
| **Plasticity: DAN-gated KC→MBON** | Bidirectional, timing-dependent two-factor rule (sign set by the odour–DA order), compartment-specific learning and decay rates, ongoing DAN-driven forgetting | Olfactory conditioning, retention, extinction, reversal | Handler 2019: DopR1 and DopR2 give depression or potentiation by event order ([Cell](https://pubmed.ncbi.nlm.nih.gov/31230716/)) [abstract]. Aso & Rubin 2016: DAN types differ in training requirement, decay and flexibility ([eLife](https://elifesciences.org/articles/16135)) [abstract]. Rate-model sufficiency: Jiang & Litwin-Kumar 2021 ([PLoS CB](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1009205)) [abstract] | LTD-only option, off |
| **Other plasticity sites** | Ring neuron→EPG Hebbian mapping (landmark–heading calibration); CX/FB for visual pattern and place learning | Navigation with landmarks, place/operant learning | Fisher et al. 2019; Kim et al. 2019 (Nature/Science) [unverified]; Ofstad 2011 place learning [unverified] | Absent |
| **Glia** | Phenomenological only: sleep-pressure integrator (astrocyte Ca²⁺ via TyrRII); no K⁺ buffering unless seizure-like runaway appears | Sleep homeostasis | Astroglial Ca²⁺ rises with sleep need and is needed for rebound ([Blum 2021](https://pubmed.ncbi.nlm.nih.gov/33186550/)) [abstract] | Absent |
| **Timestep** | 0.1 ms for flight, escape and the body. 0.5–1 ms is adequate for the brain during walking and feeding | Flight above all | ~200+ Hz wingbeat; one spike per cycle; activation phase determines kinematic efficacy (Tu & Dickinson 1994/1996, [J Comp Physiol A](https://link.springer.com/article/10.1007/BF00194985)) [abstract] | 0.1 ms everywhere |
| **Photoreceptor transduction** | Adapting, band-limited transducer (log/divisive gain control, ~10–20 ms kinetics) per ommatidium; opsin spectral sensitivity for colour and phototaxis | Optomotor, looming, phototaxis | Lappalainen used a simple front end and still predicted downstream tuning [verified]. Stochastic microvillar models (Song & Juusola 2012) matter for information rates, not for behaviour [unverified] | Graded R cells, per-ommatidium; λmax unused |
| **ORN transduction** | Two-stage: receptor binding kinetics with adaptive feedback, then a differentiating spike filter. Sets ON/OFF timing in plumes | Odour tracking, valence under fluctuating plumes | Nagel & Wilson 2011 ([Nat Neurosci](https://pubmed.ncbi.nlm.nih.gov/21217763/)) [abstract]; Gorur-Shandilya 2017 gain control ([eLife](https://elifesciences.org/articles/27670)) [abstract] | Static Hallem rates, Poisson |
| **JO / chordotonal / FeCO / campaniform** | Filters by subtype: position (tonic), velocity/movement (phasic), direction, load (campaniform), with adaptation; for flight, phase-resolved haltere/wing campaniforms | Posture, walking, grooming (JO), flight | Mamiya 2018 FeCO claw/hook/club tuning [unverified]. Sapkal 2026: stepping persists without feedback, but load and descending input shape "the microstructure of a single leg's step-cycle" ([bioRxiv](https://www.biorxiv.org/content/10.64898/2026.04.29.721658v1.full)) [verified, summary] | Static tuning, guessed gains |
| **Gustatory** | Rate code per GRN class, with state-dependent gain (DA, peptides) | Feeding (PER) | Shiu: activating sugar GRNs drives MN9 [verified]; Inagaki 2012 [abstract] | Guessed gains |
| **Thermosensation** | Phasic plus tonic (hot/cold cells) | Thermotaxis (not Tier 1–2 core) | [unverified] | Phasic temperature |

---

## 2. Minimal neural requirements per behaviour

**Standing, posture and leg reflexes (resistance reflex, flexion/extension)**
- Proprioceptor transduction by subtype: claw position, club movement, hook direction, and campaniform load. Club and hook need adaptation.
- Graded or low-threshold premotor interneurons (13A/13B/9A etc. class), or a background rate that keeps relays within reach of their threshold.
- Per-class unitary strengths for afferent→IN→MN, and the correct receptor sign at glutamatergic IN→MN synapses.
- Presynaptic inhibition of afferents, which gates the reflex during voluntary movement.
- MN recruitment by size and motor-unit twitch (already present).
- No compartments, no plasticity, no neuromodulation, except for the sign of the gain changes between walking and resting.

**Walking (gait, speed, turning)**
- A network oscillator from connectivity alone is sufficient for a rhythm: E1/E2/I1 in Pugliese [verified]. It needs a rate or graded model with per-neuron gain and threshold and τ ≈ 20 ms, but no intrinsic bursting.
- Descending command drive (DNg100, DNb08, MDN) with graded rate coding sets speed and direction.
- Proprioceptive feedback is needed for step microstructure, speed flexibility and load adaptation (Sapkal 2026), so the Tier A transducers are required.
- Neuromodulation (OA) scales vigour but is not needed for the gait itself.

**Flight (steering, saccades, stabilisation; takeoff and landing)**
- Spiking steering MNs with one spike per wingbeat, whose phase is set by wingbeat-synchronous haltere and wing campaniform input through electrical plus chemical synapses. This needs the 0.1 ms step and delays accurate to ~0.1 ms.
- Motion vision (T4/T5 with multiplication, LPTC integration) feeding DNs and neck/wing MNs.
- OA-dependent gain change when flight starts (Suver 2012).
- Saccades are discrete events, integrate-and-fire-like in DNs; adaptation probably sets their refractory interval [unverified].
- Takeoff: looming detection (LC4, LPLC2 → GF) and a GF gap-junction path to the TTM motor neuron. The GF spike timing relative to the rest of the DN population picks the short or long escape mode (von Reyn 2014) [unverified].
- Landing: looming plus leg-extension DNs [unverified].
- Asynchronous power muscles run on stretch activation, which is a muscle mechanism, not a neural one. The MNs only set power and need rates of about 5–10 Hz [unverified].

**Vision (optomotor, looming escape)**
- Adapting photoreceptors.
- Graded LMC/Mi/Tm cells with per-type τ and rest.
- A T4/T5 nonlinearity: shunting or a fitted threshold-linear point neuron.
- Gap-coupled LPTCs (optional for optomotor; HS/VS coupling improves the flow-field estimate [unverified]).
- Lappalainen's result shows that even this front end needs per-type fitting. Synapse counts plus uniform parameters are not enough.

**Olfaction (odour tracking, valence)**
- Two-stage ORN transduction.
- Short-term depression at ORN→PN.
- GABA-A and GABA-B lateral and presynaptic inhibition.
- eLN–PN electrical coupling (Yaksi & Wilson 2010) [unverified].
- KC sparse coding needs a high KC threshold plus APL feedback.
- Innate valence runs through the LH, whose wiring appears adequate as the key constraint.
- Tracking in a plume depends on ORN ON/OFF kinetics; static rates cannot give ON/OFF-driven turning.

**Touch and proprioception, grooming**
- JO and bristle transduction.
- Command-like pathways (aBN) plus a suppression hierarchy.
- Shiu reproduced grooming-circuit predictions with plain LIF [verified].
- The grooming sequence needs sensory feedback (dust removal) and perhaps slow adaptation, but no special biophysics was found [unverified].

**Feeding (PER)**
- Plain LIF was sufficient for the sensorimotor chain (Shiu) [verified].
- Hunger dependence needs DA gain on sugar GRNs and peptide signals (Hugin/AstA, sNPF, AKH). Without them the fed and starved PER curves cannot be told apart.

**State (hunger/satiety, arousal, sleep)**
- Slow state variables: nutrient, sleep pressure, circadian phase.
- Peptide and monoamine receptor maps.
- The dFB sleep switch: excitability change through K⁺-channel trafficking (Pimentel 2016) [unverified].
- R5 NMDA slow waves.
- An astrocyte Ca²⁺ sleep-need integrator.
- A circadian oscillator driving clock-neuron Na-leak / K excitability.
- All of these can be phenomenological.

**Learning, memory, retention and forgetting**
- A DAN-gated, order-sensitive two-factor rule at KC→MBON synapses, with an eligibility window of seconds.
- Compartment-specific learning and decay rates.
- Ongoing DAN activity for forgetting (Berry 2012) [unverified].
- A consolidation variable for long-term memory (hours to days).
- Operant and place learning add CX plasticity, and the ring neuron→EPG mapping plasticity.
- Timescales: acquisition over 1–10 trials of seconds; retention from minutes to days.

**Heading and navigation (CX)**
- A ring attractor can be built from LIF (Kakaria & de Bivort 2017, [Front Behav Neurosci](https://www.frontiersin.org/journals/behavioral-neuroscience/articles/10.3389/fnbeh.2017.00008/full)) [abstract] or from rate neurons (Noorman 2024) [abstract].
- Either way it needs **tuned** relative weights (EPG↔PEN excitation, Delta7 global inhibition), a PEN angular-velocity input, and noise.
- Landmark anchoring needs ring-neuron plasticity.
- Noorman shows that small rings can hold a continuous heading but are sensitive to tuning. That supports our s8 finding: uniform efficacy × synapse count does not produce a bump, while adaptation plus a rescaled Delta7 does.

---

## 3. Tiered recommendation

Here a "mechanism" means a distinct piece of simulator physics. Parameter tables for existing physics do not count.

### Tier A — walking, posture, sensory responses (≈10 mechanisms; 4 already exist in some form)
1. Mixed neuron modes: LIF for spiking classes, a graded leaky integrator with a threshold-linear output synapse for non-spiking classes, assigned per class. *Extend the existing graded option to the VNC and optic lobe.*
2. Per-class intrinsic parameters (V_rest, τm, threshold, gain) plus **background/spontaneous drive** (a noise or tonic term per class). *New as a systematic layer.*
3. Per-class unitary synaptic strength, which replaces uniform efficacy (a fitted table). *Physics exists; parameters do not.*
4. Receptor-resolved sign with two kinetic classes (fast ionotropic; slow metabotropic such as GABA-B/mGluR). *Partial.*
5. Conductance-based (shunting) inhibition for flagged classes: T4/T5, and the AL if needed. *Option exists.*
6. Short-term depression at sensory first synapses. *Option exists.*
7. Presynaptic inhibition of afferent terminals. *Option exists.*
8. Spike-frequency adaptation per class. *Option exists.*
9. Gap junctions at a curated list of sites (AL eLN–PN, JO–GF, LPTC). *GF only today.*
10. Dynamic sensory transducers: adapting photoreceptor; two-stage ORN; FeCO claw/club/hook with adaptation; campaniform load; JO; GRN. This is one family of ~6 models, several already static.

### Tier B — flight (≈5 further mechanisms)
1. Wingbeat-phase-resolved haltere and wing campaniform transduction.
2. Rectifying electrical plus chemical afferent→steering-MN synapses; a sub-ms delay budget.
3. Spiking steering-MN models that hold one-spike-per-cycle phase locking (possibly with intrinsic tonic drive).
4. OA flight-state gain on the visual (LPTC) and descending pathways. This is the first neuromodulator that must be active.
5. The GF escape system with timing-dependent choice of mode (looming → GF / DN population).

Stretch-activated power muscles are needed too, but they are body physics, not neural.

### Tier C — state and learning (≈8–9 further mechanisms)
1. Active neuromodulator pools (DA, OA, 5-HT, TA) with per-type receptor maps and GPCR kinetics (seconds to minutes).
2. A neuropeptide and hormone layer with a metabolic state variable: nutrients → AKH/DILP/Hugin/sNPF → GRN and DAN gain.
3. DAN-gated bidirectional, timing-dependent KC→MBON plasticity with per-compartment rates.
4. Memory decay, active forgetting and consolidation variables.
5. APL with local (compartmental) inhibition.
6. CX plasticity: ring neuron→EPG mapping, and FB/EB sites for place and pattern learning.
7. NMDA-type voltage-dependent slow synapses, at least in R5 and possibly the ring.
8. Sleep homeostat: dFB excitability switch plus an astrocyte Ca²⁺ integrator (glia, phenomenological).
9. A circadian oscillator driving clock-neuron excitability.

**Explicitly not needed at any tier on current evidence:**
- Hodgkin–Huxley channel kinetics across the brain;
- detailed multi-compartment morphology outside T4/T5, APL and LPTC;
- stochastic vesicle release at single synapses (a lumped noise term suffices);
- K⁺ buffering by glia;
- intracellular cAMP/PKA biochemistry: the order-sensitive rule captures its behavioural output.

Each of these should be revisited only if a validation failure points at it.

---

## 4. Uncertainties, and where perfect data would not settle the question

1. **Degeneracy.**
   - Lappalainen's 50-model ensemble fitted equally well with three different T4 mechanisms [verified].
   - Behaviour and even single-cell tuning underdetermine the internals, and perfect parameters do not tell you which abstraction is needed.
   - Sufficiency is always relative to a validation target. "Minimal" is defined by the observation set, so the held-out observations decide it, not the biology.
2. **Sufficiency evidence comes from open-loop or partial models.**
   - Shiu is brain-only, with no VNC and no body.
   - Pugliese is VNC-only and feed-forward, with no proprioception. Its authors note that realistic muscle patterns "likely rely on … proprioceptive feedback" [verified].
   - Lappalainen covers motion vision only.
   - No study has shown that one abstraction works for a closed-loop whole CNS plus body. Recurrent loops can turn tolerable errors in each part into runaway or silence, which is what our s5–s8 history shows.
3. **Which VNC neurons are non-spiking is unknown for Drosophila.** The locust and cockroach analogy is strong. Drosophila evidence is sparse (APN2; the Pugliese rationale). Perfect data would settle it, and it is the single most consequential unknown for Tier A.
4. **Gap junctions are invisible in EM.** Innexin expression maps and dye coupling give only a partial picture. Beyond the GF, AL, LPTC and flight-MN sites, where electrical synapses sit and which way they rectify is unknown.
5. **Neuromodulator and peptide receptor maps are transcript-based.**
   - Protein localisation, receptor affinity and volume-transmission range are poorly measured.
   - The C. elegans lesson (Randi 2023) is that extrasynaptic signalling can dominate functional connectivity in places the synaptic connectome does not predict.
   - OpenWorm has had a full connectome for decades without reproducing behaviour. Its missing pieces were graded dynamics, neuromodulation and body mechanics, not neuron count [partly unverified].
6. **Tuning sensitivity of attractors.** Noorman 2024 shows small rings can work but are fine-tuned. Even with measured synapse counts, the ring may need per-synapse strengths, receptor densities and compensatory homeostasis (a developmental or plastic process). A "perfect snapshot" may then not be self-consistent without a lifetime plasticity or homeostasis model.
7. **Timing precision in flight.** The Calliphora evidence for electrical afferent→MN coupling is not confirmed in Drosophila. The precision needed (≤0.1 ms?) is inferred from phase-dependent muscle efficacy, not from a sufficiency model.
8. **Cross-specimen transfer.** Our connectome is male-cns. The physiology comes from other flies (often female, other genotypes). Individual variability in synapse counts (~10–30 % between hemispheres [unverified]) sets a floor on how precise "perfect" parameters can be.
9. **Learning-rule completeness.** The known KC→MBON rules come from optogenetic DAN activation. Natural reinforcement recruits many DANs, MBON→DAN feedback and neuromodulator co-release (NO in some DANs; Aso 2019 eLife [abstract via search]). A two-factor rule may reproduce first-order conditioning but not second-order conditioning, extinction and reversal without these extras.

**The next discriminating experiment for this project**, following from conclusions 1–2:
- Switch the VNC local-interneuron classes (and the optic-lobe columnar front end) to graded mode.
- Add per-class background drive.
- Re-run the standing/reflex battery on fresh seeds.
- If relays wake and the reflex passes without the ×10.9 afferent scale, then graded transmission and background activity were the missing Tier A physics. If they do not, the gap is in per-class unitary strengths.
