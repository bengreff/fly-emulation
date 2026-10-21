# Which measurement would pin the DLMn axon share (q) and soma-axon coupling (ρ)

fly2, s20, 21 Oct 2026. Feeds Ben's measurement experiment. It follows F-GJ-6: the two-compartment DLMn passed the pre-registered GF escape test at the class values q 0.07 and ρ 1.6, which are derived from guessed geometry.

## What the result depends on

- **ρ decides whether DLMn follows the GF at all.** The passive pair is calibrated so the soma peak equals the measured 4.71 mV. Its axon peak then crosses the 7 mV rest-to-threshold gap only for **ρ < about 4**, at any q in the bracket (0.012-0.15). The crossing points are 4.2 at q 0.012, 4.0 at 0.07 and 3.6 at 0.15.
  - This is derived, from the model's own equations at the shared tau_m 20 ms and tau_s 5 ms. The whole-CNS runs agree with it. The axon peak at the central values is 13.8 mV in both the gate run and the arithmetic. The corners follow 20/20 at ρ 0.13 and 0/20 at ρ 25.
  - The registered bracket (0.13-25) spans the boundary. So today the pass rests on a guessed diameter and path length.
- **q sets the details.** It moves the latency (1.90-2.20 ms across the corners that follow) and the spikes per GF spike (2-4; the fly gives 1). It does not decide following.

So the first measurement to buy is one that tells ρ < 4 from ρ > 4. The second pins q.

## Candidates, cheapest first

Each fills the slots `cell_class:MN|soma_axon_coupling` (ρ) and `cell_class:MN|axon_membrane_share` (q). The per-value bar is "consistent with some wild-type fly", so any MN5 recording or reconstruction qualifies.

### A. A published trace (no new experiment)

**What it measures.** The amplitude and half-width, at the soma, of the axon-initiated spike in MN5. Fayyazuddin et al. 2006 (PLoS Biol 4:e63) describe it as "small and broad in somatic recordings" but give no number in the text. If a figure trace shows it, digitise the amplitude.

**How it maps to ρ.** In the two-compartment cell the soma sees an axon spike only through the coupling. Take a guessed axon spike of 80 mV for 1 ms, and tau_m 4.4 ms (measured for MN5, same paper). The soma amplitude is then:

| ρ | Soma spike amplitude |
|---|---|
| 0.13 | about 2 mV |
| 1.6 | about 23 mV |
| 4 | about 45 mV |

**What it gives.** A soma spike well under about 30 mV favours ρ < 4. This needs only reading the paper's figures; the axon waveform stays guessed.

### B. EM geometry (no wet lab; fly2 can do it with neuPrint)

**What it measures.**
- The MN5 (DLMn a, b) skeleton radius along the segment that carries the PSI synapses.
- The path length from the dendritic arbor's junction to the centroid of the PSI synapses.
- The total membrane area, from the mesh. The measured whole-cell capacitance (43 pF, Fayyazuddin 2006; 127 ± 16 pF, Herrera-Valdez et al. 2012, J Comput Neurosci 34:211, PMC6595220; earlier misattributed here to "Kadas et al.") is an alternative.

Source: male-cns v1.0 and MANC.

**What it gives.**
- q, as measured geometry.
- d and ℓ in g_c = πd²/(4·Ri·ℓ). Only Ri stays open (fitted Drosophila range 102-311 Ω·cm, Gouwens & Wilson 2009). That narrows ρ from a 190× range to about 3×.

**Caveats.**
- Part of the PSI contact lies in the posterior dorsal motor nerve, outside the volume (F-GJ-5).
- EM radii shrink with fixation.
- Skeleton radii are approximate.

The label would move from "derived from guessed geometry" to "derived from measured geometry and a fitted Ri".

### C. One new recording (pins both q and ρ, label measured)

**The recording.** Whole-cell at the MN5 soma: the response to a small current step, or the voltage-clamp capacitive transient.

**Current step.** In the two-compartment cell the somatic step response has two time constants:
- tau_m;
- an equalising one, τ1 = tau_m / (1 + ρ/(q(1−q))).

Their amplitude split gives q, and τ1 then gives ρ. Ri drops out.

**Capacitive transient.** In voltage clamp the transient has a slow component with time constant ≈ q·tau_m/ρ, carrying about a q share of the charge.

**Expected values.** At the central values τ1 ≈ tau_m/25: 0.17 ms at the measured tau_m 4.4, 0.8 ms at the model's 20. At the ρ = 4 boundary it is tau_m/62.

**Caveats.**
- Telling these apart needs good series-resistance compensation (Rs·C is about 0.4 ms at 10 MΩ and 43 pF).
- The dendritic arbor adds its own fast components, so the fit needs a third exponential.

Herrera-Valdez et al. 2012 (with Ryglewski and Duch) already measured MN5 capacitance from these transients (n 52). Their raw traces, if obtainable, might contain this without a new experiment.

## Recommendation

1. **B now.** It is in our hands, and it upgrades q to measured geometry.
2. **A** as a quick consistency read.
3. **C** for Ben's measurement experiment. It is the one recording type that pins both values as measured in one cell, and it decides the ρ < 4 question that the GF escape result hangs on.

If B or C gives ρ > 4, the registered build fails, and the next candidate is an axon with a lower spike threshold than the soma (a spike-initiation zone). That is a new mechanism with its own registration.
