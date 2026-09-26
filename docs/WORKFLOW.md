# Workflow

How work is done on this project, attended or unattended. `CLAUDE.md` states the goals and scientific requirements; this file states the procedure. Where they overlap, `CLAUDE.md` wins; an active user instruction overrides both.

Each rule exists because its absence cost something. The session that taught it is cited.

## 1. Cadence

| Unit | Length | Who | Output |
|---|---|---|---|
| **Session** | ≤ 5 h unattended, or any length attended | Claude | log, commits, FINDINGS section, updated HANDOFF |
| **Review** | ~10 min, between sessions | Ben | answers to the review checklist (§10); next session's prompt |
| **Milestone** | when a pre-registered criterion passes or a layer is replaced | both | a DECISIONS entry that names what is now trusted |

Unattended sessions longer than about 5 hours are not recommended. The failure mode is not stalling but compounding: a confident chain of work built on an unchecked premise (session 6: guessed sensor subtypes carried two sessions of inference).

The fix is a review at decision points, not frequent status reports.

## 2. Session lifecycle

**Start**
1. Run `date` and create `docs/SESSION<N>_LOG.md` with the start time.
2. Read, in order: `CLAUDE.md`, this file, `docs/HANDOFF.md`, the newest FINDINGS and DECISIONS sections, and the prompt (`docs/NEXT_SESSION_PROMPT.md` if unattended).
3. Run `uv run pytest tests -q`. It must pass before anything is changed.
4. Check the machine:
   - `pgrep -fl "flyemu|scripts/|serve_viz|curl"` shows nothing left over from this project;
   - `ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'` if GPU work is planned.

**During**
- Work the priorities in order.
- Check `date` before each new task, and stop starting new work 20 minutes before the limit.
- Do not stop early because one experiment failed. Record it and move to the next priority (session 6 stopped at 1 h 40 m of 3 h).
- Commit after each completed item; see §8.

**End: wrap-up (always, even if stopped early)**
1. Run the full test suite, the regression checks (§6), the ledger (`scripts/blank_ledger.py`) and the census (`scripts/sensory_census.py`).
2. Process hygiene: stop every process this project started (§7).
3. Append a FINDINGS section; update HANDOFF, including the **unverified-foundations list** and the **sealed-data register**; update PLAN_NEXT; finish the log.
4. Commit and push.
5. End with a plain-language summary for Ben: what changed, what it means, what is next.

## 3. Evidence labels

Every quantity in code, tables, the registry and reports carries one label:

| Label | Meaning | Required with it |
|---|---|---|
| measured | observed directly | source and location (figure/table); uncertainty |
| derived | computed from measurements by a stated method | inputs and method |
| inferred | fitted, borrowed, or estimated with justification | justification, uncertainty |
| guessed | a placeholder so the model runs | why this value |
| unknown / absent | no value / mechanism not simulated | none |

Rules:
- **Labels never upgrade.**
  - A fitted value is inferred.
  - One recorded cell's value applied to a class is inferred for the class.
  - A literature number is measured only once someone has read the source for it. Agent reports are leads.
- `Registry.validate()` returns `[]`, and the table tests in `tests/test_repo_hygiene.py` pass, before any commit.
- **Filling a blank** means adding a labelled row to a table in `data/params/`, or a registry entry. Then re-run the ledger.

## 4. Experiments

### 4.1 Pre-register before scoring

Write the entry in `docs/DECISIONS.md` **before** running anything that is judged:

```
### Pre-registration: <change> (<date time>)
Change: <mechanism, parameters, labels, registry keys>
Motivation: <evidence; say "post-hoc" if it came from inspecting a failure>
Fit set: <exact data used to set any value; the statistic>
Held out: <exact data used only for testing; confirm it is unseen>
Criteria: <numbers and thresholds, fixed now>
Adoption: <what must pass for it to become the default; otherwise option, off>
Expectation (optional): <what you predict, written now>
```

Append the result under the same heading, **including failures**, with the numbers. A change that fails stays in the code as an option, off by default. Parameter rows that were tested and rejected go to `data/params/hypotheses_not_adopted.csv`, never into the live tables.

### 4.2 Data splits: fit, dev, held out, sealed

- **Fit:** used to set values. It becomes "seen".
- **Dev:** seen data, used to reject candidates cheaply before a real test. Passing on dev is not evidence.
- **Held out:** declared unseen before a test. It is spent once scored.
- **Sealed:** raw data deliberately left unopened for a future test.
  - It is opened only by a scorer that runs the model first (e.g. `scripts/score_reflex.py`).
  - It is opened only after the candidate passes on dev.
  - The register of sealed data lives in HANDOFF. Update it whenever something is opened.

Tag every entry of `data/measurements/` with its status in the `use` column.

### 4.3 Post-hoc budget

After a pre-registered test fails, at most **two** post-hoc repairs may be tried against the same fit target, each pre-registered. Then stop fitting that target. Record the diagnosis (which layer fails, with numbers) and move on (session 6b tried three).

The log records how many post-hoc attempts each target has used.

### 4.4 Do not build on unverified foundations

Before inferring anything from a value or assignment labelled guessed or inferred, spend a bounded search on data that could settle it:
- existing tables and caches;
- BANC, MANC and FlyWire annotations;
- open deposits;
- one Explore agent.

Session 6 guessed which male-cns types were claw, hook and club. Two sessions of inference rested on it. BANC metadata settled it in minutes, and most guesses were wrong.

