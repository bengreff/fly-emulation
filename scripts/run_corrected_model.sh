#!/bin/zsh
# The payoff experiment. With the F11 excitability artefact corrected (soma size
# normalised within class) the published stimulus no longer drives the network,
# because the published operating point was calibrated with the artefact in
# place. Sweep the descending stimulus to find the corrected model's own working
# point, then ask the F7 question there: can it give rhythm AND physiological
# motor-neuron rates at the same time?
set -u
LOG=runs/corrected_model.log
: > $LOG
for I in 250 500 1000 2000 4000 8000; do
  echo "===== size-norm=class stim=$I $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py --condition baseline \
      --replicates 6 --rtol 2e-6 --atol 5e-9 --size-norm class --stim-amp $I >> $LOG 2>&1
done
echo "CORRECTED MODEL DONE $(date -u +%H:%M:%S)" >> $LOG
