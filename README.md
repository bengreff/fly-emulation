# Biologically constrained fly emulation

> ## Current state, 15 September 2026
>
> **Read [docs/PLAN.md](docs/PLAN.md) first.** It is the plan for the next
> session and it supersedes the milestone sequence in `docs/ROADMAP.md`.
>
> **The approach changed after session 1.** That session built and audited one
> isolated subsystem, the front-leg premotor network of the nerve cord. It could
> not produce both a rhythm and usable motor force across 333 simulations, and
> that was reported as a property of the approach. It was not. The fragment was
> deafferented and open-loop, so everything that normally sets a premotor
> circuit's operating point was missing: descending drive, sensory context,
> neuromodulator state. A part was being asked to do the whole animal's job.
>
> **The new first task is a whole-organism field inventory.** Enumerate every
> quantity the organism needs, at per-cell-type grain for physiology and
> per-neuron for structure, and mark each one measured, derived, fitted, assumed
> or empty. Find out how much of a fly we actually have before simulating any of
> it. Then build a scaffold whose only job is to fail loudly on missing fields,
> and a control that runs on measured values alone.
>
> **What session 1 did establish**, restated at field level in
> [docs/FINDINGS.md](docs/FINDINGS.md): the motor-neuron to muscle mapping is
> complete and independently corroborated; 41% of modelled inhibition rests on a
> sign convention the connectome cannot settle; the sign field is wrong for most
> leg proprioceptors; excitability is derived from a volume that is invalid for
> input populations; afferent firing rates have no published calibration at all;
> and the whole-CNS connectome is a far better source than the nerve cord alone,
> 94% traced against 23%.
>
> | Read this | For |
> |---|---|
> | [Plan](docs/PLAN.md) | what to do next and why the approach changed |
> | [Findings](docs/FINDINGS.md) | which fields are filled, wrong, or empty |
> | [Decisions](docs/DECISIONS.md) | what was chosen and why |
> | [Environment](docs/ENVIRONMENT.md) | measured hardware, two-machine setup |
> | [Running](docs/RUNNING.md) | how to reproduce what remains |

---

# Original handoff brief

Repository starter brief • research compiled 14 September 2026

Build an increasingly faithful simulation of the Drosophila brain, body and environment, constrained by anatomical measurements, physiological research and observed behavior. The long-term aim is an organism able to live a fly-like life: sense, move, select behaviors, adapt, learn and retain memories. Walking is the first whole-body milestone; flight follows. Agreement with actual biological data is the main success criterion.

This pack is a specification and research handoff, not a working simulator. It supersedes earlier conversational plans requiring zero behavioral fitting, permanently fixed connectivity, or recovery of the scanned animal's identity. It contains no downloaded biological datasets or pretrained controllers.

## Use in a repository

Copy these files into the project repository, preserving the `docs/` directory. In an existing repository, merge `CLAUDE.md` with existing instructions rather than blindly overwriting them. Claude should read:

1. [CLAUDE.md](CLAUDE.md) — concise working instructions.
2. [Project](docs/PROJECT.md) — user decisions, scope and scientific claims.
3. [Research](docs/RESEARCH.md) — source map, useful assets, caveats and corrections.
4. [Architecture](docs/ARCHITECTURE.md) — model components and fitting methods.
5. [Validation](docs/VALIDATION.md) — evidence tracking, evaluation and experiment records.
6. [Roadmap](docs/ROADMAP.md) — initial work and progressive milestones.

Suggested first message to Claude Code:

> Read CLAUDE.md and the linked project documents. Treat PROJECT.md as the current user scope, and the research notes as evidence leads with explicit verification limits. Inspect this repository and the available hardware, then begin the first executable milestone in ROADMAP.md. Make implementation decisions autonomously within the existing permission workflow. Preserve biological constraints, record assumptions, and produce a small measured result before broad infrastructure. Continue through routine obstacles and keep progress reviewable.

## Current resources and decisions

- NVIDIA RTX 4070 Super; Mac and Windows available. Inspect actual VRAM, system RAM, storage and software environment. Do not assume the Mac has CUDA or that Windows tooling is automatically compatible.
- This remains alongside the user's propulsion research. No fixed weekly hours or cloud budget have been specified.
- Primary connectome, specimen sex, body platform and numerical backend are deliberately undecided. Choose through evidence and small benchmarks.
- Full autonomy for research and implementation, using Claude Code's existing permission workflow. This pack creates no additional approval process.
- Optimization of uncertain biological quantities using behavior is authorized. Neural/muscle mechanisms must remain biologically meaningful and consistent with the wider literature within justified uncertainty.
- Learning and realistic dynamic connectivity are permitted. Implement supported mechanisms when needed; do not add arbitrary rewiring merely to improve a score.

## Status of this handoff

Papers, release pages and selected source code were reviewed. Large physiological arrays have not been fully inspected, no end-to-end runtime was benchmarked, and no fly behavior was generated in this preparation. Historical numerical estimates are not empirical measurements. Start by turning the most important accessible evidence into runnable component tests.
