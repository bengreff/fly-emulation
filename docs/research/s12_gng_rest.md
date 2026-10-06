# S12: resting activity of GNG feeding-circuit cells (for the leg sugar route bracket)

Why: the leg sugar route opens when its 43 cells sit 1 mV below their own rheobase and stays shut at the
model's default rest, 7 mV below threshold (DECISIONS 6 October 00:05 and its result). The measurable
counterpart is the resting potential against threshold, or the spontaneous rate, of a GNG route cell.

A Sonnet agent searched (6 October, about 00:06 to 00:22). It was read-only, so no texts were
saved to `data/raw/gng_rest_s12/`; it read the sources below by fetch. Labels: **agent read** = the
agent reports reading the full text and I did not re-read it; **I read** = I checked the text myself;
**unverified** = abstract or search summary only.

## Answer

**No resting rate, and no resting potential against threshold, was found for any adult GNG
feeding-circuit cell:** not for second-order taste cells, MN9/MN11/MN12, feeding premotor cells, or
DNg/DNge descending cells. The papers that would hold one used calcium imaging, anatomy or optogenetics.

| Paper | What it has | Label |
|---|---|---|
| Schwarz et al. 2017 eLife 6:e19892 (PMC5315463), feeding motor neurons MN1-MN12 | genetics, optogenetics and behaviour; no electrophysiology | agent read |
| Shiu et al. 2022 eLife 11:e79887, taste quality and hunger in a feeding circuit | GCaMP6s imaging only; no patch or rate | agent read; I searched the local text (`data/raw/shiu2022/s.txt`) for electrophysiology, patch, whole-cell and tonic, and found none |
| Kim, Kirkhart & Scott 2017 eLife 6:e23386 (PMC5310837), taste projection neurons | imaging and behaviour only | agent read |
| Sterne et al. 2021 eLife 10:e71679, GNG cell types | anatomy and driver lines; full text did not load | unverified |
| Jourjine et al. 2016 Cell, hunger and thirst sensing cells (ISNs) | no electrophysiology indicated | unverified |
| Tastekin et al. (bioRxiv 2025.08.25.671814 v2), taste connectome | EM only | agent read; consistent with my earlier read |
| Hugin feeding motor programme (PMC4068981) | larval; fold changes only | agent read; out of scope |
| Sui et al. 2026 Nat Neurosci (PMID 42637923), "Motor neurons organize Drosophila feeding sequences via a disinhibitory cascade" | search summaries describe cell-attached recordings of spontaneous rates in adult feeding motor neurons, then whole-cell recordings | unverified: paywalled, and no open copy found. **The lead.** |

## What this settles

- The route bracket's `near` arm (1 mV below rheobase, silent) has no measured GNG counterpart to check
  against. The only central resting numbers in reach are outside the GNG: 0.1-1.4 Hz for LH and AL cells
  (Frechter 2019), 3.9 Hz for P-EN (Turner-Evans 2017), and 12.1 Hz for MBON-α3 (Hafez 2023), all in
  `docs/research/s12_central_fi.md`.
- The settling measurement stays on Ben's list: a cell-attached rate, or a whole-cell resting potential
  and threshold, from Roundup (GNG108) or Bract (DNge173/DNge174) in a fed and in a starved fly.
- Sui et al. 2026 (DOI 10.1038/s41593-026-02412-y) is published only in Nature Neuroscience; a search on
  6 October 00:23 found no preprint. If an open copy appears, its MN9 or premotor resting rates would be
  the first measured GNG number.
