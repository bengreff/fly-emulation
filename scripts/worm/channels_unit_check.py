"""Row 4 unit check (night of 6 Nov 2026, wneuron): Nicoletti 2024's AIY current clamp, published mods against
wormemu's ported KQT-1 and bulk-Ca SLO-1 (mech/channels) and against the brain's own channel library.

The bar was written before the first run (docs/worm/night/2026-11-06_wneuron.md, "Unit-check bars"):
  ref  Nicoletti's published mods and AIY script values (AIY_simulation_iclamp.py), in their own process
  A    the same, with wormemu's kqt1 and slo1iso mods, kinetics from the channel_library Specs, densities from
       dens_kqt1_AIY / dens_slo1iso_AIY, cai_to_uM = 1 and cai 0.05 uM:      pass if within 0.1 mV at every step
  A0   A without the two channels: reported (does the check test anything?)
  W    BAAIWorm's egl19 / slo1_egl19 / nca / shl1 mods (their defaults), pas, wormemu's kqt1 / slo1iso, every
       density Nicoletti's AIY value:                                           pass if within 2 mV at every step
Each model runs in its own process (NEURON loads one mechanism set per process).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/channels_unit_check.py PUBLISHED_REPO_DIR [--forms]
       (a checkout of github.com/martinanicoletti92/CelegansInterMotorNeuronsModels; the commit is recorded)
Output: runs/worm/night_wneuron/channels_unit_check.json and .png

--forms (DEBUG_TRIAGE line 1, wbrain2, 8 Nov 2026; bars in docs/worm/night/2026-11-08_wbrain2.md, "Line 1"): the W
model under mech/channel_forms' EGL-19 and SHL-1 forms, against Fig 3C of Nicoletti 2024 (the AIY V-I curve, model,
digitised: data/worm/ephys/nicoletti2024_fig3c/aiy_vi_model.csv) and against ref. Wv is W built from the vendored mods
as they are (no build-time patch): the patched default must equal it bit for bit. Mode W:<egl19 form>:<shl1 form>.
Output: runs/worm/wbrain2/channel_forms_check.json and .png
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs" / "worm" / "night_wneuron"
sys.path.insert(0, str(ROOT / "src"))

# AIY_simulation.py / AIY_simulation_iclamp.py, as published
SURF_CM2, CM, ELEAK, EK, ECA = 65.89e-8, 1.6, -89.57, -80.0, 60.0
AMPS_NA = np.linspace(-0.015, 0.035, 11)
DELAY, DUR, TSTOP, DT, V0 = 1000.0, 5000.0, 11000.0, 0.4, -60.0
SS_WIN, PEAK_WIN = (5990.0, 6000.0), (1000.0, 1300.0)
CAI0_MM = 5e-5                                   # NEURON's default cai0, which the published AIY model runs at
PORTED = ("kqt1", "slo1iso")
BAAI_NAME = {"egl19": ("egl19", "gbegl19"), "slo1egl19": ("slo1_egl19", "gbslo1"), "nca": ("nca", "gbnca"),
             "shl1": ("shl1", "gbshl1")}
FIG3C = ROOT / "data" / "worm" / "ephys" / "nicoletti2024_fig3c" / "aiy_vi_model.csv"
FORM_MODES = ["ref", "Wv", "W", "W:n24_code:n24_code", "W:n24_printed:n24_printed", "W:n24_code:off", "W:off:n24_code",
              "W:n24_printed:off", "W:off:n24_printed", "W:off:off:slo24", "W:n24_code:n24_code:slo24",
              "ref:eca60", "W:off:off:eca60", "W:n24_code:n24_code:eca60", "W:n24_code:n24_code:slo24:eca60",
              "W:n24_printed:n24_printed:eca60"]
# diagnostics, added after the pre-registered run failed its bar (night file, line 1): suffix :slo24 sets the SLO-1
# rate constants of the authors' slo1egl19.mod, which BAAIWorm's slo1_egl19.mod carries rounded to two or three
# figures; suffix :eca60 holds E_Ca at the 60 mV the authors' script sets (seg.eca = 60), which NEURON otherwise
# replaces at finitialize with the Nernst value of cai0 / cao0 at 6.3 C, 127.6 mV (measured), because slo1iso READs
# cai. The published model, and so Fig 3C, ran at 127.6 mV; BAAIWorm's nanodomain hard-codes (v - 60).
SLO24 = dict(wyx=0.012643, wxy=-0.027527, wom=3.152961, wop=0.156217, kxy=55.726186, nxy=1.299198, kyx=34.338784)
VC_STEPS = np.arange(-80.0, 41.0, 10.0)            # mV, from a -60 mV hold, 600 ms steps (diagnostic, --forms)


def _compile(mods, tag):
    d = Path.home() / ".cache" / "wormemu" / "nic24" / hashlib.sha1(
        b"".join(m.name.encode() + m.read_bytes() for m in mods)).hexdigest()[:12]
    libs = list(d.glob("*/libnrnmech.*")) + list(d.glob("*/.libs/libnrnmech.so"))
    if not libs:
        (d / "src").mkdir(parents=True, exist_ok=True)
        for m in mods:
            shutil.copy(m, d / "src" / m.name)
        exe = shutil.which("nrnivmodl") or str(Path(sys.executable).parent / "nrnivmodl")
        with open(d / "build.log", "w") as log:
            subprocess.run([exe, "src"], cwd=d, check=True, stdout=log, stderr=subprocess.STDOUT)
        libs = list(d.glob("*/libnrnmech.*")) + list(d.glob("*/.libs/libnrnmech.so"))
    return str(libs[0])


def model(mode, pub):
    from neuron import h
    from wormemu.mech import channels as C
    pub = Path(pub)
    spec = {s.id: s.template for s in C.SPECS}
    eca60 = mode.endswith(":eca60")
    mode = mode.removesuffix(":eca60")
    if mode.startswith("W:") or mode == "W":
        from wormemu.brain import _neuron
        from wormemu.mech import channel_forms as CF
        h = _neuron()
        CF.restore(h)
        if mode != "W":
            for ch, f in zip(("egl19", "shl1"), mode.split(":")[1:3]):
                for name, x in CF.values(f, ch).items():
                    for mod in (CF.EGL19_MODS if ch == "egl19" else ("shl1",)):
                        setattr(h, f"{name}_{mod}", x)
            if ":slo24" in mode:
                for name, x in SLO24.items():
                    setattr(h, f"{name}_slo1_egl19", x)
            mode = "W"
    elif mode == "Wv":                              # the vendored BAAIWorm mods as they are, ours for kqt1 / slo1iso
        mods = [ROOT / "third_party" / "baaiworm" / "mod" / f"{m}.mod" for m, _ in BAAI_NAME.values()]
        h.nrn_load_dll(_compile(mods + [C.MODS / f"{c}.mod" for c in PORTED], mode))
        h.load_file("stdrun.hoc")
        mode = "W"
    else:
        mods = sorted(pub.glob("*.mod"))
        if mode == "A":
            mods = [m for m in mods if m.stem not in PORTED] + [C.MODS / f"{c}.mod" for c in PORTED]
        h.nrn_load_dll(_compile(mods, mode))
        h.load_file("stdrun.hoc")
    g = {c: C.fitted_density("AIY", c) for c in C.FIT_NS["AIY"]}
    if mode in ("A", "W"):
        g["kqt1"], g["slo1iso"] = spec["dens_kqt1_AIY"], spec["dens_slo1iso_AIY"]
        for ch in PORTED:
            for name, _, _ in C.KINETICS[ch]:
                setattr(h, f"{name}_{ch}", spec[f"kin_{ch}_{name}"])
        h.cai_to_uM_slo1iso = C.UNIT_CAI_UM
        h.cai0_ca_ion = CAI0_MM * 1000.0
    soma = h.Section(name="soma")
    soma.L = soma.diam = math.sqrt(SURF_CM2 / math.pi) * 1e4
    soma.cm, soma.Ra = CM, 100.0
    if mode == "W":
        for c, (mod, var) in BAAI_NAME.items():
            soma.insert(mod)
            setattr(soma(0.5), f"{var}_{mod}", g[c])
        soma.insert("pas")
        soma(0.5).pas.g, soma(0.5).pas.e = g["leak"], ELEAK
        chans = PORTED
    else:
        chans = ["egl19", "slo1egl19", "nca", "leak", "shl1"] + ([] if mode == "A0" else list(PORTED))
    for c in chans:
        soma.insert(c)
        getattr(soma(0.5), c).gbar = g[c]
    if mode != "W":
        soma(0.5).leak.e = ELEAK
    for seg in soma:
        if h.ismembrane("ca_ion", sec=soma):
            seg.eca = ECA
        if h.ismembrane("k_ion", sec=soma):
            seg.ek = EK
    if eca60:
        h.ion_style("ca_ion", 1, 1, 0, 0, 0, sec=soma)    # concentrations and eca constant, no Nernst at init
        soma(0.5).eca = ECA
    stim = h.IClamp(soma(0.5))
    stim.delay, stim.dur = DELAY, DUR
    v, t = h.Vector(), h.Vector()
    v.record(soma(0.5)._ref_v)
    t.record(h._ref_t)
    ss, pk, traces = [], [], []
    for j, a in enumerate(AMPS_NA):
        stim.amp = a
        h.tstop, h.dt = TSTOP, DT
        h.finitialize(V0)
        h.run()                                     # as published: run() re-initialises at v_init, dt from stdrun
        V, T = v.as_numpy().copy(), t.as_numpy().copy()
        w = (T >= SS_WIN[0]) & (T <= SS_WIN[1])
        p = (T >= PEAK_WIN[0]) & (T <= PEAK_WIN[1])
        ss.append(float(V[w].mean()))
        pk.append(float(V[p].min() if j <= 2 else V[p].max()))
        traces.append(V[::400].tolist())
    return dict(mode=mode, ss=ss, peak=pk, dt=float(h.dt), v_init=float(h.v_init), t=T[::400].tolist(),
                traces=traces, cai=float(soma(0.5).cai), eca=float(soma(0.5).eca), celsius=float(h.celsius))


def main(pub):
    OUT.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    res = {}
    for mode in ("ref", "A", "A0", "W"):
        r = subprocess.run([sys.executable, __file__, "--mode", mode, pub], capture_output=True, text=True, env=env)
        assert r.returncode == 0, r.stderr[-3000:]
        res[mode] = json.loads(r.stdout.strip().splitlines()[-1])
    ref = res["ref"]
    out = dict(published_repo=str(pub), amps_pA=(AMPS_NA * 1000).round(3).tolist(), ref_ss=ref["ss"],
               ref_peak=ref["peak"], dt_used=ref["dt"], v_init_used=ref["v_init"])
    try:
        out["commit"] = subprocess.run(["git", "-C", pub, "rev-parse", "HEAD"], capture_output=True,
                                       text=True).stdout.strip() or "84726a72 (copied tree, no .git)"
    except OSError:
        out["commit"] = "84726a72 (copied tree, no .git)"
    for mode, bar in (("A", 0.1), ("A0", None), ("W", 2.0)):
        d = max(max(abs(a - b) for a, b in zip(res[mode]["ss"], ref["ss"])),
                max(abs(a - b) for a, b in zip(res[mode]["peak"], ref["peak"])))
        out[mode] = dict(max_abs_mV=d, ss=res[mode]["ss"], peak=res[mode]["peak"], bar_mV=bar,
                         passed=None if bar is None else bool(d <= bar))
    (OUT / "channels_unit_check.json").write_text(json.dumps(out, indent=1))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    t = np.array(ref["t"])
    for j in (0, 3, 6, 10):
        for mode, st in (("ref", "k-"), ("A", "r--"), ("A0", "b:"), ("W", "g-.")):
            ax[0].plot(t, res[mode]["traces"][j], st, lw=1, label=mode if j == 0 else None)
    ax[0].set(xlabel="t (ms)", ylabel="V (mV)", title="AIY current clamp, -15 / 0 / +15 / +35 pA")
    ax[0].legend()
    amps = AMPS_NA * 1000
    for mode, st in (("ref", "ko-"), ("A", "r+--"), ("A0", "bs:"), ("W", "g^-.")):
        ax[1].plot(amps, res[mode]["ss"], st, label=f"{mode} steady state")
        ax[1].plot(amps, res[mode]["peak"], st, alpha=0.4)
    ax[1].set(xlabel="I (pA)", ylabel="V (mV)", title="steady state (solid) and peak (faint)")
    ax[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "channels_unit_check.png", dpi=110)
    print(json.dumps({k: (v if not isinstance(v, dict) else {kk: v[kk] for kk in ("max_abs_mV", "passed")})
                      for k, v in out.items() if k not in ("ref_ss", "ref_peak")}))


def vclamp(mode, pub):
    """EGL-19 and SHL-1 each alone in a voltage-clamped AIY soma at Nicoletti's AIY density: the current at 2, 20
    and 595 ms into each step. ref = the authors' mods; W:<egl19 form>:<shl1 form> = BAAIWorm's under the forms."""
    from neuron import h
    from wormemu.mech import channels as C
    g = {c: C.fitted_density("AIY", c) for c in C.FIT_NS["AIY"]}
    if mode == "ref":
        h.nrn_load_dll(_compile(sorted(Path(pub).glob("*.mod")), "ref"))
        h.load_file("stdrun.hoc")
        ins = {"egl19": ("egl19", "gbar"), "shl1": ("shl1", "gbar")}
    else:
        from wormemu.brain import _neuron
        from wormemu.mech import channel_forms as CF
        h = _neuron()
        CF.restore(h)
        for ch, f in zip(("egl19", "shl1"), mode.split(":")[1:3]):
            for name, x in CF.values(f, ch).items():
                setattr(h, f"{name}_{ch}", x)
        ins = {"egl19": ("egl19", "gbegl19"), "shl1": ("shl1", "gbshl1")}
    rec, keep = {}, []
    for ch, (mod, var) in ins.items():                 # one soma per channel, clamped together
        soma = h.Section(name=f"soma_{ch}")
        soma.L = soma.diam = math.sqrt(SURF_CM2 / math.pi) * 1e4
        soma.insert(mod)
        setattr(soma(0.5), f"{var}_{mod}", g[ch])
        vc = h.SEClamp(soma(0.5))
        vc.rs, vc.dur1, vc.dur2, vc.dur3 = 1e-3, 1000.0, 600.0, 10.0
        rec[ch] = h.Vector()
        rec[ch].record(getattr(soma(0.5), "_ref_ica" if ch == "egl19" else "_ref_ik"))
        keep.append((soma, vc))
    t = h.Vector()
    t.record(h._ref_t)
    out = {ch: [] for ch in ins}
    for vs in VC_STEPS:
        for soma, vc in keep:
            vc.amp1, vc.amp2, vc.amp3 = -60.0, float(vs), -60.0
        h.dt, h.tstop = 0.025, 1600.0
        h.finitialize(-60.0)
        for soma, vc in keep:
            for seg in soma:
                if h.ismembrane("ca_ion", sec=soma):
                    seg.eca = ECA
                if h.ismembrane("k_ion", sec=soma):
                    seg.ek = EK
        h.finitialize(-60.0)
        h.continuerun(1600.0)
        T = t.as_numpy()
        for ch in ins:
            out[ch].append([float(np.interp(1000.0 + d, T, rec[ch].as_numpy())) for d in (2.0, 20.0, 595.0)])
    return out


def forms(pub):
    out_dir = ROOT / "runs" / "worm" / "wbrain2"
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    res = {}
    for mode in FORM_MODES:
        r = subprocess.run([sys.executable, __file__, "--mode", mode, pub], capture_output=True, text=True, env=env)
        assert r.returncode == 0, (mode, r.stderr[-3000:])
        res[mode] = json.loads(r.stdout.strip().splitlines()[-1])
    import csv
    fig = [float(r["v_mV"]) for r in csv.DictReader(l for l in open(FIG3C) if not l.startswith("#"))]
    out = dict(published_repo=str(pub), amps_pA=(AMPS_NA * 1000).round(3).tolist(), fig3c=fig, modes={})
    for mode in FORM_MODES:
        ss, rf = res[mode]["ss"], res["ref:eca60" if mode.endswith(":eca60") else "ref"]
        out["modes"][mode] = dict(ss=ss, peak=res[mode]["peak"], eca=res[mode]["eca"], ref_for_vs_ref=
                                  "ref:eca60" if mode.endswith(":eca60") else "ref",
                                  vs_fig_max_mV=max(abs(a - b) for a, b in zip(ss, fig)),
                                  vs_ref_ss_max_mV=max(abs(a - b) for a, b in zip(ss, rf["ss"])),
                                  vs_ref_peak_max_mV=max(abs(a - b) for a, b in zip(res[mode]["peak"], rf["peak"])))
    out["neutral_W_vs_Wv_max_mV"] = max(max(abs(a - b) for a, b in zip(res["W"][k], res["Wv"][k]))
                                        for k in ("ss", "peak"))
    out["neutral_traces_identical"] = res["W"]["traces"] == res["Wv"]["traces"]
    out["vc_steps_mV"], out["vc"] = VC_STEPS.tolist(), {}
    for mode in ("ref", "W:off:off", "W:n24_code:n24_code", "W:n24_printed:n24_printed"):
        r = subprocess.run([sys.executable, __file__, "--vc", mode, pub], capture_output=True, text=True, env=env)
        assert r.returncode == 0, (mode, r.stderr[-3000:])
        out["vc"][mode] = json.loads(r.stdout.strip().splitlines()[-1])
    for mode in ("W:off:off", "W:n24_code:n24_code", "W:n24_printed:n24_printed"):
        out["vc"][mode]["rel_max_vs_ref"] = {
            ch: max(abs(a - b) / max(abs(np.array(out["vc"]["ref"][ch])).max(), 1e-30)
                    for ra, rb in zip(out["vc"][mode][ch], out["vc"]["ref"][ch]) for a, b in zip(ra, rb))
            for ch in ("egl19", "shl1")}
    (out_dir / "channel_forms_check.json").write_text(json.dumps(out, indent=1))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, ax = plt.subplots(1, 2, figsize=(13, 5))
    amps = AMPS_NA * 1000
    ax[0].plot(amps, fig, "rs", ms=9, mfc="none", label="Fig 3C model (digitised)")
    sty = {"ref": "k.-", "W": "g^-", "W:n24_code:n24_code": "b+-", "W:n24_printed:n24_printed": "m x--",
           "ref:eca60": "k.:", "W:n24_code:n24_code:eca60": "b+:", "W:off:off:eca60": "g^:"}
    for mode, st in sty.items():
        ax[0].plot(amps, res[mode]["ss"], st.replace(" ", ""), lw=1, label=mode)
        ax[1].plot(amps, np.array(res[mode]["ss"]) - np.array(fig), st.replace(" ", ""), lw=1, label=mode)
    ax[0].set(xlabel="I (pA)", ylabel="steady-state V (mV)", title="AIY V-I: forms of EGL-19 and SHL-1")
    ax[1].axhspan(-2, 2, color="0.9")
    ax[1].set(xlabel="I (pA)", ylabel="model - Fig 3C (mV)", title="difference from the figure (bar +-2 mV shaded)")
    ax[0].legend(fontsize=7)
    fig_.tight_layout()
    fig_.savefig(out_dir / "channel_forms_check.png", dpi=110)
    print(json.dumps({m: {k: round(v, 3) for k, v in d.items() if k.endswith("_mV")} for m, d in out["modes"].items()}))
    print(json.dumps({k: out[k] for k in ("neutral_W_vs_Wv_max_mV", "neutral_traces_identical")}))
    print(json.dumps({m: out["vc"][m]["rel_max_vs_ref"] for m in out["vc"] if m != "ref"}))


if __name__ == "__main__":
    if sys.argv[1] == "--mode":
        print(json.dumps(model(sys.argv[2], sys.argv[3])))
    elif sys.argv[1] == "--vc":
        print(json.dumps(vclamp(sys.argv[2], sys.argv[3])))
    elif "--forms" in sys.argv:
        forms(sys.argv[1])
    else:
        main(sys.argv[1])
