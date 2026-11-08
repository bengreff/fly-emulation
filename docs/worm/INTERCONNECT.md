# Interconnect: how the worm's mechanisms feed each other

Status 7 Nov 2026 (wmodel). Authority for the module-to-module links; generated from the running code by
`src/wormemu/iograph.py` and held by `tests/test_worm_iograph.py`.

**Verdict.** In the default model every module-to-module read now has a producer, a unit and a test. The last open
read, `pathogen_exposure`, has a producer since 7 Nov evening (`mech/pathogen`, off by default: the naive 0 stays the
default). Three new links, each written only away from neutral: `bath_amine_nM` (drugs to neuromod),
`glia_amine_nM` (glia_release to neuromod) and `pathogen_exposure` (pathogen to learning). Temperature now reaches every rate class it was meant
to reach, including the compiled channel, synapse and pharynx mods. The body and the organs now share one internal
pressure. DAF-7 and CREB now act on something, and the AFD threshold reset has a producer. Every new effect is
neutral at its template (checked below), so nothing the scoreboard measured has moved.

## How the graph is read

`iograph.record(ms, values=...)` runs a default brain. It wraps `mech.Ctx` so that every `ctx.outputs` and
`ctx.obs` lookup is logged against the module making it, and it logs each module's writes (out keys, g_scale
names, I_pA, act_add). `iograph.contract_check(g)` compares that record with `iograph.LINKS`, the hand-written
contract with one unit per key. The checks are:

- every read is in the contract (or in `OPEN_READS`);
- every contracted read has a producer that wrote it;
- every non-conditional producer writes;
- every listed consumer's source names its key.

The test runs 40 ms with `slow_set_s` = 10 ms, so the slow modules start reading inside the run. It also moves
the conditional producers off neutral (daf7_effect -0.5, afd_tstar fracs 0.5) so that they write. The 24 modules
ran in REGISTRY order (measured).

## The links (default model; unit = the unit both sides use)

| key | producer | consumers | unit | what |
|---|---|---|---|---|
| q10 | temperature | senses_chem, senses_touch, senses_proprio, slow_signalling, learning, organs_intestine, organs_pharynx (clock form) | 1, dict by rate class | Q10 factor per rate class at the worm's temperature |
| temperature_C | temperature | slow_signalling, organs_pharynx | C | the worm's temperature (AFD T* components; the pharynx GHK temperature) |
| afd_gc_scale | glia | senses_chem | 1 per AFD | AMsh glia's scale on AFD guanylyl cyclase |
| coelomocyte_uptake_per_s | organs_other | organs_intestine, neuromod | 1/s | pseudocoelomic clearance |
| pressure_kPa | organs_other | senses_touch; the FEM body at start-up | kPa | body-fluid pressure |
| peptide_release | organs_intestine | neuromod | molecules/s by compartment | intestinal NLP-40 into the pseudocoelom |
| pumps | organs_pharynx | metabolism | pumps per step | feeding |
| pump_atp_excess_J_per_d | pumps | metabolism | J/d | Na/K pump ATP above rest (read at each DEB update) |
| egg_production_per_h | metabolism | organs_egglaying | eggs/h | DEB reproduction flux |
| energy_fraction | metabolism | slow_signalling, learning | 0 to 1 | reserve density e, clipped (fed = 1) |
| daf16_nuclear | slow_signalling | learning | 0 to 1 per cell | starvation signal |
| ma_release_scale | learning | neuromod | 1 per cell | pathogen learning on ADF serotonin (written once the state is away from 1) |
| ma_release_scale_slow | slow_signalling | neuromod | 1 per cell | **new**: DAF-7 on RIM/RIC amine release |
| afd_Tstar_shift_C | slow_signalling | senses_chem | C | **new**: AFD threshold reset |
| bath_amine_nM | drugs | neuromod | nM, dict by amine | **new (7 Nov evening)**: exogenous 5-HT, DA, OA, TA in the body fluid, added to every compartment (only while a bath amine is scheduled) |
| glia_amine_nM | glia_release | neuromod | nM, dict by amine | **new**: AMsh glial serotonin, added to the head compartment (glia_serotonin on; read one step late, as glia_release runs after neuromod) |
| pathogen_exposure | pathogen | learning | 0 to 1 | **new**: PA14 infection load from Experiment.infection_h (pathogen_sickness on) |

