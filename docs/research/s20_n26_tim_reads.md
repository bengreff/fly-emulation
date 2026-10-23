# N26 TIM/CRY protein reads: light-driven degradation, dark turnover, recovery

Scope: what could actually be pulled from open-access full text (PMC / Europe PMC) for TIM (and CRY)
protein degradation kinetics. Most of the foundational 1996-1999 papers on this list are **not**
open access anywhere I could check (no PMC record, Europe PMC `isOpenAccess: N` for every PMID
checked) — see "What I could NOT get" at the end. Lamba et al. 2014 was not opened (not searched,
not fetched), per the hard rule.

Figures saved under `docs/research/figs/s20_n26_tim/`. Cached PMC HTML saved under
`data/raw/papers/koh2006_pmc.html` and `data/raw/papers/lin2001_pmc.html` (no PDFs were obtainable —
both sources were HTML-only PMC articles, so nothing was saved as PDF).

## Summary table

| Quantity | Value | Units | Source & panel | Conditions | Label |
|---|---|---|---|---|---|
| TIM ubiquitination onset after light, S2 cells | within 5 | min | Lin et al. 2001 MCB 21:7287, text (Fig. 5A referenced) | S2 cells, hs-*tim*/hs-Ub, bench-top light ~600 lx | measured (stated in text, not independently pixel-checked — Fig. 5 image not fetched) |
| CRY levels unchanged up to | 30 | min of light | Lin et al. 2001, text (Fig. 5B referenced) | same S2-cell experiment as above | measured (stated in text) |
| In-fly TIM degradation after light onset (cited, not primary) | 30–60 | min | Lin et al. 2001, text, citing ref. "(15)" (their numbering; likely Hunter-Ensor 1996 or Myers 1996 — original not opened, see below) | stated as general fly in-vivo fact, no further detail given in Lin 2001 | measured, secondhand (Lin 2001's citation of an inaccessible primary source — do not treat as independently verified) |
| CRY/MAPK ratio, S2 cells, dark, pIZ-*cry* transfected | ≈0.38 | ratio (arbitrary densitometry units) | Lin et al. 2001 Fig. 1A, pixel/visual read of bar chart | S2 cells, 40 h post-transfection, then 5 h **dark** | measured, pixel read (visual estimate against y-axis ticks 0/0.2/0.4/0.6/0.8; no MG115) |
| CRY/MAPK ratio, S2 cells, light, pIZ-*cry* transfected | ≈0.08 | ratio | Lin et al. 2001 Fig. 1A | S2 cells, 5 h **light**, ~600 lx bench-top, no inhibitor | measured, pixel read (same calibration) |
| CRY/MAPK ratio, light + MG115 (proteasome inhibitor) | ≈0.45 (large error bar, up to ≈0.6) | ratio | Lin et al. 2001 Fig. 1A | S2 cells, 5 h light, 20 µM MG115 | measured, pixel read |
| CRY/MAPK ratio, dark + MG115 | ≈0.78 | ratio | Lin et al. 2001 Fig. 1A | S2 cells, 5 h dark, 20 µM MG115 | measured, pixel read |
| CRY(L)/CRY(D) ratio, 2 h light pulse (wild-type CRY) | light ≈0.55–0.6 vs dark normalised to 1.0 | ROD, normalized | Lin et al. 2001 Fig. 2B ("CRY" group, n=6) | S2 cells, 2 h light pulse, ~600 lx, dark control = 1.0 by definition | measured, pixel read (y-axis ticks 0/0.5/1.0/1.5/2.0) |
| Same, CRY-N truncation mutant | dark ≈0.35, light ≈0.35 (no change) | ROD | Lin et al. 2001 Fig. 2B (n=4) | same | measured, pixel read |
| Same, CRY-C truncation mutant | dark ≈1.15, light ≈1.05 (no change) | ROD | Lin et al. 2001 Fig. 2B (n=4) | same | measured, pixel read |
| Same, CRY^b point mutant (flavin-binding site) | dark ≈0.6, light ≈0.65 (no change) | ROD | Lin et al. 2001 Fig. 2B (n=3) | same | measured, pixel read |
| Light intensity used for all Lin 2001 S2-cell light pulses | ~600 | lux | Lin et al. 2001, Materials and Methods text | "at the bench top" | measured (stated in text) |
| Light pulse durations used (Lin 2001) | 10 min, or 2 h, or 5 h (panel-dependent) | — | Lin et al. 2001, Methods text | S2 cells; 10-min used for TIM-ubiquitination timecourse (Fig. 5/6/7), 5 h for Fig. 1 CRY/proteasome blot, 2 h for Fig. 2B CRY-mutant blot | measured (stated in text) |
| TIM ubiquitination increase window | 10–15 | min of light | Lin et al. 2001, text | S2 cells, high-CRY condition (Fig. 5A/7A context) | measured (stated in text) |
| TIM staining 1 h after a 2-min light pulse at ZT16 (qualitative only) | visibly reduced vs no-LP (quantified in supp. fig. S3, not accessed) | — | Koh, Zheng & Sehgal 2006 Science 312:1809, Fig. 2C legend text | *tim-Gal4* driven imaging, small ventral-LNvs, 2-min light pulse (LP) at ZT16, fixed 1 h later; genotype/temperature/intensity not stated in accessible text | measured (stated in text); **no numeric % remaining obtained** — quantification is in a supplementary figure not accessible from the fetched PMC page |
| TIM ubiquitination increase after light | significant by 10 min | min | Koh et al. 2006 Fig. 3D (S2-cell assay) | S2 cells, pIZ-*jet*/pIZ-*cry* cotransfection system | measured (stated in text) |
| Behavioural phase delay at ZT16 (control, cry-Gal4/tim-Gal4) | ≈ −3.5 to −3.8 h (control-r) and ≈ −3.3 h (control-c) | h, phase shift | Koh et al. 2006 Fig. 1A, pixel read | locomotor activity assay, genotype groups control-r / jetʳ / control-c / jetᶜ | measured, pixel read (y-axis ticks at 0, −1, −2, −3, −4 h); **not a TIM-protein measurement** — included only because it was on the same panel; not otherwise used |

## Source-by-source notes

### Lin, Song, Meyer-Bernstein, Naidoo & Sehgal 2001, Mol Cell Biol 21(21):7287–7294, "Photic Signaling by Cryptochrome in the Drosophila Circadian System"
PMID 11585911, PMCID PMC99903 (open access, ASM journal, full HTML + figure images on PMC).
Saved: `docs/research/figs/s20_n26_tim/lin2001_fig1.jpg`, `lin2001_fig2.jpg`; cached HTML
`data/raw/papers/lin2001_pmc.html`.

This is an S2-cell-culture paper, not whole-fly tissue — flagged explicitly since the task asked
preferentially for fly heads/clock neurons. It is the only accessible primary source with
quantitative CRY light-degradation data, so it is reported (lower priority, as instructed) with the
tissue caveat.

- Light source/intensity: bench-top light, ~600 lx (stated in Methods; no spectral info, no W/cm²
  conversion given — "not stated" for irradiance).
- Fig. 1 (CRY proteasome dependence): pIZ-*cry*-transfected S2 cells, dark 40 h post-transfection,
  then 5 h light or dark ± 20 µM MG115 (panel A) or 20 µM lactacystin (panel B). Pixel/visual read of
  the bar chart against labelled y-axis ticks (0.2 increments, panel A) gives CRY/MAPK ≈0.38 (dark) vs
  ≈0.08 (light) — i.e. light knocks CRY down to roughly a fifth of the dark level after 5 h, and this
  is substantially blocked by MG115 (light+MG115 ≈0.45, large SEM).
- Fig. 2B (mutant CRY): 2-h light pulse, 600 lx. Wild-type CRY drops to ≈0.55–0.6 of its dark level;
  CRY-N, CRY-C and CRY^b mutants show little or no light-dependent drop (pixel-read values in the
  table above). This is the paper's point: light responsiveness needs the intact flavin-binding
  region.
- Text (not a figure number given at that point): "We detected an increase in TIM ubiquitination
  within 5 min of light exposure (Fig. 5A), while CRY levels in the same extracts remained unchanged
  up to the end of a 30-min light pulse (Fig. 5B)." I did not fetch Fig. 5 itself (image URL not
  pulled within budget) so this is reported from text only, not a pixel read.
