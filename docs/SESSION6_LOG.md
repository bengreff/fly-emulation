# Session 6 log

Start: Fri 25 Sep 2026 21:11 CDT (Mac `date`). Stop new work at 23:56; wrap-up by 00:11.
Ben was present at start and approved: "Do standing and filling in values from research,
walking (stretch goal) and more biological fidelity... lean towards as written, build the
foundation." Order: priority 1 (measurements), 2 (standing), 3 (absent mechanisms).

## Timeline
- 21:11 start. Read prompt, findings, decisions. Dispatched one Explore agent (literature leads → docs/LIT_SESSION6.md).
- 1a: fetched 11,751 skeletons (one per type) + 300 presynapses each (neuPrint, ~5 min, 12 threads). Delay = 0.5 ms + L/v.
  GF check: 549 µm at measured 2.07 m/s → 0.27 ms vs measured GF conduction 0.29 ms (Kadas 2019).
- 1b: Hallem 2006 SFR/Rmax for 24 receptors from DoOR unit files; ORNs now Poisson at calibrated rates
  (a noise-free LIF cannot fire at 1-2 Hz from constant drive: found while testing).
- Regression (pre-registered): sugar→MN9_L 26.3/86.3 Hz (was 7.5/93.5; passes >5 Hz); closed loop stable,
  whole brain excl. ORN 0.24 Hz, uPN mean 5.9 Hz but median 0 (only 33% of PNs active). Adopted.
- 1c: per-MN torque per spike for 308 leg MNs (data/params/motor_forces.csv). Tibia flexor (Ti flexor +
  Acc. ti flexor, ~13/leg) classed fast/intermediate/slow by EM-volume rank; Azevedo 2020 forces × tibia
  length (derived). Others size-scaled (F ∝ V^5.1, inferred). Per-MN twitch tau (30/100 ms, guessed).
- **Regression failure found (F-ORN-2):** with Hallem ORN spontaneous rates, 3/6 seeds enter a self-sustaining
  state (~1,700 cells: optic-lobe Mi18/Lawf2/Pm/Dm, DNg12/DNge019) that survives silencing all senses. The
  session-5 baseline and delays-only never do (deterministic). The earlier seed-0 pass was luck.
  Per pre-registration: ORN rate calibration kept as option, **off by default**. Delays + forces pass.
- 1d: data/params/opsin_spectra.csv (Salcedo 1999 ERG λmax, measured; Govardovskii template in vision.py);
  renderer gets per-eye pale/yellow masks from the derived R7/R8 assignment (PerEyeRetina).
- 21:47 standing pre-registered (DECISIONS). Found and fixed two bugs on the way:
  (1) sensory.py read "FTi" proprioception at the actuator index into joint_angles (102 dofs vs 98 actuators)
      → every leg's FTi afferents actually read thorax-coxa roll since session 2/3;
  (2) body.py applied the anatomical femur-tibia range 18-180° directly to q; q=18 is geometric 113°, so knees
      could not flex below neutral and the fly started clamped at the limit. Now mapped through geometry.
- Measured-form proprioceptors (claw/hook/club/hair plate). First run tipped over (promotor MNs 88 Hz): guessed
  hair-plate/claw directions formed positive feedback. Directions then inferred from wiring under a
  resistance-reflex prior (post-hoc, recorded). Slow flexor MNs given measured 30 Hz rest rate (derived drive).
- Standing FAILS: z_min 0.774 mm (limp 0.675; criterion 0.90). Resistance reflex ABSENT in closed loop:
  a 34° imposed flexion raises lm claw 6→18 Hz and hook-flex 0→25 Hz, but Ti extensor stays 0 Hz and flexor
  18→19 Hz. Open loop the wiring does resist (claw-flex 40 Hz → extensor 0→4 Hz, flexor 12→9 Hz). Failing layer:
  afferent→premotor→MN gain (efficacy 0.165 mV global; FeCO absolute rates unmeasured).
- Re-measured joint-sign calibration for the corrected body (neutral no longer at the FTi limit): 5 secondary
  components flip (hind ThC/CTr fore-aft, rf coxa lateral); 12/66 dominant actions change. Adopted.
  With it the fly tips (roll 52°, z_min 0.64). Standing outcome is sensitive to hind-leg ThC sign; fails either way.
- 22:15 Priority 3: glutamate sign per target, GABA-B share, presynaptic inhibition (sensory terminals),
  DAN-gated KC→MBON LTD — all simulated, neutral/off by default, tested.
- 22:24 Wrap-up checks: sugar→MN9_L 26.3 / 84.3 Hz (100/200 Hz); closed loop stable (0.34 Hz, 0 non-tonic
  spikes after silencing); 42 tests pass; Registry.validate() [] (tested); ledger + census re-run.
  Ledger delta (parameter scale): filled 548 → 13,325; default 408,528 → 439,573; absent 385,211 → 342,083.
