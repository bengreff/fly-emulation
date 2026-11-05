"""The brain <-> body contract for the worm (docs/worm/INTERFACE.md is the authority; this file is its code form).

The body calls the brain in lockstep: every exchange interval (default 1 ms of biological time) it hands over a
BodyToBrain observation and gets back a BrainToBody command. The brain holds the observation constant over the
interval (zero-order hold) and returns the command at the end of it. All delays that are biology (synaptic,
neuromuscular, muscle calcium) are inside the brain; the body adds none.

Ownership: the brain worker owns BrainToBody and the sensory channel list; the body worker owns how BodyToBrain is
filled. Changes go through docs/worm/INTERFACE.md "Open between workers".

Units: ms, mV, um, uN, mM, uM, degrees C, percent (gas), mW/mm2. Body arclength s runs from 0 at the nose tip to
1 at the tail tip. Curvature is signed: positive when the dorsal side is concave (dorsal muscles shorter).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

INTERFACE_VERSION = 1

# --- the 95 body-wall muscles, in output order (Cook 2019 SI 4 names) -----------------------------------------
# Four quadrants (dorsal/ventral x left/right), 24 cells each along the body, numbered from the head; ventral left
# has 23 (vBWML24 does not exist). Measured: Cook et al. 2019 Nature 571:63 cell list.
BWM_NAMES: list[str] = (
    [f"dBWML{i}" for i in range(1, 25)] + [f"dBWMR{i}" for i in range(1, 25)]
    + [f"vBWML{i}" for i in range(1, 24)] + [f"vBWMR{i}" for i in range(1, 25)]
)
assert len(BWM_NAMES) == 95


def muscle_quadrant(name: str) -> str:
    """'DL', 'DR', 'VL' or 'VR'."""
    return name[0].upper() + name[4]


def muscle_index_along(name: str) -> int:
    """1..24 from the head."""
    return int(name[5:])


def muscle_position(name: str) -> float:
    """Approximate arclength of the muscle's centre, 0 nose .. 1 tail. GUESSED: muscle k of 24 tiles the span
    s = 0.05 .. 0.95 evenly (the first body-wall muscles start behind the pharynx bulb region, the last stop
    before the tail spike). The body worker may replace this with Virtual Worm geometry; say so in INTERFACE.md."""
    k = muscle_index_along(name)
    return 0.05 + (k - 0.5) / 24 * 0.90


# other muscle groups the brain also drives (optional for the body)
# names as in the Cook 2019 SI 5 adjacency (the cell list SI 4 spells some in lower case, e.g. pm2d, mu_sphincter)
PHARYNX_MUSCLES = ["pm1"] + [f"pm{k}{q}" for k in range(2, 8) for q in ("D", "VL", "VR")] + ["pm8"]
ENTERIC_MUSCLES = ["mu_intL", "mu_intR", "mu_anal", "mu_sph"]
# vulval and uterine (hermaphrodite sex muscles)
SEX_MUSCLES = [f"{m}{a}{s}" for m in ("vm1", "vm2", "um1", "um2") for a in ("A", "P") for s in ("L", "R")]

# --- chemical and physical stimuli at the sensory endings ---------------------------------------------------------
# What the body/world samples at the nose (amphid, labial and cephalic endings) and the tail (phasmids).
# Missing keys take the DEFAULT_WORLD value (a standard NGM plate at 20 C, no gradient). Unknown keys are ignored
# and reported once.
HEAD_CHANNELS = {
    "nacl_mM": 50.0,             # ASE (ASEL ON / ASER OFF), standard NGM ~50 mM NaCl
    "diacetyl_uM": 0.0,          # AWA (ODR-10)
    "isoamyl_alcohol_uM": 0.0,   # AWC
    "benzaldehyde_uM": 0.0,      # AWC
    "butanone_uM": 0.0,          # AWC-ON
    "nonanone_uM": 0.0,          # AWB (repellent)
    "octanol_uM": 0.0,           # ASH/ADL/AWB (repellent)
    "glycerol_mM": 0.0,          # ASH (osmotic)
    "copper_mM": 0.0,            # ASH/ADL
    "quinine_mM": 0.0,           # ASH
    "temperature_C": 20.0,       # AFD (and AWC, ASI), relative to the cultivation temperature
    "o2_pct": 21.0,              # URX/AQR/PQR (rise), BAG (fall)
    "co2_pct": 0.04,             # BAG, AFD, ASE
    "light_mW_mm2": 0.0,         # LITE-1 (ASJ, ASK, ASH, AWB, ASI) ~ blue/UV
    "food_OD": 0.0,              # bacteria at the mouth: pharynx (NSM, I2, MC drive), ADF/ASI/ASJ food cues
}
TAIL_CHANNELS = {
    "sds_mM": 0.0,               # PHA/PHB (repellent)
    "nacl_mM": 50.0,
}
DEFAULT_WORLD = {"head": HEAD_CHANNELS, "tail": TAIL_CHANNELS}


@dataclass
class BodyToBrain:
    """What the body tells the brain each exchange interval. Arrays are float64 or float32 numpy."""
    t_ms: float = 0.0
    # midline samples along the body, s in [0, 1] increasing nose -> tail, K points (K chosen by the body, >= 25)
    s: np.ndarray = field(default_factory=lambda: np.linspace(0.0, 1.0, 49))
    curvature_per_mm: np.ndarray = field(default_factory=lambda: np.zeros(49))       # signed, + = dorsal concave
    curvature_rate_per_mm_ms: np.ndarray = field(default_factory=lambda: np.zeros(49))
    # normal contact force from objects (probes, other worms, obstacles), uN, >= 0, per midline sample;
    # the substrate (agar surface) is NOT included here: it is a constant load, not a touch
    contact_force_uN: np.ndarray = field(default_factory=lambda: np.zeros(49))
    nose_force_uN: float = 0.0          # axial force on the nose tip (nose touch: ASH, FLP, OLQ, IL1)
    # per-muscle fibre strain (L / L_rest - 1), BWM_NAMES order; optional (None = brain derives it from curvature)
    muscle_strain: np.ndarray | None = None
    head: dict = field(default_factory=lambda: dict(HEAD_CHANNELS))
    tail: dict = field(default_factory=lambda: dict(TAIL_CHANNELS))
    # whole-body mechanical events the brain senses (plate tap = vibration, uN-equivalent impulse); 0 = none
    tap: float = 0.0


@dataclass
class BrainToBody:
    """What the brain tells the body each exchange interval."""
    t_ms: float
    # body-wall muscle activation in [0, 1], BWM_NAMES order: the fraction of maximal isometric active force at
    # optimal length. The brain owns membrane -> Ca -> activation (including its rise and decay); the body owns
    # activation -> force (force-length, force-velocity, passive tissue).
    muscle_activation: np.ndarray
    pharynx_activation: np.ndarray          # PHARYNX_MUSCLES order, [0, 1]
    enteric_activation: np.ndarray          # ENTERIC_MUSCLES order, [0, 1] (defecation)
    sex_muscle_activation: np.ndarray       # SEX_MUSCLES order, [0, 1] (egg-laying)
    # discrete events completed in this interval
    eggs_laid: int = 0
    expulsions: int = 0                     # defecation expulsion steps
    pumps: int = 0                          # completed pharyngeal pumps
    # pseudocoelomic pressure scale (1 = baseline; the brain moves it only if an osmotic/pressure toggle is on)
    pressure_scale: float = 1.0
    # for the viewer: per-cell soma voltage (mV) and Ca (uM), in brain.cell_names order; and GCaMP dF/F per
    # neuron (observation model) when enabled. Filled every interval; decimate as you like.
    v_mV: np.ndarray | None = None
    ca_uM: np.ndarray | None = None
    gcamp_dff: np.ndarray | None = None


def default_observation(t_ms: float = 0.0, k: int = 49) -> BodyToBrain:
    """A straight, untouched worm on a standard plate: the neural-only (open-loop) input."""
    return BodyToBrain(t_ms=t_ms, s=np.linspace(0, 1, k), curvature_per_mm=np.zeros(k),
                       curvature_rate_per_mm_ms=np.zeros(k), contact_force_uN=np.zeros(k))
