"""Item 2 stage 2 check (wbody2, 9 Nov 2026): MC -> pharyngeal muscle through EAT-2 (spec: docs/worm/night/wbody2/
pharynx_stage2_spec.md; sources lit_mc_nmj.md, lit_mc_site.md).

Toggle ph_mc_route (organs_pharynx): cook (nested, the code before the port: MC's Cook synapses onto the mc2 marginal
cells only), eat2 (MC's Cook contacts onto each mc2 cell placed instead on the pm5 cells that mc2 cell borders, as
nicotinic synapses at the ledger's NMJ conductance per contact), both (half the contacts each way).

Bars (written before running the ported code; the reference saved on the unported code first):
    1 neutral    ph_mc_route=cook, the setup below: every pharyngeal muscle and marginal cell's V at every NEURON step
                 identical to the unported code's (max |dV| = 0)
    2 muscle     MC not driven, default toggles: a 40 ms square current into the three pm5 cells every 1450 ms (Sherman &
                 Harel 2024's input, at the metacorpus-isthmus border), 3 inputs from 0.5 s; at the smallest of 25, 50,
                 100, 200, 400, 800 pA per cell at which pm5 fires (V above -20 mV), pm4 fires exactly one AP (an upward
                 crossing of -20 mV) in each input's 1450 ms window
    3 effect     ph_mc_route=eat2, the setup below: pumps >= 0.8 x MC pulses
    4 latency    in bar 3's run, the median over pulses of the time from MCL's soma crossing its synapses' release
                 threshold (Vth, upward) to the peak of the model EPG (mean dV/dt over the 20 muscles) in the next 100 ms:
                 inside 6.7 +- 1.7 ms (Steger et al. 2005 Table 1, wild type EPSP to E spike 6.7 +- 0.3 ms SEM, n = 8
                 animals; SD = 0.3 x sqrt(8) = 0.85 ms, derived; +- 2 SD)
    5 eat-2 null ph_mc_route=eat2 with the EAT-2 synapses' conductance set to 0: every pm's V within 1 mV of the same null
                 with MC not driven, at every NEURON step (Steger et al. 2005: eat-2 mutants have no EPSPs). (00:42: the
                 first run's control had EAT-2 at full conductance, so it measured EAT-2's own transmission at rest, not
                 an MC-evoked response in the null; corrected to the null's own undriven run, the bar unchanged)
Reported, no bar: the same run under both and under cook (pumps, pm4 and pm5 peak V, latency).
Setup (the coupling probe's): the pharyngeal sub-brain (pharynx_trace.PN), ledger values (at_ledger), template gap
(ph_gap_nS_per_contact 5 nS) and marginal-cell area (500 um2), 40 pA x 30 ms pulses into MCL and MCR at 4 Hz from 0.5 s,
3 bio s at 1 ms brain steps. One subprocess per run (a fresh NEURON).
Validity: MC's 30 ms injected pulse is not its natural spike, so the latency includes how fast the pulse takes MC past
the release threshold.
Usage: python pharynx_stage2_check.py ref   (on the unported code)  /  python pharynx_stage2_check.py
       -> runs/worm/wbody2/pharynx_stage2_check.json
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
SECS, HZ, MS, PA = 3.0, 4.0, 30.0, 40.0
PM5_EVERY, PM5_MS, PM5_N = 1450.0, 40.0, 3
PM5_AMPS = [25.0, 50.0, 100.0, 200.0, 400.0, 800.0]
LAT_LO, LAT_HI = 6.7 - 2 * 0.3 * 8 ** 0.5, 6.7 + 2 * 0.3 * 8 ** 0.5


def one(cfg):
    """One run in this process. cfg: route (None = no toggle, the unported code), mc (drive MC), null (EAT-2 gmax 0),
    pm5_pA (drive pm5 instead), tag (npz name). Saves the traces, returns a summary."""
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm"))
    sys.path.insert(0, str(ROOT / "scripts" / "worm" / "wbody2"))
    import at_ledger
    at_ledger.patch()
    from wormemu import brain as B
    from wormemu.mech import organs_pharynx as P
    from pharynx_trace import PN
    spec = B.sample_worm(None)
    tg = {} if cfg["route"] is None else {"ph_mc_route": cfg["route"]}
    b = B.Brain(spec, toggles=tg, cells=PN)
    ph = next(m for m in b.mechs if isinstance(m, P.Mech))
    if cfg.get("null"):
        for pp in ph.eat2_syn:
            pp.gmax = 0.0
    h = b.h
    tv = h.Vector().record(h._ref_t)
    rec = {n: h.Vector().record(ph.sec[n](0.5)._ref_v) for n in ph.names}
    vmc = h.Vector().record(b.soma[b.idx["MCL"]](0.5)._ref_v)
    vth = float(next((pp.Vth for pp, pre, *_ in b.wsyn if pre == b.idx["MCL"]), -20.0))
    inj = [b.idx["MCL"], b.idx["MCR"]]
    pm5 = [n for n in P.PHARYNX_MUSCLES if n.startswith("pm5")]
    clamps = []                    # the pm5 drive: own IClamps, so the 5-HT current on ph.stim is left alone
    for k in range(PM5_N if cfg.get("pm5_pA") is not None else 0):
        for n in pm5:
            c = h.IClamp(ph.sec[n](0.5))
            c.delay, c.dur, c.amp = 500.0 + k * PM5_EVERY, PM5_MS, cfg["pm5_pA"] / 1000.0
            clamps.append(c)
    b.reset()
    secs = SECS if cfg.get("pm5_pA") is None else (500.0 + PM5_N * PM5_EVERY) / 1000.0
    pumps, n_pulse = 0, 0
    for k in range(int(secs * 1000)):
        b.extra_pA[:] = 0.0
        if cfg.get("mc") and k >= 500 and (k - 500) % (1000.0 / HZ) < MS:
            b.extra_pA[inj] = PA
            n_pulse += (k - 500) % (1000.0 / HZ) == 0
        o = b.step(None, 1.0)
        pumps += int(o.pumps)
    t = np.array(tv)
    V = np.array([np.array(rec[n]) for n in ph.names])
    np.savez(OUT / f"stage2_{cfg['tag']}.npz", t=t, V=V, vmc=np.array(vmc), names=np.array(ph.names))
    pm = [ph.names.index(n) for n in P.PHARYNX_MUSCLES]
    i4 = [ph.names.index(n) for n in P.PHARYNX_MUSCLES if n.startswith("pm4")]
    i5 = [ph.names.index(n) for n in pm5]
    late = t >= 500.0
    out = dict(cfg=cfg, pulses=int(n_pulse), pumps=pumps, n_eat2=len(ph.eat2_syn) if hasattr(ph, "eat2_syn") else None,
               pm4_v_max=float(V[i4][:, late].max()), pm5_v_max=float(V[i5][:, late].max()),
               MCL_max=float(np.array(vmc)[late].max()), vth=vth)
    if cfg.get("mc"):
        out["latency_ms"] = latency(t, np.array(vmc), V[pm], vth)
    if cfg.get("pm5_pA") is not None:
        out["pm4_aps_per_input"] = aps_per_input(t, V[i4].mean(0))
        out["pm5_fired"] = bool(V[i5][:, late].max() > -20.0)
    return out


def latency(t, vmc, Vpm, vth):
    """Per MC release onset (MCL crossing vth upward): ms to the EPG peak (mean dV/dt over the muscles) within 100 ms."""
    epg = np.diff(Vpm, axis=1).mean(0) / np.diff(t)
    up = np.where((vmc[:-1] < vth) & (vmc[1:] >= vth))[0]
    out = []
    for i in up:
        w = (t[1:] > t[i]) & (t[1:] <= t[i] + 100.0)
        if w.any():
            j = np.where(w)[0][int(np.argmax(epg[w]))]
            out.append(round(float(t[j + 1] - t[i]), 3))
    return out


def aps_per_input(t, v4):
    up = np.where((v4[:-1] < -20.0) & (v4[1:] >= -20.0))[0]
    return [int(((t[up] >= 500.0 + k * PM5_EVERY) & (t[up] < 500.0 + (k + 1) * PM5_EVERY)).sum()) for k in range(PM5_N)]


def sub(cfg):
    r = subprocess.run([sys.executable, __file__, "one", json.dumps(cfg)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "one":
        print(json.dumps(one(json.loads(sys.argv[2]))))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if len(sys.argv) >= 2 and sys.argv[1] == "ref":
        print(json.dumps(sub(dict(route=None, mc=True, tag="ref"))))
        return
    res = {"bar": __doc__.split("Bars (written before running")[1].split("Reported, no bar")[0].strip()}
    r1 = sub(dict(route="cook", mc=True, tag="cook"))
    a, b_ = np.load(OUT / "stage2_ref.npz"), np.load(OUT / "stage2_cook.npz")
    same = a["V"].shape == b_["V"].shape and np.array_equal(a["t"], b_["t"])
    d = float(np.max(np.abs(a["V"] - b_["V"]))) if same else float("inf")
    res["1_neutral"] = dict(max_abs_dV_mV=d, pass_=same and d == 0.0, run=r1)
    rows = []
    for amp in PM5_AMPS:
        rows.append(sub(dict(route="cook", mc=False, pm5_pA=amp, tag=f"pm5_{amp:g}")))
        print(rows[-1], flush=True)
        if rows[-1]["pm5_fired"]:
            break
    fired = rows[-1] if rows[-1]["pm5_fired"] else None
    res["2_muscle"] = dict(rows=rows, amp_pA=fired["cfg"]["pm5_pA"] if fired else None,
                           pass_=bool(fired and fired["pm4_aps_per_input"] == [1] * PM5_N))
    r3 = sub(dict(route="eat2", mc=True, tag="eat2"))
    res["3_effect"] = dict(run=r3, pass_=r3["pumps"] >= 0.8 * r3["pulses"])
    lat = r3["latency_ms"]
    med = float(np.median(lat)) if lat else float("nan")
    res["4_latency"] = dict(median_ms=med, range_ms=[round(LAT_LO, 3), round(LAT_HI, 3)], pass_=LAT_LO <= med <= LAT_HI)
    sub(dict(route="eat2", mc=False, null=True, tag="eat2_quiet"))
    r5 = sub(dict(route="eat2", mc=True, null=True, tag="eat2_null"))
    q, z = np.load(OUT / "stage2_eat2_quiet.npz"), np.load(OUT / "stage2_eat2_null.npz")
    names = list(q["names"])
    pm = [names.index(n) for n in names if n.startswith("pm")]
    dn = float(np.max(np.abs(z["V"][pm] - q["V"][pm])))
    res["5_eat2_null"] = dict(max_abs_dV_pm_mV=dn, pass_=dn <= 1.0, run=r5)
    res["report"] = dict(both=sub(dict(route="both", mc=True, tag="both")), cook=r1)
    res["wall_s"] = time.time() - t0
    (OUT / "pharynx_stage2_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "bar"}, indent=1))


if __name__ == "__main__":
    main()
