"""Chemotaxis scene (mechanism MB11), ported from BAAIWorm b99ca5ab: eworm/ghost_in_mesh_sim/worm_in_env.py
(placement) and worm_neural_network.py (`_get_concentration`, `normalize_delta_concentration`).

What upstream does (read 2026-11-05): one target point. The concentration at the head is minus the distance from the
head vertex (MetaWorm vertex 102, `Worm::mLocalContourIndex[0]`) to the target, in sim units, with no physical unit.
The brain sees only its change per control step, rescaled against the last 11 changes and clipped, as one current
into 15 sensory neurons (AWA, AWC, ASK, ALN, PLM, PHA, URY); that transducer is a brain mechanism (INTERFACE.md).
Upstream's default run is "offline": the input is a recorded signal and the gradient is not used. The food drawn on
screen, (1.83, -0.03, -0.31), is not the gradient target, (0, 0, 0). There is no plate: the worm swims in 3D fluid
and the floor is only drawn.

Here the field is evaluated in mm in the worm's rest frame (the driver's sim world) and reported as a physical
channel at the nose (vertex 102) and the tail tip (vertex 173), the INTERFACE.md `head` / `tail` dicts. Rest frame
(measured from the mesh): head at -z, tail at +z, dorsal +x, left +y (the MDL / MVL strings lie at +y).

Placement (derived): upstream rotates the worm's default forward (0, 0, -1) onto the scene heading (0, 0, 1) with
Eigen `setFromTwoVectors`; the vectors are antiparallel, so Eigen picks the axis (x, checked with Eigen 5.0.1;
upstream's Eigen 3 may pick another). The target in the worm frame is then (-0.437, -1.068, -1.749) from the start
point: 1.748 ahead, 0.408 ventral, 1.080 to the right; 2.095 sim units = 3.34 mm at L = 1 mm.

Fields (toggle `env.chemical_field`, neutral `none`):
- `none`: the default plate of INTERFACE.md, no gradient.
- `cone_published`: BAAIWorm's shape, C = c_peak - slope * r (floored at c_background), r = distance to the target.
- `exp_spot`: C = c_background + c_peak exp(-r / decay_mm), the shape Tanimoto et al. 2017 (eLife) measured for an
  odour spot on a 9 cm plate (gas phase, by gas chromatography).
Physical scale (channel presets in PRESETS, labels there): BAAIWorm's field has no unit; ours must, because our
brain transduces a concentration. Sources: docs/worm/research/CHEMOTAXIS_PLATE.md.
Placement (toggle `env.chemical_target`): `published_3d` (the target above, for the swimming scene) or
`plate_projected` (the target dropped into the plate plane through the start point; the plate normal is the
lateral axis, so 1.802 sim units = 2.87 mm away, measured).
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

import numpy as np

HEAD_VERTEX = 102  # Worm::mLocalContourIndex[0] (data/worm.meta line 6), the point upstream's gradient samples
TAIL_VERTEX = 173  # Worm::mEndEffectorIndex[1] (data/worm.meta line 5), the tail tip (s = 1.000 at rest)
L_SIM = 0.6276  # rest length in sim units (measured from the mesh, metaworm.Frame)

# Upstream numbers (published, worm_in_env.py defaults), global frame, sim units.
UPSTREAM = {
    "start_global": (0.43650287, -1.0677443, -1.7485859),
    "target_global": (0.0, 0.0, 0.0),
    "food_drawn_global": (1.8275, -0.0276, -0.3082),
    "heading_global": (0.0, 0.0, 1.0),
    "default_forward_local": (0.0, 0.0, -1.0),
    "history_len": 11,
    "input_neurons": ("AWAL", "AWAR", "AWCL", "AWCR", "ASKL", "ASKR", "ALNL", "ALNR", "PLML", "PHAL", "PHAR",
                      "URYDL", "URYDR", "URYVL", "URYVR"),
}
# Target relative to the start, worm frame (derived: the rotation above, Eigen 5.0.1).
TARGET_FROM_START_LOCAL = np.array([-0.436503, -1.067744, -1.748586])
LATERAL_AXIS = np.array([0.0, 1.0, 0.0])  # plate normal when the worm lies on its side (rest frame, measured)


def rest_length(X_rest: np.ndarray) -> float:
    """Rest length along the long axis (z in the rest frame), in the driver's units."""
    return float(np.ptp(X_rest[:, 2]))


@dataclass
class Param:
    value: float
    unit: str
    label: str  # published / measured / derived / inferred / guessed
    low: float | None = None
    high: float | None = None
    source: str = ""


