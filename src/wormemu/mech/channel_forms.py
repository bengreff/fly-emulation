"""Nicoletti et al. 2024's EGL-19 and SHL-1 gating as forms of BAAIWorm's own mods (DEBUG_TRIAGE line 1, wbrain2,
8 Nov 2026).

BAAIWorm's egl19 and shl1 mods are Nicoletti et al. 2019's channels. Nicoletti et al. 2024 (PLoS ONE 19:e0298105)
fitted AIY, RIM and the motor neurons with the same two channels in changed form, and its CC-BY S1 File prints the
equations (pages 4-5 and 10-11). They are BAAIWorm's functional forms term for term (the first Gaussian of EGL-19's
tau_m is typeset without its minus sign), so each form is a set of constants for the same mods:

  off          BAAIWorm as ported (Nicoletti 2019's constants), the default
  n24_printed  the S1 File's Table S9 (EGL-19) and Table S1 (SHL-1), as printed
  n24_code     the authors' mods (github.com/martinanicoletti92/CelegansInterMotorNeuronsModels @ 84726a72), which
               made the paper's figures; their 10 mV shift is folded into the midpoints

EGL-19: printed and code agree except m_inf V0.5 (printed -5.6, code 5.6 - 10 = -4.4 mV); both move BAAIWorm's six
midpoints by -10 mV, and the code carries more figures where BAAIWorm and the table round. SHL-1: the printed table
matches neither (its tau amplitudes are BAAIWorm's / 10, except dthf; V0.5s -6.8 and -40 mV); the code uses m^1 with
weights 0.8 / 0.2 and other midpoints, and divides tau_m by 2 and tau_hf by 3, where BAAIWorm multiplies its three
taus by 0.4, 0.08 and 0.3. brain.patch_shl1_form makes those factors, the exponent and the weights GLOBALs.

Under either n24 form the EGL-19 copy inside slo1_egl19 and slo2_egl19 (the Ca channel each SLO is coupled to) takes
the same constants: the authors' slo1egl19.mod shifts its copy by the same 10 mV. Validity: the gates only; densities
stay BAAIWorm's per-cell fits, made with BAAIWorm's forms, so a cell's fit is not expected to hold under another form.
Check: scripts/worm/channels_unit_check.py --forms (Fig 3C, the AIY V-I curve).
"""
from __future__ import annotations

from wormemu.brain_layers import Spec

MECHANISMS = [
    ("egl19_kinetics", "EGL-19 (L-type Ca) gating: BAAIWorm (Nicoletti 2019, off) or Nicoletti 2024, as printed in "
     "its S1 File or as in the authors' code", "channel", "off"),
    ("shl1_kinetics", "SHL-1 (Kv4, A-type K) gating: BAAIWorm (Nicoletti 2019, off) or Nicoletti 2024, as printed in "
     "its S1 File or as in the authors' code", "channel", "off"),
]
FORMS = ("off", "n24_printed", "n24_code")
EGL19_MODS = ("egl19", "slo1_egl19", "slo2_egl19")      # the SLO mods carry their own copy of the EGL-19 gates
S1 = "Nicoletti et al. 2024 PLoS ONE 19:e0298105, S1 File (CC-BY)"
CODE = ("Nicoletti et al. 2024, the authors' mods (github.com/martinanicoletti92/CelegansInterMotorNeuronsModels "
        "@ 84726a72)")

# name: (BAAIWorm, printed, code, unit, role); role m = midpoint, s = slope or width, t = time, x = dimensionless.
# Code values: egl19.mod's PARAMETERs with shift 10 subtracted from each midpoint, bth = pds2 * pds3, eth = pds7 * pds8
EGL19 = {
    "vhm": (5.6, -5.6, -4.4, "mV", "m"), "vhh": (24.9, 14.9, 14.8573, "mV", "m"), "ki": (12.0, 12.0, 11.9541, "mV", "s"),
    "vhhb": (-20.5, -20.5, -20.5428, "mV", "m"), "kib": (8.1, 8.1, 8.0552, "mV", "s"),
    "ahinf": (1.43, 1.43, 1.4314, "1", "x"), "bhinf": (0.14, 0.14, 0.1427, "1", "x"),
    "chinf": (5.96, 5.96, 5.9589, "1", "x"), "dhinf": (0.60, 0.60, 0.6038, "1", "x"),
    "atm": (2.9, 2.9, 2.9324, "ms", "t"), "btm": (5.2, -4.8, -4.7643, "mV", "m"), "dtm": (1.9, 1.9, 1.8739, "ms", "t"),
    "etm": (1.4, -8.6, -8.607, "mV", "m"), "gtm": (2.3, 2.3, 2.3359, "ms", "t"),
    "bth": (44.6, 44.6, 44.614845, "ms", "t"), "cth": (-23.0, -33.0, -32.9723, "mV", "m"),
    "eth": (36.4, 36.4, 36.43965, "ms", "t"), "fth": (28.7, 18.7, 18.7251, "mV", "m"),
    "gth": (3.7, 3.7, 3.7125, "mV", "s"), "hth": (43.1, 43.1, 43.0937, "ms", "t"),
}
# code: shl1.mod's PARAMETERs with shalsfhit 10 subtracted from the two V0.5s; tau_m's /2 and tau_hf's /3 are tmsc, thfsc
SHL1 = {
    "vhm": (11.2, -6.8, 0.26, "mV", "m"), "ka": (14.1, 14.1, 16.25, "mV", "s"), "vhh": (-33.1, -40.0, -50.0, "mV", "m"),
    "atm": (13.8, 1.4, 13.8, "ms", "t"), "btm": (-17.5, -17.5, -40.0, "mV", "m"), "ctm": (12.9, 12.9, 12.9213, "mV", "s"),
    "dtm": (-3.7, -3.7, -40.0, "mV", "m"), "etm": (6.5, 6.5, 6.4876, "mV", "s"), "ftm": (1.9, 0.2, 1.8849, "ms", "t"),
    "athf": (539.2, 53.9, 539.1584, "ms", "t"), "bthf": (-28.2, -28.2, -60.0, "mV", "m"),
    "cthf": (4.9, 4.9, 4.9199, "mV", "s"), "dthf": (27.3, 27.3, 27.2811, "ms", "t"),
    "aths": (8422.0, 842.2, 8422.0, "ms", "t"), "bths": (-37.7, -37.7, -60.0, "mV", "m"),
    "cths": (6.4, 6.4, 6.3785, "mV", "s"), "dths": (118.9, 11.9, 118.8983, "ms", "t"),
    "mexp": (3, 3, 1, "1", "x"), "wf": (0.7, 0.7, 0.8, "1", "x"), "ws": (0.3, 0.3, 0.2, "1", "x"),
    "tmsc": (0.4, 1.0, 0.5, "1", "x"), "thfsc": (0.08, 1.0, 1.0 / 3.0, "1", "x"), "thssc": (0.3, 1.0, 1.0, "1", "x"),
}
TABLES = {"egl19": EGL19, "shl1": SHL1}
COL = {"n24_printed": 1, "n24_code": 2}
TAG = {"n24_printed": "n24p", "n24_code": "n24c"}
# the GLOBALs brain.patch_shl1_form adds to shl1.mod, at BAAIWorm's literals
SHL1_FORM = {k: SHL1[k][0] for k in ("mexp", "wf", "ws", "tmsc", "thfsc", "thssc")}


