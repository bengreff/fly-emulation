"""The EKI vector and the worm it builds (weki, 9 Nov 2026; FIT_GENERAL.md sections 1-3). NO FIT: the bridge between
params.Theta's numbers and the z coordinates eki.EKI and fit.driver move, the joint-constraint check, the prior
ensemble, and the battery forward a member runs. Nothing here runs until the gate passes and Ben says go.

    v = Vector()                       # Theta's log and logit numbers (section 1)
    z0, rate = v.prior(128, seed=20261109)
    spec = v.spec(z0[0])               # the template worm with the member's numbers set
    g, ok = battery_forward(z0[0], k, obs)

The member is the template worm (sample_worm(None)) with its vector numbers set; every number outside the vector
stays at its template: the 15 bernoulli syn_inhibitory[cell] rows (section 6) and everything params.Theta leaves out,
which since main 27f7276 includes the experiment settings (params.SETTINGS: the scene_* plume shapes and the imaging
noise, fixed per experiment). Prior draws take the vector's numbers from
sample_worm(s), which draws each from its ledger prior in natural units (uniform or log-uniform on [bio_min, bio_max]),
and map them to z; a draw is checked as the member it builds (template base plus its numbers), not as sample_worm(s).

The forward runs each battery condition as `python -m wormemu.fit.vitals run COND SECONDS DIR --theta=FILE
--noise-seed=N` in its own process (NEURON keeps every cell it builds). N = noise_seed("battery_" + COND, k): one noise
seed per experiment per iteration, shared by every member (section 7's common random numbers), through wbrain2's
Experiment.noise_seed (main 1d1206b, 9 Nov). k None keeps the template's noise (the worm seed's, as before).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
RANGES = ROOT / "scripts" / "worm" / "ranges"
# signs with a bar that a 200 bio-s template run produces (FIT_GENERAL section 3, Ben to confirm item 5): dmp_period_s
# (no defecation on the template), egg_inactive_min and egg_intra_s (1800 bio-s each) are left out
BATTERY_IDS = ("rest_AWA", "pc3_frac", "gcamp_range", "pump_hz", "pump_hz_off", "bwm_rest_mV", "bwm_spike_hz")
CONDS = ("food", "nofood")


def _load(name):
    spec = importlib.util.spec_from_file_location(f"_weki_{name}", RANGES / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path[:0] = [str(RANGES)]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(RANGES))
    return mod


@lru_cache(maxsize=1)
def _checker():
    """(joint, default_breaks, ledger, constraints): the range work's checker, read-only (scripts/worm/ranges)."""
    from bioemu import ledger
    from wormemu.brain import MODEL
    joint = _load("joint")
    led = ledger.load(MODEL)
    return joint, _load("sample").default_breaks, led, joint.constraints(led)


