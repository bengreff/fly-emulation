# Premotor input to T1 leg MNs from outside the 106-cell core, by hemilineage (s18, 21 Oct 2026)

Connectivity-only query on the local cache (`data/cache/male_cns_neurons.parquet`,
`male_cns_edges.parquet`, `male_cns_hemilineage.parquet`). No neuPrint call, no simulation.
Script: `scripts/connectome/premotor_outside_core.py`. Raw table:
`runs/s18/premotor_outside_core.csv`.

## Method

- Core and leg-MN sets reuse `CORE_TYPES`/`LEG_TYPES` and the T1 selection from
  `scripts/connectome/premotor_mn_geometry.py` (`somaNeuromere` starts with `T1`, type in the
  list) without copying the lists by hand.
- **Synapse threshold: weight >= 5 per connection**, applied everywhere (pool totals,
  presynaptic-type ranking, the DNg100 hop search, the core-input check, the reciprocal-
  inhibition check). This matches the convention already used in the s16/s17 writeups
  (F-REFLEX-2 and the s15/s17 arms); the raw `male_cns_edges.parquet` itself has no built-in
  threshold (every weight >= 1 is present).
- Hemilineage = `trumanHl` from `male_cns_hemilineage.parquet` (the VNC/Truman-Lacin call).
  `itoleeHl` is null for every VNC-resident cell checked here (brain/optic-lobe naming), so it
  was not used.
- Predicted transmitter = the mode of `celltypePredictedNt` (type-level consensus) across all
  instances of a presynaptic type.
- Pool mapping from `LEG_TYPES` names, using function already stated in
  `tests/test_muscles.py` (anterior rotator = forward swing i.e. promotor-like, posterior =
  backward i.e. remotor-like) — **derived from existing repo code, not re-derived from
  anatomy here**:
  - `coxa_promotor` = Tergopleural/Pleural promotor MN, Sternal anterior rotator MN
  - `coxa_remotor` = Pleural remotor/abductor MN, Sternal posterior rotator MN
  - `trochanter_flexor` = Tr flexor MN, Acc. tr flexor MN
  - `trochanter_extensor` = Tr extensor MN
  - `tibia_flexor` = Ti flexor MN, Acc. ti flexor MN
  - `tibia_extensor` = Ti extensor MN
  - `other` = Sternal adductor MN, Sternotrochanter MN, Tergotr. MN — **no clean
    flexor/extensor or promotor/remotor axis was found in the repo for these three** (Tergotr.
    MN is documented elsewhere in this repo as the T2-specific jump muscle, so a "T1" instance
    of it is itself odd; Sternotrochanter's action wasn't pinned down here). Kept in the
    "all T1 leg MN" totals, excluded from the flexor/extensor reciprocal-inhibition check.

## Counts

- T1 core: **12** cells (IN16B036, IN17A001, IN19A002, IN19A004, IN19A007, INXXX466 — 2 per
  type, L+R).
- T1 leg MNs: **94** cells across the 13 `LEG_TYPES`.
- Core + MN = **106**, matching the s15 "about 106" reference exactly.

## Pool input summary (full per-pool top-15 tables are in the CSV)

| pool | n MN | total input syn (>=5) | core's share |
|---|---:|---:|---:|
| tibia_flexor | 29 | 17,830 | 0.002 |
| tibia_extensor | 4 | 19,322 | 0.019 |
| trochanter_flexor | 21 | 8,267 | 0.055 |
| trochanter_extensor | 4 | 10,058 | 0.002 |
| coxa_promotor | 12 | 77,928 | 0.008 |
| coxa_remotor | 10 | 42,194 | 0.005 |
| other | 14 | 54,387 | 0.003 |
| **all T1 leg MN** | **94** | **229,986** | **0.008** |

The s15 core (12 cells) supplies **0.8%** of all synaptic input onto T1 leg MNs at this
threshold (pool range 0.2%-5.5%); everything else is outside-core.

## Out-of-core input by hemilineage (top 10 of 48, all T1 leg MN pooled)

| hemilineage | synapses | share of total input |
|---|---:|---:|
| 20A.22A | 24,655 | 0.107 |
| 04B | 21,580 | 0.094 |
| 03A | 19,484 | 0.085 |
| 13A | 19,482 | 0.085 |
| 21A | 16,494 | 0.072 |
| 16B | 14,057 | 0.061 |
| 08A | 13,894 | 0.060 |
| 19A | 12,515 | 0.054 |
| TBD (unassigned) | 10,905 | 0.047 |
| 01A | 8,293 | 0.036 |

For comparison, the core's own hemilineages (16B, 17A, 19A) are already in or near this top
10 (16B 6th, 19A 8th) but as the 12 *core* cells specifically, not the hemilineage total above
(which includes many non-core 16B/19A cells too).

## Top-20 out-of-core presynaptic types (all T1 leg MN): DNg100 hops, core input, flexor/extensor side

