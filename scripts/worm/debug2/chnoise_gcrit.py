"""How large is channel noise's explicit conductance? (wbrain2, 9 Nov 2026; weki's inbox item 01:45.) mech/noise.Channel
injects -dG (V_start - E) per population, held over the exchange step, so its slope is -G with G the cell's summed
step-mean fluctuation (nS, signed). This runs the brain (default toggles) at a 4 ms exchange step and records G per
neuron per step, with the step's own draws (a copy of Channel.step that also returns G; the module is not edited).
Usage: python chnoise_gcrit.py [template|top] [seconds] [dt_ms]     (top: every chnoise_*_pS at its range top)
Output: runs/worm/wbrain2/chnoise_gcrit_<form>.json
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
RIS_4p5 = 0.79      # nS, weki's lowest measured threshold (RIS, 4.5 ms; scripts/worm/fit/explicit_gcrit.py)
WEKI = {"HSNL": 1.22, "RIS": 0.79, "AWAL": 1.79, "ASHL": 1.27, "AFDL": 1.34, "AVAL": 1.84}   # nS at 4.5 ms


def main(form="template", secs=5.0, dt=4.0):
    sys.path.insert(0, str(ROOT / "src"))
    from wormemu.brain import Brain, sample_worm
    from wormemu.mech import noise as NZ
    spec = sample_worm(None)
    if form == "top":
        spec = copy.copy(spec)
        spec.values = dict(spec.values)
        for s in NZ.SPECS:
            if s.id.startswith("chnoise_") and s.id.endswith("_pS"):
                spec.values[s.id] = s.hi
    rec = []

    def step(self, ctx, dt_ms):                   # Channel.step, verbatim, plus G
        if not self.groups:
            return {}
        I, G = np.zeros(self.n), np.zeros(self.n)
        for g in self.groups:
            gmax = self._read(g["gb"]) * g["area"]
            dG = np.zeros(len(g["cells"]))
            for sb in g["subs"]:
                x, tau = self.gates(g, sb)
                W, r = NZ.weights(x, tau, sb["pw"], sb["J"], sb["binom"])
                s2 = (sb["w"] * gmax * g["gam"])[:, None] * W
                z0, z1, z2 = (self.rng.standard_normal(W.shape) for _ in range(3))
                if sb["y"] is None:
                    sb["y"] = np.sqrt(s2) * z0
                sb["y"], m = NZ.ou_step(sb["y"], s2, 1.0 / r, dt_ms, z1, z2)
                dG += m.sum(axis=1)
            I[g["cells"]] -= dG * (ctx.v[g["cells"]] - g["E"])
            G[g["cells"]] += dG
        rec.append(G)
        nn = ~np.asarray(self.brain.is_muscle, bool)
        return {"I_pA": I, "out": {NZ.C: dict(I_rms_pA=float(np.sqrt(np.mean(I[nn] ** 2))),
                                              channels_median=float(np.median(self.n_channels[nn])))}}

    NZ.Channel.step = step
    t0 = time.time()
    b = Brain(spec)
    b.reset()
    n = int(round(secs * 1000.0 / dt))
    vs = []
    for _ in range(n):
        vs.append(np.array(b.step(None, dt).v_mV, float))
    G, V = np.array(rec), np.array(vs)
    nn = np.flatnonzero(~np.asarray(b.is_muscle, bool))
    names = [b.cell_names[i] for i in nn]
    Gn = G[:, nn]
    mx = Gn.max(axis=0)
    order = np.argsort(-mx)
    alt = np.mean(np.sign(np.diff(V[:, nn], axis=0))[1:] * np.sign(np.diff(V[:, nn], axis=0))[:-1] < 0, axis=0)
    out = dict(form=form, secs=secs, dt_ms=dt, steps=n, wall_s=round(time.time() - t0, 1),
               max_G_nS=float(mx.max()), min_G_nS=float(Gn.min()), sd_G_nS_median=float(np.median(Gn.std(axis=0))),
               p999_G_nS=float(np.percentile(Gn, 99.9)), cells_over_0p79=int((mx > RIS_4p5).sum()),
               steps_over_0p79=int((Gn > RIS_4p5).sum()), top10=[(names[i], round(float(mx[i]), 4)) for i in order[:10]],
               weki_cells={c: dict(max_G=round(float(mx[names.index(c)]), 4), thr=t) for c, t in WEKI.items()
                           if c in names},
               max_alternation_fraction=float(alt.max()), alternating_cells=[names[i] for i in np.flatnonzero(alt > 0.9)])
    p = ROOT / f"runs/worm/wbrain2/chnoise_gcrit_{form}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else "template", float(a[1]) if len(a) > 1 else 5.0, float(a[2]) if len(a) > 2 else 4.0)
