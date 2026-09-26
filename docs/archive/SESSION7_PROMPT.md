# Session 7 prompt: unattended, 5 hours maximum

Paste everything below the line into a fresh Claude Code session in `/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben will not answer questions.

## Before anything else

1. Run `date` and create `docs/SESSION7_LOG.md` with the start time.
2. Follow `docs/WORKFLOW.md` exactly. It is the procedure, and this prompt only adds the session-specific parts:
   - the session lifecycle;
   - evidence labels;
   - the pre-registration template;
   - the fit / dev / held-out / sealed splits;
   - the **post-hoc budget of two repairs per target**;
   - the unverified-foundations rule;
   - controls with ≥ 3 seeds;
   - process hygiene;
   - git.
3. Read the rest:
   - `docs/HANDOFF.md`: current state, **unverified foundations**, **sealed-data register**;
   - `docs/PLAN_NEXT.md`;
   - `docs/MODEL.md`;
   - `docs/RUNNING.md`;
   - `docs/FINDINGS.md` from "# Session 6" to the end (the index is at the top);
   - `docs/DECISIONS.md` from "## Session 6" to the end.
4. Run `uv run pytest tests -q`. It must pass.

## Session-specific rules

**Time**
- At most **5 hours** of wall time. Check `date` before each task.
- Stop starting new work at **4h40m**, then do the wrap-up in WORKFLOW §2.
- Do not stop early because one experiment failed; move to the next priority.

**Agents:** at most **one** Explore subagent at a time (the `CLAUDE.md` unattended cap).

**Ben's downloads**
- These may be in `~/Downloads`:
  - `180621_F1_C1.zip`, 1,091,311,819 bytes;
  - `181127_F1_C1.zip`, 1,160,638,264 bytes.
- If present:
  - verify the exact size;
  - move and unzip each to `data/raw/azevedo2020/<cell>/`;
  - add MANIFEST entries;
  - record them as **sealed spares** in the HANDOFF register.
- Do not open their Piezo trials.

**The working model** is the default of every run script (`docs/MODEL.md`). Report the regression checks in WORKFLOW §6.

## Priorities (in order)

### 1. Antennal lobe: ORN→PN transmission from measurements (F-AL-3)

a. **Constraints.** Collect the measured values below, with one Explore agent plus open deposits (check whether the Kazama & Wilson recordings are public). Add each to `data/measurements/targets_session6.csv` with its `use` status:
   - unitary ORN→PN EPSP/EPSC amplitude and reliability (Kazama & Wilson 2008);
   - spontaneous EPSC rate of 74.9 ± 8.6 Hz per DM4 PN;
   - ORN counts and rates (Kazama & Wilson 2009);
   - PN input resistance and resting Vm.

b. **Change.** Pre-register an ORN→uPN efficacy scale, following the pattern of `connection_class:vnc_sensorimotor|efficacy_scale` in `src/flyemu/connectome.py`. Set it **from the unitary PSP**, not from the spontaneous-rate target.

c. **Test:**
   - spontaneous uPN rate 1–5 Hz with ≥ 70% active (`scripts/probes/pn_silence.py`);
   - held out: flybench olfactory tasks 08/17/18/26/27 (m2 baseline graded 0.80; see F-AL-1 and `scripts/flybench_variants.py`);
   - regression checks.

### 2. Leg VNC operating point (F-AZ-2, F-VNC-1/2)

a. **Identify 13Bα and 10Bα** among male-cns IN13B/IN10B types. Check BANC metadata first (`data/raw/banc/banc_888_meta.feather`: hemilineage, FANC/MANC matches, functional annotations); otherwise use claw input from SNpp50/51 in **T2/T3** (front-leg claw axons are missing). Record the match basis and its label.

b. **Pre-register graded operation for the matched types:**
   - `graded` rows in `data/params/cell_types.csv`, labelled inferred;
   - an operating point fitted to `data/derived/agrawal2020_13Balpha_static_tuning.csv` (median 0.046 mV/deg; −57 to −39 mV);
   - tonic release at rest needs a declared offset parameter in the graded code of `src/flyemu/lif.py`;
   - held out: the 10Bα/9Aα Vm–angle relations (fetch members with `scripts/fetch/zenodo_zip_members.py`).

c. **Score the reflex:**
   - run `scripts/score_reflex.py --cell 180111_F2_C1 --tag <name>` (dev);
   - only if H1 and H2 pass, score the sealed cell 181021_F1_C1 **once** and update the register.

d. If premotor excitation now exists, revisit the slow MN's intrinsic tonic drive (Azevedo: its rest rate is synaptic).

### 3. If 1 or 2 passes: standing and walking

Re-score with `scripts/probes/standing.py` (criterion pre-registered in DECISIONS) and `scripts/probes/command_walk.py`. Report per layer.

### 4. As time allows

- Re-score flybench with the Hallem rates on.
- Look up measured resting potentials of central neurons, to replace the borrowed −52 mV.

## Wrap-up

Follow WORKFLOW §2 "End". In addition:
- rewrite `docs/HANDOFF.md` (not append), including the unverified-foundations list and the sealed register;
- rewrite `docs/PLAN_NEXT.md`;
- write the next `docs/NEXT_SESSION_PROMPT.md`;
- in the log, record the post-hoc attempts used per target and any files Ben must download.

End with a plain-language summary for Ben, an engineer without a neuroscience background.
