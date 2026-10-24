# s23 N1: recorded firing modes, second compile (24 October 2026)

Sonnet reader (Explore, 24 Oct). The task was to find every adult *Drosophila* type whose spiking or graded mode
comes from electrophysiology, beyond the existing `graded_rec` rows. Rows were then added only under the rule
fixed in DECISIONS 24 Oct 00:20, before the reader reported:

- a primary adult recording (whole-cell, sharp electrode or isolated unit) is required; calcium imaging alone does not count;
- rows are written only where they change the model;
- contested types and graded-with-spikelets types get no row and are listed here as validity limits.

Two sources were read in open full text: Agrawal et al. 2020 (eLife 9:e60299, PMC7752136) and Schenk & Gaudry 2023
(eNeuro 10:ENEURO.0109-22.2022, PMC9884108). The main agent then rechecked Schenk & Gaudry (quotes below). Every
other source came from abstracts or search summaries because the full text was paywalled or would not download.
Those sources are labelled secondary, and none of them was used for a row.

**Result: no new rows.** m10f9 runs with the rows listed in DECISIONS 24 Oct 00:20.

## Recorded spiking types: no row, because the model already spikes them

Under m10f8/m10f9 every unknown-mode group (`mode:n1_p_graded_*`) is at its neutral 0 (spiking). A spiking row
for these types would therefore change nothing. They would need a row only if a group default ever became graded.

| Type (connectome) | Source | Method | Text status |
|---|---|---|---|
| IN09A (9Aalpha) | Agrawal 2020 | whole-cell, adult female 1-3 d | open text: "responded to tibia movement through changes in membrane potential and action potential firing rate" |
| panglomerular AL LNs (R70A09, NP3056) | Schenk & Gaudry 2023 | in vivo whole-cell, 1-2 dpe | open text: odor-evoked "large spikes", abolished by TTX; TTX-sensitive Na currents |
| KCs | Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734 | in vivo whole-cell | secondary |
| uniglomerular PNs | Wilson, Turner & Laurent 2004 Science 303:366 | in vivo whole-cell | secondary |
| LHNs | Fisek & Wilson 2014 Nat Neurosci 17:280 | paired in vivo whole-cell | secondary |
| MBON-a3 | eLife 2023 12:e77578 | ex vivo whole-cell | secondary |
| l-LNv | Sheeba et al. 2008 J Neurophysiol 99:976; Cao & Nitabach 2008 J Neurosci 28:6493 | whole-cell current clamp, brain explant | secondary |
| DN1p | Flourakis et al. 2015 Cell 162:836 | whole-cell | secondary |
| GF, DNg13, other DNs | von Reyn et al. 2014; Dickinson lab DN papers | whole-cell | secondary, citations not pinned |

## Recorded non-spiking with no connectome mapping: no row (a candidate)

Schenk & Gaudry 2023 recorded R32F10-Gal4 patchy LNs in vivo by whole-cell patch at 1-2 dpe. The main agent's
recheck quotes: "we did not detect action potentials nor sodium current in R32F10-Gal4 patchy LNs"; "we failed to
observe any TTX-sensitive currents in the cells" (n = 9 in voltage clamp, Fig. 1K). The paper does not map these
cells to a connectome type. Schlegel et al. 2021 (eLife 10:e66018) uses the Chou 2010 morphological classes
(broad, patchy, regional, sparse), but its main text does not say which connectome types are patchy. The connectome
has `lLN2P_a/b/c` (28 cells in the `n1_p_graded_al_ln` group), but the meaning of the letter P was not verified.
Writing a row would mean guessing which cells the driver labels, so no row is written.

**What would decide it:** a per-type morphological class table for the ALLN types (Schlegel 2021 supplement or its
code repository), or an R32F10 to connectome match. With one of these, the row would be `lLN2P_*`, graded_rec 1,
labelled inferred (measured for the R32F10 cells and extended by morphological class).

## Validity limits (no row, by the rule)

- **HS, VS (LPTCs):** graded with spikelets or occasional action potentials. Mixed mode, secondary text.
- **IN10B (10Balpha):** Agrawal 2020 open text: "current injection failed to evoke identifiable action potentials,
  though we did occasionally observe spike-like events". By the 00:20 rule this is graded-with-spikelets. The
  existing s13 `^IN10B\d+$` graded row predated the rule and was listed in the m10f9 registration, so it stayed for
  that stage. m10f9 then failed gate G with a VNC runaway (DECISIONS 24 Oct 00:29). The row was removed for stage
  m10f9b, registered as applying the rule after the failure was seen (row text in git at 676b47f). IN10B keeps its
  group mode (spiking) as a validity limit.
- **LPi (e.g. LPi4-3):** non-spiking per Mauss et al. 2015 Cell 162:351, but secondary (paywalled).
- **AL LN classes of Seki et al. 2010 (J Neurophysiol 104:1007):** all four classes spike (burst or tonic). Secondary.
- **Calcium imaging only, so mode not established:** Mi4, Mi9, Tm4, Tm9 (Arenz et al. 2017); LC4, LC6, LC11, LPLC2
  (only the downstream GF was patched, Ache et al. 2019); E-PG, P-EN, Delta7, FB tangentials (Seelig & Jayaraman
  2015 and later). CX units spike in extracellular recordings (Weir & Dickinson 2015 PNAS 112:E5523), but the units
  were not assigned to types.
- **Nothing found:** T1, T2, T3, C2, C3, Lawf1/2, Dm, Pm; VNC hemilineages 19A, 21A, 8A, 3A, 1A, 6A, 12A, 18B; DANs;
  octopaminergic VPM neurons (Suver et al. 2012 could not be read).

## What this means for N1

Under the 00:20 rule, every recorded type with an established mode either already has its row (R1-R8, L1-L5,
Mi1, Tm1-3, T4, T5, IN13B, IN10B; APL through its `graded` row) or already spikes by default. The open item is the patchy LN
mapping. The 2,969 unknown-mode types stay at the group default (spiking), as Bernoulli unknowns.
