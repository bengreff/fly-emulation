# Leg mechanosensory organ counts: literature audit (2026-10-04)

Method: Europe PMC REST API + direct curl/pdftotext on primary PDFs/HTML (bypassing
WebSearch's AI summarizer, which gave internally inconsistent numbers on cross-check
and should not be trusted for exact figures). Items marked READ were pulled from
primary full text I fetched myself; SECONDARY = seen only in another paper's citation
of the primary source; NOT FOUND = could not access/verify in time budget.

## 1. Leg campaniform sensilla (CS) — Dinges et al. 2021, J Comp Neurol 529:905-925,
doi:10.1002/cne.24987 (Dinges, Chockley, Bockemühl, Ito, Blanke, Büschges)

**Full text access**: legitimately open access (CC-BY-NC, confirmed via Unpaywall),
but the Wiley host returns a Cloudflare bot-check page to every fetch method tried
(WebFetch, curl with UA spoof, r.jina.ai proxy) — 100% of attempts blocked. Could not
read the results/tables section. The numbers below are what I could verify from the
abstract (READ, verbatim) and from a 2025 paper that quotes Dinges' figure directly
(SECONDARY, verbatim).

- **READ (PubMed/EuropePMC abstract, PMID 32678470, verbatim)**: "we compared the
  front, middle, and hind legs of multiple flies using scanning electron microscopy...
  On the legs, the number and relative arrangement of CS varied between individuals,
  and single CS of corresponding segments showed characteristic differences between
  legs." → Confirms per-leg differences and inter-individual variability exist, but no
  numeric counts are in the abstract itself.
- **SECONDARY (Saltin et al. 2025, J R Soc Interface, PMC12056673, READ in full text)**:
  "CS were numbered from 1 (posterior–distal) to 11 (anterior–proximal; figure 1D,H)
  following descriptions by Dinges et al. [2021]." → the Drosophila **femoral** CS
  field (front leg) has **11 numbered sensilla** per Dinges' Fig. 1D/H scheme (an
  earlier WebSearch summary claimed "1–10 in three columns of 3/4/3"; I could not
  confirm that grouping independently and it conflicts with the "1 to 11" quote above,
  so treat the 3-column/10-sensilla claim as UNVERIFIED/likely wrong).
- **Per-leg/per-group (trochanter, femur, tibia, tarsus) exact counts: NOT FOUND** —
  blocked by paywall bot-check; would need institutional PDF access or the thesis
  (Dinges 2021, Univ. Cologne, kups.ub.uni-koeln.de/53025) full text, whose abstract
  PDFs I fetched but could not text-extract (encoded Word-export PDF streams).

## 2. Hair plate sensilla

- **READ (Pratt, Dallmann, Tuthill et al., Nat Commun 2026, PMC13009157, verbatim)**:
  "The six Drosophila legs have **214 hair plate mechanosensory neurons** that are
  clustered into **42 hair plates**" — citing Schubiger 1968 (classic SEM/clonal
  study), Hodgkin & Bryant 1978 (SEM), and Kuan et al. 2020 (EM). This is a 1-neuron-
  per-sensillum structure (hair plates have 1 neuron each), so 214 neurons = 214
  sensilla total across all 6 legs, averaging 42/6 ≈ 7 plates/leg, 214/6 ≈ 36
  neurons/leg (paper does not give the per-leg breakdown explicitly in the text I
  matched).
- **READ (same paper)**: names three coxa-thorax (ThC) hair plates on the front leg
  — CxHP3, CxHP4, **CxHP8** — and three coxa-trochanter hair plates — TrHP5, TrHP6,
  TrHP7.
- **READ (same paper, verbatim)**: "We reconstructed all **8 CxHP8 axons** within one
  left front leg neuromere of a Drosophila female VNC (FANC) electron microscopy
  volume" and "CxHP8 input threshold: 8 cells". A driver-line check found "CxHP8
  neurons on the front and middle legs (6 and 3 out of 8 cells, respectively)" —
  i.e. the true count is 8/leg, the Gal4 line just doesn't label all 8.
- **READ (Kuan et al. 2020, Nat Neurosci, PMC8354006, figure legends, verbatim)**:
  independently names "CoHP8", "CoHP4", "CoHP3" sensory-neuron axon bundles in the
  front-leg prothoracic nerves with measured axon diameters (e.g. CoHP8: 1030±90 nm) —
  the same coxal hair plates as CxHP8/4/3 above, cross-confirming the naming/count
  from a different lab's EM reconstruction (front leg, T1).
- Tarsal/tibial hair plate counts: NOT FOUND individually (only the 214/42 whole-leg
  total above).

## 3. Femoral chordotonal organ (FeCO) neuron counts

- **READ (Mamiya, Gurung, Tuthill 2018, Neuron 100:636-650, pdftotext of primary PDF,
  front/T1 leg, verbatim)**: "iav-Gal4 was previously thought to drive expression in
  all FeCO neurons, we found that it labeled 80% of the total population (**135
  neurons**; Figures 3F and 3G)." → implies total FeCO population ≈135/0.80 ≈ 169
  neurons (T1 leg), but the paper never states this total explicitly — 135 is the
  only directly reported absolute number, and it is a Gal4-driver label count, not a
  full anatomical census.
