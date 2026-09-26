# Biologically constrained fly emulation

A *Drosophila* brain–body simulation. The male-CNS connectome (neuPrint `male-cns:v1.0`, 167,111 neurons) drives a flybody MuJoCo fly in closed loop, with no controller, decoder or prescribed gait. Every model quantity is read through a registry that labels it **measured**, **derived**, **inferred** or **guessed**. The measurable unknowns are counted in a blank ledger.

**Current state (session 6c, 26 September 2026).**
- The body, senses and motor units are increasingly set from data.
- The fly does not yet stand. Its leg reflex and antennal-lobe spontaneous activity fail for the same reason: relay neurons sit silent below threshold under one borrowed, brain-wide synaptic strength.
- The next work sets transmission from measurements, one circuit at a time.

Details: [docs/HANDOFF.md](docs/HANDOFF.md).

## Quick start

```bash
uv sync
uv run python scripts/fetch_male_cns.py     # once; needs a neuPrint token in ~/.config/flyemu/neuprint_token
uv run pytest tests -q
uv run python scripts/run_organism.py --duration-ms 200 --set 'motor_unit:all|force_per_spike=10'
```

More commands, regression checks and data rebuilds: [docs/RUNNING.md](docs/RUNNING.md).

## Documentation map

| File | Read for | Kind |
|---|---|---|
| [CLAUDE.md](CLAUDE.md) | goals and scientific requirements | stable |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | how work is done: sessions, labels, pre-registration, data splits, hygiene, review checklist | stable |
| [docs/HANDOFF.md](docs/HANDOFF.md) | **current state**, unverified foundations, sealed-data register | rewritten each session |
| [docs/PLAN_NEXT.md](docs/PLAN_NEXT.md) | ranked next experiments | rewritten each session |
| [docs/NEXT_SESSION_PROMPT.md](docs/NEXT_SESSION_PROMPT.md) | prompt for the next unattended session | rewritten each session |
| [docs/MODEL.md](docs/MODEL.md) | the model's equations, mechanisms and defaults | living |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | code, data and test layout | living |
| [docs/RUNNING.md](docs/RUNNING.md) | commands | living |
| [docs/INTERFACE.md](docs/INTERFACE.md) | brain–body channel inventory and literature | living |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | machines | living |
| [docs/FINDINGS.md](docs/FINDINGS.md) | every result, with an index at the top | append-only |
| [docs/DECISIONS.md](docs/DECISIONS.md) | decisions and pre-registrations with results | append-only |
| [docs/PROJECT.md](docs/PROJECT.md), [docs/RESEARCH.md](docs/RESEARCH.md), [docs/VALIDATION.md](docs/VALIDATION.md) | scope, sources, validation principles | reference |
| `docs/SENSORS_*.md`, `docs/MOTOR_TARGETS.md`, `docs/LIT_SESSION6.md` | literature leads for senses, muscles and physiology | reference |
| [docs/archive/](docs/archive/) | superseded plans, the original brief, old handoffs and session logs | historical |
