# BRAIN_PORT section 6 C1: the body worker's 5 s closed loop (cl_tmpl.py at their 48b6ac6), brain from main's src.
# argv: seconds out MECH=STATE[,MECH=STATE] [PARAM=VALUE[,PARAM=VALUE]] (every element of that ledger row)
import sys, time, json
sys.path.insert(0, "/Users/ben/fly-emulation/src")
import wormemu
wormemu.__path__.append("/Users/ben/fly-emulation/.claude/worktrees/wormbody/src/wormemu")   # body package only
import numpy as np
from wormemu.brain import sample_worm, Brain
from wormemu.body.loop import Body, run
from wormemu.body.scene import ChemotaxisScene
secs, out = float(sys.argv[1]), sys.argv[2]
toggles = dict(receptor_sign="on")
toggles.update(kv.split("=") for kv in sys.argv[3].split(",") if kv) if len(sys.argv) > 3 else None
spec = sample_worm(None)
for kv in (sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else []):
    k, v = kv.split("="); x = spec.values[k]
    spec.values[k] = x * 0 + float(v) if hasattr(x, "index") else float(v)
brain = Brain(spec, toggles=toggles)
b = Body(out, scene=ChemotaxisScene(field="cone_published"), solver_exit="published")
meta = run(brain, b, seconds=secs, brain_config=dict(seed=None, toggles=toggles, solver_exit="published"))
sys.path.insert(0, "/Users/ben/fly-emulation/scripts/worm/port")
from c1_readouts import readouts
print(json.dumps(readouts(out, sys.argv[4] if len(sys.argv) > 4 else "")))
