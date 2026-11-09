"""EXP-1 port check (wbody2, 9 Nov 2026; spec docs/worm/night/wbody2/exp1_port_spec.md, bars written there first).

Once DVB fires, does each int9 wave give one expulsion? DVB is driven by an SEClamp playing Jiang et al. 2022's spike
(rest -49.0, peak 26.3 mV, half-width 358.8 ms; a Gaussian, derived) 3 s after each int9 Ca peak, found causally with
the battery's rule (vitals.peaks on the mean of int9L and int9R, sampled at the battery's 20 Hz). DVB's own spike is
wbrain2's (Jiang 2022 port); this test does not use it. Diagnostic preparation: the DMP sub-brain with every organ.

Usage: python exp1_check.py TAG [form=brain|beg2003] [drive=on|off] [du=RANK] [secs=150] [ref=TAG] [rescore=1]
  -> runs/worm/wbody2/exp1_check_TAG.{json,npz}; ref=TAG compares this run's traces with that run's (bar 1).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbody2"
V_REST, V_PEAK, FWHM_MS = -49.0, 26.3, 358.8          # Jiang et al. 2022 Fig. 1 legend (DVB, n 5), measured
SIGMA_MS = FWHM_MS / (2.0 * np.sqrt(2.0 * np.log(2.0)))   # 152.4 ms, derived
DELAY_S = 3.0                                          # Jiang 2022 "about 3 s"; Wang et al. 2013 "about three seconds"
SETTLE_S, TAIL_S, SAMPLE_MS = 8.0, 10.0, 50


def main():
    tag = sys.argv[1]
    a = dict(x.split("=", 1) for x in sys.argv[2:])
    form, drive, secs = a.get("form", "brain"), a.get("drive", "on"), float(a.get("secs", 150))
    if a.get("rescore") == "1":                  # re-score a saved run (no simulation; synapses and wall_s not kept)
        res = dict(tag=tag, form=form, drive=drive, du=a.get("du"), secs=secs, rescored=True)
        res.update(score(np.load(OUT / f"exp1_check_{tag}.npz"), drive, secs))
        return write(tag, res)
    for p in ("src", "scripts/worm", "scripts/worm/wbody2"):
        sys.path.insert(0, str(ROOT / p))
    import at_ledger
    at_ledger.patch()
    from dmp_trace import DMP
    from enteric_probe import du_set
    from wormemu import brain as B
    from wormemu.fit import vitals
    spec = B.sample_worm(None)
    if "du" in a:
        spec.values.update(du_set(a["du"])["values"])
    tog = {} if form == "brain" else {"enteric_exp1": form}
    b = B.Brain(spec, toggles=tog, cells=DMP)
    b.reset()
    h = b.h
    m = next(x for x in b.mechs if type(x).__module__.endswith("organs_intestine"))
    syn = [dict(ec50_mM=w.ec50, hill=w.hill, erev_mV=w.erev, gmax_uS=w.gmax, tau_off_ms=w.tau_off,
                tau_des_ms=w.tau_des) for w in m.wsyn]
    jd = b.idx["DVB"]
    clamp = h.SEClamp(b.soma[jd](0.5))
    clamp.dur1, clamp.rs, clamp.amp1 = 1e9, 1e9, V_REST
    c9 = vitals.int9_columns()
    n_ms = int(secs * 1000)
    ts, x9, dvb, ev, ea, eca = [], [], [], [], [], []
    exp_t, spk_t, pk_t, onsets = [], [], [], []
    last_pk, prev_v = -1e9, None
    w0 = time.time()
    for k in range(n_ms):
        t = k / 1000.0
        if drive == "on":
            on = [tp for tp in spk_t if abs(t - tp) <= 3.0 * SIGMA_MS / 1000.0]
            if on:
                clamp.rs = 0.01
                clamp.amp1 = V_REST + (V_PEAK - V_REST) * np.exp(-0.5 * ((t - on[0]) * 1000.0 / SIGMA_MS) ** 2)
            else:
                clamp.rs = 1e9
        o = b.step(None, 1.0)
        mo = b.mech_out
        if o.expulsions:
            exp_t += [t] * int(o.expulsions)
        v0 = float(np.asarray(mo["enteric_v_mV"])[0])
        if prev_v is not None and prev_v < 0.0 <= v0:          # a mu_intL spike (upward 0 mV crossing)
            onsets.append(t)
        prev_v = v0
        if k % SAMPLE_MS == 0:
            ts.append(t)
            x9.append(float(np.mean(np.asarray(mo["intestine_ca_uM"])[c9])))
            dvb.append(float(o.v_mV[jd]))
            ev.append(np.asarray(mo["enteric_v_mV"], float).copy())
            ea.append(np.asarray(mo["enteric_activation"], float).copy())
            eca.append(np.asarray(mo["enteric_ca_mM"], float).copy())
            if len(x9) >= 3 and x9[-2] > vitals.CA_PEAK_UM and x9[-2] >= x9[-3] and x9[-2] > x9[-1] \
                    and ts[-2] - last_pk >= vitals.CA_PEAK_GAP_S:
                last_pk = ts[-2]
                pk_t.append(last_pk)
                spk_t.append(last_pk + DELAY_S)
    ts, ev, ea, eca = np.array(ts), np.array(ev), np.array(ea), np.array(eca)
    np.savez(OUT / f"exp1_check_{tag}.npz", t=ts, int9_ca=np.array(x9), dvb_v=np.array(dvb), enteric_v=ev,
             enteric_act=ea, enteric_ca=eca, expulsions_s=np.array(exp_t), mu_intL_spike_s=np.array(onsets),
             dvb_spike_peaks_s=np.array(spk_t if drive == "on" else []), int9_peaks_s=np.array(pk_t))
    res = dict(tag=tag, form=form, drive=drive, du=a.get("du"), secs=secs, synapses=syn, wall_s=time.time() - w0)
    res.update(score(np.load(OUT / f"exp1_check_{tag}.npz"), drive, secs))
    if "ref" in a:
        r = np.load(OUT / f"exp1_check_{a['ref']}.npz")
        z = np.load(OUT / f"exp1_check_{tag}.npz")
        same = {k: bool(np.array_equal(r[k], z[k])) for k in ("enteric_v", "dvb_v", "expulsions_s", "int9_ca")}
        res["bar1_identical_to_" + a["ref"]] = same
        res["bar1"] = "pass" if all(same.values()) else "fail"
    write(tag, res)


def score(z, drive, secs):
    """Spec bar 2 from a run's saved traces (z: the npz)."""
    ts, ea, eca = z["t"], z["enteric_act"], z["enteric_ca"]
    exp_t, onsets, spk_t = (z[k].tolist() for k in ("expulsions_s", "mu_intL_spike_s", "dvb_spike_peaks_s"))
    on_t = [tp - 3.0 * SIGMA_MS / 1000.0 for tp in spk_t if tp <= secs] if drive == "on" else []
    scored = [i for i, s in enumerate(on_t) if s >= SETTLE_S and secs - s >= TAIL_S]
    per = []
    for i in scored:
        lo, hi = on_t[i], (on_t[i + 1] if i + 1 < len(on_t) else secs)
        sel = (ts >= lo) & (ts < hi)
        per.append(dict(onset_s=lo, expulsions=sum(lo <= e < hi for e in exp_t),
                        act3_peak=float(ea[sel][:, :3].mean(axis=1).max()) if sel.any() else None,
                        ca_peak_mM=float(eca[sel].max()) if sel.any() else None,
                        mu_intL_spikes=sum(lo <= e < hi for e in onsets)))
    first = on_t[scored[0]] if scored else secs
    pre = sum(SETTLE_S <= e < first for e in exp_t)
    ok = drive == "on" and len(scored) >= 2 and all(p["expulsions"] == 1 for p in per) and pre == 0
    rest = (ts >= SETTLE_S) & (ts < first)
    return dict(int9_peaks_s=z["int9_peaks_s"].tolist() if "int9_peaks_s" in z else None,
                dvb_spike_peaks_s=spk_t, expulsions_s=exp_t, per_spike=per, expulsions_before_first_spike=pre,
                rest_act3_mean=float(ea[rest][:, :3].mean()) if rest.any() else None,
                rest_mu_intL_spikes_per_s=sum(SETTLE_S <= e < first for e in onsets) / max(first - SETTLE_S, 1e-9),
                dvb_v_max=float(np.max(z["dvb_v"])), bar2="pass" if ok else ("fail" if drive == "on" else "control"))


def write(tag, res):
    (OUT / f"exp1_check_{tag}.json").write_text(json.dumps(res, indent=1, default=lambda x: x.item()))
    print(json.dumps({k: res[k] for k in res if k not in ("synapses",)}, default=lambda x: x.item())[:3000])


if __name__ == "__main__":
    main()
