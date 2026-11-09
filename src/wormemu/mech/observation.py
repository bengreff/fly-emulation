"""Row 23, observation: what the instruments see. GCaMP fluorescence per variant, the Randi 2023 optogenetic
actuator, NeuroPAL identity uncertainty, and Tierpsy-style gait features of the body's midline.

GCaMP (toggle "gcamp", takes over brain_layers' lumped layer): the indicator binds Ca cooperatively with
first-order kinetics, dB/dt = k_on c^n (1 - B) - k_off B, k_on = k_off / Kd^n, so the steady state is the measured
Hill curve B = c^n / (c^n + Kd^n) and the indicator's own decay has the measured half-time, k_off = ln 2 / t_half
(structure inferred: the PLAN.md row 23 form, the binding scheme used by indicator-kinetics models; values
measured per variant). Fluorescence F = F_min (1 + (R_f - 1) B), R_f = F_sat / F_apo the dynamic range, and
dF/F0 = (F - F0) / F0 against F0 at the resting Ca (Atanas 2023 / Kato 2015 style baseline). Solved exactly for
Ca held over the step. Forms: gcamp6s (default; Randi 2023 imaged nuclear GCaMP6s, strain AML462, 2 volumes/s),
gcamp6f, gcamp7f (Atanas 2023 imaged NLS-GCaMP7f, strain SWF415, at 1.7 Hz; STAR Methods, PMC10836760),
lumped (brain_layers' first-order layer, one step later, as nested), off. Additive imaging noise per sample
(obs_noise_dff, guessed), drawn from a generator seeded at reset. The Ca it reads: the brain's Eq. 28 pool (ctx.ca,
Nicoletti's submembrane microdomain), or, with mech/capool's ca_bulk on, the bulk cytosolic pool
(outputs['ca_bulk_uM'], NEURON's cadifpmp; cells without one keep ctx.ca). F0 stays at obs_ca_rest_nM either way.

Optogenetics (toggle "opto_gur3", on; no light = no current): GUR-3/PRDX-2, the purple-light-gated system Randi et
al. 2023 (Nature 623:406, arXiv 2208.04790) expressed pan-neuronally and drove with two-photon targeted, temporally
focused illumination of single somata for 0.3 or 0.5 s (read 6 Nov 2026). The current here is a light-gated
non-selective cation conductance with first-order activation and deactivation (inferred structure; GUR-3 is a
gustatory-receptor-family channel downstream of PRDX-2, Bhatla & Horvitz 2015). Every number guessed (no kinetics
reported in the parts opened). The light schedule is observation.SCHEDULE = [(cell, t_on_ms, dur_ms, intensity
0-1), ...], read when the brain is built; empty = no point processes, the brain unchanged.

NeuroPAL (toggle "neuropal", on): each neuron, at reset, is unlabelled with p_unlabelled, else given its own
name with p_correct, else confused with one of its k nearest neighbours along the body axis (inferred: NeuroPAL
confusions are between nearby cells of similar colour; Yemini et al. 2021 Cell 184:272). out['neuropal_id'] is
the assigned cell index per neuron (-1 = unlabelled); neuropal_labels(brain) gives the names. Readout only.

Gait features (gait_features(rec), offline, as Tierpsy runs on recorded skeletons; Javer et al. 2018 Nat Methods
15:645 feature definitions, approximated): midbody speed (signed by head direction), head / midbody / tail bend
angles, the dominant body-bend frequency, wavelength from the curvature phase, path curvature, and the
forward / backward / paused fractions with a speed threshold.
"""
from __future__ import annotations

import numpy as np

from wormemu.mech.senses_base import Conductance, spec

