# s21 N25 sleep homeostat: scope for a sourced mechanism (not built)

Written 23 Oct 2026, 00:52 CDT, s21. Director's order (00:45): find the sourced homeostatic mechanism that makes
rebound scale with time awake, and scope it before building. The 411 vs ≥ 618 min/day gap (F-S20-4) belongs to the
same row. Sources came from a Sonnet literature agent (no subagents; it never opened Huber 2004, Brown 2020 or
Chowdhury 2023). The connectome numbers are mine, from `male_cns_neurons/edges.parquet` (v1.0, all statuses,
synapse counts summed by type).

## 1. What is structurally wrong now

- N25 is a lumped Borbély process S with a deterministic hysteresis switch. S rises toward 1 while awake and
  decays while asleep. The dFB switch turns on above `th_hi + c(ct)` and off below `th_lo + c(ct)`, and while it is
  on the dFB types get a fixed tonic drive.
- Each threshold crossing gives one long sleep episode. Its length depends on τ_sleep and th_lo, so it hardly
  depends on how far S rose. S is also capped at 1.
  - So rebound is flat: +138-144 min after 6-24 h of deprivation (DECISIONS 23 Oct 00:34).
  - Total sleep is set by the threshold values, not by any measured fly quantity: mode 0 sleeps 411 min/day
    against ≥ 618 cited.
- Real fly sleep is fragmented into many bouts. The probabilities of falling asleep (P(Doze)) and of waking
  (P(Wake)) vary with sleep need (Wiggin et al. 2020 PNAS 117:10024; abstract only). A rebound that grows with time
  awake needs a **graded need variable** acting on **graded or stochastic sleep transitions**. A single fixed
  threshold cannot give it.

## 2. Candidate mechanisms (what is measured)

| mechanism | graded variable, measured | time course | necessity for rebound | read status |
|---|---|---|---|---|
| **R5 (ER5) plasticity**, Liu, Liu, Tabuchi & Wu 2016 Cell 165:1347 (PMC4892967) | BRP up after 24 h SD (Fig 4C-D); dNR1 about 7× (Fig 7C); spontaneous firing about 3× at ZT13-15 vs ZT0-2 (Fig 3B,D); bursting in 75 % of SD recordings vs 0 % rested; Ca²⁺ higher at ZT12 than ZT0, higher still after 12 h night SD (Fig 5J-K) | BRP still up 2 h into recovery, back to baseline after 24 h of recovery sleep (Fig 4A-C). No time constant | Partial: IP3R or NMDAR knockdown in R5 reduces rebound, does not abolish it (Fig 6C, 7E). Sufficient: 30 min dTrpA1 activation of R5 gives rebound-like sleep (Fig 6E-F) | full text (agent) |
| R5 slow waves, Raccuglia et al. 2019 Curr Biol 29:3611 | compound oscillation power rises with sleep need | not obtained | NMDAR coincidence block abolishes the oscillation and disrupts sleep | abstract only; no numbers usable |
| R5 morning/evening, Andreani et al. 2022 eLife 11:e74327 | BRP higher at ZT1.5 than ZT9.5 in controls and SD (n 11, 11); SD raises Ca²⁺ in the morning only (n 10) | two time points | R5 output block abolishes the morning/evening rebound asymmetry (n 16) | full text (agent); females |
| **dFB excitability and bistability**, Donlea, Pimentel & Miesenböck 2014 Neuron 81:860; Pimentel et al. 2016 Nature 536:333 (PMC4998959); Kempf et al. 2019 Nature 568:230 (PMC6522370) | SD raises dFB spikes per current step (2014; cv-c needed). Dopamine switches dFB cells ON→OFF: Rin falls to 53.3 ± 1.8 %, τm to 24.0 ± 1.3 % (n 15); 7 of 15 cells restart spiking after 7-60 min, mean 25.86 ± 7.61 min (2016). Mito-ROS (MitoTimer) up after 12 h night SD, not after day SD (2019) | ON→OFF within minutes (τ about 1.1 min) | cv-c mutants: no excitability rise and no rebound (2014, abstract level) | 2016, 2019 full text; 2014 abstract |
| **dFB-helicon-R5 loop**, Donlea et al. 2018 Neuron 97:378 (PMC5779612) | dFB AstA hyperpolarises helicon cells by 10.9 ± 2.3 mV. Helicon illumination raises R2 EPSP frequency from 9.44 ± 1.41 to 15.33 ± 1.73 Hz and depolarises R2 by 5.30 ± 1.25 mV | not tracked over time awake | AstA-R1 knockdown in helicon, or AstA mutants, reduce or abolish rebound. 24 h of 20 Hz helicon activation gives +7.64 h of sleep the next day | full text (agent) |
| Astrocyte Ca²⁺, Blum et al. 2021 Curr Biol 31:150 | rises with sleep need; Spätzle → Toll on R5 | not obtained | stated as necessary | secondary only; must be read before use |
| 23E10 controversy: De et al. 2023 Curr Biol 33:3660 (PMC10573663); Jones et al. 2023 PLoS Biol (10.1371/journal.pbio.3002012) | De: blocking 23E10 dFB output does not reduce rebound after 4 h SD (females). Jones: silencing the VNC-SP cells cuts baseline sleep, not rebound; silencing all of 23E10 blocks rebound, which by elimination points back at the dFB cells | | unresolved | full text (agent) |

