# Frozen model-selection verdict: NO-GO

**NO-GO. No model passed the frozen cross-assay development gate. No new independent resource was searched or opened.**

The gate and composite were fixed at `d6a0623`, before model comparison. They require improvements of >=0.02 in at least three of four studies, macro gain >=0.02, benefit remaining after removing the best study, no one-study concentration above 60%, bounded avoidable-risk/individual-study harm and a descriptive bootstrap lower bound >=−0.01. Every condition is required. No threshold changed after seeing results.

| composite | gain_ci_high | gain_ci_low | macro_avoidable_worsening | macro_avoidable_wrong | macro_gain | macro_regret | max_positive_gain_share | model | passes | studies_harmed | studies_helped | studies_helped_at_least_0_02 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.70689 | -0.00254 | -0.05093 | 0.01109 | 0.37110 | -0.02483 | 0.52170 | 1.00000 | delta2 | False | 3 | 1 | 0 |
| 0.69786 | -0.00887 | -0.03520 | -0.00402 | 0.35599 | -0.02106 | 0.51793 | 1.00000 | hierarchical | False | 3 | 1 | 0 |
| 0.65366 | 0.02538 | -0.02307 | -0.03970 | 0.32031 | 0.00138 | 0.49549 | 0.54448 | interaction_10 | False | 2 | 2 | 2 |
| 0.68781 | -0.00148 | -0.03287 | -0.02630 | 0.33371 | -0.01605 | 0.51292 | 1.00000 | interaction_25 | False | 3 | 1 | 1 |
| 0.65132 | 0.02308 | -0.00740 | -0.01459 | 0.34542 | 0.00864 | 0.48823 | 0.63086 | interaction_3 | False | 2 | 2 | 2 |
| 0.67579 | 0.01188 | -0.02571 | -0.03333 | 0.32668 | -0.00709 | 0.50395 | 1.00000 | interaction_50 | False | 3 | 1 | 1 |
| 0.69724 | -0.00598 | -0.03314 | -0.00020 | 0.35982 | -0.01959 | 0.51646 | 1.00000 | interaction_full | False | 3 | 1 | 1 |
| 0.72120 | -0.01214 | -0.03606 | 0.03200 | 0.39201 | -0.02364 | 0.52051 | 1.00000 | kmer123 | False | 4 | 0 | 0 |
| 0.69363 | 0.01132 | -0.03149 | 0.01097 | 0.37098 | -0.01093 | 0.50780 | 1.00000 | meta_shrink | False | 3 | 1 | 1 |

## Failed checks remain explicit

| model | passes | failed_checks |
| --- | --- | --- |
| delta2 | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_gain_at_least_0_02; no_study_over_60pct_positive_gain |
| hierarchical | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_gain_at_least_0_02; no_study_over_60pct_positive_gain |
| interaction_10 | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_gain_at_least_0_02 |
| interaction_25 | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_gain_at_least_0_02; no_study_over_60pct_positive_gain |
| interaction_3 | False | at_least_three_studies_gain_0_02; leave_best_study_out_positive; macro_gain_at_least_0_02; no_study_over_60pct_positive_gain |
| interaction_50 | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_gain_at_least_0_02; no_study_over_60pct_positive_gain |
| interaction_full | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_gain_at_least_0_02; no_study_over_60pct_positive_gain |
| kmer123 | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_avoidable_harm_at_most_0_02; macro_gain_at_least_0_02; no_study_avoidable_harm_over_0_05; no_study_over_60pct_positive_gain |
| meta_shrink | False | at_least_three_studies_gain_0_02; descriptive_gain_lower_at_least_minus_0_01; leave_best_study_out_positive; macro_gain_at_least_0_02; no_study_avoidable_harm_over_0_05; no_study_over_60pct_positive_gain; no_study_regret_harm_over_0_05 |

## Per-study comparison with the strongest simple envelope

