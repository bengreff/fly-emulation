# Worm Knowledge Index

Status: complete, first pass (auditor, 2026-11-07). This is the map of the worm knowledge base: where each
fact lives today, what is stale or contradicted, what is duplicated, and a proposed lean structure with one
entry point. Built by reading every file in scope (docs/worm/, docs/HANDOFF.md, data/worm/ structure, the
module docstrings in src/wormemu, src/bioemu, scripts/worm, viewer/worm) without running code.

Legend: **Authority** = the file/section to trust and edit. **Secondary** = places the same topic is
mentioned but should defer to the authority. Dates below are as stated in each file's own header, not
guessed.

How current the picture is, in one line: the authorities for "what is built and does it work" are
**MECHANISMS_AUDIT.md** (rows 1-28, 7 Nov) and **CATALOG.md** (numbers, 7 Nov) and **HANDOFF.md** (state, 7
Nov). Everything else that predates 6-7 Nov (BRAIN_PORT.md, GAPCHECK.md, SPIKE.md, W1_RIM_AFD.md, PLAN.md's
roadmap) is a decision/history record, not a live status report, even though several of them still read like
one.

---

## A. Topic Index

### 1. Structure (anatomy, wiring, geometry)

| Topic | Authority | Secondary |
|---|---|---|
| Cell inventory (302 neurons, muscles, glia, end organs) | MECHANISMS_AUDIT.md row 1 | PLAN.md row 1 (original scope); ADOPTED.md (Cook 2019 credit) |
| Morphology / compartments (Virtual Worm geometry) | MECHANISMS_AUDIT.md row 2 | PLAN.md row 2, DECISIONS item 1; `data/worm/structure/geometry.csv` |
| Connectome, chemical and gap wiring (Cook 2019) | `data/worm/structure/{cells,chem_edges,gap_edges}.csv` (built by `scripts/worm/extract_structure.py`) | ADOPTED.md (licence/credit); MANIFEST.md section 1 (source data); BRAIN_PORT.md section 2-3 (why `wiring=cook` was adopted) |
| CeNGEN expression table | `data/worm/structure/cengen_t2.csv` | MANIFEST.md section 3; CHANNEL_SLOTS.md (genes with no kinetics) |
| Transmitter identity, peptide/monoamine receptor pairs | `data/worm/structure/{transmitters_wang2024,peptide_gpcr_pairs,monoamine_receptor_pairs}.csv` | MANIFEST.md section 9; research/NEUROPEPTIDES.md |
| Wiring diagram data for the viewer | `viewer/worm/data/graph.json`, built by `scripts/worm/export_viewer_graph.py` | ADOPTED.md Viewer table |

### 2. Cells, channels, calcium, homeostasis

| Topic | Authority | Secondary |
|---|---|---|
| Channel presence per class (CeNGEN threshold) | MECHANISMS_AUDIT.md row 3 | PLAN.md row 3, DECISIONS item 5; src/wormemu/brain.py `_density` |
| Channel kinetics (BAAIWorm + Nicoletti 2024) | MECHANISMS_AUDIT.md row 4; src/wormemu/nicoletti.py docstring | SPIKE.md (first 13 channels ported/checked); W1_RIM_AFD.md Q2 (9 more channels, port2/port2b/port2c); CHANNEL_SLOTS.md (genes with NO kinetics) |
| Channel densities, Cm, leak, Ra | MECHANISMS_AUDIT.md row 5 | PLAN.md row 5; BRAIN_PORT.md section 6a (literature overrides) |
| Calcium handling (bulk pool, nanodomains) | MECHANISMS_AUDIT.md row 6; src/wormemu/mech/ca_volume.py, capool.py docstrings | PLAN.md row 6 |
| Ion pumps (Na/K-ATPase) | MECHANISMS_AUDIT.md row 27; src/wormemu/mech/pumps.py docstring | — |
| Noise (quantal release, channel noise) | MECHANISMS_AUDIT.md row 26; src/wormemu/mech/noise.py docstring | GAPCHECK.md is unrelated (gap-junction numerics, not noise) |
| Activity-dependent expression / homeostatic tuning | MECHANISMS_AUDIT.md row 19 | PLAN.md row (homeostasis), STRATEGY.md move 2 |
| Slow intracellular signalling (EGL-4, CMK-1, GLR-1, DAF-16, DAF-7, CREB) | MECHANISMS_AUDIT.md row 18; src/wormemu/mech/slow_signalling.py docstring | PLAN.md row 18 |
| Genes with no published kinetics (slots) | CHANNEL_SLOTS.md | MECHANISMS_AUDIT.md row 4's "missing" list |
| Expression-to-physiology map (the plan, not yet built) | STRATEGY.md move 2; research/GENES_TO_PHYSIOLOGY.md | TO_A_REAL_WORM.md item 2 |

