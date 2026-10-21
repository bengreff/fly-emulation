"""s15c (fly, 21 Oct): passive multi-compartment cells from male-CNS EM skeletons (CPU reference path).

One compartment per skeleton node (node-centred: a node owns half of each frustum it touches; the soma node is
a sphere of the root radius, as mn_axon_geometry.reduce). Axial conductance along each skeleton edge from the
frustum, pi r1 r2 / (Ri dl). Backward Euler on the whole block-diagonal set of cells: the passive matrix is
constant, so it is factorised once (scipy splu) and each step is one solve.

Units: V mV, t ms, C pF, G nS, I pA (pF mV/ms = pA = nS mV).

Validity: passive uniform membrane (Rm, Cm, Ri shared); skeleton radii as traced (no shrinkage correction),
radii <= R_MIN_UM replaced by the mean of the cell's neighbouring traced radii; isopotential compartments of the
skeleton's own node spacing. The active spike zone is not here (lif's hybrid applies a threshold at a node).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.sparse as sp

VOXEL_UM = 0.008
R_MIN_UM = 0.05
DL_MIN_UM = 0.01


@dataclass
class Cell:
    """One skeleton as compartments. par[root] = -1; xyz um; area um2; gax_per_ri = pi r1 r2 / dl (um), the
    axial conductance of each node's edge to its parent times Ri (so G = 1e5 gax_per_ri / Ri nS)."""
    body_id: int
    xyz: np.ndarray
    rad: np.ndarray
    par: np.ndarray
    root: int
    order: np.ndarray
    area: np.ndarray
    gax_per_ri: np.ndarray
    n_radius_filled: int

    @property
    def n(self) -> int:
        return len(self.xyz)

    def path_dist(self) -> np.ndarray:
        d = np.zeros(self.n)
        for v in self.order[1:]:
            d[v] = d[self.par[v]] + np.linalg.norm(self.xyz[v] - self.xyz[self.par[v]])
        return d

    def nearest(self, pts_um: np.ndarray) -> np.ndarray:
        from scipy.spatial import cKDTree
        return cKDTree(self.xyz).query(pts_um)[1]


def build_cell(skel: pd.DataFrame, soma_um: np.ndarray | None, body_id: int = 0) -> Cell:
    """Compartments from a neuPrint skeleton (rowId, x, y, z, radius, link; voxels), re-rooted at the node
    nearest the soma (mn_axon_geometry.tree)."""
    from scipy.sparse.csgraph import breadth_first_order
    s = skel.reset_index(drop=True)
    idx = {r: i for i, r in enumerate(s.rowId.to_numpy())}
    par0 = np.array([idx.get(l, -1) for l in s.link.to_numpy()])
    xyz = s[["x", "y", "z"]].to_numpy(float) * VOXEL_UM
    rad = s.radius.to_numpy(float) * VOXEL_UM
    n = len(s)
    ch = np.flatnonzero(par0 >= 0)
    g = sp.coo_matrix((np.ones(ch.size), (ch, par0[ch])), shape=(n, n)).tocsr()
    root = int(np.argmin(np.linalg.norm(xyz - soma_um, axis=1))) if soma_um is not None else 0
    order, pred = breadth_first_order(g, root, directed=False, return_predecessors=True)
    if order.size != n:
        raise ValueError(f"{body_id}: skeleton has {n - order.size} nodes outside the root component")
    par = np.where(pred < 0, -1, pred)
    par[root] = -1
    # untraced radii: the mean of the neighbours' traced radii (parent and children), else the cell's q10
    bad = rad <= R_MIN_UM
    nfill = int(bad.sum())
    if nfill:
        good = ~bad
        fill = np.quantile(rad[good], 0.1) if good.any() else 0.1
        nb_sum, nb_n = np.zeros(n), np.zeros(n)
        e = np.flatnonzero(par >= 0)
        for a, b in ((e, par[e]), (par[e], e)):
            m = good[b]
            np.add.at(nb_sum, a[m], rad[b[m]])
            np.add.at(nb_n, a[m], 1)
        rad = rad.copy()
        rad[bad] = np.where(nb_n[bad] > 0, nb_sum[bad] / np.maximum(nb_n[bad], 1), fill)
    has = par >= 0
    pp = np.maximum(par, 0)
    dl = np.where(has, np.maximum(np.linalg.norm(xyz - xyz[pp], axis=1), DL_MIN_UM), 0.0)
    r1, r2 = rad, rad[pp]
    a_e = np.where(has, np.pi * (r1 + r2) * np.sqrt(dl ** 2 + (r1 - r2) ** 2), 0.0)
    a_e[has & (par == root)] = 0.0             # the soma sphere replaces the edges touching it
    area = np.zeros(n)
    np.add.at(area, np.flatnonzero(has), 0.5 * a_e[has])
    np.add.at(area, par[has], 0.5 * a_e[has])
    area[root] += 4.0 * np.pi * rad[root] ** 2
    gax = np.divide(np.pi * r1 * r2, dl, out=np.zeros(n), where=has)
    return Cell(body_id, xyz, rad, par, root, order, area, gax, nfill)


