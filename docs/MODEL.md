# The model (current)

What the simulator computes today, with the default of every mechanism. Values come from the registry, which labels each one measured / derived / inferred / guessed (`docs/WORKFLOW.md` §3). The per-run `inventory.csv` is the authoritative list; this file explains it. Earlier model families are in `docs/archive/MODEL_M_v1.md`.

**Names.**
- **M2** is the model family: the equations below, implemented in `src/flyemu/lif.py`.
- **m4** is the parameter profile in use (session 8), `src/flyemu/profiles.py`: m2 plus transmitter identity from `consensusNt`, efficacy 0.15675 mV (m3), and monoamines with no fast sign (M0). m2 and m3 are kept; `FLYEMU_PROFILE=m2` reproduces sessions 5–8.
- The **working model** is family M2 with profile m4 and edges of ≥ 5 synapses (`profiles.WORKING_PROFILE`, `WORKING_MIN_SYNAPSES`). Scripts default to it.
- ("M2 Pro" in `docs/ENVIRONMENT.md` is the Mac, unrelated.)

## Loop

```
body state -> afferent drive -> network (LIF) -> motor spikes -> motor units -> joint torque -> body
```

`src/flyemu/organism.py` runs this at a 0.1 ms step. Nothing bypasses these channels: no controller, no decoder, no prescribed gait. `Organism.sense()` is the single place where the world and body reach the network.

## Network

**Graph.** male-cns v1.0 (neuPrint): 167,111 neurons (traced, or typed), 6,241,231 edges with ≥ 5 synapses, 89.85 M synapses (measured). `src/flyemu/connectome.py`.

**Neuron.** Leaky integrate-and-fire per cell type (`lif.py`):

```
tau_m dV/dt = -(V - V_rest) + I_syn + I_slow + S + D_ext - A
tau_s dI_syn/dt = -I_syn + sum of arriving weights
spike at V >= V_th, reset to V_reset, refractory t_ref
```

- The shared defaults come from profile m2 (inherited by m3): V_rest −52, V_th −45, V_reset −52 mV, τm 20 ms, t_ref 2.2 ms, τs 5 ms, no membrane noise, synaptic current reset on spike. These are borrowed from Shiu et al. 2024: inferred.
- Per-type rows in `data/params/cell_types.csv` override them:
  - photoreceptors are graded (measured); L1–L3 and APL are graded (inferred);
  - the 60 slow tibia-flexor MNs are fitted to Azevedo 2020 raw recordings: τ 16 ms, threshold +32.6 mV, t_ref 4.27 ms, tonic drive 36.45 mV (inferred; F-AZ-2, F-AZ-3).
- **Q10 = 2** at a 25 °C reference: τm, τs and t_ref scale with world temperature (inferred).

**Synapse.** The weight of edge i→j is:

```
sign_i × efficacy × n_syn(ij) × release_gain_i × input_gain_j
```

- efficacy = **0.15675 mV per synapse** everywhere (m3): inferred, fitted by calibration rule v3 (closed-loop return to rest on 3 seeds under consensusNt; DECISIONS s8). m2 used 0.165 mV (rule v2).
- Sign by transmitter. m3 takes the call from the curated `consensusNt` (F-NT-1; `connectome:all|nt_source_consensus`), m2 from the EM classifier `predictedNt`:
  - ACh +; GABA −; glutamate −; histamine −;
  - dopamine, serotonin and octopamine: 0 in m4 (they act only through the neuromodulator pools); + in m2/m3 (placeholder);
  - unclear + (but AL local neurons with unclear transmitter −).
- Two profile rules:
  - m1: no chemical input onto sensory terminals (F-SENS-1);
  - m2: no chemical output from cholinergic AL LNs onto PNs or eLNs (F-LN-1).