| model | dataset | baseline | regret | regret_gain | avoidable_wrong | avoidable_wrong_worsening |
| --- | --- | --- | --- | --- | --- | --- |
| delta2 | astrocyte_gse330741 | uniform | 0.49229 | 0.00771 | 0.52083 | 0.02083 |
| delta2 | mikl_gse173098 | composition | 0.52245 | -0.03498 | 0.19667 | 0.01253 |
| delta2 | moffatt_gse334718 | uniform | 0.54921 | -0.04921 | 0.50000 | 0.00000 |
| delta2 | srle | uniform | 0.52283 | -0.02283 | 0.26689 | 0.01098 |
| hierarchical | astrocyte_gse330741 | uniform | 0.53427 | -0.03427 | 0.50000 | 0.00000 |
| hierarchical | mikl_gse173098 | composition | 0.52818 | -0.04071 | 0.19959 | 0.01545 |
| hierarchical | moffatt_gse334718 | uniform | 0.48521 | 0.01479 | 0.45833 | -0.04167 |
| hierarchical | srle | uniform | 0.52406 | -0.02406 | 0.26605 | 0.01014 |
| interaction_10 | astrocyte_gse330741 | uniform | 0.47869 | 0.02131 | 0.47917 | -0.02083 |
| interaction_10 | mikl_gse173098 | composition | 0.49777 | -0.01030 | 0.18665 | 0.00251 |
| interaction_10 | moffatt_gse334718 | uniform | 0.47453 | 0.02547 | 0.33333 | -0.16667 |
| interaction_10 | srle | uniform | 0.53095 | -0.03095 | 0.28209 | 0.02618 |
| interaction_25 | astrocyte_gse330741 | uniform | 0.53228 | -0.03228 | 0.43750 | -0.06250 |
| interaction_25 | mikl_gse173098 | composition | 0.51057 | -0.02310 | 0.20196 | 0.01783 |
| interaction_25 | moffatt_gse334718 | uniform | 0.46913 | 0.03087 | 0.41667 | -0.08333 |
| interaction_25 | srle | uniform | 0.53968 | -0.03968 | 0.27872 | 0.02280 |
| interaction_3 | astrocyte_gse330741 | uniform | 0.46987 | 0.03013 | 0.50000 | 0.00000 |
| interaction_3 | mikl_gse173098 | composition | 0.51718 | -0.02971 | 0.19812 | 0.01399 |
| interaction_3 | moffatt_gse334718 | uniform | 0.44851 | 0.05149 | 0.41667 | -0.08333 |
| interaction_3 | srle | uniform | 0.51734 | -0.01734 | 0.26689 | 0.01098 |
| interaction_50 | astrocyte_gse330741 | uniform | 0.52588 | -0.02588 | 0.41667 | -0.08333 |
| interaction_50 | mikl_gse173098 | composition | 0.51394 | -0.02647 | 0.19806 | 0.01393 |
| interaction_50 | moffatt_gse334718 | uniform | 0.44931 | 0.05069 | 0.41667 | -0.08333 |
| interaction_50 | srle | uniform | 0.52669 | -0.02669 | 0.27534 | 0.01943 |
| interaction_full | astrocyte_gse330741 | uniform | 0.53150 | -0.03150 | 0.50000 | 0.00000 |
| interaction_full | mikl_gse173098 | composition | 0.53321 | -0.04574 | 0.20559 | 0.02146 |
| interaction_full | moffatt_gse334718 | uniform | 0.47429 | 0.02571 | 0.45833 | -0.04167 |
| interaction_full | srle | uniform | 0.52684 | -0.02684 | 0.27534 | 0.01943 |
| kmer123 | astrocyte_gse330741 | uniform | 0.52683 | -0.02683 | 0.56250 | 0.06250 |
| kmer123 | mikl_gse173098 | composition | 0.52435 | -0.03688 | 0.19277 | 0.00863 |
| kmer123 | moffatt_gse334718 | uniform | 0.50504 | -0.00504 | 0.54167 | 0.04167 |
| kmer123 | srle | uniform | 0.52582 | -0.02582 | 0.27111 | 0.01520 |
| meta_shrink | astrocyte_gse330741 | uniform | 0.55585 | -0.05585 | 0.56250 | 0.06250 |
| meta_shrink | mikl_gse173098 | composition | 0.51554 | -0.02806 | 0.19535 | 0.01121 |
| meta_shrink | moffatt_gse334718 | uniform | 0.42472 | 0.07528 | 0.45833 | -0.04167 |
| meta_shrink | srle | uniform | 0.53509 | -0.03509 | 0.26774 | 0.01182 |

The comparator is the better observed simple baseline in each held study, fixed as a conservative envelope before evaluation. It is not a deployable model chosen using target labels. Exact baseline identities are retained in `strongest_simple_envelope.csv`. Macro improvements use equal study weight. Bayesian component-bootstrap intervals are descriptive and cannot overcome the small number of experiments; SRLE's one-component uncertainty is degenerate. Model development itself used these historically exposed resources, so the intervals are not new independent confirmation.

Selected model: **NONE**. Lowest-composite descriptive candidate: `interaction_3`. The latter is not a final generalizable system if no model passes. Destination-family, pretrained, edit-size or abstention subgroup findings cannot silently replace this selection rule.

New independent-dataset discovery allowed by this gate: **False**. If false, stop this branch and preserve all results. No external test is consumed to rescue the development result.
