# Worm brain <-> body interface (file contract between the two workers)

Version 1, written 2026-11-05 by the brain worker (main checkout). Code form: `src/wormemu/interface.py`
(dataclasses, canonical name orders, units). The brain worker owns the brain side and the sensory channel list;
the body worker (worktree `wormbody`) owns the body side. Change requests go in "Open between workers" at the
bottom; the Director relays.

## How the loop runs

- **Lockstep, body drives the clock.** Every exchange interval (default **1.0 ms** of biological time; the body
  may use 0.5-5 ms, stated in its run header) the body calls

  ```python
  from wormemu.brain import sample_worm, Brain
  from wormemu.interface import BodyToBrain, BrainToBody, BWM_NAMES, default_observation
  spec = sample_worm(seed=0)              # complete worm: every mechanism, every number from the ledger
  brain = Brain(spec)                     # optional: Brain(spec, toggles={...}) to flip a toggle
  out = brain.reset()                     # BrainToBody at t = 0 (muscles at rest)
  while running:
      out = brain.step(obs, dt_ms=1.0)    # obs: BodyToBrain at the start of the interval
  ```

- The brain holds `obs` constant over the interval (zero-order hold) and returns the command at the end of it.
  Every biological delay (synaptic, neuromuscular, muscle Ca rise and decay) is inside the brain. **The body
  adds no delay or filtering of its own** to `muscle_activation`.
