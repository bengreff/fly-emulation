"""Motor output: motor-neuron spikes to joint torque.

The connectome names each leg motor neuron's target muscle in its `type` field
("Ti flexor MN", "Fe reductor MN"). What the connectome does not say is which
joint that muscle moves in the body model, in which direction, or with how much
force. So this module holds three separate kinds of claim, kept apart:

  measured   which motor neurons target which muscle, and pool sizes
  assumed    which joint degree of freedom each muscle drives, and its sign
  unresolved force per motor unit, and muscle activation kinetics

Model units, measured from the compiled body: length mm, time s, mass g, so
force is uN and joint torque is uN*mm. The fly weighs 1.02 mg, i.e. about
10 uN. Moving a leg joint against its passive stiffness takes torques of order
1 uN*mm, and below about 0.1 uN*mm the joint's own spring dominates entirely -
so the passive stiffness, a body-model default rather than a measurement, sets
the scale of what counts as a motor command at all.

The muscle-to-joint map below is anatomically motivated but it is a guess about
this body model's coordinate conventions. Joint axis signs in particular are not
known to match flexion/extension; that is registered, not hidden.

Motor units are not resolved: NeuroMechFly has one torque actuator per joint
degree of freedom, so a pool of 47 accessory tibia flexor motor neurons drives
one number. The size principle cannot be expressed. This is F-BODY-1 at whole
body scale.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .registry import Registry, Status

# Leg neuromere to body-model leg position.
NEUROMERE_TO_LEG = {"T1": "f", "T2": "m", "T3": "h"}
SIDE = {"L": "l", "R": "r"}

# Muscle -> (joint group, anatomical ACTION). Not a sign.
#
# Anatomy says what a muscle does; it cannot say which sign does that in a
# given body model's coordinate frame, and the frame differs BETWEEN models:
# positive femur-tibia drive flexes the leg in NeuroMechFly and extends it in
# flybody. So the sign is resolved at build time from the measured calibration
# in data/derived/joint_signs_<model>.csv, produced by
# scripts/calibrate_joint_signs.py. Hard-coding signs silently inverts half the
# muscles the moment the body changes.
#
# Actions from Azevedo et al. 2024 (Nature 631:360-368) Supplementary Table A1,
# which is the provenance of these connectome labels. Note the trap recorded in
# F-SIGN-5: levator/depressor does NOT map onto flexor/extensor - the trochanter
# levator flexes its joint while the tibia levator extends its joint.
MUSCLE_TO_ACTION: dict[str, tuple[str, str]] = {
    # femur-tibia
    "Ti flexor":                     ("FTi", "flexion"),
    "Acc. ti flexor":                ("FTi", "flexion"),
    "Ti extensor":                   ("FTi", "extension"),
    # coxa-trochanter. This joint is a levator/depressor, not a flexor pair:
    # the trochanter "flexor" is Soler's trochanter LEVATOR and raises the femur.
    "Tr flexor":                     ("CTr", "levation"),
    "Acc. tr flexor":                ("CTr", "levation"),
    "Tr extensor":                   ("CTr", "depression"),
    # All three of these insert on the SAME trochanter extensor tendon.
    "Sternotrochanter":              ("CTr", "depression"),
    # The giant-fibre escape JUMP muscle, and biarticular: it crosses the
    # thorax-coxa joint before extending the trochanter, so a single-joint
    # assignment is an approximation.
    "Tergotr.":                      ("CTr", "depression"),
    # tibia-tarsus: the depressor EXTENDS this joint and the levator FLEXES it.
    "Ta levator":                    ("TiTa", "flexion"),
    "Ta depressor":                  ("TiTa", "extension"),
    # thorax-coxa
    "Tergopleural/Pleural promotor": ("ThC", "protraction"),
    "Pleural remotor/abductor":      ("ThC", "retraction"),
    "Sternal adductor":              ("ThC", "adduction"),
    # Named for rotation about the coxa's long axis. Which rotator takes which
    # direction is not established, so these carry an assumed sign.
    "Sternal anterior rotator":      ("ThC", "rotation_a"),
    "Sternal posterior rotator":     ("ThC", "rotation_b"),
}

# Joint group -> the actuator-name fragment identifying it, {leg} per leg.
JOINT_GROUPS: dict[str, str] = {
    "ThC": "c_thorax-{leg}_coxa-",
    "CTr": "{leg}_coxa-{leg}_trochanterfemur-",
    "FTi": "{leg}_trochanterfemur-{leg}_tibia-",
    "TiTa": "{leg}_tibia-{leg}_tarsus1-",
}

# Action -> (calibration column, the sign of that column which realises it).
ACTION_COLUMN: dict[str, tuple[str, float]] = {
    "protraction": ("foot_fore_mm", +1.0),
    "retraction":  ("foot_fore_mm", -1.0),
    "abduction":   ("foot_lateral_mm", +1.0),
    "adduction":   ("foot_lateral_mm", -1.0),
    "levation":    ("foot_up_mm", +1.0),
    "depression":  ("foot_up_mm", -1.0),
    "extension":   ("leg_len_change_mm", +1.0),
    "flexion":     ("leg_len_change_mm", -1.0),
}

# Rotation about the coxa's long axis moves the foot least, so it is found as
# the thorax-coxa actuator with the smallest tip displacement rather than by a
# direction. The two rotators are then assigned opposite signs, which is an
# assumption: the sources name them for rotation without settling which way.
ROTATION_ACTIONS = {"rotation_a": -1.0, "rotation_b": +1.0}

# The long tendon muscle. Its fibres sit in the femur (ltm2) and the tibia
# (ltm1) and pull ONE tendon, the retractor unguis, which runs to the pretarsal
# claw. There are no muscles inside the tarsal segments at all (Soler et al.
# 2004), and the tarsus is "moved together by muscle tension on the long
# tendon" (Haustein et al. 2024). So these three labels are one muscle driving
# one tendon-coupled group of four joints per leg, not three muscles on three
# different joints. Splitting them, as the first map did, made them
# antagonists of themselves.
COUPLED_TO_JOINTS: dict[str, tuple[tuple[str, ...], float]] = {
    name: ((
        "{leg}_tarsus1-{leg}_tarsus2-pitch",
        "{leg}_tarsus2-{leg}_tarsus3-pitch",
        "{leg}_tarsus3-{leg}_tarsus4-pitch",
        "{leg}_tarsus4-{leg}_tarsus5-pitch",
    ), +1.0)
    for name in ("ltm", "ltm1-tibia", "ltm2-femur")
}

# What the body model still cannot receive. The claw itself is the gap: the
# long tendon's actual target is the pretarsal claw, and there is no claw or
# grip degree of freedom, so tarsal flexion is a partial stand-in for it.
UNMAPPABLE: dict[str, str] = {
    "Fe reductor":
        "function unknown. Azevedo et al. 2024 Table A1 gives its Action as "
        "'Unknown' and states 'The function of the femur reductor muscle is "
        "unknown'; the trochanter-femur joint it would serve is thought to be "
        "FUSED in the adult, and the body model has no such joint. The only "
        "supporting idea is cross-species and a hypothesis: Frantsevich & Wang "
        "2009 propose the reductor acts as a spring. Ozdil et al. 2025 omitted "
        "these muscles for the same reason. 20 motor neurons with no "
        "defensible sign.",
}

# Signs that anatomy names but does not settle.
UNRESOLVED_SIGN = {
    "Sternal anterior rotator": "rotation direction about the coxa's long axis "
                                "not established; it also adducts",
    "Sternal posterior rotator": "rotation direction not established; it is "
                                 "also described as a remotor",
}

@dataclass
class Neuromuscular:
    """Maps motor-neuron rows onto body actuators and integrates activation."""

    adhesion_index: np.ndarray      # adhesion actuator per grip motor neuron
    adhesion_rows: np.ndarray       # network row index per grip motor neuron
    n_adhesion: int
    mn_index: np.ndarray            # network row index per mapped motor neuron
    actuator_index: np.ndarray      # body actuator index per mapped motor neuron
    drive_sign: np.ndarray          # +1/-1 per mapped motor neuron
    force_per_spike: np.ndarray     # mN*mm of torque impulse per spike
    n_actuators: int
    tau_act_ms: float
    unmapped: pd.DataFrame          # motor neurons with no actuator
    tau_mn: np.ndarray | None = None  # per mapped motor neuron twitch decay, ms
    activation: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.activation = np.zeros(self.n_actuators, dtype=np.float32)
        self.grip = np.zeros(max(self.n_adhesion, 1), dtype=np.float32)
        self._decay: float | None = None

    def step(self, spiked: np.ndarray, timestep_ms: float) -> np.ndarray:
        """Advance muscle activation and return torque per actuator.

        Each mapped motor neuron has its own motor-unit state: a spike adds its
        torque per spike, which decays with its own twitch time constant. The
        actuator's torque is the signed sum over its motor units."""
        if self._decay is None:
            self._decay = float(np.exp(-timestep_ms / self.tau_act_ms))
            tau = self.tau_mn if self.tau_mn is not None else np.full(
                len(self.mn_index), self.tau_act_ms)
            self._decay_mn = np.exp(-timestep_ms / tau).astype(np.float32)
            self.unit = np.zeros(len(self.mn_index), dtype=np.float32)
            self._w = (self.drive_sign * self.force_per_spike).astype(np.float32)
        self.unit *= self._decay_mn
        if spiked.size:
            hits = np.isin(self.mn_index, spiked, assume_unique=False)
            if hits.any():
                self.unit[hits] += self._w[hits]
        self.activation = np.bincount(self.actuator_index, weights=self.unit,
                                      minlength=self.n_actuators).astype(np.float32)
        # Grip decays on the same muscle time constant and saturates at 1.
        self.grip *= self._decay
        if spiked.size and self.adhesion_rows.size:
            hits = np.isin(self.adhesion_rows, spiked)
            if hits.any():
                np.add.at(self.grip, self.adhesion_index[hits], 0.05)
        np.clip(self.grip, 0.0, 1.0, out=self.grip)
        return self.activation