- 22:31 F-ORN-2 re-examined: attractor absent under the post-fix model (seeds 0-5); pre-registered fresh-seed
  re-test 6-11 → 6/6 pass → ORN Hallem rates ON by default (F-ORN-3). Rule v2 re-run under delays: 0.165 mV
  still the calibrated scale (F-CAL-3).
- 22:37 Second Explore agent: Azevedo 2020 reflex numbers exist only in figures. Dryad raw data blocked (API needs a
  bearer token; no account created). Reflex-gain protocol built (tethered, PD probe); VNC efficacy scale added
  (neutral default); sweep ×1.5–3 does not reproduce slow-MN position sensitivity — not adopted (F-REFLEX-1).
- 22:47 Exploratory DNg100 closed-loop stimulation: no stepping (F-WALK-0).

## End
End of work: Fri 25 Sep 2026 22:49 CDT. All wrap-up steps done; everything committed and pushed.

**Done:** 1a delays (derived, 11,751 types); 1b Hallem ORN rates (measured, on after re-test); 1c Azevedo
motor-unit forces (derived/inferred); 1d opsin λmax + connectome eye mask; 2 standing attempted with measured-form
proprioceptors, slow-MN rest rate, reflex probes; 3 four absent mechanisms simulated (neutral defaults).
**Failed:** standing (0.745–0.79 mm vs 0.90 criterion); closed-loop resistance reflex absent; DNg100 → no stepping.
**Bugs fixed:** FTi proprioceptors read the wrong joint; femur-tibia range applied to the wrong coordinate.
**Ledger delta (parameter scale):** filled by data 548 → 13,325 (+12,777, mostly derived delays); absent 385,211 →
342,083 (−43,128 moved to simulated-on-default); default 408,528 → 439,573.
**Blocked:** Azevedo 2020 raw data (Dryad API requires a bearer token); 1e (per-type measured electrophysiology)
not started. backhouse was reachable but not needed (all runs fit on the Mac).

# Session 6b (26 Sept, Ben present at start; 2 h budget)
Start 06:32 CDT. Ben downloaded Azevedo 2020 Dryad cell 180111_F2_C1 (slow MN, R35C09, PiezoRamp2T at 5 offsets).
- 06:40 Extracted targets from 180111_F2_C1 (scripts/azevedo_slow_mn.py; derived CSV/JSON). Fitted slow-MN LIF to
  intrinsic data (tau 16 ms measured; theta 32.6 mV, t_ref 4.27 ms, drive 36.45 mV fitted). Pre-registered
  held-out reflex test (DECISIONS 6b).
- 06:40-07:10 Held-out reflex test failed (+1 vs +20.3 Hz). Three pre-registered post-hoc repairs (afferent rate mode,
  VNC scale, glutamate sign on flexor MNs) each failed on the fit target; none adopted. Diagnosis: premotor
  excitatory INs silent, 5-10 mV below threshold, under tonic GABA from IN13A005 (F-AZ-2). Stopped fitting on this
  target (three post-hoc attempts). Slow-MN intrinsic fit adopted (reproduces measured f-I). Stability 6/6.
- 07:10-07:30 Third Explore agent: slow-MN spontaneous rate is synaptically driven (Azevedo); GluCl dominant in MNs
  (Lesser 2024) — consistent with rejecting the glutamate hypothesis. Agrawal 2020 raw data found on Zenodo (CC0,
  7.5 GB, throttled <1 MB/s): fetched selected members by HTTP range requests (scripts/fetch/zenodo_zip_members.py).
  F-VNC-1: real 13B/10B/9A interneurons rest at -40..-53 mV with graded angle coding; model VNC pinned at V_rest.
- 07:30-08:02 13Balpha ramp-and-hold fetched; static tuning extracted (15 cells, 0.046 mV/deg). Model 13B flat (T1).
  Pre-registered grid fit failed; confound: male-cns front legs have 2-3 claw axons (vs 25-32). Exploratory T2: tuning
  appears with rate-coded afferents but mixed-sign (F-VNC-2). Note: one commit ("Log and plan: VNC data route") went
  out without the Co-Authored-By line; history not rewritten per project rules.

## End 6b
End: Sat 26 Sep 2026 ~08:05 CDT. Adopted: slow-MN intrinsic fit (Azevedo raw data). Not adopted (failed, pre-registered):
afferent rate mode, VNC efficacy scale, excitatory glutamate onto flexor MNs, VNC grid fit to 13Balpha tuning.
New measured targets: slow MN (F-AZ-1), VNC interneurons (F-VNC-1/2). Key diagnosis: model VNC sits at rest (1-2%
firing); real premotor/interneurons are depolarised and graded; front-leg claw afferents missing from male-cns.
