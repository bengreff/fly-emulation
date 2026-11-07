# Non-neural organ mechanisms: what to port (research note, not canon)

Compiled 2026-11-06. Written for the builder implementing PLAN.md rows 11-16, 20-23 (glia, body-wall
muscle EC coupling, pharynx, intestine/defecation, egg-laying, other non-neural cells, metabolism, body,
environment, observation models). Scope: find the best PUBLISHED mechanistic model to PORT, not invent,
per the "port, don't build" rule. Read first (not repeated here except where they answer a row directly):
`docs/worm/MECHANISMS_AUDIT.md` (current code state, rows 1-23), `docs/worm/PLAN.md` section a,
`docs/worm/research/BODY.md`, `docs/worm/research/c302_port.md`, `docs/worm/STATE_OF_THE_ART.md`, and the
body worker's `HANDOFF_BODY.md` / `BODY_TESTS.md` on the wormbody worktree.

Labels used throughout: **measured** (read off data or a cited source directly), **derived** (arithmetic
on measured numbers, shown), **inferred** (taken from a source by reasoning, e.g. homology), **guessed**
(an estimate with no direct basis, bounded and reasoned). Anything not independently verified by opening
the source is marked **UNVERIFIED**.

## Section list (mechanism -> PLAN row)

- O1. Body-wall muscle excitation-contraction (row 12)
- O2. Pharynx (row 13)
- O3. Intestine and defecation motor program (row 14)
- O4. Egg-laying (row 15)
- O5. Glia (row 11)
- O6. Other non-neural cells: hypodermis/seam, excretory canal, coelomocytes (row 16)
- O7. Metabolism (row 20)
- O8. Body: cuticle, pressure, viscoelasticity (row 21)
- O9. Environment fields: food lawn, O2/CO2, salt, temperature, mechanical, viscoelastic media (row 22)
- O10. Observation models: GCaMP, optogenetics, NeuroPAL (row 23)

## Summary table (filled in as each section completes)

| # | Mechanism | Model to port | Open code? | Confidence |
|---|---|---|---|---|
| O1 | Body-wall muscle EC coupling | Du/Crodelle 2025 (membrane, PMC11781704) + Boyle-Cohen 2008/c302 (fallback) + Boyle-Berri-Cohen 2012 (Ca-to-force, tau_M 100ms) | Yes, both (GitHub, CC-BY / MIT) | High on membrane models; low on the force-model exact equations (UNVERIFIED) |
| O2 | Pharynx | PNAS 2024 29-cell FitzHugh-Nagumo network + bioRxiv 228650 EGL-19/EXP-2 single-cell | Not found | Medium structure, low on exact parameters (both PDFs unreadable this pass) |
| O3 | Intestine/defecation | Teramoto & Iwasaki 2006 IP3R negative-feedback oscillator (mechanism) + Peters 2007 INX-16 wave + Beg 2008 PBO-4/5 + NLP-40/AVL/DVB | Not found | Medium mechanism, low on rate constants (UNVERIFIED, generic de Young-Keizer/Li-Rinzel as fallback) |
| O4 | Egg-laying | Waggoner 1998 two-state process + Collins/Koelle 2013/2016 (UNC-103/EGL-19 gate) + Ravi 2018/2021 (muscle-HSN feedback) | Not found | High on measured timing numbers; low on channel-level parameters |
| O5 | Glia | Singhvi 2016 KCC-3/AFD mechanism + cross-species Kir4.1 buffering as fallback numbers | Not found | Low (no C. elegans quantitative model exists) |
| O6 | Other non-neural cells | Liu 2013 (muscle Gj, 6 innexins) + CLH-3/AQP-8 canal mechanism + Fares/Greenwald 2001 coelomocyte assay | Not found | Low (mechanism only, almost no rate constants found) |
| O7 | Metabolism | Add-my-Pet standard DEB model, C. elegans entry (already fitted) | Yes (DEBtool/AmPtool) | High (direct numeric fit found, open code) |
| O8 | Body (cuticle/pressure) | Already ported: MetaWorm FEM body; add Frontiers 2024 layer-resolved cuticle/muscle/pseudocoelom moduli + Backholm 2013 Maxwell damping | Yes (already in repo, Apache 2.0) | High (already running; gap is a known, named missing feature) |
| O9 | Environment fields | Demir et al. 2020 eLife worm-density/O2 PDE (food lawn) + standard NaCl diffusion + Krieg/Pruitt 2017 touch-force calibration | Not found (Demir); n/a (standard diffusion) | High on numbers found; medium on attribution for some standard values |
| O10 | Observation models | GCaMP6s/6f (Chen 2013/GENIE) + GCaMP7f (Dana 2019) Hill-curve kinetics; GUR-3/PRDX-2 (Randi 2023/TWISP) under-characterised; NeuroPAL (Yemini 2021-adjacent) accuracy | n/a (indicator kinetics, not simulation code) | High on GCaMP; low on the optogenetic actuator (source itself calls it under-characterised) |

---

(Sections below are appended as each mechanism is finished. Partial work survives a stall.)

---

## O1. Body-wall muscle membrane and excitation-contraction (PLAN row 12)

**Two separate published models are needed, because no single paper covers both halves.** The membrane/Ca
model (channels to Ca influx) and the Ca-to-force model are different papers with different code bases;
"Du/Crodelle 2024" named in PLAN.md does NOT cover force (verified below), so the ledger's wording that
pairs it with "Ca to force (Hill-type) inferred" needs to be read as: Du/Crodelle gives the membrane, a
separate older source gives the force.

### (a) Membrane and Ca influx

**Model to port: two candidates, pick by how much channel detail is wanted.**

