# Small-edit prediction results

**The strongest supported result is within-assay prediction of two-position SRLE swap effects. The stronger claim of useful small-edit prediction or selection for unseen parent genes is not supported by the new Mikl analysis.** Single-nucleotide generalization is not established.

This is one frozen exploratory analysis of already-exposed development data, not a replacement for any historical NO-GO gate. The protocol and all initial fitting/evaluation code were committed in **6e793d7 before fitting**. All ten inner selections chose delta 1–3-mer Ridge over the paired interaction representation. Each cell is fitted separately; outer genes, parents and exact alleles are held out, while biological contexts are seen. All <=6-base training examples are used, but every result is reported separately by size. There were no seed retries, architecture search, significance filtering, or new SRLE fits.

## Task A: quantitative localization change in held-out Mikl genes

Units are author-processed mutant-minus-WT log2(neurite/soma). RMSE and MAE are gene-balanced. The 95% intervals resample genes, condition on the fixed fitted models and splits, and omit refitting uncertainty. They do not restore independence from earlier source exposure.

| context | edit_size_band | rmse | rmse_ci_low | rmse_ci_high | mae | sign_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| CAD | 1 | 1.3037 | 0.5706 | 1.8622 | 0.8908 | 0.4848 |
| CAD | 2 | 0.8334 | 0.6989 | 0.9650 | 0.6105 | 0.5682 |
| CAD | 3 | 0.8336 | 0.7381 | 0.9293 | 0.5913 | 0.6831 |
| CAD | 4-6 | 0.8805 | 0.8255 | 0.9359 | 0.5774 | 0.6143 |
| Neuro-2a | 1 | 1.5561 | 0.6118 | 2.3001 | 1.0177 | 0.5758 |
| Neuro-2a | 2 | 0.8639 | 0.6331 | 1.1114 | 0.5398 | 0.6544 |
| Neuro-2a | 3 | 0.7533 | 0.6521 | 0.8572 | 0.4644 | 0.6559 |
| Neuro-2a | 4-6 | 0.7381 | 0.6824 | 0.7960 | 0.4619 | 0.6301 |

Strong simple comparisons (the complete results include every model, not just these):

| context | edit_size_band | delta_AU | no_change | primary | train_mean |
| --- | --- | --- | --- | --- | --- |
| CAD | 1 | 1.2760 | 1.1990 | 1.3037 | 1.2800 |
| CAD | 2 | 0.8240 | 0.8380 | 0.8334 | 0.8167 |
| CAD | 3 | 0.8270 | 0.8783 | 0.8336 | 0.8269 |
| CAD | 4-6 | 0.8754 | 0.8967 | 0.8805 | 0.8770 |
| Neuro-2a | 1 | 1.5183 | 1.4534 | 1.5561 | 1.5236 |
| Neuro-2a | 2 | 0.8605 | 0.8865 | 0.8639 | 0.8601 |
| Neuro-2a | 3 | 0.7535 | 0.7736 | 0.7533 | 0.7509 |
| Neuro-2a | 4-6 | 0.7335 | 0.7491 | 0.7381 | 0.7357 |

Global descriptive correlations and calibration of the selected prediction:

| context | edit_size_band | global_pearson_descriptive | global_spearman_descriptive | calibration_slope_descriptive |
| --- | --- | --- | --- | --- |
| CAD | 1 | -0.2896 | -0.3297 | -4.5711 |
| CAD | 2 | 0.0301 | 0.0090 | 0.2648 |
| CAD | 3 | 0.0072 | 0.0227 | 0.0519 |
| CAD | 4-6 | 0.0324 | 0.0513 | 0.2137 |
| Neuro-2a | 1 | -0.6048 | -0.4341 | -12.7096 |
| Neuro-2a | 2 | 0.1004 | 0.1273 | 1.1487 |
| Neuro-2a | 3 | 0.0225 | 0.0228 | 0.2199 |
| Neuro-2a | 4-6 | 0.0368 | 0.0556 | 0.2764 |

Paired gene-bootstrap MSE improvement over ΔAU (positive favors the selected model):

