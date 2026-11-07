# Hard physical bounds: literature

Date: 7 Nov 2026

Scope: hard physical/chemical ceilings and floors on model parameters (what physics and chemistry forbid
for any animal cell), not what C. elegans typically does. Free sources only (PMC, bioRxiv, BioNumbers,
open textbooks, lab pages). Each item gives the number, exact source, a quote/paraphrase, and a label:
**measured** (the source was actually opened and the number seen in it) or **recalled** (known from training,
source not opened in this session).

---

## 1. Maximum ion-channel packing density and channel footprint

- **Nicotinic AChR, crests of junctional folds: 20,000-25,000 receptors/um^2.** Salpeter MM, Eldefrawi ME (1973)
  "Sizes of end plate compartments, densities of acetylcholine receptor and other quantitative aspects of
  neuromuscular transmission," J Histochem Cytochem 21(9):769-778. PubMed abstract page
  https://pubmed.ncbi.nlm.nih.gov/4354891/. Paraphrase from secondary sources citing this paper: "the receptor
  site density at the crests of the junctional folds is estimated to be 20,000-25,000/um^2." Label: **recalled**
  (full text is paywalled; only the PubMed abstract page and secondary citations were opened, not the number
  itself inside the primary PDF).

- **Whole mouse endplate total: 3x10^7 AChR per endplate** (not a density, but the BioNumbers-cited primary
  count). BioNumbers BNID 115054, https://bionumbers.hms.harvard.edu/bionumber.aspx?id=115054 , citing
  Barnard EA, Wieckowski J, Chiu TH (1971) Nature 234(5326):207-9, and Porter CW et al. (1973) Nat New Biol
  241(105):3-7. Quote: "3e+7 receptors/end plate," method "radioactive labeling with 3H-alpha-bungarotoxin
  followed by electron microscope autoradiography of mouse diaphragm endplates." Label: **measured** (page
  opened directly).

- **Nav channels, node of Ranvier: ~1200-1500/um^2** (mammalian), with some amphibian nodes reported up to
  5000/um^2. Secondary summaries point to a freeze-fracture study, rat optic nerve, ~1400/um^2, and the
  classic estimate "~1500/um^2 at the node, about 25x higher than in the internode." Primary PNAS 1977 paper
  (Rosenbluth J or similar, Proc Natl Acad Sci USA 74(1):211-215) could not be opened (403 Forbidden on the
  PDF link). Label: **recalled**.

- **Footprint of a tetrameric channel (Kv1.2, Long/Campbell/MacKinnon 2005 Science crystal structure):**
  overall tetramer dimensions reported as approximately 135 Å x 95 Å x 95 Å. Treating the in-membrane
  cross-section as a disk of diameter ~95 Å gives a footprint of ~71 nm^2 per channel, i.e. a geometric upper
  bound of roughly 1.4x10^4 channels/um^2 if channels were close-packed with no other protein or lipid between
  them. This is consistent in order of magnitude with the measured AChR crest density above (20,000-25,000/um^2
  for a receptor with a smaller, more compact footprint than Kv1.2). Source: Long SB, Campbell EB, MacKinnon R
  (2005) "Crystal structure of a mammalian voltage-dependent Shaker family K+ channel," Science 309(5736):897-903,
  https://www.science.org/cms/asset/b7b48978-d95c-4699-beab-2f49b82a48a3/pap.pdf (dimensions found via search
  snippet of this paper, not confirmed by opening the full PDF). Label: **recalled** for the exact Å figures;
  the derived 71 nm^2 / 1.4x10^4 per um^2 figure is **derived** from that recalled number, not itself in any
  source.

**Practical hard ceiling for the model:** treat ~2x10^4 channels/um^2 as an absolute physical ceiling for any
single channel type (measured AChR crest density, the highest directly measured value found), and note that
geometric packing (tetramer footprint) independently gives the same order of magnitude.

---

## 2. Unitary conductances (single-channel, picosiemens)

All values below came from search-engine snippets of secondary and primary sources, not from directly opened
and read primary PDFs (several primary PDFs were paywalled or returned 403). All labelled **recalled** unless
noted. Treat these as a sanity-check range, not citation-grade; re-verify any specific number before it goes
into the ledger with a "published_fit" or "measured" tag.

- **BK/Slo1 (KCa1.1):** ~250-300 pS in symmetrical 150 mM K+ (up to ~600 pS at saturating K+). This is the
  largest conductance reported for a K+-selective channel. Secondary sources citing the BK channel literature
  (e.g. Cui, Cox, Aldrich lineage of papers); bioRxiv 2025.10.05.680598 "Evolution towards higher unitary
  conductance in mammals makes BK channels more efficient and precise" discusses this family's conductance range.
