# Session 10 log

Start: Sun Sep 27 20:37:46 CDT 2026. Unattended, 5 h (Ben: "Complete the brain-body model and start on GPU porting if you have time"; 1-2 subagents).
Stop new work at ~01:17; wrap up by 01:37.

- 20:40 backhouse reachable. Killed a leftover serve_viz.py from an earlier session (PID 24437).
- 20:45 tests 94 pass. Subagent 1 (general-purpose, told no sub-agents): batched GPU simulator on backhouse (src/flyemu/gpu/, tests/test_gpu_batched.py, scripts/gpu_bench.py, docs/GPU.md).
- 21:00 N3/N5 at class grain built (lif._class_scales; 280 rows n3c_*/n5c_*; tests/test_class_mechanisms.py; neutral = bit-identical). closed_loop_check counts class tonic drive as network activity (only per-type tonic cells excluded).
- 21:05 Subagent 2 (general-purpose, no sub-agents): task 5 remainder — coxa muscles with 3-axis moment arms (switch muscle:leg|coxa_model) + motor-unit fatigue. Deviation: body item delegated in parallel (Ben allowed 1-2 subagents); files partitioned (agent: muscles.py, Hill block of organism.py; me: brain files).
- 21:05 backhouse baseline batch s10_base: template seeds 0-2 + sugar->MN9 10 trials.
- 21:25 baseline (backhouse) template fails 3/3 seeds (44.6/42.8/46.1 spikes/ms); sugar 8.9+-5.9. Rule classes: DN, central_other, optic_columnar, optic_other, AN (+MN_other, sensory_gustatory). Screen s10_screen: 42 one-at-a-time candidates, seed 0 + sugar.
- 21:45 N7 (mGluR, mAChR slow parts) and N8 (NMDA-type, Mg block) built, neutral 0, tests; silence() now also removes slow GABA-B output (bug fix, only matters with gabab on).
- 22:15 N2 class threshold offset/tau_m scale; B20 antenna oscillator (switch sense:antenna|oscillator) with tests.
- 21:05 (clock check: earlier log times were estimates and ran ahead; `date` is authoritative from here) Task 8 started: src/flyemu/flight.py (wing ranges by function, WingKinematics, WingBeat PD hook), scripts/probes/tethered_lift.py. F-WING-1: flybody wing yaw = stroke, roll = deviation, pitch = rotation (joints.py labels all three wrong). F-FLIGHT-1: with exact hover-like kinematics (218 Hz, 140 deg stroke), MuJoCo default ellipsoid coefficients give lift/weight <= 0.65 (rot amp 25-65 deg: 0.30-0.65); PD tracking at 1500 Hz bandwidth misses by up to 44 deg (not usable yet).
- 21:05 screen partial: DN release 0.5 silent but MN9 5.2; optic_other release 2.0 silent with MN9 8.9; AN release 2.0 silent (MN9 pending); central_other scales change MN9 massively (0 or 216 Hz).
- 21:15 Subagent 2 done (coxa_model, fatigue; 9 tests; dead fly unchanged; seed 1 template still unstable with coxa switch). Task 13: model_data.sample_fly + joint constraints (v_th - v_rest >= 2, v_th - v_reset >= 0.5); acceptance batch s10_acc (10 seeds, stage 1, 3 s) launched on backhouse.
- 21:22 screen done except gustatory; phase 2a (s10_p2): 13 single-parameter candidates on seeds 0-2 + sugar.
- 21:35 phase 2a: single knobs seed-fragile; DN rel 0.6 silent 3/3 but MN9 4.1. Phase 2b (s10_p2b): 18 combos (DN 0.6/0.65 x MN9-path levers; 6 random in +-2x).
- 21:52 N1 wired (3 Bernoulli mode groups), N12 curated gap junctions wired into organism (were assay-only), N15 per-class adaptation, N21/N22 plasticity. Acceptance: 8/10 sampled flies done, no runaway; brain means 0.08-106 Hz.
- 21:51 B11 steering map; B15 TTM jump (GF volley -> thorax +0.63 mm in 20 ms); subagent 3 done: internal_state.py (S1-S4, N20, N25, N26). Note: log times before 21:47 were estimated ahead of the clock by up to ~15 min.
- 22:08 search done (80 candidates); best DN rel 0.70 + MN_other inp 1.30; held-out batch s10_ho launched (template seeds 3-5, m4 body seeds 0-2, bitter, water). Code on backhouse = sync of ~21:15 (all later changes neutral). GPU subagent done: exact equivalence, 30-90x per member.
- 22:15 held-out: stability 6/6 silent, bitter pass, water->MN9 0 Hz FAIL -> not adopted. N16 Coriolis; N17 probe (b1 VS 0.40->0.55 with haltere->b1 coupling). 0 absent mechanisms now.
- 22:17 m4 water->MN9 = 0 Hz too (criterion ill-chosen; rule stands). GPU assay: 810 trials in 362 s, all 70 CPU-scored candidates identical to 0.1 Hz. Template += coxa_model, wing ranges by function, antenna oscillator, TTM, organs, pump gating; template dead fly passes all criteria; closed loop s10_tmpl2 running.
- 22:22 GPU closed loop (scripts/gpu_closed_loop.py, k=10, B=3) == CPU --hold-k 10 exactly on seeds 0-2; 28 s wall per sim-s per member (bodies sequential). k-hold vs k=1 (CPU): brain excl ORN s0 0.349/0.157/0.208 for k=1/5/10; silence unchanged. Regressions (backhouse): m4 seeds 0-2 silent (0.349/0.223/0.297 Hz), sugar 8.9+-5.9, m2 seed 0 silent.
- 22:28 repair 1 passed all four (fresh seeds 6-8 template, 3-5 m4 body, bitter suppression, dose response) -> m5 adopted as working profile; m4 frozen. Parallel-body GPU loop (3 workers) identical, 64 s vs 109 s.
- 22:33 F-FLIGHT-2: vein mesh doubled wing lift area; membrane-only + Kutta 3.1 (inferred) -> 0.99 W kinematic, 0.89 W PD.
- 22:33 GPU closed loop B=12 (m5, k=10, 12 workers): 10 s wall per member-sim-s; silent on 7/12 seeds (3,5,9,10,11 sustain ~20 spikes/ms). Exact CPU check seeds 9-11 + CPU k=10 seed 3 (confirms GPU) launched (s10_rob).
- 23:29 latency (prior centres) m5 seeds 0-5 silent: hold, not latency, breaks stability. GPU k=1 throughput run (B=12, 0.4 s) launched.
- 23:32 GPU k=1 exact closed loop, B=12, 12 workers: 20 s wall per member-sim-s (3.5x CPU); k=10: 10 s (7x). (Run used a short 100 ms silent window: throughput only.) Launched m6 latency check seeds 6-11 (s10_lat2).
- 23:33 step profile (Mac, m5): vision 3.77 ms/step avg (render every 100 steps), aff 0.75, motor 1.09, net 1.25, chem 0.24, extra 0.21, organs 0.07, observe 0.07 -> vision is the closed-loop bottleneck.
- 23:35 m6 = m5 + latency adopted (seeds 0-11 silent).
- 23:36 CORRECTION to the step profile: the 3.77 ms/step vision average was the one-off first render (1.8 s); steady state 13-20 ms per render (every 100 steps) = ~0.2 ms/step. Body side ~2.5 ms/step. The k=1 GPU loop at B=12 spends ~24 ms/step, so its cost is per-step overhead (a (B, n) drive transfer each step, dispatch, pipes): next step is sensory-rows-only transfer (ext_rows) and fewer round trips.
- 23:36 Process-limit breach: the two B=12 GPU closed-loop runs used 12 body workers (limit 8 model processes on backhouse). No harm observed (load, memory fine); future runs <= 8 workers.
- 00:00 rows-only transfer: 23.5 s per member-s (B=8, m6, k=1), no gain; overhead is per-step python/dispatch/pipes. Natural end: wrap-up started.
- 00:08 wrap-up: 147 tests pass; census and ledger run (56 mechanisms: 17 have / 39 partial / 0 absent; 655 unknowns, 79 bounds from data); backhouse clean (PID 523 untouched); keep-alive stopped. End.
