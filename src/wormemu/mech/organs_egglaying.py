"""Egg-laying circuit (PLAN row 15): sex muscles, uterus, uv1 feedback onto HSN.

Structure ported from Zhang, Schafer & Breitling 2010 BMC Syst Biol 4:81 (the egg-laying temporal pattern generator:
HSN is the command neuron, VC gives short inhibition, uv1 gives long inhibition after eggs pass; that paper's
equations are in its Additional Files, not opened: every number below is this module's, labelled) with the
mechanisms Collins et al. 2016 eLife 5:e21126 measured (uv1 releases tyramine after each egg and inhibits HSN through
LGC-55), Collins & Koelle 2013 J Neurosci 33:761 (the ERG channel UNC-103 keeps the vulval muscles subthreshold;
unc-103 loss makes egg laying hyperactive), Ravi et al. 2018 (vulval-muscle activity feeds back to HSN) and Medrano
& Collins 2023 Curr Biol (eggs accumulating in the uterus drive the circuit; sterile animals have no active state).

Cells. The 16 sex muscles (vm1, vm2, um1, um2 x A/P x L/R; Cook 2019 nodes, not brain cells) are one compartment
each with the Du, Crodelle et al. 2025 body-wall muscle membrane (inferred: vulval muscles also run on EGL-19 Ca
spikes) and the UNC-103 ERG current as Du's own Kr current at a vulval density (fitted, see egg_unc103_gkr_nS).
Cook's gaps join them (and VC03 to vm2), Cook's synapses reach them from HSN, VC, VA, VB, VD (GABA inhibitory, the
rest excitatory: VC and HSN are cholinergic in the project's transmitter map; organs_nrn.chem_synapse with the
body-wall NMJ's receptor classes when receptor kinetics run). uv1 is not a Cook node: it is one
lumped tyramine pool. HSN and VC are the brain's own cells.

Loop. Eggs enter the uterus at the rate from metabolism (ctx.outputs['egg_production_per_h'], row 20) or this
module's default; uterine stretch S = Hill(eggs) opens a cation conductance on vm1/vm2; 5-HT (SER-1, SER-7) and NLP-3
from B1's pools (mech.neuromod's compartment of HSN, at the vulva; brain_layers' well-mixed pools when neuromod is
absent) open the same conductance, at neuromod's SER-1, SER-7 and NPR-42 EC50s. With neuromod's amine_synaptic on
(nicholson; wneuro's toggle, off by default), vm2's 5-HT read adds the near-field excess at HSN's release sites onto
vm2 (neuromod.near_nM('serotonin', HSN); wbody2, 9 Nov, inbox 02:45) and vm1 keeps the pool alone; with it off
nothing changes. The vm Ca -> activation is row 12's
Boyle-Berri-Cohen integrator; an egg passes when the mean vm activation crosses egg_vm_act_on with an egg in the
uterus. Each egg releases uv1 tyramine, which opens LGC-55 (a Cl channel, row 7's rec_lgc55_* EC50, Hill and
reversal) on HSN; vm activity feeds a depolarising
current back to HSN. Nothing sets the active/inactive states: they come out of this loop or they do not.
The nested form `timer` is brain_layers.Layers.egg_laying verbatim (two-state timer, Waggoner 1998 durations).
The id egg_laying is brain_layers' id, so this module takes that toggle over. `egg_unc103=off` is the unc-103 null
(no Kr in the sex muscles).
Solver (`egg_g_solver`; wbody2, 9 Nov, A, inbox 01:45). implicit (default): the vm cation conductance and HSN's
LGC-55 conductance are wgc point processes (nmodl/wgc.mod) whose g is set each exchange step, so NEURON solves them
implicitly at its 0.5 ms step. Nested `explicit`: the code before, g (E - V) from V at the step's start held as a
current over the exchange step; it alternates above about 1.2 nS on HSN at 4-4.5 ms steps (weki, 01:13), inside
egg_lgc55_g_nS's range. The conductances' gating (stretch, occupancies, tyramine) updates once per exchange step in
both forms.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec
from wormemu.interface import SEX_MUSCLES

MECHANISMS = [
    ("egg_laying", "Egg-laying circuit: 16 sex muscles (Du membrane, UNC-103 as Kr), Cook HSN/VC/VA/VB/VD wiring, "
     "uterine stretch, 5-HT/NLP-3 from B1's pools, uv1 tyramine -> HSN LGC-55 (nested: two-state timer)",
     "organ", "circuit"),
    ("egg_unc103", "UNC-103 ERG K+ in the sex muscles at the vulval density (off: the unc-103 null)", "organ", "on"),
    ("egg_g_solver", "Egg-laying conductances (vm cation, HSN LGC-55) as NEURON point processes, implicit (nested "
     "explicit: g (E - V) from the step's start V as a current)", "organ", "implicit"),
]

ZHANG = "Zhang, Schafer, Breitling 2010 BMC Syst Biol 4:81"
COLLINS = "Collins et al. 2016 eLife 5:e21126"
CK13 = "Collins & Koelle 2013 J Neurosci 33:761"
MEDRANO = "Medrano & Collins 2023 Curr Biol"
DU = "Du, Crodelle et al. 2025 PLOS Comput Biol 21:e1012318"
_A = "vulval and uterine muscles"
VM = [n for n in SEX_MUSCLES if n.startswith("vm")]


def _s(pid, mech, unit, v, lo, hi, src, label="guessed", applies="egg-laying circuit", grain="class", notes=""):
    return Spec(pid, mech, unit, v, lo, hi, source=src, label=label, grain=grain, applies_to=applies, notes=notes)


SPECS = [
    _s("egg_production_per_h", "egg_laying", "eggs/h", 9.0, 2.0, 12.0, "STATE_OF_THE_ART item 45", "derived",
       "whole worm", "global", "eggs entering the uterus when metabolism (row 20) gives no rate: the measured peak "
       "laying rate (~9/h), which equals production at steady state"),
    _s("egg_uterus_init", "egg_laying", "eggs", 12.0, 5.0, 20.0, "general knowledge", applies="uterus",
       notes="eggs in utero at the start; a young adult holds ~10-15 (not opened tonight)"),
    _s("egg_stretch_half", "egg_laying", "eggs", 15.0, 8.0, 25.0, MEDRANO, applies="uterus",
       notes="eggs in utero at half stretch drive; guessed"),
    _s("egg_stretch_hill", "egg_laying", "1", 4.0, 1.0, 8.0, MEDRANO, applies="uterus", notes="guessed"),
    _s("egg_stretch_g_nS", "egg_laying", "nS", 0.6, 0.1, 2.0, MEDRANO, applies=_A,
       notes="stretch-opened cation conductance on vm1/vm2 at full stretch; guessed, set against this model's vm "
       "rheobase (0.3-0.5 nS of 0 mV conductance): a full uterus alone makes the vm fire weakly"),
    _s("egg_cation_erev_mV", "egg_laying", "mV", 0.0, -10.0, 10.0, "nonselective cation channel", "inferred", _A),
    _s("egg_5ht_g_nS", "egg_laying", "nS", 1.0, 0.1, 3.0, "Carnell 2005; Hobson 2006 (SER-1, SER-7 on vm)",
       applies=_A, notes="5-HT-opened cation conductance at full occupancy (Gq/Gs excitability as a conductance); "
       "occupancy = mean of SER-1 and SER-7 at neuromod's EC50s; guessed"),
    _s("egg_nlp3_g_nS", "egg_laying", "nS", 0.5, 0.0, 2.0, "Brewer et al. 2019 PLOS Genet", applies=_A,
       notes="NLP-3-opened cation conductance at full occupancy; NLP-3's vm receptor is unknown, neuromod's "
       "NLP-3/NPR-42 EC50 (Beets 2023) is used; guessed"),
    _s("egg_unc103_gkr_nS", "egg_unc103", "nS", 9.6, 3.2, 32.0, CK13, "inferred", _A,
       notes="UNC-103 as Du's Kr current; fitted: 3x Du's body-wall value, the smallest multiple that keeps an "
       "undriven vm at rest (numpy, 4 s: 1x fires 17 spikes, 3x rests at -35 mV), as UNC-103 keeps vm "
       "subthreshold (Collins & Koelle 2013)"),
    _s("egg_c_pF", "egg_laying", "pF", 22.0, 11.0, 44.0, DU, "inferred", _A, notes="Du's body-wall capacitance"),
    _s("egg_gap_nS_per_contact", "egg_laying", "nS", 0.35, 0.05, 0.35, "Liu et al. 2006 JBC 281:7881", "inferred",
       _A, notes="per Cook contact, the body-wall muscle value"),
    _s("egg_act_khalf_mM", "egg_laying", "mM", 0.014, 0.002, 0.05, "row 12 (bwm_act_khalf_mM)", "inferred", _A),
    _s("egg_act_hill", "egg_laying", "1", 2.0, 1.0, 4.0, "row 12 (bwm_act_hill)", "inferred", _A),
    _s("egg_act_tau_ms", "egg_laying", "ms", 100.0, 50.0, 200.0, "Boyle, Berri, Cohen 2012", "inferred", _A),
    _s("egg_vm_act_on", "egg_laying", "activation", 0.5, 0.3, 0.8, "this model", applies=_A,
       notes="mean vm activation at which an egg passes the vulva; guessed"),
    _s("egg_vm_act_off", "egg_laying", "activation", 0.2, 0.05, 0.4, "this model", applies=_A,
       notes="re-arm level after an egg; guessed"),
    _s("egg_ret_gain_pA", "egg_laying", "pA", 10.0, 0.0, 50.0, "Ravi et al. 2018 J Neurosci", applies="HSN",
       notes="depolarising current into each HSN per unit mean vm activation (retrograde feedback; sign "
       "measured, size guessed)"),
    _s("egg_uv1_tyr_uM_per_egg", "egg_laying", "uM", 5.0, 1.0, 20.0, COLLINS, applies="uv1",
       notes="tyramine added near HSN by uv1 per egg passed; guessed"),
    _s("egg_uv1_tyr_tau_s", "egg_laying", "s", 60.0, 20.0, 1200.0, ZHANG, applies="uv1",
       notes="uv1 tyramine clearance; Zhang 2010 makes uv1 the long (cluster-ending) inhibition; guessed"),
    _s("egg_lgc55_g_nS", "egg_laying", "nS", 1.0, 0.1, 5.0, COLLINS, applies="HSN",
       notes="LGC-55 Cl conductance on each HSN at full occupancy (EC50, Hill and reversal: row 7's rec_lgc55_*); "
       "guessed"),
]

# the nested timer reuses brain_layers' own egg specs (read from brain.layers.p when present)
_OLD = {"egg_active_min": 2.0, "egg_inactive_min": 20.0, "egg_rate_active_per_min": 2.0, "egg_vm_dur_ms": 1000.0}
FORMS = ("circuit", "timer", "off")


def defaults():
    return {s.id: s.template for s in SPECS}


def _hill(x, k, n):
    x = np.maximum(x, 0.0)
    return x ** n / (x ** n + k ** n)


class Mech:
    """Builds the 16 sex muscles in the brain's simulator and steps the uterus, uv1 and the HSN feedback."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        self.form = toggles.get("egg_laying", "circuit")
        if self.form == "on":
            self.form = "circuit"
        assert self.form in FORMS, self.form
        self.unc103 = toggles.get("egg_unc103", "on") != "off"
        self.solver = toggles.get("egg_g_solver", "implicit")
        assert self.solver in ("implicit", "explicit"), self.solver
        q = defaults()
        q.update(_OLD)
        q.update({k: v for k, v in (getattr(brain.layers, "p", {}) or {}).items() if k in _OLD})
        q.update({k: float(v) for k, v in (params or {}).items() if np.isscalar(v)})
        self.q = q
        idx = brain.idx
        self.hsn = np.array([idx[c] for c in ("HSNL", "HSNR") if c in idx], int)
        self.n_syn = self.n_gap = 0
        if self.form == "circuit":
            self._pools()
            self._build()
        self.reset()

    def _pools(self):
        """neuromod's 5-HT (SER-1, SER-7) and NLP-3 (NPR-42) EC50s (nM) and row 7's LGC-55 (EC50 uM, Hill, reversal),
        from the brain's spec when it has one; where 5-HT and NLP-3 sit in brain_layers' pools (the fallback)."""
        from wormemu import mech
        from wormemu.mech import neuromod, receptors
        b = self.brain
        p = {s.id: s.template for s in neuromod.SPECS + receptors.SPECS}
        if getattr(b, "spec", None) is not None:
            for m in (neuromod, receptors):
                p.update({k: v for k, v in mech.params_for(m, b.spec).items() if np.isscalar(v)})
        self.ec5 = np.array([float(p["ma_ec50_serotonin_ser-1_nM"]), float(p["ma_ec50_serotonin_ser-7_nM"])])
        self.ec3 = float(p["pep_ec50_nlp-3_npr-42_nM"])
        self.lgc = tuple(float(p[f"rec_lgc55_{k}"]) for k in ("ec50_uM", "hill", "erev_mV"))
        self.nm = None                                     # the neuromod Mech, looked up at the first step
        self.i5 = self.i3 = None
        sv = getattr(getattr(b, "spec", None), "v", None)
        for attr, sid, lig in (("i5", "ma_release_nM_per_s", "serotonin"), ("i3", "pep_release_nM_per_s", "nlp-3")):
            try:
                setattr(self, attr, list(sv(sid).index).index(lig))
            except (KeyError, ValueError, TypeError, AttributeError):
                pass

    def _build(self):
        from wormemu.mech import muscle_bwm as mb, organs_nrn
        b, q = self.brain, self.q
        h = b.h
        organs_nrn.load_organ_mods(h)
        vals = getattr(b.spec, "values", {}) or {}
        qb = {s.id: (float(vals[s.id]) if s.id in vals and np.isscalar(vals[s.id]) else s.template) for s in mb.SPECS}
        self.sec, self.clamp, self.gvm, self.glgc = {}, [], [], []
        for n in SEX_MUSCLES:
            sec = h.Section(name=f"sex_{n}")
            sec.nseg, sec.L, sec.diam = 1, 20.0, 5.0              # BAAIWorm's muscle cylinder
            sec.insert("du_bwm")
            area = organs_nrn.area_um2(sec)
            mb.configure(sec, qb, area)
            sec.cm = q["egg_c_pF"] * 100.0 / area
            sec(0.5).du_bwm.gkr = q["egg_unc103_gkr_nS"] if self.unc103 else 0.0
            if self.solver == "explicit":
                c = h.IClamp(sec(0.5))
                c.delay, c.dur, c.amp = 0.0, 1e12, 0.0
                self.clamp.append(c)
            elif n in VM:
                pp = h.wgc(sec(0.5))
                pp.e, pp.g = q["egg_cation_erev_mV"], 0.0
                self.gvm.append(pp)
            self.sec[n] = sec
        if self.solver == "implicit":
            for i in self.hsn:
                pp = h.wgc(b.soma[i](0.5))
                pp.e, pp.g = self.lgc[2], 0.0
                self.glgc.append(pp)
        st, nm, mine = b.st, b.st.names, set(SEX_MUSCLES)
        g = q["egg_gap_nS_per_contact"] / 1000.0
        for i, j, n in st.gap:
            a, c = nm[i], nm[j]
            if a in mine and c in mine:
                b._gap(self.sec[a](0.5), self.sec[c](0.5), n * g, "gap_sex")
            elif (a in mine) != (c in mine) and (a in b.idx or c in b.idx):
                cell, mus = (a, c) if c in mine else (c, a)
                b._gap(b.soma[b.idx[cell]](0.5), self.sec[mus](0.5), n * g, "gap_sex")
            else:
                continue
            self.n_gap += 1
        g_nmj = float(np.median(b.spec.v("nmj_strength_per_pair").to_numpy(float)))
        self.wsyn = []
        for i, j, n in st.chem:
            a, c = nm[i], nm[j]
            if c in mine and a in b.idx:
                inh = "gaba" in st.transmitter.get(a, set())
                self.wsyn += organs_nrn.chem_synapse(b, a, self.sec[c](0.5), g_nmj * n, inh, "syn_sex", muscle=True)
                self.n_syn += 1
        k = len(SEX_MUSCLES)
        self._pca, self._pv = h.PtrVector(k), h.PtrVector(k)
        for x, n in enumerate(SEX_MUSCLES):
            self._pca.pset(x, self.sec[n](0.5).du_bwm._ref_cad)
            self._pv.pset(x, self.sec[n](0.5)._ref_v)
        self._buf = h.Vector(k)
        self.is_vm = np.array([n in VM for n in SEX_MUSCLES])
        self.is_vm2 = np.array([n.startswith("vm2") for n in SEX_MUSCLES])
        self.gvm_is_vm2 = [n.startswith("vm2") for n in SEX_MUSCLES if n in VM]          # self.gvm order (implicit)

    def reset(self):
        from wormemu.mech.muscle_bwm import INIT
        q = self.q
        self.U = q["egg_uterus_init"]
        self.tyr = 0.0
        self.act = np.zeros(len(SEX_MUSCLES))
        self.in_egg, self.eggs_total = False, 0
        self.active, self.t_next, self.vm_t = False, 0.0, -1e9   # the timer form's state (Layers' own start)
        for sec in getattr(self, "sec", {}).values():
            seg = sec(0.5)
            seg.v = INIT["v"]
            for k, x in INIT.items():
                if k != "v":
                    setattr(seg.du_bwm, k, x)
        for c in getattr(self, "clamp", []):
            c.amp = 0.0
        for pp in getattr(self, "gvm", []) + getattr(self, "glgc", []):
            pp.g = 0.0

    def _read(self, pv):
        pv.gather(self._buf)
        return self._buf.as_numpy().copy()

    def timer(self, t_ms, dt):
        """brain_layers.Layers.egg_laying, verbatim (its rng): (sex muscle activation level, eggs laid)."""
        q, rng = self.q, self.brain.layers.rng
        if t_ms >= self.t_next:
            self.active = not self.active
            m = q["egg_active_min"] if self.active else q["egg_inactive_min"]
            self.t_next = t_ms + rng.exponential(m * 60000.0)
        laid = 0
        if self.active and rng.random() < q["egg_rate_active_per_min"] * dt / 60000.0:
            laid, self.vm_t = 1, t_ms
        return (1.0 if t_ms - self.vm_t < q["egg_vm_dur_ms"] else 0.0), laid

    def concentrations(self):
        """(5-HT nM, NLP-3 nM) at the vulva: neuromod's compartment of HSN, else brain_layers' well-mixed pools."""
        from wormemu.mech import neuromod as nmod
        if self.nm is None:
            self.nm = next((m for m in getattr(self.brain, "mechs", None) or [] if isinstance(m, nmod.Mech)), False)
        nm, c5, c3 = self.nm, None, None
        if nm and len(self.hsn):
            if nm.on.get(nmod.A):
                c5 = float(nm.ma.nM()[nmod.AMINES.index("serotonin"), nm.ma_comp[self.hsn[0]]])
            if nm.on.get(nmod.P) and "nlp-3" in nmod.PRECURSORS:
                c3 = float(nm.pep.nM()[nmod.PRECURSORS.index("nlp-3"), nm.pep_comp[self.hsn[0]]])
        L = self.brain.layers
        if c5 is None and self.i5 is not None and getattr(L, "ma_c", None) is not None:
            c5 = float(L.ma_c[self.i5])
        if c3 is None and self.i3 is not None and getattr(L, "pep_c", None) is not None:
            c3 = float(L.pep_c[self.i3])
        return c5 or 0.0, c3 or 0.0

    def occupancy(self):
        """(5-HT occupancy on vm, NLP-3 occupancy on vm)."""
        c5, c3 = self.concentrations()
        return float(np.mean(c5 / (c5 + self.ec5))), c3 / (c3 + self.ec3)

    def near_5ht(self):
        """neuromod's near-field 5-HT excess (nM) at vm2 from HSN's release sites; None under amine_synaptic off (or
        with no neuromod or no HSN). Call after concentrations(), which finds the neuromod Mech."""
        nm = self.nm
        if not nm or not len(self.hsn) or getattr(nm, "synaptic", "off") == "off":
            return None
        return nm.near_nM("serotonin", self.hsn)

    def step(self, ctx, dt_ms):
        k = len(SEX_MUSCLES)
        if self.form == "off":
            return {"out": {"eggs_laid": 0, "sex_muscle_activation": np.zeros(k)}}
        if self.form == "timer":
            a, laid = self.timer(ctx.t_ms + dt_ms, dt_ms)        # Layers.egg_laying runs at the step's end time
            return {"out": {"eggs_laid": laid, "sex_muscle_activation": np.full(k, a)}}
        q = self.q
        v, ca = self._read(self._pv), self._read(self._pca)
        rate = float(ctx.outputs.get("egg_production_per_h", q["egg_production_per_h"]))
        self.U += rate * dt_ms / 3.6e6
        S = float(_hill(self.U, q["egg_stretch_half"], q["egg_stretch_hill"]))
        o5, o3 = self.occupancy()
        g = q["egg_stretch_g_nS"] * S + q["egg_5ht_g_nS"] * o5 + q["egg_nlp3_g_nS"] * o3
        near = self.near_5ht()
        if near is None:                          # amine_synaptic off: every vm reads the pool (the code before)
            o5_vm2, g2, gv = o5, g, g
        else:                                     # vm2 reads the pool plus HSN's near field; vm1 the pool
            c5 = self.concentrations()[0] + near
            o5_vm2 = float(np.mean(c5 / (c5 + self.ec5)))
            g2 = q["egg_stretch_g_nS"] * S + q["egg_5ht_g_nS"] * o5_vm2 + q["egg_nlp3_g_nS"] * o3
            gv = np.where(self.is_vm2, g2, g)
        if self.solver == "explicit":
            i_vm = np.where(self.is_vm, gv * (q["egg_cation_erev_mV"] - v), 0.0)       # pA
            for c, x in zip(self.clamp, i_vm):
                c.amp = x / 1000.0                                                     # pA -> nA
        else:
            for pp, x in zip(self.gvm, self.gvm_is_vm2):
                pp.g = (g2 if x else g) / 1000.0                                       # nS -> uS
        target = _hill(ca, q["egg_act_khalf_mM"], q["egg_act_hill"])
        self.act += (target - self.act) * min(1.0, dt_ms / q["egg_act_tau_ms"])
        a_vm = float(np.mean(self.act[self.is_vm]))
        laid = 0
        if not self.in_egg and a_vm > q["egg_vm_act_on"] and self.U >= 1.0:
            laid, self.in_egg = 1, True
            self.U -= 1.0
            self.eggs_total += 1
            self.tyr += q["egg_uv1_tyr_uM_per_egg"]
        elif self.in_egg and a_vm < q["egg_vm_act_off"]:
            self.in_egg = False
        self.tyr -= self.tyr * min(1.0, dt_ms / (1000.0 * q["egg_uv1_tyr_tau_s"]))
        I = np.zeros(len(ctx.names))
        if len(self.hsn):
            ec50, hl, erev = self.lgc
            occ = float(_hill(self.tyr, ec50, hl))
            I[self.hsn] = q["egg_ret_gain_pA"] * a_vm
            if self.solver == "explicit":
                I[self.hsn] += q["egg_lgc55_g_nS"] * occ * (erev - ctx.v[self.hsn])
            else:
                for pp in self.glgc:
                    pp.g = q["egg_lgc55_g_nS"] * occ / 1000.0
        return {"I_pA": I, "out": {"eggs_laid": laid, "sex_muscle_activation": self.act.copy(),
                                   "eggs_total": self.eggs_total, "egg_uterus": self.U, "egg_stretch": S,
                                   "uv1_tyramine_uM": self.tyr, "egg_5ht_occ": o5, "egg_nlp3_occ": o3,
                                   "egg_5ht_occ_vm2": o5_vm2, "egg_5ht_near_nM": 0.0 if near is None else near,
                                   "egg_vm_v_mV": v[self.is_vm], "egg_vm_ca_mM": ca[self.is_vm],
                                   "egg_vm_act": a_vm}}
