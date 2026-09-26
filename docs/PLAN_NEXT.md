# Plan for sessions 4 to 8

## After session 6b (26 Sept morning): the next discriminating experiments (read first)

0. **The VNC operating point (F-AZ-2).** This is the current bottleneck for every leg behaviour.
   - The held-out reflex of Azevedo cell 180111_F2_C1 fails because the excitatory premotor interneurons (IN03A004, IN21A004, IN21A006) sit 5–10 mV below threshold under tonic GABA, mainly from IN13A005.
   - The reflex signal has the right sign but is rectified away. Only 8% of T2 interneurons fire at rest.
   - Constrain the resting activity of VNC interneurons from recordings. Agrawal 2020 raw data are now local (F-VNC-1; fetch more with `scripts/fetch/zenodo_zip_members.py`).
   - 13Bα and 10Bα are measured nonspiking. Fit graded operating ranges to the 13Bα Vm-angle tuning (the ramp-and-hold set), pre-registered, with no reflex data.
   - The slow MN's tonic drive should then move from intrinsic to synaptic (Azevedo: its rest rate is synaptically set).
   - Then re-run `scripts/probes/azevedo_reflex.py` **unchanged**. All conditions of this cell have now been seen at least once, so a second recorded slow cell (e.g. Dryad 181021_F1_C1) is the fresh held-out set. Do not fit further on 180111.
   - **Match 13Bα among the model's 13B cells** by morphology/connectivity, using T2/T3 (front-leg claw axons are missing from male-cns). Then fit afferent rate × VNC gain to the 13Bα tuning (F-VNC-2), and test on 10Bα/9Aα plus a second slow MN cell.
1. **AL spontaneous state (F-AL-2).** Test presynaptic/GABA-B LN inhibition against measured PN spontaneous rates.

## After session 6: the next discriminating experiments

1. **The sensorimotor gain (F-STAND-1, F-REFLEX-1).** The leg reflex arc has the right sign but too little gain, and slow flexor MNs are position-blind. A single VNC efficacy scale cannot fix this (sweep ×1–3).
   - Next, give leg MNs per-class biophysics from Azevedo 2020 Fig 3, together: Vrest −48/−60/−68 mV and Rin 700/300/150 MΩ, with the 30 Hz rest rate emerging rather than imposed.
   - Then score `scripts/probes/reflex_gain.py` against Fig 6.
   - **Ben:** the Dryad raw data (10.5061/dryad.76hdr7stb, CC0) needs a logged-in download. One slow-MN cell zip (~200–500 MB) would give Hz/deg directly.
   - Find measured VNC numbers: FeCO→premotor→MN EPSP sizes and afferent spike rates. Candidates are Agrawal et al. 2020, Dallmann et al. 2025 (unverified), and locust and stick-insect FeCO spike rates as priors.
   - Set a VNC-specific efficacy or afferent rate scale from those numbers only.
   - Pre-register, then re-score "stands" and the resistance reflex. Do not tune on standing.
2. **Re-derive the efficacy scale under morphological delays.** Calibration rule v2 was not re-run after F-DELAY-1, and sugar→MN9 at 100 Hz went from 7.5 to 26 Hz.
3. **F-ORN-2 attractor.** Find the minimal self-sustaining set (Mi18, Lawf2, Pm, Dm, DNg12) and its route from the ORNs. Candidates: Lawf2's unclear transmitter, which is treated as excitatory, and missing adaptation. Then re-enable Hallem rates. Stability must be scored across ≥ 6 seeds.
4. **Hind-leg thorax-coxa signs.** Standing flips between tipping and not tipping with the re-measured calibration. Least-squares multi-axis muscle action is the session-3 known limitation.
5. **Walking (stretch).** Only after 1 passes: DNg100/DNp09 stimulation in closed loop (Session 7 below).


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

**Done 24 Sept, see F-GAIN-2.** The anatomy is load-bearing (real graph ≠ shuffled everywhere), but it ignites through self-exciting cliques; calibrated scale 0.165 mV. Held out: sugar weak pass, water fail, GF→TTMn fail (gap junctions), DNg100 recruits but no rhythm. Session 5 therefore starts with adaptation, then gap junctions for identified pairs.

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

**Progress 24 Sept, evening (F-SFA-1 … F-STD-1, reviewed by an independent agent):**
- Rejected by pre-registration: uniform adaptation, volume-scaled input resistance, uniform short-term depression.
- Input onto sensory terminals was dropped (m1); it changed no held-out result.
- Bugs fixed after review: rewired-control efficacy, 1-step delay error, lost refractory kicks, calibration rule.
- **F-TYPE-1:** a cell-type block-preserving shuffle reproduces nearly every result; only sugar→MN9 shows neuron-level dependence.
- F-DATA-3: MN9_R and other pharyngeal MNs are "Hard to trace"; readouts now exclude flagged cells.
- flybench (independent simulator) scores m1 at 1/18 unseen tasks, graded 0.65.

**The central conflict:** at any single synaptic scale, the model either transmits the weaker known pathways (water, JO-F) or stays stable. The real animal does both. Uniform single-mechanism fixes have so far failed. Conductance-based synapses were tested: sugar-stable to 0.8x, but they still fail rule v2. **F-LN-2 locates the conflict in the antennal lobe:** odour input ignites the model at every usable scale. Ranked next:
0. **Done (F-AL-1): m2 adopted.** The AL corrections make the model stable under odour input and raise held-out olfactory physiology from 0.54 to 0.80. Next inside the AL:
   - add eLN-PN gap junctions to restore lateral excitation (Yaksi & Wilson 2010);
   - check the PN transfer function saturation;
   - find why CO2 does not reach PNm1.

   Then **re-run the full flybench suite and the fresh-assay battery on m2**, and re-open the remaining failures: water→MN9, JO-F, JO-C/E→MDN, and PSI→DLMn (subthreshold chemical synapse). Superseded plan for this item, kept for the record: **Antennal lobe physiology, fitted to AL recordings only.**
   - eLN→PN as gap junctions instead of chemical synapses (Yaksi & Wilson 2010).
   - ORN presynaptic inhibition as a divisive gain on ORN output (Olsen & Wilson 2008).
   - An AL-specific synaptic scale fitted to the PN transfer function (Olsen et al. 2010; flybench task 17), never to behaviour.
   - Then rule v2 again. Pre-register before building.
2. **The ignition cores are type-level cliques** (lLN1_bc; the KC/CX recruits). Find the minimal self-sustaining set under rule v2 and ask what the animal has that the model lacks there: graded APL, a GABAergic LN partner, gap junctions to PNs (eLNs are electrically coupled, Yaksi & Wilson 2010).
3. **Assays that need neuron-level wiring.** F-TYPE-1 says the current battery cannot distinguish the scanned individual from its type-level average. Add assays whose published result depends on identified single cells (e.g. left/right-specific steering, DNa02 vs DNa01; retinotopic LC→DN) and score them against the type null.
4. Gap junctions for GF→TTMn/PSI.
5. Presynaptic inhibition at sensory terminals as a divisive output gain (restores what m1 removed).


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
