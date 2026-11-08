"""UNC-58, a K2P (TWK) channel with a constitutive Na+ permeability (PLAN row 4; KNOWLEDGE_GAPS section C item 5).

UNC-58 has a cysteine in its selectivity filter that lets Na+ through: in Xenopus oocytes (ND96: 96 mM Na+, 2 mM
K+) the gain-of-function UNC-58(L428F) reverses at -15 (IQR 5) mV, n = 6, where a K+-selective channel would sit
near E_K; removing bath Na+ shifts it left; wild-type UNC-58 gave no detectable current (PNAS 2024 121(43),
doi:10.1073/pnas.2400650121, PMC11513965, read through a summary of the full text; authors not recorded here). unc-58 is in body-wall muscle, almost every
ventral-cord motor neuron class, head and tail neurons and glia (same paper).

Here a leak conductance at the soma of every neuron whose CeNGEN class detects unc-58 (threshold 2) and every
body-wall muscle, reversal unc58_erev_mV (the oocyte number carried over: inferred, the worm's ion gradients are
not the oocyte's), density unc58_g_S_cm2 (guessed: the wild-type channel's current is below the oocyte detection
limit, so the template is small). One wgc conductance per cell (implicit in NEURON); the stand-in brain injects the
explicit current. Off by default (neutral). Validity: one lumped open probability, no voltage, pH or
temperature dependence; the 34 other TWK genes stay a slot (docs/worm/CHANNEL_SLOTS.md).
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

M = "unc58_na_leak"
MECHANISMS = [(M, "UNC-58 K2P leak with a constitutive Na+ permeability (PNAS 2024) in its CeNGEN "
               "classes and body-wall muscle", "channel", "off")]
SRC = "PNAS 2024 121(43), doi:10.1073/pnas.2400650121 (PMC11513965)"
SPECS = [
    Spec("unc58_erev_mV", M, "mV", -15.0, -40.0, 0.0, f"{SRC}: UNC-58(L428F) reverses at -15 (IQR 5) mV in ND96 "
         "oocytes (measured there; carried to the worm's gradients, inferred)", "inferred",
         applies_to="unc-58 cells"),
    Spec("unc58_g_S_cm2", M, "S/cm2", 2e-6, 0.0, 2e-5, f"{SRC}: wild-type UNC-58 current not detectable in "
         "oocytes; no in vivo current recorded", "guessed", applies_to="unc-58 cells",
         notes="soma density, as the brain's channels"),
]


def cells_expressing(brain):
    """Indices of the brain's cells that carry unc-58: CeNGEN-detecting neuron classes and body-wall muscles."""
    from wormemu.brain_structure import cengen_class
    st = brain.st
    row = st.tpm[st.gene_index["unc-58"]] if "unc-58" in st.gene_index else None
    det = {c for k, c in enumerate(st.cengen_classes) if row is not None and row[k] > 0}
    classes = set(st.cengen_classes)
    return [i for i, n in enumerate(brain.cell_names)
            if brain.is_muscle[i] or cengen_class(n, classes) in det]


class Mech:
    def __init__(self, brain, params, toggles):
        self.on = toggles.get(M, "off") == "on"
        self.idx, self.pps, self.g_uS = np.zeros(0, int), [], np.zeros(0)
        if not self.on:
            return
        self.e = float(params["unc58_erev_mV"])
        self.idx = np.array(cells_expressing(brain), int)
        soma = getattr(brain, "soma", None)
        if soma is not None:
            area = np.array([sum(seg.area() for seg in soma[i]) for i in self.idx])     # um2
            self.g_uS = params["unc58_g_S_cm2"] * area * 1e-2                            # S/cm2 x um2 -> uS
            for i, g in zip(self.idx, self.g_uS):
                pp = brain.h.wgc(soma[i](0.5))
                pp.e, pp.g = self.e, float(g)
                self.pps.append(pp)
        else:
            self.g_uS = np.full(len(self.idx), params["unc58_g_S_cm2"] * 1e3 * 1e-2)    # a 1000 um2 soma

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        if not self.on:
            return {}
        out = {"unc58_cells": int(len(self.idx)),
               "unc58_g_max_nS": float(1000.0 * self.g_uS.max()) if len(self.g_uS) else 0.0}
        if self.pps:
            return {"out": {"k2p": out}}
        I = np.zeros(len(ctx.names))
        I[self.idx] = 1000.0 * self.g_uS * (self.e - np.asarray(ctx.v, float)[self.idx])
        return {"I_pA": I, "out": {"k2p": out}}
