# Biologically constrained fly emulation

> ## Current state, 16 September 2026
>
> **Read [docs/HANDOFF.md](docs/HANDOFF.md) first.** It is the entry point for
> a new session and says what to do next and why.
>
> **There is a whole organism and it runs.** 176,422 neurons and 25,862,574
> connectome edges from `male-cns:v1.0` drive a MuJoCo fly body in a closed
> loop at a 0.1 ms timestep. Joint angles, foot contact, transmitted load and
> per-eye luminance come back in through the real afferent populations. No
> controller, no prescribed gait, no descending command. It falls over and
> thrashes, which is the expected result with guessed parameters.
>
> **The body is now measured, not assumed.** The body model is **flybody**,
> chosen on evidence (see `docs/DECISIONS.md`): masses from 52 weighed flies,
> 102 joint ranges fitted to real poses, differentiated passive joint
> parameters, self-collision, tarsal adhesion, tendons and quasi-steady
> aerodynamics. 0.985 mg, 98 torque actuators, 963 us per step.
>
> **The gate, and the most important fact in the project.** A 16x change in
> every synapse in the animal moves the firing rate less than 4x. A 2.5x change
> in the background noise term moves it 400x. **The connectome is not yet doing
> the work** - the term standing in for everything the model omits is. Until
> that changes, nothing downstream is evidence, and an optimiser pointed at
> behaviour would tune a parameter with no biological referent. See F-GAIN-1.
>
> **The parameters are guesses, and the model says so itself.** Every
> biological quantity is read through a registry recording what it is, which
> equation needs it, its units, its provenance and how many model elements it
> fills. The inventory is emitted by a run rather than maintained beside it.
> **19 distinct inferences fill 27.5 million model elements**; every neuron in
> the brain shares one membrane time constant.
>
> | Read this | For |
> |---|---|
> | [Handoff](docs/HANDOFF.md) | what to do next |
> | [Model family M](docs/MODEL_M.md) | the equations, the grain, what M omits |
> | [Findings](docs/FINDINGS.md) | every result, newest at the bottom |
> | [Interface](docs/INTERFACE.md) | the brain-body channel inventory |
> | [Decisions](docs/DECISIONS.md) | what was chosen and why |
> | [Running](docs/RUNNING.md) | how to run everything |
> | [Environment](docs/ENVIRONMENT.md) | measured hardware, two-machine setup |

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