- **Slo2/KNa (Slick/Slack, KCNT1/2):** Slick (Slo2.1) ~141 pS, Slack (Slo2.2) ~183 pS, chord conductance at +80 mV
  in 130 mM symmetrical K+; some native KNa currents reported up to ~201 pS. Bhattacharjee A, Kaczmarek LK and
  colleagues' Slick/Slack electrophysiology papers (J Neurosci 2003, 2007).
- **Kv/Shaker:** ~20-25 pS at 100-150 mM K+, rising to ~45-60 pS at saturating (3 M) symmetric K+ (an
  unphysiological ceiling, not a biological one). A single point mutant has been reported with "unusually high"
  conductance (Pérez-Cornejo/Oliva group paper on a Shaker Kv point mutant).
- **Kir (inward rectifier):** ~2-33 pS across Kir2.1 and relatives, 150 mM external KCl.
- **SK (small-conductance Ca-activated K):** <20 pS (hence the name).
- **KCNQ:** ~2-10 pS (KCNQ1 in kidney).
- **ERG/EAG (KCNH family):** ERG (Kv11.1/hERG) ~10-13 pS in symmetrical high K+, dropping to ~1-2 pS at
  physiological K+; EAG (rEag1) ~7.5 pS.
- **L-type Ca channel:** ~25 pS with Ba2+ as charge carrier (common surrogate because Ca2+ itself gives very
  small currents); only ~2.4 pS with 2 mM physiological Ca2+ as the charge carrier; one study gives 16.6 pS
  with 70 mM Ba2+.
- **N-type Ca channel:** ~14-20 pS. **P-type:** ~9-20 pS. **Q-type:** ~16 pS. (Figures from rat sensory/moto­neuron
  single-channel surveys, e.g. the "single-channel properties of four calcium channel types in rat motoneurons"
  line of work, PMC6578168 and related.)
- **NALCN:** ~27 pS (canonical subunit composition).
- **ENaC/DEG (vertebrate):** ~4-8 pS (commonly cited "5 pS channel"; up to 8 pS with Li+ as charge carrier).
  **MEC-4 (C. elegans DEG/ENaC, touch receptor neurons):** no unitary conductance value was found in the sources
  opened; this looks like it has not been directly patch-clamped at the single-channel level (the channel's
  native context, a punctate mechanosensory complex, is hard to patch). Flag as *not found* rather than guessed.
- **Nicotinic AChR (muscle):** fetal-type ~39 pS, adult-type ~59 pS (vertebrate endplate); neuronal/sympathetic
  nAChR ~27-48 pS (mean ~37 pS in 1 mM Ca2+).
- **GABA-A:** multiple conductance states, roughly 12, 20, 30, 45 pS, with ~30 pS the most common "main state"
  for gamma-subunit-containing receptors and ~22 pS for delta-containing receptors; native channels span
  roughly 10-90 pS overall.
- **GluCl (glutamate-gated chloride, nematode/invertebrate):** ~23 pS (homomeric GluClR, the channel used as
  the ivermectin-silencing tool, Slimko/Lester-type constructs).
- **Gap junctions, connexins (vertebrate):** wide range, from a few pS (Cx30.2, Cx36) up to 200-300 pS (Cx50,
  Cx37).
