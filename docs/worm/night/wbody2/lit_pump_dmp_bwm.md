# Lit check: pharyngeal pumping, defecation motor program, body-wall muscle APs

Date: 2026-11-08. Free sources only; paywalled items are marked "could not open" with no numbers guessed.

## 1. Pharyngeal pumping rate, N2 adult, off food vs on food

- **On food (well-fed adults):** "a pharyngeal pumping rate of more than 200 pumps per minute" (paraphrase in a review, citing earlier work incl. Avery & Horvitz 1990).
  Source: Trojanowski et al.-adjacent review, *Multiple excitatory and inhibitory neural signals converge to fine-tune C. elegans feeding to food availability*, PMC4714553. https://pmc.ncbi.nlm.nih.gov/articles/PMC4714553/
- **Early food deprivation (0-120 min off food):** "pumping rate remained low but increased during the first 120 min of food deprivation, to about one-quarter of the rate on food (i.e., 50 pumps per minute)". Same source, same URL. This is the review's own number, attributed to earlier Avery/Horvitz-era work; I could not pull the exact sentence from Avery & Horvitz 1990 itself (see below) to confirm this is literally their number vs. the review's rounding.
- **Hiebert, Chicas-Cruz & McCormick 2017**, microPublication Biology (confirmed metadata: PMID 32550358, PMCID PMC7255878, free, https://pmc.ncbi.nlm.nih.gov/articles/PMC7255878/): N2 control pumping rate **on food after a 2 h fast = 3.46 ± 0.19 Hz** (one of two trials/measures quoted; mean ± SEM). Exact quote pulled via fetch: "C. elegans [N2] control animals (A, [N2] = 3.46 ± 0.19 Hz". No off-food rate is reported in this paper (confirmed by direct fetch - it only measured the post-fast feeding burst).
- **Avery & Horvitz 1990, J Exp Zool 253:263-270** ("Effects of starvation and neuroactive drugs on feeding in C. elegans"): COULD NOT OPEN FREE FULL TEXT. Wiley paywall; abstract only via PubMed (https://pubmed.ncbi.nlm.nih.gov/2181052/). No numbers taken from it directly - the 50 pumps/min "off food" figure above is from the PMC4714553 review, not verified against Avery & Horvitz's own text.

## 2. Pumping rate after neuron ablation

- **Raizen, Lee & Avery 1995, Genetics 141:1365-82** ("Interacting genes required for pharyngeal excitation by motor neuron MC"). PMID 8601480, PMCID **PMC1206873** (confirmed via NCBI esummary), free in principle at https://pmc.ncbi.nlm.nih.gov/articles/PMC1206873/ - but PMC only holds a scanned PDF (`pdf/ge14141365.pdf`) gated behind a proof-of-work/JS interstitial ("Preparing to download...") that neither the fetch tool nor curl could get past (no bot-bypass attempted). The abstract (free, via Oxford Academic https://academic.oup.com/genetics/article/141/4/1365/6061972) states: "By laser ablating subsets of the pharyngeal nervous system, we found that the MC neuron type is necessary and probably sufficient for rapid pharyngeal pumping." **No pumps/min numbers could be extracted** - I did not guess any. A secondary review (PMC4714553) paraphrases but gives no numbers either, only "MC... acts as a pacemaker motor neuron to drive the high rate of pumping in the presence of food," and separately notes "laser ablation of RIP has surprisingly little effect on pharyngeal function."
- **Avery & Horvitz 1989, Neuron 3:473-485** ("Pharyngeal pumping continues after laser killing of the pharyngeal nervous system of C. elegans"). PMID 2642006, **no PMCID** - this is pre-PMC and Cell Press/ScienceDirect paywalled (https://www.sciencedirect.com/science/article/abs/pii/0896627389902067). COULD NOT OPEN. The title itself is the finding (pumping continues after killing the whole pharyngeal nervous system), quoted indirectly as a citation inside PMC1299054 (Embo Reports, "Slow Ca2+ dynamics in pharyngeal muscles..."): "Pharyngeal pumping continues after laser killing of the pharyngeal nervous system of C. elegans." No rate numbers available from a free source.

## 3. EAT-2 localization and MC synapse target

- **McKay et al. 2004, Genetics 166:161** ("eat-2 and eat-18 are required for nicotinic neurotransmission in the C. elegans pharynx"), PMCID **PMC1470703**, free: https://pmc.ncbi.nlm.nih.gov/articles/PMC1470703/
  Exact quote: "It is localized to the synapse between pharyngeal muscle and the main pharyngeal excitatory motor neuron MC." So McKay et al. describe EAT-2 as sitting at the MC-to-muscle synapse (not specifically "marginal cells" in this sentence).
- **Pharyngeal connectome paper** (Cook, Jarrell, or similar group), *The connectome of the Caenorhabditis elegans pharynx*, bioRxiv 868513, free: https://www.biorxiv.org/content/10.1101/868513v1.full
  Exact quote: "The outlier is the MC neuron, which has been electrophysiologically shown to function as a motorneuron, yet synapses solely onto marginal cells." This directly states MC's synapses (anatomically, EM-reconstructed) are onto marginal cells, not onto contractile muscle per se - marginal cells are the non-contractile support cells within the pharyngeal muscle syncytium. The paper notes it is giving "a more detailed view" than earlier (implicitly Albertson & Thomson 1976-era) classification, but does not quote Albertson & Thomson directly in the fetched text.
- **Albertson & Thomson 1976** ("The pharynx of Caenorhabditis elegans," Phil Trans R Soc Lond B): could not locate a free full text or a direct verbatim quote about MC's synapse target from the original 1976 paper itself in the time available. The connectome bioRxiv paper is the best free proxy with an explicit, directly-quoted statement (above).
- Net: McKay et al.'s phrase ("synapse between pharyngeal muscle and MC") and the connectome paper's phrase ("synapses solely onto marginal cells") are not necessarily contradictory - marginal cells are part of the muscle-cell complex, not separate neurons - but I have not reconciled the wording further.

## 4. MC's own activity and site of 5-HT action

- **Direct recording of MC is not possible**: PMC4791602 (*Pharyngeal pumping in C. elegans depends on tonic and phasic signaling from the nervous system*, Nature Sci Rep, free: https://pmc.ncbi.nlm.nih.gov/articles/PMC4791602/) states: "The MC neuron cell bodies are small (2-3 μm in diameter) and are embedded in the pharyngeal muscle...electrical recording from these neurons is not currently possible." MC activity is inferred only indirectly, via the "E1 spike" in electropharyngeogram (EPG) recordings of the muscle, described as: "Each pharyngeal muscle action potential is preceded by a small depolarization resembling an excitatory postsynaptic potential (EPSP) (the E1 spike)." This is consistent with one MC input event per pump, but is an inference from the muscle EPG, not a direct MC recording.
- **Song & Avery 2012, J Neurosci 32:1920** ("Serotonin activates overall feeding by activating two separate neural pathways in C. elegans"): jneurosci.org blocked the fetch (403/Cloudflare) and I could not reach a free full text in the time available (searched for a PMC mirror; did not confirm a PMCID). From search-engine snippets only (not independently verified by me by opening the source, so treat as unconfirmed): SER-7 in MC (and SER-1/other receptors in M4/M2) said to mediate 5-HT's effect on pumping vs. isthmus peristalsis respectively. **I did not verify this by opening the paper - flagging it as unconfirmed rather than citing it as read.**
- **Hobson et al. 2006, Genetics 172:159** ("SER-7, a C. elegans 5-HT7-like receptor, is essential for the 5-HT stimulation of pharyngeal pumping and egg laying"), PMCID **PMC1456143**, free, opened directly: https://pmc.ncbi.nlm.nih.gov/articles/PMC1456143/
  Exact quotes: "ser-7∷gfp is expressed in several pharyngeal neurons, including the MC, M2, M3, M4, and M5, and in vulval muscle." And: "The EPG data along with the observation that SER-7 is expressed in the MCs suggests that SER-7 mediates the increase in the overall rate of pharyngeal pumping by increasing the firing of the MC motorneurons." And on the EPG data itself: "EPGs from nearly all (>90%, 200 pumps examined from 10 worms) of the wild-type and ser-7(tm1325)(+) animals contained an E1 spike, whereas EPGs from <5% of the ser-7(tm1325) animals had an E1 spike." (E1 = inferred MC input event.)

## 5. Liu & Thomas 1994 - defecation cycle vs. temperature

Correct citation (verified against PubMed, the title in the question was not exact): **Liu DW & Thomas JH 1994, "Regulation of a periodic motor program in C. elegans," J Neurosci 14(4):1953-1962**, PMID 8158250, PMCID **PMC6577142**. This is the paper that established the ~45 s defecation cycle; "Temperature effects on behavior... the defecation cycle" is not its actual title.

- jneurosci.org full-text/PDF is Cloudflare-gated (confirmed 403 both via the fetch tool and via curl with a browser user-agent - got a "Just a moment..." challenge page, not the paper).
- PMC6577142 (https://pmc.ncbi.nlm.nih.gov/articles/PMC6577142/) renders only the abstract through the fetch tool; the PDF link (`pdf/jneuro_14_4_1953.pdf`) is behind the same NCBI proof-of-work "Preparing to download..." interstitial as PMC1206873 above, which I could not pass programmatically.
- Europe PMC's full-text XML endpoint returned HTTP 500 for this PMCID (no XML available for this 1994 article), checked directly with curl.
- **What I could confirm (abstract, free, read directly):** "A three-part motor program mediates a defecation every 45 sec in well-fed wild-type Caenorhabditis elegans. Individual worms maintain this 45 sec rhythm with an SD of about 3 sec."
- **I could NOT get the per-temperature breakdown (19-30 C) or any Q10 value from the primary source.** A search-engine summary (not independently opened/verified by me) claimed "defecation occurs every 45 seconds, with a standard deviation of less than 3 seconds at 20°C" and temperature-compensation from 19-30 C, but since I never opened the underlying text to see that exact sentence, I'm flagging it as unconfirmed rather than quoting it as read. No Q10 number found anywhere in the time available - none is reported here.

## 6. Kwan et al. 2008 - wild-type control defecation period

**Kwan CS, Vázquez-Manrique RP, Ly S, et al. 2008, "TRPM channels are required for rhythmicity in the ultradian defecation rhythm of C. elegans," BMC Physiology 8:11**, PMCID **PMC2409367**, free, opened directly: https://pmc.ncbi.nlm.nih.gov/articles/PMC2409367/

Exact quotes:
- "mean period (τ) of 45-50 seconds, in normal conditions at 20°C" (general statement of wild-type range).
- For the specific control group plotted in their Fig. 2A: "the mean and the mean C.V. for the control animals are 46.4 s and 5.5%, whereas those for gon-2(RNAi);gtl-1(RNAi) animals are 46.5 s and 21.1%."
- Methods, on n: "L4 worms were each scored for 15 consecutive cycles (unless otherwise noted) for each experiment. In most experiments more than 25 worms were scored." I could not find one single explicit "n=" tied directly to the 46.4 s/5.5% control number in the text I could fetch - reporting the general methods n (>25 worms, 15 cycles each) rather than inventing an exact figure for that specific panel.
- Temperature: 20 C (standard condition stated in Methods).

## 7. Gao & Zhen 2011, PNAS 108:2557 - body-wall muscle recording

**Gao S & Zhen M 2011, "Action potentials drive body wall muscle contractions in Caenorhabditis elegans," PNAS 108:2557-2562**, PMCID **PMC3038695**, free, opened directly: https://pmc.ncbi.nlm.nih.gov/articles/PMC3038695/

Exact quotes obtained:
- Method is "whole-cell patch current-clamp recording."
- Pipette (intracellular) solution: "115 K-gluconate; 25 KCl; 0.1 CaCl2; 5 MgCl2; 1 BAPTA; 10 Hepes; 5 Na2ATP; 0.5 Na2GTP; 0.5 cAMP; 0.5 cGMP, pH 7.2."
- Extracellular/bath solution: "150 NaCl; 5 KCl; 5 CaCl2; 1 MgCl2; 10 glucose; 5 sucrose; 15 Hepes, pH 7.3."
- Resting potential: "The resting potential, -25.0 ± 1.0 mV (n = 27)."
- Spontaneous activity: "Spontaneous action potentials were also recorded in ~80% of preparations" with "an averaged spontaneous firing frequency of 0.73 ± 0.14 Hz."
- Dependence on motor neuron input: "unc-13(lf) mutants showed a severe reduction in the action potential frequency (0.04 ± 0.01 Hz)" - directly supports that spontaneous muscle APs largely depend on (cholinergic) motor neuron input, since unc-13 loss (which blocks synaptic vesicle release) nearly abolishes them.
- Also: "cholinergic motoneuron activity led to an increase of action potential frequency" - i.e. the preparation retained functional, synaptically-connected ventral cord motor neuron input (consistent with intact innervation), though I did not get an explicit sentence describing the dissection procedure itself (muscle exposure, glue, etc.) or an explicit recording temperature - the fetch tool could not locate those specific sentences in the main text (they may be in the SI Methods, which I did not access given time budget). I did NOT confirm whether "-25 mV" was measured specifically "at 0 pA injected current" - this detail was not found in the text retrieved.
- I could not confirm this same information from Liu, Chen & Wang (SLO-2 papers) in the time available - not opened.
- In vivo/intact locomotion AP rate: a 2024 biophysical-modeling paper (Y. Liu et al./Zhen lab collaborators?, "Biophysical modeling and experimental analysis of the dynamics of C. elegans body-wall muscle cells," PLOS Comp Biol, PMCID PMC11781704, free: https://pmc.ncbi.nlm.nih.gov/articles/PMC11781704/) states: "While the undulation frequency of C. elegans during locomotion barely exceeds 2 Hz for swimming animals and is even slower during crawling on agar plates, these observed undulation frequencies do not directly correspond to the firing rates of individual muscle action potentials," and reports in vitro "burst firing mode frequency of 4.8 ± 1.05 Hz" and a "regular" firing mode below 2 Hz (3 WT cells) - but this is in vitro (dissected prep under current injection), not a true in vivo AP rate during locomotion. I found no true in vivo (intact, behaving animal) muscle AP rate in the time available; none is reported here to avoid guessing.

## 8. Is the pharyngeal muscle myogenic?

- Avery & Horvitz 1989's title itself is the core finding: pumping continues after killing the whole pharyngeal nervous system (could not open full text - see Q2 - so I cannot quote their exact post-ablation rate).
- A free secondary source (PMC4791602, Nature Sci Rep, opened directly, https://pmc.ncbi.nlm.nih.gov/articles/PMC4791602/) states: "Laser ablation of all pharyngeal neurons does not completely abolish pharyngeal pumping" (explicitly citing Avery & Horvitz 1989), but gives **no rate number** in the sentence I could retrieve.
- A search-engine summary (not independently verified by me by reading the source paper, so flagged as unconfirmed) characterized the system as "basically myogenic, similar to pumping of the vertebrate heart, with the pharyngeal nervous system playing mainly modulatory roles," and separately noted that, unlike heart/leech/mollusc myogenic pacemakers, "the pharyngeal muscle requires an extrinsic factor" - specifically tonic ACh release - "to exhibit pumping" even in the myogenic rhythm. I did not open the primary source for this specific phrasing, so no number is reported here - this is a qualitative, not quantitative, answer, and the quantitative part (the actual reduced ablated rate, e.g. in pumps/min) was not obtained from any source I could open.

---

## Sources actually opened (free) vs. not opened (paywalled or blocked)

Opened directly and quoted from:
- PMC4714553, PMC7255878 (Hiebert 2017), PMC1470703 (McKay 2004), bioRxiv 868513 (pharynx connectome), PMC4791602, PMC1456143 (Hobson 2006), PMC2409367 (Kwan 2008), PMC3038695 (Gao & Zhen 2011), PMC11781704 (2024 biophysical model), academic.oup.com abstract page for Raizen et al. 1995, PMC6577142 abstract (Liu & Thomas 1994).

Could not open (paywalled or bot-gated), no numbers guessed from these:
- Avery & Horvitz 1990, J Exp Zool (Wiley paywall).
- Avery & Horvitz 1989, Neuron (ScienceDirect paywall, no PMC record).
- Raizen, Lee & Avery 1995, Genetics - full text (PMC PDF gated behind a proof-of-work JS interstitial I could not pass; only the free abstract was read).
- Liu & Thomas 1994, J Neurosci - full text (jneurosci.org Cloudflare-gated; PMC PDF same proof-of-work gate as above; Europe PMC XML endpoint returned HTTP 500 - no XML exists for this article).
- Song & Avery 2012, J Neurosci (jneurosci.org Cloudflare-gated; did not find/verify a PMC mirror in the time available).
- Albertson & Thomson 1976 (not located in a free full-text form).
