"""The fly_brain.zip entry point (docs/FLY_BRAIN_ZIP.md, "Entry point").

    PYTHONPATH=fly_brain.zip/code python -m flyemu.run fly_brain.zip --world flat_floor --stimulus none \\
        --profile m10f0 --seed 12 --set KEY=V --ms 1000 --out run/
    PYTHONPATH=src python -m flyemu.run --tree . --profile m10f0 --seed 12 --ms 1000 --out run_tree/

1. Checks every member against its sha256 (flyzip.verify) and refuses on any mismatch, missing or extra member.
2. Extracts the members to their runtime paths under a fresh directory and runs a child Python there with only
   that tree's `src` on the path, so Organism is built from the zip's code and data, not the repo's. flygym is
   imported from the zip's body/ copy (the vendored package with its assets) and its mesh cache is pointed at
   the zip's meshes. A read guard records every file the child opens and refuses reads under --deny roots, the
   installed flygym and its mesh cache.
3. Loads the arena and stimulus from world/ (today: flat_floor and none; the rest are declared TODO in the
   manifest and refused here).
4. Refuses any --set key that resolves to no mechanism (model_data.owners over parameters.csv,
   structural_keys.csv and the switch lists of mechanisms.yaml). Absent stubs keep refusing non-neutral values.
5. Writes run_manifest.json (zip and manifest hashes, settings, runtime versions, the read-guard report, spike
   and body-state hashes), registry_reads.csv (every registry read with value, unit, label and source) and
   spikes.npz (step and neuron index of every spike).

--tree runs the same loop from a repo tree (no extraction, no redirect, the profile from code): the reference
for the zip identity check. The loop is the closed-loop smoke loop of scripts/probes/smoke_live.py.

The launcher part uses the standard library only (it is imported from inside the zip).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import flyzip

BUILT_WORLDS = {"flat_floor"}
BUILT_STIMULI = {"none"}
MANIFEST_COPY = ".flybrain_manifest.json"


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the fly from fly_brain.zip")
    ap.add_argument("zip", nargs="?", help="fly_brain.zip (omit with --tree)")
    ap.add_argument("--tree", help="run from this repo tree instead of a zip (reference runs)")
    ap.add_argument("--world", default=None)
    ap.add_argument("--stimulus", default=None)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--min-synapses", type=int, default=None)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=V")
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--deny", action="append", default=[], help="refuse any read under this root (repeatable)")
    ap.add_argument("--workdir", help="extraction directory (new or empty); default a fresh temp dir")
    ap.add_argument("--keep", action="store_true", help="keep the extracted tree")
    ap.add_argument("--allow-runtime-mismatch", action="store_true")
    ap.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--root", help=argparse.SUPPRESS)
    return ap


# --- launcher (standard library only) ------------------------------------------------------------------

def launch(a, module: str = "flyemu.run", result_file: str = "run_manifest.json") -> int:
    """Verify and extract the zip (or take --tree), then run `python -m <module> --inside` in that tree."""
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / result_file).exists():
        raise flyzip.Refused(f"{out} already holds a result ({result_file})")
    env = {k: v for k, v in os.environ.items() if not k.startswith("FLYEMU_") and k != "PYTHONPATH"}
    dropped = sorted(k for k in os.environ if k.startswith("FLYEMU_"))
    if a.tree:
        root, mode, tmp = Path(a.tree).resolve(), "tree", None
    else:
        if not a.zip:
            raise flyzip.Refused("give fly_brain.zip or --tree")
        t0 = time.time()
        man = flyzip.verify(a.zip)
        print(f"verified {len(man['members'])} members in {time.time() - t0:.0f} s; zip sha256 "
              f"{man['_zip_sha256'][:16]}", file=sys.stderr)
        tmp = None if a.workdir else tempfile.mkdtemp(prefix="flybrain_")
        root = Path(a.workdir or tmp).resolve()
        flyzip.extract(a.zip, root, man)
        man["_zip_path"] = str(Path(a.zip).resolve())
        (root / MANIFEST_COPY).write_text(json.dumps(man))
        mode = "zip"
        env["FLYGYM_ASSET_CACHE_DIR"] = str(root / "body" / "flygym_assets")
    env["PYTHONPATH"] = str(root / "src")
    passthrough = [x for x in sys.argv[1:] if x != a.zip] if a.zip else sys.argv[1:]
    # the child runs in the tree, so it gets the absolute output path (argparse keeps the last --out)
    cmd = [sys.executable, "-m", module, "--inside", "--root", str(root), *passthrough, "--out", str(out)]
    env["FLYBRAIN_DROPPED_ENV"] = ",".join(dropped)
    env.setdefault("PYTHONHASHSEED", "0")           # set and str iteration order fixed across processes
    try:
        return subprocess.run(cmd, cwd=root, env=env).returncode
    finally:
        if tmp and not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)


# --- inside the extracted (or repo) tree ----------------------------------------------------------------

def _native_wrappers(guard: flyzip.ReadGuard) -> None:
    """pyarrow and MuJoCo open files in C; route their paths through the guard."""
    import mujoco
    import pyarrow.parquet as pq
    rt, pf_init, xp = pq.read_table, pq.ParquetFile.__init__, mujoco.MjModel.from_xml_path

    def chk(src):
        if isinstance(src, (str, os.PathLike)):
            guard.check(os.path.realpath(os.fspath(src)))

    def read_table(source, *x, **k):
        chk(source)
        return rt(source, *x, **k)

    def parquet_file(self, source, *x, **k):
        chk(source)
        return pf_init(self, source, *x, **k)

    def from_xml_path(path, *x, **k):
        chk(path)
        return xp(path, *x, **k)
    pq.read_table, pq.ParquetFile.__init__ = read_table, parquet_file
    mujoco.MjModel.from_xml_path = staticmethod(from_xml_path)


def _check_flygym(root: Path) -> dict:
    """The body must come from the zip: flygym imported from root/src/flygym (vendored package and its assets),
    meshes from root/body/flygym_assets."""
    import flygym
    from flygym.utils.assets_lazy_loading import get_cache_root
    got = {"package": str(Path(flygym.__file__).resolve().parent), "assets_dir": str(Path(flygym.assets_dir).resolve()),
           "mesh_cache": str(Path(get_cache_root()).resolve())}
    for k, v in got.items():
        if root not in Path(v).parents:
            raise flyzip.Refused(f"flygym {k} is {v}, outside the zip")
    return got


def _world(root: Path, mode: str, name: str):
    import dataclasses

    import numpy as np

    from .world import World
    if name not in BUILT_WORLDS:
        raise flyzip.Refused(f"world {name!r} is not built (declared TODO in the manifest); "
                             f"built: {sorted(BUILT_WORLDS)}")
    if mode == "tree":
        return World(), "flyemu.world.World() defaults"
    doc = json.loads((root / "world" / "arenas" / f"{name}.json").read_text())
    kw = {}
    for f in dataclasses.fields(World):
        v = doc["world"][f.name]
        default = f.default_factory() if f.default_factory is not dataclasses.MISSING else f.default
        kw[f.name] = np.asarray(v, dtype=float) if isinstance(default, np.ndarray) else v
    if kw["odours"] or kw["food"]:
        raise flyzip.Refused("odour sources and food patches in arena files are not built yet")
    return World(**kw), f"world/arenas/{name}.json"


def _check_sets(sets: dict) -> dict:
    from . import model_data
    mdat = model_data.load()
    owned, orphans = {}, []
    for k in sets:
        o = model_data.owners(mdat, k)
        if o:
            owned[k] = sorted({m for *_, m in o})
        else:
            orphans.append(k)
    if orphans:
        raise flyzip.Refused(f"--set key(s) with no mechanism in mechanisms.yaml / parameters.csv / "
                             f"structural_keys.csv: {orphans}")
    return owned


def _versions() -> dict:
    import importlib.metadata as md
    import platform
    from .pack import RUNTIME_PACKAGES
    return {"python": platform.python_version(), "platform": f"{sys.platform} {platform.machine()}",
            "packages": {p: md.version(p) for p in RUNTIME_PACKAGES}}


def child_setup(a) -> dict:
    """Inside the extracted (or repo) tree: install the read guard, then check that flyemu, flygym and the
    runtime are the zip's. Shared by run and check."""
    root = Path(a.root).resolve()
    mode = "tree" if a.tree else "zip"
    man = json.loads((root / MANIFEST_COPY).read_text()) if mode == "zip" else None
    allowed = [root, sys.prefix, sys.base_prefix]
    deny_inside = []
    if mode == "zip":                               # the installed flygym and its mesh cache are the repo's body
        import sysconfig
        deny_inside = [str(Path(sysconfig.get_paths()["purelib"]) / "flygym"),
                       os.path.expanduser("~/.cache/flygym_assets")]
    guard = flyzip.ReadGuard(allowed, a.deny, deny_inside).install()
    _native_wrappers(guard)
    import flyemu
    if root not in Path(flyemu.__file__).resolve().parents:
        raise flyzip.Refused(f"flyemu imported from {flyemu.__file__}, not from {root}")
    versions = _versions()
    if man:
        pins = {k: v for k, v in man["runtime_pins"].items() if k != "vendored"}
        if {k: v for k, v in versions.items() if k != "vendored"} != pins and not a.allow_runtime_mismatch:
            raise flyzip.Refused(f"runtime {versions} differs from the zip's pins {man['runtime_pins']}")
    body_src = _check_flygym(root) if mode == "zip" else None
    return {"root": root, "mode": mode, "man": man, "guard": guard, "versions": versions, "body_src": body_src}


