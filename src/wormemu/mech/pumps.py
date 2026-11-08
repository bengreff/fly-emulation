"""Na/K-ATPase per cell (PLAN row 27): activity-driven Na+ load, the pump's current and its ATP cost, lumped.

Ported: the Luo & Rudy 1994 (Circ Res 74:1071) Na/K pump, the standard form reused in neuron models,
  I_p = I_max f_NaK(V) / (1 + (K_mNa / [Na]i)^1.5) x [K]o / ([K]o + K_mK),
  f_NaK = 1 / (1 + 0.1245 exp(-0.1 V F/RT) + 0.0365 sigma exp(-V F/RT)), sigma = (exp([Na]o / 67.3) - 1) / 7,
one net outward charge and one ATP per cycle (3 Na out, 2 K in). C. elegans has the pump (EAT-6 alpha subunit,
Davis et al. 1995), but no per-cell density is published: I_max per neuron and per muscle are guessed.

Lumped per cell (every cell of ctx.v: the neurons and the brain's muscles), one [Na]i state in the cell's volume:
  d[Na]i/dt = (3 I_p,rest + g_Na (V - V0)^+ - 3 I_p) / (F vol),
V0 the cell's mean voltage over the first pump_v0_ms of a run (its rest in this network), I_p,rest = I_p at
([Na]rest, V0). The resting influx is set to balance the resting pump, so at rest nothing changes; C. elegans
neurons have no voltage-gated Na+ channels, so the activity load is a guessed Na-carrying conductance (cation
channels, nAChRs) per mV above rest. Injected current: -(I_p - I_p,rest), the change of the pump current from rest
(the fitted leaks already contain the resting pump), so a load gives a pump after-hyperpolarisation.
A neuron's volume is its hoc morphology's (scan; 13 to 856 um3), and its I_max and g_Na scale with its membrane area,
the templates being the median neuron's (a density x area rule); the muscles keep the per-cell values (the brain's
muscle is a stand-in cylinder).
Outputs: out['na_i_mM'], out['pump_current_pA'] (injected), out['pump_atp_J_per_d'] (all cells),
out['pump_atp_excess_J_per_d'] (above rest; mech.metabolism adds it to somatic maintenance).

Forms (nested): na_k_pump on (default) | rest (pump fixed at rest: no current, constant ATP; = on with g_Na 0 at
rest) | null (ouabain / eat-6 loss: no pump; the resting pump current is lost, [Na]i climbs) | off (nothing).
Validity: one well-mixed [Na]i per cell (no axonal or dendritic gradients); [K]o fixed at the bath (the amphid
glia's K+ rise is not read); the Na load is linear in depolarisation; mammalian cardiac affinities.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

MECHANISMS = [
    ("na_k_pump", "Na/K-ATPase per neuron and muscle (Luo-Rudy 1994 form): activity-driven Na+ load, pump current "
     "from rest, ATP cost to metabolism (nested: rest, null = ouabain)", "membrane", "on"),
]

F = 96485.0
NA_MM_PER_PA_S_UM3 = 1e-12 / F / 1e-15 * 1e3          # mM/s per pA into 1 um3 (10.36), derived
LR94 = "Luo & Rudy 1994 Circ Res 74:1071"


def _s(pid, unit, v, lo, hi, src, label="guessed", applies="neurons and muscles", grain="class", notes=""):
    return Spec(pid, "na_k_pump", unit, v, lo, hi, source=src, label=label, grain=grain, applies_to=applies,
                notes=notes)


SPECS = [
    _s("pump_imax_neuron_pA", "pA", 10.0, 1.0, 50.0, "no C. elegans pump density published (EAT-6, Davis et al. "
       "1995)", applies="neurons", notes="maximal pump current of the median-area neuron (others scale with area); "
       "guessed so [Na]i recovers in ~10-20 s"),
    _s("pump_imax_muscle_pA", "pA", 100.0, 10.0, 500.0, "no C. elegans pump density published", applies="muscles",
       notes="maximal pump current per muscle cell; guessed (volume ratio x the neuron's density)"),
    _s("pump_km_nai_mM", "mM", 10.0, 5.0, 20.0, LR94, "published_fit", grain="global",
       notes="internal Na half-activation (mammalian cardiac)"),
    _s("pump_hill_nai", "1", 1.5, 1.0, 3.0, LR94, "published_fit", grain="global", notes="Na Hill coefficient"),
    _s("pump_km_ko_mM", "mM", 1.5, 0.5, 3.0, LR94, "published_fit", grain="global",
       notes="external K half-activation"),
    _s("pump_na_o_mM", "mM", 140.0, 100.0, 160.0, "C. elegans recording saline ~145 mM NaCl (Goodman et al. 1998)",
       "inferred", grain="global", notes="pseudocoelomic Na+"),
    _s("pump_k_o_mM", "mM", 5.0, 2.0, 10.0, "recording saline 5 mM KCl (Goodman et al. 1998); = glia_k_bath_mM",
       "inferred", grain="global", notes="pseudocoelomic K+"),
    _s("pump_na_rest_mM", "mM", 10.0, 5.0, 20.0, "typical cytosolic Na+ (mammalian neurons 5-15 mM)", "inferred",
       grain="global", notes="resting [Na]i; no C. elegans measurement found"),
    _s("pump_vol_neuron_um3", "um3", 100.0, 20.0, 500.0, "soma 2-3 um across plus neurite (WormAtlas)",
       applies="neurons", notes="volume [Na]i fills; guessed. Used only without a brain's morphology (the numpy "
       "reference); a brain's neurons take their own hoc volume"),
    _s("pump_vol_muscle_um3", "um3", 3000.0, 1000.0, 10000.0, "body-wall muscle cell ~100 x 10 x 3 um (WormAtlas)",
       applies="muscles", notes="guessed"),
    _s("pump_gna_neuron_nS", "nS", 0.2, 0.02, 2.0, "this model", applies="neurons",
       notes="the median-area neuron's Na-carrying conductance per mV of depolarisation above rest; guessed"),
    _s("pump_gna_muscle_nS", "nS", 2.0, 0.2, 20.0, "this model (nAChR and leak Na entry)", applies="muscles",
       notes="guessed"),
    _s("pump_atp_kJ_per_mol", "kJ/mol", 55.0, 45.0, 65.0, "cytosolic free energy of ATP hydrolysis, ~50-60 kJ/mol",
       "inferred", grain="global", notes="energy per pump cycle"),
    _s("pump_rt_f_mV", "mV", 25.26, 24.0, 26.7, "R T / F at 20 C", "derived", grain="global"),
    _s("pump_v0_ms", "ms", 1000.0, 100.0, 5000.0, "this model", "derived", grain="global",
       notes="window over which each cell's resting voltage V0 is averaged; no load or current in it"),
]


def defaults():
    return {s.id: s.template for s in SPECS}


class Pump:
    """Luo-Rudy pump current and the lumped [Na]i per cell (numpy reference)."""

    def __init__(self, q, muscle, geom=None):
        """geom: (volume um3, membrane area um2) per cell from the morphology, or None (the per-cell templates)."""
        self.q = q
        mus = np.asarray(muscle, bool)
        pick = lambda a, b: np.where(mus, q[b], q[a])
        self.imax = pick("pump_imax_neuron_pA", "pump_imax_muscle_pA")
        self.vol = pick("pump_vol_neuron_um3", "pump_vol_muscle_um3")
        self.gna = pick("pump_gna_neuron_nS", "pump_gna_muscle_nS")
        if geom is not None and (~mus).any():
            vol, area = (np.asarray(x, float) for x in geom)
            rel = np.where(mus, 1.0, area / np.median(area[~mus]))
            self.vol = np.where(mus, self.vol, vol)
            self.imax, self.gna = self.imax * rel, self.gna * rel
        sig = (np.exp(q["pump_na_o_mM"] / 67.3) - 1.0) / 7.0
        self.sig = sig
        self.kf = q["pump_k_o_mM"] / (q["pump_k_o_mM"] + q["pump_km_ko_mM"])

    def i_p(self, na, v):
        q = self.q
        u = np.asarray(v, float) / q["pump_rt_f_mV"]
        f = 1.0 / (1.0 + 0.1245 * np.exp(-0.1 * u) + 0.0365 * self.sig * np.exp(-u))
        h = 1.0 / (1.0 + (q["pump_km_nai_mM"] / np.maximum(na, 1e-9)) ** q["pump_hill_nai"])
        return self.imax * f * h * self.kf

    def atp_J_per_d(self, ip):
        return float(np.sum(ip)) * 1e-12 / F * self.q["pump_atp_kJ_per_mol"] * 1e3 * 86400.0


class Mech:
    def __init__(self, brain, params, toggles):
        self.form = toggles.get("na_k_pump", "on")
        assert self.form in ("on", "rest", "null", "off")
        q = defaults()
        q.update({k: float(v) for k, v in (params or {}).items() if np.isscalar(v)})
        self.q = q
        cells = getattr(brain, "cells", None)
        self.geom = None if not cells else (
            [sum(seg.volume() for sec in c.all for seg in sec) for c in cells],
            [sum(seg.area() for sec in c.all for seg in sec) for c in cells])
        self.reset()

    def reset(self):
        self.pump, self.na, self.vsum, self.nv, self.t = None, None, None, 0, 0.0
        self.v0 = self.ip_rest = None

    def step(self, ctx, dt_ms):
        if self.form == "off":
            return {}
        q = self.q
        v = np.asarray(ctx.v, float)
        if self.pump is None:
            mus = getattr(ctx, "is_muscle", None)
            self.pump = Pump(q, np.zeros(len(v), bool) if mus is None else mus,
                             self.geom if self.geom is not None and len(self.geom[0]) == len(v) else None)
            self.na = np.full(len(v), q["pump_na_rest_mM"])
            self.vsum = np.zeros(len(v))
        p, n = self.pump, len(v)
        self.t += dt_ms
        if self.v0 is None:
            self.vsum += v * dt_ms
            self.nv += dt_ms
            ip = p.i_p(self.na, v)
            if self.t >= q["pump_v0_ms"] - 1e-9:
                self.v0 = self.vsum / self.nv
                self.ip_rest = p.i_p(np.full(n, q["pump_na_rest_mM"]), self.v0)
            atp = p.atp_J_per_d(ip)
            return {"out": {"na_i_mM": self.na.copy(), "pump_current_pA": np.zeros(n), "pump_atp_J_per_d": atp,
                            "pump_atp_excess_J_per_d": 0.0}}
        if self.form == "rest":
            return {"out": {"na_i_mM": self.na.copy(), "pump_current_pA": np.zeros(n),
                            "pump_atp_J_per_d": p.atp_J_per_d(self.ip_rest), "pump_atp_excess_J_per_d": 0.0}}
        ip = np.zeros(n) if self.form == "null" else p.i_p(self.na, v)
        load = 3.0 * self.ip_rest + p.gna * np.maximum(v - self.v0, 0.0)          # Na entry as pA of charge
        self.na = self.na + (load - 3.0 * ip) * NA_MM_PER_PA_S_UM3 / p.vol * dt_ms / 1000.0
        I = -(ip - self.ip_rest)
        atp = p.atp_J_per_d(ip)
        return {"I_pA": I, "out": {"na_i_mM": self.na.copy(), "pump_current_pA": I, "pump_atp_J_per_d": atp,
                                   "pump_atp_excess_J_per_d": atp - p.atp_J_per_d(self.ip_rest)}}
