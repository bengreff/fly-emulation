"""Mechanosensory transduction: gentle touch, harsh and nose touch, plate tap (audit row 17, wbody, 6 Nov 2026).

Ported: Sanzeni, Katta, Petzold, Pruitt, Goodman & Vergassola 2019 (eLife 8:e43226), the MEC-4/MEC-10 channel
model of the touch receptor neurons (TRNs) and the body's force-indentation relation:

  indentation   F = a1 p R w0 (1 + a2 Rb/R)(1 + a3 w0/R)     eq 12, a1 0.76, a2 2.1, a3 0.66 (published fit),
                inverted for the depth w0 (um) at each contact sample from the body's contact force F (uN);
                p internal pressure, R body radius, Rb the probe radius
  filament      x' + x/tau = dGamma/dt                       eq 5, tau 1.4 ms (published fit); Gamma = w0 here
  energy        beta dG_oc = g0 - g1 |x|                     eq 8 (their g_h, g_s act on a Gamma normalised to the
                                                             bead's own deformation field, which a midline body
                                                             does not give: g0, g1 are guessed, see SPECS)
  3 states      C <-> S <-> O, eq 46-47 as printed:
                R_sc = r_cs exp((1+b)(1-a) beta dG),  R_cs = r_cs exp(b(1-a) beta dG)
                R_os = r_so exp((1+d) beta dG),       R_so = r_so exp(d a beta dG)
  current       per channel i0 in O, (is/i0) i0 in S         i0 -1.6 pA at -60 mV (measured, O'Hagan 2005,
                                                             Brown 2008), is/i0 0.71 (published fit)

Mapping onto the body (inferred): each sensory cell's channels are spread evenly over the midline samples of its
receptive field (one channel per punctum, Sanzeni after Cueva 2007), and a channel's Gamma is the indentation at
its sample (Sanzeni compute the neurite's deformation from the shell's full displacement field; a midline body
has only one depth per sample). The filament is faster (1.4 ms) than the brain's exchange interval, so within each
step Gamma ramps linearly from its old to its new value and the channel ODEs are sub-stepped (0.25 ms, implicit
Euler with the rates frozen over each sub-step). |x| gives the ON and OFF responses Sanzeni reproduce.

Shared template (said per the brief): harsh touch (PVD MEC-10/DEGT-1, Chatzigeorgiou 2010; FLP, Chatzigeorgiou &
Schafer 2011) and nose touch (ASH DEG-1, Geffeney 2011; FLP; OLQ and IL1) use the same channel kinetics with their
own channel count, g0 and g1 (per-modality Specs). Tap (Rankin 1990 plate tap): obs['tap'] (uN-equivalent) becomes
a decaying whole-body indentation added to every TRN channel's Gamma.

Toggles (forms in senses_base): sens_touch_gentle, sens_touch_harsh, sens_tap, each "cascade" | "lumped" | "off".
The conductance acts through SensG point processes (one per cell, at the soma).
"""
from __future__ import annotations

import numpy as np

from wormemu.brain_layers import NOSE, TOUCH_ANT, TOUCH_POST
from wormemu.mech.senses_base import CASCADE, LUMPED, Conductance, form, lumped_current, spec

MECHANISMS = [
    ("sens_touch_gentle", "Gentle touch: MEC-4/MEC-10 channels in ALM, AVM, PLM, PVM (Sanzeni et al. 2019)", "sensory",
     CASCADE),
    ("sens_touch_harsh", "Harsh and nose touch: PVD, FLP (body); ASH, FLP, OLQ, IL1 (nose); Sanzeni template",
     "sensory", CASCADE),
    ("sens_tap", "Plate tap: whole-body indentation pulse to the touch receptor neurons", "sensory", CASCADE),
]
IDS = [m[0] for m in MECHANISMS]

