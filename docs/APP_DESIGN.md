# Fly workbench: design

**Status:** design written 4 October 2026, 16:45 CDT; Ben's answers recorded and milestone 1 (M1)
built at 17:20 CDT the same day, milestone 2 (M2: protocols, labelled optogenetics, replay of
interventions, a scored library) by 18:10 CDT, and M2b (the app checked against the model's own
sugar assay, live sessions, the protocol editor, a sham distribution) in the evening (section 14
says what each contains, with the results; `app/README.md` says how to run it). Owner: the app worker (branch `app`). The model is owned by the fly worker; the app reads it
only through public functions and asks for new ones (section 13, on hold).

**State at 03:01 CDT, 6 October 2026 (M3, the graded-medulla run, the T4/T5 direction test for the
fly worker and M4 are done; nothing of mine is running on either machine):**

- **Parked early** (Director's usage note, 02:55: park by 03:45). On backhouse nothing of mine
  runs: no `flyapp-*` tmux session and no recorder. `~/flyapp` holds the code at d63adbb (a
  `git archive` copy), `runs/app/t4t5/` (both validation sets, also copied to the Mac) and
  `runs/app/replay/t4t5-m9r-control-merged`, with the scripts `bh_t4t5.sh` and `bh_replay.sh`.
  The other tmux sessions there (crucible_*, s12vis_*) belong to other projects. A process listed
  as `tmux new-session -d -s flyapp-graded ...` (PID 93713) is the shared tmux server, which
  keeps the command line that started it at 01:44; it hosts those sessions and must not be
  killed.
- **Since 02:05:**
  - **The T4/T5 direction test** (section 13.1; validation in section 14): one command,
    `app/tools/t4t5_ds.py --profile <rung> [--model-root <checkout>]`, records 17 runs and reports
    per T4/T5 subtype whether the cells respond and prefer the fly's direction. It reproduces the
    graded-medulla runs spike for spike. Baselines (measured): m9r with the graded-medulla rows
    responds to medulla bars but 0 of 8 subtypes are selective; plain m9r gives no response in
    either set, since its medulla inputs spike and the bars leave them below threshold. A
    paragraph for the fly worker's HANDOFF is in section 13.1.
  - **M4** (section 14): the Fidelity tab (the model's construction tables, this run's values by
    evidence, bounds, ledger, mechanisms, profiles) and run configuration (profile, body, scan,
    switches) sent to the Session tab; the protocol check refuses unknown profiles, bodies, scans
    and override keys and reports the status the run will be recorded with; a named profile with
    overrides is now labelled custom. Screenshot `docs/media/app_fidelity.png`.
  - **Request 10** to the fly worker: quote the comma-containing flow text in
    `data/model/mechanisms.yaml`.
  - **`main` merged** (81e7afa, at f7e4490): its working profile is now m9c (m9r plus a clock
    drive). The Fidelity tables were rebuilt from it (72 mechanisms, 685 unknowns, 105 structural
    rows, 23 profiles), and the configure form lists the 75 switch keys, including the fly
    worker's new `release_at_rest` and `mode_from_recordings`. Tests that named m9r as the working
    profile now follow the model's own setting. Replay check (measured): the plain m9r T4/T5
    control, recorded at a73e966, replayed on backhouse at the merged d63adbb
    (`runs/app/replay/t4t5-m9r-control-merged` there) is identical in all 31 arrays (106,287
    spikes), so `main`'s new switches leave m9r unchanged at their defaults. The replay is
    labelled "custom, not validated", since m9r is no longer the working profile.

- **Done and pushed** (branch `app`; 188 tests pass).
  - **The model's sugar to MN9 assay** (`scripts/assay_pathways.py`, m9) is reproduced by the app.
    - On seeds 0 to 2, every cell's spike count matches the model's own run.
    - Over seeds 0 to 9 both give 5.7 ± 1.4 Hz; the app's own kick draws give 5.8 ± 2.1 Hz
      (measured; M2b in section 14).
  - **Shams:** 17 recorded at seed 12, 13 distinct, plus one per seed in the 10-seed library.
  - **Built:** the live session and the protocol editor (M2b); the Eye tab, with the inspector
    link and the photoreceptor assignment check (M3, first part).
  - **The noise rule for the 10-seed mean,** declared at 02:10 CDT before any of its runs: a
    paired sign-flip test against each seed's sham (section 14, "10-seed library").
  - **Tooling for backhouse:** `run_library.py --parallel N`; in a copy without `.git`,
    `record.py` takes the commit from `FLYAPP_COMMIT`, labelled as declared.
- **The 10-seed m9 library is complete** (section 14, "10-seed library: results").
  - **Runs:** 66, all exit 0. Mac: seeds 0 to 5 of the five informative protocols (30, 190 to
    240 s each). Backhouse: all six protocols at seeds 6 to 9, and the control and leg sugar at
    seeds 0 to 5 (36, 8 at a time, about 330 s each, finished 04:29 CDT).
  - **Folders on the Mac:** `runs/app/lib-m9-seeds` holds seeds 0 to 9 of the five informative
    protocols (the backhouse seeds 6 to 9 were copied in). `runs/app/lib-m9-seeds-bh` is the
    backhouse folder as collected, and is where leg sugar is scored. The stopped Mac run
    `control-s6.incomplete-20261005-0354` stays in the first folder; the scorer skips it.
  - **Result on the mean of 10 seeds** (derived): sugar GRN to MN9 +8.8 Hz (SD 2.2), PASS,
    p = 0.001 against the shams. MDN -0.015 mm and DNa02 -0.30 deg, FAIL, both within noise
    (p = 0.66 and 0.53). Leg sugar changes no spike at any seed. All four match the expectations
    written before the runs.
  - **Mac against backhouse:** the same control at the same seed runs identically for 244 to
    972 ms, then drifts apart; at 2 of 6 seeds before the stimulus. Each seed must stay on one
    machine.
- **Ben's decision (Director, 05:05):** keep m9 for this round, since it matched the fly worker's
  assay and was already partly recorded. Next round, record the fly worker's current working
  profile, m9r, as a second library, so the app can compare models side by side.
- **Decided (Director, after 05:08; go at 21:30):** record m9r as named, with no override.
- **The fold (Director, 22:05):** the fly worker folded `motor_unit:all|force_per_spike` = 10
  (guessed) into m9r at `main` 019dae2, so the name means the gated model. The Director ordered a
  restart on the folded m9r: one name, one model.
- **Done tonight:**
  - `main` merged into `app` twice: afb666c at 21:28, then aed81a6 (which includes 019dae2) at
    22:00. No file overlaps either time, and 144 app tests pass.
  - `run_library.py --profile/--set` passes a model to every recording. `record.py` notes what
    the command line changed (`launched_with`, and a suffix on the title), so an m9 protocol run
    as m9r is not labelled m9.
  - `record.py` now writes the profile's values and statuses, as defined at the run's commit,
    into each manifest (`profile_values`). A library then stays readable if a name changes
    meaning again.
  - **30 ms check, folded m9r, seed 3, commit 4723e1b on both machines (measured):** the Mac and
    backhouse give identical spike trains (292 spikes, no divergence) and identical body
    positions. Both manifests record force_per_spike 10 (guessed) among m9r's 67 values. Peak
    memory 2.9 GB on backhouse.
  - **The pre-fold attempt was stopped** at 21:59, cleanly: the runner, its 5 in-flight
    recordings and the tmux session. Its outputs were moved, not deleted, to
    `~/flyapp/runs/app/lib-m9r-prefold-afb666c` on backhouse, with a `NOTE.txt`. That folder holds
    25 complete runs (all six protocols at seeds 0 to 3, plus control-s4) and 5 stopped ones. In
    those runs, 71 leg motor units used the old shared value, 1. The planned
    `lib-m9r-f10-seeds` library was dropped, since folded m9r is the same model.
- **The m9r library is complete** (section 14, "m9r library: results").
  - **Runs:** 60, all exit 0, on backhouse from 22:01 to 22:57 CDT (`~/flyapp/bh_m9r.sh`, 6 at a
    time, code a `git archive` of 4723e1b). Collected to the Mac at 00:45 as
    `runs/app/lib-m9r-seeds`. The pre-fold folder was also copied, as
    `runs/app/lib-m9r-prefold-afb666c`, for the fold check.
  - **Result on the mean of 10 seeds** (derived): sugar GRN to MN9 +11.1 Hz (SD 1.8), PASS,
    p = 0.001, 10 of 10 seeds (m9: +8.8 Hz). DNa02 +0.61 deg: left at all 10 seeds and beyond
    noise (p = 0.001), but an eighth of the 5 deg threshold, so FAIL (m9: within noise). MDN
    +0.004 mm, within noise. Leg sugar changes no spike.
  - **m9r is quieter:** a one-cell kick changes about 300 cells against m9's 2,200 (medians), and
    the resting body moves less.
  - **The fold changed nothing here** (measured): the pre-fold and folded runs are byte-identical.
  - **Nothing of mine is running.** The tmux session `flyapp-m9r` ended with the runner, and no
    keepalive is left on the Mac. The other tmux sessions on backhouse (crucible_*, s12*) belong to
    other projects.
- **The Compare tab has a model selector** (section 14, "Compare tab: models side by side";
  screenshot `docs/media/app_compare_m9r_vs_m9.png`). It reads the scores from each library and
  what differs between the models from the runs' registry inventories: 7 values differ, 35 are
  only in m9r's build and 3 only in m9's.
- **M3 is done** (section 14, "M3, second part"; screenshots `docs/media/app_eye_columns.png` and
  `docs/media/app_eye_traces.png`). The Eye tab has the column table, placed by connectivity
  (derived), and the motion-sensing traces. A watched control run (measured) shows the light
  signal reaching the photoreceptors and L1 to L3 and stopping at the first spiking stage of the
  medulla. T4 and T5 do not move, and the tangential cells carry only an internal rhythm through
  one inhibitory cell, Am1.
- **The discriminating run is done** (section 14, "The discriminating run: graded medulla").
  With the medulla cells that flies' recordings show as graded made graded, as a labelled variant
  (measured cell list, 14 runs at seed 0): T4 respond to ON bars and T5 to OFF bars, locally,
  with peaks of 1.2 to 2.0 mV, but neither is direction-selective (|DSI| at most 0.02 on the
  peak). Untouched, the model passes no light signal past L1-L3, because its graded rule
  transmits nothing at or below rest. Three notes for the fly worker (section 13, requests 7 to 9).
- **Next step: M5** (other scans' atlases and the cross-specimen comparison; section 6.1). The
  T4/T5 temporal-dynamics follow-up is the fly worker's (Director, 6 October); the app runs the
  test when asked. Exact steps, checked against the local data at 03:05 on 6 October:
  1. **Fix section 6.1's table first.** The male-cns cache (`data/cache/male_cns_neurons.parquet`,
     26 columns) holds `mancBodyid` but not `flywireType` or `hemibrainType`. The crosswalk hub
     is BANC instead: `data/raw/banc/banc_888_meta.feather` (188,508 cells, 81 columns) has
     `fafb_`, `manc_`, `malecns_`, `hemibrain_` and `fanc_` `cell_type` and `_match` columns, and
     separate `_nblast_match` columns; reviewed match tables sit beside it
     (`banc_malecns_reviewed_matches.csv.gz`, `banc_manc_reviewed_matches.csv.gz`).
  2. **BANC atlas.** Give `app/build/atlas.py` a `--scan banc` path writing
     `app/data/atlas/banc-888/` in the same flyemu-atlas/1 format, from the feather's
     `position`/`root_position_nm`, `super_class`, `cell_class`, `cell_type`, `side` and `flow`.
     Check the coordinate frame and units before drawing; there are no edges, so the atlas is
     cells only, with `input_connections` and `output_connections` as counts.
  3. **Crosswalk build** (`app/build/crosswalk.py`, new): per male-cns type, the matched cells in
     BANC from the reviewed table (derived: a published match), and in FAFB, hemibrain and MANC
     through BANC's match columns (inferred: two hops). NBLAST-only matches kept apart and
     labelled inferred. MANC also directly via `mancBodyid` (derived); report where the two
     MANC routes disagree.
  4. **Compare view:** a type's cell count in each scan, side by side, with the join basis on
     every number; the atlas selector in the Brain tab gets the BANC atlas. Partner overlap and
     synapse-count spread wait for edges (BANC edges are not local; download size to be checked,
     not assumed).
  5. **Tests:** atlas counts against the feather; every crosswalk row has a basis; no row joins
     a cell to two types in the same scan without a flag.
- **Blocked:**
  - MDN and DNa02 cannot pass until the body walks. m9r's fly lies down at rest (`main`'s
    handoff, F-STAND-3).
  - Warm starts and branching wait on model request 2 (section 13, on hold).

## 1. What it is for

Ben, 2026-10-04: a public viewer "fully fleshed out instead of just a cartoon viewer, brain map and
interaction mechanisms etc, to replace our current viewer ... a research tool in itself where you can
select and mix and match bodies and brain scans and levels of fidelity". Also a fly's-eye view and
virtual optogenetics. Standing rules: a local web page or standalone app (not a Claude artifact);
behaviour realism over pretty graphics; public on GitHub with a static replay mode for GitHub Pages.

Ben's answers (4 October 2026, section 16) set the direction:

