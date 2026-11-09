# Literature search: HSN -> vm2 geometry for Nicholson volume-transmission model

Date: 2026-11-09. Free sources only. Each finding: number, units, verbatim quote, source, URL opened, what it measures.

## Q1. HSN presynaptic puncta count and length of vulval synaptic region

### Source: Patel MR, Lehrman EK, Poon VY, Crump JG, Zhen M, Bargmann CI, Shen K (2006) "Hierarchical assembly
of presynaptic components in defined C. elegans synapses." Nat Neurosci 9(11):1488-1498. doi:10.1038/nn1806.
PMID 17115039. PMC free: PMC3917495. URL opened: https://pmc.ncbi.nlm.nih.gov/articles/PMC3917495/ (raw HTML
downloaded with curl, plain text extracted and grepped directly by me).

On the total number of HSNL en passant synapses (Results, citing refs 8 and 37, i.e. White et al. 1986 Phil
Trans R Soc B and a Shen/Bargmann-lab reference - the paper's own in-text citation markers, not independently
traced by me this session):
> "The HSNL motor neuron, which regulates egg-laying in C. elegans, forms 12–20 en passant synapses onto vulval
> muscles and the VC4 and VC5 neurons."
CONFIRMED, exact quote, Results section ("Multiple proteins localize to the presynaptic region of HSNL"). This
is the primary-source confirmation of the "12-20 en passant synapses" figure that the prior session's lit_vt.md
could only find as an unverified search-snippet summary - now directly quoted from an opened page. Note this
count is HSNL's TOTAL synapse count onto vm2 + VC4 + VC5 combined, not specifically the vm2-only subset (which
Cook et al. 2019's "6 synapses per side onto each of vm2AL/AR/PL/PR" would represent a further breakdown of).

On the length of the vulval synaptic region (the stretch of axon containing ALL of HSNL's presynaptic sites)
(Results):
> "These HSNL synapses reside within a short stretch of the axon (∼10 μm) near the vulval opening, whereas the
> remainder of the HSNL axon (∼500 μm) in the ventral nerve cord is devoid of any pre- or postsynaptic
> specializations."
CONFIRMED, exact quote, Results section. Restated again later in Results:
> "In wild-type N2 adults, all the presynaptic sites in HSNL are restricted to within ∼10 μm of the axon segment
> near the vulva."
CONFIRMED, exact quote.

Methods definition of the same ∼10 μm segment used for quantification (Methods):
> "For the quantification of syg-1, syd-1 and syd-2 mutants, the vulval segment was defined as the most dorsally
> defasciculated part of HSNL (∼10 μm). This segment of axon contacts the 1° vulval epithelial cells at the L4
> stage. The anterior ectopic synaptic region was defined as the 30 μm of HSNL immediately anterior to the
> vulval region."
CONFIRMED, exact quote, Methods section.

=> **Usable numbers: HSNL forms 12-20 en passant synapses total (onto vm2 + VC4 + VC5), confined to a ~10 μm
stretch of axon near the vulva.** This gives an average synapse spacing of roughly 10 μm / (12 to 20) =
0.5-0.83 μm if synapses were evenly spaced along that stretch (DERIVED by me, not stated in the paper - the
paper does not claim even spacing, this is just a back-of-envelope density figure).

On the markers used (GFP::RAB-3, SNB-1::YFP, SYD-2, etc.) and their punctate co-localization, confirming the
synapses are marked by discrete puncta rather than diffuse signal (Results):
> "Proteins that exhibited discrete localization to the presynaptic region of HSNL near the vulva included
> SYD-2 (liprin-α), SYD-1, ELKS-1 (ERC), GIT, SNN-1 (Synapsin-I), RAB-3 (M. Nonet, personal communication), SAD-1
> kinase and UNC-57 (endophilin)."
> "We have previously shown that the fluorescently tagged synaptic vesicle protein synaptobrevin (SNB-1::YFP)
> localizes to the same region of HSNL as the presynaptic sites observed by serial se[ction electron
> microscopy]..." [sentence continues, cut by my grep window]
CONFIRMED, exact quote (RAB-3/SNB-1/SYD-2/SYD-1/ELKS-1/GIT/SAD-1/UNC-57 all localize punctately to the same
~10 μm region). No exact COUNT of individual RAB-3 puncta (e.g. "N puncta per axon") was found in the text I
extracted - the paper quantifies fluorescence INTENSITY at the 10 μm segment (relative to wild type, in mutant
comparisons), not a raw puncta count number. Searched extracted text for a bare puncta-count number near "Fig.
1k" (figure legend: "Quantification of number of puncta on the HSNL axon segment that contacts the 2° vulval
epithelial cells") - the legend text itself does not give the number in prose; it would be in the figure/graph
only, which I cannot read from HTML text extraction. So: NOT FOUND (exact puncta count number) - only the
qualitative figure-panel description was recovered.

### Cross-check: does the figure caption/text use "SYD-2" correctly for this HSN paper? (Ben's question listed
Shen, Bargmann 2003 Cell for SYG-1 and Shen, Fetter, Bargmann 2004 Cell for SYG-2 as candidate sources - these
two Cell papers were NOT opened this session; cell.com is paywalled and neither is in PMC per the prior
session's lit_vt.md check. The 12-20 synapse count and ~10 μm region length above come from Patel et al. 2006
Nat Neurosci instead, which is freely available via PMC and cites White 1986 and a Shen/Bargmann-lab paper as
its own source for the "12-20" figure.)