MECHANISMS = [
    ("gcamp", "GCaMP observation: cooperative Ca binding with first-order kinetics, per indicator variant",
     "observation", "gcamp6s"),
    ("opto_gur3", "Optogenetic actuator GUR-3/PRDX-2 (Randi 2023), targeted light on a schedule", "observation", "on"),
    ("neuropal", "NeuroPAL identity uncertainty (unlabelled, wrong-neighbour labels)", "observation", "on"),
    ("gait_features", "Tierpsy-style gait features of the recorded midline (offline readout, gait_features())",
     "observation", "tierpsy"),
]
VARIANTS = ("gcamp6s", "gcamp6f", "gcamp7f")
CHEN = "Chen et al. 2013 Nature 499:295, Supp Table 1 (purified protein; read via a secondary summary, 6 Nov 2026)"
DANA = ("Dana et al. 2019 Nat Methods 16:649 (jGCaMP7), read in the free bioRxiv preprint 10.1101/434589v1 "
        "(8 Nov 2026; not checked against the journal version)")
ZHANG = "Zhang et al. 2023 Nature 615:884 (jGCaMP8; reports jGCaMP7f for comparison)"
RANDI = "Randi et al. 2023 Nature 623:406 / arXiv 2208.04790 (methods read 6 Nov 2026)"
SPECS = [
    spec("obs_gcamp6s_kd_nM", "gcamp", "nM", 144.0, 130.0, 160.0, "measured", CHEN, applies_to="GCaMP6s"),
    spec("obs_gcamp6s_hill", "gcamp", "1", 2.90, 2.5, 3.3, "measured", CHEN, applies_to="GCaMP6s"),
    spec("obs_gcamp6s_range", "gcamp", "1", 63.2, 50.0, 70.0, "measured", CHEN + ": F_sat / F_apo",
         applies_to="GCaMP6s"),
    spec("obs_gcamp6s_thalf_ms", "gcamp", "ms", 550.0, 300.0, 2000.0, "guessed",
         "recalled, not opened: ~0.5 s half-decay after one spike in mouse cortex; slower at 20 C and in nuclei",
         applies_to="GCaMP6s", notes="the paper that would pin it: Chen 2013 Fig 1 / Supp Table 3 (culture, 1 AP)"),
    spec("obs_gcamp6f_kd_nM", "gcamp", "nM", 375.0, 340.0, 410.0, "measured", CHEN, applies_to="GCaMP6f"),
    spec("obs_gcamp6f_hill", "gcamp", "1", 2.27, 2.0, 2.5, "measured", CHEN, applies_to="GCaMP6f"),
    spec("obs_gcamp6f_range", "gcamp", "1", 51.8, 45.0, 60.0, "measured", CHEN + ": F_sat / F_apo",
         applies_to="GCaMP6f"),
    spec("obs_gcamp6f_thalf_ms", "gcamp", "ms", 150.0, 80.0, 600.0, "guessed",
         "recalled, not opened: ~0.15 s half-decay after one spike in mouse cortex", applies_to="GCaMP6f",
         notes="the paper that would pin it: Chen 2013 Fig 1 / Supp Table 3"),
    spec("obs_gcamp7f_kd_nM", "gcamp", "nM", 174.0, 156.0, 192.0, "measured", ZHANG + ": 174 +/- 9 nM",
         applies_to="jGCaMP7f", notes=DANA + " Supp Table 1: 174 +/- 5 nM (purified protein)"),
    spec("obs_gcamp7f_hill", "gcamp", "1", 3.1, 2.3, 3.3, "measured", ZHANG + ": Hill 3.1",
         applies_to="jGCaMP7f", notes=DANA + " Supp Table 1: 2.3 +/- 0.12, the lower bound"),
    spec("obs_gcamp7f_range", "gcamp", "1", 30.19, 27.0, 33.0, "measured",
         DANA + ", Supp Table 1 (purified protein, Fmax/Fmin): 30.19 +/- 0.36 (mean +/- s.e.m.)",
         applies_to="jGCaMP7f", notes="bounds guessed (+-10%, as the 6s and 6f ranges)"),
    spec("obs_gcamp7f_thalf_ms", "gcamp", "ms", 118.0, 100.0, 800.0, "derived",
         DANA + ", Supp Table 1 (purified protein, stopped flow): koff 5.86 +/- 0.01 /s; ln 2 / 5.86 = 118 ms",
         applies_to="jGCaMP7f",
         notes="as the GCaMP6 rows: binding_step's koff is the sensor's own unbinding, which the stopped-flow koff "
               "measures (temperature not stated); the 1-AP half-decay in culture is 265 +- 20 ms (Results), slower "
               "than koff predicts, unlike 6s and 6f; bounds guessed"),
    spec("obs_ca_rest_nM", "gcamp", "nM", 50.0, 20.0, 150.0, "guessed",
         "typical neuronal resting Ca (the F0 reference; brain_layers gcamp_ca_rest_nM)"),
    spec("obs_noise_dff", "gcamp", "dF/F", 0.03, 0.0, 0.2, "guessed",
         "per-sample imaging noise, brain_layers' gcamp_noise_pct (3 %); nuclear GCaMP6s whole-brain SNR"),
    spec("obs_volume_rate_hz", "gcamp", "Hz", 1.7, 1.0, 10.0, "measured",
         "Atanas et al. 2023 Cell 186:4134 STAR Methods (PMC10836760): 'a volume rate of 1.7 Hz (1.4 Hz for the "
         "datasets acquired with the Newport piezo)'; Randi 2023 imaged at 2 vol/s (arXiv 2208.04790v3 Methods, as "
         "relayed); sample_volumes() uses it",
         notes="readout only: gcamp_dff is published every step, sampling is offline"),
    spec("obs_opto_g_nS", "opto_gur3", "nS", 0.3, 0.05, 2.0, "guessed",
         RANDI + ": pulses chosen to evoke modest Ca responses; no conductance reported",
         applies_to="every neuron (pan-neuronal expression)"),
    spec("obs_opto_e_mV", "opto_gur3", "mV", 0.0, -10.0, 10.0, "inferred",
         "non-selective cation channel (GUR-3, gustatory-receptor family; Bhatla & Horvitz 2015 Neuron 85:804)"),
    spec("obs_opto_tau_on_ms", "opto_gur3", "ms", 100.0, 10.0, 1000.0, "guessed", RANDI + ": no kinetics reported"),
    spec("obs_opto_tau_off_ms", "opto_gur3", "ms", 500.0, 50.0, 3000.0, "guessed", RANDI + ": no kinetics reported"),
    spec("obs_neuropal_p_unlabelled", "neuropal", "1", 0.3, 0.05, 0.6, "guessed",
         "Atanas et al. 2023 Cell 186:4134 and Yemini et al. 2021 Cell 184:272 label most but not all head neurons "
         "per animal; fraction not opened", notes="the paper that would pin it: Atanas 2023 Fig S1 / Yemini 2021 Fig 6"),
    spec("obs_neuropal_p_correct", "neuropal", "1", 0.9, 0.7, 0.99, "guessed",
         "Yemini et al. 2021 Cell 184:272: accuracy of labelled IDs, not opened"),
    spec("obs_neuropal_k_neighbours", "neuropal", "1", 3.0, 1.0, 10.0, "guessed",
         "confusions go to one of the k nearest cells along the body axis (inferred structure)"),
    spec("obs_gait_pause_L_s", "gait_features", "L/s", 0.05, 0.01, 0.1, "guessed",
         "forward / backward / paused speed threshold (Yemini et al. 2013 Nat Methods motion-state rule, value "
         "recalled, not opened)", notes="used by gait_features (offline)"),
]
P = {s.id: s.template for s in SPECS}
SCHEDULE: list[tuple[str, float, float, float]] = []   # (cell, t_on_ms, dur_ms, intensity 0-1)


