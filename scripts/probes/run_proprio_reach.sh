#!/bin/bash
# fly2 stance loop step R (reach gate), DECISIONS 13 Oct 23:58. Mac, 4 parallel, 2 threads each.
cd "$(dirname "$0")/../.."
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2
O=runs/s13/proprio/reach
mkdir -p $O
P=".venv/bin/python scripts/probes/proprio_reach.py"
run() { local tag=$1; shift; $P "$@" --out $O/$tag.json > $O/$tag.log 2>&1; echo "$tag exit $?" >> $O/progress.txt; }
run clamp_lm_g8 --stim clamp --leg lm --gain-mv 8 &
run clamp_lm_g40 --stim clamp --leg lm --gain-mv 40 &
run clamp_lm_zero --stim clamp --leg lm --zero-afferents &
run load_lm_g8 --stim load --leg lm --gain-mv 8 &
wait
run clamp_lf_g8 --stim clamp --leg lf --gain-mv 8 &
run clamp_lf_g40 --stim clamp --leg lf --gain-mv 40 &
run clamp_lf_zero --stim clamp --leg lf --zero-afferents &
run load_lm_g40 --stim load --leg lm --gain-mv 40 &
wait
touch $O/ALL.done
