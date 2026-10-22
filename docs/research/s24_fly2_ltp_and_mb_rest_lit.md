# s24 fly2: KC->MBON potentiation sources and mushroom body resting rates (22 Oct 03:50)

Two web searches by read-only search agents (fly2 s24, after F-S24-2). Their numbers were read from the papers'
text by the agents and have **not been re-checked by fly2**. Re-check a number before using it. "Plot only" means
no number in text or tables; using it would need a figure estimate. Handler 2019 is spent (F-S24-2) and is not
listed.

## 1. KC->MBON potentiation (N21's missing half)

**No paper outside Handler 2019 gives a DAN-induced potentiation size in its text.** Three plotted sources agree on
one point: DAN activity *not* paired with KC activity restores or potentiates KC->MBON transmission. This is a
different rule from the one built. `lif.py` has only Handler-type potentiation: a KC spike during the DA trace,
moving the weight toward the cap (`kc_mbon_ltp_timing_rate`).

| Source | Compartment, method | Protocol | Result | Number |
|---|---|---|---|---|
| Cohn, Morantte & Ruta 2015 Cell 163:1742 (PMC4732734) | γ2, γ4 MBONs; **whole-cell EPSC** to ACh iontophoresis; GCaMP6s | DANs by P2X2 + ATP. Paired (KC/DAN < 500 ms apart) vs unpaired (> 45 s apart) | Paired depresses, unpaired potentiates; both last up to about 1 h; compartment-specific | plot only (Fig 6B-E n 5-6; Fig 7D-E n 6; Fig 7I n 6 and 12). The only source in charge-like units, so it's the best fit target for a potentiation rate |
| Berry, Phan & Davis 2018 Cell Rep 25:651 (PMC6239218) | PPL1-γ2α'1 -> MBON-γ2α'1; GCaMP6f | 5 s odour; 6 pulses 1 ms at 2 Hz. Forgetting: the same trains, unpaired (22 s before odour) | Paired: complete depression. Unpaired DAN trains restore the CS+ response | plot only (Fig 5H-I, n 8-9) |
| Hattori et al. 2017 Cell 169:956 (PMC5806120) | PPL1-α'3 -> MBON-α'3; calcium | Repeated odour suppresses > 80%; then DAN-only stimulations (10 × 50 ms at about 7 Hz), tested after 1, 3, 6 and 10 | Recovery after 6-10 stimulations (a dose-response) | plot only (Fig 6E-F, n 10). In text: a novel odour moved suppression from 100% to 70% |
| Davidson & Hige 2023 eNeuro 10:ENEURO.0275-23.2023 (PMC10616905) | PAM -> MBON-γ5β'2a; GCaMP6f | Reversal: odour B paired, odour A unpaired | The unpaired odour A is potentiated ("recovery") | plot only (Fig 1E-G n 12; boutons Fig 6E, p 0.0037) |
| Yamada, Davidson & Hige 2024 J Physiol 602:2019 (doi 10.1113/JP285745) | γ KC -> MBON-γ1pedc; whole-cell | Dopamine + KC firing (LTD); an sGC agonist + KC firing (LTP) | DA LTD **54.7 ± 8.5%, n 6** (D1-like, PKA). sGC LTP 77.9 ± 11.9%, n 5 (not DAN-driven). DA alone or KC alone: no change | text |
| Hige et al. 2015 Neuron 88:985 (PMC4674068) | γ1pedc; whole-cell spikes | **Backward pairing:** odour 0.5 s after the last of 4 DAN pulses | **No change** (n 7; Fig 1H, 1J). CS− 110 ± 11 -> 83 ± 14 spikes | text |

Also checked, nothing usable: Hancock 2022 Sci Rep (shock, significance only), Aso 2019 eLife (no KC->MBON
physiology), Stahl 2022 eLife (GRAB-ACh, significance only), Pribbenow 2022, Noyes & Davis 2023 (genetics),
McCurdy 2021 (reversal depresses γ5β'2a), Zeng 2023 Neuron 111:1118 (forward-ISI t50 for depression only: 14.7 s
wild type). Receptor assignments disagree: Handler gives Dop1R2 to potentiation, Berry 2018 gives DAMB/Dop1R2 to
forgetting, and in Hattori 2017 DAMB serves the suppression.

