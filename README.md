# Biologically constrained fly emulation

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
