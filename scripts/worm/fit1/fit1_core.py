"""Fit 1 core (docs/worm/FIT1.md): class-level synapse strengths against Randi et al. 2023's signal propagation
atlas. The parameter table and its bounded transforms, the fitted values put into the worm's spec (the same path a
ledger value takes), and one simulated stimulation experiment.

One experiment = one worm (a parameter vector): the 302 neurons (no neuron-muscle gap or chemical pair exists, so
neuronal responses are exact without the muscles), warmed up, then one forked child per stimulated neuron and one
control child with no light, all continuing from the same state. A child switches on the GUR-3 actuator
(mech.observation, B3's) in its target for the pulse and runs the response window. Readout: the soma Ca pool
computed from each soma's own Ca current with Nicoletti 2019's equation in total current (cainternm.mod divides the
density, mA/cm2, by the cell volume, so its pool rises 10 x area too little: night file, Open), then GCaMP6s binding
(observation.binding_step) and F = 1 + (R - 1) B, sampled at Randi's 2 volumes/s. The statistic is Randi's: the mean
dF/F over the window after the onset, with F0 taken from the control child at the same times (removes the drift a
30 s pre-stimulus baseline would remove in the data).

The integration step (h_dt) and the mechanism step (mech_dt) are arguments; the reference path is brain.py's own
(0.5 ms, mechanisms every 1 ms), checked against the fit's choice in step 4 of the night file.
"""
from __future__ import annotations

import os
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd

from wormemu import brain as wb
from wormemu import mech
from wormemu.brain import Brain, load_structure, sample_worm
from wormemu.mech import observation as obs
from wormemu.mech import receptors

FARADAY = 96485.0                     # cainternm.mod's CONSTANT
VOL_S = 0.5                           # Randi: 2 volumes/s

# the fitted values: (id, transform). Bounds and template come from the ledger row, else the module's Spec.
# Not fitted, with reasons (FIT1.md): rec_lacr_gamma_pS (the per-contact strength's reference: it cancels),
# lgc55 (6 sites, 0.55 nS in all), the monoamine and betaine tmax (degenerate with their classes' gamma at so few
# sites), every kinetic constant, gap_innexin_unitary (only its product with the open-channel count enters).
FIT = ([("syn_strength_per_pair", "log")]
       + [(f"rec_{c}_gamma_pS", "log") for c in ("acr16", "nachr", "acc", "glr", "nmr", "glucl", "gabacl",
                                                  "gabacat", "mod1", "lgc53", "acr23")]
       + [(f"rec_tmax_{lg}_uM", "log") for lg in ("acetylcholine", "glutamate", "gaba")]
       + [("syn_exc_Vth", "lin"), ("syn_exc_delta", "log"), ("gap_open_channels_per_em", "log"),
          ("obs_opto_g_nS", "log"), ("obs_opto_tau_off_ms", "log"), ("obs_gcamp6s_thalf_ms", "log")])
IDS = [i for i, _ in FIT]


def bounds(spec=None):
    """{id: (template, lo, hi, label, transform)} for the fitted values."""
    spec = spec or sample_worm(None)
    P = spec.led.parameters.set_index("param_id")
    mods = {s.id: s for m in (receptors, obs) for s in m.SPECS}
    out = {}
    for pid, tr in FIT:
        if pid in P.index:
            r = P.loc[pid]
            v = spec.values[pid]
            t = float(v.median()) if isinstance(v, pd.Series) else float(v)
            out[pid] = (t, float(r.bio_min), float(r.bio_max), str(r.label), tr)
        else:
            s = mods[pid]
            out[pid] = (float(s.template), float(s.lo), float(s.hi), s.label, tr)
    return out


def to_values(x, B):
    """Unbounded x (one per FIT id) -> values inside [lo, hi] (a sigmoid; on log scale for 'log')."""
    u = 1.0 / (1.0 + np.exp(-np.asarray(x, float)))
    out = {}
    for k, pid in enumerate(IDS):
        t, lo, hi, _, tr = B[pid]
        out[pid] = float(np.exp(np.log(lo) + u[k] * (np.log(hi) - np.log(lo)))) if tr == "log" \
            else float(lo + u[k] * (hi - lo))
    return out


