# s25 fly2: figure check for the dopamine-only restoration rule (22 Oct 04:10)

One Sonnet read-only agent (foreground), reading the figure images on PMC. "text" = stated in text or legend;
"fig" = read from a plot by the agent (its stated reading error). Not re-checked by fly2. Berry 2018 Fig 5H-I and
Hige 2015 Fig 1H/1J (backward pairing) values are in `docs/research/sealed/s25_restoration_heldout_sealed.md`,
**sealed, unread by fly2**; only their protocols are here.

Figures viewed: Cohn 2015 Figs 5-7 (PMC4732734, nihms-738448-f0006/7/8.jpg); Hattori 2017 Fig 6 (PMC5806120,
nihms938414f6.jpg); Berry 2018 Fig 5 (PMC6239218, nihms-1510873-f0006.jpg); Hige 2015 Fig 1 (PMC4674068,
nihms-736536-f0001.jpg).

## Cohn, Morantte & Ruta 2015 Cell 163:1742 (existence and direction; no per-spike number)

DAN drive is P2X2 + focal ATP (2 mM, a pressure pulse; no spike count, no stated duration). KCs are driven by ACh
iontophoresis in the calyx. Paired means KC and DAN stimulation < 500 ms apart; unpaired means > 45 s apart (text).

| Panel | Readout | Compartment | Result (fig) | n |
|---|---|---|---|---|
| 6A | EPSC, KC-evoked | γ4, DA alone | 2 ± 1 -> 16 ± 2.5 pA | 5 |
| 6B | GCaMP, KC-evoked | γ4, DA alone | 1.0 ± 0.3 -> 2.1 ± 0.7 | 6 |
| 6C | GCaMP | γ2, γ2-DAN alone | 0.5 ± 0.2 -> 6.0 ± 1.5 | 6 |
| 6D, 6E | GCaMP | cross-compartment controls | n.s.; small depression | 6 |
| 7D | GCaMP, odour, in vivo | γ4 | 0.12 ± 0.04 -> 0.45 ± 0.10 | about 6 |
| 7I paired | GCaMP, KC-evoked | γ4 | from the potentiated state, 2.2 ± 0.6 -> 0.4 ± 0.15 | 6 (text) |
| 7I unpaired | GCaMP, KC-evoked | γ4 | **from the depressed state, 0.7 ± 0.2 -> 2.2 ± 0.5** | 12 (text) |

Fig 7G-I interleaves paired and unpaired trials in one preparation. So DA alone **restores a depressed response**
(7I), and from naive it also **potentiates above naive** (6A-C, 7D). The no-P2X2 control (ATP alone, Fig 5C, n 6) is
flat.

## Hattori et al. 2017 Cell 169:956, Fig 6E-F (the per-stimulation rate)

- Suppression: MCH 15 times at a 30 s interval suppresses MBON-α'3 (odour-evoked DA from PPL1-α'3 depresses the
  active KC->MBON-α'3 synapses; text).
- One stimulation is 10 × 50 ms CsChrimson pulses at about 7 Hz (617 nm, 4.8 µW/mm², "calibrated to physiological
  odour-evoked PPL1-α'3 activity"), with no odour (text). The interval between stimulations isn't stated (about 30 s
  inferred).
- Recovery, % (mean of 3 trials, normalised to trials 13-15), fig:

| Stimulations | PPL1-α'3 > CsChrimson | Genetic controls |
|---|---|---|
| 1 | 8 ± 5 | −3 ± 5 |
| 3 | 18 ± 7 | 3 ± 5 |
| 6 | 33 ± 6 | 2 ± 5 |
| 10 | 40 ± 6 | 0 ± 5 |

n is 10 cells from 7 flies (each control 10 cells, 7 and 9 flies; text). The controls get light but no DAN
activation, and they **don't recover** over the same time.

## Berry, Phan & Davis 2018 Cell Rep 25:651, Fig 5H-I (held out; protocol only)

- Cells: DAN-γ2α'1 (MB296B, Chrimson); MBON-γ2α'1 (R25D02-LexA, GCaMP6f, axon, two-photon).
- Odours: 5 s MCH, then 5 s OCT, 45 s between pulses, 15 trials. MCH is CS+.
- **Learn** (trials 3-5): 6 × 1 ms pulses at 2 Hz, from 1 s after MCH onset.
- **Forget** (trials 8-10, Paired>Unpaired): the same train, 22 s before MCH onset.
- **Paired>Decay**: light during Learn only. **No LED**: no light at all.
- Readout: %ΔF/F0 (F0 = 5 s before odour), the mean over the 5 s odour, at Pre, Post 1 and Post 2, for MCH and OCT
  separately. n 8-9 flies per condition. Readable from the figure (reading error 10-20%).

## Hige et al. 2015 Neuron 88:985, Fig 1G-J backward pairing (falsifier; protocol only)

- Cells: MBON-γ1pedc>α/β, in vivo whole-cell; PPL1-γ1pedc (MB320C, CsChrimson, 627 nm, 14.7 mW/mm²).
- Pairing: 4 × 1 ms pulses at 2 Hz, then a 1 s odour (OCT or MCH) 0.5 s after the last pulse; one trial.
- Baseline: 5 (3-10) presentations of each odour, interleaved, 25 s apart. Pairing comes 1 min after them.
- Post: about 5 presentations per odour, from 1-1.5 min after pairing.
- Readout: Fig 1J, odour-evoked spikes in a 1.4 s window (spontaneous subtracted), Pre against Post, raw counts. n 7.