| context | edit_size_band | gain | ci_low | ci_high | eligible_genes |
| --- | --- | --- | --- | --- | --- |
| CAD | 1 | -0.0714 | -0.1558 | -0.0025 | 11 |
| CAD | 2 | -0.0155 | -0.0363 | 0.0051 | 72 |
| CAD | 3 | -0.0109 | -0.0297 | 0.0064 | 157 |
| CAD | 4-6 | -0.0089 | -0.0171 | -0.0004 | 189 |
| Neuro-2a | 1 | -0.1163 | -0.3125 | 0.0033 | 11 |
| Neuro-2a | 2 | -0.0059 | -0.0280 | 0.0140 | 72 |
| Neuro-2a | 3 | 0.0003 | -0.0091 | 0.0096 | 157 |
| Neuro-2a | 4-6 | -0.0068 | -0.0113 | -0.0029 | 189 |

The four-to-six-base model has near-zero effect correlation and is worse than ΔAU in both cells by paired MSE intervals. Small improvements over zero prediction are not sufficient evidence of useful sequence-specific intervention prediction; a training mean is competitive. One-base estimates rest on only 11 genes/13 variants per cell.

## Task B: direction prediction

Logistic predictions use a fixed 0.5 threshold and the regression-selected feature family. AUROC below is the mean within eligible genes containing both observed signs. It is different from pooled/global AUROC. In the one-base stratum **only one gene qualifies**, so values of 0 or 1 are not evidence of decisive generalization. Quantitative-model sign accuracy above and logistic probability accuracy below are different measures.

| context | edit_size_band | auroc | auroc_ci_low | auroc_ci_high | auroc_eligible_genes | balanced_accuracy | probability_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAD | 1 | 0.0000 | 0.0000 | 0.0000 | 1 | 0.5000 | 0.4848 |
| CAD | 2 | 0.5881 | 0.4071 | 0.7659 | 21 | 0.5000 | 0.5795 |
| CAD | 3 | 0.4664 | 0.3925 | 0.5460 | 81 | 0.4967 | 0.6829 |
| CAD | 4-6 | 0.5295 | 0.5055 | 0.5520 | 186 | 0.5180 | 0.6215 |
| Neuro-2a | 1 | 1.0000 | 1.0000 | 1.0000 | 1 | 0.5000 | 0.5758 |
| Neuro-2a | 2 | 0.3467 | 0.2222 | 0.4897 | 27 | 0.5000 | 0.6481 |
| Neuro-2a | 3 | 0.5095 | 0.4401 | 0.5822 | 92 | 0.5158 | 0.6579 |
| Neuro-2a | 4-6 | 0.5290 | 0.5081 | 0.5503 | 187 | 0.5153 | 0.6352 |

For four-to-six-base edits, balanced accuracy is approximately **0.518 CAD / 0.515 Neuro-2a**. Global gene-weighted AUROC is **0.541 / 0.544**, versus **0.549 / 0.558** for ΔAU. The primary quantitative sign accuracy of 0.614 / 0.630 is below training-mean sign accuracy of 0.626 / 0.635; exceeding 0.5 alone mostly reflects sign imbalance. Fixed-bin probability calibration, Brier scores and all paired intervals are exported. Near-constant control correlations can be numerically unstable and are not used as success evidence.

## Task C: choosing among measured candidate edits

Candidates are compared only within the same exact parent, cell and size band. The model ranks without the held-out outcome; evaluation subsequently compares those ranks with measurements. Both desired directions are retained. All metrics first average directions and parents within gene, then genes equally. Normalized regret is zero for a best observed choice and one for a worst choice. Averaged across both directions, uniform selection has exactly **0.5 expected regret**. The lexical tie policy of constant predictors is not a stochastic uniform policy.

| context | edit_size_band | eligible_genes | regret | regret_ci_low | regret_ci_high | correct_direction | wrong_direction | best_choice | within_parent_rank_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAD | 2 | 4 | 0.7500 | 0.2500 | 1.0000 | 0.5000 | 0.5000 | 0.2500 | -0.5000 |
| CAD | 3 | 23 | 0.5674 | 0.3696 | 0.7522 | 0.4478 | 0.5522 | 0.4326 | -0.1348 |
| CAD | 4-6 | 173 | 0.5040 | 0.4684 | 0.5426 | 0.5144 | 0.4842 | 0.4434 | -0.0053 |
| Neuro-2a | 2 | 4 | 0.5000 | 0.0000 | 1.0000 | 0.3750 | 0.6250 | 0.5000 | 0.0000 |
| Neuro-2a | 3 | 23 | 0.4854 | 0.2870 | 0.6783 | 0.4891 | 0.5109 | 0.5065 | 0.0239 |
| Neuro-2a | 4-6 | 173 | 0.5027 | 0.4649 | 0.5406 | 0.5112 | 0.4870 | 0.4427 | -0.0011 |

