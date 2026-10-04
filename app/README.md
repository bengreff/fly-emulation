# Fly Workbench

A local research app for the fly emulation: the body, every neuron of the scan on a brain map, the
recorded activity and the evidence behind each model value. Design and milestones:
`docs/APP_DESIGN.md`. Milestone 1 replays recordings; live runs and interventions come in M2.

## Build the data (once; not kept in version control)

    .venv/bin/python app/build/atlas.py                     # male-cns atlas from data/cache (about 10 s, 50 MB)
    .venv/bin/python scripts/export_geometry.py --out app/data/body/flybody   # body meshes (13 MB)
    .venv/bin/python app/build/convert_legacy.py            # old runs/organism-record-* into runs/app/legacy

## Record a run

    python3 ~/director/harness/slot.py run --label "app: record m9 2 s" -- \
        .venv/bin/python app/server/record.py --profile m9 --seed 12 --duration-ms 2000 --out runs/app/m9-s12-2000ms

About 96 s of wall time per simulated second and 2.4 GB of memory on the Mac (measured for m9).
`record.py --help` lists the options.

## Open it

    .venv/bin/python app/server/serve.py                    # http://127.0.0.1:8765/

The page lists every recording under `runs/app`. URL parameters keep the view: `rec`, `t` (ms),
`sel` (bodyId), `view` (anatomy, flow, groups), `colour`, `theme`.

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
| `server/serve.py` | local server and recording catalogue |
| `build/atlas.py` | `flyemu-atlas/1`: positions with basis codes, annotations, flow layers, edge shards |
| `build/convert_legacy.py` | old `replay_data.js` files to rec/1 (motor spikes only, flagged) |
| `build/site.py` | static bundle |
| `web/` | the page (ES modules, three.js r170 vendored) |
| `tests/` | pytest checks |
| `tools/` | screenshots, live-cost benchmark |
