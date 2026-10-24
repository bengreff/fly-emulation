# Literature read: activity/structural plasticity rules for a whole-CNS Drosophila spiking model

Search budget ~40 min. Full text obtained and read directly (by me, via pdftotext / HTML-strip of the
actual article, not a secondary summarizer) for: Apostolopoulou & Lin 2020 PNAS, Engel & Wu 1996 J
Neurosci, Das et al. 2011 PNAS, Bushey/Tononi/Cirelli 2011 Science. For Gilestro et al. 2009 Science and
Donlea et al. 2009 Science, PMC pages were blocked by a Google reCAPTCHA wall on direct fetch; numbers
below for those two come from a WebFetch call that itself retrieved the live PMC full-text page and had a
secondary model extract numbers from it — i.e. full text existed and was fetched, but I did not personally
re-verify the digits against the rendered page/figure. These are marked "secondary (auto-extracted from
full text, unverified)" rather than "measured" to be conservative. Kazama & Wilson 2008 Neuron, Larkin et
al. 2010 Learn Mem, and Sudhakaran et al. 2012 J Neurosci were paywalled (cell.com / CSHL / jneurosci.org
all returned HTTP 403) and no open full text was found in the time budget — those entries are
abstract/secondary-only, explicitly flagged, with no invented numbers.

---

## Topic 1: Homeostatic plasticity in the adult brain over days

### Apostolopoulou & Lin 2020, PNAS 117(28):16606–16615, "Mechanisms underlying homeostatic plasticity in
the Drosophila mushroom body in vivo" — **read in full text** (accepted manuscript PDF, White Rose
Research Online eprint 162916, text identical to published PNAS version per their deposit notice).

- Manipulation 1 (lack of inhibition): tetanus toxin (TNT) in APL, acute (16–24 h, tubP-GAL80ts released
  by heat) vs. constitutive (TNT throughout development). Driver: NP2631-GAL4 ∩ GH146-FLP intersection
  (labels APL only). — conditions; *measured*, full text p.4–5 / Fig. 1C,D.
- Result 1: KCs show **little to no compensation** for loss of APL inhibition — KC odor responses stay
  elevated whether TNT expression was acute or constitutive, with only a small (not fully characterized)
  difference between the two ("# p<0.05 acute vs constitutive" in Fig. 1D, no percent given in text). —
  *measured* (significance only; no % magnitude recovered from text), Fig. 1C,D, Table S2.
- Manipulation 2 (excess inhibition): dTRPA1 (temperature-gated cation channel) in APL, heated to 31 °C
  for 1, 2, 3 or 4 d (88–96 h for "4 d"); flies raised 22 °C, collected 0–1 d post-eclosion; KC odor
  responses (GCaMP6f) recorded back at 22 °C. Two independent APL drivers used: NP2631-GAL4∩GH146-FLP and
  VT43924-GAL4. — conditions; *measured*, full text p.6–8.
- Result 2: KC odor responses (max ΔF/F, isoamyl acetate "strong" odor and δ-decalactone "weak" odor) are
  **significantly higher** after 4 d pre-activation vs. unlabeled/non-heated controls, in all lobes, with
  both drivers (Fig. 2B–E, Fig. 3A). No percent-increase number is given in the running text (only
  significance stars and ANOVA stats in Table S2); the actual effect size sits in the bar-graph figures,
  which were not read as images in this pass — **gap: no % magnitude extracted**, flagged rather than
  guessed. — *measured* (direction and significance only), Fig. 2B–E/3A, Table S2.
- Time course of induction: tested at 1, 2, 3, 4 d of 31 °C APL activation (fly age at imaging held
  constant at 4–5 d post-eclosion). Effect was **significant and consistent only at 4 d**; at 1–3 d there
  was a trend, "sometimes significant at 2–3 d" but not reliably. → **induction takes ~4 days**, i.e. no
  single clean exponential time constant is given, but the paper's own framing is "most prominent after 4
  d." — *measured*, full text p.8, Fig. 3A, S9–S11.
