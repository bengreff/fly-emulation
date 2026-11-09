"""The neurons' bulk Ca pool in whole-cell units (Director check, 6 Nov 2026; docs/worm/night/2026-11-06_wbrain.md).

BAAIWorm's cainternm.mod (third_party/baaiworm/mod) is Nicoletti et al. 2019 PLoS One 14:e0218738 Eq. 28,
    d[Ca]/dt = -f I_Ca/(2 F V_cell) - ([Ca] - [Ca]eq)/tau_Ca,
where I_Ca is the whole-cell Ca current in pA (EGL-19 + UNC-2 + CCA-1) and V_cell the cell's volume. The mod feeds it
NEURON's ica, which is a density (mA/cm2 = 10 pA/um2), so the influx misses the factor 10 x soma area (99 for AVAL,
241 for AWCL; BAAIWorm somas are 2 to 3 um across) and the pool stays within 0.1% of [Ca]eq at any voltage (measured:
AVAL at -15 mV, 0.05004 uM). Every Ca channel sits on the soma (BAAIWorm's neurites are passive), so the whole-cell
current is the soma's density times its area. The fix sets each neuron soma's vcell to V_cell / (10 A_soma), so the
same mod computes Eq. 28 with the whole-soma current. V_cell, f, tau_Ca and [Ca]eq stay the ledger's ca_pool values.
Muscles are excluded (their pool is B2's). Form: total_current (default) / off (BAAIWorm as ported).
No new numbers: 10 is the unit conversion (exact), the area is the model's geometry.

slo_ca_source (DEBUG_TRIAGE item 4, wbrain2, 8 Nov 2026): the Ca the four SLO channels see. BAAIWorm's network mods
(ours) compute each SLO's nanodomain from one open Ca channel, gsc = 40 pS (Nicoletti 2019): `single_channel`, the
default. BAAIWorm's single-cell tuner (eworm/single_nrn_tune/neuron_model.py:84-108) fitted the cells with
`cainternn` instead (Metaworm modfile_d: the same nanodomain formula, but with gbcav = the cell's summed SLO density in
nS/um2 where the single-channel conductance in nS belongs) and SLO mods that read it; it never inserted KCNL.
`tuner_gbar` sets each cell's SLO gsc to that sum read as nS, which reproduces cainternn's Ca (same constants).
No new numbers: the sum is the cell's own published densities.

kcnl_density (wbrain2, 9 Nov 2026; night file, "KCNL: the network's density or the tuner's none"): the same tuner
never inserted KCNL ("Delete: gbkcnl"), while the network's cell_param gives 88 neurons KCNL (80 at 0.00063
nS/um2, AIYL's set 2 among them; AVA, AVB, AVE, PVC at 0.005), so the fitted densities were found without it.
`network` (default) keeps the cell_param values; `tuner` sets gbkcnl 0 in every section of every neuron at build,
before the brain gathers its conductance targets, so no g_scale brings it back. No new numbers.

ca_bulk (DEBUG_TRIAGE lines 19 and 17, inbox item 3, wbrain2, 8 Nov 2026): a bulk cytosolic Ca pool for the
indicator. Eq. 28's pool is Nicoletti's submembrane microdomain (tau_Ca 50 ms), the Ca the channels see; GCaMP reads
bulk cytosolic Ca. No C. elegans neuron form with a bulk pool was found (night file, Open), so the nearest system's
published form is borrowed (Director's rule, 6 Nov): NEURON's cadifpmp (Hines and Carnevale, NEURON 9.0.2
share/nrn/demo/release/cabpump.mod), radial diffusion in 10 annuli of the soma cylinder, a fixed-ratio buffer and a
saturable membrane pump, as nmodl/cabulk.mod. A readout only: it reads the soma's total ica and writes neither cai
nor ica, so every channel keeps Eq. 28 and the membrane is unchanged; GCaMP (mech/observation) reads its mean free Ca.
Form cadifpmp; off (default) inserts nothing. Validity: soma Ca only (BAAIWorm's Ca channels are all somatic), end caps
ignored as cadifpmp, and the pump is the only extrusion: a Ca current above its capacity (k3 pump0 2F = 0.029 pA/um2,
derived) accumulates without bound.
"""
from __future__ import annotations

import numpy as np

from wormemu.mech.senses_base import spec

