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
