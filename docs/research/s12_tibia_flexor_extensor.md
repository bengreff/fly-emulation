# Tibia flexor (tidm/tidm2) vs tibia extensor (tilm) — literature extraction

Scope: find published numbers that fix the relative size/force of the Drosophila
femur muscles that move the tibia — tidm (= tibia depressor = flexor, plus
tidm2) vs tilm (= tibia levator = extensor) — for T1 and, if available, T2/T3.

Method: Europe PMC REST API (`fullTextXML`), PMC HTML (new `pmc.ncbi.nlm.nih.gov`
domain when `europepmc` full-text XML 500'd), bioRxiv/arXiv HTML+PDF
(`pdftotext`), and one WebFetch for a paywalled journal page. Every number below
is tagged READ (I saw it in the primary-text file myself), SECONDARY (quoted by
another paper I read, not independently verified), UNVERIFIED (search-engine
synthesis only, not opened), or NOT FOUND. ~37 tool calls used.

Primary sources opened in full text this pass (local cache paths for
reproducibility):
- Guillermin et al. 2026 Sci Adv, PMC13322264 (`/tmp/guillermin.xml`,
  `/tmp/guillermin_suppl/sm.txt` = Table S1 from the supplementary PDF)
- Azevedo, Dickinson, Gurung, Venkatasubramanian, Mann & Tuthill 2020 eLife
  9:e56754, PMC7347388, **including its published decision-letter/author-response
  sub-articles** (`/tmp/azevedo.xml`/`.txt`)
- Baek & Mann 2009 J Neurosci 29(21):6904-6916, PMC6665603 — fetched via
  `pmc.ncbi.nlm.nih.gov` HTML (europepmc fullTextXML 500'd) (`/tmp/baekmann_pmc2.txt`)
- Enriquez et al. 2015 Neuron 86(4):955-970, PMC4441546 — fetched via
  `pmc.ncbi.nlm.nih.gov` HTML (`/tmp/enriquez_pmc.txt`)
- Maqbool, Soler, Jagla et al. 2006 PLoS ONE 1:e122, PMC1762424 (`/tmp/maqbool.txt`)
- Kuan, Phelps, Thomas, Nguyen, Han, Chen, Azevedo, Tuthill, Funke, Cloetens,
  Lee 2020 Nature Neuroscience (the published version of the X-ray
  holographic nano-tomography (XNH) leg dataset), PMC8354006 — fetched via
  `pmc.ncbi.nlm.nih.gov` HTML (europepmc fullTextXML 500'd) (`/tmp/kuan_pmc.txt`)
- Ozdil et al. (FlyMimic), arXiv 2509.06426, main PDF + appendix (23 pages;
  `pdftotext -layout`) (`/tmp/flymimic.txt`)
- Review PMC4740448 (Soler, Laddada & Jagla 2016 Front Physiol) — checked, no
  numeric muscle data (`/tmp/review4740448.txt`)

Blocked / not found this pass:
- **Soler, Daczewska, Da Ponte, Dastugue & Jagla 2004 Development 131:6041**
  — not in PMC/Europe PMC; `journals.biologists.com` returns HTTP 403 to curl
  and, via WebFetch, an explicit paywall ("You do not currently have access
  to this content… Buy This Article $30.00"). This is the one paper that
  almost certainly has the original per-muscle fiber-count table, and I could
  not open it. All numbers attributed to it below are SECONDARY, via other
  papers' citations.
- **Brierley, Rathore, VijayRaghavan & Williams 2012 J Comp Neurol 520:1629**
  — `inPMC:"N"`, not open access; not fetched.
- Guillermin et al. 2026 supplementary PDF Table S1 was retrieved (via the
  Europe PMC `supplementaryFiles` zip) but it only tabulates **phenotype
  incidence under *bi* knockdown** (e.g. "tilm: WT N=16"), not baseline adult
  fiber counts.

---

## 1. Per-muscle fibre counts for the femur muscles (tidm, tidm2, tilm, ltm2)

- **[READ, Kuan et al. 2020 Nat Neurosci, PMC8354006, Results]**: "We
  identified 97 muscle fibers in the femur (Fig. 3h), significantly exceeding
  the 33 to 40 fibers reported previously using fluorescence microscopy
  [ref 38 = Soler et al., 2004]." — This is a **whole-femur total** (all of
  tidm+tidm2+tilm+tirm+ferm+fedm+ltm2 combined, by micro-CT/XNH), not broken
  out per named muscle in the text I could read.
  - The "33 to 40 fibers" figure is **SECONDARY** (Kuan et al.'s citation of
    Soler et al. 2004 — I could not open Soler 2004 itself to confirm which
    femur muscle(s) that range refers to; it reads as if it's also a
    whole-femur total, not tidm/tilm individually, but this is not certain
    from the citing sentence alone).
- **[READ, Kuan et al. 2020, same paragraph]**: "we found that six muscle
  fibers in the femur attach to the long tendon, rather than three as
  previously reported [38]. Two of the six (light red fibers) attach at the
  proximal tip of the long tendon and are innervated by a single motor
  neuron… whereas the other four (dark red fibers) attach more distally and
  are innervated by two different motor neurons." — This is **ltm2** (femur
  long tendon muscle): **6 fibers (READ, direct XNH count)** vs **3 fibers
  (SECONDARY, attributed to Soler et al. 2004)**. This is the single most
  concrete, named-muscle, cross-validated fiber-count number found in this
  pass, but it is for ltm2, not tidm/tilm directly.
- No paper opened in this pass gives a separate adult fiber count for tidm,
  tidm2, or tilm by name. **[NOT FOUND]**
- **[READ, Maqbool, Soler, Jagla et al. 2006 PLoS ONE, PMC1762424, Results/
  Fig. 8]** — not an adult fiber count, but a quantitative **larval
  myoblast-precursor count** for the tilm lineage specifically: "we counted
  the Twi/Lbe/Duf-LacZ positive myoblasts in the dorsal femur tilm… We found
  that in Htl^RNAi third instar discs the number of tilm myoblasts [was]
  34.2; n = 5… was significantly reduced compared with the wild type 55.2;
  n = 5. In contrast, overexpression of the constitutively active form of
  the Htl receptor results in strongly increased number of… tilm myoblasts
  118.5; n = 5." — **Wild-type tilm myoblast count ≈ 55.2 (mean, n = 5 third-
  instar leg discs), T1 leg presumed (not stated), sex not stated.** This is
  a *precursor* count, not the final adult fibre number (myoblasts fuse into
  multinucleate fibres later), and should not be relabeled as an adult fibre
  count. No equivalent tidm myoblast count was given in the same paper for
  direct comparison — only a qualitative statement that "ventrally located
  femur myoblasts [tidm] express significantly higher levels of Lbe than
  those in the dorsal [tilm]" region.
- **[READ, Baek & Mann 2009 J Neurosci, PMC6665603]** gives **motor-neuron**
  counts (not fibre counts), useful as an indirect size proxy: "Lin A
  generates 15 motor neurons that target the tibia and 13 motor neurons that
  target the femur… the long tendon muscle in the tibia (ltm1) is targeted by
  nine Lin A motor neurons… Fe1 and Fe4 target the tibia depressor (tidm),
  and Fe8, Fe9, and Fe10 target the tibia reductor (tirm)… Fe3… targets
  ltm2." No Lin A motor neuron is reported as targeting **tilm**; a single
  **Lin B** motor neuron (Fe1 of Lin B) is reported instead
  (see Enriquez below). Sex/leg: labeled generically as "the leg" (front leg,
  context of whole-mount MARCM clones); not stated per-sex.
- **[READ, Enriquez et al. 2015 Neuron, PMC4441546, Results/Fig. 1]**: "Co1-4
  innervate the trochanter levator muscle (trlm), Tr1, Tr2 innervate the
  femur reductor (ferm) and femur depressor (fedm) muscles, and **Fe1
  innervates the distal part of the tibia levator (tilm) and tibia reductor
  (tirm) muscles**." So the (Lin B-derived) tilm innervation documented here
  is a single motor neuron to its *distal* part only — implying additional,
  unidentified motor neurons (from other lineages) must supply the
  *proximal* part of tilm, which this paper does not enumerate.
- **[READ, Azevedo et al. 2020 eLife, main text, PMC7347388]**: "The muscles
  that control flexion of the Drosophila tibia are innervated by
  approximately 15 motor neurons (Baek and Mann, 2009; Brierley et al.,
  2012)." Also: "Those studies estimated that 2–5 neurons innervate the
  proximal muscle fibers in the femur, similar to the intermediate motor
  neuron, and 8–9 neurons innervate distal muscle fibers, similar to the
  slow motor neuron" (main text, before the sub-articles). And: "Tibia
  flexor motor neurons outnumber the extensor neurons (Baek and Mann, 2009;
  Brierley et al., 2012)" — qualitative only, no extensor MN count given.
- **[READ, but from the published eLife author-response sub-article (sa2),
  not the peer-reviewed main text — flag accordingly]**, Azevedo et al. 2020:
  "8-9 slow motor neurons innervate the distal tibia flexor muscle (muscle
  41)… 2-5 intermediate neurons innervate the proximal portion of the tibia
  flexor muscle that attaches to the tibia flexor tendon (muscle 40); 1 fast
  neuron innervates the rest of the tibia flexor muscle fibers (muscle 40)."
  Also in the same reply: "based on MARCM clone expression in the leg, Baek
  and Mann, 2009 found that six neurons… innervate the tibia flexor muscle,
  whereas Brierley and Williams, 2012, found only two" — an explicit,
  acknowledged **discrepancy between the two cited primary sources** for
  flexor motor-neuron count, unresolved in the reply ("so it is possible
  that more may exist"). Muscle numbering ("muscle 40" = proximal tibia
  flexor, "muscle 41" = distal tibia flexor) is **Miller, 1950** nomenclature,
  used only in this reply, not the main text's tidm/tilm (Soler 2004)
  nomenclature.
