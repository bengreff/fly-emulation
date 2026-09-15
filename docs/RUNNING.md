# Running the code

## Setup

Mac (orchestration and CPU work):

```bash
cd /Users/ben/fly-emulation
uv sync                                   # pinned Python 3.12 environment
git clone https://github.com/smpuglie/Pugliese_cpg_2025 external/Pugliese_cpg_2025
uv pip install -e external/Pugliese_cpg_2025
uv run pytest tests -q                    # 7 checks: units, identity joins, determinism
```

The neuPrint token lives at `~/.config/flyemu/neuprint_token`, mode 600, outside
the repository. It unlocks `manc`, `male-cns`, `hemibrain` and `optic-lobe` for
live queries, which avoids downloading multi-gigabyte dumps.

PC (`backhouse`, 28 cores under WSL2 Ubuntu). Its internet is blocked at the
router, so its environment was built from wheels shipped over the Tailscale SSH
link rather than from the network:

```bash
# on the Mac
pip download --platform manylinux2014_x86_64 --python-version 3.12 \
    --only-binary=:all: --dest /tmp/wheels_linux <packages>
scp /tmp/wheels_linux/*.whl backhouse:C:/flyemu/wheels/
# on the PC, via: ssh backhouse "wsl -d Ubuntu -- bash /mnt/c/flyemu/<script>.sh"
~/flyemu/venv/bin/python -m pip install --no-index --find-links /mnt/c/flyemu/wheels <packages>
```

The PC's SSH login shell is `cmd.exe`, so quoting bash inline is unreliable.
Ship a script and execute it: `ssh backhouse "wsl -d Ubuntu -- bash /mnt/c/flyemu/x.sh"`.

## Reproducing the session-1 results

```bash
# the five conditions and controls, 16 parameter draws each, paper tolerances
./scripts/run_condition_set.sh 16

# one condition on its own
uv run python scripts/pugliese_conditions.py --condition baseline \
    --replicates 8 --rtol 2e-6 --atol 5e-9 --save-traces

# sweep tonic proprioceptive drive
uv run python scripts/pugliese_conditions.py --condition baseline \
    --replicates 8 --sensory-amp 200

# phasic versus tonic sensory drive at matched mean amplitude
uv run python scripts/phasic_sensory.py --sensory-amp 200 --freq 10 --replicates 8

# the corrections found in F10 and F11
uv run python scripts/pugliese_conditions.py --condition baseline --replicates 8 \
    --proprio-cholinergic          # leg afferents excitatory, per published physiology
uv run python scripts/pugliese_conditions.py --condition baseline --replicates 8 \
    --size-norm class              # excitability normalised within cell class

# controls that matter for any drive experiment
uv run python scripts/pugliese_conditions.py --condition baseline --replicates 8 \
    --sensory-amp 5 --drive-target random_interneurons --threshold-matched
uv run python scripts/pugliese_conditions.py --condition baseline --replicates 24 \
    --sample-transmitters          # propagate the EM classifier's own uncertainty

# aggregate everything present and render the figures
uv run python scripts/make_figures.py
uv run python scripts/make_figures2.py
uv run python scripts/summarize_session.py

# the headline claim, checked against every run present
uv run python scripts/rhythm_rate_exclusion.py

# every run record complete: commit, input hashes, environment, scaffolds
uv run python scripts/audit_provenance.py

# which sign flips broke the rhythm, reconstructed from seeds, no re-simulation
uv run python scripts/analyze_sign_flips.py runs/pugliese-baseline-n24-papertol-ntsample
```

Batch scripts, each writing one log under `runs/`:

| Script | Question |
|---|---|
| `run_condition_set.sh` | the five conditions and controls |
| `run_sensory_sweep.sh`, `run_fine_sensory.sh` | how much proprioceptive drive breaks the rhythm |
| `run_drive_control.sh` | does the sensory pathway matter, or just added current |
| `run_threshold_matched.sh` | the same question with drive matched to each cell's threshold |
| `run_glutamate_sweep.sh` | how much rests on glutamate being inhibitory |
| `run_nt_uncertainty.sh` | does the result survive the classifier's own uncertainty |
| `run_corrected_model.sh` | does the model have a working point once F11 is fixed |
| `run_ei_balance.sh` | can stronger inhibition hold a high-rate rhythm |
| `phasic_sensory.py` | does the timing of sensory drive matter |
| `run_corrected_window.sh` | where the corrected model's working point is |
| `run_fully_corrected.sh` | every correction at once, plus sensory drive |

If a run is killed, `metrics_partial.csv` keeps the completed replicates, and
`scripts/recover_from_logs.py <out.csv> <dir> "<glob>" <key>` recovers older
runs from their logs.

Conditions are `baseline`, `silence_i1i2`, `shuffle`, `dna02`, `no_stim`.
Tolerances `--rtol 2e-6 --atol 5e-9` are the published values; `1e-4 / 1e-7`
runs about three times faster and is adequate for smoke tests, not for results.

## Outputs

Each run writes `runs/<run_id>/`:

- `metrics.csv`, one row per parameter draw
- `<run_id>.provenance.json`, with code commits, input file SHA-256 hashes,
  resolved config, environment, wall time, peak memory, and an explicit list of
  **scaffolds**: every imposed stimulus, prescribed input or non-biological
  substitute used in that run
- `R_replicate0.npz` when `--save-traces` is given

`runs/` is not tracked in git. Raw data belongs on the PC's Linux disk, which
has 936 GB free; the Mac has about 56 GB and holds no raw data.

## Timing observed

| Machine | Per simulation, paper tolerances |
|---|---|
| Mac M2 Pro, single process | 17 s |
| PC WSL2, single process | 43 s |
| PC, 10 processes in parallel | 170-230 s each, higher throughput overall |

Runs get much slower as network activity rises, because the adaptive solver
takes smaller steps. High synaptic scales and high sensory drive are expensive.
