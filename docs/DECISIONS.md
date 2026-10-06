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

## Session 10 decisions (27 September 2026)

**Budget and agents.** Ben: "Complete the brain-body model and start on GPU porting if you have time"; 5 h; 1-2 subagents. backhouse is reachable. Subagent 1 builds the batched GPU simulator (the first search item after construction), subagent 2 the task 5 remainder (coxa muscles with three-axis moment arms, fatigue). Both are general-purpose agents told not to launch agents; files are partitioned. This runs the body items in parallel with the brain items rather than after them (deviation from PLAN_NEXT's order, for throughput).

**N3/N5 at class grain.** Per circuit class (70 classes from `classes.csv`): release scale, input scale (N5, bounds 0.1-20, prior lognormal(1, 0.5)), tonic drive (N3, -10 to 20 mV, prior normal(0, 2)) and extra noise (N3, 0-3 mV/sqrt(ms), stage 2). All guessed bounds. Neutral values are bit-identical to m4 (test). The class tonic drive counts as network activity in the closed-loop criterion (only per-type tonic cells, e.g. the slow MNs, are excluded), so a search cannot pass the silence criterion by relabelling activity as tonic.

### Pre-registration: class-level search for a stable template brain (declared search, 27 Sep 2026 ~21:10, before reading the baseline diagnostics)
Change: per-class N5 release/input scale and N3 tonic drive (rows n5c_rel_*, n5c_inp_*, n3c_drive_*), inside their bounds.
Search space, fixed by rule now: the circuit classes that carry >= 5% of the silent-window spikes on any failing seed of the baseline template run (backhouse, seeds 0-2), plus the classes of the sugar->MN9 readout (MN9's circuit class) and stimulus (LB3b/c's). For each such class: release_scale, input_scale, tonic_drive. Bounds as in parameters.csv; no bound may be widened.
Objective (a MAP-style constrained search): minimise the departure from the prior, sum over parameters of ((log x)/0.5)^2 for scales and (x/2)^2 for drives, subject to (i) 0 non-tonic spikes in the last 100 ms of the silent window on template seeds 0, 1, 2 and (ii) sugar->MN9_L > 5 Hz (100 Hz stimulus, 10 trials, mean). Violations are penalised: 10 x log1p(silent spikes/ms) per seed + 10 x max(0, 5.5 - MN9 Hz).
Method: one-at-a-time screen (each parameter at 2 values toward quenching), then a small random/CMA search over the parameters the screen shows active, on backhouse CPU, <= 6 processes.
Fit set: template seeds 0-2 closed loop; sugar->MN9_L 10 trials (both seen).
Held out (unseen, run once on the best candidate): template seeds 3, 4, 5 closed loop (silent-window criterion); m4-body closed loop seeds 0-2 (regression criterion, 0 non-tonic spikes); bitter->MN9 at 100 Hz (must stay < 2 Hz: bitter alone should not drive MN9, Shiu 2024); water->MN9 > 0 Hz (drives MN9 in Shiu 2024).
Adoption: if the best candidate meets the fit constraints and all held-out criteria, its class values become the template's brain values (`model_data.TEMPLATE_BRAIN`), and, with the body switches, the template becomes the working default per the session 9 adoption rule; m4 is frozen as the regression reference. A bound hit is reported as a finding. Otherwise the values are recorded in `data/params/hypotheses_not_adopted.csv`.
Expectation: input scale of the DN or MN class below 1 quenches the loop; the risk is the MN9 pathway, which passes through DN-free gustatory/SEZ circuitry.
Search record (22:08, before the held-out run): screen (42 one-at-a-time candidates, seed 0 + sugar), phase 2a (13 single knobs, seeds 0-2), 2b (18 combinations, 6 random within +-2x), 2c (7 refinements); 80 candidates, ~290 runs on backhouse CPU. Single knobs are seed-fragile (e.g. optic_other release 2.0 silent on seeds 0-1 but 3.1 spikes/ms on seed 2); DN release 0.6 alone silences all three but drops sugar->MN9 to 4.1 Hz. Fit-set passes all combine reduced DN release (0.60-0.70) with a raised MN9-path lever (MN_other input 1.15-2.0, gustatory release 1.5-2.0, or MN_other release 1.5). **Best by the objective: class:DN|release_scale = 0.70, class:MN_other|input_scale = 1.30** (silent 0/0/0 spikes/ms, sugar->MN9_L 7.3 Hz, prior cost 0.78). Runner-up DN 0.65 + MN_other input 1.15 (8.2 Hz, 0.82). The best sits next to a failure (DN 0.72 fails on all seeds): a narrow margin. No bound was approached (all values inside [0.1, 20]).
Held-out result (22:14, run once, backhouse): template seeds 3/4/5 silent (0.0 spikes/ms; brain excl. ORNs 0.12/0.115/0.104 Hz; no MuJoCo warnings, no NaN); m4-body seeds 0-2 silent (0.0; 0.178/0.306/0.294 Hz); bitter->MN9_L 0.0 Hz at 100 Hz (pass, < 2); **water->MN9_L 0.0 Hz (fail; criterion > 0)**. By the pre-registered rule the candidate is **not adopted**; its values go to data/params/hypotheses_not_adopted.csv. The m4 water baseline is being run for context only (it cannot rescue the candidate: WORKFLOW 4.3).

### Pre-registration: repair 1 of the template-adoption test (post-hoc attempt 1 of 2; 22:23, before running the candidate)
Motivation (post-hoc): the failed held-out criterion (water->MN9 > 0) is failed by m4 itself (0 Hz at 100 and 200 Hz), so it could not detect a change caused by the candidate; the pre-registration did not check the baseline. The candidate is **unchanged** (class:DN|release_scale 0.70, class:MN_other|input_scale 1.30); nothing is refitted.
Fresh held-out evidence, criteria checked on m4 only (GPU, 10 trials): (a) template seeds 6, 7, 8: 0 non-tonic spikes in the silent window; (b) m4-body seeds 3, 4, 5: same; (c) bitter suppression: sugar_bitter_mn9 with bitter at 100 Hz gives MN9_L <= 50% of bitter at 0 Hz (m4: 9.5 -> 0.0 Hz); (d) sugar dose response: sugar->MN9_L at 200 Hz > 2 x at 100 Hz (m4: 96.0 vs 8.9). Seeds 6-8 and 3-5 have never been run with this candidate; (c) and (d) have not been run with it.
Adoption: all four pass -> the candidate's class values join the template (model_data.TEMPLATE_BRAIN) and the template becomes the working default per the s9 rule; m4 frozen as the regression reference. Any fail -> not adopted, and this target has one post-hoc attempt left.
Result (22:28): **pass on all four.** (a) template seeds 6/7/8 silent (brain excl. ORNs 0.131/0.135/0.120 Hz; these runs used the extended s10 template: coxa muscles, wing ranges, antenna, TTM, organs, pump gating); (b) m4-body seeds 3/4/5 silent (0.316/0.260/0.266 Hz); (c) sugar+bitter: 7.5 Hz with bitter 0 -> 0.0 Hz with bitter 100 (GPU, 10 trials); (d) sugar 100/200 Hz: 7.3/96.4 Hz. No MuJoCo warnings or NaN. **Adopted**: profile m5 = m4 + TEMPLATE_SWITCHES + class:DN|release_scale 0.70 + class:MN_other|input_scale 1.30 is the working model (profiles.WORKING_PROFILE); m4 is frozen as the regression reference (FLYEMU_PROFILE=m4). Caveats recorded with it: the stability margin is narrow (DN 0.72 fails on the fit seeds); the extended template without the class values fails seeds 0/1 (s10_tmpl2: 43.0/44.1/3.4 spikes/ms), so the class values carry the stability; water->MN9 is 0 Hz as in m4; the flight generator is not in the walking template.

### Pre-registration: does m5 stay stable with realistic sensory latency? (exploratory, 22:53, before the runs)
Motivation (post-hoc, from the GPU k=10 runs): holding the sensory drive for 1 ms breaks m5's return to silence on 5/12 seeds, although exact coupling is silent on 12/12. The model senses within 0.1 ms, far faster than real receptors. Change: new N15 latency per sensory class (transducers.Delay), set to the prior centres: photoreceptors 12 ms, olfactory 25, gustatory 20, mechano 1, proprioceptive 1, other 5. m5 otherwise. Seeds 0-5, exact coupling, closed_loop_check.
Criterion: 0 non-tonic spikes in the silent window on all 6 seeds. Exploratory: no adoption either way; a failure means the class-level search must include latency (a missing mechanism the adopted values may be compensating for).
Result (23:29): **pass**, seeds 0-5 all silent (0.0 spikes/ms; brain excl. ORNs 0.11-0.13 Hz), no warnings. Realistic pure latency does not break m5; the 1 ms sample-and-hold of the GPU k=10 scheme does (5/12 seeds). Latency stays 0 in m5 this session (not part of the adopted test); switching it on at the prior centres is a template change for session 11.

### Pre-registration: switch N15 latency on at its prior centres in the working model (m6) (23:32, before the runs)
Change: m6 = m5 + transducer latency at the prior centres (photoreceptors 12 ms, ocellar 12, olfactory 25, gustatory 20, mechano 1, proprioceptive 1, other 5). Principle 2: a built mechanism runs at its prior. Latency is the only session-10 neutral mechanism whose prior has a centre; the others have uniform priors and enter through sample_fly.
Criteria: closed loop silent after input removal on seeds 0-11 (0-5 already run in the exploratory check above: silent; 6-11 new); no MuJoCo warnings or NaN. Sugar->MN9 is unaffected by construction (the assay kicks GRNs directly, bypassing transducers), so it is not re-scored.
Adoption: all 12 silent -> m6 becomes the working profile (m5 kept); otherwise latency stays 0 and the result is recorded.
Result (23:35): **pass**: seeds 6-11 silent (brain excl. ORNs 0.116-0.143 Hz), with seeds 0-5 from the exploratory run: 12/12. **Adopted**: profile m6 = m5 + latency is the working model; m5 kept; m4 remains the regression reference.

## Direction after session 10 (Ben, 28 September 2026)

"The goal should NOT be tweaking things until we get a little bit of behaviour, the goal should always be filling in parts of the brain until we get 100% of the information filled in at the highest fidelity that could plausibly matter." Next: finish the entire brain-body build, get many copies running in parallel, then run experiments to fill in data. Ben also rejected the assumption that per-cell values need not be searched or filled: per-cell properties are to be inferred from development and biology. Consequences: the ledger's fill fraction (by source level and grain) is the headline progress metric; behaviour and stability are guardrails; the per-cell rules, transcriptome-derived per-synapse identities and the parallel evaluator come before any behaviour-directed search. PLAN_NEXT and the session 11 prompt were rewritten accordingly.

## Session 11 decisions (30 September 2026)

### Ledger v3 (17:05)
Progress is reported by source level (measured > derived > rule > prior > mixed > guessed > absent) per grain and per mechanism (scripts/blank_ledger.py; data/ontology/fly_information.yaml gains `mech` and `fidelity`). Because 96% of slots are per-synapse quantities (270 M synapse ultrastructure with no mechanism), the headline is reported three ways: all slots, slots outside the synapse grain, and each quantity weighted equally. Session 10's "26% filled" counted 90 M unused synapse locations; data the model uses is 1.9% of all slots.

### Pre-registration: switch the within-type per-cell size rule on in the working model (m7) (30 Sep 17:13, before any run)
Change: m7 = m6 + `cell_type:all|within_type_size_exponent` 1.0 (non-motor typed cells) + `cell_type:motor|within_type_size_exponent` 1.49 (motor neurons); `within_type_input_exponent` stays 0. Per-cell input gain x (type geometric-mean volume / cell volume)^alpha (src/flyemu/percell.py). Neutral at 0 (bit-identical, tests/test_percell.py).
Motivation (not post-hoc; Ben's direction and F-VAR-1): per-cell physiology follows morphology. alpha = 1 is the isopotential-membrane prediction (dV per charge ~ 1/area, area ~ volume) and matches Tobin, Wilson & Lee 2017 (compartmental models of EM PNs with measured Rm/Cm: larger arbors equalise unitary EPSPs; within-type log input vs log volume slope in male-cns 0.87, so total drive per cell stays ~constant). Motor alpha 1.49 = least-squares slope of log Rin (Azevedo 2020 Fig 3E, read s11: 150/300/700 MOhm fast/intermediate/slow, n = 15/11/14) on log median EM volume of the volume-ranked flexor classes (3.28e9/1.91e9/1.17e9 voxels).
Fit set: Azevedo Rin class means (motor alpha). General alpha is not fitted (prior centre).
Held out / guardrails (never tuned toward): closed loop silent after input removal on seeds 0-5 (m6 criterion; 0-2 are the standing guardrail, 3-5 margin); sugar->MN9_L at 100 Hz > 5 Hz over 10 trials (m6 7.3 Hz); bitter (100 Hz) suppresses sugar->MN9 as in m6; no MuJoCo warnings. The template dead fly is unaffected by construction (brain-only change) and is not re-run.
Adoption: all guardrails pass -> m7 becomes the working profile (m6 kept). If any fails, the rule stays at neutral in the working model, the failure is diagnosed (which classes move), and the per-cell rows stay "prior" in the ledger; at most two post-hoc repairs, each pre-registered.
Expectation: gains move by 0.78-1.30 for 80% of cells; motor pools spread most (factor 0.3-3). Stable; sugar->MN9 within the m6 trial spread.
Result (17:16): **fail, not adopted.** sugar->MN9_L 100 Hz: 0.5 ± 0.5 Hz over 10 trials (criterion > 5 Hz; m6 7.3). Sugar+bitter 0.0 Hz (suppression kept). Closed loop seeds 0-2 silent (brain excl. ORNs 0.136/0.138/0.133 Hz, no warnings); 3-5 still running. Diagnosis: the readout cell itself moved. MN9 has two cells; MN9_R is under-traced (633 input synapses vs 6,358 for MN9_L; volume 1.89e9 vs 4.35e9), so the within-type reference makes the complete MN9_L look large and lowers its gain to 0.54 (motor alpha 1.49). The two-hop sugar->X->MN9 interneurons moved little (weighted mean log factor +0.06). A within-type rule inherits reconstruction incompleteness: an under-traced homolog distorts the reference for its complete partners. (Across L/R pairs volume is the steadier size measure: median |log L/R| 0.059 vs 0.112 for input count.)

### Pre-registration: repair 1 of 2 for the per-cell size rule (post-hoc; 17:20, before running)
Change: completeness guard. Cells whose input synapse count is < 0.25x their type's median are treated as reconstruction-incomplete: they keep factor 1 and are excluded from the type reference; a type needs >= 2 unflagged cells for the rule to act. Flags 1,081 cells (0.6%; mostly sensory and optic lobe cells). Exponents unchanged (alpha 1.0, motor 1.49). Motivation post-hoc (the MN9 failure).
Dev (not evidence): sugar->MN9_L 100 Hz > 5 Hz (10 trials).
Held out (fresh): closed loop silent on seeds 6-8; sugar->MN9_L at 200 Hz > 48 Hz (half of m6's 96.4 Hz) over 10 trials; sugar+bitter suppression (< 1 Hz); plus seeds 3-5 from the running batch (they were launched before the failure was known).
Adoption: all pass -> m7 (with the guard) becomes the working profile. Otherwise the rule stays neutral in the working model; one more repair allowed.
Result (17:30): **dev fails, not adopted.** sugar->MN9_L 100 Hz 1.8 ± 1.5 Hz (10 trials; criterion > 5). Held out passed but is not evidence without the dev pass: sugar 200 Hz 84.4 ± 10.2 Hz (> 48), sugar+bitter 0.0 Hz; closed loop seeds 6-8 in the log. Unguarded m7 seeds 3-5 were silent (0.127/0.122/0.146 Hz). MN9_L's own factor is now 1, so the loss sits upstream. Mechanism note (before any further repair): the 100 Hz sugar response is at threshold (m4 8.9 ± 5.9, single trials below 5; 200 Hz gives ~90 Hz), and the m5 class values (DN release 0.70, MN_other input 1.30) were fitted with this criterion in the objective, on the old per-cell gains. A rule that redistributes gain within types around unchanged class values can move a threshold pathway without being wrong. Attribution diagnostics (general exponent only; motor exponent only; not candidates) follow. One post-hoc repair remains for this target.
Attribution (17:34, diagnostics, not candidates; 10 trials each, 100 Hz): general exponent 1.0 alone -> sugar->MN9_L 1.8 ± 1.5 Hz; motor exponent 1.49 alone -> 6.9 ± 2.3 Hz (m6 7.3). The loss comes entirely from the within-type rule on central neurons. Repair-1 closed loop seeds 6-8 silent (0.163/0.139/0.127 Hz). Diagnosis: the central rule is stable (seeds 0-8 silent under both variants) but moves a threshold pathway whose operating point was fitted by the s10 class search on the old per-cell gains; the principled fix is a joint re-search of the class values with the rule on (a declared search, GPU-scale), not a smaller exponent.

### Pre-registration: repair 2 of 2 for the per-cell size rule: motor pools only (post-hoc; 17:37, before running)
Change: m7 = m6 + `cell_type:motor|within_type_size_exponent` 1.49 (the Azevedo-fitted size principle in motor pools), completeness guard on; `cell_type:all|within_type_size_exponent` stays 0 (central rule kept as an option pending a joint class re-search). Motivation: post-hoc (attribution above).
Dev (seen): sugar->MN9_L 100 Hz 6.9 ± 2.3 Hz (the attribution run).
Held out (fresh for this candidate; base-model values known): closed loop silent on seeds 9-11 (m6 silent on 0-11); bitter->MN9_L 100 Hz < 1 Hz (m5/m6 0 Hz, s10); sugar+bitter 100 Hz < 1 Hz.
Adoption: all pass -> m7 = motor rule becomes the working profile. Otherwise nothing is adopted and this target's repair budget is spent.
Result (17:47): **pass, adopted; m7 is the working profile** (m6 kept). Closed loop seeds 9-11 silent (0 spikes in the last 100 ms; brain excl. ORNs 0.113/0.115/0.126 Hz; no MuJoCo warnings). bitter->MN9_L 100 Hz 0.0 ± 0.0 Hz; sugar+bitter 100 Hz 0.0 ± 0.0 Hz (10 trials each). The repair budget for this target is spent; the central rule stays neutral until a joint class re-search.

### Pre-registration: VNC rhythm probe, graded VNC local interneurons (17:45, before running)
Question: does the VNC make a rhythm from DNg100 drive when its local interneurons transmit graded (non-spiking) rather than spiking? Session 4 found no front-leg rhythm with all cells spiking (rhythmicity 0.21-0.29 vs a Poisson floor 0.21); Pugliese et al. 2025 get 7-15 Hz rhythms from the same connectome with a rate model, and many VNC premotor interneurons are non-spiking (Burrows; Agrawal 2020 / Azevedo 2024 for fly leg premotor cells, lead). A mechanism probe, not an adoption test.
Arms: profile m6, assay dng100_legs (stim DNg100, readout all front-leg motor neurons), rates 0, 100, 200 Hz, 5 trials of 1 s, no shuffles. (a) as is (the 2,778 unknown-mode vnc_local types spiking); (b) `mode:n1_p_graded_vnc_local|graded` = 1.
Measure: per trial, median over active MNs of rhythm_excess (autocorrelation rhythm score minus ISI-shuffled surrogates) and of rhythm frequency; readout rate.
Pre-declared reading: "rhythm present" in an arm if at 100 or 200 Hz the trial-mean rhythm_excess_median > 0.10, the median rhythm frequency is within 4-25 Hz, the readout rate is > 1 Hz, and the 0 Hz condition does not show the same (excess < 0.05). Both arms without rhythm -> graded transmission alone does not produce the rhythm; next suspects are the graded rate map (graded_rmax 100 Hz, guessed) and the missing sensory feedback (open loop). (b) with rhythm and (a) without -> graded VNC mode becomes the candidate for a pre-registered working-profile change (needs the m6 guardrails: sugar->MN9, bitter suppression, closed-loop silence).
Result (17:52): **no rhythm in either arm.** (a) spiking: readout 3.73 / 4.00 / 4.35 Hz at 0 / 100 / 200 Hz; rhythm_excess_median 0.000-0.003 per trial; the raw rhythmicity (0.70-1.03 at ~23-25 Hz) is regular tonic firing of ~60 front-leg MNs that fire without input (the surrogate removes it). (b) graded vnc_local: DNg100 recruits more of the VNC (active cells 60 -> 572 / 646) and roughly doubles front-leg MN output (6.15 ± 1.25 / 6.75 ± 1.33 Hz), but rhythm_excess_median stays 0.000-0.041 per trial (mean 0.009 / 0.015; criterion > 0.10). Graded transmission of VNC local cells alone does not produce the walking rhythm in this model. Next suspects, in order: VNC glutamate signs (glutamate is inhibitory in every VNC target by default; Allen 2020 VNC atlas being extracted), missing cellular rhythm mechanisms (spike-frequency adaptation / post-inhibitory rebound, all at neutral), and missing proprioceptive feedback (open loop). The 0 Hz condition is identical across trials: m6 has no background noise into front-leg MNs.

### Pre-registration: rhythm probe arm (c), graded VNC + spike-frequency adaptation (17:53, before running)
Same assay, reading and criterion as the rhythm probe above. Arm (c) = arm (b) + `cell_type:all|adaptation_increment` 3 mV and `cell_type:all|adaptation_tau` 150 ms (N4; bounds 0-10 mV and 20-2000 ms, guessed; a mid-range value, not tuned). Rationale: half-centre rhythms need a cellular process that ends each burst (adaptation or rebound); the model has none switched on. A probe only; adopting adaptation would need the m7 guardrails.
Result (17:57): **no rhythm.** Driven: readout 3.2 / 3.1 Hz at 100 / 200 Hz; rhythm_excess_median per trial 0.003-0.053 (100 Hz) and 0.030-0.059 (200 Hz), criterion > 0.10. The undriven condition shows more (0.178 at ~10 Hz: adaptation makes the ~60 tonically firing MNs fire in slow waves), so the 0 Hz exclusion also fails. Adaptation plus graded VNC cells does not give a DNg100-driven rhythm.

### Pre-registration: walking failure localisation, closed loop (18:02, before running)
Question: which layer stops DNg100 from producing stepping: neural recruitment, body/muscle transfer, or sensory feedback? Diagnostic, no parameter changes (design adapted from an outside review that was not kept; reduced to Mac scale). Profile m7 (working), `scripts/probes/command_walk.py` (1.4 s; stimulation 300-1300 ms; default force_per_spike 10 as in closed_loop_check).
Arms: (1) DNg100 0 vs 100 Hz x body afferents on vs off (`--no-body-afferents`), seeds 0-2: 12 trials. (2) Synthetic tripod MN bursts (`--replay-hz 10 --replay-rate 150`, DNg100 off), seeds 0-2: 3 trials.
Readouts: mean leg MN rate in the stimulation window; per leg the tarsal-tip fore-aft oscillation (dominant 3-25 Hz frequency, band power share, peak-to-peak amplitude); thorax displacement; MuJoCo warnings.
Pre-declared reading. "Leg oscillation" = band share > 0.5 and amplitude > 0.1 mm in >= 4 of 6 legs; "progress" = |thorax dx| > 0.5 mm. Neural recruitment is "weak" if DNg100 raises the mean leg MN rate by < 5 Hz over the 0 Hz arm (seed-matched mean). Then: weak recruitment and replay oscillates -> the failure is neural (transmission / operating point); replay does not oscillate -> motor/body failure (whatever the brain does); DNg100 oscillates only with afferents off -> the sensory loop suppresses it; everything oscillates but no progress -> coordination/contact mechanics.
Result (18:13): **two layers fail.** Recruitment weak: DNg100 at 92 Hz (achieved) raises the mean leg MN rate from 3.18-3.23 to 3.89-4.05 Hz with afferents on, and from 2.13-2.14 to 2.56-2.60 Hz with afferents off (+0.7 Hz; criterion 5 Hz). Replay does not oscillate: synthetic 10 Hz tripod bursts (leg MNs 49-50 Hz mean; 426 mapped leg MNs) move the tarsal tips 0.2-0.9 mm peak-to-peak but with band share 0.05-0.48 (no leg > 0.5; dominant at the 3 Hz band edge, i.e. slow drift), and the thorax slides backwards 0.40-0.85 mm. No arm oscillates in >= 1 leg by the criterion except single legs by chance (band share 0.53-0.56 at < 0.1 mm). Removing body afferents lowers leg MN rates by a third and changes nothing else. MuJoCo warnings 0 in all 15 trials. Reading: the failure is both neural (DNg100 barely reaches the MNs) and motor/body (a 10 Hz alternating MN pattern does not give 10 Hz leg movement), so fixing the brain alone would not produce stepping. Diagnostic next (not a candidate): body response to replay at 5 and 20 Hz.
Diagnostics (18:19-18:43; tethered, synthetic replay, seed 0; not candidates): joint-angle power at the drive frequency, median over 100 moving leg DOFs: 2 Hz 0.823 (91% of joints > 0.3), 10 Hz 0.057 (0%). Fast and intermediate units only at 10 Hz: 0.056 (slow units are not the filter). Muscle torque at 10 Hz: median share 0.539 over 55 actuators (71% > 0.3). So the muscles deliver the 10 Hz pattern and the leg joints filter it. Leg hinge DOFs carry damping ~1 uN*mm*s/rad (flybody/NMF default, guessed; row b3_d_leg) against measured springs of median 0.86 uN*mm/rad (Wang 2025): c/k ~1 s, a corner near 0.16 Hz (derived), where FlyMimic uses c/k = 0.05 s.

### Pre-registration: leg joint damping at the FlyMimic time constant (m8 candidate) (18:44, before running)
Change: new key `joint:leg|damping` (0 = unchanged defaults; neutral) set to 0.043 uN*mm*s/rad on every leg hinge DOF except the inter-tarsal chain = c/k 0.05 s (FlyMimic, Ozdil et al.) x the median measured leg stiffness 0.86 (Wang 2025). Inferred; inside the b3_d_leg bounds (1e-4 to 10). Motivation: the diagnostics above (post-hoc to the localisation run, recorded before this run).
Mechanism check (dev): tethered 10 Hz replay, seed 0: median joint share at 10 Hz > 0.3 (from 0.057).
Held out / guardrails: dead-fly test (`scripts/dead_fly.py --template`, deterministic; corrected 18:45 before any guardrail run, the first draft named the wrong script) with the same verdicts as without the damping; closed loop silent after input removal on seeds 0-2 (m7 criterion; brain is unchanged, the body feeds back); standing replay 10 Hz (seeds 0-2) gives >= 4 legs with tarsal band share > 0.5 (walking-relevant, reported, not an adoption criterion).
Adoption: mechanism check and all guardrails pass -> m8 = m7 + leg damping becomes the working profile. Otherwise not adopted; at most two pre-registered repairs.
Result (18:47): **mechanism check fails; not adopted, guardrails not run.** Tethered 10 Hz replay with leg damping 0.043: median joint share at 10 Hz 0.094 (8% of 102 joints > 0.3; criterion > 0.3; m7 0.057); torque share unchanged (0.538); joint amplitude 0.164 rad; no warnings. Passive damping is at most a minor part of the filter. Next suspects (not yet tested): joints held at their range limits by the mean (DC) torque, so only slow reversals move them; Hill force-velocity and passive muscle force acting as a velocity-dependent brake; co-contraction of antagonists within a leg in this synthetic pattern (all +1 MNs of a leg fire together). The key stays at neutral (0 = unchanged). One-trial diagnostics that separate these: fraction of time each leg joint sits within 0.05 rad of a range limit, and replay with Hill force-velocity off.

### Pre-registration: body low-pass diagnostics, joint limits and force-velocity (18:49, before running; diagnostics, not candidates)
Tethered 10 Hz tripod replay, seed 0, m7, as the 18:19 runs. (i) Baseline with a new readout: fraction of samples each limited leg hinge joint spends within 5% of its range from a limit. (ii) Same with the Hill force-velocity factor forced to 1 (`--no-fv`). Reading: if mean occupancy > 0.3 or more than a quarter of joints sit near a limit over half the time, joint limits are the leading suspect; if (ii) raises the median joint share at 10 Hz above 0.3 (baseline 0.057; also read against the new 3-50 Hz band share, added 18:50 before any run completed, because the whole-spectrum share includes the slow postural shift at replay onset), muscle force-velocity acts as the low-pass (the vmax values are then the thing to check against data). Neither reading adopts anything.
Note (18:56): the full suite failed on the m4 view of the table because the damping key's neutral 0 did not equal the row's current value (1). The key now means the damping of the leg DOFs whose flybody default is 1 (femur-tibia 0.4 scales with it), neutral 1. The 18:47 run set 0.043 on every leg DOF including femur-tibia (0.043 rather than 0.017); the conclusion does not depend on that.
Result (18:54): **neither joint limits nor force-velocity is the low-pass.** Baseline: mean fraction of time near a limit 0.079 (2 of 42 joints over half the time); 3-50 Hz band share at 10 Hz 0.119. Force-velocity off: 0.101. Remaining explanation (derived): the flybody default damping 1 on every leg DOF; a 3.3 µN·mm torque swing at 10 Hz through c = 1 predicts 3.3 / (2π·10·1) ≈ 0.05 rad, as observed (0.06 rad in 3-50 Hz). The 18:47 damping run lowered c to 0.043 but kept the force-velocity damping (derived 0.004-0.78 µN·mm·s/rad per muscle at full activation, median 0.09), and the share metric there was confounded by the onset drift.

### Pre-registration: damping 0.043 with and without force-velocity, amplitude readout (18:55, diagnostics, not candidates)
Tethered 10 Hz replay, seed 0: (i) `joint:leg|damping` 0.043; (ii) same plus `--no-fv`. New readout: peak-to-peak joint amplitude at the drive frequency (median and 90th percentile over moving leg DOFs; baseline recomputed in a third run (iii) at defaults). Reading: if (i) or (ii) raises the median 10 Hz amplitude at least 3x over (iii), damping is the low-pass and a biologically bounded damping becomes the m8 question (with FlyMimic's c/k 0.05 s as the only reference).
Result (18:59): **under the 3x criterion in both arms.** Median peak-to-peak joint amplitude at 10 Hz: defaults 0.031 rad (90th pct 0.167), damping 0.043 0.052 (1.7x), damping 0.043 + force-velocity off 0.079 (2.6x; 90th pct 0.236). Torque share at 10 Hz falls from 0.54 to 0.34 when damping is lowered. Real femur-tibia swings in walking are around 1 rad, so something else holds the legs. The tether lifts the thorax only 1 mm; the tarsi may still touch the floor.

### Pre-registration: tether height (18:59, diagnostic)
Same as (ii) above (damping 0.043, force-velocity off) with the thorax held 5 mm up, plus the mean contact count. Reading: contacts near 0 and median 10 Hz amplitude > 3x the 1 mm run (0.079) means ground contact was clamping the legs; otherwise the limit is in the muscle-joint model (stiffness, moment arms, or activation depth).
Result (19:02): **ground contact is not the clamp.** Thorax 5 mm up: median 10 Hz amplitude 0.075 rad (1 mm: 0.079); about 10 contacts remain, none leg-ground (at rest in the lifted pose: body-abdomen-wing pairs only).

### Diagnostic: body-only joint transfer (19:05; `scripts/probes/joint_impedance.py`, no brain, no muscles)
Sinusoidal torque 1.5 µN·mm on one leg actuator, thorax held 5 mm up, swing peak-to-peak at the drive frequency. Femur-tibia at defaults (damping 0.4): 0.84 rad at 2 Hz, 0.13 rad at 10 Hz; a pure damper predicts 0.12 rad at 10 Hz (derived). Running three joints at defaults and at damping 0.043 next: if the bare body then swings near 1 rad at 10 Hz while the muscle-driven replay gives 0.08, the clamp is in the muscle path (activation depth or muscle stiffness), not in the body.
Result (19:10): **the bare body follows 10 Hz once damping is low.** Torque 1.5 µN·mm, 10 Hz swing peak-to-peak at defaults / at damping 0.043: trochanter-femur 0.050 / 0.39 rad, femur-tibia 0.13 / 1.80 rad, coxa pitch 0.049 / 0.62 rad (no warnings). The muscle-driven replay at the same damping gives 0.08 rad, so the remaining clamp is in the muscle path. Next: per-joint 10 Hz torque and impedance (torque / swing) in the replay, compared with the bare-body impedance (about 1.7-7.7 µN·mm/rad at damping 0.043, derived from the rows above).
Result (19:12): **the muscles add no stiffness; the 10 Hz torque is too small.** Replay (damping 0.043, force-velocity off, 5 mm tether), per leg actuator at 10 Hz: torque 0.20 µN·mm peak-to-peak (median of 33), swing 0.14 rad, impedance 2.5 µN·mm/rad (bare body 1.7-7.7). About 2.5 µN·mm at 10 Hz is needed for a 1 rad swing; a pooled muscle gives up to ~4 µN·mm at full activation (F0 x r, derived). Activation is not modulated at 10 Hz.

### Pre-registration: activation depth at 10 Hz (19:12, diagnostics, not candidates)
As the 19:12 run, plus one change each: (i) fast/intermediate twitch decay 15 ms (table lower bound; current 40 ms, inferred), (ii) `motor_unit:leg|fused_rate` 300 Hz (table upper bound; current 100, guessed; at 150 Hz replay the on-phase saturates). Reading: an arm that raises the median per-actuator 10 Hz torque at least 3x (to ≥ 0.6 µN·mm) identifies the term that filters the drive. Neither is adopted from this; a bounded change would go to its own pre-registration with guardrails.
Result (19:15): **neither reaches 3x.** Median per-actuator 10 Hz torque: twitch decay 15 ms 0.41 µN·mm (2.0x; median swing at the joint 0.096 rad, 90th pct 0.37); fused rate 300 Hz 0.23 (1.15x). Next: per-muscle activation swing and antagonist phase at 10 Hz in the same replay, to test whether antagonist pairs are driven in phase (the replay assigns MNs to phases by their calibrated drive sign).
Result (19:22): **the stepping joint follows; the distal joints do not.** Per complete antagonist pair at 10 Hz (14 pairs, all in antiphase, median phase difference 166°; force-length gain median 0.98; 10 of 48 non-coxa muscles have no motor neurons): coxa-trochanter pitch (lf, lh, rf, rh) torque 2.2-2.8 µN·mm, swing 0.58-0.91 rad, stepping scale; femur-tibia 0.20-0.39 µN·mm, 0.15-0.22 rad; tibia-tarsus 0.15-0.16, 0.05 rad. Mid-leg coxa-trochanter pitch receives almost no torque (0.002-0.13) yet swings 0.69-0.79 rad, carried by coupling. Femur-tibia capacity is large (F0 x r 10.1 and 1.0 µN·mm), so its activation is not modulated. The median over all DOFs hid this.
Next (19:22, diagnostics): per-pair activation swing and mean in the same tethered replay; and the standing fly with damping 0.043 and force-velocity on (the physical configuration), reading forward thorax displacement over 1 s of 10 Hz tripod replay (earlier standing replays at default damping slid backwards 0.4-0.85 mm).
Result (19:26): **the strong femur-tibia muscle works far from its optimum.** Per complete pair, force-length gain (mean over the replay, +1 / -1 direction): femur-tibia 0.10-0.30 / 0.99 with the joint 0.79-1.01 rad from the reference angle; mid-leg coxa-trochanter 0.14-0.21 on both sides, 1.48-1.54 rad off; front/hind coxa-trochanter 0.71-0.81. Activations swing 0.33-0.45 peak-to-peak in antiphase on every pair. Cause: `leg_muscles.csv` (s9) places each muscle's optimum (normalised length 1) at the flybody zero pose, but FlyMimic's optima sit at its own posture and its joints use different zeros and ranges (Trochanter_pitch -3.24 to -1.22 rad, flybody -1.75 to 1.75). A join error between two skeletons' coordinates, not a parameter value.

### Construction: muscle optimum joined by anatomy (19:28)
`scripts/build_muscle_optimum_join.py` -> `data/derived/leg_muscle_optimum_join.csv`: each FlyMimic muscle's optimum (keyframe angle + (1 - L_key) L0 / arm) becomes an interior segment angle (femur vs tibia axis; coxa vs femur axis), pooled F0-weighted per flybody DOF and direction, and is found in flybody per leg on the monotonic branch containing the zero pose (match error ≤ 0.1°). Front legs derived; mid/hind copy the front-leg interior angle (guessed). Optima: femur-tibia +1 (tibia extensor) 0.49-0.60 rad, -1 0.02-0.13; coxa-trochanter 0.84-1.38. New switch `muscle:leg|optimum_join` (0 = s9 zero pose, neutral; test `tests/test_muscle_optimum_join.py`).

### Pre-registration: m8 candidate = m7 + muscle:leg|optimum_join 1 (19:29, before running)
Interpretation: a corrected join of measured-model (FlyMimic) muscle geometry, no fitted value. Mechanism check (dev, tethered 5 mm, 10 Hz tripod replay, seed 0, default damping and force-velocity on, i.e. the physical configuration): median femur-tibia 10 Hz torque over the 6 legs at least 2x the m7 value in the same configuration (run alongside), and the femur-tibia +1 force-length gain median ≥ 0.5. Guardrails: closed loop silent after input removal on seeds 0-2 (m7 criterion) and no thorax fall (thorax height at the end within 0.3 mm of m7's, reported by the probe). The dead-fly test is unaffected by construction (zero activation gives zero active force whatever the optimum) and is not re-run. Reported, not criteria: standing 10 Hz replay thorax displacement and video.
Adoption: mechanism check and guardrails pass -> m8 = m7 + optimum join becomes the working profile.
Note (19:31): timestamps in this session's entries from 18:49 on were first written ahead of the clock (up to 21:15) and corrected at 19:31 from the run files' modification times; the order of pre-registration before result is unchanged.

### Result: m8 mechanism check FAILS; m8 not adopted (19:32)
Runs `runs/s11/walk/m{7,8}_tet_rep10_s0.json` (tethered 5 mm, 10 Hz replay, seed 0, default damping, FV on). Median femur-tibia 10 Hz torque p2p over 6 legs: m7 1.05, m8 1.17 µN·mm (1.12x; criterion 2x) - fail. Femur-tibia +1 (extensor) FL gain median: m7 0.30, m8 0.44 (criterion 0.5) - fail. Femur-tibia swing p2p rose (front 0.06-0.09 -> 0.10-0.13 rad) but the pre-registered bar was not met. Guardrails not run (moot).
What the readout shows (measured): both femur-tibia muscles sit at ~0.6-0.7 mean activation (tonic co-contraction under the replay), the flexor at FL ~0.98, and the joint is flexed 0.5-0.97 rad past the extensor optimum. So the posture itself, set by flexor dominance under co-activation, keeps the extensor short-of-optimum; the join moved the extensor optimum by ~0.1-0.15 rad, far less than that offset.
Kept: the join table and switch (neutral 0) as a construction artefact for later re-test. Next discriminating question: is the tonic co-activation (mean act 0.65 on both sides) biological, or an artefact of motor-unit recruitment (activation = r/fused clipped at 1) under the replay drive? A replay with lower tonic drive should show whether the extensor recovers FL and the 10 Hz torque grows.

### Diagnostic: replay rate 40 Hz (post-hoc, not a candidate) and a corrected reading (19:42)
Same as the m7/m8 tethered runs with `--replay-rate 40`: femur-tibia mean activation falls to ~0.16 on both sides, but the posture barely moves (m7 joint 0.50-0.96 rad past q_ref, as at 150 Hz; m8 0.02-0.65). Median 10 Hz femur-tibia torque p2p m7 0.66, m8 0.85; extensor FL gain m8 0.47-0.75. So co-activation level does not set the posture.
Correction to the 19:32 reading: it is the +1 muscle (FlyMimic `LFTibia_extensor`, F0 304 µN, arm 0.033 mm, L0 0.087 mm) that wins, not the flexor (`LFTibia_flex`, F0 68 µN, arm 0.015 mm, L0 0.309 mm). Capacity F0·r is 10.1 vs 1.04 µN·mm (derived, from leg_muscles.csv). Under equal activation the joint runs toward the extensor's short end until its FL gain falls to ~0.1, where it balances the flexor, whose length hardly changes with angle (r/L0 0.05 vs 0.38 per rad). The posture is an equilibrium set by the capacity ratio and FL slopes, so moving the optimum cannot fix it. Open question (inferred, to check against anatomy): Drosophila tibia flexor vs extensor size and motor pool (Azevedo et al. 2020 report many more flexor than extensor MNs), against FlyMimic's 4.5:1 extensor:flexor F0.

### Pre-registration: m8 candidate = m7 + muscle:leg|ft_flexor_scale 40 (19:48, before running)
Evidence (measured force, derived torque): Azevedo et al. 2020 front-leg tibia flexor pushes a probe with close to 100 µN at a 417 ± 7 µm lever (force underestimated per the authors), i.e. ≥ 42 µN·mm; the model's flexor (FlyMimic F0 68.1 µN x r 0.01524 mm) gives at most 1.04 µN·mm. Value 40 = the measurement's lower bound (derived); bounds [1, 150] (row b4_ft_flexor_scale). Applied to every leg (mid/hind copy, guessed). The extensor keeps FlyMimic F0 (fitted, no force measurement). Optimum join stays off (0), so this is one change.
Mechanism check (tethered 5 mm, 10 Hz replay at 150 Hz MN rate, seed 0, default damping, FV on; m7 baseline `m7_tet_rep10_s0`): median femur-tibia 10 Hz swing p2p over the 6 legs ≥ 3x m7 (m7 0.033 rad, so ≥ 0.10 rad), and median femur-tibia extensor FL gain ≥ 0.5. Guardrails: closed loop silent after input removal (0 non-tonic spikes, last 100 ms) on seeds 0-2; no MuJoCo warnings. The dead fly is unaffected by construction (zero activation gives zero active force). Reported only: femur-tibia posture (q - q_ref), limit occupancy, a standing 10 Hz replay displacement.
Adoption: all pass -> m8 = m7 + ft_flexor_scale 40 becomes the working profile.
Result (19:56): **m8 (flexor scale 40) fails the mechanism check; not adopted.** `runs/s11/walk/m8f_tet_rep10_s0.json`: median femur-tibia 10 Hz swing p2p 0.098 rad (bar 0.10; per leg 0.006-0.19); extensor FL gain 0.08-0.20 (bar 0.5). Femur-tibia 10 Hz torque p2p rose from ~1 to 12-16 µN·mm, but the joint now runs 1.0-1.3 rad toward flexion and pins (limit occupancy: 8 of 42 leg joints near a limit > half the time; m7 2). No warnings.
Reading: under the synthetic replay every mapped MN of a muscle fires at the same rate, so antagonists of unequal capacity are equally activated and the joint runs to the stronger muscle's end, whichever that is (FlyMimic extensor in m7, measured-scale flexor here). The symmetric replay cannot test asymmetric muscles; a real pool is graded (slow flexor units < 0.1 µN per spike vs fast ~10 µN; Azevedo 2020) and posture is under feedback. The measured flexor capacity stays the best-evidenced value; what is missing is drive that is graded by recruitment order, which the brain's MNs should supply (the size principle is already in m7).

### Pre-registration: size-ordered replay (diagnostic, not a candidate) (19:56, before running)
`command_walk.py --replay-graded`: half-sine drive per half-cycle; within each muscle MNs recruited in order of force per spike, thresholds 0 to 0.8 of the drive peak (thresholds guessed; order from Azevedo 2020). Tethered 5 mm, 10 Hz, seed 0, default damping, FV on, for m7 and m7 + ft_flexor_scale 40. Reading: if the flexor-scale arm gives median femur-tibia 10 Hz swing p2p ≥ 0.3 rad with fewer joints pinned than the symmetric replay (8 of 42), graded recruitment is what lets the measured flexor capacity step, and the blocker for closed-loop walking is the brain-to-MN drive (layer 1), not the body. Neither arm is adopted from this.
Result (20:01): **graded recruitment does not free the joint.** Mean femur-tibia activation stays 0.44 / 0.34 (+1 / -1) under the size-ordered replay; median femur-tibia 10 Hz swing p2p m7 0.04 rad (joint at the extensor end, +0.69-1.0 rad), flexor-scale 0.08 rad (flexion end, -0.8 to -1.27 rad; 8 leg joints pinned). Coxa-trochanter swings are unchanged (0.02-0.27). Closed loop with flexor scale 40, seed 0: silent (0 spikes/ms last 100 ms), no warnings, thorax 0.60 mm.
Conclusion (inferred): no open-loop pattern that drives antagonists comparably can step this leg; the joint goes to whichever muscle is stronger. A real leg holds mid-range posture through feedback (femoral chordotonal organ -> VNC -> tibia MNs, the resistance reflex). The reflex is a held-out physiology test of that circuit.

### Pre-registration: femur-tibia resistance reflex in the closed loop (held-out physiology test, 20:02, before running)
`scripts/probes/resistance_reflex.py`: m7 closed loop, all senses, thorax held 5 mm up; the left front femur-tibia joint is clamped and moved 0.4 rad x sin(2 pi 2 Hz t) for 1 s after a 100 ms hold. Readout: spike rate per MN of the joint's +1 (extensor) and -1 (flexor) pools during imposed flexion (q falling) vs extension. Prediction (resistance reflex: measured in stick insect and locust; reported for Drosophila tibia via the femoral chordotonal organ; for this model inferred): extensor rate flexing/extending ≥ 1.5 and flexor rate extending/flexing ≥ 1.5, with the ratio near 1 when body afferents are zeroed (control). Seed 0, then seeds 1-2 if seed 0 shows any modulation. Nothing in the model was fitted to this. If the pools are silent or unmodulated, the information gap lies between FeCO and the tibia MNs.
Result (20:09), left front leg seed 0: **no reflex.** Extensor pool (2 MNs) silent throughout; flexor pool (15 MNs) tonic 16.3 / 17.6 / 19.1 Hz per MN (hold / flexing / extending; ratio 1.08), identical with body afferents zeroed. The afferents respond as designed (hook_flex 24 Hz only during flexion, hook_ext 24 Hz only during extension, claw ~7 Hz tonic), but the front leg has only 4 claw + 4 hook FeCO afferents in the model (rf 1 + 6) against 21-30 claw and 11-18 hook per middle/hind leg (`scripts/probes/feco_paths.py`; the front-leg FeCO incompleteness was already flagged in SENSORS_MECHANO). Paths exist (claw -> flexor pool 66 direct synapses; 2-hop via IN21A006, IN13A006, IN21A004, IN03A004).
Post-hoc extension (20:09, before running): the same test and criteria on the left middle leg (lm, 25 claw + 12 hook afferents), seed 0 with and without body afferents.
Result (20:11), left middle leg seed 0: **no reflex.** Hook afferents fire 24 Hz in phase with the imposed movement (hook_flex during flexion, hook_ext during extension), claw 1.6-1.8 Hz; extensor pool silent; flexor pool 14.1 / 15.6 / 16.2 Hz (ratio 1.03; afferents zeroed 1.08). The flexor pool's tonic firing is independent of body afferents.
Diagnostic (20:11, before running, not a candidate): proprioceptor rate mode `afferent:leg_proprioceptors|rate_mode_max_hz` 200 (row b21_rate_max, bounds 0-500, guessed; 0 = mV mode, where hook cells cap at 24 Hz). Same lm test. Reading: ratios ≥ 1.5 would mean the circuit carries a resistance reflex once afferent rates are realistic; still ~1 means the block is downstream (interneuron gain or inhibition).
Result (20:16), rate mode 200 Hz, lm seed 0: **still no reflex (ratios 1.0 / 1.03), and the block is at the MNs, not the relay layer.** Afferents: hook_flex 162 Hz flexing / 0 extending, hook_ext 0 / 153, club 82-86, claw 19-21. Relay interneurons (`relay_interneurons` in `runs/s11/reflex/lm_s0_r200.json`: ≥ 20 synapses from claw/hook and ≥ 20 onto a tibia pool; 45 cells) are phase-modulated, several in the resistance direction (IN21A022, excitatory, 247 synapses onto the flexor pool: 0 Hz flexing, 68 Hz extending) and several against it. Per-MN inputs (inspection script, derived): 7 of 11 lm flexor MNs are slow units with the measured-rest-rate tonic drive (spont 36.45 mV) and only 6-33 weak input edges, so they fire regardless; the 4 large flexor MNs and both extensor MNs get the strong relay inputs but sit under tonic inhibition (IN13A006 33 Hz, IN13A014 22 Hz, IN08A005 22 Hz, IN19A005 onto the extensors; IN21A002 and DNg105 onto the flexors) and stay silent. Reading (inferred): at rest the model's leg is "slow flexors on, everything else held off"; a resistance reflex needs the large MNs within reach of threshold, which the tonic inhibitory interneurons prevent. Open: whether those inhibitors' resting activity and the signs of glutamatergic 21A cells (IN21A002 is an inhibitor here) are right.

### 2026-09-30 20:35: direction correction (Director, Ben): walking-diagnostics thread closed

Ben: "Fit to recorded and test walking is EXACTLY what we already tried! We must run a detailed search, inferring missing data with development models, and find 100% of the missing data, and MASSIVELY increase our simulation fidelity." The session-11 walking diagnostics (17:55 onward) drifted toward behaviour-targeted work. They are closed. Their measurements stay as findings (F-RHYTHM-1, F-WALK-1, F-BODY-1, F-REFLEX-1), read as information gaps. Every switch they added stays at neutral: damping 1, optimum_join 0, ft_flexor_scale 1. `docs/ROUTE_TO_BEHAVIOUR.md` is removed and the outside route review was never committed. Direction re-locked to 2026-09-28: the ledger by source level and grain; per-cell rules from development, each at neutral with an equivalence test; transcriptome receptor/channel/innexin tables; all built mechanisms on at their priors; then the bounded search as defined in CONSTRUCTION.md / PLAN_NEXT.md. New: `docs/FIDELITY_LADDER.md` ranks fidelity upgrades. Behaviour stays a guardrail, never an objective.

### Pre-registration: fidelity rung 1 (intrinsic conductances) on at its priors in the working model (20:47, before any whole-CNS run)

Built: `src/flyemu/channels.py` (A-type, M-type, Ih, T-type Ca, persistent Na, spike-triggered Kv2 and BK, SK on a spike Ca pool; rest potential and resting input conductance preserved), switch `cell_type:all|intrinsic_channels` (neutral 0), gbar priors and expression exponent beta 0.5 in parameters.csv (all guessed), densities from `data/derived/channel_expression_by_type.csv` (Davis 2020 + Özel 2021, 82 types) and `channel_expression_allen2020_vnc.csv` (Allen 2020, 21 hemilineages, proxy labels). Single-cell tests pass (`tests/test_channels.py`).
Candidate: m7 + `cell_type:all|intrinsic_channels=1` at the priors. Following the 09-28 direction (all built mechanisms on at their priors); behaviour is a guardrail only.
Milestone criteria (all must hold):
- M1 cost: whole-CNS brain step on the Mac <= 2.0x the m7 step (same stimulus, 3000 steps, `scripts/probes/intrinsic_cost.py`).
- G1 stability: `closed_loop_check.py --seed 12` and `--seed 13` (fresh seeds, spent here): 0 non-tonic spikes after silencing; brain rate excl. ORNs within 0.5-2x of m7 on the same seeds.
- G2 sugar -> MN9_L (100 Hz, 10 trials): > 5 Hz (the standing regression bar). Bitter not run (Mac time).
Adoption if all pass: m8 = m7 + rung 1 becomes the working profile. If any fails, the switch stays neutral in the working model, the failure is diagnosed by channel (which current moves which class), and at most two pre-registered repairs follow; gbar values are never tuned to a behaviour.
Result (21:12): **rung 1 fails M1 and G2; not adopted. `cell_type:all|intrinsic_channels` stays 0 in the working model (m7 unchanged).**
- M1 (measured, `runs/s11/rung1/cost.json`, brain only, 3000 steps): 5.92 ms vs 0.667 ms per step = **8.9x** (bar 2.0x). No resting conductance was capped (n_capped 0).
- G2 (measured, `runs/assay-sugar_mn9-m7-rung1/`): sugar -> MN9_L **1.7 ± 1.1 Hz** over 10 trials (bar > 5; m7 6.9 ± 2.3).
- Same stimulus, brain-only spikes over 300 ms: vnc_motor 421 -> 0, descending 156 -> 26, central intrinsic 783 -> 256; sensory unchanged (985).
- G1 not run: the candidate had already failed, so the fresh seeds 12-13 stay unspent.
Diagnosis by channel (derived, no fitting):
- Subthreshold currents do not cause it (`scripts/probes/intrinsic_rheobase.py`, all male-cns cells at the priors). The extra drive to reach threshold is 0.95x the LIF value for fast input and 1.11x for sustained input (median; 90th percentile 1.22x). The NaP gain offsets the A and M load.
- Spike-triggered SK does (`scripts/probes/intrinsic_fi.py`, single cell, 1 s at a constant drive). At 12 mV of drive the cell fires 50 Hz leak-only and 13 Hz with every channel on. Removing SK restores 35 Hz; removing BK gives 13 and Kv2 13; subthreshold-only gives 49. At 20 mV: 92 / 33 / 67 (no SK).
- The guessed Ca pool explains the size (derived): 1 unit per spike, tau 80 ms, K_d 2 means the pool reaches 0.8 at 10 Hz, so SK is ~30% open. At 40 Hz the pool reaches 3.2 and SK is ~60% open: about 0.3x leak of K conductance, far from E_K. A 3-4x rate cut per cell compounds over the 3-4 synapses from GRN to MN9.
Reading (inferred): rung 1's failure is a single unconstrained guess, the spike-to-SK coupling, not the transcriptome densities or the subthreshold set. The fix must come from recorded physiology, not from the sugar rate.

### Pre-registration: rung-1 repairs (21:12, before any run; at most two)
1. **Spike-triggered channels constrained by recorded single-cell physiology.**
   - Data: Azevedo 2020 current-step trials (cells 181021, 180621, 181127; status seen, not sealed), giving f-I gain and adaptation ratio (last/first ISI) per step amplitude. Add Drosophila central-neuron current-step recordings from the literature, extracted and labelled per class (PN, LN, KC where available).
   - Fit: the SK gbar, Ca per spike, Ca tau and BK/Kv2 increments, at the class prior, within the parameters.csv bounds (0-10x prior), by least squares to those f-I and adaptation curves with the single-cell model at each recorded cell's own measured rest and threshold. MN-derived values are transferred to central cells as inferred.
   - Score: M1, G1 (seeds 12-13 fresh) and G2 with the same bars. Sugar is never in the fit.
   - If the fitted SK hits a bound, record that as a finding; do not widen the bound.
2. **Cost (engineering, no biology change).**
   - Implementation: gate steady states from tables at 0.1 mV resolution instead of per-step exp; channels updated only on cells with nonzero density; float32 throughout; or the GPU path on backhouse.
   - Equivalence: max |v| difference ≤ 1e-3 mV against the current implementation over 1 s of the single-cell tests and 300 ms of the whole CNS.
   - Bar: M1 ≤ 2.0x.

### 2026-09-30 21:17: Ben's answers (via Director) on rung 1 and the ladder
1. Finish rung 1, then climb the ladder (rung 2, synapse dynamics per receptor, next): it is a sequence, not a menu. Compute is no reason to cut fidelity. Port the channels to the GPU on backhouse with a CPU equivalence test instead of simplifying them. **Repair 2 is redefined:** the GPU port, gated by equivalence. Mac cost is reported only, no longer a gate.
2. The spike-triggered channels are fitted to recorded current steps for the classes that have recordings, then scaled per type by channel mRNA (labelled inferred).
3. **The adoption rule changes for mechanisms that add real biology.** The mechanism is adopted once its parameters are filled from data. The parameters that were fitted on the old membrane are then re-searched. Closed-loop silence after the input is removed stays a hard gate. Sugar -> MN9 and other behaviour readouts are recorded as information; they no longer veto. "Mechanisms always on, parameters released gradually; a guardrail miss after adding real biology means the parameters must be re-found, not that the biology comes out."

### Pre-registration: rung 1 repair 1 and adoption, revised rule (21:17, before any fitting)
**Data.**
- Measured: Azevedo 2020 current steps from 4 cells, all R35C09 slow tibia-flexor MNs (180111_F2_C1, 181021_F1_C1, 180621_F1_C1, 181127_F1_C1). The steps are -55 to +110 pA for 0.5 s, recorded at 50 kHz. These trials are "seen", not sealed (the sealed parts are the Piezo trials).
- Literature: current-step f-I and adaptation for central classes (PN, LN, KC, DN where found), extracted per class with source and conditions.
- **Held out:** cell 181127_F1_C1's current steps. They are not used in the fit and are scored afterwards.

**Per recorded cell (derived).**
- Rin from the -25 / -50 pA steps (steady dV/dI).
- tau_m from the charging curve.
- Rest and spike threshold measured on the cell.
- Ih sag ratio from the hyperpolarising steps.
- f-I curve (rate over 0.5 s per amplitude).
- Adaptation ratio (last ISI / first ISI).

**Model.**
- The rung-1 single cell. The recorded rest maps to the model rest (-52 mV) and the threshold keeps its recorded distance from rest.
- Drive in mV = I x Rin (derived).
- tau_m is the cell's own.

**Fitted parameters.** All within parameters.csv bounds; no bound is widened.
- Group S: SK gbar, BK gbar, Kv2 gbar, Ca per spike, Ca tau. Ca per spike and Ca tau get new registry keys and parameters.csv rows, bounds 0.1-10x and 20-500 ms, guessed.
- Group H: Ih gbar, fitted to the sag ratio, if a sag is present (> 2%).
- Other channels stay at their priors.

**Objective.** Least squares on f-I (Hz) and adaptation ratio over the 3 fit cells, with equal weights per cell.

**Labels.**
- Fitted values: derived from measurement for the slow-MN class.
- The same values applied to other MNs and to central cells without data: inferred. Literature classes, where found, override them.
- Per-type scaling by mRNA: unchanged (rel_level^beta, inferred).

**Held-out check (reported, not a gate).** Predicted f-I on 181127 within 30% RMS of its recorded rates.

**Adoption (revised rule).** m8 = m7 + rung 1 at the fitted values. Gates:
- G1 hard: `closed_loop_check.py` seeds 12 and 13 give 0 non-tonic spikes after silencing, with no runaway (no cell class over 200 Hz).
- GPU equivalence: the batched GPU brain with channels matches the CPU path on a 300 ms whole-CNS run (spike-count correlation per cell ≥ 0.99 and total spikes within 2%, the bar used for earlier ports), measured on backhouse.

**Reported as information:** sugar -> MN9_L, brain rates by class, Mac cost.

**Then** the joint re-search of the m5 class values (DN release, MN_other input) and the central size rule on the new membrane, as in session 10's search (pre-registered separately before it runs).
Deviation (21:20, before fitting): **the spike threshold cannot be measured in these recordings.** Somatic spikes are 2-5 mV, initiated distally (raw traces in `runs/s11/rung1/azevedo/raw_steps.png`).
- The slow-MN threshold distance θ is therefore fitted jointly as a class value, bounded 5-35 mV. The session-6 LIF-only fit gave 32.6 mV, θ fitted with t_ref 4.27 ms. Here t_ref is fixed at 2.2 ms (network default).
- A tonic drive d0 per cell is fitted as a nuisance to that cell's spontaneous rate. It is not transferred.
- With rung 1 on, the slow-MN class rows (v_th, spontaneous_drive) take the jointly fitted θ and the mean d0, so that the session-6 values, fitted without channels, are not double-counted.
- Features (`data/derived/azevedo2020_current_step_features.csv`, measured), compared at every step on the fit cells:
  - spontaneous rate;
  - rate over 0.55-1.0 s;
  - late/early rate ratio (0.9-1.0 s over 0.5-0.6 s);
  - sag fraction on the largest hyperpolarising step.
- Weights: 10 Hz, 0.1 and 0.05 per unit. Each cell's terms are averaged, then the cells are averaged.
- Baselines reported alongside: (i) the channel priors with θ and d0 fitted; (ii) LIF only with θ and d0 fitted.

### Result: rung-1 repair 1 fitted; m8 = m7 + rung 1 adopted (21:47)
**Fit** (`scripts/fit_spike_channels.py`, differential evolution, 4 seeds; `runs/s11/rung1/spike_channel_fit*.json`). Loss by seed (lower is better):

| Seed, gens | Loss | SK | BK | Kv2 | Ca/spike | Ca tau ms | h | θ mV | Held-out rel RMS |
|---|---|---|---|---|---|---|---|---|---|
| 0, 60 | 1.254 | 2.82 | 6.84 | 0.30 | 0.11 | 30 | 0.031 | 19.2 | 0.047 |
| 1, 60 | 1.671 | 0.07 | 8.91 | 0.83 | 1.29 | 39 | 0.001 | 19.5 | 0.054 |
| 2, 150 | 1.474 | 0.001 | 0.04 | 0.96 | 0.15 | 84 | 0.002 | 34.0 | 0.009 |
| **3, 150** | **1.028** | **0.027** | **8.69** | **0.27** | **1.24** | **38** | **0.050** | **26.2** | **0.032** |

Baselines (θ and d0 fitted): channel priors loss 2.87-3.79; LIF only 2.14-2.42 (held-out 0.09-0.12).
- Adopted: seed 3 (lowest loss). Values are derived for the slow-MN class and inferred elsewhere (scaled by each type's channel mRNA).
- Slow-MN class under rung 1: θ 26.2 mV, t_ref 2.2 ms, tonic drive 35.55 mV (mean of the 3 fitted cells). These are new `*_rung1` rows in `data/params/cell_types.csv`, read only when the channels are on.
- Profile m8 stores each gbar as the slow-MN value divided by the slow-MN expression factor, so the recorded class gets the fitted value exactly. Checked on the built brain: the 60 slow MNs have BK 8.694, SK 0.0272, Kv2 0.2748, h 0.0502, Ca/spike 1.245, θ 26.2, spont 35.55.
- Held-out cell 181127 passes (3% rel RMS). But LIF only also passes (10%), so this check is weak.

**GPU port** (`src/flyemu/gpu/batched.py`). Gates advance on the pre-update v, the conductance-form exponential Euler, and on_spike after the reset, as on the CPU. A per-member v_rest is refused.
- Toy test (`tests/test_gpu_batched.py`, 2 new cases): exact raster match (415 spikes with channels, 516 without).
- Whole CNS, m8, 300 ms, backhouse RTX 4070 Ti SUPER (`runs/gpu_equiv/{sugar,broad}_300ms_m8.json` there):
  - sugar: 1,939 vs 1,939 spikes over 179 active cells, per-cell counts identical, 2 steps with a one-step spike shift. Reference member shown; the class-gains member was exact.
  - broad: 32,947 vs 32,947 spikes over 5,957 active cells, per-cell counts identical.
  - **Pass** (bar: correlation ≥ 0.99, totals within 2%). GPU 4.0 s for 2 members × 300 ms including compile.

**G1 hard gate** (`runs/s11/rung1/g1/`, closed_loop_check 1 s senses + 300 ms silent):

| | m8 s12 | m8 s13 | m7 s12 | m7 s13 |
|---|---|---|---|---|
| Spikes in last 100 ms silent | 0 | 0 | 0 | 0 |
| Spikes in whole silent window | 154 | 136 | 368 | 34 |
| Brain Hz (excl. ORN) | 0.244 (0.071) | 0.232 (0.061) | 0.344 (0.126) | 0.330 (0.112) |
| Motor Hz | 2.40 | 2.38 | 2.99 | 2.85 |
| Wall s | 123 | 122 | 56 | 55 |

- **Pass**: no NaN, no ongoing activity after silencing. The script does not report a per-class maximum rate. The brain mean of 0.24 Hz over 167k cells bounds any 200 Hz class to under ~200 cells, and the last 100 ms is silent.
- Information: sugar -> MN9_L (assay_pathways, 100 Hz, 10 trials) m8 **2.7 ± 1.1 Hz**; m7 re-run now 6.9 ± 2.3 Hz (`runs/s11/rung1/g1/m7_sugar.txt`; older m7-tagged files at 0.5-1.8 Hz predate m7's motor-only rule); rung-1 priors 1.7. The fitted membrane recovers part of the loss; the class gains fitted on the leak-only membrane must be re-found (Ben's answer 3). Mac cost per 1 s brain trial: 54.9 s vs 6.5 s (8.4x); whole organism 2.2x. The GPU path now carries the channels.

**Decision:** m8 adopted as the working profile (`profiles.WORKING_PROFILE`). m7 is kept. Next is the separately pre-registered joint re-search of the class values on the new membrane.

### Pre-registration: joint re-search of the class gains and the central size rule on the m8 membrane (22:01, before any run)
Motivation (Ben's answer 3): mechanisms stay on; the class gains fitted on the leak-only membrane are re-found. Under m8, sugar -> MN9_L is 2.7 Hz (bar 5).
- **Parameters (5).** All bounds come from parameters.csv; none may be widened.
  - `class:DN|release_scale` (m8: 0.70) and `class:MN_other|input_scale` (1.30): the m5 pair.
  - `class:sensory_gustatory|release_scale` and `class:MN_other|release_scale`: the MN9-path levers active in the s10 search.
  - `cell_type:all|within_type_size_exponent` (central size rule, 0-1.5; m8: 0).
- **Objective (MAP style, as s10).** Minimise the prior departure: Σ((log x)/0.5)² for the scales, plus ((e - 1.0)/0.25)² for the size exponent (its declared prior normal(1.0, 0.25), so the rule is favoured on). This is subject to:
  - (i) 0 non-tonic spikes in the last 100 ms of the silent window on **fit seeds 14, 15, 16**. Fresh seeds; closed_loop_check, m8 body.
  - (ii) sugar -> MN9_L > 5 Hz (100 Hz, 10 trials).
  - Violations are penalised as in s10: 10 × log1p(silent spikes/ms) per seed, plus 10 × max(0, 5.5 - MN9 Hz).
- **Method.** Run on backhouse CPU, ≤ 14 processes, resumable: one JSON per run, and collect skips finished runs.
  - Screen: m8 values; each lever at 2 values toward MN9 drive; exponent at 0.5 and 1.0.
  - Then random combinations within ±2x of the screen's best levers, then refinements. ≤ 60 candidates in total.
- **Held out** (run once on the best candidate, never seen):
  - closed loop seeds 17, 18, 19 silent;
  - bitter suppression: sugar+bitter 100 Hz gives MN9_L ≤ 50% of bitter 0;
  - sugar dose response: 200 Hz > 2x the 100 Hz rate;
  - bitter -> MN9_L < 2 Hz at 100 Hz.
- **Adoption.** All pass: m9 = m8 + the values becomes the working profile. A size exponent ending at 0 is reported as a finding against the central rule. Any fail: the values go to `data/params/hypotheses_not_adopted.csv`, with at most two pre-registered repairs. m8 stays working meanwhile.
Search record, screen (22:47; `runs/s11_rs_screen/` on backhouse, 12 candidates × seeds 14-16 + sugar).
- Every candidate is silent on all 3 fit seeds, including DN release 0.85 and 1.0. On the m8 membrane, DN suppression is no longer needed for silence.
- Sugar -> MN9_L by lever (Hz):
  - m8 values: 2.5.
  - Size exponent 0.5 / 1.0: 2.8 / 2.1.
  - MN_other input 2.0 / 3.0: 5.5 / 5.6.
  - Gustatory release 1.5 / 2.5: 7.0 / 27.1.
  - MN_other release 1.5 / 2.5: 2.5 / 2.5 (inactive).
  - DN 0.85 / 1.0: 1.7 / 2.1.
- Best: DN 0.7, MN_other input 2.0, gustatory 1.5, exponent 1.0, giving 11.4 Hz (J 3.09).
- Phase 2, a grid that lowers the prior cost: DN {0.85, 1.0} × MN_other input {1.0, 1.3, 1.6} × gustatory {1.25, 1.5}, exponent 1.0; plus exponent 0.75 and 1.25 at (1.0, 1.3, 1.5). 14 candidates; MN_other release fixed at 1.
Search record, phase 2 (23:35; `runs/s11_rs_p2/`, 14 candidates, all silent on seeds 14-16). MN_other release and size exponent are 1.0 throughout unless stated. Sugar -> MN9_L (Hz) and J:

| DN \ MN_other input, gust | 1.0, 1.25 | 1.0, 1.5 | 1.3, 1.25 | 1.3, 1.5 | 1.6, 1.25 | 1.6, 1.5 |
|---|---|---|---|---|---|---|
| 0.85 | 0.1 / 54.3 | 0.7 / 48.8 | 3.4 / 21.6 | 3.7 / 19.0 | **5.7 / 1.19** | 7.0 / 1.65 |
| 1.0 | 0.7 / 48.2 | 0.5 / 50.7 | 1.8 / 37.5 | 2.7 / 28.9 | 3.8 / 18.1 | 5.2 / 4.54 |

- At (DN 1.0, MN_other input 1.3, gust 1.5), size exponents 0.75 and 1.25 both give 2.7 Hz (J 29.9). The trials differ, but the MN9 rate is insensitive to the central exponent, because motor neurons use their own fitted exponent.
- MN_other input is the dominant lever. Gustatory release adds about 1 Hz per 0.25.
- Refinement (phase 3, 8 candidates): DN {0.85, 1.0} × MN_other input {1.45, 1.75} × gust {1.0, 1.25}. The total stays within the 60-candidate budget (34 used).
Search record, phase 3 (00:04; `runs/s11_rs_p3/`, all silent on seeds 14-16). MN9_L Hz / J:

| DN \ MN_other input, gust | 1.45, 1.0 | 1.45, 1.25 | 1.75, 1.0 | 1.75, 1.25 |
|---|---|---|---|---|
| 0.85 | 1.7 / 38.7 | 4.3 / 12.9 | 2.6 / 30.4 | 6.4 / 1.56 |
| 1.0 | 2.1 / 34.6 | 3.0 / 25.8 | 3.1 / 25.3 | 4.3 / 13.5 |

The search ends at 42 of 60 candidates. Best overall is phase 2's (DN 0.85, MN_other input 1.6, gust 1.25, MN_other release 1.0, exponent 1.0): MN9_L 5.7 Hz, J 1.19.
- This sits just above the 5.5 bar. The trial SD is about 2 Hz, and neighbours at 1.45 and 1.75 give 4.3 and 6.4, so the bar is crossed on a noisy slope.
- Silence held on every one of the 42 candidates.
- The size exponent stays at 1.0, so the central rule survives on m8.
- Held out: launched once on this candidate at 00:04 (`runs/s11_rs_heldout/`).

### Result: joint re-search held out; m9 = m8 + re-searched class gains adopted (00:27, 2026-10-01)
Held out, run once on the best fit candidate (`runs/s11_rs_heldout/` on backhouse, m8 + `--set`). All four pass:

| Test | Criterion | Measured | Verdict |
|---|---|---|---|
| Closed loop seeds 17/18/19 | 0 spikes, last 100 ms | 0 / 0 / 0 (brain 0.23 Hz, motor 2.4-2.5 Hz, no MuJoCo warnings) | pass |
| Bitter suppression | sugar+bitter 100 ≤ 50% of bitter 0 | 0.0 vs 4.8 ± 1.7 Hz | pass |
| Sugar dose response | 200 Hz > 2 × 100 Hz | 15.7 ± 1.6 vs 5.7 ± 1.4 Hz | pass |
| Bitter alone | MN9_L < 2 Hz at 100 Hz | 0.0 Hz | pass |

- m9 = M8 + DN release 0.85, MN_other input 1.6, gustatory release 1.25, central size exponent 1.0 (MN_other release stays at 1.0). It is now `WORKING_PROFILE`.
- The size exponent did not end at 0, so there is no finding against the central rule.
- Checks:
  - Full suite: 164 passed under m9.
  - `--profile m9` without overrides reproduces the held-out sugar trials exactly (7, 6, 7 Hz for trials 0-2, on backhouse).
- Caveat (F-RS-1): the sugar fit bar is crossed on a noisy slope. A 10-trial replicate inside the bitter assay gave 4.8 Hz.

### Pre-registration: rung 2, synapse receptor mix and kinetics per postsynaptic type (00:45, 2026-10-01, before any run)
Director instruction: pre-register; port the conductance-synapse switch to the GPU with CPU equivalence; fill per-type receptor composition from the receptor tables (labelled); switch it on at priors; re-search the class gains as with rung 1. m9 stays working until the gates below pass.

**Mechanisms.** Each enters neutral, with a bit-identical neutral test.
- **R2a. Conductance synapses** (`cell_type:all|conductance_based`, which exists on the CPU).
  - Fast excitatory and inhibitory conductances with reversals e_exc 0 and e_inh -70 mV (the N9 priors).
  - Weights are scaled so the PSP at rest is unchanged.
  - GPU port in `gpu/batched.py`, replacing the refusal.
- **R2b. Receptor shares per postsynaptic cell from transcriptomes** (`src/flyemu/receptors.py`; switch `cell_type:all|receptor_shares_from_rna`, neutral 0). The probability that a cell expresses gene X, p(X), is taken from the first source that has it:
  1. per type, Davis 2020 / Özel 2021 `p_expressed` (mean of the two where both exist);
  2. the VNC hemilineage `frac_expressed` (Allen 2020);
  3. otherwise the mean over profiled types (population prior).
  Labels: inferred in every case, with the source recorded per cell. The slow share of each transmitter's input is then f = s·p_slow / (s·p_slow + p_fast), where:
  - GABA: p_slow = p(GABA-B-R1)·p(GABA-B-R2), the obligate heterodimer; p_fast = p(Rdl). This gives `gabab_fraction`.
  - ACh: p_slow = max(p(mAChR-A), p(mAChR-B)); p_fast = max over nAChRα1/5/6/7. This gives `machr_fraction`.
  - Glutamate: p_slow = p(mGluR); p_fast = max(GluClα, GluRIA, GluRIB). This gives `mglur_fraction`.
  - NMDA, of excitatory glutamate: p_slow = p(Nmdar1)·p(Nmdar2); p_fast = max(GluRIA, GluRIB). This gives `nmda_fraction`.
  - s is one rule parameter per receptor family (`receptor:<family>|slow_peak_ratio`): the peak of the slow current relative to the fast at equal expression. It is guessed at a prior of 0.05, with bounds 0-0.3. The model's slow pools copy a share of the fast peak, so even small shares carry large charge (tau 150-300 vs 5 ms).
  - The glutamate sign per type is already filled (66 rows) and is not changed.
- **R2c. A separate decay for the fast inhibitory conductance** (`cell_type:all|tau_s_inh`). It is neutral when equal to tau_s (5 ms); guessed prior 10 ms (GABA-A/GluCl IPSCs decay more slowly than nicotinic EPSCs; fly values unread, so the prior is guessed). It is only active when R2a is on.
- **Not in this rung** (stated gaps): a rise time per receptor; facilitation and release probability; ORN and leg depression on.

**Gates**
- **A. Mechanism.**
  - The neutral switches are bit-identical, checked by tests.
  - GPU equals CPU:
    - toy networks: exact, with cond, cond+channels and cond+slow pools;
    - whole CNS, m9 + R2a/b/c at priors, 300 ms sugar and broad stimuli: total spikes within 0.1%, and at least 99.9% of cells with identical counts.
- **B. Candidate at priors** (m10p = m9 + R2a + R2b + R2c, all at priors):
  - closed loop fit seeds 20, 21, 22 silent (closed_loop_check, last 100 ms);
  - sugar -> MN9_L (100 Hz, 10 trials) measured.
  If silent and MN9_L > 5.5 Hz, it goes straight to held out. Otherwise the class gains are re-searched.
- **C. Re-search** (as s11 rung 1). Same objective and prior as DECISIONS 22:01. The levers are DN release, MN_other input, gustatory release and MN_other release, starting from m9's values. The receptor rule parameters stay at their priors. At most 30 candidates, on fit seeds 20-22 plus sugar, on backhouse.
- **D. Held out, run once on the best:**
  - closed loop seeds 23, 24, 25 silent;
  - sugar+bitter 100 Hz ≤ 50% of bitter 0;
  - sugar 200 Hz > 2 × 100 Hz;
  - bitter alone < 2 Hz.
  All pass: m10 is adopted as working. Any fail: record in hypotheses_not_adopted.csv; m9 stays.
- **Cost.** A Mac per-step brain cost above 1.5x m9 is reported, not gating. The GPU is the throughput path.
- **Not targets.** Walking and recorded behaviour are guardrails only, per Ben.

### Result: rung 2 gates A and B, and repair 1 pre-registered (01:06)
**Gate A: passes.**
- The neutral switches are bit-identical (2 new tests).
- Toy GPU vs CPU is exact: cond 488/488 spikes, cond+channels+slow 881/881, cond+adapt+std+gabab+mod 405/405.
- Whole CNS, m10p, 300 ms on backhouse:
  - sugar: exact, 2,299 = 2,299 spikes;
  - broad: 34,273 = 34,273 spikes over 5,990 active cells, with identical counts in every cell (36 steps carry a one-step shift).
- Full suite: 169 passed. Mac brain step cost: 6.03 ms (m10p) vs 4.90 ms (m9), i.e. 1.23x.
- Receptor-share coverage: 73,253 cells from type mRNA, 10,492 from VNC hemilineage, 83,366 from the population prior.
- Mean shares: GABA-B 0.045, mAChR 0.033, mGluR 0.013, NMDA 0.062.
  - 3,555 cells have GABA-B > 0.5, and 8,215 have NMDA > 0.5. These lack Rdl or GluRIA/B mRNA.

**Gate B (m10p at priors): fails silence.** Closed loop seeds 20/21/22 give 94.7 / 80.8 / 97.6 spikes/ms in the last 100 ms. No MuJoCo warnings; brain 0.36-0.39 Hz.

**Diagnosis** (seed 20, diagnostic only, not scored):

| Variant | Silent spikes/ms |
|---|---|
| Shares off (cond + tau_s_inh) | 0.0 |
| mAChR ratio 0, rest on | 0.0 |
| Cond off, mAChR 0 | 0.0 |

Cause: the muscarinic share. The model's slow pools copy a share of the fast *peak* into a 300 ms current. A mean mAChR share of 0.033 therefore adds about 0.033 × 300/5 ≈ 2x the fast cholinergic charge. Since ACh is the dominant transmitter, cholinergic excitation roughly triples. The pre-registration noted this ("small shares carry large charge"). The class gains cannot sensibly remove a brain-wide 3x cholinergic increase.

**Repair 1** (pre-registered now, before any run of it): define the slow share by **charge**, not peak.
- New switch `cell_type:all|slow_share_basis`: 0 = peak (m4-m9 meaning, neutral), 1 = charge. With charge, a share f moves f of the synapse's fast charge to the slow receptor:
  - the fast peak is scaled by (1 - f);
  - the slow peak is f × tau_s / tau_slow.
  The per-cell tau_s (excitatory fast decay) is used for every family. This is an approximation for inhibitory families, where tau_s_inh differs.
- Reason: the rule's s is meant as the slow receptor's share of transmission at equal expression. On a peak basis, a 5% prior silently means 300% of the charge. The prior s stays 0.05, now read as a charge share (guessed).
- Repair 1 is scored exactly as gate B, on fit seeds 20-22 plus sugar. Then gates C and D follow unchanged (held-out seeds 23-25 are still unseen). One repair remains.

### Result: repair 1 at priors, and Gate C pre-registered (01:18)
**Repair 1 (m10p = m9 + cond + receptor shares + tau_s_inh 10 + charge basis), fit seeds:**
- Closed loop seeds 20/21/22: 0.0 / 0.0 / 0.0 spikes/ms. Silence passes; the brain runs at 0.25 Hz.
- Sugar to MN9_L at 100 Hz: 0.0 Hz in 10 trials, with about 157 cells active.
  - Peak basis (before repair 1): 149 Hz, with the loop not silent.
  - m9: 5.7 Hz.
- Gate B fails on sugar, so Gate C runs.
- Diagnostic only: with cond off and shares on (peak basis), seed 20 gave 370 spikes/ms. The conductance synapses were limiting the runaway, not causing it.

**Gate C** (pre-registered now; before any candidate is run). Profile m10p.
- Up to 30 candidates on fit seeds 20-22 plus sugar 100 Hz, scored with the s11 objective (prior cost + 10 log1p(silent) per seed + 10 max(0, 5.5 - MN9)).
- Candidates: a log-uniform Latin hypercube (numpy seed 11) over:
  - `class:DN|release_scale` 0.85-2.5;
  - `class:MN_other|input_scale` 1.6-4;
  - `class:sensory_gustatory|release_scale` 1.25-4;
  - `class:MN_other|release_scale` 0.7-1.5.
- The lower bounds sit at the m9 values (MN_other release at its neutral 1, with a range to 0.7), because the change removed sugar drive.
- At most one refinement batch, of up to 10 candidates around the best, if no candidate passes.
- The best candidate with J below 5 (silent on all three seeds and MN9 at least 5.5 Hz, within prior cost 5) goes once to Gate D, on held-out seeds 23-25 plus the held-out assays.
- If nothing reaches J below 5, rung 2 is not adopted this session; m9 stays the working profile, and the result is recorded in hypotheses_not_adopted.csv.

**Gate C amendment (01:34, before any candidate result exists): staged evaluation on the Mac.**
- The first launch on backhouse (16 parallel) was killed by the out-of-memory killer. No candidate result exists.
- The WSL VM's 31 GB is about 95% used by another project's distro. Running more there risks killing their processes, so the screen moves to the Mac, which only has the compute for a staged evaluation:
  1. **Sugar screen.** All 30 pre-registered candidates (unchanged), at 3 trials each instead of 10, 2 in parallel.
  2. **Full scoring.** Only candidates with a screen mean of at least 4.0 Hz get it: sugar at 10 trials, plus closed loop on seeds 20-22. Below 4 Hz a candidate cannot plausibly reach the J < 5 bar, which needs MN9 above 5.
- The objective, bounds, pass bar and Gate D are unchanged. If the screen's cut-off excludes a candidate that the full protocol would have passed, the pass bar is not loosened to compensate.

### Result: Gate C fails; rung 2 not adopted; m9 stays the working profile (02:44)
**Sugar screen** (profile m10p, 30 pre-registered candidates, 3 trials each, Mac; `runs/s11_r2_gc/screen_summary.csv`):
- 29 candidates give MN9_L 0.0 Hz. The best, c009 (DN 2.20, MN_other input 3.53, gust 1.36, MN_other release 0.91), gives 0.7 Hz.
- None reaches the 4.0 Hz screen bar, so none was fully scored.
- The optional refinement batch was not run: around a 0.7 Hz best it cannot reach the bar.
- Rung 2 is not adopted. The rows are added to `data/params/hypotheses_not_adopted.csv`, and Gate D (held-out seeds 23-25) stays unseen.

**Diagnostics** (sugar 100 Hz, 3 trials each, Mac; not scored, recorded to aim the next step):

| Profile | MN9_L Hz (3 trials) |
|---|---|
| m9 | 7, 6, 7 |
| m9 + cond | 2, 0, 1 |
| m10p with cond off (shares, charge basis) | 6, 3, 5 |
| m10p with receptor shares off | 0, 0, 0 |
| m10p with tau_s_inh 0 | 1, 1, 0 |
| m9 + cond, e_inh -55 | 0, 0, 0 |
| m9 + cond, e_exc +10 | 0, 0, 0 |

- **Conductance synapses are what remove the sugar response.** The receptor shares with charge basis are close to neutral on it.
- Per-cell trace (`scripts/probes/sugar_cond_trace.py`, m9 vs m9 + cond):
  - The loss sits 1-2 synapses from the sugar neurons.
  - MN9_L's main excitatory input, GNG108 (348 synapses), falls from 11 to 1.3 Hz.
  - 14 cells above 1 Hz go silent, 11 of them at hop 2 (GNG second-order neurons, DNge098/101/106).
- Inferred mechanism, not proven: inhibition grows under conductance synapses.
  - With v_rest -52 and e_inh -70, the weight-to-conductance scaling gives inhibitory synapses about 3x the conductance per mV of resting PSP that excitatory ones get (1/18 vs 1/52).
  - Their drive also grows about 1.4x between rest and threshold (-45).
  - Moving e_inh to -55 (about 6x more inhibitory conductance) also gives 0 Hz.
  - The e_exc +10 result is within noise of m9 + cond.
- **Next discriminating experiment.** Record GNG108's excitatory and inhibitory input currents in m9 vs m9 + cond to separate shunting from driving force. Then pre-register a re-search whose box includes the levers that actually act on inhibition:
  - `class:*` GABA/glutamate release;
  - per-type v_rest from measured rest potentials (currently one borrowed value, -52);
  - e_inh within its bounds;
  - rather than the pathway-end gains used in this Gate C.

### Pre-registration: fill reversal and resting potentials from recordings; rung 2 repair 2 (02:49, before any run)
**F1. Inhibitory reversal e_inh = -56 mV** (measured_related; prior sd 3).
- GABA currents in larval central neurons reverse at -56 ± 3 mV (Rohrbough & Broadie 2002, J Neurophysiol 88:847).
- A 1 s GABA pulse holds adult antennal-lobe PNs at -56 ± 2 mV (Wilson & Laurent 2005, J Neurosci 25:9069), a lower bound on E_GABA.
- This replaces the guessed -70. One value for all cells; GluCl is assumed to share the chloride reversal (inferred).

**F2. Repair 2: the voltage at which conductance weights keep their fitted effect** (`cell_type:all|cond_reference`: 0 = rest, as in m10p; 1 = threshold).
- With E_Cl only about 4 mV below the -52 rest, keeping the resting PSP needs 4.5x the inhibitory conductance of m10p. That is a shunt the class efficacies were never fitted against.
- The efficacies were fitted on spiking outcomes, so the reference becomes each cell's threshold: weight / (e_exc - v_th) for excitation and weight / (v_th - e_inh) for inhibition.
- This is the second and last repair allowed for rung 2.

**F3. Per-type resting potentials from the measurement library.** Only rows not reserved as held out are used.
- Mi1, Tm1, Tm2 and Tm4 get v_rest = -55 mV (centre of -50 to -60; Behnia et al. 2014, measured_related).
- v_th and v_reset shift by the same -3 mV, keeping the gap (inferred).
- Not used:
  - Azevedo 2020 MN rests and Agrawal 2020 VNC interneuron rests stay held out;
  - DN AX (-59, Schnell 2017) has no confident male-CNS type match;
  - the PN estimate is model-based.
- The global v_rest stays -52, because no measurement covers the bulk.

**Candidate m10q = m10p + F1 + F2 + F3.** No gains are re-searched.
- Fit: closed loop on fresh seeds 26-28 silent, and sugar to MN9_L at least 5.5 Hz (10 trials).
- If both pass: the held-out test runs once (seeds 23-25 silent, bitter suppression, sugar dose response, bitter alone), and m10 is adopted if all pass.
- Otherwise: recorded as not adopted, with m9 kept.

### Result: m10q fit fails the sugar bar; not adopted; m9 stays (03:01)
**m10q** (m10p + recorded e_inh -56, weights referenced to threshold, Mi1/Tm1/Tm2/Tm4 rest -55), scored on its fit tests:
- Closed loop seeds 26/27/28: 0.0 / 0.0 / 0.0 spikes/ms. Passes.
- Sugar to MN9_L at 100 Hz: 2.4 ± 1.6 Hz over 10 trials (2, 0, 4, 3, 3, 0, 5, 1, 3, 3). Fails the 5.5 Hz bar.
- Held-out seeds 23-25 and the held-out assays remain unseen.
- With the recorded chloride reversal, repair 2 recovers part of the sugar pathway (m10p 0 Hz; m9 + cond 1 Hz).
- The F1 and F3 fills stay in the tables as information, neutral by default (`cell_type:all|rest_from_recordings`, e_inh only in m10q).
- Both rung-2 repairs are spent. Pre-registered next step: a class-gain re-search on m10q, with inhibitory release in the box, on fresh fit seeds from 29.

### Pre-registration: class-gain search on m10q with an inhibitory gain (03:23, before any run)
- **New lever:** `cell_type:all|inh_cond_scale`, the inhibitory conductance per unit fitted weight in conductance mode. Neutral 1, bounds 0.25-1.5, prior lognormal(1, 0.5), guessed. There is no transmitter-level inhibitory gain otherwise, and the class efficacies were fitted with current synapses.
- **Candidates:** 24, as a log-uniform Latin hypercube (numpy seed 29) over:
  - inh_cond_scale 0.3-1.2;
  - `class:DN|release_scale` 0.85-2;
  - `class:MN_other|input_scale` 1.6-4;
  - `class:sensory_gustatory|release_scale` 1.25-3;
  - `class:central_other|release_scale` 0.8-1.3.
- **Staged on backhouse**, within free memory (4 jobs at a time, about 8 GB), resumable:
  1. Sugar to MN9_L at 100 Hz, 10 trials, for every candidate.
  2. Candidates at or above 5.5 Hz get the closed loop on fresh seeds 29-31.
- **Score:** the s11 objective. Pick the lowest J among candidates that are silent on all three seeds with MN9 at least 5.5. That candidate goes once to the held-out test (seeds 23-25 plus the held-out assays). If it passes, m10 is adopted.
- Whatever is unfinished at 04:45 stays running detached for the next session, which must not re-run finished jobs.

### Amendment: closed-loop stage runs on the Mac (03:47, after the first 4 sugar results, before any closed loop was scored)
- The backhouse is full with 4 sugar jobs (7 GB free), so the closed loops for candidates that pass the sugar bar run on the Mac instead. Same script, same seeds 29-31, same profile and overrides, results in `runs/s11_m10q_gs_cl/`. The scoring is unchanged.
- An observation, not a scoring change: the pre-registered objective has no upper bar on MN9. Round 1 gave 100, 178, 10.4 and 214 Hz. Rates above 100 Hz are probably beyond what the real MN9 does (inferred; no recorded MN9 sugar rate is in the tables). A future objective should take a two-sided band from a recording.

### Result (partial): 12 of 24 search candidates scored; c008 leads; search continues detached (04:33)
Measured, m10q, sugar 10 trials at 100 Hz, closed loop on seeds 29/30/31 (spikes/ms in the last 100 ms). J is the s11 objective.

| cand | MN9 Hz | silence 29/30/31 | J |
|---|---|---|---|
| c008 | 8.1 | 0 / 0 / 0 | **3.68** |
| c002 | 10.4 | 0 / 0 / 0 | 5.92 |
| c001 | 178.3 | 0 / 0 / 0 | 14.12 |
| c005 | 108.4 | 0 / 3.0 / 0 | 20.65 |
| c011 | 9.5 | 0 / 7.6 / 0 | 27.14 |
| the other 7 | 20-215 | fail on 2-3 seeds | 50-150 |

- **Leader c008:**
  - inh_cond_scale 1.107;
  - DN release 1.193;
  - MN_other input 1.792;
  - gustatory release 2.049;
  - central_other release 1.163.
- Every one of the 12 clears the sugar bar. Silence is the binding gate: a high MN9 rate goes with runaway (5 of 6 candidates above 100 Hz fail at least one seed). The candidates that pass sit near the bar, at 8-10 Hz, except c001. With these boxes, inhibitory release alone does not decide sugar transmission (c008 has 1.1, c002 0.71, c001 0.32).
- **Not yet decided:** the pre-registered pick is across all 24. Candidates c012-c023 are running detached on backhouse (tmux `s11_m10q_gs`, sugar stage). The Mac closed-loop results are copied into `runs/s11_m10q_gs/`, so `collect` sees them. Held-out seeds 23-25 and the held-out assays are still unseen.

## Session 12 decisions (4 October 2026)

### Wings at rest: two switches, adoption gated on m9's silence seeds (pre-registered 17:35, before any gate run was read)
- **Diagnosis (F-WING-2, F-SENSE-NERVE-1).** On seed 12, the resting wing motor neurons fire because wing-nerve campaniforms were driven as leg load. The legacy wing map also sends the steering muscles to the wrong axes.
- **Fixes.** Two switches, each with the legacy behaviour as neutral:
  - `motor_map:wing|roles`: a sourced role table;
  - `sense:mechano|assign_by_nerve`: census entry nerve.
  - Neither was fitted. Each follows from anatomy, and seed 12 was used only to find the fault.
- **Adoption test.** Both switches on, with everything else exactly as at m9's adoption: `closed_loop_check.py`, non-leg torque per spike 10, seeds 12-19.
  - Pass: `silent_last100ms_spikes_per_ms` is 0 on all 8 seeds, the same criterion as m9.
  - Sugar to MN9 is not re-run, because `assay_pathways.py` is brain-only and builds no afferents, so neither switch can change it.
  - If all 8 pass, a profile m9w = m9 + the two switches becomes the working profile. m9 is kept.
  - If any seed fails, the switches are not adopted, and the failing seed and the classes carrying its spikes are recorded.
- **Not part of this decision.** The 10× non-leg torque per spike stays in the gate scripts. Changing it would change m9's gate conditions. F-WING-2 records that it throws the wings, and replacing it with a wing value needs a source.

### Result: m9w adopted; seeds 12-19 silent with both switches (17:50)
- Measured with `closed_loop_check.py`, everything as at m9 adoption plus the two switches. Outputs are in `runs/s12/gates/cl_rn_s{12..19}.json`.

| seed | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|
| spikes/ms, last 100 ms of silence | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| whole-brain Hz with senses on | 0.252 | 0.251 | 0.245 | 0.250 | 0.249 | 0.240 | 0.251 | 0.249 |

- No MuJoCo warnings and no NaN state on any seed. Motor rate is 2.02-2.06 Hz.
- `profiles.M9W` = m9 + `motor_map:wing|roles` + `sense:mechano|assign_by_nerve`, and it is now the default `WORKING_PROFILE`. m9 is kept (`FLYEMU_PROFILE=m9`).
- Sugar to MN9 is unchanged by construction: the assay is brain-only.
- The thorax ends at 0.52-0.55 mm on every seed, and the contact sheets show the fly on its belly. That is m9's leg output and is carried as an open item, not part of this test.

### Coxa ranges kept off; standing needs a resting support drive that no data fix (18:23)
- **`joint:coxa|range_source` stays at 0.** The flybody ranges and the refit rest angles pass the dead-fly test. However, they leave the trunk on the floor (thorax 0.77 mm against a target near 1.0 mm), and they prop the front legs forward and up on a non-unique +90° coxa solution (F-COXA-2). Live equals dead, so the switch does not change any live result. It is kept, tested, for the next attempt.
- **One principled refit is left, not run.** Regularise the five references toward flybody's native spring references instead of the spawn pose. That would choose among the equal-residual front solutions by an outside prior, not by standing. If it is tried, it is fix 1 of at most 2, and the dead-fly test and contact sheet decide it.
- **Standing (F-STAND-3).** Rest angles, ranges, passive stiffness and adhesion do not hold the fly up, and the measured physiology says they should not. Wang 2025 shows real flies stand on active force. The model has none at rest, because no resting rate is measured for the trochanter-depressor or coxa pools.

**DECISION NEEDED (Ben): how to fill the resting support drive.**
- (a) **Leave it unfilled.** The fly lies down until a resting rate is recorded. This is honest, but every embodied run starts from a collapsed body.
- (b) **Fit one shared resting drive to the support pools** against the standing height (Wang 0.5 mm head; Pratt 1.04 mm).
  - The fall after silencing is held out as the test: onset 40-300 ms, about 1.3 mm/s. That curve is set by the muscle force decay (τ ≈ 100 ms), not by the height, so it can falsify the fit.
  - Labelled fitted, not measured. One number for all pools.
  - This is a behavioural fit, which the Director's "no tuning toward standing" currently forbids.
- (c) **Fill it through the load reflex.** Correct the load-sensor assignment first (rm has 0 load afferents; this is B's next item). Then see whether the connectome's own campaniform-to-motor-neuron paths carry support.
  - No fitting is involved. The paths found are sparse, so (c) may well fail. If it fails, that is informative.
- Recommendation: (c) now, because it is next in B anyway, then (b) only if (c) fails and Ben approves it, with the fall time course as the held-out check.

### Pre-registration: leg sensors by each cell's own entry nerve (`sense:mechano|assign_by_nerve` = 2) (18:28)
- **Why.** Option 1 decides by the type's census nerve. That misses combined type names: 23 wing- and haltere-nerve campaniforms (e.g. "SNpp29,SNpp63", "SApp06,SApp15") stayed in the leg load channel, and 29 notum- and wing-nerve bristles stayed in leg contact. It also keeps the dominant-neuropil leg. That agrees with the cell's own nerve for 98.7% of leg afferents but for only 2 of the 12 true leg campaniforms (SNpp53), which project to both sides and to all three segments.
- **Option 2.** It is anatomy, not a fit.
  - The cell's own male-cns entry nerve and root side (measured) give its leg.
  - A cell whose own nerve is a non-leg nerve is not a leg sensor. The exception is the prothoracic nerves DProN, VProN and ProAN, where the front-leg hair plates enter; the type decides there, as under option 1.
  - Combined type names are split into their parts.
  - Result (seed 0): load sensors are 2 per leg (12 SNpp53, plus 1 with no recorded nerve). Wing strain grows from 211 to 237 cells and haltere strain from 288 to 408.
- **Adoption test.** Identical to m9w's (17:35): `closed_loop_check.py`, force per spike 10, wing roles 1, seeds 12-19, plus `assign_by_nerve` 2.
  - Pass: 0 spikes/ms in the last 100 ms of silence on all 8 seeds, no MuJoCo warnings, no NaN.
  - Sugar to MN9 is brain-only and unaffected.
  - Pass gives m9n = m9w with option 2 as the working profile, and m9w is kept. A failure is recorded with the failing seed and its spiking classes.
- **Result (18:46): pass.** Seeds 12-19 all show 0 spikes/ms in the last 100 ms, no MuJoCo warnings and no NaN. Final thorax height is 0.535-0.55 mm (`runs/s12/gates/cl_n2_s*.json`). m9n is the working profile; m9w is kept.

### Pre-registration: mid/hind leg muscles by measured segment size (`muscle:leg|midhind_source` = 1) and the TTM torque from fibre data (18:38)
- **Why.** Every mid- and hind-leg muscle was a copy of FlyMimic's front leg (guessed). FlyMimic reconstructed mid/hind muscle geometry from micro-CT but fitted no forces, because only one dataset existed for those legs (arXiv 2509.06426, Suppl. A.1; agent report `docs/research/s12_leg_muscle_anatomy.md`). The Director asked for a labelled derivation instead of a copy.
- **Option 1** (`scripts/build_midhind_muscles.py`; F-MUSCLE-MH-1). Each front-leg FlyMimic member is scaled by the measured size of the segment that houses it, on the flybody mesh. Force scales with cross-section; moment arm and optimal length scale with the joint width. Thoracic muscles scale with the coxal opening. Labelled inferred, with the assumptions stated in the script and the copy kept as the lower sensitivity bound.
- **TTM peak torque 90 µN·mm** (inferred; 5-95% 53-134), replacing the guessed 100. Derivation: 27 fibres (Jaramillo 2009, 26-28) × 71.2 × 40.7 µm (Jarvis 2021) × 34.7 mN/mm² (Jarvis 2021) = 2.7 mN, times the mid-leg trochanter-extensor arm 0.033 mm (FlyMimic front arm × measured mid/front coxa width).
- **Adoption test.** Same as m9w and m9n: `closed_loop_check.py`, force per spike 10, wing roles 1, `assign_by_nerve` 2 (1 if m9n fails), seeds 12-19, plus both values.
  - Pass: 0 spikes/ms in the last 100 ms on all 8 seeds, no MuJoCo warnings, no NaN.
  - Pass gives m9m = m9n with both values as the working profile; m9n is kept.
  - Standing height is reported, not a criterion: at rest only the slow tibia flexors fire (F-STAND-3), so the muscles are not expected to lift the fly.
- **Result (19:07): pass.** All 8 seeds (`runs/s12/gates/cl_mh_s12..19.json`) show 0 spikes/ms in the last 100 ms, no MuJoCo warnings and no NaN. Whole brain 0.24-0.26 Hz, motor 2.01-2.04 Hz, thorax 0.537-0.551 mm. m9m is the working profile; m9n is kept.

### Pre-registration: leg damping from the measured stiffness (`joint:leg|damping_source` = 1, τ 0.05 s) and TTMn out of the Hill pool (`jump:ttm|exclude_from_hill` = 1) (18:53)
- **Why damping.** flybody's leg damping (1 µN·mm·s/rad, femur-tibia 0.4) is guessed. Against the measured springs it gives a relaxation time c/k of about 1.2 s.
  - Wang et al. 2025 (read) report no damping value. Their motor-silenced flies reach the passive posture about 350 ms after light-on, and their own model explains that with active-force decay (τ ≈ 100 ms). A passive relaxation time longer than about 0.1 s would add visibly to it. So c/k ≲ 0.1 s (inferred bound).
  - Option 1 sets each leg joint's damping to τ × its own measured stiffness (diagonal of J^T K J), with τ 0.05 s (inferred; FlyMimic's choice, inside the bound). The tarsal chain is unchanged. Test: `tests/test_leg_damping.py`.
- **Measured before registration** (seed 12, m9w, 1.5 s; `runs/s12/standing/standing_damp_*_s12.*`, viewed):

  | run | 90% of drop | 0-50 ms rate | end height | legs carry |
  |---|---|---|---|---|
  | dead, flybody damping | 410 ms | 5.0 mm/s | 0.544 mm | 2.8 µN |
  | dead, option 1 | 50 ms | 13.7 mm/s | 0.565 mm | 4.5 µN |
  | live, option 1 | 60 ms | 13.7 mm/s | 0.555 mm | 3.9 µN |

  - The trunk touches the floor at 20 ms instead of 50 ms, and the passive fly rolls.
  - Damping does not change where the fly comes to rest, only how fast it gets there.
  - The old slow collapse came from viscous creep in a damping value the data rule out; it was not physiology. The real silenced fly's slow fall (about 1.3 mm/s) needs active force (F-STAND-3), which the model lacks.
- **Why TTMn.** With the B15 TTM hook on, TTMn_L/R also sit in the mid CTr extensor Hill pool, with a 4-5% weight share (`scripts/probes/ttm_double_count.py`). The TTM is therefore counted twice, and the pool's activation is diluted at rest. Option 1 removes them from the pool. Test: `tests/test_ttm_exclusion.py`.
- **Adoption test.** Same as m9w, m9n and m9m: `closed_loop_check.py`, seeds 12-19, with m9m's values (m9n's if m9m fails) plus both switches.
  - Pass: 0 spikes/ms in the last 100 ms on all 8 seeds, no MuJoCo warnings, no NaN.
  - Pass gives m9d = that profile + both switches as working; the previous profile is kept.
  - Standing is reported, not a criterion. Walking dynamics change with damping (F-BODY-1: 10 Hz transfer). The next walking measurement reads them on m9d, not tuned.
- **Result (19:13): pass.** All 8 seeds (12-19) give 0 spikes/ms in the last 100 ms, no MuJoCo warnings, no NaN (`runs/s12/gates/cl_md_s*.json`). m9d is the working profile; m9m is kept.
  - Thorax ends at 0.508-0.560 mm (m9m: 0.537-0.551). Motor 2.03-2.05 Hz (m9m 2.01-2.04).
  - Not a criterion, but unexplained: whole-brain rate excluding ORNs rose from 0.067-0.086 Hz (m9m) to 0.140-0.143 Hz on 7 of 8 seeds (seed 15: 0.052). Spikes in the silent window fell (seed 13: DN 37 to 0, AN 19 to 0, central_other 91 to 6, optic_columnar 67 to 30) while AL local neurons and PNs rose (11 to 23, 1 to 11). The gate does not record per-class rates over the run, so which population carries the extra ~0.06 Hz is not known. Open item: per-class rates, m9m vs m9d, one seed.

### Blade-element wing behind `aero:wing|model` (19:08); pre-registered test with measured kinematics
- **Why.** F-FLIGHT-3: the fitted Kutta number (3.1) makes hover lift match weight at one condition. Against the robofly it gives 1.72× the lift at every angle and a flat drag of 1.0, where the robofly measures 0.39-3.46. One fitted number was standing in for both aerodynamics and kinematics errors.
- **Option 1.** A blade-element quasi-steady wing: robofly translational coefficients (measured) and rotational force from Sane & Dickinson 2002, with C_rot from the model's pitch-axis position (derived). No fitted number. It is read only with `aero:wing|membrane_only` 1, and no current profile sets that. So the working closed loop is unchanged, and the switch matters only for flight probes and a future flight profile.
- **Measured so far.** Guessed hover kinematics give 0.72 W imposed and 0.55 W PD-tracked, against 0.99 W and 0.89 W with the fitted Kutta number.
- **Pre-registered held-out test.** Impose measured Drosophila hover kinematics (source search running; `runs/s12/flight/kinematics_lit.md`) with no change to the aero model.
  - Pass: mean lift within 0.8-1.2 of weight, with imposed kinematics. The band covers the robofly-based quasi-steady model's known shortfall without wake capture, and the unchecked wing size.
  - Pass makes option 1 the B12 default for flight profiles and retires `kutta_lift` to a legacy fixture.
  - Fail is recorded as the mechanism (wing size, missing wake capture or added mass, stroke-plane geometry), with no coefficient changed.
- **Kinematics fixed before the run (19:22).** Source found by the agent (`runs/s12/flight/kinematics_lit.md`): Muijres, Elzinga, Melis & Dickinson 2014 (Science 344:172), Table S1, Fourier fits to 1603 steady free-flight wingbeats. These are D. hydei (wing 2.99 mm, 1.8 mg), not D. melanogaster. No melanogaster phase table was found; Fry et al. 2005 give only scalar melanogaster values (218 ± 7 Hz, amplitude 140 ± 10°, wing length 2.39 ± 0.08 mm; measured).
  - Primary run: Muijres angle time courses unchanged (stroke peak-to-peak 131.6°, inside Fry's melanogaster 140 ± 10°), at the melanogaster frequency of 218 Hz. The thorax is held at Muijres's body pitch of 47.6° (measured). The stroke plane is tilted 47.5° nose-up from the body axis, so it is horizontal.
  - Conventions (inferred, stated here because the main-text figure was not accessible):
    - α = 0 means the chord is normal to the stroke plane, leading edge up. Muijres's α crosses 0 at both stroke reversals, so it is not measured from the plane.
    - The leading edge must lead in both half-strokes. That forces φ positive = posterior, and α positive = leading edge toward anterior.
    - So τ = 0 is the dorsal reversal, and the downstroke (posterior to anterior) takes 54% of the cycle. Fry 2005 measured 53.8%.
    - Deviation is positive toward the stroke-plane normal (Fry's "upward positive").
    - Mean vertical force in a horizontal stroke plane is nearly unchanged by a front/back mirror. So the φ-sign inference matters little to the test; the α reference matters a lot.
  - Hinge angles come from `flight.wing_pose_ik` per phase point (span and leading-edge vectors in the thorax frame). The pose-fit error is reported, and a worst-axis error above 5° voids the run.
  - Expected sensitivities, reported but not used to pass or fail:
    - lift ∝ f², so ±7 Hz is ±6%;
    - lift ∝ Φ², so Fry's 140° would give about +13%;
    - the model wing is 2.65 mm from hinge to tip against 2.39 ± 0.08 mm (Fry, free flight). At fixed kinematics, lift scales roughly as R⁴.
- **Result (19:35): FAIL, high.** Mean vertical force is 1.53 W (translational lift 1.35, rotational 0.11, drag 0.07); pose-fit error 0.0°.
  - The first run gave 0.29 W because the rotational term used the pitch-joint rate, which is not the wing's rotation in the stroke frame for this model's hinge axes (F-WING-3). That is a correctness fix, with no coefficient touched (F-FLIGHT-3), and both numbers are reported.
  - The excess matches the wing-size sensitivity listed above: (2.39/2.65)⁴ × 1.53 = 1.01.
  - Per this pre-registration: nothing is refitted, option 1 is not made the default, and `kutta_lift` stays.
  - Next: check the model wing's size against measured female morphometrics. If oversized, a measured-size membrane goes behind a switch, and this same test is rerun unchanged.

### F-WING-3 fix behind switches (19:44); no profile change
- **Why.** The s10 joint-space generator and `WING_RANGE_DEG` swing each wing over the dorsum (F-WING-3). Every generator-driven flight number so far used crossed wings.
- **Built.**
  - `flight:wings|kinematics` 1: the measured Muijres 2014 beat, given in stroke-frame angles and mapped to the hinges (`flight.StrokeFrameKinematics`), with B11 steering applied to stroke-frame angles.
  - `joint:wing|range_by_function` 2: the measured hinge envelope plus the folded pose, with a 20° margin (guessed).
  - Both are off by default. No walking profile reads them, because the generator is off in the walking template. So the working closed loop (m9d) is unchanged and no gate is needed.
- **Evidence.** Unit and organism tests in `tests/test_flight.py`, and the contact sheet `docs/media/s12_wing_beat_views.png`, viewed.
- **Next.** A flight profile would combine `generator` 1, `kinematics` 1, ranges 2 and the blade-element wing. That waits on the wing-size check (F-FLIGHT-3), because the pre-registered lift test failed high.

### Pre-registration: measured-size wing for the 19:08 hover test (19:58)
- **Why.** The 19:35 result failed high (1.53 W), with wing size as the likely mechanism. Size check (`runs/s12/flight/wing_size_lit.md`, `mass_wing_lit.md`; agent extraction, not all re-read):
  - Model geometry: the wing hinge sits on the thorax surface (anchor y 0.432 mm, surface 0.439 mm), so hinge-to-tip is comparable with a measured wing length. The membrane reaches 2.65 mm (derived, `runs/s12/diag/wing_root_geometry.py`).
  - Lehmann & Dickinson 1997: 27 female Canton-S, R = 2.47 mm (measured; the paper's SD of 0.71 mm conflicts with its own 4.6% area SD, probably a misprint). The same cohort weighed 1.05 ± 0.13 mg (1998).
  - Fry 2005 (page re-read by me): R = 2.39 ± 0.08 mm free flight, n = 6, sex not stated; mass estimated, not weighed.
  - flybody's 0.983 mg is measured: 52 weighed females, by body part (bioRxiv Methods). That is a different population from the one scanned fly.
  - So the model pairs a measured population mass with one fly's wing that is 7-11% longer than every measured female mean. Its R⁴/m is about 1.4× both cohorts. The wing is long for the mass, not the mass low for the wing.
- **Switch.** `aero:wing|size_source`:
  - 0: scanned wing (2.65 mm).
  - 1: the blade-element strips scaled isometrically about the hinge to R = 2.47 mm (Lehmann & Dickinson 1997, female, measured).
  - Mesh, inertia and MuJoCo added mass are unchanged. The validity statement is aero only.
  - Chosen before the run because those flies are female and weighed. Fry's 2.39 mm is reported as a sensitivity, not used to pass or fail.
- **Test.** Identical to 19:08/19:35: Muijres beat, 218 Hz, body pitch 47.6°, stroke-frame rotational rate, pass band 0.8-1.2 W.
  - Prediction from R⁴ scaling: 1.53 × (2.47/2.651)⁴ = 1.15 W (derived). Fry's 2.39 mm would give 1.01 W.
  - This is a consistency check of the scaling inside the full blade-element model, not held-out validation: the wing length was chosen after seeing the 1.53 W.
  - Pass: `size_source` 1 joins the flight-profile candidate set with the blade-element wing. Fail: the R⁴ attribution is wrong, and the mechanism is written up. No coefficient changes either way.
- **Result (20:04): PASS.** With `size_source` 1 (R = 2.47 mm), the mean vertical force is 1.153 W (translational lift 1.016, drag 0.056, rotational 0.082; `runs/s12/flight/hover_blade_trace_muijres2014_R2.47.json`, trace PNG viewed). Prediction 1.15 W.
  - Scan-wing rerun with the same code: 1.528 W (19:35 gave 1.535).
  - Sensitivity, Fry's 2.39 mm: 1.011 W.
  - So R⁴ scaling holds inside the full blade-element model. `size_source` 1 joins the flight-profile candidate set with `aero:wing|model` 1. No profile changes, no coefficient changes.
  - Still not held out: the size was chosen after seeing 1.53 W. The next discriminating test is a second measured condition (a different stroke amplitude or forward speed with measured force), with no further changes.

### Pre-registration: flight force across 13 measured conditions, against the robotic fly (20:31)
- **Why.** B asks for flight coefficients beyond one condition. The literature agent found no accessible measured force-vs-amplitude regression: Lehmann & Dickinson 1997 and 1998 are paywalled, with abstracts only (`runs/s12/flight/force_vs_amplitude_lit.md`). But Muijres et al. 2014's Database S1 (already downloaded, open) holds `robotForcesTorques.ForceModulations`:
  - 13 wingbeats built from the measured kinematic change per unit force (SM eq. S3; flies pooled, 719 wingbeats), at F/mg 0.85 to 1.76;
  - their frequencies, 182.4 to 220.0 Hz (SM: 188.7 + 41.5 (F/mg − 1); the robot time bases agree to 0.1 Hz);
  - the forces a dynamically scaled robotic wing measured with each beat, converted to fly scale and normalized by weight (measured). Steady level: 1.02 W.
  - The robot's steady beat equals Table S1 (the beat already imposed) with stroke and rotation signs flipped and deviation unchanged (checked: correlation −1.000, +1.000, −1.000; deviation RMS difference 0.03°). That sign map is applied unchanged to all 13 levels.
  - Species D. hydei. Database settings: wing length 2.99 mm, mean chord 0.9468 mm, mass 1.8 mg.
- **Test.** For each level, impose the beat on both wings with the thorax at 47.6° pitch (stroke plane horizontal, as the robot's axes), using the blade-element wing (`aero:wing|model` 1) with no coefficient changed. Read the mean vertical force of the wings alone (lift + drag + rotational; the robot has no body) over the last 2 of 6 beats.
- **Primary (pass/fail): the ratio.** The model's force at each level divided by its force at the steady level, against the robot's same ratio (robot: 0.91 at the lowest level, 1.99 at the highest). Size cancels. Pass if the two ratios differ by at most 0.10 at every level.
- **Secondary (pass/fail): the steady level at hydei size.** Strips scaled to R = 2.99 mm, chords scaled so the planform is R × c̄ = 2.83 mm² (both from the database; the flybody ellipse shape kept). Normalized by 1.8 mg × g. Pass if within ±20% of the robot's 1.02 W.
  - Prediction from the 20:04 result by scaling (span⁴, chord, f²; rotational term with chord²): 0.86 W, 0.85 of the robot's. This part is a scaling consistency check, not new information, because the steady beat is the one already used.
- **Reported, not pass/fail:**
  - the free-flying flies' own F/mg at each level (0.85-1.76; the robot overshoots it at the top, 1.99);
  - the robot's single-angle decompositions (stroke only, rotation only, deviation only, frequency only).
- **Either way.** No coefficient, kinematics or size changes after the run. A pass makes the blade-element wing the measured-force candidate for flight across force levels. A fail is written up with the levels and terms where it departs.

### Pre-registration: MuJoCo noslip off (`contact:floor|noslip_iterations` 0) as candidate m9s (20:33)
- **Why.** F-DAMP-2: flybody's arena runs 3 noslip iterations, and at the 0.1 ms step these do not converge on m9d's lightly damped legs. Resting leg speed then changes non-monotonically with the step, by up to 4× (seeds 12-14 agree, so the step sets it, not chaos). With noslip off the closed loop converges (seed 13: 13.6, 12.0, 12.3 deg/s at k = 1, 2, 4); with 20 iterations it nearly does (15.6, 14.5). flygym's GPU path (MJWarp) has no noslip and sets it to 0, so the many-flies runs (task 3) need the CPU reference at 0 to compare like with like.
- **Choice of 0 over 20.** Both converge; 0 matches the GPU path and costs nothing. Without noslip, MuJoCo's soft contacts allow some creep under shear; that is reported below, not assumed small.
- **Switch.** `contact:floor|noslip_iterations` (B6), registered by `passive.register_noslip` in the organism, `dead_fly.py` and `deadfly_decay.py`. Neutral 3 keeps every earlier profile unchanged. Test: `tests/test_contact_solver.py`.
- **Adoption test.** As every s12 adoption: `closed_loop_check.py`, seeds 12-19, with m9d's values plus the switch.
  - Pass: 0 spikes/ms in the last 100 ms on all 8 seeds, no MuJoCo warnings, no NaN. Pass gives m9s = m9d + noslip 0 as working; m9d is kept.
  - Also required (pass/fail): the template dead-fly test (`dead_fly.py --template`) keeps its verdicts with the switch on, since dead-fly results so far ran at 3.
  - Reported, not criteria: resting step convergence on two more seeds (k = 1, 2), the head-contact share, thorax height, and foot creep (horizontal drift of the six tarsal tips over 1 s of rest).
- **Result (20:36): primary FAIL at the top two levels; secondary PASS.** (`runs/s12/flight/robot/`, `summary.json`; plot `docs/media/s12_robot_force_levels.png`, viewed.)
  - Ratio to the steady level, model against robot: within 0.03 up to F/mg 1.45 (levels 0-8), −0.05 at 1.53, −0.09 at 1.60, **−0.11 at 1.68 and −0.17 at 1.76**. Fails the 0.10 rule at levels 11 and 12.
  - Steady level at hydei size: 0.865 W (prediction 0.86), 0.85 of the robot's 1.02. Inside ±20%: pass.
  - Where it departs (diagnostic, after the result): the model's frequency response is f² exactly (top-level angles at the steady frequency give 1.340×, f² arithmetic 1.339×). Angle changes alone agree with the robot: the robot's all-changes/frequency-only quotient at the top is 1.327, the model's angle-only effect 1.340. The whole gap is in the robot's frequency-only record, which rises 1.50× where f² gives 1.36× (an exponent of about 2.65). A quasi-steady wing at fixed angles cannot do that, and the SM does not say how the robot runs were scaled in frequency. Not resolved.
  - Against the free-flying flies' own F/mg (reported, not pass/fail): the model's ratio rises with slope 1.04 (1.82 at the top against the flies' 1.76); the robot's with 1.18 (1.99).
  - Per this pre-registration: nothing changes. The blade-element wing is not declared the measured-force candidate across all force levels; it is the candidate up to F/mg ≈ 1.5, with the top of the range open on the robot's frequency scaling.

### Pre-registration: roll torque across 13 measured roll conditions, against the robotic fly (20:43)
- **Why.** The force test (20:31, result 20:36) checked symmetric changes. Steering needs left-right differences to give the right torque. Muijres 2014 Database S1 `RollModulations` gives 13 robotic-wing beats with per-side kinematics built from the flies' measured kinematic change per unit roll acceleration (−0.72 to 3.61 deg per beat², steady frequency), and the robot's mean forces and torques for all changes and for stroke-only, rotation-only and deviation-only changes.
- **Conditions, as the force test.** Blade-element wing (`aero:wing|model` 1, stroke-frame rotational rate), hydei wing length 2.99 mm and planform 2.831 mm², weight 1.8 mg, body pitch 47.6°, kinematics through `flight.wing_pose_ik` with the same angle map (stroke and rotation negated; checked equal to ForceModulations at the steady beat). Tools: `build_measured_kinematics.py --robot-roll k [--roll-part]`, `hover_blade_trace.py` (new: mean wing force and torque about the hinge midpoint in the robot frame, x forward and horizontal at the hover attitude, y right, z down). Last 2 of 6 beats.
- **Normalization (inferred).** The SM does not state the robot's torque normalization; m g l with l the wing length (2.99 mm) is assumed. A body-length normalization (3.138 mm) would move the reference by 5%.
- **Primary.** Model roll torque Mx/(m g l), multiplied by the robot's steady vertical force over the model's (this removes the known 0.85 steady deficit, 20:36), is within ±20% of the robot's at each level where the robot's |Mx| ≥ 0.03 (levels 6-12), with the same sign at all 12 non-steady levels.
- **Secondary (normalization-free).** At the top level, the stroke-only, rotation-only and deviation-only torques as shares of the all-changes torque are each within ±0.15 of the robot's (0.41, 0.36, 0.11).
- **Reported, not criteria.** The uncorrected Mx (predicted about 0.85 of the robot's), the vertical force ratio across levels against the robot's, and yaw coupling (robot Mz 0.044 at the top).
- **Prediction.** Primary ratio 0.9-1.1 at every level (pass); secondary shares within 0.1 (pass).
- **What follows.** Nothing in the model changes on the result. A pass makes the blade-element wing the roll-torque candidate for steering at measured kinematics; a fail points at the spanwise centre of pressure (planform) or the asymmetric rotation and deviation terms.
- **Result (20:49): primary FAIL; secondary FAIL.** (`runs/s12/flight/roll/`, `summary.json`; plot `docs/media/s12_robot_roll_torque.png`, viewed.)
  - Normalization: m g l is now sourced, not inferred. Dickinson & Muijres 2016 (Phil Trans B 371:20150388, PMC4992712, Fig. 2 caption, on the same robot data): "torques are normalized by the product of body mass and wing length (mg l)".
  - Magnitude: the force-corrected model roll torque is 0.42-0.52 of the robot's at levels 6-12; uncorrected it is 0.36-0.47. It fails the ±20% rule at every level.
  - Sign: opposite to the robot's at every level. In the frame as registered, the model's sign is the physical one: the wing with the larger stroke (right, 150° against 146°) makes more lift, which gives negative Mx with x forward, y right, z down. The robot's stroke-only torque is positive for the same change. Its yaw torque is also opposite, while its side and vertical forces agree in sign. So the robot's torque sign convention probably differs (for example, reported as the reaction on the sensor). The SM does not say, and the main text is paywalled. The sign is unresolved and not counted against the wing, but the magnitude fails either way.
  - Shares at the top level (model against robot): stroke-only 0.67 against 0.41, rotation-only 0.45 against 0.36, deviation-only 0.32 against 0.11. The model's parts sum to 1.44 of its all-changes torque, the robot's to 0.89. Absolute component torques, model over robot: stroke 0.59, rotation 0.44, deviation 1.01.
  - Symmetric part (reported): vertical force over steady, model 1.232 against robot 1.260 at the top; the stroke-only force rise agrees (1.224 against 1.242).
  - Where it departs (diagnostic, after the result): the deficit is in the left-right difference, not in the summed lift.
    - A quasi-steady estimate from the stroke-amplitude difference alone (lift ∝ amplitude², 2.8% amplitude difference, arm about 2.2 mm) gives about 0.026 m g l. That is the model's 0.023, against the robot's 0.039.
    - The model's hinges are 0.43 mm off the midline, against 0.71 mm in the hydei body model. That shortens the arm by about 11%, not a factor of 2.
    - Unsteady effects the quasi-steady wing lacks (wake capture, added mass, timing-dependent rotational circulation) are the leading candidate, mainly through the rotation-only component (0.44). Not tested.
  - Per this pre-registration: nothing changes. The blade-element wing is not the roll-torque candidate. Steering torques from it are about half the robot's at the same kinematics.

### Result: m9s gate (20:33 pre-registration) — PASS; m9s is the working profile (20:49)
- **Gate** (`closed_loop_check.py`, seeds 12-19, m9d values plus `contact:floor|noslip_iterations` 0, confirmed in each run's overrides): 0 spikes/ms in the last 100 ms on all 8 seeds, 0 MuJoCo warnings, no NaN (`runs/s12/gates/cl_ms_s*.json`, backhouse).
- **Template dead fly** with the switch on: every verdict unchanged (valid run, collapse, range limits, energy, non-leg at rest, leg rest posture all pass). Thorax 1.32 → 0.549 mm, the same as at 3 iterations; end energy 5.59 against 5.63 (`runs/s12/m9s/deadfly_tpl_ns{0,3}`).
- **Reported:**
  - Step convergence (closed loop, RMS leg speed, k = 1 then 2): seed 12, 12.9 then 12.2 deg/s; seed 14, 12.8 then 12.6. At 3 iterations: 17.0 then 24.5, and 16.6 then 25.8.
  - Head contact 95-97% of samples, 2.43-2.52 µN. That is unchanged: the head still lies on the floor (F-DAMP-2).
  - Thorax 0.554-0.557 mm, still collapsed (F-STAND-3).
  - Foot motion (horizontal drift of the six tarsal tips from 200 ms to 1 s, summed): 0.32 and 0.37 mm at 0 iterations, against 0.75 and 0.84 mm at 3. No tip stayed on the floor throughout, so this is foot motion of a collapsed fly, not slip under load.
- **Adopted:** `profiles.M9S` = m9d + noslip 0; `WORKING_PROFILE` = m9s. m9d is kept. Resting runs now converge with the step and match the GPU path's contact.

### Pre-registration: non-leg torque per spike from the leg motor-unit anchor (21:12)
- **Why.** Every head, proboscis, antenna, abdomen, wing and haltere motor neuron uses the shared `motor_unit:all|force_per_spike` 10 µN·mm (guessed). The census (`scripts/probes/nonleg_motor_census.py`, seed 12, m9s gate values, `runs/s12/nonleg/census_s12.json`) has the head yaw and pitch, rostrum and both antennae within 1° of a joint limit 97-100% of the time from 200 to 600 ms, and the left wing yawed out. The literature search (`docs/research/s12_nonleg_muscle_sources.md`) found no measured force, cross-section or arm for any non-leg fly muscle.
- **Change, behind a switch.** `motor_unit:nonleg|torque_source` 1 reads `data/params/nonleg_motor_forces.csv` (`scripts/build_nonleg_forces.py`): torque per spike = 1.035 µN (tibia-flexor pool-mean twitch, derived from Azevedo 2020's measured classes) × length of the moved part on the flybody mesh (derived). Label inferred. Values (µN·mm): head 0.49, rostrum 0.40, haustellum 0.25, labrum 0.21, antenna 0.44, abdomen 0.43-0.77, wing 2.73, haltere 0.31. Bounds are the measured unit range 0.05-10 µN times the same lever. The old 10 µN·mm lies above the upper bound for the head, proboscis, antennae and halteres.
- **Conditions.** m9s gate values plus the switch. Nothing else changes (neck and antenna drive signs stay +1 on both sides, guessed; ±30 µN·mm actuator clip and flybody non-leg stiffness unchanged).
- **Primary.** (1) Gate (`closed_loop_check.py`, seeds 12-19): 0 spikes/ms in the last 100 ms, no MuJoCo warnings, no NaN, on all 8 seeds. (2) Census seed 12: head yaw, head pitch, rostrum and both antennae each spend under 50% of 200-600 ms within 1° of a joint limit.
- **Secondary.** Contact sheet (Mac, seed 12, 300 and 600 ms): head, proboscis and antennae visibly off their stops and both wings folded back, viewed.
- **Prediction (linear steady state, rates as in the baseline census).** Mean deflection = torque per spike × summed rate × 30 ms ÷ stiffness: head yaw about 7°, head pitch about 16° (limit 25°), rostrum about 12° (limit 40°), antennae about 6° (limit 20°), left wing yaw about 12°. Primary pass on both parts. Rates may change with the posture, so these are rough.
- **What follows.** A pass makes m9t = m9s + the switch the working profile. A fail on (2) with rates unchanged points at the drive mapping (one-sided neck and antenna signs) or the flybody stiffness, and is written up rather than tuned.

- **Result (21:21): primary PASS on both parts; secondary FAIL on the wings.** (`runs/s12/gates/cl_nl_s*.json`, backhouse; `runs/s12/nonleg/census_s12_nl1.json`; sheets `runs/s12/nonleg/sheet_base.png` and `sheet_nl1.png`, viewed.)
  - Gate, seeds 12-19: 0 spikes/ms in the last 100 ms, 0 MuJoCo warnings, no NaN on all 8. Brain excluding ORNs 0.151-0.154 Hz (m9s 0.137-0.153), motor 2.03-2.06 Hz (unchanged), thorax 0.562-0.564 mm (m9s 0.554-0.560).
  - Census, seed 12, 200-600 ms, share of time within 1° of a limit, m9s then switched: head yaw 1.00 → 0, head pitch 1.00 → 0, rostrum 1.00 → 0, left antenna 0.97 → 0, right antenna 1.00 → 0. Mean angles: head yaw 15.2° → −0.4°, head pitch 25.4° → 0.3°, rostrum −40.3° → −12.3°, antennae 20.1°/20.2° → 5.1°/6.3°. Mean |torque| at the head 7.7 → 0.31 µN·mm.
  - Against the prediction: rostrum (12°) and antennae (about 6°) as predicted; head yaw and pitch near 0° instead of 7° and 16°. The head pitch neurons' summed rate fell from 55 to 37.5 Hz, and yaw and pitch now sit inside the range, so contact and the posture changed the balance; the linear estimate ignored that.
  - Sheet: the head is upright and centred, the proboscis is off its stop (on the m9s sheet the head was pitched down onto the floor). **Both wings are raised in a V over the thorax at 300 ms and the left at 600 ms**, so the secondary fails. On m9s the left wing was yawed out at 300 ms.
  - Wings (reported, diagnosis after the result): the wing torque per spike fell 10 → 2.73 µN·mm, but the wing motor neurons fire about twice as often at rest (left yaw 2.5 → 5 Hz, left pitch 7.5 → 15 Hz, the right side now firing: yaw 2.5, pitch 7.5 Hz). Mean left wing yaw fell 46.7° → 20.3°, right rose 4.2° → 14.6°. Against the flybody wing stiffness of 1 µN·mm/rad (unsourced), a few spikes still move the wing tens of degrees. The derived lever (2.64 mm, the full wing) overstates the arm, because the steering muscles act on the hinge sclerites, not the blade. Not changed here; it needs its own pre-registration.
  - **Adopted per this pre-registration:** `profiles.M9T` = m9s + `motor_unit:nonleg|torque_source` 1; `WORKING_PROFILE` = m9t. m9s is kept. The wing rest is the next body item.

### Pre-registration: measured D. hydei planform in the robot force and roll comparisons (21:17)
- **Why.** Both robot comparisons (20:31, 20:43) put the flybody ellipse shape on the blade-element strips, rescaled to hydei length and area. Muijres 2014 Database S1 `wing_model.chords_L` holds the measured chord of the robot's hydei wing in 20 strips (`data/derived/muijres2014_wing_chords.csv`, `scripts/build_hydei_planform.py`). Its second and third moments are r2/L 0.584 and r3/L 0.622, against the ellipse's 0.539 and 0.587, so the measured shape carries more area outboard.
- **Change.** `BladeElementWing(planform="hydei")` (`hover_blade_trace.py --planform hydei`): measured chord/L against r/L on the same strips and tip radius; strip r2/R 0.581, r3/R 0.620 at 2.99 mm. Area still rescaled to 2.831 mm², so only the shape changes. Kinematics files, coefficients, weight, body pitch and scoring scripts are reused unchanged.
- **Criteria, as registered at 20:31 and 20:43.** Force: ratio to the steady level within 0.10 of the robot's at every level (primary); steady level within ±20% of 1.02 W (secondary). Roll: force-corrected Mx/(m g l) within ±20% of the robot's at levels 6-12 with the same sign at all non-steady levels (primary); top-level stroke, rotation and deviation shares within ±0.15 (secondary).
- **Prediction.** Steady force rises by about (0.581/0.539)² = 1.16: 0.865 → about 1.00 W, 0.98 of the robot's (secondary pass, now close). Force-ratio primary unchanged: fails at levels 11-12 (the frequency term). Roll: the lever for a lift difference, r3³/r2², moves by only 1% (0.698 → 0.706), so the force-corrected roll torque stays about 0.45 of the robot's with the sign unchanged (primary FAIL), and the shares stay as they were (secondary FAIL).
- **What follows.** The planform is a measurement, so a closer steady force is no reason to stop using it in robot comparisons; it does not enter the organism (the scanned wing stays). If the roll gap stays, the planform is ruled out as its cause, and the unsteady terms remain the lead.
- **Result (21:21): force secondary PASS (now 0.99 of the robot's); force primary FAIL at levels 11-12; roll primary and secondary FAIL. As predicted.** (`runs/s12/flight/planform/`, `summary.json`, backhouse; trace plots viewed.)
  - Steady level: 1.011 W against the robot's 1.020 (0.99; ellipse 0.865, 0.85). Prediction 1.00.
  - Ratio to steady, model against robot: within 0.04 up to level 8; −0.06 at 9, −0.10 at 10, **−0.12 at 11, −0.17 at 12** (ellipse −0.11, −0.17). Fails at 11 and 12 as before: the shape scales all levels alike, so the frequency term is untouched.
  - Roll, force-corrected Mx over the robot's at levels 6-12: 0.42-0.54 (ellipse 0.42-0.52), sign opposite at every non-steady level. Shares at the top level (stroke, rotation, deviation): 0.67, 0.48, 0.34 against the robot's 0.41, 0.36, 0.11 (ellipse 0.67, 0.45, 0.32).
  - So the spanwise distribution is ruled out as the cause of the roll gap: the measured shape moves it by 1-3%. The unsteady terms (wake capture, added mass, rotational circulation timing) remain the lead, mainly through the rotation component.
  - Per this pre-registration: the hydei planform is used in robot comparisons from now on (`--planform hydei`); it does not enter the organism.

### Pre-registration: measured wing hinge stiffness (`joint:wing|stiffness_source` 1) as candidate m9u (21:44)
- **Why.** On m9t both wings rise in a V at rest (F-NONLEG-1, 21:21). The plain body under m9t wing settings (`scripts/probes/wing_spike_response.py`, `runs/s12/wing/spike_m9t.json`) shows one wing spike (2.73 µN·mm, 30 ms decay) swinging the folded left wing to +40° yaw, −41° pitch or −28° roll. It peaks at 38 ms, and 17° is still left at 100 ms. The hinge spring is flybody's 1 µN·mm/rad, unsourced.
- **Source** (`docs/research/s12_wing_hinge_sources.md`). Bergou et al. 2010 (PRL 104:148101) fitted a wing-pitch torsional stiffness of 91 ± 9 pN·m/deg (5.21 µN·mm/rad) to measured D. melanogaster free-flight kinematics. No Drosophila value exists for the yaw or roll axes or for the folded hinge, so those take the same value (inferred transfer).
- **Change, behind a switch.** `joint:wing|stiffness_source` 1 (`passive.register_wings`, `passive.WING_STIFFNESS_BERGOU`) sets 5.214 µN·mm/rad on all six wing hinges. Neutral 0 keeps flybody's 1. Nothing else changes: flybody damping 0.05, the wing torque per spike, the s10 wing ranges and the wing drive mapping all stay.
- **Primary.**
  1. Gate (`closed_loop_check.py`, seeds 12-19, m9t gate values plus the switch): 0 spikes/ms in the last 100 ms, no MuJoCo warnings and no NaN on all 8 seeds.
  2. Census seed 12, 200-600 ms (`nonleg_motor_census.py`): the mean yaw and pitch angle of each wing lies within ±10° of the fold. On m9t: left yaw 20.3°, left pitch −18.5°, right yaw 14.6°, right pitch −13.8°.
- **Secondary.**
  - Contact sheet, seed 12, 300 and 600 ms (`--sheet`): both wings folded back over the abdomen, viewed.
  - Head, rostrum and antennae still under 50% of the time within 1° of a limit.
- **Prediction.**
  - Body-only, at 5.214 (`runs/s12/wing/spike_k5p2.json`): one spike peaks at +15° yaw, −16° pitch and −17° roll at 16 ms, with 1-6° left at 100 ms.
  - Closed loop, scaling m9t's excursion from rest by 1/5.2 at unchanged rates:
    - left yaw about 7°, right yaw about 6°;
    - left and right pitch about −5°;
    - so primary 2 passes, but yaw sits near the 10° bound.
  - The gate is unchanged: the network sees the wings only through the wing afferents.
- **What follows.**
  - A pass makes m9u = m9t + the switch the working profile, and the battery is rerun.
  - A fail on (2) at unchanged rates points at the resting wing motor drive (wing motor neurons firing at rest; no source says whether real ones do) or at the i1/i2 yaw mapping (+1, guessed). That fail is written up, not tuned.
  - The stiffness is a measurement either way. It stays in the record even if the wings still rise.

- **Result (21:49): primary PASS on both parts, secondary PASS.** Sources: `runs/s12/gates/cl_wk_s*.json` (backhouse); `runs/s12/wing/census_wk_s12.json`, with the m9t census rerun in the same batch, `census_m9t_s12.json`; sheets `census_wk_s12.png` and `census_m9t_s12.png`, both viewed.
  - **Gate, seeds 12-19:** 0 spikes/ms in the last 100 ms, 0 MuJoCo warnings and no NaN on all 8 seeds.
    - Brain excluding ORNs: 0.140-0.153 Hz (m9t 0.151-0.154).
    - Motor: 2.02-2.06 Hz (unchanged).
    - Thorax: 0.560-0.564 mm (unchanged).
  - **Reported, not a criterion:** spikes in the first 200 ms of the silent window rose on seeds 14, 16 and 18, to 378, 157 and 475 (m9t 62, 62, 98). They are mostly DN, AN and central cells, and all die out before the last 100 ms.
  - **Census, seed 12, 200-600 ms, mean wing angles** (m9t, then switched):

    | Wing angle | m9t | switched |
    |---|---|---|
    | left yaw | 20.3° | 2.8° |
    | left pitch | −18.5° | −2.8° |
    | right yaw | 14.6° | 2.8° |
    | right pitch | −13.8° | −2.4° |

    - All four are inside the ±10° bound.
    - Head, rostrum, antennae, abdomen and halteres spend 0% of the time within 1° of a limit, and their angles are within 4° of m9t.
  - **Against the prediction:** the angles are smaller than predicted (about 7° yaw and −5° pitch), because the prediction assumed unchanged rates. Over 200-600 ms the wing motor neurons did not fire at all; on m9t they averaged 1.25 Hz, with up to 5 Hz per actuator. The cause is examined below the result.
  - **Sheet:** both wings lie folded flat over the abdomen at 300 and 600 ms. On the m9t sheet from the same batch, they stand in a V over the thorax.
  - **Adopted per this pre-registration:** `profiles.M9U` = m9t + `joint:wing|stiffness_source` 1; `WORKING_PROFILE` = m9u. m9t is kept. Battery to rerun.
  - **Diagnostic after the result (21:54): the seed-12 silence comes from the trajectory, not from the stiffness.**
    - Spike timing on the Mac (`runs/s12/wing/wing_mn_timing_s12.json`): on m9t the wing motor neurons fire in two bursts, 8 spikes at 225-235 ms and 4 at 542-543 ms. The wing is still resting (yaw 4.8°) when the first burst starts, so the burst comes before any wing motion. With the switch they do not fire at all in 600 ms.
    - Over the 8 gate seeds the class rate is about the same: wing and haltere motor neurons 0.19 Hz on m9t, 0.16 Hz switched.
    - So the stiffness does not silence the wing motor neurons. Seed 12 simply took a different path.
    - Body-only bursts (`wing_spike_response.py --spikes`, 1.5 ms apart; `runs/s12/wing/burst*_k*.json`):

      | Burst | Hinge stiffness | Peak yaw | Peak pitch | Left at 100 ms |
      |---|---|---|---|---|
      | 4 spikes | 1 µN·mm/rad | +169° | −127° | 149° yaw, −79° pitch |
      | 4 spikes | 5.21 µN·mm/rad | +70° | −72° | 6° yaw, −5° pitch |
      | 2 spikes | 5.21 µN·mm/rad | +34° | −35° | 3-5° |

    - With the measured stiffness, a burst becomes a flick of about 50 ms rather than a wing held up. The resting angle averaged over time now depends on how often the wing motor neurons burst at rest. No source says whether real ones do (`docs/research/s12_wing_hinge_sources.md`).
    - A census on more seeds is queued behind the neck runs.

### Pre-registration: mirror-image neck motor neurons on opposite head yaw and roll signs (`motor_map:neck|mirror_sides` 1) as candidate m9v (21:50)
- **Why.** In `data/params/motor_targets.csv` every head yaw motor neuron (10 left, 10 right) and every head roll motor neuron (7 left, 8 right) maps +1, a guess. So a bilateral pair firing together turns the head one way. Yaw and roll change sign under left-right reflection; pitch does not.
- **Source** (`docs/research/s12_neck_antenna_sources.md`).
  - No accessible per-neuron direction table exists: Gorko et al. 2024 and Strausfeld 1987 are paywalled.
  - Gorko 2024 (via open commentary) shows that a neck motor neuron drives the head toward a target pose, with the direction depending on the starting angle. So any fixed sign is an approximation.
  - The change rests on bilateral symmetry alone (derived). The absolute direction of each left-side type stays guessed.
- **Change, behind a switch.** `motor_map:neck|mirror_sides` 1 (`neuromuscular._map_non_leg`, `HEAD_ODD`) gives right-side motor neurons on head yaw and roll the opposite sign. Side comes from the instance suffix, as for `{s}` targets.
  - Pitch, the antennae (already one joint per side) and everything else are unchanged.
  - Neutral 0 keeps the guessed map.
- **Primary.**
  1. Gate (`closed_loop_check.py`, seeds 12-19, m9u values plus the gate overrides and the switch): 0 spikes/ms in the last 100 ms, no MuJoCo warnings and no NaN on all 8 seeds.
  2. Census, seeds 12 and 13, 200-600 ms, against m9u in the same batch:
     - head yaw, roll and pitch each under 50% of the time within 1° of a limit;
     - the mean |torque| on head yaw and on head roll lower than m9u's on both seeds (left and right drive now cancel).
- **Secondary.** Contact sheet, seed 12: head upright and centred, wings folded, viewed.
- **Prediction.**
  - Yaw and roll torque fall by about the fraction of left-right coincident drive.
  - Head angles stay within 5° of m9u's: at rest the head already sits mid-range (yaw −1°, roll −5°, pitch 4° on seed 12).
  - The gate is unchanged.
- **What follows.**
  - A pass makes m9v = m9u + the switch the working profile.
  - A fail on (2), with head torque not falling, means the left and right neck neurons fire at different times, so the drive does not cancel. That would be reported, and the switch kept as the symmetric default only if the gate passes.
- **Result (21:58): primary 1 PASS; primary 2 PASS on limits and yaw, NOT MET as written on roll; secondary PASS. Adopted m9v, with the roll clause recorded as untested.** Sources: `runs/s12/gates/cl_nk_s12-19.json` (backhouse); `runs/s12/neck/census_{nk,m9u}_s{12,13}.json`, same batch; sheets `census_nk_s12.png` and `census_m9u_s12.png`, both viewed.
  - Gate: 0 spikes/ms in the last 100 ms, no MuJoCo warnings, no NaN, on all 8 seeds. Brain without ORNs 0.152-0.155 Hz, motor 2.02-2.06 Hz, thorax height 0.559-0.561 mm.
  - Census, 200-600 ms (m9u → m9v):

    | Seed | Yaw \|torque\| µN·mm | Roll \|torque\| | Pitch \|torque\| | Yaw ° | Roll ° | Pitch ° | Time near a limit |
    |---|---|---|---|---|---|---|---|
    | 12 | 0.329 → 0.0076 | 0 → 0 | 0.678 → 0.714 | −1.0 → −5.6 | −5.4 → −4.5 | 3.9 → 6.0 | 0% all |
    | 13 | 0.333 → 0.0079 | 0 → 0 | 0.677 → 0.781 | −0.4 → −6.1 | −5.0 → −4.3 | 4.5 → 6.4 | 0% all |

  - Yaw torque falls about 40-fold on both seeds: left and right yaw motor neurons fire together (25 Hz summed in both profiles), so with opposite signs they cancel.
  - Roll: no roll motor neuron fired in either profile on either seed, so 0 is not lower than 0. The clause is not met as written. It is untested rather than failed: the failure it was written to catch (left and right firing at different times) did not occur on yaw, the only axis with drive.
  - Adoption follows "What follows": the gate passes, the switch rests on bilateral symmetry (derived), not on a fit, and the anticipated failure did not happen. Roll stays to be checked in a condition where roll motor neurons fire.
  - Prediction: missed on seed 13 yaw (moved 5.7°, predicted within 5°). Mechanism: on the plain body with zero drive the head yaw stays within 0.3° of 0 for 600 ms, so the −6° comes from the rest of the closed-loop body. Inferred: the fly lies on its belly (F-STAND-3), and gravity on the head about a tilted yaw axis sets it. Under m9u the net one-way yaw drive, 0.33 µN·mm on flybody's 3 µN·mm/rad spring (about 6.3°), happened to offset it.
  - Pitch motor neurons fire a little more under m9v (40 → 47.5-55 Hz summed). This is a trajectory difference; pitch mapping is unchanged.
  - Working profile is now m9v = m9u + `motor_map:neck|mirror_sides` 1.

### Pre-registration: flat-plate added mass on the blade-element wing (`aero:wing|added_mass` 1), scored on the roll set and the held-out pitch set (22:08)
- **Why.** At measured asymmetric kinematics the blade-element wing gives 0.42-0.54 of the robot's roll torque (F-FLIGHT-3, DECISIONS 20:43, 21:17). Unsteady terms were the leading candidate. Of these, only added mass has a closed form with no fitted constant: the inviscid flat-plate reaction to normal acceleration, Sane & Dickinson 2001 (JEB 204:2607, eq. 2). Wake capture has no accepted closed form; any version would carry a fitted coefficient, so it is not attempted here.
- **Change, behind a switch.** `BladeElementWing(added_mass=True)` (`aero:wing|added_mass` 1 in the organism; `hover_blade_trace.py --added-mass`). On each strip: −ρπc²/4 dr dv_n/dt along the plate normal, applied at mid-chord. Here v_n is the mid-chord velocity normal to the plate, and dv_n/dt is the backward difference between physics steps.
  - The robofly coefficients (measured at constant speed) do not contain this term, and neither does the circulatory C_rot.
  - MuJoCo's ellipsoid model keeps only the velocity-dependent added-mass part. It is not in the scored forces, which come from the hook alone.
  - Label: derived.
- **Implementation check (done before this registration; `scripts/probes/added_mass_check.py`, robot level 2; `runs/s12/flight/added_mass/`, plot viewed).** The hook's left-wing added-mass force is compared with an independent calculation from the stroke-frame angles (spline as in the table, central differences, mid-chord points r s − (0.5 − x0) c le):
  - correlation 0.988 / 0.970 / 0.995 (x, y, z, world);
  - model RMS 0.91-0.94 of the independent value;
  - cycle-mean Fz 1.09 µN against 1.18 µN.
  - Unit test: `test_blade_added_mass_is_the_flat_plate_reaction_to_normal_acceleration`.
- **Conditions.** As at 21:17: hydei planform, wing length 2.99 mm, area 2.831 mm², weight 1.8 mg, body pitch 47.6°, 0.05 ms step. The scorer is `scripts/probes/score_robot_sets.py`, checked to reproduce the registered roll result on the 21:17 outputs (0.425-0.534).
- **Sets.**
  - Roll, 13 levels plus the three single-angle parts at level 12. This is the development set; it is not held out.
  - Pitch: Database S1 `PitchModulations`, 21 levels at pitch acceleration −2.15 to +2.15 per beat², steady level 10. It is built by `build_measured_kinematics.py --robot-pitch k` (symmetric, same sign map, steady frequency). **Held out: no robot pitch force or torque has been read.** It is run with and without the switch, so this is the first look for both arms.
  - Force: 13 levels, run with the switch and reported.
- **Primary.**
  1. Roll, as registered at 20:43: force-corrected Mx about the hinge midpoint within ±20% of the robot's at levels 6-12. Sign reported, not scored (the convention is unresolved).
  2. Pitch, held out. Force-corrected change from the steady beat, ΔMy, about the Database S1 centre of mass (`score_robot_sets.py`, hinge offset (0.087, 0, −0.783) mm, derived), within ±20% of the robot's ΔMy at every level where the robot's |ΔMy| ≥ 0.03 m g l (≥ 0.01 if fewer than 3 levels qualify). Sign consistent across those levels: a uniform flip is read as the torque convention, as for roll and yaw; mixed signs fail. The hinge-midpoint version is reported.
- **Adoption rule for the switch** (robot comparisons and the flight configuration; no walking profile uses the blade-element wing). Adopt if both hold:
  - on the held-out pitch set, the median |log ratio| with added mass is no worse than without by more than 0.05;
  - on roll, the median ratio does not move further from 1 by more than 0.05.
  Added mass is physics the real wing has. If it worsens the fit, that is recorded as evidence about something else (the robot's data reduction, or the quasi-steady terms), not hidden by leaving it out quietly.
- **Prediction.**
  - Roll: the ratio moves by less than 0.05, because added mass is nearly left-right symmetric at these kinematics. Primary 1 FAILs again, which rules out added mass as the roll-gap cause.
  - Steady vertical force rises by about 0.12 W (two wings × 1.09 µN over 17.66 µN): 0.99 → about 1.11 of the robot's.
  - Pitch, low confidence:
    - without added mass, the |ΔMy| ratio is 0.5-1.5 with a consistent sign;
    - added mass changes ΔMy by less than 20%;
    - so primary 2 passes or fails the same in both arms.
- **What follows.**
  - A pitch pass makes the blade-element wing (with whichever arm passes) the pitch-torque candidate for flight control at measured kinematics.
  - A roll fail with added mass leaves these candidates for the gap:
    - the robot's torque reference and convention (paywalled main text);
    - wake capture (would need a fitted term);
    - the model's hinge spacing (about 11%).
  - Nothing in the walking model changes.
- **Result (22:15): roll primary FAIL; held-out pitch primary FAIL in both arms (consistent sign); switch ADOPTED under the rule.** Outputs: `runs/s12/flight/am/` (with added mass), `runs/s12/flight/pitch/` (pitch without), scores `score_*.json`. Plots viewed: `docs/media/s12_robot_pitch_torque.png`, `docs/media/s12_robot_roll_added_mass.png`.

  | set (levels scored) | reference | without added mass | with added mass |
  |---|---|---|---|
  | roll Mx (6-12) | hinge midpoint (primary) | 0.425-0.534, median 0.461, opposite sign | 0.464-0.554, median 0.494, opposite sign |
  | roll Mx (6-12) | Database S1 CoM | 0.496-0.628 | 0.560-0.674 |
  | pitch ΔMy (0-5, 14-20; 13 levels) | Database S1 CoM (primary) | 0.605-0.691, median abs log ratio 0.413, same sign | 0.615-0.698, 0.402, same sign |
  | pitch ΔMy (same) | hinge midpoint | 0.713-0.812, 0.256 | 0.667-0.756, 0.327 |

  - Primary 1 (roll): FAIL. Primary 2 (pitch): FAIL, every qualifying level below 0.8 in both arms. The sign is the same as the robot's at all 13 levels, where roll and yaw are opposite.
  - Adoption rule:
    - pitch about the CoM: 0.402 against 0.413, not worse;
    - roll median: 0.494 against 0.461, closer to 1.
    - Both clauses hold, so `aero:wing|added_mass` 1 is used in robot comparisons and the flight configuration from now on. No walking profile is affected.
  - Not in the rule, reported:
    - About the hinge midpoint, added mass makes pitch worse by 0.071.
    - On the force set it makes the response worse. Steady force rises to 1.11 of the robot's (1.134 against 1.020 W). Ratios to the steady level depart by more than 0.10 at levels 9-12 (−0.13 to −0.29), against 11-12 without it.
    - The added-mass mean is +0.12 W at the steady level and +0.09 W at the top, so it dilutes the response.
  - Predictions:
    - roll moves less than 0.05: met (+0.033);
    - steady force about 1.11: met (1.11);
    - pitch ratio 0.5-1.5 with a consistent sign, added mass changes ΔMy less than 20%, the same verdict in both arms: all met;
    - force set fails only at levels 11-12: **missed** (9-12).
  - Mechanism (derived): the strip formula keeps only the normal component, −m_a dv_n/dt n. Its cycle mean equals m_a⟨v_n dn/dt⟩, which is not zero. The full inviscid impulse form −d(m_a v_n n)/dt has zero mean over a periodic beat. The in-plane remainder corresponds to leading-edge suction, which separated flow loses. Quasi-steady models in the literature use the normal-only form, so it is kept, labelled.
  - **Roll: two fixes have now failed (planform at 21:17, added mass here), so no third is attempted.** Both are written up in F-FLIGHT-3:
    - the torque gap is a near-constant fraction across levels, about 0.5 in roll and 0.65-0.75 in pitch, while forces agree;
    - a missing unsteady force term would vary with the kinematics, not scale every level alike;
    - a constant fraction points to geometry or convention: the robot's reference point, its normalization length, or its hinge position.
    The robot's main text (on Ben's list) or its time-resolved record would discriminate.
- **Diagnostic after the result (22:18), not a fix: within-beat comparison** (`scripts/probes/robot_torque_reference.py`; F-FLIGHT-3).
  - The opposite roll and yaw sign is a left-right labelling convention in Database S1 (derived). Fy, Mx and Mz are mirrored at roll level 12 and in every single-angle part. The database's `R` wing has the larger stroke at positive roll, yet the robot reports positive Mx.
  - No single reference point explains the roll magnitude.
  - The model's Fx along the stroke is 0.68-0.72 of the robot's at every condition, while Fz agrees.
  - Next: split the model's Fx by term against a measured coefficient set for this wing.

### Pre-registration: folded wings resting on the abdomen (`joint:wing|folded_pose` 1) as candidate m9f (5 October, 02:31)
- **Why.** Ben (5 Oct): the folded wings clip through the body when swept straight back. Diagnosis on the plain body (`scripts/probes/wing_clip.py`, `runs/s12/wingclip/`, F-WING-5):
  - **Visual, yes.** flybody's folded pose (all wing hinge angles 0) holds each wing flat at the hinge height, 40-150 µm below the dorsal surface of abdominal segments 1-4. About 24% of the vein-mesh vertices lie inside the abdomen meshes (deepest 123 µm). Viewed from above, the abdomen covers the wing bases.
  - **Physical, yes.** Wing-abdomen contacts are enabled: the bitmasks allow them and the abdomen is not the wing's parent body. At t = 0 they penetrate 54-144 µm on segments 1-4, plus 20 µm against each haltere. flybody's own XML excludes the wing-abdomen 1-3 and wing-wing pairs; flygym's port drops those excludes. After 300 ms passive with the m9v hinge spring, the contacts prop each wing up about 4° but leave it 51-80 µm inside, because the spring presses toward a pose inside the abdomen.
  - **Wing-thorax: never checked.** The wings are children of the thorax, and MuJoCo's parent-child filter drops those contacts. At rest only the wing root overlaps the thorax mesh: vein vertices within 0.24 mm of the hinge, membrane within 0.6 mm. This is the articulation of a rigid flat wing; a real wing base folds along its basal lines.
- **Change, behind a switch.** `joint:wing|folded_pose` 1 (`passive.rest_wings_on_abdomen`) sets the folded pose (keyframes, start state and folded spring reference) to each wing rotated about the thorax transverse axis through the hinges:
  - the lower (right) wing by 12.5°, derived as the smallest elevation, on a 0.25° grid, with no wing render vertex inside the abdomen and no wing-body contact (12.25° still touches);
  - the upper (left) wing by 1.5° more, derived so that its vertices clear the lower wing's by at least 2 µm where they overlap;
  - which wing lies on top is guessed: no Drosophila data were found.
  - The hinge angles are about yaw +9.3°, roll −8.4° and pitch +0.7°, inside both the function and the measured ranges. Neutral 0 keeps flybody's pose. Nothing else changes.
- **Primary.**
  1. Gate (`closed_loop_check.py`, seeds 12-19, the m9v gate overrides plus the switch): 0 spikes/ms in the last 100 ms, no MuJoCo warnings and no NaN on all 8 seeds.
  2. Plain body at t = 0: no wing render vertex inside the abdomen and no wing contact. After 300 ms passive: wing-abdomen penetration at most 20 µm (soft-contact sag under the wing's own weight), against 51-80 µm on the flybody pose.
- **Secondary.** Contact sheet, side and top, at the folded rest pose, viewed: the wings lie over the abdomen and none of the abdomen shows through them. Battery: no new failures.
- **Prediction.** The gate is unchanged: the wings are passive at rest and the network sees them only through wing afferents. The thorax height changes by less than 0.01 mm.
- **What follows.** A pass makes m9f = m9v + the switch the working profile. A gate failure is written up, not tuned.
- **Result (02:36-02:50): primary PASS on both; m9f adopted as the working profile.**
  1. Gate (`runs/s12/gates/cl_wf_s12..19.json`): 0 spikes/ms in the last 100 ms, no MuJoCo warnings and no NaN on all 8 seeds. Brain excluding ORNs 0.150-0.153 Hz (m9v 0.152-0.155), motor 2.01-2.07 Hz (m9v 2.02-2.06), thorax 0.560-0.562 mm (m9v 0.559-0.561). Prediction met: thorax change under 0.01 mm.
  2. Plain body (`runs/s12/wingclip/wing_clip_on_abdomen.json`): at t = 0 no wing render vertex inside the abdomen and no wing contact. After 300 ms passive, wing-abdomen contacts 3-12 µm and vein overlap at most 19 µm, against 51-80 µm on the flybody pose.
  - Secondary: plain-body sheets (`rest_on_abdomen.png`, `rest_on_abdomen_settled.png`, `zoom_hinge.png`; side, top, rear) viewed: the wings lie along and over the abdomen and none of it shows through. Battery: see SESSION12_LOG.
  - Closed loop (`wing_clip.py --organism m9f --seed 12`; `organism_m9f_s12.png` and `.json`, viewed; 0, 150, 300, 600 ms, gate overrides). Wing-abdomen: at most 4 µm of contact and at most 72 vein vertices up to 9 µm inside the abdomen at 150-600 ms. The fly lies on its belly rolled 15-19° (F-STAND-3), so in the fixed rear cameras the wing pair looks shifted sideways off the abdomen. It still rests on it: the right wing touches abdomen 1-2. At 600 ms wing motor neuron spikes have driven the left wing out (yaw 26°, pitch −15°); that is the network, not the pose.
  - Still open (not part of this switch): the rigid flat wing's root sits inside the thorax mesh, 1400 vein vertices up to 67 µm at rest and 4256 up to 80 µm with the left wing driven out. The parent-child filter hides it from the contact model, and it does not show on the sheets. A real wing base folds along its basal lines; this one cannot (F-WING-5).

### Pre-registration: F-STAND-3 option (c), the connectome's own load reflex on m9f, nothing fitted (5 October, 02:41; runs launched 02:40, no result read)
- **Director's order (02:05).** (c) first: the load reflex through the connectome's own campaniform→motor neuron paths with the m9n nerve-based sensor assignment, no fitting. In parallel, a data fill (not a fit) of homologous leg motor neuron resting rates if published. Option (b), fitting a support drive to the recorded stance, is not approved. If (c) and the homolog fill both fail, take (a): leave the value unfilled and say plainly that the fly lies down.
- **What (c) is.** The working model m9f as it stands: 2 SNpp53 load afferents per leg (3 on lh) assigned by entry nerve (`sense:mechano|assign_by_nerve` 2, measured nerve and side), their own synapses onto the leg motor pools, and every other path in the ≥ 5-synapse connectome. No parameter is added or changed. Structure already counted (`load_reflex_paths_assign_by_nerve2.json`): direct load→support-pool synapses only lh tergotrochanter 7, lh and rh tibia flexor 6 and 5; two-hop paths below 1 synapse-equivalent per pool.
- **Runs** (`scripts/probes/standing_rest.py`, backhouse, `runs/s12/stand3/run_c.sh`): seeds 12-14, 1500 ms, `motor_unit:all|force_per_spike` 10 as in every probe; live, dead (motor output silenced from t = 0), and motor output silenced at 500 ms (the Wang et al. 2025 protocol). Logged: thorax height every 10 ms, trunk-floor contact, per-leg floor force, leg MN rates by joint group before and after silencing, load-afferent rates per leg. Plot: `scripts/probes/stand_fall_plot.py`.
- **Primary.** (c) holds the fly up if, on all three seeds, the live thorax is at least 0.9 mm (target near 1.0 mm, inferred from Wang 2025 and Pratt 2024; F-STAND-3) and the trunk is off the floor for the last 500 ms. A weaker partial: live ends at least 0.05 mm above dead.
- **Prediction.** Fails. Live and dead end within 0.01 mm of each other, the trunk is on the floor within 100 ms on every seed, and the only tonic leg motor neurons are the slow tibia flexors. After silencing at 500 ms the thorax falls by less than 0.025 mm, because it is already down, so the model shows no Wang-type fall (onset 40-300 ms, 1.3 mm/s).
- **What follows.** A fail moves to the homolog fill if the source search (`docs/research/s12_resting_mn_rates.md`) finds a measured resting rate of a homologous leg motor pool; otherwise (a).
- **Result (02:50): (c) FAIL on all three seeds; prediction met. The homolog fill has no number to fill. Option (a) taken: the support drive stays unfilled and the fly lies down.** (`runs/s12/stand3/`; `fall_curves.png`, `standing_silence500_s12.png` viewed; `fall_summary.json`.)
  - Placed at 1.32 mm, live and dead both fall to the floor: trunk contact from 40 ms on every seed, 94-95% of the run. Live ends at 0.554 mm and dead at 0.560 mm, so live is 6 µm lower, not higher. Partial criterion (live ≥ dead + 0.05 mm) also fails.
  - Tonic leg motor neurons, live: slow tibia flexors only (FTi 12.6-16.1 Hz per leg, the same on every seed), plus lf ThC at 0.3-0.5 Hz. Every trochanter and coxa support pool is silent.
  - Load afferents fire at 21-23 Hz per cell on five legs and 0 Hz on lh, the same on every seed. They reach the support pools through 7 synapses at most (lh tergotrochanter), so their firing does not move the pools.
  - **Fall after silencing** (motor output off at 500 ms): the thorax drops 2-4 µm, because the fly is already lying down. The model has no standing state to fall from, so the Wang 2025 curve (onset 40-300 ms, 1.3 mm/s) cannot be compared. The only fall in the model is the passive one from placement: onset within 10 ms, 15 mm/s (10-90% of a 0.76 mm drop). Real silenced flies fall about 12× more slowly; Wang's passive-only simulation gives 37 mm/s.
  - **Homolog fill** (`docs/research/s12_resting_mn_rates.md`, subagent, sources read where marked). The only measured resting rate of a Drosophila leg motor neuron is the slow tibia flexor's: about 30 Hz, n = 14 (Azevedo et al. 2020, text and Fig. 3D). The model's target, 24.8 Hz, is one cell from the Dryad raw data. Locust SETi is active during standing, with no rate given (Burns & Usherwood 1979, abstract). Cricket SETi is silent at rest. Cockroach Ds is tonic at rest only in secondary, unverified claims. No source gives a resting rate for the coxa promotor/remotor or trochanter-depressor pools in any insect. There is no number to fill. Copying the tibia flexor rate to the support pools was already computed to give about 0.3% Hill activation against the 11-32% needed (F-STAND-3).
  - **So, plainly: the model fly lies down at rest.** The support drive real flies use is unmeasured, the connectome's load paths are too sparse to supply it, and filling it to make the fly stand would be the behavioural fit the Director ruled out. The value stays an open blank in the ledger.

### Pre-registration: blade-element wing against Dickson et al. 2010 yaw damping and yaw actuation (5 October, 02:45; probe committed as WIP in 4b834b3, never run)
- **Why.** Held-out drag test identified at 22:26 (s12). Dickson, Polidoro, Tanner & Dickinson 2010 (J Exp Biol 213:3047; open; `data/raw/flight_kinematics/dickson2010/`) measured, on a dynamically scaled D. melanogaster wing pair (R 0.23 m, mean chord 0.065 m, hinges 0.11 m apart, Re about 100, horizontal stroke plane), the stroke-averaged yaw torque while the robot turned at constant rate (passive yaw damping) and under four bilateral kinematic changes (yaw actuation). Nothing in the model has been fitted to these numbers; no model output has been computed on them.
- **Protocol** (`scripts/probes/yaw_damping_dickson2010.py`, as committed apart from the docstring date). Their baseline kinematics (eqs 1-3: stroke amplitude 70°, k_φ 0.01, rotation 45°, k_α 1.5, no deviation), mapped to hinge angles through `flight.wing_pose_ik`. Thorax pitched so the stroke plane is horizontal; body turned at constant ω about the vertical through the hinge midpoint; torque from the wing forces only, averaged over beats 4-6 of 6. Chords scaled so mean chord over R equals the robot's (0.283; the scan's is 0.374), scan length and shape kept; τ* = τ/(ρ c̄⁵ f²), ω* = ω/f, so the wingbeat frequency drops out. Blade-element model with flat-plate added mass (adopted for robot comparisons at 22:15); no-added-mass reported.
  - Damping: ω* at −0.73, −0.365, 0, 0.365, 0.73 (the robot's range). Actuation: differential angle of attack pa, deviation pd and stroke-plane rotation pr at 0, ±0.087, ±0.17 rad; velocity asymmetry pv at 0, ±0.033, ±0.066 (their Figs 7-8). 25 runs.
- **Primary.** Damping slope C*_ω (least squares of τ* on ω*) negative and within ±20% of the robot's −6.4×10² (the robot's spread over trials is under 5%); τ* linear in ω* (r² ≥ 0.95).
- **Secondary.** Actuation slope magnitudes within ±20% of the robot's (their Table 3: pa 3.1×10³, pd 1.3×10³, pr 1.3×10³, pv 3.4×10³). Magnitudes only: the robot's sign convention for each parameter relative to this frame is not established (stated in the probe before any run).
- **Reported, not criteria.** The no-added-mass slopes; mean vertical force; the model's hinge half-separation over R against the robot's 0.24; maximum hinge-angle fitting error per table.
- **Prediction.** Primary FAIL low: C*_ω about 0.6-0.8 of the robot's. Yaw damping comes mostly from the drag difference between the wing moving with and against the turn, and the model's stroke-direction force was about 0.70 of the robot's (22:20, drag term). Actuation magnitudes 0.4-0.9 of the robot's, lowest for pa (left-right differences ran about 0.5 in roll, 22:15).
- **What follows.** Nothing in the model changes on the result. A pass is the first held-out torque test the blade-element wing passes; a fail low with the same ratio as the 22:20 force deficit points at the drag coefficient, which has no open measured set (22:26).
- **Result (02:52): primary FAIL, high; secondary 2 of 4 within ±20%.** (`runs/s12/flight/dickson2010/dickson2010.json`, `.png` viewed; `_noam` reported.)

  | slope | model | robot | ratio | r² |
  |---|---|---|---|---|
  | C*_ω (damping) | −856 | −640 | 1.34 | 1.0000 |
  | pa (angle of attack) | −3493 | 3100 | −1.13 | 1.0000 |
  | pd (deviation) | −1208 | 1300 | −0.93 | 1.0000 |
  | pr (stroke-plane rotation) | −1760 | 1300 | −1.35 | 1.0000 |
  | pv (velocity asymmetry) | 1577 | 3400 | 0.46 | 0.9999 |

  - Damping has the right sign (it opposes the turn) and is linear, but 34% too strong: outside ±20%. Without added mass it is the same (−856), so added mass plays no part.
  - Actuation magnitudes: pa 1.13 and pd 0.93 within ±20%; pr 1.35 and pv 0.46 outside. The model's sign is opposite to the robot's for pa, pd and pr and the same for pv. The probe does not establish the robot's sign conventions, so the sign is reported and not scored.
  - Hinge-angle fitting error 0.0° in every table. The model's hinge half-separation over R is 0.164, against the robot's 0.24. A smaller offset should lower the damping, so it does not explain the excess.
  - Prediction missed: it said 0.6-0.8 for damping, with pa lowest among the actuation slopes. Measured: 1.34 for damping, pv lowest. Extrapolating from the hydei-robot force deficit (22:20) was wrong for this wing and these kinematics.
  - Nothing in the model changes. Next discriminating experiment: split the damping torque by term (translational lift, translational drag, rotational force). The rotational term's coefficient is derived from theory (C_rot = π(0.75 − x̂₀)), not measured on this wing, and it scales with |w|. That makes it the first suspect for an excess that tracks the velocity asymmetry.

### Pre-registration: leg and wing taste modality per type from receptor-line matching (`sense:taste_leg|modality_source` 1) (5 October, 02:57; no run yet)

Problem (flyapp relay): leg taste peaks at about 2.9 mV at 1 M sugar (15 mV x 1/(1+0.05) x 0.2), below the about 7 mV spiking threshold, because every leg/wing taste type carries a guessed weight of 0.2 to every tastant. The weight, not the gain, is the guess that can be replaced from data.

Change behind the switch (0 = legacy, minimal): types matched to receptor lines in the gustatory connectome preprint (bioRxiv 2025.08.25.671814, preprint of Cell 2026; secondary read, `docs/research/s12_tarsal_grn_physiology.md`) take the labellar rule, 1 for their modality and 0 otherwise: LgLG4 (Gr64f+/Ir56b+), LgAG2 (Gr61a+) and WG2 as sugar, LgAG1 (Gr33a+) as bitter. Contact-pheromone types (LgLG1a, LgLG1b, LgLG2, LgLG5-8, WG1, WG3, WG4) get 0 to all five tastants. Unmatched types (LgLG3, LgAG3-9, LB2b, LB2d, SNch05, untyped; 237 cells) keep 0.2 to all (guessed). Basis of the channel becomes inferred. Gain 15 mV and K 0.05 M stay as they are (guessed; no leg dose-response found; Ling 2014 says tarsal and labellar sugar GRN rates are comparable, which supports sharing the labellar gain but does not measure it).

Expected drive (derived): sugar types 10.0 mV at 100 mM and 14.3 mV at 1 M; unmatched types unchanged at 2.0 and 2.9 mV.

Pass criteria, fixed now (probe `scripts/probes/leg_taste_dose.py`, m9f, seed 12, rates over 100-400 ms on a sucrose patch covering the arena):
1. Held-out rate (Ling et al. 2014, secondary read, about 50-55 Hz at 100 mM sucrose): LgLG4 mean rate at 100 mM within a factor of 2, 25-110 Hz. A weak test: one concentration, read through a summary, and the model's per-type rate depends on how many tarsi touch the patch.
2. Specificity: LgAG1 (bitter) and the pheromone types below 3 Hz on sucrose (Ling: spontaneous below 3 Hz).
3. No-food rest unchanged: the switch acts only through a food patch, so the gate (`closed_loop_check`, seeds 12-19) must give the same numbers as m9f.
If 1 fails the switch stays off and the miss is recorded; nothing is tuned to reach it.

Result (5 October, 03:03; m9f seed 12, rates over 100-400 ms; `runs/s12/legtaste/`):

| Sucrose | Switch | Drive, sugar types | LgLG4 mean | LgLG4 per second of tarsus contact | LgAG1, pheromone types |
|---|---|---|---|---|---|
| 0 | 0 and 1 | 0 | 0 Hz | n/a | 0 Hz |
| 100 mM | 0 | 2.0 mV | 0 Hz | 0 | 0 Hz |
| 100 mM | 1 | 10.0 mV | 4.5 Hz (max 20) | 18.5 Hz | 0 Hz |
| 1 M | 0 | 2.86 mV | 0 Hz | 0 | 0 Hz |
| 1 M | 1 | 14.3 mV | 7.8 Hz (max 33) | 34.0 Hz | 0 Hz |

- Criterion 1 (held-out rate, 25-110 Hz at 100 mM): FAIL, 4.5 Hz. The cause is contact, not transduction. Only two of six tarsi touch the patch: rm 44% and rh 92-97% of the window, the other four 0%. The fly lies down (F-STAND-3 option (a)), so most leg GRNs never meet the sugar. A cell with steady contact at 10 mV would fire 38 Hz and at 14.3 mV 64 Hz (derived from its own LIF constants: tau_m 20 ms, threshold 7 mV above rest, reset at rest, refractory 2.2 ms, no adaptation), which is inside the band. That is a calculation, not the pre-registered measurement, so the criterion stands as failed.
- Criterion 2 (specificity): PASS. LgAG1 and every pheromone type at 0 Hz on sucrose, and every leg taste type at 0 Hz with no food.
- Drive now crosses threshold: 14.3 mV at 1 M against 2.86 mV before, as derived. The flyapp relay problem (2.9 mV peak, below threshold) is answered by the weights, not by changing the gain.
- Side findings: WG2 (wing margin) cells have no leg and take the mean over six legs' contact, so at 1 M they all fire 26.7 Hz from leg contact. Wing taste should come from wing contact; that mapping is guessed and stays open. MN9 (proboscis motor neuron) stays at 0 Hz with leg sugar GRNs firing, so tarsal sugar does not reach proboscis extension in this run. Real flies extend the proboscis to tarsal sugar; not tested further here.
- Per the rule above the switch stays off in the working profile (m9f unchanged). It is available as `--set 'sense:taste_leg|modality_source=1'`.
- Criterion 3 (gate unchanged): PASS. Seeds 12-19 with the switch on give the same numbers as m9f in every field except wall time (brain excluding ORNs 0.150-0.153 Hz, motor 2.01-2.07 Hz, thorax 0.560-0.562 mm; `runs/s12/gates/cl_wg_s*.json`).
- Sheet: `docs/media/s12_leg_taste.png` (viewed).

### Pre-registration: Dickson 2010 yaw damping split by force term (5 October, 03:15; diagnostic, nothing changes in the model)

Record-only change: `BladeElementWing.parts_m0` keeps each term's moment about the world origin. The probe takes each term's yaw torque about the vertical through the hinge midpoint, (moment about the origin) − O × F, and fits a damping slope per term on the same five yaw rates as the 02:45 test (added mass on, dt 0.05 ms, mean of beats 4-6). The four term slopes must add up to the total slope (−856) within 1%.

Prediction, from symmetry, which revises the 02:52 note that named the rotational term first:
- Lift: about 0. With a horizontal stroke plane, the strip velocity stays horizontal and perpendicular to the span under yaw, so lift stays vertical and has no yaw arm.
- Rotational: about 0. Yaw adds a speed change that has the same sign through each half-stroke and is nearly even about mid-stroke. dα/dt is odd about mid-stroke, so the first-order change in U·dα/dt cancels over each half-stroke.
- Added mass: about 0 (a cycle average of a time derivative; the 02:52 runs with and without it gave the same slope).
- Drag: at least 90% of the total. If so, the 34% excess sits in the drag term: its coefficient, the wing's radial chord distribution (torque scales with (R/c̄)^4 times the third moment of area), or a definition of R or c̄ that differs from the robot's.
If drag carries less than 90%, the symmetry argument is wrong for this model and the leading term is examined next.

Result (5 October, 03:21; `runs/s12/flight/dickson2010/dickson2010_split.json`): prediction holds. Damping slope by term: drag −858.0, rotational +1.9, added mass −0.1, lift 0.0; the four sum to the total −856.2 exactly. Drag carries 100.2% of the damping.
- The 02:52 note naming the rotational coefficient as first suspect is withdrawn: its contribution cancels over each half-stroke, as the symmetry argument says.
- The 34% excess therefore sits in the translational drag term. The model's geometry matches the robot's definitions as far as the paper states them: rotation angle is the chord from vertical with 45° angle of attack at mid-stroke (paper, Fig. 2 legend and text), R is the wing length, c̄ the mean chord, and the model's c̄/R is set to the robot's 0.283. The model's ellipse has r̂2 0.539 and r̂3 0.587 (derived), close to a melanogaster wing; no published r̂ for the robot wing was found in the paper.
- The hinge offset makes the gap larger, not smaller. A strip-theory estimate (derived) of the drag damping, proportional to ∫ c r (r + h cos φ)² dr averaged over the stroke, gives about 15% more damping at the robot's offset (0.24 R) than at the model's (0.164 R). At equal offset the model's excess would be about 1.5×.
- Interpretation (inferred, not tested): the quasi-steady drag derivative 2·C_D(45°)·q/U, with the 1999 robofly C_D of about 1.7 at 45°, overstates how much a flapping wing's drag changes with a small change in speed. Candidates: a lower C_D at Re 100 in this robot, or induced flow, which the model leaves out. This runs the opposite way to the hydei-robot comparison, where the model's stroke-direction force is 0.70 of the robot's, so one coefficient scale cannot fix both.
- Next discriminating experiment: a measured revolving-wing drag polar at Re about 100 (Sane & Dickinson 2001, or Dickson & Dickinson 2004) put through both tests unchanged. If it lowers the damping toward 1.0 without lowering Fx further against the hydei robot, the coefficient is the cause; if both fall, the quasi-steady drag derivative itself is the problem. No model change until then.

Note (5 October, 03:22): the "measured drag polar" next step above is not a new test. The model's C_D is already the measured robofly polar (Dickinson, Lehmann & Sane 1999, Re about 136; `flight.robofly_coefficients`), the same polar Sane & Dickinson used. The remaining candidates are the coefficients' dependence on advance ratio (Dickson & Dickinson 2004) and induced inflow, both model-form changes to pre-register before building.

### Pre-registration: mirror the leg rest angles (5 October, 03:25; `joint:leg|rest_mirror`)

Finding that prompts it (03:22-03:25, `scripts/probes/load_afferent_legs.py`, `scripts/probes/mirror_audit.py`, `runs/s12/stand3/`):
- The lh load afferents are silent because the lh leg carries little transmitted load (strain proxy 0.83 against 1.7-6.4 on the other legs; drive 5.1 mV, under the 7 mV threshold; the other legs reach 9.0-9.7 mV). The dead fly lies rolled 26° onto its right side with lm and lh in the air.
- The roll starts in mid-air: 0.9° at 10 ms and 1.9° at 30 ms, before any contact at 40 ms. A mirror-symmetric body in a mirror pose with no actuator input cannot do that. The m9w dead fly tips the other way (−25°).
- Mirror audit of the built m9f body (41 left/right hinge pairs; every leg pair has the same angle sign convention): the leg spring references, and so the placed pose, differ left from right. Front leg: coxa roll 23.2° left against 5.0° right, coxa yaw −29.4° against −19.7°, CTr −63.6° against −71.1°, FTi 63.0° against 66.8°. Middle and hind pairs differ by at most 1°.
- Cause: the rest angles (`data/params/passive_leg_rest_fit.csv`, F-REST-1, inferred) were fitted per leg. The measured targets (eLife 2025 Fig. 3C) are right legs only. The left legs were fitted to the same targets and landed on another solution of a fit the file already calls non-unique for the front coxa yaw/roll split. The left/right difference is a fitting artifact, not data.

Change: `joint:leg|rest_mirror` 1 gives each left leg joint the right partner's fitted reference (same sign; the audit found every leg pair on the same convention). The right legs are the measured side. Default 0 keeps the per-side fit. It applies to all three fitted tables (spring_reference 1, 2, 3). Inferred: bilateral symmetry of the passive rest posture, since no left-leg data exist. Note: in left-leg geometry the left front solution fitted the targets better (residuals 3.5/−3.8/3.1° against 6.7/−11.0/2.0°). flybody's legs are not exact mirrors either (the audit finds sub-1° range and axis differences and up to 0.15 mm in segment origins), so mirrored angles are not exactly mirrored equilibria.

Predictions:
1. Dead drop (`standing_rest.py --dead`): mid-air roll at 30 ms falls from 1.9° to under 0.5°.
2. The tip-over itself may remain. A fly lying on its sternum with splayed legs may be sideways-unstable, and the scan's own asymmetry would then pick the side. If |roll| at the end is still above 10°, the tip-over is an instability and not this asymmetry; if it falls under 5°, the asymmetry was the cause.
3. Silence gate, seeds 12-19: pass.

Adoption rule: adopt into the working profile if 1 and 3 hold, whatever 2 shows (symmetry is the better-supported construction either way). Report 2 as a finding. Contact sheet: the dead-drop frames, viewed.

Result (5 October, 03:30; `runs/s12/stand3/standing_dead_mirror_s12.json`, `mirror_audit_m9f_mirror.json`, `runs/s12/gates/cl_wm_s12..19.json`, all backhouse):
- Audit with the switch: every leg pair's spring reference and placed angle now agree. What remains is leg damping, which differs by up to 10% (lf coxa yaw 0.049 against 0.053; derived per leg from its own stiffness projection), FTi ranges under 1°, and segment origins up to 0.15 mm (flybody scan).
- Prediction 1: PASS on the stated number. Roll at 30 ms is −0.2°, against 1.9°. Caveat: the 10 ms sample already shows rh floor contact (12 µN), and the roll reaches −1.4° at 20 ms before it reverses. Contact is sampled every 10 ms, so the earlier run may also have touched between samples. The "mid-air" window is therefore not clean in either run.
- Prediction 2: |roll| at the end is 16.2° (was 25.3°), onto the same (right) side; lf 0.57, rm 1.75, rh 1.95 µN; lm and lh in the air. Above 10°, so by the registered reading the tip-over is an instability of the lying pose and not caused by this asymmetry alone; mirroring removed about a third of it. lh load afferents are still at 0 Hz.
- Prediction 3: PASS. Seeds 12-19: 0 spikes/ms in the last 100 ms, no MuJoCo warnings, no NaN; brain excluding ORNs 0.154-0.158 Hz (m9f 0.150-0.153), motor 2.02-2.11 Hz (2.01-2.07), thorax 0.547-0.552 mm (0.560-0.562).
- Sheet `docs/media/s12_rest_mirror_dead.png`, viewed: the fly lies closer to level, and its left legs still lift at the end; wings folded with no visible clipping.
- Adopted per the rule: **m9r** = m9f + `joint:leg|rest_mirror` 1 is the working profile (03:31). Battery started on backhouse.
- Battery on m9r (backhouse, 03:41, `runs/s12/pytest_battery_m9r.log`): 202 passed, 12 skipped, 1 failed, the known backhouse-only raw-data path check (`data/raw/door/units/`, passes on the Mac). One more test than m9f (the new mirror test). No regressions. The single MuJoCo NaN warning in the log is `test_a_diverged_run_is_flagged_invalid`, which diverges on purpose; it appears in every earlier battery log.

### Pre-registration: mirror the leg damping, dead drop (5 October, 04:13; `joint:leg|damping_mirror`; diagnostic, nothing adopted)

Director item 3. After m9r (rest angles mirrored) the dead fly still lies tipped 16.2° onto its right side. The mirror audit's largest remaining leg difference is damping: up to 10% left against right (lf coxa yaw 0.049 against 0.053 µN·mm·s/rad). Damping is derived per leg as tau × the leg's own projected stiffness (F-DAMP-1), and the stiffness differs 2.5-6.6% because the scanned segment geometry differs (03:34, kept as specimen geometry).

Change: `joint:leg|damping_mirror` 1 gives each left leg hinge DOF (not the inter-tarsal chain) its right partner's damping. Default 0. Only acts with `joint:leg|damping_source` 1 (m9r has it). Inferred bilateral symmetry.

Predictions:
1. Audit with the switch: no leg pair differs in damping.
2. Damping sets how the fly moves, not where it can rest, so it cannot remove an instability of the lying pose. Final |roll| stays above 10° (the 03:25 reading: an instability, with the scan's asymmetry picking the side). The side may flip, which would show the damping asymmetry picks it. If |roll| falls under 5°, the damping asymmetry was the cause.

No adoption rule. Mirroring damping alone breaks c = tau × k on the left legs while their stiffness stays unmirrored, so this is a diagnostic. If the side flips or the roll falls under 5°, the next step would be a pre-registered mirror of the whole left leg (stiffness and damping). Sheet: the dead-drop frames, viewed.

Result (5 October, 04:21; `runs/s12/dampmirror/`, backhouse; m9r baseline rerun alongside, same code):
- Prediction 1: PASS. With the switch, no leg pair differs in damping (16 leg pairs listed before, none now). Left 38 flagged pairs, as before: hinge axes are not exact mirrors (lf coxa 3-4°, lf tarsus chain 13°, other legs under 3.2°; angle from the audit's axis error), FTi ranges under 1°, the wing fold, the labrum. The 03:30 text "sub-1° range and axis differences" understated the axes; the ranges are sub-1°, the axes are not.
- Prediction 2: the side flips. The m9r baseline reproduces +16.2° (right side down; rm 1.75, rh 1.95, lf 0.57 µN). With mirrored damping the fly ends at −25.5° (left side down; lm 1.62, lh 1.82 µN; right legs in the air). The first 30 ms are nearly the same (roll −0.6, −1.3, −1.7° against −0.6, −1.4, −0.2°); the runs part at 50 ms (−2.9° against +2.2°). |roll| stays above 10° in both.
- Reading: the lying pose is bistable. The dead fly settles on either side at 16-26°, and which side is decided by left/right differences of a few percent (here leg damping, which changes how it falls but not where it can rest). So the tip-over is not an artefact of one asymmetry, and a perfectly mirrored body would still fall to one side. Whether real dead flies lie tilted is not in the sources used (eLife 2025 used tethered flies), so this is not a defect by any measurement.
- Sheet `docs/media/s12_damp_mirror_dead.png`, viewed: the fly lies on its left side with the right legs raised; wings folded on the abdomen, no visible clipping, no limp wing.
- Not adopted (diagnostic, as registered). Switch stays 0. The registered next step if the side flipped was a mirror of the whole left leg; given the bistability that would only choose the side again, so it is not run.

## Pre-registration: ascending leg sugar cells alone, presynaptic gain sweep (5 October, 04:40; diagnostic, nothing adopted)

- **Question.** F-TASTE-LEG-1: leg sugar dies between layer 1 and layer 2. Thoma et al. 2016 put tarsal PER on the ascending sweet GRNs (inferred match: LgAG2, 11 cells, `sensory_ascending`). Hunger in real flies raises sweet GRN presynaptic calcium via dopamine (Marella 2012, Inagaki 2012; summary level, no gain in numbers found). How much presynaptic gain on LgAG2 alone does MN9 need?
- **Run.** `assay_pathways.py --assay ascsugar_mn9 --release-gain LgAG2=G`, G = 1, 3, 10 (guessed range, a measuring sweep, not a value); Poisson 100 Hz into the 11 LgAG2 (above Ling 2014's 50-55 Hz at 100 mM; secondary), 2 trials, open loop; m2 (Shiu parameters) and m9r. Readout MN9_L.
- **Predictions.** (1) G = 1: MN9_L 0 Hz under both (the 54-cell drive already fails). (2) G = 3: layer-1 cells near threshold fire, MN9_L still 0 Hz under m9r; under m2 MN9_L under 5 Hz. (3) G = 10: MN9_L fires under m2 (at least 5 Hz), not under m9r. If MN9 stays at 0 Hz at G = 10 under m2, the route from the ascending cells is not a gain problem at the first synapse.
- **Use.** Diagnostic. The option scales every output synapse of the chosen types; no switch, nothing changes in the working profile.

### Result (04:47; `runs/s12/legsugar/gain_*.log`, `runs/assay-ascsugar_mn9-*`, backhouse)

MN9_L, Hz (2 trials, LgAG2 at 100 Hz):

| gain on LgAG2 | m2 | m9r |
|---|---|---|
| 1 | 0, 0 | 0, 0 |
| 3 | 0, 0 | 0, 0 |
| 10 | 3, 3 | 0, 0 |

- Prediction 1 PASS. Prediction 2 PASS (under m2, layer-1 cells on the LgAG2 → MN9_L shortest paths that fire: 3 of 16 at gain 1, 10 at gain 3, 15 at gain 10). Prediction 3 FAIL under m2 (3 Hz, below the 5 Hz predicted); PASS under m9r.
- Layer 2 (26 cells) under m2: 0, 0 and 3 cells fire at gains 1, 3 and 10. So with almost every layer-1 cell recruited, layer 2 stays nearly silent. MN9_L inputs that fire at gain 10 include GABAergic GNG130 (7 Hz), DNg90, DNge051 ×2, as well as cholinergic GNG108, DNge080 ×2, DNge059 and serotonergic GNG002.
- Post hoc, not pre-registered (m2, 2 trials): LgAG2 at gain 30, 5 and 7 Hz. All 54 leg sugar GRNs at gain 3, 0 Hz; at gain 10, 10 and 13 Hz. For scale, labellar sugar at 100 Hz with no gain gives 21-31 Hz.
- Reading: a presynaptic gain on the ascending cells recruits their first relay but barely moves layer 2. An order-of-magnitude gain gives a few Hz, far below labellar sugar, and nothing under the working profile. A first-synapse gain such as hunger at the GRN terminal is not enough on its own in the modelled wiring. Nothing adopted.

## Pre-registration: is feedforward inhibition what stops leg sugar at layer 2? (5 October, 04:50; diagnostic, nothing adopted)

- **Question.** 52% of the layer 1 → 2 edges on the leg sugar paths are inhibitory, and at LgAG2 gain 10 the MN9_L inputs that fire include GABAergic cells (GNG130, DNg90, DNge051). Is the block feedforward inhibition rather than weak excitation?
- **Run.** m2, open loop, `ascsugar_mn9`, Poisson 100 Hz into LgAG2, 2 trials, with `--silence-ids` (new diagnostic option). (a) The 8 inhibitory cells (predicted GABA or glutamate, Shiu's sign rule) on the LgAG2 → MN9_L shortest paths (GNG147 ×3, GNG182, GNG001, GNG088, DNge146, GNG297), at gain 1 and 3. (b) Those plus every inhibitory direct input to MN9_L (51 cells; MN9_L has 93 direct inputs at 5 or more synapses), gain 1, at 0 and 100 Hz.
- **Predictions.** (a) MN9_L 0 Hz at gain 1, under 5 Hz at gain 3: the excitatory share is too small for disinhibition to matter. (b) Under 2 Hz at 0 Hz input; under 5 Hz at 100 Hz input. If (b) at 100 Hz gives 5 Hz or more against under 2 Hz at 0 Hz, inhibition onto MN9 is a main part of the block.

### Result (04:51; `runs/s12/legsugar/sil_*.log`, backhouse)

- (a) 8 on-path inhibitory cells silenced: MN9_L 0, 0 Hz at gain 1 and 0, 0 Hz at gain 3. Active cells unchanged at gain 1 (101, as without silencing). PASS.
- (b) 51 cells silenced (on-path plus every inhibitory direct input to MN9_L): 0, 0 Hz at 0 Hz input and 0, 0 Hz at 100 Hz input. PASS.
- Reading: feedforward inhibition is not the block. With every inhibitory input to MN9_L removed, the ascending leg sugar cells at 100 Hz still give 0 Hz, so layer 2 lacks excitation, not disinhibition. With the gain sweep this makes two failed rescues (first-synapse gain, disinhibition); per the working rules the mechanism is written up in F-TASTE-LEG-1 and no further fix is tried this session. Nothing adopted.

## Pre-registration: leg sugar including LgLG3 (5 October, 04:59; diagnostic, nothing adopted)

- **Source.** Tastekin et al. (bioRxiv 10.1101/2025.08.25.671814 v2, Fig 6; secondary read): Dandelion is male-cns AN13B002 (FlyWire AN_GNG_68) and a key partner of labellar sugar GRNs (LB3b); LgLG3 has Dandelion as a top partner, so the authors propose LgLG3 expresses sugar receptors, especially Gr5a (a proposal, not a measurement). Male-cns: LgLG3 is 162 cells (23-31 per leg, all `vnc_sensory`); 8770 of its 58495 output synapses go to AN13B002, against 298 from LgLG4 and 0 from LgAG2. AN13B002 is predicted GABAergic (type confidence 0.89), so the model treats it as inhibitory. The model gives LgLG3 the unmatched weight 0.2.
- **Run.** `assay_pathways.py --assay legsugar3_mn9`, Poisson 0 and 100 Hz into LgLG3 + LgLG4 + LgAG2 (216 cells), 2 trials, open loop, m2 and m9r.
- **Predictions.** m2: MN9_L under 5 Hz at 100 Hz (Dandelion is inhibitory in the model, and the 54-cell drive gives 0 Hz). m9r: 0 Hz. If MN9_L reaches 5 Hz or more under m2, LgLG3 carries a leg sugar route the model has been leaving undriven.

### Result (05:02; `runs/s12/legsugar/lg3_*.log`, `runs/assay-legsugar3_mn9-*`, backhouse)

- MN9_L, 216 leg cells at 100 Hz: m2 0, 0 Hz; m9r 0, 0 Hz (0 Hz at rest). Both predictions PASS.
- Under m2 Dandelion (AN13B002, both cells) fires at 310-320 Hz, and LgLG3's other main partners fire too (AN05B023d 134-159 Hz, DNge153 239-245 Hz, DNpe029 42-72 Hz). So LgLG3 strongly drives the cell the authors tie to feeding, and the model, using the male-cns GABA prediction, makes that cell inhibitory.
- Reading: in the model, the leg sugar signal reaches Dandelion strongly, and Dandelion's sign decides what it does next. Its transmitter is a prediction from EM, not a measurement. Changing it would be a third rescue after two failures, so none is tried this session. Next evidence: a measured transmitter for Dandelion / AN_GNG_68 (reference [47] of Tastekin et al. names it), and the authors' own LgLG4 → MN9 path analysis read by eye. Nothing adopted.
- Correction (05:04): Dandelion's transmitter is not only an EM prediction. BANC also labels both AN13B002 cells `neurotransmitter_verified` = gaba. The basis is undocumented locally and the label covers 431 of 440 hemilineage-13B cells, so it is probably lineage-level (inferred). No measurement of this cell type was found. HANDOFF item 1.

## Pre-registration: fold force_per_spike 10 into m9r (5 October, 21:27; Director night order 2)

- **Why.** A profile name must mean one model. Every gate and probe since session 5 ran with `--set 'motor_unit:all|force_per_spike=10'` (guessed) on top of the profile; the profile left it at the registry default of 1 (guessed). flyapp records m9r as named, without the override, so its m9r and the gated m9r differ. Under m9r, 71 of 732 mapped motor neurons read this shared value (all leg cells with no row in `data/params/motor_forces.csv`; census 5 Oct 05:11, `scripts/probes/shared_fps_census.py`).
- **Change.** `profiles.M9R` gains `motor_unit:all|force_per_spike` = 10 µN·mm, labelled guessed (the value every m9-family gate ran with; bounded by the fast tibia unit, 10 µN at the tibia, Azevedo et al. 2020, × a lever of order 1 mm). Folded into m9r, not a new name, because m9r's gate already ran with it, so the name gets the model that passed. Earlier profiles keep their definitions. Profile values enter by `setdefault`, so explicit `--set` still wins and the scripts' `=10` defaults become no-ops.
- **Predictions.** (1) Static: m9r with no override gives the same per-neuron torque array as pre-fold m9r with `--set ...=10` (all 858 rows equal). (2) Gate seed 12 (`closed_loop_check`, 1000 ms, backhouse) after the fold, with the profile alone (its `--set` default left in place, now a no-op), reproduces the archived m9r gate `runs/s12/gates/cl_wm_s12.json` (hand-listed keys) in every rate field. (Amended 21:28 before any run: `closed_loop_check` cannot drop its default `--set`, so the no-override case is covered by (1); the scalar has one reader, `neuromuscular.build`.) (3) Battery: no regressions against 203 passed / 12 skipped / 1 known backhouse path failure. If any test changes, it is one that builds m9r with no override, and that is the fold acting as intended; check each before accepting.

## Pre-registration: Dandelion sign bracket (5 October, 21:30; Director night order 1; diagnostic, neither sign adopted)

- **Why.** Dandelion (male-cns AN13B002, 2 cells) is GABA by EM classifiers; no measurement for the cell type was found by 05:04 (the literature search is running again tonight). Bracket both signs so the consequence of the unknown is on record.
- **Structure (derived, male-cns cache, edges ≥ 5 synapses).** Dandelion makes 21,220 output synapses onto 732 cells, mostly VNC interneurons and ascending neurons (top partners AN09B004 1523, ANXXX027 1309, AN17A015 863, IN23B005/056/009 about 580 each). No direct synapse onto MN9. One 2-hop route: Dandelion → GNG297 (GABA, 45 synapses) → MN9 (42).
- **Run.** `assay_pathways.py`, open loop, `--rates 0,100 --trials 3 --shuffles 0`, profiles m2 and m9r, assays `legsugar3_mn9` (216 leg cells), `sugar_mn9` (labellar LB3b/LB3c) and `sugar_bitter_mn9`; each once as is (GABA, sign −1) and once with `--nt AN13B002=acetylcholine` (sign +1; new diagnostic option, which also sets the transmitter label the GABA-B split reads). 12 runs, backhouse.
- **Predictions.** (1) GABA reproduces 05:02: leg drive gives MN9_L 0 Hz under m2 and m9r. (2) Acetylcholine: leg drive still gives MN9_L under 5 Hz under both profiles (no direct synapse; the only 2-hop route goes through an inhibitory cell). (3) Labellar sugar at 100 Hz: MN9_L differs by less than 30% between signs, under each profile. (4) Sugar + bitter: MN9_L differs by less than 1 Hz between signs.
- **Reading rule.** If acetylcholine gives MN9_L ≥ 5 Hz to leg drive under either profile, the model's leg PER hinges on Dandelion's sign and the measurement goes high on Ben's list. If not, the leg sugar failure does not depend on this sign. Neither sign is adopted either way; the model keeps the classifier call (GABA) until a measurement exists.

### Result of the fold (21:40; `runs/s12/fpsfold/`, backhouse and Mac; pre-registration two sections up)

- (1) Static, Mac: m9r with no override and m9r with `--set ...=10` give identical per-neuron torque and twitch arrays (858 rows; 71 at 10). PASS.
- (2) Gate seed 12 after the fold (`cl_fold_s12.json`) equals the archived m9r gate (`runs/s12/gates/cl_wm_s12.json`) in all 18 fields. PASS.
- (3) Battery (`pytest_battery_m9r_fold.log`): 203 passed, 12 skipped, 2 failed. One is the known backhouse path check. The other, `test_steering_mns_change_their_wing_only`, was a truncated CSV read (`EOF inside string`) because I re-synced code to backhouse while the battery ran. Rerun alone it passes (`pytest_rerun_steering.log`, with the new fold test). So 204 passed, 1 known failure, no regressions. PASS.
- Adopted: m9r now carries force_per_spike 10. Not a new model: it is the model every m9r gate ran. Docs updated (MODEL.md motor units, RUNNING.md examples, HANDOFF profile line).
- **flyapp timing.** flyapp's m9r library started on backhouse at 21:30:45 from its own copy (`/home/greff/flyapp`), before this fold reached main, so those recordings run m9r at the old default of 1 for the 71 leg motor neurons. Not touched (another worker's runs). For the Director: restart it after merging main at the fold commit, or label it pre-fold.

### Result of the Dandelion bracket (21:56; `runs/s12/dandelion/*.log`, `runs/assay-*-dand_{gaba,ach}/`, backhouse)

MN9_L in Hz, 3 trials each, GABA (as built) vs acetylcholine (`--nt AN13B002=acetylcholine`). All numbers are model outputs (derived).

| assay, stimulus | m2 GABA | m2 ACh | m9r GABA | m9r ACh |
|---|---|---|---|---|
| leg sugar (216 cells incl. LgLG3), 100 Hz | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 |
| labellar sugar, 100 Hz | 26 25 10 | 25 22 17 | 7 6 7 | 5 5 5 |
| labellar sugar 100 Hz + bitter 0 Hz | 27 13 19 | 23 30 30 | 6 4 5 | 7 5 6 |
| labellar sugar 100 Hz + bitter 100 Hz | 0 0 0 | 0 0 0 | 0 0 0 | 0 0 0 |

- (1) GABA, leg drive: MN9_L 0 Hz under both profiles. PASS (reproduces 05:02).
- (2) Acetylcholine, leg drive: MN9_L 0 Hz under both profiles, under the 5 Hz bound. PASS. Dandelion itself fires 294 to 320 Hz under leg drive with either sign, so the sign changes what it does downstream, not whether it is driven. With acetylcholine, 782 (m2) and 537 (m9r) more cells sit 2.5 Hz above their GABA-run rate, mostly its direct partners and their targets (IN01B065, IN00A031, leucokinin LK, AN09B004, ANXXX027, abdominal motor neurons MNad03/06); none of this reaches MN9.
- (3) Labellar sugar: m2 means 20.3 vs 21.3 Hz (+5%), m9r 6.7 vs 5.0 Hz (−25%). Both under 30%. PASS, but m9r's is close to the bound with 3 trials; read it as "small", not "none". Dandelion fires 41 to 78 Hz under labellar sugar alone.
- (4) Sugar + bitter at 100 Hz: 0 Hz under every condition, difference 0. PASS.
- **Reading.** The reading rule's trigger did not fire: the model's leg-sugar-to-MN9 failure does not hinge on Dandelion's sign. The sign does change the activity of several hundred VNC cells under leg sugar, so it matters for any readout downstream of Dandelion's partners (AN09B004, abdominal motor neurons), just not for PER.
- **Adopted: nothing.** The model keeps GABA, labelled inferred: transcripts for GABA are measured in hemilineage 13B (Lacin et al. 2019 FISH, ground-truth confidence 3), carried to this cell by lineage; EM classifiers predict GABA for it but are trained on lineage-level labels, so not fully independent. No cell-type measurement exists that the search found. The settling experiment is in `docs/research/s12_tarsal_per_pathway.md` and on HANDOFF's list for Ben.
- `scripts/assay_pathways.py --nt TYPE=TRANSMITTER` stays as a diagnostic option (sets sign and the transmitter label the GABA-B split reads, for the named types, in this run only).


## Pre-registration: the taste connectome's leg sugar route, and feedforward inhibition at Bract 2 (5 October, 22:04; Director 22:00, the by-eye comparison; diagnostic, nothing adopted)

- **The paper's route, read by eye** (Tastekin et al. bioRxiv 10.1101/2025.08.25.671814 v2, Figure 9B and text p. 20; PDF in `data/raw/tastekin2025/`, sha256 ef045ceb...): LgLG4 → AN01B004 (ascending, cholinergic) → Bract I and Bract II → Roundup → MN9, with a side branch AN01B004 → S&S → Roundup and S&S → MN9. "Multiple positive feedforward loops"; LgLG4 needs 7 hops for its maximum effective connectivity to feeding MNs, 2 more than most labellar GRNs.
- **Names in male-cns** (measured annotation: male-cns `synonyms` column): Bract 1 = DNge174, Bract 2 = DNge173, Roundup = GNG108 (all "Shiu 2022"). S&S has no synonym; by its edges it is GNG159 (inferred: AN01B004→42, Bract 2→40, →Roundup 184, →MN9 60 synapses, against the figure's thin/thin/medium/thin; GNG134 fits less well, →Roundup 69).
- **Weights agree** (derived, male-cns type sums): LgLG4→AN01B004 960 (figure about 925), AN01B004→Bract 1 378, →Bract 2 245, Bract 2→Roundup 319, Bract 1→Roundup 3, Roundup→MN9 381. The model has the paper's route; the s12 trace saw only its 3-hop part (AN01B004 in layer 1; GNG108/GNG159/GNG134 in layer 2).
- **Where it stops in the model** (m2, open loop, all 54 LgLG4+LgAG2 at 200 Hz, `runs/assay-legsugar_mn9-m2-s12`): AN01B004 16-74 Hz, Bract 1 10-11 Hz, Bract 2 0-2.5 Hz, Roundup 0, MN9 0. Under labellar sugar at 100 Hz Bract 2 reaches 40 Hz on one side and Roundup 13-37 Hz. Mean-drive split (derived: rate × synapses × sign × 0.275 mV × 5 ms, Shiu constants; threshold gap 7 mV): Bract 2 gets 9-10 mV excitation, 7-9 mV of it from AN01B004, and 4-9 mV inhibition from GNG093 and GNG250 (GABA predicted), which AN01B004 itself drives (280 and 572 synapses). Net 1-5 mV, below threshold. Roundup gets 0.6 mV.
- **Held-out check, qualitative** (Shiu et al. 2022 eLife 11:e79887, full text, `data/raw/shiu2022/`): Fdg (GNG588, synonym "Shiu 2022: Fdg") "did not respond to proboscis taste stimulation, but did respond to optogenetic activation of sugar-sensing GRNs", which the authors read as pharyngeal or leg input. Model: Fdg 0 Hz under labellar sugar, 1-6 Hz under leg sugar. Agrees in direction (not scored before; recorded as a post hoc observation, not a pass). No leg-sugar recording of Bract or Roundup exists in that paper (proboscis stimulation only).
- **Run.** `assay_pathways.py --silence-ids` with the 4 GNG093 + GNG250 cells (515718, 13937, 580188, 29520), against the same command without silencing. Assays `legsugar_mn9` (54 cells) and `legsugar3_mn9` (216 cells), profiles m2 and m9r, `--rates 0,100,200 --trials 3 --shuffles 0`. 8 runs, backhouse.
- **Predictions.** (1) Silencing raises Bract 2 (both cells, mean) to ≥ 10 Hz at 200 Hz under m2 (`legsugar_mn9`). (2) Roundup rises above 0 Hz under m2 at 200 Hz. (3) MN9_L: no prediction of the sign of the outcome beyond the reading rule.
- **Reading rule.** If silencing gives MN9_L ≥ 5 Hz under m2, feedforward inhibition at Bract 2 is the main block on the paper's route in the model, and the next questions are the transmitter and strength of GNG093 and GNG250 (measured or predicted) and the GRN rate. If Bract 2 fires but MN9_L stays under 5 Hz, the route is too weak in convergence along Bract 2 → Roundup → MN9 as well, and no single cell explains it. If Bract 2 does not reach 10 Hz, the mean-drive split is wrong and I write that up. Either way nothing changes in the model: silencing is a diagnostic, and the two earlier rescues stand as failed.

### Result (22:45; 8 runs, backhouse, `runs/assay-legsugar{,3}_mn9-{m2,m9r}-ffi_{base,sil}`, `runs/s12/ffi/*.log`)

Rates at 200 Hz GRN input, mean of 3 trials (Bract 2 and Roundup per cell; MN9_L per trial):

| assay, profile | arm | Bract 2 (Hz) | Roundup (Hz) | MN9_L (Hz) |
|---|---|---|---|---|
| legsugar_mn9 (54 cells), m2 | base | 0, 2.3 | 0, 0 | 0 0 0 |
| | silenced | 22.3, 10.0 | 1.3, 2.7 | 2 1 0 |
| legsugar_mn9, m9r | base | 0.3, 11.7 | 0, 0 | 0 0 0 |
| | silenced | 16.3, 25.3 | 0, 0 | 0 0 0 |
| legsugar3_mn9 (216 cells), m2 | base | 0, 7.3 | 0, 0 | 0 0 0 |
| | silenced | 21.7, 10.7 | 4.3, 10.3 | 15 3 6 |
| legsugar3_mn9, m9r | base | 0.3, 12.7 | 0, 0 | 0 0 0 |
| | silenced | 17.7, 25.0 | 1.3, 1.0 | 3 0 0 |

Read from each run's `rates.npz` (Bract 2 = 268258, 14157; Roundup = 26764, 523040). At 100 Hz every arm gives MN9_L 0 Hz and Roundup 0 Hz. The silenced cells (output removed, still simulated) fire at 200 Hz: 13937, 580188 and 29520 at 24-52 Hz, 515718 at 0-16 Hz.

- (1) Bract 2 ≥ 10 Hz under m2 with silencing (`legsugar_mn9`): 16.2 Hz (mean of 22.3 and 10.0). **PASS.**
- (2) Roundup above 0 Hz under m2 with silencing: 1.3 and 2.7 Hz. **PASS.**
- **Reading rule.** On the pre-registered 54-cell assay MN9_L stays under 5 Hz (mean 1 Hz), so the second branch applies: the route is too weak in convergence along Bract 2 → Roundup → MN9 as well. With LgLG3 added (216 cells, the paper's proposed sugar type), m2 silencing gives MN9_L 8 Hz mean (15, 3, 6; 2 of 3 trials ≥ 5 Hz), the first branch. Under m9r neither assay gets past Roundup (1 Hz with Bract 2 at 21 Hz, against 7 Hz with Bract 2 at 16 Hz under m2).
- **Reading.** The paper's route exists in the model and its feedforward inhibition at Bract 2 is a real block: removing GNG093 and GNG250 is necessary for any MN9 response to leg sugar in these runs. It is not sufficient under the 54 GRNs the paper matched to sugar, and under m9r a second block sits at Bract 2 → Roundup. Both blocks are in values the model guessed or fitted (GNG093 and GNG250 transmitter is predicted GABA; m9r's per-cell excitability), not in the wiring. Nothing adopted.
- **Next discriminating facts.** A measured transmitter or inhibitory effect for GNG093 and GNG250 (whether feedforward inhibition at Bract 2 exists in the animal); whether LgLG3 is a sugar type (the paper proposes it from connectivity alone); and why m9r's Roundup needs more drive than m2's (compare its per-cell threshold, membrane time constant and GABA-B load under the two profiles).

## Pre-registration: rung 8 step 1, short-term plasticity per connection class (5 October, 22:20; N29, Director night order item 3; diagnostic until the rule below says otherwise)

- **Data first** (Sonnet Explore agent, PMC full texts read by keyword, 22:05; then the decisive number read by me in the PMC text of Nagel & Wilson 2016 at 22:09). Two adult connections have a published short-term plasticity fit, both from 10 Hz antennal-nerve trains and the same single-component model (amplitude × f per spike, recovery τ): ORN→PN f 0.78, τ 893 ms (Nagel, Hong & Wilson 2015 Fig 1b-c, DM6 and VM2, n 19); ORN→LN f 0.75, τ 1566 ms (Nagel & Wilson 2016 J Neurosci 36:4325, Fig 6B legend, n 9). Qualitative only: LN→LN inhibition facilitates (same paper; no number). Searched without a usable number: PN→KC (Gruntman & Turner 2013 has none), KC→MBON baseline (Hige 2015 is long-term plasticity), PN→LHN, photoreceptor→LMC, JO→GF, GF→TTMn, DN→MN, leg afferent→VNC, GRN→second order. Larval NMJ (Peled & Isacoff 2011: median Pr 0.07, paired-pulse ratio 1.34-1.43 at 50 ms in low Ca/high Mg) is outside this model.
- **Mechanism** (`synapse:all|per_synapse_parameters` = 1; `lif._stp_connections`, `Network._stp_factor`). Tsodyks-Markram per edge (Markram 1998 form), updated lazily at each presynaptic spike; amplitude w·u⁺x/U, so w keeps its meaning at rest. With τ_facil 0 it is the published model with U = 1 − f (derived exactly). Table `data/params/stp_connections.csv`: ORN→class ALPN U 0.22, τ 893 ms; ORN→class ALLN U 0.25, τ 1566 ms; both **derived** (published fits to recorded EPSC trains; other glomeruli and LN subtypes inferred). These rows cover 56,261 edges (ORN→ALPN 16,234, ORN→ALLN 40,027), 90% of ORN output synapses at ≥ 5 synapses per edge. The other 12,051 ORN edges (ORN→ORN, ALBN, AL-AST1 and others) keep the per-cell rule, which m9r leaves off. Values above 1 (per-synapse weight, release probability, receptor mix, latency) raise NotImplementedError; the GPU port refuses the switch. Tests: `tests/test_stp_connections.py` (neutral builds nothing; equal to the per-cell rule at τ_facil 0; each edge follows its fit at 10 Hz; Markram paired-pulse ratio), 9 passed with the stub tests.
- **What changes under m9r.** The ORN-wide switch `afferent:ORN|measured_depression` is off in m9r (session 7: with the 11× measured unitary EPSP, PNs were overdriven; neither package adopted; F-AL-4). So switch 1 adds depression to ORN→PN and ORN→LN where today there is none. Derived steady state at the gate's mean ORN rate (11 Hz, regular train): resource 0.33 on PN edges and 0.19 on LN edges after about 2 s.
- **Runs.**
  1. Gate (`closed_loop_check.py`, m9r, seeds 12-19, plus the switch), backhouse, against the m9r gate `runs/s12/gates/cl_wm_s*.json`.
  2. Odour step (`scripts/probes/stp_al.py`, new): m9r, 1.5 s clean air then the most broadly activating DoOR odour at 1e-2 until 3.5 s; ORN, uPN and LN rates in 50 ms bins; switch 0 and 1, seeds 12-14, Mac.
- **Predictions.**
  1. Gate passes: 0 spikes/ms in the last 100 ms, no MuJoCo warnings and no NaN on all 8 seeds.
  2. uPN mean rate falls on every gate seed (m9r seed 12: 3.97 Hz), and AL_LN falls by a larger fraction than AL_PN (LN edges depress more, and LN→PN inhibition falls with them).
  3. Odour step: transience (late − base)/(peak − base) falls for uPNs and LNs on every seed, and with the switch LN transience is below uPN transience on every seed.
- **Held out.** uPN spontaneous rate "typically 1-5 spikes/s" (Kazama & Wilson 2009, qualitative). LN odour responses are more transient than PN responses (Nagel & Wilson 2016 Results, citing Nagel 2015; from odour recordings, not used in the fits).
- **Adoption rule.** Adopt into the working profile only if prediction 1 passes, the gate's uPN mean stays within 1-5 Hz on at least 6 of 8 seeds, and prediction 3's held-out ordering (LN more transient than PN) holds on all three seeds. Otherwise the switch stays built and off, labelled, and the failure is written up. My expectation, written now: the uPN mean falls below 1 Hz because PNs are already under-driven in m9r (median 0 Hz, 31% active), so the rung stays off. That would repeat F-AL-4 from the other side: measured depression needs the measured unitary strength, which needs per-class inhibition that is not yet fitted.

### Result (22:45; gate seeds 12-19 backhouse `runs/s12/stp/cl_stp_s*.json`; odour seeds 12-14 Mac `runs/s12/stp/al_*`; figure `runs/s12/stp/al_step.png`, viewed)

| gate seed | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|
| uPN mean, m9r → switch 1 (Hz) | 3.97 → 0.88 | 3.74 → 0.88 | 3.86 → 0.86 | 3.91 → 0.84 | → 0.84 | → 0.80 | → 0.82 | → 0.81 |
| AL_LN (Hz) | 1.80 → 0.51 | 1.72 → 0.52 | 1.77 → 0.49 | 1.63 → 0.54 | 1.72 → 0.54 | 1.62 → 0.51 | 1.62 → 0.50 | 1.65 → 0.50 |
| AL_PN (Hz) | 2.03 → 0.43 | 1.92 → 0.43 | 1.99 → 0.42 | 2.00 → 0.41 | 1.89 → 0.41 | 1.92 → 0.39 | 1.99 → 0.40 | 1.92 → 0.39 |

Silent last 100 ms 0 spikes/ms, 0 MuJoCo warnings, no NaN, thorax 0.546-0.550 mm on all 8. uPN fraction active 0.15-0.18 (m9r 0.31). AL_other rises 1.15-1.38 → 2.86-3.32 Hz (cells whose LN inhibition falls). Odour step, transience (late − base)/(peak − base), off → on: uPN 0.953 → 0.022, 0.931 → 0.049, 0.940 → 0.043; LN 0.958 → 0.066, 0.965 → 0.110, 0.985 → 0.067. With the switch on, uPN rates fall over the first 500 ms to about 0.5 Hz; the odour gives a 150 ms transient to about 3 Hz and the rate returns near baseline (switch off: sustained 13-14 Hz).

- (1) Gate passes on all 8 seeds. **PASS.**
- (2) uPN falls on every seed: **PASS.** AL_LN falls by a larger fraction than AL_PN: LN −67 to −72%, PN −78 to −80%. **FAIL** on all 8.
- (3) Transience falls for uPN and LN on every seed: **PASS.** Held-out ordering, LN below uPN with the switch: LN is above uPN on all 3 seeds. **FAIL.**
- **Adoption rule.** uPN within 1-5 Hz on 0 of 8 seeds (0.80-0.88 Hz); held-out ordering fails. **Switch stays built and off**, as expected when registered.
- **Mechanism (derived).** Depression is a per-spike multiplicative loss of resource: at the gate's ORN rate the PN edges sit at about a third of resting strength, so baseline ORN→PN drive falls by two thirds. The m9r ORN→PN weight was fitted without depression, so the two cannot be combined: the measured depression needs the measured unitary EPSP (11× the current weight, F-AL-4), and that overdrove PNs in session 7 because per-class inhibition is not fitted. Derived from the table (deterministic train, x_ss = 1/(1 + U·r·τ)): PN edges 0.32 of resting strength at 10.9 Hz ORN and 0.15 at 29.2 Hz, so ORN→PN drive under odour is 1.25× baseline (2.7× without depression); LN edges 0.19 and 0.08, 1.13×. LN edges depress more, yet AL_LN falls by a smaller fraction than AL_PN and LN transience stays above uPN transience. Why is not tested. Candidates: LNs lose LN→LN inhibition as LN rates fall, and LNs also get PN→LN input that is not depressed. LN→LN facilitation is in Nagel & Wilson 2016 qualitatively, without a number, and is not in the table.
- **What stays.** The per-connection STP machinery (`lif._stp_connections`, the measured table, 6 tests) is in place behind `synapse:all|per_synapse_parameters` = 1. N29 becomes **partial**: per-connection STP is built for the two measured adult connections; per-synapse weight, release probability, receptor mix and latency are not.
- **Next discriminating experiment.** The same odour step with ORN→PN at the measured unitary strength and STP together, with LN→PN GABA-A/B gains fitted to Olsen & Wilson 2008 lateral inhibition (held out: the Bhandawat 2007 PN dose-response). That is the step session 7 could not take.

## Pre-registration: whole-leg compression stiffness, a held-out check on the passive leg (5 October, 22:37; B26 data-first, Director night order item 3; diagnostic, nothing adopted)

- **Data** (B26 search, Sonnet agent 22:20; the numbers below read by me in the PMC full text, `data/raw/b24_b26_s12/PMC13310938.txt`). Oeftger, Moussian & Lehmann 2026 iScience 29:116404: decapitated living flies (ice anaesthesia, head and all legs but the left middle leg removed, body glued), the leg pushed against a tungsten force wire in 0.05 mm steps to 1.0 mm body displacement over 10 s, then unloaded. The leg is treated as a strut from coxa to pretarsus. Wild-type Canton S compression stiffness **13.1 ± 7.97 µN/mm** (mean ± SD, n 11; measured). Femur-tibia angle slope −3.3 to −5.3 °/µN across strains; coxa-trochanter +6.0 °/µN in wild type; tibia-tarsus −0.31 °/µN in wild type (measured). The authors note that active control through the femoral chordotonal organ may contribute: the flies were alive, so this is passive plus resting tone and reflexes.
- **What it checks.** B3's leg springs (Wang et al. 2025, measured in flies with silenced motor neurons, projected J^T K J; F-PASSIVE-2) were fitted to different data, so this is held out. B26 (cuticle compliance) stays absent either way: the angles change, so the compliance is in the joints, not the segments.
- **Run.** New probe `scripts/probes/leg_compression.py`: body only, m9r body switches (B2, B3, B6, B14 as the organism sets them), thorax held fixed in the air, all actuators at zero (the model's passive leg; no tone). Settle 0.5 s, then a force on the left middle leg's tarsus5 body along the line to the thorax-coxa joint, in steps 0.25, 0.5, 1, 2, 4, 8, 12 µN, 0.4 s each. Strut compression and the three joint angles at the end of each step.
- **Predictions.** (1) The model's passive leg is softer than the living leg: secant stiffness at 4 µN below 13.1 µN/mm. (2) Femur-tibia flexes under load (the strut shortens mainly there).
- **Reading rule.** Above 21 µN/mm (mean + SD): B3's projected springs are too stiff for a leg that includes active tone, and that is a finding against B3. Between 5 and 21: passive springs alone account for the living leg, which conflicts with Wang 2025's "passive torques ~70× below weight support" unless leg geometry makes the strut stiff; I check the geometry before reading it. Below 5: consistent; the measured number then becomes a target for the resting fly's tone (a closed-loop arm with the network, later), not a test of B3.

### Result (22:49; Mac, `runs/s12/legk/{m9r,m9r_locked,m9r_solo,m9r_solo_locked}.json`, figure `runs/s12/legk/legk.png`, viewed)

Four arms: tarsus free or locked (the lm tarsal joints held at their settled angles, the experiment's tarsus lies on the wire), other legs colliding or not (`--solo`; the experiment removed them). **Deviations from the registration**, both before scoring: the settle is 1.5 s, not 0.5 s (the passive leg was still moving at 0.5 s); and the first run collapsed at 0.25 µN because the probe called `mj_step` directly, which skips the coupled leg springs (B3 source 2, applied by `body.passive_hooks` in `Body.step`). The probe now calls the hooks every step. That was a probe bug, not a model result.

| force (µN) | 0.25 | 0.5 | 1 | 2 | 4 | 8 | 12 |
|---|---|---|---|---|---|---|---|
| compression, tarsus free (mm) | 0.044 | 0.114 | 0.453 | 0.865 | 1.080 | 1.213 | 1.264 |
| secant, tarsus free (µN/mm) | 5.6 | 4.4 | 2.2 | 2.3 | 3.7 | 6.6 | 9.5 |
| compression, tarsi locked (mm) | 0.036 | 0.079 | 0.195 | 0.526 | 0.953 | 1.130 | 1.150 |
| secant, tarsi locked (µN/mm) | 6.9 | 6.3 | 5.1 | 3.8 | 4.2 | 7.1 | 10.4 |

Strut at rest 1.692 mm (lm_coxa to lm_tarsus5 origins; the measured leg is 1.85 ± 0.02 mm long). The solo arms differ from these by under 0.02 mm. 0 MuJoCo warnings, no NaN, all four arms. Above about 1 mm the curve stiffens because joints reach their limits (tibia-tarsus −60° from 2 µN with the tarsus free; femur-tibia −77.2° from 8 µN locked; coxa-trochanter −100° at 12 µN), so the high-force secants measure the stops, not springs.

- The paper estimates stiffness as the loading slope over 0.2-0.9 mm displacement, not a secant. The model's slope over the same range (derived, between the force steps nearest 0.2 and 0.9 mm): tarsus free 2.4 µN/mm (1→2 µN), locked 4.0 µN/mm (1→4 µN). Measured 13.1 ± 7.97.
- (1) Secant at 4 µN below 13.1: 3.7 (free), 4.2 (locked). **PASS.** By the paper's own slope the model is 3-5× softer than the mean living leg and below the mean − 1 SD (5.1) as well.
- (2) Femur-tibia flexes under load: 19.6° → −41.9° (free) and → −64.6° (locked) by 4 µN, the largest change of the three joints once the tarsus is locked. **PASS.**
- Angle slopes at small load (0-0.5 µN, derived): femur-tibia −20.7 (free) and −19.4 (locked) °/µN against measured −3.3 to −5.3, so the model's femur-tibia is 4-6× more compliant; coxa-trochanter −3.6 (free) and −2.9 (locked) °/µN against measured +6.0 (the paper's sign convention for this angle is not matched to the model's, so only the magnitude compares: about half). Tibia-tarsus −13 to −19 °/µN free against −0.31 measured: not comparable, because the measured tarsus lies on the wire.
- **Reading rule:** below 5, so the result is consistent. A passive model leg is softer than a living leg with tone, reflexes and the femoral chordotonal organ's control, which the authors name as a likely contributor. B3 is not falsified. The measured 13.1 µN/mm and the femur-tibia slope become targets for resting tone in a later closed-loop arm with the network; that arm would also test whether the femur-tibia springs are too soft or the tone is missing.
- **Seen, not scored.** After unloading the leg does not return: coxa-trochanter stays at −71 to −89° against −39° at the start, while femur-tibia returns to 20-22°. The final contacts are lm_tibia and lm_trochanterfemur against `c_thorax` (and against `lf_trochanterfemur` when other legs collide). So the leg is wedged against the body by contact, a possible body issue for any posture with a strongly flexed coxa-trochanter. The living leg loses 72% of the loading work per cycle (measured, all strains, Data S8), so it also returns incompletely, but it is not wedged; not directly comparable.
- **B26 decision.** The compliance in both the living and the model leg is in the joints (the angles change), so this experiment does not need cuticle compliance. B26 stays absent.

## Why m9r blocks the leg sugar route at Roundup: analysis of the 22:45 runs, then a profile-ladder pre-registration (5 October, 23:05; Director 22:00, the live lead; diagnostic, nothing adopted)

**Post hoc analysis of existing runs** (`legsugar3_mn9` silenced arms, m2 and m9r, 200 Hz, mean of 3 trials; new probes `scripts/probes/cell_params_compare.py` and `scripts/probes/input_drive.py`, outputs `runs/s12/ffi/*.json`; Mac). Mean drive is derived (rate × final edge weight × τ_s, current synapses; it ignores spike timing, refractoriness and the intrinsic currents).

- **Roundup itself is the same cell in both profiles.** Its LIF constants are identical (cell_params_compare); m9r adds the rung-1 class-prior intrinsic currents, which raise the sustained rheobase by about 1 mV (M-current; derived from the gbar table).
- **Bract 2 → Roundup is the same.** Drive from DNge173 onto Roundup: m2 1.57 and 2.52 mV, m9r 2.91 and 1.69 mV. Bract 2 fires faster under m9r (17.7, 25.0 Hz against 21.7, 10.7), which offsets the DN release scale 0.85.
- **What differs is co-excitation from a GNG cluster.** Under m2 Roundup also gets 1.5-1.8 mV from GNG143, 0.5-0.8 mV from GNG167 and 0.5-0.7 mV from DNge059 (all cholinergic); under m9r 0.27-0.32, 0.17-0.37 and 0. Roundup net drive m2 1.1 and 4.9 mV (4.3, 10.3 Hz), m9r 1.6 and 2.0 mV (1.3, 1.0 Hz), against a threshold gap of 7 mV (firing is partly fluctuation-driven).
- **The cluster is a feedforward chain that is attenuated at every layer under m9r.** All its cells are silent at 0 and 100 Hz in both profiles and turn on only at 200 Hz. Main path by drive: leg GRNs → AN17A002 (ascending) → GNG588 and GNG578 (with GNG468, AN05B106) → GNG421, GNG318, GNG167, GNG143 → Roundup. Rates, m2 → m9r (mean of the two cells): AN17A002 114 → 71 Hz (0.62×), GNG468 25 → 14 (0.55×), GNG578 26 → 9 (0.34×), GNG588 18 → 10, GNG167 18 → 8, GNG143 11 → 2 (0.19×), DNge059 5 → 0, Roundup 7.3 → 1.2 (0.16×). AN05B106 does not follow (two of its four cells fire faster under m9r).
- **GNG093 and GNG250 transmitter (for the first block, at Bract 2).** Predicted GABA only: male-cns per-type confidence 0.847 and 0.801, BANC 0.84 and 0.91, FlyWire consensus GABA. Both are primary neurons (no hemilineage), so the hemilineage transcript evidence used for Dandelion does not apply. No ground-truth row and no measurement found. Tastekin et al. call GNG250 GABAergic on the same predictions. Lead not checked: the GNG split-GAL4 lines of Sterne et al. 2021 eLife 10:e71679.

**Pre-registration.** The attenuation starts at the first central layer and compounds, which points at something every cell has (the intrinsic currents, the central size rule or psp) rather than one class scale. The profiles between m2 and m9r differ in the brain by: m3 consensusNt and psp 0.157 mV; m4 monoamines off; m5-m7 DN release 0.70, MN_other input 1.3, latencies, motor size rule; m8 intrinsic currents; m9 DN release 0.85, MN_other 1.6, gustatory release 1.25, central size rule (exponent 1.0). m9w-m9r change the body and mechanosensor nerves only.

- **Runs** (backhouse, `assay_pathways.py --assay legsugar3_mn9 --rates 0,100,200 --trials 3 --shuffles 0 --silence-ids runs/s12/ffi/ids.txt`, tag `ladder_sil`): profiles m4, m7, m8, and m9r with `--set "cell_type:all|intrinsic_channels=0"`. With the two existing arms this gives m2 → m4 → m7 → m8 → m9r, and m9r without intrinsic currents.
- **Readout** at 200 Hz: Roundup mean of both cells over 3 trials; also AN17A002, GNG578, GNG143 and MN9_L. Roundup "passes" at ≥ 4 Hz (m2 7.3), "blocked" at ≤ 2 Hz (m9r 1.2), partial between.
- **Hypotheses and predictions.** H1, the intrinsic currents cause the attenuation: m4 and m7 pass, m8 blocked, m9r without intrinsic currents passes. H2, the class gains or size rules cause it: m7 or m9r without intrinsic currents blocked. H3, consensusNt or psp: m4 blocked. My expectation, written now: H1, because AN17A002 already loses 38% of its rate one synapse from the GRNs while gustatory release is 1.25× under m9r.
- **Reading rule.** Whichever step blocks Roundup is the step whose values decide the leg sugar route; its evidence label then decides what the route result means. If H1: the intrinsic currents for central cells are a class prior scaled by channel mRNA (inferred; fitted only on slow leg MNs, F-RUNG1), so the m9r block is in an inferred value, and the discriminating data are firing-rate-versus-current curves of one central GNG cell type. If more than one step blocks, I report the ladder and do not assign a single cause. Nothing changes in the model either way.
- **Addendum (23:09, before launching; after reading the m4, m7 and m9r-without-intrinsic arms, before m8 finished).** Two more arms without silencing (feedforward inhibition at Bract 2 intact): m7, and m9r with intrinsic currents off; same assay, rates and trials, tag `ladder_base`. Question: is feedforward inhibition at Bract 2 still a block once the cluster can ignite? Reading: MN9_L ≥ 5 Hz at 200 Hz without silencing means it is not a block in that profile. No hypothesis about the outcome.

### Result (23:14; all six arms complete, 3 trials each; `scripts/probes/route_rates.py`, `runs/s12/ffi/ladder_route_rates.json`; figure `docs/media/s12_legsugar_ladder.png`, viewed)

Feedforward inhibition silenced, 200 Hz, mean rates (Hz). Roundup is the mean of its two cells; MN9_L is the readout (MN9_R is incompletely traced).

| Arm | AN17A002 | Bract 2 (DNge173) | GNG578 | GNG143 | Roundup | MN9_L |
|---|---|---|---|---|---|---|
| m2 | 113.5 | 16.2 | 26.0 | 11.3 | 7.3 | 8.0 |
| m4 | 109.0 | 20.0 | 86.5 | 48.8 | 81.8 | 120.3 |
| m7 | 101.7 | 17.7 | 83.8 | 54.2 | 77.5 | 123.7 |
| m8 | 60.3 | 12.8 | 0 | 0 | 0 | 0 |
| m9r | 71.3 | 21.3 | 9.0 | 2.2 | 1.2 | 1.0 |
| m9r, intrinsic currents off | 119.8 | 25.7 | 82.0 | 49.3 | 76.5 | 130.7 |

- **H1 holds; H2 and H3 are rejected.** m4 and m7 pass, m8 is blocked, and m9r without intrinsic currents passes, so the rung-1 intrinsic currents alone cause the block. m8 blocks harder than m9r (cluster at 0 against 2-9 Hz); m9's gustatory release of 1.25 partly offsets it. Without intrinsic currents, m9r passes even at 100 Hz (Roundup 27.8, MN9_L 50).
- **Addendum arms (feedforward inhibition intact):** m7 gives Roundup 0 and MN9_L 0; m9r without intrinsic currents gives 1.2 and 0.3. So feedforward inhibition is still a block once the cluster can ignite. GNG093 and GNG250 inhibit the cluster as well as Bract 2: 430 synapses onto GNG588, 67 onto GNG143, 63 onto GNG167, 38 onto GNG578 and 471 onto Bract 2 (male-cns edge table; derived). GNG578 falls from 82-84 to 8-21 Hz when they are left on.
- **What the route needs in the model:** both blocks lifted. That means the feedforward inhibition off (its transmitter is predicted GABA only) and central intrinsic currents weaker than the class prior. Either alone leaves MN9_L at or below 1 Hz.
- **Not pre-registered; observation only.** m2 → m4 raises the cluster from 26 to 86 Hz and Roundup from 7 to 82. m3 (consensusNt, psp) or m4 (monoamine signs 0) does this, and the ladder cannot separate them. MN9_L at 120-130 Hz in the passing arms is far above any proboscis motor rate I have seen reported. It is not a fit target, and I take it to mean the route saturates once it ignites.
- **What it means.** In the working model the leg sugar → MN9 route is closed by two things: an inferred transmitter sign (feedforward inhibition) and the inferred central intrinsic currents (a class prior fitted only on slow leg motor neurons, then scaled by mRNA). The first data that would settle the second are firing-rate-versus-current curves from one central GNG type. The first that would settle the first are the transmitter of GNG093 and GNG250. Both go on Ben's list. Next, under the 23:12 pre-registration: which channel causes the block.

## Pre-registration: which intrinsic current blocks the leg sugar route under m9r (5 October, 23:12; written after reading the ladder arms m4, m7, m9r-without-intrinsic and two of three m8 trials at 200 Hz, all of which follow H1; diagnostic, nothing adopted)

Values under m9r (slow-MN fitted value ÷ slow-MN expression factor, × the cell's own mRNA factor at β 0.5; x g_L0): BK 7.87, A 2.81 (guessed prior), M 0.355 (guessed prior), T 0.248 (guessed prior), Kv2 0.219, h 0.046, SK 0.025, NaP 0.015 (guessed prior); Ca 1.0 per spike, τ 37.9 ms.

- **Runs** (backhouse; `assay_pathways.py --assay legsugar3_mn9 --profile m9r --rates 100,200 --trials 3 --shuffles 0 --silence-ids runs/s12/ffi/ids.txt`), one `--set` group per arm, tag `chko_<arm>`: `A` (A gbar 0), `BK`, `Kv2`, `SK`, `M`, `h`, `AHP` (BK, Kv2 and SK all 0), `subK` (A and M 0). T and NaP are inward currents; removing them can only lower excitability, so they are not tested.
- **Readout and rule** as in the ladder: Roundup (GNG108) mean at 200 Hz, ≥ 4 Hz passes, ≤ 2 Hz blocked; also AN17A002, GNG578, GNG143, MN9_L.
- **Reading rule.** A single-channel arm that passes names a channel that is necessary for the block. If only a group arm passes, the block is shared within the group. If no arm passes, the block needs channels from both groups, and I report it as distributed. The evidence label of the named channel (A and M guessed priors held in the slow-MN fit; BK, Kv2, SK and h fitted on slow MNs and scaled to central cells by mRNA, inferred) decides what Ben's settling measurement has to be. Nothing changes in the model either way.
- **Expectation, written now:** `A` and `subK` pass, and `BK` is partial. Reason: A at 2.8 × g_L0 is the largest subthreshold conductance and it opens near threshold, so it shunts summed EPSPs at every hop; BK is large but brief (τ 3 ms) and mostly caps the top rate.
- **Addendum (23:15, before launching; ladder observation, not the knockouts).** One more ladder arm: m3 with the feedforward inhibition silenced (same assay, `--rates 100,200`, tag `ladder_sil`). It splits the unexplained m2 → m4 rise (Roundup 7 → 82 Hz). If m3 passes (Roundup ≥ 4 Hz at 200 Hz, cluster near m4), consensusNt or psp caused the rise; if m3 is near m2, the monoamine signs (m4 sets them to 0) did. No expectation.

### Result (23:26; all eight arms and the m3 arm complete, 3 trials each; `runs/s12/ffi/chko_route_rates.json`; figure `docs/media/s12_legsugar_chko.png`, viewed)

Roundup (mean of 2 cells) and MN9_L at 200 Hz, feedforward inhibition silenced, m9r: as is 1.2 and 1.0; A off 1.7 and 2.0; M off 2.0 and 2.0; h off 1.0 and 1.0; SK off 0.7 and 0.3; Kv2 off 2.0 and 2.3; **A and M off 4.2 and 3.7**; **BK off 31.5 and 48.0** (MN9_L 52, 36, 56 per trial); **BK, Kv2 and SK off 69.5 and 120.3**; all rung 1 off (ladder) 76.5 and 130.7.

- **BK is necessary for the block.** BK off alone passes. With all three spike-triggered potassium currents off, the route is almost back to rung 1 off. Kv2 and SK alone change nothing, but they add to BK (31.5 → 69.5 Hz). A and M together pass only at the threshold (4.2 Hz; MN9_L 3.7), and neither alone passes.
- **My expectation was wrong.** I wrote that A and subK would pass and BK would be partial. A alone is blocked, subK is marginal, and BK passes.
- **Why, at the single-cell level** (`scripts/probes/central_fi.py`, `runs/s12/ffi/central_fi_m9r.json`, figure `docs/media/s12_central_fi.png`, viewed; one unconnected cell with Roundup's constants and the m9r class prior, no noise; derived). Rheobase is unchanged: every arm starts firing at 8 mV of drive. BK roughly halves the gain above it: 95 Hz at 40 mV with every channel on, 155 with BK off, 167 with rung 1 off. 50 against 92 Hz at 20 mV. A, M, h, SK and Kv2 each change the mean rate over the step by 6% or less. A relay whose input rate is halved at every hop fails over the 5-7 hops of this route, and the input stays near threshold on the way.
- **Evidence label of the cause.** BK's value is 8.69 × g_L0 at the slow tibia flexor class, fitted to Azevedo 2020 current steps ("strong in 3 of 4 seeds", DECISIONS 2026-09-30 21:17), divided by the slow-MN slo expression factor (1.104). Every cell on this route has no transcriptome row, so it takes that value unscaled (7.87; `runs/s12/ffi/cluster_params_m7_m9r.json`). So the block rests on a value fitted to one motor neuron class and carried to central GNG interneurons by a class prior (inferred). Whether central GNG neurons have a fast AHP this strong is not measured in the project's sources. A search for central-neuron current-step data is running (5 October 23:18).
- **m3 addendum.** m3 passes (Roundup 84.3, MN9_L 124.7), the same as m4. So the m2 → m4 rise comes from m3 (consensusNt or psp 0.157 mV), not from the monoamine signs. The two are not separated.
- Nothing in the model changes. The discriminating data, for Ben's list and for the running search: current steps in one central GNG type (or any adult central neuron with a published f-I curve and AHP), to set BK for central cells separately from motor neurons.

## Pre-registration: does the clock drive reproduce DN1p day-night firing? (5 October, 23:34; written before the baseline probe returned)

Data (read, `docs/research/s12_central_fi.md`): wild-type DN1p "fire at ∼10Hz in the morning (Zeitgeber
Time, ZT0-4) and are nearly silent in the evening (ZT8–12)"; *per*⁰¹ DN1p fire 2.2 ± 1.1 Hz (ZT0-4) and
3.9 ± 1.5 Hz (ZT8-12) with no rhythm (Flourakis et al. 2015 Cell, brain explant). The model drives
DN1pA/DN1pB (with s-LNv, l-LNv) by `g_clock_mv` × cos(2π(ct − 2 h)/24), `g_clock_mv` 3 mV (guessed).

- **Probe:** `scripts/probes/clock_phase_rates.py`, brain only, open loop, profile noise, 1 s per phase,
  clock set to CT 2 (inside ZT0-4) and CT 10 (inside ZT8-12), entrained so ZT = CT. Readout: mean rate of
  the DN1pA and DN1pB cells.
- **Pass rule:** DN1p mean 5-20 Hz at CT 2 (about 10 Hz; a factor of 2 either way for the explant-to-model
  transfer, inferred), and ≤ 1 Hz at CT 10 (my reading of "nearly silent", inferred).
- **Prediction, written now:** m9r fails. At CT 2 the clock adds 3 mV, under the 7 mV class threshold
  gap, so DN1p sit below 1 Hz at both phases unless the profile's noise does it.
- **If it fails, the fit:** one number, `g_clock_mv`, set so the DN1p mean is 10 Hz at CT 2 (the single
  target), searched on a grid with the same probe. Held-out checks: CT 10 ≤ 1 Hz, and DN1p at
  `g_clock_mv` 0 (a clock-less cell, a loose stand-in for *per*⁰¹) between the CT 10 and CT 2 rates. The
  evening group gets the same gain (inferred transfer; no evening-cell rates were read). Adoption only
  as a new profile with the battery passing and a contact sheet viewed; `peak_morning_h` stays 2 h.

### Result of the probe and the fit (23:40; backhouse, `runs/s12/clock/m9r*.json`; figure `docs/media/s12_clock_dn1p_grid.png`, viewed)

| `g_clock_mv` (mV) | 0 | 3 (m9r) | 6 | 7.0 | 7.25 | 7.5 | 7.75 | 8 | 10 | 12 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DN1p at CT 2 (Hz) | 0 | 0 | 0 | 0 | 0 | 1 | 11 | 14 | 23 | 29.8 | 38 |
| DN1p at CT 10 (Hz) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- **Prediction held: m9r fails.** Every clock cell is silent at both phases; the clock drive never reaches
  spiking in the working model. All 12 DN1p cells fire identically (no noise reaches them, no network
  input of note), and s-LNv and l-LNv follow the same curve. The onset is steep: 1 Hz at 7.5 mV, 11 Hz at
  7.75 mV.
- **Fit:** `g_clock_mv` 7.75 (11 Hz at CT 2; the grid point closest to 10 Hz). Held out: CT 10 is 0 Hz
  (≤ 1 Hz, **pass**). Clock-less DN1p (gain 0) are silent, which is "between" 0 and 11 Hz only in a
  degenerate way; *per*⁰¹ DN1p fire 2.2-3.9 Hz, so the model's clock-less cell does not match (recorded as
  a mismatch: a baseline drive plus a smaller swing would fit all three, a two-number fit not
  pre-registered here).
- **Fragility, derived from the grid:** 0.25 mV moves DN1p from 1 to 11 Hz, so the fitted rate holds only
  while nothing else changes their input. Any later change to central excitability must re-run this probe.

## Addendum: candidate m9c (23:40; before any gate run)

m9c = m9r + `state:coupling|clock_gain` 7.75 (fitted above) + `state:clock|initial_ct` 1.5 (new key,
default 0 keeps m4-m9r; the male-cns specimen was dissected at ZT 1.5 in 12:12 LD, Nern et al. 2024
Methods, read; ZT = CT under entrainment, inferred). Why both: with the fit alone, every run starts at
CT 0, where the morning drive is 7.75 × cos(2π·2/24) = 6.7 mV, under the 7.5 mV onset, so the fit would
change nothing. At CT 1.5 it is 7.68 mV.

- **Runs (backhouse):** (1) the probe at CT 1.5 with gain 7.75; (2) gate `closed_loop_check.py`, seeds
  12-19, `FLYEMU_PROFILE=m9c`, against the m9r gate `runs/s12/gates/cl_wm_s*.json`, plus m9r seed 12
  re-run now as a same-code control; (3) the test battery with `FLYEMU_PROFILE=m9c`; (4) contact sheet,
  seed 12, viewed.
- **Predictions:** (1) DN1p 1-11 Hz at CT 1.5. (2) Gate passes on all 8 seeds (silent last 100 ms, no
  MuJoCo warnings, no NaN); the silent phase removes the clock drive with the senses, so it cannot fail
  on clock cells. Whole-brain rate within 10% of m9r; the morning types fire; posture (thorax height)
  within 0.01 mm of m9r. (3) Battery: no new failures beyond the known backhouse raw-data path check.
- **Adoption rule:** adopt m9c as the working profile only if (2) and (3) pass and the sheet shows no
  posture change. Otherwise m9c stays a named candidate, written up.

### Result: m9c adopted (23:53; backhouse `runs/s12/clock/m9c.json`, `cl_m9c_s12..19.json`, `cl_m9r_s12.json`, `pytest_battery_m9c.log`; sheets `runs/s12/clock/census_m9{c,r}_s12.png`, both viewed)

- **(1) Probe at CT 1.5:** DN1pA/DN1pB 4.2 Hz, s-LNv and l-LNv 4.0 Hz, evening group 0. Within the
  predicted 1-11 Hz. At CT 10 the evening group fires (LNd_b 9, LNd_c 11, 5thsLNv_LNd6 8 Hz) and the
  morning group is silent.
- **(2) Gate, seeds 12-19: pass on all 8.** Silent last 100 ms 0 spikes/ms, 0 MuJoCo warnings, no NaN.
  - Whole brain 0.325-0.330 Hz against m9r 0.325-0.329.
  - uPN 3.67-3.97 and motor 2.02-2.11 Hz, the same ranges as m9r.
  - Thorax height 0.547-0.552 mm, within 0.001 mm of m9r seed for seed.
  - The clock class rises from 0 to 0.98-1.25 Hz; that class is 32 cells, 12 of them DN1p, so DN1p fire
    about 3-4 Hz (derived).
  - Apart from `clock`, the only class that moves is optic_other (0.036 to 0.040 Hz, seed 12).
  - The m9r seed 12 control re-run is identical to the archived m9r gate.
- **(3) Battery, `FLYEMU_PROFILE=m9c`:** 211 passed, 12 skipped, 1 failed. The failure is the known
  backhouse raw-data path check (`data/raw/door/units/`). No new failures.
- **(4) Sheet:** m9c and m9r seed 12 look the same, and their census JSONs agree in all 436 values
  except the profile name. The clock cells reach no motor neuron within 600 ms.
- **Adopted:** `WORKING_PROFILE` m9c. flyapp's library was started on m9r. It differs only in the clock
  drive, which changes no motor output in these runs. Whether to relabel or restart it is the Director's
  call; I have not touched it.
- **Not done:** *per*⁰¹ (2-4 Hz with no rhythm) is not matched: the model's clock-less DN1p is silent. The
  fit is fragile: a 0.25 mV change takes DN1p from 1 to 11 Hz, so any later change to central
  excitability must re-run `clock_phase_rates.py`.

## Pre-registration: does the class-prior BK give a central cell the right f-I gain? MBON-α3 (5 October, 23:56; before any model run of this cell)

Why: the leg sugar route opens only with BK off (23:26), and BK off on central cells could be argued as
a fix. MBON-α3 (male-cns MBON14, 4 cells, no transcriptome row) carries the same class-prior channels as
the route's cells, and it is the one adult central cell with a published current-step f-I.

- **Data.**
  - Hafez et al. 2023 eLife 12:e77578, Fig. 1 supp. 1C, figure estimate (my reading, ±1 Hz, ±1 pA).
    These are 400 ms steps, −26 to +32 pA in 2 pA increments, ex vivo.
    - Onset: cell 1 at +2 pA, cell 2 at −6 pA, cell 3 at −2 pA.
    - Rate at +32 pA: 20, 50 and 30 Hz.
    - Slope above onset: 0.67, 1.32 and 0.88 Hz/pA.
  - "spike-frequency adapting neuron" (read).
  - Soma spikes 4-6 mV (supp. 1D, figure estimate).
  - Passive values: Rm 926 ± 55 MΩ and τm 16.06 ± 2.3 ms in four other cells (read). The f-I cells' own
    deflection at −10 pA is about −17, −17 and −25 mV (supp. 1E, figure estimate), i.e. 1.7-2.5 GΩ.
  - Gouwens & Wilson 2009 (PN model, read): "a voltage step at the soma declines to ∼40–70% of its
    original amplitude at the predicted spike initiation zone". MBON-α3 soma spikes are as small as PN
    soma spikes, so a similar transfer is assumed (inferred).
- **Model mapping, derived.** The model's drive is steady depolarisation at a single compartment, read as
  the spike initiation zone. Current maps to drive as I × Rin × k.
  - Primary: Rin 1.7 GΩ (the f-I cells' own) × k 0.55 gives 0.94 mV/pA.
  - Corners: 0.926 × 0.4 = 0.37 mV/pA up to 2.5 × 0.7 = 1.75 mV/pA. That is a factor of about 1.9
    either way around the primary.
  - The model cell is calibrated so that its passive deflection at −10 pA equals −10 pA × the mapping,
    separately in each arm.
- **Probe:** `scripts/probes/central_fi.py --cell-type MBON14`. It takes the model's own MBON14 constants
  under m9c (τm, rest, threshold, reset, refractory period, spontaneous drive) and the profile's channels
  at their mRNA factor. It applies the paper's protocol with no noise and no synapses.
  - Arms: m9c as is; BK off; rung 1 off. The cell constants are held fixed in every arm, so each arm
    is a knockout.
  - Readout: onset current, rate at +32 pA, and slope (rate at +32 pA over 32 pA minus the onset).
- **Pass rule:** under the primary mapping the slope lies within 0.35-2.5 Hz/pA. That is the measured
  0.67-1.32 range widened by the 1.9 mapping factor. Rate at +32 pA is reported, not scored.
- **Prediction, written now:** m9c as is fails high or sits at the top edge (generic central cell about
  3 Hz/mV, so about 2.8 Hz/pA). BK off fails high (about 4.7 Hz/pA) at every mapping corner.
- **Reading, fixed in advance:** if BK off fails high at every corner, the data argue against removing
  central BK. The leg sugar block then needs another explanation (synaptic drive, state, missing cells).
  If m9c passes, the class prior is consistent with the one central cell measured. Nothing is adopted
  either way: one cell type, ex vivo, a soma recording, and figure estimates.

### Result (23:58; Mac, `runs/s12/ffi/mbon14_fi_m9c{,_lo,_hi}.json`; figure `docs/media/s12_mbon14_fi.png`, viewed)

The model's MBON14 cells carry generic constants: τm 20 ms, rest −52 mV, threshold gap 7 mV, refractory
period 2.2 ms, no spontaneous drive, class-prior channels (mRNA source 0). All 4 cells are identical.

| Mapping (mV/pA) | Arm | Onset (pA) | Rate at +32 pA (Hz) | Slope (Hz/pA), as registered |
|---|---|---|---|---|
| primary, 0.98 | m9c as is | +8 | 77.5 | **3.23 (FAIL high; band 0.35-2.5)** |
| primary, 0.98 | BK off | +8 | 127.5 | 5.31 |
| primary, 0.94 | rung 1 off | +8 | 132.5 | 5.52 |
| low corner, 0.39 | m9c as is | +20 | 30 | 2.50 |
| low corner, 0.39 | BK off | +20 | 42.5 | 3.54 |
| high corner, 1.84 | m9c as is | +4 | 132.5 | 4.73 |
| high corner, 1.84 | BK off | +4 | 200 | 7.14 |
| measured (3 cells) | | −6 to +2 | 20-50 | 0.67-1.32 |

- **Prediction held: m9c fails high** under the primary mapping, at 3.23 Hz/pA. The predicted figure
  was about 2.8.
- **BK off fails high at every corner** (3.5-7.1 Hz/pA against 0.67-1.32), as predicted.
- **Post hoc** (not registered): at the low corner the registered slope is inflated, because the span
  above onset is only 12 pA. Matched to onset, the model rises 30 Hz over its first 12 pA with BK
  (2.5 Hz/pA) and 42.5 Hz without. The recorded cells rise 10-17 Hz (0.8-1.4 Hz/pA). So even under the
  mapping most favourable to the model, its gain above onset is about 2-3× the recording with BK and
  3-4× without.
- **Seen, not scored:**
  - The model cell does not adapt over 400 ms: the last 100 ms equals the first 100 ms at every
    current. MBON-α3 "is a spike-frequency adapting neuron" (read). Its traces (supp. 1A-B) show
    roughly even spike trains at high current, so the adaptation is modest.
  - The recorded cells start firing at −6 to +2 pA and rise gradually from 0. Hafez also reports
    spontaneous firing at 12.1 Hz (read, other cells). The model cell needs 4-20 pA and jumps to
    12-23 Hz at onset, because it sits 7 mV below threshold with no noise.
- **Reading, as fixed in advance:** the one measured central cell argues against removing central BK.
  Its gain is already lower than the model's with BK. So BK off is not a biological fix for the leg
  sugar block. If anything, central gain is too high and adaptation is missing.
  The mismatch that does point towards the route is resting excitability. The real cell sits at or
  near threshold at rest and relays small inputs. The model cell sits 7 mV below threshold with a steep
  onset, which makes it a threshold device. That reasoning about the route is inferred, not tested. It
  is one cell type, and its spontaneous rate is not shared by every central cell (Frechter 2019:
  LHONs 0.1 Hz, PNs 1.4 Hz, read).
- **Next discriminating experiment (not run):** pre-register the leg sugar route with route cells set
  nearer threshold, as a bracket bounded by measured central resting rates. Keep BK on and the
  feedforward inhibition intact. Read Roundup and MN9_L. If the route passes there and not at m9c, the
  block is resting excitability, which has a measurable counterpart: resting rates of GNG cells.
  Nothing adopted.

## Pre-registration: does resting excitability block the leg sugar route? A route bracket nearer threshold (6 October, 00:05; diagnostic, nothing adopted)

Why: F-FI-1 rules out central BK as the fix. The remaining candidate is resting excitability. Under m9c every
route cell sits 7 mV below threshold with no noise. Recorded central cells rest nearer threshold:
MBON-α3 fires at 12.1 Hz at rest (Hafez 2023), and PNs, LH local and LH output neurons at 1.4, 1 and 0.1 Hz
(Frechter 2019) (all read).

- **Route cells** (43 cells, 17 types; `scripts/probes/route_rest.py`, `ROUTE`):
  - the paper's route: AN01B004, Bract I and II (DNge174, DNge173), Roundup (GNG108), S&S (GNG159);
  - the co-exciting cluster from the ladder: AN17A002, GNG588, GNG578, GNG468, AN05B106, GNG421, GNG318,
    GNG167, GNG143, DNge059;
  - the feedforward inhibitors GNG093 and GNG250, raised with the rest so the test does not favour a pass.
  - MN9 and the GRNs are unchanged.
- **Single-cell calibration** (derived; m9c, each cell's own constants and channels, no synapses, 1 s;
  `runs/s12/rest/route_rest_m9c.json`): rheobase 7.70 mV of drive (AN01B004 8.05, AN05B106 7.55).
  - The onset is steep: 2 Hz at rheobase, 10 Hz 0.05 mV above, 12 Hz at 7.85 mV.
  - So a deterministic model cell cannot rest at 0.1-4 Hz except on a knife-edge.
- **Arms** (one `spontaneous_drive` row per cell through `FLYEMU_EXTRA_PARAMS`, files
  `runs/s12/rest/route_{near,tonic2,tonic12}.csv`, labelled guessed):
  - `base`: m9c as is.
  - `near`: 1 mV below each cell's rheobase. Silent in isolation; stands for the 0.1-1.4 Hz cells.
  - `tonic2`: at rheobase, about 2 Hz in isolation (1-4 Hz cells).
  - `tonic12`: 12 Hz in isolation (MBON-α3).
- **Runs** (backhouse): `assay_pathways.py --profile m9c --rates 0,100,200 --trials 3 --shuffles 0`.
  - Run on both leg sugar assays: `legsugar_mn9` (the 54 paper-matched GRNs) and `legsugar3_mn9`
    (216 cells, with LgLG3 proposed).
  - Feedforward inhibition and BK stay on. Tag `rest_<arm>`.
- **Readout:**
  - Roundup (GNG108, mean of 2 cells) and MN9_L at 0 and 200 Hz.
  - Each route type's rate at 0 Hz input, which is the achieved resting rate in the network.
- **Pass rule.** The route passes when all three hold:
  - Roundup ≥ 4 Hz at 200 Hz and at least 4 Hz above its own 0 Hz rate;
  - MN9_L ≥ 5 Hz at 200 Hz;
  - MN9_L ≤ 2 Hz at 0 Hz.
  - A failure of the last condition is "fires at rest". That is a failure too: no proboscis extension
    without sugar.
  - Blocked means Roundup ≤ 2 Hz at 200 Hz.
- **Expectation, written now** (low confidence):
  - `base` is blocked on both assays.
  - `near` passes Roundup on `legsugar3_mn9` but MN9_L stays under 5 Hz.
  - `tonic12` fires at rest: Roundup at 12 Hz drives MN9_L above 2 Hz at 0 Hz input.
- **Reading rule.**
  - If `near` or `tonic2` passes and `base` does not, resting excitability on the route is enough to open
    it with the feedforward inhibition intact. The measurable counterpart is the resting potential
    against threshold, or the spontaneous rate, of a GNG route cell (Roundup or Bract patch); that goes on
    Ben's list.
  - If only `tonic12` passes, the route needs tonically firing relays, and its rest condition decides
    whether that is plausible.
  - If no arm passes, resting excitability alone does not open the route against the feedforward
    inhibition. The GNG093/GNG250 sign is then the deciding unknown.
  - Nothing is adopted either way. A route-only shift is not a model candidate: as a model change it
    would have to be a class property, tested on the whole brain and the gate.

### Result (00:22; 8 runs, 3 trials each, backhouse; `runs/s12/rest/route_rest_rates.json`; figure `docs/media/s12_legsugar_rest.png`, viewed)

Mean rates (Hz). Roundup is the mean of its 2 cells. At 0 Hz input the 3 trials are identical, because
there is no noise.

| Assay | Arm | Roundup, 0 Hz | Roundup, 100 Hz | Roundup, 200 Hz | MN9_L, 0 Hz | MN9_L, 100 Hz | MN9_L, 200 Hz | Verdict |
|---|---|---|---|---|---|---|---|---|
| 54 GRNs | base | 0 | 0 | 0 | 0 | 0 | 0 | blocked |
| 54 GRNs | near | 0 | 32.5 | 34.8 | 0 | 35.0 | 39.0 | **PASS** |
| 54 GRNs | tonic2 | 38.0 | 39.2 | 43.3 | 42.0 | 41.7 | 49.0 | fires at rest |
| 54 GRNs | tonic12 | 37.0 | 41.2 | 43.8 | 41.0 | 44.7 | 50.7 | fires at rest |
| 216 GRNs | base | 0 | 0 | 0 | 0 | 0 | 0 | blocked |
| 216 GRNs | near | 0 | 31.3 | 33.5 | 0 | 32.0 | 34.0 | **PASS** |
| 216 GRNs | tonic2 | 38.0 | 38.7 | 39.3 | 42.0 | 40.7 | 43.3 | fires at rest |
| 216 GRNs | tonic12 | 37.0 | 39.2 | 39.5 | 41.0 | 40.7 | 43.7 | fires at rest |

- **Predictions:**
  - `base` blocked on both assays: held.
  - `tonic12` fires at rest: held.
  - `near` passes Roundup only on the 216-cell assay and leaves MN9_L under 5 Hz: wrong. `near` passes
    on both assays, including the 54 GRNs the paper matched to sugar, with MN9_L at 32-39 Hz.
- **Reading, as fixed in advance:**
  - `near` passes and `base` does not. So resting excitability on the route is enough to open it, with
    BK on and the feedforward inhibition intact.
  - The inhibitors fire hard in `near` (GNG093 48 Hz, GNG250 54 Hz at 200 Hz) and the route still opens.
    So the inhibition is not the deciding block once the relays sit near threshold.
  - The measurable counterpart is the resting potential against threshold, or the spontaneous rate, of a
    GNG route cell. It goes on Ben's list.
  - Nothing is adopted.
- **Seen, not scored:**
  - **The route switches rather than grades.** Under `near`, Roundup and MN9_L are nearly the same at
    100 and 200 Hz (32.5 against 34.8, and 35 against 39). The cluster (GNG578, GNG143, GNG167) runs at
    26-42 Hz at both rates.
  - **The route cells excite one another.** Under `tonic2`, each cell fires about 2 Hz alone but 30-40 Hz
    in the network at rest (GNG167 39, Roundup 38). Under `near` with 54 GRNs, the cluster ignites
    while AN17A002 fires only 4-8 Hz (60-83 Hz on the 216-cell assay).
  - So near threshold the route behaves as a recurrent switch. Whether it switches off when the sugar is
    removed is untested. Real PER is graded with concentration and ends when the stimulus ends (not
    sourced this session).
  - Bract 2 (DNge173) never exceeds 11 Hz in any arm, while Bract 1 (DNge174) reaches 31-41 Hz. So
    Roundup is probably driven through the cluster and Bract 1 rather than Bract 2 (inferred from rates,
    not tested by removing cells).
  - **Without noise, the low resting rates are a knife-edge** (`scripts/probes/noise_rest.py`,
    `runs/s12/rest/noise_rest_m9c.txt`; one generic central cell, derived). m9c has no membrane noise
    (Shiu 2024 has none). Rates in the alone column below are for one cell with no synapses:

    | Noise (mV/√ms) | Rate alone at 0 mV drive | Rate alone at 4 mV drive | Membrane SD |
    |---|---|---|---|
    | 0.75 | 0.1 Hz | 9 Hz | 2.3-2.9 mV |
    | 1.0 | 1.8 Hz | 11 Hz | 2.9-3.3 mV |
    | 1.5 | 7.6 Hz | 16 Hz | 3.9-4.0 mV |

    So noise reaches the measured 0.1-12 Hz range smoothly, as tonic drive alone cannot.
- **Next discriminating experiments** (pre-register before running):
  1. Specificity under `near`. Leg bitter alone (LgAG1, new assay `legbitter_mn9`) should leave MN9_L
     silent. Leg bitter on top of leg sugar (`legsugar_legbitter_mn9`) should give at most moderate
     suppression: optogenetic Gr66a activation on legs and proboscis reduces PER by 22% (French et al.
     2015 J Neurosci 35:3990, PMC6605581, Fig. 3; secondary read). Labellar sugar, bitter and sugar +
     bitter should be unchanged from `base`.
  2. Dose and offset under `near`: GRN rates 3, 10, 25 and 50 Hz (tarsal sugar GRNs fire under 3 Hz
     spontaneously and about 50-55 Hz at 100 mM; Ling 2014), and whether MN9_L stops after the
     stimulus.
  3. A noise version: route cells (or the whole central class) resting at 0.1-1.4 Hz through membrane
     noise instead of a fixed drive. Then the whole-brain question: does a class-level change pass the
     gate?

## Pre-registration: under the `near` arm, is the opened leg sugar route specific, graded and does it stop? (6 October, 00:26; diagnostic, nothing adopted)

**Question.** The `near` arm opens the leg sugar route (result above). Is that a model of tarsal PER or just
a hair trigger? Three questions:
- Does the opened route stay silent for bitter?
- Does it grade with GRN rate, or fire at spontaneous GRN rates?
- Does it stop when the sugar is removed?

**Setup.** As above: m9c, open loop, 3 trials, 1000 ms per trial, no shuffles. `near` is the m9c profile
plus `runs/s12/rest/route_near.csv`, the same file. `base` is plain m9c. Backhouse tmux `s12spec_*`; tags
`rest_base` and `rest_near`.

| Run | Assay | Arms | Rates (Hz) | Pass rule (`near`) | Basis of the rule |
|---|---|---|---|---|---|
| S1 | `legbitter_mn9` (LgAG1, 25 tarsal bitter GRNs) | base, near | 0, 100, 200 | MN9_L ≤ 2 Hz at 100 and 200 | expected by analogy with labellar bitter, which does not drive MN9 (Shiu 2024); no leg-specific source this session |
| S2 | `legsugar_legbitter_mn9` (leg sugar held at 100 Hz; leg bitter swept) | near | 0, 100, 200 | MN9_L at 200 Hz bitter ≤ MN9_L at 0 Hz bitter + 3 Hz (bitter does not raise it) | French et al. 2015: optogenetic Gr66a activation on legs and proboscis reduces PER by 22%, "only a moderate inhibition" (secondary read). The magnitude is reported, not scored: an optogenetic PER fraction does not map to a MN9 rate. |
| S3 | `bitter_mn9` (labellar LB1a-d) | base, near | 0, 100, 200 | MN9_L ≤ 2 Hz at 200 | Shiu 2024 |
| S4 | `sugar_mn9` (labellar LB3b/c) | base, near | 0, 100, 200 | MN9_L ≤ 2 Hz at 0 Hz and ≥ 5 Hz at 200 Hz | MN9 drives proboscis extension and labellar sugar drives it (Shiu 2024) |
| S5 | `sugar_bitter_mn9` (labellar sugar held at 100 Hz; bitter swept) | base, near | 0, 100, 200 | MN9_L at 200 Hz bitter ≤ half its 0 Hz bitter value, or ≤ 2 Hz | bitter suppresses sugar-evoked MN9 (Shiu 2024, predicted and confirmed) |
| D1 | `legsugar_mn9`, with the new `--off-ms 1000` (1 s with no stimulus after each trial) | near | 3, 10, 25 and 50, 100, 200 (two runs) | MN9_L ≤ 2 Hz at 3 Hz input | tarsal sugar GRNs fire under 3 Hz spontaneously (Ling 2014), so spontaneous GRN activity must not trigger extension |

- **D1 observations:**
  - the lowest input rate at which MN9_L reaches 5 Hz, against 50-55 Hz for tarsal sugar GRNs at 100 mM
    sucrose (Ling 2014);
  - whether MN9_L rises with input rate (graded) or jumps (switch);
  - MN9_L in the 1 s after the stimulus. If MN9_L is 5 Hz or more after the stimulus ends, the route
    **latches**: a bistable switch that stays on.
- **My expectations, written now:**
  - S1 and S3 pass.
  - S2 changes MN9_L by less than 5 Hz, because the route switches.
  - S4 under `near` is higher than under `base`.
  - S5 fails under `near`: once the cluster ignites, bitter no longer halves MN9_L.
  - D1: silent at 3 Hz. Switches on somewhere between 10 and 50 Hz, with no grading above that. Latches
    after 100 and 200 Hz.
- **Reading rule:**
  - **The near arm is a credible candidate only if all of these hold:**
    - S1, S3 and S5 pass;
    - D1 is silent at 3 Hz;
    - D1 does not latch.
    Then a sourced whole-brain version (noise, or a class-level resting potential, behind a switch and
    gated) is worth building.
  - **If it fails on specificity or latches,** resting excitability alone is not the missing piece, and
    the route needs something that keeps it graded:
    - adaptation, which the model's central cells lack (F-FI-1);
    - or inhibition that scales with the input.
    That is the next mechanism to test.
  - Either way, nothing is adopted from this route-only, 43-cell bracket.

### Result (6 October 01:02; S runs complete; D1 completed 01:28)

MN9_L per trial (Hz). Means of 3 trials for the route cells are in `runs/s12/spec/spec_rates.json`; figure
`docs/media/s12_route_spec.png` (viewed: rows are runs, columns the route cells and the GABA loop cells,
panels at 0 and 200 Hz).

| Run | Arm | 0 Hz | 100 Hz | 200 Hz | Rule | Verdict |
|---|---|---|---|---|---|---|
| S1 leg bitter | base | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 | | |
| S1 leg bitter | near | 0, 0, 0 | 9, 7, 6 | 3, 2, 1 | ≤ 2 at 100 and 200 | **FAIL** at 100 |
| S2 leg sugar 100 + leg bitter | near | 36, 32, 32 | 19, 23, 21 | 8, 10, 9 | 200 ≤ 0 + 3 | pass |
| S3 labellar bitter | base, near | all 0 | all 0 | all 0 | ≤ 2 at 200 | pass |
| S4 labellar sugar | base | 0, 0, 0 | 7, 6, 7 | 13, 14, 17 | ≤ 2 at 0, ≥ 5 at 200 | pass |
| S4 labellar sugar | near | 0, 0, 0 | 56, 57, 57 | 67, 66, 66 | same | pass |
| S5 labellar sugar 100 + bitter | base | 6, 4, 5 | 0, 0, 0 | 0, 0, 0 | 200 ≤ half of 0 | pass |
| S5 labellar sugar 100 + bitter | near | 57, 55, 57 | 0, 0, 0 | 0, 0, 0 | same | pass |

D1, leg sugar under `near`, MN9_L during the stimulus and (after the bar) in the 1 s after it:

| Input (Hz) | 3 | 10 | 25 | 50 | 100 | 200 |
|---|---|---|---|---|---|---|
| MN9_L | 17, 13, 14 \| 2, 0, 2 | 23, 22, 24 \| 1, 0, 2 | 24, 26, 25 \| 0, 2, 2 | 33, 31, 30 \| 1, 2, 2 | 36, 35, 34 \| 0, 1, 1 | 38, 39, 40 \| 1, 0, 1 |

- **`near` fails the reading rule** on two counts: leg bitter alone drives MN9_L (S1 at 100 Hz), and 3 Hz
  of leg sugar, the spontaneous GRN level (Ling 2014), drives it at 13-17 Hz (D1).
- **It does not latch.** MN9_L falls to 0-2 Hz in the second after every stimulus so far.
- **It grades, compressively.** MN9_L goes 15, 23, 31, 36 Hz from 3 to 100 Hz input: about 4 Hz per
  doubling of input across the range (logarithmic). It does not switch.
- **Labellar specificity holds.** Labellar bitter alone stays at 0 Hz, and labellar bitter at 100 Hz
  silences labellar sugar under both arms (S5). `near` raises labellar sugar 8-fold at 100 Hz (57 against
  7 Hz), seen, not scored.
- **Leg bitter suppresses leg sugar.** At 200 Hz it cuts MN9_L by 73% (33 → 9 Hz). French et al. 2015 report
  a 22% drop in PER for optogenetic bitter activation (secondary). Reported, not scored, as pre-registered.
- **Where leg bitter enters** (inferred from the means). Under S1 `near`, AN05B106 fires at 28-41 Hz (21-35
  under base), and the GNG cluster follows: GNG578, GNG143 and GNG167 at 11-14 Hz, Roundup (GNG108) at 6-9.
  AN01B004, which gets no leg bitter synapses, fires at about 5 Hz. So the leak runs through AN05B106, the
  entry cell that gets 316 synapses from leg bitter.
- **My expectations:**
  - S1 passing: wrong.
  - S3 passing: held.
  - S2 changing by under 5 Hz: wrong (−12 and −24 Hz).
  - S4 near above base: held.
  - S5 failing under `near`: wrong.
  - D1 silent at 3 Hz, switch-like and latching: all wrong.
- **Why 3 Hz is enough** (`scripts/probes/unitary_psp.py`, 01:00, `runs/s12/margin/unitary_near.json`;
  derived from the model, not measured).
  - Under `near` the entry cells rest 1.16 mV (AN01B004) and 1.08 mV (AN05B106) below threshold.
  - One spike in one sugar GRN gives them 0.12-1.17 mV, about 0.03 mV per synapse.
  - 12 of 25 tested GRN → AN01B004 connections and 8 of 32 GRN → AN05B106 connections fire the cell from
    a single GRN spike.
  - So at a 1 mV margin each entry cell repeats single GRN spikes. No unitary GRN → second-order PSP has
    been measured in the fly, so this cannot be checked against data.
- The 00:41 margin sweep (below) asks whether a larger margin fixes both failures. (D1 at 25 and 200 Hz
  added 01:30; they change no verdict.)

## Pre-registration: is there a resting margin at which the leg sugar route ignores spontaneous GRN input and leg bitter, but opens at a real sugar rate? (6 October, 00:41; diagnostic, nothing adopted)

**Why now.** The first trials of the 00:26 runs already fail its reading rule, so `near` (1 mV below
rheobase) is not a candidate:
- 3 Hz of tarsal sugar GRN input, the spontaneous level, drives MN9_L at 17 and 13 Hz (D1, two trials).
- Leg bitter alone at 100 Hz drives it at 9 and 7 Hz (S1, two trials).

Its full result is written above once all trials finish. At the m9c default, about 7 mV below rheobase,
the route stays shut even at 200 Hz. Before turning to a new mechanism, this checks whether both failures
come only from choosing 1 mV.

**Question.** Is there a margin between 1 and 7 mV at which all of these hold?
- 3 Hz input stays silent.
- 50 Hz input opens the route. That is about the tarsal sugar GRN rate at 100 mM sucrose (Ling 2014).
- Leg bitter stays silent.
- Labellar bitter still suppresses labellar sugar.

Separately: does the Roundup–DNge059 loop make the hair trigger? GNG108 → DNge059 has 343 synapses and
DNge059 → GNG108 has 333, both cholinergic (male-cns, edges ≥ 5).

**Setup.**
- m9c, open loop, 3 trials, 1000 ms, no shuffles.
- Margin arms: the 43 route cells sit k mV below their own rheobase, for k = 2, 3 and 4.
  - Files: `runs/s12/rest/route_near{2,3,4}.csv`, which are `route_near.csv` minus 1, 2 and 3 mV.
  - The margins are guessed and diagnostic. The rheobase is derived, from `route_rest.py`.
- Loop arm L1: `near` (k = 1) with DNge059's output removed (`--release-gain DNge059=0`).
- Backhouse tmux `s12margin_*`; logs in `runs/s12/margin/`. The A, B and L runs start first; the S and T
  runs start when the 00:26 runs free memory.

| Run | Assay | Rates (Hz) | Pass rule (per margin) |
|---|---|---|---|
| Ak | `legsugar_mn9` | 3, 10, 25 | MN9_L ≤ 2 Hz at 3 Hz |
| Bk | `legsugar_mn9` with `--off-ms 1000` | 50, 200 | MN9_L ≥ 5 Hz at 50 Hz, and ≤ 2 Hz in the 1 s after the stimulus |
| Tk | `legbitter_mn9` (LgAG1) | 100, 200 | MN9_L ≤ 2 Hz at both |
| Sk | `sugar_bitter_mn9` (labellar sugar held at 100 Hz) | bitter 0, 200 | MN9_L at bitter 200 ≤ half its bitter-0 value, or ≤ 2 Hz |
| L1 | `legsugar_mn9`, DNge059 silent, k = 1 | 3, 50 | none: a mechanism probe |

- The rules and their sources are those of the 00:26 pre-registration: Ling 2014 for the GRN rates, Shiu
  2024 for labellar bitter, and the analogy for leg bitter.
- Labellar bitter alone is dropped: it stayed at 0 Hz under `near`, the most excitable arm.
- **A margin is a candidate only if Ak, Bk, Tk and Sk all pass.**
- **L1:** if MN9_L at 3 Hz falls to ≤ 2 Hz with DNge059 silent, the loop makes the hair trigger.
  Otherwise the trigger is elsewhere.

**Expectations (mine).**
- k = 2 still fires at 3 Hz.
- k = 3 is silent at 3 Hz and opens at 50 Hz.
- k = 4 does not open at 50 Hz.
- Tk fails wherever the route opens at 50 Hz. Leg bitter enters the route through AN05B106, which gets
  316 synapses from LgAG1 against 1,029 from leg sugar. Two of its four cells get as much bitter input as
  sugar input (115 against 260, and 196 against 113; male-cns, derived).
- Sk passes at every margin.
- L1 at 3 Hz drops below 5 Hz.

**Reading rule.**
- **If a margin passes,** that is a one-number fit to one route.
  - It does not make the margin a model value.
  - The next step is a whole-brain version behind a switch, with the battery and gate: a class-level
    resting level, or noise.
  - That version must fit the MBON-α3 evidence that central rest looks like pacemaking
    (`docs/research/s12_central_fi.md`).
- **If no margin passes,** resting excitability alone cannot make the route both sensitive and specific.
  - If the failure is leg bitter, the gap is in how bitter suppresses sugar.
    - The model forces every stimulated GRN to spike: each Poisson input is a 68.75 mV kick, as in Shiu
      2024.
    - So presynaptic inhibition of sugar GRN terminals cannot act. In the labellum, bitter suppresses
      sweet GRNs through GABA-B on their terminals (Chu et al. 2014 Curr Biol 24:1978; search summary,
      unverified).
    - That is the next mechanism to examine.
  - If the failure is grading (fires at 3 Hz at one margin, misses 50 Hz at the next), the next
    mechanism is adaptation or inhibition that scales with input.
- Nothing is adopted.

### Result (6 October 01:28; all runs complete, 3 trials each; backhouse `runs/s12/margin/*.log`, rates `runs/s12/margin/dose_k{1..4}_{real,off_real}.json`, `dose_L1_real.json`; figure `docs/media/s12_route_margin.png`, viewed)

MN9_L rate per trial (Hz); after the bar, the 1 s after the stimulus. k = 1 is `near` (D1, 00:26 runs).

| Arm | 3 | 10 | 25 | 50 | 200 | Tk: leg bitter 100, 200 | Sk: bitter 0 → 200 | Verdict |
|---|---|---|---|---|---|---|---|---|
| k = 1 | 17, 13, 14 | 23, 22, 24 | 24, 26, 25 | 33, 31, 30 \| 1, 2, 2 | 38, 39, 40 \| 1, 0, 1 | 9, 7, 6 and 3, 2, 1 | 57, 55, 57 → 0 | fails A, T |
| k = 2 | 9, 3, 8 | mean 11 | mean 16 | mean 24 \| ≤ 1 | mean 29 \| ≤ 1 | 0 at both | 44, 41, 47 → 0 | fails A |
| k = 3 | 1, 0, 0 | 5, 2, 3 | 12, 13, 13 | 18, 17, 16 \| 0, 0, 1 | 22, 24, 21 \| 1, 0, 1 | 0 at both | 33, 32, 29 → 0 | **passes all four** |
| k = 4 | 0, 0, 0 | 0, 0, 0 | 3, 5, 7 | 8, 8, 9 \| 0, 0, 0 | 17, 17, 13 \| 0, 0, 1 | 0 at both | 24, 25, 28 → 0 | **passes all four** |
| L1 (k = 1, DNge059 silent) | 15, 10, 14 | | | 27, 27, 26 | | | | probe |

- **Two margins pass: 3 and 4 mV below rheobase.** Both ignore 3 Hz, ignore leg bitter, open at 50 Hz and
  stop within a second, and labellar bitter still silences labellar sugar. This is a one-number fit to one
  route (guessed margin, derived rheobase), not a model value.
- **The input rate that brings MN9_L to 5 Hz** (derived from the means): k = 1 and 2 below 3 Hz, k = 3
  about 10 Hz, k = 4 about 25 Hz. The real tarsal sugar GRN rate at 100 mM is 50-55 Hz (Ling 2014), so
  both passing arms put threshold below the real rate.
- **Leg bitter is cured by the margin, not by a new mechanism.** At 2 mV and above, leg bitter at 100 and
  200 Hz gives 0 Hz on every trial. So the presynaptic inhibition switch is not needed for this failure
  (`docs/research/s12_presyn_inhibition.md`).
- **Where the separation happens** (figure, means). The entry cells grade the same at every margin:
  AN05B106 38-44 Hz and AN01B004 30-39 Hz at 50 Hz input for k = 1-4. The margin acts downstream. There
  are two branches:
  - GNG250, DNge174, GNG093 and DNge173 open first. At k = 4 and 50 Hz they run at 27, 17, 12 and 9 Hz and
    carry MN9_L to 8 Hz on their own.
  - GNG578, GNG143 and the Roundup–DNge059 pair open late. At k = 4 and 50 Hz GNG578, GNG143 and DNge059 are
    below 1 Hz and GNG108 is at 4 Hz; at 200 Hz GNG578 and GNG143 reach 13 Hz. At k = 3 they open between
    10 and 25 Hz.
- **Single spikes no longer cross** (`unitary_psp.py`, `runs/s12/margin/unitary_near3.json`). At k = 3 the
  entry cells rest 2.7-2.8 mV below threshold. One GRN spike fires the cell alone for 1 of 25 GRN →
  AN01B004 connections and 0 of 32 GRN → AN05B106 connections (12 and 8 at k = 1).
- **L1:** silencing DNge059's output cuts MN9_L only slightly (13 against 15 Hz at 3 Hz, 27 against 31 at
  50 Hz). The Roundup–DNge059 loop adds to the route but does not make the hair trigger.
- **Labellar sugar is amplified at every margin** (seen, not scored): MN9_L at labellar sugar 100 Hz is
  24-47 Hz at k = 2-4 against 4-6 Hz under m9c, because the route cells are shared.
- **My expectations:**
  - k = 2 fires at 3 Hz: held.
  - k = 3 silent at 3 Hz and open at 50: held.
  - k = 4 does not open at 50: wrong (8-9 Hz, through the first branch).
  - Tk fails where the route opens: wrong.
  - Sk passes: held.
  - L1 below 5 Hz at 3 Hz: wrong.
- **Per the reading rule,** the next step was a whole-brain version behind a switch. That is the 01:16
  pre-registration below.

## Pre-registration: a class-level resting level, the whole-brain version of the leg sugar margin (6 October, 01:16; written after the first trial of every 00:41 run; diagnostic until the rule below says otherwise)

**Why now.** In the first trial of each 00:41 run, margins k = 3 and k = 4 pass all four route rules
(A, B, T and S) and k = 2 fails A (MN9_L 9, 3 and 8 Hz at 3 Hz input). That margin is a fit to one route of
43 cells. The 00:41 reading rule asks next for a whole-brain version behind a switch, gated and battery
tested. This is it. The 00:41 result is written above once its last trials finish. If they reverse a pass,
the matching arm here is dropped.

**The switch.** The existing class rows `class:<c>|tonic_drive` (N3, mV added to the spontaneous drive,
bounds −10 to 20, prior normal(0, 2), guessed; `data/model/parameters.csv`) for the three classes that hold
all 43 route cells: central_other (22,674 cells), AN (1,878) and DN (1,318).
- **W3:** 4.7 mV in all three. That is 7.7 mV, the isolated rheobase of a cell with the prior channels
  (derived, `route_rest.py`), minus k = 3. With per-cell channels it leaves AN01B004 3.35 mV and AN05B106
  2.85 mV below rheobase.
- **W4:** 3.7 mV in all three (k = 4).
- The value is fitted on one route (inferred). It stands for central cells resting nearer threshold than
  the Shiu constants put them. It is not a measured resting potential.
- Not driven: MBONs (MBON-α3 fires 12 Hz at rest, a different regime; F-FI-1), MNs (fitted templates),
  VNC local, optic, CX, AL, MB, clock and sensory classes.

**Runs** (backhouse; logs `runs/s12/whole/`; m9c plus `--set` for the arm; launch script
`runs/s12/whole/launch_w.sh`):

| Run | What | Pass rule | Basis |
|---|---|---|---|
| A | `legsugar_mn9` at 3 and 50 Hz, `--off-ms 1000` | MN9_L ≤ 2 Hz at 3 Hz; ≥ 5 Hz at 50 Hz; ≤ 2 Hz in the 1 s after | Ling 2014, as 00:41 |
| T | `legbitter_mn9` at 100 and 200 Hz | MN9_L ≤ 2 Hz at both | analogy with labellar bitter, as 00:41 |
| S | `sugar_bitter_mn9`, labellar sugar 100 Hz, bitter 0 and 200 | MN9_L at bitter 200 ≤ half its bitter-0 value, or ≤ 2 Hz | Shiu 2024, as 00:41 |
| G | `closed_loop_check.py`, seeds 12-15 first, 16-19 if 12-15 pass | no runaway; silent last 100 ms 0 spikes/ms; 0 MuJoCo warnings; no NaN; thorax height within 0.01 mm of m9c for the same seed | the gate since s6 |
| R | central_other class mean rate in G's 1 s run, each seed | ≤ 1.4 Hz | held out: Frechter et al. 2019 in vivo baselines, PN 1.4, LH local 1, LH output 0.1 Hz (measured, read) |
| C | `clock_phase_rates.py` at CT 2 and 10 | DN1p 5-20 Hz at CT 2, ≤ 1 Hz at CT 10 | the 23:34 clock rule (Flourakis 2015); m9c's fit is fragile, so any change to central excitability must re-run it |

- The class tonic drive counts as network activity in G (only per-type tonic rows are excluded). So a
  driven cell that fires by itself in silence fails the gate. That is intended: no recording says these
  cells fire with all input removed.
- R is weak. The class mean includes silent cells and Frechter's cells are a few identified types. It can
  only catch a class that runs hot.
- C and the battery run only for an arm that passes A, T, S, G (8 seeds) and R.

**Adoption rule.** An arm that passes A, T, S, G, R and C becomes candidate profile m9e (m9c plus the three
class drives). It is adopted as the working profile only if the battery under `FLYEMU_PROFILE=m9e` has no
new failures and its seed 12 sheet (`nonleg_motor_census.py --sheet`) looks like m9c's. If both arms
qualify, W4 is adopted (the smaller change). The drive is then a fitted value (inferred) with this
section as its derivation.

**Expectations (mine, written now).**
- W3 fails G: runaway or silent-window spikes on at least one of seeds 12-15. The DN class holds the
  latent DNge019/DNg12 loop (F-STAB-1, F-STAB-2), and 4.7 mV across 1,318 DN cells is a large push.
- W4 passes G and R. central_other rises from 0.15 Hz to 0.2-0.5 Hz.
- The route is more excitable than in the route-only arm at the same k, because 25,870 driven cells add
  recurrent input to it. So W3 fails A at 3 Hz and W4 passes it.
- T and S pass under both arms.
- C: DN1p rise above 20 Hz at CT 2 under W3 and stay within 5-20 Hz under W4.

**Reading rule.**
- If no arm passes G, a uniform class drive is not how this brain can rest nearer threshold. The candidates
  then are a drive limited to the gustatory and SEZ cells (smaller and nearer the route, but a narrower
  claim), or membrane noise, which the MBON-α3 trace argues against for that cell. Next steps are written
  then.
- If an arm passes G but fails A, B, T or S, the route-only margin does not survive the rest of the brain,
  and the route's opening depends on how its neighbours rest. That is reported as such.
- Nothing is adopted from this section except by the adoption rule above.

### Result of stage 1 (01:24; gate seeds 12 and 13 only; backhouse `runs/s12/whole/cl_w{3,4}_s1{2,3}.{json,log}`)

**Both arms fail G on both seeds, so neither can be adopted.** Seeds 14-15 and the A, T and S assays were
not launched: no later run could change the verdict.

| Seed | Arm | Silent last 100 ms (spikes/ms) | Thorax final (mm), m9c | central_other (Hz) | AN | DN | Motor | P-EN |
|---|---|---|---|---|---|---|---|---|
| 12 | m9c | 0 | 0.552 | 0.149 | 0.47 | 0.86 | 2.11 | 0 |
| 12 | W3 | 24.5 | 0.542 | 1.00 | 1.83 | 4.40 | 3.56 | 26.1 |
| 12 | W4 | 14.9 | 0.537 | 0.64 | 1.53 | 4.18 | 3.58 | 0 |
| 13 | m9c | 0 | 0.547 | 0.146 | 0.46 | 0.85 | 2.03 | 0 |
| 13 | W3 | 17.0 | 0.555 | 0.99 | 1.81 | 3.63 | 3.11 | 22.0 |
| 13 | W4 | 1.4 | 0.554 | 0.64 | 1.38 | 2.92 | 2.79 | 0 |

- No runaway, no MuJoCo warnings, no NaN. Thorax height misses the 0.01 mm tolerance on W4 seed 12 (0.015)
  and is at its edge on W3 seed 12.
- **R passes** on all four runs: central_other 0.64-1.00 Hz, under 1.4 Hz.
- **Seen, not scored.** Under W3 the central complex lights up: P-EN 22-26 Hz, EPG 12 Hz. Standing P-EN fire
  3.9 ± 2.6 Hz (Turner-Evans 2017, loose patch, read), so W3 would fail that check. The clock class doubles
  (1.0-1.25 → 1.8-2.1 Hz), so DN1p are pushed off the fitted 23:34 rate, which C would have tested.
- **What keeps firing** (the gate log's table of cells active in the silent window). On W4 seed 12 and W3
  seed 12, the sustaining cells are DNge019 (11 cells), DNg12_a/c/e (22), DNge022, DNge009, DNg33,
  DNge137, GNG117, GNG153, GNG423 and others, with leg MNs downstream. That is the latent DNge019 / DNg12
  loop recorded in F-STAB-1 and F-STAB-2. On W4 seed 13, where silent activity decays to 1.4 spikes/ms,
  DNge019, DNg12 and DNge022 are absent from the table.
- **My expectations:** W3 fails G: held. W4 passes G: wrong. R under W4 0.2-0.5 Hz: wrong (0.64). The rest
  were not run.
- **Reading.** A uniform drive across central_other, AN and DN, at the margin the route needs, ignites the
  DN loop that the Shiu 7 mV gap holds latent. This is the second fix for the leg sugar block that fails:
  the route-only margin works but is a one-route fit, and its whole-brain version fails the gate. Per the
  working rules, I stop fixing and write up the mechanism (FINDINGS F-TASTE-LEG-1 and F-STAB-1). The one
  further run is the diagnostic below, which asks which class ignites the loop. It is not adoptable.

## Pre-registration: which class drive ignites the DN loop? (6 October, 01:24; diagnostic only, nothing adoptable)

**Question.** Is the DN class drive what ignites the DNge019 / DNg12 loop, and does the route still open with
central_other and AN driven but not DN?

**Arms** (m9c plus `--set`, all at 3.7 mV, gate seeds 12 and 13, backhouse `runs/s12/whole/`):
- **noDN:** central_other and AN at 3.7 mV; DN 0.
- **DNonly:** DN at 3.7 mV; central_other and AN 0.
- **noDN, route:** `legsugar_mn9` at 3 and 50 Hz, `--off-ms 1000`, 3 trials.

**Expectations (mine).**
- noDN passes G on both seeds (silent 0).
- DNonly fails G on seed 12.
- Under noDN the route opens more weakly than in the route-only k = 4 arm (MN9_L 2-8 Hz at 50 Hz), because
  its three DN types (DNge059, DNge173, DNge174) are not driven.

**Reading rule.**
- If noDN passes and DNonly fails, the DN loop's ignition needs the DN drive. Raising DN excitability is
  then unsafe in this model without whatever holds that loop in the real fly. The candidates are
  adaptation (N4) and per-class inhibition, recorded for the next session.
- If noDN also fails, the loop can be ignited from upstream, and no class-level drive at this margin is
  gate-safe.
- Either way nothing is adopted. A class subset that passed would need its own pre-registration, with
  held-out checks, before it could be a candidate.

### Result (01:38; backhouse `runs/s12/whole/cl_{nodn,dnonly}_s1{2,3}.{json,log}`, `a_nodn.log`, run `runs/assay-legsugar_mn9-m9c-nodn4/`)

Gate (closed loop, 1 s). Silent = spikes/ms in the last 100 ms after all input is removed; the rule is 0.

| Arm | Seed | Silent | Thorax (mm; m9c 0.552, 0.547) | central_other (Hz) | AN | DN | Clock class |
|---|---|---|---|---|---|---|---|
| m9c | 12, 13 | 0, 0 | 0.552, 0.547 | 0.15, 0.15 | 0.47, 0.46 | 0.86, 0.85 | 0.98-1.25 |
| W4 (all three at 3.7) | 12, 13 | 14.9, 1.4 | 0.537, 0.554 | 0.64, 0.64 | 1.53, 1.38 | 4.18, 2.92 | 1.76, 2.03 |
| noDN | 12, 13 | **10.0, 11.0** | 0.550, 0.546 | 0.63, 0.65 | 1.06, 1.06 | 2.20, 2.29 | 1.91, 1.80 |
| DNonly | 12, 13 | **0, 1.06** | 0.549, 0.556 | 0.15, 0.16 | 0.48, 0.86 | 2.12, 2.44 | 1.41, 1.45 |

No MuJoCo warnings or NaN in any run. CX stays at 0 Hz in every noDN and DNonly run.

Route under noDN (open loop, MN9_L per trial, Hz; after the bar, the 1 s after):
- 3 Hz: 0, 0, 0 | 0, 0, 0. The whole brain sits at 0.01 Hz mean (119-129 active cells).
- 50 Hz: 15, 11, **81** | 0, 0, **105**. Trial 3 latched.

- **noDN fails G on both seeds**, with the same sustained cells as W3 and W4. So the loop can be ignited
  without driving any DN, and per the reading rule **no class-level drive at this margin is gate-safe.**
- **DNonly passes seed 12 and fails seed 13 narrowly** (1.06 spikes/ms). The cells that keep firing on seed
  13 are a different, VNC-side set: AN09A005 (11 cells), AN27X013, DNg33, IN09A005, EA27X006.
- **What holds the loop: the GNG117 pair** (male-cns, measured synapse counts; transmitter predicted).
  - In the gate logs (noDN), the latched noDN route trial and the stage 1 runs, the highest-rate cells are
    the same: GNG117 (both cells, 110-155 Hz), GNG153 (glutamate), GNG186 (GABA), DNge022 and GNG031. In
    the latched trial they drive MN9 at 105 Hz and other cranial motor neurons (GNG668, MNx02) at 45-68 Hz
    after the stimulus.
  - GNG117_L and GNG117_R excite each other: 914 synapses one way and 973 the other, 22-23% of each cell's
    4,000-4,400 input synapses, both predicted acetylcholine. GNG117 also sends 903 synapses to DNge022, 1,167
    to GNG153 and 792 to GNG186. DNge019 (11 cells, 1,125 synapses among themselves) joins at lower rates.
  - A reciprocal excitatory pair that strong is bistable in a model without adaptation or depression: once
    both cells fire, each holds the other above threshold. Raising central excitability by 4 mV lets any
    burst of input (body afferents in the gate, leg sugar in the open-loop route) push the pair into its
    on state.
  - Its largest inhibitory inputs are DNg98 (546 synapses, GABA) and AN05B007 (497, GABA). Its next
    largest input after itself is GNG642 (505, serotonin).
- **Correction to the stage 1 result.** I named the sustaining core the DNge019 / DNg12 loop. The cells
  with the highest rates are the GNG117 pair and its targets; DNge019 is a lower-rate member. F-STAB-1's
  Mi18/DNge019/DNg12 loop and this one may share DNge019 but are not the same circuit.
- **Open-loop silence.** With no body, noDN at 3 Hz leaves the brain at 0.01 Hz. The gate's ignition needs
  closed-loop afferent input (inferred; as in F-STAB-2).
- **Seen, not scored.** The clock class rises from about 1.0-1.25 Hz to 1.4-2.0 Hz under every arm. F-CLOCK-1
  warned that its fit is a 0.25 mV knife edge; DNonly raises it too.
- **My expectations:**
  - noDN passes G on both seeds: wrong.
  - DNonly fails G on seed 12: wrong (passes 12, fails 13 through other cells).
  - noDN route 2-8 Hz at 50 Hz: wrong (11-15 Hz on two trials, latched at 81 Hz on the third).
- **Reading.** A whole-brain resting level 4 mV below rheobase is not gate-safe, because the GNG117 pair
  becomes a switch that any strong input can turn on and nothing turns off. Nothing is adopted, and I stop
  fixing per the two-failed-fixes rule. What could hold the pair, in order of evidence available:
  - spike-frequency adaptation (N4) at a central value; MBON-α3's recorded adaptation is weak within
    400 ms (`docs/research/s12_central_fi.md`);
  - short-term depression at the GNG117 ↔ GNG117 synapse (no measurement for this cell);
  - stronger GABA from DNg98 and AN05B007 (per-class inhibition, not fitted);
  - the acetylcholine call for GNG117 (predicted; a glutamate or GABA sign would remove the loop).
  The measurable facts for Ben's list: GNG117's transmitter, and whether paired GNG117 cells fire
  persistently after a brief stimulus.

## Pre-registration: does vision die at the lamina's release rule, at the medulla's mode, or both? (6 October, 01:58; diagnostic first, adoption rule below)

**Relay** (flyapp, 883c836 on app): under m9r, L1-L3 respond with the right signs, but the medulla cells spike (the optic columnar mode group, guessed) and move by under 1.5 mV, so T4/T5 never respond. Recordings say Mi1, Tm1, Tm2, Tm3 and others are graded.

**A second mechanism, found before any arm ran** (derived from the code and the m9c baseline's static segment). Graded release is `r = clip((v - v_rest)/(v_th - v_rest), 0, 1)` (lif.py), so a graded cell releases nothing at or below rest. L1 and L2 get their photoreceptor input through histamine (inhibitory), so they can only hyperpolarise. At mean luminance the L1 type mean is −54.17 mV against rest −52 (m9c, open loop, `motion_grating.py` static segment). They therefore release nothing in any light, and the lamina is silent downstream whatever the medulla's mode. Fly graded synapses are tonically active: transmitter is released at rest, and hyperpolarisation lowers it (Juusola et al. 1996 TINS; Uusitalo et al. 1995; [unverified], to be checked against the evidence agent's sources).

**Two switches** (both neutral at 0; lif.py; registered in structural_keys.csv and parameters.csv):
- `cell_type:all|mode_from_recordings` 1: per-type `graded_rec` rows in `data/params/cell_types.csv` (1 graded, 0 spiking, each with basis and source) override the class group for those types only. The rows are written from the evidence agent's table before arms R and RT launch, and committed before their results are read. Types with no recording stay in the group (spiking, guessed).
- `cell_type:ol_graded|release_at_rest` r0: optic-lobe graded interneurons (superclass ol_intrinsic) release r0 × rmax at rest, `r = clip(r0 + (1 − r0)(v − v_rest)/(v_th − v_rest), 0, 1)`. Photoreceptors keep r0 = 0 (their dark potential is the bottom of their range). The value 0.5 (midpoint of the release range) is guessed. CPU path only; the GPU path refuses it.

**Probe.** `scripts/probes/motion_grating.py` (new): no body, open loop, seed 1. A sine grating (30°, 1 Hz, contrast 1) drives every photoreceptor with a derived direction (6,026 of 6,091) through the eye's own drive rule, 1 s per direction (±az, ±el in each eye's derived frame) after a 1 s static grating at mean luminance. Reported per type: mean v, F1 of the type-mean v at 1 Hz, spike rate; for T4/T5 subtypes a direction index over opposite directions.

**Arms** (m9c plus `--set`; backhouse `runs/s12/vision/`):

| Arm | Set | Prediction |
|---|---|---|
| B | none (m9c) | L1-L3 modulate; T4/T5 at rest in every direction (type-mean F1 < 0.1 mV) |
| T | release_at_rest 0.5 | Mi1/Tm1/Tm2/Tm3 type-mean F1 rises above B's; T4/T5 respond only if the spiking medulla cells cross threshold (no prediction) |
| R | mode_from_recordings 1 | T4/T5 stay near rest (F1 < 0.1 mV): with the lamina silent, the mode change alone cannot revive them, except through R7/R8 inputs to the medulla |
| RT | both | T4 and T5 respond: type-mean F1 or mean shift ≥ 0.5 mV in at least one direction for every subtype |

- Direction selectivity is reported and not required. The model has no fitted visual parameters, so DSI could come out near 0 or with the wrong subtype pattern; T4a/T4b and T4c/T4d preferring opposite directions would be the biological pattern.
- **What would change the plan.** If R alone revives T4/T5, the release rule is not the block, and r0 stays unproposed. If RT leaves T4/T5 silent, the next block is the photoreceptor-to-LMC gain (L1 moves 2.2 mV for the full range) and I stop after writing the mechanism up.

**Adoption rule.** An arm that passes V (RT's row) then runs the gate G (`closed_loop_check.py` seeds 12-15; silent last 100 ms 0 spikes/ms; no runaway; 0 MuJoCo warnings; no NaN; thorax within 0.01 mm of m9c) and the battery (no new failures), and its seed 12 contact sheet is viewed. If all pass, it becomes candidate profile m9o (m9c plus the arm). The gate silences the eye too (zero drive), so tonic graded release keeps running in silence; if that alone makes visual projection cells fire in the silent window, it is reported as a conflict between the gate's convention and tonically active synapses, not passed.

**Deviation, 02:00, before any R or RT result exists.** B finished first, and its photoreceptor type-mean F1 is 0.04 mV even though the drive swings ±5 mV. A 30° grating puts the columns of one type at every phase, so averaging the type before taking the F1 cancels the modulation. The type-mean F1 could never have passed V for any columnar type; the criterion was mis-specified. The probe now also records a per-cell F1 (`f1_cell_mv`, the mean over the type of each cell's F1 at 1 Hz), and the V criterion becomes: for every T4/T5 subtype, the per-cell F1 in at least one direction exceeds the static grating's per-cell F1 by ≥ 0.5 mV, or the mean shift is ≥ 0.5 mV. This makes V easier to pass than the row above, so it is declared here rather than applied silently. B and T were restarted with the fixed probe; the first B output is kept as `grating_m9c_typemeanonly.json`. Its mean potentials are unchanged by the fix: same seed, and the fix only adds recording.

**Correction to s11 fill F3** (1 October, "Per-type resting potentials from the measurement library"): Behnia et al. 2014 recorded Mi1, Tm1, Tm2 and **Tm3**, not Tm4. Their full text names Tm3 about 69 times and Tm4 not at all. The `v_rest_shift_rec` row in `data/params/cell_types.csv` now reads Tm3. Only `cell_type:all|rest_from_recordings` reads these rows (m10p and m10q, rejected rungs), so m9c and every adopted profile are unchanged.

### Result, arms B and T (6 October, 02:08; per-cell F1; `runs/s12/vision/grating_{B,T}.json`, backhouse)

| Type | B v (mV) | B per-cell F1 | T v (mV) | T per-cell F1 |
|---|---|---|---|---|
| R1-R6 | −48.62 | 2.95 | −48.62 | 2.95 |
| L1 / L2 / L3 | −54.17 / −53.77 / −52.72 | 1.61 / 1.50 / 0.45 | −54.16 / −55.30 / −53.22 | 1.62 / 1.50 / 0.43 |
| Mi1 / Tm3 | −52.38 / −52.00 | 0.23 / 0.00 | −54.05 / −53.82 | 0.56 / 0.38 |
| Tm1 / Tm2 / Tm4 / Tm9 | −52.00 each | ≤ 0.001 | −50.05 / −51.39 / −50.50 / −51.24 | 0.65 / 0.45 / 0.46 / 0.06 |
| Mi4 / Mi9 | −52.62 / −52.08 | 0.38 / 0.05 | −53.09 / −50.81 | 0.38 / 0.15 |
| CT1, T4a-d, T5a-d, Am1, HS, H2, VS, LC4, LPLC2, LC11 | −52.00 | 0 | −52.00 | 0 |

Static per-cell F1 (noise floor) ≤ 0.01 mV for every type; no spikes anywhere in the visual pathway in either arm.

- **B as predicted:** the lamina modulates, nothing below it does. Mi1 and Mi4 move 0.2-0.4 mV in B through inputs other than L1/L2 (L1/L2 release nothing).
- **T as predicted for the medulla:** with release at rest, L1's tonic glutamate hyperpolarises Mi1 by 1.7 mV and L2's acetylcholine depolarises Tm1 by 2 mV (right signs), and the OFF cells now follow the grating at 0.45-0.65 mV per cell. Every medulla cell stays 5-9 mV below its spike threshold (−45 mV), so T4/T5 get nothing: exactly −52.00 in every direction. This reproduces the relay's "under 1.5 mV".
- **The gain is small at both stages.** At full contrast L1 swings 1.6 mV and the medulla under 0.7 mV. That is far below the 7 mV graded range, and below the LMC responses in fly recordings (tens of mV in Calliphora, Laughlin; to be sourced for Drosophila). If RT fails, this gain is the next block, as pre-registered.
- **Gate seed 12 under T (diagnostic, not an adoption step):** silent last 100 ms 16.36 spikes/ms (FAIL; m9c 0.0), and optic_columnar spikes 4,946 times in the silent window (m9c 53). The silence convention makes the eye dark, so L1/L2 depolarise to rest and release r0 = 0.5 tonically, and the OFF columnar cells fire. Thorax 0.550 mm (m9c 0.552), 0 MuJoCo warnings, no NaN. This is the pre-registered conflict between the gate's convention and tonically active synapses: darkness is not silence for a fly's optic lobe. It is not passed.

**The `graded_rec` rows (02:24, before R and RT launch).** Written from the evidence agent's table (`data/raw/vision_mode_s12/`; agent stopped at rate limits), keeping only recordings read in full text:
- **Measured, graded** (in vivo whole-cell, Drosophila): Mi1, Tm1, Tm2, Tm3 (Behnia et al. 2014; graded light responses, no action potentials mentioned anywhere in the text), T4a-d (Gruntman et al. 2018) and T5a-d (Gruntman et al. 2019). Their authors say the weak 1-2 mV transients "could not be verified as spikes". Para sits on T4/T5 axons (Fendl et al. 2020), so axonal spiking stays open.
- **Inferred, graded:** L4 and L5. They are lamina monopolar cells like L1-L3, and classes.csv already labels them graded, but cell_types.csv had no row, so every profile spiked them. Their responses have not been measured in Drosophila (Currier et al. 2023 review).
- **Left in the group (spiking, guessed):**
  - Mi4 and Mi9: the "whole-cell" claim for Strother et al. 2017 came from a search snippet. The public abstract says calcium imaging, and the full text is paywalled.
  - Tm4 and Tm9: calcium imaging only (Serbe et al. 2016 and Arenz et al. 2017, not read).
  - CT1, Am1, C2, C3, TmY15, LPi and the LPTCs: no Drosophila recording was read. Schnell et al. 2010 (HS) was blocked.
  - Lawf2 spikes (Tuthill et al. 2014, secondary read). It already spikes in the model, so no row.
- So R and RT test the recorded types only. T5's other cholinergic inputs, Tm4 (9.9%) and Tm9 (21.0%), and the shared CT1 (8-15%) still spike.
- No Drosophila LMC amplitude per contrast was found. Rivera-Alba et al. 2011 (read): "photoreceptor terminals to L1 and L2 have each 42 synapses", per terminal. A complete cartridge (six R1-R6 terminals) therefore gives L1 and L2 about 250 each, in line with the scan's maximum (about 320). The scan's right-side median where present (34-36) is about one terminal's worth, so even the cartridges with input are mostly partial (F-VISION-4, truncation).

### Result, arms R and RT (6 October, 02:40; per-cell F1; `runs/s12/vision/grating_{R,RT}.json`, `vx_RT.json`; figure `docs/media/s12_vision_grating.png`)

**V fails on all eight subtypes. No gate, battery or adoption is run (the adoption rule applies only to an arm that passes V).** As pre-registered, the next block is the photoreceptor-to-LMC gain, and this write-up is where the block stops.

| Type | R per-cell F1 (max dir) | RT per-cell F1, grating / static | RT static v (mV) | RT static rate (Hz) |
|---|---|---|---|---|
| T4a-d | ≤ 0.0001 | 0.20-0.21 / 0.02-0.04 | −53.6 to −55.4 | 0 |
| T5a-d | ≤ 0.0003 | 0.14-0.15 / 0.04-0.05 | −55.9 to −58.5 | 0 |
| Mi1 / Tm1 | 0.23 / 0.0005 (= B) | 0.62 / 0.65 | −57.11 / −54.74 | 0 |
| CT1 | 0.056 | 0.006 / 0.03 | −51.16 | 335.5 |
| HSN / HSE / HSS | ≤ 0.02 | 0.23 / 0.44 / 0.59 | about −52 | 132.0 / 140.5 / 104.5 |
| VS | 0.0095 | 0.13 / 0.16 | about −52 | 59.2 |
| Am1 / H2 / HST | ≤ 0.07 | 4.7 / 1.1 / 0.14 (static 4.3 / 1.3 / 0.27: drifting, not following the grating) | −504.58 / −226.89 / −69.33 | 0 |

- **R as predicted.** Upstream of T4/T5, R is B to four decimals (Mi1 0.2294 mV in both). T4/T5 stay at −52.00 (per-cell F1 ≤ 0.0003 mV). The lamina releases nothing in either arm, so recorded modes alone cannot revive the pathway. CT1, Am1, HS and H2 pick up ≤ 0.07 mV with no spikes. Likely source: rectified release from the newly graded medulla cells (not traced).
- **RT, V criterion.** The T4 per-cell F1 exceeds static by 0.18-0.19 mV, and T5 by 0.09-0.10 mV. The largest mean shift is ≤ 0.07 mV. The threshold was 0.5 mV, so V fails by a factor of 3-5. T4/T5 now follow the grating faintly. Recorded T4/T5 responses are much larger: Gruntman et al. 2018 and 2019 had to widen a trial-stability criterion to 25 mV for slow bars "due to their strong responses" (Methods). Their Fig. 1D-E (T5, whole-cell, dark bars moving across the receptive field; read, figure estimate against the 10 mV scale bar; `data/raw/vision_mode_s12/elife50706_fig1.jpg`, eLife CC BY): preferred-direction peaks about 5-11 mV, null direction about 2-4 mV, DSI 0.4-0.6. The stimulus is a bar, not a grating, so the numbers are not directly comparable. Still, the model's 0.1-0.15 mV is about two orders of magnitude short. DSI is not meaningful at this size.
- **RT, the static state is wrong.** At mean luminance with no motion, HS cells fire 104-140 Hz, VS 59 Hz and CT1 335 Hz. T4/T5 sit 2-6 mV below rest. The likely causes have not been decomposed. One is CT1 (GABA; 2 cells with 109-138k output synapses each, a median 8-17% of each T4/T5's input). The other is Mi1, which sits 5 mV below rest (L1's tonic glutamate is among its inputs), cutting its release to T4.
  - Recorded HS cells rest graded, depolarising with some spikelets, not tonic 100+ Hz spiking (from memory; Schnell et al. 2010 is blocked). CT1 is a compartmentalised graded cell (Meier & Borst 2019, from memory, to verify). Both are spiking in the model, which is guessed: the group default plus para.
- **RT, runaway hyperpolarisation.** vm_extremes (300 ms static, `vx_RT.json`) finds 111 cells in 21 types below −100 mV. All are spiking-mode cells: Pm3 56 of 69 cells, MeLo8 23 of 47, both H1, both H2, both Am1 (minimum −667.6 mV), Nod2-5, LPT21/22/27/49, Li32, Pm13 and others. The first crossing comes 20-90 ms in.
  - The mechanism is that m9c's current-based synapses have no reversal potential, so tonic inhibitory release drives voltage without bound.
  - Am1's input is 73% T4b/T5b acetylcholine (low release when they sit hyperpolarised), 9.6% TmY5a glutamate and 5.1% LPi12 GABA. Once excitation falls, the inhibitory share is unopposed.
  - Real GABA-A and GluCl currents reverse near −70 to −80 mV. Tonic release therefore needs bounded inhibition (the conductance-mode switch, e_inh −70, which m9c leaves off) before it can be adopted for any profile.

**What this says about the blank.**
1. The release rule is the first block, and is now understood. Graded release starts at rest, and L1/L2 only ever receive histamine inhibition, so they release nothing at any light level. R confirms that recorded modes cannot fix this alone.
2. Tonic release (T) fixes the sign and passes the modulation to the medulla. It cannot be adopted as is: it breaks the gate's silence convention (seed 12: 16.36 spikes/ms) and, under current-based synapses, drives 111 cells out of range.
3. **The gain is the remaining block.** At full contrast R1-R6 swing 2.95 mV, L1/L2 about 1.5, and the medulla about 0.6. That leaves T4/T5 at 0.1-0.2 mV. The 7 mV graded range (rest −52, threshold −45) is guessed, and so are the synaptic weights per release unit. No Drosophila LMC amplitude per contrast has been read. Laughlin 1981 (Calliphora) gives the matching principle: LMC gain is set so that the natural contrast distribution fills the response range (inferred for Drosophila).
   - **Where the gain is lost** (per-cell F1, 90th percentile against the mean, RT). Cells with full photoreceptor input swing much more than the type mean:
     - L1/L2: 4.5-4.8 mV against 1.5;
     - Mi1/Tm1/Tm3: 1.7-1.9 mV;
     - T4a 0.66 mV, T5a 0.41 mV.
     Two losses compound. Truncation (F-VISION-4) leaves about half the cartridges without input, which halves the type mean. Each graded synaptic stage after the lamina then passes on about 1/2.6 of its input's swing. The per-stage factor is set by `graded_rmax` (100 Hz equivalent, guessed, bounds 10-500) times the per-synapse efficacy, both unsourced. The 7 mV graded range (v_th − v_rest) is also shared by every optic graded type, and that is guessed too. Recorded responses are larger (read, figure estimates against the 10 mV scale bars):
     - Behnia et al. 2014 Fig. 2 (`data/raw/vision_mode_s12/behnia2014_fig2.jpg`, PMC author manuscript), full-field flashes from dark to full intensity, mean ± SEM: Mi1 depolarises about 20 mV and Tm3 about 15 mV at light ON; Tm1 and Tm2 dip a few mV at ON and depolarise 15-20 mV at OFF.
     - T5: 5-11 mV for moving bars (above).
     So real medulla cells swing at least 15-20 mV, about 3× the model's whole graded range. Each stage in the model ends up about 10× short in mV.
4. The r0 = 0.5 for every ol_intrinsic graded cell extrapolates lamina evidence (Juusola et al. 1996, Uusitalo et al. 1995) to the medulla. It is guessed for every cell type downstream of the lamina.
5. The relay's 13 Hz Am1 rhythm was not reproduced open loop. In RT, Am1 runs away instead of oscillating. The rhythm needs the closed loop (the flyapp m9r control) to diagnose.

**Next discriminating experiment (next block, not started).**
- Pre-register a photoreceptor-to-LMC gain arm with three parts: a sourced LMC contrast response, bounded inhibition (conductance mode on), and a release rule in which hyperpolarisation increases L1/L2 output to their ON/OFF targets. The last part could be either tonic release with the dark state handled by the gate convention, or a sign-correct histamine-to-LMC transfer.
- Pass condition: V as above. T4/T5 at least 0.5 mV, CT1/HS not tonic at mean luminance, and no cell below −90 mV.
- Mode rows for CT1, HS/VS and Am1 need read recordings first: Ben's list.

**Diagnostic, 02:43 (mechanism check, not a fix; nothing is adopted from it).** The claim above is that the runaway in RT comes from current-based inhibition. Test: rerun `vm_extremes.py` under RT with conductance mode on (`cell_type:all|conductance_based` 1, e_inh −70 mV, the existing switch, neutral otherwise), threshold −90 mV, everything else as `vx_RT.json`. Predictions:
- No cell goes below −90 mV. Inhibition then cannot pass −70 mV, and nothing else in m9c drives below it except the intrinsic K channels' reversal, which is guessed.
- If cells still go below −90 mV, the claim is wrong and the write-up gets corrected.

**Result, 02:44 (`runs/s12/vision/vx_RTc.json`).** 0 of 167,111 cells leave [−90, 20] mV under RT with conductance-mode inhibition, against 111 cells below −100 mV with current-based inhibition. The prediction holds: the runaway was current-based inhibition. (The RT log's overflow warnings in `channels.py` came from the same −500 mV voltages.)

**Arm RTc, pre-registered 02:44, launched before any result.** `motion_grating.py` under RT plus `cell_type:all|conductance_based` 1, same seed and stimulus as RT. It tests which of the RT failures bounded inhibition removes, not a candidate for adoption: conductance mode changes every synapse in the model and needs its own gate and battery.

| Quantity | Prediction |
|---|---|
| V (T4/T5 per-cell F1 above static ≥ 0.5 mV) | Fails. The gain is unchanged: conductance weights are scaled to keep their effect at rest. |
| HS / CT1 at mean luminance | Still tonic. HS's input is 91% T4a/T5a, which release tonically at r0. |
| Am1, H2 | Within [−90, 20] mV (from vx_RTc) |

If V passes, gain is not the remaining block, and the next block is reconsidered before it is pre-registered.

**Flash baseline, 02:48 (measurement, launched before any result).** New probe `scripts/probes/visual_flash.py`. It applies the Behnia et al. 2014 Fig. 2 stimulus (full-field flashes from darkness, 200 ms and 1 s) through the eye's drive rule, open loop with no body, and reports type-mean and 90th-percentile-cell deflections in the ON and OFF windows. It runs under B (m9c) and RTc.

These results become the starting point of the gain block. The fit target and the held-out split will be declared before any gain arm runs, so these are not used as a fit.

Prediction: Mi1/Tm3 ON and Tm1/Tm2 OFF deflections of 0.5-3 mV in RTc, against 15-20 mV recorded (figure estimate), and about 0 in B.

**Photoreceptor amplitude, read 02:49** (Juusola & Hardie 2001 J Gen Physiol 117:3, PMC2232468, in vivo intracellular Drosophila R1-R6 at 25 °C; `data/raw/vision_gain_pr_s12/`):
- The dark resting potential is "−60 to −75 mV". Included cells had "saturating impulse responses ≥60 mV", sometimes "∼75 mV".
- Under bright backgrounds, the mean potential "saturates at 25–40 mV above the dark resting potential".

In the model, R1-R6 sit about 1 mV above −52 mV in the dark (`photoreceptor:all|dark_drive` 1 mV, guessed). Full light adds `luminance_gain` 10 mV (guessed), and release saturates 7 mV above rest. The model's photoreceptor swing is therefore about 1/5 to 1/10 of the recorded one (derived). The same compression into a 7 mV graded range runs through every optic graded stage. This is the gain blank stated in measured terms: amplitudes at each stage (R1-R6 60-75 mV, medulla 15-20 mV, T5 5-11 mV) against a single guessed 7 mV range.

**Per-stage wiring for the gain block (male-cns edges at the model's 5-synapse threshold, measured counts; 02:50).**

| Stage | Synapses per postsynaptic cell, median (p90) | Share of the cell's input | Cells with none |
|---|---|---|---|
| R1-R6 → L1 / L2 | 0 (200) / 0 (210) | | 55% / 55% |
| L1 → Mi1, L1 → Tm3 | 82 (99), 68 (93) | 0.29, 0.29 | 0 |
| L2 → Tm1, L2 → Tm2 | 119 (150), 130 (157) | 0.41, 0.47 | 0 |
| Mi1 → T4a, Tm3 → T4a | 61 (80), 23 (34) | 0.38, 0.14 | 0, 2% |
| Tm1 / Tm2 / Tm9 / Tm4 → T5a | 19 / 30 / 23 / 15 | 0.13 / 0.21 / 0.16 / 0.10 | 1-7% |
| CT1 → T5a / T4a | 24 / 14 | 0.17 / 0.08 | 1% / 4% |

- The medulla wiring is complete: every Mi1, Tm1 and T4 has its main input. The losses are elsewhere:
  - the lamina truncation (55% of L1/L2 cells get no photoreceptor synapse);
  - the guessed per-stage gain (efficacy × `graded_rmax`), set alike for every synapse in the brain;
  - the guessed 7 mV range.