- **Gap junctions, innexins (C. elegans UNC-7/UNC-9):** described only as "low conductance," with whole
  cell-pair junctional conductance in body-wall muscle up to ~350 pS (not a unitary single-channel value; this
  is the summed conductance of a cell-cell electrical synapse, not one channel). Pereda/Starich/Shaw group
  papers (e.g. "Low conductance gap junctions mediate specific electrical coupling in body-wall muscle cells of
  C. elegans," PubMed 16434400) and "Interactions between innexins UNC-7 and UNC-9..." (PMC2694797). No
  unitary (single-channel, pS) conductance for an isolated UNC-7 or UNC-9 innexin hemichannel was found in the
  sources opened; flag as *not found* for the single-channel number specifically.

**Working hard ceiling for any single ion-selective plasma-membrane channel:** ~300 pS (BK/Slo1 upper measured
range), with up to ~600 pS only under non-physiological saturating ion concentrations. Below ~5 pS (ENaC) is
the practical low end for a channel still called "conducting" rather than a near-silent leak.

---

## 3. Specific membrane capacitance

- **Pure lipid bilayer:** reported values cluster around 0.4-1 uF/cm^2 depending on composition and thickness;
  one secondary source gives "a typical specific capacitance value for lipid bilayers... 0.65 uF/cm^2."
  Classic planar bilayer work (e.g. the Mueller/Rudin-type "black lipid membrane" literature) is the usual
  primary source but was not opened directly. Label: **recalled**.
- **Biological (neuronal) membranes:** BioNumbers lists ~0.88-0.9 uF/cm^2 for rat neural tissue (BNID
  110761, "tau = Cm/Gm," https://bionumbers.hms.harvard.edu/bionumber.aspx?s=n&v=0&id=110761 — page title
  snippet seen via search, not opened directly in this session; treat as **recalled**, not measured). Gentet,
  Stuart and Clements (2000) "Direct measurement of specific membrane capacitance in neurons," Biophys J
  79(1):314-320, is the paper Ben's prompt names for the ~0.9 uF/cm^2 figure; a secondary summary paraphrased
  its range as "1-2 uF/cm^2" for neuronal membranes, which is inconsistent with the commonly cited 0.9 uF/cm^2
  headline number and could not be resolved without opening the PDF directly (it did not open in this search
  pass). Label: **recalled**, flagged as needing direct verification before use.
- **Practical bound for the model:** treat ~0.6-1.0 uF/cm^2 as the normal biological range, with a hard
  physical floor near the thinnest possible pure-lipid value (~0.4 uF/cm^2, thicker/more ordered bilayers) and
  no real ceiling above ~1-2 uF/cm^2 for a plasma membrane with normal lipid composition (higher values would
  need abnormally thin or high-dielectric membrane, not biologically plausible).

---

## 4. Specific membrane resistance and axial/saline resistivity

- **Pure lipid bilayer resistance:** ~10^6-10^8 ohm*cm^2 for unmodified ("black") planar lipid bilayers.
  Secondary summary of the classic bilayer biophysics literature (Mueller/Rudin-era and later). Label: **recalled**.
- **Biological cell membrane resistance:** reported range ~10-10^6 ohm*cm^2 "depending on the number of open
  ion channels" (i.e. a membrane full of open channels approaches the low end, a membrane with channels shut
  approaches the bilayer-like high end). Label: **recalled**.
- **Cytoplasm (axoplasm) axial resistivity:** squid giant axon values cluster around 30-100 ohm*cm depending
  on the study; one source gives "longitudinal resistivity 30 to 60 ohm*cm," another gives "average internal
  specific resistance 71 ohm*cm, about 2.9x that of seawater." Primary sources: Cole KS and Hodgkin AL/Rushton
  WAH axoplasm-resistivity papers from the 1930s-1950s (Resistivity of axoplasm I and II, J Gen Physiol), found
  via search snippets, not opened directly. Label: **recalled**.
- **Saline/physiological bath resistivity:** 0.9% NaCl saline at 22 C has resistivity ~69 ohm*cm; seawater
  ~35 ohm*cm; saturated NaCl ~5 ohm*cm (floor for any aqueous NaCl solution). Label: **recalled**.
- **Practical bounds for the model:** cytoplasm axial resistivity should stay in roughly 30-200 ohm*cm (wider
  than the squid-specific figure to allow for smaller, more crowded invertebrate cytoplasm); membrane specific
  resistance has no meaningful hard physical ceiling for a living membrane (approaches the bilayer limit,
  10^6-10^8 ohm*cm^2, only when essentially channel-free) and a floor set by how many channels can physically
  fit (see item 1) and how big each one's single-channel conductance is (see item 2).

---

## 5. Q10 of biological rates

