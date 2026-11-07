# usage: bash -s REPO LABEL   (runs freeze_check.py on CPU 27, detached; writes ~/worm-night/wfit/freeze/LABEL.*)
R=$1; L=$2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1 LP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH=$R/src:$R/scripts/worm/fit1 WORMEMU_NRNMECH=/home/greff/worm-night/wfit/nrnmech
mkdir -p ~/worm-night/wfit/freeze; cd ~/worm-night/wfit/freeze
nohup taskset -c 27 ~/worm-night/wfit/venv/bin/python $R/scripts/worm/fit1/freeze_check.py $L.json > $L.log 2>&1 &
echo "$L $! $(date '+%F %T') $R" >> pids.txt
tail -1 pids.txt