MECHANISMS = [
    ("ca_pool_units", "Neuron bulk Ca pool fed the whole-soma Ca current (Nicoletti 2019 Eq. 28) instead of the "
     "current density", "channel", "total_current"),
    ("slo_ca_source", "Ca seen by the SLO channels: one open channel's nanodomain (gsc 40 pS, BAAIWorm's network and "
     "Nicoletti 2019) or the tuner's cainternn (gsc = the cell's summed SLO density)", "channel", "single_channel"),
    ("ca_bulk", "Bulk cytosolic Ca for the indicator (NEURON's cadifpmp: radial diffusion, fixed-ratio buffer, "
     "membrane pump), fed by the soma's Ca current; a readout, the channels keep Eq. 28", "channel", "off"),
    ("kcnl_density", "KCNL (SK-type K) as the network's cell_param gives it (88 neurons) or none, as BAAIWorm's "
     "single-cell tuner fitted every cell", "channel", "network"),
]
# the form that is the code without each switch (the ledger's neutral column)
NEUTRAL = {"ca_pool_units": "off", "slo_ca_source": "single_channel", "ca_bulk": "off", "kcnl_density": "network"}
FORMS = ("total_current", "off")
SLO_CA = ("single_channel", "tuner_gbar")
SLO_GB = {"slo1_egl19": "gbslo1", "slo1_unc2": "gbslo1", "slo2_egl19": "gbslo2", "slo2_unc2": "gbslo2"}
BULK = ("off", "cadifpmp")
KCNL = ("network", "tuner")
CADIF = "NEURON 9.0.2 cadifpmp (Hines and Carnevale; share/nrn/demo/release/cabpump.mod, opened 8 Nov 2026)"
BORROW = "borrowed from the nearest system (a generic vertebrate neuron demo); no C. elegans value found"
SPECS = [
    spec("cabulk_dfree_um2_ms", "ca_bulk", "um2/ms", 0.6, 0.2, 0.8, "inferred", CADIF + "; " + BORROW,
         notes="free Ca diffusion; bounds guessed (aqueous Ca2+ about 0.8 um2/ms, cytosolic free Ca lower)"),
    spec("cabulk_beta", "ca_bulk", "1", 50.0, 20.0, 2000.0, "inferred", CADIF + "; " + BORROW,
         notes="fixed bound/free ratio (kappa_S); bounds guessed from neuronal kappa_S as relayed, not opened: "
               "Maravall 2000 44-80, Helmchen 1996 100-200, Purkinje cells near 2000"),
    spec("cabulk_k1_per_mM_s", "ca_bulk", "1/(mM s)", 1e7, 1e6, 1e7, "inferred", CADIF + "; " + BORROW,
         notes="Ca + pump -> pumpca. cadifpmp's 5e8 /(mM s) = 5e11 /(M s) is 50x the diffusion limit (~1e10 /M/s, "
               "the hard bound): the template is the limit, and k2 is lowered with it so cadifpmp's Km stays 0.50 uM; "
               "the pool's clearance (k3 pump0/Km) and capacity (k3 pump0) are unchanged and the binding still "
               "relaxes in 0.2 ms (derived); lower bound guessed (10x)"),
    spec("cabulk_k2_per_s", "ca_bulk", "1/s", 4.5e3, 4.5e2, 4.5e4, "derived", CADIF + "; " + BORROW,
         notes="pumpca -> Ca + pump: Km k1 - k3, with cadifpmp's Km = (k2 + k3)/k1 = 0.50 uM and k1 at the "
               "diffusion limit (cadifpmp: 0.25e6 with k1 5e8); bounds guessed (10x)"),
    spec("cabulk_k3_per_s", "ca_bulk", "1/s", 0.5e3, 0.5e2, 0.5e4, "inferred", CADIF + "; " + BORROW,
         notes="pumpca -> pump + Ca out (the turnover); bounds guessed (10x)"),
    spec("cabulk_k4_per_mM_s", "ca_bulk", "1/(mM s)", 5.0, 0.5, 50.0, "inferred", CADIF + "; " + BORROW,
         notes="reverse transport; sets the pump's floor cao k2 k4/(k1 k3) = 9 nM at the ledger's k1, k2 "
               "(cadifpmp's own 10 nM; derived); bounds guessed"),
    spec("cabulk_pump0_mol_cm2", "ca_bulk", "mol/cm2", 3e-14, 3e-15, 3e-13, "inferred", CADIF + "; " + BORROW,
         notes="pump sites per membrane area; capacity k3 pump0 2F = 0.029 pA/um2 (derived); bounds guessed (10x)"),
]
GLOBALS = {"cabulk_dfree_um2_ms": "DFree_cabulk", "cabulk_beta": "beta_cabulk", "cabulk_k1_per_mM_s": "k1_cabulk",
           "cabulk_k2_per_s": "k2_cabulk", "cabulk_k3_per_s": "k3_cabulk", "cabulk_k4_per_mM_s": "k4_cabulk",
           "cabulk_pump0_mol_cm2": "pump0_cabulk"}