- Internal brain step: **0.5 ms** (BAAIWorm's fixed NEURON step), so `dt_ms` must be a multiple of 0.5 and the
  default 1 ms exchange is 2 internal steps. The lumped layers (senses, muscle Ca and activation, peptides,
  monoamines, organs, GCaMP) step once per exchange interval.
- `brain.cell_names`: the 302 neurons (Cook 2019 order) then the 95 body-wall muscles (`BWM_NAMES` order). `v_mV`,
  `ca_uM` and `gcamp_dff` follow this order.
- Build one `Brain` per process (NEURON is a single simulator per process).
- Neural-only runs use `default_observation()`: a straight, untouched worm on a standard plate.
- Determinism: same `seed` and toggles and the same observation stream give the same output (float64 on CPU;
  `reset()` reproduces the membrane run exactly, checked in tests/test_worm_brain.py; the GCaMP noise and the
  egg-laying clock keep drawing from the worm's random stream across resets).

## Brain -> body (`BrainToBody`)

| field | shape | unit | meaning |
|---|---|---|---|
| `muscle_activation` | 95 | 0..1 | body-wall muscle activation in `BWM_NAMES` order (dBWML1-24, dBWMR1-24, vBWML1-23, vBWMR1-24; Cook 2019 names; vBWML24 does not exist). Fraction of maximal isometric active force at optimal length. The brain owns membrane -> Ca -> activation; **the body owns activation -> force** (force-length, force-velocity, passive tissue, max force) |
| `pharynx_activation` | 20 | 0..1 | pharyngeal muscles pm1, pm2D/VL/VR ... pm7D/VL/VR, pm8 (optional for the body: pumping visuals, food intake) |
| `enteric_activation` | 4 | 0..1 | mu_intL, mu_intR, mu_anal, mu_sph (defecation aBoc/expulsion; optional) |
| `sex_muscle_activation` | 16 | 0..1 | vm1/vm2/um1/um2 x A/P x L/R (egg-laying; optional) |
| `eggs_laid`, `expulsions`, `pumps` | int | count | events completed in this interval |
| `pressure_scale` | float | 1 = baseline | pseudocoelomic pressure; stays 1 unless the osmotic toggle is on |
| `v_mV`, `ca_uM` | N cells | mV, uM | every cell's soma voltage and Ca, in `brain.cell_names` order, for the viewer (decimate as you like) |
| `gcamp_dff` | N cells | dF/F | GCaMP observation model output when its toggle is on, else None (use the neuron entries) |

Posterior body contraction in the defecation cycle (pBoc) arrives through `muscle_activation` (the intestine's
proton signal acts on posterior body-wall muscles inside the brain package), not as a separate channel.

**Muscle positions.** `interface.muscle_position(name)` gives the muscle centre as arclength s (0 nose, 1 tail):
muscle k of 24 tiles s = 0.05-0.95 evenly (**guessed**). If the body has Virtual Worm or Sibernetic muscle
geometry, use that and tell me here so the brain's proprioceptive map uses the same positions.

**Activation dynamics (so the body does not double them).** Activation a = Hill(Ca) with its own rise/decay time
constants, all ledger parameters (`mca_vhalf_mV`, `mca_k_mV`, `mca_max_uM` for V -> Ca; `mact_hill`,
`mact_khalf_uM`, `mact_tau_rise_ms`, `mact_tau_decay_ms` for Ca -> activation; all guessed). Force rise time in the
body should come only from the body's own mechanics.

**Muscle names (verified 5 Nov).** BAAIWorm builds 96 muscle cells `MC[D|V][L|R]01-24`; the worm has 95 (Cook 2019:
no vBWML24). The brain maps `MCDL01` -> `dBWML1` and so on (`brain_structure.bwm_name`) and drops `MCVL24`. Under
this map 337 of BAAIWorm's 552 neuron-to-muscle pairs are Cook 2019 edges, against 309 with the index shifted by -1,
278 by +1 and 26 with dorsal and ventral swapped (measured), so the direct map is the right one.

## Body -> brain (`BodyToBrain`)

| field | shape | unit | meaning |
|---|---|---|---|
| `t_ms` | float | ms | time at the start of the interval |
| `s` | K | 0..1 | arclength of the midline samples, nose -> tail; K chosen by the body (>= 25; 49 is fine) |
| `curvature_per_mm` | K | 1/mm | signed midline curvature; **positive = dorsal side concave** (dorsal muscles shorter) |
| `curvature_rate_per_mm_ms` | K | 1/(mm ms) | its time derivative (for rate-sensitive stretch receptors) |
| `contact_force_uN` | K | uN, >= 0 | normal force from objects (probe, eyelash, obstacle, other worm) at each sample; **not** the substrate load |
| `nose_force_uN` | float | uN | axial force on the nose tip (nose touch) |
| `muscle_strain` | 95 or None | L/L0 - 1 | per-muscle fibre strain, BWM order; None = the brain derives it from curvature and its own radius |
| `head` | dict | see below | stimulus values at the nose (amphid, labial, cephalic endings) |
| `tail` | dict | see below | stimulus values at the tail (phasmids) |
| `tap` | float | 0..1 | plate tap (vibration) this interval; 0 = none |

`head` keys (defaults = a standard NGM plate at 20 C with no gradient; missing keys take the default; unknown keys
are ignored and reported once): `nacl_mM` 50, `diacetyl_uM` 0, `isoamyl_alcohol_uM` 0, `benzaldehyde_uM` 0,
`butanone_uM` 0, `nonanone_uM` 0, `octanol_uM` 0, `glycerol_mM` 0, `copper_mM` 0, `quinine_mM` 0,
`temperature_C` 20, `o2_pct` 21, `co2_pct` 0.04, `light_mW_mm2` 0, `food_OD` 0. `tail` keys: `sds_mM` 0,
`nacl_mM` 50.

The world reaches the brain only through these fields and the brain's own sensory models (standing rule: no
unobserved world state bypasses the senses). If the body needs a new stimulus type, ask here; the brain adds a
channel and its transducer.

## Rates and cost

- Exchange 1 kHz (1 ms) by default. The body's internal step is its own business.
- Brain cost: **7.06 s of wall per biological second** for the whole network (302 neurons, 96 muscles, 48,202
  segments, one thread, 888 MB; port302a, measured on backhouse). brain.py numbers per run are in
  `docs/worm/BRAIN_PORT.md` section 3. Ben's cap is 100x slower than real time; this is 7x.

## Toggles (brain side)

`Brain(spec, toggles={...})`; defaults from `data/worm/model/mechanisms.yaml`. Uncertain mechanisms are off until
adopted (gate, battery run, viewed figure).

| toggle | default | values |
|---|---|---|
| `literature_overrides` | on | off = BAAIWorm as published (the port302a reference) |
| `wiring` | cook | `cook` = every Cook 2019 pair at per-EM strengths (adopted 5 Nov, port302c); `baaiworm` = BAAIWorm's construction as published |
| `sign_rule` | transmitter | `allexc` = BAAIWorm's all-excitatory rule |
| `receptor_sign` | off | on = sign per pair from CeNGEN receptor expression (guessed rule; flips 1125 of 3709 pairs) |
| `bwm_coupling` | off | on = Cook's 96 muscle-muscle gap pairs at 5 nS each (guessed) |
| `expression_map` | off | on = CeNGEN gates channel presence |
| `muscle_active` | off | on raises NotImplementedError (c302 muscle channels not in the NEURON build yet) |
| `gap_rectification` | off | on raises NotImplementedError (not wired yet) |
| layers | see the ledger | `sens_*`, `muscle_ca`, `muscle_activation`, `pharynx`, `defecation`, `egg_laying`, `gcamp` on; `peptides`, `monoamines`, `glia`, `metabolism`, `homeostasis`, `slow_signalling` off |

## Files the viewer can read (brain side)

- `docs/worm/ledger.json`: every mechanism, every parameter row (value used, bounds, prior, label, source,
  precision needed), slot counts per grain, toggles and their neutral settings, and the source project x fill kind
  table. Regenerate: `PYTHONPATH=src uv run python scripts/worm/build_ledger.py`.
- `data/worm/structure/`: cells, chemical and gap-junction edges (Cook 2019), CeNGEN expression subset; the
  wiring diagram for the viewer comes from `chem_edges.csv` and `gap_edges.csv`.
- Neural run traces: `data/worm/brain_runs/<run>/run.npz` (V and Ca, cells x 1 ms samples, cell names; not in
  git, kept on backhouse under `~/worm-port/runs/`), `summary.json` and figures beside it (in git).

## Body side (body worker, 2026-11-05)

The body is the ported MetaWorm body (BAAIWorm b99ca5ab, Apache 2.0; `third_party/metaworm`, driven by
`src/wormemu/body/metaworm.py`). Its numbers and their labels: `data/worm/ledger/metaworm_parameters.csv`.

- **Exchange: every published physics step, 1/240 s = 4.167 ms** (implemented, `src/wormemu/body/loop.py`).
  The brain's 0.5 ms step does not divide 4.167 ms, so the body asks the brain to advance to the 0.5 ms grid
  point nearest its own time: `dt_ms` = 4.0, 4.5, 4.0, repeating (12.5 ms per 3 exchanges); the two clocks never
  differ by more than 0.25 ms (derived). No published constant changes; dt = 1/250 s is no longer needed.
- **Order in an exchange.** Body and brain run at the same time in separate processes: the body steps with the
  command from the end of the previous interval while the brain steps with the observation from the start of
  this one. A command therefore reaches the muscles one exchange (4.17 ms) after the brain computes it. That is
  the loop's lag, not a filter; the body adds nothing else.
- **First closed loop (5 Nov, measured, Mac).** brain.py `sample_worm(0)`, default toggles, with the body and the
  chemotaxis cone field: 3 s of biological time in 10.7 s of wall (3.6x slower than real time; brain and body in
  parallel), finite throughout. The brain's largest muscle activation was 4.4e-6, so the body did not move; 142 of
  302 neurons ended above -20 mV. Run `runs/worm/metaworm/cl_brain_s0`, in the viewer and as an MP4.
- **Weak drive and the published solver.** MetaWorm's solver stops when one iterate changes by less than an
  absolute threshold (5e-7 per coordinate on average) and returns the iterate from before that last solve. For a
  body at rest under a weak load, that is the inertial prediction, so the muscles are ignored: a prescribed wave
  of amplitude 0.03 moves nothing (displacement exactly 0), 0.06 moves it (measured). Toggle `body.solver_exit`,
  neutral `published`; `latest` returns the converged solve instead (amplitude 0.01 then moves 0.0099; the
  published gait P2 keeps 1.5 Hz, its wavelength moves 1.4%, head amplitude 3.7% and speed 5%; measured). Until it
  is adopted, brain drive below about 0.05 does not move the body.
- **Activation -> force.** `muscle_activation` goes into MetaWorm's muscle input 1:1 (the published input range is
  [0, 1] after its key gain and clip; the mapping is **inferred**, not measured). The body updates it every
  physics step and adds no filter. No force-length or force-velocity in the published body (toggle
  `muscle.force_model`, neutral = the published linear muscle).
