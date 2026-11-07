# Independent audit of the worm parameter catalog

Date: 7 Nov 2026
Auditor: independent (did not build the catalog)

Method: loaded `docs/worm/ledger.json`, key `parameters` (1,206 rows after the per-pair
connectome/structure blocks, `kind == "structure"`, 8 rows, were excluded from the
sampling pool as instructed). Drew a stratified random sample in Python
(`random.seed(7)`, `random.sample` per label group) of 50 rows: 15 measured, 10
published_fit, 8 derived, 7 inferred, 10 guessed. All target counts were available in
the pool. For each row the cited source was opened where free full text exists (PMC,
bioRxiv, eLife, PLoS, GitHub, lab/database pages); paywalled or unreachable sources are
marked UNVERIFIABLE. No simulations were run, no files other than this one were edited,
no git commands were run.

Note found during the audit: most sampled rows already carry an internal note stamped
"fill 6 Nov (catalog audit)" or similar, meaning the catalog authors ran their own
correction pass on 6 Nov 2026, the day before this audit. This independent pass treats
those notes as claims to verify, not as given fact.

## Summary table

| Label | OK | MINOR | WRONG | UNVERIFIABLE | Total checked |
|---|---|---|---|---|---|
| measured | 15 | 0 | 0 | 0 | 15 |
| published_fit | 7 | 0 | 0 | 3 | 10 |
| derived | 6 | 0 | 1 | 1 | 8 |
| inferred | 5 | 1 | 1 | 0 | 7 |
| guessed | 9 | 1 | 0 | 0 | 10 |
| **Total** | **42** | **2** | **2** | **4** | **50** |

## Row-by-row results

Big finding up front: the main peptide-GPCR EC50 source (Beets et al. 2023 Cell Rep,
cited for 9 of the 15 measured rows here) could not be fully checked from the PMC
article text alone, because its Table S6 is a bound Excel file, not inline text. The
file was recovered directly from the bioRxiv preprint's supplementary materials
(`2022.10.30.514428`, media file for Table S6) and opened with Python/openpyxl. Every
one of the 9 sampled peptide rows matched the spreadsheet's EC50 and its 95% CI to
4 significant figures. This is the strongest check in the whole audit: real primary
numbers, not just a citation that exists.

