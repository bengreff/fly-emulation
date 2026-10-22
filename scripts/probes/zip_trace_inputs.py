"""Which files does a model build actually read? (s22 fly2, fly_brain.zip packer input check.)

Builds Organism (default: m10f0, seed 12, >= 5 synapses) and steps the smoke loop a few times, recording
every file the process opens or lists: Python audit events ("open", "os.listdir", "os.scandir", "glob.glob")
plus wrappers on the readers that open files natively (pyarrow parquet, MuJoCo XML). Writes the sorted list
grouped by root (repo, the flygym package, the flygym mesh cache, other). The packer's member list is
checked against it: every repo/body file read here must be a zip member.

    .venv/bin/python scripts/probes/zip_trace_inputs.py --profile m10f0 --steps 20 --out /tmp/zip_trace.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")

SEEN: dict[str, set] = {"open": set(), "list": set()}


def _hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        p = os.fsdecode(args[0])
        SEEN["open"].add(os.path.realpath(p) if os.path.isabs(p) else os.path.realpath(os.path.join(os.getcwd(), p)))
    elif event in ("os.listdir", "os.scandir", "glob.glob") and args and isinstance(args[0], (str, bytes, os.PathLike)):
        SEEN["list"].add(os.path.realpath(os.fsdecode(args[0])))


def _wrap_native_readers():
    import pyarrow.parquet as pq
    orig_rt, orig_pf = pq.read_table, pq.ParquetFile.__init__

    def read_table(source, *a, **k):
        if isinstance(source, (str, os.PathLike)):
            SEEN["open"].add(os.path.realpath(os.fspath(source)))
        return orig_rt(source, *a, **k)

    def pf_init(self, source, *a, **k):
        if isinstance(source, (str, os.PathLike)):
            SEEN["open"].add(os.path.realpath(os.fspath(source)))
        return orig_pf(self, source, *a, **k)
    pq.read_table, pq.ParquetFile.__init__ = read_table, pf_init
    import mujoco
    orig_xp = mujoco.MjModel.from_xml_path

    def from_xml_path(path, *a, **k):
        SEEN["open"].add(os.path.realpath(os.fspath(path)))
        return orig_xp(path, *a, **k)
    mujoco.MjModel.from_xml_path = staticmethod(from_xml_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f0")
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    _wrap_native_readers()
    sys.addaudithook(_hook)
    from flyemu.organism import Organism
    org = Organism(policy="minimal", profile=a.profile, min_synapses=5, seed=a.seed)
    for s in range(a.steps):
        obs = org.body.observe()
        sp = org.net.step(external_mv=org.sense(s, obs))
        org.motor_step(sp)
    repo = os.path.realpath(".")
    main_repo = os.path.realpath("data/cache/..")          # data/cache is a symlink into the shared checkout
    import flygym
    pkg = os.path.realpath(os.path.dirname(flygym.__file__))
    cache = os.path.realpath(os.path.expanduser("~/.cache/flygym_assets"))
    # first match wins: the package and venv sit inside the shared checkout, the worktree too
    roots = {"flygym_pkg": pkg, "flygym_cache": cache, "python": os.path.realpath(sys.prefix),
             "base_python": os.path.realpath(sys.base_prefix), "repo": repo,
             "shared_checkout": os.path.realpath(main_repo + "/..")}

    def group(paths):
        out = {k: [] for k in roots} | {"other": []}
        for p in sorted(paths):
            for k, r in roots.items():
                if p.startswith(r + os.sep):
                    out[k].append(os.path.relpath(p, r))
                    break
            else:
                out["other"].append(p)
        return out
    res = {"profile": a.profile, "seed": a.seed, "steps": a.steps, "roots": roots,
           "opened": group(p for p in SEEN["open"] if os.path.isfile(p)),
           "listed": group(SEEN["list"])}
    for kind in ("opened", "listed"):
        res[kind]["python"] = len(res[kind]["python"])          # stdlib and site-packages: counted only
        res[kind]["base_python"] = len(res[kind]["base_python"])
    Path(a.out).write_text(json.dumps(res, indent=1))
    print({k: (len(v) if isinstance(v, list) else v) for k, v in res["opened"].items()})


if __name__ == "__main__":
    main()