## 3. Connectome map (male-cns v1.0, measured synapse counts)

| link | synapses | predicted NT (pre) | sign in our model | source claim |
|---|---|---|---|---|
| ER5 → ER5 | 15,478 | GABA | − | |
| ER5 (21 cells) → ExR1 (4 cells) | 10,044 | GABA | − | |
| ExR1 → ER5 | 5,624 | ACh | + | Donlea 2018: helicon → R2 excitatory (the agent reported glutamate; to check) |
| dFB (FB6A_a/b/c, FB6E; 8 cells) → ExR1 | 260 | Glu | − | Donlea 2018: dFB ⊣ helicon via AstA (a peptide; the fast transmitter sign agrees) |
| ER5 → ExR3 (2 cells) | 211 | GABA | − | |
| ExR1 → ExR3 | 203 | ACh | + | |
| ExR3 → dFB | 692 | 5-HT | modulatory | serotonin input to dFB (lead: Liu C et al. 2019 Curr Biol, 5-HT7 in dFB; not read) |
| ExR2 (PPM3, 4 cells, DA) → ER5 | 21 | DA | modulatory | Andreani 2022: PPM3 → R5 suppresses evening rebound |
| ExR2 → dFB | 0 | | | Pimentel 2016's dopamine switch-off of dFB must come from elsewhere: PPL107 → dFB has 8 synapses |
| TuBu06 → ER5 | 1,734 | ACh | + | |
| ER5 → EL / EPG | 10,073 / 3,222 | GABA | − | |

- **ExR1 = helicon cells is inferred, not stated.** Both are 4 large cells running from the superior arch to the
  EB. Donlea 2018 gives only GAL4 drivers, and no paper read so far names the hemibrain type.
- **The loop the sources describe is present.**
  - Helicon (ExR1) excites R5.
  - R5 inhibits helicon: ER5 → ExR1 is the strongest ER5 output after ER5 itself.
  - The dFB inhibits helicon.
  - The only route from R5 to the dFB is through ExR3 (5-HT), weak on the R5 side (211). There is no direct
    ER5 → dFB edge, so the "R5 need drives the dFB" link is an inference with a two-hop serotonergic path.
- Only 0.1 % of dFB input is dopaminergic, and 31 % is serotonergic (PFGs, hDeltaK, ExR3).

## 4. Recommendation: build an R5 need variable driving stochastic dFB switching (mode 1 of a new neutral switch)

