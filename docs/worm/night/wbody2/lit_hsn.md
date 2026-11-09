# HSN membrane model: literature survey

Date of search: 2026-11-08 (NCBI eutils / Europe PMC / direct PMC page text / cengen.org). Zhang, Schafer & Breitling 2010 and Collins et al. 2016 eLife 5:e21126 are check-only per instructions: not used as a source of numbers below.

## 1. Published electrophysiology of HSN itself

**Main finding: Ravi et al. 2021, Genetics 218(4):iyab080, PMID 34037773, PMC8864752. OPENED (full text via PMC page).** Whole-cell patch clamp done directly on HSN cell bodies, not a model or indirect assay.

Prep, quoted: "day 2 adult worms were glued on the surface of Sylgard-coated coverslips using the cyanoacrylate-based glue (Gluture Topical Tissue Adhesive, Abbott Laboratories). A dorsolateral incision was made using a sharp glass pipette to expose the cell bodies of HSN neurons for recording." Rig: "upright microscope (Olympus BX51WI) coupled with an EPC-10 amplifier and Patchmaster software." Bath (mM): "145 NaCl, 2.5 KCl, 5 CaCl2, 1 MgCl2, and 20 glucose (325-335 mOsm, pH 7.3)." Pipette (mM): "145 KCl, 5 MgCl2, 5 EGTA, 0.25 CaCl2, 10 HEPES, 10 glucose, 5 Na2ATP and 0.5 NaGTP (315-325 mOsm, pH 7.2)." Method: "resting membrane potentials were tested with 0 pA holding under the Current Clamp model of the whole-cell patch." Figure 5B, n >= 7 animals/genotype, error bars are 95% CI (no SEM/SD given; no input resistance or capacitance reported anywhere in the paper, checked explicitly, not found):

| genotype | resting potential |
|---|---|
| wild type | -21.8 mV |
| HSN::Pertussis Toxin (Go silenced) | -14.75 mV (depolarized) |
| goa-1(n1134) lf | -17.9 mV (depolarized vs WT) |
| egl-10(md176) (RGS lf, excess Go) | -40.8 mV (hyperpolarized) |

This is the single most load-bearing number for the model: published wild-type HSN resting potential is **-21.8 mV**, far more depolarized than our current silent -54 mV. Even the most hyperpolarized genotype measured (egl-10(md176), excess inhibitory Go signaling) is only -40.8 mV.

**Yue et al. 2018, Neuron 97(2):571-585, PMC7038793 (TMC paper). OPENED.** Also real whole-cell patch of HSN (same solution recipe, Kang lab methods tradition). Voltage clamp at -60 mV for leak current. Quoted: "HSN neurons were hyperpolarized and the Na+-leak currents were significantly reduced in tmc-1 mutant worms" (Fig 5D) and "transgenic expression of TMC-1 in HSN neurons of tmc-1(ok1859) mutant worms completely rescued the defective resting membrane potential and Na+-leak conductance" (Fig 5E-F), n >= 12/genotype, significance stars present but the actual mV/pA numbers are only in the bar-graph artwork, not recoverable as text (flagged: opened, numbers graphical only). Channel gene: **tmc-1** (background Na+-leak conductance setting HSN resting potential).

**Emtage et al. 2012, J Neurosci 32(46):16285-16295, PMC3544400 (IRK-1). OPENED.** No HSN patch clamp. IRK-1 (Kir) characterized by two-electrode voltage clamp in Xenopus oocytes only: oocytes "voltage clamped at -10 mV, and subjected to a series of voltage steps from -80 to +60 mV" show "large inwardly rectified whole-cell currents," and IRK-1 expression "caused the resting membrane potential of oocytes to be close to the reversal potential of potassium" (qualitative, no mV number quoted in text). In the worm: "We observed strong expression of Pirk-1::yfp in the HSN motor neurons" (Fig 2C), a qualitative reporter call, not a quantitative expression level. Epistasis: egl-6(gf) egg-laying suppression by irk-1 deletion, p=1.3e-15 (Table 1). Channel gene: **irk-1**.

