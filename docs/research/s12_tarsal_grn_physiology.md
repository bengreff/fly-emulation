# S12: tarsal (leg/wing) taste transduction constants — literature search

Budget: ~45 min, cut short by coordinator after one fetch timeout. Method:
WebSearch + WebFetch (Europe PMC REST endpoints returned 500/403 for full-text
XML/HTML on two tries — jneurosci.org blocked with 403, EBI XML endpoint gave
500 — so the primary-source extractions below went through WebFetch's own
fetch-and-summarize pass over the PMC HTML / bioRxiv HTML mirrors, not a
direct read of the raw XML/PDF by me). That is a real evidence-quality
caveat: treat the Table-2 numbers from Ling et al. 2014 as **SECONDARY**
(machine-summarized quote, not independently re-checked against the typeset
table) until someone pulls the PDF and re-reads Table 2 by eye.

## What can be filled, and how

1. **Per-type modality (connectome mapping).** A 2025 bioRxiv preprint /
   2026 Cell paper (Marin-lab-style MANC + male-CNS cross-match, "The
   Comprehensive Drosophila Taste-Feeding Connectome" /
   "The complete gustatory connectome of adult Drosophila") assigns modality
   to most but not all of the named leg/wing GRN types the model uses:
   LgAG1 = bitter/aversive (Gr33a+), LgAG2 = appetitive (Gr61a+), LgLG4 =
   sugar + low salt (Gr64f+/Ir56b+), LgLG1a/1b/2 and LgLG5-8 = contact-
   pheromone types (ppk23+/ppk25+/fru+ combinatorics, Ir52a+), WG2 = sugar,
   WG1/WG3/WG4 = pheromone/courtship. **LgLG3 and LgAG3-9 modality: NOT
   FOUND** in the text WebFetch returned — the source may map them in a
   figure/table I did not get rendered; needs a second pass with the actual
   PDF. This is enough to stop giving every leg GRN an equal weak response
   to all 5 tastants: the model can now route sugar response preferentially
   to LgLG4/WG2, bitter to LgAG1, and leave the pheromone types (which are
   not one of the model's 5 "tastants" at all) at zero/separate channel
   rather than forcing them into the sugar/water/bitter/salt/amino-acid
   basis.

2. **Dose-response.** Ling et al. 2014 (J Neurosci 34:7148-7164, open
   access PMC4028494) is a single-concentration screen (100 mM sugars, 1-10
   mM bitter compounds, 25-50 mM amino acids) across tarsal sensillum
   classes, **not a concentration series** — so there is no EC50/half-max
   for any leg GRN in this paper, contrary to the brief's hope. Max firing
   rates at that one concentration are tens of spikes/s (same order as
   labellar sweet/bitter GRNs), directly contradicting the model's current
   "weak response to all tastants" guess at the top end, but the model's
   half-saturation constant (0.05 M) has **no support found** either way
   because no multi-concentration leg data turned up in the budget.

3. **Spontaneous rate.** Ling 2014 states spontaneous/vehicle-only firing
   is "very low" (<3 spikes/s in the control condition in Table 2), same
   order as labellar GRNs; no separate quantitative spontaneous-rate value
   for leg GRNs specifically was found elsewhere.

Bottom line for `extrasenses.py`: there is now a real basis to (a) stop
applying one weight to all 5 tastants for every leg GRN type and instead
zero out sugar/bitter/salt drive for the pheromone-coded types (LgLG1a/1b,
LgLG2, LgLG5-8, WG1/WG3/WG4) and route sugar preferentially through
LgLG4/WG2 and bitter through LgAG1/LgAG2; (b) raise the leg sweet/bitter
GRN max response toward the labellar 15 mV order (Ling's spike rates are
comparable to labellar, not obviously weaker) rather than the current 0.2x
blanket discount; but (c) the 0.05 M half-saturation constant for leg GRNs
remains a guess — no dose-response curve for any leg GRN was located.

---

## Table 1 — connectome type → modality

| Type | n (brief) | Modality found | Basis / status |
|---|---|---|---|
| LgAG1 | ? | bitter / aversive | Gr33a-GAL4 match, Fig 5G — READ (WebFetch quote) |
| LgAG2 | ? | appetitive (non-bitter) | Gr61a-GAL4 match, Fig 5G — READ (WebFetch quote) |
| LgAG3-9 | 3-25 ea. | NOT FOUND | not in extracted text; "9 lgAGRN types (LgAG1-9)" counted but only 1,2 named |
| LgLG1a | 136 | contact pheromone | VGlut-/fru+/ppk23+/ppk25- — SECONDARY (WebFetch quote) |
| LgLG1b | 134 | contact pheromone | VGlut+/fru+/ppk23+/ppk25+ — SECONDARY |
| LgLG2 | 130 | contact pheromone | Ir52a-GAL4 match, Fig 6I — SECONDARY |
| LgLG3 | 162 | NOT FOUND | no explicit gene/modality match surfaced |
| LgLG4 | 43 | sugar + low salt | Gr64f-GAL4 and Ir56b-GAL4 match, Fig 6I — READ (WebFetch quote) |
| LgLG5-8 | 13/16/21/14 | male-specific contact pheromone | "sexually dimorphic... taste bristles that exist solely in males" — SECONDARY, not individually gene-matched |
| WG1 | ~96 | courtship pheromone | fru+/Ir52a+ match, Fig S6A — SECONDARY |
| WG2 | ~96 | sugar | "likely to detect sugar and trigger feeding" — SECONDARY, no gene named |
| WG3 | ~96 | contact pheromone | VGlut+/fru+/ppk23+/ppk25+ — SECONDARY |
| WG4 | ~96 | contact pheromone | VGlut-/fru+/ppk23+/ppk25- — SECONDARY |

Source: bioRxiv 2025.08.25.671814 "From Sensory Detection to Motor Action:
The Comprehensive Drosophila Taste-Feeding Connectome" (preprint of
Cell (2026) "The complete gustatory connectome of adult Drosophila reveals
how taste guides feeding, foraging, and social behavior",
https://www.cell.com/cell/fulltext/S0092-8674(26)00943-8,
https://www.biorxiv.org/content/10.1101/2025.08.25.671814). Cross-matches
MANC and male-CNS (maleCNS) connectomes. I could not get the PDF rendered
directly (10 MB size limit on WebFetch) — all quotes below came from
WebFetch summarizing the bioRxiv HTML mirror, so treat as SECONDARY pending
a manual read of Figs 5-6 and their legends.

Also found but not separately quoted: Cheong et al. 2024 (MANC connectome
descriptive paper, Nature; and the companion "Comparative connectomics of
Drosophila descending and ascending neurons" Nature 2025,
https://www.nature.com/articles/s41586-025-08925-z) establish the
leg-ascending-GRN (lgAGRN, -> SEZ via cervical connective) vs
leg-local-GRN (lgLGRN, confined to T1-3 VNC) distinction the brief's LgAG/
LgLG naming follows, and give the "67 single-leg-local neuron types (448
neurons), 75 leg-interconnecting types (231 neurons)" premotor-circuit
counts — these are leg *premotor* counts, not GRN counts, included here
only because they confirm the LgAG/LgLG anatomical split is real and
independently described outside the taste-connectome paper.

## Table 2 — dose-response / firing-rate numbers

| Prep | Stimulus | Conc. | Rate (spikes/s, mean ± SEM) | Sensillum | Status |
|---|---|---|---|---|---|
| Ling 2014, tip recording | sucrose | 100 mM (single point) | 51.7 ± 3.0 | f5s | SECONDARY |
| Ling 2014 | sucrose | 100 mM | 54.5 ± 3.2 | f4s | SECONDARY |
| Ling 2014 | sucrose | 100 mM | 50.2 ± 4.4 | f5b | SECONDARY |
| Ling 2014 | sparteine (bitter) | 1-10 mM range | 48.8 ± 2.0 | f5s | SECONDARY |
| Ling 2014 | aristolochic acid (bitter) | 1-10 mM range | 41.4 ± 3.7 | f5s | SECONDARY |
| Ling 2014 | vehicle (TCC) only | 0 | <3 (SECONDARY reading of Table 2) | pooled | SECONDARY |
| Ling 2014, comparison | aristolochic acid, labellar | — | 13 (max, sensillum S3) | labellar S3 | SECONDARY quote, see below |
| Ling 2014, comparison | saponin, labellar | — | 52, labellar S5; "essentially no response" tarsal | labellar S5 vs tarsal | SECONDARY quote |

No multi-point concentration series (needed for an EC50 / half-saturation
constant) was located for any leg or wing GRN within the search budget.
Ling et al. 2014 tested a single concentration per tastant class (100 mM
sugars, 1-10 mM bitter compounds depending on solubility, 25-50 mM amino
acids) — this is stated directly in the WebFetch extraction and is
consistent with the paper being a cell-typing/mapping study, not a
dose-response study.

**Not reached in this budget (NOT SEARCHED, not NOT FOUND):** Meunier et
al. 2003, Miyazaki & Ito 2010, Thoma et al. 2016 (Nat Commun — functional
imaging, could plausibly contain a leg-GRN dF/F-vs-concentration curve
rather than spike rate), Dahanukar et al. 2007, Hiroi et al. 2002, Chen &
Amrein 2017, Jeong et al. 2016, Moon et al. 2006. The coordinator cut the
session short after one WebFetch timeout; these are the next things to
pull if a labellar-vs-leg half-saturation comparison is still wanted.

## Table 3 — sensillum classification / counts (Ling 2014, female, SECONDARY)

| Leg | approx. sensilla count |
|---|---|
| Foreleg | ~28 |
| Midleg | ~21 |
| Hindleg | ~22 |

Six functional response classes on the foreleg per the WebFetch summary:
A1 (f5s only), A2 (f4s, f5b), B (f4b, f3b, f2b), C (unresponsive), plus f5v
and f4c treated as distinct. These counts are per-leg total tarsal
sensilla (not GRN cell count; each sensillum houses ~2-4 GRNs), so they are
not directly comparable to the MANC per-cell-type counts in the brief
(136, 134, 130... for LgLG1a etc.) without a mapping step this search did
not reach.

---

## Quotes

All quotes below are as returned by WebFetch's fetch-and-summarize pass
over the cited page; I did not independently re-open the raw PDF/XML
(two direct attempts — jneurosci.org full text: HTTP 403; Europe PMC
fullTextXML for PMC4028494: HTTP 500 — both failed before the coordinator
asked me to stop extending the search). Status markers follow the
READ / SECONDARY / NOT FOUND convention from the brief; "SECONDARY" here
specifically means "WebFetch-summarized quote from the correct cited
source, not yet re-verified character-for-character against the typeset
original."

### Connectome / modality (bioRxiv 2025.08.25.671814)

> "we have been able to match the Gr33a-GAL4 driver projection pattern to
> LgAG1 neurons" (Fig. 5G) — SECONDARY

> "we have also matched Gr61a-GAL4 positive lgAGRNs to the LgAG2 type,
> suggesting that this GRN type senses appetitive tastants" (Fig. 5G) —
> SECONDARY

> "we propose that those molecular identities correspond to the LgLG1a and
> LgLG1b types" [VGlut+/fru+/ppk23+/ppk25+ and VGlut-/fru+/ppk23+/ppk25-]
> — SECONDARY

> "we have anatomically matched the LgLG2 type to Ir52a-GAL4 positive
> lgLGRNs" (Fig. 6I) — SECONDARY

> "we have matched the anatomy of LgLG4 GRNs to GR64f- and Ir56b-GAL4
> positive lgLGRNs" (Fig. 6I) ... detecting "sugar and low salt" —
> SECONDARY

> "these contralaterally projecting neurons are sexually dimorphic,
> projecting from taste bristles that exist solely in males" [LgLG5-8] —
> SECONDARY

> "nine lgAGRN types (LgAG1-9)" with counts "essentially consistent across
> the two connectomes" (Fig. 5F) — SECONDARY

> "LgLG1 is the type with the most neurons, while LgLG4 is the type with
> the fewest" (Fig. 6J) — SECONDARY (note: this ranks LgLG1 vs LgLG4 only;
> does not itself give the LgLG5-8 ranking in the brief's count table)

> "different wGRN types are basically formed by the same number of
> neurons (48-50 GRNs on each side)" (Fig. 6E) — SECONDARY (brief's ~96
> total per WG type = 2 x 48-50 sides, consistent)

