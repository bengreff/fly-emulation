"""The ported MetaWorm (BAAIWorm) body: run the headless C++ driver and read gait out of its vertex frames.

The physics is upstream C++ in third_party/metaworm/sim (unchanged); third_party/metaworm/driver/run_body.cpp only
replaces the GUI loop and Python bridge. Here: run it, load the frames, and measure the gait the same way as the
rod tests (docs/worm/BODY_TESTS.md): complex demodulation of a dorsoventral curvature kymograph.

Midline: the rest mesh is cut into material slices along its long axis; the midline node of a slice is the mean
current position of its vertices. Signed curvature = d(tangent)/ds projected on the slice's current dorsoventral
direction (mean dorsal-half vertex minus mean ventral-half vertex, made normal to the tangent), so dorsal bending
is positive. Curvatures are reported as kappa * L and speeds in L/s, L = rest length (0.628 sim units).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3] / "third_party" / "metaworm"
DRIVER = ROOT / "driver" / "run_body"
MUSCLES = ("MDR", "MVR", "MDL", "MVL")  # upstream order (Worm::MakeMuscles reads the obj "o" lines)
N_SEG = 24  # sampling segments per muscle string, head first


def run(out: str | Path, mode: str = "key", seconds: float = 10.0, key: str | None = None, f: float = 1.76,
        lam: float = 1.54, amp: float = 0.03, release_at: float | None = None, frame_every: int = 1) -> dict:
    """Run the driver (cwd = third_party/metaworm, as upstream expects) and return load(out)."""
    if not DRIVER.exists():
        subprocess.run([str(ROOT / "driver" / "build.sh")], check=True)
    cmd = [str(DRIVER), "--mode", mode, "--seconds", str(seconds), "--f", str(f), "--lam", str(lam),
           "--amp", str(amp), "--frame_every", str(frame_every), "--out", str(out)]
    if key:
        cmd += ["--key", key]
    if release_at is not None:
        cmd += ["--release_at", str(release_at)]
    subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
    return load(out)


def load(prefix: str | Path) -> dict:
    prefix = str(prefix)
    meta = json.load(open(prefix + ".json"))
    nv, na = meta["n_vertices"], meta["n_act"]
    X = np.fromfile(prefix + ".frames.f32", np.float32).reshape(-1, nv, 3).astype(float)
    A = np.fromfile(prefix + ".act.f32", np.float32).reshape(-1, na).astype(float)
    t = np.arange(len(X)) * meta["frame_dt"]
    return {"meta": meta, "X": X, "A": A, "t": t}


class Frame:
    """Material frame of the rest mesh: long axis, head end, dorsoventral axis, slices."""

    def __init__(self, meta: dict, X0: np.ndarray, n_slices: int = 48):
        starts = np.array(meta["segment_starts"]).reshape(len(MUSCLES), N_SEG, 3)
        c0 = X0.mean(0)
        u, sv, vt = np.linalg.svd(X0 - c0, full_matrices=False)
        ax = vt[0]
        head = starts[:, 0].mean(0)
        if (head - c0) @ ax > 0:  # axis points head -> tail
            ax = -ax
        z = (X0 - c0) @ ax
        self.length = z.max() - z.min()
        self.s = (z - z.min()) / self.length  # 0 = head tip, 1 = tail tip
        dors = starts[[0, 2]].mean((0, 1)) - starts[[1, 3]].mean((0, 1))
        dv = dors - (dors @ ax) * ax
        self.dv0 = dv / np.linalg.norm(dv)
        self.dorsal = (X0 - c0) @ self.dv0 > 0
        self.n = n_slices
        self.slice = np.minimum((self.s * n_slices).astype(int), n_slices - 1)
        self.s_nodes = (np.arange(n_slices) + 0.5) / n_slices
        self.ax0 = ax
        self.X0 = X0
        self.head_vertex = int(np.argmin(self.s))

    def midline(self, X: np.ndarray) -> np.ndarray:
        """[n_frames, n_slices, 3] midline nodes."""
        out = np.zeros((len(X), self.n, 3))
        for k in range(self.n):
            out[:, k] = X[:, self.slice == k].mean(1)
        return out

    def dv_dirs(self, X: np.ndarray) -> np.ndarray:
        out = np.zeros((len(X), self.n, 3))
        for k in range(self.n):
            m = self.slice == k
            out[:, k] = X[:, m & self.dorsal].mean(1) - X[:, m & ~self.dorsal].mean(1)
        return out

    def curvature(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Signed dorsoventral curvature kappa*L at interior nodes: (s_interior, [n_frames, n_slices-2])."""
        c = self.midline(X)
        e = np.diff(c, axis=1)
        le = np.linalg.norm(e, axis=2)
        T = e / le[..., None]
        dT = (T[:, 1:] - T[:, :-1]) / (0.5 * (le[:, 1:] + le[:, :-1]))[..., None]
        d = self.dv_dirs(X)[:, 1:-1]
        Tn = 0.5 * (T[:, 1:] + T[:, :-1])
        Tn /= np.linalg.norm(Tn, axis=2, keepdims=True)
        d = d - (d * Tn).sum(2, keepdims=True) * Tn
        d /= np.linalg.norm(d, axis=2, keepdims=True)
        return self.s_nodes[1:-1], (dT * d).sum(2) * self.length

    def shape_rms(self, X: np.ndarray) -> np.ndarray:
        """RMS vertex deviation from the rest shape after best rigid alignment (Kabsch), / L, per frame."""
        A0 = self.X0 - self.X0.mean(0)
        out = np.zeros(len(X))
        for i, x in enumerate(X):
            B = x - x.mean(0)
            U, _, Vt = np.linalg.svd(B.T @ A0)
            R = U @ np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))]) @ Vt
            out[i] = np.sqrt(((B - A0 @ R.T) ** 2).sum(1).mean()) / self.length
        return out