**Zang, Ho & Ringstad 2017, eLife 6:e22771, PMC5330680 (T-type Ca channel). OPENED.** No HSN patch clamp. "cca-1...mutates to strongly and specifically suppress the effects of excess peptidergic inhibition onto serotonin neurons" (Results) is genetic/behavioral evidence for cca-1 in HSN, not electrophysiology. The only electrophysiology in the paper is mammalian Cav3.1 in Xenopus oocytes (half-activation -37.14+-2.4 mV WT vs -44.69+-1.4 mV mutant; half-inactivation -58.18+-0.7 vs -63.11+-0.3 mV, Fig 4), heterologous and not native C. elegans CCA-1, not HSN; label as **inferred** at best, not a direct source for HSN cca-1 kinetics. Channel gene: **cca-1**.

**Shyn, Kerr & Schafer 2003, Curr Biol 13(21):1910-1915, PMID 14588249. ABSTRACT ONLY** (not open access, no PMC record; Europe PMC confirms inEPMC=N). From the PubMed abstract: "the spontaneous activity of the egg-laying motorneurons was silenced by serotonin... mutations in the G(o)alpha homolog goa-1 prevented the silencing of motorneuron activity by serotonin." Method was cameleon Ca2+ imaging, not patch clamp. No numbers in the abstract.

**Banerjee et al. 2017, PLoS Genetics 13(4):e1006697, PMC5398689. OPENED.** No HSN electrophysiology or Ca imaging numbers; only quantified datum is behavioral/genetic (egl-47, goa-1 epistasis with nlp-7 overexpression, Fig 7D). "NLP-7 peptides do not activate EGL-6 in vitro" (qualitative negative result).

**Collins & Koelle 2013, J Neurosci 33(3):761-775, PMC3542984 (ERG/unc-103).** Found by search, checked by title/snippet only (not opened in full): indicates unc-103 acts **postsynaptically in the vulval muscle**, not presynaptically in HSN. Noted so it is not mistakenly ported as an HSN channel.

**Branicky et al. 2014, J Neurosci 34(11):3933-3945, PMC3891957 (clh-3). OPENED.** HSN assayed by cameleon Ca2+ imaging only, not patch clamp: "HSN imaging was performed essentially as described previously using the integrated Cameleon ljIs19 [pcat-1::YC2.1]." Figure 5 reports spike frequency for clh-3 mutants vs wild type but the numeric values are only in the figure artwork; text states clh-3(n995gf) "significantly reduces the spike frequency," n > 13 recordings (145 spikes for clh-3(n995), >750 spikes other genotypes).

**No published HSN input resistance or capacitance was found anywhere** (checked explicitly in Ravi 2021 and Yue 2018, and searched generally: "HSN input resistance", "HSN capacitance patch clamp C. elegans"). Genuine gap, not an oversight.

Ravi & Collins 2018/2019 micropublications (PMC7252377, PMC7255765) opened but are Ca imaging / defecation-coupling notes, not electrophysiology; no numbers beyond item 2 below.

## 2. Published HSN Ca imaging numbers

**Zhang et al. 2008, Curr Biol 18(19):1445-1455, PMC2621019. OPENED.** Indicator: cameleon ("ljIs25[myo-3::YC2.0]" vulval muscle, "ljIs19[cat-1::iYC2.1]" HSN/VC). Under low-osmolarity perturbation (not baseline): "both HSN and VC neurons exhibited calcium spikes in a strikingly rhythmic pattern, with periods ranging from 6 to 12 seconds" (Fig 3B,C); under high osmolarity "HSN is originally hypoactive" (Fig 4B,C). "The onset of the neuronal calcium transient preceded the egg-laying event by an average of approximately 1 second" (Fig 2). No rise/decay time constants given. These are osmotic-perturbation numbers, not resting active/inactive-state baselines.