# Field parameters per channel. BAAIWorm gives the shape only (its brain sees normalised changes), so every scale
# below is ours: guessed inside a cited range, or taken from a protocol. "secondary" = read in a later paper or
# summary, not in the source itself (docs/worm/research/CHEMOTAXIS_PLATE.md).
TS17 = "Tanimoto et al. 2017 eLife 6:e21629, Methods (2-nonanone gas phase on a 9 cm plate; read in the paper)"
YU = "Yamazoe-Umemoto et al. (Nat Commun; secondary): responses to +-0.01 uM/s on a ~2 uM background"
PRESETS: dict[str, dict[str, Param]] = {
    "diacetyl_uM": {
        "c_background": Param(0.0, "uM", "guessed", 0.0, 0.04, "lowest measured plate value 0.04 uM, " + TS17),
        "c_peak": Param(2.0, "uM", "guessed", 0.04, 22.9, "range = measured plate range, " + TS17 + "; 2 uM after " + YU),
        "slope_per_mm": Param(0.1, "uM/mm", "guessed", 0.02, 1.0,
                              "a worm at 0.1-0.2 mm/s then sees 0.01-0.02 uM/s, the response threshold in " + YU),
        "decay_mm": Param(10.0, "mm", "guessed", 5.0, 30.0, "exponential shape from " + TS17 + "; length not read"),
    },
    "nacl_mM": {
        "c_background": Param(0.0, "mM", "guessed", 0.0, 50.0, "far side ~0 mM (Kunitomo and Iino 2013; secondary)"),
        "c_peak": Param(100.0, "mM", "published", 50.0, 100.0, "100 mM NaCl plug, Kunitomo and Iino 2013 (secondary)"),
        "slope_per_mm": Param(0.2, "mM/mm", "published", 0.1, 0.5, "linear gradient 2 mM/cm, Luo et al. 2014 Neuron (secondary)"),
        "decay_mm": Param(20.0, "mm", "guessed", 5.0, 45.0, "no measured profile found; up to the 9 cm plate radius"),
    },
}
PARAMS: dict[str, Param] = {
    "mm_per_body_length": Param(1.0, "mm", "measured", 0.9, 1.2, "ledger worm length (adult hermaphrodite)"),
}


@dataclass
class ChemotaxisScene:
    field: str = "none"  # none | cone_published | exp_spot
    target: str = "plate_projected"  # published_3d | plate_projected
    channel: str = "diacetyl_uM"  # INTERFACE.md head key; inferred: AWA's attractant, AWA is in upstream's input set
    params: dict = dc_field(default_factory=dict)  # overrides of PARAMS and PRESETS[channel] values

    def __post_init__(self):
        if self.field not in ("none", "cone_published", "exp_spot"):
            raise ValueError(self.field)
        if self.target not in ("published_3d", "plate_projected"):
            raise ValueError(self.target)
        base = {k: p.value for k, p in {**PARAMS, **PRESETS[self.channel]}.items()}
        self.params = {**base, **self.params}

    def target_point(self, X_rest: np.ndarray) -> np.ndarray:
        """Target in the driver's sim world: the published offset from the rest head vertex (the start point), in
        body lengths, so it holds for a rescaled body (body.scale) too."""
        off = TARGET_FROM_START_LOCAL * (rest_length(X_rest) / L_SIM)
        if self.target == "plate_projected":
            off = off - (off @ LATERAL_AXIS) * LATERAL_AXIS
        return X_rest[HEAD_VERTEX] + off

    def mm_per_unit(self, X_rest: np.ndarray) -> float:
        return self.params["mm_per_body_length"] / rest_length(X_rest)

    def concentration(self, r_mm: np.ndarray) -> np.ndarray:
        p = self.params
        if self.field == "none":
            return np.full(np.shape(r_mm), np.nan)
        if self.field == "cone_published":
            return np.maximum(p["c_peak"] - p["slope_per_mm"] * np.asarray(r_mm), p["c_background"])
        return p["c_background"] + p["c_peak"] * np.exp(-np.asarray(r_mm) / p["decay_mm"])

    def sample(self, X: np.ndarray, X_rest: np.ndarray) -> tuple[dict, dict]:
        """(head, tail) stimulus dicts for one frame X [n_vertices, 3] (INTERFACE.md BodyToBrain)."""
        if self.field == "none":
            return {}, {}
        tgt = self.target_point(X_rest)
        k = self.mm_per_unit(X_rest)
        r_head = np.linalg.norm(X[HEAD_VERTEX] - tgt) * k
        r_tail = np.linalg.norm(X[TAIL_VERTEX] - tgt) * k
        head = {self.channel: float(self.concentration(r_head))}
        tail = {self.channel: float(self.concentration(r_tail))} if self.channel in ("nacl_mM", "sds_mM") else {}
        return head, tail

    def published_signal(self, X_frames: np.ndarray, X_rest: np.ndarray) -> np.ndarray:
        """Upstream's own head signal per control step: minus the head-target distance in sim units (for checks)."""
        tgt = self.target_point(X_rest)
        return -np.linalg.norm(X_frames[:, HEAD_VERTEX] - tgt, axis=1)
