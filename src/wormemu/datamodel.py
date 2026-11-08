"""The data model of the worm: simulate(theta, experiment) -> observations (docs/worm/DATA_MODEL.md).

theta is the fit's vector (params.Theta order, natural units), a {parameter id: value} dict, or None (this worm's
values). The experiment is declarative: environment and fields, a stimulus schedule, optogenetics, clamps, the body
(off / immobilised / on), the genotype and other interventions (ablations, drugs), the duration and what to observe.
Interventions act through the model's own quantities (GENES), never through a free knob:
    ("g", name)       a per-cell conductance multiplier (mech.G_SCALE_NAMES): a channel density or a receptor class
    ("tx", transmitter) a vesicular or synthesis marker: the transmitter leaves every cell's identity (null only); a
                      cell left with none gets fast release 0
    ("tpm", gene)     the gene's CeNGEN expression, wherever the model reads it (receptor shares, innexin weights,
                      the density map; developmental only)
    ("spec", id)      a scalar number scaled (developmental only)
Timing: developmental = from t = 0, so the worm's slow set points and homeostasis form with the allele; acute = from
t_on_ms (default: the end of the set-point window, slow_set_s), on a worm that formed without it.
One NEURON per process: call simulate in a fresh process for each experiment.
"""
from __future__ import annotations

import copy
import dataclasses
import sys
from dataclasses import dataclass, field

import numpy as np

from wormemu import mech
from wormemu.mech import receptors, slow_signalling

# channel genes -> the densities they carry (BAAIWorm's composite SLO channels need both genes)
_CH = {"egl-19": ("egl19", "slo1_egl19", "slo2_egl19"), "unc-2": ("unc2", "slo1_unc2", "slo2_unc2"),
       "slo-1": ("slo1_unc2", "slo1_egl19", "slo1iso"), "slo-2": ("slo2_unc2", "slo2_egl19", "slo2iso"),
       "egl-2": ("egl2",), "shl-1": ("shl1",), "kqt-1": ("kqt1",), "kqt-3": ("kqt3",), "kvs-1": ("kvs1",),
       "egl-36": ("egl36",), "cca-1": ("cca1",), "shk-1": ("shk1",), "unc-103": ("unc103",), "exp-2": ("exp2",),
       "nca-1;nca-2": ("nca",)}       # NCA is one current for both genes (nicoletti.GENE): the double null only
_TX = {"unc-17": "acetylcholine", "eat-4": "glutamate", "unc-25": "gaba", "cat-2": "dopamine",
       "tph-1": "serotonin", "tdc-1": "tyramine", "tbh-1": "octopamine"}      # brain_structure.MARKERS


def _genes():
    g = {k: ([("g", f"dens_{c}") for c in v], "channel density (mech.CHANNEL_NAMES)") for k, v in _CH.items()}
    for c, (_, _, genes, rule, what) in receptors.CLASSES.items():
        for gene in genes:
            if rule == "all" or len(genes) == 1:      # an obligate subunit or the only gene: the whole class
                g[gene] = ([("g", f"rec_{c}")], f"receptor class {c} ({what}; rule '{rule}')")
            elif gene not in g:                       # one of several: its share, where the model reads expression
                g[gene] = ([("tpm", gene)], f"one gene of receptor class {c} ({what}); CeNGEN share")
    for gene, t in _TX.items():
        g[gene] = ([("tx", t)], f"marker of {t} (brain_structure.MARKERS)")
    g["tdc-1"] = ([("tx", "tyramine"), ("tx", "octopamine")], "tyramine synthesis; octopamine is made from tyramine")
    for inx in ("unc-7", "unc-9", "eat-5", "inx-1", "inx-2", "inx-7", "inx-8", "inx-10", "inx-11", "inx-12",
                "inx-13", "inx-14", "inx-18", "inx-19", "inx-20", "inx-21", "inx-22"):
        g[inx] = ([("tpm", inx)], "innexin (structure_rules innexin weights)")
    g["unc-31"] = ([("spec", "dcv_rate_per_s")], "CAPS: dense-core vesicle release of every peptide (neuromod)")
    return g


