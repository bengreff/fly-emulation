# Literature extraction, session 6 (leads, partly verified)

Produced by one read-only Explore agent, 25 Sept 2026. **These are leads.** A
DOI marked (unverified) was not confirmed by loading its page. A value enters
a params table only with the label its use justifies.

> **Update (session 6b/6c):** the raw recordings of two slow MNs were analysed. Measured Rin 1,041 and 617 MΩ; spontaneous rate 24.8 and 23.5 Hz (F-AZ-1, F-AZ-3). Those supersede the class values quoted below for model use.

## Leg motor units: Azevedo et al. 2020, eLife 9:e56754, 10.7554/eLife.56754 (unverified DOI; text read at PMC7347388)

The tibia flexor has about 15 motor neurons.

| Class | Count | Force per spike | Half-max force | Rin | Vrest | Rest rate |
|---|---|---|---|---|---|---|
| fast (R81A07) | 1 | ~10 µN | ~8.5 ms | 150 MΩ | −68 mV | silent |
| intermediate (R22A08) | 2–5 | ~1 µN | ~8.5 ms | 300 MΩ | −60 mV | silent |
| slow (R35C09) | 8–9 | <0.1 µN | gradual, no peak within 500 ms | 700 MΩ | −48 mV | ~30 Hz |

- Force was measured at the probe and tibia tip. The probe calibration is 5 µm = 1.1 µN.
- Co-activation gives "close to 100 µN".
- Dryad 10.5061/dryad.76hdr7stb is confirmed: 48.8 GB, per-cell zips and `MN_anatomy_confocal_measurements.xlsx`.

## Opsins: Salcedo et al. 1999, J Neurosci 19:10716, 10.1523/JNEUROSCI.19-24-10716.1999

- ERG spectral sensitivity peaks, with each opsin expressed in R1–R6 (Fig 5 legend): Rh1 478, Rh3 345, Rh4 375, Rh5 437, Rh6 508 nm.
- Pigment absorbance: Rh5 442 nm, Rh6 515 nm.
- Sharkey et al. 2020, Sci Rep 10:18242 (unverified): Rh1 485–490, Rh3 330, Rh4 355, Rh5 435 nm. Their Rh6 value is shifted by screening pigment.

## Conduction and delays

- **Giant fibre velocity:** 1.15 ± 0.09 m/s at 1 h after eclosion and 2.07 ± 0.21 m/s at 24 h. Axon about 7 µm across. Kadas, Duch & Consoulas 2019, eNeuro 6:ENEURO.0181-19.2019 (unverified).
- **Giant fibre latencies:** stimulus to TTM 0.93 ms, to DLM 1.44 ms in young flies. The model estimate of NMJ delay is ~0.35 ms. Augustin et al. 2017/2019 (unverified).
- **Larval axons:** motor 0.196 m/s and sensory 0.129 m/s; mean axon radius 0.19 µm. Kottmeier et al. 2020, Nat Commun 11:4491 (unverified).
- **Cockroach giant interneurons:** 40–60 µm across, 5–7 m/s (unverified). Taken together, velocity scales roughly with √diameter.
- No measured central synaptic delay was found.

## Leg proprioceptors: Mamiya et al. 2018, Neuron 100:636; Mamiya et al. 2023, Neuron, 10.1016/j.neuron.2023.07.009

- The femoral chordotonal organ has 152 cells:
  - club (vibration, tonotopic 100–1600 Hz): 66;
  - hook-extension plus claw: 58;
  - hook-flexion: 28.
- **Claw (position) cells** are goniotopic. For flexion-tuned claw cells, the angle at half-maximal activity spans about 20–80° of femur-tibia angle, ±20° across the map. Extension-tuned claw cells cover about 90–180°.
- **Hook cells** are phasic and direction-selective.
- Data are calcium imaging only; no firing rates.

## Posture

- No absolute standing thorax height was found in the literature. Body length is 2.04 mm (Pratt et al. 2024).
- Femur-tibia range during walking: front 97°, middle 22°, hind 84° (Haustein et al. 2024).

## VNC interneurons and motor-neuron inputs (third agent, session 6b; leads)

- **Azevedo 2020:** "Spontaneous firing rate in slow motor neurons is set by excitatory synaptic input." LJP correction −13 mV.
- **Agrawal et al. 2020, eLife 9:e60299.** Whole-cell recordings from T1; LJP 12 mV subtracted.
  - 13Bα: GABAergic and **nonspiking**; graded, tonic, non-adapting position coding that rises past ~90°; example Vm −44 to −61 mV.
  - 9Aα: GABAergic and spiking, up to ~250–300 Hz evoked. Picrotoxin depolarises it at rest, so it receives tonic GABA.
  - 10Bα: cholinergic and effectively nonspiking.
  - Raw data: Dryad 10.5061/dryad.k3j9kd55t; open Zenodo mirror 4307018 (CC0), Ephys_data.zip 7.5 GB.
- **Lesser et al. 2024, Nature:** "GluCl is the most highly expressed glutamate receptor in MNs" (GluRIA/IB lower). This is evidence against the excitatory-glutamate hypothesis rejected in F-AZ-2.
- **Gowda et al. 2018, PNAS:** Rdl knockdown in leg MNs impairs walking; preliminary GluCl knockdown too.
- **Locust prior** (Burrows & Siegler 1978; Laurent 1991): premotor local interneurons are nonspiking.
  - Some release transmitter tonically at rest.
  - A 2 mV depolarisation suffices for release in others.
  - Vm swings up to 15 mV; resting Vm about −58 mV.
- No recordings were found of 13A, 19A, 21A, 3A, 8A or 14A interneurons.
