# s23 reads for B27 (circulation), N27 (brain K+) and N33 (astrocyte uptake)

24 Oct 2026, Sonnet readers (open full text where stated; quotes verbatim from the readers' reports). Director
ruling 24 Oct 00:55 sets the required levels (MECHANISM_STATUS). Nothing here is held out.

## B27: a cited circulation or mixing time

| item | value | source, preparation | read |
|---|---|---|---|
| heart end-diastolic / end-systolic dimension | 76 ± 3 µm / 8 ± 2 µm, fractional shortening 90 ± 2 % | Wolf et al. 2006 PNAS (PMC1360529), adult w1118, awake, OCT M-mode | full text |
| heart rate | 271 ± 13 bpm at 22 °C; 511 ± 26 bpm at 38 °C | same | full text |
| diastolic heart diameter | about 100 µm; peak wall velocity about 1 mm/s | Choma et al. (PMC2994925), adult, Doppler OCT, 24 °C | full text |
| heart reversal | "switched from forwards to backwards beating and then back again once every 20 to 25 s"; anterograde about 14 s at about 4 Hz, retrograde about 5 s at about 5 Hz | Wasserthal 2007 J Exp Biol 210:3707 | partial full text |
| hemolymph volume | extractable 24 ± 2 nL (male), 56 ± 8 nL (female); a lower bound on the total | Yerushalmi et al. 2014 J Insect Physiol | abstract only |
| cardiac output | 100 mL/min/kg; intracardiac velocity 2-4 mm/s | PMC3097462, **pre-pupa**, 24 °C | full text |
| circulation time | dye reaches the head within one cardiac cycle (projections about 500 ms) | same, **pre-pupa** | full text |

**Not found:** an adult stroke volume or cardiac output, the adult heart chamber length (needed to turn the
diameters into a stroke volume), and any adult tracer transit time. **Consequence:** the adult mixing time cannot
yet be derived from cited adult values. The pre-pupal numbers put a single transit at under a second and whole-body
turnover at about V_h / Q (V_h unmeasured at that stage). B27 stays absent.

## N27: activity-dependent extracellular K+ in the fly brain

| item | value | source, preparation | read |
|---|---|---|---|
| resting brain [K+]o | 13.1 ± 2.8 mM (n = 12) | Armstrong, Rodgers & Robertson 2011 (PMC3236231), adult male brain neuropil, K+-sensitive microelectrode, about 20 °C | full text |
| repetitive anoxia plateau | 54.1 ± 13.9 mM; "two phases of [K+]o clearance" (no time constant given) | same | full text |
| spreading depolarisation surge | 10-70 mM, median 24.05 mM (IQR 19.08-37.82, n = 16) | Spong et al. 2016 J Neurophysiol (PMC5013169), adult male, ouabain or KCl injection | full text |
| hemolymph K+ | 26-40 mM (e.g. 28.4 ± 2.4) | several | abstract only |
| cockroach CNS | extra-axonal 10-15 mM; rise up to 1 mM/s without glial buffering | Treherne / Schofield (**other insect**) | abstract only |

**Not found:** a K+ rise per spike or per physiological stimulus train, and a clearance time constant, in any fly
CNS. The fly numbers are a resting level and pathological surges. **Consequence:** N27's per-spike load and
clearance τ have no fly measurement to sit inside; the row stays partial (gain 0).

## N33: astrocytic Eaat1 / GAT uptake and synaptic time course

- **Eaat1, acute block** (MacNamee et al. 2016 J Comp Neurol 524:1979, PMC4861170, full text; larval third-instar
  VNC, looper interneuron → motor neuron glutamatergic IPSC; 100 µM DL-TBOA; n = 5 pairs): "This acute glutamate
  transporter block slowed the decay of IPSCs (Fig. 8A), significantly increasing IPSC half-width time, decay time,
  and the time constant resulting from a single exponential fit (Fig. 8B); no changes were found in IPSC rise time
  or amplitude". Means are in Fig. 8B only (not yet read).
- **Eaat1, astrocyte RNAi** (alrm-GAL4 > Eaat1-RNAi, same paper; control n = 10, knock-down n = 8): decay changes
  "remained significant", smaller than with acute block.
- **Fig. 8 read (24 Oct 02:27, s23; figure `nihms-776898-f0009.jpg` from the PMC author manuscript; values read by
  eye from the plotted points and bars, about ±10 %; label measured, by-eye precision).**
  - What was measured: looper-evoked motor-neuron IPSCs, compound currents during and after a ~200 ms ChR light pulse
    (whole-cell voltage clamp, −60 mV; third-instar larval VNC; room temperature, not stated). Decay time is
    2/3 → 1/3 of peak; tau is a single-exponential fit.
  - **8B, acute TBOA (100 µM DL-TBOA), n = 5 paired:**

    | Measure | Saline (ms) | TBOA (ms) | Ratio of means |
    |---|---|---|---|
    | Half-width | 310-480 (mean about 400) | 620-850 (about 750) | about 1.9 |
    | Decay time | 90-290 (about 190) | 300-760 (about 520) | about 2.7 |
    | Tau | 170-350 (about 260) | 530-1080 (about 760) | **about 2.9 (per pair about 2-4)** |

  - **8E, astrocyte Eaat1 RNAi (alrm-GAL4 control n = 10, knock-down n = 8; bars):** half-width 400 → 530 (×1.33),
    decay time 190 → 275 (×1.45), tau 275 → 565 (**×2.05**).
  - **8G, RP2 motor neurons only:** half-width 475 → 625, decay time 165 → 350, tau 320 → 690 (×2.2).
  - **Validity limits.** These are compound, light-evoked IPSCs at a larval glutamatergic (GluCl-type, inhibitory)
    synapse with no astrocyte ensheathment, not unitary currents. The control tau (170-350 ms) is far slower than a
    unitary fast receptor decay, so presynaptic firing after the pulse is part of it. The ratio under block is the
    transferable content; applying it to an adult unitary decay is inferred. TBOA blocks all EAATs, not only the
    astrocytic Eaat1; the RNAi arm is the astrocyte-specific one, with an unknown residual uptake.
- **Ensheathment** (same paper, EM, n = 67 presynaptic sites): no site fully ensheathed; astrocyte process to
  synapse 0.375 ± 0.2 µm (range 0.0006-0.93).
- **Adult NMJ** (Rival et al. 2006 J Neurobiol 66:1061; abstract only): glial dEAAT1 loss "prolonged the duration of
  the individual responses", more so during trains.
- **GAT:** Muthukumar, Stork & Freeman 2014 (expression and seizure behaviour; no current data); Chaturvedi et al.
  2022 Curr Biol (gat hypomorph: more, more consolidated sleep; "no ... electrophysiology data"). **No fly GABA
  current decay with GAT loss found.**
- **Kinetics** (Km, Vmax, density) for fly Eaat1/GAT: not found.
- **Ensheathing glia and sleep:** Stahl et al. 2018 Curr Biol (ensheathing-glia Eaat2 loss increases sleep;
  abstract level). Ties to N25.

**Consequence:** the glutamate side has one larval acute-block effect on decay (Fig. 8B, read 24 Oct: tau ×2.9 under
TBOA, ×2.05 under astrocyte Eaat1 RNAi);
the GABA side has no fly current measurement. A class-level uptake mechanism with intact uptake as the healthy
constant (S7) reproduces the current decay values exactly; its only measured content is the decay ratio under
block, larval and glutamatergic.
