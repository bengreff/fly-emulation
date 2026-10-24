# Handoff: current state

**Rewritten each session; do not append.** State as of Sat 24 October 2026, 02:14 CDT, session 23 (third context of the night; main at 617a790 plus this commit; base m10f5 from fly2).
- **Brief (Director, 24 Oct 00:55 entry in `/Users/ben/director/decisions/fly.md`):** about 5 % of the week left tonight; park at a clean commit by 05:30 with HANDOFF current. The seven required-level questions are not Ben's: fidelity is an engineering call he delegated, with a bias toward simulating more. Work the path-to-done table in rank order: (1) score m10f9b and the m10f6/7/8 smokes; (2) source graded_rmax; (3) the next rows. A row is done only on evidence.
- **Director rulings (00:55), now applied in the path-to-done column:**
  - Derived constants beat declared ones. A row is never done by declaring it out of scope.
  - S5: a lumped heat balance near ambient at rest, checked against a cited measurement.
  - B27: well-mixed only with a cited circulation or mixing time, and only for slower processes.
  - S7: a constant healthy state is OK. S8: a naive-male constant is OK, stated as such.
  - N27: class level where no type-specific data exist, with the search documented.
  - N33: in scope. Build at least astrocytic Eaat1/GAT uptake and its effect on synaptic time course at class level. The ensheathing-glia sleep roles tie to N25.
  - N28: a cited measured Q10 range is enough when a documented search finds no independent check in open text.
  - N1: graded_rmax must be sourced (fly first; other insects labelled derived).
- **Goal:** a **mechanism-complete fly**. "Done" means built at the required fidelity, ON in `m10f` with values inside a cited measured range, and passing a unit check against a measurement where one exists (where none exists, built and ON counts).
- **Heavy runs:** backhouse for multi-run sets (at most 4 threads per job, queue above load 24, nohup, done-files); on the Mac, through `python3 ~/director/harness/slot.py run --label "fly: <what>" -- <cmd>` under nohup with done-files.
- **My rows (fly):** neuromodulation, hormones, internal state, metabolism, N1-N4 intrinsics and N27/N33 glia: 20 rows. **2 done as ruled constants (S7, S8), 0 done on evidence.**
- **fly2:** plasticity, synaptic dynamics, sensors, body, plus N13, N14, N18. Stay out of those, and out of `~/fly2_mc` and the flyapp worktree.

## Report for Ben (s23)
**Rows moved: S7 and S8 done as ruled constants (no evidence check exists); 0 rows done on evidence yet.** The first evidence-based done rows wait on adopting m10f9b or m10f10, whose 60 s smokes are running. S5 is built and passes its measurement check.

- **S5 body temperature (built, neutral off; DECISIONS 24 Oct 00:51, 00:57; F-S23-9).**
  - Lumped heat balance: C T_b' = P_met − P_evap − G (T_b − T_air), with G = 2π k_air D + 4εσT³πD² and D = (6m/πρ)^(1/3). The values are sourced (mass 0.505 mg, ρ 1.07, c_p 3.5 J/g/K, ε 0.95). The resting excess is derived at **+0.07 K**. The neural Q10 reads the resting body temperature at build (`internal_state.neural_temperature_c`).
  - **Check D PASS (spent).** Digby 1955 J Exp Biol 32:279 measured a small *D. melanogaster* warming by 2.5 K in 10 cm/s air under 1.0 cal/cm²/min. The model predicts 2.36 K (ratio 0.94; the bar was ×2).
  - Switch `state:body_temp|model` 0 = body at air temperature; m10f10 sets it to 1. S5 is done once m10f10 is adopted.
- **Director challenge (01:30): is G's silent window biology or convention? Answer: m10f9c failed on the model, not
  on the gate (F-S23-10; `docs/research/s23_gate_silent_window.md`).**
  - G is an engineering stability convention: the noise-free network must return to rest. It is not a claim that
    the brain is silent. S scores measured resting rates with noise on.
  - The amendment G2 was registered before rescoring (DECISIONS 01:31): a 1000 ms window, no growth in any 100 ms
    step, and 0 non-eye spikes in the last 100 ms. A stage that adds a sourced tonic source gets a clamp arm.
  - G2 results, seeds 12-15: m10f9b and m10f10 pass. m10f9c fails on all four seeds.
  - m10f9c's optic lobe holds a self-sustained loop with no input, noise or tonic source. Release at rest is 0
    in this chain, so F-S23-8's mechanism was wrong.
  - Localisation (DECISIONS 01:40, scored 02:12): 300 Hz at the photoreceptors alone returns to rest; 300 Hz at
    the other graded cells sustains and grows (L1-L5, Tm1-Tm3, T5 with the Pm/T1/Dm13 medulla cells).
  - Measured lamina dark rest: tonic photoreceptor release in dark and light, inhibitory onto L1-L3, with the
    synapse resting mid-curve. No fraction of maximal release at rest and no downstream dark rates are in open
    text.
  - Two G2 limits are written down and not applied: (a) is weak to slow drift, and (b) would also fail a real
    noise-free attractor.
- **N1 graded_rmax (F-S23-8, F-S23-10).**
  - Derived 300 Hz (171-684), **sourced for the 6,091 photoreceptors only**: Laughlin 1987 via secondaries, and
    Kazama & Wilson 2008.
  - For the other 30,269 graded cells it is applied beyond its source. No open text gives a non-photoreceptor
    graded release rate; locust graded synapses give only a voltage axis. The `n1_graded_rmax` row says this.
  - The chain keeps 100 Hz (guessed).
  - Laughlin 1987 and Uusitalo 1995 are on `docs/PAPERS_FOR_BEN.md` (new; README map).
- **m10f10** = m10f9b + S5 on. It was registered on m10f9c and rebased on m10f9b when m10f9c failed (DECISIONS 00:57). **G passes on seeds 12-15**, within ±0.005 Hz of m10f9b. The smoke is running.
- **m10f9b** (N1 recorded modes, IN10B row removed; DECISIONS 00:29, 00:42) passes G on seeds 12-15. Its smoke checkpoint at 10.5 s reads whole brain 0.332 Hz, active 0.030, max 58.5 Hz, no NaN, 0 warnings, no runaway (provisional; S is scored on 60 s).
- **S7 and S8 (done, ruled constants; DECISIONS 01:18).** `stubs.CONSTANT_STATES`:
  - `state:immune|model` 0: a healthy, uninfected, conventionally reared lab fly.
  - `state:reproductive|model` 0: a naive (virgin) mature male.

  Every profile reads them, and any other value raises. Test: `tests/test_stubs.py::test_constant_states_are_read_at_their_value_and_refused_otherwise`. Ledger (S7 inferred, S8 guessed, fidelity global) regenerated; the filled fraction is unchanged.
