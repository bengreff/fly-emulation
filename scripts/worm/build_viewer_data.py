"""Viewer data for the ported MetaWorm body: mesh + muscle map (committed) and run frames (gitignored).

Writes
  viewer/worm/data/body_mesh.json   surface triangles, rest pose, per-vertex arclength and nearest muscle segment,
                                    the 96 MetaWorm segments with their Cook 2019 muscle names (committed, small)
  viewer/worm/runs/<id>.frames.f32  [n_frames, n_vertices, 3] float32, in body lengths (runs/ is gitignored)
  viewer/worm/runs/<id>.act.f32     [n_frames, 96] float32 muscle activations as fed to the body
  viewer/worm/runs/index.json       run list with titles, drive settings and test readouts
Usage: build_viewer_data.py [run ...]   (default: the MetaWorm test runs in runs/worm/metaworm/)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from wormemu.body import metaworm as mw  # noqa: E402
from wormemu.body.scene import ChemotaxisScene  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "runs" / "worm" / "metaworm"
VIEW = REPO / "viewer" / "worm"
TESTS = REPO / "data" / "worm" / "body_runs" / "metaworm_tests.json"

# MetaWorm string -> Cook 2019 quadrant prefix. Segment j (0 = head) of a string = Cook muscle j + 1 of that
# quadrant (both run head first, 24 per quadrant). vBWML24 does not exist: MetaWorm's MVL segment 23 has no Cook
# muscle; on the interface it copies vBWML23 (an interface choice, docs/worm/INTERFACE.md body side).
COOK = {"MDR": "dBWMR", "MVR": "vBWMR", "MDL": "dBWML", "MVL": "vBWML"}

RUNS = {
    "p2": ("Published key t0_fast", "MetaWorm's own periodic muscle key (symmetric, 1.5 Hz), as published"),
    "p2b": ("Published key turn2", "MetaWorm's default key (dorsal 0.72 / ventral 0.42, 1.5 Hz): curving gait"),
    "p3_final": ("Prescribed wave (swim means)", "sine wave f 1.76 Hz, wavelength 1.54 L (Fang-Yen 2010); "
                 "amplitude fitted to head kappa*L 4.5"),
    "p1_release": ("Release at 3 s", "key t0_fast for 3 s, then all muscles off"),
    "p0_dead": ("Dead worm", "all muscles off for 10 s"),
}


def seg_dist(P: np.ndarray, A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Distance from points P [n, 3] to segments A-B [m, 3] -> [n, m]."""
    AB = B - A
    t = np.clip(((P[:, None] - A[None]) * AB[None]).sum(2) / (AB * AB).sum(1)[None], 0, 1)
    Q = A[None] + t[..., None] * AB[None]
    return np.linalg.norm(P[:, None] - Q, axis=2)


def build_mesh(meta: dict, X0: np.ndarray) -> dict:
    fr = mw.Frame(meta, X0)
    L = fr.length
    A = np.array(meta["segment_starts"])
    B = np.array(meta["segment_ends"])
    d = seg_dist(X0, A, B)
    near = d.argmin(1)
    dmin = d.min(1)
    tri = np.array(meta["triangles"])
    surf = np.unique(tri)
    # display weight: 1 at the fibre's typical surface distance, fading over 0.01 L beyond it (display choice)
    d0 = np.percentile(dmin[surf], 25)
    w = np.clip(1 - (dmin - d0) / (0.01 * L), 0, 1)
    segs = []
    for m, name in enumerate(meta["muscles"]):
        for j in range(mw.N_SEG):
            k = m * mw.N_SEG + j
            mid = 0.5 * (A[k] + B[k])
            cook = f"{COOK[name]}{j + 1}" if not (name == "MVL" and j == 23) else None
            segs.append({"i": k, "string": name, "seg": j, "cook": cook,
                         "s_mid": float(((mid - X0.mean(0)) @ fr.ax0 - ((X0 - X0.mean(0)) @ fr.ax0).min()) / L)})
    c0 = X0.mean(0)
    return {
        "source": "MetaWorm (BAAIWorm b99ca5ab, Apache 2.0): worm_mesh_4.mesh x 0.004, worm_nerve_cord_highResCord.obj",
        "units": "body lengths (rest length 0.628 sim units = 1 L)",
        "n_vertices": int(len(X0)),
        "triangles": tri.ravel().tolist(),
        "rest": np.round((X0 - c0) / L, 5).ravel().tolist(),
        "s": np.round(fr.s, 4).tolist(),
        "muscle": near.tolist(),
        "muscle_weight": np.round(w, 3).tolist(),
        "axis": fr.ax0.tolist(), "dorsal": fr.dv0.tolist(),
        "segments": segs,
        "notes": "muscle = nearest of the 96 MetaWorm fibre segments (strings MDR, MVR, MDL, MVL x 24, head first); "
                 "weight is a display fade, not a physics quantity. Cook names: segment j = muscle j+1 of the "
                 "quadrant; MVL segment 23 has no Cook muscle (vBWML24 does not exist).",
    }


