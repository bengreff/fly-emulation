"""The organism: body, network, and the two interfaces between them, in a loop.

    body state  ->  afferent drive  ->  CNS  ->  motor spikes  ->  torque  ->  body

Nothing bypasses those channels. The network sees the body only through its
afferents, and the body receives only muscle torque. There is no controller, no
prescribed gait, no descending command beyond what the network produces.

With the parameters guessed, this is expected to flail. That is the point: it
flails through the anatomy rather than through a policy, and every guess it
flails with is recorded in the inventory the run emits.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import adhesion, connectome, extrasenses, interface, lif, muscles, neuromuscular, olfaction, passive, profiles, sensory, vision
from .world import World
from .body import Body
from .registry import Policy, Registry, Requirement


class StrictRefusal(Exception):
    """C0: the model will not integrate, and the refusal list is the result."""

    def __init__(self, refusals: list[Requirement]) -> None:
        elements = sum(r.instances for r in refusals)
        super().__init__(
            f"refusing to integrate: {len(refusals)} unresolved requirements "
            f"covering {elements:,} model elements"
        )
        self.refusals = refusals


@dataclass
class Organism:
    timestep_ms: float = 0.1
    policy: Policy | str = Policy.MINIMAL
    seed: int = 0
    min_synapses: int = 1
    overrides: dict = field(default_factory=dict)
    profile: str | None = None   # a named borrowed parameter set (profiles.py)
    world: World = field(default_factory=World)
    with_camera: bool = False    # attach the tracking camera (for rendering only)

    reg: Registry = field(init=False)
    body: Body = field(init=False)
    conn: connectome.Connectome = field(init=False)
    net: lif.Network = field(init=False)
    nm: neuromuscular.Neuromuscular = field(init=False)
    aff: sensory.Afferents = field(init=False)

    def __post_init__(self) -> None:
        self.reg = Registry(self.policy)
        self.reg.overrides.update(self.overrides)
        self.kick_mv = None
        if self.profile:
            self.kick_mv = profiles.apply(self.reg, self.profile)["kick_mv"]
        self.body = Body(timestep=self.timestep_ms / 1000.0, with_camera=self.with_camera)
        # B3/B14 passive mechanics (session 9): switches default to the legacy body
        passive.register(self.reg, self.body)
        passive.register_rest(self.reg, self.body)
        passive.register_wings(self.reg, self.body)
        self.conn = connectome.build(
            self.reg, min_synapses=self.min_synapses
        )
        params = lif.default_params(
            self.reg, self.conn, timestep_ms=self.timestep_ms
        )
        # temperature dependence: time constants scale by Q10^((T - Tref)/10)
        q10 = self.reg.require(
            "cell_type:all", "q10", units="dimensionless",
            model_use="temperature scaling of membrane, synaptic and refractory times",
            subsystem="neuron_biophysics", instances=self.conn.n, minimal=2.0,
            justification="Q10 of 2-3 is typical for insect neuronal and channel kinetics "
                          "(e.g. Hille; Robertson & Money 2012 review of insect thermal "
                          "effects); 2 taken, one value for all types",
            uncertainty="per-type Q10 unmeasured; reference 25 degC is the world default")
        f = q10 ** ((self.world.temperature_c - 25.0) / 10.0)
        if f != 1.0:
            params.tau_m = params.tau_m / f
            params.tau_s = np.asarray(params.tau_s) / f
            params.t_ref = params.t_ref / f
        self.net = lif.Network(
            self.conn, params, self.timestep_ms,
            rng=np.random.default_rng(self.seed),
        )
        # N12 identified electrical synapses (s10: wired into the organism; strength 0 = absent in m4)
        from . import electrical
        el = electrical.build(self.reg, self.conn)
        if len(el[0]):
            self.net.elec = el
        self.nm = neuromuscular.build(
            self.reg, self.conn, self.body.actuator_names,
            fly_name=self.body.fly.name,
            adhesion_names=self.body.adhesion_names,
            model=self.body.model,
        )
        # B7 adhesion gate (session 9): grip needs surface contact, released by shear
        self.adhesion_gate = bool(int(self.reg.require(
            "adhesion:leg", "detachment", units="enum",
            model_use="0 neural grip only (legacy m4), 1 gated by tarsal load and shear (adhesion.py)",
            subsystem="body_mechanics", minimal=0,
            minimal_note="legacy m4; the load/shear gate is a template option")))
        # B4/B5 antagonist Hill muscles on the legs (session 9); 0 = legacy net torque
        self.hill = None
        if int(self.reg.require(
                "muscle:leg", "model", units="enum",
                model_use="0 net torque per DOF (legacy m4), 1 antagonist Hill muscle pairs",
                subsystem="muscle_mechanics", minimal=0,
                minimal_note="legacy m4; Hill pairs are an option until adopted")):
            fused = self.reg.require(
                "motor_unit:leg", "fused_rate", units="Hz",
                model_use="unit firing rate at which its force saturates (B5)",
                subsystem="muscle_mechanics", minimal=100.0,
                minimal_note="guessed; bounded in data/model/parameters.csv (b5_fused_hz)")
            fb = pd.read_csv(neuromuscular.FORCE_TABLE, comment="#").set_index("bodyId").unit_class
            bid = self.conn.neurons.bodyId.to_numpy()[self.nm.mn_index]
            ucls = fb.reindex(bid).fillna("intermediate").to_numpy()
            remap = {}
            if int(self.reg.require(
                    "muscle:leg", "rotator_map", units="enum",
                    model_use="sternal rotator MNs: 0 legacy rule (least-foot-motion coxa joint, assumed sign), "
                              "1 by action (anterior = protraction, posterior = retraction)",
                    subsystem="muscle_mechanics", minimal=1,
                    justification="Cheong et al. eLife PMC13384506 (read s9): anterior rotator MNs 'rotate the "
                                  "leg forwards during the swing phase'; posterior rotator MNs 'rotate the coxa "
                                  "posteriorly' (stance); joint and sign from the calibrated foot action")):
                cal = neuromuscular.load_calibration(self.body.model)
                short = [a.split("/")[-1].removesuffix("-motor") for a in self.body.actuator_names]
                mtypes = self.conn.neurons.type.fillna("").to_numpy()[self.nm.mn_index]
                acts = {"Sternal anterior rotator MN": "protraction", "Sternal posterior rotator MN": "retraction"}
                for k, (t, ai) in enumerate(zip(mtypes, self.nm.actuator_index)):
                    if t in acts:
                        leg = short[ai].split("-")[1].split("_")[0]
                        r = neuromuscular.resolve_sign(cal, leg, "ThC", acts[t])
                        if r is not None:
                            remap[k] = (r[0], float(r[1]))
            # s10: anatomical coxa muscles with moment-arm vectors (0 = s9 per-DOF pairs)
            coxa_model = int(self.reg.require(
                "muscle:leg", "coxa_model", units="enum",
                model_use="coxa muscles: 0 one antagonist pair per flybody coxa hinge (s9), 1 anatomical "
                          "FlyMimic coxa muscles with moment-arm vectors over all three hinges, MNs joined by type",
                subsystem="muscle_mechanics", minimal=0,
                minimal_note="s9 behaviour; 1 is an option (scripts/build_coxa_muscles.py; s10)"))
            units_kw = {"fused_hz": float(fused)}
            fat = float(self.reg.require(
                "motor_unit:leg", "fatigue_fraction", units="dimensionless",
                model_use="fraction of a fast/intermediate unit's resource used per spike (B5 fatigue)",
                subsystem="muscle_mechanics", minimal=0.0,
                minimal_note="neutral: no fatigue; bounded in parameters.csv (b5_fatigue_fraction)"))
            if fat > 0.0:
                units_kw["fatigue_fraction"] = fat
                units_kw["fatigue_tau_ms"] = float(self.reg.require(
                    "motor_unit:leg", "fatigue_tau_ms", units="ms",
                    model_use="recovery time constant of the fatigue resource (B5)",
                    subsystem="muscle_mechanics", minimal=muscles.FATIGUE_TAU_MS,
                    minimal_note="guessed; bounded in parameters.csv (b5_fatigue_tau_ms)"))
            mn_types = self.conn.neurons.type.fillna("").to_numpy()[self.nm.mn_index]
            self.hill = muscles.HillLegDrive(self.nm, self.body, unit_class=ucls, remap=remap,
                                             units_kw=units_kw, coxa_model=coxa_model,
                                             mn_types=mn_types)
            self.nm.bypass_forbidden = True
        self.aff = sensory.build(self.reg, self.conn, self.body, params)
        self.vis = (
            vision.build(self.reg, self.conn, timestep_ms=self.timestep_ms)
            if self.body.vision else None
        )
        if self.vis is not None:
            vision.install_connectome_mask(self.reg, self.body.sim)
        self.chem = olfaction.build(self.reg, self.conn, self.body, params,
                                    timestep_ms=self.timestep_ms, seed=self.seed)
        self.extra = extrasenses.build(self.reg, self.conn, self.body)
        # --- S1-S4, N20, N25, N26 internal state (task 12); state:organs|model 0 = off (m4) ---
        from . import internal_state
        self.organs = internal_state.build(self.reg, self.conn)
        # --- end internal state ---
        # Record every brain-body channel, including the ones with no
        # implementation, so the inventory measures interface completeness
        # rather than only the parts that happen to be wired.
        self.channels = interface.register(self.reg)
        # B10/B13 flight motor (session 10): 0 = legacy wing torques (m4)
        self.flight = None
        mode = int(self.reg.require(
            "flight:wings", "generator", units="enum",
            model_use="0 legacy direct wing torques (m4), 1 wingbeat generator driven by power MNs "
                      "(flight.py), 2 generator forced on (tethered-flight probes)",
            subsystem="muscle_mechanics", minimal=0,
            minimal_note="legacy m4; the generator needs timestep <= 0.05 ms"))
        if mode:
            from . import flight
            self.flight = flight.FlightMotor(self.reg, self.conn, self.body, self.timestep_ms,
                                             force_on=mode == 2)
        if int(self.reg.require(
                "joint:wing", "range_by_function", units="enum",
                model_use="0 joints.py wing envelopes (pitch = stroke; wrong for flybody), 1 envelopes by "
                          "function: yaw = stroke, roll = deviation, pitch = rotation (F-WING-1)",
                subsystem="body_mechanics", minimal=0, minimal_note="legacy m4 envelopes")):
            from . import flight
            flight.apply_wing_ranges(self.body)

    # --- sensing -------------------------------------------------------------

    def sense(self, step: int, obs: dict) -> np.ndarray:
        """All afferent drive for this step: body senses, eyes, chemosenses.

        The single place where the world and body reach the network, used by
        run() and by the recording scripts alike.
        """
        self._last_obs = obs
        drive = self.aff.drive(obs)
        if self.vis is not None:
            # The eyes are rendered at their own rate; between renders the
            # photoreceptors hold their last drive.
            if step % self.vis.sample_every == 0:
                drive = drive + self.vis.drive(np.asarray(
                    self.body.sim.get_ommatidia_readouts(self.body.fly.name)))
            else:
                drive = drive + self.vis.last()
        drive = drive + self.chem.drive(self.world, self.body.sim.mj_data.xpos)
        drive = drive + self.extra.drive(self.world, self.body, obs, self.timestep_ms)
        drive = drive if self.organs is None else drive + self.organs.drive(self, self.timestep_ms, drive)
        return drive

    # --- running -------------------------------------------------------------

    def motor_step(self, spiked: np.ndarray, extra: dict[int, float] | None = None) -> np.ndarray:
        """Motor spikes -> muscles -> body, then advance the body one step.
        The single motor path: probes that step the loop themselves must call
        this, or they silently bypass mechanisms such as Hill mode (s9).
        `extra` adds an external (probe) torque per actuator index, e.g. a
        joint clamp; it is not a muscle and is applied after them."""
        self.nm.bypass_forbidden = False
        torque = self.nm.step(spiked, self.timestep_ms)
        self.nm.bypass_forbidden = self.hill is not None
        if self.hill is not None:
            self.hill.step(spiked, self.timestep_ms)
            torque = self.hill.torque(self.nm, self.body.sim.mj_data, torque)
        if self.flight is not None:
            torque = self.flight.step(spiked, torque)
        if extra:
            torque = np.array(torque, dtype=np.float32, copy=True)
            for j, v in extra.items():
                torque[j] += v
        self.body.actuate(torque)
        grip = self.nm.grip
        if self.adhesion_gate and getattr(self, "_last_obs", None) is not None:
            grip = grip * adhesion.gate(self._last_obs["contact_forces"])
        self.body.set_adhesion(grip)
        self.body.step()
        return torque

    def run(
        self,
        duration_ms: float,
        *,
        record_every: int = 10,
        spike_cap_per_step: int | None = None,
    ) -> pd.DataFrame:
        """Run the closed loop. Returns a per-sample trace."""
        if self.reg.policy is Policy.STRICT and self.reg.refusals:
            raise StrictRefusal(self.reg.refusals)

        n_steps = int(round(duration_ms / self.timestep_ms))
        trace = []
        spike_counts = np.zeros(self.conn.n, dtype=np.int32)

        for step in range(n_steps):
            obs = self.body.observe()
            drive = self.sense(step, obs)
            spiked = self.net.step(external_mv=drive)
            if spike_cap_per_step is not None and spiked.size > spike_cap_per_step:
                raise RuntimeError(
                    f"runaway activity: {spiked.size:,} neurons spiked in one "
                    f"step at t={step * self.timestep_ms:.1f} ms"
                )
            spike_counts[spiked] += 1
            torque = self.motor_step(spiked)

            if step % record_every == 0:
                trace.append({
                    "t_ms": step * self.timestep_ms,
                    "n_spiked": int(spiked.size),
                    "thorax_x": float(obs["body_positions"][0, 0]),
                    "thorax_y": float(obs["body_positions"][0, 1]),
                    "thorax_z": float(obs["body_positions"][0, 2]),
                    "contact_total": float(
                        np.abs(obs["contact_forces"]).sum()
                    ),
                    "torque_absmean": float(np.abs(torque).mean()),
                    "afferent_drive_mean": float(drive[self.aff.rows].mean())
                    if self.aff.rows.size else 0.0,
                })

        self.spike_counts = spike_counts
        self.duration_ms = n_steps * self.timestep_ms
        return pd.DataFrame(trace)

    # --- what the run says ---------------------------------------------------

    def population_rates(self) -> pd.DataFrame:
        """Mean firing rate by superclass, in Hz."""
        n = self.conn.neurons
        hz = self.spike_counts / (self.duration_ms / 1000.0)
        df = pd.DataFrame({
            "superclass": n.superclass.fillna("unannotated").to_numpy(),
            "hz": hz,
        })
        return (
            df.groupby("superclass")
            .agg(neurons=("hz", "size"), mean_hz=("hz", "mean"),
                 max_hz=("hz", "max"), frac_active=("hz", lambda s: (s > 0).mean()))
            .sort_values("neurons", ascending=False)
        )

    def write_inventory(self, path: str | Path) -> Path:
        return self.reg.write(path)
