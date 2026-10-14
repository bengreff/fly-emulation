Gathered by Sonnet subagent, 13-14 Oct 2026; not yet checked row by row

# Leg MN firing rates, premotor IN bursting, intrinsic burstiness, unitary PSPs — literature scan

All numbers below are from primary-text searches of full article XML/HTML (not abstracts only, except where
noted). Labels: **measured (stated in text)**, **read from figure (approximate, not independently verified
against the image)**, or **not found**.

## Q1. Leg motor neuron firing rates

**Azevedo, Dickinson, Gurung, Venkatasubramanian, Mann, Tuthill 2020, eLife 9:e56754**
(DOI [10.7554/eLife.56754](https://doi.org/10.7554/eLife.56754); fetched full JATS XML)

- Recording condition — **measured (stated in text)**: whole-cell current-clamp of genetically identified
  slow/intermediate/fast tibia flexor MNs "while the fly pulled on the force probe" during **spontaneous tibia
  movement in a tethered, non-walking fly** (Results §2-2, Figure 2D). Walking-ball experiments (Figure 7,
  Methods §4-14/4-15) were optogenetic activation/silencing + behavior tracking on a spherical treadmill —
  **no electrophysiology was recorded during walking**; Fig. 7 is purely behavioral.
- Resting/spontaneous firing rate — **measured (stated in text)**: "the slow neuron had a resting spike rate
  of approximately 30 Hz" (Figure 3D, n=14 slow cells; fast n=15 and intermediate n=11 were silent at rest, i.e.
  ≈0 Hz baseline). Two individual example traces: a slow MN "rested around −53 mV, with a spontaneous spike rate
  of 12 Hz" (Fig. 2H) and another "rested around −51 mV, with a spontaneous spike rate of 28 Hz" (Fig. 2K).
- Firing rate *during* flexion bouts for intermediate/fast MNs — **not found**: text states only that firing
  rate increases during tibia flexion (Fig. 2D) and gives force vs. spike-count relations (Fig. 4D, 4E) rather
  than a quantified Hz value during movement for intermediate/fast cells.
- Recruitment order — **measured (stated in text)**, verbatim: "Recordings during spontaneous leg movements
  revealed a recruitment hierarchy: slow motor neurons typically fire first, followed by intermediate, then fast
  neurons (Figure 5)." Also: "recruitment order is occasionally violated" (§3-1).
- Spike-frequency adaptation — **not found**. No adaptation ratio or time constant anywhere in the main or
  supplementary text; the only "adapt-" hit in the whole XML is an unrelated reference title ("Mechanosensation
  and adaptive motor control in insects").
- Input resistance (context for excitability gradient, measured): fast 150 MΩ, intermediate 300 MΩ, slow 700 MΩ
  (Fig. 3E text).

**Step frequency during walking (not MN spike rates, but constrains plausible MN burst rate):**

- Mendes, Bartos, Akay, Márka, Mann 2013, eLife 2:e00231 (DOI [10.7554/eLife.00231](https://doi.org/10.7554/eLife.00231);
  fetched full JATS XML) — **measured (stated in text)**: "step period... reaches a steady state of about ∼60 ms,
  corresponding to a frequency of **16 cycles per s**" above ~30 mm/s forward speed (Figure 2C). This is the
  clearest directly-measured adult free-walking step-frequency ceiling found.
- Wosnitza, Bockemühl, Dübbert, Scholz, Büschges 2013, J Exp Biol 216:480-491 — WebFetch of the publisher page
  could not locate an explicit Hz value; the paper reports cycle period (ms) and speed (body lengths/s) and
  states "Drosophila controls its walking speed almost exclusively via step frequency" — **read from figure
  (approximate)** at best for an Hz number; treat as not found for a citable number without the PDF.
- DeAngelis, Zavatone-Veth, Clark 2019, eLife 8:e46409 (fetched full JATS XML) — caution: the "5 to 12.5 Hz for a
  tripod gait" figure found in this text is from the paper's **synthetic/model data generation** ("generated
  trajectories with swing durations iid from a uniform distribution corresponding to stepping frequencies between
  5 and 12.5 Hz for a tripod gait"), i.e. a modeling assumption, **not a measured value** from their fly data.
  The paper's real kinematic data are reported as forward velocity (mm/s: slow 0–10.2, medium 10.2–19, fast >19)
  and as "mean stepping frequency" color-coded on a UMAP manifold (Figure 4A) without a plain-text Hz scale found
  in the body text.

**Calcium imaging / EMG during walking:**

- Chen, Hermans, Viswanathan, Fortun, Aymanns, Unser, Cammarato, Dickinson, Ramdya 2018, Nat Commun 9:4390
  (DOI 10.1038/s41467-018-06857-z) — reports VNC population activity during walking/grooming and descending-neuron
  (MDN/MAN/A1) encoding; no MN firing-rate numbers located in available excerpts — **not found** within budget
  (would need full-text pull of figures, not done).
- No EMG/extracellular nerve recording of leg MNs during walking with spikes-per-step counts was located; Azevedo
  2020's EMG was from the tethered spontaneous-movement preparation, not walking (see above). **Not found** for a
  walking-EMG spikes/step number.

## Q2. Leg premotor interneuron recordings during walking/rhythmic activity

No whole-cell recording of an identified VNC leg-premotor interneuron (13A/13B/19A/20A/21A/9A/10B or similar)
showing spike bursts locked to stepping was located in the time budget. Specifics:

- Bidaye, Laturney, Chang, Liu, Bockemühl, Büschges, Scholz 2020, Neuron 108:469-485 — this paper is about
  **brain descending neurons** (P9, BPN) that *initiate* forward walking, not VNC premotor interneuron
  electrophysiology during stepping. No burst-rate data for VNC premotor INs. **Not applicable / not found.**
- Agrawal, Dickinson, Sustar, Gurung, Shepherd, Truman, Tuthill 2020, eLife 9:e60299 ("Central processing of leg
  proprioception in Drosophila") — whole-cell recordings from 13Bα (GABAergic, hemilineage 13B) VNC neurons, but
  these are characterized by their response to **passive leg movement/proprioceptive stimuli** (tibia extension
  encoding), not by bursting during self-generated walking. No burst-during-stepping firing rate found.
- "Inhibitory circuits control leg movements during Drosophila grooming" (eLife reviewed preprint 106446 /
  biorxiv 2024.06.05.597468) — patch-clamp of 13A/13B/9A hemilineage neurons, but during **grooming**, not
  walking; could not retrieve the eLife XML (404 on the expected URL pattern) within budget to extract numbers.
  **Not found** (access failure, not ruled out as absent from the paper).
- Lesser, Yang, Deng, Lee, ... (2024, "Synaptic architecture of leg and wing premotor control networks in
  Drosophila") — this is a connectomics/EM paper on synaptic architecture, not a physiology/burst-rate study;
  no firing-rate data expected. **Not applicable.**
- Chen et al. 2018 (above) — calcium imaging shows population-level VNC activity patterns during walking but
  calcium signals give no spike rate; duty-cycle/phase-in-step-cycle values were not extracted within budget.

**Bottom line for Q2: no measured burst firing rate, spikes-per-burst, or burst duration for an identified leg
premotor interneuron during walking or fictive stepping was found.** This looks like a genuine gap in the adult
Drosophila literature, not just a search miss — all four candidate papers checked are proprioceptive-input,
descending-command, grooming, or purely anatomical studies. A larval CPG premotor-interneuron burst number
(A27h, below) is available but is for peristalsis, not leg stepping.

## Q3. Intrinsic burstiness properties of central interneurons

- Spike-frequency adaptation (olfactory PNs/LNs, Gouwens & Wilson 2009; Seki, Rybak, Wicher, Sachse, Hansson 2010,
  J Neurophysiol 104(2); Nagel & Wilson antennal-lobe LN/PN work) — WebSearch surfaced that Seki et al. 2010
  classified AL local interneurons into "four classes... showing differences in firing patterns, degree of spike
  adaptation, and amplitude of spike afterhyperpolarization," which is exactly the kind of number requested, but
  the full text (journals.physiology.org and EuropePMC mirror) returned HTTP 403 (paywalled) and could not be
  retrieved within budget. **Not found (access blocked)** — flagging as a concrete follow-up target rather than
  a true absence.
- Gouwens & Wilson 2009 (J Neurosci 29:6239, "Signal propagation in Drosophila central neurons") is a passive
  electrotonic-structure/compartmental-model paper built from PN recordings; it is not itself an adaptation-ratio
  source. **Not found / wrong target** for Q3 as stated.
- Nagel & Wilson 2011, Nat Neurosci — a WebSearch snippet surfaced "ORNs fired with a rate of 20 Hz" at rest and
  a phenomenological spike-triggered-adaptation time constant τ_A used in their model, but this is sensory
  receptor neuron (ORN) modeling, not a central interneuron, and the exact τ_A value was not independently pulled
  from primary text in this session. **Not found (not verified, and wrong cell class for Q3)**.
- Azevedo et al. 2020 MN adaptation — confirmed **not found** (see Q1; no adaptation data in the whole-cell MN
  paper).
- Larval premotor interneuron intrinsic properties (Kohsaka et al.; Fushiki, Zwart, Kohsaka 2016 eLife 5:e13253,
  "A circuit mechanism for the propagation of waves of muscle contraction in Drosophila", DOI
  10.7554/eLife.13253) — fetched full JATS XML. No explicit ADP/rebound/plateau numeric value found in text for
  A27h or GDL. The paper documents rhythmic endogenous bursting of A27h locked to peristaltic waves (Fig. 5E) and
  coherence with aCC (Fig. 5F) but reports this qualitatively/graphically, not as a burst-duration or spikes/burst
  number in the text. **Read from figure (approximate) at best; no citable number found in text.**
- Choi, Park, Griffith 2004, J Neurophysiol 91:2353 ("Electrophysiological and Morphological Characterization of
  Identified Motor Neurons in the Drosophila Third Instar Larva CNS") — this is identified **motor neurons**
  (aCC/RP2-type), not interneurons as the brief implied; found a qualitative statement about first-spike delay
  tied to a Shal-like IA current kinetics, but no adaptation ratio number was retrieved from the paywalled full
  text. **Not found (access not completed within budget).**

**Overall for Q3: no adult or larval central-interneuron adaptation ratio, ADP amplitude/duration, or rebound/
plateau number was confirmed from primary text in this session.** Several named sources (Seki 2010, Choi 2004)
plausibly contain exactly this data behind a paywall that WebFetch could not pass; these are the recommended next
targets (try sci-hub-free channels, institutional access, or request PDFs directly) rather than literature gaps.

## Unitary premotor-interneuron → leg-MN PSP amplitude

No adult leg-premotor → leg-MN unitary PSP was found. The best available adult/larval data are from the **larval
intersegmental (axial locomotion) system**, not legs, and are evoked (optogenetic/current-command), not
single-spike-triggered unitary PSPs in the strict sense:

- Fushiki, Zwart, Kohsaka, Landgraf, Nose 2016, eLife 5:e13253 — paired recording of A27h (excitatory premotor
  IN) and aCC MN: a 50 pA current command drives A27h spiking, and the postsynaptic aCC response is shown only
  graphically (Figure 5C–D, "maximum voltage response... mean of 100 trials") with a 0.5 mV scale bar on the
  presynaptic (A27h) trace inset — **no explicit postsynaptic mV amplitude number is stated in the text.**
  **Read from figure (approximate)/not found as a text number.**
- Carreira-Rosario / Baines lab, "Electrophysiological validation of premotor interneurons monosynaptically
  connected to the aCC motoneuron in the Drosophila larval CNS," J Neurosci 42(35):6724 (2022), DOI confirmed via
  PMC9435966 — **measured (stated in text)**, from paired current-/voltage-clamp recordings (optogenetic
  ChR+NaChBac activation of the presynaptic IN, TTX ± to isolate monosynaptic component):
  - A18a (excitatory, cholinergic) → aCC: voltage-clamp current density **−2.74 ± 1.09 pA/pF (n=5)** without TTX,
    **−1.49 ± 0.73 pA/pF (n=6)** with TTX (Figure 4C); a second driver line gave −3.59 ± 1.10 pA/pF (n=5) down to
    −1.25 ± 0.55 pA/pF (n=10).
  - A18b3 → aCC: −0.09 ± 0.09 pA/pF (n=8) / −0.01 ± 0.01 pA/pF (n=9) with TTX — **no monosynaptic connection
    detected** (i.e., a measured null result).
  - A23a (inhibitory, GABAergic) → aCC: current-clamp hyperpolarization **−1.88 ± 0.87 mV (n=10)** without TTX,
    **−1.66 ± 0.80 mV (n=11)** with TTX, recorded at a −40 mV holding/driving potential.
  - A31k (inhibitory) → aCC: **−2.82 ± 0.51 mV (n=10)** without TTX, **−2.11 ± 0.72 mV (n=11)** with TTX
    (Figure 7D), at −40 mV.
  - Caveat: these are evoked responses to optogenetically-driven presynaptic firing (not necessarily single
    spikes), reported as either current density (pA/pF, voltage-clamp) or voltage deflection (mV, current-clamp)
    — treat as an order-of-magnitude PSP/PSC scale for a single larval premotor-IN→MN connection, not a precise
    unitary quantal amplitude.

No equivalent number for an adult leg hemilineage interneuron → leg MN connection was found.

## Summary table

| Question | Best number found | Status | Source |
|---|---|---|---|
| Slow tibia flexor MN spontaneous rate | ~30 Hz (range 12–28 Hz across example cells) | measured | Azevedo 2020, Fig. 2H/2K/3D |
| Intermediate/fast tibia flexor MN spontaneous rate | 0 Hz (silent at rest) | measured | Azevedo 2020, Fig. 3D |
| Intermediate/fast MN rate during flexion | — | not found | Azevedo 2020 (qualitative only) |
| Adult walking step frequency ceiling | ~16 Hz (step period plateau ~60 ms, >30 mm/s) | measured | Mendes 2013, Fig. 2C |
| MN recruitment order | slow → intermediate → fast | measured | Azevedo 2020, Fig. 5 |
| MN spike-frequency adaptation | — | not found | Azevedo 2020 (absent) |
| Leg premotor IN burst rate during walking | — | not found | (no paper located with this data) |
| Central IN adaptation ratio / ADP | — | not found (paywalled) | Seki 2010; Choi 2004 |
| Larval excitatory premotor IN → MN PSP | qualitative only, no mV number in text | fig-only | Fushiki 2016 |
| Larval GABAergic premotor IN → aCC PSP | −1.9 to −2.8 mV | measured | Baines lab, JNeurosci 2022 (PMC9435966) |
| Larval cholinergic A18a → aCC PSC | −1.5 to −3.6 pA/pF | measured | same |

## Tool-budget note

~37 of the allotted ~40 tool calls were used. Q2 (leg premotor IN burst data during walking) returned nothing
positive after four distinct search strategies; Q3's two most promising named sources (Seki 2010, Choi 2004) were
identified but blocked by paywalls (HTTP 403) rather than exhausted as negative results — worth a follow-up pass
with institutional/PDF access rather than being treated as "not in the literature."
