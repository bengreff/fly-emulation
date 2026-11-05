#!/bin/bash
cd ~/worm-spike; . .venv/bin/activate
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LP_NUM_THREADS=1
export JAX_PLATFORMS=cpu XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
R=~/worm-spike/runs/kcnl1; S=~/worm-spike/repo/scripts/worm/check_kcnl.py
taskset -c 12 python $S nrn ~/worm-spike/ext/nicoletti2024 $R/pub.npz > $R/pub.log 2>&1 &
taskset -c 13 python $S nrn ~/worm-spike/ext/nicoletti2024_patched $R/pat.npz > $R/pat.log 2>&1 &
taskset -c 14 python $S jx $R/jx.npz > $R/jx.log 2>&1 &
wait
taskset -c 12 python $S score $R $R/kcnl1.png > $R/score.log 2>&1
echo "rc $? $(date)" > $R/done