**Ravi, Garcia & Collins 2018, J Neurosci 38(37):8060-8074, PMC6041790. OPENED.** Indicator: "GCaMP5 along with mCherry in HSN using the nlp-3 promoter," ratiometric (GCaMP5:mCherry). Reports intertransient interval, not transients/min: inactive-like L4.7-8 stage median ~34 s (Fig 2D); active state shows burst firing with "<20 s intertransient intervals" (Fig 2D). No transients-per-burst count, no intraburst interval, no rise/decay kinetics in text. Typically ~10 animals/genotype pooled for peak-amplitude figures.

**Ravi et al. 2021, Genetics, PMC8864752. OPENED (same paper as item 1).** Best-quantified HSN Ca record found: wild type "average HSN Ca2+ transient frequency of about ~0.4 transients per minute" (Fig 3C); HSN::Pertussis-Toxin (Go silenced) "average 1.9 transients per minute" (Fig 3C); goa-1(sa734) null shows a "significant increase" in frequency (Fig 2B,C); egl-10(md176) (excess Go) shows "single HSN Ca2+ transients occurring several minutes apart" (Fig 2A,B). GCaMP5/GCaMP5G, nlp-3 promoter.

**Brewer, Olson, Collins & Koelle 2019, PLoS Genetics 15(1):e1007896, PMC6363226. OPENED.** GCaMP5 used, but HSN Ca2+ itself is not quantitatively reported; the quantified Ca2+ data are for the vulval muscle ("vm1+vm2 vulval muscle contractions occurred exclusively within active phases, the ~2-minute intervals during which eggs were laid"). HSN was optogenetically driven, not imaged, in the figures checked.

**Chen, Zang, Ahamed & Ringstad 2025, Sci Adv 11, PMC12002139. OPENED.** GCaMP6 (promoter not stated in excerpted Methods). "Wild-type HSNs exhibited spontaneous Ca2+ transients that were almost completely abolished in egl-6(gf) mutants" (Fig 1B); in the EGL-6 suppressor "spikes in HSNs of egl-6(gf) sup(n5210) animals were narrower and had faster decay time constants than spikes recorded from the wild type" (qualitative only, no numeric decay tau in text, only figure).

Shyn et al. 2003: abstract only, see item 1 (cameleon, qualitative silencing by serotonin, no numbers). Collins et al. 2016 eLife and Zhang/Schafer/Breitling 2010: deliberately not opened/used as sources (check-only per instructions).

## 3. CeNGEN ion channel gene expression in HSN (threshold 2-4)

CeNGEN (Taylor et al. 2021, Cell 184(16):4329-4347, PMC8710130) threshold CSVs ARE freely downloadable (not blocked): `cengen.org/storage/021821_medium_threshold2.csv`, `..._conservative_threshold3.csv`, `..._stringent_threshold4.csv`. Per the site's own description (OPENED, www.cengen.org/downloads): "For binary expression patterns, csv files are available for thresholds 1 (most permissive)...4 (most stringent)... a gene determined not expressed in a cell has a value of 0, a gene above the threshold has a value >0 (the average TPM per gene per neuron type, as calculated by the monocle3 package)." Downloaded directly and parsed for the HSN column (values = average TPM when called expressed; 0 = not called expressed at that threshold):

