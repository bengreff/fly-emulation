"""Internal state (construction task 12): lumped organs and slow state variables
that couple into the nervous system. S1-S4, N20 (minimal), N25, N26.

Off in the legacy model m4 (switch `state:organs|model` = 0: no object, no drive).
With the switch at 1 the organism carries one `InternalState`, advanced every
`update_ms` of simulated time from quantities the body and world actually
provide, and returning a per-neuron tonic drive (mV) that `Organism.sense`
adds to the afferent drive.

Units: time s (the clock and sleep homeostat keep h in their parameters),
volume nL, sugar nmol glucose-equivalents (1 trehalose = 2 glucose), concentration
mM (= nmol/uL = nmol per 1000 nL), light lux, temperature degC, humidity 0-1.

State variables and equations (every coefficient is a row of PARAMS below and of
data/model/parameters.csv; all are bounded guesses unless labelled otherwise):

  S3 crop/gut      ingestion r_ing * (1 - crop/crop_max) while the labellum or
                   haustellum touches a food patch (the taste contact rule of
                   extrasenses.py); a patch is a liquid drop, the ingested volume
                   is water and carries the patch's sugar molarity.
                   crop' = ingest - crop/tau_crop          (volume and sugar alike)
                   gut'  = crop/tau_crop - gut/tau_gut     (absorbed into S1 / S4)
  S1 hemolymph     H (nmol) in hemolymph volume V_h (nL); conc = 1000 H / V_h mM
                   H' = gut_sugar/tau_gut + R_akh - S_dilp - use
                   use = basal * Q10^((T-25)/10) * (1 + k_act * activity)
                   activity in [0, 1] = tanh(mean |motor activation| / act_scale)
  S2 fat body      F' = S_dilp - R_akh;  R_akh = k_rel * akh * F / (F + K_F)
                   S_dilp = k_sto * dilp * conc / conc0
                   akh'  = (1 / (1 + exp( x/s)) - akh ) / tau_hormone
                   dilp' = (1 / (1 + exp(-x/s)) - dilp) / tau_hormone,  x = conc/conc0 - 1
  S4 water         W' = gut_water/tau_gut - evap - excrete
                   evap = e0 (1 - RH) Q10w^((T-25)/10) (1 + k_w activity)
                   excrete = max(0, W - W0) / tau_excrete
                   V_h = max(0.2 V_h0, V_h0 + f_h (W - W0));  osm = V_h0 / V_h
  N26 clock        Stuart-Landau limit cycle z = x + iy:
                   z' = (mu (1 - |z|^2) + i 2 pi / period) z + K Lsat e^{i alpha}
                   Lsat = L / (L + L50); alpha = the phase light pulls toward
                   (circadian time ct_light). ct = arg(z) / 2 pi * 24 h.
  N25 sleep        Borbely process S: P' = (1 - P)/tau_wake awake, -P/tau_sleep
                   asleep; asleep = inactive (activity < a_rest) for >= t_sleep.
                   Switch (dFB) on when P > th_hi + c_amp cos(4 pi ct / 24), off
                   when P < th_lo + c_amp cos(4 pi ct / 24) (crepuscular wake drive).

Indices read by the nervous system (N20, minimal):
  hunger  = clip(2 akh - 1, 0, 1)       satiety = clip(2 dilp - 1, 0, 1)
  thirst  = clip((osm - 1) / osm_full, 0, 1)

Couplings (per-neuron mV; populations by male-cns `type`, see COUPLED):
  ISN      g_isn * (hunger - thirst)     Jourjine et al. 2016 Cell (abstract, via
           search summary): AKH increases ISN activity, high osmolality decreases it
  IPC      g_ipc * satiety               lead (not read): IPC activity rises with
           circulating sugar; the lumped DILP level is not fed back from IPC spikes
  LB3b/c   + g_sugar_hunger * hunger * (their taste drive this step)  [gain]
  LB3a     + g_water_thirst * thirst * (their taste drive this step)  [gain]
  clock    g_clock * cos(2 pi (ct - peak) / 24), morning or evening group
  dFB      g_dfb * switch                (FB6A_a/b/c, FB6E; see COUPLED)

Validity: a lumped, single-compartment fly at rest-to-walking activity; no
circulation delays, no separate trehalose/glucose/glycogen/TAG pools, no protein,
no diuretic hormones, ingestion without a cibarial pump (B17 absent), clock
without molecular feedback loops, light without eye/CRY transduction. Every
coupling gain is guessed. None of this is fitted.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .registry import Registry, Status

SWITCH = ("state:organs", "model")

# (field, mechanism, entity, property, unit, default, lo, hi, bound_basis,
#  bound_source, prior_dist, label, note). The default is the prior centre.
# Rows of data/model/parameters.csv are generated from this list
# (param_id = mechanism prefix + field), so the two cannot drift.
PARAMS = [
    # --- S3 crop and gut ---------------------------------------------------------
    ("ingest_nl_s", "S3", "state:crop", "ingest_rate", "nL/s", 2.0, 0.2, 20.0, "guessed",
     "no rate read; a fly drinks a few hundred nL meal in minutes (lead: CAFE assays, Ja et al. 2007, not read)",
     "loguniform", "guessed", "lumped pump: rate while the labellum touches liquid food"),
    ("crop_max_nl", "S3", "state:crop", "capacity", "nL", 400.0, 100.0, 1500.0, "guessed",
     "crop stretch limits meal size; meals of a few hundred nL after starvation (lead, not read)",
     "loguniform", "guessed", "ingestion falls linearly to 0 at capacity"),
    ("tau_crop_s", "S3", "state:crop", "emptying_tau", "s", 900.0, 120.0, 7200.0, "guessed",
     "crop empties over minutes to an hour (leads, not read)", "loguniform", "guessed", ""),
    ("tau_gut_s", "S3", "state:gut", "absorption_tau", "s", 1800.0, 300.0, 14400.0, "guessed",
     "midgut transit/absorption over tens of minutes to hours (lead, not read)", "loguniform", "guessed", ""),
    # --- S1 hemolymph sugar ------------------------------------------------------
    ("conc0_mM", "S1", "state:hemolymph", "sugar_setpoint", "mM glucose-eq", 40.0, 10.0, 100.0,
     "measured_related", "adult hemolymph trehalose 5-50 mM by state (literature summary via web search, s10; "
     "not read in a primary source) = 10-100 mM glucose-equivalents", "lognormal", "inferred",
     "fed set point of the AKH/DILP loop"),
    ("vh0_nl", "S1", "state:hemolymph", "volume", "nL", 60.0, 25.0, 150.0, "measured_related",
     "about 25 nL is extractable from one adult and usually < 50 nL (hemolymph sampling methods, Anal Chem "
     "2012 via search summary); total volume larger than the extractable part", "lognormal", "guessed", ""),
    ("basal_nmol_s", "S1", "state:energy", "basal_use", "nmol/s", 0.002, 0.0005, 0.01, "guessed",
     "a store of ~100-1000 nmol glucose-eq lasting ~1-3 days of starvation implies ~0.001-0.01 nmol/s "
     "(consistency argument; resting O2 consumption not read)", "loguniform", "guessed", "at 25 degC"),
    ("k_act", "S1", "state:energy", "activity_factor", "x basal", 5.0, 1.0, 20.0, "insect_wide",
     "insect locomotion raises metabolic rate a few-fold, flight ~10x or more (general insect physiology; "
     "no Drosophila value read)", "loguniform", "guessed", "extra use at activity 1"),
    ("act_scale", "S1", "state:energy", "activity_scale", "motor activation units", 1.0, 0.01, 100.0,
     "guessed", "scale of Neuromuscular.activation that counts as full activity; unknown",
     "loguniform", "guessed", ""),
    ("q10_met", "S1", "state:energy", "q10", "dimensionless", 2.0, 1.5, 3.5, "insect_wide",
     "metabolic Q10 of ectotherms is typically 2-3", "normal", "guessed", ""),
    # --- S2 fat body / hormones ----------------------------------------------
    ("fat0_nmol", "S2", "state:fat_body", "store", "nmol glucose-eq", 300.0, 50.0, 2000.0, "guessed",
     "~5-15 ug TAG plus glycogen per adult (leads, not read) ~ 100-500 nmol glucose-eq", "loguniform", "guessed",
     "initial store"),
    ("k_rel_nmol_s", "S2", "state:fat_body", "akh_release_max", "nmol/s", 0.02, 0.002, 0.2, "guessed",
     "must exceed peak use (basal x k_act) for glycaemia to hold in activity", "loguniform", "guessed", ""),
    ("k_sto_nmol_s", "S2", "state:fat_body", "dilp_storage_max", "nmol/s", 0.01, 0.001, 0.1, "guessed",
     "storage rate at the set point with full DILP; no data", "loguniform", "guessed", ""),
    ("K_fat_nmol", "S2", "state:fat_body", "release_half_store", "nmol", 20.0, 1.0, 200.0, "guessed",
     "release fails as the store empties; no data", "loguniform", "guessed", ""),
    ("hormone_s", "S2", "state:hormone", "sensitivity", "fraction of set point", 0.1, 0.02, 0.5, "guessed",
     "AKH/DILP respond to tens of % changes in sugar; no data", "loguniform", "guessed", ""),
    ("tau_hormone_s", "N20", "state:hormone", "tau", "s", 600.0, 10.0, 7200.0, "insect_wide",
     "neuropeptide and hormone actions last seconds to hours (same basis as n20_peptide_tau)",
     "loguniform", "guessed", "AKH-like and DILP-like levels"),
    # --- S4 water ------------------------------------------------------------
    ("w0_nl", "S4", "state:water", "body_water", "nL", 600.0, 400.0, 800.0, "insect_wide",
     "insects are ~60-70% water; flybody mass 0.985 mg", "normal", "inferred", ""),
    ("evap_nl_s", "S4", "state:water", "evaporation_dry", "nL/s", 0.004, 0.001, 0.02, "guessed",
     "desiccation survival ~10-30 h (s4_water_tau basis) after losing ~100-300 nL", "loguniform", "guessed",
     "at 0 RH, 25 degC, rest"),
    ("k_w_act", "S4", "state:water", "activity_factor", "x", 1.0, 0.0, 5.0, "guessed",
     "respiratory water loss rises with activity (spiracles open); no data", "uniform", "guessed", ""),
    ("q10_evap", "S4", "state:water", "q10", "dimensionless", 2.0, 1.0, 4.0, "guessed",
     "vapour pressure deficit and cuticle permeability rise with temperature", "normal", "guessed", ""),
    ("tau_excrete_s", "S4", "state:water", "excretion_tau", "s", 3600.0, 300.0, 36000.0, "guessed",
     "Malpighian tubules remove excess water over minutes to hours (lead, not read)", "loguniform", "guessed", ""),
    ("f_h", "S4", "state:water", "hemolymph_share", "fraction", 0.5, 0.1, 1.0, "guessed",
     "share of a body-water change borne by hemolymph volume; no data", "uniform", "guessed", ""),
    ("osm_full", "S4", "state:water", "thirst_full_osm_rise", "fraction", 0.2, 0.05, 0.5, "guessed",
     "osmolality rise that saturates thirst; no data", "loguniform", "guessed", ""),
    # --- N26 clock -----------------------------------------------------------
    ("period_h", "N26", "state:clock", "period", "h", 24.0, 22.0, 26.0, "measured_this_class",
     "wild-type free-running period about 23.5-24.5 h (Konopka & Benzer 1971 lead; same as n26_clock_period)",
     "normal", "inferred", "free-running period of the lumped oscillator"),
    ("mu_per_h", "N26", "state:clock", "amplitude_rate", "1/h", 1.0, 0.1, 10.0, "guessed",
     "amplitude relaxation of the lumped limit cycle; no data", "loguniform", "guessed", ""),
    ("k_light_per_h", "N26", "state:clock", "light_coupling", "1/h", 0.2, 0.02, 2.0, "guessed",
     "flies entrain to 12:12 LD within a few days; no PRC data read", "loguniform", "guessed",
     "0.2 re-entrains a 12 h shift in ~2-3 days at 500 lux (s10 check)"),
    ("l50_lux", "N26", "state:clock", "light_half_lux", "lux", 10.0, 0.01, 1000.0, "guessed",
     "flies entrain to dim light (leads, not read)", "loguniform", "guessed", ""),
    ("ct_light_h", "N26", "state:clock", "light_target_ct", "h", 8.0, 0.0, 12.0, "guessed",
     "light pulls the phase toward subjective day: delays in the early night, advances late (sign of the "
     "classic PRC; no dead zone)", "uniform", "guessed",
     "8 h puts entrained CT 0 within ~1 h of lights-on under 12:12 LD (convention ZT0 = CT0; s10 check)"),
    # --- N25 sleep -----------------------------------------------------------
    ("tau_wake_h", "N25", "state:sleep", "rise_tau", "h", 12.0, 1.0, 48.0, "guessed",
     "sleep rebound after hours of deprivation (same basis as n25_sleep_tau)", "lognormal", "guessed", ""),
    ("tau_sleep_h", "N25", "state:sleep", "decay_tau", "h", 3.0, 0.5, 12.0, "guessed",
     "process-S decay is faster than build-up (Borbely/Daan two-process model, mammals; lead)",
     "lognormal", "guessed", ""),
    ("t_sleep_s", "N25", "state:sleep", "inactivity_criterion", "s", 300.0, 60.0, 600.0, "measured_related",
     "fly sleep = >= 5 min inactivity (Shaw et al. 2000; Hendricks et al. 2000; a behavioural convention)",
     "uniform", "inferred", ""),
    ("a_rest", "N25", "state:sleep", "rest_activity", "activity", 0.05, 0.005, 0.3, "guessed",
     "activity below which the fly counts as inactive", "loguniform", "guessed", ""),
    ("th_hi", "N25", "state:sleep", "switch_on", "pressure", 0.6, 0.3, 0.9, "guessed",
     "dFB switch-on threshold of the two-process model", "uniform", "guessed", ""),
    ("th_lo", "N25", "state:sleep", "switch_off", "pressure", 0.3, 0.05, 0.6, "guessed",
     "dFB switch-off threshold (hysteresis)", "uniform", "guessed", ""),
    ("c_amp", "N25", "state:sleep", "circadian_amplitude", "pressure", 0.1, 0.0, 0.3, "guessed",
     "circadian wake drive peaking at dawn and dusk (crepuscular activity)", "uniform", "guessed", ""),
    # --- N20 couplings (mV) ----------------------------------------------------
    ("g_isn_mv", "N20", "state:coupling", "isn_gain", "mV", 3.0, 0.0, 15.0, "guessed",
     "tonic drive at full hunger or thirst; sign from Jourjine 2016", "uniform", "guessed", ""),
    ("g_ipc_mv", "N20", "state:coupling", "ipc_gain", "mV", 3.0, 0.0, 15.0, "guessed",
     "tonic drive at full satiety", "uniform", "guessed", ""),
    ("g_sugar_hunger", "N20", "state:coupling", "sugar_grn_hunger_gain", "x", 1.0, 0.0, 3.0, "guessed",
     "starvation raises sugar GRN sensitivity (lead: Inagaki et al. 2012, not read); relative gain at full hunger",
     "uniform", "guessed", ""),
    ("g_water_thirst", "N20", "state:coupling", "water_grn_thirst_gain", "x", 1.0, 0.0, 3.0, "guessed",
     "relative water-GRN gain at full thirst; no data", "uniform", "guessed", ""),
    ("g_clock_mv", "N26", "state:coupling", "clock_gain", "mV", 3.0, 0.0, 15.0, "guessed",
     "day-night firing modulation of clock neurons (leads: Cao & Nitabach 2008; Flourakis et al. 2015; not read)",
     "uniform", "guessed", "amplitude of the cosine drive"),
    ("peak_morning_h", "N26", "state:coupling", "morning_peak_ct", "h", 2.0, 0.0, 6.0, "guessed",
     "LNv/DN1p fire most around dawn (leads as above)", "uniform", "guessed", ""),
    ("peak_evening_h", "N26", "state:coupling", "evening_peak_ct", "h", 10.0, 8.0, 14.0, "guessed",
     "LNd/5th s-LNv are evening oscillator cells (lead: Grima 2004; Stoleru 2004; not read)",
     "uniform", "guessed", ""),
    ("g_dfb_mv", "N25", "state:coupling", "dfb_gain", "mV", 5.0, 0.0, 20.0, "guessed",
     "dFB neurons switch between electrically active and silent states with sleep need "
     "(lead: Donlea et al. 2014, not read)", "uniform", "guessed", ""),
]

MECH_PREFIX = {"S1": "s1", "S2": "s2", "S3": "s3", "S4": "s4", "N20": "n20", "N25": "n25", "N26": "n26"}

# Populations coupled (male-cns `type`), evidence and label of the mapping.
COUPLED = {
    "isn": (["ISN"], "inferred",
            "interoceptive SEZ neurons (Jourjine et al. 2016 Cell): AKHR and Nanchung; name match "
            "to the male-cns type 'ISN' (inferred)"),
    "ipc": (["IPC"], "inferred",
            "insulin-producing cells of the pars intercerebralis; male-cns type 'IPC' (name match)"),
    "sugar_grn": (["LB3b", "LB3c"], "inferred",
                  "labellar sugar GRNs by receptor-line projection matching (extrasenses.LABELLAR_MODALITY)"),
    "water_grn": (["LB3a"], "inferred", "labellar water GRNs (as above)"),
    "clock_morning": (["s-LNv", "l-LNv", "DN1pA", "DN1pB"], "guessed",
                      "morning-active clock cells; phase assignment per type is a guess from leads"),
    "clock_evening": (["LNd_b", "LNd_c", "5thsLNv_LNd6"], "guessed",
                      "evening oscillator cells (LNd, 5th s-LNv); phase assignment guessed"),
    "dfb": (["FB6A_a", "FB6A_b", "FB6A_c", "FB6E"], "inferred",
            "sleep-promoting dFB cells: 'we ... tentatively equate these cells with FB6A and FB6E' "
            "(hemibrain types; A half-centre oscillator encodes sleep pressure, bioRxiv "
            "10.1101/2024.02.23.581780, read s10); hemibrain FB6A taken as male-cns FB6A_a/b/c "
            "(name split, guessed). 23E10-GAL4 labels 23-30 dFB neurons (PMC12135941), so this is a subset"),
}
# Identified in the literature but not coupled here (recorded, not guessed into the model).
NOT_COUPLED = {
    "AKH-producing cells": "corpora cardiaca, outside the CNS volume: represented only by the lumped akh level",
    "fat body": "not neural: lumped store F",
    "DH44, Hugin-RG, LK, CAPA, CRZ, AstA": "present as types; their state dependence is not coded (task 12 keeps the list short)",
    "DN1a, LPN_a/b, LN-DN2": "clock cells with unassigned firing phase: not driven",
    "remaining dFB (FB6*/FB7*) 23E10 cells": "type correspondence unknown: not driven",
}


@dataclass
class Organs:
    """The pure ODE system (no organism): S1-S4, N25, N26 and the hormone levels."""
    p: dict
    t_s: float = 0.0
    crop_nl: float = 0.0
    crop_sugar: float = 0.0
    gut_nl: float = 0.0
    gut_sugar: float = 0.0
    fat: float = field(default=np.nan)
    water_nl: float = field(default=np.nan)
    sugar: float = field(default=np.nan)          # hemolymph nmol glucose-eq
    akh: float = 0.5
    dilp: float = 0.5
    z: complex = 1.0 + 0.0j                       # clock state; arg 0 = CT 0
    pressure: float = 0.2
    inactive_s: float = 0.0
    asleep: bool = False
    switch: bool = False

    def __post_init__(self):
        p = self.p
        if np.isnan(self.fat):
            self.fat = p["fat0_nmol"]
        if np.isnan(self.water_nl):
            self.water_nl = p["w0_nl"]
        if np.isnan(self.sugar):
            self.sugar = p["conc0_mM"] * p["vh0_nl"] / 1000.0

    # --- derived quantities ----------------------------------------------------
    @property
    def vh_nl(self) -> float:
        p = self.p
        return max(0.2 * p["vh0_nl"], p["vh0_nl"] + p["f_h"] * (self.water_nl - p["w0_nl"]))

    @property
    def sugar_mM(self) -> float:
        return 1000.0 * self.sugar / self.vh_nl

    @property
    def osm(self) -> float:
        return self.p["vh0_nl"] / self.vh_nl

    @property
    def hunger(self) -> float:
        return float(np.clip(2 * self.akh - 1, 0, 1))

    @property
    def satiety(self) -> float:
        return float(np.clip(2 * self.dilp - 1, 0, 1))

    @property
    def thirst(self) -> float:
        return float(np.clip((self.osm - 1) / self.p["osm_full"], 0, 1))

    @property
    def ct_h(self) -> float:
        return float((np.angle(self.z) % (2 * np.pi)) / (2 * np.pi) * 24.0)

    # --- one step --------------------------------------------------------------
    MAX_SUB_S = 20.0    # hemolymph sugar turns over in minutes: explicit sub-steps stay below this

    def step(self, dt_s: float, **inputs) -> None:
        n = max(1, int(np.ceil(float(dt_s) / self.MAX_SUB_S)))
        for _ in range(n):
            self._step(float(dt_s) / n, **inputs)

    def _step(self, dt: float, *, activity: float = 0.0, food_sugar_M: float = 0.0,
              touching_food: bool = False, light_lux: float = 0.0, pump: float = 1.0,
              temperature_c: float = 25.0, humidity_rh: float = 0.5) -> None:
        p = self.p
        act = float(np.clip(activity, 0, 1))
        # S3 ingestion and crop/gut transit (exact exponential transfer per step)
        # B17 (s10): the cibarial pump's activity (0-1) scales ingestion; 1 = ungated (s10 agent default)
        ing = (p["ingest_nl_s"] * pump * max(0.0, 1 - self.crop_nl / p["crop_max_nl"]) * dt
               if touching_food else 0.0)
        self.crop_nl += ing
        self.crop_sugar += ing * food_sugar_M          # M x nL = nmol
        fc = 1 - np.exp(-dt / p["tau_crop_s"])
        fg = 1 - np.exp(-dt / p["tau_gut_s"])
        mv_nl, mv_s = self.crop_nl * fc, self.crop_sugar * fc
        self.crop_nl -= mv_nl
        self.crop_sugar -= mv_s
        ab_nl, ab_s = self.gut_nl * fg, self.gut_sugar * fg
        self.gut_nl += mv_nl - ab_nl
        self.gut_sugar += mv_s - ab_s
        # S1/S2 energy
        use = p["basal_nmol_s"] * p["q10_met"] ** ((temperature_c - 25) / 10) * (1 + p["k_act"] * act)
        x = self.sugar_mM / p["conc0_mM"] - 1
        s = p["hormone_s"]
        fh = 1 - np.exp(-dt / p["tau_hormone_s"])
        self.akh += (1 / (1 + np.exp(np.clip(x / s, -50, 50))) - self.akh) * fh
        self.dilp += (1 / (1 + np.exp(np.clip(-x / s, -50, 50))) - self.dilp) * fh
        rel = p["k_rel_nmol_s"] * self.akh * self.fat / (self.fat + p["K_fat_nmol"])
        sto = p["k_sto_nmol_s"] * self.dilp * self.sugar_mM / p["conc0_mM"]
        rel = min(rel * dt, self.fat)
        sto = min(sto * dt, self.sugar + ab_s + rel)            # cannot store more than is there
        dH = ab_s + rel - sto - use * dt
        self.sugar = max(0.0, self.sugar + dH)
        self.fat = max(0.0, self.fat - rel + sto)
        # S4 water
        evap = p["evap_nl_s"] * (1 - humidity_rh) * p["q10_evap"] ** ((temperature_c - 25) / 10) \
            * (1 + p["k_w_act"] * act)
        exc = max(0.0, self.water_nl - p["w0_nl"]) * (1 - np.exp(-dt / p["tau_excrete_s"]))
        self.water_nl = max(0.0, self.water_nl + ab_nl - evap * dt - exc)
        # N26 clock: exact rotation, Euler amplitude and forcing (dt << 1 h)
        dth = dt / 3600.0
        w = 2 * np.pi / p["period_h"]
        L = light_lux / (light_lux + p["l50_lux"]) if light_lux > 0 else 0.0
        alpha = 2 * np.pi * p["ct_light_h"] / 24.0
        z = self.z * np.exp(1j * w * dth)
        z = z + dth * (p["mu_per_h"] * (1 - abs(z) ** 2) * z + p["k_light_per_h"] * L * np.exp(1j * alpha))
        self.z = complex(z)
        # N25 sleep homeostat
        self.inactive_s = self.inactive_s + dt if act < p["a_rest"] else 0.0
        self.asleep = self.inactive_s >= p["t_sleep_s"]
        tau = (p["tau_sleep_h"] if self.asleep else p["tau_wake_h"]) * 3600.0
        target = 0.0 if self.asleep else 1.0
        self.pressure = target + (self.pressure - target) * np.exp(-dt / tau)
        c = p["c_amp"] * np.cos(4 * np.pi * self.ct_h / 24.0)
        if self.pressure > p["th_hi"] + c:
            self.switch = True
        elif self.pressure < p["th_lo"] + c:
            self.switch = False
        self.t_s += dt


def default_params() -> dict:
    return {r[0]: float(r[5]) for r in PARAMS}


def read_params(reg: Registry) -> dict:
    out = {}
    for f, mech, ent, prop, unit, val, lo, hi, *_rest in PARAMS:
        out[f] = float(reg.require(
            ent, prop, units=unit, model_use=f"{mech} internal state ({f})",
            subsystem="internal_state", minimal=val,
            minimal_note=f"bounded [{lo}, {hi}] in data/model/parameters.csv "
                         f"({MECH_PREFIX[mech]}_{f}); read only with state:organs|model = 1"))
    return out


class InternalState:
    """Organs + couplings, stepped from the organism every `update_ms`."""

    def __init__(self, p: dict, n_neurons: int, rows: dict, update_ms: float = 10.0):
        self.p = p
        self.organs = Organs(p)
        self.n = n_neurons
        self.rows = {k: np.asarray(v, dtype=np.int64) for k, v in rows.items()}
        self.update_ms = update_ms
        self._acc_ms = 0.0
        self._tonic = np.zeros(n_neurons, dtype=np.float32)
        self.pump_cells = None            # B17: set by build() when pump gating is on
        self.pump_rate = 0.0
        self._refresh()

    def _refresh(self) -> None:
        o, p, r = self.organs, self.p, self.rows
        t = np.zeros(self.n, dtype=np.float32)
        t[r["isn"]] += p["g_isn_mv"] * (o.hunger - o.thirst)
        t[r["ipc"]] += p["g_ipc_mv"] * o.satiety
        ct = o.ct_h
        t[r["clock_morning"]] += p["g_clock_mv"] * np.cos(2 * np.pi * (ct - p["peak_morning_h"]) / 24)
        t[r["clock_evening"]] += p["g_clock_mv"] * np.cos(2 * np.pi * (ct - p["peak_evening_h"]) / 24)
        t[r["dfb"]] += p["g_dfb_mv"] * float(o.switch)
        self._tonic = t

    def tonic(self) -> np.ndarray:
        return self._tonic

    def taste_extra(self, base: np.ndarray | None) -> np.ndarray:
        """State-dependent gain on the GRN drive already computed this step."""
        out = np.zeros(self.n, dtype=np.float32)
        if base is None:
            return out
        o, p = self.organs, self.p
        s, w = self.rows["sugar_grn"], self.rows["water_grn"]
        out[s] = p["g_sugar_hunger"] * o.hunger * base[s]
        out[w] = p["g_water_thirst"] * o.thirst * base[w]
        return out

    def advance(self, dt_s: float, **inputs) -> None:
        self.organs.step(dt_s, **inputs)
        self._refresh()

    def drive(self, org, dt_ms: float, base: np.ndarray | None = None) -> np.ndarray:
        """Per-neuron mV for this organism step. Advances the organs every
        update_ms from what the body and world provide (motor activation of the
        previous step, labellum contact with food, world light/temperature/RH)."""
        self._acc_ms += dt_ms
        if self.pump_cells is not None:   # B17: pump MN rate (Hz per cell), ~100 ms estimate
            sp = getattr(org, "_last_spiked", None)
            n = int(np.isin(self.pump_cells, sp).sum()) if sp is not None and len(sp) else 0
            a = np.exp(-dt_ms / 100.0)
            self.pump_rate = self.pump_rate * a + n / max(len(self.pump_cells), 1) * 10.0
        if self._acc_ms >= self.update_ms - 1e-9:
            dt_s, self._acc_ms = self._acc_ms / 1000.0, 0.0
            act = float(np.tanh(np.abs(np.asarray(org.nm.activation)).mean() / self.p["act_scale"]))
            touching, sugar = labellum_food(org)
            pump = (1.0 if self.pump_cells is None
                    else float(np.clip(self.pump_rate / self.pump_full_hz, 0.0, 1.0)))
            self.advance(dt_s, activity=act, touching_food=touching, food_sugar_M=sugar, pump=pump,
                         light_lux=float(getattr(org.world, "light_lux", 0.0)),
                         temperature_c=org.world.temperature_c, humidity_rh=org.world.humidity_rh)
        return self._tonic + self.taste_extra(base)


def labellum_food(org) -> tuple[bool, float]:
    """The extrasenses taste contact rule: a labrum (or the haustellum) in
    contact, over a food patch. Returns (touching liquid food, sugar M)."""
    if not org.world.food:
        return False, 0.0
    ex = org.extra
    m, d = org.body.sim.mj_model, org.body.sim.mj_data
    hc = ex._head_contact(m, d)
    best = (False, 0.0)
    for s in "lr":
        if not (hc[f"{s}_labrum"] > 0 or hc["c_haustellum"] > 0):
            continue
        p = d.xpos[ex.body_ids[f"{s}_labrum"]]
        for fp in org.world.food:
            if np.linalg.norm(p[:2] - np.asarray(fp.center)[:2]) <= fp.radius_mm:
                best = (True, max(best[1], float(fp.tastants.get("sugar", 0.0))))
    return best


def population_rows(conn) -> tuple[dict, dict]:
    types = conn.neurons.type.fillna("").to_numpy()
    rows, counts = {}, {}
    for k, (tys, _label, _why) in COUPLED.items():
        idx = np.flatnonzero(np.isin(types, tys))
        rows[k] = idx
        counts[k] = {t: int((types == t).sum()) for t in tys}
    return rows, counts


def build(reg: Registry, conn) -> InternalState | None:
    """The switch, and (only when on) the parameters and population records."""
    on = int(reg.require(
        *SWITCH, units="enum",
        model_use="0 no internal state (legacy m4); 1 lumped organs, clock and sleep homeostat with "
                  "tonic drive to identified populations (internal_state.py, task 12)",
        subsystem="internal_state", minimal=0,
        minimal_note="legacy m4; internal state is a template option"))
    if not on:
        return None
    p = read_params(reg)
    rows, counts = population_rows(conn)
    # model rows are conn.neurons order (Connectome.index_of uses the same order)
    for k, (tys, label, why) in COUPLED.items():
        n = int(len(rows[k]))
        reg.provide(f"state:population_{k}", "types", ";".join(tys), units="male-cns types",
                    model_use="neurons receiving internal-state drive",
                    status=Status.INFERRED if label == "inferred" else Status.GUESSED,
                    subsystem="internal_state", instances=n,
                    evidence=f"{why}; counts {counts[k]}",
                    uncertainty="mapping from literature names to male-cns types by name")
    reg.provide("state:population_absent", "list", ";".join(NOT_COUPLED), units="populations",
                model_use="identified populations not coupled", status=Status.ABSENT,
                subsystem="internal_state", instances=len(NOT_COUPLED),
                evidence="; ".join(f"{k}: {v}" for k, v in NOT_COUPLED.items()))
    st = InternalState(p, conn.n, rows)
    # B17 (s10): ingestion gated by the cibarial pump MNs (MN11D/MN12D innervate the
    # cibarial dilator muscles; Manzo et al. 2012 PNAS, lead, not read)
    if int(reg.require("state:crop", "pump_gated", units="enum",
                       model_use="0 ingestion on contact alone; 1 scaled by cibarial pump MN activity",
                       subsystem="internal_state", minimal=0, minimal_note="ungated")):
        types = conn.neurons.type.fillna("").to_numpy()
        st.pump_cells = np.flatnonzero(np.isin(types, ["MN11D", "MN11V", "MN12D"]))
        st.pump_full_hz = float(reg.require(
            "state:crop", "pump_full_rate_hz", units="Hz", model_use="pump MN rate for full ingestion",
            subsystem="internal_state", minimal=10.0,
            minimal_note="guessed: cibarial pumping ~6-8 Hz (lead), one spike burst per cycle"))
    # N26 start phase (s12): the clock's CT at t = 0. 0 is the convention of m4-m9r. The male-cns
    # specimen was raised in 12:12 LD and "dissected 1.5 hours after lights-on" (Nern et al. 2024
    # bioRxiv Methods, read), so 1.5 starts the clock where the wiring was fixed (entrained, ZT = CT).
    ct0 = float(reg.require(
        "state:clock", "initial_ct", units="h", model_use="circadian time of the clock at t = 0",
        subsystem="internal_state", minimal=0.0,
        minimal_note="convention: CT 0 at t = 0 (m4-m9r)"))
    if ct0:
        st.organs.z = complex(np.exp(1j * 2 * np.pi * ct0 / 24.0))
        st._refresh()
    return st
