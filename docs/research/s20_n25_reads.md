# s20 N25 sleep homeostat: source reads

Round 1 (23 Oct, Sonnet scout, no subagents): an inventory. Category A numbers were allowed (baseline,
training). For categories B-D the scout reported **no magnitudes**, so a training / held-out split can be
registered before any of those values are seen.

## A. Baseline daily sleep, wild-type males, 12:12 LD, 25 °C (numbers seen)

| source | strain, n | measure | value | where |
|---|---|---|---|---|
| Cirelli & Bushey 2008 Ann NY Acad Sci 1129:323, PMID 18591491 | CS, w1118, wCS10 and screened stocks | total daily sleep, males | about 800-1100 min/day (stated range) | text |
| Harbison, McCoy & Mackay 2013 BMC Genomics 14:281, PMID 23617951 | DGRP, 168 lines, males | night / day sleep | night 278-703 min, day 120-682 min (range across lines) | tables |
| Buchert et al. 2022 Comp Biochem Physiol A 264:111114, PMC9299756 | DGRP-859, males, n 30 | total | 986 ± 8 min/day | text; bouts Fig. 2 |
| Geissmann, Beckwith & Gilestro 2019 Sci Adv 5:eaau9253, PMC6382397 | Canton-S males, n 485, ethoscope video | total | 618.5 min/day (95% CI 607-630) | text, figure |

The spread (about 620 to over 1000 min/day) comes from strain, the method (beam-break DAM overcounts sleep
against video) and the bout criterion. Day sleep is much smaller than night sleep in males.

## B. Rebound after deprivation (no magnitudes seen)
- Huber et al. 2004 Sleep 27:628, PMID 15282997: recovery amount and arousal threshold against prior wake
  duration (graded mechanical deprivation), several WT lines, both sexes; dose-response and time course; text
  and table.
- Shaw et al. 2002 Nature 417:287, PMID 12015603: rebound across clock mutants after graded deprivation.
- Brown et al. 2020 PLoS Genet, PMC7089559: recovery time course, mechanical against caffeine deprivation.
- Chowdhury et al. 2023 eLife, PMID 37906092: multi-day deep-sleep recovery, CS and w1118 males, ethoscope,
  Figs. 4-5.

## C. Physiological correlates of sleep pressure (no magnitudes seen)
- Donlea, Pimentel & Miesenböck 2014 Neuron, PMID 24559676: dFB excitability (input resistance, membrane time
  constant), rested against deprived.
- Pimentel et al. 2016 Nature 536:333, PMID 27487216: dFB ON/OFF switching; dopamine suppresses excitability.
- Liu, Liu, Tabuchi & Wu 2016 Cell 165:1347: R2/R5 ring-neuron firing mode and synaptic markers against wake
  duration and recovery (time course).
- Raccuglia et al. 2019 Curr Biol 29:3611, PMID 31630955: R5 slow-oscillation power against sleep need and time
  of day.
- Gilestro, Tononi & Cirelli 2009 Science 324:109; Bushey, Tononi & Cirelli 2011 Science 332:1576: BRP and
  synapse size against sleep/wake history.

## D. Published homeostat fits (no magnitudes seen)
- Abhilash & Shafer 2024 Sleep 47(2):zsad277, PMID 37930351: a two-process (Borbély) model fitted to fly
  sleep records (CS, w1118, yw; LD/DD; a period allelic series), giving build-up and decay time constants and
  their dependence on clock period. Fig. 2B-D, Fig. 5D, Tables 2-3. Round 2 reads it in full.

## Round 2 (23 Oct, Sonnet reader, no subagents): Abhilash & Shafer 2024, full text

Source: Sleep 47(2):zsad277, PMC11275470 (bioRxiv 2022.08.12.503775 spot-checked, no numerical differences).

**Model (Methods).** The time step is Δt = 1 min.
- Wake: s_t = 1 - e^(-Δt/t_i)(1 - s_(t-1)), a build-up towards 1.
- Sleep: s_t = e^(-Δt/t_δ) s_(t-1), a decay towards 0.
- Thresholds: U = M_u + A_u cos(ωt + φ) and L = M_l + A_l cos(ωt + φ), with ω = 2π/τ. The modulation is one cosine with the circadian period, **not a 12 h harmonic**.
- Switching: sleep starts once S(t-1) ≥ U(t) and lasts until S falls to L(t) or below.
- Sleep in the data is ≥ 5 min of DAM inactivity.