- **Reads for the next rows** (`docs/research/s23_b27_n27_n33_reads.md`):
  - **B27:** adult heart dimensions and rates (Wolf 2006) and the reversal cycle 20-25 s (Wasserthal 2007). There is no adult stroke volume, chamber length or tracer transit, so no adult mixing time can be derived yet; the pre-pupal transit is under 1 s. B27 stays absent.
  - **N27:** resting brain [K+]o is 13.1 ± 2.8 mM (Armstrong 2011), and the surges are pathological only (anoxia 54 mM; spreading depolarisation, median 24 mM). There is no physiological per-spike rise or clearance τ, so the class-level build has its resting value but no rate.
  - **N33:** one larval TBOA effect on synaptic decay (MacNamee 2016 Fig. 8B; the ratio is not read yet) and no fly GAT current data. Eaat1/GAT class uptake is the build; it needs the decay ratio first.
- **Carried from the first s23 context:**
  - m10f6 (N26 light input), m10f7 (MB class noise, N21 off) and m10f8 (sourced organ values) pass G. Their smokes are running on backhouse (F-S23-1).
  - N25: the night-input candidate B **failed** Chowdhury 2023, which is now spent (F-S23-6).
  - m10f9 failed G from the IN10B graded row (F-S23-7).
  - Source corrections (F-S23-5): `ingest_nl_s` 5.0 nL/s; `crop_max_nl` re-sourced to measured meals; N28 Q10 2.5 (Juusola & Hardie 2001).
  - MB output layer sign (F-S23-2; `MEASUREMENT_LIST.md` entry 6).
  - Reads with no usable value (F-S23-3, F-S23-4). Desiccation stays unscored and unspent.
  - Reader notes: `docs/research/s23_n28_n26_checks.md` and `s23_n2_membrane_values.md`.

## Running now
- **Mac**, through slot.py:
  - `runs/s23/fc/run_m10f9b_smoke_mac.sh` (pid 24479): the 60 s smoke. Writes `runs/s23/fc/smoke_m10f9b_s12.json` and `_rates.npz`; done-file **`/Users/ben/fly-emulation/runs/s23/fc/smoke_m10f9b.done`**. ETA about 02:50.
  - `runs/s23/fc/run_stage_mac.sh` with P=m10f10 (pid 27223; smoke pid 29147). Gate done; smoke done-file `runs/s23/fc/smoke_m10f10.done`. ETA about 03:20.
- **backhouse** `/home/greff/fly-m10f` (one thread per job; load about 30 on 28 threads):
  - `run_s23_gate.sh`: smokes m10f6 and m10f7 (`runs/s23/fc/smoke_m10f{6,7}_s12.done`, then `ALL.done`), started 23:06. ETA about 02:45.
  - `run_s23_m10f8.sh`: smoke m10f8 (`smoke_m10f8.done`), started 23:24. ETA about 03:15.
  - `run_s23_kc.sh`: KC grid σ_KC 0.5-3.0 on m10f7 seed 12. Gated on load below 22; `kc0.5_s12` is done.
- G2 and the localisation diagnostic are finished (`runs/s23/g2/`, all done-files present).
- **Keepalive:** Mac pid 32120 (`ssh backhouse ... exec sleep 14400`), started 01:22 under nohup; it ends by itself at about 05:22.
- **Park checklist:** before 05:30, stop whatever of these is unfinished: the two Mac runs and their slots, the three backhouse scripts, and the keepalive shell. Rerun them next session.
- Not mine; never touch: fly2's s29 smokes (`m10f5n7`, `m10f5s29`) on backhouse, CRUCIBLE, and other projects' processes.

## Next (this order)
1. **Score S** for each smoke when it lands, on the registered bars: whole brain 0.162-0.486 Hz, active 0.014-0.042, no runaway or NaN, 0 warnings.
   - m10f9b: also the unit check from `smoke_m10f9b_s12_rates.npz` (every cell of a graded_rec = 1 type has 0 spikes).
   - m10f10: the same bars.
   - m10f6/7/8: copy `smoke_m10f{6,7,8}_s12.json` and `_rates.npz` from backhouse to `runs/s23/fc/` first.
   - Then re-render and view `docs/media/s23_frontier.png` (it is untracked; commit it with the smoke panel).
2. **Adopt** the last stage that passes S into `PROFILES["m10f"]` (m10f10 if it passes, else m10f9b, else m10f8). Run the full battery first: the last one was 299/0, before the S5 and constant-state tests; run it through slot.py, about 15 min. Then view the figure. Then update MECHANISM_STATUS (the N26, N3, N28, S1, S3, S5 rows, each against its own bar, plus the count with a timestamp from `date`), FINDINGS, and the ledger S5 row.
3. **N1:** register and run a class-specific stage: photoreceptors at 300 Hz (derived), the other graded cells at
   100 Hz (guessed, labelled). It needs a per-class `graded_rmax` (CPU path; neutral = one value), G2 on seeds
   12-15, and S. Then source `release_at_rest`. The open-text search found none; the candidates are Ben's PDFs of
   Laughlin 1987 or Uusitalo 1995, or a value derived from the mid-curve resting point (Weckström & Laughlin
   2010). Run its effect on the lamina (tonic chloride current into L1-L3); don't assume it.
4. **N33:** read the MacNamee 2016 Fig. 8B TBOA decay ratio. Then build class-level astrocytic Eaat1/GAT uptake (neutral off, CPU path), with a pre-registered check.
5. `rest_vs_reference.py` on the m10f7 rates; the KC grid summary (`s23_kc_summary.py`, descriptive) once it lands.
6. The rest of the ranked list in MECHANISM_STATUS (count paragraph, 24 Oct 01:20).

**For fly2:**
- From m10f7 on, N21 is off (`cell_type:all|kc_mbon_ltd_timing_rate` 0), because the stage puts DANs at measured rest (7.8-8.0 Hz). It returns when your resting-safe rule lands.
- N22 forgetting stays on (a no-op at rest).
- Your N24 selection includes ER5. The N25 night term acts only on the dFB OFF rate and touches no weights.
- **B17 pump rate (yours):** `pump_full_rate_hz` 10 is guessed. Measured values:
  - cibarial pumping is 5-7 Hz (Manzo 2012 ≈6 Hz, n 14-21, females, 25 °C; Sui et al. 2026 Nat Neurosci 5 / 6 / 7 Hz by method);
  - the pump MNs burst at 25-90 Hz within each cycle (Sui 2026, n 18 per MN).

  Quotes are in `docs/research/s23_crop_pump_q10_adaptation.md`. S3 waits only on this term now.
- S5 (m10f10 on) gives a body temperature 0.07 K above ambient at rest. A body model that needs thorax temperature can read `internal_state.neural_temperature_c`.

