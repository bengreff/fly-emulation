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
