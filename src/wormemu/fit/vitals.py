"""The vital-signs battery (weki, 8 Nov 2026; docs/worm/VITAL_SIGNS.md): the entire worm's physiology, read out of
one closed-loop run per condition. The gate's instrument, and the candidate EKI observations (FIT_GENERAL.md).

Ben (8 Nov): "Vital signs is a good direction as a check, as long as all the signs emerge from the mechanics of the
entire worm." So every sign is read from the same everything-on run through wormemu.simulate(theta, experiment):
the body on (MetaWorm FEM in closed loop on the agar film), every registered mechanism at its default form, the plate
fields of body/environment.py at their defaults (lawn, O2, CO2, salt plug, temperature gradient), food on or off.
Nothing here writes an observable: a sign the worm does not produce is a miss, never patched.

The plate: datamodel.simulate builds its Body with no environment, the published world and the default scene
(Requests, night file 2026-11-08_weki). Until that changes, `plate()` hands simulate's Body the agar film, the
environment and wtriage's scene (vital_loop.py's exact setup) by subclassing body.loop.Body for the call. Nothing else
in simulate changes.

Physicality, per run (DEBUG_PASS_PLAN refinement 3), pre-registered:
    finite      every recorded voltage, Ca and module concentration is finite
    V bounds    every soma voltage inside [E_lo - 1 mV, E_hi + 1 mV], E_lo / E_hi the lowest and highest reversal
                potential this worm's values contain (REVERSAL_IDS plus BAAIWorm's literal -80 mV K and +60 mV Ca
                reversals); a membrane made only of conductances cannot leave that interval, so a departure means a
                module injects current past it (the 1 mV is integrator overshoot, guessed)
    conc >= 0   every recorded concentration (ca_uM and each out:*_uM / _mM / _nM) >= -1e-9
Activity (the fraction of neurons above -20 mV) is reported with no bar: none is published (DEBUG_TRIAGE line 18).

Usage:
    python -m wormemu.fit.vitals run COND SECONDS OUTDIR [--seed=N]     COND food | nofood
    python -m wormemu.fit.vitals table OUTDIR [OUTDIR ...]               the markdown table of every COND.json
"""
from __future__ import annotations

import contextlib
import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

EXCHANGE_MS = 1000.0 / 240.0          # the body's published step; simulate samples once per exchange at every_ms <= it
SETTLE_S = 5.0                        # readouts skip the first 5 bio-s (slow_set_s 2 s plus the body's first bends)
SPIKE_MV = -10.0                      # BWM action potential: an upward crossing of -10 mV (wtriage's readout)
CA_PEAK_UM, CA_PEAK_GAP_S = 0.3, 10.0  # intestinal Ca peaks: > 0.3 uM, >= 10 s apart (wtriage's readout)
EGG_BOUT_GAP_S = 300.0                # eggs closer than this belong to one active phase (inferred, VITAL_SIGNS.md)
EGG_MIN_BIO_S = 1800.0                # bout statistics need at least one inactive phase (~20 min, VITAL_SIGNS.md)
DMP_MIN_INTERVALS = 2                 # a defecation period needs at least 2 expulsion-to-expulsion intervals
ATANAS_DT_S = 1.0 / 1.7               # resample GCaMP to Atanas 2023's volume rate before the PC statistic
PC_K = 3
PLATES = {"food": {"env_food": "lawn"}, "nofood": {"env_food": "off"}}
CLASSES = {"AIY": ("AIYL", "AIYR"), "AFD": ("AFDL", "AFDR"), "AWA": ("AWAL", "AWAR")}   # RIM: its clamp is sealed
CONC = ("out:intestine_ca_uM", "out:intestine_ip3_uM", "out:pharynx_ca_core_uM", "out:bwm_ca_mM",
        "out:enteric_ca_mM", "out:egg_vm_ca_mM", "out:afd_cascade_ca_uM", "out:afd_cgmp_uM", "out:nlp40_nM",
        "out:uv1_tyramine_uM", "out:amphid_k_mM", "out:na_i_mM")
