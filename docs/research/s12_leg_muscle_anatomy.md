# Leg muscle anatomy across front/middle/hind legs: literature findings

Scope: support derivation of meso/metathoracic Hill-type leg muscles from the
FlyMimic (Ozdil et al. 2025, arXiv:2509.06426) prothoracic fit. Search via
WebSearch + WebFetch (Europe PMC, journal sites), ~25 min bound. Every item
tagged [FULL TEXT] (fetched and quoted from the article body), [ABSTRACT/SEARCH]
(only abstract or a search-engine synthesis was accessible — treat as lower
confidence, re-verify before using as a fitted constant), or [NOT FOUND].

## 0. The source model itself (FlyMimic, arXiv:2509.06426)

[ABSTRACT/SEARCH, via ar5iv fetch, not independently re-verified against PDF]
- Front (T1) leg: **15 muscle-tendon units** — "7 in the thorax, 6 in the coxa,
  and 2 in the femur" (Section 3.2). Hill-type params fitted to this leg only.
- The paper **already did a micro-CT anatomical reconstruction of mid- and
  hind-leg muscle fibers**: "we modeled seven muscle-tendon units (MTUs) per
  midleg" (Suppl. A.1 / Fig. S1B) and "eight MTUs per hindleg" (Fig. S2B), from
  synchrotron micro-CT fiber annotation. No muscle names, PCSA, volumes, fiber
  counts, max isometric force, optimal fiber length or tendon slack length are
  given for mid/hind leg — explicitly "restricted ... to anatomical
  reconstruction rather than optimizing the models to reproduce motor
  behaviors" because "only a single dataset was available for these legs."
  **Action item**: check if the authors' supplementary data/repo (not fetched
  here) contains the raw mid/hind-leg mesh or point data — it may give
  attachment geometry even without fitted force parameters.
- No explicit leg segment lengths found in main text.

## 1. Which muscles exist per leg

- **14 "distinct muscles"** per leg, attributed to Miller 1950 and Soler et al.
  2004, stated in a later review [FULL TEXT, PMC4740448]: "the leg muscle
  system of Drosophila is a complex structure that counts 14 distinct
  muscles." Each leg muscle "is composed of several fibers organized around a
  specific long internal apodeme" (Soler et al. 2004, as quoted there).
  Independently, Azevedo et al. 2020 eLife give the same figure for the front
  leg [FULL TEXT, PMC7347388, Introduction]: "The leg ... contains 14 muscles
  which are innervated by just 53 motor neurons."
- Brierley, Rathore, VijayRaghavan & Williams 2012 J Comp Neurol 520:1629-1649
  ("Developmental origins and architecture of Drosophila leg motoneurons")
  [ABSTRACT/SEARCH]: "13 muscle groups confined within the proximal leg
  segments, and another five in the thorax that insert in the leg" (≈18 total
  counting extrinsic thoracic-origin muscles), innervated by ~70 MNs/leg from
  ~15 hemilineages. The discrepancy with "14" likely reflects intrinsic-only
  vs. intrinsic+extrinsic counting conventions — **not resolved here, flag as
  an open bookkeeping question**, not a contradiction to silently average.
- I could not obtain Soler et al. 2004's actual per-segment muscle table (the
  paper sits behind journals.biologists.com; a ResearchGate table image
  "Muscles and tendons of the Drosophila leg" exists at
  https://www.researchgate.net/figure/Muscles-and-tendons-of-the-Drosophila-leg_tbl1_51368904
  but returned HTTP 403). [NOT FOUND — recommend a follow-up fetch with
  institutional access.]
- A specific, leg-pair-differentiated anatomical claim surfaced only through a
  WebSearch synthesis, not confirmed in the full text I could reach: that "the
  only major variation in muscle fiber numbers [between wild-type legs] is
  observed in the tarsus depressor muscle (tadm), in the first leg pair
  compared with the second and third" — attributed to Guillermin et al. 2026
  Sci Adv (10.1126/sciadv.aed0910, PMC13322264) "Spatiotemporal control of
  myoblast identity drives muscle diversity in the Drosophila leg." When I
  fetched the PMC full text directly and searched for "tadm"/leg-pair
  comparisons, **this sentence did not appear**; the paper's text explicitly
  states it analyzes T1 only and leaves T2/T3 "not detailed here." **Treat the
  tadm claim as unverified / possibly a search-tool fabrication — do not use
  it as a sourced number.** [NOT FOUND in full text; flagged, not used]
