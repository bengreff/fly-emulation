#!/bin/bash
# N19 v4, s19 (DECISIONS 22 Oct 04:42). Resumes the refined U2 grid; a* = first crossing of 2.66 using only (0, 1)
# and the grid points run so far, in list order (a = 0.25 last). Then Dacks once at a*. No gate, no U1 (next session).
set -u
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 XLA_FLAGS=--xla_cpu_multi_thread_eigen=false
NEW=~/fly-m10f; OUT=$NEW/runs/s19/n19; mkdir -p $OUT
P=scripts/probes/s19_n19_units.py
PY=$NEW/.venv/bin/python
load1() { cut -d' ' -f1 /proc/loadavg; }
launch() {
  local name=$1; shift
  [ -f $OUT/$name.done ] && grep -q rc=0 $OUT/$name.done && return 0
  while awk "BEGIN{exit !($(load1) > 24)}"; do sleep 30; done
  echo "$(date +%T) start $name" >> $OUT/drive.log
  ( cd $NEW && $PY $P "$@" --out $OUT/$name.json > $OUT/$name.log 2>&1; echo "rc=$?" > $OUT/$name.done )
}
astar() {  # astar <a values run so far, in list order>
$PY - $OUT "$@" > $OUT/astar.json <<'PYEOF'
import json, sys
from pathlib import Path
out = Path(sys.argv[1]); rows = []
for a in sys.argv[2:]:
    d = json.loads((out / f"u2_a{a}.json").read_text()); r0, r1 = d["u0"], d["u1"]
    ratio = (r1["spikes"] / r0["spikes"]) if r0["spikes"] else None
    rows.append({"a": d["a"], "use": "spikes", "ratio": ratio, "u0": r0["spikes"], "u1": r1["spikes"]})
target = 2.66; astar = None; bracket = None
pts = [(0.0, 1.0)] + [(r["a"], r["ratio"]) for r in rows if r["ratio"] is not None]
for (a0, y0), (a1, y1) in zip(pts, pts[1:]):
    if (y0 - target) * (y1 - target) <= 0 and y1 != y0:
        astar = round(a0 + (target - y0) * (a1 - a0) / (y1 - y0), 4); bracket = [a0, a1]; break
print(json.dumps({"target": target, "astar": astar, "bracket": bracket, "grid": rows,
                  "rule": "DECISIONS 22 Oct 02:25 and 04:42"}, indent=1))
PYEOF
$PY -c "import json;a=json.load(open('$OUT/astar.json'))['astar'];print(a if a is not None else 'none')"
}
echo "$(date +%T) drive4 start" >> $OUT/drive.log
A=none; RUN=""
for a in 0.02 0.04 0.06 0.08 0.11 0.15 0.2 0.25; do
  launch u2_a$a u2 --a $a; RUN="$RUN $a"; A=$(astar $RUN); [ "$A" != none ] && break
done
echo "$(date +%T) astar=$A (grid:$RUN)" >> $OUT/drive.log
if [ "$A" = none ]; then echo "no a*" > $OUT/ALL.done; exit 0; fi
launch dacks dacks --a $A
echo "$(date +%T) dacks finished" >> $OUT/drive.log; touch $OUT/ALL.done
