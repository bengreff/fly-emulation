"""Build viewer/worm/catalog_guide.json: the explanation block shown at the top of the viewer's
Catalog tab (what the labels mean, why we trust each one, what "derived" is derived from, and how
many of today's guessed numbers are being re-expressed as rules on measured structure).

Reads docs/worm/ledger.json only (the catalog's source of truth; do not hand-edit the counts here).
Run it again whenever docs/worm/ledger.json is rebuilt, so the numbers in the viewer stay current:

    uv run python viewer/worm/build_catalog_guide.py

It also looks for docs/worm/UNKNOWNS.md (the modelling agent's re-expression plan). If that file
exists, this script pulls one count out of it ("after" total guessed numbers once the per-pair and
per-cell blocks are re-expressed as rules). If it does not exist yet, the viewer says so plainly
instead of inventing a number.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "docs" / "worm" / "ledger.json"
UNKNOWNS = REPO / "docs" / "worm" / "UNKNOWNS.md"
OUT = Path(__file__).resolve().parent / "catalog_guide.json"


def find_param(params: list[dict], param_id: str) -> dict | None:
    for p in params:
        if p.get("param_id") == param_id:
            return p
    return None


def label_n(p: dict | None, label: str) -> int:
    """How many of this row's elements actually carry `label`. A catalog row's own `label` field is
    only the dominant label for the row (e.g. syn_sign_receptor is filed under "guessed" but is really
    1,997 guessed + 1,703 derived + 9 measured): prefer the per-element breakdown when the row has one,
    and only fall back to the row's single label when it has no per-element split to read."""
    if p is None:
        return 0
    by_label = (p.get("element_stats") or {}).get("by_label")
    if by_label:
        return int(by_label.get(label, 0))
    return int(p.get("n_values", 0)) if p.get("label") == label else 0


def guessed_n(p: dict | None) -> int:
    return label_n(p, "guessed")


def example_for(params: list[dict], label: str, preferred: list[str]) -> dict:
    """A short, readable example row for this label: try the preferred param_ids first."""
    for pid in preferred:
        p = find_param(params, pid)
        if p is not None:
            return row_example(p)
    for p in params:
        if p.get("label") == label:
            return row_example(p)
    return {}


def sig3(x):
    """Round a value to 3 significant figures, the way the viewer's own sig() does, so an example
    like 0.4472135954999579 nS shows as 0.447 nS."""
    if not isinstance(x, (int, float)):
        return x
    if x == 0:
        return 0.0
    return float(f"{x:.3g}")


def row_example(p: dict) -> dict:
    return {
        "param_id": p.get("param_id"),
        "plan_row": p.get("plan_row"),
        "applies_to": p.get("applies_to"),
        "n_values": p.get("n_values"),
        "value": sig3(p.get("value_template")),
        "unit": p.get("unit"),
        "source": p.get("template_source") or p.get("source_project"),
    }