- Decay: after 4 d of APL activation, flies returned to 22 °C for 1, 2 or 3 d ("forget" period) before
  imaging. The APL>dTRPA1 vs. control difference was **no longer statistically significant by 1–2 d**. →
  decay/"forgetting" time constant **~1–2 days**. — *measured*, full text p.9, Fig. 3B, S12.
- Mechanism (two components, not mutually exclusive, differing by KC subtype):
  1. **Reduced odor-evoked APL activity itself** after adaptation (APL odor responses significantly lower
     in adapted vs. non-adapted flies, Fig. 4B,C) — implicates decreased synaptic excitation onto APL
     and/or decreased APL intrinsic excitability.
  2. **Increased KC-intrinsic excitation/excitability that persists even with APL output acutely silenced**
     — shown in αβ KCs using histamine-gated Cl⁻ channel "Ort" expressed in APL + bath histamine (2 mM) to
     silence APL output regardless of its activity history (Fig. 6C,D): adapted αβ KCs still showed higher
     responses than non-adapted even with APL silenced, implicating increased PN→KC synaptic excitation
     and/or increased KC intrinsic excitability. In γ KCs, by contrast, silencing APL abolished the
     adaptation difference, meaning γ-KC adaptation is explained mostly by reduced APL activity (mechanism
     1 only). — *measured*, full text p.10–13, Fig. 4–6.
- Conditions not found in the extracted text: sex of flies not stated in the sections read (may be in
  Methods detail not captured by this pass) — flagged, not assumed.

### Independent check candidate: Kazama & Wilson 2008, Neuron 58(3):401–413, "Homeostatic matching and
nonlinear amplification at identified central synapses" — **could not obtain full text** (cell.com and a
direct PMC search both blocked/unavailable in the time budget). What is known only from
abstract/secondary sources (WebSearch snippets, Wilson lab publication page): ORN→PN synapse; unitary
synaptic current amplitude in a given PN type is matched to that PN's input resistance/dendritic-arbor
size, so that different PN types (which vary severalfold in dendrite size) end up with roughly uniform
depolarization per ORN spike. This is presented as a **cross-cell-type structural/developmental matching**,
not an activity-triggered day-scale compensation — i.e. it answers a different question than
Apostolopoulou & Lin's "how fast does a perturbed set point recover," and no induction/decay time constant
or % magnitude could be extracted from available sources. **Label: secondary (abstract-level only); no
usable magnitude or timescale found — flagged as a gap, not filled with a guess.**

### Larval fallback (explicitly labelled, not read in full text this session): larval motor-neuron
homeostasis at the glutamatergic NMJ (Petersen et al. 1997 Neuron; Davis & Goodman 1998; Mee et al. 2004 J
Neurosci; Frank et al.; Driscoll et al. 2013; Parrish et al. 2014, per general literature knowledge, not
verified in full text this session) is the textbook case: genetically reducing postsynaptic glutamate
receptor sensitivity triggers a compensatory increase in presynaptic quantal content within the same
larval developmental window, restoring the postsynaptic potential close to wild-type despite the receptor
lesion. **Label: secondary/background knowledge, NOT verified against primary text in this session — larval
fallback only, per task instructions. No numeric magnitude is given here because none was confirmed from a
primary source this session.**

---

## Topic 2: Structural synaptic plasticity with wake and sleep

### Bushey, Tononi & Cirelli 2011, Science 332(6037):1576–1581, "Sleep and Synaptic Homeostasis: Structural
Evidence in Drosophila" — **read in full text**, PMC3128387 (HTML fetched directly, scripts/tags stripped
and read by me).

