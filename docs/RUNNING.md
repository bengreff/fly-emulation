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

# aggregate everything present and render the figures
uv run python scripts/make_figures.py
```

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
