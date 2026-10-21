"""Pack the species layer into fly_brain.zip (docs/FLY_BRAIN_ZIP.md, "Contents of fly_brain.zip").

    .venv/bin/python -m flyemu.pack --out fly_brain.zip          (from the repo root, with src on the path)

Repo members come from git-tracked files only, and the tree must be clean for them (or --allow-dirty, which
the manifest records). External members (the connectome cache, the CT1 extract, the flygym body assets and
mesh cache) are hashed and pinned; the male-cns neuron and edge hashes are checked against the pins the T1
fill recorded. Generated members: profiles/*.json (each named parameter set as explicit KEY=value rows with
labels), world/ (only what exists today; the rest is declared TODO in the manifest, not written), and
register.json (the sealed/held-out register from docs/HANDOFF.md).

The member list was checked against what an m10f0 build actually reads (scripts/probes/zip_trace_inputs.py).
The zip carries no clock time, so the same commit and inputs give the same bytes.
"""
from __future__ import annotations

import argparse
import dataclasses
import importlib.metadata as md
import json
import platform
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from . import flyzip

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "data" / "cache"
ANNOTATIONS = ("male_cns_extra.parquet", "male_cns_extra2.parquet", "male_cns_hemilineage.parquet",
               "male_cns_sensorimotor_roiinfo.parquet", "photoreceptor_terminals.parquet", "landmarks.json")
INFERRED = ("t1_fill.json", "t1_fill.csv.gz", "t1_add.json", "t1_add.csv.gz", "gap_junctions.csv")
LEDGER = ("blank_ledger.csv", "ledger_levels.csv", "blanks_audit_coverage.csv")
CT1_RAW = REPO / "data" / "raw" / "ct1_columns_s14"
# passive_rest_protocol: imported by passive.projected_matrices at build; blank_ledger: run by flyemu.check
CODE_EXTRA = ("scripts/passive_rest_protocol.py", "scripts/blank_ledger.py")
RUNTIME_PACKAGES = ("numpy", "scipy", "pandas", "pyarrow", "mujoco", "PyYAML", "numba", "matplotlib", "pillow")
VENDORED = ("flygym",)                 # shipped inside the zip (body/flygym), so not a runtime pin
DEFAULTS = {"profile": "m10f0", "seed": 12, "min_synapses": 5, "world": "flat_floor", "stimulus": "none",
            "timestep_ms": 0.1, "policy": "minimal"}

GROUPS = {
    "code": "the simulator, pinned (n/a)",
    "connectome": "measured (male-cns v1.0 via neuPrint); the >= min_synapses cut is a run setting, not baked in",
    "annotations": "measured (male-cns v1.0 annotation tables)",
    "inferred": "inferred graph transforms; each json names its rule, sources, hashes and switch; never "
                "overwrites connectome/",
    "params": "per row: measured / derived / inferred / guessed / fitted, with source",
    "derived": "derived tables; per row as each file states",
    "model": "per row (parameters.csv basis columns; mechanisms.yaml status)",
    "ledger": "n/a (the blank ledger and the ontology it is built from)",
    "measurements": "measured, cited in the file",
    "datasets": "n/a (dataset and external-code manifest)",
    "profiles": "per KEY: the profile's own label (fitted values are labelled inferred, as the registry does)",
    "body": ("measured geometry (flybody meshes and MJCF-side tables, built by the vendored flygym 2.1.0 "
             "package); masses and inertias as in the registry"),
    "world": "a protocol, not a fly quantity",
    "tests": "n/a",
    "register": "n/a",
}

