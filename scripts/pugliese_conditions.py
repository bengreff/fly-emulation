"""Reproduce and probe the Pugliese et al. connectome-constrained VNC rate model.

First executable milestone (docs/ROADMAP.md, "First session", step 3-4).

Runs a named condition on the MANC T1 descending-to-motor network and reports
quantitative readouts: how many neurons are active, how rhythmic the motor
output is, at what frequency, and which leg motor modules are recruited.

Conditions
----------
baseline       Left DNg100 stimulated. Reproduction target.
silence_i1i2   Same, with IN19A007 + IN16B036 (LHS) removed.
shuffle        Same stimulus, connectivity shuffled within transmitter/class
               groups. Preserves out-degree and weight distributions, destroys
               cell identity. This is the "does the specific graph matter" control.
dna02          Left DNa02 (turning descending neuron) stimulated instead.
no_stim        No stimulation. Checks the network is quiescent without drive.

Every condition imposes an artificial tonic current on a descending neuron.
That is a scaffold, not spontaneous behavior, and is declared in the run record.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
EXT = REPO / "external" / "Pugliese_cpg_2025"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(EXT))

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402

from flyemu.provenance import RunRecord  # noqa: E402
from src.simulation.vnc_sim import (  # noqa: E402
    prepare_neuron_params,
    prepare_sim_params,
    reweight_connectivity,
    run_single_simulation,
)
from src.utils.shuffle_utils import full_shuffle  # noqa: E402
from src.utils.sim_utils import compute_oscillation_score, load_wTable  # noqa: E402

CONDITIONS = ("baseline", "silence_i1i2", "shuffle", "dna02", "no_stim")


def build_config(experiment: str = "DNg100_Stim") -> OmegaConf:
    """Compose the external repo's YAML configs without Hydra's path magic."""
    cfg = OmegaConf.create({"paths": {"data_dir": str(EXT / "data")}})
    for group, name in (
        ("experiment", experiment),
        ("sim", "default"),
        ("neuron_params", "default"),
    ):
        part = OmegaConf.load(str(EXT / "configs" / group / f"{name}.yaml"))
        cfg = OmegaConf.merge(cfg, OmegaConf.create({group: part}))
    return cfg


def apply_condition(cfg, wTable, condition: str):
    """Mutate the config for one condition. Returns (cfg, notes)."""
    notes = {}
    if condition == "baseline":
        notes["stim"] = "left DNg100 (bodyId 10093, index 31) at I=250"
    elif condition == "silence_i1i2":
        idxs = wTable.loc[
            wTable["type"].isin(["IN19A007", "IN16B036"]) & (wTable["somaSide"] == "LHS")
        ].index.tolist()
        cfg.experiment.removeNeurons = [idxs]
        notes["stim"] = "left DNg100 at I=250"
        notes["removed_indices"] = idxs
        notes["removed_bodyIds"] = wTable.loc[idxs, "bodyId"].tolist()
    elif condition == "shuffle":
        notes["stim"] = "left DNg100 at I=250; W shuffled within class/transmitter groups"
    elif condition == "dna02":
        idxs = wTable.loc[wTable["bodyId"] == 10126].index.tolist()
        if not idxs:
            raise SystemExit("DNa02 bodyId 10126 not present in this wTable version")
        cfg.experiment.stimNeurons = [idxs]
        cfg.experiment.stimI = [[300]]
        notes["stim"] = f"left DNa02 (bodyId 10126, index {idxs[0]}) at I=300"
    elif condition == "no_stim":
        cfg.experiment.stimI = [[0]]
        notes["stim"] = "none (I=0); quiescence control"
    else:
        raise SystemExit(f"unknown condition {condition}")
    return cfg, notes


def fft_frequency_hz(R: np.ndarray, rows: np.ndarray, t: np.ndarray,
                     t_lo: float = 0.5, t_hi: float = 1.9,
                     f_min: float = 0.5) -> float:
    """Independent dominant-frequency estimate in Hz, by periodogram.

    Cross-check on the external library's oscillation frequency, which it
    reports in cycles per sample rather than Hz. Returns NaN if nothing
    oscillates.
    """
    if len(rows) == 0:
        return float("nan")
    dt = float(np.median(np.diff(t)))
    win = (t >= t_lo) & (t <= t_hi)
    if win.sum() < 16:
        return float("nan")
    freqs = np.fft.rfftfreq(int(win.sum()), d=dt)
    band = freqs >= f_min
    if not band.any():
        return float("nan")
    peaks = []
    for i in rows:
        x = R[i][win].astype(np.float64)
        if x.max() - x.min() <= 0:
            continue
        x = x - x.mean()
        P = np.abs(np.fft.rfft(x)) ** 2
        peaks.append(freqs[band][int(np.argmax(P[band]))])
    return float(np.median(peaks)) if peaks else float("nan")


def metrics_for(R: np.ndarray, wTable: pd.DataFrame, mn_idx: np.ndarray, t_axis) -> dict:
    """Quantitative readouts for one simulated replicate.

    R has shape (n_neurons, n_timepoints) in spikes/second.

    Units note: the external compute_oscillation_score builds its time axis as
    arange(n_samples), so its "frequency" is cycles per sample. Multiplying by
    the sampling rate 1/dt converts to Hz. Verified against an independent FFT
    estimate; see docs/FINDINGS.md.
    """
    t = np.asarray(t_axis)
    dt = float(np.median(np.diff(t)))
    fs = 1.0 / dt

    peak = R.max(axis=1)
    active = peak > 0.0
    osc, freq_cps = compute_oscillation_score(jnp.asarray(R), jnp.asarray(active))

    mn_active_mask = np.zeros(R.shape[0], dtype=bool)
    mn_active_mask[mn_idx] = True
    mn_active_mask &= active
    mn_osc, mn_freq_cps = compute_oscillation_score(
        jnp.asarray(R), jnp.asarray(mn_active_mask)
    )

    active_mn_rows = np.where(mn_active_mask)[0]
    modules = wTable.loc[active_mn_rows, "motor module"].value_counts().to_dict()

    # Steady-state window: late in the stimulus, past the onset transient.
    ss = (t >= 1.4) & (t <= 1.9)
    # Amplitude of the rhythm matters for later embodiment: a motor neuron
    # oscillating between 0 and 0.1 Hz cannot drive a muscle.
    if active_mn_rows.size:
        mn_ss = R[np.ix_(active_mn_rows, ss)]
        mn_peak_rates = R[active_mn_rows].max(axis=1)
        mn_swing = float(np.median(mn_ss.max(axis=1) - mn_ss.min(axis=1)))
        mn_peak_median = float(np.median(mn_peak_rates))
        mn_peak_max = float(mn_peak_rates.max())
        mn_mean_ss = float(mn_ss.mean())
    else:
        mn_swing = mn_peak_median = mn_peak_max = mn_mean_ss = 0.0

    return {
        "n_active": int(active.sum()),
        "n_active_mn": int(mn_active_mask.sum()),
        "n_mn_total": int(len(mn_idx)),
        "oscillation_score_all_active": float(osc),
        "oscillation_score_mn": float(mn_osc),
        "oscillation_freq_hz_all_active": float(freq_cps) * fs,
        "oscillation_freq_hz_mn": float(mn_freq_cps) * fs,
        "fft_freq_hz_mn": fft_frequency_hz(R, active_mn_rows, t),
        "mean_rate_active_hz": float(R[active].mean()) if active.any() else 0.0,
        "max_rate_hz": float(peak.max()),
        "mn_peak_rate_median_hz": mn_peak_median,
        "mn_peak_rate_max_hz": mn_peak_max,
        "mn_rhythm_swing_median_hz": mn_swing,
        "mean_mn_rate_steady_hz": mn_mean_ss,
        "n_high_rate_over_100hz": int((peak > 100).sum()),
        "active_motor_modules": {str(k): int(v) for k, v in modules.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=CONDITIONS)
    ap.add_argument("--replicates", type=int, default=8,
                    help="independent biophysical parameter draws")
    ap.add_argument("--rtol", type=float, default=2e-6, help="paper value 2e-6")
    ap.add_argument("--atol", type=float, default=5e-9, help="paper value 5e-9")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=str(REPO / "runs"))
    ap.add_argument("--tag", default="", help="suffix for the run id")
    ap.add_argument("--save-traces", action="store_true",
                    help="store the full rate matrix for replicate 0")
    ap.add_argument("--exc-mult", type=float, default=None,
                    help="override excitatory synaptic multiplier (default 0.03)")
    ap.add_argument("--inh-mult", type=float, default=None,
                    help="override inhibitory synaptic multiplier (default 0.03)")
    ap.add_argument("--stim-amp", type=float, default=None,
                    help="override stimulus current amplitude")
    ap.add_argument("--sensory-amp", type=float, default=None,
                    help="tonic current applied to leg proprioceptors "
                         "(chordotonal organ, hair plate, campaniform sensilla). "
                         "A swept unknown, not a measured value: no published "
                         "spike-rate calibration exists for these afferents.")
    args = ap.parse_args()

    tol_tag = "papertol" if args.rtol <= 2e-6 else f"rtol{args.rtol:g}"
    mult_tag = ""
    if args.exc_mult is not None or args.inh_mult is not None:
        mult_tag = f"-e{args.exc_mult if args.exc_mult is not None else 0.03:g}"
        mult_tag += f"i{args.inh_mult if args.inh_mult is not None else 0.03:g}"
    if args.stim_amp is not None:
        mult_tag += f"-I{args.stim_amp:g}"
    if args.sensory_amp is not None:
        mult_tag += f"-S{args.sensory_amp:g}"
    run_id = f"pugliese-{args.condition}-n{args.replicates}-{tol_tag}{mult_tag}{args.tag}"
    out_dir = Path(args.out) / run_id
    rec = RunRecord(run_id, out_dir,
                    description=f"Pugliese MANC T1 VNC rate model, condition={args.condition}")
    rec.add_code("pugliese_repo", EXT)

    cfg = build_config()
    cfg.experiment.n_replicates = args.replicates
    cfg.experiment.seed = args.seed
    cfg.sim.rtol = args.rtol
    cfg.sim.atol = args.atol
    if args.exc_mult is not None:
        cfg.neuron_params.excitatoryMultiplier = args.exc_mult
    if args.inh_mult is not None:
        cfg.neuron_params.inhibitoryMultiplier = args.inh_mult

    wTable = load_wTable(cfg.experiment.dfPath)
    cfg, notes = apply_condition(cfg, wTable, args.condition)
    if args.stim_amp is not None:
        cfg.experiment.stimI = [[args.stim_amp] * len(cfg.experiment.stimNeurons[0])]
        notes["stim_amp_override"] = args.stim_amp
    if args.sensory_amp is not None:
        prop = wTable.loc[
            wTable["subclass"].isin(["chordotonal organ", "hair plate",
                                     "campaniform sensilla"])
        ].index.tolist()
        cfg.experiment.stimNeurons = [list(cfg.experiment.stimNeurons[0]) + prop]
        cfg.experiment.stimI = [list(cfg.experiment.stimI[0])
                                + [args.sensory_amp] * len(prop)]
        notes["proprioceptors_driven"] = len(prop)
        notes["sensory_amp"] = args.sensory_amp
        notes["proprioceptor_breakdown"] = (
            wTable.loc[prop, "subclass"].value_counts().to_dict())

    rec.add_input("W", cfg.experiment.wPath, "MANC T1 DN-to-MN connectivity, signed by predicted transmitter")
    rec.add_input("wTable", cfg.experiment.dfPath, "neuron annotation table with motor module assignments")
    rec.add_config(cfg)
    rec.rec["condition"] = args.condition
    rec.rec["condition_notes"] = notes
    rec.declare_scaffold(
        "Tonic current injected directly into a descending neuron; no sensory input, "
        "no body, no muscles. Reproduces an optogenetic experiment, not spontaneous behavior."
    )
    if args.sensory_amp is not None:
        rec.declare_scaffold(
            f"Proprioceptive afferents driven by an imposed tonic current of "
            f"{args.sensory_amp}, not by a body. No measured spike-rate "
            f"calibration exists for these neurons; this is a swept unknown "
            f"used to ask how much sensory drive would be required."
        )
    rec.declare_scaffold(
        "Synaptic sign taken from EM transmitter prediction; weight is synapse count "
        "times a single global multiplier. Not measured physiological efficacy."
    )

    print(f"[{run_id}] preparing parameters ...", flush=True)
    t0 = time.time()
    neuronParams = prepare_neuron_params(cfg, wTable)
    nNeurons = int(neuronParams.W.shape[0])
    simParams = prepare_sim_params(cfg, 1, nNeurons)
    mn_idx = np.asarray(neuronParams.mn_idxs)
    print(f"  {nNeurons} neurons, {len(mn_idx)} motor neurons, "
          f"setup {time.time()-t0:.1f}s", flush=True)

    W_base = neuronParams.W
    rows = []
    for i in range(args.replicates):
        t1 = time.time()
        W = W_base * neuronParams.W_mask[i]
        if args.condition == "shuffle":
            W = full_shuffle(
                W, jax.random.PRNGKey(1000 + i),
                neuronParams.exc_dn_idxs, neuronParams.inh_dn_idxs,
                neuronParams.exc_in_idxs, neuronParams.inh_in_idxs,
                neuronParams.mn_idxs,
            )
        Wr = reweight_connectivity(W, simParams.exc_multiplier, simParams.inh_multiplier)
        R = run_single_simulation(
            Wr, neuronParams.tau[i], neuronParams.a[i], neuronParams.threshold[i],
            neuronParams.fr_cap[i], neuronParams.input_currents[0][i],
            simParams.noise_stdv, simParams.t_axis, simParams.T, simParams.dt,
            simParams.pulse_start, simParams.pulse_end,
            simParams.r_tol, simParams.a_tol, jax.random.PRNGKey(i),
        )
        R.block_until_ready()
        Rn = np.asarray(R)
        m = metrics_for(Rn, wTable, mn_idx, simParams.t_axis)
        m["replicate"] = i
        m["sim_seconds"] = round(time.time() - t1, 2)
        rows.append(m)
        print(f"  rep {i}: active={m['n_active']:4d} activeMN={m['n_active_mn']:3d} "
              f"oscMN={m['oscillation_score_mn']:.3f} fMN={m['oscillation_freq_hz_mn']:.2f}Hz "
              f"({m['sim_seconds']}s)", flush=True)
        if i == 0 and args.save_traces:
            np.savez_compressed(out_dir / "R_replicate0.npz",
                                R=Rn.astype(np.float32), t=np.asarray(simParams.t_axis),
                                mn_idx=mn_idx)

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "metrics.csv", index=False)

    numeric = [c for c in df.columns if df[c].dtype.kind in "fi" and c != "replicate"]
    summary = {c: {"mean": float(df[c].mean()), "std": float(df[c].std(ddof=1)) if len(df) > 1 else 0.0,
                   "min": float(df[c].min()), "max": float(df[c].max())} for c in numeric}
    rec.result("per_replicate_summary", summary)
    rec.result("n_neurons", nNeurons)
    rec.result("n_motor_neurons", int(len(mn_idx)))
    module_union: dict[str, int] = {}
    for r in rows:
        for k, v in r["active_motor_modules"].items():
            module_union[k] = max(module_union.get(k, 0), v)
    rec.result("active_motor_modules_max_across_replicates", module_union)
    p = rec.finish()

    print(f"\n[{run_id}] done in {rec.rec['wall_seconds']}s, peak RSS {rec.rec['peak_rss_gb']} GB")
    print(f"  metrics:    {out_dir/'metrics.csv'}")
    print(f"  provenance: {p}")
    print(f"  MN oscillation score {df['oscillation_score_mn'].mean():.3f} "
          f"+/- {df['oscillation_score_mn'].std(ddof=1) if len(df)>1 else 0:.3f}")
    print(f"  MN frequency {df['oscillation_freq_hz_mn'].mean():.2f} Hz "
          f"(independent FFT {df['fft_freq_hz_mn'].mean():.2f} Hz)")
    print(f"  MN peak rate median {df['mn_peak_rate_median_hz'].mean():.2f} Hz, "
          f"max {df['mn_peak_rate_max_hz'].max():.2f} Hz")
    print(f"  active MNs {df['n_active_mn'].mean():.1f} of {len(mn_idx)}")


if __name__ == "__main__":
    main()