def gait(rec: dict, f_drive: float, t_from: float, frame: Frame | None = None) -> dict:
    """Gait readouts over [t_from, end], trimmed to a whole number of drive periods ending at the last frame."""
    fr = frame or Frame(rec["meta"], rec["X"][0])
    t = rec["t"]
    n_per = int(np.floor((t[-1] - t_from) * f_drive + 1e-9))
    w = t >= t[-1] - n_per / f_drive - 1e-9
    tw, X = t[w], rec["X"][w]
    s, k = fr.curvature(X)
    kc = k - k.mean(0)
    mid = kc[:, (s > 0.3) & (s < 0.7)]
    fgrid = np.linspace(0.5 * f_drive, 1.5 * f_drive, 401)
    pw = np.array([np.abs(np.exp(-2j * np.pi * fg * tw) @ mid).sum() for fg in fgrid])
    f_body = fgrid[pw.argmax()]
    c = (np.exp(-2j * np.pi * f_drive * tw) @ kc) / len(tw)
    amp = 2 * np.abs(c)
    band = (s >= 0.1) & (s <= 0.9)
    ph = np.unwrap(np.angle(c[band]))
    slope = np.polyfit(s[band], ph, 1)[0]
    lam = 2 * np.pi / abs(slope) if slope != 0 else np.inf
    cen = X.mean(1)
    disp = cen[-1] - cen[0]
    hd = X[:, fr.head_vertex] - cen  # head direction from the centroid
    sign = np.sign(disp @ hd.mean(0))
    speed = sign * np.linalg.norm(disp) / (tw[-1] - tw[0]) / fr.length
    head = amp[(s >= 0.1) & (s <= 0.2)].mean()
    tail = amp[(s >= 0.8) & (s <= 0.9)].mean()
    return {"periods": n_per, "f_body_hz": float(f_body), "wavelength_L": float(lam), "wave_dir": float(-np.sign(slope)),
            "head_amp_kL": float(head), "tail_amp_kL": float(tail), "tail_head_ratio": float(tail / head),
            "speed_L_s": float(speed), "amp_profile_kL": amp.tolist(), "s": s.tolist(),
            "mean_kL_profile": k.mean(0).tolist()}


def zigzag(rec: dict, t_from: float, f_drive: float, frame: Frame | None = None) -> dict:
    """Head-tip path relative to the net centroid path over [t_from, end]: net displacement (L, signed head
    first), dominant frequency of the head's lateral excursion, net heading change (deg) of the body axis."""
    fr = frame or Frame(rec["meta"], rec["X"][0])
    t = rec["t"]
    w = t >= t_from - 1e-9
    X = rec["X"][w]
    tw = t[w]
    cen = X.mean(1)
    net = cen[-1] - cen[0]
    nd = net / np.linalg.norm(net)
    head = X[:, fr.head_vertex]
    hd_mean = (head - cen).mean(0)
    sign = np.sign(net @ hd_mean)
    rel = head - cen[0]
    lat = rel - np.outer(rel @ nd, nd)
    # lateral excursion in the plane of the motion: project on its principal direction
    lat_c = lat - lat.mean(0)
    _, _, vt = np.linalg.svd(lat_c, full_matrices=False)
    y = lat_c @ vt[0]
    fgrid = np.linspace(0.2 * f_drive, 3.0 * f_drive, 561)
    pw = np.array([np.abs(np.exp(-2j * np.pi * fg * tw) @ (y - y.mean())) for fg in fgrid])
    # heading = centroid displacement over the first and over the last two drive periods of the window
    n2 = int(round(2 / f_drive / (tw[1] - tw[0])))
    a0 = cen[n2] - cen[0]
    a1 = cen[-1] - cen[-1 - n2]
    ang = np.degrees(np.arccos(np.clip(a0 @ a1 / np.linalg.norm(a0) / np.linalg.norm(a1), -1, 1)))
    return {"net_disp_L": float(sign * np.linalg.norm(net) / fr.length), "head_lat_f_hz": float(fgrid[pw.argmax()]),
            "head_lat_amp_L": float(np.ptp(y) / 2 / fr.length), "heading_change_deg": float(ang)}
