#!/usr/bin/env bash
# Prior predictive of the vital-signs battery (weki, 8 Nov 2026; FIT_GENERAL.md sections 3 and 5). NOT A FIT: forward
# runs of worms drawn from the prior (brain.sample_worm(seed): each guessed number from its prior, known values fixed),
# scored against the opened bars of VITAL_SIGNS.md; nothing is tuned or adopted.
#
# Pre-registered 8 Nov 22:23 CST (date), before any run:
#   runs      seeds 1-6, condition food, 200 bio-s each, f8e7699 code, 3 at a time (2 waves).
#   reported  per sign: the 6 values, how many inside the band, and the template (seed None) value beside them; per draw:
#             physical, the per-neuron V-range activity check (neurons above 5 mV), and whether its values pass the
#             hard constraints (joint.check; reported, a draw is not rejected here).
#   question  is the quiet brain (PC3 0.056, GCaMP range 0.098, pumping 0 on the template) a property of the template or
#             of the prior? Read: "the prior reaches a sign" if at least 1 of 6 draws is inside its band. If none of the 6
#             reaches PC3 and GCaMP range, the EKI's first ensemble has no member near those observations (inferred
#             risk: the update moves inside the ensemble's span), and the fit needs a different start or a mechanism
#             fix first. The noise seed is the worm seed (mech/noise.py), so draws differ in values and noise both.
#   threshold "at least 1 of 6" guessed. A draw that fails physicality counts as outside every band.
# Added 8 Nov 22:25 CST (date), before any run result was read: joint.check passes only seeds 1 and 4 of the 6 (2, 3, 5,
#   6 break a reversal-order constraint; 230 of 560 prior draws admissible, 41 %, measured). A third wave runs the next
#   3 admissible seeds, 7, 9, 10 (the fit runs only admissible members), launched after the first two waves:
#   `$PY -m wormemu.fit.vitals run food 200 OUTDIR/seed$k --seed=$k` for k in 7 9 10. The question is then read on the
#   5 admissible draws (1, 4, 7, 9, 10) as well as on all 9.
# Added 8 Nov 23:24 CST (date), before any run result was read (wave 1 still running, no seed output opened): the
#   imaging noise obs_noise_dff is one of the drawn numbers (0.035-0.176 over these 9 draws, measured from
#   sample_worm on f8e7699), and white noise of SD s alone gives a per-neuron P95 - P5 of 3.29 s: seed 1's 0.176 gives
#   0.579, inside the gcamp_range bar (0.567-0.983), with no brain activity. So the table also reports per draw:
#   obs_noise_dff; the noise-only range 3.29 x obs_noise_dff; the GCaMP signal SD (vitals.noise_sd's signal part, on F /
#   mean F of the stored 50 ms traces resampled at 0.600 s, median over neurons); and the range the same signal would
#   give under Atanas's own noise (0.0417, atanas_noise.py), 3.29 x sqrt(signal^2 + 0.0417^2) (Gaussian approximation,
#   derived). Reading: a draw "reaches gcamp_range from the brain" only if it is in band AND its noise-only range is
#   below the band's low end; an in-band draw whose noise alone reaches the band is reported as "noise-reached" and
#   does not count. pc3_frac is read as registered (white noise only lowers it).
# Usage (backhouse, after sourcing env.sh): bash scripts/worm/fit/prior_predictive.sh OUTDIR
set -u
OUT=$1
mkdir -p "$OUT"
for wave in "1 2 3" "4 5 6"; do
  pids=()
  for k in $wave; do
    $PY -m wormemu.fit.vitals run food 200 "$OUT/seed$k" --seed=$k > "$OUT/seed$k.log" 2>&1 &
    pids+=($!)
  done
  echo "wave $wave pids ${pids[*]} $(date +%H:%M)" >> "$OUT/pids.txt"
  wait "${pids[@]}"
done
touch "$OUT/DONE"
