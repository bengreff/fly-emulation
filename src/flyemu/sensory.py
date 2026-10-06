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
  mechanosensory bristle contact

Everything else the fly senses - vision, olfaction, taste, wind, gravity,
audition, temperature - has receptors in this graph and no transduction model
in M v1. Those are registered unresolved so that "not implemented" cannot be
mistaken for "not sensing".
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
import os
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
    # "leg bristle" is NOT here: in male-cns that subclass is class
    # gustatory (768 LgLG/LgAG taste neurons). It was driven as touch until
    # session 5 (F-CENSUS-1).
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


# Leg nerves (Court et al. 2020 Neuron 107:1071, VNC nerve nomenclature, as used in male-cns).
LEG_NERVES = {"ProLN", "MesoLN", "MetaLN"}


def entry_nerves() -> dict[str, str]:
    """Cell type -> entry nerve(s) ';'-joined, from the sensory census (male-cns entry nerve per type)."""
    cen = pd.read_csv(Path(__file__).resolve().parents[2] / "data" / "derived" / "sensory_census.csv")
    out = {}
    for g, e in zip(cen.group, cen.entry_nerves):
        for t in str(g).split(","):
            out[t] = str(e) if isinstance(e, str) else ""
    return out


def enters_by_leg_nerve(nerves: str) -> bool | None:
    """True/False when the entry nerve is known, None when it is not."""
    parts = [x for x in str(nerves).split(";") if x and x != "nan"]
    if not parts:
        return None
    return any(x in LEG_NERVES for x in parts)


def assign_by_nerve(reg: Registry) -> int:
    return int(reg.require(
        "sense:mechano", "assign_by_nerve", units="enum",
        model_use="0 legacy: a mechanosensory afferent is a leg sensor if it has any leg-neuropil "
                  "synapses (dominant LegNp); 1 only if its type enters by a leg nerve (census entry "
                  "nerve); wing-nerve (ADMN) and haltere-nerve (DMetaN) campaniforms go to the wing and "
                  "haltere strain channels, prosternal-nerve hair plates to the neck (F-SENSE-NERVE-1); "
                  "2 as 1 but by each cell's own entry nerve and root side where male-cns records them "
                  "(leg = side + segment of its leg nerve), combined type names split (F-SENSE-NERVE-2)",
        subsystem="sensory_transduction", minimal=0, minimal_note="legacy dominant-leg-neuropil rule"))


SEGMENT_OF_NERVE = {"ProLN": "f", "MesoLN": "m", "MetaLN": "h"}
# Prothoracic nerves other than the leg nerve. male-cns front-leg hair plates enter here
# (SNpp45 by VProN, SNpp52 by DProN; ProLN carries 1), so a cell entering by one of them
# is not excluded on its own nerve: its type decides, as under option 1 (inferred).
PROTHORACIC_OTHER = {"DProN", "VProN", "ProAN"}


@lru_cache(maxsize=1)
def cell_nerves() -> dict[int, tuple[str, str]]:
    """bodyId -> (entry nerve, root side) per cell, from male-cns (measured); '' when absent."""
    e = pd.read_parquet(CACHE / "male_cns_extra.parquet", columns=["bodyId", "entryNerve", "rootSide"])
    return {int(b): (n if isinstance(n, str) else "", s if isinstance(s, str) else "")
            for b, n, s in zip(e.bodyId, e.entryNerve, e.rootSide)}


def type_nerves(t, nerve: dict[str, str]) -> str:
    """Census entry nerves of a type; a combined name ('SNpp29,SNpp63') takes all its parts."""
    if not isinstance(t, str):
        return ""
    parts = {y for p in t.split(",") for y in nerve.get(p, "").split(";") if y}
    return ";".join(sorted(parts))


