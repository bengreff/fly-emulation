"""Pathogen infection state (PLAN rows 24 and 9; KNOWLEDGE_GAPS section C item 6): the producer of
outputs['pathogen_exposure'], which mech/learning's pathogen context reads (ADF serotonin up).

Pradhan et al. 2025 Nat Commun 16:3200 (abstract and a summary of the results read, figures not): on P. aeruginosa
PA14 feeding falls progressively over the first 20 h (Fig. 1B) and quiescence bouts start after about 2 days. The
infection load is one first-order state in the hours on the pathogen (INFECTION_H, set by wormemu.simulate from the
experiment's history; a run's seconds do not move it):

    pathogen_exposure = 1 - exp(-INFECTION_H / pathogen_load_tau_h)

Slots, not built (the paper's pathways, each a consumer still to write): ALA and its peptides FLP-7, FLP-24 and
NLP-8 cut feeding (ceh-17, flp-24 and nlp-8 mutants do not reduce it); quiescence needs ASI and DAF-7/TGF-beta (ASI
activity tracks the bouts) and not RIS; FLP-13 from I1, I5, ASH and OLL acts through DMSR-1 and EGL-4 to delay it.
Their peptide genes are in mech/neuromod already; what is missing is the infection's drive on each source.

Off by default (neutral); on with INFECTION_H = 0 is also neutral (exposure 0).
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

M = "pathogen_sickness"
MECHANISMS = [(M, "PA14 infection load from the hours on the pathogen (Pradhan et al. 2025) -> pathogen_exposure",
               "learning", "off")]
INFECTION_H: float = 0.0       # hours on PA14 before the run, set by wormemu.simulate
SPECS = [
    Spec("pathogen_load_tau_h", M, "h", 10.0, 3.0, 40.0, "Pradhan et al. 2025 Nat Commun 16:3200 Fig. 1B: feeding "
         "falls progressively over the first 20 h on PA14 (time constant not fitted there)", "guessed",
         applies_to="whole worm"),
]


class Mech:
    def __init__(self, brain, params, toggles):
        self.on = toggles.get(M, "off") == "on"
        self.x = 1.0 - np.exp(-max(float(INFECTION_H), 0.0) / params["pathogen_load_tau_h"])

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return dict(out={"pathogen_exposure": float(self.x)}) if self.on else {}