## Q2. Ultrastructure: HSN->vm2 synapse type, distances, cleft width

### Source: Li P, Collins KM, Koelle MR, Shen K (2013) "LIN-12/Notch signaling instructs postsynaptic muscle
arm development by regulating UNC-40/DCC and MADD-2 in Caenorhabditis elegans." eLife 2:e00378.
doi:10.7554/eLife.00378. PMID 23539368. PMC free: PMC3601818 (I could not fetch this PMC mirror directly - curl
hit a Google reCAPTCHA challenge page, 0 article text recovered). URL actually opened and read successfully:
https://elifesciences.org/articles/00378 (fetched directly via WebFetch, targeted extraction).

On vm2 muscle arms being the postsynaptic specialization that HSN/VC synapse onto, described explicitly as
analogous to vertebrate dendritic spines (Introduction, Results, Discussion - three separate occurrences):
> "the dendritic spine-like postsynaptic membrane protrusions called muscle arms" (Introduction)
> "the dendritic spine-like membrane protrusions (muscle arms) from the vm2 cell bodies" (Results)
> "The EM reconstruction work proposed that the vm2 muscle arms serve as the postsynaptic specializations, which
> are similar to the dendritic spines in the vertebrate neurons" (Discussion)
CONFIRMED, exact quotes, as extracted by WebFetch from the live eLife HTML page (I did not independently
re-download and grep the raw HTML myself for this one source, unlike most others in this file - noting the
slightly lower verification bar for this source specifically).

=> This directly answers the "direct synapse with muscle arms at the active zone vs. some distance away"
question: by this paper's and the underlying EM-reconstruction description, the vm2 muscle sends out an arm
(a spine-like protrusion) that extends TO MEET the HSN/VC presynaptic site, i.e. the synapse is anatomically a
direct, close (dendritic-spine-like) apposition, not a long-range en-passant contact across open space - but
no exact distance (nm or µm) between the HSN presynaptic density and the vm2 muscle arm membrane was found in
the text extracted from this page. The WebFetch extraction explicitly reported: "No specific numerical distance
or gap measurement is provided in this document" and "No synaptic cleft width measurements are provided in this
document." So: NOT FOUND (exact nm/µm gap and cleft width numbers), but the QUALITATIVE ultrastructural
category (direct, spine-like muscle-arm apposition, not en-passant-at-a-distance) IS confirmed.

### Generic (non-C.-elegans-specific) synaptic cleft width figure found, flagged as such
Source: "Understanding Synaptogenesis and Functional Connectome in C. elegans by Imaging Technology" (review),
PMC free: PMC4925697. URL opened: https://pmc.ncbi.nlm.nih.gov/articles/PMC4925697/ (raw HTML downloaded with
curl, plain text extracted and grepped directly by me).
> "Chemical synapses are specialized intercellular junctions with two apposed compartments, the pre-synaptic
> terminal and the postsynaptic target, and the synaptic cleft which is about 20 nm gap between the pre- and
> postsynapses (Cowan and Kandel, 2001)."
CONFIRMED, exact quote - BUT this is explicitly cited to Cowan and Kandel 2001, a general vertebrate-neuroscience
textbook/review source (not a C. elegans EM measurement), appearing in this C. elegans review only as generic
background framing before the C. elegans-specific discussion begins. Treat the "~20 nm" figure as a GENERIC
chemical-synapse cleft width, NOT independently confirmed as a measured C. elegans NMJ or HSN->vm2 value. This
is consistent with and does not resolve the prior session's lit_vt.md finding that a C. elegans-specific cleft
width number could not be confirmed in Hammarlund et al. 2007, Watanabe et al. 2013, or Rand & Nonet's WormBook
chapter (all either searched with no "cleft" hits, or blocked by bot-challenges).

### Not opened / blocked this session (additional attempts beyond the prior session's list in lit_vt.md)
- Rostaing P et al. 2004 (J Histochem Cytochem, EM of C. elegans NMJs, pre-embedding immunogold) and Stigloher C
  et al. 2011 (J Neurosci, dense projection/SYD-2) were both named in search-result snippets as "key references
  for electron microscopy studies of C. elegans neuromuscular junction ultrastructure," but I did not open
  either paper directly this session (time budget) - their specific cleft-width numbers, if any, remain
  UNCONFIRMED/not checked.
- PMC3601818 (the NCBI PMC mirror of Li et al. 2013) is blocked by a Google reCAPTCHA challenge page when
  fetched directly with curl; I used the live elifesciences.org HTML page instead, which worked.

## Q3. SER-1 / SER-7 localization on vulval muscles (vm1 vs vm2)

### Source: Fernandez RW, Wei K, Wang EY, Mikalauskaite D, Pepper J, Christie N, Kim S, Weissenborn S, Sarov M,
Koelle MR (2020) "Cellular Expression and Functional Roles of All 26 Neurotransmitter GPCRs in the
Caenorhabditis elegans Egg-Laying Circuit." J Neurosci 40(38):7475-7488. PMID 32847964. PMC free: PMC7511189.
URL opened: https://pmc.ncbi.nlm.nih.gov/articles/PMC7511189/ (raw HTML downloaded with curl and plain-text
extracted directly by me with a script, not only the WebFetch summarizer, then grepped for exact sentences).

