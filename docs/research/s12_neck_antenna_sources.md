# Neck and antennal motor neuron directions (s12)

Source search for HANDOFF s12 Next item 2, the neck and antenna drive signs (`data/params/motor_targets.csv`, +1 on both sides with no antagonists, guessed). One agent ran it on 4 October 2026, about 21:25-21:48, using open sources only. The values were read by the agent, not by me.

## Neck

- **Gorko et al. 2024** (Nature 628:596, "Motor neurons generate pose-targeted movements via proprioceptive sculpting"). The paper itself is paywalled; what follows comes from open commentary (PMC11362485) and news summaries.
  - Activating one identified neck motor neuron does not rotate the head in a fixed direction. The head converges on a target pose specific to that neuron, and the direction depends on the starting angle.
  - Example (measured): with the head pitched up, CvN7 activation pitches it down. With the head pitched down, the same activation gives a weaker pitch up.
  - Silencing the lateral neck chordotonal neurons abolishes the convergence (measured).
  - So a fixed per-neuron torque sign is itself an approximation. The target pose comes from motor drive plus neck proprioception.
- **Muscle identity** (Cheong, Eichler, Stürner et al. 2024, eLife 96084, open access):
  - MANC has 12 neck motor neuron pairs, defined by neck tectulum input and exit via the cervical or dorsal prothoracic nerve (inferred).
  - Only 3 pairs are tentatively homologised to named Calliphora neck muscles (Strausfeld 1987, paywalled; the authors flag this as uncertain; Supplementary file 3).
  - No yaw, roll or pitch direction is given for any pair.
- The GNG-numbered neck types (GNG276, GNG283, GNG641, GNG648, GNG650, GNG653) have no functional description in accessible sources.
- No source gives resting head angles or tonic neck motor neuron rates in a standing fly.

## Antenna

- **Suver, Medina & Nagel 2023** (Curr Biol; bioRxiv 2022.09.30.510392):
  - Four scape muscles move the scape-pedicel joint (anatomy after Miller 1950).
  - Driver 18D07-GAL4 labels 2 motor neurons on muscles 1 and 4. Activating them moves the antennae **forward and up** (measured, optogenetic activation and video).
  - The pedicel-funiculus joint is passive.
- The model's antennal types (GNG133, GNG649, GNG651, GNG652, GNG668, PS348) have no accessible description. Which of them are the 18D07 cells is unknown, so no per-type sign can be set.

## What can be fixed without a per-neuron table

- Head yaw and roll flip sign under left-right reflection, and head pitch does not. In the model, all 10 + 10 yaw and 7 + 8 roll motor neurons map +1 on both sides, so a bilateral pair pushes the head the same way.
- Bilateral symmetry alone (derived) puts mirror-image neurons on opposite yaw and roll signs. The absolute direction of each type stays guessed. Pitch is unchanged.
- The antennae are already per side (`{s}`), so their signs are not a symmetry question. Their elevator/depressor balance needs the per-type table above, and it is not available.

## For Ben's list

- Gorko et al. 2024 (Nature) main text and supplement: the per-neuron target poses and any mapping to MANC types.
- Strausfeld et al. 1987 (Calliphora neck muscles).
