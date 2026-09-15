# Plan: whole-organism requirement inventory first

Written at the end of session 2, revised after the pack author's response.
Supersedes the milestone sequence in `docs/ROADMAP.md`, which built upward from
an isolated leg.

## Why the approach changed

Session 1 took the front-leg premotor network of the nerve cord and tested it in
isolation. It could not simultaneously produce a rhythm and motor output strong
enough to move a leg, across 333 simulations, and that was reported as a property
of the modelling approach. It was a property of the isolation. Descending drive,
sensory context and neuromodulator state were all absent, so the circuit had no
defined operating condition.

You cannot isolate the part of a brain that walks forward. Walking is under
voluntary control and continuously corrected by systems that are not the walking
circuit. A fly is simpler, not different in kind.

The pack author accepts the ordering error and adds the precise version of it:
**tethering and removing neural context are different interventions and need
separate description.** Tethering imposes a mechanical constraint. Removing
afferents, descending inputs or modulation changes the system being tested. An
isolated premotor circuit is a legitimate experiment only once its external
drive, sensory conditions, modulatory conditions, initial state and mechanical
load are all specified. Without those, failure to oscillate cannot distinguish a
wrong local circuit from a wrong operating condition. Session 1 had none of them
specified and treated the result as a feasibility gate anyway.

## Step zero, which the plan previously skipped

The `model_use` column cannot be filled without having chosen equations, and the
equations determine the requirement list. That is a genuine circularity and it
was sitting unaddressed in the abandon criteria.

It resolves by declaring the model family **M** first, as an explicit and
revisable assumption, before enumerating anything. The grain decision already
commits most of it: single-compartment units, per-cell-type physiology, synapses
as weighted sums with kinetics, rate or spiking to be fixed. Write that down as
M, with its known omissions listed, and every requirement then follows
mechanically from it.

A different M gives a different inventory. That is not a flaw, it is why the
output form is always *for model family M and assay set A*, never a bare
percentage. When M changes, the inventory is regenerated, and the diff between
the two is itself informative.

## The governing idea

Treat this as **an experiment in biological identifiability**. The question is
which properties of a working fly are forced by the measurements, which depend
on additional assumptions, and which remain interchangeable even after extensive
validation. Building a convincing fly is the first instrument for running that
experiment, not the goal in itself.

That reframing changes what the inventory is for. It is not a completeness score.
It is a map of what the data can and cannot pin down.

## Scope, as decided

| Decision | Choice |
|---|---|
| Grain, physiology | per cell type, with within-type variation as a distribution |
| Grain, structure | per neuron, because that is what the connectome gives |
| Boundary | core loop, plus neuromodulator systems, energy and hunger state, circadian and arousal |
| Counting | one row per shared parameter group, with instance count, **plus separate rows for the shared inference dependencies** |
| Run horizon | tiered: seconds for sensitivity, minutes for assays, hours for slow-state demonstration only |
| Primary graph | whole-CNS male connectome, carrying nerve-cord work across by `mancBodyid` |

Hours of simulated time does not by itself demand more resident memory than
seconds; runtime, retained recordings and optimisation history are separate
costs, and streaming forward simulation keeps bounded state. Differentiating
through a long trajectory is the expensive case. Whole-CNS against BANC was never
compared, so whole-CNS is a default, not a settled choice.

**The horizon has to be tiered, and the plan previously was not.** Measured
against the actual graph: `male-cns:v1.0` has **25,862,574 neuron-to-neuron edges
carrying 125,024,863 synapses**. At a generous 10^10 edge-updates per second on
one consumer GPU:

| Timestep | Edge-updates per simulated hour | Wall time per simulated hour |
|---|---|---|
| 1 ms | 9.3 x 10^13 | ~2.6 hours |
| 0.1 ms, needed for a 200 Hz wingbeat | 9.3 x 10^14 | ~26 hours |

So a single hours-long demonstration run is affordable and a replicate-heavy
sweep at that horizon is not. The tiering:

| Tier | Horizon | Replicates | Purpose |
|---|---|---|---|
| A | 0.1 to 2 s | many, hundreds | sensitivity and identifiability, where most of the science is |
| B | seconds to a minute | tens | assay-level behaviour checks |
| C | hours | one or two | slow-state demonstration only |

Every sensitivity and identifiability result therefore comes from tier A, and
tier C exists to show that slow fields are wired in at all. Choosing hours as the
project horizon was right; assuming the whole plan runs there was not.

## What makes a requirement inventory legitimate

A field count is meaningless on its own. You can change the percentage without
changing the model: split receptor complement into fifty columns, collapse ten
channel parameters into one object, or store connectivity as contacts rather than
edges. None of that changes what has been measured.

