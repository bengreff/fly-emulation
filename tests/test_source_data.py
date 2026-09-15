"""Validation tests for the source data every model will rest on.

These check properties of the connectome annotations themselves, not of any
particular simulation. They survived the session-1 rewrite because they test
the data, and the data is what the inventory is built from.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
EXT = REPO / "external" / "Pugliese_cpg_2025"
DATA = EXT / "data" / "manc t1 connectome data"
WTABLE = DATA / "wTable_20250813_DNtoMN_unsorted_withModules.csv"
WMATRIX = DATA / "W_20250813_DNtoMN_unsorted.csv"
DERIVED = REPO / "data" / "derived" / "manc_leg_motor_neurons.csv"

pytestmark = pytest.mark.skipif(
    not WTABLE.exists(), reason="reference connectome extract not present")


def _wtable() -> pd.DataFrame:
    return pd.read_csv(WTABLE, index_col=0, low_memory=False)


def _w() -> np.ndarray:
    return pd.read_csv(WMATRIX).drop(columns="bodyId_pre").to_numpy(float)


def test_weight_matrix_is_signed_square_and_integer():
    W = _w()
    assert W.shape[0] == W.shape[1] == 4604
    assert (W > 0).any() and (W < 0).any(), "signs must already be applied"
    nz = W[W != 0]
    assert np.all(np.mod(nz, 1) == 0), "weights are synapse counts, so integers"


def test_dale_principle_holds():
    """Every neuron's outgoing connections share one sign.

    Required for any sign-level manipulation to be well defined.
    """
    W = _w()
    has_pos = (W > 0).any(axis=1)
    has_neg = (W < 0).any(axis=1)
    assert not (has_pos & has_neg).any(), "a neuron has both signs outgoing"


@pytest.mark.skipif(not DERIVED.exists(), reason="run the neuPrint extraction first")
def test_anatomical_identity_join_is_total_and_exact():
    """Every motor neuron maps to an annotation on exact integer bodyId."""
    wt = _wtable()
    manc = pd.read_csv(DERIVED)
    wt_mn = wt[wt["class"] == "motor neuron"].copy()
    fl = manc[manc.leg == "fl"].copy()
    wt_mn["bodyId"] = wt_mn["bodyId"].astype("int64")
    fl["bodyId"] = fl["bodyId"].astype("int64")
    assert len(wt_mn) == len(fl) == 144
    assert set(wt_mn.bodyId) == set(fl.bodyId)
    assert fl.muscle.notna().all(), "every motor neuron needs a target muscle"


@pytest.mark.skipif(not DERIVED.exists(), reason="run the neuPrint extraction first")
def test_tibia_flexor_pool_matches_independent_electrophysiology():
    """Azevedo et al. 2020 report ~15 motor neurons for tibia flexion,
    measured without this connectome. The annotation gives exactly 15 per side."""
    manc = pd.read_csv(DERIVED)
    fl = manc[manc.leg == "fl"]
    tf = fl[fl.muscle.isin(["Ti flexor", "Acc. ti flexor"])]
    per_side = tf.somaSide.value_counts()
    assert set(per_side.index) == {"LHS", "RHS"}
    assert per_side["LHS"] == per_side["RHS"] == 15


def test_glutamate_carries_a_large_share_of_inhibition():
    """Finding F-SIGN-1. If this share moves, the sign convention matters less
    and the finding must be restated with the new number."""
    W = _w()
    wt = _wtable()
    glu = wt.index[wt["predictedNt"] == "glutamate"].values
    share = np.abs(W[glu, :]).sum() / -W[W < 0].sum()
    assert 0.35 < share < 0.45, f"glutamate share of inhibition is {share:.3f}"


def test_transmitter_confidence_is_low_for_sensory_neurons():
    """Finding F-SIGN-2. Sensory afferents are the least confidently typed
    population, and they are the ones whose sign the model gets wrong."""
    wt = _wtable()
    sens = wt["class"].isin(["sensory neuron", "sensory ascending"])
    assert wt.loc[sens, "predictedNtProb"].mean() < 0.75
    assert wt.loc[~sens, "predictedNtProb"].mean() > 0.80


def test_soma_size_differs_systematically_by_class():
    """Finding F-EXCITE-1. The size column measures a whole cell for nerve-cord
    neurons and only an axon arbor for sensory and descending neurons, so using
    it as an excitability proxy mis-scales exactly the input populations."""
    wt = _wtable()
    med = float(np.nanmedian(wt["size"].values.astype(float)))
    sens = float(np.nanmedian(
        wt.loc[wt["class"] == "sensory neuron", "size"].values.astype(float))) / med
    intr = float(np.nanmedian(
        wt.loc[wt["class"] == "intrinsic neuron", "size"].values.astype(float))) / med
    assert sens < 0.2, f"sensory relative size {sens:.3f}"
    assert 0.8 < intr < 1.2, f"intrinsic relative size {intr:.3f}"
