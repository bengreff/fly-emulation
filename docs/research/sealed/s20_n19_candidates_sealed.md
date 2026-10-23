# S20/N19 held-out candidates — sealed magnitudes

Date written: 2026-10-22 (per `date`). Sealed per instructions — parent/report must not see magnitudes.
Access note: primary publisher pages (Cell Press / ScienceDirect, PubMed abstract pages) returned
HTTP 403 / cookie-wall to WebFetch and to curl-with-browser-UA; figures below are read from
search-engine abstract snippets and from the one accessible PMC/PLOS/Frontiers full texts, not from
the primary PDF/figure panels directly, except where noted "read from full text." Treat accordingly —
some magnitudes are my best reading of abstract language, not a verified figure value.

## 1. Suver, Mamiya & Dickinson 2012, Curr Biol 22(24):2294–2302, doi:10.1016/j.cub.2012.10.034

Not accessible full-text (Cell Press paywall; WebFetch 403 on cell.com and sciencedirect.com). Abstract
language only: octopamine bath/pressure application onto quiescent-fly VS-cell whole-cell recordings
"evokes responses... that mimic those observed during flight," i.e. reproduces the flight-induced boost.
Companion/later papers (Suver et al. 2012 J Neurosci on photoreceptors; Longden & Krapp 2009/2010 on
blowfly LPTCs with CDM) describe the flight/CDM boost in VS cells as on the order of a doubling to several-fold
increase in response amplitude to wide-field motion, and an increase in spontaneous depolarization /
spike-let rate; I could not pin an exact percentage or figure panel for the octopamine-bath condition
specifically (as opposed to the flight condition) from accessible text. Figure believed to be Figure 3 or
4 of the 2012 Curr Biol paper (VS-cell response amplitude, quiescent + octopamine vs quiescent + saline).
Sample size not confirmed from accessible text (typical whole-cell LPTC recordings in this lab's other
papers run n=5–12 cells/flies). FLAG: magnitude and exact figure/n not independently verified here —
re-pull via institutional access or the Dickinson lab site before scoring.

## 2. Suzuki, Schenk, Tan & Gaudry 2020, Curr Biol 30(6):1110–1118.e4, doi:10.1016/j.cub.2020.01.018

Not accessible full-text (403 on cell.com/sciencedirect.com). From abstract/search snippets: a population
of GABAergic antennal-lobe local neurons expresses the high-affinity 5-HT7 receptor and is depolarized by
basal (tonic, non-stimulus-evoked) serotonin; these LNs then deliver GABAergic postsynaptic inhibition onto
projection neurons, producing a "subtractive" (i.e. roughly additive/offset, not multiplicative) reduction
of PN odor-evoked output — abstract frames this as a gain-control subtraction, not a specified percent.
No numeric dose–response or percent change recovered from accessible text. Likely figure: the PN-IPSC or
PN-firing-rate panel showing the subtractive baseline shift (probably Fig. 4–6 range given the e4 extended
figure count) — not confirmed by panel number. Sample sizes not recovered. FLAG: magnitude unverified;
needs primary PDF.

## 3. Sampson et al. 2020, PLOS Genetics 16(8):e1009003, doi:10.1371/journal.pgen.1009003 — OPEN ACCESS, full text read

L2 lamina monopolar neuron, ex vivo exposed-optic-lobe prep, GCaMP6f, 100 µM serotonin via gravity-fed bath
perfusion. Figure 4B: peak ΔF/F = 1.73 ± 0.77 SEM (serotonin) vs −0.03 ± 0.05 SEM (saline control), p=0.0095.
That is roughly a 1.7-unit ΔF/F increase from ~0 baseline — a large, clearly excitatory calcium transient.
n = 4–8 flies per panel (exact n varies 4–8 across Fig 4B/C/D; not broken out further in the snippet I
pulled). T1 (Fig 4D) and L1 (Fig 4C) were also tested; tool-fetch summary stated T1 showed "no significant
effect" and did not give a number for L1 — so only L2 is usable as a positive held-out point; T1/L1 could be
used as a null/negative control point instead (predicted a≈0 net effect on T1 given mixed receptor signs,
consistent with "no effect" — worth a separate held-out null check, not a magnitude check). Fig 6A–B repeats
the serotonin-on-L2 effect in a 5-HT2B mutant background to show it is abolished/reduced — useful as a
second, receptor-specific lever if the model's L2 receptor assignment is weighted toward 5-HT2B.

## 4. Frighetto, Zordan, Castiello, Megighian & Martin 2022, Front Physiol 13:849142, doi:10.3389/fphys.2022.849142 — OPEN ACCESS (PMC9048027), full text read

Ellipsoid-body ring neurons R2 and R5, in vivo bioluminescent Ca2+ imaging (GFP-aequorin, photon counts,
not GCaMP dF/F — a different, lower-SNR readout than fluorescence; keep that in mind for how tight any
match needs to be). 100 µM dopamine bath, 10 min pre-incubation, then challenge stimulus.
- R2 (Fig. 5): challenge = 100 µM nicotine puff. Dopamine pre-treatment enhanced the nicotine-evoked
  photon-count response (excitatory potentiation) and shortened response latency (latency dropped toward
  ~304 s scale per the fetch summary — exact baseline/treated latency pair and the amplitude fold-change
  were not individually itemized in the summary I pulled; re-read Fig. 5 panels directly for the actual
  before/after numbers). Framed as acting via Dop1R1 (Gs/Gq-coupled in this model → sign +1, consistent
  with excitatory direction seen). n = 12 (dopamine) vs 13 (control) flies.
- R5 (Fig. 6): challenge = 250 µM picrotoxin. Dopamine pre-treatment reduced the picrotoxin-evoked photon
  response (inhibitory suppression) and increased response latency — opposite sign from R2. Framed as
  acting via D2R (Gi/o-coupled → sign −1, consistent with the suppressive direction seen). n = 15 (control)
  vs 21 (dopamine) flies.
- Caveat for scoring: both readouts are indirect (dopamine's effect on a *second* drug's evoked response,
  not a direct dopamine-evoked response), and bioluminescence photon counts are nonlinear/slow compared to
  GCaMP — treat the comparison to the model's instantaneous gain multiplier as approximate, and note this
  explicitly if adopted as a held-out test.

## Overall note for scoring

Only candidates 3 and 4 were read from accessible full text; candidates 1 and 2 rest on abstract-level
search snippets only (Cell Press paywall blocked WebFetch and curl-with-UA alike — got a bare cookie-wall
page from pubmed.ncbi.nlm.nih.gov too). Before spending these as held-out evidence, pull the actual PDFs
(library proxy / institutional access / ResearchGate request) for #1 and #2 to confirm figure numbers, n,
and exact magnitudes rather than relying on this sealed note's abstract-level reading.
