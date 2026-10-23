# s22 N25 homeostat: the cheap reads before building mode 1

Written 23 Oct 2026, s22 (the session after s21, same night). Two Sonnet readers (Explore type, no subagents of
their own) read full texts for the open items of `s21_n25_homeostat_scope.md` §5. Neither opened Chowdhury 2023's
data or any rebound magnitude. What each read changed in the build is marked **→**.

## 1. Liu, Liu, Tabuchi & Wu 2016 Cell 165:1347 (PMC4892967)

- **Cell name.** The paper calls the cells "R2" (R69F08-GAL4). Later papers call the same ring neurons R5; the
  male-cns type is ER5. The R2 = R5 = ER5 mapping is **inferred** from that later naming, not stated in the paper.
  **→** recorded in the τ_decay row and in DECISIONS.
- **BRP (Fig. 4).** Raised 2 h after deprivation ends (n 19), back to the rested level 24 h after (n 16). No fold
  changes in the text, so the s21 bracket for τ_decay stands: [2.9, 10.4] h, centre 5.5 h, from reading "still
  up" as ≥ 50 % of the excess left at 2 h and "back" as ≤ 10 % left at 24 h.
- **Firing (Fig. 3).** About 3× higher at ZT13-15 than at ZT0-2 in rested flies. No Hz values in the text.
  **→** training check T4: mean need ZT13-15 / ZT0-2 ≥ 2. If firing is affine in need with a non-negative
  offset, the need ratio is at least the firing ratio; 2 allows for "about".
- **Ca²⁺.** ZT12 above ZT0 and ZT24.
- **Deprivation.** Vortexer 5 s per min, 12 or 24 h. Sex not stated.

## 2. Pimentel et al. 2016 Nature 536:333 (PMC4998959)

- **Restart.** After dopamine switched dFB cells OFF, 7 of 15 cells restarted spiking within the recording, at
  7-60 min, mean 25.86 ± 7.61 (SEM) min. The other 8 recordings ended first; how long they were held is not
  stated (censored).
- **The flies were sleep-deprived for more than 12 h** before recording. Mixed sexes, 3-10 days old.
  **→** the restart rate k_r = 1/25.86 min⁻¹ is the OFF → ON rate at full need (n = 1, inferred), not at rest.
  Mode 1 uses k_on(n) = k_r (1 + γ n) / (1 + γ).
- **Range of k_r.** Upper 1/(mean − 2 SEM) = 0.094 min⁻¹. Lower 0.0106 min⁻¹ = the censored exponential
  estimate 7 / (7 × 25.86 + 8 × 60), if the 8 silent cells were held 60 min. Both are estimates under stated
  assumptions (derived).
- **Not measured:** the fraction of dFB cells ON at any time, and a spontaneous ON → OFF rate. So k_off and its
  light dependence are fitted.

## 3. Donlea et al. 2018 Neuron 97:378 (PMC5779612)

- The helicon cells' fast transmitter is **not identified** in the paper (male-cns predicts ACh for ExR1). The s21
  agent's "glutamate" is not in the text.
- 4 cells, drivers R22H05, R22H10, R24B11, R78A01. No hemibrain or male-cns name; ExR1 = helicon stays inferred.
- Not used in the reduced loop (no helicon node); it matters once ER5's network gain is built.

## 4. Abhilash & Shafer 2024 Sleep 47:zsad277 (PMC11275470)

- Canton-S, w1118 and yw males, about 5 days old, DAM, LD 12:12, 25 °C, 400-500 lux, corn syrup/soy food,
  about 32 flies per strain, the last 4 of 9 LD days.
- Total sleep: "~70 % to 80 %" of 24 h across the three strains (Fig. 1E is a histogram; no per-strain mean or
  SEM in the text), about 75 % pooled. **→** primary training band 1008-1100 min/day (70-80 % of 1440 min,
  capped by the registered 618-1100).
- Day vs night: only qualitative (two sleep phases, Fig. 1B somnograms). No minutes, no bouts. **→** the
  training check stays "night > day"; no split target.
- The reader saved a temporary copy of the XML to /tmp for text search, against its no-write instruction; it
  reported this itself. No repo file was touched.

## 5. Night bout structure (a third Sonnet reader, then my own figure read)

Asked after the fit showed every accepted set consolidating the night. Baseline sleep only; rebound papers barred.
- **Garbe et al. 2015 Biol Open 4:1558 (PMC4728345), Fig. 2.** iso31 virgin males, 24 h on sucrose/agar,
  classic single-beam DAM (SB) against multibeam (MB). Means ± s.d. read off the figure (± a few min):
  - SB: day about 515 min, night about 610, total about 1,120.
  - SB bouts: day about 8.7 ± 3.3 per 12 h, about 57 ± 25 min; night about 7.0 ± 4.2, about 113 ± 70 min, per-fly
    means from about 25 to about 335 min.
  - MB splits bouts further (night about 9 bouts of about 85 ± 45 min).
  **→** the reported sensitivity and the proposed T5 (mean night bout ≤ 335 min, the per-fly maximum).
- **Harbison et al. 2013 (PMC3644253).** DGRP males, night 278-703 min, day 120-682 across lines. Bout means are
  in a supplement, not read.
- **Buchert et al. 2022.** 24 h totals only.
- Caveats: different strain from Chowdhury (iso31 vs Canton-S), and the 5-min rule plus the beam layout set the
  bout numbers. SB matches the held-out paper's monitors, so SB is the comparison.

## 6. Still open

- No Canton-S male day/night minutes from any source read so far.
- No source pins how strongly need raises the restart rate (γ). Baseline data cannot separate γ from τ_rise
  well, so the held-out prediction carries the spread over all accepted sets.
- Liu 2016 figure values (BRP folds, Hz) would need a figure read.
