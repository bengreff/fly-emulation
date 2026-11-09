"""Set the status of each entry in viewer/worm/mechanisms_summary.json from docs/worm/MECHANISMS_AUDIT.md, so the
viewer's Mechanisms tab and the audit count the same way (DEBUG_TRIAGE line 21, 9 Nov 2026).

The audit files a row under its main category, the first bold category of its Category cell, and names any part in
another category. Here a row is "full" when that main category is full and "simplified" otherwise (lumped, spec
only, missing). For the audit's own split rows, `parts` carries the Category cell's text (a split row whose cell is
only its category, its other parts named in other columns, gets none). The plain-English text of each entry stays
hand-written. The script asserts that the full count matches the audit's Counts table over the summary's rows, and
lists audit rows the summary does not cover.

    uv run python viewer/worm/build_mechanisms_summary.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "docs" / "worm" / "MECHANISMS_AUDIT.md"
OUT = Path(__file__).resolve().parent / "mechanisms_summary.json"
CATS = ("full", "lumped", "spec only", "missing", "instrument")
RULE = ("Each row is counted under the audit's main category, as MECHANISMS_AUDIT.md counts it ('simplified' = "
        "lumped, spec only or missing); where a row has parts in another category, they are named under its title.")


def audit_rows(text):
    """{row id: (name, Category cell)} for the numbered rows of the audit table."""
    rows = {}
    for line in text.splitlines():
        m = re.match(r"\| (\d+) \|", line)
        if m:
            cells = line.split("|")
            rows[int(m.group(1))] = (cells[2].strip(), cells[3].strip())
    return rows


def main_category(cell):
    """The first bold category of a Category cell."""
    for b in re.findall(r"\*\*([^*]+)\*\*", cell):
        for c in CATS:
            if b.strip().startswith(c):
                return c
    raise ValueError(f"no main category in {cell!r}")


def split_rows(text):
    """The audit's own list of split rows (a part in another category)."""
    m = re.search(r"Split rows \(a part in another category\): ([\d, ]+)\.", text)
    return {int(x) for x in m.group(1).split(",")}


def counts_table(text):
    """{category: [row ids]} from the audit's Counts table."""
    sec = text.split("## Counts", 1)[1]
    out = {}
    for line in sec.splitlines()[:12]:
        m = re.match(r"\| (full|lumped|instrument|spec only|missing) \| \d+ \| ([^|]*)\|", line)
        if m:
            out[m.group(1)] = [int(x) for x in re.findall(r"\b(\d+)\b", m.group(2).split("(")[0])]
    return out


def main():
    text = AUDIT.read_text()
    rows, counted, splits = audit_rows(text), counts_table(text), split_rows(text)
    d = json.loads(OUT.read_text())
    seen = set()
    for g in d["groups"]:
        for e in g["rows"]:
            name, cell = rows[e["id"]]
            cat = main_category(cell)
            e["status"] = "full" if cat == "full" else "simplified"
            plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", cell).replace("`", "")
            if e["id"] in splits and plain != cat:
                e["parts"] = plain
            else:
                e.pop("parts", None)
            seen.add(e["id"])
            assert e["id"] in counted.get(cat, []), (e["id"], cat, "not in the audit's Counts table under it")
    full = sorted(e["id"] for g in d["groups"] for e in g["rows"] if e["status"] == "full")
    want = sorted(i for i in counted["full"] if i in seen)
    assert full == want, (full, want)
    head = text.splitlines()[0].lstrip("# ")
    d["as_of"] = f"docs/worm/MECHANISMS_AUDIT.md ({head}); statuses set by viewer/worm/build_mechanisms_summary.py"
    d["regenerate"] = ("Statuses and parts: run viewer/worm/build_mechanisms_summary.py after the audit changes (it "
                       "reads each row's main category). The plain-English text is hand-written from the audit rows.")
    if RULE not in d["note"]:
        d["note"] = d["note"].rstrip() + " " + RULE
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    split = [e["id"] for g in d["groups"] for e in g["rows"] if "parts" in e]
    print(f"full {len(full)} of {len(seen)}: {full}")
    print(f"simplified {len(seen) - len(full)}; parts named on {split}")
    print("audit rows not in the summary:", sorted(set(rows) - seen))


if __name__ == "__main__":
    main()
