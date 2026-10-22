SEALED FILE — Part C values (Berry, Phan & Davis 2018 Cell Rep 25:651, PMC6239218 Fig 5H-I;
Hige, Aso, Modi, Rubin & Turner 2015 Neuron 88:985, PMC4674068 Fig 1H/1I/1J)
Read 2026-10-22 from downloaded figure JPEGs in /tmp/fly2n/figs/ (berry_f5.jpg, hige_f1.jpg).
All values are "figure estimate" (read off plotted bars/points with ruler-by-eye on a
cropped/upscaled PNG), not text-stated numbers, unless marked [text].

=====================================================================
1) HIGE ET AL. 2015, Figure 1 (G-J): BACKWARD PAIRING, MBON-γ1pedc
=====================================================================
Protocol [text, from legend + Results + STAR Methods]:
- Cell: MBON-γ1pedc (a.k.a. MB-MVP2), in vivo whole-cell recording (current clamp for
  spikes; same prep as forward pairing in 1A-F).
- DAN: PPL1-γ1pedc, CsChrimson (MB320C split-GAL4 driver), 627 nm LED, 14.7 mW/mm^2.
- Backward pairing protocol (Fig 1G): 4 light pulses, 1 ms duration each, delivered at 2 Hz
  (i.e., spanning ~1.5 s). Odor (1-s pulse, OCT or MCH) delivered 0.5 s AFTER the LAST of
  the 4 light pulses (so DAN activity strictly precedes odor/KC activity — "unpaired"/
  backward order, opposite of the forward CS->US order used in 1A-F).
- This is a SINGLE pairing trial (one bout of 4 pulses + one later odor pulse), not a
  repeated/multi-stimulation protocol.
- Pre-pairing baseline: 5 (range 3-10) interleaved odor presentations (both OCT & MCH),
  25-s ISI. Backward-pairing trial given 1 min after last pre odor pulse. Post-pairing
  responses recorded starting 1-1.5 min after the backward-pairing trial; each odor
  presented ~5 times (>=3) interleaved, 25-s ISI.
- n = 7 flies/cells (same cells also shown in Fig 1D-F forward-pairing dataset? no —
  separate experiment, same n=7 reported for Fig1 E/F/I/J per legend/text).
- Quantity plotted: (I) mean PSTH (spikes/s) vs time, ±SEM shading, n=7.
                     (J) mean odor-evoked spike count (number of spikes in the 1.4-s
                     response window, spontaneous rate subtracted), ±SEM, Pre vs Post,
                     individual fly lines in gray, bars/points not normalized (raw spike
                     counts, not a ratio or %).
- Two columns in H/I/J = the two test odors; based on column order matching panels D-F
  (which show OCT left/MCH right), left = OCT, right = MCH. (Not 100% certain which odor
  was "CS+" in the backward protocol since backward pairing has no CS+/CS- distinction
  functionally — text just says "the same two test odors".)

Figure-estimate values (Fig 1J, mean odor-evoked spike count ± SEM; reading error ~±5
spikes given bar/whisker thickness at this image resolution, 800x395 px full figure):
- Left column (OCT): Pre ≈ 93 ± 12 spikes/s-window; Post ≈ 100 ± 10. Individual fly lines
  (gray) mostly flat/slightly up.
- Right column (MCH): Pre ≈ 83 ± 10; Post ≈ 80 ± 8. Individual fly lines flat/slightly down.
- No bar pair shows a visible gap large relative to the error bars; this matches the text
  statement "Backward pairing showed no effect (p > 0.05, repeated-measures two-way ANOVA)".
- PSTH panel (I) peak amplitude for both Pre and Post traces (both odors) ≈ 110-130
  spikes/s at peak (~0.3 s), visually near-superimposed Pre vs Post traces.

=====================================================================
2) BERRY, PHAN & DAVIS 2018, Figure 5 H-I: MBOn-γ2α'1, Paired>Decay vs Paired>Unpaired
=====================================================================
Protocol [text, from legend + STAR Methods "Optogenetic Protocols for In Vivo Imaging"]:
- DAN: DAn-γ2α'1 (MB296B-GAL4), ChrT (Chrimson::tdTomato). MBON: MBOn-γ2α'1
  (R25D02-LexA), GCaMP6f, two-photon imaging of axon (scan box positioned to avoid direct
  ChrT excitation).
- Base odor-pulse protocol: 5 s MCH then 5 s OCT, 45-s inter-pulse interval, 15 trials
  total (same timeline as Fig 4C odor-shock protocol, but light substituted for shock).