- Guillermin et al. 2026 (PMC13322264) reports **qualitative** RNAi phenotype
  data (fibre-*number-reduced* phenotypes) for tarsus muscles (tarm1, tadm,
  talm) but **states "WT" (no detectable phenotype, N=16 legs) for tidm,
  tidm2, tilm, tirm, ltm1 under *bi* knockdown** — i.e. this paper's data do
  not give a baseline fibre count for any femur muscle, only that these five
  femur muscles were *not* perturbed in that specific experiment. **[READ
  the phenotype table itself; NOT FOUND for baseline fibre counts]**
- No T2/T3 comparison for tidm/tidm2/tilm fibre counts, or MN counts, was
  found in any source opened. **[NOT FOUND]**

## 2. Volume / cross-sectional area / fibre length / pennation (micro-CT, confocal)

- **[READ, Kuan et al. 2020, PMC8354006]** — the only directly-measured fibre
  *diameter* figure for Drosophila leg (non-jump/flight) muscle found in this
  pass: "Motor neurons and muscle fibers had large diameters (1–2 μm and
  8–16 μm respectively), enabling straightforward reconstruction throughout
  the dataset." I.e. **leg muscle fibre diameter ≈ 8–16 μm** (whole-leg XNH
  dataset; not broken out by muscle or leg segment in the passage read).
  Imaged leg/sex not stated in the excerpt I read (single adult leg + T1
  VNC, "half of the tibia" imaged — tarsus excluded, "contains no muscles").