def load_profile(root: Path, mode: str, profile: str) -> str:
    """In zip mode the profile comes from the zip's profiles/<name>.json, not from the code; returns its source."""
    if mode != "zip":
        return "flyemu.profiles (code)"
    from . import profiles
    from .registry import Status
    pdoc = json.loads((root / "profiles" / f"{profile}.json").read_text())
    profiles.PROFILES[profile] = {"kick_mv": pdoc["kick_mv"],
                                  "values": {r["key"]: (r["value"], Status(r["label"]), r["why"])
                                             for r in pdoc["values"]}}
    return f"profiles/{profile}.json"


def inside(a) -> int:
    c = child_setup(a)
    root, mode, man, guard, versions, body_src = (c[k] for k in ("root", "mode", "man", "guard", "versions",
                                                               "body_src"))
    d = man["defaults"] if man else {"profile": "m10f0", "seed": 12, "min_synapses": 5, "world": "flat_floor",
                                     "stimulus": "none", "timestep_ms": 0.1, "policy": "minimal"}
    profile = a.profile or d["profile"]
    seed = d["seed"] if a.seed is None else a.seed
    min_syn = d["min_synapses"] if a.min_synapses is None else a.min_synapses
    world_name, stim = a.world or d["world"], a.stimulus or d["stimulus"]
    out = Path(a.out).resolve()
    if stim not in BUILT_STIMULI:
        raise flyzip.Refused(f"stimulus {stim!r} is not built (declared TODO in the manifest); "
                             f"built: {sorted(BUILT_STIMULI)}")
    world, world_src = _world(root, mode, world_name)
    sets = {k: float(v) for k, v in (s.split("=", 1) for s in a.set)}
    set_owners = _check_sets(sets)

    import numpy as np

    from .organism import Organism
    profile_src = load_profile(root, mode, profile)
    t_build = time.time()
    org = Organism(policy=d["policy"], timestep_ms=d["timestep_ms"], profile=profile, min_synapses=min_syn,
                   overrides=sets, seed=seed, world=world)
    build_s = time.time() - t_build
    mesh_files = []
    for mesh in org.body.fly.mjcf_root.meshes:
        f = getattr(mesh, "file", None)
        if f:
            mesh_files.append(os.path.realpath(f))
    if mode == "zip":
        outside = [f for f in mesh_files if root not in Path(f).parents]
        if outside:
            raise flyzip.Refused(f"{len(outside)} mesh file(s) outside the zip, e.g. {outside[0]}")
    m, dd = org.body.sim.mj_model, org.body.sim.mj_data
    steps_n = int(round(a.ms / org.timestep_ms))
    st, ix, runaway = [], [], None
    t0 = time.time()
    for s in range(steps_n):
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        if sp.size > 20000:
            runaway = s * org.timestep_ms
            break
        if sp.size:
            st.append(np.full(sp.size, s, np.int32))
            ix.append(np.asarray(sp, np.int32))
        org.motor_step(sp)
        if (s + 1) % 1000 == 0:
            print(f"{(s + 1) * org.timestep_ms:.0f} ms, {time.time() - t0:.0f} s", file=sys.stderr, flush=True)
    wall = time.time() - t0
    steps = np.concatenate(st) if st else np.zeros(0, np.int32)
    idx = np.concatenate(ix) if ix else np.zeros(0, np.int32)
    out.mkdir(parents=True, exist_ok=True)
    body_ids = org.conn.neurons.bodyId.to_numpy()
    np.savez_compressed(out / "spikes.npz", step=steps, neuron=idx, body_id=body_ids[idx],
                        timestep_ms=org.timestep_ms)
    org.reg.write(out / "registry_reads.csv")
    qpos = np.ascontiguousarray(dd.qpos, dtype=np.float64)
    rm = {
        "mode": mode, "root": str(root),
        "zip": {"path": man.get("_zip_path"), "sha256": man["_zip_sha256"], "manifest_sha256": man["_manifest_sha256"],
                "git_commit": man["git_commit"], "layer": man["layer"]} if man else None,
        "tree_git_commit": _git_head(root) if mode == "tree" else None,
        "settings": {"profile": profile, "profile_source": profile_src, "seed": seed, "min_synapses": min_syn,
                     "world": world_name, "world_source": world_src, "stimulus": stim, "ms": a.ms,
                     "timestep_ms": org.timestep_ms, "policy": d["policy"], "set": sets, "set_mechanisms": set_owners},
        "runtime": versions,
        "env": {"dropped": [k for k in os.environ.get("FLYBRAIN_DROPPED_ENV", "").split(",") if k],
                "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
                "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS",
                                                           "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}},
        "body": {"source": body_src, "meshes": len(mesh_files),
                 "mesh_dirs": sorted({str(Path(f).parent) for f in mesh_files}), "nq": int(m.nq),
                 "final_qpos_sha256": flyzip.sha256_bytes(qpos.tobytes()),
                 "mujoco_warnings": int(sum(w.number for w in dd.warning))},
        "read_guard": {"deny": guard.deny, "deny_inside": guard.deny_inside, "denied": guard.denied,
                       "outside_allowed": sorted(guard.outside)},
        "registry": {**org.reg.summary(), "rows_file": "registry_reads.csv"},
        "result": {"steps": steps_n if runaway is None else int(runaway / org.timestep_ms), "runaway_at_ms": runaway,
                   "spikes": int(idx.size), "neurons": int(org.conn.n),
                   "spikes_sha256": flyzip.sha256_bytes(steps.tobytes() + idx.tobytes()),
                   "nan_state": bool(not np.isfinite(dd.qpos).all() or not np.isfinite(org.net.v).all()),
                   "build_s": round(build_s, 1), "wall_s": round(wall, 1)},
    }
    by = rm["registry"].get("by_status")
    if by:
        rm["registry"]["by_status"] = {k: {kk: int(vv) for kk, vv in v.items()} for k, v in by.items()}
    (out / "run_manifest.json").write_text(json.dumps(rm, indent=1, default=str))
    print(json.dumps(rm["result"]))
    return 0


def _git_head(root: Path) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    try:
        return inside(a) if a.inside else launch(a)
    except flyzip.Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