MA_CM2_TO_PA_UM2 = 10.0                          # 1 mA/cm2 = 1e-3 A / 1e8 um2 = 10 pA/um2


def _bulk(toggles):
    b = toggles.get("ca_bulk", "off")
    if b not in BULK:
        raise ValueError(f"ca_bulk form {b!r} not in {BULK}")
    return b


def _kcnl(toggles):
    k = toggles.get("kcnl_density", "network")
    if k not in KCNL:
        raise ValueError(f"kcnl_density form {k!r} not in {KCNL}")
    return k


def build_cell(brain, name, obj, params, toggles):
    """ca_bulk: insert the bulk pool (nmodl/cabulk.mod) in each neuron's soma, where every Ca channel sits.
    kcnl_density tuner: gbkcnl 0 in every section of the neuron."""
    if name not in brain.st.index or brain.st.kind[brain.st.index[name]] != "neuron":
        return
    if _kcnl(toggles) == "tuner":
        for sec in obj.all:
            if brain.h.ismembrane("kcnl", sec=sec):
                for seg in sec:
                    seg.kcnl.gbkcnl = 0.0
    if _bulk(toggles) != "off":
        obj.Soma.insert("cabulk")


class Mech:
    """Rescales vcell (and, under tuner_gbar, the SLO gsc) once at build; the mods do the rest. Under ca_bulk,
    publishes each neuron's bulk free Ca (out['ca_bulk_uM'], uM, NaN where there is no pool) every step."""

    def __init__(self, brain, params, toggles):
        v = toggles.get("ca_pool_units", "off")
        if v not in FORMS:
            raise ValueError(f"ca_pool_units form {v!r} not in {FORMS}")
        src = toggles.get("slo_ca_source", "single_channel")
        if src not in SLO_CA:
            raise ValueError(f"slo_ca_source form {src!r} not in {SLO_CA}")
        self.slo_gsc = {}
        if src == "tuner_gbar":
            for i, sec in enumerate(brain.soma):
                for seg in sec:
                    ms = [getattr(seg, m) for m in SLO_GB if hasattr(seg, m)]
                    if ms:
                        g = sum(getattr(m, SLO_GB[m.name()]) for m in ms)      # nS/um2, read as nS (the tuner)
                        for m in ms:
                            m.gsc = g
                        self.slo_gsc[brain.cell_names[i]] = g
        self.scale = {}
        for i, sec in enumerate(brain.soma):
            if v == "off" or brain.is_muscle[i]:
                continue
            area = sum(seg.area() for seg in sec)
            for seg in sec:
                m = getattr(seg, "cainternm", None)
                if m is not None:
                    m.vcell = m.vcell / (MA_CM2_TO_PA_UM2 * area)
                    self.scale[brain.cell_names[i]] = MA_CM2_TO_PA_UM2 * area
        self.bulk = None
        if _bulk(toggles) != "off":
            h = brain.h
            for pid, g in GLOBALS.items():
                setattr(h, g, float(params[pid]))
            h.caom_cabulk = brain.spec.v("ion_cao") if brain.lit else 2.0     # mM (the ion itself is held in uM)
            idx = [i for i, sec in enumerate(brain.soma) if h.ismembrane("cabulk", sec=sec)]
            self.bulk_idx = np.array(idx, int)
            self.bulk = h.PtrVector(len(idx))
            for k, i in enumerate(idx):
                seg = brain.soma[i](0.5)
                seg.cabulk.ca0 = h.caeq_cainternm            # the ledger's capool_caeq, the Eq. 28 pool's start
                self.bulk.pset(k, seg._ref_cab_cabulk)
            self._buf = h.Vector(len(idx))
            self.n = len(brain.cell_names)

    def reset(self):
        pass

    def read_bulk(self):
        """Each cell's bulk free Ca (uM), NaN where no pool is inserted."""
        out = np.full(self.n, np.nan)
        self.bulk.gather(self._buf)
        out[self.bulk_idx] = self._buf.as_numpy()
        return out

    def step(self, ctx, dt_ms):
        if self.bulk is None:
            return {}
        return {"out": {"ca_bulk_uM": self.read_bulk()}}
