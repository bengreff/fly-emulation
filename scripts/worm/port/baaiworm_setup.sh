#!/bin/bash
# Port step 1: BAAIWorm (Zhao et al. 2024 Nat Comput Sci 4:978, Apache 2.0) run AS PUBLISHED on backhouse.
# Pinned: github.com/Jessie940611/BAAIWorm commit b99ca5a (shallow clone 2026-11-05). Venv ~/worm-port/.venv
# (neuron 9.0.2, torch cpu, xlrd 1.2.0 as the repo's requirements say). Writes ~/worm-port/out/*.
#   a) eworm/network/test.py: the 136-cell detailed circuit as shipped (untrained construction weights)
#   b) eworm_learn/trial10 in RUN_MODE test: the trained 136-cell network with its optimal weights and inputs;
#      CPU only (cupy replaced by a numpy shim, ngpu 8 -> 1; the training path is not run). Compared with the
#      shipped v_final_eworm_v4.npy, which is the authors' own output of the same network.
set -e
W=~/worm-port; B=$W/BAAIWorm; OUT=$W/out; mkdir -p $OUT
source $W/.venv/bin/activate
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMBA_NUM_THREADS=4
uv pip install opt_einsum > /dev/null 2>&1 || true
cd $B && git log --oneline -1 > $OUT/commit.txt
# compile the channel and synapse mechanisms (eworm: forward model; eworm_learn: the _lr variants)
cd $B/eworm/components/mechanism && [ -d x86_64 ] || nrnivmodl modfile > $OUT/nrnivmodl_eworm.log 2>&1
cd $B/eworm_learn && [ -d x86_64 ] || nrnivmodl components/mechanism/modfile > $OUT/nrnivmodl_learn.log 2>&1
# a) as shipped
cd $B && export PYTHONPATH=$B
/usr/bin/time -v taskset -c 0-3 python eworm/network/test.py > $OUT/a_test.log 2> $OUT/a_test.time || echo "a failed" >> $OUT/a_test.log
# b) trained network, CPU
mkdir -p $W/shim/cupy
cat > $W/shim/cupy/__init__.py <<'P'
"""numpy stand-in for cupy so BAAIWorm's trained network can be run (not trained) on CPU."""
import contextlib
from numpy import *          # noqa
import numpy as _np
asnumpy = _np.asarray
newaxis = None
class cuda:                  # noqa
    @staticmethod
    def Device(i):
        return contextlib.nullcontext()
P
cd $B/eworm_learn
sed -e 's/^ngpu = 8 /ngpu = 1 /' run_eworm_v4.py > run_eworm_v4_cpu.py
PYTHONPATH=$W/shim:$B/eworm_learn /usr/bin/time -v taskset -c 0-3 python run_eworm_v4_cpu.py > $OUT/b_trained.log 2> $OUT/b_trained.time || echo "b failed" >> $OUT/b_trained.log
echo done