- Text: "In flies, TIM degradation (which presumably follows ubiquitination) occurs within 30 to 60
  min of light treatment (15) and is apparently critical for resetting the clock." This is Lin et
  al.'s own citation of a third-party in-vivo result (their ref. 15 — the reference list itself was
  not fetched, so I cannot confirm which 1996 paper this points to). Reported here as a secondhand
  pointer only, not as an independently verified fly-tissue measurement.

### Koh, Zheng & Sehgal 2006, Science 312(5781):1809–1812, "JETLAG Resets the Drosophila Circadian Clock by Promoting Light-Induced Degradation of TIMELESS"
PMID 16794082, PMCID PMC2767177 (NIH author manuscript, open access via PMC).
Saved: `docs/research/figs/s20_n26_tim/koh2006_fig1.jpg` (behavioural phase-shift bars, not TIM
protein — included for completeness only), `koh2006_fig2.jpg` (behavioural + immunostaining panels
A–D), `koh2006_fig3.jpg` (S2-cell Western-blot mechanism panels A–F). Cached HTML
`data/raw/papers/koh2006_pmc.html`.

This paper turned out to be mostly behavioural phase-shift genetics plus S2-cell biochemistry, **not**
a quantitative fly-tissue TIM-vs-minutes-of-light time course. What is there:
- Fig. 2C/D: anti-TIM immunostaining of small ventral-LNvs, "no LP" vs "LP" (2-min light pulse at
  ZT16, fixed 1 h later), compared across *jetᶜ* and rescue genotypes. The images show a qualitative
  drop in TIM signal with the light pulse in control and in partially-rescued genotypes, but the
  actual quantification is stated to be in "fig. S3" (supplementary), which I did not fetch, so no
  numeric % TIM remaining is reported here — correctly labelled "not stated" rather than guessed from
  the raw fluorescence image.
