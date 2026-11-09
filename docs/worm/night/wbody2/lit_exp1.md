# Literature search: EXP-1, enteric muscles, DVB/AVL, expulsion timing

Started 2026-11-09. In progress, written as I go.

## Summary table

| quantity | value | label | source | full text opened |
|---|---|---|---|---|
| (filling in below) | | | | |

## A. Beg & Jorgensen 2003, EXP-1 is an excitatory GABA-gated cation channel

Source: Beg AA, Jorgensen EM. "EXP-1 is an excitatory GABA-gated cation channel." Nat Neurosci 6:1145-1152 (2003). doi:10.1038/nn1136.
Full text opened: YES. Found via Semantic Scholar API (closed openAccessPdf) then via the Jorgensen lab's own website (redirects to thejorgensenlab.org/publications), which links the lab-hosted PDF at
`https://jorgensen.biology.utah.edu/%20%20MANUSCRIPTS%20pdfs/2003%20Beg%20EXP-1%20%C6%92/2003%20Beg%20EXP-1.pdf`. Downloaded with curl, converted with pdftotext -layout. 8 pages, full article including Methods. This paper is NOT in PMC (pubmed_pmc elink for PMID 14555952 returns no pmc link, only pubmed_pmc_refs = papers that cite it).

All recordings below are from Xenopus laevis oocytes expressing exp-1 cRNA, two-electrode voltage clamp, holding potential -60 mV unless stated otherwise, "Ringer's solution" (composition not given numerically in the text I extracted; standard oocyte Ringer's, 115 mM NaCl as stated in the NaCl-dilution experiment).

**GABA EC50 and Hill coefficient.**
Quote: "For EXP-1 receptors, EC50 = 26.4 ± 1.08 µM and H = 1.8 ± 0.24 (n = 19)." (Figure 5 legend, panel a)
Also in main text: "The EC50 (effective concentration for half-maximum response) for GABA activation of EXP-1 receptors was 26.4 ± 1.08 µM (n = 19), which is lower than that determined for the UNC-49B homomeric GABA receptor (43.7 ± 2.9 µM) when expressed in X. laevis oocytes."
Label: measured. Conditions: oocyte, -60 mV, GABA 1-1000 µM bath-applied for 5 s.

**Reversal potential, ion selectivity.**
Quote: "The GABA-dependent current from oocytes expressing EXP-1 reverses at -5.54 ± 2.20 mV (n = 24) in Ringer's solution." Measured, standard Ringer's, GABA-evoked (30 µM, 5 s) responses at various holding potentials (I-V curve).
Quote (Cl- test): "In chloride-free Ringer's solution, the reversal potential for EXP-1 currents was -5.05 ± 1.08 mV (n = 9)... This value was not significantly different (P = 0.88, paired t-test) from that determined in normal Ringer's and indicates that chloride ions make no significant contribution to the current passing through the EXP-1 channel." Chloride replaced with gluconate. Measured.
Quote (Na+ test): "When external Na+ was completely replaced by NMDG, the EXP-1 reversal potential shifted to -84.34 ± 1.0 mV (n = 8), near the predicted potassium equilibrium potential (EK) in X. laevis oocytes... Replacement of sodium in the external bath with NMDG abolished the GABA-induced inward current, suggesting that EXP-1 is not permeable to large cations (NMDG) and anions (Cl-), but is permeable to the small cation Na+." Measured.
Quote (K+ test): "When external NaCl was replaced by 115 mM KCl, the reversal potential of EXP-1 expressing cells was -4.12 ± 1.28 mV (n = 13), demonstrating that K+ ions are also permeant through EXP-1 channels. Using the averaged ΔErev values measured in KCl Ringer's compared to NaCl Ringer's, a permeability (P) ratio of PK/PNa = 1.1 ± 0.08 (n = 13) was determined using a modified Goldman-Hodgkin-Katz equation." Measured permeability ratio: PK/PNa = 1.1 ± 0.08.
Quote (NaCl dilution): "Reversal potentials obtained from the dilution experiments (50%: -19.4 ± 3.19 mV, n = 13; 25%: -42.98 ± 6.52 mV, n = 10)... As extracellular NaCl decreased, negative reversal potential shifts were observed, as predicted by the Goldman-Hodgkin-Katz equation for a nonselective cation channel (50%: Erev = -20.24 mV; 25%: Erev = -37.51 mV)." Measured values vs. derived (GHK-predicted) values given side by side.
Quote (divalent/Ba2+ test): "we increased extracellular barium ten-fold (18 mM Ba2+) in the absence of Na+... GABA-induced responses did not show a significant shift in reversal potential from control conditions (ΔErev = -0.11 mV, n = 10, P ≥ 0.05, two-way ANOVA), suggesting EXP-1 has negligible divalent cation permeability." Measured; no PCa/PNa ratio given (not found - divalent permeability not quantified beyond "negligible").
Ca2+ permeability ratio specifically: not found (no PCa value reported; only the qualitative Ba2+ null result above).
Cl- permeability ratio: not found as a number (only the qualitative "no significant contribution" result and matched reversal potentials above). No PCl/PNa is computed in the text.

**Single-channel conductance.** Not found. This paper reports only whole-cell (macroscopic) oocyte currents; no single-channel recordings are described anywhere in the text.

**Desensitisation and activation/deactivation kinetics.** Not found. The paper reports dose-response and I-V data but no desensitization extent/time constant, nor activation or deactivation time constants, for EXP-1. (Searched the full text for "desensit", "kinetic", "single-channel", "deactivat" - no hits beyond the dose-response and pharmacology data already quoted.)

**Agonist pharmacology.**
Quote: "the GABA agonist muscimol activated EXP-1 expressing cells (EC50 = 420.5 ± 1.09 µM, n = 5), demonstrating conservation of the GABA binding pocket." Measured. (Muscimol EC50 is ~16x higher than GABA's EC50 for EXP-1 - derived: 420.5/26.4 = 15.9.)

**Antagonist/blocker pharmacology.**
Quote: "Bicuculline is a competitive antagonist of GABAA receptors; surprisingly, EXP-1 is not blocked by bicuculline." "Picrotoxin is regarded as a pore blocker of ligand-gated anion channels..., and as expected, the EXP-1 receptor is not blocked by picrotoxin." "Mecamylamine is regarded as a cation channel blocker. Although the EXP-1 M2 pore domain is analogous to cholinergic receptors at the molecular and functional levels, the EXP-1 receptor is highly resistant to the channel blocking activity of mecamylamine." All measured (dose-response curves in Fig. 5f, applying EC50 GABA alone or with drug at varying concentrations, n=5-7), but no numeric IC50/Ki values given for bicuculline, picrotoxin or mecamylamine resistance - only that no significant block was seen. Numeric values: not found.

**Expression location.**
Quote: "Fluorescence was observed in the intestinal and anal depressor muscles, but not in the sphincter muscle." (transcriptional GFP fusion under 3.5-kb exp-1 promoter) Measured (anatomical/expression, not electrophysiology).
Quote: "The enteric muscles are comprised of three muscles classes: the intestinal, sphincter and anal depressor muscles."
Quote: "Interestingly, the inhibitory UNC-49B GABA receptor isoform is expressed in the sphincter muscle and not in the anal depressor or intestinal muscles. Thus, complementary expression patterns of excitatory and inhibitory GABA receptors can explain how AVL and DVB can cause muscle contraction in hermaphrodites and muscle relaxation in males." This is a key fact for the body-sex split: EXP-1 (excitatory) is NOT in the sphincter; UNC-49B (inhibitory) IS in the sphincter and NOT in anal depressor/intestinal muscles.
Quote on male anatomy: "due to differences in anatomy between hermaphrodites and males, expulsion is regulated by relaxation of the sphincter muscle in adult males." (cites ref 18, not further detailed in this paper)
Quote on synapse location: "GFP-tagged receptors were juxtaposed to the pre-anal ganglion where AVL and DVB innervate the enteric muscles, suggesting that EXP-1 receptors are clustered at sites that may correspond to neuromuscular junctions." Also: "DVB forms a neuromuscular junction at the dorsal edge of the preanal ganglion as depicted [ref 13]." And: "Fluorescence was observed in the intestine and anal depressor muscles as well as the neuron PDA. PDA is a motor neuron that receives input from the GABA motor neuron DVB and forms synapses on the dorsal muscles. Activation of this motor neuron may cause dorsal flexure, which could aid in opening the anus." Also expressed (translational fusion) in head neurons RID, ADE, SABD, and two unidentified head neurons - not enteric-muscle relevant but noted for completeness.

**exp-1 mutant phenotype (percent of cycles with EMC).**
Quote (Fig. 1a legend): "Percentage of EMC/def. cycle: wild type, 95.7 ± 2.0%; ox276, 20.0 ± 2.3%; n2570, 24.2 ± 2.1%; n2676, 24.0 ± 3.0%; n2641, 21.6 ± 1.7; sa6, 13.6 ± 4.0%; sa6; oxEx[EXP-1], 90.1 ± 4.6%; sa6; oxEx[EXP-1:GFP], 95.6 ± 2.2%." Measured. "Eleven defecation cycles from ten individual young adult animals were scored for each genotype." Scored at room temperature (22°C).
Quote: "exp-1 mutants have normal posterior and anterior body muscle contractions, but lack enteric muscle contractions (Fig. 1a). Moreover, these animals exhibit normal locomotion, which requires the inhibitory action of GABA. Thus, exp-1 is the only gene known to be specifically required for the excitatory function of GABA."
exp-1 allele table (Table 1): n2570 S140F, n2676 P187S, n2641 M233I, sa6 D280N, ox276 a 724 bp deletion causing a frameshift/early stop. All EMS-induced.

**In vivo recording from enteric muscles.** Not found in this paper. Beg & Jorgensen 2003 contains NO direct electrophysiological recording from enteric muscles (intestinal, sphincter or anal depressor) in vivo - all electrophysiology is from EXP-1-expressing Xenopus oocytes. No resting potential, evoked current, or evoked potential of the enteric muscles is reported here.

**UNC-49 / other GABA receptors on enteric muscles.**
Quote: "lack of the chloride-selective UNC-49 GABA receptor does not affect enteric muscle contraction, demonstrating that the inhibitory and excitatory actions of GABA are mediated by distinct GABA receptors." (cites ref 12, i.e. an earlier Bamber et al. paper on UNC-49B, not primary data in this paper)
Quote: "Interestingly, the inhibitory UNC-49B GABA receptor isoform is expressed in the sphincter muscle and not in the anal depressor or intestinal muscles." As above - sphincter gets UNC-49B (inhibitory, Cl-), anal depressor/intestine get EXP-1 (excitatory, cation).

**AVL/DVB and where they synapse.**
Quote: "two GABA motor neurons, one whose cell body is in the dorsorectal ganglion (DVB) and the other a ventral cord motor neuron (AVL), innervate the enteric muscles and are required for enteric muscle contraction." "When AVL and DVB are jointly laser-ablated, enteric muscle contractions are eliminated." "Flattened processes of the GABA motor neurons AVL and DVB abut the enteric muscles and DVB forms a neuromuscular junction at the dorsal edge of the preanal ganglion as depicted [ref 13]." (Fig. 3a legend) These synapse/ablation facts cite Thomas 1990 and McIntire et al. 1993 (ref 11) rather than being new data in this 2003 paper.

**unc-25 (GABA biosynthesis) mutant data cited (not primary to this paper):**
Quote: "In unc-25 mutants, which lack GABA immunoreactivity, enteric muscle contractions are reduced to 12% of the normal frequency." Labelled here as reported-by-citation (ref 11,15), not primary data of Beg & Jorgensen 2003.

## B. Jiang et al. 2022 Nat Commun, AVL/DVB spikes

Source: Jiang J, Su Y, Zhang R, Li H, Tao L, Liu Q. "C. elegans enteric motor neurons fire synchronized action potentials underlying the defecation motor program." Nat Commun 13:2783 (2022). PMID 35589790. doi:10.1038/s41467-022-30452-y. PMCID PMC9120479.
Full text opened: YES, via NCBI efetch XML (`efetch.fcgi?db=pmc&id=9120479&rettype=xml`), then stripped of XML tags with a short python script for readability. Open access (CC BY 4.0).

All recordings are whole-cell patch clamp from dissected worms (cell bodies of AVL and DVB), current-clamp or voltage-clamp as stated; GFP marks GABA neurons for identification. Measurements of resting membrane potential, threshold, peak amplitude, AHP and spike width were "made by hand with the measure function in Fitmaster (Heka)."

**Spike shape, resting potential, threshold, AHP, width (wild type).**
Quote: "Statistical measurements of resting membrane potential (DVB: -49.0 ± 3.6 mV; AVL: -45.7 ± 1.1 mV), threshold (DVB: -23.4 ± 1.6 mV; AVL: -23.3 ± 0.8 mV), peak amplitude (DVB: 26.3 ± 2.6 mV; AVL: 9.8 ± 0.8 mV), afterhyperpolarization (AHP) (DVB: -38.5 ± 2.5 mV; AVL: -64.8 ± 1.2 mV), and half-maximum spike width (DVB: 358.8 ± 59.5 ms; AVL: 394.2 ± 40.0 ms) for DVB (n = 5) and AVL action potentials (n = 17) in wild-type animals." (Fig. 1 legend) Measured.
Quote: "In particular, under suprathreshold stimuli, DVB membrane potential depolarized gradually at first, then evolved into an abrupt upstroke overshooting 20 mV after reaching a threshold of about -20 mV." Measured/descriptive.
Quote: "The peak of the upstroke was followed by a fast downstroke and a modest afterhyperpolarization (AHP), forming a broad spike of nearly 400 ms in half-maximum width" (describing AVL). Measured.
AVL fires a compound action potential: "AVL fires unusual compound action potentials with each depolarizing calcium spike mediated by UNC-2 followed by a hyperpolarizing potassium spike mediated by a repolarization-activated potassium channel EXP-2." DVB fires "giant calcium-mediated action potentials" without the negative spike (no EXP-2 current detected in DVB: "no EXP-2 currents were detected in DVB as shown in Fig. S2b").
Channels (brief, as requested): AVL positive spike mediated primarily by UNC-2 (CaV2/P-Q-type), minor contribution from EGL-19 (CaV1/L-type); AVL negative spike mediated by EXP-2 (repolarization-activated K+ channel); SHL-1 (Kv4) contributes separate transient currents but not needed for the negative spike (exp-2;shl-1 double mutant looks like exp-2 alone). DVB's channel identity was not electrophysiologically tested in this paper; cites "previous calcium imaging studies [ref 11,13] suggest that EGL-19 mediates calcium transient in DVB with a possible minor contribution from additional calcium channels," and "the repolarization of DVB action potential does not rely on potassium conductances but rather mainly on voltage-gated calcium channel inactivation." No voltage-gated Na+ channels: "the C. elegans genome lacks genes encoding voltage-gated sodium channels" (so these are calcium-based action potentials).

**Long AHP in AVL (slow timescale).**
Quote: "We accurately measured the length of the long-lasting AHP by inducing an action potential like waveform in AVL using a 1-s-long stimulus... and found the averaged AHP lasted for ~40 s, matching the duration of the intercycle." Measured, ~40 s AHP duration, matched (derived comparison) to intercycle duration.

**Number of spikes per cycle / firing pattern.**
Not reported as a simple count. Instead: "In wild-type animals, expulsion was reliably detected in 94.7% cycles (18 out of 19 cycles) and was always associated with synchronized AVL/DVB spikes." Implies essentially one synchronized AVL+DVB spike event (not a multi-spike burst) drives one expulsion per cycle in WT. No explicit "N spikes per cycle" count or instantaneous intra-burst firing frequency is given - not found.

**Timing relative to intestinal Ca wave, pBoc, aBoc, Exp.**
Quote: "The peak of posterior body muscle contractions preceded the peak of anterior body muscle contractions by ~2.5 s and the start of the intestinal calcium wave by ~1 s." (as written - the pBoc peak precedes the *start* of the Ca wave by ~1 s, meaning the Ca wave is already identified as starting very close after pBoc's peak; quoted exactly as the paper states it)
Quote: "Synchronized calcium spikes in AVL and DVB coincided with anterior body muscle contractions and expulsions but lagged about 3 s behind the intestinal calcium wave." Measured (imaging-derived delay, ~3 s).
Quote: "When both anterior body muscle contraction and expulsion events were clearly visible in the same cycle, we found that they were always initiated at roughly the same time... The near concurrence of anterior body muscle contraction and expulsion is consistent with their common control by intestinal neuropeptide signaling and the instantaneous action potential propagation along the AVL axon from head to tail." So aBoc and Exp are essentially simultaneous; both lag the intestinal Ca wave onset by ~3 s per the AVL/DVB-spike measurement above.
Quote: "These measurements are consistent with the existing model that the posterior body muscle contraction is directly activated by calcium-mediated proton release from the intestine and that AVL and DVB drive anterior body muscle contraction and expulsion steps downstream of the intestinal clock."
Delay between AVL and DVB spikes themselves: reported as a figure (Fig. 7d, "Time delay between AVL and DVB spikes in wild-type, exp-2(lf), inx-1, and inx-1 rescued animals") but the numeric value for WT delay is in the figure, not stated as a sentence in the text I extracted - not found as a quoted number (only group n's: WT n=19 from 12 animals).

**Double-expulsion timing (a kinetic proxy for one EMC's duration).**
Quote: "The average delay between the two consecutive expulsions in exp-2(lf) was 430 ± 155 ms (n = 6), which corresponds well with the averaged spike width of AVL action potential (394.2 ± 40.0 ms, n = 17)." Measured; the paper explicitly links a ~400-430 ms timescale to how closely two expulsions can follow each other when AVL's negative spike (normal "brake") is missing.

**Ca imaging of AVL/DVB (not muscle) timing/amplitude:** "Indeed, in immobilized worms expressing GCaMP6f in GABAergic neurons including AVL and DVB, spontaneous and periodic calcium spikes were detected in the cell body of both neurons." No Ca imaging of the enteric muscles themselves is reported in this paper - not found (this paper images neurons and the intestine, not the muscles).

**EXP-1 / exp-1 mutant statements.** EXP-1 appears only in the Introduction/Discussion as background, not as new data: "release the neurotransmitter GABA at the neuromuscular junctions (NMJs) to activate downstream enteric muscles through excitatory GABA receptors EXP-1" and in the reference list ("Beg AA, Jorgensen EM, EXP-1 is an excitatory GABA-gated cation channel, Nat..." ref 12). No exp-1 mutant was recorded or analyzed in this paper - not found beyond the citation.

**exp-2 mutant and unc-2 mutant spike data (for context, since they report full tables):**
WT vs egl-19 vs unc-2(lf) vs unc-2(gf), AVL: Vrest WT -45.7±1.1 mV, egl-19 -42.1±2.3, unc-2(lf) -46.4±2.5, unc-2(gf) -38.2±13.4 mV. Peak amplitude: WT 9.8±0.8, egl-19 10.2±1.2, unc-2(lf) -0.6±1.9, unc-2(gf) 7.4±2.2 mV. Threshold: WT -23.3±0.8, egl-19 -20.8±1.4, unc-2(lf) -22.8±2.0, unc-2(gf) -28.1±1.5 mV. Spike width: WT 394.2±40.0, egl-19 387.9±67.6, unc-2(lf) 234.3±48.4, unc-2(gf) 677.7±147.8 ms. All measured, n=17/8/8/8 respectively.
exp-2(lf)/exp-2(gf) AVL: Vrest -43.1±1.1 / -49.0±2.8 mV; peak amplitude 9.1±0.4 / 9.4±2.4 mV; threshold -24.8±0.8 / -20.2±1.4 mV; spike width 334.7±34.5 / 144.9±12.8 ms. n=7/5. Measured.
These are all AVL (neuron) properties, included here only because they are the fullest quantitative membrane-property tables in the paper and may be useful context; they are NOT the enteric muscle.

## C. Enteric muscle membrane properties

Short answer: direct electrophysiology (resting potential, input resistance, capacitance, action potentials) of the C. elegans intestinal muscles, anal sphincter or anal depressor was NOT FOUND in any free source opened in this session. What exists and was found:

**Expression pattern only, no electrophysiology (from Beg & Jorgensen 2003, section A above):** EXP-1 (excitatory, cation-selective GABA receptor) is expressed in the intestinal and anal depressor muscles, not in the sphincter. UNC-49B (inhibitory, Cl- GABA receptor) is expressed in the sphincter, not in anal depressor or intestinal muscles. No resting potential, input resistance, capacitance, Ca transient or channel current was recorded from any of these three muscle classes in that paper - it is anatomy (GFP) only.

**Jiang et al. 2022 (section B above):** records only AVL and DVB (neurons) and the intestine's calcium wave. It does NOT record from, or image calcium in, the intestinal muscles, sphincter or anal depressor. No muscle resting potential, Ca transient duration, or channel data for the muscles themselves. The ion channels this paper characterizes (UNC-2, EGL-19, EXP-2, CCA-1, SHL-1, NCA-1/NCA-2, EGL-36) are all shown to act in the AVL neuron (a few in DVB by inference/citation only), not in the enteric muscles. Not found: any of these channels directly demonstrated in the intestinal/sphincter/anal depressor muscle membrane.

**Male anal depressor muscle (Garcia lab):** LeBoeuf B, Chen X, Garcia LR. "WNT regulates programmed muscle remodeling through PLC-β and calcineurin in Caenorhabditis elegans males." Development 147(9):dev181305 (2020). PMID 32317273. PMCID PMC10679511.
Full text opened: NO, abstract only. NCBI efetch for this PMCID returned only front matter/abstract (`pmc-prop-has-pdf: no` in the PMC metadata, suggesting PMC holds only the abstract/metadata for this record, not the body). Attempted the publisher page `https://journals.biologists.com/dev/article/147/9/dev181305/225520` directly; it returned a Cloudflare "Just a moment..." bot-check page (HTTP 403), so the full text was not retrievable through free means in the time available.
Quote (abstract, confirmed quoted from the metadata returned by efetch): "In hermaphrodites and larval males, the single cell anal depressor muscle, used for waste expulsion, contains bilateral dorsal-ventral sarcomeres. However, prior to male adulthood, the muscle sex-specifically remodels its sarcomeres anteriorly-posteriorly to promote copulation behavior... We show that WNT signaling through Gαo and PLC-β results in sustained Ca2+ release via IP3 and ryanodine receptors to activate calcineurin."
Label: measured (stated as a result in the paper), but this is development/sarcomere remodeling, not an electrophysiological membrane property. This IS male-specific data - it is explicitly described as occurring "prior to male adulthood" as a sex-specific remodeling of the one anal depressor muscle cell shared with hermaphrodites. No resting potential, current or channel numbers are visible in the abstract; the paper evidently used Ca2+ imaging and "controlled Ca2+ release" but no quantitative Ca2+ transient amplitude/duration numbers were retrievable without the body text. Not found: any membrane electrophysiology number for the anal depressor in this paper (could not access body text).

**Duration of one expulsion contraction:** not directly measured here as a muscle-contraction duration, but see section D below for a closely related number: in Jiang et al. 2022, the measured delay between two consecutive expulsion events within one cycle in exp-2(lf) mutants was 430 ± 155 ms (n=6), and the authors note this "corresponds well with the averaged spike width of AVL action potential (394.2 ± 40.0 ms, n=17)" - i.e. the fastest two expulsions can follow each other is around 400-430 ms, which is a lower bound / proxy time constant related to one EMC's underlying drive, not a direct measurement of muscle contraction duration itself.

**Computational model of the enteric muscles or the expulsion step:** NOT FOUND. Jiang et al. 2022 built a Hodgkin-Huxley type model, but explicitly of the AVL neuron's action potential (channels UNC-2, EGL-19, CCA-1, SHL-1, EXP-2, NCA, EGL-36), not of any enteric muscle. No model of the intestinal, sphincter or anal depressor muscle membrane, nor of the expulsion contraction itself, was found in any source opened this session.

**Gap junction innexins in enteric muscles:** INX-1 is shown (Jiang et al. 2022) to electrically couple AVL and DVB (the two neurons), synchronizing their spikes; "calcium spikes in AVL and DVB were de-synchronized in inx-1(lf) mutant background." This is neuron-neuron coupling, not muscle-muscle or neuron-muscle gap junction data. No innexin data for the enteric muscles themselves was found.

## D. Timing of the motor program (pBoc -> aBoc -> Exp)

**Wang et al. 2013 Curr Biol** (title: "Neuropeptide secreted from a pacemaker activates neurons to control a rhythmic behavior"; this is the nlp-40 paper, confirmed PMCID PMC3651789 via esummary title match).
Full text opened: YES, via efetch XML, tags stripped with python.
Quote: "the C. elegans defecation motor program is a very simple rhythmic behavior with a period of about 50 seconds. It is composed of three stereotypical, sequential muscle contractions: first, the posterior body wall muscles contract (pBoc); three seconds later, the anterior body wall muscles contract (aBoc); next, the enteric muscles contract which leads to the expulsion (Exp) of digested food from the intestine."
Quote (Figure 1A legend, same number restated): "Each cycle is initiated with posterior body wall muscle contraction (pBoc), and 3 seconds later, anterior body wall muscles contract (aBoc), which is immediately followed by enteric muscle contraction (the expulsion (Exp) step)."
So: pBoc -> aBoc delay = 3 s (measured, stated directly, no error bars given in the sentence); aBoc -> Exp delay = "immediately" (not quantified in seconds in this paper - qualitative, not found as a number here, though Jiang 2022 above effectively quantifies "immediately" as near-simultaneous, see section B).
Quote on DVB Ca spike timing relative to pBoc and Exp: "In wild type worms, we observed a single robust calcium spike in the synaptic region of the DVB neuron (and also often in the cell body) that began approximately three seconds following each pBoc step, peaked immediately before each Exp step, and returned to baseline about two to three seconds following Exp." Measured (Ca imaging, GCaMP3.0 in DVB).
Quote on NLP-40 peptide injection timing: "the NLP-40 P3-1 peptide consistently induced a single calcium spike in DVB neurons 3.5 ± 0.60 (mean ± s.d.) seconds following injection (10 out of 10 injections, n=10 worms)." Measured, but this is an artificial-injection experiment timing, not the natural pBoc-to-DVB-spike delay (which is the ~3 s figure above).

**Jiang et al. 2022** (section B, repeated here for the D question specifically):
Quote: "The peak of posterior body muscle contractions preceded the peak of anterior body muscle contractions by ~2.5 s and the start of the intestinal calcium wave by ~1 s." Measured.
Quote: "Synchronized calcium spikes in AVL and DVB coincided with anterior body muscle contractions and expulsions but lagged about 3 s behind the intestinal calcium wave." Measured.
Note the apparent discrepancy between papers: Wang et al. 2013 states pBoc precedes aBoc by 3 s; Jiang et al. 2022 states the pBoc PEAK precedes the aBoc PEAK by ~2.5 s. Both are measured, in different labs/years, with a small (0.5 s) difference - both numbers are quoted verbatim above and should be treated as two independent measured values, not reconciled by me.

**Espelt et al. 2005, J Gen Physiol** (PMCID PMC2266627, as given in the brief). Full text opened: YES, via efetch XML, tags stripped.
This paper is about intestinal epithelial Ca2+ oscillation genetics (itr-1, egl-8/PLC-β, plc-3/PLC-γ), not directly about aBoc/Exp timing, but it gives the intestinal Ca2+ oscillation rise and fall times and pBoc period in the control (glo-1) background:
Quote (Table I): "glo-1 [pBoc period] 55 ± 1 (6) s, [pBoc CV] 4 ± 1% (6), [Ca2+ oscillation period] 49 ± 3 (6) s, [Ca2+ oscillation CV] 16 ± 1% (6), [Ca2+ oscillation rise time] 8 ± 1 (5) s, [Ca2+ oscillation fall time] 23 ± 3 (5) s." All measured, room temperature (21-22°C), 2-day-old adult worms.
Quote: "Oscillatory changes in intestinal epithelial cell Ca2+ levels track the defecation cycle with Ca2+ levels peaking just before the initiation of pBoc." Measured/qualitative - i.e. the intestinal Ca2+ peak comes just before pBoc, consistent with pBoc being triggered by the Ca2+ peak (not contradicting the Jiang 2022 statement above about Ca wave "start").
No aBoc or Exp timing number is given in this paper - not found (this paper doesn't track aBoc/Exp at all, only pBoc and intestinal Ca2+).

**Thomas 1990 Genetics, Liu and Thomas 1994, Teramoto and Iwasaki 2006, Nehrke papers:** NOT opened. Thomas JH 1990 Genetics ("Genetic analysis of defecation in Caenorhabditis elegans") predates PMC/NIH open access mandates; PubMed/PMC search for it and for "Liu Thomas 1994" returned no PMC record (0 results for the Liu/Thomas 1994 search). Did not find a free full text for either in the time available. Teramoto & Iwasaki 2006 and the Nehrke PBO papers were located by PMC ID search (PMC9374441 = "Distinct roles for two C. elegans acid-sensing ion channels in an ultradian clock" turned up for both searches, and PMC3273995/PMC2258244 for Nehrke-adjacent queries on the intestine's Na+/H+ exchange and proton signaling) but were not opened/read in the time budget - noting them as leads, not as sourced quotes. Not found: any quoted sentence from these specific papers in this session.

## Gaps / not found

- EXP-1 single-channel conductance: not found (Beg & Jorgensen 2003 report only whole-cell oocyte currents).
- EXP-1 desensitization extent/time constant, activation/deactivation kinetics: not found anywhere in Beg & Jorgensen 2003 (no such data reported).
- EXP-1 Ca2+ and Cl- permeability ratios as explicit numbers (PCa/PNa, PCl/PNa): not found; only qualitative "negligible" (divalent) and "no significant contribution" (Cl-) statements with matched reversal potentials.
- Numeric IC50/Ki for bicuculline, picrotoxin, mecamylamine on EXP-1: not found (paper states "not blocked"/"resistant" without a number).
- Direct electrophysiology (Vrest, input resistance, capacitance, action potential or Ca transient duration) of the intestinal muscles, anal sphincter, or anal depressor (hermaphrodite or male): not found in any source opened.
- Numeric Ca2+ transient / electrophysiology data for the male anal depressor muscle (LeBoeuf, Chen & Garcia 2020, Development): abstract only opened; full text blocked by Cloudflare bot check at the publisher and not available as full text via PMC efetch.
- A published computational model of the enteric muscles themselves or of the expulsion contraction: not found (the only model found, in Jiang et al. 2022, is of the AVL neuron's action potential, not the muscle).
- Number of action potentials/spikes per defecation cycle in AVL/DVB as an explicit count, and the intra-burst instantaneous firing frequency: not found as a stated number (the paper's data imply essentially one synchronized AVL+DVB spike event per cycle, associated with 94.7% of cycles showing expulsion, but no "N spikes/cycle" sentence was found).
- Numeric value for the WT AVL-DVB spike time delay (shown only in Fig. 7d of Jiang et al. 2022, not stated as a text sentence in the portions I could parse from the XML).
- aBoc -> Exp delay as a quantified number in seconds: only described as "immediately" (Wang et al. 2013) or effectively simultaneous (Jiang et al. 2022); no explicit seconds value found for this specific sub-delay.
- Thomas 1990 Genetics, Liu & Thomas 1994, Teramoto & Iwasaki 2006, and the Nehrke PBO-4/5/6 papers: not opened (see section D).

## Failed URLs / attempts

- `https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/nn1136?...` - returned metadata but `openAccessPdf.status: "CLOSED"`, no usable PDF URL.
- `https://jorgensenlab.com` - HTTP 403.
- `https://jorgensen.biology.utah.edu` (bare) - HTTP 200 but it's just an old redirect page to `https://www.thejorgensenlab.org/`; not itself useful, but following the redirect and then `/publications` worked and gave the real PDF link.
- `https://duckduckgo.com/html/?q=...` - returned HTTP 202 with a JS challenge page, no results extracted (switched to the WebSearch tool instead, which worked).
- `https://journals.biologists.com/dev/article/147/9/dev181305/225520` (LeBoeuf, Chen & Garcia 2020 Development, full text) - HTTP 403, Cloudflare "Just a moment..." bot-check page. Not retrieved.
- PMC esearch queries for "Liu Thomas 1994 defecation C. elegans" - 0 results; this paper does not appear to be in PMC under a free-text search.
- Did not attempt Sci-Hub/LibGen/any non-free source, per instructions.

## Note on scope not completed

Given the ~25 minute budget, sections A and B (Beg & Jorgensen 2003; Jiang et al. 2022) were covered thoroughly with full text opened for both. Section C came back largely empty for genuine enteric-muscle electrophysiology - this looks like a real gap in the free literature, not a search failure, but Teramoto & Iwasaki 2006, the Nehrke PBO papers, and the LeBoeuf/Chen/Garcia 2020 full text were not read closely and could still contain useful numbers; they are flagged above as unopened leads for a follow-up pass if more time is allocated.
