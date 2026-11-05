#!/bin/bash
# Q2 port check (W1_RIM_AFD.md, run port2): eight new Nicoletti 2024 channels, Jaxley vs NEURON, one compartment.
# usage (backhouse WSL): bash repo/scripts/worm/check_port2.sh [run=port2] [extra channels, e.g. exp2 for port2b]
#   -> runs/<run>/{*.npz,*_jx.npy,*.log,score.json,port2.png,done}
cd ~/worm-spike; . .venv/bin/activate
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LP_NUM_THREADS=1 JAX_PLATFORMS=cpu XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
R=runs/${1:-port2}; shift; mkdir -p $R; MOD=~/worm-spike/ext/nicoletti2024
python repo/scripts/worm/port2_configs.py $R "$@" > $R/configs.log 2>&1
cp ref/aiy_pub.npz $R/r0_aiy_pub.npz; cp ref/all_test.npz $R/r0_all_test.npz
lane() {  # $1 core, rest: config names
    local c=$1; shift
    for n in "$@"; do
        [ -f $R/$n.npz ] || taskset -c $c python repo/scripts/worm/neuron_ref.py $MOD $R/$n.npz "$(cat $R/$n.json)" > $R/$n.nrn.log 2>&1
        taskset -c $c python repo/scripts/worm/check_port.py $R/$n.npz > $R/$n.jx.log 2>&1
    done
}
L=($(ls $R/*_dt0.[14].json | xargs -n1 basename | sed 's/\.json$//' | sort))
A=(); B=(); C=(); i=0
for n in "${L[@]}"; do case $((i % 3)) in 0) A+=($n);; 1) B+=($n);; 2) C+=($n);; esac; i=$((i+1)); done
lane 12 r0_aiy_pub "${A[@]}" & lane 13 r0_all_test "${B[@]}" & lane 14 "${C[@]}" & wait
python repo/scripts/worm/score_port2.py $R > $R/score.json 2> $R/score.err
echo "rc $? $(date)" > $R/done
