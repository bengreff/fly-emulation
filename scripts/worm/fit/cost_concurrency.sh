#!/usr/bin/env bash
# Concurrency scaling of one battery condition (weki, 8 Nov 2026; brief item 4; FIT_GENERAL.md section 10): N copies of
# `vitals run food SECONDS` at once, N = 1, 2, 3 in turn, one thread each; wall time per copy (build included).
# Usage (backhouse, after sourcing env.sh): bash scripts/worm/fit/cost_concurrency.sh OUTDIR [SECONDS]
set -u
OUT=$1; SEC=${2:-20}
mkdir -p "$OUT"
for N in 1 2 3; do
  pids=()
  for k in $(seq 1 "$N"); do
    ( s=$(date +%s.%N); $PY -m wormemu.fit.vitals run food "$SEC" "$OUT/n${N}_$k" > "$OUT/n${N}_$k.log" 2>&1
      echo "$N $k $(awk "BEGIN{print $(date +%s.%N) - $s}")" >> "$OUT/wall.txt" ) &
    pids+=($!)
  done
  echo "N=$N pids ${pids[*]}" >> "$OUT/pids.txt"
  wait "${pids[@]}"
  uptime >> "$OUT/wall.txt"
done
touch "$OUT/DONE"
