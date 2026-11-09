"""The EKI's run loop on disk (weki, 8 Nov 2026; FIT_GENERAL.md sections 3, 9 and 10). NO FIT: tested on toy maps
(tests/test_worm_fit_driver.py); the worm's forward (a member's battery from its z) is not written here, and no run
starts until the gate passes and Ben says go.

backhouse reboots and the Mac sleeps, so every step is on disk and a run resumes where it stopped:

    root/state_<k>.npz    the EKI before iteration k's forward runs: z, t, steps, the generator state, the per-iteration
                          log (written atomically: a stall mid-write leaves the previous state)
    root/it<k>/m<j>.json  member j's forward result {"g": [...], "ok": bool}, written atomically by the member's process
    root/STOP             why the run ended (one of the stops below), written last

A member result that exists is never re-run, so a resume repeats only the members that had not finished, and the
generator state is restored, so an interrupted run ends bit-identical to an uninterrupted one.

Stops (FIT_GENERAL.md section 9, first to fire): (a) the controller's time reaches 1; (b) max_iter iterations (30,
guessed there); (c) a plateau: the mean misfit per observation over the admissible members improved by under 1 %
over the last 5 iterations, after at least 10; (d) rejection (section 3): more than half the members failed in each of
the last 3 iterations. (b) or (c) with t < 1 is reported as model error, never patched.

    d = Driver(root, z0, y, gamma, forward, processes=3)   # forward(z_row) -> (g, ok); a top-level function
    d.run()
    Z, G = d.pairs()                                         # every (z, G(z)) for ces.Emulator
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from wormemu.fit.eki import EKI
from wormemu.fit import ces

STOPS = {"max_iter": 30, "plateau_n": 5, "plateau_min_iter": 10, "plateau_rel": 0.01, "reject_n": 3,
         "reject_frac": 0.5}


def _atomic_write(path: Path, text: str):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def run_member(forward, z, path):
    """One member's forward run, its result written atomically (the unit a process pool runs)."""
    g, ok = forward(np.asarray(z, float))
    _atomic_write(Path(path), json.dumps({"g": [float(x) for x in np.ravel(g)], "ok": bool(ok)}))


class Driver:
    def __init__(self, root, z0, y, gamma, forward, processes=1, admissible=None, stops=None, **eki_kw):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.forward, self.processes, self.admissible = forward, int(processes), admissible
        self.stops = {**STOPS, **(stops or {})}
        self.e = EKI(z0, y, gamma, **eki_kw)
        self.log = []                                    # per iteration: t, dt, phi per observation, n_ok
        ks = sorted(int(p.stem.split("_")[1]) for p in self.root.glob("state_*.npz"))
        if ks:
            self.k = ks[-1]
            self._load(self.k)
        else:
            self.k = 0
            self._save()

    def _save(self):
        e = self.e
        tmp = self.root / f"tmp_state_{self.k}.npz"     # not matched by the resume glob
        np.savez(tmp, z=e.z, t=e.t, dts=np.array(e.dts), rng=json.dumps(e.rng.bit_generator.state),
                 log=json.dumps(self.log), y=e.y, gamma=e.gamma)
        os.replace(tmp, self.root / f"state_{self.k}.npz")

    def _load(self, k):
        s = np.load(self.root / f"state_{k}.npz")
        if not (np.array_equal(s["y"], self.e.y) and np.array_equal(s["gamma"], self.e.gamma)):
            raise ValueError(f"{self.root} holds a run on other data (y or gamma differ): not resumed")
        self.e.z, self.e.t, self.e.dts = s["z"].copy(), float(s["t"]), list(s["dts"])
        self.e.rng.bit_generator.state = json.loads(str(s["rng"]))
        self.log = json.loads(str(s["log"]))

    def forward_all(self):
        """Run every member of the current iteration that has no result yet; return (G, ok) for all members."""
        d = self.root / f"it{self.k}"
        d.mkdir(exist_ok=True)
        todo = [j for j in range(len(self.e.z)) if not (d / f"m{j}.json").exists()]
        if self.processes > 1 and len(todo) > 1:
            with ProcessPoolExecutor(self.processes) as ex:
                for f in [ex.submit(run_member, self.forward, self.e.z[j], d / f"m{j}.json") for j in todo]:
                    f.result()
        else:
            for j in todo:
                run_member(self.forward, self.e.z[j], d / f"m{j}.json")
        res = [json.loads((d / f"m{j}.json").read_text()) for j in range(len(self.e.z))]
        return np.array([r["g"] for r in res], float), np.array([r["ok"] for r in res], bool)

    def stop_reason(self):
        s, lg = self.stops, self.log
        if self.e.done:
            return "t reached 1"
        if self.k >= s["max_iter"]:
            return f"{s['max_iter']} iterations with t = {self.e.t:.3f} < 1: model error at the data's noise"
        n = s["plateau_n"]
        if len(lg) >= max(s["plateau_min_iter"], n + 1):
            old, new = lg[-n - 1]["phi_per_obs"], lg[-1]["phi_per_obs"]
            if old - new < s["plateau_rel"] * old:
                return f"plateau (misfit per observation {old:.4g} -> {new:.4g} over {n} iterations) with t = " \
                       f"{self.e.t:.3f} < 1: model error at the data's noise"
        r = s["reject_n"]
        if len(lg) >= r and all(x["n_ok"] < (1.0 - s["reject_frac"]) * x["J"] for x in lg[-r:]):
            return f"more than half the members rejected in each of the last {r} iterations"
        return None

    def run(self):
        while (why := self.stop_reason()) is None:
            G, ok = self.forward_all()
            if (ok & np.isfinite(G).all(1)).sum() < 2:
                why = f"fewer than 2 of {len(G)} members ran in iteration {self.k}: no covariance"
                break
            self.e.update(G, ok, admissible=self.admissible)
            h = self.e.history[-1]
            self.log.append({"k": self.k, "t": self.e.t, "dt": h["dt"], "phi_per_obs": h["phi_mean"] / G.shape[1],
                             "n_ok": h["n_ok"], "J": len(G), "n_redrawn": h["n_redrawn"]})
            self.k += 1
            self._save()
        else:
            self.forward_all()                           # the final ensemble's runs: the last calibrate pairs
        _atomic_write(self.root / "STOP", why + "\n")
        return why

    def pairs(self):
        """Every (z, G(z)) the run made, failed members left out (ces.pairs)."""
        hist = []
        for k in range(self.k + 1):
            d = self.root / f"it{k}"
            z = np.load(self.root / f"state_{k}.npz")["z"]
            if not d.exists() or not all((d / f"m{j}.json").exists() for j in range(len(z))):
                continue
            res = [json.loads((d / f"m{j}.json").read_text()) for j in range(len(z))]
            hist.append((z, np.array([r["g"] for r in res], float), np.array([r["ok"] for r in res], bool)))
        return ces.pairs(hist)