SZ = "Sanzeni et al. 2019 eLife 8:e43226"
G, H, T = "sens_touch_gentle", "sens_touch_harsh", "sens_tap"
SPECS = [
    # channel kinetics (shared by every modality here)
    spec("met_rcs_per_ms", G, "1/ms", 1 / 69.5, 1 / 200, 1 / 20, "published_fit", SZ + " (1/r_cs = 69.5 ms)",
         applies_to="every Sanzeni-template channel"),
    spec("met_b", G, "1", -0.75, -1.0, 0.0, "published_fit", SZ + " eq 46", applies_to="every Sanzeni channel"),
    spec("met_rso_per_ms", G, "1/ms", 1 / 18, 1 / 60, 1 / 5, "published_fit", SZ + " (1/r_so = 18 ms)",
         applies_to="every Sanzeni-template channel"),
    spec("met_d", G, "1", -0.56, -1.0, 0.0, "published_fit", SZ + " eq 47",
         notes="eq 47 printed R_so = r_so exp(d a beta dG); detailed balance with eq 10 would need (1+d) a: ported "
               "as printed", applies_to="every Sanzeni channel"),
    spec("met_a", G, "1", 0.5, 0.2, 0.8, "published_fit", SZ + " eq 10 (S at fraction a of the C-O energy gap)",
         applies_to="every Sanzeni channel"),
    spec("met_is_frac", G, "1", 0.71, 0.5, 0.9, "published_fit", SZ + " (is/i0)", applies_to="every Sanzeni channel"),
    spec("met_tau_ms", G, "ms", 1.4, 0.5, 5.0, "published_fit", SZ + " eq 5 (filament relaxation)",
         applies_to="every Sanzeni channel"),
    spec("met_i0_pA", G, "pA", 1.6, 1.4, 1.8, "measured", "O'Hagan et al. 2005; Brown et al. 2008 (via " + SZ + ")",
         notes="single-channel current magnitude (inward) at the holding potential", applies_to="TRN MEC-4"),
    spec("met_vhold_mV", G, "mV", -60, -75, -60, "measured", SZ + " methods (recordings at -60 mV)",
         notes="the voltage i0 refers to; the unit conductance is i0 / (E - v_hold)", applies_to="TRN MEC-4"),
    spec("met_E_mV", G, "mV", 30, 0, 60, "guessed", "none opened: DEG/ENaC channels are Na-selective, so E > 0",
         notes="O'Hagan et al. 2005's MRC I-V would pin it", applies_to="every Sanzeni channel"),
    # body mechanics feeding the channel (eq 12)
    spec("touch_pressure_kPa", G, "kPa", 40, 10, 100, "published_fit", SZ + " (p/E = 0.01 fit, E 4 MPa)",
         notes="internal hydrostatic pressure; replaced by out['pressure_kPa'] when an organ module provides it"),
    spec("touch_radius_um", G, "um", 25, 20, 40, "measured", SZ + " Fig 1 (R + t/2 about 25 um, adult)"),
    spec("touch_probe_radius_um", G, "um", 10, 3, 50, "inferred", SZ + " (standard 10 um bead)",
         notes="radius of whatever touches the body; an eyelash is wider (unmeasured here)"),
    spec("touch_a1", G, "1", 0.76, 0.6, 0.9, "published_fit", SZ + " eq 12"),
    spec("touch_a2", G, "1", 2.1, 1.5, 2.7, "published_fit", SZ + " eq 12"),
    spec("touch_a3", G, "1", 0.66, 0.4, 0.9, "published_fit", SZ + " eq 12"),
    # gentle touch (TRNs)
    spec("touch_n_channels", G, "channels per cell", 50, 10, 500, "guessed",
         "none opened: one channel per punctum (" + SZ + "); Cueva et al. 2007 puncta counts would pin it",
         grain="per type", applies_to="ALML/R, AVM, PLML/R, PVM"),
    spec("touch_g0", G, "kT", 10, 5, 20, "guessed",
         "set so the channels are closed at rest (P_S about 0.007, P_O < 1e-5); " + SZ + "'s g_h is not mappable",
         applies_to="ALML/R, AVM, PLM, PVM"),
    spec("touch_g1_per_um", G, "kT/um", 10, 1, 50, "guessed",
         "set so a 2 ms indentation step of 1 um gives no current, 3 um a small one (8% conducting) and 10 um "
         "(about the deepest indentation in " + SZ + ") saturates; Eastwood et al. 2015 MRC vs indentation would "
         "pin it", applies_to="ALML/R, AVM, PLM, PVM"),
    spec("touch_split_s", G, "body length", 0.5, 0.4, 0.6, "inferred",
         "Chalfie & Sulston 1981: ALM/AVM neurites anterior, PLM/PVM posterior, meeting near mid body",
         notes="receptive field boundary (0 nose, 1 tail)"),
    # harsh and nose touch
    spec("harsh_n_channels", H, "channels per cell", 50, 10, 500, "guessed", "none opened",
         grain="per type", applies_to="PVD, FLP, ASH, OLQ, IL1"),
    spec("nose_flp_channel_frac", H, "1", 0.5, 0.2, 1.0, "guessed", "FLP also has its head-body field, so its nose "
         "patch carries this share of harsh_n_channels (the other nose cells all of them)", applies_to="FLPL, FLPR"),
    spec("harsh_g0", H, "kT", 10, 5, 20, "guessed", "as touch_g0", applies_to="PVD, FLP, ASH, OLQ, IL1"),
    spec("harsh_g1_per_um", H, "kT/um", 1.0, 0.1, 10, "guessed",
         "a tenth of touch_g1: harsh touch needs forces about ten times larger (Way & Chalfie 1989; "
         "Chatzigeorgiou et al. 2010)", applies_to="PVD, FLP, ASH, OLQ, IL1"),
    spec("harsh_pvd_s0", H, "body length", 0.25, 0.15, 0.35, "inferred",
         "PVD menorahs cover the body behind the head (Albeg et al. 2011; Smith et al. 2010)", applies_to="PVD"),
    spec("harsh_pvd_s1", H, "body length", 0.9, 0.8, 0.95, "inferred", "as harsh_pvd_s0", applies_to="PVD"),
    spec("harsh_flp_s1", H, "body length", 0.1, 0.05, 0.15, "inferred",
         "FLP dendrites cover the head (Albeg et al. 2011)", applies_to="FLP"),
    spec("nose_g1_per_um", H, "kT/um", 1.0, 0.1, 10, "guessed", "as harsh_g1 (Geffeney et al. 2011 ASH MRC "
         "vs nose displacement would pin it)", applies_to="ASH, FLP, OLQ, IL1"),
    # tap
    spec("tap_tau_ring_ms", T, "ms", 20, 2, 200, "guessed",
         "none opened: plate vibration decay after a tap (Rankin et al. 1990 apparatus)",
         applies_to="ALML/R, AVM, PLML/R, PVM"),
]
assert len({s.id for s in SPECS}) == len(SPECS)


