# S12: hemolymph ions and the model's reversal potentials (S6, data first)

Question (BLANKS_AUDIT S6, night order item 3): is there measured data to build
`state:hemolymph|ion_model`, an ion model that sets reversal potentials from hemolymph composition and
lets feeding or dehydration move them?

Method: one Sonnet Explore agent (web search and fetch, 5 October 21:59), then a check of how the model
uses reversals. The agent read some papers in full and others only as abstracts or snippets; it says
which. I could not re-read Naikkhwah & O'Donnell 2011 (the JEB page returned a Cloudflare block, saved as
`data/raw/naikkhwah2011/p.html`), so every literature item below is **secondary**.

## Measured composition (secondary)

| Quantity | Compartment | Value | Method, n | Source | Read |
|---|---|---|---|---|---|
| K | adult hemolymph | about 26 mM; unchanged on a 0.4 M KCl diet | ion-selective microelectrode, n = 19-22 | Naikkhwah & O'Donnell 2011 J Exp Biol 214:3443, Fig. 2 | agent, full text |
| Na | adult hemolymph | about 26-36 mM; +32-57% on a 0.4 M NaCl diet | same | same | agent, full text |
| Na, K, Ca, Cl | adult *D. hydei* hemolymph | Na 56, K 31, Ca about 18 mval/l, Cl 36 | not identified | J Insect Physiol 1974, doi:10.1016/0022-1910(74)90047-X | snippet, unverified |
| Ca | adult hemolymph | about 0.5 mM | not identified | cited in Dubé et al. 2000 | snippet, unverified |
| osmolality | adult hemolymph | 251 ± 9 mOsm (SE) | freezing point | Singleton & Woodruff 1994 Dev Biol 161 | abstract |
| osmolality | adult hemolymph | 353 ± 11 mOsm (control); 315 ± 7 (desiccation-selected) | not stated | Albers & Bradley 2004 J Exp Biol 207:2313 | abstract |
| osmolality | larval hemolymph | 319 ± 5.7 mOsm/kg (n = 8) | osmometry, gut contamination corrected | Kurio et al. 2024 J Exp Biol 227:jeb247249, Fig. 2B | agent, full text |
| ions | brain interstitial fluid | **no Drosophila measurement found** | | | |
| [K]i, [Cl]i | central neurons | **no absolute value found** (SuperClomeleon gives relative changes only) | | Flourakis et al. 2015 Cell 162:836 | snippet |

Feeding state: no reversal potential measured fed against starved. IPC resting potential is −51 mV fed and
−59 mV starved (median, Bisen et al. 2025 eLife 13:RP98514, Fig. 1E; agent read the full text). That is a
resting potential, not a reversal.

## What the reversals in recordings depend on

- Adult central recordings use a fixed saline: 103 NaCl, 3 KCl, 26 NaHCO3, 1.5 CaCl2, 4 MgCl2 (Wilson &
  Laurent 2005 and later; snippet). So bath K is 3 mM, about a ninth of the hemolymph value above.
- In other insects the perineurial glia form a blood-brain barrier that holds interstitial K below
  hemolymph K (Treherne & Schofield 1981, abstract; Hendy & Djamgoz 1987, cockroach K-electrodes, values
  not retrieved). No Drosophila value.
- Measured reversals depend on the pipette solution as well: nAChR EPSCs +8.9 ± 1.7 mV in adult Kenyon
  cells (Gu & O'Dowd 2006, snippet); GABA −56 ± 3 mV in larval central neurons (Rohrbough & Broadie 2002,
  snippet; the value m10q uses as `e_inh`).

## Where the model uses reversals (derived from the code, 5 October)

- Synapses under m9r are current-based (`conductance_based` 0), so `e_exc` and `e_inh` are not read in
  the working model. The m10 line uses `e_inh` −56 (measured in related preparations).
- The rung-1 intrinsic channels use `channels.E_K, E_NA, E_CA, E_H = −80, 50, 100, −35` mV, a module
  constant labelled guessed, outside the registry.
- Nernst at 22 °C (RT/F = 25.43 mV) with a guessed [K]i of 140 mM: E_K is −97.7 mV at 3 mM outside
  (recording saline), −80.1 mV at 6 mM, −42.8 mV at 26 mM (hemolymph). So the model's −80 corresponds to
  about 6 mM outside (derived from a guess).
- The channel densities were fitted to current steps recorded in 3 mM K saline (Azevedo 2020 slow
  motor neurons). The fitted values carry the saline's reversals with them.

## Reading

There is measured hemolymph K and Na for the adult, and diet moves Na but not K. There is no measurement of
what neurons see: brain interstitial ions and intracellular ions are both unmeasured in Drosophila, and
the blood-brain barrier separates the two compartments. Putting hemolymph K into the Nernst equation
would move E_K from about −80 to −43 mV, which would depolarise every cell with K channels by tens of
millivolts. That would be wrong for the brain and inconsistent with the fitted values, which were
measured in 3 mM K saline.

## Decision (5 October)

S6 stays **absent**. A sourced ion model needs interstitial K, Na, Cl and Ca in the adult brain, or a
barrier model with measured transport rates. Neither exists for Drosophila. The data above are recorded
so the stub's reason is specific. One thing changes: `channels.E_K` and the other channel reversals are
module constants outside the registry. Moving them into the registry, labelled guessed and declared
equivalent to recording saline, is a bookkeeping step that would make the S6 switch's target explicit.
It is listed for later, not done tonight.

Experiment that would settle it (for Ben's list): K- and Na-selective microelectrodes in the adult
central brain interstitium (as Hendy & Djamgoz did in cockroach), fed against 24 h starved against
desiccated, alongside a hemolymph sample from the same fly.
