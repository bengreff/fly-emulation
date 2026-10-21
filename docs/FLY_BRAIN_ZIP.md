# fly_brain.zip and scan files: draft spec (fly2, 20 Oct 2026; rev 2)

Draft for Ben and the Director. Nothing here is built yet. Today the model runs from the repo tree (`Organism(...)` reads `data/` by path). This page says what one file must hold so that the fly runs from it alone, and how a second file type, the scan file, lets the reconstruction study in `docs/FIDELITY_LADDER.md` run as a clean pipeline.

**Goal (Ben, 20 Oct):** one file, `fly_brain.zip`, that is a complete functional emulation of a fly: **brain + body + world** (standard arenas and stimuli) behind one entry point. Inferred values are part of it, labelled as inferred. "Complete" is measured with the instruments we already have: every blank-ledger row has a member in the zip with a label, and the zip carries its own tests and behaviour scoreboard.

## Two layers and one address space

The reconstruction study needs a fly whose every value is known, so the zip separates two layers:
- **Species layer:** rules, per-type tables and distributions (what we fit or infer for "some fly of this species"). The zip we have today is species-layer only. Per-cell and per-synapse values are rebuilt from rules at load.
- **Individual layer:** the realised value of every per-cell and per-synapse slot for one fly, drawn from the variation model with a recorded seed. A **complete possible fly** is a species layer plus a fully realised individual layer. It is synthetic and labelled so, never a claim about a real fly.

Every quantity has one **slot address**, the registry's `entity|property` key extended to single elements:
- `cell_type:DNg100|v_thresh` for a type;
- `cell:<bodyId>|v_rest` for a cell;
- `synapse:<pre>-><post>|release_prob` for a connection;
- `body:lf_tibia|mass` for the body.

The ledger, the parameter catalogue, the run manifest and the scan file all use these addresses. That is what lets a scan hold any subset.

## Contents of fly_brain.zip

Sizes are measured on 20 Oct from the files the model reads today.

| member | holds | size now | label rule |
|---|---|---|---|
| `manifest.json` | zip schema version; layer (`species` or `individual`); git commit; sha256 of every member; dataset pins (male-cns v1.0; MANC and BANC extract hashes, as in `data/params/t1_fill.json`); runtime pins (Python 3.12, MuJoCo, numpy, scipy, pandas, pyarrow, numba, ...; flygym is vendored, so its version is recorded, not pinned); default profile and seed; for an individual, its parent species zip hash and variation seed | <1 MB | n/a |
| `connectome/neurons.parquet`, `annotations/*.parquet` | 167,111 neurons: type, class, side, neuromere, transmitter prediction, plus the hemilineage, ROI and photoreceptor tables | 5.1 + 6.7 MB | measured |
| `connectome/edges.parquet` | all 25.9M connections and 125.0M synapses (the model keeps ≥5 synapses: 6.29M edges, 90.3M synapses). The cut is a switch, not baked into the file | 95 MB | measured |
| `inferred/<name>.{csv.gz,json}` | graph transforms on the measured connectome, each with its rule, sources, hashes and switch. Today: T1 fill and T1 added connections (`t1_fill`, `t1_add`; from MANC and BANC), CT1 column compartments, the gap-junction map. Later: development-inferred tables | 1.5 MB + small | inferred; never overwrites `connectome/` |
| `params/*.csv` | per-type, per-class and per-cell tables (transmitter physiology, receptor kinetics, STP, unitary PSPs, muscles, passive mechanics, sensor rates, ...) | 6.9 MB | per row: measured / derived / inferred / guessed / fitted, with source |
| `model/parameters.csv`, `model/mechanisms.yaml` | 830 parameter rows with unit, registry key, measured bounds, prior, basis and source. 72 mechanisms with tier, status, switch keys and neutral values (tier A: 15 have, 16 partial, 2 absent; B: 3 / 9 / 2; C: 1 / 15 / 9) | 2.8 MB | per row |
| `variation/*.csv` | the variation model: per slot class, the between-fly spread (left vs right homologues, male-cns vs FAFB vs MANC/BANC, per-type spread) | to build | inferred |
| `individual/*.parquet` | individual layer only: realised per-cell and per-synapse values by slot address | per-synapse at about 8 values in float16: about 2 GB; per-cell only: about 10 MB | synthetic, drawn (seed in manifest) |
| `ledger/` | 145 measurable quantities, each mapped to a mechanism (basis: 15 measured, 6 derived, 21 inferred, 15 mixed, 53 guessed, 33 unknown, 2 absent) | 0.1 MB | n/a |
| `profiles/*.json` | each named parameter set (e.g. `m10f0`) as an explicit list of `KEY=value` with labels, not code | small | fitted or borrowed, marked |
| `body/` | the flygym 2.1.0 package (pure Python, Apache-2.0, with its MJCF-side tables) and the 85 fullsize flybody meshes, copied in so the zip doesn't depend on a package version or a download cache | 145 MB unpacked (measured 21 Oct; the 5 MB estimate left out the fullsize meshes) | measured geometry; masses and inertias as in the registry |
| `world/arenas/*.xml`, `world/stimuli/*.yaml` | **standard arenas:** flat floor, air-supported ball, flight tether, sugar patch. **Stimuli as data, not code:** full-field flash, moving grating, looming disc, labellar and leg sugar, bitter, odour pulse, DN or MN current injection. Each stimulus is a declarative schedule (onset, duration, amplitude, geometry) that the entry point plays into the sensory models. Today these live in `scripts/probes/*` and flygym's arenas. **Built 21 Oct:** `flat_floor.json` (the `World()` defaults) and `none.json`; the rest are declared TODO entries in the manifest, not files | small | the stimulus is a protocol, not a fly quantity |
| `code/flyemu/` | the simulator (LIF network, graded release, synapses, body coupling, senses, registry) | 1.5 MB | n/a |
| `tests/` | unit tests (38 files today), the neutral-switch identity tests, the gates with expected outputs, the scoreboard harness | <1 MB | n/a |
| `register.json` | the sealed / held-out data register (HANDOFF), so a reader can tell which evidence has been spent | small | n/a |

