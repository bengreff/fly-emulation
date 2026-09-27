"""Turn a file of shell command lines into one bash script per job, for backhouse.

    python3 scripts/mkjobs.py runs/<batch> <lines.txt>
    tmux new-session -d -s <name> -c ~/fly-emulation \
        "xargs -P 8 -n 1 bash < runs/<batch>/joblist.txt > runs/<batch>/xargs.log 2>&1" </dev/null >/dev/null 2>&1

One script per job avoids every quoting failure met in session 8 (cmd.exe mangling
'|', xargs defaulting to echo, split --set arguments). Each script pins BLAS to one
thread: a threaded gemv per step oversubscribed 28 cores (load 138) in session 8.
Plain python3 (no uv) so it runs before the venv is touched.
"""
import pathlib
import sys

d = pathlib.Path(sys.argv[1])
(d / "jobs").mkdir(parents=True, exist_ok=True)
lines = [l.rstrip("\n") for l in open(sys.argv[2]) if l.strip()]
with open(d / "joblist.txt", "w") as f:
    for i, l in enumerate(lines):
        p = d / "jobs" / f"j{i:03d}.sh"
        p.write_text("#!/bin/bash\ncd ~/fly-emulation && export PATH=$HOME/.local/bin:$PATH "
                     "OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n" + l + "\n")
        f.write(str(p) + "\n")
print(len(lines), "jobs")