- **95 -> 96 muscles.** MetaWorm has 4 strings x 24 segments, head first. Segment j of MDR / MVR / MDL / MVL is
  Cook muscle j+1 of dBWMR / vBWMR / dBWML / vBWML. MetaWorm's MVL segment 23 has no Cook muscle (vBWML24 does not
  exist); it copies vBWML23 (**guessed**; the alternative is 0, a toggle if it matters).
- **Muscle positions** (answer to the brain's question): use these instead of the guessed 0.05-0.95 tiling.
  Centre of each MetaWorm fibre segment as arclength s, **derived** from the published mesh
  (`viewer/worm/data/body_mesh.json`, `segments[].s_mid`), index 1-24 from the head:
  - dBWMR: 0.033 0.078 0.118 0.152 0.189 0.234 0.276 0.314 0.351 0.381 0.417 0.462 0.501 0.534 0.572 0.623
    0.676 0.717 0.759 0.804 0.846 0.881 0.912 0.954
  - vBWMR: 0.034 0.080 0.119 0.150 0.188 0.228 0.262 0.298 0.344 0.395 0.437 0.477 0.519 0.556 0.607 0.663
    0.709 0.749 0.783 0.817 0.853 0.886 0.914 0.953
  - dBWML: 0.035 0.074 0.113 0.148 0.183 0.222 0.263 0.310 0.359 0.406 0.448 0.493 0.533 0.566 0.619 0.674
    0.718 0.753 0.778 0.809 0.845 0.878 0.907 0.949
  - vBWML (1-23): 0.038 0.073 0.100 0.142 0.188 0.224 0.272 0.322 0.365 0.413 0.449 0.473 0.500 0.531 0.570
    0.618 0.656 0.696 0.742 0.786 0.826 0.865 0.910
- **Midline: K = 49**, s evenly spaced 0..1. Curvature is computed from 24 material slices of the body (slice
  centroids, so the samples follow the same tissue over time) and interpolated to the 49 samples. It is the
  signed dorsal-ventral curvature in the body's own plane, positive = dorsal concave. Why 24 and not 48: the
  readout's static noise at rest is kappa*L RMS 1.9 at 24 slices but 7.4 at 48 (measured, BODY_TESTS.md), and a
  swimming worm's head kappa*L is about 4.5. **Units:** the published body is 0.628 sim units long; the body
  reports curvature_per_mm = (kappa x L) / L_mm with L_mm = 1.0 mm (the ledger's worm length, measured range
  0.9-1.2 mm).
- `curvature_rate_per_mm_ms`: backward difference over one exchange interval.
- `contact_force_uN`, `nose_force_uN`, `tap`: 0 (the published world has no objects, no substrate and no
  contact; MB6 in the body ledger).
- `head` / `tail`: the default plate (`HEAD_CHANNELS`, `TAIL_CHANNELS`) with the chemotaxis scene on top
  (`src/wormemu/body/scene.py`, MB11, toggle `env.chemical_field`, neutral `none`). With a field on, the body
  samples it at the nose (vertex 102) and, for `nacl_mM` / `sds_mM`, at the tail tip (vertex 173). Default
  channel `diacetyl_uM`; numbers and sources in `docs/worm/research/CHEMOTAXIS_PLATE.md`. BAAIWorm's own transducer
  (normalised change of minus the distance, one current into 15 sensory neurons) is described there; it is a
  brain mechanism, so it is the brain worker's to port as a toggle if wanted.
- `muscle_strain`: None in v1 (the brain derives it, as it defaults to). The body can report fibre strain from
  its muscle segment lengths later; it would come in as a toggle.
- `pharynx`, `enteric`, `sex` activations: accepted and ignored (the body has none of those parts yet, MB12).

## Open between workers

(Write questions here with a date and your side. Answered items move to a "Settled" list.)

- [body, 5 Nov 17:10] Brain: the body exchanges every 4.167 ms with `dt_ms` 4.0, 4.5, 4.0 (Body side). Your
  lumped layers step once per exchange; is a 4-4.5 ms step fine for them (muscle Ca and activation time
  constants, GCaMP)? If you need 1 ms, say so: the body would hold the command and send the same observation
  for four brain steps of 1.0, 1.0, 1.0, 1.0-1.5 ms, at about 4x the Python call overhead.

### Settled

- [brain, 5 Nov] K and muscle geometry: K = 49; muscle positions listed under Body side (from the MetaWorm
  mesh). [body, 5 Nov]
- [brain, 5 Nov] `muscle_strain`: the brain derives it in v1; the body may supply it later as a toggle.
  [body, 5 Nov]
