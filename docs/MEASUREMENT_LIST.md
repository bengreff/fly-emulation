# Ben's measurement list

Measurements that would pin a model value we can't pin from the literature or the connectome. These feed Ben's measurement experiment. Each entry gives what to record, which slots it fills, and why it matters now. Started by fly2 on 21 Oct 2026; the newest entries go at the bottom.

## 1. One whole-cell recording at the MN5 soma (adult DLM motor neuron, DLMn a, b)

**Why now.**
- Whether DLMn follows the giant fibre (GF escape, F-GJ-6) depends on the soma-axon coupling ρ.
- The male-CNS skeletons put ρ at 3.8 (option B, 21 Oct). That is on the follow boundary ρ*: 3.8 at the model's shared tau_m 20 ms, 2.9 at 12.3 ms and 2.2 at 4.4 ms. The last two are MN5's Rin × Cm from two labs: Herrera-Valdez et al. 2012 and Fayyazuddin 2006.
- The fitted range of axial resistivity spans the boundary (ρ 2.4-7.5), and the two MN5s of one fly differ by a factor of 2.7.
- The same cell also carries the doublet blank. At the earlier guessed geometry, the axon compartment fired twice per GF spike, because the PSI synaptic current outlasts the axon's 2 ms refractory period with no afterhyperpolarisation. At the derived geometry it fires once, but late or not at all.
- None of these is published in readable primary text: the PSI→MN5 decay, MN5's spike threshold, its AHP, its refractory period. The adult nicotinic bracket for the decay (1.1-6.73 ms) spans the point where the model's answer flips.

