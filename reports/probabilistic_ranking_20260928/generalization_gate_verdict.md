# Frozen generalization gate: NO-GO

**NO-GO: no primary probabilistic supervision method passed the frozen decision gate.** Selected method: **NONE**.

| assays_harmed_vs_H0 | assays_helped_vs_H0 | calibration_claim_gate_passes | composite | gain_ci_high | gain_ci_low | macro_gain_vs_H0 | macro_gain_vs_simple | macro_regret | median_gain_vs_H0 | model | passes_decision_checks | passes_primary_gate | primary_selection_eligible | worst_harm_vs_H0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 1 | False | 0.67692 | 0.01352 | -0.02257 | -0.01483 | -0.00619 | 0.50306 | -0.01725 | P1 | False | False | True | 0.03769 |
| 3 | 1 | False | 0.67951 | 0.00885 | -0.02439 | -0.01749 | -0.00885 | 0.50572 | -0.02243 | P2 | False | False | True | 0.03769 |
| 2 | 2 | False | 0.64943 | 0.02185 | -0.00595 | -0.00120 | 0.00744 | 0.48942 | -0.00022 | P3 | False | False | True | 0.04402 |
| 2 | 2 | False | 0.64632 | 0.01851 | -0.01510 | -0.00749 | 0.00115 | 0.49572 | -0.00806 | Hraw | False | False | False | 0.04192 |
| 3 | 1 | False | 0.67968 | 0.00687 | -0.02458 | -0.01811 | -0.00947 | 0.50634 | -0.02207 | P2_weighted | False | False | False | 0.03903 |
| 3 | 1 | False | 0.64652 | 0.01914 | -0.01923 | -0.00856 | 0.00008 | 0.49678 | -0.01455 | Partial | False | False | False | 0.04267 |
| 1 | 3 | False | 0.67568 | 0.01612 | -0.01469 | -0.00766 | 0.00098 | 0.49588 | 0.00545 | H0_pairfree | False | False | False | 0.04889 |
| 2 | 2 | False | 0.65203 | 0.01856 | -0.01355 | -0.00726 | 0.00138 | 0.49548 | -0.00346 | P2_pairfree | False | False | False | 0.03520 |
| 2 | 2 | False | 0.62384 | 0.02795 | 0.00400 | 0.00608 | 0.01472 | 0.48215 | 0.00169 | P3_hetero | False | False | False | 0.03536 |

## Every failed condition

| model | primary | failed_checks |
| --- | --- | --- |
| P1 | True | Mikl_SRLE_harm_at_most_0_01_vs_both; descriptive_bootstrap_lower_at_least_minus_0_01; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; no_assay_over_60pct_positive_gain; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| P2 | True | Mikl_SRLE_harm_at_most_0_01_vs_both; descriptive_bootstrap_lower_at_least_minus_0_01; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; no_assay_over_60pct_positive_gain; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| P3 | True | Mikl_SRLE_harm_at_most_0_01_vs_both; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; no_assay_over_60pct_positive_gain; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| Hraw | False | Mikl_SRLE_harm_at_most_0_01_vs_both; descriptive_bootstrap_lower_at_least_minus_0_01; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| P2_weighted | False | Mikl_SRLE_harm_at_most_0_01_vs_both; descriptive_bootstrap_lower_at_least_minus_0_01; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; no_assay_over_60pct_positive_gain; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| Partial | False | Mikl_SRLE_harm_at_most_0_01_vs_both; descriptive_bootstrap_lower_at_least_minus_0_01; each_avoidable_harm_at_most_0_05_vs_both; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| H0_pairfree | False | Mikl_SRLE_harm_at_most_0_01_vs_both; descriptive_bootstrap_lower_at_least_minus_0_01; each_avoidable_harm_at_most_0_05_vs_both; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; no_assay_over_60pct_positive_gain; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| P2_pairfree | False | Mikl_SRLE_harm_at_most_0_01_vs_both; descriptive_bootstrap_lower_at_least_minus_0_01; leave_best_assay_out_positive; macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |
| P3_hetero | False | macro_gain_vs_simple_at_least_0_02; macro_regret_at_most_0_468; three_assays_gain_vs_H0_at_least_0_01; three_assays_gain_vs_simple_at_least_0_02 |

## Per-assay gains and harms

