# Running

Every command here runs the **working model** (profile m2, edges ≥ 5 synapses; `docs/MODEL.md`) unless it says otherwise. The procedure around these commands (pre-registration, splits, hygiene) is in `docs/WORKFLOW.md`.

## Setup (Mac)

```bash
uv sync                                     # Python 3.12, pinned by uv.lock
uv run python scripts/fetch_male_cns.py     # neuPrint cache into data/cache/ (once; needs ~/.config/flyemu/neuprint_token)
uv run pytest tests -q                      # ~2 min
```

## Run the organism

```bash
uv run python scripts/run_organism.py --duration-ms 200 --set 'motor_unit:all|force_per_spike=10'
uv run python scripts/record_organism.py --duration-ms 3000 --set 'motor_unit:all|force_per_spike=10' --tag mytag
uv run python scripts/serve_viz.py --run runs/organism-record-3000ms-mytag   # browser replay; stop it when done
uv run python scripts/replay_mujoco.py runs/organism-record-3000ms-mytag
```

- `--profile none --min-synapses 1` gives the session-3 baseline.
- `--policy strict` refuses to run while any requirement is unresolved (C0).
- About 50 s of wall time per simulated second on the M2 Pro.

**Overrides.** Any registry value can be changed with `--set 'entity|property=value'`, using the key as it appears in the run's `inventory.csv`. An override is recorded as guessed, with a note; it never reads back as a measurement.

## Regression checks (report every session)

| Check | Command | Reference (session 6c) |
|---|---|---|
| Sugar → MN9_L | `uv run python scripts/assay_pathways.py --assay sugar_mn9 --rates 100,200 --shuffles 0` | 26.5 / 88 Hz |
| Stability | `uv run python scripts/probes/closed_loop_check.py --seed N` for N = 0, 1, 2 | 0 non-tonic spikes after silencing; brain 0.3–0.4 Hz |
| Tests | `uv run pytest tests -q` | all pass |

## Assays and scoring

```bash
uv run python scripts/assay_pathways.py --assay <name>         # open-loop pathway battery; --help lists assays
uv run python scripts/calibrate_gain.py --generic 4 --scales 0.8,1.0,1.2   # calibration rule v2
uv run python scripts/score_reflex.py --cell <cell> --tag <candidate>      # reflex vs a recorded slow MN
```

- `score_reflex.py` is **the** reflex scorer. It runs `scripts/probes/azevedo_reflex.py` for the standard conditions and saves the model's output **before** extracting the cell. Only this script may open a sealed cell (`docs/WORKFLOW.md` §4.2).
- Probes (standing, stability, VNC and AL diagnostics) are listed in `scripts/probes/README.md`. Each takes `--help`.

## Rebuilding data tables

| Table | Command |
|---|---|
| `data/params/conduction_delays.csv` | `scripts/skeleton_lengths.py` (neuPrint, ~5 min, resumable), then `scripts/conduction_delays.py` |
| `data/params/motor_forces.csv` | `scripts/motor_forces.py` |
| `data/params/orn_rates.csv` | `scripts/orn_rates.py` (needs `data/raw/door/units/`) |
| `data/params/proprio_assignment.csv` directions | `scripts/proprio_direction.py` |
| `data/derived/azevedo2020_slow_mn_<cell>.*` | `scripts/azevedo_slow_mn.py --cell <cell> [--intrinsic-only]` |
| `data/derived/agrawal2020_*.csv` | `scripts/agrawal_vnc_ins.py [--tuning]` |
| `data/derived/joint_signs_flybody.csv` | `scripts/calibrate_joint_signs.py --out data/derived/joint_signs_flybody.csv`. Re-run after **any** body change |
| `data/derived/blank_ledger.csv` | `scripts/blank_ledger.py` |
| `data/derived/sensory_census.csv` | `scripts/sensory_census.py` |

Large Zenodo archives: `uv run python scripts/fetch/zenodo_zip_members.py --list`, then fetch named members.

## backhouse (optional GPU / extra CPU)

The Windows 11 PC runs WSL2 Ubuntu; see `docs/ENVIRONMENT.md` for the hardware. The Mac is sufficient for current work.

```bash
ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'          # reachable?
scripts/sync_backhouse.sh                                              # push code (not data) to ~/fly-emulation
ssh backhouse 'wsl -d Ubuntu -- bash -c "exec sleep infinity"' &      # keep WSL alive while jobs run
ssh backhouse 'wsl -d Ubuntu -- bash -s' < job.sh                      # run scripts via stdin (cmd.exe breaks nested quotes)
```

- Jobs run inside `tmux` on WSL. Copy the `data/cache/` files a job needs; the neuPrint fetch from backhouse is slow.
- Kill the keep-alive `ssh` when finished.
- flybench has its own venv at `external/flybench/.venv` (on both machines).
- Never touch `/home/greff` outside `~/fly-emulation`.

## Outputs

Each run writes `runs/<run_id>/<run_id>.provenance.json`: environment, git state, inputs and results. Most runs also write `inventory.csv`, every requirement with its label and evidence. `runs/` is not in git. `scripts/audit_provenance.py` summarises the records.
