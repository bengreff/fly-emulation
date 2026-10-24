"""Lifetime plasticity (s29 fly2): N32 homeostatic set point, N34 other-site plasticity, N31 sleep/wake scaling.

Built from the s12 stubs (docs/BLANKS_AUDIT.md), each behind its own switch, neutral 0 (the model is unchanged).
CPU only: the GPU port refuses them. Each builder returns None at neutral, else the dict the Network keeps.

N32 cell_type:all|homeostatic_plasticity. Each listed cell holds its activity at a set point by an additive
    intrinsic current h (mV; a stand-in for the channel-density changes). Activity is the spike rate for spiking
    cells and the depolarisation above rest for graded ones (a rate or voltage sensor, not calcium). The set
    point is the cell's mean activity over the first capture_ms (the connectome specimen is already the adapted
    state, s12). Then h moves at h_max / tau per unit relative error (clipped to +-1), bounded to [lo, hi] per
    type: homeostat_up allows h > 0 (more excitable when too quiet), homeostat_down allows h < 0. Rows: APL down
    only, alpha/beta KCs up only (inferred, Apostolopoulou & Lin 2020: APL odour responses fall after its chronic
    activation; alpha/beta KCs gain excitability under excess inhibition; KCs do not compensate for lost APL
    inhibition, so no KC down; gamma KCs change only through APL). Validity: one actuator for all channel
    changes, set point from a short window, tau of days, so a 60 s run moves h by under 0.01 mV.
N34 synapse:other_sites|plasticity. Per-edge factor y on the connections a row of data/params/site_plasticity.csv
    selects (spiking presynaptic cells only): each presynaptic spike moves y toward the row's bound by u (depress
    toward floor, potentiate toward cap), and y relaxes to 1 with tau_rec. y multiplies the fast, slow and channel
    copies of the edge, as short-term depression does. Rows: afferents onto the giant fibre (Engel & Wu 1996
    habituation, recovery tens of seconds to 2 min) and AL LNs onto uniglomerular PNs (Das 2011 short-term
    habituation, half-life about 20 min); per-spike fractions are guessed and unchecked.
N31 synapse:all|structural_plasticity. One whole-brain synaptic scale s on every chemical synapse (spiking and
    graded): awake, s relaxes toward 1 + wake_gain with tau_wake; asleep, toward 1 with tau_sleep (Bushey 2011:
    wake raises synapse size or number over hours, recovery sleep reverts it in 5-7 h; Gilestro 2009 BRP 30-40 %
    after 12-24 h awake, secondary read). s = 1 is the specimen as reconstructed. The organism passes the N25 sleep
    state (Network.set_asleep); a bare Network is always awake. Validity: one scale for all synapses and
    neuropils, no per-synapse addition or removal.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .registry import Registry, Status

SITE_TABLE = Path(__file__).resolve().parents[2] / "data" / "params" / "site_plasticity.csv"
DAY_MS = 86_400_000.0
HOUR_MS = 3_600_000.0


def homeostat(reg: Registry, conn, table, per_neuron) -> dict | None:
    """N32: per-cell set-point rule, or None at neutral."""
    def one(prop, units, use, minimal, note):
        return float(reg.require("cell_type:all", prop, units=units, model_use=use, subsystem="neuron_biophysics",
                                 instances=conn.n, minimal=minimal, conventional=minimal, minimal_note=note))
    on = one("homeostatic_plasticity", "boolean", "N32: activity set-point intrinsic plasticity (lifetime.py)", 0.0,
             "neutral 0: no homeostatic intrinsic plasticity")
    # the scalars are read at neutral too, so they are inventoried (parameters.csv rows); they act only when on
    tau_d = one("homeostat_tau_days", "d", "N32: time for h to cross its full range at maximal error", 2.0,
                "inferred: Apostolopoulou & Lin 2020 PNAS 117:16606, KC compensation induced over about 4 d and "
                "gone 1-2 d after the APL activation stopped (Fig 3A,B); the full-range time is taken as 2 d")
    h_max = one("homeostat_max_mv", "mV", "N32: largest intrinsic shift the rule can make", 5.0,
                "guessed: no measured size of the compensating current (A&L 2020 give direction and significance)")
    s_tau = one("homeostat_sensor_tau_s", "s", "N32: averaging time of the activity sensor", 600.0,
                "guessed: must average over many odour encounters and be far shorter than tau")
    cap = one("homeostat_capture_ms", "ms", "N32: window whose mean activity is the set point", 1000.0,
              "guessed: the first second of the run; a lifetime protocol should cover representative input")
    if not on:
        return None
    if on != 1.0:
        raise ValueError(f"cell_type:all|homeostatic_plasticity = {on:g}: 0 or 1")
    up = per_neuron(reg, conn, "homeostat_up", 0.0, units="boolean", table=table)
    down = per_neuron(reg, conn, "homeostat_down", 0.0, units="boolean", table=table)
    idx = np.flatnonzero((up > 0) | (down > 0))
    pos = np.full(conn.n, -1, np.int64)
    pos[idx] = np.arange(idx.size)
    k = idx.size
    return {"idx": idx, "pos": pos, "lo": np.where(down[idx] > 0, -h_max, 0.0).astype(np.float32),
            "hi": np.where(up[idx] > 0, h_max, 0.0).astype(np.float32), "rate_mv_per_ms": h_max / (tau_d * DAY_MS),
            "sensor_tau_ms": s_tau * 1000.0, "capture_ms": cap, "h": np.zeros(k, np.float32),
            "cnt": np.zeros(k, np.float64), "acc": np.zeros(k, np.float64), "acc_ms": 0.0,
            "sensor": np.zeros(k, np.float64), "set": None, "h_full": np.zeros(conn.n, np.float32)}


def _cells(neurons: pd.DataFrame, sel: str) -> np.ndarray:
    from .lif import _stp_cells
    return _stp_cells(neurons, sel)


def site_plasticity(reg: Registry, conn, graded: np.ndarray) -> dict | None:
    """N34: per-edge use-dependent plasticity at identified sites, or None at neutral."""
    on = float(reg.require("synapse:other_sites", "plasticity", units="enum",
                           model_use="N34: use-dependent plasticity at identified sites outside the MB and ring "
                                     "(data/params/site_plasticity.csv, lifetime.py)",
                           subsystem="synaptic_efficacy", instances=conn.n_edges, minimal=0.0, conventional=0.0,
                           minimal_note="neutral 0: no plasticity outside the mushroom body and ring"))
    if not on:
        return None
    if on != 1.0:
        raise ValueError(f"synapse:other_sites|plasticity = {on:g}: 0 or 1")
    tab = pd.read_csv(SITE_TABLE, comment="#")
    pre = np.repeat(np.arange(conn.n), np.diff(conn.indptr))
    post = conn.indices
    row = np.full(conn.n_edges, -1, np.int32)
    for i, r in enumerate(tab.itertuples()):
        m = _cells(conn.neurons, r.pre)[pre] & _cells(conn.neurons, r.post)[post] & ~graded[pre]
        if isinstance(r.pre_nt, str) and r.pre_nt:
            m &= _cells(conn.neurons, f"nt:{r.pre_nt}")[pre]
        if r.sign == "exc":
            m &= conn.sign[pre] > 0
        elif r.sign == "inh":
            m &= conn.sign[pre] < 0
        row[m] = i
        for prop, val, u, basis, note in (
                ("site_u", r.u, "dimensionless", r.basis_u, r.note_u),
                ("site_tau_rec", r.tau_rec_ms, "ms", r.basis_tau, r.note_tau),
                ("site_bound", r.bound, "x baseline", r.basis_bound, r.note_bound)):
            reg.provide(f"connection:{r.site}", prop, float(val), units=u,
                        model_use=f"N34 {r.kind} at {r.site} ({r.pre} -> {r.post}, {r.sign})",
                        status=Status(basis), evidence=r.source, subsystem="synaptic_efficacy",
                        instances=int(m.sum()), uncertainty=note)
    idx = np.flatnonzero(row >= 0)
    k = row[idx]
    pos = np.full(conn.n_edges, -1, np.int64)
    pos[idx] = np.arange(idx.size)
    return {"idx": idx, "pos": pos, "u": tab.u.to_numpy(np.float64)[k],
            "tau": tab.tau_rec_ms.to_numpy(np.float64)[k], "bound": tab.bound.to_numpy(np.float64)[k],
            "y": np.ones(idx.size, np.float64), "sites": tab.site.tolist(), "row": k}


def structural(reg: Registry, conn) -> dict | None:
    """N31: whole-brain wake/sleep synaptic scale, or None at neutral."""
    def one(prop, units, use, minimal, note):
        return float(reg.require("synapse:all", prop, units=units, model_use=use, subsystem="synaptic_efficacy",
                                 instances=conn.n_edges, minimal=minimal, conventional=minimal, minimal_note=note))
    on = one("structural_plasticity", "enum", "N31: wake/sleep synaptic scaling read from the N25 sleep state "
             "(lifetime.py)", 0.0, "neutral 0: synapses fixed as reconstructed")
    # the scalars are read at neutral too, so they are inventoried (parameters.csv rows); they act only when on
    gain = one("structural_wake_gain", "dimensionless", "N31: synaptic scale approached while awake, minus 1", 0.35,
               "guessed: Gilestro et al. 2009 Science 324:109 report BRP about 30-40 % higher after 12-24 h awake "
               "(secondary read, figure values unchecked); BRP as a stand-in for synaptic strength is a guess")
    tw = one("structural_tau_wake_h", "h", "N31: rise of the scale while awake", 12.0,
             "inferred: Bushey et al. 2011 Science 332:1576, synapse size or number higher after a 12 h light "
             "period awake than after a night of sleep (Fig 1); one rise time of a day's waking half")
    ts = one("structural_tau_sleep_h", "h", "N31: return of the scale while asleep", 2.5,
             "inferred: Bushey 2011, staining back to baseline after 5 h (Fig 1h-j) or 7 h (Fig 3) of recovery "
             "sleep, so tau about 2.5 h")
    s0 = one("structural_initial_scale", "dimensionless", "N31: scale at t = 0", 1.0,
             "guessed: the specimen as reconstructed (its time of day at fixation is not known)")
    if not on:
        return None
    if on != 1.0:
        raise ValueError(f"synapse:all|structural_plasticity = {on:g}: 0 or 1")
    return {"s": s0, "s_wake": 1.0 + gain, "tau_wake_ms": tw * HOUR_MS, "tau_sleep_ms": ts * HOUR_MS,
            "asleep": False}


def homeostat_tick(hs: dict, net, dt_ms: float) -> None:
    """N32 update over the last dt_ms (called every 100 network steps)."""
    idx = hs["idx"]
    if not idx.size:
        return
    g = net.graded[idx]
    act = np.where(g, net.v[idx] - net.v_rest[idx], hs["cnt"] / (dt_ms / 1000.0))
    hs["cnt"][:] = 0.0
    if hs["set"] is None:                           # capture window: mean activity is the set point
        hs["acc"] += act * dt_ms
        hs["acc_ms"] += dt_ms
        if net.t_ms + net.timestep_ms >= hs["capture_ms"]:
            hs["set"] = hs["acc"] / hs["acc_ms"]
            hs["sensor"][:] = hs["set"]
        return
    hs["sensor"] += (act - hs["sensor"]) * (1.0 - np.exp(-dt_ms / hs["sensor_tau_ms"]))
    floor = np.where(g, 1.0, 0.1)                   # mV or Hz: guessed scale of a relative error near zero
    e = np.clip((hs["sensor"] - hs["set"]) / (np.abs(hs["set"]) + floor), -1.0, 1.0)
    hs["h"] = np.clip(hs["h"] - hs["rate_mv_per_ms"] * e * dt_ms, hs["lo"], hs["hi"]).astype(np.float32)
    hs["h_full"][idx] = hs["h"]


def site_tick(st: dict, dt_ms: float) -> None:
    """N34 recovery of every edge factor toward 1 over dt_ms."""
    st["y"] += (1.0 - st["y"]) * (1.0 - np.exp(-dt_ms / st["tau"]))


def site_factor(st: dict, sel: np.ndarray) -> np.ndarray | None:
    """N34 factor on the edges `sel` used by this step's spikes (then the spikes move y); None if none apply."""
    k = st["pos"][sel]
    m = k >= 0
    if not m.any():
        return None
    k = k[m]
    f = np.ones(sel.size, np.float32)
    f[m] = st["y"][k]
    y, u, b = st["y"][k], st["u"][k], st["bound"][k]
    st["y"][k] = y + u * (b - y)                     # toward the floor (depress) or the cap (potentiate)
    return f


def structural_tick(ss: dict, dt_ms: float) -> None:
    """N31 scale update over dt_ms from the sleep state last passed in."""
    target, tau = (1.0, ss["tau_sleep_ms"]) if ss["asleep"] else (ss["s_wake"], ss["tau_wake_ms"])
    ss["s"] = target + (ss["s"] - target) * float(np.exp(-dt_ms / tau))
