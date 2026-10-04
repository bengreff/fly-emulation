"""flyemu-protocol/1: one JSON document describing an experiment (configuration,
build-time genotype, run-time stimuli, what to record, what a real fly does).
The recorder executes it and embeds it, resolved, in the recording.

Effectors, all through the model's public API (Organism / Network.step):

  genotype  TNT         Network.silence(rows) before the run (irreversible output block)
            Kir2.1      constant hyperpolarising current from step 0 (approximation:
                        a K+ leak would be a conductance that shunts and reverses)
  events    current     external_mv added to the target rows (mV of steady-state
                        depolarisation in current mode); optional pulse train
            CsChrimson  approximated as `current` (+mV) while the light is on
            GtACR1      approximated as `current` (-mV) while the light is on
            kick        Poisson input as in Shiu et al. 2024: each event is the
                        profile's kick (Network.step(kick=...)), large enough to
                        force a spike; rate_hz per cell
            world       set fields of the organism's World (food patches, odour
                        sources, wind, sound, humidity, CO2, light) for the event's
                        duration; the fly senses them only through its receptors

Every approximation is written into the resolved protocol as `approximation`, so
the app can show it next to the result. Random kicks use their own generator
(seeded from the run seed), so a stimulated run and its control share every
model random draw and are identical before the first event.
"""
from __future__ import annotations

import copy
import re

import numpy as np
import pandas as pd

APPROX = {
    "current": None,
    "CsChrimson": "current injection standing in for a light-gated cation conductance "
                  "(no reversal potential, no channel kinetics, no light scattering)",
    "GtACR1": "hyperpolarising current standing in for an anion conductance "
              "(no shunting, no reversal potential, no channel kinetics)",
    "kick": "Poisson input as in Shiu et al. 2024: each event forces a spike in a resting cell, "
            "so the target fires at about the set rate whatever its synaptic input",
    "world": None,
    "TNT": None,
    "Kir2.1": "constant hyperpolarising current standing in for a K+ leak conductance "
              "(no shunting, no reversal potential)",
}
DEFAULT_MV = {"current": 10.0, "CsChrimson": 10.0, "GtACR1": -10.0, "Kir2.1": -10.0}
CURRENT_LIKE = ("current", "CsChrimson", "GtACR1")
SELECTORS = ("bodyId", "type", "class", "superclass", "somaSide", "instance")
# World fields an event may set (world.World); temperature is excluded because its
# Q10 scaling of the network is applied once, at build time.
WORLD_FIELDS = ("food", "odours", "wind_mm_s", "sound_mm_s", "sound_hz", "sound_dir",
                "humidity_rh", "co2_fraction", "light_lux")
MAX_DURATION_MS = 10_000.0


def resolve_target(target: dict, neurons: pd.DataFrame) -> np.ndarray:
    """Rows of `neurons` (the model's row order) matching every given key."""
    if not any(k in target for k in SELECTORS):
        raise ValueError(f"target {target} names no selector")
    keep = np.ones(len(neurons), dtype=bool)
    if "bodyId" in target:
        ids = np.atleast_1d(np.asarray(target["bodyId"], dtype=np.int64))
        keep &= np.isin(neurons["bodyId"].to_numpy().astype(np.int64), ids)
    for key in SELECTORS[1:]:
        if key not in target:
            continue
        col = neurons[key].astype(str).to_numpy()
        want = target[key]
        if isinstance(want, str) and want.startswith("re:"):
            rx = re.compile(want[3:])
            keep &= np.fromiter((bool(rx.fullmatch(c)) for c in col), bool, len(col))
        else:
            keep &= np.isin(col, np.atleast_1d(want).astype(str))
    return np.flatnonzero(keep)


def target_label(target: dict) -> str:
    return " ".join(f"{k}={'/'.join(map(str, np.atleast_1d(v)))}" for k, v in target.items())


def _steps(e: dict, ts: float) -> tuple[int, int]:
    on = int(round(float(e["t_ms"]) / ts))
    return on, on + max(1, int(round(float(e["dur_ms"]) / ts)))


def resolve(protocol: dict, neurons: pd.DataFrame, timestep_ms: float) -> dict:
    """Resolve targets to rows and times to steps; return the protocol with a
    `resolved` block added. Raises if a target matches nothing or a value is
    out of range."""
    dur = float(protocol.get("duration_ms", 1000.0))
    if not 0 < dur <= MAX_DURATION_MS:
        raise ValueError(f"duration_ms {dur} outside (0, {MAX_DURATION_MS:g}]")
    out = {"genotype": [], "events": []}
    for g in protocol.get("genotype", []):
        eff = g["effector"]
        if eff not in ("TNT", "Kir2.1"):
            raise ValueError(f"genotype effector {eff} not available (TNT, Kir2.1)")
        rows = resolve_target(g["target"], neurons)
        if rows.size == 0:
            raise ValueError(f"genotype target {g['target']} matches no neuron")
        r = {**g, "rows": rows.tolist(), "n": int(rows.size), "approximation": APPROX[eff],
             "label": g.get("label") or f"{eff} in {target_label(g['target'])}"}
        if eff == "Kir2.1":
            r["mv"] = float(g.get("mv", DEFAULT_MV[eff]))
        out["genotype"].append(r)
    for e in protocol.get("events", []):
        eff = e.get("effector", "current")
        if eff not in APPROX or eff in ("TNT", "Kir2.1"):
            raise ValueError(f"event effector {eff} not available")
        on, off = _steps(e, timestep_ms)
        r = {**e, "effector": eff, "on_step": on, "off_step": off, "approximation": APPROX[eff]}
        if eff == "world":
            bad = set(e.get("set", {})) - set(WORLD_FIELDS)
            if not e.get("set") or bad:
                raise ValueError(f"world event must set some of {WORLD_FIELDS}; got {sorted(e.get('set', {}))}")
            r["label"] = e.get("label") or "world: " + ", ".join(sorted(e["set"]))
            r["n"] = 0
        else:
            rows = resolve_target(e["target"], neurons)
            if rows.size == 0:
                raise ValueError(f"event target {e['target']} matches no neuron")
            r.update(rows=rows.tolist(), n=int(rows.size))
            if eff == "kick":
                r["rate_hz"] = float(e.get("rate_hz", 100.0))
                if not 0 < r["rate_hz"] <= 1000:
                    raise ValueError("kick rate_hz outside (0, 1000]")
                r["label"] = e.get("label") or f"kick {r['rate_hz']:g} Hz: {target_label(e['target'])}"
            else:
                r["mv"] = float(e.get("mv", DEFAULT_MV[eff]))
                if abs(r["mv"]) > 40:
                    raise ValueError("|mv| above 40")
                hz, width = float(e.get("pulse_hz", 0) or 0), e.get("pulse_ms")
                if hz > 0:
                    width = float(width if width is not None else 0.5 * 1000.0 / hz)
                    r.update(pulse_hz=hz, pulse_ms=width,
                             pulse_steps=(int(round(1000.0 / hz / timestep_ms)),
                                          max(1, int(round(width / timestep_ms)))))
                r["label"] = e.get("label") or f"{eff} {r['mv']:+g} mV: {target_label(e['target'])}"
        out["events"].append(r)
    w = protocol.get("record", {}).get("watch")
    out["watch"] = sorted(set(resolve_target(w, neurons).tolist())) if w else []
    return {**protocol, "resolved": out}


