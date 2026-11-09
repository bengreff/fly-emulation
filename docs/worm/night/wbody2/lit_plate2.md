# Literature check: two guessed agar-plate values

Session 2026-11-09, started 04:09 CST. Free sources only (PMC / Europe PMC, bioRxiv, theses, open-access
journal pages). No subagents spawned. Time-boxed to about 25 minutes; stopped at that mark, so some leads
below are flagged "not chased further" rather than exhausted.

Tool note: all full-text access below went through a web-fetch tool that converts the page to markdown and
runs a small model over it to pull quotes. For pages that loaded cleanly (PMC HTML pages that did not show a
captcha) I treat this as "opened full text." For scanned/old PDFs or pages that only returned an abstract or a
captcha page, I say so explicitly and treat the result as unverified / lower confidence. I did not visually
re-check every quoted sentence character-by-character against the raw page myself, only via this tool's
extraction, so treat exact wording as "as extracted" rather than hand-transcribed.

---

## 1. co2_rq (respiratory quotient of aerobic E. coli; model uses 1.0, range 0.7-1.2)

### Andersen & von Meyenburg 1980, J Bacteriol 144(1):114-123, "Are growth rates of Escherichia coli in
batch cultures limited by respiration?" PMC294601 (also journals.asm.org/doi/10.1128/jb.144.1.114-123.1980,
paywalled there).

- Access: attempted full text via PMC. The PMC page rendered only a "preparing to download" placeholder and
  the direct PDF link also would not render text through the fetch tool; what came back was effectively the
  abstract/front matter only. So this is **abstract-level access, not verified full text**, despite PMC listing
  it as available.
- Quote (abstract): "the specific rate of oxygen consumption was about 20 mmol of O2/h per g (dry weight)"
- Medium/phase: minimal medium with various carbon sources (not glucose specifically identified in what I
  could read), batch culture, growth rates 0.2-1.3 /h. Carbon source for this particular number not confirmed.
- No CO2 production rate or explicit RQ number came through in what I could access. The paper is known (per
  search-engine summary, not verified by me in the text) to plot Qo2 against "RQ/k," implying RQ was measured
  and used as a parameter, but I could not pull the actual value(s) from the table/figure.
- Verdict: **not found** (RQ number itself not recovered from this source despite it being the paper the
  brief suggested).

### Biorxiv preprint: "Escherichia coli metabolism under short-term repetitive substrate dynamics: adaptation
and trade-offs" (biorxiv.org/content/10.1101/2020.03.14.982140v1.full; later published in Microbial Cell
Factories 2020, 19:70, open access).

- Access: full text opened (bioRxiv page rendered as text, no captcha).
- Strain/medium: "Escherichia coli wild-type strain K12 MG1655 ... was used in all the experimental work of
  this study," aerobic bioreactor/chemostat on glucose minimal medium, aeration "0.44 L min-1 (0.5 vvm)."
  This is NOT peptone/NGM/LB; it is a glucose minimal medium bioreactor study, so it's a comparison point for
  glucose metabolism, not for peptone-grown OP50.
- Quote (results, describing a feast-famine pulse, not a flat RQ): "The respiratory quotient was then derived
  from these rates over time (Figure 2G). We observed that the RQ decreased from 1.5 to 0.7 during the first
  50 s of the feast phase, and increased back to the initial value after approximately 200 s."
- Quote (reference steady-state chemostat, not RQ directly but O2/glucose stoichiometry): "During the
  reference chemostat operation, the oxygen to substrate consumption ratio was 2.85 +/- 0.05 mol O2/mol glc."
- Reading: this paper shows RQ swinging between roughly 0.7 and 1.5 around a resting/initial value during
  transient glucose pulses in a chemostat, and implies the initial/steady value (before the pulse) is the
  "increased back to" value, which from the 1.5-to-0.7 transient reads as close to 1 at baseline, though the
  paper does not give one clean steady-state RQ number in what I could extract. This is a **proxy**, not
  OP50-on-agar, but it is a measured RQ in aerobic E. coli.

### PLOS ONE: "Experimental determination of Escherichia coli biomass composition for constraint-based
metabolic modeling" (journals.plos.org/plosone/article?id=10.1371/journal.pone.0262450), open access.