- Three circuits examined, all in adult flies:
  1. **Small ventral Lateral Neurons (sLNvs)**, presynaptic terminal, markers syt-eGFP and PDF
     immunostaining. 7-day-old females: wake (W, >75% spontaneous wake, light period, n=9) vs. sleep (S,
     >80% asleep, dark period, n=9) vs. sleep-deprivation (SD, >90% kept awake, dark period, n=5): staining
     higher in W and SD than S (Fig. 1b–d). Males (1,3,7-day-old, n=5/timepoint): SD > S at night, both 3-
     and 7-day-old (Fig. 1e–g); 1-day-old flies show low staining regardless of condition (neurons judged
     not yet functionally mature). per01 clock-null males (no consolidated sleep; forced 7 h or 12 h SD, or
     7 h SD + 5 h recovery sleep, n=7/group): staining still high after 7 and 12 h SD, low after recovery
     sleep (Fig. 1h–j). — **No % magnitude given**, only qualitative "higher/lower" plus significance; —
     *measured* (direction only), Fig. 1, full text Results.
  2. **Mushroom body γ-neuron axon terminals** (MARCM single-cell clones). Axonal tip width larger after 7
     h SD (n=15) than 7 h S (n=26) (Fig. 2c,d). syt-eGFP puncta width larger in SD (n=26) and spontaneous W
     (n=20) than S (n=34) (Fig. 2g,h); **puncta count per lobe did not differ**: S=28±2, SD=29±2, W=30±2
     (mean±SEM) — i.e. size changed, number per lobe did not. — *measured*, full text Fig. 2 legend
     (explicit numbers, directly read by me).
  3. **VS1 lobula-plate tangential neuron dendritic spines** (postsynaptic; actin-GFP). Total spine number
     higher after 7 h SD than after S or spontaneous W (mainly "stubby" spines), n=10/group (Fig. 3d);
     mushroom-type spine count unchanged (p=0.29); spine *density* (spines/branch length) unchanged
     (p=0.20) — the absolute increase comes with proportional branch growth. — *measured*, full text Fig.
     3, Results.
- "Fly mall" social/sensory enrichment (12 h, up to 100 flies in a large lit chamber, free flight): vs. 12
  h alone in a tube, enrichment increased VS1 branch length, branch points, and spine number (n=10 tube vs.
  n=12 mall, Fig. 3e,f). After enrichment, 7 h of recovery sleep reverted all three parameters to baseline
  (n=12 S-post-mall vs. n=11 SD-post-mall, Fig. 3g,h); flies also slept more over the following 24 h after
  enrichment (n=76 enriched vs. 75 controls, Fig. 3i). A second protocol (12 h mall + 12 h overnight SD,
  then either immediate harvest n=9, +6 h more SD n=7, or +6 h recovery sleep n=10, Fig. 3j,k) confirmed
  reversal requires actual sleep, not just elapsed time. — *measured*, full text, no % given (counts and
  lengths only, not normalized to percent in the text).
- **Fmr1 (fragile X) role** — the cleanest quantitative numbers in this paper:
  - Fmr1-overexpressing (OE) flies show **no** SD-induced increase in VS1 spine number/branch
    length/branch points (OE: S n=9, SD n=8; WT: S n=11, SD n=8; Fig. 4d,e). — *measured*, full text.
  - OE flies sleep **9.6% less** than WT at baseline (n WT=110, OE=62, p<0.05, Mann-Whitney). — *measured*,
    full text Results (matches Fig. 4 legend context), read directly by me.
  - After 12 h overnight sleep deprivation, OE flies recover **39%** of lost sleep vs. **49%** for WT (n
    OE=293, WT=420, p<0.05); both groups lost **>90%** of sleep during the SD itself. — *measured*, full
    text.
  - *Derived* (by me, simple arithmetic, not stated verbatim in the paper): the WT/OE rebound gap is 49% −
    39% = **10 percentage points** of lost sleep not recovered in OE flies — a single clean number that
    could anchor a "how much sleep debt gets repaid" rule. Shown as derived since the paper states the two
    percentages but not their difference.
- No explicit per-hour or per-day percent growth rate for synapse number/size is given anywhere in the main
  text — only directional (higher/lower), with sample sizes and significance. **This is a real gap for
  building a quantitative growth-rate rule from this paper alone.**

