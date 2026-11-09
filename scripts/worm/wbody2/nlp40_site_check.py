"""Where the intestine's NLP-40 goes (wbody2, 8 Nov 2026; inbox 23:36, wneuro's request). organs_intestine releases
NLP-40 at R x the mean Hill(Ca) of its 20 cells, all of it into mech/neuromod's posterior-body compartment. Wang et
al. 2013 (lit_nlp40.md, full text opened by the literature agent): the intestine releases NLP-40 when each cycle's
Ca spike reaches SNT-2 on its dense-core vesicles; no cell is named, and the anterior intestine is imaged secreting.
Espelt et al. 2005: the wave runs posterior to anterior at 20-60 um/s (check_intestine's bar), so the anterior rings
release seconds after int9. Putting their release next to DVB is an interconnect error (A): each cell's release
belongs in the compartment its ring lies in.

The fix: ring k spans fraction (k-1)/9 to k/9 of the intestine, which runs from neuromod's head cut (pc_head_end_y_um,
just behind the retrovesicular ganglion, about the pharynx's end) to its tail cut (pc_tail_start_y_um, the pre-anal
ganglion, about the rectum); rings of equal length (WormAtlas: 9 rings over about 720 um; inferred) and release
uniform along a ring (inferred). Each ring's release splits over the compartments by length overlap. The total
(molecules/s) is unchanged.

Bar (written before running the fixed code; references saved on the unfixed code first):
    total    the intestine Mech alone (the unit test's stand-in brain), 150 s at 1 ms, default toggles: the summed
             peptide_release over all keys equals the unfixed code's at every step to 1e-12 relative (so neuromod's
             well_mixed form, which adds every key to its one compartment, sees an identical input)
    direct   nlp40_aex2=direct: the AEX-2 current into AVL and DVB bit-identical to the unfixed code's at every step
    routing  Ca held at rest in every cell except ring k at 1 uM: the release above the all-rest release appears only
             in the compartments ring k overlaps, in proportion to the overlap (to 1e-12), for k = 1..9
Reported, no bar: in the same 150 s run, the time from each int9 Ca peak to the next peak of the posterior-body
release rate, before (all cells) and after (rings by compartment).
Usage: python nlp40_site_check.py ref   (on the unfixed code)  /  python nlp40_site_check.py
       -> runs/worm/wbody2/nlp40_site_check.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runs/worm/wbody2"
SECS = 150.0
sys.path.insert(0, str(ROOT / "src"))

from wormemu.mech import organs_intestine as gi  # noqa: E402
from wormemu.mech.muscle_bwm import BWM_NAMES  # noqa: E402


def gut_brain():
    """tests/test_worm_organs._gut_brain: 302 neurons named n0.., AVL and DVB, then the BWM; no NEURON."""
    names = [f"n{k}" for k in range(300)] + ["AVL", "DVB"] + list(BWM_NAMES)
    bp = np.tile(np.linspace(0.0, 1.0, 24), 4)[:len(BWM_NAMES)]
    q = gi.defaults()
    layers = SimpleNamespace(bwm_pos=bp, dmp_t=1234.0, p=dict(q))
    return SimpleNamespace(cell_names=names, bwm=np.arange(302, 302 + len(BWM_NAMES)), layers=layers,
                           idx={n: i for i, n in enumerate(names)}), q


def run(form):
    brain, q = gut_brain()
    m = gi.Mech(brain, q, {"defecation": "ip3r", "enteric_muscle": "off", "pboc_protons": "off", "nlp40_aex2": form})
    ctx = SimpleNamespace(v=np.full(len(brain.cell_names), -30.0), outputs={})
    n = int(SECS * 1000)
    tot, post, aex, c9 = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    keys = set()
    for k in range(n):
        r = m.step(ctx, 1.0)
        pr = r["out"]["peptide_release"]
        keys |= set(pr)
        tot[k] = sum(pr.values())
        post[k] = pr.get("nlp-40@posterior_body", 0.0)
        aex[k] = float(r["I_pA"][m.aex2_cells].sum()) if "I_pA" in r else 0.0
        c9[k] = float(m.gut.c[gi.RING == 9].mean())
    return dict(tot=tot, post=post, aex=aex, c9=c9, keys=sorted(keys))


def lags(c9, post):
    """Seconds from each int9 Ca peak (local max above half its range, 10 s apart) to the posterior release peak in the
    next 30 s."""
    thr = c9.min() + 0.5 * (c9.max() - c9.min())
    pk, k = [], 0
    while k < len(c9):
        if c9[k] > thr:
            j = k
            while j < len(c9) and c9[j] > thr:
                j += 1
            pk.append(k + int(np.argmax(c9[k:j])))
            k = j + 10000
        else:
            k += 1
    return [round((int(np.argmax(post[p:p + 30000])) if p + 1 < len(post) else 0) / 1000.0, 3) for p in pk]


def routing():
    from wormemu.mech import neuromod
    brain, q = gut_brain()
    m = gi.Mech(brain, q, {"defecation": "ip3r", "enteric_muscle": "off", "pboc_protons": "off"})
    W = getattr(m, "nlp_W", None)
    if W is None:
        return dict(pass_=False, note="no nlp_W (unfixed code)")
    ctx = SimpleNamespace(v=np.full(len(brain.cell_names), -30.0), outputs={})
    rest = np.full(len(gi.INT_CELLS), q["int_ca_rest_uM"])

    def rel(c):
        m.gut.step = lambda dt_s, c=c: c.copy()
        pr = m.step(ctx, 1.0)["out"]["peptide_release"]
        return np.array([pr.get(f"nlp-40@{cp}", 0.0) for cp in neuromod.COMPARTMENTS])
    r0 = rel(rest)
    ok, rows = True, []
    for ring in range(1, 10):
        c = rest.copy()
        c[gi.RING == ring] = 1.0
        d = rel(c) - r0
        share = W[gi.RING == ring].sum(0)
        want = d.sum() * share / share.sum()
        good = bool(np.allclose(d, want, rtol=1e-12, atol=1e-12 * abs(d).max()))
        ok &= good
        rows.append(dict(ring=ring, share=[round(float(x), 4) for x in share / share.sum()], pass_=good))
    return dict(pass_=ok, rings=rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ref = len(sys.argv) >= 2 and sys.argv[1] == "ref"
    d, x = run("release_only"), run("direct")
    if ref:
        np.savez(OUT / "nlp40_site_ref.npz", tot=d["tot"], post=d["post"], c9=d["c9"], aex=x["aex"])
        print("reference saved", d["keys"], lags(d["c9"], d["post"]), f"{time.time() - t0:.0f} s")
        return
    r = np.load(OUT / "nlp40_site_ref.npz")
    rel_err = float(np.max(np.abs(d["tot"] - r["tot"]) / np.maximum(np.abs(r["tot"]), 1e-300)))
    out = dict(bar=__doc__.split("Bar (written before running the fixed code")[1].split("Reported, no bar")[0].strip(),
               total=dict(max_rel_err=rel_err, pass_=rel_err <= 1e-12, keys=d["keys"]),
               direct=dict(max_abs_diff_pA=float(np.max(np.abs(x["aex"] - r["aex"]))),
                           pass_=bool(np.array_equal(x["aex"], r["aex"]))),
               routing=routing(),
               report=dict(lag_s_before=lags(r["c9"], r["post"]), lag_s_after=lags(d["c9"], d["post"]),
                           posterior_share_of_total_after=float(d["post"].sum() / d["tot"].sum())),
               wall_s=time.time() - t0)
    (OUT / "nlp40_site_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "bar"}, indent=1))


if __name__ == "__main__":
    main()
