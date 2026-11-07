"""NEURON helpers shared by the organ and muscle mechanisms: compile and load src/wormemu/nmodl/organs/*.mod (once,
into $WORMEMU_NRNMECH_ORGANS or ~/.cache/wormemu/nrnmech_organs/<hash>) unless the brain's own build already has them,
and set a soma up for a whole-cell (nS, pF) mechanism."""
from __future__ import annotations

import glob
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ORGAN_MODS = Path(__file__).resolve().parents[1] / "nmodl" / "organs"


def density_mechanisms(h) -> set:
    """Every mechanism name this NEURON knows (density and point processes)."""
    s, out = h.ref(""), set()
    for kind in (0, 1):
        mt = h.MechanismType(kind)
        for i in range(int(mt.count())):
            mt.select(i)
            mt.selected(s)
            out.add(s[0])
    return out


def load_organ_mods(h):
    """Load the organ mods into this NEURON (no-op if every one is already a known mechanism)."""
    mods = sorted(ORGAN_MODS.glob("*.mod"))
    have = density_mechanisms(h)
    suffixes = [_suffix(m) for m in mods]
    if all(s in have for s in suffixes if s):
        return h
    tag = hashlib.sha1(b"".join(m.name.encode() + m.read_bytes() for m in mods)).hexdigest()[:12]
    d = Path(os.environ.get("WORMEMU_NRNMECH_ORGANS", Path.home() / ".cache" / "wormemu" / "nrnmech_organs")) / tag

    def find():
        libs = glob.glob(str(d / "*" / "libnrnmech.*")) + glob.glob(str(d / "*" / ".libs" / "libnrnmech.so"))
        return libs[0] if libs else None
    lib = find()
    if lib is None:
        (d / "src").mkdir(parents=True, exist_ok=True)
        for m in mods:
            shutil.copy(m, d / "src" / m.name)
        exe = shutil.which("nrnivmodl") or str(Path(sys.executable).parent / "nrnivmodl")
        with open(d / "build.log", "w") as log:
            subprocess.run([exe, "src"], cwd=d, check=True, stdout=log, stderr=subprocess.STDOUT)
        lib = find()
    h.nrn_load_dll(lib)
    return h


def _suffix(mod: Path) -> str:
    for line in mod.read_text().splitlines():
        w = line.split()
        if len(w) >= 2 and w[0] in ("SUFFIX", "POINT_PROCESS"):
            return w[1]
    return ""


def area_um2(sec) -> float:
    return float(sum(seg.area() for seg in sec))