Three other kinds of link do not go through outputs:

- **g_scale** (per cell multipliers, product over modules): temperature (every density, the leak, rec_*,
  release), senses_chem, neuromod (Gq/Gs/Gi on release, EGL-19, IRK, NCA), slow_signalling (release, rec_glr,
  homeostatic densities), learning (release), drugs (release of cholinergic cells: aldicarb's cleft factor).
- **Implicit conductances** (NEURON point processes the modules set): drugs (levamisole, ivermectin), glia_release
  (AMsh GABA onto ASH), senses_proprio (DVA TWK-16 in the split form), k2p_leak (UNC-58).
- **Drive** (I_pA, act_add): noise, the organs, senses.
- **To the body**: BrainToBody (`mech.OVERRIDES`: pumps, eggs_laid, expulsions, pharynx/enteric/sex muscle
  activation, gcamp_dff, pressure_scale). The FEM body reads only `muscle_activation`
  (`body/loop.py Body.activations96`). The rest of BrainToBody goes to the observation models.

Body to brain is `BodyToBrain` (INTERFACE.md): head and tail fields from the environment, proprioceptive strain
and touch from the FEM.

## Temperature into every rate (row 25)

| class | Q10 template (label) | now applied to |
|---|---|---|
| gating | 3.0 (guessed) | **new**: every compiled channel's gates (`tadj` in the 15 BAAIWorm channel mods, the 5 Nicoletti mods, du_bwm's m/h/n/p/kr/ps, AWA's 7 gates); the transduction channels of senses_touch, senses_chem TRPV and senses_proprio (already) |
| conductance | 1.5 (guessed) | every BAAIWorm density, the leak, rec_* and release (g_scale, already) |
| enzyme | 2.5 (guessed) | senses_chem's cGMP cascade (already); **new**: the slow states, the homeostatic integrators, the AFD T* components, the associative states (dt x phi) |
| synapse | 2.0 (guessed) | **new**: wsyn's release, receptor, desensitisation and short-term plasticity states (`tadj`), and BAAIWorm's 4 synapse mods |
| pump | 2.0 (guessed) | **new**: the pharyngeal muscle gates (sh_pharynx's Crank-Nicolson gate step); the lumped clock's rate |
| dmp_clock | 1.0 (measured) | **new**: the intestine's IP3R oscillator and the nested timer (dt x phi) |

How the compiled factor works: `mech/temperature.py RATE_MODS` lists each mod, its class and the states to scale.
`patch_mod` adds `GLOBAL tadj` (1 by default) and multiplies those state equations while `brain._neuron` copies
the mods into the build, so the vendored files stay verbatim. The build tag hashes the patched text. temperature's
Mech sets `tadj_<suffix>` whenever T moves. du_bwm's Ca equation is left out, because scaling it would scale the
Ca influx, which is not a rate.

Checks (measured, 7 Nov): the whole brain for 300 ms at 20 C (T_ref) on the patched build against the unpatched
build gave max |dV| 0.0 mV over 397 cells, bit-identical. At 30 C, tadj is 3 (gating), 2 (synapse) and 2 (pump),
and all 397 cells' traces move (max 97 mV).

Not scaled yet (no class assigned; Open):

- Ca clearance in the Ca pools (cainternm, du_bwm's cad, sh_pharynx's shell);
- neuromod's diffusion and release kinetics;
- the c302 muscle mods (they read NEURON's celsius, set once from ion_celsius; nested form only).

## One pressure

The FEM body had its own constant pressure (body_pressure_kPa 100 and body_pressure_ctrl_kPa 100, both guessed).
organs_other's body fluid starts at osmo_p_set_kPa = 40 kPa (Sanzeni et al. 2019). These were two numbers for one
quantity. `body.layers.pressure_link` now sets the run's pressure to organs_other's steady state in the
experiment's medium, and the control pressure to the set point. Both body numbers become derived (`params.LINKED`,
out of the vector). In the template medium the ratio is 1, so the core modulus is unchanged (test_one_pressure).
A medium 50 mOsm more concentrated starts the body at a lower pressure, and so a softer core.

Validity: the linear volume-pressure law holds for P >= 0 (below that P is held at 0, the depressurised end).
Mid-run changes still do not reach the FEM, because the driver factorises once (Open).

## DAF-7, CREB, AFD threshold (row 18; all neutral at their templates)

- **DAF-7**: ASI's daf7 state (food) now acts through DAF-1 on RIM and RIC. Their amine release is multiplied by
  1 + daf7_effect x the mean ASI daf7. The new output `ma_release_scale_slow` is multiplied with learning's
  `ma_release_scale` in neuromod. daf7_effect: template 0, range -0.9 to 0, guessed (Greer et al. 2008, not
  opened).
- **AFD threshold**: T*AFD resets toward the worm's temperature with Yu et al. 2014's two components (tau
  cmk1_fast_tau_min and cmk1_slow_tau_h). The output `afd_Tstar_shift_C` = f_fast X_fast +
  f_slow (1 + creb_effect x creb_AFD) X_slow, read by senses_chem. f_fast and f_slow: template 0, range 0 to 1.
  A fit that adopts them should set the CMK-1 release stand-ins (cmk1_*_effect) to 0, so the reset is not
  counted twice.
- **CREB**: CRH-1 in AFD is the gain on the slow T* component. creb_effect: template 0, range -1 to 1, guessed
  (Nishida et al. 2011, not opened).
- learning now reads this worm's slow_set_s and slow_act_dv_mV (it read the templates), so the shared numbers are
  one number.

## Outputs no module reads (observation channels)

57 keys in the default run (measured). These are read by the data model's observation models (DATA_MODEL.md),
not by other modules:

- **Voltages and Ca**: glia_v_mV, other_v_mV, pharynx_v_mV, pharynx_ca_core_uM, enteric_v_mV, enteric_ca_mM,
  egg_vm_v_mV, egg_vm_ca_mM, bwm_ca_mM, intestine_ca_uM, intestine_ip3_uM, na_i_mM.
- **Sensory**: sens_*_po, sens_I_pA, sens_g_nS, sens_cgmp_uM, afd_cgmp_uM, afd_cascade_ca_uM, afd_Tstar_C,
  touch_indent_um, sens_proprio_strain.
- **Organs**: pharynx_epg_mV_per_ms, pharynx_pumps_total, expulsions_total, eggs_total, egg_uterus, egg_stretch,
  egg_vm_act, egg_5ht_occ, egg_nlp3_occ, uv1_tyramine_uM, nlp40_nM, pbo5_open, cleft_pH, body_fluid_volume_rel.
- **Energy**: deb, energy_state, pump_atp_J_per_d, pump_current_pA, o2_pmol_per_min.
- **Slow and plastic states**: slow_states, homeo, creb, daf7, associative, plasticity, neuromod, quantal_noise,
  channel_noise.
- **Other**: amphid_k_mM, amphid_ek_shift_mV, afd_cl_excess_mM, bwm_activation, neuropal_id.

Three of these were suspected breaks and are not:

- glia applies its amphid K shift itself, as a K leak current;
- egg-laying applies uv1 tyramine to HSN itself;
- the intestine's NLP-40 reaches neuromod as peptide_release (nlp40_nM is the direct form's diagnostic).

## Open

- The PA14 sickness pathways (ALA feeding cut, ASI DAF-7 quiescence, FLP-13 through DMSR-1): `pathogen_exposure`
  feeds only learning so far (`mech/pathogen` docstring).
- New out keys written only in non-default forms, read by nobody yet: glia_amsh_act, dva_twk16_po, k2p (diagnostics),
  drugs (per-drug body-fluid uM, agonist nS, ach_cleft_factor).
- Pressure changes during a run (FEM factorised once).
- The Q10 gaps listed above.
- The metaworm driver's own constants (`mw_*` slot rows: force-length width, density, plate contact). They are
  read only under non-default driver toggles and are not in the vector.
