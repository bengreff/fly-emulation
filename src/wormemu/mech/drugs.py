"""Drugs in the bath (data model interventions; PLAN rows 7, 10 and 22).

A drug is applied to the bath at a concentration (uM) from a time on (SCHEDULE, set by wormemu.simulate). It crosses
the cuticle and gut into the body fluid as one first-order step: C' = (frac x C_bath - C) / tau, with frac the steady
body-fluid fraction of the bath and tau the uptake time (both per drug, guessed: the cuticle's permeability to each
compound is unmeasured; plate concentrations of mM against uM or nM receptor potencies say frac is small). Then:

  agonists    a tonic conductance on every cell that carries the drug's receptor class at its synapses (row 7):
              g = (the cell's summed synaptic gmax of that class) x drug_receptor_pool_ratio x occ x ss_frac,
              occ = C^h / (C^h + EC50^h), ss_frac the class's open fraction under sustained agonist (row 7, its own
              number), reversal the class's. One wgc conductance per cell (nmodl/wgc.mod, implicit in NEURON).
              levamisole -> L-AChR (lacr; the levamisole-sensitive receptor, Lewis et al. 1980 Genetics 95:905 by
              its name), ivermectin -> GluCl (glucl; avr-14, avr-15, glc-1 resistance, Dent et al. 2000 PNAS
              97:2674).
  aldicarb    inhibits acetylcholinesterase, inh = C / (C + IC50). The ACh clearance step: graded release sets the
              cleft ACh at the balance of release and clearance, so with a fraction f of clearance by AChE the
              cleft ACh of every cholinergic cell's synapses is multiplied by 1 / ((1 - f) + f (1 - inh)) (g_scale
              "release"; at most 1 / (1 - f)). Validity: clearance faster than release changes (quasi-steady
              cleft); ACh that escapes the cleft and builds up in the body fluid is not modelled; a cell that also
              releases GABA or glutamate has those synapses scaled too.
  amines      exogenous serotonin, dopamine, octopamine and tyramine: the body-fluid concentration is written as
              out['bath_amine_nM'] and neuromod adds it to every compartment's amine concentration for its GPCRs and
              the MOD-1, LGC-55 and LGC-53 channels outside synapses (row 10). Validity: uniform along the body;
              MOD-5/DAT-1 reuptake and the residual loss act on the worm's own amine only.

Neutral by default: with no drug scheduled the module builds nothing and returns nothing (bit-identical).
"""
from __future__ import annotations

import numpy as np

from wormemu import mech
from wormemu.brain_layers import Spec

MECHANISMS = [("drugs", "Drugs in the bath: first-order uptake; levamisole (L-AChR) and ivermectin (GluCl) as tonic "
               "agonist conductances, aldicarb as the ACh clearance step, exogenous 5-HT, DA, OA and TA into "
               "neuromod's compartments", "pharmacology", "on")]
M = "drugs"
SCHEDULE: list = []            # [(name, bath uM, t_on_ms)], set by wormemu.simulate before the brain builds
AGONISTS = {"levamisole": "lacr", "ivermectin": "glucl"}
AMINES = ("serotonin", "dopamine", "octopamine", "tyramine")
DRUGS = tuple(AGONISTS) + ("aldicarb",) + AMINES
NOT_CUT = "internal fraction unmeasured: the cuticle is a strong barrier to most small molecules (Burns et al. 2010 " \
          "Nat Chem Biol 6:549, qualitative)"


def _uptake(d, frac, lo, hi, tau, tlo, thi, why):
    return [Spec(f"drug_{d}_cuticle_frac", M, "1", frac, lo, hi, f"{why}; {NOT_CUT}", "guessed",
                 applies_to=f"bath {d}", notes="steady body-fluid concentration / bath concentration"),
            Spec(f"drug_{d}_uptake_tau_s", M, "s", tau, tlo, thi, why, "guessed", applies_to=f"bath {d}")]