def entry_nerve_per_cell(body_ids, types, mode: int) -> np.ndarray:
    """The nerve the assignment reads, per cell: option 1 the type's census nerve (unsplit
    name); option 2 the cell's own nerve when recorded, otherwise the split type's."""
    nerve = entry_nerves()
    if mode < 2:
        return np.array([nerve.get(t, "") if isinstance(t, str) else "" for t in types], dtype=object)
    own = cell_nerves()
    return np.array([own.get(int(b), ("", ""))[0] or type_nerves(t, nerve)
                     for b, t in zip(body_ids, types)], dtype=object)


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
    # measured-form proprioception (session 6); None = session-5 tanh placeholders
    subtype: np.ndarray | None = None     # per afferent: claw|hook_flex|hook_ext|club|hairplate_*|''
    theta50: np.ndarray | None = None     # claw half-activation angle, deg
    fti_bodies: dict | None = None        # leg -> (femur, tibia, tarsus1) body ids
    hp_joint: dict | None = None          # (leg, subtype) -> (dof index, lo, hi, sign toward limit)
    dt_ms: float = 0.1
    claw_width_deg: float = 10.0
    hook_w0_dps: float = 200.0
    rate_max_hz: float = 0.0              # >0: proprioceptors are Poisson rate generators
    pulse_mv: np.ndarray | None = None    # per afferent: one-step suprathreshold drive
    t_ref_ms: np.ndarray | None = None
    rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(3))
    _prev: dict = field(default_factory=dict)
    _omega: dict = field(default_factory=dict)

    def fti_angle_deg(self, xpos: np.ndarray, leg: str) -> float:
        """Anatomical femur-tibia angle: 180 deg = straight, small = flexed."""
        f, t, ta = self.fti_bodies[leg]
        u, v = xpos[t] - xpos[f], xpos[ta] - xpos[t]
        c = np.dot(-u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12)
        return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))

    def _proprio(self, obs, leg, sel) -> np.ndarray:
        st = self.subtype[sel]
        out = np.zeros(int(sel.sum()), dtype=np.float32)
        th = self.fti_angle_deg(obs["xpos"], leg)
        prev = self._prev.get(leg, th)
        w_raw = (th - prev) / (self.dt_ms / 1000.0)
        a = self.dt_ms / 2.0                      # 2 ms low-pass on angular velocity
        w = self._omega.get(leg, 0.0) + (w_raw - self._omega.get(leg, 0.0)) * min(a, 1.0)
        self._prev[leg], self._omega[leg] = th, w
        t50 = self.theta50[sel]
        cw = self.claw_width_deg
        flex = (st == "claw") & (t50 < 85.0)
        ext = (st == "claw") & (t50 >= 85.0)
        out[flex] = 1.0 / (1.0 + np.exp((th - t50[flex]) / cw))
        out[ext] = 1.0 / (1.0 + np.exp((t50[ext] - th) / cw))
        out[st == "hook_flex"] = np.clip(-w / self.hook_w0_dps, 0.0, 1.0)
        out[st == "hook_ext"] = np.clip(w / self.hook_w0_dps, 0.0, 1.0)
        out[st == "club"] = np.tanh(abs(w) / (2 * self.hook_w0_dps))
        for key in ("hairplate_ThC_protraction", "hairplate_ThC_retraction",
                    "hairplate_CTr_levation", "hairplate_CTr_depression"):
            m = st == key
            if m.any() and (leg, key) in self.hp_joint:
                j, lo, hi, sgn = self.hp_joint[(leg, key)]
                q = float(obs["joint_angles"][j])
                p = (q - lo) / (hi - lo) if hi > lo else 0.5
                p = p if sgn > 0 else 1.0 - p            # 1 = at the limit this plate reads
                out[m] = 1.0 / (1.0 + np.exp(-(p - 0.85) / 0.05))
        return out

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
            if self.subtype is None:
                signal[ch == "joint_angle"] = np.tanh(a)
                signal[ch == "joint_angle_velocity"] = np.tanh(a) + 0.1 * np.tanh(v)
            else:
                pr = np.isin(ch, ["joint_angle", "joint_angle_velocity"])
                signal[pr] = self._proprio(obs, leg, sel)[pr]
            lb = self.load_bodies.get(leg)
            strain = float(seg_load[lb].sum()) if lb is not None else 0.0
            signal[ch == "load"] = np.tanh(strain)
            signal[ch == "contact"] = np.tanh(load)
            val = self.baseline_mv[sel] + self.gain_mv[sel] * signal
            if self.rate_max_hz > 0 and self.subtype is not None:
                # rate-coded proprioceptors: Poisson with dead time at r_max * signal
                pr = self.subtype[sel] != ""
                hz = self.rate_max_hz * signal[pr]
                tr = self.t_ref_ms[sel][pr] / 1000.0
                lam = hz / np.maximum(1.0 - hz * tr, 0.05)
                fire = self.rng.random(hz.shape) < lam * self.dt_ms / 1000.0
                val[pr] = np.where(fire, self.pulse_mv[sel][pr], 0.0)
            out[self.rows[sel]] = val
        return out


