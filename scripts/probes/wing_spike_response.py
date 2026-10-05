"""Session 12 B (wing rest): what one wing motor-neuron spike does to a folded wing
on the plain body (no network), under the m9t wing settings.

One spike is the motor path's unit state: torque fps * exp(-t / tau_act) on one wing
actuator. Reports, per hinge axis and sign, the resting angle, the peak excursion and
its time, and the excursion left at 100, 200 and 500 ms. Hinge stiffness, torque per
spike and the range set are arguments, so a candidate change can be predicted before
the closed-loop gate.

    uv run python scripts/probes/wing_spike_response.py --k 1 --fps 2.734 --out runs/s12/wing/spike_k1.json
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import flight, passive  # noqa: E402
from flyemu.body import Body  # noqa: E402

AXES = ("yaw", "roll", "pitch")


def response(axis: str, sign: int, k: float | None, fps: float, tau_ms: float, ranges: int,
             settle_ms: float = 100.0, ms: float = 500.0, spikes: int = 1, isi_ms: float = 1.5) -> dict:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        b = Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    if ranges:
        flight.apply_wing_ranges(b, flight.WING_RANGE_MEASURED_DEG if ranges == 2 else None)
    passive.fold_wings(b)
    jid = {a: mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, f"flybody/c_thorax-l_wing-{a}") for a in AXES}
    if k is not None:
        for j in jid.values():
            m.jnt_stiffness[j] = k
    names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_ACTUATOR, i) or "" for i in range(m.nu)]
    motor = [n for n in names if n.endswith("-motor")]
    ai = motor.index(f"flybody/c_thorax-l_wing-{axis}-motor")
    qa = m.jnt_qposadr[jid[axis]]
    dt_ms = m.opt.timestep * 1000.0
    z = np.zeros(b.n_actuators)
    for _ in range(int(settle_ms / dt_ms)):
        b.actuate(z); b.step()
    q0 = float(d.qpos[qa])
    tr = np.empty(int(ms / dt_ms))
    for s in range(len(tr)):
        t = s * dt_ms
        tq = z.copy(); tq[ai] = sign * fps * sum(np.exp(-(t - n * isi_ms) / tau_ms) for n in range(spikes) if t >= n * isi_ms)
        b.actuate(tq); b.step(); tr[s] = d.qpos[qa]
    dq = np.degrees(tr - q0)
    i = int(np.argmax(np.abs(dq)))
    at = lambda t: round(float(dq[min(int(t / dt_ms), len(dq)) - 1]), 2)  # noqa: E731
    return {"axis": axis, "sign": sign, "spikes": spikes, "isi_ms": isi_ms, "rest_deg": round(float(np.degrees(q0)), 2),
            "peak_deg": round(float(dq[i]), 2), "peak_ms": round(i * dt_ms, 1),
            "left_100ms": at(100), "left_200ms": at(200), "left_500ms": at(500),
            "stiffness_uNmm_per_rad": float(m.jnt_stiffness[jid[axis]]),
            "damping": float(m.dof_damping[m.jnt_dofadr[jid[axis]]]),
            "range_deg": np.degrees(m.jnt_range[jid[axis]]).round(1).tolist()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=float, default=None, help="wing hinge stiffness, uN*mm/rad (default: flybody)")
    ap.add_argument("--fps", type=float, default=2.734, help="torque per spike, uN*mm (m9t wing row)")
    ap.add_argument("--tau", type=float, default=30.0, help="motor-unit decay, ms (motor path tau_act)")
    ap.add_argument("--ranges", type=int, default=1, help="joint:wing|range_by_function (0, 1, 2)")
    ap.add_argument("--spikes", type=int, default=1, help="spikes in the burst")
    ap.add_argument("--isi", type=float, default=1.5, help="interval between burst spikes, ms")
    ap.add_argument("--axes", default=",".join(AXES))
    ap.add_argument("--out", default=str(REPO / "runs/s12/wing/spike_response.json"))
    a = ap.parse_args()
    rows = [response(ax, s, a.k, a.fps, a.tau, a.ranges, spikes=a.spikes, isi_ms=a.isi)
            for ax in a.axes.split(",") for s in (1, -1)]
    for r in rows:
        print(r)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"k": a.k, "fps": a.fps, "tau_ms": a.tau, "ranges": a.ranges,
                                       "spikes": a.spikes, "isi_ms": a.isi,
                                       "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
