"""The neurons' bulk Ca pool in whole-cell units (Director check, 6 Nov 2026; docs/worm/night/2026-11-06_wbrain.md).

BAAIWorm's cainternm.mod (third_party/baaiworm/mod) is Nicoletti et al. 2019 PLoS One 14:e0218738 Eq. 28,
    d[Ca]/dt = -f I_Ca/(2 F V_cell) - ([Ca] - [Ca]eq)/tau_Ca,
where I_Ca is the whole-cell Ca current in pA (EGL-19 + UNC-2 + CCA-1) and V_cell the cell's volume. The mod feeds it
NEURON's ica, which is a density (mA/cm2 = 10 pA/um2), so the influx misses the factor 10 x soma area (99 for AVAL,
241 for AWCL; BAAIWorm somas are 2 to 3 um across) and the pool stays within 0.1% of [Ca]eq at any voltage (measured:
AVAL at -15 mV, 0.05004 uM). Every Ca channel sits on the soma (BAAIWorm's neurites are passive), so the whole-cell
current is the soma's density times its area. The fix sets each neuron soma's vcell to V_cell / (10 A_soma), so the
same mod computes Eq. 28 with the whole-soma current. V_cell, f, tau_Ca and [Ca]eq stay the ledger's ca_pool values.
Muscles are excluded (their pool is B2's). Form: total_current (default) / off (BAAIWorm as ported).
No new numbers: 10 is the unit conversion (exact), the area is the model's geometry.

slo_ca_source (DEBUG_TRIAGE item 4, wbrain2, 8 Nov 2026): the Ca the four SLO channels see. BAAIWorm's network mods
(ours) compute each SLO's nanodomain from one open Ca channel, gsc = 40 pS (Nicoletti 2019): `single_channel`, the
default. BAAIWorm's single-cell tuner (eworm/single_nrn_tune/neuron_model.py:84-108) fitted the cells with
`cainternn` instead (Metaworm modfile_d: the same nanodomain formula, but with gbcav = the cell's summed SLO density in
nS/um2 where the single-channel conductance in nS belongs) and SLO mods that read it; it never inserted KCNL.
`tuner_gbar` sets each cell's SLO gsc to that sum read as nS, which reproduces cainternn's Ca (same constants).
No new numbers: the sum is the cell's own published densities.
"""
from __future__ import annotations

MECHANISMS = [
    ("ca_pool_units", "Neuron bulk Ca pool fed the whole-soma Ca current (Nicoletti 2019 Eq. 28) instead of the "
     "current density", "channel", "total_current"),
    ("slo_ca_source", "Ca seen by the SLO channels: one open channel's nanodomain (gsc 40 pS, BAAIWorm's network and "
     "Nicoletti 2019) or the tuner's cainternn (gsc = the cell's summed SLO density)", "channel", "single_channel"),
]
FORMS = ("total_current", "off")
SLO_CA = ("single_channel", "tuner_gbar")
SLO_GB = {"slo1_egl19": "gbslo1", "slo1_unc2": "gbslo1", "slo2_egl19": "gbslo2", "slo2_unc2": "gbslo2"}
SPECS: list = []
MA_CM2_TO_PA_UM2 = 10.0                          # 1 mA/cm2 = 1e-3 A / 1e8 um2 = 10 pA/um2


class Mech:
    """Rescales vcell (and, under tuner_gbar, the SLO gsc) once at build; the mods do the rest."""

    def __init__(self, brain, params, toggles):
        v = toggles.get("ca_pool_units", "off")
        if v not in FORMS:
            raise ValueError(f"ca_pool_units form {v!r} not in {FORMS}")
        src = toggles.get("slo_ca_source", "single_channel")
        if src not in SLO_CA:
            raise ValueError(f"slo_ca_source form {src!r} not in {SLO_CA}")
        self.slo_gsc = {}
        if src == "tuner_gbar":
            for i, sec in enumerate(brain.soma):
                for seg in sec:
                    ms = [getattr(seg, m) for m in SLO_GB if hasattr(seg, m)]
                    if ms:
                        g = sum(getattr(m, SLO_GB[m.name()]) for m in ms)      # nS/um2, read as nS (the tuner)
                        for m in ms:
                            m.gsc = g
                        self.slo_gsc[brain.cell_names[i]] = g
        self.scale = {}
        for i, sec in enumerate(brain.soma):
            if v == "off" or brain.is_muscle[i]:
                continue
            area = sum(seg.area() for seg in sec)
            for seg in sec:
                m = getattr(seg, "cainternm", None)
                if m is not None:
                    m.vcell = m.vcell / (MA_CM2_TO_PA_UM2 * area)
                    self.scale[brain.cell_names[i]] = MA_CM2_TO_PA_UM2 * area

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return {}