Counting is legitimate only when the claim is explicitly about **coverage of a
defined model's requirements**. So the unit of the inventory is a *requirement*,
and each one carries eight things:

| Column | What it establishes |
|---|---|
| `entity` | cell, cell type, compartment, connection class, muscle, receptor organ |
| `property` | a named physical quantity, categorical property, or response function |
| `conditions` | sex, age, temperature, preparation, physiological state, stimulus range |
| `model_use` | which equation or interface requires it |
| `evidence` | exact measurement, dataset, annotation, or derivation |
| `transfer` | why evidence from another cell, specimen or preparation applies |
| `uncertainty` | bounds, distributions, and which other rows share the uncertainty |
| `status` | measured, derived, fitted, assumed, unresolved, conflicting, inapplicable |

Three rules that the session-1 failures were all violations of.

**Keep observations separate from model parameters.** A calcium response is an
observation. A firing-rate transfer function inferred from it is a different
object with additional assumptions. They get different rows and the inference
between them is itself a row.

**Distinguish partially constrained from filled.** Transcriptomic evidence may
support receptor presence while leaving density, localisation, conductance and
modulation unresolved. That is not a filled row.

**Count the shared inference dependencies, not just the requirements.**
Propagating one assumed conductance to 5,000 neurons fills 5,000 rows and adds
no independent evidence. If the inventory does not represent that, it will look
complete while being empty. The dependency is the thing to count.

The defensible output form is: *for model family M and assay set A, N% of
required quantitative properties have directly matched measurements.* Never: *we
possess N% of the fly's behavioural information.*

## Identifiability, which the inventory must represent

Some quantities are recoverable only in combination. If sensory firing is
modelled as `r = g_s · f(θ)` and downstream current as `I = w · r`, then
observing downstream current constrains the product `w · g_s` and not either
factor. Doubling sensory gain while halving synaptic efficacy produces identical
observations.

That is not a failure. It means the data identify an effective interaction while
leaving its biological decomposition open. But if the inventory does not carry
these coupled ambiguities explicitly, I will spend days estimating quantities
that the chosen observations mathematically cannot separate. Adaptation,
saturation, noise and direct neural recordings are what can break the degeneracy
later.

So the inventory needs, alongside each row, which other rows it is only jointly
identifiable with under a stated observation set.

## Subsystems that get rows

Counts verified against `male-cns:v1.0` where possible. These are the estimate to
be replaced by the real enumeration.

| Subsystem | Grain | Rows | Expected fill |
|---|---|---|---|
| Neuron identity and region | per neuron | ~166,700 with non-null superclass | near complete |
| Chemical connectivity | per connection | separate, much larger tables | complete as counts, empty as efficacy |
| Electrical coupling | per cell-type pair | unknown | no comparable reconstruction in these releases |
| Transmitter and confidence | per neuron | ~166,700 | predictions with stated confidence |
| Receptor complement | per type x subtype x compartment | large | **mostly unresolved; this sets sign** |
| Neuron biophysics | per type | 11,751 labels x 10-30 groups | very sparse |
| Synaptic efficacy and short-term dynamics | per connection class | unknown | empty |
| Long-term plasticity | per plastic pathway | tens | mushroom body relatively good |
| Neuromodulator action | per modulator x target x dose x location | large | **nearly all unresolved; sets gain** |
| Sensory transduction, quantitative | per receptor class | ~100 x ~8 | roles known, absolute gain empty |
| Neuromuscular recruitment and force | per motor unit | ~700 | 3 measured points for one pool |
| Muscle mechanics | per muscle | ~200 | 15 of 20 front-leg muscles, whole-muscle grain |
| Body geometry and inertia | per segment | ~100 | largely available |
| Contact, friction, adhesion | per surface | ~50 | sparse |
| Aerodynamics | per wing surface | ~20 | RoboFly measurements exist |
| Energy and nutritional state | per compartment | ~10 | empty as dynamics |
| Circadian oscillator | per clock cell type | ~10 x ~8 | partial |
| Sleep and arousal | per state variable | ~10 | empty as mechanism |
| Physiological initialisation | per state variable | large | empty |
| Glia | per glial class | thousands of cells | present in the annotation, absent from every model here |
| Humoral and hemolymph signalling | per circulating factor | tens | empty; carries hunger and hormonal state |
| Sensory organ mechanics | per organ | ~50 | distinct from transduction; tendon coupling, antennal resonance |
| Wing hinge mechanics | per hinge element | ~20 | a distinct bistable structure, not just aerodynamics |
| Efferent control of sense organs | per organ x modulator | ~50 | flies modulate their own receptors; almost always omitted |
| Environment model | per modality | ~10 | a modelling choice, not a measurement |

