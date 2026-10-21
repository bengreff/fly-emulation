# Hemilineage 16B (I1's class): spiking or graded release? Literature scan for arm A

Sonnet subagent (read-only), 20 Oct 2026, about 35 tool calls. **Unchecked by the lead** except where marked; the agent
reports, for each item, whether it read the full text, only the abstract, or a secondary source.

## Bottom line
- **No recording of any 16B neuron, of IN16B036 (male-CNS I1) or IN16B007 (MANC I1) exists** in the literature searched.
  Whether I1 spikes or releases graded is unmeasured. Arm A is a diagnostic about an unmeasured class property.
- Harris et al. 2015 (eLife 4:e04493) excluded 16B from their hemilineage activation screen: "Of the 33 major thoracic
  hemilineages, hemilineages 0A, 4A, 16B and 17A are not addressed in this study." (full text)
- Lacin et al. 2019 (eLife 8:e43701): 16B is glutamatergic (VGlut+). Transmitter only, no physiology.
- Allen et al. 2020 (eLife 9:e54074): no statement on 16B or on para (NaV) levels by hemilineage found.
- Pugliese et al. 2025 (bioRxiv 10.1101/2025.09.12.675944) name "E1 (IN17A001), E2 (INXXX466), and I1 (IN16B036)" and justify
  a rate model because "some neurons in the insect VNC, including premotor neurons active during walking, are nonspiking
  [39-42]". That is a general modelling choice, not a measurement of I1 (full text; reference list via a secondary query).

## Sibling Drosophila VNC hemilineages (Agrawal et al. 2020, eLife 9:e60299, in vivo whole-cell, full text)
- 13Bα (GABA): non-spiking, "All 13Bα cells lacked detectable action potentials"; graded, tonic, non-adapting responses.
- 10Bα: mostly non-spiking, "Current injection failed to evoke identifiable action potentials" (rare spike-like events).
- 9Aα, 9Aα2: spiking.
- So within the leg premotor hemilineages, both modes occur. The mode is a per-hemilineage unknown; 16B could be either.

## Graded-release bounds (locust non-spiking local interneurons onto leg MNs)
- Burrows & Siegler 1978, J Physiol 285:231-255 (PMC1281754), abstract level:
  - tonic release at rest in some cells: "At their resting potential some interneurones tonically release sufficient
    transmitter to have a measurable post-synaptic effect";
  - release threshold: "a depolarization of only 2 mV is sufficient to effect the release of transmitter";
  - operating range: "membrane potentials of non-spiking interneurones can fluctuate by as much as 15 mV during active
    movements";
  - postsynaptic effect: "individual p.s.p.s as large as 5 mV can be recorded".
- Burrows & Siegler 1976, Nature 262:220-224: transmission without spikes (secondary).
- Büschges 1990 (J Exp Biol 151:133) and 1995 (J Neurobiol 27:488): stick-insect non-spiking interneurons in rhythm
  generation; no numbers retrieved (paywalled).
- Not found: an input-output gain curve (post mV per pre mV), absolute resting potential, saturation span.

## Use in arm A (lead's reading, inferred)
The model's graded release starts at rest and saturates at threshold (7 mV span, no release at rest; `lif.Network.step`).
Against the locust bounds: release onset 0-2 mV above rest (model 0) and an operating range up to 15 mV (model 7) are
inside. The rate-equivalent at saturation (`cell_type:all|graded_rmax` 100 Hz) is guessed and has no insect bound here.

| Item | Finding | Prep | Source | Read as | Label |
|---|---|---|---|---|---|
| 16B transmitter | glutamate | Drosophila IHC | Lacin 2019 | full text | measured |
| 16B physiology | none recorded | - | Harris 2015 and all searched | full text | absent |
| 13Bα | non-spiking | in vivo whole-cell | Agrawal 2020 | full text | measured |
| 10Bα | mostly non-spiking | in vivo whole-cell, n 18 | Agrawal 2020 | full text | measured |
| 9Aα | spiking | in vivo whole-cell | Agrawal 2020 | full text | measured |
| locust NSI release onset | ~2 mV above rest; some tonic at rest | intracellular | Burrows & Siegler 1978 | abstract | measured |
| locust NSI operating range | up to 15 mV | intracellular, active movement | Burrows & Siegler 1978 | abstract | measured |
