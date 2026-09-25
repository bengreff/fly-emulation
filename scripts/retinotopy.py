"""Derive which ommatidium each photoreceptor looks through (F-VISION-2).

Terminal position encodes viewing direction. R7/R8 end in medulla columns
(one ommatidium each) and R1-R6 end in lamina cartridges (one viewing
direction each, neural superposition). So:

1. Terminal centroids: mean presynapse location per photoreceptor
   (neuPrint, data/cache/photoreceptor_terminals.parquet). **Derived.**
2. Volume axes: anterior = -z, dorsal = -y (AL vs calyx landmarks; dorsal
   rim terminals as a check). **Derived.**
3. Each eye's terminal sheet in (anterior, dorsal) volume coordinates. The
   medulla's anterior axis is flipped: the first optic chiasm reverses A-P
   between lamina and medulla. **Inferred (standard anatomy).**
4. Ommatidium viewing directions from the body model's retina map and eye
   camera poses, as (azimuth, elevation) in the head frame. **Derived.**
5. Global alignment: match each sheet's mean and standard deviations to the
   ommatidia cloud along the anterior and dorsal axes, then assign each cell
   to the nearest ommatidium. **Inferred** (a smooth, axis-aligned map is
   assumed; there is no local distortion model).

Checks, not used for fitting: R7/R8 pale/yellow subtype concordance within
an assigned ommatidium; whether dorsal-rim cells land at the dorsal edge.

    uv run python scripts/retinotopy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

REPO = Path(__file__).resolve().parents[1]
MED = ["R7p", "R7y", "R8p", "R8y", "R7d", "R8d", "R7_unclear", "R8_unclear", "R7R8_unclear"]


def ommatidia_directions():
    """(eye, idx, azimuth deg, elevation deg, pale) per ommatidium, head frame."""
    import mujoco as mj
    from flygym.vision.retina import Retina
    from flyemu.body import Body

    ret = Retina()
    idmap = ret.ommatidia_id_map            # (rows, cols), 1-based ids, 0 = none
    rows, cols = idmap.shape
    ids = np.arange(1, idmap.max() + 1)
    rr, cc = np.nonzero(idmap)
    lab = idmap[rr, cc]
    r_mean = np.bincount(lab, rr, minlength=ids.max() + 1)[1:] / np.bincount(lab, minlength=ids.max() + 1)[1:]
    c_mean = np.bincount(lab, cc, minlength=ids.max() + 1)[1:] / np.bincount(lab, minlength=ids.max() + 1)[1:]

    body = Body(vision=True)
    m, d = body.sim.mj_model, body.sim.mj_data
    mj.mj_forward(m, d)
    head = [i for i in range(m.nbody) if m.body(i).name.endswith("c_head")][0]
    thor = [i for i in range(m.nbody) if m.body(i).name.endswith("c_thorax")][0]
    fwd = d.xpos[head] - d.xpos[thor]; fwd[2] = 0; fwd /= np.linalg.norm(fwd)
    up = np.array([0.0, 0.0, 1.0])
    left = np.cross(up, fwd)
    out = []
    for e, name in ((0, "l_eye_cam_camera"), (1, "r_eye_cam_camera")):
        cam = [i for i in range(m.ncam) if m.cam(i).name.endswith(name)][0]
        R = d.cam_xmat[cam].reshape(3, 3)       # columns = camera x, y, z in world
        fovy = np.deg2rad(m.cam_fovy[cam])
        f = (rows / 2) / np.tan(fovy / 2)
        x = (c_mean - cols / 2) / f
        y = -(r_mean - rows / 2) / f
        ray = np.stack([x, y, -np.ones_like(x)], 1) @ R.T
        ray /= np.linalg.norm(ray, axis=1, keepdims=True)
        az = np.degrees(np.arctan2(ray @ left, ray @ fwd))    # + = left of midline
        el = np.degrees(np.arcsin(ray @ up))
        for i in range(len(ids)):
            out.append(dict(eye="L" if e == 0 else "R", ommatidium=int(i), az=az[i], el=el[i],
                            pale=int(ret.pale_type_mask[i])))
    return pd.DataFrame(out)


def main() -> None:
    om = ommatidia_directions()
    t = pd.read_parquet(REPO / "data" / "cache" / "photoreceptor_terminals.parquet").dropna(subset=["x"])
    t["layer"] = np.where(t.type.isin(MED), "medulla", "lamina")
    t = t[t.type != "HBeyelet"]
    # eye by terminal side of midline; which volume side is the fly's left is
    # checked against the ommatidia azimuth sign below
    mid = t.x.median()
    t["vol_side"] = np.where(t.x > 48000, "hiX", "loX")
    t["ant"] = -t.z
    t["dor"] = -t.y

    dra = t.type.isin(["R7d", "R8d"])
    check_dorsal = {s: float(t[(t.vol_side == s) & dra & (t.layer == "medulla")].dor.mean()
                             - t[(t.vol_side == s) & ~dra & (t.layer == "medulla")].dor.mean())
                    for s in ("hiX", "loX")}
    print("dorsal-rim terminals above other medulla terminals (positive = dorsal):",
          {k: round(v) for k, v in check_dorsal.items()})

    # Which volume side is the fly's LEFT eye? Derived from annotated soma
    # sides: somaSide L cells sit on one x side of the volume.
    ex = pd.read_parquet(REPO / "data" / "cache" / "male_cns_extra2.parquet")
    nn = pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet")[["bodyId", "somaSide"]].merge(ex, on="bodyId")
    nn = nn[nn.somaLocation.notna()]
    sx = nn.somaLocation.map(lambda v: v[0])
    xl, xr = sx[nn.somaSide == "L"].median(), sx[nn.somaSide == "R"].median()
    print(f"median soma x: somaSide L {xl:.0f}, R {xr:.0f} -> fly's left is at {'larger' if xl > xr else 'smaller'} x")
    side_eye = {"hiX": "L", "loX": "R"} if xl > xr else {"hiX": "R", "loX": "L"}
    from scipy.optimize import linear_sum_assignment
    ant_v = np.array([0.0, 0.0, -1.0]); dor_v = np.array([0.0, -1.0, 0.0])
    rows = []
    for vs, eye in side_eye.items():
        o = om[om.eye == eye].reset_index(drop=True)
        O = np.c_[o.az, o.el]
        for layer, g in t[t.vol_side == vs].groupby("layer"):
            X = g[["x", "y", "z"]].to_numpy(float)
            c = X - X.mean(0)
            _, _, vt = np.linalg.svd(c, full_matrices=False)
            n_hat = vt[2]                                  # sheet normal
            # anatomical axes projected into the sheet plane (removes the
            # R7-vs-R8 depth offset along the normal)
            ea = ant_v - (ant_v @ n_hat) * n_hat; ea /= np.linalg.norm(ea)
            ed = dor_v - (dor_v @ n_hat) * n_hat - ((dor_v @ ea) * ea); ed /= np.linalg.norm(ed)
            a, dv = c @ ea, c @ ed
            if layer == "medulla":
                a = -a                                     # first optic chiasm reverses A-P
            side = 1.0 if eye == "L" else -1.0
            za = (a - a.mean()) / a.std(); zd = (dv - dv.mean()) / dv.std()
            az_p = o.az.mean() - side * za * o.az.std()     # anterior -> frontal
            el_p = o.el.mean() + zd * o.el.std()
            P = np.c_[az_p, el_p]
            assign = np.full(len(g), -1)
            if layer == "medulla":
                # one R7 and one R8 per ommatidium (measured biology): optimal
                # one-to-one assignment per photoreceptor class
                for cls in ("R7", "R8"):
                    sel = np.flatnonzero(g.type.str.startswith(cls).to_numpy() & ~g.type.eq("R7R8_unclear").to_numpy())
                    D = np.linalg.norm(P[sel, None, :] - O[None, :, :], axis=2)
                    ri, ci = linear_sum_assignment(D)
                    assign[sel[ri]] = ci
                rest = np.flatnonzero(assign < 0)
                if len(rest):
                    assign[rest] = cKDTree(O).query(P[rest])[1]
            else:
                assign = cKDTree(O).query(P)[1]
            dist = np.linalg.norm(P - O[assign], axis=1)
            for (bid, typ), kk, dd, ap, ep in zip(g[["bodyId", "type"]].itertuples(index=False),
                                                 assign, dist, az_p, el_p):
                rows.append(dict(bodyId=int(bid), type=typ, eye=eye, layer=layer,
                                 ommatidium=int(o.ommatidium.iloc[kk]), az_pred=ap,
                                 el_pred=ep, match_deg=dd))
    r = pd.DataFrame(rows)
    r["basis"] = "derived topology (terminal positions); inferred global alignment"
    out = REPO / "data" / "derived" / "retinotopy.csv"
    r.to_csv(out, index=False)

    # --- checks ---------------------------------------------------------------
    m = r[r.layer == "medulla"].copy()
    m["sub"] = m.type.str[-1]
    ok = m[m["sub"].isin(["p", "y"])]
    conc = []
    for (eye, om_i), g in ok.groupby(["eye", "ommatidium"]):
        r7 = g[g.type.str.startswith("R7")]["sub"]; r8 = g[g.type.str.startswith("R8")]["sub"]
        for a in r7:
            for b in r8:
                conc.append(a == b)
    rng = np.random.default_rng(0)
    s = ok["sub"].to_numpy()
    chance = np.mean([(rng.permutation(s)[:500] == rng.permutation(s)[:500]).mean() for _ in range(200)])
    dra_el = r[r.type.isin(["R7d", "R8d"])].el_pred.mean(); all_el = r[r.layer == "medulla"].el_pred.mean()
    print(f"{len(r):,} photoreceptors assigned -> {out.relative_to(REPO)}")
    print(r.groupby(["eye", "layer"]).agg(cells=("bodyId", "size"),
          ommatidia_used=("ommatidium", "nunique"), median_match_deg=("match_deg", "median")).to_string())
    print(f"R7/R8 subtype concordance within assigned ommatidium: {np.mean(conc):.2f} "
          f"(n={len(conc)} pairs; chance {chance:.2f})")
    print(f"dorsal-rim cells mean predicted elevation {dra_el:.1f} deg vs all medulla {all_el:.1f}")


if __name__ == "__main__":
    main()
