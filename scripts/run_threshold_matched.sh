#!/bin/zsh
# F8b. The model scales spike threshold with soma size. Proprioceptors are 0.44x
# the median size, so a flat injected current is a 2.1x larger perturbation to
# them than to a typical interneuron. This repeats the drive-target comparison
# with each cell's current scaled by its own threshold, so every driven cell is
# pushed the same fraction above threshold.
set -u
LOG=runs/threshold_matched.log
: > $LOG
for A in 5 12.5; do
  for T in proprioceptors random_interneurons; do
    echo "===== A=$A target=$T threshold-matched $(date -u +%H:%M:%S) =====" >> $LOG
    uv run python scripts/pugliese_conditions.py --condition baseline \
        --replicates 8 --rtol 2e-6 --atol 5e-9 --sensory-amp $A \
        --threshold-matched --drive-target $T >> $LOG 2>&1
  done
done
echo "THRESHOLD MATCHED DONE $(date -u +%H:%M:%S)" >> $LOG
