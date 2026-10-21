"""python -m flyemu.check: test a fly_brain.zip from its own contents (docs/FLY_BRAIN_ZIP.md, "Entry point").

    PYTHONPATH=fly_brain.zip/code python -m flyemu.check fly_brain.zip --out check/ [--deny <repo>]
    PYTHONPATH=src python -m flyemu.check --tree . --out check_tree/        # the same from the repo

Inside the extracted tree, under the same read guard as flyemu.run:
1. runs the zip's own tests/ (pytest, in process, so the guard sees every read) and records each test's outcome;
2. rebuilds the blank ledger from the zip's own ontology and tables (scripts/blank_ledger.py, written to the
   output directory, never over the tree) and compares it with the packed ledger;
3. prints the ledger fill fraction: the share of slots whose value comes from data (measured or derived), then
   with the rule-inferred share added, by slot and with each measurable quantity weighted equally;
4. lists the behaviour scoreboard and which items have a protocol in the zip's world/ (the scoreboard runs
   themselves are separate flyemu.run calls; see SCOREBOARD).
Writes check_manifest.json, junit.xml, ledger_report.txt and ledger/*.csv. Exit code 0 only if every test
passes or skips and the rebuilt ledger matches the packed one.

The launcher part uses the standard library only (it is imported from inside the zip).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import flyzip, run

RESULT = "check_manifest.json"
LEDGER_TABLES = ("blank_ledger.csv", "ledger_levels.csv")

# The fixed behaviour scoreboard (scope brief, 6 Oct). A protocol is a world/ arena + stimulus pair that
# flyemu.run can play, plus the readout that scores it; None until it is built and passes a zip-vs-tree
# identity run.
SCOREBOARD = {
    "stands": None,
    "walks": None,
    "grooms": None,
    "PER to labellar sugar": None,
    "PER to leg sugar": None,
    "optomotor turning": None,
    "giant-fibre escape": None,
    "stable flight": None,
}


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Check a fly_brain.zip from its own contents")
    ap.add_argument("zip", nargs="?", help="fly_brain.zip (omit with --tree)")
    ap.add_argument("--tree", help="check this repo tree instead of a zip (the identity reference)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tests", default="tests", help="pytest target inside the tree (default: all of tests/)")
    ap.add_argument("-k", dest="keyword", default=None, help="pytest -k expression")
    ap.add_argument("--no-tests", action="store_true", help="skip the tests (ledger and scoreboard only)")
    ap.add_argument("--deny", action="append", default=[], help="refuse any read under this root (repeatable)")
    ap.add_argument("--workdir", help="extraction directory (new or empty); default a fresh temp dir")
    ap.add_argument("--keep", action="store_true", help="keep the extracted tree")
    ap.add_argument("--allow-runtime-mismatch", action="store_true")
    ap.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--root", help=argparse.SUPPRESS)
    return ap


# --- inside the extracted (or repo) tree ----------------------------------------------------------------

def _tests(root: Path, out: Path, target: str, keyword: str | None) -> dict:
    import xml.etree.ElementTree as ET
    from collections import Counter

    import pytest
    junit = out / "junit.xml"
    # the same rootdir and test ids in zip and tree mode (the tree's pyproject only sets testpaths)
    args = ["-q", "-p", "no:cacheprovider", "--rootdir", str(root), "-o", "testpaths=tests",
            "-o", "junit_family=xunit2", "--junitxml", str(junit), str(root / target)]
    if keyword:
        args += ["-k", keyword]
    t0 = time.time()
    code = pytest.main(args)
    outcomes = {}
    for tc in ET.parse(junit).iter("testcase"):
        kind = "passed"
        for child in tc:
            if child.tag in ("failure", "error", "skipped"):
                kind = child.tag
                break
        outcomes[f"{tc.get('classname')}::{tc.get('name')}"] = kind
    return {"target": target, "keyword": keyword, "exit_code": int(code), "pytest": pytest.__version__,
            "counts": dict(Counter(outcomes.values())), "outcomes": dict(sorted(outcomes.items())),
            "wall_s": round(time.time() - t0, 1)}


def _ledger(root: Path, out: Path) -> dict:
    import contextlib
    import importlib.util
    import io

    import pandas as pd
    spec = importlib.util.spec_from_file_location("blank_ledger", root / "scripts" / "blank_ledger.py")
    bl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bl)
    if Path(bl.REPO).resolve() != root:
        raise flyzip.Refused(f"blank_ledger.py resolves its tables under {bl.REPO}, not {root}")
    (out / "ledger").mkdir(exist_ok=True)
    bl.OUT = out / "ledger"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bl.main()
        bl.construction_report()
    (out / "ledger_report.txt").write_text(buf.getvalue())
    same = {n: flyzip.sha256_file(out / "ledger" / n) == flyzip.sha256_file(root / "data" / "derived" / n)
            for n in LEDGER_TABLES}
    df = pd.read_csv(out / "ledger" / "blank_ledger.csv")
    tot = int(df.slots.sum())
    lv = df.groupby("level").slots.sum().reindex(bl.LEVELS, fill_value=0)
    data = int(lv[["measured", "derived"]].sum())
    q = df.assign(q=df.quantity.str.replace(r" \[filled: .*\]$", "", regex=True))
    w = q.pivot_table(index="q", columns="level", values="slots", aggfunc="sum", fill_value=0)
    w = w.div(w.sum(axis=1), axis=0).mean().reindex(bl.LEVELS, fill_value=0)
    ns = df[df.grain_group != "synapse"].groupby("level").slots.sum().reindex(bl.LEVELS, fill_value=0)
    pct = lambda x, n: round(100 * float(x) / float(n), 2)  # noqa: E731
    return {
        "rebuilt_matches_packed": same,
        "quantities": int(q.q.nunique()), "slots": tot,
        "fill_by_slot": {"data_pct": pct(data, tot), "data_plus_rule_pct": pct(data + lv["rule"], tot)},
        "fill_per_quantity": {"data_pct": round(100 * float(w[["measured", "derived"]].sum()), 2),
                              "data_plus_rule_pct": round(100 * float(w[["measured", "derived", "rule"]].sum()), 2)},
        "fill_outside_synapse_grain": {"slots": int(ns.sum()),
                                       "data_pct": pct(ns[["measured", "derived"]].sum(), ns.sum()),
                                       "data_plus_rule_pct": pct(ns[["measured", "derived", "rule"]].sum(), ns.sum())},
        "slots_by_level": {k: int(v) for k, v in lv.items()},
    }


def _scoreboard(root: Path) -> dict:
    built = sorted(p.stem for p in (root / "world" / "protocols").glob("*.json")) \
        if (root / "world" / "protocols").is_dir() else []
    return {item: (proto if proto in built else None) for item, proto in SCOREBOARD.items()}


def inside(a) -> int:
    c = run.child_setup(a)
    root, man, guard = c["root"], c["man"], c["guard"]
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    guard.allowed.append(str(out))                  # reading back its own outputs (junit.xml) is not a read of the fly
    res = {"mode": c["mode"], "root": str(root),
           "zip": {"path": man.get("_zip_path"), "sha256": man["_zip_sha256"],
                   "manifest_sha256": man["_manifest_sha256"], "git_commit": man["git_commit"]} if man else None,
           "tree_git_commit": run._git_head(root) if c["mode"] == "tree" else None,
           "runtime": c["versions"], "body": c["body_src"]}
    res["tests"] = None if a.no_tests else _tests(root, out, a.tests, a.keyword)
    res["ledger"] = _ledger(root, out)
    res["scoreboard"] = _scoreboard(root)
    res["read_guard"] = {"deny": guard.deny, "deny_inside": guard.deny_inside, "denied": guard.denied,
                         "outside_allowed": sorted(guard.outside)}
    t = res["tests"]
    tests_ok = t is None or not ({"failure", "error"} & set(t["counts"]))
    ledger_ok = all(res["ledger"]["rebuilt_matches_packed"].values())
    res["ok"] = bool(tests_ok and ledger_ok)
    (out / RESULT).write_text(json.dumps(res, indent=1, default=str))
    L = res["ledger"]
    print(f"tests: {t['counts'] if t else 'not run'}", file=sys.stderr)
    print(f"ledger rebuilt from the zip's tables matches the packed ledger: {L['rebuilt_matches_packed']}",
          file=sys.stderr)
    print(f"ledger fill fraction ({L['quantities']} quantities, {L['slots']:,} slots): data (measured + derived) "
          f"{L['fill_by_slot']['data_pct']}% of slots, {L['fill_by_slot']['data_plus_rule_pct']}% with "
          f"rule-inferred; per quantity {L['fill_per_quantity']['data_pct']}% / "
          f"{L['fill_per_quantity']['data_plus_rule_pct']}%; outside the synapse grain "
          f"{L['fill_outside_synapse_grain']['data_pct']}% / {L['fill_outside_synapse_grain']['data_plus_rule_pct']}%",
          file=sys.stderr)
    sb = res["scoreboard"]
    print(f"scoreboard protocols in the zip: {sum(v is not None for v in sb.values())} of {len(sb)}", file=sys.stderr)
    return 0 if res["ok"] else 1


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    try:
        return inside(a) if a.inside else run.launch(a, module="flyemu.check", result_file=RESULT)
    except flyzip.Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