GENES = _genes()
# corpus genes the model cannot express yet, and why (docs/worm/DATA_MODEL.md)
NOT_YET = {
    "unc-47": "no GABA vesicular transporter apart from the unc-25 marker", "unc-46": "as unc-47",
    "cat-1": "no vesicular monoamine transporter apart from the synthesis markers",
    "cat-4": "no dopamine cofactor", "bas-1": "no decarboxylase paralog",
    "unc-36": "no auxiliary Ca channel subunit", "unc-13": "release is one lumped curve, no priming genes",
    "unc-18": "as unc-13", "tax-4": "the CNG output is keyed by cell, not by gene", "tax-2": "as tax-4",
    "osm-9": "the TRPV output is keyed by cell, not by gene", "ocr-2": "as osm-9",
    "mec-4": "the touch channels are keyed by cell", "trp-4": "proprioception has no gene",
    "daf-2": "only DAF-16's nuclear state is modelled", "daf-7": "ASI's daf7 state has no gene switch yet",
    "npr-1": "a GPCR null needs neuromod's receptor table edited (not wired yet)",
    "egl-1": "no cell death", "unc-77": "no NALCN auxiliary subunit", "unc-80": "as unc-77",
}
DRUGS = {   # name: what the model would need (none is representable yet; simulate raises)
    "levamisole": "a tonic agonist conductance on L-AChR (rec_lacr) without release",
    "aldicarb": "an ACh clearance step in the cleft (wsyn models receptor unbinding, not AChE)",
    "ivermectin": "a tonic agonist conductance on GluCl", "muscimol": "a tonic agonist on UNC-49",
    "nicotine": "a tonic agonist on lacr, acr16 and nachr",
    "serotonin": "a bath source in neuromod's amine compartments (cuticle permeation unmodelled)",
    "dopamine": "as serotonin", "octopamine": "as serotonin", "tyramine": "as serotonin",
}


@dataclass
class Allele:
    gene: str
    kind: str = "null"               # null (expression 0) | reduction (scaled by factor)
    factor: float = 0.0              # remaining fraction for a reduction
    timing: str = "developmental"    # developmental | acute
    t_on_ms: float | None = None     # acute onset (None = the end of the set-point window)


@dataclass
class Stimulus:
    channel: str                     # a head/tail field (interface.HEAD_CHANNELS), or nose_force_uN, tap,
    t_on_ms: float                   # contact_force_uN (with s_range)
    dur_ms: float
    value: float
    where: str = "head"              # head | tail (fields only)
    s_range: tuple = (0.0, 1.0)      # contact_force_uN: the midline span touched (0 nose, 1 tail)


@dataclass
class Clamp:
    cell: str
    kind: str                        # current (pA injected) | voltage (mV held; the clamp current is observed)
    t_on_ms: float
    dur_ms: float
    value: float


@dataclass
class Experiment:
    duration_ms: float = 100.0
    dt_ms: float = 1.0               # exchange step, a multiple of 0.5 ms
    temperature_C: float = 20.0      # the worm and the bath (NEURON celsius, the head field, every Q10)
    cultivation_C: float | None = None   # sets AFD's T* (sens_afd_Tstar_C); None = this worm's value
    head: dict = field(default_factory=dict)     # constant fields over interface.HEAD_CHANNELS
    tail: dict = field(default_factory=dict)     # (osmolarity_mOsm: external excess, organs_other and the body)
    stimuli: list = field(default_factory=list)  # [Stimulus]
    opto: list = field(default_factory=list)     # [(cell, t_on_ms, dur_ms, intensity 0-1)], GUR-3/PRDX-2
    clamps: list = field(default_factory=list)   # [Clamp]
    body: str = "immobilised"        # off | immobilised (straight, untouched: open loop) | on (FEM body, closed loop)
    genotype: list = field(default_factory=list)  # [Allele]
    ablations: list = field(default_factory=list)  # cell names removed with every synapse and gap they make
    drugs: list = field(default_factory=list)    # [(name, uM, t_on_ms)]
    observe: tuple = ("v_mV",)       # see OBSERVABLES; "out:<key>" for any module output
    cells: list | None = None        # cells reported for per-cell channels (None = all)
    every_ms: float = 1.0
    toggles: dict = field(default_factory=dict)  # mechanism forms over the defaults
    seed: int | None = None          # the worm drawn (None = the template worm); theta applies over it


OBSERVABLES = {
    "v_mV": "soma voltage per cell", "ca_uM": "soma Ca per cell", "gcamp_dff": "GCaMP dF/F per neuron (row 23)",
    "muscle_activation": "body-wall muscle activation, BWM_NAMES order", "pharynx_activation": "pharyngeal muscles",
    "enteric_activation": "enteric muscles", "sex_muscle_activation": "sex muscles",
    "pumps": "pharyngeal pumps per sample", "eggs_laid": "eggs per sample", "expulsions": "expulsions per sample",
    "clamp_pA": "each voltage clamp's electrode current (pA, + = into the cell)",
    "posture": "midline curvature (body on only)",
}