| gene | family | thr2 | thr3 | thr4 |
|---|---|---|---|---|
| egl-19 | Ca L-type (Cav1) | 198.8 | 198.8 | 198.8 |
| unc-2 | Ca P/Q-type (Cav2) | 72.5 | 72.5 | 72.5 |
| cca-1 | Ca T-type (Cav3) | 1067.0 | 1067.0 | 0 (drops out) |
| nca-2 | NALCN-like Na leak | 161.5 | 161.5 | 161.5 |
| nca-1 | NALCN-like Na leak | absent from dataset (searched, not found) | | |
| unc-80 | NALCN complex | 564.4 | 564.4 | 564.4 |
| unc-79 | NALCN complex | 147.5 | 147.5 | 147.5 |
| kcnl-1 | SK | 1080.7 | 1080.7 | 1080.7 |
| kcnl-2 | SK | 141.4 | 141.4 | 141.4 |
| kcnl-4 | SK | 38.3 | 38.3 | 0 (drops out) |
| slo-1 | BK | 117.7 | 117.7 | 117.7 |
| slo-2 | BK (Na/Cl-activated) | 64.7 | 64.7 | 64.7 |
| unc-103 | ERG | 47.3 | 47.3 | 0 (drops out) |
| egl-2 | EAG | 0 | 0 | 0 |
| shk-1 | Shaker | 0 | 0 | 0 |
| shl-1 | Shal | 42.1 | 42.1 | 42.1 |
| irk-1 | Kir | 131.6 | 131.6 | 131.6 |
| irk-2 | Kir | 39.1 | 39.1 | 39.1 |
| irk-3 | Kir | 34.4 | 34.4 | 34.4 |
| egl-6 | NPY-like GPCR | 227.7 | 227.7 | 227.7 |
| lgc-55 | tyramine-gated Cl | 33.5 | 33.5 | 33.5 |
| egl-30 | Gq alpha | 1626.6 | 1626.6 | 1626.6 |
| goa-1 | Go alpha | 625.9 | 625.9 | 625.9 |
| egl-10 | RGS | 121.4 | 121.4 | 121.4 |
| flp-10 / flp-17 / nlp-7 | neuropeptide | 0 / 0 / 0 | 0 / 0 / 0 | - |
| ser-1 / ser-4 / ser-7 / mod-1 | 5-HT receptor | 0 / 201.3 / 0 / 0 | same | - |
| tph-1 / cat-1 | 5-HT synthesis / VMAT | 1610.5 / 579.6 | - | - |

flp-10/flp-17/nlp-7 reading 0 is expected: those peptides are released *onto* HSN by other cells (uv1 etc), not made by HSN. ser-1/ser-7/mod-1 reading 0 in CeNGEN but ser-1 and ser-7 reported "expressed in HSN" by GFP reporter in a 2020 paper (item 5) is a real discrepancy between RNA-seq threshold calls and transgenic reporter data, flagged rather than silently resolved. nca-1 is genuinely absent from the whole CeNGEN gene matrix (not merely zero in HSN), searched by gene name, not found in any threshold file.

CengenApp (`cengen.shinyapps.io/CengenApp`) and `www.cengen.org` are the stated free access points (quoted Data Availability: "The raw data are available at GEO (single cell data: Accession Number GSE136049, bulk sequence data: Accession Number GSE169137)... The full and neuron only datasets are available at www.cengen.org.") HSN confirmed as one of the 128 profiled neuron classes (present as a named column in the downloaded CSVs).

## 4. Published biophysical/conductance-based HSN models

**OpenWorm c302** (Gleeson et al. 2018, Phil Trans R Soc B, PMC6158223; repo github.com/openworm/c302, checked directly as a repo listing, not as a paper). No HSN-specific parameter file or tuned conductance set found. The framework applies a shared generic parameter set (e.g. "neuron_leak_cond_density" fixed at e.g. 0.005 mS/cm^2) across all neurons in a given configuration (A/B/C/D), mostly integrate-and-fire or single-compartment generic cells, not per-cell-type biophysics. README states c302 "is still in active development and not all of the configurations are producing physiologically realistic results."

**BAAIWorm-type model**: Zhao et al. 2024, Nat Comput Sci, "An integrative data-driven model simulating C. elegans brain, body and environment interactions," PMC11659166. OPENED. No sentence mentions HSN by name anywhere in retrievable text. Model has "14 ion channel classes" in a generic multicompartmental scheme, explicitly builds on OpenWorm/c302 and Sibernetic: "OpenWorm developed data-driven models of both the nervous system (c302, ref. 9) and the body (Sibernetic)... BAAIWorm builds upon OpenWorm's valuable tools and data, such as cell model morphology, synaptic dynamics and 3D worm body information." No HSN-specific parameter set found.

