#!/bin/zsh
set -u
while ! grep -q "NT UNCERTAINTY DONE" runs/nt_uncertainty.log 2>/dev/null; do sleep 45; done
# 1. Does correcting the proprioceptor sign change the sensory-drive result?
LOG=runs/proprio_sign.log
: > $LOG
for A in 2 5; do
  for MODE in default cholinergic; do
    echo "===== A=$A proprioceptor sign=$MODE $(date -u +%H:%M:%S) =====" >> $LOG
    if [[ $MODE == cholinergic ]]; then
      uv run python scripts/pugliese_conditions.py --condition baseline \
          --replicates 8 --rtol 2e-6 --atol 5e-9 --sensory-amp $A \
          --proprio-cholinergic >> $LOG 2>&1
    else
      uv run python scripts/pugliese_conditions.py --condition baseline \
          --replicates 8 --rtol 2e-6 --atol 5e-9 --sensory-amp $A >> $LOG 2>&1
    fi
  done
done
echo "PROPRIO SIGN DONE $(date -u +%H:%M:%S)" >> $LOG
# 2. Can stronger inhibition hold a high-rate rhythm?
./scripts/run_ei_balance.sh
