"""Batched spiking-network simulator in JAX: B parameter variants of one connectome.

Reproduces `flyemu.lif.Network.step` (the CPU reference) for B members at once.
The weight matrix is shared; per-member parameters are per-neuron vectors.

Equations and step order are those of lif.Network.step (see its docstring):

    arriving_i(t) = input_i * mod_i(t) * sum_j W_ij * y_j(t - d_j)
    y_j = release_j * (spike_j * x_res_j)         spiking cells, d_j = delay_steps_j
    y_j = release_j * r_max dt * clip((V-V_rest)/(V_th-V_rest), 0, 1)
                                                   graded cells, d_j = 1

Delays: instead of scattering each spike into a ring buffer of arrival slots
(lif.py), this keeps a ring buffer of the last D presynaptic OUTPUT vectors y and
gathers, per presynaptic cell, the entry from its own delay d_j ago. That makes
the per-step input one sparse product over all edges (a sorted segment sum over
edges ordered by target) whatever the number of delay values; it is the "delay
bucket" decomposition with the buckets fused into a single gather.

Sparsity: activity is sparse (m4: ~1-15 spikes and 0-600 depolarised graded
cells per step), so each step first tries an event path that expands only the
outgoing edges of presynaptic cells with nonzero output in any member, in fixed
capacity tiers (DEFAULT_TIERS); a step that exceeds every tier falls back to the
dense product. Both give the same sums up to float32 order (tested).

Gains: lif.py folds release_gain[pre] * input_gain[post] into each edge weight.
Here W is the reference network's edge weights (its own gains included) and each
member carries relative factors release_b/release_ref (on y, presynaptic) and
input_b/input_ref (on the summed input, postsynaptic). Because both gains factor
per pre and per post cell this is the same product; the float32 rounding differs.

Supported (bit-level semantics of lif.py, float32): exponential-Euler LIF,
refractory period (float32 time comparison as in lif.py), per-presynaptic-type
delays, graded (non-spiking) continuous transmission with a one-step delay,
spike reset of synaptic current, tonic drive (spont_mv), external_mv, kicks
(held while refractory), silence (per member), spike-frequency adaptation,
short-term depression (Tsodyks-Markram resource, incl. ORN/leg depression),
GABA-B slow path, neuromodulator pools, identified electrical synapses
(net.elec kicks), membrane noise (own RNG: statistical equivalence only).

Conductance synapses (params.cond, s11 rung 2): fast excitatory and inhibitory
conductances in separate edge columns, as lif.py. Not supported (raise
NotImplementedError): presynaptic inhibition of sensory terminals (presyn_inh_gain > 0),
DAN-gated KC->MBON depression (kc_mbon_eta > 0; structural plasticity of W).
Static edge transforms (glutamate sign per target, CX ring class normalisation,
FLYEMU_EDGE_SCALES) are inherited from the reference network's weights.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import NamedTuple

import numpy as np

try:
    import jax
    import jax.numpy as jnp
except ImportError as e:  # pragma: no cover
    raise ImportError("flyemu.gpu needs JAX (CPU: `uv pip install jax`; GPU: "
                      "`uv pip install 'jax[cuda12]'`, see docs/GPU.md)") from e

from .. import channels as ichan
from .. import lif

# per-neuron parameters that may differ between batch members
MEMBER_PARAMS = ("release_gain", "input_gain", "spont_mv", "v_rest", "v_th", "v_reset",
                 "tau_m", "t_ref", "tau_s", "adapt_mv", "tau_adapt", "std_u", "std_tau_rec")


# event-path tiers (active cells, edges); measured on the 4070 Ti SUPER (docs/GPU.md)
DEFAULT_TIERS = ((1024, 16384), (4096, 65536))


class Cfg(NamedTuple):
    """Static (compile-time) switches."""
    n: int
    B: int
    D: int
    reset_syn: bool
    adapt: bool
    std: bool
    spont: bool
    mod: bool
    ch_vdep: tuple  # slow channels (GABA-B, mGluR, mAChR, NMDA as present): Mg-blocked?
    noise_class: bool
    mg357: float    # NMDA block constant [Mg]/3.57, float32 as in lif.py
    elec: bool
    noise: float
    dt: float
    graded_scale: float
    mod_increment: float
    tiers: tuple    # event-path capacities ((K, E), ...) ascending: K active presynaptic
                    # cells (any member), E expanded edges; () = dense every step
    ich: tuple = ()  # rung-1 intrinsic channels present (channels.Intrinsic.on order)
    cond: bool = False   # s11 rung 2: conductance synapses (edge column 1 = inhibitory)
    e_exc: float = 0.0
    e_inh: float = -70.0


def _f32(x, n):
    a = np.asarray(x, np.float32)
    return np.full(n, a, np.float32) if a.ndim == 0 else a.astype(np.float32)


class BatchedNetwork:
    """B variants of one reference `lif.Network` (its connectome and parameters).

    `member` maps names in MEMBER_PARAMS to per-member values: a (B, n) array,
    an (n,) array or a scalar shared by all members. Values are absolute (same
    meaning as the LIFParams field); omitted names take the reference network's
    values. Arrays are stored neuron-major, shape (n, B) or (n, 1) if shared.
    """

    def __init__(self, net: lif.Network, B: int = 1, member: dict | None = None,
                 seed: int = 0, tiers=None) -> None:
        p = net.params
        if net.w_pi is not None:
            raise NotImplementedError("presynaptic inhibition (presyn_inh_gain > 0) is not ported")
        if net.kc_edge is not None:
            raise NotImplementedError("KC->MBON plasticity (kc_mbon_eta > 0) is not ported")
        # session-10 mechanisms added after the port (main session): refuse, never ignore
        if getattr(net, "ring_e", None) is not None:
            raise NotImplementedError("N24 ER->EPG plasticity is not ported")
        if getattr(net, "glia_k", None) is not None:
            raise NotImplementedError("N27 lumped glia is not ported")
        if getattr(net, "apl_mask", None) is not None:
            raise NotImplementedError("N23 compartmental APL is not ported")
        ich = getattr(net, "ich", None)
        if ich is not None and "v_rest" in (member or {}) and not np.array_equal(
                np.broadcast_to(np.asarray(member["v_rest"], np.float32), (B, net.conn.n)),
                np.broadcast_to(np.asarray(net.v_rest, np.float32), (B, net.conn.n))):
            raise NotImplementedError("per-member v_rest with rung-1 channels (gate rest "
                                      "states are set from the reference v_rest)")
        n = net.conn.n
        self.net, self.n, self.B = net, n, B
        self.dt = float(net.timestep_ms)
        self.member = {k: np.asarray(v) for k, v in (member or {}).items()}
        bad = set(self.member) - set(MEMBER_PARAMS)
        if bad:
            raise ValueError(f"not per-member parameters: {sorted(bad)}")

        # --- edges: spiking rows from net.w, graded rows from net.W_graded ---
        counts = np.diff(net.conn.indptr).astype(np.int64)
        pre0 = np.repeat(np.arange(n), counts)
        post0 = np.asarray(net.conn.indices, np.int64)
        # one edge list; column 0 the fast weight, then one column per slow channel,
        # in lif.py's drive order: GABA-B (w_slow), then net.chan (mGluR, mAChR, NMDA)
        chans = []                                     # (weights per conn edge, decay, vdep)
        if net.w_slow is not None:
            chans.append((net.w_slow, np.float32(net.decay_slow), False))
        for ch in getattr(net, "chan", []):
            chans.append((ch["w"], np.float32(ch["decay"]), bool(ch["vdep"])))
        cond = bool(p.cond)
        if cond:   # lif.py splits by sign: excitatory into delay, -w into delay_i
            cols = [np.where(net.w > 0, net.w, 0).astype(np.float32),
                    np.where(net.w < 0, -net.w, 0).astype(np.float32)] + [w_ for w_, _, _ in chans]
        else:
            cols = [net.w] + [w_ for w_, _, _ in chans]
        pre, post = pre0, post0
        gmats = []
        if net.W_graded is not None:   # (n_post, n_graded); graded cells have no slow channels
            gmats.append((0, net.W_graded.tocoo()))
            if cond and getattr(net, "W_graded_i", None) is not None:
                gmats.append((1, net.W_graded_i.tocoo()))
        for col, g in gmats:
            pre = np.concatenate([pre, net.g_idx[g.col]])
            post = np.concatenate([post, g.row.astype(np.int64)])
            cols = [np.concatenate([x, g.data.astype(np.float32) if k == col
                                    else np.zeros(g.nnz, np.float32)]) for k, x in enumerate(cols)]
        W = np.stack(cols, 1).astype(np.float32)       # (edges, 1 + n_channels)
        keep = np.any(W != 0, axis=1)
        pre, post, W = pre[keep], post[keep], W[keep]
        o = np.lexsort((pre, post))            # target-major: dense segment sum
        self.n_edges = int(o.size)
        e_pre, e_post, e_w = pre[o].astype(np.int32), post[o].astype(np.int32), W[o]
        q = np.lexsort((post, pre))            # source-major: event-driven expansion
        rowlen = np.bincount(pre, minlength=n)
        p_indptr = np.zeros(n + 1, np.int64)
        np.cumsum(rowlen, out=p_indptr[1:])
        p_w = W[q]

        graded = np.asarray(net.graded, bool)
        dly = np.where(graded, 1, net.delay_steps).astype(np.int32)
        D = int(max(net.D, 1))

        # --- per-neuron parameters (reference values, then member overrides) ---
        ref = {"release_gain": _f32(p.release_gain, n), "input_gain": net.input_gain,
               "spont_mv": net.spont, "v_rest": net.v_rest, "v_th": net.v_th,
               "v_reset": net.v_reset, "tau_m": net.tau_m, "t_ref": net.t_ref,
               "tau_s": _f32(p.tau_s, n), "adapt_mv": net.adapt_mv,
               "tau_adapt": _f32(p.tau_adapt, n), "std_u": net.std_u,
               "std_tau_rec": _f32(p.std_tau_rec, n)}
        val = {}
        for k in MEMBER_PARAMS:
            if k in self.member:
                v = self.member[k].astype(np.float32)
                if v.ndim == 2:
                    if v.shape != (B, n):
                        raise ValueError(f"{k}: expected ({B}, {n}), got {v.shape}")
                    v = v.T
                else:
                    v = np.broadcast_to(v, (n,))[:, None]
                val[k] = np.ascontiguousarray(v)
            else:
                val[k] = ref[k][:, None]
        dt = self.dt
        # derived constants: the same float32 expressions as lif.Network.__post_init__
        dv = np.exp(-dt / val["tau_m"]).astype(np.float32)
        rel_ref, inp_ref = ref["release_gain"][:, None], ref["input_gain"][:, None]

        def ratio(new, base, name):
            if np.any((base == 0) & (new != 0)):
                raise ValueError(f"{name}: the reference network has 0 where a member is "
                                 "nonzero; build the reference with nonzero gains")
            return np.where(base == 0, np.float32(1), new / np.where(base == 0, 1, base)
                            ).astype(np.float32)

        mod_release = np.asarray(net.mod_release, np.int32)
        self.cfg = Cfg(
            n=n, B=B, D=D, reset_syn=bool(p.reset_syn),
            adapt=bool(np.any(val["adapt_mv"])), std=bool(np.any(val["std_u"])),
            spont=bool(np.any(val["spont_mv"])), mod=bool(net._mod_active),
            ch_vdep=tuple(v for _, _, v in chans),
            noise_class=getattr(p, "noise_class_mv", None) is not None,
            mg357=float(np.float32(getattr(p, "nmda_mg_mM", 1.0) / 3.57)),
            tiers=tuple((int(k), int(e)) for k, e in (DEFAULT_TIERS if tiers is None else tiers)),
            elec=net.elec is not None and len(net.elec[0]) > 0,
            noise=float(p.noise_mv), dt=dt,
            graded_scale=float(p.graded_rmax_hz * dt / 1000.0),
            mod_increment=float(p.mod_increment),
            ich=() if ich is None else tuple(ich.on),
            cond=cond, e_exc=float(p.e_exc), e_inh=float(p.e_inh))
        c = dict(
            e_pre=e_pre, e_post=e_post, e_w=e_w, dly=dly, graded=graded,
            p_indptr=p_indptr.astype(np.int32), p_rowlen=rowlen.astype(np.int32),
            p_post=post[q].astype(np.int32), p_w=p_w,
            v_rest=val["v_rest"], v_th=val["v_th"], v_reset=val["v_reset"], t_ref=val["t_ref"],
            decay_v=dv, one_minus_dv=(1.0 - dv).astype(np.float32),
            decay_s=np.exp(-dt / val["tau_s"]).astype(np.float32),
            decay_a=np.exp(-dt / val["tau_adapt"]).astype(np.float32),
            rec_step=(1.0 - np.exp(-dt / val["std_tau_rec"])).astype(np.float32),
            adapt_mv=val["adapt_mv"], std_u=val["std_u"], spont=val["spont_mv"],
            rel=ratio(val["release_gain"], rel_ref, "release_gain"),
            inp=ratio(val["input_gain"], inp_ref, "input_gain"),
            mod_sens=np.asarray(net.mod_sens, np.float32),
            mod_cells=np.flatnonzero(mod_release >= 0).astype(np.int32),
            mod_of=mod_release[mod_release >= 0].astype(np.int32),
            mod_decay=np.float32(net.mod_decay),
        )
        if chans:
            c.update(ch_decay=np.array([d for _, d, _ in chans], np.float32))
        if cond:
            c.update(decay_si=np.asarray(net.decay_si, np.float32)[:, None])
        if cond or ich is not None:
            c.update(tau_m=val["tau_m"])
        if ich is not None:   # rung 1: the reference network's initialised Intrinsic
            c.update(ca_per_spike=np.asarray(ich.ca_per_spike, np.float32)[:, None],
                     ich_d=np.array([ich.d[k] for k in _GATES] + [ich.d_kv2, ich.d_bk, ich.d_ca],
                                    np.float32))
            for ch in ich.on:
                c[f"g_{ch}"] = np.asarray(ich.g[ch], np.float32)[:, None]
                c[f"xr_{ch}"] = np.asarray(ich.x_r[ch], np.float32)[:, None]
            vr = np.asarray(net.v_rest, np.float32)   # gates at rest, as Intrinsic.init
            self._ich0 = {k: ichan._boltz(vr, *ichan.KINETICS[g][:2]).astype(np.float32)
                          for k, g in zip(("a", "b", "w", "hh", "th"), _GATES)}
        if self.cfg.noise_class:
            c.update(noise_class=(np.asarray(p.noise_class_mv, np.float32)
                                  * np.float32(np.sqrt(dt)))[:, None])
        if self.cfg.elec:
            ep, eq, ev = net.elec
            c.update(el_pre=np.asarray(ep, np.int32), el_post=np.asarray(eq, np.int32),
                     el_mv=np.asarray(ev, np.float32))
        self.c = {k: jnp.asarray(v) for k, v in c.items()}
        self.key = jax.random.PRNGKey(seed)
        self.reset()
        self._run = jax.jit(partial(_run, self.cfg), static_argnames=("rec_mode",))

    # --- state ---------------------------------------------------------------

    def reset(self) -> None:
        """Physiological initialisation, as lif.Network: every neuron at rest."""
        n, B, D = self.n, self.B, self.cfg.D
        z = jnp.zeros((n, B), jnp.float32)
        self.t_ms = 0.0
        self.state = dict(
            k=jnp.int32(0), H=jnp.zeros((D, n, B), jnp.float32),
            v=jnp.broadcast_to(self.c["v_rest"], (n, B)).astype(jnp.float32),
            i_syn=z, ref_until=z, kick_held=z, adapt=z, x_res=jnp.ones((n, B), jnp.float32),
            g_i=z, i_ch=tuple(z for _ in self.cfg.ch_vdep), mod_level=jnp.zeros((3, B), jnp.float32),
            counts=jnp.zeros((n, B), jnp.int32), key=self.key,
            ich={} if not self.cfg.ich else dict(
                **{k: jnp.broadcast_to(jnp.asarray(v, jnp.float32)[:, None], (n, B))
                   for k, v in self._ich0.items()},
                n_kv2=z, n_bk=z, ca=z))

    def silence(self, idx, members=None) -> None:
        """Remove all output of these neurons (all members, or the listed ones),
        permanently, as lif.Network.silence (release factor set to 0)."""
        m = np.array(np.broadcast_to(np.asarray(self.c["rel"]), (self.n, self.B)))
        cols = slice(None) if members is None else np.asarray(members)
        m[np.asarray(idx)[:, None], cols] = 0.0
        self.c["rel"] = jnp.asarray(m)

    def spike_counts(self) -> np.ndarray:
        """(B, n) spikes since reset."""
        return np.asarray(self.state["counts"]).T

    def _times(self, T: int) -> np.ndarray:
        # lif.py accumulates t_ms as a Python float and compares it as float32
        t = np.empty(T, np.float32)
        for s in range(T):
            t[s] = np.float32(self.t_ms)
            self.t_ms += self.dt
        return t

    # --- running -------------------------------------------------------------

    def run(self, T: int, external_mv=None, kicks=None, record=None,
            ext_rows=None) -> dict:
        """Advance T steps.

        external_mv: None, (n,), or (B, n); held constant over the T steps.
            With ext_rows (m,) given: (m,) or (B, m) values for those rows only
            (the closed-loop form: only sensory rows cross the bus; docs/GPU.md).
        kicks: None or (idx (k,), mask, mv): idx unique neuron indices; mask a
            (T, k) or (T, B, k) bool schedule of which get a `mv` kick at each
            step (Shiu-style Poisson input; lif.Network.step(kick=...)).
            Or (idx, rate_hz, mv), rate_hz scalar or (k,): Poisson kicks drawn on
            device, independently per member (statistical equivalence only).
        record: None; 'packed' for the full raster, (T, ceil(n/8), B) uint8 packed
            along neurons; or an index array for a per-step (T, B, r) bool raster.
        Returns dict with 'n_spikes' (T, B) and optionally 'raster'.
        """
        n, B = self.n, self.B
        if external_mv is None:
            ext = jnp.zeros((n, 1), jnp.float32)
        elif ext_rows is not None:
            rows = np.asarray(ext_rows, np.int32)
            vals = np.asarray(external_mv, np.float32).reshape(-1, rows.size).T   # (m, 1|B)
            ext = _scatter_rows(jnp.asarray(rows), jnp.asarray(vals), n)
        else:
            ext = jnp.asarray(np.asarray(external_mv, np.float32).reshape(-1, n).T)
        t32 = jnp.asarray(self._times(T))
        kidx, kmask, kmv, krate = jnp.zeros(0, jnp.int32), None, 0.0, None
        if kicks is not None:
            idx, sched, kmv = kicks
            idx = np.asarray(idx, np.int32)
            if np.unique(idx).size != idx.size:
                raise ValueError("kick indices must be unique")
            kidx = jnp.asarray(idx)
            sched = np.asarray(sched)
            if sched.ndim <= 1:        # Poisson rate(s) in Hz, scalar or per kicked cell
                krate = jnp.asarray(np.broadcast_to(sched.astype(np.float32) * np.float32(
                    self.dt / 1000.0), (idx.size,))[:, None])
            else:
                if sched.ndim == 2:
                    sched = np.broadcast_to(sched[:, None, :], (T, B, idx.size))
                kmask = jnp.asarray(np.ascontiguousarray(np.swapaxes(sched, 1, 2)), jnp.bool_)
        if kmask is None:
            kmask = jnp.zeros((T, 0, 0), jnp.bool_)
        rec_mode, rec_idx = "none", jnp.zeros(0, jnp.int32)
        if isinstance(record, str) and record == "packed":
            rec_mode = "packed"
        elif record is not None:
            rec_mode, rec_idx = "idx", jnp.asarray(np.asarray(record, np.int32))
        self.state, out = self._run(self.c, self.state, t32, ext, kidx, kmask,
                                    jnp.float32(kmv), krate if krate is not None else jnp.zeros((0, 1), jnp.float32),
                                    rec_idx, rec_mode=rec_mode)
        res = {"n_spikes": np.asarray(out[0])}
        if rec_mode != "none":
            res["raster"] = np.asarray(out[1])
        return res

    def step(self, external_mv=None, kick=None) -> np.ndarray:
        """One step, lif.Network.step-compatible inputs; returns (B, n) bool spikes.
        Slow per step (one dispatch): use run() for throughput."""
        kicks = None
        if kick is not None and len(kick[0]):
            kicks = (np.asarray(kick[0]), np.ones((1, len(kick[0])), bool), float(kick[1]))
        r = self.run(1, external_mv=external_mv, kicks=kicks, record="packed")
        return np.unpackbits(r["raster"][0], axis=0, count=self.n).astype(bool).T


@partial(jax.jit, static_argnums=2)
def _scatter_rows(rows, vals, n):
    return jnp.zeros((n, vals.shape[1]), jnp.float32).at[rows].set(vals)


def _dense_input(cfg: Cfg, c: dict, z):
    """All edges every step: sorted segment sum over targets."""
    zz = z[c["e_pre"]]
    seg = lambda k: jax.ops.segment_sum(c["e_w"][:, k, None] * zz, c["e_post"],
                                        num_segments=cfg.n, indices_are_sorted=True)
    return tuple(seg(k) for k in range(1 + cfg.cond + len(cfg.ch_vdep)))


def _event_input(cfg: Cfg, c: dict, z, act, nnz, total, K: int, E: int):
    """Only the outgoing edges of presynaptic cells with a nonzero output in any
    member (spikes, depolarised graded cells), expanded once for all members.
    Requires nnz <= K active cells and total <= E edges."""
    pre = jnp.nonzero(act, size=K, fill_value=0)[0]
    L = jnp.where(jnp.arange(K) < nnz, c["p_rowlen"][pre], 0)
    start = jnp.cumsum(L) - L
    # edge e belongs to active cell j(e): mark each cell's first edge, running max
    mark = jnp.zeros(E, jnp.int32).at[jnp.where(L > 0, start, E)].max(
        jnp.arange(K, dtype=jnp.int32), mode="drop")
    j = jax.lax.cummax(mark)
    e = jnp.arange(E, dtype=jnp.int32)
    ok = e < total
    edge = jnp.where(ok, c["p_indptr"][pre[j]] + e - start[j], 0)
    zj = jnp.where(ok[:, None], z[pre[j]], 0.0)                     # (E, B)
    tgt = c["p_post"][edge]

    def add(k):
        return jnp.zeros_like(z).at[tgt].add(c["p_w"][edge, k][:, None] * zj)
    return tuple(add(k) for k in range(1 + cfg.cond + len(cfg.ch_vdep)))


def _input(cfg: Cfg, c: dict, z):
    """Arriving input: the smallest event-path tier that holds this step's active
    cells and edges, else the dense product (identical semantics)."""
    if not cfg.tiers:
        return _dense_input(cfg, c, z)
    act = jnp.any(z != 0, axis=1)
    nnz = jnp.count_nonzero(act)
    total = jnp.sum(jnp.where(act, c["p_rowlen"], 0))
    fits = [(nnz <= K) & (total <= E) for K, E in cfg.tiers]
    idx = len(cfg.tiers) - jnp.sum(jnp.stack(fits).astype(jnp.int32))  # tiers ascend
    branches = [partial(_event_input, cfg, c, z, act, nnz, total, K, E) for K, E in cfg.tiers]
    branches.append(lambda: _dense_input(cfg, c, z))
    return jax.lax.switch(idx, branches)


def _step(cfg: Cfg, c: dict, s: dict, t32, ext, kick):
    n = cfg.n
    D = cfg.D
    k = s["k"]
    # arriving input: per presynaptic cell, its output from its own delay ago
    slot = (k - c["dly"]) % D
    z = s["H"][slot, jnp.arange(n)]                                  # (n, B)
    arr, *a_ch = _input(cfg, c, z)
    if cfg.cond:
        arr_i, *a_ch = a_ch
        arr_i = arr_i * c["inp"]
    arr = arr * c["inp"]
    if cfg.mod:
        gain = 1.0 + (c["mod_sens"][:, 0:1] * s["mod_level"][0] + c["mod_sens"][:, 1:2]
                      * s["mod_level"][1] + c["mod_sens"][:, 2:3] * s["mod_level"][2])
        arr = arr * gain
        if cfg.cond:
            arr_i = arr_i * gain
    i_syn = s["i_syn"] * c["decay_s"] + arr
    g_i = s["g_i"]
    if cfg.cond:
        g_i = g_i * c["decay_si"] + arr_i
    drive = i_syn
    i_ch = []
    for ci, vdep in enumerate(cfg.ch_vdep):
        ik = s["i_ch"][ci] * c["ch_decay"][ci] + a_ch[ci] * c["inp"]
        i_ch.append(ik)
        if vdep:   # NMDA-type Mg block at the membrane potential before this update
            blk = 1.0 / (1.0 + jnp.float32(cfg.mg357) * jnp.exp(jnp.float32(-0.062) * s["v"]))
            drive = drive + ik * blk
        else:
            drive = drive + ik
    drive = drive + ext
    if cfg.spont:
        drive = drive + c["spont"]
    adapt = s["adapt"]
    if cfg.adapt:
        adapt = adapt * c["decay_a"]
        drive = drive - adapt
    v_rest = c["v_rest"]
    gates = s["ich"]
    if cfg.cond:   # rung 2: conductance synapses (lif.py p.cond), exponential Euler
        G = 1.0 + i_syn + g_i
        num = v_rest + (drive - i_syn) + i_syn * jnp.float32(cfg.e_exc) + g_i * jnp.float32(cfg.e_inh)
        if cfg.ich:
            gates, dG, dGE = _ich_step(cfg, c, gates, s["v"])
            G, num = G + dG, num + dGE
        v_inf = num / G
        v = v_inf + (s["v"] - v_inf) * jnp.exp(-jnp.float32(cfg.dt) * G / c["tau_m"])
    elif cfg.ich:   # rung 1: leak + intrinsic conductances, exponential Euler (lif.py)
        gates, dG, dGE = _ich_step(cfg, c, gates, s["v"])
        G = 1.0 + dG
        v_inf = (v_rest + drive + dGE) / G
        v = v_inf + (s["v"] - v_inf) * jnp.exp(-jnp.float32(cfg.dt) * G / c["tau_m"])
    else:
        v = v_rest + (s["v"] - v_rest) * c["decay_v"] + drive * c["one_minus_dv"]
    key = s["key"]
    if cfg.noise:
        key, sub = jax.random.split(key)
        v = v + jax.random.normal(sub, v.shape, jnp.float32) * jnp.float32(
            cfg.noise * np.sqrt(cfg.dt))
    if cfg.noise_class:
        key, sub = jax.random.split(key)
        v = v + jax.random.normal(sub, v.shape, jnp.float32) * c["noise_class"]
    free = t32 >= s["ref_until"]
    v = jnp.where(free, v, c["v_reset"])
    kick_held = s["kick_held"]
    if kick is not None:
        kick_held = kick_held.at[kick[0]].add(kick[1])
    land = free & (kick_held > 0)
    v = jnp.where(land, v + kick_held, v)
    kick_held = jnp.where(land, 0.0, kick_held)
    graded = c["graded"][:, None]
    spk = free & ~graded & (v >= c["v_th"])
    vth = c["v_th"]
    den = jnp.where(graded, vth - v_rest, 1.0)
    y_g = jnp.clip((v - v_rest) / den, 0.0, 1.0) * jnp.float32(cfg.graded_scale)
    x_res = s["x_res"]
    if cfg.std:
        x_res = x_res + (1.0 - x_res) * c["rec_step"]
    mod_level = s["mod_level"]
    if cfg.mod:
        mod_level = mod_level * c["mod_decay"]
    v = jnp.where(spk, c["v_reset"], v)
    if cfg.reset_syn:
        i_syn = jnp.where(spk, 0.0, i_syn)
        if cfg.cond:
            g_i = jnp.where(spk, 0.0, g_i)
    if cfg.adapt:
        adapt = adapt + jnp.where(spk, c["adapt_mv"], 0.0)
    if cfg.mod:
        cnt = jax.ops.segment_sum(spk[c["mod_cells"]].astype(jnp.float32), c["mod_of"],
                                  num_segments=3)
        mod_level = mod_level + cnt * jnp.float32(cfg.mod_increment)
    if cfg.elec:
        kick_held = kick_held + jax.ops.segment_sum(
            spk[c["el_pre"]] * c["el_mv"][:, None], c["el_post"], num_segments=n)
    if cfg.ich:   # channels.Intrinsic.on_spike
        K = ichan.KINETICS
        gates = dict(gates,
                     n_kv2=jnp.where(spk, gates["n_kv2"] + (1.0 - gates["n_kv2"]) * jnp.float32(K["Kv2"][0]),
                                     gates["n_kv2"]),
                     n_bk=jnp.where(spk, gates["n_bk"] + (1.0 - gates["n_bk"]) * jnp.float32(K["BK"][0]),
                                    gates["n_bk"]),
                     ca=jnp.where(spk, gates["ca"] + c["ca_per_spike"], gates["ca"]))
    ref_until = jnp.where(spk, t32 + c["t_ref"], s["ref_until"])
    y_s = spk.astype(jnp.float32)
    if cfg.std:
        y_s = y_s * x_res
        x_res = jnp.where(spk, x_res * (1.0 - c["std_u"]), x_res)
    y = jnp.where(graded, y_g, y_s) * c["rel"]
    H = s["H"].at[k % D].set(y)
    ns = dict(k=k + 1, H=H, v=v, i_syn=i_syn, g_i=g_i, ref_until=ref_until, kick_held=kick_held,
              adapt=adapt, x_res=x_res, i_ch=tuple(i_ch), mod_level=mod_level,
              counts=s["counts"] + spk, key=key, ich=gates)
    return ns, spk


_GATES = ("A_act", "A_inact", "M_act", "h_act", "T_inact")


def _boltz(v, vh, k):
    return 1.0 / (1.0 + jnp.exp(-(v - jnp.float32(vh)) / jnp.float32(k)))


def _ich_step(cfg: Cfg, c: dict, g: dict, v):
    """channels.Intrinsic.step on device: advance gates at v (pre-update), return
    (gates, dG, dGE), the conductance change from rest and its reversal-weighted sum."""
    K, d = ichan.KINETICS, c["ich_d"]

    def relax(x, i, key):
        inf = _boltz(v, *K[key][:2])
        return inf + (x - inf) * d[i]

    a, b = relax(g["a"], 0, "A_act"), relax(g["b"], 1, "A_inact")
    w, hh, th = relax(g["w"], 2, "M_act"), relax(g["hh"], 3, "h_act"), relax(g["th"], 4, "T_inact")
    n_kv2, n_bk, ca = g["n_kv2"] * d[5], g["n_bk"] * d[6], g["ca"] * d[7]
    x = {"A": lambda: a ** 3 * b, "M": lambda: w, "h": lambda: hh,
         "T": lambda: _boltz(v, *K["T_act"][:2]) ** 2 * th, "NaP": lambda: _boltz(v, *K["NaP_act"][:2]),
         "Kv2": lambda: n_kv2, "BK": lambda: n_bk, "SK": lambda: ca / (ca + jnp.float32(K["SK_kd"]))}
    dG = jnp.zeros_like(v)
    dGE = jnp.zeros_like(v)
    for ch in cfg.ich:
        gx = c[f"g_{ch}"] * (x[ch]() - c[f"xr_{ch}"])
        dG = dG + gx
        dGE = dGE + gx * jnp.float32(ichan.CHANNELS[ch][1])
    return dict(a=a, b=b, w=w, hh=hh, th=th, n_kv2=n_kv2, n_bk=n_bk, ca=ca), dG, dGE


def _run(cfg: Cfg, c, state, t32, ext, kidx, kmask, kmv, krate, rec_idx, *, rec_mode):
    n, B = cfg.n, cfg.B
    has_mask = kmask.shape[1] > 0
    has_kicks = kidx.shape[0] > 0

    def body(s, xs):
        t, km = xs
        kick = None
        if has_kicks:
            if has_mask:
                m = km
            else:
                key, sub = jax.random.split(s["key"])
                s = {**s, "key": key}
                m = jax.random.uniform(sub, (kidx.shape[0], B)) < krate
            kick = (kidx, jnp.where(m, kmv, 0.0))
        s, spk = _step(cfg, c, s, t, ext, kick)
        out = spk.sum(0, dtype=jnp.int32)
        if rec_mode == "packed":
            return s, (out, jnp.packbits(spk, axis=0))
        if rec_mode == "idx":
            return s, (out, spk[rec_idx].T)
        return s, (out,)

    xs = (t32, kmask if has_mask else jnp.zeros((t32.shape[0], 0, B), jnp.bool_))
    return jax.lax.scan(body, state, xs)
