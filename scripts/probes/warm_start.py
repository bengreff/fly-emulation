"""Warm-start CX bump test (session 8).

Every earlier run started the whole CNS exactly at rest, with no noise, and
switched every sense on as a step at t = 0 ("brain death" start). This probe
starts the fly in a living state instead, then applies the CX bump test that
Ben set after session 7 (DECISIONS s7, decision 2).

Timeline (defaults):
  0 .. warm           background noise and senses both ramp linearly 0 -> 1 over --ramp-ms
  warm .. +kick       external drive to EPGs: local (within +-half-width of a random
                      heading drawn from --seed), full (all EPGs) or none
  +kick .. +post      all afferent drive removed (noise stays on); scoring windows

Heading of each EPG is inferred from its PB glomerulus (instance "EPG(PB08)_L3"):
angle = (k - 1) x 45 deg, +22.5 deg on the right side (Wolff 2015; Hulse 2021 PB->EB
map; resolution +-22.5 deg). The session-7 cx_kick probe kicked the first N EPGs in
table order (L3, L5, L5, L3, R3, R7): not a local kick.

    uv run python scripts/probes/warm_start.py --noise 0.5 --kick local --seed 1
    uv run python scripts/probes/warm_start.py --noise 0.5 --kick none --senses off   # control
"""
import argparse
import json
import re
import sys
import time

import numpy as np

sys.path.insert(0, "src")
from flyemu.organism import Organism  # noqa: E402
from flyemu.profiles import WORKING_PROFILE  # noqa: E402

# Declared CX ring type list (pre-registration, session 8): scored by the bump
# test, excluded from the "every other cell goes quiet" criterion.
CX_RING = ("EPG", "PEN_a", "PEN_b", "PEG", "Delta7", "ER", "EL")


