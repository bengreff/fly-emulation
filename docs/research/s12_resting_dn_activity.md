# Resting activity of descending neurons, VNC and whole brain: literature search

Date: 2026-10-05, about 03:45-03:52. Director leads of 03:00 on F-STAND-3. Web search by one Sonnet agent (about 5 minutes, 45 tool calls), plus my own read of Rayshubskiy et al. 2025. Labels: READ means the text was read (by fetch); SUMMARY means only a search-engine summary or abstract was reachable, and no number from it is used.

## Answer

- **No paper found gives a resting firing rate in Hz for any identified Drosophila descending neuron (DN).**
- **The one population measure of DNs at rest is qualitative and points to quiet DNs.** Aymanns, Chen & Ramdya 2022 imaged about 100 DNs per fly with calcium indicators. "Only a very small fraction of DNs encode resting." About 60% encode walking and about 15% head grooming.
- **Whole-VNC and whole-brain imaging give no resting rate.** Calcium signals cannot be converted to Hz without a calibration these papers do not give.
- **Lead (1) therefore supplies no number.** The real fly's resting support drive is still unmeasured. Its location (descending, VNC premotor, or sensory feedback) is also unresolved.

## Sources

1. **Rayshubskiy et al. (Wilson lab), "Neural circuit mechanisms for steering control in walking Drosophila", eLife 2025 (bioRxiv 2020.04.04.024703).** PMC12279373. READ (my fetch and the agent's).
   - Quote: "DNa02 hyperpolarized whenever the fly stopped walking (Figure 6A and B)".
   - Quote: "it continued responding to lateralized odors even when the fly was stopped."
   - The text gives no rate or membrane potential for the stopped fly; the figure traces were not read.
   - A search-engine summary claimed a background of about 5 Hz. It was not found in the text and is not used.
2. **Aymanns, Chen & Ramdya, "Descending neuron population dynamics during odor-evoked and spontaneous limb-dependent behaviors", eLife 2022;11:e81527.** READ.
   - Quotes: "Only a very small fraction of DNs encode resting"; "The largest fraction (~60%) of DNs encode walking"; "The second largest group of DNs encode head grooming (~15%)".
   - The rest-encoding DNs lie "medially, close to the giant fibers, as well as in the lateral extremities".
   - The authors suggest they "may suppress other behaviors or could actively drive the tonic muscle tone required to maintain a natural posture". This is a hypothesis in the discussion, not a measurement.
   - Preparation: tethered on a spherical treadmill; GCaMP6s ΔF/F; cell types not identified.
3. **Chen, Hermans, Viswanathan et al. (Ramdya lab), "Imaging neural activity in the ventral nerve cord of behaving adult Drosophila", Nat Commun 2018;9:4390.** READ (agent).
   - No quantitative comparison of rest against walking.
   - Baseline fluorescence is a technical normalisation, not a behavioural rest state.
   - MDN activity is described only relative to backward-walking onset.
4. **Aimon, Katsuki, Jia et al., "Fast near-whole-brain imaging in adult Drosophila during responses to stimuli and behavior", PLoS Biol 2019.** READ (agent).
   - "global activity (average ΔF/F) was correlated with walking (R² = 0.37 +/− 0.19 ... N = 6)".
   - Grooming gave "only local activation".
   - No fraction active at rest; calcium only.
5. **Brezovec et al., "Mapping the neural dynamics of locomotion across the Drosophila brain", Curr Biol 2024.** SUMMARY only (publisher 403). Reportedly about 40% of brain volume carries locomotor signals. Not used.
6. **Mann, Gallen & Clandinin, "Whole-brain calcium imaging reveals an intrinsic functional network in Drosophila", Curr Biol 2017.** Not read for resting levels. My brief to the agent miscited it as Mann, Gordon & Scott, Neuron.
7. **Other sources, SUMMARY only or with no resting rate in the readable text:**
   - Sen et al. 2017 Curr Biol (MDN). A summary says "MDNs were spontaneously active in stationary flies"; unverified, no number.
   - Bidaye et al. 2018 eLife 7:e38554 (MDN; READ, no resting rate).
   - Ache et al. 2019 Nat Neurosci (DNp07/DNp10).
   - von Reyn et al. 2014 Nat Neurosci (giant fiber).
   - Schnell, Ros & Dickinson 2017 Curr Biol.
   - Namiki et al. 2022 Curr Biol (DNg02).
8. **Already in hand: Azevedo et al. 2020 eLife 9:e56754** (`s12_resting_mn_rates.md`).
   - The slow tibia flexor fires about 30 Hz at rest.
   - A nicotinic antagonist (MLA 1 µM) lowers that rate and the resting force by about 1.5 µN.
   - So part of the resting motor neuron drive is cholinergic synaptic input (inferred). The input could be central premotor neurons or cholinergic leg sensory afferents; the paper does not separate them.

## Not found

- A Hz resting rate for DNa01, DNa02, the giant fiber, DNp07, DNp10, DNg02, MDN, BPN or P9.
- Resting activity of coxa, trochanter or femur motor neurons or their premotor interneurons, by imaging or electrophysiology.
- Spontaneous rates for other central types: none surfaced in this search. The model's parameter table already cites PN 1-5 Hz and KC about 0.1 Hz.
