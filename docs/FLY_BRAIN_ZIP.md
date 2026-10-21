# fly_brain.zip: draft spec (fly2, 20 Oct 2026)

Draft for Ben and the Director. Nothing here is built yet. Today the model runs from the repo tree (`Organism(...)` reads `data/` by path). This page says what one file must hold so that the fly runs from it alone, and what is still missing.

**Goal (Ben, 20 Oct):** one file, `fly_brain.zip`, that is a complete functional emulation of a fly. Inferred values are part of it, labelled as inferred. "Complete" is measured with the instruments we already have: every blank-ledger row has a member in the zip with a label, and the zip carries its own tests and behaviour scoreboard.

## Contents

Sizes are measured on 20 Oct from the files the model reads today.

| member | holds | size now | label rule |
|---|---|---|---|
| `manifest.json` | zip schema version; git commit; sha256 of every member; dataset pins (male-cns v1.0; MANC and BANC extract hashes, as in `data/params/t1_fill.json`); runtime pins (Python 3.12, MuJoCo, flygym 2.1.0); default profile and seed | <1 MB | n/a |
| `connectome/neurons.parquet`, `annotations/*.parquet` | 167,111 neurons: type, class, side, neuromere, transmitter prediction, plus the hemilineage, ROI and photoreceptor tables | 5.1 + 6.7 MB | measured |
| `connectome/edges.parquet` | all 25.9M connections and 125.0M synapses (the model keeps ≥5 synapses: 6.29M edges, 90.3M synapses). The cut is a switch, not baked into the file | 95 MB | measured |
| `inferred/<name>.{csv.gz,json}` | graph transforms on top of the measured connectome, each with its rule, sources and hashes, and the switch that applies it. Today: T1 fill (`t1_fill`, inferred from MANC and BANC), CT1 column compartments, the gap-junction map. Later: development-inferred tables | 1.3 MB + small | inferred; never overwrites `connectome/` |
| `params/*.csv` | per-type, per-class and per-cell tables (transmitter physiology, receptor kinetics, STP, unitary PSPs, muscles, passive mechanics, sensor rates, ...) | 6.9 MB | per row: measured / derived / inferred / guessed / fitted, with source |
| `model/parameters.csv` | the parameter catalogue: 830 rows with unit, registry key, measured bounds (bio_min, bio_max), prior, basis, source, label | 2.8 MB (with the rest of `model/`) | per row |
| `model/mechanisms.yaml` | 72 mechanisms with tier, status, switch keys and neutral values. Tier A: 15 have, 16 partial, 2 absent. B: 3 / 9 / 2. C: 1 / 15 / 9 | in the above | n/a |
| `ledger/fly_information.yaml`, `ledger/blank_ledger.csv` | 145 measurable quantities, each mapped to a mechanism (basis: 15 measured, 6 derived, 21 inferred, 15 mixed, 53 guessed, 33 unknown, 2 absent) | 0.1 MB | n/a |
| `profiles/*.json` | each named parameter set (e.g. `m10f0`) as an explicit list of `KEY=value` with labels, not code | small | fitted or borrowed, marked |
| `body/` | flybody MJCF and meshes (ships in flygym 2.1.0 today; copy them in so the zip doesn't depend on a package version) | about 5 MB | measured geometry; masses and inertias as labelled in the registry |
| `code/flyemu/` | the simulator (LIF network, graded release, synapses, body coupling, senses, registry) | 1.5 MB | n/a |
| `tests/` | unit tests (38 files today), the neutral-switch identity tests, the gates with their expected outputs, and the scoreboard harness | <1 MB | n/a |
| `register.json` | the sealed / held-out data register (HANDOFF), so a reader can tell which evidence has been spent | small | n/a |

**Total today: about 125 MB**, most of it the edge table. Raw source data (`data/raw`, about 7.3 GB, 6.3 GB of it Azevedo 2020 video) stays out. The manifest cites it by hash.

**Per-synapse rung (N29, ladder rung 8):** 125M synapses × about 8 values (weight, release probability, STP U and time constants, receptor mix, latency) at float16 is about 2 GB if stored. The fitting rule says values are shared by type, class or development, so the zip stores the rule tables plus a seed and rebuilds the per-synapse values when it loads. Storing them explicitly is an export option, not the format.

## Entry point (to build)

    python -m flyemu.run fly_brain.zip --profile m10f0 --seed 12 --set KEY=V --ms 1000 --out run/

1. Check every member against its sha256 and refuse on any mismatch.
2. Build `Organism` from the zip members, not from repo paths.
3. Refuse any `--set` key that isn't in `mechanisms.yaml`. Absent stubs keep refusing non-neutral values, as they do now.
4. Write a run manifest: every registry read with its value, unit, label and source, plus the zip hash.

`python -m flyemu.check fly_brain.zip` runs `tests/` and the scoreboard, and prints the ledger fill fraction from the zip's own tables.

## How it maps onto the ledger and inventory

Each ledger row resolves through a chain: row → mechanism id (`mechanisms.yaml`) → switch keys and parameter ids (`parameters.csv`) → one zip member and its rows.

- **Completeness:** the zip is complete when all 145 rows resolve to a member and none resolves to an `absent` mechanism. Today 4 tier A/B mechanisms are absent (N30 compartments, S6 hemolymph ions, B24 efferent gain, B26 cuticle) and 9 tier C.
- **Fill fraction:** computed by `scripts/blank_ledger.py` run against the zip, so the number travels with the file.
- **Switches:** stay neutral (off or unity) inside the zip unless adopted. An adopted switch moves into the default profile with its gate, battery run and figure cited in the manifest.

## Tests that ship with it

1. Integrity: hashes, schema, and every ledger row resolving.
2. Neutral identity: every switch at neutral leaves the model unchanged (as `test_t1_fill.py`, `test_stubs.py`).
3. Unit tests: the existing suite.
4. The fixed behaviour scoreboard: stands, walks, grooms, PER (labellar and leg sugar), optomotor turning, giant-fibre escape, stable flight. About 1 of 7 passes today (labellar sugar), so it is reported, not asserted.
5. Physiology gates: the pre-registered checks with their held-out data named, so a new value can't be scored on data it was fitted to.

## Open questions for Ben

- Should the zip pin the code (fully self-contained) or only data plus a code version? The draft above pins the code.
- MANC and BANC derived tables are inside (inferred members). The zip is internal; nothing here publishes it.
- Explicit per-synapse values: an export option only (draft), or the default once N29 is built?
