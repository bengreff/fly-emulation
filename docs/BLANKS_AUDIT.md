# Blanks audit (session 12, 2026-10-04)

Question (Ben, 2026-10-04): do we have the full set of blanks, at every grain down to the single synapse? A blank is a measurable quantity of a real fly. Each one should have a ledger slot (`data/ontology/fly_information.yaml`) and a mechanism that carries it (`data/model/mechanisms.yaml`), even if that mechanism is only a registered stub held at a neutral value.

Answer: the ledger now has 143 measurable quantities. Before this audit it had 91. Every one of the 143 names a mechanism. 22 of them are carried by one of 14 new stubs. Of the 91 earlier rows, 8 had no carrier (`mech: none`); every row has one now. 102 quantities are simulated in some form, 26 at their own grain. The other 41 have a slot and an owner but no simulated value.

Reproduce:

    uv run python scripts/blank_ledger.py         # regenerates data/derived/blank_ledger.csv, ledger_levels.csv
    uv run python scripts/blanks_audit.py         # before (git 80836db) vs now; writes data/derived/blanks_audit_coverage.csv
    uv run pytest tests/test_stubs.py tests/test_model_data.py

Raw outputs: `runs/s12/ledger_before.txt`, `runs/s12/ledger_after.txt`, `runs/s12/blanks_audit.txt` (not tracked).

## Method

I went through the fly grain by grain: synapse, connection (edge) and cell pair, cell, cell type, class and neuropil, body part, and organism and world. At each grain I listed what an experimenter can measure, from the categories Ben named (below) and from the CONSTRUCTION inventory. For each quantity I asked four questions:

| column | meaning |
|---|---|
| slot | the ledger has a row for it |
| carrier | the row names a mechanism that exists in the inventory, built or stub |
| simulated | the model uses some value for it (`fidelity` is not `none`) |
| own grain | the model's value varies at the quantity's own grain (`fidelity: element`) |

A quantity with no row got a new row (tagged `audit: s12`) with labels for the model as it stands today: fidelity, model state (simulated/default/absent) and source basis. Adding a row never improves a label. If no existing mechanism could own the row, I added a stub mechanism. If an existing mechanism holds the quantity at a coarser grain than the measurement, the row keeps that mechanism and names the stub that would hold it at its own grain under `upgrade:` (for example, release probability is held per class by N10, and N29 would hold it per synapse).

The enumeration is mine, made from the literature and the inventory. It is not checked against an external standard, so "full set" means "nothing I could name is missing", not a proof. Known limits are listed at the end.

## Stubs (14 new mechanisms, all `status: absent`)

Each stub has an inventory entry, a registry switch that the organism reads at build time (`src/flyemu/stubs.py`), and a test. At its neutral value the switch leaves the model exactly as it was. Any other value raises `NotImplementedError`, so a stub can never pass for a built mechanism (`tests/test_stubs.py`).

| id | tier | switch (neutral) | what it would build | ladder rung |
|---|---|---|---|---|
| N29 | A | `synapse:all\|per_synapse_parameters` (0) | per-synapse weight, release probability, STP, receptor mix, latency | 8 |
| N30 | A | `cell_type:all\|n_compartments` (1) | reduced multi-compartment neurons, synapses placed by position | 6 |
| S6 | A | `state:hemolymph\|ion_model` (0) | hemolymph ions setting reversal potentials | |
| B24 | B | `sense:all\|efferent_gain_control` (0) | central (e.g. octopaminergic) gain control of sense organs | |
| B26 | B | `body:cuticle\|compliance` (0) | segment and thorax elasticity, cuticle strain | |
| N31 | C | `synapse:all\|structural_plasticity` (0) | synapse addition and removal during life | |
| N32 | C | `cell_type:all\|homeostatic_plasticity` (0) | activity-dependent regulation of channel densities | |
| N33 | C | `glia:all\|astrocyte_model` (0) | astrocyte uptake, OA/TA-gated Ca, glial coupling | 7 |
| N34 | C | `synapse:other_sites\|plasticity` (0) | plasticity outside the mushroom body and ring | |
| B25 | C | `sense:active\|sensor_muscles` (0) | retinal and antennal muscles | |
| B27 | C | `state:circulation\|model` (0) | heart, hemolymph flow, tracheal ventilation | |
| S7 | C | `state:immune\|model` (0) | immune state and gut microbiome | |
| S8 | C | `state:reproductive\|model` (0) | male reproductive state, pheromone production | |
| D1 | C | `development:all\|model` (0) | lineage, birth order, maturation, rearing (construction time) | |

