# S12: measured values for the five dynamics rungs (survey, 6 October 04:35-)

Director order 02:10 (DECISIONS 6 October 04:36): fill spike-frequency adaptation, short-term
depression/facilitation, membrane noise, graded against spiking mode, and per-type membrane time
constant model-wide, measured rows first. This note lists what open sources give. It is evidence for
pre-registrations, not a fill.

Labels: **re-read** = I saw the number in the source text this session (quote kept); **read (agent)** =
a survey agent quoted it from the PMC text and I did not re-open it; **unverified** = search snippet or
secondary synthesis only, not usable as a value. Sources were PMC / Europe PMC / eLife open text; local
copies are in `data/raw/` where noted (gitignored).

## Rung 5: membrane time constant and passive values

| Cell | Quantity | Value | Method | Label | Source |
|---|---|---|---|---|---|
| HS (lobula plate, *Drosophila*) | τ_m | 4.3 ± 1.4 ms at 30 s, 4.9 ± 1.3 ms at 10 min after break-in (mean ± s.d.) | whole-cell current clamp, 50 pA hyperpolarising steps, single-exponential fit | re-read: "Both input resistance and membrane time constant increased during the recording period from 176±46 to 205±45 MΩ and from 4.3 ± 1.4 to 4.9±1.3 ms respectively within 10 minutes" | Cuntz et al. 2013 PLoS One 8:e71540 (PMC3747245; `data/raw/cable_s12/`) |
| HS | R_in | 176 ± 46 to 205 ± 45 MΩ | same | re-read (same sentence) | same |
| Slow tibia flexor MNs (4 cells) | τ_m | 15.5-16.6 ms | fit to Azevedo 2020 raw current steps | measured this class (F-AZ-2; already a model row, 60 cells at 16 ms) | Azevedo et al. 2020 eLife 9:e56754 |
| AL projection neuron | R_in | 598.0 ± 69.3 MΩ, n 14, antennae removed | in vivo whole-cell | re-read earlier (`s12_central_fi.md`) | Gouwens & Wilson 2009 J Neurosci 29:6239 (PMC2709801) |
| DM1 PN, 3 cells | R_m × C_m | 8.3 × 2.6 = 21.6 ms; 20.4 × 1.5 = 30.6 ms; 20.8 × 0.8 = 16.6 ms | derived here from the fitted cable parameters (NEURON fits to somatic pulses) | derived (fitted inputs) | same; table in `s12_compartments.md` |
| AL PN | resting potential | −57.8 ± 1.5 mV (n 12) corrected for the seal; −47.8 ± 1.6 mV uncorrected whole-cell | cell-attached-based correction | read (agent) | same |
| ORN→PN unitary EPSP | decay time constant | "roughly 30 msec" | citing Kazama & Wilson 2008 | re-read (secondary citation) | Jeanne & Wilson 2015 Neuron (`data/raw/central_fi_s12/`) |
| Kenyon cell | R_in about 10 GΩ; EPSC decay 2.8 ± 1.2 ms | | whole-cell | unverified (image-only PDF) | Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734 |

Note: Hafez et al. 2023's MBON model uses a 15 ms cell time constant (author response); it is a model
choice, not a measurement.

## Rung 4 and the motion pathway: response kinetics (not membrane τ)

| Cell | Quantity | Value | Method | Label | Source |
|---|---|---|---|---|---|
| Mi1 | linear filter peak time | 71 ms (SEM 3.8) | in vivo whole-cell, white-noise contrast, linear filter | re-read: "For Mi1 the average peak response time was 71 ms after a contrast change (SEM=3.8 ms) while it was 53 ms (SEM=5.2 ms) for Tm3" | Behnia et al. 2014 Nature 512:427 (PMC4243710; `data/raw/vision_rest_s12/behnia2014_pmc_text.txt`) |
| Tm3 | same | 53 ms (SEM 5.2) | same | re-read | same |
| Tm1 | same | 56 ms (SEM 3.8) | same | re-read: "the average peak time was 56 ms (SEM=3.8 ms) for Tm1 and 43 ms (SEM=2.7 ms) for Tm2" | same |
| Tm2 | same | 43 ms (SEM 2.7) | same | re-read | same |

These are whole-pathway filter peaks (photoreceptor to the recorded cell), not membrane time
constants. A rung 5 fill can use them only as held-out targets for the chain, not as τ_m rows.

## Rung 2: short-term plasticity

| Synapse | Quantity | Value | Method | Label | Source |
|---|---|---|---|---|---|
| ORN→PN (DM6, VM2), total EPSC, 10 Hz train | depression fraction f, recovery τ | f 0.78, τ 893 ms (n 19 PNs) | in vivo whole-cell, fit of a simple depression model | re-read: "Line is a fit of the simple synaptic depression model (Equation 1, see Methods; f = 0.78 and τ = 893 ms)" (already the model's `afferent:ORN\|measured_depression`, U = 1 − f = 0.22) | Nagel, Hong & Wilson 2015 Nat Neurosci 18:56 (PMC4289142) |
| ORN→PN, IMI-resistant (fast) component | f, τ | 0.77, 1006 ms | same | re-read: "For the IMI-resistant component, these parameters were f = 0.77, and τ = 1006 ms, whereas for the curare-resistant component, these parameters were f = 0.91, τ = 629 ms" | same |
| ORN→PN, curare-resistant (slow) component | f, τ | 0.91, 629 ms | same | re-read (same sentence) | same |
| ORN→PN (DL5, DM4) | release probability p; sites N; quantal size q | 0.79 ± 0.02; 51.4 ± 7.8; 1.05 ± 0.11 pA | multiple-probability fluctuation analysis | read (agent) | Kazama & Wilson 2008 Neuron 58:401 (PMC2429849) |

Kazama's p (0.79, per release site, first spike) and Nagel's per-spike depression (1 − f = 0.22 in a
train) are different quantities from different glomeruli; they are not interchangeable and are not a
conflict to resolve by averaging.

Not short-term plasticity: KC→MBON-γ1pedc depression after odour-DAN pairing (Hige et al. 2015
Neuron 88:985, PMC4674068; EPSC charge −90 ± 3.7%, n 5; read (agent)) is lifetime plasticity, already
the model's KC→MBON rule.

## Rungs 1 and 3

No measured adaptation time constant or ratio, and no measured membrane-noise s.d., were found for any
adult *Drosophila* central cell in this pass or in the 5 October search (`s12_central_fi.md`;
MBON-α3 f-I from Hafez 2023 is the one central f-I, F-FI-1).

## Survey record

- Agent 1 (Sonnet Explore, 04:35-04:38): Wilson-lab, Turner, Gouwens. URLs read: PMC4289142,
  PMC2429849, PMC2709801, PMC4674068. Failed: jneurosci.org, wilson.hms.harvard.edu PDFs,
  journals.physiology.org, elifesciences.org page (use api.elifesciences.org).
- Re-read by me: Nagel 2015 (NCBI efetch full text), Cuntz 2013 and Behnia 2014 (local copies).
