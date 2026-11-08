"""Proprioception: stretch-gated channels in B-type motor neurons, DVA and SMD (audit row 17, wbody, 6 Nov 2026).

Structure (PLAN.md form, borrowed mechanism labelled inferred): no published channel model of worm proprioceptors
exists that I could open. Wen et al. 2012 (Neuron 76:750) show that B-type motor neurons are driven by the
bending of the body anterior to them (ventral bending depolarises VB, dorsal DB); Li et al. 2006 (Nature 440:684)
show DVA senses body stretch through TRP-4; Yeon et al. 2018 (PLoS Biol 16:e2004929) show SMD senses head bending
through TRP-1/TRP-2. Each is modelled as a population of stretch-gated cation channels (the generic gating-spring
form: a Boltzmann open probability in the local strain, relaxing with one time constant):

    strain        eps = sign * kappa * r            kappa (1/um) the midline curvature, r the body radius: the
                                                    strain of a fibre at the cuticle, sign set per cell class so
                                                    the cell is depolarised by the bending its papers report
    open prob.    Po_inf = 1 / (1 + exp(-(eps - eps_half) / eps_slope)),  dPo/dt = (Po_inf - Po) / tau
    current       g_max Po (E - v), E 0 mV (nonselective cation; TRP-4 and the DEG/ENaC candidates)

Fields: a B-type cell senses the mean curvature over proprio_bfield_frac of body length anterior of its soma (Wen
2012); SMD the head (s < 0.1); DVA the mean |kappa| over the whole body (its process runs the ventral cord).
Signs follow brain_layers' lumped layer (+ curvature = dorsal concave): VB eps = -kappa r, DB +kappa r, SMDD
+kappa r, SMDV -kappa r, DVA |kappa| r.

Toggle sens_proprio: "cascade" (this) | "lumped" (brain_layers' linear current, the nested form) | "off".

Toggle dva_strain_split (off by default; KNOWLEDGE_GAPS section C item 3, row 17): DVA's transduction depends on the
sign of the local strain, not its size. Compression of DVA's ventral-cord process opens TRP-4 (the cascade's channel,
now driven by the mean compression), and membrane tension opens the K2P channel TWK-16, which hyperpolarises
(a second conductance at E_K, its own Po in the mean tension; same gating constants). The ventral fibre's strain is
+kappa r (+ curvature = dorsal concave stretches the ventral side). Source: the DVA note of KNOWLEDGE_GAPS A2 (a
later DVA paper, year and venue unverified, not opened); Li et al. 2006 Nature 440:684 for TRP-4. Validity: TWK-16's
suppression of the TRP-4 current is not modelled beyond its own K+ current; both channels share proprio_eps_*.
"""
from __future__ import annotations

import numpy as np

from wormemu.mech.senses_base import CASCADE, LUMPED, Conductance, form, lumped_current, spec

MECHANISMS = [("sens_proprio", "Proprioception: stretch channels in VB/DB (Wen 2012), DVA (TRP-4), SMD (TRP-1/2)",
               "sensory", CASCADE),
              ("dva_strain_split", "DVA: compression opens TRP-4, tension opens the K2P channel TWK-16 (sign split "
               "instead of |kappa|)", "sensory", "off")]
P = "sens_proprio"
SPLIT = "dva_strain_split"
SPECS = [
    spec("proprio_radius_um", P, "um", 25, 20, 40, "measured", "Sanzeni et al. 2019 Fig 1 (adult radius ~25 um)"),
    spec("proprio_eps_half", P, "1", 0.1, 0.02, 0.3, "guessed",
         "none opened: half-activation strain; crawling bends give |kappa| r ~ 0.1-0.25 (kappa 5-10 /mm)",
         applies_to="VB, DB, DVA, SMD"),
    spec("proprio_eps_slope", P, "1", 0.03, 0.01, 0.1, "guessed", "none opened", applies_to="VB, DB, DVA, SMD"),
    spec("proprio_tau_ms", P, "ms", 20, 2, 200, "guessed",
         "none opened: Li et al. 2006 DVA Ca responses follow bending within the imaging rate",
         applies_to="VB, DB, DVA, SMD"),
    spec("proprio_E_mV", P, "mV", 0, -10, 20, "inferred", "nonselective cation channel (TRP-4, Li et al. 2006)",
         applies_to="VB, DB, DVA, SMD"),
    spec("proprio_g_b_nS", P, "nS", 0.5, 0.05, 5, "guessed", "none opened (Wen et al. 2012 report no current)",
         grain="per class", applies_to="VB, DB"),
    spec("proprio_g_dva_nS", P, "nS", 0.5, 0.05, 5, "guessed", "none opened (Li et al. 2006: Ca imaging only)",
         grain="per class", applies_to="DVA"),
    spec("proprio_g_smd_nS", P, "nS", 0.5, 0.05, 5, "guessed", "none opened (Yeon et al. 2018: Ca imaging only)",
         grain="per class", applies_to="SMDDL/R, SMDVL/R"),
    spec("proprio_bfield_frac", P, "body length", 0.4, 0.25, 0.5, "inferred",
         "Wen et al. 2012 (anterior bending drives the region behind it); as brain_layers' proprio_field_frac",
         lit="J12", applies_to="VB, DB"),
    spec("proprio_smd_s1", P, "body length", 0.1, 0.05, 0.2, "inferred",
         "Yeon et al. 2018: SMD processes sense head bending", applies_to="SMD"),
    spec("proprio_g_dva_twk16_nS", SPLIT, "nS", 0.5, 0.05, 5, "guessed",
         "none opened (KNOWLEDGE_GAPS A2: TWK-16 opens under DVA membrane tension; no current measured)",
         grain="per class", applies_to="DVA"),
    spec("proprio_ek_twk16_mV", SPLIT, "mV", -80, -90, -60, "inferred", "a K+ selective K2P channel at the "
         "worm's E_K (Nicoletti's scripts -80 mV)", applies_to="DVA"),
]


