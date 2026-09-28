# Decisions and pre-registrations (construction programme, session 9 onward)

Append-only. Pre-registrations are written before anything judged is run (WORKFLOW §4.1), with results appended under the same heading, failures included. Sessions 1–8 are archived in `docs/archive/DECISIONS_s1-8.md`.

## Pivot to the construction programme (Ben, 27 September 2026)

After session 8, Ben set the direction: build a complete fly (every mechanism that plausibly matters, always on), represent every unknown as a biologically bounded parameter in one data model, validate the body with the brain dead, then construct the brain by search against physiology and judge on held-out data. Simulate more rather than less. The plan, principles, template inventory, data model, acceptance tests and task list are in `docs/CONSTRUCTION.md`.

Carried over: the working model m4 (reproducible), the legacy switches (to become views of the data model), the sealed and held-out register (`docs/HANDOFF.md`), and the findings distilled in `docs/LESSONS.md`. Superseded: the session 8 ranked plans (ring-first, scoped locomotion, calibration-engine-first). An ensemble-fitting strategy with hierarchical priors was agreed in session 4 (archived DECISIONS, "Strategy (agreed)") and never executed; this programme carries it out.

## Session 9 decisions (27 September 2026)

**Budget.** Ben set a ~2 h unattended session at the start (the prompt said 5 h), muscles as antagonist pairs on flybody with FlyMimic parameters where joints correspond, and PID 523 on backhouse left alone. backhouse was unreachable (ssh timeout) all session. No agents were used.

**Data model design (task 1).** Registry keys match table rows by `entity|property` patterns with `*` as the only wildcard (keys contain regex text). Numeric unknowns go in `parameters.csv`; data, assignments, policies, switches and registered absences in `structural_keys.csv`; mechanism switches in `mechanisms.yaml`. Every live key must have exactly one owning mechanism. A wired row's current m4 value must lie inside its bounds. A legacy body value outside its bounds on an unwired row is reported (`legacy_outside_bounds`), never absorbed by widening the bound. Discrete unknowns (spiking vs graded per class) use a Bernoulli prior. `sample(seed, stage)` is the numeric core of `sample_fly`; stage 0 reproduces the current model exactly (tested).

**New body mechanisms enter as registry switches, off in m4 and on in the construction template.** The switches are `joint:leg|passive_stiffness_source` (B3), `joint:wing|spring_reference` (B14) and `muscle:leg|model` (B4/B5). m4 and its regressions are unchanged (sugar->MN9 8.9 +- 5.9 Hz over 10 trials, identical to the reference; closed loop seeds 0-2 silent). Nothing was adopted into the working default this session.

**Figure 3C of the eLife paper is not used for spring rest angles.** Its medians are equilibria under tarsal weights, not zero-torque angles; using them would upgrade a label. The rest angle stays at the flybody neutral pose (guessed) until the weighted protocol is replicated in the model.

**Muscle passive force is off (fpmax 0).** The eLife springs are the joint's total passive torque, muscle included; adding FlyMimic's passive muscle force would count it twice.

**Coxa muscle directions are guessed.** FlyMimic coxa muscles act on all three coxa axes. The legacy MN map's coxa assignments disagree with axis geometry (F-MUSCLE-1). The FTi and CTr pairs use the calibrated flexor signs (derived).

### Pre-registration: template body stability (27 Sep 2026, before reading the runs)
Change: B3 measured leg stiffness + B14 folded wings + B4/B5 Hill pairs, all on, with the m4 brain (`closed_loop_check.py --set` the three switches).
Criteria: seeds 0-2 each run 1 s of closed loop with no NaN, no runaway, no MuJoCo divergence, and 0 non-tonic spikes in the silent window.
Adoption: none this session. A pass allows the template (sample_fly) to carry these switches on; a fail is recorded and the switches stay template-only options.
Result (Mac), **corrected**. First reading: "pass, brain 0.234/0.328/0.289 Hz". That run did **not** test Hill mode. `closed_loop_check.py` steps the loop itself and called `Neuromuscular.step` directly, bypassing the muscles. It therefore tested B3 + B14 only, and a re-run after the twitch-kinetics change gave identical numbers, which exposed the bypass. A zero-force control confirmed that the muscles do change a run (1,114 of 20,413 spikes differ in 300 ms). Fix: `Organism.motor_step()` is the single motor path. `run()` and the probes use it, and under Hill mode a direct `Neuromuscular.step` call raises (test). Re-run with all three switches through `motor_step`: **pass** on seeds 0/1/2: no divergence, NaN or runaway; 0 spikes in the silent window; final thorax 0.685/0.694/0.687 mm. **Reported move:** brain excluding ORNs 0.112/0.118/0.120 Hz, below the m4 range (0.22–0.38). Hill leg torques (≤ ~3 µN·mm) are far smaller than the legacy torques at the probe's 10 µN·mm per spike, so there is likely less proprioceptive drive (untested). The template may carry the three switches on; the working default is unchanged.
Re-run after the B5 constants were set from Azevedo 2020 (F-TWITCH-1): **pass** on seeds 0/1/2; brain excluding ORNs 0.115/0.130/0.122 Hz; 0 spikes in the silent window. The numbers differ from the previous run, as they should once the muscles are really in the loop.

