# s13 body interface (fly2, 13 Oct 2026): what the sources and the code say

Agent-gathered (three Sonnet Explore agents, 13 Oct about 23:00). Quotes are as reported by the agents. Rows marked "check" have not been read by fly2 in the primary text. This file is for planning; it is not a value table.

## (a) MN-to-muscle mapping
- **Code** (`src/flyemu/neuromuscular.py` build(): type must end in " MN", and the stripped name is looked up in `MUSCLE_TO_ACTION` / `COUPLED_TO_JOINTS`; Hill join in `muscles.py` CoxaMuscles via `coxa_muscles*.csv` mn_type).
- **The 187 of 505** (S1 audit, `scripts/probes/bypass_s1_actuation.py:84-105`; `runs/s13/bypass/s1b/need/s1_m10f0_adh1.json`):
  - 168 long-tendon-muscle MNs: `ltm MN` 84, `ltm2-femur MN` 48, `ltm1-tibia MN` 36. They are mapped for the legacy torque actuators (COUPLED_TO_JOINTS), but **there is no Hill muscle for the LTM**, so in Hill mode they drive nothing.
  - 2 TTMn, excluded on purpose (the GF hook drives them).
  - 17 unnamed T2/T3 types: MNml80 6, MNhl64 2, MNml77 2, MNhl01 2, MNhl88 2, MNhl59 2, MNml83 1.
- **T2/T3 coxa promotors: a published annotation gap, not our bug.** In male-cns, `Tergopleural/Pleural promotor MN` exists only on T1 (8 cells). Cheong et al. 2024 eLife 96084 (MANC): "For the Tergopleural/Pleural promotor MNs that innervate a muscle in the thorax, we could not find MNs in T2 and T3 that were similar in morphology and connectivity, suggesting that these MNs are either not present or have a different function and morphology." Also: "All MN targets in T1 were assigned by careful matching to... FANC... while all MN targets in T2 and T3 were assigned by serial sets"; 52 T2/T3 leg MNs unidentified. Supplementary files 3 (light-level matching), 6 (serial leg MN groups) and 7 (standard leg groups) are the tables to fetch (check).
- **Named T2/T3 coxa MNs that have serial homologs:** Sternal anterior rotator, Sternal posterior rotator, Pleural remotor/abductor, Sternal adductor (Cheong 2024).
- **Other sources:** Azevedo 2024 Nature (FANC) and Lesser 2024 Nature (motor modules; GitHub `tuthill-lab/Lesser_Azevedo_2023`, Supplementary Tables 1-3) cover T1 only. Azevedo 2020 eLife: T1, 14 muscles, 53 MNs.
- **Note:** S1 drives muscles directly (bypass), so (a) does not change the S1 verdict. It matters once the brain drives standing. The LTM gap may matter for (b), since the LTM flexes the tarsus/claw through its long tendon.

## (b) Distal capacity and the standing pose
- **Muscles:** FlyMimic (Ozdil et al. 2025, arXiv 2509.06426) fitted only the T1 leg (15 MTUs: 7 thorax, 6 coxa, 2 femur). Mid and hind legs were reconstructed anatomically but not fitted. Specific tension 28 mN/mm² (chosen inside 9-37 mN/mm²). Ours: mid/hind scaled from T1 by segment size (`leg_muscle_midhind_scale.csv`, inferred). No passive force in the MTUs (fpmax 0).
- **Forces measured** (Azevedo 2020, PMC7347388, T1 tibia flexor): fast MN spike about 10 µN, intermediate about 1 µN; max tibia-tip force in a behaving fly about 100 µN. No extensor force anywhere.
- **Weight:** about 1 mg, about 10 µN. No adult ground-reaction-force or tarsal adhesion number found for Drosophila.
- **Standing height:**
  - Wang et al. 2025 eLife (PMC12324252): "the median fly stands at a height of 0.5 mm"; a fly's own height varies 0.1-0.4 mm between trials. Check what "height" refers to (ventral thorax? CoM?).
  - Pratt et al. 2024 (repo FINDINGS): dorsal thorax 0.51 body lengths (about 1.04 mm) at the slowest walking speed.
  - Our placed pose: thorax origin 1.32 mm, the outcome of `deadfly.place_standing()` lowering flybody's neutral keyframe until contact. It is not a stored parameter.
  - F-BYPASS-1 used about 1.0 mm "inferred from Wang 2025".
- **Joint angles:** Haustein 2024 CTr flexion envelopes, front 10-160°, mid 70-140°, hind 70-180° (tethered); Karashchuk 2021 qualitative. Local copies in `data/raw/leg_kinematics/`. No standing-only angle table found.

