"""Glial transmitter release onto neurons (PLAN rows 11 and 17; KNOWLEDGE_GAPS section C items 1 and 2).

AMsh glia sense nose touch and feed GABA back onto ASH through LGC-37/LGC-38, shortening the touch-induced escape
(bioRxiv 2023, updated 2024, "The AMsh glia of C. elegans modulates the duration of touch-induced escape
responses"; not opened). Glial KCNQ K+ channels gate the Ca-dependent GABA release (Graziano et al. 2024 Neuron
112:1832; not opened). One AMsh activation per side, a in 0..1, follows the nose force with one time constant:

    a' = (F / (F + K_F) - a) / tau          F = obs nose_force_uN (both sides alike)
    g_ASH = g_max x a x k                    reversal: the GABA-gated Cl- class (rec_gabacl_erev_mV, row 7)

with k = 1 for wild type and glia_kcnq_null_factor in the kcnq null form. Every number is guessed: no glial Ca or
GABA current is in the papers' abstracts. LGC-37/LGC-38 are taken as GABA-gated anion channels (inferred from the
GABA-Cl- class they are named with; not confirmed).

Forms (nested): glia_gaba on | kcnq_null | off (default, neutral). Validity: nose touch only (the odorant arm of AMsh
sensing is a slot); no glial membrane, so no glial voltage or Ca dynamics beyond a.

glia_serotonin (off by default): AMsh glia release serotonin from dense-core vesicles after nose touch, and it
acts on SER-5 in ASH to enable ASH's touch Ca response; ser-5 knockdown in ASH and mod-1 knockdown in AMsh both cut
it (Logan et al. 2026 Cell Rep 45:117553; abstract read, numbers not). The same AMsh activation a sets a 5-HT
concentration added to neuromod's head compartment, out['glia_amine_nM'] = {'serotonin': c_max x a} (nM), which
every 5-HT receptor there reads (SER-5 among them, where CeNGEN detects it). Validity: the glia-to-ASH cleft is
taken as the head compartment (volume transmission, an upper bound on spread); the MOD-1 requirement in AMsh
(autocrine) is not modelled; needs the monoamines toggle on.
"""
from __future__ import annotations

import numpy as np

from wormemu import mech
from wormemu.brain_layers import Spec

M = "glia_gaba"
MECHANISMS = [(M, "AMsh glia GABA onto ASH (LGC-37/LGC-38) after nose touch, gated by glial KCNQ (nested: kcnq_null)",
               "glia", "off"),
              ("glia_serotonin", "AMsh glia serotonin after nose touch onto SER-5 (Logan et al. 2026), into "
               "neuromod's head compartment", "glia", "off")]
FORMS = ("on", "kcnq_null", "off")
M5 = "glia_serotonin"
SRC = ("bioRxiv 2023/24 AMsh glia touch-escape duration preprint; Graziano et al. 2024 Neuron 112:1832 (neither "
       "opened)")
SPECS = [
    Spec("glia_amsh_tau_s", M, "s", 2.0, 0.2, 20.0, f"{SRC}: no glial time course read", "guessed",
         applies_to="AMsh glia"),
    Spec("glia_amsh_K_uN", M, "uN", 1.0, 0.1, 10.0, f"{SRC}: half-activating nose force not read", "guessed",
         applies_to="AMsh glia"),
    Spec("glia_gaba_g_nS", M, "nS", 0.1, 0.01, 1.0, f"{SRC}: no glia-to-ASH current measured", "guessed",
         applies_to="ASHL, ASHR"),
    Spec("glia_kcnq_null_factor", M, "1", 2.0, 0.0, 5.0, "Graziano et al. 2024 Neuron 112:1832 (not opened): the "
         "release in the glial kcnq null over wild type; the sign is not read here", "guessed",
         applies_to="AMsh glia", notes="read only in the kcnq_null form"),
    Spec("glia_5ht_max_nM", M5, "nM", 100.0, 1.0, 1000.0, "Logan et al. 2026 Cell Rep 45:117553 (glial 5-HT "
         "imaged, concentration not read)", "guessed", applies_to="head compartment 5-HT receptors"),
]
CELLS = ("ASHL", "ASHR")


class Mech:
    def __init__(self, brain, params, toggles):
        self.p = params
        self.form = toggles.get(M, "off")
        if self.form not in FORMS:
            raise ValueError(f"{M} form {self.form!r} not in {FORMS}")
        self.cond = None
        if self.form != "off" and getattr(brain, "soma", None) is not None:
            from wormemu.mech import receptors
            from wormemu.mech.senses_base import Conductance
            e = float(mech.params_for(receptors, brain.spec)["rec_gabacl_erev_mV"])
            self.cond = Conductance(brain, CELLS, e)
        self.k = params["glia_kcnq_null_factor"] if self.form == "kcnq_null" else 1.0
        self.ser = toggles.get(M5, "off") == "on"
        self.reset()

    def reset(self):
        self.a = np.zeros(2)

    def step(self, ctx, dt_ms):
        if (self.cond is None or not len(self.cond)) and not self.ser:
            return {}
        p = self.p
        F = max(float(ctx.obs.get("nose_force_uN", 0.0)), 0.0)
        s = F / (F + p["glia_amsh_K_uN"])
        self.a += (s - self.a) * (1.0 - np.exp(-dt_ms / (1000.0 * p["glia_amsh_tau_s"])))
        out = {"glia_amsh_act": {"L": float(self.a[0]), "R": float(self.a[1])}}
        if self.cond is not None and len(self.cond):
            side = np.array([0 if c.endswith("L") else 1 for c in self.cond.cells])
            self.cond.set(p["glia_gaba_g_nS"] * self.a[side] * self.k)          # the SensG is implicit (NEURON)
        if self.ser:
            out["glia_amine_nM"] = {"serotonin": float(p["glia_5ht_max_nM"] * self.a.mean())}
        return dict(out=out)
