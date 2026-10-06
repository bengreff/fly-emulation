"""Per-cell parameters and static input of named cells under two profiles (diagnostic, no simulation).

Built for the leg sugar route (F-TASTE-LEG-1, DECISIONS 22:04): with feedforward inhibition at Bract 2
removed, Roundup (GNG108) fires at 1.3-10 Hz under m2 but 0-1.3 Hz under m9r for similar Bract 2 rates.
This prints, for each named cell and profile, every per-cell LIF field that differs between the profiles,
the intrinsic conductances (rung 1), the static rheobase gap v_th - v_rest - spont, and the summed PSP
amplitude of its inputs by sign and by named presynaptic type (sign x efficacy x synapses x release gain x
input gain, mV per presynaptic spike, and the network's final edge weight after edge scales and the
conductance conversion; derived from the build, not a simulation).

    uv run python scripts/probes/cell_params_compare.py --profiles m2 m9r \
        --cells 268258,14157,26764,523040 --pre DNge173,DNge174,AN01B004,GNG159,GNG093,GNG250
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

FIELDS = ("tau_m", "v_rest", "v_th", "v_reset", "t_ref", "tau_s", "tau_s_inh", "spont_mv", "noise_mv",
          "input_gain", "release_gain", "gabab_fraction", "machr_fraction", "mglur_fraction", "nmda_fraction",
          "adapt_mv", "tau_adapt", "std_u", "cond", "e_inh", "inh_cond_scale", "cond_reference")


def per_cell(v, i):
    a = np.asarray(v)
    return float(a.ravel()[i]) if a.ndim and a.size > 1 else (float(a) if np.ndim(a) == 0 else float(a.ravel()[0]))


def describe(profile: str, cells: list[int], pre_types: list[str], min_syn: int) -> dict:
    reg = Registry(Policy.MINIMAL)
    profiles.apply(reg, profile)
    conn = connectome.build(reg, min_synapses=min_syn)
    p = lif.default_params(reg, conn, timestep_ms=0.1)
    nrn = conn.neurons
    idx = conn.index_of(np.array(cells))
    pre_of = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    net = lif.Network(conn, p, 0.1, rng=np.random.default_rng(0))
    w0 = (conn.sign[pre_of] * conn.efficacy_mv * conn.weight_syn
          * np.broadcast_to(np.asarray(p.release_gain, np.float32), (conn.n,))[pre_of]
          * net.input_gain[conn.indices])                    # mV per presynaptic spike, before cond
    amp = w0
    out = {}
    for b, i in zip(cells, idx):
        if i < 0:
            out[str(b)] = "absent"
            continue
        r = {"instance": str(nrn.instance.iat[i])}
        for f in FIELDS:
            if hasattr(p, f):
                v = getattr(p, f)
                r[f] = per_cell(v, i) if not isinstance(v, (bool, np.bool_)) else bool(v)
        r["gap_mV"] = round(r["v_th"] - r["v_rest"] - r.get("spont_mv", 0.0), 3)
        ich = p.intrinsic
        if ich is not None:
            r["intrinsic_g"] = {c: round(float(np.asarray(g).ravel()[i]), 4) for c, g in ich.g.items()}
        m = conn.indices == i
        r["in_exc_mV"] = round(float(amp[m & (amp > 0)].sum()), 3)
        r["in_inh_mV"] = round(float(amp[m & (amp < 0)].sum()), 3)
        r["net_w_exc"] = round(float(net.w[m & (net.w > 0)].sum()), 4)   # after edge scales and cond
        r["net_w_inh"] = round(float(net.w[m & (net.w < 0)].sum()), 4)
        by = {}
        pre_type = nrn.type.fillna("").to_numpy()[pre_of]
        for t in pre_types:
            sel = m & (pre_type == t)
            by[t] = {"edges": int(sel.sum()), "syn": int(conn.weight_syn[sel].sum()),
                     "psp_sum_mV": round(float(amp[sel].sum()), 3), "net_w": round(float(net.w[sel].sum()), 4)}
        r["from"] = by
        out[str(b)] = r
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", nargs=2, default=["m2", profiles.WORKING_PROFILE])
    ap.add_argument("--cells", required=True)
    ap.add_argument("--pre", default="")
    ap.add_argument("--min-synapses", type=int, default=profiles.WORKING_MIN_SYNAPSES)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    cells = [int(x) for x in a.cells.split(",")]
    pre = [t for t in a.pre.split(",") if t]
    res = {pr: describe(pr, cells, pre, a.min_synapses) for pr in a.profiles}
    print(json.dumps(res, indent=1, default=str))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
