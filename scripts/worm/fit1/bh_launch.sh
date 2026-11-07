# launch the two FIT1 fits (main, shuf) detached on backhouse.
# Usage: bash -s ROOT DEADLINE|none COMMIT REPO H_DT MECH_DT
set -e
ROOT=$1; DEADLINE=$2; COMMIT=$3; R=$4; HDT=$5; MDT=$6
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1 LP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH=$R/src:$R/scripts/worm/fit1 WORMEMU_NRNMECH=/home/greff/worm-night/wfit/nrnmech
PY=/home/greff/worm-night/wfit/venv/bin/python
TOG='{"quantal_noise": "off", "channel_noise": "off"}'
mkdir -p $ROOT; cd $ROOT
COMMON="--train /home/greff/worm-night/wfit/fit1/train.npz --pop 16 --batch 4 --h-dt $HDT --mech-dt $MDT --window-s 30 --warm-s 5 --pulse-ms 500 --max-gens 200 --commit $COMMIT"
[ "$DEADLINE" != none ] && COMMON="$COMMON --deadline $DEADLINE"
nohup taskset -c 24 $PY $R/scripts/worm/fit1/fit1_run.py $ROOT/main --cpus 0,2,4,6,16,17,18,19 $COMMON --toggles "$TOG" > main.out 2>&1 &
echo "main $! $(date '+%F %T') repo $R h $HDT mech $MDT" >> drivers.txt
nohup taskset -c 25 $PY $R/scripts/worm/fit1/fit1_run.py $ROOT/shuf --cpus 8,10,12,14,20,21,22,23 --shuffle-seed 1 $COMMON --toggles "$TOG" > shuf.out 2>&1 &
echo "shuf $! $(date '+%F %T') repo $R h $HDT mech $MDT" >> drivers.txt
disown -a
cat drivers.txt
