# NLP-40 release: where, when, and how it reaches AVL/DVB

Date 2026-11-08. Question: does the literature support tonic, mean-calcium-driven NLP-40 release, or once-per-cycle pulsatile release? Primary source, full text read: Wang et al 2013, Curr Biol 23(9):746-754, PMC3651789 (opened via pmc.ncbi.nlm.nih.gov HTML and NCBI efetch NXML, both stripped to plain text; quotes below are verbatim from that text). Secondary source, full text read: Mahoney et al 2008, PNAS 105(42):16350-16355, PMC2570992 (opened via pmc.ncbi.nlm.nih.gov HTML, full text). Also skimmed (abstract/partial only, see bottom): PMC9346499 (Sieburth lab synaptic-assembly paper) and bioRxiv 2022.04.09.487752 (TWK-40 preprint).

## 1. Where NLP-40 is released

"nlp-40 was exclusively expressed in intestinal cells" and "NLP-40 is secreted from the intestine" (Wang 2013, Fig 1/2 text). No mention of "int9" anywhere in the retrieved full text; no claim that release is restricted to posterior cells.

Imaging: a functional NLP-40::YFP fusion in the intestine "adopted a highly punctate pattern of fluorescence on the basolateral surface of the intestinal cells (Figure 2C and 2D)... YFP fluorescence was also detected in six coelomocytes (Figure 2C and 2E)." Fig 2D legend: "Representative image of NLP-40::YFP localization on the basolateral surface of the anterior intestine" — the one representative image shown happens to be anterior, but the transcriptional reporter (Fig 2A) shows expression broadly across intestinal nuclei, and the paper never quantifies a map of release along the gut. Label: **stated** (imaged puncta pattern; no quantitative anterior-vs-posterior comparison; "all cells release equally" was not tested either).

SNT-2 (the Ca2+ sensor on NLP-40 dense-core vesicles) is expressed "throughout the intestine, as well as in several neurons in the head and tail" (Fig 3C) and co-localizes with NLP-40::YFP puncta ("90.4% +/- 1.9% co-localization, n=13 worms", Fig 3D) — **measured**. Mahoney 2008: AEX-5::VENUS (proprotein convertase) "is secreted from the intestine and subsequently endocytosed by coelomocytes" (Fig 1E-F) — **measured** (imaged), again whole intestine, no named cell. aex-4 (intestinal SNARE) "expresses only in intestinal cells" (Fig 1B), localizing "along the plasma membrane of intestinal cells" (Fig 1C,D) — general epithelium, not posterior-specific. Neither paper names int9 or any single cell as the release site.

## 2. Timing of release: rhythmic/once per cycle, or tonic?

Neither paper directly films NLP-40 release during a live cycle (no pHluorin-style real-time secretion imaging) — the coelomocyte assay is a steady accumulation readout, not a per-cycle pulse readout. So there is no literal movie of "one release event per cycle." But the stated mechanism and the downstream DVB readout both point to one sharp, time-locked release per ~50s cycle, not a tonic/mean-level signal.

Model statement (Wang 2013, Fig 6E legend and Discussion, exact quotes): "Each defecation cycle is initiated with a calcium spike in the intestine. SNT-2/synaptotagmin on DCVs senses the increase in calcium and promotes the release of NLP-40 derived peptides from the intestine." And: "calcium oscillations in the intestine drive calcium-dependent rhythmic secretion of NLP-40, which is mediated by the calcium sensor SNT-2/synaptotagmin." Label: **stated** ("rhythmic secretion" tied to the Ca spike/peak, not to a time-average).

DMP timeline (Wang 2013 Fig 1A legend; Mahoney 2008 Fig 1A legend): pBoc, then aBoc "3 seconds later", then Exp "immediately" after aBoc. Cycle period: Wang 2013 "a period of about 50 seconds"; Mahoney 2008 "~45-sec periodicity". Intestinal Ca wave: Mahoney 2008 states it is posterior-to-anterior and "levels peak in the posterior and anterior intestinal cells just before the pBoc and aBoc contractions, respectively," citing refs 3-5 (Teramoto & Iwasaki 2006; Nehrke et al 2008; Peters et al 2007) — **stated**, citing earlier Ca-imaging papers, not re-measured here.

