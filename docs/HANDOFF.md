# Handoff: current state

**Rewritten each session; do not append.** State as of 1 October 2026, 03:15, end of session 11.

Session 11 was Director-run, from 30 September about 17:00 to 1 October about 03:00, mostly on the Mac. Its results are in `docs/FINDINGS.md` (Session 11), decisions in `docs/DECISIONS.md`, the timeline in `docs/SESSION11_LOG.md`, the plan in `docs/PLAN_NEXT.md`, and ranked fidelity upgrades in `docs/FIDELITY_LADDER.md`.

## Where the project stands

- **Direction (Ben, locked 2026-09-28, re-stated 2026-09-30):** fill 100% of the fly's information at the highest plausible fidelity; the ledger fill fraction is the metric. Missing data is inferred with development models (size rule, lineage/hemilineage, birth order, wiring compensation, segment/side) and transcriptome tables, every built mechanism runs at its prior, then the bounded search of CONSTRUCTION.md / PLAN_NEXT.md. Behaviour and stability are guardrails, never objectives: do not fit to recorded walking or tune for walking (that was tried; see DECISIONS 2026-09-30 20:35).
- **Working model: m9** (`profiles.M9`, the default since 2026-10-01 00:27) = m8 + class gains re-searched on the rung-1 membrane (DN release 0.85, MN_other input 1.6, gustatory release 1.25, central size exponent 1.0; held out seeds 17-19 silent, bitter suppression, sugar dose response, bitter alone all pass; sugar -> MN9_L 5.7 Hz; F-RS-1). m8 kept (`FLYEMU_PROFILE=m8`).
- **Rung 2 (synapse receptor mix and kinetics): built, tested, not adopted** (F-R2-1; DECISIONS 2026-10-01 00:45 to 02:44).
  - What exists:
    - conductance synapses, with a GPU port equal to the CPU (`gpu/batched.py`; tests in `tests/test_gpu_batched.py`);
    - slow-receptor shares per cell from mRNA (`src/flyemu/receptors.py`);
    - `tau_s_inh`;
    - a charge-basis switch for slow shares (`cell_type:all|slow_share_basis`).
    All are neutral by default; the candidate profile is `m10p`.
  - Gates:
    - Gate A (equivalence) passed.
    - At priors the loop ran away, because muscarinic peak shares tripled cholinergic charge. Repair 1 (charge basis) restored silence on seeds 20-22.
    - Sugar -> MN9_L fell to 0 Hz, and 30 pre-registered class-gain candidates (best 0.7 Hz) did not restore it.
  - The cause is the conductance synapses themselves. The block sits 2 synapses in, at GNG108, and the inferred mechanism is inhibitory shunting.
  - **Fill from recordings and repair 2 (m10q, 03:01):**
    - e_inh is now -56 mV, recorded (Rohrbough & Broadie 2002; Wilson & Laurent 2005).
    - Conductance weights are referenced to threshold (`cell_type:all|cond_reference`).
    - Mi1/Tm1/Tm2/Tm4 rest at -55 mV, recorded (Behnia 2014), via `cell_type:all|rest_from_recordings` and `v_rest_shift_rec` rows in cell_types.csv.
    - Result: silent on seeds 26-28, sugar -> MN9_L 2.4 ± 1.6 Hz against a 5.5 bar. Not adopted; both rung-2 repairs are used.
  - Next: a class-gain re-search on m10q (inhibitory release in the box) on fresh seeds from 29. Held-out seeds 23-25 and the held-out assays remain unseen for rung 2.