**Nicoletti et al. 2019** (PMC6602206) models AWCon and RMD only, not HSN (confirmed by title, not opened in depth since title already answers the question: "Single ion currents and whole-cell dynamics of AWCon and RMD").

**Conclusion for item 4**: no open, HSN-specific conductance-based model was found in c302, BAAIWorm, or the general egg-laying modelling literature searched. Any such model would have to be built from the Ravi 2021 / Yue 2018 patch data plus the CeNGEN channel list above, labelled fitted/inferred, not ported from an existing parameter set.

## 5. Neuromodulator/receptor inputs onto HSN with numbers

**EGL-6 / FLP-10 / FLP-17**: Ringstad & Horvitz 2008, Nat Neurosci 11(10):1168-1176, PMC2963311. OPENED. "We detected egl-6::gfp expression using an antibody to GFP and observed strong and consistent expression in HSN motor neurons" (Fig 3a). Oocyte pharmacology: "flp-10 peptides were effective at nanomolar concentrations" (Fig 4e,f); peptide sequences: FLP-10 = QPKARSGYIRFamide, FLP-17 = KSAFVRFamide and KSQYIRFamide; response measured as "the ratio of the peptide-evoked inward K+ current" (consistent with EGL-6 coupling to IRK-1, item 1). No exact EC50 recoverable from text, only figure. Downstream channel: irk-1 (Emtage 2012, item 1).

**NLP-7 / EGL-47**: Banerjee et al. 2017, PMC5398689. OPENED. "EGL-47 may act directly as a receptor for NLP-7 peptides"; "mutation of egl-47 partially restores egg-laying in NLP-7 OE animals" (Fig 7D); "Combined mutation of egl-47 and goa-1...completely reverses the effects of nlp-7 overexpression" (Fig 7D), epistasis not a current/concentration number. "NLP-7 peptides do not activate EGL-6 in vitro" (negative pharmacology).

**Tyramine / LGC-55**: Pirri et al. 2009, Neuron 62(4):526-538, PMC2804440. OPENED. HSN is listed among cells expressing an lgc-55::mCherry reporter ("We have identified these neurons as the AVB, RMD, SMDD, SMDV, IL1D, IL1V, SDQ, HSN and ALN neurons," Fig 4A), but the functional/electrophysiology work on LGC-55 is in body wall muscle and Xenopus oocytes, not HSN. Oocyte pharmacology (not HSN-specific, same channel): tyramine EC50 = 12.1 +/- 1.2 uM, maximum current = 2.2 +/- 0.17 uA (Fig 3B). The 2025 uv1-feedback paper (Yan, Claman, Bode & Collins, J Neurosci, PMC11800740, OPENED) states only qualitatively: "The uv1 cells release tyramine and neuropeptides that may signal to inhibit HSN activity and terminate the egg-laying behavior active state," no quantitative uv1-to-HSN current or concentration data found (searched explicitly, not found).

**Gq/Go (EGL-30/GOA-1)**: Shyn et al. 2003 (abstract only, item 1): goa-1 mutation blocks serotonin-driven silencing of HSN activity. Ravi et al. 2021 (item 1): goa-1 loss depolarizes HSN (-17.9 mV vs -21.8 mV WT) and raises Ca2+ transient frequency; Go signaling is presynaptic within HSN itself (title: "Presynaptic Galpha-o (GOA-1) signals to depress command neuron excitability"). NALCN (nca-1/nca-2/unc-80/unc-79) was tested as a possible downstream target and ruled out: micropublication PMC10823792 (OPENED), "NALCN channels are not required for the increased egg laying in mutants with too much excitatory Galpha-q or lacking inhibitory Galpha-o signaling", useful negative result: don't wire nca-1/2 as the Go/Gq effector in HSN.

