"""The data model of the worm: simulate(theta, experiment) -> observations (docs/worm/DATA_MODEL.md).

theta is the fit's vector (params.Theta order, natural units), a {parameter id: value} dict, or None (this worm's
values). The experiment is declarative: environment and fields, a stimulus schedule, optogenetics, clamps, the body
(off / immobilised / on), the genotype and other interventions (ablations, drugs), the duration and what to observe.
Interventions act through the model's own quantities (GENES), never through a free knob:
    ("g", name)       a per-cell conductance multiplier (mech.G_SCALE_NAMES): a channel density or a receptor class
                      (mech.AWA_G_SCALE_NAMES: Liu's conductances in AWA; egl-19 and shk-1 reach theirs)
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

from wormemu import heldout, mech
from wormemu.mech import drugs, pathogen, receptors, slow_signalling

# channel genes -> the densities they carry (BAAIWorm's composite SLO channels need both genes); in AWA under Liu 2018's
# membrane, egl-19 is its Ca current and shk-1 its K1 (Liu et al. 2018: egl-19 rf mutants lose AWA's spikes, the
# methods' SHK-1 current, Table S4's shk-1 fit sets gK1 to 0); Liu names no gene for the other six
_CH = {"egl-19": ("egl19", "slo1_egl19", "slo2_egl19", "awa_ca"), "unc-2": ("unc2", "slo1_unc2", "slo2_unc2"),
       "slo-1": ("slo1_unc2", "slo1_egl19", "slo1iso"), "slo-2": ("slo2_unc2", "slo2_egl19", "slo2iso"),
       "egl-2": ("egl2",), "shl-1": ("shl1",), "kqt-1": ("kqt1",), "kqt-3": ("kqt3",), "kvs-1": ("kvs1",),
       "egl-36": ("egl36",), "cca-1": ("cca1",), "shk-1": ("shk1", "awa_k1"), "unc-103": ("unc103",), "exp-2": ("exp2",),
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
# drugs: name -> what it acts on (mech/drugs.py); NOT_YET_DRUGS raise with what the model would need
DRUGS = {"levamisole": "tonic agonist conductance on L-AChR (lacr)", "ivermectin": "tonic agonist on GluCl (glucl)",
         "aldicarb": "AChE inhibition: the cholinergic cleft ACh multiplier (ache_clear_frac)",
         "serotonin": "bath source into neuromod's amine compartments", "dopamine": "as serotonin",
         "octopamine": "as serotonin", "tyramine": "as serotonin"}
NOT_YET_DRUGS = {"muscimol": "a tonic agonist on UNC-49 (the drugs table has no row yet)",
                 "nicotine": "a tonic agonist on lacr, acr16 and nachr (no row yet)"}


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
    temperature_C: float = 20.0      # the worm and the bath (NEURON celsius, every Q10; the head field unless the
    #                                  plate has an env_temp gradient, which then sets the head value; see simulate)
    cultivation_C: float | None = None   # sets AFD's T* (sens_afd_Tstar_C); None = this worm's value
    head: dict = field(default_factory=dict)     # constant fields over interface.HEAD_CHANNELS
    tail: dict = field(default_factory=dict)     # (osmolarity_mOsm: external excess, organs_other and the body)
    stimuli: list = field(default_factory=list)  # [Stimulus]
    opto: list = field(default_factory=list)     # [(cell, t_on_ms, dur_ms, intensity 0-1)], GUR-3/PRDX-2
    clamps: list = field(default_factory=list)   # [Clamp]
    body: str = "immobilised"        # off | immobilised (straight, untouched: open loop) | on (FEM body, closed loop)
    world: dict | None = None        # body on: the driver's world flags (body.metaworm, e.g. AGAR_FILM); None = Body's
    env: dict | None = None          # body on: environment.Environment toggles (row 22); None = the default plate
    env_params: dict = field(default_factory=dict)   # body on: environment.P overrides (the plate's protocol)
    env_events: list = field(default_factory=list)   # body on: environment events (tap, eyelash, o2_ambient)
    scene: dict | None = None        # body on: body.scene.ChemotaxisScene kwargs (field, target, channel, params:
    #                                  the scene_* numbers, experiment settings); None = ChemotaxisScene()
    genotype: list = field(default_factory=list)  # [Allele]
    ablations: list = field(default_factory=list)  # cell names removed with every synapse and gap they make
    drugs: list = field(default_factory=list)    # [(name, bath uM, t_on_ms)] (DRUGS)
    infection_h: float = 0.0         # hours on P. aeruginosa PA14 before the run (mech/pathogen; pathogen_sickness on)
    sources: list = field(default_factory=list)  # [(dataset, identifier)] the data this experiment reproduces
    heldout: bool = False            # True only in the pre-registered scoring run: locked identifiers allowed
    body_out: str | None = None      # body on: the FEM run's files (None = a temporary directory)
    observe: tuple = ("v_mV",)       # see OBSERVABLES; "out:<key>" for any module output
    cells: list | None = None        # cells reported for per-cell channels (None = all)
    every_ms: float = 1.0
    toggles: dict = field(default_factory=dict)  # mechanism forms over the defaults
    seed: int | None = None          # the worm drawn (None = the template worm); theta applies over it
    noise_seed: int | None = None    # the run's noise (quantal, channel, brain_layers, observation); None = seed


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
            pid, el = (k[:-1].split("[", 1) if k.endswith("]") and "[" in k else (k, None))
            spec = params.set_value(spec, pid, x, element=el)    # "pid[element]": one element of a table
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
    hits = heldout.experiment_locks([a.gene for a in ex.genotype], ex.ablations, ex.sources)
    if hits and not ex.heldout:
        raise heldout.HeldOut(f"locked identifiers {hits} (docs/worm/HELDOUT.md): only the pre-registered scoring "
                              "run sets Experiment.heldout")
    for d in ex.drugs:
        if d[0] not in DRUGS:
            raise NotImplementedError(f"drug {d[0]}: needs {NOT_YET_DRUGS.get(d[0], 'a mechanism (unknown drug)')}")
        if d[0] in drugs.AMINES and ex.toggles.get("monoamines", "compartments") not in ("compartments", "on",
                                                                                          "well_mixed"):
            raise ValueError(f"drug {d[0]}: a bath amine acts through the monoamine compartments (toggle off)")
    if ex.body != "on" and (ex.world is not None or ex.env is not None or ex.scene is not None or ex.env_params
                            or ex.env_events):
        raise ValueError("world, env, env_params, env_events and scene act through the body: body='on' only")
    if ex.env is None and (ex.env_params or ex.env_events):
        raise ValueError("env_params and env_events need env (the environment's toggles)")
    if ex.infection_h > 0 and ex.toggles.get("pathogen_sickness", "off") != "on":
        raise ValueError("infection_h: the infection state needs toggle pathogen_sickness on (off by default)")
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
    dsched, drugs.SCHEDULE[:] = list(drugs.SCHEDULE), [tuple(d) for d in ex.drugs]
    inf, pathogen.INFECTION_H = pathogen.INFECTION_H, float(ex.infection_h)
    orig, patched = B.load_structure, []
    try:
        if st is not None:                       # every module holding the loader sees the edited structure
            for m in list(sys.modules.values()):
                if getattr(m, "__name__", "").startswith("wormemu") and getattr(m, "load_structure", None) is orig:
                    m.load_structure = lambda st=st: st
                    patched.append(m)
        b = Brain(spec, toggles=ex.toggles, cells=names, noise_seed=ex.noise_seed)
    finally:
        for m in patched:
            m.load_structure = orig
        observation.SCHEDULE[:] = sched
        drugs.SCHEDULE[:] = dsched
        pathogen.INFECTION_H = inf
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
    cmd = b.reset()
    cells = list(b.cell_names) if ex.cells is None else list(ex.cells)
    ci = np.array([b.idx[c] for c in cells])
    neuron_ix = {n: k for k, n in enumerate(c for c, m in zip(b.cell_names, b.is_muscle) if not m)}
    if ex.body not in ("off", "immobilised", "on"):
        raise ValueError(ex.body)
    head = {**default_observation().head, "temperature_C": float(ex.temperature_C), **ex.head}
    tail = {**default_observation().tail, **ex.tail}
    rec = {k: [] for k in ex.observe}
    ts, ev = [], {"pumps": 0, "eggs_laid": 0, "expulsions": 0}
    body = None
    if ex.body == "on":   # the FEM body in closed loop (body/loop.py's exchange; the body sets the step)
        import tempfile
        from wormemu.body import layers as BL
        from wormemu.body.loop import Body, brain_dt_schedule
        out_dir = ex.body_out or tempfile.mkdtemp(prefix="wormemu_body_")
        mosm = float(ex.tail.get("osmolarity_mOsm", 0.0))
        osmo = ex.toggles.get("excretory_osmo", "canal")
        kw = {}                          # only what the experiment sets, so Body's defaults (and patches) stand
        if ex.world is not None:
            kw["world"] = dict(ex.world)
        if ex.env is not None:
            from wormemu.body import environment
            ep = dict(ex.env_params)
            ep.setdefault("temp_T0_C", float(ex.temperature_C))    # the plate is at the run's temperature at the start
            kw["env"] = environment.Environment(toggles=dict(ex.env), params=ep, events=list(ex.env_events))
        if ex.scene is not None:
            from wormemu.body.scene import ChemotaxisScene
            kw["scene"] = ChemotaxisScene(**ex.scene)
        body = Body(f"{out_dir}/body", params=BL.params_for(spec, osmo, extra_mosm=mosm),
                    body={k: v for k, v in ex.toggles.items() if k.startswith("body_")} or None, **kw)
        grad = body.env is not None and body.env.tog["env_temp"] == "gradient"
        if grad:
            notes.append("env_temp gradient: the head reads the plate's temperature; the worm's own (NEURON celsius, "
                         "the Q10s) stays at temperature_C")
        n = int(round(ex.duration_ms / (body.dt_s * 1000.0)))
        dts = brain_dt_schedule(n, body.dt_s * 1000.0)
        every = max(1, int(round(ex.every_ms / (body.dt_s * 1000.0))))
        notes.append(f"body on: exchange {body.dt_s * 1000.0:.3f} ms (the body's), files {out_dir}")
    else:
        n = int(round(ex.duration_ms / ex.dt_ms))
        dts = np.full(n, float(ex.dt_ms))
        every = max(1, int(round(ex.every_ms / ex.dt_ms)))
    t = 0.0
    for k in range(n):
        if body is None:
            o = default_observation(t)
            o.head, o.tail = dict(head), dict(tail)
        else:
            body.send(cmd, 1, dump=False)
            o = copy.copy(body.obs)
            o.head = {**body.obs.head, **({} if grad else {"temperature_C": float(ex.temperature_C)}), **ex.head}
            o.tail = {**body.obs.tail, **ex.tail}
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
        out = cmd = b.step(o, float(dts[k]))
        if body is not None:
            body.recv()
        t += float(dts[k])
        for e in ev:
            ev[e] += int(getattr(out, e) or 0)
        if (k + 1) % every:
            continue
        ts.append(t)
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
            elif ch == "posture":
                if body is None:
                    raise KeyError("posture: body on only")
                rec[ch].append(np.asarray(body.obs.curvature_per_mm, float))
            elif ch in OBSERVABLES:
                rec[ch].append(np.asarray(getattr(out, ch)))
            else:
                raise KeyError(f"observable {ch}")
    if body is not None:
        body.close()
    res = {"t_ms": np.array(ts), "cells": cells, "notes": notes}
    for ch, x in rec.items():
        try:
            res[ch] = np.array(x, float)
        except (TypeError, ValueError):
            res[ch] = x
    return res
