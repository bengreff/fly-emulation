# BRAIN_PORT section 6, M2: one isolated c302 muscle, steps 0, +1, +3, +10, +30 pA (1 s each).
# argv: moddir dt out.json, where moddir holds a copy of third_party/c302/mod (patched) or .../generated
# (as generated) built with `nrnivmodl .`. Run each set in its own process (the mechanism names are the same).
import sys, json, numpy as np
from neuron import h
h.nrn_load_dll(sys.argv[1] + "/arm64/libnrnmech.dylib")
h.load_file("stdrun.hoc")
dt = float(sys.argv[2])
s = h.Section(name="m"); s.L, s.diam, s.nseg, s.cm = 20.0, 5.0, 1, 1.0
G = {"Leak": 2e-6, "k_slow_muscle": 0.45833751019872582e-3, "k_fast_muscle": 0.042711643917483308e-3,
     "ca_boyle_muscle": 0.812775772264702e-3}
for m, g in G.items():
    s.insert(m); setattr(getattr(s(0.5), m), "gmax", g)
s(0.5).Leak.e = -20.0
s.insert("CaPoolMuscle"); s(0.5).CaPoolMuscle.decayConstant = 60.811870945509265; s(0.5).CaPoolMuscle.rho = 0.002238919e-8
h.ion_style("ca_ion", 3, 1, 0, 0, 0, sec=s)
ic = h.IClamp(s(0.5)); ic.dur = 1e9; ic.delay = 0
steps = [0, 1, 3, 10, 30]
tv = h.Vector().record(h._ref_t); vv = h.Vector().record(s(0.5)._ref_v)
h.dt = dt; h.steps_per_ms = 1.0 / dt; s(0.5).cai = 0.0; s(0.5).v = -28.0; h.finitialize()
for k, a in enumerate(steps):
    ic.amp = a * 1e-3
    h.continuerun((k + 1) * 1000.0)
t, v = np.array(tv), np.array(vv)
out = {"dt": dt, "finite": bool(np.isfinite(v).all())}
for k, a in enumerate(steps):
    w = (t >= k * 1000) & (t < (k + 1) * 1000); x = v[w]; tt = t[w]
    up = np.where((x[1:] > -10) & (x[:-1] <= -10))[0]
    out[f"{a}pA"] = dict(spikes=int(len(up)), spike_t=[float(tt[j + 1]) for j in up][:50],
                         last200=float(x[tt >= (k + 1) * 1000 - 200].mean()), vmin=float(x.min()), vmax=float(x.max()))
g = np.arange(0, 5000, 0.5); out["v_on_grid"] = np.interp(g, t, v).tolist()
json.dump(out, open(sys.argv[3], "w"))
print({k: (v["spikes"], round(v["last200"], 3), round(v["vmax"], 2)) for k, v in out.items() if k.endswith("pA")}, out["finite"])