### Gilestro, Tononi & Cirelli 2009, Science 324(5923):109–112, "Widespread Changes in Synaptic Markers as a
Function of Sleep and Wakefulness in Drosophila" — PMC2715914. **Label: secondary (auto-extracted from the
live full-text page by a WebFetch sub-call; direct curl of the PMC page was blocked by a Google reCAPTCHA
challenge page, so I could not personally re-verify these digits against the rendered figures).**

- Bruchpilot (BRP) protein (presynaptic active-zone marker, Western blot + confocal): increase after sleep
  deprivation, described as modest after 6 h SD and larger, "approximately 30–40%," after 12–24 h SD
  (Fig. 1C–E, 3B per the extraction).
- Whole central brain BRP increase ≈ **76 ± 15%** after wake vs. sleep (Fig. 4, per extraction); regional
  breakdown: antennal lobes **69 ± 11%**, mushroom body β lobes **40 ± 11%**, ellipsoid body/central
  complex **67 ± 18%** (same figure, per extraction). Antennal lobe volume itself up **~15%** after 16 h
  deprivation.
- Synapsin, Syntaxin, CSP: ~30% increase after 24 h SD (Fig. 1F–H per extraction); DLG ~20–40% lower after
  recovery sleep vs. SD controls (Fig. 3B per extraction).
- Time course: BRP declines progressively through the sleep period, reaching its lowest point near the end
  of the night (Fig. 3A per extraction); decline requires actual sleep (forced-wake controls stay elevated,
  Fig. 3B).
- Genotype Canton-S and w1118 reported; both sexes tested; explicit temperature and age not captured in the
  extraction.
- **All numeric % values in this sub-section should be treated as provisional** until re-checked against
  the actual Fig. 1/3/4 bar graphs — they are internally consistent with the Bushey 2011 qualitative
  pattern (wake ↑, sleep ↓) but I have not independently confirmed the digits.

### Donlea, Ramazan & Shaw 2009, Science 324(5923):105–108, "Use-Dependent Plasticity in Clock Neurons
Regulates Sleep Need in Drosophila" — PMC2850598. **Same caveat as Gilestro: secondary (auto-extracted from
the live PMC full text by WebFetch; direct curl blocked by reCAPTCHA).**

- 5 days of social enrichment (not hours), 3–4-day-old males, before testing daytime sleep increase
  (Fig. 1A–E per extraction); rutabaga mutants fail to show the enrichment-induced sleep increase, rescued
  by pdf-GAL4-driven rut+ in the LNvs (p=0.03, per extraction); period (rescued by a 7.2-kb genomic
  fragment) and blistered (rescued by bs-GAL4) similarly required in LNvs.
- Postsynaptic LNv terminal marker (dlg-GFP): significant increase after 5 d enrichment (P=1.5×10⁻⁵,
  n=33–34/group, Fig. 4C per extraction); after 48 h of recovery sleep, significantly reduced vs.
  sleep-deprived siblings (P=0.003, n=15–18, Fig. 4D).
- Presynaptic marker (VAMP-GFP): "modest" increase after enrichment (P=0.03, n=16–18, Fig. 4G); reduced
  after 48 h recovery (P=0.01, n=18, Fig. 4H).
- **No % magnitude of the terminal increase/decrease is given**, only P-values and n — another real gap.
- This paper and Bushey 2011 together give two independent neuron populations (LNv terminals here vs. VS1
  spines / γ-KC terminals in Bushey) and two independent manipulations (5-day social enrichment here vs.
  7 h SD or 12 h "fly mall" in Bushey) showing the same qualitative rule — synapse size/number grows with
  waking experience and recedes only with actual sleep (not just elapsed time) — which is useful as a
  **qualitative cross-check** even though neither gives a percent growth rate.

---

## Topic 3: Plasticity at other sites — habituation

