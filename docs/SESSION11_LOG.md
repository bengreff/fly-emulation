# Session 11 log

Start: Wed 30 Sep 2026 16:59 CDT. Directed by the Director (Ben's authority). Budget ~6-8 h.
Mode: Mac-only (backhouse unreachable: ssh timed out at 17:00). Heavy processes at most 2, each through `~/director/harness/slot.py`.

## Timeline

- 16:59 start; read worker rules, CLAUDE.md order, NEXT_SESSION_PROMPT. backhouse ssh timeout.
- 17:00-17:09 start test suite (slot limiter): 147 passed, 9 m 23 s.
- 17:05 ledger v3: every ontology row names its mechanism (mech) and the grain its value varies at (fidelity); source levels measured > derived > rule > prior > mixed > guessed > absent; reconciled with mechanisms.yaml (13 rows moved absent -> default where session 10 built lumped mechanisms; count_basis/quoting fixes); 3 new per-cell/per-edge rows (within-type excitability, per-cell offsets, per-edge unitary efficacy). Baseline: runs/s11/ledger_start.txt.
- 17:06 Sonnet Explore agent: Azevedo 2020 / Tobin 2017 numbers for the within-type size rule.
- 17:10 per-cell within-type rule (src/flyemu/percell.py; three registry keys, neutral 0, bit-identical test); hemilineage transmitter rule (LOTO 0.989 cells at purity >= 0.9, baseline 0.584; 817 unclear cells fillable; switch connectome:unclear|nt_by_development, neutral 0); Özel 2021 receptor calls (65 types; 12 new live GluCl sign rows; agreement with Davis 0.556).
- 17:13 m7 pre-registered (general alpha 1.0 + motor 1.49). 17:16 fail: sugar->MN9_L 0.5 Hz; MN9_R under-traced (633 vs 6,358 inputs) lowered MN9_L's gain.
- 17:20 repair 1 (completeness guard) pre-registered; 17:30 dev fail 1.8 Hz. 17:34 attribution: general alpha alone 1.8 Hz, motor alpha alone 6.9 Hz.
- 17:37 repair 2 (motor alpha only) pre-registered. Director interrupt killed the runs; relaunched 17:37.
- 17:45 VNC rhythm probe pre-registered (DNg100, spiking vs graded vnc_local). Route note drafted (docs/ROUTE_TO_BEHAVIOUR.md). Sonnet agent: Allen 2020 VNC atlas glutamate-receptor calls by hemilineage.
- 17:47 repair 2 passes; m7 adopted (commit 5b22c0e). 17:52 rhythm probe: no rhythm in spiking or graded arms (excess < 0.05).
- 17:57 rhythm arm (c) graded + adaptation 3 mV/150 ms: no driven rhythm (excess <= 0.06).
