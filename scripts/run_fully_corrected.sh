#!/bin/zsh
# The strongest test of F15. Apply every correction the session found at once:
# excitability normalised within cell class (F11), leg afferents forced
# excitatory per published physiology (F10), and the stimulus set to the
# corrected model's own working point rather than the published value. Then add
# sensory drive and ask whether the combination reaches the region no simulation
# has reached: rhythmic AND firing hard enough to move a leg.
set -u
LOG=runs/fully_corrected.log
: > $LOG
for A in 0 1 2 5 10; do
  echo "===== fully corrected, stim=300, sensory=$A $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py --condition baseline \
      --replicates 6 --rtol 2e-6 --atol 5e-9 --size-norm class \
      --proprio-cholinergic --stim-amp 300 --sensory-amp $A >> $LOG 2>&1
done
echo "FULLY CORRECTED DONE $(date -u +%H:%M:%S)" >> $LOG
