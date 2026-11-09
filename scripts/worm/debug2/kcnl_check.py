"""Bars of "KCNL: the network's density or the tuner's none" (docs/worm/night/2026-11-08_wbrain2.md, written before this
ran; wbrain2, 9 Nov 2026): `kcnl_density` network (default) | tuner in mech/capool.

  python scripts/worm/debug2/kcnl_check.py FEATURES.npz OUT.json
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

FEATS, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], FEATS]                          # ephys_score reads its features path from argv[1]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))
import ephys_score as E  # noqa: E402
from wormemu.mech import CHANNEL_NAMES, capool  # noqa: E402

S, B = E.S, E.S.B
ROOT = Path(__file__).resolve().parents[3]
res = {}


def cell_param_kcnl(c):
    m = re.search(r'"gbkcnl":\s*([0-9.eE+-]+)', (ROOT / "third_party/baaiworm/cell_param" / f"{c}.json").read_text())
    return float(m.group(1))


def run(br, into, n=400, on=200, amp=10.0):
    br.reset()
    V = []
    for k in range(n):
        br.extra_pA[:] = 0.0
        if k >= on:
            br.extra_pA[br.cell_names.index(into)] = amp
        V.append(br.step(None, 1.0).v_mV.copy())
    return np.array(V)


def densities(br):
    """{cell: {mech.gb: value}} over every section of every cell (gb* RANGE variables and pas g)"""
    h, out = br.h, {}
    for c, obj in zip(br.cell_names, br.cells):
        d = {}
        for j, sec in enumerate(obj.all):
            for ch in list(CHANNEL_NAMES) + ["pas"]:
                if h.ismembrane(ch, sec=sec):
                    for i, seg in enumerate(sec):
                        m = getattr(seg, ch)
                        for a in ("g",) if ch == "pas" else [x for x in dir(m) if x.startswith("gb")]:
                            d[f"{j}.{i}.{ch}.{a}"] = float(getattr(m, a))
        out[c] = d
    return out


# bar 1: neutral
cells = ["AIYL", "AVAL", "AFDL"]
br = S.build(cells=cells)
got = {c: float(br.cells[br.cell_names.index(c)].Soma(0.5).kcnl.gbkcnl) for c in cells}
want = {c: cell_param_kcnl(c) for c in cells}
V1 = {c: run(br, c) for c in cells}
orig = capool.build_cell


def bulk_only(brain, name, obj, params, toggles):              # the hook as it was before kcnl_density
    if capool._bulk(toggles) == "off" or name not in brain.st.index or brain.st.kind[brain.st.index[name]] != "neuron":
        return
    obj.Soma.insert("cabulk")


capool.build_cell = bulk_only
br0 = S.build(cells=cells)
V0 = {c: run(br0, c) for c in cells}
capool.build_cell = orig
dv = max(float(np.abs(V1[c] - V0[c]).max()) for c in cells)
res["bar1"] = dict(gbkcnl=got, cell_param=want, max_abs_dV_mV=dv,
                   passed=bool(dv == 0.0 and all(abs(got[c] - want[c]) < 1e-12 for c in cells)))
print("bar1", res["bar1"], flush=True)

# bar 2: tuner zeroes KCNL everywhere and nothing else
dn = densities(S.build())
dt = densities(S.build(extra={"kcnl_density": "tuner"}))
k_left = sorted({c for c, d in dt.items() for k, x in d.items() if ".kcnl.gbkcnl" in k and x != 0.0})
other = sorted({c for c in dn for k in dn[c] if ".kcnl." not in k and dn[c][k] != dt[c].get(k)})
had = sorted({c for c, d in dn.items() for k, x in d.items() if ".kcnl.gbkcnl" in k and x != 0.0})
res["bar2"] = dict(neurons=len(dn), with_kcnl_network=len(had), kcnl_left_tuner=k_left, other_changed=other,
                   passed=not k_left and not other)
print("bar2", {k: v for k, v in res["bar2"].items() if k != "other_changed"}, "other", other[:5], flush=True)

# bar 3: AIYL (fitted without KCNL) no worse under tuner; AFDL unmoved
net, tun = E.score({}, ["AIY", "AFD"]), E.score({"kcnl_density": "tuner"}, ["AIY", "AFD"])
res["bar3"] = dict(aiy_rmse=(net["AIY"]["rmse_mV"], tun["AIY"]["rmse_mV"]),
                   afd_rmse=(net["AFD"]["rmse_mV"], tun["AFD"]["rmse_mV"]),
                   aiy_model=dict(network=net["AIY"]["model"], tuner=tun["AIY"]["model"]), aiy_data=net["AIY"]["data"])
res["bar3"]["passed"] = bool(tun["AIY"]["rmse_mV"] <= net["AIY"]["rmse_mV"] + 0.5
                             and tun["AFD"]["rmse_mV"] == net["AFD"]["rmse_mV"])
print("bar3", res["bar3"]["aiy_rmse"], res["bar3"]["afd_rmse"], res["bar3"]["passed"], flush=True)

# reported: AVAL alone input resistance at -10 pA; the combined tuner world for AIYL
rin = {}
for form in ("network", "tuner"):
    b = S.build(cells=["AVAL"], extra={"kcnl_density": form})
    b.reset()
    b.extra_pA[:] = 0.0
    for _ in range(2000):
        v0 = float(b.step(None, 1.0).v_mV[0])
    b.extra_pA[:] = -10.0
    for _ in range(2000):
        v1 = float(b.step(None, 1.0).v_mV[0])
    rin[form] = dict(v_rest_mV=v0, v_step_mV=v1, rin_GOhm=(v0 - v1) / 10.0)
res["aval_rin"] = rin
both = E.score({"kcnl_density": "tuner", "slo_ca_source": "tuner_gbar"}, ["AIY"])["AIY"]
res["aiy_tuner_world_rmse"] = both["rmse_mV"]
print("aval", rin, "aiy tuner world", both["rmse_mV"], flush=True)
Path(OUT).write_text(json.dumps(res, indent=1))
