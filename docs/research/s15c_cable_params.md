# S15c — cable-model parameter literature scan

Scope: passive cable parameters, spike-initiation-zone (SIZ) geometry, and unitary synaptic
conductance for building passive multi-compartment T1 leg-MN / premotor models with an active SIZ.
~25-tool-call web scan, 2026-10-21. Primary sources fetched where possible; items drawn only from
search-engine synthesis (not confirmed against the paper's own text/figures) are flagged **[unverified —
confirm against PDF before using]**.

## 1. Fitted passive cable parameters, insect CNS neurons

| Rm (specific membrane R) | Cm (specific membrane C) | Ri (axial resistivity) | Cell / species | Prep | Label | n | Citation |
|---|---|---|---|---|---|---|---|
| 20.8 kΩ·cm² | 0.8 µF/cm² | 266.1 Ω·cm | Adult *Drosophila* antennal-lobe projection neurons (example cell) | Whole-cell patch in vivo; morphology from dye fill/confocal; fit in NEURON 6.2 | fitted | small n (paper fits individual cells, ~3 shown) | Gouwens NW, Wilson RI (2009) *Signal propagation in Drosophila central neurons*. J Neurosci 29(19):6239–6249. **[unverified — WebFetch of jneurosci.org and the ModelDB/GitHub mirror (model 118662) were blocked/empty; this triple is search-engine-reported and recurs consistently across two independent queries, but I could not read it off the paper's own table or `fit_params.hoc`. Confirm before use.]** |
| 26.35 kΩ·cm² (= 1/g_leak, g_leak = 37.96 ± 4.38 µS/cm²) | 0.77 ± 0.02 µF/cm² | 212.47 ± 3.69 Ω·cm (their "Ra") | 3rd-instar larval *Drosophila* aCC/RP2 motoneuron | Whole-cell voltage clamp passive step, ex vivo; morphology from confocal dye-fill reconstruction (Amira → NEURON) | fitted | n = 5 (Table 2) | Günay C, Sieling FH, Dharmar L, Lin W-H, Wolfram V, Marley R, Baines RA, Prinz AA (2015) *Distal Spike Initiation Zone Location Estimation by Morphological Simulation...* PLoS Comput Biol 11(5):e1004189, Table 2. **Confirmed from primary PDF.** Paper also fits an electrode-seal model: g_seal = 0.20 ± 0.03 nS, C_electrode = 1.28 ± 0.24 pF, R_electrode = 41.47 ± 3.88 MΩ (same Table 2) — relevant if you simulate the patch-clamp artifact rather than just the cell. |
| 2.0 kΩ·cm² | 0.9 µF/cm² (HS) / 0.8 µF/cm² (VS) | 40 Ω·cm | Blowfly (*Calliphora*) lobula-plate HS and VS tangential cells | Intracellular recording + cobalt-fill 3D reconstruction; fit by compartmental model (not Drosophila) | fitted | several cells per class, pooled fit | Haag J, Borst A (1996/1997) *The intrinsic electrophysiological characteristics of fly lobula plate tangential cells* (parts I–II), J Comput Neurosci. **[unverified — WebFetch of the Springer page and the paper itself returned no table; numbers are search-engine-reported, and I could not confirm exact author order/part/volume. This is blowfly, not Drosophila — treat as a sanity-check range, not a value to import directly.]** |
| not found | not found | not found | Drosophila, Meier & Borst (2019), Tobin et al. (2017), Hesse/Gjorgjieva | — | — | — | No compartmental-model Rm/Cm/Ri fit located for these. Tobin/Gjorgjieva-type searches returned only the MBON-α3 model below (single-compartment, not a cable fit) and mushroom-body KC papers unrelated to cable parameters. |

**Cross-check**: Günay et al. 2015 state in their Results that "the passive morphology cable parameters
we derived were similar to those reported in *Drosophila* central neurons (see Table 1 in [26])" where
ref [26] is the Gouwens & Wilson line of work — i.e. the larval-motoneuron fit (26.3 kΩ·cm², 0.77 µF/cm²,
212 Ω·cm) and the adult-PN fit (20.8 kΩ·cm², 0.8 µF/cm², 266 Ω·cm) are reported by the authors themselves
as being in the same ballpark. That is independent partial corroboration of the Gouwens & Wilson triple
even though I couldn't re-derive it from their own table directly.

**Working bracket for T1 leg-MN / premotor cable fits** (derived, not measured): Rm ~20–30 kΩ·cm²,
Cm ~0.75–0.9 µF/cm², Ri ~210–270 Ω·cm, as a prior/initialization range spanning the two confirmed
Drosophila CNS fits above. Label as **inferred** (cross-cell-type generalization), not measured for T1
leg MNs specifically — no adult Drosophila VNC passive fit exists (see §5).

## 2. Adult Drosophila T1 leg motor neurons (Azevedo et al. 2020)

Source: Azevedo A, Lesser E, Phelps JS, ... Tuthill JC (2020) *A size principle for recruitment of
Drosophila leg motor neurons*. eLife 9:e56754. In vivo whole-cell patch clamp, anesthetized restrained
flies, tibia flexor MNs split into fast/intermediate/slow classes by morphology+physiology. **Confirmed
from primary text via WebFetch of elifesciences.org.**

| Class | Input resistance | Resting potential | Spontaneous rate | n |
|---|---|---|---|---|
| Fast | 150 MΩ | −68 mV | silent | 15 |
| Intermediate | 300 MΩ | −60 mV | silent | 11 |
| Slow | 700 MΩ | −48 mV | ~30 Hz | 14 |

All measured, in vivo, whole-cell.

**Not found in this paper** (explicitly checked, not present in the fetched text): membrane time
constant, whole-cell capacitance, spike threshold, or spike amplitude at the soma, for any class.

**Spike initiation / somatic isolation**: the paper states that current injection into fast and
intermediate MNs "failed to reliably trigger action potentials, based on recordings from both the cell
body (whole-cell) and axon (EMG)," which they attribute to "intrinsic morphological or
electrophysiological properties that electrically isolate the soma from the spike initiation zone." No
quantitative distance or length is given — this is a qualitative/inferential statement, not a measured
SIZ location. No numeric value for "how small somatic spikes are" was found in the fetched text (gap).

**Azevedo et al. 2024 / Gorko et al. 2024 follow-ups**: searches turned up Azevedo et al. 2024 (Nature,
*Connectomic reconstruction of a female Drosophila ventral nerve cord* — EM atlas, not new
electrophysiology) and Gorko et al. 2024 (Nature, *Motor neurons generate pose-targeted movements via
proprioceptive sculpting* — neck/head MNs, proprioceptive loop study, not T1 leg MN biophysics). Neither
appears to add quantal/cable-parameter data for T1 leg MNs; not fetched in full given budget, so treat as
"not found, not confirmed absent" rather than a hard negative.

## 3. Spike initiation zone location / length

- **Günay et al. 2015** (same paper as §1, primary-source-confirmed): model-predicted SIZ for the larval
  aCC/MN1-Ib motoneuron is **on the primary axon, 70 µm distal to the most distal dendritic branching
  point** — i.e. defined relative to the branch point, not the soma. This locates the SIZ roughly where
  the primary neurite exits the nerve cord neuropil toward the periphery. This is a **derived/fitted**
  location (from matching an in vivo current-clamp signature via simulation), not a direct
  anatomical/molecular measurement, and it is larval, not adult, and light-microscopy- not EM-based. No
  explicit "length" of the SIZ domain (as opposed to its start point) is given in the fetched text — the
  model places fast Na⁺/K⁺ conductances at the distal tip of a small number of discretized axon
  compartments, not over an explicitly stated micrometer span.

- **Ravenscroft et al. 2020** J Neurosci 40(42):7999–8024, *Drosophila Voltage-Gated Sodium Channels Are
  Only Expressed in Active Neurons and Are Localized to Distal Axonal Initial Segment-like Domains*.
  Para (the sole Drosophila NaV channel) is enriched at a **distal axonal segment, located distal to
  where dendrites impinge on the axon**, proposed as the likely site of AP initiation — directionally
  consistent with Günay's branch-point-relative finding. The one quantitative distance found is for a
  peripheral sensory neuron, not a CNS motor/premotor neuron: in 3rd-instar larval PNS ddaE neurons, Para
  intensity peaks **~40–60 µm from the soma**. **No CNS or motor-neuron-specific micrometer distance or
  AIS-domain length was found** in the material fetched — this is the main gap for this question; the
  paper's main CNS finding is qualitative (distal-to-dendrites) rather than a stated distance.

- **Gouwens & Wilson 2009**: not checked for SIZ-location claims within budget (companion paper
  "Lessons from a compartmental model of a Drosophila neuron," J Neurosci 29(39):12033, was identified
  but not fetched) — not found/not checked, don't treat as absent.

- **Trunova et al. 2011** J Neurosci, *Cdk5 regulates the size of an axon initial segment-like
  compartment in mushroom body neurons*: establishes that Drosophila mushroom-body γ-neurons have an
  ankyrin/K⁺-channel-enriched AIS-like proximal axonal domain, organized by Ankyrin (the
  invertebrate/vertebrate-conserved AIS scaffold). This is a brain (Kenyon cell), not VNC motor-neuron,
  result, and no micrometer distance/length was found in the search snippets — **not found** for this
  question's purposes (motor-neuron, distance-in-µm).

**Net for Q3**: only one quantitative, directly-relevant number was found — Günay's 70 µm from the
most-distal dendritic branch point, larval, light-microscopy, model-derived. Nothing adult, nothing EM,
nothing directly for T1 leg MN or premotor classes. No explicit SIZ *length* (as opposed to *onset
distance*) was found anywhere in this scan.

## 4. Unitary synaptic conductance, Drosophila central cholinergic synapse

Source: Kazama H, Wilson RI (2008) *Homeostatic matching and nonlinear amplification at identified
central synapses*. Neuron 58(3):401–413. ORN→PN synapse, antennal lobe, ex vivo whole-cell recording.
**Search-engine-synthesized, not independently confirmed against the PDF/figures** — WebFetch of the
Neuron/ScienceDirect/PubMed pages was not attempted directly (budget); treat as
**[unverified — confirm against Fig/Table before use]**, though the numbers are internally consistent and
match this reviewer's background recollection of the paper.

| Quantity | Value | Label | Notes |
|---|---|---|---|
| Unitary EPSC amplitude (one ORN spike → one PN) | ~13.5 pA | measured | population/connection-level event, not one release site |
| Unitary EPSP amplitude | ~7 mV | measured | same connection-level event |
| Peak synaptic conductance for that unitary event | 0.28 nS | fitted (conductance-based model fit to the EPSC) | this is the *whole-connection* conductance |
| Release sites per ORN→PN connection | ~30 (stated range "several dozen"; model used 30) | measured/estimated (EM-based bouton counts informing the model) | — |

**Derived per-release-site bracket** (derived by me, not stated in the paper): 0.28 nS / 30 sites ≈
**9–10 pS per release site**, assuming near-unity release probability and linear summation at rest (the
paper also reports strong short-term depression, so this is a resting/first-spike value, not a
depressed-state one). This is the number to use for bracketing a per-EM-synapse conductance in the
cable model, labelled **derived**, with the caveat that it assumes release probability ≈ 1 at this
synapse (stated qualitatively as "high" in the paper) and that EM synapse count may not equal functional
release-site count 1:1.

No separate Gouwens & Wilson 2009 "unitary EPSC" value was located in this scan (that paper is about
passive cable fitting, not synaptic quantal size) — not found for that specific sub-ask.

## 5. Published multi-compartment model of an adult Drosophila VNC neuron from EM/LM morphology

**Not found.** Specifically checked and ruled out:

- Cheong HSJ, Eichler K, Stürner T, ... Tuthill JC, Phelps JS (2020/2021 Cell, *Reconstruction of motor
  control circuits in adult Drosophila using automated transmission electron microscopy*) — this is the
  EM reconstruction of all 507 adult leg/motor-control VNC neurons that the T1 skeletons in this project
  will come from. **Confirmed by direct WebFetch of the biorxiv full text**: the paper is purely
  structural/connectomic (NBLAST morphology comparison, synaptic connectivity, atlas registration) — "no
  mention of passive membrane parameters, electrical signal propagation simulations, or
  compartmental/cable modeling." No multi-compartment biophysical model is built from this EM data in
  this paper.
- Günay et al. 2015 (§1/§3): the closest thing to an EM/LM-morphology multi-compartment active model, but
  it is **larval**, **confocal light-microscopy** (not EM) reconstruction, and the cell is aCC/RP2, not an
  adult T1 class. Simulator: NEURON.
- A 2025 bioRxiv preprint, *Connectome simulations identify a central pattern generator circuit for fly
  walking*, runs dynamic simulations directly on the adult VNC connectome, but each neuron is represented
  by a **4-parameter rectified-tanh point-neuron activation model**, not a multi-compartment cable model —
  does not answer this question.
- A single-compartment, EM-connectivity-constrained biophysical model of mushroom-body output neuron
  MBON-α3 (EM architecture of 948 presynaptic Kenyon cells + patch-clamp membrane properties) was found in
  search snippets (likely Bennett, Li, et al., mushroom-body modeling literature, title/year not
  confirmed) — this is **brain, not VNC**, and **single-compartment**, so it does not answer this
  question either, but it is the closest analog for "EM connectivity + patch-clamp-derived membrane
  properties combined into a simulated model" that this scan turned up. Not independently verified;
  flagged for follow-up if a brain-side precedent is wanted.

**Bottom line for Q5**: as of this scan, no published adult Drosophila VNC multi-compartment cable model
built from EM (or LM) skeletons exists. This project's planned T1 leg-MN/premotor cable model would be a
first for the adult VNC specifically (larval VNC precedent: Günay et al. 2015, light microscopy).

## Caveats on this scan

- Several numeric triples (Gouwens & Wilson 2009 Rm/Cm/Ri; Haag/Borst blowfly Rm/Cm/Ri; Kazama & Wilson
  2008 EPSC/conductance numbers) came from the search tool's own synthesis rather than a page/table I
  directly read — they are internally plausible and partly cross-corroborated (Günay et al. 2015's own
  text), but should be re-verified against the primary PDF/figure before being written into the model
  registry as "measured" or "fitted" with a citation — pull the actual PDFs (jneurosci.org and
  sciencedirect/cell.com blocked WebFetch with 403 in this session; try via a library proxy or `gh`-style
  authenticated fetch, or ask Ben for institutional access) before promoting any of these three rows past
  "inferred."
- Only one of the five questions (Q2, Azevedo 2020) was fully primary-source-confirmed end-to-end, plus
  one full primary PDF for Q1/Q3 (Günay et al. 2015, all 10 pages read directly, Tables 1–3 transcribed
  verbatim above).
- No numbers in this document should be treated as "measured" for an **adult T1** leg MN or premotor
  neuron's Rm/Cm/Ri or SIZ location — none exist in the literature found. Everything usable for the T1
  model is either adult-PN-from-a-different-brain-region (Gouwens & Wilson), larval-VNC (Günay), or
  blowfly-visual-system (Haag/Borst), and must be labelled **inferred** (cross-type/cross-species
  generalization) if used, per the project's provenance rules — not relabelled measured or fitted for T1.