def binding_step(B, c_nM, kd, n, thalf_ms, dt_ms):
    """Exact step of dB/dt = k_on c^n (1 - B) - k_off B with c held over dt."""
    koff = np.log(2.0) / thalf_ms
    a = koff * (np.maximum(c_nM, 0.0) / kd) ** n           # k_on c^n
    r = a + koff
    Binf = a / r
    return Binf + (B - Binf) * np.exp(-r * dt_ms)


def hill(c_nM, kd, n):
    x = (np.maximum(c_nM, 0.0) / kd) ** n
    return x / (1.0 + x)


def dff(B, B0, R):
    return (R - 1.0) * (B - B0) / (1.0 + (R - 1.0) * B0)


class Mech:
    def __init__(self, brain, params, toggles):
        self.brain, self.p = brain, {**P, **params}
        self.form = toggles.get("gcamp", "gcamp6s")
        if self.form == "on":
            self.form = "gcamp6s"
        self.opto_on = toggles.get("opto_gur3", "on") not in ("off", False, None)
        self.pal_on = toggles.get("neuropal", "on") not in ("off", False, None)
        self.bulk = toggles.get("ca_bulk", "off") not in ("off", False, None)
        self.n = len(brain.cell_names)
        self.neuron = ~np.asarray(brain.is_muscle)
        self.sched = [s for s in SCHEDULE if s[0] in brain.idx] if self.opto_on else []
        self.opto = None
        if self.sched:
            cells = sorted({s[0] for s in self.sched})
            self.opto = Conductance(brain, cells, self.p["obs_opto_e_mV"])
            self.opto_k = {c: k for k, c in enumerate(self.opto.cells)}
        self.reset()

    def reset(self):
        p = self.p
        seed = getattr(self.brain, "noise_seed", getattr(self.brain.spec, "seed", None))   # NeuroPAL: the worm's
        self.rng = np.random.default_rng((0 if seed is None else int(seed)) + 2311)
        if self.form in VARIANTS:
            v = self.form
            self.kd, self.hn = p[f"obs_{v}_kd_nM"], p[f"obs_{v}_hill"]
            self.R, self.th = p[f"obs_{v}_range"], p[f"obs_{v}_thalf_ms"]
            self.B0 = hill(p["obs_ca_rest_nM"], self.kd, self.hn)
            self.B = np.full(self.n, self.B0)
        self.m = np.zeros(len(self.opto.cells)) if self.opto is not None else None
        if self.opto is not None:
            self.opto.set(np.zeros(len(self.opto.cells)))
        self.id = self._neuropal() if self.pal_on else None

    def _neuropal(self):
        p, names = self.p, self.brain.cell_names
        neurons = np.flatnonzero(self.neuron)
        pos = np.asarray(self.brain.layers.pos, float)[neurons]
        rng = np.random.default_rng(1000 + (0 if getattr(self.brain.spec, "seed", None) is None
                                            else int(self.brain.spec.seed)))
        k = int(round(p["obs_neuropal_k_neighbours"]))
        out = np.full(self.n, -1, int)
        for j, i in enumerate(neurons):
            u = rng.random()
            if u < p["obs_neuropal_p_unlabelled"]:
                continue
            if rng.random() < p["obs_neuropal_p_correct"]:
                out[i] = i
            else:
                d = np.abs(pos - pos[j])
                d[j] = np.inf
                near = neurons[np.argsort(d, kind="stable")[:k]]
                out[i] = int(near[rng.integers(len(near))])
        return out

    def step(self, ctx, dt_ms):
        p, out = self.p, {}
        if self.form in VARIANTS:
            c = np.asarray(ctx.ca, float)
            if self.bulk:                                      # mech/capool's bulk pool, this step's start
                cb = ctx.outputs.get("ca_bulk_uM")
                c = np.where(np.isfinite(cb), cb, c)
            c = c * 1000.0                                     # uM -> nM
            self.B = binding_step(self.B, c, self.kd, self.hn, self.th, dt_ms)
            out["gcamp_dff"] = dff(self.B, self.B0, self.R) + self.rng.normal(0.0, p["obs_noise_dff"], self.n)
        elif self.form == "lumped":
            L = self.brain.layers
            saved = L.on
            L.on = set(saved) | {"gcamp"}
            try:
                out["gcamp_dff"] = L.gcamp(np.asarray(ctx.ca, float), dt_ms)
            finally:
                L.on = saved
        if self.opto is not None:
            light = np.zeros(len(self.opto.cells))
            for cell, t0, dur, inten in self.sched:
                if t0 <= ctx.t_ms < t0 + dur:
                    light[self.opto_k[cell]] = max(light[self.opto_k[cell]], inten)
            tau = np.where(light > self.m, p["obs_opto_tau_on_ms"], p["obs_opto_tau_off_ms"])
            self.m = light + (self.m - light) * np.exp(-dt_ms / tau)
            self.opto.set(p["obs_opto_g_nS"] * self.m)
            out["opto_g_nS"] = float((p["obs_opto_g_nS"] * self.m).sum())
        if self.id is not None:
            out["neuropal_id"] = self.id
        return {"out": out}