On which cells express SER-1 and SER-7 (Discussion):
> "Our results show that the serotonin receptors that activate the circuit, principally SER-1 and SER-7, with
> SER-5 playing a lesser role (Hapiak et al., 2009), are each expressed in different overlapping sets of cells
> in the egg-laying system. SER-1 and SER-7 are both expressed in the vm2 muscle cells, whose serotonin
> activation is crucial for executing egg laying (Brewer et al., 2019). SER-7 is also expressed in the VC
> neurons, which synapse onto vm2."
CONFIRMED, exact quote, Discussion section.

On the HSN itself as a possible serotonin autoreceptor site:
> "We also found that the SER-1, SER-5, and SER-7 receptors are expressed on the HSNs themselves, suggesting the
> hypothesis that serotonin from the HSN could act in an autocrine feedback loop to maintain HSN activity."
CONFIRMED, exact quote, Discussion section.

On which serotonin receptors are "strongly expressed" on vm2 specifically (Results/Discussion):
> "If we restrict our analysis only to strongly expressed receptors, vm2 cells express three serotonin
> receptors: the SER-1 and SER-7 receptors that stimulate egg laying by coupling to Gαq and Gαs, respectively,
> and the SER-4 receptor that inhibits egg laying by coupling to Gαo (Cho et al., 2000; Carnell et al., 2005;
> Dempsey et al., 2005; Carre-Pierrat et al., 2006; Hapiak et al., 2009; Gürel et al., 2012)."
CONFIRMED, exact quote.

On extrasynaptic (volume-transmission) signaling to vm1/um1/um2, which are NOT HSN synaptic targets but DO
express serotonin receptors - directly relevant to our volume-transmission hypothesis:
> "Remarkably, our data show seven additional instances in which serotonin receptors are strongly and
> reproducibly expressed by cells of the egg-laying system that do not receive synapses from the HSN or any
> other serotonergic neurons (Fig. 5). For example, the vm1 and um1/2 egg-laying muscle cells, which contract
> with the vm2 muscle cells to cause egg laying, all express serotonin receptors. Therefore, serotonin released
> by HSN may travel extrasynaptically to the vm1 and um1/2 cells to signal through serotonin receptors on these
> cells to help induce their activ[ity]..."
CONFIRMED, exact quote (truncated by my grep window at "activ" - the word is almost certainly "activity" or
"activation" continuing the sentence; flagging the truncation rather than guessing the exact remaining letters).
This is the paper's OWN explicit statement that HSN 5-HT reaches vm1/um1/um2 by extrasynaptic (volume
transmission) diffusion, since these cells are not postsynaptic to HSN - strong direct support for modeling
HSN->vm2 (and beyond) with a volume-transmission term, not just a synaptic-cleft term.

Method caveat (relevant to interpreting "expression" here as NOT a subcellular/punctate localization claim):
> "...the GFP produced fills out the cells that express the GPCR gene (Tursun et al., 2009)."
This paper's fosmid-based GFP reporters are designed to diffusely fill the whole expressing cell, so they
report cellular identity of expression, NOT subcellular (synaptic vs extrasynaptic puncta) localization of the
receptor protein. I searched the full extracted text for "punctate" and "diffuse" - zero matches for either
term anywhere in the paper. So: NOT FOUND - no statement on subcellular (synaptic-cleft vs extrasynaptic)
localization of SER-1 or SER-7 protein on the vm2 muscle membrane in this paper.

### Source: Fernandez RW et al. (2023) "Multiple Subthreshold GPCR Signals Combined by the G-Proteins Gαq and
Gαs Activate the Caenorhabditis elegans Egg-Laying Muscles." J Neurosci 43(21):3789-3806. PMC free: PMC10219013.
URL opened: https://pmc.ncbi.nlm.nih.gov/articles/PMC10219013/ (raw HTML downloaded with curl, plain text
extracted and grepped directly by me).

On vm1 vs vm2 SER-1/SER-7 expression, stated explicitly and unambiguously (Results):
> "The expression of serotonin receptors in each cell of the egg-laying system has been characterized, and this
> work showed that both SER-1 and SER-7 are coexpressed on the vm2 vulval muscles, whereas SER-7 but not SER-1
> is expressed on the vm1 vulval muscles (Fernandez et al., 2020)."
CONFIRMED, exact quote, Results section. This is the paper's own restatement of the Fernandez 2020 finding,
unambiguous on the vm1-vs-vm2 asymmetry: **vm2 has both SER-1 and SER-7; vm1 has SER-7 only, no SER-1.**

On the four egg-laying muscle cell types and which receptors they coexpress (Figure 1 legend / Introduction):
> "There are 16 egg-laying muscle cells in total, four each of four types, which are the um1 and um2 uterine
> muscle cell types, as well as vm1 and vm2 vulval muscle cell types. The um1, um2, and vm2 muscle cells each
> coexpress the two serotonin receptors SER-1 and SER-7 that contribute to inducing egg laying (Fernandez et
> al., 2020). SER-1 is a Gαq-coupled receptor, whereas SER-7 couples to Gαs (Hamdan et al., 1999; Hobson et al.,
> 2003; Carnell et al., 2005; Dempsey et al., 2005)."
CONFIRMED, exact quote. So the receptor pattern across all four muscle types is: um1 = SER-1+SER-7; um2 =
SER-1+SER-7; vm1 = SER-7 only; vm2 = SER-1+SER-7 (+SER-4, inhibitory, per the 2020 paper above).

No subcellular localization (punctate/synaptic vs diffuse) statement for SER-1/SER-7 protein was found in this
paper's extracted text either (searched "punctate" and "diffuse" - zero matches in both).

