"""The worm brain: BAAIWorm's NEURON cells (ported, Apache 2.0) for all 302 neurons and the 95 body-wall muscles,
the connectome, and the lumped layers of brain_layers. Every number comes from the ledger (data/worm/model).

    spec = sample_worm(seed)              # seed None = the template worm (the ledger's values); an int = one draw
    brain = Brain(spec, toggles={...})    # ledger toggles; defaults from mechanisms.yaml
    out = brain.reset()                   # BrainToBody at t = 0
    out = brain.step(obs, dt_ms=1.0)      # BodyToBrain in, BrainToBody out (internal step 0.5 ms, BAAIWorm's)

literature_overrides off = BAAIWorm as published: the cell parameters in third_party/baaiworm/cell_param, the mod
defaults, 1e-5 uS per gap junction half, NEURON's ion defaults (celsius 6.3, cao 2, cai 5e-5). This is the port302a
reference. On = the ledger's values with the literature ranges applied, including the Ca units fix: the mods keep
Ca in uM but NEURON's ion defaults are mM, so E_Ca sat near +42 mV; with cao0 = 2000 (2 mM in uM) and cai0 = caeq
0.05 uM it is about +130 mV at rest (derived).

wiring=baaiworm: BAAIWorm's construction as placed in port302a (data/worm/brain_runs/port302a/connections.csv,
seed 1), MCVL24 dropped (the worm has no such muscle). wiring=cook: every Cook 2019 pair, strength = the ledger's
per-EM value x the pair's EM count, split over BAAIWorm's sites where it placed any, else one site on the nearest
segment pair; Cook's 956 neuron-to-muscle pairs; no muscle-to-neuron synapses.

muscle_active on = c302 C2's body-wall muscle membrane (third_party/c302, MIT; Boyle and Cohen 2008's leak, slow K,
fast K and Ca currents with a Ca pool) in place of BAAIWorm's passive muscle, on the same 5 x 20 um cylinder, every
value from the ledger's c302_* rows; the muscles start at c302's -28 mV with no Ca.

gap_rectification on = the gap junctions between AVA, AVB, AVD, AVE, PVC and DA, VA, DB, VB rectify (nmodl/rectgap.mod):
the template conductance when current flows from the motor neuron into the interneuron (Liu et al. 2017), divided
by gap_rect_ratio the other way.

NEURON is one simulator per process: build one Brain per process.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from bioemu import ledger
from wormemu import brain_layers, mech
from wormemu.brain_structure import BAAIWORM_NO_SUCH_MUSCLE, bwm_name, cengen_class, load_structure
from wormemu.interface import (BWM_NAMES, ENTERIC_MUSCLES, PHARYNX_MUSCLES, SEX_MUSCLES, BrainToBody,
                               default_observation, muscle_position)

ROOT = Path(__file__).resolve().parents[2]
BAAI = ROOT / "third_party" / "baaiworm"
C302 = ROOT / "third_party" / "c302"
OWN_MODS = Path(__file__).resolve().parent / "nmodl"
MODEL = ROOT / "data" / "worm" / "model"
PORT302A = ROOT / "data" / "worm" / "brain_runs" / "port302a" / "connections.csv"
DT_MS = 0.5                     # BAAIWorm's step
V_INIT = -65.0                  # BAAIWorm's v_init
V_INIT_MUSCLE = -28.0           # c302 GenericMuscleCell initMembPotential (muscle_active on)
MUSCLE_ACTIVE = {               # c302 mod: {range variable: ledger row}; the reversals are set after INITIAL
    "Leak": {"gmax": "c302_muscle_leak_cond_density", "e": "c302_muscle_leak_erev"},
    "k_slow_muscle": {"gmax": "c302_muscle_k_slow_cond_density", "n_timeCourse_tau": "c302_k_slow_gate_n_tau",
                      "n_steadyState_scale": "c302_k_slow_gate_n_scale",
                      "n_steadyState_midpoint": "c302_k_slow_gate_n_midpoint"},
    "k_fast_muscle": {"gmax": "c302_muscle_k_fast_cond_density",
                      **{f"{g}_{a}": f"c302_k_fast_gate_{g}_{b}" for g in "pq" for a, b in (
                          ("timeCourse_tau", "tau"), ("steadyState_scale", "scale"),
                          ("steadyState_midpoint", "midpoint"))}},
    "ca_boyle_muscle": {"gmax": "c302_muscle_ca_boyle_cond_density",
                        **{f"{g}_{a}": f"c302_ca_boyle_gate_{g}_{b}" for g in "ef" for a, b in (
                            ("timeCourse_tau", "tau"), ("steadyState_scale", "scale"),
                            ("steadyState_midpoint", "midpoint"))},
                        "h_alpha": "c302_ca_boyle_gate_h_alpha", "h_ca_half": "c302_ca_boyle_gate_h_ca_half",
                        "h_k": "c302_ca_boyle_gate_h_k"},
    "CaPoolMuscle": {"decayConstant": "c302_ca_conc_decay_time_muscle", "rho": "c302_ca_conc_rho_muscle"},
}
MUSCLE_EREV = {"c302_muscle_k_slow_erev": -30.0, "c302_muscle_k_fast_erev": -30.0,   # fixed inside the c302 mods
               "c302_muscle_ca_boyle_erev": 0.0}                                       # (INITIAL, not reachable)
RHO_SI_TO_MOD = 1e-8            # mol / (m A s) -> umol / (cm nA ms), the mod's unit (derived)
# gap_rectification: AVA-class interneuron (UNC-7 side) to A- and B-type motor neuron (UNC-9 side) junctions pass
# current into the interneuron (Liu et al. 2017, measured for AVA-VA5; the other classes by the ledger's C3 range)
RECT_INTO = re.compile(r"(AVA|AVB|AVD|AVE|PVC)[LR]")
RECT_FROM = re.compile(r"(DA|VA|DB|VB)\d\d")
CHANNELS = ["slo1_unc2", "egl2", "shl1", "kqt3", "unc2", "kvs1", "slo1_egl19", "slo2_unc2", "irk", "egl36", "egl19",
            "cca1", "shk1", "slo2_egl19", "nca", "kcnl", "cainternm"]          # BAAIWorm's insert order
GB = {"slo1_egl19": "gbslo1", "slo1_unc2": "gbslo1", "slo2_egl19": "gbslo2", "slo2_unc2": "gbslo2"}
SLO = ("slo1_egl19", "slo1_unc2", "slo2_egl19", "slo2_unc2")
KNOWN = {"measured", "published_fit", "derived", "inferred"}

_h = None


def _neuron():
    """NEURON with the vendored mods loaded (compiled once into $WORMEMU_NRNMECH or ~/.cache/wormemu/nrnmech)."""
    global _h
    if _h is not None:
        return _h
    from neuron import h
    mods = sorted((BAAI / "mod").glob("*.mod")) + sorted((C302 / "mod").glob("*.mod")) \
        + sorted(OWN_MODS.rglob("*.mod"))                # ours, including the organ workers' nmodl/organs/
    tag = hashlib.sha1(b"".join(m.name.encode() + m.read_bytes() for m in mods)).hexdigest()[:12]
    d = Path(os.environ.get("WORMEMU_NRNMECH", Path.home() / ".cache" / "wormemu" / "nrnmech")) / tag

    def find():
        libs = glob.glob(str(d / "*" / "libnrnmech.*")) + glob.glob(str(d / "*" / ".libs" / "libnrnmech.so"))
        return libs[0] if libs else None
    lib = find()
    if lib is None:
        d.mkdir(parents=True, exist_ok=True)
        exe = shutil.which("nrnivmodl") or str(Path(sys.executable).parent / "nrnivmodl")
        (d / "src").mkdir(exist_ok=True)
        for m in mods:
            shutil.copy(m, d / "src" / m.name)
        with open(d / "build.log", "w") as log:
            subprocess.run([exe, "src"], cwd=d, check=True, stdout=log, stderr=subprocess.STDOUT)
        lib = find()
    if not hasattr(h, "neuron_to_neuron_exc_syn"):
        h.nrn_load_dll(lib)
    h.load_file("stdrun.hoc")
    _h = h
    return h


# --- the worm's numbers --------------------------------------------------------------------------------------------
@dataclass
class WormSpec:
    """One worm: every ledger number (a float for a global row, a Series by element for a values table)."""
    seed: int | None
    values: dict
    led: ledger.Ledger

    def v(self, pid, element=None):
        x = self.values[pid]
        return float(x[element]) if element is not None else x


def _draw_around(rng, r, x):
    """Per-element draws around each element's own value with the row's prior shape, truncated to the bounds."""
    lo, hi = float(r.bio_min), float(r.bio_max)
    out = x.copy()
    todo = np.ones(len(x), bool)
    for _ in range(200):
        if not todo.any():
            break
        n = int(todo.sum())
        if r.prior_dist == "lognormal":
            y = np.where(x[todo] > 0, x[todo] * np.exp(rng.normal(0, float(r.prior_b), n)), 0.0)
        elif r.prior_dist == "normal":
            y = x[todo] + rng.normal(0, float(r.prior_b), n)
        else:                                            # uniform / loguniform: each element from the prior
            y = ledger.draw(rng, r, n)
        ok = (y >= lo) & (y <= hi)
        idx = np.flatnonzero(todo)
        out[idx[ok]] = y[ok]
        todo[idx[ok]] = False
    return out


def sample_worm(seed: int | None = None, root: Path = MODEL) -> WormSpec:
    """seed None: the template worm. An int: known values (measured, published fit, derived, inferred) and
    structure stay fixed; each guessed global number is drawn from its prior; a guessed connection-grain row gets
    one shared factor (its pairs keep their ratios); other guessed elements are drawn one by one."""
    led = ledger.load(root)
    rng = np.random.default_rng(seed)
    vals = {}
    for r in led.parameters.itertuples():
        if r.label == "absent":
            continue
        t = led.values(r.param_id)
        draw = seed is not None and r.prior_dist not in ("fixed", "bernoulli", "categorical")
        if t is None:
            v = float(r.value_template)
            if draw and r.label == "guessed":
                v = float(ledger.draw(rng, r)[0])
            vals[r.param_id] = v
            continue
        x = t.value.to_numpy(float).copy()
        g = (t.label == "guessed").to_numpy()
        if draw and g.any():
            if r.grain == "connection":
                f = float(ledger.draw(rng, r)[0]) / float(r.value_template)
                x[g] = np.clip(x[g] * f, r.bio_min, r.bio_max)
            else:
                x[g] = _draw_around(rng, r, x[g])
        vals[r.param_id] = pd.Series(x, index=t.element.to_numpy())
    return WormSpec(seed=seed, values=vals, led=led)


def default_toggles(led: ledger.Ledger) -> dict:
    m = led.mechanisms
    return {r.toggle: r.default for r in m.itertuples() if isinstance(r.toggle, str) and r.toggle}


def _toggle_mechanisms(led: ledger.Ledger) -> dict:
    m = led.mechanisms
    return {r.toggle: r.id for r in m.itertuples() if isinstance(r.toggle, str) and r.toggle}


# --- geometry: BAAIWorm's segment list (detailed_circuit.Cell.prepare, length_per_seg 2 um) -----------------------
def _segments(hobj, length_per_seg=2.0):
    """[(hoc segment, midpoint xyz)], in BAAIWorm's segment index order (connections.csv pre_seg / post_seg)."""
    pts, segs, ends = [], [], []
    for sec in hobj.all:
        soma = "Soma" in sec.name()
        sec.nseg = 1 if soma else int(np.ceil(sec.L / length_per_seg))
        init = np.array((sec.x3d(0), sec.y3d(0), sec.z3d(0)))
        if soma:
            pts.append(init)
            prev = 0
            ends.append(0)
        else:
            prev = ends[int(np.argmin([np.linalg.norm(pts[e] - init) for e in ends]))]
        bar = np.linspace(0, 1, sec.nseg + 1)
        cnt = 1
        for i in range(sec.n3d() - 1):
            a0, a1 = sec.arc3d(i) / sec.L, sec.arc3d(i + 1) / sec.L
            p0 = np.array((sec.x3d(i), sec.y3d(i), sec.z3d(i)))
            p1 = np.array((sec.x3d(i + 1), sec.y3d(i + 1), sec.z3d(i + 1)))
            while cnt <= sec.nseg and bar[cnt] <= a1:
                pts.append((p1 - p0) * (bar[cnt] - a0) / (a1 - a0) + p0)
                segs.append((sec((bar[cnt] + bar[cnt - 1]) / 2), (pts[prev] + pts[-1]) / 2))
                prev = len(pts) - 1
                cnt += 1
        ends.append(len(pts) - 1)
    return segs