| model | dataset | regret | avoidable_wrong | simple_baseline | gain_vs_simple | gain_vs_H0 | avoidable_harm_vs_simple | avoidable_harm_vs_H0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | astrocyte_gse330741 | 0.50756 | 0.50000 | uniform | -0.00756 | -0.03769 | 0.00000 | 0.00000 |
| P1 | mikl_gse173098 | 0.50433 | 0.19503 | composition | -0.01686 | 0.01285 | 0.01089 | -0.00309 |
| P1 | moffatt_gse334718 | 0.47178 | 0.37500 | uniform | 0.02822 | -0.02327 | -0.12500 | -0.04167 |
| P1 | srle | 0.52857 | 0.26605 | uniform | -0.02857 | -0.01123 | 0.01014 | -0.00084 |
| P2 | astrocyte_gse330741 | 0.50756 | 0.50000 | uniform | -0.00756 | -0.03769 | 0.00000 | 0.00000 |
| P2 | mikl_gse173098 | 0.50461 | 0.19974 | composition | -0.01713 | 0.01258 | 0.01561 | 0.00162 |
| P2 | moffatt_gse334718 | 0.48371 | 0.37500 | uniform | 0.01629 | -0.03520 | -0.12500 | -0.04167 |
| P2 | srle | 0.52700 | 0.26267 | uniform | -0.02700 | -0.00966 | 0.00676 | -0.00422 |
| P3 | astrocyte_gse330741 | 0.51389 | 0.50000 | uniform | -0.01389 | -0.04402 | 0.00000 | 0.00000 |
| P3 | mikl_gse173098 | 0.50138 | 0.19069 | composition | -0.01391 | 0.01580 | 0.00656 | -0.00743 |
| P3 | moffatt_gse334718 | 0.46474 | 0.41667 | uniform | 0.03526 | -0.01623 | -0.08333 | 0.00000 |
| P3 | srle | 0.47768 | 0.23057 | uniform | 0.02232 | 0.03967 | -0.02534 | -0.03632 |
| Hraw | astrocyte_gse330741 | 0.49450 | 0.50000 | uniform | 0.00550 | -0.02463 | 0.00000 | 0.00000 |
| Hraw | mikl_gse173098 | 0.50869 | 0.19594 | composition | -0.02121 | 0.00850 | 0.01181 | -0.00218 |
| Hraw | moffatt_gse334718 | 0.49043 | 0.45833 | uniform | 0.00957 | -0.04192 | -0.04167 | 0.04167 |
| Hraw | srle | 0.48925 | 0.24155 | uniform | 0.01075 | 0.02810 | -0.01436 | -0.02534 |
| P2_weighted | astrocyte_gse330741 | 0.50756 | 0.50000 | uniform | -0.00756 | -0.03769 | 0.00000 | 0.00000 |
| P2_weighted | mikl_gse173098 | 0.50645 | 0.19863 | composition | -0.01898 | 0.01073 | 0.01449 | 0.00051 |
| P2_weighted | moffatt_gse334718 | 0.48754 | 0.37500 | uniform | 0.01246 | -0.03903 | -0.12500 | -0.04167 |
| P2_weighted | srle | 0.52379 | 0.26182 | uniform | -0.02379 | -0.00645 | 0.00591 | -0.00507 |
| Partial | astrocyte_gse330741 | 0.49292 | 0.41667 | uniform | 0.00708 | -0.02304 | -0.08333 | -0.08333 |
| Partial | mikl_gse173098 | 0.52324 | 0.20294 | composition | -0.03576 | -0.00605 | 0.01881 | 0.00482 |
| Partial | moffatt_gse334718 | 0.49118 | 0.50000 | uniform | 0.00882 | -0.04267 | 0.00000 | 0.08333 |
| Partial | srle | 0.47980 | 0.23902 | uniform | 0.02020 | 0.03754 | -0.01689 | -0.02787 |
| H0_pairfree | astrocyte_gse330741 | 0.51876 | 0.56250 | uniform | -0.01876 | -0.04889 | 0.06250 | 0.06250 |
| H0_pairfree | mikl_gse173098 | 0.50982 | 0.19812 | composition | -0.02234 | 0.00737 | 0.01398 | -0.00001 |
| H0_pairfree | moffatt_gse334718 | 0.44447 | 0.41667 | uniform | 0.05553 | 0.00404 | -0.08333 | 0.00000 |
| H0_pairfree | srle | 0.51049 | 0.26943 | uniform | -0.01049 | 0.00686 | 0.01351 | 0.00253 |
| P2_pairfree | astrocyte_gse330741 | 0.47925 | 0.43750 | uniform | 0.02075 | -0.00938 | -0.06250 | -0.06250 |
| P2_pairfree | mikl_gse173098 | 0.50411 | 0.19808 | composition | -0.01663 | 0.01308 | 0.01395 | -0.00004 |
| P2_pairfree | moffatt_gse334718 | 0.48371 | 0.37500 | uniform | 0.01629 | -0.03520 | -0.12500 | -0.04167 |
| P2_pairfree | srle | 0.51487 | 0.27027 | uniform | -0.01487 | 0.00247 | 0.01436 | 0.00338 |
| P3_hetero | astrocyte_gse330741 | 0.48714 | 0.43750 | uniform | 0.01286 | -0.01727 | -0.06250 | -0.06250 |
| P3_hetero | mikl_gse173098 | 0.49653 | 0.19720 | composition | -0.00906 | 0.02065 | 0.01306 | -0.00092 |
| P3_hetero | moffatt_gse334718 | 0.48387 | 0.41667 | uniform | 0.01613 | -0.03536 | -0.08333 | 0.00000 |
| P3_hetero | srle | 0.46105 | 0.22128 | uniform | 0.03895 | 0.05629 | -0.03463 | -0.04561 |

The gate requires macro regret <=0.468, improvement over the strongest simple envelope, distributed improvement over H0, specific Mikl/SRLE harm limits, bounded avoidable-wrong risk, nonconcentrated gains, and the fixed descriptive component-bootstrap check. No threshold was changed. The user reference 0.488 was used literally; historical H0 is approximately 0.488228. Four studies, one-component SRLE and already-exposed development constrain all uncertainty interpretations.

Only primary P1/P2/P3 methods are eligible for selection. Secondary checks are displayed but do not change the primary verdict. Prior cross-assay gate: **NO-GO, unchanged**. New independent-dataset discovery: **not allowed in this experiment**. A primary pass would authorize only a separately committed representation-combination experiment, which itself must succeed before considering another independent test.