Paired comparison with ΔAU:

| context | edit_size_band | regret_gain | regret_gain_ci_low | regret_gain_ci_high | fraction_genes_improved |
| --- | --- | --- | --- | --- | --- |
| CAD | 2 | -0.2500 | -0.7500 | 0.2500 | 0.2500 |
| CAD | 3 | -0.0152 | -0.2326 | 0.2066 | 0.2174 |
| CAD | 4-6 | -0.0057 | -0.0515 | 0.0385 | 0.4335 |
| Neuro-2a | 2 | 0.2500 | -0.2500 | 0.7500 | 0.5000 |
| Neuro-2a | 3 | 0.0630 | -0.2130 | 0.3326 | 0.3478 |
| Neuro-2a | 4-6 | 0.0181 | -0.0236 | 0.0603 | 0.4104 |

No size/cell combination satisfies the frozen descriptive superiority criterion against all comparators. The largest cohorts have regret **0.504 / 0.503**, close to uniform, and wrong-direction choice rates of **48.4% / 48.7%**. There is no defensible general-purpose edit-selection demonstration here. No unchanged-parent/abstention option was added after observing outcomes. Top-three recovery is trivial when there are <=3 candidates; use the exported `top3_informative` metric for sets with >3. Two-base decisions have only four genes and cannot support breadth claims.

The complete candidate CSV contains every eligible parent sequence, measured candidate, exact coordinates, desired direction, predicted/measured rank, selected candidate and its direction success. Parent-level improvement fractions (descriptive; correlated within genes) and gene-level paired improvements are both exported. Failure plots retain all eligible parents rather than selected successes.

## Fixed secondary evidence: SRLE two-position swaps

The original SRLE aggregate/risk analyses replayed to floating-point precision, including all **9,472 original model/replicate/direction choices**. No SRLE fitting, new neighborhoods, new candidates or gate changes were performed. On the original 1,744 directed candidate links, differences of frozen short-mer scores predict measured mutant-minus-anchor log2 nuclear-retention changes:

| Metric | Replicate 1 | Replicate 2 |
| --- | --- | --- |
| Pearson r (95% composition-class bootstrap CI) | 0.609 [0.565, 0.649] | 0.597 [0.533, 0.664] |
| Spearman rho | 0.607 | 0.595 |
| MAE | 0.206 [0.188, 0.226] | 0.219 [0.199, 0.241] |
| RMSE | 0.272 [0.244, 0.301] | 0.294 [0.260, 0.328] |
| Composition/no-change RMSE | 0.344 | 0.366 |
| Sign accuracy | 0.731 [0.702, 0.760] | 0.703 [0.671, 0.733] |
| Score AUROC | 0.810 | 0.775 |

The positional-pair model is competitive (r **0.587 / 0.587**, RMSE **0.278 / 0.296**), but does not establish superiority over short k-mers. Composition-preserving swaps force composition-only change predictions to zero. This result demonstrates sequence-order information within the measured assay. It does not prove a new molecular mechanism or broad generalization.

Intervals resample 60 composition classes for row-weighted candidate-edge metrics; edges overlap and include reverse links. They are **not** confidence intervals across independent biological parents or independent experiments. Source training and these replicate measurements belong to the same reporter experiment. The original selected-choice risk remains: positional-pair choices were wrong in both replicates in **20.78% of decrease / 23.57% of increase** decisions, versus **25.13% / 22.11%** for k-mers (class-weighted). These selected-choice risks must not be confused with all-edge sign error. Full raw-to-author-Table-5 lineage is still partial.

## Fixed secondary evidence: SIRLOIN single-base edits

Only 223 finite variants from two parents can be scored. Frozen short-mer effect scores have Pearson r **0.072 / −0.077**, sign accuracy **0.498 / 0.453**, and score AUROC **0.484 / 0.421** in discovery replicates 1/2. Pair scores have r **0.124 / 0.006** and sign accuracy **0.529 / 0.466**. CCTCCC motif scores correlate **0.263 / 0.316**, but have many zero changes and do not establish a general model advantage. Existing selection-gate failure remains unchanged. Source log scores and target ratio changes are uncalibrated, so magnitude errors are deliberately not reported. Two parents do not support population bootstrap claims. This does not confirm single-base transfer.