OBSERVE = ("v_mV", "ca_uM", "gcamp_dff", "pumps", "eggs_laid", "expulsions", "posture") + CONC
REVERSAL_IDS = ("ion_ek", "syn_exc_erev", "syn_inh_erev", "c302_muscle_leak_erev", "c302_muscle_k_slow_erev",
                "c302_muscle_k_fast_erev", "c302_muscle_ca_boyle_erev", "unc58_erev_mV", "rec_lacr_erev_mV",
                "rec_acr16_erev_mV", "rec_nachr_erev_mV", "rec_acc_erev_mV", "rec_glr_erev_mV", "rec_nmr_erev_mV",
                "rec_glucl_erev_mV", "rec_gabacl_erev_mV", "rec_gabacat_erev_mV", "rec_mod1_erev_mV",
                "rec_lgc55_erev_mV", "rec_lgc53_erev_mV", "rec_acr23_erev_mV", "proprio_ek_twk16_mV",
                "bwm_du_eca_mV", "bwm_du_ek_mV", "bwm_du_ena_mV", "bwm_du_el_mV", "pbo5_erev_mV",
                "egg_cation_erev_mV", "glia_e_leak_mV", "other_e_leak_mV", "sens_glia_e_leak_mV", "endo_e_leak_mV",
                "obs_opto_e_mV")
BAAI_E = (-80.0, 60.0)                # BAAIWorm's literal K and Ca reversals (brain.py EK_MODS note; nicoletti.E_K, E_CA)


@dataclass
class Sign:
    """One vital sign: its readout, the condition it is read in, and the measured range (VITAL_SIGNS.md)."""
    id: str
    what: str
    cond: tuple                       # conditions it is scored in ("food",), ("nofood",) or both
    unit: str
    mean: float | None = None         # the published mean
    sd: float | None = None           # between-animal SD (derived from SEM x sqrt(n) where only SEM is reported)
    n: int | None = None
    lo: float | None = None           # explicit band (a percentile range); else mean +- 2 sd
    hi: float | None = None
    source: str = ""
    label: str = "measured"           # of the range
    min_bio_s: float = 0.0            # shorter runs report "too short"
    notes: str = ""

    def band(self):
        if self.lo is not None and self.hi is not None:
            return self.lo, self.hi
        if self.mean is not None and self.sd is not None:
            return self.mean - 2.0 * self.sd, self.mean + 2.0 * self.sd
        return None


# The ranges. Each source was opened (who and when in VITAL_SIGNS.md); None = no opened measurement yet.
SIGNS = [
    Sign("rest_AIY", "AIY soma, median voltage", ("food", "nofood"), "mV"),
    Sign("rest_AFD", "AFD soma, median voltage", ("food", "nofood"), "mV"),
    Sign("rest_AWA", "AWA soma, median voltage", ("food", "nofood"), "mV"),
    Sign("pc3_frac", "whole-brain GCaMP: variance fraction in the top 3 PCs (z-scored traces, run-length windows)",
         ("food", "nofood"), "1"),
    Sign("gcamp_range", "GCaMP per-neuron range, median over neurons", ("food", "nofood"), "dF/F"),
    Sign("ca_rest_uM", "neuron soma Ca, median over neurons of each one's median", ("food", "nofood"), "uM"),
    Sign("pump_hz", "pharyngeal pumping rate on food", ("food",), "Hz"),
    Sign("pump_hz_off", "pharyngeal pumping rate off food", ("nofood",), "Hz"),
    Sign("dmp_period_s", "defecation period (expulsion to expulsion) on food", ("food",), "s", min_bio_s=150.0),
    Sign("egg_inactive_min", "egg-laying: inactive phase duration", ("food",), "min", min_bio_s=EGG_MIN_BIO_S),
    Sign("egg_intra_s", "egg-laying: interval between eggs inside an active phase", ("food",), "s",
         min_bio_s=EGG_MIN_BIO_S),
    Sign("bwm_rest_mV", "body-wall muscle, median voltage", ("food", "nofood"), "mV"),
    Sign("bwm_spike_hz", "body-wall muscle action potentials per firing muscle", ("food", "nofood"), "Hz"),
]
SIGN = {s.id: s for s in SIGNS}


