# S12: data for the tier C stubs (N31, N32, N33, N34, B25, B27, S7, S8, D1)

Night order item 3 (5 October), data first. Sources were found through PubMed and read by me in the PMC
full text (curl, keyword search of the text, sentences quoted), except where marked abstract. Raw HTML and
text are in `data/raw/plasticity_s12/` (gitignored).

## N31 structural plasticity (synapse addition and removal)

- **Bushey, Tononi & Cirelli 2011** Science 332:1576 (PMC3128387, full text). "In 3 Drosophila neuronal
  circuits, synapse size or number increases after a few hours of wake and decreases only if flies are
  allowed to sleep." Measured in small LNv terminals (syt-eGFP and PDF staining, 7 h wake against 7 h
  sleep), VS1 dendritic spines (more spines after sleep deprivation; more again after an enriched
  "fly mall" day) and a third circuit. The magnitudes are in figures I did not read; a search summary
  gives "almost 70% more" spines after the enriched day (secondary).
- **Sachse et al. 2007** Neuron 56:838 (abstract): prolonged CO2 exposure gives a reversible volume
  increase of the CO2 glomerulus; a later paper cites the mean as 38% (eLife 85443, secondary).
- Timescale: hours (sleep and wake) to days (rearing). Rules per synapse: none measured.
- **Decision: stays absent.** Simulation episodes last seconds. The connectome is one animal's snapshot
  after its own history, so structural plasticity is already folded into the wiring the model uses. It
  becomes relevant for multi-day experiments and for the synthetic-upload extension.

## N32 homeostatic intrinsic plasticity

- **Apostolopoulou & Lin 2020** PNAS 117:16606 (abstract): 4 days of artificial APL activation raise
  Kenyon cell odour responses after it stops; little compensation for loss of APL.
- **Ping & Tsunoda 2012** Fly 6:153 (abstract, a commentary on their 2011 paper): prolonged inactivity
  in central neurons raises Dα7 nAChR and then Shal (Kv4) currents.
- **Mee et al. 2004** J Neurosci 24:8695 (abstract): larval motor neurons lower *para* (Na channel) mRNA
  under raised synaptic excitation, via Pumilio.
- Timescale: hours to days. Set points and time constants per cell class: not measured.
- **Decision: stays absent**, for the same reason as N31: the per-cell channel values the model uses
  are already the adapted state of recorded adult cells.

## N33 astrocytes (uptake, OA/TA-gated Ca, coupling)

- **Ma, Stork, Bergles & Freeman 2016** Nature 539:428 (PMC5161596, full text): in the **larval** CNS
  (3rd instar, semi-dissected and intact), tyramine and octopamine from Tdc2 neurons raise astrocyte Ca
  through Oct-TyrR and the TRP channel Wtrw; astrocyte Ca silences dopaminergic neurons through
  adenosine receptors. "Control larvae exhibited 8-9 rhythmic oscillations in somatic Ca2+ transients
  over 15 minutes" (about one per 100-110 s). *wtrw* mutants: "~50-70%" more frequent DA Ca transients.
- Adult: no equivalent measurement read tonight. Glia are not in the male-cns Neuron table, so which
  synapses each astrocyte covers is unknown.
- **Decision: stays absent.** A larval rate and sign exist; the adult territory map and the transfer
  function (TA/OA concentration to astrocyte Ca to adenosine to DA neuron current) do not. A built
  version would be one slow node per neuropil, driven by Tdc2 cell spikes and inhibiting DA neurons,
  with every constant guessed except the larval oscillation period.

## N34 plasticity at other identified sites

- **Engel & Wu 1996** J Neurosci 16:3486 (PMC6579151, full text, Table 2). Giant fiber escape pathway,
  long-latency response (stimulation through the eyes at low intensity, which recruits the GF's
  afferents). Canton-S median stimuli to five consecutive failures: **42 at 2 Hz (n 26), 85 at 5 Hz
  (n 90), 39 at 10 Hz (n 13)**. Recovery at 5 Hz after rest: 85 first bout, 47 after 30 s, 29 after
  5 s (n 15); 39 then 34 after 120 s (n 15). The authors place the habituation in the afferents to the
  GF in the brain, not in the GF or the thoracic pathway. rutabaga slows it (473 at 5 Hz); dunce
  rutabaga speeds it (23).
- This is the most usable dataset found: a measured, frequency-dependent decline over 4-40 s at an
  identified circuit the model has (looming detectors → GF → TTMn and DLM). It is behavioural and
  circuit-level, not a synaptic parameter.
- Others (abstract level, not read tonight): Das et al. 2011 (AL habituation through LN plasticity,
  30 min to 4 days); courtship conditioning (MB); visual experience (LNv).
- **Decision: stays absent tonight.** Building it means fitting a slow depression at the
  afferent → GF edges to these curves. That is a fitted mechanism, so Engel & Wu would then be the
  fit data, not a held-out check. Recorded as the first candidate when N34 is built; an electrical
  stimulus through the eyes cannot be reproduced, but their 20 ms light-off flashes (visually evoked
  responses in white-eyed flies) can.

## B25 active sensing muscles

- **Correction to the stub's reason.** The antenna is not absent: `c_head-{l,r}_antenna-pitch` is a
  powered joint (±20°, Mamiya et al. 2011) driven by antennal motor neurons (GNG133, GNG649, GNG651,
  GNG652, GNG668, PS348) through `data/params/motor_targets.csv` (mapping inferred). What is absent is
  the retina.
- **Fenk et al. 2022** Nature 612:116 (PMC10103069, full text): two retinal muscles per eye move the
  photoreceptors under fixed lenses. Peak-to-peak photoreceptor displacement "~3 inter-photoreceptor
  spacings, which corresponds to ~15° in angular space" (optogenetic activation). Optokinetic tracking:
  "The mean initial retinal speed in response to gratings moving horizontally at 15°/s was ~3°/s" (gain
  about 0.2, derived). Receptive fields shift with the retina; small saccades activate visual neurons;
  vergence during gap crossing.
- Retinal motor neurons in male-cns: not found by name (searched type, class, synonyms, flywireType;
  `cb_motor` has 107 cells, none labelled retinal). Fenk et al. used split-GAL4 lines.
- **Decision: stays absent** (retina part). Building needs the motor neuron identity in male-cns and a
  shift of the ommatidial sampling directions in `vision.py`. The kinematic numbers above would
  constrain it.

## B27, S7, S8, D1

Not searched tonight; lower priority than N30, B24 and B26.

- B27 circulation and respiration: no coupling to the target behaviours identified.
- S7 immune state and microbiome: a healthy laboratory fly is assumed.
- S8 male reproductive state: courtship is not yet a target behaviour.
- D1 development: construction time, not lifetime; phase 2 of Ben's order (4 October).

They stay absent with their existing reasons.