SPECS = (
    _uptake("levamisole", 0.01, 1e-4, 1.0, 300.0, 30.0, 3000.0,
            "0.1-1 mM levamisole plates paralyse wild type within minutes (Lewis et al. 1980 Genetics 95:905, "
            "qualitative)")
    + [Spec("drug_levamisole_ec50_uM", M, "uM", 10.0, 1.0, 100.0, "levamisole is an agonist of the reconstituted "
            "L-AChR (Boulin et al. 2008 PNAS 105:18590, oocytes); its EC50 not retrieved here", "guessed",
            applies_to="L-AChR (lacr) cells"),
       Spec("drug_levamisole_hill", M, "1", 1.0, 0.8, 2.5, "not retrieved", "guessed", applies_to="L-AChR cells")]
    + _uptake("ivermectin", 0.01, 1e-4, 1.0, 600.0, 60.0, 7200.0,
              "ivermectin stops pharyngeal pumping and movement over tens of minutes at nM-uM in the bath (Dent et "
              "al. 2000 PNAS 97:2674, qualitative)")
    + [Spec("drug_ivermectin_ec50_uM", M, "uM", 0.1, 0.001, 10.0, "GluCl alpha/beta in oocytes open at nM-uM "
            "ivermectin, nearly irreversibly (Cully et al. 1994 Nature 371:707, not opened)", "guessed",
            applies_to="GluCl (glucl) cells"),
       Spec("drug_ivermectin_hill", M, "1", 1.0, 0.8, 2.5, "not retrieved", "guessed", applies_to="GluCl cells")]
    + _uptake("aldicarb", 0.01, 1e-4, 1.0, 1800.0, 300.0, 14400.0,
              "wild type paralyses on 1 mM aldicarb over 1-2 h (Mahoney, Luo and Nonet 2006 Nat Protoc 1:1772)")
    + [Spec("drug_aldicarb_ic50_uM", M, "uM", 10.0, 0.1, 1000.0, "AChE inhibition by aldicarb not retrieved for "
            "C. elegans ACE-1/ACE-2", "guessed", applies_to="acetylcholinesterase"),
       Spec("ache_clear_frac", M, "1", 0.9, 0.5, 0.99, "share of cleft ACh clearance by AChE (the rest diffusion): "
            "ace-1; ace-2 double mutants are severely uncoordinated (Culotti et al. 1981 Genetics 97:281, "
            "qualitative), so AChE dominates", "guessed", applies_to="cholinergic synapses",
            notes="the cleft ACh multiplier at full inhibition is 1 / (1 - this)")]
    + _uptake("serotonin", 1e-3, 1e-5, 0.1, 300.0, 30.0, 3600.0,
              "1-25 mM bath serotonin raises egg laying and pumping (Horvitz et al. 1982 Science 216:1012) against "
              "nM-uM receptor EC50s")
    + _uptake("dopamine", 1e-3, 1e-5, 0.1, 300.0, 30.0, 3600.0,
              "2-40 mM dopamine plates slow locomotion (Sawin, Ranganathan and Horvitz 2000 Neuron 26:619)")
    + _uptake("octopamine", 1e-3, 1e-5, 0.1, 300.0, 30.0, 3600.0,
              "4-10 mM octopamine inhibits egg laying and pumping (Horvitz et al. 1982 Science 216:1012)")
    + _uptake("tyramine", 1e-3, 1e-5, 0.1, 300.0, 30.0, 3600.0,
              "about 30 mM tyramine paralyses through LGC-55 (Pirri et al. 2009 Neuron 62:526, qualitative)")
    + [Spec("drug_receptor_pool_ratio", M, "1", 1.0, 0.5, 10.0, "receptors a bath agonist reaches over those at "
            "the cell's synapses (extrasynaptic receptors unmeasured)", "guessed",
            applies_to="levamisole and ivermectin cells")]
)