def set_range(sid, **kw):
    for k, v in kw.items():
        setattr(SIGN[sid], k, v)


# --- the experiment -------------------------------------------------------------------------------------------------
def experiment(cond: str, seconds: float, seed=None, toggles=None, body_out=None):
    from wormemu.datamodel import Experiment
    if cond not in PLATES:
        raise ValueError(f"{cond}: one of {sorted(PLATES)}")
    return Experiment(duration_ms=1000.0 * seconds, body="on", temperature_C=20.0, observe=OBSERVE,
                      every_ms=EXCHANGE_MS, toggles=dict(toggles or {}), seed=seed, body_out=body_out,
                      sources=[("vital_signs", cond)])


@contextlib.contextmanager
def plate(env_toggles: dict, events=()):
    """simulate's Body on the agar film with the plate's fields (vital_loop.py's setup), for the duration."""
    from wormemu.body import environment, loop
    from wormemu.body.metaworm import AGAR_FILM
    from wormemu.body.scene import ChemotaxisScene
    orig = loop.Body

    class PlateBody(orig):
        def __init__(self, out, **kw):
            kw.setdefault("world", dict(AGAR_FILM))
            kw.setdefault("env", environment.Environment(toggles=dict(env_toggles), events=list(events)))
            kw.setdefault("scene", ChemotaxisScene(field="cone_published"))
            super().__init__(out, **kw)

    loop.Body = PlateBody
    try:
        yield
    finally:
        loop.Body = orig


def reversal_bounds(spec) -> tuple[float, float]:
    vals = [float(spec.values[k]) for k in REVERSAL_IDS if k in spec.values]
    return min([BAAI_E[0]] + vals), max([BAAI_E[1]] + vals)


# --- readouts -------------------------------------------------------------------------------------------------------
def peaks(t, x, thr, gap_s):
    """Local maxima above thr at least gap_s apart (wtriage's vital_signs.peaks)."""
    out, last = [], -1e9
    for k in range(1, len(x) - 1):
        if x[k] > thr and x[k] >= x[k - 1] and x[k] > x[k + 1] and t[k] - last >= gap_s:
            out.append(float(t[k]))
            last = t[k]
    return out


def event_times(t_s, counts):
    """Times of events from per-sample counts (one entry per event)."""
    c = np.asarray(counts, float)
    return [float(t_s[k]) for k in np.flatnonzero(c > 0) for _ in range(int(round(c[k])))]


def upcrossings(v, thr):
    """Upward crossings of thr per column of v [samples, cells]."""
    v = np.asarray(v, float)
    return ((v[:-1] < thr) & (v[1:] >= thr)).sum(axis=0)


def resample(t_s, x, dt_s):
    """x [samples, cells] at t_s, sampled by linear interpolation every dt_s from t_s[0]."""
    tt = np.arange(t_s[0], t_s[-1] + 1e-9, dt_s)
    return tt, np.stack([np.interp(tt, t_s, x[:, j]) for j in range(x.shape[1])], axis=1)


def pc_frac(x, k=PC_K):
    """Fraction of the variance of the z-scored columns of x [frames, neurons] in the top k principal components.
    Flat columns (SD < 1e-9) are dropped; returns (fraction, columns used)."""
    x = np.asarray(x, float)
    sd = x.std(axis=0)
    keep = np.isfinite(sd) & (sd > 1e-9)
    z = (x[:, keep] - x[:, keep].mean(axis=0)) / sd[keep]
    if z.shape[1] < k + 1 or z.shape[0] < k + 1:
        return float("nan"), int(keep.sum())
    ev = np.linalg.svd(z, compute_uv=False) ** 2
    return float(ev[:k].sum() / ev.sum()), int(keep.sum())