1. **Boyle and Cohen 2008**, *Caenorhabditis elegans body wall muscles are simple actuators*, Biosystems
   94:170-181, DOI [10.1016/j.biosystems.2008.05.025](https://doi.org/10.1016/j.biosystems.2008.05.025).
   Single-compartment HH-type cell: Ca current (ca_boyle, activation gate power 2 tau 0.1 ms, inactivation
   gate power 1 tau 150.9 ms, plus a Ca-concentration-dependent inactivation gate that is c302's own addition,
   not in the original paper's Table A1 - c302's own code comment flags a sign discrepancy, -5.03 mV vs the
   paper's +5 mV, sourced from OpenWorm's own Matlab/Python support code, not the paper directly), K fast
   (activation power 4 tau 2.26 ms, inactivation power 1 tau 150 ms), K slow (activation power 1, fixed tau
   25.0 ms), leak, and a simple decaying Ca pool (tau 60.8 ms for muscle, rho 0.000238919 mol/m/A/s in the
   OpenWorm NeuroML port, vs tau 13.8 ms for the neuron version of the same channel set) [c302-source,
   verified directly from the generated NEURON code in `docs/worm/research/c302_port.md` this project already
   ran]. **Open code: yes.** `github.com/openworm/muscle_model` (Matlab/C++/Python/NeuroML2, license file
   present, not independently re-read here beyond "LICENSE file present"); also already regenerated and
   verified by this project via c302 (`data/worm/ported/c302/`, MIT licence for c302 itself, LGPL-3 for
   pyNeuroML). **This is the model already running in `brain._c302_muscle`, off by default** (MECHANISMS_AUDIT
   row 12).

2. **Du, Crodelle, Barranca, Li, Shi, Gao and Zhou 2025**, *Biophysical modeling and experimental analysis of
   the dynamics of C. elegans body-wall muscle cells*, PLOS Computational Biology 21(1):e1012318, DOI
   [10.1371/journal.pcbi.1012318](https://doi.org/10.1371/journal.pcbi.1012318) (posted as a 2024 bioRxiv
   preprint, hence PLAN.md's "2024" label; published Jan 2025). Opened via PMC11781704. A 7-dimensional
   Hodgkin-Huxley model fit to the authors' own voltage-clamp and mutant data: EGL-19 (L-type Ca, m^2 h
   gating), SHK-1 (Kv, n^4), SLO-2 (Ca-gated K, voltage term z_inf^3 times a Ca-dependent term p^2), an early
   inhibitory K current K_r (gate 1-q), an NCA Na-leak channel, and leak. **UNC-2/CCA-1, SHL-1, SLO-1, KQT and
   EXP-2 are NOT in this model** (checked directly, not just inferred from the title) - PLAN's channel list for
   row 12 is broader than what either published whole-cell muscle model actually contains; CCA-1/UNC-2/SLO-1/
   KQT/EXP-2 densities in muscle would have to come from tissue-expression homology to the neuron versions
   (row 3-5), labelled inferred, if the builder wants them. Ca dynamics: `d[Ca]_i/dt = -I_Ca/(2FA*d) -
   gamma*([Ca]_i - [Ca]_rest)`, i.e. a single well-mixed shell with linear clearance, same structural form as
   Boyle and Cohen's pool, different gamma. SLO-2 Ca binding rates given directly: alpha = 58 ms^-1 mM^-2,
   beta = 0.09 ms^-1 [measured, fit]. **Finding that matters for the builder**: the fitted model shows a
   resonant/burst firing frequency around 4.7-4.8 Hz (burst mode) vs <2 Hz (regular mode) - this is itself an
   isolated check (see below). **No Ca-to-force coupling is in this paper** - confirmed by direct read, not
   assumed from the title. **Open code: yes.** `github.com/XuexingDu/C.elegans-Muscle`, CC-BY 4.0, with a 64 MB
   S1 Data zip of the fitting data.

Recommendation: port Du/Crodelle for the membrane/Ca-influx dynamics (it is the directly-fit, most recent
whole-cell muscle model and already has open code and a clear isolated check), and keep Boyle-Cohen/c302 as
the fallback already running in this codebase (cheaper, already verified end-to-end against NEURON).

### (b) Calcium release: UNC-68/RyR and SERCA

**UNC-68 (RyR) is NOT required for basic excitation-contraction in C. elegans** - `unc-68` null mutants still
contract (measured phenotype, [Maryon, Coronado & Anderson 1996, J Cell Biol](https://pubmed.ncbi.nlm.nih.gov/8769414/)),
so unlike vertebrate skeletal muscle, voltage-gated Ca influx through EGL-19 is sufficient on its own; RyR-
mediated Ca-induced-Ca-release is a modulatory addition, not the core mechanism. A 2024 mechanistic result,
**Gao, Zheng et al. 2024**, *Voltage-induced calcium release in C. elegans body muscles*, PNAS 121(19):e2317753121,
DOI [10.1073/pnas.2317753121](https://doi.org/10.1073/pnas.2317753121) (opened via search; full text not
independently fetched - **UNVERIFIED beyond abstract**), proposes a VICR mechanism: EGL-19's voltage-sensing
domain is allosterically coupled through JPH-1/Junctophilin and SHN-1/Shank scaffolding to RyR and IP3R
channels on the SR, triggering Ca release without needing Ca influx first (a "mechanical" voltage link, not a
diffusible-Ca link). A rebuttal/response paper exists (**PNAS 2024, "Response to Allard"**,
10.1073/pnas.2415044121) arguing the effect is minor; **no quantitative kinetic parameters were extracted from
either paper in this pass - mark the VICR coupling rate UNVERIFIED/guessed if used.** SERCA reuptake into the
SR is mentioned in the C. elegans literature only qualitatively (no extracted rate constant found this pass);
**the nested-simplest form for a builder is to fold SR release/reuptake into the single Ca pool's clearance
time constant** (as Boyle-Cohen and Du/Crodelle already both do), and treat UNC-68/JPH-1/SHN-1 coupling as an
optional second, slower Ca pool only if finer detail is later needed - labelled inferred/guessed, not fitted.

### (c) Ca to force

**No published whole-cell C. elegans muscle paper (Boyle-Cohen 2008, Du/Crodelle 2025) includes a Ca-to-force
step** (verified directly for both). The force model that is actually used throughout the C. elegans
locomotion-modelling literature (OpenWorm/Sibernetic, Izquierdo and Beer 2018, Olivares et al. 2021, the
MetaWorm body this project has already ported) is from **Boyle, Berri and Cohen 2012**, *Gait modulation in
C. elegans: an integrated neuromechanical model*, Frontiers in Computational Neuroscience 6:10, DOI
10.3389/fncom.2012.00010 (also in Boyle's 2009 PhD thesis, etheses.whiterose.ac.uk/1377): muscle activation is
a **leaky integrator**, "T_muscle = tau_M = 100 ms" (cited directly by name in Olivares et al. 2021, PAR.NSF
10286537, as matching the measured response time of C. elegans' obliquely striated muscle), with **two stages
of low-pass filtering**: one on membrane potential, one on internal Ca concentration, followed by a described
"linear second order model ... used to calculate the isometric force" (the exact coefficients of that second-
order system were not extracted from primary text in this pass - the OpenWorm `muscle_model` repo's
`F_thi.m` file, fetched directly, turned out to be a *coupling-effect* analysis between adjacent muscle arms,
not the force ODE itself; **mark the exact second-order coefficients UNVERIFIED**, with tau_M = 100 ms as the
one directly-sourced number). Separately, muscle mechanical output in Boyle-Berri-Cohen 2012 is a **damped
spring** whose spring constant, rest length and damping constant are each functions of the activation level
(a Hill-type nonlinearity in the spring constant, not a classical sarcomere force-length curve) - this is the
"simplest nested form" for a builder: `F = k(a)*(L0(a) - L) - c(a)*dL/dt`, with k, L0, c all monotonic
functions of activation a in [0,1], no numeric values extracted this pass.

**Simplest nested form overall (cheapest to most detailed), in order:**
1. Voltage -> sigmoid -> activation -> linear force (what `layers.muscle_activation` does today; lumped, no Ca state).
2. Add a single bulk Ca pool per muscle cell with linear clearance (Boyle-Cohen `CaPool` form, tau ~ 13-60 ms depending on cell type) + a Hill curve Ca -> activation.
3. Full Du/Crodelle 7-state membrane model per muscle cell + a leaky-integrator activation (tau_M = 100 ms) + damped-spring force (Boyle-Berri-Cohen 2012).
4. Add VICR-coupled SR release as a second, slower Ca compartment (UNVERIFIED parameters, optional).
5. UNC-9 gap junctions between body-wall muscle cells: **not separately parameterised in this pass** - c302's own `muscle_to_muscle_elec_syn` component exists in `parameters_C2.py` but is set to 0 nS "off by design" (verified directly, `c302_port.md`); no non-zero published muscle-muscle gap conductance was found this pass. Treat as guessed, bounded by the neuron-neuron UNC-9 range already in the ledger (row 8), until a muscle-specific value is found.

### Parameter table

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| EGL-19 activation tau (Boyle-Cohen ca_boyle) | 0.1 | - | ms | Boyle & Cohen 2008 via c302 NEURON export | published fit |
| EGL-19 inactivation tau | 150.9 | - | ms | same | published fit |
| K fast (SHK-1-like) activation tau | 2.26 | - | ms | same | published fit |
| K fast inactivation tau | 150 | - | ms | same | published fit |
| K slow activation tau | 25.0 | - | ms | same | published fit |
| Ca pool decay tau (muscle) | 60.8 | - | ms | Boyle & Cohen via c302 NEURON export | published fit |
| Ca pool decay tau (NeuroML CaPool.nml generic) | 11.5943 | - | ms | OpenWorm muscle_model repo, CaPool.nml | published fit (generic, not muscle-specific - header flags "may need replacement for muscle model") |
| SLO-2 Ca-binding alpha | 58 | - | ms^-1 mM^-2 | Du/Crodelle 2025 (PMC11781704) | published fit |
| SLO-2 Ca-binding beta | 0.09 | - | ms^-1 | Du/Crodelle 2025 | published fit |
| Resonant/burst firing frequency | 4.7-4.8 | 4.8 +/- 1.05 | Hz | Du/Crodelle 2025, measured in their recordings | measured |
| Regular-firing frequency ceiling | <2 | - | Hz | Du/Crodelle 2025 | measured |
| Muscle activation leaky-integrator tau_M | 100 | - | ms | Boyle, Berri & Cohen 2012, cited by name in Olivares et al. 2021 | published fit |
| Muscle-muscle UNC-9 gap conductance | 0 (off by design in c302 C2) | unknown | nS | c302 `parameters_C2.py` | spec only / not found published; guessed if turned on |
| Second-order Ca-to-force time constants | UNVERIFIED | - | ms | Boyle-Berri-Cohen 2012 / Boyle thesis 2009 | not extracted this pass |

**Cells:** all 95 body-wall muscle cells (4 quadrants: DL, DR, VR 24 each, VL 23; MECHANISMS_AUDIT row 1, BODY.md s1).

**Isolated check for the builder:** drive a single isolated muscle-cell membrane model (Du/Crodelle 7-state,
or Boyle-Cohen c302 single cell) with a step current and check the burst-mode resonance peaks at 4.7-4.8 Hz
(Du/Crodelle 2025's own measured result) - a unit check on the membrane alone, no force or body needed. A
second, independent check: `unc-68` (RyR) null should still produce near-normal contraction amplitude (Maryon
1996) - if a ported model's force collapses without RyR, the model has made SR release load-bearing when the
real animal does not.

---

## O2. Pharynx (PLAN row 13)

**Best model to port: a 29-cell FitzHugh-Nagumo pharyngeal network that computes the EPG directly, plus a
two-channel (EGL-19/EXP-2) single-cell pharyngeal muscle AP model for the channel-level detail PLAN asks for.**
Neither paper's full equations/parameters could be extracted from primary text in this pass (both PDFs
returned binary/garbled content to the fetch tool, and the PNAS page returned HTTP 403); what follows is
verified from abstracts, PubMed/PMC search snippets and this project's own existing sources (STATE_OF_THE_ART,
WormBook) only - **mark exact equations and parameter values UNVERIFIED** pending a direct read of the PDFs
or supplements (a builder with institutional access should pull these first).

1. **Network/EPG model**: *Deciphering the underlying mechanisms of the pharyngeal pumping motions in
   Caenorhabditis elegans*, PNAS 121(7):e2302660121, 2024, DOI
   [10.1073/pnas.2302660121](https://doi.org/10.1073/pnas.2302660121) (PMID 38315866; an earlier related
   preprint is [arXiv:1903.12009](https://arxiv.org/pdf/1903.12009), title "Deciphering the underlying
   mechanisms of the pharyngeal motions in Caenorhabditis elegans" - likely the same group's earlier version,
   not independently confirmed as the same model). Per search-snippet description: a pharyngeal muscle model
   with **29 cell models**, each cell's membrane potential simulated by **FitzHugh-Nagumo equations** (a
   2-variable relaxation-oscillator simplification of Hodgkin-Huxley, cheaper than full channel kinetics),
   and the **electropharyngeogram computed directly from the simulated membrane potentials** (i.e. the EPG is
   a derived observable of the network model, not a separately fit waveform - this is the right structure for
   PLAN's "EPG shape" requirement). **Open code: not found this pass** - no GitHub/OSF link located;
   UNVERIFIED whether code exists.

2. **Single-cell channel model**: *EGL-19 and EXP-2 Ion Channels Modelling within C. Elegans Pharyngeal
   Muscle Cell Allows Reproduction of Ca2+ Driven Action Potentials, Both Single Events and Trains*, bioRxiv
   228650, posted 2017-12-21 ([https://www.biorxiv.org/content/10.1101/228650](https://www.biorxiv.org/content/10.1101/228650.full.pdf)).
   Title alone states the model's structure: two voltage-gated channels, **EGL-19** (L-type Ca, the same gene
   used in body-wall muscle, row 12) and **EXP-2** (a fast-inactivating, unusually-shaped K channel specific
   to pharyngeal muscle repolarisation - EXP-2 is known in the literature to be responsible for the pharynx's
   distinctively rapid repolarisation, faster than body-wall muscle), reproducing both single action potentials
   and trains. **CCA-1** (a T-type-like Ca channel contributing to pharyngeal pacemaking) is named in PLAN but
   not in this paper's title; STATE_OF_THE_ART.md already notes from a different search pass that "C. elegans
   pharyngeal muscles exhibit repetitive, characteristic action potentials generated by the activity of three
   main ion channels: CCA-1, EGL-19, and EXP-2" - so CCA-1's role is established in the broader literature even
   though this specific paper's title only names two. **Equations/parameters not extracted this pass -
   UNVERIFIED.**

### Circuit roles (measured/established, not modelled with parameters in this pass)

- **MC**: cholinergic motor neuron, activated by serotonin signalling, drives the fast pump rhythm via the
  **EAT-2** nicotinic AChR (a non-alpha nAChR subunit) on pharyngeal muscle - each pump cycle = one pharyngeal
  muscle action potential, *initiated by MC*.
- **M3**: glutamatergic, inhibitory, acting through **AVR-15** (an avermectin-sensitive glutamate-gated Cl-
  channel, i.e. GluCl) on pharyngeal muscle; *terminates* each action potential (shortens contraction). Loss of
  M3 signalling (via `eat-4` vesicular glutamate transporter or `avr-15` mutants) **prolongs the AP** (measured
  phenotype, found via PubMed/PMC search of srep22940 and related sources).
  M4 is required for **isthmus peristalsis** specifically (the posterior-pharynx bolus transport step, distinct
  from the anterior pump itself) - MC and M3 control the pump, M4 controls isthmus peristalsis (established
  division of labour, same sources).
- **NSM**: serotonergic; serotonin biosynthesis in NSM and HSN is reported as individually sufficient and
  jointly required for triggering bursts of fast pumping in response to food (Lockery lab, *Serotonin-dependent
  kinetics of feeding bursts underlie a graded response to food availability in C. elegans*, Nature
  Communications 8:14221, 2017, DOI 10.1038/ncomms14221, PMC5296638). The 5-HT1 ortholog **SER-1** mediates the
  food-dependent induction of fast pumping (measured, same source).
- **I1, I2, I3**: apical sensory neurons with direct contact to the pharyngeal lumen (I1/I2/I3 at the
  metastomal flaps), plausibly chemosensing bacteria directly; **I2 monosynaptically inhibits pumping** when it
  senses the environment (measured, Trojanowski et al., *The connectome of the Caenorhabditis elegans
  pharynx*, PMC7601127/bioRxiv 868513 - this paper is the best source for pharyngeal circuit structure, though
  it is a connectome/anatomy paper, not a dynamical model).

### Pumping rate quantitative data (measured, no mechanistic equation given in the source - PMC5296638)

These are the numbers a model's output should reproduce, not model parameters per se:

| Quantity | Value | Condition | Source | Label |
|---|---|---|---|---|
| Single pump duration | ~80 ms | fed, all food concentrations tested | PMC5296638 | measured |
| Single pump duration (alt., WormBook) | ~170 ms | general | STATE_OF_THE_ART.md item 33, WormBook Feeding | measured |
| Fast-pumping interval (peak of distribution) | 174 ms (Gaussian fit, SD 20 ms) | fast/burst pumping | PMC5296638 | measured |
| Fast pumping rate | ~345 pumps/min (6 Hz) | peak of interval distribution | PMC5296638, derived from 174 ms | measured/derived |
| Maximum average pumping rate | ~270 pumps/min | OD600 >= 3 (dense food) | PMC5296638 | measured |
| "Fed" pumping rate (general) | ~250 pumps/min (4-5 Hz) | fed, general | Avery & Horvitz 1989, via STATE_OF_THE_ART item 32 | measured |
| "Long pause" threshold | interval > 600 ms | operational definition | PMC5296638 | measured (operational) |
| Food on/off switching | pumping ceases within seconds of food removal | | WormBook Feeding, STATE_OF_THE_ART item 34 | measured |

### Parameter table (channel/network level)

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| FitzHugh-Nagumo pharyngeal cell count | 29 | - | cells | PNAS 2024 (search-snippet only) | UNVERIFIED (not read from primary text) |
| EGL-19/EXP-2/CCA-1 role assignment | qualitative only | - | - | bioRxiv 228650 title + STATE_OF_THE_ART cross-check | inferred (role established; no numeric conductances found this pass) |
| EAT-2 nAChR role | MC -> pharyngeal muscle, initiates AP | - | - | multiple sources above | measured (qualitative) |
| AVR-15 GluCl role | M3 -> pharyngeal muscle, terminates AP | - | - | multiple sources above | measured (qualitative) |
| Single pump duration | 80-170 | - | ms | PMC5296638 / WormBook | measured |
| Fast pump rate | 250-345 | - | pumps/min | PMC5296638 / Avery & Horvitz 1989 | measured |

**Cells it applies to:** the 20 pharyngeal neurons (I1, I2, I3, I4, I5, I6, M1-M5, MC, MI, NSM, 8 further
per WormAtlas naming) and the pharyngeal muscle cells (pm1-pm8, not separately counted in this pass - PLAN's
row 13 names "pharyngeal muscle" as a lump; MECHANISMS_AUDIT row 13 confirms the body currently has *no*
pharyngeal muscle at all, body row MB12 missing).

**Simplest nested form:** (1) current code's fixed-waveform pump-rate clock driven by a food signal (what
`layers.pharynx` already does, lumped); (2) a single FitzHugh-Nagumo pharyngeal muscle oscillator, food/
serotonin-gated pump rate, no neuron-level detail; (3) the full 29-cell FHN network with MC/M3/M4/NSM/I1-I3
roles wired per Trojanowski's connectome, EPG computed from the simulated potentials; (4) add EGL-19/EXP-2/
CCA-1 channel-level detail per pharyngeal muscle cell (bioRxiv 228650) in place of the FHN relaxation
oscillator.

**Isolated check for the builder:** drive the pump-rate model with a food step (OD600 0 -> >=3) and check
pump interval settles near 174 ms (6 Hz) with the measured SD of 20 ms (PMC5296638) - a unit check on rate
alone, no circuit identity needed. A second check: an `avr-15` (M3/GluCl) knockout should lengthen the single
pump duration beyond the 80-170 ms wild-type range (measured phenotype, srep22940/PMC cross-check above) - if
removing M3 in the model does not lengthen the AP, the model has not captured M3's termination role.

---

## O3. Intestine and defecation motor program (PLAN row 14)

**Core finding: there is no single off-the-shelf mathematical model with a complete, published parameter set
for the IP3R Ca oscillator across the 20 intestinal cells.** The mechanism is well characterised
qualitatively and the downstream motor program is well characterised quantitatively (timing), but the
oscillator's own rate-constant-level kinetics were not located in open, extractable form this pass. Treat
this row as "mechanism known, oscillator parameters to be fit within bounds", consistent with PLAN's own
label for row 14 ("rates fitted").

**Model to port (mechanism): a two-component IP3R negative-feedback oscillator**, per **Teramoto and
Iwasaki 2006**, *Intestinal calcium waves coordinate a behavioral motor program in C. elegans*, Cell Calcium
40(4):319-327 (title/authorship from search; DOI not independently opened this pass -
**UNVERIFIED beyond the search-engine summary**). Structure described: ITR-1 (the single C. elegans IP3
receptor) is activated by low cytoplasmic Ca2+ and inhibited by high Ca2+ - this bidirectional Ca dependence
is, on its own, sufficient to generate oscillation (a textbook IP3R negative-feedback oscillator, the same
class of model as de Young-Keizer or Li-Rinzel IP3R models used throughout the Ca-oscillation literature
generally, not worm-specific) - the paper additionally proposes Ca feedback onto PLC activity, making a
second, slower feedback loop (IP3R activity <-> PLC <-> IP3 production). **No rate constants extracted this
pass.** The de Young-Keizer (1992) or Li-Rinzel (1994) generic IP3R model forms (widely available, open
implementations exist in many Ca-signalling modelling toolkits, e.g. CellML repository) are the nearest
generic, parameterised template if the C. elegans-specific rate constants cannot be found; using them would
mean porting generic IP3R kinetics with C. elegans-specific values labelled guessed/inferred, which is
consistent with "port the mechanism, bound the unknowns."

**Supporting single-cell data: Espelt et al. 2005**, *Oscillatory Ca2+ signaling in the isolated
Caenorhabditis elegans intestine: role of the inositol-1,4,5-trisphosphate receptor and phospholipases Cbeta
and Cgamma*, Journal of General Physiology 126:379-392. Confirms the oscillator persists in the *isolated*
intestine (i.e. it is autonomous, not driven by an external pacemaker) and that **PLCgamma generates the IP3
that drives ITR-1, while PLCbeta runs a separate, required pathway** - so the mechanism has (at least) two
upstream inputs into the same IP3R oscillator, not one. **Dal Santo et al. 1999**, *The inositol
trisphosphate receptor regulates a 50-second behavioral rhythm in C. elegans*, Cell 98(6):757-767 (DOI from
STATE_OF_THE_ART.md's own prior citation: 10.1016/s0092-8674(00)81510-x), established ITR-1 as necessary (an
`itr-1` strong loss-of-function abolishes the Ca wave entirely - measured, a strong isolated check).

**Gap junction coupling: INX-16.** **Peters, Rogers, Bhatt et al. 2007** (title from search: *A calcium wave
mediated by gap junctions coordinates a rhythmic behavior in C. elegans*, Current Biology, specific volume/
page/DOI not independently confirmed this pass - PDF fetched but returned unreadable binary content,
**UNVERIFIED** numeric content) establishes that **INX-16** gap junctions between intestinal cells are
required to propagate the Ca wave along the gut; no numeric diffusion/conductance value was extracted. A
companion/related paper, **Peters/Nehrke et al. 2007**, *Intestinal Ca2+ wave dynamics in freely moving
C. elegans coordinate execution of a rhythmic motor program*, American Journal of Physiology-Cell Physiology
(PMID 17942636; full text blocked, 403), found that **in freely moving (not restrained) animals the wave
initiates simultaneously at both the anterior and posterior ends of the 20-cell intestine and propagates
inward** - different from the single-direction (posterior-to-anterior or similar) wave seen in restrained
preparations - a finding that matters if the model is validated against restrained-animal imaging data vs.
freely-moving data; the two should not be expected to match exactly. That paper also lists `egl-8`/PLC-beta,
`kqt-3`/KCNQ1 (a K channel), `sca-1`/SERCA, and `unc-43`/CaMKII as genes that alter Ca handling in this
system - SERCA (sca-1) is explicitly implicated, confirming PLAN's ask for SERCA in the Ca-handling list.

**Downstream: proton signalling to posterior body muscle.** **Beg, Ernstrom, Nix, Davis and Jorgensen 2008**
(title from search: *Protons act as a transmitter for muscle contraction in C. elegans*, Cell, PMID 18191228,
PMC2258244): intestinal Ca oscillations drive a Na+/H+ exchanger, **PBO-4**, on the intestine's basolateral
membrane (apposed to the posterior body muscles), releasing protons that act as the transmitter; **PBO-5**
(with PBO-6) forms a proton-gated cation channel on the muscle side that responds to the acidification -
**this is a non-synaptic, non-peptide chemical transmission step (H+ as transmitter) that is a mechanism in
its own right**, separate from and in addition to the NLP-40 peptide pathway below; both operate in the same
motor program (H+ to posterior body muscle directly; NLP-40 to AVL/DVB neurons). No numeric pH/concentration
values extracted this pass - UNVERIFIED.

**Downstream: NLP-40 to AVL/DVB and the all-or-none expulsion step.** Ca oscillations in the intestine drive
Ca-dependent rhythmic secretion of the neuropeptide **NLP-40** (via the calcium sensor SNT-2/synaptotagmin,
measured mechanism), which activates **AVL and DVB** (GABAergic enteric motor neurons). A 2022 paper,
*C. elegans enteric motor neurons fire synchronized action potentials underlying the defecation motor
program*, Nature Communications 13:2783 (DOI-pattern 10.1038/s41467-022-30452-y, from search), establishes
that **AVL and DVB fire synchronous, all-or-none, calcium-mediated giant action potentials** downstream of
the intestinal pacemaker - i.e. the neural half of the circuit is itself spiking/digital, not graded, which
is a useful simplification for a builder (AVL/DVB can be modelled as a threshold-triggered event, not a
continuous dynamical system, once NLP-40 crosses a release threshold).

**Motor sequence and timing (measured, STATE_OF_THE_ART corpus items 49-52, WormBook Defecation chapter,
Thomas 1990):** three sequential steps - **pBoc** (posterior body-wall muscle contraction, triggered by the
H+ signal above) - **aBoc** (anterior body-wall muscle contraction, ~3 s after pBoc) - **Exp** (enteric
muscle contraction, expulsion) - with overall cycle period **45 s (+/- <3 s at 20C), temperature-insensitive
from 19-30C** (measured, Thomas 1990), and the next DMP occurring 45 s after an experimentally-imposed touch
perturbation (reset behaviour, measured, WormBook).

### Parameter table

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| Defecation cycle period | 45 | 42-50, +/-<3 SD at 20C | s | Thomas 1990 / STATE_OF_THE_ART corpus item 49 | measured |
| Temperature sensitivity of period | none (flat) | 19-30 | C | Thomas 1990 | measured |
| pBoc -> aBoc delay | ~3 | - | s | STATE_OF_THE_ART item 49, WormBook | measured |
| Intestinal cell count in the oscillator | 20 | - | cells | multiple sources above (Cook 2019 node list cross-check) | measured |
| IP3R (ITR-1) rate constants | UNVERIFIED | - | - | Teramoto & Iwasaki 2006 (not opened) | not found - use generic de Young-Keizer/Li-Rinzel values as a bounded placeholder, labelled guessed |
| INX-16 gap conductance | UNVERIFIED | - | nS | Peters et al. 2007 (PDF unreadable) | not found this pass |
| PBO-4/PBO-5 proton signal amplitude/pH | UNVERIFIED | - | - | Beg et al. 2008 (not opened in full) | not found this pass |
| NLP-40 release threshold | UNVERIFIED | - | - | multiple sources above (qualitative only) | not found this pass |

**Cells:** the 20 intestinal cells (int1-int9 by WormAtlas naming, paired bilaterally for most positions), AVL
and DVB enteric motor neurons, posterior/anterior body-wall muscle (shared with row 12), enteric/anal
depressor muscle.

**Simplest nested form:** (1) the fixed 45 s timer already in `layers.defecation` (lumped, current default);
(2) a single lumped IP3R negative-feedback oscillator (2 state variables: cytoplasmic Ca, IP3 or PLC
activity) shared across the 20 cells as one effective compartment, tuned to a 45 s period within the measured
range; (3) 20 separately-coupled IP3R oscillators linked by INX-16 gap junctions, reproducing the
simultaneous-bidirectional wave initiation result; (4) add the PBO-4/PBO-5 proton pathway and NLP-40/AVL/DVB
spiking as two parallel, threshold-triggered downstream readouts of the shared intestinal Ca state.

**Isolated check for the builder:** the free-running period of the lumped oscillator (no sensory/touch input)
should land at 45 s +/- a few seconds and stay flat across a 19-30C range (Thomas 1990) - a unit check on the
oscillator alone, independent of the body or motor output. A falsifier: an `itr-1(lf)` ablation in the model
(zero IP3R flux) must abolish the oscillation entirely (Dal Santo 1999's measured result), not just slow it
down - if the model's rhythm persists without ITR-1, the model has made Ca release non-essential when the
real animal does not.

---

## O4. Egg-laying (PLAN row 15)

**Best model to port: Waggoner et al. 1998's two-state stochastic model for the system level, plus Collins
and Koelle 2013/2016 and Ravi et al. 2018/2021 for the circuit mechanism that produces the two states.** No
single paper gives both a complete stochastic process AND channel-level vulval muscle equations with numeric
parameters; this is a "port the structure, fit the rates" row, as PLAN already labels it.

**System level: Waggoner, Zhou, Schafer and Schafer 1998**, *Control of alternative behavioral states by
serotonin in Caenorhabditis elegans*, Neuron 21(1):203-214 (PMID 9697864, DOI via ScienceDirect
S0896-6273(00)80527-9 - not independently opened full-text this pass, summary from search).
**Egg laying is a two-state random process**: an **active state** (~2 min, measured) during which eggs are
laid in rapid clusters of 4-6, and an **inactive state** (~20 min, measured) during which eggs accumulate and
are retained; serotonin from **HSN** and the **VC4/VC5** motor neurons (and HSN alone sufficient by
single-cell ablation) triggers transition into the active state. This two-state renewal-process structure
(state durations drawn from some distribution, not literally a two-parameter Markov chain - Waggoner's own
phrase is "a novel random process") is the right level for PLAN's "active/inactive states" ask and is cheap
(two state durations plus a within-active-state egg-release sub-process).

**Circuit mechanism and feedback: Collins and Koelle 2013** (*Postsynaptic ERG potassium channels limit
muscle excitability to allow distinct egg-laying behavior states in Caenorhabditis elegans*, Journal of
Neuroscience 33(2):761-775, PMID 23303953) and **Collins, Koelle et al. 2016** (*Activity of the C. elegans
egg-laying behavior circuit is controlled by competing activation and feedback inhibition*, eLife 5:e21126 -
opened directly, no formal equations in the paper, but concrete measured numbers, see table). Mechanism:
**UNC-103 (an ERG-family K+ channel)** keeps vulval muscle Ca subthreshold between active-state bouts by
repolarising after each **EGL-19 (L-type Ca)**-driven depolarisation - i.e. UNC-103 is the gate that converts
a continuously-excitable muscle into a twitching one; loss of UNC-103 collapses the two-state behaviour into
continuous egg-laying (measured phenotype, Collins & Koelle 2013). Negative feedback: **uv1 neuroendocrine
cells release tyramine**, acting through the **LGC-55** receptor on HSN, inhibiting HSN and ending the active
state (measured mechanism, Collins et al. 2016) - this is the "uv1 tyramine/NLP-7 feedback" PLAN asks for;
**NLP-7** itself was not independently verified as uv1's peptide in this pass (uv1 is also reported to release
NLP-7 in other sources not opened here - UNVERIFIED which specific peptide pairs with which specific feedback
loop).

**Vulval muscle Ca linked to body bends: Ravi et al. 2018a** (histamine-gated-Cl transgenic manipulation of
vulval muscle excitability) **and Ravi et al. 2018b/2021** (titles not independently opened this pass, cited
via search summary; likely bioRxiv/J Neurosci pieces on vm1/vm2 Ca imaging during locomotion): vulval muscle
Ca activity shows **distinct rhythmic transients tied to body bends** even outside the egg-laying active
state (twitches), and **retrograde Ca-dependent feedback from vulval muscle to presynaptic HSN** modulates
HSN's own activity and the active-state transition - i.e. the circuit has a stretch/activity feedback loop in
both directions (HSN/VC -> muscle -> HSN), not a single feedforward command. **No numeric Ca amplitude,
delay, or coupling-strength values were extracted this pass - UNVERIFIED.**

### Parameter table

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| Active-state duration | ~2 | - | min | Waggoner 1998 | measured |
| Inactive-state duration | ~20 | - | min | Waggoner 1998 / Collins 2016 | measured |
| Eggs laid per active-state cluster | 4-6 | - | eggs | Waggoner 1998 | measured |
| HSN inter-transient interval, active state | 17 | +/- 2 (SEM) | s | Collins et al. 2016 | measured |
| HSN inter-transient interval, inactive state | 41 | +/- 5 (SEM) | s | Collins et al. 2016 | measured |
| VC inter-transient interval | ~10 | - | s | Collins et al. 2016 | measured |
| Vulval muscle twitch frequency | ~50 | - | mHz | Collins et al. 2016 | measured |
| Basal egg-laying rate | 1-3 | - | eggs/hr | STATE_OF_THE_ART corpus item 43 (Comm Biology 2022) | measured |
| Serotonin/nicotine-stimulated rate | ~7.4 | - | eggs/hr | STATE_OF_THE_ART corpus item 44 | measured |
| Peak adult rate | up to ~9 | - | eggs/hr | STATE_OF_THE_ART corpus item 45, ~92 h post-hatch | measured |
| Brood size | ~300 | - | eggs/animal | STATE_OF_THE_ART corpus item 47, Byerly 1976 | measured |
| UNC-103/EGL-19 channel conductances | UNVERIFIED | - | - | Collins & Koelle 2013 (not opened in full) | not found this pass |
| Tyramine/LGC-55 feedback strength | UNVERIFIED | - | - | Collins et al. 2016 (qualitative only) | not found this pass |

**Cells:** HSNL/HSNR, VC1-VC6 (VC4/VC5 specifically implicated), vm1/vm2 vulval muscles, uv1 neuroendocrine
cells, germline/uterus (egg production rate, lumped).

**Simplest nested form:** (1) the current fixed two-state timer with a random laying rate (what
`layers.egg_laying` already does, lumped, default on); (2) Waggoner's two-state renewal process with measured
state durations (2 min active / 20 min inactive) and a within-active-state Poisson-ish egg-release
sub-process at the measured HSN/VC inter-transient intervals (17 s / 10 s); (3) add the UNC-103/EGL-19
vulval-muscle channel pair so the two states emerge from the channel dynamics rather than being imposed by a
timer, plus the uv1-tyramine-to-HSN feedback loop; (4) add the Ravi et al. retrograde vulval-muscle-to-HSN Ca
feedback and body-bend coupling once the base circuit is validated.

**Isolated check for the builder:** a model run with no stimulus should spend close to 2 min / 20 min
(active/inactive) on average, each eggs-per-active-bout cluster 4-6 (Waggoner 1998, measured) - a unit check
on the state-timer alone. A second check: removing UNC-103 from the model should collapse the two-state
pattern into continuous twitching/egg release (Collins & Koelle 2013's measured phenotype) - if the two-state
pattern survives UNC-103 removal, the model has not located the actual gate.

---

## O5. Glia (PLAN row 11)

**No quantitative C. elegans glial model with numeric kinetic parameters was found this pass.** Every
C. elegans glia source found is mechanistic/qualitative (which transporter, which cell, which phenotype) with
no fitted rate constants - consistent with PLAN row 11's own label ("mechanisms inferred, parameters fitted,
borrow mechanism not values from other invertebrates") and with MECHANISMS_AUDIT's "spec only" status for
this row today. The best move is exactly what PLAN already prescribes: port the mechanism structure from the
C. elegans papers below, and borrow a generic (leech/mammalian astrocyte) quantitative K+/Cl- buffering model
for the actual rate constants, labelled inferred/guessed.

**AMsh glia and AFD thermosensory microvilli: Singhvi, Liu, Friedman, Fong, Lu, Huang et al. 2016**, *A glial
K/Cl transporter controls neuronal receptive ending shape by chloride inhibition of an rGC*, Cell
165(4):936-948 (opened via search summary, not full text - mechanism confirmed, no numeric Cl- concentration
or rate given in the summary). Mechanism: the amphid sheath (AMsh) glial cell expresses **KCC-3** (a K+/Cl-
cotransporter) specifically in the sub-apical domain surrounding **AFD** neuron microvilli (absent from the
region around AWC or other amphid neurons - cell-type-specific sub-cellular localisation, not just cell-type
specific expression). KCC-3 controls the local extracellular Cl- concentration, and **Cl- directly inhibits
GCY-8**, an AFD-specific receptor guanylyl cyclase, by binding an S(x)nGPxC motif in GCY-8's extracellular
domain - i.e. the glial transporter sets a chemical (not electrical) modulatory tone on a specific sensory
transduction enzyme. `kcc-3` mutants have thermotaxis defects (measured phenotype) and altered AFD neuron
receptive-ending shape (structural, not just functional, effect). A **2024 follow-up, Ray et al.**, *Neuron
cilia restrain glial KCC-3 to a microdomain to regulate multisensory processing*, Cell Reports (DOI pattern
S2211-1247(24)00172-4), refines this: AFD's own cilium restrains KCC-3 to its correct microdomain, and
disrupting that restraint causes cross-talk between AFD and neighbouring sensory endings (AWC) sharing the
same glial cell - i.e. the glial compartment is not fully sealed per-neuron, a finding relevant if ASH/AWC
cross-modulation (PLAN's other ask for this row) is modelled through the same glial cell.

**GLR glia, RME and muscle arms: a 2016/2017 eLife paper** (title from search: *Regulation of neuronal axon
specification by glia-neuron gap junctions in C. elegans*, eLife, PMC5083064). GLR glial sheet processes form
**gap junctions directly onto head muscle cells and onto RME motor neurons**; gap-junction signalling
(calcium-dependent, through a calpain CLP-4, activating a CDK-5 pathway) regulates RME's axon specification
during development - this is a developmental/structural role, not an ongoing adult signalling role, so it may
be out of scope for an adult-snapshot model (same caveat PLAN gives for row 19, gene-expression-as-a-fixed-
parameter).

**CEPsh glia, sleep and dopamine:** per the Shaham lab's own review material and a cited paper ("Glia modulate
a neuronal circuit for locomotion suppression during sleep", Shaham lab PDF, not independently opened full
text) CEPsh glia modulate locomotory quiescence during sleep and modulate dopamine-dependent behaviours;
**no quantitative mechanism or parameter found this pass - UNVERIFIED, mechanism only.**

**Cross-species fallback for the actual numbers (since C. elegans itself has none, as instructed by the
task brief):** mammalian astrocyte **Kir4.1-mediated K+ spatial buffering** gives measured extracellular K+
recovery time constants after stimulation of **tau ~ 0.3-6 s** depending on preparation and channel block
(wild-type ~4.2 s, Kir4.1 conditional knockout ~6.3 s, a tri-compartment neuron/astrocyte/extracellular model
fit at ~0.7 s for a single stimulation, PLoS Comp Biol 10.1371/journal.pcbi.1004137 and related sources found
this pass). **This is an inferred cross-species bound, not a C. elegans measurement** - use it only as a
guessed order-of-magnitude range for a KCC-3/Cl- clearance time constant around AFD microvilli until a direct
C. elegans number is found.

### Parameter table

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| KCC-3 Cl- clearance time constant (worm) | not found | - | - | Singhvi 2016 (mechanism only) | not found this pass |
| Astrocyte K+ clearance tau (cross-species fallback) | 0.7-6.3 | 0.3-6.3 | s | mammalian Kir4.1 literature (PLoS Comp Biol 2015 and others, see above) | inferred (cross-species, bounded, not C. elegans-specific) |
| GLR-RME gap junction conductance | not found | - | - | eLife PMC5083064 (mechanism only) | not found this pass |
| Current code's glia_gain multiplier | 1 (off by default, a constant) | - | - | `layers.sensory_current`, ledger row "glia" | guessed (per MECHANISMS_AUDIT row 11) |

**Cells:** AMsh (2 cells), CEPsh (4 cells), GLR (6 cells) as the first-priority glia named in the task; the
other 44 of the 56 total glia (per STATE_OF_THE_ART's count) are not covered by any source found this pass.

**Simplest nested form:** (1) current constant `glia_gain` multiplier on sensory current (spec only, no
state); (2) a single extracellular Cl- (around AFD) or K+ (around GLR-coupled neurons) compartment per glial
cell with linear clearance at the cross-species tau above, modulating the relevant channel (GCY-8 for AFD) or
coupled neuron's reversal potential; (3) add the cilium-restrained-microdomain structure (Ray 2024) so AFD and
AWC can cross-talk through a shared, imperfectly-compartmentalised glial cell.

**Isolated check for the builder:** none available from C. elegans data directly (no quantitative dataset
found this pass to check against) - the nearest available check is qualitative: a `kcc-3` null in the model
should shift AFD's thermosensory dose-response curve and/or receptive-ending shape (Singhvi 2016's measured
phenotype), not merely scale its gain uniformly, since the mechanism is a local Cl--to-GCY-8 inhibition, not a
generic sensitivity knob.

**Note back to O1 (muscle-muscle gap junctions):** while researching this section, found a directly relevant
correction to O1's "no published muscle-muscle gap value" statement: **Liu, Chen, Altun, Gross, Shan, Schuman,
Hall and Wang 2013**, *Six innexins contribute to electrical coupling of C. elegans body-wall muscle*, PLoS
ONE 8(10):e76877, DOI [10.1371/journal.pone.0076877](https://doi.org/10.1371/journal.pone.0076877) (opened
directly via PMC3793928), measured **junctional conductance (Gj) between ventral body-wall muscle cell
pairs directly** and found **UNC-9, INX-1, INX-10, INX-11, INX-16 and INX-18** mutants all show a
significant decrease in Gj vs wild type (i.e. all six contribute to the measured coupling; exact absolute Gj
numbers in pS/nS were not extracted from the summary available this pass - UNVERIFIED pending a full-text
read, but the six-innexin identity and the qualitative "mutants reduce Gj" result are measured). This directly
fills the gap flagged in O1 ("no non-zero published muscle-muscle gap conductance found") - a builder should
read this paper's Methods/Results tables directly for the Gj numbers before falling back to a guessed value.

---

## O6. Other non-neural cells: hypodermis/seam, excretory canal, coelomocytes (PLAN row 16)

**No single published model covers all three; each has a different literature with, again, mostly mechanism
and no fitted kinetic parameters found this pass.** PLAN row 16 itself only asks for a lumped lump "where
they carry state" - the finding below supports treating this row as mechanism-with-bounded-guessed-rates,
not a port of a specific paper's numbers.

**Hypodermis and seam cells - electrical role.** Three innexins (**INX-8, INX-11, INX-12**) are detected in
seam cells, co-expressed in the hypodermis, with **INX-5** also expressed in both; seam cells are linked to
the surrounding hypodermal syncytium by gap junctions on their lateral membranes (measured anatomically,
WormAtlas gap junction pages and the Altun 2009 innexin map, same source already cited in STATE_OF_THE_ART
s2). **No search result found hypodermis/seam gap junctions coupling directly to muscle or neurons** (the O1
correction above, Liu et al. 2013, covers muscle-muscle coupling specifically, not hyp-muscle); MECHANISMS_AUDIT's
own stand-in test network (c302_port.md's "the hypodermis, 57 partners, AIY-sized" used as a worst-case
coupling stress test) implies the Cook 2019 graph *does* give the hypodermis many gap-junction partners, but
no source found this pass characterises the biophysics of those connections. **Treat hypodermis/seam
electrical coupling to muscle/neurons as structurally present (from Cook 2019 counts, already in the ledger)
but biophysically unparameterised - guessed conductance, bounded by the measured UNC-9 range already used
for neuron-neuron gaps (row 8).**

**Excretory canal osmoregulation.** Mechanism (qualitative, measured at the gene level, not kinetically):
water enters the canal lumen through **AQP-8** (an aquaporin, exclusively expressed in the excretory cell);
increased luminal osmotic pressure drives luminal expansion; **CLH-3** (and **CLH-4**) chloride channels set
the ion gradient; **WNK-1** positively regulates the kinase **GCK-3**, which negatively regulates CLH-3
activity - a WNK-kinase-to-chloride-channel cascade structurally identical to the vertebrate WNK/SPAK/OSR1
osmoregulatory pathway (a plausible cross-species mechanism match, though not independently confirmed as
homologous regulation in this pass - inferred). **No volume, pressure or time-constant number was found this
pass for the canal itself** - UNVERIFIED/not found. The canal must regulate its own lumen diameter (too
narrow blocks flow, too wide loses pressure, a stated structural constraint, [PMC7557474](https://pmc.ncbi.nlm.nih.gov/articles/PMC7557474/))
but no explicit setpoint or feedback-gain value was located.

**Coelomocytes.** Six scavenger cells, anatomically fixed, that **continuously and non-specifically
endocytose** pseudocoelomic fluid (no phagocytosis, endocytosis only - measured, multiple sources). The
standard assay (**Fares and Greenwald 2001**, *Genetics* 159:133-145, the ssGFP/`pmyo-3::ssGFP` secretion-and-
uptake assay used throughout the field, including the later CUP - Coelomocyte Uptake Defective - screen that
found 14 genes) demonstrates uptake and lysosomal degradation occur, with the *rate* read out qualitatively
(GFP accumulates in the body cavity when uptake is slowed, clears into coelomocytes when normal) rather than
as a fitted half-life. **No numeric uptake rate (molecules/s, or a half-life in minutes) was found this
pass - not found, UNVERIFIED.** CUP-4 (a receptor), DYN-1 (a fission GTPase) and TAX-6/CNB-1 (a calcineurin
regulator of DYN-1) are the named molecular players (ScienceDirect/PMC sources above, mechanism only, no
fitted rate).

### Parameter table

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| Seam/hypodermis innexins | INX-5, INX-8, INX-11, INX-12 | - | - | WormAtlas/Altun 2009 gap junction map | measured (identity only, no conductance) |
| Muscle-muscle Gj-contributing innexins | UNC-9, INX-1, INX-10, INX-11, INX-16, INX-18 | - | - | Liu et al. 2013 (PMC3793928) | measured (identity; absolute Gj value not extracted this pass) |
| Hyp/seam-to-muscle/neuron gap conductance | not found | bound by row 8's neuron-neuron UNC-9 range | nS | none found this pass | guessed |
| Excretory canal AQP-8 water permeability | not found | - | - | multiple sources, mechanism only | not found this pass |
| Excretory canal volume/pressure time constant | not found | - | s | none found this pass | not found this pass |
| Coelomocyte endocytic uptake rate | not found | - | molecules/s or 1/s | Fares & Greenwald 2001 (qualitative assay only) | not found this pass; a bounded guess of minutes-to-tens-of-minutes turnover is reasonable by analogy to generic constitutive fluid-phase endocytosis in other systems, but this is a guess, not a C. elegans number |
| Coelomocyte count | 6 | - | cells | multiple sources | measured |
| Excretory canal cell count | 1 (H-shaped single cell) | - | cells | WormAtlas/PMC7557474 | measured |

**Cells:** hypodermis (a syncytium, hyp7 the largest), 16 seam cells, 1 excretory canal cell (plus duct and
pore cells, not separately covered), 6 coelomocytes.

**Simplest nested form:** (1) anatomy only, no dynamics (current state, "missing" per MECHANISMS_AUDIT row
16); (2) a single lumped pseudocoelomic fluid-volume/pressure state fed by the excretory canal (a slow
integrator against a setpoint) and a single lumped clearance-rate state for all coelomocyte-cleared peptides/
molecules (an exponential decay, rate guessed and bounded), both read by other rows (body pressure feeds row
21; peptide clearance feeds row 9's "degradation" term); (3) add structural gap-junction coupling between
hypodermis/seam and muscle/neurons at a guessed, bounded conductance, read from the Cook 2019 counts already
in the ledger.

**Isolated check for the builder:** none quantitative found this pass. The qualitative check available: a
`cup-4` or `dyn-1` loss-of-function in the model should visibly slow pseudocoelomic clearance of an injected
tracer (the direction Fares & Greenwald's assay reads out), not merely change coelomocyte morphology.

---

## O7. Metabolism (PLAN row 20)

**Best model to port: the Add-my-Pet (AmP) project's already-fitted Dynamic Energy Budget (DEB) model for
Caenorhabditis elegans - a direct, numeric, open-data hit, better than expected going in.** This is exactly
the kind of "port, don't build" target the task brief wants: a standard DEB model (Kooijman's formalism,
originating with Jager et al. 2005's application of DEB theory to C. elegans toxicology) with parameters
*already fitted to C. elegans life-history data* by the AmP project and published openly.

**Model: standard DEB "abj" model (Kooijman formalism)**, fitted entry at
`bio.vu.nl/thb/deb/deblab/add_my_pet/entries_web/Caenorhabditis_elegans/` (opened directly). State variables
in the standard DEB model: structural body volume/length, a reserve energy density [E], and a maturity/
reproduction buffer; dynamics: assimilation (surface-area-scaling intake) feeds the reserve, a fixed fraction
**kappa** of reserve mobilisation funds somatic maintenance and growth, the rest funds maturity maintenance
and reproduction. **Open code: yes.** DEBtool (Matlab, GPL-ish - licence not independently re-verified this
pass) implements the standard model and the parameter-estimation pipeline; AmPtool supports using the
collection directly. **Original application to C. elegans toxicology: Jager, Albert, Preuss, Klok, Kammenga
2005** (exact title/journal not independently re-opened this pass, cited via PLAN.md's own row 20 entry
instead - treat the AmP entry as the current, maintained version of that lineage, since AmP absorbed many
species-specific DEB fits including worm ones post-2005).

### Parameter table (at T_ref = 20C, from the AmP C. elegans entry, opened directly)

| Name | Value | Units | Meaning | Source | Label |
|---|---|---|---|---|---|
| v (energy conductance) | 0.03208 | cm/d | sets growth/reserve-turnover rate | AmP C. elegans entry | published fit |
| p_M (volume-specific somatic maintenance) | 3724 | J/(d*cm^3) | maintenance cost per unit structural volume | AmP C. elegans entry | published fit |
| k_J (maturity maintenance rate coefficient) | 0.002 | 1/d | | AmP C. elegans entry | published fit |
| k (maintenance ratio, = k_J/k_M derived) | 0.0009726 | dimensionless | | AmP C. elegans entry | published fit |
| kappa (allocation fraction to soma) | 0.5056 | dimensionless | fraction of mobilised reserve to soma, rest to maturity/reproduction | AmP C. elegans entry | published fit |
| kappa_G (growth efficiency) | 0.8086 | dimensionless | | AmP C. elegans entry | published fit |
| kappa_R (reproduction efficiency) | 0.95 | dimensionless | | AmP C. elegans entry | published fit |
| Fit quality SMSE / MRE | 0.109 / 0.242 | dimensionless | standardised mean squared error / mean relative error of the fit to the underlying data | AmP C. elegans entry | published fit (goodness-of-fit) |
| Whole-animal O2 consumption (basal, wild type) | <5, one study 13.8 +/- 2.5 | pmol/min/worm | | Sarasija et al., AMC respirometry protocol (amc.edu PDF found this pass); JoVE 59277 | measured |
| O2 consumption (sel-12 mutant, for calibration contrast) | ~7 | pmol/min/worm | | same source | measured |
| iCEL1273 genome-scale model size | 1,273 genes, 623 enzymes, 1,985 reactions | - | check only, not run per step (per PLAN's own row 20 treatment) | Yilmaz & Walhout 2016, Cell Systems (already in STATE_OF_THE_ART s2) | measured |

**Fat storage, satiety, insulin/TGF-beta/serotonin outputs:** not separately parameterised by the DEB model
(DEB's "reserve" state is a lumped energy density, not literally fat droplets); PLAN's own ask for fat
mobilisation and insulin/TGF-beta/serotonin output signals is better served by treating the DEB reserve state
[E] as the single number that gates those three pathways (low reserve -> higher insulin/DAF-16 signalling,
etc.), each gating function labelled guessed/inferred until fit. **You, Kim, Raizen & Avery 2008** (satiety
quiescence, already in STATE_OF_THE_ART corpus item 40) and the general insulin/DAF-16, TGF-beta/DAF-7
literature (corpus items 31, 37, 40, 63, 69) are the qualitative sources for which pathways to gate; no
single paper found this pass gives a quantitative fat-to-insulin-output transfer function for C. elegans
specifically.

**Cells/scope:** whole-animal lumped (DEB models are explicitly organism-level, not tissue-resolved); the
MERGE model (Yilmaz 2020, already in STATE_OF_THE_ART) is the nearest tissue-resolved alternative if
per-tissue (muscle/intestine/hypodermis) flux is needed instead of a single whole-animal energy budget.

**Simplest nested form:** (1) the current single energy-store integrator (`layers.metabolism`, spec only,
nothing reads it); (2) the full standard DEB model above as a single whole-animal reserve/structure/maturity
system, fed by the pharynx's pumping rate (row 13) as the assimilation input, with kappa/kappa_R routing
reserve to growth vs. reproduction (feeding row 15's egg production rate directly); (3) add explicit gating
functions from the DEB reserve state to insulin/DAF-16, TGF-beta/DAF-7 and serotonin output levels, each
bounded and guessed pending a fit; (4) cross-check the whole model's steady-state flux predictions against
the iCEL1273/MERGE genome-scale models as a consistency check, not a per-step computation (as PLAN already
specifies).

**Isolated check for the builder:** run the DEB model alone (no body, no brain) from hatching and check it
reproduces the standard life-history outputs the AmP fit was scored against - generation time ~3.5 days at
20C and brood size ~300 (STATE_OF_THE_ART corpus items 47-48, both independently measured/cited elsewhere in
this project) - against the AmP entry's own reported SMSE/MRE (0.109/0.242) as the expected residual, not
zero. A unit check on whole-animal O2 consumption: the model's assimilation-driven dissipation flux, when
converted to O2 via a standard respiratory quotient, should land within the measured 5-14 pmol/min/worm
range above - a check on the energy budget's absolute scale, independent of growth or reproduction.

---

## O8. Body: cuticle, pressure, viscoelasticity (PLAN row 21)

**Already extensively researched by this project** (`docs/worm/research/BODY.md`, read in full for this
task; and the body worker's `HANDOFF_BODY.md`/`BODY_TESTS.md`, also read in full) - this section summarises
and does not repeat that work, adding only the specific "cuticle as a separate layer" gap PLAN asks about
here and cross-checking it was not missed.

**Model already chosen and ported: MetaWorm's (BAAIWorm commit b99ca5ab, Apache 2.0) tetrahedral FEM body**,
solved with projective dynamics (not standard stiff FEM), already running in this codebase at
`third_party/metaworm` / `src/wormemu/body/metaworm.py`, per `HANDOFF_BODY.md`. **This is a single
homogeneous elastic material** (MECHANISMS_AUDIT row 21: "One homogeneous elastic material (no separate
cuticle) and no internal pressure") - i.e. PLAN's specific ask for "cuticle as a separate layer" and
"internal hydrostatic pressure" are **both currently unmet gaps in the already-ported body**, not just
unresearched; BODY.md section 1 already explains *why* a single bulk modulus cannot reproduce all four kinds
of stiffness measurement (AFM, whole-body bending, layer-resolved FE inversion, direct pressurisation) at
once - the biology genuinely has (at least) two separate mechanical compartments (cuticle shell, pressurised
core), and BODY.md's own recommendation already states this: "A 3D model needs both a cuticle shell term and a
pressure-dominated core term; a single bulk modulus cannot reproduce all four kinds of measurement at once."

**The layer-resolved finite-element paper is the best port target for a two-layer (or three-layer) cuticle +
muscle + pseudocoelom structure with numbers already fitted**: [Frontiers in Bioengineering and
Biotechnology 2024](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1335788/xml/nlm),
already opened and cited in BODY.md: fits a multi-compartment FE model (cuticle shell, muscle layer,
pseudocoelom core) to combined indentation/pressure data, giving **cuticle 75-140 kPa, muscle 600-850 kPa
(individual-worm variation 910-2,100 kPa), pseudocoelom 48-185 kPa (variation 42-275 kPa)** - all measured/
fitted, already tabulated in BODY.md section 1. This is the direct numeric answer to PLAN's "cuticle as a
separate layer (stiffness ... by method)" ask; Park et al. 2007 PNAS (piezoresistive microcantilever, hollow
cylindrical shell model) is the direct answer to "internal hydrostatic pressure (measured values)": ranges
found span **50-100 kPa (older estimates) to 150-200 kPa (newer FE-based estimates)**, flagged in BODY.md as
**measured but unreconciled across sources** - a genuine open conflict, not a simple gap.

**Viscoelasticity: Backholm, Ryu and Dalnoki-Veress 2013**, PNAS 110(10):4528-4533 (already cited and opened
in BODY.md): whole-body bending gives an effective modulus of **110 +/- 30 kPa**, with damping that **falls
as a power law over two decades of bending speed** (shear-thinning, non-Newtonian), **better fit by a Maxwell
model than Kelvin-Voigt or elastic beam theory** - BODY.md already flags that the body's current damping (a
fixed linear Kelvin-Voigt-style coefficient, if that is what MetaWorm's FEM uses - not independently
re-checked in this pass) is "a known-wrong simplification, useful only as the project's own required
deliberately-wrong control" (DECISIONS item 2 in PLAN.md).

**Sibernetic's own parameters** (already extracted in BODY.md section 3, not repeated numerically here):
500,000 particles (full resolution) / 81,000 (half resolution) SPH, 96 muscles in 4 quadrants, validated
against measured crawl/swim speed, wavelength and frequency (BODY.md's 6-row table) - this table **is** the
concrete target for "validated against Sibernetic's published results" per PLAN's own DECISION 4, already
flagged as ready to use with no further literature work needed (BODY.md section 4, point 3).

### Parameter table (summarising BODY.md; see that file for full citations)

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| Cuticle modulus (layer-resolved FE) | 75-140 | up to 910-2,100 for muscle individual variation band | kPa | Frontiers Bioeng 2024 | measured/fitted |
| Muscle layer modulus (layer-resolved FE) | 600-850 | 910-2,100 individual variation | kPa | Frontiers Bioeng 2024 | measured/fitted |
| Pseudocoelom modulus (layer-resolved FE) | 48-185 | 42-275 individual variation | kPa | Frontiers Bioeng 2024 | measured/fitted |
| Cuticle modulus, AFM point indentation | 8-2000 (or 200-400 MPa if cuticle-only assumption) | - | kPa | Essmann et al. 2020 Nat Commun | measured |
| Whole-body bending modulus | 110 +/- 30 | - | kPa | Backholm, Ryu & Dalnoki-Veress 2013 PNAS | measured |
| Internal hydrostatic pressure | 50-200 (unreconciled across sources) | 50-100 older / 150-200 newer FE | kPa | Park et al. 2007 PNAS; Frontiers 2024; bioRxiv 2023.11.09.566289 | measured, unreconciled |
| Body mass density | 1.07-1.08 | - | g/cm^3 | Shifts in Mass Densities, PLOS ONE 2013 | measured |
| MetaWorm body: scale, mass | worm_1mm scale; mass 2.13 ug | density 1074 kg/m^3 (inside 1070-1080) | - | HANDOFF_BODY.md, already ported/running | published (MetaWorm's own, within the measured density range) |
| MetaWorm published E, Poisson, muscle stiffness, mass (original units) | E 2e5, Poisson 0.4, muscle stiffness 5e5, mass 10 | - | MetaWorm's own unit system | HANDOFF_BODY.md / BODY_TESTS.md | published (BAAIWorm's own tuned values) |
| Agar RFT drag coefficients (c_t, c_n) | 3.2, 128 | - | Pa s | HANDOFF_BODY.md, Boyle Berri Cohen 2012-derived, K=40 | inferred |

**Cells/scope:** whole-body continuum, not per-cell; relevant to rows 1 (muscle), 12 (EC coupling force
output), and all of row 21-22.

**Simplest nested form:** this is already staged in the running code per `HANDOFF_BODY.md`'s "Next" list:
(1) homogeneous elastic body, no pressure (current state, running); (2) add a separate cuticle shell material
at the Frontiers-2024 cuticle modulus (75-140 kPa) wrapping the current homogeneous core; (3) add explicit
internal pressure (toggle `body.pressure`, named but not built per MECHANISMS_AUDIT row 21 and
`HANDOFF_BODY.md`'s "Next" item 5, "Sibernetic toggles... each with its own pre-registration"); (4) replace
the linear/Kelvin-Voigt damping (if present) with a Maxwell-type, power-law shear-thinning damping per
Backholm 2013.

**Isolated check for the builder:** these are already pre-registered and partly run - see `BODY_TESTS.md`'s
D1-D3 (dead-worm energy decay), P0-P3 and the solver_exit gate (already FAILED and recorded, published solver
kept as default) - a new cuticle/pressure layer should be checked the same way: a static indentation test
against the Frontiers-2024 layer-resolved numbers (75-140 kPa cuticle response under a point load) is a unit
check independent of locomotion.

---

## O9. Environment fields (PLAN row 22)

**Viscoelastic media (gelatin/agar gait-vs-medium data) is already fully covered by this project's own
BODY.md** section 2 (Fang-Yen 2010 Table 1 numbers, Berri 2009's gait continuum, resistive-force-theory
anisotropy ratios) - not repeated here. This section covers the fields BODY.md does not: food lawn/O2
depletion, salt gradients, temperature gradients, and mechanical stimuli (tap, gentle touch) force values.

**Food lawn and O2 depletion: Demir, Kadakia, Fawzi Aoudi, Yakman and Kocabas 2020**, *Dynamics of pattern
formation and emergence of swarming in Caenorhabditis elegans*, eLife 9:e52781, DOI
[10.7554/eLife.52781](https://doi.org/10.7554/eLife.52781) (opened directly). **This is the best port
target for PLAN's food-lawn/O2 field ask: a coupled PDE model with numeric parameters, matching exactly the
structure needed** (worm density W, oxygen concentration O, coupled by aerotaxis):

- Worm transport: `dW/dt = div(D_W * grad(W)) + div(beta_W * grad(O))` - a random-walk diffusion term plus an
  oxygen-gradient-driven drift (aerotaxis) term.
- Oxygen kinetics: `dO/dt = D_O * laplacian(O) + f*(O_am - O) - kc*W` - diffusion, penetration from the air
  above the plate toward the atmospheric value O_am, and consumption proportional to worm (and implicitly
  bacterial) density.
- Aerotactic coupling coefficient `beta = V^2 * tau * dV/dO`, where V is an oxygen-dependent run speed and tau
  a tumbling rate.
- **Open code: not found this pass** (no repository link located; UNVERIFIED).
- Parameters (measured/fitted, opened directly): D_O = 2e-5 cm^2/s, f = 0.65 /s, kc = 7.3e-10 /s, tumbling
  rate tau = 0.5 /s, worm density range in the fitted regime 1-90 worms/mm^2.
- Qualitative cross-check (search summary, not independently opened in full): the OP50 lawn's bacterial
  metabolism creates a radial O2 gradient, lowest O2 at the lawn rim where bacterial density is highest;
  within dense aggregates O2 can drop below 0.1% (measured, same search pass); worms are attracted to lower O2
  as a food-finding proxy (measured behaviour, aerotaxis literature already in STATE_OF_THE_ART corpus item
  23).

**Salt gradients: standard chemotaxis assay geometry and diffusion constant**, found via search of the
methods sections used across the Bargmann-lab-derived literature (not independently traced to one single
primary citation this pass - **UNVERIFIED attribution**, but the numbers themselves are a widely-repeated
standard): NaCl diffusion coefficient **D = 1.5e-5 cm^2/s**, assay plate **9 cm diameter, agar depth ~0.18-0.264
cm** (two slightly different depths found across different search snippets - treat as "roughly a few mm,
exact value assay-specific"), concentration computed as the solution of the diffusion equation for a point
bolus in a cylindrical aqueous volume with the plate's own dimensions. This is directly implementable as a
2D (or thin-3D) diffusion PDE with a point or line source, standard numerics, no further model needed - the
mechanism is just Fickian diffusion, not a worm-specific model.

**Temperature gradients:** thermotaxis assays use either a **linear gradient (0.5 C/cm, measured, used to
quantify accumulation)** or a **radial (non-uniform, non-linear) gradient on a standard 9 cm plate** (Mori and
Ohshima 1995, already cited in STATE_OF_THE_ART corpus item 28); the radial assay's exact degree-per-cm
profile was not extracted this pass (depends on the specific heating/cooling apparatus at the plate edges) -
UNVERIFIED beyond "radial, non-linear, 9 cm plate."

**Mechanical stimuli:**
- **Tap** (plate-tap assay, STATE_OF_THE_ART corpus items 15-17): the tapper delivers **~1-2 N** per tap to
  the side of the plate (measured, search summary of tap-withdrawal methods literature), transmitted through
  the dish and agar - a mechanical impulse/acceleration applied to the whole plate, not a local force on the
  worm; this needs the plate's own vibrational/acceleration transfer function, not just a force number, to be
  applied correctly as a stimulus to a body model (not located further this pass).
- **Gentle touch (eyebrow/eyelash hair pick): Pruitt lab / Krieg et al.** (title from search: *Forces applied
  during classical touch assays for Caenorhabditis elegans*, PLOS ONE 12(7):e0178080, DOI
  10.1371/journal.pone.0178080, opened directly) **measured the actual forces human experimenters apply**:
  eyebrow-hair force **median 26 uN, mean 61 uN** across volunteers, against a measured **behavioural
  saturation threshold of ~2 uN** (i.e. classical touch assays apply 10-30x more force than needed to
  saturate the reversal response - an important calibration fact: using the *assay's* force as a model input
  would badly overdrive the touch-receptor model; use the saturation value, 2 uN, as the relevant physiological
  scale instead). Hair stiffness itself varies 0.067-0.41 N/m across individual eyebrow hairs (a 6x spread),
  which is the main source of the 26-61 uN spread in applied force at a fixed hand motion.

### Parameter table

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| O2 diffusion coefficient (agar/plate) | 2e-5 | - | cm^2/s | Demir et al. 2020 eLife | measured/fitted |
| O2 penetration rate (air to agar) | 0.65 | - | 1/s | Demir et al. 2020 | fitted |
| O2 consumption rate coefficient (per worm/bacteria density) | 7.3e-10 | - | 1/s (per unit density) | Demir et al. 2020 | fitted |
| Worm tumbling rate | 0.5 | - | 1/s | Demir et al. 2020 | fitted |
| Worm density range (model validity) | 1-90 | - | worms/mm^2 | Demir et al. 2020 | measured |
| NaCl diffusion coefficient | 1.5e-5 | - | cm^2/s | standard chemotaxis-assay methods (attribution UNVERIFIED) | measured (widely used standard value) |
| Chemotaxis plate diameter | 9 | - | cm | same | measured (standard assay) |
| Chemotaxis agar depth | 0.18-0.264 | - | cm | same (two values found, not reconciled) | measured |
| Linear thermotaxis gradient | 0.5 | - | C/cm | thermotaxis assay literature | measured |
| Tap force | 1-2 | - | N | tap-withdrawal methods literature | measured |
| Gentle-touch behavioural saturation force | 2 | - | uN | Krieg/Pruitt, PLOS ONE 2017 (0178080) | measured |
| Gentle-touch assay-applied force (eyebrow hair, classical method) | 26 (median), 61 (mean) | 10-30x the saturation value | uN | same | measured |
| Eyebrow hair stiffness | 0.067-0.41 | - | N/m | same | measured |

**Cells:** sensory transduction layer (row 17) is the consumer of all these fields; the fields themselves are
environment state, not cells.

**Simplest nested form:** (1) constant plate-wide values (current state, MECHANISMS_AUDIT row 22: "Temperature,
O2/CO2, food lawn, salt, touch and tap are constants or zero"); (2) static spatial gradients (linear
temperature, Fickian point-source salt diffusion, both cheap closed-form or simple PDE solves, no worm
feedback); (3) the Demir et al. 2020 coupled worm-density/O2 PDE pair for the food-lawn/O2 case specifically
(this one needs worm feedback into the field, since worms deplete O2 themselves); (4) full multi-field plate
(temperature + salt + O2 + food lawn simultaneously, each its own PDE, summed sensory drive at the worm's
nose position, already the structure of `body/scene.py`'s existing single cone field per HANDOFF_BODY.md -
extending it to multiple simultaneous fields is the natural next step).

**Isolated check for the builder:** a point-source NaCl diffusion simulation alone (no worm) should match
the standard assay's reported concentration-vs-distance-vs-time curve at the stated diffusion coefficient
(1.5e-5 cm^2/s) - a textbook diffusion-equation check, independent of any sensory model. For the O2/food-lawn
field: with worm density clamped at a fixed, uniform value (no aerotaxis feedback), the O2 field should relax
to the steady state `O_ss = O_am - kc*W/f` from the Demir et al. 2020 equation - a closed-form unit check on
the field equation alone.

---

## O10. Observation models (PLAN row 23)

**GCaMP kinetics are well published with exact numbers for every variant named in the task; NeuroPAL error
rates likewise; the Randi 2023 optogenetic actuator is comparatively under-characterised (the source itself
calls it "unconventional" and "less well characterized").**

**GCaMP6s / GCaMP6f (used widely, including as the imaging indicator in TWISP/Randi 2023's own strains):
Chen et al. 2013 and the Janelia GENIE project** (standard citation for GCaMP6 variants; not independently
re-opened this pass, numbers from a 2023 companion/successor paper's own stated comparisons, cross-checked
across two search passes): **Kd (Ca2+ dissociation constant) = 157 nM (GCaMP6s), 364 nM (GCaMP6f)**; **Hill
coefficient n ~ 2-3** for GCaMP6 variants generally; **half-decay time at 20C = 769 ms (GCaMP6s)**, reduced to
216 ms by a later point-mutant (RS-1 EF-3, not one of the variants named in the task, noted for context only);
**response time (effectively rise) 20 ms (GCaMP6s) vs 2 ms (GCaMP6f)** (measured, stopped-flow fluorimetry,
Nature 2023 "Fast and sensitive GCaMP..." paper, DOI pattern s41586-023-05828-9).

**GCaMP7f (jGCaMP7f, used in Atanas 2023 per the task brief): Dana et al. 2019**, *High-performance GFP-based
calcium indicators for imaging activity in neuronal populations and microcompartments*, (bioRxiv 434589,
published version in Nature Methods - exact journal/DOI not independently re-opened this pass): **1-AP
half-rise time 26 +/- 2 ms; 1-AP half-decay time 265 +/- 20 ms (in vitro), 270 +/- 15 ms (in vivo)** (measured).
**jGCaMP7f's Kd was not extracted from the search-accessible portions this pass - UNVERIFIED**, though the
Dana 2019 paper is known in the broader literature to report Kd values per variant in its main tables; a
builder with full-text access should pull the exact number rather than use GCaMP6f's as a stand-in.

**Optogenetic actuator: Randi et al. 2023** (the same *Neural signal propagation atlas of Caenorhabditis
elegans*, Nature 623:406-414, already the row-7/9 functional-atlas source in STATE_OF_THE_ART) used
**GUR-3/PRDX-2**, described directly in the companion **TWISP** preprint (*A Transgenic Worm for
Interrogating Signal Propagation in C. elegans*, bioRxiv 2023.08.03.551820) as "an unconventional optogenetic
actuator... less well characterized compared to traditionally used optogenetic proteins such as
Channelrhodopsin." Its one stated mechanistic advantage: **it is activated by light delivered
intracellularly** (GUR-3 is a light-sensitive guanylyl cyclase-related receptor, PRDX-2 a peroxiredoxin
acting as a redox relay - the actual activation chemistry is H2O2-mediated oxidation signalling, not a
classical photocurrent), so it does not need membrane-localised illumination the way channelrhodopsin does.
**No activation-kinetics numbers (time constant, action-spectrum sensitivity, saturation irradiance) were
located for GUR-3/PRDX-2 in this pass - UNVERIFIED**; this is a genuine gap, not just an unexplored search
path, since the source material itself flags the actuator as under-characterised relative to standard
opsins.

**NeuroPAL identification error rates: Yemini et al. 2021**, *NeuroPAL: a multicolor atlas for whole-brain
neuronal identification in C. elegans*, Cell 184(1):272-288 (DOI pattern S0092-8674(20)31682-2); accuracy
numbers from the semi-automated pipeline built on top of it (a related, not identical, paper/pipeline found in
this search pass - **the 86%/94% numbers below should be attributed carefully; they come from a semi-
automated identification pipeline cited alongside Yemini 2021, not necessarily from Yemini 2021's own main
text - UNVERIFIED exact attribution, numbers themselves measured by someone in this line of work**):
**86% head accuracy, 94% tail accuracy**, accuracy inversely related to local neuron density (the dense
ventral ganglion in the head is the hardest region); manually identifying 8 additional neurons raises head
accuracy above 90%.

### Parameter table

| Name | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| GCaMP6s Kd | 157 | - | nM | Chen 2013 / GENIE, via cross-check in Nature 2023 | measured |
| GCaMP6f Kd | 364 | - | nM | same | measured |
| GCaMP6 Hill coefficient | 2-3 | - | dimensionless | same | measured |
| GCaMP6s half-decay time (20C) | 769 | - | ms | same | measured |
| GCaMP6s response/rise time | 20 | - | ms | same | measured |
| GCaMP6f response/rise time | 2 | - | ms | same | measured |
| GCaMP7f half-rise time (1 AP) | 26 | +/-2 | ms | Dana et al. 2019 | measured |
| GCaMP7f half-decay time (1 AP, in vitro) | 265 | +/-20 | ms | Dana et al. 2019 | measured |
| GCaMP7f half-decay time (1 AP, in vivo) | 270 | +/-15 | ms | Dana et al. 2019 | measured |
| GCaMP7f Kd | not found this pass | - | nM | Dana et al. 2019 (not opened in full) | not found this pass |
| GUR-3/PRDX-2 activation time constant | not found this pass | - | - | TWISP preprint (mechanism only) | not found this pass |
| NeuroPAL head ID accuracy | 86 | - | % | Yemini 2021-adjacent pipeline (attribution UNVERIFIED) | measured |
| NeuroPAL tail ID accuracy | 94 | - | % | same | measured |

**Cells it applies to:** all GCaMP-imaged neurons (whole-brain imaging data sets, rows 7-10, 17-18); the
optogenetic actuator applies wherever Randi 2023's stimulation protocol is replicated; NeuroPAL identification
uncertainty applies to any model output that claims per-cell identity against imaging data.

**Simplest nested form:** (1) current single-setting GCaMP Hill curve (`layers.gcamp`, one rise/decay/noise
setting for all cells, per MECHANISMS_AUDIT row 23); (2) per-indicator-variant Kd/Hill/rise/decay parameters
(GCaMP6s vs 6f vs 7f) selected by which dataset is being compared against, since Randi 2023 and Atanas 2023
used different indicators and mixing them up would misattribute a kinetic difference to a biological one;
(3) add the GUR-3/PRDX-2 actuator as a separate (under-characterised, guessed-kinetics) optogenetic input
channel, distinct from the GCaMP readout channel, only when replicating Randi 2023's stimulation protocol
specifically; (4) add a NeuroPAL identification-uncertainty layer that stochastically mislabels ~6-14% of
cells (inverse of the 86-94% accuracy) when scoring against NeuroPAL-identified data, so the model is not
penalised for errors that are actually in the identification pipeline, not the biology.

**Isolated check for the builder:** convolve a single simulated action potential's Ca transient with the
GCaMP6s Hill curve (Kd 157 nM, n ~2.5, rise 20 ms, decay 769 ms) and check the resulting fluorescence
transient's own half-rise and half-decay match those numbers directly - a pure signal-processing unit check,
no neuron or circuit model needed. A second check, same idea, for GCaMP7f (rise 26 ms, decay 265-270 ms) -
the two should look visibly different (7f decays ~3x faster) when driven by the identical underlying Ca
transient, which is itself a useful sanity check that the observation model is not accidentally shared/
conflated between the two datasets.











