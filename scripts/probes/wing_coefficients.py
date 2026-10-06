"""Session 12 B (flight coefficients beyond one condition): the model wing's
translational lift and drag coefficients against angle of attack, compared with
the robotic-fly measurements of Dickinson, Lehmann & Sane 1999 (Science 284:1954;
dynamically scaled Drosophila wing, Re ~136, steady translation):

    CL(a) = 0.225 + 1.58 sin(2.13 a - 7.20 deg)
    CD(a) = 1.92 - 1.55 cos(2.04 a - 9.82 deg)

Method: the fly is held still, gravity off, fluid forces off on every geom but the
left wing membrane; a uniform wind U at angle a to the chord, in the chord-normal
plane, is the only flow. The free joint's translational generalized force is then
the fluid force on that wing (world frame). Coefficients use the membrane
ellipsoid's planform area pi*a*b (the area the MuJoCo model sees).
F-FLIGHT-2 fixed one number (Kutta lift 3.1) at one condition (hover lift = weight);
this tests the force shape across angles that the hover average hides.

    uv run python scripts/probes/wing_coefficients.py [--kutta 1 3.1] [--blade] [--out runs/s12/flight]

--blade adds the blade-element wing (aero:wing|model 1, flight.BladeElementWing),
which must reproduce the robofly curves in steady wind by construction.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import mujoco as mj
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from flyemu import flight  # noqa: E402
from flyemu.body import AIR_DENSITY, Body  # noqa: E402


def robofly(a_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return (0.225 + 1.58 * np.sin(np.radians(2.13 * a_deg - 7.20)),
            1.92 - 1.55 * np.cos(np.radians(2.04 * a_deg - 9.82)))


def sweep(kutta: float, U: float, alphas: np.ndarray, membrane_only: bool = True) -> dict:
    b = Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    m.opt.gravity[:] = 0.0
    target = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, "flybody/l_wing_membrane")
    for g in range(m.ngeom):
        if g != target:
            m.geom_fluid[g][0] = 0.0
    m.geom_fluid[target][0] = 1.0
    m.geom_fluid[target][4] = kutta
    free = int(m.jnt_dofadr[0])
    assert m.jnt_type[0] == mj.mjtJoint.mjJNT_FREE
    d.qvel[:] = 0.0
    mj.mj_forward(m, d)
    R = d.geom_xmat[target].reshape(3, 3)            # columns: geom axes in world
    sz = m.geom_size[target]
    order = np.argsort(sz)                           # thickness, chord, span
    n_hat, c_hat = R[:, order[0]], R[:, order[1]]
    S = np.pi * sz[order[1]] * sz[order[2]]
    q = 0.5 * AIR_DENSITY * U ** 2 * S
    CL, CD = [], []
    coef = m.geom_fluid[target][1:6].copy()
    base = []
    for a in np.radians(alphas):
        u = np.cos(a) * c_hat + np.sin(a) * n_hat    # air velocity seen by the wing
        e_lift = -np.sin(a) * c_hat + np.cos(a) * n_hat
        m.opt.wind[:] = U * u
        # MuJoCo applies its inertia-box drag to every body with no ellipsoid geom,
        # so the free joint also carries the rest of the fly; subtract that baseline
        # (same wind, this wing's coefficients zero, its body still in ellipsoid mode).
        m.geom_fluid[target][1:6] = 0.0
        mj.mj_forward(m, d)
        F0 = d.qfrc_fluid[free:free + 3].copy()
        m.geom_fluid[target][1:6] = coef
        mj.mj_forward(m, d)
        F = d.qfrc_fluid[free:free + 3] - F0
        CD.append(float(F @ u) / q)
        CL.append(float(F @ e_lift) / q)
        base.append(float(np.linalg.norm(F0)) / q)
    return dict(kutta=kutta, U_mm_s=U, area_mm2=round(float(S), 4), CL=CL, CD=CD,
                rest_of_fly_force_coef=[round(x, 3) for x in base],
                semi_axes_mm=[round(float(x), 4) for x in sz[order]])


def sweep_blade(U: float, alphas: np.ndarray) -> dict:
    b = Body(vision=False)
    m, d = b.sim.mj_model, b.sim.mj_data
    m.opt.gravity[:] = 0.0
    hook = flight.apply_blade_element(b)
    mj.mj_forward(m, d)
    g = mj.mj_name2id(m, mj.mjtObj.mjOBJ_GEOM, "flybody/l_wing_membrane")
    R, sz = d.geom_xmat[g].reshape(3, 3), m.geom_size[g]
    o = np.argsort(sz)
    n_hat, c_hat = R[:, o[0]], R[:, o[1]]
    q = 0.5 * AIR_DENSITY * U ** 2 * np.pi * sz[o[1]] * sz[o[2]]
    CL, CD = [], []
    for a in np.radians(alphas):
        u = np.cos(a) * c_hat + np.sin(a) * n_hat
        m.opt.wind[:] = U * u
        hook(d)
        F = hook.force[0]
        CD.append(float(F @ u) / q)
        CL.append(float(F @ (-np.sin(a) * c_hat + np.cos(a) * n_hat)) / q)
    return dict(kutta="blade element", U_mm_s=U, CL=CL, CD=CD, x0_hat=[round(x, 3) for x in hook.x0],
                C_rot=[round(x, 3) for x in hook.c_rot])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kutta", type=float, nargs="+", default=[1.0, 3.1])
    ap.add_argument("--U", type=float, default=1000.0, help="mm/s")
    ap.add_argument("--blade", action="store_true")
    ap.add_argument("--out", default=str(REPO / "runs" / "s12" / "flight"))
    a = ap.parse_args()
    alphas = np.arange(0, 91, 5.0)
    rl, rd = robofly(alphas)
    res = {"alpha_deg": alphas.tolist(), "robofly_CL": rl.round(3).tolist(), "robofly_CD": rd.round(3).tolist(),
           "model": [sweep(k, a.U, alphas) for k in a.kutta] + ([sweep_blade(a.U, alphas)] if a.blade else [])}
    for r in res["model"]:
        cl, cd = np.array(r["CL"]), np.array(r["CD"])
        r["max_abs_err_vs_robofly"] = round(float(max(abs(cl - rl).max(), abs(cd - rd).max())), 4)
        r["CL_peak"], r["CL_peak_alpha"] = round(float(cl.max()), 3), float(alphas[cl.argmax()])
        r["CD_at_90"], r["CL_at_45_ratio_to_robofly"] = round(float(cd[-1]), 3), round(float(cl[9] / rl[9]), 3)
        r["L_over_D_at_45"] = round(float(cl[9] / cd[9]), 3)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "wing_coefficients.json").write_text(json.dumps(res, indent=1))
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(alphas, rl, "k-", lw=2, label="robofly (Dickinson 1999)")
    ax[1].plot(alphas, rd, "k-", lw=2, label="robofly (Dickinson 1999)")
    for r in res["model"]:
        ax[0].plot(alphas, r["CL"], "o-", ms=3, label=f"model, {r['kutta']}" if isinstance(r["kutta"], str) else f"model, Kutta {r['kutta']}")
        ax[1].plot(alphas, r["CD"], "o-", ms=3, label=f"model, {r['kutta']}" if isinstance(r["kutta"], str) else f"model, Kutta {r['kutta']}")
    for x, t in zip(ax, ("lift coefficient", "drag coefficient")):
        x.set_xlabel("angle of attack (deg)")
        x.set_title(t)
        x.grid(alpha=0.3)
        x.legend(fontsize=8)
    fig.suptitle(f"translational coefficients, left wing membrane, U = {a.U:.0f} mm/s")
    fig.tight_layout()
    fig.savefig(out / "wing_coefficients.png", dpi=110)
    print(json.dumps({k: v for k, v in res.items() if k != "model"} | {"model": [
        {k: v for k, v in r.items() if k not in ("CL", "CD")} for r in res["model"]]}, indent=1))


if __name__ == "__main__":
    main()
