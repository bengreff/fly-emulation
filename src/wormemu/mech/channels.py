"""Channel library (PLAN row 4): the Nicoletti et al. 2024 channels that BAAIWorm has no model for, in every neuron
class whose CeNGEN profile detects the gene.

Nicoletti et al. 2024 PLoS ONE 19:e0298105 (code: github.com/martinanicoletti92/CelegansInterMotorNeuronsModels
@ 84726a72) models 22 currents and fits seven cells (AIY, RIM, AVAL, AVAR, VA5, VB6, VD5). Five of its channel
models have no BAAIWorm counterpart (BAAIWorm is built on Nicoletti 2019's library):

  kqt1     KQT-1, M-type K+ (kqt-1)
  unc103   UNC-103, ERG-type K+ (unc-103)
  exp2     EXP-2, the inward-rectifying Kv (exp-2)
  slo1iso  SLO-1 BK channels gated by the bulk Ca pool (slo-1), not by a Ca-channel nanodomain
  slo2iso  SLO-2 likewise (slo-2)

The mods in wormemu/nmodl/channels are Nicoletti's, copied verbatim except that the two SLO mods' Ca conversion
(the published `ca*1e3`, cai in mM) is a GLOBAL `cai_to_uM`, set here to 1 because BAAIWorm's cells hold cai in uM.
Every kinetic constant in the mods' PARAMETER blocks is a Spec here (published_fit) and is written back to the mod
GLOBAL at build, so the ledger, not the mod file, sets the numbers.

Inclusion: a neuron gets a channel when its CeNGEN class (brain_structure.cengen_class) detects the gene at
threshold 2 (Taylor et al. 2021). Density: one Spec per (channel, class), S/cm2 on the soma as BAAIWorm's own
channels (Nicoletti's whole-cell density, transferred per area):
  - a class Nicoletti 2024 fitted: the published value (nS / the model's whole-cell area), published_fit; 0 where
    the published model omits the channel (the authors fitted that cell without it). VD5's fit stands for class
    VD_DD and VA5's / VB6's for VA / VB; AVAL and AVAR are both class AVA, so AVA takes their mean (derived).
  - any other class: the median of the gene's nonzero fitted values, bounds the fitted range ([min, max], inferred)
    when two or more cells were fitted with it; one fitted cell gives [0, 2 x value] (guessed); EXP-2 (no fitted
    cell) takes the median of every nonzero K+ density in the seven fits, bounds [0, their max] (guessed).

Form (nested): channel_library baaiworm_plus_nicoletti (default) | baaiworm (no channel added: BAAIWorm as ported;
"off" is the same). Validity: soma only, as BAAIWorm (its neurites are passive); the K+ channels read the soma's ek
(the ledger's ion_ek, -77 mV in the template) where Nicoletti's scripts set -80 mV; the iso SLO channels read the
soma's bulk cai (cainternm). The published current-clamp check is scripts/worm/channels_unit_check.py.
"""
from __future__ import annotations

import re
from pathlib import Path
from statistics import median

from wormemu.brain_layers import Spec

MECHANISMS = [
    ("channel_library", "Nicoletti 2024's KQT-1, UNC-103, EXP-2 and bulk-Ca SLO-1/SLO-2 channels in every class "
     "whose CeNGEN profile detects the gene (nested: baaiworm = BAAIWorm's 16 channels only)", "channel",
     "baaiworm_plus_nicoletti"),
]
FORMS = ("baaiworm_plus_nicoletti", "baaiworm", "off")
NIC24 = ("Nicoletti et al. 2024 PLoS ONE 19:e0298105 (github.com/martinanicoletti92/CelegansInterMotorNeuronsModels "
         "@ 84726a72)")
MODS = Path(__file__).resolve().parents[1] / "nmodl" / "channels"
CHANNELS = {"kqt1": "kqt-1", "unc103": "unc-103", "exp2": "exp-2", "slo1iso": "slo-1", "slo2iso": "slo-2"}
K_CHANNELS = ("kqt1", "unc103", "exp2", "slo1iso", "slo2iso", "shl1", "shk1", "egl2", "irk", "slo1egl19",
              "slo2egl19", "slo1unc2", "slo2unc2")
CA_UNIT = {"slo1iso": "cai_to_uM", "slo2iso": "cai_to_uM"}     # the edit: BAAIWorm's cai is in uM
UNIT_CAI_UM = 1.0                                              # exact: cai is already uM

# --- the published fits: *_simulation.py g0 vectors (nS, whole cell) and each model's whole-cell area (cm2) -------
SURF_CM2 = {"AIY": 65.89e-8, "AVAL": 1123.84e-8, "AVAR": 1121.79e-8, "VA5": 389.3e-8, "VB6": 524.64e-8,
            "VD5": 351.53e-8, "RIM": 103.34e-8}
