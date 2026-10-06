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