class CableSet:
    """Block-diagonal passive cells, backward Euler with a constant factorised matrix.
    rm_ohm_cm2, cm_uf_cm2, ri_ohm_cm shared; e_leak (mV) per cell."""

    def __init__(self, cells: list[Cell], rm_ohm_cm2: float, cm_uf_cm2: float, ri_ohm_cm: float,
                 e_leak: np.ndarray, dt_ms: float):
        self.cells, self.dt = cells, dt_ms
        self.off = np.concatenate([[0], np.cumsum([c.n for c in cells])]).astype(np.int64)
        N = int(self.off[-1])
        area = np.concatenate([c.area for c in cells])
        self.C = cm_uf_cm2 * area * 0.01                      # pF
        self.GL = area * 10.0 / rm_ohm_cm2                    # nS
        i_, j_, g_ = [], [], []
        for k, c in enumerate(cells):
            e = np.flatnonzero(c.par >= 0)
            i_.append(e + self.off[k])
            j_.append(c.par[e] + self.off[k])
            g_.append(1e5 * c.gax_per_ri[e] / ri_ohm_cm)      # nS
        i_, j_, g_ = (np.concatenate(x) for x in (i_, j_, g_))
        L = sp.coo_matrix((np.concatenate([-g_, -g_]), (np.concatenate([i_, j_]), np.concatenate([j_, i_]))),
                          shape=(N, N)).tocsr()
        diag = np.asarray(-L.sum(axis=1)).ravel()
        self.L = (L + sp.diags(diag)).tocsc()                 # Laplacian: (L V)_i = sum g (V_i - V_j)
        self.E = np.concatenate([np.full(c.n, float(e_leak[k])) for k, c in enumerate(cells)])
        A = (sp.diags(self.C / dt_ms + self.GL) + self.L).tocsc()
        from scipy.sparse.linalg import splu
        self.lu = splu(A, permc_spec="MMD_AT_PLUS_A")
        self.V = self.E.copy()
        self.cell_of = np.repeat(np.arange(len(cells)), np.diff(self.off))

    def step(self, i_pa: np.ndarray | None = None) -> np.ndarray:
        rhs = self.C / self.dt * self.V + self.GL * self.E
        if i_pa is not None:
            rhs = rhs + i_pa
        self.V = self.lu.solve(rhs)
        return self.V

    def g_total_ns(self) -> np.ndarray:
        """Per-cell leak conductance (nS); 1e3 / it is the isopotential input resistance (MOhm)."""
        return np.bincount(self.cell_of, self.GL)

    def input_resistance_mohm(self, nodes: np.ndarray) -> np.ndarray:
        """DC input resistance at one global node per cell (MOhm): solve (GL + L) V = e_node."""
        from scipy.sparse.linalg import splu
        lu = splu((sp.diags(self.GL) + self.L).tocsc(), permc_spec="MMD_AT_PLUS_A")
        out = np.zeros(len(nodes))
        b = np.zeros(len(self.GL))
        b[nodes] = 1.0                                        # 1 pA each; cells are independent blocks
        v = lu.solve(b)
        out[:] = v[nodes] * 1e3                               # mV / pA = GOhm -> MOhm
        return out