class _Intervene:
    """A registered-mechanism-shaped step: the genotype's conductance multipliers and the current clamps."""

    def __init__(self, brain, g, clamps):
        self.n, self.g, self.cl = len(brain.cell_names), g, [(brain.idx[c.cell], c) for c in clamps]

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        t = ctx.t_ms
        gs = {}
        for name, f, t_on in self.g:
            if t >= t_on:
                gs[name] = gs.get(name, np.ones(self.n)) * f
        r = {"g_scale": gs} if gs else {}
        if self.cl:
            I = np.zeros(self.n)
            for i, c in self.cl:
                if c.t_on_ms <= t < c.t_on_ms + c.dur_ms:
                    I[i] += c.value
            r["I_pA"] = I
        return r


def _theta(spec, theta):
    from wormemu import params
    if theta is None:
        return spec
    if isinstance(theta, dict):
        for k, x in theta.items():
            spec = params.set_value(spec, k, x)
        return spec
    return params.Theta().set(spec, np.asarray(theta, float))


def _structure(alleles):
    """The CeNGEN structure with the developmental tpm and transmitter edits, or None."""
    from wormemu.brain_structure import load_structure
    tpm_f, tx_null = {}, set()
    for a, eff in alleles:
        f = 0.0 if a.kind == "null" else a.factor
        for kind, x in eff:
            if kind == "tpm":
                tpm_f[x] = tpm_f.get(x, 1.0) * f
            elif kind == "tx":
                tx_null.add(x)
    if not tpm_f and not tx_null:
        return None, []
    st = load_structure()
    tpm = st.tpm.copy()
    for gene, f in tpm_f.items():
        if gene in st.gene_index:
            tpm[st.gene_index[gene]] *= f
    tx = {n: set(s) - tx_null for n, s in st.transmitter.items()}
    left = sorted(n for n, s in tx.items() if not s and st.transmitter[n])
    return dataclasses.replace(st, tpm=tpm, transmitter=tx), left


