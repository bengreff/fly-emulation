# Handoff

Written at the end of session 3, 16 September 2026. **Updated in session 4
(24 September): the next work is now `docs/PLAN_NEXT.md`**, which reorders the
"immediate next task" below: reproduce published pathway results with noise
off before differentiating biophysics. Session 4 also committed session 3's
work, excluded 9,311 untyped fragments from the graph (F-COUNT-2: 167,111
neurons now), and mapped the non-leg motor neurons (`docs/MOTOR_TARGETS.md`).
Then it ran the pathway battery: F-GAIN-2 (the anatomy is load-bearing but
ignites), F-SFA-1 (uniform adaptation fails), F-SENS-1 (profile `m1`, fresh
held-out 2/5). The current open list is at the top of PLAN_NEXT session 5.
Later that evening: an independent review found and fixed a control bug; F-TYPE-1
shows results are type-level; three uniform mechanisms were rejected by
pre-registration. backhouse is deployed: `~/fly-emulation` (code synced by
`scripts/sync_backhouse.sh`), flybench in `external/flybench/.venv`, and jobs run
in tmux under a keep-alive SSH session (WSL shuts down otherwise).
**Session 5 (25 Sept):** blank ledger (F-LEDGER-1, ~250k blank slots at declared
grain, `scripts/blank_ledger.py`), sensory census (F-CENSUS-1, all 17,896 sensory
neurons classified), derived retinotopy (F-VISION-2), olfaction/CO2/humidity wired
to `world.py` (F-OLF-1). 66% of sensory neurons driven. Every inventory value has a
`basis` label: measured / derived / inferred / unknown.
**Session 5, later:** strict evidence labels (measured / derived / inferred /
guessed / unknown / absent; `Registry.validate()` tested), complete ontology of
measurable fly biology (`data/ontology/fly_information.yaml`, F-LEDGER-2/3),
model family M2 with per-type table `data/params/cell_types.csv`, graded
transmission, neuromodulator pools, Q10, every sensory neuron transduced
(F-SENSE-ALL), 756/815 motor neurons mapped (`data/params/motor_targets.csv`,
F-MOTOR-2). Filling a blank = adding a labelled row to a params table.
**Current working model: profile `m2` (F-AL-1)**, 0.165 mV per synapse, calibration
rule v2 satisfied. flybench also runs locally (`external/flybench/.venv`).
backhouse dropped off the network again at ~22:30 on 24 Sept; the m2 jobs that
were running there are lost, and were redone on the Mac.

## What this project is

A biologically constrained *Drosophila* brain-body simulation. The structure is
a real connectome, the body is a real scanned fly in MuJoCo, and the physiology
is guessed - but every guess is recorded, counted, and reported as a guess.

Three nested goals, in dependency order:

1. **The instrument.** A whole organism that runs with every guess recorded.
   Essentially built.
2. **The science.** Which properties of a working fly are forced by the
   measurements, which depend on assumptions, and which stay interchangeable
   even after validation. This is the near-term output.
3. **The aspiration.** An organism that lives a fly-like life: walking, then
   flight, then internal state and learning.

## Where it stands

**Runs end to end.** 176,422 neurons, 25,862,574 edges, 125,024,863 synapses
from `male-cns:v1.0`, driving a flybody MuJoCo fly at a 0.1 ms timestep. It
falls over and thrashes. That is the expected result.

**The body is good.** 0.985 mg from 52 weighed flies, 103 joints all with
ranges, 98 torque actuators on real articulations only, self-collision, tarsal
adhesion, 8 tendons, quasi-steady aerodynamics. 963 us per step.

**The physiology is one guess repeated.** 19 distinct unresolved inferences fill
27.5 million model elements. Every neuron in the brain shares one membrane time
constant, one threshold, one synaptic strength.

**The interface is a third wired.** 434 of 708 motor neurons drive something;
3,033 neurons in the graph still have no channel at all. Of 42 brain-body
channels, 35 are absent.

## The gate: read F-GAIN-1 before planning anything

A 16x change in every synapse in the animal moves the mean firing rate less
than 4x. A 2.5x change in the background noise term moves it 400x.

**The connectome is not yet doing the work.** The term standing in for
everything the model omits is. Two consequences:

- Nothing downstream is evidence until this changes.
- An optimiser pointed at behaviour today would tune the noise term, which has
  no biological referent, and produce a walking fly that had learned nothing
  about flies.