class Mech:
    def __init__(self, brain, params, toggles):
        self.p, self.brain = params, brain
        self.sched = [(d, float(c), float(t)) for d, c, t in SCHEDULE]
        bad = [d for d, _, _ in self.sched if d not in DRUGS]
        if bad:
            raise KeyError(f"drugs {bad}: not in mech.drugs.DRUGS")
        names = list(brain.cell_names)
        self.n = len(names)
        used = {d for d, _, _ in self.sched}
        self.ag = []                                    # (drug, cells, G uS at full open, erev, ss_frac, pps, pv)
        w = getattr(brain, "wsyn", None) or []
        if used & set(AGONISTS):
            from wormemu.mech import receptors
            rp = mech.params_for(receptors, brain.spec)
            for d in sorted(used & set(AGONISTS)):
                c = AGONISTS[d]
                k = mech.RECEPTOR_CLASSES.index(c)
                G = np.zeros(self.n)
                for pp, _, post, cls in w:
                    if cls == k:
                        G[post] += pp.gmax
                cells = np.flatnonzero(G > 0)
                G = G[cells] * params["drug_receptor_pool_ratio"]
                erev, ss = float(rp[f"rec_{c}_erev_mV"]), float(rp[f"rec_{c}_ss_frac"])
                pps, pv = None, None
                if getattr(brain, "soma", None) is not None and len(cells):
                    h = brain.h
                    pps = [h.wgc(brain.soma[i](0.5)) for i in cells]
                    pv = h.PtrVector(len(pps))
                    for j, pp in enumerate(pps):
                        pp.e = erev
                        pv.pset(j, pp._ref_g)
                self.ag.append((d, cells, G, erev, ss, pps, pv))
        self.ach = None
        if "aldicarb" in used:
            st = brain.st
            self.ach = np.array([float("acetylcholine" in (st.transmitter.get(c) or set())) for c in names])
        self.reset()

    def reset(self):
        self.C = {d: 0.0 for d, _, _ in self.sched}     # body-fluid uM
        for _, _, _, _, _, pps, _ in self.ag:
            for pp in pps or ():
                pp.g = 0.0

    def step(self, ctx, dt_ms):
        if not self.sched:
            return {}
        p, t, dt = self.p, ctx.t_ms, dt_ms / 1000.0
        bath = {}
        for d, c, t_on in self.sched:
            if t >= t_on:
                bath[d] = bath.get(d, 0.0) + c
        for d in self.C:
            tgt = p[f"drug_{d}_cuticle_frac"] * bath.get(d, 0.0)
            self.C[d] += (tgt - self.C[d]) * (1.0 - np.exp(-dt / p[f"drug_{d}_uptake_tau_s"]))
        out = {f"drug_{d}_uM": float(x) for d, x in self.C.items()}
        r = {}
        I = None
        for d, cells, G, erev, ss, pps, pv in self.ag:
            x, e50, hh = self.C[d], p[f"drug_{d}_ec50_uM"], p[f"drug_{d}_hill"]
            occ = x ** hh / (x ** hh + e50 ** hh) if x > 0 else 0.0
            g = G * occ * ss                             # uS
            out[f"drug_{d}_max_nS"] = float(1000.0 * g.max()) if len(g) else 0.0
            if pv is not None:
                pv.scatter(self.brain.h.Vector(g))
            elif len(cells):                             # the stand-in brain (no NEURON): an explicit current
                I = np.zeros(self.n) if I is None else I
                I[cells] += 1000.0 * g * (erev - np.asarray(ctx.v, float)[cells])     # nS x mV = pA
        if I is not None:
            r["I_pA"] = I
        if self.ach is not None:
            inh = self.C["aldicarb"] / (self.C["aldicarb"] + p["drug_aldicarb_ic50_uM"])
            f = p["ache_clear_frac"]
            m = 1.0 / ((1.0 - f) + f * (1.0 - inh))
            out["ach_cleft_factor"] = float(m)
            r["g_scale"] = {"release": np.where(self.ach > 0, m, 1.0)}
        am = {lg: 1000.0 * self.C[lg] for lg in AMINES if lg in self.C}
        r["out"] = {"drugs": out, **({"bath_amine_nM": am} if am else {})}
        return r
