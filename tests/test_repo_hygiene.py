"""Repository hygiene: parameter tables are well-formed and labelled, every
script compiles, and every repo path the docs mention exists.

These tests are cheap (no model build) and guard the bookkeeping the project
relies on: a value without a label, a table row pointing at a cell that does
not exist, or a doc pointing at a deleted script are all silent failures
otherwise.
"""
from __future__ import annotations

import py_compile
import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "src"))
BASES = {"measured", "derived", "inferred", "guessed"}


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "params" / name, comment="#")


@pytest.fixture(scope="module")
def neurons() -> pd.DataFrame:
    p = ROOT / "data" / "cache" / "male_cns_neurons.parquet"
    if not p.exists():
        pytest.skip("connectome cache not present")
    return pd.read_parquet(p, columns=["bodyId", "type"])


# --- parameter tables -------------------------------------------------------

def test_cell_type_rows_are_labelled_and_resolve(neurons):
    t = read("cell_types.csv")
    assert set(t.basis) <= BASES
    assert t.justification.notna().all()
    assert t[t.basis.isin(["measured", "derived"])].source.notna().all()
    types = set(neurons.type.dropna())
    bids = set(neurons.bodyId)
    for r in t.itertuples():
        if r.type.startswith("bodyId:"):
            ids = {int(x) for x in r.type[7:].split(";") if x}
            assert ids and ids <= bids, f"unknown bodyIds in {r.param} row"
        elif r.type.startswith("^"):
            assert any(re.match(r.type, x) for x in types), f"regex matches no type: {r.type}"
        else:
            assert r.type in types, f"unknown type {r.type}"


def test_motor_force_table_is_consistent(neurons):
    t = read("motor_forces.csv")
    assert set(t.basis) <= BASES and set(t.force_basis) <= BASES and set(t.tau_basis) <= BASES
    assert (t.torque_uNmm > 0).all() and (t.twitch_tau_ms > 0).all()
    assert set(t.bodyId) <= set(neurons.bodyId)
    classed = t[t.unit_class.fillna("") != ""]
    assert (classed.basis == "derived").all()        # measured force x derived lever
    for _, g in classed.groupby("leg"):
        assert (g.unit_class == "fast").sum() == 1


def test_orn_rate_table_is_labelled():
    t = read("orn_rates.csv")
    assert set(t.sfr_basis) <= BASES and set(t.rmax_basis) <= BASES
    assert (t.rmax_hz > t.sfr_hz).all() and (t.sfr_hz >= 0).all()
    assert (t[t.sfr_basis == "measured"].door_unit != "none").all()


def test_conduction_delays_are_physical():
    t = read("conduction_delays.csv")
    assert t.type.is_unique
    assert t.delay_ms.between(0.5, 10).all()        # t_syn 0.5 ms plus conduction
    assert set(t.velocity_basis) <= {"measured", "inferred"}
    assert (t[t.type == "DNp01"].velocity_basis == "measured").all()


def test_proprioceptor_assignment_matches_the_banc_crosswalk():
    t = read("proprio_assignment.csv")
    x = pd.read_csv(ROOT / "data" / "derived" / "banc_proprio_crosswalk.csv").set_index("type")
    assert set(t.basis) <= BASES | {"unknown"}
    for r in t[t.basis == "derived"].itertuples():
        banc = str(x.banc_subclass.get(r.type, ""))
        st = "" if pd.isna(r.subtype) else r.subtype
        if banc.startswith("nonleg"):
            assert st == "", r.type
        elif banc in ("claw", "club"):
            assert st == banc, r.type
        elif banc == "hook":
            assert st in ("hook_flex", "hook_ext"), r.type
        elif banc == "leg_hair_plate":
            assert st.startswith("hairplate_"), r.type
    # every tuned subtype carries an inferred direction
    tuned = t[t.subtype.fillna("").str.match(r"^(claw|hook_|hairplate_)")]
    assert (tuned.direction_basis == "inferred").all()


def test_opsin_and_motor_target_tables_are_labelled():
    o = read("opsin_spectra.csv")
    assert set(o.basis) <= BASES and o.lambda_max_nm.between(300, 650).all()
    m = pd.read_csv(ROOT / "data" / "params" / "motor_targets.csv", comment="#")
    assert len(m) > 0


def test_rejected_hypotheses_are_not_loaded():
    """Rows tested and not adopted live outside the tables the model reads."""
    h = ROOT / "data" / "params" / "hypotheses_not_adopted.csv"
    if h.exists():
        rej = pd.read_csv(h, comment="#")
        live = read("cell_types.csv")
        both = rej.merge(live, on=["type", "param"])
        assert both.empty, both[["type", "param"]]


# --- code and docs ----------------------------------------------------------

def test_every_script_compiles():
    files = list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py"))
    for f in files:
        py_compile.compile(str(f), doraise=True)


PATH_RE = re.compile(r"`((?:src|scripts|tests|data|docs|viz)/[A-Za-z0-9_./\-{}<>*]+)`")


def test_paths_mentioned_in_living_docs_exist():
    """Living docs may only point at files that exist. Historical records
    (FINDINGS, DECISIONS, session logs, docs/archive) are exempt: they describe
    what was true then."""
    living = ["README.md", "CLAUDE.md", "docs/HANDOFF.md", "docs/WORKFLOW.md",
              "docs/ARCHITECTURE.md", "docs/RUNNING.md", "docs/PLAN_NEXT.md",
              "docs/NEXT_SESSION_PROMPT.md", "docs/MODEL.md", "docs/INTERFACE.md",
              "docs/ENVIRONMENT.md", "docs/VALIDATION.md", "docs/PROJECT.md",
              "scripts/probes/README.md"]
    missing = []
    for doc in living:
        p = ROOT / doc
        if not p.exists():
            continue
        for m in PATH_RE.finditer(p.read_text()):
            ref = m.group(1).rstrip(".,:)")
            if any(c in ref for c in "{}<>*"):
                continue                          # templates and globs
            if re.fullmatch(r"docs/SESSION\d+[a-z]?_LOG\.md", ref):
                continue                          # logs a session prompt tells the session to create
            if not (ROOT / ref).exists():
                missing.append(f"{doc}: {ref}")
    assert not missing, "\n".join(missing)


def test_run_records_capture_the_environment(tmp_path):
    """Provenance must build with the declared dependencies only (a removed
    dependency once broke every run script while the suite stayed green)."""
    from flyemu.provenance import RunRecord, environment
    env = environment()
    assert env["numpy"] and env["mujoco"]
    RunRecord("hygiene-test", tmp_path)


def test_scripts_default_to_the_working_model():
    import subprocess
    import sys
    from flyemu import profiles
    for script in ("run_organism.py", "record_organism.py", "assay_pathways.py"):
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / script), "--help"],
                             capture_output=True, text=True, cwd=ROOT).stdout
        assert "--min-synapses" in out and "--profile" in out, script
    assert profiles.WORKING_PROFILE in profiles.PROFILES


def test_docs_cited_in_code_exist():
    missing = set()
    for f in list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")):
        for ref in re.findall(r"docs/[A-Za-z0-9_/\-]+\.md", f.read_text()):
            if not (ROOT / ref).exists() and not re.fullmatch(r"docs/SESSION\d+[a-z]?_LOG\.md", ref):
                missing.add(f"{f.relative_to(ROOT)}: {ref}")
    assert not missing, "\n".join(sorted(missing))
