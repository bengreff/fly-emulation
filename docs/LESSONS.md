# Lessons from sessions 1–8 that constrain the construction

The directly applicable scientific findings, extracted from the full records. Session 1–8 FINDINGS and DECISIONS are archived in `docs/archive/FINDINGS_s1-8.md` and `docs/archive/DECISIONS_s1-8.md`, where the IDs below point. Items are grouped by the mechanism layer they constrain in `docs/CONSTRUCTION.md`. **Labels are as recorded; none is upgraded here.**

## Connectome and identity

- **Inclusion:** male-cns v1.0, traced or typed, edges ≥ 5 synapses: 167,111 neurons and 6.24 M edges. 9,311 untyped fragments were excluded because they are not whole neurons (F-COUNT-2). The whole-CNS graph is the right source, not the VNC alone (F-DATA-2).
- **Transmitter identity:** use the curated `consensusNt`, not the classifier `predictedNt`. The classifier calls all 4,058 KCs dopaminergic and leaves ~3.3k GABA/glutamate cells "unclear" (F-NT-1). Transcripts agree with the type-level call on 62 of 68 types.
- **Receptor sign cannot be predicted from wiring** (F-RCPT-1: leave-one-type-out at chance for GluRIA/B, Nmdar1, GABA-B-R3). It must come from transcriptomes matched to type (Davis 2020, Turner-Evans 2020, Epiney 2025; F-RCPT-2). snRNA iGluR/GluCl ratios are biased upward relative to bulk data.
- **Ring cells** (EPG, Delta7, PEN_b, PEG) are GluCl-dominated in three datasets, so Delta7 → Delta7 is inhibitory (F-RCPT-2).
- **EPG heading** must come from connectivity, not glomerulus labels: L1–L8 and R1–R8 run in opposite directions round the ring (`scripts/infer_epg_heading.py`).
- **Proprioceptor subtypes** come from BANC (F-SENSE-2). The old sign field was wrong for most leg proprioceptors (F-SIGN-2). Claw direction is inferred and awaits FANC labels.
- **Sensory neurons are fired from the periphery,** not from inside the brain: central input onto sensory terminals must be presynaptic modulation, not spike-generating synapses (F-SENS-1).

## Neuron and synapse

- **One global efficacy cannot be both stable and functional.** The stability fit gives 0.157–0.165 mV per synapse (F-GAIN-2, s8 rule v3), but the measured ORN→PN unitary EPSP is 11× that (F-AL-4). Transferring it to leg afferents gives a right-signed reflex but an unstable brain (F-XFER-1). Strength must be per class, and fitted.
- **Uniform single knobs trade function for stability:** adaptation (F-SFA-1), depression (F-STD-1), input normalisation (F-NORM-1) and size scaling (F-SIZE-1) all fail when applied uniformly.
- **Inhibitory populations mostly inhibit each other:** Delta7 → Delta7 626 synapses/cell vs 86 to EPG; ER cells get 73% of their input from other ER. Under uniform efficacy they fall silent (F-CX-3).
- **Latent self-sustaining loops** exist in the calibrated network (Mi18/DNge019/DNg12; AL eLNs; the reciprocally wired GNG117 pair, which a 4 mV rise in central excitability turns into a switch). Which one appears depends on labels, scale and resting margin (F-STAB-1, F-LN-1, F-STAB-6).
- **Graded signalling:** real leg interneurons rest depolarised and code position in graded Vm; the model's spiking versions are pinned (F-VNC-1). Non-spiking classes need graded mode (research note `docs/research/fidelity_neural_s9.md`).
- **Slow tibia-flexor MNs:** τm 15.5–16.6 ms transfers across 4 cells. The rest rate is 20–47 Hz, driven synaptically (nicotinic), not intrinsically, and a single point fit does not transfer (F-AZ-2/3/4).
- **Delays:** per-type delays come from 11,751 skeletons (F-DELAY-1); untyped cells are inferred with CV error 0.14 ms (F-DELAY-2).
- **Monoamines have no fast sign** (all fly DA/5-HT/OA receptors are GPCRs); stable once the KC labels are fixed (F-M0-2). Receptor-signed pool sensitivities are stable in the default config but sustain a ~9 Hz brain under stronger drive. Pool magnitudes need calibration.
- **Starting state:** starting from a living, noisy state rather than exact rest does not rescue the ring, and noise lowers its ignition threshold (F-WARM-1).

## Sensors

- **Every sensory neuron is assigned a transduction model** (F-CENSUS-1, F-SENSE-ALL). Most are static proxies. Afferent firing rates have no published calibration for most classes (F-GAP-1).
- **ORNs:** Hallem rates are attached (F-ORN-3). ORN→PN depression follows Nagel 2015 (U 0.22, τ 893 ms, hand-verified).
- **Photoreceptors:** retinotopy is derived from the connectome (F-VISION-2), with spectral identity (F-VISION-3).