> "we propose that these GRNs are the previously identified
> courtship-promoting fru+/Ir52a+ GRNs" [WG1] (Fig. S6A) — SECONDARY

> "we propose that the WG2 GRNs are likely to detect sugar and trigger
> feeding." — SECONDARY

> "we propose that the WG3 type corresponds to the VGlut+/fru+/ppk23+/
> ppk25+ GRNs and the WG4 type to the VGlut-/fru+/ppk23+/ppk25- GRNs." —
> SECONDARY

> "The document contains no dose-response curves, firing magnitude
> measurements, or direct physiological comparisons between leg/wing and
> labellar GRN responses." — WebFetch's own summary statement, i.e. this
> connectome paper is anatomy/connectivity only, no electrophysiology.

### Dose-response / spontaneous rate (Ling et al. 2014, J Neurosci
34:7148-7164, PMID 24849350, PMCID PMC4028494, DOI
10.1523/JNEUROSCI.0649-14.2014 — open access, not paywalled)

> "Aristolochic acid elicits a much stronger response from a foreleg
> sensillum (f5s) than from any labellar sensillum (13 spikes/s maximum,
> from S3)." — SECONDARY

> "52 spikes/s from the labellar sensillum S5" [saponin] but "essentially
> no response from any tarsal sensillum tested." — SECONDARY

> "A very low level of spontaneous firing was observed when TCC was tested
> alone, without any sugar or bitter compounds." — SECONDARY

> f5s/f4s/f5b sucrose rates and f5s sparteine/aristolochic-acid rates:
> "51.7 ± 3.0", "54.5 ± 3.2", "50.2 ± 4.4", "48.8 ± 2.0", "41.4 ± 3.7"
> spikes/s, attributed to "Table 2" — SECONDARY, numbers not yet
> cross-checked against the typeset table.

No DOI access problem for Ling 2014 — it is fully open access on PMC; the
403 was jneurosci.org's own anti-bot block, not a paywall. A follow-up pass
should fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC4028494/ at smaller
scope (e.g. just Table 2 and the Methods concentration list) rather than
the whole article, and should also pull the actual PDF table image if the
HTML table doesn't render for WebFetch.

### Not reached

Meunier et al. 2003, Miyazaki & Ito 2010, Thoma et al. 2016, Dahanukar et
al. 2007, Hiroi et al. 2002, Chen & Amrein 2017, Jeong et al. 2016, Moon et
al. 2006, Stürner et al. 2025, Marin et al. 2024, Shiu et al.,
Pfeiffer/Wang/Montell tarsal sensilla maps — NOT SEARCHED, time budget.