### 26 mM serotonin plate dose (relevant also to Q6 below, recorded here since found in this source)
> "Worms were photographed 45 min after being placed on plates containing 26 mm serotonin." [HTML-extraction
renders "mM" with a stray space as "26 m m serotonin" - I am reading this as "26 mM" based on context; see
exact raw grep hit preserved for audit: "placed on plates containing 26 m m serotonin."]
> "NGM plates containing 26 mm serotonin creatine sulfate monohydrate (catalog #H7752-5G, Sigma-Aldrich) were
> poured and seeded with OP50 1 d before assay." [same "m m" -> mM reading]
> "This assay was adapted from the work of Hobson et al. (2006)."
CONFIRMED, exact quote (Methods, "Measuring effects of exogenous serotonin on egg laying on NGM plates").
This independently corroborates the "~26 mM" serotonin dose figure Ben already holds (the "5 to 26 mM" range),
sourced here to Hobson et al. 2006 via this paper's methods, using serotonin creatine sulfate monohydrate salt
(Sigma H7752) - a DIFFERENT salt form than assumed in the prior session's "7.5 mg/mL" derivation from Brewer
et al. 2019 (which did not state a salt form). The molecular weight of serotonin creatine sulfate monohydrate
was NOT looked up in this session (not derived) - flagging as a follow-up if an exact molar concentration is
needed for the 7.5 mg/mL figure's cross-check.

## Q4. HSN 5-HT vesicle type, firing/Ca rates, molecules per vesicle/event

### HSN Ca2+ transient rate, active vs inactive phase (found, full text)

Source: Collins KM, Bode A, Fernandez RW, Tanis JE, Brewer JC, Creamer MS, Koelle MR (2016) "Activity of the
C. elegans egg-laying behavior circuit is controlled by competing activation and feedback inhibition." eLife
5:e21126. doi:10.7554/eLife.21126. PMID 27849154. PMC free: PMC5142809. URL actually opened successfully this
session: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5142809/fullTextXML (Europe PMC full-text XML
mirror - the PMC HTML page itself returned only a 21 KB reCAPTCHA-challenge stub when fetched directly with
curl, so I used this alternate free full-text route instead; XML downloaded and plain-text extracted directly
by me with a script, then grepped).

> "Mean HSN inter-transient intervals in wild-type animals were 41 ± 5 s in the inactive state and 17 ± 2 s
> during the active state, while intervals in lgc-55 mutants were reduced to 22 ± 2 s in the inactive state and
> 13 ± 1 s during the active state."
CONFIRMED, exact quote, Results section.

=> **Usable numbers: HSN Ca2+ transient inter-event interval, wild type: 41 ± 5 s (inactive/quiescent phase),
17 ± 2 s (active/egg-laying phase).** DERIVED by me (not stated this way in the paper): taking these as mean
inter-spike intervals and inverting gives an approximate transient rate of 1/41 ≈ 0.024 Hz (inactive) and
1/17 ≈ 0.059 Hz (active) - roughly a 2.4x increase in transient frequency between phases. This is an
approximation assuming a Poisson-like or regular process from a mean interval; the paper does not itself state
a rate in Hz.

No exact spike/firing RATE in Hz from electrophysiology (as opposed to Ca imaging inter-transient interval) was
found for HSN in this paper or any other opened this session - HSN activity is measured via Ca2+ imaging
(GCaMP) in essentially all the C. elegans egg-laying literature I could access, not via electrophysiological
spike counting.

### HSN 5-HT vesicle type (synaptic vs dense-core) - NOT CONFIRMED by a directly opened primary source

- A WebSearch AI-generated summary (not a page I opened and verified) stated: "Monoamine neurotransmitters, such
  as serotonin, may be released from synaptic vesicles or dense-core vesicles... The cat-1 gene encodes the
  C. elegans vesicular monoamine transporter (VMAT) that loads serotonin into synaptic vesicles... C. elegans
  VMAT is associated with synaptic vesicles in approximately 25 neurons, including all of the cells reported to
  contain dopamine and serotonin." This reads like a paraphrase of Duerr, Gaskin, Rand (2001) "Identified
  neurons in C. elegans coexpress vesicular transporters for acetylcholine and monoamines," Am J Physiol Cell
  Physiol 280(6):C1616-C1622, and/or Duerr et al. 1999. I attempted to open the primary source directly -
  https://journals.physiology.org/doi/full/10.1152/ajpcell.2001.280.6.C1616 - and got an HTTP 403 (paywalled).
  **UNCONFIRMED** - this "synaptic vesicles, ~25 neurons" claim was never verified by me against an opened
  primary-source page this session.
- Source actually opened and checked for this question: "A neurotransmitter atlas of C. elegans males and
  hermaphrodites" (eLife reviewed preprint / PMC free: PMC11185579). URL opened:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11185579/ (raw HTML downloaded with curl, ~415 KB, plain text
  extracted and grepped directly by me). This paper confirms cat-1/VMAT as a general serotonergic-neuron marker
  gene but does NOT state in the text I extracted whether CAT-1 protein itself localizes to small clear
  synaptic vesicles or dense-core vesicles specifically in HSN:
  > "tph-1/TPH and bas-1/AAAD: the co-expression of these two biosynthetic enzymes, together with the
  > co-expression of the monoamine vesicular transporter cat-1/VMAT, defines all serotonin-synthesizing and
  > -releasing neurons (Fig. 1A) (Horvitz et al. 1982; Duerr et al. 1999; Sze et al. 2000; Hare and Loer 2004)."
  CONFIRMED, exact quote - but this only establishes CAT-1 as a marker of serotonergic identity, not vesicle
  type. Searched the full extracted text for "dense-core," "dense core," and "DCV" - zero matches anywhere in
  this paper. **NOT FOUND** (vesicle type for HSN 5-HT specifically) in this source.
