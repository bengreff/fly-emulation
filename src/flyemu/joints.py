"""Which of the body model's joints are real, and what their ranges are.

The model ships 126 rotational degrees of freedom and, before this audit,
powered every one of them. Several are not joints. A powered non-joint lets the
model move in ways the animal physically cannot, so this is a correctness
problem, not a tidiness one.

Three categories:

    POWERED   a real articulation with muscles; gets an actuator
    PASSIVE   a real articulation with no muscles; keeps the joint, no actuator
    LOCKED    not an articulation; pinned shut

Sources are named per rule. The two that decide the largest blocks:

  Eyes. The compound eye "attaches rigidly to the head capsule"; what moves is
  the retina sliding beneath a stationary lens array, ~15 deg peak, driven by
  two muscles that insert on the retina itself (Fenk et al. 2022, Nature
  612:116-122). A rigid eye rotation would swing the lenses and the head
  silhouette, which is the wrong mechanism. Both independently built whole-body
  fly models (NeuroMechFly, flybody) exclude eye degrees of freedom.

  Tarsal segments. There are no muscles inside the tarsus (Soler et al. 2004,
  Development 131:6041-6051); the tarsal segments "are moved together by muscle
  tension on the long tendon" (Haustein et al. 2024). So four independently
  torqued inter-tarsal joints per leg is wrong in kind: they are one
  tendon-coupled group driven by the long tendon muscle.

Ranges. Anatomical limits are published for almost nothing. Femur-tibia is the
exception at 18 to 180 degrees (Mamiya et al. 2018, Neuron 100:636-650). Where
only walking kinematics exist, the range here is a generous envelope around the
measured excursion and is recorded as ASSUMED, never as an anatomical limit -
behavioural range is not a constraint, it is a validation target.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Mode(str, Enum):
    POWERED = "powered"
    PASSIVE = "passive"
    LOCKED = "locked"


@dataclass(frozen=True)
class Rule:
    pattern: str            # regex against the short actuator/joint name
    mode: Mode
    range_deg: tuple[float, float] | None
    evidence: str
    measured: bool          # True only for a real anatomical limit
    models: tuple[str, ...] = ()   # empty means any body model

    def matches(self, name: str, model: str = "") -> bool:
        if self.models and model and model not in self.models:
            return False
        return re.search(self.pattern, name) is not None


# Order matters: the first matching rule wins.
RULES: tuple[Rule, ...] = (
    # --- not joints -------------------------------------------------------
    Rule(r"c_head-[lr]_eye-", Mode.LOCKED, None,
         "the compound eye is rigidly fused to the head capsule; the retina "
         "moves beneath a stationary lens array, ~15 deg peak, via two muscles "
         "inserting on the retina (Fenk et al. 2022, Nature 612:116-122). A "
         "rigid eye rotation is the wrong mechanism", False),
    Rule(r"_funiculus-[lr]_arista-", Mode.LOCKED, None,
         "the arista is a cuticular process of the funiculus, not an "
         "articulation. NeuroMechFly's authors state these DOF exist only 'to "
         "emulate the compliance of the arista' (Wang-Chen et al. 2024)", False),

    # --- real joints with fewer axes than the rigging gives them ----------
    Rule(r"c_thorax-[lr]_haltere-(roll|yaw)", Mode.LOCKED, None,
         "the haltere beats in one fixed plane, driven by a single "
         "asynchronous muscle with a passive downstroke; roll and yaw are "
         "rigging axes (Deora et al. 2015, cross-species; Hall et al. 2015 "
         "for Drosophila frequency and phase)", False),
    Rule(r"c_rostrum-c_haustellum-(roll|yaw)", Mode.LOCKED, None,
         "the rostrum-haustellum joint is a single extension/flexion axis "
         "(McKellar & Simpson 2020, eLife 54978: 16 proboscis muscles, 8 for "
         "reaching across three articulations). NeuroMechFly-only: flybody "
         "fits a second axis from real postures, handled by its own rule",
         False, ("neuromechfly",)),
    Rule(r"c_head-c_rostrum-(roll|yaw)", Mode.LOCKED, None,
         "rostrum motion is protraction/retraction (lift) about one axis "
         "(McKellar & Simpson 2020)", False),
    Rule(r"c_abdomen\d+-c_abdomen\d+-yaw|c_thorax-c_abdomen12-yaw", Mode.LOCKED, None,
         "in NeuroMechFly's axis convention the abdomen's third axis is axial "
         "twist, and segments bend and telescope rather than twisting "
         "independently. NOTE the trap: flybody's abdominal 'yaw' is the "
         "LATERAL BEND, not twist, because its abdomen has only two axes. Same "
         "axis name, different anatomy, so this rule is NeuroMechFly-only",
         False, ("neuromechfly",)),
    Rule(r"c_head-[lr]_pedicel-(roll|yaw)", Mode.LOCKED, None,
         "the scape-pedicel joint is the only actively controlled antennal "
         "joint and its measured active movement is a single rostro-caudal "
         "rotation of 5-15 deg (Mamiya et al. 2011, J Neurosci 31:6900). The "
         "true DOF count 'remains unknown' (Wang-Chen et al. 2024), so one "
         "axis is kept", False),
    Rule(r"[lr]_pedicel-[lr]_funiculus-(roll|yaw)", Mode.LOCKED, None,
         "the antennal receiver rotates essentially about one axis", False),

    # --- real but unmuscled ----------------------------------------------
    Rule(r"[lr]_pedicel-[lr]_funiculus-pitch", Mode.PASSIVE, (-30.0, 30.0),
         "the pedicel-funiculus joint 'lacks direct muscular control'; it is "
         "moved by air particle velocity or by the active proximal joint, and "
         "is what Johnston's organ transduces (Nunn et al. 2025, JEB "
         "228:jeb251495). Sense it, never drive it", False),

    # --- tendon-coupled group --------------------------------------------
    Rule(r"[lr][fmh]_tarsus\d-[lr][fmh]_tarsus\d-pitch", Mode.POWERED, (-45.0, 45.0),
         "no muscles exist inside the tarsal segments (Soler et al. 2004); "
         "they are moved together by tension on the long tendon (Haustein et "
         "al. 2024), so these four joints per leg are ONE tendon-coupled group "
         "driven by the long tendon muscle, not four independent joints", False),

    # --- real, muscled, with a measured anatomical limit ------------------
    Rule(r"[lr][fmh]_trochanterfemur-[lr][fmh]_tibia-pitch", Mode.POWERED, (18.0, 180.0),
         "femur-tibia range of motion 18 deg fully flexed to 180 deg fully "
         "extended, measured by magnet-actuated joint displacement (Mamiya et "
         "al. 2018, Neuron 100:636-650). The only clean anatomical limit in "
         "the whole body", True),

    # --- real, muscled, range assumed from walking excursion --------------
    Rule(r"c_thorax-[lr][fmh]_coxa-pitch", Mode.POWERED, (-45.0, 45.0),
         "thorax-coxa promotion/remotion during straight walking spans "
         "40.9+/-5.2 deg front, 26.5+/-4.6 mid, 18.6+/-3.9 hind (Haustein et "
         "al. 2024). Envelope assumed; behavioural range is not an anatomical "
         "limit", False),
    Rule(r"c_thorax-[lr][fmh]_coxa-roll", Mode.POWERED, (-25.0, 25.0),
         "thorax-coxa ad/abduction during walking spans about 8 deg in all "
         "leg pairs (Haustein et al. 2024), at the 5.6 deg tracking noise "
         "floor of markerless 3D pose (Karashchuk et al. 2021). Envelope "
         "assumed", False),
    Rule(r"c_thorax-[lr][fmh]_coxa-yaw", Mode.POWERED, (-30.0, 30.0),
         "long-axis rotation of the coxa; walking excursion 4.9+/-2.7 deg mid "
         "and 11.3+/-3.0 hind (Haustein et al. 2024). Envelope assumed", False),
    Rule(r"[lr][fmh]_coxa-[lr][fmh]_trochanterfemur-pitch", Mode.POWERED, (-100.0, 100.0),
         "coxa-trochanter flexion/extension during walking spans 91.2+/-9.5 "
         "deg front, 22.5+/-3.4 mid, 56.3+/-9.0 hind (Haustein et al. 2024). "
         "Envelope assumed", False),
    Rule(r"[lr][fmh]_coxa-[lr][fmh]_trochanterfemur-roll", Mode.POWERED, (-30.0, 30.0),
         "CONTESTED. A seventh leg DOF is needed to fit 3D kinematics, but "
         "Lobato-Rios et al. 2022 place it at coxa-trochanter while Haustein "
         "et al. 2024 place it at trochanter-femur and find it necessary only "
         "for front legs. Both are inverse-kinematics inferences, not "
         "dissections. Kept here as NeuroMechFly places it, as an inference", False),
    Rule(r"[lr][fmh]_tibia-[lr][fmh]_tarsus1-pitch", Mode.POWERED, (-60.0, 60.0),
         "tibia-tarsus is muscled, but from muscles sitting inside the tibia "
         "(Lesser et al. 2024). Range of motion not located; envelope assumed", False),
    Rule(r"c_thorax-c_head-yaw", Mode.POWERED, (-15.0, 15.0),
         "head yaw is driven to anatomical limits of about +/-15 deg in "
         "body-fixed flies (Cellini & Mongeau 2020 PNAS, 2022 eLife 80880)", True),
    Rule(r"c_thorax-c_head-(pitch|roll)", Mode.POWERED, (-25.0, 25.0),
         "the neck is a real 3-DOF joint. Pitch and roll anatomical limits "
         "were NOT located; grooming medians are >14 deg pitch and >8 deg "
         "roll (Ozdil et al. 2026). Envelope assumed", False),
    Rule(r"c_head-c_rostrum-pitch", Mode.POWERED, (-40.0, 40.0),
         "rostrum lift, one of three proboscis articulations, 8 muscles for "
         "reaching (McKellar & Simpson 2020). Numeric angles not located", False),
    Rule(r"c_rostrum-c_haustellum-pitch", Mode.POWERED, (-60.0, 60.0),
         "haustellum extension/flexion (McKellar & Simpson 2020). Numeric "
         "angles not located", False),
    Rule(r"c_head-[lr]_pedicel-pitch", Mode.POWERED, (-20.0, 20.0),
         "active scape-pedicel rotation measured at 5-15 deg caudal and 2-5 "
         "deg rostral during visually induced turns (Mamiya et al. 2011)", True),
    Rule(r"c_abdomen\d+-c_abdomen\d+-pitch|c_thorax-c_abdomen12-pitch",
         Mode.POWERED, (-20.0, 20.0),
         "abdominal dorsoventral deflection in free flight is 10.1+/-5.3 deg "
         "with variation about +/-15 deg (Berthe & Lehmann 2015, JEB "
         "218:3295). Courtship and oviposition ranges not located", False),
    Rule(r"c_abdomen\d+-c_abdomen\d+-roll|c_thorax-c_abdomen12-roll",
         Mode.POWERED, (-10.0, 10.0),
         "abdominal horizontal deflection in free flight is 2.0+/-3.5 deg "
         "(Berthe & Lehmann 2015)", False),
    Rule(r"c_thorax-[lr]_wing-pitch", Mode.POWERED, (-80.0, 80.0),
         "wing stroke amplitude 140+/-10 deg in free hovering flight (Fry, "
         "Sayaman & Dickinson 2005, JEB 208:2303)", True),
    Rule(r"c_thorax-[lr]_wing-yaw", Mode.POWERED, (-15.0, 15.0),
         "stroke deviation about 25 deg peak to peak (Fry et al. 2005)", True),
    Rule(r"c_thorax-[lr]_wing-roll", Mode.POWERED, (-90.0, 90.0),
         "wing rotation/pitch varies strongly through the stroke; a clean "
         "min-max was NOT located. Envelope assumed", False),
    # --- flybody naming ---------------------------------------------------
    # flybody collapses the antenna into one joint instead of the
    # scape/pedicel/funiculus/arista chain. The scape-pedicel rotation is the
    # only actively controlled antennal movement; the rest is the passive
    # receiver that Johnston's organ transduces.
    Rule(r"c_head-[lr]_antenna-pitch", Mode.POWERED, (-20.0, 20.0),
         "the scape-pedicel joint is the only actively controlled antennal "
         "joint; measured active rotation 5-15 deg caudal, 2-5 deg rostral "
         "(Mamiya et al. 2011, J Neurosci 31:6900)", True),
    Rule(r"c_head-[lr]_antenna-(roll|yaw)", Mode.PASSIVE, (-30.0, 30.0),
         "the antennal receiver 'lacks direct muscular control' and moves with "
         "air particle velocity or with the active proximal joint (Nunn et al. "
         "2025, JEB 228:jeb251495). Sense it, never drive it", False),
    Rule(r"c_haustellum-[lr]_labrum-pitch", Mode.POWERED, (-30.0, 30.0),
         "labellar extension, one of the three proboscis articulations; mn6 "
         "and mn7 drive labellar extension and abduction (McKellar & Simpson "
         "2020, eLife 54978). Range not located", False),
    Rule(r"c_abdomen\d-c_abdomen\d-pitch|c_thorax-c_abdomen1-pitch",
         Mode.POWERED, (-20.0, 20.0),
         "abdominal dorsoventral deflection in free flight 10.1+/-5.3 deg, "
         "varying about +/-15 deg (Berthe & Lehmann 2015, JEB 218:3295)",
         False, ("flybody",)),
    Rule(r"c_abdomen\d-c_abdomen\d-yaw|c_thorax-c_abdomen1-yaw",
         Mode.POWERED, (-10.0, 10.0),
         "abdominal horizontal deflection in free flight 2.0+/-3.5 deg; this "
         "is flybody's lateral bend axis, not axial twist "
         "(Berthe & Lehmann 2015)", False, ("flybody",)),
    Rule(r"c_rostrum-c_haustellum-yaw", Mode.POWERED, (-30.0, 30.0),
         "flybody fits a second haustellum axis from real postures; the "
         "anatomy literature describes haustellum extension/flexion as one "
         "axis, so this is kept but flagged as a model inference", False),

    Rule(r"c_thorax-[lr]_haltere-pitch", Mode.POWERED, (-110.0, 110.0),
         "haltere stroke. The often-quoted 140-220 deg amplitude is an "
         "author's cross-taxon summary, not a Drosophila measurement; "
         "Drosophila values are frequency 207.7+/-0.9 Hz and phase 152 deg "
         "(Hall et al. 2015). Halteres do not move during walking", False),
)


def classify(name: str, model: str = "") -> Rule:
    """The rule governing one actuator or joint, by its short name.

    `model` selects between body models where the same axis name means
    different anatomy. Pass it whenever the body model is known.
    """
    for rule in RULES:
        if rule.matches(name, model):
            return rule
    raise KeyError(f"no joint rule matches {name!r}; the audit must be explicit")


def audit(names: list[str], model: str = "") -> dict[str, Rule]:
    return {n: classify(n, model) for n in names}