**Why R5.** It is the only candidate with all three of the following:
- a graded variable measured to rise with wake and fall with sleep (BRP, Ca²⁺, firing);
- loss-of-function evidence for rebound;
- a cell type identified in our connectome (ER5, 21 cells).

The dFB has the best biophysics, but whether it carries the need is contested (De 2023 vs Jones 2023), so it is
used here only as the switch the need acts on. That is also the role our model already gives it.

**Proposed structure** (switch `state:sleep|homeostat`, neutral 0 = the current process S; mode 1 as below):
1. **Need variable b (ER5 release gain, BRP-like; rested at ZT0 = 1).**
   - Awake: b relaxes toward b_wake with τ_rise. Asleep: b relaxes toward 1 with τ_decay. No hard cap at a
     threshold.
   - Anchors:
     - Liu 2016 BRP: up after 24 h SD, still up at +2 h, baseline after 24 h of recovery.
     - Liu 2016 firing: about 3× at ZT13-15 vs ZT0-2, after a normal day awake.
   - τ_decay is **derived as a bracket** from those anchors. With "still up" read as ≥ 50 % of the excess left
     at 2 h, and "baseline" as ≤ 10 % left at 24 h, τ_decay lies in [2.9, 10.4] h. That bracket depends on
     those two reading thresholds, which must be stated in the registration.
   - τ_rise has no direct anchor and is fitted (labelled fitted).
2. **Need → network.** b scales ER5's outgoing weights as one type-level gain (not per synapse), so the need acts
   through the connectome: ER5 → ExR3 → dFB, and ER5 ⊣ ExR1.
   - In the reduced loop, the dFB drive is a lumped function of b. Its one gain is fitted to baseline daily
     sleep (category A data, seen, so training only).
   - Ownership: this is a slow synaptic gain, next to fly2's plasticity rows. It goes in `internal_state.py` as an
     N25 state, and fly2 is told before it is built.
3. **Stochastic dFB switching instead of the hysteresis threshold.**
   - Each of the 8 dFB cells is ON or OFF. The OFF → ON rate comes from Pimentel 2016's spontaneous restart
     (mean 25.9 min, so k₀ ≈ 1/26 min, measured; only 7 of 15 cells restarted within 60 min). It is scaled by
     the need input.
   - Arousal drive (light, the clock wake drive) sets the ON → OFF rate.
   - Sleep propensity per minute follows the ON fraction. That gives fragmented bouts, and a total sleep amount
     that depends on how high b rose. The single-threshold cap goes.
4. **Validity range.** Multi-day sleep dynamics exist only in the lumped loop. A whole-brain spiking run over
   days is out of reach. During organism runs, the network sees b as a gain and the dFB ON fraction as the dFB
   drive. The link from dFB activity to inactivity is assumed in the reduced loop, as in s20.

**Fitted vs measured, as planned.**
- Measured: k₀ (Pimentel), and the anchor points for τ_decay (Liu).
- Fitted: τ_rise, the need gain, and the arousal ON → OFF rate. That makes 3 shared quantities, fitted to
  training data only: baseline daily sleep 618-1100 min/day, night > day, the Liu 2016 time anchors, and Huber 2004
  as training context if the full text arrives.
- Held out: Chowdhury 2023 Fig. 1 (registered in DECISIONS 23 Oct, s21).
- **Falsifier:** if no setting of the 3 fitted quantities inside their ranges puts baseline sleep in range with
  b inside the measured bracket, the structure fails before any held-out read.

## 5. Open before building (cheap reads)

- Liu 2016 Fig. 4A-C: the exact BRP time points and fold changes, to replace the bracket guesses. Fig. 3: firing
  rates in Hz.
- Pimentel 2016: the restart distribution (7-60 min). How the ON fraction depends on sleep need, if measured.
- Donlea 2018: the helicon transmitter (ACh in male-cns vs the agent's "glutamate").
- Blum 2021 primary numbers, if the glia route (N27) is to join later.
- Sex: most mechanism data are from females. Our model is male; this is recorded as a validity limit.
