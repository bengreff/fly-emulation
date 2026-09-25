# Chemosensory transduction: evidence for wiring olfaction, humidity, temperature, CO2

Session 5, from a bounded literature and data extraction (read-only agent).
Counts from the local connectome were queried by the agent. Labels: **M**
measured, **D** derived, **I** inferred.

## Coverage

- **56 ORN types** in male-cns (M). The glomerulus comes from the type name; `somaSide` is empty, so side comes from the `instance` suffix.
- **51 have DoOR 2.0 consensus profiles** (M, normalised 0-1, not spikes/s). None: DA1 (Or67d; raw only in Dweck 2015b / van der Goes van Naters 2007), VA7m (orphan), VM6l/m/v (Rh50 + Ir25a ammonia sensing; Task 2022, Vulpe 2021; tuning I).
- IR-unit profiles (24 odours each) come from AL calcium imaging (Silbering 2011) and are relative only.
- **24 receptors (23 glomeruli) have absolute rates** in Hallem & Carlson 2006: spikes/s above spontaneous, 110 odorants at 10^-2 (M). They were recorded in the empty-neuron host (ab3A Δhalo), so the rates are heterologous. Spontaneous rates (spikes/s): Or2a 8, Or7a 17, Or9a 3, Or10a 14, Or19a 29, Or22a 4, Or23a 9, Or33b 25, Or35a 17, Or43a 21, Or43b 2, Or47a 1, Or47b 47, Or49b 8, Or59b 2, Or65a 18, Or67a 11, Or67c 6, Or82a 16, Or85a 14, Or85b 13, Or85f 7, Or88a 26, Or98a 12.

## Model form (suggested; D where built from M data)

- Amplitude: rate = SFR + DoOR x Rmax per unit, with SFR and Rmax from spike studies in DoOR's per-unit CSVs (D).
- Dynamics: LN filter (Martelli et al. 2013, intensity-invariant shape, Hill output) with Weber-adapting K_D, gain ∝ 1/mean within ~130 ms (Gorur-Shandilya et al. 2017), then a biphasic spike filter (Nagel & Wilson 2011: odour→LFP half-width 105 ms, latency < 10 ms). Kinetic constants are in the supplements, not yet extracted.
- **CO2** (ORN_V; Gr21a/Gr63a): steep dose-response from 0.1% to 100%, about half-maximal at ~5% (M qualitative; Jones 2007, Kwon 2007). No Hill fit found.
- **Humidity**: dry (HRN_VP4; Ir40a/Ir93a/Ir25a) and moist (HRN_VP5; Ir68a/Ir93a/Ir25a) cells give sustained, non-adapting, opposite responses over 7-90% RH. GCaMP only (Enjin 2016; Knecht 2016, 2017).
- **Temperature**: arista hot cells (TRN_VP2, Gr28b) and cooling cells (TRN_VP3a/b, Ir21a/Ir25a/Ir93a) are phasic, driven by dT/dt, with baseline firing (Gallio 2011; Ni 2013; Budelli 2019). Numeric rates not retrieved.
- **Label caution**: male-cns `class` for HRN_VP1l (hygro) and TRN_VP1m (thermo) is the reverse of their putative modalities (VP1l cooling, VP1m humid; Marin 2020). Use the modality, not `class`.

## Data source

DoOR.data (github.com/ropensci/DoOR.data, v2.0.1, CC BY-SA 4.0 per its DESCRIPTION file), plain `;`-separated CSVs: `door_response_matrix.csv` (691 odours x 78 units), `door_response_matrix_non_normalized.csv` (with an SFR row), `door_mappings.csv`, and one CSV per unit. Paper: Münch & Galizia 2016 Sci Rep 6:21841, 10.1038/srep21841.

## References

Hallem & Carlson 2006 Cell · Nagel & Wilson 2011 Nat Neurosci 10.1038/nn.2725 · Martelli et al. 2013 J Neurosci 10.1523/JNEUROSCI.0426-12.2013 ·
Gorur-Shandilya et al. 2017 eLife 10.7554/eLife.27670 · Jones et al. 2007 Nature 10.1038/nature05466 · Kwon et al. 2007 PNAS 10.1073/pnas.0700079104 ·
Enjin et al. 2016 Curr Biol 10.1016/j.cub.2016.03.049 · Knecht et al. 2016 eLife 10.7554/eLife.17879 · Knecht et al. 2017 eLife 10.7554/eLife.26654 ·
Gallio et al. 2011 Cell 10.1016/j.cell.2011.01.028 · Ni et al. 2013 Nature 10.1038/nature12390 · Budelli et al. 2019 Neuron 10.1016/j.neuron.2018.12.022 ·
Marin et al. 2020 Curr Biol 10.1016/j.cub.2020.06.028 · Task et al. 2022 eLife 10.7554/eLife.72599 · Vulpe et al. 2021 Curr Biol 10.1016/j.cub.2021.05.025