- "Paired" (Learn phase, trials 3-5): 6 LED pulses of 1 ms duration at 2 Hz (~3-s train,
  consistent with the 3-s/2-Hz train characterized in Fig 5C/D), delivered starting 1 s
  after the start of the MCH odor pulse, on trials 3, 4, and 5 (one pairing per trial,
  i.e., 3 paired trials total during Learn).
- "Unpaired" (Forget phase, trials 8-10, "Paired > Unpaired" condition only): same 6-pulse/
  1-ms/2-Hz LED train, now delivered starting 22 s BEFORE the MCH pulse, on trials 8, 9,
  and 10 (3 unpaired trials total during Forget). This directly follows the Learn-phase
  pairing (trials 3-5) in the same fly — i.e., DAN-only activation delivered onto an
  already-depressed MBOn-γ2α'1 input.
- "Paired > Decay" condition: light given only during Learn (trials 3-5, paired), nothing
  during Forget (trials 8-10) — spontaneous/no-DAN comparison for recovery over the same
  elapsed trial/time window.
- "No LED" condition: no light at any point (full negative control for the optogenetic
  manipulation itself).
- Odor tested at Pre (before trial 3), Post 1 (after trial 5 / before trial 8), Post 2
  (after trial 10, within trials 11-15 window) — exact trial(s) used for each probe not
  stated beyond "same timeline as Figure 4C".
- Quantity plotted: Activity(t) = 100*(F(t)-F0)/F0 (%ΔF/F0), F0 = mean signal in the 5 s
  before odor onset; panel I = mean %ΔF/F0 during the 5-s odor exposure window, ±SEM.
  Top row of I = response to MCH (the paired/CS+ odor); bottom row = response to OCT
  (odor not paired with light, control odor).
- n = 8-9 flies per condition/odor (legend states "n = 8-9").
- Stats: two-way repeated-measures ANOVA, Bonferroni post hoc; significance markers shown
  per bar-pair in the image (exact p-value thresholds not fully legible without further
  zoom beyond */**).

Figure-estimate values (Fig 5I; bars read off a ~1480x800 px crop; y-axis gridlines at
0/75/150(top)/0/50/100/150/200(bottom); reading error roughly ±5-8 %ΔF/F0 units for bar
heights, ±5-10 for error-bar extents given line thickness):

MCH (top panel, paired/CS+ odor), mean %ΔF/F0 ± SEM, n=8-9:
- No LED:          Pre ≈ 148 ± 18,  Post1 ≈ 150 ± 20,  Post2 ≈ 163 ± 25   (ns across all)
- Paired > Decay:  Pre ≈ 232 ± 15 (bar top just above the 225 gridline; ** vs Post1),
                    Post1 ≈ 18 ± 10,  Post2 ≈ 55 ± 18
                    (Pre vs Post1 **, Post1 vs Post2 ns, per bracket annotations)
- Paired > Unpaired: Pre ≈ 148 ± 15,  Post1 ≈ 8 ± 5,  Post2 ≈ 112 ± 30
                    (Pre vs Post1 **, Post1 vs Post2 *, Pre vs Post2 ns, per brackets)

OCT (bottom panel, unpaired/control odor), mean %ΔF/F0 ± SEM, n=8-9:
- No LED:          Pre ≈ 138 ± 25,  Post1 ≈ 160 ± 35,  Post2 ≈ 100 ± 25   (ns)
- Paired > Decay:  Pre ≈ 172 ± 20,  Post1 ≈ 117 ± 22,  Post2 ≈ 88 ± 20    (ns)
- Paired > Unpaired: Pre ≈ 113 ± 25,  Post1 ≈ 75 ± 12,  Post2 ≈ 61 ± 18   (ns, bracket over
                    whole group marked ns)

Qualitative pattern visible in the image (described structurally, not as an effect size
per instructions — for internal modelling use only): for the MCH/paired odor, "Paired >
Decay" and "Paired > Unpaired" both drop sharply from Pre to Post1 (consistent with
LTD during Learn); Post2 differs between the two conditions, Post1->Post2 comparison is
starred (*) only in "Paired > Unpaired", ns in "Paired > Decay". OCT (control odor)
shows no starred comparisons in any condition/timepoint.

Reading-error caveat: image resolution (800x1007 px full figure; crops upscaled ~3-4x)
limits precision; treat all above numbers as ±10-20% of the stated value, and bar/error
positions near axis gridlines are more reliable than those between gridlines.
