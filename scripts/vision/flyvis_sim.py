"""A numpy re-implementation of the flyvis network (Lappalainen et al. 2024), for reading out the
published ensemble's per-type properties without torch.

Builds the hexagonal lattice (extent 15, 721 columns), the convolutional edges of the
fib25-fib19_v2.2 connectome spec (offsets with the convex-hull fill of 1 synapse), and each model's
fitted parameters from scripts/fetch/flyvis_checkpoint.py:

    tau_t dV/dt = -V + b_t + sum_e sign_e * n_syn_e * alpha_(s,t) * relu(V_s) + x,   tau floored at dt

x is the luminance (0..1) on R1-R8. Grey is 0.5, as flyvis's steady_state().

Used by scripts/vision/flyvis_rows.py. Checks (run this file): the parameter groups line up with
the checkpoint (synapse counts equal the spec's), and T4/T5 subtypes come out direction selective
with opposite preferences within a/b and c/d, as the paper reports for the ensemble.

    uv run python scripts/vision/flyvis_sim.py --models 0,1,2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.path as mp
import numpy as np
import scipy.sparse as sparse
import scipy.spatial as ss

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
from flyvis_checkpoint import load  # noqa: E402
from flyvis_types import EXTENT, RAW, spec  # noqa: E402


def _fill_hull(offsets, n_fill=1.0):
    """flyvis connectome.fill_hull: add unreported offsets inside the hull, n_syn = n_fill."""
    known = np.array([o[0] for o in offsets])
    known_set = set(map(tuple, known))
    hull = ss.ConvexHull((1 + 1e-6) * known, False, "QJ")
    verts = known[hull.vertices]
    grid = np.concatenate(np.dstack(np.mgrid[known[:, 0].min():known[:, 0].max() + 1,
                                             known[:, 1].min():known[:, 1].max() + 1]))
    inside = grid[mp.Path(verts).contains_points(grid)]
    return offsets + [[[int(u), int(v)], n_fill] for u, v in inside if (u, v) not in known_set]


class FlyvisNet:
    def __init__(self, extent: int = EXTENT):
        s = spec()
        self.types = [n["name"] for n in s["nodes"]]
        node_t, node_u, node_v, index = [], [], [], {}
        for ti, n in enumerate(s["nodes"]):
            pat, args = n["pattern"]
            us, vs = (args, args) if pat == "tile" else ((1, 1) if pat == "single" else args)
            ext = 0 if pat == "single" else extent
            for u in range(-ext, ext + 1):
                for v in range(max(-ext, -ext - u), min(ext, ext - u) + 1):
                    if u % us == 0 and v % vs == 0:
                        index[(ti, u, v)] = len(node_t)
                        node_t.append(ti); node_u.append(u); node_v.append(v)
        self.node_type = np.array(node_t); self.u = np.array(node_u); self.v = np.array(node_v)
        self.n = len(node_t)
        tid = {t: i for i, t in enumerate(self.types)}
        by_type = {ti: np.flatnonzero(self.node_type == ti) for ti in range(len(self.types))}
        src, tgt, sign, nsyn, grp, pair = [], [], [], [], [], []
        groups, pairs, group_nsyn = {}, {}, []
        for e in s["edges"]:
            offs = _fill_hull(e["offsets"]) if len(e["offsets"]) >= 3 else e["offsets"]
            a, b = tid[e["src"]], tid[e["tar"]]
            for (du, dv), n_syn in offs:
                for i in by_type[a]:
                    j = index.get((b, self.u[i] + du, self.v[i] + dv))
                    if j is None:
                        continue
                    g = groups.setdefault((a, b, du, dv), len(groups))
                    if g == len(group_nsyn):
                        group_nsyn.append(n_syn)
                    p = pairs.setdefault((a, b), len(pairs))
                    src.append(i); tgt.append(j); sign.append(e["alpha"]); nsyn.append(n_syn)
                    grp.append(g); pair.append(p)
        self.src, self.tgt = np.array(src), np.array(tgt)
        self.sign = np.array(sign, float); self.nsyn = np.array(nsyn, float)
        self.grp, self.pair = np.array(grp), np.array(pair)
        self.group_nsyn = np.array(group_nsyn, float)
        self.n_groups, self.n_pairs = len(groups), len(pairs)
        self.pair_types = [k for k, _ in sorted(pairs.items(), key=lambda kv: kv[1])]
        r = s["input_units"]
        self.input_nodes = np.flatnonzero(np.isin(self.node_type, [tid[t] for t in r]))
        # column of each input node, so a luminance per (u, v) reaches R1-R8 of that column
        self.cols = sorted({(int(a), int(b)) for a, b in zip(self.u, self.v)})
        col_index = {c: k for k, c in enumerate(self.cols)}
        self.input_col = np.array([col_index[(self.u[i], self.v[i])] for i in self.input_nodes])
        self.node_col = np.array([col_index[(int(a), int(b))] for a, b in zip(self.u, self.v)])
        self.tid = tid
        self.params = None

    def set_model(self, path: Path) -> None:
        d = load(path)["network"]
        assert len(d["edges_syn_count"]) == self.n_groups, (len(d["edges_syn_count"]), self.n_groups)
        assert len(d["edges_syn_strength"]) == self.n_pairs, (len(d["edges_syn_strength"]), self.n_pairs)
        # syn_count is stored as log(n_syn) (Lognormal parameter, semantic value = exp(raw))
        self.nsyn_ckpt = np.exp(d["edges_syn_count"].astype(float))
        w = self.sign * self.nsyn_ckpt[self.grp] * d["edges_syn_strength"][self.pair]
        self.W = sparse.csr_matrix((w, (self.tgt, self.src)), shape=(self.n, self.n))
        self.tau = d["nodes_time_const"][self.node_type].astype(float)
        self.bias = d["nodes_bias"][self.node_type].astype(float)
        self.ckpt = d

    def run(self, lum: np.ndarray, dt: float, v0: np.ndarray | None = None, record=None,
            inject: np.ndarray | None = None) -> np.ndarray:
        """lum: (T, n_cols) luminance per frame; inject: optional (T, n_cols) current scale per frame,
        multiplied by self.inject_gain (per node). Returns V (T, n) or V[:, record]."""
        v = self.bias.copy() if v0 is None else v0.copy()
        k = dt / np.maximum(self.tau, dt)
        out = []
        x = np.zeros(self.n)
        for ti, f in enumerate(lum):
            x[self.input_nodes] = f[self.input_col]
            drive = x if inject is None else x + self.inject_gain * inject[ti][self.node_col]
            v = v + k * (-v + self.bias + self.W @ np.maximum(v, 0.0) + drive)
            out.append(v if record is None else v[record])
        return np.array(out)

    def steady(self, value=0.5, dt=0.005, t=2.0) -> np.ndarray:
        lum = np.full((int(t / dt), len(self.cols)), value)
        return self.run(lum, dt)[-1]

    def central(self, typ: str) -> int:
        ti = self.tid[typ]
        idx = np.flatnonzero(self.node_type == ti)
        return int(idx[np.argmin(np.abs(self.u[idx]) + np.abs(self.v[idx]) + np.abs(self.u[idx] + self.v[idx]))])

    def col_xy(self) -> np.ndarray:
        """Column centres in a Cartesian frame (flat hex axial -> pixel; unit spacing)."""
        u = np.array([c[0] for c in self.cols], float); v = np.array([c[1] for c in self.cols], float)
        return np.stack([1.5 * u, np.sqrt(3) * (v + u / 2)], 1)


def edge_sweep(net: FlyvisNet, angle_deg: float, on: bool, speed=13.0, dt=0.005, v0=None, rec=None):
    """A full-field moving edge (ON: dark->bright behind the edge), speed in columns/s."""
    xy = net.col_xy()
    d = np.array([np.cos(np.radians(angle_deg)), np.sin(np.radians(angle_deg))])
    proj = xy @ d
    T = int((proj.max() - proj.min()) / speed / dt) + int(0.3 / dt)
    t = np.arange(T) * dt
    front = proj.min() - 1 + speed * t
    passed = proj[None, :] <= front[:, None]
    lum = np.where(passed, 1.0 if on else 0.0, 0.5)
    return net.run(lum, dt, v0=v0, record=rec)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="0,1,2")
    a = ap.parse_args()
    net = FlyvisNet()
    print(f"{net.n} nodes, {len(net.src)} edges, {net.n_groups} count groups, {net.n_pairs} type pairs")
    root = RAW / "results" / "flow" / "0000"
    angles = np.arange(0, 360, 30)
    t4 = ["T4a", "T4b", "T4c", "T4d"]; t5 = ["T5a", "T5b", "T5c", "T5d"]
    for m in [int(x) for x in a.models.split(",")]:
        net.set_model(root / f"{m:03d}" / "best_chkpt")
        same = np.allclose(net.nsyn_ckpt, net.group_nsyn, rtol=1e-4)
        print(f"model {m:03d}: checkpoint synapse counts equal the spec's: {same}")
        v0 = net.steady()
        rec = np.array([net.central(t) for t in t4 + t5])
        peak_on, peak_off = [], []
        for ang in angles:
            peak_on.append(np.maximum(edge_sweep(net, ang, True, v0=v0, rec=rec) - v0[rec], 0).max(0))
            peak_off.append(np.maximum(edge_sweep(net, ang, False, v0=v0, rec=rec) - v0[rec], 0).max(0))
        peak_on, peak_off = np.array(peak_on), np.array(peak_off)
        for k, ty in enumerate(t4 + t5):
            p = peak_on[:, k] if ty.startswith("T4") else peak_off[:, k]
            pd_ = angles[np.argmax(p)]
            nd = (pd_ + 180) % 360
            dsi = (p.max() - p[angles == nd][0]) / (p.max() + p[angles == nd][0] + 1e-12)
            print(f"  {ty}: preferred {pd_:3d} deg, DSI {dsi:.2f}, peak {p.max():.3f}")


if __name__ == "__main__":
    main()
