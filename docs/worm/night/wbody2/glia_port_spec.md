# Item 8 (line 4), glia K+ load from the neurons' own K+ currents: port spec (wbody2, 9 Nov 2026)

Status: class B (the published form is missing), to be built as a C toggle with the current form nested. Nothing
built yet. Source: `lit_glia_port.md` (Sonnet agent, full text of Sibille, Dao Duc, Holcman & Rouach 2015 PLoS
Comput Biol 11:e1004137, PMC4380507, read from the article's MathML; equations 1-30 and Table 1 in the main text).

## What runs now (glia.py, glia_kbuffer = kir)

Each amphid neuron's K+ load into its side's ending is a linear leak estimate, g_K ((v - v0) - dE_K), with g_K the
K+ share (glia_k_leak_frac 0.5, guessed) of the neuron's passive leak and v0 its mean over the first 1 s. The K+ rise
acts back as an injected current g_K dE_K. Measured (23:27 probe): the 0-1 s mean holds the start-up from V_INIT
-65 mV, and the network keeps moving (consecutive 1 s means 0.5-1.5 mV apart, 0.26 mV noise floor, 40-60 s), so
v - v0 is a steady sink: the endings sit 0.15 mM below the bath at the check's clamp and 0.36 mM by 24 s, and
check_glia fails tau (1.25 s vs 3.4-4.0) and the null ratio (1.11x vs >= 1.24x).

## What the source does (quoted in lit_glia_port.md)

- Only the neuron's gated K+ current feeds extracellular K+ (HH I_K = gK n^4 (V - E_K), eq. 8), not its leak.
- d K0 / dt = iK - 2 ipumpN - 2 ipumpA + iKir (eq. 25): neuronal K+ current in, neuronal and astrocytic pumps
  (2 K+ per cycle) out, Kir4.1 either way. No diffusion or bath term.
- Pump (eq. 24): ipump = imax (1 + 7.3 / K0)^-2 (1 + 10 / Na)^-3 (the printed "10 Na" is read as 10 / Na, a
  dropped fraction bar; flagged in the notes).
- Rest: the leaks (glN, VlN, glA, VlA) are set so the system rests at stated concentrations (K0 2.5 mM, neuronal K+
  135 and Na+ 12 mM). There is no subtracted resting current; balance is a property of the resting state.
- E_K follows K0 in every K+ current (Nernst), so the feedback runs through the channels themselves.

## The port

Toggle `glia_k_load` (glia.py):
- `leak` (nested; the current code): g_K ((v - v0) - dE_K), the injected g_K dE_K feedback.
- `channels` (the port): each amphid neuron's load is its gated K+ current, the sum of ik over its segments (ik x
  area, pA; every K+ mod reads ek and writes ik, brain.EK_MODS plus kqt3 and the Nicoletti mods: to verify at
  build), minus the same sum at rest. The feedback sets ek on that neuron's sections to ion_ek + (RT/F) ln(Ko /
  Ko_bath) each step (the channels' own E_K, eq. 8), and injects nothing. Validity: the resting balance (Sibille's
  tuned leaks and pumps) is represented by subtracting the resting ik, because the fitted leaks here already contain
  the resting pump (pumps.py makes the same choice).
- The reference: the source's balance is a settled rest; this network does not settle. Both forms take the
  reference over the same window, `glia_v0_window` = first (nested: 0-1 s, as now) | settled (1-2 s, after the
  start-up from V_INIT; 23:27 probe: median drift 0.20-0.32 mV at 19-20 s against it, vs 3.0 mV against 0-1 s).
  The window is a choice about the start-up transient, not a fitted value; no other value moves.

## Bars (write into the check script's docstring before running)

1. Neutral: `glia_k_load=leak`, `glia_v0_window=first` bit-identical to the code before the port (check_glia's
   setup, every recorded quantity).
2. Load identity: with one amphid neuron clamped 20 mV above rest for 1 s, the `channels` load equals the change
   in that neuron's summed ik to 1e-9 relative, and the ek shift on its sections equals (RT/F) ln(Ko / Ko_bath) to
   1e-9 mV.
3. Zero input (the Open item's bar): the ending K+ stays within 0.05 mM of the bath for 20 s, in each of the 4
   forms (reported for all 4; the bar applies to the adopted candidate).
4. check_glia re-run under each form with its bars unchanged (ceiling 10.2 mM, tau 3.4-4.0 s, null >= 1.24x).

Then tests (forms, neutral, identity), the vitals battery, and the MECHANISMS_AUDIT row 11 text through wbrain2.
Defaults stay `leak` and `first` until a gate, a battery run and a viewed figure adopt a change.

Expected (guessed, written before building): the settled window removes most of the false sink (bar 3 likely
passes in both load forms); the channels form changes tau through the gated K+ currents' size, direction unknown.
If bar 3 fails under `settled`, the drift is the network's (wbrain2's), and the line is written down as such.
