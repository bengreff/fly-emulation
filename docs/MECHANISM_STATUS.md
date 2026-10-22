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
| S1 | C | fly | partial | Consistency only: 39.2 mM after 6 h of fasting against a set point of 40 (s19, `runs/s19/met/checks.json`). | On in m10f with the s10 guesses. s19 adds sourced values behind `state:organs\|values_from_sources` (neutral 0): basal use 0.00626 nmol/s, derived from Burggren 2017 (grouped males, 25 °C), and hemolymph volume 24 nL (inferred, secondary). `conc0` is still from a web summary; `k_act` and `act_scale` are guessed (flight 10-15× is secondary, and there is no walking value). Needed: an adult hemolymph trehalose read, and the switch through a stage gate. |
| S2 | C | fly | partial | s19 held-out starvation: 28.4 h against 24-112 h, pass (weak: secondary band, near its edge; fails at the single-fly metabolic rate, 12.2 h). Spent. | Store 672 nmol glucose-eq from about 50 µg TAG per male (derived; glycogen missing), behind the s19 switch (off). The AKH/DILP loop is still guessed (k_rel, k_sto, K_fat, sensitivity, τ). |
| S3 | C | fly | partial | s19 held-out CAFE: 1.85 µl/fly/day against 1.0-2.25 (Ja 2007, single males), pass. 1.00 with yeast-extract energy counted; 4.3 at the single-fly rate. Spent. | Crop τ 3.1 h (from 32%/h turnover, derived) and gut τ 45 min (inferred), behind the s19 switch (off). Ingest rate and crop capacity are still guessed (sip 1.05 nL and meals of 6-200 nL are leads only). |
| S4 | C | fly | partial | Desiccation not scored in s19 (loss rate and lethal water fraction not found); its held-out values stay unspent. | `w0` 344 nL from Burggren male wet minus dry mass (derived), behind the s19 switch. Evaporation, excretion and the hemolymph share are still guessed. Needed: a water-loss rate and a lethal-loss fraction. |
| S5 | A | fly | partial | none | No body heat balance; world temperature drives Q10 (N28). Probably body temperature = ambient is the right level for a 1 mg fly (inferred, unchecked). |
| S6 | A | fly | absent | none | Stub `state:hemolymph\|ion_model` 0. Data read s12 (`s12_hemolymph_ions.md`). |
| S7 | C | fly | absent | none | Stub; healthy lab fly assumed. |
| S8 | C | fly | absent | none | Stub; courtship not a target. |
| N1 | A | fly | partial | none | Point LIF for every cell; graded mode only for photoreceptors, L1-L3 and APL (13B/10B `graded_rec` rows exist behind a neutral switch). Required level: spiking or graded by class, from recordings. Most classes have no recorded mode, so the default is spiking (guessed). |
| N2 | A | fly | partial | Slow tibia-flexor MN fit to Azevedo 2020 current steps (fitted at that class only). | V_rest −52, threshold −45 and τ_m 20 ms are Shiu 2024's shared values (borrowed, not per class). Class threshold-offset and τ_m-scale rows are built at neutral. Rung-1 channels (A, M, h, T, NaP, Kv2, BK, SK) are on in m10f with per-type densities from mRNA. Candidate in-range values: MBON τ_m 16 ms measured (13.8-18.4) against 20; HS τ 4.3-4.9 ms (s13 table, not row-checked). |
| N3 | A | fly | partial | S0 rest-vs-reference (s13): MB classes (MBON, KC, DAN, APL, DPM) are 0 Hz at rest, while published spontaneous rates are nonzero. | Class tonic-drive and noise rows are built; noise is 0 in m10f; per-type spontaneous drive for a few types (some fitted). The resting-rates reference CSV still has broken quoting (21 rows). |
| N4 | A | fly | built-off | none: no class has a numeric recorded adaptation ratio (MBON data qualitative). | Class-grain adaptation built (bfc5751); increment 0 in m10f. `adapt_fit.py`: a recorded late/early ratio of 0.5 would map to 3.05 mV (inferred). |
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
| N27 | C | fly | partial | none | Per-class K+ load from spikes, cleared with τ, depolarises the class; gain 0 (off) in m10f. No measured clearance τ or K+ rise per spike read; FIDELITY sets no required level for glia. |
| N28 | A | fly | partial | none | Q10 2 at 25 °C on neural rates (inferred, structural). Needed: a cited Drosophila neural Q10 range and a check. |
| N29 | A | fly2 | fly2 to fill | | registry partial |
| N30 | A | fly2 | fly2 to fill | | registry partial (fly2 first build s20) |
| N31 | C | fly2 | fly2 to fill | | stub |
| N32 | C | fly2 | fly2 to fill | | stub |
| N33 | C | fly | absent | none | Stub `glia:all\|astrocyte_model` 0. Glia are not in the male-cns Neuron table. Larval data only (Ma 2016: astrocyte Ca 8-9 events per 15 min, silences DA neurons via adenosine); no adult transfer function. OA/TA-gated astrocyte Ca would read N19's OA pool. |
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
