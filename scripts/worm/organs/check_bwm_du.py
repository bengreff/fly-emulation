"""Row 12 unit check: the Du/Crodelle muscle (numpy reference, and the NEURON mod when --neuron) on the paper's
current-clamp protocol against the recording in the Du repo (data/spikes.npy: columns 30, 25, 20, 15 pA)."""
import argparse
import json
import sys

import numpy as np

from wormemu.mech import muscle_bwm as mb

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="/tmp/worgans/C.elegans-Muscle/data/spikes.npy")
ap.add_argument("--neuron", action="store_true")
ap.add_argument("--out", default="")
a = ap.parse_args()

amps = (30.0, 25.0, 20.0, 15.0)
V, ca, t = mb.du_step_protocol(amps)
rec = np.load(a.data)
res = {"amps_pA": amps, "model": {}, "recording": {}}
for i, A in enumerate(amps):
    v = V[:, i]
    r = rec[:, i]
    st = np.flatnonzero((v[:-1] < 0) & (v[1:] >= 0)) * 0.1
    res["model"][A] = dict(spikes=mb.upcrossings(v), rest=float(v[t < 57].mean()), peak=float(v.max()),
                           first_ms=float(st[0]) if len(st) else None, spike_ms=[float(x) for x in st],
                           ca_mean_on_mM=float(ca[(t > 60) & (t < 257), i].mean()),
                           ca_max_mM=float(ca[:, i].max()))
    tr = np.linspace(0, 500, len(r))
    sr = tr[:-1][(r[:-1] < 0) & (r[1:] >= 0)]
    res["recording"][A] = dict(spikes=mb.upcrossings(r), rest=float(r[tr < 57].mean()), peak=float(r.max()),
                               first_ms=float(sr[0]) if len(sr) else None)
ok = all(abs(res["model"][A]["spikes"] - res["recording"][A]["spikes"]) <= 1 for A in amps) and \
    all(abs(res["model"][A]["rest"] + 31) <= 5 for A in amps) and all(res["model"][A]["peak"] > 20 for A in amps)
res["bar_pass_numpy"] = bool(ok)
print(json.dumps(res, indent=1))
if a.out:
    np.savez(a.out, V=V, ca=ca, t=t, rec=rec)

if a.neuron:
    from neuron import h
    from wormemu.mech import organs_nrn
    organs_nrn.load_organ_mods(h)
    h.load_file("stdrun.hoc")
    q = {s.id: s.template for s in mb.SPECS}
    out = {}
    for dt in (0.1, 0.5):
        h.dt, h.secondorder = dt, 0
        sec = h.Section(name="m")
        sec.L, sec.diam, sec.nseg = 20.0, 5.0, 1
        sec.insert("du_bwm")
        ar = organs_nrn.area_um2(sec)
        mb.configure(sec, q, ar)
        sec(0.5).du_bwm.published_init = 1
        sec.cm = q["bwm_du_c_pF"] * 100.0 / ar
        stim = h.IClamp(sec(0.5))
        Vs = []
        for A in amps:
            stim.delay, stim.dur, stim.amp = 57.8, 200.0, A / q["bwm_du_input_scale"] / 1000.0
            h.finitialize(-30.0)
            vv = []
            while h.t < 500.0 - 1e-9:
                h.fadvance()
                vv.append(sec(0.5).v)
            vv = np.array(vv)
            Vs.append(vv)
            st = (np.flatnonzero((vv[:-1] < 0) & (vv[1:] >= 0)) + 1) * dt
            ref = np.array(res["model"][A]["spike_ms"])
            n = min(len(st), len(ref))
            out[f"dt{dt}_{A}"] = dict(spikes=len(st), rest=float(vv[: int(57 / dt)].mean()), peak=float(vv.max()),
                                      spike_ms=[round(float(x), 2) for x in st],
                                      max_dt_vs_numpy_ms=float(np.max(np.abs(st[:n] - ref[:n]))) if n else None)
        del stim, sec
    print(json.dumps(out, indent=1))
    rec_n = {A: res["recording"][A]["spikes"] for A in amps}
    print("bar: dt0.1 spike times within 2 ms of numpy:",
          all(out[f"dt0.1_{A}"]["spikes"] == res["model"][A]["spikes"] and out[f"dt0.1_{A}"]["max_dt_vs_numpy_ms"] <= 2
              for A in amps))
    print("bar: dt0.5 (the brain's step) spike count within 1 of the recording:",
          all(abs(out[f"dt0.5_{A}"]["spikes"] - rec_n[A]) <= 1 for A in amps))
