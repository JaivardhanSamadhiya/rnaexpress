# RNAddress v3.5R corrected exact-SNV benchmark audit

## Partial reconstructed cohort

The separately versioned table `data/processed/nzip_snv_intervention_pairs_v4_truth_corrected.csv.gz` contains 3,453 exact-SNV rows across 13 retained parents. It is a deterministic partial raw reconstruction, not a validated replacement benchmark because the protocol's publication-reproduction thresholds failed.

Starting from 4,695 designed exact SNVs:

- 3,453 have a coverage-valid mutant, coverage-valid WT, finite source-defined UMI ratio, and non-Cflar identity;
- 1,242 are excluded;
- all 300 Cflar_2 exact SNVs remain quarantined;
- 13 of 16 candidate parent landscapes retain at least one quantitative SNV;
- `Map2|5` is excluded: its WT has zero samples with at least 20 distinct UMIs;
- `Cox5b|6+7` is excluded: its WT has only two samples with at least 20 distinct UMIs;
- the third non-retained parent identity is the quarantined Cflar_2 landscape.

For the 4,395 historical truth-safe SNV rows, 3,453 remain in the partial cohort and 942 are removed. Every invalid mutant or WT produces `NA`, never a zero-derived delta.

## Historical numeric impact

All 3,453 retained deltas differ numerically beyond `1e-6` from the historical workbook-derived delta; 3,332 differ by more than `0.05`. Among 3,418 rows whose historical parent and mutant statistics were both finite, the corrected-versus-historical delta MAE is `0.406972` and the maximum absolute discrepancy is `9.349905`.

These differences exceed the prospective finite-value validation thresholds. The problem is broader than sentinel zeros and prevents this partial cohort from being declared a valid Phase 3.5 benchmark.

## Duplicate handling

There are six exact-sequence duplicate groups (12 design rows). Each group maps to one canonical outcome vector. No duplicate design ID becomes an independent experimental observation. The groups include convergent k-mer/mutation designs and one convergent SNV/multibase design; the latter still contributes at most one sequence measurement.

## Required next evidence

Reliable recovery would require at least one provenance-complete historical artifact from the authors: the six processed per-sequence count tables, the exact experiment `config.txt` plus counter invocation/version, or an equivalent intermediate that reproduces both 5,679 eligibility identities and finite workbook ratios.
