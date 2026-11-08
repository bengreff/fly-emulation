"""Other non-neural cells (PLAN row 16): hypodermis, head mesodermal cell and excretory cells as passive coupled
cells; body fluid volume and pressure held by the excretory canal; coelomocyte clearance of the pseudocoelom.

No published model covers these (PORT_SOURCES_ORGANS O6); every rate is a bounded guess, labelled.

  other_cells     hyp (the hypodermal syncytium), hmc (head mesodermal cell), exc_cell (excretory canal cell) and
                  exc_gl (excretory gland), the Cook et al. 2019 non-neural nodes the brain does not build, as
                  passive cells (area x 1 uF/cm2, leak at a guessed specific resistance and resting level) joined by
                  Cook's gaps (to PVD, CAN, ALA, AVH, AVK, AS10/11, the posterior body-wall muscles and each other)
                  at the brain's per-contact neuronal gap (inferred). Seam cells are not Cook nodes and are absent.
  excretory_osmo  O6 nested form (2): one body-fluid volume state v (1 = normal). Hydrostatic pressure P =
                  E_vol (v - v_slack), with v_slack set so P(1) = the setpoint. Water enters across the body wall
                  at Lp (dPi - P), dPi = RT x (internal osmotic excess - any extra external osmolarity from
                  obs['head']['osmolarity_mOsm'] above the medium); the excretory canal (AQP-8 water, CLH-3 Cl- set
                  by WNK-1/GCK-3, lumped as one controller) removes the resting influx plus gain x Lp (P - P_set).
                  out['pressure_kPa'] = P (B3's body and touch read it), out['body_fluid_volume_rel'] = v.
  coelomocytes    six coelomocytes' continuous fluid-phase endocytosis (Fares & Greenwald 2001) as one first-order
                  clearance of the pseudocoelom, k = n x per-cell clearance / pseudocoelom volume:
                  out['coelomocyte_uptake_per_s'] (mech.neuromod's peptide pools and the intestine's NLP-40 read
                  it).

Forms (nested): other_cells on | off; excretory_osmo canal (default) | null (canal ablated: Nelson & Riddle 1984) |
fixed (no state: P = the setpoint, v = 1); coelomocytes on | null (cup: no uptake, key written as 0) | off (no key:
neuromod's own placeholder).
Validity: one well-mixed fluid volume (no local swelling); linear body-wall elasticity and water permeability; no
glycerol or other osmolyte synthesis (hours-long volume recovery in hypertonic media is absent, Lamitina 2004); the
canal's ion transport is not resolved; coelomocyte uptake is not saturable.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

MECHANISMS = [
    ("other_cells", "Hypodermis, head mesodermal cell, excretory cell and gland as passive cells with Cook's gaps",
     "organ", "on"),
    ("excretory_osmo", "Body fluid volume and pressure: osmotic water influx against pressure, the excretory canal "
     "removing it at a setpoint; out['pressure_kPa'] (nested: null = canal ablated, fixed = constant)", "organ",
     "canal"),
    ("coelomocytes", "Six coelomocytes' fluid-phase uptake as the pseudocoelom's clearance; "
     "out['coelomocyte_uptake_per_s'] (nested: null = cup, off = neuromod's placeholder)", "organ", "on"),
]

OTHER_CELLS = ["hyp", "hmc", "exc_cell", "exc_gl"]
FG01 = "Fares & Greenwald 2001 Genetics 159:133"
NR84 = "Nelson & Riddle 1984 J Exp Zool 231:45"
LAM04 = "Lamitina et al. 2004 Am J Physiol Cell 286:C785"
RT_KPA_PER_MOSM = 2.436                     # kPa per mOsm/L at 20 C (R T), derived


def _s(pid, mech, unit, v, lo, hi, src, label="guessed", applies="whole worm", grain="global", notes=""):
    return Spec(pid, mech, unit, v, lo, hi, source=src, label=label, grain=grain, applies_to=applies, notes=notes)


SPECS = [
    _s("other_area_hyp_um2", "other_cells", "um2", 1.6e5, 5e4, 4e5, "body surface 2 pi x 25 um x 1 mm", "derived",
       "hyp", "cell", notes="the syncytium's outer face only (apical and basal folds would add more)"),
    _s("other_area_hmc_um2", "other_cells", "um2", 5000.0, 1000.0, 20000.0, "WormAtlas (hmc: soma and two long "
       "processes)", applies="hmc", grain="cell", notes="guessed"),
    _s("other_area_exc_cell_um2", "other_cells", "um2", 2e4, 5000.0, 6e4, "WormAtlas (H-shaped canal, ~2 mm of "
       "canals)", applies="exc_cell", grain="cell", notes="guessed (basal plus luminal membrane)"),
    _s("other_area_exc_gl_um2", "other_cells", "um2", 2000.0, 500.0, 8000.0, "WormAtlas", applies="exc_gl",
       grain="cell", notes="guessed"),
    _s("other_rm_kohm_cm2", "other_cells", "kOhm cm2", 10.0, 1.0, 50.0, "generic epithelial / glial range",
       applies="hyp, hmc, exc_cell, exc_gl", grain="class", notes="specific membrane resistance; guessed"),
    _s("other_e_leak_mV", "other_cells", "mV", -50.0, -80.0, -20.0, "no recording", applies="hyp, hmc, exc_cell, "
       "exc_gl", grain="class", notes="resting level; guessed"),
    _s("other_gap_nS_per_contact", "other_cells", "nS", 0.2236, 0.05, 0.5, "the brain's gap_strength_per_pair",
       "inferred", "Cook gaps of hyp, hmc, exc_cell, exc_gl", "class",
       notes="the brain's per-contact neuronal gap, read from the ledger when present; O6: bounded by row 8's range"),
    _s("osmo_p_set_kPa", "excretory_osmo", "kPa", 40.0, 20.0, 200.0, "Sanzeni et al. 2019 (B3's "
       "touch_pressure_kPa, p/E = 0.01 at E 4 MPa); Park et al. 2007 PNAS measured 50-200 kPa", "published_fit",
       notes="internal hydrostatic pressure the canal holds; B3's value so the body sees no change at rest"),
    _s("osmo_dosm_mOsm", "excretory_osmo", "mOsm/L", 50.0, 20.0, 150.0, "nematodes are hyperosmotic to their medium "
       "(the canal exists to bail water, " + NR84 + ")", notes="body fluid osmotic excess over the culture medium; "
       "guessed (no C. elegans body fluid osmolality found free tonight)"),
    _s("osmo_e_vol_kPa", "excretory_osmo", "kPa per unit volume", 200.0, 50.0, 3000.0, "thin-shell cylinder, "
       "dV/V = 1.5 P r / (E t), cuticle E 4-400 MPa (B3, Essmann 2020), t 0.5 um, r 25 um", notes="volumetric "
       "elastance of the body wall; guessed inside the shell formula's span (53 kPa to 5 MPa)"),
    _s("osmo_lp_per_kPa_s", "excretory_osmo", "1/(kPa s)", 3e-7, 3e-8, 3e-6, LAM04 + " (worms shrink "
       "'dramatically' within minutes in 200 mM NaCl)", notes="body-wall water permeability as relative volume per "
       "s per kPa; guessed as ~20 % volume loss in 10 min against ~400 mOsm (975 kPa): 0.2 / 600 / 975; not set "
       "from the ablation time (that is the unit check)"),
    _s("osmo_canal_gain", "excretory_osmo", "1", 10.0, 1.0, 100.0, "this model", applies="excretory canal",
       grain="cell", notes="canal correction per unit pressure error, in units of the body wall's Lp; guessed"),
    _s("cc_count", "coelomocytes", "cells", 6.0, 6.0, 6.0, "WormAtlas; " + FG01, "measured", "coelomocytes"),
    _s("cc_clearance_um3_per_s", "coelomocytes", "um3/s per cell", 67.0, 7.0, 670.0, FG01 + "; injected TR-BSA "
       "reaches coelomocyte endosomes in 5-10 min (PMC2441656)", applies="coelomocytes", grain="class",
       notes="fluid-phase clearance per cell; guessed so k = 1e-3 /s (neuromod's placeholder, a ~17 min "
       "lifetime), bounds one decade either side"),
    _s("cc_pc_volume_um3", "coelomocytes", "um3", 4e5, 1e5, 1.5e6, "neuromod's pc_cross_section_um2 (400) x 1 mm",
       "derived", "pseudocoelom", notes="the pseudocoelomic fluid volume the coelomocytes clear"),
]


def defaults():
    return {s.id: s.template for s in SPECS}


class Osmo:
    """Body fluid volume v and pressure (numpy, exact per step for the linear system)."""

    def __init__(self, q, form):
        self.q, self.form = q, form
        self.v = 1.0

    @property
    def P(self):
        q = self.q
        return q["osmo_p_set_kPa"] + q["osmo_e_vol_kPa"] * (self.v - 1.0)

    def step(self, dt_s, extra_mosm=0.0):
        q = self.q
        if self.form == "fixed":
            return
        lp, E, ps = q["osmo_lp_per_kPa_s"], q["osmo_e_vol_kPa"], q["osmo_p_set_kPa"]
        dpi = RT_KPA_PER_MOSM * (q["osmo_dosm_mOsm"] - extra_mosm)
        rest = lp * (RT_KPA_PER_MOSM * q["osmo_dosm_mOsm"] - ps)     # the resting influx the canal bails
        canal = self.form == "canal"
        g = q["osmo_canal_gain"] * lp
        if canal and rest + g * (self.P - ps) < 0.0:
            canal = False                                  # the canal cannot pump water in: this step runs without it
        # dv/dt = lp (dpi - P) - [rest + g (P - ps)]_canal, P = ps + E (v - 1): linear in v, solved exactly
        a = (lp + (g if canal else 0.0)) * E
        b = lp * (dpi - ps) - (rest if canal else 0.0)
        v_inf = 1.0 + b / a
        self.v = v_inf + (self.v - v_inf) * np.exp(-a * dt_s)


def steady_pressure_kPa(q, form="canal", extra_mosm=0.0):
    """Body pressure after equilibrating to a medium extra_mosm above the template's (the data model's start-up
    state, passed to the FEM body; osmo_p_set_kPa exactly in the template medium)."""
    o = Osmo(q, form)
    for _ in range(200):                                   # 1 h steps; the slowest relaxation is about 5 h
        o.step(3600.0, extra_mosm)
    return float(o.P)


class Mech:
    """Builds the passive non-neural cells and steps body fluid pressure and coelomocyte clearance."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        self.cells_on = toggles.get("other_cells", "on") != "off"
        self.osmo_form = toggles.get("excretory_osmo", "canal")
        self.osmo_form = {"on": "canal", "off": "fixed"}.get(self.osmo_form, self.osmo_form)
        self.cc = toggles.get("coelomocytes", "on")
        assert self.osmo_form in ("canal", "null", "fixed") and self.cc in ("on", "null", "off")
        q = defaults()
        q.update({k: float(v) for k, v in (params or {}).items() if np.isscalar(v)})
        sp = getattr(brain, "spec", None)
        if sp is not None and getattr(sp, "led", None) is not None and "other_gap_nS_per_contact" not in (params or {}):
            try:
                q["other_gap_nS_per_contact"] = float(np.median(sp.v("gap_strength_per_pair").to_numpy(float)))
            except (KeyError, ValueError):
                pass
        self.q = q
        self.osmo = Osmo(q, self.osmo_form)
        self.sec, self.n_gap = {}, 0
        if self.cells_on and hasattr(brain, "h"):
            self._build()
        self.reset()

    def _build(self):
        b, q = self.brain, self.q
        h = b.h
        st, nm = b.st, b.st.names
        for n in OTHER_CELLS:
            if n in b.idx:
                continue
            sec = h.Section(name=f"other_{n}")
            sec.nseg, sec.diam = 1, 10.0
            sec.L = q[f"other_area_{n}_um2"] / (np.pi * sec.diam)
            sec.cm = 1.0
            sec.insert("pas")
            sec.g_pas = 1.0 / (q["other_rm_kohm_cm2"] * 1000.0)                    # S/cm2
            sec.e_pas = q["other_e_leak_mV"]
            self.sec[n] = sec
        g = q["other_gap_nS_per_contact"] / 1000.0
        mine = set(self.sec)
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
            b._gap(sa, sb, n * g, "gap_other")
            self.n_gap += 1

    def reset(self):
        self.osmo.v = 1.0
        for sec in self.sec.values():
            sec(0.5).v = self.q["other_e_leak_mV"]

    def uptake_per_s(self):
        q = self.q
        if self.cc == "null":
            return 0.0
        return q["cc_count"] * q["cc_clearance_um3_per_s"] / q["cc_pc_volume_um3"]

    def step(self, ctx, dt_ms):
        try:
            extra = float(ctx.obs["head"].get("osmolarity_mOsm", 0.0))
        except (AttributeError, KeyError, TypeError):
            extra = 0.0
        self.osmo.step(dt_ms / 1000.0, extra)
        out = {"pressure_kPa": float(self.osmo.P), "body_fluid_volume_rel": float(self.osmo.v)}
        if self.cc != "off":
            out["coelomocyte_uptake_per_s"] = self.uptake_per_s()
        if self.sec:
            out["other_v_mV"] = {n: float(s(0.5).v) for n, s in self.sec.items()}
        return {"out": out}
