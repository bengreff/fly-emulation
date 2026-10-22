"""Unit checks for frontier stages 1-2 (fly2, s24; pre-registered in DECISIONS 22 Oct).

Isolated CNS (no body), membrane noise as in the profile (off in m10f). The network settles, then is copied; the copy is kicked and the
unkicked copy subtracted (same random state), so only the evoked input remains. "Input current" into
a cell is i_syn plus every extra receptor channel's current (stage 2 moves some edges into their own
channels).

stp:   all ORN_DM6 cells kicked together 10 times at 10 Hz (antennal-nerve trains, Nagel, Hong & Wilson
       2015 Fig 1b-c). Per pulse, the peak evoked input current summed over DM6 uniglomerular PNs in the
       5 ms after the kick, normalised to pulse 1, against Nagel Eq 1 (f 0.78, tau 893 ms) from rest.
decay: for each receptor_kinetics.csv decay, the edge with the largest weight from a spiking cell;
       its presynaptic cell kicked once; the decay time constant of the evoked input current in its
       postsynaptic cell (log-linear fit from the peak down to 5% of it) against the row.

    .venv/bin/python scripts/probes/m10f_unit_checks.py --profile m10f3 --out runs/s24/unit/m10f3.json
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1


def input_current(net, cells: np.ndarray) -> np.ndarray:
    s = net.i_syn[cells].astype(np.float64)
    for ch in net.chan:
        s = s + ch["i"][cells]
    return s


def nagel_eq1(n: int, f: float = 0.78, tau: float = 893.0, isi: float = 100.0) -> list[float]:
    x, out = 1.0, []
    for _ in range(n):
        out.append(x)
        x = 1.0 - (1.0 - f * x) * math.exp(-isi / tau)
    return out


def pair(net, memo):
    return copy.deepcopy(net, dict(memo)), copy.deepcopy(net, dict(memo))


def stp_check(net, memo, conn, kick_mv, pulses=10, isi_ms=100.0, win_ms=5.0) -> dict:
    t = conn.neurons.type.fillna("")
    pre = np.flatnonzero(t.str.fullmatch("ORN_DM6").to_numpy())
    post = np.flatnonzero((lif._stp_cells(conn.neurons, "class:ALPN") & t.str.startswith("DM6").to_numpy()))
    # resting resource x on ORN_DM6 -> DM6 PN edges at train start (spontaneous ORN spikes depress them)
    x_rest = None
    if net.stp is not None:
        s = net.stp
        e = np.concatenate([np.arange(conn.indptr[i], conn.indptr[i + 1]) for i in pre])
        e = e[np.isin(conn.indices[e], post)]
        k = s["pos"][e]
        pre_of = np.repeat(np.arange(conn.n), np.diff(conn.indptr))[e][k >= 0]
        k = k[k >= 0]
        d = net.t_ms - s["t_last"][pre_of]
        x_rest = float(np.mean(1.0 - (1.0 - s["x"][k]) * np.exp(-d / s["tau_rec"][k])))
    ctrl, kick = pair(net, memo)
    isi, nwin, n_steps = int(isi_ms / DT), int(win_ms / DT), int((pulses * isi_ms + 20.0) / DT)
    dI = np.zeros(n_steps)
    spont = 0
    for s_ in range(n_steps):
        ctrl.step()
        on = s_ % isi == 0 and s_ // isi < pulses
        sp = kick.step(kick=(pre, kick_mv) if on else None)
        if not on:
            spont += int(np.isin(sp, pre).sum())
        dI[s_] = input_current(kick, post).sum() - input_current(ctrl, post).sum()
    peaks = [float(dI[k * isi: k * isi + nwin].max()) for k in range(pulses)]
    norm = [p / peaks[0] for p in peaks]
    ref = nagel_eq1(pulses)
    dev = [n - r for n, r in zip(norm, ref)]
    rms = float(np.sqrt(np.mean(np.square(dev[1:]))))
    # single-parameter refit: f with tau fixed at 893 ms, the value the in-network curve implies
    fs = np.linspace(0.40, 0.99, 591)
    err = [np.sum((np.array(norm) - np.array(nagel_eq1(pulses, f))) ** 2) for f in fs]
    f_fit = float(fs[int(np.argmin(err))])
    return {"n_orn": int(len(pre)), "n_pn": int(len(post)), "x_rest_mean": x_rest,
            "spont_orn_spikes_during_train": spont,
            "spont_orn_hz": spont / len(pre) / (n_steps * DT / 1000.0),
            "peak_input": peaks, "normalised": norm, "nagel_eq1": ref, "deviation": dev,
            "rms_dev_pulses_2_10": rms, "pulse10_dev": dev[-1], "f_fit_tau893": f_fit,
            "pass": bool(rms <= 0.10 and abs(dev[-1]) <= 0.10)}


def decay_check(net, memo, conn, kick_mv, win_ms=25.0) -> list[dict]:
    t = conn.neurons.type.fillna("")
    pre_of = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    rows = []
    for ch in net.chan:
        if not ch.get("kin"):
            continue
        tau_row = -DT / math.log(float(ch["decay"]))
        nz = np.flatnonzero(ch["w"])
        nz = nz[~net.graded[pre_of[nz]]]
        e = int(nz[np.argmax(np.abs(ch["w"][nz]))])
        i, j = int(pre_of[e]), int(conn.indices[e])
        ctrl, kick = pair(net, memo)
        nw = int(win_ms / DT)
        dI = np.zeros(nw)
        for s_ in range(nw):
            ctrl.step()
            kick.step(kick=(np.array([i]), kick_mv) if s_ == 0 else None)
            dI[s_] = input_current(kick, np.array([j]))[0] - input_current(ctrl, np.array([j]))[0]
        sg = np.sign(dI[np.argmax(np.abs(dI))])
        y = dI * sg
        k0 = int(np.argmax(y))
        k1 = k0 + 1
        while k1 < nw and y[k1] > 0.05 * y[k0]:
            k1 += 1
        tt = np.arange(k0, k1) * DT
        slope = np.polyfit(tt, np.log(y[k0:k1]), 1)[0]
        tau_fit = float(-1.0 / slope)
        rows.append({"channel": ch["name"], "tau_row_ms": round(tau_row, 3), "pre_type": t.iat[i],
                     "post_type": t.iat[j], "edge_w": float(ch["w"][e]), "peak_input": float(y[k0] * sg),
                     "t_peak_ms": round(k0 * DT, 1), "fit_points": int(k1 - k0), "tau_fit_ms": round(tau_fit, 3),
                     "rel_err": round(tau_fit / tau_row - 1.0, 4),
                     "pass": bool(abs(tau_fit / tau_row - 1.0) <= 0.05)})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f3")
    ap.add_argument("--settle-ms", type=float, default=500.0)
    ap.add_argument("--checks", default="stp,decay")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    reg = Registry(Policy.MINIMAL)
    prof = profiles.apply(reg, a.profile)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(1))
    net.elec = el if len(el[0]) else None
    for _ in range(int(a.settle_ms / DT)):
        net.step()
    memo = {id(conn): conn, id(params): params}
    out = {"profile": a.profile, "settle_ms": a.settle_ms, "kick_mv": prof["kick_mv"]}
    if "stp" in a.checks:
        out["stp"] = stp_check(net, memo, conn, prof["kick_mv"])
        print("stp", json.dumps({k: v for k, v in out["stp"].items() if k not in ("peak_input",)}), flush=True)
    if "decay" in a.checks:
        out["decay"] = decay_check(net, memo, conn, prof["kick_mv"])
        for r in out["decay"]:
            print("decay", json.dumps(r), flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
