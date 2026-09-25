# Small-edit dataset inventory

The objective is prediction of measured localization change caused by a small sequence edit. This inventory covers all **admitted local paired intervention resources**, plus documented exclusions. It is not an exhaustive survey of all public data. Discovery of additional datasets remains blocked by the earlier automatic approval review; no restricted or unadmitted outcomes were opened.

Tier 1 is one corresponding-coordinate substitution; Tier 2 is two or three; Tier 3 is four to six. The table always separates 1, 2, 3, 4–6 and >6. A count of changed bases does not establish a short contiguous edit: coordinate span is recorded separately. Global minimum unit-cost Levenshtein distance and a deterministic optimal alignment are also recorded. For repetitive sequences, minimum alignment can shift bases and differ from experimentally aligned substitution count; it does not redefine the physical intervention. All admitted pairs here have equal-length sequences; alignment insertion/deletion operations are not necessarily laboratory insertions/deletions.

## Complete admitted counts

Distinct pairs count each parent–mutant relationship once; context measurements count repeated reporters/cells separately. SRLE counts directed measured candidate edges, including overlapping/reverse links. Its 592 anchor sequences are within one HBB reporter, not 592 independent genes. Dataset parent/gene counts overlap between size rows and must not be summed.

| dataset | edit_size_band | distinct_parent_mutant_pairs | unique_parents | unique_genes | contexts | variant_context_measurements |
| --- | --- | --- | --- | --- | --- | --- |
| mikl_gse173098 | 1 | 13 | 13 | 11 | 2 | 26 |
| mikl_gse173098 | 2 | 148 | 144 | 73 | 2 | 296 |
| mikl_gse173098 | 3 | 667 | 636 | 161 | 2 | 1334 |
| mikl_gse173098 | 4-6 | 8972 | 5052 | 221 | 2 | 17944 |
| mikl_gse173098 | >6 | 2100 | 1628 | 183 | 2 | 4200 |
| moffatt_gse334718 | 1 | 7 | 2 | 2 | 3 | 13 |
| moffatt_gse334718 | 2 | 313 | 6 | 6 | 7 | 522 |
| moffatt_gse334718 | 3 | 968 | 7 | 7 | 7 | 1522 |
| moffatt_gse334718 | 4-6 | 7756 | 8 | 8 | 9 | 12054 |
| moffatt_gse334718 | >6 | 37248 | 10 | 10 | 10 | 50920 |
| sirloin | 1 | 227 | 2 | 2 | 1 | 227 |
| srle | 2 | 1744 | 592 | 1 | 1 | 1744 |
| tdp43_gse288185 | 4-6 | 2086 | 2086 | 16 | 1 | 2086 |
| tdp43_gse288185 | >6 | 2480 | 2480 | 15 | 1 | 2480 |

## Measurement and exposure

- **Mikl GSE173098:** certified parent/test-insert pairs; author-processed mutant-minus-matched-WT log2(neurite/soma), measured in CAD and Neuro-2a. Three raw paired replicate deltas support diagnostics, but are not identical to the processed effect estimator. Absolute parent/mutant measurements absent from the common table remain missing; zero is not an imputed WT measurement. Full inventory has 11,900 variants across 224 genes. New fits use only the already-certified Phase-B fold cohort: per cell, **13 / 147 / 663 / 8,896** examples for 1 / 2 / 3 / 4–6 substitutions, representing **11 / 72 / 157 / 189 genes**. This is 19,438 held-out cell measurements, 9,719 distinct pairs. Outcomes and prior broad results were already exposed; nested grouping prevents current fit leakage but cannot make the source pristine confirmation.
- **Moffatt GSE334718:** author reference-normalized localization effects, with source-specific reporter/cell contexts and uncertainty fields. Absolute parent measurements are unavailable in the certified common table. Thousands of variants arise from only 2–8 parents/genes in the small-edit strata. WT-omitted sufficiency controls and source operation classes remain identified. Already development-exposed; inventory only in this frozen study, not an independent validation cohort.
- **TDP43 GSE288185 localization only:** 2,086 four-to-six-base paired substitutions from 16 genes, one mutant per exact parent and no candidate-choice groups. Paired localization effects are available, but replicate uncertainty is absent in this table. No stability data were accessed. Previously development-exposed; inventory only in this study.
- **SIRLOIN:** 227 original single-base variants from **two** parents. Only 223 have finite discovery-replicate 1/2 measurements; four missing rows remain in inventory and are not fabricated or fitted. Workbook headers identify nuclear/cytoplasmic **ratios**, not log2 ratios. WT subtraction is on that ratio scale. Frozen SRLE model differences are on a log-score scale, so correlation/ranking/sign are reported; MAE/RMSE would be uncalibrated and are omitted. No reserved replicate outcomes, target fitting, or recalibration were used.
- **SRLE:** the original 1,744 composition-preserving two-position swaps among 592 candidate anchors and 60 composition classes, within a single HBB reporter experiment. All endpoints come from the previously frozen evaluated roster; this is not every possible pairing among all 4,096 measured six-mers. Target is mutant-minus-anchor log2 nuclear-retention score. Two previously reconstructed raw replicates are scored separately; the source aggregate uses the same experiment. Exact sequence holdout does not establish independent parent or context holdout. Full raw-to-author-Table-5 provenance remains **PARTIAL**, as documented in the prior provenance report; exact table/prediction mapping and saved replicate arithmetic are verified.

