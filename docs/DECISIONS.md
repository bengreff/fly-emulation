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

**LMC amplitude and LPTC modes, read 02:54** (Sonnet extraction; raw pages and quote files in `data/raw/vision_gain_s12/`; the Zheng quotes re-checked here against the saved PMC page).
- **Drosophila LMC, measured** (Zheng et al. 2006 J Gen Physiol 127:495, PMC2151524, sharp electrodes in vivo, LMC subtypes not separated):
  - "LMCs responded to light pulses with transient hyperpolarizations that could reach values of 45 mV";
  - "WT ... LMCs had resting potentials <−40 mV and maximum responses >40 mV" (an inclusion criterion);
  - photoreceptors "maximum responses >40 mV" and "resting potentials in darkness <−60 mV";
  - feedback onto photoreceptor terminals "requires tonic transmitter release" (their inference, from shibire^TS1).
- **The measured amplitude chain for a bright flash from dark** (per cell, peak):
  - R1-R6 >40 to 75 mV (Zheng 2006; Juusola & Hardie 2001);
  - LMC up to 45 mV, hyperpolarising (Zheng 2006);
  - Mi1/Tm3 about +15-20 mV ON, Tm1/Tm2 about +15-20 mV OFF (Behnia 2014 Fig. 2, figure estimate);
  - T5 5-11 mV for a preferred-direction bar (Gruntman 2019 Fig. 1, figure estimate).
  - Every stage after the photoreceptor passes about 0.4-1 of its input's swing (derived across studies and preparations: sharp electrode against whole-cell, flash against bar; uncertain to a factor of 2).
- **Against the model** (grating per-cell F1, F-VISION-5): R1-R6 2.95, LMC 1.5, medulla 0.6, T4/T5 0.2 mV. Its stage ratios (0.5, 0.4, 0.33) are within that factor of 2. **Most of the deficit is at the first stage: the photoreceptor swings about 1/15-1/25 of the recorded amplitude, and the 7 mV graded range (guessed) cannot carry more.** This is a reading from two runs, not a test; the flash baseline measures the stage ratios directly.
- **Constraint for any amplitude fit.** In conductance mode, a cell can hyperpolarise only to the inhibitory reversal: −70 mV (guessed) from −52 mV rest (guessed) allows 18 mV. A 45 mV LMC hyperpolarisation needs a sourced LMC rest and chloride reversal, or a declared amplitude cap.
- **Not usable as measured values:**
  - HS and VS mode: Joesch 2008, Schnell 2010 and Maimon 2010 were abstract-only (403, not in PMC). Numbers seen only in search summaries are excluded.
  - CT1: Meier & Borst 2019 was abstract-only and is calcium imaging, so it gives no mode.
  - Am1: no recording found.
  - These stay guessed. HS, VS and CT1 tonic firing at mean luminance therefore cannot be scored against a recording, only against the guess.

### Result, arm RTc (6 October, 02:58; `runs/s12/vision/grating_RTc.json`, 746 s on backhouse; figure `docs/media/s12_vision_grating.png`, five arms, viewed)

| Quantity | Prediction (02:44) | Result |
|---|---|---|
| V (T4/T5 per-cell F1 above static ≥ 0.5 mV) | Fails; gain unchanged | **Fails on all 8 subtypes**: T4 0.080-0.089 mV (static 0.006-0.013), T5 0.064-0.073 (static 0.008-0.012). The gain is not unchanged: it is about half of RT's. |
| HS / CT1 at mean luminance | Still tonic | **Held**: HSN 150.5 Hz, HSE 149.5, HSS 109, VS 60.7, CT1 354 |
| Am1, H2 | Within [−90, 20] mV | **Held**: Am1 −54.94, H2 −53.19 (RT: −504.6 and −226.9) |

- **Per-cell F1 per stage (RTc, against RT):**
  - R1-R6 2.95 (2.95);
  - L1 1.09 (1.54), L2 0.86 (1.50);
  - Mi1 0.28 (0.62), Tm1 0.42 (0.65), Tm3 0.35 (0.59);
  - T4 0.08-0.09 (0.20-0.21), T5 0.06-0.07 (0.14-0.15).
- **Stage ratios fall from 0.3-0.5 to 0.2-0.5.** The stated reason for "gain unchanged" was wrong. Conductance weights keep each synapse's effect at rest, but the standing conductance from tonic release (r0 0.5) lowers every graded cell's input resistance, so each added input moves it less. That is inferred from the drop and has not been decomposed.
- **Reading.** Conductance mode removes the runaway but costs gain. It does not change the conclusion: the visual chain is 10-100× short of recorded amplitudes at every stage after the photoreceptor. The motion tuning seen in RT (T4a/T4d DSI 1.0 at 0.06 mV) was noise-level and is gone in RTc (DSI 0-0.33).

### Result, flash baseline (6 October, 03:00; `runs/s12/vision/flash_{B,RTc}.json`, 641 s each on backhouse; figure `docs/media/s12_vision_flash.png`, viewed, recorded peaks drawn as dashes)

Prediction (02:48): Mi1/Tm3 ON and Tm1/Tm2 OFF deflections of 0.5-3 mV in RTc, about 0 in B. **Partly held.**

| Type (1 s flash, type mean; 90th/10th-percentile cell) | B | RTc | Recorded |
|---|---|---|---|
| R1-R6 ON peak | +7.66 | +7.66 | >40 to 75 |
| L1 ON | −3.88 | −2.51 (p10 −6.70) | down to −45 |
| L2 ON | −3.40 | −1.66 (p10 −5.36) | down to −45 |
| Mi1 ON | **−0.44** (wrong sign) | +0.38 (p90 +1.53) | about +20 |
| Tm3 ON | 0.00 | +0.91 (p90 +2.72) | about +15 |
| Tm1 ON dip / OFF | 0.00 / +0.13 | −0.68 / +0.14 (p90 OFF +0.64) | dip / +15-20 |
| Tm2 ON dip / OFF | 0.00 / +0.12 | −0.53 / +0.20 (p90 OFF +0.86) | dip / +15-20 |
| T4a ON / T5a OFF | 0 / 0 | +0.26 / +0.12 | not recorded for flashes |

- **Where the prediction held and where it failed:**
  - Tm3 is in range.
  - Mi1's type mean (0.38) is just under the range; its 90th-percentile cell (1.5) is in range.
  - Tm1/Tm2 OFF (0.13-0.20) is below the range.
  - In B, Mi1 hyperpolarises by 0.44 mV. L1 does not release in B, so this is another input (not traced).
- **Signs in RTc are right for every recorded type:** Mi1/Tm3 ON depolarisation, and the Tm1/Tm2 ON dip with an OFF rebound.
- Mi4 hyperpolarises to light in both arms. It is spiking by guess and subthreshold. Mi4 is reported as an ON cell in imaging studies that were not read here, so this is an unscored sign flag.
- **Stage ratios (RTc, strongest-decile cells against the recorded chain):**

  | Stage | RTc | Recorded |
  |---|---|---|
  | R → L1 | 0.87 | 0.75 |
  | L1 → Mi1 | 0.23 | 0.44 |
  | L1 → Tm3 | 0.41 | 0.33 |
  | L2 → Tm1 dip | 0.45 | — |
  | Mi1 → T4a | 0.44 | T5/Tm 0.3-0.65 |

  The stage ratios are within 2× of the recordings. **The absolute scale is set at the input:** the photoreceptor swings 7.7 mV against 60. The 7 mV graded spans (guessed) cap every stage after it.
- **Probe bug, fixed:** the trace array had one unfilled final row, which plotted as a spike to 0 mV. The analysis windows never reached it. The plot trims it for existing files, and the probe now allocates the right length.

### Pre-registration: the gain block (6 October, 03:04, before any gain run)

**Question.** Do sourced graded spans, plus a photoreceptor amplitude and one synaptic gain fitted to two recorded amplitudes, bring the held-out medulla and T4/T5 responses to their recorded scale without destabilising the network?

**New switch** (neutral 0, battery before adoption): `cell_type:all|graded_range_from_recordings`.
- 1 = the release span of a graded type is its recorded response amplitude, from `cell_types.csv` `graded_range_rec` rows:
  - R1-R6 60 mV (measured);
  - L1-L3 45 (measured), L4/L5 45 (inferred);
  - Mi1 20 (figure estimate, measured);
  - Tm1/Tm2/Tm3 20 (inferred from Mi1, so that their own amplitudes stay held out);
  - T4/T5 keep 7 (no row).
- 2 = as 1, and each graded synapse keeps its transfer per mV at rest (release × span/(v_th − v_rest), derived). The span then moves only the saturation point. Tonic release at rest scales with it.

**Base for every arm:** RTc (`mode_from_recordings` 1, `release_at_rest` 0.5, `conductance_based` 1) + `graded_range_from_recordings` 2.

**Fitted parameters and training targets.** Each is scored as the median over connected cells (`scripts/probes/visual_flash_score.py`: L cells with R1-R6 input, and downstream cells taking at least half of their L input from such cells).
- `photoreceptor:all|luminance_gain` (guessed 10) → R1-R6 ON peak 60 mV (Juusola & Hardie 2001). Set to 78 by linear scaling of RTc's 7.66 mV at 10 and checked in every run.
- `class:LMC|release_scale` (neutral 1, bounds 0.1-20) → Mi1 ON 20 mV (Behnia 2014 Fig. 2, figure estimate). Grid {1, 3, 10} on a short flash (settle 600 ms, a 1 s flash at 300 ms, tail 600 ms). Pick by log-interpolation, then confirm with one run.

**Held out:**

| Quantity | Recorded | Prediction at the fitted LMC scale | Pass band |
|---|---|---|---|
| L1/L2 ON (connected) | −45 | −12 to −18 mV: capped by the inhibitory reversal (−70, guessed) from −52 rest. A predicted miss. | within 2× |
| Tm3 ON | +15 | 8-25 (same L1 path as Mi1) | within 2× (7.5-30) |
| Tm1/Tm2 OFF | +15-20 | Fails, under 4 mV. The model photoreceptor has no light adaptation, so the OFF rebound is small. | within 2× (8.75-35) |
| Tm1/Tm2 ON dip | dip | negative | sign |
| T4/T5 drifting grating, per-cell F1 above static | ≥ 0.5 mV (criterion V) | Passes for T4. T5 uncertain. | V on 8 subtypes |
| T4/T5 direction selectivity (grating DSI) | 0.4-0.6 (T5 bar, figure estimate) | below 0.2 on most subtypes: the wiring is there, but delays and kinetics are guessed | DSI ≥ 0.3 |
| Network bounds (vm_extremes) | — | 0 cells outside [−90, 20] mV | 0 |

**Interpretation rules:**
- If no LMC scale in the bounds gets Mi1 to 15 mV, the block is the disinhibition ceiling. Mi1's ON response is release of L1's tonic glutamate, so its swing cannot exceed the distance from its inhibited potential to its uninhibited one. That mechanism gets written up rather than fixed by a third change.
- Nothing is adopted from this block. Conductance mode changes every synapse and needs its own gate and battery, and HS/VS/CT1 modes remain guessed.

### Result, the gain block (6 October, 03:14; `runs/s12/vision/flash_G_k{1,3,10}.json` with `.score.json`, 278-290 s each on backhouse; figure `docs/media/s12_vision_gain.png`, viewed)

**The fit failed, so the interpretation rule applies.** The block hit the disinhibition ceiling. No held-out test is scored, because no fitted scale exists. Nothing is adopted and no third change is tried.

| Connected-cell median (type-mean dark baseline) | LMC ×1 | LMC ×3 | LMC ×10 | Recorded |
|---|---|---|---|---|
| R1-R6 ON peak (training) | +46.8 (−51.4) | +46.8 | +46.8 | 60 |
| Mi1 ON (training) | +1.51 (−58.7) | +2.74 (−59.9) | +3.12 (−61.6) | +20 |
| L1 ON | −16.6 (−44.7) | −19.7 (−38.0) | −23.2 (−26.0) | −45 |
| L2 ON | −9.9 (−56.1) | −10.9 (−54.4) | −13.7 (−47.1) | −45 |
| Tm3 ON | +2.76 (−54.8) | +3.79 (−58.7) | +3.38 (−61.8) | +15 |
| Tm1 / Tm2 OFF | +0.35 / +0.53 (−47.7 / −46.6) | +0.47 / +0.68 (−35.6 / −37.8) | +0.44 / +0.38 (−18.0 / −22.8) | +15-20 |
| Tm1 / Tm2 ON dip | −2.5 / −2.0 | −3.9 / −3.2 | −3.7 / −3.4 | dip |
| T4a ON / T5a OFF | +0.68 / +0.07 | +0.97 / +0.22 | +0.99 / +0.10 | — |
| Cells outside [−90, 20] mV | 0 | 0 | 0 | — |

**Mechanism (Mi1), read from the numbers above:**
- Mi1's leak reversal is −55 mV, the recorded resting potential (Behnia et al. 2014, applied by `rest_from_recordings`). In the dark, L1's tonic glutamate pulls Mi1 3.7-6.6 mV below that.
- In light, connected Mi1 cells reach −57.2, −57.2 and −58.5 mV (dark baseline plus ON median). They never get back to −55.
- Raising the LMC scale lowers the dark baseline about as much as it raises the light peak. The swing grows by 1.6 mV over a tenfold scale and is saturating.
- Disinhibition can only return a cell toward its uninhibited potential. The uninhibited potential is the leak reversal, plus excitation from L5 and L3 (acetylcholine, 14% and 7% of Mi1's input synapses). L3 is itself hyperpolarised by light. So Mi1's ON swing is bounded by roughly 4-7 mV, whatever the LMC gain.
- The recorded ON response reaches about −35 mV from a dark −55. **A disinhibited cell can reach −35 only if its uninhibited potential is −35 or above.** So the recorded "rest" is a dark potential held down by tonic synaptic inhibition, not the cell's leak reversal.
- The model uses the recorded dark potential as the leak reversal, then adds the tonic inhibition on top. That counts the inhibition twice and leaves no room for an ON response. This is inferred from the model's numbers and the recorded amplitudes. No recording of Mi1's input resistance in dark and light has been read.

**Side findings:**
- **Mode 2 makes tonic release grow with the span.** In darkness, Tm1/Tm2 sit at −47.7/−46.6 at ×1 and depolarise to −18/−23 mV at ×10, under L2's tonic acetylcholine. L1's dark baseline climbs from −44.7 to −26.0 through LMC → LMC excitation (L5 is 20% of L1's input). Both are unphysiological at ×3 and above. So the LMC scale is bounded by the dark potentials before it is bounded by Mi1.
- **The photoreceptor is sublinear in conductance mode.** Gain 78 gives a 46.8 mV peak, not the 60 predicted by linear scaling. The peak sags to a +26 mV plateau and undershoots by 11 mV at OFF; these are network effects in the model, whose source has not been traced. The training target was missed (0.78); not refitted, because Mi1 is the binding limit.
- **The L1 response grows with the LMC scale**, from −16.6 to −23.2 mV, as its dark potential rises away from the −70 mV inhibitory reversal. That is the cap predicted in the pre-registration.
- **T4a ON doubles over RTc** (+0.68 to +0.99 against about +0.26 type-mean in RTc). This is a flash, not the grating V test, and not scored.
- **HS, VS and CT1 still fire tonically** (HSN 154-192 Hz, VS 86-98 Hz, CT1 409-434 Hz; all spiking by guess).

**Next discriminating step (pre-register before any run).** Make the recorded dark potential a target of the in-network dark state, not the leak reversal, for graded cells with tonic synaptic input. Then a disinhibited cell's light potential is set by its leak reversal and the strength of its tonic inhibition. The prediction to test is that Mi1's input resistance rises in light (several-fold if the inhibition carries the 20 mV). That is a recordable discriminator: Ben's list.

### Correction to the gain block mechanism (6 October, 03:29; `runs/s12/vision/cstate_k{1,10}.json` and `.log`, `scripts/probes/visual_conductance_state.py`, 81 s each on backhouse)

**The mechanism written at 03:14 is wrong in its premise, and its "Next" step targets the wrong limit.**
- m9c does not set `cell_type:all|rest_from_recordings`; only M10Q does (`profiles.py`). So every Mi1 and Tm cell in the gain block had the global rest and leak reversal of −52 mV, not the recorded −55. The dark baselines (−58.7 to −61.6) are 6.7-9.6 mV below the leak, and the light peaks (−57.2 to −58.5) are 5-6.5 below it.
- The model therefore never used a recorded dark potential as a leak reversal, so the "double count" was not what happened in these runs.

**What the conductances show.** I measured the conductance state directly. The probe takes cells whose cartridge has photoreceptor input, settles them 600 ms in the dark, then gives 300 ms of full-field light. The base is the gain block's, LMC ×1. Values are medians, with conductances in units of the leak conductance. They are model outputs (derived), not recordings.

| Connected cells | v dark → light (mV) | g_e | g_i dark → light | of which graded (by presynaptic type) | Potential with all inhibition removed (light g_e) |
|---|---|---|---|---|---|
| L1 | −46.1 → −60.0 | 0.16 | 0.04 → 1.72 | R1-R6 0.04 → 1.69 | −44.6 |
| Mi1 | −58.7 → −57.6 | 0.27 | 2.00 → 1.72 | L1 1.27 → 0.94 | −41.0 |
| Tm3 | −54.4 → −52.3 | 0.33 | 1.30 → 1.04 | L1 1.11 → 0.84 | −38.9 |

- **Modulation depth.** L1's release (r × g_k) falls only 27% in light, from 3.64 to 2.65. Over this window L1 hyperpolarises 14 mV, and with r0 0.5 and a 45 mV span the release falls by only about a third.
  - L1 cannot hyperpolarise past the inhibitory reversal, −70 mV, which is 24 mV below its dark potential. So even unlimited photoreceptor drive could cut L1's release by at most about half (inferred from the release rule).
  - Light removes 0.28 of Mi1's 2.00 inhibitory conductance, 14%.
- **The tonic remainder.** The other 0.73-0.78 of Mi1's g_i comes from inputs that are not graded in this configuration, and light leaves it unchanged. By synapse count the inhibitory ones are Pm1/Pm2a/Pm2b/Pm3 (GABA) and Dm1 and Mi13 (glutamate), 34% of Mi1's input synapses.
  - Suppose L1's release went to zero and nothing else changed. From the light conductances, Mi1 would sit at (−52 + 0.27·0 + 0.78·(−70)) / 2.05 = −52.0 mV, which is 6.7 mV above its dark potential (derived).
  - The tonic inhibition from these other inputs roughly cancels the L5/L3 acetylcholine, so that is the real ceiling. It is still short of the recorded 20 mV.
- **The leak is not the binding limit.** With every inhibitory input removed, Mi1 would sit at −41 mV, 18 mV above dark. Mi1 recovers 1.1 mV of that in the 300 ms window, about 6%.
- **At LMC ×10** Mi1 is in a high-conductance state: g_i 18.4, G 21.9, dark −61.3, pinned near the −70 mV reversal.
  - Tm1 and Tm2 sit at −15.7 and −20.2 mV under 7-10 leak conductances of L2's tonic acetylcholine.
  - L1 sits at −27.2 under L5's acetylcholine (g_e 1.05).
  - More LMC gain scales the tonic and modulated parts together, so the dark potential falls and the swing stays small.

**Restated mechanism (inferred from the model's conductances).** Mi1's ON swing is the product of two factors:
- how much of L1's tonic release light removes, which is set by L1's swing, the r0 and span of the release rule (r0 guessed, span inferred from the recorded LMC maximum), and the −70 mV reversal (a declared default);
- how much of Mi1's inhibition is L1's at all. The rest comes from tonic, non-graded GABA/glutamate inputs whose modes are guessed.

Each factor alone caps the swing far below 20 mV. The 03:14 conclusion that the LMC scale cannot fit Mi1 stands. Its reason is replaced.

**Consequences.**
- F-VISION-6 is corrected by F-VISION-7.
- The leak-calibration switch built for the operating-point block (`cell_type:all|leak_from_network_rest`, neutral, CPU-only, with `scripts/probes/visual_rest_calibrate.py`) is kept as tested infrastructure.
  - It does not address the binding limit.
  - Its smoke test at input gain 3 (rest targets −52, before this correction) put the Mi1 and Tm2 leaks at the bounds (−25 and −85 mV): Mi1 G 7.7, Tm1 5.2, Tm2 5.3, Tm3 5.8.
  - The script now requires `rest_from_recordings` so that its targets are the recorded rests.
- The recording that discriminates these readings is the same one: Mi1's input conductance in dark and light. Both readings predict that it falls in light. This reading predicts a small fall (14% of g_i in the model now). Matching the recordings needs most of the dark conductance to be L1's and removed by light.
- Ben's list also gets: whether Pm and Dm1 cells are graded or spiking, and their light responses.

### Result, the dim flash: first-synapse small-signal gain (6 October, 03:42; `runs/s12/vision/flash_dim_i{0.01,0.05}.json`, 155 s each on backhouse; diagnostic, nothing changed)

**Question.** The gain block base set gives an L1 ON swing of 16.6 mV against R1-R6's 46.8 mV. Is the photoreceptor→LMC synapse itself weak, or is the large flash compressing it?

**Test.** Same base set as the gain block (no LMC scale). One 500 ms flash (onset 300 ms) at intensity 0.01 and 0.05 of the full flash (`visual_flash.py --intensity`). Readout: median over connected cells (`/tmp/s12/dim_gain.py`), cross-checked against the type-mean trace divided by the connected fraction (0.45). The two agree to within 0.05 mV, and L1 has no dark noise (trace s.d. 0.000).

| | i 0.01 | i 0.05 | Recorded (Juusola, Uusitalo & Weckström 1995, J Gen Physiol 105:117, PMC2216927, *Calliphora*) |
|---|---|---|---|
| R1-R6 peak | +0.64 mV | +3.12 | |
| L1 peak | −0.79 | −3.45 | |
| R→L1 gain | 1.24 | 1.10 | "~13-fold amplification of low frequency signals" at the lowest background (~160 photons/s), rolling off to 4-fold at 60 Hz; 1.5-4.5 across cells at 500,000 photons/s |
| R→L2 gain | 0.66 | 0.55 | |
| Mi1 peak | +0.16 | +0.33 | |
| Tm3 peak | +0.22 | +0.58 | |
| t½ R1-R6 / L1 | 15 / 30 ms | 15 / 30 ms | transfer delay 9 ms falling to 3.3 ms with background |

**Reading.**
- The first synapse is about 10× weaker than the recorded dim-background gain. That target is measured in *Calliphora*; its transfer to *Drosophila* is inferred. The model synapse is static. It has no adaptation, so no single value can match both 13 (dim) and 1.5-4.5 (bright).
- Mi1 is compressive already at small L1 swings. Mi1 per mV of L1 was 0.19 at i 0.01 and 0.075 at i 0.05, while Tm3 stayed about linear (0.18 and 0.17 per mV). The mechanism is not identified.
- The t½ difference (15 ms, at 5 ms sampling) includes L1's membrane charging, so it is not a measure of transfer delay.

### Pre-registration: first-synapse gain (6 October, 03:42, before any run)

**Question.** Can photoreceptor release strength alone bring R→L1 to the recorded dim gain, and what does that do to L1's dark potential and to Mi1?

**Switch.** `class:photoreceptor|release_scale` k (existing, neutral 1; scales R1-R8 release onto every target). Base set as the dim flash.

**Derived prediction (conductance arithmetic from the 03:29 conductance state; L1 dark g_e 0.16 and g_i 0.04, all of it R1-R6 tonic release, leak −52, e_inh −70).**
- Photoreceptor tonic release in darkness scales with k too. L1's dark potential is therefore v(k) = (−52 − 2.8k)/(1.16 + 0.04k), and its small-signal gain scales as k/(1.16 + 0.04k)².
- That gain peaks at k ≈ 29, at 7.8× the k = 1 value, so about 9.6. Under the current release rule no k reaches 13.

| Arm | Dim R→L1 gain | L1 dark | L1 ON swing (full flash) | Mi1 ON (full flash) |
|---|---|---|---|---|
| k 1 (measured above / gain block) | 1.24 | −46.1 | −16.6 | +1.51 |
| k 10 | 5-7.5 | −51.3 ± 2 | | |
| k 30 | 6-9.6 (lower than linear: Δg is no longer small at i 0.01) | −57.6 ± 2 | −8 to −14 (the dark potential falls toward the −70 floor) | 1.0-2.5 |

**Held out.** L1's dark potential against Pantazis et al. 2008 −43 ± 7.3 mV (n = 6; reference electrode not stated). At k 30 the predicted dark potential is 2 s.d. below it.

**Interpretation.**
- If the dim gain saturates below 13 as predicted, the bound comes from the release rule's tonic dark release scaling with the gain (photoreceptor dark offset `dark_mv` 1.0, guessed).
- Tonic histamine release in darkness is real (Uusitalo et al. 1995 J Neurophysiol, *Calliphora*; to be read). The candidate next mechanism is a separately sourced dark release, or the lamina field potential that adds driving force in light (Zheng et al. 2006). It is not a third gain.
- Nothing is adopted from this block.

### Pre-registration addendum: R1-R6 alone (6 October, 03:53, before the run)

At k 30 the full flash flipped Mi1 to −1.4 mV, failing the 1.0-2.5 mV prediction. The conductance split (`visual_conductance_state.py`, now with a spiking split by presynaptic type) shows:
- L1's inhibition of Mi1 fell by 0.29 in light, while the spiking Pm/Dm1 inhibition stayed flat;
- 595 of the 795 connected Mi1 cells receive R7/R8 synapses (mean 10.7 per cell). These are spread over R8p, R8y, R8_unclear, R7d and R8d, so every per-type median is 0.

`class:photoreceptor|release_scale` scales R7/R8 too.

**Follow-up.** A per-type `release_gain` row scales R1-R6 alone at 30 (`FLYEMU_EXTRA_PARAMS`, basis guessed, diagnostic).

**Predictions.**
- Mi1 ON at the full flash 1.0-2.5 mV, as pre-registered.
- Mi1's light g_i below its dark g_i.
- L1 is unchanged from the k 30 arm within 0.5 mV.

If Mi1 still flips, the R7/R8 reading is wrong.

### Result: first-synapse gain and the R1-R6 addendum (6 October, 03:59; `runs/s12/vision/flash_kR{10,30}_i0.01`, `flash_kR30_i1`, `flash_R16kR30_i1`, `cstate2_kR{1,30}`, `cstate2_R16kR30`; figure `docs/media/s12_vision_first_synapse.png`, viewed; F-VISION-8; nothing adopted)

Against the 03:42 pre-registration (connected medians; dark potentials from the conductance probe, connected cells):

| Arm | Dim R→L1 gain (pred.) | L1 dark (pred.) | L1 ON full (pred.) | Mi1 ON full (pred.) |
|---|---|---|---|---|
| k 1 | 1.24 | −46.1 | −16.6 | +1.51 |
| k 10 | **6.07** (5-7.5, pass) | all-cell mean −47.4; connected not measured (−51.3 ± 2) | | |
| k 30, R1-R8 | **6.18** (6-9.6, pass at the low edge) | **−58.2** (−57.6 ± 2, pass) | **−11.5** (−8 to −14, pass) | **+0.003** (1.0-2.5, **fail**) |
| 30 on R1-R6 only (addendum) | | −57.6 | −12.1 (within 0.5 of k 30: **fail by 0.07 mV**) | **+1.13** (1.0-2.5, pass) |

- **Held out.** L1's dark potential at k 30 is −58.2 (R1-R6 only −57.6) against Pantazis et al. 2008 −43 ± 7.3 mV: 2 s.d. below, as predicted. The arm fails the held-out check.
- **Addendum.** Mi1 recovers (+1.13 mV), and its inhibitory conductance now falls in light (1.73 to 1.46 leak units; at k 30 on R1-R8 it rose, 1.85 to 2.49). So the k 30 flip was R7/R8 histamine onto Mi1, as the addendum read it.
  - L1 moved 0.57 mV, just outside the declared 0.5 mV. The cause is that the class switch also scaled R7/R8→L1 synapses in the medulla (F-VISION-4); L1's dark inhibitory conductance drops from 1.28 to 1.17 without them.
  - The same synapses explain the unconnected L1 cells that responded at k 30 (all-cell median −10.3). With R1-R6 alone the all-cell median is −1.3, so this is R7/R8 input, not lateral spread.
- **Gain saturation.** The gain saturates at 6.1-6.2 by k 10, below the 13 recorded (*Calliphora*, dim background) and below the 9.6 small-signal estimate.
  - The derived bound in F-VISION-8 is the general form. In a single-compartment conductance cell, the small-signal R→LMC gain cannot exceed (E_inh − v₀)/(4s), whatever the release scale. Here v₀ is L1's potential with no histamine (−44.8 mV), and s is the release curve's foot or e-fold below the dark potential (model 0.65 mV, effective). The model sits at 25.2/(4 × 0.65) ≈ 9.7.
  - So a third release gain is not the next step; the remaining levers are the release curve's shape and the driving force.
- **Correction to the 03:42 pre-registration's interpretation.** It named "the lamina field potential that adds driving force in light (Zheng et al. 2006)". That is not what the sources say.
  - Zheng et al. 2006 give dark resting values: space −20 to −40 mV against the retina, LMCs −40 to −70 on the same reference.
  - Weckström & Laughlin 2010 (*Calliphora*) find the cartridge space 30 mV below the retina in the dark, promoting tonic release, and depolarising in light, which backs off the presynaptic drive.
  - So the field does not add driving force in light. What it may do is set the LMC transmembrane dark potential 20-30 mV less negative than the recorded value (inferred from the same-reference numbers). That would raise ort's driving force at every light level if the histamine-gated chloride reversal holds near −70 mV transmembrane (not measured).
- **Uusitalo et al. 1995 (J Neurophysiol, *Calliphora*, abstract via Europe PMC).** Transmitter release "decreased dramatically approximately 12 mV below the resting potential" of the photoreceptors. The model's release floor is about 0.65 mV below the dark potential.
  - A linear rule with a 12 mV foot would cap the gain near 0.5.
  - The recorded high gain together with release continuing below dark points to a steep, curved (exponential-like) release curve, not a linear one with a high foot (inferred).
- **Nothing adopted.** The k 30 and R1-R6 arms fail L1's held-out dark potential, and no arm moves Mi1 beyond 1.5 mV.

**Next (pre-register first).** A two-lever block, each lever behind its own switch with declared bounds:
1. A curved photoreceptor release rule (exponential in V − V_dark, e-fold s bounded 0.5-3 mV, with tonic dark release fixed by the Uusitalo 12 mV extent).
2. The LMC transmembrane operating point under the lamina field (dark offset 0-30 mV, Zheng 2006 / Weckström & Laughlin 2010).

The derived bound sets the prediction before any run: gain ≤ (E − v₀)/(4s). Train on the dim R→L1 gain. Hold out L1's dark potential (Pantazis) and the full-flash Mi1/Tm3/Tm1/Tm2.

**Refinement to "Next" (04:02; F-VISION-8 refinement, derived).**
- The small-signal gain is D(1 − p)/s, where D is the tonic histamine hyperpolarisation of the dark LMC. It is capped near D/s, so the driving-force lever buys at most 2×.
- The model's s is already 0.6 mV (the dark-drive offset above the linear release foot). The 6.2 is the large-signal gain of a flash that doubles release; the small-signal gain at k 30 is 10.6.
- The two-lever block therefore becomes:
  1. L1/L2's histamine-free potential v₀, sourced from an LMC dark potential with histamine transmission removed if one exists.
  2. A curved release rule: s bounded 0.5-3 mV, extent about 12 mV below dark (Uusitalo).
- The lamina-field offset is held back. The test flash for the small-signal gain must move R1-R6 by much less than s (i ≤ 0.001).
- A source search for D, s and the LMC chloride reversal is running (04:00).

### Pre-registration: LMC histamine-free potential plus R1-R6 release (6 October, 04:05, before any run)

**Question.** F-VISION-8 gives the R→LMC small-signal gain as D(1 − p)/s. Can one sourced-target pair, L1's dark potential and the dim-background gain, be met together by moving only L1/L2's histamine-free potential v₀ and R1-R6's tonic release? And what does the medulla do then?

**Sources** (searched 04:00-04:04, open full text only).
- No open source gives an LMC potential with histamine transmission removed; Uusitalo 1995, Laughlin, Howard & Blakeslee 1987, Hardie 1989 and Zheng 2006 were paywalled.
- Dau et al. 2016 (PMC4801898): hdc photoreceptors rest about 7 mV above wild type in the dark; LMCs were not recorded.
- Rusanen & Weckström 2016 (PMC4869513, *Calliphora*, measured): L1/2 dark rest −38.4 ± 3.2 mV (n 15), L3 −49.3 ± 6.5 (n 11).
- An unverified secondary snippet attributes "an e-fold increase in postsynaptic conductance per 1.50-1.86 mV, peak slope about 6" to the blowfly R→LMC synapse. It is not used as a value. It is listed for Ben (Laughlin, Howard & Blakeslee 1987 full text). If true, it conflicts with the model's s 0.6 mV and with 13 as a target.

**Switches** (existing; rows in `FLYEMU_EXTRA_PARAMS`, diagnostic).
- `cell_type:all|leak_from_network_rest` 1 with `v_leak_shift_fit` +15.1 mV on `^L1$|^L2$` (leak −36.9 mV; basis derived: solved from the two targets below). L3 is left alone (its *Calliphora* rest is 11 mV lower).
- `release_gain` 12.5 on `^R1-R6$` (derived: same solve).
- Base set as the gain block.

**Derived solve** (one-compartment arithmetic from `cstate2_kR1`: a = 1 + g_e = 1.161, R1-R6 g_i 0.0387 per unit k, E −70, s 0.61 mV = the photoreceptor dark offset above the linear foot).
- The targets are L1 dark −43 (Pantazis 2008, *Drosophila*, untyped LMCs) and small-signal gain 13 (Juusola 1995, *Calliphora*).
- They give p 0.294, g_i 0.48, D 11.2 mV and v₀ −31.8 mV.

**Predictions** (connected medians).

| Readout | Role | Prediction | Recorded |
|---|---|---|---|
| L1 dark | train | −43 ± 2 | −43 ± 7.3 (Pantazis); −38.4 ± 3.2 (Rusanen, *Calliphora*, held) |
| R→L1 gain, flash i 0.001 (R1-R6 ≈ 0.064 mV) | train | 13 ± 2.5 | about 13 |
| R→L1 gain, i 0.01 | check | 9.0 ± 1.5 (release doubles) | |
| L1 ON, full flash | held | −22 to −27 | −45 (recorded value in the score, field-referenced) |
| L1 release, dark → light | check | 0.60 → 0.31 | |
| Mi1 ON, full flash | held | +2 to +4 (still fails; F-VISION-7's tonic Pm/Dm1 inhibition) | +20 |
| Tm3 ON, Tm1/Tm2 OFF, L2 | held | not predicted numerically; reported | |
| v₀ (histamine-free LMC potential) | prediction for Ben's list | −32 ± 3 | not measured |

**Interpretation.**
- If the two training numbers land, the formula is confirmed, and the first synapse can meet both recordings only with v₀ about 12 mV above the model's current −44.8. That is a testable prediction (ort or hdc LMC rest).
- If they miss by more than the tolerance, the one-compartment reading is wrong and I stop and write up.
- Nothing is adopted. Adoption needs Ben's call on a fitted LMC leak, plus the gate and battery.

### Result: LMC histamine-free potential plus R1-R6 release (6 October, 04:11; `runs/s12/vision/flash_v0_i{0.001,0.01,1}`, `cstate_v0`, about 4 min on backhouse; figure `docs/media/s12_vision_first_synapse.png`, viewed; F-VISION-9; nothing adopted)

| Readout | Role | Prediction | Model | Recorded |
|---|---|---|---|---|
| L1 dark (connected median) | train | −43 ± 2 | **−43.7** pass | −43 ± 7.3 (Pantazis); −38.4 ± 3.2 (Rusanen, *Calliphora*, held: 1.7 s.d. below) |
| R→L1 gain, i 0.001 | train | 13 ± 2.5 | **11.8** pass | about 13 |
| R→L1 gain, i 0.01 | check | 9.0 ± 1.5 | **9.6** pass | |
| L1 ON, full flash | held | −22 to −27 | **−25.1** pass | −45 (0.56 of it; k 1 was 0.37) |
| L1 release, dark → light | check | 0.60 → 0.31 | 0.60 → 0.33 pass | |
| Mi1 ON, full flash | held | +2 to +4 | **+2.33** pass (the prediction); FAIL against +20 | +20 |
| Tm3 ON | held | reported | +4.22 (k 1: 2.76) | +15 |
| Tm1 / Tm2 OFF | held | reported | +1.58 / +1.89 (k 1: 0.35 / 0.53) | +17.5 |
| L2 ON / dark | held | reported | −18.2 / −50.4 | −45; L1/2 rest −38.4 ± 3.2 (*Calliphora*) |
| T4a ON | extra | | +1.02 (k 1: 0.68) | |

No cell left [−90, 20] mV.

**Reading.**
- The one-compartment arithmetic predicted the first synapse to within 10% (gain) and 0.7 mV (dark potential).
- Both lamina targets are met together only with L1's histamine-free potential near −32 mV, 13 mV above the model's default. That is a prediction for an ort or hdc LMC recording, not a measurement.
- The lamina now carries 0.56 of the recorded L1 swing. The deficit moves downstream:
  - Mi1's L1 inhibition now falls 0.60 leak units in light (k 1: 0.33), but its 0.7 of tonic Pm/Dm1 inhibition is untouched (F-VISION-7). Even total L1 shutoff would leave Mi1 about 6.9 mV above dark (derived).
  - Tm3 has little tonic inhibition (0.17). L1's release cannot fall below 0.30 even at −70 mV (r0 0.5, 45 mV span), so Tm3 is already at its ceiling of about 4.3 mV. If L1's release could fall to zero, Tm3 would reach about 12 mV, against 15 recorded (derived).
- L2's dark potential is 12 mV below its *Calliphora* L1/2 rest, held there by spiking Dm6/Dm17/Dm1 inhibition (0.45 leak units, modes guessed).
- Seen, not scored: L1 has no depolarising OFF transient at light-off in this arm (k 30 had +5-7 mV). Recorded LMCs have a strong one.

**Decided by Ben, 13 Oct (see the s13 entry at the end): v0 superseded by v0r as the vision diagnostic base.** The question was: should the v0 arm become the vision base for the next blocks? It is a fitted L1/L2 leak (−36.9 mV, derived from two recordings) plus R1-R6 release ×12.5 (derived).
- My recommendation is yes for vision diagnostics, and no for the working profile until the Mi1 block and the gate and battery have run.
- Both rows are fitted to one *Drosophila* and one *Calliphora* number. The v₀ they imply is unmeasured.

**Next (pre-register first): the Mi1/Tm3 block on the v0 base.**
- Mi1: the Pm/Dm1 modes (graded against spiking; their light responses are unknown) and the GluClα reversal (M10Q −56 against −70).
- Tm3: the r0 and span of L1's release.
- Hold out Tm1/Tm2 OFF, L2 and the T4/T5 grating.

### Pre-registration: LMC output release reaches zero at the LMC's light-saturated potential (6 October, 04:19, before any run)

**Question.** F-VISION-9 puts Tm3's ceiling (about 4.3 mV) at L1's release floor: with the class release at rest r0 0.5 (guessed) and span 45 mV (Zheng et al. 2006, measured), L1's release can only fall from 0.59 to 0.31 as L1 swings from −43.7 to −68. Does lowering L1/L2's r0, alone, raise Tm3 and Mi1 as the one-compartment arithmetic predicts?

**Lever (inferred).** New switch `cell_type:all|release_at_rest_per_type` (neutral 0; per-type `release_at_rest` rows replace the class value for those graded cells; CPU and GPU both read the per-neuron array; unit test added). Rows: L1 and L2 `release_at_rest` 0.26.
- Principle: a graded synapse uses its presynaptic cell's whole voltage range, so release reaches zero where the LMC saturates in bright light (Juusola et al. 1996 TINS; Laughlin's matched coding). This is an inference, not a measured LMC release curve.
- Arithmetic: r0 + (1 − r0)(−68 + 52)/45 = 0 gives r0 = 16/61 = 0.26 (L1 light −68.0, L2 −68.2 in `cstate_v0`). The release reference stays −52 mV and the span stays 45.
- L3 is left at 0.5. It barely responds in this arm (−55.7 to −57.2 mV), so its floor is not the limit.

**Base.** The v0 arm (DECISIONS 04:05) unchanged, plus the switch and the two rows. The same flash protocol: i 0.001 and 0.01 (300:500, tail 400) and i 1 (300:1000, tail 600). Then the conductance state.

**Predictions** (derived from `cstate_v0` conductances, steady state, one compartment):

| Readout | Role | v0 arm | Prediction |
|---|---|---|---|
| L1 dark | check | −43.7 | −43.7 ± 1 |
| R→L1 gain, i 0.001 | check | 11.8 | 11.8 ± 1 |
| L1 release, dark → light | check | 0.59 → 0.33 | 0.40 ± 0.03 → ≤ 0.04 |
| Tm3 ON, full flash | held | +4.2 | **+7 to +11** (recorded +15) |
| Tm3 dark | held | −54.8 | −52.4 ± 1.5 |
| Mi1 ON, full flash | held | +2.3 | **+4 to +6.5** (recorded +20) |
| Mi1 dark | held | −59.0 | −57.2 ± 1.5 |
| Tm1 dark | held | −46.4 | −51 ± 2 (L2's tonic excitation falls by about 45%) |
| Tm1 / Tm2 OFF | held | +1.6 / +1.9 | larger (direction only; recorded +17.5) |
| L2 dark | check | −50.4 | −50.4 ± 1 |

No cell may leave [−90, 20] mV.

**Failure.** If Tm3 ON comes in below +6 or above +12, the one-compartment reading of F-VISION-9 is wrong; write up why, and do not try a second r0.

**Not adoption.** Even a pass leaves r0 0.26 inferred from a principle, and the working profile untouched until the Mi1 block, gate and battery have run.

### Result: LMC output release floor (6 October, 04:32; `runs/s12/vision/flash_v0r_i{0.001,0.01,1}`, `cstate_v0r`, about 10 min on backhouse; figure `docs/media/s12_vision_release_floor.png`, viewed; F-VISION-10; nothing adopted)

| Readout | Role | v0 arm | Prediction | v0r | Recorded |
|---|---|---|---|---|---|
| L1 dark | check | −43.7 | −43.7 ± 1 | **−43.7** pass | −43 ± 7.3 |
| R→L1 gain, i 0.001 | check | 11.8 | 11.8 ± 1 | **11.8** pass | about 13 |
| L1 release, dark → light | check | 0.59 → 0.32 | 0.40 ± 0.03 → ≤ 0.04 | **0.40 → 0.00** pass | |
| Tm3 ON, full flash | held | +4.2 | +7 to +11 | **+9.3** pass | +15 |
| Tm3 dark | held | −54.8 | −52.4 ± 1.5 | **−52.0** pass | |
| Mi1 ON, full flash | held | +2.3 | +4 to +6.5 | **+5.5** pass | +20 |
| Mi1 dark | held | −59.0 | −57.2 ± 1.5 | **−57.2** pass | |
| Tm1 dark | held | −46.4 | −51 ± 2 | **−51.1** pass | |
| Tm1 / Tm2 OFF | held | +1.6 / +1.9 | larger | **+2.8 / +3.4** pass | +17.5 |
| L2 dark | check | −50.4 | −50.4 ± 1 | **−49.8** pass | |
| Tm1 / Tm2 ON dip | extra | −4.4 / −3.7 | | −8.7 / −7.3 | present (Behnia 2014 Fig. 2) |
| T4a ON | extra | +1.0 | | +2.0 | |

No cell left [−90, 20] mV. Steady-state potentials from the conductance probe landed within 0.5 mV of the one-compartment predictions (Mi1 light −52.1 against −52.1, Tm3 light −43.3 against −43.0, Tm1 light −59.5 against −60.3).

**Reading.**
- F-VISION-9's Tm3 reading holds: L1's release floor was Tm3's limit. With release reaching zero at the LMC's light-saturated potential, Tm3 carries 0.62 of its recorded ON response, Mi1 0.27.
- Mi1 is now at the ceiling set by its tonic inhibition: in light, L1's share of its g_i is zero and 0.80 leak units of spiking Pm2b/Dm1/Pm2a/Pm1 inhibition remain. More Mi1 needs the Pm/Dm1 modes or the GluClα reversal, not the lamina.
- Tm3 in light sits at −43.3 with 0.27 leak units of tonic inhibition (Dm1, Pm9, Pm10) against a no-inhibition ceiling of −37.5. At most about 6 mV more is available from that inhibition.
- Tm1/Tm2 now dip on ON as recorded, but their OFF response is 0.16-0.20 of recorded. Their OFF is driven by L2 rising above its dark release after light-off, against 0.78 leak units of tonic Pm2a/Pm2b inhibition. That is the next OFF-pathway limit (not measured yet).

**Corrections.**
- The pre-registration said the CPU and GPU paths both read the per-neuron array. The GPU path refuses any nonzero release at rest (`gpu/batched.py` raises NotImplementedError), so the switch is CPU-only like the class value. `structural_keys.csv` says so.
- The 04:11 result said "L1 has no depolarising OFF transient at light-off in this arm". That is wrong. Connected L1 cells overshoot by a median +10.7 mV after light-off in the v0 arm (+10.6 in v0r, +13.4 at k 30, +1.5 at k 1). I misread it from the type-mean trace, which unconnected cells dilute to +4.7.

**Decided by Ben, 13 Oct (see the s13 entry at the end): yes, v0r is the vision diagnostic base, not the working profile.** The question, extending 04:11, was: should v0r (the v0 rows plus L1/L2 `release_at_rest` 0.26, inferred) become the vision diagnostic base? My recommendation is yes for diagnostics, and no for the working profile until the Mi1 block, gate and battery have run.

**Next (pre-register first).**
- The T4/T5 grating (V) on v0r, held out since 02:08.
- The Mi1 block: Pm/Dm1 modes and the GluClα reversal.
- The Tm1/Tm2 OFF limit: L2's OFF overshoot and Pm2a/Pm2b tonic inhibition.

### Pre-registration: T4/T5 grating on the v0r base (6 October, 04:33, before any run; launched 04:33:43)

**Question.** The relay's original failure was V: T4/T5 per-cell F1 or mean shift ≥ 0.5 mV in at least one direction for every subtype (DECISIONS 6 Oct, vision blank, with the 02:00 per-cell deviation). RTc gave T4 0.05-0.09 and T5 0.05-0.07 mV. Does v0r pass?

**Run.** `motion_grating.py`, the same stimulus and seed as RTc (30°, 1 Hz, contrast 1, 1 s per direction after 1 s static), on the v0r set: the gain-block base set, `leak_from_network_rest` 1, `release_at_rest_per_type` 1 and the three diagnostic rows (L1/L2 leak shift 15.1, R1-R6 release ×12.5, L1/L2 release at rest 0.26). There is one confound against RTc: the gain block's photoreceptor gain 78 (RTc 10) and the graded spans.

**Predictions** (coarse; derived from RTc's grating-to-input ratios and v0r's flash amplitudes, not from a model of the grating):
- Mi1 per-cell F1 1.5-3.5 mV, and Tm3 2.5-5.5 mV (RTc 0.28 / 0.35).
- T4a-d: per-cell F1 0.4-1.2 mV (RTc T4/Mi1 ratio about 0.3). **V passes for at least three of the four T4 subtypes.**
- T5a-d: no confident call. The Tm1/Tm2 OFF limit still applies; reported against 0.5.
- The direction index is reported, not required. The biological pattern is T4a/T4b and T4c/T4d preferring opposite directions.
- No cell leaves [−90, 20] mV. HS and VS rates are reported (RTc: HSE 149 Hz tonic).

**Failure.** If T4 F1 stays below 0.3 mV, then T4 is limited past Mi1/Tm3 (Mi4/Mi9/C3 inhibition or T4's own leak), and that is the next block. No second try tonight.

## Director order (02:10, received 04:35): stop route tuning; fill neuron and synapse dynamics model-wide (6 October, 04:36)

**Order.** Three of tonight's results share one root: the leg sugar per-route margin, GNG117's latch with nothing to switch it off, and flyapp's T4/T5 with the right ON/OFF split but no direction selectivity (DS needs fast against slow inputs). The model lacks neuron and synapse dynamics. Route tuning stops; the leg sugar margin stays a recorded diagnostic (it was never adopted). The work moves up the ladder model-wide, as item 1 of Ben's priority ("upgrades to fidelity up to synapse-specific"), not as a new direction. Each rung is a switch, filled from data where measured, by cell class where inferred, and labelled.

**The five rungs already have switches; what is missing is their fill.**

| Rung | Switch today (`lif.py`) | Fill today | Existing evidence notes |
|---|---|---|---|
| 1. Spike-frequency adaptation | per-type `adaptation_increment` (default 0, guessed) and `adaptation_tau` (200 ms, guessed); also rung-1 intrinsic channels (M-type K, BK/SK with a Ca pool) | none per type (F-SFA-1) | `docs/research/s12_central_fi.md`: no adult central f-I, AHP or adaptation ratio in open text (5 Oct search) |
| 2. Short-term depression/facilitation | per-type `std_release_fraction` (0) and `std_tau_rec` (500 ms); `afferent:ORN\|measured_depression` (Nagel 2015, U 0.22, τ 893 ms); rung 8 per connection (`stp_connections.csv`, 2 rows) | ORN only; off in m9c (F-STP-1: on, it silenced PNs because the ORN→PN weight was fitted without it) | Kazama & Wilson 2008; Nagel 2015/2016 |
| 3. Membrane noise | one global `background_noise` (profiles set 0, a modelling choice) | none per type | none collected |
| 4. Graded against spiking per type | `cell_type:all\|mode_from_recordings` (built tonight) | 7 `graded_rec` rows (Mi1, Tm1-3, T4, T5 measured; L4/L5 inferred) plus 3 `graded` rows | Behnia 2014; Gruntman 2018/2019 |
| 5. Per-type membrane time constant | per-type `tau_m` (default 20 ms, borrowed) | 1 row | `docs/research/s12_compartments.md` (Gouwens & Wilson 2009 passive cable) |

**Held-out tests for every rung** (fixed now, before any fill):
- the silence check: `closed_loop_check.py` silent window, 0 spikes/ms, plus the gate's no-runaway, no-NaN and thorax criteria;
- leg sugar: DECISIONS 00:41's checks (spontaneous GRN input and leg bitter ignored, a real sugar rate opens the route);
- labellar sugar plus bitter: the `assay_pathways.py` taste assays;
- T4/T5 direction selectivity: flyapp's eye harness (via the Director; I do not touch the flyapp worktree), and `motion_grating.py` open loop as the in-repo check.
- GNG117 persistence after a brief stimulus is a reported readout, not a target. Its transmitter is on Ben's list (HANDOFF 1j).

**Order of work.**
1. Survey measured values (started 04:35; one Sonnet Explore agent on the open literature: Gouwens & Wilson 2009, Behnia 2014, Groschner 2022, Wilson-lab ORN/PN/LN, Strother 2017, Gruntman 2018/2019, Azevedo 2020, Turner 2008, Hige 2015), merged with the s12 research notes above. Output: `docs/research/s12_dynamics_survey.md`, each number re-read in the source before use.
2. One pre-registration per rung: the fill rule (measured rows, then class priors with bounds, labelled), the predicted effect on each held-out test, and what would falsify it. Rungs 5 (τ_m) and 4 (modes) come first: they are the most measured, and they decide T4/T5 DS (Mi1/Tm3 against Mi4/Mi9 time constants).
3. Every fill runs the gate, the battery and a viewed contact sheet before any adoption.

**The vision work tonight is consistent with this.** The v0/v0r rows are per-type biophysical values fitted or inferred from physiology recordings (L1 dark potential, R→L1 gain), not from behaviour, and stay diagnostic. The Mi1 block's next lever (the Pm/Dm1 modes) is rung 4.

### Result: T4/T5 grating on the v0r base (6 October, 04:46; pre-registration 04:33)

Run finished 04:43 (backhouse, 543 s; `runs/s12/vision/grating_v0r.json`, md5 checked; figure `docs/media/s12_vision_grating_v0r.png`, viewed). Per-cell F1 per direction (az+/az−/el+/el−), mV:

| Type | RTc | v0r | Predicted | Score |
|---|---|---|---|---|
| Mi1 | 0.24-0.28 | 0.70-1.07 | 1.5-3.5 | FAIL (low) |
| Tm3 | 0.24-0.35 | 0.89-1.55 | 2.5-5.5 | FAIL (low) |
| T4a-d | 0.05-0.09 | 0.14-0.29 | 0.4-1.2, V for at least 3 of 4 | FAIL; V 0 of 4 (best 0.27-0.29) |
| T5a-d | 0.05-0.07 | 0.15-0.30 | no call | V 0 of 4 |

- Direction index 0.00-0.03 on every subtype (reported, not required). Every stage modulates 3-4× more than in RTc, and T4 still carries about 0.26 of Mi1 (RTc 0.3), so the T4 stage itself is no worse. The pre-registered failure clause (T4 below 0.3) is met, but Mi1 and Tm3 also missed, so the failure is in both places: the grating drive into Mi1/Tm3, and T4's transfer.
- Tonic spiking during the grating: CT1 400 Hz, Mi9 22 Hz, Tm4 21 Hz, HSN 150 Hz, HSE 132 Hz, HSS 27 Hz. The grating script does not record the [−90, 20] mV bounds; not scored.
- Diagnostic, measurement only (`visual_conductance_state.py --types T4a,T4c,T5a,Mi4,Mi9,C3,CT1`, `runs/s12/vision/cstate_v0r_t4.json`): T4a inhibition is 0.37 leak units, 0.24 of it from CT1 firing tonically at 400 Hz; Mi9 gives 0.02 and Mi4 about 0. T5a: 0.56, of which CT1 0.45. Mi4 and Mi9 run in spiking mode near −49 mV and light moves them by 0.3-1.5 mV. **T4/T5 have no modulated slow arm and their inhibition is a tonic CT1 shunt, so direction selectivity cannot appear.** Mi4, Mi9, C3, Tm4, Tm9 and CT1 have no mode row; their mode and kinetics are rung 4 and rung 5 of the Director's 02:10 order.
- Nothing adopted. No second try (as registered). Next: the rung plan (DECISIONS 04:36), with this grating and flyapp's T4/T5 direction command as held-out tests.

## Session 13 decisions (Ben via the Director, recorded 13 October, 21:32)

**v0 and v0r (answers the open questions of 04:11 and 04:32).** v0r becomes the vision DIAGNOSTIC base, not the working profile (m9c stays). fly2 is importing flyvis (Lappalainen 2024) this run, which may supersede it, so no more hand-tuning of the eye here.

**Silence gate for the eye (F-VISION-5): option (a).** Count only non-optic spikes in the silent window, and require optic activity in darkness to be stationary: eye spikes in the last 100 ms may not exceed the previous 100 ms by more than 3 Poisson SDs (3·√(prev+last)). Tonic lamina release in the dark is biology. `closed_loop_check.py` now reports `silent_eye_stationary` and `silent_pass` (both halves).

**Next block: motor-pathway bypass and rescue assay before more mechanism work** (Director, from brainstorm 13 Oct B and F). Stages S1 actuation, S2 descending drive, S3 graded release and signs, S4 feedback; each pre-registered in one line with a pass criterion. Output: a failure-localisation report. Forced drive is a diagnostic, not emergent walking. The mushroom body at 0 Hz waits behind it.

### Pre-registration S1, actuation with the CNS bypassed (13 October, 21:36, before any run)
`bypass_s1_actuation.py`, m10f0, adhesion 1, 3 s, patterns support/coact at activation 0-1 (DIAGNOSTIC, forced drive). **Pass:** at some activation ≤ 0.5 (plausibility bound guessed), the thorax origin stays ≥ 0.9 mm (standing ≈ 1.0 mm, inferred from Wang 2025), sinks < 0.05 mm over the last 2 s, the leg floor force is 0.8-1.2× body weight, and the trunk never touches the floor. **Fail** localises to the static audit (unmapped muscles or MNs, moment arm, force-length at pose) or to contact.

### Pre-registration S2, descending drive with the brain off (13 October, 21:41, before any run)
`bypass_s2_descending.py`, m10f0, brain silenced (non-VNC output removed), senses off, thorax tethered 1 mm up; constant drive 300-1300 ms into DNg100 at 10/15/25/40 mV, then DNb08 (Pugliese's second pathway), DNg97 (oDN1) and DNa02 (DIAGNOSTIC, forced drive). **Pass:** at a drive keeping the driven DNs ≤ 200 Hz (bound guessed), some leg MN pool has an MN with rhythm excess > 0.10 at 4-25 Hz (F-RHYTHM-1 score) and is anti-correlated with its antagonist pool (r ≤ −0.3, 20 ms smoothing; Pugliese 2025's within-leg readout) or with its left-right mate. Reference: Pugliese 2025 rate model, about 7-15 Hz; Bidaye 2020 air-stepping about 11 Hz (secondary source). A fail is localised along the recorded chain: DN rate, premotor recruitment, MN rate, activation.

### S1 addendum, written after the first S1 sweep (13 October, 21:50)
Two measurement fixes, found by looking at the first sweep's frames, apply to every S1 run from now on: a foot is a tarsal segment only (the coxa had counted as leg, so a fly lying on its coxae scored as standing), and the adhesion pull is reported and subtracted from the foot force (adhesion presses the feet down, so foot normal force exceeded weight in every lifted run). The pre-registered criterion is scored as written on the first sweep. New pattern **need** (DIAGNOSTIC): each muscle at the activation that supplies exactly the measured static hold torque, times k in {0.5, 1, 1.5, 2}; a 1.5 s test at k = 1 was run while writing the code (sank 1.29 to 0.88 mm). Pass as S1, with the foot force taken net of adhesion and any non-tarsus floor contact counting as trunk contact.

### Results S1 and S2 (DNg100), 13 October, 21:58 (F-BYPASS-1, F-BYPASS-2)
S1 fails as pre-registered. The legs lift the fly, but no constant activation holds: distal muscles are short of the static hold at the placed pose (hind TiTa 6.1×, FTi 1.3-1.5×), force-length is flat over the joint range, the abdomen drags, and 12 mid/hind coxa promotors have no MN. S2 (DNg100, brain off) fails at 10-40 mV: E1 and E2 fire at 13-18 Hz, I1 is silent, MNs stay tonic. Next: S3 (graded VNC interneurons, sign and scaling audit), since I1's recruitment is the first broken link.

### Results S2 (DNb08, DNg97, DNa02), and the reference check on Pugliese's own spiking model, 13 October, 22:09 (F-BYPASS-2 addendum, F-BYPASS-3)
S2 fails for all three remaining DNs at 15 and 40 mV (frames `docs/media/s13_bypass_s2_other.png` and rasters `docs/media/s13_bypass_s2_rasters.png`, both viewed): the MNs stay tonic, with no alternating pool. Reference check (F-BYPASS-3): Pugliese's own LIF (their Extended Data Fig. 4 code, Shiu parameters) oscillates on their MANC T1L mini-circuit, but on the same circuit taken from their male-CNS extract it never brings I1 to threshold. Our I1 failure therefore reproduces in their formulation and is not an implementation error.

### Pre-registration S3, graded release and synaptic scaling in the VNC (13 October, 22:09, before any S3 run)
DIAGNOSTIC, forced drive. `bypass_s2_descending.py` unchanged (m10f0, brain silenced, senses off, tethered 1 mm, DNg100 drive 300-1300 ms) at 15/25/40 mV, with one arm per row. No value is fitted; each arm is one existing class-level switch.
- **A, literature list** (`cell_type:all|mode_from_recordings` = 1, with two new `graded_rec` rows, `^IN13B\d+$` and `^IN10B\d+$`: 95 + 33 types, 433 + 254 cells). Agrawal et al. 2020 eLife 9:e60299 recorded 13Bα as nonspiking (all cells) and 10Bα as largely nonspiking (measured for those subsets; extended to the hemilineage by type name, so inferred). No recording exists for 16B, 17A or 19A (Sonnet sweep, 13 Oct).
- **B, class unknown** (`mode:n1_p_graded_vnc_local|graded` = 1): every VNC local type of unknown mode is graded (2,778 types, including E1, E2, I1 and IN19A007). This is the assumption behind Pugliese's rate model ("some neurons in the insect VNC, including premotor neurons active during walking, are nonspiking"). Prior 0.5, guessed.
- **C, count scaling** (`connection_class:vnc_sensorimotor|efficacy_scale` = 1.754, which is 0.275/0.15675): the VNC intrinsic and motor edges get Shiu 2024's per-synapse efficacy, the value Pugliese's LIF uses, instead of our whole-brain stability ceiling. Borrowed, so inferred.
- **D, A + C.**

**Pass** (Ben's brief): at a drive keeping DNg100 ≤ 200 Hz, alternating MN output in at least one leg pair. Scored with S2's criterion unchanged: an MN with rhythm excess > 0.10 at 4-25 Hz whose pool has r ≤ −0.3 against its antagonist pool or its left-right mate. The rasters and frames must also show it on viewing; a score without visible alternation is a fail.

**Also reported, not scored:** the oscillator cells per neuromere (`bypass_s3_chain.py`, network only, 25 mV per arm): whether I1 or IN19A007 is recruited every cycle, and the cycle frequency against Pugliese's 7-15 Hz.

**Falsifier and localisation:** if no arm passes, mode and per-synapse scale are not the break, and it moves to premotor→MN transmission (the sign and count audit, reported alongside) or to the MN layer.

**Held out:** nothing is fitted, so no data are spent. If an arm passes, then before any adoption: silencing E1 or E2 must abolish the rhythm (Pugliese's in-model result); DNb08 drive must also alternate; and the gate and resting rates must hold with the brain on.
- 22:11 addendum to the S3 pre-registration (before any S3 run). A run of Pugliese's own LIF on their MANC mini-circuit (F-BYPASS-3) shows that 1 of 25 MNs carries the rhythm there too. So "at least one leg pair alternates" means one antagonist or left-right pair, scored as already registered; I am not counting how many pools are recruited.
- 22:18, calibration note, written before any S3 score has been seen. I ran Pugliese's own rate model (their repository at 10e7661, their DNg100_Stim configuration, Mac CPU at relaxed tolerances as a smoke test; the GPU run at paper tolerances is queued on backhouse):
  - MANC, I 250: oscillation score 0.91 at 11.4 Hz, 3 active MNs.
  - Male CNS, DNg100 R, I 400: score 0.999 at 12.0 Hz, 7 active MNs, all left T1: 2 coxa swing promotors, 1 coxa stance remotor, 4 trochanter flexors.
  - Their swing and stance MNs are both rhythmic but lag each other by only 12-17 ms of an 83 ms cycle. At zero lag they correlate positively (r +0.20 to +0.44), so no pair reaches S2's r ≤ −0.3. The reference model would therefore fail our pre-registered criterion.
  - The S3 pass criterion stays as registered (primary). Also reported, never counted as a pass: a lagged readout. It flags a pair of a leg's MN pools that are both rhythmic (rhythm excess > 0.10, 4-25 Hz) with the peak of their cross-correlation (lags within ±45 ms) at |lag| ≥ 10 ms and r ≥ 0.5. Its purpose is to set the criterion for S4 against the reference.

### fly2 pre-registration: flyapp T4/T5 direction test on v0r + flyvis (13 Oct, 22:05)
Call: `app/tools/t4t5_ds.py` (held out, never run on v0r), seed 0, both sets, profile m9c + the 7 v0r `--set`s + `cell_type:all|optic_lobe_flyvis=1`, `--extra-params data/params/candidates/candidates_s13_v0r.csv`, model root = a detached checkout of fly2 commit 18d6f8f (this entry as first committed, before the rebase onto main). v0r alone is called only if this passes any subtype (to attribute it).
Prediction: FAIL in both sets (fewer than 8 subtypes selective as in flies). Reason, measured before the call: in the 50 flyvis networks themselves DS needs type-pair strengths (10 networks, median DSI over subtypes: published 0.40 medulla / 0.49 photoreceptor, tau 20 ms 0.32 / 0.32, per-type-product strengths 0.02 / 0.06; `runs/vision/flyvis_ablate_ds_{0-4,5-9}.csv`), and the import carries only per-type mode, tau and release at rest. The flash run also shows CT1 saturated at -11 mV.
Falsifier: all 8 subtypes selective as in flies in either set. Diagnostic rung: nothing is adopted either way.

### fly2 pre-registration: giant-fibre escape latency, gap junctions off vs on (13 Oct, 22:18, before any run)
`scripts/probes/gf_latency.py`, profile m10f, seed 0, isolated CNS (network only, noise on); both GFs kicked to one spike every 50 ms, 20 trials, arms `electrical:all|gap_conductance` 0 and 1. Latency to muscle = first MN spike within 10 ms − GF spike + the MN's delay row (axon L/v + 0.5 ms neuromuscular). Reference: Augustin et al. 2017 S1 Table, WT brain stimulation, young to old means: TTM 0.926 (SEM 0.03) to 1.216 ms, DLM 1.440 (SEM 0.04) to 1.849 ms. Band: young mean − 2 SEM to old mean (TTM 0.866-1.216, DLM 1.36-1.849).
Prediction: off, TTMn follows under 50% of trials or TTM lies above the band; on, TTM is about 1.1 ms, in the band, and followed in ≥ 90% of trials; DLM on lies above the band (about 2 ms), since PSI→DLMn is chemical (0.5 ms + inferred L/v + integration) plus DLMn's 0.8 ms row.
Falsifier for the GF rows: the on-arm TTM median falls outside the band, or TTMn follows in under 90% of trials. TTM is not held out: the brain-minus-thoracic difference (0.25 ms ≈ GF conduction) set the no-chemical-delay rule, so TTM is a consistency check. The DLM values were not used. Diagnostic: nothing is adopted.

### fly2 result: GF escape latency (13 Oct, 22:24)
Gaps off: TTMn, PSI and DLMn follow 0/20 GF spikes. Gaps on: TTMn and PSI follow 20/20, TTM 1.099 ms to muscle, inside the 0.866-1.216 band, so the TTM falsifier did not fire. A consistency check only: 1:1 following is built in, and the latency is the sum of delay rows. DLM prediction failed: there was no DLMn spike in either arm, because PSI has no transmitter in male-cns (sign 0). PSI→DLMn is cholinergic (Fayyazuddin 2006). DLM latency is now spent on m10f. Nothing adopted; the switch stays neutral (F-GJ-3).

### fly2: N29 receptor decay per connection, and the pre-handoff smoke criterion (13 Oct, 22:33, before the run)
New neutral switch `synapse:all|receptor_kinetics_per_connection` with table `data/params/receptor_kinetics.csv`. It has 3 rows, all inferred: ORN→PN 1.1 ms, fitted (Gouwens & Wilson 2009); ACh→KC 1.4 ms and GABA→KC 3.7 ms, measured in culture (Su & O'Dowd 2003). Charge per spike is kept; current-based synapses only; CPU only. Found no STP numbers to add (searched GF/PSI pathway, PN→KC, KC→MBON, LN→PN, R1-6→LMC). Smoke: `smoke_live.py` m10f, seed 12, 5 s, with gap_conductance, per_synapse_parameters and receptor_kinetics on. Pass: no runaway, no NaN, and whole-brain rate within ±50% of m10f0 seed 12 (0.324 Hz over 60 s). A pass means the fly worker can take it, not that it is adopted.

### fly2 pre-registration: GF→PSI→DLM with PSI cholinergic (13 Oct, 22:35, before the run)
New neutral switch `connectome:identified|nt_from_physiology` (table `transmitter_physiology.csv`; PSI = acetylcholine, Fayyazuddin 2006, measured). Run `gf_latency.py` m10f, seed 0, 20 trials, with this switch on (gaps off and on). The DLM latency is spent (F-GJ-3), so this is a consistency check only. Prediction: gaps on, if DLMn fires, the delay rows put DLM at about 2.1-2.3 ms, above the 1.36-1.849 band. Reason: PSI L/v 0.30 ms + 0.5 ms synapse + integration + DLMn L/v 0.35 ms + 0.5 ms neuromuscular. If the PSI synapse sits on the DLMn axons outside the VNC, as its name says (King & Wyman 1980, not read), then per-type point delays count the path twice. Gaps off: DLMn follows 0. Nothing adopted either way.

### fly2 result: pre-handoff smoke, gaps + N29 STP + receptor decay on m10f (13 Oct, 22:45)
Pass on the 22:33 criterion (`runs/s13/fly2/smoke_m10f_gap_n29_s12_5s.json`): no runaway, no NaN, 0 MuJoCo warnings, whole brain 0.307 Hz against 0.324 (−5%), 2.65% of cells active, median active cell 11.8 Hz. Max cell 57.6 Hz against 221 in the 60 s m10f0 run; the windows differ (4.5 s against 60 s), so that is not compared. The fly worker can take the three switches into a candidate; none is adopted (that needs the 60 s smoke, the silence gate, a battery and a viewed figure).

### fly2 result: GF→PSI→DLM with PSI cholinergic (13 Oct, 22:48)
PSI now follows 20/20 GF spikes (gaps on); DLMn follows 0/20 in both arms, so the conditional DLM latency prediction is untestable and gaps-off matched. Measured reason (F-GJ-4): one PSI spike gives DLMn 0.47-1.65 mV against a 7 mV threshold gap; Fayyazuddin 2006 measured 4.71 ± 0.35 mV at the MN5 soma, with the PSI contacts on the axon into the nerve. The shared synapse scale is 3-10× low, and a point neuron cannot carry an axonal relay. The switch stays neutral; Ben decides on a per-pair measured EPSP vs waiting for N30.

### fly2 result: flyapp T4/T5 on v0r + flyvis (13 Oct, 22:48)
FAIL in both sets, 0 of 8, as pre-registered 22:05 (F-VISION-12; sheet viewed). Medulla inputs respond with the recorded polarity (Mi4 +3.6, Mi9 −3.3 mV); T4 rises 0.6-0.8 mV to every direction (DSI ≈ 0). The photoreceptor set barely passes the lamina. Reason measured beforehand: flyvis DS needs its type-pair strengths. v0r alone is not called (rule: only if this passed). The T4/T5 call on v0r + flyvis is spent. Nothing adopted; type-pair strengths go to Ben.

### Ben (via Director) decisions for fly2, 13 Oct 22:53
1. flyvis type-pair strengths: YES, as a separately switched arm labelled "fitted (flyvis, task-trained)" (shared by type pair, published, connectome-constrained). Conditions: each pair strength × synapse count must give a PSP inside the measured range for its class (flag outliers, never clip silently); stays out of the frontier profile until a held-out physiology check passes (T4/T5 tuning or Mi1/Tm3 recordings flyvis was not trained on); CT1 compartmentalised as in flyvis.
2. PSI→DLMn 4.71 mV: YES, as a MEASURED value for that one identified connection, recorded as a scan-gap fill (part of the contact lies in the nerve outside the volume; the synapse is axonal), not a free knob. Check the claim against Fayyazuddin 2006 / the primary source first; revisit when N30 exists.
3. Order: both queued behind the body-interface block (Director 13 Oct: the body cannot stand under any constant activation, F-BYPASS-1). fly2 fast-forwards main now (fly idle).

### Results S3, 13 October, 23:10 (F-BYPASS-4)
FAIL on all arms (A, B, C, D at 15/25/40 mV). B passed the scorer at all three drives, but viewing shows a VNC-wide runaway that continues after the drive stops: DNg100 is suppressed, the body convulses, and the raster shows no alternation. Per the pre-registration that is a fail. No held-out data spent; nothing adopted; m10f0 unchanged. The `graded_rec` rows for 13B/10B stay in cell_types.csv. They are read only under `cell_type:all|mode_from_recordings = 1` (neutral 0), so m10f0 is unaffected.
- **23:13, GPU reference collected** (F-BYPASS-4 addendum). Male CNS at I 400: score 1.00 at 10.4-12.0 Hz. One zero-lag promotor/remotor pair at r −0.31, on the L side only. So the reference just meets the S2/S3 criterion on one side and misses it on the other, which keeps the 22:18 calibration note valid. An S4 criterion should keep r ≤ −0.3 OR a pre-registered lagged-phase readout. It should also require per-cycle MN modulation depth, because that is the variable that separates us from the reference. Write it down before any S4 run.

### S4 step 1: what our model does differently from Pugliese's at the oscillator→MN step, written before any change (13 October, 23:31; F-BYPASS-5)
Director brief (23:15): the reference is a rate model in arbitrary units and drives 4-7 of 130 MNs, so it is a reference for oscillator→MN transfer, not for walking. The difference is the mechanism. Full numbers in F-BYPASS-5. In short, at the same synapse counts:
- **Threshold:** a median-sized cell in their model reaches threshold at 250·size synapse·Hz (θ 7.5, W 0.03 per synapse). Ours needs 8,932/g (7 mV gap, 0.15675 mV per synapse, τs 5 ms). For the core's target MNs ours needs 14-25× more input.
- **Gain above threshold:** ours is 0.17-0.22× theirs. Spike-triggered Kv2/BK/SK halve our f-I slope (3.3 against 6.1 Hz/mV).
- **Input units:** theirs is a rate passed on instantly and continuously. Ours is one spike per core cell per cycle, giving a PSP of 0.06-3.5 mV against a 7 mV gap. So 1 E2 spike gives 0 MN spikes, 2 give 0, and 3-5 give 1.
- **Size:** their threshold and gain scale with every cell's volume (a size principle across all cells). Ours varies input gain within type only. Between types, every non-slow MN shares one set of membrane values.
- **Leak and time constants:** both use τ 20 ms. Ours adds τs 5 ms, so a spike's PSP peaks at 0.157× the weight.
- **Tonic slow tibia flexors:** ours fire 23 Hz on a fitted spontaneous drive. Theirs rest at 0.

Measured values touch only one of these: MN input resistance by class (Azevedo 2020: fast 150, intermediate 300, slow 700 MΩ). The scale (theirs fitted to oscillate, ours a brain-stability ceiling) and the core's burst output are unmeasured.

### Pre-registration S4a: oscillator→MN transfer, two shared arms (13 October, 23:31, before any S4 run or code change)
DIAGNOSTIC, forced drive. Same harness as S3: `bypass_s2_descending.py`, m10f0, brain off, senses off, tethered 1 mm, DNg100 at 15/25/40 mV for 300-1300 ms. Each arm is one new neutral switch (off by default):
- **R, MN input resistance by type (measured Rin, derived mapping).** Leg-MN input gain ∝ Rin(V), where V is the cell's EM volume and Rin(V) runs through Azevedo 2020's three classes (fast 150, intermediate 300, slow 700 MΩ; measured) via the repo's volume law, exponent 1.49 (F-PERCELL-1; derived, already fitted, so not held out). The arm extends that law from within type to between types. It is normalised so the median leg MN keeps gain 1 (guessed normalisation), so the arm redistributes gain and does not rescale it. Predicted from F-BYPASS-5: the trochanter flexors (small) gain about 2×, the promotors and remotor (large) lose about 2×. Some TrF pools may reach the transfer bar, but no antagonist pair alternates.
- **G, glutamate sign on leg MNs = +1 (one shared arm, inferred).** The receptor evidence is mixed. Allen 2020 finds GluClα in 39-70% of cells in every VNC hemilineage, alongside GluRIA/GluRIB; MN clusters co-express GluClα with NMDA and kainate subunits. No leg-MN glutamate PSP has been recorded. The excitatory sign was tried before on the tibia flexors only, and it failed its held-out reflex (F-AZ-2; spent). Glutamate is 19% of the premotor input to leg MNs. Prediction: more MN drive overall, with tonic rather than rhythmic output.
- **RG:** R + G.

**Readout** (`scripts/probes/bypass_moddepth.py`, calibrated 23:20-23:30 on the reference and on the S2/S3 traces only). For each pool over 500-1300 ms:
- f0 is the pool's spectral peak in 7-15 Hz (Pugliese 2025's range);
- per-cycle depth m_k = (on − off)/(on + off), using the half-cycle with the most activity;
- cycles with fewer than 3 pool spikes score 0 (the floor is guessed);
- depth = median m_k.

Reference depth: male CNS 0.59-0.80 (DNg100 R) and 0.35-0.78 (L); MANC 0.63-0.67. Calibration found that the tonic tibia flexors (23 Hz, synchronous) look modulated at their own firing frequency. So a pool counts only if it is drive-dependent: rate ≥ 2× pre-drive, or silent before drive.

**Transfer pass (per pool):** drive-dependent, f0 in 7-15 Hz, depth ≥ 0.5, and the 3-spike floor reached on ≥ 2/3 of cycles.

**Baseline, before any arm** (all 22 S2/S3 runs): one pool passes, S2 DNg100 40 mV, right-hind coxa-trochanter +1 (depth 0.50, 4.4 spikes per cycle). Every other run has none. So a single pool does not separate arms.

**S4a pass:** at DNg100 ≤ 200 Hz, two antagonist pools of one leg both meet the transfer pass, and their phase relation shows either r ≤ −0.3 at zero lag or a lagged peak (lag 10-30 ms, r ≥ 0.5; the reference has offsets of 12-25 ms). Two further conditions:
- on viewing, the rasters and frames show the bursts;
- activity stops after the drive (post-drive pool rate ≤ 1.5× pre-drive).

Also reported, not scored: the number of transfer-pass pools against the baseline (0/0/1 at 15/25/40 mV).

**Held-out check (Ben's item 2), with a correction.** Azevedo 2020 has no f-I curve for fast or intermediate MNs: current injection did not evoke spikes in them. The slow-MN f-I is already spent (F-AZ-2/3, F-RUNG1-2). So the f-I check as briefed cannot be run. In its place, the held-out check is the recruitment order across classes: slow, then intermediate, then fast (Azevedo 2020, measured; never fitted). In arm R, the intermediate tibia flexors must start firing at a lower DNg100 drive than the fast ones, or else the arm fails the check. Azevedo's resting potentials (−68/−60/−48 mV) stay held out. R does not touch them.

**Falsifier:** if R, G and RG all fail S4a, then per-type MN properties and the glutamate sign are not the break. What remains is the scale (14-25×) and the core's single-spike output, and neither has a measured value. Both would go to Ben's list: a unitary premotor→MN PSP recording, and an E1/E2 burst recording.

No adoption from S4a. A pass goes on to the held-out tests: silencing E1/E2, DNb08 drive, and the gate and rest with the brain on.

### S4a switches built, run launched (13 October, 23:40; no adoption)
Director brief 23:3x: run S4a as registered, then pre-register S4b (bounded fit of two shared VNC-class quantities). Built, neutral at 0, CPU path (`percell.py`, `lif.py`), tests in `tests/test_percell.py` (17 passed with hygiene):
- **R** `cell_type:leg_motor|between_type_size_exponent` (1.49 for the arm): leg MNs = vnc_motor with subclass fl/ml/hl (381 cells). Factor (median leg-MN volume / type geometric-mean volume)^γ on top of the within-type law; incomplete cells take their type's factor. Factors span 0.30 (Ti extensor) to 12 (MNml76, a one-cell type). **Pre-registration prediction partly wrong before any run:** promotors 0.42 and remotor 0.46 (predicted ~0.5, right), but Tr flexors 0.88 (predicted ~2×; wrong, their type mean is near the median). Ti flexor type 0.80.
- **G** `cell_type:leg_motor|glutamate_receptor_sign` (+1 for the arm): sets the glutamate sign on all 381 leg MNs, overriding per-type rows.
- GPU: R is an input_gain change and G a static weight transform, both inherited by `BatchedNetwork` from the reference build. `scripts/gpu_bench.py equiv` gained `--set`; the R+G check runs on backhouse alongside the 9 S4a runs (`~/fly-m10f/runs/s13/bypass/s4a/run.sh`, done-files, ALL.done). Scoring follows the 23:31 pre-registration unchanged.

### fly2 body block: what Wang 2025's standing height measures (13 Oct, 23:16)
Read in the primary text (Europe PMC full text, PMC12324252, eLife RP107390, Wang, Babski … Bhandawat), plus a Sonnet check:
- **Experiment (measured):** "we automatically tracked a point on the fly's head in all views" (DeepLabCut, 4 views, 3D). Free-standing VGlut-Gal4 > GtACR1 flies in a 25 × 10 × 10 mm chamber, n = 92 trials from 8 flies. Fig 5C: "the starting height varies from 0.4 mm to 0.1 mm in this fly". Methods 7: "The median height of the fly was 0.5 mm."
- **Zero (inferred, not stated):** a head point 0.1 mm above an absolute floor is impossible, so the height is above the collapsed position the fly falls to. This agrees with the s12 reading (`targets_session6.csv` row 61). It is the head, not the thorax or the CoM.
- **OpenSim (a different quantity):** Fig 4D plots the model's "final thorax center-of-mass height". The 40×/90×/100× stiffness factors map the experimental head heights onto that curve. They are model values, not measurements.
- **Pratt 2024** (Curr Biol, DOI 10.1016/j.cub.2024.08.006): "the vertical distance between the ground and thorax" (absolute, DLC + Anipose, treadmill, walking). The 0.51 BL value is read off Fig 1H, not stated in the text. The point is unspecified, so it cannot be placed on our mesh without assuming one; not used.
- **For this body (derived):** the collapsed head point is 0.429 mm (S1 level 0, `runs/s13/bypass/s1/support/s1_m10f0_adh1.json`). Wang's median standing head is therefore 0.929 mm, against 1.32 mm thorax origin at flybody's neutral placement. Wang's height becomes a SETTING here, so it is spent as a validation target (register updated).

### fly2 pre-registration: S1 fix 1, the fly placed at Wang's median head height (13 Oct, 23:16)
- **Change (instrument only, no parameter):** `bypass_s1_actuation.py --head-mm 0.929`. After `place_standing`, the root is pinned (position and orientation) and lowered over 300 ms, then held for 100 ms, with no activation and no adhesion. The unpowered legs fold where the floor pushes them. Joint angles: inferred (passive fold), not measured; no measured standing joint-angle table was found (Wang has none).
- **Seen before writing this (unscored smoke, Mac, 200 ms, need k = 1):** placed thorax origin 0.96 mm, pitch 0. Hold need: hind TiTa 1.50× capacity (was 6.1×), every other pair ≤ 0.9×, pair max 1.502. In the frame, the legs fold out sideways, and head, abdomen and coxae touch from the start. The fly sinks to 0.57 mm.
- **Runs (backhouse, m10f0, seed 12, adhesion 1, 3 s):** need k = 0.5, 0.75, 1, 1.25, 1.5, 2; support 0.1, 0.2, 0.3, 0.5. Frames at 0, 250, 1000 and 3000 ms.
- **Pass (`holds_prereg`, per run):** trunk touch fraction 0 (no head, thorax, abdomen, coxa, femur or tibia on the floor); sink over the last 2 s < 0.05 mm; |z_final − z_place| ≤ 0.15 mm; |pitch change| ≤ 10° throughout; net foot support 0.8-1.2 W; final head ≥ 0.1 mm above the collapse (Wang's lower bound); no NaN. "Plausible constant activation" means need k ≤ 1 with no muscle clipped at 1, or support ≤ 0.5. The contact sheet must be viewed.
- **Prediction:** FAIL on trunk touch at every level, because the passive-fold pose puts the abdomen down. The hind TiTa need at 1.5× is clipped at k ≥ 0.67.
- **Falsifier for "pose alone closes the gap":** any run passing.
- **If it fails:** the next fixes are (i) a placement that keeps the legs under the body (pitch joints only), then (ii) the LTM Hill muscle, if a sourced force exists. Each gets its own pre-registration.

### fly2 result: S1 fix 1 (13 Oct, 23:25)
FAIL 0 of 10, as predicted (F-STAND-4; sheet `docs/media/s13_bypass_s1fix1.png`, viewed). The passive fold splays the legs, the fly ends on its belly at the collapse height at every level, and the active legs swing up into the air. The fix 1 hold-need numbers are confounded by trunk contact at placement.

### fly2 pre-registration: S1 fix 1b, legs folded in their pitch planes (13 Oct, 23:26)
- **Change (instrument only):** `--head-mm 0.929 --pitch-only`, the same lowering as fix 1. During the lowering, the instrument springs (K_HOLD 200 µN·mm/rad, D_HOLD) hold the thorax-coxa yaw and roll and the trochanter-femur roll of every leg at their neutral angles, and are removed before the run. Pose: inferred (pitch-plane fold), not measured.
- **Gate 1 (placement, checked before any run):** at the placed pose, no head, thorax, abdomen, coxa, femur or tibia touches the floor. If anything does, fix 1b fails at placement, no run is launched, and that is the result.
- **Runs (if gate 1 passes; backhouse, m10f0, seed 12, adhesion 1, 3 s):** need k = 0.5, 0.75, 1, 1.25, 1.5, 2; support 0.1, 0.2, 0.3, 0.5.
- **Pass:** the same `holds_prereg` criteria as fix 1 (DECISIONS 23:16), the same plausibility rule, and the sheet viewed.
- **Prediction (written before the placement check):** gate 1 passes or nearly passes, because the abdomen hangs below the thorax and its clearance at 0.96 mm thorax origin is unknown. The need runs then fail on sinking, because the force-length curve is flat (F-BYPASS-1). A constant need k > 1 may hold for a while.
- **Falsifier for "a pose with the legs under the body closes the gap":** any run passing.

### fly2 result: S1 fix 1b (13 Oct, 23:36)
FAIL 0 of 10, as predicted (F-STAND-5; sheet `docs/media/s13_bypass_s1fix1b.png`, viewed). The pose hypothesis is dropped: the original 1.32 mm placement already puts the head 0.86 mm above the collapse, inside Wang's measured range, and lowering made standing worse. The hold-need instrument lets the trunk reach the floor at lowered poses (the floor carries 0.93 W), so need patterns there are invalid. `--head-mm` stays as an instrument and is not the default.

### fly2 pre-registration: S1 fix 2, a tibia-tarsus capacity from an inferred bound instead of the guessed placeholder (13 Oct, 23:36; not run)
Both steps run at the original placement (`place_standing`, thorax origin 1.32 mm, head 0.86 mm above collapse, inside Wang's range).
- **Step 0, instrument check (before any fix):**
  - Rerun `hold_need` at 1.32 mm with the non-foot contact record.
  - If the floor carries > 0.05 W, or anything but the feet touches during the hold, raise K_HOLD (×5, then ×25) until the sag is < 0.01 mm and only the feet touch. Report the converged need; the 6.1× is valid only if it survives.
- **Step 1, the change (a new neutral switch, off by default):** the TiTa pair's F0 = tibia cross-section × specific tension.
  - Cross-section: inferred, from flybody's tibia mesh at mid-length (outer section, an upper bound, because the wall thickness is unknown).
  - Specific tension: 28 mN/mm² (FlyMimic's choice, inside the measured 9-37). Run at 9, 28 and 37 to give the range.
  - Moment arm r: inferred, half the distal tibia diameter (an upper bound).
  - Shared by type across all six legs, scaled by segment size like the other mid/hind rows. Labelled inferred, with the derivation in the CSV.
  - No muscle-specific Drosophila value exists (research note addendum 23:30). No held-out check that isn't standing exists for this value, so it can only be "consistent", never "validated".
- **Runs (backhouse, m10f0, seed 12, adhesion 1, 3 s):** need k = 0.5, 0.75, 1, 1.5 (from the step 0 need); support 0.1, 0.2, 0.3, 0.5; each specific tension.
- **Pass:** `holds_prereg` (DECISIONS 23:16) plus a placement-relative height test: |z_final − 1.32| ≤ 0.15 mm. The activation must be plausible (need k ≤ 1 with nothing clipped, or support ≤ 0.5), and the sheet must be viewed.
- **Falsifier for "distal capacity is the bottleneck":** if nothing holds even at 37 mN/mm² (the bound's top), capacity is ruled out. The next question is then stability under constant activation: the flat force-length curve and the lack of feedback (F-BYPASS-1; S4 belongs to the fly worker).
- **The LTM is deferred.** It acts on the tarsal chain, not on TiTa, and no source exists for it. It comes after step 1 and uses the same inferred-bound route if needed.

### fly2 addendum to the S1 fix 2 pre-registration, written before any step 1 run (13 Oct, 23:40)
Director brief (after /clear, 13 Oct ~23:37). These points sharpen the interpretation of fix 2; its criteria are unchanged.
- **What fix 2 can and cannot show.** An awake fly does not stand on constant activation. It stands on tonic drive plus resistance reflexes: the femoral chordotonal organ (FeCO) and campaniform sensilla (CS) drive leg MNs against imposed joint movement (the classic insect postural loop). So S1 under constant activation tests only whether the muscles CAN carry the weight at the placed pose. It does not test whether the fly stands as a fly does.
  - If any run passes at 9-37 mN/mm²: distal capacity was the bottleneck, and the placeholder TiTa pair was too weak to carry the weight. A pass is not evidence that the fly could stand without feedback; the passing activation is a setting for the next step, not a fitted posture.
  - If nothing passes even at 37: capacity is ruled out as the only break, and the failure is stability: constant activation with a flat force-length curve has no restoring force (F-BYPASS-1).
  - **Either way, the next body-side step is fly2's, not fly's:** a minimal measured proprioceptive loop. FeCO and CS afferents already in the connectome, driven by their measured encoding (FeCO claw = position, hook = direction, club = vibration/velocity, Mamiya 2018; CS load encoding, Dallmann/Tuthill), a sensory delay inside the measured range, through the real connectome to the MNs, with the bypass drive held constant. Pass (Director): the fly holds a stance for 3 s and returns after a small push, with the contact sheet viewed. That gets its own pre-registration after the fix 2 result, and it does not touch fly's DN→oscillator→MN switches (S4a/S4b).
- **L0 travels with r (clarification of step 1, the convention of `scripts/build_midhind_muscles.py`, assumption 3).** Moving r from 0.01 mm to half the distal tibia width (0.039-0.054 mm) with L0 fixed at 0.1 mm would make the TiTa force-length curve 4-5× steeper per radian. That is a second change (steepness is the stability variable above) and would confound a capacity pass. So step 1 scales L0 by the same factor as r, keeping strain per radian (r/L0 = 0.1/rad) and the curve's shape as now. Only peak torque changes. Labelled inferred.
- **Per-leg values (derived from `data/derived/leg_segment_geometry_flybody.csv`, the flybody mesh, left/right mean):** tibia mid-third cross-section front 0.00285, mid 0.00201, hind 0.00410 mm²; distal width 0.0870, 0.0781, 0.1068 mm. So r = 0.0435, 0.0391, 0.0534 mm. At 28 mN/mm², F0 = 80, 56, 115 µN, giving 3.5, 2.2, 6.1 µN·mm per muscle against the placeholder's 0.2 (11-31×). Even 9 mN/mm² gives 3.5-10×. So if step 0 confirms the 6.1× need, capacity on paper exceeds it at every tension; the runs test whether that matters for holding. The whole cross-section is used for each direction of the pair, so the bound double-counts the antagonists' shared space: an upper bound by construction.

### fly2 result: S1 fix 2 step 0, the hold-need instrument at 1.32 mm (13 Oct, 23:43); predictions for step 1 written before its runs
`bypass_s1_actuation.py --need-only --k-hold-mult {1,5,25,125}` on the Mac (m10f0, seed 12; `runs/s13/bypass/s1fix2/step0/`). K_HOLD × k, damping × √k (same damping ratio).
- **Only the feet touch at every stiffness** (non-foot floor force 0 throughout the hold). Sag: 0.043 mm at ×1, 0.012 at ×5, 0.0035 at ×25, 0.0015 at ×125. So the pre-registered criterion (sag < 0.01 mm, feet only) is first met at ×25. The original 6.1× (×1) was not clean: it sagged 0.043 mm.
- **The need does not converge.** Pair max 6.1 → 8.0 → 10.0 → 4.9×; coxa max 0.96 → 1.15 → 1.40 → 1.16. As the instrument stiffens, the load moves onto fewer legs. At ×125 only a diagonal pair carries the TiTa load (lh 4.9×, rf 4.8×; the other four ≤ 0.02). This is static indeterminacy: six feet on the floor and one weight, so the split between legs depends on the compliances, not on the body alone. "The need" is an instrument-dependent distribution, not a number.
- **What survives:** at every valid stiffness (×25, ×125), at least one tibia-tarsus muscle needs 4.8-10× the placeholder's capacity, and the femur-tibia flexors need up to 1.1-2.8× theirs (F0 from FlyMimic, F-BODY-1). The conclusion "the TiTa placeholder is far below the hold" survives; the value 6.1 does not.
- **For step 1 the need pattern uses ×25**, the first stiffness meeting the pre-registered criterion. ×125 is reported only.

**Predictions for step 1 (written before any step 1 run):**
1. **Need pattern:** at ×25 the femur-tibia flexors need up to 2.84× capacity, and fix 2 does not touch them. So every need run at k ≥ 0.35 clips them at 1, and no need run can be a plausible pass ("k ≤ 1 with nothing clipped"). Need runs are reported but can only fail.
2. **Support pattern:** these are the only runs that can pass. At the placeholder, support 0.3 lifted and then reared the fly 45° nose-up (F-BYPASS-1). With TiTa 11-31× stronger, support's TiTa contribution grows by the same factor. Prediction: **FAIL at every tension**. Low support (0.1-0.2) sinks more slowly than before, and higher support rears or rolls, because constant activation with a flat force-length curve has no restoring force. This predicts the falsifier branch: "capacity is ruled out; stability is the break." If any support run passes, capacity was the break.

### fly2 result: S1 fix 2 step 1 (13 Oct, 23:47)
FAIL 0 of 24, as predicted (F-STAND-6; sheet `docs/media/s13_bypass_s1fix2.png`, viewed). The falsifier branch is hit: capacity is ruled out as the break, and stability is the break. At 9 mN/mm², support 0.3 stands for 3 s with no trunk contact but sinks (0.16 mm over the last 2 s; pitch 10.6°), and support 0.5 rises 0.29 mm. At 28-37, support 0.5 flips the fly over. Need runs are capacity-independent by construction and clip the femur-tibia flexors. `muscle:leg|tita_specific_tension` stays neutral and is not adopted. Next: the minimal measured proprioceptive loop (Director's interpretation, addendum 23:40), with its own pre-registration. It needs a CPU path that steps the VNC with the brain off and adds the constant bypass activation to the MN-driven activation; fly's S4a/S4b switches stay untouched.

### fly2 pre-registration: proprioceptive stance loop, step R (reach gate; 13 Oct, 23:58)
Director brief (after /clear): build the minimal proprioceptive stance loop (`docs/research/s13_proprio_loop.md`). Check F-REFLEX-1 first; if the loop can't reach the MNs, that is the localisation result and fly2 stops there. Step R is that check. It runs in the loop's own configuration and is written before any run (a 400 ms smoke of the probe was run to test the code, not scored).
- **Probe:** `scripts/probes/proprio_reach.py`. m10f0, seed 12. Brain off: every cell outside the VNC set loses its output, as in S2. Senses: leg proprioceptors only (chordotonal, hair-plate and CS rows of `sensory.Afferents`). Bristle rows, eyes, chemosenses and organs are not driven. Thorax tethered 1 mm above the standing placement, legs in air. No afferent delay (a delay cannot change whether a path exists).
- **Stimuli:**
  - **clamp:** the femur-tibia joint is held from 200 ms, then moved 0.4 rad at 2 Hz from 300 to 1300 ms (F-REFLEX-1's protocol). Legs lm (the best-assigned leg: 25 claw, 12 hook) and lf (4 claw, 4 hook).
  - **load:** on lm, the 2 CS afferents get full signal (1) over 300-1300 ms. Leg free. In m10f0 each leg has only 2-3 CS rows (assignment count, checked now).
  - **Control:** `--zero-afferents` (no afferent drive at all) for clamp lm and clamp lf.
- **Gain arms (mV mode):** 8 mV per unit (`afferent:all|rate_gain`, the profile default, guessed) and 40 mV (5×, a sweep arm). The afferent rates reached are reported. Any arm whose FeCO or CS rates exceed the measured maximum found by the literature search (running now) is labelled supraphysiological, and a reach seen only there counts as no reach.
- **Readout:** per-MN rate of every motor pool on the leg (Hill pairs by joint and direction, coxa by MN type), binned hold / flexing / extending (clamp) or before / during (load). Also the afferent rates by subtype and the F-REFLEX-1 inhibitor rates.
- **Reach criterion (a pool "is reached"):**
  - **clamp:** max/min of its rate across flexing and extending ≥ 1.25, with a difference ≥ 2 Hz per MN, and under 1.08 in the zero-afferent control.
  - **load:** during/before ≥ 1.25 or ≤ 0.8, with a difference ≥ 2 Hz per MN.
  - The loop "reaches the MNs" if, on lm at a physiological arm, a tibia pool is reached by clamp or any lm pool is reached by load.
- **Prediction:** NO REACH at 8 mV on lm. F-REFLEX-1's block is in the VNC (tonic inhibitors IN13A/IN08A/IN19A/IN21A), and turning the brain off removes DNg105 but not those. At 40 mV, prediction uncertain.
- **If no reach at any physiological arm:** write the localisation finding (where the signal stops, with the inhibitor rates) and stop. No gain is tuned to force a reach. **If reached:** go on to step L (the stance loop), pre-registered separately before its runs.

### fly2 result: stance loop step R (14 Oct, 00:07)
**NO REACH, 0 of 8** (F-REFLEX-2; `docs/media/s13_fly2_reach.png`, viewed). The prediction for 8 mV was right, but its reason was wrong: F-REFLEX-1's tonic inhibitors are silent with the brain off. The signal stops at the first hop at 8 mV. At 40 mV (hook 76-78 Hz, the top of the only Drosophila chordotonal range) the path it opens is net inhibitory onto the tibia extensors. The CS load channel is saturated (0.94 in air), so the load arm tests nothing. **Per the brief, the stance loop stops here.** No HillLegDrive bias or delay was built, nothing was tuned, and no switch was added. The localisation readout (first-order and premotor rates, MN gap to threshold, CS signal) was added to the probe after the 8 scored runs, as extra outputs, and run once more on lm at 8 and 40 mV. Next test: rerun step R on fly's adopted S4a/S4b arm. Delay for a future loop: about 3 ms, inferred (Tuthill & Wilson 2016, bristle afferent → VNC EPSP); no Drosophila FeCO/CS latency exists.

### Results S4a, 13 October, 23:57 (F-BYPASS-6)
Fail on every arm: 0 transfer-pass pools in 9 runs; no antagonist pair; viewed. Nothing adopted; R and G stay neutral switches. The recruitment order was not spent. Battery fix: R's key gained its owner row `n2p_between_type_size_exponent_leg_mn` in `data/model/parameters.csv` (test_model_data had failed on the missing owner). The first battery stopped at that failure (`-x`), so the full rerun is pending at commit time.
Director decision (as Ben), held from 13 Oct: S4b fits the premotor→MN scale only, against the force-probe MN firing read off Azevedo 2020's figures plus the 7-16 Hz rhythm band. It is labelled fitted, with the recruitment order held out. Burstiness stays unfitted until a measured range exists. Seki 2010 and Choi 2004 go on Ben's paywalled-paper list.

### Pre-registration S4b: one fitted premotor→leg-MN synaptic scale (14 October, 00:12, before any S4b run)
DIAGNOSTIC, forced drive; implements the Director's held decision (as Ben, recorded under Results S4a). Burstiness stays unfitted.
- **Quantity.** One new neutral switch, `cell_type:leg_motor|synaptic_input_scale` (default 1; owner row `n5p_leg_mn_synaptic_input_scale`; percell.py). It multiplies the input gain of all 381 leg MNs (vnc_motor, subclass fl/ml/hl), so every synapse onto them scales together. It is shared by class: one number, no per-route or per-cell knob. Bounds 1-25, guessed. No premotor→leg-MN unitary PSP has been recorded. The upper edge is the 14-25× deficit in F-BYPASS-5, a model-to-model comparison, not a biological bound. Any value chosen is labelled **fitted**, never measured. The implied per-synapse peak PSP at s* is reported against measured fly central unitary PSPs as a plausibility check, not a target.
- **Fit targets.**
  - Measured, read off the plot: Azevedo 2020 eLife, Fig 5—figure supplement 1A. Average spike rate over all trials with spontaneous leg movements: fast ≈ 1, intermediate ≈ 10, slow ≈ 60 Hz. Reading error about ±3 Hz. No numbers are in the text (`docs/research/s13_s4b_azevedo_forceprobe.md`, Sonnet; figure read by me).
  - The 7-16 Hz rhythm band.
  - Constraint, measured (Fig 3D): intermediate and fast are silent at rest.
- **Validity.** Those rates come from a fly with the femur fixed, moving spontaneously against a force probe, averaged over whole trials. They are not DNg100-driven walking. So they are an order-of-magnitude envelope, hence the ×3 acceptance bar.
- **Run.** GPU batch, `scripts/probes/s4b_scale_sweep.py sweep`, on backhouse. It reproduces the bypass harness without the body (m10f0, seed 12, brain off, senses off, DNg100 300-1300 ms of 1500 ms; the body does not feed back in that harness).
  - Grid: s ∈ {1, 1.5, 2, 3, 4, 6, 8, 12, 16, 25} × drive {15, 25, 40} mV (30 members).
  - Tibia-flexor classes follow `motor_forces.py`: volume rank 1 fast, 2-4 intermediate, the rest slow.
- **GPU checks (before any score).**
  - CPU switch at s = 4 against a GPU member with leg input gain ×4, over 300 ms (100 ms rest, 200 ms at 25 mV). The input gains must be bit-identical, and the spike totals and leg-MN spikes must agree within 1%. Otherwise the sweep is not used.
  - The s = 1 / 25 mV member against the CPU harness baseline `runs/s13/bypass/s2/s2_DNg100_25mv_traces.npz` (pool_rate), reported.
- **Fit (25 mV members only; `s4b_score.py fit`).**
  - E_rate = mean over 6 legs × 3 classes of [ln((r+1)/(r*+1))]², where r is the class's mean per-MN rate in 500-1300 ms.
  - Admissible s:
    - intermediate and fast mean pre-drive rate (0-300 ms) ≤ 1 Hz;
    - **and** S4a's pass at 25 mV with the band widened to 7-16 Hz: two antagonist pools of one leg both transfer-pass, with r ≤ −0.3 at zero lag or a lagged peak (10-30 ms) r ≥ 0.5, and the summed leg-MN rate post-drive ≤ 1.5× pre-drive.
  - s* = the admissible s with the lowest E_rate.
  - Accepted if every class's leg-mean rate is within ×3 of target, i.e. |ln((r+1)/(r*+1))| ≤ ln 3.
  - Nothing at 15 or 40 mV is looked at before s* is written down.
- **Held out (spent once, at s* only; `s4b_score.py heldout`).**
  - Recruitment order, Azevedo 2020 (measured, never fitted): slow before intermediate before fast.
  - Scored as the recruited fraction (MNs with ≥ 2 spikes in 300-1300 ms) per class at 15/25/40 mV.
  - Pass iff slow ≥ intermediate ≥ fast at every drive, with intermediate recruited at some drive and the order not degenerate.
  - The 25 mV point is partly constrained by the fit; 15 and 40 mV are not.
  - Reported, not scored: the fraction of intermediate spikes preceded within 25 ms by a same-leg slow spike (Fig 5C: 2972/3082), against chance from the slow pool's rate. With 7-12 slow MNs per leg, chance is near 1, so it cannot discriminate.
- **Viewing.** Rasters at s* (all three drives). Then one CPU harness run with the body at s*, 25 mV (frames; confirms GPU = harness).
- **Falsifier.**
  - No s in 1-25 is admissible: the scale alone cannot carry the core's rhythm to the MNs. The break is the core's burst output, which is unfitted and has no measured range. That goes to Ben's list (E1/E2 burst recording; unitary premotor→MN PSP).
  - Admissible but rates off by more than ×3: the fit is rejected.
  - Held-out fail: s* is not adopted.
- **No adoption from S4b alone.** A pass goes to the S4a follow-ons: E1/E2 silencing, DNb08 drive, and gate and rest with the brain on.


### fly2 pre-registration: PSI→DLMn at the measured 4.71 mV, GF escape rerun (14 Oct, 00:21, before any run)
Ben via the Director (13 Oct 22:53, item 2; brief 14 Oct): PSI→DLMn takes Fayyazuddin 2006's value as MEASURED, a scan-gap fill. Source checked against the primary text (PMC1382016) by a Sonnet subagent and by fly2: "The mean amplitude of the synaptic potential underlying the spike measured at the soma using these three methods was 4.71 ± 0.35 mV (n = 10)" (SEM; whole-cell, MN5 soma held at −74 mV, GF at 1 Hz; methods: spike failure at high frequency, amplitude to the inflection point, forced MN5 refractoriness). MN5 supplies DLMa and b (same paper). Scan-gap reason: part of the PSI contact "follow[s] the axons out into the posterior dorsal motor nerve", outside the reconstructed volume, and the synapse bypasses the dendrites, so synapse count × the shared scale is not expected to carry it.
Built: neutral switch `connectome:identified|unitary_psp_from_recordings` (table `data/params/unitary_psp.csv`; CPU only, the GPU refuses it). A row sets its edges to the weight whose passive PSP peak for one presynaptic spike equals the value. Rows: PSI→DLMn a, b 4.71 mV measured; PSI→DLMn c-f 4.71 mV inferred (same cell and contact, no MN1-4 recording). `tests/test_unitary_psp.py` 4 passed.
Runs (Mac, isolated CNS, seed 0, profile m10f + `nt_from_physiology=1` + `unitary_psp_from_recordings=1`): (1) `gf_psi_dlm_path.py`, the DLMn peak after one GF spike; mechanism gate: DLMn a, b peak within 4.71 ± 0.5 mV of its pre-spike value (else report why: intrinsic channels, other inputs). (2) `gf_latency.py --trials 20`, gaps off and on.
Pass (the Director's): gaps on, DLMn follows ≥ 90% of GF spikes with the median muscle latency inside 1.36-1.849 ms. The DLM latency is spent (F-GJ-3), so this is a consistency check, not a validation.
Prediction: FAIL. DLMn a, b peaks about 4.7 mV above −52, i.e. −47.3 against a −45 threshold (shared guessed rest and threshold), so follow ≤ 10% (noise only). If it did fire, the latency would sit above the band: GF→PSI 0.3 ms + PSI delay row 0.8 ms + rise at tau_m 20 ms + DLMn delay row 0.8 ms ≥ 2.5 ms. Falsifier of the prediction: DLMn follows ≥ 90%. A fail is reported with its measured reason; no rest, threshold, tau_m or gain is tuned to make it fire. Nothing adopted either way.

### fly2 result: PSI→DLMn at the measured 4.71 mV, GF escape rerun (14 Oct, 00:25)
FAIL, as pre-registered 00:21 (F-GJ-5). Mechanism gate passed: one GF spike lifts every DLMn by 4.78 mV, against 0.6 mV at the shared scale. DLMn follows 0/20 with gaps on (TTM 1.099 ms and PSI 20/20, unchanged); the peak is −47.2 mV, 2.2 mV below threshold, about 10 ms after the GF spike. Reason: a soma-measured EPSP of an axonal synapse in a point neuron with the shared 7 mV gap and tau_m 20 ms. Next blanks, none tuned: DLMn tau_m 4.4 ms (MN5 Rin × Cm, same paper, derived), MN5 rest and threshold (not in this paper), N30. The switch stays neutral; nothing adopted. Figure `docs/media/s14_fly2_psi_dlm.png`, viewed.

### fly2 pre-registration: flyvis type-pair strengths, T4/T5 direction test (14 Oct, 00:41, before any run)
Arm (Ben's item, DECISIONS 13 Oct 22:53): `cell_type:all|optic_lobe_flyvis_pair_strength=1`, neutral 0, CPU only. 517 flyvis type pairs (`data/params/flyvis_pair_strength.csv`, labelled fitted, task-trained, basis inferred) set the 627,657 edges from graded cells so the steady-state voltage gain is alpha × synapse count (`Network._flyvis_pair_weights`, tests in `tests/test_flyvis_pairs.py`). Our sign is kept. 25 pairs disagree with flyvis's sign (C2/C3→L1/L2, R8→Mi1/Mi4/Mi9/Mi15, Mi10→T4a-d and others), listed in `docs/media/s14_fly2_flyvis_pairs.json`.
Size check (Ben's condition; F-VISION-13): 28 pairs have no male-cns edges; 25 are flagged because one presynaptic type across its release range would move the most-driven post cell more than 60 mV (guessed ceiling); not clipped. Only one class has a measured comparison: R1-R6→L1 −0.78 and →L2 −0.41 mV/mV, both above the Zheng 2006 lower bound of 0.4 (derived). Every other class has no measured range found and is unchecked.
**Deviation from Ben's condition, stated before the run:** CT1 is not compartmentalised. Male-cns has 2 CT1 cells and no column assignment in our data, so flyvis's CT1(M10)/CT1(Lo1) rows are not read and CT1 keeps the shared scale as in the F-VISION-12 base. This run therefore tests the pair strengths without the CT1 part of the arm. A pass would not clear the frontier: the CT1 condition and the held-out recordings check are still open.
Test: flyapp `app/tools/t4t5_ds.py` at app commit 80bc01c (unchanged since F-VISION-12), both stimulus sets, m9c + the 7 v0r switches + `optic_lobe_flyvis=1` + the pair switch + `candidates_s13_v0r.csv`, **seed 1** (seed 0 was spent on v0r + flyvis), model from the fly2 commit that carries this entry, backhouse at --parallel 4.
Pass (the Director's): all 8 T4/T5 subtypes direction selective with the fly's preferred direction under the tool's statistics, in the medulla set (the circuit the pair strengths act on). The photoreceptor set is secondary: it also needs the lamina, which F-VISION-8/9/12 found passes almost nothing.
Prediction: FAIL in the medulla set, with some subtypes selective but fewer than 8, and |DSI| above F-VISION-12's ≤ 0.02. Reasons: in flyvis itself DS needs the pair strengths (median DSI 0.40, against 0.02 with product strengths), but here the synapses are conductances with tonic release (shunting), CT1 is a point cell that saturated in the flash run, and the T4/T5 offsets come from the connectome rather than flyvis's hex lattice. Photoreceptor set: FAIL (lamina gap).
Falsifier: 8 of 8 selective in the medulla set. Spent by this call: the flyapp T4/T5 test at seed 1 on this arm. Nothing is adopted either way. T4/T5 direction selectivity was not a flyvis training target, but flyvis networks show it, so this is not the held-out recordings check Ben asked for before frontier use.

### fly2 pre-registration: flyvis pair strengths with CT1 per-column compartments, T4/T5 direction test, seed 2 (14 Oct, 01:05, written before the seed-1 result is known)
Arm: the seed-1 arm plus `cell_type:CT1|compartments_by_column=1` (F-VISION-14). CT1 becomes 3,398 independent per-column graded compartments: 1,669 M10 and 1,729 Lo1, split by male-cns column ROIs. The flyvis CT1(M10)/CT1(Lo1) rows set their 81k edges. This is the arm as Ben specified it (CT1 compartmentalised as in flyvis). Size check: none of the 24 CT1 pairs with edges is flagged, and the largest full-range response is 8.9 mV. No measured CT1 range was found, so CT1 is unchecked. C3↔CT1 has no edges at 5 synapses.
Test: as seed 1. flyapp `app/tools/t4t5_ds.py` at app commit 80bc01c, both stimulus sets, m9c + the 7 v0r switches + `optic_lobe_flyvis=1` + the pair switch + the CT1 switch + `candidates_s13_v0r.csv`, **seed 2**. The model comes from the fly2 commit that carries this entry, in a separate backhouse snapshot (`~/fly2_s2`) so the running seed-1 job is untouched. --parallel 3, queued to start when seed 1 finishes.
Pass (the Director's): all 8 T4/T5 subtypes direction selective with the fly's preferred direction, under the tool's statistics, in the medulla set. The photoreceptor set is secondary (lamina gap).
Prediction: FAIL in the medulla set, with the number of selective subtypes within ±2 of seed 1. Reason: CT1 feedback is local inhibition onto T4/T5 at small gains (−0.1 to −0.6 mV/mV per post cell). The shunting and offset reasons given for seed 1 still apply. Photoreceptor set: FAIL.
Falsifier: 8 of 8 selective in the medulla set. Spent by this call: the flyapp T4/T5 test at seed 2 on this arm. A different seed means the seed-1 and seed-2 results are not a paired comparison of CT1; they are two draws, read as such. Nothing is adopted either way. This is not the held-out recordings check (the Behnia 2014 temporal measures, still sealed), which Ben requires before frontier use.
Amendment (14 Oct 01:07, before the seed-2 run starts; it is still queued behind seed 1): seed 2 runs the **medulla set only** (`--stimulus medulla`, 9 runs instead of 17). Reason: under the current backhouse load each 2-s protocol takes about 47 min at --parallel 3, so both sets would take about 4.7 h. The pass and the falsifier are read in the medulla set only, and the photoreceptor set was secondary and predicted FAIL on the lamina gap. Pass, prediction and falsifier are unchanged; the photoreceptor-set prediction is withdrawn for seed 2.

### Results S4b fit, 14 October, 00:21 (written before any held-out or 15/40 mV look; F-BYPASS-7 pending the body run and PSP check)
**s\* = none. FALSIFIED:** no scale in 1-25 is admissible. The verdict is from `s4b_score.py fit` (`runs/s13/bypass/s4b/fit.json`), 25 mV members only.
- **Checks passed first.**
  - `gpu_check.json`: input gains bit-identical; 957 = 957 spikes and 605 = 605 leg-MN spikes; exact over 3000 steps.
  - Baseline: the s=1 / 25 mV GPU member's pool_rate equals the CPU harness `s2_DNg100_25mv_traces.npz` exactly (2158 = 2158 spikes, L1 difference 0). The body does not feed back in this harness.
- **Silent at rest:** holds at every s (intermediate and fast are 0 Hz pre-drive).
- **Rates** (class mean in 500-1300 ms; target slow 60 / intermediate 10 / fast 1 Hz):
  - Slow sits at 21-23 Hz at every s. That is the tonic, drive-independent tibia-flexor line (23 Hz pre-drive too).
  - Intermediate rises from 0 Hz at s ≤ 2 to 5.8 Hz at s 25. Fast rises from 0 Hz to 4.4 Hz.
  - Within ×3 of target only at s 16 and 25; lowest E_rate 1.50 at s 25.
- **Rhythm fails at every s:**
  - Transfer-pass pools: 0 at s ≤ 2, 4-6 at s 3-4, 13-14 at s 12-25.
  - **No antagonist pair at any s.** The candidate pairs fire together. lh sternal anterior vs posterior rotator: r0 from +0.03 to +0.42 (lagged peak ≤ 0.48). lf pleural remotor vs promotor: r0 from +0.37 to +0.82.
  - Activity stops at drive-off (post/pre 0.94-1.13). There is no runaway at any s.
- **Viewed:** `docs/media/s13_bypass_s4b_rasters_25mv.png` (s 1, 4, 12, 25). A ~12 Hz rhythm reaches lf, rf and lh pools from s ≥ 4 and is clear at s 12-25. It is one co-active burst per cycle; nothing alternates with it.
- **Reading (falsifier as pre-registered):** the scale alone cannot carry the core's rhythm to the MNs as alternation. Raising MN gain only makes the existing in-phase volley visible in more pools. The stance antagonists have no rhythmic inhibition (I1 silent, F-BYPASS-3/4). The break is the core's burst output and I1, which are unfitted and have no measured range. Ben's list (E1/E2 burst recording; unitary premotor→MN PSP) stands.
- **Not spent:** the recruitment order stays held out. The pre-registration spends it at s\* only, and there is no s\*. 15 and 40 mV members are not looked at.
- **Nothing adopted.** `synaptic_input_scale` stays neutral 1.
- **Pending (diagnostic only):**
  - one CPU body run at s 25, the best-rate arm, to view frames;
  - the Director's PSP check: the model's unitary premotor→leg-MN PSP at s 1/16/25 (`scripts/probes/s4b_unitary_psp.py`) against measured insect unitary PSPs.

### Results S4b, diagnostics after the fit, 14 October, 00:33 (F-BYPASS-7; nothing adopted)
- **Body run at s 25, 25 mV** (best-rate arm, not s\*; `runs/s13/bypass/s4b/body/`, backhouse, 228 s). Its pool_rate equals the GPU s25/25 mV member exactly (5375 = 5375 spikes, L1 0), so GPU = harness at a non-unity scale too.
  - The S2 harness scorer says "passes". That comes only from left-right mirror pools (r −0.32 to −0.55). Every within-leg antagonist r is positive or missing (+0.23 to +0.58), so this is not the pre-registered S4b criterion.
  - **Viewed** (`docs/media/s13_bypass_s4b_frames.png`, s=1 top, s=25 bottom): the thorax lies on the floor in both rows (S1's body block). At s=25 the legs splay sideways and shift between frames (joint SD up to 17°), with no stance and no stepping cycle. Wings open as at s=1.
- **PSP plausibility check (Director's held note).** `scripts/probes/s4b_unitary_psp.py`; `runs/s13/bypass/s4b/psp/unitary_psp.json`; 24 cholinergic premotor cells spread over connection size, 126 pairs.
  - Method: one forced premotor spike, minus an unkicked copy.
  - The peak comes at 10.5 ms (monosynaptic) and scales linearly with s (measured/s1 ratio 16.0 and 24.9).
  - Model PSP at a leg MN (derived from the model):

    | s | mV per synapse | median connection (12 syn) | q90 connection (54 syn) | sampled pairs where one premotor spike fires the MN |
    |---|---|---|---|---|
    | 1 | 0.021 (q10-q90 0.009-0.035) | 0.25 mV | 1.1 mV | 0/126 |
    | 16 | 0.34 | 4.1 mV | 18 mV | 52/126 (41%) |
    | 25 | 0.53 | 6.4 mV | 29 mV | 68/126 (54%) |

  - Measured comparison (`docs/research/s13_s4b_unitary_psp.md`; Sonnet, unchecked row by row; no adult premotor→leg-MN unitary PSP exists):
    - Drosophila central unitary PSPs are 0.4-10 mV per spike, mostly 1-7. Examples: ORN→PN ~5; PN→LHN 0.4-6.6 (Liu et al. 2022); PN→KC 1.4 ± 0.8 (Turner 2008); larval premotor A31k→aCC −2.8 ± 0.5 (Giachello 2022).
    - Locust nonspiking IN→leg MN reaches up to ~5 mV; locust FETi→flexor at 12-24 mV is a MN→MN outlier.
    - mV per synapse is ~0.1-0.3 (derived) in small, high-Rin central cells (KC Rin >10 GΩ). Leg MNs are 150-700 MΩ (Azevedo 2020), so they are expected at or below that band (inferred).
  - **Verdict.** s 1 is consistent: low per synapse, as a leaky MN should be, and strong connections reach 1-5 mV. **s 16-25, the only scales with rates within ×3, are not consistent:**
    - per synapse 0.34-0.53 mV, above the small-cell band;
    - strong connections at 18-29 mV, beyond every measured interneuron→MN value;
    - a single premotor spike fires about half the sampled MNs.
  - So a rate-matching scale would be compensating for something else. In this harness the premotor layer is nearly silent: 0.13 Hz mean over 5314 cells during the drive, with the core giving one spike per cycle (F-BYPASS-4/5). That is the missing burst output.
  - Proposed evidence bound, if the scale is ever refitted: s ≤ ~14 (0.3 mV per synapse). This is inferred, from the unchecked table, and replaces the guessed 25. Not adopted.
- **Held-out recruitment order: NOT spent.** There is no s\*, and the pre-registration spends it at s\* only. 15 and 40 mV members were not looked at.

### Pre-registration X1: cross-connectome control of the E2→I1 deficit (14 October, 00:39, before any count extraction beyond F-BYPASS-3 or any run)
DIAGNOSTIC, forced drive; Director brief (14 Oct, after S4b). No fitting, no new switch, nothing adopted. Question: is I1's silence (F-BYPASS-3/4) a property of this animal's counts, and if so is the deficit reconstruction or individual variation?
- **Simulation (our neuron model, everything identical except counts).** A wrapper replaces `connectome.load_tables` edges before `connectome.build`, so every mechanism, threshold, sign (from the male-CNS cell), the `min_synapses` 5 cut and m10f0 apply unchanged. Counts come from MANC (Pugliese's full-MANC matrix `W_20260522_allSynapses`, checked first against their T1L minicircuit, E2→I1 = 71).
  - **M0:** male CNS as is (re-run in the same batch).
  - **Xc (core swap):** cells of types DNg100, IN17A001 (E1), INXXX466 (E2), IN16B036 (I1), IN19A007, IN19A004, IN19A002 with a one-to-one `mancBodyid`; every edge between two of them takes the MANC count of the matched pair (edges absent in MANC are removed, MANC-only edges added).
  - **Xv (VNC swap):** the same rule for every VNC-set cell (superclass vnc_*, descending, ascending, as in the S2 harness) with a one-to-one `mancBodyid`. Edges with an unmatched endpoint keep male-CNS counts.
  - Each arm × DNg100 15/25/40 mV, seed 12, brain and senses off: `bypass_s3_chain.py` (core cells, 900 ms) and `bypass_s2_descending.py` (MN pools, body tethered, 1500 ms). Backhouse, done-files.
- **Readouts (scored per arm, any drive).**
  - *I1 recruited:* T1L I1 fires on ≥ 50% of core cycles during drive (rate ≥ 0.5 × E1 cycle frequency). All six neuromeres reported.
  - *Alternation:* S4b's admissibility criterion unchanged (two antagonist pools of one leg both transfer-pass, band 7-16 Hz; r ≤ −0.3 at zero lag or lagged peak 10-30 ms ≥ 0.5; post-drive leg-MN rate ≤ 1.5× pre-drive), then viewed on rasters.
- **Interpretation, fixed now.**
  - Xc or Xv alternates and M0 doesn't → the male-CNS counts are the break; the audit below says which kind.
  - I1 recruited under a swap but no alternation → the E2→I1 deficit explains I1's silence but not the failed transfer.
  - Neither → the male-CNS counts are not the break; our spiking model can't run this circuit on either animal's wiring (the threshold/efficacy/burst question, Ben's list).
  - **Prediction (mine, before running):** the last. Pugliese's own LIF on MANC gets I1 to one spike per cycle and 1 of 25 MNs bursting at 0.275 mV per synapse (F-BYPASS-3); ours is 0.157 mV. Expect I1 at most ~1 spike per cycle at 40 mV under Xc, and no antagonist pair in any arm.
- **Count audit (descriptive; no simulation).** Per leg neuromere and side, the core edges in male CNS, MANC, BANC and FANC (Pugliese's T1 extracts; BANC/FANC matched through their MANC type labels).
  - Normalisation: the median male-CNS/MANC ratio over matched VNC edges with ≥ 10 MANC synapses (dataset-wide detection and completeness difference).
  - *Outlier call:* the normalised E2→I1 log ratio lies outside the 5-95% band of matched edges of similar MANC size (30-150 synapses).
  - *Reconstruction indicators:* I1's and E2's status labels; I1's total postsynapses and the fraction of its input from Traced bodies, against MANC's I1; whether the deficit is specific to E2→I1 or shared by all of I1's inputs (whole-cell under-reconstruction).
  - *Individual-variation indicators:* the left-right and T1/T2/T3 spread of E2→I1 inside each animal, and where BANC/FANC fall. If the other animals sit with MANC and the male CNS alone is low, the deficit is male-CNS-specific (reconstruction or this individual; counts alone can't separate those two, and the report will say so). If the animals spread across the range, it is individual variation, and under the per-value bar both counts are admissible.

### X1 count audit result and simulation launch (14 October, 00:45; F-XCONN-1)
- Count audit as pre-registered: T1L E2→I1 is **not an outlier** on the pre-registered normaliser (0.538, matched edges ≥ 10 MANC synapses; normalised log ratio ≈ 0). On the secondary normaliser (edges in both, 0.875), it is low. The deficit is male-CNS T1-wide (per-cell matched-input ratio T1 0.58, T2 0.69, T3 0.82) and whole-cell for I1 (all of I1's T1 inputs 0.34-0.38× MANC's). BANC sits with MANC. Reading: male-CNS-specific, more likely reconstruction than individual variation (inferred). Detail in F-XCONN-1.
- Simulation launched on backhouse at 00:43 exactly as pre-registered (`runs/s13/xconn/run.sh`, 18 runs, done-files). Nothing scored yet.
- Wrapper fix at 00:46, before any swapped run started (the M0 chain batch was still running): the swap set is now restricted to cells whose MANC body is in the MANC table. Before the fix, 74 matched cells outside it would have lost their within-set edges under Xv. Checked on the Mac: Xc swaps 36 cells (182 male-CNS edges, 17,774 synapses → 199 MANC edges, 20,652), and T1L E2→I1 becomes 71, I1→E2 172, E1→E2 539.

### Results X1 simulation (14 October, 02:21; F-XCONN-2; nothing adopted)
Scored as pre-registered, before viewing: I1 not recruited in any arm or drive (T1L Vmax ≤ −47.5 mV against −45). S4b alternation pass fails in all 9 runs (0 transfer-pass pools, no antagonist pair). Viewed `docs/media/s13_xconn_rasters_{25,40}mv.png`: arms indistinguishable at the MN layer. Interpretation branch "neither": the male-CNS counts are not the break. F-XCONN-1's T1 undercount stands as a dataset finding; no change to the model's counts (MANC substitution was a control, not a candidate). Rule 16 noted (Director, 14 Oct): from the next backhouse launch, cap OMP/MKL/OPENBLAS/JAX threads at 4 per job and check `uptime` first; X1 was launched before the rule.

### fly2 pre-registration T1F: inferred T1 synapse fill from MANC and BANC (20 Oct, 22:02, rule written before any code, count or run)
Brief: Director 20 Oct (Ben's goal: fly_brain.zip, a complete functional emulation; inferring missing data is core). Development mode. Motivation: F-XCONN-1 (male-CNS T1 per-cell matched input 0.58 of MANC, T2 0.69, T3 0.82; BANC sits with MANC; reading: reconstruction undercount, inferred).
- **Unit.** x_X(A, B, s) = synapses from all cells of type A (any neuromere, any side) onto the cells of type B with soma in T1 on side s, divided by the number of those B cells, in animal X. Raw counts, before the model's 5-synapse cut.
- **Animals.**
  - Male CNS: our cache; included cells (Traced or typed, as `connectome.build`); type, somaNeuromere, somaSide from the dataset.
  - MANC: Pugliese_cpg_2025's full-MANC matrix (`W_20260522_allSynapses`, sign dropped), aggregated by MANC's own type, somaNeuromere and somaSide labels (not by body matching).
  - BANC: Pugliese's T1 premotor extract (`W_20260217`, `cell_type`, `side`). It has no neuromere label and holds only premotor-network cells, so it enters a pair only if the extract holds exactly as many B cells on side s as the male CNS has in T1 on side s, and A is in the extract. Its pre side is limited to the extract, so it can only read low, which can only lower the target.
- **Target** t = median over the animals that have a value for the pair, the male CNS included (male CNS + MANC: the mean of the two; with BANC: the median of three).
- **Factor** f = t / x_mcns if x_mcns > 0, x_manc > 0 and t > x_mcns; otherwise 1. Fill only, never below 1, no cap (t never exceeds the largest animal's value).
- **Application.** Every male-CNS edge from a type-A cell onto a T1 type-B cell on side s that the model keeps (≥ 5 synapses) is multiplied by f (weights become non-integer). Edges below the cut stay out even if the filled count would cross it. Untyped cells, non-T1 post cells, signs and every other quantity are unchanged. **No edge is added or removed: no partner is invented.**
- **Label:** inferred (cross-animal). Switch `connectome:T1|fill_from_other_animals` (boolean, neutral 0) reading `data/params/t1_fill.csv`, built by `scripts/connectome/t1_fill_table.py` with the source files pinned by sha256.
- **Validity range:** T1 post cells only; assumes the T1 deficit is reconstruction, not biology (F-XCONN-1 reading); assumes per-post-cell input by type is conserved across animals; no ROI or neuropil split; the fill-only rule raises the T1 total above the median of totals (measured below).
- **Count audit, before and after (no simulation), stated expectations:**
  1. T1 per-cell matched-input ratio male CNS/MANC (F-XCONN-1 metric; T2/T3 untouched as reference): expect 0.58 → about 0.8-0.95.
  2. I1 (IN16B036) T1L/T1R inputs (1,176/836 now; T2/T3 copies 2,110-2,509; MANC 2,489-2,932): expect about 1,700-2,300. E2→I1 T1L/T1R (38/27; MANC 71/60, BANC 50/53): expect about 50-60/40-55.
  3. Pairs filled, edges scaled, synapses added, factor distribution, edges below the cut that would cross it; edge set identical (checked).
  4. Type-name agreement male CNS vs MANC for T1 cells (fraction of T1 post types found in MANC T1 on the same side).
- **Held-out checks** (the rule is fixed above and is not changed after seeing these; fill off rerun on the same code as the baseline; m10f0, seed 12, min_synapses 5):
  - **H1, bypass S2 DNg100**, brain off, 15/25/40 mV (fly's `bypass_s2_descending.py`, X1's s2 settings). Pass = the harness's own `passes` (a rhythmic MN pool, excess > 0.10 at 4-25 Hz, with antagonist or left-right r ≤ −0.3). Also read I1 recruitment (T1L/T1R I1 spikes or Vmax ≥ −45 mV). **Predicted FAIL in all 3, and I1 not recruited**: MANC counts across the whole VNC (X1 Xv) did neither, and this fill is a smaller change confined to T1.
  - **H2, step R reach gate**, 8 runs as `run_proprio_reach.sh` (DECISIONS 13 Oct 23:58 criteria). **Predicted NO REACH 0/8**: F-REFLEX-2's block is first-hop transmission, which counts did not fix in X1 or S4b. Only the lf arms have their MN pools inside the fill.
  - Falsifier for "the male-CNS T1 undercount is a cause of the motor failure": H1 and H2 both unchanged from fill off. If either passes, the fill becomes an adoption candidate (gate, battery, viewed figure), not adopted here.
- Rasters viewed for H1 (fill on vs off), the reach figure for H2.

### fly2 T1F amendment and count audit (20 Oct, 22:08; amendment made from the count audit, before any simulation; H1/H2 unspent)
- **Amendment: unit.** The pre-registered unit (synapses per T1 post cell from type A) failed its own per-value bar on the first audit: where the male CNS has typed far fewer cells of a presynaptic type than MANC (sensory types especially), the whole cross-animal input lands on the few existing edges. Worst case: one SNch05 → IN05B002 edge went from 6 to 1,550 synapses (factor 258), far outside any animal's single-connection range. **New unit: x = synapses per connected cell pair**, i.e. synapses from type A onto T1 type-B cells on side s divided by the number of (A cell, B cell) pairs with ≥ 1 synapse, in each animal. Everything else is as pre-registered (median over animals, fill only, kept edges only, no partner invented, BANC count-match rule). This unit is insensitive to differences in typed cell numbers on either side and to BANC's extract boundary. Its bias: the male CNS loses weak connections to the undercount, which raises its mean per connection, so it under-fills (conservative).
- **Audit result** (`scripts/connectome/t1_fill_audit.py`, `runs/s20/t1fill/audit.json`, figure `docs/media/s20_fly2_t1fill_audit.png`, viewed). Table `data/params/t1_fill.csv.gz`: 121,660 of 475,242 male-CNS T1 type pairs filled (13,643 with BANC); factor median 1.5, 99% 6.5, max 158 (pair level, mostly tiny pairs); on kept edges the largest additions have factors 1.7-7.9.
  - Edge set identical before and after (asserted); weights only rise, and only onto T1 cells.
  - Kept edges (cut 5) onto T1: 73,741 of 216,006 scaled; 3.60M → 4.00M synapses (+11%); synapse-weighted factor median 1.0, 90% 1.36, 99% 2.3.
  - 24,624 raw edges below the cut (74,774 synapses) would cross 5 after the fill; they stay out, as pre-registered.
  - **Per-cell matched-input ratio (F-XCONN-1 metric): T1 0.578 → 0.669**, against T2 0.694 and T3 0.821 (untouched). Expected 0.8-0.95: **missed.** T1 now sits at the male CNS's own T2 level, not at MANC's.
  - Why: the deficit decomposes into absent connections and weaker present ones. MANC synapses on matched pairs absent in the male CNS: T1 24.6%, T2 22.1%, T3 21.8% (the same in every neuromere, so not the T1-specific part). On present pairs the male CNS has 0.70 of MANC in T1, 0.83 in T2, 0.93 in T3; the fill takes T1's to 0.80. With only MANC beside it, the median of two closes half the gap by construction.
  - **I1 (IN16B036) inputs, raw: T1L 1,125 → 1,225, T1R 797 → 938** (expected 1,700-2,300: **missed**; T2/T3 1,603-2,283; MANC 2,489-2,932). I1's missing input is mostly absent connections, which the rule cannot fill. **E2 → I1: T1L 38 → 50, T1R 27 → 53** (expected 50-60 / 40-55: met; MANC 71/60, BANC 50/53).
  - Type agreement: 2,247 of 2,545 male-CNS T1 (type, side) post groups exist in MANC T1 (1,884 with the same cell count); 3,803 of 4,220 typed T1 cells have their type in MANC T1.

### fly2 T1F H1 reading note (20 Oct, 22:15; before any H1 or H2 output exists)
- The S2 harness records MN pools only, not I1. H1's I1 reading ("T1L/T1R I1 spikes or Vmax ≥ −45 mV") is taken the way X1 took it (F-XCONN-2): `bypass_s3_chain.py`, DNg100 at 15/25/40 mV, brain off, its default window (drive 100-900 ms), fill on and off, same snapshot. Six extra network-only runs. The H1 pass criterion is unchanged (S2 `passes`).
- Run note: the first launch (22:11) died at about 22:13 when the WSL distro stopped with no client attached. Relaunched with the keep-alive; no output was read.

### fly2 T1F results (20 Oct, 22:30; F-XCONN-3)
- **H1, bypass S2 DNg100 15/25/40 mV, brain off: FAIL in 3 of 3 with the fill on, as predicted, the same as off.** I1 is not recruited: T1L Vmax −48.2 mV against −45. The fill reached the model (T1L E2→I1 6.88 → 9.06 mV, T1R 4.84 → 9.5 mV). The fill-off chain runs reproduce X1's M0 exactly. Rasters viewed.
- **H2, step R: NO REACH 0 of 8 with the fill on, as predicted.** Fill off is also 0 of 8, with identical MN pool rates. Figure viewed.
- **Falsifier holds:** H1 and H2 are unchanged. At the size a no-invention fill can repair, the male-CNS T1 undercount doesn't cause either motor failure.
- **Decision:** the switch stays neutral and is not adopted. It is kept as a labelled inferred member for fly_brain.zip (`docs/FLY_BRAIN_ZIP.md`).
- **Not done here:** inventing partners from MANC to fill the ~25% of MANC input on connections absent in the male CNS. That would need its own rule and pre-registration, and it doesn't touch the T1-specific part (the absent share is the same in T2 and T3).
- H1 and H2 are spent for this switch. Any future T1 candidate needs a new held-out test or new seeds.

### fly2 T1A pre-registration: add absent T1 connections found in both MANC and BANC (20 Oct, 22:44; Ben via the Director, 20 Oct; before any code)
- **Ben's ruling (Director, 20 Oct):** a T1 connection missing in the male CNS may be added only where the same matched type-to-type connection exists in BOTH MANC and BANC. Use the cross-animal median count, label it inferred (cross-connectome), and keep it behind the fill switch. Never connect pairs that neither animal has.
- **Switch:** `connectome:T1|fill_from_other_animals` becomes a level:
  - 0: off (neutral);
  - 1: T1F as scored (scale kept edges);
  - 2: T1F plus T1A, the added connections.
  Level 1 is unchanged.
- **Which pairs are absent:** a key (presynaptic type A, T1 postsynaptic type B, post side s) where:
  - A has included male-CNS cells;
  - B has male-CNS T1 cells on side s;
  - the male CNS has zero synapses from A onto them (raw counts, any size).
  Present but below the synapse cut is not absent; level 1 already covers that case.
- **Which absent pairs are added:** both MANC (`manc_t1_typepair.parquet`) and BANC (`banc_typepair`, under the count-match rule) have the key with at least one connected pair.
- **Counts:**
  - Synapses per added edge: x_add = median(x_manc, x_banc), the synapses per connected (A, B) cell pair. The male CNS's zero is read as a reconstruction miss, not a value, so it is left out of the median. With two animals, the median is their mean.
  - A partners per B cell: c_add = median(n_conn/n_post in MANC, in BANC), rounded, between 1 and the number of male-CNS A cells.
- **Which A cells (guessed, deterministic):**
  - The candidates are the A cells on side s first, then the other A cells, each in bodyId order.
  - B cells are taken in bodyId order. B cell j takes the c_add candidates starting at j·c_add, wrapping round within the same-side cells, then within the others if c_add is larger.
  - No self-edges.
  - Label: partner identity within the type is guessed; the counts are inferred.
- **The synapse cut applies as to measured edges:** an added edge is kept only if x_add ≥ min_synapses (5). Key pairs below it are in the table, for a cut-1 build, but add nothing to the model.
- **Table:** `data/params/t1_add.csv.gz` from `scripts/connectome/t1_fill_table.py add`, with provenance in `t1_add.json`.
- **Count audit predictions:**
  - T1A adds under 10% to the T1 input.
  - The T1 matched-input ratio goes from 0.669 to between 0.67 and 0.72. BANC is a premotor extract with count-matched groups only, so few keys qualify.
- **Motor checks** (rerun once, as Ben asked):
  - H1: bypass S2 at DNg100 15/25/40 mV, plus the I1 chain readout.
  - H2: step R, 8 arms.
  - Both at level 2, same snapshot method as T1F.
  - These checks were already spent once on T1F (level 1). A pass here is weaker evidence and would need a fresh check before any adoption.
- **Predictions:** H1 FAIL 3 of 3 with I1 not recruited (Vmax < −45 mV); H2 NO REACH 0 of 8.
- **Falsifier:** any H1 pass or any H2 reach would mean the absent connections matter. Either way the switch stays neutral (completeness member, not adopted).

### fly2 T1A results (20 Oct, 22:54; F-XCONN-4)
- **Audit:** +0.8% synapses onto T1 at the model cut; T1 ratio 0.669 → 0.680. Both are inside the predictions.
- **H1:** FAIL 3 of 3; I1 not recruited (Vmax −47.8 mV).
- **H2:** NO REACH 0 of 8; MN rates equal level 1.
- Both predictions were right, so the falsifier did not fire.
- **Decision:** level 2 stays neutral and is not adopted. It is kept as the completeness member of the T1 fill, with the partner identity labelled guessed.
- The S2 and step R checks are now spent twice on T1 fills. A future VNC candidate needs a fresh check.

### fly2 T4/T5 seed 1 and seed 2 results (20 Oct, 23:23; F-VISION-15)
- **Seed 1 (00:41 arm):** medulla set FAIL, 1 of 8. T4a only formally passes (DSI +0.04, peak 0.51 against 0.48 mV); every other subtype sits under the 0.5 mV floor or at DSI 0. Photoreceptor set FAIL, 0 of 8.
- **Seed 2 (01:05/01:07 arm, recovered earlier):** FAIL, 0 of 8.
- **Predictions:** the FAIL predictions were right on both seeds, and seed 2 landed within ±2 of seed 1 (0 vs 1). Seed 1's "|DSI| above 0.02" held only at the maximum (0.04); 6 of 8 subtypes are at ≤ 0.01. The falsifier (8 of 8) did not fire.
- **Decision:** the pair-strength and CT1-compartment switches stay neutral; nothing is adopted. The flyapp T4/T5 test is now spent at seeds 0, 1 and 2, so the next candidate needs seed 3 or a new test. The Behnia 2014 check is still sealed.

### fly2 pre-registration: two-compartment DLMn with the PSI input on the axon (N30, first build), GF escape (20 Oct, 23:30; Ben via the Director, 20 Oct; before any code)
**Why here.** F-GJ-5 shows the point model fails for PSI→DLMn: a 4.71 mV EPSP measured at the soma, from an axonal synapse, cannot cross the 7 mV gap. The recording paper says where the spike starts: "the action potential generated at the distal PSI-DLMmn synapse on the axon appeared small and broad in somatic recordings ... suggesting that the peripherally generated action potential fails to propagate antidromically into the dendrite" (Fayyazuddin et al. 2006 PLoS Biol 4:e63, measured, qualitative). PSI "makes multiple synaptic contacts that span 50 μm and follow the axons out into the posterior dorsal motor nerve" (same paper).

**Build** (CPU only; the GPU refuses it; switch `cell_type:all|two_compartments_where_point_fails`, neutral 0; owner N30, which goes from absent to partial):
- Table `data/params/two_compartment.csv` lists the cells (DLMn a, b = MN5; DLMn c-f, inferred, same contact), the inputs that land on the axon (PSI), the class whose shared values apply, and the finding.
- **Soma + dendrite compartment:** the existing cell, unchanged. It keeps every other input, its tau_m, rest, noise, channels and gap junctions.
- **Axon compartment:** the same tau_m, rest, threshold, reset and refractory as the cell (the shared guessed values, as now). It receives the listed inputs, and **the cell's spikes start only here**.
- **Coupling:** both ways, from start-of-step voltages. Soma drive += κs(Va − Vs). The axon relaxes toward (Vrest + Ia + κa·Vs)/(1 + κa) by exponential Euler.
- Uniform membrane and two class values: q (the axon's share of the membrane) and ρ (coupling conductance × whole-cell input resistance). κs = ρ/(1 − q) and κa = ρ/q.
- **The PSI→DLMn weight is recalibrated so the soma peak equals 4.71 mV** with the input on the axon. The measured value stays matched where it was measured.
- Tests: neutral identity; only the listed edges move; the soma PSP equals the table value; the GPU refuses; conductance synapses are refused.

**Values** (class `MN`, shared by every listed motor neuron; derived from guessed geometry, labelled so):
- **q = 0.07.** Derivation: a 50 µm axon segment carrying the contacts (measured), diameter 2 µm (guessed), area 314 µm², against 4,300 µm² from the MN5 whole-cell 43 pF (Fayyazuddin 2006) at Cm 1 µF/cm² (guessed). Bracket 0.012-0.15: diameter 1-4 µm, and Kadas et al. adult MN5 127 ± 16 pF, n 52 (PMC6595220, measured).
- **ρ = 1.6.** Derivation: g_c = π d²/(4 Ri ℓ), with d 2 µm (guessed), Ri 200 Ω·cm (inside the fitted Drosophila 102-311, Gouwens & Wilson 2009; s12) and ℓ 100 µm, the arbor-to-contact path (guessed). That gives 15.7 nS × Rin 102 MΩ. Bracket 0.13-25 (d 1-4, Ri 100-400, ℓ 50-150).
- No value is fitted to the test.

**Runs** (Mac, isolated CNS, profile m10f + `nt_from_physiology=1` + `unitary_psp_from_recordings=1` + the switch, **seed 1**; seed 0 was spent on the point model):
1. `gf_psi_dlm_path.py`: mechanism gate. Soma peak 4.71 ± 0.5 mV after one GF spike; the axon peak is reported.
2. `gf_latency.py --trials 20`, gaps on and off.
3. Sensitivity, reported and not scored: the four (q, ρ) bracket corners, 20 trials each, gaps on.

**Pass** (the Director's): gaps on, DLMn a, b follow ≥ 90% of GF spikes, **and** the median muscle latency is inside the measured range for some wild-type fly:
- **(a) Augustin 2017, 1.36-1.849 ms.** Spent (F-GJ-3), so this is a consistency check.
- **(b) Ryglewski et al. 2014 PNAS 111:18049** (PMC4273390): "the delay between giant fiber stimulation and muscle potential is 1.85 ± 0.21 ms". n 10, the onset of the DLM response, control genotypes. The ± is not defined in the text. Read as SD (the narrower case), that is 1.43-2.27 ms (mean ± 2 SD). **Held out and never used before; spent by this call.**

**Prediction:**
- DLMn a, b follow 20/20 at the central values.
- Median latency 2.0-2.3 ms: GF→PSI about 0.3 ms + the PSI delay row 0.797 + an axon rise of 0.1-0.4 + the DLMn a, b delay row 0.796.
- So **FAIL on (a)** and **PASS on (b)**.
- Gaps off: 0/20, as for the point model. Sensitivity: follows at every corner except low ρ with high q.

**Falsifier of the prediction:** DLMn follows < 90% at the central values. If so, the derived coupling cannot relay the measured EPSP, and the threshold gap or the soma-axon split is wrong. A latency < 1.9 ms also falsifies it.

**Not adopted by this test alone:** adoption needs the gate, a battery run and a viewed figure. Then: DLMn tau_m (4.4 ms from Fayyazuddin, 12.3 ms from Kadas; measured spread) and the inferred delay rows (velocity 0.5 m/s, t_syn 0.5 ms).

### fly2 N30 build note and gate reading (20 Oct, 23:48; after the toy-graph tests, before any whole-CNS run)
**Built as registered** (`lif._two_compartments`, `Network._two_comp_init`, `tests/test_two_compartment.py`, 8 tests). The switch `cell_type:all|two_compartments_where_point_fails` is neutral 0. The GPU, conductance synapses, graded cells and a receptor-channel or slow copy on an axon edge are refused. `cell_type:all|n_compartments` (per-cell counts, synapses placed by position) is still refused. N30 goes from absent to partial. q and ρ are registered as class `MN` (`cell_class:MN|axon_membrane_share`, `|soma_axon_coupling`). Their registry status is INFERRED with the method "derived from guessed geometry", because the registry's DERIVED requires every input measured. parameters.csv bound basis: guessed; prior log-uniform over the bracket.

**Choices the registration left open, fixed now (none tuned on output):**
- **Axon weights.** An axon edge's weight is divided by q, so the synaptic charge is kept. The unitary-PSP recalibration then sets the weight from the passive pair's soma peak. The division only changes the weight before recalibration.
- **No soma reset.** The soma is never reset or clamped by an axon spike.
- **Soma processes.** Spike-triggered soma processes (adaptation, ADP, the rung-1 channel spike hook) do not see the axon spike. The paper: "small and broad in somatic recordings".
- **Output spike.** Every output of the cell (transmission, gap and electrical events, spike count) uses the axon spike.
- **What the axon has.** The axon has no noise and no channels of its own. It uses the cell's v_leak and starts at rest.
- **Soma DC loss.** The soma's other inputs lose a little steady-state effect to the axon load: (1−q)/((1−q)+qρ/(q+ρ)) = 0.93 of the point cell's at the class values. This is stated as the validity range in the code.

**Gate reading** (clarifying run 1, made before it runs). The paper measured the 4.71 mV EPSP without the spike: spike failures, the inflection point, and forced refractoriness (F-GJ-5). So the gate's soma peak is read with the DLMn axon spike disabled (`gf_psi_dlm_path.py --axon-passive` raises the DLMn threshold out of reach; the soma cannot spike under the switch). Window 30 ms, because the 10 ms window cut the point-model peak at its last step. The same probe with spiking on reports the soma and axon peaks and the DLMn spike count. Both runs use seed 1.

**Toy-graph observation, not tuned:** one PSI spike gave two DLMn axon spikes 2.8 ms apart. The 5 ms synaptic current outlasts the 2 ms refractory period at about 2.5× threshold. The real DLM fires 1:1 to GF. `gf_latency.py` now reports the DLMn spikes per GF spike. A doublet in the whole CNS is recorded as an observation and a blank (axon refractory, or PSI→DLMn decay), not a pass or fail item.

### fly2 N30 results (21 Oct, 00:01; F-GJ-6)
**Registration:** DECISIONS 20 Oct 23:30, with the 23:48 build note.

**Results:**
- **Gate: PASS.** Soma 4.78 mV with the axon passive; axon 13.8 mV.
- **Director's pass: PASS.** Gaps on, DLMn a, b follow 20/20, median muscle latency 2.196 ms.
  - Inside Ryglewski 2014's 1.43-2.27 ms (held out, now spent).
  - Outside Augustin 2017's 1.36-1.849 ms (spent; as predicted).
- **Gaps off:** 0/20.
- **Predictions:** all met except the sensitivity one.
- **Corners:** follow at ρ 0.13 (both q), 0/20 at ρ 25 (both q).
  - Derived boundary: ρ < about 4 at any q in the bracket.
- **Doublet:** DLMn fires 2 spikes per GF spike (the fly fires 1). This is a new blank.

**Decision:**
- **Nothing adopted.** The switch stays neutral.
- **Before adoption:**
  1. pin ρ (it decides the pass; the registered bracket spans the boundary);
  2. register a fix for the doublet as its own blank (axon refractory or the PSI→DLMn current decay, both from measurements);
  3. the DLMn tau_m blank (4.4 ms measured against the shared 20);
  4. a battery run.
- **Measurement plan:** `docs/research/s20_n30_pin_q_rho.md`. EM geometry first (fly2 can do it), then one MN5 soma recording for Ben's measurement experiment.
- **Fixed in passing:** `tests/test_organism.py::test_depression_weakens_repeated_spikes_and_recovers` failed at HEAD. It passed LIFParams positionally, and the ADP fields added earlier shifted its depression arguments. It now uses keywords for std_u and std_tau_rec.

### fly2 pre-registration: class MN q and ρ from the male-CNS MN5 skeleton (N30 option B; 21 Oct, 00:07; Director's brief 21 Oct; before any skeleton or synapse fetch for this purpose)
**Why.** F-GJ-6 passed at q 0.07 and ρ 1.6, derived from guessed geometry. DLMn follows the GF only for ρ below about 4, and the registered bracket (0.13-25) spans that boundary. The male-CNS skeleton of MN5 (DLMn a, b) gives the diameter and path length, so only Ri stays fitted.

**Seen before writing.** The `data/derived/skeleton_lengths.csv` row of one DLMn a, b cell (bodyId 801970): cable 7,454 µm; median radius along the root-to-farthest-leaf path, excluding its first 10%, 1.36 µm; root radius 4.67 µm. Nothing else about this geometry.

**Method** (`scripts/connectome/mn_axon_geometry.py`; male-cns v1.0, neuPrint; 8 nm voxels to µm):
- **Cells.** Every DLMn a, b cell (MN5, where Rin and Cm were measured) sets the class value. Every DLMn c-f cell is computed and reported, not used.
- **Data.** The healed skeleton, rooted at the soma node as in `skeleton_lengths.py`. Every PSI→cell synapse, each mapped to its nearest skeleton node.
- **Axon base.** Walk from the PSI contact nearest the root toward the root. The axon base is the first branch point whose off-path subtrees hold ≥ 5% of the cell's cable. Sensitivity: 1% and 20%.
- **Contact site.** The synapse-weighted median path position of the PSI contacts.
- **Coupling.** R_ax = Ri Σ Δℓ / (π r₁ r₂) over the skeleton edges from the axon base to the contact site (a frustum's axial resistance). g_c = 1 / R_ax.
- **ρ = g_c × Rin**, with Rin 102 MΩ (Fayyazuddin 2006, MN5, measured). Ri is 200 Ω·cm at the centre, with the range 102-311 (Gouwens & Wilson 2009, fitted, as registered 20 Oct).
- **q = A_axon / A_total.** Areas are frustum lateral areas, π(r₁ + r₂)·slant, plus the soma as a sphere of the root radius. A_axon is the whole subtree distal to the axon base that holds the PSI contacts, inside the volume. Reported brackets: A_axon / (Cm / 1 µF/cm²) at 43 pF (Fayyazuddin 2006) and 127 pF (Kadas et al.).
- **Class value.** The mean over the DLMn a, b cells.
- **Boundary.** ρ*(q) is the ρ at which the passive pair's axon peak reaches the 7 mV gap, with the soma peak held at the measured 4.71 mV. It uses the model's own pair update (tau_m 20, tau_s 5, dt 0.1 ms; `Network.psp_peak_per_mv_axon`).

**Decision rule:**
- **PASS** (the geometry supports the build): ρ < ρ*(q) across the whole Ri range. Class MN then takes the derived q and ρ (central Ri), with the label "derived from EM geometry, measured Rin, fitted Ri"; the registry status stays inferred, because Ri is fitted. The GF escape is rerun at seeds 1 and 2 as a consistency check only, since Ryglewski 2014 is spent.
- **FAIL**: ρ > ρ*(q) across the whole Ri range. The build fails at measured geometry, F-GJ-6's pass is withdrawn as resting on guessed geometry, and the next candidate is a spike-initiation zone with a lower threshold (its own registration).
- **UNDECIDED**: the Ri range spans ρ*. The recording (option C) decides. The table takes the derived values and brackets, and the label says so.
- **Shrinkage.** Report the linear radius factor that would move ρ across ρ*. No correction is applied; no factor is measured for this volume.

**Prediction.** From the cached 1.36 µm radius and a guessed 50-150 µm base-to-contact path: ρ 1.9-5.8 at Ri 200, central about 3. So PASS or UNDECIDED, and q 0.03-0.10.

**Falsifier of the prediction:** ρ at Ri 200 above 4.

**Validity, stated now.**
- Only the part inside the volume is counted. The axon and part of the PSI contact continue into the nerve (F-GJ-5).
- Skeleton radii are approximate; the membrane is uniform; the cell has one isopotential axon segment.
- The axon base is the conservative choice. It gives the shortest path, so the highest ρ.

### fly2 N30 option B results and the doublet diagnosis (21 Oct, 00:18; F-GJ-7)
**Registration:** DECISIONS 21 Oct 00:07.

**Geometry** (`scripts/connectome/mn_axon_geometry.py`; `data/derived/mn_axon_geometry.csv`/`.json`; skeletons and PSI synapses saved under `data/derived/mn_axon_geometry_skel/`; figure `docs/media/s21_fly2_mn5_geometry.png`, viewed):

| MN5 | PSI synapses | Base → median contact | d_equiv | q | ρ at Ri 200 (102-311) | ρ* |
|---|---|---|---|---|---|---|
| L (801970) | 17 | 76 µm | 1.96 µm | 0.156 | 2.03 (1.31-3.98) | 3.51 |
| R (801295) | 26 | 23 µm | 1.78 µm | 0.052 | 5.57 (3.58-10.9) | 4.03 |
| **Class mean** | | 49 µm | 1.87 µm | **0.104** | **3.80 (2.44-7.45)** | **3.78** |

- **Verdict: UNDECIDED.** The Ri range spans ρ*. The class value sits 0.5% above the boundary, and a 1.00× radius change crosses it, so any shrinkage correction (real radii larger) would push it to FAIL. The two MN5s of one fly fall on opposite sides.
- **Prediction met.** "PASS or UNDECIDED, ρ about 3" came out UNDECIDED at 3.80; the falsifier (ρ > 4) was not triggered. q came out 0.104, inside the predicted 0.03-0.10 only at its top edge (outside by 0.004).
- **Base.** The 1% sensitivity puts the base inside the contact field for both cells (only 8-18% of PSI synapses distal), so the 5% rule is the meaningful one. The 20% rule finds no branch point for MN5 L (the arbor splits into small branches).
- **DLMn c-f** (reported, not used): the rule gives a value for 6 of the 8 cells. ρ at Ri 200 is 2.41-35.98 and q is 0.003-0.147.
  - In 800890 and 803013, the PSI contacts sit on more than one branch, so the median contact is not distal to the base at any FRAC. The rule raises an error and the cell gets no row.
  - In 801998, the 5% base lands inside the contact field: only 2.5% of the PSI synapses are distal to it (q 0.003).
  - So the base rule is fragile wherever the PSI contacts spread over branches. In the two MN5s, all PSI synapses are distal to the base.
- **Table.** As registered for UNDECIDED, `two_compartment_classes.csv` now has q 0.104 (0.052-0.156) and ρ 3.80 (1.31-10.9), labelled "derived from EM geometry, measured Rin, fitted Ri". The `parameters.csv` rows were updated to match. The mechanism tests pin the s20 pair by override.

**Consistency runs in the network** (seed 1, gaps on, 20 trials; Ryglewski 2014 is spent, so none of these is scored; `scripts/probes/n30_optB_runs.sh`, outputs `runs/s21/optB_*.json`):

| Values | DLMn a, b follow | Spikes per GF | Muscle latency |
|---|---|---|---|
| Class (0.104, 3.80) | 19/20 | 1 | 3.20 ms |
| MN5 L (0.156, 2.03) | 20/20 | 1 | 2.80 ms |
| MN5 R (0.052, 5.57) | 0/20 | 0 | |
| s20 guessed (0.07, 1.6), F-GJ-6 | 20/20 | 2 | 2.20 ms |

So at measured geometry the doublet goes away, but the spike comes late (2.8-3.2 ms against Ryglewski's 1.43-2.27) or not at all. The axon reaches threshold only near its peak.

**Doublet diagnosis** (`scripts/probes/n30_doublet_mechanism.py`, an exact replica of the lif.py pair update; figure `docs/media/s21_fly2_n30_doublet.png`, viewed). At the s20 values, when the 2 ms refractory period ends, the axon's target potential is 11.5 mV from the synaptic current and 0.11 mV from the soma, against the 7 mV threshold.
- Cutting the soma→axon term keeps the doublet (second spike 3.3 ms instead of 3.2): **not ping-pong**.
- Removing the synaptic current at the first spike leaves 1 spike: **the synaptic tail is the cause**. The reset to rest without an afterhyperpolarisation (AHP) lets it act.
- The in-network second spike comes 3.2 ms after the first (spike steps 15, 47 in `gate_spiking`), as in the replica.
- Any one of these removes it at the s20 values: refractory ≥ 3.0 ms, an AHP ≥ 7.5 mV below rest, tau_s ≤ 1.8 ms, or tau_m 4.4 ms.

**Synaptic decay and tau_m across the derived values** (replica):
- At tau_m 20, every decay in the Drosophila nicotinic range (1.1-4 ms; N29 table) gives exactly one spike, 0.1-0.9 ms after the EPSC starts, at the class values (R needs ≤ 3 ms). At the shared 5 ms the class gives none.
- At tau_m 4.4 ms, the class and R values never fire at any decay.

**The 4.4 ms tau_m is suspect.**
- It is Rin × Cm (102 MΩ × 43 pF). The skeleton membrane is 24,650-25,840 µm², which is about 250 pF at 1 µF/cm², 6× the 43 pF.
- The capacitance read from a soma transient in a cell this extended is likely space-clamp limited.
- Rin × skeleton area gives Rm of about 25 kΩ·cm², inside the fitted Drosophila 8.3-26.4 (Gouwens & Wilson 2009), and tau_m of about 25 ms.
- **Reading:** the DLMn tau_m blank stays open. The slow time constant of a step response (MEASUREMENT_LIST item 1) is the measurement that decides it. 4.4 ms is not applied as measured.

**Decision:**
- Nothing adopted.
- The doublet is no longer the main blank: at measured geometry the cell fires once, but late.
- **Next**, as its own registration: give the PSI→DLMn connection a nicotinic decay from measurement. It is the one candidate that fixes latency and spike count together at the derived values.
  - Building it means letting an N29 decay row act on an axon edge and on a unitary-PSP edge; both are refused today.
  - The value comes from a measurement: a PSI→MN5 EPSC or EPSP decay if the literature has one, otherwise the class bracket for adult nicotinic synapses.
  - The test is held-out GF→DLM data (sealed by the literature agent, not read) at seed 2.
- MN5 soma recording added to `docs/MEASUREMENT_LIST.md` (item 1: q, ρ, tau_m, threshold, AHP and refractory, the soma amplitude of the axon spike, EPSP decay).

### fly2 N30: what the MN5 literature changes, and why no doublet or latency fix is adopted (21 Oct, 00:25)
**Source.** `docs/research/s21_mn5_literature.md` (Sonnet literature agent, sections A-D; read). The sealed file `docs/research/sealed/s21_gf_dlm_sealed.md` was not read. A repo grep for "Kadas" matched one header line of it ("Source 1 — Ryglewski S, Kadas D, … (2014)"); no quantity or value was seen. The agent's value-free summary of it is in HANDOFF's sealed register.

**What changes.**
- **The 127 pF is Herrera-Valdez et al. 2012** (J Comput Neurosci 34:211, PMC6595220). It reports MN5 Rin 97 ± 31 MΩ and Cm 127 ± 16 pF, n 52, measured. The s20 note and the 00:07 pre-registration called it "Kadas et al."; the s20 note and the script's column name are corrected, and no value changes.
- **MN5 tau_m as Rin × Cm is 4.4 ms (Fayyazuddin 2006) or 12.3 ms (Herrera-Valdez 2012).** Both are derived from measurements; the two labs' Cm differ 3×. Rin × the skeleton area bounds it at about 25 ms (1 µF/cm²). The DLMn tau_m blank stays open. ρ* at the class q is 3.78 at tau_m 20 and 2.94 at 12.3.
- **The adult nicotinic decay bracket is wider than the 1.1-4 ms used at 00:18.**
  - Gu & O'Dowd 2006 (adult Kenyon cells in situ, read directly) give an mEPSC decay τ of 4.45-6.73 ms.
  - The bracket is now 1.1 (ORN→PN, fitted) to 6.73 ms (measured). The shared 5 ms is inside it.
- **Not found in readable primary text:** a PSI→MN5 decay, or MN5's threshold, AHP and refractory period. Fayyazuddin 2006 gives the EPSP amplitude only. Ryglewski & Duch 2009 and Ryglewski, Kilo & Duch 2014 (EJN, spike shape by stage) were behind paywalls.

**Replica scan** (`n30_doublet_mechanism.run`; one PSI spike, soma peak held at 4.71 mV). Each cell gives the spike count, then the spike times in ms after the EPSC starts:

| tau_m | Cell (q, ρ) | tau_s 1.1 | 2 | 3 | 4 | 5 | 6.73 |
|---|---|---|---|---|---|---|---|
| 4.4 | class (0.104, 3.80) | 0 | 0 | 0 | 0 | 0 | 0 |
| 12.3 | class | 1: 0.1 | 1: 0.4 | 1: 1.4 | 0 | 0 | 0 |
| 20 | class | 1: 0.1 | 1: 0.3 | 1: 0.5 | 1: 0.9 | 0 | 0 |
| 20 | class at Ri 311 (ρ 2.44) | 1: 0.1 | 1: 0.2 | 1: 0.4 | 1: 0.6 | 1: 0.7 | 1: 1.1 |
| 20 | MN5 L (0.156, 2.03) | 1: 0.2 | 1: 0.4 | 1: 0.6 | 1: 0.8 | 1: 1.0 | 1: 1.4 |
| 20 | MN5 R (0.052, 5.57) | 1: 0.0 | 1: 0.2 | 1: 0.5 | 0 | 0 | 0 |
| 20 | s20 guessed (0.07, 1.6) | 1: 0.1 | 2: 0.1, 3.0 | 2: 0.2, 2.9 | 2: 0.3, 3.1 | 2: 0.4, 3.2 | 2: 0.5, 3.5 |

- tau_m 25 matches tau_m 20 within 0.1 ms, except that the class cell also fires at 5 ms (1: 1.2).
- One in-network point maps replica time to muscle latency: s20 gives 0.4 ms in the replica and 2.20 ms in the network. On that single point, Ryglewski's spent upper bound of 2.27 ms corresponds to about 0.5 ms here.

**Reading.**
- Within the measured ranges, the derived class values give one early spike (≤ 0.5 ms) only for tau_s ≤ 3 ms at tau_m ≥ 20, or at the high-Ri end.
- At the shared 5 ms the class does not fire, and at tau_m 4.4 it never fires.
- So no value available tonight fixes latency and spike count from a measurement. The decay bracket spans the flip, and DLMn's AHP and refractory period are not in readable text.
- A PSI→DLMn-only decay chosen to pass would be a per-route knob. Changing the shared nicotinic decay would move every cholinergic synapse, and this pathway alone doesn't justify that.

**Decision.**
- Nothing adopted. The 00:18 "Next" (a PSI→DLMn nicotinic decay from measurement) is withdrawn: there is no measurement to take it from.
- The decider is `docs/MEASUREMENT_LIST.md` item 1, now annotated with the replica's thresholds.
- The held-out GF→DLM data stay sealed, kept for the build at measured values.
- Corrections:
  - F-GJ-7's "nicotinic range (1.1-4 ms)" is corrected in place.
  - In the 00:07 pre-registration, "Kadas et al." means Herrera-Valdez et al. 2012.
  - The 00:18 entry's "Next" is superseded by this entry.

### Pre-registration s14: class-level options test for the walking break (20 October, 22:28, before any network run with a new switch)
DIAGNOSTIC, forced drive (Director brief, 20 Oct). Nothing is adopted. All new values are **guessed**, shared by type or hemilineage, and never set per synapse. The question: does one unmeasured class property (16B firing mode; E1/E2 intrinsic bursting) let the bypass core (DNg100 → E1/E2/I1/IN19A007 → leg MNs) alternate antagonist pools? On male-CNS and MANC counts it does not (F-XCONN-2).
- **Harness (as X1):** m10f0, seed 12, brain and senses off, DNg100 driven at 15/25/40 mV for 300-1300 ms of 1500 ms, thorax tethered: `bypass_s2_descending.py` (MN pools, body). Same drive with `bypass_s3_chain.py` (core cells, 900 ms, drive 100-900 ms). Backhouse, done-files, launches gated on load < 24.
- **Arms** (one line each; the pass criterion is the same for all, below):
  - **M0:** neutral m10f0, re-run in the same batch. It must fail. If M0 passes, the test is broken.
  - **A:** `class:vnc_local_16B|graded=1`. The 433 unknown-mode 16B cells, I1 included, release graded through the shared N1 graded rows (inside locust NSI bounds; docs/research/s14_16b_firing_mode.md).
  - **B4:** E1/E2 saturating ADP at 20 mV ceiling, 100 ms decay, 200 ms recovery (`cell_type:core_rhythm_exc|adp_mv=20, |adp_tau_ms=100, |adp_recovery_ms=200`). Chosen by calibration rule v2 on isolated cells before this run: 4 spikes in 92 ms.
  - **B2:** the same ADP at 25 mV, 40 ms, 50 ms, the shortest admissible burst (2 spikes in 21 ms). B4 matches the cricket spike count and B2 the cricket burst duration; no setting does both (docs/research/s14_burst_ranges.md).
  - **C4 = A + B4; C2 = A + B2.**
  - **B' / C' (NaP x 1.5-10): not run.** No admissible scale (1 spike at every scale, calibration). Recorded as a negative calibration result.
- **Pass (per arm, scored on the S2 run at each drive): `s4b_score.rhythm` → rhythm_pass, then confirmed by viewing the raster.**
  - Two antagonist pools of one leg each have modulation depth ≥ 0.5 (f0 7-16 Hz, at least 2/3 of cycles at the 3-spike floor) and are drive-locked (rate ≥ 2× pre-drive, or silent before).
  - They are out of phase: r ≤ −0.3 at zero lag, or a lagged peak (10-30 ms) of ≥ 0.5.
  - Activity stops at drive-off: summed leg-MN rate over 1300-1500 ms ≤ 1.5× pre-drive.
  - Before viewing I write down which pair passed. On the raster the two pools must visibly alternate over most cycles; if not, the pass is void.
  - An arm passes if any of its drives passes. That is 5 arms × 3 drives = 15 tries, so a single pass is weak evidence and needs a seed repeat before any claim.
- **Secondary (reported, not pass criteria), from the chain run:**
  - I1 recruited. Spiking I1: as X1 (T1L I1 fires on ≥ 50% of E1 cycles). Graded I1 (arms A, C): mean V during drive ≥ 2 mV above rest (the locust NSI release threshold, Burrows & Siegler 1978) and a cycle-locked swing ≥ 2 mV at E1's f0.
  - E1/E2 spikes per cycle, and f0.
- **Falsifiers, written now.**
  - An arm with no rhythm_pass at any drive falsifies "this class property alone, inside these bounds, fixes the break".
  - If every arm fails, neither unmeasured fact alone is sufficient in this model; the next suspects are the slow-MN BK the E1/E2 cells inherited, and the MN transfer (F-BYPASS-7).
- **Held-out register.** The S4b recruitment order stays unspent; nothing here reads it and `s4b_score heldout` is not run. No sealed data is used.
- **If an arm passes, the measurement that would settle it is written into FINDINGS for Ben's measurement experiment:**
  - A: whether 16B premotor cells (IN16B036) spike or release graded, by patch or voltage imaging during fictive walking.
  - B: whether E1/E2 burst intrinsically, by current injection with synapses blocked (spikes per burst, rate, burst end).
- **Prediction (mine, before running):** A recruits graded I1 more than spiking I1 did, because release starts 2 mV above rest instead of at threshold, but A alone does not alternate the MN pools; the B arms raise E1/E2 output and I1 drive. I expect at most one arm to pass, and C2 is the likeliest.

### Results s14 at 25 mV, S2 only (20 October, 23:57; partial: 15/40 mV and the chain runs are queued; nothing adopted)
Scored with `s14_score.py` (written before any output) on the six S2 runs from backhouse, then viewed: `docs/media/s14_arms_rasters_25mv.png` and `docs/media/s14_arms_frames_25mv.png`.
- **No arm passes at 25 mV.** M0, A, B4, B2, C4 and C2 all have 0 transfer-pass pools and 0 antagonist pairs. Leg-MN activity stops at drive-off (post/pre 0.93-0.95). M0 fails as required, so the test is not broken.
- **Viewing agrees; no pair was written down, because none passed.** All six rasters look alike: the tonic ~23 Hz tibia-flexor line (present before drive) and sparse co-active flecks in other pools. Nothing alternates in any leg. Frames: the thorax is on the floor and the legs are splayed in every arm, with no stepping. The wing flicks at 700 and 1100 ms are also in M0, so they don't come from any arm.
- **What each arm changes at the MN layer** (run JSON, during drive): the B arms raise the mean premotor rate from 0.13 to 0.28-0.29 Hz, but the leg-MN rate stays 4.72-4.76 Hz (M0 4.81) and no pool becomes rhythmic. The A arms (16B graded) lower the leg-MN rate to 4.22-4.29 Hz and the peak activation from 0.079 to 0.050, and they blur the tonic line. The B arms also raise peak activation from 0.079 to 0.13. M0, A and C2 each have one rhythmic pool (a tibia pool on a different leg each time); B4, B2 and C4 have none. More core output does not reach the MNs as a rhythm.
- **Runner:** the previous session's runner was waiting on the load gate (backhouse load 26, all from outside our distro). It was restarted detached at 23:57 with chain:25 queued next, so the network-only check of whether the switches engage E1/E2/I1 comes first. Done-files are `~/fly-m10f/runs/s14/arms/{s2,chain}/<arm>_<mv>.done`; `ALL.done` marks the end.

### Results s14, all drives (21 October, 01:16; F-S14-1; nothing adopted)
18 S2 tries, 0 pass. The falsifier is hit for every arm. Viewed: rasters at 15/25/40 mV, the frame sheet for all 18 runs, and the T1L chain panels. The B arms don't burst inside the network: E1/E2 fire a near-continuous 24-33 Hz train, and the 12 Hz cycle is lost. I1 is never recruited; graded I1 rises at most 1.54 mV above rest, under the 2 mV threshold. Adding core spikes leaves MN output unchanged. The hand-off probe (`s14_handoff.py`): a median E2 → leg-MN edge gives 0.47 mV per spike, and E1 0.17 mV, against a 7 mV gap. **Hand-off reading: confirmed as a bottleneck, not as the only break** (E2 → I1 fails the same way). This meets the condition for the two-compartment arm below.

### Pre-registration s15: two-compartment premotor and leg-MN arm (21 October, 01:16, before any two-compartment row for these cells or any run)
DIAGNOSTIC, forced drive. Nothing is adopted. Ben approved it (Director note, 20 Oct): two compartments are allowed where a point model provably fails. The failure (F-S14-1, F-BYPASS-7): one somatic-range PSP can't both stay in the measured range and carry the core's output across the hand-off.
- **Mechanism (built by fly2, N30; `lif._two_compartments`, switch `cell_type:all|two_compartments_where_point_fails`, neutral 0).** The listed cells get a spike-initiation compartment. Edges from `axon_inputs` land there, and spikes start there. Channels (BK, ADP), noise and gap junctions stay on the soma. Shared class values are q (spike-zone share of the membrane) and ρ (coupling × whole-cell Rin). This is the CPU path; the S2 and chain harnesses run on the CPU.
- **Precondition (ownership; DECISION NEEDED from the Director):** the rows go into fly2's `data/params/two_compartment.csv` and `two_compartment_classes.csv`. Either fly2 adds them or the Director clears fly to. The switch also turns on the existing DLMn rows. They are flight MNs outside the walking circuit, which I'll state in the result.
- **Values (no fitting).** Option B as F-GJ-7: skeleton geometry from male-cns v1.0 via fly2's `mn_axon_geometry.py`, a measured Rin where one exists, and Ri 200 Ω·cm (102-311, Gouwens & Wilson 2009, fitted there). Bracket: across cells and the Ri range.
  - Class **leg_MN**: front-leg MNs (tibia fast/intermediate/slow and coxa/trochanter types). Rin from a measured leg-MN source (Azevedo 2020, which a Sonnet scan checks before the run).
  - Class **core_premotor**: E1, E2, I1 and IN19A007/004/002. There is no Rin recording for them, so Rin is guessed from Drosophila VNC interneuron recordings (scan) and labelled guessed.
  - If a class can't be derived, the arm doesn't run. The class MN (MN5) values are not carried over silently.
- **Admissibility gate (single-cell and unitary, before any network run).** Rerun `s4b_unitary_psp.py`, recording at the soma, at the class values. The somatic unitary PSP per synapse must stay inside the measured insect range (`docs/research/s13_s4b_unitary_psp.md`). The spike-zone PSP is reported. If it fails, that arm has no admissible value and is recorded as negative.
- **Arms:** M0 (neutral, re-run); TM (leg_MN rows, all chemical inputs on the spike zone); TP (core_premotor rows, likewise); TPM = TM + TP. DNg100 15/25/40 mV, seed 12, the s14 harnesses (S2 + chain) on backhouse, with done-files and the rule-16 gate.
- **Pass:** exactly as s14 (`s4b_score.rhythm` → rhythm_pass, then viewing, with the passing pair written down before viewing). 3 arms × 3 drives = 9 tries. A single pass needs a seed repeat (13, 14) before any claim.
- **Secondary:** transfer-pass pools per arm, I1 recruitment (the X1 spiking criterion), E1/E2 spikes per group, and leg-MN rates. Bracket corners (q_lo/ρ_hi, q_hi/ρ_lo) are reported as sensitivity and never count as a pass.
- **Held-out:** if an arm passes, its seed repeats come first. Then the S4b recruitment order (slow, then intermediate, then fast; measured, unspent) is spent once on that arm at its passing drive. Nothing is spent otherwise.
- **Falsifier:** no pass at the class values at any drive. That would mean a two-compartment hand-off at derived values doesn't fix alternation. The next suspects would be the slow-MN BK on E1/E2 (named by s14) and proprioceptive feedback (S4 proper).
- **Prediction (mine):** TM raises transfer-pass pools above 0 but gives no antagonist pair, because without I1 the stance pools get no rhythmic inhibition. TP is likelier to recruit I1. If anything passes it is TPM, and I expect at most one pass.
- **Measurement for Ben's list:** see F-S14-1. A front-leg MN somatic recording with E2/E1 activation gives the unitary PSP and Rin, and ideally the soma-to-neurite attenuation, which fixes ρ.

### s15 ownership cleared, Rin values and the gate's operational form (21 October, 01:22; before any row is written or any arm runs)
- **Ownership (Director, as Ben, 21 Oct):** fly may add the leg_MN and core_premotor rows to `data/params/two_compartment.csv` and `two_compartment_classes.csv`. Append only; fly2's DLMn and MN rows and its derivation method stay unchanged. fly2 is on the zip packer tonight and won't touch those tables. Cell rows and their class rows go in together, so the switch never meets a class without values (that would also break fly2's DLMn runs).
- **Geometry:** `scripts/connectome/premotor_mn_geometry.py` imports fly2's `mn_axon_geometry.reduce()` and runs it unchanged. Only the cells and contacts differ. The cells are the T1 leg-MN types in LEG_TYPES (tibia and coxa/trochanter) and the 12 T1 core cells, both sides. The contacts are every postsynaptic site, because the arms put all chemical inputs on the spike zone. The class value is the mean over cells at FRAC 0.05 and Ri 200. The bracket is the cells' q10-q90 × the Rin range × the Ri range; with this many cells I use q10-q90 rather than fly2's two-cell min/max.
- **Rin (s15 Sonnet scan):**
  - **leg_MN:** 300 MΩ (intermediate), bracket 150-700. Measured: Azevedo et al. 2020 eLife Fig. 3E, T1 tibia flexors, fast 150 (n 15), intermediate 300 (n 11), slow 700 (n 14), whole-cell at the soma, in vivo. The same paper says current injection at the soma failed to fire fast and intermediate MNs, "likely because of intrinsic morphological or electrophysiological properties that electrically isolate the soma from the spike initiation zone". That is the measured, qualitative basis for the leg_MN row, the same kind of evidence as fly2's DLMn row.
  - **core_premotor:** 600 MΩ, guessed. No adult VNC interneuron Rin was found. The central value is adult antennal-lobe PNs, 598 ± 69 MΩ (Gouwens & Wilson 2009, measured in another class). The bracket, 150-1000, is guessed.
- **Cells in the rows:** type selectors can't split segments (instances have no neuromere), and q and ρ are class values. So each row names its types in all three thoracic neuromeres; the values are derived from T1, where Rin was measured. The pre-registration said "front-leg MNs". This applies the same class to the other legs and is stated in the result.
- **Admissibility gate, operational form (fixed now):** `s4b_unitary_psp.py` at the class values, recording at the soma. TM measures excitatory premotor → leg MN; TP measures excitatory inputs → core cells. An arm is admissible if both hold:
  - the somatic median is ≤ 0.3 mV per synapse (the top of the small-central-neuron band, with leg MNs expected at or below it);
  - the somatic q90 PSP per spike is inside 0.4-10 mV (the measured insect band; the MN→MN outlier is excluded).

  The spike-zone PSP is reported, not gated. Otherwise as pre-registered (01:16).

### Results s15 step 1, geometry (21 October, 01:25; F-S15-1; no row written, no arm run)
fly2's option-B rule doesn't define a spike-zone compartment for cells whose inputs cover the arbor. The base walk starts from the input contact nearest the soma, which here sits close to the soma. It then fails for 27 of 94 T1 leg MNs and 4 of 12 core cells (no branch point holds ≥ 5% of the cable off the path). Where it does return values, the compartment it picks holds a median 2.1% of the leg MN's input sites, and 0.1% of the core cells'. Mean q is 0.085 (leg_MN) and 0.0024 (core). That compartment is a twig, not the arbor the arm puts every input on. **Per the 01:16 pre-registration, "if a class can't be derived, the arm doesn't run"**: TM, TP and TPM don't run at option-B values. ρ at the stated Rin is reported anyway, in `data/derived/premotor_mn_geometry.json`: leg_MN 1.30, core 3.10. These are not used.

### Pre-registration s15b: a soma–arbor split for distributed-input cells (21 October, 01:25, before computing it)
The rule fly2's method lacks, for unipolar insect neurons whose inputs and spike zone are in the neuropil and whose soma hangs off a primary neurite. It is a new derivation for the new rows only; fly2's rows and method are unchanged.
- **Rule:**
  - **Split point:** walk from the soma along the skeleton. The split is the first branch point whose off-path subtrees hold ≥ 5% of the cable (1% and 20% are reported).
  - **Soma compartment:** the soma sphere plus the primary neurite up to that point.
  - **Spike-zone compartment:** everything distal to the split point (arbor, spike zone and axon).
  - **q:** the distal membrane area divided by the whole.
  - **R_ax:** Ri × Σ dl/(π r1 r2) along the primary neurite.
  - **ρ:** Rin / R_ax.
  - **Rin and Ri:** as 01:22.
  - **Check:** report the fraction of input sites distal to the split. A class is derivable only if its median is ≥ 0.9.
- **Validity:** it lumps the arbor and the spike zone into one isopotential compartment, so it only describes the soma-to-arbor attenuation, not attenuation within the dendrites.
- **Prediction (mine):** q comes out near 0.9. The spike zone then sees about the point-model PSP and the soma a smaller one, so TM and TP change the hand-off little at the shared scale 1. Read that way, a two-compartment cell matters for this break only if the shared scale is anchored at the soma. That would be a separate, later pre-registration.
- **Gate, arms, pass, held-out and falsifier:** as 01:16 and 01:22.

### Results s15b step 1, split geometry, and the class values (21 October, 01:30; before the gate or any arm run)
- **Derivable, both classes** (`premotor_mn_geometry.py --split --offline`; `data/derived/premotor_mn_split.{csv,json}`). At FRAC 0.05 every cell has a split (94/94 leg MNs, 12/12 core).
  - leg_MN: median 95% of post synapses distal to the split (q10 82%); split median 81 µm from the soma; q mean 0.725 (cells q10-q90 0.517-0.880).
  - core_premotor: median 97.5% distal (q10 94%); split median 97 µm; q mean 0.933 (0.902-0.955).
  - FRAC 0.01 gives the same verdict; at 0.20 some cells have no split (reported, not used).
- **ρ uses the cell median, not the mean (a choice made now, before any gate or network run).** The 01:22 entry said "mean over cells", written for reduce(). Here one Ti flexor MN pair (L/R) splits ~1 µm from the soma, so its coupling is near-infinite (ρ 8,600 and 12,200) and the leg_MN mean is 223. That's a skeleton feature of two cells, not a class value. The median ρ is 1.38 (leg_MN, Rin 300) and 1.58 (core, Rin 600). Rin / mean(R_ax), the resistance-averaged alternative, gives 1.34 and 1.40, so the choice barely matters. q stays the mean (no outliers; the median is 0.75 and 0.93).
- **Rows written** (append only; fly2's rows untouched): `two_compartment.csv` gets leg_MN (the LEG_TYPES regex, axon_inputs `*`, measured from Azevedo's soma isolation) and core_premotor (the six core types, `*`, inferred). `two_compartment_classes.csv` gets leg_MN q 0.725 (0.517-0.880), ρ 1.38 (0.254-18.9) and core_premotor q 0.933 (0.902-0.955), ρ 1.58 (0.156-7.80). The brackets are the cells' q10-q90 × the Rin range × the Ri range.
- **Arm control:** `lif._two_compartments` gets `cell_class:<class>|two_compartments_in_run` (neutral 1, read only when set). It leaves a whole class out of a run. Every s15b arm sets `cell_class:MN|...=0`, so the DLMn (flight) rows stay off and the arms differ from M0 only in the walking rows. That's cleaner than the 01:16 plan, which let the DLMn rows ride along. TM sets core_premotor off, TP sets leg_MN off, TPM sets neither.
- **Gate as 01:22:** `s4b_unitary_psp.py --scales 1` at the class values, on backhouse. TM uses `--post leg` and TP `--post core`. M0 at both posts is run as the reference. The spike-zone PSP is reported, not gated.
- **What the geometry predicts (passive arithmetic, before any run):** with all inputs on the arbor compartment, its input resistance is about (q + (1−q)ρ/(1−q+ρ))⁻¹ × Rin. That's 1.05 × Rin for leg_MN and 1.00 × for core, and the soma sees ρ/(1−q+ρ) of the arbor's DC voltage (0.83 and 0.96). So the spike zone gets about the point-model PSP, and the hand-off should change little (my 01:25 prediction stands).

### s15b gate: both arms admissible (21 October, 01:34; before any arm output; arms launched 01:33 on backhouse)
`s4b_unitary_psp.py --scales 1`, seed 1, 24 excitatory presynaptic cells; `runs/s15/gate/*.json`.

| run | post | pairs | soma median mV/syn | soma per spike median (q10-q90) | spike-zone per spike median (q10-q90) |
|---|---|---|---|---|---|
| M0 | leg MN | 126 | 0.0212 | 0.344 (0.104-1.57) | n/a |
| TM | leg MN | 134 | 0.0180 | 0.295 (0.086-1.32) | 0.361 (0.106-1.78) |
| M0 | core | 46 | 0.0252 | 0.326 (0.140-1.77) | n/a |
| TP | core | 43 | 0.0237 | 0.277 (0.132-1.37) | 0.289 (0.137-1.43) |

- **Both arms pass the 01:22 gate:** the somatic median is ≤ 0.3 mV per synapse, and the somatic q90 per spike is inside 0.4-10 mV.
- The leg MN spike zone sees 1.05× the point PSP. The core spike zone sees 0.89×, against the passive DC estimate of 1.00×. The pair sets differ slightly, since pairs where the post cell spikes are dropped. So the hand-off gain from the split is about 1, as predicted at 01:30, against the 15-20× the 7 mV gap needs (F-S14-1).

### Pre-registration s15c: morphological walking cells in the point network (a hybrid) (21 October, 01:38; before any morphological cell is scored or embedded)
DIAGNOSTIC, forced drive. Nothing is adopted. Director's brief (21 Oct): the next clean fidelity step after s15b, toward "the minimum for functional behaviour". This is FIDELITY_LADDER rung 6 (compartments with synapses placed by position) for the walking circuit only.
- **Question:** is the point reduction what breaks the core → MN hand-off? Test it by replacing the 106 T1 walking cells with passive cables built from their own EM skeletons, with synapses at their EM positions and the spike zone at the axon initial segment. Nothing else in the network changes.
- **What already bounds the answer:**
  - S4b swept a uniform leg-MN input scale over 1-25 and found no alternation at any scale (F-BYPASS-7). To first order, a passive morphology rescales each input by a position-dependent gain. So it can only help by changing the inputs' *relative* weights, for example if I1's and the other inhibitory premotor synapses sit nearer the spike zone than the tonic excitation.
  - Pugliese's point LIF alternates on MANC, so point reduction isn't necessary for alternation in a model. What the morphology replaces is our un-measured point gain. It puts physical quantities in its place: area, Rm, Cm, Ri and the synapse positions.
- **Cells:** the 106 T1 cells of `premotor_mn_geometry.py`: 94 leg MNs (LEG_TYPES) and the 12 core cells (E1, E2, I1, IN19A007/004/002), both sides. They are male-cns v1.0 healed skeletons, already saved in `data/derived/premotor_mn_geometry_skel/`. The input synapses with their partners and positions come from `walking_morph_fetch.py` → `data/derived/walking_morph/syn_in.parquet`, kept as raw data. T2/T3 cells stay point cells, which I'll state in every result.
- **Solver:** a small custom implicit solver, `src/flyemu/morph.py`, the CPU reference path.
  - **How it works:** one compartment per skeleton node, node-centred frustum areas, a soma sphere of the root radius, and axial conductance π r1 r2/(Ri dl). The block-diagonal passive matrix is constant, so it is factorised once (scipy splu, Hines-equivalent on trees) and each 0.1 ms step is one solve. Measured: 434,567 nodes, 0.15 s to factorise, 9.4 ms per step on the Mac.
  - **Why not NEURON or Arbor in production:** the cells must step inside `lif.Network` at its 0.1 ms step, with its current synapses, delays, noise and spike exchange. NEURON or Arbor would need a Python round trip and event translation every step, and neither can host the rest of the network. Arbor's step coupling is the harder of the two.
  - **NEURON's role (`neuron` 9.0.2 from pip):** the independent check of the cable maths (gate 1a), not the production path.
  - The custom path keeps one code route open for a later GPU port of batched triangular solves, per the CPU-first rule.
- **Membrane (shared, not fitted):**
  - **Cm 1.0 µF/cm²** is the standard value.
  - **Rm = the cell's point τ_m / Cm**, which is 20 kΩ·cm² at τ_m 20 ms (derived). It is checked against the fitted insect range in `docs/research/s15c_cable_params.md` (Sonnet scan, running).
  - **Ri is 200 Ω·cm, bracket 102-311** (Gouwens & Wilson 2009, fitted there, as s15).
  - **Radii:** traced. Radii ≤ 0.05 µm take the neighbours' mean (none in these 106 cells). There is no shrinkage correction; a ×0.8 and ×1.25 radius scaling is reported as sensitivity.
  - **E_leak** is the cell's point v_rest.
- **The isopotential-limit rule (design):** every point-cell mechanism is placed so that, as Ri → 0, the morphological cell *is* the point cell.
  - Each synapse's current is the point edge weight × the point synaptic kernel / Rin_iso (Rin_iso = Rm / area), split equally over that edge's EM sites. The total charge is the point model's.
  - Noise and any whole-cell intrinsic current are spread in proportion to area.
  - An edge with no EM site found is spread over the cell's input-site distribution; I'll report the weight share this affects.
  - Graded inputs, gap junctions, receptor/slow copies and conductance synapses onto these cells are refused, as in N30. If any is present in m10f0 the arm stops and I record which.
- **Spike zone (operational):**
  - **Leg MN:** the motor axon is the soma → leaf path with the longest synapse-free terminal run, which is the nerve exit. The arbor exit is the last node on that path with an input synapse on or distal to it. The spike zone is the AIS segment starting there. Its length and offset come from the scan (Ravenscroft 2020, the para distal AIS-like domain). Default if the scan finds none: 0-20 µm distal to the arbor exit (guessed).
  - **Core:** the s15b split node, with the same segment length distal along the largest-cable child. A sensitivity alternative is the centroid of the cell's neuPrint "linker" synapses, where there are ≥ 5. For leg MNs the alternative is the s15b split.
  - **Spike rule:** the cell's point threshold is read at the segment's middle node. On a spike, the segment's nodes are set to v_reset and held there for the point t_ref. The spike is the cell's output spike. The arbor and soma are not reset; a spike is local, and Azevedo 2020 reports small somatic spikes.
  - So, unlike the passive limit, the f-I curve differs from the point cell. It is reported, not gated.
- **Gate 1 (single cell, before any network run; all must pass):**
  - (a) **Solver vs NEURON:** for 6 cells (2 core, 4 leg MN), the somatic Rin and the soma and spike-zone PSP peaks for 10 random input sites each agree within 2%, at dt 0.1 with backward Euler on both.
  - (b) **Isopotential limit:** at Ri 10⁻³ Ω·cm with spikes off, the soma trace of a 1 s synaptic drive equals the point cell's within 0.05 mV.
  - (c) **Rin check (measured, never fitted):** the model somatic Rin of the T1 tibia flexor MNs (Ti flexor MN and Acc. ti flexor MN) has its median inside Azevedo 2020 Fig. 3E's class means (150-700 MΩ). Its cells' q10-q90 must overlap that range. If (c) fails at the registered values, the build doesn't go into the network; Rm is not tuned. Measured already on the build (01:36, Rm 20 kΩ·cm², Ri 200): Ti flexor MN somatic Rin median 527 MΩ (253-832, n 10). The full gate is still to run.
- **Gate 2 (unitary, the hand-off):** the s4b probe on the hybrid. Soma per synapse and q90 per spike must sit inside the 01:22 band. Reported, not gated: the spike-zone PSP per E1/E2 spike onto leg MNs and onto I1, against the 7 mV gap; and the spread of spike-zone gain across inputs (position-dependence), split by sign. **Stop rule:** if the spike-zone gain is ≤ 2× for the core → MN and E2 → I1 edges *and* the inhibitory/excitatory gain ratio is within 0.8-1.25, the hybrid is a re-weighting S4b already covered. Gate 3 still runs, as the Director asked, but the falsifier is then the expected outcome.
- **Gate 3 (network): arms H0 (point, re-run), HM (leg MNs morphological), HP (core), HPM (both).** DNg100 15/25/40 mV, seed 12, the s14 harnesses (S2 + chain), on backhouse under rule 16. The switch is `cell_type:all|morphological_walking_cells` (neutral 0, CPU only, GPU refuses). **Pass** exactly as s14: `s4b_score.rhythm` → rhythm_pass, then viewing, with the passing pair written down before viewing. 9 tries; a pass needs seeds 13 and 14 first. Secondary: transfer-pass pools, I1 recruitment, E1/E2 spikes per cycle, leg-MN rates. The Ri, radius and spike-zone-site alternatives are sensitivity runs and never count as a pass.
- **Held-out:** the S4b recruitment order (slow → intermediate → fast; measured, unspent) is spent once, only on a passing arm at its passing drive, after the seed repeats. The Rin check (c) uses Azevedo's Rin as a check for the first time; s15/s15b used it as an input to ρ, not as a target.
- **Falsifier:** no pass in 9 tries means a passive EM morphology with an AIS spike zone, at the point model's synaptic charge and threshold, doesn't restore alternation. Then point reduction isn't the break. The remaining suspects are the per-synapse strength itself (Ben's measurement list: a unitary PSP from E1/E2 onto a front-leg MN) and the missing mechanisms (I1's mode, proprioceptive feedback in S4 proper).
- **Prediction (mine):** gate 1(c) passes, since the build already gives 527 MΩ. The spike-zone gain is 1-2× with a modest position spread. No arm passes. HM raises the transfer-pass pools a little, because the AIS-only reset lets the arbor's depolarisation carry over to the next spike.

### s15c addendum: values from the scan (21 October, 01:38; before any gate-1 run; `docs/research/s15c_cable_params.md`)
- **Rm check:** Günay et al. 2015 (PLoS Comput Biol, Table 2; larval aCC/RP2 MNs, n 5, fitted) give Cm 0.77 µF/cm², Ri 212 Ω·cm and g_leak 38 µS/cm², i.e. Rm 26.3 kΩ·cm². Their τ = Rm·Cm is 20.2 ms, the same as our point τ_m, so the registered Rm 20 kΩ·cm² at Cm 1.0 sits inside the fitted insect values. Rin scales with Rm, so Günay's pair gives Rin ×1.31, run as a sensitivity corner. Gouwens & Wilson 2009's numbers couldn't be fetched from the primary source; they stay as cited in s15 (Ri bracket only).
- **Spike-zone site (the rule as registered, "offset and length from the scan"):**
  - **Offset:** 70 µm distal to the arbor exit. Günay 2015 derived it from their model, 70 µm past the most distal dendritic branch point in larval MNs (inferred, another stage).
  - **Length:** 20 µm (guessed; no SIZ length found). If the traced axon past the arbor exit is shorter than 90 µm, the segment is its last 20 µm before the exit leaf, which I'll report.
  - **Sensitivity alternative:** offset 0. Core: as registered (s15b split + 20 µm).
- **Azevedo 2020:** rest −68/−60/−48 mV (fast/intermediate/slow). No τ, Cm or threshold is given. Rin 150/300/700 MΩ, as used.
- **Precedent:** no adult EM-based multi-compartment VNC model was found.

### Results s15b arms (21 October, 02:03; F-S15-2; nothing adopted)
24 runs (M0/TM/TP/TPM × 15/25/40 mV × S2 + chain) finished on backhouse at 01:59; scored with `s14_score.py` unchanged (`runs/s15/arms/score.json`), then viewed: `docs/media/s15b_arms_rasters_{15,25,40}mv.png`, `s15b_arms_frames_all.png`, `s15b_arms_chain_T1L_40mv.png`.
- **0/12 S2 tries pass.** No arm has a transfer-pass pair or an antagonist pair at any drive (TP and TPM at 25 mV: 1 transfer-pass pool each, no pair). M0 fails, as required. No pair was written down before viewing, because none passed. The 01:16 falsifier is hit for TM, TP and TPM.
- **Viewing agrees.** TP looks like M0: the tonic tibia-flexor line plus sparse co-active flecks. TM and TPM lose the tonic line entirely and keep only sparse, drive-locked, co-active flecks (lh at ~12 Hz). Nothing alternates in any leg. Frames: the thorax is on the floor with the legs splayed in all 12 runs; the wing raises at 25/40 mV are in M0 too.
- **TM/TPM silence the leg MNs, and the cause is not the hand-off.** Leg-MN rate before drive falls from 3.77 Hz (M0) to 0, and during drive from 4.4-5.4 to 0.06-1.35 Hz. The fitted `spontaneous_drive` (35.55 mV for the slow tibia flexors; it "stands in for tonic premotor excitation", cell_types.csv) is applied to the soma compartment, and at q 0.725, ρ 1.38 the spike zone sees 0.24× a soma DC input (derived: soma 1/(1 + κs(1 − κa/(1+κa))) = 0.367, spike zone κa/(1+κa) = 0.656 of that). 8.5 mV is below the 26.2 mV gap. So TM changed two things: the synaptic hand-off (×1.05, gate) and the tonic drive at the spike zone (×0.24). The registration didn't place `spontaneous_drive`; this is a confound in the arm design, recorded here, not a re-run. It doesn't change the reading, because TP (hand-off-only for the core) also fails, and TM with the tonic line gone shows no alternation either.
- **Core (chain, T1L):** TP and TPM at 40 mV turn E1/E2's ~20 Hz single spikes (M0) into ~3-spike bursts at 5.8 Hz with deeper troughs. M0 already does this in T2 at 40 mV, so it is not new. I1 is recruited only in T2R at 40 mV (TP 5.7 Hz, TPM 4.3 Hz), never in T1.
- **Reading:** a soma–arbor split at the derived class values doesn't fix the hand-off (gain ~1, as the gate and the 01:25 prediction said). My prediction ("no pass, little change from M0") held for TP; TM's large change is the soma-placed tonic drive.
- **Carried into s15c:** the hybrid spreads whole-cell currents over the membrane by area (01:38). That must include `spontaneous_drive`; with uniform current density on a uniform passive membrane the steady state is uniform, so the spike zone sees the point cell's full tonic drive. I'll check it in gate 1(b) by running the isopotential test with the cell's spontaneous drive on.

### s15c: the leg-MN spike-zone rule finds no motor axon (21 October, 02:10; before any gate-1 output)
- **What I found building the locator** (`morph.spike_zone`; `runs/s15/morph/axon_search.csv`): the male-CNS v1.0 skeletons of the 94 T1 leg MNs end inside LegNp(T1). Every input synapse is in that ROI, no skeleton node is more than 94 µm from an input site (median 38), and the 99th-percentile radius is ~0.9 µm (no thick nerve axon). The longest synapse-free terminal run is median 40 µm (10.6-175). 89/94 cells take the registered fallback (run < 90 µm), and for 13/94 the "exit" is the soma itself (the longest run is a twig off the soma). So the rule doesn't identify a motor axon; the nerve part isn't in these skeletons.
- **The core rule works:** the s15b split node is reproduced exactly (e.g. 109.7 µm, as the CSV), and the segment is the next 20 µm along the largest-cable child.
- **For gate 1 this doesn't matter:** (a) checks the cable maths at whatever node the locator returns, and (b) and (c) don't use the spike zone. The spike-zone Rin in (c) is reported, not gated.
- **Before gate 2, a choice is needed** and will be written down here before any gate-2 output. The registered sensitivity alternative for leg MNs (the s15b split + 20 µm, the arbor base on the soma side) is one option. Another is the trunk end: follow the thickest child from the soma, and take the last 20 µm before the leaf where the main trunk leaves the arbor. The skeleton can't settle which is right. The measurement that would is the site of spike initiation in an adult leg MN (Ben's list).
- **Point mechanisms on these cells at m10f0** (`runs/s15/morph/point_params.json`): no graded cells, no noise, no gap junctions, current synapses, τ_s 5 ms, v_rest −52 mV, τ_m 16-20 ms, **intrinsic channels ON** (the slow flexors' rung-1 channels; spont 35.55 mV). The hybrid has to spread or refuse those channels in step 4; the registration says whole-cell intrinsic currents are spread by area.

### Results s15c gate 1: all three parts pass (21 October, 02:12; F-S15-3; nothing adopted, nothing in the network yet)
`scripts/probes/s15c_gate1.py {a,b,c}` → `runs/s15/morph/gate1_{a,b,c}.json`. The point parameters come from `s15c_point_params.py` at m10f0. Membrane as registered: Cm 1, Rm = τ_m/Cm (20 kΩ·cm² at τ_m 20 ms, 16 kΩ·cm² for the 21 τ_m-16 slow flexors), Ri 200, E_leak −52 mV.
- **(a) PASS, solver vs NEURON 9.0.2.** I built 6 cells in NEURON (INXXX466, IN16B036, Ti flexor, Acc. ti flexor, Tr extensor and Sternal anterior rotator MNs; 3,193-12,310 nodes). Each skeleton edge is a pt3d frustum section, and the soma is a sphere-area cylinder. Somatic Rin agrees within 2×10⁻⁵ (Impedance at 0 Hz). Soma and spike-zone PSP peaks for 10 random EM sites per cell agree within 3×10⁻⁵, full traces within 8×10⁻⁶ mV, with zero lag. The two codes discretise differently (node-centred vs section-centred), so a residual of order (dx/λ)² is expected; the tolerance was 2%. NEURON stays a check-only dependency, installed into .venv with `uv pip install neuron==9.0.2`.
- **(b) PASS, isopotential limit (all 106 cells, 1 s).** At Ri 10⁻³ Ω·cm with spikes off, each cell got 20 Poisson inputs at 20 Hz (weights ±0.5-3 mV on EM sites, 30% negative) plus its tonic drive spread by area. Max |soma − point| was 0.0065 mV for the 85 cells without tonic drive. For the 21 slow flexors with the 35.55 mV tonic drive it was 0.047 mV (V range 41 mV), under the 0.05 mV bar but with a thin margin. The cause is the integrator, not the cable. Backward Euler's decay per step, 1/(1 + dt/τ), versus the point model's exponential Euler, e^(−dt/τ), gives a max transient difference of S·e⁻¹·(dt/τ)/2 = 0.041 mV for a 35.55 mV step at τ 16 (derived), which matches. If the hybrid needs a tighter limit, the fix is a capacitance matched to exponential Euler, C·(dt/τ)/(e^(dt/τ) − 1), a 0.3% change. Not done now.
- **(c) PASS, Rin (measured check, first use of Azevedo as a target).** Ti flexor + Acc. ti flexor MNs (n 29): somatic Rin median 582 MΩ, q10-q90 369-959. That's inside 150-700, and the spread overlaps it. Sensitivity (median): Ri 102 → 541, Ri 311 → 620, radius ×1.25 → 438, all inside. Two corners fall outside: radius ×0.8 → 774, and Günay's Rm 26.3 kΩ·cm² with Cm 0.77 → 934. So the registered values sit in the middle-to-upper part of the range, and thinner traced radii or Günay's membrane would push the flexors past the slow-MN mean.
- **Also reported:** the core soma is remote from its input zone (somatic Rin 420 MΩ, spike zone 113, isopotential 98). Leg MNs: soma 468, spike zone 539 (mostly the fallback node), isopotential 321.
- **Preview of gate 2 (not a gate result):** in (a), a 1 mV point weight at a random EM site gives 0.11-0.20 mV at the soma and 0.13-0.19 mV at the spike zone. The isopotential point cell gives 0.157 mV (derived for τ_s 5, τ_m 20). So the per-synapse gain at the spike zone looks like about 1 (0.8-1.3×), which points to the gate-2 stop rule. Gate 2 measures it properly on network edges.

### s15c: leg-MN spike-zone site, and gate 2's operational form (21 October, 02:17; Director's decision; before any gate-2 output)
- **Spike zone, leg MNs (Director, 21 Oct):** primary is the **arbor base**, the s15b split node + 20 µm along the largest-cable child. That is the same rule as the core, and it is defined in every cell. The **trunk end** is the sensitivity run: from the soma, follow the child with the largest radius (ties go to the larger subtree cable) down to a leaf; the segment is the last 20 µm before that leaf, and the threshold node is its middle. Both are guessed sites: the skeletons have no motor axon (02:10). The registered "motor axon + 70 µm" rule is dropped for leg MNs because it isn't defined on these skeletons. The site of spike initiation in an adult leg MN goes on Ben's measurement list (`docs/MEASUREMENT_LIST.md` item 2).
- **Gate 2, operational form.** The cells are passive and linear, and the synapses onto them are current synapses (point_params.json: no conductance synapses, graded inputs, gap junctions or noise). So the s4b network probe's kicked-minus-control difference equals the single-cell response at rest, and I compute it with the cable solver instead of the hybrid network. For each cell I inject a unit exponential current (τ_s of the cell) at the recording node, which is the soma or the spike-zone middle node. By reciprocity (A⁻¹(CA⁻¹)ᵏ is symmetric, so this is exact in discrete time too) that gives every input site's transfer to the recording node in one run per node. Each network edge onto the 106 cells (m10f0, min_synapses 5, final `lif.Network.w` in mV) gets current w × G_total, split equally over its EM sites (`syn_in.parquet`, nearest skeleton node). An edge with no EM site is spread over all of the cell's input sites, and I report its weight share. The isopotential reference is the same edge in a one-compartment cell with the same integrator (backward Euler, dt 0.1, τ_m, τ_s). The slow flexors' rung-1 channels are off, so the gain is the cable's alone, a caveat for those 21 cells. The window is 60 ms.
- **Quantities, as registered on 01:38 and made exact here:**
  - **Spike-zone gain of an edge:** its peak PSP per spike at the spike zone ÷ its isopotential peak. A group's gain is the |w|-weighted mean over its edges; I also report the median and q90.
  - **Admissibility (01:22 band, somatic):** excitatory edges (w > 0, presynaptic cell not a leg MN) onto leg MNs, and separately onto core cells, must have a median somatic PSP per synapse ≤ 0.3 mV and a q90 somatic PSP per spike of 0.4-10 mV.
  - **Stop rule:** it applies if the spike-zone gain is ≤ 2 for both groups, core → leg-MN edges (presynaptic cell one of the 12 T1 core cells) and E2 → I1 (INXXX466 → IN16B036), **and** the inhibitory/excitatory gain ratio (the |w|-weighted means of w < 0 and w > 0 edges) is within 0.8-1.25 for the inputs onto leg MNs and onto core cells. It is judged at the primary site; the trunk end and the Ri/radius corners are reported only.
- **Director's instruction for the stop rule (21 Oct):** if it applies, step back. Gate 3 and the hybrid network (s15c steps 3-4) are not built, and the morphology path is parked. That replaces the 01:38 line "Gate 3 still runs". The next arm is the neuromodulatory state (to be pre-registered after this result).

### Results s15c gate 2: admissible, and the stop rule applies; the morphology path is parked (21 October, 02:20; F-S15-4; nothing adopted)
`scripts/probes/s15c_gate2.py` → `runs/s15/morph/gate2.json` and `gate2.edges.csv.gz` (gitignored). 11,417 network edges onto the 106 cells (m10f0, min_synapses 5, none zero). Every edge has EM sites (no-site weight share 0). Runtime 58 s on the Mac. The operational form is as written at 02:17. The cable solver's reciprocity was checked on two cells before the run: forward and reverse transfer agree to 10⁻¹⁰.
- **Admissible (01:22 band):** excitatory inputs onto leg MNs (n 5,762) give a somatic median of 0.021 mV per synapse and a q90 of 1.03 mV per spike. Onto core cells (n 1,152), 0.021 mV and 1.44 mV. Both pass.
- **Spike-zone gain at the primary site (arbor base), |w|-weighted means:**
  - core → leg MN 1.015 (n 80, q10-q90 0.96-1.08, max 1.17);
  - E2 → I1 0.974 (n 2);
  - all excitatory onto leg MNs 1.016, inhibitory 1.012;
  - core-cell inputs 1.013 / 1.002.
  The inhibitory/excitatory ratio is 0.997 (leg MN) and 0.990 (core). **The stop rule applies**, by a wide margin: the gain is ≤ 2 for both edge groups, and both ratios sit inside 0.8-1.25.
- **Sensitivity (reported, not judged):**
  - **Trunk end:** core → MN 0.911, ratio 0.984.
  - **Soma:** gain 0.77-0.90.
  - **Ri 102 / 311 and radius ×0.8 / ×1.25:** every group gain is 0.96-1.03, and every ratio 0.99-1.00.
  - **Position dependence:** across edges, q10-q90 is 0.94-1.10 at leg MNs and 0.80-1.19 at core cells. Position barely matters at these membrane values.
- **Against the 7 mV gap:** E2 → I1 gives 1.07 mV and 0.75 mV per spike at the spike zone (38 and 27 synapses, the two sides). E1/E2 → leg MN gives a median of 0.44 mV per spike (n 38, max 3.4).
- **Reading:** a passive EM morphology at the point model's synaptic charge gives the same hand-off as the point cell, to within a few percent, for every input sign, spike-zone site and cable corner. It can't change the inputs' relative weights, which was its only way to help (01:38). So the point reduction is not the break.
  - The s15 → s15c series rules out the cell's shape. s14 and S4b rule out a uniform transmission strength (F-S14-1, F-BYPASS-7). Neither is the single cause.
  - My 01:38 prediction (gain 1-2×, "a modest position spread") held at its low end; the spread was smaller than I expected.
- **Decision (Director's instruction, 02:17):** gate 3 doesn't run. The `lif.Network` hybrid (steps 3-4) isn't built. The morphology path is parked with its tools kept: `morph.py`, gate 1 and gate 2 are the CPU reference if a later arm needs active dendrites or measured synapse-specific sites. The held-out S4b recruitment order is still unspent. Next: pre-register the neuromodulatory-state arm (octopamine).

### Pre-registration s16: an aroused, octopamine-high state at class grain (21 October, 02:28; before any state row is written or any arm runs; to run next session)
DIAGNOSTIC, forced drive. Nothing is adopted. Director's brief (21 Oct): shape (F-S15-4) and uniform transmission strength (F-S14-1, F-BYPASS-7) are ruled out as the single cause. The next biologically motivated arm is the neuromodulatory state. Walking flies are aroused and octopamine (OA)-high. Brain-off flies walk when OA is applied to the cut neck (Yellman et al. 1997 PNAS, full text; that paper used OA itself, not chlordimeform or naphazoline). Feeding OA, or Tdc2 neuron activation, raises walking speed (Schretter et al. 2018). This arm is also part of Ben's mechanism-complete scope.
- **What the literature gives (Sonnet search, `docs/research/s16_octopamine_excitability.{csv,md}`, 26 rows):**
  - **No measured OA magnitude exists for adult VNC leg MNs or premotor interneurons.** Every motor-circuit result is from locust, stick insect or larva, and almost all are qualitative.
  - **At the MN, the one direct measurement is a null.** In larval RP2 MNs, OA (1-10 µM) had no effect on the response to current injection (Schützler et al. 2019 PNAS, full text). Tyramine lowered the rate and left Rin and threshold unchanged.
  - **The premotor direction is excitatory.** In the stick insect, OA raises the tonic leg-MN depolarisation during fictive walking and mianserin lowers it, and the action is attributed to premotor neurons (abstract-level via a secondary quote; flagged). In the locust, OA induces bursting in flight premotor interneurons and raises their responses (Ramirez & Pearson 1991, abstract).
  - **At sensory synapses, the effect is mixed or depressing.** The locust fSR → BA1 EPSP falls at 10⁻⁴ M (abstract). The stick-insect FT resistance reflex is present at 3.5-12 min and abolished at 15-20 min (Büschges et al. 1993, abstract).
  - **Receptors:** Octβ1-3R are Gs (HEK293, EC50 ~0.03 µM). OAMB is Gq. Octα2R is Gi, and knocking it down with D42-GAL4 (MN driver) impairs climbing (El-Kholy et al. 2022, full text).
  - So the brief's premise "OA raises MN and premotor excitability" holds as a measured direction (other species) only for premotor neurons, and is contradicted at the larval MN. The brief also asked for the arm to come from "the measured effects in s13_neuromodulation_effects.csv". Those rows hold receptor couplings and visual neurons only, with no VNC magnitude. The Sonnet row check of that file is running, and its result will be added here.
- **Which classes carry the state (receptor expression, measured mRNA):** Allen et al. 2020 VNC atlas per hemilineage (`data/derived/receptor_calls_allen2020_vnc.csv`). Octβ2R is expressed in 16-47% of each hemilineage's cells and Octβ3R in 19-50%.
  - **Called (≥ 0.30 for Octβ2R or Octβ3R, the project's call threshold), 18 classes:** vnc_local_ 00A, 01A, 01B, 05B, 06A, 06B, 08B, 09A, 09B, 10B, 11B, 13A, 14A, 16B (I1), 19A (IN19A007), 20A.22A, 21A, 23B.
  - **Measured, not called, 4 classes, left out:** 04B, 08A, 12B, 13B.
  - **Not in the atlas, 15 classes, included and labelled inferred** (every measured hemilineage expresses Octβ2R): 02A, 03A, 03B, 04A, 07B, 11A, 12A, 14B, 17A (E1), 17B, 18B, 19B, 26X, 27X, TBD (E2).
  - **Leg MNs (MN_leg):** hemilineage 15B, Octβ3R 0.50 and Octβ2R 0.34, so the receptors are present. But the only measurement found is a functional null (larval RP2).
- **Mechanism: no new code.** I use the existing class keys `class:<c>|tonic_drive` (N3, mV, neutral 0). The state is a sustained depolarisation of the premotor classes, which is the stick-insect direction and the Gs/cAMP → K⁺-closure reading of Octβ (inferred). The rows go in `data/params/octopamine_state.csv` (class, value, label, source), expanded to `--set` overrides by the run script. No row is written before this entry. Every value is **guessed in magnitude, inferred in direction**.
  - **Adaptation and f-I gain stay neutral**, because no OA number exists for them in any motor cell found.
  - **Sensory release stays neutral**, because the evidence is mixed, and the proprioceptive loop isn't in the S2/chain harnesses.
- **Arms** (m10f0 otherwise; DNg100 at 15/25/40 mV; seed 12; the s14 harnesses S2 + chain; backhouse under rules 16/17; done-files):
  - **M0:** re-run.
  - **OA2:** +2 mV on the 33 premotor classes.
  - **OA4:** +4 mV on the 33 premotor classes.
  - **OA4M:** OA4 plus +4 mV on MN_leg, the brief's MN assumption, run against the larval null.
  - **Bound (the per-value bar applied to the resulting quantity):** the shifted rest must stay inside the measured central-neuron range (−70 to −45 mV, parameters.csv n2_v_rest), with a threshold gap ≥ 2 mV (n2c_vth). At m10f0 (rest −52, threshold −45), +4 leaves a 3 mV gap and +6 would breach it, so +4 is the top of the sweep. Cells whose own rest or threshold differs are checked one by one at build time, and the arm stops if any cell breaches the bound.
- **Pass, exactly as s14/s15b:** `s4b_score.rhythm` → rhythm_pass, then viewing, with the passing pair written down before viewing. 9 tries (3 arms × 3 drives, M0 not counted). A pass needs seeds 13 and 14 first.
- **Secondary (reported, never a pass):**
  - I1 (IN16B036) recruitment per side. Gate 2 left E2 → I1 at 0.75-1.07 mV per spike against a 7 mV gap; +4 mV narrows that gap to 3.
  - E1/E2 spikes per cycle, transfer-pass pools, leg-MN rates before and during drive.
  - A **brain-off, no-drive run** (0 mV, S2 only, each arm): any rhythm without DN drive is the model's analogue of the decapitated-fly result. It is qualitative, and the comparison is spent here once.
- **Held-out:** the S4b recruitment order (unspent), spent only on a passing arm at its passing drive, after the seed repeats.
- **Falsifier:** no pass in 9 tries means a sustained class-level premotor depolarisation of the size the threshold bound allows, the only OA effect with a measured direction in motor circuits, doesn't restore alternation. The state then isn't the single missing piece either. The remaining suspects are I1's mode (graded or spiking), proprioceptive feedback (S4 proper) and the per-synapse strength, all on Ben's list.
- **Prediction (mine):** no pass. OA4 recruits I1 in some legs and raises the co-active flecks and the tonic MN rate. OA4M brings back the M0 tonic tibia-flexor line, stronger. The brain-off run is silent at OA2 and gives sparse tonic firing at OA4.
- **Measurement for Ben's list:** the OA effect on adult VNC premotor and leg-MN rest, Rin and f-I. It would come from a whole-cell recording, as in Azevedo 2020, before and after bath OA (10 µM) or Tdc2 activation (`docs/MEASUREMENT_LIST.md` item 3).

### s16 addendum: the s13 neuromodulation table checked row by row (21 October, 02:31; before any s16 row is written)
Sonnet check, `docs/research/s16_neuromod_rowcheck.csv` (63 rows): **32 CONFIRMED, 20 CORRECTED, 6 WRONG, 5 UNVERIFIABLE.** `s13_neuromodulation_effects.csv` is left unchanged as raw. Use it only through the row check.
- **OA rows:**
  - s13_011 (Octβ1R EC50 ~0.03 µM, Balfanz 2005) and s13_014-018 are confirmed.
  - **s13_012 is WRONG.** "Octβ1-3R all raise cAMP" comes from Maqueira, Chatwin & Evans 2005 (J Neurochem 94:547, CHO cells), not Balfanz 2005. The finding stands; the citation is fixed.
  - s13_013 and s13_060 are corrected: Balfanz's three receptors are Octα1R-a/b and Octβ1R.
  - **s13_062 is WRONG:** Drosophila has six OA receptors, not four.
- **Elsewhere:** reviews are labelled "measured" where they should be "measured (secondary)". The 5-HT gain-control rows s13_028/029 are misattributed (they come from Suzuki et al. 2020 Curr Biol). s13_007/061 carry a quote that doesn't appear in the cited paper.
- **Effect on s16: none.** The arm takes its direction from `s16_octopamine_excitability` and its classes from the Allen 2020 calls. The Gs coupling of Octβ2R/β3R, which underlies the "depolarising" reading (inferred), stands on Maqueira 2005. In the 02:28 entry, read the "Octβ1-3R are Gs (HEK293 ...)" line as Octβ1R from Balfanz 2005 (HEK293) and Octβ2R/β3R from Maqueira 2005 (CHO).

### s16: the state table, the bound's operational form, and the run (21 October, 02:35; before the bound is computed or any arm runs)
- **Table:** `data/params/octopamine_state.csv`, one row per (arm, class): OA2 and OA4 on the 33 classes of the 02:28 entry, OA4M the same plus `MN_leg`. Every value is labelled magnitude guessed, direction inferred (MN_leg: direction guessed, against the larval null). Class inclusion is labelled measured (the 18 Allen calls, with their Octβ2R/β3R fractions) or inferred (the 15 not in the atlas). `scripts/probes/s16_oa.py sets <arm>` expands the table to `--set class:<c>|tonic_drive=<v>`.
- **The bound, operational form** (`s16_oa.py check <arm>`, on the built network, per cell, every cell whose class carries a nonzero value):
  1. **As registered:** the cell's own rest parameter plus the shift, `v_rest + Δ`, stays at or below −45 mV and at least 2 mV below the cell's own threshold (`v_th`, after any class threshold offset).
  2. **Including the fitted spontaneous drive** (stricter, added here): the cell's steady state without synaptic input is `v_leak + spont`. For cells below threshold at baseline, the shifted steady state must also stay at or below −45 mV with a 2 mV gap. A cell already within 2 mV at baseline counts as a breach too, because the shift pushes it over. Cells already above threshold at baseline (fitted tonic firers, e.g. the slow tibia flexors at 35.55 mV) aren't moved across by the shift; they are counted and reported, not a breach.
  3. **Every key is consumed:** each `--set` key must appear in the run's registry; a key that names no class fails the check.
  - **Any breach of 1-3 stops that arm** (it isn't run), as registered. The check runs on backhouse before the arm's runs.
- **Run:** `runs/s16/oa/run.sh`, a copy of the s15b runner. M0, OA2, OA4, OA4M × DNg100 15/25/40 mV × {S2, chain}, plus a 0 mV brain-off S2 run per arm. Seed 12, m10f0. Rule 16 caps and load gate, rule 17 detached, done-files per run and `ALL.done`. Scoring: `s14_score.py --arms M0,OA2,OA4,OA4M` unchanged. The 0 mV runs are read by eye and by leg-MN rate only.

### Results s16: the octopamine-state arms (21 October, 03:12; F-S16-1; nothing adopted)
0/9 pass (OA2, OA4, OA4M × 15/25/40 mV); M0 fails as required. The falsifier in the 02:28 entry is hit: a sustained class-level premotor depolarisation, of the size the threshold bound allows, doesn't restore alternation. I1 fires under OA4 in most neuromeres, but the leg-MN pools stay co-active. The brain-off, no-drive comparison is spent: there is no rhythm in any arm. The recruitment order is still unspent. The `tonic_drive` keys stay neutral (0) everywhere; `data/params/octopamine_state.csv` is the record of the arm, not an adopted state. Scripts: `scripts/probes/s16_oa.py`. Runs: `runs/s16/oa/` (Mac copy; backhouse `~/fly-m10f/runs/s16/oa/`).

### Pre-registration s17: S4 proper, the closed proprioceptive loop, under M0 and the OA4 state (21 October, 03:18; before any harness change or run)
DIAGNOSTIC, forced drive. Nothing is adopted. Director's brief (21 Oct, after F-S16-1): three single-cause families remain, and this tests the only one that needs no measurement from Ben. Does leg proprioceptive feedback, with the loop closed through the tethered body and the connectome, make antagonist leg-MN pools alternate? Insect antagonist switching depends on position and load feedback (Büschges's stick-insect and locust work, cited in DECISIONS 13 Oct as needing a range). The loop is run with the OA4 state on, because it is the first state where I1 fires (F-S16-1), and with M0 as the state control.
- **Harness:** `bypass_s2_descending.py` (the s14/s16 S2 harness), with one new switch, neutral by default. `--proprio` adds the leg proprioceptor drive computed from the body every step (`sensory.Afferents.drive(body.observe())`, exactly as fly2's `proprio_reach.py`). It goes into the same `external_mv` as the DN drive. Without `--proprio` the script is unchanged. m10f0, seed 12, brain off, thorax tethered 1 mm above standing (legs in air), DNg100 15/25/40 mV during 300-1300 of 1500 ms. Backhouse, rule 16 caps and load gate, rule 17 detached, a done-file per run and `ALL.done`.
- **Afferent set (from F-REFLEX-2):** the leg proprioceptor rows of `sensory.Afferents`, on all six legs: femoral chordotonal claw, hook (flexion, extension) and club, the campaniform sensilla (CS, the `load` channel) and the hair plates. The bristle (`contact`) rows, eyes, chemosenses and organs are not driven, as in F-REFLEX-2. Every leg afferent must be inside the brain-off VNC set (asserted).
- **Afferent gain (`afferent:all|rate_gain`, guessed), F-REFLEX-2's two values:**
  - **g8:** the profile's 8 mV. Hook about 16 Hz per cell in F-REFLEX-2's clamp.
  - **g40:** 40 mV. Hook 76-78 Hz, the top of the only measured Drosophila chordotonal spike-rate range (larval lch5 1.5-78.4 Hz, Warren & Göpfert 2024). This is the physiological edge.
  - **Bound:** each run reports its afferent rate per subtype during drive. A pass at a run whose chordotonal rates (claw, hook, club) average above 78.4 Hz is void. CS rates are reported only; F-REFLEX-2 found the CS channel saturated in air (0.94), so load is not tested.
- **Delay band (inferred):** 1.5-3 ms from body state to afferent drive (a FIFO of whole drive vectors, `--proprio-delay-ms`). Sources: locust FeCO afferent → flexor tibiae MN central latency about 1.5 ms (Burrows 1987, J Neurosci 7:1064); Drosophila femur bristle afferent spike → VNC EPSP about 3 ms (Tuthill & Wilson 2016, Cell 164:1046), F-REFLEX-2's value. Both edges are run. The model's own synaptic integration adds to this; the loop period at 7-16 Hz is 60-140 ms, so the band is a few percent of a cycle.
- **Drive:** DNg100 15/25/40 mV, as s14-s16.
- **Arms (tries):** {M0, OA4} × {g8, g40} × {d3, d1.5} × 15/25/40 mV = **24 tries**. OA4 is `s16_oa.py sets OA4` (bound already checked in s16: 0 breaches, smallest gap 3.0 mV; feedback adds input, not a parameter shift). Names: `M0g8d3`, `M0g40d3`, `OA4g8d3`, `OA4g40d3`, and the same with `d1p5`. Launch order: d3 first (25, 15, 40 mV), then the controls, then d1.5.
- **Controls:**
  - **Open loop:** the s16 M0 and OA4 S2 runs (same seed, harness and drives) are the no-feedback references; they failed. In this batch, M0 25 mV is re-run without `--proprio` on the edited script, and it must match `runs/s16/oa/s2/s2_M0_25mv.json` exactly (rates, MN count, pools). If not, the harness change broke something and the batch is void.
  - **Feedback without drive:** M0g40d3 and OA4g40d3 at 0 mV. Any rhythm here is a model property, read by eye and by leg-MN rate. It is not compared with the decapitated-fly result again (spent in s16).
- **Pass, exactly as s14/s16:** `s4b_score.rhythm` → rhythm_pass on the S2 traces, via `s14_score.py` unchanged. Two antagonist pools of one leg each at depth ≥ 0.5 (f0 7-16 Hz, ≥ 2/3 of cycles at the 3-spike floor) and drive-locked (≥ 2× pre-drive, or silent before); out of phase (r ≤ −0.3 at zero lag, or a lagged 10-30 ms peak ≥ 0.5); summed leg-MN rate over 1300-1500 ms ≤ 1.5× pre-drive. Before viewing I write down the passing pair. On the raster the two pools must visibly alternate over most cycles, or the pass is void. A pass needs seeds 13 and 14 first, before any claim.
  - **Drive-off rule under feedback:** feedback can sustain activity after drive-off. That fails the stop rule, as registered; it is not waived here. A self-sustained rhythm would be reported as a separate observation.
- **Secondary (reported, never a pass):** afferent rates per subtype; rate and activity count of first-order targets (≥ 20 synapses from leg proprioceptor rows); premotor rate; leg-MN rates before and during drive; joint-angle SD; per-cell rates of E1/E2/I1/IN19A007 with neuromere and side. The chain harness has no body, so it is not run.
- **Held-out:** the S4b recruitment order stays unspent. It is spent only on a passing arm at its passing drive, after the seed repeats. No sealed data is used.
- **Falsifier:** no pass in 24 tries means leg proprioceptive feedback, closed through the tethered body and the connectome, at afferent rates up to the top of the measured chordotonal range and across the inferred delay band, doesn't restore alternation, with or without the state where I1 fires. Proprioception is then not the single missing piece either, and the two left are connection-specific strength (measurement list item 4) and a premotor driver outside the 106-cell core (a connectome query, queued).
- **Prediction (mine):** no pass. At g8 the loop stops at the first hop (F-REFLEX-2), so the MN layer matches open loop to within the noise. At g40 the FeCO recruits mostly inhibitory first-order cells (IN14A, IN09A, IN19A005, IN13A006), which thins extensor output rather than patterning it. OA4g40 gives the most premotor activity and the first measurable change at the MN layer, but co-active, not alternating. The delay edges don't differ. The 0 mV runs are silent apart from the tonic tibia-flexor line.

### Results s17: the closed proprioceptive loop (21 October, 03:56; F-S17-1; nothing adopted)
0/24 pass ({M0, OA4} × {g8, g40} × {d3, d1.5} × DNg100 15/25/40 mV), with no antagonist pair in any run. The open-loop repro equals s16 exactly, so the batch is valid. Every run's chordotonal rate is inside the 78.4 Hz bound (highest subtype 11.8 Hz), so no void rule applied. Feedback without drive (g40, 0 mV) gives no rhythm under M0 or OA4. The falsifier in the 03:18 entry is hit: proprioception is not the single missing piece. The finding states two limits. The loop's afferents stay far below their clamp rates because the legs barely move. The replay half of S4 (imposed walking-like joint trajectories under drive and OA4) was not run. `--proprio` stays a neutral switch (off by default); `afferent:all|rate_gain` stays at the profile's 8. The S4b recruitment order is still unspent. Scored with `s14_score.py` unchanged and `s17_loop_summary.py` (`runs/s17/loop/{score,summary}.json`). Viewed: `docs/media/s17_loop_rasters_{0,15,25,40}mv.png`, `docs/media/s17_loop_frames.png`.
### fly2: how the first fly_brain.zip is built (21 Oct, 00:50)
**Brief.** Director, 21 Oct: build the species-layer zip, its entry point, and the identity test. Spec: `docs/FLY_BRAIN_ZIP.md` rev 2.

**What was decided, and why.**
- **The zip holds the files the code reads, under the spec's names.** Each member has a spec path (`connectome/edges.parquet`) and a runtime path (`data/cache/male_cns_edges.parquet`). The runner extracts each member to its runtime path under a fresh root and runs the code there unchanged. The other route, rewriting every loader to read through a zip layer, touches 20+ modules and could change results.
- **What goes in.**
  - The inclusion policy came from a trace first: `scripts/probes/zip_trace_inputs.py` audit-hooks one m10f0 build and records every file opened.
  - The zip then takes all git-tracked files under `data/params`, `data/derived`, `data/model`, `data/ontology` and `data/measurements`, plus `tests/`. It also takes the external caches the code reads (connectome extract, annotations, CT1 column files, flybody meshes), each hashed.
  - Untracked files are never packed. The packer refuses a dirty tree, and refuses if the neuron or edge hash differs from the `t1_fill.json` pin.
- **flygym 2.1.0 is vendored** (Apache-2.0, pure Python, about 2 MB plus 143 MB of fullsize meshes).
  - The first approach, pointing the installed flygym at the zip's assets, failed: its asset paths are module constants and default arguments bound at import.
  - The read guard caught it as a read of the installed `all_geom_suffixes.yaml`.
  - flygym therefore leaves the runtime pins and is recorded as vendored, with its version and licence.
- **A read guard, not just PYTHONPATH.**
  - The child process installs Python audit hooks and wraps pyarrow's parquet reader and MuJoCo's XML loader. It also checks every compiled mesh path.
  - Reads under `--deny` roots, the installed flygym and its mesh cache are refused. Any other read outside the root and the Python install is listed in `run_manifest.json`.
  - Limit: native reads that bypass these paths would not be seen. The identity result below is the backstop.
- **World.** Only `flat_floor` (the `World()` defaults, as JSON) and the null stimulus are built. The other three arenas and nine stimuli are declared `todo` entries in the manifest, and the runner refuses them by name.
- **Profiles go out as data.** Each profile is exported as JSON (key, value, label, why). In zip mode the runner loads the profile from that JSON, not from `profiles.py`.
- **Determinism.** Members get fixed dates and a sorted order, and the manifest has no clock time. The child runs with `PYTHONHASHSEED=0`, and `FLYEMU_*` environment variables are dropped and recorded.

**Acceptance (registered in the brief before running).** A 1 s m10f0 smoke run (seed 12, ≥ 5 synapses, flat floor) from the zip, in a fresh temp dir with the repo denied, must be spike-for-spike identical to the same run from the repo tree. Falsifier: any difference in the spike arrays, the final body pose or the registry reads. Result: FINDINGS F-ZIP-1.

### fly2: scoreboard protocols as zip world/ data; flyemu.check (21 Oct, 01:10)
**Brief.** Director, 21 Oct: build flyemu.check, then turn the probe arenas and stimuli into zip `world/` data, each tested zip against tree, so the scoreboard runs from the zip alone. The zip is over 50 MB, so it stays a build artifact; the packer is committed.
- **Format.** Source files live in `data/world/` (git-tracked) and are packed as the zip's `world/`.
  - `scoreboard.json` lists the 8 fixed items in order. Each names a protocol or gives the reason there is none.
  - A protocol (`protocols/<name>.json`) holds the brain build, settings, seeds, duration, stimulus name, readout, pass conditions, bar source, reference script and evidence status.
  - A stimulus (`stimuli/<name>.json`) is a list of timed events on cell types.
  - `flyemu.score` only interprets these files. No number lives in its code.
- **Two harnesses, each a copy of the script whose numbers it must reproduce.**
  - `assay` builds the brain as `scripts/assay_pathways.py` does: no stubs, no body, no Q10, and a fresh network per seed.
  - `organism` builds it as `scripts/probes/gf_latency.py` does: Organism, with the body not stepped.
  - Both step only the network. The sugar gate has always been scored by the first and GF latency by the second, so this keeps both comparable with every earlier number.
  - The cost: the two protocols do not share one brain build. Moving to a single harness would mean re-scoring both gates. Not done here.
- **Built:**
  - `per_labellar_sugar`: LB3b/LB3c Poisson drive at 100 Hz, read out on MN9 with incompletely traced cells dropped (which leaves MN9_L). Pass: mean over seeds 0-9 > 5 Hz, the class-search gate.
  - `gf_escape`: DNp01 kicked 20 times; TTMn, PSI and DLMn latency plus conduction delay, against Augustin 2017. Pass: the gf_latency verdict, with gap junctions at the model default of 0.
- **Not built, with the reasons in `scoreboard.json`:**
  - Stands and walks: expressible as data, but both fail for want of mechanisms, and the closed-loop harness is not yet a protocol harness.
  - Grooms: no test and no mechanism.
  - Leg sugar: same harness, but its bar is the four-part check of 6 Oct 00:41, with no single number for "opens". Writing that number is a decision, not plumbing.
  - Optomotor turning and stable flight: these need code. Vision bypasses the World, and flight kinematics are imposed.
- **Evidence status.** Both built protocols score spent evidence: the sugar gate was a fit target, and the Augustin latencies have been scored since s13. Their runs are regression checks, not held-out tests. The register says so.
- **Acceptance (written before the zip runs finished).** For each protocol:
  - The tree run must reproduce its reference script exactly: the per-seed MN9 rate for sugar, and every gf_latency type field for GF.
  - The zip run, from a scratch directory with `/Users/ben/fly-emulation` denied, must give per-seed spike hashes over every neuron equal to the tree run's.
  - flyemu.check from the zip must give the same test outcomes as from the tree, and a rebuilt ledger equal to the packed one.
  - Any difference fails the zip, whatever the verdicts are.
  - GF tree vs reference had already finished (exact match, FAIL) when this was written; the rest had not.

### fly2: a closed-loop protocol harness; stands and walks as zip world/ data with no bar yet (21 Oct, 02:16)

- **Harness `closed_loop`** (`flyemu.score`): the Organism with the body stepped and every sense reaching the brain. Each step is observe, sense, network step (with the stimulus kick) and motor step, the loop of `flyemu.run` and `scripts/probes/command_walk.py`. Body samples every 10 steps (1 ms) after the motor step, as command_walk takes them. Each trial also records the final-pose hash, the NaN state and the MuJoCo warning count.
- **Readouts.**
  - `leg_oscillation` is command_walk.py's per-leg summary over 300-1300 ms: the dominant tarsal-tip fore-aft frequency in 3-25 Hz, the band's power share, the peak-to-peak amplitude, the thorax displacement, and the leg motor neuron and DNg100 rates.
  - `posture` gives the thorax height (median, minimum, last) and its horizontal drift.
- **Protocols.**
  - `walks_dng100`: DNg100 at 100 Hz, 300-1300 ms, seed 0, 1.4 s. Reference: `command_walk.py --type DNg100 --hz 100 --seed 0` at m10f0.
  - `stands_flat_floor`: no stimulus, seed 12, 1 s. Reference: the F-ZIP-1 tree run of `flyemu.run` (same build, seed and loop).
- **No bar, so the verdict is NO BAR.** What counts as standing (a thorax height) or walking (a step-frequency band, how many legs, a forward displacement) is not written down anywhere as a number. Choosing one is a decision for the Director or Ben, not plumbing. Each protocol carries a `bar_todo`, and `flyemu.score` refuses a protocol with neither pass conditions nor a `bar_todo`. Proposals go to the Director in the report and are not adopted. Both items still fail today for want of mechanisms (F-STAND-3 to 6; F-BYPASS-7, F-XCONN-2).
- **Evidence.** Seed 12 is the F-ZIP-1 engineering seed. Seed 0 is exploratory for command_walk. Nothing is scored without a bar.
- **Acceptance (written before any run of these protocols):**
  - Walks: the tree run equals command_walk.py's output on every field it reports, at the script's rounding.
  - Stands: the tree run reproduces the F-ZIP-1 tree run's spike hash (770807852827186b…) and final-pose hash (3ec293bad4b3b7b7…).
  - For both, the zip run (scratch directory, `/Users/ben/fly-emulation` denied) equals the tree run: spike hash, final-pose hash and every readout field.
  - Any difference fails the zip.

### fly2: bars for stands, walks and PER to leg sugar (Director as Ben, 21 Oct; recorded 02:33, before any run with them)
**Brief.** Director, 21 Oct: the three bars below are decided (as Ben, reversible). Each is a definition of the behaviour, not a fit; nothing in the model changes. Pre-registered here before any scored run.
- **Stands (`stands_flat_floor`, seed 12, last 500 ms of 1 s).**
  - Only the feet touch the floor: `nonfoot_floor_frac` ≤ 0, the share of 1-ms samples in 500-1000 ms where the floor pushes (normal force > 0) on any body other than a tarsal segment. "Foot" is any tarsal segment (tarsus1-5), the definition of `bypass_s1_actuation.py`'s `floor_forces` and of the 13 Oct `holds_prereg` (no head, thorax, abdomen, coxa, femur or tibia on the floor). A fly stands on its tarsi, not only on the last tarsomere, so "foot tips" is read as the tarsi.
  - Height inside the measured standing range: `head_above_collapse_mm_median` ≥ 0.1 mm over 500-1000 ms.
    - Wang 2025 (eLife RP107390) tracked a head point, not the thorax, so the bar reads the same point: the `c_head` body origin above this body's motor-silenced collapse, 0.429 mm (derived; S1 level 0, m10f0, adhesion 1, 3 s; `runs/s13/bypass/s1/support/s1_m10f0_adh1.json`). Wang's zero is the collapsed position (inferred, DECISIONS 13 Oct 23:16). A thorax height would need a conversion through an assumed point; Pratt 2024's thorax value was read off a figure from an unspecified point and is not used.
    - Lower bound 0.1 mm: the lowest standing start height in Wang Fig 5C ("varies from 0.4 mm to 0.1 mm in this fly"; measured). No upper bound: the paper gives a median (0.5 mm) but no population maximum, IQR or histogram (Sonnet check 21 Oct, this session), so an upper limit would be invented. The earlier note that 0.86 mm is "inside Wang's measured range" (F-STAND-5) is not supported by a published maximum.
  - Evidence status: Wang's median head height was spent as an instrument setting in s13 (S1 fix 1, `--head-mm`, not the default). This bar defines standing; it is not held-out evidence.
- **Walks (`walks_dng100`, seed 0, 300-1300 ms).**
  - At least 4 of 6 legs step in the walking band: dominant tarsal-tip fore-aft frequency (searched in 3-25 Hz, unchanged) in 7-15 Hz AND `step_band_share` ≥ 0.5, the tip's power share inside 7-15 Hz (Director: "at least half their movement in that band"; this is stricter than the 3-25 Hz `band_share` proposed). Band: Pugliese 2025, as command_walk.py cites.
  - The thorax moves forward: `thorax_forward_mm` > 0, the horizontal displacement over the window along the thorax heading at 300 ms.
  - The stepping comes from the connectome: every closed-loop run (stands too) is refused unless only the network's motor spikes move the body. Checked in the scorer (`_connectome_driven`): no position or velocity servo actuator, no mocap body, no active weld or connect constraint (tether), no wingbeat generator (`flight:wings` 0), no stimulated motor neuron; by construction motor_step gets no external torque and nothing writes qpos or ctrl. No CPG stub or kinematic replay exists in `src/flyemu` (the replays live in `scripts/probes` and are not reachable from the scorer).
- **PER to leg sugar (`per_leg_sugar`, new; seeds 0-9, 1 s, assay harness).** LgLG4 + LgAG2 Poisson drive at 50 Hz; MN9 rate with incompletely traced cells dropped (leaves MN9_L, as the labellar protocol); pass `rate_hz_mean` > 5 Hz. Reference: `scripts/assay_pathways.py --assay legsugar_mn9 --rates 50 --shuffles 0 --trials 10 --profile m10f0`. The other three parts of the 6 Oct 00:41 check (3 Hz silent, leg bitter silent, labellar bitter suppresses) stay as written and are not part of this item. Evidence status: spent (leg sugar at 50 Hz was the target of the s12 margin diagnostics, F-TASTE-LEG-1, F-STAB-6), a regression check.
- **Acceptance (code):** stands and walks with the new readouts reproduce their F-ZIP-3 spike and final-pose hashes and every earlier readout field (reading contacts must not change the run); `per_leg_sugar` tree equals the reference script per trial; zip equals tree for all three.
- **Predictions (written before any run):** stands FAIL on both conditions (the model lies on its belly, F-STAND-3 to 6). Walks FAIL: 0 legs counted (tips at 3-4 Hz, band share 0.1-0.3) and the thorax moves backwards (-0.04 mm). Leg sugar FAIL, MN9_L near 0 Hz (the route is blocked at rest, F-TASTE-LEG-1; not measured at m10f0). The scoreboard stays at 1 of 8 passing, now with 5 of 8 scored.

### fly2: a grooming test spec (proposal to the Director, 21 Oct 02:44; not built, not adopted)
**Grooms, proposed protocol `grooms_antenna_jo`.** *Stimulus:* the antennal Johnston's-organ neurons of the JO-C and JO-E groups (male-CNS types JO-CA1, JO-CA2, JO-CL, JO-CM and JO-ED1, JO-ED2_a-c, JO-EV1-6; 68 + 267 cells, counted in `male_cns_neurons.parquet`), the population whose activation drives antennal grooming in Hampel et al. 2015 (their "aJO" lines; that these lines are JO-C/E is inferred and must be checked against the paper's line names before building). Drive: Poisson kicks at 100 Hz (a protocol choice, as for the sugar drives) during the on-phases of Hampel's CsChrimson pattern, 5 Hz for 5 s with 0.1 s on and 0.1 s off (Fig 7); the control is the same seed with no stimulus. *Harness:* closed loop on the flat floor, m10f0, with the connectome-only drive check of the walk bar. *Readout:* the share of 1-ms samples in which a front-leg tarsal segment (lf or rf) touches an antenna or the head (the contact readout built for stands, applied to body-body contacts), and the number of front-tarsus passes over the antennae. *Bar:* the grooming share during stimulation above the control's and above the minimum percent of time grooming the antennae under aJO activation in Hampel 2015 Fig 1B (n ≥ 17 flies); that number has not been read off the figure, so the protocol would carry a `bar_todo` until it is. *Source:* Hampel, Franconville, Simpson & Seeds 2015, eLife 4:e08758 (behaviour, measured; mechanical antennal displacement in the same paper gives a second, non-genetic stimulus: 31 ± 6 µm at 1 Hz for 10 s). *Validity:* a fly grooms its antennae while standing on its mid and hind legs, so this item cannot pass before stands does. The paper's interneurons (aBN1, aBN2, aDN1, aDN2) have no confirmed male-CNS type names, so the readout is behavioural only. The model's Johnston's organ is a proxy (`extrasenses.py`: gravity and wind projected on the head, plus a vibration term; guessed stiffness), not the antenna's own deflection, which matters only for the mechanical variant; the genetic variant kicks the JO cells directly. The l_antenna and r_antenna bodies already exist (`extrasenses.HEAD_BODIES`).

### fly2: frontier stages 1-3, built synaptic switches turned on, with the gate written first (21 Oct 21:35, before any run)
Brief: the Director's 21 Oct night brief (Ben: a mechanism is done when built at full fidelity, ON in the frontier profile at in-range values, and passing a unit check against a measurement where one exists). The switch inventory (`scripts/probes/switch_inventory.py --profile m10f0`) shows that several mechanisms the yaml calls "have" are off in m10f0: N10 (all three), N7, N9, N11, N21, both N29 switches, and N12 (`electrical:all|gap_conductance`, not in the yaml's switch list). Stages, cumulative, one switch group each (`src/flyemu/profiles.py`): **m10f1** = m10f0 + `synapse:all|per_synapse_parameters` (STP rows ORN→PN, ORN→LN, derived from Nagel 2015 / Nagel & Wilson 2016); **m10f2** = m10f1 + `synapse:all|receptor_kinetics_per_connection`; **m10f3** = m10f2 + `electrical:all|gap_conductance` + `connectome:identified|nt_from_physiology` (PSI cholinergic, measured). `m10f` keeps pointing at m10f0 until a stage passes.
- **Gate (the m10f stage-entry rule of 13 Oct, as written in profiles.py):** (G) `closed_loop_check.py --profile m10fK`, seeds 12-15, 1000 ms + 300 ms silent, noise removed in the silent window: 0.0 non-eye spikes/ms in the last 100 ms on every seed, no NaN, 0 MuJoCo warnings, no class above 200 Hz; eye cells reported apart. (S) `smoke_live.py --profile m10fK --ms 60000 --seed 12`: no runaway, no NaN, 0 MuJoCo warnings, whole-brain rate within ±50% of m10f0's 0.324 Hz (the 13 Oct 22:33 criterion), and the active fraction within ±50% of m10f0's 0.0281.
- **Unit checks (each written down before its run, below or in its own entry):** stage 1, a network-only ORN→PN train probe against a held-out depression measurement (to be named before the run); stage 2, the in-network unitary current decay per row; stage 3, `gf_latency.py` at m10f3 against Augustin 2017 (TTM band 0.866-1.216 ms; a consistency check, spent in s13).
- **Prediction:** all three stages pass G and S (the s13 5 s smoke with all three on was within 5%); the KC rows of stage 2 change nothing at rest because KCs are silent at rest in m10f0.
- **Falsifier / consequence:** a stage that fails G or S stays built-off with the reason recorded, and later stages are rerun on the last passing stage.
- Runs on backhouse, `~/fly2_mc` (git archive of the commit carrying this entry), rule 16 caps, rule 17 detached, done-files.


### s18 N19 plan revised before building (21 October, 21:56; pre-registration of the unit checks; nothing built yet)
**Hige 2015 dropped as N19's unit check.** The row-check (`docs/research/s18_n19_rowcheck.md`, Sonnet, full text)
shows the −90 ± 3.7% is depression after *pairing* odor with one DAN, absent with backward pairing or a
non-cognate DAN, and attributed to Dop1R1 in KC axons (presynaptic). N19 is a non-associative postsynaptic gain,
so that number can't test it. It goes to fly2 as a candidate unit check for the MB plasticity rows (N21).

**Mechanism (CPU path in `lif.py`; GPU path refuses it until ported and matched).** Switch
`neuromodulation:all|receptor_map`, neutral 0, bit-identical when off.
- s_ik = a_k · Σ_r p_ir · sign_r. p_ir comes from `receptors.gene_probabilities`. Coverage is 82 types with
  type-specific rows (optic lobe and KCs, Davis 2020 / Özel 2021), VNC cells by hemilineage (Allen 2020), and
  the rest of the brain on the population prior. Coverage counts will be reported. Validity: the prior cells get
  one shared s per modulator.
- Sign rule (written down before use): +1 if every reported coupling arm is Gs or Gq; −1 if Gi/o; 0 if the
  receptor is non-canonical. So Dop1R1 +1, Dop1R2 +1 (Gs and Gq, both excitatory), Dop2R −1, DopEcR 0,
  Oamb +1, Octβ1-3R +1, 5-HT2A/2B/7 +1, 5-HT1A/1B −1 (primary Gi; the heterologous PLC report is noted as
  uncertainty).
- Gain law in this mode: g_i = max(0, 1 + Σ_k s_ik · u_k), with occupancy u_k = m_k/(m_k + K_k). m_k is in spikes
  per releasing cell (each pool normalised by its own cells).
  - K_k is half occupancy: guessed 10 spikes per releasing cell. The measurement that would fix it is the GRAB ΔF/F
    per pulse relative to a saturating bath in the same prep.
- Kinetics per pool, an alpha-like rise (τ_on) then decay (τ_off):
  - OA: τ_on 0.34 s, τ_off 5.90 s, measured (Lv 2024 Fig. 2J, single pulse, MB γ3).
  - 5-HT: τ_on 0.07 s, τ_off 4.08 s, measured (Wan 2021 Fig. 2h-j).
  - DA: τ_off 1.4 s, derived from larval protocerebrum DAT Vmax/Km 0.08/0.11 µM/s per µM (Privman/Venton 2015;
    larval stage, secondary read; VNC gives 2.0 s). Its τ_on is inferred from OA's.
- **Tyramine:** a fourth pool, held at 0. The EM transmitter classifier has no tyramine class, so the pool has no
  releasing cells. No transcript table carries a TA receptor (or Octα2R), and the receptor names
  (TyrR/TyrRII/honoka/TAR1) aren't reconciled with FlyBase. Its sensitivity is 0, with that reason recorded.
- Validity range: postsynaptic excitability only. There is no presynaptic release modulation (that is where Hige's
  Dop1R1 acts) and no GPCR second-messenger lag beyond the pool kinetics.

**Unit checks (pre-registered, scored once):**
- **U1, kinetics (consistency):** whole brain, receptor map on. One kick to every OA-releasing cell; read the
  network's OA pool. Pass if τ_on and τ_off are within ±25% of 0.34 s / 5.90 s. The same for 5-HT against
  0.07 / 4.08 s.
- **U1h, held out:** 50 kicks at 100 Hz to the OA cells. Measured τ_on 0.6 s, τ_off 9.4 s (Lv Fig. 2E; a different
  region and stimulation mode). Pass is ±25% on each. A linear pool predicts τ_off ≈ 5.9 s, so a fail is expected
  unless the network reverberates. A fail is recorded as the validity limit (stimulus-dependent clearance,
  e.g. saturable uptake).
- **U2, magnitude:**
  - Calibrate one shared a (monoamine GPCR rule; a_DA = a_OA = a_5HT, fitted) on the Strother 2018 Fig. 6F/H Mi4
    gain to L5 photoactivation under 50 nM CDM. Model: kick L5, Mi4 rate with u_OA held at 1 against 0. Mi4 has
    type-specific transcripts.
  - **Held-out magnitude test:** Dacks 2009. Kick the ORNs of DM2/DL1/DM3; PN response with u_5HT held at 1
    against 0. Measured ~+15% (n=8). Pass is +5% to +30%. PNs are on the population prior, a hard test of the prior.
- **U3, held-out sign test:** Strother 2018 Fig. 4E-F (in vivo CDM raises Mi1, Tm3, Mi4, Mi9 and T4 responses).
  Pass if s_i,OA > 0 in at least 4 of these 5 types, from the Özel rows.
- **Falsifier for adoption:** if U2-held-out or U3 fails, N19 stays built-off at neutral, with the reason. If the
  m10f1 stability gate fails (`closed_loop_check.py --profile m10f1`, eye excluded, seeds 12-15; 60 s
  `smoke_live.py` on backhouse: no runaway, no NaN, whole-brain rate within 2× of m10f), it also stays built-off.
Stage name (21 October, 21:58): fly2 owns m10f1-m10f4 tonight, so N19's stage is the next free m10f stage, on top of fly2's last passing one. The gate and smoke are run on that profile, not on "m10f1".

### s19 N19 built; protocol details fixed before any whole-brain run (22 October, 01:56)
**Strother 2018 Fig. 6F, read from the figure pixels (derived).** Mi4 peak dF/F to L5 photoactivation, with 50 nM
CDM against without, at 0.2 mW/mm²: ratio **2.66**. Across the five light intensities the ratio runs 2.4 to 3.6;
the Fig. 6H example traces give 2.6, consistent. This is the one number the shared gain a is calibrated on.
Assumptions, both inferred: dF/F is proportional to Mi4 rate (GCaMP6s near-linear at low rates), and 50 nM CDM
is taken as OA occupancy 1 (CDM is a potent Octβ agonist; a lower true occupancy would mean a larger true a).

**U2 protocol.** Isolated CNS, profile m10f3 with the receptor map on, settle 500 ms. One settled network is
deep-copied; each copy holds u_OA (0 or 1). L5 cells get Poisson kicks at 100 Hz × the profile's kick_mv for
1 s; the response is Mi4's evoked activity (stim minus a no-stim copy with the same random state; spike count, or
the rate-equivalent sum if Mi4 is graded). Run a on a grid (0.25, 0.5, 1, 1.5, 2, 3, 4); a* is interpolated to
ratio 2.66. If no a in 0 to 5 (the registered range) reaches 2.66, U2 fails and N19 stays off. Dacks uses the same
protocol with DM2/DL1/DM3 ORNs kicked, uniglomerular PNs read, u_5HT held, at a*. a* is labelled **fitted**.

**U1/U1h fit method.** The pool trace is the kicked-minus-control m_k, sampled every 10 ms for 20 s. τ_off is a
log-linear fit from the peak to 10% of it; τ_on is a single-exponential rise A(1 − e^(−t/τ)) fitted from onset to
peak, as a GRAB trace is fitted. On the analytic kernels this method returns 285 ms for a 340 ms τ_on (−16%,
inside the ±25%), 5922 ms for 5900, and 65 ms for 70. The impulse-kernel τ_on implied by the peak time is
reported as a secondary number, not scored. On a 50-pulse train the rise fit returns about 1.35 s and decay 5.9 s
for a linear pool, so U1h is expected to fail on τ_off (and on τ_on), as registered.

**Off-path identity.** receptor_map 0 must give the same spikes as the code before N19: a 300 ms whole-brain
spike hash (m10f3, seed 1), old code (commit 71c4048) against new, on backhouse.

**Stage.** N19's stage is m10f5, on fly2's m10f3 (the last passing stage); it moves onto m10f4 if fly2's
passes first. Added to `profiles.py` only if Dacks and U3 pass.

### s19 N19 run order and lengths changed before the runs they affect; U3 scored (22 October, 02:05)
backhouse sits at load 22-25 from other work (the GPU is at 98% under another job), so my jobs run about one at a
time under the load-24 rule. Changes, made before the affected runs started:
- The a-grid stops at its first crossing of 2.66. a* is defined as the first crossing, so later points can't
  change it.
- U1 runs at a* (receptor map on, nothing held), OA trace 16 s, 5-HT 12 s, U1h 16 s. These are long enough for
  the decay to fall to 10% of its peak at the registered τ_off (OA: peak about 1.2 s, then 2.3 × 5.9 s).
- Order: off-path hash, U2 grid, Dacks, then the stage gate and smoke (if Dacks passes), then U1, U1 5-HT, U1h.
  U1 is not an adoption criterion in the 21:56 entry.
- Stage gate for m10f5: fly2's stage rule (21 Oct 21:35: G seeds 12-15; S 60 s, whole-brain rate within ±50%
  of 0.324 Hz and active fraction within ±50% of 0.0281) **and** my 21:56 rule (rate within 2× of m10f). Both
  must pass; ±50% is the stricter.

**U3 scored (held-out sign, Strother 2018 Fig. 4E-F; spent).** Mean net OA expression Σ p·sign from the Özel
rows (`runs/s19/n19/map.json` on backhouse): Mi1 2.50, Tm3 2.00, Mi4 2.00, Mi9 2.00, T4a-d 1.50. All five are
> 0, so s_OA > 0 for any a > 0: **pass, 5 of 5.** It's weak by construction, since every OA receptor in the
tables is +1 under the sign rule; it would only have failed if these types expressed no OA receptor.
Other map facts (derived): coverage 73,253 cells on type rows, 10,492 on VNC hemilineage rows, 83,366 on the
prior. Releasing cells DA 392, OA 101, 5-HT 48, TA 0. The 12 Dacks PNs (DL1_adPN, DM2_lPN, DM3_adPN,
DM3_vPN) are all on the prior. Their net 5-HT expression is only +0.056 (DA 0.27, OA 1.59), so Dacks' +15%
needs a·0.056 to carry it through the network. If a* is near 1, the input gain is about +6% and the test is
borderline. Mi4's net OA is 2.0, so a* near 0.8 would give gain 2.66 if Mi4 responded linearly.

### s19 S1-S4 plan, written before any source is read (22 October, 02:06)
Next row after N19 is S1-S4 (metabolism). FIDELITY's required level for this layer is a "peptide/metabolic state
layer", which the lumped `internal_state` model meets. What's missing is values from read sources and a check
against a measurement. A Sonnet read-only agent gathers measured values (it doesn't edit the repo).
- **Parameter sources (used to set values):** hemolymph volume; hemolymph trehalose and glucose (fed adult);
  whole-fly resting metabolic rate (CO2 or O2) and its Q10; flight or walking metabolic rate relative to rest;
  TAG and glycogen per fly; body water content; water loss rate at low humidity; ingestion rate during a meal;
  crop capacity or meal volume; crop emptying time.
- **Held out (never used to set a value; each scored once):**
  - S2: starvation survival on water (adult male, about 25 °C);
  - S4: desiccation survival without food or water (adult male, low RH);
  - S3: daily food intake (CAFE).
  The model predicts each one from the parameter sources above.
- **Consistency only:** S1's resting sugar is its set point, so a match there is not evidence.
- The pass band for each held-out check is the measured range across the reports the agent finds (strains,
  labs). Where only one report exists, the band is ×/÷ 1.5 around it. This is written down now, before any
  value is seen.
- Where a source is for a different sex, strain or temperature, the value is labelled measured_related, not
  measured_this_class.
- Value rule, fixed now so the held-out numbers can't steer it: each parameter takes the median of the reports for
  fed adult males at 22-25 °C. If there are none, it takes the median for adult females or mixed sexes, and if
  none of those, the nearest condition. Its bounds are the range across all reports.

### s19 U2 grid refined after a one-point bracket; Dacks stopped before any output (22 October, 02:25)
**What happened.** The first grid point, a = 0.25, gave evoked Mi4 spikes of 213 with u_OA 0 and 2,751 with
u_OA 1: ratio 12.9 (`runs/s19/n19/u2_a0.25.json`, backhouse). Mi4 is spiking in m10f3, so the spike readout is
the registered one. The driver interpolated the first crossing linearly from (0, 1) to (0.25, 12.9), getting
a* = 0.035, and it started Dacks and the smoke at that value. I stopped both before either wrote a result.
Dacks' partial log is moved to `runs/s19/n19/void/` and stays unread. **Dacks is unspent.**
**Why the a* is voided.** The interpolation spans a 13-fold jump in one step. Mi4's input gain at a = 0.25 is
only 1 + 0.25 × 2.0 = 1.5, but its output rose 12.9-fold, so the response is strongly nonlinear in a. Linear
interpolation across that bracket can be off by a large factor. This is an estimation step inside a calibration
(U2 is fitted, not held out), and nothing held out has been scored.
**Change (before any held-out result exists).** Readout, target (2.66) and first-crossing rule are unchanged.
- New grid inside the bracket: a = 0.02, 0.04, 0.06, 0.08, 0.11, 0.15, 0.2, run in order with the early stop
  (at load 22-25 only one job fits). Because a* is the first crossing, later points can't change it.
- The gate (smoke plus seeds 12-15) starts only if Dacks lands inside its band, as the 02:05 order says. The
  v2 driver had started it unconditionally.
- a* is linear between the two grid points that bracket the first crossing, with (0, 1) as the lowest point.
- Dacks, the gate and U1/U1h then run at that a*, in the 02:05 order.
- Expected consequence, written now: a* will be small (below 0.25). The Dacks PN gain is 1 + a* × 0.056 under
  bath 5-HT, so below about +1.4% at a* < 0.25. A Dacks fail is likely, and it would keep N19 built-off.
- Validity note for the fitted a: Mi4's steep response says the model's Mi4 sits near threshold under L5
  drive. A small a* therefore partly reflects Mi4's excitability in m10f3, not the receptor gain alone. This is
  recorded with the result.

### s19 S1-S4 values from sources and the held-out bands, fixed before any check is run (22 October, 02:30)
Applied under the 02:06 value rule. The agent's report (most numbers secondary) was re-checked for the two
load-bearing sources: Burggren, Souder & Ho 2017 Biol Open 6:471 (PMC5399560) and Ja et al. 2007 PNAS 104:8253
(PMC1899109). Both were read for the numbers below.
**Neutral by default.** `state:organs|model` is on in every profile (`model_data.py`). Changing the PARAMS
defaults would therefore shift every stage, fly2's included. So the values go behind a new switch,
`state:organs|values_from_sources`, neutral 0. With it at 0 the s10 guesses run unchanged.
| field | value | bounds | label | source |
|---|---|---|---|---|
| basal_nmol_s | 0.00626 | 0.00574-0.0146 | derived | Burggren: grouped Oregon R males, fed, 25 °C, about 6 µl O2/mg wet/h; male wet mass 0.505 mg. Converted with 6 O2 per glucose and 22.4 µl/µmol. STPD is not stated; at 24.45 µl/µmol the value is 8% lower. The upper bound is the authors' single-fly extrapolation, 14 µl/mg/h. The value is the measured group figure, not the extrapolation. |
| fat0_nmol | 672 | 320-1170 | derived | about 50 µg TAG per male (PMC8774106, read off a bar graph; Dahomey, 10 d, 20-21 °C) × 37.7 kJ/g ÷ 2803 kJ/mol glucose. Bounds are 24-87 µg across the reports (mixed sexes per mg, females). Glycogen is left out because no male value was found, so the store is low. |
| vh0_nl | 24 | 10-60 | inferred | 24 ± 2 nL extractable from males (attributed to an AJP-Regu 2015 paper; secondary, fetch blocked) |
| w0_nl | 344 | 300-780 | derived | Burggren: male wet 0.505 minus dry 0.161 mg |
| tau_crop_s | 11,250 | 11,250-25,700 | derived | crop turnover 32%/h of capacity when fully fed, 14%/h under dietary restriction (PMC4335172, full text read by the agent; a Geer 1970 model) |
| tau_gut_s | 2,700 | 900-7,200 | inferred | dye in the faeces from 15 min and abundant by 45-60 min (PMC4335172); whole-tract transit under 1 h (secondary). Transit time is not an absorption τ. |
Unchanged, because nothing was found: conc0, evaporation, k_act (flight is 10-15× rest, but activity 1 here is
walking, and no walking value was found), ingestion and crop capacity (sip 1.05 nL and meals of 6-200 nL are leads
only), and the hormone loop.
**Checks (scored once each; run with the switch on, nothing else changed).**
- **S2, starvation (held out).** Hours until fat + sugar falls to 5% of the start; RH 1, rest, 25 °C. The
  residual 0.05 is guessed (the death criterion; no measured residual found), and it is the value used in the
  dry run before any source was read. Band: 24-112 h, the range across the agent's reports (young and old
  Canton-S males 48 and 24 h; mixed sexes 58-112 h). All of these are secondary, so a pass is weak evidence.
- **S3, CAFE (held out).** The Ja 2007 read: single males, Canton-S, 25 °C, 1.5 ± 0.04 µl/fly/day. That is
  one report, so the band is ×/÷ 1.5 around it: **1.0-2.25 µl/day** (the paper's 1.3-2.3 across experiments is
  also reported). Food: 5% sucrose plus 5% yeast extract. The model has no protein pool, so only the sucrose
  is counted: 292 mM glucose-eq, inferred. Assimilation is 1, guessed (an upper bound, which gives the lowest
  intake). The prediction with yeast-extract energy counted is reported as a sensitivity, unscored.
- **S4, desiccation: not scored.** The water-loss rate and the lethal water fraction were not found, so its
  prediction would test two guesses. Its held-out values stay unspent.
- **S1:** consistency only (rest sugar after 6 h of fasting, from the set point).
- **Falsifier.** A fail on S2 or S3 keeps the switch off and records which value is wrong. A pass on both
  fills the S-rows' values as sourced. Adoption into a stage needs the profile gate (S couples into the
  brain through hunger/satiety), so it is not done tonight.

**S1-S4 scored (22 October, 02:31; `runs/s19/met/checks.json`, Mac).** With the switch on and nothing else changed:
- **S2 starvation: 28.4 h. Band 24-112 h: pass.** It's weak: the band is secondary and the value sits near
  its low edge. The store is TAG only (glycogen is missing), which biases the prediction short.
- **S3 CAFE: 1.85 µl/fly/day. Band 1.0-2.25: pass** (also inside the paper's 1.3-2.3).
- Registered sensitivity, unscored: with yeast-extract energy counted (5% at 3.3 kcal/g, guessed; 538 mM
  glucose-eq), CAFE is 1.00 µl/day, at the band's edge.
- Extra sensitivity, unscored: at the single-fly extrapolated rate (14 µl O2/mg/h) both fail, starvation
  12.2 h and CAFE 4.3 µl/day. The CAFE males were housed singly, so the S3 pass holds only if the measured
  group rate is the right one for a single fly. Burggren's extrapolation says it is not; that remains open.
- S4: not scored, as registered. Its held-out values stay unspent.
- S1, consistency: 39.2 mM after 6 h of fasting, against a set point of 40.
Both held-out values are now spent. By the falsifier, the S-rows' values count as sourced and the switch
stays off until a stage gate.

### s19 driver bug: a* = 0.0458 came from the voided bracket; its products voided unread, grid resumed (22 October, 04:42)
**What happened.** `n19_drive3.sh` ran the first refined point, a = 0.02 (Mi4 evoked spikes 213 → 290, ratio 1.36),
and then stopped the grid. Its `astar()` step globbed every `u2_a*.json`, including the old a = 0.25 run (ratio
12.9). It therefore found the bracket [0.02, 0.25] and interpolated a* = 0.0458 across a 9.5-fold jump, which is
the kind of step the 02:25 entry voided. The registered rule is the first crossing on the refined grid
0.02, 0.04, ..., 0.2, so 0.0458 is not the registered a*. Dacks, U1, U1 5-HT and U1h then all ran at 0.0458.
**What has been seen.** Only the driver's lines: `astar=0.0458`, `dacks finished, gate_runs=0`, and
`GATE_ALL.done`: "gate not run: Dacks outside +5% to +30% or missing". Since `dacks.done` is rc=0, this says
Dacks at a = 0.0458 was outside the band (or its `change` was null). The number was not read. U1, U1 5-HT and
U1h were not read.
**Change (decided before any further output).**
- `dacks.json/log`, `u1_*.json/log`, `u1h.json/log`, `astar.json` and their done-files move to
  `runs/s19/n19/void/v3_a0.0458/`, unread.
- `n19_drive4.sh` resumes the refined grid at a = 0.04 in order. The early stop and the interpolation use only
  (0, 1) and the points run so far, in list order. a = 0.25 is used only if 0.02-0.2 never cross.
- Dacks runs once at that a* and is scored once (pass if +5% ≤ change ≤ +30%). This re-run would have been made
  whatever the leaked verdict was, because a* was wrong either way, and nothing chosen here depends on Dacks.
  **Recorded weakness:** the held-out test is not fully clean. A fail at a nearby a is known. A pass at the
  registered a* would be reported with that caveat.
- The stage gate (about 4 h) does not start automatically; the park is 05:30. U1/U1h are re-run at the
  registered a* next session.

### s19 N26 clock light-input plan, written before any source is read (22 October, 04:44)
N26 is on and has one unit check (F-CLOCK-1, DN1p day/night). Its light coupling `k_light_per_h`, `l50_lux`,
`ct_light_h` and the cell drive peaks `peak_morning_h`/`peak_evening_h` are guessed. A Sonnet read-only agent
gathers measured values (it does not edit the repo).
- **Parameter sources (used to set values):**
  - `l50_lux`: the half-maximal light intensity of a phase-shift intensity-response curve (wild type, adult).
  - `ct_light_h` and `k_light_per_h`: one light-pulse PRC (wild type, adult, its pulse duration and intensity
    recorded). `ct_light_h` is set so that the model PRC's delay-to-advance zero crossing matches the measured
    one. `k_light_per_h` is then set so that the model's delay at the measured maximal-delay phase (near CT15)
    matches the measured delay, under the same pulse (duration and lux through the `l50` above).
  - `peak_morning_h`, `peak_evening_h`: the measured time of peak firing (or, if none, peak Ca²⁺) of the morning
    cells (s-LNv, l-LNv, DN1p) and the evening cells (LNd, 5th s-LNv), under 12:12 LD, ZT taken as CT.
- **Held out (never used to set a value; scored once):** the maximal phase advance of the same PRC, near CT21,
  as the model predicts it at that measured phase and pulse. Pass band: the measured range across the PRCs the
  agent finds for that pulse class. With one report, ×/÷ 1.5 around it, and the sign must match.
- **Consistency only:** the entrained phase under 12:12 LD (the model's CT 0 against lights-on), and the DN1p
  CT 2 / CT 10 rates (F-CLOCK-1's held-out value is spent). If moving `peak_morning_h` breaks the CT 2 rate,
  `g_clock_mv` is re-fitted at CT 2 alone by the F-CLOCK-1 rule, and labelled fitted.
- **Value rule:** median of the reports for adult wild-type flies at 25 °C, males if given, otherwise mixed or
  female (labelled measured_related). Bounds are the range across reports.
- **Validity, known in advance:** the lumped Stuart-Landau oscillator with additive forcing has a sinusoidal PRC
  with no dead zone. A measured dead zone in subjective day is a recorded limit, not a fitted feature.
- The values go behind a new switch `state:clock|values_from_sources`, neutral 0, as with S1-S4.

### s19 N26 first read thin; method clarifications before any fit (22 October, 04:49)
The first read (Sonnet, about 4 min) found one full-text source, Vinayak et al. 2013 PLoS Genet 9:e1003615
(w1118, about 21 °C), with two results. First, a maximal advance of 2.4 h at CT20-21 for a 1 h white pulse of
about 150 µW/cm². Second, intensity-response half-maxima at CT20 for blue pulses: about 600 nW/cm² for 10 min,
4 for 120 min and 3 for 360 min. No delay, zero crossing or clock-cell peak time came from a read source; those
were secondary or unverified (a "Levine 1994" PRC could not be traced). A second, narrower read is running.
Clarifications, decided now and independent of any number above:
- **`l50_lux`** is set so that the model's own intensity-response half-maximum (shift against intensity, the same
  CT and pulse duration, under the fitted k) falls at the measured half-max intensity. The model's IRC half-max
  depends on k as well as l50, so l50 is not copied from the measured half-max. Duration class: 10 min, the
  class of the ZT15/ZT21 pulse assays. Blue irradiance is converted to lux at 470 nm (683 lm/W × V(470) = 0.091,
  so 1 µW/cm² is about 0.62 lux). That conversion is labelled inferred: the fly's CRY action spectrum is not
  photopic. The 120 min half-max is a consistency check. The model integrates dose linearly below l50, so it
  predicts a 12-fold lower half-max at 120 min, against 150-fold measured. A miss is a recorded limit.
- If no read source gives the zero crossing, `ct_light_h` keeps its guess, and k is fitted at the delay alone.
- The held-out point stays the maximal advance near CT21. Vinayak's 2.4 h (1 h pulse) is held out only for a
  model run with its own pulse (1 h, 150 µW/cm² white, inferred as lux by the source's own conversion if given).
  A different pulse class is not compared.

### s19 N26 sources so far; no value changed; the held-out advance kept blind (22 October, 04:56)
**Read (full text):**
- Vinayak et al. 2013 PLoS Genet 9:e1003615: maximal advance 2.4 h at CT20-21 (1 h white pulse, about
  150 µW/cm²). Intensity-response half-max at CT20 for blue pulses: about 600 nW/cm² for 10 min, 4 for 120 min
  and 3 for 360 min (via the agent; the figure was not re-read by me).
- Lamba et al. 2014 Cell Rep 7:601 (PMC4303071), Methods and the Fig. 1 legend: y w controls get a 5 min,
  1,500 lux pulse at ZT15 and at ZT21 after 5 LD days, then 6 DD days; 16 flies × 3; SEM. Values exist only
  in the Fig. 1C bars. A blind Sonnet reader is extracting the y w ZT15 delay alone. **I have not seen the ZT21
  advance**, and it stays held out.
- Liang, Holy & Taghert 2016 Science 351:976 (PMC4836443), text: M cells (s-LNv) peak in Ca²⁺ toward the end
  of subjective night (around lights-on), and E cells (LNd) toward the end of subjective day (before lights-off).
  The M-E phase difference is about 10 h, and both lead their behavioural peaks by about 4 h. This holds in
  long and short photoperiods. The per-group ZT is only in Fig. 1F, which was not read. These are Ca²⁺ phases,
  not firing.
- Dollish et al. 2022 (bioRxiv 2021.04.08.439018; D. ananassae, so a related species only): a delay zone of
  about 5 h, an advance zone of about 10 h and a 9 h dead zone, anchored to lights-off.
**Not found in a read source:** the D. melanogaster delay-to-advance zero crossing, and a full wild-type PRC.
Candidates for a figure read are Kistenpfennig et al. 2012 J Biol Rhythms (epub.uni-regensburg.de/34459) and
the Dollish PRC figure (related species).
**Decision.** Under the 04:49 rule, `ct_light_h` keeps its guess (8 h). At 8 h the model's weak-pulse PRC
crosses from delay to advance at CT20 and peaks its advance at CT2. That contradicts Vinayak's maximal advance
at CT20-21, so the guess is already known to be wrong. Scoring the held-out ZT21 advance against it would spend
the point to learn nothing new. So nothing is fitted or scored tonight: `CLOCK_SOURCED` stays empty behind the
neutral switch. The fit (ct_light from a read zero crossing, k from Lamba's ZT15 delay, l50 from Vinayak's
10 min IRC) and the one held-out score (Lamba ZT21 advance, same pulse) wait for the zero-crossing read.
Liang's text is consistent with the current peak guesses in direction (morning group 2, evening 10, 8 h apart
against about 10 h). They are left unchanged until Fig. 1F is read, because any change to `peak_morning_h`
also moves the fitted DN1p drive at CT 2 (F-CLOCK-1).
Tool: `scripts/probes/s19_n26_prc.py` (prc, irc, fit, entrain modes; the Organs ODE m10f uses). Check: under
the guesses, a 10 min 1,000 lux pulse gives −0.13 h at CT14 and +0.13 h at CT2, about 20× below measured
shifts, so k will rise far above its guessed bounds [0.02, 2].

**N26 addendum (22 October, 05:04).** The blind reader returned the Lamba 2014 Fig. 1C **y w ZT15 delay:
−3.1 h, SEM about 0.35 h** (5 min, 1,500 lux; 16 flies × 3). Derived from the figure pixels: the axis ticks fit
to under 0.02 h, and the bar end is at y = 215 px. Crops are in `/tmp/lamba_crops/` (not kept). The reader was told
not to report any ZT21 or advance value and did not. The ZT21 advance stays held out and unseen. This is the
value k will be fitted to once ct_light is sourced.
Correction to the 04:49 entry: Vinayak's 2.4 h advance was seen in the agent report before 04:49 called it held
out, so it counts as consistency only. The one held-out N26 point is Lamba's ZT21 advance.

### s19 N19 U2 a* and Dacks scored once: Dacks FAILS, N19 stays built-off (22 October, 05:23)
**U2 (fitted, Strother 2018 Fig. 6F ×2.66; `runs/s19/n19/astar.json`, backhouse).** Mi4 evoked spikes, u_OA 1
against 0 (u0 = 213): a = 0.02 ×1.36, 0.04 ×1.82, 0.06 ×2.50, 0.08 ×3.16. The first crossing is between 0.06 and 0.08:
**a* = 0.0649 (fitted)**. At a*, Mi4's own input gain is 1 + 0.0649 × 2.0 = 1.13 (net OA 2.0, type row). The
kicked L5 are modulated too (net OA 2.98). Even so, the ×2.66 output is network amplification of a near-threshold Mi4
(`runs/s19/n19/map.json`).
**Dacks 2009 (held out; scored once; `runs/s19/n19/dacks.json`).** At a* = 0.0649, with DM2/DL1/DM3 ORNs kicked
(200 ORNs, 100 Hz Poisson × 68.75 mV) and 12 uniglomerular PNs read (DL1_adPN, DM2_lPN, DM3_adPN, DM3_vPN): evoked PN spikes **297 at u_5HT 0, 296 at
u_5HT 1, change −0.34%**, against the band +5% to +30%. **FAIL.** The 04:42 weakness applies (a fail at
a = 0.0458 had leaked), but the outcome is the same.
**Consequence (falsifier, 21 Oct 21:56).** N19 stays built-off at neutral; no gate, and no m10f5. The input-gain
arithmetic predicted this: all 12 PNs sit on the population prior (no type or hemilineage row), with net 5-HT
+0.0556, so their input gain at a* is about +0.4%. The network does not amplify that the way it amplifies Mi4.
**Validity limit (recorded).** One shared monoamine gain a can't carry both Mi4's ×2.66 under CDM and the PNs'
+15% under 5-HT, given the receptor map's population prior for PNs. The candidates, none of them tested:
- PN-specific 5-HT receptor rows from a transcript source (the Davie 2018 brain atlas fetched tonight has PN
  clusters; not yet read).
- Presynaptic 5-HT action at ORN terminals, outside N19's validity range.
- A per-modulator a. That would need a second calibration point, and is not adopted without one.
Dacks is now **spent**.

### s20 MB resting rates with plasticity off: one noise level per class, fitted on two cells, tested on Huang 2024 (pre-registered 22 October, 22:23, before any grid run)
**Director's held note.** fly2 found the KC->MBON rules wipe memories in seconds at real DAN resting rates. So this
fit runs with plasticity off. In this checkout m10f3 has no N21 (it lives in fly2's worktree), and the probe asserts
N22 forgetting is 0. ORN->PN short-term depression (N29, stage 1) stays as it is; it is not memory. Nothing here
may enter a profile with N21 on until fly2's resting-safe rule lands.
**Mechanism (N3, existing rows).** `class:DAN|noise` (340 cells) and `class:MBON|noise` (97 cells), in mV/√ms.
The row bounds are 0-3, guessed. Tonic drive stays 0 because without noise the low rates are a knife-edge
(DECISIONS s12). KC, APL and DPM are untouched: KCs at 0 Hz sit inside Turner 2008's 0.1 ± 0.4 Hz, and APL/DPM
have no rate.
**Probe.** `scripts/probes/s20_mb_rest.py`: m10f3, isolated CNS, no stimulus, settle 0.5 s, read 4 s.
**Grid (seed 12).** σ in {0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0}, applied to both classes in each run.
**Fit (labelled fitted).**
- σ*_DAN: the first crossing of 8 Hz by PPL105's (PPL1-α'2α2) mean rate. 8 Hz is the middle of Huang 2018
  Nat Commun 6-10 Hz.
- σ*_MBON: the first crossing of 12.1 Hz by MBON14's (MBON-α3) mean rate (Hafez 2023 eLife).
- Both by linear interpolation between grid points. No crossing means no fit, and that is reported.
**Confirm (not held out).** One run at (σ*_DAN, σ*_MBON) with seeds 12 and 13. Needs PPL105 in 6-10 Hz and MBON14
in 9.7-15.1 Hz (×/÷1.25, guessed). Whole-brain rate and active fraction are reported against σ = 0.
**Held-out test, once: Huang et al. 2024 Nature Fig. 1 voltage imaging** (Zenodo 10998457, `data/raw/huang2024/`).
This is unseen, and the register names it for resting rates. Opened only after the confirm runs are written.
- **Data readout.** Per trial, rate = number of `DetectedSpikes` / (t[-1] − t[0]). Average trials within a fly.
  Per type, take the median across flies and the 10th-90th percentile across flies.
- **Model readout.** The per-type mean rate over that type's cells at σ*, averaged over seeds 12 and 13.
- **Map.** PPL1-γ1 → PPL101, PPL1-γ2 → PPL103, PPL1-α'3 → PPL104, PPL1-α2 → PPL105, PPL1-α3 → PPL106;
  MBON-γ1 → MBON11, MBON-γ2 → MBON12, MBON-α'2 → MBON13, MBON-α3 → MBON14, MBON-α'3m → MBON17,
  MBON-α2sc → MBON18. These come from instance labels; PPL106 = α3 by its 860 synapses onto MBON14.
- **Per-type pass.** The model is inside [min(P10, median/2), max(P90, 2 × median)].
- **Test set.** The 9 types other than PPL105 and MBON14 (the fit types). **Pass if at least 6 of 9.**
  PPL105 and MBON14 are reported apart, as a cross-study consistency check.
- **Falsifier.** 5 or fewer of 9: one noise level per class can't carry the per-type spread. Not adopted.
- **Weaknesses, recorded now.**
  - One PPL1-α'3 trial's spike count showed in fly2's zip listing.
  - Huang's flies were on a ball, with walking and rest mixed, and spikes detected optically.
  - The model is an isolated CNS with no body input.
**Adoption, if it passes.** Not tonight. It needs a stage on m10f3 (name chosen then, to avoid fly2's m10f4), the
gate, a battery run and a viewed figure, with N21 off. Until then N3 stays partial.

### s20 N26 fit void: the Stuart-Landau light input cannot carry the read sources; Lamba ZT21 stays sealed and unspent (22 October, 22:43)
The registered fit (04:44, 04:49, 05:04; `scripts/probes/s20_n26_fit.py`, `runs/s20/n26/fit.json`) did not converge:
k ran to its 500/h bound, no PRC zero crossing was found, and lights-on in 12:12 LD fell at model CT 18.5. A k scan at
ct_light 6.5 (the zero-crossing solution) shows why, at every k from 0.3 to 100/h:
- **Entrained phase.** Lights-on sits at model CT 19-22, not CT 0. Light pulls the phase towards one point (ct_light), so the
  day can't sit in a dead zone. The PRC zero crossing (CT 18.5) and the entrained phase can't both be met.
- **Pulse length.** The shift grows with pulse length until type-0 resetting. At CT15, a 5 min pulse gives 3.5 h and a
  60 min pulse 9.2 h (k 10). Flies give about 3.1 h for 5 min (Lamba 2014, y w, 25 °C) and 4.05 h for 60 min (Kistenpfennig 2012, w1118, 20 °C).
**Decision.**
- Nothing is fitted or written to `CLOCK_SOURCED`. The switch stays neutral 0 and the guessed values stay as they are.
- The −9.08 h ZT21 "prediction" in fit.json comes from the void fit and is void. Lamba's ZT21 measurement was never
  opened, so it stays held out, unspent.
- The peak hours read from Liang 2016 are not written either, since they depend on a valid entrained phase.

**Next.** A light input gated by a light-labile night state, i.e. CRY-dependent TIM degradation. The input is
present only when TIM is high (subjective night) and is used up by light within minutes. That gives the dead zone
and the pulse-length saturation. Its values come from sources: TIM's daily profile and its light degradation
half-time (Western blots). Then re-register the fit.

### s20 N19 receptor_map mode 2: Davie 2018 brain-cluster rows for types with no Davis/Ozel row (22 October, 22:43)
- **Rows.** `data/derived/receptor_calls_davie2018.csv` (`scripts/probes/s20_davie_rows.py`) covers 122 male-cns types, 2,447 cells.
  - p is the share of a cluster's cells with ≥ 1 UMI, pooled by cell count (derived).
  - The crosswalk is by name (inferred): `*_adPN` → the five adPN clusters (365 cells); `*_lPN` → the three lPN clusters (107);
    KCg* → G-KC; KCab-m → A/B-KC + A/B*-KC; MBON* → MBON; PAM* → PAM; PPL1/PPL2 → Dopaminergic; s/l-LNv → LNv; DN1* → DN1.
  - Not covered: ventral PNs, KCa'b', ring neurons, AL local neurons.
  - Peptide-receptor genes are in the same file (N20 data, not wired).
- **Switch.** `neuromodulation:all|receptor_map` = 2 uses these rows for cells with no Davis/Ozel row (source 3).
  Precedence is type > Davie > hemilineage > prior. Mode 1 is unchanged everywhere: checked equal outside the
  2,447 cells, and Mi4 is untouched, so a* = 0.0649 still holds. The default stays 0.
- **Scale check (overlap).** On 11 types that also have Davis/Ozel rows (143 type-gene pairs), Davie p vs Davis p gives r = 0.63.
  Davie p runs lower (median 0.22 vs 0.99; 10x dropout), and the 5-HT2B and 5-HT7 shortfalls are the largest
  (0.03/0.06 vs 0.30/0.27). Validity limit: Davie and Allen rows share this 10x scale, the Davis rows don't.
- **PN result (not a score; Dacks is spent).** Under mode 2, net 5-HT is −0.29 for the adPNs and −0.11 for the lPNs, against +0.056 on the prior.
  Postsynaptic N19 therefore predicts PN *inhibition* under 5-HT with PN-specific transcripts. Dacks 2009's
  facilitation then has to come from paths N19 doesn't have (release from ORN terminals, LNs). The s19 failure was not only the
  prior. A PN retry on Dacks would be both re-use and expected to fail, so it isn't run.
- **N19's next held-out test** goes on unspent evidence for cells on type or Davie rows. Candidates are Sampson 2020 L2/T1 5-HT
  (open access; direction already known from the abstract, magnitudes sealed unread) and a KC/MBON/LNv monoamine
  measurement still to be found. To be registered next session.

### s20 N19 scope: the AL routes for 5-HT, which data cover them (scoped, not built; 22 October, 22:51)
F-S20-2 is corrected: Davie's PN sign flips under a per-gene dropout scale. The magnitude gap stands: the direct PN gain at a* is ≤ 2%,
against +15%.
**Connectome (male-cns, traced).** 2 CSD cells (5-HT) make 14,743 output synapses:
- 6,415 onto AL LNs (420 cells, 79 types; 128 ACh, 114 GABA, 87 Glu, 89 unclear);
- 1,795 onto PNs;
- 518 onto ORN terminals (2,635 ORNs, 53 types).
Wiring favours an LN route over a presynaptic ORN route (5-HT also acts by volume, so this isn't decisive).
**Receptor data per route.**
- **Davie 2018 covers neither.** It is brain-only, so there are no ORN cell bodies (they sit in the antenna), and it has no named
  AL-LN cluster. Its 20+ unnamed GABAergic clusters can't be assigned to AL LNs without a marker.
- **ORNs.** McLaughlin et al. 2021 eLife (adult ORN scRNA-seq, per ORN class) or Fly Cell Atlas antenna (Li et al. 2022 Science;
  s19's FCA download got a 503).
- **LNs.** No type-resolved transcriptome is known. Sizemore & Dacks 2016 Sci Rep give per-receptor PN-vs-LN presence from
  MiMIC-GAL4 lines (qualitative, so p would be inferred 0/1). Suzuki 2020 places 5-HT7 in a GABAergic LN population.
- **PNs.** Li et al. 2017 Cell (Smart-seq2, PN class-resolved, deeper than 10x) would settle the PN sign without dropout.
**Mechanism needed.**
- LN route: no new code. LNs already get N19's postsynaptic gain; they only need rows (mode 2 extension).
- ORN route: a presynaptic gain (a cell's outgoing spikes × (1 + a s_pre u)) as a new neutral switch, CPU first, plus ORN rows.
- Both must keep the shared a* and stay neutral off.
**Proposed order (not started).**
1. Li 2017 PN rows (settles the sign).
2. McLaughlin 2021 ORN rows and the presynaptic switch.
3. LN presence calls from Sizemore & Dacks 2016.
4. Register the next held-out test on unspent evidence (Suzuki 2020's LN/PN gain control is the natural one, since it tests the LN route).

### s20 N26 CRY-TIM refit, registered before running (22 October, 23:02)
**Mechanism.** Switch `state:clock|light_input` = 1 (neutral 0 keeps the s10 pull). Light activates CRY, CRY
removes TIM, and the TIM removed pushes the phase (`internal_state` docstring):
- c' = a L (1 − c) − c/τ_c
- T' = (P(ct) − T)/τ_rec − k_d c T
- z += k_tim (k_d c T dt) e^{i 2π ct_tim/24}

It is night-gated, because T is low in the subjective day, and saturates in pulse length, because T gets used up.
Before this entry I ran only the smoke and assay checks (`s20_n26_tim.py`; the fast assays match the reference
to < 1e-4 h) and one evaluation at the guessed k_tim 1 and ct_tim 6.5. No fit has been run.

**Values (labels).**
- **TIM_DD** (measured, pixel read): Shafer, Rosbash & Truman 2002 J Neurosci 22:5946, Fig. 6D.
  - Small vLNs (s-LNv), Canton-S, DD day 1, 25 °C, 4 brains per point.
  - Value = cytoplasmic + nuclear mean pixel intensity, read by eye from a 3× crop (±3 of 200), divided by the
    CT16 maximum.
  - CT0 0.77, 1 0.51, 2 0.16, 3 0.065, 4 0.029, 6-10 0.015, 12 0.15, 14 0.30, 16 1.0, 18 0.51, 20 0.26, 22 0.98.
  - Interpolation is log-linear. P = TIM_DD (1 + τ_rec d ln TIM_DD/dct) (derived), so T follows TIM_DD in DD.
- **τ_rec = 0.86 h** (derived). It is the upper bound set by the profile's steepest decline, CT1→2: ln(0.51/0.16) = 1.16/h,
  where P reaches 0. The value is taken at that bound. A slower dark turnover can't produce the measured
  morning fall.
- **k_d by rule** (derived). A 10 min, 1000 lux pulse at CT15 (DD) leaves 10% of unpulsed TIM 1 h after the
  pulse. Source: Tang et al. 2010 Neuron 66:378, where DN/LNd TIM is "undetectable" after a saturating 10 min
  ZT15 pulse fixed 1 h later. The 10% is inferred.
- **a by rule** (as registered 04:49). The model's 10 min IRC half-max at CT20 is 0.372 lux (Vinayak 2013,
  600 nW/cm² blue; the lux conversion is inferred). The two rules are solved jointly at every evaluation.
- **τ_c = 0.5 h** (guessed). Two reads found no in vivo active-CRY lifetime.
- Period 24 h (inferred) and μ 1/h (guessed) are unchanged.

**Fitted (labelled fitted).** `k_tim` and `ct_tim_h`. Search: a 5 × 12 grid (k 0.3-30, ct 0-22), then Nelder-Mead
from the two best cells (`scripts/probes/s20_n26_tim_fit.py`).

**Training targets (4 targets, 2 free parameters).**
- PRC zero crossing CT 18.5: Kistenpfennig 2012, DD, 60 min, 1000 lux, w1118, 20 °C.
- DD CT15 delay −4.05 h: same source and pulse.
- LD ZT15 delay −3.1 h: Lamba 2014 y w, 5 min, 1500 lux. The model's LD is 1000 lux for 20 days.
- Lights-on in 12:12 LD (1000 lux) at CT 0.

The loss is the sum of squared band-scaled residuals.

**Pass bands.** Zero crossing ±1 h; both delays ×/÷ 1.5, with sign; lights-on ±2 h.

**Falsifier.** If any of the four is outside its band at the best fit, CRY-TIM with these sourced values fails.
That goes in FINDINGS, and ZT21 is not scored.

**Robustness variants.** Registered now; reported, not deciding:
- V1: τ_c 0.1 h.
- V2: τ_c 2 h.
- V3: τ_rec 0.43 h.
- V4: TIM_DD without the CT20 point. Its dip may be staining noise.
- V5: Tang fraction 3%.

The primary fit decides. If it passes and a variant fails, the dependence is reported. If it fails and only a
variant passes, nothing is scored tonight (a post hoc choice).

**Consistency only.**
- Vinayak 120 min half-max, 4 nW/cm² ≈ 0.0025 lux. The model integrates dose, so about 12-fold below the 10 min
  value is expected, against 150-fold measured. A miss is a recorded limit.
- Vinayak TIM loss ≥ 60% after 10 min at the threshold intensity.
- Vinayak 2.4 h maximal advance near CT20-21 (already seen).
- Pulse-length saturation: CT15 delay for 1-120 min.
- A small subjective-day response.

**Held out (scored once).** Lamba 2014 y w ZT21 advance, 5 min, 1500 lux, in the same LD assay. It is predicted
only by the primary fit and only if all four targets pass. The prediction goes in DECISIONS before a blind
reader opens the figure. Band ×/÷ 1.5 around the measured value, and the sign must match.

**Validity, known in advance.**
- s-LNv TIM stands in for the network's light-labile TIM. Tang finds DN/LNd TIM, not s-LNv TIM, degraded at ZT15.
- One lumped oscillator.
- The sources differ in strain and temperature: 20 °C against 25 °C.
- Lamba's LD intensity is not known.

**Adoption.** The switch stays 0 whatever happens. The N26 row moves only on a held-out pass followed by a gate.

### s20 N26 CRY-TIM refit scored against the 23:02 registration; ZT21 prediction written before the blind read (22 October, 23:55)
**Primary fit: all four training targets pass.**
- Fitted values: k_tim 0.789, ct_tim_h 7.59 h. Loss 0.634.
- Rule-set values (derived):
  - k_d 13.8/h (half-life 3 min under full CRY);
  - a 10.3/(lux·h).
  - The two rules close: Tang left 0.100, IRC half-max 0.373 lux.

| target | measured | model | band | result |
|---|---|---|---|---|
| PRC zero crossing, DD 60 min | CT 18.5 | CT 18.80 | ±1 h | pass |
| DD CT15 delay, 60 min 1000 lux | −4.05 h | −3.86 h | ×/÷1.5 | pass |
| LD ZT15 delay, 5 min 1500 lux | −3.1 h | −2.36 h | ×/÷1.5 (−2.07..−4.65) | pass, low side |
| lights-on in 12:12 LD | CT 0 | CT −0.54, no drift | ±2 h | pass |

**Variants** (reported, not deciding):

| variant | ld15 | ZT21 | result |
|---|---|---|---|
| V1 τ_c 0.1 h | −2.73 | +4.15 | passes; Tang rule unmet (k_d at its 50/h bound, left 0.135) |
| V2 τ_c 2 h | −1.97 | +0.17 | **fails**: does not entrain (lights-on drifts 7.9 h); ld15 out of band |
| V3 τ_rec 0.43 h | −2.26 | +2.45 | passes |
| V4 no CT20 point | −2.27 | +3.75 | passes |
| V5 Tang 3% | −2.41 | +2.68 | passes; rule unmet (k_d at bound, left 0.047) |

- The result depends on τ_c, which is guessed. It needs active CRY to clear within about an hour of lights-off;
  at 2 h the clock cannot entrain.
- ld15 sits on the low side (−2.0 to −2.7) in every variant. ct_tim is 7.2-7.8 h wherever a variant passes.

**Consistency only** (registered list).
- Vinayak 120 min half-max: model 0.014 lux against 0.0025 measured. The model's 10 → 120 min ratio is 26-fold
  against 150-fold measured. This is the recorded limit: the model integrates dose and the fly does more.
- Vinayak TIM loss right after 10 min at 0.372 lux, CT20: model 38% against ≥ 60% measured (Vinayak's fixation
  delay unknown). This misses.
- Saturating 10 min CT20 advance: model +2.11 h against Vinayak's ~2.4 h maximum. The half-max pulse gives
  +1.05 h.
- Pulse-length saturation at CT15: 1 / 5 / 15 / 30 / 60 / 120 min give −2.86 / −2.93 / −3.10 / −3.36 / −3.86 /
  −4.86 h.
- Subjective-day response: |shift| < 0.25 h from CT 3 to CT 9 (60 min).

**Figures viewed** (`docs/media/s20_n26_tim_prc.png`, `docs/media/s20_n26_tim_tim.png`).
- The 60 min PRC is strong type 1, with steep but continuous delay → advance across CT 17-20.
- The advance extends to CT0 (+2.4 h) and fades by CT3.
- In LD:
  - TIM is ≈ 0 through the day and rises from ZT13.
  - The LD TIM waveform has two peaks (ZT16.5, ZT22.5). That shape is inherited from the single Shafer CT20 point. V4
    drops the point and still passes, so it isn't load-bearing, but the waveform shape is an artefact.
  - Lights-on clears TIM within about 10 min.
- Entrainment settles in 2 days.

**Held-out prediction** (written now, before anyone opens Lamba 2014 for ZT21).
- Protocol: Lamba 2014 y w, 5 min pulse, 1500 lux, at ZT21 on the last LD night, same LD assay as the ZT15
  training point.
- **Primary fit predicts a phase advance of +2.89 h.** The fast path (`LD.shift`) and the reference
  `s20_n26_tim.ld_shift` agree to 3 decimals.
- Pass if the measured value is an advance and the prediction is within ×/÷1.5 of it, i.e. measured in
  +1.93 to +4.34 h.
- The variants span +2.45 to +4.15 among the passing ones. They are reported only and do not change the score.
- For context, not a scoring rule: the ZT15 training point came out at 0.76 of the measured value, so a similar
  shortfall at ZT21 would still pass.

**Blind read.**
- One Sonnet reader, no subagents of its own.
- It extracts only the y w ZT21 value (mean and SEM) from Lamba 2014 Fig. 1C, by pixel read with axis
  calibration.
- It is not told the prediction. Scored once, then spent.

### s20 N26 held-out Lamba ZT21 scored once: PASS; start-up state fixed; not adopted tonight (23 October, 00:09)
**Blind read** (one Sonnet reader, no subagents; it was not told the prediction; Lamba 2014 Fig. 1C,
`nihms655030f1.jpg` 601 × 456 px).
- Calibration: 9 axis ticks, fit residual ≤ 0.03 h.
- y w bar identified by its legend fill.
- Result: **y w ZT21 = +3.21 ± 0.23 h (SEM), an advance.**
- Neither the text nor the legend states the number. n = 16 flies per genotype, N = 3 experiments.
- Calibration check: the same read gives y w ZT15 −3.04 ± 0.38 h, against the 22 Oct 05:04 blind read of −3.1 ± 0.35.

**Score.**
- Predicted +2.89 h (23:55, written before the read). Measured / predicted = 1.11, the sign matches, and the
  prediction lies inside [3.21/1.5, 3.21 × 1.5] = [2.14, 4.82]: **PASS.** The point is now **spent**.
- Variant predictions, reported only: V1 4.15, V3 2.45, V4 3.75, V5 2.68 would all pass. V2 (τ_c 2 h) at 0.17
  would fail, as it already failed training.

**Start-up state (fixed, before any adoption).**
- With `light_input` 1, `Organs` started T at TIM_DD(ct): 0.29 at the m9c start CT 1.5.
- A run in light therefore began by clearing night-level TIM. The clock jumped +0.18 h in its first minute
  at 100-1000 lux.
- Now c and T start from 2 days of 12:12 LD at 1000 lux, ending at ZT = start CT. This matches a fly kept in
  LD, like the male-cns specimen (`initial_ct`, ZT 1.5). Rearing intensity is guessed; the rule is inferred.
  - At ZT 1.5: c 0.9998, T 9 × 10⁻⁵. After 60 s at 1000 lux the clock reads CT 1.5198 against 1.5197
    free-running.
  - At night (CT 16): c ≈ 0, T 0.975.
- DD assays now start from a DD state (c 0, T = TIM_DD), as in the registered fit.
- Every registered number reproduces exactly: ld15 −2.3571, ZT21 +2.891, dd15 −3.8607, Tang 0.100.
- `cry_tim_step` is shared by `_step` and the pre-run.
- New test: `test_cry_tim_light_input_is_night_gated_and_starts_entrained`.

**Registry.**
- `cry_rate_per_lux_h` 10.26 and `tim_kdeg_per_h` 13.85 become the PARAMS defaults, labelled inferred (each
  set by a rule from a measured point through an inferred step). They are read only with `light_input` 1.
- `tim_tau_rec_h` keeps value 0.86 (derived); its bounds are labelled guessed (the validator caught
  `bound_basis` derived).
- `k_tim` 0.789 and `ct_tim_h` 7.59 are fitted. As with `clock_gain`, they belong in the stage profile, not
  in PARAMS.

**Not adopted tonight (reason).** The registration requires a gate after a held-out pass. fly2's branch has
moved the frontier (`m10f` = m10f4, with m10f5 defined; commits 134de81 and 4b79905, not on main), so a stage
defined now on main's m10f0 would sit on a stale base and collide with fly2's numbering.

**Next (registered now).** Adoption stage on fly2's latest passing stage once it is on main; the name is chosen
then. It sets `state:clock|light_input` 1, `k_tim` 0.789 and `ct_tim_h` 7.59 (both fitted).
- Gate: fly2's stage rule (G seeds 12-15; S 60 s, whole-brain rate within ±50%).
- Plus an LD check on the organism: 3 days of 12:12 LD, lights-on within CT 0 ± 2 h.
- The default world is dark (`light_lux` 0). The gate therefore tests only that the switch is inert in the
  dark. The LD check is the meaningful one.
- N26 stays **partial** even then: τ_c and μ are guessed, and the cell peak hours are guessed.

### s20 N25 sleep homeostat: Abhilash & Shafer 2024 values against held-out rebound, registered before building (23 October, 00:27)

**Question.** Does the two-process set that Abhilash & Shafer 2024 fitted to fly sleep predict rebound sleep after deprivation? Their fit never used deprivation data. Implemented in our N25 homeostat, a pass would replace guessed N25 values with inferred ones. Sources: `docs/research/s20_n25_reads.md`, rounds 1-2.

**Nothing is fitted.** All values are taken as published. The only free choices are the structural ones below, and they are fixed now.

**Model (new switch `state:sleep|values_from_sources`, neutral 0).**
- **Mode 0** is unchanged: the s10 guesses (tau_wake 12 h, tau_sleep 3 h, th 0.6/0.3) with the 12 h harmonic c_amp cos(4π ct/24).
- **Mode 1** is the Abhilash set:

  | field | value | label |
  |---|---|---|
  | tau_wake_h | 8.76 | inferred |
  | tau_sleep_h | 9.51 | inferred |
  | th_hi | 0.35 | guessed (Daan) |
  | th_lo | 0.15 | guessed (Daan) |
  | c_amp | 0.10 | guessed (Daan) |

  - Modulation is c_amp cos(2π(ct − φ)/24), a 24 h cosine.
  - φ is the time origin of their simulation, being read now (round 3, model information only). If the paper does not state it, φ = CT 0 (guessed). That is the Daan convention: the thresholds peak at dawn, so sleep falls at night.
  - The S equations and the behavioural sleep criterion (≥ 5 min below a_rest) are unchanged.

**Reduced loop (CPU probe, `scripts/probes/s20_n25_sleep.py`).**
- The clock is entrained (ct = ZT, period 24 h).
- Activity is 0 while the dFB switch is on and 1 while it is off. This assumes the switch-to-inactivity link through the brain, which this probe does not test (validity limit).
- Deprivation forces activity to 1, as mechanical deprivation keeps the fly moving.
- Time step 1 min. Sleep is scored like DAM data: inactivity runs ≥ 5 min count whole.
- The probe reports the last of 10 entrained days (baseline), then deprivation and recovery.

**Checks before the held-out score (not evidence).**
- **C1, implementation (unit) check.** Abhilash's discrete rule with their values at τ 24 h must give 74.36 % sleep/24 h within ±1 pp.
  - Our continuous form with the 5-min onset lag must match the discrete rule within ±2 pp.
  - If C1 fails, the implementation is wrong and nothing is scored.
- **C2, consistency with seen data (category A, already read; not held out).**
  - Baseline total sleep must lie within 618-1100 min/day.
  - Night sleep must exceed day sleep.
  - These are reported for mode 0 and mode 1. A fail is recorded as a validity limit; it is not a reason to retune.

**Held-out score (spent once): Huber et al. 2004 Sleep 27:628 rebound after mechanical deprivation.**
- The protocol (durations, timing, recovery window, baseline, units) is being read now **without magnitudes**.
- The model is then run on that exact protocol, and the predictions for mode 1 and mode 0 are written here before any magnitude is read.
- **Pass (mode 1).** "Consistent with some fly" is the per-value bar. Take the span of wild-type group means ± 2 SEM, over the lines and sexes Huber reports (males preferred; females used only if no male group exists).
  - The predicted recovery for the longest deprivation (the primary point) must lie inside that span.
  - The predictions for at least two-thirds of the other durations must also lie inside it.
  - If only figure reads are available, the read uncertainty is added to the SEM.
- **Falsifier.** If the primary point falls outside the span, the published set fails as a rebound model. N25 then keeps its guessed values, and the miss and its direction go into FINDINGS. There is no refit on Huber, because it will be spent.
- **Variants (reported, not scored).** V1: S decays from switch-on (no 5-min lag). V2: τ 23.5 and 24.5 h. V3: φ = CT 12.

**Physiology.** dFB excitability against sleep need (Donlea 2014, Pimentel 2016) is not scored. Our dFB state is a binary switch with a fixed drive g_dfb, so no continuous excitability can be compared. This is recorded as a validity limit of N25.

**Adoption.** Even on a pass, adoption needs a stage on fly2's frontier with the usual gate, as for N26. N25 is already on in m10f with mode 0.

### s20 N25 checks C1 and C2 scored against the 00:27 registration: C1 FAILS, nothing scored, Huber 2004 stays unread (23 October, 00:30)

**C1 (implementation) FAILS, by the registered ±1 pp.**
- Abhilash's discrete rule with their values gives 75.56 % sleep per 24 h against their stated 74.36 %, a gap of 1.20 pp.
- The gap is not explained by:
  - τ: 23.5 / 24 / 24.5 h give 75.83 / 75.56 / 75.42;
  - update order: updating S before the threshold test also gives 75.56;
  - including the transient: all 9 LD days give 75.22, and days 1-4 give 73.26 / 74.93 / 75.49 / 75.56;
  - a coarser step: 15 min gives 75.0, 1 h gives 77.1.
- Our continuous form (Organs, 5-min onset lag) gives 75.83 %, against 75.56 % for the discrete rule (within the ±2 pp tolerance). So our code matches my reading of their equations. The gap lies in an unstated detail of their simulation.
- By the registration, nothing is scored. The tolerance is not relaxed after the fact.

**C2 (consistency with seen data; recorded, not used to retune).**

| run | total (min/day) | day | night | in 618-1100? | night > day? |
|---|---|---|---|---|---|
| mode 1, φ = CT 0 | 1092 | 576 | 516 | yes | **no** |
| mode 1, V3 φ = CT 12 | 1092 | 516 | 576 | yes | yes |
| mode 1, V1 (no lag) | 1088 | 594 | 494 | yes | no |
| mode 0 (s10 guesses, on in m10f) | 411 | 205 | 206 | **no** | equal |

- **The s10 values now on in m10f sleep too little in the reduced loop.** 411 min/day (28.5 %) is below every cited wild-type value (≥ 618).
- **Mode 1 with φ at CT 0 sleeps through the day.** It sleeps ZT 2.1-16.0 and ZT 19.4-23.6. Abhilash's own figure legend says their model profile is night-biased ("underestimate daytime sleep and somewhat overestimate nighttime sleep"; round 3). So their time origin is probably not CT 0, but it is not stated.

**Huber 2004 protocol read (round 3).** No full text is reachable: there is no PMC version and the OUP page is paywalled.
- Only the methods fragments in the abstract were found: deprivation of 6, 12 and 24 h by mechanical stimulation, in DAM.
- The recovery window, baseline and units are unknown, so the registered held-out score cannot be specified.
- No magnitudes were read. The reader saw a number quoted by secondary sources and withheld it. **Huber 2004 stays unspent.**

**Next.**
1. Resolve C1 and the time origin from the authors' code or supplement, if public. This is model information, not held-out data. A new registration would follow before any rebound data are read.
2. Huber's full text needs Ben (library access). An open-access alternative (Brown et al. 2020 PLoS Genet, PMC7089559) would need its own registration and protocol read first.
3. Nothing on N25 changes tonight. The switch stays neutral (0) and mode 0 stays on in m10f.

### s20 N25 rebound predictions written before any magnitude is read (23 October, 00:34)
**Not a score.** C1 failed, so nothing is scored. These predictions are recorded now so that a later score on Huber 2004, or on a registered open-access substitute, compares against numbers fixed before the data were read.

**Design.** Reduced loop as registered. Deprivation ends at ZT 0 of the recovery day: 6 h is ZT 18-24, 12 h is ZT 12-24, 24 h is ZT 0-24. Baseline is the same day without deprivation. Output: `runs/s20/n25/sd.json`, with hourly time courses for any window.

**Sleep gained over baseline.**

| set | deprivation | sleep lost | gain, first 6 h | gain, 24 h | share of lost sleep regained in 24 h |
|---|---|---|---|---|---|
| mode 1, φ = CT 0 | 6 h | 266 min | 144 | 142 | 53 % |
|  | 12 h | 516 | 144 | 139 | 27 % |
|  | 24 h | 1092 | 144 | 138 | 13 % |
| mode 1, φ = CT 12 (V3) | 6 / 12 / 24 h | 360 / 576 / 1092 | 110 / 110 / 110 | 175 / 195 / 212 | 49 / 34 / 19 % |
| mode 0 (s10) | 6 / 12 / 24 h | 16 / 205 / 411 | −30 / 3 / 55 | 19 / −22 / 49 | not meaningful |

**What the table shows.**
- **Recovery barely depends on time awake.**
  - With φ = CT 0, the fly sleeps through the morning gap it is normally awake in (ZT 0-2). From there the recovery day matches the baseline day: the long day episode is circadian-gated, and S cannot exceed 1.
  - With φ = CT 12 the gain rises only from 175 to 212 min as deprivation goes from 6 to 24 h.
  - Mode 0 has no consistent rebound.
- **The model fails the qualitative claim.** Huber's abstract says recovery "was dependent on prior time awake", seen through the round-3 reader. On that the model fails as a structure, whatever the magnitudes turn out to be. The cap comes from fixed thresholds with long single episodes, not from the values.

**Register.** Huber 2004's qualitative direction is now seen; its magnitudes are unseen and unspent.

### s21 N25 held-out rebound test: Chowdhury et al. 2023 Fig. 1, registered before any magnitude is read (23 October, 00:53)

**Director (00:45).** Huber 2004's direction leaked, so it is now training context. Register Brown 2020 or Chowdhury 2023, whichever has the cleaner deprivation-length series.

**Choice: Chowdhury, Abhilash, Ortega, Liu & Shafer 2023 eLife 12:e91355 (PMC10642965, CC-BY).**
- It is the only one of the two with a deprivation-length series in one wild-type line and one sex: Canton-S males, vortexer in DAM, 6, 12 and 24 h.
- Brown et al. 2020 PLoS Genet 16:e1008270 has one duration (24 h), mainly in mated females, varied by method.
- The protocol came from a Sonnet reader that reported no outcomes, plus my own read of the Methods subsections only. The XML is pinned at `data/raw/chowdhury2023/PMC10642965_fullText.xml`, downloaded 23 Oct 00:52.

**Protocol (Methods, verbatim facts).**
- Flies: male Canton-S, 5-7 days old at loading, single in DAM tubes on 5 % sucrose / 2 % agar, 12:12 LD, 25 °C. One acclimation day, then 1 baseline day.
- Deprivation: vortexer shakes each DAM for 2 s at random, every 20, 120 or 220 s.
  - 24 h runs ZT 0-24, 12 h runs ZT 12-24 and 6 h runs ZT 18-24, so all end at lights-on of recovery day 1.
  - Arms (from the reader, legends): 6 h at 20 s (n 62) and 220 s (n 57); 12 h at 20 s (64) and 220 s (64); 24 h at 20 s (32), 120 s (64) and 220 s (64).
- Sleep: DAM beam crossings in 20 s bins, ≥ 5 min of inactivity.
- Rebound: (focal post − focal pre) − (unperturbed post − unperturbed pre), with total sleep per 24 h day. "Post" is days 1, 2 and 3 after deprivation, "pre" is the baseline day. Units: min per 24 h.
- Sleep during deprivation is measured: debt = deprivation-window 24 h sleep minus baseline 24 h sleep.
- Raw data: Dryad doi:10.5061/dryad.qnk98sfpp. **Not downloaded and not opened.**

**What is scored (spent once).**
- **Primary:** the 20 s arm, 24 h deprivation, day-1 normalised rebound (min).
- **Secondary:** the 20 s arm, 6 h and 12 h, day 1.
  - The 20 s arm is primary because it comes closest to the reduced loop's assumption of complete deprivation (activity forced to 1).
  - The 120 and 220 s arms are reported, not scored. Our model has no path by which the stimulus itself affects sleep, and that sleep-independent effect is the paper's own subject (validity limit).
- Our counterpart is the model's recovery-day sleep minus the same day without deprivation, with 24 h windows from ZT 0. That is exactly the "gain, 24 h" column of DECISIONS 23 Oct 00:34, and in an entrained model the unperturbed difference is 0.

**Pass rule (the Huber rule of 23 Oct 00:27, unchanged).**
- Compute each arm's group mean ± 2 SEM from the Dryad raw data with the paper's formula and the ≥ 5 min criterion. If the raw data cannot be read, use a blind figure read with its read uncertainty added.
- **Pass:** the primary point lies inside its span, and the 6 h and 12 h predictions both lie inside theirs (two-thirds of the other durations, which with two means both).
- **Also reported, not part of the pass:**
  - the ordering rule: the sign of 24 h − 6 h, wherever the data's difference exceeds 2 combined SEM;
  - the residual sleep during deprivation in each arm (the model assumes 0);
  - days 2 and 3.

**What the test is spent on.** Spent once, on the first candidate of the new homeostat structure (`docs/research/s21_n25_homeostat_scope.md`) that passes its implementation check and its training checks: baseline 618-1100 min/day, night > day, and the Liu 2016 anchors.
- The fixed 00:34 predictions for mode 0 and mode 1 are reported at the same read and spend nothing extra: mode 1 φ CT 0 gives 142 / 139 / 138 min; V3 gives 175 / 195 / 212; mode 0 gives 19 / −22 / 49 (6 / 12 / 24 h).
- **Falsifier:** if the primary point misses, the candidate fails as a rebound model. FINDINGS gets the miss and its direction, with no refit on Chowdhury.

**Leak, recorded honestly (00:52).** Printing the XML's section list also showed the Results and Discussion subsection titles. Their qualitative content is now **seen**:
- measured rebound depends on the stimulus frequency;
- with yoked controls, significant rebound appears with low-frequency triggers;
- rebound accumulates over multiple cycles, but little debt is paid off;
- short-bout sleep masks the rebound magnitude, and long-bout sleep is under potent homeostatic control;
- serotonin is a candidate sleep substance in the central brain.

**Not seen:** any magnitude, the dependence on deprivation length, and the Fig. 1 values. The ExR3 (5-HT) → dFB route in the scope was found in the connectome query at about 00:42, before this leak. The test stays usable but weakened, and it is marked so in the register.

**Huber 2004** stays training context, if Ben supplies the full text.

### s20 MB resting rates scored once against Huang 2024: PASS 6 of 9 (23 October, 01:01)
Scored as registered on 22 Oct at 22:23 (F-S21-1).
- **Fit:** σ*_DAN 1.477 and σ*_MBON 2.287 mV/√ms (fitted).
- **Confirm:** PPL105 and MBON14 sit inside their bands on seeds 12 and 13.
- **Huang 2024 (held out, now spent): 6 of 9 test types pass, the minimum for a pass.**
  - Fails: PPL1-γ1, MBON-γ1 and PPL1-α3, all low by ×0.23-0.44.
- **Not adopted tonight.** The class noise rows stay off in m10f. A stage with N21 off is next once the frontier merges, and fly2 is told of the resting DAN rates.
- **Deviation from the registration:** the whole-brain comparison used σ = 0.5, because no σ = 0 run was made.

### s22 N25 homeostat mode 1 built on the CPU; training fit and prediction protocol registered before any fit is run (23 October, 02:58)

**Director (23 Oct 01:10, and the session order).** Build the N25 reduced ER5/dFB loop on the CPU under its registration, behind a switch that is off by default. Item (1), the N26 and MB noise adoption, waits on fly2's merge.

**What is built (nothing adopted).**
- Switch `state:sleep|homeostat`, neutral 0 = the s10 process S with the hysteretic dFB threshold. Mode 1 (`internal_state.py`):
  - ER5 need n (BRP-like, Liu et al. 2016; their cells are called "R2" in the paper, R69F08-GAL4; the mapping to ER5/R5 is **inferred** from later naming). Awake n relaxes to 1 with τ_rise; asleep to 0 with τ_decay.
  - Each of the 8 dFB cells (FB6A_a/b/c and FB6E, 2 cells each in male-cns v1.0, measured) is a two-state unit. OFF → ON at k_r (1 + γ n) / (1 + γ); ON → OFF at k_off (1 + λ Lsat(light)). Transitions use the exact two-state probabilities over the step.
  - Sleep link (reduced loop only): asleep-capable while ≥ 4 of 8 cells are ON (guessed, the s20 convention of a dFB switch). In organism runs each dFB cell gets the dFB drive by its own state.
  - No clock input in mode 1. Validity limit: no rhythm in DD and no anticipation peaks; LD only.
- **k_r anchoring changed after the source read.** Pimentel et al. 2016 measured the restart (7 of 15 cells, 7-60 min, mean 25.86 ± 7.61 SEM min) in flies sleep-deprived > 12 h. So k_r = 1/25.86 min⁻¹ is the rate at full need (n = 1, **inferred**). Range [0.0106, 0.094] min⁻¹: the upper end is 1/(mean − 2 SEM); the lower end is the censored-exponential estimate if the 8 silent cells were held 60 min (the hold time is not stated).
- Implementation checks, all passed before this entry (`runs/s21/n25/unit.json`):
  - U1, OFF dwell of the model class at γ = 0: 25.83 min against 1/k_r = 25.84.
  - U2, stationary ON fraction 0.2889 against k_on/(k_on + k_off) = 0.2922 (tolerance 0.01).
  - U3, the vectorised probe loop against the Organs class (2 days, 200 vs 60 flies): 10.0 min apart in daily sleep, tolerance 3 combined SE = 25 min.

**Fit, registered now (script `scripts/probes/s21_n25_homeostat.py fit`, output `runs/s21/n25/fit.json`).**
- Fitted (shared, one value each, labelled fitted): τ_rise ∈ {1 … 48} h (12 values), γ ∈ {0 … 100} (11), k_off ∈ 0.001-0.9 min⁻¹ (12, log-spaced), λ ∈ {0 … 20} (9). 14,256 sets.
- Fixed: k_r 0.0387 min⁻¹ (measured, at n = 1 inferred); τ_decay 5.5 h (derived bracket 2.9-10.4 from Liu 2016); 8 cells; ≥ 4 ON; LD 12:12 at 1000 lux; 1-min steps; DAM scoring (inactive runs ≥ 5 min count whole).
- Stage 1, baseline (64 flies per set, 6 burn-in days, 2 scored days):
  - T1 total sleep inside 618-1100 min/day (the registered training range);
  - T2 night > day;
  - T4 Liu 2016 firing: mean need ZT13-15 / ZT0-2 ≥ 2. Firing about 3× in rested flies; if firing is affine in need with a non-negative offset, the need ratio is at least the firing ratio; 2 allows for "about".
- Stage 2, deprivation (128 flies per arm per set, on the stage-1 survivors): control, and 6, 12 and 24 h of forced activity ending at ZT 0 of recovery day R1 (6 h ZT18-24, 12 h ZT12-24, 24 h ZT0-24 of day S), days B, S, R1-R3.
  - T3 Liu 2016 BRP anchors on the 24 h arm, need excess over control: at +2 h ≥ 50 % of the excess at the end of deprivation, and at +24 h within ±10 % of it. Liu's own deprivation timing differs (vortexer 5 s per min; end time not recorded here); this is the loop's version.
- **Primary accepted set:** T1-T4, with the total also inside 1008-1100 min/day. That band is Abhilash & Shafer 2024 (Sleep 47:zsad277): Canton-S, w1118 and yw males in DAM, LD, "~70 % to 80 %" of 24 h asleep. It is seen training data from the same lab and line as the held-out paper (food differs: corn syrup/soy vs 5 % sucrose agar). **Variant:** the full 618-1100 band, reported.
- **Selection rule:** the candidate is the accepted set whose day-1 rebound predictions (6, 12, 24 h) lie closest (Euclidean, min) to the per-arm medians over the accepted set. Reported with it: the medians and the 2.5-97.5 % range over the accepted set. The training data do not pin γ well, so the range is part of the prediction and goes into the register.
- **Prediction (counterpart of the 00:53 registration):** rebound on day k = (focal Rk − focal B) − (control Rk − control B), 24 h windows from ZT 0, group means; day 1 scored, days 2 and 3 reported. The model's residual sleep during deprivation is 0 by construction.
- **Falsifier (before any held-out read):** no grid set passes T1-T4 in the primary band. Then the structure fails as built and FINDINGS records it; the wide variant is reported but cannot rescue the primary.
- Chowdhury 2023 Dryad stays unopened until the predictions are written into this file. Huber 2004 stays training context; no rebound magnitude is read from any source before then.
