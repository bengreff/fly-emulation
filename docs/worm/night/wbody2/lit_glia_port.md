Lookup date: 2026-11-09

Paper: Sibille J, Dao Duc K, Holcman D, Rouach N (2015) "The neuroglial potassium cycle during
neurotransmission: role of Kir4.1 channels." PLoS Comput Biol 11(3): e1004137.

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC4380507/
Full text opened: YES. Downloaded the raw PMC article HTML directly with curl (not the WebFetch tool,
whose first pass through a summarizing model produced a paraphrase with some invented detail — the
equations below are read straight out of the article's own MathML markup, cross-checked against the
plain-text rendering of the same HTML). No separate S1 Text with extra methods was found; the
"Supporting Information" section only lists S1 and S2 Figures (figures only, no extra equations). All
numbered equations (1-30) and Table 1 are in the main-text Materials and Methods.

---

## 1. How neuronal K+ efflux into the extracellular space is computed, and the full d[K+]o/dt equation

The neuron is a single-compartment Hodgkin-Huxley (HH) neuron with Na+, K+ and leak currents. The
voltage-gated K+ current is HH-style:

Quote: "I N a = g N a m 3 h ( V N − V r e s t + V N a N )" (equation 7)
Quote: "I K = g K n 4 ( V N − V r e s t + V K N )" (equation 8)

So the neuronal K+ current that feeds the extracellular pool is the HH gated current I_K = gK n^4
(VN - Vrest + VKN), NOT a passive leak. The neuron also has a separate leak current:

Quote: "I l N = g l N ( V N − V l N )" (equation 20) — "which stabilizes the membrane potential at its
resting value."

The leak current (I_lN) is not itself one of the terms added into d[K+]o/dt — only the gated K+
current I_K (converted to an ionic flux i_K) appears in the K+ balance equations. (The leak current's
role is to set the neuron's resting Vm in the HH system; it is a mixed/generic leak in the voltage
equation, not carried as a separate K+-flux term in equation 25.)

Currents are converted to ionic fluxes via mass-action / Faraday-type scaling. Quote (Balance of ionic
fluxes section): "A current I across a membrane induces a flow of charge i equals to δQ = I per unit
of time. The corresponding change in extracellular concentration is given by I/(qN_A Vol_0), where q =
1.6 * 10^-19 C is the charge of an electron, N_A the Avogadro number and Vol_N, Vol_A and Vol_0 are the
neuronal, astrocytic and extracellular volume respectively. To model the ionic concentration dynamics,
we converted the currents I_Na, I_K and I_Kir to the corresponding ionic fluxes i_Na, i_K and i_Kir."

So the "Faraday factor" used in this paper is not the Faraday constant F directly for the flux
conversion (F appears elsewhere, in the Nernst equations, see Q3/Q4 below) — the flux conversion uses
elementary charge q and Avogadro's number N_A (i.e. q·N_A = F in effect) together with the relevant
compartment volume.

The full extracellular K+ balance, from the "Potassium fluxes" section:

Quote: "To determine the system of equations for the K+ fluxes, we use the mass conservation law for
the extracellular K0, the neuronal KN and the astrocytic KA K+ concentrations. The extracellular K+ K0
increases with the neuronal current IK (see equation 8), which is here converted to iK (ion flux), but
it is also uptaken back into neurons with a flux 2ipumpN (the factor 2 is described in [67]) and into
astrocytes as the sum of the two fluxes 2ipumpA plus iKir. Similarly, we obtain the equations for the
neuronal and astrocytic K+ to balance the various fluxes. Finally, we get"