- **Recording:** `docs/media/m9_closed_loop.mp4` shows 3 s of m9 in closed loop, body beside brain activity by class. The caption, `docs/media/m9_closed_loop.md`, says what it shows. It is a communication artifact, not evidence.
- **m8** (`profiles.M8`, the default from 2026-09-30 21:47 to 00:27) = m7 + rung-1 intrinsic conductances (A, M, Ih, T, NaP, Kv2, BK, SK + Ca pool) per type. SK/BK/Kv2/Ih/Ca fitted to Azevedo 2020 slow-MN current steps (`scripts/fit_spike_channels.py`; derived at that class, inferred elsewhere by channel mRNA); slow-MN θ/t_ref/drive from `*_rung1` rows. Gates passed: G1 silent on seeds 12-13; GPU (`gpu/batched.py`) equals CPU per cell on 300 ms whole CNS. Sugar -> MN9_L 2.7 Hz (m7 6.9), so the class gains were re-searched, giving m9. Mac brain cost 8.4x m7; use the GPU path for many runs. m7 kept (`FLYEMU_PROFILE=m7`).
- **Previous working model: m7** (`profiles.M7`, the default) = m6 + the motor size principle: per-cell input gain x (type geometric-mean volume / cell volume)^1.49 for 757 motor neurons (`src/flyemu/percell.py`, table `data/derived/percell_motor_factors.csv`). Adopted after a pre-registered held-out test: seeds 9-11 silent, bitter and sugar+bitter -> MN9_L 0 Hz, sugar -> MN9_L 6.9 ± 2.3 Hz. The same rule for central neurons (alpha 1.0) is built but neutral: it cuts sugar -> MN9 to 1.8 Hz because the m5 class values were fitted on the old gains (F-PERCELL-1).
- **Ledger v3** (`scripts/blank_ledger.py`, per source level): data used for 1.9% of 374 M slots; outside per-synapse grain 47% measured, 45% class prior (F-LEDGER-3). Rule-filled slots 3,282 after m7 (`runs/s11/ledger_after_m7.txt`).
- **Built, neutral, awaiting pre-registration:** hemilineage transmitter rule for 817 unclear cells (`connectome:unclear|nt_by_development`, LOTO 0.989, F-NT-2); leg joint damping (`joint:leg|damping`, neutral 1; 0.043 failed its mechanism check); muscle optimum join (`muscle:leg|optimum_join`, neutral 0) and femur-tibia flexor scale (`muscle:leg|ft_flexor_scale`, neutral 1), both failed their mechanism checks.
- **Fidelity rung 1 (intrinsic conductances per type): adopted in m8 at 21:47 after repair 1 (fit to recorded current steps; first scoring at priors failed)** (`src/flyemu/channels.py`, switch `cell_type:all|intrinsic_channels`, neutral 0, 6 single-cell tests). Channel and innexin mRNA per type: Davis + Özel (82 types, 73,253 neurons) and Allen VNC hemilineages (10,498 neurons); the rest take the class prior (F-RNA-4). At the guessed priors:
  - Mac step cost 8.9x;
  - sugar -> MN9_L 1.7 Hz;
  - VNC motor output silent.
  The cause was the guessed spike-to-SK coupling (F-RUNG1-1). The repair (fit to recorded current steps) gave m8.
- **Receptor data:** Özel 2021 optic-lobe calls (+12 glutamate-sign rows, F-RNA-2); Allen 2020 VNC atlas: every hemilineage co-expresses GluCl and iGluR, so VNC glutamate cannot be signed by lineage (F-RNA-3).
- **Session 11 diagnostics, kept as findings, all switches neutral** (F-RHYTHM-1, F-WALK-1, F-BODY-1, F-REFLEX-1): no VNC rhythm with spiking, graded or adapting local cells; DNg100 at 92 Hz adds ~0.7 Hz to leg MNs; joints follow imposed torque at 2 Hz but not 10 Hz (damping); FlyMimic femur-tibia extensor:flexor F0·r is 10:1 against Azevedo's measured flexor force; no femur-tibia resistance reflex (front-leg FeCO under-assigned, tibia pools under tonic VNC inhibition). These are information gaps for the ledger, not targets.
- **Template dead fly, flight configuration, GPU brain:** unchanged from session 10 (dead fly passes; tethered hover lift 0.99 with exact kinematics; batched GPU brain 0.37-0.45 s per member-second). Backhouse came back late in the session and ran rung 2's equivalence and Gate B runs. At 01:30 its WSL VM was about 95% full from another distro, and 16 parallel fly jobs were OOM-killed, so check `free -g` before launching there (each whole-CNS job needs about 2 GB).

## Regressions (Mac, session 11 end)

