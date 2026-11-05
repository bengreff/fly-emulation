# Archived: own planar rod body (2026-11-05)

Our own overdamped Kirchhoff rod with Boyle-Berri-Cohen 2012 numbers. Archived on Ben's direction (2026-11-05
15:05 CST): port published bodies (MetaWorm/BAAIWorm eworm; a published rod model's code if a fast body is
needed) instead of writing our own physics. It was not a faithful port of any published code.
Test results: docs/worm/BODY_TESTS.md. To rerun, copy rod.py back into src/wormemu/body/ and restore the
`Body, BodyConfig` import in src/wormemu/body/__init__.py.
Its ledger moved here too (body_parameters.csv, body_mechanisms.json, build_body_ledger.py; paths inside still
point at data/worm/ledger/). The live body ledger is data/worm/ledger/metaworm_parameters.csv; it reuses this
ledger's literature rows (water viscosity, agar drag, density, tissue moduli).
Ben 15:30 (5 Nov): 3D body only, drop the rod entirely. muscles.py (the rod's muscle-over-joint coverage) moved
here too; drive.py and gait.py were already here and their duplicates in src/wormemu/body/ were removed. To
rerun the rod, copy rod.py, muscles.py, drive.py and gait.py back into src/wormemu/body/.