def build(reg: Registry, conn, body, params=None) -> Afferents:
    n = conn.neurons
    roi = pd.read_parquet(CACHE / "male_cns_sensorimotor_roiinfo.parquet")
    roi_lut = dict(zip(roi.bodyId, roi.roiInfo))

    sens = n[n.subclass.isin(ENCODES)].copy()
    sens["leg"] = [leg_from_roiinfo(roi_lut.get(b)) for b in sens.bodyId]
    mode = assign_by_nerve(reg)
    if mode >= 2:
        # a cell that enters by a leg nerve belongs to that nerve's leg on its root side (measured);
        # the dominant leg neuropil misplaces intersegmental projections (F-SENSE-NERVE-2)
        own = cell_nerves()
        by_nerve = []
        for b in sens.bodyId:
            nv, sd = own.get(int(b), ("", ""))
            by_nerve.append(f"{SIDE[sd]}{SEGMENT_OF_NERVE[nv]}" if nv in SEGMENT_OF_NERVE and sd in SIDE else None)
        moved = int(sum(a is not None and a != b for a, b in zip(by_nerve, sens.leg)))
        sens["leg"] = [a if a is not None else b for a, b in zip(by_nerve, sens.leg)]
        reg.provide(
            "afferent:leg_mechano", "leg_from_own_nerve_moved", moved, units="neurons",
            model_use="leg afferents whose own leg nerve and root side name a different leg than "
                      "their dominant leg neuropil; the nerve is used",
            status=Status.DERIVED, method="male-cns entryNerve/rootSide per cell (measured)",
            subsystem="sensory_transduction", instances=moved)
    sens = sens[sens.leg.notna()]
    if mode:
        nv = entry_nerve_per_cell(sens.bodyId, sens.type, mode)
        if mode >= 2:
            nerve = entry_nerves()
            nv = np.array([type_nerves(t, nerve) if x in PROTHORACIC_OTHER else x
                           for x, t in zip(nv, sens.type)], dtype=object)
        legn = pd.Series([enters_by_leg_nerve(x) for x in nv], index=sens.index)
        dropped = sens[legn.eq(False).to_numpy()]
        reg.provide(
            "afferent:non_leg_nerve", "excluded_from_leg_drive", int(len(dropped)), units="neurons",
            model_use="mechanosensory afferents with leg-neuropil synapses whose type enters by a "
                      "non-leg nerve: no longer driven by leg signals",
            status=Status.DERIVED, method="male-cns entry nerve per type (sensory census, measured) under the leg-nerve rule",
            evidence="; ".join(f"{k}: {v}" for k, v in dropped.groupby("subclass").size().items()),
            subsystem="sensory_transduction", instances=int(len(dropped)),
            uncertainty="cells whose type has no census entry nerve keep the legacy rule")
        sens = sens[~legn.eq(False).to_numpy()]

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
            status=Status.INFERRED, method="literature, organ class",
            evidence="published response selectivity for this organ class "
                     "(docs/SENSORS_MECHANO.md: Mamiya 2018/2023, Dinges 2020, "
                     "Pratt 2026, Walker 2000)",
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
            uncertainty="count of reconstructed axons under the Traced-or-typed "
                        "policy; incomplete for front-leg FeCO (SENSORS_MECHANO)",
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
    # joint_angles are ordered by the fly's jointdofs, NOT by actuator: there
    # are 102 dofs and 98 actuators. Until session 6 this looked the FTi joint
    # up by actuator index and so read thorax-coxa roll (4 dofs earlier).
    dof = [f"{d.parent.name}-{d.child.name}-{d.axis.value}"
           for d in body.fly.get_jointdofs_order()]
    joint_cols: dict[str, int] = {}
    for leg in ["lf", "lm", "lh", "rf", "rm", "rh"]:
        want = f"{leg}_trochanterfemur-{leg}_tibia-pitch"
        if want in dof:
            joint_cols[leg] = dof.index(want)
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

    prop = _measured_form(reg, body, sens, dof, joint_cols)
    if prop and params is not None:
        rmax = reg.require(
            "afferent:leg_proprioceptors", "rate_mode_max_hz", units="Hz",
            model_use="Poisson rate at full signal for FeCO and hair-plate afferents; 0 = mV mode",
            subsystem="sensory_transduction", instances=int((prop["subtype"] != "").sum()),
            minimal=0.0, minimal_note="0: session-6 mV transduction (2 mV + 8 mV x signal)")
        if rmax > 0:
            rws = conn.index_of(sens.bodyId.to_numpy())
            pick = lambda a: np.broadcast_to(np.asarray(a, dtype=float), (conn.n,))[rws]  # noqa: E731
            v_th, v_rest, tau, t_ref = (pick(getattr(params, k)) for k in ("v_th", "v_rest", "tau_m", "t_ref"))
            dt = float(body.timestep * 1000.0)
            prop.update(rate_max_hz=float(rmax), t_ref_ms=t_ref,
                        pulse_mv=1.5 * (v_th - v_rest) / (1.0 - np.exp(-dt / tau)))
    return Afferents(
        **prop,
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


PROPRIO_TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "proprio_assignment.csv"


def _measured_form(reg: Registry, body, sens: pd.DataFrame, dof: list[str],
                   joint_cols: dict) -> dict:
    """Measured-form leg proprioception (session 6), per docs/SENSORS_MECHANO.md.

    claw: tonic sigmoid of the anatomical femur-tibia angle. Flexion-tuned cells
      have half-activation angles spread evenly over 20-80 deg, extension-tuned
      over 90-170 deg (Mamiya et al. 2018, 2023; measured ranges, calcium).
      Width 10 deg, guessed. Hysteresis omitted.
    hook: rectified angular velocity of the preferred direction, saturating at
      200 deg/s (guessed; direction selectivity measured, DSI 0.81).
    club: |angular velocity| (movement, bidirectional; vibration not simulated).
    hair plates: tonic sigmoid near the ThC or CTr joint limit (Pratt et al. 2026),
      half-activation at 85% of the range toward that limit (guessed).
    Subtype per cell type: data/params/proprio_assignment.csv, all guessed.
    """
    import mujoco as mj
    on = reg.require(
        "afferent:leg_proprioceptors", "measured_form", units="boolean",
        model_use="claw/hook/club/hair-plate transduction instead of tanh(angle)",
        subsystem="sensory_transduction", instances=int(len(sens)), minimal=1.0,
        minimal_note="modelling choice (session 6); 0 restores the session-5 tanh placeholders")
    table = Path(os.environ.get("FLYEMU_PROPRIO_ASSIGNMENT", PROPRIO_TABLE))  # candidate table (session 7)
    if not on or not table.exists():
        return {}
    tab = pd.read_csv(table, comment="#").set_index("type")
    st = sens.type.fillna("").map(tab.subtype).fillna("").to_numpy(dtype=object)
    st[~sens.subclass.isin(["chordotonal organ", "hair plate"]).to_numpy()] = ""
    direction = sens.type.fillna("").map(tab.direction).fillna("").to_numpy(dtype=object)
    theta = np.full(len(sens), np.nan)
    legs = sens.leg.to_numpy()
    for leg in np.unique(legs):
        # flexion-tuned claw cells: theta50 spread over 20-80 deg; extension-tuned 90-170
        for d, lo, hi in (("flexion", 20, 80), ("extension", 90, 170)):
            c = np.flatnonzero((legs == leg) & (st == "claw") & (direction == d))
            theta[c] = np.linspace(lo, hi, len(c)) if len(c) > 1 else (lo + hi) / 2
    m = body.sim.mj_model
    pre = f"{body.fly.name}/"
    bid = lambda nm: mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, pre + nm)  # noqa: E731
    fti = {leg: (bid(f"{leg}_trochanterfemur"), bid(f"{leg}_tibia"), bid(f"{leg}_tarsus1"))
           for leg in joint_cols}
    from .neuromuscular import load_calibration
    cal = load_calibration("flybody")
    hp = {}
    for leg in joint_cols:
        for key, frag, col, want in (
                ("hairplate_ThC_protraction", f"c_thorax-{leg}_coxa-", "foot_fore_mm", +1),
                ("hairplate_ThC_retraction", f"c_thorax-{leg}_coxa-", "foot_fore_mm", -1),
                ("hairplate_CTr_levation", f"{leg}_coxa-{leg}_trochanterfemur-", "foot_up_mm", +1),
                ("hairplate_CTr_depression", f"{leg}_coxa-{leg}_trochanterfemur-", "foot_up_mm", -1)):
            rows = cal[cal.actuator.str.startswith(frag)] if cal is not None else None
            if rows is None or rows.empty:
                continue
            pick = rows.loc[rows[col].abs().idxmax()]
            name = pick.actuator
            if name not in dof:
                continue
            j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, pre + name)
            lo, hi = (float(x) for x in m.jnt_range[j]) if j >= 0 else (-1.0, 1.0)
            hp[(leg, key)] = (dof.index(name), lo, hi, want * np.sign(pick[col]))
    n_claw = int((st == "claw").sum())
    reg.provide("afferent:FeCO claw", "angle_tuning", "sigmoid, theta50 spread 20-80 / 90-170 deg",
                units="deg", model_use="tonic position encoding", status=Status.INFERRED,
                subsystem="sensory_transduction", instances=n_claw,
                evidence="Mamiya et al. 2018 Neuron; 2023 Neuron (goniotopic map, calcium)",
                uncertainty="ranges measured by calcium imaging; per-cell theta50 placement, "
                            "width 10 deg and absence of hysteresis are guesses")
    reg.provide("afferent:leg_proprioceptors", "subtype_assignment",
                "data/params/proprio_assignment.csv", units="category",
                model_use="claw/hook/club/hair-plate identity per type", status=Status.GUESSED,
                subsystem="sensory_transduction", instances=int((st != "").sum()),
                evidence="no SNpp-to-claw/hook/club crosswalk exists; types assigned to match "
                         "measured FeCO proportions (Mamiya 2023)")
    reg.provide("afferent:claw_hook_hairplate", "preferred_direction",
                "data/params/proprio_assignment.csv (direction)", units="category",
                model_use="flexion/extension tuning and which joint limit",
                status=Status.INFERRED, subsystem="sensory_transduction",
                instances=int(np.isin(st, ["claw", "hook_flex", "hook_ext"]).sum()
                              + np.char.startswith(st.astype(str), "hairplate").sum()),
                evidence="net signed drive onto antagonist MN pools (connectome) under a "
                         "resistance-reflex prior (scripts/proprio_direction.py)",
                uncertainty="post-hoc (after a failed standing run); types with near-zero net "
                            "drive are unconstrained by this rule")
    reg.provide("afferent:hook_club_hairplate", "gains_and_widths",
                "hook/club 200 deg/s; hair plate 85% +/- 5% of range", units="various",
                model_use="velocity and limit transduction", status=Status.GUESSED,
                subsystem="sensory_transduction",
                instances=int(((st != "") & (st != "claw")).sum()),
                evidence="guessed: direction selectivity and limit tuning are measured in form "
                         "only (calcium imaging; Pratt 2026)")
    return dict(subtype=st, theta50=theta, fti_bodies=fti, hp_joint=hp,
                dt_ms=float(body.timestep * 1000.0))