## Interpretation and remaining research need

The new analysis tests the requested small-edit consequence directly. Its negative Mikl outcome is consistent with low paired-effect repeatability, limited independent single-base data, weak signal beyond composition, and unresolved parent/context interactions. These are explanations consistent with the evidence, not proven exclusive causes. Earlier positive broad Mikl direction summaries (including the historical approximately 0.705 value) used different significance-filtered/larger-edit and cell-aggregation estimands; they cannot be carried over to this unfiltered small-edit task.

Moffatt and TDP small subsets remain useful inventory resources, but their few independent genes, limited choice structure, prior exposure and frozen scope preclude treating them as new confirmation here. The next scientific advance needs a **new, independently admitted localization dataset with measured WT and multiple small mutants per independent parent, replicated paired outcomes, and compatible endpoint semantics**. Admission and evaluation rules must be fixed before reading its outcomes. Repeated fitting on the current evaluation data cannot provide that evidence.

## Figures and full outputs

- [01_predicted_vs_measured](../../results/small_edit_20260925/figures/01_predicted_vs_measured.png) ([SVG](../../results/small_edit_20260925/figures/01_predicted_vs_measured.svg))
- [02_performance_by_size](../../results/small_edit_20260925/figures/02_performance_by_size.png) ([SVG](../../results/small_edit_20260925/figures/02_performance_by_size.svg))
- [03_direction_prediction](../../results/small_edit_20260925/figures/03_direction_prediction.png) ([SVG](../../results/small_edit_20260925/figures/03_direction_prediction.svg))
- [04_selection_regret](../../results/small_edit_20260925/figures/04_selection_regret.png) ([SVG](../../results/small_edit_20260925/figures/04_selection_regret.svg))
- [05_all_baselines](../../results/small_edit_20260925/figures/05_all_baselines.png) ([SVG](../../results/small_edit_20260925/figures/05_all_baselines.svg))
- [06_per_parent_performance](../../results/small_edit_20260925/figures/06_per_parent_performance.png) ([SVG](../../results/small_edit_20260925/figures/06_per_parent_performance.svg))
- [07_failure_analysis](../../results/small_edit_20260925/figures/07_failure_analysis.png) ([SVG](../../results/small_edit_20260925/figures/07_failure_analysis.svg))

- [small_edit_predictions.csv](../../results/small_edit_20260925/small_edit_predictions.csv)
- [small_edit_candidate_selection.csv](../../results/small_edit_20260925/small_edit_candidate_selection.csv)
- [small_edit_secondary_predictions.csv](../../results/small_edit_20260925/small_edit_secondary_predictions.csv)
- [secondary_candidate_selection.csv](../../results/small_edit_20260925/secondary_candidate_selection.csv)
- [effect_direction_metrics.csv](../../results/small_edit_20260925/effect_direction_metrics.csv)
- [global_prediction_metrics.csv](../../results/small_edit_20260925/global_prediction_metrics.csv)
- [direction_calibration.csv](../../results/small_edit_20260925/direction_calibration.csv)
- [paired_prediction_comparisons.csv](../../results/small_edit_20260925/paired_prediction_comparisons.csv)
- [decision_metrics.csv](../../results/small_edit_20260925/decision_metrics.csv)
- [paired_decision_comparisons.csv](../../results/small_edit_20260925/paired_decision_comparisons.csv)
- [parent_context_comparisons.csv](../../results/small_edit_20260925/parent_context_comparisons.csv)
- [fold_performance.csv](../../results/small_edit_20260925/fold_performance.csv)
- [secondary_effect_direction_metrics.csv](../../results/small_edit_20260925/secondary_effect_direction_metrics.csv)
- [secondary_decision_metrics.csv](../../results/small_edit_20260925/secondary_decision_metrics.csv)
- [srle_direct_effect_intervals.csv](../../results/small_edit_20260925/srle_direct_effect_intervals.csv)
- [verification_receipt.json](../../results/small_edit_20260925/verification_receipt.json)

See [the frozen protocol](small_edit_prediction_protocol.md), [data inventory](small_edit_dataset_inventory.md), [final claim](small_edit_final_claim.md), and [reproduction instructions](reproduction.md). Nothing here changes prior failed gates or establishes novelty by itself.
