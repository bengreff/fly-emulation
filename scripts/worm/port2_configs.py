"""Writes the port2 configurations (W1_RIM_AFD.md, Q2) as JSON files for neuron_ref.py / check_port.py.
usage: port2_configs.py <rundir> [extra channels]   (port2: none; port2b: exp2, added to all-on and tested alone)"""
import json, os, sys
R = sys.argv[1]
RIM = dict(surf=103.34e-8, vol=10.94e-12, cm=1.5, eL=-50.0)
# RIM_simulation.py (Nicoletti 2024), S/cm2: SHL1, EGL2, IRK, CCA1, UNC2, EGL19, LEAK; eleak -50, cm 1.5
g = [0.0009048750067326097, 0.0001411644285181245, 0.0003272854640954744, 0.0008451919806776876,
     9.676795045480941e-05, 0.00032005818627638106, 9.676795045480941e-05]
pub = {k: x * RIM["surf"] * 1e9 for k, x in zip(["shl1", "egl2", "irk", "cca1", "unc2", "egl19", "leak"], g)}
NEW8 = ["cca1", "egl2", "egl36", "irk", "kqt3", "kvs1", "shk1", "unc103"]
EXTRA = sys.argv[2:]
NEW = EXTRA or NEW8  # the channels tested alone
ALL13 = {"leak": 0.14, "slo1iso": 1, "kqt1": 0.2, "egl19": 0.3, "slo1egl19": 0.92, "nca": 0.06, "shl1": 0.5, "unc2": 0.3,
         "slo1unc2": 0.3, "slo2egl19": 0.5, "slo2unc2": 0.5, "slo2iso": 0.3, "kcnl": 0.3}  # = ref/all_test.npz
cfgs = {"rim_pub": dict(RIM, g_nS=pub), "leak_only": dict(RIM, g_nS={"leak": 0.5})}
for c in NEW:
    cfgs[f"iso_{c}"] = dict(RIM, g_nS={"leak": 0.5, c: float(os.environ.get("ISO_NS", 1.0))})  # port2c: ISO_NS=10
cfgs[f"all{13 + len(NEW8) + len(EXTRA)}"] = dict(eL=-89.57, cm=1.6, surf=6.589e-07, vol=7.42e-12,
                                                g_nS=dict(ALL13, **{c: 0.3 for c in NEW8 + EXTRA}))
for dt in (0.4, 0.1):
    for n, c in cfgs.items():
        json.dump(dict(c, dt=dt), open(os.path.join(R, f"{n}_dt{dt}.json"), "w"))
print(json.dumps({n: c["g_nS"] for n, c in cfgs.items()}))
