#!/bin/zsh
# The transition from rhythmic to arrhythmic happens below sensory drive 12.5.
# Map it finely. Cheap: low drive means low activity means a fast solver.
set -u
LOG=runs/fine_sensory.log
: > $LOG
for A in 0.5 1 2 3 5 8 10; do
  echo "===== fine sensory_amp=$A $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py --condition baseline \
      --replicates 8 --rtol 2e-6 --atol 5e-9 --sensory-amp $A >> $LOG 2>&1
done
echo "FINE SENSORY DONE $(date -u +%H:%M:%S)" >> $LOG