HANDOFF keeps an **Unverified foundations** list: every guessed or inferred item that later work depends on, and what would settle it. It is reviewed every session.

### 4.5 Controls and noise

- A single run is an anecdote. Stochastic results need ≥ 3 seeds; stability claims need ≥ 3 seeds (session 6: one seed hid a self-sustaining state).
- A response needs a no-stimulus control run through the same windows (session 6: a "reflex" was noise).
- Check units and sampling rates per file (session 6c: a 50 kHz cell read as 10 kHz).

## 5. Data acquisition

Public data is allowed, up to about 200 GB in total.
- Raw files go in `data/raw/` (git-ignored).
- Each gets a `data/MANIFEST.yaml` entry: source, version or DOI, licence, sha256 prefix, and what it is used for.
- Record the exact file size of downloads Ben makes, and verify it on arrival.

Access routes:
- **Slow Zenodo archives:** fetch single members with `scripts/fetch/zenodo_zip_members.py`.
- **Dryad API:** needs a login. Do not create accounts; list the exact files for Ben, with sizes.
- **Credentials:** the neuPrint token lives outside the repo (`~/.config/flyemu/`). Never commit tokens.

## 6. Regression checks (report every session)

| Check | Command | Current reference |
|---|---|---|
| Sugar → MN9_L | `uv run python scripts/assay_pathways.py --assay sugar_mn9 --profile m2 --rates 100,200 --shuffles 0` | 26.5 / 88 Hz |
| Closed-loop stability | `uv run python scripts/probes/closed_loop_check.py --seed N`, N = 0, 1, 2 | 0 non-tonic spikes after silencing; brain ~0.3–0.4 Hz |
| Tests | `uv run pytest tests -q` | all pass |

A change may move the reference numbers. Report the move; do not hide it.

## 7. Compute and process hygiene

Ben's Mac overheats and is shared with other projects.
- Run simulations in the foreground with timeouts where possible. Run at most 3 heavy Python processes at once.
- Wait for or stop every background job you start. Long-lived servers (`serve_viz.py`) are stopped when you are done.
- Before wrap-up, run `pgrep -fl "flyemu|scripts/|serve_viz|curl"` and stop only this project's processes.
- **Never kill other projects' processes** (e.g. `~/sunscatter`, `~/lightsadersCode`). Report them to Ben.
- backhouse (GPU, WSL2): see `docs/RUNNING.md`. Keep a `sleep infinity` session attached or WSL kills jobs, and stop it afterwards.

## 8. Git and agents

**Git**
- Commit after each completed item with a descriptive message ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Push after each commit. Never force-push or rewrite history. If a commit message is wrong, say so in the log.

**Agents**
- The agent cap is set in `CLAUDE.md` (three attended, one unattended, never an agent type that can spawn agents).
- Instruct it not to launch agents, and verify with `ListAgents`.
- Its output is leads: unverified DOIs are marked, and numbers are re-read before being labelled measured.

## 9. Documentation ownership

Each fact lives in one place. Other files link to it rather than restating it.

| File | Owns | Nature |
|---|---|---|
| `CLAUDE.md` | goals and scientific requirements | stable |
| `docs/WORKFLOW.md` | procedure (this file) | stable |
| `README.md` | what the project is, quick start, doc map | stable |
| `docs/PROJECT.md` | objective and scope | stable |
| `docs/ARCHITECTURE.md` | code structure and data flow | living, current state |
| `docs/MODEL.md` | model equations and mechanisms, with defaults | living, current state |
| `docs/INTERFACE.md` | brain-body channels | living, current state |
| `docs/RUNNING.md`, `docs/ENVIRONMENT.md` | how to run; machines | living |
| `docs/HANDOFF.md` | **current state**, unverified foundations, sealed-data register, next step | rewritten each session |
| `docs/PLAN_NEXT.md` | ranked next experiments | rewritten each session |
| `docs/NEXT_SESSION_PROMPT.md` | the next unattended session's prompt | rewritten each session |
| `docs/FINDINGS.md` | results, append-only, newest last | historical |
| `docs/DECISIONS.md` | decisions and pre-registrations with results, append-only | historical |
| `docs/SESSION<N>_LOG.md` | timeline of one session | historical |
| `docs/SENSORS_*.md`, `docs/MOTOR_TARGETS.md`, `docs/RESEARCH.md`, `docs/VALIDATION.md`, `docs/LIT_*.md` | reference material and literature leads | reference |
| `docs/archive/` | superseded plans | historical |
| `scripts/probes/README.md` | which probes are current | living |

Historical files are never edited to match the present; they record what was believed then. Living files must be true now. `tests/test_repo_hygiene.py` checks that every path a living doc mentions exists.

## 10. Review checklist (Ben, about 10 minutes per session)

Read the top of `docs/HANDOFF.md` and the session's final summary. Then ask:
1. **Foundations:** does any new result rest on an item in the unverified-foundations list? Is there data that could settle it?
2. **Labels:** is anything called measured that was fitted, borrowed or transferred?
3. **Splits:** was any held-out or sealed data opened? Was it opened by the rules?
4. **Post-hoc:** how many repairs were tried per failed target?
5. **Downloads:** does the handoff list files only Ben can fetch?
6. **Direction:** is the next priority still the most useful one?
7. **Machine:** is anything left running?
