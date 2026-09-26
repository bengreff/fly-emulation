> **Historical — do not act on this file.** Kept for the record. The current state is in `docs/HANDOFF.md`; the procedure is in `docs/WORKFLOW.md`.

# Model family M v1

Declared before enumerating anything, because the requirement list follows from
the equations and cannot be written without them (`docs/PLAN.md` step 0). M is
an assumption, it is revisable, and every inventory figure this project quotes
is indexed by it: *for model family M and assay set A*, never a bare percentage.

## Grain

| | Choice | Why |
|---|---|---|
| Structure | per neuron | that is what the connectome gives |
| Physiology | per cell type | that is how measurements are published |
| Primary graph | `male-cns:v1.0`, whole central nervous system, male | brain and nerve cord in one specimen, live queryable, motor annotations present (F-DATA-2) |
| Type grouping | the 11,751 distinct `type` labels used as-is | any collapsing below that number is an assumption and would need a recorded rationale |
| Timestep | 0.1 ms | set by the fastest thing in scope, a ~200 Hz wingbeat |

## Equations

For neuron *i*, membrane potential *V* in mV, synaptic drive *I* in mV:

```
tau_m dV_i/dt = -(V_i - V_rest,i) + I_i(t)
tau_s dI_i/dt = -I_i + sum_j sign_j * eff_ij * n_ij * delta(t - t_j - d_ij)
spike when V_i >= V_th,i, then V_i <- V_reset,i held for t_ref,i
```

plus a membrane noise increment of `sigma * sqrt(dt)` mV per step, which stands
in for every input to the CNS that M does not model.

- `n_ij` is the anatomical synapse count. Measured.
- `sign_j` is set by the postsynaptic receptor, which the connectome does not
  contain. Settled for acetylcholine and GABA; unresolved for glutamate,
  which is 28,199 neurons (F-SIGN-1).
- `eff_ij`, the millivolts one anatomical synapse is worth, is unresolved.
- `d_ij`, conduction delay, is unresolved and currently one shared scalar.

Body: NeuroMechFly in MuJoCo, 70 segments, 126 torque-actuated joint degrees of
freedom. Model units are mm, s and g, so force is µN and joint torque is
µN·mm; the fly weighs 1.02 mg, about 10 µN.

Interfaces: afferents receive a membrane current computed from joint angle,
joint velocity and foot contact force. Motor neurons drive a first-order muscle
activation per joint, which becomes torque. Nothing else crosses in either
direction — no prescribed gait, no descending command, no world state that does
not pass through a receptor.

## What M v1 omits entirely

Listed so that "not implemented" can never be read as "biologically inactive".

| Omitted | Consequence |
|---|---|
| Dendrites and spatial integration | single compartment; no local processing |
| Gap junctions | no electrical coupling. The releases contain no comparable electrical reconstruction, so this is unknown coupling, not measured absence |
| Graded transmission | photoreceptors and many optic-lobe interneurons are non-spiking in the animal. M makes them spike. **M v1 is wrong for the optic lobe**, which is half the neurons |
| Conductance-based synapses | current-based, so inhibition cannot shunt and there are no reversal potentials |
| Short-term plasticity, adaptation | no depression, facilitation or spike-rate adaptation |
| Neuromodulation as a mechanism | dopamine, serotonin and octopamine neurons are present in the graph and carry no modulatory action; they contribute nothing |
| Long-term plasticity | no learning of any kind |
| Glia | annotated in the primary graph, absent here; potassium buffering, sleep and circadian roles all sit inside the declared boundary |
| Energy, hunger, circadian, arousal | inside the declared boundary, entirely absent from M v1 |
| Humoral and hemolymph signalling | absent |
| Force-length and force-velocity | torque is proportional to activation regardless of joint state |
| Motor units | one actuator per joint DOF, so a 47-neuron pool drives one number and the size principle cannot be expressed |
| Sensory organ mechanics | tendon coupling and antennal resonance absent; transduction reads joint state directly |
| Wing hinge | no bistable hinge mechanism; no aerodynamics |
| Vision, olfaction, taste, wind, gravity, audition, temperature | receptors present in the graph, no transduction model, so they receive no input at all |

## Assay set A0

What this version is asked to do, which is very little: stand or fall under
gravity, move its legs through its own motor neurons, and let foot contact and
joint state reach its afferents. Nothing about walking, and no acceptance
threshold. A0 exists so that the requirement list has a declared purpose behind
it rather than being everything a fly could conceivably need.
