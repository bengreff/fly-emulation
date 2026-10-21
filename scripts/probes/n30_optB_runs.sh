#!/bin/zsh
# s21 fly2: GF escape at the option-B class values and the two MN5 cells' own values (DECISIONS 21 Oct 00:07,
# UNDECIDED case; consistency only, Ryglewski 2014 is spent). Writes runs/s21/optB_runs.done.
#   nohup scripts/probes/n30_optB_runs.sh > runs/s21/optB_runs.log 2>&1 & disown
cd /Users/ben/fly-emulation/.claude/worktrees/fly2 || exit 1
OUT=runs/s21
mkdir -p $OUT
PY=.venv/bin/python
SLOT=(python3 /Users/ben/director/harness/slot.py run)
BASE=(--profile m10f --seed 1 --set "connectome:identified|nt_from_physiology=1"
      --set "connectome:identified|unitary_psp_from_recordings=1"
      --set "cell_type:all|two_compartments_where_point_fails=1")
codes=()
run() { local name=$1; shift; echo "== $name $(date +%H:%M:%S)"; "$@" > $OUT/$name.log 2>&1; local c=$?; codes+=("$name=$c"); echo "   exit $c $(date +%H:%M:%S)"; }
arm() { local name=$1 q=$2 r=$3
  run $name $SLOT --label "fly2: N30 $name" -- $PY scripts/probes/gf_latency.py $BASE --trials 20 --arms gaps_on \
      --set "cell_class:MN|axon_membrane_share=$q" --set "cell_class:MN|soma_axon_coupling=$r" --out $OUT/$name.json; }
arm optB_class 0.104 3.80
arm optB_L 0.156 2.03
arm optB_R 0.052 5.57
echo "${codes[*]} $(date +%H:%M:%S)" > $OUT/optB_runs.done
