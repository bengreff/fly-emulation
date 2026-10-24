"""s23: split each MB type's rest drive (s22_mb_rest_drive.py basis) by presynaptic MBON transmitter (predictedNt).
Feeds docs/MEASUREMENT_LIST.md entry 6. No simulation.

    PYTHONPATH=src .venv/bin/python scripts/probes/s23_mb_glu_split.py
"""
import json, sys, numpy as np
sys.path.insert(0, "src"); sys.path.insert(0, "scripts/probes")
import s22_mb_rest_drive as m
from flyemu import connectome, lif, profiles
from flyemu.registry import Policy, Registry
c = json.loads(m.CONFIRM.read_text())
reg = Registry(Policy.MINIMAL)
reg.overrides["class:DAN|noise"] = c["dan_noise"]; reg.overrides["class:MBON|noise"] = c["mbon_noise"]
profiles.apply(reg, c["profile"])
conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
params = lif.default_params(reg, conn, timestep_ms=m.DT)
net = lif.Network(conn, params, m.DT, rng=np.random.default_rng(c["seed"]))
types = conn.neurons.type.fillna("").to_numpy(str)
ntcol = next(col for col in ("nt", "consensusNt", "predictedNt") if col in conn.neurons.columns)
nt = conn.neurons[ntcol].fillna("").to_numpy(str)
rate = np.full(conn.n, float(c["whole_brain_hz"]))
for t, hz in c["type_hz"].items(): rate[types == t] = hz
is_mbon = np.char.startswith(types, "MBON")
pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr)); post = conn.indices
w = np.asarray(net.w, np.float64)
out = {}
for t in m.TYPES:
    cells = np.flatnonzero(types == t); e = np.isin(post, cells); we, pe = w[e], pre[e]; d = we * rate[pe]; k = len(cells)
    row = {}
    for lab in ("glutamate", "gaba", "acetylcholine", "dopamine"):
        sel = is_mbon[pe] & (np.char.lower(nt[pe]) == lab)
        row[f"mbon_{lab}"] = round(float(d[sel].sum() / k), 1)
    row["net_all"] = round(float(d.sum() / k), 1)
    row["kc_per_hz"] = round(float(we[np.char.startswith(types[pe], "KC")].sum() / k), 1)
    out[t] = row; print(t, row, flush=True)
json.dump({"ntcol": ntcol, "types": out}, open("runs/s20/mb/glu_split.json", "w"), indent=1)
