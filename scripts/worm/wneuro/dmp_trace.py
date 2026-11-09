"""wneuro item 1 (8 Nov 2026): the defecation chain from intestinal NLP-40 to DVB, after neuromod's fixes.
wbody2's dmp_trace.py (its worktree, scripts/worm/wbody2/) with three additions: the NLP-40 each cell READS (area-
weighted over its compartments: Mech.cell_nM; under neuromod_site=soma it is the soma's compartment, as before), the
EGL-19 and UNC-2 Gs factors, and DVB / AVL spike counts per intestinal cycle. Diagnostic only, nothing tuned.

Check and bar (written before running): Wang et al. 2013 Curr Biol (PMC3651789, opened 8 Nov 2026), "a single robust
calcium spike in the synaptic region of the DVB neuron ... began approximately three seconds following each pBoc step
... (51 out of 51 cycles in 14 worms)", and Wang and Sieburth 2013 (PLoS Genet e1003831): the pattern "occurring 100%
of the time", no ectopic transients in wild type. Bar: in every intestinal cycle after the first (int9L/R mean Ca
peaks, wbody2's record), DVB fires exactly one spike within 0-10 s after the int9 peak and none in the rest of the
cycle. A spike is an up-crossing of -23.4 mV, DVB's recorded threshold (Jiang et al. 2022 Nat Commun 13:2783,
PMC9120479: threshold -23.4 +- 1.6 mV, rest -49.0 +- 3.6, peak +26.3 +- 2.6), counted again only after V falls below
-35 mV. The 0 mV crossings are reported too.

Usage: python dmp_trace.py [SECONDS] [cells=dmp] [toggle=value ...] [clamp_gs=CELL:VALUE] [inject=CELL:pA:t0:t1]
  cells=dmp  build only AVL, DVB and their Cook partners (wbody2's list)
  clamp_gs   holds that cell's Gs at VALUE from 2 s on (diagnostic: can the Gs route make it fire at all?)
  inject     a current step into a cell (diagnostic)
  p.ID=VALUE sets parameter ID in this worm (a feasibility probe inside the Spec's range; never adopted)
-> runs/worm/wneuro/dmp_trace[_tag].json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "triage"))
import at_ledger  # noqa: E402

at_ledger.patch()
from vital_signs import peaks  # noqa: E402
from wormemu import brain as B  # noqa: E402
from wormemu.interface import ENTERIC_MUSCLES  # noqa: E402
from wormemu.mech import neuromod as nmod  # noqa: E402
from wormemu.mech import organs_intestine as I  # noqa: E402

DMP = ["AVL", "DVB", "PVR", "AVAL", "AVAR", "PHAL", "PHAR", "PDA", "DA09", "VA12", "LUAL", "LUAR", "PVCL", "PVCR"]
THR, RESET = -23.4, -35.0


def spikes(t, v, thr, reset):
    out, armed = [], True
    for k in range(1, len(v)):
        if armed and v[k - 1] < thr <= v[k]:
            out.append(float(t[k]))
            armed = False
        elif not armed and v[k] < reset:
            armed = True
    return out


def per_cycle(peaks_s, sp, end):
    """For each int9 peak after the first: spikes 0-10 s after it, and spikes in the rest of the cycle."""
    rows = []
    for k in range(1, len(peaks_s)):
        a, b = peaks_s[k], (peaks_s[k + 1] if k + 1 < len(peaks_s) else end)
        win = [s for s in sp if a <= s < min(a + 10.0, b)]
        rest = [s for s in sp if a + 10.0 <= s < b]
        rows.append(dict(peak_s=a, in_window=len(win), rest_of_cycle=len(rest), first_delay_s=(win[0] - a) if win
                         else None))
    passed = bool(rows) and all(r["in_window"] == 1 and r["rest_of_cycle"] == 0 for r in rows)
    return rows, passed


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 and "=" not in sys.argv[1] else 120.0
    tog = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    tag = "_".join(f"{k}-{v}".replace(":", "@") for k, v in tog.items())
    cells = DMP if tog.pop("cells", None) == "dmp" else None
    clamp = tog.pop("clamp_gs", None)
    inject = tog.pop("inject", None)
    pset = {k[2:]: float(tog.pop(k)) for k in list(tog) if k.startswith("p.")}
    spec = B.sample_worm(None)
    spec.values.update(pset)
    b = B.Brain(spec, toggles=tog, cells=cells)
    nm = next((m for m in b.mechs if isinstance(m, nmod.Mech)), None)
    i9 = [I.INT_CELLS.index(n) for n in ("int9L", "int9R")]
    who = [n for n in ("AVL", "DVB") if n in b.idx]
    b.reset()
    if clamp:
        cc, cv = clamp.split(":")
        cj, cv = b.idx[cc], float(cv)
    if inject:
        ic, ia, it0, it1 = inject.split(":")
        ij, ia, it0, it1 = b.idx[ic], float(ia), float(it0), float(it1)
    rec = {k: [] for k in ("t", "int9", "int_mean", "nlp40_release_per_s", "nlp40_local_nM", "exp_total")}
    for n in who:
        for x in ("v", "gs", "nlp40_read_nM", "nlp40_soma_nM", "occ"):
            rec[f"{n}_{x}"] = []
    vfine = {n: [] for n in who}
    exps, t0 = 0, time.time()
    ec50 = float(nm.p["pep_ec50_nlp-40_aex-2_nM"])
    hh = float(nm.p["gpcr_hill"])
    row = nmod.PRECURSORS.index("nlp-40")
    for k in range(int(secs * 1000)):
        if clamp and k >= 2000:
            nm.G[cj, 2] = cv
        if inject:
            b.extra_pA[ij] = ia if it0 * 1000 <= k < it1 * 1000 else 0.0
        o = b.step(None, 1.0)
        exps += int(o.expulsions)
        for n in who:
            vfine[n].append(float(o.v_mV[b.idx[n]]))
        if k % 10:
            continue
        mo = b.mech_out
        c = mo.get("intestine_ca_uM")
        rec["t"].append(k / 1000.0)
        rec["int9"].append(float(np.mean(c[i9])))
        rec["int_mean"].append(float(np.mean(c)))
        rec["nlp40_release_per_s"].append(float((mo.get("peptide_release") or {}).get("nlp-40@posterior_body", 0.0)))
        rec["nlp40_local_nM"].append(float(mo.get("nlp40_nM", np.nan)))
        rec["exp_total"].append(exps)
        cp = nm.pep.nM()[row]
        for n in who:
            j = b.idx[n]
            x = nm.cell_nM(nmod.P, "nlp-40", j)
            rec[f"{n}_v"].append(float(o.v_mV[j]))
            rec[f"{n}_gs"].append(float(nm.G[j, 2]))
            rec[f"{n}_nlp40_read_nM"].append(x)
            rec[f"{n}_nlp40_soma_nM"].append(float(cp[nm.pep_comp[j]]))
            rec[f"{n}_occ"].append(float(nm.pep_W[j] @ nmod._hill(cp, ec50, hh)))
    t = np.array(rec["t"])
    tf = np.arange(len(vfine[who[0]])) / 1000.0
    p9 = peaks(t, np.array(rec["int9"]), 0.3, 10.0)
    sp = {n: spikes(tf, np.array(vfine[n]), THR, RESET) for n in who}
    sp0 = {n: spikes(tf, np.array(vfine[n]), 0.0, RESET) for n in who}
    cyc = {n: per_cycle(p9, sp[n], secs) for n in who}
    summ = {k: dict(min=float(np.nanmin(v)), median=float(np.nanmedian(v)), max=float(np.nanmax(v)))
            for k, v in rec.items() if k != "t" and np.isfinite(np.asarray(v, float)).any()}
    wts = {n: dict(zip(nmod.COMPARTMENTS, np.round(nm.pep_W[b.idx[n]], 3).tolist())) for n in who}
    res = dict(bio_s=secs, wall_s=time.time() - t0, cells=len(b.idx), toggles=tog, params=pset, clamp_gs=clamp,
               inject=inject,
               site=nm.site, gs_ca=nm.gs_ca, read_weights=wts, expulsions=exps, int9_peaks_s=p9,
               spikes_thr_s=sp, spikes_0mV_s=sp0, v_max={n: float(np.max(vfine[n])) for n in who},
               cycles={n: dict(rows=cyc[n][0], bar_passed=cyc[n][1]) for n in who},
               summary=summ, trace={k: v[::10] for k, v in rec.items()})
    out = ROOT / f"runs/worm/wneuro/dmp_trace{'_' + tag if tag else ''}_{int(secs)}s.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k != "trace"}, indent=1, default=float))


if __name__ == "__main__":
    main()
