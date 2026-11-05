"""The worm's measured structure, as the brain uses it: the cell list, both wiring graphs, CeNGEN expression per
neuron class, transmitter identity and Virtual Worm geometry. Everything here is data (measured or a fixed naming
rule); no fitted or guessed number lives in this module. Guessed geometry conventions (the body-axis scale used to
place somata along s) are ledger parameters and are passed in.

Sources (all under data/worm/structure, extracted by scripts/worm/extract_structure.py and extract_geometry.py;
pinned in docs/worm/MANIFEST.md):
  cells.csv, chem_edges.csv, gap_edges.csv   Cook et al. 2019 Nature 571:63, SI 4 cell list and SI 5 adjacency
                                             (hermaphrodite, corrected July 2020)
  cengen_t2.csv                              CeNGEN (Taylor et al. 2021 Cell 184:4329), threshold 2 (medium), TPM
  transmitters_wang2024.csv                  Wang et al. 2024 eLife 13:e95402 reporter-allele atlas, as mapped on the
                                             Cook graph by the OpenWorm ConnectomeToolbox (Wang2024Herm, fetched 5 Nov)
  geometry.csv                               OpenWorm CElegansNeuroML (Virtual Worm) soma positions and membrane area
  peptide_gpcr_pairs.csv                     Ripoll-Sanchez et al. 2023 Neuron, ligand-receptor pairs with
                                             EC50 <= 500 nM (from Beets et al. 2023)
  monoamine_receptor_pairs.csv               Bentley et al. 2016 PLoS Comput Biol, via Ripoll-Sanchez 2023
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

from .interface import BWM_NAMES, ENTERIC_MUSCLES, PHARYNX_MUSCLES, SEX_MUSCLES

ROOT = Path(__file__).resolve().parents[2]
STRUCT = ROOT / "data" / "worm" / "structure"


# --- names -------------------------------------------------------------------------------------------------------
def canon(name: str) -> str:
    """One spelling per cell: the Cook 2019 SI 5 adjacency spelling (SI 4 writes some names in lower case)."""
    n = name.strip()
    if n == "mu_sphincter":
        return "mu_sph"
    if n == "g1P":
        return "g1p"
    m = re.fullmatch(r"pm([2-7])(d|vl|vr)", n)
    if m:
        return f"pm{m.group(1)}{m.group(2).upper()}"
    m = re.fullmatch(r"mc([1-3])(dl|dr|v)", n)
    if m:
        return f"mc{m.group(1)}{m.group(2).upper()}"
    m = re.fullmatch(r"(vm[12]|um[12])([ap])([LR])", n)
    if m:
        return f"{m.group(1)}{m.group(2).upper()}{m.group(3)}"
    m = re.fullmatch(r"(AS|DA|DB|DD|VA|VB|VC|VD)(\d+)", n)
    if m:
        return f"{m.group(1)}{int(m.group(2)):02d}"
    return n


# --- neuron -> CeNGEN class (a naming rule; AWC ON/OFF is drawn per individual, see cengen_class) -----------------
_VNC_CLASS = {"AS": "AS", "DD": "VD_DD", "VD": "VD_DD"}


def cengen_class(name: str, classes: set[str], awc_on: str = "L") -> str | None:
    """CeNGEN class of a neuron (None for non-neurons). awc_on: which AWC is AWC-ON in this individual ('L'/'R';
    measured: the choice is stochastic, about half each side, Troemel et al. 1999 Cell 99:387)."""
    if name in ("AWCL", "AWCR"):
        return "AWC_ON" if name[-1] == awc_on else "AWC_OFF"
    if name in classes:
        return name
    m = re.fullmatch(r"(AS|DA|DB|DD|VA|VB|VC|VD)(\d+)", name)
    if m:
        cls, k = m.group(1), int(m.group(2))
        if cls in _VNC_CLASS:
            return _VNC_CLASS[cls]
        special = {("DA", 9): "DA9", ("DB", 1): "DB01", ("VA", 12): "VA12", ("VB", 1): "VB01", ("VB", 2): "VB02",
                   ("VC", 4): "VC_4_5", ("VC", 5): "VC_4_5"}
        return special.get((cls, k), cls)
    if name.startswith("IL2"):
        return "IL2_DV" if name[3] in "DV" else "IL2_LR"
    if name.startswith("RMD"):  # RMDDL/RMDDR/RMDVL/RMDVR -> RMD_DV; RMDL/RMDR -> RMD_LR
        return "RMD_DV" if len(name) == 5 else "RMD_LR"
    if name in ("RMED", "RMEV"):
        return "RME_DV"
    if name in ("RMEL", "RMER"):
        return "RME_LR"
    for k in (1, 2):  # strip side / quadrant suffixes: AIYL -> AIY, CEPDL -> CEP, SAADL -> SAA, I1L -> I1
        if len(name) > k and name[:-k] in classes and re.fullmatch(r"[DVLR]+", name[-k:]):
            return name[:-k]
    return None


# --- BAAIWorm muscle cell -> body-wall muscle name (interface.BWM_NAMES) -------------------------------------------
BAAIWORM_NO_SUCH_MUSCLE = "MCVL24"


def bwm_name(baai: str) -> str | None:
    """MCDL01 -> dBWML1. None for MCVL24: BAAIWorm builds 4 x 24 muscles but the worm has 95 (no ventral-left 24;
    Cook 2019 has no vBWML24). Checked 5 Nov against Cook 2019 neuron->muscle edges: of BAAIWorm's 552 placed NMJ
    pairs, 337 are Cook edges under this map, 309 with the index shifted by -1, 278 by +1, 26 with D and V swapped."""
    if baai == BAAIWORM_NO_SUCH_MUSCLE:
        return None
    m = re.fullmatch(r"MC([DV])([LR])(\d\d)", baai)
    assert m, baai
    return f"{m.group(1).lower()}BWM{m.group(2)}{int(m.group(3))}"


# --- the structure object ----------------------------------------------------------------------------------------
NEURON_CATS = {"sensory", "interneuron", "motorneuron", "neuron"}
TRANSMITTERS = ["acetylcholine", "glutamate", "gaba", "dopamine", "serotonin", "tyramine", "octopamine", "betaine"]
# CeNGEN marker genes, the fallback for neurons the Wang 2024 table does not cover (no outgoing chemical synapse)
MARKERS = {"acetylcholine": ("unc-17",), "glutamate": ("eat-4",), "gaba": ("unc-25",), "dopamine": ("cat-2",),
           "serotonin": ("tph-1",), "tyramine": ("tdc-1",), "octopamine": ("tbh-1",)}


@dataclass
class Structure:
    names: list[str]                      # every cell, brain order
    kind: np.ndarray                      # neuron, bwm, pharynx_muscle, enteric_muscle, sex_muscle, glia, gland, ...
    category: list[str]                   # Cook 2019 category (sensory, interneuron, motorneuron, ...)
    soma_y_um: np.ndarray                 # Virtual Worm soma y (long axis), NaN where no geometry
    area_um2: np.ndarray                  # Virtual Worm membrane area (neurons only), NaN elsewhere
    chem: list[tuple[int, int, int]]      # (pre, post, EM synapse count)
    gap: list[tuple[int, int, int]]       # (a, b, EM gap-junction count), a < b
    genes: list[str]
    cengen_classes: list[str]
    tpm: np.ndarray                       # genes x classes, threshold-2 TPM (0 = below threshold)
    transmitter: dict[str, set[str]]      # neuron -> set of transmitters (Wang 2024, CeNGEN fallback)
    transmitter_source: dict[str, str]    # neuron -> "wang2024" | "cengen" | "none"
    peptide_pairs: list[tuple[str, str]]  # (ligand gene, receptor gene), lower case
    monoamine_pairs: list[tuple[str, str]]  # (transmitter, receptor gene)
    index: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.index = {n: i for i, n in enumerate(self.names)}
        self.gene_index = {g: i for i, g in enumerate(self.genes)}
        self.class_index = {c: i for i, c in enumerate(self.cengen_classes)}

    @property
    def n(self) -> int:
        return len(self.names)

    def of_kind(self, *kinds) -> np.ndarray:
        return np.isin(self.kind, kinds)

    def expr(self, gene: str, cls: str | None) -> float:
        """Threshold-2 TPM of a gene in a CeNGEN class (0 if below threshold, not in the subset, or no class)."""
        if cls is None or gene not in self.gene_index:
            return 0.0
        return float(self.tpm[self.gene_index[gene], self.class_index[cls]])


def _kind(name: str, cat: str) -> str:
    if cat in NEURON_CATS:
        return "neuron"
    if name in BWM_NAMES:
        return "bwm"
    if name in PHARYNX_MUSCLES:
        return "pharynx_muscle"
    if name in ENTERIC_MUSCLES:
        return "enteric_muscle"
    if name in SEX_MUSCLES:
        return "sex_muscle"
    if name.startswith(("CEPsh", "GLR")):
        return "glia"
    if re.fullmatch(r"g[12].*", name):
        return "gland"
    if name.startswith("mc"):
        return "marginal"
    if re.fullmatch(r"e[123].*", name):
        return "epithelium"
    return {"hyp": "hypodermis", "int": "intestine", "exc_gl": "excretory", "exc_cell": "excretory",
            "hmc": "head_mesoderm", "bm": "basement_membrane"}.get(name, "other")


def _rows(f: str) -> list[dict]:
    with open(STRUCT / f, encoding="utf-8-sig") as fh:
        return [r for r in csv.DictReader(fh) if any(v.strip() for v in r.values() if v)]


@lru_cache(maxsize=1)
def load_structure() -> Structure:
    cells = _rows("cells.csv")
    cat = {canon(r["name"]): r["category"] for r in cells}
    chem_rows = [(canon(r["pre"]), canon(r["post"]), int(r["n"])) for r in _rows("chem_edges.csv")]
    gap_rows = [(canon(r["a"]), canon(r["b"]), int(r["n"])) for r in _rows("gap_edges.csv")]
    edge_names = {a for a, b, _ in chem_rows} | {b for a, b, _ in chem_rows} | {a for a, b, _ in gap_rows} | {
        b for a, b, _ in gap_rows}
    for nm in edge_names:  # SI 5 nodes absent from the SI 4 list (exc_cell; e2D/e2VL/e2VR spelt e2DL/e2DR/e2V there)
        if nm not in cat:
            cat[nm] = "excretory" if nm.startswith("exc") else ("epithelium" if nm.startswith("e") else "other")
    # SI 4 names with no edge and a differently spelt SI 5 twin are dropped (e2DL/e2DR/e2V = e2D/e2VL/e2VR)
    for nm in ("e2DL", "e2DR", "e2V"):
        cat.pop(nm, None)
    neurons = [canon(r["name"]) for r in cells if r["category"] in NEURON_CATS]
    order = (neurons + list(BWM_NAMES) + PHARYNX_MUSCLES + ENTERIC_MUSCLES + SEX_MUSCLES
             + sorted(n for n in cat if n not in set(neurons) | set(BWM_NAMES) | set(PHARYNX_MUSCLES)
                      | set(ENTERIC_MUSCLES) | set(SEX_MUSCLES)))
    assert len(order) == len(set(order)), "duplicate cell names"
    missing = edge_names - set(order)
    assert not missing, f"edge cells missing from the cell list: {sorted(missing)}"
    idx = {n: i for i, n in enumerate(order)}
    kind = np.array([_kind(n, cat[n]) for n in order])

    geo = {canon(r["name"]): r for r in _rows("geometry.csv")}
    soma_y = np.array([float(geo[n]["soma_y"]) if n in geo else np.nan for n in order])
    area = np.array([float(geo[n]["area_um2"]) if n in geo else np.nan for n in order])

    with open(STRUCT / "cengen_t2.csv") as fh:
        r = csv.reader(fh)
        hdr = next(r)
        classes = hdr[3:]
        genes, vals = [], []
        for row in r:
            genes.append(row[1].strip('"'))
            vals.append([float(x) for x in row[3:]])
    tpm = np.array(vals)

    gi = {g: i for i, g in enumerate(genes)}
    tx, txs = {}, {}
    wang = {canon(r["name"]): {t for t in TRANSMITTERS if r[t] == "1"} for r in _rows("transmitters_wang2024.csv")}
    cls_set = set(classes)
    for n in neurons:
        if n in wang and wang[n]:
            tx[n], txs[n] = wang[n], "wang2024"
            continue
        c = cengen_class(n, cls_set)
        got = {t for t, gs in MARKERS.items() if c and any(g in gi and tpm[gi[g], classes.index(c)] > 0 for g in gs)}
        tx[n], txs[n] = got, ("cengen" if got else "none")

    pp = [tuple(x.lower() for x in (r["GeneLigand"], r["GeneGPCR"])) for r in _rows("peptide_gpcr_pairs.csv")]
    mono_name = {"Ser": "serotonin", "DA": "dopamine", "Oct": "octopamine", "Tyr": "tyramine"}
    mp = [(mono_name[r["Gene ligand"]], r["Gene GPCR"].lower()) for r in _rows("monoamine_receptor_pairs.csv")]

    return Structure(names=order, kind=kind, category=[cat[n] for n in order], soma_y_um=soma_y, area_um2=area,
                     chem=[(idx[a], idx[b], k) for a, b, k in chem_rows],
                     gap=[(idx[a], idx[b], k) for a, b, k in gap_rows],
                     genes=genes, cengen_classes=classes, tpm=tpm, transmitter=tx, transmitter_source=txs,
                     peptide_pairs=pp, monoamine_pairs=mp)
