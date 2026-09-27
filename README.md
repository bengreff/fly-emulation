# Biologically constrained fly emulation

A *Drosophila* brain–body simulation. The male-CNS connectome (neuPrint `male-cns:v1.0`, 167,111 neurons) drives a flybody MuJoCo fly in closed loop, with no controller, decoder or prescribed gait. Every model quantity is read through a registry that labels it **measured**, **derived**, **inferred** or **guessed**. The measurable unknowns are counted in a blank ledger.

**The programme: construct a fly.** Build every mechanism that plausibly matters for behaviour, from receptors through the CNS to motor units, muscles and body mechanics. Represent every quantity the connectome does not fix as a biologically bounded unknown. Validate the body with the brain dead. Then construct the brain by search against measured physiology, and judge it on held-out data. Simulate more rather than less: which mechanisms make behaviour emerge is itself the result. Plan: [docs/CONSTRUCTION.md](docs/CONSTRUCTION.md). What sessions 1–8 established: [docs/LESSONS.md](docs/LESSONS.md). Current state: [docs/HANDOFF.md](docs/HANDOFF.md).

## Quick start

```bash
uv sync
uv run python scripts/fetch_male_cns.py     # once; needs a neuPrint token in ~/.config/flyemu/neuprint_token
uv run pytest tests -q
uv run python scripts/run_organism.py --duration-ms 200 --set 'motor_unit:all|force_per_spike=10'
uv run python scripts/serve_viz.py          # browser replay of the newest recording
```

More commands, regression checks and data rebuilds: [docs/RUNNING.md](docs/RUNNING.md).

## Documentation map

| File | Read for | Kind |
|---|---|---|
| [CLAUDE.md](CLAUDE.md) | goals and scientific requirements | stable |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | how work is done: sessions, labels, pre-registration, data splits, hygiene, review checklist | stable |
| [docs/CONSTRUCTION.md](docs/CONSTRUCTION.md) | **the plan**: mission, principles, the complete-fly template, the data model of bounded unknowns, acceptance tests, task list | living |
| [docs/LESSONS.md](docs/LESSONS.md) | the applicable findings of sessions 1–8 | reference |
| [docs/research/](docs/research/) | fidelity research (what a fly needs, per behaviour), transcriptome sources | reference |
| [docs/HANDOFF.md](docs/HANDOFF.md) | **current state**, sealed-data register, pitfalls | rewritten each session |
| [docs/PLAN_NEXT.md](docs/PLAN_NEXT.md) | next work (points to CONSTRUCTION.md) | rewritten each session |
| [docs/NEXT_SESSION_PROMPT.md](docs/NEXT_SESSION_PROMPT.md) | prompt for the next unattended session | rewritten each session |
| [docs/MODEL.md](docs/MODEL.md) | the model's equations, mechanisms and defaults | living |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | code, data and test layout | living |
| [docs/RUNNING.md](docs/RUNNING.md) | commands | living |
| [docs/INTERFACE.md](docs/INTERFACE.md) | brain–body channel inventory and literature | living |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | machines | living |
| [docs/FINDINGS.md](docs/FINDINGS.md) | results from session 9 on (sessions 1–8 archived) | append-only |
| [docs/DECISIONS.md](docs/DECISIONS.md) | decisions and pre-registrations from session 9 on (sessions 1–8 archived) | append-only |
| [docs/PROJECT.md](docs/PROJECT.md), [docs/RESEARCH.md](docs/RESEARCH.md), [docs/VALIDATION.md](docs/VALIDATION.md) | scope, sources, validation principles | reference |
| `docs/SENSORS_*.md`, `docs/MOTOR_TARGETS.md` | literature leads for senses and muscles | reference |
| [docs/archive/](docs/archive/) | superseded plans, the original brief, old handoffs and session logs | historical |
