# S12: the tarsal PER pathway in real flies, and where it sits in the model

Question (F-TASTE-LEG-1 next experiment, 5 Oct 04:31): which cells carry leg sugar to the SEZ in real
flies, and is any of them identified in male-cns on the model's path to MN9?

Method: one Sonnet Explore agent (web search and fetch, about 2 min), then a structural cross-check in
the model connectome by me. The agent's quotes went through a fetch-and-summarise pass and were not
re-read by eye, so every literature item below is **secondary**. Items the agent saw only as abstracts or
search snippets are marked so.

## Literature (secondary)

1. **Two classes of tarsal sweet GRN.** Thoma et al. 2016, *Nat Commun* 7:10678,
   doi:10.1038/ncomms10678 (PMC4762887; agent read the full text). Most tarsal sweet GRNs end in their
   own thoracic neuromere (segmental, "stGRNs"); "a few additional GRNs in the fifth tarsal segment of
   *Gr64f-GAL4* project directly to the GNG through the cervical connective" (ascending, "atGRNs").
   Counts per leg: 9-10 segmental against 2-4 ascending. Function: segmental cells drive sugar-dependent
   slowing of locomotion; ascending cells drive feeding initiation (PER).
2. **Second-order cells named in the taste connectome.** Tastekin et al., bioRxiv
   10.1101/2025.08.25.671814 (Cell 2026; agent fetched the full text): "LgLG4 also has Dandelion as a
   relevant second-order neuron, and it shares other appetitive outputs, like DNg103, with other GRN
   types." Search snippet only, not found in the fetched text: LgLG4 "reaches high connectivity in a few
   hops with every motor neuron of the feeding sequence including MN9". No firing or calcium data for
   any second-order leg taste cell (structural study).
3. **Taste projection neurons.** Kim, Kirkhart & Scott 2017, *eLife* 6:e23386 (abstract level): three
   classes of sweet- or bitter-selective SEZ projection neurons postsynaptic to GRNs. Not confirmed to
   carry leg input.
4. **Hunger.** Marella, Mann & Scott 2012, *Neuron* 73:941 and Inagaki et al. 2012, *Cell* 148:583
   (summary level only; Marella full text blocked): in hungry flies dopamine raises sweet GRN presynaptic
   calcium (not spike rate) and lowers the sucrose threshold for PER. This acts at the GRN terminal.
5. **Not found:** a tarsal PER probability at 100 mM sucrose in starved flies from a primary source; any
   firing rate of a second-order leg taste neuron to tarsal sugar; whether the labellum is needed (one
   unsourced snippet suggests leg stimulation alone spreads the labella).

6. **Dandelion is AN13B002** (Tastekin et al. v2 full text, fetched by me 5 Oct 04:58 through a
   fetch-and-summarise pass; secondary): "A key downstream partner of WG2 is Dandelion, an AN typed as
   AN13B002 in the male CNS and as AN_GNG_68 in FAFB – FlyWire [47]. Given that Dandelion is also a key
   downstream neuron of LB3b GRNs in the labellum ... we propose that the WG2 GRNs are likely to detect
   sugar and trigger feeding." And: "Similar to WG2, LgLG3 GRNs have Dandelion as one of their top
   downstream partners. We therefore propose that it is likely to express sugar GRs, especially Gr5a".
   These are the authors' proposals from wiring, not measured responses. The fetched text gives no
   transmitter for Dandelion and no LgLG4 → MN9 path analysis; the "sensorimotor arc ... through
   multiple positive feedforward loops" wording appears only in a search summary.

## Cross-check in the model connectome (derived; male-cns, `data/cache`, 5 Oct 04:38)

- **The two classes are in male-cns.** LgAG2 (11 cells, superclass `sensory_ascending`) and LgLG4
  (43 cells, `vnc_sensory`). Leg by dominant neuropil: LgAG2 1-3 per leg (rf 3, lf 2, lm 2, rm 2, lh 1,
  rh 1); LgLG4 5-9 per leg. Matching LgAG2 to Thoma's ascending class and LgLG4 to the segmental class
  is **inferred** (both sugar lines by projection; LgAG2 ascends). LgAG2 count is at or below the low
  end of Thoma's 2-4 per leg; LgLG4 below their 9-10.