def load_calibration(model: str) -> pd.DataFrame | None:
    """The measured actuator-to-foot table for this body model."""
    path = (Path(__file__).resolve().parents[2] / "data" / "derived"
            / f"joint_signs_{model}.csv")
    if not path.exists():
        return None
    return pd.read_csv(path)


def resolve_sign(
    cal: pd.DataFrame, leg: str, group: str, action: str
) -> tuple[str, float] | None:
    """Which actuator, and which sign of it, performs this anatomical action.

    Returns the actuator name and the sign, or None if the calibration shows
    no actuator in that joint group producing that action.
    """
    frag = JOINT_GROUPS[group].format(leg=leg)
    rows = cal[cal.actuator.str.startswith(frag)]
    if rows.empty:
        return None

    if action in ROTATION_ACTIONS:
        # Rotation about the limb's own axis displaces the tip least.
        disp = rows[["foot_fore_mm", "foot_lateral_mm", "foot_up_mm"]].abs().sum(axis=1)
        pick = rows.loc[disp.idxmin()]
        return pick.actuator, ROTATION_ACTIONS[action]

    column, want = ACTION_COLUMN[action]
    pick = rows.loc[rows[column].abs().idxmax()]
    value = float(pick[column])
    if abs(value) < 1e-4:
        return None                     # this joint group cannot do that
    return pick.actuator, want * np.sign(value)


