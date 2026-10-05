"""Session 12 B (F-DAMP-2): the dead-fly test under Wang et al. 2025's protocol.

Their motor-silenced flies start standing and lose active force over about
100 ms (tau of their model's force decay; MN inactivation measured). The
standard dead-fly test releases the placed fly at once. Here the placed fly
first gets the joint torques that hold it there, measured as in
stand_budget.py (stiff instrument springs to the placed pose, 300 ms, torque
read off), and those torques then decay as exp(-t / tau). Body, scoring and
criteria are deadfly.run / deadfly.score unchanged.

The hold torque is not a model quantity: it stands in for whatever active force
held the real fly up before silencing (F-STAND-3: the model has none).

    uv run python scripts/probes/deadfly_decay.py --label s12/deadfly_decay_damp --set "joint:leg|damping_source=1" [--tau-ms 100]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco as mj
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import deadfly, model_data, passive  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.registry import Registry  # noqa: E402

LEGS = ("lf", "lm", "lh", "rf", "rm", "rh")
K_HOLD, D_HOLD = 200.0, 0.5          # instrument, as stand_budget.py


def build(sets: dict[str, float]) -> Body:
    """The dead_fly.py --template body with the given switches."""
    reg = Registry("minimal")
    reg.overrides.update(model_data.TEMPLATE_SWITCHES)
    reg.overrides.update(sets)
    b = Body(vision=False)
    passive.register(reg, b)
    passive.register_coxa(reg, b)
    passive.register_ctr(reg, b)
    passive.register_rest(reg, b)
    passive.register_wings(reg, b)
    passive.register_noslip(reg, b)
    if int(reg.require("joint:wing", "range_by_function", units="enum", model_use="", minimal=0)):
        from flyemu import flight
        flight.apply_wing_ranges(b)
    return b


def leg_hinges(m, pre: str) -> list[int]:
    return [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE
            and any(f"{L}_" in (m.joint(j).name or "") for L in LEGS)]


def hold_torques(sets: dict[str, float], ms: float = 300.0) -> tuple[np.ndarray, list[str]]:
    b = build(sets)
    m, d = b.sim.mj_model, b.sim.mj_data
    b.reset()
    deadfly.place_standing(b)
    hj = leg_hinges(m, f"{b.fly.name}/")
    qa = np.array([m.jnt_qposadr[j] for j in hj]); va = np.array([m.jnt_dofadr[j] for j in hj])
    q_hold = d.qpos[qa].copy()
    k0, ref0 = m.jnt_stiffness[hj].copy(), m.qpos_spring[qa].copy()
    m.jnt_stiffness[hj] += K_HOLD
    m.qpos_spring[qa] = (k0 * ref0 + K_HOLD * q_hold) / (k0 + K_HOLD)
    m.dof_damping[va] += D_HOLD
    b.set_adhesion(np.zeros(len(b.adhesion_names)))
    zero = np.zeros(b.n_actuators)
    for _ in range(int(round(ms / (m.opt.timestep * 1e3)))):
        b.actuate(zero)
        b.step()
    return K_HOLD * (q_hold - d.qpos[qa]), [m.joint(j).name for j in hj]


class DecayingHold:
    """Adds tq * exp(-t / tau) to qfrc_applied on the leg DOFs; per DOF, its previous
    share is removed unless an earlier hook rewrote that DOF this step (as jump.TTM)."""

    def __init__(self, dofs: np.ndarray, tq: np.ndarray, tau_ms: float, dt_ms: float):
        self.dofs, self.tq, self.tau, self.dt = dofs, tq, tau_ms, dt_ms
        self.k, self.last, self.written = 0, np.zeros(len(dofs)), None

    def __call__(self, d) -> None:
        tq = self.tq * np.exp(-self.k * self.dt / self.tau)
        self.k += 1
        cur = d.qfrc_applied[self.dofs].copy()
        base = cur if self.written is None else np.where(cur == self.written, cur - self.last, cur)
        d.qfrc_applied[self.dofs] = base + tq
        self.last, self.written = tq, d.qfrc_applied[self.dofs].copy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--tau-ms", type=float, default=100.0, help="Wang et al. 2025 model force-decay tau (inferred)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    a = ap.parse_args()
    sets = {k: float(v) for k, v in (x.split("=") for x in a.set)}
    tq, names = hold_torques(sets)
    b = build(sets)
    m = b.sim.mj_model
    jid = [mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, n) for n in names]
    b.passive_hooks = list(getattr(b, "passive_hooks", ())) + [
        DecayingHold(np.array([m.jnt_dofadr[j] for j in jid]), tq, a.tau_ms, m.opt.timestep * 1e3)]
    tr = deadfly.run(duration_ms=a.ms, body=b)
    s = deadfly.score(tr)
    z = tr.thorax_z
    t90 = float(tr.t_ms[np.argmax(z <= z[0] - 0.9 * (z[0] - z[-1]))])
    s["decay_protocol"] = dict(tau_ms=a.tau_ms, hold_abs_sum_uNmm=round(float(np.abs(tq).sum()), 2),
                               t90_ms=t90, z_at_ms={t: round(float(np.interp(t, tr.t_ms, z)), 3)
                                                    for t in (0, 50, 100, 200, 400, 1000)}, sets=sets)
    out = REPO / "runs" / a.label
    out.mkdir(parents=True, exist_ok=True)
    (out / "deadfly.json").write_text(json.dumps(s, indent=1, default=str))
    for k, v in s.items():
        print(f"{k:18s} {v.get('verdict', ''):8s} " + json.dumps({x: y for x, y in v.items()
                                                                  if x not in ('verdict', 'criterion')}, default=str)[:400])


if __name__ == "__main__":
    main()
