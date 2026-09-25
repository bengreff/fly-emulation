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

from . import connectome, interface, lif, neuromuscular, sensory, vision
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

    reg: Registry = field(init=False)
    body: Body = field(init=False)
    conn: connectome.Connectome = field(init=False)
    net: lif.Network = field(init=False)
    nm: neuromuscular.Neuromuscular = field(init=False)
    aff: sensory.Afferents = field(init=False)

    def __post_init__(self) -> None:
        self.reg = Registry(self.policy)
        self.reg.overrides.update(self.overrides)
        self.body = Body(timestep=self.timestep_ms / 1000.0)
        self.conn = connectome.build(
            self.reg, min_synapses=self.min_synapses
        )
        params = lif.default_params(
            self.reg, self.conn, timestep_ms=self.timestep_ms
        )
        self.net = lif.Network(
            self.conn, params, self.timestep_ms,
            rng=np.random.default_rng(self.seed),
        )
        self.nm = neuromuscular.build(
            self.reg, self.conn, self.body.actuator_names,
            fly_name=self.body.fly.name,
            adhesion_names=self.body.adhesion_names,
            model=self.body.model,
        )
        self.aff = sensory.build(self.reg, self.conn, self.body)
        self.vis = (
            vision.build(self.reg, self.conn, timestep_ms=self.timestep_ms)
            if self.body.vision else None
        )
        # Record every brain-body channel, including the ones with no
        # implementation, so the inventory measures interface completeness
        # rather than only the parts that happen to be wired.
        self.channels = interface.register(self.reg)

    # --- running -------------------------------------------------------------

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
            drive = self.aff.drive(obs)
            if self.vis is not None:
                # The eyes are rendered at their own rate; between renders the
                # photoreceptors hold their last drive.
                if step % self.vis.sample_every == 0:
                    drive = drive + self.vis.drive(
                        np.asarray(self.body.sim.get_ommatidia_readouts(
                            self.body.fly.name))
                    )
                else:
                    drive = drive + self.vis.last()
            spiked = self.net.step(external_mv=drive)
            if spike_cap_per_step is not None and spiked.size > spike_cap_per_step:
                raise RuntimeError(
                    f"runaway activity: {spiked.size:,} neurons spiked in one "
                    f"step at t={step * self.timestep_ms:.1f} ms"
                )
            spike_counts[spiked] += 1
            torque = self.nm.step(spiked, self.timestep_ms)
            self.body.actuate(torque)
            self.body.set_adhesion(self.nm.grip)
            self.body.step()

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
