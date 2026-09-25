# Mechanosensory transduction: evidence for wiring the senses

Session 5, from a bounded literature extraction (read-only agent), not yet
independently verified line by line. Labels: **M** measured, **D** derived,
**I** inferred. DOIs marked (unverified) were not confirmed by lookup.

## What the data give per organ

| Organ / subtype | Encoded variable | Tuning and dynamics | Readout in source | Label |
|---|---|---|---|---|
| FeCO claw (flexion) | tibia angle, flexed side | tonic; population 90°→18°; per-cell half-activation spread ~20-80° along a goniotopic map; hysteresis, larger when approached from flexion (Mamiya 2018, 2023) | GCaMP calcium, no spikes | M (calcium) |
| FeCO claw (extension) | tibia angle, extended side | tonic, 90-180°, reverse and noisier map | calcium | M |
| FeCO hook (flex/ext) | movement direction | phasic, fast-decaying; hook-flexion DSI 0.81 ± 0.03 | calcium (too slow for velocity tuning) | M; velocity gain I |
| FeCO club | vibration, bidirectional movement | DSI 0.12; responds to 2 kHz; tonotopic 100-1600 Hz; claw threshold > 10x club | calcium | M |
| FeCO mechanics | arculum splits motion: lateral tendon to club, medial to claw/hook | FE model: claw dendrite strain 0.10→0.26 ΔL/L over 170°→10°; constant strain threshold reproduces the goniotopic map (Lee et al. 2025) | model | M/D |
| Hair plates (coxa CxHP8; trochanter HP5-7) | ThC / CTr angle near limit | tonic, no phasic tuning (Pratt et al. 2026) | calcium | M qualitative |
| Leg campaniform sensilla | cuticular strain, force and dF/dt | fields mapped (Dinges 2020); blowfly spikes: force and rate, hysteresis, suppressed by force decrease (Zill et al.) | spikes, other species | M (other species) / D |
| Leg bristles | shaft deflection | onset burst plus sustained firing (Walker et al. 2000, NompC) | spikes | M qualitative; time constants I |
| JO-A/B | a3 rotation velocity (near-field sound) | A+B 19-952 Hz; B prefers low frequencies; A gives nm sensitivity (Kamikouchi 2009; Matsuo 2014; Patella & Wilson 2018) | calcium, CAPs | M |
| JO-C/E | sustained a3 deflection (wind, gravity) | tonic; forward deflection excites anterior and inhibits posterior neurons, and the reverse (Kamikouchi 2009; Yorozu 2009) | calcium | M; per-type push/pull I |
| JO in flight | wingbeat-frequency antenna oscillation | strong oscillatory and weak tonic responses (Mamiya & Dickinson 2015) | calcium | M |
| Antenna pair | wind azimuth | left-right difference is linear in azimuth (Suver et al. 2019) | ephys and tracking | M |
| Haltere / wing CS | Coriolis and wingbeat strain | haltere dF2 gives phase-locked monosynaptic EPSCs in b1 MN, mixed electrical/chemical (blowfly; Fayyazuddin & Dickinson 1996) | EPSCs | M (Calliphora) |

## Gaps that stay open

- **No SNpp-to-claw/hook/club crosswalk exists.** Subtypes were identified in FANC (Lee et al. 2025), not MANC or male-cns; assigning them needs morphological matching (I).
- **Every FeCO and hair-plate result is calcium.** Absolute firing rates cannot be calibrated from them; rate gains stay inferred (F-GAP-1).
- Coverage in male-cns (D): the front leg has far fewer chordotonal axons (~60) than the ~150 per leg expected, so the front-leg FeCO reconstruction is incomplete. Only 86 of 426 campaniform neurons map to a leg ROI.
- **403 "leg" mechanosensory neurons are not driven** (proprioceptive/leg 190, tactile/leg 213).

## Recommended transduction models (all I unless stated)

1. Claw: per-cell sigmoid of FTi angle with thresholds spread over the measured ranges, better driven by the FE strain proxy (D); add direction-dependent hysteresis.
2. Hook: rectified high-passed velocity of the preferred sign; time constant unmeasured.
3. Club: band-passed tibia vibration per best frequency. Needs a ≤ 0.3 ms physics step or a separate vibration channel.
4. Hair plates: tonic sigmoid near the ThC/CTr limits, not the FTi joint.
5. Campaniform sensilla: a·F + b·dF/dt of local strain, suppressed on force decrease.
6. Bristles: high-passed contact plus a small tonic term.
7. JO-A/B: band-passed a2-a3 rotation velocity. JO-C/E: tonic signed a3 angle, opposite signs for anterior and posterior cells. Needs a driven a2-a3 hinge in the body (flybody has antenna DOFs; check which).

## References (as reported)

Mamiya, Gurung & Tuthill 2018 Neuron 10.1016/j.neuron.2018.09.009 · Mamiya et al. 2023 Neuron 10.1016/j.neuron.2023.07.009 ·
Lee et al. 2025 Nat Commun 10.1038/s41467-025-59302-3 · Pratt et al. 2026 Nat Commun 10.1038/s41467-026-69333-z ·
Dallmann et al. 2025 Nature 10.1038/s41586-025-09554-2 (unverified) · Dinges et al. 2020 J Comp Neurol 10.1002/cne.24987 ·
Zill et al. 2025 J Neurophysiol 10.1152/jn.00044.2025 · Tuthill & Wilson 2016 Cell 10.1016/j.cell.2016.01.014 ·
Walker et al. 2000 Science 10.1126/science.287.5461.2229 · Kamikouchi et al. 2009 Nature 10.1038/nature07810 ·
Yorozu et al. 2009 Nature 10.1038/nature07843 · Matsuo et al. 2014 Front Physiol 10.3389/fphys.2014.00179 ·
Mamiya & Dickinson 2015 J Neurosci 10.1523/JNEUROSCI.0034-15.2015 · Patella & Wilson 2018 Curr Biol 10.1016/j.cub.2018.02.074 ·
Suver et al. 2019 Neuron 10.1016/j.neuron.2019.03.012 · Fayyazuddin & Dickinson 1996 J Neurosci 10.1523/JNEUROSCI.16-16-05225.1996