The last five were missing from the first draft of this table. Glia in
particular are annotated in the primary graph and appear in no model this project
has touched, despite doing potassium buffering and having roles in sleep and
circadian regulation, both inside the chosen boundary.

**11,751 is a count of distinct `type` labels, not of established distinct
physiological types.** Any grouping down from that number needs an explicit
rationale recorded as an assumption. Session 2 initially guessed 9,000 from
memory, which is exactly the kind of unverified number this project keeps
tripping over.

The categories expected to dominate *uncertainty* are not necessarily those
dominating *row count*. Receptor complement is not one missing scalar per type;
its relevant structure spans subtype, compartment, connection class, density and
physiological state. Neuromodulator action likewise spans dose, location,
kinetics and interactions.

Planning expectation, held at low confidence and not an audited result: **over
80% of quantitative, type-specific physiology requirements will lack directly
matched measurements.** No single overall percentage across structure and
physiology should be quoted, because their relative row counts would dominate it
arbitrarily.

## Cataloguing absences properly

"Never measured" is a stronger claim than a literature search usually supports.
For each unresolved row, record which kind of absence it is:

1. Not present in the scan.
2. Available only through an indirect observable.
3. Measured in another species, stage, cell or preparation.
4. Available but not mapped to connectome identity.
5. Not located after a documented search.
6. Conflicting or insufficiently quantitative.

The defensible form for the leg proprioceptor case is *the cited resources do not
establish the required absolute firing-rate calibration*, which is category 2.
Its response selectivity constrains the shape of a sensory model while leaving
absolute gain and timing unresolved, and those must stay explicit through fitting.

## Which behaviours make a field required

A field is required because a modelled mechanism depends on it under a declared
assay, not because its neuron carries a convenient behaviour label. The minimum
inventory scope, as a research contract rather than a definition of a fly's life:

| Capability | Behaviours the inventory must support |
|---|---|
| Terrestrial movement | posture, initiation and stopping, turning, coordinated stepping, disturbance recovery |
| Flight | power generation, stabilisation, steering, takeoff and landing |
| Sensory responses | light, motion and looming; odour; contact and taste; proprioception; load and airflow feedback |
| Maintenance | grooming and feeding-related actions |
| Internal state | defined arousal and hunger effects on behaviour |
| Learning | one conditioning protocol, retention, and reversal or extinction |

Courtship, reproduction, sleep behaviour and additional modalities are **later
scope, explicitly marked**, not accidentally omitted. Acceptance thresholds come
from specified experimental datasets, later.

## Order of work for session 3

**0. Declare the model family M.** One page. The equation forms, the grain, and
an explicit list of what M omits entirely, for example gap junctions,
compartmental integration, glia. Nothing below is meaningful without it.

**0b. Declare the type-grouping policy.** The primary graph carries **11,751
distinct `type` labels** over 164,506 typed neurons. Some are genuine
physiological types, some are annotation granularity. Any grouping below 11,751
is an assumption and gets recorded as one, with its rationale. Do not quietly
round to a convenient number, which is what session 2 did when it wrote 9,000
from memory.

**1. Build the requirement skeleton, no values.** Every requirement with entity,
property, conditions, `model_use` and grain, all evidence null, plus the
dependency rows. Nothing simulated.

Concrete deliverable, so this is checkable rather than vague: one file, a total
row count, a per-subsystem breakdown matching the table above, a dependency graph
of which rows share an inference, and a list of the twenty requirements with the
largest instance counts. If the total is not surprising, the enumeration is too
coarse.

**2. Fill what is queryable.** Identity, connectivity, transmitter predictions
with confidence, muscle targets, body geometry. Each row `measured` or `derived`
with source and version.

**3. Mark what current models assume.** Walk the published precedents and record
what each puts in the unresolved rows. `docs/FINDINGS.md` has the template in
F-SIGN-1, F-SIGN-2 and F-EXCITE-1. Each becomes `assumed` with an instance count.

**4. Rank, then test identifiability, then budget experiments.** Rank by instance
count times load-bearing-for-a-declared-assay times whether a measurement
technique exists. Sensitivity is unknown for nearly every row, so it cannot be a
ranking input yet. That is why the next part is a step rather than a hope:
**budget ten tier-A sensitivity experiments** against the top of that list, run
them, and write the results back into the `uncertainty` column. Then ask of each
high-ranking row whether the proposed observation can separate it from its
partners at all. A row that ranks high but is only jointly identifiable needs a
different experiment, not a measurement.

