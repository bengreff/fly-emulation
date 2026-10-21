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
