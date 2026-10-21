# Premotor hemilineages outside the Pugliese core: a literature scan for the third family (s17, 21 Oct 2026)

Sonnet subagent (Explore, web), 21 Oct 03:2x CDT. **I have not checked any of it.** The agent's own labels are kept: "quote checked in full text" means the agent says it read the full text; "abstract only" and "secondary" mean less. Two sources were new to the project and look recent (Sapkal et al. 2026 bioRxiv; Guan et al. arXiv 2609.38665). Check their existence and the quoted claims before using any row. Purpose: rank the hemilineages for next session's connectome query (HANDOFF "Next", item 2). Nothing here sets a value.

| Hemilineage | Evidence type | Finding (as the agent reports it) | Citation | Agent's label |
|---|---|---|---|---|
| 13A, 13B | MANC connectome + optogenetics | About 120 GABAergic neurons per leg. The 13A cells that inhibit flexors and the ones that inhibit extensors are reciprocally connected. Pulsed activation at about 7-8 Hz drives flexion-extension alternation; silencing locks the legs flexed | Lesser et al. 2024 Nature (numbers); Syed, Ravbar, Simpson, Jovanic, eLife (grooming; bioRxiv 2024.06.05.597468) | Lesser: abstract only. Syed: full text |
| 13A, 13B in walking | Optogenetic silencing during walking | Silencing 13A **did not change the extension-flexion cycle frequency in walking**; only small postural effects on the front legs. The circuit's demonstrated function is grooming | Syed et al., eLife | full text |
| 19A | MANC connectome + simulation | 19A local cells give inhibitory antiphase coupling within a leg, and 19A intersegmental cells give antiphase coupling between adjacent segments. These pathways get direct DN and proprioceptor input | Sapkal, Kumar, Sunke, Mancini, Pitchford, Murakami, Bidaye 2026, bioRxiv | full text |
| 19B | Connectome + simulation | 19B commissural cells carry left-right alternation through excitatory coupling | Sapkal et al. 2026 | full text |
| 16B, 19A (the core's I1, I2) | Connectome-constrained simulation | 13A/13B get input from 03A, 04B, 16B and 19A, and project back onto 16B. So 16B and 19A sit between the core oscillator and the 13A/13B antagonist module | Pugliese et al. 2025 bioRxiv | full text |
| 03A, 04B | MANC | 13A input comes mostly from 03A, plus 04B/16B/19A | Takemura 2024 / Marin 2024 via search synthesis | secondary |
| No single hemilineage | Rewiring/ablation on MANC + FANC leg networks | Real wiring coordinates antagonists better than rewired networks, through network-wide reciprocal innervation. Cutting the 13A/13B motif reduced coordination no more than size-matched random cuts | Guan, Zhao, Zhang, Lyu, Chen, arXiv 2609.38665 | full text |
| DNg97 (oDN1), DNg74 | Simulation | The core cells also get direct input from DNg97/oDN1 and DNg74 (and the grooming DNs DNg12, DNg62/aDN1) | Pugliese et al. 2025 | full text |
| Rhythm without feedback | Behaviour, amputated or deafferented legs | Single DNs (DNg100, DNg97, MDN) drive stepping rhythms with legs amputated or sensory input removed. Each leg has its own CPG module, whose intrinsic period shows when proprioceptive feedback is reduced | Sapkal et al. 2026 | full text |

- Harris et al. 2015 eLife (hemilineage activation): local hemilineages give uncoordinated leg movement, intersegmental ones coordinated walking-like movement. It names no rhythm-generating hemilineage (abstract only).
- **Not found:** a per-hemilineage percentage of premotor input to T1 leg MNs. The Cheong 2024 and Lesser 2024 numbers are behind paywalls.

**Agent's ranking for the query:** (1) 19A and 19B; (2) 16B beyond I1, plus 03A and 04B; (3) 13A/13B; (4) the T1 targets of DNg97/oDN1 and DNg74.

**Bearing on s17 (if the sources hold):** Sapkal 2026 says the walking rhythm is central and survives deafferentation, which argues against feedback as the *missing* piece. The model's S2 harness is already deafferented, so the fly's analogue of our test is "rhythm present without feedback". Feedback would shape the period, not create the alternation.