The downstream DVB Ca readout (item 3) shows exactly ONE spike per cycle, starting ~3s after pBoc and peaking right before Exp, then decaying — the strongest evidence for a single pulsatile release event timed to the Ca wave peak, not a tonic drive. A release rate set purely by mean/whole-intestine calcium would tend to smear this into a more graded or sustained signal rather than the measured 51/51 single sharp spikes. Label: **derived from measured DVB data**, not a direct measurement of secretion itself.

Latency, injected synthetic NLP-40 P3-1 to DVB Ca rise: "3.5+/-0.60 (mean+/- s.d.) seconds following injection (10 out of 10 injections, n=10 worms)" (Fig 6A-B) — **measured**. Note this is receptor-to-Ca latency in DVB, not intestine-release-to-receptor latency (injection bypasses the intestine).

## 3. AVL and DVB calcium transients

DVB (GCaMP3.0, Fig 4B-F): "we observed a single robust calcium spike in the synaptic region of the DVB neuron (and also often in the cell body) that began approximately three seconds following each pBoc step, peaked immediately before each Exp step, and returned to baseline about two to three seconds following Exp. Calcium spikes were not observed at any other time in the cycle (51 out of 51 cycles in 14 worms, Figure 4B, 4C)." — **measured**, n=14, 51/51 cycles, one spike/cycle.

nlp-40 mutants: "no calcium spikes in DVB neurons (0 out 46 cycles in 14 worms, Figure 4D), except for two calcium spikes that were associated with two passive Exp steps." — **measured**. Intestinal rescue (nlp-40 cDNA, intestine-only): "completely restored rhythmic calcium transients (35 out of 35 cycles in 12 worms, Figure 4E)." — **measured**. aex-2 mutants: "0 out of 47 cycles in 12 worms, Figure 4F" — **measured**.

AVL was NOT separately imaged with calcium in Wang 2013 — all the reported Ca traces and counts above are for DVB only; the text never gives a separate AVL spike count or trace. AVL appears only in anatomy/model statements (Fig 1A, Fig 6E). Label: **not found** (no AVL-specific Ca numbers in this paper). Mahoney 2008 did no calcium imaging of either neuron; it used behavioral (Exp/pBoc ratio) and optogenetic (ChR2) assays. aex-2 reporter expression in AVL and DVB was anatomical only: "mCherry expressed under the aex-2 promoter is detected in AVL... and DVB... GABAergic neurons" (Fig 1 J-L) — **stated/measured expression**, no Ca data.

## 4. AEX-2: expression, site of action, G protein

Wang 2013 model: "AEX-2/GPCR... is coupled to the activation of the Galphas adenylate cyclase (ACY) to produce cAMP" (Fig 6E) — **stated**, model only, no new biochemistry here.

Mahoney 2008: "aex-2 functions in the nervous system and activates a Gsalpha signaling pathway to regulate defecation" (Abstract). Expression is broad: nerve ring, ciliary sensory processes, head mesodermal cell, intestinal/enteric muscle, anal depressor, AND AVL/DVB (Fig 1 G-L) — but tissue-specific rescue shows it FUNCTIONS in neurons: "neuronal expression of AEX-2::GFP fully rescues the defecation defects of aex-2 mutants, muscular and intestinal aex-2 does not (Fig 2A)", and specifically the GABAergic promoter Punc-47 (not cholinergic Punc-17 or interneuron Pglr-1) rescues (Fig 2B) — **measured**. Gsalpha/cAMP genetic evidence: "Gain-of-function allele of Gsalpha [gsa-1(ce81)] completely suppresses the Exp defects in aex-2 mutants... an activated adenylyl cyclase gene [acy-1(js127)]... significantly suppresses the Exp defects of aex-2, aex-4, and aex-5 mutants" (Fig 4A) — **measured** (genetic suppression, not a direct cAMP assay).

## 5. Effect of synthetic/exogenous NLP-40 on DVB

Injected NLP-40 P3-1 into nlp-40 mutant pseudocoelom: "consistently induced a single calcium spike in DVB neurons 3.5+/-0.60 seconds following injection (10 out of 10 injections, n=10 worms)" (Fig 6A,B) — **measured**. nlp-40;aex-2 double mutants: "0 out of 8 injections, n=8 worms" (Fig 6D) — **measured**. Inactive peptide NLP-40 P1: "0 out of 7 injections, n=7 worms" (Fig 6C) — **measured**.

