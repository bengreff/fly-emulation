# s23 N2: measured passive and threshold membrane values by class (24 October 2026)

Sonnet reader (Explore, 24 Oct). Only values the reader took from primary full text ("direct") are usable. Values
taken from search summaries are listed as leads. None was checked against the PDF, and one (the 16.06 ms "KC" τ_m)
is the MBON-α3 value misattributed. The model now uses Shiu 2024's shared values: V_rest −52 mV, threshold −45 mV,
τ_m 20 ms (borrowed, not per class).

## Direct (primary full text)

| Class | τ_m | R_in | V_rest | Other | n, prep | Source |
|---|---|---|---|---|---|---|
| AL uniglomerular PNs | — | 598.0 ± 69.3 MΩ (SEM) | −57.8 ± 1.5 mV "true" rest (cell-attached rate match; whole-cell reads −47.8 ± 1.6) | SIZ threshold "near −40 mV" (assumed by the authors, not measured) | 14 (R_in), 12 (V_rest); in vivo whole-cell, female 2-10 d, LJP +13 mV | Gouwens & Wilson 2009 J Neurosci 29:6239 (PMC2709801) |
| MBON-α3 | 16.06 ± 2.3 ms | 926 ± 55 MΩ | −56.7 ± 2.0 mV | C_m 16.76 ± 1.90 pF (τ/R, derived) | 5; ex vivo whole-cell, 2-3 d, room temperature, LJP 13 mV | Bilz et al. 2023 eLife 12:e77578 (PMC10069864), Table 1 |
| Leg tibia flexor MNs, fast / intermediate / slow | — | 150 / 300 / 700 MΩ (means, Fig. 3E) | −68 / −60 / −48 mV (Fig. 3C) | — | 15 / 11 / 14; in vivo whole-cell, female 1-4 d | Azevedo et al. 2020 eLife 9:e56754 |

**Blinding note (Azevedo):** the reader saw the per-type R_in and V_rest. The input resistances fall in the order of
the size principle, which underlies the held-out recruitment order (slow → intermediate → fast). These values must
not set MN parameters while the recruitment order stays held out: using them would make that test circular. The
order itself was not read. This is recorded in the HANDOFF register.

## Leads only (search summaries; verify before any use)

KC R_in 2.5 ± 1 GΩ and V_rest −55 ± 10 mV (Turner, Bazhenov & Laurent 2008); AL LN R_in 1-4 GΩ (Wilson & Laurent
2005, via Seki 2010); ORN R_in about 1.8 GΩ, V_rest −70 mV (Dubin & Harris 1997); DN1p R_in 1.6 ± 0.1 GΩ, V_rest about
−63 mV in the subjective day, cycling with time of day (Flourakis 2015); GF R_in 50-100 MΩ (acceptance criterion, weak).
HS about −55 mV may be blowfly data.

## Nothing usable found

DANs, LHNs, CX types (E-PG, P-EN, Delta7, FB tangentials), DNa02/DNg, flight MNs, VNC 13B/10B/9A, optic-lobe types.

## Model against the direct values

- τ_m 20 ms against MBON-α3 16.06 ± 2.3 ms (n 5; spread type not stated): 20 is above the reported spread.
- V_rest −52 against PN −57.8 ± 1.5 (SEM, n 12; SD about 5.2) and MBON-α3 −56.7 ± 2.0: inside the PN spread, near
  the MBON edge.
- Threshold −45: there is no measured threshold for any class; PN −40 is the authors' assumption.

N2 path: a per-class stage for PNs and MBONs (V_rest shift; MBON τ_m 16 ms) is possible with these values, but each
stage needs a gate and a smoke, and threshold stays shared and borrowed. So N2 stays heavy.
