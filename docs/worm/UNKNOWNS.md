# The worm's unknown numbers

Status 7 Nov 2026 (wmodel). Source: `wormemu.params` (`counts()`, `Theta().table`, `catalog()`), all measured
from the code today.

**Verdict.** 347 numbers are genuinely unknown. That is the whole fit vector: 43 shared rules plus 304 gaps (15 of
them discrete). It is well under Ben's 1,000-2,000 target. Everything else is fixed and labelled with its origin
(1,270 scan rows covering 79,942 elements), or taken out of the vector for a stated reason (317 rows). The
per-element residuals (6,298 slots) are frozen at 0. Today's wiring moved the count from 340 at 13:00 to 347: a net
seven quantities that code now reads became gaps. Fitting has not started.

## What the roles mean

| role | n | in the fit? | what it is |
|---|---|---|---|
| rule | 43 | yes | a shared rule on structure (`structure_rules`): a few numbers that set many per-cell values from CeNGEN, EM counts and transmitter identity |
| gap | 304 | yes | a guessed or absent value the code reads, with a cited range (`lo`, `hi`) where wranges has one |
| scan | 1,270 rows, 79,942 elements | no, fixed | measured, published fit, derived or inferred; labelled with its origin for debugging |
| residual | 6,298 slots | no, frozen at 0 | a per-element correction on top of a rule; frozen until the rules alone fail held-out data |
| inactive unknown | 317 | no | guessed or absent, but out of the vector for the reason below |

## Why 317 unknowns are out of the vector

| reason | n | meaning |
|---|---|---|
| replaced by structure_rules | 197 | per-cell or per-class values now set by a rule. The rule's numbers are in the vector instead |
| other form only | 73 | read only by a mechanism form that is off by default (for example muscle_active's 10, peptides' 5). It enters if that form is adopted |
| slot only | 29 | a ledger slot with no code reading it yet (monoamine uptake 4, sleep_ris_ala 3, ...) |
| absorbed | 8 | the receptor unitary conductances: only gamma x syn_nchan_per_em_* enters, so the product is the gap |
| linked | 4 | set by another quantity: `ion_celsius` and `env_default_temperature_C` (the experiment's temperature), `body_pressure_kPa` and `body_pressure_ctrl_kPa` (organs_other's steady pressure) |
| not read | 3 | `ion_ena` (nca uses its own +30 mV), `ion_cao` (sets only NEURON's Nernst eca; every Ca current uses +60 mV), `glia_k_gleak_nS` (replaced by `glia_k_leak_frac`, the K+ share of each amphid neuron's own leak) |
| other | 3 | single rows; `params.catalog()` gives each reason |

## The 347 by grain

| grain | n |
|---|---|
| class | 184 |
| global | 106 |
| gene | 20 |
| cell | 19 |
| channel | 11 |
| pathway | 4 |
| pairing | 3 |

The 19 per-cell numbers are the 15 discrete synapse signs (`syn_inhibitory[cell]`, the cells whose sign CeNGEN
cannot settle), three cell areas in other_cells and `osmo_canal_gain`. Nothing in the vector is per synapse.

## The 347 by PLAN row

| row | | n | row | | n |
|---|---|---|---|---|---|
| 5 | channel densities, Cm, leak | 8 | 17 | sensory transduction | 33 |
| 6 | calcium | 1 | 18 | slow signalling | 14 |
| 7 | chemical synapses | 86 | 19 | homeostatic tuning | 5 |
| 8 | gap junctions | 19 | 20 | metabolism | 4 |
| 9 | neuropeptides | 17 | 22 | environment | 6 |
| 10 | monoamines | 12 | 23 | observation | 7 |
| 11 | glia | 14 | 24 | plasticity and learning | 22 |
| 12 | body-wall muscle | 7 | 25 | temperature | 5 |
| 13 | pharynx | 5 | 26 | noise | 12 |
| 14 | intestine and defecation | 30 | 27 | ion pumps | 6 |
| 15 | egg-laying | 14 | | | |
| 16 | other non-neural cells | 17 | 21 | body (damping) | 3 |

