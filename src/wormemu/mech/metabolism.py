"""Metabolism (PLAN row 20): the Add-my-Pet (AmP) Dynamic Energy Budget model of Caenorhabditis elegans.

Ported: Kooijman's standard DEB model with metabolic acceleration ("abj", the AmP entry's model type), its four
states and the AmP C. elegans entry's fitted parameters at T_ref 20 C (opened 6 Nov 2026,
bio.vu.nl/thb/deb/deblab/add_my_pet/entries_web/Caenorhabditis_elegans; PORT_SOURCES_ORGANS O7). The DEB lineage for
this species is Jager et al. 2005; AmP's fit is to Byerly, Cassada & Russell 1976 (Dev Biol 51:23) life history.

  states   E reserve (J), L structural length (cm, V = L^3), E_H maturity (J), E_R reproduction buffer (J)
  fluxes   p_A = f {p_Am} s_M L^2 (none before birth, E_H < E_Hb);  p_S = [p_M] L^3 (+ {p_T} s_M L^2, 0 here);
           p_C = [E] (E_G v s_M L^2 + p_S) / (kap [E] + E_G);  dE/dt = p_A - p_C;  dV/dt = (kap p_C - p_S) / E_G;
           p_J = k_J E_H;  (1 - kap) p_C - p_J goes to E_H below puberty (E_Hp), to E_R after;
           s_M = 1 before birth, L / L_b while E_Hb <= E_H < E_Hj, L_j / L_b after (the "abj" acceleration)
  eggs     continuous: kap_R x the flux into E_R / E_0 (eggs/d), E_0 the cost of an egg, found once by bisection so
           that a hatchling has the mother's reserve density f [E_m] at birth (DEB's maternal-effect rule, f = 1)
  temp     every rate x exp(T_A / T_ref - T_A / T), T from obs['head']['temperature_C']

Fed by the pharynx: f = min(1, mean pump rate / met_pump_max_hz) x X / (X + K), X = obs['head']['food_OD'], the pump
rate a running mean of outputs['pumps'] (row 13). Activity-driven Na/K-ATPase cost (row 27's outputs
['pump_atp_excess_J_per_d']) is added to somatic maintenance (DEB's [p_M] already pays the resting pumps).

Outputs: out['energy_state'] = e = [E] / [E_m] (scaled reserve density, 1 = fully fed; B1's insulin and DAF-7 read
it), out['egg_production_per_h'] (row 15's uterus reads it), out['deb'] = {E_J, L_cm, E_H_J, E_R_J, f, age_d},
out['o2_pmol_per_min'] (dissipation heat at an oxycaloric 450 kJ/mol O2).

Forms (nested): metabolism deb (default) | std (no acceleration: s_M = 1 throughout, the standard model, = deb with
E_Hj = E_Hb) | store (brain_layers' lumped energy store, verbatim; no egg output) | off. met_feeding pumps (default) |
food (DEB's own Holling functional response X / (X + K), no pharynx) | fixed (f = met_f_fixed).
Validity: one whole-animal budget (no tissues, no fat droplets); no ageing (h_a, s_G not run), no sperm limit on the
hermaphrodite's brood (~300 self sperm), egg cost fixed at f = 1; starvation: the deficit is paid from E_R, then
from structure at kap_G E_G per volume (one of Kooijman's rules); the model's day-scale clock runs at sim time, so a
10 s run moves it by ~1e-4 d.
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import Spec

MECHANISMS = [
    ("metabolism", "Dynamic Energy Budget (AmP C. elegans abj: reserve, structure, maturity, reproduction buffer), "
     "fed by pharyngeal pumping; out['energy_state'], out['egg_production_per_h'] (nested: std, store = the "
     "lumped layer)", "organ", "deb"),
    ("met_feeding", "DEB feeding: scaled functional response from pumps x food (nested: food only, fixed)", "organ",
     "pumps"),
]

AMP = "AmP Caenorhabditis_elegans entry (abj; opened 6 Nov 2026)"
BCR76 = "Byerly, Cassada & Russell 1976 Dev Biol 51:23"
KAP_G = 0.8086                                  # AmP's implied growth efficiency mu_V d_V / (w_V E_G), derived
_E0 = {}


def _s(pid, unit, v, lo, hi, src, label="published_fit", mech="metabolism", applies="whole worm", grain="global",
       notes=""):
    return Spec(pid, mech, unit, v, lo, hi, source=src, label=label, grain=grain, applies_to=applies, notes=notes)


SPECS = [
    _s("deb_p_am_J_per_d_cm2", "J/(d cm2)", 36.8735, 20.0, 60.0, AMP, notes="{p_Am}, surface-specific maximum "
       "assimilation; range guessed around the fit"),
    _s("deb_v_cm_per_d", "cm/d", 0.032076, 0.015, 0.06, AMP, notes="v, energy conductance"),
    _s("deb_kap", "1", 0.5056, 0.3, 0.9, AMP, notes="kappa, fraction of mobilised reserve to soma"),
    _s("deb_kap_r", "1", 0.95, 0.9, 0.95, AMP, notes="kappa_R, reproduction efficiency (AmP's standard fixed value)"),
    _s("deb_kap_x", "1", 0.8, 0.5, 0.9, AMP, notes="kappa_X, digestion efficiency of food to reserve (fixed in AmP)"),
    _s("deb_kap_p", "1", 0.1, 0.05, 0.3, AMP, notes="kappa_P, food to faeces"),
    _s("deb_p_m_J_per_d_cm3", "J/(d cm3)", 3724.1, 1500.0, 8000.0, AMP, notes="[p_M], volume-specific somatic "
       "maintenance"),
    _s("deb_k_j_per_d", "1/d", 0.002, 0.0005, 0.01, AMP, notes="k_J, maturity maintenance rate coefficient"),
    _s("deb_e_g_J_per_cm3", "J/cm3", 1811.0, 1000.0, 5000.0, AMP, notes="[E_G], cost of structure"),
    _s("deb_e_hb_J", "J", 3.098e-05, 1e-5, 1e-4, AMP, notes="E_H^b, maturity at birth (hatching)"),
    _s("deb_e_hj_J", "J", 0.00165, 5e-4, 5e-3, AMP, notes="E_H^j, maturity at the end of acceleration"),
    _s("deb_e_hp_J", "J", 0.005589, 2e-3, 1.5e-2, AMP, notes="E_H^p, maturity at puberty"),
    _s("deb_t_a_K", "K", 13007.8, 6000.0, 16000.0, AMP, notes="T_A, Arrhenius temperature"),
    _s("deb_t_ref_K", "K", 293.15, 293.15, 293.15, AMP, "derived", notes="the fit's reference temperature, 20 C"),
    _s("deb_del_m", "1", 0.1887, 0.1, 0.3, AMP, notes="shape coefficient: structural length / total length"),
    _s("deb_f_max_feeding", "1", 6.5, 2.0, 20.0, AMP, notes="{F_m}, maximum surface-specific searching rate, "
       "l/(d cm2); recorded for the catalog, the OD half-saturation below stands in for it"),
    _s("met_age_d", "d", 3.5, 2.9, 6.0, "N2 young adult: first eggs ~2.7-3 d after hatching at 20 C (" + BCR76 + ")",
       "guessed", notes="age since hatching at the start of a run (the brain is Cook's adult); the budget is pre-run "
       "from the egg to this age at f = 1, 20 C"),
    _s("met_pump_max_hz", "Hz", 4.2, 3.0, 5.0, "~250 pumps/min on food (Avery & Horvitz 1990; Raizen et al. 1995)",
       "measured", mech="met_feeding", notes="pump rate that gives f = 1 at saturating food"),
    _s("met_pump_tau_s", "s", 60.0, 10.0, 600.0, "this model", "guessed", mech="met_feeding",
       notes="running-mean window of the pump rate (the gut buffers intake; minutes)"),
    _s("met_food_k_od", "OD600", 0.5, 0.05, 5.0, "lawn bacteria are OD600 ~1-10; no free C. elegans half-saturation "
       "in OD found tonight", "guessed", mech="met_feeding", notes="half-saturation of intake per pump in bacterial "
       "density (DEB's K, as OD)"),
    _s("met_f_fixed", "1", 1.0, 0.0, 1.0, AMP + " (f = 1 for the zero-variate data)", "inferred", mech="met_feeding",
       notes="f of the fixed feeding form"),
    _s("met_oxycal_kJ_per_mol", "kJ/mol O2", 450.0, 430.0, 480.0, "oxycaloric equivalent for mixed substrates "
       "(Gnaiger 1983)", "inferred", notes="heat per O2 respired; recorded from memory, the paper not opened"),
    _s("met_step_s", "s", 1.0, 0.1, 10.0, "this model", "derived", notes="DEB update interval in the closed loop "
       "(rates are per day; Euler at 1 s is exact to < 1e-6)"),
]


def defaults():
    return {s.id: s.template for s in SPECS}


class Deb:
    """The abj DEB model (numpy reference; rates per day, energy in J, lengths in cm)."""

    def __init__(self, q, accel=True):
        self.q, self.accel = q, accel
        self.E_m = q["deb_p_am_J_per_d_cm2"] / q["deb_v_cm_per_d"]                    # [E_m], J/cm3
        self.L_b = self.L_j = None
        self.E_0 = None

    def tc(self, T_C=20.0):
        q = self.q
        return float(np.exp(q["deb_t_a_K"] / q["deb_t_ref_K"] - q["deb_t_a_K"] / (T_C + 273.15)))

    def s_m(self, L, E_H):
        q = self.q
        if not self.accel or E_H < q["deb_e_hb_J"] or self.L_b is None:
            return 1.0
        if E_H < q["deb_e_hj_J"]:
            return L / self.L_b
        return (self.L_j if self.L_j is not None else L) / self.L_b          # L_j is None only mid-crossing

    def fluxes(self, y, f, TC=1.0, extra_maint=0.0):
        """(dy/dt, flux dict) at state y = (E, L, E_H, E_R); f scaled feeding, TC the temperature factor."""
        q = self.q
        E, L, E_H, E_R = y
        L = max(L, 1e-9)
        V = L ** 3
        sM = self.s_m(L, E_H)
        v, pAm = q["deb_v_cm_per_d"] * TC * sM, q["deb_p_am_J_per_d_cm2"] * TC * sM
        kap, EG = q["deb_kap"], q["deb_e_g_J_per_cm3"]
        born = E_H >= q["deb_e_hb_J"]
        pA = f * pAm * L * L if born else 0.0
        pS = q["deb_p_m_J_per_d_cm3"] * TC * V + extra_maint
        Ed = E / V
        pC = Ed * (EG * v * L * L + pS) / (kap * Ed + EG)
        pJ = q["deb_k_j_per_d"] * TC * E_H
        pR = (1.0 - kap) * pC - pJ
        gS = kap * pC - pS
        dE_R = 0.0
        if gS >= 0.0:
            dV = gS / EG
        elif E_R > 0.0:
            dV, dE_R = 0.0, gS                                      # starvation: maintenance from the buffer
        else:
            dV = gS / (KAP_G * EG)                                  # then from structure
        pG = max(dV, 0.0) * EG
        if E_H < q["deb_e_hp_J"]:
            dE_H = pR
        else:
            dE_H, dE_R = 0.0, dE_R + pR
        dy = np.array([pA - pC, dV / (3.0 * L * L), dE_H, dE_R])
        return dy, {"pA": pA, "pC": pC, "pS": pS, "pJ": pJ, "pR": pR, "pG": pG,
                    "adult": E_H >= q["deb_e_hp_J"], "dE_R": dE_R}

    def heat_J_per_d(self, fl):
        """Dissipation: maintenance, maturity maintenance, growth, reproduction and assimilation overheads."""
        q = self.q
        over_a = (1.0 - q["deb_kap_x"] - q["deb_kap_p"]) / q["deb_kap_x"] * fl["pA"]
        over_g = (1.0 - KAP_G) * fl["pG"]
        over_r = (1.0 - q["deb_kap_r"]) * max(fl["pR"], 0.0) if fl["adult"] else 0.0
        mat = fl["pR"] if not fl["adult"] else 0.0                  # maturation is dissipated too
        return fl["pS"] + fl["pJ"] + over_g + over_r + over_a + max(mat, 0.0)

    def eggs_per_d(self, fl):
        if not fl["adult"] or self.E_0 is None:
            return 0.0
        return self.q["deb_kap_r"] * max(fl["dE_R"], 0.0) / self.E_0

    def integrate(self, y, t_d, f, TC=1.0, until=None, h=None):
        """RK4 from y over t_d days at constant f; `until(y)` stops early (returns y, t)."""
        h = h or min(1e-3, t_d / 50.0)
        t = 0.0
        y = np.array(y, float)
        while t < t_d - 1e-15:
            dt = min(h, t_d - t)
            k1 = self.fluxes(y, f, TC)[0]
            k2 = self.fluxes(y + 0.5 * dt * k1, f, TC)[0]
            k3 = self.fluxes(y + 0.5 * dt * k2, f, TC)[0]
            k4 = self.fluxes(y + dt * k3, f, TC)[0]
            yn = y + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
            yn[3] = max(yn[3], 0.0)
            if until is not None and until(yn):
                lo, hi = 0.0, dt                                     # bisect the crossing inside the step
                for _ in range(30):
                    m = 0.5 * (lo + hi)
                    ym = y + m * self.fluxes(y, f, TC)[0]
                    lo, hi = (m, hi) if not until(ym) else (lo, m)
                return y + hi * self.fluxes(y, f, TC)[0], t + hi
            y, t = yn, t + dt
            self._crossings(y)
        return y, t

    def _crossings(self, y):
        q = self.q
        if self.L_b is None and y[2] >= q["deb_e_hb_J"]:
            self.L_b = y[1]
        if self.L_j is None and y[2] >= q["deb_e_hj_J"]:
            self.L_j = y[1]

    def embryo(self, E_0):
        """Hatch an egg of reserve E_0 (f = 0 before birth): (state at birth, age at birth d)."""
        self.L_b = self.L_j = None
        q = self.q
        y0 = np.array([E_0, 1e-6, 0.0, 0.0])
        y, t = self.integrate(y0, 2.0, 0.0, until=lambda y: y[2] >= q["deb_e_hb_J"] or y[0] <= 0.0, h=5e-4)
        return y, t

    def solve_e0(self, f=1.0):
        """E_0 such that the hatchling's reserve density is f [E_m] (bisection on log E_0; cached per parameters)."""
        key = (f, tuple(sorted((k, v) for k, v in self.q.items() if k.startswith("deb_"))))
        if key not in _E0:
            lo, hi = np.log(1e-7), np.log(1e-3)
            for _ in range(32):
                m = 0.5 * (lo + hi)
                y, t = self.embryo(np.exp(m))
                if y[2] < self.q["deb_e_hb_J"] * (1 - 1e-9) or y[0] <= 0.0 or y[0] / y[1] ** 3 < f * self.E_m:
                    lo = m
                else:
                    hi = m
            _E0[key] = float(np.exp(hi))
        self.E_0 = _E0[key]
        y, t = self.embryo(self.E_0)
        self.L_b = y[1]
        self._crossings(y)
        return self.E_0, y, t


