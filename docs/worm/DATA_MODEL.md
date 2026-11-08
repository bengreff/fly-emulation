# The data model: `wormemu.simulate(theta, experiment) -> observations`

Status 7 Nov 2026 (wmodel). Code: `src/wormemu/datamodel.py`. Tests: `tests/test_worm_datamodel.py`.

**Verdict.** The fit can now call one function on the whole worm. It takes the parameter vector and a declarative
experiment, and it returns the observation channels. With no intervention it reproduces a plain brain run exactly.
Genotype, ablation, clamps, optogenetics, fields and temperature all act through the model's own quantities. Not yet
covered: drugs (none representable), the body-on closed loop (route named, not wired) and 21 corpus genes (listed in
`NOT_YET`, each with the reason).

## Call

```python
from wormemu import datamodel as D
ex = D.Experiment(duration_ms=2000, temperature_C=22, cultivation_C=20,
                  head={"nacl_mM": 50}, stimuli=[D.Stimulus("nacl_mM", 500, 1000, 25.0)],
                  opto=[("AVAL", 800, 300, 1.0)], clamps=[D.Clamp("AVBL", "voltage", 0, 2000, -40.0)],
                  genotype=[D.Allele("unc-49"), D.Allele("egl-19", "reduction", 0.5, "acute")],
                  ablations=["AVAR"], observe=("gcamp_dff", "clamp_pA", "pumps", "out:afd_Tstar_C"))
r = D.simulate(theta, ex)      # r["t_ms"], r["cells"], r[channel], r["notes"]
```