## (c) Force-length and passive stiffness
- **Ours:** `passive_leg_stiffness.csv` = Wang 2025 Table 1 medians (measured; F-PASSIVE-1), switch `joint:leg|passive_stiffness_source`.
- **Wang 2025:** stiffness 8e-9 to 6e-8 N·m/°; passive torques are about 70× too small to hold the weight; holding the fly up in OpenSim needed a 40-80× uniform stiffness increase. So measured passive stiffness cannot make the fly stand; real standing is active.
- **Hooper 2009 J Neurosci:** in small limbs, rest postures are set by passive forces and are gravity-independent. Ache & Matheson 2013: locust, abstract only.
- **Force-length:** stick insect extensor tibiae (Guschlbauer 2007 J Exp Biol 210:1092) works on both limbs, with a 2-4× force change over 30-180°. Ours is nearly flat (r/L0 about 0.09 per rad). No Drosophila curve was found.

## (d) Abdomen
No abdomen stiffness or abdomen standing-angle measurement found anywhere. Wang 2025 gives abdomen ellipsoid axes 1080 × 700 × 700 µm (measured). Ours has no abdominal tone (no sourced row), and the tip drags.

## Viewed: `docs/media/s13_bypass_s1.png`
Support 0.3-0.5 and coact 1 rear nose-up, pivoting on the abdomen tip. Need 1.5-2 pitches head-down. Low levels lie down.

## Candidate fixes (to pre-register one at a time; none run)
1. **Pose:** the real stance is lower than 1.32 mm. Settle the height definition in Wang 2025 and Pratt 2024 first, then place the fly at the measured height and recompute the need pattern (fly's S1 follow-up).
2. **LTM:** add the long tendon muscle as a Hill muscle on the tarsal flexion joints, if a sourced force or PCSA exists (FlyMimic does not fit tibia/tarsus muscles: check). This would also give the 168 LTM MNs a target.
3. **Abdomen:** a support or tone at the abdomen joint needs data; none found. Record it as a blank, and test whether stopping the tip drag (a diagnostic only) removes the rearing.
4. **Force-length:** keep FlyMimic's curve unless Drosophila data appear. The insect-wide range (2-4× over the working range) is the only bound.

## Addendum (13 Oct 23:30): tibia-tarsus and LTM sources (Sonnet search, quotes as reported; "check" = not read by fly2)
- **The TiTa pair the 6.1× need was measured against is a guessed placeholder** on every leg (`leg_muscles*.csv`: F0 20 µN, r 0.01 mm, "no FlyMimic tarsal muscle; placeholder"). The Ta levator and Ta depressor drive it (`neuromuscular.MUSCLE_TO_ACTION`). The LTM is mapped onto the tendon-coupled tarsus 1→5 chain, not onto TiTa (`COUPLED_TO_JOINTS`). So the 6.1× is a gap against a guess, not against a measured capacity.
- **No Drosophila source gives a force, PCSA, volume or moment arm for the LTM (ltm1/ltm2) or for the tarsal levator or depressor.**
  - FlyMimic (Ozdil 2025, arXiv 2509.06426): "Muscles housed in the tibia were excluded because the tibia segment was partially captured in the X-ray data." Only the fast tibia flexor and extensor are modelled in the femur. Its specific tension is 28 mN/mm², inside the measured 9 (IFM) to 37 (jump muscle) mN/mm².
  - Azevedo 2020 (PMC7347388): about 10 / 1 / < 0.1 µN per spike (fast / intermediate / slow) for the tibia flexor/reductor only. There is no LTM text (checked by the agent).
  - Lesser 2024 (Nature), ED Fig 6g: "The LTM is composed of two muscles, one in the femur and one in the tibia, that both insert on the long tendon that crosses multiple articulations to insert on the claw." It gives two LTM MNs and no force.
  - Soler 2004: tadm has more fibres than talm; no forces.
  - Stick-insect homologue: retractor unguis (Radnikow & Bässler 1991, JEB 157:87); numbers not read (check).
  - No Drosophila claw adhesion force, per-leg standing ground-reaction force, or leg-muscle micro-CT volumetry was found. Chaturvedi 2019 covers the flight muscles only.
- **Consequence for fix 2:** "an LTM Hill muscle with a sourced force" cannot be built from published values. The only route is an INFERRED force: the tibia's internal cross-section from the body mesh × 28 mN/mm², as an upper bound shared by the tibia muscles (tadm, talm, ltm2). It would be labelled inferred and bounded by the 9-37 mN/mm² range. That needs its own pre-registration and, because it would set the capacity that the standing test then probes, a held-out check that isn't standing.
