# s26 fly2: measured resting activity of mushroom-body DANs, per compartment (22 Oct 22:45)

One web search by a read-only search agent (fly2 s26b, the Director's option (b), 22 Oct). The numbers were read from
the papers by the agent and **have not been re-checked by fly2**; re-check before using one as a value. Exclusions held:
Huang et al. 2024 (held out) was not opened; from Berry, Phan & Davis 2018 only non-Fig-5 material was eligible and
nothing usable was found there. Cell names: MP1 = PPL1-γ1pedc, MV1 = PPL1-γ2α'1, V1 = PPL1-α'2α2.

| DAN / compartment | Quantity | Value | Method, state | Source | Kind |
|---|---|---|---|---|---|
| PPL1-α'2α2 (V1) | spontaneous spike rate | about 6-10 /s, stable over the first 10 days | voltage imaging (Ace2N-2AA-mNeon), head-fixed, tethered, alert | Huang et al. 2018 Nat Commun 9:872, Fig 6b,e | **spike rate, measured** |
| PPL1-α'3 | spontaneous spike rate | "stationary" over a 4-day baseline; no Hz in the text read | voltage imaging, as above | Huang et al. 2018, Fig 7i | spike rate, magnitude not read |
| PPL1-γ1pedc (MP1), PPL1-γ2α'1 (MV1) | ongoing calcium activity | significantly above zero (p < 0.0001, n ≥ 20); no number | GCaMP3, 2 Hz confocal, awake, restrained | Berry et al. 2012 Neuron 74:530, Fig 5C | calcium proxy |
| PPL1-α'2α2 (V1) | ongoing calcium activity | not different from zero (p ≥ 0.245, n ≥ 17) | GCaMP3, as above | Berry et al. 2012, Fig 5C-D | calcium proxy |
| MP1, MV1 | slow calcium oscillation | about 0.10 and 0.29 Hz (power-spectrum fits); which cell has which is unverified | calcium imaging, naive, immobilised | Plaçais et al. 2012 Nat Neurosci 15:592 | calcium proxy; **unverified** (secondary summaries only; primary not opened) |
| PAM-γ4/γ5, PPL1-γ2/γ3 | ongoing fluctuation | robust, alternating with quiescence and flailing; no Hz | sytGCaMP6s, 2-photon, tethered | Cohn, Morantte & Ruta 2015 Cell 163:1742, Fig 2D-E | calcium proxy, qualitative |
| PAM/PPL1 α3, α'1, γ1, γ2, γ3 | pre-stimulus activity | significant, odour-independent; no Hz | GCaMP, 2-photon, immobilised | Siju et al. 2020 Curr Biol 30:2104, Fig 1I | calcium proxy, qualitative |
| all DANs (TH-Gal4) | activity at rest | "surprisingly little activity during resting or grooming"; strong increase with walking | light-field GCaMP6f, tethered | Aimon et al. 2019 PLoS Biol 17:e2006732, Fig 2A | calcium proxy, qualitative |
| PAM-γ4/γ5 | quiescent fluctuation | "minimal motor-associated fluctuations in the dark" | GCaMP, 2-photon, walking on a ball | Zolin et al. 2021 Nat Neurosci 24:1555, Fig 1C | calcium proxy, qualitative |

Nothing usable: Mao & Davis 2009 and Riemensperger et al. 2005 (evoked responses only).

**Reading (fly2, inferred):**
- PPL1-α'2α2 is the only compartment with a measured resting spike rate.
- Calcium quiet does not mean spike quiet. Berry 2012's GCaMP3 found PPL1-α'2α2 indistinguishable from zero, while Huang 2018's voltage imaging finds the same cell type spiking at 6-10 Hz. So the qualitative "little activity at rest" reports (Aimon 2019, Zolin 2021) can't place any compartment near N21's 0.0015 Hz bound (F-S26-1).
- Resting spike rates for five PPL1 types exist in Huang 2024, which is held out (fly's resting fit).