Consequence: session 10 reported 0 absent mechanisms in tiers A and B. That no longer holds. Tier A now has 3 absent (N29, N30, S6) and tier B has 2 (B24, B26) (as of the audit; N29 became partial on 5 October, see the data-first pass below). Nothing got worse; the audit found these quantities had no owner. Inventory: 70 mechanisms. Tier A: 13 have, 15 partial, 3 absent. Tier B: 3 have, 9 partial, 2 absent. Tier C: 1 have, 15 partial, 9 absent. `model_data.validate` reports 0 problems.

## Data-first pass on the stubs (night of 5 October)

Director night order item 3: each stub in audit order, data first, every number labelled. The records hold the sources and how each was read (read by me, agent, or unverified).

| id | data found (label) | decision | record |
|---|---|---|---|
| N29 | ORN→PN and ORN→LN Tsodyks-Markram fits to recorded EPSC trains (Nagel 2015; Nagel & Wilson 2016; derived) | **partial**: per-connection STP built behind the switch, off (cut LN and PN rates 67-80% at rest; held-out ordering failed) | DECISIONS 22:20 and result; F-STP-1 |
| N30 | Cable values fitted for DM1 PNs and HS cells only (Gouwens & Wilson 2009; Cuntz 2013; fitted). Electrotonic length per type derived from skeleton radii that sit at a floor value for 76% of types | absent; build plan and validity range written | `docs/research/s12_compartments.md` |
| S6 | Adult hemolymph K about 26 mM, Na 26-36 mM (measured by ion-selective electrode; agent read, page blocked for me); brain interstitial ions unmeasured | absent | `docs/research/s12_hemolymph_ions.md` |
| B24 | No measured efferent to a Drosophila sense organ. Found: presynaptic inhibition of hook axons by 9A (Dallmann 2025, read), octopamine on Mi4 (Strother 2018, read), dopamine on labellar sugar GRNs (Inagaki 2012, read) | absent; content belongs to the connectome, N19 and the hunger gain | `docs/research/s12_b24_b26.md` |
| B26 | Drosophila thorax stiffness unmeasured; whole middle leg compression 13.1 ± 7.97 µN/mm (Oeftger 2026, read), used as a held-out check: model leg 3-5× softer | absent; the leg result is a B3 tone target | `docs/research/s12_b24_b26.md`; DECISIONS 22:37 and result; F-LEGK-1 |
| N31 | Wake raises synapse size or number over hours, sleep reverses it (Bushey 2011); no per-synapse rule | absent | `docs/research/s12_tierC_stubs.md` |
| N32 | Compensation over hours to days (Apostolopoulou & Lin 2020); recorded channel values are already the adapted state | absent | same |
| N33 | Larval astrocyte Ca oscillates and silences DA neurons via adenosine (Ma 2016); no adult transfer function | absent | same |
| N34 | Giant-fibre pathway habituation measured (Engel & Wu 1996), the first fit target | absent | same |
| B25 | Retinal muscle kinematics measured (Fenk 2022); retinal motor neurons not identified in male-cns | absent | same |
| B27 | Spiracle aperture tracks flight power and spiracle closure limits it (Luo ... van Breugel & Tuthill 2026, read). The spiracle motor neurons are in male-cns as ENXXX226 (inferred), with their measured GABAergic interneurons SpINA/SpINB (INXXX204, INXXX472), and are simulated as neurons. Heart rate 3-6 Hz (unverified) | absent; reason corrected; 3-step build plan for when flight runs | `docs/research/s12_b27_s7_s8_d1.md` |
| S7 | Axenic females walk faster, and octopamine reproduces it (Schretter 2018, read); infection raises male activity and sleep (read) | absent; healthy, conventionally reared fly stated as the assumption; validation data must record rearing and infection | same |
| S8 | Courtship matures over 72 h after eclosion; mature-male tap starts courtship 47% of the time (Zhang 2021, read); cVA 0.2-2.9 µg on a mature male (read, review) | absent; courtship not a target; the model fly is a mature male | `docs/research/s12_b27_s7_s8_d1.md` |
| D1 | Specimen record: 5-day-old Canton S G1 × w1118 male (Berg 2025, read), 12:12 LD, dissected ZT 1.5 (Nern 2024, read); density, food, temperature not stated | absent; values recorded on the age, rearing and genotype rows | same |

Counts after the pass: tier A 15 have, 16 partial, 2 absent (N30, S6); tier B 3 have, 9 partial, 2 absent (B24, B26); tier C 1 have, 15 partial, 9 absent; 72 mechanisms.

## Ben's categories mapped to ledger rows