def gcamp_range(dff):
    """Per neuron (P95 - P5) of dF/F, the median over neurons with a finite trace."""
    d = np.asarray(dff, float)
    ok = np.isfinite(d).all(axis=0)
    if not ok.any():
        return float("nan")
    r = np.percentile(d[:, ok], 95, axis=0) - np.percentile(d[:, ok], 5, axis=0)
    return float(np.median(r))


def egg_bouts(times_s, gap_s=EGG_BOUT_GAP_S):
    """Active phases (eggs closer than gap_s), the intervals inside them and the inactive gaps between them."""
    t = sorted(times_s)
    bouts = []
    for x in t:
        if bouts and x - bouts[-1][-1] < gap_s:
            bouts[-1].append(x)
        else:
            bouts.append([x])
    intra = [b - a for bout in bouts for a, b in zip(bout[:-1], bout[1:])]
    inactive = [b2[0] - b1[-1] for b1, b2 in zip(bouts[:-1], bouts[1:])]
    return bouts, intra, inactive


def readouts(res: dict, cond: str, bio_s: float) -> dict:
    """Every sign's model value from one simulate() result (VITAL_SIGNS.md defines each)."""
    from wormemu.interface import BWM_NAMES
    cells = list(res["cells"])
    t = np.asarray(res["t_ms"], float) / 1000.0
    w = t >= SETTLE_S
    dur = float(t[w][-1] - t[w][0]) if w.sum() > 1 else 0.0
    V = np.asarray(res["v_mV"], float)
    bwm = [k for k, c in enumerate(cells) if c in set(BWM_NAMES)]
    neur = [k for k, c in enumerate(cells) if c not in set(BWM_NAMES)]
    out = {"bio_s": bio_s, "settle_s": SETTLE_S, "window_s": dur}
    for cls, pair in CLASSES.items():
        med = [float(np.median(V[w, cells.index(c)])) for c in pair if c in cells]
        out[f"rest_{cls}"] = float(np.mean(med)) if med else None
        out[f"rest_{cls}_cells"] = med
    g = np.asarray(res["gcamp_dff"], float)[:, neur]
    tt, gr = resample(t[w], g[w], ATANAS_DT_S)
    out["pc3_frac"], out["pc3_n_neurons"] = pc_frac(gr)
    out["gcamp_range"] = gcamp_range(g[w])
    ca = np.asarray(res["ca_uM"], float)[:, neur]
    out["ca_rest_uM"] = float(np.median(np.median(ca[w], axis=0)))
    out["ca_range_uM"] = float(np.median(np.percentile(ca[w], 95, axis=0) - np.percentile(ca[w], 5, axis=0)))
    pumps = event_times(t, res["pumps"])
    out["pumps"] = len(pumps)
    out["pump_hz" if cond == "food" else "pump_hz_off"] = (sum(p >= SETTLE_S for p in pumps) / dur) if dur else None
    ex = event_times(t, res["expulsions"])
    out["expulsions"], out["expulsion_s"] = len(ex), ex
    iv = np.diff(ex)
    out["dmp_period_s"] = float(np.mean(iv)) if len(iv) >= DMP_MIN_INTERVALS else None
    ic = np.asarray(res["out:intestine_ca_uM"], float)
    icm = ic.max(axis=1) if ic.ndim == 2 else ic
    pk = peaks(t, icm, CA_PEAK_UM, CA_PEAK_GAP_S)
    out["int_ca_peaks_s"] = pk
    out["int_ca_period_s"] = float(np.mean(np.diff(pk))) if len(pk) > 1 else None
    out["int_ca_max_uM"] = float(np.nanmax(icm))
    eggs = event_times(t, res["eggs_laid"])
    bouts, intra, inactive = egg_bouts(eggs)
    out.update(eggs=len(eggs), egg_s=eggs, egg_bouts=len(bouts),
               egg_intra_s=float(np.median(intra)) if intra else None,
               egg_inactive_min=float(np.median(inactive)) / 60.0 if inactive else None)
    vb = V[:, bwm]
    out["bwm_rest_mV"] = float(np.median(np.median(vb[w], axis=0)))
    sp = upcrossings(vb[w], SPIKE_MV)
    out["bwm_frac_firing"] = float((sp > 0).mean())
    out["bwm_spike_hz"] = float(sp[sp > 0].mean() / dur) if (sp > 0).any() and dur else None
    out["bwm_spike_hz_all"] = float(sp.mean() / dur) if dur else None
    hi = (V[:, neur] > -20.0).mean(axis=1)
    out["neur_frac_above_m20_mean"], out["neur_frac_above_m20_max"] = float(hi[w].mean()), float(hi[w].max())
    out["neur_median_mV"] = float(np.median(V[w][:, neur]))
    post = res.get("posture")
    if post is not None and np.ndim(post) == 2:
        out["curvature_abs_mean_per_mm"] = float(np.mean(np.abs(np.asarray(post, float)[w])))
    return out


