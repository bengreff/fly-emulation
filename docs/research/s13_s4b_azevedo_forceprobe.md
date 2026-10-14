Gathered by Sonnet subagent, 14 Oct 2026; not yet checked row by row

# Azevedo et al. 2020 eLife 9:e56754 — tibia flexor MN firing, force probe

Source: full JATS XML via Europe PMC (PMC7347388), cross-checked against PMC
summary and search snippets. Figure numbers below are the **published eLife
numbering** (A-F panels etc.), which differs from the task prompt's guess of
"2D/2H/2K, 4D/4E, 5" — see note under each item.

## 1. Firing rate during spontaneous movement bouts

- No per-class **peak** or **typical** Hz value during movement bouts is
  stated in the main text. The only quantitative rate numbers in the text are
  the **resting** rates (item 4) and two **unidentified** cells' resting rates
  (item on "other neurons" below).
- **Figure 5—figure supplement 1A** ("The effective spike rate of fast,
  intermediate and slow motor neurons, over the course of all trials with
  spontaneous leg movements. Instantaneous spike rates could be much
  higher.") plots this per class but the XML gives no axis-tick numbers and I
  did not open the image — figure-only, values **not found** (would need
  direct image read to report "read from figure (approximate)").
- "Other" (non-canonical, unidentified) flexor neurons in **Figure 4—figure
  supplement 1**: panel H neuron (R81A06-Gal4, described as an "other" cell,
  not confirmed as one of the three main classes) — "spontaneous spike rate
  of 12 Hz" (stated in text, Fig 4-fig.supp.1H). Panel K neuron (R81A04-Gal4)
  — "spontaneous spike rate of 28 Hz, input resistance 486 MΩ" (stated in
  text, Fig 4-fig.supp.1K). These are two extra cells recorded for
  robustness, not the headline fast/intermediate/slow exemplars — do not use
  as "the intermediate/fast rate."

## 2. Spikes per bout / burst duration

- Not found. The word "burst" does not appear anywhere in the paper (0
  hits). "Bout" appears only in unrelated contexts (walking bout initiation
  after optogenetic stim, not flexion-bout spike counts).

## 3. Firing rate vs. force relationship per class

- "A comparison of force production as a function of firing rate revealed
  that fast, intermediate and slow motor neurons occupy distinct force
  production regimes which span three orders of magnitude (Figure 4D)."
  (stated in text)
- "For fast and intermediate neurons, the force produced by two spikes was
  ~1.6X the force produced by a single spike (Figure 4E) and the
  force-per-spike curves saturated at ~10 spikes (Figure 4D)." (stated in
  text)
- "the effect of a spike in the fast and intermediate motor neurons reached
  half maximal force in ~8.5 ms (Figure 4H), whereas the effect of
  increasing the spike rate in slow motor neurons was gradual and did not
  reach its peak within 500 ms." (stated in text)
- Force-per-spike magnitudes (from the general WebSearch summary and
  consistent with Fig 4 text): fast ~10 µN/spike, intermediate ~1 µN/spike,
  slow <0.1 µN/spike — figure values, not independently re-verified against
  axis ticks in this pass; treat as "read from figure/summary (approximate)."
- Slow neuron: increasing its firing rate experimentally produced small
  (~1 µm) slow tibia movements (Figure 4C); decreasing it produced
  extension; blocking nicotinic input (1 µM MLA) "led to a decrease in the
  spontaneous firing rate and reduced the resting force on the probe by
  ~1.5 µN, or ~15% of the fly's weight (Figure 4C)." (stated in text)

## 4. Resting / spontaneous rate per class

Exact sentence (Results, discussing Figure 3C-D, n = fast 15, intermediate
11, slow 14 cells): "While the fast and intermediate neurons were silent at
rest, the slow neuron had a resting spike rate of approximately **30 Hz**
(Figure 3D)." — stated in text.
Resting potentials in the same sentence context: fast −68 mV, intermediate
−60 mV, slow −48 mV (Figure 3C).
Note: the task prompt's guess of "Fig 2D/2H/2K" is wrong for this — the
quantitative resting-rate panel is **Figure 3D** (Figure 2 in the published
paper only has panels A–F, anatomy and one example-trace panel D; no H/K).

