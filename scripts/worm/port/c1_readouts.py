# BRAIN_PORT sections 6-8: readouts of one closed-loop run from its saved files (out.json, .neural/.act/.frames.f32).
# The .act.f32 columns are in MetaWorm driver order (meta "muscles": MDR, MVR, MDL, MVL, rows 1-24 each; MVL24 is a
# copy of MVL23, body/loop.py muscle_map), so the copy is dropped before counting muscles.
# argv: out_prefix [sets] ... recomputes and rewrites out_prefix.c1.json for each (sets = the PARAM=VALUE string used).
import sys, json
import numpy as np


def readouts(out, sets=""):
    meta = json.load(open(out + ".json"))
    nf, secs, nn = meta["n_frames"], meta["seconds"], 302
    V = np.fromfile(out + ".neural.f32", np.float32).reshape(-1, len(meta["cells"]))
    A = np.fromfile(out + ".act.f32", np.float32).reshape(nf, -1)
    X = np.fromfile(out + ".frames.f32", np.float32).reshape(nf, -1, 3)
    grp = np.repeat(meta["muscles"], 24); row = np.tile(np.arange(1, 25), len(meta["muscles"]))
    keep = ~((grp == "MVL") & (row == 24))
    A, grp, row = A[:, keep], grp[keep], row[keep]
    c = X.mean(1)
    F = np.abs(np.fft.rfft(A - A.mean(0), axis=0)) ** 2
    frac = F[2:].sum(0) / np.maximum(F[1:].sum(0), 1e-30)      # power above the lowest nonzero bin, per muscle
    L = float(np.linalg.norm(np.diff(X[0], axis=0), axis=1).sum())
    r = dict(toggles=meta["brain_config"]["toggles"], sets=sets, seconds=secs, wall_s=meta["loop_wall_s"], n_frames=nf,
             finite=bool(np.isfinite(V).all()),
             neurons_above_m20_last=int((V[-1, :nn] > -20).sum()), muscles_above_m20_last=int((V[-1, nn:] > -20).sum()),
             act_max=float(A.max()), act_mean_last_s=float(A[-30:].mean()),
             act_std_time_median=float(np.median(A.std(0))), power_above_lowest_bin_median=float(np.median(frac)),
             centroid_net_body_lengths=float(np.linalg.norm(c[-1] - c[0]) / L),
             centroid_path_body_lengths=float(np.linalg.norm(np.diff(c, axis=0), axis=1).sum() / L))
    t = np.arange(nf) * secs / (nf - 1); w = t >= 1.0
    dors = np.isin(grp, ["MDR", "MDL"]); mid = (row >= 9) & (row <= 16)
    dv = A[w][:, mid & dors].mean(1) - A[w][:, mid & ~dors].mean(1); dv = dv - dv.mean()
    r.update(muscles_sd_gt_0p05=int((A[w].std(0) > 0.05).sum()),
             midbody_dv_zero_crossings=int((np.diff(np.sign(dv)) != 0).sum()), midbody_dv_p2p=float(dv.max() - dv.min()))
    r["rhythm_candidate"] = bool(r["midbody_dv_zero_crossings"] >= 3 and r["midbody_dv_p2p"] >= 0.1)
    json.dump(r, open(out + ".c1.json", "w"), indent=1)
    return r


if __name__ == "__main__":
    a = sys.argv[1:]
    for i in range(0, len(a), 2):
        print(json.dumps(readouts(a[i], a[i + 1] if i + 1 < len(a) else "")))
