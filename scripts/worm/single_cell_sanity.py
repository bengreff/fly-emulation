"""Single-cell sanity at the ledger values (wexcite, 7 Nov 2026; TO_A_REAL_WORM item 2, step 0).

Every neuron alone: the brain's own cell model (BAAIWorm cell + mech/channels' Nicoletti channels, Ca pool, pump,
temperature, homeostasis at the ledger values), no synapses, no gap junctions, no peptides or amines, no sensory
drive. All 302 neurons are built in one Brain with the wiring removed, so they are uncoupled; the same current goes
into every soma. Protocol: 1.5 s at 0 pA, a 1 s step, 0.5 s back at 0 pA; steps -20, -10, 0, +10, +20, +30, +40 pA,
each from a fresh reset.

Bars (written before the first run, 7 Nov 01:45):
  upper  V <= the highest reversal present at that moment (max of E_Na, the soma's E_Ca from its own cai, e_pas) at
         every sample of every step. A cell above it is a correctness problem (a cell with too little outward
         conductance for the current, a unit error, or numerics).
  lower  the brief's V >= the lowest reversal (E_K, e_pas) is NOT a law under injected current: the recorded cells
         break it (measured, Naudin 2022 training sweeps at -15 pA: AIY -126.3 mV, RIM -119.2 mV, AFD -94.6 mV,
         against E_K -77 mV). It is reported, not scored. Scored instead: V >= -150 mV at -20 pA (derived: AIY's
         -126.3 mV at -15 pA from its -54 mV baseline, scaled linearly to -20 pA).
  also   finite everywhere; reported (not scored) cells above +75 mV (the highest any recorded cell reached in the
         training sweeps: RIM at +35 pA).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/single_cell_sanity.py OUT.json [--noise] [--cells=A,B] [--dt=0.5]
       [--tog=toggle=form ...] (attribution runs, e.g. --tog=expression_map=off)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wormemu import brain as B  # noqa: E402

STEPS_PA = (-20, -10, 0, 10, 20, 30, 40)
T_PRE, T_STEP, T_POST = 1500.0, 1000.0, 500.0      # ms
UPPER_SLACK = 0.0                                    # mV
FLOOR_M20 = -150.0                                   # mV at -20 pA (derived, docstring)
REC_MAX = 75.0                                       # mV (measured, RIM training sweep at +35 pA)

# isolation: no inputs, no coupling between cells; the membrane mechanisms stay at their defaults
OFF = {k: "off" for k in (
    "sens_salt", "sens_odor_attract", "sens_repellent", "sens_thermo", "sens_o2", "sens_co2", "sens_light",
    "sens_food", "sens_touch_gentle", "sens_touch_harsh", "sens_tap", "sens_proprio",
    "peptides", "monoamines", "receptor_kinetics", "stp", "habituation", "slow_signalling", "associative",
    "quantal_noise", "channel_noise", "glia_cells", "glia_kbuffer", "glia_kcc3", "other_cells", "excretory_osmo",
    "coelomocytes", "glia_sensilla", "endorgan_cells", "pharynx", "defecation", "pboc_protons", "nlp40_aex2",
    "enteric_muscle", "egg_laying", "egg_unc103", "bwm_gap_liu", "opto_gur3", "neuropal", "gait_features",
    "metabolism", "met_feeding", "gcamp", "gap_rectification")}


def build(noise=False, cells=None, extra=None):
    B.Brain._wire_cook = lambda self: None            # no synapses, no gaps: every cell is alone
    B.Brain._wire_baaiworm = lambda self: None
    st = B.load_structure()
    neurons = [n for n, k in zip(st.names, st.kind) if k == "neuron"]
    tog = dict(OFF)
    if noise:
        tog["channel_noise"] = "diffusion"
    tog.update(extra or {})
    return B.Brain(B.sample_worm(None), toggles=_known(tog), cells=cells or neurons)


def _known(tog):
    """drop toggles this checkout does not define (the brain asserts on unknown names)"""
    from wormemu import brain_layers, mech
    ids = {t[0] for t in brain_layers.MECHANISMS} | {t[0] for t in mech.all_mechanisms()} \
        | set(B.default_toggles(B.sample_worm(None).led)) | set(B.TEMPLATE_ON)
    return {k: v for k, v in tog.items() if k in ids}


def reversals(br):
    """per cell: E_K, E_Na, e_pas (soma, neurite min/max) as built; E_Ca is read each sample"""
    h = br.h
    out = []
    for s, cell in zip(br.soma, br.cells):
        seg = s(0.5)
        ek = seg.ek if h.ismembrane("k_ion", sec=s) else np.nan
        ena = seg.ena if h.ismembrane("na_ion", sec=s) else np.nan
        ep = [sg.e_pas for sec in cell.all for sg in sec]
        out.append((ek, ena, min(ep), max(ep)))
    return np.array(out)


def run(br, amp_pA, dt_rec=1.0):
    h = br.h
    n = len(br.cell_names)
    pe = h.PtrVector(n)
    has_ca = np.zeros(n, bool)
    for i, s in enumerate(br.soma):
        if h.ismembrane("ca_ion", sec=s):
            pe.pset(i, s(0.5)._ref_eca)
            has_ca[i] = True
        else:
            pe.pset(i, s(0.5)._ref_v)          # placeholder, masked below
    buf = h.Vector(n)
    br.reset()
    T = T_PRE + T_STEP + T_POST
    nt = int(round(T / dt_rec))
    V, E = np.empty((nt, n)), np.empty((nt, n))
    for k in range(nt):
        t = k * dt_rec
        br.extra_pA[:] = amp_pA if T_PRE <= t < T_PRE + T_STEP else 0.0
        o = br.step(None, dt_rec)
        V[k] = o.v_mV
        pe.gather(buf)
        E[k] = np.where(has_ca, buf.as_numpy(), np.nan)
    br.extra_pA[:] = 0.0
    return V, E


def main():
    out = Path(sys.argv[1])
    noise = "--noise" in sys.argv
    cells = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--cells=")), None)
    dt = next((float(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--dt=")), None)
    extra = dict(a[len("--tog="):].split("=", 1) for a in sys.argv if a.startswith("--tog="))
    t0 = time.time()
    br = build(noise, cells, extra)
    if dt is not None:
        B.DT_MS = dt
    names = br.cell_names
    rev = reversals(br)
    added = getattr(br, "added_channels", {})
    print(f"built {len(names)} cells in {time.time() - t0:.0f} s", flush=True)
    res = dict(names=names, steps_pA=list(STEPS_PA), ek=rev[:, 0].tolist(), ena=rev[:, 1].tolist(),
               epas_min=rev[:, 2].tolist(), epas_max=rev[:, 3].tolist(), noise=noise, per_step={},
               added=added, toggles={k: v for k, v in br.toggles.items()})
    i0, i1 = int(T_PRE), int(T_PRE + T_STEP)
    for a in STEPS_PA:
        t1 = time.time()
        V, E = run(br, a)
        win = slice(i0, i1 + 200)                    # the step and 200 ms after it
        emax = np.fmax(np.fmax(E, rev[:, 1][None, :]), rev[:, 3][None, :])
        over = V[win] - emax[win]
        emin = np.fmin(rev[:, 0], rev[:, 2])
        res["per_step"][str(a)] = dict(
            v_rest=V[i0 - 1].tolist(), v_max=np.nanmax(V[win], 0).tolist(), v_min=np.nanmin(V[win], 0).tolist(),
            v_end_step=V[i1 - 1].tolist(), v_final=V[-1].tolist(),
            over_emax=np.nanmax(over, 0).tolist(), eca_at_vmax=E[win][np.nanargmax(V[win], 0), range(len(names))]
            .tolist(), below_emin=(emin - np.nanmin(V[win], 0)).tolist(),
            finite=bool(np.isfinite(V).all()))
        print(f"step {a:+d} pA: {time.time() - t1:.0f} s wall; finite {np.isfinite(V).all()}; "
              f"max V {np.nanmax(V):.1f} min V {np.nanmin(V):.1f}; over E_max: "
              f"{int((np.nanmax(over, 0) > UPPER_SLACK).sum())} cells", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res))
    print("wrote", out, flush=True)


if __name__ == "__main__":
    main()
