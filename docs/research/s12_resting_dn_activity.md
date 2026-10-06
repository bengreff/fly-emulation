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

## Neck-position match of the rest-encoding DNs (Director item 2, 5 Oct, 03:56-04:05)

All matches below are **inferred**. Nothing here sets a model drive.

**Data.**
- BANC neck cross-section, Dataverse doi:10.7910/DVN/8TFGGB, version 8.1.
  - File `neck_connective_y92500.tab`: file id 11844868, md5 5c0857091b4f153610c108bfe069602e.
  - Downloaded as the original CSV to `data/raw/banc/dataverse_v8.1/neck_connective_y92500.orig` (430540 bytes; `data/raw/` is not tracked).
- The table gives one point per axon at BANC plane y = 92500.
  - 3648 of 3652 points join to `banc_888_meta` through its root-id columns.
  - 1270 points belong to DN axons.
- Scripts: `scripts/probes/neck_rest_dn_match.py` and `scripts/probes/rest_dn_reach.py`. Output: `runs/s12/dnrest/neck_rest_match.json` and `rest_dn_reach.json`.

**Geometry** (derived; BANC voxels 4 × 4 × 45 nm).
- The connective here is 59.8 µm wide and 26.4 µm deep.
- The giant fibers (DNp01) lie 9.8 µm apart.
- High z is dorsal. This is inferred from three agreeing checks:
  - the giant fibers sit near the high-z edge;
  - Kenyon cell somata have high z;
  - DNx01 lies 17-18 µm lower than the giant fibers, matching Aymanns' "large-caliber axons in the cervical connective positioned ventral to the giant fiber neurons axons".

**The paper's constraints** (eLife API full text, read 04:01).
- Positions: rest-encoding DNs "were located medially, close to the giant fibers, as well as in the lateral extremities of the connective (Figure 2e, olive circles)". They "were located in less consistent locations" across flies.
- Driver: it "lacks expression in the subesophageal zone (SEZ)". DNs with gnathal somata (DNg, DNge, DNxl; male-cns somaNeuromere LB, MX, MD or GNG) were therefore never recorded, so they are excluded.
- Imaging plane: the thoracic cervical connective, posterior to BANC's y = 92500 plane. Axon positions can shift between the two planes.
- ROIs: the "75-95 of the most distinct and clearly visible ROIs" per fly, each "likely" an "individual large axon or possibly tightly packed groups of smaller axons".

**Bands** (guessed translations of the words, each run at two widths).
- Medial: within 5 µm (narrow) or 8 µm (wide) of either giant fiber centre.
- Lateral: beyond the 90th (narrow) or 80th (wide) percentile of |x − midline| over all neck axons. These cuts are 22.1 µm and 19.3 µm.

**Confidence grades.**
- **low**: brain soma, in the narrow band, and every cell of the type in the wide band.
- **very low**: brain soma, in the band only partly or only at the wide width.
- **excluded**: SEZ soma, not in the driver line.

No match is graded higher than low, for four reasons:
- the positions are a qualitative, pooled description that the authors call inconsistent;
- 26 low types compete for what is probably a handful of rest ROIs per fly;
- the imaging plane differs from the BANC plane;
- the band widths are guessed.

**Result.**

| Band | Low | Very low | Excluded (SEZ) |
|---|---|---|---|
| Medial near GF | 21 types | 61 | 20 |
| Lateral extremity | 5 types | 21 | 156 |

- The lateral extremities are mostly SEZ axons, which Aymanns could not record. The brain-soma DNs there are few, which narrows that band to five low types.
- **Low, medial near GF:** DNa07, DNa09, DNa13, DNae002, DNae004, DNae005, DNae006, DNae009, DNae010, DNb01, DNb07, DNbe004, DNp07, DNp13, DNp26, DNp30, DNp51, DNp57, DNp62, DNpe027_ab, MDN.
- **Low, lateral extremity:** DNa02, DNa06, DNb06, DNp20, DNp33.
- Very-low types are listed in the JSON.

**Reach to the leg motor neurons** (structure only, m9r connectome).
- Method: signed synapses, direct and two-hop. Each path is weighted by the DN's share of the interneuron's input, as in `load_reflex_paths.py`.
- Each type is ranked against all 1318 DNs on |two-hop|. The median DN scores 14.8; the 90th percentile is 146.5.
- Low candidates above the 90th percentile:
  - **DNp07**, the landing DN of Ache 2019: 96.5th percentile, 117 direct synapses per cell onto leg MNs.
  - **DNa02**, a steering DN: 94.5th percentile, 462 direct.
- Next tier (77th-87th percentile): DNa13 (86.8), DNb06 (79.0), DNa06 (78.5), DNb01 (76.8), DNp26 (76.3), MDN (76.2), DNae005 (76.2) and DNb07 (75.9).
- Near zero (below the 15th percentile): DNp30, DNp62 and DNp20.
- DNp51 and DNpe027_ab are not types in the model.
- **In the model at rest** (seed 12, `dn_rest_s12.json`): every low candidate is at 0 Hz.

**Reading.**
- The rest-encoding blank now has named candidate locations, mostly brain DNs that sit dorsomedially beside the giant fibers.
- Two of these candidates have a strong, direct route to the leg pools: DNp07 and DNa02.
- DNa02 is a conflicting case. It "hyperpolarized whenever the fly stopped walking" (Rayshubskiy 2025). If Aymanns' encoding score is blind to sign, a rest-encoding DNa02 would encode rest by falling silent, which is not a tonic drive. Whether the score is sign-blind was not read.
- No rate follows from any of this.

**Next discriminating test.** Image or record DNp07 and DNa13 in resting flies with split-GAL4 lines. Both are brain DNs in the medial band with high leg reach.