## Data sufficiency and localization of edits

| dataset | edit_size_band | variants_per_parent_min | variants_per_parent_median | variants_per_parent_max | parent_contexts_with_2_candidates | span_le6_measurements |
| --- | --- | --- | --- | --- | --- | --- |
| mikl_gse173098 | 1 | 1 | 1.0000 | 1 | 0 | 26 |
| mikl_gse173098 | 2 | 1 | 1.0000 | 2 | 8 | 292 |
| mikl_gse173098 | 3 | 1 | 1.0000 | 3 | 60 | 1210 |
| mikl_gse173098 | 4-6 | 1 | 1.0000 | 10 | 4390 | 9416 |
| mikl_gse173098 | >6 | 1 | 1.0000 | 6 | 672 | 0 |
| moffatt_gse334718 | 1 | 1 | 3.5000 | 6 | 2 | 13 |
| moffatt_gse334718 | 2 | 39 | 52.5000 | 71 | 21 | 511 |
| moffatt_gse334718 | 3 | 1 | 172.0000 | 250 | 21 | 1517 |
| moffatt_gse334718 | 4-6 | 1 | 1138.5000 | 1626 | 34 | 9691 |
| moffatt_gse334718 | >6 | 33 | 3129.5000 | 9252 | 53 | 0 |
| sirloin | 1 | 65 | 113.5000 | 162 | 2 | 227 |
| srle | 2 | 2 | 3.0000 | 7 | 592 | 1744 |
| tdp43_gse288185 | 4-6 | 1 | 1.0000 | 1 | 0 | 2086 |
| tdp43_gse288185 | >6 | 1 | 1.0000 | 1 | 0 | 0 |

For Mikl, only 9,416 of 17,944 full-inventory four-to-six-base context measurements span <=6 positions. Thus the Mikl category is **four to six changed bases**, not uniformly a localized six-base edit. The model cohort is a subset of this inventory. After its fixed nonzero-range choice eligibility, it supplies no one-base choice sets; two-base choice has only four genes; three-base choice has 23 genes; four-to-six-base choice has 173 genes (2,176 CAD and 2,175 Neuro-2a parents).

The full sufficiency table reports effect variance, finite sample counts, parent structure, replicate information, and measurable-effect diagnostics for each source/context/tier. Mikl raw paired-effect repeatability is weak in the largest small-edit stratum: replicate Pearson averages **0.168 CAD / 0.122 Neuro-2a**; approximately **5.64% / 6.30%** of raw three-replicate paired t intervals exclude zero. These are diagnostics of raw paired deltas, not confidence intervals on author-processed effects, a proven prediction ceiling, or a filtering criterion. SRLE paired-swap effect replicate correlation is **0.744**. Where replicate uncertainty is unavailable, the clearly-measurable fraction is unknown, not zero.

[small_edit_data_sufficiency.csv](../../results/small_edit_20260925/small_edit_data_sufficiency.csv) supplies all 50 context/tier rows, including variance and replicate diagnostics. [minimum_distance_counts.csv](../../results/small_edit_20260925/minimum_distance_counts.csv) reports minimum-alignment distance counts separately.

## Exclusions and protected resources

N-zip remains quarantined; Astrocyte remains sealed; TDP EV5 stability remains forbidden. mutREL mutation-event semantics and Wen RNA/outcome mapping are unadmitted. Arora, context2022 and Shukla tiled alternatives do not supply an admitted small-mutant/reference lineage (Shukla also has unresolved raw/processed mapping). SEERS random inserts lack declared parent-mutant relationships; Faraway intron/barcode configurations are not admitted small RNA substitutions. External stability has the wrong endpoint and failed admission. No nearest-sequence parents were invented, no reserved outcome schemas were inspected, and none of these sources is silently counted as independent confirmation.

## Machine-readable deliverables

[small_edit_pairs.csv.gz](../../results/small_edit_20260925/small_edit_pairs.csv.gz); [small_edit_size_counts.csv](../../results/small_edit_20260925/small_edit_size_counts.csv); [inventory_receipt.json](../../results/small_edit_20260925/inventory_receipt.json); [mikl_existing_fold_eligible.csv.gz](../../results/small_edit_20260925/mikl_existing_fold_eligible.csv.gz).

The pair inventory includes exact sequences, coordinate edits, alignment operations, size/span, localization change, measured parent/mutant values when available, reference semantics, replicate data, context, provenance, exposure and eligibility. Missing absolute measurements remain missing. Input SHA-256 hashes are pinned in the receipt.