**What this means for the model:**
- Handler-type timing potentiation has no numeric source left (Handler is spent). The supported rule is **DAN
  activity without KC coincidence restores the weight toward baseline**, and it has three plotted sources.
- Berry 2012/2018 make forgetting (N22) partly *active*: ongoing DAN activity erases memory. N22 is currently
  passive relaxation (3 h, guessed). A DAN-driven restoration rule would merge the missing half of N21 with a more
  faithful N22. In this model that only matters if DANs fire at rest (section 2).
- **Hige 2015 backward pairing (no change at γ1pedc, ISI 0.5 s after the last pulse) is unspent.** F-S24-2 reported
  it but didn't score it (LTP was off). Any future potentiation rule must pass it: it's the natural falsifier.
- A pre-registration sketch: fit one shared restoration rate to Cohn 2015 Fig 7I (figure estimate, EPSC units);
  hold out Berry 2018 Fig 5H-I (restoration after unpaired trains) plus Hige 2015 backward pairing (must stay
  within ± 10% of no change).

## 2. Mushroom body resting rates

In the m10f3 60 s smoke, KCs, DANs (PAM/PPL1, 340) and MBONs (97) are all at 0 Hz at rest.

| Neuron | Rate | Preparation | Source | How read |
|---|---|---|---|---|
| KC (all classes pooled) | 0.1 ± 0.4 spikes/s; 14 of 71 never fired | in vivo whole-cell | Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734 | text (already in the register as spent) |
| PPL1-α'2α2 (MB-V1) | about 6-10 spikes/s, n 10 flies, stable days 2-10 | in vivo voltage imaging, head-fixed awake | Huang et al. 2018 Nat Commun 9:872 (PMC5830414), Fig 6d-e | text |
| MBON-α3 | 12.1 Hz, n 5 | ex vivo whole-cell, room temperature | Hafez et al. 2023 eLife 12:e77578 | text (already in `s13_intrinsic_ranges.csv`) |
| PPL1-γ1pedc, γ2α'1, α'2α2, α3, α'3m; MBON-γ1pedc>α/β, γ2α'1, α2sc, α'2, α3, α'3m | type-specific spike rates, n 20 per type | in vivo voltage imaging on a ball (walking and resting mixed) | Huang et al. 2024 Nature 634:1141 (PMC11525173), Fig 1d-e; **raw data Zenodo 10998457** | plot only |
| MBON-α2sc; γ1pedc>α/β; β1>α; γ4>γ1γ2 | "quiescence or sparse firing"; "persistent irregular spiking or bursting"; UP/DOWN states | in vivo whole-cell | Vrontou et al. 2021 Curr Biol 31:4911 (PMC8612741) | words only |
| MP1, MV1 (PPL1) | calcium oscillations 0.03-0.3 Hz (event rate, not spikes), 6 of 13 naive flies | GCaMP3 in vivo | Plaçais et al. 2012 Nat Neurosci 15:592 | text |
| PAM (any) | no electrophysiological rate found | | | |

Caveats: the 0.03 Hz KC figure that circulates (Ito 2008) is from *Manduca*, not *Drosophila*. DAN activity
depends on state: it follows walking, flailing, arousal and sleep (Cohn 2015, Berry 2015, Zolin 2021, Siju 2020).

**What this means for the model:** DANs and MBONs at 0 Hz are outside every measured value (PPL1-α'2α2 6-10 Hz,
MBON-α3 12 Hz). This is a resting-state miss, first noted in s13 (HANDOFF "Resting rates fail for the mushroom
body"). It's also why the m10f4 gate can't see N21/N22. The best data source is Huang 2024's raw data on Zenodo
(per-type rates for 5 PPL1 and 6 MBON types, n 20 each). Pin the record version before downloading.
