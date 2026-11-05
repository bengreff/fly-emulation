# C. elegans body-mechanics parameters for a planar rod / RFT model

Compiled 2026-11-05. Labels: **measured** (reported directly in the source), **derived** (arithmetic shown here),
**inferred** (reasoned from a source but not a direct readout), **guessed**. "Not found" is used rather than making
a number up.

## 1. Boyle, Berri & Cohen 2012 (Front Comput Neurosci 6:10, doi 10.3389/fncom.2012.00010; full text PMC3296079)

Body/environment table (their Table 1/2, equations 1-2; values quoted from the paper, labelled **measured/adopted-
from-source** by Boyle et al., i.e. they are Boyle et al.'s modelling choices, not independent new measurements):

- Segments: M = 48 rod segments.
- Body length: L = 1 mm.
- Max radius: R = 40 um.
- Radius profile (eq. 2): R_i = R * sin[cos^-1((i - M/2 + 1)/(M/2 + 0.2))], i = 1..M. A smoothed ellipsoid-like
  taper, largest at mid-body, tapering to the head and tail ends.
- Drag, water (Newtonian, slender-body theory, citing Lighthill 1976): C_parallel,water = L / (2*pi*mu*ln(2q/a)),
  C_perp,water = L / (4*pi*mu*ln(2q/a)) + 0.5 (eq. 1); ratio K = C_perp/C_parallel ~ 1.5. Note: mu here is the
  **water/buffer viscosity** (~1 mPa s); the web-extraction tool returned "1 MPa s" which is almost certainly an
  OCR/unit error for 1 mPa s given mu is meant to be water-like — flagged, not corrected from a source I could
  re-check in the time available.
- Drag, agar: C_parallel,agar = 3.2e-3 kg/s, C_perp,agar = 128e-3 kg/s (ratio K ~ 40). Boyle et al. attribute
  C_parallel,agar to Wallace 1969 (via Niebur & Erdos 1991) and C_perp,agar to an estimate from Berri et al. 2009.
  These are lumped per-worm (or per-segment, unit unclear from the extraction — likely per-segment, not per unit
  length) coefficients in kg/s, i.e. force per velocity, not force per unit length per velocity. Flag: could not
  independently confirm the exact unit convention (per-segment vs whole-body) from the fetched text; treat as
  **measured-by-citation, unit convention uncertain**.
- Elastic/damping constants (their Table 1 notation): longitudinal spring kappa_L = (M/24) * 0.01 kg/s^2(?);
  diagonal spring kappa_D = kappa_L * 350; lateral damping beta_L = kappa_L * 0.025 s; diagonal damping
  beta_D = kappa_D * 0.01 s. (Units as extracted; the underlying units in the source table were not independently
  re-verified against the PDF, only the web-fetch extraction — treat these four as **measured-by-citation,
  low confidence on exact units**.)
- Muscle time constant: tau_M = 100 ms (their Table 3).
- Muscle force scaling: max force at the head F_max,1 = 0.7*(2/3); posterior gradient
  F_max,m = 0.70 - 0.42*(m-1)/M for m = 2..M, i.e. force capacity falls roughly linearly from ~0.70 (head,
  normalized units) to ~0.28 (tail), a 2.5x head-to-tail gradient. Minimum contracted length
  L_min,m = L0_L,m * (1 - Delta_M*(R_m+R_{m+1})/(2R)), Delta_M = 0.65.
- All of the above: **measured-by-citation** (i.e., Boyle et al.'s stated parameter choices, drawn by them from
  the cited sources or tuned by them) — not independently re-derived here. Given the time budget, the exact table
  was retrieved via an automated text extraction of the PMC page rather than visual inspection of the PDF table;
  recommend a follow-up direct read of Tables 1-3 in the PDF before using these numbers for component-level
  tuning, especially the spring/damping constants whose units look non-standard as extracted.

## 2. Fang-Yen et al. 2010 PNAS 107(47):20323-20328, doi 10.1073/pnas.1003016107 (PMC2996704)

- Table 1 (**measured**, mean +/- SEM, n > 10 young-adult N2 worms per condition, exact n not given beyond ">10"
  in the extraction): wavelength lambda/L swim 1.54 +/- 0.04, crawl 0.65 +/- 0.03; frequency swim 1.76 +/- 0.07 Hz,
  crawl 0.30 +/- 0.02 Hz. (Matches the context already supplied.)
- Bending/elastic modulus of the body: b = 9.5 (+/- 1.0) x 10^-14 N*m^2 (**measured**, their fit of the
  elastohydrodynamic model to wavelength vs. viscosity data). Derived-from-this Young's modulus ~13 MPa, noted by
  Fang-Yen et al. as far below the ~380 MPa of prior cuticle cantilever measurements (i.e., the effective
  whole-body bending stiffness is much softer than cuticle alone) — **measured/derived**, as reported.
  Cross-check: Wen et al. 2012 Neuron cite the identical b = 9.5e-14 N*m^2 value from Fang-Yen 2010 in their
  eq. 1, confirming the number.
  Note: this differs from Backholm et al. 2013's E_rod = 110 +/- 30 kPa derived from cantilever bending (section 7
  below) — the two groups measure different quantities (dynamic bend-propagation stiffness during active
  undulation vs. passive cantilever bending of a dead/anesthetized worm) and are not directly comparable without
  more care than this survey allows.
