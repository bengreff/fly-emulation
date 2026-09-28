"""B20 antenna oscillator (s10): what it claims, and the legacy path untouched."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu.extrasenses import Antenna  # noqa: E402


def _drive(f_hz, a=1e-3, f0=250.0, q=1.5, ms=200.0, dt=0.1):
    ant = Antenna(f0, q)
    th = []
    for k in range(int(ms / dt)):
        t = k * dt / 1000.0
        th.append(ant.step(0.2 + a * np.sin(2 * np.pi * f_hz * t), dt)[0])
    th = np.array(th[len(th) // 2:])
    return th.mean(), (th.max() - th.min()) / 2


def test_static_input_gives_the_legacy_deflection():
    ant = Antenna(250.0, 1.5)
    for _ in range(2000):
        th, hp = ant.step(0.2, 0.1)
    assert abs(th - 0.2) < 1e-9 and abs(hp) < 1e-9


def test_resonance_amplifies_near_f0_and_filters_high_frequencies():
    m, a_low = _drive(20.0)
    _, a_res = _drive(250.0)
    _, a_high = _drive(2000.0)
    assert abs(m - 0.2) < 1e-4
    assert abs(a_low / 1e-3 - 1.0) < 0.05          # quasi-static below resonance
    assert 1.3 < a_res / 1e-3 < 1.7                # ~Q at f0
    assert a_high / 1e-3 < 0.05                    # mass-dominated above


def test_sound_drives_jo_ab_only_with_the_oscillator():
    REPO = Path(__file__).resolve().parents[1]
    import pytest
    if not (REPO / "data/cache/male_cns_edges.parquet").exists():
        pytest.skip("no graph cache")
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile="m4", min_synapses=5,
                   overrides={"sense:antenna|oscillator": 1.0})
    import mujoco
    mujoco.mj_forward(org.body.sim.mj_model, org.body.sim.mj_data)   # head pose defined
    org.world.sound_mm_s, org.world.sound_hz = 5.0, 250.0
    org.world.sound_dir = org.body.sim.mj_data.xmat[org.extra.body_ids["c_head"]].reshape(3, 3)[:, 0]
    ex = org.extra
    ab = ex.channels["jo_ab"].rows
    got = []
    for s in range(300):
        got.append(ex.drive(org.world, org.body, org.body.observe(), org.timestep_ms)[ab].mean())
    assert max(got[100:]) > 1.0                      # mV: sound reaches JO-A/B
    org.world.sound_mm_s = 0.0
    quiet = [ex.drive(org.world, org.body, org.body.observe(), org.timestep_ms)[ab].mean()
             for _ in range(1500)]
    assert quiet[-1] < 0.2 * max(got[100:])
