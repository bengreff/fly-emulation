# Plan: whole-organism field inventory first

Written at the end of session 2, for session 3 to execute. Supersedes the
milestone sequence in `docs/ROADMAP.md`, which built upward from an isolated leg.

## Why the approach changed

Session 1 took one subsystem, the front-leg premotor network of the nerve cord,
and tested it in isolation. It could not simultaneously produce a rhythm and
motor output strong enough to move a leg, across 333 simulations.

That result was reported as a property of the modelling approach. It is not. The
fragment was deafferented and open-loop, so the things that normally set a
premotor circuit's operating point were all absent: descending drive from the
central complex, visual and mechanosensory context, and neuromodulator state.
Asking it to produce both a rhythm and usable force was asking a part to do the
whole animal's job.

The analogy that settles it: you cannot isolate the part of a brain that walks
forward. Walking is under voluntary control and continuously corrected by
systems that are not the walking circuit. A fly is simpler, not different in
kind. Its leg circuits are gated by descending neurons, tuned by octopamine
during flight and walking, and steered by the central complex. A leg loop with
those removed is not a small version of the animal; it is a different system.

So the order inverts. **Enumerate the whole organism's parameter space first.**
Find out how much of a fly we actually have. Only then decide what to simulate,
because the inventory tells you which questions are answerable at all.

## Scope, as decided

| Decision | Choice |
|---|---|
| Grain, physiology | per cell type, with within-type variation as a distribution |
| Grain, structure | per neuron, because that is what the connectome gives |
| Boundary | core loop, plus neuromodulator systems, energy and hunger state, circadian and arousal |
| Counting | one row per shared parameter group, with an instance count and the sharing recorded as an assumption |
| Run horizon | hours, so every slow-state field is in scope and load-bearing |
| Primary graph | whole-CNS male connectome, carrying nerve-cord work across by `mancBodyid` (F-DATA-2) |

Choosing hours as the horizon is the consequential one. It means the circadian
oscillator, nutritional state and arousal are not optional extras but rows that
gate everything else, and most of those rows will be empty.

## The inventory is the deliverable

One machine-readable file. Every quantity the organism needs is one row, at the
coarsest grain where we would currently assume it uniform.

```yaml
- id: SYN-KIN-ACH-NIC
  subsystem: synapse
  quantity: postsynaptic conductance rise and decay time constants
  grain: transmitter x receptor pair
  instances: 2015846
  instance_basis: cholinergic synapses in the reference nerve-cord extract
  value: null
  units: ms
  provenance: empty           # measured | derived | fitted | assumed | empty
  source: null
  conditions: null            # species, sex, age, temperature, preparation
  sharing_assumption: >
    One kinetic pair for every nicotinic synapse in the animal. Almost
    certainly false across cell types. Refine when a test demands it.
  candidate_sources:
    - patch recordings from identified central synapses
  blocks: [any spiking or conductance-based model]
  sensitivity: unknown        # measured effect on a declared readout
```

`provenance` is the column that does the work. Five values, no others, and
`assumed` is never allowed to masquerade as `measured`. That single rule is what
session 1's failures were all violations of: a convention about glutamate sign
was carrying 41% of the model's inhibition, and an excitability rule derived from
a cropped microscope volume was handing sensory neurons a ninefold advantage.
Both would have been visible immediately as `assumed` rows with large instance
counts.

`sensitivity` is filled by experiment, not guessed. Session 1 produced exactly
one worked example of how: redrawing synaptic sign from the classifier's own
probabilities flips 9.5% of the network and destroys the rhythm in a third of
draws, with every failure traceable to four named cells (F-SIGN-3). A row with
high sensitivity, few instances and an available measurement technique is the
cheapest thing in the world to go and settle.

## Subsystems that get rows

Approximate row counts at the chosen grain. These are the estimate to be
replaced by the real enumeration, not a result.

