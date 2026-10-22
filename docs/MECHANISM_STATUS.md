# Mechanism status (Ben's definition, 21 Oct 2026)

A mechanism is **done** only when it is (1) built at full fidelity (the required level in
`docs/research/FIDELITY.md`), (2) switched ON in the frontier profile `m10f` with values inside a cited
measured range, and (3) passing a unit or physiology check against a measurement, where one exists.
Behaviour is not required.

Status words:
- **done:** all three hold.
- **built-off:** built at the required level, but off in `m10f` or at neutral.
- **partial:** something is built (on or off), but below the required level, or on with values guessed
  or outside a cited range, or with no unit check where a measurement exists.
- **absent:** nothing built, or a stub only.

One row per entry in `data/model/mechanisms.yaml`; X1 and X2 are infrastructure and are not counted.
Owners: **fly** = neuromodulation, hormones, internal state, metabolism, plus (Director, 21 Oct) neuron
intrinsics N1-N4 and glia N27, N33; **fly2** = plasticity, synaptic dynamics, sensors, body, plus (Director,
21 Oct) N13, N14, N18. The Director's brief called N13/N14/N18 "the giant-fibre escape system"; only N18 is GF.
N13 is per-type conduction delays and N14 is membrane noise. The IDs were followed as listed. N27 (lumped glial
K+) is glial, not synaptic, so it went to fly with N33.

Frontier `m10f` = m10f0 = m9c + `sense:taste_leg|modality_source` 1 + `connectome:unclear|nt_by_development` 1.
It sets `state:organs|model` 1, so every internal-state row below is on, but almost every value in
`internal_state.PARAMS` is labelled guessed and its bounds are guessed as well.

**Count (fly rows, 21 Oct 21:32 CDT): 0 done of 14.**

