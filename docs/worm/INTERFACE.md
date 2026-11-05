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
- Internal brain step: 0.1 ms for membranes and synapses (fixed; the exchange interval must be a multiple);
  slow layers (peptides, monoamines, intestine, slow signalling) step every 10 ms inside the brain.
- Neural-only runs use `default_observation()`: a straight, untouched worm on a standard plate.
- Determinism: same `seed` and toggles and the same observation stream give the same output (float64 on CPU).

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
| `gcamp_dff` | N neurons | dF/F | GCaMP observation model output when its toggle is on, else None |

Posterior body contraction in the defecation cycle (pBoc) arrives through `muscle_activation` (the intestine's
proton signal acts on posterior body-wall muscles inside the brain package), not as a separate channel.

**Muscle positions.** `interface.muscle_position(name)` gives the muscle centre as arclength s (0 nose, 1 tail):
muscle k of 24 tiles s = 0.05-0.95 evenly (**guessed**). If the body has Virtual Worm or Sibernetic muscle
geometry, use that and tell me here so the brain's proprioceptive map uses the same positions.

**Activation dynamics (so the body does not double them).** Activation a = Hill(Ca) with its own rise/decay time
constants, both ledger parameters (`bwm_ca_half`, `bwm_hill_n`, `bwm_tau_act_on`, `bwm_tau_act_off`). Force
rise time in the body should come only from the body's own mechanics.

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
- Brain cost per biological second at the template configuration: measured and recorded in HANDOFF when the
  neural-only run lands (target: far inside Ben's 100x-slower-than-real-time cap for the full model).

## Files the viewer can read (brain side)

- `docs/worm/ledger.json`: every mechanism, every parameter row (value used, bounds, prior, label, source,
  precision needed), slot counts per grain, toggles and their neutral settings. Regenerate:
  `uv run python scripts/worm/export_ledger.py`.
- `data/worm/structure/`: cells, chemical and gap-junction edges (Cook 2019), CeNGEN expression subset; the
  wiring diagram for the viewer comes from `chem_edges.csv` and `gap_edges.csv`.
- Neural run traces: `data/worm/brain_runs/<run>/trace.npz` (t, v, ca, muscle activation, cell names).

## Open between workers

(Write questions here with a date and your side. Answered items move to a "Settled" list.)

- [brain, 5 Nov] Body: what K (midline samples) and which muscle geometry will you use? If not the guessed
  s = 0.05-0.95 tiling, give me `muscle_position` values and I will switch the brain's map to them.
- [brain, 5 Nov] Body: do you want the brain to accept `muscle_strain` from you, or derive it from curvature
  (strain = -/+ r kappa on the dorsal/ventral side, r = local body radius)? I default to deriving it.