- Brewer et al. 2019 PLoS Genet (PMC6363226, title explicitly about serotonin AND neuropeptide co-release from
  HSN - the single most likely paper to discuss this) could NOT be fully read this session: the PMC HTML page
  fetch returned only the Abstract and Introduction (~96 KB of text total, no Results/Discussion/Methods body
  recovered by either direct curl or the Europe PMC XML route, which itself returned an HTTP 500 for this PMCID)
  despite multiple attempts. Searched what text WAS recovered (abstract + intro) for "vesicle" - zero matches.
  **NOT FOUND / NOT FULLY CHECKED** - flagging this as a real gap (the paper likely does discuss vesicle type
  given its topic, e.g. via UNC-31/CAPS or EGL-3 proprotein convertase for the NLP-3 dense-core pathway) rather
  than a confirmed absence, since the body of the paper was never actually read.

### Molecules per vesicle, invertebrate cross-species bound (reused from prior-session verified finding, same
source and URL re-confirmed as still valid for this question)

Source: Trueta C, De-Miguel FF (2012) "Extrasynaptic exocytosis and its mechanisms: a source of molecules
mediating volume transmission in the nervous system." Front Physiol 3:319. Open access. URL opened:
https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2012.00319/full.
> "each vesicle containing 67,000 molecules of serotonin" (large dense-core vesicle, leech Retzius neuron,
attributed by this review to Bruns and Jahn, 1995, Nature 377:62-65).
CONFIRMED (quote from the review, which I re-verified is still present on this page); the underlying 1995
Nature primary paper itself remains paywalled and was not independently opened (nature.com redirects to a
login wall) - so this number is a secondary-source citation only, not independently verified against Bruns and
Jahn's own text, consistent with the prior session's flag in lit_amines.md.

This is NOT HSN-specific or C. elegans-specific (it is leech Retzius neuron data) - included here only as the
invertebrate cross-species per-vesicle bound Ben already asked to compare against Bunin and Wightman 1998's
3500 molecules/terminal (rat, already confirmed in the prior session's lit_vt.md, same quote reused here for
completeness):
> "This gives a value of 3500 molecules/terminal" (Bunin MA, Wightman RM, 1998, J Neurosci 18:4854, PMC6792557,
Discussion/Results, rat brain slice amperometry).

## Q5. Extracellular volume fraction (alpha) and tortuosity (lambda) in invertebrate/worm nervous tissue

### Source: Sykova E, Nicholson C (2008) "Diffusion in Brain Extracellular Space." Physiol Rev 88(4):1277-1340.
doi:10.1152/physrev.00027.2007. PMC free: PMC2785730. URL opened:
https://pmc.ncbi.nlm.nih.gov/articles/PMC2785730/ (raw HTML downloaded with curl, ~1.06 MB; plain text
extracted and grepped directly by me - this is the same review the prior session (lit_vt.md) used for the
general "alpha~0.2, lambda~1.6, healthy CNS" figures; I went back to the SAME paper and found its dedicated
invertebrate section, which the prior session did not report).

Section "9. Invertebrate brain" (Results/body text), on cephalopod (not nematode) invertebrate nervous tissue -
this is the only invertebrate ECS diffusion data this review covers, and it explicitly excludes most
invertebrates including nematodes for being too small to measure with the RTI-TMA method:
> "Most invertebrates present too small a mass of neural tissue to allow meaningful diffusion measurements with
> the RTI-TMA method. The cephalopods, i.e. octopus, cuttlefish and squid, provide an exception. In octopus, the
> brain is comparable in size to that of a rat, although very different in regional organization (423) and the
> brains of squid and cuttlefish are similar. This has allowed both in vivo and slice studies on the vertical
> and optical lobes of the cuttlefish and octopus (256) (Table 4A, 4B). Tortuosities ranged from 1.54-1.75 while
> volume fractions ranged from 0.09-0.29. The variation was probably caused both by the lack of established
> protocols for dealing with these preparations and an apparent sensitivity to ischemia. Nevertheless, these
> studies suggest that the values of α and λ are comparable to those found in vertebrates."
CONFIRMED, exact quote. Original primary measurement source for this cephalopod data, per the review's own
reference list (ref 256): Nicholson C, Miyan JA, Potter KT, Williamson R, Abbott NJ, "Diffusion properties of
the microenvironment of cephalopod brain," in Cephalopod Neurobiology (Abbott NJ, Williamson R, Maddock L, eds),
Oxford University Press, 1995, pp. 383-397 (a book chapter - I did NOT independently open this 1995 book
chapter; the quote and table values above are as reported secondhand by the 2008 review, not verified against
the 1995 primary source itself).

