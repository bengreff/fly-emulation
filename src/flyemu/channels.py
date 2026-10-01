"""Intrinsic conductances per cell type (fidelity ladder rung 1, session 11).

Interpretation: a point neuron whose membrane carries, besides the leak, eight
intrinsic conductances with per-type densities from transcriptomes. Spike
generation stays threshold-and-reset (the fast Na/K spike waveform is
abstracted), so channels that open only during a spike (Kv2/Shab, BK/slo, the
HVA Ca entry through cac) are driven by a per-spike gate increment; the
subthreshold and slow channels (A-type, M-type, Ih, T-type Ca, persistent Na,
SK via a Ca pool) follow the membrane potential. Validity: membrane dynamics
between spikes and on the 1-1000 ms scale at the network step (0.1 ms); not the
spike shape, not dendritic compartments (ladder rung 6).

In units of the leak conductance g_L0 (tau_m = C / g_L0):

    tau_m dv/dt = -(v - v_rest) + drive + sum_k g_k (x_k - x_k,rest) (E_k - v)

i.e. the measured/declared rest potential and input conductance at rest are
taken to include the resting intrinsic conductances (the leak is reduced by
sum_k g_k x_k,rest and its reversal shifted to keep v_rest). A cell's g_k at rest
is capped so the remaining leak is >= 10% of g_L0.

Density: g_k(cell) = gbar_k x rel_level(type, gene_k)^beta. rel_level is the
type's mRNA level over the median of profiled types
(data/derived/channel_expression_by_type.csv: Davis 2020, Özel 2021); VNC cells
of unprofiled types take their hemilineage's level over the all-neuron mean
(Allen 2020, inferred: proxy cluster labels); the rest take 1 (class prior).
beta = 0 makes every type equal (no transcriptome rule).

Kinetics (KINETICS below) are generic insect-neuron Boltzmann forms with
constant time constants: guessed, to be replaced by Drosophila voltage-clamp
fits (e.g. Shal/Sh: Ryglewski & Duch 2009-2012 motoneurons; Ih, T-type:
Gu & O'Dowd 2007 cultured neurons). Every value is labelled where declared.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
EXPRESSION = _REPO / "data/derived/channel_expression_by_type.csv"
# VNC fallback at hemilineage grain: Allen 2020 atlas, marker-proxy cluster labels
# (scripts/channels_allen2020_vnc.py), joined to trumanHl through the Allen->Truman
# table of scripts/receptors_allen2020_vnc.py; rel = mean_cp10k / all-neuron mean.
EXPRESSION_HL = _REPO / "data/derived/channel_expression_allen2020_vnc.csv"
HL_JOIN = _REPO / "data/derived/glutamate_sign_by_hemilineage_allen2020.csv"
HL_CELLS = _REPO / "data/cache/male_cns_hemilineage.parquet"
E_K, E_NA, E_CA, E_H = -80.0, 50.0, 100.0, -35.0   # mV; guessed insect-saline reversals

# name: (genes setting density, reversal mV, role, prior gbar x g_L0 (guessed))
CHANNELS = {
    "A":   (("Shal", "Sh"), E_K, "A-type K (Kv4/Kv1): delays and sparsens firing", 3.0),
    "M":   (("KCNQ",), E_K, "M-type slow K (Kv7): subthreshold adaptation", 0.3),
    "h":   (("Ih",), E_H, "Ih (HCN): sag and rebound", 0.2),
    "T":   (("Ca-alpha1T",), E_CA, "T-type Ca (Cav3): rebound depolarisation", 0.3),
    "NaP": (("para",), E_NA, "persistent Na (Nav): plateau and amplification", 0.02),
    "Kv2": (("Shab",), E_K, "delayed rectifier (Kv2), spike-triggered: slow AHP", 0.5),
    "BK":  (("slo",), E_K, "BK (slo), spike-triggered: fast AHP", 1.0),
    "SK":  (("SK",), E_K, "SK, gated by the spike Ca pool: medium AHP and adaptation", 0.5),
}
# Gate kinetics (all guessed generic forms; see module docstring)
KINETICS = {
    "A_act": (-40.0, 8.0, 1.0),        # v_half mV, slope mV (+ = activates with depolarisation), tau ms
    "A_inact": (-65.0, -6.0, 25.0),
    "M_act": (-35.0, 10.0, 100.0),
    "h_act": (-75.0, -8.0, 150.0),
    "T_act": (-55.0, 6.0, 0.0),        # tau 0 = instantaneous
    "T_inact": (-75.0, -5.0, 30.0),
    "NaP_act": (-48.0, 5.0, 0.0),
    "Kv2": (0.3, 15.0),                # per-spike gate increment toward 1, decay tau ms
    "BK": (0.5, 3.0),
    "Ca": (1.0, 80.0),                 # pool units per spike (x cac rel_level^beta), decay tau ms
    "SK_kd": 2.0,                      # pool units for half activation
}
REST_LEAK_FLOOR = 0.1


def _boltz(v, vh, k):
    return 1.0 / (1.0 + np.exp(-(v - vh) / k))


def _hl_rel(body_ids: np.ndarray) -> pd.DataFrame | None:
    """Per-cell (rows aligned to body_ids) Allen hemilineage rel levels, NaN where none."""
    if not (EXPRESSION_HL.exists() and HL_JOIN.exists() and HL_CELLS.exists()):
        return None
    a = pd.read_csv(EXPRESSION_HL)
    ref = a[a.allen_hl == "ALL_NEURONS"].set_index("gene").mean_cp10k
    a = a[a.allen_hl != "ALL_NEURONS"].assign(rel=lambda d: d.mean_cp10k / d.gene.map(ref))
    rel = a.pivot_table(index="allen_hl", columns="gene", values="rel")
    j = pd.read_csv(HL_JOIN)[["allen_hl", "trumanHl"]]
    j = j.assign(trumanHl=j.trumanHl.str.split("/")).explode("trumanHl").dropna()
    by_t = rel.loc[rel.index.intersection(j.allen_hl)]
    by_t = j.set_index("allen_hl").join(by_t, how="inner").set_index("trumanHl")
    cells = pd.read_parquet(HL_CELLS, columns=["bodyId", "trumanHl"]).dropna()
    hl = pd.Series(cells.trumanHl.to_numpy(), index=cells.bodyId.to_numpy())
    hl = hl[~hl.index.duplicated()]
    per = hl.reindex(body_ids)
    return by_t.reindex(per.to_numpy()).set_axis(range(len(body_ids)))


def expression_factors(types: np.ndarray, beta: float, body_ids: np.ndarray | None = None,
                       path: Path = EXPRESSION) -> tuple[dict, np.ndarray]:
    """Per-cell density factor per channel: rel_level^beta. Precedence: type-level
    (Davis/Özel) > VNC hemilineage (Allen) > 1. Returns ({channel: factor}, source per
    cell: 2 type, 1 hemilineage, 0 prior)."""
    n = len(types)
    out = {c: np.ones(n, np.float32) for c in CHANNELS}
    out["Ca"] = np.ones(n, np.float32)
    src = np.zeros(n, np.int8)
    rel = None
    if path.exists():
        e = pd.read_csv(path)
        rel = e.pivot_table(index="male_cns_type", columns="gene", values="rel_level")
        idx = pd.Index(rel.index).get_indexer(types)
        src[idx >= 0] = 2
    hlr = _hl_rel(body_ids) if body_ids is not None else None
    if hlr is not None:
        src[(src == 0) & hlr.notna().any(axis=1).to_numpy()] = 1
    if beta == 0.0:
        return out, src

    def factor(genes):
        lv = np.ones(n)
        if rel is not None:
            g = [x for x in genes if x in rel.columns]
            if g:
                t = np.exp(np.log(rel[g].clip(lower=1e-3)).mean(axis=1)).to_numpy()   # geometric mean
                lv[src == 2] = t[idx[src == 2]]
        if hlr is not None:
            g = [x for x in genes if x in hlr.columns]
            if g:
                h = np.exp(np.log(hlr[g].clip(lower=1e-3)).mean(axis=1)).to_numpy()
                lv[src == 1] = h[src == 1]
        return (lv ** beta).astype(np.float32)

    for c, spec in CHANNELS.items():
        out[c] = factor(spec[0])
    out["Ca"] = factor(("cac",))
    return out, src


@dataclass
class Intrinsic:
    """Per-cell maximal conductances (x g_L0) and the state of every gate."""
    g: dict                     # channel -> per-cell gbar array (float32)
    ca_per_spike: np.ndarray
    dt: float
    n_capped: int = 0
    source: np.ndarray | None = None   # per cell: 2 type mRNA, 1 hemilineage mRNA, 0 prior
    ca_tau: float = KINETICS["Ca"][1]  # ms, decay of the spike Ca pool

    def init(self, v_rest: np.ndarray) -> None:
        self.state = {}
        x_r = self._steady(v_rest)
        tot = sum(self.g[c] * x_r[c] for c in x_r)
        scale = np.where(tot > 1.0 - REST_LEAK_FLOOR, (1.0 - REST_LEAK_FLOOR) / np.maximum(tot, 1e-9), 1.0)
        self.n_capped = int((scale < 1.0).sum())
        if self.n_capped:
            self.g = {c: (g * scale).astype(np.float32) for c, g in self.g.items()}
        self.x_r = x_r
        self.rev = {c: CHANNELS[c][1] for c in CHANNELS}
        self.a = _boltz(v_rest, *KINETICS["A_act"][:2]).astype(np.float32)
        self.b = _boltz(v_rest, *KINETICS["A_inact"][:2]).astype(np.float32)
        self.w = _boltz(v_rest, *KINETICS["M_act"][:2]).astype(np.float32)
        self.hh = _boltz(v_rest, *KINETICS["h_act"][:2]).astype(np.float32)
        self.th = _boltz(v_rest, *KINETICS["T_inact"][:2]).astype(np.float32)
        n = len(v_rest)
        self.n_kv2 = np.zeros(n, np.float32)
        self.n_bk = np.zeros(n, np.float32)
        self.ca = np.zeros(n, np.float32)
        dt = self.dt
        self.d = {k: np.float32(np.exp(-dt / KINETICS[k][2])) for k in ("A_act", "A_inact", "M_act", "h_act", "T_inact")}
        self.d_kv2 = np.float32(np.exp(-dt / KINETICS["Kv2"][1]))
        self.d_bk = np.float32(np.exp(-dt / KINETICS["BK"][1]))
        self.d_ca = np.float32(np.exp(-dt / self.ca_tau))
        self.on = [c for c in CHANNELS if np.any(self.g[c] > 0)]

    @staticmethod
    def _steady(v) -> dict:
        """Open fraction of every channel at a fixed potential (spike-driven gates closed)."""
        a = _boltz(v, *KINETICS["A_act"][:2]); b = _boltz(v, *KINETICS["A_inact"][:2])
        t = _boltz(v, *KINETICS["T_act"][:2]); th = _boltz(v, *KINETICS["T_inact"][:2])
        z = np.zeros_like(v, dtype=np.float32)
        return {"A": (a ** 3 * b).astype(np.float32),
                "M": _boltz(v, *KINETICS["M_act"][:2]).astype(np.float32),
                "h": _boltz(v, *KINETICS["h_act"][:2]).astype(np.float32),
                "T": (t ** 2 * th).astype(np.float32),
                "NaP": _boltz(v, *KINETICS["NaP_act"][:2]).astype(np.float32),
                "Kv2": z, "BK": z, "SK": z}

    def step(self, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Advance gates by one step at potential v. Returns (dG, dGE): the change of
        intrinsic conductance from rest and its reversal-weighted sum, both x g_L0."""
        K, d = KINETICS, self.d

        def relax(x, key):   # exponential Euler toward the steady state at v
            inf = _boltz(v, *K[key][:2])
            return inf + (x - inf) * d[key]

        self.a = relax(self.a, "A_act")
        self.b = relax(self.b, "A_inact")
        self.w = relax(self.w, "M_act")
        self.hh = relax(self.hh, "h_act")
        self.th = relax(self.th, "T_inact")
        self.n_kv2 *= self.d_kv2
        self.n_bk *= self.d_bk
        self.ca *= self.d_ca
        x = {"A": self.a ** 3 * self.b, "M": self.w, "h": self.hh,
             "T": _boltz(v, *K["T_act"][:2]) ** 2 * self.th, "NaP": _boltz(v, *K["NaP_act"][:2]),
             "Kv2": self.n_kv2, "BK": self.n_bk, "SK": self.ca / (self.ca + K["SK_kd"])}
        dG = np.zeros_like(v)
        dGE = np.zeros_like(v)
        for c in self.on:
            gx = self.g[c] * (x[c] - self.x_r[c])
            dG += gx
            dGE += gx * self.rev[c]
        return dG.astype(np.float32), dGE.astype(np.float32)

    def on_spike(self, idx: np.ndarray) -> None:
        self.n_kv2[idx] += (1.0 - self.n_kv2[idx]) * KINETICS["Kv2"][0]
        self.n_bk[idx] += (1.0 - self.n_bk[idx]) * KINETICS["BK"][0]
        self.ca[idx] += self.ca_per_spike[idx]