class Mech:
    """Steps the whole-worm energy budget; writes energy_state and egg_production_per_h."""

    def __init__(self, brain, params, toggles):
        self.brain = brain
        self.form = toggles.get("metabolism", "deb")
        self.form = {"on": "deb"}.get(self.form, self.form)
        self.feed = toggles.get("met_feeding", "pumps")
        self.feed = {"on": "pumps", "off": "fixed"}.get(self.feed, self.feed)
        assert self.form in ("deb", "std", "store", "off") and self.feed in ("pumps", "food", "fixed")
        q = defaults()
        q.update({k: float(v) for k, v in (params or {}).items() if np.isscalar(v)})
        self.q = q
        lay = getattr(brain, "layers", None)
        self.store_p = dict(getattr(lay, "p", {}) or {})
        self.deb = Deb(q, accel=self.form == "deb") if self.form in ("deb", "std") else None
        if self.deb is not None:
            self.y_birth = self.deb.solve_e0(1.0)[1]
            self.Lb_Lj = None
            y, _ = self.deb.integrate(self.y_birth, q["met_age_d"], 1.0)
            self.Lb_Lj = (self.deb.L_b, self.deb.L_j)
            self.y_start = y
        self.reset()

    def reset(self):
        self.acc_ms, self.rate_hz, self.store = 0.0, 0.0, 0.0
        if self.deb is not None:
            self.deb.L_b, self.deb.L_j = self.Lb_Lj
            self.y = self.y_start.copy()
            self.age_d = self.q["met_age_d"]
            self.last = self._report(self.y, self.feeding({}, 0.0) if self.feed == "fixed" else 0.0, 1.0, 0.0)

    def feeding(self, head, X=None):
        q = self.q
        if self.feed == "fixed":
            return q["met_f_fixed"]
        X = float(head.get("food_OD", 0.0)) if X is None else X
        hol = X / (X + q["met_food_k_od"]) if X > 0.0 else 0.0
        if self.feed == "food":
            return hol
        return min(1.0, self.rate_hz / q["met_pump_max_hz"]) * hol

    def _report(self, y, f, TC, extra):
        d = self.deb
        _, fl = d.fluxes(y, f, TC, extra)
        o2 = d.heat_J_per_d(fl) / (self.q["met_oxycal_kJ_per_mol"] * 1e3) * 1e12 / 1440.0
        return {"energy_state": float(y[0] / y[1] ** 3 / d.E_m),
                "egg_production_per_h": float(d.eggs_per_d(fl) / 24.0),
                "deb": {"E_J": float(y[0]), "L_cm": float(y[1]), "E_H_J": float(y[2]), "E_R_J": float(y[3]),
                        "f": float(f), "age_d": float(self.age_d)},
                "o2_pmol_per_min": float(o2)}

    def step(self, ctx, dt_ms):
        if self.form == "off":
            return {}
        q = self.q
        pumps = float(ctx.outputs.get("pumps", 0) or 0)
        if self.form == "store":                                     # brain_layers.Layers.metabolism, verbatim
            p = self.store_p
            self.store += pumps * p.get("met_intake_per_pump", 1e-5) \
                - self.store * dt_ms / (p.get("met_store_tau_h", 24.0) * 3.6e6)
            return {"out": {"energy_store": float(self.store)}}
        a = 1.0 - np.exp(-dt_ms / (q["met_pump_tau_s"] * 1000.0))
        self.rate_hz += a * (pumps / (dt_ms / 1000.0) - self.rate_hz)
        self.acc_ms += dt_ms
        if self.acc_ms >= q["met_step_s"] * 1000.0 - 1e-9:
            head = (ctx.obs or {}).get("head", {}) if isinstance(ctx.obs, dict) else {}
            f = self.feeding(head)
            TC = self.deb.tc(float(head.get("temperature_C", 20.0)))
            extra = float(ctx.outputs.get("pump_atp_excess_J_per_d", 0.0) or 0.0)
            h = self.acc_ms / 8.64e7
            dy, _ = self.deb.fluxes(self.y, f, TC, extra)
            self.y = self.y + h * dy
            self.y[3] = max(self.y[3], 0.0)
            self.deb._crossings(self.y)
            self.age_d += h
            self.acc_ms = 0.0
            self.last = self._report(self.y, f, TC, extra)
        return {"out": dict(self.last)}