def epg_heading(instances: np.ndarray) -> np.ndarray:
    out = np.full(len(instances), np.nan)
    for i, s in enumerate(instances):
        m = re.search(r"_([LR])(\d)$", str(s))
        if m:
            k = int(m.group(2))
            out[i] = ((k - 1) % 8) * 45.0 + (22.5 if m.group(1) == "R" else 0.0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--noise", type=float, default=0.0, help="background noise, mV/sqrt(ms)")
    ap.add_argument("--ramp-ms", type=float, default=500.0)
    ap.add_argument("--warm-ms", type=float, default=1000.0)
    ap.add_argument("--kick", choices=("local", "full", "none"), default="local")
    ap.add_argument("--kick-ms", type=float, default=50.0)
    ap.add_argument("--kick-mv", type=float, default=10.0, help="steady depolarisation while kicked")
    ap.add_argument("--half-width", type=float, default=45.0, help="local kick half-width, deg")
    ap.add_argument("--post-ms", type=float, default=500.0)
    ap.add_argument("--senses", choices=("on", "off"), default="on")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--heading", type=float, default=None, help="kick heading, deg (default: drawn from the seed)")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--heading-map", choices=("embed", "glomerulus"), default="embed")
    ap.add_argument("--out", default=None, help="append the JSON line to this file")
    a = ap.parse_args()
    ov = {"motor_unit:all|force_per_spike": 10.0}
    ov.update({k: float(v) for k, v in (s.split("=") for s in a.set)})
    ov["cell_type:all|background_noise"] = a.noise
    org = Organism(policy="minimal", profile=WORKING_PROFILE, min_synapses=5, overrides=ov, seed=a.seed)
    net, dt, N = org.net, org.timestep_ms, org.conn.n
    nr = org.conn.neurons
    t = nr.type.fillna("").to_numpy().astype(str)
    sw = lambda *p: np.any([np.char.startswith(t, x) for x in p], axis=0)  # noqa: E731
    grp = {
        "EPG": np.flatnonzero(sw("EPG")), "PEN": np.flatnonzero(sw("PEN_a", "PEN_b")),
        "PEG": np.flatnonzero(sw("PEG")), "Delta7": np.flatnonzero(sw("Delta7")),
        "ER": np.flatnonzero(sw("ER")), "EL": np.flatnonzero(sw("EL")),
        "PFN": np.flatnonzero(sw("PFN")),
        "uPN": np.flatnonzero((nr["class"].fillna("") == "ALPN").to_numpy() & np.char.endswith(t, "PN")),
        "KC": np.flatnonzero(sw("KC")),
        "MN": np.flatnonzero((nr.superclass.fillna("") == "vnc_motor").to_numpy()),
    }
    cx = sw(*CX_RING)
    tonic = np.broadcast_to(np.asarray(net.params.spont_mv), (N,)) > 0
    epg = grp["EPG"]
    if a.heading_map == "embed":   # inferred from connectivity (scripts/infer_epg_heading.py)
        import pandas as pd
        hm = pd.read_csv("data/derived/epg_heading_embedding.csv").set_index("bodyId").heading_deg
        ang = nr.bodyId.to_numpy()[epg]
        ang = pd.Series(ang).map(hm).to_numpy(float)
    else:                         # s8 first version: L_k and R_k share a heading (wrong; see DECISIONS s8)
        ang = epg_heading(nr.instance.to_numpy()[epg])
    h = float(np.random.default_rng(1000 + a.seed).uniform(0, 360)) if a.heading is None else a.heading % 360
    d = np.abs((ang - h + 180) % 360 - 180)
    target = {"local": epg[d <= a.half_width], "full": epg, "none": epg[:0]}[a.kick]

    warm, k_end = a.warm_ms, a.warm_ms + a.kick_ms
    total = k_end + a.post_ms
    w_warm = (warm - 500, warm)                 # living-state rates
    w_post = (k_end + 200, total)               # >= 200 ms after the kick ends
    w_last = (total - 100, total)               # the "goes quiet" window
    c_warm, c_post = np.zeros(N), np.zeros(N)
    last_noncx, epg_ts = 0, []
    z, t0 = [], time.time()
    zero = np.zeros(N, np.float32)
    for s in range(int(total / dt)):
        ms = s * dt
        ramp = min(1.0, ms / a.ramp_ms) if a.ramp_ms > 0 else 1.0
        net.params.noise_mv = a.noise * ramp
        obs = org.body.observe()
        if ms < k_end and a.senses == "on":
            ext = org.sense(s, obs) * np.float32(ramp)
        else:
            ext = zero.copy() if warm <= ms < k_end else zero
        if warm <= ms < k_end and len(target):
            ext[target] += a.kick_mv
        sp = net.step(external_mv=ext)
        if sp.size > 20000:
            print(json.dumps({"runaway_at_ms": ms, "noise": a.noise, "kick": a.kick, "seed": a.seed}))
            return
        if w_warm[0] <= ms < w_warm[1]:
            c_warm[sp] += 1
        if w_post[0] <= ms < w_post[1]:
            c_post[sp] += 1
        if w_last[0] <= ms < w_last[1]:
            last_noncx += int((~cx[sp] & ~tonic[sp]).sum())
        if ms >= k_end and s % 100 == 0:       # EPG activity every 10 ms after the kick
            epg_ts.append(int(np.isin(sp, epg).sum()))
        org.body.actuate(org.nm.step(sp, dt)); org.body.set_adhesion(org.nm.grip); org.body.step()
        if s % 100 == 0:
            z.append(float(obs["body_positions"][0, 2]))
    hw = c_warm / ((w_warm[1] - w_warm[0]) / 1000)
    hp = c_post / ((w_post[1] - w_post[0]) / 1000)
    r = hp[epg]
    vec = (r * np.exp(1j * np.deg2rad(ang))).sum() / max(r.sum(), 1e-9)
    bump_deg = float(np.rad2deg(np.angle(vec)) % 360)
    out = {
        "noise": a.noise, "kick": a.kick, "senses": a.senses, "seed": a.seed,
        "set": {k: v for k, v in ov.items() if k not in ("cell_type:all|background_noise",)},
        "warm_hz": {g: round(float(hw[ix].mean()), 2) for g, ix in grp.items()},
        "warm_frac_active": {g: round(float((hw[ix] > 0).mean()), 2) for g, ix in grp.items()},
        "warm_brain_hz": round(float(hw.mean()), 3),
        "warm_noncx_hz": round(float(hw[~cx].mean()), 3),
        "post_hz": {g: round(float(hp[ix].mean()), 2) for g, ix in grp.items()},
        "epg_active_frac": round(float((r >= 10).mean()), 3),
        "epg_vector_strength": round(float(abs(vec)), 3),
        "bump_deg": round(bump_deg, 1), "kick_heading_deg": round(h, 1),
        "bump_error_deg": round(float(abs((bump_deg - h + 180) % 360 - 180)), 1),
        "n_kicked": int(len(target)), "heading_map": a.heading_map,
        "epg_post_hz_by_heading": [[round(float(x), 1), round(float(y), 1)] for x, y in sorted(zip(ang, r))],
        "last100_noncx_hz": round(last_noncx / (~cx & ~tonic).sum() / 0.1, 4),
        "post_noncx_hz": round(float(hp[~cx & ~tonic].mean()), 4),
        "epg_spikes_per_10ms_after_kick": epg_ts[::5],
        "z_min_mm": round(min(z), 3), "z_final_mm": round(z[-1], 3),
        "wall_s": round(time.time() - t0),
    }
    line = json.dumps(out)
    print(line)
    if a.out:
        with open(a.out, "a") as f:
            f.write(line + "\n")


if __name__ == "__main__":
    main()
