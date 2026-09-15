#!/bin/zsh
# Control for F7/F8: is the rhythm broken by the sensory pathway specifically,
# or by any added excitation? Same per-neuron amplitude into 102 randomly chosen
# intrinsic neurons instead of the 102 proprioceptors. Three target seeds.
set -u
LOG=runs/drive_control.log
: > $LOG
for A in 5 12.5; do
  for T in proprioceptors random_interneurons bristles; do
    echo "===== A=$A target=$T $(date -u +%H:%M:%S) =====" >> $LOG
    uv run python scripts/pugliese_conditions.py --condition baseline \
        --replicates 8 --rtol 2e-6 --atol 5e-9 --sensory-amp $A \
        --drive-target $T --drive-seed 0 >> $LOG 2>&1
  done
done
echo "DRIVE CONTROL DONE $(date -u +%H:%M:%S)" >> $LOG