New rows are marked (new). Every other row existed before the audit.

| category | rows |
|---|---|
| cells | cell identity and type, morphology; per-cell channel densities (new); cell volume and area, motor neurons (new, measured, used) and other cells (new, measured, unused); spike-initiation zone and calibre (new); homeostatic set point (new); intracellular signalling state (new); per-cell transcriptome (new) |
| synapses, per synapse | weight: per-synapse efficacy (new, upgrade N29). Position: synapse locations on the neuron (existing, owner moved X1 to N30). Release probability (new). STP (new). Receptor mix (new). Also: latency (new), polyadic structure (new), vesicle content (new), presynaptic receptors (new), plastic state (new, upgrade N34), weak synapses on 1-4 synapse connections (new). Ultrastructure (existing, upgrade N29) |
| channels | ion-channel complement (existing; was `mech: none`, now N2 rung 1); intrinsic bursting (existing, now N2); channel kinetics per gene (new); per-cell densities (new) |
| receptors | fast receptor sign and other subtypes per postsynaptic type (existing); modulator receptors per type (existing); per-synapse receptor mix (new); presynaptic receptors (new); gustatory receptor identity per GRN (new) |
| modulators and volume transmission | modulator release and receptors (existing); modulator concentration per neuropil (new); release sites per modulatory cell (new); extracellular K+ and transmitter per neuropil (new) |
| gap junctions | electrical synapses per type (existing); electrical coupling per cell pair (new) |
| glia | glial cells, glial functions (existing); ensheathment per glial territory (new); transporters and coupling per glial type (new); stub N33 |
| development state | developmental identity code per type (new); age and maturation (new); rearing history (new); stub D1. Hemilineage labels are in the cache (53,600 of 176,422 male-cns bodies have one) |
| body: cuticle | cuticle elasticity (existing, now B26) |
| body: joints | joint stiffness, damping, ranges (existing); passive rest angle per joint (new) |
| body: muscles | muscle parameters (existing); fibre type and motor-unit composition (new); fatigue and energetics (new) |
| body: sensors | proprioceptor periphery (existing); afferent to sensillum assignment (new); proprioceptor tuning per afferent (new); sensillum position and orientation (new); efferent control (existing, now B24); ocelli (new); retinal muscles (new); antennal muscles (new) |
| body: organs | heart and trachea (existing, now B27); reproductive system (existing, now S8); proboscis hydraulics (new); immune and microbiome (new, S7); hemolymph ions (new, S6) |
| body: wings and halteres | wing hinge mechanics (new); courtship song (new); haltere mechanics (new) |
| organism and world | sex and genotype (new); substrate mechanics (new); sound and vibration (new); conspecifics (new) |

## Coverage before and after, per grain

Counts of measurable quantities (from `data/derived/blanks_audit_coverage.csv`). "Before" is git 80836db.

| grain | quantities | slot | carrier | of which stub | simulated | own grain |
|---|---|---|---|---|---|---|
| synapse | 12 | 2 → 12 | 2 → 12 | 2 | 0 → 6 | 0 → 0 |
| edge and cell pair | 4 | 2 → 4 | 2 → 4 | 0 | 2 → 3 | 1 → 1 |
| cell | 23 | 13 → 23 | 13 → 23 | 2 | 12 → 17 | 6 → 7 |
| type | 40 | 36 → 40 | 33 → 40 | 2 | 30 → 34 | 12 → 12 |
| class and neuropil | 17 | 10 → 17 | 9 → 17 | 6 | 9 → 11 | 0 → 0 |
| body part | 26 | 15 → 26 | 14 → 26 | 3 | 13 → 19 | 5 → 6 |
| organism and world | 21 | 13 → 21 | 10 → 21 | 7 | 8 → 12 | 0 → 0 |
| all | 143 | 91 → 143 | 83 → 143 | 22 | 74 → 102 | 24 → 26 |

Some of the rise in "simulated" comes from correcting stale rows, not from new model code. Ion-channel complement and bursting were listed as absent although rung 1 simulates them. Six new synapse rows count as simulated because the model uses a class-level or global value for them, for example a class STP value applied to every synapse of the class.

Slot counts and source shares per grain (a slot is one number a full model would hold; from `data/derived/ledger_levels.csv`):

