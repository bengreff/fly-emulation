"""The dead-fly test (docs/CONSTRUCTION.md, "Acceptance tests for the template").

The brain is silent: no neuron fires and no motor unit is active, so every
actuator (joint motors, tendon actuators, tarsal adhesion) is held at zero and
the body is exactly as built. The fly is placed standing in its neutral pose
with its lowest point just touching the ground, then left alone.

A real fly with silenced motor neurons (eLife 2025, PMC12324252):
  - collapses on 92/92 trials, starting within ~40 ms (passive torques are
    ~70x below what holds the weight);
  - its legs settle toward a measured passive rest posture (prothoracic
    protracted, metathoracic retracted relative to mesothoracic);
and it keeps its wings folded and head and abdomen at rest. The acceptance
criteria on the model are also: no joint within 3% of a range limit for more
than 5% of the time, and mechanical energy that decays without jitter.

`run()` returns the traces and `score()` the metrics with pass/fail. Criteria
that need measured data not yet entered (the rest posture, task 4) are
reported as "pending".
"""
from __future__ import annotations

from dataclasses import dataclass, field

import mujoco as mj
import numpy as np

from .body import Body

LIMIT_BAND = 0.03          # within 3% of the range from either end
LIMIT_TIME = 0.05          # for more than 5% of the time
COLLAPSE_ONSET_MS = 40.0   # measured: falls start within ~40 ms (eLife 2025)
ONSET_DROP_MM = 0.05       # thorax drop that counts as the start of the fall


@dataclass
class Trace:
    t_ms: np.ndarray
    thorax_z: np.ndarray
    qpos_hinge: np.ndarray        # (T, n_hinge)
    qvel_hinge: np.ndarray
    energy: np.ndarray            # (T, 2) potential, kinetic (g mm^2 / s^2 = nJ)
    body_ground_contact: np.ndarray   # thorax/abdomen/head touching the floor
    hinge_names: list[str]
    hinge_range: np.ndarray       # (n_hinge, 2)
    q0: np.ndarray
    info: dict = field(default_factory=dict)


def _hinges(m) -> list[int]:
    return [j for j in range(m.njnt) if m.jnt_type[j] == mj.mjtJoint.mjJNT_HINGE]


def place_standing(body: Body, step_mm: float = 0.002) -> float:
    """Lower the free joint until the first contact with the floor appears.
    Returns the thorax height. The neutral pose is flybody's (legs extended)."""
    m, d = body.sim.mj_model, body.sim.mj_data
    floor = [g for g in range(m.ngeom) if m.geom_bodyid[g] == 0]

    def touching() -> bool:
        mj.mj_forward(m, d)
        return any(d.contact[i].geom1 in floor or d.contact[i].geom2 in floor
                   for i in range(d.ncon))

    while not touching():
        d.qpos[2] -= step_mm
    d.qpos[2] += step_mm            # last contact-free height, gap < step_mm
    d.qvel[:] = 0
    mj.mj_forward(m, d)
    return float(d.qpos[2])