def summary(tests: dict, rid: str) -> dict:
    key = {"p0_dead": "P0", "p1_release": "P1", "p2": "P2", "p2b": "P2b", "p3_final": "P3"}.get(rid)
    r = tests.get(key, {})
    out = {}
    for k in ("pass", "pass_disp", "pass_freq", "pass_speed", "pass_wavelength", "a0", "max_disp_from_rest",
              "end_over_peak"):
        if k in r:
            out[k] = r[k]
    for k in ("speed_L_s", "wavelength_L", "f_body_hz", "head_amp_kL"):
        if k in r.get("gait", {}):
            out[k] = r["gait"][k]
    if "zigzag" in r:
        out["net_disp_L"] = r["zigzag"]["net_disp_L"]
        out["heading_change_deg"] = r["zigzag"]["heading_change_deg"]
    return out


def add_runs(ids: list[str], titles: dict | None = None) -> list[dict]:
    """Convert runs/worm/metaworm/<id> to viewer files and merge them into viewer/worm/runs/index.json."""
    (VIEW / "data").mkdir(parents=True, exist_ok=True)
    (VIEW / "runs").mkdir(parents=True, exist_ok=True)
    tests = json.load(open(TESTS)) if TESTS.exists() else {}
    idx_path = VIEW / "runs" / "index.json"
    index = json.load(open(idx_path))["runs"] if idx_path.exists() else []
    titles = {**RUNS, **(titles or {})}
    added = []
    for rid in ids:
        rec = mw.load(SRC / rid)
        meta, X = rec["meta"], rec["X"]
        fr = mw.Frame(meta, X[0])
        if not (VIEW / "data" / "body_mesh.json").exists() or rid == ids[0]:
            json.dump(build_mesh(meta, X[0]), open(VIEW / "data" / "body_mesh.json", "w"))
        ((X - X[0].mean(0)) / fr.length).astype(np.float32).tofile(VIEW / "runs" / f"{rid}.frames.f32")
        rec["A"].astype(np.float32).tofile(VIEW / "runs" / f"{rid}.act.f32")
        title, desc = titles.get(rid, (rid, ""))
        entry = {"id": rid, "title": title, "description": desc, "mode": meta["mode"], "key": meta.get("key"),
                 "f": meta.get("f"), "lam": meta.get("lam"), "amp": meta.get("amp"),
                 "n_frames": meta["n_frames"], "frame_dt": meta["frame_dt"], "seconds": meta["seconds"],
                 "tests": summary(tests, rid), "label": "simulated (ported MetaWorm body, published parameters)"}
        c0 = X[0].mean(0)  # viewer coordinates: (x - c0) / L, as the frames below
        if meta.get("scale", "published") != "published":  # worm-scale world (BODY_TESTS.md, agar plate / film)
            entry["world"] = {k: meta[k] for k in ("scale", "fluid", "substrate", "side_down")}
            entry["label"] = (f"simulated (ported MetaWorm body, published parameters; world {meta['scale']}, "
                              f"{meta['fluid']}, {meta['substrate']})")
            w = meta["world"]
            if meta["substrate"] != "none_published":  # the plate is normal to y (driver plate_axis 1)
                entry["world"]["plate_y_L"] = float((w["plate_y"] - c0[1]) / fr.length)
            if meta["substrate"] == "agar_film":
                entry["world"]["film_y_L"] = float((w["film_y"] - c0[1]) / fr.length)
        sc = meta.get("scene") or {}
        if sc.get("field", "none") != "none":  # closed loop with a chemical field (scene.py, MB11)
            scene = ChemotaxisScene(field=sc["field"], target=sc["target"], channel=sc["channel"], params=sc["params"])
            entry["chem"] = {"field": sc["field"], "channel": sc["channel"], "params": scene.params,
                             "target_L": ((scene.target_point(X[0]) - c0) / fr.length).tolist()}
        neural = SRC / f"{rid}.neural.f32"
        if neural.exists() and meta.get("cells"):  # closed loop: the brain's soma voltages at the body's frames
            V = np.fromfile(neural, np.float32).reshape(-1, len(meta["cells"]))[:meta["n_frames"]]
            V.tofile(VIEW / "runs" / f"{rid}.neural.f32")
            entry.update(cells=meta["cells"], brain=meta.get("brain"),
                         label="simulated (closed loop: brain.py and the ported MetaWorm body, every number labelled "
                               "in the ledgers)")
        index = [e for e in index if e["id"] != rid] + [entry]
        added.append(entry)
        print(rid, meta["n_frames"], "frames")
    json.dump({"runs": index}, open(idx_path, "w"), indent=1)
    return added


if __name__ == "__main__":
    add_runs(sys.argv[1:] or list(RUNS))