# --- the brain -------------------------------------------------------------------------------------------------------
class Brain:
    """cell_names = the 302 neurons (Cook 2019 order) then the 95 body-wall muscles (BWM_NAMES order); a subset
    if `cells` is given (for tests). `extra_pA` (cell order) is a test-input current added every step."""

    def __init__(self, spec: WormSpec | None = None, toggles: dict | None = None, cells=None,
                 keep_mcvl24: bool = False):
        self.spec = spec or sample_worm(None)
        led = self.spec.led
        self.toggles = default_toggles(led)
        self._mods = mech.modules()
        for mid, _, _, dflt in (t for m in self._mods for t in m.MECHANISMS):
            self.toggles.setdefault(mid, dflt)            # a registered mechanism the ledger has no row for yet
        for k, v in (toggles or {}).items():
            assert k in self.toggles, f"unknown toggle {k}"
            self.toggles[k] = {True: "on", False: "off"}.get(v, v)
        tg = self.toggles
        self.lit = tg["literature_overrides"] == "on"
        self.mact = tg["muscle_active"] == "on"
        self.h = h = _neuron()
        st = self.st = load_structure()
        neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
        muscles = list(BWM_NAMES) + ([BAAIWORM_NO_SUCH_MUSCLE] if keep_mcvl24 else [])
        want = set(cells) if cells is not None else None
        self.cell_names = [n for n in neurons + muscles if want is None or n in want]
        self.idx = {n: i for i, n in enumerate(self.cell_names)}
        self.is_muscle = np.array([n not in set(neurons) for n in self.cell_names])
        self._baai = {m: m for m in neurons}
        self._baai.update({n: f"MC{n[0].upper()}{n[4]}{int(n[5:]):02d}" for n in BWM_NAMES})
        self._baai[BAAIWORM_NO_SUCH_MUSCLE] = BAAIWORM_NO_SUCH_MUSCLE
        assert all(bwm_name(self._baai[n]) == n for n in BWM_NAMES)

        self._ions()
        self.cells, self.segs, self.soma = [], [], []
        for n in self.cell_names:
            b = self._baai[n]
            h.load_file(str(BAAI / "model" / f"{b}.hoc"))
            obj = getattr(h, b)()
            self._biophysics(n, obj)
            self.cells.append(obj)
            self.segs.append(_segments(obj))
            self.soma.append(obj.Soma)
        self.n_segments = sum(len(s) for s in self.segs)
        self._kinetics()
        self.conn = []                                   # hoc point processes (kept alive)
        self.placed = defaultdict(int)
        if tg["wiring"] == "baaiworm":
            self._wire_baaiworm()
        elif tg["wiring"] == "cook":
            self._wire_cook()
        else:
            raise ValueError(tg["wiring"])
        if tg["bwm_coupling"] == "on":
            for e, g in self.spec.v("bwm_gap").items():
                a, b = e.split("-")
                if a in self.idx and b in self.idx:
                    self._gap(self.segs[self.idx[a]][0][0], self.segs[self.idx[b]][0][0], g / 1000.0, "gap_bwm")

        n = len(self.cell_names)
        self.stim = []
        for s in self.soma:
            c = h.IClamp(s(0.5))
            c.delay, c.dur, c.amp = 0.0, 1e12, 0.0
            self.stim.append(c)
        self._amp = np.zeros(n)
        self.extra_pA = np.zeros(n)
        self._pv, self._pc = h.PtrVector(n), h.PtrVector(n)
        for i, s in enumerate(self.soma):
            self._pv.pset(i, s(0.5)._ref_v)
            self._pc.pset(i, s(0.5)._ref_cai)
        self._buf = h.Vector(n)
        # c302's muscle pool holds cai in mM (on c302's own scale: its rho is a blind guess); BAAIWorm's cells hold uM
        self._ca_scale = np.where(self.is_muscle & self.mact, 1000.0, 1.0)

        claimed = {t[0] for m in self._mods for t in m.MECHANISMS}   # taken over by a registered mechanism
        on = {mid for tog, mid in _toggle_mechanisms(led).items() if tg.get(tog) == "on"} - claimed
        p = {s.id: self.spec.v(s.id) for s in brain_layers.SPECS if s.id in self.spec.values
             and not isinstance(self.spec.values[s.id], pd.Series)}
        y = np.array([st.soma_y_um[st.index[c]] if not m else np.nan for c, m in zip(self.cell_names,
                                                                                    self.is_muscle)])
        yall = np.array([st.soma_y_um[st.index[c]] for c in neurons])
        pos = (y - np.nanmin(yall)) / (np.nanmax(yall) - np.nanmin(yall))
        self.bwm = np.array([self.idx.get(m, -1) for m in BWM_NAMES])
        self.layers = brain_layers.Layers(self.cell_names, pos, [muscle_position(m) for m in BWM_NAMES], p, on,
                                          0 if self.spec.seed is None else self.spec.seed,   # template: fixed
                                          peptide=self._modulators("pep"),
                                          monoamine=self._modulators("ma"))
        self._g_targets()
        self.mechs = [m.Mech(self, mech.params_for(m, self.spec), tg) for m in self._mods
                      if any(mech.is_on(tg[t[0]]) for t in m.MECHANISMS)]
        self.mech_out = {}
        self.t = 0.0

    # --- biophysics --------------------------------------------------------------------------------------------
    def _ions(self):
        h, sv = self.h, self.spec.v
        h.dt, h.secondorder = DT_MS, 0
        if self.lit:
            h.celsius = sv("ion_celsius")
            h.cao0_ca_ion = sv("ion_cao") * 1000.0       # the mods' Ca unit is uM
            h.cai0_ca_ion = sv("capool_caeq")
        else:
            h.celsius, h.cao0_ca_ion, h.cai0_ca_ion = 6.3, 2.0, 5e-5

    def _cell_param(self, name):
        b = self._baai[name]
        cp = json.loads((BAAI / "cell_param" / f"{b}.json").read_text())
        if not self.lit or name == BAAIWORM_NO_SUCH_MUSCLE:
            return cp
        sv = self.spec.v
        if name in BWM_NAMES:
            for q in ("Ra", "cm", "gpas", "epas"):
                cp["soma"][q] = sv(f"mpas_{q}", name)
            return cp
        for part in ("soma", "neurite"):
            if part in cp:
                for q in ("Ra", "cm", "gpas", "epas"):
                    cp[part][q] = sv(f"pas_{part}_{q}", name)
        for ch in CHANNELS[:-1]:
            cp["soma"][f"gb{ch}"] = self._density(ch, name)
        return cp

    def _density(self, ch, name):
        v = self.spec.v(f"dens_{ch}", name)
        if self.toggles["expression_map"] != "on":
            return v
        t = self.spec.led.values(f"dens_{ch}").set_index("element")
        tpm, cls = float(t.cengen_tpm[name]), t.cengen_class[name]
        if isinstance(cls, str) and cls and tpm == 0:
            return 0.0
        if tpm > 0 and v == 0:
            nz = t.value[(t.value > 0) & (t.cengen_tpm > 0)]
            return float(nz.median()) if len(nz) else 0.0
        return v

    def _biophysics(self, name, obj):
        if self.mact and name in BWM_NAMES:
            return self._c302_muscle(obj)
        cp = self._cell_param(name)
        for sec in obj.all:
            part = "soma" if "Soma" in sec.name() else "neurite"
            q = cp.get(part, cp["soma"])
            sec.Ra, sec.cm = q["Ra"], q["cm"]
            sec.insert("pas")
            for seg in sec:
                seg.pas.g, seg.pas.e = q["gpas"], q["epas"]
        for ch in CHANNELS:
            obj.Soma.insert(ch)
        for seg in obj.Soma:
            for ch in CHANNELS[:-1]:
                setattr(getattr(seg, ch), GB.get(ch, f"gb{ch}"), cp["soma"][f"gb{ch}"])
        if self.lit:
            sv = self.spec.v
            for ion, pid, dflt in (("k_ion", "ion_ek", -77.0), ("na_ion", "ion_ena", 50.0)):
                if sv(pid) != dflt and self.h.ismembrane(ion, sec=obj.Soma):
                    setattr(obj.Soma, "ek" if ion == "k_ion" else "ena", sv(pid))

    def _c302_muscle(self, obj):
        """muscle_active: c302 C2's GenericMuscleCell membrane (cm 1 uF/cm2 as BAAIWorm's; one compartment, so its
        Ra does not act), every value from the ledger."""
        sv = self.spec.v
        for pid, e in MUSCLE_EREV.items():
            if sv(pid) != e:
                raise ValueError(f"{pid} = {sv(pid)}: the c302 mod fixes this reversal at {e} mV")
        for sec in obj.all:
            sec.cm = 1.0
            for mod, pars in MUSCLE_ACTIVE.items():
                sec.insert(mod)
                for seg in sec:
                    for name, pid in pars.items():
                        setattr(getattr(seg, mod), name, sv(pid) * (RHO_SI_TO_MOD if name == "rho" else 1.0))
            # the pool owns cai (c302's own units, starting at 0); the mods use their own E_Ca, not the ion's
            self.h.ion_style("ca_ion", 3, 1, 0, 0, 0, sec=sec)

    def _kinetics(self):
        """Channel kinetics, nanodomain and Ca pool constants: mod GLOBALs (RANGE ones set on every soma)."""
        if not self.lit:
            return
        h, p = self.h, self.spec.led.parameters
        for r in p.itertuples():
            if r.mechanism_id.startswith("ch_") and r.param_id.startswith("kin_"):
                mod = r.mechanism_id[3:]
                targets = [(mod, r.param_id[len(f"kin_{mod}_"):])]
            elif r.mechanism_id == "ca_nanodomain":
                targets = [(m, r.param_id[5:]) for m in SLO]
            elif r.mechanism_id == "ca_pool":
                targets = [("cainternm", r.param_id[7:])]
            else:
                continue
            v = self.spec.v(r.param_id)
            for mod, name in targets:
                try:
                    setattr(h, f"{name}_{mod}", v)          # a GLOBAL
                    continue
                except (AttributeError, LookupError, TypeError):
                    pass
                for s in self.soma:
                    for seg in s:
                        m = getattr(seg, mod, None)
                        if m is not None and hasattr(m, name):
                            setattr(m, name, v)

    def _g_targets(self):
        """The conductances a mechanism can scale per cell (mech.G_SCALE_NAMES): a PtrVector over every soma that
        has the channel (BAAIWorm cells; c302 muscles have none), with its base values."""
        h = self.h
        self._gt = {}
        for name in mech.G_SCALE_NAMES:
            ch = name[5:] if name.startswith("dens_") else "pas"
            var = GB.get(ch, f"gb{ch}") if ch != "pas" else "g"
            cells = [i for i, s in enumerate(self.soma) if h.ismembrane(ch, sec=s)]
            if not cells:
                continue
            pv = h.PtrVector(len(cells))
            for k, i in enumerate(cells):
                pv.pset(k, getattr(self.soma[i](0.5), f"_ref_{var}_{ch}"))
            buf = h.Vector(len(cells))
            pv.gather(buf)
            self._gt[name] = (np.array(cells), pv, buf.as_numpy().copy(), np.ones(len(cells)))

    def _apply_g_scale(self, g):
        """Set each scalable conductance to base x this step's product of multipliers (1 where no mechanism returned
        one this step); a NEURON write only where the multiplier changed."""
        bad = set(g) - set(mech.G_SCALE_NAMES)
        if bad:
            raise KeyError(f"g_scale {sorted(bad)} not conductances the brain knows (mech.G_SCALE_NAMES)")
        for name, (cells, pv, base, cur) in self._gt.items():
            f = np.asarray(g[name], float)[cells] if name in g else 1.0
            if np.array_equal(cur, np.broadcast_to(f, cur.shape)):
                continue
            cur[:] = f
            pv.scatter(self.h.Vector(base * cur))

    # --- connections -------------------------------------------------------------------------------------------
    def _inhibitory(self, pre, post):
        """Sign of a synapse from a neuron: the sign_rule toggle, then receptor_sign for neuron-neuron pairs."""
        if self.toggles["sign_rule"] == "allexc":
            return False
        if self.toggles["receptor_sign"] == "on":
            r = self.spec.values["syn_sign_receptor"]
            if f"{pre}>{post}" in r.index:
                return bool(r[f"{pre}>{post}"])
        return bool(self.spec.v("syn_inhibitory", pre))

    def _syn(self, pre_seg, post_seg, weight, inh, kind):
        h = self.h
        sk = "inh" if inh else "exc"
        pp = getattr(h, f"neuron_to_neuron_{sk}_syn")(post_seg)
        h.setpointer(pre_seg._ref_v, "vpre", pp)
        pp.weight = weight
        if self.lit:
            for q in ("conductance", "delta", "k", "Vth", "erev"):
                setattr(pp, q, self.spec.v(f"syn_{sk}_{q}"))
        self.conn.append(pp)
        self.placed[kind + ("_inh" if inh else "")] += 1

    def _gap(self, seg_a, seg_b, g_uS, kind, into=None, ratio=1.0):
        """One gap junction between two segments. `into` (seg_a or seg_b): a rectifying junction that passes
        current into that side at g_uS and the other way at g_uS / ratio (gap_rectification)."""
        h = self.h
        for x, y in ((seg_a, seg_b), (seg_b, seg_a)):
            if into is None:
                pp = h.gapjunction(x)
            else:
                pp = h.rectgap(x)
                pp.ratio, pp.side = ratio, 1.0 if x is into else -1.0
            h.setpointer(y._ref_v, "vpre", pp)
            pp.weight = g_uS
            self.conn.append(pp)
        self.placed[kind if into is None else kind + "_rect"] += 1

    def _g_syn(self, inh):
        sk = "inh" if inh else "exc"
        if self.lit:
            return self.spec.v(f"syn_{sk}_conductance")
        return 2e-4 if inh else 4.9e-4                   # mod defaults (uS)

    def _read_port302a(self):
        rows = []
        with open(PORT302A) as f:
            for r in csv.DictReader(f):
                a, b = (bwm_name(x) or x if re.fullmatch(r"MC[DV][LR]\d\d", x) else x for x in (r["pre"], r["post"]))
                rows.append((a, int(r["pre_seg"]), b, int(r["post_seg"]), r["category"], abs(float(r["weight"]))))
        return rows

    def _wire_baaiworm(self):
        g_gap = self.spec.v("gap_weight") if self.lit else 1e-5
        for a, i, b, j, cat, w in self._read_port302a():
            if a not in self.idx or b not in self.idx:
                continue
            ps, qs = self.segs[self.idx[a]][i][0], self.segs[self.idx[b]][j][0]
            pm, qm = self.is_muscle[self.idx[a]], self.is_muscle[self.idx[b]]
            if cat == "gj":                              # connections.csv lists each half; place one half
                pp = self.h.gapjunction(qs)
                self.h.setpointer(ps._ref_v, "vpre", pp)
                pp.weight = g_gap
                self.conn.append(pp)
                self.placed["gap_half"] += 1
                continue
            kind = "syn_mn" if pm else ("syn_nmj" if qm else "syn_nn")
            self._syn(ps, qs, w, False if pm else self._inhibitory(a, b), kind)

    def _nearest(self, a, b):
        from scipy.spatial import cKDTree
        sa, sb = self.segs[self.idx[a]], self.segs[self.idx[b]]
        tb = cKDTree(np.array([x for _, x in sb]))
        d, k = tb.query(np.array([x for _, x in sa]))
        i = int(np.argmin(d))
        return i, int(k[i])

    def _wire_cook(self):
        rows = self._read_port302a()
        syn_sites, gap_sites = defaultdict(list), defaultdict(set)
        for a, i, b, j, cat, _ in rows:
            if cat == "syn":
                syn_sites[(a, b)].append((i, j))
            else:
                key = tuple(sorted(((a, i), (b, j))))
                gap_sites[(key[0][0], key[1][0])].add((key[0][1], key[1][1]))
        sv, led = self.spec.v, self.spec.led
        n_em = {pid: led.values(pid).set_index("element").n_em for pid in
                ("syn_strength_per_pair", "gap_strength_per_pair", "nmj_strength_per_pair")}
        for e, g in sv("syn_strength_per_pair").items():
            a, b = e.split(">")
            if a not in self.idx or b not in self.idx:
                continue
            inh = self._inhibitory(a, b)
            sites = syn_sites.get((a, b)) or [self._nearest(a, b)]
            w = g * n_em["syn_strength_per_pair"][e] / len(sites) / (self._g_syn(inh) * 1000.0)
            for i, j in sites:
                self._syn(self.segs[self.idx[a]][i][0], self.segs[self.idx[b]][j][0], w, inh, "syn_nn")
        inx = self.toggles.get("innexin_identity") == "on"
        rect = self.toggles.get("gap_rectification") == "on"
        for e, g in sv("gap_strength_per_pair").items():
            a, b = e.split("-")
            if a not in self.idx or b not in self.idx:
                continue
            if inx:                                      # innexin channels (ledger mechanism innexin_identity)
                if not sv("gap_innexin_pair", e):
                    continue                             # a partner expresses no innexin (CeNGEN)
                g = sv("gap_open_channels_per_em") * sv("gap_innexin_unitary") / 1000.0     # pS -> nS
            key = tuple(sorted((a, b)))
            sites = sorted(gap_sites.get(key, ())) or [self._nearest(*key)]
            w = g * n_em["gap_strength_per_pair"][e] / len(sites) / 1000.0
            into = next((n for n in key if RECT_INTO.fullmatch(n)), None) if rect else None
            if into is not None and not any(RECT_FROM.fullmatch(n) for n in key):
                into = None
            for i, j in sites:
                sa, sb = self.segs[self.idx[key[0]]][i][0], self.segs[self.idx[key[1]]][j][0]
                self._gap(sa, sb, w, "gap_nn", into=None if into is None else (sa if into == key[0] else sb),
                          ratio=sv("gap_rect_ratio") if into else 1.0)
        for e, g in sv("nmj_strength_per_pair").items():
            a, b = e.split(">")
            if a not in self.idx or b not in self.idx:
                continue
            inh = self._inhibitory(a, b)
            i, _ = self._nearest(a, b)
            w = g * n_em["nmj_strength_per_pair"][e] / (self._g_syn(inh) * 1000.0)
            self._syn(self.segs[self.idx[a]][i][0], self.segs[self.idx[b]][0][0], w, inh, "syn_nmj")

    # --- neuromodulators ---------------------------------------------------------------------------------------
    def _modulators(self, key):
        """(release cells x ligands, receptor cells x pairs, (ec50 per pair, ligand index per pair))."""
        st, sv = self.st, self.spec.v
        rate, ec50, gain = (sv(f"{key}_release_nM_per_s"), sv(f"{key}_ec50_nM"), sv(f"{key}_gain_pA"))
        ligs = list(rate.index)
        classes = set(st.cengen_classes)
        cls = [None if m else cengen_class(c, classes) for c, m in zip(self.cell_names, self.is_muscle)]
        n = len(self.cell_names)
        rel = np.zeros((n, len(ligs)))
        for k, lg in enumerate(ligs):
            for c in range(n):
                makes = (st.expr(lg, cls[c]) > 0) if key == "pep" else \
                    (not self.is_muscle[c] and lg in st.transmitter.get(self.cell_names[c], set()))
                rel[c, k] = rate[lg] if makes else 0.0
        pairs = [e for e in ec50.index if e.split(">")[0] in ligs]
        rec = np.zeros((n, len(pairs)))
        for j, e in enumerate(pairs):
            r = e.split(">")[1]
            for c in range(n):
                if st.expr(r, cls[c]) > 0:
                    rec[c, j] = gain[r]
        return rel, rec, (ec50[pairs].to_numpy(float), np.array([ligs.index(e.split(">")[0]) for e in pairs], int))

    # --- running -----------------------------------------------------------------------------------------------
    def _read(self, pv):
        pv.gather(self._buf)
        return self._buf.as_numpy().copy()

    def _out(self, v, ca, act, pha, ent, sex, eggs=0, exps=0, pumps=0, gc=None):
        return BrainToBody(t_ms=self.t, muscle_activation=act, pharynx_activation=np.full(len(PHARYNX_MUSCLES), pha),
                           enteric_activation=ent, sex_muscle_activation=np.full(len(SEX_MUSCLES), sex),
                           eggs_laid=eggs, expulsions=exps, pumps=pumps, v_mV=v, ca_uM=ca, gcamp_dff=gc)

    def reset(self) -> BrainToBody:
        self._ions()
        for c in self.stim:
            c.amp = 0.0
        self._amp[:] = 0.0
        if self.mact:
            for s, m in zip(self.soma, self.is_muscle):
                for seg in (s if m else ()):
                    seg.cai = 0.0                        # c302's initial concentration
        self.h.finitialize(V_INIT)
        if self.mact:
            for s, m in zip(self.soma, self.is_muscle):
                for seg in (s if m else ()):
                    seg.v = V_INIT_MUSCLE
            self.h.finitialize()                         # keeps each segment's v
        self.layers.reset()
        for name, (cells, pv, base, cur) in self._gt.items():
            cur[:] = 1.0
            pv.scatter(self.h.Vector(base))
        for m in self.mechs:
            m.reset()
        self.mech_out = {}
        self.t = 0.0
        return self._out(self._read(self._pv), self._read(self._pc) * self._ca_scale, np.zeros(len(BWM_NAMES)), 0.0,
                         np.zeros(len(ENTERIC_MUSCLES)), 0.0)

    def step(self, obs=None, dt_ms: float = 1.0) -> BrainToBody:
        n_int = int(round(dt_ms / DT_MS))
        assert n_int >= 1 and abs(n_int * DT_MS - dt_ms) < 1e-9, "dt_ms must be a multiple of 0.5 ms"
        o = vars(obs) if obs is not None else vars(default_observation(self.t))
        L = self.layers
        v = self._read(self._pv)
        I = L.sensory_current(o, dt_ms) + L.modulator_current(v, dt_ms) + L.homeostatic_current(v, dt_ms) \
            + self.extra_pA
        act_add, ovr = 0.0, {}
        if self.mechs:
            ctx = mech.Ctx(t_ms=self.t, obs=o, v=v, ca=self._read(self._pc) * self._ca_scale, names=self.cell_names,
                           is_muscle=self.is_muscle, outputs=dict(self.mech_out))
            g, outs = {}, {}
            for m in self.mechs:
                r = m.step(ctx, dt_ms)
                if "I_pA" in r:
                    I = I + r["I_pA"]
                if "act_add" in r:
                    act_add = act_add + r["act_add"]
                for k, x in r.get("g_scale", {}).items():
                    g[k] = g[k] * x if k in g else np.asarray(x, float)
                if "out" in r:
                    mech.merge(outs, r["out"])
                    ctx.outputs.update(r["out"])
            self._apply_g_scale(g)
            self.mech_out = outs
            ovr = {k: outs[k] for k in mech.OVERRIDES if k in outs}
        ch = np.flatnonzero(I != self._amp)
        for k in ch:
            self.stim[k].amp = I[k] / 1000.0             # pA -> nA
        self._amp[ch] = I[ch]
        for _ in range(n_int):
            self.h.fadvance()
        self.t += dt_ms
        v, ca = self._read(self._pv), self._read(self._pc) * self._ca_scale
        vb = np.array([v[i] if i >= 0 else np.nan for i in self.bwm])
        act = L.muscle_activation(np.nan_to_num(vb, nan=V_INIT), dt_ms)
        boost, ent, exps = L.defecation(dt_ms)
        act = np.clip(act + boost + act_add, 0.0, 1.0)
        pha, pumps = L.pharynx(o["head"].get("food_OD", 0.0), dt_ms)
        sex, eggs = L.egg_laying(self.t, dt_ms)
        L.metabolism(pumps, dt_ms)
        out = self._out(v, ca, act, pha, ent, sex, eggs, exps, pumps, L.gcamp(ca, dt_ms))
        for k, x in ovr.items():                         # a registered mechanism's output replaces the lumped one
            setattr(out, k, x)
        return out