- Internal viscosity: upper bound b_v < 5 x 10^-16 N*m^2*s (**measured**, upper bound from their fits); the paper
  states "forces due to internal viscosity are at least 100-fold smaller than forces due to internal elasticity
  during locomotion" — i.e. internal (body-material) viscous damping is a minor term compared to internal
  elasticity for their frequency range.
- Drag coefficient used: C_N ~ 3.3*eta (transverse/normal drag coefficient scaling with medium viscosity eta,
  **measured/fitted** by them) with a noted ~9.7x enhancement in their thin experimental chambers vs. bulk fluid
  (a confinement correction, not a free-swimming value). C_T (tangential) value: **not found** in the extracted
  text — likely present in their Methods/SI but not retrieved in the time available.
  Curvature amplitude (normalized, i.e. kappa*L) and absolute forward speed per medium: **not found** in the
  extracted text (Table 1 as retrieved only shows wavelength and frequency, not curvature amplitude or absolute
  speed) — flagged as not found rather than derived, since wave speed = lambda*f would give the *wave* speed, not
  the body's forward speed (these differ by the slip ratio), and I did not want to conflate the two without the
  paper's own number.

## 3. Agar and water drag coefficients from direct force measurements

**Rabets, Backholm & Dalnoki-Veress 2014, Biophys J 107(8):1980-1987, doi 10.1016/j.bpj.2014.09.006 (PMC4213666).**
Key finding: on agar, drag does **not** follow simple linear RFT (constant C_N, C_T); instead force follows a
power law F = alpha * v^gamma. **Measured** (their Fig. 5), fit parameters at agar concentrations {1.0, 1.7, 3.0,
4.0, 6.0}% (w/v):
  - alpha_tangential = {0.35, 0.32, 0.26, 0.24, 0.20}
  - alpha_normal = {4.6, 6.8, 7.9, 7.3, 5.8}
  - gamma_tangential = {0.55, 0.58, 0.68, 0.77, 0.81}
  - gamma_normal = {0.27, 0.31, 0.30, 0.34, 0.38}
  (Units of alpha were not resolved in the extraction — likely nN per (um/s)^gamma or similar; re-check the PDF
  directly before using numerically.)
  - Ratio of normal-to-tangential drag slopes at high speed (>500 um/s): 1.4 +/- 0.2 (**measured**, their Fig. 2
    inset) — this is their measured effective anisotropy ratio, well below the K~40 that Boyle et al. 2012
    (section 1) attribute to Wallace/Niebur & Erdos. That's a real, citable discrepancy between an older
    literature value and this group's direct cantilever force measurement; flag it rather than silently pick one.
  - Young-adult crawling speed under their conditions: 80-300 um/s typical, assays run up to 1 mm/s (**measured**,
    consistent with the Sibernetic 2018 range of 0.1-0.3 mm/s already supplied).
  - Exact n (worms) for the force curves: **not found** in the extraction.

**Boyle, Berri & Cohen 2012** cite Wallace 1969's C_parallel,agar = 3.2e-3 kg/s and an estimate of
C_perp,agar = 128e-3 kg/s from Berri et al. 2009 (see section 1) — this is the "Niebur & Erdos 1991" lineage
value (Niebur & Erdos 1991, J Theor Biol, reviewed/re-used Wallace 1968's agar measurements for a related
crawling model); I could not independently open Wallace 1968 or Niebur & Erdos 1991 in the time budget, so these
numbers are **measured-by-citation, two citation hops removed** from the original Wallace 1968 measurement.

