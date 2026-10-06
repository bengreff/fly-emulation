# Working instructions

Read first, every session: `docs/HANDOFF.md` (current state; rewrite it each session, don't append), the newest
entries of `docs/DECISIONS.md` and `docs/FINDINGS.md`, and the approved scope brief
`/Users/ben/director/logs/night-2026-10-06/briefs/fly-scope.md` (Ben's locked order and the per-value bar).
`README.md` has the full documentation map if more context is needed.

## Objective

Whole-CNS spiking model on the male-cns v1.0 connectome, with a MuJoCo flybody body. Ben's order: (1) a full set
of blanks, an accurate body and brain, and fidelity rungs up to synapse-specific; (2) development models; (3) many
flies; (4) a reconstruction study. Progress is the ledger fill fraction and the fixed behaviour scoreboard (see
HANDOFF and the scope brief). Never tune toward a behaviour; "fit to recordings, then test walking" as a method is rejected.
The per-value bar is "consistent with SOME fly of this species" (inside the measured range, source cited), not
this specimen's exact value.

## Standing rules

- Label every quantity **measured / derived / inferred / guessed**; never relabel a fitted value as measured.
  Record provenance, units, conditions, uncertainty and derivation.
- **Pre-register** before scoring: objective, held-out split, falsifier, written down first.
- New switches and mechanisms are **neutral by default** (off / unity) until adopted; adoption needs a gate, a
  battery run, and a viewed figure.
- Validate on held-out observations; spend held-out/sealed evidence only once; keep the sealed/held-out register
  (HANDOFF) current. Behavioural success alone is not evidence of correct internal physiology.
- Preserve identified biological pathways end-to-end; every abstraction states its validity range.
- Preserve raw data and pin dataset/model versions. Don't optimize hidden state to encode future target
  behaviour, and don't let unobserved world-state bypass the sensory models.
- Don't treat claimed completeness percentages, counts or sizes as fact without checking the actual inclusion
  policy.
- **At most 3 subagents at a time, counted recursively; never an agent that can spawn its own subagents.**
- Keep a CPU reference path for any new mechanism; port to GPU only once it matches the CPU path on a check.
- Run `date` immediately before writing any timestamp into logs or decisions , estimates drift ahead.
- Stop background runs/servers you started before ending a session; never touch another project's processes.
- The neuPrint token lives at `~/.config/flyemu/neuprint_token`. Never read, print or copy it.
- Work autonomously within the existing permission workflow; ask Ben only for what only Ben can decide.