def run(duration_ms: float = 1000.0, sample_ms: float = 1.0,
        body: Body | None = None, activation: np.ndarray | None = None,
        activation_tau_ms: float | None = None) -> Trace:
    """Simulate the dead fly. `activation` (optional, per torque actuator)
    with `activation_tau_ms` is the decaying-drive variant: torques start at
    `activation` and decay exponentially, as after sudden MN silencing."""
    b = body or Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    m.opt.enableflags |= mj.mjtEnableBit.mjENBL_ENERGY
    b.reset()
    place_standing(b)
    hj = _hinges(m)
    hadr = np.array([m.jnt_qposadr[j] for j in hj])
    vadr = np.array([m.jnt_dofadr[j] for j in hj])
    names = [mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j).split("/")[-1] for j in hj]
    thorax = next(i for i in range(m.nbody)
                  if (mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, i) or "").endswith("c_thorax"))
    trunk = {i for i in range(m.nbody) if any(
        k in (mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, i) or "")
        for k in ("thorax", "abdomen", "head"))}
    floor = {g for g in range(m.ngeom) if m.geom_bodyid[g] == 0}
    zero = np.zeros(b.n_actuators)
    b.set_adhesion(np.zeros(len(b.adhesion_names) // 1 if b.adhesion_names else 0))
    d.ctrl[:] = 0.0
    dt_ms = m.opt.timestep * 1e3
    n_steps = int(round(duration_ms / dt_ms))
    every = max(1, int(round(sample_ms / dt_ms)))
    q0 = d.qpos[hadr].copy()
    rows = []
    for k in range(n_steps + 1):
        if k % every == 0:
            mj.mj_energyPos(m, d)
            mj.mj_energyVel(m, d)
            gc = False
            for i in range(d.ncon):
                c = d.contact[i]
                if c.geom1 in floor and m.geom_bodyid[c.geom2] in trunk:
                    gc = True
                elif c.geom2 in floor and m.geom_bodyid[c.geom1] in trunk:
                    gc = True
            en = d.energy.copy()
            en[0] += b.extra_potential()                 # coupled springs etc.
            rows.append((k * dt_ms, d.xpos[thorax, 2], d.qpos[hadr].copy(),
                         d.qvel[vadr].copy(), en, gc))
        if k == n_steps:
            break
        if activation is not None:
            b.actuate(activation * np.exp(-k * dt_ms / activation_tau_ms))
        else:
            b.actuate(zero)
        b.step()
    t, z, qp, qv, e, gc = zip(*rows)
    from .legangles import paper_angles
    bid = lambda n: mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, f"{b.fly.name}/{n}")  # noqa: E731
    phi_end = {L: float(paper_angles(d.xpos[bid(f"{L}_trochanterfemur")], d.xpos[bid(f"{L}_tibia")],
                                     d.xpos[bid(f"{L}_tarsus1")], right=L.startswith("r"))[1])
               for L in ("lf", "lm", "lh", "rf", "rm", "rh")}
    # MuJoCo resets the state silently when it diverges; a reset run is invalid
    names_w = [n for n in dir(mj.mjtWarning) if n.startswith("mjWARN_")]
    warn = {n: int(d.warning[int(getattr(mj.mjtWarning, n))].number) for n in names_w
            if d.warning[int(getattr(mj.mjtWarning, n))].number}
    return Trace(np.array(t), np.array(z), np.array(qp), np.array(qv), np.array(e),
                 np.array(gc), names, m.jnt_range[hj].copy(), q0,
                 info=dict(ctrl_max=float(np.abs(d.ctrl).max()), timestep_ms=dt_ms,
                           mujoco_warnings=warn, phi_end=phi_end))


def limit_occupancy(q: np.ndarray, rng: np.ndarray, band: float = LIMIT_BAND) -> np.ndarray:
    """Fraction of samples each joint spends within `band` of either range end."""
    span = rng[:, 1] - rng[:, 0]
    lo = q <= rng[:, 0] + band * span
    hi = q >= rng[:, 1] - band * span
    return (lo | hi).mean(axis=0)


def _group(name: str) -> str:
    for key, g in (("wing", "wing"), ("haltere", "haltere"), ("abdomen", "abdomen"),
                   ("head", "head"), ("rostrum", "proboscis"), ("haustellum", "proboscis"),
                   ("labrum", "proboscis"), ("antenna", "antenna"), ("tarsus", "tarsus")):
        if key in name:
            return g
    return "leg"


def score(tr: Trace) -> dict:
    """Metrics against the acceptance criteria; each has value and verdict."""
    out: dict = {}
    bad_run = {k: v for k, v in tr.info.get("mujoco_warnings", {}).items()
               if k in ("mjWARN_BADQACC", "mjWARN_BADQPOS", "mjWARN_BADQVEL")}
    out["valid_run"] = dict(mujoco_warnings=tr.info.get("mujoco_warnings", {}),
                            actuator_max=tr.info.get("ctrl_max"),
                            verdict="pass" if not bad_run and tr.info.get("ctrl_max", 0) == 0 else "fail",
                            criterion="no divergence reset; every actuator zero")
    z = tr.thorax_z
    drop = z[0] - z
    onset = tr.t_ms[np.argmax(drop > ONSET_DROP_MM)] if (drop > ONSET_DROP_MM).any() else None
    trunk_down = bool(tr.body_ground_contact[-1])
    out["collapse"] = dict(
        thorax_start_mm=round(float(z[0]), 3), thorax_end_mm=round(float(z[-1]), 3),
        onset_ms=None if onset is None else float(onset), trunk_on_ground_at_end=trunk_down,
        verdict="pass" if (onset is not None and onset <= COLLAPSE_ONSET_MS and trunk_down) else "fail",
        criterion=f"fall starts within {COLLAPSE_ONSET_MS:.0f} ms and the trunk reaches the ground")
    occ = limit_occupancy(tr.qpos_hinge, tr.hinge_range)
    bad = [(n, round(float(o), 3)) for n, o in zip(tr.hinge_names, occ) if o > LIMIT_TIME]
    groups: dict[str, int] = {}
    for n, _ in bad:
        groups[_group(n)] = groups.get(_group(n), 0) + 1
    out["range_limits"] = dict(
        n_joints=len(tr.hinge_names), n_over=len(bad), by_group=groups, worst=sorted(bad, key=lambda x: -x[1])[:10],
        verdict="pass" if not bad else "fail",
        criterion="no joint within 3% of a range limit for > 5% of the time")
    e = tr.energy.sum(axis=1)
    ke = tr.energy[:, 1]
    # energy must not rise: largest increase of total energy over any 10 ms window
    w = max(1, int(round(10.0 / (tr.t_ms[1] - tr.t_ms[0]))))
    rise = float(np.max(e[w:] - e[:-w])) if len(e) > w else 0.0
    tail = tr.t_ms >= tr.t_ms[-1] - 100.0
    vrms_tail = float(np.sqrt(np.mean(tr.qvel_hinge[tail] ** 2)))
    out["energy"] = dict(
        total_start=float(e[0]), total_end=float(e[-1]), max_rise_10ms=rise,
        ke_peak=float(ke.max()), ke_end=float(ke[-1]),
        joint_vel_rms_last_100ms_rad_s=round(vrms_tail, 4),
        verdict="pass" if (rise <= 1e-3 * max(abs(e[0]), 1e-12) and vrms_tail < 0.5) else "fail",
        criterion="total energy never rises by >0.1% of its start in 10 ms; hinge-velocity rms < 0.5 rad/s over the last 100 ms")
    dq = tr.qpos_hinge[-1] - tr.q0
    posture = {}
    for g in ("wing", "head", "abdomen", "haltere"):
        idx = [i for i, n in enumerate(tr.hinge_names) if _group(n) == g]
        if idx:
            posture[g] = dict(max_abs_change_deg=round(float(np.degrees(np.abs(dq[idx]).max())), 1),
                              at_limit=[tr.hinge_names[i] for i in idx if occ[i] > LIMIT_TIME])
    at_rest = all(not v["at_limit"] and v["max_abs_change_deg"] < 20 for v in posture.values())
    out["non_leg_at_rest"] = dict(**posture, verdict="pass" if at_rest else "fail",
                                  criterion="wings, head, abdomen, halteres stay near their rest pose (< 20 deg, off limits)")
    # rest posture (eLife 2025): prothoracic more protracted and metathoracic
    # more retracted than mesothoracic, i.e. phi front < middle < hind
    phi = tr.info.get("phi_end", {})
    order = all(phi[f"{s}f"] < phi[f"{s}m"] < phi[f"{s}h"] for s in "lr") if phi else None
    out["leg_rest_posture"] = dict(
        phi_end_deg={k: round(v, 1) for k, v in phi.items()},
        verdict="pending" if order is None else ("pass" if order else "fail"),
        criterion="phi (protraction angle, eLife definition) front < middle < hind on both sides")
    return out
