# RNAddress Project Log

All timestamps use ISO 8601 with the local offset where available. Entries are labeled **PRE-SPECIFIED** or **POST-HOC**.

## 2026-08-26 — Project initialization — PRE-SPECIFIED

- Initialized the repository from the uploaded master specification.
- Preserved the required order: novelty and physical data audit before modeling.
- Central gate: reconstruct experimental `(parent, edit, mutant, parent outcome, mutant outcome)` tuples in at least N-zip and astrocyte SN-MPRA.
- No model was developed or fit.

## 2026-08-26 — Public data acquisition — PRE-SPECIFIED

- Acquired GSE173098 processed counts and the complete Mikl supplementary archive.
- Acquired all N-zip supplementary workbooks plus BioStudies metadata for E-MTAB-10902, E-MTAB-11572, and E-MTAB-11575.
- Acquired the GSE330741 processed-count archive, complete astrocyte supplementary workbook, and public analysis repository.
- Acquired the SRLE-seq supplementary archive, source repository, and HRA016642 public raw-file checksum list. The raw HRA archive is approximately tens of gigabytes and was not required for the first processed-data gate.
- Acquired the Arora/Taliaferro supplementary archive and identified GSE183192.

## 2026-08-26 — N-zip intervention discovery — PRE-SPECIFIED

- Source workbook contains 4,813 initial-library tiles after excluding its embedded header row.
- Mutagenesis table contains 6,266 constructs: 20 WT, 4,695 single-nucleotide substitutions, 783 2-nt windows, 313 5-nt windows, 179 10-nt windows, 106 deletions, 102 targeted mutations, and 68 scrambles.
- Sixteen WT parents have exhaustive single-nucleotide coverage. Their total assayed length is 1,565 nt, exactly matching `1,565 × 3 = 4,695` substitutions.
- All 6,266 mutagenesis constructs have a WT primary-neuron neurite/soma localization value in the source table.

## 2026-08-26 — External-outcome quarantine deviation — POST-HOC

- During workbook schema discovery, the first three rows of the astrocyte result sheet were printed before the external manifest was written. This exposed a few individual numeric result cells but no aggregate outcome distribution, ranking, threshold analysis, or model result.
- Mitigation: those values are prohibited from informing target thresholds, feature design, model selection, or evaluation policy. The complete source workbook is now hash-frozen, and subsequent pre-freeze inspection is limited to schema, sequence/edit identity, row counts, and missingness counts.
- This deviation must remain visible in the final report; the external evaluation can be outcome-blinded from this point forward but cannot be described as perfectly never-seen.

## 2026-08-26 — Novelty collision findings — PRE-SPECIFIED

- CRISPR-TO and PULR directly provide programmable RNA repositioning, but through trans-acting RNA-binding/motor systems rather than minimal cis-sequence rewriting.
- Saturation and random-mutagenesis assays (N-zip, mutREL-seq, Mikl, astrocyte SN-MPRA) experimentally identify causal localization nucleotides, but do not accept a requested destination and computationally select minimal edits on held-out parents.
- Nuclear-speckle work experimentally designs motif/splice-site combinations and is a serious sequence-engineering collision, but is not a general minimal-edit inverse framework benchmarked on held-out intervention landscapes.
- No comparable system found so far performs starting RNA + requested localization + protected properties → minimal edit, then evaluates ranked recommendations on independent exhaustive mutagenesis landscapes.

## 2026-08-26 — N-zip identity ambiguity correction — POST-HOC

- The mutagenesis outcome sheet omits the source tile identifier and contains two distinct `Cflar_2` parents under the same gene-level identity. Row-order assignment would recover all 4,695 designed SNVs but is not independently verifiable from the workbook.
- The central benchmark therefore excludes the duplicated identity entirely. Its truth-safe benchmark contains 4,395 exhaustive SNVs across 15 unambiguous parents (1,465 positions, three alternate alleles each); 300 SNVs are quarantined.
- This correction supersedes any implication above that all 16 design parents are safely usable as outcome-linked intervention tuples.

## 2026-08-26 — Model-development preregistration — PRE-SPECIFIED

- Retained the frozen 12-development/3-locked-parent N-zip split rather than replacing it after outcomes had already been reconstructed.
- Prespecified nested leave-one-parent-out model selection on the 12 development parents and one-time evaluation on the three locked parents.
- Fixed continuous inverse metrics, the exact random expectation, a development-only binary threshold rule, model families, Mikl ablations, parent-level inference and internal GO criteria in `reports/preregistration.md`.
- Astrocyte outcome files remain sealed. Only the frozen outcome-free feature artifact may be used to create candidate inputs.

