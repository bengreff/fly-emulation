# S12: intrinsic properties of adult central neurons (for the central BK question)

Why: the leg sugar route is blocked by the rung-1 BK carried to central cells at the class prior, which
was fitted on slow leg motor neurons (DECISIONS 23:26). Setting BK for central cells separately needs
current steps in some adult central neuron: a firing rate against injected current (f-I), the spike
afterhyperpolarisation (AHP), adaptation, with input resistance and time constant in the same cells.

A Sonnet agent searched (5 October, 23:18-23:27); full texts saved under `data/raw/central_fi_s12/`
(gitignored). I re-read every number below in the saved text. Labels: **read** = I read the sentence;
**figure only** = the paper has it in a figure or a supplement I could not open; **unverified** = snippet.

| Cell | Quantity | Value | Prep | Label | Source |
|---|---|---|---|---|---|
| AL projection neuron (PN) | input resistance | 598.0 ± 69.3 MΩ, n 14, antennae removed | in vivo whole-cell | read | Gouwens & Wilson 2009 J Neurosci 29:6239 (PMC2709801) |
| PN | seal resistance | 10.1 ± 1.6 GΩ, n 13 | same | read | same |
| PN | true resting potential, seal-corrected | about −55 to −60 mV with ORN input, about −65 mV without | estimate from a circuit model | read | same |
| PN | spike threshold at the initiation zone | "assuming a spike threshold at the SIZ near −40 mV" | an assumption, not a measurement | read | same |
| PN, LH local, LH output | baseline rate | 1.4, 1, 0.1 Hz | in vivo | read | Frechter et al. 2019 eLife 8:e44590 (PMC6550879) |
| PN, LH output | odour-evoked rate, significant responses only | 21 and 14 Hz | in vivo | read | same |
| LH neurons against PNs | input resistance, capacitance | "much higher Rin and lower Cm" (no number in text) | in vivo | figure only | same, Fig. 4D |
| l-LNv | resting potential, firing, membrane resistance across the day | hyperpolarise dawn to dusk, firing and resistance fall; depolarise dusk to dawn | brain explant | read (direction) | Cao & Nitabach 2008 J Neurosci 28:6493 (PMC2680300) |
| l-LNv | subthreshold oscillation | 0.28 ± 0.18 Hz, 7.4 ± 3.5 mV peak to trough (35 of 58 cells) | same | read | same |
| s-LNv | resting potential across the day | "highest around lights-on"; falls ZT0-6, rises ZT18-24 | same | read | same |
| DN1p | spontaneous firing | "fire at ∼10Hz in the morning (Zeitgeber Time, ZT0-4) and are nearly silent in the evening (ZT8–12)" | brain explant, whole-cell and cell-attached | read | Flourakis et al. 2015 Cell 162:836 (PMC4537776) |
| DN1p, *per*⁰¹ | firing, potential | 2.2 ± 1.1 Hz, −56 ± 2 mV (n 15, ZT0-4); 3.9 ± 1.5 Hz, −55 ± 1.9 mV (n 10, ZT8-12) | same | read | same |
| DN1p | response to depolarising current | "more responsive to depolarizing currents in the morning than in the evening"; input resistance has no daily rhythm | same | read (direction); numbers in Table S.2A, figure only (supplement behind a PMC download wall; Europe PMC: not open access) | same |
| Kenyon cell | input resistance | "> 10 GΩ" | in vivo | unverified (no open full text) | Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734 |

Correction to the agent's report: it gave DN1p as "~7 Hz (day) to 0.5-2 Hz (night)". Those numbers are
from the paper's model of a mouse SCN neuron (Fig. 7J), not from fly cells. The fly numbers are in the
DN1p row above.

## What this settles

- **No adult central f-I curve or AHP number was found in open text.** None of the six papers reports a
  rheobase, an f-I slope, an AHP amplitude or decay, or an adaptation ratio for a central cell. The one
  current-step dataset in reach (DN1p, Flourakis Table S.2A) is in a supplement that is not open.
- So a sourced central BK is **not possible from this search**. The class prior stays, and the leg sugar
  diagnosis stays diagnostic (DECISIONS 23:26).
- PN input resistance (about 600 MΩ) is close to the model's slow leg MN template, so passive size does
  not argue for a different central gain. That is no evidence about BK either way.

## A sourced check this search did give: the clock

DN1p firing (about 10 Hz at ZT0-4, nearly silent at ZT8-12) is a direct target for the N26 clock coupling,
which drives DN1pA/DN1pB, s-LNv and l-LNv as the morning group (`g_clock_mv` 3 mV, peak CT 2 h, both
guessed). The s-LNv and l-LNv directions (depolarised around lights-on, hyperpolarising through the day)
agree with a morning peak near CT 0-2. Tested in `scripts/probes/clock_phase_rates.py` (below).

