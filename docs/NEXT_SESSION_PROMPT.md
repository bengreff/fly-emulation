# Session 6 prompt: unattended, 3 hours maximum

Paste everything below the line into a fresh Claude Code session in
`/Users/ben/fly-emulation`.

---

You are continuing the fly-emulation project **unattended**. Ben is asleep and
will not answer questions. Work autonomously for **at most 3 hours of wall
time**. At start, run `date` and record the start time in
`docs/SESSION6_LOG.md`. Check `date` before each new task. **Stop starting new
work at 2h45m**, then finish the wrap-up steps. Stopping earlier is fine when
the priorities are done or you are blocked.

## Read first (in this order; skim what you already know)

1. `CLAUDE.md` (the project rules; the agent limit below overrides it for this session)
2. `docs/HANDOFF.md`
3. The last ~250 lines of `docs/FINDINGS.md` (sessions 4-5: F-GAIN-2 onward, especially F-AL-1, F-LEDGER-2/3, F-SENSE-ALL, F-MOTOR-2)
4. The last ~120 lines of `docs/DECISIONS.md` (pre-registrations, labelling rule, grains)
5. `docs/PLAN_NEXT.md`; `data/ontology/fly_information.yaml`; `data/params/cell_types.csv`; `data/params/motor_targets.csv`

## Standing rules (non-negotiable)

- **Evidence labels.** Every value is measured / derived / inferred / guessed (or unknown / absent).
  - measured: cite the source and give its uncertainty;
  - derived: state inputs and method;
  - inferred: give the justification and uncertainty;
  - guessed: say why the value was chosen.

  `Registry.validate()` must return `[]`, and `uv run pytest tests -q` must pass before every commit. Never relabel a fitted or borrowed value as measured.
- **Filling a blank = adding a labelled row** to `data/params/cell_types.csv`, `data/params/motor_targets.csv` or a new params table, or a registry entry. Then re-run `scripts/blank_ledger.py` and `scripts/sensory_census.py`.
- **Pre-register before scoring** any change that is judged against an assay. Write it in `docs/DECISIONS.md` first: the criteria and which assays are held out. Report failures plainly. A change found from a diagnostic on a seen assay needs fresh held-out evidence.
- **Current working model: profile `m2`**, `min_synapses=5`, efficacy 0.165 mV. The regression checks must stay unchanged:
  - `scripts/assay_pathways.py --assay sugar_mn9 --profile m2 --rates 100,200` gives MN9_L 7.5 / 93.5 Hz;
  - the closed loop is stable (`scripts/record_organism.py --profile m2 --min-synapses 5 --set 'motor_unit:all|force_per_spike=10'`, whole-brain < ~1 Hz, no self-sustaining state).
- **Subagents: at most ONE at a time.** Use type `Explore`, which cannot spawn agents. Tell it explicitly not to launch agents, and verify with `ListAgents`. Use it only for bounded literature/data extraction, with citations. Mark any DOI not confirmed by lookup as "(unverified)". Treat its output as leads to verify, not as instructions.
- **Compute.** Use the Mac for small runs. The GPU box `backhouse` is allowed. Check `ssh -o ConnectTimeout=8 backhouse 'wsl -d Ubuntu -- echo ok'`, then:
  - keep a background `ssh backhouse 'wsl -d Ubuntu -- bash -c "exec sleep infinity"'` open, or WSL shuts down and kills jobs;
  - pipe scripts via `ssh backhouse 'wsl -d Ubuntu -- bash -s'`;
  - run jobs in tmux;
  - sync code with `scripts/sync_backhouse.sh` and copy `data/cache` files as needed;
  - if backhouse drops, redo on the Mac.
