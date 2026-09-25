"""Sensory input: body state to afferent drive.

Which afferent classes exist, and which leg each one innervates, is annotation.
How a joint angle becomes a firing rate is not: the definitive study of the
fly's main leg proprioceptor characterises it with calcium imaging and reports
no firing rates at all (F-GAP-1). So the encoding shape is taken from published
response selectivity, and every gain is a declared guess.

Afferents are ordinary nodes of the network, so the encoding delivers a
membrane current in mV and their own LIF dynamics turn it into spikes. Nothing
writes spikes into the network directly, and no unobserved world state reaches
the model except through these channels.

Classes wired here, per leg:

  chordotonal organ      femoral chordotonal organ: joint angle and velocity
  hair plate             joint angle near its limit
  campaniform sensilla   cuticular load, read as foot contact force
  leg bristle            contact

Everything else the fly senses - vision, olfaction, taste, wind, gravity,
audition, temperature - has receptors in this graph and no transduction model
in M v1. Those are registered unresolved so that "not implemented" cannot be
mistaken for "not sensing".
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .registry import Registry, Status

CACHE = Path(__file__).resolve().parents[2] / "data" / "cache"

NEUROMERE_TO_LEG = {"T1": "f", "T2": "m", "T3": "h"}
SIDE = {"L": "l", "R": "r"}

# Afferent class -> which body signal it is taken to encode.
ENCODES = {
    "chordotonal organ": "joint_angle_velocity",
    "hair plate": "joint_angle",
    "campaniform sensilla": "load",
    "leg bristle": "contact",
    "mechanosensory bristle": "contact",
}

# Modalities present in the graph with no transduction model in M v1.
UNMODELLED = {
    "ol_sensory": "vision: photoreceptor transduction and the optic lobe",
    "cb_sensory": "olfaction, taste, and other head sensory modalities",
}


def leg_from_roiinfo(roi_json: str | None) -> str | None:
    """Assign an afferent to a leg by its dominant leg neuropil."""
    if not isinstance(roi_json, str):
        return None
    try:
        rois = json.loads(roi_json)
    except Exception:
        return None
    best, best_w = None, 0
    for key, stats in rois.items():
        if not key.startswith("LegNp("):
            continue
        seg = key[6:8]
        side = key[key.rfind("(") + 1 : key.rfind(")")]
        w = stats.get("synweight", 0) or 0
        if w > best_w and seg in NEUROMERE_TO_LEG and side in SIDE:
            best, best_w = f"{SIDE[side]}{NEUROMERE_TO_LEG[seg]}", w
    return best


@dataclass
class Afferents:
    """Which network rows receive which body signal, and with what gain."""

    rows: np.ndarray            # network row index
    leg: np.ndarray             # leg key per afferent, e.g. 'lf'
    channel: np.ndarray         # 'joint_angle' | 'load' | ...
    gain_mv: np.ndarray         # mV of drive per unit of normalised signal
    baseline_mv: np.ndarray     # mV of resting drive
    joint_cols: dict[str, int]  # leg -> index of the leg's FTi joint angle
    contact_cols: dict[str, np.ndarray]   # leg -> indices into contact array
    load_bodies: dict[str, np.ndarray]    # leg -> body indices for strain
    n_neurons: int

    def drive(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        """Turn one body observation into a per-neuron current, in mV."""
        out = np.zeros(self.n_neurons, dtype=np.float32)
        angles = obs["joint_angles"]
        vels = obs["joint_velocities"]
        contact = np.linalg.norm(obs["contact_forces"], axis=-1)
        # Campaniform sensilla transduce CUTICULAR STRAIN. Ground contact force
        # is a different quantity: a leg bearing load through the air, or a leg
        # pushed by another leg, strains its cuticle with no ground contact at
        # all. The load transmitted through each body is a far closer proxy.
        # It is still not a deformation model; the segments are rigid.
        seg_load = np.linalg.norm(obs["segment_load"][:, 3:], axis=-1)

        for leg, jcol in self.joint_cols.items():
            sel = self.leg == leg
            if not sel.any():
                continue
            a = float(angles[jcol])
            v = float(vels[jcol])
            ccols = self.contact_cols.get(leg)
            load = float(contact[ccols].sum()) if ccols is not None else 0.0

            signal = np.zeros(int(sel.sum()), dtype=np.float32)
            ch = self.channel[sel]
            # Normalised, dimensionless, then scaled by an assumed gain.
            signal[ch == "joint_angle"] = np.tanh(a)
            signal[ch == "joint_angle_velocity"] = np.tanh(a) + 0.1 * np.tanh(v)
            lb = self.load_bodies.get(leg)
            strain = float(seg_load[lb].sum()) if lb is not None else 0.0
            signal[ch == "load"] = np.tanh(strain)
            signal[ch == "contact"] = np.tanh(load)
            out[self.rows[sel]] = (
                self.baseline_mv[sel] + self.gain_mv[sel] * signal
            )
        return out


def build(reg: Registry, conn, body) -> Afferents:
    n = conn.neurons
    roi = pd.read_parquet(CACHE / "male_cns_sensorimotor_roiinfo.parquet")
    roi_lut = dict(zip(roi.bodyId, roi.roiInfo))

    sens = n[n.subclass.isin(ENCODES)].copy()
    sens["leg"] = [leg_from_roiinfo(roi_lut.get(b)) for b in sens.bodyId]
    sens = sens[sens.leg.notna()]

    rows = conn.index_of(sens.bodyId.to_numpy())
    ok = rows >= 0
    sens, rows = sens[ok], rows[ok]

    gain = reg.require(
        "afferent:all", "rate_gain", units="mV per normalised stimulus",
        model_use="sensory transduction: body signal to membrane drive",
        subsystem="sensory_transduction", instances=int(len(sens)),
        minimal=8.0,
        minimal_note="declared default afferent gain",
        uncertainty="no published absolute firing-rate calibration exists for "
                    "the fly's leg proprioceptors (F-GAP-1); response "
                    "selectivity constrains the shape only",
    )
    baseline = reg.require(
        "afferent:all", "resting_drive", units="mV",
        model_use="afferent drive with the body at rest",
        subsystem="sensory_transduction", instances=int(len(sens)),
        minimal=2.0, minimal_note="declared default resting afferent drive",
        uncertainty="tonic afferent rate is unmeasured; jointly identifiable "
                    "with downstream synaptic efficacy",
        shared_with=("connection_class:all|efficacy_per_synapse",),
    )

    for subclass, grp in sens.groupby("subclass"):
        reg.provide(
            f"afferent:{subclass}", "encoded_variable", ENCODES[subclass],
            units="dimensionless",
            model_use="which body signal this afferent class reads",
            status=Status.ASSUMED,
            evidence="published response selectivity for this organ class",
            subsystem="sensory_transduction", instances=int(len(grp)),
            uncertainty="selectivity is documented; the mapping onto this "
                        "body model's coordinates is a guess",
        )
        reg.provide(
            f"afferent:{subclass}", "count", int(len(grp)), units="neurons",
            model_use="afferent population size",
            status=Status.MEASURED,
            evidence="male-cns:v1.0 subclass annotation, leg assigned by "
                     "dominant LegNp neuropil",
            subsystem="sensory_transduction", instances=int(len(grp)),
        )

    reg.provide(
        "afferent:campaniform sensilla", "transduced_variable",
        "load transmitted through the leg segment",
        units="uN and uN*mm",
        model_use="strain proxy driving campaniform afferents",
        status=Status.DERIVED,
        evidence="campaniform sensilla transduce cuticular strain; this reads "
                 "the internal interaction force through each leg segment "
                 "(MuJoCo cfrc_int), which is the load that would strain the "
                 "cuticle. Closer than ground contact force, which a loaded "
                 "leg need not have at all",
        subsystem="sensory_transduction", instances=426,
        uncertainty="the segments are RIGID, so there is no deformation and no "
                    "strain field; a thin-shell or finite-element cuticle is "
                    "what the organ actually reports",
    )

    for superclass, what in UNMODELLED.items():
        cnt = int((n.superclass == superclass).sum())
        reg.provide(
            f"population:{superclass}", "transduction_model", None,
            units="dimensionless",
            model_use="omitted from M v1",
            status=Status.UNRESOLVED,
            evidence=f"{what}: {cnt:,} receptor neurons present in the graph "
                     "with no transduction model, so they receive no input",
            subsystem="sensory_transduction", instances=cnt,
        )

    # Body column lookups.
    dof = [d for d in body.actuator_names]
    joint_cols: dict[str, int] = {}
    for leg in ["lf", "lm", "lh", "rf", "rm", "rh"]:
        want = f"{leg}_trochanterfemur-{leg}_tibia-pitch"
        for i, a in enumerate(dof):
            if a.endswith(want + "-motor"):
                joint_cols[leg] = i
                break
    contact_names = getattr(body, "contact_names", None) or [
        s if isinstance(s, str) else s.name for s in body.contact_segments
    ]
    contact_cols = {
        leg: np.array([i for i, s in enumerate(contact_names) if s.startswith(leg)])
        for leg in joint_cols
    }
    # Bodies whose transmitted load stands in for cuticular strain, per leg.
    import mujoco as mj

    m = body.sim.mj_model
    prefix = f"{body.fly.name}/"
    load_bodies = {}
    for leg in joint_cols:
        ids = []
        for b in range(m.nbody):
            nm = mj.mj_id2name(m, mj.mjtObj.mjOBJ_BODY, b) or ""
            if nm.startswith(prefix + leg + "_"):
                ids.append(b)
        load_bodies[leg] = np.array(ids, dtype=np.int64)

    return Afferents(
        rows=rows.astype(np.int64),
        leg=sens.leg.to_numpy(),
        channel=np.array([ENCODES[s] for s in sens.subclass]),
        gain_mv=np.full(len(sens), gain, dtype=np.float32),
        baseline_mv=np.full(len(sens), baseline, dtype=np.float32),
        joint_cols=joint_cols,
        contact_cols=contact_cols,
        load_bodies=load_bodies,
        n_neurons=conn.n,
    )
