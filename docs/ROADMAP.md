# Initial work and progressive milestones

This is a starting sequence, not a year-long promise. Walking precedes flight as the first whole-body outcome. Audit flight feasibility early so locomotion infrastructure does not prevent the later objective.

## First session: establish a runnable scientific foothold

1. Inspect the existing repository, instructions and environment. Determine GPU/VRAM, RAM, storage, OS/backend compatibility and current dependencies. Do not ask the user to repeat decisions already recorded in PROJECT.md.
2. Create a small dataset manifest and evidence ledger. Read the official MaleCNS/BANC access instructions and identify one primary candidate, with a short comparison of anatomical coverage, motor mappings, body compatibility and actual access. Do not download raw EM.
3. Choose one reproducible reference calculation: preferably a Pugliese VNC circuit or an accessible identified motor-unit recording. Verify availability and licensing; download only necessary data.
4. Produce a runnable import/analysis or small simulation with units, source version and a numerical/physiological readout. If the first candidate is blocked, use another documented route while recording the blocker.
5. Leave a concise run command, result and next action. Do not invent working commands in advance of an implementation.

The first artifact should be an executed, interpretable result—not a large directory hierarchy or a visual mockup.

## Milestone A: causal leg interface

- Reproduce a selected neural baseline and measured motor-unit responses.
- Map an identified leg motor unit to a compatible anatomical muscle model.
- Validate passive and activated mechanics under local measurements.
- Build an evidence-based proprioceptive transducer and close a local feedback loop.
- Test a held-out displacement/load or pathway intervention.

This can begin tethered, but tethering must be explicit. A one-leg result is an integration gate, not the full project scope.

In the same early period, inspect flybody/FlyGym compatibility and the Melis flight dataset/causality issue. Decide what can be reused, what needs refitting and what remains unidentified. Do not replace the primary walking milestone with a second equally large flight project.

## Milestone B: whole-body walking

- Extend anatomical and physiological mappings to the required legs and supporting body mechanics.
- Preserve ascending, descending and local feedback paths needed for the chosen behavior.
- Fit unresolved biological parameters against multiple walking conditions and neural data.
- Demonstrate support, initiation/stopping and stimulus-dependent turning without a substitute gait controller.
- Test new conditions and selected perturbations; report limitations quantitatively.

Do not claim “spontaneous behavior” when the trial is driven by an externally imposed command-neuron stimulus. Such trials remain useful reproductions of experiments.

## Milestone C: flight and transitions

- Establish causal steering-muscle/hinge dynamics and independent aerodynamic constraints.
- Implement power-muscle/thorax dynamics and suitable haltere/wing/visual feedback.
- Progress from isolated/tethered tests to already-airborne stabilization, then takeoff and landing.
- Measure response timing, stability and intervention effects. Clearly identify supplied power/rhythm/pose assumptions at each stage.
- Seek one compatible organism, rather than separately fitted walking and flight controllers selected externally.

## Milestone D: broader repertoire and lifetime learning

Add sensory modalities, grooming/feeding and other behaviors through their anatomical pathways as data support them. Introduce relevant internal states and plasticity mechanisms. Demonstrate adaptation, new learning, retention and state-dependent behavior in the frozen outer model. Expand duration and repertoire with validated mechanisms rather than requiring every slow biological process at the beginning.

Assess which Tier 1+2 capabilities are demonstrated, partial or unsupported. Reassess individual fidelity and synthetic-upload work when the reference organism is scientifically useful, not only after every aspirational behavior is complete.

## Milestone E: synthetic reconstruction experiments

Start on a validated learning circuit if the whole animal is still developing. Freeze reference individuals, hide information, reconstruct and test hidden behavior. Extend to the whole organism as appropriate. Compare algorithms and reference model families, and separate generic function from identity recovery.

## Agent work allocation

Useful independent assignments include: a source-to-parameter extraction with exact evidence; an anatomical identity/muscle mapping audit; a reproducible component fit; a numerical backend comparison; and independent held-out evaluation. Require concrete deliverables and citations. Coordinate schemas before parallel implementation and use one scheduler for expensive experiments.

Do not let many agents fill a large parameter table with unsupported defaults. Maintain a short ranked list of uncertainties by their effect on the current milestone. Spend work on the next test that distinguishes explanations.

## Continue, simplify or reconsider

Continue when a component predicts withheld observations and remains compatible with adjacent components. Increase fidelity when a specific discrepancy implicates a missing mechanism. Simplify only if the relevant physiological behavior is preserved. If several admissible completions disagree, preserve that uncertainty rather than choosing the best animation and calling it measured.

If an interface cannot be identified from existing evidence, document the alternatives and the strongest conditional result achievable. This is scientifically useful and can guide the next data search. It does not require abandoning the overall goal or inventing compensating mechanisms.

## Known unknowns to settle through inspection

- Actual system RAM, free disk, driver versions and practical overnight throughput.
- Which source files are readily accessible and have usable time-aligned measurements.
- Which primary specimen and body minimize unsupported identity/sex substitutions.
- Whether a sufficiently causal wing interface can be inferred from existing observations.
- The effective dimension of unresolved physiology after justified parameter sharing.
- How much biological detail is necessary for each assay; no preset GB or cell-model complexity guarantees fidelity.