class Vector:
    def __init__(self, theta=None):
        from wormemu import params
        from wormemu.brain import sample_worm
        self.T = T = params.Theta() if theta is None else theta
        names = [(str(i), str(p)) for i, p in zip(T.ids, T.table.pid)]
        fixed = np.array([any(params.setting(n) for n in ip) for ip in names])   # Theta drops them; kept as a guard
        out = ~np.isin(T.kind, ("log", "logit")) | fixed
        self.keep = np.flatnonzero(~out)
        self.ids = [T.ids[i] for i in self.keep]
        self.p = len(self.keep)
        self.base_spec = sample_worm(None)
        self.base = T.get(self.base_spec)                # the template's numbers, also those outside the vector

    def values(self, z):
        """Theta's full vector for the member z: its numbers set, the rest at the template."""
        z = np.asarray(z, float)
        assert z.shape == (self.p,), z.shape
        zf = self.T.to_z(self.base)
        zf[self.keep] = z
        x = self.base.copy()
        x[self.keep] = self.T.from_z(zf)[self.keep]
        return x

    def z(self, x):
        """The member's z from Theta's full vector (natural units)."""
        return self.T.to_z(np.asarray(x, float))[self.keep]

    def theta(self, z) -> dict:
        """{id: value} of the vector's numbers, the form vitals.run and datamodel.simulate take (no element ids)."""
        return {i: float(v) for i, v in zip(self.ids, self.values(z)[self.keep])}

    def spec(self, z):
        return self.T.set(self.base_spec, self.values(z))

    def broken(self, z) -> list[str]:
        """The hard constraints the member breaks, as the default worm feels them (section 2; [] = admissible)."""
        joint, breaks, led, cons = _checker()
        return breaks(joint.check(self.spec(z).values, led, cons), led)

    def admissible(self, z) -> bool:
        return not self.broken(z)

    def prior(self, J: int, seed: int, tries: int = 1000):
        """J admissible members drawn from the ledger priors (section 2: reject and redraw, up to `tries` per member).
        Returns (z0 [J x p], acceptance rate); stops if the rate is under 1 % (the box and the constraints disagree)."""
        from wormemu.brain import sample_worm
        rng = np.random.default_rng(seed)
        z0, n = [], 0
        for j in range(J):
            for _ in range(tries):
                n += 1
                z = self.z(self.T.get(sample_worm(int(rng.integers(2 ** 31)))))
                if self.admissible(z):
                    z0.append(z)
                    break
            else:
                raise RuntimeError(f"member {j}: no admissible draw in {tries}")
            if n >= 100 and len(z0) / n < 0.01:
                raise RuntimeError(f"acceptance {len(z0)}/{n} under 1 %: the box and the constraints disagree")
        return np.array(z0), J / n


def targets(ids=BATTERY_IDS, conds=CONDS):
    """(names, y, sigma) of the battery observations the forward returns, in its order (vitals.observations)."""
    from wormemu.fit import vitals
    names, _, y, sig = vitals.observations({c: {} for c in conds}, ids=ids)
    return names, y, sig


def noise_seed(exp_id: str, k) -> int | None:
    """The run's noise seed for experiment exp_id at iteration k (section 7): a stable hash (Python's hash() of a str
    changes per process), in [1, 2**31 - 1] so it never meets the template's 0. None for k None."""
    if k is None:
        return None
    return int(hashlib.sha256(f"{exp_id}/{int(k)}".encode()).hexdigest()[:8], 16) % (2 ** 31 - 2) + 1


def battery_forward(z, k, obs, seconds: float = 200.0, ids=BATTERY_IDS, conds=CONDS, workdir=None, python=None):
    """One member's battery (FIT_GENERAL section 3): each condition a fresh `vitals run` process on the member's worm.
    Returns (g, ok): g the observations `obs` (indices into targets(); None = all), NaN where a sign is not produced;
    ok False if any run is unphysical or fails. k (the iteration) sets each condition's noise seed (noise_seed)."""
    from wormemu.fit import vitals
    v = _vector()
    py = python or sys.executable
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    with tempfile.TemporaryDirectory(prefix="weki_fwd_", dir=workdir) as d:
        d = Path(d)
        (d / "theta.json").write_text(json.dumps(v.theta(z)))
        results, ok = {}, True
        for c in conds:
            ns = noise_seed(f"battery_{c}", k)
            cmd = [py, "-m", "wormemu.fit.vitals", "run", c, str(seconds), str(d), f"--theta={d / 'theta.json'}"]
            p = subprocess.run(cmd + ([] if ns is None else [f"--noise-seed={ns}"]), env=env, capture_output=True,
                               text=True)
            f = d / f"{c}.json"
            if p.returncode != 0 or not f.exists():
                ok, results[c] = False, {}
                continue
            results[c] = json.loads(f.read_text())
            ok &= bool(results[c]["physicality"]["physical"])
    _, g, _, _ = vitals.observations(results, ids=ids)
    return (g if obs is None else g[np.asarray(obs, int)]), ok      # a NaN sign fails the member in the driver


@lru_cache(maxsize=1)
def _vector():
    return Vector()