Eight of these are code Specs added today or earlier with no ledger row yet (`rec_des_recover_ratio` in 7, DAF-7,
CREB and the two AFD T* fractions in 18, the three damping numbers in 21); wranges has the list. Rows 1-4 (inventory,
morphology, channel presence, kinetics) and 28 (sleep, through row 9) have no gaps: they are scan.

## The largest mechanisms

receptor_kinetics 48; structure_rules 44 (43 rules plus 1 gap); defecation 19; peptides 17; syn_sign 15;
egg_laying 14; slow_signalling 14; monoamines 12; channel_noise 11; stp 11. The other 44 mechanisms have 9 or fewer
each. The body has 3 (`body_damp_tau_ms`, `body_damp_w_ref_rad_s`, `body_damp_clip`).

## Degeneracies the fit will meet

These are pairs or groups the data cannot tell apart. They are not removed yet; the fit should constrain them
jointly (wranges' 177 joint constraints cover some) or fix one side.

- `gap_open_channels` x each innexin's unitary conductance: only the product sets a gap junction's conductance.
- `cmk1_*_effect` and the AFD T* fractions (`afd_tstar_fast_frac`, `afd_tstar_slow_frac`): both scale how far T*
  moves, so a check on T* alone cannot split them.
- The receptor unitary conductances x `syn_nchan_per_em_*` are already merged (the 8 "absorbed" rows).

## The failing unit checks: values, not bugs

11 of the audit's unit checks fail today (MECHANISMS_AUDIT.md, counts; 13 lines below, as rows 17 and 21 each fail
two ways). None is a code bug.

| row | check | fails | why |
|---|---|---|---|
| 7 | NMJ IPSC | 29.2 ms against 24.8 +/- 2.7 | gap values: the UNC-49 and release kinetics together (UNC-49 alone passes) |
| 11 | glia | recovery 0.525 s; right side 26% (before the 7 Nov K+ leak fix; not re-run) | gap values: the K leak's reversal feedback sets recovery |
| 15 | egg-laying | no egg in 3 h | gap values: HSN's resting 5-HT release is low against nM EC50s |
| 16 | other cells | canal 10.7 h against 12-24 h | gap value: the canal time constant |
| 17 | proprioception | DVA Po 0.483 against > 0.5 | gap value: the gain |
| 21 | body damping | 16.7 ms | gap value |
| 23 | opto | AVAL +0.39 mV against > 1 | gap value: the sign is right, the conductance is guessed |
| 24 | GABA | plateaus 0.76, 0.57 against > 0.8 | gap value: GABA short-term plasticity borrows ACh's numbers |
| 4 | channel W | 3.8 mV against 2 | scan: two published kinetic models differ (BAAIWorm's mods at Nicoletti's AIY densities) |
| 6 | Ca volume | AIYL 3.05x, RIML 2.21x, VA05 2.05x | scan: BAAIWorm's hoc morphology against Nicoletti's NeuroMorpho cells, two reconstructions |
| 17 | AWA | 33.9 mV against 25.8 +/- 6 | published fit: the NEURON mod matches the scipy Table S4 reference within 0.07 mV (measured); the Table S4 transcription is not re-checked |
| 21 | body bending | 856 kPa, 7.8x the measurement | scan: the layer moduli are a published fit (frontiers2024) |
| 28 | RIS Gi | 0.034 against 0 | the bar is probably wrong: it assumes DMSR-1 is RIS's only Gi input, and CeNGEN gives RIS others |

The 8 value failures are the fit's job. The 4 scan and published-fit rows (4, 6, 17 AWA, 21 bending) need a decision,
not a fit: either promote the number to a gap with its published value as the prior, or find a representation error.
Row 21 is the one most likely to matter for behaviour.

The single-cell excitability sanity check (wexcite: 74 cells over the upper bar, 47 below -150 mV) traces to
expression-map values, which are rules and gaps in the vector. It is a value failure too.

## How to use this

- The vector: `params.Theta()` (ids, bounds, transforms, origins); `params.set_value(spec, id, x)` sets one and
  raises on a scan number.
- The model the fit calls: `wormemu.simulate(theta, experiment)` (DATA_MODEL.md).
- Where each number acts: INTERCONNECT.md (who reads whom) and MECHANISMS_AUDIT.md (per PLAN row).
