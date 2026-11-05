"""Worm body: ported published bodies (MetaWorm/BAAIWorm eworm first), 95 body-wall muscle names, the body ledger.

Owned by the body worker; contract with the brain in docs/worm/INTERFACE.md. Every body number comes from the body
rows of the ledger (`data/worm/ledger/metaworm_parameters.csv`, loaded by `ledger.BodyLedger`), labelled with its
source. Our own rod (2026-11-05) is archived in archive/worm/rod_own/ (Ben 15:05: port, don't write physics).
"""
from .ledger import BodyLedger  # noqa: F401
