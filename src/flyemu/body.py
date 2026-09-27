"""The body: a whole fly in MuJoCo, with the physics the interface needs.

Two body models are supported and the default is **flybody**, chosen on
evidence rather than preference (docs/DECISIONS.md):

  - its per-segment masses come from 52 flies weighed part by part, against
    NeuroMechFly's fractions-from-another-lab times an assumed 1 mg total;
  - it carries 102 joint ranges fitted to real annotated poses, against
    NeuroMechFly's none at all;
  - it differentiates passive joint parameters into 8 groups, against one
    global stiffness and damping for every joint;
  - it has no `boundmass` floor, so none of its mass is a solver artefact;
  - it ships aerodynamics and adhesion, both of which the interface needs;
  - and its rigging already omits the non-joints the audit in joints.py
    identified independently: no eye degrees of freedom, no arista degrees of
    freedom, one haltere axis. Two different methods reaching the same answer.

Leg joint names are identical between the two models, so the muscle map and the
measured sign calibration carry across unchanged.

Physics implemented here:

  self-collision    every fly geom collides with every other, as the convex
                    hull of its real mesh. MuJoCo excludes same-body and
                    parent-child pairs itself, so adjacent segments do not
                    fight their own joint.
  aerodynamics      MuJoCo's quasi-steady fluid model in air, with ellipsoid
                    fluid interaction on the wings and halteres.
  adhesion          tarsal adhesion actuators, driven by the long tendon
                    motor pool, standing in for claw and pulvillus mechanics.
  tendons           real MuJoCo tendons for the tarsal chain, which has no
                    muscles of its own.
  joint limits      from joints.py, which separates the four measured
                    anatomical limits from assumed envelopes.

Model units, verified by test rather than assumed: length mm, time s, mass g,
so force is uN and joint torque uN*mm. A fly weighs about 10 uN.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import mujoco as mj
import numpy as np

from flygym.anatomy import (
    LEGS,
    ActuatedDOFPreset,
    ContactBodiesPreset,
    JointPreset,
    Skeleton,
)
from flygym.compose import (
    ActuatorType,
    FlatGroundWorld,
    FlyBody,
    KinematicPosePreset,
    NeuroMechFly,
)
from flygym.flybody import (
    FlyBodyContactBodiesPreset,
    FlyBodyJointPreset,
    FlyBodySkeleton,
)
from flygym.simulation import Simulation
from flygym.utils.math import Rotation3D

from . import joints

# NeuroMechFly's global joint defaults. Not measured fly mechanics: they appear
# in no paper, only in code, and moved by up to 200-fold between releases.
NMF_STIFFNESS = 10.0
NMF_DAMPING = 0.5
NMF_ARMATURE = 1e-6
NMF_FORCERANGE = (-30.0, 30.0)   # uN*mm

# Air at 20 C, in model units (mm, s, g): 1.204 kg/m^3 and 1.825e-5 Pa*s.
AIR_DENSITY = 1.204e-6           # g/mm^3
AIR_VISCOSITY = 1.825e-5         # g/(mm*s)

# MuJoCo's ellipsoid fluid coefficients: blunt drag, slender drag, angular
# drag, Kutta lift, Magnus lift. These are MuJoCo's own defaults for
# fluidshape="ellipsoid"; they are not fitted to fly wings.
ELLIPSOID_FLUID = (0.5, 0.25, 1.5, 1.0, 1.0)

# Anatomical regions for self-collision. Segments within a region nest at
# their joints and must not collide; different regions must.
REGIONS: tuple[tuple[str, ...], ...] = (
    ("lf_",), ("lm_",), ("lh_",), ("rf_",), ("rm_",), ("rh_",),   # six legs
    ("c_head", "c_rostrum", "c_haustellum", "_labrum", "_antenna",
     "_eye", "_pedicel", "_funiculus", "_arista"),                # head complex
    ("c_thorax",),
    ("c_abdomen",),
    ("_wing",),
    ("_haltere",),
)
_ALL_REGION_BITS = (1 << len(REGIONS)) - 1


def _region_index(geom_name: str) -> int:
    for i, keys in enumerate(REGIONS):
        if any(k in geom_name for k in keys):
            return i
    return len(REGIONS) - 1      # anything unrecognised joins the last region


# Geom name suffixes that carry a body's physical shape WHERE A BODY HAS ONE.
# Not every body does: the wings are `_membrane` and `_brown`, and the distal
# tarsus - the foot, carrying the claw - is `_brown` alone. Treating these
# suffixes as the whole rule silently removed the feet and the wings from
# collision, which are the surfaces that matter most.
PHYSICAL_GEOM_SUFFIXES = ("_body", "_lower")

LOCK_EPSILON_RAD = 1e-4
LOCK_STIFFNESS = 1e4


@dataclass
class Body:
    """A compiled whole-fly MuJoCo simulation with torque-controlled joints."""

    model: str = "flybody"               # or "neuromechfly"
    timestep: float = 1e-4
    spawn_height: float = 2.0            # mm above the ground plane
    with_camera: bool = False
    self_collision: bool = True
    aerodynamics: bool = True
    adhesion: bool = True
    tendons: bool = True
    max_hull_vertices: int = 32
    vision: bool = True
    forcerange: tuple[float, float] = NMF_FORCERANGE

    sim: Simulation = field(init=False)
    actuator_names: list[str] = field(init=False)

    def __post_init__(self) -> None:
        if self.model == "flybody":
            fly = FlyBody()
            # flybody ships only the yaw_roll_pitch Euler decomposition, so
            # the sign calibration has to be re-measured against it rather than
            # inherited from NeuroMechFly.
            skeleton = FlyBodySkeleton(
                axis_order=fly.AXIS_ORDER_CLASS.YAW_ROLL_PITCH,
                joint_preset=FlyBodyJointPreset.ALL_BIOLOGICAL,
            )
            neutral = KinematicPosePreset.FLYBODY_NEUTRAL
            joint_kwargs: dict[str, Any] = {}     # flybody carries its own
        elif self.model == "neuromechfly":
            fly = NeuroMechFly()
            skeleton = Skeleton(
                axis_order=fly.AXIS_ORDER_CLASS.PITCH_ROLL_YAW,
                joint_preset=JointPreset.ALL_BIOLOGICAL,
            )
            neutral = KinematicPosePreset.NEUTRAL
            joint_kwargs = dict(stiffness=NMF_STIFFNESS, damping=NMF_DAMPING,
                                armature=NMF_ARMATURE)
        else:
            raise ValueError(f"unknown body model {self.model!r}")

        fly.add_joints(skeleton, neutral_pose=neutral, **joint_kwargs)

        # Actuate only real articulations with muscles. The audit distinguishes
        # powered, passive and locked; see src/flyemu/joints.py.
        all_dofs = list(skeleton.iter_jointdofs())
        self.dof_mode: dict[str, joints.Mode] = {}
        actuated = []
        for dof in all_dofs:
            name = f"{dof.parent.name}-{dof.child.name}-{dof.axis.value}"
            rule = joints.classify(name, self.model)
            self.dof_mode[name] = rule.mode
            if rule.mode is joints.Mode.POWERED:
                actuated.append(dof)

        if self.tendons and self.model == "flybody":
            # Real tendons for the chains that have no muscles of their own.
            self.tendon_map = fly.add_tendons()
        else:
            self.tendon_map = {}

        # Torque actuators: a motor pool delivers force, not a position target.
        # A position servo would smuggle in a controller the fly does not have.
        fly.add_actuators(
            actuated, ActuatorType.MOTOR,
            forcelimited=True, forcerange=self.forcerange,
        )
        if self.tendon_map:
            fly.add_tendon_actuators()
        if self.adhesion and self.model == "flybody":
            self.adhesion_map = fly.add_leg_adhesion()
        else:
            self.adhesion_map = {}

        if self.vision:
            # Two compound-eye cameras plus the ommatidia sampling map. Must be
            # added before the model is compiled.
            fly.add_vision()

        fly.colorize()
        if self.with_camera:
            fly.add_tracking_camera()

        if self.self_collision:
            # Cap the COLLISION convex hull before the fly's meshes are copied
            # into the world's spec by attach; afterwards is too late.
            self._cap_collision_hulls(fly)

        world = FlatGroundWorld()
        contact_preset = (
            FlyBodyContactBodiesPreset.LEGS_THORAX_ABDOMEN_HEAD
            if self.model == "flybody"
            else ContactBodiesPreset.LEGS_THORAX_ABDOMEN_HEAD
        )
        world.add_fly(
            fly,
            spawn_position=np.array([0.0, 0.0, self.spawn_height]),
            spawn_rotation=Rotation3D("quat", [1.0, 0.0, 0.0, 0.0]),
            bodysegs_with_ground_contact=contact_preset,
            # flygym 2.1.0 emits ground-contact sensors whose object names lack
            # the attachment prefix, so compilation fails. Contact force is read
            # per body segment instead.
            add_ground_contact_sensors=False,
        )
        self.sim = Simulation(world, timestep=self.timestep)
        self.fly, self.world = fly, world

        m = self.sim.mj_model
        # The model carries motor, adhesion and tendon actuators together, but
        # each family is commanded through its own channel and its own length.
        all_actuators = [
            mj.mj_id2name(m, mj.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)
        ]
        self.actuator_names = [a for a in all_actuators if a.endswith("-motor")]
        # flygym's leg-adhesion channel takes one value per leg; the two
        # labrum adhesion actuators belong to feeding and are commanded apart.
        adhesion_all = [a for a in all_actuators if a.endswith("-adhesion")]
        self.adhesion_names = [a for a in adhesion_all if "_labrum" not in a]
        self.labrum_adhesion_names = [a for a in adhesion_all if "_labrum" in a]
        # Take the segment objects from the fly itself: each body model uses
        # its own BodySegment subclass, and a string would be coerced to the
        # base class and fail the lookup.
        wanted = {f"{leg}_tarsus{i}" for leg in LEGS for i in range(1, 6)}
        self.contact_segments = [
            seg for seg in fly.get_bodysegs_order() if seg.name in wanted
        ]
        self.contact_names = [seg.name for seg in self.contact_segments]
        self._apply_joint_limits()
        if self.self_collision:
            self._enable_self_collision()
        if self.aerodynamics:
            self._enable_aerodynamics()

    # --- physics setup -------------------------------------------------------

    def _apply_joint_limits(self) -> None:
        """Give every joint a range, and pin the ones that are not joints."""
        m, d = self.sim.mj_model, self.sim.mj_data
        self.locked_joints: list[str] = []
        for j in range(m.njnt):
            raw = mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j)
            if raw is None or m.jnt_type[j] != mj.mjtJoint.mjJNT_HINGE:
                continue                       # skip the free joint
            name = raw.removeprefix(f"{self.fly.name}/")
            try:
                rule = joints.classify(name, self.model)
            except KeyError:
                continue
            if rule.mode is joints.Mode.LOCKED:
                m.jnt_limited[j] = 1
                m.jnt_range[j] = (-LOCK_EPSILON_RAD, LOCK_EPSILON_RAD)
                m.jnt_stiffness[j] = LOCK_STIFFNESS
                self.locked_joints.append(name)
            elif rule.range_deg is not None:
                lo, hi = rule.range_deg
                if rule.measured and lo > 0:
                    # An absolute ANATOMICAL angle, e.g. femur-tibia 18 to 180
                    # deg. The joint coordinate q is not that angle: in flybody
                    # q = 18 deg is a geometric 113 deg. Until session 6 the
                    # range was applied to q directly, so the femur-tibia joint
                    # could not flex below its neutral pose (~113 deg) and
                    # "extended" past straight. Map through the geometry.
                    m.jnt_range[j] = self._anatomical_range(j, lo, hi)
                else:
                    q0 = float(d.qpos[m.jnt_qposadr[j]])
                    m.jnt_range[j] = (q0 + np.deg2rad(lo), q0 + np.deg2rad(hi))
                m.jnt_limited[j] = 1

    def _anatomical_range(self, j: int, lo_deg: float, hi_deg: float) -> tuple[float, float]:
        """q range realising an anatomical inter-segment angle range for a hinge
        between parent (femur) and child (tibia): the angle between the parent
        segment and the child segment (180 = straight), measured on the
        kinematics at two probe values of q."""
        m = self.sim.mj_model
        d = mj.MjData(m)
        d.qpos[:] = self.sim.mj_data.qpos
        child = m.jnt_bodyid[j]
        parent = m.body_parentid[child]
        grand = next((b for b in range(m.nbody) if m.body_parentid[b] == child), None)
        adr = m.jnt_qposadr[j]

        def angle(q: float) -> float:
            d.qpos[adr] = q
            mj.mj_kinematics(m, d)
            u = d.xpos[child] - d.xpos[parent]
            v = d.xpos[grand] - d.xpos[child]
            c = np.dot(-u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
            return float(np.degrees(np.arccos(np.clip(c, -1, 1))))

        q0 = float(self.sim.mj_data.qpos[adr])
        a0, a1 = angle(q0), angle(q0 + np.deg2rad(5.0))
        slope = (a1 - a0) / 5.0                      # anatomical deg per q deg
        s = 1.0 if slope > 0 else -1.0
        qa = q0 + np.deg2rad((lo_deg - a0) * s)
        qb = q0 + np.deg2rad((hi_deg - a0) * s)
        self.anatomical_map = getattr(self, "anatomical_map", {})
        self.anatomical_map[mj.mj_id2name(m, mj.mjtObj.mjOBJ_JOINT, j)] = (q0, a0, slope)
        return (min(qa, qb), max(qa, qb))

    def _cap_collision_hulls(self, owner) -> None:
        """Limit the vertex count of each mesh's COLLISION convex hull.

        Measured: colliding flybody's meshes at full resolution costs 5414 us
        per step against 162 us without self-collision, a factor of 34, because
        the hulls carry thousands of vertices each. Capping them keeps the real
        scanned geometry - this is still each mesh's own convex hull, not a
        fitted primitive - while making the narrow phase affordable. The visual
        mesh is untouched.
        """
        self.capped_meshes = 0
        for mesh in owner.mjcf_root.meshes:
            mesh.maxhullvert = self.max_hull_vertices
            self.capped_meshes += 1

    def _enable_self_collision(self) -> None:
        """Let the fly collide with itself.

        Both body models ship with every geom at contype=0, conaffinity=0, so
        nothing collides except through explicit ground pairs: the legs pass
        through each other and through the thorax. Enabling the default
        bitmasks on the fly's own geoms fixes that. MuJoCo excludes geoms in
        the same body and in parent-child bodies by itself, so adjacent leg
        segments do not generate contacts against their own joint.

        Mesh geoms collide as their convex hulls, which slightly fattens
        concave parts such as the claw and the wing edge.
        """
        m = self.sim.mj_model
        prefix = f"{self.fly.name}/"
        self.colliding_geoms = 0
        self.regions: dict[str, int] = {}

        # Decide per BODY, not by name alone: a body's physical shape is its
        # `_body`/`_lower` geom where it has one, and all of its geoms where it
        # does not. Otherwise the wings and the feet drop out of collision.
        physical: set[int] = set()
        by_body: dict[int, list[int]] = {}
        for g in range(m.ngeom):
            name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or ""
            if name.startswith(prefix):
                by_body.setdefault(int(m.geom_bodyid[g]), []).append(g)
        def vertex_count(g: int) -> int:
            mid = int(m.geom_dataid[g])
            return int(m.mesh_vertnum[mid]) if mid >= 0 else 0

        for geoms in by_body.values():
            named = [
                g for g in geoms
                if (mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or "")
                .removeprefix(prefix).endswith(PHYSICAL_GEOM_SUFFIXES)
            ]
            if named:
                physical.update(named)
            else:
                # No designated physical geom, as for the wings and the distal
                # tarsus. Take the SIMPLEST geom that represents the segment:
                # the wing membrane spans the same extent as its venation
                # overlay with 1,500 vertices against 18,684, and colliding
                # both would only duplicate every contact.
                physical.add(min(geoms, key=vertex_count))

        for g in range(m.ngeom):
            name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or ""
            if not name.startswith(prefix):
                continue                       # leave the ground plane alone
            short = name.removeprefix(prefix)
            if g not in physical:
                # flybody carries several geoms per body: one physical shape
                # plus colour overlays that occupy the SAME space. Colliding
                # the overlays duplicates every contact and is ruinously
                # expensive - the eye pigment mesh alone has 177,912 vertices
                # against 54,936 for the whole thorax. Collide the physical
                # geometry only.
                continue
            bit = 1 << _region_index(short)
            # MuJoCo collides two geoms when
            #     (contype1 & conaffinity2) or (contype2 & conaffinity1)
            # so giving each anatomical region its own bit, and letting each
            # region accept every bit but its own, collides ACROSS regions and
            # not within them. Segments inside one region nest at their
            # articulations - the convex hull of a rostrum overlaps its
            # haustellum - and colliding them would fight their own joints.
            m.geom_contype[g] = bit
            m.geom_conaffinity[g] = _ALL_REGION_BITS & ~bit
            b = int(m.geom_bodyid[g])
            # MuJoCo prunes candidate pairs at the BODY level first, using
            # masks aggregated from the geoms at compile time. Those compiled
            # to zero, so setting only the geom masks changes nothing and the
            # fly still passes through itself.
            m.body_contype[b] |= bit
            m.body_conaffinity[b] |= _ALL_REGION_BITS & ~bit
            self.colliding_geoms += 1
            self.regions[short] = _region_index(short)

    def _enable_aerodynamics(self) -> None:
        """Quasi-steady fluid forces in air.

        MuJoCo's fluid model is a quasi-steady approximation: added mass, blunt
        and slender drag, angular drag, Kutta lift and Magnus lift. It does NOT
        capture the unsteady mechanisms that dominate insect flight at
        Reynolds number ~100 - delayed stall and the leading-edge vortex,
        rotational circulation, and wake capture. Registered as the
        approximation it is; a blade-element or CFD treatment is the next step.
        """
        m = self.sim.mj_model
        m.opt.density = AIR_DENSITY
        m.opt.viscosity = AIR_VISCOSITY
        self.fluid_geoms: list[str] = []
        for g in range(m.ngeom):
            name = mj.mj_id2name(m, mj.mjtObj.mjOBJ_GEOM, g) or ""
            if "_wing" in name or "_haltere" in name:
                m.geom_fluid[g][0] = 1.0                      # enable ellipsoid
                m.geom_fluid[g][1:6] = ELLIPSOID_FLUID
                self.fluid_geoms.append(name)

    # --- shape ---------------------------------------------------------------

    @property
    def n_actuators(self) -> int:
        """Torque actuators only, which is what `actuate` commands."""
        return len(self.actuator_names)

    @property
    def n_adhesion(self) -> int:
        return len(self.adhesion_names)

    def summary(self) -> dict[str, Any]:
        m = self.sim.mj_model
        return {
            "model": self.model,
            "nq": m.nq, "nv": m.nv, "nu_total": m.nu,
            "n_motor": self.n_actuators, "n_adhesion": self.n_adhesion,
            "nbody": m.nbody,
            "ngeom": m.ngeom, "njnt": m.njnt, "ntendon": m.ntendon,
            "timestep": self.timestep,
            "total_mass_mg": float(m.body_mass.sum()) * 1e3,
            "colliding_geoms": getattr(self, "colliding_geoms", 0),
            "fluid_geoms": len(getattr(self, "fluid_geoms", [])),
            "locked_joints": len(getattr(self, "locked_joints", [])),
            "max_hull_vertices": self.max_hull_vertices,
            "capped_meshes": getattr(self, "capped_meshes", 0),
            "vision": self.vision,
        }

    # --- the loop ------------------------------------------------------------

    def observe(self) -> dict[str, np.ndarray]:
        """Everything the sensory model is allowed to read."""
        n = self.fly.name
        m, d = self.sim.mj_model, self.sim.mj_data
        # Internal interaction forces: the load transmitted THROUGH each body.
        # This is the right proxy for cuticular strain, which is what
        # campaniform sensilla actually transduce - far closer than ground
        # contact force, though still not a deformation model.
        mj.mj_rnePostConstraint(m, d)
        return {
            "joint_angles": np.asarray(self.sim.get_joint_angles(n)),
            "joint_velocities": np.asarray(self.sim.get_joint_velocities(n)),
            "contact_forces": np.asarray(
                self.sim.get_bodysegment_contact_forces(n, self.contact_segments)
            ),
            "body_positions": np.asarray(self.sim.get_body_positions(n)),
            "segment_load": np.asarray(d.cfrc_int).copy(),
            "xpos": np.asarray(d.xpos).copy(),
            "n_contacts": int(d.ncon),
        }

    def actuate(self, torques: np.ndarray) -> None:
        if torques.shape != (self.n_actuators,):
            raise ValueError(
                f"expected {self.n_actuators} torques, got {torques.shape}"
            )
        self.sim.set_actuator_inputs(self.fly.name, ActuatorType.MOTOR, torques)

    def set_adhesion(self, states: np.ndarray) -> None:
        """Tarsal adhesion, one value per leg, driven by the long tendon pool."""
        if not self.adhesion_map:
            return
        self.sim.set_leg_adhesion_states(self.fly.name, states)

    def step(self) -> None:
        # passive force hooks (e.g. coupled leg springs, passive.CoupledSprings)
        # write qfrc_applied before each physics step
        for hook in getattr(self, "passive_hooks", ()):
            hook(self.sim.mj_data)
        self.sim.step()

    def extra_potential(self) -> float:
        """Potential energy stored by passive hooks (not in MuJoCo's d.energy)."""
        return float(sum(getattr(h, "energy", lambda d: 0.0)(self.sim.mj_data)
                         for h in getattr(self, "passive_hooks", ())))

    def reset(self) -> None:
        self.sim.reset()