- **Output split.** LgAG2 put 37-62% of output synapses onto central-brain intrinsic cells and
  descending neurons; LgLG4 put 0% onto central-brain intrinsic cells and 0-23% onto descending neurons
  (the rest onto VNC and ascending cells). The ascending class is the one with direct brain access, as
  Thoma describe.
- **LgAG2's brain partners** (by synapses: GNG266 666, SLP237 493, GNG353 292, GNG564 252, PRW072 114,
  GNG147 103, GNG195 84, PRW046 79, GNG141 70) are 2-4 hops from MN9_L at 5 synapses per edge.
- **Names.** Dandelion is AN13B002 (item 6): 2 cells, predicted GABAergic (male-cns type prediction,
  confidence 0.89), so the model treats it as inhibitory. It is a layer-1 cell on the model's leg sugar
  path and fires at 10-30 Hz in the injection and patch runs. LgLG3 (162 cells, 23-31 per leg, all
  `vnc_sensory`) sends it 8770 of 58495 output synapses; LgLG4 298; LgAG2 none. The model gives LgLG3
  the unmatched weight 0.2. "DNg103" has no male-cns label match.
- **Activity** (seed 12 runs, `runs/s12/legsugar/run_inj_all_s12.npz`): with all 54 leg sugar GRNs
  injected at their 1 M drive, every LgAG2 fires at 36.7 Hz. Of its 39 central-brain partners, 4 fire
  (GNG353 17 Hz, GNG141 17 Hz, two GNG266 at 20 Hz). Most others peak at 0.4-0.96 of the way to
  threshold (SLP237 0.59-0.76, GNG564 0.88-0.90, GNG266 0.83-0.96, GNG147 0.37-0.58). In the 1 M
  patch run only 3 LgAG2 fire (lm and lh legs; 23-33 Hz), and none of their brain partners do.

## Reading

The literature puts tarsal PER on the ascending GRNs, which reach the GNG directly. The model has them
(LgAG2) and they reach GNG cells at one synapse. Four of those cells fire and most of the rest sit just
below threshold, but nothing downstream of them reaches MN9. The forelegs, which carry 5 of the 11 LgAG2, do not touch the patch in
the lying posture. Hunger in real flies acts at the GRN terminal (presynaptic gain), which the model
applies only to the labellar sugar GRNs. A presynaptic hunger gain on LgAG2 is a sourced candidate, but
it would have to carry the signal past layer 2 as well, where leg input is 1-2% of the synapses.

## Next (as written 04:39; done)

The LgAG2 presynaptic gain test was run as a diagnostic (DECISIONS 04:40): MN9_L 3 Hz at ×10 under m2,
0 Hz under m9r. Disinhibition also failed (DECISIONS 04:50). See F-TASTE-LEG-1.

## Added 05:02: LgLG3 included (diagnostic, DECISIONS 04:59)

Driving LgLG3 + LgLG4 + LgAG2 (216 cells) at 100 Hz open loop: Dandelion fires at 310-320 Hz under m2;
MN9_L stays at 0 Hz under m2 and m9r. In the model Dandelion is inhibitory (male-cns GABA prediction).
Its transmitter is the most discriminating missing fact for this pathway.

## Transmitter evidence for Dandelion (05:04, local metadata lookup)

- Predicted: male-cns GABA (type-level confidence 0.89); BANC GABA (score 0.968 left, 0.956 right).
- BANC `neurotransmitter_verified` = gaba for both cells. The basis is undocumented locally; the column
  covers 65,486 of 188,508 BANC cells and gives gaba for 431 of 440 hemilineage-13B cells, and both
  AN13B002 cells are hemilineage 13B. So it is probably a lineage-level assignment (inferred).
- Measured for this cell type: none found. BANC cross-matches the left cell to FlyWire AN_GNG_68 and the
  right to AN_GNG_193.

## Transmitter evidence for Dandelion, tonight (5 October 21:31)