- Tests: the full suite passed (171) on 1 October at 03:10, after the m10q code.
- m9's guardrails passed at adoption:
  - seeds 12-19 silent;
  - sugar 5.7 ± 1.4 Hz, and 15.7 Hz at 200 Hz;
  - bitter and sugar+bitter at 0.
- An m9 sugar replicate at 3 trials gave 7, 6 and 7 Hz.

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
| Agrawal 2020 13Bα static tuning | seen | none |
| Agrawal 2020 10Bα / 9Aα recordings | held out; not extracted | none |
| PN spontaneous rate; PEN 3.9 Hz; KC 0.1 Hz | spent | none |
| flybench olfactory tasks 08/17/18/26/27 | held out for AL changes (m2 baseline 0.80); not run | m5 changes no AL class, but check before use |
| Command direction (MDN back, DNg100 forward) | spent on seeds 1-4 (s7) | new seeds and a gait criterion |
| eLife 2025 passive stiffness, fall onset | seen (s9) | rest-posture data (Fig 3C) unused |
| Azevedo 2020 twitch-kinetics text/figures | seen (s9) | raw recordings keep their status |
| Session 10 search fit set: template seeds 0-2, sugar->MN9 100 Hz | seen (fit) | none |
| Session 10 held out: template seeds 3-8, m4 body seeds 0-5, bitter, sugar+bitter, sugar 200 Hz | spent (m5 candidate) | new candidates need new held-out evidence |

## Things that will bite you

- **The default profile is now m7** (m6 + motor size principle). Regression commands need `FLYEMU_PROFILE=m4`. `standing.py` reads legacy per-unit torque states and fails under Hill mode: run it with m4. `scripts/model_keys.py` always dumps the m4 inventory.
- **Probes must step the motor path with `Organism.motor_step()`** and check `d.warning` (F-HARNESS-1/2).
- **closed_loop_check's "tonic" exclusion** uses per-type spontaneous drive; a sampled global drive makes every cell tonic (F-SAMPLE-1). Class tonic drive is counted as network activity.
- **GPU:** `.venv-gpu` sees the main venv through a `.pth`; XLA prints out-of-memory retries at start (shared GPU) and continues; runs are not bitwise reproducible in busy regimes; plasticity mechanisms (N21-N24, N27 glia, conductance, presynaptic inhibition) are refused, not ported; k > 1 in the closed loop is an approximation.
- **Flight needs a 0.05 ms step** (FlightMotor raises otherwise); halteres and wings are PD-imposed at 3 kHz bandwidth (5 kHz diverges).
- **parameters.csv:** append rows or rewrite with pandas `dtype=str, keep_default_na=False`; `build_class_params.py` rewrites the class rows (n2c_/n3c_/n5c_) and keeps the others. Retired placeholders are in `data/params/retired_placeholder_rows_s10.csv`.
- **backhouse was offline for session 11** (Director's note); it may need waking. A sync can fail silently inside a compound command: check `synced` before launching jobs.
- **GPU physics:** MJX 3.9 refuses this fly (mesh-contact margins on 69 adhesion pairs; body-transmission adhesion actuators); mujoco-warp needs MuJoCo 3.14 while flygym pins 3.9 (F-GPU-3). Body time is 30% physics, 70% our Python.
- From earlier sessions, still true: eLife stiffness units mN·m/° (F-PASSIVE-1); FlyMimic in g, mm, s; Hill mode replaces leg torques only; `date` is the only clock; `runs/` and `data/cache/` hold evidence (untracked); ≤ 8 model processes on backhouse; re-run `calibrate_joint_signs.py` after an adopted body change (not re-run for m5; the signs should depend on joint geometry, not on the springs m5 changes, but that is unverified).
- **Diagnostic probes** (`scripts/probes/command_walk.py`, `resistance_reflex.py`, `feco_paths.py`) measure; they are not objectives. In command_walk the whole-spectrum joint share includes the slow posture shift at replay onset, so read the 3-50 Hz share.
- **`FLYEMU_EXTRA_PARAMS`** adds candidate per-type rows for probes without editing cell_types.csv.