Equation 25 (exact, transcribed from the article's MathML):

  d K0 / dt = iK − 2·ipumpN − 2·ipumpA + iKir        (25)

Equation 26 (neuronal K+, for completeness, same section):

  d KN / dt = ( − iK + 2·ipumpN ) · (Vol0 / VolN)     (26)

Equation 27 (astrocytic K+, for completeness):

  d KA / dt = ( − iKir + 2·ipumpA ) · (Vol0 / VolA)   (27)

So the four terms in d[K+]o/dt are exactly: (a) neuronal HH gated K+ current flux iK (source, +), (b)
neuronal Na/K pump flux 2·ipumpN (sink, taking K+ back into the neuron), (c) astrocytic Na/K pump flux
2·ipumpA (sink, taking K+ into the astrocyte), (d) astrocytic Kir4.1 flux iKir (can be source or sink
depending on sign, see Q4). There is no separate neuronal leak-K+ term and no explicit diffusion/bath
exchange term in equation 25 as printed — diffusion to a "bath" is not modelled; the only three
compartments are neuron, astrocyte and a single well-mixed extracellular compartment. (A constant K+
leak flux is added only in the Kir4.1-knockout condition, into equation 27 for the astrocyte — see Q2.)
Volumes Vol0/VolN and Vol0/VolA appear only in the neuronal and astrocytic concentration equations (26,
27), not in equation 25 itself (which is already per unit extracellular volume since K0 is the
extracellular concentration).

---

## 2. How rest is balanced — pump strength, leak, or initial [K+]o

The paper does not present an explicit algebraic "resting reference" subtraction term in the pump
equation; balance at rest is obtained numerically, by setting leak parameters (and the two pump imax
constants) so the full system sits at a stable fixed point at prescribed resting concentrations and
voltages. Quote (Numerical implementations section):

Quote: "The leak currents parameters were adjusted to stabilize the model at the resting membrane
potentials (-70 mV and -80 mV for neurons and astrocytes respectively) and resting concentrations
(neuronal [K+] and [Na+]: 135 mM and 12 mM, respectively; extracellular [K+] and [Na+]: 2.5 mM and 116
mM, respectively; astrocytic [K+] and [Na+]: 135 mM and 12 mM, respectively). The parameters for the
Hodgkin Huxley equations were also adjusted to these concentrations."

So the mechanism is: the leak conductances/potentials (glN, VlN for the neuron; glA, VlA for the
astrocyte — see Table 1) are hand-tuned so that, given the pump equation's built-in dependence on [K+]o
and [Na+]i (equation 24, which naturally produces more pump current as K0 rises or Na_k rises — see Q3
caveat), the whole system is at equilibrium at the stated resting concentrations. This is a fitted
leak, not a literal "zero-flux at rest" closed-form constraint written into the pump formula itself —
no separate algebraic resting-subtraction term is used in equation 24 or 25.

There IS one explicit exception where a resting-balance term is added directly into the flux equation:
in the Kir4.1-knockout condition, the astrocytic Kir4.1 current and the astrocytic leak are both set to
zero, and a constant replacement K+ flux is added directly into equation 27 to hold [K+]o at its
resting value. Quote: "we added in equation 27 a constant K+ flux to maintain [K+]o at an equilibrium
value of 2.5 mM." This constant flux is explicitly described as a stand-in for other, unmodelled
constitutive K+-permeable pathways (TASK-1, Cx43 hemichannels), not as evidence that the normal model
needs such a term — in the control (Kir4.1-intact) model, balance comes purely from the leak-tuning
described above plus the pump's K0/Na dependence.

---

## 3. Pump form(s): neuronal and astrocytic Na/K-ATPase

Quote (Na/K pump ionic flux section): "The K+ resting concentrations in neurons and astrocytes are
maintained by Na/K pumps that balance the outward K+ and inward Na+ fluxes. The associated pump
currents ipump,k (index k = N for the neuron, k = A for the astrocyte) depend on the extracellular K+
K0 and intracellular Na+ concentrations (NaN for the neuron and NaA for the astrocyte) and follow the
same equation as [66],"

Equation 24, transcribed exactly from the article's MathML (confirmed by inspecting the raw <math>
markup, not just the flattened text):

  ipump,k = imaxk · (1 + 7.3/K0)^-2 · (1 + 10·Na_k)^-3     for k = N, A     (24)

Important: I checked the underlying MathML directly. The K0 term is a true fraction (7.3 divided by
K0, rendered with an <mfrac> tag: numerator 7.3, denominator K0). The Na_k term is NOT rendered as a
fraction in the article's markup — it is literally "10 multiplied by Na_k", i.e. (1 + 10·Na_k)^-3, with
no <mfrac> around the 10 and Na_k. This is asymmetric with the K0 term and with the standard
Michaelis-Menten pump form this equation is attributed to (ref [66], typically (1+Km/[Na]i)^-3 so that
pump current increases with rising intracellular Na+). As printed in the PMC HTML, equation 24's Na+
term would make the pump current fall as intracellular Na+ rises, which is the opposite of the
expected biology and of the equation's own description ("balance the outward K+ and inward Na+
fluxes"). I flag this as a likely typesetting artifact in the article (the slash/fraction bar may have
been dropped for the Na+ term during PLOS's math rendering), not a deliberate modelling choice — it
should not be ported as literally "10·Na_k" without re-deriving from the cited source [66] first.

The "7.3" and "10" are not labelled Km_K and Km_Na in the text or Table 1; the paper does not give them
separate symbolic names in Table 1 — they appear only inline in equation 24. The only pump parameters
listed by name in Table 1 are the two prefactors:

Quote (Table 1): "i_maxA — Astrocytic Na/K pump rate — 0.3 mM.ms^-1"
Quote (Table 1): "i_maxN — Neuronal Na/K pump rate — 0.9 μM.ms^-1"

