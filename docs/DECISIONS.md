# Decision log

Short records of user decisions and major implementation choices. Newest last.

## 2026-09-14 Session 1 setup

- **Compute:** backhouse GPU (RTX 4070 Ti SUPER, WSL2 Ubuntu 24.04) may be used freely. Set up direct SSH into WSL for long jobs. Existing `/home/greff` content belongs to another project; do not modify.
- **Data access:** user has no neuPrint/Janelia or FlyWire/CAVE account yet and will register on request. Proceed with open releases first (Pugliese code/data, Azevedo Dryad, Zenodo, Caltech Data) and list exactly which registration unblocks which dataset.
- **Budget:** overnight unattended GPU jobs are acceptable. Raw data up to ~200 GB on the WSL disk. Mac keeps no raw data (56 GB free).
- **Repository:** private GitHub repo as canonical remote; checkouts on both the Mac and WSL. Raw data stays out of git.
- **Hardware correction:** README's "RTX 4070 Super" is actually a 4070 Ti SUPER with 16 GB (see ENVIRONMENT.md).
- **Router:** backhouse internet was paused at the eero router on first contact (apt/curl returned an eero "Device Paused" page). User is unpausing it; no tunneling workaround was used.
- **Reporting style:** user has little neuroscience background. Define fly-specific terms on first use; lead with milestone meaning.
- **Cadence:** run autonomously to a first measured result, then report with a run command and the next discriminating test.
- **Git identity:** Ben Greff <ben@thegreffs.com>; applied to new commits only; the first four commits keep the earlier author.
- **Reference code licensing:** Pugliese repo declares MIT in pyproject.toml but ships no LICENSE file; treat as MIT-intended, do not redistribute its bundled data until confirmed.

## 2026-09-14 Session 1, during work

- **CUDA skipped on the PC.** The workload parallelises across cores and the PC has 28.
  Measured CPU throughput there matches the Mac. Building CUDA offline would have added
  ~2.5 GB of transfers and version risk for no gain on this experiment class.
- **High synaptic-scale runs stopped early.** Scales 0.13, 0.2 and 0.3 were killed
  mid-sweep. The trend across 0.03, 0.045 and 0.09 already showed the transition to
  hyperactive and arrhythmic, those runs cost 500+ s per replicate and rising, and they
  were starving the phasic-versus-tonic experiment, which is the discriminating one.
  Rerun them if the transition point itself becomes the question.
- **Reimplemented the rate equation rather than patching the external repo.** Keeps the
  pinned upstream clone clean for provenance. The reimplementation was verified to
  reproduce the external solver path exactly at matched settings before use.
- **Glutamate sweep stopped after four of six points.** 0.03, 0.02, 0.01 and 0.0 complete
  at eight draws, which already show the monotonic collapse; the excitatory points run in a
  hyperactive regime and are very slow, and they were blocking the transmitter-uncertainty
  experiment, which is the more important one. The -0.03 row is a single draw.
- **Two sweeps at a time on the laptop, not three.** Three concurrent sweeps drove load to
  25 on ten cores and slowed everything proportionally.
- **Matched fixed-label control for the transmitter experiment dropped.** The resampled
  24 draws are compared against the existing 16-draw baseline (0.836 +/- 0.119) rather
  than a fresh 24-draw fixed-label run. The comparison is between a bimodal distribution
  and a tight one, so the extra draws would not have changed the conclusion, and the
  capacity went to the corrected-model window sweep, which was producing the more
  interesting result.
- **Proprioceptor-sign comparison and E/I balance sweep not run.** Both were queued and
  released for capacity. The sign question is already answered qualitatively by F10 and
  F12; the E/I question is largely superseded by the corrected-model sweep, which varies
  excitability rather than the excitation/inhibition ratio.