def simulate(theta, experiment: Experiment) -> dict:
    """Run one experiment on the worm theta describes. Returns {"t_ms": [n], channel: array [n, ...], "cells",
    "notes"}. Per-cell channels are [n samples, len(cells)]."""
    from wormemu import brain as B
    from wormemu.brain import Brain, sample_worm
    from wormemu.interface import default_observation
    from wormemu.mech import observation
    ex = experiment
    notes = []
    for d in ex.drugs:
        raise NotImplementedError(f"drug {d[0]}: needs {DRUGS.get(d[0], 'a mechanism (unknown drug)')}")
    spec = _theta(sample_worm(ex.seed), theta)
    vals = dict(spec.values)
    vals["ion_celsius"] = float(ex.temperature_C)                # linked (params.LINKED)
    if ex.cultivation_C is not None:
        vals["sens_afd_Tstar_C"] = float(ex.cultivation_C)       # T* follows the cultivation temperature
    spec = copy.copy(spec)
    spec.values = vals
    alleles = []
    for a in ex.genotype:
        if a.gene in NOT_YET:
            raise NotImplementedError(f"{a.gene}: {NOT_YET[a.gene]}")
        if a.gene not in GENES:
            raise KeyError(f"{a.gene}: not in datamodel.GENES")
        eff = GENES[a.gene][0]
        if a.timing == "acute" and any(k != "g" for k, _ in eff):
            raise ValueError(f"{a.gene}: only a developmental allele reaches {eff[0][0]}")
        if a.kind == "reduction" and any(k == "tx" for k, _ in eff):
            raise ValueError(f"{a.gene}: a transmitter marker takes null only")
        alleles.append((a, eff))
    for a, eff in alleles:
        for kind, x in eff:
            if kind == "spec":
                spec.values[x] = float(spec.values.get(x, 0.0)) * (0.0 if a.kind == "null" else a.factor)
    st, left = _structure(alleles)
    if left:   # no fast transmitter left: no fast release (else the unknown-transmitter path's graded synapse)
        notes.append(f"fast release 0 (no transmitter left): {', '.join(left)}")
    names = None
    if ex.ablations:
        from wormemu.brain_structure import load_structure
        s0 = load_structure()
        gone = set(ex.ablations)
        from wormemu.interface import BWM_NAMES
        names = [n for n, k in zip(s0.names, s0.kind) if k == "neuron" and n not in gone] + \
            [m for m in BWM_NAMES if m not in gone]
    sched, observation.SCHEDULE[:] = list(observation.SCHEDULE), [tuple(o) for o in ex.opto]
    orig, patched = B.load_structure, []
    try:
        if st is not None:                       # every module holding the loader sees the edited structure
            for m in list(sys.modules.values()):
                if getattr(m, "__name__", "").startswith("wormemu") and getattr(m, "load_structure", None) is orig:
                    m.load_structure = lambda st=st: st
                    patched.append(m)
        b = Brain(spec, toggles=ex.toggles, cells=names)
    finally:
        for m in patched:
            m.load_structure = orig
        observation.SCHEDULE[:] = sched
    set_ms = 1000.0 * float(mech.params_for(slow_signalling, spec)["slow_set_s"])
    g = []
    for a, eff in alleles:
        f = 0.0 if a.kind == "null" else a.factor
        t_on = 0.0 if a.timing == "developmental" else (set_ms if a.t_on_ms is None else a.t_on_ms)
        g += [(x, f, t_on) for kind, x in eff if kind == "g"]
    if left:
        f = np.ones(len(b.cell_names))
        f[[b.idx[c] for c in left if c in b.idx]] = 0.0
        g.append(("release", f, 0.0))
    cur = [c for c in ex.clamps if c.kind == "current"]
    if g or cur:
        b.mechs.append(_Intervene(b, g, cur))
    vcl = []
    for c in ex.clamps:
        if c.kind == "voltage":
            k = b.h.SEClamp(b.soma[b.idx[c.cell]](0.5))
            k.dur1, k.amp1, k.rs = 1e12, c.value, 1e9               # off until t_on (1e9 MOhm passes nothing)
            vcl.append((c, k))
        elif c.kind != "current":
            raise ValueError(c.kind)
    b.reset()
    cells = list(b.cell_names) if ex.cells is None else list(ex.cells)
    ci = np.array([b.idx[c] for c in cells])
    neuron_ix = {n: k for k, n in enumerate(c for c, m in zip(b.cell_names, b.is_muscle) if not m)}
    if ex.body == "on":
        raise NotImplementedError("body on: body.loop.run(brain, Body(out, params=body.layers.params_for(spec, "
                                  "extra_mosm=...)), seconds) is the route; not wired into simulate yet")
    if ex.body not in ("off", "immobilised"):
        raise ValueError(ex.body)
    head = {**default_observation().head, "temperature_C": float(ex.temperature_C), **ex.head}
    tail = {**default_observation().tail, **ex.tail}
    rec = {k: [] for k in ex.observe}
    ts, ev = [], {"pumps": 0, "eggs_laid": 0, "expulsions": 0}
    n = int(round(ex.duration_ms / ex.dt_ms))
    every = max(1, int(round(ex.every_ms / ex.dt_ms)))
    for k in range(n):
        t = k * ex.dt_ms
        o = default_observation(t)
        o.head, o.tail = dict(head), dict(tail)
        for s in ex.stimuli:
            if s.t_on_ms <= t < s.t_on_ms + s.dur_ms:
                if s.channel == "contact_force_uN":
                    o.contact_force_uN = np.where((o.s >= s.s_range[0]) & (o.s <= s.s_range[1]), s.value,
                                                  o.contact_force_uN)
                elif s.channel in ("nose_force_uN", "tap"):
                    setattr(o, s.channel, s.value)
                else:
                    getattr(o, s.where)[s.channel] = s.value
        for c, kc in vcl:
            kc.rs = 0.01 if c.t_on_ms <= t < c.t_on_ms + c.dur_ms else 1e9
        out = b.step(o, ex.dt_ms)
        for e in ev:
            ev[e] += int(getattr(out, e) or 0)
        if (k + 1) % every:
            continue
        ts.append(t + ex.dt_ms)
        for ch in ex.observe:
            if ch in ("v_mV", "ca_uM"):
                rec[ch].append(np.asarray(getattr(out, ch))[ci])
            elif ch == "gcamp_dff":
                x = getattr(out, ch)
                rec[ch].append(np.full(len(cells), np.nan) if x is None else
                               np.array([x[neuron_ix[c]] if c in neuron_ix else np.nan for c in cells]))
            elif ch in ev:
                rec[ch].append(ev[ch])
                ev[ch] = 0
            elif ch == "clamp_pA":
                rec[ch].append([1000.0 * kc.i for _, kc in vcl])
            elif ch.startswith("out:"):
                rec[ch].append(b.mech_out.get(ch[4:]))
            elif ch in OBSERVABLES and ch != "posture":
                rec[ch].append(np.asarray(getattr(out, ch)))
            else:
                raise KeyError(f"observable {ch}")
    res = {"t_ms": np.array(ts), "cells": cells, "notes": notes}
    for ch, x in rec.items():
        try:
            res[ch] = np.array(x, float)
        except (TypeError, ValueError):
            res[ch] = x
    return res