**Fit (Results, Fig. 2B).**
- Flies: Canton-S, w1118 and yw males, about 32 per genotype. DAM, 1-min bins, 25 °C. LD 12:12 for 9 days, then DD for 7; the fit uses the last 4 LD cycles.
- Objective: the sum of squared differences (SSD) on % time asleep per 24 h, for the three genotypes pooled. The fit was restricted to parameter pairs that give a biphasic daily waveform.
- Method: an exhaustive 2-D grid over (t_i, t_δ). There are no error bars ("no estimates of errors on these parameter values").

| quantity | value | label here | note |
|---|---|---|---|
| t_i (build-up) | 8.76 h | inferred (others' fit to fly sleep) | stated |
| t_δ (decay) | 9.51 h | inferred | stated |
| M_u, M_l | 0.35, 0.15 | guessed (fixed from Daan et al. 1984, human model) | stated, not fitted |
| A_u = A_l | 0.10 | guessed (Daan) | stated, not fitted |
| φ | 0 | guessed | the time origin is not yet confirmed (round 3) |
| model % sleep / 24 h | 74.36 % | - | data 70-80 % across the three strains (Fig. 1E) |

**Deprivation data: none.** Sleep deprivation appears only in the Introduction and Discussion. So rebound after deprivation (category B) is independent of this fit and can be held out.

**Our s10 N25 against this.** Our model has the same S equations, with tau_wake 12 h and tau_sleep 3 h (both guessed). Its thresholds differ:
- th_hi 0.6 and th_lo 0.3, modulated by c_amp 0.1 cos(4π ct/24), a 12 h (crepuscular) harmonic;
- our "asleep" for S is behavioural (≥ 5 min of activity below a_rest), and the dFB switch is a separate state.

The Abhilash set is a different structure (24 h modulation) and needs its own neutral switch.

## Round 3 (23 Oct, Sonnet reader, methods only): Huber et al. 2004 protocol; Abhilash time origin
- **Huber 2004.** No full text was reachable (no PMC version, OUP paywall).
  - Methods fragments from the abstract and secondary sources: DAM, individual flies, mechanical stimulation, deprivations of 6, 12 and 24 h, 2 baseline days before and recovery days after.
  - Not found: strains, sex, n, ZT timing, the recovery window and baseline, units, figure panels.
  - The paper also measures arousal threshold and episode length (methods not read).
  - No magnitudes were read. The reader saw a value quoted by secondary sources and withheld it.
- **Abhilash & Shafer 2024.**
  - On φ they say only: "φ is the phase angle by which the starting phase of the oscillations are adjusted and was likewise fixed at the same value (0)". No ZT anchor for t = 0 is given.
  - Of their simulated LD profile, the bioRxiv figure legend says the model "appears to underestimate daytime sleep and somewhat overestimate nighttime sleep", so it is night-biased.

## Round 4 (23 Oct, Sonnet reader): Abhilash & Shafer 2024 code and supplement (model information)
- **No source code is public.** Searched GitHub user abhilashlakshman, Zenodo, OSF and figshare. There is only a hosted GUI, https://abhilashlakshman.shinyapps.io/twoprocessmodel/ (not source-available). The paper has no code-availability statement.
- **Simulation** (bioRxiv v3 Methods and Supplementary Figs. 1, 3, 6):
  - "The model was allowed to run for a duration of 60 days. The first 30 days ... discarded ... The remaining 30 days were used for all analyses."
  - Simulated sleep is "the window of time ... where sleep pressure is being released". No 5-min bout criterion is applied to the model.
  - Update rule: S(t−1) is compared with the threshold at t. No ≥ or > is stated.
  - τ is fixed at 24 h for the LD wild-type fit (Suppl. Fig. 1, step 2).
  - Grid 0.01-15 h in 0.25 h steps for both taus, so 8.76 and 9.51 are grid points.
- **Not stated anywhere:** the ZT of t = 0 (the threshold peak), and the initial S or state.
- **Consequence.** The last 30 of 60 days of our discrete implementation are steady at 75.56 %. Their stated procedure therefore gives 75.56 % against their stated 74.36 %, and C1 stays failed. Grid resolution doesn't explain it either. The neighbouring grid points give 76.25 (t_i 8.51), 75.00 (9.01), 75.42 (t_δ 9.26) and 75.81 % (9.76), and none reaches 74.36. Their 74.36 % may be the strains' mean, which the text calls "identical", rather than the model's exact output. Not confirmed.
