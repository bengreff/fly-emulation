"""k2p_leak (UNC-58) skips cells whose whole membrane is a published model (wbrain2, 9 Nov 2026): Jiang's AVL and
DVB, Naudin's AFD and Liu's AWA were fitted to wild-type recordings, so their leak already holds the cell's own.
On today's CeNGEN none of those classes detects unc-58, so a stub brain in which every class does is the test."""
import types

import numpy as np

from wormemu.mech import k2p_leak

CELLS = ["AWAL", "AWAR", "AVL", "DVB", "AFDL", "AFDR", "AIYL"]


def _stub():
    cls = ["AWA", "AVL", "DVB", "AFD", "AIY"]
    st = types.SimpleNamespace(gene_index={"unc-58": 0}, cengen_classes=cls, tpm=np.ones((1, len(cls))))
    return types.SimpleNamespace(st=st, cell_names=CELLS, is_muscle=[False] * len(CELLS))


def _names(toggles):
    return {CELLS[i] for i in k2p_leak.cells_expressing(_stub(), toggles)}


def test_k2p_skips_swapped_membranes():
    assert _names({"awa_membrane": "baaiworm"}) == set(CELLS)                       # no swaps: every cell
    assert _names({}) == set(CELLS) - {"AWAL", "AWAR"}                              # Liu's AWA is the default
    swap = dict(avl_membrane="jiang22", dvb_membrane="jiang22_noexp2", afd_membrane="naudin22")
    assert _names(swap) == {"AIYL"}
