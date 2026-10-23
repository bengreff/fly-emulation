#!/bin/bash
# s20 MB resting-rate grid, fit and confirm (pre-registered DECISIONS 22 Oct 22:23). Two lanes, 4 threads each.
set -u
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 XLA_FLAGS=--xla_cpu_multi_thread_eigen=false
NEW=~/fly-m10f; OUT=$NEW/runs/s20/mb; mkdir -p $OUT; cd $NEW
PY=$NEW/.venv/bin/python; P=scripts/probes/s20_mb_rest.py
load1() { cut -d' ' -f1 /proc/loadavg; }
one() {  # one <name> <dan> <mbon> <seed>
  [ -f $OUT/$1.done ] && grep -q rc=0 $OUT/$1.done && return 0
  while awk "BEGIN{exit !($(load1) > 24)}"; do sleep 30; done
  echo "$(date +%T) start $1" >> $OUT/drive.log
  $PY $P --dan $2 --mbon $3 --seed $4 --out $OUT/$1.json > $OUT/$1.log 2>&1; echo "rc=$?" > $OUT/$1.done
  echo "$(date +%T) end $1 $(cat $OUT/$1.done)" >> $OUT/drive.log
}
export -f one load1; export OUT PY P
printf "%s\n" 0.5 0.75 1.0 1.25 1.5 2.0 2.5 3.0 | xargs -P 2 -I{} bash -c 'one g{}_s12 {} {} 12'
$PY - $OUT > $OUT/sigma_star.json <<'PYEOF'
import json, sys
from pathlib import Path
out = Path(sys.argv[1]); grid = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
res = {}
for t, key, target in (("PPL105", "dan", 8.0), ("MBON14", "mbon", 12.1)):
    pts = [(0.0, None)] + [(s, json.loads((out / f"g{s}_s12.json").read_text())["fit_targets"][t]["model_hz"]) for s in grid]
    pts = [(s, y) for s, y in pts if y is not None]
    star = None
    for (s0, y0), (s1, y1) in zip(pts, pts[1:]):
        if y0 < target <= y1:
            star = round(s0 + (target - y0) * (s1 - s0) / (y1 - y0), 4); break
    res[key] = {"type": t, "target_hz": target, "sigma_star": star, "grid": pts}
print(json.dumps(res, indent=1))
PYEOF
D=$($PY -c "import json;d=json.load(open('$OUT/sigma_star.json'));print(d['dan']['sigma_star'])")
M=$($PY -c "import json;d=json.load(open('$OUT/sigma_star.json'));print(d['mbon']['sigma_star'])")
if [ "$D" != None ] && [ "$M" != None ]; then
  printf "%s\n" 12 13 | xargs -P 2 -I{} bash -c "one confirm_s{} $D $M {}"
fi
touch $OUT/ALL.done
