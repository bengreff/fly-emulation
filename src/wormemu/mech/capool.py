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
"""
from __future__ import annotations

MECHANISMS = [
    ("ca_pool_units", "Neuron bulk Ca pool fed the whole-soma Ca current (Nicoletti 2019 Eq. 28) instead of the "
     "current density", "channel", "total_current"),
]
FORMS = ("total_current", "off")
SPECS: list = []
MA_CM2_TO_PA_UM2 = 10.0                          # 1 mA/cm2 = 1e-3 A / 1e8 um2 = 10 pA/um2


class Mech:
    """Rescales vcell once at build; the mod does the rest."""

    def __init__(self, brain, params, toggles):
        v = toggles.get("ca_pool_units", "off")
        if v not in FORMS:
            raise ValueError(f"ca_pool_units form {v!r} not in {FORMS}")
        self.scale = {}
        for i, sec in enumerate(brain.soma):
            if brain.is_muscle[i]:
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
