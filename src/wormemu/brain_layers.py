"""The worm brain's layers that no ported project has, at general ranges.

BAAIWorm (ported, NEURON) supplies the neurons, synapses, gap junctions and passive body-wall muscles. Everything
else the worm needs is here, each as a small lumped model whose parameters are declared next to it in SPECS. The
ledger (scripts/worm/build_ledger.py) reads SPECS, so a number exists in the ledger because the code uses it.

Every number below is a template value inside a general range. Where docs/worm/research/param_ranges.csv has a
literature row the spec names it in `lit`, and the ledger takes bounds, label and source from that row (literature
wins). Everything else is labelled guessed with a guessed range. None of it is fitted.

Layers (mechanism ids; the toggle and its default are in MECHANISMS):
  sensory transduction, one mechanism per modality      stimulus -> current (pA) into the receptor neurons
  muscle_ca, muscle_activation (excitation-contraction)   BWM soma V -> Ca -> activation [0, 1] for the body
  peptides, monoamines (well-mixed, by family)           release from expressing neurons -> receptor current
  glia (lumped amphid sheath)                            a gain on amphid sensory currents
  pharynx (lumped pump oscillator)                       pharynx_activation, pumps
  defecation (intestinal clock)                          pBoc/aBoc/Exp: posterior BWM boost, enteric_activation
  egg_laying (two-state)                                 sex_muscle_activation, eggs_laid
  metabolism (lumped energy store)                       a state; feeds nothing yet
  gcamp (observation)                                    Ca -> GCaMP dF/F
  homeostasis, slow_signalling (plasticity)              a slow bias current per neuron; hours-scale odour gain
  gap_rectification                                      applied by the brain to AVA-class gap junctions
The expression-to-physiology map (CeNGEN gating which channels a cell has) is the brain's `expression_map` toggle.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Spec:
    """One numeric unknown as the code uses it. If `lit` names a param_ranges.csv row, the ledger takes the
    bounds, label and source from that row; template must lie inside them."""
    id: str
    mechanism: str
    unit: str
    template: float
    lo: float
    hi: float
    source: str = "guessed"
    label: str = "guessed"
    lit: str = ""
    grain: str = "global"
    applies_to: str = "whole worm"
    notes: str = ""
    # scan | rule | gap | residual (wormemu.params.ROLES); "" = from the label: measured, published_fit, derived and
    # inferred are scan, guessed and absent are gap
    role: str = ""


# --- mechanisms: id, name, layer, toggle, default state, source ------------------------------------------------
# default "on" = part of the template worm; "off" = neutral until adopted. Ben, 6 Nov 2026: every mechanism on in the
# template worm, the simpler nested forms as toggles; so the neuromodulator, plasticity and rectification layers are on.
MECHANISMS = [
    ("sens_salt", "Salt sensing (ASEL ON, ASER OFF)", "sensory", "on"),
    ("sens_odor_attract", "Attractive odours (AWA ON; AWC OFF)", "sensory", "on"),
    ("sens_repellent", "Repellents and nociception (ASH, ADL, AWB, PHA/PHB)", "sensory", "on"),
    ("sens_thermo", "Thermosensation (AFD around T*)", "sensory", "on"),
    ("sens_o2", "Oxygen (URX/AQR/PQR rise, BAG fall)", "sensory", "on"),
    ("sens_co2", "Carbon dioxide (BAG)", "sensory", "on"),
    ("sens_light", "Light (LITE-1 in ASJ, ASK, ASH, AWB, ASI)", "sensory", "on"),
    ("sens_food", "Food cue at the mouth (ADF, ASI, ASJ, NSM)", "sensory", "on"),
    ("sens_touch_gentle", "Gentle touch (MEC-4 in ALM, AVM, PLM, PVM)", "sensory", "on"),
    ("sens_touch_harsh", "Harsh and nose touch (PVD, FLP, ASH, OLQ, IL1)", "sensory", "on"),
    ("sens_tap", "Plate tap (all touch receptor neurons)", "sensory", "on"),
    ("sens_proprio", "Proprioception (B-type stretch, DVA, SMD)", "sensory", "on"),
    ("muscle_ca", "BWM membrane V -> Ca (lumped, passive muscles)", "muscle", "on"),
    ("muscle_activation", "BWM Ca -> activation (Hill, rise/decay)", "muscle", "on"),
    ("peptides", "Neuropeptide signalling by ligand-GPCR pair (well mixed)", "neuromodulation", "on"),
    ("monoamines", "Monoamine signalling (5-HT, DA, TA, OA; well mixed)", "neuromodulation", "on"),
    ("glia", "Amphid sheath glia, lumped as a sensory gain", "glia", "off"),
    ("pharynx", "Pharyngeal pumping oscillator (lumped)", "organ", "on"),
    ("defecation", "Defecation motor programme clock (intestine)", "organ", "on"),
    ("egg_laying", "Egg-laying two-state circuit (lumped HSN/VC/vulval muscles)", "organ", "on"),
    ("metabolism", "Energy store (lumped)", "organ", "off"),
    ("gcamp", "GCaMP observation model", "observation", "on"),
    ("homeostasis", "Homeostatic self-tuning: a slow bias current pulls each neuron's V toward a target", "plasticity",
     "on"),
    ("slow_signalling", "Hours-scale sensory adaptation (EGL-4, CMK-1), lumped as a slow gain drift", "plasticity",
     "on"),
    ("gap_rectification", "Rectifying gap junctions (AVA-A class UNC-7/UNC-9)", "gap", "on"),
]

S = Spec
SPECS: list[Spec] = [
    # sensory: current per unit of transformed stimulus u, adaptation u - a * lowpass(u, tau)
    S("salt_gain_pA", "sens_salt", "pA", 10, 0, 100, applies_to="ASEL, ASER"),
    S("salt_c0_mM", "sens_salt", "mM", 10, 0.1, 200, notes="u = log(1 + c/c0)"),
    S("salt_tau_adapt_s", "sens_salt", "s", 10, 1, 30, lit="J1"),
    S("salt_adapt_frac", "sens_salt", "1", 0.8, 0, 1),
    S("odor_gain_pA", "sens_odor_attract", "pA", 10, 0, 100, applies_to="AWAL/R, AWCL/R"),
    S("odor_c0_uM", "sens_odor_attract", "uM", 1, 0.001, 1000),
    S("odor_tau_adapt_s", "sens_odor_attract", "s", 3, 1, 10, lit="J2"),
    S("odor_adapt_frac", "sens_odor_attract", "1", 0.7, 0, 1),
    S("repel_gain_pA", "sens_repellent", "pA", 15, 0, 100, applies_to="ASH, ADL, AWB, PHA, PHB"),
    S("repel_c0", "sens_repellent", "mM or uM", 1, 0.001, 1000, notes="one half-saturation for every repellent "
      "channel (mM for glycerol, copper, quinine, SDS; uM for octanol, nonanone)"),
    S("repel_tau_adapt_s", "sens_repellent", "s", 5, 0.2, 60),
    S("repel_adapt_frac", "sens_repellent", "1", 0.5, 0, 1),
    S("thermo_gain_pA_per_C", "sens_thermo", "pA/C", 5, 0, 50, applies_to="AFDL, AFDR"),
    S("thermo_Tstar_C", "sens_thermo", "C", 20, 15, 25, lit="J5", notes="threshold, tracks cultivation"),
    S("thermo_tau_adapt_s", "sens_thermo", "s", 30, 1, 600),
    S("o2_gain_pA_per_pct", "sens_o2", "pA/%", 1.5, 0, 20, applies_to="URX, AQR, PQR (+), BAG (-)"),
    S("o2_threshold_pct", "sens_o2", "%", 10, 0, 21, lit="J9"),
    S("co2_gain_pA_per_pct", "sens_co2", "pA/%", 5, 0, 50, applies_to="BAGL, BAGR"),
    S("co2_threshold_pct", "sens_co2", "%", 2, 0.5, 10, lit="J10"),
    S("light_gain_pA_per_mWmm2", "sens_light", "pA per mW/mm2", 20, 0, 200, applies_to="ASJ, ASK, ASH, AWB, ASI"),
    S("food_gain_pA", "sens_food", "pA", 5, 0, 50, applies_to="ADF, ASI, ASJ, NSM"),
    S("food_od0", "sens_food", "OD600", 0.5, 0.01, 5),
    S("touch_gain_pA", "sens_touch_gentle", "pA", 30, 0, 200, applies_to="ALML/R, AVM, PLML/R, PVM"),
    S("touch_f0_uN", "sens_touch_gentle", "uN", 1, 0.05, 20),
    S("touch_tau_adapt_ms", "sens_touch_gentle", "ms", 50, 10, 200, lit="J7"),
    S("touch_adapt_frac", "sens_touch_gentle", "1", 0.9, 0, 1),
    S("harsh_gain_pA", "sens_touch_harsh", "pA", 30, 0, 200, applies_to="PVD, FLP, ASH, OLQ, IL1"),
    S("harsh_f0_uN", "sens_touch_harsh", "uN", 10, 0.5, 200),
    S("tap_gain_pA", "sens_tap", "pA", 30, 0, 200, applies_to="ALM, AVM, PLM, PVM"),
    S("tap_tau_ms", "sens_tap", "ms", 20, 2, 200),
    S("proprio_gain_pA_mm", "sens_proprio", "pA per 1/mm", 2, 0, 50, applies_to="VB, DB, DVA, SMD",
      notes="no measured current per unit curvature found (param_ranges J13 DVA and J14 SMD not retrieved), so the "
            "gain and its range are guessed, not cited"),
    S("proprio_field_frac", "sens_proprio", "body length", 0.4, 0.25, 0.5, lit="J12",
      notes="a B-type neuron senses the mean curvature over this length ANTERIOR of its soma (Wen et al. 2012: "
            "anterior bending drives the region posterior to it); posterior until 5 Nov, which contradicted J12"),
    # muscle: V -> Ca (passive BAAIWorm muscles have no Ca channel; lumped sigmoid) and Ca -> activation
    S("mca_vhalf_mV", "muscle_ca", "mV", -20, -40, 0),
    S("mca_k_mV", "muscle_ca", "mV", 5, 1, 15),
    S("mca_max_uM", "muscle_ca", "uM", 1, 0.1, 10),
    S("mact_hill", "muscle_activation", "1", 2, 1, 4, lit="F7"),
    S("mact_khalf_uM", "muscle_activation", "uM", 0.5, 0.05, 5),
    S("mact_tau_rise_ms", "muscle_activation", "ms", 50, 20, 100, lit="F8"),
    S("mact_tau_decay_ms", "muscle_activation", "ms", 100, 50, 200, lit="F9"),
    # neuromodulation (well mixed: one pseudocoelomic concentration per ligand)
    S("pep_release_nM_per_s", "peptides", "nM/s per releasing neuron", 0.05, 0.0001, 10, grain="family",
      applies_to="each ligand gene", notes="released at rate x sigmoid((V - Vth_release)/5 mV)"),
    S("pep_release_vth_mV", "peptides", "mV", -30, -50, 0),
    S("pep_clear_tau_s", "peptides", "s", 100, 10, 600, lit="D4"),
    S("pep_ec50_nM", "peptides", "nM", 10, 0.0001, 500, grain="pairing", applies_to="each ligand-GPCR pair",
      notes="measured per pair in Beets et al. 2023 (all <= 500 nM by the pair list's inclusion rule); the per-pair "
            "values are not yet in the repo, so the template uses one guessed value"),
    S("pep_gain_pA", "peptides", "pA", 2, -20, 20, grain="gene", applies_to="each GPCR gene",
      notes="current at full receptor activation; sign (G-protein class) unknown, template +"),
    S("ma_release_nM_per_s", "monoamines", "nM/s per releasing neuron", 1, 0.001, 100, grain="family",
      applies_to="5-HT, DA, TA, OA"),
    S("ma_release_vth_mV", "monoamines", "mV", -30, -50, 0),
    S("ma_clear_tau_s", "monoamines", "s", 1, 0.1, 10, lit="D5"),
    S("ma_ec50_nM", "monoamines", "nM", 1000, 10, 100000, grain="pairing", applies_to="each transmitter-receptor pair",
      notes="MOD-1 and LGC-55 EC50 measured (param_ranges D6, D7); others guessed"),
    S("ma_gain_pA", "monoamines", "pA", 2, -20, 20, grain="gene", applies_to="each monoamine receptor gene"),
    S("glia_gain", "glia", "1", 1, 0.5, 1.5, notes="multiplies amphid sensory currents; 1 = no effect"),
    # pharynx
    S("pump_rate_food_hz", "pharynx", "Hz", 4.3, 3.5, 5, lit="G1"),
    S("pump_rate_nofood_hz", "pharynx", "Hz", 0.3, 0, 1, lit="G2"),
    S("pump_duration_ms", "pharynx", "ms", 170, 150, 200, lit="G3"),
    S("pump_food_od0", "pharynx", "OD600", 0.2, 0.01, 5),
    # defecation (times after the posterior body contraction, pBoc)
    S("dmp_period_s", "defecation", "s", 45, 42, 48, lit="H1"),
    S("dmp_pboc_dur_s", "defecation", "s", 2, 1, 3, lit="H2"),
    S("dmp_aboc_delay_s", "defecation", "s", 3, 2, 4.5),
    S("dmp_aboc_dur_s", "defecation", "s", 1, 1, 3, lit="H3"),
    S("dmp_exp_delay_s", "defecation", "s", 4, 3, 6),
    S("dmp_exp_dur_s", "defecation", "s", 0.3, 0.1, 1),
    S("dmp_pboc_amp", "defecation", "activation", 0.5, 0, 1, notes="added to the posterior 1/3 of BWM"),
    S("dmp_pboc_frac", "defecation", "body length", 0.33, 0.2, 0.5),
    # egg-laying
    S("egg_active_min", "egg_laying", "min", 2, 1, 5, lit="I1"),
    S("egg_inactive_min", "egg_laying", "min", 20, 15, 30, lit="I2"),
    S("egg_rate_active_per_min", "egg_laying", "eggs/min", 2, 0.5, 6,
      notes="in the active phase; with I1 and I2 gives the basal rate of param_ranges I3"),
    S("egg_vm_dur_ms", "egg_laying", "ms", 1000, 200, 3000, notes="vulval muscle contraction per egg"),
    # metabolism
    S("met_store_tau_h", "metabolism", "h", 24, 12, 48, lit="L1"),
    S("met_intake_per_pump", "metabolism", "store units", 1e-5, 1e-7, 1e-3),
    # observation
    S("gcamp_kd_nM", "gcamp", "nM", 157, 100, 200, lit="M1", notes="GCaMP6s"),
    S("gcamp_hill", "gcamp", "1", 2.5, 2, 3, lit="M3"),
    S("gcamp_tau_rise_ms", "gcamp", "ms", 50, 30, 80, lit="M4"),
    S("gcamp_tau_decay_ms", "gcamp", "ms", 500, 200, 2000),
    S("gcamp_dff_max", "gcamp", "dF/F", 10, 2, 50),
    S("gcamp_ca_rest_nM", "gcamp", "nM", 50, 20, 150),
    S("gcamp_noise_pct", "gcamp", "% dF/F", 3, 1, 10, lit="M8"),
    S("homeo_target_mV", "homeostasis", "mV", -30, -45, -17, lit="A4", applies_to="every neuron"),
    S("homeo_tau_s", "homeostasis", "s", 100, 10, 1000),
    S("homeo_gain_pA_per_mV", "homeostasis", "pA/mV", 0.5, 0, 5),
    S("homeo_max_pA", "homeostasis", "pA", 20, 0, 100),
    S("slow_olf_tau_h", "slow_signalling", "h", 2, 1, 4, lit="K1", applies_to="AWC"),
    S("slow_thermo_tau_h", "slow_signalling", "h", 3, 1, 6, lit="K2", applies_to="AFD (T* drift)"),
    S("slow_gain_floor", "slow_signalling", "1", 0.3, 0, 1, notes="fraction of the odour gain left after full "
      "long-term adaptation"),
    S("gap_rect_ratio", "gap_rectification", "ratio", 4, 2, 10, lit="C3", grain="class",
      applies_to="AVA, AVB, AVD, AVE, PVC to A- and B-type motor neurons",
      notes="preferred conductance / reverse conductance. The direction is measured (Liu et al. 2017: current "
      "passes from VA5 into AVA, not back); no paper gives a number for the ratio (GAP_RECT_DIRECTION.md)"),
]

# Receptor neurons and sign per stimulus channel (structure, measured: WormAtlas / the papers named in INTERFACE).
SENSORS = {
    "sens_salt": [("nacl_mM", "head", {"ASEL": 1, "ASER": -1})],
    "sens_odor_attract": [("diacetyl_uM", "head", {"AWAL": 1, "AWAR": 1}),
                          ("isoamyl_alcohol_uM", "head", {"AWCL": -1, "AWCR": -1}),
                          ("benzaldehyde_uM", "head", {"AWCL": -1, "AWCR": -1}),
                          ("butanone_uM", "head", {"AWCL": -1})],
    "sens_repellent": [("nonanone_uM", "head", {"AWBL": 1, "AWBR": 1}),
                       ("octanol_uM", "head", {"ASHL": 1, "ASHR": 1, "ADLL": 1, "ADLR": 1, "AWBL": 1, "AWBR": 1}),
                       ("glycerol_mM", "head", {"ASHL": 1, "ASHR": 1}),
                       ("copper_mM", "head", {"ASHL": 1, "ASHR": 1, "ADLL": 1, "ADLR": 1}),
                       ("quinine_mM", "head", {"ASHL": 1, "ASHR": 1}),
                       ("sds_mM", "tail", {"PHAL": 1, "PHAR": 1, "PHBL": 1, "PHBR": 1})],
    "sens_light": [("light_mW_mm2", "head", {n: 1 for n in ("ASJL", "ASJR", "ASKL", "ASKR", "ASHL", "ASHR",
                                                          "AWBL", "AWBR", "ASIL", "ASIR")})],
    "sens_food": [("food_OD", "head", {n: 1 for n in ("ADFL", "ADFR", "ASIL", "ASIR", "ASJL", "ASJR", "NSML",
                                                     "NSMR")})],
}
AMPHID = {"ASEL", "ASER", "AWAL", "AWAR", "AWBL", "AWBR", "AWCL", "AWCR", "ASHL", "ASHR", "ADLL", "ADLR", "AFDL",
          "AFDR", "ASIL", "ASIR", "ASJL", "ASJR", "ASKL", "ASKR", "ADFL", "ADFR", "ASGL", "ASGR"}
TOUCH_ANT, TOUCH_POST = ("ALML", "ALMR", "AVM"), ("PLML", "PLMR", "PVM")
HARSH = ("PVDL", "PVDR", "FLPL", "FLPR")
NOSE = ("ASHL", "ASHR", "FLPL", "FLPR", "OLQDL", "OLQDR", "OLQVL", "OLQVR", "IL1L", "IL1R", "IL1DL", "IL1DR",
        "IL1VL", "IL1VR")


def template_params() -> dict[str, float]:
    return {s.id: s.template for s in SPECS}


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


class Layers:
    """State and stepping of every lumped layer. `names` is the brain's cell list; `pos` the soma position along
    the body (0 nose, 1 tail) for neurons, NaN otherwise; `p` the parameter dict (template_params() or a draw);
    `on` the set of mechanisms switched on; `seed` for the stochastic layers (defecation phase, egg-laying times,
    GCaMP noise); the generator is rebuilt at every reset, so a reset replays the same draws."""

    def __init__(self, names, pos, bwm_pos, p, on, seed, peptide=None, monoamine=None):
        self.names, self.idx = list(names), {n: i for i, n in enumerate(names)}
        self.pos, self.bwm_pos, self.p, self.on, self.seed = np.asarray(pos), np.asarray(bwm_pos), p, set(on), seed
        self.peptide, self.monoamine = peptide, monoamine     # (release matrix, receptor matrix, ec50s) or None
        self.reset()

    def reset(self):
        n = len(self.names)
        self.rng = np.random.default_rng(self.seed)
        self.slow = {}                                   # adaptation low-pass per (mechanism, channel)
        self.act = np.zeros(len(self.bwm_pos))
        self.gc = np.zeros(n)
        self.pump_phase, self.pumps = 0.0, 0
        self.dmp_t = self.rng.uniform(0, self.p["dmp_period_s"] * 1000.0)
        self.egg_active, self.egg_t_next, self.egg_vm_t = False, 0.0, -1e9
        self.store = 1.0
        self.ih, self.sg = np.zeros(n), 1.0
        self.pep_c = None if self.peptide is None else np.zeros(self.peptide[0].shape[1])
        self.ma_c = None if self.monoamine is None else np.zeros(self.monoamine[0].shape[1])

    # --- sensory -----------------------------------------------------------------------------------------------
    def _adapt(self, key, u, tau, frac, dt):
        s = self.slow.get(key, u)
        s = s + (u - s) * min(1.0, dt / tau)
        self.slow[key] = s
        return u - frac * s

    def sensory_current(self, obs, dt) -> np.ndarray:
        """pA into each cell from every switched-on modality."""
        p, I = self.p, np.zeros(len(self.names))

        def add(cells, amp):
            for c, sgn in cells.items():
                if c in self.idx:
                    I[self.idx[c]] += sgn * amp

        if "sens_salt" in self.on:
            for ch, side, cells in SENSORS["sens_salt"]:
                u = np.log1p(obs[side].get(ch, 0.0) / p["salt_c0_mM"])
                add(cells, p["salt_gain_pA"] * self._adapt(("salt", ch), u, 1000 * p["salt_tau_adapt_s"],
                                                            p["salt_adapt_frac"], dt))
        if "sens_odor_attract" in self.on:
            g_slow = self.slow_gain(dt)
            for ch, side, cells in SENSORS["sens_odor_attract"]:
                u = np.log1p(obs[side].get(ch, 0.0) / p["odor_c0_uM"])
                g = g_slow if "AWCL" in cells else 1.0
                add(cells, g * p["odor_gain_pA"] * self._adapt(("odor", ch), u, 1000 * p["odor_tau_adapt_s"],
                                                            p["odor_adapt_frac"], dt))
        if "sens_repellent" in self.on:
            for ch, side, cells in SENSORS["sens_repellent"]:
                u = np.log1p(obs[side].get(ch, 0.0) / p["repel_c0"])
                add(cells, p["repel_gain_pA"] * self._adapt(("rep", ch), u, 1000 * p["repel_tau_adapt_s"],
                                                             p["repel_adapt_frac"], dt))
        if "sens_thermo" in self.on:
            u = obs["head"].get("temperature_C", 20.0) - p["thermo_Tstar_C"]
            add({"AFDL": 1, "AFDR": 1}, p["thermo_gain_pA_per_C"] * self._adapt(
                ("thermo",), u, 1000 * p["thermo_tau_adapt_s"], 1.0, dt))
        if "sens_o2" in self.on:
            u = obs["head"].get("o2_pct", 21.0) - p["o2_threshold_pct"]
            add({"URXL": 1, "URXR": 1, "AQR": 1, "PQR": 1}, p["o2_gain_pA_per_pct"] * max(u, 0.0))
            add({"BAGL": 1, "BAGR": 1}, p["o2_gain_pA_per_pct"] * max(-u, 0.0))
        if "sens_co2" in self.on:
            u = obs["head"].get("co2_pct", 0.04) - p["co2_threshold_pct"]
            add({"BAGL": 1, "BAGR": 1}, p["co2_gain_pA_per_pct"] * max(u, 0.0))
        if "sens_light" in self.on:
            add(SENSORS["sens_light"][0][2], p["light_gain_pA_per_mWmm2"] * obs["head"].get("light_mW_mm2", 0.0))
        if "sens_food" in self.on:
            od = obs["head"].get("food_OD", 0.0)
            add(SENSORS["sens_food"][0][2], p["food_gain_pA"] * od / (od + p["food_od0"]))
        if "glia" in self.on:
            for c in AMPHID:
                if c in self.idx:
                    I[self.idx[c]] *= p["glia_gain"]
        f = np.asarray(obs["contact_force_uN"], float)
        s = np.linspace(0, 1, len(f))
        if "sens_touch_gentle" in self.on and f.size:
            for cells, sel in ((TOUCH_ANT, s < 0.5), (TOUCH_POST, s >= 0.5)):
                u = f[sel].max() / p["touch_f0_uN"] if sel.any() else 0.0
                y = self._adapt(("touch", cells[0]), u, p["touch_tau_adapt_ms"], p["touch_adapt_frac"], dt)
                add({c: 1 for c in cells}, p["touch_gain_pA"] * y)
        if "sens_touch_harsh" in self.on:
            add({c: 1 for c in HARSH}, p["harsh_gain_pA"] * (f.max() if f.size else 0.0) / p["harsh_f0_uN"])
            add({c: 1 for c in NOSE}, p["harsh_gain_pA"] * obs["nose_force_uN"] / p["harsh_f0_uN"])
        if "sens_tap" in self.on:
            k = self.slow.get(("tap",), 0.0) * np.exp(-dt / p["tap_tau_ms"]) + obs["tap"]
            self.slow[("tap",)] = k
            add({c: 1 for c in TOUCH_ANT + TOUCH_POST}, p["tap_gain_pA"] * k)
        if "sens_proprio" in self.on:
            kap = np.asarray(obs["curvature_per_mm"], float)
            ks = np.asarray(obs["s"], float) if obs.get("s") is not None else np.linspace(0, 1, len(kap))
            for n, i in self.idx.items():
                if n[:2] in ("VB", "DB") and np.isfinite(self.pos[i]):
                    sgn = 1 if n[0] == "V" else -1   # ventral B senses ventral bending
                    sel = (ks >= self.pos[i] - p["proprio_field_frac"]) & (ks <= self.pos[i])   # anterior field
                    if sel.any():
                        I[i] += sgn * p["proprio_gain_pA_mm"] * -kap[sel].mean()
                elif n in ("SMDDL", "SMDDR", "SMDVL", "SMDVR"):
                    sgn = -1 if n[3] == "D" else 1
                    I[i] += sgn * p["proprio_gain_pA_mm"] * -kap[ks < 0.1].mean()
                elif n == "DVA":
                    I[i] += p["proprio_gain_pA_mm"] * np.abs(kap).mean()
        return I

    # --- neuromodulators: well-mixed concentration per ligand, receptor current per cell -------------------------
    def modulator_current(self, v, dt) -> np.ndarray:
        """pA per cell. self.peptide / self.monoamine = (release, receptor, (ec50, ligand_of_pair)): release is
        cells x ligands in nM/s (the ledger's per-family rate on every expressing cell), receptor is cells x pairs
        in pA (the per-receptor gain on every expressing cell), ec50 in nM per pair."""
        I = np.zeros(len(self.names))
        p = self.p
        for key, on, conc, vth, tau in (("pep", "peptides", "pep_c", "pep_release_vth_mV", "pep_clear_tau_s"),
                                        ("ma", "monoamines", "ma_c", "ma_release_vth_mV", "ma_clear_tau_s")):
            data = self.peptide if key == "pep" else self.monoamine
            if on not in self.on or data is None:
                continue
            release, receptor, (ec50, lig) = data
            c = getattr(self, conc)
            r = _sig((v - p[vth]) / 5.0) @ release * dt / 1000.0
            c = c + r - c * dt / (1000.0 * p[tau])
            setattr(self, conc, c)
            occ = c[lig] / (c[lig] + ec50)                # per pair, Hill 1
            I += receptor @ occ
        return I

    # --- plasticity ----------------------------------------------------------------------------------------------
    def homeostatic_current(self, v, dt) -> np.ndarray:
        """pA per cell, integrating (target - V) slowly, clipped to +-max. Neurons only (pos is finite)."""
        if "homeostasis" not in self.on:
            return np.zeros(len(self.names))
        p = self.p
        neur = np.isfinite(self.pos)
        self.ih = self.ih + neur * p["homeo_gain_pA_per_mV"] * (p["homeo_target_mV"] - v) * dt / (
            1000.0 * p["homeo_tau_s"])
        self.ih = np.clip(self.ih, -p["homeo_max_pA"], p["homeo_max_pA"])
        return self.ih

    def slow_gain(self, dt) -> float:
        """Multiplier on the AWC odour current: decays toward slow_gain_floor while odour is present."""
        if "slow_signalling" not in self.on:
            return 1.0
        p = self.p
        exposed = self.slow.get(("odor", "isoamyl_alcohol_uM"), 0.0) > 0 or self.slow.get(
            ("odor", "benzaldehyde_uM"), 0.0) > 0
        target = p["slow_gain_floor"] if exposed else 1.0
        self.sg += (target - self.sg) * dt / (3.6e6 * p["slow_olf_tau_h"])
        return self.sg

    # --- muscles -------------------------------------------------------------------------------------------------
    def muscle_activation(self, v_bwm, dt) -> np.ndarray:
        p = self.p
        if "muscle_ca" in self.on:
            ca = p["mca_max_uM"] * _sig((v_bwm - p["mca_vhalf_mV"]) / p["mca_k_mV"])
        else:
            ca = np.zeros_like(v_bwm)
        if "muscle_activation" in self.on:
            n, k = p["mact_hill"], p["mact_khalf_uM"]
            target = ca ** n / (ca ** n + k ** n)
            tau = np.where(target > self.act, p["mact_tau_rise_ms"], p["mact_tau_decay_ms"])
            self.act = self.act + (target - self.act) * np.minimum(1.0, dt / tau)
        else:
            self.act = np.zeros_like(v_bwm)
        return self.act

    # --- organs --------------------------------------------------------------------------------------------------
    def pharynx(self, food_od, dt):
        p = self.p
        if "pharynx" not in self.on:
            return 0.0, 0
        f = food_od / (food_od + p["pump_food_od0"])
        rate = p["pump_rate_nofood_hz"] + (p["pump_rate_food_hz"] - p["pump_rate_nofood_hz"]) * f
        self.pump_phase += rate * dt / 1000.0
        done = int(self.pump_phase)
        self.pump_phase -= done
        self.pumps += done
        x = self.pump_phase * 1000.0 / max(rate, 1e-9)       # ms since this pump began
        a = np.sin(np.pi * x / p["pump_duration_ms"]) if x < p["pump_duration_ms"] else 0.0
        return float(max(a, 0.0)), done

    def defecation(self, dt):
        """(posterior BWM boost, enteric activation [int L, int R, anal, sph], expulsions this step)."""
        p = self.p
        if "defecation" not in self.on:
            return np.zeros(len(self.bwm_pos)), np.zeros(4), 0
        t0 = self.dmp_t
        self.dmp_t = (self.dmp_t + dt) % (p["dmp_period_s"] * 1000.0)
        t = self.dmp_t / 1000.0
        boost = np.zeros(len(self.bwm_pos))
        if t < p["dmp_pboc_dur_s"]:
            boost[self.bwm_pos > 1 - p["dmp_pboc_frac"]] = p["dmp_pboc_amp"]
        a0, a1 = p["dmp_aboc_delay_s"], p["dmp_aboc_delay_s"] + p["dmp_aboc_dur_s"]
        e0, e1 = p["dmp_exp_delay_s"], p["dmp_exp_delay_s"] + p["dmp_exp_dur_s"]
        if a0 <= t < a1:
            boost[self.bwm_pos < p["dmp_pboc_frac"]] = p["dmp_pboc_amp"]
        ent = np.zeros(4)
        if e0 <= t < e1:
            ent[:] = 1.0
        n_exp = int(t0 / 1000.0 < e0 <= t)
        return boost, ent, n_exp

    def egg_laying(self, t_ms, dt):
        """(sex muscle activation level, eggs laid this step)."""
        p = self.p
        if "egg_laying" not in self.on:
            return 0.0, 0
        if t_ms >= self.egg_t_next:
            self.egg_active = not self.egg_active
            m = p["egg_active_min"] if self.egg_active else p["egg_inactive_min"]
            self.egg_t_next = t_ms + self.rng.exponential(m * 60000.0)
        laid = 0
        if self.egg_active and self.rng.random() < p["egg_rate_active_per_min"] * dt / 60000.0:
            laid, self.egg_vm_t = 1, t_ms
        a = 1.0 if t_ms - self.egg_vm_t < p["egg_vm_dur_ms"] else 0.0
        return a, laid

    def metabolism(self, pumps, dt):
        if "metabolism" in self.on:
            p = self.p
            self.store += pumps * p["met_intake_per_pump"] - self.store * dt / (p["met_store_tau_h"] * 3.6e6)

    # --- observation ---------------------------------------------------------------------------------------------
    def gcamp(self, ca_uM, dt):
        if "gcamp" not in self.on:
            return None
        p = self.p
        c = np.maximum(ca_uM * 1000.0, 0.0)                  # nM
        kd, n = p["gcamp_kd_nM"], p["gcamp_hill"]
        f = lambda x: x ** n / (x ** n + kd ** n)
        target = (f(c) - f(p["gcamp_ca_rest_nM"])) / (1 - f(p["gcamp_ca_rest_nM"])) * p["gcamp_dff_max"]
        tau = np.where(target > self.gc, p["gcamp_tau_rise_ms"], p["gcamp_tau_decay_ms"])
        self.gc = self.gc + (target - self.gc) * np.minimum(1.0, dt / tau)
        return self.gc + self.rng.normal(0, p["gcamp_noise_pct"] / 100.0, self.gc.shape)
