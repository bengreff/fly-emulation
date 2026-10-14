# Minimal proprioceptive loop for standing: repo state and measured inputs (s13 fly2, 13 Oct 23:50)

Agent-gathered (Sonnet, read-only survey, 13 Oct 23:47-23:50). Not yet checked line by line. Items marked "secondary" or "not found" are not usable as sources until read in the primary text. Purpose: inputs for the pre-registration of fly2's next body step (Director, 13 Oct). The fly stands under constant support plus FeCO/CS resistance reflexes through the real connectome (F-STAND-6).

## A. What the repo has

- **Afferent models (`src/flyemu/sensory.py`).** `ENCODES` (≈45-53): chordotonal organ → joint angle and velocity, hair plate → joint angle, campaniform sensilla → load. The measured-form transduction (`_measured_form`, ≈445-536, session 6):
  - FeCO claw: a tonic sigmoid of the anatomical femur-tibia angle. Per-cell θ50 spreads over 20-80° (flexion) and 90-170° (extension), width 10° (INFERRED; Mamiya 2018/2023).
  - Hook: rectified angular velocity, saturating at 200°/s, split by direction (gain GUESSED).
  - Club: |angular velocity| through tanh. Vibration is not simulated.
  - Hair plates: tonic sigmoids at 85 ± 5% of the ThC/CTr range.
  - CS: transmitted segment load (MuJoCo `cfrc_int`) as a strain proxy (DERIVED).
  - Defaults: `afferent:all|rate_gain` 8 mV/unit (GUESSED), `afferent:all|resting_drive` 2 mV, `afferent:leg_proprioceptors|rate_mode_max_hz` 0 (mV mode, not Poisson).
- **Cell selection.** `assign_by_nerve` mode 2 in m10f0 (per-cell entry nerve/root side, F-SENSE-NERVE-2). Subtypes come from an unverified BANC crosswalk (`data/params/proprio_assignment.csv`). **The front-leg FeCO is under-assigned:** about 60 chordotonal axons against the 150-170 expected. F-REFLEX-1 found 4 claw + 4 hook on the left front leg, against 21-30 claw and 11-18 hook on the mid and hind legs.
- **Delay.** No afferent delay exists: `sensory:peripheral_axon|conduction_delay` is UNRESOLVED and omitted (lif.py ≈262-266). Central delay is the global 1.8 ms, or per-type morphology (0.5 ms + L/v, v ≈ 0.5 m/s, `data/params/conduction_delays.csv`).
- **Stepping pattern.**
  - `bypass_s2_descending.py` turns the brain off, never calls `org.sense()` (senses off), and steps `org.net.step` and then `org.motor_step(sp)`. Reuse it with `org.sense()` on, limited to the leg proprioceptors.
  - `bypass_s1_actuation.py` REPLACES `h.activation`/`h.coxa_activation` and steps no network. For the loop, the constant bypass must be ADDED inside `HillLegDrive.torque()` (`muscles.py` ≈423 `a = self.activation(nm)`, ≈429 `coxa_activation()`), clipped to [0, 1], so MN-driven activation sums with it.
- **F-REFLEX-1, still open.** With the joint clamped and oscillated, the front-leg flexor MNs stay tonic (16-19 Hz), the same with afferents zeroed, and the 2 extensor MNs stay silent. The afferents fire (hook 24 Hz phasic, claw ~7 Hz tonic), but their direct and 2-hop paths land on MNs held under tonic inhibition (IN13A006/014, IN08A005, IN19A005, IN21A002, DNg105). Nothing since has addressed that inhibition or the front-leg assignment.

## B. Literature (measured only)

1. **FeCO.** Mamiya, Gurung & Tuthill 2018, *Neuron* 100:636-650 (GCaMP6f, no spikes). Claw: tonic position, flexion and extension subpopulations, a goniotopic map over ~90°. Hook: phasic, direction-selective. Club: vibration-tuned, bidirectional. Mamiya et al. 2023 *Neuron* adds hysteresis. **No absolute firing rates for any FeCO subtype** (calcium only; F-GAP-1).
2. **CS, Drosophila:** no verifiable Dallmann/Tuthill paper with field-level load gains was found. The repo's "Dallmann et al. 2025 Nature" DOI is flagged unverified (SENSORS_MECHANO.md). Measured CS physiology exists in blowfly (Zill et al. 2025, *J Neurophysiol*: force plus dF/dt, hysteresis), not in Drosophila.
3. **Delays:**
   - Afferent spike → postsynaptic EPSP 5-15 ms, and vibration-afferent latency ~8 ms: secondary (web summary), primary source not located.
   - Karashchuk et al. 2024, *eLife* 13:RP99005: walking is robust up to ~8-10 ms sensory and ~25-30 ms motor delay. Model-inferred, not a direct measurement.
   - "Chockley 2022": not found.
   - **A measured Drosophila sensory delay is still a blank.** The pre-registration must either find the primary value or state the delay as inferred, with a sweep across the band.
4. **Pathway.** Agrawal et al. 2020, *eLife* 9:e60299: 13Bα (femur-tibia angle, postural; nonspiking), 9Aα (movement), 10Bα (vibration). Direct claw → flexor-MN contacts (66 synapses) are present in male-cns (DECISIONS s11 ≈200).

## Recipe and blanks

- **Buildable now:** brain off, leg proprioceptors on, network stepped each tick, constant support added at `HillLegDrive.torque()`. Claw/hook/club tuning shapes, per-type central delays, relay-cell identities.
- **Blanks:** absolute afferent rates (the mV gain of 8 is guessed), a Drosophila afferent delay, front-leg FeCO completeness, the tonic VNC inhibition on the tibia MNs (F-REFLEX-1), and a Drosophila CS gain.
- **Expected first-order risk:** the loop may not reach the MNs (F-REFLEX-1). If so, that is a localisation result in itself, not a reason to tune gains.
