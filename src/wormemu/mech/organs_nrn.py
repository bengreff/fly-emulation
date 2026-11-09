"""NEURON helpers shared by the organ and muscle mechanisms: compile and load src/wormemu/nmodl/organs/*.mod (once,
into $WORMEMU_NRNMECH_ORGANS or ~/.cache/wormemu/nrnmech_organs/<hash>) unless the brain's own build already has them,
and set a soma up for a whole-cell (nS, pF) mechanism."""
from __future__ import annotations

import glob
import hashlib
import math
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


def d_lambda_nseg(sec, f_hz: float = 100.0, frac: float = 0.1) -> int:
    """NEURON's d_lambda rule (neuronsimulator.org, "Using the d_lambda rule"): the odd nseg that keeps every segment
    within frac x the AC length constant at f_hz, lambda_f = 1e5 sqrt(diam / (4 pi f Ra cm)) um (diam um, Ra ohm cm,
    cm uF/cm2). Set L, diam, Ra and cm first; uniform cylinders only (reads segment 0.5)."""
    lam = 1e5 * math.sqrt(sec(0.5).diam / (4.0 * math.pi * f_hz * sec.Ra * sec(0.5).cm))
    return int((sec.L / (frac * lam) + 0.9) / 2) * 2 + 1


def chem_synapse(b, pre, post_seg, g_nS, inh, kind, muscle=False):
    """One chemical synapse from the brain's neuron `pre` onto an organ segment, g_nS in total (Cook's contacts x the
    ledger's conductance per NMJ contact), in the brain's receptor form (wbody2, 8 Nov: the organs had placed
    BAAIWorm's graded synapse whatever receptor_kinetics said, so no wsyn gain reached them).
        receptor_kinetics off, or sign_rule allexc: BAAIWorm's graded synapse (brain._syn), as before
        graded: one wsyn in mode 0, the BAAIWorm-equivalent form the brain's own synapses take in that mode
        instantaneous / kinetic: one wsyn per (class, share) of receptors.pair_classes with no CeNGEN profile for the
            organ cell (the transmitter's default class of the synapse's sign), or with muscle=True the body-wall NMJ
            set; each at g_nS x share x gamma_class / gamma_L-AChR (the brain's NMJ rule without structure_rules)
    The wsyn is set up as brain._wsyn sets one, and appended to brain.wsyn as (wsyn, pre index, -1, class index or -1):
    post -1 = not a brain cell, so no per-cell receptor gain applies to it. Returns the wsyn placed ([] for _syn)."""
    pre_seg = b.soma[b.idx[pre]](0.5)
    if b.toggles["receptor_kinetics"] == "off" or b.toggles["sign_rule"] == "allexc":
        b._syn(pre_seg, post_seg, g_nS / (b._g_syn(inh) * 1000.0), inh, kind)
        return []
    from wormemu import mech
    from wormemu.mech import receptors
    h, sv = b.h, b.spec.v
    cl = [] if b._rk_mode == 0 else receptors.pair_classes(b.st, pre, None, None, inh, muscle,
                                                           float(b._rk_p["rec_nmj_lacr_share"]))
    out = []
    for c, sh in cl or [(None, 1.0)]:
        pp = h.wsyn(post_seg)
        h.setpointer(pre_seg._ref_v, "vpre", pp)
        pp.gmax = g_nS * sh * (receptors.gamma_ratio(b._rk_p, c) if c else 1.0) / 1000.0
        sk = "inh" if inh and c is None else "exc"
        for q in ("delta", "k", "Vth"):
            setattr(pp, q, sv(f"syn_{sk}_{q}") if b.lit else
                    {"delta": 5.0, "k": 0.015000001 if sk == "inh" else 0.5, "Vth": -20.0}[q])
        if c is None:
            pp.mode = 0
            pp.erev = sv(f"syn_{'inh' if inh else 'exc'}_erev") if b.lit else (-70.0 if inh else 30.0)
        else:
            for q, x in b._rk_par[c].items():
                setattr(pp, q, x)
        b.conn.append(pp)
        b.wsyn.append((pp, b.idx[pre], -1, -1 if c is None else mech.RECEPTOR_CLASSES.index(c)))
        b.placed[f"wsyn_{c or ('graded_inh' if inh else 'graded_exc')}"] += 1
        out.append(pp)
    b.placed[kind + ("_inh" if inh else "")] += 1
    return out