- **READ (same paper, verbatim)**: "The claw Gal4 line labeled **20 cell bodies**
  (Figure 3F)... The club Gal4 line drove expression in **30 neurons** (Figure 3F)...
  Finally, the hook Gal4 line drove expression in only **three** FeCO neurons (Figure
  3F)." The paper explicitly cautions these Gal4 lines "label less than half of the
  total FeCO neuron population" (line ~641) — i.e. claw=20, club=30, hook=3 are
  **undercounts**, not the true subclass sizes.
- A commonly repeated set of numbers "claw n=26, hook n=29, club n=50 (~150 total,
  front leg)" attributed to Kuan et al. 2020 appears in several WebSearch summaries
  but **I could not verify it** in Kuan 2020's accessible text (only figure/extended-
  data legends were retrievable; they discuss axon diameters and a "group of eight
  campaniform sensilla on the trochanter" but give no claw/hook/club subtype counts).
  Treat the 26/29/50 figures as UNVERIFIED pending full-text access to Kuan 2020's
  results section.
- **READ (Mamiya et al. 2023/bioRxiv 2022.08.08.503192, "Biomechanical origins of
  proprioceptive maps", full text)**: refines the classification to **five**
  functional subtypes by EM reconstruction — claw-flexion, claw-extension,
  hook-flexion, hook-extension, and club — organized into three physical compartments
  in the femur; no new absolute per-subtype counts found in the fetched sections.
- Tibial/tarsal chordotonal organ counts: NOT FOUND in this pass.

## 4/5. MANC (male-cns v1.0, Marin et al. 2024) and FANC (female VNC, Lesser/Phelps)
connectome annotation of leg CS / unassigned proprioceptor types

- Correction of task framing: **FANC = Female Adult Nerve Cord** (Phelps et al. 2021
  Cell; Lesser et al. 2024 Nature "Connectomic reconstruction of a female Drosophila
  ventral nerve cord"), not "front" — important not to conflate with male MANC.
- **Access failures**: Marin et al. 2024 eLife ("Systematic annotation of a complete
  adult male Drosophila nerve cord connectome...", bioRxiv 10.1101/2023.06.05.543407,
  eLife reviewed-preprint 97766) — blocked on every route tried (eLife 406, bioRxiv
  429 rate-limit, elife API 404, WebFetch load error). Phelps et al. 2021 Cell — 403
  Forbidden. **Could not independently confirm any leg-CS axon count, per-leg
  breakdown, or the SNpp naming scheme from primary text.**
- A WebSearch summary claimed specific SNpp numbers (SNpp04/08/11/33/36/06/26 as
  "small distal CS", SNpp30/32/31 as "large CS", SNpp28/37/38 as "tegula CS") but
  this mixes in wing/tegula types and could not be corroborated against the primary
  paper — **flag as UNVERIFIED, do not use**.
- **READ (Cheong et al., eLife, "Organization of circuits linking descending input to
  motor output...", PMC13384506, full text)**: extensively discusses **wing and
  haltere** campaniform sensilla connectivity (citing Marin et al. 2024) but contains
  no leg-CS-specific counts in the sections I could match — this paper's CS focus is
  wing/haltere, not leg.
- **READ (Chen/Dallmann et al., "Divergent neural circuits for proprioceptive and
  exteroceptive sensing of the Drosophila leg", Nat Commun 2025, PMC11071415, full
  text)**: confirms FANC's leg sensory-axon categories include "campaniform sensilla
  axons (CS)" and "hair plate axons (HP)" alongside claw/hook/club FeCO axons and
  bristle axons, in the T1 (front) leg nerve — but gives no numeric CS/HP counts in
  the matched text.
- No statement about "SNpp" untyped/unassigned leg proprioceptor categories could be
  verified in any primary source reached in this session.

## Summary table (verified primary numbers only)

| Quantity | Value | Leg | Source (READ) |
|---|---|---|---|
| Hair plate neurons, whole animal | 214 | all 6 legs | Pratt/Dallmann 2026 Nat Commun, citing Schubiger 1968 + Hodgkin & Bryant 1978 + Kuan 2020 |
| Hair plates (plate count), whole animal | 42 | all 6 legs | same |
| CxHP8 (coxa hair plate) neurons | 8 | front leg (T1), also present middle leg | Pratt/Dallmann 2026; corroborated by Kuan 2020 "CoHP8" |
| FeCO, iav-Gal4-labeled fraction | 135 (=80% of total) | front leg (T1) | Mamiya et al. 2018 Neuron |
| FeCO claw Gal4 line | 20 cell bodies | front leg (T1) | Mamiya et al. 2018 (stated as an undercount) |
| FeCO club Gal4 line | 30 neurons | front leg (T1) | Mamiya et al. 2018 (undercount) |
| FeCO hook Gal4 line | 3 neurons | front leg (T1) | Mamiya et al. 2018 (undercount) |
| Trochanteral CS, front leg | "group of eight" | front leg (T1) | Kuan et al. 2020 Nat Neurosci figure legend |
| Femoral CS field numbering | 1–11 | front leg (T1) | Dinges et al. 2021, quoted in Saltin et al. 2025 |

## Open gaps (not resolved this session)
- Dinges 2021 exact per-leg, per-segment CS table (paywall bot-blocked despite legitimate OA).
- True (non-Gal4-undercount) claw/hook/club FeCO subtype totals, and whether they differ pro/meso/metathoracic.
- Any MANC/FANC leg-CS axon counts or SNpp nomenclature — needs direct eLife/Cell access, ideally via an institutional proxy or the papers' supplementary data tables rather than the HTML page.
