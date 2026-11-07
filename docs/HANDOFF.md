# Handoff: current state

**Rewritten each session; do not append.** State at 2026-11-07 01:18 CST, written by wfinal at the end of the worm
night push (6-7 Nov; Director session relays Ben). The fly is paused (its handoff: `docs/archive/HANDOFF_fly_2026-11-04.md`).

## Where the worm stands

- **What exists.** A whole-worm model on main with every PLAN.md row running and on by default. That is 23 mechanism modules (`src/wormemu/mech/`), the 302-neuron NEURON brain on Cook 2019 wiring (`src/wormemu/brain.py`), and MetaWorm's 3D body on an agar plate.
  - Strict audit: **13 rows full, 15 lumped, 0 spec only, 0 missing** (main category), and 11 rows fail a unit check.
  - Catalog: 1,483 rows and 91,253 numbers. 9,246 of the 20,252 physiology numbers are guessed (46%, derived), 7,753 of them in four per-pair connection blocks.
- **The measured result.** `v1_everything` (7 Nov, 5b7e141) is a 20 s closed loop with every module on, on the standard plate.
  - It ran finite at **11.85 s wall per bio s** on the Mac. That is inside STRATEGY's 100x cap for the full model.
  - At the end, 16% of neurons were above -20 mV, mean body-wall activation was 0.037, and the pharynx had 0 pumps.
  - The worm holds a shallow one-sided bend and drifts 0.61 body lengths; **it does not crawl**. That is expected: no behaviour has been fitted, by Ben's rule.
- **Next, and why.** Read FIT1's held-out result once it exists. FIT1 is the class-level synapse fit to Randi 2023, pre-registered in wfit's worktree. Synapse and gap strengths are the largest guessed block (item 1 of TO_A_REAL_WORM). Then build the expression-to-physiology map for excitability (item 2): FIT1's declared limit is that the template's responses are too small for the fit to reach the data except near its bounds.
- **Blocked or Ben's call.**
  - The Nicoletti 2024 repo has no LICENSE file, so it is Ben's call before any public release.
  - Lab measurements: TO_A_REAL_WORM's L items.
  - The 478 `mech.channels` and 9 `mech.cells_passive` Specs are not in the ledger yet (asked of wcatalog).

## Read these

| What | Where |
|---|---|
| What the code does, row by row (strict) | `docs/worm/MECHANISMS_AUDIT.md` |
| Every number, labelled, with sources | `docs/worm/CATALOG.md`; rows in `data/worm/model/catalog.csv`, `parameters.csv`; browser `viewer/worm/catalog.html` |
| What has to change for a real worm, ranked | `docs/worm/TO_A_REAL_WORM.md` |
| The first fit (pre-registered) | `docs/worm/FIT1.md` on branch `worktree-wormfit` (`.claude/worktrees/wormfit`) |
| Order of attack and the bar | `docs/worm/STRATEGY.md`, `docs/worm/PLAN.md`, `docs/worm/SCOREBOARD.md` |
| The night's work, per worker, with Open lists | `docs/worm/night/2026-11-06_{wbrain,worgans,wbody,wneuron,wcatalog}.md`, `2026-11-07_wfinal.md` |
| Body, viewer, driver | `docs/worm/HANDOFF_BODY.md`, `docs/worm/INTERFACE.md` |

## How to run and see it

- **Tests.** `PYTHONPATH=src .venv/bin/python -m pytest tests/test_worm_*.py`: 97 pass (7 Nov 01:03, measured).
- **The full loop.** `python3 ~/director/harness/slot.py run --label "worm: ..." -- .venv/bin/python scripts/worm/wbody_loop_check.py 20 <label> --modules=observation --env=standard`. Outputs go to `runs/worm/night_wbody/`. It takes about 4 min of wall for 20 bio s.
- **The viewer.**
  - Build: `.venv/bin/python scripts/worm/build_viewer_data.py --src=runs/worm/night_wbody <label> --first`. `--first` puts the run first, so the viewer opens on it.
  - Serve: `cd viewer/worm && ../../.venv/bin/python serve.py 8793`, then open http://127.0.0.1:8793/.
  - The run data under `viewer/worm/runs/` is git-ignored.
