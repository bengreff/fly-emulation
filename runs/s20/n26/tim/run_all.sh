#!/bin/bash
# s20 N26 CRY-TIM refit (DECISIONS 22 Oct 23:02): primary + V1-V5, in parallel; writes ALL.done at the end.
cd /Users/ben/fly-emulation
F=scripts/probes/s20_n26_tim_fit.py; O=runs/s20/n26/tim; PY=.venv/bin/python
nice -n 5 $PY $F --out $O/primary.json > $O/primary.log 2>&1 &
nice -n 5 $PY $F --out $O/v1_ctau0.1.json --set cry_tau_h=0.1 > $O/v1.log 2>&1 &
nice -n 5 $PY $F --out $O/v2_ctau2.json --set cry_tau_h=2.0 > $O/v2.log 2>&1 &
nice -n 5 $PY $F --out $O/v3_trec0.43.json --set tim_tau_rec_h=0.43 > $O/v3.log 2>&1 &
nice -n 5 $PY $F --out $O/v4_noct20.json --drop-ct 20 > $O/v4.log 2>&1 &
nice -n 5 $PY $F --out $O/v5_tang0.03.json --tang-frac 0.03 > $O/v5.log 2>&1 &
wait
date > $O/ALL.done
