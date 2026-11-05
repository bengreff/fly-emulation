# BRAIN_PORT section 6 C1: the body worker's 5 s closed loop (cl_tmpl.py at their 48b6ac6), brain from main's src.
# argv: seconds out MECH=STATE[,MECH=STATE]
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
brain = Brain(sample_worm(None), toggles=toggles)
b = Body(out, scene=ChemotaxisScene(field="cone_published"), solver_exit="published")
meta = run(brain, b, seconds=secs, brain_config=dict(seed=None, toggles=toggles, solver_exit="published"))
V = np.fromfile(out + ".neural.f32", np.float32).reshape(-1, len(meta["cells"]))
A = np.fromfile(out + ".act.f32", np.float32).reshape(meta["n_frames"], -1)
X = np.fromfile(out + ".frames.f32", np.float32).reshape(meta["n_frames"], -1, 3)
c = X.mean(1); nn = 302
F = np.abs(np.fft.rfft(A - A.mean(0), axis=0)) ** 2
frac = F[2:].sum(0) / np.maximum(F[1:].sum(0), 1e-30)      # power above the lowest nonzero bin, per muscle
L = float(np.linalg.norm(np.diff(X[0], axis=0), axis=1).sum())
r = dict(toggles=toggles, seconds=secs, wall_s=meta["loop_wall_s"], n_frames=meta["n_frames"], finite=bool(np.isfinite(V).all()),
         neurons_above_m20_last=int((V[-1, :nn] > -20).sum()), muscles_above_m20_last=int((V[-1, nn:] > -20).sum()),
         act_max=float(A.max()), act_mean_last_s=float(A[-30:].mean()),
         act_std_time_median=float(np.median(A.std(0))), power_above_lowest_bin_median=float(np.median(frac)),
         centroid_net_body_lengths=float(np.linalg.norm(c[-1] - c[0]) / L),
         centroid_path_body_lengths=float(np.linalg.norm(np.diff(c, axis=0), axis=1).sum() / L))
json.dump(r, open(out + ".c1.json", "w"), indent=1); print(json.dumps(r))