def physicality(res: dict, bounds: tuple[float, float], tol_mV: float = 1.0) -> dict:
    """The per-run physicality check (module docstring). Returns the verdict and what failed."""
    V = np.asarray(res["v_mV"], float)
    cells = list(res["cells"])
    out = {"E_lo_mV": bounds[0], "E_hi_mV": bounds[1], "tol_mV": tol_mV}
    fin = {"v_mV": bool(np.isfinite(V).all()), "ca_uM": bool(np.isfinite(np.asarray(res["ca_uM"], float)).all())}
    neg = {}
    for ch in ("ca_uM",) + CONC:
        x = res.get(ch)
        if x is None:
            continue
        try:
            a = np.asarray(x, float)
        except (TypeError, ValueError):
            fin[ch] = False
            continue
        fin[ch] = bool(np.isfinite(a).all())
        m = float(np.nanmin(a)) if a.size else 0.0
        if m < -1e-9:
            neg[ch] = m
    lo, hi = bounds[0] - tol_mV, bounds[1] + tol_mV
    Vf = np.where(np.isfinite(V), V, 0.0)
    bad = (Vf < lo) | (Vf > hi)
    per = bad.mean(axis=0)
    worst = np.argsort(-per)[:8]
    out.update(finite=all(fin.values()), nonfinite=[k for k, v in fin.items() if not v], negative=neg,
               v_out_frac=float(bad.mean()), v_out_cells=int((per > 0).sum()),
               v_out_worst=[(cells[k], float(per[k]), float(V[:, k].min()), float(V[:, k].max()))
                            for k in worst if per[k] > 0],
               v_min=float(np.nanmin(V)), v_max=float(np.nanmax(V)))
    out["physical"] = bool(out["finite"] and not neg and out["v_out_cells"] == 0)
    return out


def score(r: dict, cond: str) -> dict:
    """Each sign scored in this condition: in / miss / not produced / too short / no bar."""
    res = {}
    for s in SIGNS:
        if cond not in s.cond:
            continue
        x = r.get(s.id)
        band = s.band()
        if r["bio_s"] < s.min_bio_s:
            st = "too short"
        elif x is None or (isinstance(x, float) and math.isnan(x)):
            st = "not produced"
        elif band is None:
            st = "no bar"
        else:
            st = "in" if band[0] <= x <= band[1] else "miss"
        z = (x - s.mean) / s.sd if (st in ("in", "miss") and s.mean is not None and s.sd) else None
        res[s.id] = {"value": x, "status": st, "band": band, "z": z}
    return res


