"""B15 jump muscle and the GF->TTMn path (s10)."""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
needs_graph = pytest.mark.skipif(not (REPO / "data/cache/male_cns_edges.parquet").exists(),
                                 reason="no graph cache")


def _escape(ov):
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5, overrides=ov)
    t = org.conn.neurons.type.fillna("").to_numpy()
    gf, ttmn = np.flatnonzero(t == "DNp01"), np.flatnonzero(t == "TTMn")
    d = org.body.sim.mj_data
    for _ in range(300):                               # settle 30 ms
        org.motor_step(org.net.step())
    z0, first, zs = float(d.qpos[2]), None, []
    for s in range(200):                               # 20 ms after one GF spike volley
        sp = org.net.step(kick=(gf, 50.0) if s == 0 else None)
        if first is None and np.isin(ttmn, sp).any():
            first = s * org.timestep_ms
        org.motor_step(sp)
        zs.append(float(d.qpos[2]))
    assert sum(w.number for w in d.warning) == 0
    return first, max(zs) - z0


@needs_graph
def test_gf_drives_ttmn_fast_and_the_ttm_lifts_the_body():
    ov = {"electrical:DNp01->TTMn|spike_coupling": 20.0}
    lat, dz_off = _escape(ov)
    assert lat is not None and lat <= 2.0               # GF->TTMn ~0.8 ms in the animal (lead)
    lat2, dz_on = _escape({**ov, "jump:ttm|model": 1.0})
    assert lat2 == lat
    assert dz_on > dz_off + 0.05                         # the jump muscle raises the thorax