- Access: full text opened, but RQ appears only as a graphed quantity, not a stated number in text.
- Quote (figure 1 legend): "Glucose concentration [mM], CO2 in the off-gas [mmol h-1], respiratory quotient
  (RQ) [unitless], and OD600 [unitless]. Unity is highlighted on the same axis as the RQ for reference."
- Strain/medium: E. coli K12 MG1655, minimal glucose medium, batch fermentor, sampled through exponential
  growth (~7.5 h).
- The text states unity (RQ = 1) is drawn as a reference line on the same plot as the measured RQ trace,
  which implies the measured trace sits near 1, but I could not read the plotted numeric value itself (it's
  in a figure, not accessible as text through this tool). **Not a clean quoted number** - reported honestly
  as "seen only as a graph, not a number I can quote."

### Bacterial lawn / plate CO2 and O2 measurements (the brief's second ask: any direct measurement inside or
above an OP50 lawn on an NGM plate).

- Searched for: Bretscher et al. 2008 PNAS, Hallem & Sternberg 2008 PNAS, Carrillo et al. 2013,
  Kodama-Namba 2013, microsensor/biofilm O2 studies, "Bacterial Respiration and Growth Rates Affect the
  Feeding Preferences, Brood Size and Lifespan of C. elegans" (Yu et al. 2015, PLOS ONE,
  doi 10.1371/journal.pone.0134401, open access).
- Opened the Yu et al. 2015 PLOS ONE paper (PDF came through as embedded images/corrupted text via the fetch
  tool, so this is **not reliable full-text access** - treat as unverified). What came through: the paper
  measures headspace CO2 concentration over time for bacterial cultures including E. coli (OP50 context) by
  gas chromatography, with text noting "In the first 4 hours, E. coli produced the highest concentration of
  CO2" and bacteria "cultured in the dark at 20C," CO2 sampled "at 1, 2, 4, 8, 12, 24, 36, and 48 hours by gas
  chromatography." No O2 consumption number came through, so no RQ could be derived, and I would not trust
  the few numbers that did come through without a second read.