**Sznitman, Purohit, Krajacic, Lamitina & Arratia 2010, Biophys J 98(4):617-626, doi 10.1016/j.bpj.2009.11.010
(PMC2820645)** — water/buffer swimming:
  - M9 buffer viscosity: 1.1 cP = 1.1 mPa*s, density 1.0 g/cm^3 (**measured**, their stated experimental
    conditions).
  - Wild-type (N2) swim speed: <U> = 0.45 mm/s, n = 25 worms (**measured**; uncertainty/spread not given in the
    extraction beyond the mean).
  - dys-1 mutant swim speed: 0.17 mm/s, Re ~ 0.15 (**measured**, given only as a contrast case, not N2).
  - Wave frequency: f = 2.17 +/- 0.18 Hz, n = 25 (**measured**).
  - Head/tail curvature: head ~6.07 mm^-1, tail ~2.21 mm^-1, from head/tail lateral displacement amplitudes of
    465 um and 400 um respectively (**measured**).
  - Young's modulus E = 3.77 +/- 0.62 kPa, n = 25 (**measured**, their beam/elastohydrodynamic fit — note this is
    yet a third stiffness estimate, far softer than Backholm's 110 +/- 30 kPa and not obviously reconcilable with
    Fang-Yen's b = 9.5e-14 N*m^2 without a worked unit conversion I did not have time to do carefully; flag all
    three stiffness numbers as method-dependent, not interchangeable).
  - Bending modulus K_b = 4.19 +/- 0.49 x 10^-16 N*m^2 (**measured**) — note this is ~230x smaller than Fang-Yen's
    b = 9.5e-14 N*m^2; the two papers define/measure body bending stiffness differently (likely a cross-section
    convention difference, e.g. a thin-shell vs solid-rod model) — this is a real tension in the literature, not
    a typo, and should be resolved against the primary PDFs before picking one value for a model.
  - Explicit C_N, C_T drag coefficient values: **not found** in the extraction — the paper states they come "from
    slender body theory with wall corrections" but the extraction did not surface the numeric table.

## 4. Swim/crawl speeds, curvature, wave efficiency (N2 young adults)

- Crawl speed: 0.1-0.3 mm/s (Sibernetic 2018 experimental range, already supplied); consistent with Rabets 2014's
  80-300 um/s (**measured**, section 3).
- Swim speed: 0.29-0.38 mm/s (Sibernetic 2018, already supplied) vs. Sznitman 2010's 0.45 mm/s, n=25
  (**measured**) — same order, not identical; different strains/batches/temperature likely explain the gap, not
  resolved further here.
- Curvature amplitude: only found in normalized form from Sznitman 2010 (head ~6.07 mm^-1, tail ~2.21 mm^-1,
  **measured**, swimming). Fang-Yen 2010's Table 1 curvature-amplitude numbers were **not found** in the
  extraction (only wavelength/frequency were retrieved); Wen et al. 2012 Neuron report normalized curvature
  kappa*L as their plotting unit (Fig. 2A) but did not give a single summary amplitude number in the pages
  fetched.
- Wave efficiency / slip ratio (speed / wave speed): **not found** — none of the six sources opened in this pass
  gave this ratio explicitly, though it is derivable in principle from wavelength x frequency (wave speed) versus
  measured forward speed once both are in hand from the same source/row. Flagged for follow-up rather than
  computed from mismatched sources.