def run(theta, cond: str, seconds: float, outdir, seed=None, toggles=None) -> dict:
    """One battery condition through simulate(); writes OUTDIR/COND.json and the compact traces OUTDIR/COND.npz."""
    from wormemu import datamodel
    from wormemu.brain import sample_worm
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    ex = experiment(cond, seconds, seed=seed, toggles=toggles, body_out=str(outdir / f"{cond}_body"))
    spec = datamodel._theta(sample_worm(seed), theta)
    t0 = time.time()
    with plate(PLATES[cond]):
        res = datamodel.simulate(theta, ex)
    wall = time.time() - t0
    bio_s = float(res["t_ms"][-1]) / 1000.0 if len(res["t_ms"]) else 0.0
    r = readouts(res, cond, bio_s)
    out = {"cond": cond, "seed": seed, "theta": None if theta is None else "given", "toggles": dict(toggles or {}),
           "plate": PLATES[cond], "wall_s": wall, "wall_per_bio_s": wall / bio_s if bio_s else None,
           "readouts": r, "physicality": physicality(res, reversal_bounds(spec)), "score": score(r, cond),
           "notes": res.get("notes", [])}
    (outdir / f"{cond}.json").write_text(json.dumps(out, indent=1, default=float))
    t = np.asarray(res["t_ms"], float) / 1000.0
    k = np.arange(0, len(t), 12)                                # every 50 ms
    neur = [j for j, c in enumerate(res["cells"]) if not c.startswith(("dBWM", "vBWM"))]
    np.savez_compressed(outdir / f"{cond}.npz", t=t[k], v=np.asarray(res["v_mV"], np.float32)[k],
                        gcamp=np.asarray(res["gcamp_dff"], np.float32)[k][:, neur],
                        int_ca=np.asarray(res["out:intestine_ca_uM"], np.float32)[k],
                        cells=np.array(res["cells"]))
    return out


def table(results: list[dict]) -> str:
    """Markdown: one row per sign, one column per condition run."""
    hdr = "| Sign | Unit | Published band (mean +- 2 SD, or range) | " + " | ".join(
        f"{r['cond']} ({r['readouts']['bio_s']:.0f} s)" for r in results) + " |"
    lines = [hdr, "|" + "---|" * (3 + len(results))]
    for s in SIGNS:
        b = s.band()
        bt = f"{b[0]:.3g} to {b[1]:.3g}" if b else "no opened measurement"
        cells = []
        for r in results:
            sc = r["score"].get(s.id)
            if sc is None:
                cells.append("")
                continue
            v = sc["value"]
            vt = "none" if v is None else (f"{v:.3g}" if isinstance(v, (int, float)) else str(v))
            cells.append(f"{vt} ({sc['status']})")
        lines.append(f"| {s.what} | {s.unit} | {bt} | " + " | ".join(cells) + " |")
    lines.append("| physical (finite, V in reversal bounds, conc >= 0) | | | " + " | ".join(
        "yes" if r["physicality"]["physical"] else
        f"no: {r['physicality']['v_out_cells']} cells outside [{r['physicality']['E_lo_mV']:.0f}, "
        f"{r['physicality']['E_hi_mV']:.0f}] mV, negative {sorted(r['physicality']['negative'])}, "
        f"nonfinite {r['physicality']['nonfinite']}" for r in results) + " |")
    lines.append("| wall per bio-s | s | | " + " | ".join(f"{r['wall_per_bio_s']:.1f}" for r in results) + " |")
    return "\n".join(lines)


def _main(argv):
    if argv[0] == "run":
        cond, secs, outdir = argv[1], float(argv[2]), argv[3]
        seed = next((int(a.split("=", 1)[1]) for a in argv[4:] if a.startswith("--seed=")), None)
        out = run(None, cond, secs, outdir, seed=seed)
        print(json.dumps({k: out[k] for k in ("cond", "wall_s", "wall_per_bio_s")}), flush=True)
        print(table([out]))
    elif argv[0] == "table":
        rs = [json.loads(p.read_text()) for d in argv[1:] for p in sorted(Path(d).glob("*.json"))]
        print(table(rs))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    _main(sys.argv[1:])
