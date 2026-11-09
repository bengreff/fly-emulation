# HSN port spec (wbody2 item 9, DEBUG_TRIAGE line 5; 8 Nov 2026)

Spec only: nothing here is built. The overnight egg probe (wtriage, backhouse PID 82978) decides B vs D first;
the port starts only if it says B, or after every earlier item. Sources: `lit_hsn.md` (Sonnet search, 8 Nov), the
numbers marked (spot-checked) re-opened by wbody2.

## What the model has now (measured, 8 Nov 22:40, Mac, HSNL alone at the ledger, 5 s at zero input)

- HSNL: 2 sections, 706.8 um2; 25 mechanisms: pas (e -75 mV, g 5e-5 S/cm2), cca1, egl19, unc2, nca (Na leak,
  0.00015 S/cm2), kcnl, irk, shl1, kqt3, kvs1, egl36, exp2, unc103, slo1 and slo2 (iso, egl19- and unc2-coupled),
  egl2 and shk1 at 0, cainternm. No Cl conductance, no TMC channel.
- Rest -54.4 mV (mean of the last 1 s); one start-up excursion to -1.5 mV, then silent.
- In the 8-cell row 15 brain: -53.6 mV, 0.65 % of the time above -30 mV (wtriage).

## Published HSN quantities (the check set; none of these is a model parameter)

| quantity | value | source | status |
|---|---|---|---|
| rest, wild type (whole-cell, 0 pA, 145 mM KCl pipette) | -21.8 mV (second control group -21.1) | Ravi et al. 2021 Genetics, PMC8864752, Fig. 5B | opened, spot-checked |
| rest, HSN::PTX (Go off in HSN) | -14.75 mV | same | spot-checked |
| rest, goa-1(n1134) | -17.9 mV | same | spot-checked |
| rest, egl-10(md176) (excess Go) | -40.8 mV | same | spot-checked |
| the authors' caveat | "The high Cl- content of the intracellular solution used may contribute to the relatively depolarized membrane potentials we observed" | same, Methods | spot-checked |
| Na leak sets the rest; tmc-1 loss hyperpolarises HSN, HSN-specific TMC-1 rescues | numbers in figure art only | Yue et al. 2018 Neuron, PMC7038793, Fig. 5D-F | opened by the agent, not re-checked |
| Ca transient rate, wild type | ~0.4 /min; HSN::PTX ~1.9 /min | Ravi 2021 Fig. 3C | opened by the agent |
| inter-transient interval | inactive ~34 s median; active bursts < 20 s | Ravi et al. 2018 J Neurosci, PMC6041790, Fig. 2D | opened by the agent |
| active / inactive pattern | as row 15's bar (Collins et al. 2016 eLife; Zhang, Schafer & Breitling 2010) | check only, never a source | |
| input resistance, capacitance, I-V | none published (searched) | | gap |

## CeNGEN in HSN (Taylor et al. 2021; cengen.org threshold CSVs, opened by the agent)

Expressed at threshold 2-4: egl-19, unc-2, nca-2 (+ unc-79, unc-80), kcnl-1, kcnl-2, slo-1, slo-2, shl-1, irk-1,
irk-2, irk-3, egl-6, lgc-55, egl-30, goa-1, egl-10. Threshold 2-3 only: cca-1, kcnl-4, unc-103. Zero: egl-2, shk-1
(the model has both at 0: consistent). nca-1 is not in the CeNGEN matrix. Not yet looked up: egl-36, kqt-3, kvs-1,
exp-2 (all carried by the model's HSN), tmc-1 and the Cl channels (to do before building).

## Port plan (what would be built, and whose file)

1. Like-for-like first (no new mechanism): the published rest is a high-Cl pipette number. The model's HSN has
   no Cl conductance, so its rest cannot move with the pipette Cl; the check must either add the cell's Cl leak at
   E_Cl ~ 0 mV (145 mM pipette Cl) or compare against the egl-10 to PTX ordering (-40.8 < -21.8 < -14.75: Go
   hyperpolarises), not the absolute -21.8 mV. Bar to write before running: the ordering, and rest within the
   measured span -40.8 to -14.75 mV under the pipette condition.
2. B, the missing Na leak: TMC-1 (Yue 2018) as HSN's background Na leak. A port needs a published TMC-1 leak
   conductance or I-V; Yue's numbers are figure-only. Without them it is a guessed density bounded by the rest
   it must produce, which is a fit to one number: not allowed by itself. Ask: does a TMC-1 current density exist
   in any opened paper (Yue 2018 supplement; Gao? Tang? 2020 TMC papers)? Until then: spec only.
3. B, the Go and Gq inputs that set the two states: GOA-1 (inhibitory, hyperpolarises; Ravi 2021), EGL-6 from
   FLP-10/FLP-17 (Ringstad & Horvitz 2008; EC50 in figure art only), NLP-7 via EGL-47 (Banerjee 2017), tyramine via
   LGC-55 (Pirri 2009: EC50 12.1 uM in oocytes, heterologous). The egg-laying module (mine) already releases uv1
   tyramine onto HSN LGC-55; the Go/Gq cascade inside HSN is neuromod's / receptors' (wbrain2).
4. Channel densities: the model's HSN set is BAAIWorm's generic assignment (expression_map keeps it). A CeNGEN-
   consistent HSN set would use the brain's own channel models (wbrain2's channels.py), densities shared by class,
   inside their registered ranges. Not a per-cell knob.

Owners: HSN's membrane and receptors are wbrain2's (channels, receptors, neuromod, brain). Mine: the egg-laying
module's inputs to HSN (uv1 tyramine, vulval feedback, egg_ret_gain_pA) and the check. So steps 1-4 are Requests
to wbrain2 unless the Director moves HSN's membrane to me.

## Line 22 (5-HT at the vulva, D)

wbrain2's 8 Nov night file (as of 22:10) has no entry on 5-HT reuptake (MOD-5) or line 22, so there is nothing to
read yet. The D stays as wtriage left it: a pass is an upper bound because the row 15 brain has no MOD-5 cells.
