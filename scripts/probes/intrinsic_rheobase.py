"""Rung-1 failure diagnosis (session 11): how much extra drive each channel demands to
reach threshold, per cell, computed from the gate curves (no simulation).

Membrane at steady state with intrinsic currents (rest-subtracted form, src/flyemu/channels.py):
    drive needed to hold v = (v - v_rest) + sum_c g_c (x_c(v) - x_c,rest) (v - E_c)
so channel c adds g_c (x_c(v_th) - x_c,rest)(v_th - E_c) mV to the rheobase (LIF alone: v_th - v_rest).
Two regimes: 'fast' (input within a few ms: A activation, T activation and NaP follow v;
A/T inactivation, M and h stay at rest) and 'sustained' (every voltage gate at steady state).
Spike-triggered Kv2/BK/SK are excluded (zero below threshold). v_rest -52, v_th -45 (m4 defaults;
declared). Densities from channels.expression_factors at the registry priors.

    uv run python scripts/probes/intrinsic_rheobase.py
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from flyemu import channels as ch  # noqa: E402
from flyemu.channels import KINETICS as K, _boltz  # noqa: E402

V_REST, V_TH = -52.0, -45.0
nrn = pd.read_parquet("data/cache/male_cns_neurons.parquet")
f, src = ch.expression_factors(nrn.type.fillna("untyped").to_numpy(), 0.5, nrn.bodyId.to_numpy())
g = {c: ch.CHANNELS[c][3] * f[c] for c in ch.CHANNELS}
E = {c: ch.CHANNELS[c][1] for c in ch.CHANNELS}
xr = ch.Intrinsic._steady(np.array([V_REST], np.float32))
xs = ch.Intrinsic._steady(np.array([V_TH], np.float32))
b_r = _boltz(V_REST, *K["A_inact"][:2]); th_r = _boltz(V_REST, *K["T_inact"][:2])
xf = dict(xr)
xf["A"] = _boltz(V_TH, *K["A_act"][:2]) ** 3 * b_r
xf["T"] = _boltz(V_TH, *K["T_act"][:2]) ** 2 * th_r
xf["NaP"] = xs["NaP"]
out = {"v_rest": V_REST, "v_th": V_TH, "lif_rheobase_mV": V_TH - V_REST}
for name, x in (("fast", xf), ("sustained", xs)):
    add = {c: g[c] * float(np.ravel(x[c])[0] - xr[c][0]) * (V_TH - E[c]) for c in ("A", "M", "h", "T", "NaP")}
    tot = (V_TH - V_REST) + sum(add.values())
    out[name] = {"per_channel_mV_median": {c: round(float(np.median(a)), 2) for c, a in add.items()},
                 "rheobase_ratio_pct": {p: round(float(np.percentile(tot / (V_TH - V_REST), p)), 2) for p in (10, 50, 90)},
                 "frac_cells_ratio_over_2": round(float((tot > 2 * (V_TH - V_REST)).mean()), 3)}
out["gate_open_fraction"] = {"rest": {c: round(float(v[0]), 4) for c, v in xr.items()},
                             "v_th_steady": {c: round(float(v[0]), 4) for c, v in xs.items()},
                             "A_fast": round(float(np.ravel(xf["A"])[0]), 4)}
print(json.dumps(out, indent=1))
json.dump(out, open("runs/s11/rung1/rheobase.json", "w"), indent=1)