def to_x(vals, B, clip=0.02):
    x = []
    for pid in IDS:
        t, lo, hi, _, tr = B[pid]
        v = vals[pid]
        u = (np.log(v) - np.log(lo)) / (np.log(hi) - np.log(lo)) if tr == "log" else (v - lo) / (hi - lo)
        u = float(np.clip(u, clip, 1 - clip))
        x.append(np.log(u / (1 - u)))
    return np.array(x)


def make_spec(vals):
    """The template worm with the fitted values in place (a table row: every element gets the one value)."""
    spec = sample_worm(None)
    for pid, v in vals.items():
        cur = spec.values.get(pid)
        spec.values[pid] = pd.Series(float(v), index=cur.index) if isinstance(cur, pd.Series) else float(v)
    return spec


class FitBrain(Brain):
    """Brain with the wiring recorded (and, for the wrong model, shuffled) before the mechanisms are built."""
    shuffle_seed = None

    def _wire_cook(self):
        self._site = []                                  # per wsyn: (pre_seg, post_seg)
        self._gaps = []                                  # per junction: (pp at a, pp at b, seg_a, seg_b, rect)
        super()._wire_cook()
        if self.shuffle_seed is not None:
            self.shuffle_info = shuffle_wiring(self, self.shuffle_seed)

    def _wsyn(self, pre_seg, post_seg, *a, **k):
        super()._wsyn(pre_seg, post_seg, *a, **k)
        self._site.append((pre_seg, post_seg))

    def _gap(self, seg_a, seg_b, g_uS, kind, into=None, ratio=1.0):
        n0 = len(self.conn)
        super()._gap(seg_a, seg_b, g_uS, kind, into=into, ratio=ratio)
        if hasattr(self, "_gaps"):
            self._gaps.append((self.conn[n0], self.conn[n0 + 1], seg_a, seg_b, into is not None))


def _cell_of(b):
    m = {}
    for i, segs in enumerate(b.segs):
        for seg, _ in segs:
            m[seg.sec.name()] = i
    return m


def shuffle_wiring(b, seed, swaps_per_edge=10):
    """The wrong model: a degree-preserving rewiring. Chemical: every site keeps its postsynaptic segment, receptor
    classes and conductance; double-edge swaps exchange presynaptic partners (with their presynaptic segments)
    between two sites whose senders have the same fast-transmitter set, so each cell keeps its numbers of input and
    output sites and its classes stay those of a sender of that transmitter. Gap junctions (non-rectifying): swaps
    exchange partner halves (a-b, c-d -> a-d, c-b), both halves of a new junction taking the weight of the old
    junction on its first side, so each cell keeps its number of junction sites. Self-connections are refused."""
    rng = np.random.default_rng(seed)
    h, st = b.h, b.st
    cell = _cell_of(b)
    # chemical sites: group the wsyn point processes by (pre seg, post seg)
    key = {}
    for k, ((ps, qs), (pp, i, j, c)) in enumerate(zip(b._site, b.wsyn)):
        key.setdefault((ps.sec.name(), ps.x, qs.sec.name(), qs.x, i, j), []).append(k)
    sites = [(kk[4], kk[5], b._site[v[0]][0], v) for kk, v in key.items()]   # (pre, post, pre_seg, [wsyn k])
    groups = {}
    for s, (i, j, _, _) in enumerate(sites):
        tr = tuple(lg for lg in receptors.LIGANDS if lg in st.transmitter.get(b.cell_names[i], set()))
        groups.setdefault(tr, []).append(s)
    pre = np.array([s[0] for s in sites])
    pseg = [s[2] for s in sites]
    post = np.array([s[1] for s in sites])
    done = 0
    for tr, ss in groups.items():
        ss = np.array(ss)
        if len(ss) < 2:
            continue
        for _ in range(swaps_per_edge * len(ss)):
            s1, s2 = rng.choice(ss, 2, replace=False)
            if pre[s1] == pre[s2] or pre[s2] == post[s1] or pre[s1] == post[s2]:
                continue
            pre[s1], pre[s2] = pre[s2], pre[s1]
            pseg[s1], pseg[s2] = pseg[s2], pseg[s1]
            done += 1
    moved = 0
    for s, (i, j, ps0, ks) in enumerate(sites):
        if pre[s] == i:
            continue
        moved += 1
        for k in ks:
            pp, _, jj, c = b.wsyn[k]
            h.setpointer(pseg[s]._ref_v, "vpre", pp)
            b.wsyn[k] = (pp, int(pre[s]), jj, c)
    # gap junctions
    G = [g for g in b._gaps if not g[4]]
    ga = np.array([cell[g[2].sec.name()] for g in G])
    gb = np.array([cell[g[3].sec.name()] for g in G])
    seg_b = [g[3] for g in G]
    pp_b = [g[1] for g in G]
    gdone = 0
    for _ in range(swaps_per_edge * len(G)):
        k1, k2 = rng.choice(len(G), 2, replace=False)
        if ga[k1] == gb[k2] or ga[k2] == gb[k1] or gb[k1] == gb[k2]:
            continue
        gb[k1], gb[k2] = gb[k2], gb[k1]
        seg_b[k1], seg_b[k2] = seg_b[k2], seg_b[k1]
        pp_b[k1], pp_b[k2] = pp_b[k2], pp_b[k1]
        gdone += 1
    gmoved = 0
    for k, (pa, pb0, sa, sb0, _) in enumerate(G):
        if pp_b[k] is pb0:
            continue
        gmoved += 1
        pb = pp_b[k]
        h.setpointer(seg_b[k]._ref_v, "vpre", pa)        # a's half now sees the new partner
        h.setpointer(sa._ref_v, "vpre", pb)              # the partner's half sees a
        pb.weight = pa.weight
    return dict(chem_sites=len(sites), chem_swaps=done, chem_moved=moved, gap_junctions=len(G), gap_swaps=gdone,
                gap_moved=gmoved, gap_rect_kept=len(b._gaps) - len(G))


