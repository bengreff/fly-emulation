# Fly workbench: design

**Status:** design written 4 October 2026, 16:45 CDT; Ben's answers recorded and milestone 1 (M1)
built at 17:20 CDT the same day, milestone 2 (M2: protocols, labelled optogenetics, replay of
interventions, a scored library) by 18:10 CDT, and M2b (the app checked against the model's own
sugar assay, live sessions, the protocol editor, a sham distribution) in the evening (section 14
says what each contains, with the results; `app/README.md` says how to run it). Owner: the app worker (branch `app`). The model is owned by the fly worker; the app reads it
only through public functions and asks for new ones (section 13, on hold).

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
recorded side by side; that is planned with the fidelity panel (M4).

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

- **Profiles:** m4 (regression reference), m7, m8, m9 (working), m10p and m10q (rung 2 candidates,
  not adopted), each shown with its status from `profiles.py` and HANDOFF.
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
3. **Columns downstream:** L1-L5, Mi1, Tm1-4, T4/T5 placed at a column derived from connectivity
   (each cell's dominant upstream column, iterated from the photoreceptors; derived, with a
   confidence per cell). This table may be useful to the model too and will be offered to fly.
4. **Outputs:** lobula plate tangential cells (HS, VS) and visual projection neurons (LC types) as
   rate traces.

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
- Library on m9 as the model owner fits it, with eight more shams (`runs/app/lib-m9/scores.json`,
  recorded and scored 4 October 2026, evening). Same protocols, seed 12, closed loop, the app's
  kicks, thresholds and windows. Three rules changed after the first library was viewed, and are
  labelled so: the override is gone, the readout drops incompletely traced cells, and the trials
  summary judges a mean. Every number is derived from the recordings.

  | Protocol | Criterion | Measured | Driven cells | 9 shams, same window (6 distinct) | Verdict |
  |---|---|---|---|---|---|
  | sugar-grn-kick | MN9_L minus control >= 5 Hz | +7.00 Hz (7 vs 0) | | all 0.00 | PASS |
  | sugar-patch-legs | as above | 0.00; no spike changed | | all 0.00 | FAIL, no spike changed |
  | mdn-cschrimson | forward minus control <= -0.5 mm | +0.04 mm | the 4 MDN 22 to 23 Hz, control 0 | -0.06 to +0.02 mm | FAIL within noise |
  | dna02-left | left turn minus control >= +5 deg | -0.15 deg | the left DNa02 19 Hz, control 0 (the right one, not driven, 0) | -1.0 to +2.9 deg | FAIL within noise |

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
    reset, so different cells funnel into a few trajectories. Across the shams the body moves
    -0.06 to +0.02 mm forward and turns -1.0 to +2.9 deg, and 786 to 2,604 cells change.
  - A second set of 8 shams with new cells and onsets 505 to 540 ms (rule added after the first
    set was seen): queued at 20:31 CDT behind other projects' jobs in the slot limiter; not yet recorded.

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
attention if retinotopic precision matters for motion vision. Not yet built: the column table,
LPTC traces.

**M4: fidelity and body selection.** Profiles and switches with labels and status; flybody vs
NeuroMechFly (request 1); inventory and ledger panel per run.

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
