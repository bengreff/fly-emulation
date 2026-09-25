# The brain-body interface

Ben's direction, 2026-09-15: *"the brain body interface must be complete."*
Complete here means every channel the animal has is either implemented or
recorded as a known gap with its instance count. It does not mean everything is
implemented.

**Provenance warning.** The literature counts and citations below were gathered
by a research agent in one session and are **not yet independently verified by
me**, except the `male-cns` counts in the right-hand columns, which I queried
directly. The agent marked its own confidence and flagged what it could not
reach behind paywalls; those flags are preserved. Treat every citation here as a
lead to check before any number becomes a model parameter. Several sources it
reported were explicitly "title-level only" because full text returned 403.

## Current state, for contrast

| | Implemented | Exists |
|---|---|---|
| Efferent | 328 motor neurons driving joint torques | 708 `vnc_motor` plus endocrine, enteric and efferent classes |
| Afferent | 3,246 leg mechanosensory afferents | 17,937 sensory neurons in `male-cns` |
| Physics | rigid-body contact, gravity | see Part C |

So roughly **46% of the efferent side and 18% of the afferent side** have a
channel at all, and the afferent figure is generous because the implemented
channel is a `tanh` of a joint angle rather than a transduction model.

---

## Part A. Efferent channels, CNS to body

`male-cns` counts are mine, by `superclass`/`subclass` query. Literature counts
are the agent's, mostly from MANC, a different specimen and inclusion policy.

| Channel | Target | Literature count | `male-cns` count | Implemented |
|---|---|---|---|---|
| Leg motor neurons | 14 muscles per leg | MANC: T1 142, T2 119, T3 131 = **392** | fl 135, ml 116, hl 130 = **381** | 328 mapped |
| Wing power muscles | DLM ~6 and DVM ~7 fibres, asynchronous, drive ~200 Hz thorax resonance | 12 MNs | — | none |
| Wing steering muscles | b1-b3, i1-i2, iii1/iii3/iii4, hg1-hg3 direct; tp1/tp2/tpN, ps1, tt indirect | ~16 of 21 identified; 26 wing MNs in MANC | wm **67** | none |
| Neck | ~8+ paired neck muscles, gaze stabilisation and head saccades | MANC 12 pairs, **only 3 matched to a muscle** | nm **24** | none |
| Haltere | haltere base muscles, set stroke plane and gyroscope gain | MANC 7 pairs; a female VNC dataset reportedly 32, unreconciled | hm **16** | none |
| Abdominal | body wall, oviduct/uterus, male reproductive tract | ~150 in MANC, **targets largely unidentified** | ad **214** | none |
| Proboscis and pharynx | rostrum, haustellum, labella; pharyngeal pump m.11/m.12 | 16 proboscis, 9 pharyngeal | (in `cb_motor`, 107) | none |
| Neurosecretory | corpora cardiaca/allata, hemolymph: DILPs, AKH, PTTH, ETH, bursicon, CCAP, DH44 | IPCs 12-16, varies by paper | cb_endocrine 72, vnc_endocrine 22 | none |
| Enteric and visceral | foregut, midgut, hindgut, crop, Malpighian tubules, heart | anatomical description, no count | ENS 50 | none |
| Spiracles and trachea | spiracular occluder muscles | **not located** | — | none |
| Other efferent | — | — | vnc_efferent 94, cb_efferent 4, efferent asc/desc 12 | none |

### Discrepancies I checked myself, which matter

- **Wing motor neurons: 26 in MANC against 67 in `male-cns`.** A factor of 2.6.
  Either the datasets use different inclusion policies for the wing subclass, or
  `wm` in `male-cns` covers more than the muscles MANC matched. Not reconciled.
  Do not adopt either number as the animal's.
- **Neck agrees exactly:** MANC 12 pairs, `male-cns` `nm` 24. That agreement is
  worth something, and it also carries the warning that only 3 of those 12 pairs
  have an identified muscle target even in the connectome literature. The neck is
  a gap in fly science, not only in this model.
