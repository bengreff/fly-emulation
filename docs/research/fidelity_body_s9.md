# Minimum body, biomechanics and periphery fidelity per target behaviour (session 9)

Scope: everything from motor-neuron output to the world, and from the world to
sensory-neuron input. Neural fidelity is covered separately. Question: assuming
perfect data, what is the least physical machinery that lets a neurally driven
simulated adult *Drosophila* reproduce each target behaviour, and what evidence
supports that?

Evidence labels: **[verified]** means I read the paper text (full text or a
structured extraction of it) in this session. **[abstract]** means I read only
the abstract or a search summary. **[unverified]** means I cite from memory or
secondary sources; check before relying on a number. Model state was read from
the repo (`src/flyemu/body.py`, `neuromuscular.py`, `vision.py`,
`docs/MODEL.md`) and by compiling the body (`Body(vision=False)`, 2026-09-27).

## 0. What the model has now (measured from the compiled body)

- flybody via flygym 2.1. 102 hinge DOFs (+ free joint), 106 actuators in total: 98
  net-torque motors plus adhesion and tendon actuators. Timestep 0.1 ms. Mass
  0.985 mg, derived from weighed flies.
- Non-leg DOFs present: head yaw/roll/pitch, rostrum pitch, haustellum
  yaw/pitch, left/right labrum pitch, antenna yaw/roll/pitch ×2, abdomen 6
  segments × yaw/pitch, wing yaw/roll/pitch ×2, haltere pitch ×2 (no actuator).
- Passive joint parameters (compiled, units µN·mm/rad and µN·mm·s/rad): leg
  joints stiffness 1.0 with damping 1.0 (FTi damping 0.4), tarsal joints 10/0.2,
  wings 1.0/0.05, halteres 400/0.04. These are flybody group defaults, not fly
  measurements.
- Muscle model: each motor neuron adds a torque impulse that decays with a
  single twitch time constant, then the MN contributions are summed into one
  signed net torque per DOF. The legs use Azevedo 2020 force-per-spike for
  tibia flexor classes and size scaling elsewhere. Twitch τ is guessed at
  30/100 ms. There is **no force–length–velocity, no antagonist stiffness and
  no activation-dependent impedance**: co-contraction cancels to zero.
- Contact and periphery: convex-hull self-collision, MuJoCo quasi-steady fluid
  model on the wings and halteres, tarsal adhesion driven by the long-tendon MN
  pool, and a tendon-coupled tarsal chain. Vision renders 721 ommatidia per eye
  in two spectral channels with connectome-derived retinotopy. ORNs fire at
  Hallem–Carlson rates, and most other senses use guessed gains.
- Available but unused: flygym ships **FlyMimic** (Özdil et al.), a separate
  MJCF with 15 Hill-type muscle–tendon units on the left front leg only, spatial
  tendons, passive stiffness/damping with spring reference angles, and a
  0.1 ms step. Its topology does not match flybody's.

## 1. Summary table

