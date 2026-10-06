"""The model's construction tables for the Fidelity tab (M4): mechanisms with their
status and switches, every unknown with its biological bounds and label, the named
profiles with their status, and which scans and bodies the recorder can use.

    .venv/bin/python app/build/fidelity.py          # -> app/data/model/fidelity.json

Sources, read only, through the model's public functions:
- `flyemu.model_data.load()` and `construction_state()`: data/model/mechanisms.yaml,
  parameters.csv and structural_keys.csv, and the ledger counts made from them;
- `flyemu.profiles.PROFILES`: every profile value with its label and justification;
- app/server/record.py `profile_status`: the status the recorder writes for a profile.

These are the tables at this checkout's commit, not a record of any run: a run's own
values are its inventory.csv. The page says so and flags a run made at another commit.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import yaml

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
from record import git_state, profile_status  # noqa: E402  (puts the model's src/ on the path)
from flyemu import model_data, profiles  # noqa: E402

OUT = APP / "data" / "model" / "fidelity.json"
TABLES = ("mechanisms.yaml", "parameters.csv", "structural_keys.csv")

# What the recorder can run on, and why not otherwise (docs/APP_DESIGN.md sections 6.1, 6.2, 13)
SCANS = [
    {"id": "male-cns:v1.0", "coverage": "whole CNS", "sex": "male", "simulate": True,
     "why": "the model's connectome (connectome.build reads the male-cns cache)"},
    {"id": "BANC", "coverage": "whole CNS", "sex": "female", "simulate": False,
     "why": "metadata only in the project, no edges; needs a connectome adapter in the model"},
    {"id": "FlyWire FAFB v783", "coverage": "brain only", "sex": "female", "simulate": False,
     "why": "type crosswalk only; needs a VNC joined at the neck (e.g. MANC)"},
    {"id": "MANC v1.2", "coverage": "VNC only", "sex": "male", "simulate": False,
     "why": "crosswalk only; a partner for FAFB"},
    {"id": "hemibrain v1.2.1", "coverage": "part of the central brain", "sex": "female", "simulate": False,
     "why": "cannot drive a body; comparison only"},
]
BODIES = [
    {"id": "flybody", "simulate": True, "why": "the model's body (MuJoCo, flybody via flygym)"},
    {"id": "neuromechfly", "simulate": False,
     "why": "Body supports it, Organism does not expose the choice (request 1 to the fly worker, on hold)"},
]


def clean(v):
    """JSON-safe: NaN and blanks become null, numpy scalars become Python numbers."""
    if v is None or v == "":
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


MECH_FIELDS = ("id", "name", "tier", "status", "switch", "neutral", "test", "notes", "absent_reason",
               "infrastructure")


def mechanisms(md) -> list[dict]:
    """The mechanism entries in file order. A comma inside unquoted text in a YAML flow
    mapping ends the field, and the rest of the text becomes keys with no value: B1's name
    "rigid skeleton ... (mm, g, s)" loads as name "... (mm" plus keys "g" and "s)". Such
    keys are joined back onto the field before them, and the entry lists the field under
    `rejoined` so the page can say so. The file itself is the fly worker's to fix."""
    raw = yaml.safe_load((model_data.MODEL / "mechanisms.yaml").read_text())
    assert [r["id"] for r in raw] == list(md.mechanisms.id), "mechanisms.yaml and model_data disagree"
    out = []
    for r in raw:
        e, cur, rejoined = {}, None, []
        for k, v in r.items():
            if k in MECH_FIELDS:
                e[k], cur = v, k
            elif v is None and isinstance(e.get(cur), str):
                e[cur] += f", {k}"
                if cur not in rejoined:
                    rejoined.append(cur)
            else:
                raise ValueError(f"{r['id']}: unexpected field {k!r}")
        e["switch"] = list(e.get("switch") or [])
        e["test"] = list(e.get("test") or [])
        e["infrastructure"] = bool(e.get("infrastructure") or False)
        out.append({**{k: e.get(k) for k in MECH_FIELDS}, "rejoined": rejoined})
    return out


def build() -> dict:
    md = model_data.load()
    st = model_data.construction_state(md)
    piv = st["mechanisms"]
    by_tier = {t: {s: int(piv.loc[t, s]) if s in piv.columns else 0 for s in sorted(model_data.STATUSES)}
               for t in piv.index}
    mech = mechanisms(md)
    par_cols = ["param_id", "mechanism_id", "grain", "applies_to", "unit", "registry_key", "bio_min",
                "bio_max", "bound_basis", "bound_source", "bound_verified", "prior_dist", "prior_a",
                "prior_b", "prior_basis", "label", "release_stage", "value_fixed", "current_m4"]
    par = [{k: clean(r[k]) for k in par_cols} for r in md.parameters.to_dict("records")]
    struct = [{k: clean(v) for k, v in r.items()} for r in md.structural.to_dict("records")]
    # status as the recorder writes it; "earlier" marks profiles defined before the working one
    # in profiles.py (each working profile extends the one before it)
    names = list(profiles.PROFILES)
    profs = [{"name": name, "status": profile_status(name, {}), "kick_mv": p.get("kick_mv"),
              "earlier": names.index(name) < names.index(profiles.WORKING_PROFILE),
              "values": {k: [v, str(getattr(s, "value", s)), why] for k, (v, s, why) in p["values"].items()}}
             for name, p in profiles.PROFILES.items()]
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "data/model", "src/flyemu/profiles.py",
                            "src/flyemu/model_data.py"], cwd=REPO, capture_output=True, text=True).stdout.split("\n")
    return {
        "format": "flyemu-fidelity/1",
        "built": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": {**git_state(REPO), "tables": {t: md5(model_data.MODEL / t) for t in TABLES},
                   "tables_modified": [x[3:] for x in dirty if x.strip()],
                   "basis": "the model's construction tables and profiles at this checkout; not a run record"},
        "state": {
            "n_mechanisms": int(st["n_mechanisms"]), "by_tier": by_tier,
            "n_unknowns": int(st["n_unknowns"]), "bounded_by_data": int(st["bounded_by_data"]),
            "bounds_verified": int(st["bounds_verified"]), "fixed_by_measurement": int(st["fixed_by_measurement"]),
            "wired": int(st["wired"]), "by_label": {k: int(v) for k, v in st["by_label"].items()},
            "by_stage": {str(clean(k)): int(v) for k, v in st["by_stage"].items()},
            "legacy_outside_bounds": list(st["legacy_outside_bounds"]),
            "absent_c_without_reason": list(st["absent_c_without_reason"]),
        },
        "mechanisms": mech, "parameters": par, "structural": struct,
        "profiles": profs, "working": profiles.WORKING_PROFILE, "regression": profiles.REGRESSION_PROFILE,
        "scans": SCANS, "bodies": BODIES,
    }


def main() -> None:
    f = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(f, separators=(",", ":")))
    s = f["state"]
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1e3:.0f} kB): {s['n_mechanisms']} mechanisms, "
          f"{s['n_unknowns']} unknowns, {len(f['profiles'])} profiles; commit {f['source']['commit'][:9]}"
          f"{', tables modified: ' + ', '.join(f['source']['tables_modified']) if f['source']['tables_modified'] else ''}")


if __name__ == "__main__":
    main()