- **[READ, FlyMimic / Ozdil et al., arXiv:2509.06426, main text + Appendix]**:
  "We estimated maximum isometric forces from the physiological
  cross-sectional areas (PCSAs) of the muscles, scaling them with a specific
  tension of 28 mN/mm². This value falls between those reported for
  Drosophila jump muscles (37 mN/mm²) [Eldred, Simeonov, Koppes, Yang, Corr &
  Swank 2010 Biophys J 98:1218] and indirect flight muscles (9 mN/mm²)
  [Swank 2012 Methods 56:69]." and (Appendix A.5): "Maximum isometric force
  was computed as the product of a fixed base tension (from prior
  experimental work), a scaling factor (optimized between 0.3–3), and the
  physiological cross-sectional area (PCSA) calculated from CT scans." —
  **The actual PCSA numbers (mm²) for the front-leg tibia flexor vs extensor
  MTUs are never printed in the paper text**; they exist only inside the
  CT-derived geometry used by the optimizer and in Figure S5 (a distribution
  plot, not a table), which text extraction cannot recover. The paper
  explicitly says the femur was modeled with "the fast tibia flexor and
  extensor which dominate force generation at the femur-tibia joint,"
  confirming both muscles were CT-segmented, but **no numeric PCSA, volume,
  fibre length, or pennation angle for either one is given in text.**
  **[NOT FOUND — numeric values only in an unreadable figure/the code
  repository, not fetched here]**
