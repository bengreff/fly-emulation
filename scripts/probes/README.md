# Probes

Probes are diagnostic scripts. Each produced or checks a specific finding.
- **Current** probes run on the current model (profile `m2`), and later sessions should reuse them.
- **Historical** probes are the record behind an older finding. They were written for an earlier model state (profile `m1`, pre-session-6 body or sensors) and may no longer run or mean the same thing. Keep them for provenance; do not cite their numbers as current.

All run with `uv run python scripts/probes/<name>.py [--help]`. Heavy ones build the whole organism (about 10 s) and simulate about 1 s in about 50 s.

## Current

| Script | Checks | Finding / pre-registration |
|---|---|---|
| `closed_loop_check.py` | Closed-loop stability; rates by group; return to rest after silencing senses (tonic cells excluded) | DECISIONS session 6, criterion 2 |
| `standing.py` | Thorax height, posture, afferent and MN rates; `--push` resistance-reflex push | F-STAND-1; DECISIONS standing |
| `azevedo_reflex.py` | Tethered PD-probe step/ramp protocol; slow flexor MN responses | F-AZ-2; used by `scripts/score_reflex.py` |
| `premotor_inputs.py` | Steady synaptic input to chosen VNC cells, by presynaptic type | F-AZ-2 |
| `vnc_rest_state.py` | Resting V and firing of VNC hemilineages | F-VNC-1 |
| `vnc_angle_tuning.py` | Vm-angle slope of a hemilineage under a clamped tibia (`--leg`) | F-VNC-2 |
| `pn_silence.py` | uPN spontaneous rates; ORN and LN input decomposition (takes `K=V` overrides) | F-AL-2, F-AL-3 |
| `command_walk.py` | Closed-loop stimulation of a descending command type; leg rhythm | F-WALK-0 |
| `odour_closed_loop.py` | PN recruitment by an odour near the antennae | F-OLF-1 |
| `sugar_patch_closed_loop.py` | Taste channels and MN9 on a sugar patch | F-SENSE-ALL |
| `route_strength.py` | Signed 1- and 2-hop synaptic drive from stimulus types to readout cells | anatomy utility |

## Historical

| Script | Finding |
|---|---|
| `reflex_gain.py`, `reflex_arc.py` | F-REFLEX-1, F-STAND-1. Superseded by `azevedo_reflex.py`; pre-BANC sensor subtypes |
| `attractor_core.py` | F-ORN-2. The attractor no longer occurs (F-ORN-3) |
| `al_residual_loop.py`, `al_unclear_sign.py`, `aln_ach.py`, `aln_ach_targets_v2.py`, `eln_outputs.py`, `orn_ignition.py`, `orn_persist_types.py`, `orn_presyn.py` | F-LN-1/2, F-AL-1 (m1 AL ignition diagnostics) |
| `ignite.py`, `ignition_core_screen.py`, `ignition_route.py`, `core.py`, `kckc.py`, `flip.py`, `sfa_check.py`, `sensory_input.py` | F-GAIN-2, F-SFA-1, F-SENS-1 (m1 ignition) |
| `joce_mdn_route.py`, `mn9_asymmetry.py` | F-SIZE-1, F-DATA-3 |
| `density.py` | FlyWire connectivity density check (session 4; reads `external/`) |