def neurons():
    st = load_structure()
    return [n for n, k in zip(st.names, st.kind) if k == "neuron"]


class Experiment:
    """One worm, built once; run(targets) gives the model's statistic for each stimulated target."""

    def __init__(self, vals, targets, toggles=None, shuffle_seed=None, h_dt=0.5, mech_dt=10.0, cells=None,
                 warm_s=5.0):
        if "observation" not in mech.REGISTRY:
            mech.REGISTRY.append("observation")
        wb.DT_MS = float(h_dt)                           # brain.py reads its module step at build and per step
        self.mech_dt, self.warm_s = float(mech_dt), float(warm_s)
        self.vals = dict(vals)
        cells = cells or neurons()
        self.targets = [t for t in targets if t in cells]
        obs.SCHEDULE[:] = [(c, 1e15, 1.0, 0.0) for c in self.targets]    # actuators exist, never lit
        t0 = time.time()
        FitBrain.shuffle_seed = shuffle_seed
        b = self.b = FitBrain(make_spec(vals), toggles={"neuropal": "off", "gcamp": "off", **(toggles or {})},
                              cells=cells)
        FitBrain.shuffle_seed = None
        self.build_s = time.time() - t0
        self.om = next(m for m in b.mechs if type(m).__module__ == obs.__name__)
        h = self.h = b.h
        # Ca pool (Nicoletti 2019 in total current) from each soma's Ca current, recorded every integration step
        self.f, self.tca, self.caeq = h.f_cainternm, h.tca_cainternm, h.caeq_cainternm
        area = np.array([sum(seg.area() for seg in s) for s in b.soma])
        vcell = np.array([s(0.5).vcell_cainternm if h.ismembrane("cainternm", sec=s) else np.nan for s in b.soma])
        self.kca = self.f * area * 1e7 / (2.0 * FARADAY * vcell)             # uM/ms per mA/cm2
        self.has_ca = np.isfinite(self.kca)
        self.rec = []
        for i, s in enumerate(b.soma):
            v = h.Vector()
            if self.has_ca[i]:
                v.record(s(0.5)._ref_ica)
            self.rec.append(v)
        p = mech.params_for(obs, b.spec)
        self.kd, self.hn, self.R = p["obs_gcamp6s_kd_nM"], p["obs_gcamp6s_hill"], p["obs_gcamp6s_range"]
        self.th = p["obs_gcamp6s_thalf_ms"]
        b.reset()
        t0 = time.time()
        for _ in range(int(round(self.warm_s * 1000 / self.mech_dt))):
            b.step(dt_ms=self.mech_dt)
        self.warm_wall = time.time() - t0

    def _readout(self, n0):
        """F per cell at each volume from t = 0 of the warm-up to now; returns (t_s, F[cells, volumes])."""
        dt = wb.DT_MS
        n = int(self.rec[int(np.flatnonzero(self.has_ca)[0])].size())
        I = np.zeros((len(self.rec), n))
        for i, v in enumerate(self.rec):
            if self.has_ca[i]:
                I[i] = v.as_numpy()[:n]
        from scipy.signal import lfilter
        a = np.exp(-dt / self.tca)
        k = np.where(self.has_ca, self.kca, 0.0)[:, None]
        u = self.caeq - k * self.tca * I                  # the pool's steady state for the current held
        c0 = np.full((len(self.rec), 1), self.caeq)
        C, _ = lfilter([1 - a], [1, -a], u, axis=1, zi=c0 * a)
        # GCaMP6s on 1 ms samples, the Ca held over each sample
        stride = max(1, int(round(1.0 / dt)))
        Cs = C[:, ::stride] * 1000.0                      # uM -> nM
        B = np.full(len(self.rec), obs.hill(self.caeq * 1000.0, self.kd, self.hn))
        per_vol = int(round(VOL_S * 1000 / (dt * stride)))
        F = []
        for t in range(Cs.shape[1]):
            B = obs.binding_step(B, Cs[:, t], self.kd, self.hn, self.th, dt * stride)
            if (t + 1) % per_vol == 0:
                F.append(1.0 + (self.R - 1.0) * B)
        F = np.array(F).T
        tv = (np.arange(F.shape[1]) + 1) * VOL_S
        return tv, F

    def _child(self, target, window_s, pulse_ms, w):
        b, om = self.b, self.om
        t_on = b.t
        om.sched = [(target, t_on, float(pulse_ms), 1.0)] if target is not None else []
        for _ in range(int(round(window_s * 1000 / self.mech_dt))):
            b.step(dt_ms=self.mech_dt)
        tv, F = self._readout(0)
        keep = tv > t_on / 1000.0 - 1e-9
        os.write(w, pickle.dumps((tv[keep] - t_on / 1000.0, F[:, keep].astype(np.float32))))

    def run_one(self, target, window_s=30.0, pulse_ms=500.0):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            code = 0
            try:
                self._child(target, window_s, pulse_ms, w)
            except BaseException:
                import traceback
                traceback.print_exc()
                code = 1
            finally:
                os.close(w)
                os._exit(code)
        os.close(w)
        chunks = []
        while True:
            x = os.read(r, 1 << 20)
            if not x:
                break
            chunks.append(x)
        os.close(r)
        _, status = os.waitpid(pid, 0)
        if status != 0 or not chunks:
            raise RuntimeError(f"child for {target} failed (status {status})")
        return pickle.loads(b"".join(chunks))

    def run(self, targets, window_s=30.0, pulse_ms=500.0):
        """{'t': volume times after onset (s), 'ctrl': F[cells, vols], 'stat': [cells, targets], 'F': {target: F}}"""
        t0 = time.time()
        tv, Fc = self.run_one(None, window_s, pulse_ms)
        out = {"t": tv, "ctrl": Fc, "F": {}, "wall": {}}
        S = np.full((len(self.b.cell_names), len(targets)), np.nan)
        for k, tg in enumerate(targets):
            t1 = time.time()
            _, Fs = self.run_one(tg, window_s, pulse_ms)
            S[:, k] = np.mean((Fs - Fc) / Fc, axis=1)
            out["F"][tg] = Fs
            out["wall"][tg] = time.time() - t1
        out["stat"], out["targets"], out["run_wall"] = S, list(targets), time.time() - t0
        return out