## 2026-08-26 — Nested-tree runtime amendment — POST-HOC

- Stopped the first formal benchmark before it wrote any complete outer-parent result because 300-tree models in every inner grid fold projected beyond the stated CPU budget.
- Inner tree hyperparameter screening was reduced from an initially attempted 60-tree surrogate to 20 trees after the former still exceeded budget before a formal fold completed; selected outer-fold and final models retain 300 trees. No folds, feature sets, candidate hyperparameters, labels, metrics or selection rules changed.
- Full disclosure and timing rationale are recorded in `reports/preregistration_deviations.md`.
- A second pre-result stop capped only the exploratory joint N-zip+Mikl ablation at 100 trees with leaf size 10 and feature fraction 0.25; primary outer models remain at 300 trees.
- A third pre-result stop changed only compute-heavy inner selection to deterministic three-fold grouped validation and reduced the fixed diagnostic local boosting iterations to 100. Outer evaluation remains leave-one-parent-out.
- After timing one complete fold but before computing aggregate metrics, discarded that checkpoint and fixed all hyperparameters at preregistered grid centers. This removes inner tuning while preserving strict outer leave-one-parent-out evaluation; details are in `reports/preregistration_deviations.md`.

## 2026-08-26 — Development benchmark — PRE-SPECIFIED ANALYSIS

- Computed the development-only assay threshold as 0.675864 log2 localization units and retained continuous rank percentile and normalized regret as primary metrics.
- Completed strict outer leave-one-parent-out prediction for all 12 development parents. Pairwise ranking led development with macro rank percentile 0.636, versus 0.561 for retrieval and 0.521 for strong forward-model exhaustive search.
- Parent-bootstrap 95% intervals for the pairwise rank-percentile gain crossed zero versus both retrieval and forward search. Development was classified as promising, not confirmed.
- Mikl-only transfer was below random (0.456). Joint N-zip+Mikl training reached 0.572 but did not beat N-zip pairwise ranking, while a Mikl prior reduced the intervention forest result. Mikl was excluded from the selected primary model.
- No Astrocyte outcome was accessed.

## 2026-08-26 — Locked internal prediction freeze — PRE-SPECIFIED

- Fit the selected pairwise model using the 12 development parents and generated outcome-free predictions for 855 SNVs across the three untouched N-zip parents.
- Committed the prediction freeze before reveal at commit `46a78dec1a4f654c6b0ea3bcbcf11d301bd8e046`.
- Frozen prediction SHA-256: `3b1fb0d494052fa6001615c3cbc257ff627e3464454457c846ab6cb153d37ad8`.
- Frozen model SHA-256: `fbe9a46c6f8ca722382a6f35d2b0804d4e2ef47f49d869609ff70e1a17f5d337`.
- The calibrator used only cross-fitted development predictions and could not alter within-parent ranking.

## 2026-08-26 — One-time locked internal reveal — PRE-SPECIFIED ANALYSIS

- Verified the committed frozen-prediction hash before joining any locked N-zip outcome.
- Pairwise ranking achieved macro rank percentile 0.566 and normalized regret 0.480. It beat exact random rank percentile 0.500 and retrieval 0.279, but lost to strong forward-model exhaustive search at 0.624 with normalized regret 0.421.
- The preregistered internal gate therefore **FAILED**. The model was not changed after reveal.
- The external prediction freeze and external outcome reveal were not authorized. Astrocyte localization, expression, translation, and ribosome-occupancy outcomes remain sealed.

## 2026-08-26 — Post-lock hostile internal audit — POST-HOC

- Combined only truth-safe cross-fitted predictions across the 15 N-zip parents for descriptive diagnostics; this analysis cannot rescue the failed gate.
- Pairwise ranking had descriptive rank percentile 0.622, versus 0.542 for forward search, 0.612 for metadata-only, 0.594 for GC-only, and 0.528 after shuffling edit identities within parent.
- Sequence-cluster-held-out pairwise ranking scored 0.619. Closest-parent 3-mer cosine similarity ranged from 0.501 to 0.919, with no exact duplicate parent sequences.
- The custom pairwise objective is not established as necessary because it failed to beat the strong forward baseline on the untouched lock. No external or software-build phase was started.