- Bretscher 2008, Hallem & Sternberg 2008, Carrillo 2013, Kodama-Namba 2013: not independently re-checked for
  free full text in the time available (search snippets only referenced O2/CO2 preference ranges for the
  worm's behavior, not a bacterial-lawn RQ number). **Not found** within the time box.

### What I searched but did not pin a number from
- "Andersen von Meyenburg 1980 RQ table" (abstract only, no table values recovered)
- "E. coli LB medium respiratory quotient measured" (no paper found reporting LB-specific RQ)
- Oxygen/CO2 microsensor measurements inside an NGM bacterial lawn specifically (no free full text located
  in the time box; Gray et al. 2004 and Rogers et al. 2006 are paywalled as the brief already expected)

### Bottom line on co2_rq
No single clean "RQ = X, measured on peptone/NGM medium" quote was recovered with verified full-text access.
The two numbers that came through with real confidence are: (1) Andersen & von Meyenburg's O2 uptake rate
(~20 mmol O2/h/g dry wt, abstract-level only, no matching CO2 number), and (2) the bioRxiv feast-famine paper's
RQ trace swinging 0.7-1.5 around a near-1 baseline in a glucose minimal-medium chemostat (full text opened).
Both support "RQ near 1, plausible range roughly 0.7-1.5" as a biologically reasonable envelope, consistent
with the model's 1.0 default and 0.7-1.2 range, but neither is a peptone-medium, OP50-specific, directly
quoted RQ value. I did not find or invent a better number.

---

## 2. nose_force_uN (force on/at the C. elegans nose tip in a nose-touch assay)

### Kaplan & Horvitz 1993, PNAS 90(6):2227-2231, "A dual mechanosensory and chemosensory neuron in
Caenorhabditis elegans." PMCID PMC46059.

- Access: not independently opened within the time box (relied on search-engine summary only, which
  described the touch method - a fine hair/platinum wire touched to the nose - and the ASH/FLP/OLQ circuit,
  but did not surface any force or force-estimate number). **Not found**: no force value in this paper
  surfaced via search; full text not opened by me, so I cannot rule out a number being in the methods that I
  did not see.

### Petzold et al. 2013, "MEMS-based force-clamp analysis of the role of body stiffness in C. elegans touch
sensation," Integrative Biology (Camb). PMCID PMC3701114.

- Access: **full text opened** (PMC page rendered as text, no captcha).
- This looks like the paper behind the "100 nN / 2 uN saturation" figure that review articles cite as
  "Petzold et al. 2013" (note: there are two 2013 Petzold-first-author papers; the brief named "Petzold et al.
  2013 Biophys J 'C. elegans body mechanics are regulated by body wall muscle tone,'" which is a different,
  related paper from the same group - I was not able to separately confirm the Biophys J paper's text in the
  time box, only this Integrative Biology force-clamp paper, which uses the same MEMS cantilever system and
  is almost certainly the immediate source of the "100 nN / 1 uN / sub-uN F1/2" numbers quoted by reviews
  under "Petzold et al. 2013.")
- Quote (results): "Forces of 100 nN evoked reversal behaviors with a low probability, while forces above
  1 uN generated reversal behaviors with high probability"
- Quote (results): "wild-type animals could detect sub-uN forces, with an F1/2 of approximately 0.5 uN"
- Quote (figure 2 legend): "we stimulated with forces between 100 nN and 10 uN"
- Quote (methods): "we first held a designated force for 100 ms and then retracted the cantilever slightly so
  that the applied normal force was approximately zero"
- This is a MEMS force-clamp cantilever pressed against the body (mid-body / touch-receptor-neuron region in
  the classic gentle-touch sense), not specifically the nose tip and not the ASH nose-touch circuit. Treat as
  a **proxy for the general sensitivity range of mechanosensory neurons to point forces**, not a nose-specific
  number. F1/2 (force giving half-maximal response) was about 0.5 uN; response probability was high by 1 uN
  and forces up to 10 uN were tested without a stated plateau in what I read.

### Review: "How Caenorhabditis elegans Senses Mechanical Stress, Temperature, and Other Physical Stimuli,"
PMC6499529 (open review article).

- Access: full text opened (PMC HTML rendered).
- Quote (section "Gentle or light touch"): "Freely moving wild-type animals can respond to forces as small as
  100 nN and the response probability saturates near 0.8 (or 8 of 10 trials) for forces exceeding 2 uN
  (Petzold et al. 2013)."
- This is a secondary citation (the review quoting Petzold et al. 2013), not the primary paper's own wording,
  though it is consistent with the PMC3701114 numbers above (100 nN low end, response rising toward high
  probability as force approaches/exceeds 1-2 uN). Also body-touch, not nose-specific.

### Nekimken, Mazzochette, Goodman & Pruitt 2017, "Forces applied during classical touch assays for
Caenorhabditis elegans," PLOS ONE 12(5):e0178080. PMCID PMC5438190.

- Access: full text opened (PMC HTML rendered cleanly, no captcha).
- Quote (results): "a 2-uN force is sufficient to saturate the behavioral response of wild-type worms"
- Quote (results, human-volunteer eyelash-hair touch): "The median force from all trials was 26 uN. The
  coefficient of variation of the distribution was 1.7, and the mean force was 61 uN."
- Quote (results): "The mean (61 uN) and median forces (26 uN) were more than ten times higher than the 2-uN
  force known to saturate the probability of evoking a reversal"
- Quote (methods, re: the eyelash hairs used as the mechanical probe): "Stiffness values varied between
  0.067 N/m and 0.41 N/m"
- This is the **classical anterior/body gentle-touch assay** (an eyelash hair stroked across the body,
  commonly near the head/anterior region but not specifically calibrated as "the nose tip"), done by human
  volunteers, with the actual forces measured by a force-sensing cantilever standing in for the worm. It
  confirms 2 uN as the saturating force for the touch-reversal response and shows real human-applied touches
  are 10-30x higher (26-61 uN median/mean) than what's needed to saturate the response. No plate-tap /
  tapper-habituation force was in this paper (checked explicitly; not present).

### Nose-touch-specific force number: searched for but access was weaker

- A search snippet (not independently opened/verified) pointed to a number "87 uN" described as a force
  "pushed against the nose" in a nose-touch stimulation protocol, apparently from a 2026 Cell Reports paper,
  "Glia-released serotonin drives nose touch responses in Caenorhabditis elegans." Attempting to open the
  full text at cell.com returned HTTP 403 (paywalled/blocked), so I could **not verify this number myself** -
  flagging it only as an unverified lead, not a usable citation. Do not treat "87 uN" as confirmed.
- A separate unverified search-engine summary (not traced to a specific paper, and I could not re-find the
  primary source before time ran out) claimed "ASH neurons respond to force stimuli ranging from 5-80
  micronewtons delivered through a 20 um diameter probe." I could not attribute this to a specific
  paper/section within the time box, so it should be treated as **not found / unverified**, not cited as fact.
- Geffeney et al. 2011, Neuron 71(5):845-857, "DEG/ENaC but not TRP channels are the major mechanoelectrical
  transduction channels in a C. elegans nociceptor" (the paper that most likely has real, calibrated ASH
  glass-probe nose-touch force numbers in uN, per task brief and per search summaries describing "glass
  probes or microbeads with a radius of 5-10 um... indent the body to a maximum depth of approximately
  10 um"): confirmed via Europe PMC as **not open access** (PMC3170654 flagged isOpenAccess = N) and
  cell.com/neuron full text returned 403. **Excluded as paywalled**, per the free-sources-only instruction.
  Not used for any number here.
- Chatzigeorgiou & Schafer 2011 (Neuron, lateral facilitation between mechanosensory neurons): referenced
  only in passing by other search results; I did not independently locate or open free full text for it in
  the time box. **Not found / not chased**.
- Hilliard et al. 2005: referenced only as "a 50 um glass probe... moved toward the animal so that it could
  touch the animal's nose" (search-engine summary, not opened). No calibrated force number came through.
  **Not found**.

### Crawling thrust force (used only as an explicit upper-bound proxy, not as a nose-touch number)

### Rabets, Backholm, Dalnoki-Veress & Ryu 2014, Biophys J 107(8):1980-1987, "Direct measurements of drag
forces in C. elegans crawling locomotion." PMCID PMC4213666.

- Access: full text opened (PMC HTML rendered), but Europe PMC flags it isOpenAccess = N; it rendered anyway
  without a captcha block, so treat as opened-but-uncertain-license (reporting the quote is fine for research
  notes; redistribution rights are a separate question not relevant here).
- Quote (results, comparing their agar-crawling force estimate to a micropillar-array measurement): "The
  average exerted force is several times smaller than that observed in a microstructured pillar environment,
  but this is expected because the main resistive medium on agar is liquid."
- No absolute force-in-uN number for the worm's own thrust came through in what I could extract; the paper
  reports drag coefficients (velocity-dependent), not a single force magnitude, in the sections I could read.
  **Could not extract a number to use as the "worm's own thrust" upper bound** from this paper specifically.

### Johari (Canterbury PhD thesis), "Microsystems for C. elegans Mechanics and Locomotion Study"

- Access: blocked by Cloudflare ("Attention Required," HTTP 403-equivalent block page) when fetched directly;
  the only numbers I have are from a **search-engine summary, not opened full text**: "measure force with a
  resolution of 2.07 uN for body width of 80 um... the maximum calculated force was 33.87 uN when a pillar
  experienced maximum deflection of 20.36 um." This describes a micropillar array measuring the worm's
  push-force during crawling (whole-body thrust via pillar bending), not nose-specific, and it is
  **unverified** (I never saw the thesis text myself). Flagging as a lead only.

### Plate-tap force (Rankin et al. 1990 tapper), seen in passing per the brief

- Via a search-engine summary of a Cold Spring Harbor Learning & Memory review, "Analyses of Habituation in
  Caenorhabditis elegans" (learnmem.cshlp.org/content/8/2/63, direct fetch blocked with HTTP 403 by the
  journal site, so **not opened by me, summary only**): "A mechanical tapper (consisting of an electromagnetic
  relay with wire arm) produced mechanical taps exerting 1-2 N of force to the side of the test plate."
  This is Newtons (plate-level force), not micronewtons/nanonewtons on the worm itself, consistent with what
  the brief expected. **Unverified** (search snippet only, not confirmed against the primary Rankin 1990 text
  or the review's own page, since the review page itself would not render for me).

### Bottom line on nose_force_uN
The best **verified, full-text, directly-on-point** numbers are from Nekimken et al. 2017 (PMC5438190,
opened): 2 uN saturates the gentle-touch reversal response, and real human-applied touches run 26-61 uN
(median/mean). Petzold et al. 2013 (PMC3701114, opened) gives sub-uN sensitivity (F1/2 ~0.5 uN) and high
response probability by ~1 uN, consistent with the 2-uN saturation figure. Both are body/anterior gentle-touch
assays with the touch receptor neurons (ALM/AVM/PLM-type circuit), not the ASH-mediated nose-touch circuit
specifically, so they are a **proxy** for nose force, not a direct nose-tip measurement. I could not verify a
clean, calibrated nose-tip force number from the ASH/nose-touch literature itself (Kaplan & Horvitz 1993,
Geffeney et al. 2011, Chatzigeorgiou & Schafer 2011, Hilliard et al. 2005) within the free-sources, 25-minute
budget - either the paper was paywalled (Geffeney 2011, confirmed not open access) or full text did not load
for me in time (the others). An unverified search snippet mentioned "87 uN" for a 2026 Cell Reports nose-touch
paper, but I could not open that paper (403) to confirm it, so it is not usable as a citation here.

---

## Summary table

| Value | Best measured number(s) found | Source | Opened full text? | Direct or proxy |
|---|---|---|---|---|
| co2_rq | O2 uptake ~20 mmol/h/g dry wt (no matching CO2/RQ number recovered) | Andersen & von Meyenburg 1980, J Bacteriol, PMC294601 | No (abstract-level only; PDF/PMC page would not render) | Proxy (O2 rate only, not RQ) |
| co2_rq | RQ swings 0.7 to 1.5 around a near-1 baseline during glucose feast-famine pulses in a chemostat | bioRxiv 10.1101/2020.03.14.982140 (-> Microbial Cell Factories 2020) | Yes | Proxy (glucose minimal medium bioreactor, not peptone/NGM lawn) |
| co2_rq | RQ plotted with unity as reference line (no numeric value extractable) | PLOS ONE 10.1371/journal.pone.0262450 | Yes (text); figure value not extractable | Proxy, and number not recovered |
| co2_rq | Direct OP50-lawn O2/CO2 or RQ measurement | not found (Yu et al. 2015 PLOS ONE partially seen but unreliable; Bretscher/Hallem&Sternberg/Carrillo/Kodama-Namba not reached) | No reliable access | n/a |
| nose_force_uN | 2 uN saturates reversal response; human touches measured at 26 uN median / 61 uN mean | Nekimken, Mazzochette, Goodman & Pruitt 2017, PLOS ONE, PMC5438190 | Yes | Proxy (classical anterior/body gentle touch, not nose-tip specific) |
| nose_force_uN | F1/2 ~0.5 uN; 100 nN low-probability, >1 uN high-probability response | Petzold et al. 2013, Integrative Biology (Camb), PMC3701114 | Yes | Proxy (MEMS cantilever on body, not nose-tip/ASH specific) |
| nose_force_uN | ASH/nose-specific calibrated glass-probe force (e.g. Geffeney et al. 2011) | Excluded: Geffeney 2011 confirmed paywalled (not open access); Kaplan & Horvitz 1993, Chatzigeorgiou & Schafer 2011, Hilliard et al. 2005 not opened in time | No | n/a - not found within free-source/time budget |
| nose_force_uN (context only) | Worm's own crawling thrust ~33.87 uN max, 2.07 uN resolution, via pillar bending (unverified) | Johari PhD thesis, Univ. of Canterbury | No (Cloudflare block; search snippet only) | Proxy, and unverified |
| plate tap force (seen in passing) | mechanical tapper exerts 1-2 N on the plate (Newtons, not uN) | Rankin et al. 1990 tapper, via Learning & Memory review (learnmem.cshlp.org/content/8/2/63) | No (journal site blocked fetch; summary only) | Direct, but unverified |
