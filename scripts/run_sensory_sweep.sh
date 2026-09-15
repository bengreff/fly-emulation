#!/bin/zsh
# Waits for the condition set, then sweeps tonic proprioceptive drive.
# Question: is there a drive level giving BOTH physiological motor-neuron rates
# AND the ~10 Hz rhythm?
set -u
while ! grep -q "ALL DONE" runs/condition_set_N16.log 2>/dev/null; do sleep 20; done
LOG=runs/sensory_sweep.log
: > $LOG
for A in 0 12.5 25 50 75 100 150 200 300 400; do
  echo "===== sensory_amp=$A $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py --condition baseline \
      --replicates 8 --rtol 2e-6 --atol 5e-9 --sensory-amp $A >> $LOG 2>&1
done
echo "SENSORY SWEEP DONE $(date -u +%H:%M:%S)" >> $LOG
