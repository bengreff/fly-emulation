#!/bin/zsh
# How much of the published result rests on treating glutamate as inhibitory?
# Glutamatergic neurons are 23.8% of this network and supply 40.8% of its
# inhibitory synapse budget. Their sign is a modelling convention: in Drosophila
# glutamate is inhibitory where the GluCl chloride channel is expressed
# postsynaptically and excitatory otherwise. It is a receptor property, not a
# transmitter property, and it has not been measured for these VNC cells.
# 0.03 = default (inhibitory, same strength as GABA); 0 = silenced; negative = excitatory.
set -u
LOG=runs/glutamate_sweep.log
: > $LOG
for G in 0.03 0.02 0.01 0.0 -0.01 -0.03; do
  echo "===== glutamateMultiplier=$G $(date -u +%H:%M:%S) =====" >> $LOG
  uv run python scripts/pugliese_conditions.py --condition baseline \
      --replicates 8 --rtol 2e-6 --atol 5e-9 --glu-mult $G >> $LOG 2>&1
done
echo "GLUTAMATE SWEEP DONE $(date -u +%H:%M:%S)" >> $LOG