| Subsystem | Grain | Rows | How full, expected |
|---|---|---|---|
| Neuron identity and region | per neuron | ~176,000 | nearly complete from the connectome |
| Chemical connectivity | per connection | ~10^7 | complete as counts, empty as efficacy |
| Electrical coupling | per cell-type pair | unknown | **absent from the connectome entirely** |
| Transmitter and confidence | per neuron | ~176,000 | filled as predictions with stated confidence |
| Receptor complement | per cell type | ~9,000 x n receptors | **mostly empty; this is what sets sign** |
| Neuron biophysics | per cell type | ~9,000 x ~12 | very sparse; a handful of types recorded |
| Synapse kinetics and efficacy | per transmitter x receptor | tens | empty |
| Short-term plasticity | per cell-type pair | unknown | empty |
| Long-term plasticity | per plastic pathway | tens | mushroom body relatively good, rest empty |
| Neuromodulator sources | per neuron | thousands | identities known |
| Neuromodulator action | per modulator x target type | ~9,000 x 4 | **nearly all empty; sets the gain the fragment lacked** |
| Sensory transduction | per receptor class | ~100 classes x ~8 | roles known, rate scales empty (F-GAP-1) |
| Motor unit and NMJ | per motor neuron | ~700 | mapping filled, per-unit force filled at 3 points |
| Muscle mechanics | per muscle | ~200 | 15 of 20 front-leg muscles at whole-muscle grain (F-BODY-1) |
| Body geometry and inertia | per segment | ~100 | largely available |
| Contact, friction, adhesion | per contact surface | ~50 | sparse |
| Aerodynamics | per wing surface | ~20 | RoboFly measurements exist |
| Energy and nutritional state | per compartment | ~10 | empty as dynamics |
| Circadian oscillator | per clock cell type | ~10 x ~8 | partial |
| Sleep and arousal | per state variable | ~10 | empty as mechanism |
| Environment model | per modality | ~10 | a modelling choice, not a measurement |

The two rows to notice are **receptor complement** and **neuromodulator action**.
Both are large, both are nearly empty, and both are exactly what determines
whether a circuit excites or inhibits and at what gain. Session 1 spent a night
discovering, in one subsystem, that these were the missing fields. The inventory
should make that visible on day one across the whole animal.

## Order of work for session 3

**1. Build the skeleton before any values.** Enumerate every field group with its
grain, instance basis and `blocks` list, all values null. This is the spec and it
is cheap. Nothing is simulated. The output is a count: how many rows does a fly
need.

**2. Fill what is queryable.** Connectome identity, connectivity, transmitter
predictions with confidence, muscle targets, body geometry. Mechanical work
against neuPrint and the body model assets. Mark every row `measured` or
`derived` with its source and version.

**3. Mark what current models assume.** Walk the published precedents and record
what each one puts in the empty rows. Session 1 already did this for a few dozen
fields; F-SIGN-1, F-SIGN-2 and F-EXCITE-1 are the template. Every such row is
`assumed` with its instance count, which is what makes it rankable.

**4. Rank.** Sort by instance count times known sensitivity, and cross with
whether a measurement technique exists. The top of that list is the project's
actual research agenda.

**5. Build the scaffold, whose job is to fail loudly.** A runnable whole-organism
loop at the declared grain, with every field read from the inventory. Its purpose
is **not** to produce behaviour. It is to be a completeness checker: anything the
scaffold needs that the inventory does not have is a row that was missed, and it
should raise rather than silently default. Expect it to produce nothing
recognisable, and do not tune it.

**6. Run the control.** The same scaffold with only `measured` and `derived`
values, everything else explicitly absent rather than filled with a convention.
Whatever behaviour emerges is what the real data alone supports. That number,
whatever it is, is the honest baseline this project has never had.

Steps 1 to 4 are bookkeeping and queries, and should be most of session 3. Steps
5 and 6 follow only once the inventory can say what it is missing.

## How to tell it is working

- **After step 1:** a row count and a list of subsystems, with no values. If the
  count is not surprising, the enumeration is too coarse.
- **After step 4:** a ranked list of fields where a named measurement would
  change a named readout. If nothing ranks, the sharing policy collapsed the
  inventory too far.
- **After step 5:** a list of fields the scaffold demanded that the inventory
  lacked. That list is the real test of step 1.
- **After step 6:** a described behaviour, probably nothing, attributable to a
  specific set of absent fields rather than to a global failure.

## What would make me abandon this route

If the skeleton cannot be built without the grain decision cascading, meaning
every row's grain depends on the value of another row, then the inventory is not
separable from the model and the whole approach fails. The test is step 1: if
enumerating fields requires simulating to decide grain, stop and say so.

Second, if step 4 ranks nothing because sensitivity is unknown for essentially
every row, the inventory is a catalogue rather than an agenda. The fix is to
budget sensitivity experiments deliberately rather than hope they accumulate.

## What was deleted, and why

The session-2 cleanup removed every script that drove the isolated fragment: its
runner, its sweeps, its figures and its bespoke analyses, about 40 files. They
answered questions scoped to a part, and the questions are retired. Everything is
in git history at commit `1f7f5a4` or earlier.

What survived is what serves any model: the provenance recorder, the provenance
audit, the data-validation tests, the queried motor-neuron extraction and the
data manifest. Plus `docs/FINDINGS.md`, restated at field level, because knowing
that two specific fields are filled with wrong values and one is empty with no
source is exactly what the inventory is for.

The reference implementation in `external/` is untracked and stays on disk as a
precedent to consult, not a base to build on.