- **Bristle drive at amplitude 12.5 abandoned.** No replicate completed in 24 minutes. The
  mechanosensory bristle population carries a 12.9x gain multiplier under the model's size
  rule (F11), so driving it hard makes the network so active that the adaptive solver
  crawls. The A=5 bristle condition completed and already answers the question
  (rhythmicity 0.039). The intractability is itself a symptom of F11.

## 2026-09-14 Strategy questions, decided by me

Ben asked six framing questions before the session and then said to work from my own
judgement. These are the answers I acted on, recorded so they can be overridden.

1. **Evidence ranking: interventions first, then neural recordings, then behaviour.**
   Acted on throughout. The session spent its compute on controls and perturbations, not
   on making anything look good. The degree-matched shuffle, the drive-target control and
   the threshold-matched control are all intervention-style evidence.
2. **Specimen: the male nerve cord (MANC), by inheritance.** Chosen because the strongest
   executable precedent uses it and because its motor-neuron muscle annotations are the
   best available. Not a considered cross-specimen decision; revisit when the brain is
   needed, since the best brain data is female.
3. **Grain: rate-based, single-compartment, as published.** Kept deliberately. Nothing
   found tonight implicates the neuron model. The problems are sign, strength and
   excitability, which sit above the choice of neuron equation.
4. **Behavioural fitting: not reached, and not needed yet.** There is no behaviour to fit
   to until a leg moves. The physiology-only path has not been exhausted.
5. **End state: unchanged.** Not a live question until a leg works.
6. **Explainers: written.** The session report defines every fly-specific term on first
   use and leads with what each result means for the milestone.

The hypotheses I stated before starting, and what happened to them:

| Hypothesis | Outcome |
|---|---|
| Count-weighted synapses reproduce the rhythm under descending drive | **Confirmed** (F3), robust across 16 draws |
| That rhythm, through muscles with feedback, produces a step | **Untested.** F3 and F6 show the motor output is roughly 13x too weak and a third of it has no muscle to drive |
| Synapse count alone is insufficient; cell-type-specific gains are needed | **Supported indirectly.** F9 and F13 show the result turns on sign assignments, which is the same class of missing parameter |
| A physiology-only model predicts new interventions | **Untested** |
| Dopamine-gated plasticity produces odour learning | **Untested**, belongs to a later milestone |

The prediction I made about the workflow was that the biggest risks would fail early and
visibly on one leg. That is what happened, though not where expected: the failures were in
the model's parameter conventions rather than in the biomechanics.

## 2026-09-15 Session 2: the approach inverted

Ben rejected the session-1 strategy. His argument, which I accept: this is emergent
complexity, not incremental software. You either replicate the organism or you tack
fixes onto an incomplete brain, and an isolated sensorimotor loop is the latter. You
cannot isolate the part of a brain that walks forward, because walking is under
voluntary control and continuously corrected by systems that are not the walking
circuit. A fly is simpler, not different in kind.

This also explains session 1's central negative result better than session 1 did. The
fragment could not set its own operating point because descending drive, sensory
context and neuromodulator state were all absent. Finding F-FRAG has had its scope
narrowed accordingly, and the session-1 report's headline was over-claimed.

- **New first task: a whole-organism field inventory.** Enumerate every quantity the
  organism needs and mark its provenance, before simulating anything. Plan in
  `docs/PLAN.md`.
- **Grain:** per cell type for physiology, per neuron for structure. Roughly 9,000
  annotated types against 176,000 neurons. Chosen because measurements are published
  per type, so rows are fillable and rankable.
- **Boundary:** core loop plus neuromodulator systems, energy and hunger state, and
  circadian and arousal. All four, not a subset.
- **Counting:** one row per shared parameter group with an instance count, and the
  sharing itself recorded as a challengeable assumption. Per-instance counting was
  rejected as unrankable at millions of rows.
- **Run horizon:** hours. This makes every slow-state field load-bearing rather than
  optional, and most of those rows will be empty.
- **Primary graph moves to the whole-CNS male connectome** (F-DATA-2), carrying
  nerve-cord work across by `mancBodyid`.
