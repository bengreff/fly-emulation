#!/bin/zsh
# Follow-up to F8. The model gives excitatory and inhibitory synapses the same
# strength per synapse (both multipliers 0.03), which is an assumption, not a
# measurement. At a sensory drive that produces physiological motor rates,
# does stronger inhibition restore the rhythm the added excitation destroyed?
set -u
LOG=runs/ei_balance.log
: > $LOG
for I in 0.03 0.045 0.06 0.09 0.12 0.18 0.25; do
  echo "===== inh=$I exc=0.03 A=12.5 $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py --condition baseline \
      --replicates 8 --rtol 2e-6 --atol 5e-9 --sensory-amp 12.5 \
      --exc-mult 0.03 --inh-mult $I >> $LOG 2>&1
done
echo "EI BALANCE DONE $(date -u +%H:%M:%S)" >> $LOG