| Mechanism | Minimal level required | Behaviours needing it | Key evidence | Our model now | Gap |
|---|---|---|---|---|---|
| Rigid skeleton, mass/inertia | Rigid segments with measured per-segment mass/inertia. Cuticle compliance is not needed for locomotion. The exception is the thorax as the flight-motor spring (see flight motor). | All | flybody: 67 rigid bodies, 102 DOFs; walking, flight and grooming postures reproduced by RL (Vaxenburg 2025, https://www.nature.com/articles/s41586-025-09029-4) [verified] | flybody, weighed masses | None for Tier A |
| Leg DOFs incl. tarsus | Coxa 3, trochanter-femur 2, FTi 1, tibia-tarsus 1, plus a passively compliant tarsal chain (4–5 joints, coupled). Claw/pulvillus as a contact patch. | Walking, slopes, grooming, landing | NMF v1 minimal DOFs from 3D kinematics (Lobato-Rios 2022, https://www.nature.com/articles/s41592-022-01466-7) [abstract]; flybody couples tarsi through a tendon [verified] | Present | Joint axes and ranges beyond FTi are partly assumed (4 measured limits) |
| Passive joint mechanics | Required, per joint: stiffness, damping and a **resting angle**, with magnitudes large relative to gravity. Without them rest posture, swing dynamics and reflex gains are wrong. | Posture, resistance reflexes, swing, grooming | Limbs under ~1 cm are elastic/viscous-dominated, not inertial/gravity-dominated (Sutton et al. 2023 PNAS Nexus, https://pmc.ncbi.nlm.nih.gov/articles/PMC10563792/) [verified]; small limbs rest at gravity-independent postures (Hooper et al. 2009 J Neurosci, stick insect/cockroach/mouse; *not* locust) [abstract]; passive forces drive the locust tibia back to mid-range even with muscles removed (Ache & Matheson 2013 Curr Biol, https://pubmed.ncbi.nlm.nih.gov/23871240/) [abstract]; stiffness+damping gave the best muscle-driven imitation (Özdil 2025/ICLR 2026, https://arxiv.org/abs/2509.06426) [verified] | Group defaults (1.0 / 1.0) with spring reference unknown | **Values unmeasured for *Drosophila***; resting angles not set from data |
| Muscle model | At least **per-muscle, antagonist-paired actuators with activation dynamics and force–length–velocity** (Hill-type, rigid tendon acceptable). Net torque is insufficient wherever stiffness modulation or co-contraction matters. | Resistance reflexes, posture under load, walking speed control, grooming, takeoff | Muscles are not torque sources (Vaxenburg 2025) [verified]; FlyMimic: 15 Hill MTUs per front leg replay walking and grooming; ~19 muscles and ~69 MNs per leg (Özdil 2025) [verified]; stick-insect models use antagonistic Hill pairs per joint (Szczecinski/Quinn line; e.g. https://link.springer.com/article/10.1007/s00422-019-00811-y) [abstract] | Signed net torque per DOF | **Largest Tier-A gap**: no antagonist impedance, no F–L–V |
| Neuromuscular transform | Per-motor-unit twitch (rise/decay), nonlinear summation/saturation, facilitation; slow units near-tonic | Posture (tonic slow units), fast reflexes, jump | Fast/intermediate spike ≈10/1 µN at tibia and half-max in ~8.5 ms; slow <0.1 µN, not peaking within 500 ms; two spikes ≈1.6× one, saturating by ~10 spikes; tonic slow firing carries ~1.5 µN resting force (Azevedo 2020 eLife, https://pmc.ncbi.nlm.nih.gov/articles/PMC7347388/) [verified] | Single-exponential twitch, τ 30/100 ms, linear summation | Rise time, saturation and facilitation are missing; slow τ is too fast |
| Contact: friction, compliance | Soft contact with a friction cone and small penetration; stable at the step size | Standing, walking | All fly sims use MuJoCo soft contacts [verified] | Present | Contact parameters are untuned |
| Adhesion (claws + pulvilli) | Needed on slopes >~30° and on ceilings, and helpful for normal gait. Minimum: a per-leg normal force that is on in stance and released by peeling or shear. A load/shear-dependent rule is better than a free switch. | Slopes, ceilings, landing, feeding on surfaces | NMF v2: without adhesion the fly slips at 30°; with it, >90° inclines are possible, and climbing scales with adhesion force (Wang-Chen 2024, https://www.biorxiv.org/content/10.1101/2023.09.18.556649v4) [verified]; flybody adhesion capped at 1 body weight per leg, learned to switch on in stance [verified]; fly pulvilli detach by pulling/shifting/twisting/lifting (Niederegger & Gorb 2003 J Insect Physiol) [abstract] | Adhesion actuator driven by long-tendon pool | Attach/detach physics, force cap and safety factor are unmeasured for *D. mel.* |
| Flight motor (power muscles) | **Not** representable as spike→torque. Minimum: a self-sustained oscillator at ~200–220 Hz standing in for stretch-activated DLM/DVM plus thoracic resonance. Its amplitude is set by Ca²⁺ level (power-MN rate), and frequency is near-fixed and modulated by pleurosternal muscles. | All flight, takeoff (long mode) | Stretch activation (TnC4) required for IFM power (https://pmc.ncbi.nlm.nih.gov/articles/PMC5814588/, Springer 10.1007/s10974-014-9387-8) [abstract]; flybody used a fixed 218 Hz wingbeat pattern generator plus policy offsets [verified] | Wing joints get torque from MN spikes; nothing oscillates | **Critical Tier-B gap** |
| Wing hinge / steering muscles | A learned or phenomenological map from steering-muscle activity (b1–b3, i1–i2, iii1–iii4, hg1–4, tp) to per-stroke wing kinematic parameters. Explicit sclerite mechanics are not needed. | Saccades, steering, stabilisation, hover trim | CNN from muscle Ca²⁺ to wing kinematics, embedded in a physics sim, reproduces free-flight maneuvers (Melis, Siwanowicz & Dickinson 2024 Nature; preprint https://pmc.ncbi.nlm.nih.gov/articles/PMC10327165/) [abstract]; tonic (b1) vs phasic (b2) steering muscles (Lindsay et al. 2017 Curr Biol) [abstract] | Guessed motor targets for wing MNs | **Critical**: no hinge map |
| Aerodynamics | Quasi-steady blade-element forces (translational/Kutta lift and drag dominate; rotational and added mass are small) | Hover, saccades, perturbation recovery | Fly turns are inertia-dominated and produced by subtle kinematic changes (Fry et al. 2003 Science) [abstract]; flybody's 5-term quasi-steady model supports hover, saccades and speed changes, is robust to ±20% coefficients, and Kutta lift plus drag dominate (Vaxenburg 2025) [verified]; robot-fly validation of quasi-steady forces (Dickinson 1999 Science; Sane & Dickinson 2002) [unverified] | MuJoCo ellipsoid fluid model on wings | Adequate type. Coefficients unvalidated at 0.1 ms and in our wing geometry |
| Halteres | Minimum: a haltere beating antiphase at wingbeat frequency and a campaniform readout of the Coriolis (∝ Ω × haltere velocity) strain. A kinematic/analytic proxy is acceptable. Haltere steering muscles are optional. | Flight stabilisation, saccade termination | Yaw recovery from magnetic perturbation within a few wingbeats via a PI-like controller on sensed angular velocity attributed to halteres (Ristroph 2010 PNAS, https://www.pnas.org/doi/10.1073/pnas.1000615107) [abstract] | Haltere joint, stiffness 400, no actuator, no oscillation | **Gap**: no gyroscopic signal |
| Head/neck | Actuated 3-DOF neck with the eye fixed to the head. Needed for gaze stabilisation and head saccades, and it changes the retinal image. | Visual behaviours, flight | Head stabilisation demos in NMF v2 [verified]; head–body gaze coordination (Cellini & Mongeau) [unverified] | 3 DOFs, guessed motor targets | Guessed neck-MN mapping |
| Abdomen | Rigid body with 1–2 steering DOFs is enough. It matters for flight trim and possibly yaw; negligible for walking. | Flight trim, courtship/egg-laying (out of scope) | Abdominal steering in tethered flight (Zanker 1988) [unverified] | 6 segments × 2 DOFs, guessed | Minor |
| Jump (TTM) | A fast, high-force middle-leg extensor reached by one GF→TTMn spike. Needs correct twitch rise, a force cap high enough for multi-g takeoff, and correct timing against wing elevation. | Escape takeoff | Short-mode takeoff <7 ms with near-simultaneous leg extension and wing raise; action selected by GF spike timing (von Reyn 2014 Nat Neurosci, https://www.nature.com/articles/nn.3741) [abstract]; Card & Dickinson 2008 [unverified] | Torque cap ±30 µN·mm per actuator | Probably too weak for a jump (inferred, see §2) |
| Proboscis | 3 segments (rostrum, haustellum, labella) plus labellar spreading, driven by identified MN→muscle pairs | Feeding | ~16 MNs; MN9 lifts the rostrum, MN2 extends the haustellum, MN6 extends the labella, MN8 spreads them, MN1 retracts (McKellar et al. 2020 eLife, https://elifesciences.org/articles/54978) [abstract] | Rostrum/haustellum/labrum joints present | Labellar spread, MN map |
| Ingestion pump | Lumped hydraulic cibarial pump (muscles 11/12) filling a crop/gut volume; no CFD | Feeding, satiety state | Manzo et al. 2012 PNAS, https://www.pnas.org/doi/10.1073/pnas.1120305109 [abstract]; pharyngeal mechanosensors (eLife 88614) [abstract] | Absent | **Gap for feeding and internal state** |
| Self-collision + body contact sensing | Collisions between legs, head, wings and body, with contact reported per bristle field | Grooming | Grooming is driven by bristle/dust stimulation of specific body regions (Seeds 2014, Hampel 2015) [unverified]; FlyMimic replays grooming kinematics without contact forces (acknowledged limitation) [verified] | Self-collision present; bristles = contact only | No spatial bristle map or dust model |
| Compound eye | Per-ommatidium sampling with Gaussian acceptance (~4–5° half-width), ~5° spacing, correct eye geometry; phototransduction low-pass (~tens of Hz); frame rate ≥ several hundred Hz for flight | Optomotor, looming/escape, flight | NMF v2 hex eye 721 ommatidia, 270° FOV [verified]; flybody flight vision used only 32×32 px [verified]; acceptance angle values (Stavenga; Götz) [unverified]; photoreceptor microsaccades (Juusola 2017 eLife) [unverified] | 721 ommatidia/eye rendered; drive is a static gain | No acceptance-angle blur check, no transduction dynamics |
| Antenna / JO | Passive rotational oscillator (funiculus–arista) driven by air velocity, gravity and sound, read as displacement plus velocity | Wind orientation, flight speed control, courtship song, gravitaxis | Antennal wind sensing stabilises flight velocity (Fuller et al. 2014 PNAS, https://www.pnas.org/doi/full/10.1073/pnas.1323529111) [abstract]; NMF v2 models the arista with 3 compliant DOFs [verified] | Antenna joints present; JO gain guessed | No aero-driven antenna mechanics |
| FeCO / CS / hair plates | Joint-angle, velocity and vibration features filtered through tendon mechanics. CS read strain proxies from segment load, not FEM. | Reflexes, walking, grooming | FeCO claw/hook/club tuning (Mamiya 2018, 2023) [unverified]; CS response to load/strain (Zill; Dinges et al. FEM in stick insect) [unverified] | Derived proxies | Acceptable to start |
| Olfactory world | Odour field with **intermittency** (filaments) plus wind. Static gradients are enough only for chemotaxis in still air. | Odour-guided walking/flight | Walking flies respond to odour-encounter timing in turbulent plumes (Demir et al. 2020 eLife; Álvarez-Salvado 2018 eLife) [unverified]; NMF v2 used inverse-square fields and a PhiFlow plume [verified] | ORN rates only | Plume dynamics and wind |
| Numerics | Walking 0.1 ms is fine. Flight needs ≤0.05 ms, which flybody used with 218 Hz wings. Implicit damping for stiff passive joints. | All | flybody flight step 0.05 ms, control 0.2 ms [verified]; FlyMimic 0.1 ms, control 2 ms [verified] | 0.1 ms everywhere | Needs a convergence test for flight |

## 2. Per-behaviour minimal requirements

**Standing, posture and leg resistance reflexes.** At fly scale, gravity is a
minor load on a free leg, so the rest posture is set by passive joint forces
and tonic slow-unit activity. Evidence: Sutton 2023 puts limbs under ~1 cm in
the elastic/viscous regime; Hooper 2009 and Ache & Matheson 2013 show
gravity-independent passive rest postures. Our numbers agree. A tibia of a few µg
at a ~0.3 mm lever feels a gravity torque of order 0.01 µN·mm, against a
passive stiffness of 1 µN·mm/rad (inferred order of magnitude, not measured).
So the **resting angles (spring references) and stiffnesses decide the
posture**. They are currently flybody defaults. Azevedo 2020 shows the other
half of posture. Tonic slow MNs carry ~1.5 µN of resting tibia force (~15% body
weight), and their twitch does not peak within 500 ms, so a 100 ms slow τ is
too fast. A resistance reflex is a change in joint impedance, and a net-torque
actuator cannot express the co-contraction that raises stiffness. Minimum: an
antagonist pair per principal joint axis (FTi at least, then coxa and
trochanter), each with activation dynamics and F–L–V. With these, co-activation
yields stiffness and damping. Standing load is shared through tarsal contact,
which needs friction but not necessarily adhesion on the flat.

**Walking (gait, speed, turning).** Rigid skeleton, per-joint passive
mechanics, contact friction and actuators strong enough to support ~1 body
weight across 3 legs have all been shown sufficient. NMF v2 walked with PD
position control and CPG/rule/hybrid controllers. flybody walked at 0–4 cm/s in
tripod gait with position actuators under RL. Neither drove the body from MN
spikes, so neither shows that torque-per-spike is enough. FlyMimic replayed
walking with 15 Hill muscles, but on a tethered, contact-free leg; the authors
flag that contact forces are missing. Minimal level for a neurally driven
walk: Tier-A muscle model plus passive mechanics plus friction contact. Speed
modulation depends on stance-phase force generation, and F–V matters there.
Turning needs no extra mechanisms.

**Slopes and ceilings.** Adhesion is necessary. In NMF v2 the fly slips at
about 30° without it, and with it can climb past 90° (verified). The minimum is
a per-leg adhesive normal force with physically plausible detachment. Peeling
under proximal pull is how flies detach, and a switch that is purely neural
permits unphysical states such as holding adhesion during swing. Our
long-tendon-pool drive is a reasonable proxy, because the claw retractor is the
long-tendon muscle. Pulvillus adhesion itself is largely passive and depends on
shear, so it should be tied to contact and shear, not only to MN rate.

**Flight: hover, steering, saccades, perturbation recovery.** Four mechanisms
are needed. None of them is sclerite-level or CFD-level.
1. A wingbeat oscillator at ~200–220 Hz. Asynchronous power muscles contract
   many times per MN spike, so a spike→torque transform cannot beat the wings.
   Stretch activation is required for power (TnC4 replacement abolishes it). The
   minimal abstraction is a limit-cycle generator whose amplitude follows
   power-MN rate (Ca²⁺ level) and whose phase and frequency are near-fixed.
   flybody's fixed-trajectory WPG worked for hover, saccades and backward
   flight.
2. A hinge map from steering-muscle activity to per-stroke wing kinematics
   (stroke amplitude, deviation, rotation timing, mean angle). Melis et al. 2024
   show a learned map suffices to reproduce free-flight maneuvers in a physics
   sim. It is fitted to measured muscle-to-kinematics data, which makes it a
   legitimate "peripheral transform", not an unconstrained behavioural decoder.
   It must be labelled as fitted.
3. Quasi-steady aerodynamics. Fry 2003 shows saccades are inertia-dominated
   and produced by small kinematic changes. flybody's quasi-steady model was
   robust to ±20% coefficient error. Unsteady CFD is unnecessary for these
   behaviours.
4. A haltere angular-rate signal. Recovery from yaw perturbations uses
   PI-like feedback on sensed rate with a latency of a few wingbeats (Ristroph 2010).
   An analytic Coriolis proxy fed to haltere campaniform afferents is enough.
   Simulated haltere mechanics are optional. Wing-hinge campaniform and
   proprioceptive afferents need phase-locked strain proxies. Head motion and
   vision at ≥~200 Hz frame rate are needed for visually guided steering.
   Abdomen: 1–2 DOFs, low priority. Timestep ≤0.05 ms.

**Takeoff (GF escape).** Needs a middle-leg TTM that delivers a very fast,
large extension torque from one spike, correct leg geometry against the ground,
and wing-elevation timing relative to the jump (short mode <7 ms vs long mode).
Rough inference: a takeoff acceleration of order 10 g needs order 100 µN at the
tarsi. That implies FTi/coxa torques of order tens to 100 µN·mm, beyond the
current ±30 µN·mm actuator cap. This must be checked against Card & Dickinson
2008 kinematics before any escape claim. The flight motor (above) is needed for
the post-jump transition to flight.

**Landing.** Visual looming triggers leg extension, and touchdown needs contact
damping and adhesion. No new mechanism beyond Tier A plus flight.

**Grooming.** Self-collision (present) plus a spatial map of bristle
mechanoreceptors that turns contact location into afferent identity. The
stimulus model (dust particles or equivalent) is what triggers and ends the
grooming sequence. Tibial/tarsal combs can be friction patches. The wings must
be able to reach grooming postures, so the wing joint ranges must allow it.
Antagonist muscle impedance helps precise leg rubbing. FlyMimic found that
grooming and walking use distinct muscle synergies.

**Feeding.** Proboscis: 3 segments plus labellar spread, with 5 identified MN
actions (McKellar 2020). flybody has most of the DOFs, but spreading is
missing and the MN mapping is guessed. Ingestion needs a lumped pump (muscles
11/12 at a few Hz) filling a crop volume, with pharyngeal mechanosensors.
Contact-gated gustatory sensilla on labellum, legs and pharynx complete it. Crop
and gut fill feed internal state (satiety), so the pump model belongs to the
internal-state priority, not only to feeding kinematics.

**Visual, olfactory and mechanosensory guidance.**
- Vision: an ommatidial sampling model with Gaussian acceptance and correct
  lattice spacing; frames fast enough for motion (≥200 Hz walking, higher in
  flight); photoreceptor low-pass and adaptation dynamics. Rhabdomere optics
  and microsaccades matter only for hyperacuity claims.
- Olfaction: intermittent plume plus wind, needed for plume tracking; a static
  field is fine for still-air chemotaxis.
- Wind and gravity: an antenna-rotation oscillator driven by air velocity.
- Leg mechanosensation: strain and angle proxies, no FEM.

## 3. Tiered recommendation

**Tier A: posture, walking, sensory responses. About 13 distinct mechanisms.**
1 rigid skeleton with measured mass (have); 2 leg DOFs and tarsal chain (have);
3 per-joint passive stiffness/damping/**rest angle** (guessed); 4 per-unit twitch
kinetics with saturation and facilitation (partial); 5 **antagonist Hill-type
muscles with F–L–V** (absent); 6 moment arms and force caps (partial); 7
friction/compliant contact (have); 8 adhesion with contact/shear-coupled
detachment (partial); 9 FeCO/CS/hair-plate/bristle transducers (proxy); 10 eye
optics and phototransduction dynamics (partial); 11 antenna/JO mechanics (absent);
12 odour and wind world (partial); 13 neck actuation (guessed).
Most important gaps: (5), then the rest angles in (3) and the slow-unit kinetics
in (4). For (5), a pragmatic step is a generic antagonist-pair Hill actuator per
leg DOF using MuJoCo's built-in muscle type. Where FlyMimic has parameters, use
them for the front leg (labelled as fitted), and size-scale the other legs
(labelled as inferred).

**Tier B: flight, takeoff and landing. About 7 more.**
14 **wingbeat oscillator** standing in for stretch activation and thorax
resonance (absent, and blocking); 15 **steering-muscle→wing-kinematics hinge
map** (absent, and blocking); 16 quasi-steady aerodynamics (have); 17 **haltere
Coriolis signal** (absent); 18 wing campaniform/hinge proprioceptor proxies
(guessed); 19 fast high-force TTM jump actuator with a raised force cap (likely
inadequate); 20 abdomen steering DOFs (guessed, low priority). Also needed: a
0.05 ms flight step with a convergence test.

**Tier C: grooming and feeding. About 5 more.**
21 self-collision (have); 22 spatial bristle-field map plus a dust/stimulus
model (absent); 23 proboscis with labellar spread and identified MN map
(partial); 24 cibarial pump and crop fill (absent); 25 contact-gated gustatory
sensilla on labellum, legs and pharynx (partial).

Roughly 25 mechanisms in total. We have about 8, have partial or proxy
versions of about 11, and lack about 6. The absent ones cluster in muscle
impedance (A), the flight motor, hinge and haltere (B), and bristle and
ingestion (C).

## 4. Honest uncertainties

- **No *Drosophila* passive joint stiffness has been directly measured** as
  far as I found. The locust and stick-insect results establish the regime, not
  the values. FlyMimic's passive parameters (and flybody's groups) are fitted or
  assumed and must be labelled that way. The ratio of passive to active
  resting force is also unsettled. Azevedo 2020 attributes a measurable
  resting force to tonic slow units, so the rest posture is partly active.
- **Muscle necessity is argued, not demonstrated.** FlyMimic found final
  kinematics indistinguishable across passive-parameter variants, and it is
  contact-free. No fly study shows that a net-torque model fails a behaviour
  that a Hill model passes. The case for Hill-type muscles rests on (a)
  co-contraction and impedance control existing in insects, and (b) our
  spike-driven setting needing a physical MN→force transform. A discriminating
  experiment: drive FTi resistance reflexes in both actuator models and
  compare with measured stiffness and reflex-gain data.
- **The hinge map is data-hungry.** The Melis et al. model covers the imaged
  steering muscles in tethered flight. Transfer to free flight and to our wing
  geometry is untested. A fitted CNN inside the "body" must be declared as a
  fitted peripheral transform with a validity range.
- **The wingbeat oscillator abstraction hides physiology**: stretch activation,
  thoracic resonance and pleurosternal frequency control. That is acceptable for
  steering behaviours, but not for claims about power-muscle physiology or
  energetics.
- **Adhesion magnitudes are uncertain.** NMF v2 quotes >100× body weight for
  insect pads generally. flybody caps at 1× per leg. The *D. melanogaster*
  value and its shear dependence were not found. NMF v2's "40 mN" adhesion
  setting is in model units whose mapping I could not confirm.
- **Jump force:** the force-cap inference above is order-of-magnitude only.
- **Timestep:** 0.05 ms for flight is what flybody used, not a proven
  requirement. Run a convergence test (0.1 vs 0.05 vs 0.025 ms on wing forces
  and body rates).
- **Vision frame rate and phototransduction** requirements are inferred from
  known photoreceptor bandwidth; they were not checked against an embodied
  result.
- Several citations are [abstract] or [unverified]: Hooper 2009, Ache &
  Matheson 2013, Fry 2003, Ristroph 2010, Lindsay 2017, Melis 2024, von Reyn 2014,
  McKellar 2020, Manzo 2012 and all sensory-periphery items marked so. Confirm
  quantitative statements before registering them.

## Sources

- Vaxenburg et al. 2025 Nature, flybody: https://www.nature.com/articles/s41586-025-09029-4 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC12310536/
- Özdil et al. 2025/ICLR 2026, FlyMimic: https://arxiv.org/abs/2509.06426
- Wang-Chen et al. 2024 Nat Methods, NeuroMechFly v2: https://www.nature.com/articles/s41592-024-02497-y ; https://www.biorxiv.org/content/10.1101/2023.09.18.556649v4
- Lobato-Rios et al. 2022 Nat Methods, NeuroMechFly: https://www.nature.com/articles/s41592-022-01466-7
- Azevedo et al. 2020 eLife: https://pmc.ncbi.nlm.nih.gov/articles/PMC7347388/
- Sutton et al. 2023 PNAS Nexus: https://pmc.ncbi.nlm.nih.gov/articles/PMC10563792/
- Ache & Matheson 2013 Curr Biol: https://pubmed.ncbi.nlm.nih.gov/23871240/
- Melis, Siwanowicz & Dickinson 2024 Nature (preprint): https://pmc.ncbi.nlm.nih.gov/articles/PMC10327165/
- Fry, Sayaman & Dickinson 2003 Science: https://pubmed.ncbi.nlm.nih.gov/12702878/
- Ristroph et al. 2010 PNAS: https://www.pnas.org/doi/10.1073/pnas.1000615107
- Fuller et al. 2014 PNAS: https://www.pnas.org/doi/full/10.1073/pnas.1323529111
- von Reyn et al. 2014 Nat Neurosci: https://www.nature.com/articles/nn.3741
- IFM stretch activation: https://pmc.ncbi.nlm.nih.gov/articles/PMC5814588/ ; https://link.springer.com/article/10.1007/s10974-014-9387-8
- McKellar et al. 2020 eLife: https://elifesciences.org/articles/54978
- Manzo et al. 2012 PNAS: https://www.pnas.org/doi/10.1073/pnas.1120305109
- Szczecinski/Quinn common-inhibitor model: https://link.springer.com/article/10.1007/s00422-019-00811-y
