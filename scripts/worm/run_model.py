"""Run the worm model as it stands, closed loop, and put the run in the viewer.

Nothing is prescribed: the brain (brain.py) drives the body's muscles and the body's sensing feeds the brain back.
Every number is at its ledger template (sample_worm(None)); every toggle is at its ledger default except
receptor_sign, which is on because it carries the known synapse signs (Fenyves 2020 published polarity, Roberts
2016 measured AVA/AVB and ASH->AVB inhibition). Body: the worm-scale agar world (AGAR_FILM) with the published
diacetyl cone field (BODY_TESTS.md, MB11).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/run_model.py [seconds] [run_id]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))

from wormemu.brain import Brain, sample_worm  # noqa: E402
from wormemu.body.loop import Body, run  # noqa: E402
from wormemu.body.metaworm import AGAR_FILM  # noqa: E402
from wormemu.body.scene import ChemotaxisScene  # noqa: E402

seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
rid = sys.argv[2] if len(sys.argv) > 2 else "model"
out = ROOT / "runs" / "worm" / "metaworm" / rid
out.parent.mkdir(parents=True, exist_ok=True)

commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True,
                        text=True).stdout.strip()
brain = Brain(sample_worm(None), toggles=dict(receptor_sign="on"))
toggles = dict(brain.toggles)
body = Body(out, scene=ChemotaxisScene(field="cone_published"), frame_every=8, world=AGAR_FILM)
meta = run(brain, body, seconds, brain_config={"seed": None, "toggles": toggles, "commit": commit})

on = sorted(k for k, v in toggles.items() if v not in ("off", "none", False))
off = sorted(k for k, v in toggles.items() if v in ("off", "none", False))
title = f"The worm: the model run as it stands, closed loop ({seconds:g} s)"
desc = "Nothing prescribed: the brain (brain.py) drives the muscles and the body's sensing feeds back. Every number at its ledger template; nothing fitted to behaviour. Worm-scale agar plate, diacetyl cone. 11 mechanisms are off by default (peptides, monoamines, glia, metabolism, slow signalling, homeostasis, expression map, innexin identity, gap rectification, active muscle membrane, muscle coupling). This is what the model does."

import build_viewer_data as bvd  # noqa: E402

bvd.add_runs([rid], titles={rid: (title, desc)})
idx_path = bvd.VIEW / "runs" / "index.json"  # put the model run first, so the viewer opens on it
idx = json.load(open(idx_path))
idx["runs"] = [e for e in idx["runs"] if e["id"] == rid] + [e for e in idx["runs"] if e["id"] != rid]
json.dump(idx, open(idx_path, "w"), indent=1)
print(json.dumps({"run": rid, "wall_s": round(meta["loop_wall_s"], 1), "max_activation": meta["max_activation"],
                  "toggles_on": on, "toggles_off": off}, indent=1))