def from_registry(reg, conn, *, timestep_ms: float) -> Intrinsic | None:
    """Read the rung-1 keys (always, so the inventory is complete); None when off."""
    n = conn.n
    on = reg.require("cell_type:all", "intrinsic_channels", units="boolean",
                     model_use="N2 rung 1: intrinsic conductances per type (src/flyemu/channels.py)",
                     subsystem="neuron_biophysics", instances=n, minimal=0.0, conventional=0.0,
                     minimal_note="neutral 0: leak-only LIF membrane (m4-m7)")
    beta = reg.require("channel:all", "expression_exponent", units="dimensionless",
                       model_use="density = gbar x (type mRNA level / median)^beta",
                       subsystem="neuron_biophysics", instances=n, minimal=0.5, conventional=0.5,
                       minimal_note="guessed 0.5: mRNA is a weak proxy for channel density "
                                    "(Davis vs Özel relative levels agree at r 0.29)")
    gbar = {}
    for c, (genes, _rev, use, prior) in CHANNELS.items():
        gbar[c] = reg.require(f"channel:{c}", "gbar", units="x leak conductance",
                              model_use=f"{use}; density from {'/'.join(genes)} expression",
                              subsystem="neuron_biophysics", instances=n, minimal=prior, conventional=prior,
                              minimal_note="guessed prior: a moderate effect at the median type")
    ca_scale = reg.require("channel:Ca", "per_spike", units="pool units per spike (SK K_d = 2)",
                           model_use="spike Ca entry into the SK pool (x cac rel_level^beta)",
                           subsystem="neuron_biophysics", instances=n, minimal=KINETICS["Ca"][0],
                           conventional=KINETICS["Ca"][0], minimal_note="guessed: half-activates SK at ~2 recent spikes")
    ca_tau = reg.require("channel:Ca", "tau_ms", units="ms", model_use="decay of the spike Ca pool (SK gating)",
                         subsystem="neuron_biophysics", instances=n, minimal=KINETICS["Ca"][1],
                         conventional=KINETICS["Ca"][1], minimal_note="guessed: medium AHP time scale")
    if not on:
        return None
    types = conn.neurons.type.fillna("untyped").to_numpy()
    f, src = expression_factors(types, float(beta), conn.neurons.bodyId.to_numpy())
    g = {c: (float(gbar[c]) * f[c]).astype(np.float32) for c in CHANNELS}
    ca = (float(ca_scale) * f["Ca"]).astype(np.float32)
    return Intrinsic(g=g, ca_per_spike=ca, dt=timestep_ms, source=src, ca_tau=float(ca_tau))