- **The MP4.** `runs/worm/media/v1_everything.mp4` (20 s, 601 frames), with contact sheet `v1_everything_sheet.png`. Re-record with `record_viewer_mp4.py <label> <port>` while the server is up.
- **Unit checks at the values the brain runs.** The check scripts read code templates, but 42 Specs now have different ledger values. Use `PYTHONPATH=src .venv/bin/python scripts/worm/at_ledger.py scripts/worm/<check>.py`.
- **Data.** On backhouse under `~/worm-data/` (`docs/worm/MANIFEST.md`): Cook 2019, Witvliet 2021, CeNGEN, the peptide connectome, Randi 2023, Atanas 2023, morphologies, plus Naudin 2022's AIY/RIM/AFD recordings (another assistant's folder). Each worker's night runs are in `~/worm-night/<worker>/`.

## Parked

- **W1 (Jaxley RIM and AFD fits).** `w1m1` outputs sit uncollected in `~/worm-spike/runs/w1m1/` on backhouse. The held fits wait for `kcnl2`; see `docs/worm/W1_RIM_AFD.md`. The RIM and AFD held-out sweeps are unspent (register below).
- **Rhythm and crawling.** Not chased, by Ben's rule ("it is SUPPOSED to not work yet"). Saturation and rhythm notes are in the night files' Open lists.

## Sealed and held-out data register

### Worm