- Glutamate sign per postsynaptic type from transcripts for 51 types (−1 for 49 GluCl-dominated types, iGluR/GluClα TPM ratio < 0.1; +1 for Dm9 and T1; Davis 2020, Turner-Evans 2020; F-RCPT-1).
- **Delay** per presynaptic type = 0.5 ms + path length / velocity.
  - untyped cells: path length predicted from volume, synapse counts and superclass (F-DELAY-2; `cell_type:untyped|inferred_conduction_delay`).
  - typed cells: the path length is measured on the type's skeleton; v = 0.5 m/s (inferred), or 2.07 m/s for the giant fibre (measured). F-DELAY-1, `data/params/conduction_delays.csv`.

**Mechanisms, and their switches at their defaults** (registry keys, `entity|property`):

| Mechanism | Key | Default |
|---|---|---|
| Spike-frequency adaptation | `cell_type:all\|adaptation_increment` | 0 (off; F-SFA-1) |
| Short-term depression | `cell_type:all\|std_release_fraction` | 0 (off; F-STD-1) |
| Graded transmission | `graded` rows in `cell_types.csv` | listed types only |
| Conductance-based synapses | `cell_type:all\|conductance_based` | 0 |
| Morphological delays | `cell_type:all\|morphological_delays` | **1 (on)** |
| Neuromodulator pools (DA, OA, 5-HT) | `mod_sensitivity_*` per type | pools run; sensitivities 0 (inert). Receptor-signed candidate for 68 types: `data/params/candidates/candidates_s8_modsens.csv` (adopted, then reverted in s8: sustains a ~9 Hz brain under T) |
| Glutamate sign per target type | `cell_type:all\|glutamate_receptor_sign` | 0 = transmitter default; **54 types have transcript rows** (F-RCPT-1) |
| GABA-B slow share | `cell_type:all\|gabab_fraction` | 0 |
| Presynaptic inhibition of sensory terminals | `cell_type:all\|presynaptic_inhibition_gain` | 0 |
| DAN-gated KC→MBON depression | `cell_type:all\|kc_mbon_ltd_rate` | 0 (off) |
| GF electrical synapses | `electrical.py` | off (F-GJ-1) |
| VNC sensorimotor efficacy scale | `connection_class:vnc_sensorimotor\|efficacy_scale` | 1 |
| Inhibitory AL LN → PN postsynaptic scale | `connection_class:inhibitory_AL_LN_to_PN\|postsynaptic_scale` | 1 |
| ORN → uPN efficacy scale (s7; 10.9 = measured uEPSP) | `connection_class:ORN_to_uPN\|efficacy_scale` | 1 (F-AL-4) |
| ORN → uPN homeostatic matching (s7) | `connection_class:ORN_to_uPN\|homeostatic_matching` | 0 |
| ORN output depression, Nagel 2015 (s7) | `afferent:ORN\|measured_depression` | 0 |
| Leg proprioceptor output scale (s7; config T) | `connection_class:leg_proprioceptor_output\|efficacy_scale` | 1 (F-XFER-1) |
| Leg proprioceptor depression (s7; config T) | `afferent:leg_proprioceptors\|transferred_depression` | 0 |
| Transmitter source (s8) | `connectome:all\|nt_source_consensus` | **1 in m3/m4** (consensusNt) |
| Inferred untyped-cell delays (s8) | `cell_type:untyped\|inferred_conduction_delay` | **1 (on)** |
| CX ring per-class input normalisation (s8) | `cell_type:cx_ring\|class_input_normalisation` | 0 (screened; no bump) |
| Background noise / warm start (s8) | `cell_type:all\|background_noise`; `scripts/probes/warm_start.py` | 0 (F-WARM-1) |

Candidate per-type rows are tested without editing live tables: `FLYEMU_EXTRA_PARAMS=<csv>` appends rows to `cell_types.csv` (later rows win), `FLYEMU_PROPRIO_ASSIGNMENT=<csv>` replaces the proprioceptor assignment table, and `FLYEMU_EDGE_SCALES=<csv>` (s8) scales edges by presynaptic and postsynaptic type regex. Tested candidate rows (sessions 7–8) are in `data/params/candidates/`; none is live.