### Engel & Wu 1996, J Neurosci 16(10):3486–3499, "Altered Habituation of an Identified Escape Circuit in
Drosophila Memory Mutants" — **read in full text** (PDF via Wayback Machine mirror of jneurosci.org,
OCR'd with pdftotext; a few characters garbled by OCR, e.g. "Controls" OCR'd as "CuntKols" and "rut" as
"mt" in one table row — flagged below where this matters).

- Assay: giant-fiber pathway escape response, triggered by **direct electrical stimulation** (not just
  visual) in tethered flies; success/failure scored from the DLM "jump" muscle spike. Habituation
  criterion: **5 consecutive stimulus failures to evoke a long-latency response.** — *measured*, full text
  Methods.
- Table 2 (median number of stimuli to reach the 5-consecutive-failure criterion, by genotype and
  stimulus frequency; n in parentheses) — *measured*, full text Table 2, read directly by me (digits below
  as OCR'd; the rut row's leading genotype label was OCR-garbled but the row's identity is unambiguous from
  context and the Results text, which states rut needs far more stimuli than controls):
  - Controls: 2 Hz = 42 (n=26); 5 Hz = 8.5 (n=90); 10 Hz = 39 (n=13).
  - rutabaga (rut, cAMP-synthesis-deficient): 2 Hz ≈ 404 (n=12); 5 Hz ≈ 473 (n=36); 10 Hz ≈ 64 (n=18) —
    resistant to habituation (far more stimuli needed).
  - dunce (dnc, cAMP-elevated): 2 Hz = 37 (n=11); 5 Hz = 30 (n=32); 10 Hz = 19 (n=8) — habituates faster
    than control.
  - dnc rut double mutant: 2 Hz = 19 (n=6); 5 Hz = 23 (n=21); 10 Hz = 9 (n=7) — fastest of all, i.e. the
    double mutant is not intermediate between the two single mutants (non-additive/synergistic).
  - **OCR confidence note:** exact digit strings above should be spot-checked against the original table
    image before being used as hard calibration targets; the qualitative ranking (rut ≫ control > dnc >
    dnc-rut, in stimuli-to-criterion) is stated explicitly in the Results text independent of the table OCR
    and is high-confidence.
- Habituation is **faster at higher stimulus frequency** (10 Hz habituates faster/more abruptly than 2 or 5
  Hz) — *measured*, full text Fig. 4, Results.
- Spontaneous recovery (Fig. 5, Table 2): after habituating to criterion at 5 Hz, a **120 s** recovery
  period was "sufficient to restore initial response levels in all genotypes." Shorter recovery intervals
  (30 s then 5 s, in a three-bout protocol) showed **full recovery of response probability at 30 s**, but
  faster re-habituation on the next bout; at **5 s**, dnc and dnc-rut mutants had not fully recovered
  initial response levels, while controls and rut had. rut mutants, despite needing far more stimuli to
  reach criterion in the first place, re-habituated unusually quickly even after the full 120 s recovery. →
  **recovery time constant is on the order of tens of seconds to ~2 minutes**, genotype-dependent. —
  *measured*, full text Fig. 5, Table 2.
- Dishabituation: air puff or light flash restores responsiveness after habituation in both mutants and
  controls (Fig. 7, Table 2 gives rising fraction and mean increase in response count per genotype);
  repeated dishabituating stimuli show habituation of the dishabituating effect itself over many trials
  (Fig. 8) — qualitative, no clean single number extracted beyond the Table 2 entries already listed in a
  prior query pass (not re-verified here due to time).
- "Habituation beyond zero" (Fig. 6): repeated 10 Hz bouts with 60 s recovery intervals; once stimulation
  continued well past the point responses had already stopped (bouts 5–7), subsequent recovery was
  **reduced** relative to bouts stopped right at criterion — qualitative only, no number given.
- Site of habituation: localized to the brain (afferent side of the giant fiber), not the thoracic
  motor branches — a universal, genotype-independent, much-faster latency shift of **up to 2 msec** occurs
  with repetition but does not track habituation and is attributed to a separate, non-plastic process
  (electrode polarization or similar) (Fig. 9, Table 3). — *measured*, full text.
