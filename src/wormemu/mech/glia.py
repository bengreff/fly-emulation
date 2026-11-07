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
                GLIA_V0_MS) is an extra K+ efflux g_K (v - v0) into it; glial Kir4.1-type uptake and diffusion to the
                bulk clear it, the two time constants set from the mammalian Kir4.1 recovery (wild type 4.2 s,
                glial knockout 6.3 s; inferred, cross-species); the K+ reversal shift (RT/F) ln(Ko / Ko_bath) drives
                each amphid neuron on that side through its K+ leak g_K (pA).
  glia_kcc3     Singhvi et al. 2016 Cell 165:936: amphid sheath KCC-3 sits only in the microdomain around AFD's
                receptive ending and sets its Cl-; Cl- inhibits AFD's receptor guanylyl cyclase GCY-8. Here one Cl-
                excess compartment per AFD: KCC-3 adds Cl- at a rate scaled by its thermodynamic drive
                1 - Ko Clo / (K Cl)_AMsh relative to rest (so K+ rising at the ending slows it), cleared with the
                microdomain time constant; GCY-8 activity 1 / (1 + Clo / IC50) relative to wild-type rest is
                out['afd_gc_scale'] = {'AFDL': x, 'AFDR': y}: 1 at wild-type rest, above 1 in the kcc-3 null, for
                the AFD cyclase cascade (B3's senses) to multiply its catalytic rate by. Until a reader exists this
                arm changes no current.

Forms (nested): glia_cells on | off; glia_kbuffer kir (default) | null (no glial uptake, diffusion only: the Kir4.1
null) | fixed (no compartment: Ko stays at the bath, no current); glia_kcc3 on | null (no KCC-3 flux) | fixed (no
state, scale 1). brain_layers' lumped `glia` gain (off) stays as the simplest form and is not claimed here.
Validity: K+ and Cl- are well mixed within each ending compartment; no osmotic or volume change; the amphid neurons'
K+ load is a linear leak estimate, not their channels' own K+ currents; AFD-AWC cross-talk through one sheath (Ray et
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
    ("glia_kcc3", "Amphid sheath KCC-3 Cl- microdomain at AFD's ending; Cl- inhibits GCY-8: out['afd_gc_scale'] "
     "(nested: null = kcc-3, fixed = scale 1)", "glia", "on"),
]

GLIA_CELLS = ["GLRDL", "GLRDR", "GLRL", "GLRR", "GLRVL", "GLRVR", "CEPshDL", "CEPshDR", "CEPshVL", "CEPshVR"]
GLIA_V0_MS = 1000.0
SINGHVI = "Singhvi et al. 2016 Cell 165:936"
KIR = "mammalian Kir4.1 K+ clearance (PORT_SOURCES_ORGANS O5: PLoS Comput Biol 10.1371/journal.pcbi.1004137 and " \
      "related; wild type ~4.2 s, glial Kir4.1 knockout ~6.3 s)"
MENG = "Meng et al. 2016 eLife (PMC5083064)"
F_C_PER_MOL = 96485.0


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
       notes="K+ leak per amphid neuron: sets the activity K+ load and the reversal-shift current; guessed"),
    _s("glia_kir_tau_s", "glia_kbuffer", "s", 12.6, 2.0, 30.0, KIR, "inferred", "amphid sheath",
       notes="glial uptake alone: 1 / (1/4.2 - 1/6.3) s from the wild-type and knockout recoveries (derived from "
       "cross-species numbers)"),
    _s("glia_k_diff_tau_s", "glia_kbuffer", "s", 6.3, 3.0, 15.0, KIR, "inferred", "amphid endings",
       notes="clearance without glial uptake (the Kir4.1 knockout's recovery), cross-species"),
    _s("glia_rt_f_mV", "glia_kbuffer", "mV", 25.26, 24.4, 26.1, "RT/F at 20 C (15-30 C range)", "derived",
       grain="global", applies="whole worm"),
    _s("glia_cl_bath_mM", "glia_kcc3", "mM", 150.0, 50.0, 160.0, "C. elegans recording saline (~150 mM Cl-)",
       "inferred", "AFD ending", notes="Cl- outside the microdomain; the pseudocoelomic Cl- is unmeasured"),
    _s("glia_kcc3_dcl_mM", "glia_kcc3", "mM", 20.0, 2.0, 60.0, SINGHVI, applies="AFD ending",
       notes="Cl- excess KCC-3 holds in AFD's microdomain at rest; no measurement (the paper's Cl- levels are not in "
       "the free summary); guessed"),
    _s("glia_cl_tau_s", "glia_kcc3", "s", 4.2, 0.7, 6.3, KIR, "inferred", "AFD ending",
       notes="microdomain clearance, taken as the K+ recovery (O5's suggestion)"),
    _s("glia_amsh_kcl_mM2", "glia_kcc3", "mM2", 2800.0, 1000.0, 6000.0, "KCC thermodynamics (K x Cl in = out at "
       "equilibrium)", applies="AMsh", notes="[K+]i x [Cl-]i in the sheath (e.g. 140 x 20); guessed"),
    _s("glia_gcy8_cl_ic50_mM", "glia_kcc3", "mM", 100.0, 10.0, 300.0, SINGHVI, applies="AFD GCY-8",
       notes="Cl- at half GCY-8 inhibition, Hill 1; Singhvi measured the inhibition, the number is not in the free "
       "summary; guessed"),
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
            v = np.asarray(ctx.v, float)[self.amph]
            if self.v0 is None:
                self.v0_sum += v
                self.v0_n += 1
                if ctx.t_ms + dt_ms >= GLIA_V0_MS:
                    self.v0 = self.v0_sum / self.v0_n
                load = np.zeros(2)
            else:
                ipa = q["glia_k_gleak_nS"] * np.maximum(v - self.v0, 0.0)              # pA of extra K+ efflux
                load = np.bincount(self.amph_side, ipa, minlength=2) * 1e6 / F_C_PER_MOL / q["glia_k_volume_um3"]
            k = 1.0 / q["glia_k_diff_tau_s"] + (1.0 / q["glia_kir_tau_s"] if self.kb == "kir" else 0.0)
            e = np.exp(-k * dt)
            kb = q["glia_k_bath_mM"]
            self.ko = kb + (self.ko - kb) * e + load / k * (1.0 - e)                   # mM
            dek = q["glia_rt_f_mV"] * np.log(self.ko / kb)                             # mV
            I = np.zeros(len(ctx.v))
            I[self.amph] = q["glia_k_gleak_nS"] * dek[self.amph_side]                  # nS x mV = pA
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