### 3. Synapses and gap junctions

| Topic | Authority | Secondary |
|---|---|---|
| Chemical synapses: count, sign, receptor kinetics | MECHANISMS_AUDIT.md row 7; src/wormemu/mech/receptors.py docstring | PLAN.md row 7; research/PORT_SOURCES_NEURAL.md N1 |
| Synapse/gap strength numbers (the biggest guessed block) | CATALOG.md ("biggest unknown blocks"); TO_A_REAL_WORM.md item 1 | BRAIN_PORT.md sections 4-5 (history of how the templates moved) |
| Gap junctions per innexin, rectification | MECHANISMS_AUDIT.md row 8; src/bioemu/jx_gap.py (Jaxley-side numerics, not used by the NEURON brain path) | PLAN.md row 8; BRAIN_PORT.md section 7, research/GAP_RECT_DIRECTION.md (direction/ratio) |
| Short-term plasticity, habituation, associative learning | MECHANISMS_AUDIT.md row 24; src/wormemu/mech/plasticity.py, learning.py docstrings | research/PORT_SOURCES_NEURAL.md N2/N3; scripts/worm/stp_fit.py (the one fitted value, cholinergic grain) |
| Sign/polarity rule for each synapse (transmitter vs CeNGEN vs Fenyves 2020) | ADOPTED.md (credits); BRAIN_PORT.md sections 4b-4c, 9 (why each rule was tried and what changed) | INTERFACE.md toggle table (receptor_sign) — **see staleness item 1 below** |
| Gap-junction numerical solve (Jaxley-only; fitting path) | GAPCHECK.md | PLAN.md section c.5 |

### 4. Neuromodulation (peptides, monoamines, sleep)

