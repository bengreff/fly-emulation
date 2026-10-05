# Wing hinge stiffness, steering-muscle levers and resting wing activity (s12)

Source search for the wing-rest item (HANDOFF s12, F-NONLEG-1): one agent, 4 October 2026, about 21:25-21:37. Open sources only; paywalled items are listed as not read. The values below were read by the agent, not by me, except where marked.

## Hinge stiffness

| Quantity | Value | Basis | Species, condition | Source |
|---|---|---|---|---|
| Wing-pitch (rotation) torsional stiffness | 91 ± 9 pN·m/deg = 5.21 ± 0.52 µN·mm/rad | fitted | D. melanogaster, free flight, 9 wingstrokes | Bergou, Ristroph, Guckenheimer, Cohen & Wang 2010, PRL 104:148101, Eq. 2, Fig. 2a, 3a-c |
| Wing-pitch damping | 39 ± 12 fN·m·s/deg = 2.2 × 10⁻³ µN·mm·s/rad | fitted | same | same |
| Pitch rest angle | 90 ± 1° (wing vertical in the stroke frame) | fitted | same | same |
| Simulation reference stiffness | 50 pN·m/deg = 2.9 µN·mm/rad | guessed (a model convenience value) | Drosophila model | bioRxiv 2025.11.02.686144 (PMC12637562), Fig. 4j-l. The authors find no structure that alone acts as a pitch spring. |
| Stroke-axis stiffness | 26,300 µN·mm/rad (moth), 6,510 µN·mm/rad (honeybee) | fitted (forced-oscillation resonance) | Euxoa auxiliaris, Apis mellifera | PMC12440615, Table 1. A different axis and much larger insects. Not transferred. |

Not read: Beatus & Cohen 2015 (PRE 92:022712, paywalled), Bergou, Xu & Wang 2007 (JFM 591:321, no Drosophila value recovered), Wisser & Nachtigall 1984 (Calliphora hinge geometry, paywalled).

No source gives the stiffness of the **folded** hinge, or of the yaw (stroke) or roll (deviation) axes in Drosophila.

Unit check (mine): 91 pN·m/deg × 57.296 deg/rad = 5.214 × 10⁻⁹ N·m/rad = 5.214 µN·mm/rad.

## Steering-muscle levers

- Melis, Siwanowicz & Dickinson 2024 (Nature 628:795; bioRxiv 2023.06.29.547116v3) give the insertions: basalare → b1-b3; first axillary → i1, i2; third axillary → iii1-iii3; fourth axillary → hg1-4 (iv1-4).
- They state the lever only qualitatively: ax1 insertions lie medial to the ax2 fulcrum and ax3 insertions lie distal to it, which is why ax1 muscles raise the stroke and ax3 muscles lower it.
- They give no moment arm in µm.
- Walker et al. 2014 (PLOS Biol, Calliphora micro-CT) gives strain, not moment arm.
- Deora, Gundiah & Sane 2017 (JEB 220:1382) is conceptual only.
- So the 2.64 mm wing-length lever in `data/params/nonleg_motor_forces.csv` has no measured replacement.

## Muscle force

No accessible primary source. One unverified search-engine claim (Calliphora b1 peak force about 10⁻² N) is not used.

## Wing motor activity at rest

- **iii1.** Melis 2024: "rarely active during flight", and likely homologous with the ancestral wing-folding retractor (Willkommen & Hörnschemeyer 2007; homology argument, inferred).
- **Flight classes.** Lindsay, Sustar & Dickinson 2017 (Curr Biol 27:345, full text paywalled, classes read via Melis):
  - tonic in flight: b1, b3, i2, iii3, iv4;
  - phasic: b2, i1, iii1, iv1.
- **At rest.** No source says whether any steering motor neuron fires during standing or walking. This is open.

## Spike to wing angle

- Only qualitative: b1 spike phase, not count, sets stroke amplitude (Tu & Dickinson 1996; Balint & Dickinson 2001; both paywalled, abstracts only).
- No degrees-per-spike value exists in accessible sources.

## Used

- `joint:wing|stiffness_source` 1 (DECISIONS s12 21:44): Bergou 2010 pitch stiffness on all three wing hinge axes.
  - Pitch: fitted.
  - Yaw and roll: inferred transfer.
- Damping stays flybody's 0.05 µN·mm·s/rad (unsourced). This is one change at a time. With the model's 10⁻⁴ armature, Bergou's damping would leave the hinge ringing (ζ about 0.05).
