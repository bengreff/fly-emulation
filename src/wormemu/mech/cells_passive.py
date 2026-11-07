"""The remaining glia and the wired end organs as passive cells (PLAN row 1).

  glia_sensilla   the 46 sensillar sheath and socket glia that are not Cook et al. 2019 nodes (WormAtlas, Altun and
                  Hall, "Neuronal support cells": 56 support cells, 24 sheath, 26 socket, 6 GLR; mech/glia builds
                  the 6 GLR and 4 CEPsh). Cook lists no gap or chemical synapse for any of the 46, so each is an
                  isolated passive cell (capacitance, leak and resting level borrowed from mech/glia's GLR/CEPsh
                  template; no sheath or socket membrane is recorded). It holds a voltage and no more: no
                  connection reaches the brain until a glial wiring set (or a glial mechanism) names one.
  endorgan_cells  the Cook end organs with gaps to built cells that no module builds: pharyngeal epithelium e2D,
                  e2VL, e2VR, e3D, e3VL, e3VR and pharyngeal glands g1AL, g1AR, as passive cells (area guessed,
                  membrane resistance and resting level borrowed from mech/organs_other) on Cook's gaps to I2L/R,
                  I5, M2L/R, M3L/R, M4, pm1, pm3VL (mech/organs_pharynx's sections) and each other, at the brain's
                  per-contact neuronal gap (inferred: their innexins are not resolved). Chemical synapses onto them
                  are not modelled (no receptor on them is identified).
Not built, one line each (Cook nodes): e1D, e1VL, e1VR (no connection); g1P, g2L, g2R (chemical inputs only, no
receptor identified, nothing returns to the brain); int (mech/organs_intestine's state); bm (the basement
membrane, not a cell). hyp, hmc, exc_cell, exc_gl (mech/organs_other) and the marginal cells (mech/organs_pharynx)
are built elsewhere.
Forms: glia_sensilla on | off; endorgan_cells on | off.
Validity: one passive compartment per cell; no glial K+ or Cl- handling here (mech/glia's amphid compartments do
not read the AMsh cell's voltage).
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

MECHANISMS = [
    ("glia_sensilla", "The 46 sheath and socket glia that are not Cook nodes (amphid, phasmid, IL, OLQ, OLL, CEP "
     "socket, ADE, PDE) as isolated passive cells", "glia", "on"),
    ("endorgan_cells", "Pharyngeal epithelium (e2, e3) and glands g1AL/R as passive cells on Cook's gaps to I2, I5, "
     "M2, M3, M4 and the pharyngeal muscles", "organ", "on"),
]

WORMATLAS = "WormAtlas, Altun and Hall, Nervous system: neuronal support cells (wormatlas.org)"
GLIA_SENSILLA = ["AMshL", "AMshR", "AMsoL", "AMsoR", "PHshL", "PHshR", "PHso1L", "PHso1R", "PHso2L", "PHso2R",
                 "ILshDL", "ILshDR", "ILshL", "ILshR", "ILshVL", "ILshVR",
                 "ILsoDL", "ILsoDR", "ILsoL", "ILsoR", "ILsoVL", "ILsoVR",
                 "OLQshDL", "OLQshDR", "OLQshVL", "OLQshVR", "OLQsoDL", "OLQsoDR", "OLQsoVL", "OLQsoVR",
                 "OLLshL", "OLLshR", "OLLsoL", "OLLsoR", "CEPsoDL", "CEPsoDR", "CEPsoVL", "CEPsoVR",
                 "ADEshL", "ADEshR", "ADEsoL", "ADEsoR", "PDEshL", "PDEshR", "PDEsoL", "PDEsoR"]
EPITHELIUM = ["e2D", "e2VL", "e2VR", "e3D", "e3VL", "e3VR"]
GLANDS = ["g1AL", "g1AR"]


def _s(pid, mech, unit, v, lo, hi, src, label="guessed", applies="whole worm", grain="class", notes=""):
    return Spec(pid, mech, unit, v, lo, hi, source=src, label=label, grain=grain, applies_to=applies, notes=notes)


SPECS = [
    _s("passive_cm_uF_cm2", "glia_sensilla", "uF/cm2", 1.0, 0.8, 1.2, "Gentet, Stuart and Clements 2000 Biophys J "
       "79:314 (0.9 uF/cm2, rat cortical neurons)", "inferred", "sensillar glia, e2/e3, g1A", "global",
       notes="specific membrane capacitance; cross-species; sets each isolated glia's area from its capacitance"),
    _s("sens_glia_c_pF", "glia_sensilla", "pF", 20.0, 5.0, 50.0, "borrowed from mech/glia glia_c_pF (GLR, CEPsh)",
       applies="46 sheath and socket glia", notes="no sheath or socket recording; guessed"),
    _s("sens_glia_g_leak_nS", "glia_sensilla", "nS", 1.0, 0.2, 5.0, "borrowed from mech/glia glia_g_leak_nS",
       applies="46 sheath and socket glia", notes="no recording; guessed"),
    _s("sens_glia_e_leak_mV", "glia_sensilla", "mV", -70.0, -85.0, -50.0, "borrowed from mech/glia glia_e_leak_mV "
       "(glia rest near E_K; mammalian astrocytes -80 to -90 mV)", "inferred", "46 sheath and socket glia",
       notes="cross-species, bounded"),
    _s("endo_area_epi_um2", "endorgan_cells", "um2", 300.0, 100.0, 1500.0, "WormAtlas pharynx (e2, e3: small "
       "epithelial cells of the anterior pharynx), not measured as an area", applies="e2D, e2VL, e2VR, e3D, e3VL, "
       "e3VR", notes="guessed"),
    _s("endo_area_gland_um2", "endorgan_cells", "um2", 2000.0, 500.0, 8000.0, "WormAtlas pharynx (g1 gland cells: "
       "soma in the terminal bulb, long anterior process), not measured as an area", applies="g1AL, g1AR",
       notes="guessed"),
    _s("endo_rm_kohm_cm2", "endorgan_cells", "kOhm cm2", 10.0, 1.0, 50.0, "borrowed from mech/organs_other "
       "other_rm_kohm_cm2 (generic epithelial / glial range)", applies="e2/e3, g1A",
       notes="specific membrane resistance; guessed"),
    _s("endo_e_leak_mV", "endorgan_cells", "mV", -50.0, -80.0, -20.0, "borrowed from mech/organs_other "
       "other_e_leak_mV (no recording)", applies="e2/e3, g1A", notes="resting level; guessed"),
    _s("endo_gap_nS_per_contact", "endorgan_cells", "nS", 0.2236, 0.05, 0.5, "the brain's gap_strength_per_pair",
       "inferred", "Cook gaps of e2/e3, g1A", notes="the brain's per-contact neuronal gap, read from the ledger when "
       "present (as mech/glia and mech/organs_other); innexins of these cells unresolved"),
]


def defaults():
    return {s.id: s.template for s in SPECS}


class Mech:
    """Builds the cells once; nothing to step (passive membranes are NEURON's)."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        q = defaults()
        q.update({k: float(v) for k, v in (params or {}).items() if np.isscalar(v)})
        sp = getattr(brain, "spec", None)
        if sp is not None and getattr(sp, "led", None) is not None and "endo_gap_nS_per_contact" not in (params or {}):
            try:
                q["endo_gap_nS_per_contact"] = float(np.median(sp.v("gap_strength_per_pair").to_numpy(float)))
            except (KeyError, ValueError):
                pass
        self.q = q
        self.sec, self.e_leak, self.gaps = {}, {}, []
        if toggles.get("glia_sensilla", "on") != "off":
            area = q["sens_glia_c_pF"] / (q["passive_cm_uF_cm2"] * 0.01)          # uF/cm2 = 0.01 pF/um2
            for n in GLIA_SENSILLA:
                self._cell(n, area, q["passive_cm_uF_cm2"], q["sens_glia_g_leak_nS"] * 0.1 / area,  # nS/um2 -> S/cm2
                           q["sens_glia_e_leak_mV"])
        if toggles.get("endorgan_cells", "on") != "off":
            g = 1.0 / (q["endo_rm_kohm_cm2"] * 1000.0)                               # S/cm2
            for names, a in ((EPITHELIUM, q["endo_area_epi_um2"]), (GLANDS, q["endo_area_gland_um2"])):
                for n in names:
                    if n not in brain.idx:
                        self._cell(n, a, q["passive_cm_uF_cm2"], g, q["endo_e_leak_mV"])
            self._wire(set(EPITHELIUM + GLANDS) & set(self.sec))
        self.reset()

    def _cell(self, n, area_um2, cm, g_pas, e_pas):
        sec = self.brain.h.Section(name=f"passive_{n}")
        sec.nseg = 1
        sec.L = sec.diam = float(np.sqrt(area_um2 / np.pi))                         # a cylinder's side: pi d L
        sec.cm = cm
        sec.insert("pas")
        sec.g_pas, sec.e_pas = g_pas, e_pas
        self.sec[n], self.e_leak[n] = sec, e_pas

    def _seg(self, name, ph):
        """The segment a gap to `name` lands on: one of ours, a brain cell, or an organs_pharynx section."""
        b = self.brain
        if name in self.sec:
            return self.sec[name](0.5)
        if name in b.idx:
            return b.segs[b.idx[name]][0][0]
        if ph is not None and name in ph:
            return ph[name](0.5)
        return None

    def _wire(self, mine):
        b = self.brain
        ph = next((getattr(m, "sec", None) for m in getattr(b, "mechs", [])
                   if type(m).__module__ == "wormemu.mech.organs_pharynx"), None)
        g = self.q["endo_gap_nS_per_contact"] / 1000.0                              # nS -> uS
        nm = b.st.names
        for i, j, n in b.st.gap:
            a, c = nm[i], nm[j]
            if a not in mine and c not in mine:
                continue
            sa, sc = self._seg(a, ph), self._seg(c, ph)
            if sa is None or sc is None:
                continue
            b._gap(sa, sc, n * g, "gap_endorgan")
            self.gaps.append((a, c, int(n)))

    def reset(self):
        for n, sec in self.sec.items():
            sec(0.5).v = self.e_leak[n]

    def step(self, ctx, dt_ms):
        return {}