- That same paper does report three previously undocumented T1 muscles,
  including a "trochanter reductor muscle 2 (trrm2)" and "tibial depressor
  muscle 2 (tidm2)" [FULL TEXT, PMC13322264, Results/Methods] — T1-specific,
  no T2/T3 comparison given.
- No source found that enumerates whether the front and hind legs have an
  intrinsic trochanter-extensor muscle anatomically distinct from the
  mesothoracic TTM, vs. simply lacking an equivalent. [NOT FOUND]

## 2. Mesothoracic tergotrochanteral muscle (TTM/TDT) — the jump muscle

Identity: TTM = tergal depressor of the trochanter (TDT); extrinsic muscle
running tergum→trochanter, present only in the **mesothoracic (T2, middle)**
segment because of its tergal (wing-hinge) attachment; rapidly extends the T2
femur-tibia/coxa-trochanter joint for jumping and flight initiation (Card &
Dickinson 2008; giant-fiber literature). [ABSTRACT/SEARCH for the T2-only
anatomical claim — I did not find a paper stating explicitly that T1/T3 lack a
tergal attachment, this is inferred from consistent descriptions as "the
mesothoracic leg extensor" across sources, not from a single definitive
quote. Flag as inferred, not measured.]

**Fiber count** [FULL TEXT, Jaramillo, Lovato, Baca & Cripps 2009, Development
136(7):1105-1113, "Crossveinless and the TGFβ pathway regulate fiber number in
the Drosophila adult jump muscle," PMCID PMC2685931]:
- "The wild-type TDT comprises over 20 large muscle fibers and four small
  fibers" (Summary).
- "There are generally 26-28 large cells and four small cells" (Results) —
  i.e. ~30-32 fibers total in wild type; some mutant/background lines show as
  few as ~18 large fibers (variation is the paper's main subject).

**Fiber dimensions** [FULL TEXT, Jarvis, Bell, Loya, Swank & Walcott 2021,
Archives of Biochemistry and Biophysics 701:108809, DOI
10.1016/j.abb.2021.108809, PMCID PMC4609653]:
- "Jump muscle fibers (length: 133.0 ± 14.6 μm, width: 71.2 ± 11.5 μm, height:
  40.7 ± 5.6 μm; average ± SD)" (Results).
- "The jump muscle produced 34.7 ± 5.8 mN/mm² isometric tension at
  FLopt" (Results) — i.e. ≈34.7 kPa specific tension (1 mN/mm² = 1 kPa).

**Other isometric tension values for the same muscle, lower confidence**
[ABSTRACT/SEARCH only]:
- ≈37 ± 3 mN/mm², attributed to Koppes, Swank & Corr 2014 J Appl Physiol
  116:1543-1550, "A new experimental model to study force depression: the
  Drosophila jump muscle," DOI 10.1152/japplphysiol.01029.2013 — full text
  blocked (HTTP 403), value only from a search-engine synthesis; re-verify
  before use.
- ≈40 mN/mm² and, at the myofibril level, 19.8 ± 10.5 mN/mm² net active
  tension, from a 2025 paper "Drosophila jump muscle myofibrils: A new tool
  for investigating activation and relaxation" (PMC13316580) — only seen via
  search synthesis, not fetched in full text. [ABSTRACT/SEARCH]
- Foundational comparison source for TDT vs. flight muscle (DLM) physiology:
  Peckham, Molloy, Sparrow & White 1990, J. Muscle Res. Cell Motil. 11:203-215,
  "Physiological properties of the dorsal longitudinal flight muscle and the
  tergal depressor of the trochanter muscle of Drosophila melanogaster" — not
  fetched for exact numbers in this pass. [NOT FOUND — exact values]

**No micro-CT volume, cross-sectional area or mass values for the whole TTM**
(as opposed to single-fiber dimensions above) were found. [NOT FOUND]

## 3. Jump / TTM whole-animal force

[ABSTRACT/SEARCH level — the WebFetch tool returned what appears to be
abstract/summary content for the paywalled full article; not independently
confirmed against the PDF]
Zumstein, Forman, Nongthomba, Sparrow & Elliott 2004, J. Exp. Biol.
207:3515-3522, DOI 10.1242/jeb.01181, "Distance and force production during
jumping in wild-type and mutant Drosophila melanogaster":
- "The peak force produced by the main jumping muscle of female flies from a
  wild-type (Canton-S) strain is 101 ± 4.4 μN;" "the force takes 8.2 ms to
  reach its peak."
- A kinematics-based model in the same paper gives a required "peak force
  [that] should be 274 μN (137 μN leg⁻¹)" for the jump — this appears to be a
  derived/back-calculated value from body mass and jump kinematics, not a
  direct force-transducer measurement; **do not relabel it as measured**.
- Card & Dickinson 2008 (Performance trade-offs in flight initiation, J Exp
  Biol; and Visually mediated motor planning, Curr Biol) describe TTM-driven
  jumps with femur-tibia and/or coxa-trochanter extension kinematics but no
  exact force number surfaced in this pass. [NOT FOUND — exact numbers from
  Card & Dickinson]
- von Reyn 2014 not retrieved in this pass; no numbers found. [NOT FOUND]

## 4. Specific tension / allometric force-area relations for insect leg muscle

- Directly measured Drosophila TDT specific tension: **34.7 ± 5.8 mN/mm²
  (≈34.7 kPa)** [FULL TEXT, Jarvis et al. 2021, above] — this is the single
  most directly applicable "fitted" muscle-stress number for scaling meso/
  hind leg muscles from the front-leg model, since it is measured in the
  actual target muscle class.
- Comparative context from other insect muscle (not Drosophila leg, use only
  as a sanity bound, not a substitute): locust flight muscle tetanic tension
  ≈32.4 N/cm² ≈ 320 kPa; general citation of Josephson 1993 giving ≈200 kPa as
  a typical vertebrate skeletal-muscle maximal isometric stress; asynchronous
  insect flight muscle (Lethocerus) ≈20-80 kPa. [ABSTRACT/SEARCH, secondary]
  These are 5-10x higher than the measured Drosophila TDT value — the
  discrepancy (preparation/temperature/activation differences vs genuine
  muscle-type difference) is unresolved and should not be used to "correct"
  the direct TDT number upward without further sourcing.
- No general-insect allometric relation of the form "force ∝ segment² or
  volume^(2/3)" with an explicit Drosophila-leg-fitted exponent was found.
  [NOT FOUND]

## 5. Leg segment lengths per leg (coxa/femur/tibia, pro/meso/metathoracic)

- A directly relevant dataset exists — Zenodo record 22059491, supporting
  "Differential Proximal and Distal Podomere Allometry Defines Leg Size in
  Drosophila Species," with raw files `global_size_flies.csv` and
  `stat_ok.csv` containing podomere-length measurements and allometric
  (hypo-/hyperallometric) scaling exponents for coxa, trochanter, femur,
  tibia, tarsomeres and pretarsus — but the actual numeric values were not
  retrievable through the Zenodo landing page text alone; the CSVs need to be
  downloaded directly. [NOT FOUND in this pass — recommend downloading the two
  CSVs for exact per-leg-pair segment lengths]
- No other source in this pass gave explicit mm/μm segment lengths broken out
  by leg pair. The "anatomical atlas of Drosophila melanogaster" (Genetics
  228(2):iyae129, 2024) is SEM-morphology only and explicitly does not give
  segment-length tables or muscle volumes. [FULL TEXT checked, confirmed
  absent]

## Bottom line for the derivation

The only numbers in this search that are both (a) full-text-confirmed and (b)
directly on the mesothoracic jump/trochanter-extensor muscle are: fiber count
≈26-28 large + 4 small fibers (Jaramillo et al. 2009), single-fiber dimensions
133×71×41 μm and isometric tension 34.7±5.8 mN/mm² (Jarvis et al. 2021). The
FlyMimic paper's own micro-CT reconstruction (7 midleg MTUs, 8 hindleg MTUs,
geometry only, no forces) is the most load-bearing resource for attachment
topology but contributes no PCSA/force numbers. Front/hind-leg
trochanter-extensor anatomy, leg segment lengths, and whole-muscle TTM
volume/CSA remain NOT FOUND in this pass and are the clearest next targets
(download the FlyMimic supplementary mesh/data repo; download the Zenodo
podomere-allometry CSVs; obtain Soler et al. 2004 and Peckham et al. 1990 full
text).