Sources: one Sonnet Explore agent (web search and fetch; eLife and PMC were blocked, so Lacin 2019 was seen
only through search snippets and the Tastekin v2 PDF's restatement), then the curated ground-truth table
read by me: `flyconnectome/drosophila_neurotransmitters` `gt_data.csv` at commit a9417412 (pinned copy in
`data/raw/drosophila_neurotransmitters/`, with `COMMIT` and `README.md`). That table feeds BANC's
`neurotransmitter_verified` column (repository README, read by the agent).

- **Row for this cell type (read by me):** `adult_drosophila_melanogaster, ventral_nerve_cord, 13B, AN13B002,
  Lacin et al., 2019, FISH, confidence 3, gaba 1, acetylcholine 0`. The table's scale (README): 3 =
  "identification of RNA transcripts related to transmitter expression"; 5 = "evidence for protein
  expression in the given cell type, cell type specific labelling". 96 of the 98 rows that mention 13B cite
  Lacin et al. 2019, FISH, confidence 3, so the row is the hemilineage result applied to the type.
- **Lacin et al. 2019** (eLife 8:e43701; search snippets only, method and stage unverified): "Both the 13A
  and 13B clusters were marked with GABA, but not ChAT ... Both the 13A and 13B hemilineages are
  GABAergic." Restated in Tastekin v2: "All neurons within a hemilineage use the same neurotransmitter."
- **Cell-type-specific measurement:** none found (no driver line, immunostaining, FISH or physiology for
  Dandelion, AN_GNG_68 or AN_GNG_193). Eckstein et al. 2024 ground truth: not found to include it.
- **Labels.** Measured: GABA transcripts in hemilineage 13B (FISH, Lacin 2019; the table's confidence 3).
  Inferred for Dandelion: GABA, by hemilineage membership. Predicted: GABA by the male-cns (0.89) and
  BANC (0.96-0.97) EM classifiers. These are not fully independent: the classifiers were trained on
  ground truth of this kind. BANC's 440 hemilineage-13B cells: 431 labelled gaba, 9 with no verified
  label (none with a different transmitter; checked 21:33).

### Experiment that would settle it (for Ben's list)

A split-GAL4 line that labels AN13B002 / AN_GNG_68 (search the Janelia VNC and SEZ split collections by
the FlyWire and MANC names), then either (a) anti-GABA or anti-GAD1 immunostaining of the labelled cell
in the adult VNC and GNG, or (b) an intersection with transmitter-specific T2A reporters (Gad1, ChAT,
VGlut). Protein in this cell type would score 5 on the table's scale. A functional check would be to
stimulate the cell optogenetically while recording a downstream partner (GNG297 or AN09B004), with and
without picrotoxin.

### Consequence in the model (bracket, 5 October 21:56; DECISIONS 21:30)

Running Dandelion as acetylcholine instead of GABA leaves MN9_L at 0 Hz under leg sugar (m2 and m9r),
changes labellar sugar MN9_L by +5% (m2) and −25% (m9r), and leaves sugar + bitter at 0 Hz. The sign
changes the activity of 537-782 VNC cells downstream of Dandelion but not PER. Neither sign adopted.

## The paper's route read by eye, and feedforward inhibition at Bract 2 (5 October 22:04-22:45; DECISIONS 22:04)

Item 2 and item 6 above said the fetched text had no LgLG4 → MN9 path. The PDF (v2, `data/raw/tastekin2025/`,
read by me, Figure 9B and p. 20) has it: LgLG4 → AN01B004 → Bract I and Bract II → Roundup → MN9, with
AN01B004 → S&S → Roundup and S&S → MN9 alongside, described as "multiple positive feedforward loops", 7 hops to
maximum effective connectivity against about 5 for most labellar GRNs.

- In male-cns (measured annotation, `synonyms`): Bract 1 = DNge174, Bract 2 = DNge173, Roundup = GNG108. S&S is
  GNG159 by its edges (inferred). The type-summed weights match the figure (derived; LgLG4 → AN01B004 960
  against about 925). The model has the paper's route.
- In the model the route stops at Bract 2: AN01B004 fires, Bract 2 gets almost as much inhibition as excitation,
  from GNG093 and GNG250 (GABA predicted, not measured), which AN01B004 itself drives.
- Silencing those 4 cells (diagnostic) lifts Bract 2 to 10-25 Hz. MN9_L reaches 8 Hz mean under m2 only with
  LgLG3 added (216 GRNs); with the 54 matched sugar GRNs it reaches 1 Hz, and under m9r Roundup stays at
  0-1.3 Hz. Two blocks, both in guessed or fitted values rather than in the wiring.

Facts that would settle it: whether GNG093 and GNG250 are inhibitory in the animal (transmitter evidence as for
Dandelion), whether LgLG3 senses sugar (calcium imaging of LgLG3 GRNs to sucrose), and a recording of Bract 2 or
Roundup under tarsal sugar. The last is the held-out test for any fix.
