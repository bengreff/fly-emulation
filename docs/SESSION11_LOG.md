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
- 17:45 VNC rhythm probe pre-registered (DNg100, spiking vs graded vnc_local). Sonnet agent: Allen 2020 VNC atlas glutamate-receptor calls by hemilineage.
- 17:47 repair 2 passes; m7 adopted (commit 5b22c0e). 17:52 rhythm probe: no rhythm in spiking or graded arms (excess < 0.05).
- 17:57 rhythm arm (c) graded + adaptation 3 mV/150 ms: no driven rhythm (excess <= 0.06).
- 18:02 walking failure localisation pre-registered (recruitment, afferents off, synthetic tripod replay). 18:13 result: two layers fail (DNg100 adds only +0.7 Hz to leg MNs; replayed bursts give no stepping at 10/20 Hz, partial at 5 Hz). Allen agent finished: all 21 hemilineages mixed (committed 81868f5).
- 18:19-18:43 tethered diagnostics: joint share at the drive frequency 0.82 at 2 Hz, 0.057 at 10 Hz, 0.056 fast units only; torque share at 10 Hz 0.54. The body low-passes a delivered 10 Hz torque.
- 18:44 m8 leg damping 0.043 (FlyMimic c/k 0.05 s) pre-registered; 18:47 mechanism check fails (0.094), not adopted; key `joint:leg|damping` wired, neutral 0.
- 18:49 joint-limit occupancy and force-velocity-off diagnostics pre-registered; 18:50 band-limited (3-50 Hz) share added before any run finished.
- 18:55-19:02 damping 0.043 (+/- force-velocity) raises the 10 Hz amplitude 1.7x / 2.6x (under 3x); 5 mm tether shows ground contact is not the clamp. Key `joint:leg|damping` redefined as a multiplier, neutral 1 (full suite had failed on the 0 sentinel).
- 19:05-19:10 body-only probe (`scripts/probes/joint_impedance.py`): the bare body follows 10 Hz once damping is low (femur-tibia 1.8 rad p2p at 1.5 µN·mm).
- 19:12-19:15 activation-depth arms (twitch decay 15 ms 2.0x, fused rate 300 Hz 1.15x): neither reaches 3x.
- 19:22-19:26 per-pair readout: coxa-trochanter front/hind swing at stepping scale; femur-tibia extensor works at force-length gain 0.1-0.3. Cause found: s9 placed every muscle optimum at the flybody zero pose.
- 19:28 optimum join by interior segment angle built (`muscle:leg|optimum_join`, neutral 0). 19:29 m8 = m7 + join pre-registered (the name m8 reused: the 18:44 damping candidate was not adopted).
- 19:32 m8 fails (torque 1.12x vs 2x; extensor FL 0.44 vs 0.5); not adopted. Readout: tonic co-activation ~0.65 on both femur-tibia muscles, flexor wins, joint sits 0.5-0.97 rad past the extensor optimum. Diagnostic replays at 40 Hz MN rate running.
- 19:42 corrected reading: the +1 (FlyMimic extensor) muscle wins, 10:1 capacity. Azevedo 2020 read: flexor ~100 µN at a 417 µm lever, >= 42 µN·mm vs the model's 1.04. Key `muscle:leg|ft_flexor_scale` (row b4_ft_flexor_scale, neutral 1).
- 19:48 m8 = m7 + flexor scale 40 pre-registered; 19:56 fails (swing 0.098 vs 0.10; joint pins at flexion). Closed loop seed 0 silent.
- 19:56 size-ordered replay pre-registered; 20:01 no help: the joint runs to the stronger muscle's end under any comparable drive. Then a resistance-reflex physiology probe.
- 20:35 Director correction: walking diagnostics closed (findings kept, switches neutral); ROUTE_TO_BEHAVIOUR removed; direction re-locked to the 09-28 ledger/fill plan; FIDELITY_LADDER next.
- 20:47 rung 1 built and committed (745ef6e): channels module, expression tables (82 types + 21 hemilineages), single-cell tests; milestone M1/G1/G2 pre-registered.
- 21:12 rung 1 scored: M1 8.9x (bar 2x), G2 sugar -> MN9_L 1.7 Hz (bar 5); not adopted, switch neutral. Diagnosis: SK via the guessed Ca pool cuts rates 3-4x; subthreshold channels move rheobase only 0.95-1.11x. Two repairs pre-registered (SK coupling from recorded current steps; cost by tables/GPU). Stopped here per the Director (stop after the first implementation milestone).
- 21:17-21:20 Ben's answers recorded; repair 1 and revised adoption pre-registered; threshold deviation logged before fitting.
- 21:40 spike-channel fit, 4 seeds: best seed 3 loss 1.03 (LIF only 2.1-2.4, priors 2.9-3.8); BK and θ identified, SK/Ca not (F-RUNG1-2).
- 21:3x GPU port of the channels: toy exact; whole CNS m8 300 ms on backhouse equal per cell (sugar and broad).
- 21:47 G1 seeds 12-13 silent (m8 and m7); sugar -> MN9_L 2.7 Hz (m7 re-run 6.9); m8 adopted as working profile. Full suite 164 passed.
- 22:01 joint re-search of class gains + central size rule pre-registered (fit seeds 14-16, held out 17-19).
- 22:47 screen (12 candidates) collected: all silent; best combined candidate MN9 11.4 Hz, J 3.09.
- 23:35 phase 2 (14) and 00:04 phase 3 (8) collected: 42 candidates in total, all silent; best DN 0.85, MN_other input 1.6, gust 1.25, exponent 1.0 (MN9 5.7 Hz, J 1.19).
- 00:27 held out on that candidate: seeds 17-19 silent, bitter suppression, dose response and bitter alone all pass; m9 adopted as working profile. Suite 164 passed; m9 reproduces the held-out trials exactly.
- 00:45: rung 2 pre-registered.
- 01:00: Gate A passed (whole CNS: GPU equals CPU on m10p). Gate B at priors failed: not silent, 81-98 spikes/ms. Ablation traced it to the mAChR peak share.
- 01:06: repair 1 (charge basis) pre-registered.
- 01:18: under repair 1, seeds 20-22 silent but sugar 0 Hz; Gate C pre-registered.
- 01:30: first Gate C launch OOM-killed on backhouse (WSL VM full from another distro); moved to a staged Mac screen (amendment at 01:34).
- 02:37: Gate C done, 30 candidates, best 0.7 Hz. Rung 2 not adopted.
- 02:44: diagnostics. Conductance synapses block sugar at GNG108, hop 2 (F-R2-1). Recording `docs/media/m9_closed_loop.mp4`, 3 s.
- 02:49: fill from recordings pre-registered (e_inh -56, threshold reference, medulla rests). 03:01: m10q silent on seeds 26-28, sugar 2.4 Hz; not adopted. Suite 171 passed.
- 03:23: m10q class-gain search pre-registered (24 candidates, inh_cond_scale added). 03:47: closed loops moved to the Mac (backhouse full). 04:33: 12 of 24 scored; 3 silent on seeds 29-31; c008 leads (J 3.68, MN9 8.1 Hz); c012-c023 running detached on backhouse.
