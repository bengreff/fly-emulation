# Fly Workbench

A local research app for the fly emulation: the body, every neuron of the scan on a brain map, the
recorded activity and the evidence behind each model value. Design and milestones:
`docs/APP_DESIGN.md`. Milestone 1 replays recordings; milestone 2 adds stimulus protocols, labelled
current-injection optogenetics and replay of interventions beside a matched control; M2b adds
live sessions (start, pause, stimulate, stop from the page) and the protocol editor; M3 the
fly's-eye view (Eye tab); M4 the Fidelity tab and run configuration.

## Build the data (once; not kept in version control)

    .venv/bin/python app/build/atlas.py                     # male-cns atlas from data/cache (about 10 s, 50 MB)
    .venv/bin/python scripts/export_geometry.py --out app/data/body/flybody   # body meshes (13 MB)
    .venv/bin/python app/build/eye.py                       # eye mosaic, pale/yellow masks, photoreceptors (M3; 132 kB)
    .venv/bin/python app/build/convert_legacy.py            # old runs/organism-record-* into runs/app/legacy
    .venv/bin/python app/build/fidelity.py                  # the model's construction tables for the Fidelity tab (M4); rerun when the model changes

## Record a run

    python3 ~/director/harness/slot.py run --label "app: record m9 2 s" -- \
        .venv/bin/python app/server/record.py --profile m9 --seed 12 --duration-ms 2000 --out runs/app/m9-s12-2000ms

About 96 s of wall time per simulated second and 2.4 GB of memory on the Mac (measured for m9).
`record.py --help` lists the options.

## Interventions

A protocol (`flyemu-protocol/1`, `app/protocols/*.json`) states the configuration, the genotype
(TNT, Kir2.1), timed events (current, CsChrimson and GtACR1 as labelled current injection, Poisson
kicks, world changes), what to record, what a real fly does and a pass/fail criterion declared
before the run is viewed.

    .venv/bin/python app/server/record.py --protocol app/protocols/mdn-cschrimson.json --out runs/app/x
    .venv/bin/python app/tools/run_library.py               # every protocol not yet recorded, into runs/app/lib
    .venv/bin/python app/tools/score_library.py             # each run vs its control and the sham; runs/app/lib/scores.json
    .venv/bin/python app/tools/replay.py runs/app/lib/dna02-left   # re-run its embedded protocol; exit 0 if identical

The recorder refuses a protocol that touches a held-out item or an unspent seed unless the run
names it with `--spend-heldout <id>` (`app/server/heldout.py`). A library run takes about 3.5
minutes and 2.4 GB (measured); the runner goes through `~/director/harness/slot.py` when present,
one run at a time. `config.preparation: brain_only` runs the network alone as the model's
`scripts/assay_pathways.py` does, and `config.kick_rng: assay` draws kicks as it does;
`app/protocols/assay/` reproduces its sugar to MN9 assay (`--seeds 0 1 2` on `run_library.py`).
Runs of one protocol at several seeds are named `<protocol>-s<seed>`; the scorer summarises them
(readout per seed, mean, SD) and the Compare tab shows where each trial falls.

    .venv/bin/python app/tools/make_shams.py                # more sham protocols (one Kenyon cell each, fixed draw)
    .venv/bin/python app/tools/make_shams.py --onset-step-ms 5   # a second set: new cells, onsets 505 to 540 ms
    .venv/bin/python app/tools/run_library.py --protocols app/protocols/sham --out runs/app/lib-m9

Shams can land on the same trajectory (at one onset every sham's forced spikes fall on the same
steps), so the scorer hashes every spike outside the forced cells and reports how many shams are
distinct; only distinct ones are separate noise samples.

## T4/T5 direction test

    .venv/bin/python app/tools/t4t5_ds.py --profile m9r --out runs/app/t4t5/m9r [--model-root ~/fly-emulation] [--parallel 7]

Records 17 runs (moving ON and OFF bars into the medulla inputs and into the photoreceptors) and
reports per T4/T5 subtype whether the cells respond and prefer the direction flies prefer; exit 0
only if all 8 do. A held-out test for the fly worker's temporal-dynamics rungs: section 13.1 of
`docs/APP_DESIGN.md` gives the readout, cost and rules.

## Open it

    .venv/bin/python app/server/serve.py --open             # http://127.0.0.1:8766/ in the default browser

The page lists every recording under `runs/app`. URL parameters keep the view: `rec`, `t` (ms),
`sel` (bodyId), `view` (anatomy, flow, groups), `colour` (`delta` is rate vs control), `theme`,
`tab` (run, neuron, compare, session, eye, fidelity) and `ctrl` (the control recording's id, when more than one matches).
A stimulated run's Compare tab shows the matched control, the step where the two first differ,
the criterion's verdict, the sham runs read over the same window (the noise floor) and the cells
that changed most.

The Session tab (`tab=session`) edits a protocol (from the open recording or blank), checks it
against the atlas and the held-out guard, and starts a live session on this machine through the
slot limiter: one at a time, about 100 s of wall time per simulated second closed loop. Pause,
resume, stop and stimulus events take effect within 10 ms of simulated time and are written into
the recording's protocol, so it replays like any other. The server only accepts these requests
from a local page (`X-Workbench` header and a local Host).

The Fidelity tab (`tab=fidelity`) shows what the open run's model is made of: its values counted
by evidence (measured, derived, inferred, guessed), each against its biological bounds, the
model's construction ledger, mechanisms with their switches, and the profiles with their
differences. "Configure a run" picks a profile, body, scan and switch values and writes them into
the Session tab's protocol; the check there refuses what the recorder cannot run and shows the
status the run will be recorded with.

## Check it

    .venv/bin/python -m pytest app/tests -q                 # formats, joins, legacy conversion, page render
    .venv/bin/python app/tools/screenshot.py                # headless shots and a contact sheet in runs/app/shots

## Static copy

    .venv/bin/python app/build/site.py --only m9-s12-2000ms  # into runs/app-site; serve with any file server

Nothing is published by these tools.

## Layout

| Path | What |
|---|---|
| `server/recfmt.py` | `flyemu-rec/1` writer and reader |
| `server/record.py` | runs the model's public loop and records every spike, pose, torque, contact, eye readout and watched voltage |
| `server/serve.py` | local server and recording catalogue (with library verdicts from `scores.json`) |
| `server/protocol.py` | `flyemu-protocol/1`: target resolution, effectors and their declared approximations |
| `server/heldout.py` | held-out guard |
| `server/live.py`, `server/sessions.py` | live session: the recorder's command reader; the server's session manager and protocol check |
| `server/status.py` | the status a run is recorded with (shared by the recorder, the check and the Fidelity build) |
| `build/fidelity.py` | the model's construction tables (mechanisms, unknowns with bounds, profiles, scans, bodies) for the Fidelity tab |
| `build/atlas.py` | `flyemu-atlas/1`: positions with basis codes, annotations, flow layers, edge shards |
| `build/eye.py` | `flyemu-eye/1`: ommatidium centroids, pale/yellow masks, photoreceptor assignments |
| `build/convert_legacy.py` | old `replay_data.js` files to rec/1 (motor spikes only, flagged) |
| `build/site.py` | static bundle |
| `web/` | the page (ES modules, three.js r170 vendored) |
| `tests/` | pytest checks |
| `protocols/` | the intervention library (four tests, a control and a sham; `sham/` more shams; `assay/` the check against the model's assay) |
| `tools/` | library runner and scorer, replay check, screenshots, live-cost benchmark, eye sweeps and the T4/T5 direction test |
