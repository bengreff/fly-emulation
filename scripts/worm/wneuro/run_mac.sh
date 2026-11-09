#!/bin/bash
# wneuro: one Mac run through the slot harness, detached; writes logs/<name>.log and logs/<name>.done
# usage: run_mac.sh NAME script.py args...
cd /Users/ben/fly-emulation/.claude/worktrees/wormneuro
export DEVELOPER_DIR=/Library/Developer/CommandLineTools WORMEMU_NRNMECH=$PWD/.nrnmech WORMEMU_NRNMECH_ORGANS=$PWD/.nrnmech_organs
export PYTHONPATH=$PWD/src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
name=$1; shift
python3 ~/director/harness/slot.py run --label "worm: wneuro $name" -- /Users/ben/fly-emulation/.venv/bin/python "$@" > runs/worm/wneuro/logs/$name.log 2>&1
echo $? > runs/worm/wneuro/logs/$name.done
