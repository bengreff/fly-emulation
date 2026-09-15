# State and next actions

Written at the end of session 1, 14 September 2026.

## Where things stand

The Pugliese connectome nerve-cord model reproduces cleanly and is wired into a
pipeline with provenance, tests and figures. Read `docs/FINDINGS.md` first; its
index gives the status of every claim, including one that was retracted and
corrected twice.

The short version: the connectome constrains **which neurons connect**. It does
not constrain **sign, strength or excitability**, and in this model all three are
conventions. Two of those conventions are demonstrably wrong (F10, F11) and a
third is load-bearing (F9).

## Do these first

1. **Re-run everything with the corrections on.** `--proprio-cholinergic` and
   `--size-norm class` are implemented. Correcting excitability alone leaves the
   published stimulus unable to drive the network, because the published
   operating point was calibrated with the artefact present, so the synaptic
   scale and stimulus amplitude need recalibrating together. The sweep in
   `scripts/run_corrected_model.sh` starts that.
2. **Constrain the glutamate sign with expression data.** Fly Cell Atlas
   single-cell transcriptomes; look for glutamate-gated chloride channel
   expression in nerve-cord motor and premotor neurons. Turns a convention into
   a prior with real uncertainty. Not attempted.
3. **Ask the neuPrint annotations directly about receptors and transmitters.**
   The token in `~/.config/flyemu/neuprint_token` reaches `manc`, `male-cns`,
   `hemibrain` and `optic-lobe`. Only the MANC motor-neuron and transmitter
   fields were used this session.

## Known gaps, stated plainly

- **No descending-stimulus amplitude sweep.** F7 has three of four knobs swept.
  The fourth was started and abandoned for capacity.
- **The shuffle null is not strict.** It preserves out-degree exactly but
  reassigns in-degree patterns within a class. A both-degree-preserving null
  should be run before F4 is quoted as a headline.
- **Phasic sensory drive is open loop.** Modulation is prescribed, not generated
  by a body, and all sensors share one waveform, optionally split into antiphase
  groups. Early replicates show no frequency restores the rhythm; this is not a
  substitute for a closed loop.
- **Transmitter resampling renormalises over three exposed classes.** The
  annotation table shows only acetylcholine, GABA and glutamate probabilities,
  which sum to about 0.98 on average and as little as 0.49. The missing mass is
  redistributed proportionally, which is an approximation.
- **No body was run.** `flygym` 2.1.0 was inspected, not simulated. Its mesh
  assets download on demand and were not fetched.
- **`docs/MILESTONE_A.md`** is the plan for the leg interface and is unchanged
  by the night's findings except that steps A1 and A3 now have a prerequisite:
  fix the afferent signs first.

## Practical notes

- Reproduce anything from `docs/RUNNING.md`. Every run writes a provenance JSON
  naming its scaffolds; read those before trusting any number.
- The PC (`backhouse`) has no internet. Its environment was built from wheels
  shipped over the Tailscale SSH link. Ship a script and run it with
  `ssh backhouse "wsl -d Ubuntu -- bash /mnt/c/flyemu/<x>.sh"`; inline bash
  quoting through its `cmd.exe` login shell is unreliable.
- Do not run more than two simulation sweeps at once on the laptop. Three
  oversubscribes ten cores and everything slows by roughly the factor you added.
- Long runs now write `metrics_partial.csv` per replicate, so a killed run keeps
  its results. `scripts/recover_from_logs.py` recovers older ones from logs.
