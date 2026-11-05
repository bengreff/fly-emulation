# What the worm model adopts from other projects and datasets (brain and ledger side)

Ben's order (5 Nov): mechanisms drawn heavily from existing projects, ported wholesale and run as published first.
This file credits every outside source the brain (`src/wormemu/brain.py`, `brain_layers.py`) and the ledger
(`data/worm/model`, built by `scripts/worm/build_ledger.py`) take numbers or code from, with the licence as stated at
the source. The body, viewer and video side (worktree `wormbody`) adds its own rows.

Licence column: as stated at the source when fetched; "not stated" means checked and no licence found; "not
recorded" means nobody has checked yet. Check before redistributing anything outside this repo.

## Code

| Source | What we use | How | Licence |
|---|---|---|---|
| **BAAIWorm** (Zhao, Wang, Jiang et al. 2024, Nature Computational Science 4:978; github.com/Jessie940611/BAAIWorm commit b99ca5a) | 23 NMODL channel, Ca pool, synapse and gap files; per-cell passive values and channel densities for 302 neurons and 96 muscles; NEURON morphologies; construction constants; its wiring construction (`wiring=baaiworm`) | vendored unchanged in `third_party/baaiworm/` (NOTICE.md lists the files); `brain.py` builds their cells and reproduces their own run to 0.0 mV (BRAIN_PORT.md section 3, R1). Their numbers are labelled `published_fit` | Apache 2.0 (`third_party/baaiworm/LICENSE`) |
| **OpenWorm c302** 0.12.1 | parameters_C2 muscle channel set (28 values) | parsed into the ledger as `published_fit`, source c302; the `muscle_active` toggle (off; not yet wired into NEURON) | MIT (LICENSE in the installed dist-info) |
| **pyNeuroML / jNeuroML** 1.3.22 / 0.14.0 | ran c302 as published (C2 IClamp config, `docs/worm/research/c302_port.md`) | run on backhouse only; nothing vendored | LGPL-3 |
| **NEURON** 9.0.2 | the simulator `brain.py` runs on | pip install | BSD-3 (not re-checked here) |
| **Nicoletti et al. 2024** (PLoS ONE 19:e0298105) channel library | 22 channel kinetics in `src/wormemu/nicoletti.py` (Jaxley track, W0/W1); literature ranges for densities and kinetics | transcribed from their .mod files | not recorded |

## Data

| Source | What we use | Licence |
|---|---|---|
| **Cook et al. 2019** (Nature 571:63), wormwiring.org SI 5 | every chemical (3709 pairs, 20,965 synapses) and gap (1091 pairs) neuron pair, 956 neuron-to-muscle pairs, 96 muscle-muscle gap pairs; `wiring=cook` (default since 5 Nov) | "Emmons Lab Copyright (c) 2020"; no further terms stated |
| **CeNGEN** (Taylor et al. 2021, Cell 184:4329), cengen.org thresholded expression | channel presence (`expression_map` toggle), receptor genes for `receptor_sign`, innexin genes for `innexin_identity`, peptide and monoamine release and receptor matrices | not stated |
| **Wang et al. 2024** (eLife 13:RP95402) neurotransmitter atlas, as tabulated by OpenWorm ConnectomeToolbox | transmitter identity of 282 neurons (sign rule) | not recorded |
| **Ripoll-Sanchez et al. 2023** (Neuron 111:3570) neuropeptide connectome | peptide ligand-receptor pairs | MIT (Neuropeptide-Connectome repo) |
| **Beets et al. 2023** (Cell Reports 42:113058) | peptide-receptor pairs at EC50 <= 500 nM (the pair list's inclusion rule); per-pair EC50 values not yet loaded (`pep_ec50_nM` guessed) | open access; licence not independently confirmed |
| **Fenyves et al. 2020** (PLoS Comput Biol 16:e1007974), S1 Data sheet 5 | predicted polarity of every chemical synapse from transmitter and receptor expression; `receptor_sign=on` uses it where it says + or - (1705 of 3709 Cook pairs), our CeNGEN rule elsewhere; the two disagree on 182 of those 1705 | CC BY 4.0 (journal licence) |
| **Bentley et al. 2016** (PLoS Comput Biol 12:e1005283) | monoamine connectome | CC BY 4.0 |
| **OpenWorm CElegansNeuroML** (Virtual Worm geometry) | soma positions, diameters, membrane areas for 302 neurons (`data/worm/structure/geometry.csv`) | not stated |
| **Literature ranges** (`docs/worm/research/param_ranges.csv`, one citation per row) | the bounds every ported value is checked against; literature wins inside `literature_overrides` | per paper |

## Not adopted (and why)

- BAAIWorm's trained trial10 weights: per-synapse fits (our rules exclude per-synapse free knobs), and the trained
  network is not physiological (13 of 65 output cells leave -100 to +60 mV; BRAIN_PORT.md section 1).
- BAAIWorm's CNN muscle readout: a decoder, not a biological mechanism.
- BAAIWorm's 175 muscle-to-neuron synapses: no anatomical basis (Cook has none). They remain only under
  `wiring=baaiworm`.