- **[READ, FlyMimic Appendix A.1]**: mid-leg = 7 MTUs, hind-leg = 8 MTUs
  reconstructed from a single X-ray dataset ("Because only a single dataset
  was available for these legs… we restricted our work to anatomical
  reconstruction rather than optimizing the models"). No muscle names, PCSA,
  volumes or forces given for T2/T3. **[NOT FOUND, confirmed again this
  pass]**
- **[READ, Guillermin et al. 2026, PMC13322264]**: tilm and femoral muscle
  *volume* was quantified by confocal/STED + Imaris Surface module ("the
  volumes of the tibia levator muscle (tilm) and femur muscles were
  quantified using the Surface module in Imaris. At least 10 legs per
  genotype were analyzed") but **only as relative comparisons between
  control and gene-knockdown genotypes** (e.g. "tilm volume quantification in
  control versus Lim1 KD showing a muscle volume reduction… P = 0.0006");
  **no absolute volume (μm³) number for wild-type tilm (or any other femur
  muscle) is given in the main text or in the supplementary PDF I could
  parse.** **[NOT FOUND as an absolute number; relative-change data only]**
- **[READ, Pacureanu, Maniates-Selvin, Kuan, Thomas, Chen, Cloetens & Lee
  2019, bioRxiv 653188 — the preprint of Kuan et al. 2020]**: confirmed this
  is the X-ray holographic nano-tomography *method* paper (same dataset as
  Kuan et al. 2020); its abstract is about neuronal reconstruction generally,
  no additional muscle-specific numbers beyond what is in the published
  Kuan et al. 2020 version above. **[READ abstract only, no incremental
  data]**
- No source for Chen et al. or "Lesser et al." leg micro-CT, or Azevedo 2020
  eLife Figures themselves (image content, as opposed to text), was examined
  for muscle volume/CSA in this pass — text-only extraction cannot read
  figure panels. **[NOT FOUND / not attempted — figures not OCR'd]**

## 3. Measured force or torque for the tibia extensor; Azevedo 2020 flexor force details

- **No force or torque measurement for the tibia extensor (tilm) was found
  in any source opened.** Azevedo et al. 2020 explicitly did not resolve it:
  **[READ, main text]** "The other muscles in the femur are the tibia
  extensor and the long tendon muscle. Both likely contribute to the calcium
  signals we record in Figure 1, but they are dominated by flexor activity
  and probably unresolvable without optical sectioning." (This sentence is
  in the published **author-response** sub-article, i.e. still eLife-published
  content but not the peer-reviewed main text — flagging per the rule
  above.) The main text itself (Discussion) states only that "Genetic
  markers have also recently been identified for tibia extensor motor
  neurons in flies (Venkatasubramanian et al., 2019), which will enable
  future investigation" — i.e. as of this 2020 paper, extensor
  characterization was future work, not yet done. **[NOT FOUND — no extensor
  force value exists in this source; Venkatasubramanian et al. 2019 itself
  not located/opened this pass]**
- **Tibia flexor force — full detail, all [READ, Azevedo et al. 2020 eLife,
  main text/Methods unless noted]:**
  - Force-probe calibration: **spring constant 0.22 μN/μm**.
  - Whole-leg maximum: "the fly was capable of producing close to 100 μN of
    force at the tip of the tibia and changes in force of ~1.3 mN/s."
  - Body-weight comparison (explicitly a derived estimate, not a direct
    force measurement): "the mass of the fly is ~1 mg for a weight of
    ~10 μN; this means that the femur-tibia joint can produce enough force
    to lift approximately ten times the fly's body weight."
  - Per-motor-neuron force, single spikes: "a single fast motor neuron spike
    produced ~10 μN of force, resulting in a 50 μm movement of the force
    probe… An intermediate neuron spike produced ~1 μN that moved the tibia
    5 μm." (Calibration note given alongside a figure panel: "50 µm = 11 µN,"
    i.e. ≈0.22 μN/μm, consistent with the stated spring constant.)
  - Tonic/background force: "Bath application of 1 μM MLA, an antagonist of
    nicotinic acetylcholine receptors, led to a decrease in the spontaneous
    firing rate and reduced the resting force on the probe by ~1.5 μN, or
    ~15% of the fly's weight."
  - Comparative figure from a different muscle system, cited not measured
    here: "For comparison, during take-off, the peak force production of
    the fly leg is ~100 μN (Zumstein et al., 2004)" — **SECONDARY** (that
    number is the TDT/jump-muscle peak force from Zumstein, Forman,
    Nongthomba, Sparrow & Elliott 2004 J Exp Biol 207:3515, not independently
    re-confirmed in this pass, see the project's existing
    `leg_muscle_anatomy_lit.md` which already quotes it directly as
    "101 ± 4.4 μN" from that paper).
  - Which motor neurons: fast = R81A07-Gal4 (innervates "the large tibia
    flexor muscle fibers in the middle of the femur," "the only motor neuron
    that innervates" them, "the only motor neuron that produces 10 μN of
    force in a single spike" per text); intermediate = R22A08-Gal4
    (proximal femur, "one of several likely candidates that controls
    Flexor 2 (Baek and Mann, 2009)"); slow = R35C09-Gal4 (distal femur, weak
    calcium signal). Sex and leg: **front (T1) leg only**, in "tethered
    flies" (sex not specified in the passages read).
  - **Explicit underestimate caveat [READ, main text Methods]**: "the fly
    pulled the probe closer to its leg. As a result, the displacement (and
    thus the force) measured by the probe in Figures 1, 5 may be slightly
    underestimated." — This is about lateral-vs-vertical probe-tracking
    error in the behavioral (not optogenetic single-spike) force
    measurements; the paper does not state the single-spike (~10 μN,
    ~1 μN) numbers themselves are underestimates, only the free-behavior
    force-probe displacement measurements.
  - 14 total leg muscles / 53 total motor neurons for the whole T1 leg
    **[READ, main text]**: "The leg… contains 14 muscles which are
    innervated by just 53 motor neurons (Baek and Mann, 2009; Brierley et
    al., 2012; Maniates-Selvin et al., 2020; Soler et al., 2004)."

## 4. Fibre cross-section dimensions for leg (not jump/flight) muscles

- **[READ, Kuan et al. 2020, PMC8354006]**: leg muscle fibre diameters
  **8–16 μm** (see §2 above) — the only non-jump/flight Drosophila leg muscle
  fibre cross-section figure found in this pass. Not broken out by
  individual muscle (tidm vs tilm vs ltm2 etc.) in the text read; applies to
  the dataset as a whole (femur + coxa muscle fibres imaged by XNH).
- For contrast (not leg muscle, carried over from the project's existing
  lit file, already [FULL TEXT]/READ there): Drosophila **jump muscle
  (TDT)** fibre dimensions are much larger — 133.0 ± 14.6 μm (length) ×
  71.2 ± 11.5 μm (width) × 40.7 ± 5.6 μm (height) (Jarvis, Bell, Loya, Swank
  & Walcott 2021, Arch Biochem Biophys 701:108809) — i.e. roughly 5–10×
  wider than the 8–16 μm leg-muscle fibre diameter reported by Kuan et al.
  2020. This cross-check suggests leg (tidm/tilm-type) fibres are
  substantially thinner than jump-muscle fibres, consistent with their much
  lower per-fibre/per-spike force (Azevedo's ~10 μN per fast-flexor spike vs
  ~100 μN whole-jump-muscle peak force).
- No pennation angle or fibre cross-sectional *area* (mm²/μm², as opposed to
  diameter) for any individual femur muscle was found. **[NOT FOUND]**

---

## Usable-numbers table

| Quantity | Value | n / leg / sex | Source | Tag |
|---|---|---|---|---|
| Femur total muscle fibre count (all femur muscles combined, XNH) | 97 fibres | 1 leg (T1 presumed; sex not stated) | Kuan et al. 2020 Nat Neurosci, PMC8354006 | READ |
| Femur total muscle fibre count (fluorescence microscopy, cited) | 33–40 fibres | — | Soler et al. 2004, via Kuan et al. 2020 | SECONDARY |
| ltm2 (femur long tendon muscle) fibre count, XNH | 6 fibres (2 proximal + 4 distal, 2 different MNs) | 1 leg | Kuan et al. 2020, PMC8354006 | READ |
| ltm2 fibre count (cited, previous report) | 3 fibres | — | Soler et al. 2004, via Kuan et al. 2020 | SECONDARY |
| Leg muscle fibre diameter (XNH, whole dataset) | 8–16 μm | 1 leg | Kuan et al. 2020, PMC8354006 | READ |
| Leg motor-neuron axon diameter (XNH) | 1–2 μm | 1 leg | Kuan et al. 2020, PMC8354006 | READ |
| tilm wild-type myoblast (precursor) count | 55.2 (mean) | n=5 third-instar leg discs; leg/sex not stated | Maqbool et al. 2006 PLoS ONE, PMC1762424 | READ |
| tilm myoblast count, Htl-RNAi knockdown | 34.2 (mean) | n=5 | Maqbool et al. 2006, PMC1762424 | READ |
| tilm myoblast count, Htl constitutively active | 118.5 (mean) | n=5 | Maqbool et al. 2006, PMC1762424 | READ |
| Tibia flexor motor-neuron pool size | ~15 MNs | T1 leg | Azevedo et al. 2020, PMC7347388 (main text) | READ |
| Flexor proximal ("muscle 40") MN count (intermediate) | 2–5 MNs | T1 | Azevedo et al. 2020, main text citing Baek & Mann 2009 / Brierley et al. 2012 | READ (count), SECONDARY (original source not opened) |
| Flexor distal ("muscle 41") MN count (slow) | 8–9 MNs | T1 | Azevedo et al. 2020, main text | READ (count), SECONDARY (orig. source) |
| Flexor fast MN count | 1 MN | T1 | Azevedo et al. 2020 | READ |
| Flexor MN count, conflicting primary reports | 6 (Baek & Mann 2009) vs 2 (Brierley & Williams 2012) | T1 | Azevedo et al. 2020 eLife author response (sa2) | READ (as quoted in the reply; original papers not opened) |
| tilm (distal) MN count identified | 1 MN (Fe1 of Lin B) | T1 | Enriquez et al. 2015, PMC4441546 | READ |
| Whole T1 leg: muscles / motor neurons | 14 muscles / 53 MNs | T1 | Azevedo et al. 2020, main text | READ |
| Force-probe spring constant | 0.22 μN/μm | T1, tethered fly | Azevedo et al. 2020, Methods | READ |
| Max tibia-tip force, behaving fly | ~100 μN (Δforce ~1.3 mN/s) | T1 | Azevedo et al. 2020 | READ |
| Fly body weight (derived, for context) | ~10 μN (mass ~1 mg) | — | Azevedo et al. 2020 | READ (stated as derived, not measured) |
| Fast flexor MN, force per spike | ~10 μN (50 μm probe deflection) | T1 | Azevedo et al. 2020 | READ |
| Intermediate flexor MN, force per spike | ~1 μN (5 μm deflection) | T1 | Azevedo et al. 2020 | READ |
| MLA block, resting-force drop | ~1.5 μN (~15% of body weight) | T1 | Azevedo et al. 2020 | READ |
| Jump-muscle peak force (comparison only, not tibia) | ~100 μN | — | Zumstein et al. 2004, cited in Azevedo et al. 2020 | SECONDARY |
| Jump-muscle specific tension (FlyMimic's upper bound) | 37 mN/mm² | — | Eldred et al. 2010 Biophys J, cited in FlyMimic | SECONDARY |
| IFM specific tension (FlyMimic's lower bound) | 9 mN/mm² | — | Swank 2012 Methods, cited in FlyMimic | SECONDARY |
| Base specific tension used for all front-leg MTUs (incl. tibia flexor & extensor) | 28 mN/mm², × free scale factor 0.3–3 per muscle | T1, front leg model | FlyMimic / Ozdil et al., arXiv:2509.06426 | READ |
| Tibia extensor force or torque | — | — | — | NOT FOUND (no source measures it; Azevedo 2020 explicitly flags it as unresolved/future work) |
| tidm vs tilm adult fibre count split | — | — | — | NOT FOUND (Soler et al. 2004 likely has it; paywalled, HTTP 403 / $30 paywall confirmed) |
| Front-leg tibia flexor/extensor PCSA, volume, fibre length, pennation (numeric) | — | — | FlyMimic CT reconstruction exists but values only in an unreadable figure (Fig. S5) / code repo | NOT FOUND (methodology confirmed, numbers not extractable from text) |
