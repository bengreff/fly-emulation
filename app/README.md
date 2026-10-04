# Fly Workbench

A local research app for the fly emulation: the body, every neuron of the scan on a brain map, the
recorded activity and the evidence behind each model value. Design and milestones:
`docs/APP_DESIGN.md`. Milestone 1 replays recordings; milestone 2 adds stimulus protocols, labelled
current-injection optogenetics and replay of interventions beside a matched control. Live
sessions are not built yet.

## Build the data (once; not kept in version control)

    .venv/bin/python app/build/atlas.py                     # male-cns atlas from data/cache (about 10 s, 50 MB)
    .venv/bin/python scripts/export_geometry.py --out app/data/body/flybody   # body meshes (13 MB)
    .venv/bin/python app/build/convert_legacy.py            # old runs/organism-record-* into runs/app/legacy

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
one run at a time.

## Open it

    .venv/bin/python app/server/serve.py --open             # http://127.0.0.1:8766/ in the default browser

The page lists every recording under `runs/app`. URL parameters keep the view: `rec`, `t` (ms),
`sel` (bodyId), `view` (anatomy, flow, groups), `colour` (`delta` is rate vs control), `theme`,
`tab` (run, cell, compare) and `ctrl` (the control recording's id, when more than one matches).
A stimulated run's Compare tab shows the matched control, the step where the two first differ,
the criterion's verdict, the sham run read over the same window (the noise floor) and the cells
that changed most.

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
| `build/atlas.py` | `flyemu-atlas/1`: positions with basis codes, annotations, flow layers, edge shards |
| `build/convert_legacy.py` | old `replay_data.js` files to rec/1 (motor spikes only, flagged) |
| `build/site.py` | static bundle |
| `web/` | the page (ES modules, three.js r170 vendored) |
| `tests/` | pytest checks |
| `protocols/` | the intervention library (four tests, a control and a sham) |
| `tools/` | library runner and scorer, replay check, screenshots, live-cost benchmark |
