# Literature pass: amine release rate per neuron (Open 6), session 5, 9 Nov 2026 02:1x CST

One Sonnet agent (Explore, foreground, read-only; it wrote one stray stub file to /tmp, since removed by wneuro).
Its full report is below the verification notes. Free sources only.

## wneuro's verification (what may be used)

- Borue, Cooper, Hirsh, Condron, Venton 2009 J Neurosci Methods 179:300 (PMC2691387). Opened by wneuro through the
  NCBI BioC open-access service (PMC's page served a bot check). Quotes confirmed verbatim:
  "The wandering third instar Drosophila VNC neuropil contains an average of 12 varicosities per 1,000 um3, which are
  putative serotonin release sites. If every varicosity released one vesicle containing 4,700 molecules of serotonin,
  the resulting concentration in the sampling volume would equal 450 nM. We detected serotonin concentrations ranging
  from 280 to 640 nM following 2s to 30s of blue light exposure." ... "Therefore, on average, during maximal
  stimulation each varicosity releases 1.5 vesicles."
  "The two second-long stimulation elicits roughly half the peak serotonin concentration as seen with 10 s. The peak
  concentration for a 10 s stimulation is about equal to that using 30 s ... uptake probably acts to clear some of the
  serotonin during the stimulation, leading to a steady-state concentration."
  "Vmax was estimated as 170 +/- 40 nM/s and KT as 350 +/- 80 nM".
  Caveat, verbatim: "Some varicosities may not be stimulated, so the actual amount released per activated varicosity
  may be greater. Additionally, reuptake acts to decrease the observed peak concentration, likely causing an
  underestimation of actual release."
  Derived by wneuro (cross-species, Drosophila larval VNC, ChR2 in serotonergic neurons, maximal optogenetic drive):
  - implied volume fraction in their 450 nM: 4700 / (450 x 83.3 um3 x 0.602) = 0.21;
  - 2 s stimulus: 280 / 450 = 0.62 vesicles in 2 s, 0.31 per s, x 4700 = about 1.5e3 molecules/s per varicosity;
  - plateau (release = uptake): uptake at 640 nM from their fit with Hill 1 (the Hill number is not in the text),
    170 x 640 / (350 + 640) = 110 nM/s; 110 / 450 x 4700 = about 1.1e3 molecules/s per varicosity (0.9e3-1.4e3 over
    Vmax +- 40);
  - so at least about 1e3-1.5e3 molecules/s per activated release site at maximal drive (a lower bound by the paper's
    own caveat; no upper bound from this paper).
- Borue, Condron, Venton 2010 J Neurochem 113:188 (PMC2860618): replenishment of the releasable pool on the 1-10 min
  scale (agent CONFIRMED; not re-opened by wneuro; not used for a number).
- Wang et al. 2017 JBC 292:5943 (PMC5392585): whole-worm 5-HT 258 ng/g etc. NOT verified by wneuro (PMC bot check,
  Europe PMC full text 500, efetch front matter only, JBC blocked); units ("per g" of what) not confirmed. Not used.
- Zhou et al. 2007 Neuron 56:657 (amperometry of C. elegans serotonergic neurons in culture): paywalled, no free copy.
  The one C. elegans measurement that could pin release per event. Not used.

## The agent's summary table and gaps (verbatim; its long per-question text is not kept)

| Q | Finding | Number/units | Source | Status |
|---|---|---|---|---|
| Q1 | Whole-worm 5-HT, 5-HIAA steady-state pools (not a rate) | WT 5-HT 258±14 ng/g; WT 5-HIAA 0.64±0.45 ng/g; grk-2 5-HT 5.9±0.9 ng/g, 5-HIAA 168±22 ng/g; amx-2 5-HT 330±14 ng/g, 5-HIAA 0.08±0.01 ng/g | Wang et al. 2017 JBC, PMC5392585 | CONFIRMED (paper opened; exact decimals not independently re-grepped by me — PLAUSIBLE on precision) |
| Q1 | No C. elegans 5-HT turnover/synthesis rate exists in literature searched | — | — | NOT FOUND |
| Q1 (fallback) | Releasable 5-HT pool replenishment time scale, Drosophila | ~1–2 min (reuptake-dominated) to ~5–10 min (synthesis-dominated) full recovery | Borue, Condron & Venton 2010 J Neurochem, PMC2860618 | CONFIRMED |
| Q2 | No C. elegans DCV exocytosis rate (events/s or molecules/s) found | — | — | NOT FOUND |
| Q2 | Molecules per small (SV-type) serotonin vesicle, leech, cited in fly paper | 4,700 molecules/vesicle | Bruns & Jahn 1995 Nature, cited in Borue et al. 2009 J Neurosci Methods PMC2691387 | CONFIRMED |
| Q2 (fallback, derived) | Serotonin release rate per varicosity, Drosophila larval VNC, near-maximal optogenetic drive | ≈235 molecules/s per varicosity (DERIVED: 1.5 vesicles × 4,700 molecules ÷ 30 s) | Borue et al. 2009, PMC2691387 | CONFIRMED source numbers; DERIVED arithmetic is the agent's (wneuro's note above supersedes it: the 30 s peak is a release-uptake steady state, not the total released) |
| Q2 | Vmax of serotonin reuptake/clearance, Drosophila VNC | 170 ± 40 nM/s | Borue et al. 2009, PMC2691387 | CONFIRMED |
| Q3 | CAT-1::GFP (VMAT) concentrated at HSN vulval presynaptic region | qualitative | Huang et al. 2023 Curr Biol, PMC10860333 | CONFIRMED |
| Q3 | No direct test of unc-31 vs unc-13 dependence of HSN 5-HT release found | — | — | NOT FOUND |
| Q3 | DCV marker (ANF::GFP) release requires UNC-31, reduced by unc-13(s69), generically | relative fluorescence (WT=100) | Speese et al. 2007 J Neurosci, PMC6672138 | CONFIRMED |
| Q4 | Amperometry of serotonin release from cultured C. elegans tph-1::GFP neurons exists | unc-13 loss "severely abolished" release, unc-31 loss minor (~15%, unverified) | Zhou et al. 2007 Neuron 56:657–669 | PAYWALLED, numbers UNCONFIRMED |
| Q4 | No FSCV data on any C. elegans neuron found | — | — | NOT FOUND |

Not found: any per-neuron or whole-worm 5-HT synthesis flux; any 13C/15N-Trp pulse-chase; any PCPA time course in
C. elegans; any conditional tph-1 time course; any DCV fusion rate in a C. elegans neuron (only endpoint relative
assays); any EM count of DCVs per HSN, NSM or ADF; any direct test of unc-31 / unc-13 dependence of HSN 5-HT release;
any FSCV in C. elegans; verified numbers from Zhou 2007 (paywalled). Blocked: wormbook.org monoamines chapter (403),
Duerr et al. 2001 AJP-Cell (403), Zhou 2007 (Cell, 403).