| grain | slots before | slots after | after: measured | measured, unused | prior | mixed | guessed | absent |
|---|---|---|---|---|---|---|---|---|
| synapse | 359.4 M | 1,651.6 M | 0 % | 13.0 % | 10.9 % | 0 % | 49.0 % | 27.2 % |
| edge and cell pair | 12.48 M | 44.30 M | 14.1 % | 43.6 % | 14.1 % | 0 % | 28.2 % | 0 % |
| cell | 1.68 M | 4.77 M | 17.6 % | 3.5 % | 38.6 % | 0.5 % | 10.6 % | 29.1 % |
| type | 706 k | 879 k | 0 % | 0.1 % | 32.7 % | 24.5 % | 31.3 % | 9.8 % |
| class and neuropil | 58.0 k | 61.8 k | 0 % | 0 % | 46.4 % | 0 % | 48.4 % | 5.2 % |
| body part | 55,037 | 23,607 | 0 % | 0 % | 0.1 % | 14.0 % | 78.9 % | 1.0 % |
| organism and world | 48 | 72 | 2.8 % | 0 % | 6.9 % | 0 % | 48.6 % | 41.7 % |

Derived and rule shares are each under 6 % and omitted; the full table is in `runs/s12/blanks_audit.txt`.

The headline "data in the model" share falls from 1.90 % to 0.42 %. The model did not lose data. The denominator grew from 374.4 M to 1,701.7 M slots, nearly all at synapse grain: STP takes 3 numbers per synapse and receptor mix 4. Outside the synapse grain the ledger now counts 50.0 M slots (was 15.0 M), 14.1 % measured. The body-part total fell because about 50,000 glial-cell slots had been counted as body parts (a grain-mapping bug, below).

## Corrections to existing rows

- Ion-channel complement: `mech: none, fidelity none, absent` → N2, type, simulated, mixed (rung 1 built it in session 11).
- Intrinsic bursting or pacemaking: `none` → N2, type, default, guessed (rung 1 can burst; no cell is fitted to burst).
- Dendritic integration and synapse locations: owner → N30 (stub). Synapse ultrastructure and per-connection efficacy: `upgrade: N29`.
- Efferent control of sense organs → B24; cuticle elasticity → B26; heart, trachea → B27; reproductive system → S8 (all were `mech: none`).
- Two receptor-call fills (Davis 2020, Özel 2021) said `model: default` under rows with fidelity none. They now say `model: absent`. This removes the 4 rows the ledger flagged INCONSISTENT before the audit.
- Ledger bug: grain "glial cell" was not mapped and fell into "body part". Now mapped to cell. New grains mapped: circuit class, neuropil, glial territory → class; electrical pair → edge; sensory afferent → cell; sensillum → body part.
- No row has `mech: none` now. `tests/test_model_data.py` enforces it.

## New counts and their basis

| count | value | basis |
|---|---|---|
| weak connections (1-4 synapses, modelled cells) | 19,337,526 | measured: male-cns edge cache |
| synapses on weak connections | 34,311,400 | measured: male-cns edge cache |
| neuropils | 100 | inferred: 78 brain neuropils both sides (Ito et al. 2014 scheme) + about 22 VNC; not counted from the male-cns ROI hierarchy |
| glial territories | 2,785 | inferred: astrocyte-like glia taken as about 1/6 of glia, one territory each; order of magnitude only |
| mechanosensory sensilla | 5,781 (17,343 slots / 3) | derived: one sensillum per mechanosensory afferent in the census; chordotonal scolopidia hold 2-3, so this overcounts organs |
| sensory afferents, proprioceptors, GRNs | 17,896; 1,446; 1,423 (2,846 slots / 2) | measured: census classes |
| circuit classes | 70 | measured: `classes.csv` |

The genotype row says only "one male specimen" for male-cns. I did not check the genotype against the release paper, so the row does not name it.

## What the audit does not cover (known limits)

- Per-compartment channel distribution (dendrite vs axon densities) has no separate row. It sits under N30 with dendritic integration.
- Molecular state below the receptor (active-zone protein copy numbers, phosphorylation) is not enumerated. It enters through release probability and plastic state.
- Gut, fat body, Malpighian tubules and metabolism are covered only by the pre-existing coarse rows (S-mechanisms).
- Per-synapse counts use synapses on connections of 5 or more (89.85 M). The 34.3 M weak synapses have their own row, measured but unused.
- The synapse total is dominated by the `per` multipliers (STP 3, receptor mix 4). The numbers per synapse are my choice of a minimal description, not a measured quantity.

## What this enables

- FIDELITY_LADDER rungs 6 (N30), 7 (N33) and 8 (N29) now have inventory entries, switches and ledger slots. Building one means replacing the stub's refusal with code, behind the same switch.
- Every future fill has a row to land in. The ledger shows where the measured-but-unused data sits: synapse locations, polyadic structure, weak connections and cell volumes, 13 % of synapse slots and 44 % of edge slots.
