# BAAIWorm files vendored here

Source: https://github.com/Jessie940611/BAAIWorm, commit b99ca5a (fetched 2026-11-05). Licence: Apache 2.0
(`LICENSE`, unchanged). Paper: Zhao M., Wang N., Jiang X. et al. (2024) An integrative data-driven model simulating
C. elegans brain, body and environment interactions. Nature Computational Science 4, 978-990.

Copied unchanged, only the directories renamed:

| here | upstream |
|---|---|
| `mod/` | `eworm/components/mechanism/modfile/` (23 NMODL files) |
| `cell_param/` | `eworm/components/param/cell/` (302 neurons, 96 muscles, `MuscleCell.json`, `template.json` placeholder) |
| `connection/` | `eworm/components/param/connection/` (Cook 2019 SI 5 adjacency, neuron-muscle and muscle-neuron flags) |
| `model/` | `eworm_learn/components/model/` (NEURON hoc morphologies, 302 neurons + 96 muscles + `MuscleCell.hoc`; the neuron files are byte-identical to `eworm/components/model/`) |
| `config.json` | `eworm/network/config.json` (136-neuron cell list, construction constants `cnt_info`) |

Used by `scripts/worm/build_ledger.py` (every BAAIWorm number in the worm ledger is parsed from these files) and by
the NEURON brain. Not vendored: their Python package (run from a clone on backhouse), the trained trial10 weights
(not adopted, see docs/worm/BRAIN_PORT.md), the CNN muscle readout, MetaWorm body and Unity code.