- Conditions: tethered adult flies, Canton-S or cn1 bw controls; rutabaga, dunce, and dnc-rut double
  mutants; rested ≥1 h after mounting, 5 min immediately pre-test. **Sex and temperature were not found in
  the sections extracted — flagged as not confirmed, not assumed.**

### Das et al. 2011, PNAS 108(36):E646–E654, "Plasticity of Local GABAergic Interneurons Drives Olfactory
Habituation" — **read in full text**, PMC3169145 (HTML fetched directly and stripped by me).

- Short-term habituation (STH): **30-min exposure** to 15% CO₂ or 5% ethyl butyrate (EB); tested via Y-maze
  avoidance (response index) in **2-day-old flies starved overnight**. STH is odorant-selective (CO₂
  exposure doesn't affect EB response and vice versa). **Recovers with a half-life of ≈20 min** (Fig. 1B,C).
  — *measured*, full text, explicit "half-life of about 20 min" statement, Results + Fig. 1 legend.
- STH does not require odorant-receptor activation: direct 30-min TrpA1 thermogenetic activation (29 °C) of
  Gr21a⁺ (CO₂-sensing) or Or83b⁺ (EB-sensing) OSN subsets alone reproduces odorant-selective STH (Fig. 1D).
  — *measured*, full text.
- Long-term habituation (LTH): **4-day continuous exposure** to 5% CO₂ or 20% EB (or, for "phantom" LTH,
  4-day TrpA1 thermogenetic OSN activation); odorant-selective; **lasts several days**, with recovery
  measured at 0 d and 6 d post-exposure (response moves back toward naive levels by 6 d; full return to
  normal rearing conditions restores sensitivity "within a few days") (Fig. 1E–G). — *measured*, full text.
- Mechanism: the **rutabaga (rut)-encoded adenylate cyclase is required specifically in GABAergic LN1
  multiglomerular local interneurons** (not broadly) for both STH and LTH — shown by cell-type-specific
  rut+ rescue in a rut²⁰⁸⁰ null background (Fig. 2B,C) and by LN1/GAD1-restricted RNAi knockdown of rut
  blocking both STH and LTH (Fig. 2D, two independent RNAi lines). LTH additionally requires the CREB2
  transcription factor in LNs. — *measured*, full text.
- Postsynaptically, odorant-selectivity of both STH and LTH requires **NMDA receptors and GABA-A receptors
  in the odor-selective projection neurons (PNs)** — consistent with an LN→PN GABAergic potentiation model
  combined with NMDAR-dependent plasticity in PNs. — *measured* (qualitative requirement; magnitude not
  separately quantified in the sections read), full text.
- Physiological readout: 4-d EB exposure significantly reduced EB-evoked PN calcium responses (GCaMP3,
  GH146-Gal4 driver) specifically in the **DM2** (P=0.004) and **DM5** (P<0.001) glomeruli, with no effect
  on the unrelated DC2/3-octanol response, and no effect of CO₂ exposure on the EB response (Fig. 3A,B,
  Table S4). This PN-response reduction was **abolished in rut²⁰⁸⁰ mutants** (rescued with UAS-rut+ as the
  non-habituating control genotype) (Fig. 3B) — i.e. the same rut-dependence seen behaviorally is seen at
  the PN synapse. — *measured*, full text, n's given per condition (WT mock n=6/EB n=4 for DM2; rut mock
  n=12/EB n=8; similar pattern for DM5).
- Conditions: adult flies 0–12 h old at the start of the LTH protocol (collected young, then aged during
  the 4-d exposure); 2-day-old flies (post-eclosion) for STH testing after overnight starvation; air or
  paraffin-oil as vehicle controls; sex and rearing temperature not found in the sections extracted —
  flagged as not confirmed.

