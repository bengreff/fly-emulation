"""Item 2 stage 2 probe (wbody2, 9 Nov 2026): why the ported EAT-2 route (ph_mc_route=eat2) makes no pump.
Diagnostic only: nothing here is adopted (class D if an in-range value passes; the default stays cook).

Measured first (pharynx_stage2_check.py, 00:41): under eat2 at the ledger's NMJ conductance per contact, each MC pulse
gives a 13-17 mV EPSP in pm5 (-65.4 to -48.4 mV), below pm5's threshold; the muscle alone needs 400 pA per pm5 cell for
40 ms to fire (200 pA reaches -43.7 mV and does not). The coupled pharynx rests near -65 mV, where Sherman & Harel's
CCA-1 is about 94 % inactivated (h_inf(-65) = 1 / (1 + exp(11 / 4)) = 0.06, derived), against the measured -73 mV
(Steger et al. 2005).

A  strength  ph_mc_route=eat2, the check's setup (40 pA x 30 ms MC pulses at 4 Hz, 3 s), nmj_strength_per_pair at 0.1,
             the ledger's 0.447, 1 and 2 nS (its range 0.1-2): pumps against the check's bar (>= 0.8 x pulses)
B  rest      MC not driven, cook, 0.5 s: pm4, pm5 and the marginal cells' V at 490 ms with (default) everything, (gaps)
             the neuron-pm gaps at 0, (syn) every organ chemical synapse onto pm and marginal cells at gmax 0, (5ht) the
             SER-7 current off, and (all) all three cut. With all cut, every cell must sit within 1 mV of the leak
             reversal, -73 mV (the sanity check of the probe itself)
Usage: python pharynx_stage2_probe.py  -> runs/worm/wbody2/pharynx_stage2_probe.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbody2"
HZ, MS, PA = 4.0, 30.0, 40.0
NMJ = [0.1, None, 1.0, 2.0]
CUTS = {"default": (), "gaps": ("gaps",), "syn": ("syn",), "5ht": ("5ht",), "all": ("gaps", "syn", "5ht")}


def one(cfg):
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm" / "wbody2"))
    import at_ledger
    at_ledger.patch()
    from wormemu import brain as B
    from wormemu.mech import organs_pharynx as P
    from pharynx_trace import PN
    cut = set(cfg.get("cut", ()))
    if "gaps" in cut:
        orig = B.Brain._gap

        def gap(self, a, b, g_uS, kind, *k, **kw):
            return orig(self, a, b, 0.0 if kind == "gap_pharynx_neuron" else g_uS, kind, *k, **kw)
        B.Brain._gap = gap
    spec = B.sample_worm(None)
    if cfg.get("nmj") is not None:
        spec.values["nmj_strength_per_pair"] = spec.values["nmj_strength_per_pair"] * 0.0 + cfg["nmj"]
    b = B.Brain(spec, toggles={"ph_mc_route": cfg["route"]}, cells=PN)
    ph = next(m for m in b.mechs if isinstance(m, P.Mech))
    if "syn" in cut:
        for pp in ph.wsyn:
            pp.gmax = 0.0
    if "5ht" in cut:
        ph._ser = None
    h = b.h
    tv = h.Vector().record(h._ref_t)
    rec = {n: h.Vector().record(ph.sec[n](0.5)._ref_v) for n in ph.names}
    inj = [b.idx["MCL"], b.idx["MCR"]]
    b.reset()
    secs = cfg.get("secs", 3.0)
    pumps = n_pulse = 0
    for k in range(int(secs * 1000)):
        b.extra_pA[:] = 0.0
        if cfg.get("mc") and k >= 500 and (k - 500) % (1000.0 / HZ) < MS:
            b.extra_pA[inj] = PA
            n_pulse += (k - 500) % (1000.0 / HZ) == 0
        pumps += int(b.step(None, 1.0).pumps)
    t = np.array(tv)
    V = {n: np.array(x) for n, x in rec.items()}
    i = int(np.searchsorted(t, 490.0))
    grp = {g: [n for n in ph.names if n.startswith(g)] for g in ("pm4", "pm5", "pm7", "mc2")}
    out = dict(cfg=cfg, pulses=int(n_pulse), pumps=pumps,
               v490={g: round(float(np.mean([V[n][i] for n in ns])), 2) for g, ns in grp.items()})
    if cfg.get("mc"):
        late = t >= 500.0
        out.update(pm5_max=round(float(max(V[n][late].max() for n in grp["pm5"])), 2),
                   pm4_max=round(float(max(V[n][late].max() for n in grp["pm4"])), 2),
                   pm4_median=round(float(np.median(np.mean([V[n][late] for n in grp["pm4"]], 0))), 2))
    return out


def sub(cfg):
    r = subprocess.run([sys.executable, __file__, "one", json.dumps(cfg)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "one":
        print(json.dumps(one(json.loads(sys.argv[2]))))
        return
    t0 = time.time()
    a = []
    for x in NMJ:
        a.append(sub(dict(route="eat2", mc=True, nmj=x)))
        print(a[-1], flush=True)
    b = {}
    for k, c in CUTS.items():
        b[k] = sub(dict(route="cook", mc=False, cut=list(c), secs=0.5))
        print(k, b[k]["v490"], flush=True)
    res = dict(question=__doc__.split("A  strength")[0].strip(), A=a, B=b,
               A_passing=[r["cfg"]["nmj"] for r in a if r["pumps"] >= 0.8 * r["pulses"]],
               B_sanity_pass=all(abs(v + 73.0) < 1.0 for v in b["all"]["v490"].values()), wall_s=time.time() - t0)
    (OUT / "pharynx_stage2_probe.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("question", "A", "B")}))


if __name__ == "__main__":
    main()