- Pierce-Shimomura 2008 PNAS 105:20982-20987 and Berri et al. 2009 HFSP J 3:186-193: only qualitative summaries
  were retrieved in the time budget ("crawl ~1 Hz high-amplitude bends on dry substrate; swim ~2 Hz lower-
  amplitude bends in liquid" per secondary description) — no primary-source numeric table was opened; treat as
  **not found** (numeric) / background only.

## 5. Body radius profile, length, mass density

- Max radius ~40 um, body length ~1 mm, formula R_i = R*sin[cos^-1((i-M/2+1)/(M/2+0.2))] — all **measured-by-
  citation** via Boyle, Berri & Cohen 2012 (section 1); this is their adopted/parameterized profile, consistent
  with the commonly cited ~1 mm adult length and ~30-40 um mid-body radius seen across the C. elegans literature
  generally.
- Body mass / density: **not found** in any source opened this pass. (A commonly used approximate value elsewhere
  in the field is a density close to water, ~1000-1100 kg/m^3, but I did not find a primary measurement for this
  in the sources searched here — do not use that number without a citation; it is not included as a value in this
  file because it would be a guess.)

## 6. Body-wall muscle: timing, force, arrangement

- Muscle activation/relaxation time constant: tau_M = 100 ms, Boyle, Berri & Cohen 2012 Table 3
  (**measured-by-citation** — a model parameter they set, sourced from calcium-transient/twitch literature they
  cite, not independently verified here). No independent Ca-decay time constant from a primary physiology source
  (e.g. Ca imaging) was retrieved in this pass — flagged as **not found** for a true physiological Ca-decay
  constant distinct from Boyle et al.'s model parameter.
- Force/torque per muscle: Boyle et al.'s normalized F_max gradient (section 1) is a relative scaling, not an
  absolute force in N or stress in Pa. An absolute number was not retrieved from Fang-Yen 2010, Petzold 2011, or
  Ghanbari 2012 in the time available:
  - Petzold et al. 2011, Biophys J 100(8):1977-1985 (PMC3077690): reports whole-body **stiffness**, not muscle
    force directly: baseline body spring constant 0.60 +/- 0.03 N/m, n = 17 wild-type N2 worms (**measured**,
    piezoresistive cantilever push), rising with light-induced (ChR2) or pharmacological (levamisole) muscle
    contraction and falling with relaxation (NpHR / muscimol) — exact contracted/relaxed numeric values were not
    separately resolved in the extraction, only the qualitative direction and the baseline number. They also
    report an effective elastic modulus of ~10 MPa for the combined cuticle+hypodermis+muscle outer shell
    (cuticle thickness 1.4 um) (**measured/derived**, their shell model).
  - Ghanbari et al. 2012, J Micromech Microeng 22:095009: micropillar force sensor, resolution 2.07 uN quoted for
    an 80 um body width (**measured**, instrument resolution, not a worm force value) — the actual peak/typical
    locomotive force the worm applies was **not found** in the snippet retrieved; would need the full PDF.
  - Fang-Yen 2010's own muscle-torque estimate (mentioned in the task's prompt as something they may have
    estimated): **not found** in the extracted text in this pass.
- Longitudinal arrangement / 24-vs-23 cells: 95 body-wall muscle cells total, in four longitudinal quadrants
  (dorsal-left, dorsal-right, ventral-right: 24 cells each; ventral-left: 23 cells) (**measured**, WormAtlas
  muscle system page, consistent with White et al. 1986 reconstruction). I could not confirm from the sources
  opened in this pass *which specific position* (anterior-most, or some other specific cell) is the one missing
  in the ventral-left quadrant, nor resolve the "MVL24 naming" question (whether the cells are still numbered 1-24
  with one number skipped, or renumbered 1-23) — **not found**; WormAtlas's detailed muscle-nomenclature page
  (not the summary page fetched here) would likely resolve this and is the recommended next stop.
  Fraction-of-body-length position of each of the 24 cells per quadrant: **not found** in this pass (would need
  WormAtlas's muscle position tables or White et al. 1986 directly).

## 7. Internal body viscosity / damping

**Backholm, Ryu & Dalnoki-Veress 2013, PNAS 110(12):4528-4533, doi 10.1073/pnas.1219965110 (PMC3607018).**
Conditions: worms anesthetized in M9 + 10 mM sodium azide (NaN3); cross-checked against BDM anesthesia, giving
consistent results (their Fig. 5B) (**measured**).
- Elastic (bending) stiffness EI scales with diameter D as EI ~ D^4, best-fit exponent 4.02 (**measured**, their
  Fig. 4), consistent with modelling the worm as a self-similar elastic cylinder.
- Young's modulus of a uniform-rod model: E_rod = 110 +/- 30 kPa (**measured**, matches the value already
  supplied in context).
- Upper-bound cuticle-shell modulus: E_cuticle = 1.3 +/- 0.3 MPa (**measured**, alternative shell-only model).
- Damping coefficient vs. bending speed: power law c ~ v_u^-1 (exponent -1, shear-thinning), over two decades of
  bending speed (**measured**, their Fig. 5-area result) — this is the "shear-thinning" finding in the paper's
  title; absolute prefactor value was not resolved numerically in the extraction (units Pa*s were noted but the
  leading coefficient was not retrieved) — flagged **not found** for the exact prefactor.