Text note: "where imaxk is a constant (table 1)." No stated units or measured/fitted label are given
beyond what's in Table 1 itself (see Q5 for the provenance column as printed, which for both imax
entries is blank — no citation given).

---

## 4. Kir4.1 current form and parameters

Quote (Modeling astrocytic potassium uptake by Kir4.1 channels section): "To account for the K+
dynamics in astrocytes, we modeled the Kir4.1 channel according to its biophysical properties [59] and
I-V curve [60]. The total astroglial current IKir depends on the membrane potential, the extracellular
(K0) and the astrocytic (KA) K+ concentrations, and is approximated by"

Equation 22, transcribed exactly from the article's MathML (verified: the K0 term is inside a square
root, <msqrt>, in the numerator of a fraction whose denominator is 1 + exp(...)):

  IKir = GKir · (VA − VKA − VA1) · [ sqrt(K0) / (1 + exp( (VA − VKA − VA2) / VA3 )) ]     (22)

Quote (immediately after eq. 22): "where VKA is the Nernst astrocyte K+ potential, VA, the astrocyte
membrane potential, K0 is the extracellular K+ concentration and VA1 (an equilibrium parameter, which
sets Kir current to 0 at -80 mV), VA2 and VA3 are constant parameters calibrated by the I-V curve (Fig.
1C, [60]), as detailed below. The second term of equation 22 describes the dependence of IKir to the
square root of K0 [60-64] and to the steady state open/close partition function of Kir4.1 channels
according to the Boltzmann distribution [59], which includes dynamic variations of potassium Nernst
potential during neuronal activity."

VKA (the astrocytic K+ Nernst potential) is computed the same way as the neuronal K+ Nernst potential
(equation 19 gives the pattern for the neuron; the astrocyte analog uses KA and K0 the same way):

  Equation 19 (neuronal, given explicitly): VKN = (RT/F) · ln(K0/KN)      (19)
  (R, T, F as in Table 1 — see Q5; VKA for the astrocyte follows the identical Nernst form with KA in
  place of KN, per the "Nernst astrocyte K+ potential" label given in the text just quoted above.)

Astrocyte membrane potential equation (for context, since IKir feeds it):

  Equation 23: CA · dVA/dt = − (IKir + IlA)     (23)
  with IlA = glA·(VA − VlA), "which stabilizes the astrocyte membrane potential at -80 mV."

Fitting of VA1, VA2, VA3 — quote: "We fitted the Kir4.1 channel I-V curve (equation 22) using the
experimental recordings for the Kir4.1 channel (3 mM [K+]) (Fig. 4 in [60, 65]). We first obtained that
VA1 = (VrestA − 26 ln(3/145)) = −14.83 mV where VrestA = −80 mV (potential for which the current is
zero). We then used the Matlab fitting procedure for a single exponential with formula 22 changed to
(V − VA1 − 26 ln(3/145))^3 I with (V from -100 to 20 mV) to get that VA2 = 34 mV and VA3 = 19.23 mV
(table 1). Varying [K+]o by 0.5 mM did not affect significantly the Kir4.1 channel I-V curve, confirming
its robustness."

Parameters (also in Table 1, see Q5): GKir = 60 pS; VA1 = -14.83 mV (extracted from [60]); VA2 = 34 mV
(extracted from [60]); VA3 = 19.23 mV (extracted from [60]).

Note on the leak vs Kir comparison (Discussion): "Because the astroglial leak conductance (equation 23)
is six times smaller than the Kir4.1 channel conductance, we neglected it" when deriving the
analytical astroglial time constant — this is a simplification used only for the analytical estimate
tau_A ≈ CA/GKir ≈ 0.6 s, not a statement that the leak term is dropped from the full numerical model.

---

## 5. Full parameter table (Table 1), transcribed as printed

Values and the "Notes"/provenance exactly as given in the HTML table (this journal's Table 1 has no
separate "measured/taken from/fitted" column — provenance is given only as inline citation numbers or
"fitted" / "extracted from" wording where present; where no citation or wording is given, the table
simply states a bare value with no provenance marker, transcribed here as "(no citation given)"):

