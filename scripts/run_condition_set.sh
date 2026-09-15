#!/bin/zsh
# First long run: all conditions at the tolerances used in the paper.
set -u
N=${1:-16}
LOG=runs/condition_set_N${N}.log
: > $LOG
for c in baseline silence_i1i2 shuffle dna02 no_stim; do
  echo "===== $c $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py \
      --condition $c --replicates $N --rtol 2e-6 --atol 5e-9 --save-traces \
      >> $LOG 2>&1
done
echo "ALL DONE $(date -u +%H:%M:%S)" >> $LOG
