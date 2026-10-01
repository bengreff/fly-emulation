"""Diagnostic (s11): body-only joint transfer. Tethered body with the working
profile's passive mechanics; a sinusoidal torque (uN*mm) on one leg actuator;
reports the joint's peak-to-peak swing at the drive frequency. No brain, no
muscles: separates the body's own low-pass from the motor path."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import passive, profiles  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.registry import Registry  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--joints", default="lf_coxa-lf_trochanterfemur-pitch,lf_trochanterfemur-lf_tibia-pitch,c_thorax-lf_coxa-pitch")
    ap.add_argument("--freqs", default="1,2,5,10,20")
    ap.add_argument("--amp", type=float, default=1.5, help="torque amplitude (uN*mm)")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    reg = Registry("minimal")
    reg.overrides.update({k: float(v) for k, v in (s.split("=") for s in a.set)})
    profiles.apply(reg, profiles.WORKING_PROFILE)
    res = {"profile": profiles.WORKING_PROFILE, "amp": a.amp, "set": a.set, "rows": []}
    for jn in a.joints.split(","):
        for f in [float(x) for x in a.freqs.split(",")]:
            body = Body(vision=False)
            passive.register(reg, body)
            passive.register_rest(reg, body)
            m, d = body.sim.mj_model, body.sim.mj_data
            names = [x.split("/")[-1].removesuffix("-motor") for x in body.actuator_names]
            ka = [i for i, x in enumerate(names) if x.endswith(jn)]
            j = [i for i in range(m.njnt) if m.joint(i).name.endswith(jn)]
            assert len(ka) == 1 and len(j) == 1, (jn, ka, j)
            qa, da = m.jnt_qposadr[j[0]], m.jnt_dofadr[j[0]]
            q0 = d.qpos[:7].copy(); q0[2] += 5.0
            dt = m.opt.timestep
            n_settle, n_run = int(0.3 / dt), int(1.0 / dt)
            Q = []
            tq = np.zeros(len(names), np.float32)
            for s in range(n_settle + n_run):
                t = s * dt
                tq[ka[0]] = a.amp * np.sin(2 * np.pi * f * t) if s >= n_settle else 0.0
                body.actuate(tq)
                body.step()
                d.qpos[:7] = q0; d.qvel[:6] = 0.0
                if s >= n_settle:
                    Q.append(d.qpos[qa])
            Q = np.array(Q) - np.mean(Q)
            p = np.abs(np.fft.rfft(Q)) ** 2
            fr = np.fft.rfftfreq(len(Q), dt)
            at = np.abs(fr - f) <= 1.0
            row = {"joint": jn, "f": f, "p2p_at_f_rad": round(float(4 * np.sqrt(p[at].sum()) / len(Q)), 4),
                   "damping": float(m.dof_damping[da]), "stiffness": float(m.jnt_stiffness[j[0]]),
                   "warnings": int(sum(w.number for w in d.warning))}
            print(json.dumps(row), flush=True)
            res["rows"].append(row)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