- tau_rec — Recovery time constant — 300 ms (WT) / 500 ms (fitted KO) [55]
- tau_inac — Inactivation time constant — 200 ms (WT) / 160 ms (fitted KO) [55]
- A_se — Absolute synaptic strength — 7 (WT) / 10 (fitted KO) [55]
- U_se — Utilization of synaptic efficacy — 0.8 (WT) / 0.8 (KO) (no citation given)
- gNa — Neuronal sodium channel conductance — 15 nS (no citation given)
- gK — Neuronal potassium channel conductance — 4 nS (no citation given)
- Vrest — Neuronal resting membrane potential — -60 mV [71]
- NA — Avogadro Number — 6.02 x 10^23 (physical constant)
- qe — Net charge of single monovalent ion — 1.62 x 10^-19 C (physical constant; note: main text
  "Balance of ionic fluxes" paragraph instead writes "q = 1.6 * 10^-19 C" for the same quantity — a
  minor rounding inconsistency between Table 1 and the main text, both as printed)
- F — Faraday Constant — 9.64 x 10^-4 C.mol^-1 (physical constant; this exponent as printed looks wrong
  — the Faraday constant is ~9.65 x 10^4 C/mol, not 10^-4 — I flag this as a likely sign-of-exponent
  typo in the paper's Table 1, transcribed here exactly as printed)
- R — Gas constant — 8.314 J.mol^-1.K^-1 (physical constant)
- T — Temperature — 308 K (no citation given)
- glN — Neuronal leak conductance — 0.07 nS (no citation given — presumably fitted to the resting-state
  criterion described in Q2)
- VlN — Neuronal leak potential — -1.2793 mV (no citation given — presumably fitted)
- CN — Neuronal membrane capacitance — 136 pF [53]
- GKir — Astrocytic single channel Kir conductance — 60 pS (no citation given)
- VA1 — Kir current potential constant 1 — -14.83 mV, "extracted from [60]" (fitted, see Q4)
- VA2 — Kir current potential constant 2 — 34 mV, "extracted from [60]" (fitted, see Q4)
- VA3 — Kir current potential constant 3 — 19.23 mV, "extracted from [60]" (fitted, see Q4)
- CA — Astrocytic capacitance — 15 pF [72]
- VlA — Astrocytic leaking potential — -74 mV (no citation given — presumably fitted; note Q4 above
  says IlA "stabilizes the astrocyte membrane potential at -80 mV" while this table value is -74 mV —
  transcribed exactly as printed in each location; I did not reconcile the discrepancy)
- glA — Astrocytic leak conductance — 0.1 nS (no citation given)
- imaxA — Astrocytic Na/K pump rate — 0.3 mM.ms^-1 (no citation given)
- imaxN — Neuronal Na/K pump rate — 0.9 uM.ms^-1 (no citation given)
- Vol0/VolN — Extracellular space volume / neuronal volume — 0.5 [73]
- Vol0/VolA — Extracellular space volume / astrocytic volume — 0.5 [73]
- iNalN — Neuronal sodium leak rate — -1.35 x 10^-4 mM.ms^-1 (no citation given; used only in the
  sodium-balance equations 28-30, not quoted in full here since not asked)
- iNalA — Astrocytic sodium leak rate — -1.6 x 10^-3 mM.ms^-1 (no citation given)

Reference numbers [55],[53],[71],[72],[73],[60] are to other papers in this article's own bibliography;
I did not chase those down (out of scope for this lookup — flag if you want them resolved).

---

## 6. [K+]o at rest without stimulation

Resting extracellular K+ is explicitly stated as 2.5 mM:

Quote (Numerical implementations section, repeated): "...resting concentrations (neuronal [K+] and
[Na+]: 135 mM and 12 mM, respectively; extracellular [K+] and [Na+]: 2.5 mM and 116 mM, respectively;
astrocytic [K+] and [Na+]: 135 mM and 12 mM, respectively)."

Quote (Fig. 1 legend): "At resting membrane potential (-80 mV) and resting [K+]o (2.5 mM), the Kir4.1
current is outward, but as illustrated here, it reverses by increasing [K+]o."

Quote (Kir4.1 knockout section, repeated from Q2): "we added in equation 27 a constant K+ flux to
maintain [K+]o at an equilibrium value of 2.5 mM."

The paper does not state in so many words "[K+]o stays at its initial value forever absent
stimulation" as an isolated sentence, but the resting-state fitting procedure (Q2) and all three quotes
above together describe a model that is tuned to sit at a stable fixed point of 2.5 mM extracellular
K+ when unstimulated, and figures (e.g. S1 Fig, Fig. 3) show [K+]o returning to "baseline levels" after
a stimulation-evoked transient (quote, Results: "the extracellular K+ dynamics was associated... with a
~0.9 mM increase of [K+]o within 300 milliseconds, which slowly decayed back to baseline levels during
10 seconds"). I could not find an explicit separate sentence of the form "without any input [K+]o
remains fixed at 2.5 mM indefinitely" — this is the strongest statement found and it is inferred from
the combination of the four quotes above, not from one single explicit sentence; flagging this as the
one sub-point of Q6 that is inferred rather than directly quoted.
