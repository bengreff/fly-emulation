# Plan for sessions 4 to 8

Written 24 September 2026. Replaces the "immediate next task" in
`docs/HANDOFF.md`. `docs/PLAN.md` stays as the session-2 record.

**Goal:** the male-CNS connectome controls an accurately simulated fly body.
Accuracy has to be checked at each layer separately, because a good-looking
behaviour can hide a wrong layer underneath.

| Layer | "Accurate" means, operationally |
|---|---|
| Neural | predicts **held-out** published interventions better than a shuffled-wiring control; spontaneous and driven rates within measured ranges |
| Neuromuscular | per-spike force and twitch time course within Azevedo et al. 2020 ranges (slow <0.1 µN, fast ~10 µN per spike) |
| Body | already mass-, range- and collision-checked (F-MASS-1, F-COLLIDE-1/2) |
| Behaviour | kinematics compared with measured data under the **same stimulus protocol** as the experiment |

## What changed since session 3

- **F-GAIN-1 should be tested with pathways, not with the mean firing rate.**
  A fly brain is mostly quiet without sensory drive, so the brain-wide mean is
  a weak readout. The discriminating experiment runs with the noise off and
  drives identified sensory neurons, as Shiu et al. 2024 did. Our current
  defaults put threshold 15 mV above rest; Shiu's put it 7 mV above. That
  alone may explain why the noise dominated.
- **There is external prior art to calibrate against.** Shiu 2024 (LIF,
  FlyWire; experimentally checked predictions) and Pugliese 2025 (rate model
  on MANC and male-CNS: DNg100 drives a leg rhythm; DNg100 and DNb08 confirmed
  optogenetically). flybench (MIT) is a set of 36 cited tasks with
  shuffled-wiring controls on FlyWire and MaleCNS. It reports that
  spike-frequency adaptation beats plain LIF, and that the working gain is
  0.40-0.45 of Shiu's, not 1.0. These are unreviewed GitHub projects, so treat
  them as evidence to re-derive, not as ground truth.
- **All assay neurons exist in `male-cns:v1.0`:** MN9, MN11/12, DNg100, DNb08,
  DNp01 (giant fibre), DNp09, MDN, TTMn, and 1,428 gustatory neurons.
- **The non-leg motor map exists** (`docs/MOTOR_TARGETS.md`). TTMn/STTMm and
  the proboscis pool have direct evidence and can be wired now.
- **The graph now excludes 9,311 untyped fragments** (F-COUNT-2).
- **backhouse (the GPU machine) is unreachable.** The plan is sized for the M2
  Pro: about 40x slower than real time, 2 GB.

## Session 4: make the anatomy load-bearing, and prove it

1. **Add a borrowed parameter profile.** Load Shiu's values (V_rest −52,
   V_th −45, V_reset −52, τ_m 20 ms, τ_s 5 ms, t_ref 2.2 ms, delay 1.8 ms,
   0.275 mV per synapse) as `--profile shiu2024`. Every value is recorded
   `assumed` with source "fitted in Shiu 2024 to FlyWire", never measured.
   Set noise to 0 and add Poisson stimulation of named neuron sets.
2. **Match neurons across the two connectomes.** Shiu used FlyWire sugar GRNs;
   we need their male-CNS equivalents. Use the male-CNS FlyWire cross-match
   annotations, record the confidence of each match, and use explicit
   transmitter overrides where predictions are known to be wrong. flybench
   reports 13% of male sugar GRNs predicted glutamatergic.
3. **Open-loop assay battery, body attached but not needed:**
   sugar→MN9 (rate and dose), bitter suppression of MN9, JO→antennal grooming,
   DNp01→TTMn, and DNg100→leg motor neuron rhythm (the Pugliese prediction
   under LIF). Every assay also runs with a degree-preserving shuffled graph
   and with zero input.
4. **Fit on one assay, test on the rest.** Fit only the global synapse scale,
   and only on sugar→MN9, as Shiu did. Score everything else held out.
   Optionally score with flybench as an independent referee.
5. **Re-run the F-GAIN-1 sweep under this profile.** Record the answer:
   - If pathways reproduce and the shuffled graph fails, **the anatomy is
     load-bearing**, and the noise term shrinks to a documented background.
   - If not, the failing assay names the suspect: sign (F-SIGN-1),
     cross-specimen matching, or the neuron model.

