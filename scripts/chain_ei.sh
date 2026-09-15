#!/bin/zsh
set -u
while ! grep -q "NT UNCERTAINTY DONE" runs/nt_uncertainty.log 2>/dev/null; do sleep 45; done
./scripts/run_ei_balance.sh
