import sys, json, numpy as np
TR = sys.argv[3]; src = open(sys.argv[1]).read().split("res, traces = [], {}")[0]
sys.argv = [sys.argv[1], sys.argv[2], "/tmp/x.npz"]
__file__ = sys.argv[0]; exec(compile(src, "cgn", "exec"))
pt = np.load(TR)["S_nrn_dt0.1"]
first = nrn("S", 0.0, 0.1)
second = nrn("S", 0.0, 0.1)
fine = nrn("S", 0.0, 0.001)
third = nrn("S", 0.0, 0.1)
print(json.dumps({"patched_mods": PATCHED, "global_megl19_now": float(h.megl19_egl19) if not PATCHED else None,
    "fresh_first_vs_patched": float(np.abs(first - pt).max()), "second_vs_patched": float(np.abs(second - pt).max()),
    "after_fine_vs_patched": float(np.abs(third - pt).max())}))