## Motor and body

- **Motor neuron → muscle mapping is complete for the legs** and externally corroborated (F-DATA-1; Azevedo 2024 FANC atlas).
- **Leg motor units:** per-MN forces from Azevedo 2020 (F-MOTOR-3); fast/intermediate units ~10/1 µN at the tibia. Slow-unit twitches do not peak within 500 ms, while the model uses a guessed 100 ms decay (research note).
- **The torque the body needs is the torque a real fly delivers** (F-TORQUE-1). The body is in mm, g, s, so torque is in µN·mm; a fly weighs ~10 µN.
- **Joints:** a third of the "powered joints" were not joints (F-JOINT-1). Joint signs are calibrated (F-SIGN-4/5; re-run `calibrate_joint_signs.py` after any body change). A body swap silently inverts hard-coded signs (F-AXIS-1).
- **Passive joint parameters are guesses** (F-STIFF-1): 1 µN·mm/rad everywhere, default rest angles. Measured data now exist: "Passive muscle forces in Drosophila are large but insufficient to support a fly's weight" (eLife 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC12324252/), from silencing motor neurons; see CONSTRUCTION.md.
- **Collision:** the fly could pass through itself, and a fix dropped the feet (F-COLLIDE-1/2).
- **Non-leg motor layer:** its guessed force/sign pins joints (wings at a range limit 82% of the time, abdomen 62%; s8 reassessment).

## Behaviour observed so far

- **Command direction:** DNg100 → forward displacement 4/4 seeds under T; MDN backward fails (s7).
- **Standing:** default fails; T reaches ≥ 0.90 mm on 2/3 seeds over 0.5–1.5 s but sinks by 3 s (F-STAND-2).
- **Walking:** no stepping (F-WALK-0).

## Method lessons (how we lose sessions)

- **Verify tools before believing results:**
  - the non-local ring kick;
  - the mirrored heading map;
  - the KC transmitter labels;
  - a dimensional error that silenced the brain (F-NOISE-1);
  - a units "bug" that was not one (F-RETRACTED-1).
- **Single seeds are anecdotes** (the MDN "backward walk"). A result from one configuration can hide instability in another (MS rows).
- **Exact numbers differ between the Mac and backhouse;** each machine reproduces itself.
- **Hand-tuning one mechanism at a time did not converge:** ~8 of 36 pre-registered tests passed. This is the reason for the construction programme.

## Added in session 9

- **A probe must step the same motor path as the model.** A private loop that called `Neuromuscular.step` silently ran without the new muscles; the bypass showed up only because a re-run after a change reproduced every digit (F-HARNESS-2). `Organism.motor_step()` is now the single path.
- **MuJoCo resets a diverging state silently.** Check `d.warning` in every probe (F-HARNESS-1).
- **Reconcile units against a physical consequence the paper states.** The eLife stiffness units were settled by the "70x too weak" claim, reproduced in our own body (F-PASSIVE-1).
- **Read what a figure measures before using it.** eLife Fig 3C shows loaded equilibria, not rest angles. Azevedo's "not within 500 ms" concerns rate steps, not single twitches (F-TWITCH-1).

## Added in session 10

- **Check a held-out criterion on the base model before registering it.** Water->MN9 was 0 Hz in m4 already, so its failure said nothing about the candidate and cost a post-hoc attempt (F-STAB-4).
- **Stability found by search can be narrow.** DN release 0.70 is silent on 12/12 seeds, 0.72 fails on all three fit seeds, and a 1 ms sample-and-hold of the senses breaks it on 5/12. Report margins, not only passes.
- **Neutral values need exactness, not closeness.** Every new mechanism entered at a value where the network is bit-identical to m4 (x*1.0, x+0.0 in float32; separate RNG draws only when on). This made eleven brain mechanisms addable in one session without moving a regression.
- **A GPU port is only trusted when it reproduces spike rasters exactly.** The batched simulator matched lif.py spike for spike on the whole CNS, and then the real search's 70 CPU scores to 0.1 Hz; that is what licenses using it.
- **Look at the geometry the physics uses.** The wing had two fluid geoms (membrane and vein mesh), doubling lift (F-FLIGHT-2), and the wing joints were mislabelled (F-WING-1); both were found by printing the model, not by reading names.
- **Placeholder rows collide with real ones.** Old unwired rows (N23, N27, S1-S4) had the ids and opposite conventions of the new ones; retire them explicitly (data/params/retired_placeholder_rows_s10.csv).