| Topic | Authority | Secondary |
|---|---|---|
| Neuropeptides and receptors | MECHANISMS_AUDIT.md row 9; src/wormemu/mech/neuromod.py docstring | PLAN.md row 9; research/NEUROPEPTIDES.md (what's measured vs inferred) |
| Monoamines | MECHANISMS_AUDIT.md row 10 | PLAN.md row 10; research/NEUROPEPTIDES.md |
| Sleep neurons (RIS, ALA) | MECHANISMS_AUDIT.md row 28 | research/NEUROPEPTIDES.md |
| Peptide-GPCR EC50 source numbers | CATALOG_AUDIT_INDEPENDENT.md (verified 9 of 15 sampled "measured" rows against Beets 2023 Table S6 directly) | MANIFEST.md section 4; `data/worm/structure/peptide_gpcr_pairs.csv` |

### 5. Senses (sensory transduction, glia, temperature)

| Topic | Authority | Secondary |
|---|---|---|
| Sensory transduction per modality | MECHANISMS_AUDIT.md row 17; src/wormemu/mech/senses_{base,chem,touch,proprio,cgmp}.py docstrings | PLAN.md row 17; research/PORT_SOURCES_NEURAL.md; scripts/worm/senses_checks.py |
| Glia | MECHANISMS_AUDIT.md row 11; src/wormemu/mech/glia.py docstring | PLAN.md row 11; research/PORT_SOURCES_ORGANS.md O5 |
| Temperature / Q10 | MECHANISMS_AUDIT.md row 25; src/wormemu/mech/temperature.py docstring | night/2026-11-06_wbody.md |
| Chemotaxis plate / scene numbers | research/CHEMOTAXIS_PLATE.md; src/wormemu/body/scene.py | HANDOFF_BODY.md (MB11) |

### 6. Organs (muscle, pharynx, intestine, egg-laying, metabolism, other cells)

| Topic | Authority | Secondary |
|---|---|---|
| Body-wall muscle + excitation-contraction | MECHANISMS_AUDIT.md row 12; src/wormemu/mech/muscle_bwm.py docstring | PLAN.md row 12; TO_A_REAL_WORM.md item 7 |
| Pharynx | MECHANISMS_AUDIT.md row 13; src/wormemu/mech/organs_pharynx.py docstring | PLAN.md row 13; TO_A_REAL_WORM.md item 9 |
| Intestine / defecation clock | MECHANISMS_AUDIT.md row 14; src/wormemu/mech/organs_intestine.py docstring | PLAN.md row 14 |
| Egg-laying | MECHANISMS_AUDIT.md row 15; src/wormemu/mech/organs_egglaying.py docstring | PLAN.md row 15 |
| Other non-neural cells (hypodermis, canal, coelomocytes) | MECHANISMS_AUDIT.md row 16; src/wormemu/mech/organs_other.py docstring | PLAN.md row 16 |
| Metabolism (DEB model) | MECHANISMS_AUDIT.md row 20; src/wormemu/mech/metabolism.py docstring | PLAN.md row 20 |
| Organ-level unit checks | scripts/worm/organs/check_*.py (one file per organ) | night/2026-11-06_worgans.md (bars written before running) |

### 7. Body (3D soft body)

| Topic | Authority | Secondary |
|---|---|---|
| Which body was adopted, and why (MetaWorm, not a rod, not Sibernetic yet) | HANDOFF_BODY.md ("Ben's direction... port the 3D MetaWorm/BAAIWorm body only, the rod is dropped"); ADOPTED.md "Body" table and "Not adopted (body)" | **PLAN.md DECISIONS item 4 and STRATEGY.md's "3D rod" line are superseded — see staleness item 2 below** |
| Body mechanics row (stiffness, damping) | MECHANISMS_AUDIT.md row 21; src/wormemu/body/layers.py (via docstring in scripts/worm/body_layers_check.py) | research/BODY.md, research/BODY_PARAMS.md (literature survey; the planar-rod numbers in BODY_PARAMS.md are archived) |
| Body test results (dead worm, prescribed gait, agar plate/film, solver dead zone) | BODY_TESTS.md | HANDOFF_BODY.md (summary + what's next) |
| Body ledger numbers | `data/worm/ledger/metaworm_parameters.csv`, built by `scripts/worm/build_metaworm_ledger.py` | HANDOFF_BODY.md |
| Sibernetic mechanisms to port later | research/SIBERNETIC_PORT.md | ADOPTED.md "Surveyed, to port (body)" |
| Candidate bodies considered and rejected | research/PORT_CANDIDATES.md | ADOPTED.md "Not adopted (body)" |

### 8. Environment (plate, fields, agar)

| Topic | Authority | Secondary |
|---|---|---|
| Environment fields (O2, CO2, salt, temperature gradient, food lawn) | MECHANISMS_AUDIT.md row 22; src/wormemu/body/environment.py (not separately docstring-read; see MECHANISMS_AUDIT row 22's file list) | PLAN.md row 22 |
| Agar / fluid drag numbers | HANDOFF_BODY.md (agar film, RFT constants); BODY_TESTS.md (A1/A2/A1f/A2f gates) | research/BODY_PARAMS.md |

### 9. Observation (what the instruments would see)

| Topic | Authority | Secondary |
|---|---|---|
| GCaMP, optogenetics, NeuroPAL, gait features | MECHANISMS_AUDIT.md row 23; src/wormemu/mech/observation.py docstring | PLAN.md row 23; scripts/worm/observation_checks.py |

### 10. Catalog and ranges (every number, with sources)

| Topic | Authority | Secondary |
|---|---|---|
| Every parameter, value used, label, source | CATALOG.md (generated; do not hand-edit) | `data/worm/model/{catalog,parameters}.csv`; `docs/worm/ledger.json`; viewer `viewer/worm/catalog.html` |
| Literature ranges (one row per bound) | `docs/worm/research/param_ranges.csv` | research/param_ranges_notes.md (reasoning per guessed row); research/RANGE_ENDS_LIT.md (narrowed ends with citations) |
| Independent spot-check of the catalog | CATALOG_AUDIT_INDEPENDENT.md (7 Nov; 50-row stratified sample, found 2 wrong, 2 minor, 4 unverifiable) | CATALOG.md "Independent audit (7 Nov)" section (where its findings were folded in) |
| Hidden constants (numbers in code not in the ledger) | `data/worm/catalog/hidden_constants.json`, `scripts/worm/hidden_constants.py` | CATALOG.md "Hidden constants" section |
| Catalog fills / what moved on 6-7 Nov | `data/worm/catalog/fills.csv` | MECHANISMS_AUDIT.md "What changed on 6-7 Nov"; CATALOG.md "What the catalog changed" section |
| Precision-needed column | CATALOG.md "Precision needed" section | STRATEGY.md "ledger format" (defines the column; not yet filled, no sensitivity pass run) |

### 11. Fitting (method, bar, held-out splits, results so far)

| Topic | Authority | Secondary |
|---|---|---|
| The fitting method and order of attack | STRATEGY.md | PLAN.md section c (architecture detail); research/ASTRA_REVIEW_2026-11-05.md (the review that produced several STRATEGY changes) |
| The pass bar ("within real variability" + a must-fail control) | PLAN.md DECISIONS item 2 | SCOREBOARD.md section 0 and 16 |
| Held-out data register (what's spent, what's sealed) | HANDOFF.md "Sealed and held-out data register" | PLAN.md section c.4 (the policy, not the register itself) |
| W0 spike (AIY) result | SPIKE.md | PLAN.md item 5 of "Verdict first" (summary) |
| W1 RIM/AFD fits | W1_RIM_AFD.md (pre-registered; M1 launched, full fits parked pending `kcnl2`) | HANDOFF.md "Parked" section |
| FIT1 (class-level synapse fit to Randi 2023) | **not in this checkout** — lives on branch `worktree-wormfit`, `docs/worm/FIT1.md` | HANDOFF.md "Read these" table and sealed register (cites it; results not yet folded into main) |
| Behaviour corpus / scoreboard | SCOREBOARD.md (adds FIT/HELD-OUT split and protocol columns) | STATE_OF_THE_ART.md section 3 (the original ~90-item corpus SCOREBOARD is built from; explicitly "research note, not canon") |
| What's left to do a real worm, ranked | TO_A_REAL_WORM.md | MECHANISMS_AUDIT.md "Never checked" section (the raw list TO_A_REAL_WORM ranks) |
| Gap-junction numerics for gradient fitting | GAPCHECK.md | PLAN.md section c.5 |
| Genome-wide perturbation data as a future held-out corpus | research/PERTURBATION_CORPUS.md | SCOREBOARD.md section 15 (the mutants actually scheduled) |

### 12. Decisions (Ben's calls and the Director's adopted defaults)

| Topic | Authority | Secondary |
|---|---|---|
| The ten original binding answers that started the project | `~/director/goals.md` (fly-emulation section) — **outside this repo, not auditable here** | PLAN.md references them throughout; STRATEGY.md line 3 |
| Five numbered DECISIONS from the 5 Nov spike night | PLAN.md "DECISIONS" section | STRATEGY.md (decision 2's bar restated); ADOPTED.md |
| Body: port MetaWorm, drop the rod | HANDOFF_BODY.md top ("Ben's direction... 15:05-15:40") | ADOPTED.md "Not adopted (body)"; **supersedes PLAN.md DECISIONS item 4 — see staleness item 2** |
| wiring=cook adopted as default | BRAIN_PORT.md section 3 ("Adopted: wiring=cook is the default") | INTERFACE.md toggle table |
| ImplicitGap / GMRES adopted for gap-junction solving | GAPCHECK.md (two separate adoption gates) | PLAN.md section c.5 |
| Roberts 2016 AVA-AVB sign correction adopted | BRAIN_PORT.md section 9 | — |
| muscle_active, gap_rectification: implemented but stay off by default | BRAIN_PORT.md sections 6-7 | MECHANISMS_AUDIT.md row 12 (muscle_active off), INTERFACE.md toggle table |
| Build every mechanism first, THEN fit (revised order) | STRATEGY.md move 1 | PLAN.md's original staged W0-W9 roadmap (section e) — **now superseded in practice, see staleness item 3** |
| Astra review changes (measurement-as-model, disagreement search, etc.) | STRATEGY.md "Changes from the Astra review" | research/ASTRA_REVIEW_2026-11-05.md (full text) |

### 13. Tools (engines, scripts, viewer)

| Topic | Authority | Secondary |
|---|---|---|
| Engine adoption verdicts (Jaxley, NEURON, Arbor, c302, Sibernetic, BAAIWorm) | PLAN.md section b | research/adoption_tests.md (raw install/run tests) |
| The brain/body interface contract | INTERFACE.md | src/wormemu/interface.py (code form; docstring points back to INTERFACE.md as authority) |
| How to run and see the model (commands) | HANDOFF.md "How to run and see it" | HANDOFF_BODY.md (body-specific commands, slightly stale — see below) |
| The ledger builder | `scripts/worm/build_ledger.py` (brain+organs+body), `scripts/worm/build_metaworm_ledger.py` (body-only numbers) | src/bioemu/ledger.py docstring |
| Viewer: what each tab shows | `viewer/worm/index.html`: tabs **Wiring** (connectome diagram), **State** (per-neuron voltage/Ca readout), **Mechanisms** (toggle list), **Catalog** (condensed parameter table, links to the full one), **Run** (run metadata); 3D body panel + kymograph (muscle activation strip) always visible | `viewer/worm/catalog.html` (the full audited catalog, one page, `random row` button for spot audits) |
| Viewer data builders | `scripts/worm/build_viewer_data.py` (run frames, gitignored output), `scripts/worm/export_viewer_graph.py` (wiring graph) | ADOPTED.md "Viewer" table (three.js, data sources, licences) |
| Unit-check scripts, one per mechanism row | scripts/worm/{channels,receptor,stp,noise,chnoise,neuromod,slow,senses,observation}_unit_check.py, ca_volume_check.py, capool_unit_check.py, cells_passive_check.py, scripts/worm/organs/check_*.py | MECHANISMS_AUDIT.md "Checked" column cites each one; night files give the bars as pre-registered |
| Running a check at the ledger's current values instead of the code template | `scripts/worm/at_ledger.py` | MECHANISMS_AUDIT.md's note under the table (why most checks are stale relative to the 7 Nov catalog) |
| Fitting scripts | `scripts/worm/fit_aiy.py` (W0), `scripts/worm/fit_w1.py` (W1 RIM/AFD) | SPIKE.md, W1_RIM_AFD.md |
| External source projects ported | BAAIWorm (`third_party/baaiworm/`), c302 (`third_party/c302/`), MetaWorm (`third_party/metaworm/`), Nicoletti 2024 channels (`src/wormemu/nicoletti.py`) | ADOPTED.md (the full credit/licence table for all of them) |

### 14. Data on disk

| Topic | Authority | Secondary |
|---|---|---|
| What's on backhouse (`~/worm-data/`), sizes, licences | MANIFEST.md | HANDOFF.md "Data" bullet (pointer only) |
| Derived structure tables in-repo | `data/worm/structure/` (listed in MANIFEST.md section 9) | — |
| Brain run outputs | `data/worm/brain_runs/<run>/` (summaries in git, `.npz` traces not) | BRAIN_PORT.md, GAPCHECK.md (cite specific run directories) |
| Body run outputs | `data/worm/body_runs/` | BODY_TESTS.md, HANDOFF_BODY.md |
| Catalog working files | `data/worm/catalog/` (fills.csv, hidden_constants.json, link_check.csv, quote_check.csv, slots.csv, audit_notes.csv, independent_audit_actions.csv) | CATALOG.md (reads these during generation) |
| Gap-junction check logs | `data/worm/gapcheck/` | GAPCHECK.md |
| Spike/W1 fit outputs | `data/worm/spike/fit1/`, `data/worm/kcnl1/`, `data/worm/port2/` | SPIKE.md, W1_RIM_AFD.md |
| Model-level ledger (pre-catalog) | `data/worm/model/{mechanisms.yaml,parameters.csv,catalog.csv}` | CATALOG.md says it is generated from these |
| Older per-mechanism ledger | `data/worm/ledger/{metaworm_mechanisms.json,metaworm_parameters.csv}` | HANDOFF_BODY.md |
| ephys source data (not ours) | `data/worm/ephys/naudin2022_liu_aiy_rim_afd/` | MANIFEST.md ("another assistant's folder... left untouched") |

---

## B. Stale / Contradictory Items

1. **INTERFACE.md's toggle table silently disagrees with what every closed-loop run actually uses.**
   - Stale line: `docs/worm/INTERFACE.md:109` — `` `receptor_sign` | off | on = sign per pair from Fenyves et al. 2020's published polarity... ``. Same table also lists `innexin_identity` (line 110) and `expression_map` (line 112) as off by default.
   - What is true now: `src/wormemu/brain.py` line 95: `TEMPLATE_ON = {"receptor_sign": "on", "innexin_identity": "on", "expression_map": "on"}`. Every template worm (`sample_worm(None)`, which is what every closed loop in BRAIN_PORT.md section 8-9, HANDOFF_BODY.md, and the v1_everything run uses) has all three ON, overriding the table's "off" defaults. MECHANISMS_AUDIT.md row 7 confirms: "receptor_sign on (`TEMPLATE_ON`)".
   - Fix: add one line to INTERFACE.md's toggle table (or a note above it) saying the template worm built by `sample_worm()` sets `receptor_sign`, `innexin_identity`, `expression_map` to "on" via `TEMPLATE_ON`, overriding the registry defaults shown. A reader who only reads INTERFACE.md (the brain/body contract, the natural place to look up "is sign-correction on") will get the wrong answer for every actual run.

2. **PLAN.md's body DECISION and STRATEGY.md's "first physics body" are superseded by Ben's direct order, recorded only in HANDOFF_BODY.md.**
   - Stale line: `docs/worm/PLAN.md:329-331` — "**The 3D body.** *Decided (default):* spend about one session trying a Windows-native Sibernetic build with NVIDIA OpenCL; if it fails, write the 3D body in JAX (gradients come free), validated against Sibernetic's published results."
   - Stale line: `docs/worm/STRATEGY.md:43` — "a 3D rod with validated low-Reynolds drag is the first physics body; a full 3D/fluid body must show a scientific benefit for its cost."
   - What is true now: `docs/worm/HANDOFF_BODY.md:8-9` — "Ben's direction (via the Director, 15:05-15:40): port open-source bodies, not our own physics; the 3D MetaWorm/BAAIWorm body only (the rod is dropped)". `docs/worm/ADOPTED.md` "Not adopted (body)" section confirms: "Our own planar rod (archived, `archive/worm/rod_own/`): written by us, not a port; dropped on Ben's direction (5 Nov 15:05)." Neither Sibernetic nor a from-scratch JAX body was ever built; MetaWorm (BAAIWorm's own 3D FEM body) was ported directly and is what every body run uses today.
   - Fix: add a one-line "superseded 5 Nov 15:05, see HANDOFF_BODY.md" note at PLAN.md's DECISIONS item 4 and at STRATEGY.md's body bullet, pointing to ADOPTED.md's body table as the live answer. Do not delete the history (it explains why the rod work in BODY_TESTS.md's early sections was later archived).

3. **PLAN.md's staged roadmap (section e, W0 through W9) was abandoned in practice and nothing in the live docs says so.**
   - Stale line: `docs/worm/PLAN.md:292-309`, e.g. row "**W1 cell library**... RIM and AFD each pass the same three-part bar on their own held-out steps and population I-V" and "**W2 motor system and rod body**... blind prediction of bend frequency...".
   - What is true now: `docs/worm/STRATEGY.md:12` revises the order on 5-6 Nov to "build every mechanism first, then fit real data" — i.e., not W1 (cells) then W2 (motor) then W3 (head circuit) etc. in sequence. What actually happened (MECHANISMS_AUDIT.md, HANDOFF.md) is that all 28 mechanism rows were built and turned on together by 7 Nov, while W1's own target (RIM and AFD fits) never finished: `docs/worm/HANDOFF.md:47` — "**W1 (Jaxley RIM and AFD fits).** `w1m1` outputs sit uncollected... The held fits wait for `kcnl2`". So the roadmap's stage order and its claim that W1 gates W2 are both contradicted by what the project actually did.
   - Fix: mark PLAN.md section e "superseded by STRATEGY.md move 1 (5-6 Nov); kept for history" in a one-line header note, and point to MECHANISMS_AUDIT.md for what is actually built, and TO_A_REAL_WORM.md for what is ranked to do next (which replaces the W-stage ordering).

4. **STRATEGY.md contradicts itself within one sentence on whether the synthetic-twin control is required.**
   - Stale/self-contradicting line: `docs/worm/STRATEGY.md:12` — opens "AMENDED 6 Nov: Ben, asked whether the synthetic-twin control below is needed: 'I don't know, I don't think we need that at all.' So it is NOT a required control; held-out perturbation tests remain the bar." Then, three sentences later in the same bullet: "This is a **must-pass control**, the mirror of the must-fail controls, run alongside the real fits (about 2x compute), not before them."
   - What is true now: the amendment (Ben's own words) says it is not required; the rest of the paragraph was written before the amendment and was never edited down to match it.
   - Fix: edit the bullet so the "must-pass control" and "Pass:" sentences are explicitly marked as the pre-amendment plan, kept only as a candidate method, not a requirement. One or two words ("if run" / "optional") would resolve this without deleting the content.

5. **BRAIN_PORT.md reads as a live "current defaults" document but its specific numbers are two ledger generations out of date.**
   - Stale line: `docs/worm/BRAIN_PORT.md:416` — "**Result (D8b...)**: ... D8b is the default configuration from here on." And section 4c-9's specific values (per-EM synapse 0.447 nS, excitatory reversal +0.5 mV, decay k 0.117/ms, etc.) are presented as the ledger's state as of 5 Nov.
   - What is true now: `docs/worm/MECHANISMS_AUDIT.md:66-69` — "The catalog merge (7b49648) moved 42 Specs in 12 modules (18 receptor values, 12 amine and stirring values, 2 SLO noise conductances, the GABA STP k0, and one each in senses_chem, senses_touch, senses_proprio, egg-laying, glia, pumps and 3 GCaMP half-decays)." The current authority for "what value does the brain actually run" is CATALOG.md / `data/worm/model/parameters.csv`, not BRAIN_PORT.md's narrative.
   - Fix: this doesn't need line edits (the history and diagnosis in BRAIN_PORT.md are still correct and valuable — the saturation diagnosis, the Roberts 2016 sign fix, the rhythm screen). Add one header note: "Numeric values quoted below are as of 5 Nov; for the value the brain runs today, see CATALOG.md." This is the single biggest "two sources of truth" risk in the whole knowledge base, because BRAIN_PORT.md is 640 lines of detailed, dated, pre-registered experiments that look authoritative.

6. **HANDOFF.md points to FIT1.md, which does not exist in this checkout.**
   - Not exactly stale, but a findability gap: `docs/worm/HANDOFF.md:28` — "The first fit (pre-registered) | `docs/worm/FIT1.md` on branch `worktree-wormfit` (`.claude/worktrees/wormfit`)". A reader grepping `docs/worm/` in the main checkout will not find this file (confirmed: not present in `find docs/worm -type f`).
   - Fix: no content fix needed (the file genuinely lives on another branch/worktree), but the KNOWLEDGE_INDEX entry above (section 11) now says this explicitly, and HANDOFF.md's own line could add ", not in this checkout" to save the next reader a search.

7. **STATE_OF_THE_ART.md and SCOREBOARD.md explicitly disclaim canon status, but are the only place several facts live.**
   - Not a contradiction, but worth flagging: STATE_OF_THE_ART.md's own header says "Research note, not canon... Nothing here has been fit or used in any model." SCOREBOARD.md's header says "Canon (corpus item list, mechanism ledger, loss table, held-out policy in PLAN c.4) is treated as locked and is not reopened here." Yet SCOREBOARD.md is the only place the FIT/HELD-OUT split per corpus item lives, and STATE_OF_THE_ART.md is the only place several citations (dataset URLs, paper DOIs) live. This is fine as designed, but a reader following "is this canon" literally could wrongly discount real information. No fix needed beyond noting it in the proposed structure below (treat both as reference/working documents, not status documents).

---

## C. Duplicates (same fact maintained in more than one place — risk of drift)

| Fact | Where it is repeated | Proposed single owner |
|---|---|---|
| Mechanism-ledger row descriptions (rows 1-23) | PLAN.md section a (original, with data sources and "needed for"); MECHANISMS_AUDIT.md rows 1-23 (current status); SCOREBOARD.md "Layers" column (cites the same row numbers again) | **MECHANISMS_AUDIT.md** for current status/category; PLAN.md section a stays as the one-time design rationale (data source, cost class) and should not be re-edited when status changes |
| Speed cap (100x real time full model / 10x fitting) | PLAN.md section d.1; STRATEGY.md "Speed bars"; research/BODY.md (which also carries a correction notice about its own earlier misreading of this same number) | **PLAN.md section d.1** (the original binding statement); STRATEGY.md's line should say "see PLAN.md d.1" instead of restating the numbers; research/BODY.md's correction note should be folded in or removed once BODY.md is archived (see D) |
| Whether `wiring=cook` / `receptor_sign` / etc. are on by default | INTERFACE.md toggle table; BRAIN_PORT.md narrative; src/wormemu/brain.py `TEMPLATE_ON` and the registry defaults | **src/wormemu/brain.py` (`TEMPLATE_ON`) and `data/worm/model/mechanisms.yaml`** are the actual source of truth (code); INTERFACE.md should be corrected per staleness item 1 and then treated as the documented mirror of the code |
| Per-mechanism numeric values (template vs ledger) | BRAIN_PORT.md (many specific numbers, 5 Nov state); GAPCHECK.md (bench numbers); CATALOG.md (current, generated) | **CATALOG.md / `data/worm/model/parameters.csv`** only; every other file should describe values as "as of &lt;date&gt;" and link to CATALOG.md for the live number, never repeat it as if current |
| Behaviour corpus (the ~90-100 item list) | STATE_OF_THE_ART.md section 3 (original, with full citations); SCOREBOARD.md (same items, FIT/HELD-OUT column added); PLAN.md section c.2/c.4 refers to subsets by number | **STATE_OF_THE_ART.md section 3** owns the item list and citations (do not re-copy the citation column elsewhere); **SCOREBOARD.md** owns the split/protocol columns and should reference item numbers only, which it already mostly does |
| Adoption/credit for each external project (BAAIWorm, c302, MetaWorm, Nicoletti 2024) | ADOPTED.md (the full table, intended as the single credit ledger); PLAN.md section b (adoption verdicts, overlapping content); BRAIN_PORT.md/HANDOFF_BODY.md narrative repeats some of the same licence/version facts in prose | **ADOPTED.md** as the only credit/licence table; PLAN.md section b should keep only the *verdict and evidence* (install/run/fidelity/speed), not re-state licence terms that ADOPTED.md already owns |
| What data is on backhouse, sizes and licences | MANIFEST.md (detailed); SCOREBOARD.md section 19 (a condensed re-listing with "feeds scoreboard entries" added); HANDOFF.md "Data" bullet (another condensed pointer) | **MANIFEST.md** for size/licence/provenance; SCOREBOARD.md section 19 should keep only its own added column (which scoreboard entries each dataset feeds) and link to MANIFEST.md instead of repeating size/format/licence |
| Saturation / rhythm diagnosis history | BRAIN_PORT.md sections 4-9 (detailed); HANDOFF.md "Parked" section (one-line summary); TO_A_REAL_WORM.md (ranked-impact summary) | **BRAIN_PORT.md** owns the detailed history (it is not asked to change); HANDOFF.md and TO_A_REAL_WORM.md should keep only their one-line summaries, which they already do, as long as BRAIN_PORT.md gets the "values are dated" header note from staleness item 5 |

---

## D. Proposed Structure

**Keep as live authorities (edit these when something changes):**
- `docs/worm/HANDOFF.md` — current state, rewritten each session.
- `docs/worm/MECHANISMS_AUDIT.md` — what the code does, row by row, strict.
- `docs/worm/CATALOG.md` (+ `data/worm/model/catalog.csv`, `parameters.csv`) — every number.
- `docs/worm/TO_A_REAL_WORM.md` — ranked gap list, rewritten as items close.
- `docs/worm/STRATEGY.md` — method and order of attack (fix the item-4 self-contradiction, item B.4 above).
- `docs/worm/SCOREBOARD.md` — the held-out test plan, keyed to STATE_OF_THE_ART.md's corpus numbers.
- `docs/worm/INTERFACE.md` — the brain/body contract (fix the toggle-defaults gap, item B.1).
- `docs/worm/ADOPTED.md` — the one credit/licence ledger for every external source.
- `docs/worm/MANIFEST.md` — the one data-provenance ledger.
- `docs/worm/CHANNEL_SLOTS.md`, `docs/worm/research/GENES_TO_PHYSIOLOGY.md`, `docs/worm/research/NEUROPEPTIDES.md`, `docs/worm/research/PORT_SOURCES_{NEURAL,ORGANS}.md`, `docs/worm/research/PERTURBATION_CORPUS.md` — reference research notes, explicitly labelled "not canon" and kept that way; these are fine as secondary reading, not status reports.

**Mark superseded (add a one-line header note; do not delete; the diagnosis inside remains useful history):**
- `docs/worm/BRAIN_PORT.md` — add "values as of 5 Nov; see CATALOG.md for current numbers" (item B.5).
- `docs/worm/GAPCHECK.md` — add "numerical adoption record; the Jaxley gap-junction path is used for fitting only, not by the NEURON brain in brain.py" (clarifies scope, since a reader could think it governs the live brain).
- `docs/worm/SPIKE.md`, `docs/worm/W1_RIM_AFD.md` — add "W0/W1 pre-registration and result; superseded as the project's current method by STRATEGY.md's revised order (build every mechanism first)" — keep as the historical record of the one completed held-out test (SPIKE) and the parked one (W1).
- `docs/worm/PLAN.md` — add "section e's staged roadmap (W0-W9) was not followed after 5-6 Nov; see STRATEGY.md move 1 and HANDOFF.md for what was actually built. DECISIONS item 4 (3D body) was superseded by Ben's order, see HANDOFF_BODY.md and ADOPTED.md" — keep sections a-d as the original design rationale, which is still accurate.
- `docs/worm/STATE_OF_THE_ART.md` — no content change needed; it already says "research note, not canon" in its own header. Just link it from the new README as "background survey", not as a status file.
- `docs/worm/HANDOFF_BODY.md` — this is a worktree handoff (`wormbody`) that predates the merge into main; add "merged into main; see HANDOFF.md for current state" at the top, since right now it reads as live but duplicates ground HANDOFF.md now owns.
- `docs/worm/research/BODY.md` — already carries its own correction notice; fold that correction into PLAN.md d.1 / STRATEGY.md per item C (speed cap duplicate) and then mark this file archived.
- `docs/worm/CATALOG_AUDIT_INDEPENDENT.md` — this is a point-in-time audit, already folded into CATALOG.md's "Independent audit (7 Nov)" section. Mark it "folded into CATALOG.md; kept as the detailed record" rather than a thing to consult first.

**Archive candidates (content fully superseded and not needed as history for an active decision):**
- None of the files in scope are safe to fully archive yet — even the "superseded" ones above carry diagnosis or pre-registration detail (e.g., BRAIN_PORT.md's saturation diagnosis) that TO_A_REAL_WORM.md's ranked list still depends on for "why" context. Recommend revisiting archival once FIT1 lands and the saturation/rhythm question is resolved one way or the other.

**One top-level entry point: `docs/worm/README.md` (new, does not exist yet).**
Proposed short content (a router, not a summary):
1. One paragraph: what this is, and the one rule ("MECHANISMS_AUDIT.md + CATALOG.md + HANDOFF.md are the live truth; everything else is either a research note or a dated history record").
2. A table: question -> file. E.g. "What does the code actually do for row N?" -> MECHANISMS_AUDIT.md. "What's this number and where did it come from?" -> CATALOG.md. "What should I do next?" -> TO_A_REAL_WORM.md. "How do I run it / see it?" -> HANDOFF.md "How to run and see it". "What's on disk?" -> MANIFEST.md (data) / this file's section A.14 (repo layout). "Why does X toggle exist / what's the default?" -> INTERFACE.md, then `src/wormemu/brain.py`. "Has this been tried before by someone else?" -> STATE_OF_THE_ART.md.
3. A link to this file, `KNOWLEDGE_INDEX.md`, as "the full topic index, staleness list and duplicate list, for anyone doing a deeper audit."
4. A one-line pointer to `docs/HANDOFF.md` (repo root) for the fly's parallel status (paused).

This keeps the router under 40 lines, so it is actually read, and leaves KNOWLEDGE_INDEX.md as the longer reference for anyone auditing rather than just working.
