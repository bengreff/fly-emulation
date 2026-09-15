#!/bin/zsh
# With excitability corrected (F11), stimulus 250 leaves the network silent and
# 500 makes it hyperactive and arrhythmic. Is there a rhythmic window between?
# If not, the published rhythm depended on the excitability artefact.
set -u
LOG=runs/corrected_window.log
: > $LOG
for I in 300 350 400 450; do
  echo "===== size-norm=class stim=$I $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py --condition baseline \
      --replicates 6 --rtol 2e-6 --atol 5e-9 --size-norm class --stim-amp $I >> $LOG 2>&1
done
echo "CORRECTED WINDOW DONE $(date -u +%H:%M:%S)" >> $LOG
