"""Tests for the failure modes docs/VALIDATION.md calls out: units, anatomical
identity joins, and reproducibility. These are cheap and must always pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
EXT = REPO / "external" / "Pugliese_cpg_2025"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(EXT))

DATA = EXT / "data" / "manc t1 connectome data"
WTABLE = DATA / "wTable_20250813_DNtoMN_unsorted_withModules.csv"
DERIVED = REPO / "data" / "derived" / "manc_leg_motor_neurons.csv"

pytestmark = pytest.mark.skipif(not WTABLE.exists(), reason="external data not present")


def test_oscillation_frequency_is_cycles_per_sample_not_hz():
    """Finding F1. A 20 Hz sine sampled at 1 kHz must be recovered as 20 Hz
    only after multiplying the library value by the sampling rate."""
    from src.utils.sim_utils import compute_oscillation_score
    import jax.numpy as jnp

    fs, f_true = 1000.0, 20.0
    t = np.arange(0, 2.0, 1 / fs)
    sig = np.maximum(np.sin(2 * np.pi * f_true * t), 0.0)[None, :]
    score, freq_cps = compute_oscillation_score(jnp.asarray(sig), jnp.asarray([True]))

    assert float(score) > 0.5, "a pure rectified sine should score as oscillating"
    # Raw value is cycles per sample and must NOT be mistaken for Hz.
    assert float(freq_cps) < 1.0
    assert float(freq_cps) * fs == pytest.approx(f_true, rel=0.15)


def test_fft_cross_check_agrees_on_a_known_frequency():
    from pugliese_conditions import fft_frequency_hz

    fs, f_true = 1000.0, 12.0
    t = np.arange(0, 2.0, 1 / fs)
    sig = np.maximum(np.sin(2 * np.pi * f_true * t), 0.0)[None, :]
    est = fft_frequency_hz(sig, np.array([0]), t, t_lo=0.0, t_hi=2.0)
    assert est == pytest.approx(f_true, abs=1.0)


def test_weight_matrix_is_signed_and_square():
    from src.utils.sim_utils import load_W

    W = np.asarray(load_W(str(DATA / "W_20250813_DNtoMN_unsorted.csv")))
    assert W.shape[0] == W.shape[1] == 4604
    assert (W > 0).any() and (W < 0).any(), "signs must already be applied"
    nz = W[W != 0]
    assert np.all(np.mod(nz, 1) == 0), "weights are synapse counts, so integers"


def test_motor_neuron_count_matches_annotation():
    wt = pd.read_csv(WTABLE, index_col=0, low_memory=False)
    assert (wt["class"] == "motor neuron").sum() == 144


@pytest.mark.skipif(not DERIVED.exists(), reason="run the neuPrint extraction first")
def test_anatomical_identity_join_is_total_and_exact():
    """Finding F2. Every motor neuron in the simulated network must map to a
    MANC annotation on exact integer bodyId, with no silent loss."""
    wt = pd.read_csv(WTABLE, index_col=0, low_memory=False)
    manc = pd.read_csv(DERIVED)
    wt_mn = wt[wt["class"] == "motor neuron"].copy()
    fl = manc[manc.leg == "fl"].copy()

    wt_mn["bodyId"] = wt_mn["bodyId"].astype("int64")
    fl["bodyId"] = fl["bodyId"].astype("int64")

    assert len(wt_mn) == len(fl) == 144
    assert set(wt_mn.bodyId) == set(fl.bodyId), "bodyId sets must be identical"
    assert fl.muscle.notna().all(), "every motor neuron needs a target muscle"


@pytest.mark.skipif(not DERIVED.exists(), reason="run the neuPrint extraction first")
def test_tibia_flexor_pool_size_matches_independent_electrophysiology():
    """Finding F2. Azevedo et al. 2020 (eLife 56754) report ~15 motor neurons
    for tibia flexion, measured without this connectome."""
    manc = pd.read_csv(DERIVED)
    fl = manc[manc.leg == "fl"]
    tf = fl[fl.muscle.isin(["Ti flexor", "Acc. ti flexor"])]
    per_side = tf.somaSide.value_counts()
    assert set(per_side.index) == {"LHS", "RHS"}
    assert per_side["LHS"] == per_side["RHS"] == 15


def test_simulation_is_deterministic_for_a_fixed_seed():
    """Reproducible checkpoint continuation depends on this holding."""
    import jax
    from src.simulation.vnc_sim import reweight_connectivity, run_single_simulation

    n = 40
    rng = np.random.default_rng(0)
    W = jax.numpy.asarray(rng.normal(0, 5, (n, n)))
    Wr = reweight_connectivity(W, 0.03, 0.03)
    args = dict(
        tau=jax.numpy.full(n, 0.02), a=jax.numpy.ones(n),
        threshold=jax.numpy.full(n, 7.5), fr_cap=jax.numpy.full(n, 200.0),
        inputs=jax.numpy.zeros(n).at[0].set(250.0),
        noise_stdv=jax.numpy.asarray(0.0),
        t_axis=jax.numpy.arange(0, 0.2001, 0.001),
        T=0.2, dt=0.001, pulse_start=0.02, pulse_end=0.19,
        r_tol=1e-4, a_tol=1e-7,
    )
    k = jax.random.PRNGKey(0)
    r1 = np.asarray(run_single_simulation(Wr, key=k, **args))
    r2 = np.asarray(run_single_simulation(Wr, key=k, **args))
    assert np.array_equal(r1, r2)
    assert np.isfinite(r1).all()