**Serotonin autoreceptors on HSN**: searched specifically (Dhakal et al. 2022, Genetics, PMC9252285, OPENED). All quantified serotonin-receptor signaling in that paper (ser-1/ser-4/ser-7/mod-1, Gq/Trio/DAG) is on the postsynaptic vulval muscle, not an HSN autoreceptor: "serotonin released from the HSN signals through G-protein-coupled serotonin receptors expressed on the vulval muscles." No HSN-autoreceptor current or Ca number found, searched and explicitly absent from this paper.

## Searches that found nothing usable (queries logged)

- "HSN input resistance" / "HSN capacitance patch clamp" -- no hits with numbers in any paper opened.
- "nca-1 HSN CeNGEN" -- gene absent from the entire CeNGEN threshold matrix, not just zero in HSN.
- Direct EGL-6 EC50 or Kd number for FLP-10/FLP-17 in text (only in figure graphics, Ringstad & Horvitz 2008).
- Burst structure (transients-per-burst, intraburst interval) for HSN with an actual number, in any paper opened (Ravi 2018, Ravi 2021, Brewer 2019, Zhang 2008): always qualitative "bursts," with interval cutoffs (<20 s, <30 s) used to *define* a burst, not a mean burst size reported as text.
- uv1-to-HSN tyramine current or concentration number -- not found (Yan et al. 2025 is qualitative only).

## Summary table

| quantity | value | units | source | opened? | label |
|---|---|---|---|---|---|
| HSN resting potential, WT | -21.8 | mV | Ravi 2021 PMC8864752 Fig 5B | yes | measured |
| HSN resting potential, HSN::PTX (Go off) | -14.75 | mV | Ravi 2021 Fig 5B | yes | measured |
| HSN resting potential, goa-1(n1134) | -17.9 | mV | Ravi 2021 Fig 5B | yes | measured |
| HSN resting potential, egl-10(md176) | -40.8 | mV | Ravi 2021 Fig 5B | yes | measured |
| HSN Ca2+ transient freq, WT | ~0.4 | transients/min | Ravi 2021 Fig 3C | yes | measured |
| HSN Ca2+ transient freq, HSN::PTX | ~1.9 | transients/min | Ravi 2021 Fig 3C | yes | measured |
| HSN intertransient interval, inactive (L4.7-8) | ~34 | s | Ravi 2018 PMC6041790 Fig 2D | yes | measured |
| HSN intertransient interval, active/burst | <20 | s | Ravi 2018 Fig 2D | yes | measured |
| HSN/VC Ca spike period, low osmolarity | 6-12 | s | Zhang 2008 PMC2621019 Fig 3B,C | yes | measured, perturbed condition |
| Ca transient lead before egg-laying event | ~1 | s | Zhang 2008 Fig 2 | yes | measured |
| tyramine EC50 at LGC-55 (oocyte, not HSN) | 12.1 +/- 1.2 | uM | Pirri 2009 PMC2804440 Fig 3B | yes | measured (heterologous) |
| LGC-55 max current (oocyte) | 2.2 +/- 0.17 | uA | Pirri 2009 Fig 3B | yes | measured (heterologous) |
| egl-6 HSN egg-laying suppression by irk-1(-) | p=1.3e-15 | - | Emtage 2012 PMC3544400 Table 1 | yes | measured (behavioral) |
| HSN input resistance / capacitance | not found anywhere | - | - | searched | n/a |
| HSN kcnl-1 expression | 1080.7 | avg TPM, thr2-4 | CeNGEN csv, cengen.org | yes (data file) | measured |
| HSN cca-1 expression | 1067.0 (thr2/3), 0 (thr4) | avg TPM | CeNGEN csv | yes | measured |
| HSN unc-103 expression | 47.3 (thr2/3), 0 (thr4) | avg TPM | CeNGEN csv | yes | measured |
| HSN egl-19 expression | 198.8 | avg TPM | CeNGEN csv | yes | measured |
| HSN nca-1 expression | absent from dataset | - | CeNGEN csv | yes | n/a (gene not profiled) |
| c302 / BAAIWorm HSN-specific parameter set | none found | - | c302 repo, Zhao 2024 PMC11659166 | yes | n/a |