**Measured 21 Oct (first build): 134.7 MB zipped, 271.4 MB unpacked, 467 members** (species layer): edges 102 MB, body 145 MB unpacked (mostly meshes, which compress well). A complete possible fly with explicit per-synapse values adds about 2 GB. Raw source data (`data/raw`, about 7.3 GB) stays out; the manifest cites it by hash.

**Neuron fidelity (Ben, 20 Oct):** two-compartment neurons are approved where a point model provably fails, PSI→DLMn first (F-GJ-5: measured 4.71 mV PSP, DLMn silent in 0 of 20 escapes). Compartment parameters are per-cell slots like any other (`cell:<bodyId>|n_compartments`, coupling and dendrite values), so they need no new member.

## Entry point (built 21 Oct: `src/flyemu/run.py`; packer `src/flyemu/pack.py`)

    python -m flyemu.run fly_brain.zip --world ball --stimulus grating_ccw --profile m10f0 --seed 12 --set KEY=V --ms 1000 --out run/

1. Check every member against its sha256 and refuse on any mismatch.
2. Build `Organism` from the zip members, not from repo paths. An individual zip uses its realised values; a species zip draws nothing and uses the rules.
3. Load the arena and stimulus from `world/`. A stimulus reaches the brain only through the sensory models; no world state bypasses them.
4. Refuse any `--set` key that isn't in `mechanisms.yaml`. Absent stubs keep refusing non-neutral values.
5. Write a run manifest: every registry read with its value, unit, label and source, plus the zip hash.

**How the first build does it (21 Oct).**

    .venv/bin/python -m flyemu.pack --out fly_brain.zip          # refuses a dirty tree
    PYTHONPATH=fly_brain.zip/code python -m flyemu.run fly_brain.zip --ms 1000 --out run/ [--deny <repo>]
    python -m flyemu.run --tree . --ms 1000 --out run_tree/      # the same run from the repo, for comparison

- Every member has two names: its spec path (`connectome/edges.parquet`) and the path the code reads
  (`data/cache/male_cns_edges.parquet`). The runner verifies every hash, extracts each member to its runtime
  path under a fresh root, and runs the unchanged code there in a child process. The launcher is stdlib only
  and imports straight from the zip.
- Members come from git-tracked files only (plus the external caches: the connectome extract, the CT1 column
  files, the flybody meshes), so an untracked scratch file cannot leak in. The packer refuses if the neuron or
  edge file differs from the hashes pinned in `t1_fill.json`. The zip is deterministic: fixed member dates,
  sorted members, no clock time in the manifest.
- flygym is vendored. Its asset paths are bound at import time (module constants and default arguments), so
  they cannot be pointed at the zip after import; shipping the package is the only clean way.
- In the child, a read guard (Python audit hooks, plus path checks on pyarrow's parquet reader and MuJoCo's
  mesh loader) refuses reads under `--deny` roots, the installed flygym and its mesh cache, and records any
  other file opened outside the root and the Python install. `run_manifest.json` lists them.
- `--set KEY=V` is refused unless `parameters.csv`, `structural_keys.csv` or a mechanism's switch list owns the
  key. Unbuilt worlds and stimuli are refused by name.
- Outputs: `run_manifest.json` (zip and manifest hash, settings, runtime, body source, read-guard report,
  registry summary, result with `spikes_sha256` and `final_qpos_sha256`), `spikes.npz`, `registry_reads.csv`.
- Not built yet: `flyemu.check`, `variation/`, `individual/`, slot addresses, and every world item except the
  flat floor and the null stimulus. All are listed under `todo` in the manifest.

