# Running

Every command here runs the **working model** (profile m9v since session 12; edges ≥ 5 synapses; `docs/MODEL.md`) unless it says otherwise. The regression reference is `FLYEMU_PROFILE=m4`. The procedure around these commands (pre-registration, splits, hygiene) is in `docs/WORKFLOW.md`.

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

| Check | Command | Reference (session 10, backhouse) |
|---|---|---|
| Sugar → MN9_L (m4) | `FLYEMU_PROFILE=m4 uv run python scripts/assay_pathways.py --assay sugar_mn9 --rates 100 --shuffles 0 --trials 10` | 8.9 ± 5.9 Hz (> 5 required) |
| Stability (m4) | `FLYEMU_PROFILE=m4 uv run python scripts/probes/closed_loop_check.py --seed N`, N = 0, 1, 2 | 0 non-tonic spikes after silencing; brain excl. ORNs 0.35/0.22/0.30 Hz |
| Stability (m6; m7 working: seeds 9-11 silent, 0.113-0.126 Hz) | `uv run python scripts/probes/closed_loop_check.py --seed N`, N = 0-11 | 0 spikes after silencing on 12/12 seeds; brain excl. ORNs ~0.09-0.15 Hz |
| Sugar → MN9_L (m6 7.3 Hz; m7 6.9 ± 2.3 Hz) | `uv run python scripts/assay_pathways.py --assay sugar_mn9 --rates 100 --shuffles 0 --trials 10` | 7.3 Hz |
| Tests | `uv run pytest tests -q` | all pass (~8 min) |

Before session 10 the default profile was m4; `closed_loop_check.py --template` adds the template switches to whatever profile runs.

## GPU (backhouse, session 10)

```bash
# brain-only, many parameter sets at once (exactly the CPU assay's inputs)
~/fly-emulation/.venv-gpu/bin/python scripts/gpu_assay.py cands.json --assay sugar_mn9 --trials 10
# closed loop: B organisms, brain on the GPU, bodies in worker processes; exchange every k steps
~/fly-emulation/.venv-gpu/bin/python scripts/gpu_closed_loop.py members.json --k 1 --workers 12
~/fly-emulation/.venv-gpu/bin/python scripts/gpu_bench.py equiv --ms 500 --stim broad
```

- `.venv-gpu` has JAX + CUDA 12 and sees the main venv through `zz_main_venv.pth` (same numpy 2.5.3).
- k > 1 holds the sensory drive for k steps: an approximation that changes the dynamics (F-STAB-5); k = 1 is exact.
- The GPU is shared with another process (~2 GB, ~50% use); XLA prints out-of-memory retries when it preallocates, then continues.

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
- Rendering (contact sheets): EGL fails under WSL and the system has no OSMesa. A user-local copy needs no root: `apt-get download libosmesa6`, `dpkg -x` it into `~/osmesa/root`, add a `libOSMesa.so` symlink beside `libOSMesa.so.8`, then run with `LD_LIBRARY_PATH=$HOME/osmesa/root/usr/lib/x86_64-linux-gnu MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa` (session 12; example in `runs/s12/nonleg/run_sheet.sh` on backhouse).
- Inside `tmux new-session "..."`, quote override values (`--set 'motor_unit:all|force_per_spike=10'`), or the `|` becomes a shell pipe; a small runner script is safest.

## Outputs

Each run writes `runs/<run_id>/<run_id>.provenance.json`: environment, git state, inputs and results. Most runs also write `inventory.csv`, every requirement with its label and evidence. `runs/` is not in git. `scripts/audit_provenance.py` summarises the records.