def indentation_um(F_uN, p_kPa, R_um, Rb_um, a1, a2, a3):
    """Sanzeni eq 12 inverted for the depth w0 (um) given the force (uN); 0 where F <= 0."""
    F = np.maximum(np.asarray(F_uN, float), 0.0)
    k = a1 * p_kPa * 1e-3 * R_um * (1 + a2 * Rb_um / R_um)        # uN/um (kPa x um = 1e-3 uN/um)
    q = a3 / R_um
    return 2 * F / (k + np.sqrt(k * k + 4 * k * q * F))           # root of k (w0 + q w0^2) = F, stable form


class Channels:
    """Vectorised Sanzeni channel patches. Patch k belongs to cell cell_of[k], has n[k] channels, and per-patch
    g0 and g1. State: x (filament, um), pc, po (C and O occupancy; S = 1 - pc - po)."""

    def __init__(self, cell_of, n, g0, g1, p):
        self.cell_of, self.n = np.asarray(cell_of, int), np.asarray(n, float)
        self.g0, self.g1 = np.asarray(g0, float), np.asarray(g1, float)
        self.rcs, self.b, self.rso, self.d, self.a = (p["met_rcs_per_ms"], p["met_b"], p["met_rso_per_ms"],
                                                      p["met_d"], p["met_a"])
        self.tau, self.isf = p["met_tau_ms"], p["met_is_frac"]
        self.reset()

    def rates(self, bdg, q=1.0):
        bdg = np.clip(bdg, -60.0, 60.0)
        a, b, d, rcs, rso = self.a, self.b, self.d, self.rcs * q, self.rso * q
        return (rcs * np.exp(b * (1 - a) * bdg), rcs * np.exp((1 + b) * (1 - a) * bdg),
                rso * np.exp(d * a * bdg), rso * np.exp((1 + d) * bdg))   # R_cs, R_sc, R_so, R_os

    def reset(self):
        rcs, rsc, rso, ros = self.rates(self.g0)
        s_c, o_s = rcs / rsc, rso / ros                 # equilibrium P_S/P_C, P_O/P_S at x = 0
        pc = 1.0 / (1.0 + s_c + s_c * o_s)
        self.pc, self.po, self.x = pc, pc * s_c * o_s, np.zeros_like(self.g0)
        self.gam = np.zeros_like(self.g0)

    def step(self, gam_new, dt_ms, h_ms=0.25, q=1.0):
        """Advance dt with Gamma ramping linearly from its last value to gam_new (um); returns the conducting
        fraction per patch, P_O + (is/i0) P_S, averaged over the step. q multiplies the gating rates (Q10, row 25;
        the filament's relaxation is mechanical and is not scaled)."""
        nsub = max(1, int(np.ceil(dt_ms / h_ms - 1e-9)))
        h = dt_ms / nsub
        rate = (np.asarray(gam_new, float) - self.gam) / dt_ms
        e = np.exp(-h / self.tau)
        x, pc, po, cond = self.x, self.pc, self.po, 0.0
        for _ in range(nsub):
            x = x * e + self.tau * rate * (1 - e)
            rcs, rsc, rso, ros = self.rates(self.g0 - self.g1 * np.abs(x), q)
            # implicit Euler on dPc = -Rcs Pc + Rsc Ps, dPo = -Ros Po + Rso Ps, Ps = 1 - Pc - Po
            m11, m12, m21, m22 = 1 + h * (rcs + rsc), h * rsc, h * rso, 1 + h * (ros + rso)
            r1, r2 = pc + h * rsc, po + h * rso
            det = m11 * m22 - m12 * m21
            pc, po = (r1 * m22 - m12 * r2) / det, (m11 * r2 - m21 * r1) / det
            cond = cond + po + self.isf * (1 - pc - po)
        self.x, self.pc, self.po, self.gam = x, pc, po, np.asarray(gam_new, float).copy()
        return cond / nsub

    def per_cell(self, frac, n_cells):
        out = np.zeros(n_cells)
        np.add.at(out, self.cell_of, self.n * frac)
        return out