Every switch that is off or neutral was tested and not adopted, or is waiting for data. The results are in `docs/FINDINGS.md`.

## Senses (`sensory.py`, `vision.py`, `olfaction.py`, `extrasenses.py`)

**Leg proprioceptors.**
- Subtype per male-cns type comes from the BANC crosswalk (derived, F-SENSE-2): claw (position), hook (direction), club (movement), hair plates (joint limit).
- Tuning form follows Mamiya 2018/2023 and Pratt 2026 (inferred). Direction per type is inferred from wiring (`scripts/proprio_direction.py`).
- The femur-tibia angle is computed from segment geometry.
- Transduction: drive = 2 mV + 8 mV × signal (guessed). Rate mode, `afferent:leg_proprioceptors|rate_mode_max_hz`, is 0 (off).

**Other body senses.**
- Campaniform sensilla: load transmitted through the segment (derived proxy).
- Bristles: contact.

**Vision.**
- Every photoreceptor reads its own ommatidium: retinotopy derived from the connectome (F-VISION-2).
- The renderer's pale/yellow mask per eye comes from the connectome (F-VISION-3). Opsin λmax is stored but not yet used.

**Olfaction.**
- ORNs fire Poisson at Hallem & Carlson 2006 rates, measured for 24 types: spontaneous in clean air, up to Rmax with odour (F-ORN-1/3).
- Relative tuning comes from DoOR 2.0 (measured).
- CO2 and humidity are tonic; temperature is phasic.

**Everything else** (taste, head touch, Johnston's organ, wing/haltere campaniforms, trunk): `extrasenses.py`, mostly guessed gains (F-SENSE-ALL). About 1,561 sensory neurons of unidentified modality get an explicit zero drive.

## Motor output (`neuromuscular.py`)

- 756 of 815 motor neurons drive a body actuator. Leg MNs use a measured muscle→joint map with signs from the body calibration (`data/derived/joint_signs_flybody.csv`, re-measure after body changes). Non-leg MNs use `data/params/motor_targets.csv` (F-MOTOR-2).
- **Motor units:** each MN has its own activation; a spike adds its torque, which decays with its own twitch τ.
  - Leg MNs take torque per spike from `data/params/motor_forces.csv`: tibia flexor classes from Azevedo 2020 (derived); the rest size-scaled (inferred); twitch τ 30/100 ms (guessed). F-MOTOR-3.
  - Other MNs use `motor_unit:all|force_per_spike`, registry default 1 µN·mm (guessed). **All runs since session 5 set it to 10**, e.g. `--set 'motor_unit:all|force_per_spike=10'`; the probes do this.
- **Grip:** tarsal adhesion driven by the long-tendon MN pool (a substitute mechanism).

## Body (`body.py`, `joints.py`)

- flybody via flygym 2.1, MuJoCo, 0.1 ms step.
- 0.985 mg (derived from weighed flies).
- 102 joint DOFs with ranges and 98 torque actuators on real articulations.
- Self-collision, tarsal adhesion, tendons, quasi-steady aerodynamics.
- **Femur-tibia range:** the anatomical 18–180° is mapped through the measured geometry (F-BUG-7). `obs["joint_angles"]` is ordered by joint DOF, not actuator (F-BUG-6).

## Not simulated

The largest absent mechanisms, from the ledger (`data/derived/blank_ledger.csv`):
- explicit ion channels;
- dendritic compartments;
- glia;
- neuropeptides and co-transmitters;
- other postsynaptic receptor subtypes;
- muscle force–length–velocity;
- neuroendocrine and internal-state systems.

There is also no background activity: the working model is noise-free. Many cells therefore rest exactly at V_rest, which is the current diagnosis for the silent relay cells (F-AZ-2, F-VNC-1, F-AL-3).