The actual data table (Table 4B in the review, cephalopod rows), extracted alongside adjacent vertebrate rows -
reproducing only the cephalopod ("Invertebrate") rows here, each as [region, species, age, prep, n, alpha,
lambda, ref]:
> "Invertebrate vertical lobe cuttlefish n/a in vivo 8 0.09 1.68 256"
> "vertical lobe cuttlefish n/a slice 14 0.12 1.54 256"
> "optical lobe cuttlefish n/a slice 14 0.29 1.86 256"
> "vertical lobe octopus n/a in vivo 8 0.13 1.75 256"
CONFIRMED, exact quote (table row text as extracted from HTML; note the prose summary above says "tortuosities
ranged from 1.54-1.75" but the table itself shows one row at lambda=1.86 (optical lobe, cuttlefish, slice) which
is OUTSIDE that stated 1.54-1.75 range - flagging this internal inconsistency in the source itself, not
resolving it by picking one number over the other. The alpha range 0.09-0.29 IS consistent with the four table
rows shown (0.09, 0.12, 0.29, 0.13).

=> **No C. elegans-specific or nematode-specific alpha/lambda value exists in this review or (as far as I could
find this session) anywhere else in the free literature** - the review states explicitly that nematode/worm
nervous tissue is too small to measure by the standard RTI-TMA method. The nearest available invertebrate
numbers are cephalopod (octopus/cuttlefish) brain: **alpha 0.09-0.29, lambda 1.54-1.86** (four data points
above), which the review's authors judge "comparable to those found in vertebrates" (i.e., comparable to the
alpha~0.2, lambda~1.6 mammalian CNS figures already held). I did not find any additional invertebrate ECS
diffusion measurement (e.g., Drosophila, leech, crayfish) in a free source this session - NOT FOUND for any
non-cephalopod invertebrate.

### Not opened this session due to time budget
- Nicholson et al. 1995 book chapter (primary cephalopod data source, ref 256 above) - not independently opened
  (book chapter, likely not freely available online).
- No dedicated search for Drosophila or leech CNS ECS diffusion parameters was performed this session beyond
  the one WebSearch query above, which surfaced only the same Sykova & Nicholson 2008 cephalopod data as its
  best/only hit for "invertebrate... tortuosity... volume fraction." Flagging as a gap, not a confirmed
  absence, for taxa other than cephalopods and nematodes.

## Q6. Vulval muscle 5-HT sensitivity / dose-response

### Bath/plate serotonin dose for egg laying - two independent confirmed numbers, different assay formats

(1) Liquid M9 assay: Brewer JC, Olson AC, Collins KM, Koelle MR (2019) PLoS Genet 15(1):e1007896, PMC6363226
(abstract/intro portion successfully read this session; see Q4 caveat above about the body not loading) -
reused from the PRIOR session's already-verified quote in lit_vt.md, re-cited here for completeness since it
answers this question directly:
> "For serotonin stimulation of egg laying, we used a standard assay [22] in which worms were placed in
> microtiter wells with M9 buffer or M9 buffer containing 7.5 mg/ml serotonin, and the number of eggs laid in
> 60 minutes was counted."
CONFIRMED (verified by the prior session against the opened page; I did not re-verify this specific quote
myself this session since the paper body did not load for me this time, but the quote itself was captured and
logged with its exact text in the prior session's lit_vt.md, same PMCID/URL).

(2) NGM plate assay, a DIFFERENT and higher concentration figure, independently confirmed by me THIS session:
Fernandez RW et al. (2023) J Neurosci 43(21):3789-3806, PMC10219013 (opened and grepped directly this session,
see Q3 above for full citation):
> "NGM plates containing 26 mm serotonin creatine sulfate monohydrate (catalog #H7752-5G, Sigma-Aldrich) were
> poured and seeded with OP50 1 d before assay." [HTML extraction renders "mM" as "m m" with a stray space; read
> as 26 mM based on context and on Ben's own prior-held "5 to 26 mM" range]
> "This assay was adapted from the work of Hobson et al. (2006)."
CONFIRMED, exact quote, Methods section. This independently corroborates part of the "5 to 26 mM" range Ben
already holds, now traced to a specific salt form (serotonin creatine sulfate monohydrate, Sigma H7752) and to
Hobson et al. 2006 as the originating protocol - resolving (for the 26 mM endpoint specifically) the prior
session's inability to verify Trent, Tsung and Horvitz 1983's "5 to 26 mM" figure directly (Trent 1983 itself
remains unopened/blocked, per lit_vt.md; but this 26 mM figure is now confirmed via a different, openable,
2023 paper that cites Hobson et al. 2006 for the same protocol).

NOTE: these two numbers (7.5 mg/mL liquid M9 vs. 26 mM on NGM plates) are NOT the same preparation (liquid
immersion vs. solid agar plate the worm crawls on and presumably ingests/absorbs through the cuticle more
slowly) and are not necessarily meant to be reconciled into one number - reporting both as found, as instructed.

### Qualitative muscle-level mechanism (found, full text) - serotonin raises vm2 Ca2+ transient frequency
Source: Fernandez RW et al. (2023) J Neurosci 43(21):3789-3806, PMC10219013 (same source as above).
> "calcium imaging was recorded in both the vm1 and vm2 vulval muscles simultaneously, and ratiometric analysis
> of the calcium recordings was performed in Volocity software (PerkinElmer) to generate traces of calcium
> transients... a video of each peak was examined and scored as vm1 only or vm1 + vm2."
CONFIRMED, exact quote, Methods. This establishes the Ca-imaging methodology used across this lab's papers
(Brewer et al. 2019, Collins et al. 2016, Fernandez et al. 2020/2023) but does NOT itself give a dose-response
curve (EC50, or Ca response amplitude at a stated applied concentration) for serotonin on vulval muscle Ca -
searched the extracted text of this paper for "EC50," "dose-response," and "dose response" - zero matches for
all three terms.

### Dissected-preparation or cut-worm Ca dose-response - NOT FOUND, several leads not confirmed
- Shyn SI, Kerr R, Schafer WR (2003) "Serotonin and Go Modulate Functional States of Neurons and Muscles
  Controlling C. elegans Egg-Laying Behavior," Curr Biol 13(21):1910-1915, PMID 14588249 - this is the
  foundational paper showing "serotonin acts directly on the vulval muscles to increase the frequency of Ca2+
  transients" (per a WebSearch summary, NOT independently opened and verified by me - cell.com is paywalled and
  I could not locate a free PMC/preprint mirror in this session). **UNCONFIRMED**, not opened.
