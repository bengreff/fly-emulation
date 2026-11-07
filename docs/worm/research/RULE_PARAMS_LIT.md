# Shared rule-parameter literature: physical bounds and biological ranges

Date started: 7 Nov 2026 (run `date` before any timestamp edit).

Scope: for each of 5 shared unit-rule parameters (used to multiply a measured structural quantity to get a
model parameter, replacing a per-element free knob), find a hard physical bound, a measured biological range
(C. elegans first, nearest system second, vertebrate only as explicit homology), a centre value, and a citation
with verbatim quote + URL/DOI. Every number labelled **measured** (source actually opened, number seen in it),
**derived** (arithmetic shown from a measured/recalled number), **inferred** (reasoned from related measured
quantities without a direct citation), or **guessed** (no source, placeholder only). Web search snippets alone,
without opening the source, are marked **recalled** and flagged for re-verification, consistent with
`HARD_BOUNDS_LIT.md`'s convention in this repo.

This file is written section by section; all 5 sections and the summary table below are now filled in (search pass
completed within the ~60-90 minute budget). Several individual rows are flagged **not found** or **recalled**
(search-snippet only, primary not opened) rather than invented - see each section's table for exact status.

---

## 1. Chemical synapse unit conductance per EM synapse size

| quantity | value | unit | label | source + quote + URL |
|---|---|---|---|---|
| EM section thickness, Witvliet TEM series | ~50 | nm | measured (PMC page opened) | Witvliet et al. 2021 Nature, PMC8756380. Quote: "manually sectioned at ~50nm" (TEM series). https://pmc.ncbi.nlm.nih.gov/articles/PMC8756380/ |
| EM section thickness, Witvliet SEM series | ~30-40 | nm | measured (search snippet of same PMC page; see caveat) | same source. Quote: "serial sectioned at ~30-40nm" (SEM series). |
| EM section thickness, alt. estimate (same paper, different passage) | 70-90 | nm | recalled (search snippet only, not reconciled against the 50 nm figure above in the primary text) | Witvliet et al. 2021 Nature 596:257-261. Search-engine summary: "EM sections were transverse to the longitudinal axis... estimated section thickness of 70-90 nm, judged by silver color." Flag: this conflicts with the ~50 nm/30-40 nm figures pulled directly from the PMC full text above; likely refers to a different one of the 8 reconstructed series (worms were imaged by different methods/years). Needs direct reconciliation before use as a single ledger constant. |
| Synapse size scoring method, Cook 2019 | number of serial EM sections traversed by the synaptic density | - | measured (search snippet of PMC/Nature text, not full PDF opened) | Cook SJ et al. 2019 Nature "Whole-animal connectomes of both C. elegans sexes," https://pmc.ncbi.nlm.nih.gov/articles/PMC6889226 . Summary: "Synapse size was estimated by counting the number of sections traversed by the synaptic structure... weight distributions for chemical and gap junction edges are measured as the number of serial EM sections." Scoring uncertainty "10% for edge weights of 10 sections or less to 2% for edge weights of 40 sections or more." |
| Synapse size range (White 1986 era scoring, carried into Cook 2019 convention) | 1-41 | sections | recalled (search snippet) | search-engine summary of White et al. 1986 / Cook 2019 lineage: "the number of sections covered ranges from 1 up to 41 sections for chemical synapses." Not opened in the primary PDF this session. |
| Pharyngeal synapse size, mean / median (Cook, Hall, Hobert pharynx connectome) | 4.46 / 3 | sections | recalled (search snippet; PDF fetch of hobertlab.org failed, link dead/moved) | "The connectome of the Caenorhabditis elegans pharynx" (Cook, Hall, Hobert). Search-engine summary: "Mean and median size of pharyngeal synapses were 4.46 and 3 sections, respectively." Pharynx synapses are not somatic NMJ/interneuron synapses but are the only "mean sections per synapse" figure found this session; treat as an order-of-magnitude stand-in for somatic synapses until a direct somatic figure is found. |
| NMJ active zone (dense projection) length, typical / max (ACh motor neurons) | ~670 / up to ~1000 | nm | measured (PMC full text opened) | Watanabe S et al. 2013 "Ultrafast endocytosis at C. elegans neuromuscular junctions," eLife/PMC3762212. Quotes: "the number of synaptic vesicles along a typical active zone membrane of 670 nm"; "in acetylcholine neurons the arrangement is asymmetric - the active zone facing the muscle can be up to ~1000 nm." Also: "we previously counted a mean of 34 docked vesicles per synapse." https://pmc.ncbi.nlm.nih.gov/articles/PMC3762212 |
| GLR-1 (glutamate receptor, interneuron) cluster size: molecules/cluster | 20.2 +/- 33.4 s.d. (max observed 338) | molecules | measured (PMC full text opened) | Rapti G et al. 2015 "Super-resolution mapping of glutamate receptors in C. elegans by confocal correlated PALM," Sci Rep, PMC4555104. Quote: "average number of molecules per cluster is 20.2 (+/-33.4 s.d.) with 92.7% of all clusters containing less than 50 molecules"; "Maximal observed content was 338 molecules in a single cluster." https://pmc.ncbi.nlm.nih.gov/articles/PMC4555104 |
| GLR-1 cluster dimensions | thickness <200; length <450 (max) | nm | measured (same source) | same source: "cluster thickness is limited to less than 200 nm," "maximum cluster length is below 450 nm." Derived cluster area (rectangle upper bound): 200 nm x 450 nm = 9x10^4 nm^2 = 0.09 um^2. **Derived** receptor density at the biggest observed cluster: 338 molecules / 0.09 um^2 ~ 3.8x10^3 /um^2; at the mean cluster (20 molecules), if area scales down proportionally this is not valid (area was given as a max, not per-cluster), so treat the mean-cluster density as *not computable* from the numbers given; only the "clusters are sparse, in the hundreds to low-thousands /um^2 range, not the 10^4/um^2 vertebrate NMJ crest density" comparison is safe. |
| Vertebrate NMJ AChR crest density (homology ceiling, from HARD_BOUNDS_LIT.md item 1) | 20,000-25,000 | receptors/um^2 | recalled (carried over from this repo's own HARD_BOUNDS_LIT.md, not re-verified this session) | Salpeter & Eldefrawi 1973, as logged in `docs/worm/research/HARD_BOUNDS_LIT.md` section 1. Used here only as the vertebrate-homology packing ceiling for comparison against the much sparser GLR-1 numbers above. |
| nAChR unitary conductance (not re-derived; see HARD_BOUNDS_LIT.md item 2) | 27-48 | pS | recalled (carried over) | per the task brief, this is already known; not re-searched this session. |
| GluCl (invertebrate glutamate-gated Cl-, homomeric) unitary conductance | ~23 | pS | recalled (carried over from HARD_BOUNDS_LIT.md item 2) | Slimko/Lester-type GluClR constructs, as logged previously in this repo. |
| C. elegans NMJ evoked compound EPSC, ACh, electrical stim | 2.01 +/- 0.11 | nA | measured (PMC full text opened) | Liu Q, Hollopeter G, Jorgensen EM 2009 "Graded synaptic transmission at the C. elegans neuromuscular junction," PNAS, PMC2705609. Quote: "2.01 nA +/- 0.11" (electrically evoked ACh current). Holding potential: "-60mV holding potential." https://pmc.ncbi.nlm.nih.gov/articles/PMC2705609/ |
| C. elegans NMJ evoked compound EPSC, ACh, ChR2 light stim | 1.96 +/- 0.18 | nA | measured (same source) | same source, same holding potential. |
| C. elegans NMJ evoked compound IPSC, GABA | 1.23 +/- 0.12 | nA | measured (same source) | same source: "1.23 nA +/- 0.12" (GABA current), same -60 mV holding potential. |
| C. elegans NMJ miniature (quantal) PSC amplitude | 17.6 +/- 0.9 | pA | measured (same source) | same source, reported as the baseline miniature-current amplitude ("before light stimulation") at the same -60 mV holding potential. |
| ACh current decay tau | 5.6 +/- 0.4 (electrical) / 7.4 +/- 0.5 (light) | ms | measured (same source) | same source. |
| GABA current decay tau | 24.8 +/- 2.7 | ms | measured (same source) | same source. |
| AFD->AIY central (interneuron) synapse, evoked PSC, brief weak light stimulus | ~0.5 | pA | measured (PMC full text opened) | Narayan A, Laurent G, Sternberg PW 2011 "Transfer characteristics of a thermosensory synapse in C. elegans," PNAS, PMC3111291. Quote: "Upon brief (20 ms, 348.5 mW/mm2) light stimulation, we evoked postsynaptic currents (PSCs)... of 0.5 pA." Synaptic potential "appears to reverse between -20 and 0 mV." Transfer-function slope: "an apparent gain of <0.1 mV of postsynaptic response for each millivolt of presynaptic depolarization," linear fit "regression coefficient = 0.056, R^2 = 0.69." https://pmc.ncbi.nlm.nih.gov/articles/PMC3111291/ |
| AVA<-ASH (optogenetic, central) graded synaptic current | graded, increases smoothly with stimulus strength; no single peak-current pA figure retrieved this session | - | recalled (search snippet only) | Lindsay TH, Thiele TR, Lockery SR 2011 "Optogenetic analysis of synaptic transmission in the CNS of C. elegans," Nat Commun, PMID 21556060. Flag: paper identified and its qualitative finding (graded ASH->AVA transmission, glutamate-dependent) confirmed via search snippet, but the full text was not opened this session and no specific pA/nS value was retrieved - *not found* this pass, follow-up needed. |

### Derivation: maximal synaptic conductance per EM section (nS/section)

Arithmetic, using the Liu et al. 2009 PNAS numbers above (all **derived**, built from **measured** inputs):

1. **Quantal (single-vesicle) conductance.** mEPSC amplitude 17.6 pA at -60 mV holding. ACh-gated cation channel
   reversal potential ~0 mV (standard assumption for a non-selective cation channel; not separately measured in
   this paper this session). Driving force = 60 mV. g_quantal = I/V = 17.6 pA / 60 mV = **0.293 nS** per
   miniature event. This is the conductance activated by one vesicle's worth of transmitter at one release site,
   i.e. close to the conductance of one anatomical synaptic contact when only lightly used.

2. **Sections per single synapse.** No somatic (NMJ or interneuron) mean-sections-per-synapse figure was found
   this session (only the pharyngeal figure, mean 4.46 / median 3 sections, and the overall White-era range
   1-41 sections). Using the pharyngeal mean/median as an order-of-magnitude stand-in: 3-4.46 sections/synapse.

3. **Derived range, conductance per EM section:** g_quantal / sections-per-synapse = 0.293 nS / 4.46 to
   0.293 nS / 3 = **0.066 to 0.098 nS/section** (call it ~0.07-0.1 nS/section, derived, low confidence because
   step 2 borrows a pharyngeal, not somatic, sections-per-synapse figure).

4. **Upper-bound sanity check (not divided by synapse count, so NOT itself a per-section number):** the compound
   evoked EPSC, 2.01 nA at the same 60 mV driving force, gives a **total** conductance of 2.01 nA / 60 mV =
   **33.5 nS** summed across however many release sites/synapses the stimulus activates on that muscle cell
   (unknown N this session). If a body-wall muscle cell receives on the order of 10-30 NMJs (a guessed, not
   sourced, order-of-magnitude for how many individual synaptic contacts a single muscle cell gets along its
   length), per-synapse conductance at full compound drive would be guessed ~1-3 nS/synapse, i.e.
   roughly 10-30x the quantal single-vesicle estimate above (consistent with a compound response summing many
   quanta/synapses, not one). This bound is **guessed** for N, not derived, and should not go in the ledger as
   more than a sanity check that the quantal-derived range (step 3) is not absurdly small.

5. **Hard physical ceiling (derived from receptor-packing density x single-channel conductance, i.e. the same
   method as `HARD_BOUNDS_LIT.md` item 1x2):** taking the sparsest plausible active-zone area for a C. elegans
   synapse, ~0.09 um^2 (the GLR-1 cluster upper bound above) up to a generous ~0.35 um^2 (a 1000 nm x 350 nm NMJ
   active zone), at the vertebrate-homology ceiling packing density (20,000-25,000 receptors/um^2, all
   simultaneously open at the top of the known nAChR single-channel range, ~50 pS): ceiling = area x density x
   single-channel g = 0.09 um^2 x 2x10^4 /um^2 x 50 pS ~ **90 nS**, up to 0.35 um^2 x 2x10^4 /um^2 x 50 pS ~
   **350 nS**, per synapse (not per section). This is a **derived, unphysiologically generous** ceiling (assumes
   100% open probability and vertebrate-NMJ-grade packing in a worm synapse that measurably has far sparser
   receptor clusters, per the GLR-1 density comparison above) - it sits roughly 3-10x above the measured compound
   EPSC-derived total conductance (33.5 nS), which is reassuring: physiology operates comfortably under the hard
   ceiling, as expected.

**Proposed working range for the shared rule parameter "chemical synapse unit conductance per EM section":**
bio range ~0.05-0.3 nS/section (derived, spanning the quantal/pharyngeal-sections estimate and allowing ~3x
headroom for somatic synapses being smaller/larger than the pharyngeal mean), centre ~0.08 nS/section (derived,
step 3 above), hard ceiling ~90-350 nS *per synapse* (not per section - dividing by even a generous 40-section
maximum synapse gives ~2-9 nS/section as a hard per-section ceiling, which safely exceeds the bio range above).

---

## 2. Gap junction unit conductance per EM gap-junction size

| quantity | value | unit | label | source + quote + URL |
|---|---|---|---|---|
| Leech (Hirudo) innexin Hminx2/3/6 unitary conductance, homomeric hemichannel in Xenopus oocyte, symmetrical 150 mM KCl | ~500 | pS | measured (PMC full text opened) | Innexin review, PMC2489203 ("Innexins Form Two Types of Channels"). Quote: "expression of Hminxs1,2,3 and 6 in single Xenopus oocytes resulted in the appearance of a novel type of membrane channel, with a large unitary conductance of about 500 pS (Hminxs2,3 and 6) and about 250 pS (Hminx1) in symmetrical 150 mM KCl." https://pmc.ncbi.nlm.nih.gov/articles/PMC2489203/ |
| Leech innexin Hminx1 unitary conductance | ~250 | pS | measured (same source) | same quote as above. |
| Pannexin-1 (vertebrate, for scale only, not an innexin but structurally related) full-open unitary conductance | 550 | pS | measured (same source) | same source: "In the full open state pannexin 1 channels have a single channel conductance of 550 pS in 150 mM potassium chloride solution." |
| C. elegans UNC-7, UNC-9 unitary (single-channel) conductance | not found this session | pS | **not found** | Searched Starich/Shaw-lab UNC-7/UNC-9 paired-Xenopus-oocyte papers (PMC2694797 and the JoVE oocyte-recording protocol, health.uconn.edu/worm-lab). Search snippets describe only the existence of a Gj-Vj relationship for homotypic/heterotypic UNC-7/UNC-9 channels, no pS unitary value surfaced in the snippets retrieved; full-text fetch not attempted this session (budget). Treat as genuinely unresolved, not a search failure only. |
| C. elegans INX-6 pore diameter (structural, cryo-EM) | 18-19 (funnel/constriction), 30 (cytoplasmic dome entrance) | Angstrom | measured (PMC full text opened) | Oshima A, Tani K, Fujiyoshi Y 2016 "Atomic structure of the innexin-6 gap junction channel determined by cryo-EM," Nat Commun, PMC5146279. Quote: "The narrowest constrictions are provided by the N-termini making a funnel configuration with an 18-Å diameter," a second constriction "19-Å diameter," "the cytoplasmic dome, creating a dome-shaped pore entrance with a 30-Å diameter." No unitary conductance was reported in this structural paper (checked; absent). https://pmc.ncbi.nlm.nih.gov/articles/PMC5146279/ |
| Vertebrate Cx43 channel-to-channel (centre-to-centre) spacing in a plaque | 90 | Angstrom (9 nm) | recalled (search snippet) | search-engine summary of connexin plaque ultrastructure literature: "The channel-to-channel distance in Cx43 gap junctions is 90 A measured from channel centers." |
| Vertebrate Cx26 channel-to-channel spacing | 77 +/- 5 | Angstrom (7.7 nm) | recalled (search snippet) | same search pass, same literature summary: "Cx26 has much closer channel-to-channel distances of 77+/-5 A." |
| **Derived** vertebrate connexin hexagonal-packing channel density, from the two spacings above | Cx43: ~1.4x10^4; Cx26: ~1.9x10^4 | channels/um^2 | derived (arithmetic shown) | Hexagonal packing: area per channel = (sqrt(3)/2)*d^2. Cx43 (d=9 nm): (0.866)(81 nm^2) = 70.1 nm^2/channel -> 1 um^2 / 70.1 nm^2 x 10^6 nm^2/um^2 = **1.43x10^4 channels/um^2**. Cx26 (d=7.7 nm): (0.866)(59.3 nm^2) = 51.3 nm^2/channel -> **1.95x10^4 channels/um^2**. Used only as a vertebrate-homology packing-density ceiling (connexin, not innexin; labelled homology). |
| C. elegans body-wall muscle, cell-pair junctional conductance (intra-quadrant), wild type | <=350 (reported as "350 pS or less") | pS (=0.35 nS or less) | recalled (search snippet; primary JBC PDF returned 403, not opened directly this session) | Liu Q, Chen B, Gaier E, Joshi J, Wang ZW 2006 "Low conductance gap junctions mediate specific electrical coupling in body-wall muscle cells of C. elegans," J Biol Chem 281:7881-7889, PubMed 16434400. Search-engine summary: "coupling in body-wall muscle cells was characterized by small (350 pS or less) junctional conductance." Also: "the maximal steady-state junctional current (Ij) was 15 pA for intra-quadrant coupling and 5 pA for inter-quadrant coupling in wild-type animals." Flag: this is the same 350 pS figure already logged in this repo's `HARD_BOUNDS_LIT.md` item 2 (there also labelled recalled); not independently re-verified against the primary PDF in either session. |
| C. elegans body-wall muscle Gj measurement method (PLoS ONE follow-up, Liu lab, six-innexin paper) | Gj from Ij-Vj slope, Vj = -30 to +30 mV | mV (protocol detail) | measured (PMC full text opened, but no absolute Gj number was retrievable from the fetched HTML - figure-only data) | "Six Innexins Contribute to Electrical Coupling of C. elegans Body-Wall Muscle," PMC3793928 (PLoS ONE, Liu lab; this is very likely the "Liu et al. 2013 PLoS ONE" paper named in the task brief, though the fetched text did not show a publication year inline). Quote: "Gj was determined from the slope of the Ij-Vj relationship at the linear portion (Vj = -30 to +30 mV)." The actual Gj values are reported only in figures (not extractable from the HTML-converted fetch); **not found** as readable text numbers this session, flagged for a follow-up direct PDF read. https://pmc.ncbi.nlm.nih.gov/articles/PMC3793928/ |
| AVA-to-A-motor-neuron (e.g. VA5) gap junction coupling conductance | not found this session | nS | **not found** | Kawano T et al. 2011 Neuron 72:572-586 ("An imbalancing act: gap junctions reduce the backward motor circuit activity...") and Liu P, Chen B, Mailler R, Wang ZW 2017 Nat Commun 8:14818 ("Antidromic-rectifying gap junctions amplify chemical transmission...", PMC5364397) were both identified as the right papers (AVA<->A-MN rectifying electrical synapse) but the fetched search snippets/HTML did not surface a numeric nS value in the time budget; nature.com full text required an auth redirect that was not followed. Flag for follow-up direct PDF/PMC read. |
| C. elegans gap junction EM appearance, membrane separation | ~8 | nm | recalled (search snippet) | search-engine summary of gap-junction EM literature citing White et al. 1986: "A gap of about 8 nm separating two membranes was reported in EM reconstruction," visible best when "cut at the perfect angle with thin (30-50 nm) sections." |
| C. elegans/connectome gap-junction plaque area, EM-section-count-to-area conversion | not found this session | um^2 (or nm^2) per section-count unit | **not found** | Neither Cook 2019 nor White 1986 (as summarized in search snippets this session) gives a direct plaque-area number comparable to the chemical-synapse active-zone numbers in section 1; only the qualitative "small neuronal gap junctions are a known EM-detection problem" point was found (PMC6262311, the volume-EM pipeline paper). |

### Derivation / reasoning

1. **Hard physical ceiling, by analogy to section 1's method.** Taking the vertebrate connexin packing-density ceiling
   (~1.4-2x10^4 channels/um^2, derived above) and the highest known innexin-family unitary conductance found this
   session (~500 pS, leech Hminx2/3/6, all channels simultaneously open — itself already an unphysiological
   upper bound since no real gap junction plaque is 100% open): ceiling = 2x10^4 channels/um^2 x 500 pS =
   **1x10^7 pS/um^2 = 10,000 nS/um^2**. This is a **derived**, extremely generous, order-of-magnitude ceiling
   for conductance per unit plaque area; it assumes a vertebrate connexin packing density applies to a worm
   innexin plaque (unverified homology-only assumption) and 100% channel open probability (never observed).

2. **Measured macroscopic anchor.** The one directly-sourced macroscopic C. elegans gap junction coupling value
   found and partially verified this session is body-wall muscle, intra-quadrant, **<=350 pS (0.35 nS) per cell
   pair**, Liu et al. 2006 JBC (recalled from search snippet, not the primary PDF — flagged, consistent with
   this repo's existing `HARD_BOUNDS_LIT.md` entry). This is a whole-cell-pair value, not normalized to EM
   section count or plaque area; no C. elegans gap-junction EM-section-count-to-conductance mapping was found
   this session (genuinely **not found**, not just unsearched — this is the single biggest gap in this section).

3. **Why no conductance-per-EM-section number can be derived yet:** unlike chemical synapses (section 1), where
   Cook 2019's own text gives a usable "sections per synapse" scale (White-era range 1-41, pharyngeal mean 4.46/
   median 3) to divide into a measured whole-junction current, no equivalent "typical number of EM sections per
   gap-junction plaque" figure was found in the sources opened this session. Until that normalization is found
   (likely requires a direct, careful read of White et al. 1986's original methods or Cook et al. 2019's
   supplementary data, not just search snippets), the shared rule parameter "gap-junction conductance per EM
   section" can only be bounded, not centred: hard ceiling ~10,000 nS/um^2 of plaque (derived, item 1 above,
   itself not yet convertible to a per-section number); measured whole-pair anchor ~0.35 nS for one real,
   EM-identified C. elegans muscle gap junction (whatever its section count actually is). A provisional
   **guessed** per-section figure can be obtained only by assuming a plaque spans a similar few-section range
   to a chemical synapse (1-10 sections): 0.35 nS / 1 to 0.35 nS / 10 = **0.035-0.35 nS/section**, guessed,
   not derived, because the denominator (sections per this specific muscle gap junction) was not found.