class Mech:
    def __init__(self, brain, params, toggles):
        self.b, self.p = brain, params
        self.form = form(toggles, P)
        pos = brain.layers.pos
        self.cells, self.kind, self.sign, self.s0 = [], [], [], []
        if self.form == CASCADE:
            for n, i in brain.idx.items():
                if n[:2] in ("VB", "DB") and i < len(pos) and np.isfinite(pos[i]):
                    self.cells.append(n); self.kind.append("b"); self.sign.append(-1.0 if n[0] == "V" else 1.0)
                    self.s0.append(float(pos[i]))
                elif n in ("SMDDL", "SMDDR", "SMDVL", "SMDVR"):
                    self.cells.append(n); self.kind.append("smd"); self.sign.append(1.0 if n[3] == "D" else -1.0)
                    self.s0.append(np.nan)
                elif n == "DVA":
                    self.cells.append(n); self.kind.append("dva"); self.sign.append(1.0); self.s0.append(np.nan)
        self.kind, self.sign, self.s0 = np.array(self.kind), np.array(self.sign), np.array(self.s0)
        gmap = {"b": params["proprio_g_b_nS"], "smd": params["proprio_g_smd_nS"], "dva": params["proprio_g_dva_nS"]}
        self.gmax = np.array([gmap[k] for k in self.kind]) if self.cells else np.zeros(0)
        self.cond = Conductance(brain, self.cells, params["proprio_E_mV"]) if self.cells else None
        self.split = self.form == CASCADE and toggles.get(SPLIT, "off") == "on" and "DVA" in self.cells
        self.twk = Conductance(brain, ["DVA"], params["proprio_ek_twk16_mV"]) if self.split else None
        self.reset()

    def reset(self):
        self.po = None
        self.po_t = None

    def strain(self, obs):
        p = self.p
        kap = np.asarray(obs["curvature_per_mm"], float) * 1e-3          # 1/um
        ks = np.asarray(obs["s"], float) if obs.get("s") is not None else np.linspace(0, 1, len(kap))
        r = p["proprio_radius_um"]
        k = np.zeros(len(self.cells))
        for j, kind in enumerate(self.kind):
            if kind == "b":
                sel = (ks >= self.s0[j] - p["proprio_bfield_frac"]) & (ks <= self.s0[j])
                k[j] = kap[sel].mean() if sel.any() else 0.0
            elif kind == "smd":
                sel = ks < p["proprio_smd_s1"]
                k[j] = kap[sel].mean() if sel.any() else 0.0
            elif getattr(self, "split", False):
                k[j] = np.clip(-kap, 0.0, None).mean()                     # compression of the ventral fibre
            else:
                k[j] = np.abs(kap).mean()
        return self.sign * k * r

    def step(self, ctx, dt_ms):
        p, n_all = self.p, len(ctx.names)
        I = lumped_current(self.b, [P], ctx.obs, dt_ms) if self.form == LUMPED else np.zeros(n_all)
        out = {}
        if self.cond is not None:
            eps = self.strain(ctx.obs)
            pinf = 1.0 / (1.0 + np.exp(-(eps - p["proprio_eps_half"]) / p["proprio_eps_slope"]))
            if self.po is None:
                self.po = pinf
            q = ctx.outputs.get("q10", {}).get("gating", 1.0)       # row 25, 1 without it
            self.po = self.po + (pinf - self.po) * (1.0 - np.exp(-dt_ms * q / p["proprio_tau_ms"]))
            self.cond.set(self.gmax * self.po)
            gs = np.zeros(n_all)
            np.add.at(gs, self.cond.idx, self.cond.g_nS)
            I_twk = 0.0
            if self.twk is not None:                                       # tension of the ventral fibre: TWK-16
                et = np.clip(np.asarray(ctx.obs["curvature_per_mm"], float) * 1e-3, 0.0, None).mean() * \
                    p["proprio_radius_um"]
                pt = 1.0 / (1.0 + np.exp(-(et - p["proprio_eps_half"]) / p["proprio_eps_slope"]))
                self.po_t = pt if self.po_t is None else \
                    self.po_t + (pt - self.po_t) * (1.0 - np.exp(-dt_ms * q / p["proprio_tau_ms"]))
                self.twk.set([p["proprio_g_dva_twk16_nS"] * self.po_t])
                np.add.at(gs, self.twk.idx, self.twk.g_nS)
                I_twk = self.twk.current_pA(ctx.v, n_all)
                out["dva_twk16_po"] = float(self.po_t)
            out["sens_proprio_po"] = dict(zip(self.cells, map(float, self.po)))
            out["sens_proprio_strain"] = dict(zip(self.cells, map(float, eps)))
            out["sens_I_pA"] = self.cond.current_pA(ctx.v, n_all) + I + I_twk
            out["sens_g_nS"] = gs
        if self.form == LUMPED:
            out["sens_I_pA"] = I
        return dict(I_pA=I, out=out)
