# Running the code

Session 2 deleted the isolated-fragment drivers. What remains is infrastructure
that serves any model, plus the data-validation tests.

## Setup

Mac, orchestration and CPU work:

```bash
cd /Users/ben/fly-emulation
uv sync                       # pinned Python 3.12
uv run pytest tests -q        # 7 data-validation checks
```

The neuPrint token lives at `~/.config/flyemu/neuprint_token`, mode 600, outside
the repository. It reaches `manc`, `male-cns`, `hemibrain` and `optic-lobe` for
live queries, which avoids multi-gigabyte downloads. Use `male-cns:v1.0` as the
primary graph; see finding F-DATA-2 for why, and note its annotations use
different field names from the nerve-cord dataset.

PC, `backhouse`, 28 cores under WSL2 Ubuntu. Its internet is blocked at the
router, so its environment was built from wheels shipped over the Tailscale SSH
link:

```bash
# on the Mac
pip download --platform manylinux2014_x86_64 --python-version 3.12 \
    --only-binary=:all: --dest /tmp/wheels_linux <packages>
scp /tmp/wheels_linux/*.whl backhouse:C:/flyemu/wheels/
# on the PC
~/flyemu/venv/bin/python -m pip install --no-index \
    --find-links /mnt/c/flyemu/wheels <packages>
```

Its SSH login shell is `cmd.exe`, so quoting bash inline is unreliable. Ship a
script and execute it:

```bash
ssh backhouse "wsl -d Ubuntu -- bash /mnt/c/flyemu/<script>.sh"
```

Do not run more than two simulation sweeps at once on the laptop. Three
oversubscribes ten cores and slows everything by roughly the factor you added.

## The whole-organism model

```bash
# cache the graph: 176,422 neurons, 25.8M edges, ~26 MB of parquet, ~4 min
uv run python scripts/fetch_male_cns.py

# C0: refuses to integrate and enumerates every unresolved requirement
uv run python scripts/run_organism.py --policy strict --duration-ms 100 --tag c0

# C1: one declared default per subsystem; runs, flails
uv run python scripts/run_organism.py --policy minimal --duration-ms 200 --tag c1

# tier-A sensitivity over the two guesses with the largest reach
uv run python scripts/sweep_defaults.py --duration-ms 50
uv run python scripts/sweep_motor_gain.py --duration-ms 200

# watch it
uv run python scripts/render_organism.py --duration-ms 500 \
    --set 'motor_unit:all|force_per_spike=10'
```

Any assumed scalar can be overridden by its registry key, which is
`entity|property` as it appears in the emitted `inventory.csv`:

```bash
uv run python scripts/run_organism.py --policy minimal \
    --set 'connection_class:all|efficacy_per_synapse=0.4' \
    --set 'cell_type:all|background_noise=2.5'
```

Overrides are recorded as `assumed` with the override noted. They never read
back as measurements.

Cost on the M2 Pro: about 2 s of compute per 50 ms of simulated fly, peak
2.0 GB. `data/cache/` is untracked; `runs/<run_id>/` holds the provenance
record, the trace, the population rates and the inventory the run emitted.

## The body

The default body is **flybody**; `Body(model="neuromechfly")` selects the other
for comparison. First construction downloads ~140 MB of assets once, then takes
about 0.1 s.

```python
from flyemu.body import Body
b = Body()                      # self-collision, adhesion, aero, tendons, vision
b.summary()
```

Measured costs on the M2 Pro: 155 us per step bare, 963 us with self-collision,
11.5 ms per eye readout (rendered at 100 Hz by default).

```bash
# which sign of each actuator produces which anatomical action
uv run python scripts/calibrate_joint_signs.py --model flybody
```

The muscle map reads that calibration to resolve signs, so **re-run it after
any change to the body model or its axis order**, or the muscle signs silently
become wrong.

## Watching a run

Two visualisers, both replaying a pre-recorded run. Neither simulates anything,
so neither can diverge from what was recorded.

```bash
# record once: full-rate qpos plus the neural and motor signals, ~2 min for 3 s
uv run python scripts/record_organism.py --duration-ms 3000 \
    --set 'motor_unit:all|force_per_spike=10' \
    --set 'cell_type:all|background_noise=2.5'

# browser visualiser on localhost: body, motor raster, joint torque, CNS rate
uv run python scripts/export_geometry.py      # once: writes viz/geometry.* (untracked)
uv run python scripts/serve_viz.py              # newest recording, opens a tab
uv run python scripts/serve_viz.py --list
uv run python scripts/serve_viz.py --run runs/organism-record-3000ms-replay

# MuJoCo's own viewer: real geometry, full camera control
uv run python scripts/replay_mujoco.py runs/organism-record-3000ms-replay
#   space play/pause   . faster   , slower   [ ] step   r restart
```

A recording is two files. `recording.npz` holds `qpos` every timestep, which is
all MuJoCo needs to reconstruct every body pose: 133 floats per step, 14.6 MB
for 3 s. `replay_data.js` holds the same run downsampled to 200 Hz, plus the
motor spikes, joint torques and contact forces, for the browser page in `viz/`.
At 2.3 MB it loads as a plain `<script>`, so the page needs no build step and
no fetch.

The browser page shows the coupling rather than just the motion: the motor-
neuron raster is split so the 328 neurons that reach a muscle sit above the 380
that drive nothing, and the joint-torque panel is banded so the 60 degrees of
freedom with no motor neuron mapped to them are visibly empty rather than
looking like a drawing fault.

## What remains

```bash
uv run pytest tests -q                        # validates the source data itself
uv run python scripts/audit_provenance.py     # every run record complete
```

`src/flyemu/provenance.py` is the recorder. Any run that produces a number
should write one: commits for this repo and any pinned upstream, SHA-256 of every
input, resolved config, environment, wall time, peak memory, and an explicit list
of **scaffolds**, meaning every imposed stimulus, prescribed input or
non-biological substitute used. Session 1 wrote 53 of these and the audit script
confirms all are complete.

## What was deleted

The fragment runner, its sweeps, its figures and its bespoke analyses, about 40
files. Recoverable from git history at commit `1f7f5a4` or earlier. See
`docs/PLAN.md` for why.

`external/Pugliese_cpg_2025` is untracked and remains on disk as a precedent to
consult. Its bundled connectivity extracts are what the data-validation tests
read, so the tests skip if it is absent.

## Untracked but retained

`runs/` holds 53 provenance records and their metrics from session 1, about
16 MB. They are the evidence behind every number in `docs/FINDINGS.md`, so they
stay on disk even though the code that produced them is gone.
