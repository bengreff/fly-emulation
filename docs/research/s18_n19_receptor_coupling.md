# S18/N19: receptor coupling, magnitude and kinetics for the volume-transmitted modulator gain term

Task: fill the sign/size/time-course priors behind `s_ik` in `gain_i = 1 + sum_k s_ik * m_k` (dopamine,
octopamine, serotonin pools now; tyramine to be added), per cell type `i`, from (a) which receptor genes the
repo's transcript table actually carries, (b) G-protein coupling (gives sign), (c) measured magnitude and
kinetics (bounds the size and the pool's effective time constant).

Does not repeat `docs/research/s16_neuromod_rowcheck.csv` (the row-check of `s13_neuromodulation_effects.csv`)
or `docs/research/s16_octopamine_excitability.md`; both are read first and cited by id below rather than
re-verified. New literature in this file was searched via `WebSearch`/`WebFetch` this session (2026-10-21);
"read: full text / abstract / secondary summary" says how far I actually got for each new citation. No DOI
below was typed from memory without a confirming search hit; where a source could not be confirmed to exist
this session, it is flagged in the gaps section rather than cited.

## 0. What the repo's transcript table actually covers (src/flyemu/receptors.py)

`gene_probabilities()` (the only function that builds per-cell receptor-expression probabilities) reads exactly
three files: `data/derived/receptor_calls_davis2020.csv`, `receptor_calls_ozel2021.csv`,
`receptor_calls_allen2020_vnc.csv`. Their union of gene columns is:

```
5-HT1A, 5-HT1B, 5-HT2A, 5-HT2B, 5-HT7,
Dop1R1, Dop1R2, Dop2R, DopEcR,
Oamb, Octbeta1R, Octbeta2R, Octbeta3R,
GABA-B-R1, GABA-B-R2, GABA-B-R3, Grd, Rdl, Lcch3, HisCl1, ort,
GluClalpha, GluRIA, GluRIB, mGluR, Nmdar1, Nmdar2,
mAChR-A, mAChR-B, nAChRalpha1, nAChRalpha5, nAChRalpha6, nAChRalpha7
```

(Davis 2020 carries a smaller per-type subset of the same gene list; Ozel 2021 and Allen 2020 carry the full 32.)

For dopamine/octopamine/serotonin this means **Dop1R1, Dop1R2, Dop2R, DopEcR, Oamb (=OAMB/Octα1R), Octbeta1R,
Octbeta2R, Octbeta3R, 5-HT1A, 5-HT1B, 5-HT2A, 5-HT2B, 5-HT7 all already have a per-cell expression probability
sitting in `P` from `gene_probabilities()`** — they are just not consumed downstream: `FAMILIES` in
`receptors.py` only builds shares for `GABA_B`, `mAChR`, `mGluR`, `NMDA` (fast/slow synaptic-receptor currents,
a different mechanism from the modulator-pool gain term this file is for). Building `s_ik` from these columns
is additive to the existing code, not a rewrite.

**Not covered by any of the three wired-in tables:** `Octalpha2R` (the fourth OA receptor, Gi/o), and all three
tyramine receptors (`TyrR`/`honoka`, `TyrRII`, and whatever the repo would call Oct-TyrR/TAR1 — nomenclature
checked below). There is a fourth, unwired data source, `data/derived/epiney2025_cluster_receptors.csv` /
`epiney2025_identity_receptors.csv`, whose column header *does* include `Octalpha2R` (plus `Tbh`, `SerT`,
`ChAT`, `Gad1`, `VGlut`, `ple` — biosynthesis/transporter genes, not receptors) — but confirmed by `grep` that
`receptors.py` never reads it, and it still carries no tyramine receptor column at all. **If `s_ik` needs
Octalpha2R expression, the existing `gene_probabilities()` call must be extended to read `epiney2025_*`; tyramine
receptor expression per cell type is not available from any table in `data/derived/` and would need a new
transcriptome crosswalk before `s_ik` for tyramine can be type-specific** (a pooled/class-level guess is the only
option until then).

## 1. Coupling table (sign-determining)

| receptor | G protein | usual neuronal effect | evidence type | citation | read level |
|---|---|---|---|---|---|
| Dop1R1 (DUMB) | Gs | excitatory (cAMP up) | heterologous (NIH3T3/S2); review restates cloning papers | Himmel, Gurung, Haas 2020/2021, *Cell Tissue Res*, DOI 10.1007/s00441-020-03371-x, PMID 33501619 — secondary review citing Gotzes et al. 1994 for the original clone | secondary (per s16_neuromod_rowcheck s13_001; not re-verified this session) |
| Dop1R2 (DAMB) | Gs (cAMP) **and** Gq (Ca²⁺) — dual coupling, agonist/context-dependent | mixed; Gq arm implicated in forgetting | heterologous (HEK293/S2), EC50 for cAMP and Ca²⁺ arms measured separately | Himmelreich, Masuho, Berry, MacMullen, Skamangas, Martemyanov, Davis 2017, *Cell Reports* 21, "Dopamine Receptor DAMB Signals via Gq to Mediate Forgetting in Drosophila" | secondary summary (per s16_neuromod_rowcheck s13_003/004; full text paywalled both sessions, DOI not independently re-confirmed) |
| Dop2R (D2R) | Gi/o | inhibitory (cAMP down) | heterologous (HEK293, forskolin-stimulated cAMP assay) | Hearn, Ninan, Wen, Levitan, Hall... 2002, *PNAS* 99:14554–14559, PMID 12391323, DOI 10.1073/pnas.202498299 | secondary (per s16_neuromod_rowcheck s13_005/006; not re-fetched this session) |
| DopEcR | noncanonical / agonist-specific: dopamine → PI3K/Akt (and cAMP in some reports); 20-hydroxyecdysone → MAPK/ERK — not a single fixed Gs/Gi/Gq call | mixed, context- and ligand-dependent; cannot be reduced to one sign | heterologous (mammalian cell line) and *Drosophila* behavioural knockdown | Srivastava, Yu, Kennedy, Chatwin, Reale, Hamon, Smith, Evans 2005, *J. Neurosci.* 25(26):6145–6155, DOI 10.1523/JNEUROSCI.1005-05.2005 (confirmed real via FlyBase reference report FBrf0187904; title/authors/volume match) | secondary summary (WebSearch synthesis of abstract-level content this session; full text not fetched — **note: an earlier internal guess that this was a 2005 PLoS Biology paper was wrong and is corrected here; it is J. Neurosci.**) |
| OAMB (Octα1R, `Oamb`) | Gq (and some Gs reports) | excitatory (Ca²⁺ up) | heterologous; classification scheme | Evans & Maqueira 2005, *Invert. Neurosci.* 5:111 | secondary (per s16_neuromod_rowcheck / s13_014; "derived" label in that file) |
| Octbeta1R / Octbeta2R / Octbeta3R | Gs | excitatory (cAMP up) | heterologous (HEK293/CHO) | Balfanz, Strünker, Frings & Baumann 2005, *J. Neurochem.* 93:440 (Octβ1R, EC50) **and** Maqueira, Chatwin & Evans 2005, *J. Neurochem.* 94:547–560, PMID 15998303, DOI 10.1111/j.1471-4159.2005.03251.x (all three Octβ receptors, CHO cells — per rowcheck s13_012, the all-three-cAMP finding is Maqueira's, not Balfanz's) | secondary (per s16_neuromod_rowcheck s13_011/012; verbatim EC50 quote confirmed that session) |
| Octalpha2R | Gi/o | inhibitory (cAMP down); "associated with neuronal silencing" in the source's own framing | *Drosophila* in vivo (behavioural/knockout) plus prior pharmacology | Nakagawa, Maehara, Kume, Ohta, Tomita 2022, *Genes Brain Behav.* 21(6):e12807, DOI 10.1111/gbb.12807, PMID 35411674 | secondary summary (WebSearch synthesis this session; full text not fetched) |
| 5-HT1A | Gi | inhibitory (cAMP down) | heterologous | Saudou, Amlaiky, Plassat, Borrelli, Hen 1992, *EMBO J.* 11:7–17, DOI 10.1002/j.1460-2075.1992.tb05021.x — **rowcheck note: this paper's own terms are "5-HT-dro2A/2B"; also reports dual Gi + Gq (PLC) coupling, not Gi alone** | measured (per s16_neuromod_rowcheck s13_024, corrected) |
| 5-HT1B | Gi | inhibitory (cAMP down) | heterologous | same as 5-HT1A (s13_024) | measured (secondary, per rowcheck) |
| 5-HT2A | Gq | excitatory (Ca²⁺ up) | heterologous | Gasque, Conway, Huang, Rao & Vosshall 2013, *Sci. Rep.* 3:2120, DOI 10.1038/srep02120 (author list corrected per rowcheck s13_019 — not "Conzelmann") | measured (secondary: Saudou et al. 1992, per rowcheck) |
| 5-HT2B | Gq | excitatory (Ca²⁺ up) | heterologous | same as 5-HT2A | measured (secondary, per rowcheck) |
| 5-HT7 | Gs | excitatory (cAMP up) | heterologous | Witz et al. 1990; Colas et al. 1995, as reviewed (per rowcheck s13_025 — no DOI independently found for either; cite with that caveat) | measured (secondary, naming history only partly confirmed) |
| TyrR (`honoka`/Oct-TyrR/CG7485 — see tyramine note) | Gi/o | inhibitory (cAMP down; also reduces L-type Ca²⁺ current downstream) | *Drosophila* larval motoneuron (in situ), **not** heterologous | Schützler, Girwert, Hügli, Mohana, Roignant, Ryglewski 2019, *PNAS* 116(9):3805–3810, DOI 10.1073/pnas.1813554116, PMCID PMC6397572 | full text (fetched this session via PMC) |
| TyrRII (CG16766, the Cazzamali gene) | unknown from this source (cloning paper reports pharmacology, not coupling clearly) | — | heterologous (*Xenopus* oocytes) | Cazzamali, Klaerke & Grimmelikhuijzen 2005, *Biochem. Biophys. Res. Commun.* 338(2):1189–1196, PMID 16274665 | secondary summary (WebSearch synthesis; abstract-level EC50 only) |
| Oct-TyrR (TAR1 in some papers) | Gi/o (adenylate cyclase inhibition in NIH 3T3 cells) | inhibitory | heterologous (NIH 3T3) | Saudou, Amlaiky, Plassat, Borrelli, Hen 1990, *EMBO J.* 9:3611–3617, PMID 2170118 | secondary summary (WebSearch synthesis; this is the *original* tyramine-receptor cloning paper, and per Schützler et al. 2019 the modern gene name for the functionally relevant receptor in motoneurons is `honoka` — **nomenclature across TyrR/TAR1/Oct-TyrR/honoka is not consistently used across papers; do not assume any two of these names are the same receptor without checking FlyBase's current symbol**) |

## 2. Magnitude table (at most ~15 rows, Drosophila preferred)

| modulator | receptor | cell | effect | value | bath/stim conc. | citation (figure) | label | read level |
|---|---|---|---|---|---|---|---|---|
| DA | unspecified (KC DAN input) | MBON-γ1pedc>α/β | EPSC charge-transfer reduction | −90 ± 3.7% (range −86.3 to −93.7%) | optogenetic 4×1ms pulses, 2 Hz | Hige, Aso, Modi, Rubin, Turner 2015, *Neuron* 88:985 (their Fig., per s13_008) | measured | secondary (per rowcheck; not re-fetched) |
| DA | Dop1R2 (Gs arm) | HEK293/S2 heterologous | cAMP EC50 | 7.37 ± 0.69 µM | bath dopamine | Himmelreich et al. 2017 *Cell Reports* 21 (s13_003) | measured_related (heterologous) | secondary |
| DA | Dop1R2 (Gq arm) | HEK293/S2 heterologous | Ca²⁺ EC50 | 56.7 ± 7.7 nM | bath dopamine | same (s13_004) | measured_related (heterologous) | secondary |
| OA | Octβ1R | HEK293 heterologous | cAMP EC50 | ≈0.03 µM (3×10⁻⁸ M) | bath octopamine | Balfanz et al. 2005 *J Neurochem* 93:440 (s13_011, verbatim) | measured_related (heterologous) | secondary (verbatim quote confirmed in rowcheck) |
| OA | Octβ1-3R | HEK293/CHO heterologous | tyramine vs. OA selectivity | ≥100-fold higher conc. needed for tyramine | bath | Balfanz et al. 2005 (s13_013) | measured_related (heterologous) | secondary |
| OA | Oct‐TyrR class (unspecified) | adult *Drosophila* brain neurons, ex vivo whole brain | Ca²⁺-transient (jGCaMP7b) EC50 | 11.24 ± 6.50 µM | bath OA, 100 nM–10 mM range | Černe, Horvat et al. 2025, *Acta Physiol.* 241(2):e14270, DOI 10.1111/apha.14270, PMID 39801347 | measured | full text (fetched this session via PMC11726276) |
| OA | same | adult brain **neurons** | peak ΔF/F₀ at 10 µM OA | 83.75 ± 12.19% | 10 µM bath | same, same fetch | measured | full text |
| OA | same | adult brain **astrocytes** (for contrast — glia, not neurons) | peak ΔF/F₀ at 10 µM OA | 24.96 ± 3.16% (≈3.4-fold smaller than neurons) | 10 µM bath | same | measured | full text |
| OA | same | adult brain neurons | rate of Ca²⁺ rise | 1.57 ± 0.29 %/s (vs. 0.43 ± 0.06%/s in astrocytes) | 10 µM bath | same | measured | full text |
| TA | `honoka`/Oct-TyrR | 3rd-instar larval motoneuron (whole-cell, in situ) | firing-rate decrease | significant & reversible (exact % not extracted from this fetch — figure-panel only, Fig. 2C) | 10⁻⁵ M bath tyramine (10⁻⁴ M gave no effect) | Schützler et al. 2019 *PNAS* 116:3805 (Fig. 2C, Fig. 3H) | measured | full text (numeric % still in figure pixels, not text — see gaps) |
| TA | same | same | L-type-like Ca²⁺ current | "small but significant reduction" (no % extracted) | 10⁻⁵ M bath tyramine | same (text body) | measured | full text, but exact magnitude not in the prose |
| OA | locust fSR→BA1 flight MN synapse | locust (not Drosophila) | EPSP amplitude | decreases (direction only, no %) | 1×10⁻⁴ M | per s16_octopamine_excitability.md (s16_oa_010) | measured_related (other insect) | secondary (carried from s16, not re-checked) |
| OA | cricket Kenyon cell, isolated | single Ca²⁺ channel open probability (NPo) | decreases 29 ± 7% | 10 µM bath | *ScienceDirect* abstract (cricket MB, PMID 18761015) | measured_related (other insect) | abstract (WebSearch synthesis this session, not independently fetched) |
| DA | unspecified KC DAN input | MBON (compartment-specific) | depolarization onset/decay (shape, not amplitude) | peaks >2 s after stimulus offset, decays over tens of s | endogenous DAN stimulation, calcium/voltage imaging | Cohn, Morantte & Ruta 2015, *Cell* 163:1742 — this specific kinetic description came from a WebSearch synthesis, not from the rowchecked s13_010 line (which only has the qualitative "can depolarize" quote) | measured | secondary summary (not independently fetched full text this session — **flag for a follow-up full-text check before using the "tens of seconds" number quantitatively**) |

Rows kept to measured/measured_related only; several candidate OA/5-HT magnitude rows from the s13 CSV (e.g.
Longden & Krapp 2009 CDM-driven firing-rate/gain increase in blowfly VS/V1 cells) are direction-only in that
file already and were not repeated here since s16_octopamine_excitability.md already covers them.

## 3. Kinetics table

| quantity | value | prep | citation | label | read level |
|---|---|---|---|---|---|
| GRAB-DA1m sensor τ_on | 60 ± 10 ms | in vitro sensor characterization (cell line / rapid perfusion — this session's search did not confirm whether this specific number is the HEK-cell or the in-fly imaging condition) | Sun, Zeng, Jing, ... Li 2018, *Cell* 174(2):481–496, DOI 10.1016/j.cell.2018.06.042, PMID 30007419 | measured_related (sensor characterization, likely heterologous) | secondary summary (WebSearch synthesis; PubMed/cell.com full text both blocked this session — **could not confirm which prep these τ values were measured in**) |
| GRAB-DA1m sensor τ_off | ≈3 s | same caveat as above | same | measured_related | secondary summary |
| GRAB-DA1h sensor τ_on | 140 ± 20 ms | same caveat | same | measured_related | secondary summary |
| GRAB-DA1h sensor τ_off | ≈17 s | same caveat | same | measured_related | secondary summary |
| GRAB-OA (OA1.0) τ_on, in vitro rapid perfusion | ≈0.02 s | heterologous/in vitro perfusion | Lv, Cai, Zhang, Xia, Li, Wang, Wang, Zeng, Xue, Mao, Li 2024, *Natl. Sci. Rev.* 11(5):nwae112, DOI 10.1093/nsr/nwae112, PMID 38798960, PMCID PMC11126161 | measured_related (in vitro) | secondary summary (WebSearch synthesis; not fetched full text this session) |
| GRAB-OA τ_off, in vitro rapid perfusion | ≈1.40 s | same | same | measured_related | secondary summary |
| GRAB-OA τ_on, in vivo (*Drosophila*, single optogenetic pulse) | ≈0.34 s | *Drosophila* in vivo | same | measured | secondary summary |
| GRAB-OA τ_off, in vivo (single pulse) | ≈5.90 s | *Drosophila* in vivo | same | measured | secondary summary |
| GRAB-OA τ_on, in vivo (50 pulses @ 100 Hz) | ≈0.6 s | *Drosophila* in vivo | same | measured | secondary summary |
| GRAB-OA τ_off, in vivo (50 pulses @ 100 Hz) | ≈9.4 s | *Drosophila* in vivo | same | measured | secondary summary |
| Dopamine transporter kinetics (FSCV, optogenetically evoked DA, larval VNC) | Vmax 0.05 µM/s, Km 0.10 µM | *Drosophila* larva, in situ, CsChrimson-evoked | Privman (Trueblood), ... Venton 2015, *J. Neurochem.* 135:695–704, DOI 10.1111/jnc.13286 | measured (larval stage — not adult; flag stage mismatch if used for an adult-CNS model) | secondary summary (WebSearch synthesis; not fetched full text) |
| Dopamine transporter kinetics (FSCV, optogenetically evoked DA, larval protocerebrum) | Vmax 0.08 µM/s, Km 0.11 µM | *Drosophila* larva, in situ | same | measured (larval) | secondary summary |
| Exogenous DA clearance, adult brain, FSCV | qualitative difference wild-type vs. *fumin* (no DAT) only; **no numeric clearance time/rate found in the abstract** | adult *Drosophila* brain, in vivo, exogenous DA injection | Makos, Kim, Han, Heien, Ewing 2009, *Anal. Chem.* 81(5):1848–1854, DOI 10.1021/ac802297b, PMID 19192966 | measured, direction only | abstract (fetched via EuropePMC API this session; abstract itself has no number) |
| Behaviorally-evoked DA transient clearance, adult mushroom body, sugar feeding | reported (by a WebSearch synthesis only) as returning to baseline in "about 10 s" in vivo, vs. faster ex vivo — **this specific number could not be re-confirmed against the paper's own text or abstract this session (both WebFetch attempts on PubMed/PMC pages returned only cookie-consent boilerplate)** | adult *Drosophila*, in vivo FSCV | Shin & Venton 2022, *Angew. Chem. Int. Ed.* 61(44):e202207399, PMID 35989453 | **not verified — do not use the "10 s" number without a direct figure check** | unverified this session |

## 4. Tyramine note

Tyramine does have its own dedicated receptors with a measured neuronal effect in *Drosophila*, but **the direct
electrophysiological evidence found this session is larval, not adult**: Schützler et al. 2019 (*PNAS* 116:3805,
full text fetched) record from 3rd-instar larval motoneurons and show 10⁻⁵ M bath tyramine reversibly decreases
firing rate and reduces an L-type-like Ca²⁺ current, both abolished in `honoka` (the gene they identify as the
functionally relevant tyramine receptor) mutants/RNAi, with the companion receptor "TAR II" (= TyrRII in other
papers' nomenclature) excluded by its insensitivity to the antagonist yohimbine. The original tyramine-receptor
cloning paper (Saudou et al. 1990, EMBO J 9:3611, Gi/o, NIH 3T3 heterologous) and the second tyramine-specific
receptor family paper (Cazzamali, Klaerke & Grimmelikhuijzen 2005, BBRC 338:1189, Xenopus oocytes, EC50≈0.3 µM)
are both real, confirmed-to-exist sources, but neither is itself an adult CNS neuron recording.

**Net: for the adult whole-CNS model, tyramine's receptor-level sign (inhibitory, Gi/o) is reasonably well
grounded (larval motoneuron + two heterologous clones all agree), but no adult-neuron magnitude or kinetic
number for tyramine was found this session — any `s_ik` value for tyramine in an adult cell type is `inferred`
across life stage, not `measured`, same caveat the s16 file already applies to octopamine's VNC leg-MN numbers.**
Nomenclature is a live hazard: TyrR, TyrRII, Oct-TyrR, TAR1 and `honoka` are not used consistently across the
papers found, and no FlyBase cross-check of current gene symbols was done this session — this needs to happen
before any tyramine receptor column is added to the transcript table in part 0.

## 5. Could not verify / explicit gaps

- **GRAB-DA1m/1h τ_on/τ_off prep**: found via WebSearch synthesis only; could not confirm from primary text
  whether these are HEK-cell, cultured-neuron, or in-fly numbers (cell.com returned HTTP 403; PubMed and the
  bioRxiv PDF both failed to yield readable text to WebFetch this session).
- **Shin & Venton 2022 "~10 s" clearance number**: citation confirmed to exist (PMID 35989453), but the specific
  number could not be re-confirmed against the paper's own abstract or text this session — treat as unverified,
  not as a usable kinetic constant.
- **Cohn, Morantte & Ruta 2015 depolarization kinetics** ("peaks >2 s after stimulus offset, decays over tens of
  seconds"): this specific framing came from a WebSearch synthesis, not from the already-rowchecked s13_010 CSV
  line (which only carries the qualitative "can depolarize" quote) and was not independently fetched from the
  primary text this session.
- **Exact % firing-rate decrease and pA/% Ca²⁺-current reduction in Schützler et al. 2019**: the numbers exist
  but are in figure panels (2C, 3H) that WebFetch's text extraction did not render; only the qualitative
  "significant and reversible" / "small but significant" language was retrieved.
- **TyrRII and Oct-TyrR/TAR1/honoka cross-mapping to current FlyBase symbols**: not done this session; flagged
  above as a prerequisite for adding tyramine columns to the transcript table.
- **Octalpha2R per-cell-type expression**: available in `data/derived/epiney2025_cluster_receptors.csv` by
  cluster, not by `male_cns_type`/hemilineage in the same join structure as DAVIS/OZEL/ALLEN; whether that
  cluster scheme can be crosswalked to `male_cns_type` was not checked this session (out of scope — architecture
  note only, not a literature question).
- No DOI in this file was asserted without a confirming search hit this session; the two rows without a DOI
  (5-HT7's Witz 1990/Colas 1995 citation, and the "TAR II" label inside Schützler 2019) are flagged inline above
  rather than given an invented one.
