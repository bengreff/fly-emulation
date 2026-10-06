"""Clock-cell firing at set circadian phases, brain only, open loop (diagnostic).

Checks the N26 clock coupling (internal_state.py: g_clock_mv x cos(2 pi (ct - peak) / 24) onto the
morning and evening groups) against recorded day-night firing: DN1p "fire at ~10Hz in the morning
(Zeitgeber Time, ZT0-4) and are nearly silent in the evening (ZT8-12)" (Flourakis et al. 2015 Cell,
whole-brain explant, read). The clock state is set to each phase (ZT = CT, entrained), the tonic drive
is applied every step with the profile's own noise, and the mean rate per clock type is reported.

    uv run python scripts/probes/clock_phase_rates.py --profile m9r --ct 2,10 --out runs/s12/clock/m9r.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, internal_state, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

TYPES = ["DN1pA", "DN1pB", "s-LNv", "l-LNv", "LNd_b", "LNd_c", "5thsLNv_LNd6", "DN1a"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profiles.WORKING_PROFILE)
    ap.add_argument("--ct", default="2,10")
    ap.add_argument("--duration-ms", type=float, default=1000.0)
    ap.add_argument("--timestep-ms", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", action="append", default=[], metavar="ENTITY|PROP=V")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    reg = Registry(Policy.MINIMAL)
    reg.overrides["state:organs|model"] = 1.0
    for s in a.set:
        k, v = s.split("=")
        reg.overrides[k] = float(v)
    profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=a.timestep_ms)
    el = electrical.build(reg, conn)
    st = internal_state.build(reg, conn)
    types = conn.neurons.type.fillna("").to_numpy()
    sel = {t: np.flatnonzero(types == t) for t in TYPES}
    print({t: len(v) for t, v in sel.items()}, "g_clock_mv", st.p["g_clock_mv"])
    res = {"profile": a.profile, "set": a.set, "g_clock_mv": st.p["g_clock_mv"], "ct": {}}
    for ct in [float(x) for x in a.ct.split(",")]:
        st.organs.z = complex(np.exp(1j * 2 * np.pi * ct / 24.0))
        st._refresh()
        tonic = st.tonic().astype(np.float32)
        net = lif.Network(conn, params, a.timestep_ms, rng=np.random.default_rng(a.seed))
        net.elec = el if len(el[0]) else None
        counts = np.zeros(conn.n, np.int32)
        n = int(round(a.duration_ms / a.timestep_ms))
        for _ in range(n):
            spk = net.step(external_mv=tonic)
            if spk.size:
                counts[spk] += 1
        hz = counts / (a.duration_ms / 1000.0)
        row = {t: {"n": len(i), "mean_hz": float(hz[i].mean()) if len(i) else None,
                   "per_cell": hz[i].round(1).tolist(), "tonic_mv": float(tonic[i].mean()) if len(i) else None}
               for t, i in sel.items()}
        row["_all_mean_hz"] = float(hz.mean())
        res["ct"][str(ct)] = row
        print(f"CT {ct:g}: " + "  ".join(f"{t} {r['mean_hz']:.1f} Hz ({r['tonic_mv']:+.1f} mV)"
                                         for t, r in row.items() if isinstance(r, dict) and r["n"])
              + f"  all {hz.mean():.2f}")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
