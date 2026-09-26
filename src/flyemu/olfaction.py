"""Olfaction, CO2, humidity and temperature: world fields to receptor drive.

For each olfactory receptor neuron (ORN_<glomerulus>):

    drive_mV = max_drive * sum_o  r(type, o) * c_o / (c_o + K)

- r(type, o): DoOR 2.0 consensus response, normalised 0-1. **Measured**
  (relative), via data/derived/orn_tuning_door.csv. An odour the type was
  never tested with contributes 0 (**inferred**: untested is not the same as
  no response, and is recorded as such).
- c_o: concentration at the cell's own antenna (left/right from the instance
  suffix; unknown-side cells average both). **Derived** from World.
- K, max_drive: **inferred** (no absolute calibration: DoOR is relative and
  Hallem & Carlson rates are heterologous).

Absolute rate calibration (session 6, default on when the network's LIF
parameters are passed): each ORN type gets a target rate

    rate = SFR + A * sum_o r(type, o) * c_o / (c_o + K),   A = (Rmax - SFR) / (1e-2 / (1e-2 + K))

with SFR and Rmax per type from Hallem & Carlson 2006 (data/params/orn_rates.csv;
SFR measured, Rmax derived, both heterologous, empty-neuron recordings; the
median for types without a Hallem receptor, inferred). A matches Rmax at the
10^-2 dilution Hallem used. ORN spikes are then generated as a Poisson
process with dead time: each step a cell receives, with probability
lambda*dt, a one-step pulse that crosses its threshold, where
lambda = rate / (1 - rate * t_ref) so that pulses lost in refractory are
compensated. So the ORN rate, not a mV drive, is the calibrated quantity, and
spontaneous firing is irregular, as recorded (a noise-free LIF cannot fire at
1-2 Hz from a constant drive). Spike generation is thereby a rate model at the
receptor; the ORN's own LIF only supplies refractoriness.
- ORN adaptation dynamics (Nagel & Wilson 2011; Gorur-Shandilya 2017) are
  omitted: a static transduction, recorded as unresolved.

CO2 (ORN_V): DoOR's Gr21a/Gr63a unit with the World CO2 fraction, K = 0.05
(half-maximal near 5%, measured qualitatively; Jones 2007, Kwon 2007).
Humidity: dry cells (HRN_VP4) are driven by 1-RH and moist cells (HRN_VP5,
TRN_VP1m putative) by RH; tonic and non-adapting (Enjin 2016; Knecht 2016).
Temperature cells (TRN_VP2 hot, TRN_VP3a/b and HRN_VP1l cool) respond to
dT/dt (Gallio 2011; Budelli 2019), so a static world gives them only their
baseline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .registry import Registry, Status
from .world import World

REPO = Path(__file__).resolve().parents[2]
CO2_KEY = "CURLTUGMZLYLDI-UHFFFAOYSA-N"


@dataclass
class Chemosenses:
    rows: np.ndarray            # network rows of driven cells
    side: np.ndarray            # 0 left antenna, 1 right, 2 both
    tuning: pd.DataFrame        # (cell index) x odour key -> relative response
    kind: np.ndarray            # 'orn' | 'co2' | 'dry' | 'moist' | 'thermo'
    max_drive: float
    half_sat: float
    co2_half_sat: float
    baseline: float
    antenna_bodies: tuple[int, int]
    n_neurons: int
    sfr_hz: np.ndarray | None = None      # per row; rate mode when set
    amp_hz: np.ndarray | None = None
    t_ref_ms: np.ndarray | None = None    # per row
    pulse_mv: np.ndarray | None = None    # per row: one-step drive that crosses threshold
    dt_ms: float = 0.1
    rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(0))
    last_rate_hz: np.ndarray | None = None

    def rate_to_pulses(self, hz: np.ndarray, sel=slice(None)) -> np.ndarray:
        """Poisson-with-dead-time pulses realising rate `hz` (rows `sel`)."""
        hz = np.clip(np.asarray(hz, dtype=float), 0.0, None)
        tr = self.t_ref_ms[sel] / 1000.0
        lam = hz / np.maximum(1.0 - hz * tr, 0.05)
        fire = self.rng.random(hz.shape) < lam * self.dt_ms / 1000.0
        return np.where(fire, self.pulse_mv[sel], 0.0).astype(np.float32)

    def drive(self, world: World, xpos: np.ndarray) -> np.ndarray:
        out = np.zeros(self.n_neurons, dtype=np.float32)
        ant = xpos[list(self.antenna_bodies)]                 # (2, 3)
        conc = world.odour_concentrations(ant)                # odour -> (2,)
        val = np.full(len(self.rows), self.baseline, dtype=np.float32)
        orn = self.kind == "orn"
        if conc and orn.any():
            acc = np.zeros(len(self.rows))
            for odour, c in conc.items():
                if odour not in self.tuning.columns:
                    continue
                c_side = np.where(self.side == 0, c[0], np.where(self.side == 1, c[1], c.mean()))
                acc += self.tuning[odour].to_numpy() * c_side / (c_side + self.half_sat)
            if self.sfr_hz is None:
                val[orn] += self.max_drive * acc[orn]
            else:
                val[orn] = acc[orn]            # response fraction, converted below
        if self.sfr_hz is not None:
            resp = val[orn] if (conc and orn.any()) else np.zeros(int(orn.sum()))
            self.last_rate_hz = self.sfr_hz[orn] + self.amp_hz[orn] * resp
            val[orn] = self.rate_to_pulses(self.last_rate_hz, orn)
        co2 = self.kind == "co2"
        if co2.any():
            r = self.tuning.get(CO2_KEY, pd.Series(1.0, index=self.tuning.index)).to_numpy()
            c = world.co2_fraction
            val[co2] += self.max_drive * r[co2] * c / (c + self.co2_half_sat)
        val[self.kind == "dry"] += self.max_drive * (1 - world.humidity_rh)
        val[self.kind == "moist"] += self.max_drive * world.humidity_rh
        out[self.rows] = val
        return out


def build(reg: Registry, conn, body, params=None, timestep_ms: float = 0.1,
          seed: int = 0) -> Chemosenses:
    """`params`: the network's LIFParams. When given (and the registry keeps
    orn:all|rate_calibration = 1), ORNs are driven to Hallem-calibrated rates."""
    n = conn.neurons
    t = n.type.fillna("")
    sel = t.str.match(r"^(ORN_|HRN_|TRN_)").to_numpy()
    idx = np.flatnonzero(sel)
    types = t.to_numpy()[idx]
    inst = n.instance.fillna("").to_numpy()[idx]
    side = np.where(pd.Series(inst).str.endswith("_L"), 0,
                    np.where(pd.Series(inst).str.endswith("_R"), 1, 2))

    kind = np.array(["orn"] * len(idx), dtype=object)
    kind[types == "ORN_V"] = "co2"
    kind[np.isin(types, ["HRN_VP4"])] = "dry"
    kind[np.isin(types, ["HRN_VP5", "TRN_VP1m"])] = "moist"
    kind[np.isin(types, ["TRN_VP2", "TRN_VP3a", "TRN_VP3b", "HRN_VP1l", "HRN_VP1d"])] = "thermo"

    tun = pd.read_csv(REPO / "data" / "derived" / "orn_tuning_door.csv")
    # several DoOR units per glomerulus: take the mean over units per odour
    tun = tun.groupby(["orn_type", "odour_inchikey"]).response.mean().unstack()
    tuning = tun.reindex(types).fillna(0.0).reset_index(drop=True)

    m = body.sim.mj_model
    ab = tuple(next(i for i in range(m.nbody) if m.body(i).name.endswith(f"{s}_antenna"))
               for s in ("l", "r"))

    n_orn = int((kind == "orn").sum())
    has_profile = pd.Series(types[kind == "orn"]).isin(tun.index).sum()
    reg.provide("orn:all", "odour_tuning", "data/derived/orn_tuning_door.csv",
                units="relative 0-1", model_use="receptor tuning to each odour",
                status=Status.MEASURED, subsystem="sensory_transduction",
                instances=int(has_profile),
                evidence="DoOR 2.0 consensus (Münch & Galizia 2016), joined by glomerulus",
                uncertainty="relative only; untested odour -> 0 response is an inference; "
                            "5 ORN types have no profile (DA1, VA7m, VM6l/m/v)")
    max_drive = reg.require("orn:all", "max_drive", units="mV",
                            model_use="drive at full normalised response",
                            subsystem="sensory_transduction", instances=len(idx),
                            minimal=15.0, minimal_note="declared default; no absolute calibration")
    half = reg.require("orn:all", "half_saturation", units="dilution fraction",
                       model_use="c/(c+K) dose-response", subsystem="sensory_transduction",
                       instances=n_orn, minimal=1e-3,
                       minimal_note="declared default; DoOR/Hallem data are at 1e-2 dilution")
    co2k = reg.provide("orn:ORN_V", "co2_half_saturation", 0.05, units="volume fraction",
                       model_use="CO2 dose-response", status=Status.DERIVED,
                       subsystem="sensory_transduction", instances=int((kind == "co2").sum()),
                       evidence="about half-maximal near 5% CO2 (Jones 2007; Kwon 2007)",
                       uncertainty="read off qualitative dose-response, no Hill fit")
    base = reg.require("chemosense:all", "baseline_drive", units="mV",
                       model_use="drive in clean air", subsystem="sensory_transduction",
                       instances=len(idx), minimal=0.0,
                       minimal_note="declared default: no spontaneous drive (ORNs "
                                    "fire spontaneously in the animal; F-GAP-1 style gap)")
    reg.provide("orn:all", "adaptation_dynamics", None, units="dimensionless",
                model_use="omitted: static transduction", status=Status.UNRESOLVED,
                subsystem="sensory_transduction", instances=n_orn,
                evidence="LN + Weber-adapting gain models exist (Martelli 2013; "
                         "Gorur-Shandilya 2017); constants not yet extracted")
    reg.provide("thermo:all", "dT_dt_transduction", None, units="mV per degC/s",
                model_use="phasic temperature response", status=Status.UNRESOLVED,
                subsystem="sensory_transduction", instances=int((kind == "thermo").sum()),
                evidence="cooling/heating cells are phasic (Budelli 2019); static world")

    rows = conn.index_of(n.bodyId.to_numpy()[idx])
    sfr = amp = None
    if params is not None and reg.require(
            "orn:all", "rate_calibration", units="boolean",
            model_use="drive ORNs to absolute rates (Hallem 2006) instead of a mV scale",
            subsystem="sensory_transduction", instances=n_orn, minimal=0.0,
            minimal_note="off by default: with Hallem spontaneous rates the m2 network "
                         "enters a self-sustaining state in about half of seeds (F-ORN-2, "
                         "pre-registered criterion failed); 1 enables absolute ORN rates"):
        rt = pd.read_csv(REPO / "data" / "params" / "orn_rates.csv", comment="#").set_index("orn_type")
        med = rt[rt.sfr_basis == "measured"][["sfr_hz", "rmax_hz"]].median()
        sfr = rt.sfr_hz.reindex(types).fillna(med.sfr_hz).to_numpy(float).copy()
        rmax = rt.rmax_hz.reindex(types).fillna(med.rmax_hz).to_numpy(float)
        sfr[kind != "orn"] = 0.0
        amp = (rmax - sfr) / (1e-2 / (1e-2 + float(half)))
        pick = lambda a: np.broadcast_to(np.asarray(a, dtype=float), (conn.n,))[rows]  # noqa: E731
        v_th, v_rest, tau, t_ref = (pick(getattr(params, k)) for k in ("v_th", "v_rest", "tau_m", "t_ref"))
        # from anywhere at or above rest, one step of this drive crosses threshold
        pulse = 1.5 * (v_th - v_rest) / (1.0 - np.exp(-timestep_ms / tau))
        orn_types = pd.Series(types[kind == "orn"])
        meas = orn_types.isin(rt.index[rt.sfr_basis == "measured"])
        reg.provide("orn:hallem_types", "spontaneous_rate", "data/params/orn_rates.csv",
                    units="Hz", model_use="ORN rate in clean air", status=Status.MEASURED,
                    subsystem="sensory_transduction", instances=int(meas.sum()),
                    evidence="Hallem & Carlson 2006 Cell 125:143 SFR, via DoOR.data Hallem.2006.EN",
                    uncertainty="heterologous (Or expressed in the ab3A empty neuron); one "
                                "recording set; native SFR may differ")
        reg.provide("orn:hallem_types", "max_rate", "data/params/orn_rates.csv",
                    units="Hz", model_use="ORN rate at the strongest tested odour, 1e-2",
                    status=Status.DERIVED, subsystem="sensory_transduction",
                    instances=int(meas.sum()), method="SFR + max SFR-subtracted response "
                    "over 110 odours; mapped to DoOR tuning 1 at 1e-2 dilution",
                    evidence="Hallem & Carlson 2006 via DoOR.data",
                    uncertainty="heterologous; DoOR consensus max need not be the Hallem max odour")
        reg.provide("orn:other_types", "spontaneous_and_max_rate", "data/params/orn_rates.csv",
                    units="Hz", model_use="ORN rates for types without a Hallem receptor",
                    status=Status.INFERRED, subsystem="sensory_transduction",
                    instances=int((~meas).sum()),
                    evidence="median over Hallem-covered types",
                    uncertainty="types differ (Hallem SFR 1-47 Hz, Rmax 71-300 Hz)")
    return Chemosenses(rows=rows.astype(np.int64), side=side, tuning=tuning, kind=kind,
                       max_drive=float(max_drive), half_sat=float(half),
                       co2_half_sat=float(co2k), baseline=float(base),
                       antenna_bodies=ab, n_neurons=conn.n,
                       sfr_hz=sfr, amp_hz=amp,
                       t_ref_ms=None if sfr is None else t_ref, pulse_mv=None if sfr is None else pulse,
                       dt_ms=timestep_ms, rng=np.random.default_rng(seed + 7))
