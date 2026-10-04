"""Build the derived mid- and hind-leg muscle tables (session 12 B; switch
muscle:leg|midhind_source = 1). Until now every mid/hind muscle was a copy of the
front leg's (guessed); FlyMimic fitted only the front leg.

Each front-leg FlyMimic muscle is scaled to the mid and hind legs by the measured
size of the segment that houses it (scripts/probes/leg_segment_geometry.py on the
flybody mesh; data/derived/leg_segment_geometry_flybody.csv):

  housing           members                                   F0 x      r x, L0 x
  coxa              trochanter flexors a/b, accessory flexor,  A_coxa    w_coxa,dist
                    trochanter extensor
  femur             tibia flexor, tibia extensor               A_femur   w_femur,dist
  thorax -> coxa    the 7 coxa muscles (ThC)                   w_cp^2    w_cp
  thorax -> troch.  sterno-tergo-trochanter extensors a/b      w_cp^2    w_coxa,dist

A = mid-third cross-section of the housing segment, w_dist = width at the distal
joint the tendons work on, w_cp = coxa proximal width (the opening thoracic leg
muscles insert across); each a ratio of the mid or hind leg to the front leg on the
same mesh (left/right mean). Assumptions (inferred, not measured):
  1. force ~ physiological cross-section ~ housing cross-section (same fill
     fraction, pennation and specific tension as the front leg);
  2. moment arm ~ width of the joint the muscle crosses;
  3. optimal fibre length ~ moment arm, so each muscle keeps the front leg's strain
     per radian and works over the same part of its force-length curve;
  4. thoracic leg muscles scale with the square of the coxal opening, the only
     thoracic dimension measured here per segment.
Alternatives kept as sensitivity bounds in the scale table: copy (all factors 1),
and force ~ volume / fibre length (A x segment length / w_dist).

The jump muscle (TTM, mid leg) is not in these tables: it is B15 (jump.py).
Tibia-tarsus muscles stay placeholders (no FlyMimic muscle to scale).

    uv run python scripts/build_midhind_muscles.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from build_leg_muscles import DEFAULT_SHAPE, MAP, flymimic_arms  # noqa: E402

GEOM = REPO / "data" / "derived" / "leg_segment_geometry_flybody.csv"
PARAMS = REPO / "data" / "params"
OUT_PAIRS = PARAMS / "leg_muscles_midhind.csv"
OUT_COXA = PARAMS / "coxa_muscles_midhind.csv"
OUT_SCALE = PARAMS / "leg_muscle_midhind_scale.csv"

THORACIC_TROCH = ("LFF_sterno-tergo-trochanter_extensor_a", "LFF_sterno-tergo-trochanter_extensor_b")


def housing(muscle: str) -> str:
    if muscle.startswith("LFC_"):
        return "thorax_coxa"
    if muscle in THORACIC_TROCH:
        return "thorax_trochanter"
    if muscle.startswith("LFF_"):
        return "coxa"
    if muscle.startswith("LFTibia_"):
        return "femur"
    raise ValueError(muscle)


def ratios() -> dict[str, dict[str, float]]:
    """Per leg position (m, h): measured segment ratios to the front leg."""
    g = pd.read_csv(GEOM, comment="#")
    g["pos"] = g.leg.str[1]
    g = g.groupby(["pos", "segment"])[["length_mm", "area_mid_mm2", "width_dist_mm", "width_prox_mm"]].mean()
    out = {}
    for p in "mh":
        r = g.xs(p) / g.xs("f")
        out[p] = dict(A_coxa=r.area_mid_mm2["coxa"], w_coxa=r.width_dist_mm["coxa"],
                      L_coxa=r.length_mm["coxa"], w_cp=r.width_prox_mm["coxa"],
                      A_femur=r.area_mid_mm2["trochanterfemur"], w_femur=r.width_dist_mm["trochanterfemur"],
                      L_femur=r.length_mm["trochanterfemur"])
    return out


def factors(h: str, q: dict[str, float]) -> tuple[float, float, float, str]:
    """(F0 factor, r = L0 factor, volume-rule F0 factor, basis text)."""
    if h == "coxa":
        return q["A_coxa"], q["w_coxa"], q["A_coxa"] * q["L_coxa"] / q["w_coxa"], \
            "F0 x coxa mid cross-section, r and L0 x coxa distal width"
    if h == "femur":
        return q["A_femur"], q["w_femur"], q["A_femur"] * q["L_femur"] / q["w_femur"], \
            "F0 x femur mid cross-section, r and L0 x femur distal width"
    if h == "thorax_coxa":
        return q["w_cp"] ** 2, q["w_cp"], q["w_cp"] ** 2, \
            "F0 x (coxa proximal width)^2, r and L0 x coxa proximal width"
    return q["w_cp"] ** 2, q["w_coxa"], q["w_cp"] ** 2, \
        "F0 x (coxa proximal width)^2, r and L0 x coxa distal width (inserts on the trochanter)"


def main() -> None:
    q = ratios()
    arms = flymimic_arms()
    scale = []
    for p in "mh":
        for mu in sorted(arms.muscle.unique()):
            h = housing(mu)
            fF, fr, fv, basis = factors(h, q[p])
            scale.append(dict(position=p, muscle=mu, housing=h, F0_factor=round(fF, 4), r_factor=round(fr, 4),
                              L0_factor=round(fr, 4), F0_factor_volume_rule=round(fv, 4), label="inferred",
                              basis=basis))
    sc = pd.DataFrame(scale)
    fac = {(r.position, r.muscle): (r.F0_factor, r.r_factor) for r in sc.itertuples()}

    rows = []
    for side in "lr":
        for p in "mh":
            L = f"{side}{p}"
            for key, (tmpl, sgn, basis) in MAP.items():
                a = arms[arms.fm_joint == key]
                for fm_dir in (+1, -1):
                    g = a[np.sign(a.arm_mm) == fm_dir]
                    fF = np.array([fac[(p, m)][0] for m in g.muscle])
                    fr = np.array([fac[(p, m)][1] for m in g.muscle])
                    F = g.F0_uN.to_numpy() * fF
                    F0 = F.sum()
                    rows.append(dict(joint=tmpl.format(L=L), direction=fm_dir * sgn, F0_uN=round(F0, 3),
                                     r_mm=round((F * g.arm_mm.abs().to_numpy() * fr).sum() / F0, 5),
                                     L0_mm=round((F * g.L0_mm.to_numpy() * fr).sum() / F0, 4), **DEFAULT_SHAPE,
                                     label="inferred", direction_basis=basis,
                                     source="FlyMimic front-leg members scaled by measured segment size "
                                            "(inferred; leg_muscle_midhind_scale.csv)",
                                     flymimic_members=";".join(g.muscle)))
            for direction in (+1, -1):
                rows.append(dict(joint=f"{L}_tibia-{L}_tarsus1-pitch", direction=direction, F0_uN=20.0,
                                 r_mm=0.01, L0_mm=0.1, **DEFAULT_SHAPE, label="guessed",
                                 direction_basis="guessed", source="no FlyMimic tarsal muscle; placeholder",
                                 flymimic_members=""))
    pairs = pd.DataFrame(rows)

    cx = pd.read_csv(PARAMS / "coxa_muscles.csv", comment="#")
    mid = cx[cx.leg.str[1].isin(["m", "h"])].copy()
    fm = {m.removeprefix("LFC_"): m for m in arms.muscle if m.startswith("LFC_")}
    fF = np.array([fac[(lg[1], fm[m])][0] for lg, m in zip(mid.leg, mid.muscle)])
    fr = np.array([fac[(lg[1], fm[m])][1] for lg, m in zip(mid.leg, mid.muscle)])
    mid["F0_uN"] = (mid.F0_uN * fF).round(4)
    mid["r_mm"] = (mid.r_mm * fr).round(6)
    mid["r_keyframe_mm"] = (mid.r_keyframe_mm * fr).round(6)
    mid["L0_mm"] = (mid.L0_mm * fr).round(5)
    mid["label"] = "inferred"
    mid["method"] = ("lf in the thorax frame, F0 x (coxa proximal width)^2, arms and L0 x coxa proximal width "
                     "(inferred; leg_muscle_midhind_scale.csv)")

    head = ("# Session 12: mid/hind leg muscles derived from FlyMimic's front leg by measured segment size "
            "(scripts/build_midhind_muscles.py; switch muscle:leg|midhind_source = 1). Label inferred: the "
            "geometry is measured on the flybody mesh, the scaling rules are assumptions stated in the script.\n")
    for df, path in ((pairs, OUT_PAIRS), (mid, OUT_COXA), (sc, OUT_SCALE)):
        with open(path, "w") as f:
            f.write(head)
            df.to_csv(f, index=False)
    print(sc.to_string(index=False))
    old = pd.read_csv(PARAMS / "leg_muscles.csv", comment="#").set_index(["joint", "direction"])
    cmp = pairs.set_index(["joint", "direction"])
    cmp = cmp[cmp.index.get_level_values(0).str.contains("^l[mh]_|-l[mh]_", regex=True)]
    cmp["F0_copy"] = old.F0_uN.reindex(cmp.index)
    cmp["torque_cap_ratio"] = (cmp.F0_uN * cmp.r_mm / (old.F0_uN * old.r_mm).reindex(cmp.index)).round(3)
    print(cmp[["F0_uN", "F0_copy", "r_mm", "L0_mm", "torque_cap_ratio"]].to_string())
    print(len(pairs), "pair rows ->", OUT_PAIRS, ";", len(mid), "coxa rows ->", OUT_COXA)


if __name__ == "__main__":
    main()