def neuropal_labels(brain, ids) -> list:
    """Assigned names per cell ('' = unlabelled), from out['neuropal_id']."""
    return [brain.cell_names[j] if j >= 0 else "" for j in ids]


def sample_volumes(t_ms, trace, rate_hz=P["obs_volume_rate_hz"]):
    """What a whole-brain microscope records: the trace sampled at the volume rate (nearest step)."""
    t_ms = np.asarray(t_ms)
    ts = np.arange(t_ms[0], t_ms[-1], 1000.0 / rate_hz)
    k = np.clip(np.searchsorted(t_ms, ts), 0, len(t_ms) - 1)
    return ts, np.asarray(trace)[k]


def gait_features(rec: dict, frame=None, length_mm: float = 1.0, pause_L_s: float = P["obs_gait_pause_L_s"]) -> dict:
    """Tierpsy-style features of a recorded body (metaworm.load / Body frames): rec = {"X": frames, "t": s, ...}."""
    from wormemu.body import metaworm as mw
    fr = frame or mw.Frame(rec["meta"], rec["X"][0])
    X, t = rec["X"], np.asarray(rec["t"])
    mid = fr.midline(X)                                     # [f, n, 3], head first
    L = fr.length
    s, k = fr.curvature(X)                                  # kappa * L
    # bend angles (degrees): the turning angle summed over each third of the interior nodes (Tierpsy head/mid/tail)
    seg = np.linalg.norm(np.diff(mid, axis=1), axis=2).mean() / L
    ang = np.degrees(k * seg)
    thirds = {"head": s < 1 / 6 + 0.1, "midbody": (s > 0.4) & (s < 0.6), "tail": s > 5 / 6 - 0.1}
    bends = {f"{n}_bend_mean_deg": float(ang[:, m].sum(1).mean()) for n, m in thirds.items()}
    bends.update({f"{n}_bend_rms_deg": float(np.sqrt((ang[:, m].sum(1) ** 2).mean())) for n, m in thirds.items()})
    # midbody velocity, signed by the head direction
    c = mid[:, fr.n // 2]
    v = np.gradient(c, t, axis=0)
    hd = mid[:, 0] - c
    hd /= np.linalg.norm(hd, axis=1, keepdims=True)
    speed = (v * hd).sum(1) / L                              # L/s
    mode = np.where(speed > pause_L_s, 1, np.where(speed < -pause_L_s, -1, 0))
    # dominant bend frequency of the midbody curvature (FFT of the mean-removed signal)
    km = k[:, (s > 0.3) & (s < 0.7)].mean(1)
    km = km - km.mean()
    f = np.fft.rfftfreq(len(t), t[1] - t[0])
    pw = np.abs(np.fft.rfft(km * np.hanning(len(km))))
    f_dom = float(f[1:][pw[1:].argmax()]) if len(f) > 1 else 0.0
    # wavelength from the phase gradient of the curvature at f_dom
    z = (np.exp(-2j * np.pi * f_dom * t) @ (k - k.mean(0))) / len(t)
    band = (s >= 0.1) & (s <= 0.9)
    slope = np.polyfit(s[band], np.unwrap(np.angle(z[band])), 1)[0]
    # path curvature of the midbody track (1/L), from the in-plane turning of the velocity
    vu = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)
    turn = np.linalg.norm(np.diff(vu, axis=0), axis=1)
    dist = np.linalg.norm(np.diff(c, axis=0), axis=1)
    return {"speed_mean_L_s": float(speed.mean()), "speed_mean_um_s": float(speed.mean() * length_mm * 1e3),
            "forward_frac": float((mode == 1).mean()), "backward_frac": float((mode == -1).mean()),
            "paused_frac": float((mode == 0).mean()), "bend_freq_hz": f_dom,
            "wavelength_L": float(2 * np.pi / abs(slope)) if slope else float("inf"),
            "path_curvature_per_L": float(turn.sum() / max(dist.sum() / L, 1e-12)),
            "max_abs_curvature_kL": float(np.abs(k).max()), **bends}
