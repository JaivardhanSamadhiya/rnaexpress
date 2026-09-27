# What transfers, and what does not

The feature class is useful for generalization only if it helps whole-study holdouts. Optimistic within-assay fits and held-parent predictions answer different questions. All gains below compare each model with the same fixed composition baseline within the indicated task; the stricter gate separately compares the strongest simple-baseline envelope.

| model | within_assay_gain_optimistic | held_parent_gain | held_assay_gain | assays_helped | assays_harmed |
| --- | --- | --- | --- | --- | --- |
| composition | 0.00000 | 0.00000 | 0.00000 | 0 | 0 |
| delta2 | 0.10199 | -0.00087 | -0.01478 | 1 | 3 |
| hierarchical | 0.14364 | -0.00203 | -0.01102 | 1 | 3 |
| interaction_10 | 0.14452 | 0.01793 | 0.01143 | 2 | 2 |
| interaction_25 | 0.13603 | 0.01478 | -0.00600 | 1 | 3 |
| interaction_3 | 0.13817 | 0.02149 | 0.01869 | 3 | 1 |
| interaction_50 | 0.14476 | -0.00728 | 0.00296 | 1 | 3 |
| interaction_full | 0.13401 | 0.00682 | -0.00954 | 1 | 3 |
| kmer123 | 0.13450 | -0.00390 | -0.01360 | 1 | 3 |
| meta_shrink | 0.13450 | -0.00390 | -0.00088 | 1 | 3 |
| metadata | -0.00007 | -0.00173 | -0.00127 | 0 | 1 |

SRLE held-parent results are missing by design: its 592 anchors share one reporter component. A mean held-parent gain therefore covers fewer studies than the held-assay mean; those columns are not a matched biological meta-analysis. Full per-study entries and missingness remain in `feature_transfer_matrix.csv`.

## Direction consistency of independently fitted coefficients

| model | features | features_with_sign_reversal | mean_between_assay_sd | mean_majority_sign_fraction |
| --- | --- | --- | --- | --- |
| composition | 22 | 16 | 0.21556 | 0.72222 |
| delta2 | 38 | 31 | 0.22780 | 0.70946 |
| interaction_10 | 246 | 203 | 0.25134 | 0.71497 |
| kmer123 | 102 | 86 | 0.18768 | 0.71287 |
| metadata | 18 | 14 | 0.26945 | 0.68627 |

| model | study_a | study_b | features_both_nonzero | sign_concordance | coefficient_rank_concordance | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| delta2 | astrocyte_gse330741 | mikl_gse173098 | 35 | 0.45714 | -0.18398 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| delta2 | astrocyte_gse330741 | moffatt_gse334718 | 35 | 0.71429 | 0.31816 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| delta2 | astrocyte_gse330741 | srle | 31 | 0.48387 | 0.05824 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| delta2 | mikl_gse173098 | moffatt_gse334718 | 37 | 0.35135 | -0.31962 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| delta2 | mikl_gse173098 | srle | 32 | 0.46875 | -0.15693 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| delta2 | moffatt_gse334718 | srle | 32 | 0.53125 | -0.06920 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| kmer123 | astrocyte_gse330741 | mikl_gse173098 | 99 | 0.58586 | 0.12022 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| kmer123 | astrocyte_gse330741 | moffatt_gse334718 | 99 | 0.59596 | 0.16045 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| kmer123 | astrocyte_gse330741 | srle | 95 | 0.54737 | 0.06926 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| kmer123 | mikl_gse173098 | moffatt_gse334718 | 101 | 0.48515 | -0.03338 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| kmer123 | mikl_gse173098 | srle | 96 | 0.41667 | -0.10114 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |
| kmer123 | moffatt_gse334718 | srle | 96 | 0.45833 | -0.03642 | descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms |

Features with reversed signs are not called universal. Coefficients are training-scale-removed, regularized, correlated-feature associations; composition is already encoded in substitution identities and some k-mer changes. Between-study standard deviation and rank/sign concordance describe heterogeneity, not causal molecular mechanisms. Four studies cannot securely identify a universal biological effect distribution. Per-feature vectors, signs and heterogeneity are retained in `feature_heterogeneity.csv` rather than selecting only favorable motifs.

## Shared versus source-residual contribution

| stage | dataset | full_score_regret | universal_only_regret | residual_regret_gain | fraction_universal_regret_removed | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| held_parent | astrocyte_gse330741 | 0.50525 | 0.50525 | 0.00000 | 0.00000 | predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution |
| held_parent | mikl_gse173098 | 0.50492 | 0.50492 | 0.00000 | 0.00000 | predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution |
| held_parent | moffatt_gse334718 | 0.49390 | 0.49390 | 0.00000 | 0.00000 | predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution |
| within_assay | astrocyte_gse330741 | 0.38020 | 0.38020 | 0.00000 | 0.00000 | predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution |
| within_assay | mikl_gse173098 | 0.41425 | 0.41425 | 0.00000 | 0.00001 | predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution |
| within_assay | moffatt_gse334718 | 0.38427 | 0.38427 | 0.00000 | 0.00000 | predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution |
| within_assay | srle | 0.16296 | 0.16296 | 0.00000 | 0.00000 | predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution |

Residual terms can improve a measured source while disappearing on a new study. The universal-only held-study scores never use the held assay identifier or residual. Reported fractions quantify normalized-regret change, not variance explained or causal attribution. The separate empirical-Bayes coefficient model uses only source-study estimates and working curvature uncertainty; its held-assay behavior is listed alongside pooled k-mers, never promoted solely because its coefficients look consistent.

## Context scale and pretrained representations

All five context sizes were fixed before comparison. Short-k-mer deltas alone are equal across windows that retain the necessary unchanged flanks. Parent-frequency × edit interactions create the actual context dependence. Therefore a window advantage cannot be attributed to a new local delta count definition. No 4–6-mer or neural architecture expansion followed results. Frozen 3UTRBERT is compared on matched complete decision contexts in two studies, with no missing embeddings fabricated.

See `size_locality_metrics.csv` for fixed 1, 2–3, 4–6 substitution and span<=6 sensitivities; they re-rank saved predictions and do not redefine the main candidate set or gate. Small base-count edits may span a wider sequence interval.
