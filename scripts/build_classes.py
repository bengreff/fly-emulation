"""Build data/model/classes.csv: every cell type -> its class at each grain.

CONSTRUCTION.md task 2. One row per type label of the modelled graph (male-cns
v1.0, traced or typed; untyped cells are grouped as `untyped:<superclass>`).
Columns:

    superclass, class, subclass          male-cns annotations (measured labels)
    hemilineage, hemilineage_source      itoleeHl (brain) / trumanHl (VNC),
                                         majority over the type's cells
    transmitter                          majority consensusNt (F-NT-1)
    circuit_class, circuit_rule          the first matching rule in CIRCUIT
    mode                                 spiking | graded | unknown
    mode_label, mode_source              evidence for the mode (MODE_EVIDENCE)
    mode_param                           parameters.csv row that holds the
                                         unknown mode's prior (mode == unknown)

Inputs: data/cache/male_cns_neurons.parquet, male_cns_extra.parquet
(consensusNt), male_cns_hemilineage.parquet (fetched s9 from neuPrint).

    uv run python scripts/build_classes.py
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "data" / "cache"
OUT = REPO / "data" / "model" / "classes.csv"

# (circuit_class, rule description, predicate(row) -> bool); first match wins.
# Type-name regexes follow male-cns nomenclature.
def _t(pat):
    rx = re.compile(pat)
    return lambda r: bool(rx.match(r["type"]))


def _sc(*names):
    return lambda r: r["superclass"] in names


def _cl(*names):
    return lambda r: r["class"] in names


CIRCUIT = [
    ("photoreceptor", "type R1-R8", _t(r"^R[1-8]")),
    ("ocellar_photoreceptor", "ocellar sensory", _t(r"^(OCG|ocellar)")),
    ("sensory_" + "olfactory", "class olfactory", _cl("olfactory")),
    ("sensory_gustatory", "class gustatory", _cl("gustatory")),
    ("sensory_proprioceptive", "class mechanosensory_proprioceptive", _cl("mechanosensory_proprioceptive")),
    ("sensory_mechano", "class mechanosensory*", lambda r: str(r["class"]).startswith("mechanosensory")),
    ("sensory_other", "sensory superclass", lambda r: "sensory" in str(r["superclass"])),
    ("LMC", "L1-L5", _t(r"^L[1-5]$")),
    ("optic_columnar", "Mi/Tm/TmY/Dm/Pm/C2/C3/T1-T3/Lawf", _t(r"^(Mi\d|Tm\d|TmY|Dm\d|Pm\d|C[23]$|T[123]$|T2a$|Lawf)")),
    ("T4T5", "T4/T5", _t(r"^T[45][a-d]$")),
    ("optic_projection", "LC/LPLC/LLPC/LPC/LT/VS/HS", _t(r"^(LC\d|LPLC|LLPC|LPC|LT\d|VS|HS|H[12]$)")),
    ("optic_other", "optic-lobe superclasses", _sc("ol_intrinsic", "visual_projection", "visual_centrifugal")),
    ("KC", "Kenyon cell", _cl("Kenyon_Cell")),
    ("MBON", "MBON", _cl("MBON")),
    ("DAN", "DAN", _cl("DAN")),
    ("APL", "APL", _t(r"^APL$")),
    ("DPM", "DPM", _t(r"^DPM$")),
    ("AL_PN", "ALPN", _cl("ALPN")),
    ("AL_LN", "ALLN", _cl("ALLN")),
    ("AL_other", "ALIN/ALON", _cl("ALIN", "ALON")),
    ("cx_ring", "EPG/PEG/PEN/Delta7", _t(r"^(EPG|PEG|PEN_|Delta7)")),
    ("cx_ER", "ring neurons ER*", _t(r"^ER\d")),
    ("cx_other", "class CX", _cl("CX")),
    ("clock", "clock neurons", _t(r"^(s-LNv|l-LNv|LNd|LPN|DN1|DN2|DN3|5th-LNv|LNv)")),
    ("MN_leg", "vnc_motor leg subclasses", lambda r: r["superclass"] == "vnc_motor"
     and r["subclass"] in ("fl", "ml", "hl")),
    ("MN_wing_haltere", "vnc_motor wing/haltere", lambda r: r["superclass"] == "vnc_motor"
     and r["subclass"] in ("wm", "hm", "wt", "ht")),
    ("MN_other", "motor superclasses", _sc("vnc_motor", "cb_motor")),
    ("DN", "descending", lambda r: "descending" in str(r["superclass"])),
    ("AN", "ascending", lambda r: "ascending" in str(r["superclass"])),
    ("endocrine", "endocrine", lambda r: "endocrine" in str(r["superclass"])),
    ("efferent", "efferent / ENS", lambda r: "efferent" in str(r["superclass"]) or r["superclass"] == "ENS"),
    ("vnc_local", "vnc_intrinsic (premotor by hemilineage)", _sc("vnc_intrinsic")),
    ("central_other", "cb_intrinsic", _sc("cb_intrinsic")),
]

# mode by circuit class: (mode, label, source, mode_param)
MODE_EVIDENCE = {
    "photoreceptor": ("graded", "measured", "photoreceptors are non-spiking (model row; Hardie & Juusola reviews)", ""),
    "LMC": ("graded", "inferred", "LMCs non-spiking in flies (Calliphora recordings; Lappalainen 2024 used graded) [lead]", ""),
    "APL": ("graded", "inferred", "APL non-spiking, local (Amin et al. 2020) [unverified]", ""),
    "optic_columnar": ("unknown", "guessed", "Lappalainen 2024 graded front end [verified]; whether Mi1/Tm3 spike is contested [unverified]", "n1_p_graded_optic_columnar"),
    "T4T5": ("unknown", "guessed", "T4/T5 mostly graded with small spikes (Gruntman 2018) [unverified]", "n1_p_graded_optic_columnar"),
    "AL_LN": ("unknown", "guessed", "a subset of AL LNs is non-spiking (Seki et al. 2010) [unverified]", "n1_p_graded_al_ln"),
    "vnc_local": ("unknown", "guessed", "insect VNC premotor interneurons active in walking are non-spiking (Pugliese 2025 [verified]; locust Burrows); Drosophila unknown", "n1_p_graded_vnc_local"),
}
DEFAULT_MODE = ("spiking", "inferred", "Para (NaV) broadly expressed at distal spike-initiation zones (J Neurosci 2020) [abstract]", "")


def majority(s: pd.Series) -> str:
    s = s.dropna()
    s = s[s.astype(str) != ""]
    return "" if s.empty else str(s.mode().iloc[0])


def main() -> None:
    n = pd.read_parquet(CACHE / "male_cns_neurons.parquet")
    n = n[(n.status == "Traced") | n.type.notna()]           # inclusion policy (F-COUNT-2)
    ex = pd.read_parquet(CACHE / "male_cns_extra.parquet")[["bodyId", "consensusNt"]]
    hl = pd.read_parquet(CACHE / "male_cns_hemilineage.parquet")[["bodyId", "itoleeHl", "trumanHl"]]
    n = n.merge(ex, on="bodyId", how="left").merge(hl, on="bodyId", how="left")
    n["tkey"] = np.where(n.type.notna(), n.type, "untyped:" + n.superclass.fillna("none"))
    rows = []
    for t, g in n.groupby("tkey", sort=True):
        r = dict(type=t, n_cells=len(g), superclass=majority(g.superclass),
                 **{"class": majority(g["class"])}, subclass=majority(g.subclass),
                 transmitter=majority(g.consensusNt))
        ih, th = majority(g.itoleeHl), majority(g.trumanHl)
        r["hemilineage"], r["hemilineage_source"] = (th, "trumanHl") if th else ((ih, "itoleeHl") if ih else ("", ""))
        cc, rule = "unassigned", ""
        for name, desc, pred in CIRCUIT:
            if pred(r):
                cc, rule = name, desc
                break
        if cc == "vnc_local" and r["hemilineage"]:
            cc = f"vnc_local_{r['hemilineage']}"
        r["circuit_class"], r["circuit_rule"] = cc, rule
        base = "vnc_local" if cc.startswith("vnc_local") else cc
        mode, lab, src, par = MODE_EVIDENCE.get(base, DEFAULT_MODE)
        r.update(mode=mode, mode_label=lab, mode_source=src, mode_param=par)
        rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    typed = ~df.type.str.startswith("untyped:")
    print(f"{len(df)} rows ({typed.sum()} typed types) covering {df.n_cells.sum():,} cells -> {OUT}")
    print(f"hemilineage assigned: {(df.hemilineage != '').sum()} types, "
          f"{df.loc[df.hemilineage != '', 'n_cells'].sum():,} cells")
    print(df.groupby("mode").n_cells.agg(["size", "sum"]).rename(columns={"size": "types", "sum": "cells"}))
    top = df.assign(cc=df.circuit_class.str.replace(r"^vnc_local_.*", "vnc_local_<hl>", regex=True))
    print(top.groupby("cc").n_cells.agg(["size", "sum"]).sort_values("sum", ascending=False).to_string())


if __name__ == "__main__":
    main()
