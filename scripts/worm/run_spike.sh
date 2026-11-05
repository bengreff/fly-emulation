#!/usr/bin/env bash
# One command for the spike (docs/worm/SPIKE.md): push the code to backhouse, fit both AIY models, score them on
# the held-out data, draw the figure, and copy the numbers and the figure back.
#
#   scripts/worm/run_spike.sh          launch on backhouse, wait for it, pull results (about 1.5 h)
#   scripts/worm/run_spike.sh launch   launch only (detached, survives ssh drops and the laptop closing)
#   scripts/worm/run_spike.sh pull     wait for a launched run to finish, then pull results
#
# Results land in data/worm/spike/<run>/ (eval.json, fit_*.json, logs) and docs/worm/media/spike_<run>.png.
# Needs on backhouse: ~/worm-spike/.venv (jaxley 0.14, optax, openpyxl, matplotlib) and ~/worm-data (MANIFEST.md).
# CPU only, 2 cores per model (the shared GPU was slower for one small cell; SPIKE.md). Threads capped.
set -euo pipefail
cd "$(dirname "$0")/../.."
RUN=${RUN:-fit1}
CORES_A=${CORES_A:-8-9}
CORES_B=${CORES_B:-10-11}
mode=${1:-all}
R="/home/greff/worm-spike/runs/$RUN"

launch() {
  bash scripts/worm/sync_spike.sh
  ssh backhouse 'wsl -d Ubuntu -- bash -s' <<EOF
set -e
cd ~/worm-spike; mkdir -p $R; rm -f $R/*.done $R/all.done
cat > $R/job.sh <<'EOS'
#!/bin/bash
cd ~/worm-spike; . .venv/bin/activate
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMBA_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 LP_NUM_THREADS=2
export JAX_PLATFORMS=cpu XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
R=\$1
taskset -c $CORES_A python repo/scripts/worm/fit_aiy.py \$R --model cengen --starts 16 --iters 300 > \$R/cengen.log 2>&1 &
taskset -c $CORES_B python repo/scripts/worm/fit_aiy.py \$R --model pub --starts 16 --iters 300 > \$R/pub.log 2>&1 &
wait
taskset -c $CORES_A python repo/scripts/worm/eval_aiy.py \$R cengen,pub > \$R/eval.log 2>&1
taskset -c $CORES_A python repo/scripts/worm/plot_spike.py \$R \$R/spike.png >> \$R/eval.log 2>&1
echo "rc \$? \$(date)" > \$R/all.done
EOS
chmod +x $R/job.sh
setsid nohup $R/job.sh $R > $R/job.out 2>&1 < /dev/null &
sleep 3
echo "launched $RUN on backhouse: \$(date)"
EOF
}

pull() {
  until ssh backhouse "wsl -d Ubuntu -- test -f $R/all.done"; do
    ssh backhouse "wsl -d Ubuntu -- tail -qn1 $R/cengen.log $R/pub.log" || true
    sleep 120
  done
  mkdir -p "data/worm/spike/$RUN" docs/worm/media
  for f in eval.json fit_cengen.json fit_pub.json cengen.log pub.log eval.log all.done; do
    ssh backhouse "wsl -d Ubuntu -- base64 -w0 $R/$f" | base64 -d > "data/worm/spike/$RUN/$f"
  done
  ssh backhouse "wsl -d Ubuntu -- base64 -w0 $R/spike.png" | base64 -d > "docs/worm/media/spike_$RUN.png"
  cat "data/worm/spike/$RUN/all.done"
  grep -v '^W' "data/worm/spike/$RUN/eval.log" | tail -6
}

case "$mode" in
  launch) launch ;;
  pull) pull ;;
  all) launch; pull ;;
  *) echo "usage: $0 [all|launch|pull]"; exit 2 ;;
esac
