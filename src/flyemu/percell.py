"""Per-cell values inferred from biology within a cell type (session 11).

Cell type explains most connectome variation, but the rest is structured: within
a type, larger cells have more input synapses (median r = 0.67) and motor pools
spread 50-77x in input (F-VAR-1). A single compartment of membrane area A has
capacitance ~ A and input resistance ~ 1/A, so one synaptic charge moves its
voltage ~ 1/A; the motor size principle (Azevedo et al. 2020) is this effect.
Homeostatic development tunes total synaptic drive against input number (Tobin,
Wilson & Lee 2017, lead). Both are rules with one class-level exponent each:

    input_gain_i *= (G_t(size) / size_i)^alpha * (G_t(n_in) / n_in_i)^beta

G_t is the geometric mean over the cell's type t, so each type's geometric-mean
gain is unchanged: the rules add within-type structure and leave every type- and
class-level value (and its calibration) where it was. Untyped cells, types with
one cell and cells without a size keep factor 1. size is the male-cns voxel
volume, a proxy for membrane area (inferred; area ~ volume for thin neurites of
fixed calibre). n_in is the modelled input synapse count (edges >= the build's
threshold). At alpha = beta = 0 nothing is computed (bit-identical to before).
Cells with < 0.25x their type's median input count are taken as reconstruction-
incomplete (session 11 repair 1, after MN9_R: 633 vs 6,358 inputs): factor 1, and
excluded from the type reference.

F-SIZE-1 (session 4) rejected a *global* size rule (median over all cells,
factors 0.002x-2,896x); this rule is within type (factor 0.78-1.30 for the
10-90% range at alpha = 1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .registry import Registry


def within_type_ratio(values: np.ndarray, types: pd.Series, min_cells: int = 2,
                      exclude: np.ndarray | None = None) -> np.ndarray:
    """G_t / v_i per cell (geometric mean of v over the cell's type), 1 where undefined
    or excluded (excluded cells neither get a factor nor enter the reference)."""
    v = np.asarray(values, np.float64)
    ok = np.isfinite(v) & (v > 0) & types.fillna("").ne("").to_numpy()
    if exclude is not None:
        ok &= ~exclude
    lv = pd.Series(np.where(ok, np.log(np.where(ok, v, 1.0)), np.nan))
    t = types.fillna("").reset_index(drop=True)
    g = lv.groupby(t).transform("mean")
    k = lv.notna().groupby(t).transform("sum")
    r = np.exp(g - lv).to_numpy()
    return np.where(ok & (k.to_numpy() >= min_cells) & np.isfinite(r), r, 1.0)


COMPLETE_FRACTION = 0.25


def incomplete(n_in: np.ndarray, types: pd.Series) -> np.ndarray:
    """Cells with < COMPLETE_FRACTION of their type's median postsynapse count: taken as
    reconstruction-incomplete (e.g. MN9_R, 633 vs 6,358 inputs for MN9_L)."""
    med = pd.Series(n_in).groupby(types.fillna("").to_numpy()).transform("median").to_numpy()
    return types.fillna("").ne("").to_numpy() & (n_in < COMPLETE_FRACTION * med)


def input_counts(conn) -> np.ndarray:
    """Modelled input synapses per cell (sum of synapse counts over incoming edges)."""
    return np.bincount(conn.indices, weights=conn.weight_syn.astype(np.float64), minlength=conn.n)


def input_gain_factors(reg: Registry, conn) -> np.ndarray | None:
    """Per-cell multiplier on input_gain from the within-type rules, or None at neutral."""
    alpha = reg.require(
        "cell_type:all", "within_type_size_exponent", units="dimensionless",
        model_use="input gain x (type geometric-mean size / cell size)^alpha",
        subsystem="neuron_biophysics", instances=conn.n, minimal=0.0, conventional=0.0,
        minimal_note="neutral 0: every cell of a type has the type's input gain",
        uncertainty="alpha = 1 for an isopotential cell whose membrane area scales with "
                    "voxel volume; rows n2p_size_exponent in data/model/parameters.csv")
    beta = reg.require(
        "cell_type:all", "within_type_input_exponent", units="dimensionless",
        model_use="input gain x (type geometric-mean input count / cell input count)^beta",
        subsystem="synaptic_efficacy", instances=conn.n, minimal=0.0, conventional=0.0,
        minimal_note="neutral 0: no homeostatic compensation of input number",
        uncertainty="homeostatic compensation of total drive (Tobin, Wilson & Lee 2017, lead); "
                    "rows n5p_input_exponent in data/model/parameters.csv")
    motor = conn.neurons.superclass.isin(["vnc_motor", "cb_motor"]).to_numpy()
    alpha_mn = reg.require(
        "cell_type:motor", "within_type_size_exponent", units="dimensionless",
        model_use="as cell_type:all|within_type_size_exponent, for motor neurons (which "
                  "then ignore the global exponent)",
        subsystem="neuron_biophysics", instances=int(motor.sum()), minimal=0.0, conventional=0.0,
        minimal_note="neutral 0: every motor neuron of a type has the type's input gain",
        uncertainty="1.49 = slope of log input resistance (Azevedo 2020 Fig 3E, 150/300/700 MOhm "
                    "fast/intermediate/slow) on log EM volume of volume-ranked flexor classes; "
                    "rows n2p_size_exponent_motor")
    if not alpha and not beta and not alpha_mn:
        return None
    types = conn.neurons.type.reset_index(drop=True)
    n_in = input_counts(conn)
    # completeness from the cell's total postsynapse count in male-cns (all partners)
    bad = incomplete(conn.neurons["post"].to_numpy(np.float64), types)
    f = np.ones(conn.n)
    if alpha or alpha_mn:
        r = within_type_ratio(conn.neurons["size"].to_numpy(np.float64), types, exclude=bad)
        f *= r ** np.where(motor, alpha_mn, alpha)
    if beta:
        f *= within_type_ratio(n_in, types, exclude=bad) ** beta
    return f.astype(np.float32)
