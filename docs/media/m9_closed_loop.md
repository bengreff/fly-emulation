# m9 closed loop, body and brain side by side

File: `docs/media/m9_closed_loop.mp4` (0.36 MB, 736x240 pixels, 20 fps, 60 frames, 3.0 s).

## What this is

The left panel is a MuJoCo render of the fly body (the flygym cartoon mesh,
default material colours, on a grey checkerboard floor used only as a visual
ground reference). The right panel is a chart of simulated brain activity:
population firing rate (spikes per second, averaged in 1 ms bins) for five
coarse groups of neurons, plotted against simulated time, with a moving red
vertical line marking the instant shown in the left panel. Both panels come
from the same single run of the closed loop (body -> senses -> brain ->
motor neurons -> muscle torque -> body, every step), so the two sides are
exactly in sync; nothing was staged or re-timed afterwards.

The five groups are a display-only collapse of the connectome's `superclass`
column, not official brain regions:

- sensory: olfactory/visual/leg/wing sensory neurons and their immediate
  ascending relays (17,896 of 167,111 neurons)
- central: optic-lobe and central-brain/VNC interneurons, including visual
  projection neurons (144,473 neurons, the great majority of the network)
- ascending: VNC-to-brain relay neurons (1,854 neurons)
- descending: brain-to-VNC command neurons (1,318 neurons)
- motor: motor, efferent and endocrine output neurons (1,054 neurons)

About 516 neurons (0.3%) have a blank superclass label in the connectome
table and are left out of all five groups.

## What it shows

The fly is seen from the side by a tracking camera.
- It starts in its neutral pose just above the floor and settles onto its legs
  in the first few hundred milliseconds. That settling is an artifact of the
  starting condition.
- It then stays standing on its legs, in place, for the rest of the clip. It
  does not walk or take off.
- The only large movement is the wings. They start extended and by about
  1.2 s have swung down to hang below the body, where they stay.
  - Whether that is motor drive or the wings sagging under gravity and joint
    springs was not checked.
- All senses are on throughout. This is not the silence test, which removes
  all sensory input.

The brain is active but quiet overall:
- The motor group fires in regular synchronous volleys, roughly every 50 ms,
  peaking near 55 Hz early and settling near 20 Hz (population rate in 1 ms
  bins).
  - Inferred, not checked: these are mostly the slow motor neurons with
    intrinsic tonic drive (set to their measured rest rate). They all start
    from exactly the same resting state and so fire in step. This lockstep
    is an artifact of the identical start, not a claimed rhythm.
- The sensory group shows occasional sharp spikes.
- The central, ascending and descending groups stay at a few Hz.

Whether these rates are right is not established by this video. The evidence
is in docs/DECISIONS.md session 11 (the m9 held-out gates) and the run
records. This video is a communication artifact, not evidence.

## Provenance

- Model: m9 (`profiles.WORKING_PROFILE`): rung-1 spike channels with the
  re-searched class gains (DECISIONS session 11, F-RS-1).
- Seed 12 (an m9 fit seed). 3000 ms simulated. `--playback-speed 1.0`, so
  the video plays at simulated time.
- Override: `motor_unit:all|force_per_spike=10`. This is the same setting the
  closed-loop silence check uses by default.
  - Earlier drafts also set `joint:leg|damping=0.043`, which the script's
    defaults added silently. That value failed its mechanism check and is not
    part of m9.
  - With it, the legs sprawled flat. The script default is now fixed and the
    drafts were replaced.
- Command:

```
python3 ~/director/harness/slot.py run --label "fly-emulation: render m9 closed loop 3 s" -- \
  uv run python scripts/render_brain_body.py --duration-ms 3000 --seed 12 \
  --set "motor_unit:all|force_per_spike=10" --out docs/media/m9_closed_loop.mp4
```

- Script: `scripts/render_brain_body.py`.
  - It builds the organism once with the working profile and steps body and
    brain together.
  - It plots per-group spike counts read directly off the same
    `org.net.step` spikes, with 1 ms binning and no other smoothing.
  - 516 neurons (0.3%) with a blank superclass are left out of the five
    groups.

## What it is not

- Not a demonstration of walking or flight; the fly is at rest for nearly
  all of the clip.
- Not a validated prediction; no held-out observation or intervention is
  being checked here, only a run of the existing closed loop.
- Not raw data; the brain panel is a derived, binned, grouped summary for
  legibility, not a full spike raster of all 167,111 neurons.
- The checkerboard floor, body colours and camera motion are MuJoCo/flygym
  defaults, chosen for visibility, not measurements of the real animal.
