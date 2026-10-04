"""Held-out guard: does a protocol touch data the project keeps for validation?

The register below is the app's index of docs/HANDOFF.md "Sealed and held-out
data register", the held-out rows of data/measurements/targets_session6.csv and
the held-out assays of scripts/assay_pathways.py, as of 4 October 2026. Those
files are the authority; this index can lag them, so a hit (or a miss) is a
prompt to check the register, not a ruling.

A protocol that stimulates a listed cell type, or reads one out in its
expectation, is refused by the recorder unless the run names the item with
--spend-heldout; spending is appended to runs/app/heldout_spent.jsonl.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

REGISTER = [
    {"id": "gf_dlm", "stim": ["DNp01"], "readout": ["re:DLMn.*"],
     "what": "giant fibre -> DLM motor neurons",
     "status": "held out (GF electrical pre-registration)", "source": "scripts/assay_pathways.py gf_dlm"},
    {"id": "gf_latency", "stim": ["DNp01"], "readout": ["TTMn", "re:DLMn.*"],
     "what": "GF -> TTM 0.93 ms and GF -> DLM 1.44 ms stimulus-to-muscle latency",
     "status": "held out", "source": "data/measurements/targets_session6.csv"},
    {"id": "lplc2_gf", "stim": ["LPLC2"], "readout": ["DNp01"],
     "what": "LPLC2 looming detectors -> giant fibre",
     "status": "pre-registered held-out assay; may have been run in session 4 (F-SENS-1)",
     "source": "scripts/assay_pathways.py lplc2_gf"},
    {"id": "jo_grooming", "stim": ["re:JO-(C|E|F).*"], "readout": ["DNg62", "DNge078", "MDN"],
     "what": "Johnston's organ C/E/F -> antennal grooming DNs or MDN",
     "status": "pre-registered held-out assays; may have been run in session 4 (F-SENS-1)",
     "source": "scripts/assay_pathways.py joce_adn, jof_adn, jof_mdn, joce_mdn"},
    {"id": "tibia_flexor_reflex", "stim": ["Ti flexor MN", "Acc. ti flexor MN"], "readout": [],
     "what": "Azevedo 2020 tibia flexor MN recordings (Piezo trials sealed)",
     "status": "sealed", "source": "docs/HANDOFF.md register"},
]

# Seeds already used for fitting or spent as held out (docs/HANDOFF.md, DECISIONS):
# 0-2 fit, 3-8 spent (s10), 9-11 spent (m7), 12-13 spent (m8 G1), 17-19 spent (m9).
SPENT_SEEDS = set(range(0, 14)) | {17, 18, 19}


def _match(want: list[str], types: set[str]) -> list[str]:
    hit = []
    for w in want:
        if w.startswith("re:"):
            rx = re.compile(w[3:])
            hit += [t for t in types if rx.fullmatch(t)]
        elif w in types:
            hit.append(w)
    return sorted(set(hit))


def check(resolved_protocol: dict, neurons) -> dict:
    """Items of the register the protocol touches, and whether its seed is spent."""
    res = resolved_protocol["resolved"]
    typ = neurons["type"].astype(str).to_numpy()
    stim_types = set()
    for item in res["genotype"] + res["events"]:
        stim_types |= {typ[r] for r in item.get("rows", [])}
    exp = (resolved_protocol.get("expect") or {}).get("readout") or {}
    read_types = set(map(str, exp.get("type", []))) if isinstance(exp.get("type", []), list) \
        else {str(exp.get("type"))}
    hits = []
    for r in REGISTER:
        s = _match(r["stim"], stim_types)
        if s:
            hits.append({**r, "stimulated": s, "read": _match(r["readout"], read_types)})
    seed = int(resolved_protocol["config"].get("seed", 0))
    return {"items": hits, "seed": seed, "seed_spent": seed in SPENT_SEEDS,
            "register": "app/server/heldout.py index of docs/HANDOFF.md, targets_session6.csv, assay_pathways.py"}


def enforce(guard: dict, spend: list[str], log: Path, title: str) -> None:
    """Refuse unless every touched item is named in `spend`; log what was spent."""
    need = sorted({h["id"] for h in guard["items"]})
    missing = [i for i in need if i not in spend]
    msgs = []
    if missing:
        msgs.append("touches held-out items " + ", ".join(missing))
    if not guard["seed_spent"] and "seed" not in spend:
        msgs.append(f"seed {guard['seed']} may be a fresh held-out seed (not in the spent list)")
    if msgs:
        raise SystemExit("held-out guard: " + "; ".join(msgs) + ". Check docs/HANDOFF.md, then rerun with "
                         + " ".join(f"--spend-heldout {i}" for i in missing + (["seed"] if not guard["seed_spent"] else []))
                         + " to spend them.")
    if spend:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as f:
            f.write(json.dumps({"time": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                                "title": title, "spent": spend, "seed": guard["seed"]}) + "\n")
