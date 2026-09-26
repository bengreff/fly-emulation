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