WORLD_TODO = [
    {"item": "world/arenas/ball.xml", "what": "air-supported ball", "today": "not built"},
    {"item": "world/arenas/flight_tether.xml", "what": "flight tether",
     "today": "flight probes fix the thorax in code (flight.py); no arena file"},
    {"item": "world/arenas/sugar_patch.xml", "what": "sugar patch", "today": "extrasenses.FoodPatch, set in code"},
    {"item": "world/stimuli/full_field_flash.yaml", "today": "scripts/probes (code)"},
    {"item": "world/stimuli/moving_grating.yaml", "today": "scripts/probes (code)"},
    {"item": "world/stimuli/looming_disc.yaml", "today": "scripts/probes (code)"},
    {"item": "world/stimuli/leg_sugar.yaml", "today": "scripts/probes (code); the same form as "
     "world/stimuli/labellar_sugar_100hz.json, waiting for its protocol bar (world/scoreboard.json)"},
    {"item": "world/stimuli/bitter.yaml", "today": "scripts/probes (code)"},
    {"item": "world/stimuli/odour_pulse.yaml", "today": "world.OdourSource, set in code"},
    {"item": "world/stimuli/dn_current_injection.yaml", "today": "scripts/probes/bypass_* (code)"},
    {"item": "world/stimuli/mn_current_injection.yaml", "today": "scripts/probes (code)"},
]
OTHER_TODO = [
    {"item": "variation/*.csv", "what": "the variation model (between-fly spread per slot class)", "today": "unbuilt"},
    {"item": "individual/*.parquet", "what": "individual layer only; this zip is species layer", "today": "n/a"},
    {"item": "slot addresses", "what": "cell:/synapse:/body: addresses for per-element values",
     "today": "registry keys are entity|property at type/class grain only"},
]


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True, text=True).stdout


def tracked(prefix: str) -> list[str]:
    return sorted(p for p in git("ls-files", "--", prefix).splitlines() if p)


