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
- **Names.** "Dandelion" and "DNg103" (FlyWire names) have no match in the male-cns type, instance or
  BANC cross-match columns, so they cannot be placed on the path yet.
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

## Next

Test whether the ascending class alone can reach MN9 if its first relay fires: drive LgAG2 only, with a
hunger-like presynaptic gain on LgAG2 output (bounded by the measured dopamine effect, which the agent
could not quantify), and read layer 2 and MN9. A pre-registered run, behind a switch.
