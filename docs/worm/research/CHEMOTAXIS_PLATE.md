# Chemotaxis plate: what BAAIWorm's scene is, and the numbers for an agar plate with a gradient

Body worker, 2026-11-05 16:49 CST. Ben's demo environment: "agar plate with a chemical gradient (BAAIWorm's
chemotaxis scene)". Code: `src/wormemu/body/scene.py` (MB11). Literature check by a Sonnet research agent; "read in
the paper" means it read the primary text, "secondary" means a later paper or summary only.

## Verdict

BAAIWorm's chemotaxis scene is a gradient with no plate. One target point; the head senses minus its distance to
it; the brain gets the normalised change as a current into 15 sensory neurons. The worm swims in 3D fluid with no
gravity or floor (the floor is drawn only), and upstream's default run is "offline", where the gradient is not used
at all. So the port is in two parts: the field (ported, with physical units added from the literature) and the
plate (not in BAAIWorm; from Sibernetic and the literature, MB6).

## BAAIWorm scene (read in the code, b99ca5ab)

| item | value | where |
|---|---|---|
| field | C = -\|x_head - x_target\|, sim units, no physical unit | `worm_neural_network.py` `_get_concentration` |
| head point | MetaWorm vertex 102 (nose tip, s = 0.0004 at rest, measured) | `interact.cpp` GetHeadLocation, `worm.meta` |
| target | global (0, 0, 0); start (0.4365, -1.0677, -1.7486); heading (0, 0, 1) | `worm_in_env.py` defaults |
| food drawn | (1.8275, -0.0276, -0.3082), not the gradient target | `worm_in_env.py` `add_food` |
| target in the worm frame | 1.748 ahead, 0.408 ventral, 1.080 right; 2.095 units = 3.34 mm (derived) | Eigen 5.0.1 check |
| transducer | dC per control step, (dC - min) * 100 / (max - min) - 80 over the last 11 dC, then / 1000, clip [-0.08, 0.02] nA, NaN -> -0.08; one IClamp per neuron | `normalize_delta_concentration`, `_add_iclamp` |
| input neurons | AWAL/R, AWCL/R, ASKL/R, ALNL/R, PLML, PHAL/R, URYDL/DR/VL/VR (15, all the same current) | `worm_in_env.py` config |
| rates | neuron dt 5/3 ms; control (motion) step 100 ms in this file (100/3 ms in `Metaworm/interact/WormInEnv.py`) | both files |
| muscle out | soma voltages of 80 motor neurons averaged over the control step, (V @ wout + 80) / 100, clip [0, 0.8] | `motor_neuron_volt_to_muscle_sig` (fc mode) |
| plate, gravity, contact | none | `World.cpp` collision is a `// todo`; gravity commented out in `Worm.cpp` |

The rotation used to place the worm turns (0, 0, -1) onto (0, 0, 1). These are antiparallel, so Eigen chooses the
axis; Eigen 5.0.1 picks x. If upstream's Eigen 3 picked y, the target would sit dorsal and to the left instead of
ventral and to the right (the same 1.748 ahead); the distance (3.34 mm) is the same either way.

## Literature for the plate and the field

| quantity | value | units | source | read in paper |
|---|---|---|---|---|
| NGM NaCl | 51.3 (called 50) | mM | Brenner 1974 recipe (Stiernagle 2006 WormBook) | recipe only |
| NaCl plug assay | 9 cm plate, 2 mm agar, 5 mm plug of 100 mM NaCl, overnight | | Kunitomo and Iino 2013 Nat Commun | no (secondary) |
| linear NaCl gradient | 2 (= 0.2 mM/mm) | mM/cm | Luo et al. 2014 Neuron | no (secondary) |
| odour spot (2-nonanone) | 2 uL of 30% in ethanol, 9 cm plate | | Tanimoto et al. 2017 eLife, Methods | yes |
| odour field on the plate | 0.04 to 22.9, exponential decay with distance, measured by GC at 1-12 min | uM (gas) | Tanimoto et al. 2017 | yes |
| odour sensitivity | +-0.01 uM/s on a ~2 uM background | uM/s | Yamazoe-Umemoto et al. Nat Commun | no (secondary) |
| body density, 24 h adult | 1.074 (newly moulted adult 1.081, starved 1.054) | g/cm^3 | Reina et al. 2013 PLoS ONE | yes |
| agar drag, tangential | 3.2e-3 | kg/s | Boyle, Berri and Cohen 2012 (from Niebur and Erdos 1991) | yes (quoted) |
| agar drag, normal | 128e-3 (K = 40) | kg/s | Boyle, Berri and Cohen 2012 | yes (quoted) |
| agar K, other estimates | 30-40 (Fang-Yen 2010); 3-10 by direct drag (Rabets 2014); ~10 (Shen 2012) | 1 | | no (secondary) |
| liquid film holding the worm to agar | described (Gray and Lissmann 1964; Wallace 1968), no number found | | | no |
| Sibernetic agar | elastic cubes of 8 particles, 5-6 layers, bottom fixed; gravity on; no stiffness or friction number in the text | | Palyanov et al. 2018 Phil Trans R Soc B | yes |

Not found: a primary-text formula for the NaCl field on a plug plate, the diffusion coefficient of NaCl in agar, or
a measured diacetyl field. Pierce-Shimomura 1999 and Iino and Yoshida 2009 full texts could not be fetched.

## What the port uses (scene.py)

- Channel default `diacetyl_uM` (inferred: AWA's attractant, and AWA is in upstream's input set; the only measured
  plate field is for 2-nonanone, a repellent, so its numbers set the range, not the value). `nacl_mM` is the other
  preset (ASE; not in upstream's input set).
- `cone_published` (upstream's shape): diacetyl c_peak 2 uM (guessed; range 0.04-22.9 measured), slope 0.1 uM/mm
  (guessed; a worm at 0.1-0.2 mm/s then sees 0.01-0.02 uM/s, the reported threshold). NaCl: c_peak 100 mM and slope
  0.2 mM/mm (published protocol values, secondary).
- `exp_spot` (measured shape): decay length 10 mm diacetyl, 20 mm NaCl (guessed; the length was not read).
- Target placement `plate_projected` (the published target dropped into the plate plane): 2.87 mm from the nose at
  rest (measured on the rest mesh).
- Brain side: the transducer above is BAAIWorm's published one (a candidate toggle for the brain worker); our
  interface passes concentrations and the brain's own sensory models transduce them.