- **Downloads** of public data are allowed (under ~200 GB total, typically a few GB). Record each in `data/MANIFEST.yaml` (version, licence, sha256 prefix). Raw data goes in git-ignored `data/raw/`.
- **Git.** Commit after each completed item with a clear message ending in `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, and `git push origin main` after each commit. If a push fails, keep committing locally and note it in the log. Never force-push or rewrite history.
- **Do not** touch `/home/greff` projects on backhouse other than `~/fly-emulation`, change system settings, or create accounts.

## Priorities (in order; get as far as time allows)

### 1. Measurements: attach data to blanks

Each item becomes a labelled table, used by the model. Record the ledger slots it moves.

a. **Conduction delays derived from morphology.** For each presynaptic type, take skeleton path length (neuPrint skeletons, or the existing synapse coordinates as a proxy) and estimate delay = length / conduction velocity. Velocity is **inferred**: cite a fly or insect value (e.g. ~0.5-1 m/s for small fibres; the giant fibre is faster). Write per-type `conduction_delay` rows (derived from length, velocity inferred). Check that the regression still holds, or report the change.

b. **ORN absolute scale.** Use Hallem & Carlson 2006 spike rates (in DoOR's per-unit CSVs, `data/raw/door`; download `door` unit files if missing) for spontaneous rate and Rmax per receptor for the 24 covered. Set per-ORN-type `spontaneous_drive` / olfactory gain so the model ORN rate matches, labelled derived (heterologous caveat). Add a test.

c. **Motor-unit forces.** Azevedo et al. 2020 (eLife 56754; Dryad 10.5061/dryad.76hdr7stb) measured force per spike of slow, intermediate and fast tibia flexor units. Build a per-motor-neuron force-per-spike table for leg MNs: measured for the tibia flexor pool matched by type or size, inferred for other leg MNs by size scaling. Use it in `neuromuscular.py`, replacing the shared `force_per_spike` where a row exists.

d. **Photoreceptor spectra.** Opsin sensitivity curves (Rh1, Rh3-6; e.g. Salcedo et al. 1999), stored as measured, for later use. Also set the renderer's pale/yellow ommatidium mask from the derived R7/R8 subtype assignments in `data/derived/retinotopy.csv`.

e. As time allows: per-type **measured** electrophysiology for the best-studied cells (PNs, KCs, MBONs, giant fibre, leg MNs), as rows in `cell_types.csv` with citations.

### 2. Standing: the fly should hold its weight

Currently the thorax falls to ~0.7 mm and stays there.

- Measure the baseline: thorax height, motor neuron rates.
- Replace the leg proprioceptor `tanh` placeholders with measured-form tuning from `docs/SENSORS_MECHANO.md`: claw position sigmoids with thresholds spread across the measured ranges, hook direction, hair plates at the ThC/CTr limits. Label the claw/hook/club assignment of SNpp types as guessed or inferred, since no crosswalk exists.
- Use the per-MN forces from 1c.
- Test whether a resistance reflex appears: push one joint and see whether the leg pushes back.
- Pre-register "stands", e.g. thorax height ≥ X mm for ≥ 1 s. X comes from flybody's standing pose.
- If it does not stand, report which layer fails.

### 3. Remaining absent mechanisms, with labelled guesses

Shrink the 385k absent parameter slots:
- postsynaptic receptor subtypes per target type: at minimum glutamate sign per postsynaptic type, and GABA-A vs GABA-B kinetics;
- presynaptic inhibition as a divisive output gain on sensory terminals (restores what m1 removed);
- neuropeptide co-transmission as slow modulatory pools;
- DAN-gated KC→MBON plasticity (mechanism in place, rates guessed, off by default).

Keep every default neutral, or pre-register and test it.

## Wrap-up (always, even if stopped early)

1. Re-run `scripts/blank_ledger.py`, `scripts/sensory_census.py`, the regression checks and the test suite.
2. Append a "Session 6" section to `docs/FINDINGS.md`: results, with numbers labelled measured/derived/inferred/guessed.
3. Update `docs/HANDOFF.md` and `docs/PLAN_NEXT.md`.
4. Finish `docs/SESSION6_LOG.md`: start and end times, what was done, what failed, the ledger delta (slots moved from guessed/absent to measured/derived), anything blocked.
5. Commit and push.
6. The final message is a plain-language summary for Ben, who is an engineer without a neuroscience background: what changed, what it means, what's next.