## 5. Does the fast neuron fire during spontaneous movement, and at what rate?

- Yes, it fires during spontaneous (unloaded/force-probe) movement, but is
  silent at rest. "Plots of probe position and movement during example
  epochs (Figure 5D) illustrate that fast motor neurons typically spiked
  when the tibia was already flexed and moving." (stated in text, Fig 5D)
- "In comparison, spikes in fast motor neurons caused the probe to rapidly
  accelerate and approach maximum velocity (Figure 5D–E)." (stated in text)
- Quantitative n for the spike-triggered analysis (Figure 5E): fast — 5
  neurons, 4666 frames; intermediate — 4 neurons, 11,833 frames; slow — 9
  neurons, 65,473 frames (stated in text/legend). No absolute Hz value for
  fast-neuron firing during movement is given in the main text (only in the
  figure, Fig 5-fig.supp.1A, not extracted here).

## 6. Recruitment order sentence and figure

One sentence only, as requested (no numerical thresholds reported):
"In other words, activity in slow neurons preceded that of intermediate
neurons, and activity in intermediate neurons preceded that of fast
neurons." — based on paired whole-cell/EMG recordings in **Figure 5G**
(stated in text; model schematic in Figure 5F).

## Source data / Dryad check

Data availability statement (stated in text): "All data is publicly
available on Dryad https://doi.org/10.5061/dryad.76hdr7stb." Dataset:
Azevedo, Dickinson, Gurung, Venkatasubramanian, Mann, Tuthill 2020, "Data
for: A size principle for recruitment of Drosophila leg motor neurons,"
Dryad Digital Repository. Checked the Dryad file listing: it contains
`MN_anatomy_confocal_measurements.xlsx` (anatomy only, not firing rates),
`README.txt`, 8 supplementary movies, and ~48 dated raw-data zip files per
recording session (e.g. `171101_F1_C1.zip`, `180222_F1_C1.zip`) plus one
large `Dataset_3-...zip` (2.14 GB) — these look like raw/preprocessed
electrophysiology traces per cell/session, not an aggregated per-class rate
table. **No spreadsheet giving per-cell median/range firing rates was
found**; computing that would require pulling and reducing the raw
per-session zips, which I did not do. GitHub repos referenced are code only
(FlySound, LabelSelectedFramesForDLC, spikeDetection — acquisition/analysis
tools, not data).

## Caveats

- I read the full JATS XML text (figures/legends included) but did not
  open any figure images, so all "read from figure" items above are flagged
  as not independently verified against axis ticks — only the numbers
  stated in running text or figure legend prose are reported as "stated in
  text."
- Figure numbering in this note is the published eLife version; the earlier
  bioRxiv preprint (730218) used different numbering — don't mix the two.

## Figure read by the main session (14 Oct 2026, 00:07; image `elife-56754-fig5-figsupp1-v2` via iiif.elifesciences.org)

- **Fig 5—fig supp 1A** (average spike rate over all trials with spontaneous leg movements, one dot per class): fast ≈ 1 Hz, intermediate ≈ 10 Hz, slow ≈ 60 Hz. Read off the plot (axis 0-60, ticks every 20); reading error about ±3 Hz. Label: measured (read from figure, approximate). These are the S4b fit targets (DECISIONS 14 Oct 00:12).
- **Fig 5—fig supp 1D** (paired slow whole-cell and intermediate cell-attached recordings, femur-tibia angle). During rhythmic movement (about 6-7 cycles per second over the last ~1.8 s), the intermediate cell fires about 2-5 spikes per flexion cycle, phase-locked, and the slow cell is modulated between about −45 and −60 mV with 1-3 spikes per cycle. Before the movement, the intermediate cell is silent while the slow cell fires tonically. Qualitative only; not used as a target.
- **Fig 5—fig supp 1C:** of 3082 intermediate spikes, 2972 (96%) were preceded by a slow spike (cumulative, about 25 ms window). Fast spikes were preceded by intermediate spikes (histogram, peak P ≈ 0.12 per bin) and by slow spikes. This is the recruitment-order evidence: held out for S4b, not a target.
