# Fastest credible route to sustained, organised behaviour

Written 30 Sep 2026 (session 11) for Ben. It answers one question: what is the shortest credible path to a fly that walks, searches and feeds for minutes on its own, with every parameter inside biological bounds, and what compute that needs. Numbers are labelled: measured (run in this repo), derived, or guessed.

## Where the fly stands

- The whole CNS (167,111 neurons, 6.24 M connections) runs as spiking cells on a MuJoCo body. With sensory input removed it falls silent and the body stays at rest (the dead-fly test, measured on seeds 0-11).
- Identified pathways work open loop: sugar taste drives the proboscis motor neuron MN9 (7.3 Hz at 100 Hz input, measured), and bitter taste suppresses it (measured).
- It does not walk. Driving the walking command neuron DNg100 gives no leg rhythm (sessions 4 and 11, measured), and the body does not yet turn an alternating motor pattern into stepping (session 11, measured).
- About 2% of the fly's information slots hold data the model uses. Outside per-synapse detail, 47% of slots are measured and 45% sit at class-level priors (ledger v3, measured). Most gaps are per-cell physiology, and the transmitter sign of VNC glutamate synapses.

## What blocks organised behaviour

1. **No rhythm generator in the VNC.** Walking needs alternating leg motor output at 7-15 Hz. A rate model of the same VNC connectome produces it (Pugliese et al. 2025). Ours does not. The likely reasons are that premotor interneurons are non-spiking (graded) in the fly, and that the sign of VNC glutamate is unknown (glutamate can excite or inhibit, depending on the receptor). Tonight's probes tested the first reason and found no rhythm either way (section "What tonight measured").
2. **Class values are fitted narrowly.** The working values were searched to pass a few assays. Any new biology changes the operating point: tonight's per-cell size rule for central neurons broke the sugar pathway even though the rule is well founded (measured). New rules have to be added together with a joint re-search of the class values against physiology, and each search needs thousands of simulated seconds.
3. **Too slow for minutes of behaviour on the Mac.** One simulated second takes 11-39 s of CPU wall time for the brain alone, and about 70 s closed loop (measured). A 10-minute foraging bout is about 12 hours on the Mac per fly per parameter set (derived).
4. **Sensory feedback is thin.** Leg proprioception and the antennal and visual inputs exist only as rough encoders. Walking in real flies relies on proprioceptive feedback to shape and stabilise the rhythm.
5. **Nothing yet drives goal-directed behaviour.** Odour and food search need a world (an odour plume, food patches), internal state (hunger) and the learning circuit (mushroom body dopamine plasticity). The circuits are in the connectome. The world, the plasticity rule and the state variables are not built.

## The route, in order

| Step | What | Evidence it worked | Compute |
|---|---|---|---|
| 0 | Body motor transfer: a synthetic alternating MN pattern must give stepping in the tethered, then standing, body (muscle kinetics, recruitment order, co-contraction, moment arms) | legs follow 5-15 Hz alternation; forward progress when standing | Mac (about 80 s per 1.4 s trial) |
| 1 | Open-loop VNC rhythm: DNg100 → alternating front-leg motor output, with graded premotor cells and VNC glutamate signs from transcriptomes (Allen 2020 VNC atlas by hemilineage) | rhythm 4-25 Hz above surrogates; left/right and flexor/extensor phase | Mac (minutes per arm) |
| 2 | Joint class re-search with the per-cell rules on, against physiology (sugar/bitter, grooming, rhythm, rest silence) plus held-out assays | held-out assays pass at plausible values | backhouse GPU: ~10,000 member-seconds ≈ 1-2 h (derived from 0.4 s/member-s); Mac ≈ 30-100 h |
| 3 | Closed-loop walking: rhythm + proprioception + body; the first video Ben can watch of a fly walking on its own brain | sustained stepping ≥ 10 s, plausible step frequency and gait | GPU brain + batched bodies: ~10 s wall per member-second at B = 12 (measured); Mac ~70 s |
| 4 | Food search and feeding: odour plume world, hunger state, sugar → proboscis extension closing the loop | approach to odour source, feeding at food | GPU, minutes of simulated time per fly: ~1-2 h per fly-bout batch |
| 5 | Learning: mushroom body dopamine plasticity; odour-shock or odour-sugar conditioning | learned approach/avoidance on fresh odours | GPU, hours |
| 6 | Flight | later: needs wing aerodynamics and a flight body model | GPU |

Steps 1 and 3 give something to watch. Step 2 is what makes it credible, because the behaviour then comes from parameters that also pass physiology.

## Compute, Mac versus backhouse

- The Mac runs single experiments: open-loop assays at 7-40 s per simulated second (measured) and one closed-loop fly at ~70 s per simulated second. That is enough for step 1 and for spot checks.
- Searches and minutes-long behaviour need the backhouse GPU. The batched brain there runs 0.37-0.45 s wall per member per simulated second (measured, session 10). The body is the bottleneck in closed loop (a Python MuJoCo step per fly). The next speed-up is sending only the sensory rows each step, then MJX or a C body loop.
- Rough budget for steps 2-4: tens of GPU hours (guessed from the per-member rates above). Backhouse was offline tonight, so this session stayed on steps 1 and 2 groundwork.

## What tonight measured (session 11, Mac)

- **The walking command barely reaches the legs.** Driving DNg100 at 92 Hz in the closed loop raises the mean leg motor neuron rate by only 0.7 Hz (about 3.2 to 3.9 Hz; three seeds). Removing body feedback does not change this. Stepping needs tens of Hz, rhythmically modulated.
- **No rhythm in the VNC** from DNg100 with all cells spiking, with the VNC's local cells non-spiking (graded; motor output doubles to 6-7 Hz but stays arrhythmic), or with graded cells plus spike-frequency adaptation. A rate model of the same wiring does make a rhythm (Pugliese 2025), so the missing piece is in our cell and synapse model.
- **The body does not turn an alternating motor pattern into stepping.** Forcing the leg motor neurons to fire in alternating tripod bursts (about 50 Hz mean) moves the legs 0.2-1 mm but not at the burst frequency at 10 or 20 Hz, whether the fly stands or hangs tethered in the air. At 5 Hz some legs follow partly. So even a perfect brain would not walk this body yet.
- **VNC glutamate signs cannot be read from the VNC atlas by lineage.** Every hemilineage expresses both the inhibitory (GluCl) and excitatory (iGluR) receptor genes in 39-70% of cells; the sign needs cell-type-level data.
- The per-cell size principle is now in the working model for the 757 motor neurons it applies to (m7). The same rule for central neurons is sound but moves pathways fitted on the old values, so it waits for a joint re-search.

Revised order: the body's motor transfer (step 0 in the table) comes first, because a rhythm is only useful once the body can express it. It is a Mac job (a 1.4 s trial takes about 80 s). Leg joint damping at the FlyMimic time constant (0.05 s) did not fix it (joint share at 10 Hz 0.094 vs 0.057; pre-registered, not adopted). The next suspects are joints pinned at their range limits, the muscle force-velocity term acting as a brake, and antagonist co-contraction in the synthetic pattern; each is a one-trial test.

An outside review written tonight (`docs/ASTRA_ROUTE_2026-09-30.md`, not by this session) argues for the same localisation experiment and for fitting to physiology before behaviour; this note agrees on both.