def is_control(protocol: dict | None) -> bool:
    return not protocol or (not protocol.get("events") and not protocol.get("genotype"))


class Stimulator:
    """Per-step external drive, Poisson kicks and world changes from resolved
    events. Call `world(step, org)` before Organism.sense, then `drive(step)` and
    `kick(step)` for Network.step."""

    def __init__(self, resolved: dict, n: int, seed: int, kick_mv: float | None):
        self.n = n
        self.cur = [(e["on_step"], e["off_step"], np.asarray(e["rows"], np.int64), e["mv"],
                     e.get("pulse_steps")) for e in resolved["events"] if e["effector"] in CURRENT_LIKE]
        self.tonic = np.zeros(n, np.float32)
        for g in resolved["genotype"]:
            if g["effector"] == "Kir2.1":
                self.tonic[np.asarray(g["rows"], np.int64)] += g["mv"]
        self.has_tonic = bool(self.tonic.any())
        self.kicks = [(e["on_step"], e["off_step"], np.asarray(e["rows"], np.int64), e["rate_hz"])
                      for e in resolved["events"] if e["effector"] == "kick"]
        if self.kicks and not kick_mv:
            raise ValueError("kick events need a profile with kick_mv")
        self.kick_mv = kick_mv
        self.rng = np.random.default_rng([int(seed), 2024])   # not the model's generator
        self.worlds = [e for e in resolved["events"] if e["effector"] == "world"]
        self._saved: dict[int, dict] = {}
        self.applied: dict[int, dict] = {}

    def drive(self, step: int) -> np.ndarray | None:
        active = [e for e in self.cur if e[0] <= step < e[1]
                  and (e[4] is None or (step - e[0]) % e[4][0] < e[4][1])]
        if not active and not self.has_tonic:
            return None
        v = self.tonic.copy()
        for _, _, rows, mv, _ in active:
            v[rows] += mv
        return v

    def kick(self, step: int, ts: float):
        hit = [rows[self.rng.random(rows.size) < hz * ts / 1000.0]
               for on, off, rows, hz in self.kicks if on <= step < off]
        if not hit:
            return None
        rows = np.concatenate(hit)
        return (rows, self.kick_mv) if rows.size else None

    def world(self, step: int, org) -> None:
        """Apply world events that start at this step and undo those that end."""
        from flyemu.extrasenses import FoodPatch
        from flyemu.world import OdourSource
        w = org.world
        for k, e in enumerate(self.worlds):
            if step == e["off_step"] and k in self._saved:
                for f, v in self._saved.pop(k).items():
                    setattr(w, f, v)
            if step != e["on_step"]:
                continue
            here = np.array(org.body.sim.mj_data.xpos[1], float)   # the fly's root body now
            self._saved[k] = {f: copy.deepcopy(getattr(w, f)) for f in e["set"]}
            applied = {}
            for f, v in e["set"].items():
                if f == "food":
                    v = [FoodPatch(center=np.array(here[:2] if p.get("at") == "fly" else p["center"], float),
                                   radius_mm=float(p["radius_mm"]), tastants=dict(p["tastants"])) for p in v]
                    applied[f] = [{"center": p.center.tolist(), "radius_mm": p.radius_mm, "tastants": p.tastants}
                                  for p in v]
                elif f == "odours":
                    v = [OdourSource(odour=s["odour"], peak=float(s["peak"]),
                                     sigma_mm=float(s.get("sigma_mm", 20.0)),
                                     position=here + np.asarray(s["offset_mm"], float) if "offset_mm" in s
                                     else np.asarray(s["position"], float)) for s in v]
                    applied[f] = [{"odour": s.odour, "position": s.position.tolist(), "peak": s.peak,
                                   "sigma_mm": s.sigma_mm} for s in v]
                elif f in ("wind_mm_s", "sound_dir"):
                    v = np.asarray(v, float)
                    applied[f] = v.tolist()
                else:
                    v = float(v)
                    applied[f] = v
                setattr(w, f, v)
            self.applied[k] = {"step": step, "fly_xyz": here.tolist(), "set": applied}
