"""python -m flyemu.score: play one scoreboard protocol from a fly_brain.zip (docs/FLY_BRAIN_ZIP.md, "Scoreboard").

    PYTHONPATH=fly_brain.zip/code python -m flyemu.score fly_brain.zip --protocol per_labellar_sugar --out s/
    PYTHONPATH=src python -m flyemu.score --tree . --protocol per_labellar_sugar --out s_tree/   # the reference

A protocol (world/protocols/<name>.json) names the brain build, settings, seeds, duration, a stimulus
(world/stimuli/<name>.json: timed events on cell types), a readout and its pass conditions. This module only
interprets them; every number is in the files. Launch, extraction and the read guard are flyemu.run's.

Harnesses:
- build "assay": the brain as scripts/assay_pathways.py builds it, a fresh lif.Network per seed; no body;
- build "organism": flyemu.organism.Organism, as scripts/probes/gf_latency.py builds it; the body is not stepped;
- build "closed_loop": the same Organism with the body stepped and every sense reaching the brain, the loop of
  flyemu.run and scripts/probes/command_walk.py.
Stimulus events: "poisson_kick" (each listed cell gets an independent Poisson train of kicks while on) and
"kick" (a fixed train of kicks). Readouts: "mean_rate_hz", "gf_latency" (network harnesses), "leg_oscillation"
(command_walk.py's per-leg stepping summary) and "posture" (thorax and head height, drift, floor contacts)
(closed_loop). A closed-loop run is refused unless only the network's motor spikes move the body (no servo,
mocap, tether, wingbeat generator or stimulated motor neuron; _connectome_driven).

Writes score_manifest.json (per seed: spike count and hash over every neuron, readout; the aggregate readout,
each pass condition and the verdict) and registry_reads.csv. A protocol whose bar is not written yet has no pass
conditions and a "bar_todo"; its verdict is NO BAR. Exit code 0 whether the protocol passes or fails; 2 on
refusal.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from . import flyzip, run

RESULT = "score_manifest.json"
WORLD = Path("data") / "world"          # runtime path of the zip's world/ protocols, stimuli and scoreboard


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Play one scoreboard protocol from fly_brain.zip")
    ap.add_argument("zip", nargs="?", help="fly_brain.zip (omit with --tree)")
    ap.add_argument("--tree", help="run from this repo tree instead of a zip (the identity reference)")
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--deny", action="append", default=[], help="refuse any read under this root (repeatable)")
    ap.add_argument("--workdir", help="extraction directory (new or empty); default a fresh temp dir")
    ap.add_argument("--keep", action="store_true", help="keep the extracted tree")
    ap.add_argument("--allow-runtime-mismatch", action="store_true")
    ap.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--root", help=argparse.SUPPRESS)
    return ap


# --- protocol files -------------------------------------------------------------------------------------

def load(root: Path, name: str) -> tuple[dict, dict, dict]:
    """The protocol and its stimulus, plus the sha256 of each file as read."""
    pf = root / WORLD / "protocols" / f"{name}.json"
    if not pf.is_file():
        have = sorted(p.stem for p in (root / WORLD / "protocols").glob("*.json"))
        raise flyzip.Refused(f"no protocol {name!r} in world/protocols; built: {have}")
    proto = json.loads(pf.read_text())
    sf = root / WORLD / "stimuli" / f"{proto['stimulus']}.json"
    if not sf.is_file():
        raise flyzip.Refused(f"protocol {name} names stimulus {proto['stimulus']!r}, not in world/stimuli")
    stim = json.loads(sf.read_text())
    return proto, stim, {"protocol": flyzip.sha256_file(pf), "stimulus": flyzip.sha256_file(sf)}


def select(types, cell_types):
    """Indices of cells whose type is listed; an entry starting '^' is a regex (as assay_pathways.select)."""
    import numpy as np
    import pandas as pd
    t = pd.Series(cell_types).fillna("")
    m = t.isin([x for x in types if not x.startswith("^")])
    for x in types:
        if x.startswith("^"):
            m |= t.str.match(x)
    return np.flatnonzero(m.to_numpy())


class Schedule:
    """The stimulus events of one trial, resolved to cell indices and steps."""

    def __init__(self, stim: dict, cell_types, dt: float, n_steps: int, kick_mv_profile: float | None):
        import numpy as np
        self.poisson, self.trains = [], []
        seen = np.zeros(len(cell_types), bool)
        for ev in stim["events"]:
            idx = select(ev["types"], cell_types)
            if not len(idx):
                raise flyzip.Refused(f"stimulus {stim['name']}: types {ev['types']} match no cell")
            if seen[idx].any():
                raise flyzip.Refused(f"stimulus {stim['name']}: two events kick the same cell")
            seen[idx] = True
            mv = ev["kick_mv"]
            if mv == "profile":
                if kick_mv_profile is None:
                    raise flyzip.Refused("kick_mv 'profile' but the profile has no kick_mv")
                mv = kick_mv_profile
            if ev["kind"] == "poisson_kick":
                on = int(round(ev["t_on_ms"] / dt))
                off = n_steps if ev["t_off_ms"] is None else int(round(ev["t_off_ms"] / dt))
                self.poisson.append((idx, ev["rate_hz"] * dt / 1000.0, float(mv), on, off))
            elif ev["kind"] == "kick":
                s0, per = int(round(ev["start_ms"] / dt)), int(round(ev["period_ms"] / dt))
                self.trains.append((idx, float(mv), {s0 + i * per for i in range(ev["count"])}))
            else:
                raise flyzip.Refused(f"stimulus event kind {ev['kind']!r} is not built")
        self.cells = np.flatnonzero(seen)

    def kick(self, s: int, rng):
        """The (indices, mV) kick of step s, or None. One uniform per Poisson cell per step while it is on."""
        import numpy as np
        parts = []
        live = [(i, p, mv) for i, p, mv, on, off in self.poisson if on <= s < off]
        if live:
            idx = np.concatenate([i for i, _, _ in live]) if len(live) > 1 else live[0][0]
            prob = np.concatenate([np.full(len(i), p) for i, p, _ in live])
            mv = np.concatenate([np.full(len(i), m) for i, _, m in live])
            hit = rng.random(len(idx)) < prob
            parts.append((idx[hit], mv[hit]))
        for idx, mv, steps in self.trains:
            if s in steps:
                parts.append((idx, np.full(len(idx), mv)))
        if not parts:
            return None
        idx = np.concatenate([p[0] for p in parts])
        mv = np.concatenate([p[1] for p in parts])
        if len(mv) and (mv == mv[0]).all():
            return idx, float(mv[0])            # one value: the scalar form the reference scripts pass
        return (idx, mv) if len(idx) else (idx, 0.0)


# --- harnesses ------------------------------------------------------------------------------------------

def _build_assay(s: dict):
    """The brain of scripts/assay_pathways.py (no stubs, no body, no Q10)."""
    from . import connectome, electrical, lif, profiles
    from .registry import Registry
    reg = Registry(s["policy"])
    prof = profiles.apply(reg, s["profile"])
    conn = connectome.build(reg, min_synapses=s["min_synapses"])
    params = lif.default_params(reg, conn, timestep_ms=s["timestep_ms"])
    el = electrical.build(reg, conn)
    el = el if len(el[0]) else None

    def network(seed):
        import numpy as np
        net = lif.Network(conn, params, s["timestep_ms"], rng=np.random.default_rng(seed))
        net.elec = el
        return net
    return reg, conn, prof["kick_mv"], network, None


def _build_organism(s: dict, seed: int, world):
    from .organism import Organism
    org = Organism(policy=s["policy"], timestep_ms=s["timestep_ms"], profile=s["profile"],
                   min_synapses=s["min_synapses"], seed=seed, world=world)
    return org


def _connectome_driven(org, conn, stim_cells) -> dict:
    """Refuse a closed-loop run in which anything but the network's motor spikes could move the body (bar of
    21 Oct, DECISIONS 02:33: no controller, CPG stub or kinematic replay may be active). Checked: every MuJoCo
    actuator is a plain force or adhesion actuator (no position or velocity servo, i.e. no bias term); no mocap
    body; no active weld or connect constraint (a tether); no wingbeat generator (flight:wings 0); no stimulated
    cell is a motor neuron. By construction of this module's loop, motor_step gets the spikes and no external
    torque, and nothing writes qpos or ctrl. Returns what was checked, for the manifest."""
    import mujoco
    import numpy as np
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    servo = [m.actuator(i).name for i in range(m.nu) if m.actuator_biastype[i] != mujoco.mjtBias.mjBIAS_NONE]
    tether = [i for i in range(m.neq) if d.eq_active[i]
              and m.eq_type[i] in (mujoco.mjtEq.mjEQ_WELD, mujoco.mjtEq.mjEQ_CONNECT)]
    sc = conn.neurons.superclass.fillna("").to_numpy()[stim_cells]
    stim_motor = sorted({str(conn.neurons.type.iat[i]) for i, s in zip(stim_cells, sc) if "motor" in s})
    got = {"actuators": int(m.nu), "servo_actuators": servo, "mocap_bodies": int(m.nmocap),
           "equality_active": int(np.sum(d.eq_active[:m.neq])) if m.neq else 0, "tether_constraints": tether,
           "wingbeat_generator": org.flight is not None, "stimulated_motor_types": stim_motor,
           "motor_step_extra_torque": False}
    bad = {k: v for k, v in got.items() if k not in ("actuators", "equality_active") and v}
    if bad:
        raise flyzip.Refused(f"closed loop is not driven by the connectome alone: {bad}")
    return got


class _Body:
    """Body samples taken after the motor step every `every` steps, as scripts/probes/command_walk.py takes
    them: the thorax position and each tarsal tip's fore-aft position in the thorax frame (mm); the thorax
    heading (its x axis in the world, horizontal); the head body's height; and the floor contacts: which bodies
    the floor pushes on (normal force > 0, as bypass_s1_actuation.py's floor_forces counts a touch). Feet are the
    tarsal segments; a head, thorax, abdomen, wing, coxa, femur or tibia on the floor is a non-foot touch.
    Reading contacts and forces does not change the simulation."""

    def __init__(self, org, legs: list[str], every: int):
        import mujoco
        import numpy as np
        m = org.body.sim.mj_model
        pre = org.body.fly.name + "/"
        self.m, self.d, self.every = m, org.body.sim.mj_data, every
        self.X, self.P, self.H, self.Z, self.C = [], [], [], [], []
        self.tips = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, pre + f"{leg}_tarsus5") for leg in legs]
        self.th = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, pre + "c_thorax")
        self.hd = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, pre + "c_head")
        if min(self.tips + [self.th, self.hd]) < 0:
            raise flyzip.Refused("the body has no c_thorax, c_head or <leg>_tarsus5 body")
        names = [(m.body(i).name or "").split("/")[-1] for i in range(m.nbody)]
        self.names = names
        self.foot = np.array(["tarsus" in n for n in names])
        self.leg_of = {i: n[:2] for i, n in enumerate(names) if self.foot[i]}
        d = self.d
        if (d.xpos[self.hd] - d.xpos[self.th]) @ d.xmat[self.th].reshape(3, 3)[:, 0] <= 0:
            raise flyzip.Refused("the head is not ahead of the thorax along the thorax x axis")
        self._f6 = np.zeros(6)

    def _contacts(self) -> tuple[list[str], int]:
        import mujoco
        m, d = self.m, self.d
        other, legs = set(), set()
        for i in range(d.ncon):
            c = d.contact[i]
            b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
            if (b1 != 0) == (b2 != 0):
                continue
            b = b2 if b1 == 0 else b1
            mujoco.mj_contactForce(m, d, i, self._f6)
            if self._f6[0] <= 0:
                continue
            if self.foot[b]:
                legs.add(self.leg_of[b])
            else:
                other.add(self.names[b])
        return sorted(other), len(legs)

    def sample(self, step: int) -> None:
        if step % self.every == 0:
            d = self.d
            R = d.xmat[self.th].reshape(3, 3)
            self.X.append(((d.xpos[self.tips] - d.xpos[self.th]) @ R)[:, 0])
            self.P.append(d.xpos[self.th].copy())
            self.H.append(R[:2, 0].copy())
            self.Z.append(float(d.xpos[self.hd, 2]))
            self.C.append(self._contacts())


# --- readouts -------------------------------------------------------------------------------------------

def _status_excluded(root: Path, conn, idx, words):
    import numpy as np
    import pandas as pd
    f = root / "data" / "cache" / "male_cns_extra.parquet"
    if not f.is_file():
        raise flyzip.Refused("readout excludes incompletely traced cells but data/cache/male_cns_extra.parquet "
                             "is missing")
    lab = (pd.read_parquet(f, columns=["bodyId", "statusLabel"]).set_index("bodyId").statusLabel
           .reindex(conn.neurons.bodyId).fillna("").to_numpy())
    bad = np.array([any(w in x for w in words) for x in lab[idx]], bool)
    return idx[~bad], [str(conn.neurons.instance.iat[i]) for i in idx[bad]]


def _gf_latency(r: dict, sp, dt: float, gf, mns: dict, kicks: list[int], period: int, delays: dict) -> dict:
    """scripts/probes/gf_latency.py run_arm, from the recorded (step, cell) spikes."""
    import pandas as pd
    win = int(round(r["window_ms"] / dt))
    controls = [k + period // 2 for k in kicks]

    def first_after(cells, s0):
        x = sp[sp.cell.isin(cells) & (sp.step > s0) & (sp.step <= s0 + win)]
        return x.groupby("cell").step.min()

    def count_after(cells, s0):
        x = sp[sp.cell.isin(cells) & (sp.step > s0) & (sp.step <= s0 + win)]
        return x.groupby("cell").step.size()
    rows = []
    for trial, (k, c) in enumerate(zip(kicks, controls)):
        g = sp[sp.cell.isin(gf) & (sp.step >= k) & (sp.step <= k + r["gf_spike_within_steps"])].step
        s_gf = int(g.min()) if len(g) else None
        for ty, ix in mns.items():
            fk = first_after(ix, s_gf) if s_gf is not None else pd.Series(dtype=int)
            fc = first_after(ix, c)
            nk = count_after(ix, s_gf) if s_gf is not None else pd.Series(dtype=int)
            for cell in ix:
                lat = (fk[cell] - s_gf) * dt if cell in fk.index else None
                rows.append({"trial": trial, "type": ty, "cell": int(cell), "gf_spiked": s_gf is not None,
                             "central_ms": lat, "muscle_ms": None if lat is None else lat + float(delays[ty]),
                             "control_spike": cell in fc.index, "n_spikes": int(nk[cell]) if cell in nk.index else 0})
    df = pd.DataFrame(rows)
    q = {"gf_spike_fraction": float(df.drop_duplicates("trial").gf_spiked.mean())}
    for ty, d in df.groupby("type"):
        lat = d.central_ms.dropna()
        q[f"{ty}.cells"] = int(d.cell.nunique())
        q[f"{ty}.follow_fraction"] = float(d.central_ms.notna().mean())
        q[f"{ty}.control_fraction"] = float(d.control_spike.mean())
        q[f"{ty}.central_ms_median"] = float(lat.median()) if len(lat) else None
        q[f"{ty}.muscle_ms_median"] = float(d.muscle_ms.dropna().median()) if len(lat) else None
        q[f"{ty}.spikes_per_window_mean"] = float(d.n_spikes.mean())
    return q


# --- pass conditions ------------------------------------------------------------------------------------

def _window(r: dict, sample_ms: float) -> tuple[int, int]:
    i0, i1 = (int(round(t / sample_ms)) for t in r["window_ms"])
    return i0, i1


def _leg_oscillation(r: dict, X: list, P: list, H: list, hz, stim, mn, sample_ms: float) -> dict:
    """scripts/probes/command_walk.py's leg summary over the window: per leg, the dominant fore-aft frequency of
    the tarsal tip inside the band, the band's share of the tip's power and its peak-to-peak amplitude (2 SD);
    the thorax displacement; the mean rate of the leg motor neurons and of the stimulated cells. With
    "step_band_hz", also each tip's power share inside that band, and the thorax displacement along its own
    heading at the window's start (thorax_forward_mm, > 0 is forward)."""
    import numpy as np
    i0, i1 = _window(r, sample_ms)
    Xw = np.array(X)[i0:i1]
    lo, hi = r["band_hz"]
    out = {}
    s_lo, s_hi = r.get("step_band_hz", (lo, hi))
    for i, leg in enumerate(r["legs"]):
        x = Xw[:, i] - Xw[:, i].mean()
        f = np.fft.rfftfreq(len(x), sample_ms / 1000.0)
        pw = np.abs(np.fft.rfft(x)) ** 2
        band = (f >= lo) & (f <= hi)
        k = np.argmax(pw * band)
        out[f"{leg}.f_hz"] = float(f[k])
        out[f"{leg}.band_share"] = float(pw[band].sum() / pw[1:].sum())
        if "step_band_hz" in r:
            out[f"{leg}.step_band_share"] = float(pw[(f >= s_lo) & (f <= s_hi)].sum() / pw[1:].sum())
        out[f"{leg}.amp_mm"] = float(x.std() * 2)
    out["thorax_dx_mm"] = float(P[i1][0] - P[i0][0])
    out["thorax_dy_mm"] = float(P[i1][1] - P[i0][1])
    if H:
        h = H[i0] / np.hypot(*H[i0])
        out["thorax_forward_mm"] = float((P[i1][:2] - P[i0][:2]) @ h)
    out["leg_mn_hz"] = float(hz[mn].mean())
    out["stim_rate_hz"] = float(hz[stim].mean()) if len(stim) else None
    return out


def _posture(r: dict, P: list, Z: list, C: list, sample_ms: float) -> dict:
    """The thorax body's world-frame height (mm) over the window: median, minimum and last sample; and its
    horizontal drift from the window's first to last sample. With "stand_window_ms", over that window: the head
    body's height above the motor-silenced collapse ("collapsed_head_mm", the zero of Wang 2025's head heights),
    median and minimum; the share of samples with any non-foot body on the floor and those bodies (samples
    touched); the median number of legs with a tarsal segment on the floor."""
    import numpy as np
    i0, i1 = _window(r, sample_ms)
    Pw = np.array(P)[i0:i1]
    out = {"thorax_z_mm_median": float(np.median(Pw[:, 2])), "thorax_z_mm_min": float(Pw[:, 2].min()),
           "thorax_z_mm_last": float(Pw[-1, 2]), "thorax_drift_mm": float(np.hypot(*(Pw[-1, :2] - Pw[0, :2])))}
    if "stand_window_ms" in r:
        j0, j1 = _window({"window_ms": r["stand_window_ms"]}, sample_ms)
        if not 0 <= j0 < j1 <= len(Z):
            raise flyzip.Refused(f"stand_window_ms {r['stand_window_ms']} is outside the run")
        head = np.array(Z[j0:j1]) - r["collapsed_head_mm"]
        other = [c[0] for c in C[j0:j1]]
        bodies: dict[str, int] = {}
        for o in other:
            for b in o:
                bodies[b] = bodies.get(b, 0) + 1
        out.update({"head_above_collapse_mm_median": float(np.median(head)),
                    "head_above_collapse_mm_min": float(head.min()),
                    "nonfoot_floor_frac": float(np.mean([bool(o) for o in other])),
                    "nonfoot_floor_bodies": dict(sorted(bodies.items(), key=lambda kv: -kv[1])),
                    "legs_on_floor_median": float(np.median([c[1] for c in C[j0:j1]]))})
    return out


def judge(conds: list[dict], q: dict) -> list[dict]:
    out = []
    for c in conds:
        names = c["quantity"] if isinstance(c["quantity"], list) else [c["quantity"]]
        v, op = c["value"], c["op"]
        for n in names if op != "count_where" else []:
            if n not in q:
                raise flyzip.Refused(f"pass condition names {n!r}, which the readout does not produce")
        vals = [q[n] for n in names] if op != "count_where" else []
        if op == "present_all_in":
            got = [x for x in vals if x is not None]
            ok = bool(got) and all(v[0] <= x <= v[1] for x in got)
        elif op == "count_where":
            # quantity: prefixes (legs); each prefix counts if every "where" test on <prefix>.<field> holds
            hits = []
            for p in names:
                tests = [judge([{"quantity": f"{p}.{w['field']}", "op": w["op"], "value": w["value"]}], q)[0]
                         for w in c["where"]]
                if all(t["ok"] for t in tests):
                    hits.append(p)
            ok = len(hits) >= v
            out.append({**c, "observed": len(hits), "counted": hits, "ok": bool(ok)})
            continue
        else:
            x = vals[0]
            ok = x is not None and {">": lambda: x > v, ">=": lambda: x >= v, "<": lambda: x < v,
                                    "<=": lambda: x <= v, "in": lambda: v[0] <= x <= v[1]}[op]()
        out.append({**c, "observed": vals if len(vals) > 1 else vals[0], "ok": bool(ok)})
    return out


# --- inside the extracted (or repo) tree ----------------------------------------------------------------

def inside(a) -> int:
    c = run.child_setup(a)
    root, mode, man, guard = c["root"], c["mode"], c["man"], c["guard"]
    proto, stim, shas = load(root, a.protocol)
    s = proto["settings"]
    profile_src = run.load_profile(root, mode, s["profile"])
    out = Path(a.out).resolve()

    import numpy as np
    import pandas as pd
    dt, n_steps = s["timestep_ms"], int(round(proto["duration_ms"] / s["timestep_ms"]))
    r = proto["readout"]
    build = proto["harness"]["build"]
    trials, body, world_src, last_reg = [], None, None, None
    t_build = time.time()
    if build == "assay":
        reg, conn, kick_mv, network, _ = _build_assay(s)
        last_reg = reg
    elif build not in ("organism", "closed_loop"):
        raise flyzip.Refused(f"harness build {build!r} is not built")
    loop = build == "closed_loop"
    if loop != (r["kind"] in ("leg_oscillation", "posture")):
        raise flyzip.Refused(f"readout {r['kind']!r} does not go with harness build {build!r}")
    build_s = time.time() - t_build
    for seed in proto["seeds"]:
        t0 = time.time()
        if build in ("organism", "closed_loop"):
            world, world_src = run._world(root, mode, s["arena"])
            org = _build_organism(s, seed, world)
            reg, conn, kick_mv, net = org.reg, org.conn, org.kick_mv, org.net
            last_reg = reg
            body = {"source": c["body_src"], "nq": int(org.body.sim.mj_model.nq), "stepped": loop}
            if loop:
                bs = _Body(org, r.get("legs", []), r["sample_every_steps"])
        else:
            net = network(seed)
        types = conn.neurons.type.fillna("").to_numpy()
        sched = Schedule(stim, types, dt, n_steps, kick_mv)
        drive = _connectome_driven(org, conn, sched.cells) if loop else None
        rng = np.random.default_rng(seed + proto["stimulus_rng_offset"])
        counts = np.zeros(conn.n, np.int32)
        st, ix = [], []
        for step in range(n_steps):
            if loop:
                obs = org.body.observe()
                spk = net.step(external_mv=org.sense(step, obs), kick=sched.kick(step, rng))
            else:
                spk = net.step(kick=sched.kick(step, rng))
            if spk.size:
                counts[spk] += 1
                st.append(np.full(spk.size, step, np.int32))
                ix.append(np.asarray(spk, np.int32))
            if loop:
                org.motor_step(spk)
                bs.sample(step)
        steps = np.concatenate(st) if st else np.zeros(0, np.int32)
        idx = np.concatenate(ix) if ix else np.zeros(0, np.int32)
        row = {"seed": seed, "spikes": int(idx.size), "spikes_sha256": flyzip.sha256_bytes(steps.tobytes() + idx.tobytes())}
        if loop:
            dd = org.body.sim.mj_data
            row["final_qpos_sha256"] = flyzip.sha256_bytes(np.ascontiguousarray(dd.qpos, dtype=np.float64).tobytes())
            row["nan_state"] = bool(not np.isfinite(dd.qpos).all() or not np.isfinite(net.v).all())
            row["mujoco_warnings"] = int(sum(w.number for w in dd.warning))
            row["drive_check"] = drive
            sample_ms = r["sample_every_steps"] * dt
        if r["kind"] == "leg_oscillation":
            a0, a1 = r["window_ms"]
            t = steps * dt
            w = (t >= a0) & (t < a1)
            hz = np.bincount(idx[w], minlength=conn.n) / ((a1 - a0) / 1000.0)
            mn = np.flatnonzero(conn.neurons.superclass.fillna("").eq(r["mn_superclass"]).to_numpy())
            row.update(_leg_oscillation(r, bs.X, bs.P, bs.H, hz, select(r["stim_types"], types), mn, sample_ms))
        elif r["kind"] == "posture":
            row.update(_posture(r, bs.P, bs.Z, bs.C, sample_ms))
        elif r["kind"] == "mean_rate_hz":
            read = select(r["types"], types)
            read, dropped = _status_excluded(root, conn, read, r.get("exclude_status_containing", []))
            if not len(read):
                raise flyzip.Refused(f"readout types {r['types']} leave no cell")
            hz = counts / (proto["duration_ms"] / 1000.0)
            row.update({"rate_hz": float(hz[read].mean()), "rate_max_hz": float(hz[read].max()),
                        "readout_cells": [str(conn.neurons.instance.iat[i]) for i in read], "excluded": dropped})
        elif r["kind"] == "gf_latency":
            delays = pd.read_csv(root / r["delays_table"], comment="#").set_index("type").delay_ms
            gf = select(r["gf_types"], types)
            mns = {ty: np.flatnonzero(types == ty) for ty in r["mn_types"]}
            watch = np.zeros(conn.n, bool)
            watch[gf] = True
            for v in mns.values():
                watch[v] = True
            w = watch[idx]
            sp = pd.DataFrame({"step": steps[w].astype(int), "cell": idx[w].astype(int)})
            (ev,) = [e for e in stim["events"] if e["kind"] == "kick"]
            s0, per = int(round(ev["start_ms"] / dt)), int(round(ev["period_ms"] / dt))
            kicks = [s0 + i * per for i in range(ev["count"])]
            row.update(_gf_latency(r, sp, dt, gf, mns, kicks, per, {ty: float(delays[ty]) for ty in mns}))
            row["delays_ms"] = {ty: float(delays[ty]) for ty in mns}
        else:
            raise flyzip.Refused(f"readout kind {r['kind']!r} is not built")
        row["wall_s"] = round(time.time() - t0, 1)
        trials.append(row)
        print(f"seed {seed}: {row['spikes']} spikes, {row['wall_s']} s", file=sys.stderr, flush=True)
    if r["kind"] == "mean_rate_hz":
        agg = {"rate_hz_mean": float(np.mean([t["rate_hz"] for t in trials])),
               "rate_hz_per_seed": [t["rate_hz"] for t in trials]}
    elif r["kind"] == "gf_latency":
        if len(trials) != 1:
            raise flyzip.Refused("gf_latency reads one seed (the kicks are its trials)")
        agg = {k: v for k, v in trials[0].items() if "." in k or k == "gf_spike_fraction"}
    else:
        if len(trials) != 1:
            raise flyzip.Refused(f"{r['kind']} reads one seed")
        agg = {k: v for k, v in trials[0].items()
               if k not in ("seed", "spikes", "spikes_sha256", "final_qpos_sha256", "wall_s", "drive_check")}
    conds = judge(proto["pass"], agg)
    if not conds and not proto.get("bar_todo"):
        raise flyzip.Refused(f"protocol {proto['name']} has no pass conditions and no bar_todo")
    verdict = "NO BAR" if not conds else "PASS" if all(x["ok"] for x in conds) else "FAIL"
    out.mkdir(parents=True, exist_ok=True)
    last_reg.write(out / "registry_reads.csv")
    sm = {
        "mode": mode, "root": str(root),
        "zip": {"path": man.get("_zip_path"), "sha256": man["_zip_sha256"], "manifest_sha256": man["_manifest_sha256"],
                "git_commit": man["git_commit"], "layer": man["layer"]} if man else None,
        "tree_git_commit": run._git_head(root) if mode == "tree" else None,
        "protocol": {"name": proto["name"], "item": proto["item"], "file_sha256": shas, "stimulus": proto["stimulus"],
                     "harness": proto["harness"], "settings": s, "profile_source": profile_src,
                     "world_source": world_src, "seeds": proto["seeds"], "duration_ms": proto["duration_ms"],
                     "evidence_status": proto["evidence_status"], "bar_source": proto["bar_source"],
                     "bar_todo": proto.get("bar_todo")},
        "runtime": c["versions"],
        "env": {"dropped": [k for k in os.environ.get("FLYBRAIN_DROPPED_ENV", "").split(",") if k],
                "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED")},
        "body": body,
        "read_guard": {"deny": guard.deny, "deny_inside": guard.deny_inside, "denied": guard.denied,
                       "outside_allowed": sorted(guard.outside)},
        "registry_rows_file": "registry_reads.csv",
        "build_s": round(build_s, 1),
        "trials": trials, "readout": agg, "pass": conds, "verdict": verdict,
    }
    (out / RESULT).write_text(json.dumps(sm, indent=1, default=str))
    print(f"{proto['item']}: {verdict}; " + ("; ".join(f"{x['quantity']} = {x['observed']} ({x['op']} {x['value']})"
                                                      for x in conds) or json.dumps(agg)), file=sys.stderr)
    return 0


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    try:
        return inside(a) if a.inside else run.launch(a, module="flyemu.score", result_file=RESULT)
    except flyzip.Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