FIT_NS = {
    "AIY": dict(leak=0.14, slo1iso=1.0, kqt1=0.2, egl19=0.1, slo1egl19=0.92, nca=0.06, shl1=0.5),
    "AVAL": dict(egl19=0.104385, leak=0.150164, irk=0.1, nca=0.0),
    "AVAR": dict(egl19=0.0643372, leak=0.225225, irk=0.042079, nca=0.0493356, unc103=0.0481669),
    "VA5": dict(slo2egl19=3.0, slo2iso=3.0, egl19=0.15, irk=1.0, shk1=0.1, nca=0.01, leak=0.1),
    "VB6": dict(slo1egl19=0.2, slo2egl19=1.75, slo1unc2=1.0, slo2unc2=1.0, slo1iso=1.0, slo2iso=2.0, egl19=0.1,
                unc2=0.1, cca1=0.0, irk=1.0, shk1=0.4, nca=0.03, leak=0.13),
    "VD5": dict(slo2egl19=1.7, slo2iso=1.7, egl19=0.9, cca1=0.1, irk=0.7, shk1=1.2, nca=0.09, leak=0.2),
}
FIT_SCM2 = {"RIM": dict(shl1=9.048750067326097e-4, egl2=1.411644285181245e-4, irk=3.272854640954744e-4,     # RIM's
                        cca1=8.451919806776876e-4, unc2=9.676795045480941e-5, egl19=3.2005818627638106e-4,  # script
                        leak=9.676795045480941e-5)}                                                         # S/cm2
NS_TO_S = 1e-9
FIT_CLASS = {"AIY": ("AIY",), "RIM": ("RIM",), "AVA": ("AVAL", "AVAR"), "VA": ("VA5",), "VB": ("VB6",),
             "VD_DD": ("VD5",)}


def fitted_density(cell: str, ch: str) -> float:
    """A fitted cell's published density of one channel (S/cm2; 0 where its model omits the channel)."""
    if cell in FIT_SCM2:
        return FIT_SCM2[cell].get(ch, 0.0)
    return FIT_NS[cell].get(ch, 0.0) * NS_TO_S / SURF_CM2[cell]


def _cells_fitted_with(ch):
    return {c: fitted_density(c, ch) for c in SURF_CM2 if fitted_density(c, ch) > 0}


# --- kinetic constants: the mods' PARAMETER blocks -------------------------------------------------------------------
NOT_KINETIC = {"v", "ek", "eca", "cai", "celsius", "gbar", "cai_to_uM",
               "fondo",          # slo1iso declares it and never uses it
               "c1", "c2"}       # RANGE unity multipliers on the SLO time constants (never set in the published code)


def parse_params(mod: Path):
    """[(name, value, unit)] from a mod's first PARAMETER block (wormemu's own copy of build_ledger.parse_mod)."""
    out, inside = [], False
    for line in mod.read_text().splitlines():
        if line.strip().startswith("PARAMETER"):
            inside = True
            continue
        if inside and line.strip().startswith("}"):
            break
        if inside:
            m = re.match(r"\s*(\w+)\s*=\s*([-+0-9.eE]+)\s*(\(([^)]*)\))?", line)
            if m and m.group(1) not in NOT_KINETIC:
                out.append((m.group(1), float(m.group(2)), (m.group(4) or "1").strip()))
    return out


def kin_bounds(name, unit, t):
    """build_ledger.kin_bounds' rule for these mods: +-20 mV for half-(in)activations (va, vi), factor 2 for other
    mV quantities, factor 3 for everything else; sign kept."""
    if unit == "mV" and re.match(r"v[ai](_|$)", name):
        return t - 20.0, t + 20.0, "guessed: +-20 mV around the published value"
    f = 2.0 if unit == "mV" else 3.0
    lo, hi = sorted((t / f, t * f))
    return lo, hi, f"guessed: factor {f:g} either side of the published value"


KINETICS = {ch: parse_params(MODS / f"{ch}.mod") for ch in CHANNELS}


def _kin_specs():
    out = []
    for ch, rows in KINETICS.items():
        for name, t, unit in rows:
            lo, hi, why = kin_bounds(name, unit, t)
            out.append(Spec(f"kin_{ch}_{name}", "channel_library", unit, t, lo, hi, source=NIC24,
                            label="published_fit", grain="global", applies_to=f"every soma with {ch}",
                            notes=f"{ch}.mod PARAMETER {name}; bounds {why}"))
    return out


