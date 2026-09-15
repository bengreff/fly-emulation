#!/bin/zsh
# Does the published rhythm survive the connectome's own annotation uncertainty?
# The EM transmitter classifier reports a probability per neuron. The published
# model takes the most likely label. 33% of neurons have confidence below 0.8,
# and those carry 24% of the synapse budget. Here the sign is redrawn from the
# classifier's probabilities on every replicate, so the spread across replicates
# is an uncertainty estimate for the sign assignment.
set -u
while ! grep -q "DONE" runs/glutamate_sweep.log 2>/dev/null; do sleep 30; done
LOG=runs/nt_uncertainty.log
: > $LOG
echo "===== resampled transmitters, 24 draws $(date -u +%H:%M:%S) =====" >> $LOG
uv run python scripts/pugliese_conditions.py --condition baseline \
    --replicates 24 --rtol 2e-6 --atol 5e-9 --sample-transmitters >> $LOG 2>&1
echo "===== fixed most-likely labels, 24 draws (matched control) $(date -u +%H:%M:%S) =====" >> $LOG
uv run python scripts/pugliese_conditions.py --condition baseline \
    --replicates 24 --rtol 2e-6 --atol 5e-9 --tag=-nt24 >> $LOG 2>&1
echo "NT UNCERTAINTY DONE $(date -u +%H:%M:%S)" >> $LOG
