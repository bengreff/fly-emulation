import sys, json, numpy as np
src = open(sys.argv[1]).read().split("res, traces = [], {}")[0]
sys.argv = [sys.argv[1], sys.argv[2], "/tmp/x.npz"]
__file__ = sys.argv[0]; exec(compile(src, "cgn", "exec"))
def cmp(tag):
    a = nrn(tag, 0.0, 0.1); b = jxl(tag, ImplicitGap, 0.0, 0.1)
    n = min(a.shape[1], b.shape[1]); d = np.abs(a[:, :n] - b[:, :n]); it = np.unravel_index(np.argmax(d), d.shape)
    print(tag, CASES[tag], "max", float(d.max()), "at", it, "nrn", np.round(a[:, it[1]], 4), "jx", np.round(b[:, it[1]], 4),
          "v@60ms nrn", np.round(a[:, 600], 4), "jx", np.round(b[:, 600], 4), flush=True)
base = dict(CASES["P"])
for upd in [dict(ncell=1, ncomp=3, L=30.0, amp=0.01), dict(ncell=1, ncomp=3, L=30.0, amp=0.01, cm=1.6), dict(ncell=1, ncomp=2, L=20.0, amp=0.01)]:
    CASES["P"] = dict(base, **upd); cmp("P")
for upd in [dict(ncell=1, ncomp=2, L=20.0), dict(ncell=1, ncomp=3, L=30.0, amp=0.005)]:
    CASES["C"] = dict(CASES["C"], **upd); cmp("C")