Result (5 October 23:40-23:50; DECISIONS 23:34, its result and the m9c addendum; FINDINGS F-CLOCK-1):

- Under m9r the clock drive is subthreshold: DN1p 0 Hz at CT 2 and CT 10 (fails the 5-20 Hz morning target).
- Fit: `g_clock_mv` 7.75 (inferred, fitted) gives 11 Hz at CT 2 and 0 Hz at CT 10. The onset spans 0.25 mV
  (1 Hz at 7.5, 11 Hz at 7.75), so this target is fragile.
- With the run starting at the specimen's ZT 1.5 (`state:clock|initial_ct`), DN1p fire about 4 Hz in the
  closed loop. Gate and posture are unchanged from m9r (seeds 12-19).
- *per*⁰¹ (2-4 Hz with no rhythm) is not matched: the model's clock-less DN1p is silent.

## Second search (5 October 23:30-23:50) and the MBON-α3 check

A second Sonnet search (texts in `data/raw/central_fi_s12/`; every quote below re-found in the saved text)
added:

| Cell | Quantity | Value | Label | Source |
|---|---|---|---|---|
| MBON-α3 | τm, Rm, Cm | 16.06 ± 2.3 ms; 926 ± 55 MΩ; 16.76 ± 1.90 pF (n 4-5, EGFP cells) | read | Hafez et al. 2023 eLife 12:e77578 (PMC10069864) |
| MBON-α3 | resting potential, spontaneous rate | −56.7 ± 2.0 mV; 12.1 Hz | read | same |
| MBON-α3 | f-I, 400 ms steps, −26 to +32 pA | onset −6 to +2 pA; 20, 50, 30 Hz at +32 pA (3 cells) | figure estimate (Fig. 1 supp. 1C, image from eLife IIIF, CC BY) | same |
| MBON-α3 | deflection at −10 pA in the f-I cells | about −17, −17, −25 mV | figure estimate (supp. 1E) | same |
| MBON-α3 | adaptation | "a spike-frequency adapting neuron" (no ratio) | read | same |
| l-LNv | Rin, C | 305 ± 30 MΩ, 12 ± 2 pF (n 4) | read | Sheeba et al. 2008 J Neurophysiol 99:976 (PMC2692874) |
| l-LNv | AHP amplitude | 3-5 ± 1 mV (n 6, 7), no light dependence | read | same |
| AL local neurons | Rin | 1-4 GΩ (n 7) | read | Wilson & Laurent 2005 J Neurosci 25:9069 |
| P-EN | Rin; loose-patch rate | 1.9 ± 0.8 GΩ; 3.9 ± 2.6 Hz standing | read | Turner-Evans et al. 2017 eLife (PMC5440168) |
| PN (model) | steady soma-to-SIZ transfer | "∼40–70% of its original amplitude" | read | Gouwens & Wilson 2009 |

MBON-α3 is the first adult central cell with a current-step f-I in reach. It carries the class prior in
the model (no transcriptome row), so it tests exactly the BK value at issue. Result (DECISIONS 23:56 and
its result; F-FI-1): the model's MBON14 is 2-5× steeper than the recording with BK on, and steeper still
with BK off. So the data argue against removing central BK. The l-LNv AHP (3-5 mV at the soma) is not used:
soma AHPs in cells with a remote initiation zone are attenuated, and the model has one compartment.

**Adaptation in the MBON-α3 traces** (6 October, by eye, from Fig. 1 supp. 1A-B, figure estimate). At the
largest steps, cells 2 and 3 fire spikes at nearly even intervals from the first spike, about 20-50 ms after
step onset, to the end of the 400 ms step. Any adaptation within 400 ms is weak, although the text calls the
cell "a spike-frequency adapting neuron". No figure here shows adaptation over seconds.

**What MBON-α3 rest looks like** (Fig. 1E, by eye; figure estimate; ex vivo whole-cell, read).
- The 2 s example trace fires regularly, about 11 spikes (about 5.5 Hz; the text's mean is 12.1 Hz).
- Between spikes the membrane ramps from about −53.5 to −51 mV, then fires. Fluctuations on the ramp are
  about 0.5 mV or less.
- So this cell's resting activity looks like slow regular pacemaking above threshold, not noise-driven
  crossings from below. Ex vivo the synaptic noise is lower than in vivo, so this bounds the intrinsic
  part only.
- For the model: a near-threshold cell made to fire by 2-4 mV of membrane noise
  (`scripts/probes/noise_rest.py`) would look different from this trace. A small tonic suprathreshold
  drive with an AHP would look like it.
