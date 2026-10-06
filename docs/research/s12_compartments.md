# S12: data for N30, reduced multi-compartment neurons with synapses placed by position

Night order item 3 (5 October), data first. Question: is there measured data to build
`cell_type:all|n_compartments` > 1, and where does the point-neuron model break?

Sources were found through PubMed and read by me in the PMC full text (keyword search of the text,
sentences quoted below). Raw HTML and text are in `data/raw/cable_s12/` (gitignored). Skeleton
statistics come from the existing `data/derived/skeleton_lengths.csv` (one skeleton per type, produced
in an earlier session); `scripts/skeleton_lengths.py` was not rerun.

## Measured passive cable properties in Drosophila

| Cell | Rm (kΩ·cm²) | Cm (µF/cm²) | Ri (Ω·cm) | Basis | Source |
|---|---|---|---|---|---|
| DM1 PN, cell 1 | 8.3 | 2.6 | 163.9 | fitted to somatic current pulses (NEURON), measured morphology | Gouwens & Wilson 2009 J Neurosci 29:6239, table "Best fits" (PMC2709801) |
| DM1 PN, cell 2 | 20.4 | 1.5 | 102.5 | same | same |
| DM1 PN, cell 3 | 20.8 | 0.8 | 266.1 | same | same |
| DM1 PN, three tuft sizes (511, 1023, 2047 branches) | 19.2, 20.8, 26.4 | 0.80, 0.79, 0.61 | 224, 266, 311 | same, morphology varied | same |
| VM2 PN | not usable | | > 800 | fits outside the 30-400 Ω·cm literature range; authors dropped them | same |
| HS cell (lobula plate) | 8.166 | 0.6 | 400 or 900 | Rm from measured τ with Cm assumed; Ra 900 matches the mean measured input resistance | Cuntz et al. 2013 PLoS Comput Biol 9:e1003204 (PMC3747245) |

All values are **fitted** (model parameters fitted to recordings), not direct measurements. HS dendrite
diameter 0.58 ± 0.08 µm in Drosophila (n 20) against 1.92 ± 0.27 µm in Calliphora (n 25) (measured,
Cuntz 2013). Summed electrotonic length of HS dendrites 21 ± 3.8 in Drosophila (same paper).

What Gouwens & Wilson say about integration (quoted):

- "We find that these neurons are electrotonically extensive and that a somatic recording electrode can
  only imperfectly control the voltage in the rest of the cell."
- "Therefore, synaptic potentials traveling to the spike initiation zone (SIZ) bypass the soma."
- "We do find that simulated EPSPs arising at only a single site in the dendritic tuft attenuate
  substantially ... However, when the conductances underlying a unitary synaptic event are distributed
  across many dendritic branches, these conductances can sum more effectively and can produce large
  unitary EPSPs at the soma."
- "Therefore, unlike many other cells, they probably do not perform dendritic computations that rely on
  the specific spatial locations of synaptic inputs."
- A somatic voltage change "is substantially attenuated in the dendrite and severely attenuated in the
  axon".

## Electrotonic length per cell type (derived)

λ = sqrt(Rm·d / (4·Ri)), with d = 2 × the skeleton's median axon radius per type and L = the median
path from the root to the type's own presynaptic sites, divided by λ. At 100 Hz the length constant
shortens by sqrt(2 / (1 + sqrt(1 + (ωτ)²))). 11,751 types.

| Parameter set | τm (ms) | median λ_DC (µm) | median L_DC | types with L_DC > 1 | median L at 100 Hz | types with L_100Hz > 1 |
|---|---|---|---|---|---|---|
| DM1 cell 3 (20.8 k, 266) | 16.6 | 316 | 0.69 | 18% | 1.66 | 84% |
| DM1 cell 1 (8.3 k, 164) | 21.6 | 255 | 0.86 | 35% | 2.32 | 90% |
| HS (8.17 k, Ra 400) | 4.9 | 162 | 1.35 | 75% | 1.97 | 88% |
| HS (8.17 k, Ra 900) | 4.9 | 108 | 2.03 | 89% | 2.95 | 92% |

Sealed-end steady-state attenuation is 1/cosh(L): 0.81 at L 0.69, 0.48 at L 1.35, 0.26 at L 2.03
(derived).

**Caveat that limits this table.** The skeleton radii are quantized: 8,904 of 11,751 types (76%) sit at
0.256 µm, and the next values are 0.468 and 0.768 µm. So per-type diameter is close to a floor value,
not a measurement, and λ per type is uncertain by at least the square root of a factor of 2-3. The
table shows the range the published fits allow, not each cell's value.

## What this means for the point-neuron model

- **Validity range of the point neuron (inferred from the above).** Input that is distributed over many
  branches and summed at the SIZ is represented reasonably by a point neuron at steady state (Gouwens'
  conclusion for PNs). Input at a single site, timing below a few milliseconds, and anything that depends
  on where a synapse sits (axo-axonic and presynaptic inhibition, terminal-specific modulation,
  back-propagation into the dendrite) is not represented.
- **Where the model already relies on it.** Presynaptic inhibition is in the connectome as synapses
  onto sensory axons, for example the GABAergic 9A neurons onto femoral chordotonal hook axons
  (Dallmann et al. 2025, B24 note). As point neurons, these synapses lower the afferent's spike rate
  everywhere, rather than its release at the inhibited terminals only (inferred; not tested tonight).
- **Data that is public.** The male-cns v1.0 synapse points (`syn-points-male-cns-v1.0-minconf-0.5.feather`,
  13 GB) and high-resolution skeletons (`skeletons-highres-swc/`) are in the public bucket
  `gs://flyem-male-cns` and need no token. The neuPrint token is not needed for any step below.

## Decision (5 October)

N30 stays **absent** tonight. There is enough data to build a first version, but not to validate it
per type, and it is a large build (a position for every synapse from the 13 GB synapse table, a second state
per cell on the GPU).

Build plan, when it is taken:

1. Two compartments per cell: dendrite plus SIZ, and axon terminal. Synapses assigned by their position
   on the skeleton relative to an SIZ estimate (the branch point of the primary neurite, inferred).
2. Coupling conductance from Ri, the skeleton path length between the two compartments and a diameter
   bracket (the radius floor and 2× it), labelled derived.
3. Validity checks against held-out data: Gouwens & Wilson's DM1 attenuation curves and the
   input-resistance fits above (the fitted parameters would be used for the build, so the attenuation
   profile is the check), and the Dallmann 2025 hook-axon suppression during active movement.

Experiment that would settle the main uncertainty (for Ben's list): paired soma and axon-terminal
recordings, or voltage imaging along the neurite, in one identified central cell type per major class,
with the same cell's EM skeleton. That fixes λ per class instead of per published PN.
