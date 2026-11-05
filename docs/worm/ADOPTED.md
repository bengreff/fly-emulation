# Adopted code and data (worm)

What the worm model takes from other projects, under what licence, and what we changed. Brain-side entries are
the brain worker's to add; this file starts with the body and viewer (body worker, 2026-11-05).

## Body

| what | source | licence | how used | changes |
|---|---|---|---|---|
| MetaWorm body: tetrahedral mesh (984 vertices, 3341 tets), 96 muscle fibre segments, projective-dynamics FEM solver, quadratic fluid drag and lift, published muscle keys | BAAIWorm, Zhao et al. 2024 Nat Comput Sci, "An integrative data-driven model simulating C. elegans brain, body and environment interactions"; https://github.com/Jessie940611/BAAIWorm commit b99ca5ab | Apache 2.0 (`third_party/metaworm/LICENSE`) | vendored in `third_party/metaworm/sim` and `data`, unchanged; driven headless by `driver/run_body.cpp` | build flags only (`third_party/metaworm/UPSTREAM.md`); the GLUT window and Boost.Python bridge replaced by our driver |
| Soft-body solver lineage | SoftCon: Min, Won, Lee, Park & Lee 2019, ACM TOG 38(6) (SIGGRAPH Asia), as credited by BAAIWorm | within the BAAIWorm repo (Apache 2.0) | through MetaWorm | none |
| Literature values for the body ledger (water viscosity, agar drag, tissue moduli, density, gait means) | Sznitman 2010; Backholm 2013; Fang-Yen 2010; Boyle, Berri & Cohen 2012; Rabets 2014; WormAtlas; Cook 2019 (full citations in `data/worm/ledger/metaworm_parameters.csv`) | facts, cited | bounds and placeholders in the ledger | none |

## Viewer

| what | source | licence | how used | changes |
|---|---|---|---|---|
| three.js r170 (core and OrbitControls) | https://threejs.org, npm three@0.170.0 | MIT (`viewer/worm/vendor/three/LICENSE`) | 3D body and wiring diagram | none |
| Neuron positions | OpenWorm CElegansNeuroML, generatedNeuroML2 soma points | open source (OpenWorm); licence text not checked locally, check before redistributing | wiring diagram layout (`viewer/worm/data/graph.json`) | positions only; labelled inferred (an atlas, not this worm) |
| Chemical, electrical and neuromuscular edges | Cook et al. 2019 Nature 571:63, SI 5 (corrected July 2020) | published data | wiring diagram layers | none |
| Neuropeptide edges | Ripoll-Sanchez et al. 2023 Neuron (short-range network) | published data | wiring diagram layer (off by default) | none; inferred from expression |
| Monoamine edges | Bentley et al. 2016 PLOS Comput Biol | published data | wiring diagram layer (off by default) | none; inferred from expression |

## Not adopted (body), and why

- Our own planar rod (archived, `archive/worm/rod_own/`): written by us, not a port; dropped on Ben's direction
  (5 Nov 15:05).
- Other candidate bodies and the reasons for the choice: `docs/worm/research/PORT_CANDIDATES.md`.