def main() -> None:
    ledger = json.loads(LEDGER.read_text())
    params = ledger["parameters"]
    cat = ledger["catalog"]
    totals = cat["totals"]  # {"rows": {...}, "numbers": {...}, "n_rows":, "n_numbers":}

    labels = ["measured", "published_fit", "derived", "inferred", "guessed"]
    label_title = {
        "measured": "measured",
        "published_fit": "published fit",
        "derived": "derived",
        "inferred": "inferred",
        "guessed": "guessed",
    }
    label_meaning = {
        "measured": "Read straight off a cited experiment, scan or electron-micrograph count. We "
                    "trust these as far as we trust the one paper or dataset, with no extra step in "
                    "between.",
        "published_fit": "Another project already fitted or chose this value and published it "
                          "(BAAIWorm, Nicoletti et al., MetaWorm, c302...). We trust it as far as we "
                          "trust that published model; it was fit to someone else's data, not ours, "
                          "and not refit here.",
        "derived": "Plain arithmetic on a measured value, with the arithmetic shown in the row's "
                   "source note. Mostly this is the 3D cell-reconstruction points and diameters "
                   "(coordinates and widths digitized from BAAIWorm's EM-based cell shapes); a "
                   "smaller set is one-line arithmetic on a measured quantity (a physical constant, "
                   "a membrane area from a measured capacitance, an innexin assignment from measured "
                   "gene expression). We trust these as far as we trust the measurement plus the "
                   "arithmetic, which anyone can check.",
        "inferred": "Reasoned from a source by this project, not a straight measurement or "
                    "arithmetic, and not a guess either: for example assigning a channel to a cell "
                    "because its gene is reported expressed there, or picking a receptor's coupling "
                    "from a homologue. Trust these less than measured or published fit; they are our "
                    "best reasoned call, not data.",
        "guessed": "A bounded placeholder, picked to sit inside a plausible biological range so the "
                   "model runs, not read off anything. These are the real gaps: the parts of the scan "
                   "we have not filled in yet.",
    }
    preferred_examples = {
        "measured": ["wire_chem_contacts", "wire_gap_contacts"],
        "published_fit": ["pas_soma_Ra"],
        "derived": ["ph_area_um2", "glia_rt_f_mV", "morph_xyz"],
        "inferred": ["gap_innexin_unitary", "dens_unc2"],
        "guessed": ["syn_strength_per_pair"],
    }
    label_rows = []
    for lab in labels:
        label_rows.append({
            "key": lab,
            "title": label_title[lab],
            "meaning": label_meaning[lab],
            "rows": totals["rows"].get(lab, 0),
            "numbers": totals["numbers"].get(lab, 0),
            "example": example_for(params, lab, preferred_examples[lab]),
        })

    # "derived" breakdown: the reconstruction bulk, and the rest (arithmetic on a measured value)
    morph_xyz = find_param(params, "morph_xyz")
    morph_diam = find_param(params, "morph_diam")
    recon_rows = [p for p in (morph_xyz, morph_diam) if p]
    recon_numbers = sum(p.get("n_values", 0) for p in recon_rows)
    recon_row_ids = [p["param_id"] for p in recon_rows]

    other_derived = [p for p in params if p.get("label") == "derived" and p.get("param_id") not in recon_row_ids]
    other_derived.sort(key=lambda p: -p.get("n_values", 0))
    other_derived_rows = [{
        "param_id": p.get("param_id"),
        "plan_row": p.get("plan_row"),
        "n_values": p.get("n_values"),
        "unit": p.get("unit"),
        "value": sig3(p.get("value_template")),
        "arithmetic": p.get("template_source"),
    } for p in other_derived]

    # Unknowns that could be derived likewise: the "before" guessed blocks these rules would replace.
    syn_strength = find_param(params, "syn_strength_per_pair")
    nmj_strength = find_param(params, "nmj_strength_per_pair")
    gap_strength = find_param(params, "gap_strength_per_pair")
    syn_sign = find_param(params, "syn_sign_receptor")
    pas_soma_cm = find_param(params, "pas_soma_cm")
    pas_neurite_cm = find_param(params, "pas_neurite_cm")
    dens_rows = [p for p in params if p.get("param_id", "").startswith("dens_")]
    dens_guessed = sum(label_n(p, "guessed") for p in dens_rows)
    dens_inferred = sum(label_n(p, "inferred") for p in dens_rows)

    before = [
        {
            "rule": "synapse strength = EM contact count x a unit conductance per receptor class",
            "param_ids": ["syn_strength_per_pair", "nmj_strength_per_pair"],
            "guessed_numbers": guessed_n(syn_strength) + guessed_n(nmj_strength),
            "note": "today one shared per-contact value times Cook 2019's measured EM contact count, "
                    "for every chemical synapse and neuromuscular junction pair.",
        },
        {
            "rule": "gap-junction strength = EM gap-junction measure x an innexin unitary conductance",
            "param_ids": ["gap_strength_per_pair"],
            "guessed_numbers": guessed_n(gap_strength),
            "note": "today one shared per-contact value times Cook 2019's measured EM gap count.",
        },
        {
            "rule": "receptor identity from measured gene expression (CeNGEN)",
            "param_ids": ["syn_sign_receptor"],
            "guessed_numbers": guessed_n(syn_sign),
            "note": "today which receptor class carries a given chemical synapse is guessed for most pairs.",
        },
        {
            "rule": "capacitance = specific capacitance x membrane area (from the cell reconstruction)",
            "param_ids": ["pas_soma_cm", "pas_neurite_cm"],
            "guessed_numbers": guessed_n(pas_soma_cm) + guessed_n(pas_neurite_cm),
            "note": "today one shared capacitance per compartment type, not each cell's own reconstructed area.",
        },
        {
            "rule": "channel density from a gene-expression map (CeNGEN, by selector battery)",
            "param_ids": ["dens_* (channel density rows)"],
            "guessed_numbers": dens_guessed,
            "inferred_numbers": dens_inferred,
            "note": "today 189 of 438 channel-density numbers are guessed and 216 more are inferred, "
                    "per (gene, cell class), not yet read off an expression map the way row 3's channel "
                    "presence already is.",
        },
    ]
    before_total_guessed = sum(b["guessed_numbers"] for b in before)

    after_exists = UNKNOWNS.exists()
    after_count = None
    after_note = ("docs/worm/UNKNOWNS.md does not exist yet. When the modelling agent writes it, this "
                  "script will read the exact after-count from it; until then, the before-count above "
                  "is all we can show.")
    if after_exists:
        text = UNKNOWNS.read_text()
        # Look for a line this script can parse mechanically: "after: N guessed numbers" (any case,
        # with or without a comma in N). If the file exists but has no such line, say so rather than guess.
        m = re.search(r"after[^\n]*?([\d][\d,]*)\s*guessed", text, re.IGNORECASE)
        # UNKNOWNS.md's own verdict line (wmodel, 7 Nov): "**Verdict.** N numbers are genuinely unknown ...
        # N1 shared rules plus N2 gaps"; that N is the fit vector once the rules replace the per-pair blocks.
        v = re.search(r"([\d][\d,]*) numbers are genuinely unknown(?:.*?(\d+) shared rules plus\s+(\d+) gaps)?",
                      text, re.DOTALL)
        if m:
            after_count = int(m.group(1).replace(",", ""))
            after_note = f"from docs/worm/UNKNOWNS.md: {after_count:,} guessed numbers remain after the re-expression."
        elif v:
            after_count = int(v.group(1).replace(",", ""))
            split = f" ({v.group(2)} shared rules + {v.group(3)} gaps)" if v.group(2) else ""
            after_note = (f"from docs/worm/UNKNOWNS.md's verdict: {after_count:,} numbers remain unknown{split}, "
                          "the whole fit vector once the rules stand in for the per-pair and per-cell blocks.")
        else:
            after_note = ("docs/worm/UNKNOWNS.md exists but this script found no parseable "
                          "'after: N guessed' line in it yet; read the file directly for its count.")

    out = {
        "generated_by": "viewer/worm/build_catalog_guide.py",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ledger_source": "docs/worm/ledger.json",
        "framing": (
            "All the mechanisms, and all the parameters except the guessed ones, are the full "
            "realisation of a scan of a real C. elegans worm: its cells, their 3D shapes and wiring "
            "(from electron-microscopy reconstructions), and published measurements of how its "
            "channels, synapses and muscles behave. The guessed parameters are the gaps in that scan "
            "that still have to be filled in."
        ),
        "labels": label_rows,
        "counts": {
            "rows": totals["rows"],
            "numbers": totals["numbers"],
            "total_rows": totals.get("n_rows"),
            "total_numbers": totals.get("n_numbers"),
        },
        "derived_from": {
            "reconstruction": {
                "rows": len(recon_rows),
                "numbers": recon_numbers,
                "param_ids": recon_row_ids,
                "note": "BAAIWorm's 3D reconstruction of each of the 302 neurons: the (x, y, z) "
                        "position and diameter recorded at every point along the cell, digitized from "
                        "microscopy. This is almost all of the 'derived' total.",
            },
            "other_rows": other_derived_rows,
            "other_rows_count": len(other_derived_rows),
            "other_rows_numbers": sum(r["n_values"] for r in other_derived_rows),
        },
        "unknowns": {
            "intro": (
                "The big guessed blocks are per-pair (one guessed number for every connected neuron "
                "pair) or per-cell (one guessed number for every neuron). The plan today is to "
                "re-express each of those blocks as a rule applied to measured structure, the same way "
                "'derived' already works for the cell shapes, rather than leaving them as flat "
                "placeholders."
            ),
            "before": before,
            "before_total_guessed": before_total_guessed,
            "after_count_source": "docs/worm/UNKNOWNS.md",
            "after_count_exists": after_exists,
            "after_count": after_count,
            "after_note": after_note,
        },
    }

    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT} ({totals.get('n_rows')} rows, {totals.get('n_numbers')} numbers in the ledger)")


if __name__ == "__main__":
    main()