- **Leg: 392 against 381**, close enough to be the same population under
  different policies.
- **"14 muscles per leg" against my 19 distinct muscle names.** My
  muscle-to-joint map may be conflating muscles, or including thoracic muscles
  that are not leg muscles. The tergotrochanter in particular is listed by the
  agent among *wing* indirect/tergal muscles co-opted for the jump-to-flight
  transition, which supports my suspicion in F-SIGN-4 that I have it wrong.

---

## Part B. Afferent channels, body and world to CNS

| Organ | Physical variable transduced | Literature count | `male-cns` | Implemented |
|---|---|---|---|---|
| Compound eye R1-R8 | photon flux, UV to green; R1-6 feed motion | ~800 ommatidia x 8 per eye (agent's arithmetic, not a cited total) | ol_sensory **6,098** | none |
| Ocelli | ambient light, horizon | 3 ocelli | — | none |
| Antennal ORNs | odorant identity and concentration | ~1,200 per antenna, ~52 types | — | none |
| Maxillary palp ORNs | odorant, short and long range attraction | ~120 in ~60 sensilla | — | none |
| Gustatory RNs | sugar, bitter, water, salt, contact pheromone | 4 GRNs + 1 mechanosensor per sensillum; whole-animal total **not located** | taste bristle 70, taste peg 60, pharyngeal 87, labellar 163 | none |
| Femoral chordotonal organ | claw: joint angle; hook: angular velocity and direction; club: vibration | **~152**, three subtypes | chordotonal organ 425 | partial: one `tanh(angle) + 0.1 tanh(velocity)` channel, subtypes not distinguished |
| Campaniform sensilla | cuticular strain | ~1,200 body-wide; haltere base ~140 in 5 fields, or ~400, **discrepant** | 426 | partial: driven by contact force, which is not strain |
| Hair plates | joint angle near its limit | — | 113 | partial |
| Bristles | bristle deflection, contact | — | mechanosensory 2,206, leg 768, wing 385 | partial, leg only |
| Wing proprioceptors | wing bending, twisting, load at 200-250 Hz | ~36 proximal + ~17 distal CS; 14-neuron chordotonal in tegula; 1 hair plate | wing 46 | none |
| Johnston's organ | antennal receiver deflection: JO-A/B near-field sound, JO-C/E static deflection for wind and gravity | **~480** | auditory 114, wind_gravity 475 | none |
| Halteres | Coriolis force, i.e. body angular velocity, as strain during ~200 Hz beat | 5 distinct campaniform clusters | haltere 205 | none |
| Arista thermoreceptors | temperature and its rate of change | 3 hot cells + 3 cold cells | — | none |
| Sacculus cold receptors | cooling | 15-20 | — | none |
| Hygroreceptors | humidity, moist and dry cells opposed | 3 per triad sensillum; total **not located** | — | none |
| CO2 receptor ab1C | airborne CO2 | one ORN class per ab1 sensillum | — | none |
| Nociceptors | noxious mechanical, localised poking over diffuse pressure; thermal | adult count **not located**; larval class IV characterised | — | none |
| Gut and pharyngeal sensory | food presence and flow; stretch suspected | **unresolved in the animal**: a source states gut stretch receptors "remain to be established" in *Drosophila* | abdomen 1,143 | none |
| Enteroendocrine nutrient sensing | dietary sugar and amino acid concentration | not quantified; **humoral, not a neural afferent**, so it needs a different channel type | — | none |
| Oxygen sensing | — | **not located** as a discrete system | — | none |
| Efferent control of sense organs | octopaminergic gain modulation of visual processing in flight; actively tuned haltere gyroscope gain | — | — | none |

### The photoreceptor discrepancy

A fly has roughly 6,400 photoreceptors per eye by the agent's arithmetic, so
about 12,800 in total. `male-cns` carries **6,098** `ol_sensory` neurons
altogether. Whatever the resolution, the primary graph does **not** contain a
photoreceptor per ommatidium per eye, so a vision model built on this graph is
building on a subset and must say so. Unverified on both sides; flagged.

---

## Part C. Physics the interface implies

A rigid-body contact simulator can drive almost none of the channels above.

| Physics | Drives | Standard approach | Status here |
|---|---|---|---|
| Tarsal adhesion, claw and pulvillus mechanics | leg contact afferents, all stance | two-phase: claw interlocking on rough substrate, wet adhesion via tarsal fluid on smooth; peeling-force law plus meniscus term | absent. Without it, wall and ceiling walking are not reproducible at all. The agent could **not locate** a citable *Drosophila*-specific primary source, so this is a research gap as well as a model gap |
| Unsteady flapping aerodynamics | wing efferents, wing proprioceptors, haltere Coriolis sensing | quasi-steady blade element plus added mass, rotational (Kramer) and wake capture terms; CFD at Re ~100 | absent |
| Air flow field | Johnston's organ wind mode, plume tracking | wind field simulated jointly with odour, since JO senses wind as antennal deflection | absent |
| Acoustic near field | Johnston's organ sound mode | *particle velocity*, not pressure: near-field viscous flow around the antenna, not a free-field audio model | absent |
| Light transport | photoreceptors, ocelli | per-ommatidium irradiance, spectrally weighted by opsin curves Rh1, Rh3-Rh6 | absent |
| Odour plume advection and diffusion | ORNs, CO2 receptor | turbulent scalar transport; flies respond to filament intermittency and whiffs, not mean gradients | absent |
| Hemolymph and humoral transport | neurosecretory efferents, enteroendocrine signalling | compartmental concentration states with production and clearance | absent |
| Tracheal gas exchange | spiracle efferents, internal O2/CO2 | reaction-diffusion through a branching tree, spiracles as boundary conditions | absent |
| **Cuticle deformation** | **every campaniform sensillum** | thin-shell or FEA deformable cuticle; recent *Drosophila* work builds parametric FEM leg models specifically to place campaniform sensilla | absent, and this one is structural: strain is the literal variable these organs transduce, so driving them from rigid-body contact force **silently changes the channel's transfer function** to something the organ does not measure |

---

## Gaps that are gaps in fly science, not just in this model

Recorded separately, because "no one has measured this" is a different claim
from "not implemented", and the project rule is that unknown must never become
measured absence.

1. Gut and pharyngeal stretch receptors: a source states these "remain to be
   established" in *Drosophila*.
2. Oxygen-sensing neurons: not located as a discrete system.
3. Whole-animal gustatory receptor neuron total: paywalled, not located.
4. Haltere motor neuron count: two connectome datasets disagree, unreconciled.
5. Adult nociceptor counts: not located.
6. A citable *Drosophila* tarsal-adhesion biomechanics paper: not located.
7. Neck motor neuron muscle targets: only 3 of 12 pairs identified in MANC.
8. Abdominal motor neuron targets: "largely unidentified" in MANC.

## Ranked order for adding channels, as reported and as I read it

The agent's ranking, which I find defensible for a walking-then-flight goal:
wing efferents plus aerodynamics first, because flight is 100% missing and the
wing steering system is unusually well characterised; then the haltere loop,
because wings without halteres give an uncontrollable flapper; then vision with
light transport; then neck motor plus wing/neck proprioceptors, since vision is
useless for gaze stabilisation without a neck; then Johnston's organ for wind
and gravity; then olfaction with plume physics; then abdominal, proboscis and
enteric/endocrine; then nociception, temperature, humidity and taste.

I would put one thing ahead of all of it: the leg interface is not finished. It
has 28 measurably inverted signs (F-SIGN-4), no joint limits and one shared
passive stiffness (F-BODY-3), and campaniform sensilla driven by the wrong
physical variable. Adding wings to that is building the second storey first.