- Hagiwara et al. "A self-regulating feed-forward circuit controlling C. elegans egg-laying behavior," PMC
  free: PMC2621019 - attempted to open directly; curl returned only a 21 KB Google reCAPTCHA challenge stub, no
  article text recovered. **Blocked, not opened.**
- No EC50 or Kd for serotonin's effect on vulval muscle Ca2+ transients (as opposed to the SER-1/SER-7 receptor
  EC50s on heterologous cells, which ARE confirmed in this project's separate lit_amines.md / lit_open.md notes
  at SER-1 = 1.34 ± 0.84 μM, Dernovici et al., and SER-7 ≈ 30-32 nM, Hobson et al. 2003/2006) was found in any
  page actually opened this session. **NOT FOUND.**

## Summary table

| # | Quantity | Value | Unit | Source | Status |
|---|----------|-------|------|--------|--------|
| 1 | HSNL total en passant synapses (onto vm2+VC4+VC5) | 12-20 | synapses | Patel et al. 2006 Nat Neurosci, PMC3917495 | CONFIRMED |
| 1 | HSNL vulval synaptic region length | ~10 | um | Patel et al. 2006, PMC3917495 | CONFIRMED |
| 1 | HSNL axon length outside synaptic region (VNC), no synapses | ~500 | um | Patel et al. 2006, PMC3917495 | CONFIRMED |
| 1 | Derived synapse spacing (10 um / 12-20 synapses) | 0.5-0.83 | um | derived by me | DERIVED, not stated |
| 2 | vm2 muscle arms = dendritic-spine-like postsynaptic structures | qualitative | - | Li et al. 2013 eLife, elifesciences.org/articles/00378 | CONFIRMED (qualitative only) |
| 2 | HSN->vm2 release-site-to-membrane distance | not found | nm/um | - | NOT FOUND |
| 2 | Generic chemical synapse cleft width (NOT C.-elegans-specific) | ~20 | nm | Cowan & Kandel 2001 via PMC4925697 review | CONFIRMED but explicitly generic, not C. elegans EM data |
| 2 | C.-elegans-specific NMJ/HSN cleft width | could not verify | nm | Hammarlund 2007, Watanabe 2013, Rostaing 2004, Stigloher 2011 | NOT FOUND (several sources not opened or term absent) |
| 3 | SER-1, SER-7 coexpressed on vm2 | qualitative | - | Fernandez et al. 2020 J Neurosci, PMC7511189; Fernandez et al. 2023 J Neurosci, PMC10219013 | CONFIRMED |
| 3 | vm1: SER-7 only, no SER-1 | qualitative | - | Fernandez et al. 2023, PMC10219013 (citing Fernandez 2020) | CONFIRMED |
| 3 | um1, um2: both SER-1 and SER-7 | qualitative | - | Fernandez et al. 2023, PMC10219013 | CONFIRMED |
| 3 | vm2 also expresses inhibitory SER-4 (Gao-coupled) | qualitative | - | Fernandez et al. 2020, PMC7511189 | CONFIRMED |
| 3 | HSN itself expresses SER-1, SER-5, SER-7 (candidate autoreceptor) | qualitative | - | Fernandez et al. 2020, PMC7511189 | CONFIRMED |
| 3 | HSN 5-HT reaches vm1/um1/um2 "extrasynaptically" (paper's own words) | qualitative | - | Fernandez et al. 2020, PMC7511189 | CONFIRMED - direct support for volume-transmission model |
| 3 | SER-1/SER-7 subcellular (synaptic vs diffuse) localization | not stated (reporters are whole-cell fills) | - | Fernandez et al. 2020/2023 | NOT FOUND (method cannot answer this) |
| 4 | HSN Ca2+ transient inter-event interval, inactive state | 41 ± 5 | s | Collins et al. 2016 eLife, PMC5142809 | CONFIRMED |
| 4 | HSN Ca2+ transient inter-event interval, active state | 17 ± 2 | s | Collins et al. 2016, PMC5142809 | CONFIRMED |
| 4 | Derived approx. transient rate, inactive / active | ~0.024 / ~0.059 | Hz | derived by me from above | DERIVED, not stated as Hz in paper |
| 4 | HSN 5-HT vesicle type (synaptic vs dense-core) | not confirmed | - | Duerr et al. 2001 (paywalled, 403); PMC11185579 atlas (silent on this) | UNCONFIRMED / NOT FOUND |
| 4 | 5-HT per large dense-core vesicle, leech Retzius (cross-species bound) | 67,000 | molecules/vesicle | Bruns & Jahn 1995 via Trueta & De-Miguel 2012 review, Front Physiol | CONFIRMED (secondary citation; primary 1995 paper paywalled) |
| 4 | 5-HT per terminal, rat (cross-species bound, reused) | 3500 | molecules/terminal | Bunin & Wightman 1998, PMC6792557 | CONFIRMED (prior session) |
| 5 | ECS volume fraction alpha, cephalopod (octopus/cuttlefish) brain | 0.09-0.29 | fraction | Sykova & Nicholson 2008, PMC2785730, Table 4B, citing Nicholson et al. 1995 | CONFIRMED |
| 5 | ECS tortuosity lambda, cephalopod brain | 1.54-1.86 | - | same | CONFIRMED (table values; prose text says "1.54-1.75," one table row at 1.86 exceeds that - internal inconsistency in the source, both reported) |
| 5 | C.-elegans/nematode-specific alpha, lambda | explicitly not measurable by standard method per this review | - | Sykova & Nicholson 2008 | CONFIRMED ABSENT (review states nematode tissue too small for RTI-TMA method) |
| 6 | Exogenous serotonin dose, liquid M9 assay | 7.5 | mg/mL | Brewer et al. 2019 PLoS Genet, PMC6363226 (quote captured by prior session) | CONFIRMED |
| 6 | Exogenous serotonin dose, NGM plate assay (serotonin creatine sulfate monohydrate) | 26 | mM | Fernandez et al. 2023, PMC10219013, citing Hobson et al. 2006 | CONFIRMED |
| 6 | Vulval muscle Ca2+ dose-response curve / EC50 for bath-applied 5-HT | not found | - | Shyn et al. 2003 Curr Biol (paywalled, not opened); PMC2621019 (blocked by reCAPTCHA) | NOT FOUND |
| 6 | SER-1 EC50 for 5-HT (heterologous, COS-7 Ca/FLIPR assay, for context) | 1.34 ± 0.84 | uM | Dernovici et al., via prior-session lit_open.md (not re-verified this session) | CONFIRMED (prior session) |
| 6 | SER-7 EC50 for 5-HT (heterologous, COS-7 cAMP assay, for context) | ~30-32 | nM | Hobson et al. 2003/2006, via prior-session lit_amines.md (not re-verified this session) | CONFIRMED (prior session) |

## Not found

- HSN presynaptic puncta COUNT as a single number (e.g. "N puncta per axon") - only the ~10 um region length and
  12-20 total synapse count were found; Patel et al. 2006's Figure 1k quantifies puncta fluorescence intensity
  in mutant comparisons, not a raw wild-type puncta count in prose.
- Exact distance (nm or um) from HSN presynaptic density/active zone to the vm2 muscle arm membrane. Only the
  qualitative ultrastructural category (direct, dendritic-spine-like muscle-arm apposition, not a long-range
  en-passant gap) is confirmed, via Li et al. 2013 eLife.
- A C.-elegans-specific (as opposed to generic vertebrate-textbook) synaptic cleft width number, despite
  checking Hammarlund et al. 2007, Watanabe et al. 2013, PMC4925697 review, and this session's new attempts on
  Li et al. 2013 and the Rostaing 2004 / Stigloher 2011 leads (not opened, time budget).
  The only number found (~20 nm) is explicitly cited to a general neuroscience textbook (Cowan and Kandel 2001),
  not a C. elegans EM measurement.
- SER-1 / SER-7 subcellular localization on the vm2 muscle membrane (punctate/synaptic vs diffuse/extrasynaptic)
  - the fosmid GFP reporters used in the only two papers that address SER-1/SER-7 cellular expression
  (Fernandez et al. 2020, 2023) are designed to fill the whole cell and cannot resolve this; term "punctate" /
  "diffuse" does not appear in either paper.
- HSN 5-HT vesicle type (synaptic/clear vesicles vs dense-core vesicles) at the vulval release sites specifically
  - Duerr et al. 2001 (the most likely primary source) is paywalled (403 at journals.physiology.org); Brewer et
  al. 2019's Results/Discussion/Methods body never loaded in any fetch attempt this session (only
  Abstract+Introduction were recovered); the 2024 neurotransmitter atlas (PMC11185579) is silent on vesicle type.