def build(
    reg: Registry,
    conn,
    actuator_names: list[str],
    *,
    fly_name: str = "nmf",
    adhesion_names: list[str] | None = None,
    model: str = "flybody",
) -> Neuromuscular:
    n = conn.neurons
    mn = n[n.superclass == "vnc_motor"].copy()

    act_lookup = {}
    for i, a in enumerate(actuator_names):
        short = a.removeprefix(f"{fly_name}/").removesuffix("-motor")
        act_lookup[short] = i

    # Tarsal adhesion, one actuator per leg. The long tendon muscle's real
    # target is the pretarsal claw, so its motor pool drives grip here rather
    # than only tarsal flexion. Adhesion is a SUBSTITUTE mechanism, not claw
    # and pulvillus mechanics, and is declared as a scaffold in run metadata.
    adhesion_lookup: dict[str, int] = {}
    for i, a in enumerate(adhesion_names or []):
        short = a.removeprefix(f"{fly_name}/").removesuffix("-adhesion")
        for leg in NEUROMERE_TO_LEG.values():
            for side in SIDE.values():
                if short.startswith(f"{side}{leg}_"):
                    adhesion_lookup[f"{side}{leg}"] = i

    reg.provide(
        "population:vnc_motor", "count", int(len(mn)), units="neurons",
        model_use="the set of neurons that drive muscles",
        status=Status.MEASURED,
        evidence="male-cns:v1.0 superclass = vnc_motor",
        subsystem="neuromuscular", instances=int(len(mn)),
        uncertainty="dataset annotation; excludes brain motor neurons (cb_motor, 107)",
    )

    cal = load_calibration(model)
    resolved_actions: dict[str, tuple[str, float, str]] = {}
    rows, acts, signs, muscles, legs_of_row = [], [], [], [], []
    unmapped = []
    conn_index = conn.index_of(mn.bodyId.to_numpy())

    for (row_i, rec), net_i in zip(mn.iterrows(), conn_index):
        mtype = rec.type
        leg_key = None
        if isinstance(rec.somaNeuromere, str) and isinstance(rec.somaSide, str):
            seg = NEUROMERE_TO_LEG.get(rec.somaNeuromere)
            side = SIDE.get(rec.somaSide)
            if seg and side:
                leg_key = f"{side}{seg}"

        muscle = None
        if isinstance(mtype, str) and mtype.endswith(" MN"):
            muscle = mtype[:-3]

        action = MUSCLE_TO_ACTION.get(muscle) if muscle else None
        coupled = COUPLED_TO_JOINTS.get(muscle) if muscle else None
        if coupled is not None and leg_key is not None and net_i >= 0:
            templates, sign = coupled
            hit = False
            for tmpl in templates:
                a = act_lookup.get(tmpl.format(leg=leg_key))
                if a is None:
                    continue
                rows.append(net_i)
                acts.append(a)
                signs.append(sign)
                muscles.append(muscle)
                legs_of_row.append(leg_key)
                hit = True
            if hit:
                continue

        if action is None or leg_key is None or net_i < 0 or cal is None:
            unmapped.append(
                {"bodyId": rec.bodyId, "type": mtype, "subclass": rec.subclass,
                 "neuromere": rec.somaNeuromere,
                 "reason": "no muscle action declared" if leg_key else
                           "no leg assignment"}
            )
            continue
        group, act_name = action
        resolved = resolve_sign(cal, leg_key, group, act_name)
        if resolved is None:
            unmapped.append(
                {"bodyId": rec.bodyId, "type": mtype, "subclass": rec.subclass,
                 "neuromere": rec.somaNeuromere,
                 "reason": f"no actuator performs {act_name} at {group}"}
            )
            continue
        joint, sign = resolved
        a = act_lookup.get(joint)
        if a is None:
            unmapped.append({"bodyId": rec.bodyId, "type": mtype,
                             "subclass": rec.subclass,
                             "neuromere": rec.somaNeuromere,
                             "reason": f"body has no actuator {joint}"})
            continue
        rows.append(net_i)
        acts.append(a)
        signs.append(sign)
        muscles.append(muscle)
        legs_of_row.append(leg_key)
        resolved_actions[muscle] = (joint, sign, act_name)

    mapped = pd.DataFrame({"muscle": muscles})
    for muscle, grp in mapped.groupby("muscle"):
        if muscle in COUPLED_TO_JOINTS:
            templates, sign = COUPLED_TO_JOINTS[muscle]
            reg.provide(
                f"muscle:{muscle}", "joint_and_sign",
                f"{len(templates)} tarsal joints coupled x {sign:+.0f}",
                units="dimensionless",
                model_use="tendon-coupled tarsal flexion group",
                status=Status.DERIVED,
                evidence="no muscles exist inside the tarsal segments (Soler "
                         "et al. 2004, Development 131:6041); they are moved "
                         "together by tension on the long tendon (Haustein et "
                         "al. 2024). One muscle, one tendon, four joints",
                subsystem="neuromuscular", instances=int(len(grp)),
                uncertainty="the tendon's real target is the pretarsal claw "
                            "via the retractor unguis; the body model has no "
                            "claw degree of freedom, so tarsal flexion stands "
                            "in for claw retraction",
            )
            continue
        joint, sign, act_name = resolved_actions[muscle]
        group, _ = MUSCLE_TO_ACTION[muscle]
        assumed_sign = act_name in ROTATION_ACTIONS
        reg.provide(
            f"muscle:{muscle}", "joint_and_sign", f"{joint} x {sign:+.0f}",
            units="dimensionless",
            model_use=f"{group} {act_name}",
            status=Status.ASSUMED if assumed_sign else Status.DERIVED,
            evidence=(
                f"action '{act_name}' from Azevedo et al. 2024 Table A1; the "
                f"SIGN is measured, not assumed: the calibration in "
                f"data/derived/joint_signs_{model}.csv shows this actuator "
                f"produces it at {sign:+.0f}"
                + (". The rotation direction itself is NOT established by the "
                   "sources, so this sign is an assumption" if assumed_sign
                   else "")
            ),
            subsystem="neuromuscular", instances=int(len(grp)),
            uncertainty="a wrong sign inverts this muscle's whole action",
        )

    force_per_spike = reg.require(
        "motor_unit:all", "force_per_spike", units="uN*mm",
        model_use="torque impulse delivered to a joint by one motor spike",
        subsystem="neuromuscular", instances=len(rows),
        minimal=1.0,
        minimal_note="declared default of 1 uN*mm of joint torque per motor "
                     "spike. Consistent with, but not measured from, the "
                     "measured force per spike of tibia flexor motor units "
                     "(slow <0.1 uN, intermediate ~1 uN, fast ~10 uN; "
                     "Azevedo 2020 eLife 56754) acting through an assumed "
                     "moment arm of order 0.1-1 mm",
        uncertainty="measured force per spike exists for three tibia-flexor "
                    "units in one pool, spanning two orders of magnitude, and "
                    "as force rather than joint torque; the moment arm is "
                    "assumed. One shared value here, so motor units are not "
                    "resolved and the size principle cannot be expressed",
    )
    tau_act = reg.require(
        "muscle:all", "activation_tau", units="ms",
        model_use="first-order muscle activation filter",
        subsystem="muscle_mechanics", instances=len(set(acts)),
        minimal=30.0,
        minimal_note="declared default activation time constant for every muscle",
        uncertainty="no force-length or force-velocity dependence in M v1; "
                    "activation maps straight to torque",
    )
    reg.provide(
        "muscle:all", "force_length_velocity", None, units="dimensionless",
        model_use="omitted from M v1",
        status=Status.UNRESOLVED,
        evidence="no Hill-type muscle in this interface; torque is "
                 "proportional to activation regardless of joint state",
        subsystem="muscle_mechanics", instances=len(set(acts)),
    )

    # --- non-leg motor neurons: data/params/motor_targets.csv ----------------
    extra = _map_non_leg(reg, conn, n, unmapped, act_lookup, cal)
    mapped_ids = set()
    for net_i, a, sgn, bid in extra:
        rows.append(net_i); acts.append(a); signs.append(sgn)
        muscles.append("non-leg"); legs_of_row.append(None); mapped_ids.add(bid)
    unmapped = [u for u in unmapped if u["bodyId"] not in mapped_ids]

    un = pd.DataFrame(unmapped)
    if not un.empty:
        for reason, grp in un.groupby("reason"):
            reg.provide(
                f"population:vnc_motor unmapped ({reason})", "actuator_target",
                None, units="dimensionless",
                model_use="motor output that the body model cannot receive",
                status=Status.UNRESOLVED,
                evidence=f"{len(grp)} motor neurons: {reason}",
                subsystem="neuromuscular", instances=int(len(grp)),
            )

    # Which motor neurons drive grip, and on which leg.
    adh_rows, adh_idx = [], []
    for net_i, leg, muscle in zip(rows, legs_of_row, muscles):
        if muscle in COUPLED_TO_JOINTS and leg in adhesion_lookup:
            adh_rows.append(net_i)
            adh_idx.append(adhesion_lookup[leg])
    if adh_rows:
        reg.provide(
            "muscle:long tendon", "adhesion_coupling",
            f"{len(set(adh_rows))} motor neurons drive {len(set(adh_idx))} "
            "tarsal adhesion actuators",
            units="dimensionless",
            model_use="grip: the long tendon muscle retracts the pretarsal claw",
            status=Status.ASSUMED,
            evidence="adhesion substitutes for claw and pulvillus mechanics, "
                     "which the body model does not have; the long tendon "
                     "muscle activates on mechanical vibration, possibly to "
                     "activate gripping (Wang-Chen et al. 2026)",
            subsystem="neuromuscular", instances=len(set(adh_rows)),
            uncertainty="a substitute mechanism, not the animal's own",
        )

    undriven = sorted(set(range(len(actuator_names))) - set(acts))
    if undriven:
        reg.provide(
            "actuator:undriven", "motor_neuron_source", None, units="dimensionless",
            model_use="body actuators no motor neuron reaches",
            status=Status.UNRESOLVED, subsystem="neuromuscular", instances=len(undriven),
            evidence="no identified or candidate motor neuron: " + ", ".join(
                actuator_names[i].split("/")[-1] for i in undriven),
        )

    fps, tau_mn = _per_neuron_forces(reg, conn, rows, float(force_per_spike), float(tau_act))
    return Neuromuscular(
        adhesion_index=np.asarray(adh_idx, dtype=np.int64),
        adhesion_rows=np.asarray(adh_rows, dtype=np.int64),
        n_adhesion=len(adhesion_names or []),
        mn_index=np.asarray(rows, dtype=np.int64),
        actuator_index=np.asarray(acts, dtype=np.int64),
        drive_sign=np.asarray(signs, dtype=np.float32),
        force_per_spike=fps,
        n_actuators=len(actuator_names),
        tau_act_ms=tau_act,
        unmapped=un,
        tau_mn=tau_mn,
    )


