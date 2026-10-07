# Local ensemble-accessibility route: benchmark and prespecified design

This branch is prepared independently after the five-track generalization generation. Only synthetic feature tests and timing were run; no supervised fit or full-core comparative feature analysis was performed.

The 11 added features measure mutant-minus-parent differences in mean/min/max changed-site unpaired marginals; mean unpaired probability in the union of changed-site ±10-nt neighborhoods; changed-site pairing-partner entropy (including the unpaired state); expected pairing distance normalized by input length; accessibility-weighted A/G nucleotide content; AG and GA dinucleotide densities; and CCTCCC motif density and maximum accessibility. Motif weights average constituent unpaired marginals. They are not joint motif-opening or RBP-binding probabilities.

ViennaRNA2.7.2 uses the global equilibrium ensemble, explicit Turner2004 parameters, 37°C, dangles2, canonical GU pairing enabled, minimum loop3, linear RNA, salt1.021M, and unrestricted base-pair span within the exact supplied sequence. One fixed ±10-nt neighborhood is used; no temperature/window/layer search is allowed. The future ranker preserves the historical246 features and appends these11; candidate pair-RMS scaling and three L2 penalties(.005/.05/.5) use source-only nested selection.

Mikl, Astrocyte, and Moffatt inputs are exact admitted inserts. SRLE uses the certified20+6+20-nt local construction template from the reporter metadata certificate. This is not a complete mature HBB reconstruction. All contexts are truncated to available boundaries without padding. Unknown backbone, splicing, cellular RBP binding, and cotranscriptional folding can make predicted insert ensembles differ from the physical RNA. No claim is made that these RNAs fold alone in cells.

Independent synthetic QA checks the unpaired marginal against a constrained partition-function ratio, including a nucleotide represented only in the upper-triangle column of ViennaRNA's base-pair matrix. Other tests check complete motif/accessibility normalization, no-edit zeros, edit reversal, the certified SRLE coordinate shift, and invalid inputs.

Four tests passed. Forty synthetic alleles(ten per length46/150/190/260) were folded at fixed settings. The sequence-only inventory contains 18,220 unique encoded alleles. Median-based serial folding estimate: 78.18 minutes; sample-maximum-based estimate: 85.95 minutes. These are estimates from a small synthetic sample, excluding Python feature aggregation, disk/cache overhead, and contention.

| Input length | Unique core alleles | Synthetic median seconds/allele |
|---:|---:|---:|
| 46 | 742 | 0.02873 |
| 150 | 9,318 | 0.16172 |
| 190 | 3,991 | 0.25523 |
| 260 | 4,169 | 0.51430 |

The configuration was saved before tests and timing. Code/runtime/configuration/context hashes are recorded in the receipt. Full-core feature construction and supervised comparisons require the root's subsequent freeze/start instruction. No new data or paid resource was used; all prior frozen inputs remained unchanged.

Primary grounding: [Sequence, Structure, and Context Preferences of Human RNA Binding Proteins](https://pmc.ncbi.nlm.nih.gov/articles/PMC6062212/); [ViennaRNA official repository](https://github.com/ViennaRNA/ViennaRNA); [free-use copyright terms](https://raw.githubusercontent.com/ViennaRNA/ViennaRNA/master/COPYING). Predicted accessibility is a computational hypothesis whose transfer value must be tested against the same baseline and controls.