def _bounds(name, t, unit, role):
    """build_ledger.kin_bounds' rule: +-20 mV for midpoints, factor 2 for other mV quantities, factor 3 otherwise; the
    HH exponent 1 to 4 and the inactivation weights 0 to 1 (guessed)."""
    if name == "mexp":
        return 1.0, 4.0, "guessed: an HH exponent of 1 to 4"
    if name in ("wf", "ws"):
        return 0.0, 1.0, "a weight, 0 to 1"
    if role == "m":
        return t - 20.0, t + 20.0, "guessed: +-20 mV around the published value"
    f = 2.0 if unit == "mV" else 3.0
    lo, hi = sorted((t / f, t * f))
    return lo, hi, f"guessed: factor {f:g} either side of the published value"


def _specs():
    """One Spec per constant a form changes. BAAIWorm's own values are the ledger's kin_egl19_* / kin_shl1_* (set by
    brain._kinetics) and, for SHL-1's literals, the catalog's baai_shl1_hf_frac / _tm_scale / _thf_scale / _ths_scale."""
    out = []
    for form, col in COL.items():
        for ch, tab in TABLES.items():
            for name, row in tab.items():
                if row[col] == row[0]:
                    continue
                t, unit, role = float(row[col]), row[3], row[4]
                lo, hi, why = _bounds(name, t, unit, role)
                src = (f"{S1}, Table {'S9' if ch == 'egl19' else 'S1'}" if form == "n24_printed" else
                       f"{CODE}, {ch}.mod")
                out.append(Spec(f"{TAG[form]}_{ch}_{name}", f"{ch}_kinetics", unit, t, lo, hi, source=src,
                                label="published_fit", applies_to=f"every soma with {ch}"
                                + (" (and the EGL-19 copy in slo1/2_egl19)" if ch == "egl19" else ""),
                                notes=f"{form} constant {name} (BAAIWorm {row[0]:g}); bounds {why}"))
    return out


SPECS = _specs()


def form(toggles, ch):
    v = toggles.get(f"{ch}_kinetics", "off")
    if v not in FORMS:
        raise ValueError(f"{ch}_kinetics form {v!r} not in {FORMS}")
    return v


def values(form_, ch, params=None):
    """{name: value} the form sets on the channel's mods: the constants it changes ({} for off)."""
    if form_ == "off":
        return {}
    col = COL[form_]
    return {k: float(params[f"{TAG[form_]}_{ch}_{k}"]) if params is not None else float(r[col])
            for k, r in TABLES[ch].items() if r[col] != r[0]}


def restore(h):
    """BAAIWorm's literals back on the GLOBALs no ledger value sets (the SLO mods' EGL-19 copies, SHL-1's form
    constants), so a form set by an earlier Brain in the same process does not leak into the next (brain._kinetics)."""
    for mod in EGL19_MODS[1:]:
        for k, r in EGL19.items():
            setattr(h, f"{k}_{mod}", float(r[0]))
    for k, v in SHL1_FORM.items():
        setattr(h, f"{k}_shl1", float(v))


class Mech:
    """Writes the chosen form's constants into the mod GLOBALs once at build (after the ledger's kin_* values)."""

    def __init__(self, brain, params, toggles):
        h = brain.h
        self.set = {}
        for ch in TABLES:
            f = form(toggles, ch)
            if f == "off":
                continue
            v = values(f, ch, params)
            for mod in (EGL19_MODS if ch == "egl19" else ("shl1",)):
                for name, x in v.items():
                    setattr(h, f"{name}_{mod}", x)
            self.set[ch] = (f, v)

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return {}
