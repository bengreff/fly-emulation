"""Row 13 unit check (bar in docs/worm/night/2026-11-06_worgans.md, written before this ran): one isolated
Sherman & Harel pharyngeal-muscle compartment, a 40 ms step at 1.1 x the smallest firing amplitude, dt 0.1 and 0.5 ms,
against S&H Table 3 (TB intracellular recordings).
    PYTHONPATH=src .venv/bin/python scripts/worm/organs/check_pharynx_sh.py"""
import json
import sys

from neuron import h

from wormemu.mech import organs_nrn, organs_pharynx as P

organs_nrn.load_organ_mods(h)
q = P.defaults()
BAR = dict(rest=(-74.0, -72.0), peak=(31.0, 37.0), duration=(100.0, 250.0), plateau=(20.0, 30.0), undershoot=(-200, -67))
PASS_KEYS = ("rest", "peak", "duration")


def fires(amp, dt):
    t, v, _ = P.ap_protocol(h, q, amp, dt=dt, t_end=400.0)
    return v.max() > 0.0


res = {}
for dt in (0.1, 0.5):
    lo, hi = 0.0, 200.0
    assert fires(hi, dt) and not fires(lo, dt)
    while hi - lo > 1.0:
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if fires(mid, dt) else (mid, hi)
    amp = 1.1 * hi
    t, v, ca = P.ap_protocol(h, q, amp, dt=dt)
    f = P.ap_features(t, v)
    f.update(threshold_pA=hi, amp_pA=amp, ca_core_peak_uM=float(ca.max() * 1e6))
    f["in_range"] = {k: bool(BAR[k][0] <= f[k] <= BAR[k][1]) for k in BAR}
    f["pass"] = all(f["in_range"][k] for k in PASS_KEYS)
    res[f"dt{dt}"] = f
    print(f"dt {dt}: " + ", ".join(f"{k} {f[k]:.2f}" for k in ("threshold_pA", "amp_pA", "rest", "peak", "t_peak",
          "duration", "plateau", "undershoot", "upstroke", "ca_core_peak_uM")), "| in range", f["in_range"],
          "| PASS" if f["pass"] else "| FAIL")
print("overall", "PASS" if all(r["pass"] for r in res.values()) else "FAIL")
if len(sys.argv) > 1:
    json.dump(res, open(sys.argv[1], "w"), indent=1)