**5a. Instantiate the scaffold and let it fail loudly.** Build the whole-organism
model at the declared grain, reading every field from the inventory, and run
**initialisation only, no integration**. Its purpose is completeness checking, so
it does not need to simulate anything. Every field it reaches for that the
inventory lacks must raise. This is cheap and it is the real test of step 1.
**"Not implemented" must never mean "biologically inactive."**

**5b. Integrate, once 5a passes.** Tier A first. Expect nothing recognisable and
do not tune it.

**6. Run the control, and expect it not to run.** The honest version of "only
measured values" is that it **almost certainly cannot integrate at all.** If over
80% of type-specific physiology is unresolved, the model has connectivity and
identity but no membrane time constants, no thresholds and no synaptic
efficacies. There is nothing to integrate.

That is not a failed step, it is the finding, and stating it in advance stops it
being dressed up later. So the control is defined in three versions, reported
together:

| Control | Unresolved rows filled with | Expected outcome |
|---|---|---|
| C0, strict | nothing; refuses to run | does not execute; the row list it refuses on *is* the result |
| C1, minimal | one declared population-level default per subsystem, every default recorded | runs, probably produces nothing recognisable |
| C2, conventional | what the published precedents assume, from step 3 | runs; reproduces known results and their known fragilities |

C0 versus C1 is the honest measure of how much of this model is convention rather
than measurement. C1 versus C2 says whether the specific conventions in current
use are doing real work or could be anything.

Steps 0 through 4 are declaration, queries, bookkeeping and ten small
experiments, and should be most of session 3.

## Working rules adopted from the pack author's response

**Missing context can masquerade as missing physiology.** A silent circuit may
have wrong membrane parameters, or may simply lack its normal inputs. An unstable
circuit may have excessive gain, or may lack the feedback that stabilises it.
This is exactly what session 1 got wrong.

So: **every failed experiment produces competing causal hypotheses before it
produces parameter changes**, and each hypothesis names an observation that would
distinguish it. If the available evidence cannot distinguish them, both are
preserved. Otherwise optimisation compensates for an omitted subsystem by
corrupting one whose parameters were already reasonable.

**A short decision record precedes any consequential model change**, stating the
discrepancy, the competing explanations, the supporting evidence, the proposed
change, and the expected effect on an *independent* measurement. "The fly walks
better" can justify investigating a change. It cannot establish that the change
is biologically correct.

**A convincing movement can conceal two compensating errors.** Weak muscles plus
excessive motor firing gives plausible joint motion. Wrong visual sensitivity
plus excessive steering gain gives plausible turns. So optimise against several
levels at once, sensory responses, neural activity, muscle activation, forces and
motion, and reserve interventions for evaluation.

**Separate replication from physiological endorsement.** Keep a faithful
reproduction of any published model alongside the candidate biological model.
Reproducing establishes that the implementation is understood. Replacing a
questionable assumption tests whether the conclusions survive. Combining the two
makes failures uninterpretable and invites accidental edits to the reference.

**Use meaning-based sanity checks, not just code tests.** Ordinary tests often
encode the same mistaken assumption as the implementation. Five are now in
`tests/test_source_data.py`: resampling preserves frequency in hertz, unit
conversion preserves physical predictions, cropping a reconstruction is not a
change in intrinsic excitability, a missing connection record stays
distinguishable from a supported absence, and a calcium observation cannot
acquire firing-rate units without an explicit calibration. Timestep halving
should also not change a conclusion once converged.

## The later experiment this all serves

Once several biologically admissible working models exist, take each as synthetic
ground truth. Reveal progressively richer measurements, topology, then
transmitter assignments, then selected physiology, then perturbation responses,
and ask independent reconstruction runs to recover its held-out responses and
individual differences.

Use several ground-truth model *families*, including some different from the
reconstruction algorithm's family. Otherwise the result is only that an algorithm
can recover its own assumptions. This estimates measurement sufficiency within
the tested model classes. It does not establish that real brains have no
additional relevant mechanisms.

## What would make me abandon this route

If enumerating fields requires simulating to decide their grain, the inventory is
not separable from the model and the approach fails. Step 1 is the test.

If step 4's ten budgeted experiments come back with every sensitivity
indistinguishable from zero or from each other, the inventory is a catalogue
rather than an agenda, and the ranking has no signal to work with. That would be
a real result about the model family and a reason to change M rather than to
continue enumerating under it.

And an inventory identifies unresolved quantities; it does not by itself
establish their effective independent dimension. Two thousand missing fields
might reduce to twenty shared mechanisms or expand to hundreds of independently
important differences. Establishing which requires evidence for parameter
sharing, then sensitivity and identifiability analysis. Enumerate the unknowns
and the proposed sharing rules first; measuring which combinations matter comes
after.