*Exit:* a table of assay × {real, shuffled, silent} with predicted versus
published outcomes, and a new F-GAIN-2 finding.

## Session 5: the neuron model, changed only where an assay fails

Rank candidates by the failures seen in session 4. Current priors:

- **Spike-frequency adaptation** (flybench evidence; biologically ubiquitous).
  Cheap to add.
- **Graded optic lobe.** Photoreceptors and many optic-lobe cells do not
  spike, and spiking whole-brain attempts reportedly lose visual signal.
  Import the flyvis (Lappalainen 2024) graded model for optic-lobe types,
  labelled as task-fitted. Couple it to the spiking central brain through the
  visual projection neurons.
- **Retinotopy (fixes F-VISION-1).** Assign ommatidia to photoreceptors
  through their postsynaptic lamina/medulla column partners (L1-L5, Mi1, Tm)
  where those carry column identity. This must be verified before any looming
  or motion assay counts.
- **Per-type biophysics only where measured:** motor neurons (Azevedo 2020),
  the giant fibre, PNs, KCs and other cells with published recordings. All
  other types stay on the shared default, with the reason recorded.
- **Deferred until a test implicates them:** conductance-based synapses,
  terminal-aware axo-axonic input, and gap junctions (data absent).

*Exit:* the session-4 battery re-scored, plus added visual assays (looming→GF
escape, optic-flow turning), each with a shuffled control.

## Session 6: the motor periphery, from spikes to force

- **One motor unit per motor neuron**, not one actuator per joint pool. Use
  per-spike force from the Azevedo 2020 size-principle data (Dryad
  10.5061/dryad.76hdr7stb) and a twitch-shaped activation. The size principle then becomes
  expressible.
- **Muscles replace torque motors.** Adopt Hill-type leg muscles
  (Özdil/Ramdya 2025, arXiv 2509.06426) if their parameters are published.
  Otherwise project each muscle's action onto all joint axes by least squares
  (the session-3 known limitation). Re-run `calibrate_joint_signs.py` after
  either change.
- **Wire the directly identified non-leg outputs:** TTMn/STTMm to T2, and the
  proboscis pool to the rostrum, haustellum and labrum actuators.
- **Proprioceptors:** claw, hook and club tuning from published recordings
  (e.g. Mamiya 2018), replacing the direct joint-state readout.

*Exit:* simulated single-unit twitch and tetanus against Azevedo; a
DNp01-evoked jump in the body; a sugar-evoked proboscis extension in the body.

## Session 7: walking as a reproduced experiment

- In closed loop, stimulate DNg100 or DNp09 (forward) and MDN (backward) at
  the published protocol intensities. Label these as *reproductions of
  command-neuron experiments*, not spontaneous behaviour.
- Compare step frequency against stimulation intensity (Pugliese's
  optogenetic data), within-leg phase, and interleg coordination against
  measured treadmill kinematics. Pugliese could not get interleg coordination
  without a body, so the body loop is the new contribution here.
- Fit only parameters that have a biological referent (motor-unit gain,
  proprioceptor gain), on a subset of intensities, and test on the rest.

*Exit:* stepping, or a quantified reason why not, with per-layer diagnostics.

## Session 8 and beyond, in dependency order

1. **Flight.** This needs a body change first. The wing needs a hinge that is
   driven by steering muscles, plus power-muscle and thorax dynamics (Melis
   2024 is learned, so label it), and the haltere needs actuating
   (16 identified MNs). Start with an already-airborne stabilisation test.
2. **Neuromodulation.** Octopamine, dopamine and serotonin as state
   variables acting on gain and excitability, from the 4,500+ modulatory
   neurons already in the graph.
3. **Learning.** Mushroom-body DAN-gated KC→MBON plasticity, then an
   odour-shock conditioning assay held out from all fitting.

## Standing rules for these sessions

- Agent cap as in CLAUDE.md: at most three, counted recursively.
- No behavioural decoder in primary results. The arXiv 2602.17997 approach
  (learned message passing decoded to MuJoCo actions) is a comparison
  fixture at most.
- Every borrowed fitted value keeps its source and is never relabelled as
  measured. Every assay has a shuffled-graph control and a held-out split
  declared before it is scored.
- Check `ssh backhouse` at session start. When it is up, move long closed-loop
  sweeps there.