`python -m flyemu.check fly_brain.zip` runs `tests/` and the scoreboard, and prints the ledger fill fraction from the zip's own tables.

## Scan files

A **scan file** (`*.flyscan`, also a zip) holds any subset of a fly zip's quantities, as an instrument would have measured them.

| member | holds |
|---|---|
| `manifest.json` | the scanner spec hash, the scan seed, the source zip's hash **and nothing else from it**, the list of modalities included |
| `observations/<modality>.parquet` | one row per observed slot: `address, value, sd, modality`. Absent rows mean "not observed", never zero |
| `scanner.yaml` | the scanner spec that made it: per modality, which slot classes it observes and its noise model |

**Modalities and noise models** (each one a scanner-spec entry, each with a cited error rate where one exists):
- **EM connectome:**
  - Morphology and cell identity, with merge and split error rates.
  - Synapse counts per connection: a false-negative and false-positive rate per synapse, applied as binomial thinning plus Poisson additions. The male-cns T1 deficit (F-XCONN-1) is the field example of a region-dependent false-negative rate.
  - Transmitter prediction: the classifier's confusion matrix.
  - Cell typing: a mislabel rate.
- **Transcriptome per cell or per type:** channel and receptor mRNA with dropout and a count-noise model.
- **k recorded cells:** membrane values (Rin, τm, threshold, rest) with patch-clamp error.
- **Behaviour logs:** scoreboard outputs with trial-to-trial noise.

Synapse weights can be dropped, coarsened to type means, or kept, as separate modality settings.

## The pipeline: zip → scan → reconstructed zip → comparison

    python -m flyemu.scan       truth.zip  --scanner em_only.yaml --seed 3 --out s.flyscan
    python -m flyemu.reconstruct s.flyscan --species species.zip  --out recon.zip
    python -m flyemu.compare    truth.zip recon.zip --siblings sib1.zip sib2.zip --battery battery.yaml --out cmp/

- **scan** reads only the truth zip and the scanner spec. Separate code path and separate seed from reconstruction, as the ladder requires.
- **reconstruct** reads only the scan file and a species-layer zip (rules and priors, no individual layer). It runs the project's own construction pipeline: rules, transcriptome inference, bounded search. Every slot it fills from the scan is labelled `scanned`; every slot it fills from the species layer is labelled `prior`. It refuses an input whose manifest is an individual zip or whose hash appears in the scan's source field (leak guard).
- **compare** runs the same battery (arenas, stimuli and internal states from `world/`) on truth, reconstruction and siblings. It reports behaviour and physiology distances, and whether recon→truth is closer than sibling↔sibling (the ladder's identity criterion).
- **The study** sweeps scanner specs (connectome alone; plus types; plus transcriptomes; plus k cells; weights dropped or coarsened) and plots information supplied against identity recovered.
- **Pre-register** the battery and the identity criterion before the first comparison.

## How it maps onto the ledger and inventory

Each ledger row resolves through a chain: row → mechanism id (`mechanisms.yaml`) → switch keys and parameter ids (`parameters.csv`) → slot addresses → one zip member and its rows.

- **Completeness:** the zip is complete when all 145 rows resolve to a member and none resolves to an `absent` mechanism. Today 4 tier A/B mechanisms are absent (N30 compartments, S6 hemolymph ions, B24 efferent gain, B26 cuticle) and 9 tier C.
- **Fill fraction:** computed by `scripts/blank_ledger.py` run against the zip, so the number travels with the file. For a reconstruction, the same count split into `scanned` and `prior` gives the x-axis of the study's curve.
- **Switches:** stay neutral inside the zip unless adopted. An adopted switch moves into the default profile with its gate, battery run and figure cited in the manifest.

## Tests that ship with it

1. Integrity: hashes, schema, and every ledger row resolving.
2. Neutral identity: every switch at neutral leaves the model unchanged (as `test_t1_fill.py`, `test_stubs.py`).
3. Unit tests: the existing suite.
4. The fixed behaviour scoreboard: stands, walks, grooms, PER (labellar and leg sugar), optomotor turning, giant-fibre escape, stable flight. About 1 of 7 passes today (labellar sugar), so it is reported, not asserted.
5. Physiology gates: the pre-registered checks with their held-out data named.
6. **Pipeline round trips:**
   - A noiseless full scan must reconstruct the truth exactly, slot for slot.
   - An empty scan must reconstruct the species zip.
   - A scan must contain no value the scanner spec doesn't list.

## Open questions for Ben

- Should the zip pin the code (fully self-contained) or only data plus a code version? The draft pins the code.
- Explicit per-synapse values in a species zip: an export option only (draft), or the default once N29 is built? An individual zip needs them explicit (about 2 GB) unless the variation model is generative from a seed. The draft stores them, so a truth fly can't drift with code changes.
- The variation model is the study's main prerequisite and is still unbuilt. Its first source would be left-right homologue and cross-connectome spread (male-cns, FAFB, MANC, BANC).