FORCE_TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "motor_forces.csv"


def _per_neuron_forces(reg, conn, rows, default_fps: float, default_tau: float):
    """Torque per spike and twitch tau per mapped motor neuron: table rows
    (data/params/motor_forces.csv) where they exist, the shared default elsewhere."""
    fps = np.full(len(rows), default_fps, dtype=np.float32)
    tau = np.full(len(rows), default_tau, dtype=np.float32)
    on = reg.require(
        "motor_unit:all", "per_neuron_forces", units="boolean",
        model_use="use per-motor-neuron torque per spike (Azevedo 2020 anchored)",
        subsystem="neuromuscular", instances=len(rows), minimal=1.0,
        minimal_note="modelling choice (session 6): table rows replace the shared "
                     "force_per_spike for leg motor neurons; 0 = shared value for all")
    if not on or not FORCE_TABLE.exists() or not len(rows):
        return fps, tau
    t = pd.read_csv(FORCE_TABLE, comment="#").set_index("bodyId")
    bids = conn.neurons.bodyId.to_numpy()[np.asarray(rows)]
    hit = pd.Series(bids).isin(t.index).to_numpy()
    fps[hit] = t.torque_uNmm.reindex(bids[hit]).to_numpy(np.float32)
    tau[hit] = t.twitch_tau_ms.reindex(bids[hit]).to_numpy(np.float32)
    sel = t.reindex(bids[hit])
    flex = int((sel.unit_class.fillna("") != "").sum())
    reg.provide("motor_unit:tibia_flexor", "torque_per_spike", "data/params/motor_forces.csv",
                units="uN*mm", model_use="joint torque added by one motor spike",
                status=Status.DERIVED, subsystem="neuromuscular", instances=flex,
                method="measured class force (fast 10, intermediate 1, slow 0.05 uN) x tibia "
                       "length from the body model; class by EM-volume rank (inferred)",
                evidence="Azevedo et al. 2020 eLife 9:e56754 Fig 4",
                uncertainty="class matching by size rank; force measured at the tibia, lever "
                            "taken as full tibia length; slow value is '<0.1 uN'")
    reg.provide("motor_unit:other_leg", "torque_per_spike", "data/params/motor_forces.csv",
                units="uN*mm", model_use="joint torque added by one motor spike",
                status=Status.INFERRED, subsystem="neuromuscular", instances=int(hit.sum()) - flex,
                evidence="power law in EM volume fitted to the three flexor classes; lever = "
                         "moved segment length (derived from body)",
                uncertainty="steep fitted exponent (~5); different muscles, fibre types and "
                            "moment arms are not modelled; clipped 0.05-10 uN")
    reg.provide("motor_unit:leg", "twitch_tau", "data/params/motor_forces.csv",
                units="ms", model_use="per-unit activation decay", status=Status.GUESSED,
                subsystem="muscle_mechanics", instances=int(hit.sum()),
                evidence="guessed: 30 ms fast/intermediate (rise ~8.5 ms measured, decay "
                         "not reported), 100 ms slow (slow units summate over >500 ms)")
    return fps, tau


