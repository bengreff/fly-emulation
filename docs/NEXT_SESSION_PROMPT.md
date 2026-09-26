# Session 7 prompt: unattended, 5 hours maximum

Paste everything below the line into a fresh Claude Code session in
`/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions.

**Timing**
- Work for **at most 5 hours of wall time**.
- At start, run `date` and record the start time in a new `docs/SESSION7_LOG.md`.
- Check `date` before each new task.
- **Stop starting new work at 4h40m**, then do the wrap-up.
- Stopping earlier is fine if the priorities are done or blocked. Do not stop just because one experiment failed; move to the next priority.

## Read first

1. `CLAUDE.md`. The agent limit below overrides it.
2. `docs/HANDOFF.md`, especially the session 6, 6b and 6c bullets.
3. `docs/FINDINGS.md` from "# Session 6" to the end: F-DELAY-1 … F-AL-3.
4. `docs/DECISIONS.md` from "## Session 6" to the end. These are the pre-registrations and their results, and the protocols you must follow.
5. The top of `docs/PLAN_NEXT.md`.
6. `docs/LIT_SESSION6.md`: literature leads (verify before use).
7. The data tables:
   - `data/measurements/targets_session6.csv` (measured targets, with use / held-out status);
   - `data/params/cell_types.csv`;
   - `data/params/proprio_assignment.csv`.

## Where things stand (one paragraph)

- The body, sensors and motor units are now largely data-based:
  - morphological conduction delays;
  - Hallem ORN rates;
  - Azevedo motor-unit forces;
  - a slow flexor MN fitted to raw recordings, and shown to transfer to a second cell;
  - leg proprioceptor identities from the BANC crosswalk.
- The fly still does not stand, and the leg resistance reflex is absent. The diagnosis is consistent in the leg (F-AZ-2, F-VNC-1/2) and the antennal lobe (F-AL-2/3). Signals of the right sign reach relay cells that sit **silent below threshold**, because one brain-wide synaptic efficacy (0.165 mV, borrowed V_rest −52 mV, no background activity) leaves them there.
- In the animal, those cells rest partly active. 13Bα and 10Bα leg interneurons are nonspiking and graded, and PNs fire 1–5 Hz spontaneously.
- **The next step is to set transmission and operating points from measurements, one circuit at a time.**

## Standing rules (non-negotiable)

**Labels.** Every value is measured / derived / inferred / guessed (or unknown / absent), and fitted values are inferred. A value's label never gets upgraded.
- `Registry.validate()` must return `[]` before each commit.
- `uv run pytest tests -q` must pass before each commit.

**Pre-register before scoring**, in `docs/DECISIONS.md`: criteria, fit set, held-out set. Report failures plainly.

**Post-hoc limit.** At most **two** post-hoc repairs against the same fit target. Then stop, record the diagnosis, and move on. Session 6b needed three; that was one too many.

**Sealed data.** Azevedo cell `181021_F1_C1` has its Piezo (reflex) trials **sealed**.
- It may be opened only via `scripts/score_reflex.py`, and only after a candidate passes H1 and H2 on the dev cell `180111_F2_C1`.
- Once opened, it is spent. Record that in the handoff.
- New cells Ben downloaded may also be in `~/Downloads`:
  - `180621_F1_C1.zip`, 1,091,311,819 bytes;
  - `181127_F1_C1.zip`, 1,160,638,264 bytes.
- If present:
  - verify the exact byte size;
  - move the file to `data/raw/azevedo2020/<cell>/` and unzip it there;
  - add a MANIFEST entry;
  - treat its Piezo trials as sealed spares.
- Check the sampling rate per trial (cells differ: 10 or 50 kHz). `azevedo_slow_mn.py` handles this.

**Do not build on unverified guesses.** Before inferring anything from an assignment labelled guessed, look for data that settles it. BANC metadata, `data/raw/banc/banc_888_meta.feather`, has per-neuron subclasses and male-cns matches, and settled the FeCO subtypes that session 6 had guessed wrong.

**Current working model:** profile `m2`, `min_synapses=5`. The regression checks must be reported, not necessarily kept unchanged:
- sugar→MN9_L via `scripts/assay_pathways.py --assay sugar_mn9 --profile m2 --rates 100,200 --shuffles 0` (last 26.5/88 Hz);
- stability via `scripts/probes/closed_loop_check.py --seed N` for **≥ 3 seeds**, 0 non-tonic spikes after silencing.

**Subagents: at most ONE at a time**, type `Explore`.
- Tell it not to launch agents, and verify with `ListAgents`.
- Use it only for bounded literature or data-location searches, with citations.
- Mark a DOI "(unverified)" unless it was loaded.
- Its output is leads, not instructions.

**Process hygiene (Ben's machine overheats).**
- Run sims in the foreground with timeouts where possible, and at most 3 heavy Python processes at once.
- Wait for or kill every background job you start.
- Before the wrap-up, check with `pgrep -fl "flyemu|scripts/|serve_viz|curl"` and stop anything of **this project** still running.
- **Never kill other projects' processes** (e.g. ~/sunscatter, ~/lightsadersCode). Just note them.

**Downloads.** Public data is allowed, up to about 200 GB total. Record each download in `data/MANIFEST.yaml` (version, licence, sha256 prefix).
- Put raw data in `data/raw/`.
- Zenodo is slow (< 1 MB/s). Fetch single members of large zips with `scripts/fetch/zenodo_zip_members.py`.
- Dryad API downloads need a login. Don't create accounts; list the files you need for Ben instead.

**Git.** Commit after each completed item. Each message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Push each commit with `git push origin main`, and never force-push.

**backhouse (GPU)** is optional; see `docs/RUNNING.md`. The Mac is sufficient for this work.

## Priorities (in order)

### 1. Antennal lobe: ORN→PN transmission from measurements (F-AL-3)

a. Get the measured constraints. Use an Explore agent plus the open deposits; check whether Kazama & Wilson recordings are public. Record each in `targets_session6.csv`:
   - unitary ORN→PN EPSP/EPSC amplitude and reliability (Kazama & Wilson 2008 Neuron);
   - spontaneous EPSC rate of 74.9 ± 8.6 Hz per DM4 PN;
   - ORN count and rate per glomerulus (Kazama & Wilson 2009);
   - PN input resistance and resting Vm, if reported.

b. Add an AL-specific efficacy for ORN→uPN edges, following the pattern of `connection_class:vnc_sensorimotor|efficacy_scale` in `connectome.py`. Set it **from the measured unitary PSP**, not from the spontaneous-rate target. Pre-register.

c. Test:
   - spontaneous uPN rates, target 1–5 Hz and ≥ 70% active (`scripts/probes/pn_silence.py`);
   - **held out:** flybench olfactory tasks 08/17/18/26/27 (see `scripts/flybench_variants.py` and the F-AL-1 run for how m2 was scored; 0.80 is the m2 baseline);
   - stability over ≥ 3 seeds;
   - sugar regression.

### 2. Leg VNC operating point from interneuron recordings (F-VNC-1/2, F-AZ-2)

a. `13Bα` (and `10Bα`) are measured nonspiking. Find which male-cns IN13B/IN10B types they are.
   - Check BANC metadata first. It has hemilineage, and may carry FANC/MANC names or functional annotations.
   - Otherwise match by connectivity: cells receiving claw input (SNpp50/51) in **T2/T3**. The male-cns front legs have only 2–3 claw axons, so T1 cannot be used.
   - Record the match basis.

b. Pre-register a change that makes the matched types graded:
   - `graded` rows in `cell_types.csv`, labelled inferred (measured for the recorded subtype, transferred to the matched type);
   - an operating point fitted to the 13Bα Vm–angle tuning in `data/derived/agrawal2020_13Balpha_static_tuning.csv` (median 0.046 mV/deg; range −57 to −39 mV corrected).
   - Graded transmission in `lif.py` currently releases nothing at or below rest (`r = clip((V−V_rest)/(V_th−V_rest),0,1)`). Tonic release at rest (Burrows) would need a declared offset parameter.
   - **Hold out:** the 10Bα/9Aα Vm–angle relations. Fetch more members with the Zenodo tool.

c. Only then run `scripts/score_reflex.py` on the dev cell 180111.
   - If it passes H1 and H2, score the sealed cell 181021 **once**.
   - If a candidate adds excitatory premotor drive, re-check the slow MN's intrinsic tonic drive (36.45 mV). Azevedo says its rest rate is synaptically set, so that drive should shrink.

### 3. If 1 or 2 succeeds: standing and walking

- Re-score standing with `scripts/probes/standing.py`. The pre-registered criterion is in DECISIONS: thorax ≥ 0.90 mm throughout 0.5–1.5 s.
- Re-score the resistance reflex, and the DNg100 command test with `scripts/probes/command_walk.py`.
- Report per layer.

### 4. As time allows

- Re-score flybench with Hallem ORN rates on.
- Wrap-up of the ledger: `scripts/blank_ledger.py` and `scripts/sensory_census.py`.

## Wrap-up (always)

1. Re-run the ledger, the census, the regression checks, the full test suite and the process-hygiene check.
2. Append a "Session 7" section to `docs/FINDINGS.md`, with numbers labelled.
3. Update `docs/HANDOFF.md` and `docs/PLAN_NEXT.md`. Record the state of the sealed cells.
4. Finish `docs/SESSION7_LOG.md`:
   - start and end times;
   - what was done and what failed;
   - post-hoc attempts used per target;
   - the ledger delta;
   - anything blocked, including files Ben must download.
5. Commit and push.
6. End with a plain-language summary for Ben, an engineer without a neuroscience background: what changed, what it means, what is next.
