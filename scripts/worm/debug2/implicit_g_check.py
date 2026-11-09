"""Check for brain.step's implicit conductance route (G_nS, GE_pA; wbrain2, 9 Nov 2026; weki's LGC-55 item 01:04).
A one-cell sub-brain (HSNL, noise off) gets a constant conductance from 0.5 s to the end through a dummy module:
    ipa  the old route: I_pA = g (E - V_start), held over the exchange step (explicit)
    g    the new route: G_nS = g, GE_pA = g E (NEURON integrates g V at every internal step)
    pp   a SensG with e = E placed directly (the reference for the new route's transcription)
Usage: python implicit_g_check.py <ipa|g|pp> <dt_ms> [g_nS] [secs]      -> runs/worm/wbrain2/implicit_g/<form>_<dt>.json
       python implicit_g_check.py score     (the night file's bars 2 and 3)
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbrain2/implicit_g"
CELL, E = "HSNL", -41.0          # E: weki's toy (LGC-55's reversal as egg_laying uses it)


def run(form, dt, g_nS=4.15, secs=3.0):
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu import mech
    d = types.ModuleType("dummy_g")
    d.MECHANISMS = [("dummy_g", "Test: a constant conductance onto one soma", "test", "on")]
    d.SPECS = []

    class Mech:
        def __init__(self, brain, params, toggles):
            self.i, self.n, self.b = brain.idx[CELL], len(brain.cell_names), brain
            if form == "pp":
                self.pp = brain.h.SensG(brain.soma[self.i](0.5))
                self.pp.e, self.pp.g = E, 0.0

        def reset(self):
            if form == "pp":
                self.pp.g = 0.0

        def step(self, ctx, dt_ms):
            g = g_nS if ctx.t_ms >= 500.0 else 0.0
            if form == "pp":
                self.pp.g = g * 1e-3
                return {}
            x = np.zeros(self.n)
            if form == "ipa":
                x[self.i] = g * (E - ctx.v[self.i])
                return {"I_pA": x}
            x[self.i] = g
            return {"G_nS": x, "GE_pA": x * E}

    d.Mech = Mech
    sys.modules["dummy_g"] = d
    mech.REGISTRY.append("dummy_g")
    from wormemu.brain import Brain
    b = Brain(cells=[CELL], toggles=dict(quantal_noise="off", channel_noise="off"))
    b.reset()
    n = int(round(secs * 1000.0 / dt))
    t, v = [], []
    for k in range(n):
        v.append(float(b.step(None, dt).v_mV[0]))
        t.append(b.t)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{form}_{dt:g}.json").write_text(json.dumps(dict(form=form, dt=dt, g_nS=g_nS, t=t, v=v)))
    print(form, dt, "last-second mean", np.mean(np.array(v)[np.array(t) > 1000 * (secs - 1)]), "min", min(v), "max", max(v))


def _alt(r):
    t, v = np.array(r["t"]), np.array(r["v"])
    dv = np.diff(v[t > 600.0])
    return float(np.mean(np.sign(dv[1:]) * np.sign(dv[:-1]) < 0))


def score():
    R = {p.stem: json.loads(p.read_text()) for p in OUT.glob("*.json")}
    g4, p4 = np.array(R["g_4"]["v"]), np.array(R["pp_4"]["v"])
    print("2. G route vs SensG at e: max |dV|", float(np.max(np.abs(g4 - p4))), "mV")
    for k in ("ipa_4", "g_4", "g_0.5"):
        r = R[k]
        t, v = np.array(r["t"]), np.array(r["v"])
        print(f"3. {k}: sign-flip fraction {_alt(r):.3f}, last-second mean {np.mean(v[t > t[-1] - 1000]):.3f} mV, "
              f"range {v[t > 600].min():.1f} to {v[t > 600].max():.1f} mV")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "score":
        score()
    else:
        run(a[0], float(a[1]), float(a[2]) if len(a) > 2 else 4.15, float(a[3]) if len(a) > 3 else 3.0)