# --- densities: one Spec per (channel, CeNGEN class that detects the gene) -------------------------------------------
def _classes_detecting():
    from wormemu.brain_structure import load_structure
    st = load_structure()
    det = {}
    for ch, gene in CHANNELS.items():
        row = st.tpm[st.gene_index[gene]] if gene in st.gene_index else None
        det[ch] = [c for k, c in enumerate(st.cengen_classes) if row is not None and row[k] > 0]
    return det


def _density_specs():
    out = []
    allk = [x for c in SURF_CM2 for ch in K_CHANNELS if (x := fitted_density(c, ch)) > 0]
    for ch, classes in _classes_detecting().items():
        fit = _cells_fitted_with(ch)
        vals = sorted(fit.values())
        if len(vals) >= 2:
            t, lo, hi, lab = median(vals), vals[0], vals[-1], "inferred"
            why = f"median of the {len(vals)} fitted cells ({', '.join(fit)}); bounds their range"
        elif len(vals) == 1:
            t, lo, hi, lab = vals[0], 0.0, 2.0 * vals[0], "guessed"
            why = f"the one fitted cell's value ({next(iter(fit))}); bounds [0, 2x] guessed"
        else:
            t, lo, hi, lab = median(allk), 0.0, max(allk), "guessed"
            why = (f"no fitted cell has {ch}: the median of all {len(allk)} nonzero K+ densities in the seven "
                   f"Nicoletti 2024 fits; bounds [0, their max]")
        for cls in classes:
            if cls in FIT_CLASS:
                cells = FIT_CLASS[cls]
                v = sum(fitted_density(c, ch) for c in cells) / len(cells)
                lab_c = "published_fit" if len(cells) == 1 else "derived"
                note = (f"{'mean of the ' if len(cells) > 1 else ''}published fit of {' and '.join(cells)}"
                        + (" (the published model omits the channel)" if v == 0 else "")
                        + ("; one fitted cell stands for the class" if cls in ("VA", "VB", "VD_DD") else ""))
                out.append(Spec(f"dens_{ch}_{cls}", "channel_library", "S/cm2", v, 0.0, max(hi, v), source=NIC24,
                                label=lab_c, grain="class", applies_to=f"CeNGEN class {cls}", notes=note))
            else:
                out.append(Spec(f"dens_{ch}_{cls}", "channel_library", "S/cm2", t, lo, hi, source=NIC24, label=lab,
                                grain="class", applies_to=f"CeNGEN class {cls}",
                                notes=f"{CHANNELS[ch]} detected at CeNGEN threshold 2; no fit for the class: {why}"))
    return out


SPECS = _kin_specs() + _density_specs()
DENSITY = {s.id: s for s in SPECS if s.id.startswith("dens_")}


def form(toggles):
    v = toggles.get("channel_library", "off")
    if v not in FORMS:
        raise ValueError(f"channel_library form {v!r} not in {FORMS}")
    return v


def build_cell(brain, name, obj, params, toggles):
    """Insert the added channels into one neuron's soma (called by the brain while it builds each cell, before its
    pointers and conductance targets exist). Returns {channel: density} for the channels inserted."""
    if form(toggles) != "baaiworm_plus_nicoletti" or name not in brain.st.index \
            or brain.st.kind[brain.st.index[name]] != "neuron":
        return {}
    from wormemu.brain_structure import cengen_class
    if not hasattr(brain, "_cengen"):
        brain._cengen = set(brain.st.cengen_classes)
    cls = cengen_class(name, brain._cengen)
    put = {}
    for ch in CHANNELS:
        pid = f"dens_{ch}_{cls}"
        if pid not in DENSITY:
            continue
        g = float(params[pid])
        obj.Soma.insert(ch)
        for seg in obj.Soma:
            getattr(seg, ch).gbar = g
        put[ch] = g
    brain.added_channels = getattr(brain, "added_channels", {})
    brain.added_channels[name] = put
    return put


class Mech:
    """Writes the kinetic Specs and the Ca unit into the mod GLOBALs; the channels need nothing per step."""

    def __init__(self, brain, params, toggles):
        self.on = form(toggles) == "baaiworm_plus_nicoletti"
        if not self.on:
            return
        h = brain.h
        for ch, rows in KINETICS.items():
            for name, _, _ in rows:
                setattr(h, f"{name}_{ch}", float(params[f"kin_{ch}_{name}"]))
            if ch in CA_UNIT:
                setattr(h, f"{CA_UNIT[ch]}_{ch}", UNIT_CAI_UM)

    def reset(self):
        pass

    def step(self, ctx, dt_ms):
        return {}