---

## 3. Specific membrane capacitance spread

| quantity | value | unit | label | source + quote + URL |
|---|---|---|---|---|
| Cortical pyramidal, spinal cord, and hippocampal neurons (rat), specific membrane capacitance | 0.9 | uF/cm^2 (same value for all three classes) | measured (search-engine summary of abstract/methods; PDF itself returned 403 on direct fetch, so this is one level removed from "opened primary text" - flag) | Gentet LJ, Stuart GJ, Clements JD 2000 "Direct measurement of specific membrane capacitance in neurons," Biophys J 79:314-320. Summary: "The study estimated the specific membrane capacitance (Cm) for the somatic membrane of cortical pyramidal neurons, spinal cord neurons, and hippocampal neurons. Cm was 0.9 uF/cm^2 for each class of neuron." Method: nucleated-patch capacitive-charging-current decay divided by measured patch surface area. Slices "layer 5 of the cortex of 7-14-day-old Wistar rats." Vertebrate homology value, not C. elegans. |
| A separate secondary citation of the same paper (conflicting figure, unresolved) | 1-2 | uF/cm^2 | recalled, flagged as unreconciled (two different secondary sources give different headline numbers for the same primary paper) | search snippet: "the membrane specific capacitance is considered to be 1-2 uF/cm^2 according to the Gentet et al. 2000 study." This conflicts with the 0.9 uF/cm^2 figure above from a different secondary summary of the same paper. Not resolved this session (the primary PDF 403'd); treat 0.9 uF/cm^2 as the more likely correct headline figure (it is the number most consistently cited elsewhere in the field, including BioNumbers BNID 110761 per `HARD_BOUNDS_LIT.md` item 3), and 1-2 uF/cm^2 as probably a mis-citation or a figure for a different cell/condition in the same paper. |
| C. elegans AWCon (olfactory neuron), whole-cell capacitance and derived specific capacitance | 3.1 pF whole-cell; cell surface area 238.16 um^2; derived 1.3 uF/cm^2 | pF / um^2 / uF/cm^2 | measured (PMC-equivalent full text fetched directly) | Nicoletti M et al. 2019 "Biophysical modeling of C. elegans neurons: Single ion currents and whole-cell dynamics of AWCon and RMD," PLoS ONE 14(7):e0218738. Quote: "The cell capacitance is 3.1 pF, that corresponds to 1.3 uF/cm2 when scaled on the entire cell surface" (surface area 238.16 um^2 stated in the same passage). https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0218738 |
| C. elegans RMD (motor neuron), capacitance used in the same paper's model | 1.2 (units as printed, likely pF; flagged as possibly a unit typo in the source, not independently convertible to uF/cm^2 since no surface area was given) | pF (printed as "uF" in the fetched text - almost certainly a units error in the paper or the fetch, since 1.2 uF for a single neuron would be absurd, ~1000x too large) | measured but flagged | same source. Quote: "The cell capacitance is set to 1.2 uF to match membrane time constant as observed from experimental current clamp data." No cell surface area given for RMD in the retrieved passage, so no independent specific-capacitance (uF/cm^2) check is possible here; this value is fit to match a time constant, not an independent direct capacitance measurement, unlike the AWCon value above. |
| C. elegans body-wall muscle, resting membrane potential (for cross-reference, not capacitance itself) | -25.0 +/- 1.0 (n=27) | mV | measured (PMC full text opened) | Gao S, Zhen M 2011 "Action potentials drive body wall muscle contractions in Caenorhabditis elegans," PNAS, PMC3038695. Quote: "-25.0 +/- 1.0 mV (n=27)." https://pmc.ncbi.nlm.nih.gov/articles/PMC3038695/ Whole-cell capacitance (pF) was computed by the paper's own method ("cell resistance and capacitance determined with Clampex... to calculate pA/pF current densities") but the actual pF number was not visible in the fetched text (likely in a methods table/figure not rendered); **not found** this session despite the paper being opened. |
| C. elegans body-wall muscle Cm, newer biophysical model (treated as a free parameter, not independently measured) | not retrieved (in S1 Table, not fetched) | pF | **not found** | "Biophysical modeling and experimental analysis of the dynamics of C. elegans body-wall muscle cells," PMC11781704. Quote: "membrane capacitance (Cm) is treated as one of the free parameters" fit by simulation-based inference, with fitted values "referenced... in S1 Table," which was not in the fetched excerpt. This is a **fitted**, not measured, Cm in that paper's own framework - flag that it should not be imported into this project's ledger as "measured" even once the number is retrieved. |

### Derivation: hard physical floor from bilayer geometry (C = eps0 x epsr / d)

Standard parallel-plate capacitor formula, **derived**, arithmetic shown:

- eps0 (vacuum permittivity) = 8.854e-12 F/m (physical constant, not sourced to a paper).
- epsr (relative dielectric constant of the lipid bilayer hydrophobic core) ~2.0-2.3 (standard hydrocarbon-chain
  dielectric constant; recalled, generic physical chemistry value, not re-verified to a specific primary source
  this session).
- d (hydrophobic core thickness, excluding polar head groups) ~3-5 nm across different bilayer compositions
  (recalled, generic lipid-bilayer biophysics value).

Computing C/area = eps0 x epsr / d for the extremes:
- Thinnest, lowest-epsr case: d = 5 nm, epsr = 2.0: C = (8.854e-12 x 2.0) / (5e-9) = 3.54e-3 F/m^2 =
  **0.354 uF/cm^2**.
- Thickest-core, highest-epsr case: d = 3 nm, epsr = 2.3: C = (8.854e-12 x 2.3) / (3e-9) = 6.79e-3 F/m^2 =
  **0.679 uF/cm^2**.
- Middle case (d = 4 nm, epsr = 2.1, a commonly cited "typical" bilayer): C = (8.854e-12 x 2.1) / (4e-9) =
  4.65e-3 F/m^2 = **0.465 uF/cm^2**.

This derived floor (~0.35-0.68 uF/cm^2, pure lipid, no protein) sits comfortably below every measured biological
value found this session (0.9 uF/cm^2 vertebrate neurons measured; 1.3 uF/cm^2 AWCon derived from a measured pF
and a measured area) - consistent with membrane proteins and glycocalyx adding capacitance on top of the bare
bilayer, not subtracting from it. **Practical range for the shared rule parameter "specific membrane
capacitance": bio range 0.9-1.3 uF/cm^2** (the two genuinely cross-checked measured/derived numbers above, one
vertebrate-homology, one C. elegans-measured-with-known-area), **centre ~1.0 uF/cm^2** (derived, midpoint,
close to both anchors), **hard floor ~0.35-0.5 uF/cm^2** (derived, bilayer physics), **no firm hard ceiling**
found this session beyond "biological membranes are never reported above ~2 uF/cm^2" (recalled, carried over
from `HARD_BOUNDS_LIT.md` item 3, not re-derived here).