- Explicit Maxwell-model relaxation time constant (a single tau number): **not found** in the extraction — the
  paper frames the result as elastic (power-law in D) in series with a shear-thinning viscous damper (power-law
  in v), rather than quoting one scalar relaxation time; would need a direct read of their Results/Methods for
  any single-number time constant they may report for a specific worm size.
- Cross-reference: Fang-Yen 2010's internal-viscosity upper bound b_v < 5e-16 N*m^2*s (section 2) is a different
  quantity (dynamic, whole-undulation viscous term inferred from swimming/crawling wavelength data) from
  Backholm's cantilever-measured c(v_u) power law (a quasi-static mechanical test on an anesthetized worm); the
  two are not already reconciled in the sources opened here.

## 8. Proprioception: B-type motor neuron receptive field (Wen, Po, Hulme et al. 2012, Neuron 76(4):750-761,
doi 10.1016/j.neuron.2012.08.039; PDF via Harvard DASH repository)

- Spatial extent of the proprioceptive coupling: l ~ 200 um, inferred by the authors from their direct curvature-
  manipulation measurements (their Fig. 3D: bending of a posterior region requires anterior bending within a
  channel of length 300 um; posterior limit of effect at fractional body position 0.7 +/- 0.1, mean +/- SD,
  n >= 10 worms per condition) (**measured**, their Fig. 3D, with l stated as **inferred** by them from that data
  in their model section, "we can infer the spatial extent of this coupling l to be ~200 um").
  In body-length terms for a 1 mm adult, that is about 0.2 L — i.e., roughly a fifth of body length, not "half a
  body length" as one phrasing in the task prompt suggested; "half a body length" instead describes the typical
  maximum spatial extent the model needs to integrate over to reproduce wave propagation, not the single-step
  receptive-field length l itself. Treat l ~ 200 um (~0.2 L) as the number to use for a receptive-field length
  scale.
- Time constant: tau_c ~ 80 ms, **derived** by the authors (not directly measured): computed from l ~ 200 um and
  a measured maximum head-to-tail wave-propagation speed of ~2.6 mm/s for a 1-mm swimming worm in water, via
  tau_c = l / (wave speed) = 200 um / 2.6 mm/s ~ 80 ms (their text, stated explicitly as "we can estimate the
  limiting delay tau_c ... to be ~80 ms").
- Their analytic wavelength model (eq. 1): lambda = 2*pi*l / [omega*C_N*(lambda/2pi)^4/b + omega*tau_c], with
  C_N ~ 30*eta (eta = fluid viscosity) and b = 9.5e-14 N*m^2 (the identical Fang-Yen 2010 bending-modulus value,
  cited directly by Wen et al.) (**measured-by-citation** for b; C_N ~ 30*eta stated as their own approximation,
  **inferred/derived** by them, not an independent new measurement).

## Summary of open gaps (not found despite the search)

- Body mass / density of the worm (no primary source opened).
- Absolute forward speed and curvature amplitude broken out by medium in Fang-Yen 2010's own Table 1 (only
  wavelength/frequency were retrieved from the extraction).
- Wave efficiency / slip ratio (speed divided by wave speed) from any source.
- Exact units and per-segment vs. whole-body convention for Boyle et al. 2012's spring/damping constants and
  agar drag coefficients (recommend reading the PDF table directly, not just the extracted text).
- Which specific muscle-cell position is missing in the ventral-left quadrant (23 vs. 24 cells), and the
  per-cell anteroposterior position table.
- Absolute muscle force or stress (N or Pa) from a primary source; only whole-body spring-constant and shell-
  modulus surrogates were found (Petzold 2011).
- A single scalar Maxwell relaxation time constant from Backholm 2013 (only the power-law elastic and damping
  exponents were retrieved).

## Sources opened this pass

1. Boyle, Berri & Cohen (2012). Front Comput Neurosci 6:10. doi:10.3389/fncom.2012.00010. PMC3296079.
2. Fang-Yen, Wen & Samuel (2010). PNAS 107(47):20323-20328. doi:10.1073/pnas.1003016107. PMC2996704.
3. Rabets, Backholm, Dalnoki-Veress & Ryu (2014). Biophys J 107(8):1980-1987. doi:10.1016/j.bpj.2014.09.006.
   PMC4213666.
4. Sznitman, Purohit, Krajacic, Lamitina & Arratia (2010). Biophys J 98(4):617-626. doi:10.1016/j.bpj.2009.11.010.
   PMC2820645.