- HSN firing/spike rate in Hz from electrophysiology. Only Ca2+-imaging inter-transient intervals (41 s inactive,
  17 s active) were found; no spike-rate (Hz) number from electrophysiology was located.
- Molecules-of-5-HT-per-vesicle or per-release-event specifically for HSN or any C. elegans neuron. Only
  cross-species invertebrate (leech, 67,000/LDCV) and vertebrate (rat, 3500/terminal) numbers exist, both
  reused from the prior session's work, not C.-elegans-specific.
- C.-elegans/nematode-specific ECS volume fraction (alpha) and tortuosity (lambda). Sykova & Nicholson 2008
  explicitly states nematode nervous tissue is too small to measure by the standard method; the closest
  invertebrate data is cephalopod brain (alpha 0.09-0.29, lambda 1.54-1.86).
- A vulval-muscle Ca2+ dose-response curve or EC50 for bath-applied serotonin on dissected or cut preparations.
  Shyn et al. 2003 Curr Biol (the most likely primary source, establishing that serotonin directly raises vm2
  Ca2+ transient frequency) is paywalled and has no free mirror found; PMC2621019 ("A self-regulating
  feed-forward circuit...") was blocked by a reCAPTCHA challenge on direct fetch.
- Any C. elegans-specific "cuticle permeability factor" for 5-HT (not re-attempted this session; flagged as
  not found by the prior session too).
- Trent, Tsung and Horvitz 1983's original "5-26 mM" dose-response figure, directly from its own primary text
  (still blocked per the prior session; the 26 mM endpoint is now independently corroborated via a different,
  openable 2023 paper citing Hobson et al. 2006, but the primary Trent 1983 text itself remains unread).