- **Typical channel gating / enzyme Q10:** most ion-channel gating steps and most mesophilic enzyme reactions
  have Q10 ~2-5 ("for most enzyme-catalysed reactions, Q10 ~2 up to the optimum temperature... rate roughly
  doubles for every 10 C rise"; channel gating commonly cited as Q10 ~3). Secondary summaries of standard
  enzyme-kinetics and channel-biophysics teaching material. Label: **recalled**.
- **Diffusion-like processes** (ion permeation through an open channel, free diffusion): Q10 ~1.2-1.4, close to
  the Q10 of aqueous diffusion itself, far below gating Q10. Label: **recalled**.
- **Thermo-TRP channels, the largest Q10 values known for a gating process:** TRPV1 Q10 ~26-40 (one source
  "Q10 of TRPV1 is ~40," another "~26"), TRPM8 Q10 ~24-28, TRPV3 gating Q10 >20. These numbers recur across
  several reviews and a PMC paper "Thermodynamic implications of high Q10 of thermo-TRP channels in living
  cells," https://pmc.ncbi.nlm.nih.gov/articles/PMC4736789/ (found via search snippet, not opened directly).
  Label: **recalled**.
- **C. elegans AFD thermosensor:** one source (search snippet of "Bidirectional temperature-sensing by a single
  thermosensory neuron in C. elegans" and/or "The extraordinary AFD thermosensor of C. elegans," Pflugers Arch
  2018, Clark lab line of work) gives Q10 ~2.8 for AFD's thermoreceptor current at the behaviourally relevant
  range, but a different figure describes an extraordinarily steep temperature-evoked current with an
  *apparent* Q10 "> 10^15," attributed to a strong downstream amplification step (not a simple Arrhenius
  process) rather than a literal doubling-per-10C rate law. Both figures came from search snippets; neither
  primary PDF was opened. Label: **recalled**, and flagged: the >10^15 figure is almost certainly an apparent/
  fitted amplification coefficient, not a thermodynamically meaningful Q10 for a single molecular step — do not
  use it as a hard bound on any single reaction rate without reading the primary paper first.
- **Practical bound:** treat Q10 ~1-5 as the range for ordinary gating/metabolic steps, and allow up to ~Q10
  40 only for an explicitly thermoTRP-like channel, never as a default.

---

## 6. Kinetic speed limits

- **Diffusion-limited bimolecular association rate constant (Smoluchowski):** k_on = 4*pi*D*R; commonly quoted
  ceiling for protein-protein or small-ligand-protein association is ~10^9-10^10 M^-1 s^-1, with ~1x10^9 M^-1 s^-1
  often used as the standard "diffusion-controlled" reference value. Secondary summary citing the classical
  Smoluchowski treatment (e.g. Northrup/Erickson-type diffusional-association papers, PMC2279981 "Realistic
  protein-protein association rates..."). Label: **recalled**.
- **Fastest measured ion-channel gating:** nicotinic AChR channel-opening rate constant (beta) ~60,000-80,000
  s^-1 (time constant ~12-17 microseconds), with some patches giving >100,000 s^-1; this is described as among
  the fastest conformational transitions of any ligand-gated channel. Source: Maconochie DJ, Steinbach JH
  (1998) "The channel opening rate of adult- and fetal-type mouse muscle nicotinic receptors activated by
  acetylcholine," J Physiol, found via PubMed/Wiley search snippet (9481672), not opened directly. Label:
  **recalled**.
- **Fastest ligand-gated channel rise times:** experimentally achievable solution-exchange-limited 10-90% rise
  times of ~24-80 microseconds have been used to probe nicotinic receptor kinetics (a methodological limit, not
  a biological one); the biological opening step itself is faster than this measurement limit. Label: **recalled**.
- **Practical bound:** no single-channel elementary gating step should be modelled faster than roughly
  10-20 microseconds (the fastest measured, nicotinic AChR), and no bimolecular binding step faster than the
  diffusion limit, ~10^10 M^-1 s^-1.

---

## 7. Diffusion coefficients

- **Free Ca2+ in water:** not pinned down precisely in this search pass; aqueous ionic diffusion coefficients
  for small cations are typically ~0.5-1x10^-5 cm^2/s = 500-1000 um^2/s (general physical chemistry knowledge).
  Label: **recalled**, not sourced to a specific citation in this session.
- **Free/buffered Ca2+ in cytoplasm:** Allbritton NL, Meyer T, Stryer L (1992) "Range of messenger action of
  calcium ion and inositol 1,4,5-trisphosphate," Science 258(5089):1812-1815, is the classic source for the
  commonly cited ~220-225 um^2/s free-Ca2+-in-cytosol figure (lower than free water because of viscosity/
  crowding) and a buffered effective diffusion coefficient roughly an order of magnitude lower when fast
  endogenous buffers are included. A more recent paper, Nakamura et al. (Biophys J, PMC8510970, "High rates of
  calcium-free diffusion in the cytosol of living cells"), reports measured D_Ca in living cytosol larger than
  the classical ~220 um^2/s estimate, i.e. the 1992 figure may be a lower bound rather than the true free value.
  Label: **recalled** (search snippets only; Allbritton et al. 1992 PDF not opened directly in this session).
- **Small molecules in cytoplasm (general):** metabolites such as ATP, ADP, free Ca2+ are commonly cited around
  ~100-500 um^2/s depending on the molecule and the specific cytoplasm. Label: **recalled**.
- **GFP (a 27 kDa globular protein, a useful generic "protein-sized molecule" reference) in cytoplasm:**
  BioNumbers BNID 112266 and 101997/100193 give ~sim27 um^2/s in CHO (mammalian) cytoplasm and ~7.7 um^2/s in
  E. coli cytoplasm, versus faster diffusion in water (BNID 100301). Pages found via search snippet only, not
  opened directly. Label: **recalled**.
- **Neuropeptide in tissue:** somatostatin effective diffusion coefficient in brain extracellular space
  ~8.9x10^-7 cm^2/s = 8.9 um^2/s (a tissue/extracellular-space value, slower than free solution because of
  tortuosity). Source referenced via search snippet, likely Nicholson C and colleagues' "Diffusion coefficients
  of neurotransmitters and their metabolites in brain extracellular fluid space," PubMed 2866468, not opened
  directly. Label: **recalled**.
- **Practical bounds:** free small ions/metabolites in cytoplasm should sit in roughly 100-600 um^2/s; soluble
  globular proteins and neuropeptides roughly 10-50 um^2/s in cytoplasm and lower still (single digits to ~10)
  in a tissue/extracellular-space context; nothing modelled should diffuse in cytoplasm faster than the free
  small-ion ceiling (~600-1000 um^2/s, essentially the water value) since cytoplasm is always at least as
  viscous/crowded as water.

---

## 8. Hill coefficients

- **Hard rule:** the Hill coefficient cannot physically exceed the number of cooperating binding sites on the
  sensor molecule; a fitted Hill coefficient is a lower-bound estimate of the number of interacting sites, not
  an exact site count. General biochemistry teaching point, found via multiple secondary sources (Sciencedirect
  "Hill Coefficient" overview, PhysiologyWeb, etc.). Label: **recalled**.
- **Dodge RB, Rahamimoff R (1967)** "Co-operative action of calcium ions in transmitter release at the
  neuromuscular junction," J Physiol 193(2):419-432 (PubMed 6065887) — classic finding that frog NMJ
  transmitter release rises roughly as the 4th power of external Ca2+, consistent with ~4 Ca2+ ions needed per
  release event (a Hill-like coefficient of ~4, matching calmodulin's 4 EF-hand Ca2+-binding sites and
  synaptotagmin's multi-Ca2+ sensor model). Some later work suggested the true cooperativity could be closer to
  5. Found via search snippet, not opened directly. Label: **recalled**.
- **Hill coefficients above 5 reported physiologically:** most native allosteric proteins/receptors stay at
  n_H <=4-5 (matching their real site count); values much higher than 5 (5-25) have been reported only for
  engineered/aggregated constructs (e.g. multi-tetramer insoluble hemoglobin polymers where several oxygen-
  binding tetramers cooperate as a super-complex), not for a normal single physiological receptor or enzyme.
  Label: **recalled**.
- **Practical bound for the model:** cap any single binding-cooperativity parameter at n_H <= the actual known
  number of ligand-binding sites on that specific protein (4 for a classical EF-hand/C2-domain Ca2+ sensor,
  etc.); treat n_H > 5 as physically implausible for any single, non-aggregated receptor or channel gate used
  in this model.

---

## 9. Ion concentrations in nematodes / C. elegans

- **Standard C. elegans patch-clamp bath solution** (used across the Goodman 1998 / Liu 2018 AWA / Gao and Zhen
  2011 line of work): one commonly cited formulation is 145 mM NaCl, 5 mM KCl, 1 mM CaCl2, 5 mM MgCl2, 11 mM
  dextrose, 5 mM HEPES, pH 7.3; a related variant is 145 mM NaCl, 2.5 mM KCl, 5 mM CaCl2, 1 mM MgCl2, 20 mM
  glucose. Label: **recalled** (from search snippets of secondary descriptions of these papers' methods, not
  the primary methods sections themselves).
- **Standard pipette (intracellular-mimicking) solution:** 115 mM K-gluconate, 15 mM KCl, 5 mM MgCl2, 10 mM
  HEPES, 0.25 mM CaCl2, 20 mM sucrose, 5 mM EGTA, 5 mM Na2ATP, 0.5 mM NaGTP. Label: **recalled**, same caveat.
  These two together put extracellular Na+ ~145 mM, extracellular K+ ~2.5-5 mM, extracellular Ca2+ ~1-5 mM in
  the experimental bath (not necessarily the animal's true pseudocoelomic fluid), and intracellular K+ ~130 mM
  (gluconate + Cl), intracellular free Ca2+ heavily buffered near 0 by 5 mM EGTA for recording stability.
- **True pseudocoelomic fluid ion concentrations:** not found as a directly measured number in this search
  pass. A 2022 method paper, "Determination of ions in Caenorhabditis elegans by ion chromatography" (PubMed
  35689916), validates a method for measuring whole-worm Na, K, Ca, Mg, Cl content but the search snippet did
  not give the actual concentrations found; flag as *not found* here, worth a follow-up fetch of that paper
  directly if whole-animal ion content matters for the ledger.
- **Intracellular free Ca2+ in C. elegans neurons:** resting levels commonly cited around 50-200 nM (one
  source: "cultured mechanosensory neurons had a resting free calcium concentration of approximately 200 nM";
  another: "most neurons have an intracellular calcium concentration of about 50-100 nM at rest"; a third,
  specific to C. elegans: "estimated basal calcium concentrations in C. elegans neurons ranged from about
  60-90 nM"). Peak evoked levels during activity are commonly described as rising 10-100x into the
  sub-micromolar to low-micromolar range. Label: **recalled**.
- **Practical bounds for the model:** extracellular (bath-equivalent) Na+ ~140-150 mM, K+ ~2.5-5 mM, Ca2+
  ~1-5 mM; intracellular K+ ~100-130 mM typical for a healthy excitable animal cell; intracellular free Ca2+
  at rest in the tens-to-low-hundreds of nM, with evoked peaks reaching low micromolar — well below the
  millimolar extracellular Ca2+, which is itself the ultimate ceiling on any model's cytosolic free Ca2+.

---

## 10. Muscle and tissue mechanics

- **Vertebrate skeletal muscle, maximum active isometric stress:** ~0.3 MPa (0.3 N/mm^2), a standard
  biomechanics constant used across species in muscle-tendon architecture calculations. Label: **recalled**.
- **Molluscan catch muscle (e.g. Mytilus anterior byssus retractor muscle, ABRM):** reported maximum tensile
  stress ~10-14 kgf/cm^2 versus ~2.3-3.5 kgf/cm^2 for vertebrate skeletal muscle in the same old-unit papers —
  i.e. catch muscle in the "catch" (tonic, low-ATP-cost) state can sustain roughly 3-6x the stress per
  cross-sectional area of ordinary vertebrate skeletal muscle. In SI units that is roughly 1.0-1.4 MPa for
  catch muscle versus ~0.2-0.35 MPa for vertebrate muscle. Secondary source citing historical catch-muscle
  mechanics papers (reviewed in "Mechanism and Function of the Catch State in Molluscan Smooth Muscle: A
  Historical Perspective," PMC7589332). Label: **recalled**.
- **C. elegans cuticle/body stiffness (Young's modulus):**
  - Backholm M et al. (2013) micropipette-deflection estimate: E ~1.3 +/- 0.3 MPa for the whole-body composite.
  - A separate decomposition (found via search snippet, likely drawing on Park et al. 2007 PNAS and/or Petzold
    et al. 2011) gives layer-specific moduli: cuticle ~75-140 kPa, muscle layer ~600-850 kPa, pseudocoelom
    (internal pressurized core) ~48-185 kPa.
  - These numbers disagree by roughly an order of magnitude depending on whether "stiffness" means the whole
    pressurized composite body (Backholm, ~1.3 MPa) or an isolated layer (the 75-850 kPa decomposition). Label:
    **recalled** for all of the above; none of the primary PDFs (Park 2007 PNAS, Petzold 2011, Backholm 2013)
    were opened directly in this session, so treat these numbers as needing direct verification before use in
    the ledger.
- **Practical bounds:** vertebrate-style striated muscle active stress should not exceed roughly 0.3-0.5 MPa;
  a catch-muscle-like tonic mechanism could justify up to ~1-1.5 MPa if the model ever needs a "better than
  vertebrate" ceiling, but there is no physiological reason to invoke molluscan catch muscle for a nematode.
  Body/cuticle Young's modulus should stay in the ~50 kPa to ~1.5 MPa range depending on which structural
  layer is being modelled.

---

## 11. Na/K-ATPase

- **Maximum turnover rate:** reported values across species/tissue/temperature range from ~27 cycles/s at
  22 C, ~48-70 cycles/s (pig kidney, shark rectal gland, unspecified temperature), ~106 cycles/s at 25 C, up
  to ~150 cycles/s at 37 C (mammalian, physiological temperature). Secondary summaries citing the rate-limiting-
  step biophysics literature on the Na/K-ATPase cycle (e.g. "Rate Limitation of the Na+,K+-ATPase Pump Cycle,"
  Biophys J, Cell Press link seen in search results). Label: **recalled**.
- **Pump density:** ~1400 +/- 800 Na,K-ATPase enzymes/um^2 in HEK293T cell membrane (from a FRET-FCS
  quantification paper, ScienceDirect/PubMed 38643888); inter-pump spacing ~34 nm on average, consistent with
  that density. Label: **recalled**.
- **Free energy of ATP hydrolysis in cells:** standard Gibbs free energy at pH 7 is often quoted as -28 to
  -33.5 kJ/mol, but the actual physiological (non-standard-state, accounting for real cytoplasmic ATP/ADP/Pi
  concentrations) free energy released is larger in magnitude, commonly -50 to -65 kJ/mol. BioNumbers BNID
  103385 (E. coli, Gibbs free energy of ATP hydrolysis) and BNID 101989 (standard Gibbs free energy of ATP
  hydrolysis at pH 7) are the relevant entries, found via search snippet only, not opened directly. Label:
  **recalled**.
- **Practical bounds for the model:** turnover rate per pump should stay within roughly 25-150 cycles/s
  (lower end for sub-physiological/cold temperature, upper end near 37 C); pump density should stay below
  roughly a few thousand per um^2 (measured HEK293 value ~1400/um^2, itself far under the item-1 channel-
  packing ceiling of ~2x10^4/um^2 since the pump is a larger, less densely packable complex); usable free
  energy per ATP hydrolysed in vivo should be taken as -50 to -65 kJ/mol, not the smaller standard-state figure.

---

## 12. Temperature range for C. elegans

- **Standard growth/reproduction range:** ~15-25 C in the lab, with fertility highest around 20 C.
- **Upper limit:** fertility declines above ~25 C and is effectively lost (near-complete male sterility) by
  27 C; chronic heat stress above this causes reproductive failure, though worms may survive (non-reproductively)
  somewhat higher for short periods.
- **Lower limit:** severe cold stress at 2-4 C for 24-48 hours is lethal; the standard cultivation floor is
  well above this (growth essentially stops well below 15 C but brief cold survival down to ~2-4 C is possible
  before lethality sets in with prolonged exposure).
  Source for the above: multiple search snippets of "Temperature Dependence of Cell Division Timing Accounts
  for a Shift in the Thermal Limits of C. elegans and C. briggsae" (Cell Reports), "Experience Modulates the
  Reproductive Response to Heat Stress in C. elegans..." (PLOS ONE, PMC4699941), and "Defects in mating
  behavior are the primary cause of sterility in C. elegans males at elevated temperature" (bioRxiv 655027).
  None opened directly; label: **recalled**.
- **Practical bound for RT/F calculations:** use 2-27 C (275-300 K) as the physiologically survivable range for
  C. elegans, with 15-25 C (288-298 K) as the range where normal reproduction and the model's behavioural
  scoreboard should be evaluated.

---

## 13. pH

- **Cytosolic pH of animal cells generally:** ~7.0-7.4 is the typical steady-state range quoted for most
  mammalian cell types (one source: "most mammalian cells feature a steady-state cytosolic pH of 7.1-7.2"),
  with a wider reported span of 6.45-7.51 across different cell types/compartments. Label: **recalled**.
- **C. elegans intestinal lumen pH:** strongly acidic and spatially graded. Chauhan VM et al. (2013) "Mapping
  the pharyngeal and intestinal pH of Caenorhabditis elegans and real-time luminal pH oscillations using
  extended dynamic range pH-sensitive nanosensors," ACS Nano 7(6) (PubMed 23668893) — search snippet reports
  "pH of viable C. elegans lumen ranged from 5.96 +/- 0.31 in the anterior pharynx to 3.59 +/- 0.09 in the
  posterior intestine." Allman EL, Yates P, Nehrke K (2009) (nehrkelab.com PDF seen via search) describes the
  main intestinal lumen as "weakly acidic (pH ~4.4)" with ultradian oscillations above pH 6 every 45-50 s, tied
  to the defecation motor program. Label: **recalled** (both found via search snippet/title; the ACS Nano PDF
  and the Allman PDF link were not fetched and read directly in this session, so treat the exact numbers as
  needing a direct-read confirmation before use as a hard "measured" ledger entry).
- **Practical bounds:** cytosolic pH anywhere in the model should stay in roughly 6.5-7.5; the C. elegans
  intestinal lumen is a specific, biologically real exception that can go as low as ~pH 3.6-4.4, with
  oscillations up to pH >6 — this is a real, cited extracellular/luminal compartment, not a cytosolic one, and
  should not be used to justify an acidic cytosol anywhere else in the model.

---

## 14. Synaptic vesicle and dense-core vesicle content

- **Small clear synaptic vesicles, acetylcholine:** mammalian cholinergic vesicles ~2,000 ACh molecules;
  Torpedo electric organ vesicles ~20,000 molecules; a commonly cited neuromuscular-junction quantal size is
  ~10,000 ACh molecules per vesicle. The spread (2,000 to 20,000) reflects real biological variation between
  vesicle types/species, not just measurement noise. Label: **recalled**.
- **Small clear synaptic vesicles, glutamate:** ~2,000 glutamate molecules per vesicle is one commonly cited
  figure, consistent with an intravesicular glutamate concentration of roughly 60 mM in a ~40 nm vesicle;
  BioNumbers also lists a generic "neurotransmitter molecules in typical synaptic vesicle (at 150 mM): ~1790
  copies/vesicle" entry (BNID not captured in this search pass, found via a search snippet referencing BNID
  107302 "Concentration of glutamate in synaptic vesicle, Rat, https://bionumbers.hms.harvard.edu/bionumber.aspx?s=n&v=2&id=107302").
  Label: **recalled** (BioNumbers page title seen, not opened directly).
- **General order of magnitude for small synaptic vesicles:** roughly 10^3-10^4 neurotransmitter molecules per
  vesicle across the literature, i.e. "on the order of 10,000" is a reasonable round ceiling for a small clear
  vesicle, with ~2,000 a reasonable typical/lower figure.
- **Dense-core vesicles, neuropeptide content:** dense-core vesicles are reported to carry neuropeptide at a
  much lower intravesicular concentration than synaptic vesicles carry small-molecule transmitter — one source
  gives "3-10 mM" neuropeptide inside a dense-core vesicle (versus tens-of-mM for a small clear vesicle's
  small-molecule transmitter). No direct "molecules per dense-core vesicle" count was found in this search
  pass; the pool-size paper found (Persoon CM et al., "Pool size estimations for dense-core vesicles in
  mammalian CNS neurons," EMBO J 2018, PMC6187028) reports total DCV counts per neuron (1,400-18,000 DCVs per
  neuron, scaling with neurite length), not molecules per individual vesicle. Flag *not found* for a direct
  molecules-per-DCV count; the 3-10 mM concentration figure combined with typical DCV diameter (~80-120 nm,
  not independently confirmed here) could be used to derive an approximate molecule count if needed, but that
  derivation was not done in this pass. Label: **recalled** for the concentration figure, **not found** for a
  direct per-vesicle molecule count.
- **Practical bounds:** small clear synaptic vesicles, ~10^3-2x10^4 neurotransmitter molecules per vesicle;
  dense-core vesicles, lower intravesicular concentration (3-10 mM) of neuropeptide than small vesicles carry
  of small-molecule transmitter, and a correspondingly smaller absolute molecule count per vesicle once vesicle
  volume is taken into account (DCVs are typically somewhat larger than small clear vesicles, but the
  concentration is much lower, so the net molecule count per DCV is not simply higher).

---

## Items not sourced to a directly opened primary citation

Everything above is labelled per-item, but as a summary: the following sub-items could not be pinned to a
primary source actually opened and read in this session (either paywalled, 403, or not found at all in the
~40-search budget), and should be re-verified before being written into the ledger as "measured":

- Item 1: exact Kv1.2 footprint/area figure from Long et al. 2005 (dimensions found via snippet, not the PDF).
- Item 1: Nav node-of-Ranvier density primary PNAS 1977 paper (403 Forbidden).
- Item 4: axoplasm resistivity primary Cole/Hodgkin-era papers (snippet only).
- Item 9: true C. elegans pseudocoelomic fluid ion concentrations (ion-chromatography paper found but its
  actual numbers were not retrieved; worth a direct follow-up fetch).
- Item 9: MEC-4/DEG channel unitary conductance — likely genuinely not measured at the single-channel level in
  its native context, not just a search failure.
- Item 2: UNC-7/UNC-9 innexin unitary (single-channel) conductance — only whole gap-junction coupling
  conductance was found, not a single-channel pS value.
- Item 10: Park et al. 2007 PNAS and Petzold et al. 2011 primary figures (found only via a secondary
  decomposition, not the original papers).
- Item 13: Chauhan et al. 2013 and Allman et al. 2009 exact pH figures (found via search snippet/title, PDFs
  not fetched and read directly).
- Item 14: a direct molecules-per-dense-core-vesicle count (only intravesicular concentration was found).

</content>