- **Codebase cleaned.** About 40 fragment-specific files deleted: the runner, eleven
  sweep scripts, the figure and analysis scripts, the fragment result tables, the
  isolated-leg milestone plan and the session-1 report. All in git history at
  `1f7f5a4` or earlier. Kept: the provenance recorder and audit, data-validation
  tests, the queried motor-neuron extraction, the data manifest, and the findings
  restated at field level. Tracked files went from 61 to 21.
- **`runs/` retained on disk though untracked.** It holds the 53 provenance records
  that are the evidence for the surviving findings. Deleting the code that made them
  is fine; deleting the evidence is not.

## 2026-09-15 Session 2: the pack author's response, and three corrections to me

The agent that wrote the starter pack answered the questions in full. It accepted the
ordering error and supplied the precise version of it, plus corrections to three of my
own claims. The plan was rewritten around its schema.

- **F-RETRACTED-1. There was no frequency units bug.** I reported one, made it the
  opening finding and the opening of the session-1 report. The helper returns cycles
  per sample by design and the published notebooks convert correctly: I verified
  `mnFreq/overallParams.sim.dt` in Extended Data Figures 3 and 9 and Figure 2, and
  `freq = 1/period * fps` in the behavioural notebook, at commit `faee4b0`. I called
  their helper without reading their callers, got a nonsensical number, fixed my own
  code, and published my error as their defect. Withdrawn in full.
- **The traced-percentage framing is withdrawn.** "94% against 23%" is the fraction of
  `:Neuron` nodes whose `status` reads `Traced`, and `:Neuron` is itself a
  threshold-based inclusion. The dominant nerve-cord category is status *absent*,
  75,643 nodes, which is a different statement. Segment counts differ fourfold on
  imaged volume. Verified directly. The practical case for the whole-CNS graph stands
  on the brain, 1,454 proprioceptors and 673 of 708 cross-references.
- **Sensitivity is not correctness.** Flipping the glutamate population's sign and
  watching activity collapse shows leverage, not that either uniform assignment is
  right. Session 1's framing implied otherwise. Resolving it needs postsynaptic
  receptor evidence.
- **Electron microscopy is not categorically unable to resolve gap junctions.** The
  limitation is that these chemical-connectome releases provide no comparable
  electrical reconstruction. Unknown electrical coupling must not become measured
  absence.
- **Type count corrected to 11,751** distinct `type` labels in `male-cns:v1.0`, over
  164,506 typed neurons, verified by query. My "~9,000" was recalled, not checked.
  Any grouping below that number now needs a recorded rationale.
- **The Melis finding is a limitation for causal reuse, not a defect in its original
  science.** Future fluorescence can legitimately inform retrospective reconstruction.

Adopted into `docs/PLAN.md`:

- **Requirement schema of eight columns** with seven status values, replacing my five.
  Observations and model parameters are separate objects; partially constrained is not
  filled; shared inference dependencies are counted as rows, or propagating one assumed
  conductance to 5,000 neurons makes the inventory look complete while adding nothing.
- **Identifiability as the governing frame.** Some quantities are recoverable only in
  combination, so the inventory must record which rows are only jointly identifiable
  under a stated observation set.
- **Competing causal hypotheses before parameter changes**, each naming a distinguishing
  observation. Missing context masquerades as missing physiology, which is precisely
  session 1's error.
- **A minimum behaviour set of six capability rows** defining which fields are required,
  with courtship, reproduction and sleep behaviour marked later scope rather than
  omitted.
- **Separate replication from endorsement**, and **"not implemented" never means
  "biologically inactive."**
- **Five meaning-based sanity checks** now in `tests/test_source_data.py`, since
  ordinary tests encode the same assumptions as the implementation. Twelve tests pass.
- **Cloud budget reasoning corrected.** Hours of simulated time does not itself demand
  more resident memory than seconds; runtime, retained recordings and differentiating
  through long trajectories are the separate costs.
