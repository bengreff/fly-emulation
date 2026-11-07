# stop a FIT1 run on backhouse by its recorded PIDs (drivers first, so they do not retry; then each worker's forked
# children and the worker). Never by pattern. Usage: ssh backhouse 'wsl -d Ubuntu -- bash -s ROOT' < bh_stop.sh
ROOT=$1
for f in main shuf; do
  d=$(cat $ROOT/$f/driver.pid 2>/dev/null)
  if [ -n "$d" ] && grep -q fit1_run.py /proc/$d/cmdline 2>/dev/null; then kill $d && echo "killed driver $d ($f)"; fi
done
sleep 1
for f in main shuf; do
  for w in $(awk '{print $1}' $ROOT/$f/pids.txt 2>/dev/null); do
    if grep -q "$ROOT/$f/gen_" /proc/$w/cmdline 2>/dev/null; then
      for c in $(pgrep -P $w); do kill $c && echo "killed child $c of $w"; done
      kill $w && echo "killed worker $w"
    fi
  done
done
echo "$(date '+%F %T') stopped by PID (bh_stop.sh)" >> $ROOT/drivers.txt