### Larkin et al. 2010, Learning & Memory 17(12):645–653, "Central Synaptic Mechanisms Underlie Short-Term
Olfactory Habituation in Drosophila Larvae" — **full text blocked** (learnmem.cshlp.org returned HTTP 403
on every user-agent tried). **Label: secondary, abstract/search-snippet level only.** Reported (unverified)
requirements for larval STH: (1) rutabaga adenylate cyclase, (2) GABAergic transmitter release from local
interneurons (LNs), (3) GABA-A receptor function in PNs; proposed model of NMDAR-dependent depression of
the OSN–PN synapse and/or NMDAR-dependent facilitation of LN→PN inhibition. **No exposure protocol, %
reduction, or time constant could be extracted — explicitly a gap, not filled with invented numbers.** This
is a larval system and the same rut/GABA logic as the Das et al. 2011 adult STH, so it is a plausible
cross-stage qualitative check on a rutabaga/GABA-potentiation habituation rule, but cannot be used
quantitatively without the primary numbers.

### Sudhakaran et al. 2012, J Neurosci 32(21):7225–7231, "Plasticity of Recurrent Inhibition in the
Drosophila Antennal Lobe" — **full text blocked** (jneurosci.org 403 on every attempt). **Label: secondary,
title/abstract level only** — concerns LN–LN recurrent inhibition plasticity, directly relevant to the
antennal-lobe habituation mechanism in Das et al. 2011, but no numbers were obtainable in the time budget.
Flagged as a gap.

### Twick, Lee & Ramaswami 2014, Prog Brain Res 208:3–38, "Olfactory Habituation in Drosophila — Odor
Encoding and Its Plasticity in the Antennal Lobe" — **review, secondary/abstract level only**, not fetched
in full. Synthesizes that potentiation of inhibitory (LN) synapses in the antennal lobe is the central
mechanism for both short- and long-term olfactory habituation, modulated by neuromodulators. Useful as a
citation map, not as a source of new primary numbers.

---

## Six-line summary

1. **Homeostatic plasticity (adult, days):** cleanest rule value — Apostolopoulou & Lin 2020 PNAS: induction
   needs ~4 d of excess APL (GABAergic) inhibition to significantly raise KC odor responses, decaying back
   within ~1–2 d after the perturbation stops (both *measured*, full text Fig. 3A,B). Cleanest independent
   held-out check — **none found**: Kazama & Wilson 2008 was inaccessible and answers a different
   (cross-cell-type structural matching, not activity-triggered day-scale) question; flagged as a genuine
   gap rather than guessed.
2. **Sleep/wake structural plasticity:** cleanest rule value — Bushey et al. 2011 Science Fmr1 data: WT
   flies recover 49% vs. Fmr1-overexpressors 39% of lost sleep after 12 h deprivation (both baseline −9.6%
   sleep in OE; all *measured*, full text, n's given). Cleanest independent check — Donlea et al. 2009
   Science: a different neuron (LNv terminals) and manipulation (5-d social enrichment, not SD) shows the
   same qualitative direction (synapse marker ↑ with wake/enrichment, ↓ only with sleep) — but neither paper
   gives a percent growth rate, so the check is qualitative, not quantitative (Donlea numbers are
   secondary/auto-extracted, unverified by me).
3. **Habituation:** cleanest rule value — Das et al. 2011 PNAS: short-term olfactory habituation after a
   30-min odor exposure recovers with an explicit, stated **half-life of ≈20 min** (*measured*, full text).
   Cleanest independent check — Engel & Wu 1996 J Neurosci: giant-fiber habituation in a wholly different
   (escape, not olfactory) circuit is also cAMP/rutabaga-dependent and recovers on a comparable tens-of-
   seconds-to-minutes timescale (full recovery by 120 s at 5 Hz), giving a cross-circuit qualitative check
   that a rutabaga/cAMP-gated habituation-decay rule generalizes — though the two papers' time units (odor-
   exposure minutes vs. stimulus-count/frequency) are not directly interchangeable, so this is a consistency
   check on mechanism, not a strict numeric held-out test.