- **A research tool first**, dense and labelled, rather than a showcase.
- **An installable local app**, Mac first, with backhouse (GPU) for long runs. It downloads
  connectome data on demand; it offers a library of long precomputed recordings ("minutes of fly
  behaviour that took days to compute") and shareable run configurations, so a user can download a
  config and run their own test in an arbitrary simulated environment. A browser-only lite
  simulation is not a goal now.
- **Everything switchable** on the brain map, and every value carries its **layer**: measured from
  the scan, inferred by a rule, or completed by search. Layers can be toggled, and alternative
  completions (other seeds or ensemble members) can be selected, because "our ending complete brain
  that we build will not be the only possible one" (section 5.1).
- **Scans:** male CNS and FlyWire (FAFB) at least; comparison across scans now, simulation on other
  scans when the model supports it.
- **Failures are shown, labelled.** Honesty over showcase.
- **Order:** the intervention mechanism next (M2), then the fly's-eye view (M3).

Design principles, in priority order:

1. **Show the model, not a picture of it.** Every pixel comes from a recorded or running simulation,
   or from a dataset with a named version. Geometry is the compiled MuJoCo model (as now); eye images
   are the ommatidia values the network actually received; the brain map is the connectome's own
   coordinates.
2. **One format, one player.** A live session is a recording that is still growing. Static replay,
   local live runs and backhouse batch runs all write and read the same format.
3. **Provenance on screen.** Each view states its configuration (scan, body, profile, overrides,
   seed), its evidence labels and its caveats. Caveats are generated from the recording, never
   hard-coded (the current viewer's caveat text is stale; section 2).
4. **Interventions are experiments.** Every activation or silencing is a logged protocol with
   resolved target cells, so a click in the app is reproducible from the command line and can be
   cited in DECISIONS.
5. **Respect the validation discipline.** Interventions on the held-out register are marked and
   logged when run (section 7.4).
6. **Runs on the 16 GB Mac.** Live simulation is one organism at a time through the slot limiter;
   the browser stays under 1 GB.

## 2. What exists now

| Piece | What it does | Keep | Problem |
|---|---|---|---|
| `viz/index.html` (single file, three.js r128 from a CDN) | 3D body from the compiled geometry, tarsal load tint, follow camera; motor-neuron raster split into "reach a muscle" and "drive nothing"; joint-torque heat map with clipping marked white; whole-CNS rate trace | body rendering, the mapped/unmapped raster split, clipping disclosure, transport controls | no brain map, no neuron identity, no interaction; caveats hard-coded and now wrong ("every neuron shares one membrane time constant", "male-cns:v1.0 → NeuroMechFly" while the default body is flybody, "176,422 neurons" while the model runs 167,111 under its status policy: neurons whose status is Traced or that carry a type, with edges of at least 5 synapses) |
| `scripts/serve_viz.py` | serves the page plus one run's `replay_data.js` on 127.0.0.1 | the idea (no build step, localhost only) | one recording at a time; data as base64 inside a JS file (+33 % size, whole file parsed at once) |
| `scripts/record_organism.py` | runs the closed loop; writes `recording.npz` (full-rate qpos) and `replay_data.js` (200 Hz poses, torque, contact, MN spikes, whole-CNS rate) | the run loop shape | records motor-neuron spikes only, not the other ~166,000 cells; no eye, no stimuli, no voltages |
| `scripts/export_geometry.py` | compiled MuJoCo meshes to `viz/geometry.{bin,json}` (flybody: 272,550 triangles, 85 geoms, 13 MB, measured) | yes, generalised per body | written next to the page, one body only |
| `scripts/render_brain_body.py` | the m9 MP4 (`docs/media/m9_closed_loop.mp4`): body beside five class rate traces | as a video exporter | classes only; offline |

The twelve recordings in `runs/organism-record-*` (counted 4 October) predate m9;
`app/build/convert_legacy.py` keeps them viewable (M1).

## 3. Architecture

```
            build time (Mac, once per dataset/body)              run time
 ┌───────────────────────────────────────────────┐   ┌──────────────────────────────────────────┐
 │ app/build/atlas.py  connectome cache -> atlas/1│   │ app/server/serve.py  (localhost only)     │
 │ app/build/body.py   compiled MuJoCo -> body/1  │   │   static files + /api (catalog, sessions) │
 │ app/build/convert_legacy.py  replay_data.js    │   │   session = one worker process holding    │
 │                              -> rec/1          │   │   an Organism, behind the slot limiter;   │
 │ app/build/site.py   static bundle for Pages    │   │   writes rec/1 chunks as it steps         │
 └───────────────────────────────────────────────┘   │ app/server/run_protocol.py  headless batch │
                                                      │   (Mac or backhouse): protocol/1 -> rec/1  │
                                                      └──────────────────────────────────────────┘
                         app/web/  (static ES modules, vendored three.js, no bundler)
          body 3D | brain map | fly's eye | traces | inspector | protocol editor | provenance
```

**What runs where:**

| Capability | Static (GitHub Pages) | Local Mac | backhouse |
|---|---|---|---|
| Replay, brain map, inspector, scan comparison | yes | yes | n/a |
| Recordings | a curated gallery | every run under `runs/app/` | produced, synced to the Mac |
| Live session (step, pause, stimulate, branch) | no | yes, one at a time, about 100 s of wall time per simulated second at m9 (measured, section 10) | yes over an SSH tunnel (cost not measured) |
| Batch protocols, many flies | no | through the slot limiter | GPU brain, CPU bodies (`scripts/gpu_closed_loop.py` pattern) |
| Interventions | a precomputed library, labelled as such | any protocol | any protocol |

Engineering choices (mine, reversible): plain ES modules with a vendored three.js (MIT) and no
bundler, so the site runs from `python -m http.server` and deploys to Pages unchanged; Python
stdlib HTTP plus `websockets` (already in the venv) for the live API; binary arrays fetched with
`fetch()` and gunzipped in the browser with `DecompressionStream`. All app code lives under `app/`;
built data under `app/data/` (git-ignored). Nothing under `src/flyemu`, `data/model` or the fly
worker's docs is edited.

## 4. Data formats

All formats carry a `format` string with a version, units in field names or metadata, and a
`provenance` block (git SHA, dataset versions, command). Arrays are little-endian, stored as
`.bin.gz` files described by a JSON manifest (name, dtype, shape, units, file, byte offset).

### 4.1 Recording, `flyemu-rec/1`

```
runs/app/<run_id>/
  manifest.json          config, streams, chunk list, stimuli, generated caveats, provenance
  rows.bin.gz            model row -> bodyId (int64): joins every stream to the atlas
  inventory_summary.json evidence-label counts by subsystem, from the run's inventory.csv
  chunks/<k>.bin.gz      one file per 250 ms of simulated time; a live run appends chunks
```

Streams (sizes inferred from the m9 run shape, to be measured in M1):

| Stream | Content | Rate | Approx. raw size |
|---|---|---|---|
| `body.xpos`, `body.xquat` | world pose of each MuJoCo body (70 bodies) | 200 Hz | 0.4 MB/s |
| `spikes` | **every neuron's spikes**: CSR by 1 ms bin (`ptr` uint32, `row` uint32, `sub` uint8 = step within the bin), so exact step times survive | event | ~1.7 MB/s at 2 Hz mean (inferred) |
| `v.watch` | membrane potential of watched cells (selected in the protocol, ≤ 2,000) | 1 kHz | 8 MB/s per 1,000 cells |
| `motor.torque`, `contact` | actuator command per DOF, contact force per tarsal site | 200 Hz | 0.1 MB/s |
| `eye.readout` | ommatidia values, 2 eyes x 721 x 2 spectral channels, uint8 | 100 Hz (the model's eye rate) | 0.3 MB/s |
| `state` | internal state (organs, modulator pools) when the profile has them | 100 Hz | small |
| `stim` | applied stimuli with exact on/off steps and resolved target rows | event | small |

A 10 s recording is about 15 to 25 MB gzipped (inferred). Graded cells do not spike; their output is
in `v.watch` only if watched (stated in the caveats).

### 4.2 Atlas, `flyemu-atlas/1` (one per scan and version)

```
app/data/atlas/<scan>-<version>/
  neurons.bin.gz     bodyId, position (µm, float32 x3), position basis code, type, class,
                     superclass, side, transmitter, flags; ~4 MB gzipped for male-cns (inferred)
  vocab.json         names for every coded column; per-type counts
  neuropils.json + neuropils/<roi>.bin.gz    decimated region meshes
  edges/<shard>.bin.gz   per-neuron in and out partners with synapse counts, sharded by bodyId
                         (male-cns, edges ≥ 5 synapses: 6.24 M edges, measured; ~75 MB over 512 shards, inferred)
  types.bin.gz       type x type connectivity (synapses, sparse)
  crosswalk.json     type and cell matches to other scans, with the source of each match
```

### 4.3 Body, `flyemu-body/1` (one per body model)

The compiled MuJoCo geometry (as `export_geometry.py`, decimated for the web), body names and
parents, actuator and joint names, contact sites, the motor-neuron to actuator map, and the eye
layout (flygym `Retina.ommatidia_id_map` plus each ommatidium's viewing direction). Recordings bind
poses to bodies by name, as the current viewer already does.

### 4.4 Protocol, `flyemu-protocol/1`

One JSON file describes a whole experiment. `app/server/record.py --protocol` executes it and the
recording embeds it, resolved (targets turned into model rows, times into steps, every
approximation written beside its event, and the held-out check). As built in M2
(`app/server/protocol.py`; the library is in `app/protocols/`):

```json
{
  "format": "flyemu-protocol/1",
  "title": "MDN (moonwalker) CsChrimson as +10 mV current, 0.5-1.5 s",
  "config": {"scan": "male-cns:v1.0", "body": "flybody", "profile": "m9", "seed": 12,
             "min_synapses": 5, "overrides": {}},
  "duration_ms": 2000,
  "genotype": [],
  "events": [{"t_ms": 500, "dur_ms": 1000, "effector": "CsChrimson", "mv": 10,
              "target": {"type": "MDN"}, "label": "MDN light on (current approximation)"}],
  "expect": {"text": "The fly walks backward while MDN is activated.",
             "source": "Bidaye et al. 2014 Science", "readout": {"type": ["MDN"]},
             "status": "...seed 12 is a spent seed, so this run is development evidence",
             "criterion": {"metric": "forward_mm_vs_control", "op": "<=", "value": -0.5,
                           "units": "mm", "what": "...", "basis": "guessed threshold, written
                           4 October 2026 before any library result was viewed"}},
  "record": {"watch": {"type": ["MN9", "MDN", "DNa02"]}}
}
```

Targets select model rows by `bodyId` list, `type`, `class`, `superclass`, `somaSide` or `instance`
(exact, or a regular expression written `re:...`); several keys must all match. Events take
`pulse_hz` and `pulse_ms` for pulse trains; `kick` events take `rate_hz`; `world` events set
fields of the organism's World (food patches, odour sources, wind, sound, humidity, CO2, light;
not temperature, whose effect is applied at build time). A protocol with no events and no genotype
is a control; `"role": "sham"` marks the noise-floor run. Named driver-line presets are not built.
Free-text fields (`note`, `config_history`, `sham_rule`) travel into the recording and are not
read by the resolver. `config.overrides` changes registry values for the run; any override makes
the profile "custom" in the page header.

`config.preparation` is `closed_loop` (default: senses, network, muscles, body) or `brain_only`
(open loop as in the model's `scripts/assay_pathways.py`: the network steps on the protocol's
drive and kicks alone; no senses, no motor output, the body never stepped; world events refused).
`config.kick_rng` `"assay"` draws kicks from `default_rng(seed + 10000)` as that script does, so
its trials can be reproduced spike for spike (`app/protocols/assay/`); the default `"app"` stream
is `default_rng([seed, 2024])`.

## 5. Brain maps

- **Positions.** male-cns gives `somaLocation` for 141,781 of 176,422 cached neurons (80.4 %,
  measured; voxel units, converted to µm at 8 nm per voxel, an assumption to check against the
  dataset metadata in M1). The 34,641 without one are mostly sensory neurons whose somata lie
  outside the CNS (17,843), optic-lobe intrinsic cells cut at the volume edge (8,348) and
  unlabelled fragments (7,603). Those get a derived position: the centroid of their synapses where
  fetched, else the synapse-weighted centroid of their regions, else their entry nerve, each with a
  basis code that the inspector shows. A "soma" and an "arbor" layout are both offered, because
  somata sit in the cortex rind while computation happens in the neuropil.
- **Regions.** neuPrint region (ROI) meshes, decimated to a few thousand triangles each, drawn as
  faint shells; per-neuron dominant input and output regions from `roiInfo` (cached today for 7,651
  sensorimotor cells; a one-time fetch covers the rest). If a public, token-free copy of the meshes
  exists it is preferred; otherwise the existing neuPrint fetch path is used.
- **Activity.** One point per neuron (167,111 points, one draw call). Brightness is a decaying trace
  of that cell's spikes, recomputed each frame from the spike stream; colour by superclass,
  transmitter, side or a selected pathway. Watched cells can show voltage instead.
- **Selection.** Click a point, search by type, instance or bodyId, select a whole type, or lasso a
  region. The selection's partners (top inputs and outputs from the edge shards) are drawn as lines;
  all 6.2 M edges are never drawn at once.
- **Flow layout.** A second view places cells by side (x) and by a flow layer, a derived distance
  from the sensory periphery (y), so a pathway such as sugar GRN -> GNG -> MN9 can be watched as a
  wave. Built in M1 with the probabilistic traversal of Schlegel et al. 2021 (threshold 0.3, 16 runs,
  from all sensory neurons; 170,611 of 176,422 cells reached, measured). Display only.
- **Groups layout.** Blocks of cells by superclass, so rates in small classes stay visible.

As built in M1, positions have five bases (counts measured on the male-cns v1.0 cache): soma
141,781; photoreceptor terminal centroid 5,998; synapse-weighted mean of partners' positions 26,994;
class centroid 1,648; none, drawn at the CNS centroid, 1. Region shells are not built yet: there are
no region meshes in the project cache (M2 or later).

### 5.1 Layers: measured, inferred, completed

Ben, 4 October: "divisions for measured and inferred/completed data, because our ending complete
brain that we build will not be the only possible one. Max flexibility." Every value the app shows
carries one of three layers, drawn as a chip:

| Layer | Meaning | Source in the run |
|---|---|---|
| measured | read from the scan or a recording (synapse counts, soma positions, annotations) or counted in this run | atlas; recording |
| inferred | set by a stated rule from measured data (transmitter from the classifier, a parameter from a per-type table, a derived position) | inventory basis "derived" or "inferred" |
| completed | chosen by search within biological bounds where nothing constrains it (fitted class gains, profile values) | inventory basis "guessed", or method "profile" |

M1 shows the chips in the inspector, can colour the map by position basis (measured or derived),
and has a "measured positions only" filter that hides derived positions. There is no map colouring
by parameter layer yet: that needs the inventory resolved per cell. Toggling a whole layer off, and choosing
between alternative completions (seeds or ensemble members of a search), need completions to be
recorded side by side; M4's Fidelity tab counts each run's values by layer but does neither yet.

## 6. Selectable configuration: scans, bodies, fidelity

### 6.1 Brain scans

| Scan | Coverage | Sex | In the project now | App support |
|---|---|---|---|---|
| male-cns v1.0 | whole CNS | male | the model's source; cached | atlas + simulation |
| BANC | whole CNS | female | metadata for 188,508 cells with positions and matches to FAFB, MANC, male-cns, hemibrain and FANC (`data/raw/banc/banc_888_meta.feather`); no edges | atlas and comparison first; simulation needs edges and a connectome adapter |
| FlyWire FAFB v783 | brain only | female | type crosswalk only (`flywireType` in male-cns) | atlas; simulation needs a VNC (e.g. MANC) joined at the neck by descending/ascending matches |
| MANC v1.2 | VNC only | male | `mancBodyid` crosswalk in male-cns | atlas; partner for FAFB |
| hemibrain v1.2.1 | part of the central brain | female | `hemibrainType` crosswalk | atlas and comparison only: it cannot drive a body |

"Mix and match" has two levels. **Comparison** (M5) works for every scan: the same type side by side
across specimens, with cell counts, partner overlap and synapse-count spread. This is the raw
material for the individuality study in `docs/FIDELITY_LADDER.md` (how much of a scan reconstructs
the original fly). **Simulation** on another scan needs the model to accept another connectome
(`connectome.build` reads the male-cns cache today) and to carry parameters across by type; that is
model work, requested in section 13, and every cross-specimen join is labelled inferred.

### 6.2 Bodies

`Body` already supports `flybody` (default) and `neuromechfly`; `Organism` does not yet expose the
choice (request 1). Each body gets a body/1 bundle. Body-level fidelity switches (legacy torque vs
Hill muscles, flight motor, adhesion gate, TTM jump muscle) are registry switches and appear with
the brain switches.

### 6.3 Fidelity

- **Profiles:** m4 (regression reference), m9r (the working profile), m10p and m10q (rung 2
  candidates, not adopted) and the rest as "custom, not validated", each shown with its status
  from `profiles.py` and HANDOFF (built in M4: the Fidelity tab, section 14).
- **Switches:** registry keys with their neutral value, current value and evidence label
  (from `data/model/mechanisms.yaml`, `data/model/parameters.csv` and the run inventory), grouped by
  `docs/FIDELITY_LADDER.md` rung.
- **Status line:** any configuration that is not an adopted profile is shown as "custom, not
  validated". A/B mode (M2) runs or replays two configurations side by side with per-neuron rate
  differences on the brain map.

## 7. Interaction: virtual optogenetics and stimuli

### 7.1 Effectors

| Effector | What it does in a fly | Model now (public API) | Faithful version (needs request) |
|---|---|---|---|
| Current step | electrode injection | `external_mv` added to the target rows | same |
| Shiu kick | Poisson input as in Shiu 2024 | `Network.step(kick=...)` | same |
| CsChrimson | red-light cation channel | depolarising `external_mv` during light (current-based approximation, labelled) | light-gated conductance with reversal ~0 mV and on/off kinetics (request 3) |
| GtACR1 | green-light anion channel; shunting silencing | hyperpolarising `external_mv` (labelled: not shunting) | anion conductance at the chloride reversal (request 3) |
| Kir2.1 | constitutive K+ leak; build-time | constant hyperpolarising `external_mv` from step 0 (labelled: not a leak conductance) | extra leak conductance per cell (request 3) |
| TNT | blocks chemical output; build-time | `Network.silence(idx)` before the run | same |
| shibire-ts | output block above ~29 °C, reversible | not available | reversible output gain per cell (request 4) |
| Sensory | tastants, odour, touch, wind, temperature, visual objects | world and sense modules (`world.py`, `extrasenses.py`, `olfaction.py`) | visual stimulus objects in the arena (request 5) |

Light is also a world stimulus: with request 5 the stimulation light passes through the eye model's
opsin templates (`vision.opsin_sensitivity`), so the model fly can see red light as real flies
weakly can, and "blind" or "no retinal" controls are protocol options.

### 7.2 Live session API (local)

`POST /api/sessions` with a protocol's `config` starts a worker through the slot limiter and returns
a session id, or a "no slot" reply. A websocket carries commands (`run until`, `pause`, `step`,
`stim` with an event, `watch`, `snapshot`, `branch`, `stop`) and events (`chunk ready`, `status`
with simulated time and measured wall-per-sim-second, `error`). Commands take effect at the next
step boundary and are written into the recording's `stim` stream with the exact step, so a live
session replays identically from its own protocol. The browser plays the newest chunk, with an
honest speed gauge.

As built (M2b, 4 October 2026), simpler than the plan above: no websocket, no step, snapshot or
branch (those need request 2).
- `POST /api/sessions {"protocol": ...}` checks the protocol, then starts `record.py --live`
  through the slot harness (so it waits for a slot and RAM like any heavy job) and returns an id.
  One session at a time; the server stops it when the server stops. `GET /api/sessions` gives
  each session's state, simulated time and command log; `POST /api/sessions/<id>` sends `pause`,
  `resume`, `stop` or `stim` with an event. POSTs need the header `X-Workbench: 1` and a local
  Host, so another web page cannot start or steer a run.
- The server appends commands to `<runs>/live/<id>.commands.jsonl`; the recorder reads it every
  10 ms of simulated time (`app/server/live.py`). A stim starts at the step it is read, is
  resolved and checked like a protocol event, is refused if it touches a held-out item, and is
  appended to the recording's protocol, so the finished recording replays from its protocol
  alone (tested in `app/tests/test_live.py`: the kicks drawn live equal the kicks a fresh
  Stimulator draws from the final protocol). Pausing stops the clock, not the model, so pauses
  leave no trace in the recording; total pause is capped at 30 min. A stop ends the run at the
  current step and the recording is complete, with the shorter duration.
- Live runs write 50 ms chunks; the page follows any recording whose status is `recording`,
  loading new chunks every 3 s. At the measured cost (about 100 s of wall time per simulated
  second closed loop, 55 s brain only, on the Mac) a chunk arrives about every 5 s; "live" means
  steerable, about 1 % of real time.
- `POST /api/check` resolves a protocol on the atlas (the model's rows and order) and runs the
  held-out guard without building the model; the Session tab uses it before starting.
- The Session tab is the protocol editor: the protocol as JSON (from the open recording, or a
  blank one that uses the working profile), check, start, download; a stimulus form (effector,
  target types or bodyIds, rate or mV, duration) that either adds the event to the protocol at a
  chosen time or sends it to the running session; the check's result lists each event's cells
  and approximation and the expected wall time at the measured cost; pause, resume, stop and the
  session's command log, with a link that opens the growing recording.

### 7.3 Warm starts and branching

Every run started from rest begins with a transient (the fall onto the legs, lockstep MN volleys;
`docs/media/m9_closed_loop.md`). A warmed-up snapshot avoids repeating it, and "branch from here"
lets a control and a stimulated run share the same past. Both need a snapshot and restore of the
whole organism (request 2). Until then, sessions start from rest and say so.

### 7.4 Held-out guard

Some interventions are held-out tests (HANDOFF register; `data/measurements/targets_session6.csv`
`use` column). As built in M2 (`app/server/heldout.py`): an index of the register (giant fibre to
DLM and TTM, LPLC2 to giant fibre, Johnston's organ to grooming DNs and MDN, the sealed tibia
flexor recordings) and of the spent seeds (0 to 13, 17 to 19). The recorder refuses a protocol
that stimulates or reads out a listed item, or uses an unspent seed, unless the run names it with
`--spend-heldout <id>` (or `--spend-heldout seed`); spending is appended to
`runs/app/heldout_spent.jsonl` and the check is saved in the recording, where the Run tab shows it.
The index can lag the register, so a hit or a miss is a prompt to check the register, not a ruling.
The Session tab's protocol editor (M2b) does not spend held-out data: its check and the server
refuse a held-out item or an unspent seed, and a live stim that touches one is refused and
logged; spending stays a deliberate command-line act. The public intervention library contains only
protocols already run and recorded under the project's procedure, each labelled with the result's
status and shown beside the published expectation, including when the model does not reproduce it.

## 8. Fly's-eye view

The model's eyes are flygym's compound eyes: each eye is rendered by a MuJoCo camera and sampled
into 721 ommatidia with pale and yellow channels, at 100 Hz (`vision.build`, `sample_hz=100`). The
network's photoreceptors read those values through the derived retinotopy
(`data/derived/retinotopy.csv`, terminal positions with an inferred global alignment).

Panels, all synced to the replay clock:

1. **What the eye samples:** each eye's 721 values drawn as the hex mosaic (flygym's
   `ommatidia_id_map`, rendered in a shader), optionally beside the camera image before sampling.
2. **Photoreceptors:** R1-R6 and R7/R8 drive and spikes at their ommatidium's azimuth and
   elevation. Ommatidia with no assigned photoreceptor are hatched: male-cns holds 3,377 R1-R6
   against ~9,600 in a fly (`src/flyemu/vision.py`), and that gap is shown, not hidden.
3. **Columns downstream:** L1-L5, Mi1, Tm1-4, T4/T5 placed at a column derived from connectivity.
   As built (M3), each cell takes the synapse-weighted mean position of its placed inputs, iterated
   from the photoreceptors (derived), with hops, input share and spread per cell. This table may
   be useful to the model too and will be offered to fly.
4. **Outputs:** lobula plate tangential cells (HS, VS, H1, H2) as traces: membrane potential where
   watched, else spike rate. Visual projection neurons (LC types) are not drawn yet.

Visual worlds (looming disc for the giant fibre escape, rotating grating for optomotor turning, a
dark bar) need arena objects (request 5); until then the eye sees the floor and the sky.

## 9. Layout

A single page with resizable panels: body (left, large), brain map (right, large, soma/arbor/flow
toggle), fly's eye (collapsible strip), traces (selected cells, motor raster, torque, class rates),
inspector (selected neuron or type: identity, transmitter with confidence, position basis, partners,
parameters with evidence labels, matches in other scans), protocol timeline (stimulus bars on the
transport), provenance and caveats (generated). The current viewer's visual language (muted
palette, Archivo and IBM Plex Mono, light and dark themes) is kept, with fonts vendored rather than
loaded from Google.

## 10. Performance on the 16 GB Mac

Measured today (`app/tools/bench_live_cost.py`, M2 Pro, 200 steps of 0.1 ms after 20 warm-up steps,
seed 0, from rest; the network was silent in this window, so active runs cost more):

| Configuration | Build | Wall s per simulated s | Peak RSS |
|---|---|---|---|
| m9 closed loop | 7.9 s | 86.7 | 2.39 GB |
| m7 closed loop | 7.4 s | 39.1 | 2.28 GB |
| m9 brain only | 7.5 s | 54.9 | 2.03 GB |

Whole recordings agree (the assay check's manifests, 4 October, with other jobs running): m9
closed loop 95 to 102 s of wall time per simulated second over 1 to 2 s runs (15 runs), m9 brain
only 53 to 56 s (6 runs); recorder start and build add about 10 s.

Consequences:
- **Live on the Mac is slow motion:** one simulated second takes 40 s (m7) to 90 s (m9) or more.
  The live mode is "run and watch it arrive", not real time. A 1 s optogenetic pulse with 0.5 s of
  context is about 2 to 3 minutes at m9.
- **One live organism at a time** (2.4 GB); the session asks the slot limiter, which needs 3 GB free
  (3.6 GB was free today with other workers running).
- **Browser budget:** 167,111 points with a per-frame activity array (0.7 MB upload per frame) and
  ~100 k triangles of neuropil and ~100 k of body (decimated from 272,550) are well inside an M2
  Pro's WebGL budget (inferred; FPS measured in M1). Decoded data for a 30 s recording is ~100 MB.
- Faster interaction comes from backhouse (GPU brain), warm-start snapshots, and later an optional
  in-browser simulation (question 4).

## 11. Static mode and data distribution

Built in M1: `app/build/site.py` copies the page, the data and chosen recordings into one directory
with a fixed `catalog.json` (two recordings with the male-cns atlas and the flybody body: 70.7 MB,
measured); it rendered under a plain file server. Nothing is deployed. Ben's answer 4 makes the
installable app the main product, so the static site is now secondary: the same bundle layout serves
as the download unit for connectome data and recording libraries.

Generated data stays out of version control: `app/data` (the atlas, 49.8 MB, rebuilt in 10 s from
the project's neuPrint cache; the body bundle, 13 MB) and every recording. The builders are
committed.

Original plan for Pages: `app/build/site.py` writes a self-contained site: the web app, the male-cns atlas, body bundles and
a curated gallery of recordings. GitHub's published limits (as recalled, to check at M7): 1 GB per
site, 100 MB per file, about 100 GB a month of bandwidth. Recordings are chunked well under those.
Large data is not committed to git: the Pages workflow downloads a versioned data bundle (a GitHub
release asset) at deploy time. Enabling Pages and publishing release assets is publishing, so it
waits for Ben. Dataset licences and attributions (FlyEM, FlyWire, BANC, flygym/flybody meshes)
are checked and shown in the site before then.

## 12. What replaces the current viewer

- `app/` replaces `viz/index.html` and `scripts/serve_viz.py`. The good parts move across: compiled
  geometry, the mapped/unmapped motor raster, the clipped-torque disclosure, tarsal load tint.
- `app/build/convert_legacy.py` turns every `runs/*/replay_data.js` into rec/1 (motor spikes only,
  flagged as such), so old runs stay viewable.
- `scripts/record_organism.py` stays for the fly worker; the app's recorder uses the same public
  loop and records more.
- When M1 is accepted, a separate commit removes `viz/` and `scripts/serve_viz.py`, and fly is asked
  to update `docs/RUNNING.md` and `docs/ARCHITECTURE.md` (not my docs).

## 13. Requests to the fly worker (model API)

On hold: Ben ordered fly's blanks, body and ladder work first (4 October). Until then live
optogenetics uses current injection through the existing `external_mv` input, labelled as an
approximation. None blocked M1. In order of need:

1. **Body choice in `Organism`**: a `body_model` argument (or registry switch) passed to `Body`, so
   a session can pick flybody or NeuroMechFly without rebuilding parts by hand (record_organism
   rebuilds the body and five dependent modules today to add a camera).
2. **Snapshot and restore** of the whole organism (network state including delay buffers, channel
   gates and plasticity; body `qpos`/`qvel`/actuator state; senses, organs, RNG), with a
   continuation test: restore then step equals uninterrupted stepping.
3. **External conductance input** in `Network.step` (per-row conductance and reversal, CPU and GPU),
   for CsChrimson, GtACR1 and Kir2.1 as conductances rather than currents.
4. **Reversible output gain** per neuron (for shibire-ts and reversible silencing), distinct from the
   irreversible `silence()`.
5. **Visual stimulus objects** in the arena (looming disc, grating drum, bar) with a schedule, and a
   world light source with a spectrum.
6. Later: **connectome adapters** (BANC; FAFB + MANC joined at the neck) with type crosswalks for
   parameters.

Found by the graded-medulla run (section 14, 6 October); notes for the fly worker, not changes the
app makes:

7. **Graded release that is tonic at rest.** The graded rule passes nothing at or below rest, so
   L1-L3, which light hyperpolarises, are silent all run, and the light signal stops at the lamina.
   In flies the lamina cells release tonically and light lowers the release.
8. **The measured temporal filters of the T4/T5 inputs** (Mi1, Tm3 fast; Mi4, Mi9, C3 slower;
   Tm1, Tm2, Tm4, Tm9 for T5). Without them the wiring gives no direction selectivity.
9. **The variant's graded rows as candidates for `cell_types.csv`:** Mi1, Tm3, Tm1, Tm2, Mi4, Mi9,
   C3, T4a to T4d and T5a to T5d (`app/protocols/eye/variant_graded_medulla.csv`, each with its
   whole-cell source).

   The fly worker has since built switches for 7 and 9 (`main` 698c2eb and 81e7afa, merged into
   `app`, neutral by default): `cell_type:ol_graded|release_at_rest` (a fraction of the maximum
   release at rest, 0 to 0.9, guessed) and `cell_type:all|mode_from_recordings` with per-type
   `graded_rec` rows. Request 8 (temporal filters) is the open one.

Found while building M4 (section 14):

10. **Quote the flow text in `data/model/mechanisms.yaml`.** The names of B1, B3, N22 and N25 and
    the notes of B6 contain commas inside unquoted flow mappings, so a YAML reader cuts them into
    stray keys. The app rejoins them (`app/build/fidelity.py`, marked in the tab); quoting them
    would make that unnecessary.

### 13.1 The T4/T5 direction test (for the fly worker)

The Director's order (6 October): the fly worker builds per-type temporal dynamics as model rungs,
and this test is their held-out check. One command records a profile and reports, per T4/T5
subtype, whether the cells respond and whether they prefer the direction they prefer in flies.

```
.venv/bin/python app/tools/t4t5_ds.py --profile <rung> --out runs/app/t4t5/<label> \
    [--set 'entity|property=value'] [--model-root ~/fly-emulation] [--parallel 7]
```

For the fly worker's `docs/HANDOFF.md` (theirs to paste; the app does not edit it):

> **T4/T5 direction test (held-out, from the app worker).** From a checkout with `app/` (branch
> `app`): `.venv/bin/python app/tools/t4t5_ds.py --profile <rung> --model-root <checkout with the
> rung> --out runs/app/t4t5/<label> [--parallel 7]`. It records 17 two-second runs at seed 0 (a
> control, then moving ON and OFF bars in 4 directions, injected either into the medulla inputs
> of T4/T5 or into the photoreceptors) and reports, per T4/T5 subtype, "no response", "not
> selective", "selective as in flies" or "opposite" (Maisak et al. 2013 preferences, Wilcoxon
> with Holm). Exit 0 only if all 8 subtypes are selective as in flies. About 20 minutes on
> backhouse at `--parallel 7`, over an hour on the Mac. Run it once a rung's values are set, not
> while fitting, and record each call in DECISIONS. Baselines: plain m9r gives no response (its
> medulla inputs spike and the 4 mV bars stay below threshold); m9r with the medulla inputs graded
> responds but is not selective (0 of 8). The photoreceptor set also needs the lamina to transmit
> at rest. Details: `docs/APP_DESIGN.md` section 13.1 on branch `app`.

- **Where to run it.** From a checkout that has `app/` (this branch, or `main` once `app` is
  merged). `--model-root` points at the checkout that holds the model under test (its `src/` and
  `data/`), so a rung on the fly worker's branch is tested without merging anything; the manifest
  records that checkout's commit and dirty files (`provenance.model_src`). Without it the
  checkout's own `src/` is used. Profiles and the status label come from that checkout too
  (checked 6 October with a 30 ms run on `main` at 81e7afa: the manifest named that commit, and
  m9r was labelled "custom, not validated" because `main`'s working profile is now m9c). Switches
  go in with `--set`, e.g. `--set 'cell_type:ol_graded|release_at_rest=0.5' --set
  'cell_type:all|mode_from_recordings=1'`; every run's manifest keeps them and its status reads
  custom. On the Mac every recording takes a slot from the Director's
  limiter (through `run_library.py`). On backhouse set the MuJoCo environment first, as in
  `~/flyapp/bh_t4t5.sh`: `LD_LIBRARY_PATH=$HOME/osmesa/root/usr/lib/x86_64-linux-gnu
  MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa`, and pass `--parallel 7`.
- **Cost.** 17 recordings of 2 s at seed 0 (one control; medulla ON and OFF bars and photoreceptor
  ON and OFF bars, 4 directions each). On backhouse at `--parallel 7`: 342 to 431 s per run and
  20 minutes for the set (measured, validation call below), up to 3 GB per run. On the Mac, one
  at a time through the slot limiter, about 17 times 4 to 5 minutes (inferred from the M2 library's
  190 to 240 s per 2 s run). Resumable: rerun the same command and finished runs are skipped.
  `--stimulus medulla` or `photoreceptor` records one set (9 runs); `--analyse-only` re-reads.
- **Output.** A report on stdout, `<out>/ds.json` and `<out>/ds.png`. Exit 0 when every set
  recorded passes, 3 when any fails.
- **The stimuli** are fixed files, `app/protocols/t4t5/*.json` (each run records the file's md5).
  Medulla bars: current into the T4 inputs under a moving bar (Mi1, Tm3, Mi4, C3 +4 mV; Mi9
  -4 mV) or the T5 inputs (Tm1, Tm2 +4 mV); they test the circuit from the medulla inputs on.
  Photoreceptor bars: R1-R6, R7 and R8 under the bar +3 mV (ON) or -3 mV (OFF); they test the
  whole path from the eye. 19 left-eye ommatidia, 2-column bars, one column per 50 ms, two
  sweeps. Amplitudes are guessed; the axes are inferred from the retinotopy fit (front-to-back
  is mosaic -x, upward -y).
- **The readout and the verdict** (fixed 6 October, before any rung was tested). Per watched
  cell, 17 to 19 per subtype: the peak change in potential against the control over both
  sweeps; T4 from ON bars, T5 from OFF bars. DSI = (pref - null)/(|pref| + |null|) with the
  preferred direction from flies (Maisak et al. 2013: a front-to-back, b back-to-front, c upward,
  d downward). Two-sided Wilcoxon signed-rank test across cells, Holm over the 8 subtypes of a
  set. A subtype is "no response" if its median peak is under 0.5 mV in every direction
  (guessed floor), "not selective" if Holm p is 0.05 or more, otherwise "selective as in flies"
  or "selective, opposite to flies" by the sign of the median DSI. A set passes when all 8 are
  selective as in flies. A bias shared by every cell (for example from the bar geometry) cannot
  pass, because within each pair (a/b, c/d) the preferences must be opposite.
- **Held-out use.** Run it on a rung once its values are set, not while fitting them. Record each
  call, the rung and the verdict in DECISIONS. If a rung fails and is changed, say what changed
  and why before the next call. Do not edit the stimulus files to pass; `--write-stimuli`
  rebuilds them from the mosaic and is maintenance only, to be recorded as a change to the test.
- **What it cannot tell.** The bars are injected current, not light from a moving scene (the
  arena has no moving stimulus: request 5). One patch, one seed. The amplitudes are guessed.
  Flies' preferences were measured mostly by calcium imaging, and this test reads voltage.
  A pass shows the right direction preference, not the right size: no DSI magnitude from flies
  has been checked here.
- **Baselines** (measured; section 14, "The T4/T5 direction test: validation"): m9r with the
  graded-medulla rows FAILS both sets: medulla bars, T4 and T5 respond (1.2 to 2.1 mV) and 0 of 8
  are selective; photoreceptor bars, no response in any subtype. Plain m9r FAILS both sets with no
  response anywhere: its medulla inputs spike, and the 4 mV bars leave them 3 mV short of
  threshold, so not one spike changes. A rung that adds temporal dynamics should first change the
  medulla set, and needs the medulla inputs graded (request 9; `main`'s
  `cell_type:all|mode_from_recordings` switch) for that set to respond at all.
- **The photoreceptor set cannot pass while the lamina transmits nothing at rest** (request 7):
  in m9r L1-L3 sit 3 to 5 mV below rest, and even under the bars they cross rest in at most 0.2%
  of samples (measured, variant photoreceptor OFF runs). A rung aimed at the photoreceptor set
  needs tonic lamina release, or a resting point above the cut-off, first.

## 14. Milestones

Each milestone ends with a commit and push of branch `app`, headless screenshots and a contact sheet
that I look at, and the tests listed.

**M1: replay workbench on the new format (replaces the viewer for replay).** Built 4 October 2026:
the recorder, a 2 s m9 recording, the male-cns atlas, the web app (body, brain map in anatomy, flow
and groups layouts, traces, inspector with layer chips and partners, run panel with generated
caveats), the local server, the static builder, the legacy converter (12 of 12 converted, motor
spikes identical to the source files) and 20 passing tests (`app/tests`). Not in M1: region shells
(no mesh source in the cache) and an eye mosaic (M3). Planned contents:
- rec/1 writer and reader; `app/server/record.py` records every spike, poses, torque, contact and
  eye readouts through the public loop; a 2 s m9 recording (about 3 minutes of wall time).
- male-cns atlas/1 with positions and basis codes, vocabularies, edge shards; neuropil shells if a
  mesh source is available without new credentials handling, else in M2.
- Web app: body (ported), brain map with activity, search and click selection, inspector with
  partners, motor raster, torque, class rates, generated provenance and caveats.
- `app/server/serve.py` serves it locally; `app/build/site.py` writes the static site (not deployed).
- Converter for the ten legacy recordings.
- Tests: format round trip; spike totals in the bundle equal the run's count; every model row joins
  to the atlas; atlas position coverage reported; page renders non-blank headless.

**M2: live sessions and virtual optogenetics.** Session API and worker, protocol/1 editor and
timeline, current-based effectors now and conductance effectors when request 3 lands, held-out
guard, A/B comparison, a first precomputed intervention library (for example MDN, giant fibre,
sugar GRNs, DNa02 left vs right), each beside its published expectation.

Built 4 October 2026 (stimulus protocols, labelled optogenetics, replay of interventions; live
sessions and the protocol editor followed in M2b, below; conductance effectors are not built):
- `flyemu-protocol/1` (section 4.4) and its effectors (section 7.1). CsChrimson, GtACR1 and Kir2.1
  are current injection, and each resolved event carries its approximation text, which the page
  shows as a "guessed" chip beside the event. Kicks use their own seeded generator so a run and its
  control share every model random draw; the tests confirm the spike trains are identical up to
  the first event and differ after it.
- Held-out guard (section 7.4).
- Library (`app/protocols`): a control, four tests (sugar GRN kicks, sugar patch under the legs,
  MDN CsChrimson, DNa02 left current) and a sham (a few forced spikes in one Kenyon cell). All use
  seed 12, a spent seed, so every result is development evidence, not a held-out test. Each test
  states what a real fly does, its source and a pass/fail criterion written before any library
  result was viewed (the thresholds are guessed).
- Comparison in the page (Compare tab and the "rate vs control" colour): matched control, first
  step where the runs differ, the criterion's verdict, readout rates before, during and after,
  thorax movement, cells changed, the largest changes, and the sham read over the same window.
  The model is chaotic: after the first difference the two runs decorrelate, so many changed
  cells are noise, and the sham measures how large that noise is. A verdict no larger than the
  sham's is labelled "within noise". The stimulus track shows each event, pulse and forced spike.
- `app/tools/score_library.py` recomputes every comparison independently of the page and writes
  `runs/app/lib/scores.json`, whose verdicts the run picker shows; `app/tools/replay.py` re-runs a
  recording's embedded protocol and checks every array is identical.
- Results: see the verification against the model's assay and the library results below.

**Verification against the model owner's assay** (4 October 2026, after the first library below
was viewed; `app/protocols/assay`, `runs/app/assay/scores.json`). The first library's sugar test
gave +0.5 Hz where the model's own assay gives about 6 Hz, so the app's setup was checked against
that assay before any failure is read as the model's. The assay (`scripts/assay_pathways.py
--assay sugar_mn9 --profile m9`): brain only (no senses, no body), the 34 sugar GRNs (LB3b, LB3c)
kicked at 100 Hz Poisson from 0 to 1000 ms with kicks from `default_rng(seed + 10000)`, trial t
on seed t, readout MN9_L alone (MN9_R, bodyId 16949, is left out as incompletely traced). The app
reproduces it through `config.preparation: brain_only` and `config.kick_rng: assay`, then adds
the library's differences one at a time. App values are derived from recordings; MN9_L was
silent (0 Hz) in every control.

| Setup | Seeds | MN9_L, Hz |
|---|---|---|
| Model owner: assay, m9 (`runs/assay-sugar_mn9-m9-s11_r2_diag_m9base`, 1 October) | 0, 1, 2 | 7, 6, 7 |
| Model owner: m9 adoption, 10 trials (HANDOFF) | 0-9 | 5.7 ± 1.4 |
| App: brain only, assay kicks (every one of the 167,111 cells has the same spike count as in the model owner's run) | 0, 1, 2 | 7, 6, 7 |
| App: brain only, assay kicks | 0-9 | 7, 6, 7, 5, 7, 7, 5, 6, 4, 3 (mean 5.7, SD 1.4) |
| App: brain only, assay kicks | 12 | 7 |
| App: brain only, the app's kick stream (same rate, cells and window; another Poisson draw) | 0, 1, 2, 12 | 6, 6, 1, 4 |
| App: brain only, the app's kick stream | 0-9 | 6, 6, 1, 6, 7, 8, 7, 4, 8, 5 (mean 5.8, SD 2.1) |
| App: + closed loop (senses, body), 0-1000 ms | 0, 1, 2 | 8, 5, 6 |
| App: + the library's window, 500-1500 ms | 0, 1, 2 | 9, 6, 9 |
| App: + the library's override `force_per_spike` = 10 | 0, 1, 2 | 5, 5, 7 |
| App: + seed 12 (assay kicks) | 12 | 7 |
| App: as above without the override | 12 | 8 |
| First library: + the app's kick stream (seed 12, override) | 12 | 1 |
| Library on m9 without the override (seed 12, app kicks; `runs/app/lib-m9`) | 12 | 7 |

What the table shows (derived from the recordings):
- The app's setup is not the difference. Run the way the model owner runs the assay, the app
  gives the same spike count in every one of the 167,111 cells on trials 0 to 2, and the same
  10-trial result, 5.7 ± 1.4 Hz.
- The library's +0.5 Hz has three contributors.
  - Its readout averaged MN9_R with MN9_L. MN9_R (bodyId 16949) is flagged as incompletely
    traced: 633 input synapses against MN9_L's 6,358 (`docs/FINDINGS.md` F-PERCELL-1; the assay
    script cites it as F-DATA-3). The assay leaves it out; read that way the library's figure is
    +1.0 Hz. The scorer and the Compare tab now drop such cells and say so.
  - The override `force_per_spike` = 10, which is not part of m9.
  - The kick draw. The library judged one trial, with kicks from the app's stream.
- At seed 12 with the library's setup (closed loop, 500 to 1500 ms), MN9_L fires at 7 Hz with
  the override and the assay's draws, 8 Hz with neither, and 7 Hz with the app's draws and no
  override. Only the combination of the override and the app's draw gives 1 Hz. So the first
  library's sugar result was one low trial, not a property of the app's setup.
- The closed loop, the later window and seed 12 do not lower the response (5 to 9 Hz). The
  override lowered it in all 5 paired closed-loop trials, by 1 to 6 Hz (mean 2.8; n = 5, so the
  size is uncertain). The pairs share the seed but not the past: the override changes how the
  body moves before the stimulus, so the network's state at onset differs too.
- One trial of this pathway ranges from 1 to 9 Hz between perturbations that leave the input
  rate unchanged: another Poisson draw, the override, the closed loop. The kicks delivered differ
  by less than 7 % between trials (3,282 to 3,522) and do not predict the count. A criterion on
  one trial says little; the model owner reports the mean of 10.
- The app's kick stream is not a bias. On seeds 0 to 9, brain only, it gives 5.8 ± 2.1 Hz
  against the assay stream's 5.7 ± 1.4 Hz. The difference, 0.1 Hz, is well inside its standard
  error of about 0.8 Hz. Seed 2's 1 Hz is one low trial; the assay stream's lowest is 3 Hz. The
  model owner's replicate inside the bitter assay gave 4.8 ± 1.7 Hz (`docs/FINDINGS.md` F-RS-1).
  So one trial of this pathway at 100 Hz lands anywhere from about 1 to 9 Hz around a mean of 5
  to 6 Hz. The library's single-trial criterion (at least 5 Hz above control, which is silent)
  fails on 2 of 10 trials in either stream, even though the model reproduces the assay.

**First library results** (seed 12, 2 s, m9 with the override `motor_unit:all|force_per_spike` =
10; recorded and scored 4 October 2026; `runs/app/lib/scores.json`). The override was copied from
example commands in `docs/RUNNING.md`; it is not part of m9 (default 1, guessed), and it made the
page's header read "custom". Every number is derived from the recordings. Thresholds are guessed,
declared before any result was viewed. Seed 12 is spent, so these are development evidence, not
held-out tests. The sham is one sample, read over each test's window (500 to 1500 ms) against the
same control. The table is as first scored, with MN9 averaged over both cells; read as the model's
assay reads it (MN9_L alone), the sugar test is +1.0 Hz.

| Protocol | What was done | Criterion | Measured | Sham, same window | Verdict |
|---|---|---|---|---|---|
| sugar-grn-kick | 34 sugar GRNs (LB3b, LB3c) forced at 100 Hz (3,395 kicks) | MN9 rate minus control >= 5 Hz | +0.50 Hz (one extra spike across the 2 MN9 cells) | 0.00 Hz | FAIL |
| sugar-patch-legs | 1 M sugar patch, 4 mm radius, under the fly | MN9 rate minus control >= 5 Hz | 0.00 Hz; no spike anywhere differs from the control | 0.00 Hz | FAIL, no spike changed |
| mdn-cschrimson | MDN (4 cells) +10 mV, as current | forward displacement minus control <= -0.5 mm | -0.09 mm (MDN +23 Hz) | -0.06 mm | FAIL |
| dna02-left | DNa02 left (1 cell) +10 mV | left turn minus control >= +5 deg | -3.6 deg (DNa02 +10.5 Hz) | -5.7 deg | FAIL within noise |

What this shows:
- The stimuli reach their targets (the driven cells fire 10 to 23 Hz above control; kicks land
  only inside their windows on their rows), and runs are identical to the control up to the first
  event and reproducible: two protocols recorded twice gave identical arrays (all 31, including
  voltages and eye frames), and `replay.py` re-ran sugar-grn-kick from its embedded protocol with
  all 33 arrays identical, kicks included.
- None of the four expected behaviours appears in these runs. Over the same 1 s window, the sham
  (three forced spikes in one Kenyon cell) changes 644 cells by 1 Hz or more and turns the fly
  5.7 deg relative to the control. The tests change 967 to 2,125 cells, 1.5 to 3.3 times the
  sham, but their body effects are no larger than the sham's.
- Leg taste cannot respond in this model (derived from `extrasenses.py` constants, not measured):
  the leg channel's drive is 15 mV x 0.2 x c/(c + 0.05 M), at most 2.9 mV at 1 M, below the
  7 mV gap between rest and threshold, and `input_gain` scales synaptic input only. So a sugar
  patch under the legs cannot change any spike. The 0.2 weight and 15 mV gain are labelled
  guessed in the model.
- Sugar GRN to MN9 is in the model's fit set (HANDOFF register), yet in this closed-loop run,
  with the body attached and seed 12, 100 Hz on the sugar GRNs adds one MN9 spike. The
  verification above traces the difference from the model's own assay.

**M2b: the check against the model's assay, live sessions, the editor, a sham distribution.**
Built 4 October 2026, evening.
- `config.preparation` (`closed_loop` or `brain_only`) and `config.kick_rng` (`app` or `assay`)
  let a protocol reproduce the model owner's assays; `app/protocols/assay` holds the ones used
  above.
- Live sessions and the Session tab editor as in section 7.2. End-to-end test (measured, 4
  October, `runs/app/live-e2e.log`): a 220 ms brain-only session through the real server; a
  sugar GRN kick sent at 60 ms was applied to 34 cells; a giant fibre stim was refused by the
  held-out guard and logged; simulated time stayed at 100 ms through a pause; resume and stop
  worked; the session took 28 s of wall time; `replay.py` re-ran the finished recording from its
  protocol and all 31 arrays were identical.
- Library on m9 as the model owner fits it, with 16 more shams (`runs/app/lib-m9/scores.json`,
  recorded and scored 4 October 2026, evening). Same protocols, seed 12, closed loop, the app's
  kicks, thresholds and windows. Three rules changed after the first library was viewed, and are
  labelled so: the override is gone, the readout drops incompletely traced cells, and the trials
  summary judges a mean. Every number is derived from the recordings.

  | Protocol | Criterion | Measured | Driven cells | 17 shams, same window (13 distinct) | Verdict |
  |---|---|---|---|---|---|
  | sugar-grn-kick | MN9_L minus control >= 5 Hz | +7.00 Hz (7 vs 0) | | all 0.00 | PASS |
  | sugar-patch-legs | as above | 0.00; no spike changed | | all 0.00 | FAIL, no spike changed |
  | mdn-cschrimson | forward minus control <= -0.5 mm | +0.04 mm | the 4 MDN 22 to 23 Hz, control 0 | -0.06 to +0.05 mm | FAIL within noise |
  | dna02-left | left turn minus control >= +5 deg | -0.15 deg | the left DNa02 19 Hz, control 0 (the right one, not driven, 0) | -1.2 to +3.8 deg | FAIL within noise |

  - Sugar GRNs to MN9 passes on this trial, as in the model's own assay. The first library's
    FAIL came from the override and one low draw (the verification above).
  - Leg sugar still changes no spike, as the model's constants predict (first library, above).
  - MDN and DNa02 fire well above control, but the body neither backs up nor turns beyond the
    shams, because it does not walk at all. In every run of this library the thorax drops from
    3.34 mm to 0.68 mm by 250 ms, the body rolls to about 28 deg by 1 s, and it stays there.
    Over the test window the control moves 0.03 mm back and 0.13 mm sideways and turns 0.3
    deg; a walking fly covers roughly 10 mm/s (guessed, typical). The model owner's own m9
    closed-loop record says the same: "It does not walk or take off"
    (`docs/media/m9_closed_loop.md`). So these two tests ask for a behaviour the current body
    cannot produce. Their FAIL is the model's present state, not evidence against the
    descending pathways' wiring.
  - Sham distribution: the 9 shams (the original and 8 drawn Kenyon cells, all at 500 ms) give
    6 distinct trajectories. Outside the forced cells, three shams repeat one spike train exactly
    and two repeat another; the scorer now hashes every spike in the window to count this, and
    the Compare tab reports it. Two causes:
    - Every sham's forced spikes fall on the same steps, because the app's kick stream depends
      on the seed and rate, not the target.
    - A Kenyon cell's few extra spikes change no other spike until one shared downstream spike
      moves. In 4 of the 9 this is the same DL2d_adPN projection neuron, 0.1 ms later, 8.5 ms
      after the first kick; in the other 5 nothing else changes for 40 ms.
    My reading (inferred, not tested): small voltage differences are erased at each cell's next
    reset, so different cells funnel into a few trajectories.
  - A second set of 8 shams, with new cells and onsets 505 to 540 ms (a rule added after the
    first set was seen), gives 7 distinct trajectories. The 525 ms and 530 ms shams, on different
    cells, both first move the same DC1_adPN spike by 0.1 ms, 30 to 37 ms after their kicks. In 6
    of the 8, the first spike to move outside the forced cell is an antennal-lobe projection
    neuron's, one step (0.1 ms) late. In one it is a lateral horn neuron's (LHPV12a1), one step
    early. In the other, nothing else moves within 89 ms.
  - Over the 13 distinct shams the body turns -1.2 to +3.8 deg (mean +1.0, SD 1.5) and moves
    -0.06 to +0.05 mm forward (SD 0.04), and 727 to 2,736 cells change. The mean turn is not
    zero because the control is itself one trajectory, so every difference is measured from one
    draw. The within-noise rule (no larger than the largest sham) now sits at 3.8 deg against
    DNa02's 5 deg threshold, and at 0.06 mm against MDN's 0.5 mm.

**10-seed library: the rule, declared 5 October 2026 at 02:10 CDT, before any of its runs was
recorded.** The same six protocols (the control, the one-cell sham and the four tests) on m9, at
seeds 0 to 9, closed loop, with the app's kicks, into `runs/app/lib-m9-seeds`.
- **Each seed is scored as before:** the test against that seed's control, with that seed's
  one-cell sham as its single noise sample. So the single-trial verdicts keep their old rule.
- **Each test is judged on the mean of its criterion's measure over the 10 seeds,** against the
  same threshold. Judging on the mean was added after the first library was viewed. For the
  movement tests, judging on the mean is new here.
- **The noise test on the mean, declared now:**
  - For each seed, take the test's value minus the same seed's sham value. Both are read against
    the same control.
  - Run a one-sided exact sign-flip test on those 10 differences, in the criterion's direction.
    It asks how many of the 1,024 sign patterns give a mean at least as far as the observed one.
  - The mean is within noise if p ≥ 0.05.
  - A test passes on the mean only if the mean meets its threshold and p < 0.05.
  - Code: `score_library.py`, `trials` and `sign_flip_p`, with tests in `app/tests/test_scoring.py`.
- **Why not the handoff's proposal** (the mean must exceed the largest single-seed sham): a mean of
  10 varies less than a single trial. A real effect smaller than the noisiest sham trial would
  then be called noise. The paired test compares like with like.
- **Expectation, written before the runs:**
  - Sugar GRN to MN9 should pass. The brain-only assay's mean is 5.7 Hz, and the shams leave MN9
    silent.
  - Leg sugar should change no spike at any seed.
  - MDN and DNa02 should fail within noise while the body does not walk.
  - These are expectations, not results.

**10-seed library: results** (scored 5 October 2026 at 05:05 CDT; `runs/app/lib-m9-seeds/scores.json`
and `runs/app/lib-m9-seeds-bh/scores.json`). Every number is derived from the recordings by
`score_library.py`. Thresholds are guessed and were declared before any run.
- **Where each seed ran:** seeds 0 to 5 on the Mac (commits f54f3bc and 253ef36), seeds 6 to 9 on
  backhouse (9901167, declared by the launcher). No file under `src` or `data` differs between
  these commits. Leg sugar ran on backhouse at all 10 seeds, against backhouse controls.
- **Matched:** at every seed, every test's spike train is identical to its control's until the
  stimulus.

Per seed: the test minus the same seed's control, with the same seed's one-cell sham in brackets.

| Seed | Machine | Sugar GRN: MN9, Hz | MDN: forward, mm | DNa02: left turn, deg | Leg sugar: MN9, Hz |
|---|---|---|---|---|---|
| 0 | Mac | +10 (0) | -0.01 (-0.04) | -0.92 (+1.47) | 0, no spike changed |
| 1 | Mac | +10 (0) | -0.01 (-0.01) | -2.59 (-0.87) | 0, no spike changed |
| 2 | Mac | +8 (0) | -0.05 (-0.01) | -1.74 (-0.42) | 0, no spike changed |
| 3 | Mac | +7 (0) | +0.05 (-0.03) | +0.29 (+0.25) | 0, no spike changed |
| 4 | Mac | +9 (0) | -0.06 (-0.01) | -1.31 (+0.51) | 0, no spike changed |
| 5 | Mac | +8 (0) | -0.01 (-0.07) | -0.59 (-0.62) | 0, no spike changed |
| 6 | backhouse | +12 (0) | -0.02 (-0.06) | +1.59 (-2.56) | 0, no spike changed |
| 7 | backhouse | +10 (0) | +0.02 (+0.03) | +1.73 (+0.21) | 0, no spike changed |
| 8 | backhouse | +10 (0) | -0.06 (0.00) | -0.88 (-1.23) | 0, no spike changed |
| 9 | backhouse | +4 (0) | -0.00 (-0.02) | +1.48 (+1.11) | 0, no spike changed |

On the mean of the 10 seeds:

| Test | Criterion | Mean (SD) | Sign-flip p vs shams | On the mean | Single trials passing |
|---|---|---|---|---|---|
| sugar-grn-kick | MN9 +5 Hz or more | +8.8 Hz (2.2) | 0.001 (1 of 1,024) | PASS | 9 of 10 (seed 9: +4 Hz) |
| mdn-cschrimson | forward -0.5 mm or less | -0.015 mm (0.033) | 0.66, within noise | FAIL | 0 of 10 |
| dna02-left | left turn +5 deg or more | -0.30 deg (1.50) | 0.53, within noise | FAIL | 0 of 10 |
| sugar-patch-legs | MN9 +5 Hz or more | 0.0 Hz (0.0) | 1.0 (4 pairs: backhouse has shams only at seeds 6 to 9) | FAIL, no spike changed | 0 of 10 |

- **The stimulated cells do fire:** DNa02 at 9.7 Hz (SD 0.35) and MDN at 22.3 Hz (SD 0.40), both
  against 0 Hz in the control. The body does not turn or back up because the m9 body does not walk.
- **All four results match the expectations written at 02:10.**
- **The `-bh` folder on its own** (seeds 6 to 9, 4 pairs) cannot pass any test: with 4 pairs the
  smallest possible p is 1/16 = 0.0625. The 10-seed folder is the result. The sugar test there
  reads +9.0 Hz with p = 0.0625.

**Mac against backhouse, the same control at the same seed** (seeds 0 to 5; measured by comparing
the two recordings spike by spike):

| Seed | Spikes, Mac / backhouse | Same (step, cell) spikes | First divergence | Final thorax position difference |
|---|---|---|---|---|
| 0 | 91,148 / 92,017 | 67,734 | 799.1 ms | 0.014 mm |
| 1 | 90,127 / 93,792 | 69,375 | 947.8 ms | 0.046 mm |
| 2 | 82,981 / 91,303 | 72,245 | 971.6 ms | 0.072 mm |
| 3 | 91,950 / 91,619 | 69,196 | 243.8 ms | 0.020 mm |
| 4 | 90,862 / 96,822 | 68,759 | 926.9 ms | 0.044 mm |
| 5 | 92,000 / 91,797 | 68,693 | 266.0 ms | 0.034 mm |

- The two machines run identically for a while, then drift apart. At seeds 3 and 5 they diverge
  before the 500 ms stimulus. So a Mac test paired with a backhouse control would have failed the
  scorer's match check. Keeping each seed on one machine was necessary.
- After they diverge, the runs differ by as much as two seeds do. Total spikes differ by up to
  10%, and the body ends within 0.07 mm.
- Why they diverge is not tested. Candidates (inferred): floating point on arm64 against x86,
  different numpy and BLAS builds (Python 3.12.14 against 3.12.3), and the renderer (Apple GL
  against osmesa) if the eyes feed back into the brain in closed loop.

**m9r library: results** (scored 6 October 2026 at 00:45 CDT; `runs/app/lib-m9r-seeds/scores.json`).
The same six protocols at seeds 0 to 9, run as the fly worker's working profile m9r, with the noise
rule declared at 02:10. Every number is derived from the recordings by `score_library.py`.
- **Provenance:** 60 runs, all exit 0, all on backhouse (6 at a time, 22:01 to 22:57 CDT on 5
  October), all at commit 4723e1b. Profile m9r as folded at `main` 019dae2, with no override:
  every manifest records `force_per_spike` 10 (guessed) and profile status "adopted (working
  profile)".
- **Matched:** at every seed, every test's spike train is identical to its control's until the
  stimulus.
- **No expectations were written for m9r before these runs.** The m9 expectations of 02:10 are the
  only ones on record, so nothing below is a confirmed prediction.

Per seed: the test minus the same seed's control, with the same seed's one-cell sham in brackets.

| Seed | Machine | Sugar GRN: MN9, Hz | MDN: forward, mm | DNa02: left turn, deg | Leg sugar: MN9, Hz |
|---|---|---|---|---|---|
| 0 | backhouse | +13 (0) | +0.008 (0.000) | +0.40 (-0.25) | 0, no spike changed |
| 1 | backhouse | +12 (0) | +0.005 (+0.007) | +0.25 (-0.61) | 0, no spike changed |
| 2 | backhouse | +10 (0) | +0.001 (-0.002) | +1.03 (+0.30) | 0, no spike changed |
| 3 | backhouse | +11 (0) | +0.002 (+0.001) | +0.65 (-0.03) | 0, no spike changed |
| 4 | backhouse | +13 (0) | +0.007 (0.000) | +0.65 (-0.02) | 0, no spike changed |
| 5 | backhouse | +9 (0) | +0.001 (+0.001) | +1.16 (0.00) | 0, no spike changed |
| 6 | backhouse | +10 (0) | +0.005 (+0.005) | +0.68 (-0.18) | 0, no spike changed |
| 7 | backhouse | +8 (0) | +0.008 (+0.002) | +0.35 (-0.03) | 0, no spike changed |
| 8 | backhouse | +13 (0) | 0.000 (+0.003) | +0.53 (-0.09) | 0, no spike changed |
| 9 | backhouse | +12 (0) | +0.003 (+0.002) | +0.35 (-0.56) | 0, no spike changed |

On the mean of the 10 seeds, side by side with m9:

| Test | Criterion | m9r mean (SD) | m9r sign-flip p vs shams | m9r on the mean | m9r single trials | m9 mean (SD), verdict |
|---|---|---|---|---|---|---|
| sugar-grn-kick | MN9 +5 Hz or more | +11.1 Hz (1.8) | 0.001 (1 of 1,024) | PASS | 10 of 10 | +8.8 Hz (2.2), PASS, 9 of 10 |
| mdn-cschrimson | forward -0.5 mm or less | +0.004 mm (0.003) | 0.94, within noise | FAIL | 0 of 10 | -0.015 mm (0.033), FAIL, within noise |
| dna02-left | left turn +5 deg or more | +0.61 deg (0.30) | 0.001 (1 of 1,024), beyond noise | FAIL, below threshold | 0 of 10 (seeds 1 and 9 within noise) | -0.30 deg (1.50), FAIL, within noise |
| sugar-patch-legs | MN9 +5 Hz or more | 0.0 Hz (0.0) | 1.0 (10 pairs) | FAIL, no spike changed | 0 of 10 | 0.0 Hz, FAIL, no spike changed |

- **Sugar GRN to MN9 is stronger in m9r:** +11.1 Hz against +8.8 Hz, and it passes at every
  seed. The shams leave MN9 silent at every seed, as in m9.
- **DNa02 gives a small, consistent left turn in m9r, far below the threshold.**
  - All 10 seeds turn left, by +0.25 to +1.16 deg. Test minus sham is positive at all 10 seeds
    (+0.37 to +1.16 deg), so the mean is not noise by the declared rule.
  - The mean, +0.61 deg, is an eighth of the 5 deg threshold, so the test fails.
  - In m9 the same test was within noise (-0.30 deg, SD 1.50).
  - Why m9r turns at all is not tested. A candidate (inferred): m9r's body moves much less at
    rest, so a small leg torque from DNa02 shows above a smaller background.
- **MDN does nothing to the body in either model.** m9r's forward change is +0.004 mm against a
  0.5 mm backward criterion, within noise.
- **The stimulated cells fire about as in m9:** DNa02 at 10.0 Hz (SD 0.24; m9 9.7) and MDN at
  23.5 Hz (SD 0.34; m9 22.3), against 0 Hz in the control.
- **m9r's network and body are much quieter after a perturbation** (measured: cells whose rate
  changes by 1 Hz or more from 500 to 1,500 ms, up plus down, over the 10 seeds):

  | | m9r | m9 |
  |---|---|---|
  | One-cell sham | 198 to 406 cells | 1,187 to 2,714 cells |
  | MDN test | 144 to 387 | 635 to 2,702 |
  | DNa02 test | 166 to 388 | 774 to 2,695 |
  | Sugar GRN test | 501 to 1,939 (median 655) | 1,460 to 2,956 (median 2,796) |
  | Control thorax, forward over the window | -0.016 to -0.004 mm | -0.066 to +0.012 mm |
  | Control turn over the window | -0.52 to +0.41 deg | -1.52 to +0.36 deg |

  The control fires more spikes in the window in m9r (about 54,000 against 45,000 to 52,000), yet a
  one-cell kick spreads to about a seventh as many cells (medians about 300 against 2,200). This fits m9r's fly lying still at rest
  (`main`'s F-STAND-3; inferred, not tested), so less body feedback reaches the brain.
- **m9r against m9 directly** (post hoc, not declared before the runs). The seeds share kick draws
  but not models or, at seeds 0 to 5, machines. So the 10 runs of each model are treated as two
  independent samples, with an exact two-sided permutation test over all 184,756 splits:
  - sugar +2.3 Hz, p = 0.024;
  - DNa02 +0.90 deg, p = 0.079;
  - MDN +0.019 mm, p = 0.096.
  - A seed-paired sign-flip test gives sugar p = 0.043. Only the sugar difference reaches 0.05
    either way, and it is one of three tests chosen after viewing.
- **The fold changed nothing in these recordings** (measured). The pre-fold attempt
  (`lib-m9r-prefold-afb666c`, `force_per_spike` 1 for 71 leg motor neurons) was copied to the
  Mac and compared, chunk by chunk, with the folded library. 25 complete runs and the first 500 ms
  of the 5 stopped ones are byte-identical: spikes, voltages, torques and body positions. Over
  these 2 s runs, none of those 71 leg motor neurons reaches the body (inferred: they do not
  fire).

**Compare tab: models side by side** (built 6 October 2026, 01:00 CDT;
`app/web/js/models.js`; screenshot `docs/media/app_compare_m9r_vs_m9.png`, sugar GRN seed 0, m9r
beside m9).
- **Where it appears:** in the Compare tab of any run in a scored library, under "Across models".
  A picker sets the run's library beside another library holding the same protocol, other
  models first. The URL keeps the pick (`cmp=<library>`).
- **What it shows,** all read from each library's `scores.json` (`score_library.py`) and
  manifests through the catalogue:
  - per seed, the test minus control with the sham in brackets, this run's seed in bold;
  - the mean (SD), the sign-flip p against the shams, the verdict and the seeds meeting the
    criterion;
  - the stimulated cells' rate, the machines and the commits;
  - a library's `NOTE.txt`, as a warning (the pre-fold folder has one).
- **Computed in the page:** only the difference of the means, with the exact two-sided
  permutation test, labelled post hoc. For sugar it gives p = 0.024 (4,458 of 184,756 splits),
  as the Python check did.
- **What differs between the models** comes from the `inventory.csv` each run wrote, at the same
  protocol and seed. That is the record of the values the run's build asked for, so it holds for
  the m9 runs made before `record.py` wrote profile values into manifests. For sugar seed 0
  (921 values in m9r, 889 in m9), 7 values differ:
  - `force_per_spike` for all motor units: 10 against 1 (both guessed);
  - the jump muscle's peak torque: 90 uN*mm (inferred) against 100 (guessed);
  - the b1 to b3 wing motor neurons: wing yaw against wing roll;
  - four afferent class counts, all with status measured: campaniform sensilla 13 against 86,
    chordotonal organ 392 against 409, hair plate 78 against 113, mechanosensory bristle 1,764
    against 1,874.
  - 35 values are only in m9r's build. They include torque per spike for the non-leg motor
    units (abdomen, head, proboscis, wing, haltere, antenna), leg damping and rest mirroring, a
    folded wing pose, and mechanosensory afferents assigned by nerve (42 moved to their own leg,
    248 excluded from leg drive). The last may explain the changed afferent counts (inferred,
    not checked).
  - 3 values are only in m9's build: the DLMn and DVMn wing roll maps and a combined wing pitch
    map, which m9r splits.
- **Limits:**
  - The diff reads one run per library. Earlier checks found the inventories the same across
    seeds and protocols within each library.
  - Only folders with scored trials appear in the picker.

**M3: fly's-eye view.** Eye readouts to the hex mosaic, retinotopic photoreceptors, the derived
column table for L/Mi/Tm/T4/T5, LPTC traces; visual worlds when request 5 lands.

First cut built 4 October 2026, evening: `app/build/eye.py` writes each body's eye geometry
(flyemu-eye/1: the 721 ommatidium centroids per eye from flygym's ommatidia map, the model's
per-eye pale/yellow masks from `flyemu.vision.connectome_pale_masks`, and 6,026 photoreceptor
cells with an ommatidium from `data/derived/retinotopy.csv`, all derived). The Eye tab draws both
mosaics shaded by the recorded readout at the current time; clicking an ommatidium lists its
photoreceptor cells and highlights them on the brain map. Observed in the first library's
control at 1 s: the white sky reaches 1.0, the renderer's own ceiling (43 % of readouts in that
run; the recorder's uint8 scale loses nothing), and the horizon tilts with the fallen body.
A photoreceptor's inspector row links to its ommatidium. The tab states an assignment check
(derived from `data/derived/retinotopy.csv`, the fly worker's file): a real lamina cartridge
receives 6 R1-R6 terminals (neural superposition, measured anatomy), but the assignment gives 1
to 61 per ommatidium (mean 5.4 over the 629 ommatidia with any; exactly 6 in 19; 202 have one).
So the counts average out, while single ommatidia are poorly resolved; worth the fly worker's
attention if retinotopic precision matters for motion vision.

**M3, second part: the column table and motion-sensing traces** (6 October 2026, 01:00 to
01:30 CDT; screenshots `docs/media/app_eye_columns.png` and `docs/media/app_eye_traces.png`).

- **Column placement** (`app/build/columns.py`, writes `app/data/body/flybody/columns.json`,
  flyemu-columns/1, 1.6 MB, 2 s to build). The scan has no column labels for these cells, so
  the placement is derived from connectivity:
  - photoreceptors sit at their ommatidium (eye.json, itself derived topology with an inferred
    global alignment);
  - every L1-L5, Mi1, Tm3, Mi4, Mi9, C3, Tm1, Tm2, Tm4, Tm9, T4a-d and T5a-d cell takes the
    synapse-weighted mean position of its placed inputs (edges of 3 or more synapses), in the eye
    giving it the most placed input, iterated until nothing moves by 0.01 spacing (185
    iterations). The anchors stay fixed, so this is a weighted harmonic extension of the
    photoreceptor map.
  - Result: 37,763 cells placed. Every type is placed in full except L3 (1,452 of 1,772), L4
    (1,255 of 1,770), Tm9 and T5a (short by 2 and 1); the rest have no placed input. 288 (L4,
    left eye) to 456 of each eye's 721 columns hold a cell of a given type; the median is 1 cell
    per occupied column (L1 and Tm3: 2; Mi1: 1.5). Hops from a photoreceptor: median 1 for L1,
    L3, Mi1 and Mi4; 2 for the rest of the lamina and medulla and for T4; 3 for T5. That follows
    the circuit, except L2 (2 hops; see the scan observation below).
- **Checks, not used for placing** (derived):
  - every placed cell lands in the eye of its annotated soma side (all 22 types, 100 %);
  - a cell's 6 nearest cells by soma position (measured) lie within 2 column spacings of it in
    the mosaic for 0.39 (C3) to 0.66 (L5) of pairs, against 0.03 to 0.06 with the placements
    shuffled within the type. So the placement is retinotopic at the scale of a few columns.
- **Its limit:** a weighted mean cannot put a cell beyond the photoreceptors it reads. Cells past
  the edge of the photoreceptor map stack on edge ommatidia (left 700 to 715, right 0 to 28): up
  to 22 cells of one type on one ommatidium, against one per column in a real eye (T4/T5: one of
  each subtype). R1-R6 per ommatidium and L1 per ommatidium correlate only weakly (Spearman 0.24
  left, 0.46 right). Columns without assigned photoreceptors stay empty. A fit to the full
  hexagonal lattice (one cell per type per column) would fix the pile-ups; not done.
- **Scan observation for the fly worker** (measured synapse counts, `male_cns_edges`): L2 receives
  a median of 2 synapses from the assigned photoreceptors, against 16 for L1 and 13 for L3; 861
  of 1,779 L2 have any photoreceptor edge of 3 or more (L1: 1,352 of 1,776). In real lamina
  cartridges L1 and L2 are both postsynaptic at nearly every R1-R6 tetrad synapse (literature,
  Meinertzhagen and O'Neil 1991; not checked here), so this looks like how the scan's lamina was
  traced. It matters for the model: L2 feeds the OFF pathway (Tm1, Tm2, Tm4 to T5).
- **The Eye tab now has:**
  - the column table: per type, the model's mode (graded or spiking, read from the run's
    inventory with its status), placed of scan, columns per eye, cells per column, the soma
    check, cells fired, mean rate and the watched cells' mean voltage now. Clicking a type draws
    its cells on the mosaic (watched ones coloured by voltage), lights them on the brain map, and
    lists hops, input share and spread;
  - clicking an ommatidium also lists the columnar cells placed on it;
  - motion-sensing traces, synced to the clock: per type from photoreceptor to T4/T5, then every
    lobula plate tangential type (HSE, HSN, HSS, H1, H2, VS, VSm, HST, VST1, VST2) per side. A row
    shows the watched cells' mean membrane potential if any are watched, else the spike rate over
    all cells of the type; a graded type with no recorded voltage says so instead of drawing a
    flat line. Clicking sets the time;
  - the side panel widens to 600 px on this tab; `etype=<type>` and `scroll=<element id>` in the
    URL select a type and scroll the panel, for screenshots.
- **What the library control shows** (`lib-m9r-seeds/control-s0`, measured): no cell in the table
  fires. Of 44,738 cells, 11,418 are graded in the model (R1-R6, R7, R8: measured basis; L1-L3:
  inferred) and cannot spike, and the library control records none of their voltages. Every
  spiking type downstream, L4 and L5 to T4/T5 and every tangential cell, has 0 spikes in 2 s.
  Across the optic lobe 28 of 89,394 intrinsic cells fire. The scene holds no moving stimulus
  (request 5 is on hold), so the motion cells would be expected quiet; the question is whether
  anything reaches them at all.
- **A watched control** answers that. `app/tools/eye_watch.py` writes
  `app/protocols/eye/control-watch-visual-m9r-s0.json`: the library control at seed 0 with 681
  cells' membrane potential recorded at 1 kHz. Those are 194 photoreceptors and 397 columnar cells
  of a patch of 19 left-eye ommatidia around ommatidium 298 (about one cell per type per
  ommatidium, as placed), plus every tangential cell and the control's watch list (90). Run on
  backhouse (m9r, 4723e1b), 01:10 to 01:21 CDT, 642 s, exit 0. Measured:
  - watching changes nothing: 106,287 spikes, identical to `lib-m9r-seeds/control-s0`, and
    identical body positions;
  - mean voltage after the first 200 ms (every cell starts at -52 mV): R1-R6 -49.0, R7 and R8
    -43 to -48; L1 -55.3, L2 -56.3, L3 -53.4 (photoreceptors depolarise and the lamina monopolar
    cells hyperpolarise in light, the signs seen in flies); Mi1 -52.7, Mi4 -53.4, Mi9 -52.2,
    C3 -51.9; L4, L5 and Tm1 to Tm9 about -52.0; T4a to T4d -52.00 with no variation at all;
    T5a to T5d -52.01 to -52.03;
  - each photoreceptor follows its ommatidium's luminance (median correlation 0.51, n = 194). The
    patch straddles the horizon after the fall: of its 19 ommatidia, 6 see sky and 11 see floor
    (mean luminance after 200 ms above 0.8 or below 0.4), and the centre ommatidium varies between
    0.24 and 0.38. Per photoreceptor, the luminance varies by a median 0.05 and the voltage by
    0.4 mV. (Corrected at 01:46 CDT: this line first said the patch looks at sky near the renderer's
    ceiling, mean luminance 0.988; that figure came from the first frame only.)
  - **Reading** (inferred; corrected below under "The discriminating run": the signal stops one
    stage earlier, at the L1-L3 output): the light signal enters at the graded photoreceptors and L1 to L3 and
    stops at the first spiking stage. The medulla cells spike by the model's default (guessed),
    and the optic-columnar graded switch is 0 in m9r (guessed); the lamina input moves them by
    under 1.5 mV, far from threshold, so T4 and T5 receive nothing. In flies Mi1, Tm3, Tm1 and Tm2
    respond with graded potentials (Behnia et al. 2014; literature, not checked here), so the
    spiking default is likely the wrong mode for them. A note for the fly worker, not a change
    the app makes.
  - **The tangential cells' only activity is an internal rhythm**, not vision (measured). Right
    HSE, HSN, H2 and HST show 25 hyperpolarising dips of 2 to 3 mV in 2 s; on the left, HSE, HSN
    and HST show 6. Each dip follows within 6 ms a spike of Am1 on that side (25 of 25; 6 of 6).
    Am1 is one GABAergic optic-lobe cell per side (predicted transmitter) and gives 80 to 153
    synapses to each HSE, HSN and HST cell (H2: 26 and 39; HSS, which shows no dips: 13 and 4).
    It is the only spiking input to HSN R among its 858 inputs of 3 or
    more synapses. Am1 R fires every 76 ms (about 13 Hz). It fires in lockstep with MeVPOL1 L
    (cholinergic, 396 synapses onto Am1 R), MeVC11 L and Pm11 R. Octopaminergic OA-AL2i1 R (121
    synapses) fires at twice that rate. Where this rhythm starts is not checked. The 0.1 to 0.3 mV
    ripples in C3, Tm2 and other medulla rows look, by eye, to share its period; also not checked.
  - **Next discriminating experiment** (proposed at 01:30, run at 01:44; see the next block): the
    same watched control with the medulla cells graded, run as a labelled variant, and a second
    patch at the horizon where the scene has contrast. If the mode is the
    block, Mi1, Tm3, Tm1 and Tm2 follow L1 and L2, and T4 and T5 move. Direction selectivity
    needs moving stimuli (request 5, on hold); until then the only image motion is the fly's own.

**The discriminating run: graded medulla (6 October, 01:35 to 02:05 CDT, before M4).** The
Director asked for it ahead of M4, with the graded cell types taken from recordings, not guessed.

- **Which cells are graded** (`app/protocols/eye/variant_graded_medulla.csv`, every row measured,
  from whole-cell recordings in Drosophila): Mi1, Tm3, Tm1 and Tm2 (Behnia et al. 2014); Mi4, Mi9
  and C3 (Groschner et al. 2022); T4 (Gruntman et al. 2018); T5 (Gruntman et al. 2019). 26,276
  cells across both optic lobes. Tm4 and Tm9 have only calcium imaging (Serbe et al. 2016;
  Strother et al. 2014 is also imaging), which cannot tell graded from spiking, so they stay
  spiking. A literature agent compiled the list from abstracts and summaries, not full texts
  (confidence medium; the rows say so). The rows enter through the model's own
  `$FLYEMU_EXTRA_PARAMS` (`flyemu.params.load`); `record.py --extra-params` or
  `config.extra_params` sets it, the manifest keeps the rows and their md5, and the status reads
  "adopted profile with extra per-type rows: custom, not validated". The Run tab lists the rows.
  No model file changes.
- **The horizon patch.** The first patch (ommatidium 298) already straddles the horizon after the
  fall (6 sky ommatidia, 11 floor; the correction above), and among the patches with at least 5
  of each it has the most watched cells, so the same patch serves.
- **A finding from the existing control, before the run** (measured, m9r watched control,
  200 to 2000 ms): L1, L2 and L3 never rise above rest (-52 mV) in any watched cell (max -52.58,
  -52.01, -52.25 mV). The model's graded rule transmits at a rate proportional to
  (V - V_rest)/(V_th - V_rest), clipped to 0 to 1 (`flyemu.lif`), so a graded cell at or below
  rest transmits nothing. Light hyperpolarises L1-L3 (the sign seen in flies), so their output is
  zero all run. The light signal therefore stops at the L1-L3 output, one stage before the
  spiking medulla. In flies the lamina cells release transmitter tonically and light reduces the
  release (ON cells such as Mi1 respond through that decrease); the rule cannot represent a
  decrease from zero. This is a model-code question for the fly worker, noted, not changed here.
- **Runs** (`app/tools/eye_sweep.py`, protocols committed with their predictions at aab8b75 before
  any run; 14 runs at seed 0, 2 s each, same watch list as the control; backhouse, 7 at a time):
  - A, the variant control.
  - A, moving bars injected as current, because the scene has no moving stimulus. An ON bar is
    +4 mV into Mi1, Tm3, Mi4 and C3 and -4 mV into Mi9 under the bar (the T4 inputs, with the
    polarity each shows to light: Behnia et al. 2014; Strother et al. 2017, calcium imaging). An OFF bar is +4 mV
    into Tm1 and Tm2 (T5 inputs). 4 mV is guessed, inside the 7 mV graded range. The bar is 7
    columns long, steps one column every 50 ms and holds each cell 100 ms, sweeping 11 columns
    across the patch, twice per run (300 and 1100 ms), in 4 directions. Front-to-back on the left
    eye is mosaic -x and upward is -y (fit of the retinotopy table's azimuth and elevation near the
    patch, -10.1 degrees azimuth and -9.2 degrees elevation per column spacing; inferred).
  - B, the variant with a tonic +7 mV into every L1, L2 and L3 (a guessed operating point, so
    the lamina output sits mid-range and light can lower it): a probe of the rule above, not a
    claim about flies. B control, plus a photoreceptor ON bar (+3 mV into R1-R6, R7 and R8 of
    the ommatidia under the bar, guessed) in 4 directions.
- **Predictions** (written before the runs, in each protocol's `expect`):
  - A control: T4/T5 stay flat, because L1-L3 transmit nothing whatever the medulla's mode;
  - A bars: T4 (ON) and T5 (OFF) depolarise; direction selectivity weak or absent
    (|DSI| < 0.2), because injected current lacks the inputs' measured temporal filters, which
    are thought to set direction selectivity in flies;
  - B: L1-L3 transmit; T4 respond more than T5 to an ON bar; direction selectivity weak or absent.
- **Analysis** (`app/tools/eye_ds.py`, written before the results): for each watched T4/T5 cell,
  the response is the change in potential against the arm's own control (which shares every
  random draw), averaged over both sweeps. DSI = (R_pref - R_null)/(|R_pref| + |R_null|) per
  cell, with the preferred direction from flies (Maisak et al. 2013: T4a/T5a front-to-back, b
  back-to-front, c upward, d downward). The test is a two-sided Wilcoxon signed-rank test across
  the about 18 cells per subtype, Holm-corrected within each set of bars.
- **Results** (measured unless labelled; numbers in `runs/app/eye/graded-summary.json`; figure
  `docs/media/app_eye_ds.png`; screenshots `docs/media/app_eye_graded_traces.png`, the Eye tab
  during an ON sweep, and `docs/media/app_run_variant.png`, the Run tab's variant rows):
  - **Checks.** All 14 runs completed (about 330 s each). Every bar run is identical to its arm's
    control before the first bar at 300 ms, in every watched voltage and every spike, so what
    differs afterwards comes from the bars.
  - **A control: T4 and T5 stay flat, as predicted.** T4a to T4d and T5a to T5d sit at -52.00 mV,
    varying by 0.002 to 0.004 mV (SD over time). L1-L3 still transmit nothing. 106,681 spikes
    (m9r control: 106,287).
  - **A ON bars: T4 respond, T5 do not.** Under the bar the T4 inputs rise 3.3 to 5.3 mV, and each
    T4 cell peaks a median 1.7 to 2.0 mV above control (per subtype and direction, 17 or 18 cells
    per subtype). T5 peak under 0.05 mV.
  - **A OFF bars: T5 respond, T4 do not.** Tm1 and Tm2 rise 3.1 to 3.4 mV; T5 peak 1.2 to 1.4 mV;
    T4 under 0.02 mV. The ON and OFF pathways separate as in flies.
  - **The responses are local.** A cell's peak time follows its position along the sweep
    (Spearman |rho| 0.90 to 0.96, 71 to 74 T4 or T5 cells per run; Mi1 0.93 to 0.96), so the
    wiring and the column placement carry the retinotopy.
  - **A: not direction-selective.** T4, pre-registered DSI (window mean): -0.02 to +0.03 per
    subtype; the smallest Holm p (0.042, T4c) has the sign opposite to flies. T5: the
    pre-registered DSI is -0.71 to +0.56, which breaks the prediction for T5a and T5b, but it is a
    ratio of differences under 0.04 mV between window means near zero (the rise under the bar and
    the dip after it cancel), and every T5 subtype responds most to downward bars, which points to
    the stimulus or placement rather than the subtype. On the peak (post hoc) |DSI| is at most 0.02
    for every T4 and T5 subtype.
  - **B: L1-L3 transmit, but the ON medulla cells sit below rest.** With +7 mV the lamina output
    is mid-range (mean output 0.49, 0.21 and 0.47 of maximum for L1, L2, L3). That tonic input holds
    Mi1 at -55.5 mV, Tm3 -54.0, Mi4 -54.1 and C3 -53.2, below rest, so they pass nothing on; Mi9
    and Tm4 sit above rest (-50.7). T4 sit 0.8 to 0.9 mV below rest, T5 1.0 to 1.4.
  - **B photoreceptor ON bars.** Light lowers L1-L3 by a mean 0.24 mV (L3 0.05). Mi1 depolarises
    (peaks +1.1 to +1.5 mV, retinotopic, |rho| 0.46 to 0.74): the ON sign of flies, through less
    inhibition from L1. It stays below rest, so it transmits nothing. T4 peak 0.04 to 0.20 mV and
    T5 0.12 to 0.35 mV (weakly retinotopic, |rho| 0.22 to 0.60), so the prediction that T4 respond
    more than T5 fails.
  - **B: not direction-selective.** The window means (0.002 to 0.01 mV) are too small for a ratio.
    On the peak (post hoc) DSI is -0.20 to +0.15 per subtype and consistent across cells, but all
    four T4 subtypes prefer the same directions (back-to-front and upward), whichever direction
    each prefers in flies; T5 the same, weaker. That is a property of the stimulus or placement,
    not tuning.
  - **Reading** (inferred): T4 and T5 can respond, locally and with the fly's ON/OFF split, once
    their inputs are graded and driven. The wiring alone, with inputs that all share the same
    dynamics, gives no direction selectivity. In flies it is thought to come from the inputs'
    different temporal filters: fast Mi1 and Tm3 against slower Mi4, Mi9 and C3 (Arenz et al.
    2017; Groschner et al. 2022; literature, not checked here). The model has no such differences
    between graded cells. Separately, the graded rule's cut-off at rest blocks the lamina output in
    the model as it stands, and in B blocks the ON medulla cells. Both are model questions
    (section 13, requests 7 to 9).
  - **Next discriminating experiment** (proposed at 02:02, not run): arm A again with the slow
    inputs (Mi4, Mi9, C3) given a delayed, smoothed copy of the bar (delay 30 to 50 ms, guessed),
    standing in for their measured filters. If T4 then become direction-selective with each
    subtype's sign from flies, the wiring carries the direction information and the missing piece
    is the filters; if not, the wiring or the placement is at fault. Not to be run by the app
    (Director, 6 October): the fly worker builds the dynamics as model rungs, and the test in
    section 13.1 is their held-out check.

**The T4/T5 direction test: validation (6 October, 02:12 to 02:51 CDT).** `app/tools/t4t5_ds.py`
(section 13.1) run twice on backhouse at commit a73e966 (`~/flyapp/bh_t4t5.sh`, 7 at a time,
under `timeout 90m`), outputs collected to `runs/app/t4t5/`. Expected before the calls: the
variant reproduces the graded-medulla runs and fails; plain m9r gives no response.

- **m9r with the graded-medulla rows** (`m9r-graded-variant`; figure
  `docs/media/app_t4t5_variant.png`). FAIL, both sets.
  - **Reproduction** (measured): the control and the 8 medulla bar runs are identical, spike for
    spike, to the graded-A runs of the discriminating run (md5 of every spike; 106,681 spikes in
    the control). The fixed stimulus files and the harness give the same runs as the
    hand-written protocols.
  - **Medulla bars:** T4 respond to ON bars (median peaks 1.7 to 2.1 mV) and T5 to OFF bars (1.2
    to 1.4 mV), 0 of 8 selective: DSI -0.02 to +0.02, Holm p 0.36 or more.
  - **Photoreceptor bars:** no response in any subtype (T4/T5 peaks under 0.01 mV). The
    photoreceptors follow the bars (R1-R6 +2.3 mV ON, -2.4 mV OFF) and L1 and L2 invert them
    (about 2.5 to 3.0 mV), but L1-L3 sit 3 to 5 mV below rest and cross it in at most 0.2% of
    samples, so the graded rule passes nothing on (request 7).
  - 17 runs, 342 to 431 s each, 20 minutes for the set.
- **Plain m9r** (`m9r`, the profile as adopted at a73e966). FAIL, both sets: no response in any
  subtype (T4/T5 peaks 0.00 mV), as expected.
  - **Medulla bars:** the injected inputs move by their 4 mV (Mi1, Tm3, Mi4, C3 +3.8 to +4.0 mV,
    Mi9 -3.9 mV, Tm1 +4.0 mV, Tm2 +3.2 mV) but in m9r they are spiking cells: rest -52 mV,
    threshold -45 mV, and the watched Mi1 and Tm1 peak at -48 mV. Not one spike changes: every
    medulla bar run has exactly the control's 70,552 spikes in the sweep windows (measured). The
    medulla set is built for graded inputs, as flies' are (section 14, "The discriminating run");
    with spiking inputs it reads "no response" because the 4 mV (guessed) is below threshold. A
    rung that keeps these cells spiking fails it for that reason, and the amplitude is not to be
    raised to pass.
  - **Photoreceptor bars:** as in the variant up to the lamina (R1-R6 +2.3 / -2.4 mV, L1 and L2
    inverted by 2.6 to 3.0 mV). Mi1 and Mi4 move by 0.3 to 0.5 mV, Tm1 to Tm9 and C3 not at all.
  - 17 runs, 342 to 416 s each; 19 minutes for the set (02:32 to 02:51).

**M4: fidelity and body selection.** Profiles and switches with labels and status; flybody vs
NeuroMechFly (request 1); inventory and ledger panel per run. Built 6 October (commits 1daa3ac
and 5989464, then 2981fdd and d63adbb after merging `main`); screenshot
`docs/media/app_fidelity.png`, from the rebuilt tables.

- **The model's construction tables, as the app reads them.** `app/build/fidelity.py` writes
  `app/data/model/fidelity.json` through the model's public functions (`flyemu.model_data.load`
  and `construction_state`, `flyemu.profiles`): 72 mechanisms (27 body, 8 internal state, 34
  nervous system, 1 development, 2 infrastructure) with their status, switch keys, neutral values
  and tests; the 685 unknowns with their biological bounds and labels; 105 structural rows; the
  23 profiles with the status the recorder gives each (working m9c, regression m4); and the scans
  and bodies, each saying whether the recorder can run it and if not, why. Counts are from the
  rebuild after merging `main` 81e7afa (684, 101 and 22 before). It records the tables' commit and
  md5s and whether they were modified. Rerun it after the model changes; the server's catalog links the
  file.
- **The Fidelity tab** (one per run), from two sources kept apart: the run's own inventory (every
  value the model's build asked for, with its basis, written at record time) and the tables above.
  - **Configuration:** the run's profile and status, its overrides and variant rows; the scans and
    bodies it did not use, with the reason each cannot be run (BANC, FAFB, MANC and hemibrain: no
    simulation; NeuroMechFly: request 1, on hold). A warning when the run's model commit is not the
    tables' commit.
  - **Configure a run:** profile (newest first, with status), body, scan, and the 75 switch keys
    without wildcards (those named by a mechanism and the structural table's switch rows, where
    most profile additions live), each with the profile's value or the registry default. "Set in
    the Session tab" writes these into the Session protocol, which is checked there and can be
    started. Wildcard keys can be typed into the protocol's overrides.
  - **This run's values by evidence:** counts by basis per subsystem. **Biological bounds:** each
    numeric value against the range of every table row that owns its key. **Construction ledger:**
    the model's counts by tier. **Mechanisms and switches:** filterable by status, tier and
    "switched in this run". **Values in this run:** searchable, each with its owning row and range.
    **Profiles:** the table, and the differences between any two (by default the run's profile and
    the one defined before it).
- **Checks the server now makes.** The protocol check (and so a session start) refuses a profile
  the model does not define, a body or scan the recorder cannot run, and an override key that no
  construction table owns (a mistyped key would otherwise give a run identical to its profile
  under a "custom" label). It reports the status the run will be recorded with.
- **A labelling fix.** `record.py` labelled m4 with overrides "regression reference". A named
  profile with overrides or extra rows is now "<name> (<its status>) with overrides: custom, not
  validated". The rule lives in `app/server/status.py`, shared by the recorder, the check and the
  build; a test holds the page's copy to it. No recorded run was mislabelled (checked over all 284
  manifests on the Mac): the m9 runs were recorded while m9 was the working profile, and the one
  m4 run with overrides is a converted legacy recording, labelled as such.
- **Results** (measured, on the graded-variant control, `eye/graded-A-control-m9r-s0`): 925 values
  in its inventory: measured 14, derived 33, inferred 170, guessed 663, absent 28, no basis 17.
  612 numeric values have a declared range, and none is outside it. From the model's own ledger,
  two m4 values are outside their bounds (`b3_k_pro_retpro` and `b3_k_meta_retpro`, 1.0 each); the
  tab shows them.
- **Found in the model's data:** `data/model/mechanisms.yaml` writes five fields as unquoted flow
  text containing commas (the names of B1, B3, N22 and N25 and the notes of B6), so a YAML reader
  cuts them at the comma. The build rejoins the pieces in order and marks each one in the tab
  (request 10).
- **Tests** (`app/tests/test_fidelity.py`, 5): the tables match the model's; the split fields are
  rejoined; the page's owner join matches `model_data.owners` on every table key; the page's
  status and the check's equal the recorder's; the check refuses the four bad cases above.
- **Not built in M4.**
  - Choosing NeuroMechFly: listed, not selectable, until `Organism` takes a body choice (request 1,
    on hold).
  - Toggling a layer off and choosing between alternative completions (section 5.1): that needs
    completions recorded side by side, which no run does yet.
  - Colouring the brain map by parameter basis: the inventory is per type or class, not resolved
    per cell.
  - The installable-app parts (downloads, import and export of configurations beyond the protocol
    file).

**M5: other scans.** BANC, FAFB, MANC and hemibrain atlases; the cross-specimen comparison view;
simulation on other scans when request 6 lands.

**M6: many flies.** Batch protocols on backhouse from the app's queue; a gallery of individuals and
population views.

**M7: public release.** Curated gallery, landing page, attributions; Pages enabled by Ben.

**Installable app** (Ben's answer 4; folded into M4 to M6): on-demand download of connectome
bundles and recording libraries, import and export of run configurations, and environment
definitions for user runs.

**M8 (dropped for now, Ben's answer 4): in-browser simulation.** A WebGPU brain at a declared rung plus MuJoCo's WebAssembly
build for the body, admitted only if it matches the CPU reference spike for spike at that rung on
fixed seeds.

## 15. Risks and unknowns

- The model mostly stands still today (F-RHYTHM-1, F-REFLEX-1), so many interventions will show little
  movement. The app shows that plainly; it is not a reason to tune the model.
- Live speed limits what "interactive" means on the Mac (section 10).
- Neuropil meshes and per-neuron region data may need the existing neuPrint fetch path.
- The derived photoreceptor alignment and column assignment are inferences; their confidence is
  shown per cell.
- Cross-specimen simulation (FAFB + MANC) joins two animals of different sex; any result is labelled
  inferred and kept out of claims about one fly.

## 16. Questions for Ben (asked 4 October 2026; answered the same day)

Answers, in order: (1) research tool first; (2) the intervention mechanism first, then the fly's-eye
view; (3) show failures, labelled; (4) an installable local app with downloadable connectomes,
recording libraries and run configurations, no browser-only simulation for now; (5) all views
switchable, male CNS and FAFB at least, layers measured / inferred / completed with alternative
completions selectable, comparison across scans now; (6) "Fly Workbench" as the working name.

The questions as asked:

1. Research tool first or public showcase first? Default: research tool first (dense, labelled),
   with a guided tour added at M7.
2. After M1, optogenetics (live) or the fly's-eye view first? Default: optogenetics.
3. Show "not reproduced" results publicly beside the literature? Default: yes.
4. A lower-fidelity in-browser simulation for public visitors (M8)? Default: yes, later, behind an
   equivalence test.
5. Cross-scan: comparison only for now, or simulation on other scans as a priority? Default:
   comparison now, simulation when the model supports it.
6. Name. Default: "Fly Workbench".
