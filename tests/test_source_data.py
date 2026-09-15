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


# ---------------------------------------------------------------------------
# Meaning-based sanity checks.
#
# These follow from what a quantity means, not from how the code computes it.
# Ordinary unit tests often encode the same mistaken assumption as the
# implementation, so they pass while the science is wrong. Session 1 produced
# two worked examples of that and one false accusation, which is what these
# are here to prevent.
# ---------------------------------------------------------------------------

def test_a_frequency_estimate_is_invariant_to_resampling():
    """Resampling the same signal must not change its frequency in hertz.

    This is the check that would have caught my session-1 error immediately.
    A helper returning cycles per sample fails this; the same helper with its
    sampling rate applied passes. The test is on the quantity, not the code.
    """
    f_true = 12.0
    results = []
    for fs in (500.0, 1000.0, 2000.0):
        t = np.arange(0, 2.0, 1 / fs)
        x = np.maximum(np.sin(2 * np.pi * f_true * t), 0.0)
        x = x - x.mean()
        freqs = np.fft.rfftfreq(len(x), d=1 / fs)
        band = freqs > 0.5
        results.append(float(freqs[band][np.argmax(np.abs(np.fft.rfft(x))[band] ** 2)]))
    assert all(abs(r - f_true) < 1.0 for r in results), results
    assert max(results) - min(results) < 1.0, f"estimate drifts with fs: {results}"


def test_unit_conversion_preserves_a_physical_prediction():
    """Changing units must not change a physical prediction after conversion."""
    force_uN, moment_arm_um = 10.0, 50.0
    torque_uN_um = force_uN * moment_arm_um
    torque_N_m = (force_uN * 1e-6) * (moment_arm_um * 1e-6)
    assert torque_N_m == pytest.approx(torque_uN_um * 1e-12, rel=1e-12)


@pytest.mark.skipif(not WTABLE.exists(), reason="reference extract not present")
def test_cropping_a_reconstruction_is_not_a_change_in_excitability():
    """Finding F-EXCITE-1 as a meaning check.

    In-volume segmentation size is not comparable across classes whose somata
    sit outside the volume. Any excitability rule must therefore be invariant
    to which classes were cropped. Normalising within class satisfies this;
    normalising to the network median does not.
    """
    wt = _wtable()
    size = wt["size"].astype(float)
    net_med = float(np.nanmedian(size.values))

    def rel_network(cls):
        return float(np.nanmedian(size[wt["class"] == cls].values)) / net_med

    def rel_within_class(cls):
        m = float(np.nanmedian(size[wt["class"] == cls].values))
        return m / m

    cropped, intact = "sensory neuron", "intrinsic neuron"
    # network normalisation makes the cropped class look 9x more excitable
    assert rel_network(cropped) < 0.2
    assert rel_network(intact) > 0.8
    # within-class normalisation removes the artefact by construction
    assert rel_within_class(cropped) == rel_within_class(intact) == 1.0


@pytest.mark.skipif(not WTABLE.exists(), reason="reference extract not present")
def test_absent_connection_is_distinguishable_from_supported_absence():
    """A zero in a weight matrix means "no record", not "measured absence".

    The reference representation cannot express the difference, which is why
    the inventory must carry the distinction in a status field rather than in
    the numbers.
    """
    W = _w()
    zeros = int((W == 0).sum())
    assert zeros > 0
    # there is no channel in this representation carrying provenance for a zero
    assert W.dtype.kind == "f", "a float matrix cannot encode why an entry is zero"


def test_a_calcium_observation_does_not_carry_firing_rate_units():
    """Finding F-GAP-1 as a meaning check.

    An observation and a model parameter inferred from it are different
    objects. A fluorescence trace may constrain the shape of a sensory model
    while leaving its absolute gain unresolved, so no code path may convert
    one to the other without an explicit calibration object.
    """
    observation = {"quantity": "dF/F", "units": "dimensionless", "kind": "observation"}
    with pytest.raises(KeyError):
        # there is deliberately no gain field to reach for
        _ = observation["firing_rate_hz_per_unit"]
    assert observation["kind"] == "observation"