**Earlier sessions.** The s13-s22 reference blocks are in `git show 859348d:docs/HANDOFF.md` and in FINDINGS / DECISIONS: the walking bypass assay and the nine ruled-out single causes, the X1 cross-connectome control, s12 body work, the s22 N25 mode 1 fit and its bout trade-off, and the MB type-spread first look. Key carried facts:
- N25 mode 1 (s22): 140 of 14,256 sets passed T1-T4. Every accepted set over-consolidates the night (F-S22-1); at the fast end of k_r the nights fit but the days fall apart (F-S22-2). Hence the night term.
- MB type spread (s22, `docs/research/s22_mb_type_spread.md`): model rate falls with input count (ρ −0.83); data does not (+0.34).
- Walking (parked, Ben 21 Oct): every arm stalls at the core → leg-MN hand-off. `MEASUREMENT_LIST.md` item 4 is the measurement that would cut it.
- Azevedo 2020 recruitment order slow → intermediate → fast is still held out and unspent.

## fly2: s27, `m10f` = m10f5 (DLMn coupling) merged with main and pushed; N12's second check (Hurkey splay) FAILS (no done row); N21 candidate (b) ruled out by Huang 2024 (23 Oct 04:01)

fly2 works in `.claude/worktrees/fly2` (branch `worktree-fly2`). Ben's definition of done: built at full fidelity, ON in the frontier profile at in-range values, and passing a unit check against a measurement where one exists. Zip work is parked (`fly_brain.zip` v1 stays as is, F-ZIP-4). fly2 owns plasticity/learning, synaptic dynamics, sensors and muscles/body, plus N13, N14 and N18.