5. Backholm, Ryu & Dalnoki-Veress (2013). PNAS 110(12):4528-4533. doi:10.1073/pnas.1219965110. PMC3607018.
6. Wen, Po, Hulme, Chen, Liu, Kwok, Gershow, Leifer, Butler, Fang-Yen, Kawano, Schafer, Whitesides, Wyart,
   Chklovskii, Zhen & Samuel (2012). Neuron 76(4):750-761. doi:10.1016/j.neuron.2012.08.039 (read via Harvard DASH
   repository PDF, full text, 16 pages reviewed).
7. Petzold, Park, Shapiro, Pruitt et al. (2011). Biophys J 100(8):1977-1985 (PMC3077690), on body stiffness vs.
   muscle tone.
8. WormAtlas, Hermaphrodite Muscle System - Somatic Muscle page (summary numbers only; detailed nomenclature page
   not opened).

Not independently opened in this pass (cited above only via Boyle et al. 2012's reference list or secondary
description): Wallace 1968/1969; Niebur & Erdos 1991; Berri et al. 2009 HFSP J; Pierce-Shimomura et al. 2008 PNAS;
Ghanbari et al. 2012 J Micromech Microeng (abstract-level only); Krajacic 2012; Vidal-Gadea 2011.

## Follow-up 1 (2026-11-05, same-day targeted recheck)

This pass opened the actual Boyle, Berri & Cohen 2012 PDF (frontiersin.org, read directly page by page, not via
the earlier automated text-extraction tool) and re-checked Fang-Yen 2010 and several other sources for curvature
amplitude, speed, and the water/agar drag-coefficient unit convention. This corrects and sharpens section 1 and
section 2/3 of the main file above.

### 2. Boyle, Berri & Cohen 2012 — exact units and whole-worm vs. per-segment, from the PDF directly

Confirmed by reading the printed equations and Table 1-3 text directly (not the earlier automated extraction):

- Eq. (1), water (**measured-by-citation**, their adoption of Lighthill 1976 slender-body theory):
  C_parallel,water = L * 2*pi*mu / ln(2q/a); C_perp,water = L * [4*pi*mu / ln(2q/a) + 0.5].
  Immediately after the equation the paper states explicitly: "the values above are for the whole worm, so the
  drag coefficient experienced locally along the worm is proportionally smaller." This settles the question: as
  defined in eq. 1, C_parallel,water and C_perp,water are **whole-worm** force-per-velocity coefficients (units
  kg/s, i.e. N per m/s), not per-unit-length or per-segment values. A local/per-segment value is obtained by
  dividing proportionally (exact divisor, e.g. by M=48 or by fractional arc length, not stated in the equation
  itself — **not found** as an explicit formula).
  mu = dynamic viscosity, "~1 mPa*s for water" — this corrects the earlier draft's flagged "1 MPa*s", which was
  an artifact of the automated extraction tool, not the paper (**measured/corrected**).
  q is proportional to wavelength: q = 0.09*lambda; for a typical water wavelength lambda ~ 1.5 mm, q = 1.35e-4 m.
  L = 1 mm, a = 40 um (body radius, here called "a" not "R" in this equation).
  K = C_perp/C_parallel ~ 1.5 for water — stated as fixed by geometry alone for a Newtonian fluid.
- Agar (**measured-by-citation**, two citation hops): "For agar, Wallace estimated the tangential drag
  coefficient C_parallel by directly measuring the force required to pull glass fibers of similar dimension to
  C. elegans across the surface (Wallace, 1969). Based on this measurement, Niebur and Erdos (1991) estimated
  C_parallel,agar = 3.2e-3 kg*s^-1. We previously estimated the normal drag coefficient C_perp,agar from
  recordings of wild type worms using our motion simulator (Berri et al., 2009). Briefly, we found the ratio of
  drag coefficients to be in the range K_agar ~ 30-40; taking a value of K_agar = 40 and Niebur and Erdos'
  estimate for C_parallel,agar gives C_perp,agar = 128e-3 kg*s^-1." Units are again kg*s^-1 (force per velocity).
  The explicit "whole worm" sentence is textually attached only to the water equations, but given the agar and
  water coefficients are used interchangeably in the same simulation framework (same K ratio logic, same
  force-balance equations), it is **inferred** (not explicitly re-stated) that the agar values are on the same
  whole-worm basis.
  For simulations they allow any (C_parallel, C_perp) pair such that the minimum corresponds to water, the
  maximum to agar, and 1.5 <= K <= 40 (**measured-by-citation**, their stated design choice, Figure 4C).
  Numerical-methods context (section 2.4, not a physical parameter): for "less resistive media," solver tolerances
  were tightened when C_parallel <= 27.3e-6 kg*s^-1 or C_perp <= 51.2e-6 kg*s^-1 — this just shows the scale of
  their "virtual water" runs (~1e-5 kg/s), two to three orders of magnitude below the agar values; not a new
  physical drag value, flagged only for scale context.