| type | synapses | DNg100 within 2 hops | synapses from core | flexor/extensor-leaning |
|---|---:|---|---:|---|
| ANXXX006 | 3888 | 2-hop | 58 | extensor |
| IN20A.22A001 | 3505 | direct | 40 | extensor |
| IN19A016 | 2679 | direct | 1227 | extensor |
| IN13A051 | 2569 | 2-hop | 1523 | extensor |
| IN16B061 | 2510 | 2-hop | 5 | extensor |
| IN21A001 | 2455 | direct | 0 | extensor |
| IN19A005 | 2322 | direct | 0 | extensor |
| IN04B015 | 2231 | 2-hop | 0 | flexor |
| IN20A.22A018 | 2204 | 2-hop | 278 | extensor |
| IN03A066 | 1928 | 2-hop | 232 | (coxa only) |
| IN08A026 | 1928 | 2-hop | 28 | (coxa only) |
| IN08A030 | 1898 | 2-hop | 5 | (coxa only) |
| IN16B034 | 1838 | 2-hop | 0 | (coxa only) |
| IN17A052 | 1784 | 2-hop | 207 | extensor |
| IN19A003 | 1710 | 2-hop | 11 | (coxa only) |
| IN16B016 | 1679 | direct | 315 | flexor |
| DNg105 | 1648 | 2-hop | 0 | flexor |
| IN03A045 | 1635 | 2-hop | 176 | extensor |
| IN16B020 | 1572 | 2-hop | 242 | extensor |
| IN03A046 | 1541 | 2-hop | 445 | flexor |

Every one of these 20 types is within **2 hops of DNg100** at the >=5-synapse threshold (7
direct, 13 via one intermediate); 13 of 20 also receive >=5 synapses directly from the core.
6 types (IN21A001, IN19A005, IN04B015, IN16B034, DNg105, IN03A046) receive **no** direct
core input at this threshold.

## Reciprocal flexor<->extensor inhibition among the top-20

Flexor-leaning: IN04B015, IN16B016, DNg105, IN03A046. Extensor-leaning: ANXXX006,
IN20A.22A001, IN19A016, IN13A051, IN16B061, IN21A001, IN19A005, IN20A.22A018, IN17A052,
IN03A045, IN16B020. (IN03A066, IN08A026, IN08A030, IN16B034, IN19A003 feed mainly the coxa
pools and were excluded from this check.)

GABA/glutamate connections found (>=5 synapses) between a flexor- and an extensor-leaning
candidate:

- IN21A001 (glutamate, extensor-leaning) -> IN04B015 (flexor): 756 syn
- IN21A001 (glutamate) -> IN16B016 (flexor): 12 syn
- IN16B020 (glutamate, extensor) -> IN16B016 (flexor): 64 syn
- DNg105 (gaba, flexor-leaning) -> IN20A.22A001 (extensor): 117 syn
- DNg105 (gaba) -> IN03A045 (extensor): 36 syn
- DNg105 (gaba) -> IN19A016 (extensor): 16 syn
- DNg105 (gaba) -> IN13A051 (extensor): 11 syn
- IN16B016 (glutamate, flexor) -> IN19A005 (extensor): 6 syn
- IN19A005 (gaba, extensor) -> IN16B016 (flexor): 5 syn

## What this says

**Derived** (computed directly from the connectome at the stated threshold): the s15 106-cell
core supplies under 1% of synaptic input to T1 leg MNs overall (0.2%-5.5% per pool), so the
bulk of leg-MN drive is structurally outside that core; the largest out-of-core hemilineage
contributions are 20A.22A, 04B, 03A, 13A and 21A (each 7-11% of total input), with 16B and 19A
close behind; every one of the top-20 out-of-core types sits within two synaptic hops of
DNg100 at this threshold, and most (13/20) also receive direct core input, so core and DNg100
converge onto largely the same second layer rather than driving disjoint populations; and
there are several >=5-synapse GABAergic or glutamatergic connections running both ways between
types that mainly feed flexor pools and types that mainly feed extensor pools (e.g. DNg105 ->
several extensor-feeding types, IN19A005 <-> IN16B016), i.e. a reciprocal-inhibition motif
exists among this candidate set, though it is a small fraction of each type's total output and
glutamate's sign here is unresolved (F-SIGN-1, could be excitatory via a non-GluCl receptor).
**Inferred**: this out-of-core, DNg100-adjacent layer is a plausible candidate location for
the premotor rhythm/antagonist machinery the s16/s17 arms failed to find inside the core
(the hemilineages 13A, 19A, 16B, 03A and 04B seen here line up with the independent literature
scan in `docs/research/s17_premotor_hemilineages.md`, which flagged exactly these hemilineages
for reciprocal flexor/extensor inhibition and DN-driven rhythm) — but this script does not
test dynamics, only establishes that the anatomical substrate for such a motif is present at
this threshold; it is not evidence that the motif actually functions this way in the model.

## Caveats

- Pool mapping for `coxa_promotor`/`coxa_remotor`/trochanter/tibia pools leans on function
  notes already in `tests/test_muscles.py` and `tests/test_muscles_s10.py`, not on a fresh
  anatomical derivation; `other` (adductor, sternotrochanter, tergotrochanter) has no
  flexor/extensor axis assigned and was excluded from the reciprocal-inhibition check.
- Threshold is a single choice (>=5); the per-type rankings and the hemilineage shares would
  shift at a different threshold, especially for low-synapse-count candidates near the top-20
  cutoff.
- Hemilineage is missing (`TBD`/`nan`) for a non-trivial slice of types, including some
  descending/sensory types (DNg93, DNg105, SNpp45, DNge036) that aren't assigned a VNC
  hemilineage at all — their contribution is real but unattributed in the by-hemilineage
  table (`TBD` is 4.7% of out-of-core input on its own).
- "Flexor/extensor-leaning" for each candidate type is a majority vote of its own output
  synapses into the tibia/trochanter flexor vs. extensor pools only (coxa output is ignored
  for that vote), so a type that splits output between coxa and tibia pools may be
  mislabeled; 5 of the top-20 types feed mainly coxa pools and got no label at all.
- DNg100's "2 hops" search allows any intermediate cell type (not just the top-20 set or the
  core), so the 2-hop flag is a loose upper bound on reachability, not a claim about which
  specific pathway carries the drive.
