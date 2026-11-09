# Inbox 01:45 (weki): the organ conductances integrated implicitly (wbody2, 9 Nov 2026 01:52)

Class A (numerical, a code fault: the published channels are conductances; holding g (E - V_start) as a fixed current
over the 4-4.5 ms exchange step is explicit Euler in V and alternates above about 1.2 nS on HSN, weki 01:13-01:28).
Nothing built yet. Written on 9e84fa1 (main 3d620b9 merged).

## What runs now

Three terms in my modules put g (E - V) on a cell as a current computed from V at the step's start:
- egg_laying, LGC-55 on HSNL/R: `egg_lgc55_g_nS * occ * (erev - V)` into I_pA (the brain's soma IClamp).
- egg_laying, the vm cation term on the 8 vm muscles: `g * (egg_cation_erev_mV - V)` on each muscle's own IClamp,
  g = stretch + 5-HT + NLP-3 conductances (ranges 0.1-2, 0.1-3, 0-2 nS; up to 7 nS).
- intestine, PBO-5/6 on the posterior body-wall muscles: `pbo5_g_nS * p_open * (pbo5_erev_mV - V)` into I_pA (range
  0.1-10 nS; weki: these cells alternate at 12.2-13.8 nS, above the range).
The constant currents (egg_ret_gain_pA x activation on HSN, the nested `direct` AEX-2 gain) are not conductances and
stay as they are.

## The fix

Each term becomes a `wgc` point process (nmodl/wgc.mod, already in the brain's build: i = g (v - e), NEURON solves it
implicitly at its 0.5 ms step; neuromod, drugs and k2p_leak use it) whose g is set each exchange step; the module
injects no current for it. Toggles, implicit the default (a fix), the old code nested:
- `egg_g_solver` implicit | explicit (organs_egglaying: both terms)
- `pboc_g_solver` implicit | explicit (organs_intestine: PBO-5)
The g each step and its timing (set before the step's fadvance) are unchanged; only how V enters the current changes.
Validity: the conductance is held over the exchange step (as every wgc in the brain is); its own gating (occupancy,
p_open) still updates once per exchange step.

## Bars (into the check script's docstring before running)

Setup: Brain of HSNL and HSNR (egg terms; the 16 sex muscles are built by the module) or of the posterior body-wall
muscles dBWML22 and vBWMR22 (PBO-5), default toggles except quantal_noise and channel_noise off (the check is of the
numerics, not the noise). Each term's g is driven directly: occupancy, stretch or p_open forced to 1, the other
conductances of the term at 0, g on at 1.0 s for 300 exchange steps of 4.5 ms (1.35 s). Recorded: the target cells'
V per exchange step.

1. Neutral: `explicit` reproduces the pre-fix code (9e84fa1's src) exactly on every recorded trace of bars 2-3.
2. Small g (each term at the bottom of its range, 0.1 nS, and at 0.5 nS): with dV = V(g) - V(0) at the same exchange
   step, the implicit form at 4.5 ms is at least as close to the reference (explicit at a 0.5 ms exchange step, the
   old code at NEURON's own step) as the explicit form at 4.5 ms: RMS(dV_impl - dV_ref) <= 1.1 x RMS(dV_expl -
   dV_ref) + 0.05 mV over the pulse (1.1 and 0.05 mV guessed).
3. Stability (the request's step test): each term at the top of its range and at 2x (LGC-55 5 and 10 nS; vm cation
   7 and 14 nS; PBO-5 10 and 20 nS): under implicit, every target cell's V is finite and its alternation
   (fit/vitals.alternation, ALT_MV 2 mV) stays under ALT_STEPS (25). Explicit at the same g reported (expected to fail
   on HSN at 5 nS).
Reported, not barred: at the top g, RMS(dV_impl - dV_ref).

Then the tests (forms, defaults, a stability test), the vitals battery on the new default, and the MECHANISMS_AUDIT
rows (15 egg-laying, 14 intestine) through wbrain2.

Expected (guessed): 1 and 3 pass by construction of NEURON's implicit step; 2 passes because explicit's onset lag
(about half an exchange step) is what implicit removes.
