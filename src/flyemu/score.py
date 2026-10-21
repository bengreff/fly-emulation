"""python -m flyemu.score: play one scoreboard protocol from a fly_brain.zip (docs/FLY_BRAIN_ZIP.md, "Scoreboard").

    PYTHONPATH=fly_brain.zip/code python -m flyemu.score fly_brain.zip --protocol per_labellar_sugar --out s/
    PYTHONPATH=src python -m flyemu.score --tree . --protocol per_labellar_sugar --out s_tree/   # the reference

A protocol (world/protocols/<name>.json) names the brain build, settings, seeds, duration, a stimulus
(world/stimuli/<name>.json: timed events on cell types), a readout and its pass conditions. This module only
interprets them; every number is in the files. Launch, extraction and the read guard are flyemu.run's.

Harnesses (both step only the network; the body is never stepped):
- build "assay": the brain as scripts/assay_pathways.py builds it, a fresh lif.Network per seed;
- build "organism": flyemu.organism.Organism, as scripts/probes/gf_latency.py builds it.
Stimulus events: "poisson_kick" (each listed cell gets an independent Poisson train of kicks while on) and
"kick" (a fixed train of kicks). Readouts: "mean_rate_hz" and "gf_latency".

Writes score_manifest.json (per seed: spike count and hash over every neuron, readout; the aggregate readout,
each pass condition and the verdict) and registry_reads.csv. Exit code 0 whether the protocol passes or fails;
2 on refusal.
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

def judge(conds: list[dict], q: dict) -> list[dict]:
    out = []
    for c in conds:
        names = c["quantity"] if isinstance(c["quantity"], list) else [c["quantity"]]
        for n in names:
            if n not in q:
                raise flyzip.Refused(f"pass condition names {n!r}, which the readout does not produce")
        vals = [q[n] for n in names]
        v, op = c["value"], c["op"]
        if op == "present_all_in":
            got = [x for x in vals if x is not None]
            ok = bool(got) and all(v[0] <= x <= v[1] for x in got)
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
    elif build != "organism":
        raise flyzip.Refused(f"harness build {build!r} is not built")
    build_s = time.time() - t_build
    for seed in proto["seeds"]:
        t0 = time.time()
        if build == "organism":
            world, world_src = run._world(root, mode, s["arena"])
            org = _build_organism(s, seed, world)
            reg, conn, kick_mv, net = org.reg, org.conn, org.kick_mv, org.net
            last_reg = reg
            body = {"source": c["body_src"], "nq": int(org.body.sim.mj_model.nq), "stepped": False}
        else:
            net = network(seed)
        types = conn.neurons.type.fillna("").to_numpy()
        sched = Schedule(stim, types, dt, n_steps, kick_mv)
        rng = np.random.default_rng(seed + proto["stimulus_rng_offset"])
        counts = np.zeros(conn.n, np.int32)
        st, ix = [], []
        for step in range(n_steps):
            spk = net.step(kick=sched.kick(step, rng))
            if spk.size:
                counts[spk] += 1
                st.append(np.full(spk.size, step, np.int32))
                ix.append(np.asarray(spk, np.int32))
        steps = np.concatenate(st) if st else np.zeros(0, np.int32)
        idx = np.concatenate(ix) if ix else np.zeros(0, np.int32)
        row = {"seed": seed, "spikes": int(idx.size), "spikes_sha256": flyzip.sha256_bytes(steps.tobytes() + idx.tobytes())}
        if r["kind"] == "mean_rate_hz":
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
    else:
        if len(trials) != 1:
            raise flyzip.Refused("gf_latency reads one seed (the kicks are its trials)")
        agg = {k: v for k, v in trials[0].items() if "." in k or k == "gf_spike_fraction"}
    conds = judge(proto["pass"], agg)
    verdict = "PASS" if all(x["ok"] for x in conds) else "FAIL"
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
                     "evidence_status": proto["evidence_status"], "bar_source": proto["bar_source"]},
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
    print(f"{proto['item']}: {verdict}; " + "; ".join(f"{x['quantity']} = {x['observed']} ({x['op']} {x['value']})"
                                                     for x in conds), file=sys.stderr)
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
