#!/bin/zsh
# s20 fly2 N30 runs as pre-registered (DECISIONS 20 Oct 23:30 and the 23:48 build note), seed 1, sequential
# through the slot limiter. Writes runs/s20/fly2/n30_runs.done when finished (exit codes listed there).
#   nohup scripts/probes/n30_runs.sh > runs/s20/fly2/n30_runs.log 2>&1 & disown
cd /Users/ben/fly-emulation/.claude/worktrees/fly2 || exit 1
OUT=runs/s20/fly2
mkdir -p $OUT
PY=.venv/bin/python
SLOT=(python3 /Users/ben/director/harness/slot.py run)
BASE=(--profile m10f --seed 1 --set "connectome:identified|nt_from_physiology=1"
      --set "connectome:identified|unitary_psp_from_recordings=1"
      --set "cell_type:all|two_compartments_where_point_fails=1")
codes=()
run() { local name=$1; shift; echo "== $name $(date +%H:%M:%S)"; "$@" > $OUT/$name.log 2>&1; local c=$?; codes+=("$name=$c"); echo "   exit $c $(date +%H:%M:%S)"; }

run gate_passive  $SLOT --label "fly2: N30 gate passive" -- $PY scripts/probes/gf_psi_dlm_path.py $BASE \
    --window-ms 30 --axon-passive --out $OUT/gate_passive.json
run gate_spiking  $SLOT --label "fly2: N30 gate spiking" -- $PY scripts/probes/gf_psi_dlm_path.py $BASE \
    --window-ms 30 --out $OUT/gate_spiking.json
run latency       $SLOT --label "fly2: N30 latency seed 1" -- $PY scripts/probes/gf_latency.py $BASE \
    --trials 20 --out $OUT/latency.json
for q in 0.012 0.15; do
  for r in 0.13 25; do
    run corner_q${q}_r${r} $SLOT --label "fly2: N30 corner q$q rho$r" -- $PY scripts/probes/gf_latency.py $BASE \
        --trials 20 --arms gaps_on --set "cell_class:MN|axon_membrane_share=$q" \
        --set "cell_class:MN|soma_axon_coupling=$r" --out $OUT/corner_q${q}_r${r}.json
  done
done
echo "${codes[*]} $(date +%H:%M:%S)" > $OUT/n30_runs.done