| param_id | label | value | unit | source | verdict | evidence |
|---|---|---|---|---|---|---|
| pep_ec50_flp-2_dmsr-1_nM | measured | 3094.0 | nM | Beets 2023 Table S6 | OK | bioRxiv media-6.xlsx row DMSR-1-2/FLP-2-2: EC50 3094.0 nM, 95% CI 2552-3750 nM, exact match to value and bounds |
| pep_ec50_flp-1_npr-22_nM | measured | 569.0 | nM | Beets 2023 Table S6 | OK | Table S6 NPR-22-1 rows: FLP-1-9 = 569.0 nM (most potent of 2), CI gives bio_min 510.5, weaker peptide FLP-1-8 = 835.3 = bio_max; exact match |
| pep_ec50_flp-25_frpr-8_nM | measured | 0.0001315 | nM | Beets 2023 Table S6 | OK | Table S6 FRPR-8-1/FLP-25-2: EC50 1.315e-13 M = 0.0001315 nM, CI gives bio_min 3.09e-05, bio_max 0.0005495; exact match |
| pep_ec50_nlp-40_aex-2_nM | measured | 7.645 | nM | Beets 2023 Table S6 | OK | Table S6 AEX-2-1/NLP-40-2: EC50 7.645e-9 M, CI gives bio_min 5.728, bio_max 10.21; exact match |
| rec_lacr_erev_mV | measured | 11.0 | mV | Richmond & Jorgensen 1999 Nat Neurosci, PMC2585773 | OK | Paper: "reversal potential...+11 mV...(n=4; Fig. 4c)" - exact match |
| rec_glucl_ec50_uM | measured | 208.0 | uM | Cys-loop review, PMC10480131 Table 1 | OK | Table 1 lists "AVR-15B: glutamate EC50 208 uM" exactly; bio_min 62 = AVR-15B/GLC-2, bio_max 10000 = AVR-14B (10 mM), both confirmed in the same table |
| egg_uterus_init | measured | 15.0 | eggs | Wang, Gao & Pocock 2026, PMC13054943 | OK | Paper: "Young adult hermaphrodites typically retain ~15 fertilised eggs" - exact match; independently cross-confirmed by Ravi et al. 2018 J Neurosci abstract ("maintain ~12-15 eggs in the uterus") |
| pep_ec50_flp-8_dmsr-7_nM | measured | 517.9 | nM | Beets 2023 Table S6 | OK | Table S6 DMSR-7-1/FLP-8-2 = 517.9 nM (most potent of 2), CI gives bio_min 428.5; weaker FLP-8-1 = 735.9 = bio_max; exact match |
| rec_mod1_ec50_uM | measured | 0.96 | uM | Rodriguez Araujo et al. 2022 JBC, PMC9471462 | OK | Paper: "EC50 for 5-HT was 0.96 +/- 0.40 uM", whole-cell MOD-1 in BOSC-23 cells at -50 mV - exact match |
| pep_ec50_flp-22_dmsr-7_nM | measured | 1032.0 | nM | Beets 2023 Table S6 | OK | Table S6 DMSR-7-1/FLP-22-1 = 1032.0 nM (only entry), CI gives bio_min 941.9, bio_max 1130; exact match |
| pep_ec50_nlp-10_npr-35_nM | measured | 297.7 | nM | Beets 2023 Table S6 | OK | Table S6 NPR-35-1 has 4 NLP-10 entries, most potent 297.7 nM, CI gives bio_min 251.2; weakest entry 755.9 = bio_max; exact match |
| rec_acr16_ec50_uM | measured | 31.0 | uM | Boulin et al. 2008 PNAS, PMC2587545 | OK | Paper: "31 +/- 0.5 uM (n=6)...Hill coefficient...2.4" for N-AChR (ACR-16+RIC-3) in oocytes - exact match |
| pep_ec50_flp-5_egl-6_nM | measured | 268.7 | nM | Beets 2023 Table S6 | OK | Table S6 EGL-6 isoforms have 6 FLP-5 entries total, most potent 268.7 nM (EGL-6-2/FLP-5-1), CI gives bio_min 213.3; weakest entry 3788 = bio_max; exact match |
| pep_ec50_flp-13_frpr-4_nM | measured | 753.9 | nM | Beets 2023 Table S6 | OK | Table S6 FRPR-4-1 has 7 FLP-13 entries, most potent 753.9 nM, CI gives bio_min 587.5; weakest entry 1632 = bio_max; exact match |
| gcamp_hill | measured | 2.9 | 1 | Chen et al. 2013 Nature, PMC3777791 Supp Table 2 | OK | Independently confirmed via search of Supp Table 2: GCaMP6s Hill coefficient 2.90 +/- 0.17; bio_min/max 2.73-3.07 = mean +/- SD exactly |
| kin_egl19_vhhb | published_fit | -20.5 | mV | BAAIWorm egl19.mod (GitHub) | OK | Fetched raw file: "vhhb = -20.5 (mV)" - exact match |
| build_syn_mu | published_fit | 0.44 | 1 | BAAIWorm config.json (GitHub) | OK | Fetched raw file: cnt_info.syn_mu = 0.44 - exact match |
| syn_inh_erev | published_fit | -70.0 | mV | BAAIWorm (GitHub, general) | UNVERIFIABLE | Could not locate the exact file/line in the BAAIWorm repo setting -70 mV for inhibitory synapses within the time budget; the bound_source literature (Bamber 1999/2005) is a plausible, standard GABA Erev for C. elegans muscle, and -70 mV is a reasonable published_fit value, but the BAAIWorm code citation itself is unconfirmed |
| kin_cca1_dtm | published_fit | 0.7 | ms | BAAIWorm cca1.mod (GitHub) | OK | Fetched raw file: "dtm = 0.7 (ms)" - exact match |
| kin_shk1_vhm | published_fit | 20.4 | mV | BAAIWorm shk1.mod (GitHub) | OK | Fetched raw file: "vhm = 20.4 (mV)" - exact match |
| kin_egl19_ahinf | published_fit | 1.43 | 1 | BAAIWorm egl19.mod (GitHub) | OK | Fetched raw file: "ahinf = 1.43" - exact match |
| awa_liu_gK3 | published_fit | 0.1 | nS | Liu et al. 2018 Cell / bioRxiv 359935 | UNVERIFIABLE | Confirmed this is the right paper (AWA calcium action potentials, Table S4 WT fits) but could not retrieve the actual Table S4 gK3 value from free text/supplement within the time budget |
| syn_weight_mn | published_fit | 0.1 | 1 | BAAIWorm transform.py (GitHub) | OK | Fetched raw file: muscle-to-neuron connection weight literal 0.1 in `add_connection(...,'syn', 0.1)` - exact match |
| kin_cca1_vhh | published_fit | -58.0 | mV | BAAIWorm cca1.mod (GitHub) | OK | Fetched raw file: "vhh = -58.0 (mV)" - exact match |
| bwm_du_ca0_mM | published_fit | 0.001 | mM | Du, Crodelle et al. 2025 PLOS Comp Biol, PMC11781704 | UNVERIFIABLE | Confirmed right paper and that it defines a resting calcium concentration term ([Ca2+]r) in its equations, but the numeric value (0.001 mM) sits in a supplementary parameter table/PDF that could not be opened in the time budget |
| other_area_hyp_um2 | derived | 160000.0 | um2 | derived from Sanzeni 2019 eLife (r) + WormAtlas (L) | OK | Sanzeni 2019 (PMC6692131) confirms adult radius ~25 um; 2*pi*25*1000 = 157,080 um2, matching the ~1.6e5 template (catalog's own note shows the arithmetic) |
| proprio_field_frac | derived | 0.2 | body length | Wen et al. 2012 Neuron, PMC3508473 | OK | Paper: "spatial extent of this coupling l to be ~200 um" over a 1 mm worm = 0.2 body lengths - exact match |
| slow_thermo_tau_h | derived | 3.5 | h | Yu et al. 2014 Neuron, PMC4258139 | OK | Paper: downshift "time constant of ~3 hours", upshift "~3-5 hours (tau2)"; 3.5 h sits between them as claimed, range [3,5] confirmed |
| pump_rt_f_mV | derived | 25.26 | mV | R, F physical constants (NIST) | OK | Recomputed independently: 8.314462618 x 293.15 / 96485.33212 = 25.2617 mV, matches template to 4 sig figs |
| deb_t_ref_K | derived | 293.15 | K | AddMyPet DEB database | OK | Page confirms "Pseudo-data at Tref = 20 C" = 293.15 K exactly |
| obs_gcamp6f_thalf_ms | derived | 176.0 | ms | Chen et al. 2013 Nature Supp Table 2 | OK | Independently found: GCaMP6f koff = 3.93/s (tau_off = 254 ms); half-time = ln(2) x 254 ms = 176 ms, matches template exactly |
| gap_innexin_pair | derived | 1.0 | flag | CeNGEN / Taylor et al. 2021 Cell | UNVERIFIABLE | Confirmed this is the right paper (CeNGEN gene expression atlas, covers innexins); could not independently re-derive the exact count (1091 pairs, 7 without a detected innexin) from the raw CeNGEN dataset within the time budget |
| pump_v0_ms | derived | 1000.0 | ms | "this model" (no citation) | WRONG | Labelled "derived" (per CATALOG.md: "arithmetic on measured values, shown") but the row cites no measurement and shows no arithmetic - it is a free modelling choice of an averaging window, which is what the catalog's own rubric calls "guessed." Mislabelled. |
| harsh_pvd_s0 | inferred | 0.25 | body length | Albeg et al. 2011, PMC3018541 | MINOR | Paper confirms PVD branches "envelop the entire body...a network that does not cover the head region" but gives no numeric fraction; the inferred label is fine, but bound_basis "measured_related" slightly overstates how directly 0.25 ties to the paper (no number is in the source) |
| homeo_unc2_tau_h | inferred | 3.0 | h | PNAS 2024, PMC11363341 | OK | Paper confirms "1 h...not sufficient to impact UNC-2 levels" and "sessions exceeding 2 h led to a decrease" - matches the catalog's paraphrase |
| dmp_exp_delay_s | inferred | 4.0 | s | Wang & Sieburth 2013 PLoS Genet, PMC3784516 | OK | Paper: "fluorescent spikes in DVB axons began about 3 seconds following the pBoc step, reached maximal intensity about 1 second later" - exact match |
| rec_nmr_tau_rise_ms | inferred | 5.0 | ms | vertebrate NMDA receptor kinetics (no worm source) | OK | No C. elegans source exists for this; cross-species inference from vertebrate NMDAR rise times (~5-10 ms) is accurate general pharmacology and is honestly labelled as a cross-species inference, not measured |
| pump_rate_nofood_hz | inferred | 0.3 | Hz | Avery & Horvitz 1990 / Raizen & Avery 1994, PMC4460247 | WRONG | Fetched PMC4460247 (Raizen & Avery 1994) directly: it does not report any specific off-food pumping rate figure anywhere in the text. A separate search found that acute food removal cuts pumping by only about 50% (i.e., roughly 2 Hz if fed rate is ~4 Hz), not down to 0.3 Hz; the cited free source does not support the value, and the actual magnitude is questionable |
| touch_probe_radius_um | inferred | 10.0 | um | Sanzeni et al. 2019 eLife, PMC6692131 | OK | Paper: "10 um glass beads (Duke Scientific) for indenting the worms" - exact match; "inferred" rather than "measured" is a reasonably conservative choice since the parameter generalizes beyond the one bead experiment |
| obs_neuropal_p_correct | inferred | 0.9 | 1 | Yemini et al. 2021 Cell, PMC10494711 | OK | Paper: "Semi-automated neuronal identification accuracy begins at 86% for the head...Manually identifying eight neurons raises the head accuracy above 90%" - matches value and range [0.7, 0.99] |
| homeo_gain_pA_per_mV | guessed | 0.5 | pA/mV | none (model-internal) | OK | No citation claimed; free parameter in src/wormemu/brain_layers.py; order of magnitude is plausible for a homeostatic feedback gain and nothing better is in free literature |
| daf16_tau_h | guessed | 1.0 | h | general DAF-16 biology (no specific citation) | OK | DAF-16/FOXO nuclear entry under starvation in C. elegans is documented to occur over minutes to a few hours in the literature; 1 h within range [0.25, 6] is plausible |
| sens_awc_but_ref_uM | guessed | 1100.0 | uM | 1e-4 dilution of neat 2-butanone | OK | Arithmetic check: 11 M x 1e-4 = 1.1 mM = 1100 uM, correct; this matches standard odorant dilutions used in C. elegans chemotaxis assays |
| rec_acr16_tau_rise_ms | guessed | 0.5 | ms | general ligand-gated channel kinetics | OK | Sub-ms to low-ms rise times are typical for fast ionotropic receptors; plausible and honestly labelled guessed/unverified |
| aex2_ec50_nM | guessed | 10.0 | nM | Wang et al. 2013 Curr Biol | OK | Confirmed this is the right paper ("Neuropeptide Secreted from a Pacemaker Activates Neurons to Control a Rhythmic Behavior," NLP-40/AEX-2 on AVL/DVB); catalog honestly notes "full text not opened"; 10 nM is plausible given the Beets 2023 data shows peptide-GPCR EC50s commonly in the 1-3000 nM range |
| dmp_pboc_amp | guessed | 0.5 | activation | none (model-internal) | OK | Internal model constant with no claimed literature basis; plausible mid-range guess for an activation amplitude bounded [0,1] |
| egg_ret_gain_pA | guessed | 10.0 | pA | Ravi et al. 2018 J Neurosci | OK | Confirmed this is the right paper (Ravi, Garcia & Collins 2018, HSN retrograde feedback from vulval muscle); paper supports the qualitative mechanism (retrograde signal sustains HSN activity) but gives no current magnitude in pA, so "sign measured, size guessed" in the notes is an accurate characterization |
| assoc_salt_forget_tau_min | guessed | 60.0 | min | general associative learning biology | MINOR | 60 min is plausible for salt-aversion memory decay, but the range upper bound (2880 min = 48 h) contradicts the row's own notes, which say salt/thermotaxis memories fade "within hours" while only pathogen-avoidance memory "lasts longer"; the bound creeps into the territory the notes say it should exclude |
| egg_5ht_g_nS | guessed | 1.0 | nS | Carnell 2005; Hobson 2006 | OK | Both are real, correctly-themed C. elegans papers on SER-1/SER-7 serotonin receptors in vulval/uterine muscle; 1 nS (range [0.1,3]) is a plausible whole-cell conductance order of magnitude, consistent with other channel conductances elsewhere in the catalog |
| rec_glucl_tau_off_ms | guessed | 10.0 | ms | none ("not retrieved") | OK | Catalog honestly flags this as a sourcing gap; 10 ms deactivation time is plausible for a Cys-loop ligand-gated chloride channel |

## Error rate by label

- measured: 0 / 15 wrong or minor (0%). All 15 checked out, and 9 of them (the peptide-GPCR
  EC50s) were matched to 4 significant figures against the actual primary-source
  spreadsheet, not just a citation check.
- published_fit: 0 / 10 wrong, 3 / 10 (30%) unverifiable (BAAIWorm repo cross-reference for
  syn_inh_erev, and two supplementary tables - Liu 2018 Table S4, Du 2025 parameter
  table - that free-text tools could not open in the time available). No evidence
  any of the three are actually wrong, just not confirmed.
- derived: 1 / 8 wrong (12.5%, pump_v0_ms mislabelled), 1 / 8 unverifiable
  (gap_innexin_pair's exact count). The other 6 were all confirmed, several by
  independently redoing the arithmetic.
- inferred: 1 / 7 wrong (14%, pump_rate_nofood_hz - citation does not support the
  value), 1 / 7 minor (14%, harsh_pvd_s0 - bound_basis overstates source support).
  Combined error rate 2/7 = 29%, the worst-performing label in this sample.
- guessed: 1 / 10 minor (10%, assoc_salt_forget_tau_min's range inconsistency), the
  rest plausible and honestly flagged where a source gap exists. No guessed row
  claimed more support than it had.

## The 5 most important problems

1. **pump_rate_nofood_hz (inferred, WRONG).** The cited free source (Raizen & Avery
   1994, PMC4460247) does not contain any off-food pumping rate figure anywhere in
   its text - confirmed by direct fetch. A separate literature check found that
   acute food removal cuts pumping by only about 50% (not down to the 0.3 Hz / 18 per
   minute implied here), so the citation does not support the value and the value
   itself may be too low for the condition described. The real Avery & Horvitz 1990
   number (behind a Wiley paywall) should be tracked down and the citation fixed to
   point at whichever paper and figure actually state the rate.

2. **pump_v0_ms labelled "derived" with no arithmetic and no citation.** It is a
   free modelling choice (an averaging window for resting voltage), which fits the
   catalog's own definition of "guessed," not "derived." This is a one-row finding
   in the sample, but it signals the "derived" label is being used loosely in at
   least some rows for "this model decided," not "arithmetic on measured values."

3. **A likely systematic row-vs-element label mismatch (found outside the formal
   sample, flagged here because it looks structural).** While reading `ledger.json`
   to build the sample, `pas_soma_cm` (passive membrane capacitance) was inspected:
   its row-level label is `published_fit`, but `element_stats.by_label` shows all
   302 per-cell values are internally `guessed` (every one of the 302 BAAIWorm-ported
   values fell outside the literature bound and was clipped to it - the notes say so
   directly: "302 of 302 ported values outside the literature range, clipped"). The
   median/min/max shown (1.5, 1.5, 1.5) is the guessed upper bound, not a published
   fit. The row-level label overstates confidence for every element in that row.
   Since clipping-to-bound is a general mechanism in this catalog (442 guessed rows,
   many rows show "before/after fill" changes), the catalog should audit whether
   other rows have this same row-label/element-label mismatch after clipping.

4. **Three published_fit rows (syn_inh_erev, awa_liu_gK3, bwm_du_ca0_mM) could not be
   pinned to an exact line/number for free in this session.** Not proven wrong -
   the papers and repos are correctly identified and topically right - but someone
   with direct repo access or paywalled-PDF access should confirm the BAAIWorm code
   line for syn_inh_erev and the actual table values for the other two, since right
   now they rest on the catalog's own unverified say-so.

5. **assoc_salt_forget_tau_min's range contradicts its own stated reasoning.** The
   row's note explains the range should separate fast salt/thermotaxis forgetting
   (hours) from slower pathogen-avoidance memory (longer), but the upper bound
   (2880 min = 48 h) sits inside the "longer" territory the note says the range
   should exclude. Minor on its own, but worth a sanity pass on bound construction
   for the other guessed memory/timescale rows.

## Positive finding worth noting

The audit recovered the actual primary data file behind the catalog's single
most-cited peptide pharmacology source (Beets et al. 2023, bioRxiv Table S6,
459 peptide-GPCR pairs) and checked all 9 sampled peptide EC50 rows against it
directly. Every value and every derived bound (lowest 95% CI to the larger of the
upper CI or the weakest peptide's EC50) matched to 4 significant figures. This is
good evidence that the "most potent peptide, CI-based range" construction method
used throughout the neuropeptide mechanism is implemented correctly, at least for
this sample.