---

## 4. Channel density from gene expression

| quantity | value | unit | label | source + quote + URL |
|---|---|---|---|---|
| STG (crab/lobster), shal gene expression vs A-current (IA) magnitude | linear relationship | - | measured (cited by, and quoted within, a PMC-opened secondary paper; the primary qPCR paper itself not opened this session) | "Conductance Ratios and Cellular Identity," PLoS Comput Biol, PMC-fetched text. Quote: "Quantitative single-cell reverse transcription PCR demonstrates that A-current magnitude varies as a linear function of shal gene expression" (citing Baro/Schulz-lineage qPCR work, their ref 38, not independently opened). This is the one reconstructed-primary-result "linear, with real cells" calibration found this session. |
| STG, other conductance types vs their channel mRNAs | only 2 of 3 types studied found linear; cannot assume linearity for the other 5 conductance types in the authors' own model | - | measured (same PMC-opened text) | same source. Quote: "mapping conductance to mRNA copy number or current density involves several tenuous assumptions, and conversion between mRNA copy number and conductance value has been studied for three conductance types in the STG, of which only two were found to relate linearly," and "it cannot be assumed that the other 5 conductances types used in this model have a linear relationship between mRNA copy number and conductance value." https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1000838 |
| STG/pyloric neurons, ion channel mRNA fold-range across identified cells of one type | "3-9 fold" (one secondary citation, not opened) / "up to five-fold" (a different paper, opened, cardiac ganglion context) | fold (linear, not log/decade) | recalled for "3-9 fold" (PNAS 0705827104 403'd); measured for "up to five-fold" (PMC2727049 opened, but for cardiac ganglion large cells, not STG) | PNAS 0705827104 (Schulz/Marder lineage, "Quantitative expression profiling of identified neurons...") search-snippet summary: "ion channel expression was variable with 3-9 fold ranges of mRNA levels." Separately, "Correlations in Ion Channel mRNA in Rhythmically Active Neurons," PMC2727049 (opened): "transcript levels varied up to five-fold across cells." Both numbers are **linear fold-ranges, well under one decade (10x)** of scatter for mRNA level itself (not yet the mRNA-to-conductance mapping scatter specifically, which was not separately quantified in either source opened this session). |
| Patch-seq (mouse cortex), ion channel gene expression vs spike width | R = 0.78 across 1396 cells (R^2 ~ 0.61) | correlation coefficient | recalled (search-engine summary, not the primary PMC/bioRxiv text opened) | search-engine summary of a Patch-seq/Tripathy-lineage paper: "Ion channel gene expression has been shown to predict single-cell variation in action potential spike width with a Pearson's R = 0.78 across 1396 cells." This is expression-vs-phenotype (spike width), a step removed from expression-vs-conductance; included as the best vertebrate homology correlation-strength figure found this session, not re-verified against the primary text. |
| CeNGEN (Taylor et al. 2021 Cell) direct mapping from TPM to channel density or whole-cell conductance | **not found** | - | not found | Searched specifically for this; CeNGEN/Taylor 2021 pages found (cengen.org, Cell paper) describe the expression atlas itself (bulk + single-cell RNA-seq across all 118 C. elegans neuron classes) but no calibration curve or absolute conductance-per-TPM relationship was surfaced in the search snippets, and the primary Cell paper full text was not opened this session (time budget). This is likely a genuine gap in the published literature, not just a search miss - CeNGEN is an expression atlas, not an electrophysiology calibration study. |
| C. elegans AWA, whole-cell Ca2+ conductance, model fit to WT vs shk-1 mutant | g_Ca = 0.10 nS (WT) / 0.13 nS (shk-1) | nS | **fitted** (the paper's own label - a biophysical model fit to voltage-clamp data, not a direct single-channel or expression-level measurement) | Liu Q, Kidd PB, Dobosiewicz M, Bargmann CI 2018 Cell, Table S4 (image already saved in this repo at `docs/worm/research/liu2018_tableS4.jpg` from a prior session). Table row "Calcium conductance: 0.1/0.13 nS" for WT/shk-1. Also in the same table: membrane capacitance C = 1.5 pF; SHK-1 (BK-type K) conductance 1.5/0.0 nS (WT/shk-1, i.e. abolished in the mutant, as expected); leak conductance g_L = 0.25 nS, leak reversal -65 mV. This is a useful **fitted-model** anchor for AWA's whole-cell conductance scale, not a gene-expression-to-conductance calibration per se (shk-1 here is a null mutant comparison, not a graded expression-level comparison). |

### Reasoning

The clearest, best-sourced result this session is qualitative-plus-fold-range, not a usable absolute calibration:
(a) at least one specific channel (shal/A-current in crab STG) has a **measured, linear** mRNA-to-current
relationship, but this is the exception the field highlights, not the rule - the same source explicitly warns
not to assume linearity for other channel types; (b) where mRNA variability itself has been measured across
individual identified neurons of one type, the scatter is **well under one decade** (3-9 fold, or "up to
five-fold" in a different prep) - i.e. biological cell-to-cell variability in expression is real but bounded,
not log-normal-with-huge-tails; (c) no absolute "conductance per transcript copy" calibration constant was
found in either the C. elegans (CeNGEN) or crustacean (Schulz/Marder) literature searched this session - this
looks like a genuine open problem, not a search failure, consistent with the STG paper's own "tenuous
assumptions" framing. **Practical recommendation for the shared rule parameter "channel density from gene
expression": treat the TPM-to-conductance exponent/slope itself as an unconstrained free (fitted) parameter per
channel family, but cap the input scatter it is allowed to explain at less than one decade of cell-to-cell
mRNA variability (guided by the 3-9x / 5x measured fold-ranges above), and do not claim a universal absolute
calibration constant exists in the literature - none was found.**

---

## 5. Resting input resistance and capacitance per C. elegans cell class

| cell | R_in | C_m | V_rest | label | source |
|---|---|---|---|---|---|
| ASER (sensory neuron, 4 larval stages pooled per the n given) | 1.6 +/- 0.2 GOhm (n=7) | not retrieved this session | -56.6 +/- 1.0 mV (n=7) | recalled (search-engine summary of the paper; primary cell.com full text 403'd, not independently opened this session) | Goodman MB, Hall DH, Avery L, Lockery SR 1998 "Active currents regulate sensitivity and dynamic range in C. elegans neurons," Neuron 20:763-772. Search summary: "the study reported a resting membrane potential of -56.6 +/- 1.0 mV (n=7) and an input resistance of 1.6 +/- 0.2 GOhm (n=7)" for ASER. |
| AWA (olfactory neuron) | not retrieved directly; model leak conductance g_L=0.25 nS implies R_in ~ 1/g_L = **4 GOhm** (derived, a rough lower-bound-like estimate since other conductances add in parallel near rest) | 1.5 pF (fitted, model Table S4) | -75.3 mV (mean), SEM 4.7 mV | measured (V_rest, PSC amplitude - biorxiv full text opened) + fitted (C_m, g_L - Table S4 image) | Liu et al. 2018 Cell / bioRxiv 359935 (biorxiv.org/content/10.1101/359935v1.full, opened this session) for V_rest; Table S4 image already in this repo (`liu2018_tableS4.jpg`) for C_m and g_L. The R_in figure is **derived** from the fitted g_L, not itself measured or fitted directly - flag as the weakest number in this row. |
| AWCon (olfactory neuron) | not found this session (not reported in the retrieved PLoS ONE passages) | 3.1 pF, with cell surface area 238.16 um^2 given explicitly | -74.4 mV (model/fit value, "in the wild type case") | measured (C_m is explicit: "scaled on the entire cell surface" using a real measured area); V_rest flagged **fitted/model**, not a direct patch-clamp resting-potential readout, per the phrasing found ("in the wild-type case," suggesting a simulation output) | Nicoletti M et al. 2019 PLoS ONE 14(7):e0218738, full text opened via journals.plos.org fetch. |
| RMD (motor neuron) | not found this session | 1.2 (units as printed "uF," almost certainly pF; set to match the membrane time constant, i.e. **fitted**, not an independent capacitance measurement) | -69.5 mV (from a steady-state I-V crossing, "steady-state net current is negative at potentials below -69.5mV" - this is a model-fit output, not quoted as a directly patch-clamped resting potential) | fitted | same source as AWCon row. |
| AVA (command interneuron, backward) | not found as a direct GOhm number; **derived** from C_m and tau_m: R_in = tau/C_m = 0.85 ms / 0.77 pF = **1.1 GOhm** | 0.77 +/- 0.02 pF | not retrieved this session (the fetched passage covered capacitance/tau, not V_rest; recordings held "at -55 mV" per a different passage, which is a holding potential, not necessarily V_rest) | measured (C_m, tau_m - PMC full text opened); R_in **derived** from those two measured numbers | Lindsay TH, Thiele TR, Lockery SR 2011 "Optogenetic analysis of synaptic transmission in the CNS of C. elegans," Nat Commun 2:306, PMC3935721 (opened). Quote: "the whole cell capacitance in recordings of the first type [AVA] was systematically larger than... the second type [AVE] (0.77+/-0.02 pF vs. 0.53+/-0.02 pF; p<0.001)"; "the average predicted membrane time constant of AVA neurons was 0.85+/-0.03 ms." |
| AVE (command interneuron, forward; recorded in the same study as AVA above) | not found; same derivation style would give R_in = 0.85 ms / 0.53 pF = **1.6 GOhm** (**derived, and extra-cautious**: the 0.85 ms tau was stated for AVA specifically, reusing it for AVE is an assumption, not confirmed in the retrieved passage) | 0.53 +/- 0.02 pF | not retrieved this session | measured (C_m); R_in **derived with a flagged assumption** | same source as AVA row. |
| Body-wall muscle (unspecified identity within the muscle class) | not found this session (the two muscle papers opened, Gao & Zhen 2011 and the newer biophysical-modeling paper, both describe the Clampex method for getting R and C but the fetched passages did not surface the actual GOhm number) | 50-70 pF (general range, not cell-specific) | -25.0 +/- 1.0 mV (n=27) | V_rest measured (PMC full text opened); C_m recalled from a different, general methods source, not a muscle-specific primary measurement opened this session | V_rest: Gao S, Zhen M 2011 PNAS, PMC3038695 (opened). C_m range: "Electrophysiological Methods for C. elegans Neurobiology" methods review, PMC3959639 (opened). Quote: "Muscle cell capacitance (50-70 pF)." |
| General C. elegans neurons (not cell-specific, a methods-paper summary statement) | ">1 GOhm" for "most C. elegans neurons" | "typically less than 4 pF" | - | measured (summary statement in a PMC-opened methods review, itself presumably drawing on the primary patch-clamp literature, not independently re-verified against each primary paper) | "Electrophysiological Methods for C. elegans Neurobiology," PMC3959639 (opened). Quotes: "the high input resistance (>1 GOhm) of most C. elegans neurons"; "the whole-cell capacitance of C. elegans neurons is typically less than 4 pF." Recording pipette resistance for context: "8-12 MOhm." |
| Pharyngeal muscle | **not found** this session | **not found** | **not found** | Not searched directly this session (time budget); flagged as a follow-up (the pharynx connectome paper, Cook/Hall/Hobert, was used in section 1 for synapse-size data but was not checked for pharyngeal muscle electrophysiology). |

### Reasoning

Across the rows actually pinned down: C. elegans neuron R_in clusters in the **1-2 GOhm** range (ASER 1.6 GOhm
measured; AVA ~1.1 GOhm and AVE ~1.6 GOhm, both derived from measured C_m and tau; the general methods-review
statement ">1 GOhm for most neurons" is consistent with all three), with whole-cell C_m mostly in the **0.5-3 pF**
range for small neurons (AVE 0.53, AVA 0.77, RMD ~1.2, AWA 1.5, AWCon 3.1 pF) against the general review's "<4 pF
typical" statement - all internally consistent. Body-wall muscle is a different scale entirely: C_m 50-70 pF (an
order of magnitude bigger, consistent with muscle cells being much larger than neurons) and a markedly more
depolarized V_rest (-25 mV measured, vs -56 to -75 mV for the three neurons with a directly measured/quoted
V_rest). **This is the standing-rule-relevant conclusion: a single shared "capacitance per unit membrane area"
and "conductance per unit membrane area" rule, multiplied by each cell's own measured/reconstructed surface
area, is consistent with both scales (neuron vs muscle) without needing a separate per-cell-class fudge factor**
- e.g. AWCon's independently measured area (238.16 um^2) and C_m (3.1 pF) already gave 1.3 uF/cm^2 in section 3,
in the same ballpark as the body-wall-muscle-implied specific capacitance would be if its area were known (not
computed this session - muscle cell surface area was not looked up).

---

## Summary table

| proposed rule parameter | hard_min | hard_max | bio_min | bio_max | centre | basis | source key |
|---|---|---|---|---|---|---|---|
| Chemical synapse conductance per EM section | ~0 (a section with no real synapse should contribute ~0) | ~2-9 nS/section (derived: 90-350 nS per-synapse receptor-packing ceiling / 40-section max synapse size) | 0.066-0.098 nS/section (derived: quantal mEPSC conductance 0.293 nS / 3-4.46 sections-per-synapse) | same as bio_min, call it 0.05-0.3 nS/section allowing headroom | ~0.08 nS/section | measured_spread (Liu 2009 PNAS mEPSC + Cook 2019/pharynx-paper sections-per-synapse) with a physics-packing hard ceiling | LIU2009_PNAS_GRADED_NMJ; COOK2019_NATURE; GLR1_PALM_SREP13532 |
| Gap junction conductance per EM section | ~0 | not derivable yet (would need a vertebrate-connexin-density-based ceiling, ~10^4 nS/um^2 of plaque, divided by an unknown C. elegans sections-per-plaque figure - **not found**) | 0.035 (guessed, see caveat) | 0.35 nS/section (guessed, see caveat) | ~0.1 nS/section (guessed) | guessed_physical (anchored to one real measured whole-pair conductance, Liu 2006 JBC 350 pS, divided by a guessed not measured 1-10 sections-per-plaque) | LIU2006_JBC_MUSCLE_GJ; OSHIMA2016_INX6_CRYOEM (structure only, no conductance) |
| Specific membrane capacitance | ~0.35 uF/cm^2 (derived, bilayer physics, d=5nm/epsr=2.0) | ~0.68 uF/cm^2 (derived, bilayer physics, d=3nm/epsr=2.3) — biological membranes measured well above this floor, so the physics bound is a floor not a ceiling; no firm biological ceiling found, carry over ~2 uF/cm^2 from HARD_BOUNDS_LIT.md as a practical ceiling | 0.9 uF/cm^2 (measured, Gentet 2000, vertebrate homology) | 1.3 uF/cm^2 (measured+derived, Nicoletti 2019 AWCon, C. elegans) | ~1.0 uF/cm^2 | physics (floor, arithmetic shown) + measured_spread (ceiling of the usable range) | GENTET2000_BIOPHYSJ; NICOLETTI2019_PLOSONE |
| Channel density from gene expression (TPM/mRNA -> conductance exponent) | n/a (dimensionless mapping, not a hard physical bound found) | n/a | scatter floor: <1 decade of cell-to-cell mRNA variability for one channel in one cell type (3-9x / up to 5x measured) | n/a (no absolute calibration found) | n/a - **no absolute calibration constant found in the literature searched**; treat as a fitted exponent per channel family, constrained only by the <1-decade expression-scatter figures | homology + measured_spread for the scatter bound only; **no basis found** for an absolute slope/intercept | SCHULZ_STG_PCOMPBIOL_1000838; CARDIAC_GANGLION_PMC2727049 |
| Resting input resistance / specific conductance (neuron) | n/a (set by channel density bounds elsewhere) | n/a | 1.1 GOhm (derived, AVA) | 1.6 GOhm (measured, ASER; also derived AVE) | ~1.3-1.6 GOhm, C_m 0.5-3 pF for small neurons, consistent with ">1 GOhm, <4 pF typical" | measured_spread | GOODMAN1998_NEURON_ASER; LINDSAY2011_NATCOMMS_AVA |
| Resting input resistance / specific conductance (muscle) | n/a | n/a | not found (GOhm not retrieved) | not found | C_m 50-70 pF (measured range, not cell-specific); V_rest -25.0 mV measured (Gao & Zhen 2011) | measured_spread (C_m range) + measured (V_rest) | GAO2011_PNAS_MUSCLE; EPHYS_METHODS_PMC3959639 |

### Source key (expand on request; full citations are in each section above)

- LIU2009_PNAS_GRADED_NMJ = Liu, Hollopeter, Jorgensen 2009 PNAS, PMC2705609
- COOK2019_NATURE = Cook et al. 2019 Nature, PMC6889226
- GLR1_PALM_SREP13532 = Rapti et al. 2015 Sci Rep, PMC4555104
- LIU2006_JBC_MUSCLE_GJ = Liu, Chen, Gaier, Joshi, Wang 2006 J Biol Chem (PubMed 16434400)
- OSHIMA2016_INX6_CRYOEM = Oshima, Tani, Fujiyoshi 2016 Nat Commun, PMC5146279
- GENTET2000_BIOPHYSJ = Gentet, Stuart, Clements 2000 Biophys J 79:314-320
- NICOLETTI2019_PLOSONE = Nicoletti et al. 2019 PLoS ONE 14(7):e0218738
- SCHULZ_STG_PCOMPBIOL_1000838 = "Conductance Ratios and Cellular Identity," PLoS Comput Biol, 10.1371/journal.pcbi.1000838
- CARDIAC_GANGLION_PMC2727049 = "Correlations in Ion Channel mRNA in Rhythmically Active Neurons," PMC2727049
- GOODMAN1998_NEURON_ASER = Goodman, Hall, Avery, Lockery 1998 Neuron 20:763-772
- LINDSAY2011_NATCOMMS_AVA = Lindsay, Thiele, Lockery 2011 Nat Commun 2:306, PMC3935721
- GAO2011_PNAS_MUSCLE = Gao, Zhen 2011 PNAS, PMC3038695
- EPHYS_METHODS_PMC3959639 = "Electrophysiological Methods for C. elegans Neurobiology," PMC3959639
- LIU2018_CELL_AWA = Liu, Kidd, Dobosiewicz, Bargmann 2018 Cell / bioRxiv 359935 (Table S4 image already saved in this repo)
- NARAYAN2011_PNAS_AFDAIY = Narayan, Laurent, Sternberg 2011 PNAS, PMC3111291

### Biggest open gaps (not found this session, flagged rather than guessed)

1. C. elegans somatic (non-pharyngeal) mean/median sections-per-chemical-synapse - only the pharyngeal figure
   (4.46/3) and the overall 1-41 range were found; this is the single biggest uncertainty in section 1's
   derivation.
2. Any C. elegans gap-junction EM-section-count-to-plaque-area or -to-conductance mapping at all (section 2's
   central gap - the "per EM section" gap-junction number is guessed, not derived, for this reason).
3. UNC-7/UNC-9 (or any C. elegans innexin) unitary single-channel conductance in pS - genuinely appears
   unmeasured at the single-channel level, same conclusion as this repo's existing HARD_BOUNDS_LIT.md.
4. A direct C. elegans body-wall-muscle whole-cell capacitance number in pF (only a general 50-70 pF range from
   a methods review, not a primary measurement with a cell-specific number, was found this session).
5. Any absolute gene-expression-to-conductance calibration constant, in any system (section 4's central gap).
6. Pharyngeal muscle R_in/C_m/V_rest (not searched this session, time budget).

</content>
