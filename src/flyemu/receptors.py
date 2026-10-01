"""Rung 2 (s11): slow-receptor shares per postsynaptic cell from transcriptomes.

For each cell, p(gene) = probability the cell expresses a receptor gene, taken in order of
precedence from (2) its type in Davis 2020 / Özel 2021 (`p_expressed`, mean where both),
(1) its VNC hemilineage in Allen 2020 (`frac_expressed`), (0) the mean over profiled types
(population prior). The share of a transmitter's input carried by the slow (metabotropic or
Mg-blocked) receptor is

    f = s p_slow / (s p_slow + p_fast)

with s = `receptor:<family>|slow_peak_ratio`, the slow current's peak per unit fast peak at
equal expression (rule parameter, searched within parameters.csv bounds). Every value is
inferred: expression is mRNA, not receptor protein at the synapse (DECISIONS 2026-10-01 00:45).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import channels as ichan

_REPO = Path(__file__).resolve().parents[2]
DAVIS = _REPO / "data/derived/receptor_calls_davis2020.csv"
OZEL = _REPO / "data/derived/receptor_calls_ozel2021.csv"
ALLEN = _REPO / "data/derived/receptor_calls_allen2020_vnc.csv"

# family -> (LIFParams field, slow genes (product), fast genes (max), guessed prior s)
FAMILIES = {
    "GABA_B": ("gabab_fraction", ("GABA-B-R1", "GABA-B-R2"), ("Rdl",), 0.05),
    "mAChR": ("machr_fraction", ("mAChR-A|mAChR-B",),
              ("nAChRalpha1", "nAChRalpha5", "nAChRalpha6", "nAChRalpha7"), 0.05),
    "mGluR": ("mglur_fraction", ("mGluR",), ("GluClalpha", "GluRIA", "GluRIB"), 0.05),
    "NMDA": ("nmda_fraction", ("Nmdar1", "Nmdar2"), ("GluRIA", "GluRIB"), 0.05),
}


def gene_probabilities(types: np.ndarray, body_ids: np.ndarray | None) -> tuple[pd.DataFrame, np.ndarray]:
    """(cells x genes) expression probability, and the source per cell (2 type, 1 hemilineage, 0 prior)."""
    n = len(types)
    d = pd.read_csv(DAVIS).pivot_table(index="male_cns_type", columns="gene", values="p_expressed")
    o = pd.read_csv(OZEL).pivot_table(index="male_cns_type", columns="gene", values="p_expressed")
    by_type = pd.concat([d, o]).groupby(level=0).mean()
    prior = by_type.mean()
    out = pd.DataFrame(np.tile(prior.to_numpy(), (n, 1)), columns=prior.index)
    src = np.zeros(n, np.int8)
    if body_ids is not None and ichan.HL_JOIN.exists() and ichan.HL_CELLS.exists():
        a = pd.read_csv(ALLEN)
        a = a[a.allen_hl != "ALL_NEURONS"].pivot_table(index="allen_hl", columns="gene",
                                                       values="frac_expressed")
        j = pd.read_csv(ichan.HL_JOIN)[["allen_hl", "trumanHl"]]
        j = j.assign(trumanHl=j.trumanHl.str.split("/")).explode("trumanHl").dropna()
        by_t = j.set_index("allen_hl").join(a.loc[a.index.intersection(j.allen_hl)], how="inner")
        by_t = by_t.set_index("trumanHl")
        by_t = by_t[~by_t.index.duplicated()]
        cells = pd.read_parquet(ichan.HL_CELLS, columns=["bodyId", "trumanHl"]).dropna()
        hl = pd.Series(cells.trumanHl.to_numpy(), index=cells.bodyId.to_numpy())
        hl = hl[~hl.index.duplicated()].reindex(body_ids)
        h = by_t.reindex(hl.to_numpy()).set_axis(range(n))
        have = h.notna().any(axis=1).to_numpy()
        for g in out.columns.intersection(h.columns):
            col = h[g].to_numpy()
            m = have & np.isfinite(col)
            out.loc[m, g] = col[m]
        src[have] = 1
    idx = pd.Index(by_type.index).get_indexer(types)
    m = idx >= 0
    t = by_type.reindex(columns=out.columns).to_numpy()[idx[m]]
    cur = out.to_numpy().copy()
    cur[m] = np.where(np.isfinite(t), t, cur[m])
    out = pd.DataFrame(cur, columns=out.columns)
    src[m] = 2
    return out, src


def _p(P: pd.DataFrame, spec: str) -> np.ndarray:
    """'a|b' = max of genes a, b."""
    return np.max(np.stack([P[g].to_numpy() for g in spec.split("|")]), axis=0)


def shares(P: pd.DataFrame, ratios: dict) -> dict:
    """{LIFParams field: per-cell slow share} for each family."""
    out = {}
    for fam, (field, slow, fast, _prior) in FAMILIES.items():
        ps = np.prod(np.stack([_p(P, g) for g in slow]), axis=0)
        pf = np.max(np.stack([_p(P, g) for g in fast]), axis=0)
        s = float(ratios[fam])
        den = s * ps + pf
        out[field] = np.where(den > 0, s * ps / np.where(den > 0, den, 1.0), 0.0).astype(np.float32)
    return out


def from_registry(reg, conn) -> tuple[dict, np.ndarray] | None:
    """Read the rung-2 receptor keys (always); None when the switch is off."""
    n = conn.n
    on = reg.require("cell_type:all", "receptor_shares_from_rna", units="boolean",
                     model_use="N7/N8 rung 2: slow-receptor shares per postsynaptic cell from "
                               "receptor mRNA (src/flyemu/receptors.py)",
                     subsystem="neuron_biophysics", instances=n, minimal=0.0, conventional=0.0,
                     minimal_note="neutral 0: the global gabab/mglur/machr/nmda fractions apply")
    ratios = {}
    for fam, (field, slow, fast, prior) in FAMILIES.items():
        ratios[fam] = reg.require(
            f"receptor:{fam}", "slow_peak_ratio", units="dimensionless",
            model_use=f"{field} = s p({'*'.join(slow)}) / (s p({'*'.join(slow)}) + p(max {'/'.join(fast)}))",
            subsystem="neuron_biophysics", instances=n, minimal=prior, conventional=prior,
            minimal_note="guessed: slow receptor current peak per unit fast peak at equal expression")
    if not on:
        return None
    P, src = gene_probabilities(conn.neurons.type.fillna("untyped").to_numpy(),
                                conn.neurons.bodyId.to_numpy())
    return shares(P, ratios), src