### Pre-registration: full template body stability (27 Sep 2026, extension hour, before the runs)
Change: `joint:leg|passive_stiffness_source=2` (coupled projected springs) + `joint:leg|spring_reference=1` (fitted rest angles) + `joint:wing|spring_reference=1` + `muscle:leg|model=1`, m4 brain, `closed_loop_check.py` (steps through `motor_step`).
Criteria: seeds 0-2: no divergence/NaN/runaway; 0 spikes in the silent window. Adoption: template only.
Result (Mac): **fail** on 2 of 3 seeds. Seeds 0 and 2 keep firing after silencing (43.4 and 46.6 spikes/ms in the last 100 ms of the silent window); seed 1 passes (0; brain excluding ORNs 0.111 Hz). Diagnosis for seed 0: 934 active cells, led by Mi18 (66 cells), DNge019, DNg12_a/c/e and leg MNs. This is the latent Mi18/DNge019/DNg12 loop already recorded in LESSONS (F-STAB-1), now ignited by the new body's feedback. The switches stay template-only (as pre-registered). The failure implicates the uniform-strength brain (N5 per-class strength, N3 background drive, N4 adaptation), not the body. Recorded as F-STAB-2.

### Pre-registration: does adaptation (N4) stop the F-STAB-2 loop? (exploratory, 27 Sep 2026)
Change: the full template body (as above) plus `cell_type:all|adaptation_increment=1` mV (inside bounds 0-10; tau 200 ms default). Seeds 0-2.
Criterion: 0 spikes in the silent window on all 3 seeds. Exploratory: informs task 11, no adoption. Expectation: uniform adaptation previously cost function (F-SFA-1); it may still quench this loop.
Result: **pass** on stability: seeds 0/1/2 all silent (0 spikes/ms), brain excluding ORNs 0.094/0.107/0.096 Hz. **But** sugar->MN9_L (10 trials, m4 brain, same adaptation) falls to 0.7 +- 1.1 Hz (baseline 8.9 +- 5.9; > 5 required). Uniform adaptation again trades function for stability (F-SFA-1). Not adopted. Recorded as F-STAB-3: task 11 needs class-level mechanisms (per-class strength, background drive, adaptation) fitted within bounds, not a global knob.

## End-of-session judgement calls (Ben: "these are questions you can answer yourself")

1. **Task order: pull the cheapest brain mechanisms forward.** F-STAB-2/3 show the physical body destabilises the uniform brain, and the global fix (adaptation) costs the feeding pathway. Body behaviour cannot be judged through a brain known to be fragile. Session 10 therefore does task 11's N3 (per-class background drive) and N5 (per-class synaptic strength) as data-model rows with bounds, switched on at their priors and neutral-equivalence tested, before tasks 7-10. The body open items of tasks 4-6 come after them. This deviates from "work the task list in order", and the deviation is deliberate.
2. **Hip muscles act on all three coxa axes** (FlyMimic-style moment-arm vectors), rather than making two axes passive or changing the body model. This resolves F-MUSCLE-2 and F-COXA-1 without breaking the calibration. It is scheduled after item 1.
3. **Author contact is not a blocker.** Figure-digitised values stay labelled inferred. Requests for raw data (eLife per-trial angles; FlyMimic middle/hind MTUs) are listed in HANDOFF for Ben, since contacting people is outward-facing.
4. **Adoption rule for the template body.** The body switches (`model_data.TEMPLATE_SWITCHES`) become the working default when the full template is silent after input removal on 3/3 seeds *and* sugar->MN9_L stays > 5 Hz over 10 trials. m4 is then frozen as the regression reference.
5. **backhouse.** If it is unreachable, work Mac-only (≤ 3 heavy processes), as session 9 did.
6. **Sharper fall test** (the paper's fall onset vs standing height, with active force decaying at ~100 ms): after item 1, as part of task 7.