`theta` is the vector in `params.Theta` order (natural units), a `{id: value}` dict (via `params.set_value`, so a
scan number raises), or None (this worm's values). `Experiment.seed` picks the worm drawn; theta applies over it.
One NEURON per process: run each experiment in a fresh process.

## The experiment

| field | what it sets | route in the model |
|---|---|---|
| `temperature_C` | the worm's temperature | `ion_celsius` (linked) and the head field `temperature_C`, so every Q10 class and the compiled `tadj` (INTERCONNECT.md) |
| `cultivation_C` | AFD's T* | `sens_afd_Tstar_C` (an experimental condition, scan) |
| `head`, `tail` | constant fields | `interface.HEAD_CHANNELS` / `TAIL_CHANNELS` (odours, salt, O2, CO2, light, food_OD, osmolarity_mOsm) |
| `stimuli` | a schedule of field values, `contact_force_uN` over a midline span, `nose_force_uN`, `tap` | BodyToBrain each step; every stimulus reaches the brain through its sensory model |
| `opto` | GUR-3/PRDX-2 light per cell, (cell, t_on, dur, intensity) | `mech/observation.SCHEDULE` (Randi 2023's actuator) |
| `clamps` | current clamp (pA) or voltage clamp (mV) of a soma in a window | current: an `I_pA` term; voltage: a NEURON SEClamp, off (1e9 MOhm) outside the window |
| `body` | off, immobilised, on | off and immobilised: open loop, straight and untouched (the brain's inputs are the same in both). on: `NotImplementedError`; the route is `body.loop.run` with `Body(params=body.layers.params_for(spec, extra_mosm=...))` |
| `genotype` | `Allele(gene, null / reduction, factor, developmental / acute, t_on_ms)` | `GENES` below |
| `ablations` | cells removed | `Brain(cells=...)`: the cell and every synapse and gap it makes |
| `drugs` | (name, uM, t_on) | `DRUGS`: none is representable yet; `simulate` raises with what is missing |
| `toggles` | mechanism forms | over the defaults |
| `observe`, `cells`, `every_ms` | the channels, the cells reported, the sampling | below |

## Genotype (`datamodel.GENES`, 89 genes)

Each gene maps to one or more effects on quantities the model already has:

| route | genes | effect |
|---|---|---|
| `("g", dens_<channel>)` | egl-19, unc-2, slo-1, slo-2, egl-2, shl-1, kqt-1, kqt-3, kvs-1, egl-36, cca-1, shk-1, unc-103, exp-2, nca-1;nca-2 | the channel's density in every cell. BAAIWorm's nanodomain SLO channels go with both of their genes |
| `("g", rec_<class>)` | an obligate subunit (unc-29, unc-38, unc-63 for L-AChR; nmr-1, nmr-2) or a class's only gene (acr-16, mod-1, lgc-55, lgc-53, acr-23) | the receptor class's conductance at every synapse |
| `("tpm", gene)` | one gene of a multi-gene receptor class (unc-49, glr-1, glc-*, ...); the 17 innexins | the gene's CeNGEN expression, wherever the model reads it (structure_rules' receptor shares and innexin weights, the density map). Developmental only |
| `("tx", transmitter)` | unc-17, eat-4, unc-25, cat-2, tph-1, tdc-1 (tyramine and octopamine), tbh-1 | the transmitter leaves every cell's identity. A cell left with none gets fast release 0, not the unknown-transmitter graded stand-in. Null only |
| `("spec", id)` | unc-31 (dcv_rate_per_s) | the scalar scaled. Developmental only |

Timing: **developmental** applies from t = 0, so the slow set points and homeostasis form with the allele.
**Acute** applies from `t_on_ms`, by default the end of the set-point window (`slow_set_s`), to a worm that formed
without it. A null sets the effect to 0; a reduction multiplies it by `factor`.

`NOT_YET` (21 genes) lists what the model cannot express, each with its reason:
- vesicular transporters and cofactors apart from the markers (unc-47, unc-46, cat-1, cat-4, bas-1);
- unc-36;
- the release machinery (unc-13, unc-18);
- channels keyed by cell, not gene (tax-4, tax-2, osm-9, ocr-2, mec-4, trp-4);
- daf-2 and daf-7;
- npr-1 and the other GPCR nulls (neuromod's receptor table is not editable yet);
- egl-1, unc-77 and unc-80.

## Observations (`datamodel.OBSERVABLES`)

Per cell, `[samples, cells]`:
- `v_mV` and `ca_uM`;
- `gcamp_dff` (the row 23 indicator model, NaN for muscles);
- the muscle activations (body wall, pharynx, enteric, sex).

Events per sample: `pumps`, `eggs_laid` and `expulsions`. The window per voltage clamp is `clamp_pA` (electrode
current, + = into the cell). `out:<key>` returns any module output, which covers the 57 diagnostic keys in
INTERCONNECT.md (for example `out:afd_Tstar_C`, `out:intestine_ca_uM`, `out:pharynx_epg_mV_per_ms`).
`posture` (curvature, gait) needs the body on: not yet.

## Checks (measured, 7 Nov; 50 ms runs, whole brain, 397 cells)

- The template experiment against `Brain(sample_worm(None))` stepped open loop: max |dV| 0.0 mV, bit-identical.
- egl-19 null: 131 cells move by more than 0.1 mV (max 9.3 mV).
- unc-49 null by the CeNGEN-share route: 321 cells move (max 45.8 mV). The tpm route does reach the receptor shares.
- eat-4 null:
  - glutamate leaves every cell (the template has more than 50 glutamatergic cells);
  - 74 cells are left with no transmitter, and their fast release goes to 0;
  - 308 cells move.
- Clamps:
  - the voltage clamp holds AVAL at -40.0 mV and passes 102 pA at 15 ms. Outside the window it passes about 2e-5 pA
    (1e9 MOhm series resistance; measured in the test run);
  - +20 pA raises AVBL by 6.3 mV;
  - an ablated AVAR is absent.

## Validity and open items

- A gene's effect stops at what the model represents. A receptor null removes the ionotropic class at synapses.
  Whether the extrasynaptic amine channel (neuromod's mod-1 route) follows is not checked.
- The tpm route reaches only code that reads `Brain.st`. Ledger tables precomputed from CeNGEN do not move.
- Drugs need agonist conductances, a cleft ACh clearance step and bath sources in neuromod.
- Body on: wire `body.loop.run` and read posture and gait from its outputs.
- `pathogen_exposure` has no producer. The learned state has to come from the experiment's history (a training
  schedule), which is not a field yet.
