"""Agar plate and agar film gates, numerics and report-only crawl readouts (pre-registered in
docs/worm/BODY_TESTS.md, 17:20 and 17:30 CST, 5 Nov). Run from the repo root:
    .venv/bin/python scripts/worm/agar_tests.py A1|A2|A2n|A2l|A1f|A2f|crawl|crawlf
Writes runs/worm/metaworm/agar_*. Crawl readouts: from t = 3 s, which gait() trims to the last 2 periods."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import numpy as np
from wormemu.body import metaworm as mw

OUT = "runs/worm/metaworm/"
which = sys.argv[1]


def geom(r):
    m, X = r["meta"], r["X"]
    w = m["world"]
    L = w["rest_length_units"]
    down, yp = w["plate_down"], w["plate_y"]
    h = -down * (X[:, :, 1] - yp)  # height above the plate, per vertex
    c = X.mean(1)
    fr = mw.Frame(m, X[0])
    mid = fr.midline(X)
    mlen = np.linalg.norm(np.diff(mid, axis=1), axis=2).sum(1)
    return dict(L=L, finite=bool(np.isfinite(X).all()), low=h.min(1) / L, ch=-down * (c[:, 1] - yp) / L,
                drift=np.linalg.norm((c - c[0])[:, [0, 2]], axis=1) / L,
                disp=np.abs(X - X[0]).max((1, 2)) / L,
                spread=np.linalg.norm(X - c[:, None, :], axis=2).max(1) / L, mlen=mlen / mlen[0])


def readouts(r, f, t_from):
    g = mw.gait(r, f, t_from)
    return {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in g.items()}


def report(name, r, extra=None):
    m = r["meta"]
    print(name, "wall", round(m["wall_s"], 2), "s for", m["seconds"], "s, RTF", round(m["seconds"] / m["wall_s"], 3),
          "drag update mean", round(m["world"]["drag_update_s_mean"] * 1000, 2), "ms", flush=True)
    if extra:
        print("  ", extra, flush=True)


if which == "A1":
    r = mw.run(OUT + "agar_a1_dead", mode="dead", seconds=3.0, world=dict(mw.AGAR_PLATE))
    g = geom(r)
    res = {"finite": g["finite"], "lowest_point_max_L": float(np.abs(g["low"]).max()),
           "lowest_point_min_L": float(g["low"].min()), "drift_max_L": float(g["drift"].max()),
           "disp_max_L": float(g["disp"].max())}
    res["pass"] = bool(res["finite"] and res["lowest_point_max_L"] <= 1e-3 and res["drift_max_L"] < 0.01
                       and res["disp_max_L"] < 0.02)
    report("A1", r, res)
elif which in ("A2", "A2n", "A2l"):
    world = dict(mw.AGAR_PLATE)
    kw = {}
    name = "agar_a2_p3"
    if which == "A2n":
        world["drag_every"] = 8
        name += "_de8"
    if which == "A2l":
        kw["solver_exit"] = "latest"
        name += "_latest"
    r = mw.run(OUT + name, mode="wave", seconds=5.0, f=1.76, lam=1.54, amp=0.157, world=world, **kw)
    g = geom(r)
    res = {"finite": g["finite"], "spread_max_L": float(g["spread"].max()),
           "midline_len_range": [float(g["mlen"].min()), float(g["mlen"].max())],
           "centroid_height_max_L": float(g["ch"].max()), "disp_max_L": float(g["disp"].max())}
    res["pass"] = bool(res["finite"] and res["spread_max_L"] <= 0.6 and 0.8 <= g["mlen"].min()
                       and g["mlen"].max() <= 1.2 and res["centroid_height_max_L"] <= 0.08)
    report(which, r, res)
    print("   readouts (report only):", readouts(r, 1.76, 1.0), flush=True)
elif which == "A1f":
    r = mw.run(OUT + "agar_a1f_dead", mode="dead", seconds=3.0, world=dict(mw.AGAR_FILM))
    g = geom(r)
    res = {"finite": g["finite"], "lowest_point_max_L": float(np.abs(g["low"]).max()),
           "drift_max_L": float(g["drift"].max()), "disp_max_L": float(g["disp"].max())}
    res["pass"] = bool(res["finite"] and res["lowest_point_max_L"] <= 1e-3 and res["drift_max_L"] < 0.01
                       and res["disp_max_L"] < 0.02)
    a = np.fromfile(OUT + "agar_a1_dead.frames.f32", np.float32)
    b = np.fromfile(OUT + "agar_a1f_dead.frames.f32", np.float32)
    res["bit_identical_to_A1"] = bool(a.shape == b.shape and (a == b).all())
    report("A1f", r, res)
elif which == "A2f":
    r = mw.run(OUT + "agar_a2f_p3", mode="wave", seconds=5.0, f=1.76, lam=1.54, amp=0.157, world=dict(mw.AGAR_FILM))
    g = geom(r)
    w = r["meta"]["world"]
    top = -w["plate_down"] * (w["film_y"] - w["plate_y"]) / g["L"]  # film surface height, L
    h = -w["plate_down"] * (r["X"][:, :, 1] - w["plate_y"]) / g["L"]  # vertex heights above the plate, L
    hmax = float(h.max())
    res = {"finite": g["finite"], "spread_max_L": float(g["spread"].max()),
           "midline_len_range": [float(g["mlen"].min()), float(g["mlen"].max())],
           "centroid_height_max_L": float(g["ch"].max()), "film_L": float(top), "highest_vertex_L": hmax,
           "disp_max_L": float(g["disp"].max())}
    res["pass"] = bool(res["finite"] and res["spread_max_L"] <= 0.6 and 0.8 <= g["mlen"].min()
                       and g["mlen"].max() <= 1.2 and res["centroid_height_max_L"] <= 0.08 and hmax <= top + 1e-6)
    res["share_on_film"] = float((h > top - 1e-5).mean())
    res["share_on_plate"] = float((h < 1e-5).mean())
    report("A2f", r, res)
    print("   readouts (report only):", readouts(r, 1.76, 1.0), flush=True)
elif which in ("crawl", "crawlf"):
    world = mw.AGAR_PLATE if which == "crawl" else mw.AGAR_FILM
    for amp in (0.157, 1.0):
        r = mw.run(OUT + f"agar_{which}_a{amp}", mode="wave", seconds=10.0, f=0.30, lam=0.65, amp=amp,
                   world=dict(world))
        g = geom(r)
        report(f"{which} a0 {amp}", r, {"finite": g["finite"], "spread_max_L": round(float(g["spread"].max()), 3),
                                        "midline_len_range": [round(float(g["mlen"].min()), 3), round(float(g["mlen"].max()), 3)],
                                        "centroid_height_max_L": round(float(g["ch"].max()), 4)})
        print("   readouts (report only):", readouts(r, 0.30, 3.0), flush=True)