| id | tier | owner | status | unit check | evidence |
|---|---|---|---|---|---|
| B1 | A | fly2 | fly2 to fill | | registry have |
| B2 | A | fly2 | fly2 to fill | | registry partial |
| B3 | A | fly2 | fly2 to fill | | registry partial |
| B4 | A | fly2 | fly2 to fill | | registry partial; `muscle:leg\|model` 1 in m10f |
| B5 | A | fly2 | fly2 to fill | | registry partial |
| B6 | A | fly2 | fly2 to fill | | registry have |
| B7 | A | fly2 | fly2 to fill | | registry partial; detachment 1 in m10f |
| B8 | A | fly2 | fly2 to fill | | registry partial |
| B9 | B | fly2 | fly2 to fill | | registry partial |
| B10 | B | fly2 | fly2 to fill | | registry partial |
| B11 | B | fly2 | fly2 to fill | | registry partial |
| B12 | B | fly2 | fly2 to fill | | registry have |
| B13 | B | fly2 | fly2 to fill | | registry partial |
| B14 | B | fly2 | fly2 to fill | | registry have |
| B15 | B | fly2 | fly2 to fill | | registry partial |
| B16 | C | fly2 | fly2 to fill | | registry partial |
| B17 | C | fly2 | fly2 to fill | | registry partial; `state:crop\|pump_gated` 1 in m10f |
| B18 | C | fly2 | fly2 to fill | | registry partial |
| B19 | A | fly2 | fly2 to fill | | registry partial |
| B20 | A | fly2 | fly2 to fill | | registry partial; oscillator 1 in m10f |
| B21 | A | fly2 | fly2 to fill | | registry partial |
| B22 | A | fly2 | fly2 to fill | | registry partial |
| B23 | B | fly2 | fly2 to fill | | registry have |
| B24 | B | fly2 | fly2 to fill | | stub |
| B25 | C | fly2 | fly2 to fill | | stub |
| B26 | B | fly2 | fly2 to fill | | stub |
| B27 | C | fly | absent | none | Stub `state:circulation\|model` 0. Data read s12 (`docs/research/s12_b27_s7_s8_d1.md`). |
| S1 | C | fly | partial | none against a measurement. The tests check direction only (sugar falls with activity, recovers on feeding). | On in m10f. Lumped glucose-eq pool. `conc0` 40 mM is inside the 5-50 mM trehalose range (inferred, web summary, not read). `basal`, `act_scale` guessed. Needed: a resting hemolymph sugar check against a read source. |
| S2 | C | fly | partial | Test `starvation_exhausts_the_store_in_days_not_hours` is a bound, not a comparison to a measured survival time. | On. One store with AKH/DILP sigmoids; all 5 rows guessed. Needed: store size from measured TAG/glycogen, survival on water against a measured value. |
| S3 | C | fly | partial | none against a measurement | On. Crop/gut fill; ingest rate, crop max, both taus guessed (CAFE leads not read). |
| S4 | C | fly | partial | none against a measurement | On. Water balance; `w0` inferred (insects 60-70% water), the rest guessed. Needed: desiccation survival time. |
| S5 | A | fly | partial | none | No body heat balance; world temperature drives Q10 (N28). Probably body temperature = ambient is the right level for a 1 mg fly (inferred, unchecked). |
| S6 | A | fly | absent | none | Stub `state:hemolymph\|ion_model` 0. Data read s12 (`s12_hemolymph_ions.md`). |
| S7 | C | fly | absent | none | Stub; healthy lab fly assumed. |
| S8 | C | fly | absent | none | Stub; courtship not a target. |
| N1 | A | fly | to fill | | registry partial |
| N2 | A | fly | to fill | | registry partial; rung-1 channels on in m10f |
| N3 | A | fly | to fill | | registry have |
| N4 | A | fly | to fill | | registry have; increment 0 (off) in m10f |
| N5 | A | fly2 | fly2 to fill | | registry have |
| N6 | A | fly2 | fly2 to fill | | registry partial |
| N7 | A | fly2 | fly2 to fill | | registry have; slow fractions 0 in m10f |
| N8 | A | fly2 | fly2 to fill | | registry have; NMDA fraction 0 |
| N9 | A | fly2 | fly2 to fill | | registry have; off in m10f |
| N10 | A | fly2 | fly2 to fill | | registry have; off |
| N11 | A | fly2 | fly2 to fill | | registry have; off |
| N12 | B | fly2 | fly2 to fill | | registry partial; strengths 0 |
| N13 | A | fly2 | fly2 to fill | | registry have |
| N14 | A | fly2 | fly2 to fill | | registry have; noise 0 in m10f |
| N15 | A | fly2 | fly2 to fill | | registry partial |
| N16 | B | fly2 | fly2 to fill | | registry partial |
| N17 | B | fly2 | fly2 to fill | | registry partial |
| N18 | B | fly2 | fly2 to fill | | registry partial |
| N19 | C | fly | partial | none yet; pre-registered U1/U1h kinetics (Lv 2024, Wan 2021), U2 Mi4 calibration (Strother 2018) with Dacks 2009 PN 5-HT held out, U3 sign test (DECISIONS 21 Oct 21:56). Hige 2015 is associative and presynaptic, so it is not an N19 check. | Volume pools for DA, OA, 5-HT built in `lif.py` (gain × (1 + Σ s·m)). All sensitivities 0, so the pools have no effect; no tyramine pool; no per-type receptor map; `mod_tau` 1 s and increment guessed. Required level: pools with per-type receptor maps and second-to-minute kinetics. s16 `octopamine_state.csv` is a diagnostic tonic drive, not this mechanism. |
| N20 | C | fly | partial | none | On. Minimal tonic mV drive from lumped state to ISN, IPC, LB3a/b/c; every gain guessed. No peptide release cells or receptor maps (AKH, DILPs, NPF, sNPF, DH44, CRZ, ...). |
| N21 | C | fly2 | fly2 to fill | | registry have; rates 0 |
| N22 | C | fly2 | fly2 to fill | | registry partial |
| N23 | C | fly2 | fly2 to fill | | registry partial |
| N24 | C | fly2 | fly2 to fill | | registry partial |
| N25 | C | fly | partial | Tests check direction and hysteresis only. | On. Borbély process S plus dFB switch on FB6A_a/b/c and FB6E. `t_sleep` 5 min inferred (Shaw 2000); the 7 other rows guessed. Needed: daily sleep and rebound against measurement. |
| N26 | C | fly | partial | DN1p day/night firing (F-CLOCK-1): `clock_gain` 7.75 fitted at CT 2, held-out CT 10 passes. | On. Lumped Stuart-Landau oscillator; period 24 h (Konopka & Benzer 1971 range). Light coupling, `l50`, `ct_light`, peak hours guessed; no molecular loop or CRY/eye light input. Closest of the fly rows to done. |
| N27 | C | fly | to fill | | registry partial; gain 0 |
| N28 | A | fly | partial | none | Q10 2 at 25 °C on neural rates (inferred, structural). Needed: a cited Drosophila neural Q10 range and a check. |
| N29 | A | fly2 | fly2 to fill | | registry partial |
| N30 | A | fly2 | fly2 to fill | | registry partial (fly2 first build s20) |
| N31 | C | fly2 | fly2 to fill | | stub |
| N32 | C | fly2 | fly2 to fill | | stub |
| N33 | C | fly | to fill | | stub (glia; OA/TA-gated Ca would touch N19) |
| N34 | C | fly2 | fly2 to fill | | stub |
| D1 | C | (phase 2) | absent | | after mechanism-complete (Ben, 21 Oct) |

**Gaps with no registry row (fly area):** arousal (it has no row, and in flies it is mostly OA/DA state, so it is
folded into N19); tyramine as its own pool; neuropeptide release by identified cells (folded into N20).

**fly plan, highest leverage first:**
1. N19: per-type receptor map from transcript probabilities (`receptors.gene_probabilities`); sign from G-protein
   coupling; magnitude bounded by measured effects (`s16_neuromod_rowcheck.csv`); TA pool.
2. N20: identified peptide cells and receptor maps.
3. S1-S4: replace the guessed rows with read sources and add physiology checks (resting trehalose, starvation
   and desiccation survival).
4. N26 light input; N25 against daily sleep; S5/N28 temperature.
