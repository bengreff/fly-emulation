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
                   s20, switch state:clock|light_input = 1 (neutral 0 keeps the line above):
                   light acts through CRY-dependent TIM degradation instead of K Lsat:
                   c' = a L (1 - c) - c / tau_c          (active CRY fraction; a per lux per h)
                   T' = (P(ct) - T) / tau_rec - k_d c T  (TIM, units of its DD peak)
                   P = TIM_DD (1 + tau_rec dlnTIM_DD/dct), so T = TIM_DD in DD
                   z gets k_tim (k_d c T) e^{i alpha_tim} (phase pushed by the TIM light removes)
                   Night-gated (T is low in the subjective day) and saturating in pulse length
                   (T is used up), unlike the one-point pull (F-S20-1).
                   Start-up c and T: 2 days of 12:12 LD at REAR_LUX ending at ZT = the start CT (a fly
                   kept in LD, like the male-cns specimen; inferred), so a run started in the light
                   does not begin by clearing night-level TIM.
  N25 sleep        Borbely process S: P' = (1 - P)/tau_wake awake, -P/tau_sleep
                   asleep; asleep = inactive (activity < a_rest) for >= t_sleep.
                   Switch (dFB) on when P > th_hi + c_amp cos(4 pi ct / 24), off
                   when P < th_lo + c_amp cos(4 pi ct / 24) (crepuscular wake drive).
                   state:sleep|values_from_sources = 1 (s20, neutral 0): Abhilash & Shafer 2024's
                   fly fit (SLEEP_SOURCED) with their one-cycle form c_amp cos(2 pi ct / 24).
                   state:sleep|homeostat = 1 (s21, neutral 0; docs/research/s21_n25_homeostat_scope.md):
                   P is the ER5 (R5) need n, BRP-like (Liu 2016): n' = (1 - n)/need_tau_rise awake,
                   -n/need_tau_decay asleep. No thresholds: each dFB cell is a two-state unit,
                   OFF -> ON at k_r (1 + need_gain n) / (1 + need_gain) (k_r the spontaneous restart
                   measured in flies deprived > 12 h, Pimentel 2016, taken at full need n = 1),
                   ON -> OFF at k_off (1 + light_arousal Lsat + night_arousal D(CT)) (arousal; D the
                   clock's DN1 drive, s23, neutral 0), stepped exactly with a
                   seeded generator. switch = ON fraction >= DFB_SLEEP_FRACTION (the reduced loop's
                   sleep link); the organism drives each dFB cell by its own state.

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
    # s20 CRY-TIM light input, read only with state:clock|light_input = 1 (values: s20 reads and fit, DECISIONS)
    ("cry_rate_per_lux_h", "N26", "state:clock", "cry_activation_rate", "1/(lux h)", 10.26, 1e-3, 1e3, "guessed",
     "CRY photoactivation per photon flux; set by rule in the s20 fit (DECISIONS 22 Oct 23:02, 23:55): the model's "
     "10 min IRC half-max at CT20 is Vinayak 2013's 600 nW/cm2 blue = 0.372 lux (lux conversion at 470 nm "
     "inferred), solved jointly with tim_kdeg_per_h", "loguniform", "inferred",
     "read only with state:clock|light_input = 1"),
    ("cry_tau_h", "N26", "state:clock", "cry_active_lifetime", "h", 0.5, 0.02, 6.0, "guessed",
     "how long light-activated CRY keeps degrading TIM after the light ends; no in vivo measurement found "
     "(s20 reads rounds 1-2)", "loguniform", "guessed", "read only with state:clock|light_input = 1"),
    ("tim_kdeg_per_h", "N26", "state:clock", "tim_light_degradation_rate", "1/h", 13.85, 0.1, 50.0, "guessed",
     "TIM loss rate under active CRY; set by rule in the s20 fit so a saturating 10 min pulse at CT15 leaves "
     "10% (inferred) of unpulsed TIM 1 h later (Tang et al. 2010 Neuron 66:378: DN/LNd TIM 'undetectable' "
     "after that pulse); half-life 3 min under full CRY", "loguniform", "inferred",
     "read only with state:clock|light_input = 1"),
    ("tim_tau_rec_h", "N26", "state:clock", "tim_recovery_tau", "h", 0.86, 0.25, 12.0, "guessed",
     "TIM dark turnover time; upper bound from the steepest DD decline of TIM_DD (CT1-2, ln(0.51/0.16) = "
     "1.16/h; Shafer et al. 2002 Fig. 6D), taken at the bound", "loguniform", "derived",
     "read only with state:clock|light_input = 1"),
    ("k_tim", "N26", "state:clock", "tim_light_coupling", "per unit peak TIM removed", 1.0, 0.01, 100.0, "guessed",
     "phase displacement per unit of TIM removed by light; fitted to the PRC in s20", "loguniform", "guessed",
     "read only with state:clock|light_input = 1"),
    ("ct_tim_h", "N26", "state:clock", "tim_kick_ct", "h", 6.5, 0.0, 24.0, "guessed",
     "the circadian time TIM removal pushes the phase towards; fitted to the PRC in s20", "uniform", "guessed",
     "read only with state:clock|light_input = 1 (mode 0 keeps ct_light_h)"),
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
    # s21 homeostat mode 1 (read only with state:sleep|homeostat = 1; DECISIONS 23 Oct, s21 registration)
    ("need_tau_rise_h", "N25", "state:sleep", "need_rise_tau", "h", 12.0, 1.0, 48.0, "guessed",
     "ER5 need rise while awake; no direct anchor (Liu 2016 gives no time constant); fitted in s21",
     "loguniform", "guessed", "read only with state:sleep|homeostat = 1"),
    ("need_tau_decay_h", "N25", "state:sleep", "need_decay_tau", "h", 5.5, 2.9, 10.4, "measured_this_class",
     "Liu et al. 2016 Cell 165:1347 Fig. 4: BRP in R2 cells (R69F08; ER5 inferred) still raised 2 h into recovery sleep, back at baseline "
     "after 24 h (bracket: >= 50 % of the excess left at 2 h, <= 10 % at 24 h)", "loguniform", "derived",
     "read only with state:sleep|homeostat = 1"),
    ("dfb_restart_per_min", "N25", "state:sleep", "dfb_restart_rate", "1/min", 0.0387, 0.0106, 0.094,
     "measured_this_class",
     "Pimentel et al. 2016 Nature 536:333: in flies sleep-deprived > 12 h, dFB cells switched OFF by dopamine "
     "restarted spiking after 7-60 min, mean 25.86 +- 7.61 (SEM) min, 7 of 15 cells (the other 8 recordings "
     "ended first; their length not stated). Centre 1/25.86; upper 1/(mean - 2 SEM); lower the censored "
     "exponential estimate if the 8 were held 60 min (7 / (7 x 25.86 + 8 x 60))", "loguniform", "derived",
     "read only with state:sleep|homeostat = 1; the rate at full need n = 1 (inferred: > 12 h of deprivation)"),
    ("need_gain", "N25", "state:sleep", "need_restart_gain", "x", 1.0, 0.0, 100.0, "guessed",
     "dFB restart rate at full ER5 need relative to zero need, minus 1 (ER5 -> ExR3 -> dFB, 5-HT; scope s21); "
     "fitted in s21",
     "uniform", "guessed", "read only with state:sleep|homeostat = 1"),
    ("dfb_koff_per_min", "N25", "state:sleep", "dfb_arousal_off_rate", "1/min", 0.04, 0.001, 0.9, "guessed",
     "dFB ON -> OFF rate in the dark; upper bound the dopamine switch-off (time constant about 1.1 min, "
     "Pimentel 2016); fitted in s21", "loguniform", "guessed", "read only with state:sleep|homeostat = 1"),
    ("light_arousal", "N25", "state:sleep", "light_arousal_gain", "x", 1.0, 0.0, 20.0, "guessed",
     "relative rise of the dFB OFF rate in saturating light (light-driven arousal; leads Shang et al. 2008, "
     "Sheeba et al. 2008, not read); fitted in s21", "uniform", "guessed",
     "read only with state:sleep|homeostat = 1"),
    ("night_arousal", "N25", "state:sleep", "night_arousal_gain", "x", 0.0, 0.0, 20.0, "guessed",
     "relative rise of the dFB OFF rate at the peak of the clock's DN1 drive (late-night wake from DH31+ DN1, "
     "Kunst et al. 2014 Curr Biol 24:2652, abstract only: sign and window, no magnitude); fitted in s23",
     "uniform", "guessed", "read only with state:sleep|homeostat = 1; neutral 0"),
    ("ct_dn1_h", "N25", "state:sleep", "night_arousal_peak_ct", "h", 19.0, 17.0, 20.0, "measured_related",
     "Liang, Holy & Taghert 2016 Science 351:976 Fig. 1G: DN1 Ca2+ peak about CT 18.8-19, per-fly scatter "
     "CT 17-20, DD1 (figure read, docs/research/s20_n26_figreads.md)", "uniform", "inferred",
     "the Ca2+ peak taken as the peak of the wake drive (Liang: Ca2+ leads behaviour by about 4 h, not applied); "
     "read only with night_arousal > 0"),
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

# s19: values read from sources (DECISIONS 22 Oct 02:30), the defaults only with
# state:organs|values_from_sources = 1 (neutral 0 keeps the guessed PARAMS centres above).
# field: (value, lo, hi, label, bound_basis, source)
SOURCED_SWITCH = ("state:organs", "values_from_sources")
SOURCED = {
    "basal_nmol_s": (0.00626, 0.00574, 0.0146, "derived", "measured_this_class",
                     "Burggren, Souder & Ho 2017 Biol Open 6:471 (PMC5399560): grouped fed Oregon R males, 25 degC, "
                     "~6 ul O2/mg wet/h x 0.505 mg; 6 O2 per glucose, 22.4 ul/umol (STPD not stated: -8% at "
                     "24.45); upper bound the single-fly extrapolation 14 ul/mg/h"),
    "fat0_nmol": (672.0, 320.0, 1170.0, "derived", "measured_related",
                  "~50 ug TAG per male (PMC8774106 bar graph; Dahomey 10 d, 20-21 degC) x 37.7 kJ/g / 2803 kJ/mol "
                  "glucose; bounds 24-87 ug across reports; glycogen not included (no male value found)"),
    "vh0_nl": (24.0, 10.0, 60.0, "inferred", "measured_related",
               "24 +- 2 nL extractable from males (attributed to AJP-Regu 2015; secondary, not read)"),
    "w0_nl": (344.0, 300.0, 780.0, "derived", "measured_this_class",
              "Burggren 2017: male wet mass 0.505 minus dry mass 0.161 mg"),
    "tau_crop_s": (11250.0, 11250.0, 25700.0, "derived", "measured_related",
                   "crop turnover 32%/h of capacity fully fed, 14%/h dietary restriction (PMC4335172; Geer 1970 model)"),
    "tau_gut_s": (2700.0, 900.0, 7200.0, "inferred", "measured_related",
                  "faecal dye from 15 min, abundant by 45-60 min (PMC4335172); whole-tract transit < 1 h (secondary)"),
    # s23 (DECISIONS 23 Oct 23:20)
    "ingest_nl_s": (5.0, 4.4, 8.8, "derived", "measured_related",
                    "Itskov et al. 2014 Nat Commun 5:4560 (w1118 males and females, 25 degC): median sip 1.05 nL per "
                    "sip cycle of 0.13 s sip + 0.08 s inter-sip interval (yeast) = 5.0 nL/s; 4.4 with the 0.16 s "
                    "sucrose sip; upper 8.8 from Pool et al. 2014 Neuron 83:164 (~150 nL in ~17 s, 24 h deprived "
                    "females, 30 degC). s23 amendment (DECISIONS 24 Oct): the 23:20 value 7.0 omitted the interval"),
    "crop_max_nl": (250.0, 150.0, 320.0, "inferred", "measured_related",
                    "largest single meals after deprivation, females (no male value found): Pool et al. 2014 Neuron "
                    "83:164 ~150 nL after 24 h (30 degC); Qi et al. 2015 Mol Brain 8:13 0.27 +- 0.02 ul (100 mM "
                    "sucrose) and 0.32 +- 0.01 ul mean after 36 h (virgin Canton-S, 25 degC). Edgecomb et al. 1994, "
                    "cited at 23:20, scores crop size on an ordinal 1-5 scale, not in nL"),
    "q10_met": (2.0, 2.0, 2.3, "measured", "measured_this_class",
                "Klepsatel, Wildridge & Galikova 2019 Sci Rep 9:5239 (PMC6437209): whole-fly O2 consumption, adult "
                "males, 13-33 degC, Q10 2.0 Oregon R (the basal-rate strain) and 2.3 Canton S"),
}

# s19: N26 clock values read from sources (DECISIONS 22 Oct 04:44), the defaults only with
# state:clock|values_from_sources = 1 (neutral 0 keeps the s10 guesses). Same tuple layout as SOURCED.
CLOCK_SOURCED_SWITCH = ("state:clock", "values_from_sources")
CLOCK_SOURCED: dict = {}

# s20: N25 values and threshold form from Abhilash & Shafer 2024 Sleep 47:zsad277 (PMC11275470;
# docs/research/s20_n25_reads.md round 2), the defaults only with state:sleep|values_from_sources = 1, which
# also switches the threshold modulation to one cycle per day (their omega = 2 pi / tau, phi = 0 at CT 0).
# Their taus are a grid fit (no errors) to % sleep / 24 h of CS, w1118 and yw males in LD; the thresholds are
# fixed from Daan et al. 1984 (human model), so only the taus carry fly data. Same tuple layout as SOURCED.
SLEEP_SOURCED_SWITCH = ("state:sleep", "values_from_sources")
_AS24 = "Abhilash & Shafer 2024 Sleep 47:zsad277, Methods"
SLEEP_SOURCED = {
    "tau_wake_h": (8.76, 1.0, 48.0, "inferred", "guessed",
                   "Abhilash & Shafer 2024 Fig. 2B and text: build-up t_i fitted to % sleep / 24 h, LD, males "
                   "(no errors given); bounds the s10 guesses"),
    "tau_sleep_h": (9.51, 0.5, 12.0, "inferred", "guessed",
                    "Abhilash & Shafer 2024 Fig. 2B and text: decay t_delta, same fit; bounds the s10 guesses"),
    "th_hi": (0.35, 0.3, 0.9, "guessed", "guessed", f"{_AS24}: upper threshold mean M_u, fixed from Daan 1984"),
    "th_lo": (0.15, 0.05, 0.6, "guessed", "guessed", f"{_AS24}: lower threshold mean M_l, fixed from Daan 1984"),
    "c_amp": (0.10, 0.0, 0.3, "guessed", "guessed", f"{_AS24}: threshold amplitude A_u = A_l, fixed from Daan 1984"),
}

# s21: N25 homeostat mode (0 process S with the threshold switch; 1 ER5 need and stochastic dFB cells)
HOMEOSTAT_SWITCH = ("state:sleep", "homeostat")
# Reduced-loop sleep link: the dFB population drives sleep while at least half its cells are ON (guessed,
# structural; the dFB-to-inactivity path through the brain is not modelled in the reduced loop).
DFB_SLEEP_FRACTION = 0.5
N_DFB = 8           # male-cns v1.0: FB6A_a/b/c and FB6E, 2 cells each (COUPLED["dfb"])

# s20: N26 light input mode (0 the one-point pull, 1 CRY-TIM; see the module docstring)
LIGHT_INPUT_SWITCH = ("state:clock", "light_input")
# TIM's dark (DD) profile relative to its peak, at circadian times (h); used only with light_input = 1.
# Shafer, Rosbash & Truman 2002 J Neurosci 22:5946 Fig. 6D: small vLNs (s-LNv), Canton-S, DD day 1, 25 C,
# 4 brains per point; cytoplasmic + nuclear mean pixel intensity, read by eye from a 3x crop (axis 0-200,
# about +-3 units), summed and divided by the CT16 maximum (159.5). The s-LNv profile stands in for the
# light-labile TIM of the whole clock network (validity limit: Tang 2010 finds DN/LNd, not s-LNv, TIM
# degraded by an early-night pulse).
TIM_DD = ((0.0, 0.77), (1.0, 0.51), (2.0, 0.16), (3.0, 0.065), (4.0, 0.029), (6.0, 0.015), (8.0, 0.015),
          (10.0, 0.015), (12.0, 0.15), (14.0, 0.30), (16.0, 1.0), (18.0, 0.51), (20.0, 0.26), (22.0, 0.98))
TIM_DD_LABEL = "measured (pixel read)"


def _tim_seg(ct: float, prof=None) -> tuple[float, float]:
    """Log-linear periodic interpolation of TIM_DD: (TIM, d ln TIM / d ct)."""
    x, y = zip(*(prof or TIM_DD))
    xs, ly = np.array(list(x) + [x[0] + 24.0]), np.log(list(y) + [y[0]])
    c = ct % 24.0
    i = min(int(np.searchsorted(xs, c, side="right")) - 1, len(xs) - 2)
    s = (ly[i + 1] - ly[i]) / (xs[i + 1] - xs[i])
    return float(np.exp(ly[i] + s * (c - xs[i]))), float(s)


def tim_dd(ct: float, prof=None) -> float:
    """TIM_DD at ct (log-linear between the read points)."""
    return _tim_seg(ct, prof)[0]


def tim_target(ct: float, tau_rec_h: float, prof=None) -> float:
    """P(ct) = TIM_DD (1 + tau_rec dlnTIM_DD/dct), floored at 0: with it, T follows TIM_DD in the dark."""
    t, s = _tim_seg(ct, prof)
    return max(0.0, t * (1.0 + tau_rec_h * s))


def cry_tim_step(c: float, tim: float, ct: float, light_lux: float, dth: float,
                 p: dict) -> tuple[float, float, float]:
    """One step of active CRY c and TIM T (exact exponentials for constant light): (c, T, TIM removed)."""
    a, b = p["cry_rate_per_lux_h"] * max(light_lux, 0.0), 1.0 / p["cry_tau_h"]
    ci = a / (a + b)
    c1 = ci + (c - ci) * np.exp(-(a + b) * dth)
    kd = p["tim_kdeg_per_h"] * 0.5 * (c + c1)
    r = 1.0 / p["tim_tau_rec_h"] + kd
    ti = tim_target(ct, p["tim_tau_rec_h"], p.get("tim_dd")) / (p["tim_tau_rec_h"] * r)
    t1 = ti + (tim - ti) * np.exp(-r * dth)
    return float(c1), float(t1), kd * 0.5 * (tim + t1) * dth


REAR_LUX = 1000.0   # rearing light for the start-up state (guessed; the s20 fit's LD intensity)


def entrained_cry_tim(ct0: float, p: dict, days: float = 2.0, lux: float = REAR_LUX,
                      dt_h: float = 1.0 / 60.0) -> tuple[float, float]:
    """(c, T) at ZT = ct0 after `days` of 12:12 LD, lights on ZT 0-12 (CT = ZT, as initial_ct). Phase kicks
    are left out of the pre-run; c and T forget their own start within hours (tau_c, tau_rec < 1 h)."""
    n = int(round(days * 24.0 / dt_h))
    ct = (ct0 - n * dt_h) % 24.0
    c, t = 0.0, tim_dd(ct, p.get("tim_dd"))
    for _ in range(n):
        c, t, _r = cry_tim_step(c, t, ct, lux if ct % 24.0 < 12.0 else 0.0, dt_h, p)
        ct = (ct + dt_h) % 24.0
    return c, t

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
    cry: float = 0.0                              # active CRY fraction (light_input = 1)
    tim: float = field(default=np.nan)            # TIM, units of its DD peak (light_input = 1)
    pressure: float = 0.2                         # process S; the ER5 need n with homeostat = 1
    inactive_s: float = 0.0
    asleep: bool = False
    switch: bool = False
    n_dfb: int = N_DFB                            # homeostat = 1: one two-state unit per dFB cell
    seed: int = 0
    dfb_on: np.ndarray = field(default=None)

    def __post_init__(self):
        p = self.p
        if self.dfb_on is None:
            self.dfb_on = np.zeros(self.n_dfb, dtype=bool)
        self._rng = np.random.default_rng(self.seed)
        if np.isnan(self.fat):
            self.fat = p["fat0_nmol"]
        if np.isnan(self.water_nl):
            self.water_nl = p["w0_nl"]
        if np.isnan(self.sugar):
            self.sugar = p["conc0_mM"] * p["vh0_nl"] / 1000.0
        if np.isnan(self.tim):
            if p.get("light_input", 0.0) >= 1:
                self.cry, self.tim = entrained_cry_tim(self.ct_h, p)
            else:
                self.tim = tim_dd(self.ct_h, p.get("tim_dd"))

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
        if p.get("light_input", 0.0) >= 1:          # s20 CRY-TIM (exact exponential steps for c and T)
            self.cry, self.tim, removed = cry_tim_step(self.cry, self.tim, self.ct_h, light_lux, dth, p)
            z = z + dth * p["mu_per_h"] * (1 - abs(z) ** 2) * z \
                + p["k_tim"] * removed * np.exp(1j * 2 * np.pi * p["ct_tim_h"] / 24.0)
        else:
            z = z + dth * (p["mu_per_h"] * (1 - abs(z) ** 2) * z + p["k_light_per_h"] * L * np.exp(1j * alpha))
        self.z = complex(z)
        # N25 sleep homeostat
        self.inactive_s = self.inactive_s + dt if act < p["a_rest"] else 0.0
        self.asleep = self.inactive_s >= p["t_sleep_s"]
        if p.get("homeostat", 0.0) >= 1:            # s21 mode 1: ER5 need and stochastic dFB cells
            self._homeostat_step(dt, L)
            self.t_s += dt
            return
        tau = (p["tau_sleep_h"] if self.asleep else p["tau_wake_h"]) * 3600.0
        target = 0.0 if self.asleep else 1.0
        self.pressure = target + (self.pressure - target) * np.exp(-dt / tau)
        cyc = 1.0 if p.get("sleep_sourced", 0.0) >= 1 else 2.0      # cycles per day of the threshold drive
        c = p["c_amp"] * np.cos(2 * np.pi * cyc * self.ct_h / 24.0)
        if self.pressure > p["th_hi"] + c:
            self.switch = True
        elif self.pressure < p["th_lo"] + c:
            self.switch = False
        self.t_s += dt

    def _homeostat_step(self, dt: float, lsat: float) -> None:
        """Mode 1: exact relaxation of the need, exact two-state transition probabilities per dFB cell."""
        p = self.p
        tau = (p["need_tau_decay_h"] if self.asleep else p["need_tau_rise_h"]) * 3600.0
        target = 0.0 if self.asleep else 1.0
        self.pressure = target + (self.pressure - target) * np.exp(-dt / tau)
        k_on, k_off = dfb_rates(p, self.pressure, lsat, self.ct_h)
        p_stay_on, p_turn_on = dfb_transition(k_on, k_off, dt)
        u = self._rng.random(self.n_dfb)
        self.dfb_on = np.where(self.dfb_on, u < p_stay_on, u < p_turn_on)
        self.switch = bool(self.dfb_on.mean() >= DFB_SLEEP_FRACTION)


def night_drive(ct, peak_ct: float):
    """The clock's DN1 drive, one cycle: 1 at peak_ct, 0 twelve hours away (s23)."""
    return 0.5 * (1.0 + np.cos(2 * np.pi * (ct - peak_ct) / 24.0))


def dfb_rates(p: dict, need, lsat, ct=None):
    """Homeostat mode 1 rates per s: OFF -> ON k_r (1 + g n) / (1 + g), ON -> OFF
    k_off (1 + light_arousal Lsat + night_arousal D(ct)), D the DN1 drive (night_drive; s23, neutral 0)."""
    g = p["need_gain"]
    k_on = p["dfb_restart_per_min"] / 60.0 * (1.0 + g * need) / (1.0 + g)
    a = 1.0 + p["light_arousal"] * lsat
    na = p.get("night_arousal", 0.0)
    if ct is not None and np.any(na):
        a = a + na * night_drive(ct, p["ct_dn1_h"])
    k_off = p["dfb_koff_per_min"] / 60.0 * a
    return k_on, k_off


def dfb_transition(k_on, k_off, dt: float):
    """Exact two-state Markov step over dt: (P(ON at t+dt | ON), P(ON at t+dt | OFF))."""
    r = k_on + k_off
    pinf, e = k_on / r, np.exp(-r * dt)
    return pinf + (1.0 - pinf) * e, pinf * (1.0 - e)


def default_params(sourced: bool = False, clock_sourced: bool = False, sleep_sourced: bool = False,
                   homeostat: bool = False) -> dict:
    p = {r[0]: float(r[5]) for r in PARAMS}
    if homeostat:
        p["homeostat"] = 1.0
    if sourced:
        p.update({f: v[0] for f, v in SOURCED.items()})
    if clock_sourced:
        p.update({f: v[0] for f, v in CLOCK_SOURCED.items()})
    if sleep_sourced:
        p.update({f: v[0] for f, v in SLEEP_SOURCED.items()}, sleep_sourced=1.0)
    return p


def read_params(reg: Registry) -> dict:
    src = bool(reg.require(*SOURCED_SWITCH, units="boolean",
                           model_use="S1-S4: values read from sources (internal_state.SOURCED, s19) as defaults",
                           subsystem="internal_state", minimal=0.0, conventional=0.0,
                           minimal_note="neutral 0: the s10 guessed prior centres"))
    clk = bool(reg.require(*CLOCK_SOURCED_SWITCH, units="boolean",
                           model_use="N26: clock light input and cell peaks read from sources "
                                     "(internal_state.CLOCK_SOURCED, s19) as defaults",
                           subsystem="internal_state", minimal=0.0, conventional=0.0,
                           minimal_note="neutral 0: the s10 guessed clock values"))
    li = float(reg.require(*LIGHT_INPUT_SWITCH, units="mode",
                           model_use="N26 light input: 0 one-point pull K Lsat e^{i alpha}; 1 CRY-dependent TIM "
                                     "degradation (night-gated, saturating; s20)",
                           subsystem="internal_state", minimal=0.0, conventional=0.0,
                           minimal_note="neutral 0: the s10 one-point pull"))
    slp = bool(reg.require(*SLEEP_SOURCED_SWITCH, units="boolean",
                           model_use="N25: Abhilash & Shafer 2024 fly two-process values and one-cycle threshold "
                                     "form (internal_state.SLEEP_SOURCED, s20) as defaults",
                           subsystem="internal_state", minimal=0.0, conventional=0.0,
                           minimal_note="neutral 0: the s10 guessed sleep values and 12 h threshold harmonic"))
    hom = float(reg.require(*HOMEOSTAT_SWITCH, units="mode",
                            model_use="N25 homeostat: 0 process S with the hysteretic dFB switch; 1 ER5 need "
                                      "(Liu 2016) and stochastic per-cell dFB switching (Pimentel 2016; s21)",
                            subsystem="internal_state", minimal=0.0, conventional=0.0,
                            minimal_note="neutral 0: the s10 process S and threshold switch"))
    out = {"light_input": li} if li else {}
    if slp:
        out["sleep_sourced"] = 1.0
    if hom:
        out["homeostat"] = hom
    for f, mech, ent, prop, unit, val, lo, hi, *_rest in PARAMS:
        if src and f in SOURCED:
            val, lo, hi = SOURCED[f][:3]
        if clk and f in CLOCK_SOURCED:
            val, lo, hi = CLOCK_SOURCED[f][:3]
        if slp and f in SLEEP_SOURCED:
            val, lo, hi = SLEEP_SOURCED[f][:3]
        out[f] = float(reg.require(
            ent, prop, units=unit, model_use=f"{mech} internal state ({f})",
            subsystem="internal_state", minimal=val,
            minimal_note=f"bounded [{lo}, {hi}] in data/model/parameters.csv "
                         f"({MECH_PREFIX[mech]}_{f}); read only with state:organs|model = 1"))
    return out


class InternalState:
    """Organs + couplings, stepped from the organism every `update_ms`."""

    def __init__(self, p: dict, n_neurons: int, rows: dict, update_ms: float = 10.0, seed: int = 0):
        self.p = p
        self.n = n_neurons
        self.rows = {k: np.asarray(v, dtype=np.int64) for k, v in rows.items()}
        self.organs = Organs(p, n_dfb=max(1, len(self.rows.get("dfb", ()))), seed=seed)
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
        if p.get("homeostat", 0.0) >= 1 and len(r["dfb"]) == len(o.dfb_on):
            t[r["dfb"]] += p["g_dfb_mv"] * o.dfb_on.astype(np.float32)      # each dFB cell by its own state
        else:
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


def build(reg: Registry, conn, seed: int = 0) -> InternalState | None:
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
    st = InternalState(p, conn.n, rows, seed=seed)
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