| Data | Status | Rule |
|---|---|---|
| Naudin 2022 AIY current clamp (`Fig1A_AIY_CC.txt`, one cell), steps -15, -5, +5, +15, +25, +35 pA | seen (W0 spike training set) | training only |
| Naudin 2022 AIY current clamp, steps -10, 0, +10, +20, +30 pA | **spent** (W0 spike `fit1`, 5 Nov; also scored first on the 2-iteration pipeline test while `fit1` ran with frozen settings) | consistency only from now on; the same cell, so never a cross-cell test |
| Naudin 2022 AIY population voltage-clamp I-V (n 5-7; steady state and peak; `Fig1_IVcurves_AFD_RIM_AIY.xlsx`) | **spent** (W0 spike `fit1`; pipeline test before it). The table was read while writing the pre-registration (n per voltage, windows) | consistency only; the 2 SD band does not discriminate (F-W0-6) |
| Naudin 2022 RIM and AFD current clamp and I-V (same deposit) | file headers and the voltage-clamp `n` columns viewed. **Training sweeps 0, 2, 4, 6, 8, 10 now in use** (5 Nov 02:14 on: `fit_w1.py` smoke test `w1smoke`, then M1 run `w1m1`; training RMSEs printed). The held-out sweeps are dropped at load (`Vd = Vd[TRAIN]`) and no held-out or voltage-clamp value has been printed, plotted or used. The AIY loader read the whole I-V sheet into memory but used only AIY columns | **held out for W1**, split and bars pre-registered in `docs/worm/W1_RIM_AFD.md` (5 Nov 01:13): train sweeps 0, 2, 4, 6, 8, 10; held out 1, 3, 5, 7, 9 and all voltage clamp. Score once, all models together (see Next) |
| Nicoletti 2024 published AIY and RIM models (densities, kinetics, code) | seen; kinetics SET the channel library (22 channels); AIY densities SET one start of the spike fit and its baseline; RIM densities used as a port-check configuration (`port2`, 5 Nov) and, as registered, SET one start of `w1rim1` and its published-model baseline | can't validate the library |
| Randi 2023 functional atlas; Atanas 2023 whole-brain data; Witvliet 2021; Cook 2019; CeNGEN; the neuropeptide connectome | downloaded (`~/worm-data`, MANIFEST); Cook 2019 used as structure (the brain's default wiring since 5 Nov, the ledger's pair counts), CeNGEN as expression (channel presence, receptor signs, innexins, modulator matrices) and Fenyves 2020's sign predictions as structure (`receptor_sign`); no activity data read | seed the held-out split (PLAN c.4) before the first fit that uses them |
| Closed-loop engineering runs (body worker, 5 Nov: seed 0 and `sample_worm(None)` + receptor_sign, 3-10 s; brain worker BRAIN_PORT C1, C2, the section 8 screen, 10 runs of 5 s, and section 9, 2 runs of 20 s) | engineering output only: posture, centroid, activations and voltages seen; the section 8 rhythm rule is an internal screen, nothing compared to a recording or scored against behaviour | not a behaviour test; a crawling check needs its own pre-registered bar |
| Range-end literature (`docs/worm/research/RANGE_ENDS_LIT.md`: Richmond and Jorgensen 1999; Lindsay et al. 2011; and the sources it lists for the other range ends) | read as literature, not held-out data; Richmond and Jorgensen 1999 and Lindsay 2011 SET the excitatory reversal range (BRAIN_PORT 6a) | can't validate the excitatory reversal |
| Roberts et al. 2016 eLife 5:e12572 (AVA-AVB and ASH-AVB photoactivation plus patch, Fig. 6B-D and 9C-D) | read as literature; SETS the 9 measured signs in `syn_sign_receptor` (BRAIN_PORT 9) | can't validate those signs; the section 9 runs are engineering output, nothing compared to a recording |
| Liu, Chen, Mailler and Wang 2017 Nat Commun 8:14818 (VA5 to AVA junction rectification direction) | SET the `gap_rectification` direction | can't validate it |
| c302 C2 muscle model (Gleeson et al.; `third_party/c302`) | SETS the `muscle_active` membrane (published fit) | can't validate the muscle |
| Randi 2023 wild-type atlas, FIT1 training split (137 stimulated neurons, 18,835 terms; seed 20261106) | **training** (FIT1, wfit): noise model, training medians and trial-run losses seen. Before the split, aggregate statistics over all pairs were computed (no per-pair value used) | training only |
| Randi 2023 wild-type atlas, FIT1 held-out split (34 stimulated neurons, 4,719 terms; `~/worm-night/wfit/fit1/sealed/wt_heldout.npz`, mode 400) | **sealed, unread** | opened once, by `fit1_eval.py` (committed before it runs) |
| Randi 2023 unc-31 atlas (108 stimulated neurons, 9,011 terms; `sealed/unc31.npz`) | **sealed, unread** | FIT1 section 7, the peptide-layer test, once |
| Liu et al. 2009 PNAS 106:10823 NMJ trains | 1 and 5 Hz: SET the cholinergic STP values (row 24, fitted by us). 0.2 Hz tau and the 10/20 Hz bars: **spent**, seen three times during development (wbrain night file) | consistency only; row 24 needs a fresh held-out set |
| Unit-check bars of 6 Nov (each module's check script; listed per row in `docs/worm/MECHANISMS_AUDIT.md`) | read as literature; scored at the code templates (6 Nov) and four re-scored at the ledger values (wfinal, 7 Nov) | consistency only; where the same source set a value, it can't validate it |
| Catalog fills (wcatalog, `data/worm/catalog/fills.csv`, 6-7 Nov) | SET the ledger values they fill, including 42 module Specs whose ledger value now differs from the code template (e.g. GluCl Hill 1.5, touch channels 113) | can't validate those values |
| Closed loops of 6-7 Nov (builders' everything-on loops; wfinal `v1_everything`, 20 s) | engineering output only: posture, voltages and module states seen; nothing compared with a recording | none |
| Behaviour corpus (`docs/worm/STATE_OF_THE_ART.md`, about 90 items) | read as a list of items; no outcome scored | seal about a third by seed before any behaviour fit (PLAN c.4, W2) |

### Fly (paused)

The fly's register is unchanged and lives in `docs/archive/HANDOFF_fly_2026-11-04.md`, section "Sealed and held-out
data register" (it was carried here verbatim until 7 Nov; diffed identical before removal).