- Fig. 3 (A–F): all S2-cell Western blots (TIM, CRY, JET, ubiquitin, MAPK loading control) under
  single dark/light timepoints with pIZ-*jet*/pIZ-*cry* transfections — mechanistic (JET as the E3
  ligase adaptor for CRY-dependent TIM ubiquitination/degradation), not a time-course and not fly
  tissue. Text states ubiquitination increase is "significant ... after only 10 min of exposure to
  light" (referencing Fig. 3D), consistent with but not adding to the Lin 2001 S2-cell number above.
  Light intensity/temperature for this exposure are not stated in the accessible text.
- Fig. 1 (A, B): locomotor phase-shift magnitudes (delay at ZT16, advance at ZT21) across *jet*
  mutant/rescue genotypes — behavioural, not TIM protein; pixel-read only for completeness, not used
  for anything in this report beyond confirming figure content.

## What I could NOT get, and why

All of the following were searched via PubMed (NCBI eutils `esearch`), and each PMID was checked both
via NCBI `elink` (`pubmed_pmc`, direct link to a PMC copy of the article itself — came back empty for
every one of these) and via the Europe PMC REST API (`isOpenAccess` came back `N` for every one).
None has an open-access full text I could legally read; I did not attempt to bypass paywalls (e.g. no
Sci-Hub, no non-PMC mirrors beyond a direct publisher page, which I did not fetch since it would be
paywalled per the task's own guidance).

- **Zeng, Qian, Myers & Rosbash 1996, Nature 380:129** — not found in PubMed search with the terms
  tried (no PMID resolved); not pursued further; Nature did not have an open PMC deposit from this
  era. **Could not get TIM daily DD/LD profile from this source.**
- **Hunter-Ensor, Ousley & Sehgal 1996, Cell 84:677** (PMID 8625406) — PMC link empty, Europe PMC not
  open access. **Could not get the light-driven degradation time course or ZT15 vs ZT21 recovery data
  this paper is best known for.**
- **Myers, Wager-Smith, Rothenfluh-Hilfiker & Young 1996, Science 271:1736** (PMID 8596937) — PMC
  link empty, not open access. **Could not get TIM degradation time course.**
- **Lee, Parikh, Itsukaichi, Bae & Edery 1996, Science 271:1740** (PMID 8596938) — PMC link empty, not
  open access. **Could not get TIM/PER data.**
- **Sehgal et al. 1995, Science 270:808** — not searched (budget; also pre-dates PMC entirely, very
  unlikely to be open).
- **Suri, Qian, Hall & Rosbash 1998, Neuron 21:225** (PMID 9697866) — PMC link empty, not open access.
  **Could not get the ZT15-recovers-in-hours vs ZT21-doesn't-recover comparison asked for in Task 3,
  or the brief-pulse-then-dark continued-decline data in Task 2.**
- **Yang, Emerson, Su & Sehgal 1998, Neuron 21:215** — not searched (budget).
- **Naidoo, Song, Hunter-Ensor & Sehgal 1999, Science 285:1737** (PMID 10481010) — PMC link empty, not
  open access. **Could not get proteasome/degradation kinetics.**
- **Peschel, Chen, Szabo & Stanewsky 2009, Curr Biol 19:241** (PMID 19185492) — PMC link empty (even
  though post-dates the NIH public-access mandate), Europe PMC not open access either. **Could not get
  the phase-dependent CRY-TIM degradation kinetics this paper reports.**
- **Busza, Emery-Le, Rosbash & Emery 2004, Science 304:1503** (PMID 15178801) — PMC link empty, not
  open access. **Could not get CRY-dependent TIM sequestration kinetics.**

Net result: Task 1 (TIM daily DD/LD profile), Task 3 (ZT15 vs ZT21 recovery in hours) and Task 4 (TIM
dark half-life / cycloheximide chase) are **entirely unmet** — no accessible source had this data.
Task 2 (light-driven degradation time course) is **partially met** only via the secondhand Lin 2001
text pointer ("30 to 60 min" in flies, uncited original) and the S2-cell (not fly tissue) numbers
above; no fly-tissue dose/time curve with intensity was obtained. Task 5 (CRY light degradation) is
the best-covered, via Lin et al. 2001 Fig. 1 and Fig. 2B, but those are S2 cells, not heads/LNvs, and
report single timepoints (2 h, 5 h) rather than a full time course.

I did not fetch Lin 2001 Fig. 5/6/7 (the actual TIM-ubiquitination-vs-minutes time-course figures
referenced in the text above) — ran out of call budget. If more read-out is wanted, that figure (plus
its reference list to identify ref. "(15)") would be the next thing to pull from PMC99903.

## Round 2

Scope: found three strong open-access, whole-fly-tissue sources that Round 1 missed or marked
inaccessible — Vinayak et al. 2013 (PLoS Genetics, inherently open), and, unexpectedly, Tang et al.
2010 (Neuron) and Shafer et al. 2002 (J Neurosci), both of which show `isOpenAccess: N` in the Europe
PMC metadata but **do** have a fully readable PMC mirror (PMC3024912, PMC6757919) — the license flag
evidently governs re-use/text-mining rights, not read access; full text was read directly from
`pmc.ncbi.nlm.nih.gov`, not from any publisher paywall. Lamba et al. 2014 and `docs/research/sealed/`
were not opened, searched for, or referenced, per the hard rule.

Numbers below marked "measured (text)" were read from the article's Results/Methods/Figure-legend
text or verified by direct grep against the stripped PMC HTML (quoted). I did **not** pixel-read any
figure image this round (no axis calibration done) — five figure JPEGs were downloaded for the record
(see below) but not visually analyzed against their axes, so no "pixel read" rows appear in this
round's table. Cached PMC HTML saved to `data/raw/papers/tang2010_pmc.html` and
`data/raw/papers/shafer2002_pmc.html`. Figure images saved (un-analyzed) to
`docs/research/figs/s20_n26_tim/`: `tang2010_fig1.jpg`, `tang2010_fig5.jpg`, `shafer2002_fig2.jpg`,
`shafer2002_fig3.jpg`, `shafer2002_fig6.jpg`.

### Summary table

| Quantity | Value | Units | Source & panel | Conditions | Label |
|---|---|---|---|---|---|
| TIM immunofluorescence drop, all neuron classes vs no-pulse control | ≥60% degradation in all four light conditions; overall effect P=1×10⁻¹³ | % IR reduction | Vinayak et al. 2013 PLoS Genet 9:e1003615, Fig. 6A–D, text | *w1118*, whole-mount brain, s-LNv/5th-s-LNv/l-LNv/LNd, n=11 brains (1 hemisphere/brain measured) | measured (text) |
| Light condition set used for Fig. 6 | no-pulse control; 600 nW/cm² × 10 min; 50 nW/cm² × 120 min (equal photon dose to the 600/10 condition); 7000 nW/cm² × 10 min (saturating) | nW/cm², min | Vinayak et al. 2013, Fig. 6 legend + Methods | same as above | measured (text) |
| Core-cluster (s-LNv, 5th s-LNv, LNd) vs l-LNv degradation difference | significant, F(1,84)=11, P=0.001 (core clusters more degraded) | — | Vinayak et al. 2013, Results text | same | measured (text) |
| 5th s-LNv visibility, no-pulse vs 50 nW/cm²×120 min | 10/11 clusters (no pulse) vs 1/11 clusters (long dim pulse) | count of 11 | Vinayak et al. 2013, Results text | same | measured (text) |
| Behavioural phase advance, 10-min pulse at 600 nW/cm² | significant (threshold intensity) | h | Vinayak et al. 2013, Fig. 2 / Results text | locomotor assay | measured (text) |
| Behavioural phase advance, 10-min pulse at 7000 nW/cm² (saturating) | 2.4 | h | Vinayak et al. 2013, Results text | locomotor assay | measured (text) |
| TIM staining after 10-min saturating light pulse at ZT15, then 1 h dark, s-LNv/l-LNv | no detectable loss ("no detectable change in TIM staining intensity") | — | Tang et al. 2010 Neuron 66:378, Fig. 1A/1C/1E, text | Canton-S, whole-mount brain, PDF+ LNvs | measured (text) |
| TIM staining after same pulse, DN + LNd population | "undetectable in almost all" dorsal clock neurons and LNds | — | Tang et al. 2010, Fig. 1A/1C, text | same pulse, ZT15 | measured (text) |
| TIM staining after 10-min saturating light pulse at ZT21, LNvs | ~half of LNvs lose TIM ("approximately half of the LNvs also disappear") | — | Tang et al. 2010, Fig. 1B/1D, text | ZT21 = advance zone; TIM baseline at ZT21 is higher than at ZT15 | measured (text) |
| TIM staining in s-LNvs, 10-min ZT15 pulse + 3 h dark before fixation | "no detectable change" vs no-pulse control | — | Tang et al. 2010, Fig. S4 (legend quoted in main text) | Canton-S, ZT15 | measured (text) |
| DN1 TIM-positive cell count, control (no pulse), ZT15 | >15 (stated as "more than 15") | cells / hemisphere (of ~15 total scored) | Tang et al. 2010, Fig. 5 legend/text | Canton-S | measured (text) |
| DN1 TIM-positive cell count, after 30-min 37°C heat pulse at ZT15 | ~10 of 15 remain positive (≈5 lost) → ~50% described in text as "about 50% of the DNs and LNds" responding to heat | cells / 15 | Tang et al. 2010, Fig. 4B, 5A, text | Canton-S, heat pulse not light | measured (text) |
| DN1 TIM-positive cell count, after "half light pulse" (reduced-intensity 10-min light, calibrated by Western blot to give a 2-h phase shift) at ZT15 | 7–8 of 15 remain positive, in every brain hemisphere ("remarkably constant... 7–8/15") | cells / 15 | Tang et al. 2010, Fig. 4C/4D, Fig. 5C, text (direct quote: "TIM staining always remained prominent in half (7-8) of the 15 DN1s on each side of the brain") | Canton-S, reduced-intensity light, ZT15; 8 hemispheres from 4 brains (heat), 6 brains (half-light) | measured (text), exact quote confirmed by direct grep of PMC full text |
| Phase delay, 10-min saturating light pulse at ZT15 vs 30-min 37°C heat pulse at ZT15 | 4 h (light) vs 2 h (heat) | h | Tang et al. 2010, Results text, citing Edery et al. 1994; Kaushik et al. 2007 | Canton-S | measured (text), secondhand for the heat-pulse number (cites earlier papers) |
| Qualitative TIM daily LD profile (whole-fly circadian neurons, general statement, not Tang's own new data) | decreases rapidly at dawn (ZT0), stays low all day, rises through the evening/night, peaks shortly before dawn | — | Tang et al. 2010, Results text, citing Marrus et al. 1996 and Sehgal et al. 1994 | — | measured, secondhand (citation of inaccessible 1994/1996 papers, not independently verified this round) |
| Nuclear PER disappearance, large vLNs, LD | not complete until after ZT10 | ZT | Shafer, Rosbash & Truman 2002 J Neurosci 22:5946, Fig. 2A/2C, text | Canton-S, large ventrolateral neurons (l-LNv equivalent), 12h:12h LD, 25°C | measured (text) |
| Nuclear TIM disappearance, large vLNs, LD | disappeared by ZT2 | ZT | Shafer et al. 2002, Fig. 2B/2D, text | same | measured (text) |
| TIM reappearance, large vLNs, LD (early night) | detectable by ZT16, stays cytoplasmic through ZT18, starts appearing in nucleus by ZT19, predominantly nuclear by ZT21 | ZT | Shafer et al. 2002, Fig. 3B/3D, text | same | measured (text) |
| PER reappearance, large vLNs, LD (early night) | detectable ~ZT16, uniformly cytoplasmic+nuclear already at first detection, predominantly nuclear by ZT19 | ZT | Shafer et al. 2002, Fig. 3A/3D, text | same | measured (text) |
| TIM reappearance, small vLNs, LD | largely cytoplasmic through ZT20 (PER already nuclear/cytoplasmic at ZT18); phase-lagged 3–4 h vs large vLNs | ZT | Shafer et al. 2002, Fig. 4A/4B, Fig. 5, text | same, small ventrolateral neurons (s-LNv equivalent) | measured (text) |
| Small-vLN TIM "predominantly nuclear" crossover vs large vLN | large vLNs already strongly nuclear by ZT20; small vLNs still cytoplasmic at ZT20 | ZT | Shafer et al. 2002, Fig. 5B, text | same | measured (text) |
| TIM/PER ratio in whole-head extracts (cited, not Shafer's own data) | ≈2:1 at ZT16, ≈1:1 at ZT23 | ratio | Shafer et al. 2002, Discussion text, citing Zeng et al. 1996 | whole head, Western blot (original paper) | measured, secondhand (Zeng et al. 1996 Nature 380:129 not opened — see Round 1 "could not get" list; Shafer's own quote only) |
| TIM reaccumulation, DD, first subjective night, small vLNs | cytoplasmic TIM first appears CT16; nuclear accumulation first detected CT22 | CT | Shafer et al. 2002, Fig. 6B/6D, text, citing Yang & Sehgal 2001 for the CT16/22 landmark | Canton-S, DD + 25°C, entrained 3–5 d LD before release, first circadian day | measured (text) |
| TIM in large vLNs, DD | disappears from nuclei by CT2 (like LD); stays detectable but low in cytoplasm for the rest of the cycle — minimal cycling | CT | Shafer et al. 2002, Fig. 6A/6C, text | same | measured (text) |
| Sample size, DD quantification (Figs. 6–7, both cell types) | 4 brains per timepoint per protein; 3–4 large-or-small vLNs scored per brain | n | Shafer et al. 2002, Fig. 6/7 legends (verbatim) | DD | measured (text, verbatim legend) |
| Sample size, LD quantification (Figs. 2–5) | not stated in the figure legends or body text I could find | n | Shafer et al. 2002 | LD | **not stated** — do not substitute the DD figure's n=4 for the LD figures; an earlier automated pass over this paper guessed "5 brains/4 cells" for Fig. 2D, which I could not confirm by direct text search and have discarded |
| Staining intensity scale | 0–255 (8-bit), mean pixel intensity per cell compartment minus background, averaged per hemisphere, mean±SE plotted per ZT/CT | arbitrary units | Shafer et al. 2002, Methods text (verbatim) | — | measured (text, verbatim method) |

### Source-by-source notes

#### Vinayak, Dasari, Coupar et al. (actual byline: Vinayak P, Coupar J, Hughes SE, Fozdar P, et al.) 2013, PLoS Genetics 9(7):e1003615, "Exquisite Light Sensitivity of Drosophila melanogaster Cryptochrome"
Open access by publisher default (PLoS). Fetched via `journals.plos.org`, not downloaded to
`data/raw/papers/` this round (HTML only, not re-saved — the two WebFetch passes pulled it live; if a
permanent local copy is wanted, that is a follow-up, not done this round, call budget).

This is the best fly-tissue, whole-brain, intensity/duration-resolved TIM-degradation dataset found
across both rounds. Figure 6 (A–D) gives TIM immunofluorescence in four pacemaker-neuron groups
(s-LNv, 5th s-LNv, l-LNv, LNd) across four light conditions designed to separate intensity from total
photon dose: a no-pulse control, a 10-min/600-nW/cm² pulse, a 120-min/50-nW/cm² pulse (same total
photon dose as the 600/10 condition, but longer and dimmer), and a 10-min/7000-nW/cm² saturating
pulse. All three light conditions produced ≥60% TIM loss relative to control (two-way ANOVA,
F(3,160)=104, P=1×10⁻¹³), with the long-dim condition producing *more* degradation than the
short-bright condition of equal photon dose — i.e., duration matters beyond total photons, especially
in the s-LNv/5th-s-LNv/LNd "core" cluster (F(1,84)=11, P=0.001) and most strikingly in the 5th s-LNv,
which nearly vanishes from the stained population after the long-dim pulse (1 of 11 hemispheres vs 10
of 11 in control). Methods state light intensities only in nW/cm² and photons/cm²/s — no lux
conversion given, so "not stated" for lux. Behavioural phase-advance data (Fig. 2) are reported only
for completeness (not a TIM measurement): graded advances starting at 600 nW/cm², saturating at 2.4 h
for the 7000 nW/cm² pulse.

#### Tang, Hinteregger, Shang & Rosbash 2010, Neuron 66(3):378–385
PMID 20471351, PMCID PMC3024912. Europe PMC lists `isOpenAccess: N` but the PMC mirror itself is fully
readable (NIH public-access manuscript, embargo long expired) — read directly, no paywall crossed.
HTML cached `data/raw/papers/tang2010_pmc.html`; Fig. 1 and Fig. 5 images saved (not pixel-analyzed)
to `docs/research/figs/s20_n26_tim/tang2010_fig1.jpg`, `tang2010_fig5.jpg`.

Main claim (quoted): light-mediated TIM degradation *within the s-LNvs themselves* is "not necessary"
for delay-zone (ZT15) phase shifts — a 10-min saturating light pulse at ZT15 produces no detectable
change in s-LNv/l-LNv TIM staining (confirmed even after waiting 3 h in the dark before fixation,
ruling out a fast resynthesis artifact), yet the fly still delays by ~4 h — whereas TIM is essentially
eliminated in that same pulse from the dorsal neurons (DN) and LNds. The paper's interpretation is
that the pacemaker LNvs depend on light input relayed from elsewhere in the clock network (via CRY,
shown necessary in LNvs by RNAi in Fig. S5) rather than on autonomous CRY-dependent TIM degradation.
This directly complicates any "TIM level in s-LNv is the degradation readout for delay-zone light
input" assumption in a model — in this genotype/paradigm, the s-LNv's own TIM is light-insensitive at
ZT15 even though the phase does shift.

By contrast, a ZT21 (advance-zone) pulse causes "a more uniform decrease in TIM staining ... across
all brain circadian neurons," with roughly half the LNvs themselves losing TIM — a clear ZT15-vs-ZT21
asymmetry in LNv TIM light-sensitivity, consistent with (but independent evidence for) Round 1's
already-noted ZT15/ZT21 asymmetry theme.

The paper also gives a titratable intermediate: a reduced-intensity 10-min light pulse (calibrated by
Western blot and behaviour to a 2-h, i.e. half-maximal, phase delay) produces a strikingly
reproducible result in DN1s — exactly 7–8 of the ~15 scored DN1s per hemisphere stay TIM-positive
across every brain and hemisphere tested (8 hemispheres/4 brains for the heat-pulse comparison, 6
brains for the half-light pulse), i.e. almost exactly half the DN1 population is light-sensitive and
half is not, as a fixed, reproducible split rather than a smoothly graded response — this is a
genuinely unusual, quantitative, falsifiable fly-tissue number worth flagging for the model (DN1s as a
population with a bimodal, ~50/50 light-sensitive split, not a uniformly graded one). A 37°C/30-min
heat pulse gives a similar ~50% DN1/LNd TIM loss and a 2-h phase delay — half that of the 4-h light
pulse's delay — supporting the paper's "degradation-summed-across-cells-and-pathways" model of delay
magnitude. No lux/W-per-area units were given for the light pulses (only "saturating" / a
Western-blot-calibrated "half" pulse); genotype for all main figures is Canton-S (one panel repeated
in an unspecified "other genotype," result stated as identical, no further detail extracted).

The qualitative LD TIM profile sentence in this paper's Discussion ("TIM levels decrease rapidly at
dawn... remain low... increase during the end of day... peak shortly before dawn") is itself a
citation of Marrus et al. 1996 and Sehgal et al. 1994 — not new data, and those two sources were not
opened this round (not on this round's target list, and likely to hit the same pre-2000 paywall as
Round 1's list).

#### Shafer, Rosbash & Truman 2002, J Neurosci 22(14):5946–5954, "Sequential Nuclear Accumulation of the Clock Proteins Period and Timeless in the Pacemaker Neurons of Drosophila melanogaster"
PMID 12122057, PMCID PMC6757919. Same open-but-flagged-non-OA situation as Tang 2010 — read directly
from the PMC mirror. HTML cached `data/raw/papers/shafer2002_pmc.html`; Fig. 2, Fig. 3 and Fig. 6
images saved (not pixel-analyzed) to `docs/research/figs/s20_n26_tim/shafer2002_fig{2,3,6}.jpg`.

This is the single best match in either round for Priority Target C (wild-type TIM daily profile,
quantified at several ZT/CT points, immunostaining in LNvs) — though note it is a **qualitative
staging** description (cytoplasmic-only → nuclear-appearing → predominantly-nuclear, keyed to specific
ZT/CT landmarks) rather than a numeric normalized-to-peak curve; the underlying quantification is
plotted as mean±SE pixel intensity (0–255 scale, background-subtracted) in Figs. 2–7, but I did not
read off specific numeric intensity values from those plots (no pixel read done this round — see
figure files saved for follow-up).

Genotype: Canton-S (wild-type), compared against *per01* and *tim01* nulls at one timepoint (ZT0) for
validation, not used further. Conditions: 12h:12h LD, 25°C, for Figs. 2–5; released into DD (still
25°C) after 3–5 d LD entrainment for Figs. 6–7, sampled across the first circadian day (CT0–24).

Key staged landmarks (large vLNs = l-LNv-equivalent cluster; small vLNs = s-LNv-equivalent cluster;
all quoted/paraphrased directly from grep-verified text):
- Large vLNs, LD: nuclear PER present until just after ZT10, nuclear TIM gone by ZT2; both reappear
  ~ZT16, PER already partly nuclear at first detection, TIM stays cytoplasmic until ZT19, both
  predominantly nuclear by ZT21.
- Small vLNs, LD: TIM stays cytoplasmic through ZT20 (3–4 h later than large vLNs); nuclear PER
  present at ZT18 but TIM not predominantly nuclear until after ZT20 (large cells already strongly
  nuclear at that point) — this is the paper's core "sequential, cell-type-staggered nuclear entry"
  finding, not a simple single-phase oscillation.
- DD, first subjective cycle: in *large* vLNs, TIM nuclear signal disappears by CT2 like in LD, then
  stays low with minimal further cycling for the rest of the free-running day — i.e. the large-vLN TIM
  oscillation is reported as largely LD-dependent / damped in DD. In *small* vLNs, TIM reaccumulates
  on a free-running schedule: cytoplasmic signal first at CT16, nuclear accumulation first at CT22
  (citing Yang & Sehgal 2001 for this specific CT landmark, not new to this paper).
- Sample size explicitly stated only for the DD figures (Fig. 6/7 legends, verbatim): "four brains per
  time point per protein and three to four large or small vLNs per brain." I could not find an
  equivalent n statement for the LD figures (2–5) anywhere in the body text or legends I searched —
  flagged as **not stated**, rather than assumed equal to the DD n.
- One useful secondhand number in the Discussion: citing Zeng et al. 1996 (Nature 380:129 — the same
  paper Round 1 could not access), "the TIM/PER ratio is ~2:1 at ZT16 and 1:1 by ZT23" in whole-head
  extracts — reported here only as Shafer et al.'s quotation of it, not independently verified.

### Could NOT get (Round 2)

- **Full numeric pixel-intensity curves for Shafer et al. 2002 Figs. 2–7** — the underlying plots
  exist (mean±SE TIM/PER pixel intensity vs ZT or CT) but were not pixel-read this round; only the
  qualitative staging narrative (ZT/CT crossover points) was extracted from text. Figure JPEGs are
  saved locally for a follow-up pixel-read pass.
- **Lux/irradiance conversion for any of this round's three sources** — all report intensity in
  nW/cm² (Vinayak, Tang) or only as "saturating"/"half" (Tang) or don't discuss intensity at all
  (Shafer, which used no light manipulation, only LD/DD timing). No lux value obtained anywhere this
  round.
- **TIM dark half-life / cycloheximide chase (Priority D)** — not addressed by any of the three
  sources read this round; still entirely unmet across both rounds.
- **ZT15 vs ZT21 TIM *recovery* kinetics in hours (Priority B)** — Tang et al. 2010 shows ZT15 TIM
  staining is *unaffected* by the light pulse in LNvs (so "recovery" doesn't apply there) and gives no
  multi-timepoint recovery curve for the neurons that do lose TIM (DN/LNd at ZT15, or the ~half of
  LNvs at ZT21); the only dark-interval data point is the single "3 h post-pulse, no change" check in
  s-LNvs. No ZT15-vs-ZT21 recovery-time comparison was found.
- **Zeng et al. 1996 Nature 380:129** and **Marrus et al. 1996** — both cited secondhand (by Shafer
  2002 and Tang 2010 respectively) for whole-head TIM/PER ratios and the daily LD profile, but neither
  was itself opened this round (Nature 1996 era, same inaccessibility pattern as Round 1's list; not
  re-attempted here to stay within budget).
- **Yoshii et al. J Neurosci TIM time course, and any Genes Dev/PNAS control-Western TIM time
  course** — not searched this round (budget spent on the three sources above once they turned out to
  be unexpectedly rich); still an open lead for a Round 3.

Budget used this round: ~25 tool calls (web search/fetch for discovery and verification reading;
`curl`/`grep` against the stripped PMC HTML for exact-quote verification of every "measured (text)"
row above, specifically to catch and discard at least one instance where an automated page-summary
invented a sample size — see the discarded Fig. 2D "n" claim, above — rather than trust the summary
tool's paraphrase uncritically).
