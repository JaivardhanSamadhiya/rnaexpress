# Exposed multi-assay admission

This new development study starts at `8ee17a1`. The failed GSE330741 zero-shot test is development knowledge and remains immutable. All admitted resources are exposed; none supplies independent confirmation. The new user request authorizes reuse of legitimate exposed localization measurements, not quarantined or reserved measurements. No new resource discovery occurs before the new gate passes.

| Resource | Status | Endpoint, mapping and role |
| --- | --- | --- |
| SRLE, DOI 10.34133/csbj.0107 | ADMIT_PRIMARY | 1,744 directed two-base swaps among 592 six-mer anchors in one MCF7 HBB reporter. Paired log2 nuclear/cytoplasmic NRS from two already-reconstructed replicates. One biological context; 592 anchors are not independent genes. Raw-to-published-table provenance remains partial. |
| GSE330741 astrocytes | ADMIT_PRIMARY | 3,984 exact SNPs from seven 190-nt parents/two genes. Author normalized SN-input/cortex-input coefficient, mutant minus exact WT. Fourteen paired biological pool labels, 11–14 positive CPM pairs per variant. Existing outcome mapping verified; exact author REML reconstruction incomplete. |
| GSE173098 Mikl | ADMIT_PRIMARY | Certified 150-nt biological inserts, exact motif-replacement parent lineage, CAD and Neuro-2a log2 neurite/soma mutant-minus-WT effects; three paired replicate deltas. Small-edit candidate cohort has 13,781 measurements, 2,417 parents/4,825 parent-cell decisions, 187 genes. Both cell lines held together when the study is withheld. |
| GSE334718 Moffatt random substitution | ADMIT_PRIMARY | Exact 260-nt parents; author WT-normalized log2 neurite enrichment in CAD, GFP/Firefly, four replicate labels. 6,749 small-substitution measurements in six parents/twelve reporter decisions. Repeated reporters are not independent studies. |
| GSE334718 other small-change families | ADMIT_SECONDARY | Sequence-certified SHAPE/shuffle and padded deletion/replacement designs remain inventoried. Operation and normalization differences make them inappropriate primary small-substitution training. No reinterpretation of padded deletions as laboratory SNPs. |
| SIRLOIN, DOI 10.15252/embj.2020106357 | ADMIT_SECONDARY | 227 exact single substitutions in two 109-nt parents; 223 finite discovery Rep1/2 effects. Nuclear/cytoplasmic **ratio** differences (the later corrected audit supersedes the original pilot's log2 label). Only existing certified discovery values are reused. Rep3/4 and NucLibB remain closed. Not primary training or gate evidence. |
| TDP43 GSE288185 localization | DEVELOPMENT_ONLY | Certified 260-nt parent/mutant localization differences; four source replicate labels, no pair uncertainty in admitted table. One mutant per exact parent: no within-parent candidate preference can be learned. Inventory only. No stability columns or EV5 access. |
| N-zip | PROVENANCE_INSUFFICIENT | Quarantined measurement lineage; not read or resurrected for sample count. |
| Arora / context2022 | NO_VALID_PARENT_MUTANT_MAPPING | Tiled/context alternatives do not establish the requested small-edit lineage. Reserved data stay closed. |
| Shukla | PROVENANCE_INSUFFICIENT | Unresolved raw/processed mapping and no admitted small-edit lineage. |
| SEERS | NO_VALID_PARENT_MUTANT_MAPPING | Random inserts lack a declared measured parent-mutant relationship. |
| Faraway | ENDPOINT_INCOMPATIBLE | Intron/barcode configurations are not admitted pure small RNA substitutions. |
| mutREL / Wen | PROVENANCE_INSUFFICIENT | Mutation-event or RNA-to-outcome semantics remain unresolved; no new outcome access. |
| External stability / TDP EV5 | ENDPOINT_INCOMPATIBLE | Stability is not localization; EV5 remains quarantined. |
| Nuclear-speckle exon pairs | EXCLUDE | Two previously documented one-mutant comparisons cannot establish within-parent candidate ranking. |

Primary candidates have 1–6 corresponding-coordinate substitutions and no physical indels. Larger interventions remain in the full exposed inventory counts, not the primary objective. Small substitution count does not guarantee a short span: record both. Candidate sets need at least two finite distinct-ID edits and nonzero outcome range. No effect-sign, significance or favorable-performance filtering is used.

Canonical provenance uses the immutable `results/small_edit_20260925/small_edit_pairs.csv.gz` (SHA-256 `b56d9ce9712776ba477fcb8231d7d431c0dce895c2ed1054f1a1767360e482fd`) and the newly frozen GSE330741 mapped table (`f31a38ec6d03de3317d7f0c1b1aaaf8586277e2512b9512c027606da8b6cc08a`). Existing source audits and manifests document the original official supplements and GEO files. No nearest-sequence parents are invented. Missing absolute WT/mutant measurements remain missing.

Positive direction is nucleus for SRLE/SIRLOIN, neurite for Mikl/Moffatt, and SN input for astrocytes. These are deliberately heterogeneous destinations, not one physical compartment. H1 tests a common ranking rule; H2 separately restricts training to the projection class. Gene names and exact matching alleles are co-grouped across all assays before splits. This does not prove paralog or all near-sequence independence. Same assay and repeated context measurements cannot masquerade as new studies.

Primary biological units: 187 Mikl genes, six Moffatt gene/sequence groups, two astrocyte genes, and one SRLE reporter. Components shared across sources are purged together. Numerical training weights first balance studies, then components, then parent/context candidate sets. Broad biological uncertainty is limited by four studies and the narrow non-Mikl contexts regardless of variant count.