def file_members() -> list[dict]:
    """Every member that is a file on disk: path in zip, runtime path, group, source file."""
    out = []

    def add(path, runtime, group, src, origin):
        out.append({"path": path, "runtime": runtime, "group": group, "_src": Path(src), "origin": origin})
    for p in tracked("src/flyemu"):
        if p.endswith(".py"):
            add("code/flyemu/" + p[len("src/flyemu/"):], p, "code", REPO / p, "git")
    for p in CODE_EXTRA:
        add("code/" + p, p, "code", REPO / p, "git")
    add("connectome/neurons.parquet", "data/cache/male_cns_neurons.parquet", "connectome",
        CACHE / "male_cns_neurons.parquet", "external")
    add("connectome/edges.parquet", "data/cache/male_cns_edges.parquet", "connectome",
        CACHE / "male_cns_edges.parquet", "external")
    for f in sorted(CT1_RAW.iterdir()):
        add(f"connectome/ct1_columns_s14/{f.name}", f"data/raw/ct1_columns_s14/{f.name}", "connectome", f, "external")
    for name in ANNOTATIONS:
        add(f"annotations/{name}", f"data/cache/{name}", "annotations", CACHE / name, "external")
    for p in tracked("data/params"):
        name = p[len("data/params/"):]
        group = "inferred" if name in INFERRED else "params"
        add(f"{group}/{name}", p, group, REPO / p, "git")
    for p in tracked("data/derived"):
        name = p[len("data/derived/"):]
        group = "ledger" if name in LEDGER else "derived"
        add(f"{group}/{name}", p, group, REPO / p, "git")
    for p in tracked("data/ontology"):
        add("ledger/" + p[len("data/ontology/"):], p, "ledger", REPO / p, "git")
    for p in tracked("data/model"):
        add("model/" + p[len("data/model/"):], p, "model", REPO / p, "git")
    for p in tracked("data/world"):                 # scoreboard protocols, their stimuli, the scoreboard
        add("world/" + p[len("data/world/"):], p, "world", REPO / p, "git")
    for p in tracked("data/measurements"):
        add("measurements/" + p[len("data/measurements/"):], p, "measurements", REPO / p, "git")
    add("datasets.yaml", "data/MANIFEST.yaml", "datasets", REPO / "data/MANIFEST.yaml", "git")
    for p in tracked("tests"):
        add(p, p, "tests", REPO / p, "git")
    # the body: the flygym package itself (pure Python, Apache-2.0; its packaged MJCF-side yaml, pose and
    # vision assets inside) and the fullsize flybody meshes it downloads to its cache. run.py imports this
    # copy ahead of the installed one and points the mesh cache at body/flygym_assets.
    import importlib.metadata as imd

    import flygym
    from flygym.compose.fly.flybody import FLYBODY_FULLSIZE_MESH_DIR
    from flygym.utils.assets_lazy_loading import get_cache_root
    pkg = Path(flygym.__file__).parent
    for f in sorted(pkg.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            rel = f.relative_to(pkg).as_posix()
            add(f"body/flygym/{rel}", f"src/flygym/{rel}", "body", f, "external")
    lic = next(f for f in imd.distribution("flygym").files if f.name == "LICENSE")
    add("body/flygym/LICENSE", "src/flygym/LICENSE", "body", lic.locate(), "external")
    mesh_dir = get_cache_root() / FLYBODY_FULLSIZE_MESH_DIR
    if not mesh_dir.is_dir():
        raise flyzip.Refused(f"flybody meshes not cached at {mesh_dir}; build the body once to fetch them")
    for f in sorted(mesh_dir.iterdir()):
        if f.is_file():
            rel = f"body/flygym_assets/{FLYBODY_FULLSIZE_MESH_DIR}/{f.name}"
            add(rel, rel, "body", f, "external")
    return out


def profile_members() -> tuple[list[tuple[str, bytes]], dict]:
    from . import model_data, profiles
    mdat = model_data.load()
    out, coverage = [], {}
    for name, prof in profiles.PROFILES.items():
        rows, orphans = [], []
        for k, (v, status, why) in prof["values"].items():
            rows.append({"key": k, "value": v, "label": str(getattr(status, "value", status)), "why": why})
            if not model_data.owners(mdat, k):
                orphans.append(k)
        doc = {"name": name, "kick_mv": prof["kick_mv"], "values": rows,
               "note": "applied with setdefault, so a --set of the same key wins (profiles.apply)"}
        out.append((f"profiles/{name}.json", json.dumps(doc, indent=1).encode()))
        coverage[name] = {"keys": len(rows), "keys_without_owner": orphans}
    return out, coverage


def world_members() -> list[tuple[str, bytes]]:
    from .world import World

    def plain(x):
        return x.tolist() if hasattr(x, "tolist") else x
    w = {k: plain(v) for k, v in dataclasses.asdict(World()).items()}
    arena = {"name": "flat_floor", "status": "built",
             "what": "flygym flat ground as body.Body builds it (the default resting world of every gate and "
                     "smoke run) with flyemu.world.World at these field values",
             "world": w}
    return [("world/arenas/flat_floor.json", json.dumps(arena, indent=1).encode())]   # stimuli: data/world


def register_member() -> tuple[str, bytes]:
    """The sealed / held-out register table from docs/HANDOFF.md, as rows."""
    text = (REPO / "docs" / "HANDOFF.md").read_text()
    sec = text.split("## Sealed and held-out data register", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in sec.splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*-", line) and not line.startswith("| Data |"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 3:
                rows.append({"data": cells[0], "status": cells[1], "rule": cells[2]})
    doc = {"source": "docs/HANDOFF.md, 'Sealed and held-out data register'", "rows": rows}
    return "register.json", json.dumps(doc, indent=1).encode()


def dataset_pins(hashes: dict) -> dict:
    t1f = json.loads((REPO / "data/params/t1_fill.json").read_text())
    t1a = json.loads((REPO / "data/params/t1_add.json").read_text())
    n, e = hashes["connectome/neurons.parquet"], hashes["connectome/edges.parquet"]
    pin = t1f["mcns"]
    if (n, e) != (pin["neurons_sha256"], pin["edges_sha256"]):
        raise flyzip.Refused("male-cns neuron/edge hashes differ from the pins in data/params/t1_fill.json")
    return {
        "male_cns": {"dataset": "neuPrint male-cns:v1.0 (data/MANIFEST.yaml)", "neurons_sha256": n,
                     "edges_sha256": e, "matches_t1_fill_pin": True},
        "manc": {"source": "Pugliese_cpg_2025 bundle (data/MANIFEST.yaml)",
                 **{k: t1f["manc"][k] for k in ("W", "W_sha256", "table", "table_sha256")},
                 "typepair_sha256": t1a.get("manc_typepair_sha256")},
        "banc": {"source": "Pugliese_cpg_2025 bundle (data/MANIFEST.yaml)",
                 **{k: t1f["banc"][k] for k in ("W", "W_sha256", "table", "table_sha256")}},
        "raw_data": "data/raw (about 7.3 GB) stays out; cited by the hashes above and data/MANIFEST.yaml",
    }


def runtime_pins() -> dict:
    return {"python": platform.python_version(), "platform": f"{sys.platform} {platform.machine()}",
            "packages": {p: md.version(p) for p in RUNTIME_PACKAGES},
            "vendored": {p: {"version": md.version(p), "license": md.metadata(p).get("License-Expression")}
                         for p in VENDORED}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-dirty", action="store_true", help="pack modified tracked files (recorded)")
    a = ap.parse_args(argv)
    commit = git("rev-parse", "HEAD").strip()
    paths = ["src/flyemu", "data/params", "data/derived", "data/ontology", "data/model", "data/world", "data/measurements",
             "data/MANIFEST.yaml", "tests", *CODE_EXTRA, "docs/HANDOFF.md"]
    dirty = [ln for ln in git("status", "--porcelain", "--", *paths).splitlines() if ln]
    if dirty and not a.allow_dirty:
        raise flyzip.Refused(f"{len(dirty)} packed path(s) differ from {commit[:7]}; commit or pass --allow-dirty: "
                             + "; ".join(dirty[:5]))
    files = file_members()
    prof, prof_cov = profile_members()
    gen = [*prof, *world_members(), register_member()]
    names = [m["path"] for m in files] + [p for p, _ in gen]
    dup = sorted({p for p in names if names.count(p) > 1})
    if dup:
        raise flyzip.Refused(f"{len(dup)} member path(s) packed twice: {dup[:5]}")
    members, hashes = [], {}
    out = Path(a.out)
    tmp = out.with_suffix(out.suffix + ".partial")
    with zipfile.ZipFile(tmp, "w", allowZip64=True) as zf:
        for m in sorted(files, key=lambda m: m["path"]):
            data = m["_src"].read_bytes()
            flyzip.write_member(zf, m["path"], data)
            h = flyzip.sha256_bytes(data)
            hashes[m["path"]] = h
            members.append({"path": m["path"], "runtime": m["runtime"], "group": m["group"], "origin": m["origin"],
                            "sha256": h, "bytes": len(data)})
        for path, data in sorted(gen):
            flyzip.write_member(zf, path, data)
            group = path.split("/")[0] if "/" in path else "register"
            members.append({"path": path, "runtime": path, "group": group, "origin": "generated",
                            "sha256": flyzip.sha256_bytes(data), "bytes": len(data)})
        man = {
            "schema": flyzip.SCHEMA, "layer": "species", "spec": "docs/FLY_BRAIN_ZIP.md rev 2",
            "git_commit": commit, "git_dirty": dirty,
            "defaults": DEFAULTS,
            "dataset_pins": dataset_pins(hashes),
            "runtime_pins": runtime_pins(),
            "groups": {g: {"label_rule": r, "members": sum(m["group"] == g for m in members),
                           "bytes": sum(m["bytes"] for m in members if m["group"] == g)} for g, r in GROUPS.items()},
            "profile_key_coverage": prof_cov,
            "todo": {"world": WORLD_TODO, "other": OTHER_TODO},
            "members": members,
        }
        flyzip.write_member(zf, flyzip.MANIFEST, json.dumps(man, indent=1).encode())
    tmp.replace(out)
    ver = flyzip.verify(out)
    print(json.dumps({"out": str(out), "zip_bytes": out.stat().st_size, "zip_sha256": ver["_zip_sha256"],
                      "members": len(members), "unpacked_bytes": sum(m["bytes"] for m in members),
                      "git_commit": commit, "dirty": len(dirty),
                      "groups": {g: v["bytes"] for g, v in man["groups"].items()}}, indent=1))


if __name__ == "__main__":
    main()
