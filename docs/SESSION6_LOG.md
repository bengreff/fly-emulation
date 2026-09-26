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