MOTOR_TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "motor_targets.csv"


def _abdomen_joint(neuromere: str) -> str:
    """Abdominal joint for a segmental MN: A1 at thorax-A1, Ak at A(k-1)-Ak."""
    if not isinstance(neuromere, str) or not neuromere.startswith("A"):
        return "c_thorax-c_abdomen1-pitch"
    k = min(int(neuromere[1:]), 7)
    return "c_thorax-c_abdomen1-pitch" if k <= 1 else f"c_abdomen{k - 1}-c_abdomen{k}-pitch"


def _map_non_leg(reg, conn, n, unmapped, act_lookup, cal):
    """Map motor neurons the leg pass could not, from the labelled table."""
    if not MOTOR_TABLE.exists():
        return []
    table = pd.read_csv(MOTOR_TABLE, comment="#")
    unmapped_ids = {u["bodyId"] for u in unmapped}
    cand = n[(n.superclass == "cb_motor") | n.bodyId.isin(unmapped_ids)].copy()
    cand["side"] = cand.instance.fillna("").str.extract(r"_([LR])$")[0].map({"L": "l", "R": "r"})
    idx = conn.index_of(cand.bodyId.to_numpy())
    out = []
    for row in table.itertuples(index=False):
        sel = cand.type.fillna("").str.contains(row.type_regex, regex=True).to_numpy() & (idx >= 0)
        if not sel.any():
            continue
        hit = cand[sel]; hit_idx = idx[sel]
        if str(row.target).startswith("NONE:"):
            for bid in hit.bodyId:
                for u in unmapped:
                    if u["bodyId"] == bid:
                        u["reason"] = str(row.target)[5:]
            if cal is not None:
                missing = set(hit.bodyId) - unmapped_ids
                unmapped.extend({"bodyId": b, "type": t, "subclass": sc, "neuromere": nm,
                                 "reason": str(row.target)[5:]}
                                for b, t, sc, nm in hit[hit.bodyId.isin(missing)][
                                    ["bodyId", "type", "subclass", "somaNeuromere"]].itertuples(index=False))
            continue
        types_sorted = sorted(hit.type.dropna().unique())
        n_ok = 0
        for (bid, t, side, nm), net_i in zip(hit[["bodyId", "type", "side", "somaNeuromere"]].itertuples(index=False), hit_idx):
            tgt, sgn = str(row.target), float(row.sign)
            if tgt.startswith("LEG:"):
                if cal is None or not isinstance(side, str):
                    continue
                _, leg, group, action = tgt.split(":")
                res = resolve_sign(cal, f"{side}{leg}", group, action)
                if res is None:
                    continue
                tgt, sgn = res
            elif tgt == "ABDOMEN":
                tgt = _abdomen_joint(nm)
                # alternate types between pitch and yaw (guessed); yaw pulls
                # toward the neuron's own side
                if t in types_sorted and types_sorted.index(t) % 2 == 1:
                    tgt = tgt.replace("-pitch", "-yaw")
                    sgn = sgn * (1.0 if side == "l" else -1.0)
            elif tgt.startswith("LEGCYCLE:"):
                seg = NEUROMERE_TO_LEG.get(nm) if isinstance(nm, str) else None
                if seg is None or not isinstance(side, str):
                    continue
                opts = tgt[9:].split("|")
                tgt = opts[types_sorted.index(t) % len(opts)].replace("{leg}", f"{side}{seg}")
            elif tgt.startswith("CYCLE:"):
                opts = tgt[6:].split("|")
                tgt = opts[types_sorted.index(t) % len(opts)] if t in types_sorted else opts[0]
            if "{s}" in tgt:
                if not isinstance(side, str):
                    continue
                tgt = tgt.replace("{s}", side)
            a = act_lookup.get(tgt)
            if a is None:
                continue
            out.append((int(net_i), a, sgn, bid)); n_ok += 1
        if n_ok:
            status = Status(row.target_basis)
            reg.provide(
                f"motor_map:{row.type_regex}", "actuator_and_sign", f"{row.target} x {row.sign}",
                units="dimensionless", model_use="non-leg motor neuron to body actuator",
                status=status, subsystem="neuromuscular", instances=n_ok,
                evidence=f"{row.source}: {row.justification}",
                uncertainty=f"target {row.target_basis}; sign {row.sign_basis}",
                method="data/params/motor_targets.csv",
            )
    return out
