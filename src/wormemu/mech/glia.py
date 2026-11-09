"""Glia (PLAN row 11): glial cells and the spaces they control, as compartments with state.

No C. elegans glial model with numbers exists (PORT_SOURCES_ORGANS O5): the structure is ported from the C. elegans
papers below and the clearance numbers are borrowed from mammalian Kir4.1 work, labelled inferred.

  glia_cells    the 6 GLR and 4 CEPsh glia, Cook et al. 2019 nodes, as passive cells (no glial membrane is recorded:
                capacitance, leak and resting level guessed) joined by Cook's gaps to RME, CEP, RIP, ADF, ASI and the
                head muscles (GLR-RME and GLR-muscle gaps: Meng et al. 2016 eLife, PMC5083064) at the brain's own
                per-contact neuronal gap (inferred: glial innexins are not resolved). Chemical synapses onto glia are
                not modelled (no glial receptor for them is identified).
  glia_kbuffer  extracellular K+ at the amphid sensory endings, one compartment per side inside the amphid sheath.
                Each amphid neuron's depolarisation above its own resting level (the mean over the first
                GLIA_V0_MS) changes its K+ leak current into it, g_K ((v - v0) - dE_K) (a raised E_K cuts the efflux:
                the same leak current the module injects); glial Kir4.1-type uptake and diffusion to the
                bulk clear it, the two time constants guessed from a mouse model's [K+]o decay (control 3.4-4 s,
                Kir4.1 inhibited 4.2-6 s; KIR below: simulated, cross-species); the K+ reversal shift (RT/F) ln(Ko / Ko_bath) drives
                each amphid neuron on that side through its K+ leak g_K (pA). g_K is the K+ share
                (glia_k_leak_frac) of the neuron's own passive leak, so the shift moves a cell by at most that
                share of dE_K and the loop cannot run away (7 Nov: a separate 0.2 nS, larger than the amphid
                neurons' whole 0.07-0.09 nS leak, drove a cell to -384 mV); Ko is floored at 1 mM, the hard K+
                window's floor. A brain without morphology (the unit tests) uses glia_k_gleak_nS per neuron.
  glia_k_load   leak (default, the form above) | channels: Sibille, Dao Duc, Holcman & Rouach 2015 PLoS Comput Biol
                11:e1004137 (PMC4380507, full text; docs/worm/night/wbody2/lit_glia_port.md), d K0 / dt = iK - 2
                ipumpN - 2 ipumpA + iKir (eq. 25): the neuron's gated K+ current, not its leak, loads K0, and its E_K
                follows K0 (eq. 8). Here each amphid neuron's load is the sum of ik x area over its K+ sections (every
                K+ mod reads ek and writes ik) minus its mean over the reference window, and the E_K shift is set on
                those sections' ek (nothing injected). The source balances rest with tuned leaks and pumps; here
                that balance is the subtracted resting ik (the fitted leaks already hold the resting pump, as in
                pumps.py), and the activity-dependent pump uptake is in the clearance constants.
  glia_v0_window  first (default, 0-1 s) | settled (1-2 s, after the start-up from V_INIT): the window the resting
                v0 (leak) or resting ik (channels) is the mean over. 9 Nov 2026 (wbody2, glia_v0_probe): the network
                drifts 3 mV (median) off the 0-1 s mean by 19-20 s and 0.2-0.3 mV off the 1-2 s mean.
  glia_kcc3     Singhvi et al. 2016 Cell 165:936: amphid sheath KCC-3 sits only in the microdomain around AFD's
                receptive ending and sets its Cl-; Cl- inhibits AFD's receptor guanylyl cyclase GCY-8. Here one Cl-
                excess compartment per AFD: KCC-3 adds Cl- at a rate scaled by its thermodynamic drive
                1 - Ko Clo / (K Cl)_AMsh relative to rest (so K+ rising at the ending slows it), cleared with the
                microdomain time constant; GCY-8 activity 1 / (1 + Clo / IC50) relative to wild-type rest is
                out['afd_gc_scale'] = {'AFDL': x, 'AFDR': y}: 1 at wild-type rest, above 1 in the kcc-3 null, for
                the AFD cyclase cascade (B3's senses) to multiply its catalytic rate by. Until a reader exists this
                arm changes no current.

Forms (nested): glia_cells on | off; glia_kbuffer kir (default) | null (no glial uptake, diffusion only: the Kir4.1
null) | fixed (no compartment: Ko stays at the bath, no current); glia_k_load leak (default) | channels;
glia_v0_window first (default) | settled; glia_kcc3 on | null (no KCC-3 flux) | fixed (no state, scale 1). brain_layers' lumped `glia` gain (off) stays as the simplest form and is not claimed here.
Validity: K+ and Cl- are well mixed within each ending compartment; no osmotic or volume change; the amphid neurons'
K+ load is a linear leak estimate (leak) or their channels' own K+ currents (channels), from the whole cell into its
side's ending in both forms; AFD-AWC cross-talk through one sheath (Ray et
al. 2024 Cell Rep) is not modelled.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import AMPHID, Spec

MECHANISMS = [
    ("glia_cells", "GLR (6) and CEPsh (4) glia as passive cells with Cook's gaps to RME, CEP, RIP, ADF, ASI and the "
     "head muscles", "glia", "on"),
    ("glia_kbuffer", "Extracellular K+ at each side's amphid endings, cleared by glial Kir4.1-type uptake; the K+ "
     "reversal shift drives the amphid neurons (nested: null = no glial uptake, fixed = no compartment)", "glia",
     "kir"),
    ("glia_k_load", "The amphid neurons' K+ load into their ending: a linear leak estimate with the E_K shift injected "
     "(leak), or their own gated K+ currents from rest with E_K on their K+ channels following the ending's K+ "
     "(channels: Sibille et al. 2015 eq. 25)", "glia", "leak"),
    ("glia_v0_window", "The amphid neurons' resting reference window: the first second (first) or 1-2 s, after the "
     "start-up (settled)", "glia", "first"),
    ("glia_kcc3", "Amphid sheath KCC-3 Cl- microdomain at AFD's ending; Cl- inhibits GCY-8: out['afd_gc_scale'] "
     "(nested: null = kcc-3, fixed = scale 1)", "glia", "on"),
]

GLIA_CELLS = ["GLRDL", "GLRDR", "GLRL", "GLRR", "GLRVL", "GLRVR", "CEPshDL", "CEPshDR", "CEPshVL", "CEPshVR"]
GLIA_V0_MS = 1000.0
GLIA_V0_WINDOWS = {"first": (0.0, GLIA_V0_MS), "settled": (GLIA_V0_MS, 2.0 * GLIA_V0_MS)}
SINGHVI = "Singhvi et al. 2016 Cell 165:936"
KIR = "Sibille, Dao Duc, Holcman & Rouach 2015 PLoS Comput Biol 11:e1004137 (PMC4380507, opened), simulations of a " \
      "mouse hippocampal neuron-astrocyte model: [K+]o decay 3.4 s (single stimulus) and 4 s (tetanus), Kir4.1 " \
      "inhibited 4.2 s and 6 s (Fig. 4B, F)"
MENG = "Meng et al. 2016 eLife (PMC5083064)"
F_C_PER_MOL = 96485.0
KO_FLOOR_MM = 1.0           # the hard K+ window's floor (scripts/worm/ranges/rules.yaml, 1-30 mM)


def _s(pid, mech, unit, v, lo, hi, src, label="guessed", applies="amphid endings", grain="class", notes=""):
    return Spec(pid, mech, unit, v, lo, hi, source=src, label=label, grain=grain, applies_to=applies, notes=notes)


SPECS = [
    _s("glia_c_pF", "glia_cells", "pF", 20.0, 5.0, 50.0, MENG, applies="GLR, CEPsh",
       notes="glial capacitance; no recording; guessed from a ~2000 um2 sheet at 1 uF/cm2 upper bound"),
    _s("glia_g_leak_nS", "glia_cells", "nS", 1.0, 0.2, 5.0, MENG, applies="GLR, CEPsh",
       notes="glial leak; no recording; guessed"),
    _s("glia_e_leak_mV", "glia_cells", "mV", -70.0, -85.0, -50.0, "glia rest near E_K (mammalian astrocytes -80 to "
       "-90 mV)", "inferred", "GLR, CEPsh", notes="no C. elegans glial recording; cross-species, bounded"),
    _s("glia_gap_nS_per_contact", "glia_cells", "nS", 0.2236, 0.05, 0.5, "the brain's gap_strength_per_pair",
       "inferred", "GLR, CEPsh gaps", notes="the brain's per-EM-contact neuronal gap (read from the ledger when "
       "present): glial innexins unresolved"),
    _s("glia_k_bath_mM", "glia_kbuffer", "mM", 5.0, 2.5, 10.0, "C. elegans recording saline (5 mM KCl, Goodman et "
       "al. 1998)", "inferred", notes="resting Ko at the endings; the pseudocoelomic K+ is unmeasured"),
    _s("glia_k_volume_um3", "glia_kbuffer", "um3", 100.0, 10.0, 1000.0, "amphid ultrastructure (Perkins et al. "
       "1986), not measured as a volume", notes="extracellular volume around one side's 12 amphid endings inside "
       "the sheath; guessed (a 20 nm cleft over ~100 um2 is 2 um3; the open amphid channel is much larger)"),
    _s("glia_k_gleak_nS", "glia_kbuffer", "nS", 0.2, 0.05, 1.0, "this model", applies="amphid neurons",
       notes="K+ leak per amphid neuron when the brain has no morphology (unit tests only); guessed"),
    _s("glia_k_leak_frac", "glia_kbuffer", "1", 0.5, 0.1, 1.0, "this model", applies="amphid neurons",
       notes="K+ share of each amphid neuron's own passive leak: sets the activity K+ load and the reversal-shift "
       "current; guessed (neuronal leak is mostly K+ through K2P channels, share not measured in the worm)"),
    _s("glia_kir_tau_s", "glia_kbuffer", "s", 12.6, 2.0, 30.0, KIR, "guessed", "amphid sheath",
       notes="glial uptake alone; the source's pairs give 1 / (1/control - 1/inhibited) = 17.9 s (single) and 12.0 s "
       "(tetanus), the template 12.6 s inside (it came from a misread 4.2 / 6.3 s pair, value kept: catalog audit "
       "6 Nov); with glia_k_diff_tau_s the constants alone clear in 4.2 s, the source's inhibited single-stimulus "
       "decay, not its 3.4-4 s control"),
    _s("glia_k_diff_tau_s", "glia_kbuffer", "s", 6.3, 3.0, 15.0, KIR, "guessed", "amphid endings",
       notes="clearance without glial uptake, at least the source's Kir4.1-inhibited decay (4.2-6 s); template 6.3 s "
       "kept (catalog audit 6 Nov)"),
    _s("glia_rt_f_mV", "glia_kbuffer", "mV", 25.26, 24.4, 26.1, "RT/F at 20 C (15-30 C range)", "derived",
       grain="global", applies="whole worm"),
    _s("glia_cl_bath_mM", "glia_kcc3", "mM", 150.0, 50.0, 160.0, "C. elegans recording saline (~150 mM Cl-)",
       "inferred", "AFD ending", notes="Cl- outside the microdomain; the pseudocoelomic Cl- is unmeasured"),
    _s("glia_kcc3_dcl_mM", "glia_kcc3", "mM", 20.0, 2.0, 60.0, SINGHVI, applies="AFD ending",
       notes="Cl- excess KCC-3 holds in AFD's microdomain at rest; no measurement (the paper's Cl- levels are not in "
       "the free summary); guessed"),
    _s("glia_cl_tau_s", "glia_kcc3", "s", 4.2, 0.7, 6.3, KIR, "guessed", "AFD ending",
       notes="microdomain clearance, taken as the K+ recovery (O5's suggestion; the source's control is 3.4-4 s, the "
       "template 4.2 s kept, catalog audit 6 Nov)"),
    _s("glia_amsh_kcl_mM2", "glia_kcc3", "mM2", 2800.0, 1000.0, 6000.0, "KCC thermodynamics (K x Cl in = out at "
       "equilibrium)", applies="AMsh", notes="[K+]i x [Cl-]i in the sheath (e.g. 140 x 20); guessed"),
    _s("glia_gcy8_cl_ic50_mM", "glia_kcc3", "mM", 60.0, 10.0, 300.0, SINGHVI + " (PMC4860081, opened), Results and "
       "Fig. 5D: GCY-8 cyclase activity in HEK293T membrane fractions, NH4Cl titration, 30 C", "measured",
       applies="AFD GCY-8", notes="Cl- at half GCY-8 inhibition, Hill 1: 'Cl- ions ... are potent inhibitors of GCY-8 "
       "cyclase activity ... with an IC50 of ~60mM' (heterologous, no interval); was 100 guessed, filled to 60 by "
       "the catalog audit 6 Nov, module aligned 8 Nov (wbody2); range kept (guessed)"),
]


def defaults():
    return {s.id: s.template for s in SPECS}


def _side(name):
    return 0 if name.endswith("L") else 1


class Mech:
    """Builds the GLR and CEPsh cells and steps the amphid K+ and AFD Cl- compartments."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        self.cells_on = toggles.get("glia_cells", "on") != "off"
        self.kb = toggles.get("glia_kbuffer", "kir")
        self.kcc = toggles.get("glia_kcc3", "on")
        self.kb = "kir" if self.kb == "on" else self.kb
        assert self.kb in ("kir", "null", "fixed", "off") and self.kcc in ("on", "null", "fixed", "off")
        self.kload = toggles.get("glia_k_load", "leak")
        self.win = GLIA_V0_WINDOWS[toggles.get("glia_v0_window", "first")]
        assert self.kload in ("leak", "channels")
        q = defaults()
        q.update({k: float(v) for k, v in (params or {}).items() if np.isscalar(v)})
        sp = getattr(brain, "spec", None)
        if sp is not None and getattr(sp, "led", None) is not None and "glia_gap_nS_per_contact" not in (params or {}):
            try:
                q["glia_gap_nS_per_contact"] = float(np.median(sp.v("gap_strength_per_pair").to_numpy(float)))
            except (KeyError, ValueError):
                pass
        self.q = q
        amph = [c for c in sorted(AMPHID) if c in brain.idx]
        self.amph = np.array([brain.idx[c] for c in amph], int)
        self.amph_side = np.array([_side(c) for c in amph], int)
        self.afd = [(c, brain.idx[c]) for c in ("AFDL", "AFDR") if c in brain.idx]
        cells = getattr(brain, "cells", None)
        if cells:   # nS: g_pas (S/cm2) x area (um2) x 1e-8 cm2/um2 x 1e9 nS/S
            g = [10.0 * sum(seg.pas.g * seg.area() for sec in cells[i].all for seg in sec) for i in self.amph]
            self.gk = q["glia_k_leak_frac"] * np.array(g, float)
        else:
            self.gk = np.full(len(self.amph), q["glia_k_gleak_nS"])
        self.ksec, self.ek0 = [], None
        if self.kload == "channels":
            assert cells, "glia_k_load=channels needs the cells' sections"
            self.ksec = [[s for s in cells[i].all if brain.h.ismembrane("k_ion", sec=s)] for i in self.amph]
            self.kseg = [[(seg, seg.area()) for s in ss for seg in s] for ss in self.ksec]
        self.sec, self.n_gap = {}, 0
        if self.cells_on:
            self._build()
        self.reset()

    def _build(self):
        b, q = self.brain, self.q
        h = b.h
        st, nm = b.st, b.st.names
        for n in GLIA_CELLS:
            sec = h.Section(name=f"glia_{n}")
            sec.nseg, sec.L, sec.diam = 1, 10.0, 5.0
            area = sec(0.5).area()
            sec.cm = q["glia_c_pF"] * 100.0 / area                     # pF over um2 -> uF/cm2
            sec.insert("pas")
            sec.g_pas = q["glia_g_leak_nS"] * 0.1 / area               # nS over um2 -> S/cm2
            sec.e_pas = q["glia_e_leak_mV"]
            self.sec[n] = sec
        g = q["glia_gap_nS_per_contact"] / 1000.0                      # nS -> uS
        mine = set(GLIA_CELLS)
        for i, j, n in st.gap:
            a, c = nm[i], nm[j]
            if a in mine and c in mine:
                sa, sb = self.sec[a](0.5), self.sec[c](0.5)
            elif a in mine and c in b.idx:
                sa, sb = self.sec[a](0.5), b.segs[b.idx[c]][0][0]
            elif c in mine and a in b.idx:
                sa, sb = self.sec[c](0.5), b.segs[b.idx[a]][0][0]
            else:
                continue
            b._gap(sa, sb, n * g, "gap_glia")
            self.n_gap += 1

    def reset(self):
        q = self.q
        self.ko = np.full(2, q["glia_k_bath_mM"])
        self.dcl = np.full(2, q["glia_kcc3_dcl_mM"] if self.kcc == "on" else 0.0)
        self.v0_sum = np.zeros(len(self.amph))
        self.v0_n = 0
        self.v0 = None
        self.load_last = np.zeros(2)
        if self.ek0 is not None:
            for ss, e0 in zip(self.ksec, self.ek0):
                for s, e in zip(ss, e0):
                    s.ek = e
        for sec in self.sec.values():
            sec(0.5).v = q["glia_e_leak_mV"]

    def _gcy8(self, dcl):
        q = self.q
        return 1.0 / (1.0 + (q["glia_cl_bath_mM"] + dcl) / q["glia_gcy8_cl_ic50_mM"])

    def step(self, ctx, dt_ms):
        q = self.q
        out = {}
        I = None
        dt = dt_ms / 1000.0
        if self.kb not in ("fixed", "off") and len(self.amph):
            if self.kload == "leak":
                x = np.asarray(ctx.v, float)[self.amph]
            else:   # pA: each cell's gated K+ current, mA/cm2 x um2 x 10
                if self.ek0 is None:
                    self.ek0 = [[s.ek for s in ss] for ss in self.ksec]
                x = np.array([10.0 * sum(seg.ik * a for seg, a in sg) for sg in self.kseg])
            t0, t1 = self.win
            if self.v0 is None:
                if ctx.t_ms + 0.5 * dt_ms >= t0:
                    self.v0_sum += x
                    self.v0_n += 1
                if ctx.t_ms + dt_ms >= t1:
                    self.v0 = self.v0_sum / self.v0_n
                load = np.zeros(2)
            else:
                if self.kload == "leak":
                    dek0 = q["glia_rt_f_mV"] * np.log(self.ko / q["glia_k_bath_mM"])[self.amph_side]
                    ipa = self.gk * ((x - self.v0) - dek0)                              # pA: K+ leak change from rest
                else:
                    ipa = x - self.v0                                                   # pA: K+ current change from rest
                load = np.bincount(self.amph_side, ipa, minlength=2) * 1e6 / F_C_PER_MOL / q["glia_k_volume_um3"]
            k = 1.0 / q["glia_k_diff_tau_s"] + (1.0 / q["glia_kir_tau_s"] if self.kb == "kir" else 0.0)
            e = np.exp(-k * dt)
            kb = q["glia_k_bath_mM"]
            self.ko = kb + (self.ko - kb) * e + load / k * (1.0 - e)                   # mM
            self.ko = np.maximum(self.ko, KO_FLOOR_MM)
            dek = q["glia_rt_f_mV"] * np.log(self.ko / kb)                             # mV
            self.load_last = load
            if self.kload == "leak":
                I = np.zeros(len(ctx.v))
                I[self.amph] = self.gk * dek[self.amph_side]                           # nS x mV = pA
            else:
                for ss, e0, sd in zip(self.ksec, self.ek0, self.amph_side):
                    for s, e in zip(ss, e0):
                        s.ek = e + dek[sd]
            out.update(amphid_k_mM=self.ko.copy(), amphid_ek_shift_mV=dek)
        if self.kcc not in ("fixed", "off"):
            if self.kcc == "on":
                P, clb, kb = q["glia_amsh_kcl_mM2"], q["glia_cl_bath_mM"], q["glia_k_bath_mM"]
                d_rest = 1.0 - kb * (clb + q["glia_kcc3_dcl_mM"]) / P
                drive = (1.0 - self.ko * (clb + self.dcl) / P) / d_rest
                src = q["glia_kcc3_dcl_mM"] / q["glia_cl_tau_s"] * np.maximum(drive, 0.0)       # mM/s
            else:
                src = np.zeros(2)
            k = 1.0 / q["glia_cl_tau_s"]
            e = np.exp(-k * dt)
            self.dcl = self.dcl * e + src / k * (1.0 - e)
            s = self._gcy8(self.dcl) / self._gcy8(q["glia_kcc3_dcl_mM"])
            out.update(afd_gc_scale={c: float(s[_side(c)]) for c, _ in self.afd}, afd_cl_excess_mM=self.dcl.copy())
        if self.sec:
            out["glia_v_mV"] = np.array([self.sec[n](0.5).v for n in GLIA_CELLS])
        r = {"out": out}
        if I is not None:
            r["I_pA"] = I
        return r