class Mech:
    def __init__(self, brain, params, toggles):
        self.b, self.p = brain, params
        self.forms = {t: form(toggles, t) for t in IDS}
        self.lumped = [t for t in IDS if self.forms[t] == LUMPED]
        p = params
        self.g_unit = p["met_i0_pA"] / (p["met_E_mV"] - p["met_vhold_mV"])     # nS per open channel
        self.ks = None                                                      # built on the first step (K known)

    def _build(self, s):
        p, b = self.p, self.b
        cells, patch_cell, patch_sample, n, g0, g1 = [], [], [], [], [], []
        self.kind = []                                  # per patch: "body" (contact samples), "nose", "tap-only"

        def add_cell(c):
            if c not in cells:
                cells.append(c)
            return cells.index(c)

        def field(cs, sel, N, gg0, gg1, kind):
            j = np.flatnonzero(sel)
            for c in cs:
                if c not in b.idx or not j.size:
                    continue
                ci = add_cell(c)
                for jj in j:
                    patch_cell.append(ci); patch_sample.append(jj); n.append(N / j.size)
                    g0.append(gg0); g1.append(gg1); self.kind.append(kind)

        trn = self.forms[G] == CASCADE or self.forms[T] == CASCADE
        if trn:
            sp = p["touch_split_s"]
            field(TOUCH_ANT, s < sp, p["touch_n_channels"], p["touch_g0"], p["touch_g1_per_um"], "trn")
            field(TOUCH_POST, s >= sp, p["touch_n_channels"], p["touch_g0"], p["touch_g1_per_um"], "trn")
        if self.forms[H] == CASCADE:
            field(("PVDL", "PVDR"), (s >= p["harsh_pvd_s0"]) & (s <= p["harsh_pvd_s1"]), p["harsh_n_channels"],
                  p["harsh_g0"], p["harsh_g1_per_um"], "harsh")
            field(("FLPL", "FLPR"), s < p["harsh_flp_s1"], p["harsh_n_channels"], p["harsh_g0"],
                  p["harsh_g1_per_um"], "harsh")
            # nose: one patch per cell (half the channels for FLP, which also has its head-body field)
            for c in NOSE:
                if c in b.idx:
                    ci = add_cell(c)
                    patch_cell.append(ci); patch_sample.append(-1)
                    n.append(p["harsh_n_channels"] * (p["nose_flp_channel_frac"] if c.startswith("FLP") else 1.0))
                    g0.append(p["harsh_g0"]); g1.append(p["nose_g1_per_um"]); self.kind.append("nose")
        self.cells = cells
        self.kind = np.array(self.kind)
        self.sample = np.array(patch_sample, int)
        self.ch = Channels(patch_cell, n, g0, g1, p) if patch_cell else None
        self.cond = Conductance(b, cells, p["met_E_mV"])
        self.ks = len(s)
        self.tap_k = 0.0

    def reset(self):
        self.ks = None

    def step(self, ctx, dt_ms):
        p, obs = self.p, ctx.obs
        n_all = len(ctx.names)
        I = np.zeros(n_all)
        if self.lumped:
            I += lumped_current(self.b, self.lumped, obs, dt_ms)
        F = np.asarray(obs["contact_force_uN"], float)
        s = np.asarray(obs["s"], float) if obs.get("s") is not None else np.linspace(0, 1, len(F))
        if self.ks != len(s):
            self._build(s)
        out = {}
        if self.ch is None:
            if self.lumped:
                out["sens_I_pA"] = I
            return dict(I_pA=I, out=out)
        pk = float(ctx.outputs.get("pressure_kPa", p["touch_pressure_kPa"])) or p["touch_pressure_kPa"]
        eq = (pk, p["touch_radius_um"], p["touch_probe_radius_um"], p["touch_a1"], p["touch_a2"], p["touch_a3"])
        w = indentation_um(F, *eq) if self.forms[G] == CASCADE or self.forms[H] == CASCADE else np.zeros(len(F))
        gam = np.zeros(len(self.kind))
        trn = self.kind == "trn"
        if self.forms[G] == CASCADE:
            gam[trn] = w[self.sample[trn]]
        if self.forms[H] == CASCADE:
            hb = self.kind == "harsh"
            gam[hb] = w[self.sample[hb]]
            gam[self.kind == "nose"] = indentation_um(float(obs.get("nose_force_uN", 0.0)), *eq)
        if self.forms[T] == CASCADE:
            self.tap_k = self.tap_k * np.exp(-dt_ms / p["tap_tau_ring_ms"]) + float(obs.get("tap", 0.0))
            gam[trn] += indentation_um(self.tap_k, *eq)
        frac = self.ch.step(gam, dt_ms, q=ctx.outputs.get("q10", {}).get("gating", 1.0))
        g = self.ch.per_cell(frac, len(self.cells)) * self.g_unit
        self.cond.set(g)
        gs = np.zeros(n_all)
        np.add.at(gs, self.cond.idx, self.cond.g_nS)
        out["touch_indent_um"] = w
        out["sens_touch_po"] = dict(zip(self.cells, (self.ch.per_cell(self.ch.po, len(self.cells))
                                                     / self.ch.per_cell(np.ones_like(self.ch.po), len(self.cells)))))
        out["sens_I_pA"] = self.cond.current_pA(ctx.v, n_all) + I
        out["sens_g_nS"] = gs
        return dict(I_pA=I, out=out)