**What each answer would decide** (replica of the model's pair, one PSI spike, class q 0.104 and ρ 3.80; DECISIONS 21 Oct 00:25):

| Read-out | If | Then |
|---|---|---|
| EPSP decay (tau_s) | ≤ 3 ms | One spike within 0.5 ms at tau_m 20; within 1.4 ms at 12.3 |
| EPSP decay (tau_s) | ≥ 5 ms | No spike at the class values unless Ri is near 300 Ω·cm or the cell is like MN5 L. The geometry or the threshold would then be the next suspect. |
| tau_m (slow constant of the step response) | near 4.4 ms | No spike at the class values for any decay; the two-compartment reading of F-GJ-6 fails |
| tau_m (slow constant of the step response) | 12-25 ms | The decay decides, as above |
| Soma amplitude of the GF-evoked spike | | Reads ρ directly; the step response gives q |

**Protocols, all in one cell** (in situ, as in Fayyazuddin et al. 2006 or Ryglewski & Duch 2009):

| Protocol | Fills (slot) | Read-out |
|---|---|---|
| Small hyperpolarising current step, or the voltage-clamp capacitive transient | `cell_class:MN\|axon_membrane_share` (q), `cell_class:MN\|soma_axon_coupling` (ρ), DLMn tau_m | Two-exponential fit. The slow constant is tau_m; the fast, equalising one is τ1 = tau_m / (1 + ρ / (q(1 − q))); their amplitude split gives q. Ri drops out. Expected τ1 is about 0.2 ms, so series-resistance compensation matters (Rs·C ≈ 0.4 ms at 10 MΩ, 43 pF). |
| Depolarising current steps (f-I) and paired brief pulses | DLMn spike threshold, AHP amplitude and duration, refractory period | The fix for the doublet should come from these values. |
| GF stimulation with the soma spike intact | the soma amplitude and half-width of the axon-initiated spike | A direct read on ρ: about 23 mV at ρ 1.6 and about 45 mV at ρ 4 (`docs/research/s20_n30_pin_q_rho.md`). |
| GF stimulation with the soma spike blocked, as in the 2006 paper | PSI→MN5 EPSP rise and decay | Pins the synaptic decay (tau_s) of this connection. Today it uses the shared 5 ms. |

**What it replaces.** q and ρ are now derived from EM geometry, the measured Rin and a fitted Ri. The threshold gap, refractory period, AHP and tau_s for DLMn are shared defaults (guessed). The recording would move all of these to measured in one cell. That cell is consistent with some fly, which meets the per-value bar.

**Sources.** `docs/research/s20_n30_pin_q_rho.md` (option C); DECISIONS 21 Oct 00:07 and the results entry after it; F-GJ-6.

## 2. The spike-initiation site in an adult leg MN (front-leg tibia flexor, Azevedo 2020 preparation)

**Why now.** The s15c morphological arm needs a spike zone in each leg MN. The male-CNS v1.0 skeletons of the T1 leg MNs end inside LegNp(T1). The motor axon in the leg nerve isn't traced, so the skeleton can't say where spikes start (DECISIONS 21 Oct 02:10). The model guesses the arbor base (the soma-side split node + 20 µm), with the end of the main trunk as the alternative (DECISIONS 21 Oct 02:17). Azevedo et al. 2020 found that soma current steps fail to fire fast and intermediate tibia flexors, which suggests a spike zone electrically remote from the soma. That is qualitative, not a site.

| Protocol | Fills (slot) | Read-out |
|---|---|---|
| Soma whole-cell recording, plus a nerve (extracellular) recording or Ca/voltage imaging along the neurite, with antidromic stimulation of the leg nerve | the spike-zone site (path distance from the soma) and the soma spike attenuation | The latency difference between soma and nerve spikes, and the site where the spike first appears, give the initiation zone. Its distance from the arbor base or the trunk end decides between the two model sites. |
| Local TTX puff or Nav (para) immunostaining along the neurite | the site of the Nav-dense (AIS-like) domain | The Nav-dense segment's position and length. The model now guesses 20 µm. Ravenscroft et al. 2020 describe a para-dense distal AIS-like domain in Drosophila neurons. |

**What it replaces.** The leg-MN spike-zone site and length are guessed (two candidates). A measured site in one tibia flexor is consistent with some fly, which meets the per-value bar.

**Sources.** DECISIONS 21 Oct 02:10 and 02:17; F-S15-3; `docs/research/s15c_cable_params.md`.

## 3. The octopamine effect on adult VNC premotor neurons and leg MNs (rest, Rin, f-I)

**Why now.** The s16 state arm (DECISIONS 21 Oct 02:28) depolarises VNC premotor classes to stand in for the aroused, octopamine-high walking state. Its direction comes from the stick insect and the locust, and its size is guessed. No adult Drosophila VNC recording with octopamine was found. The one direct MN measurement, larval RP2, is a null (Schützler et al. 2019).

| Protocol | Fills (slot) | Read-out |
|---|---|---|
| Whole-cell recording of a front-leg tibia flexor MN (Azevedo 2020 preparation) before and after bath octopamine (1-10 µM), or Tdc2>CsChrimson activation | `class:MN_leg\|tonic_drive` and threshold under the state; leg-MN Rin and f-I change | Δrest, ΔRin, Δrheobase and the f-I slope. A null confirms the larval result in the adult. |
| The same in a premotor interneuron with a sparse line (e.g. a 19A, 16B or 17A type) | `class:vnc_local_<hl>\|tonic_drive` under the state | The same read-outs. They set the size of the s16 depolarisation, now guessed at +2-4 mV. |

**What it replaces.** The state's magnitude is guessed for every class, and its direction is inferred from other species. One recording per class would make it measured for some fly.

**Sources.** `docs/research/s16_octopamine_excitability.{csv,md}`; DECISIONS 21 Oct 02:28.

## 4. The unitary PSP from a core premotor cell onto an adult leg MN (E2, E1 or I1 onto a front-leg MN)

**Why now.** Every walking arm since s13 fails at the same step: the core's output doesn't cross to the leg MNs. That covers MANC counts (F-XCONN-2), graded release (F-BYPASS-4, F-S14-1), MN gain and a uniform synaptic scale (F-BYPASS-6, F-BYPASS-7), E1/E2 bursting (F-S14-1), two compartments (F-S15-2), passive EM morphology (F-S15-4) and an octopamine state (F-S16-1). In the model, one core spike gives a leg MN a median 0.17 mV (E1), 0.47 mV (E2) or 0.21 mV (I1), derived as connectome synapse count × 0.021 mV per synapse. The gap to threshold is 7 mV, or 26 mV for the slow tibia flexors. The 0.021 mV per synapse is inside the insect unitary-PSP range, but no adult Drosophila premotor → leg-MN unitary PSP was found. A uniform scale large enough to reach measured MN rates implies 0.34-0.53 mV per synapse, outside that range (F-BYPASS-7). The open question is whether a few connections are strong (a synapse-specific value) or all of them are as weak as the model's.

| Protocol | Fills (slot) | Read-out |
|---|---|---|
| Whole-cell recording of a front-leg tibia flexor or coxa MN (Azevedo 2020 preparation), with brief CsChrimson pulses in a sparse line for E2 (INXXX466), E1 (IN17A001) or I1 (IN16B036); a sparse split line for these types has not been checked | the mV per presynaptic spike for that connection: `connection_class:...\|efficacy_per_synapse` at connection grain, and tau_s for it | The unitary PSP amplitude, latency and decay. With Rin from the same cell, this gives the synaptic charge. |
| The same with the MN held near rest during walking-like DN drive (DNg100 activation), if the preparation allows | the summed core input per cycle at the MN | Peak-to-trough depolarisation per cycle at the soma. |

**What each answer would decide.**
- **About 0.2-0.5 mV per spike:** the fly's hand-off is as weak as the model's. Then the missing piece isn't strength; it's proprioceptive feedback (S4 proper) or another premotor driver.
- **Several mV per spike from a sparse set of connections:** connection-specific strength is the break, and the synapse-specific fidelity rung is next.

**What it replaces.** The core → leg-MN strength is now the shared per-synapse value (fitted on the brain, inferred for the VNC). One recorded connection is consistent with some fly, which meets the per-value bar.

**Sources.** F-S14-1 hand-off table (`runs/s14/handoff.json`); F-BYPASS-7 and `docs/research/s13_s4b_unitary_psp.md`; F-S15-4; F-S16-1.

## 5. Does resting dopamine erase a KC→MBON memory? MBON-γ1pedc after one pairing, with its DAN's resting spikes recorded, silenced and replayed

**Why now.**
- With measured resting rates (KCs 0.1 Hz, DANs 6-10 Hz), every sourced KC→MBON plasticity rule fitted to Hige 2015 erases a memory within seconds, and naive weights collapse too. This holds for m10f4's rule, Berry/Cohn/Hattori-style restoration, KC coincidence, DAN burst dependence and Handler 2019's two-receptor timing windows (F-S26-1, F-S26-2).
- Yet Hige 2015 saw γ1pedc depression persist for at least 40 min in vivo.
- So either spontaneous DAN spikes are about 10^3-10^4 times less effective than pairing ones, or the plastic compartments' DANs are far quieter at rest than 6-10 Hz. No unheld source says which (F-S26-3). Calcium imaging can't tell: GCaMP3 reads PPL1-α'2α2 as silent while voltage imaging finds it spiking at 6-10 Hz.
- N21 is on in m10f only because its DANs are silent at rest in the model. It must be switched off for any run with resting DANs.

**Protocols, in one preparation** (in vivo whole-cell MBON-γ1pedc>α/β as Hige et al. 2015, with voltage imaging of PPL1-γ1pedc as Huang et al. 2018):

| Protocol | Fills (slot) | Read-out |
|---|---|---|
| 10 min of no stimulus, quiescent and moving epochs | `cell_type:PPL1-γ1pedc` resting spike rate and pattern (tonic or burst) | Spikes/s and inter-spike intervals of the DAN, by voltage imaging |
| One forward pairing (Hige protocol), then CS+ and CS- tests at 1, 10, 40, 90 and 180 min, with the DAN left at rest | N22 memory tau with DANs active; `kc_mbon_memory_tau_h` | CS+ / CS- MBON charge over time |
| The same with the DAN silenced after pairing (GtACR1 or shibire-ts) | how much of the forgetting is driven by resting dopamine (Berry 2012 active forgetting) | Difference between the two retention curves |
| No odour: 10 min of CsChrimson drive of the DAN at the measured resting rate and pattern, then a naive odour test; repeat with a 2 Hz pairing-like train of equal spike count | per-spike efficacy of tonic against pairing-like DAN spikes (the missing factor, F-S26-1) | Naive-odour MBON charge before and after |

**What each answer would decide.**
- **The DAN rests at Hz rates, the memory lasts hours, and tonic replay doesn't depress naive responses:** spontaneous spikes really are far less effective. The replay at different patterns then gives the form of the factor, sourced. N21 can get it and be switched on with resting DANs.
- **The DAN rests near silence (below about 0.01 Hz) in this state:** today's rule is safe in that compartment. The fit stands, and the resting fit sets that DAN quiet.
- **The memory decays faster with the DAN at rest than silenced:** active forgetting is real here, and its rate replaces the guessed 3 h N22 tau.
- **Tonic replay at the resting rate erases naive responses within minutes:** the per-spike rule is right, and memory survives by another route (state gating, KC silence). Look there next.

**What it replaces.** The rule (`kc_mbon_ltd_timing_rate` 0.430, fitted to Hige 2015) is valid only with DANs silent at rest. One compartment's answer is consistent with some fly, which meets the per-value bar.

**Sources.** F-S26-1, F-S26-2, F-S26-3; `docs/research/s26_mb_dan_rest_rates.md`; `scripts/probes/s26_retention.py`. Huang et al. 2024 (held out) has voltage-imaging resting rates for five PPL1 types and would answer the first row for the PPL1 compartments once the Director releases it.

## 6. Is glutamate inhibitory at MBON → MBON and MBON → DAN links? MBON-γ1pedc>α/β with MBON-γ4>γ1γ2 and MBON-β1>α driven

**Why now.**
- At rest the model's MB output neurons fire too little, and the cause is inhibition from other MBONs. Glutamatergic
  MBONs supply most of it (rest drive in mV/s per cell, signed weight × presynaptic rate, m10f3 with the s21 class
  noise; `runs/s20/mb/glu_split.json`):

  | Cell type | From glutamatergic MBONs | From GABAergic MBONs | Net, all inputs | KC drive at 0.1 Hz |
  |---|---|---|---|---|
  | MBON11 (γ1pedc>α/β) | −988 | −158 | −1,115 | +303 |
  | MBON12 (γ2α′1) | −500 | −5 | −487 | +69 |
  | MBON13 (α′2) | −452 | 0 | −443 | +78 |
  | MBON14 (α3) | −336 | −42 | −299 | +74 |
  | PPL101 (PPL1-γ1pedc) | −220 | −236 | −172 | +110 |
  | PPL105 (PPL1-α′2α2) | −166 | −31 | −94 | +39 |

- The model treats glutamate as inhibitory (GluClα, a glutamate-gated chloride channel). That sign is **inferred**
  from the antennal lobe (Liu & Wilson 2013). No functional test of a glutamatergic MBON → MBON or MBON → PPL1 link
  was found (s22 reader, `docs/research/s22_mb_type_spread.md` section 3). The one measured glutamatergic MBON → DAN
  effect was excitation (Felsenberg et al. 2018, M4β′/M6 → PAM-γ5, calcium imaging, possibly indirect).
- KC firing at the measured 0.1 Hz offsets only 14-64 % of this inhibition, so the sign is the main open lever. It is
  a biological question, not a fit knob.

**Protocols** (in vivo whole-cell MBON-γ1pedc>α/β as Hige et al. 2015; MBON05 and MBON06 have split lines, Aso et
al. 2014):

| Protocol | Fills (slot) | Read-out |
|---|---|---|
| CsChrimson pulses in MBON-γ4>γ1γ2 (MBON05) or MBON-β1>α (MBON06), recording MBON-γ1pedc>α/β | the sign and size of glutamate at MBON → MBON links: `cell_type:all\|glutamate_receptor_sign` at that connection, and its mV per spike | PSP sign, amplitude, latency and reversal potential (chloride or cation) |
| The same with picrotoxin, then with GluClα RNAi in the recorded MBON | which receptor carries it (GluClα, or an excitatory ionotropic or NMDA receptor) | Fraction of the PSP removed by each |
| The same recording with PPL1-γ1pedc (voltage imaging, Huang et al. 2018) instead of the MBON | the sign at glutamatergic MBON → PPL1 links | Change in DAN spike rate during the pulses |

**What each answer would decide.**
- **Inhibitory, GluClα (chloride, blocked by picrotoxin and the RNAi):** the model's sign stands. MBON11's
  under-firing must then come from elsewhere: the MBON rates feeding it, the per-synapse strength, or a missing
  excitatory input. Look there next.
- **Excitatory:** the glutamatergic share flips sign. By the table, MBON11's net rest drive goes from −1,115 to
  about +860 mV/s, MBON12 to about +510, MBON14 to about +370 and PPL105 to about +240. The γ1 pair and the PPL1
  under-firing would likely close without any fitted value, and the class noise fitted in s21 would need refitting.
- **Mixed (different receptors in different compartments, or a biphasic PSP):** glutamate's sign becomes
  per-connection-class, which is the synapse-specific fidelity rung. Each measured link then gets its own sign,
  and the rest stay inferred.
- **No detectable PSP:** the links are weaker than the synapse counts suggest, and the per-synapse strength at
  MBON → MBON links is the next measurement.

**What it replaces.** The glutamate sign at all MBON outputs (inferred from the antennal lobe). One measured link
is consistent with some fly, which meets the per-value bar.

**Sources.** `docs/research/s22_mb_type_spread.md` sections 1-3; `runs/s20/mb/rest_drive.json` and
`runs/s20/mb/glu_split.json`; Aso et al. 2014 eLife (MBON transmitters and split lines); Liu & Wilson 2013 PNAS
(GluClα in the antennal lobe); Felsenberg et al. 2018 Cell (glutamatergic MBON → PAM excitation); Hige et al. 2015
(MBON whole-cell preparation); Huang et al. 2018 (DAN voltage imaging).