Concentration (Methods): "The injection solution was prepared as following: 10 [unit missing] M of synthetic peptide (NLP-40 P1 or P3-1), 0.5mg/ml of Dextran, rhodamine B..." The unit character before "M" is absent from both the PMC web-viewer HTML and the NCBI efetch NXML (checked raw bytes in both — the micro sign is genuinely missing from the source text I could access free, not a rendering artifact on my end). Almost certainly "10 uM" but **unconfirmed** — do not use this number without checking the publisher's own PDF/HTML, which I did not have free access to.

In vitro receptor potency (CHO/aequorin assay, not DVB): "NLP-40 P3-1 peptide (EC50=3.39 nM +/-1.17 nM)... NLP-40 P3-2 peptide (EC50=26.73 nM +/-1.18 nM)" (Fig 5B) — **measured**.

## 6. Dense-core vesicle release machinery in the intestine

SNT-2 (Wang 2013): expressed "throughout the intestine, as well as in several neurons in the head and tail" but not in AVL/DVB (Fig 3C, S3A/B) — **measured**. Intestine-specific snt-2 cDNA rescues Exp defects (Fig 3B) — **measured**, so SNT-2 acts in the intestine. snt-2 mutants: coelomocyte NLP-40::YFP uptake "reduced by approximately 50%... compared to wild type" (Fig 2E-G) — **measured** (partial, not full, loss of secretion).

AEX-5 (Mahoney 2008): proprotein convertase, "secreted from the intestine and subsequently endocytosed by coelomocytes" (Fig 1E-F) — **measured**. AEX-4 (intestinal SNARE/SNAP-25 homolog): "expresses only in intestinal cells" (Fig 1B); regulates AEX-5 secretion — "aex-4 mutants accumulate AEX-5::VENUS in intestinal cells and accumulate significantly less AEX-5::VENUS in coelomocytes (Fig 3, S5)... no defect... in WT or aex-2 mutants" — **measured**. AEX-1: "a distant homologue of the synaptic gene unc-13 (Munc13), which acts in the intestine to regulate the DMP" (citing Doi and Iwasaki) — **stated**, not re-measured in this paper.

Ca-triggered release, from which cells: both papers treat this as the working model, not a direct per-cell Ca-to-secretion measurement. Mahoney 2008 Introduction: "these studies suggest that the intestine may control the timing of the DMP via a Ca2+-dependent process, such as Ca2+-induced exocytosis" — **stated**, citing the Ca-wave imaging papers (refs 3-5). No cell-by-cell secretion-vs-calcium curve was measured in either paper. The intestinal Ca wave itself (not NLP-40 secretion) was measured as posterior-to-anterior by those earlier, separately-cited papers.

## Checked but found nothing new (abstract/skim only)

- PMC9346499 (Sieburth lab, gut-brain synaptic assembly, ~2021): about AIY presynaptic development via NLP-40/Wnt signaling, not DMP release site/timing. **Not found** relevant.
- bioRxiv 2022.04.09.487752 (TWK-40 K2P channel preprint): one paraphrased sentence, "the intestinal IP3 receptor/itr-1-driven pacemaker Ca2+ oscillations trigger a Ca2+-dependent secretion of neuropeptide NLP-40" — **stated**, no new numbers; focus is TWK-40 in DVB, not intestinal release.
- No paper found with live imaging (e.g. pHluorin) of NLP-40 secretion itself during an ongoing DMP cycle, in the time spent. **Not found.**

## Bottom line

No paper reports NLP-40 release as a function of mean/whole-intestine calcium integrated over time. The published picture (Wang 2013) is a calcium SPIKE/wave in the intestine triggering SNT-2-dependent DCV exocytosis once per ~50s cycle, producing one sharp, few-second DVB calcium spike timed to pBoc/Exp (51/51 cycles, n=14), abolished in nlp-40 and aex-2 mutants. A release rate set by a Hill function of mean calcium across all intestinal cells would smear this into a continuous/tonic signal and would not reproduce the single-spike-per-cycle result — that is a different mechanism from what is reported, consistent with the other worker's concern.