- **For the Director (03:25 brief):**
  - **Merge: done and pushed.** Main merged into `worktree-fly2` (149d07d; conflicts in parameters.csv, DECISIONS, FINDINGS, MECHANISM_STATUS and HANDOFF, with no row changed on both sides). Full suite on the merged tree, run through `slot.py` (03:22-03:37, `runs/s27/pytest_full_merged_s27.log`): **287 passed, 12 skipped, 0 failed**. Pushed to `origin/worktree-fly2`, ready for you to fast-forward main once fly parks. The commits after the merge touch only docs and probe scripts.
  - **DLMn (N12) second check:** **FAIL, so not the first done row** (F-S27-4; registered DECISIONS 03:34, scored once at 03:59). Second measurement: Hurkey Fig. 2b / Extended Data Fig. 6, the gap around phase 0 in pairwise MN phase histograms, which shakB KD removes, read as the fraction of partner spikes at phase < 0.1 or > 0.9 (uniform 0.2). Fitted c 0.0266 vs c = 0, full network, 8-10 Hz tonic firing, no refit. With independent input the coupled pairs read 0.192 against 0.198 at c = 0 (needs < 0.18 and 0.02 below), and the coupled pairs equal the uncoupled cross-side control (0.191). With shared input, fitted 0.251 vs 0.245 is the registered falsifier. Figure viewed (`runs/s27/dlmn_splay_fig.png`): flat histograms, no dip at 0. Suspects, untested: no spike step through the junction (spike amplitude unsourced), the DLMn PRC (fly's N2/N4 intrinsics; Hurkey's model needs one near the SNL point), and the guessed drive noise (the coupling signal is about a tenth of it). **Tell fly:** the miss is registered against the DLMn intrinsics too. I did not edit fly's rows. `m10f` stays m10f5 (the CC is in band, and the DLMn are silent at rest). The junction row stays partial. N12 could not be done in any case: 6 of 9 gap rows have no value. Hurkey 2b/ED6 is now spent.
  - **N21 candidate (b): ruled out for PPL1 (F-S27-3).** Huang 2024's PPL1 DANs rest at 5.0-26.6 Hz per fly (100 flies, 5 compartments, none below 0.1 Hz). The lowest fly is 3,400x above the 0.0015 Hz that test R needs. PAM is not in Huang. Of the 22 Oct ladder, only (a) remains: a dopamine-side gate, i.e. evoked vs spontaneous DA release per spike. I have no source for it (Ueno 2017 is not one). **Needs your call:** keep looking for (a), or park N21's resting safety as an open mechanism (`docs/MEASUREMENT_LIST.md` item 5) and move on.
  - **fly's ER5 sleep need vs my plasticity rows: no conflict today, one future overlap.**
    - No key collisions: `data/model/parameters.csv` has 860 rows and no duplicate ids. fly's are `n25_*` / `state:sleep|*`; mine are `n21_*`, `n22_*`, `n24_*`.
    - No shared state: the homeostat (mode 1) keeps the ER5 need as a scalar in `internal_state.py` and enters the network only as a tonic `g_dfb_mv` drive on the dFB cells (FB6A/FB6E). N21/N22 edit KC->MBON weights, and N24 edits ER->EPG weights.
    - Future overlap: N24's selection (`^ER\d`) includes ER5, and ER5->EPG is 3,222 synapses (271 edges at >= 5). If the ER5 need ever becomes ER5's release strength (Liu's BRP is an active-zone protein, so that is the natural next step), it would multiply the same edges N24 edits. Both factors would need to act on the baseline weight, and N24's floor would apply to its own factor only. N24 is off (0) in m10f and the need writes no weights, so nothing is needed now. Tell fly2 before wiring the need into ER5 synapses.
- **Done this session (s27):**
  - Commits: 120e0f6 (switch), 4b79905 (fit, m10f5 stage, cascade ruling), 015e339 (`m10f` = m10f5), 149d07d (merge), 736d8d9 (splay pre-registration), 52a7dbe (N21 (b), scorer), plus this one (splay scored). All pushed to `origin/worktree-fly2`.
  - m10f5 adoption (F-S27-1): the DLMn c-f coupling is 0.0266, which gives in-network CC 0.01433 against Hurkey's pair-count mean of 0.0143. Gate G and the 60 s smoke S pass, identical to m10f4 (the DLMn are silent at rest). Battery 277/12/0 before the merge, 287/12/0 after. Figure viewed. **`m10f` = m10f5 since 23 Oct 03:13.**
  - Task 2 (F-S27-2): the rutabaga/dunce cascade is ruled out by prediction (0 of 108 kinetic combinations pass test R; best 55x short). Not built.
  - Tools:
    - `scripts/probes/s27_dlmn_cc.py` (in-network CC; `--reverse`);
    - `s27_dlmn_cc_baseline.py` (clean-pair scoring);
    - `s27_gap_identity.py` (hash identity);
    - `s27_cascade_predict.py` (C1 fractions, the cascade under per-KC test R);
    - `s27_dlmn_cc_fig.py` (F-S27-1 figure);
    - `s27_dlmn_splay.py` (Hurkey splay phase fractions, `--coupling`, `--rate-common/--rate-indep`);
    - `s27_dlmn_splay_score.py` (the registered rules);
    - `s27_dlmn_splay_fig.py`;
    - `s27_huang_ppl1_rest.py` (per-fly PPL1 rest rates).
  - Runs are in `runs/s27/`.
  - Sources read: Hurkey 2023 full text (PMC10232364), Tomchik & Davis 2009 (PMC4080329), Ueno 2017 (not usable for N21 (a)).
- **Running:** nothing. The four splay runs and the merged suite went through `slot.py` and have finished.
- **Next, in order:**
  1. N21: the Director's call on (a) vs parking (above). If a source for evoked vs spontaneous DA per spike turns up, pre-register test R with it (`s26_retention.py`).
  2. N12: a DLMn retry needs a sourced MN spike amplitude (for the spike step) and DLMn excitability/PRC values (fly's N2/N4), then a fresh held-out functional measurement (Hurkey Fig. 3d sync index under ShakB overexpression is unspent, but its formula isn't in the text). MN5 coupling needs a measurement.
  3. Berry 2018 held-out arm (only once N21 is resting-safe).
  4. From s24's list: N10 leg/generic STD, N7 GABA-B, N11 presynaptic inhibition, N9 conductance synapses (values first); B3, B4, B12.
- **Known misses of N21/N22:**
  - No LTP.
  - DA alone doesn't potentiate naive synapses (Cohn 2015).
  - CS- doesn't change (Hige: about -25%).
  - One rate for all compartments; compartments are a DAN->MBON contact proxy.
  - The eligibility and DA trace taus are guessed.
  - Not resting-safe at measured DAN rest (F-S26-1, F-S27-3). KC-side cooperativity can't fix it (F-S27-2). Any run with fly's σ*_DAN on needs `cell_type:all|kc_mbon_ltd_timing_rate` 0.
- **Earlier fly2 state:**
  - MECHANISM_STATUS fly2 rows: 0 done of 49.
  - Scoreboard: 1 of 8 (PER labellar).
  - N30 option B is UNDECIDED (`docs/MEASUREMENT_LIST.md` item 1).
  - DLMn never follow the giant fibre.
- **Literature in hand:**
  - `docs/research/s25_restoration_figcheck.md`
  - `docs/research/s24_fly2_ltp_and_mb_rest_lit.md`
  - `docs/research/s23_fly2_synaptic_plasticity_lit.md`
  - Switch inventory: `scripts/probes/switch_inventory.py --profile m10f0`.
- **Backhouse:**
  - `~/fly2_mc` has the worktree's src, data/params and data/model as of s27 (pre-merge). Run scripts with `ssh backhouse "wsl -d Ubuntu -- bash -s" < script.sh`.
  - Send commands as scripts: cmd.exe breaks a quoted `bash -c` that contains `;`.
  - At most 4 threads; queue above load 24.
- **Mac lessons:**
  - Every heavy job goes through `python3 ~/director/harness/slot.py run --label "fly2: <what>" -- <cmd>` (rule 3; I missed it once in s27).
  - The worktree guard refuses `$(...)`, heredocs into nohup, and any compound command it can't verify. Write scripts to `/tmp/fly2n` and run them plainly.
  - DECISIONS is over 256 KB, so Read it with offset and limit.
  - `runs/` is a symlink.
  - zsh errors on an unmatched glob.
  - The full pytest takes about 15 min.
  - A 20 s full-network run of `s27_dlmn_splay.py` takes about 25 min at 1 thread and needs about 2 GB.
- **Carried:**
  - The body hook: fly owns the premotor->MN fix; then rerun the five scoreboard protocols and step R.
  - The stance loop CS rows (fly2).
  - Optic lobe T4/T5 dendritic position (Behnia 2014 is sealed).
  - `pytest tests/test_gpu_batched.py` under JAX on backhouse.
- **Stay out of:** the VNC files, fly's switches, the flyapp worktree, and `docs/research/sealed/*`. `data/raw/huang2024/` is released to fly2 (spent; consistency and bounds only).

## Where the project stands

- **Frontier profile:** `m10f` = m10f5 (fly2, since 23 Oct 03:13). Chain in `src/flyemu/profiles.py`: m10f0 → m10f1 (STP) → m10f2 (receptor decay) → m10f3 (gap junctions, PSI) → m10f4 (N21, N22) → m10f5 (DLMn coupling) → m10f6 (N26 light input) → m10f7 (MB class noise, N21 off) → m10f8 (sourced organ values) → m10f9b (N1 recorded modes, no IN10B row) → m10f10 (S5 heat balance on). Side stages that failed G: m10f9 (IN10B row) and m10f9c (graded_rmax 300). m10f6-m10f10 are registered and gated (s23), not yet adopted.
- **Default profile:** `WORKING_PROFILE` is still m9c (`FLYEMU_PROFILE` overrides; m4 is the regression reference).
- **Done rows:** fly 2 of 20, both ruled constants (S7, S8), 0 on evidence; fly2 0 of 49 (`docs/MECHANISM_STATUS.md`, with the s23 "path to done" column for fly rows). Scoreboard 1 of 8 (PER labellar; fly2).
- The m9-era state (rung 2 conductance synapses, the m10q class search, ledger v3, rung 1 in m8) is in `git show 859348d:docs/HANDOFF.md` and FINDINGS.

## Regressions

- s23 battery after the m10f6-m10f8 stage edits: 299 passed, 0 failed (`runs/s23/pytest_s23.log`). Since then the S5 heat balance, the constant states and two `parameters.csv` / `structural_keys.csv` rows were added; `test_model_data`, `test_stubs` and `test_internal_state` pass on them. A full battery is due before adoption.
- fly2's merged tree (s27): 287 passed, 12 skipped, 0 failed.

## Open items (carried)

- **Information gaps from session 11:** front-leg FeCO afferent assignment; FeCO rate model; resting activity of tonic VNC inhibitors; VNC glutamate sign per type (needs per-cell Allen labels); FlyMimic passive flexor element (dropped from leg_muscles.csv).
- **Per-cell rules:** the central size rule needs a joint class re-search (GPU); the hemilineage transmitter rule needs its own pre-registration.
- **B3/B4:** coxa DOF labels and envelopes (F-COXA-1); mid/hind muscle parameters are copies; leg damping unmeasured (FlyMimic c/k 0.05 s is a fit).
- **B5:** fused rate and facilitation guessed; fatigue built (guessed).
- **Flight:** fluid coefficients fitted to one condition; body pitch untuned.
- **Brain:** peptide receptor tables minimal; eLN->PN gap junctions absent.
- **State:** organ and clock parameters mostly guessed; ingestion path never exercised.
- **For Ben (optional, outward-facing):** raw data requests as in session 9 (eLife per-trial angles; FlyMimic mid/hind MTUs); per-cell cluster labels for Allen 2020 would let VNC glutamate be signed by cell type.

## Unverified foundations

| Item | Label | What would settle it |
|---|---|---|
| m5 class values (DN release 0.70, MN_other input 1.30) | inferred (search) | a broader search with margins; more held-out behaviours |
| Spring rest angles (fitted) and coxa labels | inferred / assumed (F-COXA-1) | coxa DOFs by function, refit |
| Coxa moment arms (front leg derived; mid/hind copied) | derived / guessed | FlyMimic mid/hind MTUs |
| Wing kinematics and Kutta lift 3.1 | guessed / inferred | measured hover kinematics; lift vs a blade-element model |
| Steering map coefficients (B11) | guessed | Melis et al. 2024 hinge model or data |
| Internal-state couplings (ISN, IPC, clock, dFB types) | inferred / guessed | per-population physiology |
| Haltere afferent identity SNpp25/SNpp34 (census) | inferred | haltere nerve labels (FANC/BANC) |
| Spiking vs graded mode for 2,969 unknown types | Bernoulli priors | per-class physiology |
| Motor size exponent 1.49 (Rin vs volume, 3 classes) | inferred | per-cell Rin and volume in one pool |
| Allen 2020 cluster assignment by marker scoring | inferred (proxy, r 0.72) | deposited per-cell labels |
| Everything in LESSONS labelled guessed/inferred | as recorded | see entries |

## Sealed and held-out data register

No sealed data was opened in session 11. Spent as held out for m7: closed-loop seeds 9-11, bitter->MN9_L, sugar+bitter (these had been spent in s10 for m5 too; seeds 9-11 were new). Seeds 12+ are fresh (12-13 reserved for the rung-1 G1 check, still unspent).

| Data | Status | Rule |
|---|---|---|
| Azevedo cell 180111_F2_C1 (slow MN) | seen (fit and dev) | dev only |
| Azevedo cell 181021_F1_C1, Piezo trials | **sealed** (unopened) | open only via `scripts/score_reflex.py` after a dev pass |
| Azevedo cells 180621_F1_C1, 181127_F1_C1, Piezo trials | **sealed spares** | as above |
| Azevedo CurrentStep trials (181021, 180621, 181127) | seen | none |
| Azevedo 2020 Fig. 3C/E per-type MN V_rest and R_in (fast 150, intermediate 300, slow 700 MΩ) | seen (s23 N2 reader, 24 Oct) | none while the recruitment order is held out: setting MN parameters from them would make that test circular |
| Agrawal 2020 13Bα static tuning | seen | none |
| Agrawal 2020 10Bα / 9Aα recordings | held out; not extracted. The papers' text statement that 13Bα/10Bα are nonspiking set the s13 S3 arm A `graded_rec` rows (mode only). The tuning recordings are untouched | don't use the spiking-mode statement as a check of arm A |
| PN spontaneous rate; PEN 3.9 Hz; KC 0.1 Hz | spent | none |
| flybench olfactory tasks 08/17/18/26/27 | held out for AL changes (m2 baseline 0.80); not run | m5 changes no AL class, but check before use |
| Command direction (MDN back, DNg100 forward) | spent on seeds 1-4 (s7) | new seeds and a gait criterion |
| eLife 2025 passive stiffness, fall onset | seen (s9) | rest-posture data (Fig 3C) unused |
| Wang 2025 silenced-fly fall time course (onset 40-300 ms, median 1.3 mm/s) | held out for standing option (b) (DECISIONS s12 18:23); model fall curves computed in an s12 diagnostic (F-DAMP-2), not compared for selection | choose nothing on it before option (b) |
| Azevedo 2020 twitch-kinetics text/figures | seen (s9) | raw recordings keep their status |
| Session 10 search fit set: template seeds 0-2, sugar->MN9 100 Hz | seen (fit) | none |
| Session 10 held out: template seeds 3-8, m4 body seeds 0-5, bitter, sugar+bitter, sugar 200 Hz | spent (m5 candidate) | new candidates need new held-out evidence |
| Wang 2025 standing head height (median 0.5 mm above collapse) | spent as a SETTING (s13 fly2, S1 fix 1 places the head at 0.929 mm) | can no longer validate standing height |
| Augustin 2017 S1 Table, GF→TTM latency (WT, brain stimulation) | seen (it set fly2's no-chemical-delay rule; F-GJ-3 used it only as a consistency check) | none |
| Augustin 2017 S1 Table, GF→DLM latency | spent on m10f + gaps (s13 fly2, F-GJ-3); DLMn silent | consistency check only from now on |
| Fayyazuddin 2006 MN5 soma potential 4.71 mV | SET a value (s14 fly2, F-GJ-5: PSI→DLMn unitary PSP, switch neutral) | can no longer validate |
| Ryglewski et al. 2014 GF→DLM delay 1.85 ± 0.21 ms (n 10; read as SD, 1.43-2.27) | spent (s20 fly2, F-GJ-6, pre-registered DECISIONS 20 Oct 23:30): two-compartment DLMn PASS at 2.196 ms | consistency check only from now on |
| `gf_latency.py` + `gf_psi_dlm_path.py` on m10f + measured NT + measured PSP + N30 two compartments, seed 1 (central values and the four corners) | spent (s20 fly2, F-GJ-6) | a changed DLMn (doublet fix, tau_m, measured q/ρ) needs seed 2+ and a new held-out range |
| `gf_latency.py` on m10f + measured NT + measured PSP + N30 at the option-B values (class, MN5 L, MN5 R), seed 1 | consistency only (s21 fly2, F-GJ-7; Ryglewski already spent) | none; a build at measured values needs seed 2+ |
| `docs/research/sealed/s21_gf_dlm_sealed.md` (GF→DLM 1:1 vs doublet, paired-pulse refractory period, following frequency, soma amplitude of the axon spike; sources Ryglewski et al. 2014 PNAS, Fayyazuddin 2006 and others) | **sealed, unread** (written by fly2's literature agent, 21 Oct). One header line ("Source 1 — Ryglewski S, Kadas D, … (2014)") was seen in a grep; no value. Value-free summary from the agent: Ryglewski 2014 states two following-frequency pairs, plots the refractory period without stating it, and gives 1:1 qualitatively; Fayyazuddin 2006 gives 1:1 and the spike shape qualitatively only | open once, for the DLMn build at measured values, after its pre-registration |
| fly_brain.zip identity runs (s22 fly2, F-ZIP-1): m10f0, flat floor, no stimulus, 1 s, seeds 12 and 13 | seen as engineering output only (spike totals and hashes; no observation compared, nothing scored or selected) | seeds 12-13 were noted as reserved for the rung-1 G1 check; seed 12 has long been the smoke default. If G1 needs unseen seeds, use 14+ |
| fly_brain.zip scoreboard protocols (s22 fly2, F-ZIP-2): `per_labellar_sugar` (LB3b/LB3c 100 Hz → MN9_L, seeds 0-9, bar > 5 Hz) and `gf_escape` (DNp01 kick train, seed 0, Augustin 2017 latency ranges) | regression checks on spent evidence: the sugar gate is the session 10 fit and class-search gate, and the Augustin ranges are seen or spent (rows above). Results: PASS 5.7 Hz; FAIL, no motor neuron follows | a PASS or FAIL here is not a held-out test; a changed model needs its own held-out check elsewhere |
| fly_brain.zip closed-loop protocols (s22 fly2, F-ZIP-3, scored in F-ZIP-4): `stands_flat_floor` (seed 12, 1 s, no stimulus) and `walks_dng100` (DNg100 100 Hz, seed 0) | seen in F-ZIP-3 before their bars were written (DECISIONS 21 Oct 02:33), then scored under those bars as regression checks: both FAIL. Seed 12 is the F-ZIP-1 engineering seed; seed 0 is command_walk's exploratory seed | a held-out standing or walking test needs new seeds |
| fly_brain.zip `per_leg_sugar` (s22 fly2, F-ZIP-4): LgLG4 + LgAG2 50 Hz → MN9_L, seeds 0-9, bar > 5 Hz | regression check on spent evidence (leg sugar at 50 Hz was the target of the s12 margin diagnostics, F-TASTE-LEG-1, F-STAB-6). Result: FAIL, 0 Hz on every seed | not a held-out test; a changed model needs its own held-out check |
| flyapp `t4t5_ds.py` on v0r + flyvis rows (seed 0, both sets) | spent (s13 fly2, F-VISION-12: 0 of 8) | a new optic-lobe candidate needs a new seed or a new test |
| flyapp `t4t5_ds.py` on v0r + flyvis rows + flyvis pair strengths (seed 1, both sets) | spent (s14/s20 fly2, pre-registered DECISIONS 14 Oct 00:41; F-VISION-15): medulla FAIL 1 of 8, photoreceptor FAIL 0 of 8 | the next candidate needs seed 3 or a new test |
| flyapp `t4t5_ds.py` on the same + CT1 per-column compartments (seed 2, medulla set) | spent (s14/s20 fly2, pre-registered DECISIONS 14 Oct 01:05/01:07): FAIL 0 of 8, responses under the 0.5 mV floor | the next candidate needs seed 3 or a new test |
| Bypass S2 DNg100 15/25/40 mV and step R (8 arms) on the T1 fill | spent twice (s20 fly2): level 1 F-XCONN-3 (DECISIONS 20 Oct 22:02) and level 2 F-XCONN-4 (22:44); FAIL 3 of 3 and NO REACH 0 of 8 both times | a new VNC candidate needs a fresh check |
| Behnia 2014 step offset/onset ratios and filter peaks (Mi1, Tm3, Tm1, Tm2) | unspent; reserved as the flyvis pair arm's held-out recordings check (Ben, 13 Oct 22:53) | their amplitudes already set graded_range_rec |
| Azevedo 2020 Fig 5—fig supp 1A class rates (fast ≈1, int ≈10, slow ≈60 Hz, read off the plot) | seen (S4b fit target, 14 Oct) | none |
| Azevedo 2020 Fig 3E Rin class means (150/300/700 MΩ) | **spent as a check** in s15c gate 1(c), 21 Oct 02:12 (pass; it had been an input to ρ in s15/s15b) | don't reuse as a held-out target |
| Azevedo 2020 recruitment order slow→intermediate→fast (Fig 5G text) | **held out, unspent** (S4b falsified with no s*, 14 Oct 00:21; its 15/40 mV members unviewed) | score once, against a future pre-registered MN-layer fit, after its chosen value is written down |
| Hige 2015 Fig 3D, MBON-γ1pedc>α/β CS+ charge after one forward pairing (−90 ± 3.7%) | seen; **fit target** for m10f4's shared `kc_mbon_ltd_timing_rate` 0.430 (F-S24-2). Its CS− (about −25%) is reported, not scored | don't reuse Fig 3D as a check of N21 |
| Hige 2015 Fig 1H/1J backward pairing (odour 0.5 s after the last DAN pulse: no change at γ1pedc, n 7) | **unspent** (F-S24-2 reported it without scoring; LTP was off) | spend once, as the falsifier of a future potentiation rule |
| Hattori 2017 Fig 6F, PPL1-α'3 restores depressed MBON-α'3 responses (8, 18, 33, 40% after 1, 3, 6, 10 DAN stimulations; flat controls; n 10 cells) | seen; **fit target** for `kc_mbon_dan_restore_rate` (provisional 0.00289, s25; `docs/research/s25_restoration_figcheck.md`). The in-network confirm (DECISIONS 22 Oct 04:11, 04:22) is a check of the implementation, not evidence | don't reuse Fig 6F as a check of the restoration rule |
| Cohn 2015 Figs 6-7 (DA alone potentiates naive KC->MBON-γ1pedc EPSCs; unpaired DA restores depressed ones, Fig 7I) | seen; **form only** (the rule's shape, no value fitted). DA-alone potentiation of naive synapses is a known miss of the s25 rule | not usable as a held-out check of the s25 rule |
| Berry 2018 Fig 5H-I, unpaired DAN activity after learning erases the MBON-γ2α'1 memory trace (Paired>Unpaired vs Paired>Decay) | **SEALED** (values in `docs/research/sealed/s25_restoration_heldout_sealed.md`, written by a figure-check agent, never read by fly2). Held out for the s25 restoration rule; score F = (R_post2 - R_post1)/(R_pre - R_post1) from the model first, then open | spend once, as the held-out test of `kc_mbon_dan_restore_rate` |
| Handler 2019 Fig 2D-E, ISI dependence of KC->MBON plasticity (γ4 signs: −1.2 s potentiation, 0 and +0.5 s depression, +6 s minimal) | **spent** on m10f4 (F-S24-2, 22 Oct): H1 and H2 pass, H3 fails (no LTP) | don't reuse as held out; a future LTP rule needs a new held-out set |
| Huang et al. 2018 PPL1-α'2α2 resting rate (6-10 Hz) and Turner 2008 KC rest (0.1 Hz) | fly's resting-fit targets; used by fly2 s26 as the rest CONDITION of test R (F-S26-1), not fitted to and not scored against | none |
| Turner 2008 KC odour responses (6 ± 5% respond; α/β 2.2, α'/β' 4.9 spikes per odour) | seen; set the KC drive in `kc_mbon_pairing.py` (F-S24-2) | none |
| Hurkey 2023 Fig 2f, MN1-4 subthreshold coupling coefficients (0.023 ± 0.003 s.d. strong pairs, 0.01 ± 0.0027 weak) | seen; **fit target** for m10f5's `electrical:DLMn c-f->DLMn c-f\|gap_coupling` 0.0266 (pair-count mean 0.0143; fly2 s27, F-S27-1) | none |
| Hurkey 2023 Fig 2h, spike AHP CC 0.042 ± 0.04 and overshoot 0.01 ± 0.004 | **seen**: the AHP CC was computed in the s27 fit runs (0.0123-0.0188) before any band was written (DECISIONS s27 amendment) | consistency only, never held out |
| Hurkey 2023 Fig 2b and Extended Data Fig. 6, MN phase histograms (gap around phase 0 in controls, absent under shakB KD; near-zero-phase fraction in (-0.1, 0.1)) | **spent** 23 Oct 03:59 on N12's second check: FAIL, falsified (F-S27-4; registered DECISIONS 03:34) | consistency only from now. Unspent: Fig 3d synchronization index under ShakB overexpression (formula not in the text). Correction: the '0.56 vs 0.61' pair is Shab KD, not shakB |
| Strother 2018 Fig. 4E-F (in vivo CDM raises Mi1, Tm3, Mi4, Mi9, T4) | **spent** (s19 U3, pass 5 of 5; DECISIONS 22 Oct 02:05) | sign consistency only from now |
| Strother 2018 Fig. 6F Mi4 ×2.66 under CDM | SETS the shared receptor gain a (s19 U2 calibration) | can't validate N19 |
| Dacks 2009 PN +15% under bath 5-HT | **SPENT (s19, 22 Oct 05:23): FAIL**, −0.34% at a* = 0.0649 (F-S19-2). Weakened beforehand: a fail at the wrong a* = 0.0458 had leaked (DECISIONS 04:42) | none; can't be reused |
| Lv 2024 Fig. 2E 50-pulse OA τ 0.6/9.4 s | **held out, unspent** for U1h (s19). The run at the wrong a* is void and unread | score once, at the registered a* = 0.0649 |
| Lamba 2014 Fig. 1C y w ZT21 advance (5 min, 1,500 lux) | **spent** 23 Oct 00:09: +3.21 ± 0.23 h (blind pixel read) against +2.89 predicted, **pass** (F-S20-3) | can't validate N26 again |
| Lamba 2014 Fig. 1C y w ZT15 delay −3.1 ± 0.35 h; Kistenpfennig 2012 zero crossing CT 18.5 and CT15 delay −4.05 h | training targets of the s20 CRY-TIM fit (k_tim, ct_tim fitted) | can't validate N26 |
| Vinayak 2013 10 min IRC half-max; Tang 2010 ZT15 TIM loss; Shafer 2002 Fig. 6D TIM profile | SET a, k_d (by rule) and TIM_DD (s20) | can't validate N26 |
| Vinayak 2013 120 min half-max, TIM loss at threshold, 2.4 h max advance | consistency only (seen); the first two miss (F-S20-3) | none |
| Vinayak 2013 CT20-21 advance 2.4 h (1 h pulse) | seen in an agent report; never used to set a value | consistency only (seen before registration) |
| Huber et al. 2004 Sleep 27:628 rebound after 6/12/24 h deprivation | **training context** (Director, 23 Oct 00:45: its direction "dependent on prior time awake" leaked through the s20 round-3 reader). Magnitudes still unread; no full text reachable | may set or train N25 values if Ben supplies the full text; never a held-out test |
| Chowdhury et al. 2023 eLife 12:e91355 Fig. 1 (Canton-S males, vortexer 20 s arm, 6/12/24 h ending ZT 0, day-1 normalised rebound); raw data Dryad doi:10.5061/dryad.qnk98sfpp | **SPENT 24 Oct 00:15** (DECISIONS; F-S23-6): s23 candidate B fails (6 h low; 24 h inside for panels I and K, outside for J; the figure's 20 s 24 h box disagrees between I and J). Scored from a blind figure read (`docs/research/s23_chowdhury_fig1_read.md`); Dryad raw data unread, needs a browser login; it can refine the recorded score, not re-open it. Before: held out, weakened (registered DECISIONS 23 Oct 00:53). Protocol read (Methods only). Results/Discussion subsection titles seen (stimulus-frequency effect, yoked low-frequency rebound, little debt repaid over cycles, short bouts mask rebound, 5-HT candidate); magnitudes and the deprivation-length dependence unseen. Dryad not downloaded | score once, on the first new-structure homeostat that passes its implementation and training checks; the 00:34 mode 0/1 predictions are reported at the same read. s22: mode 1 passes; locked 99.7 / 150.2 / 174.3 min (DECISIONS 03:24); T5 amendment 70.3 / 111.3 / 131.1 proposed (03:32); the Director names the one scored; s23: the Director chose (c) (23 Oct 04:50), a new structure first; the night-input refit is registered (DECISIONS 23 Oct 23:30) and running. Dryad still not downloaded |
| Brown et al. 2020 PLoS Genet 16:e1008270 (PMC7089559) | protocol read only (one 24 h duration, mainly females); no outcome seen | unused; not a dose series |
| Huang et al. 2024 Nature Fig. 1 voltage imaging (PPL1 and MBON resting rates, Zenodo 10998457, `data/raw/huang2024/`) | **spent** 23 Oct 01:00 on the s20 MB noise fit: PASS 6 of 9 (F-S21-1) | consistency only from now; a per-type MB rate mechanism needs another held-out source. Released to fly2 23 Oct 03:25: used as a bound (nothing fitted) to rule out N21 candidate (b) for PPL1 (F-S27-3) |
| Abhilash & Shafer 2024 two-process fit (taus 8.76 / 9.51 h, 74.36 % sleep) | model source (s20 `SLEEP_SOURCED`, neutral). C1 implementation check FAILED by 1.2 pp (F-S20-4) | not evidence for N25 |
| Abhilash & Shafer 2024 Fig. 1E: CS, w1118, yw males "~70 % to 80 %" of 24 h asleep (DAM, LD) | training: the s22 primary band 1008-1100 min/day (`docs/research/s22_n25_reads.md`) | can't validate N25 baseline |
| Liu et al. 2016 Cell 165:1347: R2 (= ER5, inferred) BRP raised at +2 h, back at +24 h; firing about 3× ZT13-15 vs ZT0-2 | SET τ_decay bracket (s21) and training checks T3, T4 of the s22 fit | can't validate N25 |
| Pimentel et al. 2016 Nature 536:333: dFB restart 25.86 ± 7.61 min (7 of 15, after > 12 h SD) | SET k_r (s22, the rate at full need) | can't validate N25 |
| Garbe et al. 2015 Biol Open 4:1558 Fig. 2 (iso31 males, SB/MB DAM bouts; own figure read) | training (s22 night check; s23 T5: day and night bouts within mean ± 1 s.d.) | can't validate N25 bouts |
| Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734: KC spontaneous 0.1 ± 0.4 Hz (71 KCs, Canton-S females; text) | seen (s22, Sonnet reader; MBON/DAN rates barred, unseen): SET candidate for a KC rest rate; the same 0.1 Hz was already spent as a check (row "PN spontaneous rate; PEN 3.9 Hz; KC 0.1 Hz") | can't validate MB rest rates |
| Felsenberg et al. 2018 Cell (M4β′/M6 → PAM-γ5 excitation, CsChrimson + GCaMP6f); Aso et al. 2014 eLife (MBON transmitters); Liu & Wilson 2013 PNAS (GluClα in the AL) | seen (s22, Sonnet reader, text only; MBON/DAN rates barred, unseen): MBON link signs | can't validate an MBON link-sign switch's rates |
| Male daily sleep 618-1100 min/day (Cirelli 2008, Harbison 2013, Buchert 2022, Geissmann 2019) | seen (s20 N25 category A); C2 consistency check | consistency only |
| Lv 2024 Fig. 2J and Wan 2021 single-pulse τ | SET the pool kinetics; U1 is a consistency check | none |
| Burggren 2017 respirometry and male mass; PMC8774106 TAG; PMC4335172 crop and gut | SET the s19 sourced values (`internal_state.SOURCED`) | can't validate S1-S4 |
| Male starvation survival 24-112 h (secondary reports) | **spent** (s19 S2, pass 28.4 h; F-S19-1) | consistency only |
| Ja 2007 CAFE, single males 1.5 µl/day | **spent** (s19 S3, pass 1.85; F-S19-1) | consistency only |
| Male desiccation survival 16.1-34.5 h (secondary) | **held out, unspent**; seen in an agent report and never used to set a value (S4 not scored; s23: the two dry-air water-loss sources in hand can't set the rate, F-S23-4; readers barred from survival times) | score once when the loss rate and lethal fraction are sourced |
| Klepsatel, Wildridge & Gáliková 2019 Sci Rep 9:5239, metabolic Q10 2.0 (Oregon R) / 2.3 (Canton S), adult males | SETS `q10_met` (s23, measured) | can't validate S1 |
| Itskov et al. 2014 sip volume and duration; Manzo et al. 2012 pumping rate; Edgecomb et al. 1994 (via a secondary) crop capacity; Qi et al. 2015 first meal 0.32 µL | SET `ingest_nl_s` (derived) and `crop_max_nl` (inferred, Qi the upper bound) for m10f8 (s23) | Qi's meal volume is circular for S3 |
| Liang, Holy & Taghert 2016 Fig. 1G DN1 Ca2+ peak CT 18.8-19; Kunst et al. 2014 DH31+ DN1 late-night wake (abstract and secondary) | SET `ct_dn1_h` 19 (inferred) and the sign and window of the N25 night term (s23) | can't validate N25 |
| Gate G seeds 12-15 and smoke S seed 12 on m10f6-m10f10, m10f9 (seed 12) and m10f9c (seeds 12-13); G2 (1000 ms window, registered 24 Oct 01:31) seeds 12-15 on m10f9b, m10f9c, m10f10, and the seed-12 localisation diagnostic (P/Q) on m10f9c (s23) | engineering checks under fly2's stage rule; nothing fitted on them | none |
| Digby 1955 J Exp Biol 32:279, small *D. melanogaster* radiant warming 2.5 K (10 cm/s air, 1.0 cal/cm²/min; wing-beat thermometer) | **spent** 24 Oct 00:57 on S5 Check D: PASS, 2.36 K predicted (F-S23-9; registered DECISIONS 00:51) | consistency only from now; S5 needs another measurement for any further check |
| Laughlin, Howard & Blakeslee 1987 (240 vesicles/s per active zone, via de Ruyter van Steveninck & Bialek 2002) and Kazama & Wilson 2008 (p 0.79) | SET `graded_rmax` 300 Hz (derived, s23) | can't validate N1 |
| B27 / N27 / N33 reads (Wolf 2006, Wasserthal 2007, Armstrong 2011, Spong 2016, MacNamee 2016; `docs/research/s23_b27_n27_n33_reads.md`) | seen; candidate SET values (none used yet) | a check for those rows needs a source not used to set them |
| Lamina dark-rest reads (Laughlin 1989; Weckström & Laughlin 2010; Rusanen & Weckström 2016; Dau 2016; Laughlin & Osorio 1989; Zheng 2006; Juusola 1995 and Uusitalo 1995 abstracts) and graded-synapse voltage reads (Simmons & de Ruyter van Steveninck 2005; Burrows & Siegler 1978); `docs/research/s23_gate_silent_window.md` | seen; candidate SET values for `release_at_rest` (none used) | a check for N1 only if not used to set r0 |

## Things that will bite you

- **The default profile is m9c** (`WORKING_PROFILE`); the frontier is `--profile m10f` (= m10f5 until a stage is adopted). Regression commands need `FLYEMU_PROFILE=m4`. `standing.py` reads legacy per-unit torque states and fails under Hill mode: run it with m4. `scripts/model_keys.py` always dumps the m4 inventory.
- **Never sync code to backhouse while a battery runs there** (5 Oct 21:30): a test read a CSV mid-overwrite (`EOF inside string`) and failed spuriously. Wait for the battery, or sync to a separate directory.
- **Probes must step the motor path with `Organism.motor_step()`** and check `d.warning` (F-HARNESS-1/2).
- **closed_loop_check's "tonic" exclusion** uses per-type spontaneous drive; a sampled global drive makes every cell tonic (F-SAMPLE-1). Class tonic drive is counted as network activity.
- **GPU:** `.venv-gpu` sees the main venv through a `.pth`; XLA prints out-of-memory retries at start (shared GPU) and continues; runs are not bitwise reproducible in busy regimes; plasticity mechanisms (N21-N24, N27 glia, conductance, presynaptic inhibition) are refused, not ported; k > 1 in the closed loop is an approximation.
- **Flight needs a 0.05 ms step** (FlightMotor raises otherwise); halteres and wings are PD-imposed at 3 kHz bandwidth (5 kHz diverges).
- **parameters.csv:** append rows or rewrite with pandas `dtype=str, keep_default_na=False`; `build_class_params.py` rewrites the class rows (n2c_/n3c_/n5c_) and keeps the others. Retired placeholders are in `data/params/retired_placeholder_rows_s10.csv`.
- **backhouse needs a WSL keepalive** while detached jobs run (`ssh backhouse 'wsl -d Ubuntu -- bash -c "exec sleep 25000"'` in the background), or the VM can stop. Send commands as piped scripts (`ssh backhouse 'wsl -d Ubuntu -- bash -s' < script.sh`); cmd.exe mangles quoted pipes and `;`. A sync can fail silently inside a compound command: check before launching. s23 overwrote `/home/greff/fly-m10f/src` from `git archive`.
- **GPU physics:** MJX 3.9 refuses this fly (mesh-contact margins on 69 adhesion pairs; body-transmission adhesion actuators); mujoco-warp needs MuJoCo 3.14 while flygym pins 3.9 (F-GPU-3). Body time is 30% physics, 70% our Python.
- From earlier sessions, still true: eLife stiffness units mN·m/° (F-PASSIVE-1); FlyMimic in g, mm, s; Hill mode replaces leg torques only; `date` is the only clock; `runs/` and `data/cache/` hold evidence (untracked); ≤ 8 model processes on backhouse; re-run `calibrate_joint_signs.py` after an adopted body change (not re-run for m5; the signs should depend on joint geometry, not on the springs m5 changes, but that is unverified).
- **Diagnostic probes** (`scripts/probes/command_walk.py`, `resistance_reflex.py`, `feco_paths.py`) measure; they are not objectives. In command_walk the whole-spectrum joint share includes the slow posture shift at replay onset, so read the 3-50 Hz share.
- **`FLYEMU_EXTRA_PARAMS`** adds candidate per-type rows for probes without editing cell_types.csv.
- **`model_data.validate`** (s23): `bound_verified` must be `verified` or `unverified`. A wired row's `current_m4` must lie inside `bio_min`/`bio_max`; never widen a bound to hide it. The n28_q10 precedent keeps a wide bound and puts the sourced range in the prior and notes. Every key the model reads needs exactly one owner, a `mechanisms.yaml` switch or a row in `structural_keys.csv`.
