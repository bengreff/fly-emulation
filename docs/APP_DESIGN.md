# Fly workbench: design

**Status:** design, 4 October 2026 (written 16:45 CDT). Nothing in this file is built yet except
`app/tools/bench_live_cost.py`. Owner: the app worker (branch `app`). The model is owned by the
fly worker; the app reads it only through public functions and asks for new ones (section 13).

## 1. What it is for

Ben, 2026-10-04: a public viewer "fully fleshed out instead of just a cartoon viewer, brain map and
interaction mechanisms etc, to replace our current viewer ... a research tool in itself where you can
select and mix and match bodies and brain scans and levels of fidelity". Also a fly's-eye view and
virtual optogenetics. Standing rules: a local web page or standalone app (not a Claude artifact);
behaviour realism over pretty graphics; public on GitHub with a static replay mode for GitHub Pages.

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
| `viz/index.html` (single file, three.js r128 from a CDN) | 3D body from the compiled geometry, tarsal load tint, follow camera; motor-neuron raster split into "reach a muscle" and "drive nothing"; joint-torque heat map with clipping marked white; whole-CNS rate trace | body rendering, the mapped/unmapped raster split, clipping disclosure, transport controls | no brain map, no neuron identity, no interaction; caveats hard-coded and now wrong ("every neuron shares one membrane time constant", "male-cns:v1.0 → NeuroMechFly" while the default body is flybody, "176,422 neurons" while the model runs 167,111 at ≥ 5 synapses) |
| `scripts/serve_viz.py` | serves the page plus one run's `replay_data.js` on 127.0.0.1 | the idea (no build step, localhost only) | one recording at a time; data as base64 inside a JS file (+33 % size, whole file parsed at once) |
| `scripts/record_organism.py` | runs the closed loop; writes `recording.npz` (full-rate qpos) and `replay_data.js` (200 Hz poses, torque, contact, MN spikes, whole-CNS rate) | the run loop shape | records motor-neuron spikes only, not the other ~166,000 cells; no eye, no stimuli, no voltages |
| `scripts/export_geometry.py` | compiled MuJoCo meshes to `viz/geometry.{bin,json}` (flybody: 272,550 triangles, 85 geoms, 13 MB, measured) | yes, generalised per body | written next to the page, one body only |
| `scripts/render_brain_body.py` | the m9 MP4 (`docs/media/m9_closed_loop.mp4`): body beside five class rate traces | as a video exporter | classes only; offline |

The ten recordings in `runs/organism-record-*` (0.7 to 2 MB each) predate m9; a converter keeps them
viewable (M1).

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
| Live session (step, pause, stimulate, branch) | no | yes, one at a time, 39 to 87 s of wall time per simulated second (measured, section 10) | yes over an SSH tunnel (cost not measured) |
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

One JSON file describes a whole experiment; the app's protocol editor writes it, the live server and
`run_protocol.py` execute it, and the recording embeds it.

```json
{
  "format": "flyemu-protocol/1",
  "config": {"scan": "male-cns:v1.0", "body": "flybody", "profile": "m9",
             "overrides": {"motor_unit:all|force_per_spike": 10}, "seed": 12,
             "min_synapses": 5, "start": "rest"},
  "duration_ms": 2000,
  "genotype": [{"effector": "TNT", "target": {"type": "DNg100"}}],
  "events": [
    {"t_ms": 500, "dur_ms": 1000, "kind": "opto", "effector": "CsChrimson",
     "target": {"type": "MDN"}, "irradiance_mw_mm2": 0.5, "pulse_hz": 0,
     "expression": {"fraction": 1.0}},
    {"t_ms": 0, "dur_ms": 2000, "kind": "taste", "site": "labellum", "tastant": "sucrose", "mM": 100}
  ],
  "record": {"watch": {"type": ["MDN", "MN9"]}, "eye": true, "web_hz": 200}
}
```

Targets: `bodyId` list, `type` (exact or regex), `class`/`superclass`, `side`, `roi`, or a named
driver-line preset (a published GAL4/split line resolved to cells with its source and an
"idealised expression" flag). Targets resolve once, at the start, and the resolved rows are saved.

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
- **Flow layout.** A second, 2D view places cells by side (x) and by synaptic distance from the
  sensory periphery (y, shortest path, derived), so a pathway such as sugar GRN -> GNG -> MN9 can be
  watched as a wave. Display-only; the caption says how it was computed.

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
| Kir2.1 | constitutive K+ leak; build-time | not available | extra leak conductance per cell (request 3) |
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

### 7.3 Warm starts and branching

Every run started from rest begins with a transient (the fall onto the legs, lockstep MN volleys;
`docs/media/m9_closed_loop.md`). A warmed-up snapshot avoids repeating it, and "branch from here"
lets a control and a stimulated run share the same past. Both need a snapshot and restore of the
whole organism (request 2). Until then, sessions start from rest and say so.

### 7.4 Held-out guard

Some interventions are held-out tests (HANDOFF register; `data/measurements/targets_session6.csv`
`use` column). The protocol editor marks a protocol that touches a held-out item, asks for
confirmation, and logs the run as spending it. The public intervention library contains only
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

## 11. Static mode (GitHub Pages)

`app/build/site.py` writes a self-contained site: the web app, the male-cns atlas, body bundles and
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

None blocks M1. In order of need:

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

**M1: replay workbench on the new format (replaces the viewer for replay).**
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

**M3: fly's-eye view.** Eye readouts to the hex mosaic, retinotopic photoreceptors, the derived
column table for L/Mi/Tm/T4/T5, LPTC traces; visual worlds when request 5 lands.

**M4: fidelity and body selection.** Profiles and switches with labels and status; flybody vs
NeuroMechFly (request 1); inventory and ledger panel per run.

**M5: other scans.** BANC, FAFB, MANC and hemibrain atlases; the cross-specimen comparison view;
simulation on other scans when request 6 lands.

**M6: many flies.** Batch protocols on backhouse from the app's queue; a gallery of individuals and
population views.

**M7: public release.** Curated gallery, landing page, attributions; Pages enabled by Ben.

**M8 (optional): in-browser simulation.** A WebGPU brain at a declared rung plus MuJoCo's WebAssembly
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

## 16. Questions for Ben (asked 4 October 2026; defaults in force until answered)

1. Research tool first or public showcase first? Default: research tool first (dense, labelled),
   with a guided tour added at M7.
2. After M1, optogenetics (live) or the fly's-eye view first? Default: optogenetics.
3. Show "not reproduced" results publicly beside the literature? Default: yes.
4. A lower-fidelity in-browser simulation for public visitors (M8)? Default: yes, later, behind an
   equivalence test.
5. Cross-scan: comparison only for now, or simulation on other scans as a priority? Default:
   comparison now, simulation when the model supports it.
6. Name. Default: "Fly Workbench".