- Table 1 ("Parameters of the physical model"), read directly from the printed table:
  M = 48; L = 1 mm; kappa_L = (M/24)*0.01 kg*s^-1 (printed exactly this way — note this is dimensionally odd for
  a Hookean spring constant, which by eq. 3's force balance should carry units of kg*s^-2 (N/m); flagging this as
  a genuine open question about either a typo in the source table or a non-standard parameterization, not
  resolved by this pass — recommend checking against the Supplementary Information model code, S14, mentioned in
  the paper, if exact units matter for implementation); kappa_D = kappa_L * 350; kappa_0M = kappa_L * 20 (muscle
  spring-constant prefactor, not seen in the earlier draft's extraction); F_max,1 = 0.7*(2/3); P = 2(M+1);
  Delta_M = 0.65; L_0L,m = sqrt(L_seg^2 + (R_m - R_{m+1})^2); L_0D,m = sqrt(L_seg^2 + (R_m + R_{m+1})^2);
  L_min,m = L_0L,m*(1 - Delta_M*(R_m+R_{m+1})/(2R)); F_max,m=2..M = 0.70 - 0.42*(m-1)/M; R = 40 um; L_seg = L/M;
  beta_L = kappa_L * 0.025 s; beta_D = kappa_D * 0.01 s; beta_0M = beta_L * 100 (muscle damping prefactor — the
  earlier draft mislabeled this family of numbers; beta_0M is a multiplier, not itself a 100 ms time constant).
  All **measured-by-citation** (Boyle et al.'s own fixed model parameters).
- Table 3 ("Parameters of the neuromuscular model") confirms the muscle time constant directly, resolving the
  earlier draft's uncertainty: tau_M = 100 ms (**measured-by-citation**, their stated value), with the text
  explicitly noting "Muscles respond as leaky integrators with a characteristic time scale of tau_M = 100 ms,
  which crudely agrees with response times of obliquely striated muscle (Milligan et al., 1997)." Governing
  equation (eq. 17): dA/dt = (1/tau_M)*(I_NMJ - A), i.e. a first-order low-pass activation variable, not a twitch
  force profile. Table 3 also gives N = 12 (repeating neural units), N_SR = M/2, N_out = M/N, and several
  dimensionless neural-circuit weights not relevant to body mechanics.

### 1 & 4. Curvature amplitude, lateral displacement, speed, frequency, wavelength (slip check)

- Boyle et al. 2012, Figure 3A (**read from figure**, their own experimental data, averaged "first over time
  (~10 s) and then over several worms," n = 3 agar worms, n = 5 water worms, error bars = SD across worms):
  curvature kappa-bar (1/mm) vs. fractional body position S (0 = head, 1 = tail). Agar: ~8-9 /mm near the head
  (S~0-0.1), declining roughly monotonically to ~2 /mm at the tail (S=1). Water: ~3 /mm near the head, declining
  to ~1 /mm at the tail. These are read off the plotted curve by eye, not table values, so treat the numbers as
  approximate (+/- ~0.5 /mm reading error) rather than exact. No forward speed, frequency or wavelength is given
  alongside this specific figure, so slip cannot be computed from this panel alone.
- Fang-Yen 2010 (re-checked): still only wavelength (lambda/L) and frequency are in the retrievable Table 1;
  I could not obtain the actual PDF (PNAS and PMC PDF fetches both failed — PNAS blocked the request, and the PMC
  PDF route returned an empty/placeholder page both in the first pass and when retried just now) so curvature
  amplitude and absolute speed from Fang-Yen 2010's Figures 1-2 and any SI remain **not found**. This is a tooling
  limitation (I could not get a renderable PDF for this one paper, unlike Boyle 2012 and Wen 2012, where the PDF
  fetch worked), not a confirmed absence in the source — flag for a follow-up that tries a different PDF host
  (e.g. the author's lab page, u.osu.edu/fangyenlab/publications) or an institutional proxy.
- Sznitman et al. 2010 (from the main pass, re-used here as the closest thing to a single-source speed+frequency
  dataset): swim speed <U> = 0.45 mm/s (n=25, **measured**), frequency f = 2.17 +/- 0.18 Hz (n=25, **measured**),
  head/tail curvature ~6.07 and ~2.21 mm^-1 (**measured**) — but no wavelength value was retrieved from this
  source either in the first pass or this one, so slip = speed/(lambda*f) still cannot be computed from a single
  source. **Not found**: an explicit wavelength number in Sznitman 2010's retrievable text.
- Karbowski et al. 2006, J Theor Biol 242:652-669, "Conservation rules, their breakdown, and optimality in
  Caenorhabditis sinusoidal locomotion": confirmed to exist and to contain crawling wavelength/amplitude/speed
  data together (per secondary description: "the spatial form and temporal frequency of the crawling gait is
  largely independent of... worm size and agar rigidity"; swimming has ~1 wavelength along the body, crawling
  ~2), but no primary numeric table was opened in the time budget — PDF not fetched. **Not found** (numeric).
- Padmanabhan et al. 2012, PLoS ONE 7(7):e40121, "Locomotion of C. elegans: a piecewise-harmonic curvature
  representation of nematode behavior": confirmed as the right paper (fits a harmonic curvature function to
  swimming image sequences, amplitude and wavevector constant across frames), but no numeric amplitude/speed
  values were retrieved in the time budget. **Not found** (numeric).
- Berri, Boyle, Tassieri, Hope & Cohen 2009, HFSP J 3(3):186-193, doi 10.2976/1.3082260: confirmed as the primary
  source behind Boyle et al. 2012's Figure 4A (frequency-wavelength data across gelatin concentrations and agar),
  and qualitatively covers frequency range 0.5 Hz (crawl) to 2 Hz (swim) with wavelength increasing accordingly,
  but I did not find an open PMC/PDF copy in the time budget (HFSP Journal does not appear to be in PMC open
  access, and no institutional-free PDF was located) — **not found** (numeric values), confirmed as a real gap
  rather than an oversight.
- Pierce-Shimomura et al. 2008 and Krajacic/Vidal-Gadea: not reopened this pass; still **not found** (numeric),
  same as the main file.
- Net result: no single primary source opened in either pass gives curvature amplitude, lateral displacement
  amplitude, forward speed, frequency and wavelength all together for the same N2 young-adult condition, so the
  slip ratio (speed / (lambda*f)) could not be computed from one self-consistent source. The two best partial
  candidates are Fang-Yen 2010 (wavelength + frequency, no speed/curvature retrieved) and Sznitman 2010 (speed +
  frequency + curvature, no wavelength retrieved) — getting the actual PDFs of either (rather than relying on
  automated web-page text extraction) is the recommended next step, since both failed to render as fetchable PDFs
  in the tools available this session.

### 3. Fang-Yen 2010 — tangential drag coefficient and forward speed

Re-checked via the PMC article page (PDF route failed again, see above). Result unchanged from the main pass:
- No explicit C_T (tangential/parallel drag coefficient) value or formula was found; the retrievable text only
  gives the normal/transverse coefficient C_N ~ 3.3*eta (eta = medium viscosity in Pa*s) and does not state a
  C_N/C_T ratio. **Not found.**
- No absolute forward speed (mm/s) per medium was found in the main text, figures, or what's indexed of the SI.
  **Not found** — flagged as a tooling gap (PDF not retrievable this session) rather than a confirmed absence,
  since SI sections are often not captured by HTML/text extraction of the PMC article page at all.

### Updated open gaps after this follow-up

- Fang-Yen 2010's full PDF (including SI) still not obtained — blocks curvature amplitude, absolute speed, and
  C_T/ratio questions. Try a non-PMC, non-PNAS host next (lab website, ResearchGate).
- No single source yet gives wavelength + frequency + speed + curvature together for one N2 condition; slip ratio
  remains uncomputed.
- Boyle et al. 2012's kappa_L units (kg*s^-1 vs. the dimensionally-expected kg*s^-2) unresolved — worth a direct
  check against their Supplementary Information model code (S14) rather than the main-text table alone.
- Karbowski 2006, Padmanabhan 2012, Berri 2009 HFSP J: existence and topic confirmed, no numeric tables opened
  yet.