So the target is not walking. The target is **making the anatomy load-bearing**,
and walking is what should fall out if it is.

## The immediate next task

**Differentiate the neural biophysics by cell type**, then re-run the
efficacy-versus-noise sweep and see whether the ratio flips.

`src/flyemu/lif.py` currently assigns one `tau_m`, `v_rest`, `v_th`, `v_reset`,
`t_ref` and `tau_s` to all 176,422 neurons, through `default_params`. The graph
carries 11,751 distinct `type` labels. Differentiating them tests the two
competing explanations for F-GAIN-1:

- the per-synapse efficacy default is far too small for the anatomy to matter, or
- uniform biophysics suppresses recurrent gain regardless of efficacy.

```bash
uv run python scripts/sweep_defaults.py --duration-ms 50
```

Either answer is worth having. If the connectome still does not matter with
per-type biophysics, that is a result about the model family and a reason to
change M - toward conductance-based synapses, or graded transmission, which we
already know is outright wrong for the optic lobe.

After that, in order: find the smallest published result this model could
*predict* rather than merely produce; finish the interface; then behaviour
validated against measured kinematics; then Tier 2 learning, which needs
neuromodulation and plasticity, both entirely absent.

## Read in this order

1. `CLAUDE.md` - working instructions, including the agent limit.
2. This file.
3. `docs/MODEL_M.md` - the declared model family and what it omits.
4. `docs/FINDINGS.md` - **newest at the bottom**; sessions 1, 2 and 3 in order.
   The session-3 sections are the current state.
5. `docs/INTERFACE.md` - the brain-body channel inventory and its gaps.
6. `docs/DECISIONS.md` - newest last.
7. `docs/PLAN.md` - **partly superseded**. Its steps 0, 5a, 5b and 6 were done;
   steps 1 to 4 were replaced by emitting the inventory from the running model.

## Things that will bite you

- **Re-run `scripts/calibrate_joint_signs.py` after any change to the body model
  or its axis order.** Muscle signs are resolved against that measured table.
  `FTi pitch +` flexes the leg in NeuroMechFly and extends it in flybody; a
  hard-coded sign inverts silently across a body swap (F-AXIS-1).
- **MuJoCo prunes collisions at the body level** before it reaches geoms.
  Setting `geom_contype` alone does nothing (F-COLLIDE-1).
- **Checking a value's distribution, not its mean**, has reversed two confident
  conclusions in this project. See the session-1 methodological lessons.
- **Unknown must never become measured absence.** Gut stretch receptors and
  oxygen sensing are unknown *in the animal*; the wing motor system is merely
  unimplemented here. A test enforces the distinction.
- `runs/` and `data/cache/` are untracked and hold the evidence. Do not delete.
- **backhouse (the GPU box) was unreachable all of session 3.** Everything ran
  on the Mac. Check `ssh backhouse` before planning GPU work.
- A research task is still outstanding: **the non-leg motor neuron targets**
  (neck, haltere, abdominal, proboscis, wing steering), which is what would let
  ~400 currently idle motor neurons drive something. An agent attempting it
  stalled and returned nothing.

## Agent discipline, which is a hard rule

At most **three subagents at a time, counted recursively**, and never an agent
type that can spawn its own. `general-purpose` inherits the Agent tool: four of
them fanned out to 22 live agents in three minutes in this session. Use
`Explore`, which cannot spawn. Verify with `ListAgents` after dispatching.

## Commands

```bash
uv run pytest tests -q                      # 27 tests

uv run python scripts/fetch_male_cns.py     # cache the graph, ~4 min, once
uv run python scripts/run_organism.py --policy strict  --duration-ms 100  # C0
uv run python scripts/run_organism.py --policy minimal --duration-ms 200  # C1

uv run python scripts/sweep_defaults.py --duration-ms 50
uv run python scripts/calibrate_joint_signs.py --model flybody

uv run python scripts/record_organism.py --duration-ms 3000 \
    --set 'motor_unit:all|force_per_spike=10'
uv run python scripts/serve_viz.py          # browser replay on localhost
uv run python scripts/replay_mujoco.py runs/organism-record-3000ms-replay
```

Any assumed scalar can be overridden by its registry key, which is
`entity|property` as it appears in the emitted `inventory.csv`. Overrides are
recorded as `assumed` with the override noted; they never read back as
measurements.
