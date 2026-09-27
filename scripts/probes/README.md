# Probes

Diagnostic scripts that run on the current model (`WORKING_PROFILE`). Each has a finding or pre-registration behind it. Run with `uv run python scripts/probes/<name>.py [--help]`. Heavy probes build the whole organism (~10 s) and simulate ~1 s in ~50 s on one CPU.

| Script | Checks | Reference |
|---|---|---|
| `closed_loop_check.py` | closed-loop stability; rates by group; return to rest after silencing senses (tonic cells excluded) | regression check (WORKFLOW §6) |
| `warm_start.py` | CX bump test: warm start, local (12 EPGs nearest a heading, inferred from connectivity) or full kick, senses removed; per-EPG rates | Ben's s7 ring criteria; LESSONS |
| `score_warm.py` | scores `warm_start.py` output: B1 bump, B2 no saturation, Q every other cell quiet | as above |
| `standing.py` | thorax height, posture, afferent and MN rates; `--push` resistance push; `--zero-joints` diagnostic | standing |
| `azevedo_reflex.py` | tethered PD-probe step/ramp protocol; slow flexor MN responses (use `--kp 100 --kd 0.133`) | used by `scripts/score_reflex.py` |
| `premotor_inputs.py` | steady synaptic input to chosen VNC cells by presynaptic type | reflex diagnosis |
| `vnc_rest_state.py` | resting V and firing of VNC hemilineages | graded-VNC evidence |
| `vnc_angle_tuning.py` | Vm-angle slope of a hemilineage under a clamped tibia | 13Bα target |
| `pn_silence.py` | uPN spontaneous rates; ORN and LN input decomposition | AL |
| `command_walk.py` | closed-loop stimulation of a descending command type; displacement and leg rhythm | command direction |
| `odour_closed_loop.py` | PN recruitment by an odour near the antennae | olfaction |
| `sugar_patch_closed_loop.py` | taste channels and MN9 on a sugar patch | taste |
| `route_strength.py` | signed 1- and 2-hop synaptic drive from stimulus types to readout cells | anatomy utility |

Historical probes from sessions 1–8 (the m1 ignition and AL diagnostics, pre-BANC reflex probes, and the non-local `cx_kick.py`) were removed in the construction pivot. They remain in git history before commit 15c4278.
