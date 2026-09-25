# Non-leg motor neuron targets

Session 4, from a bounded literature extraction checked against the local
`male-cns:v1.0` cache. Subclass counts below were re-verified locally. Muscle
identity lives only in the `type` string; `target` is empty for every non-leg
motor neuron. `exitNerve` is not cached and needs a live query.

Status: **PD** published direct (driver line or reconstruction to muscle),
**PI** published inferred (homology, naming, or muscle-to-DOF reasoning),
**U** unknown. DOIs marked (m) were not confirmed by lookup and need checking
before they are cited.

## Counts (male-cns:v1.0, all statuses)

| superclass | subclass | n | what |
|---|---|---|---|
| vnc_motor | fl / ml / hl | 135 / 116 / 130 | legs (already wired, F-DATA-1) |
| vnc_motor | wm | 67 | wing power, steering, tension, plus jump TTMn/STTMm |
| vnc_motor | hm | 16 | haltere |
| vnc_motor | nm | 24 | neck (VNC) |
| vnc_motor | ad | 214 | abdominal |
| vnc_motor | xm | 6 | unclassified |
| cb_motor | pm | 67 | proboscis, pharynx, salivary |
| cb_motor | nm | 20 | neck (brain) |
| cb_motor | am | 13 | antennal |
| cb_motor | rm | 7 | unknown meaning |

## Map

| Group | male-cns types | Target | flybody actuator | Status |
|---|---|---|---|---|
| Wing power | DLMn a,b; DLMn c-f (5/side) | DLM, indirect depressor | none, no power DOF | PD (Cheong 2024) |
| Wing power | DVMn 1a-c, 2a,b, 3a,b (7/side) | DVM1-3, indirect elevator | none | PD |
| Wing steering | b1, b2, b3 MN | basalars | `wing_yaw/roll` | MN→muscle PD; muscle→angle PI (Lindsay 2017; Melis 2024) |
| Wing steering | i1, i2 MN | 1st axillary | `wing_yaw` | PD / PI |
| Wing steering | iii1, iii3 MN; MNwm35 | 3rd axillary (MNwm35 putative iii4) | `wing_pitch/yaw` | PD; MNwm35 PI |
| Wing steering | hg1-hg4 MN | 4th axillary | `wing_roll/pitch` | PD / PI |
| Wing tension | tp1, tp2, tpn MN; ps1, ps2 MN | tergopleural, pleurosternal | none | PD; function PI (O'Sullivan 2018) |
| **Jump** | **TTMn (1/side), STTMm (2/side)** | **TTM, STTM of T2** | **T2 trochanter/femur exist** | **PD for TTM** |
| Wing, unknown | MNwm36 | unassigned | — | U |
| Haltere | hDVM, hi1, hi2, hiii2, MNhm42/43, MNhm03 | haltere power/steering | none, haltere passive | PD/PI/U (Dickerson 2019 (m)) |
| Neck (VNC) | ADNM2 MN, FNM2 | TH2 (yaw); adductor (pitch) | `head_twist/abduct`, `head` | PI by *Calliphora* homology (Stürner 2025; Strausfeld 1987) |
| Neck (VNC) | ADNM1, MNnm03-14 | — | head | U |
| Neck (brain) | CvN4-7, GNG276/283/641/648/650/653 | — | head | U |
| Proboscis | MN9 | m9 rostrum protractor | `rostrum` | PD (McKellar 2020) |
| Proboscis | MN1, MN2Da/Db, MN2V | rostrum retraction | `rostrum` | PD* |
| Proboscis | MN3L/M; MN4a/b | haustellum flexor; extensor | `haustellum` | PD*; MN4b PI |
| Labellum | MN6, MN7 | labellar extension, spreading | `labrum_left/right` | PD* |
| Pharynx, salivary | MN5, 8, 10, 11D/V, 12D; MN13 | cibarial pump; salivary valve | none | PD* |
| Proboscis | MNx01-05, CEM | — | — | U |
| Antenna | GNG133/649/651/652/668, PS348 | scape-pedicel muscles | `antenna_*` | PI; no published aMN1-5 ↔ male-cns name map (Özdil 2026; Suver 2023) |
| Abdominal | MNad01-69 | body wall, genitalia; not identified | `abdomen`, `abdomen_abduct` | U |

\* McKellar 2020 is a driver-line study, so direct, but its muscle table was
read through a summary. Check against its Table 1 before wiring m1/m2/m6/m7/m8.

## Consequences for the interface

- **Wire now, direct evidence:** TTMn/STTMm to T2 leg actuators (the giant
  fibre escape output); MN9 and the proboscis pool to `rostrum`/`haustellum`/
  `labrum` (the sugar→MN9 assay output).
- **Needs a body change, not a mapping:** DLM/DVM power pools (24/side) and
  16 haltere MNs have no DOF. Wing steering muscles are identified but flybody's
  wing is a yaw/roll/pitch hinge; the only quantitative muscle-to-kinematics
  map is Melis et al. 2024, which is learned. Any wiring there is PI.
- **Field gaps, register as unknown in the animal's literature:** neck MN
  targets (even MANC names only ~3 of 12 pairs, by homology), abdominal MN
  targets, antennal name map.
- The 26-vs-67 wing MN discrepancy in `docs/INTERFACE.md` is most likely a
  per-side, pool-collapsed count in Cheong 2024 (inferred, not checked).

## Sources

Cheong et al., eLife, 10.7554/eLife.96084 · Marin et al. 2024, 10.7554/eLife.97766 ·
Takemura et al. 2024, 10.7554/eLife.97769 · Male CNS (bioRxiv 10.1101/2025.10.09.680999; Cell 2026) ·
McKellar et al. 2020, 10.7554/eLife.54978 · Lindsay et al. 2017, 10.1016/j.cub.2016.12.018 ·
Melis et al. 2024, 10.1038/s41586-024-07293-4 (m) · O'Sullivan et al. 2018, 10.1016/j.cub.2018.06.038 (m) ·
Dickerson et al. 2019, 10.1016/j.cub.2019.08.065 (m) · Strausfeld et al. 1987, 10.1007/BF00609728 ·
Stürner et al. 2025, 10.1038/s41586-025-08925-z · Özdil et al. 2026, 10.1038/s41467-026-72152-x ·
Suver et al. 2023, PMID 36731464 · Vaxenburg et al. 2025, 10.1038/s41586-025-09029-4
