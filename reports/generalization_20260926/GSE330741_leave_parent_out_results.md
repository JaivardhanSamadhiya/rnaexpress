# Held-parent method replication: partial signal, criterion failed

The primary model predicts held-parent SNP ranks weakly positively, but **the frozen test does not establish incremental sequence-order generalization**. Mean parent rho is **0.102266 [0.043663, 0.177122]** versus simple baseline 0.089149. The paired increment is **0.013118 [−0.022045, 0.067958]**, exact one-sided block sign-flip p=0.3125. Four of seven parents improve. Position alone reaches 0.092991; the primary's increment over position is also uncertain.

All external results use 3,984 verified SNPs, seven 190-nt parents, five nonoverlap components and two genes (Slc1a2 and Sparc). The author-retained design has 14 matched biological replicate labels (three-cortex pools), with 11–14 positive matched pairs per admitted variant. Technical sequencing lanes are not biological replicates. Intervals below are descriptive 95% component-bootstrap intervals, not evidence of thousands of independent biological contexts. Historical exposure is PARTIALLY EXPOSED.

B is target-assay training with independent held-parent prediction, not zero-shot validation. Its entire model family, selection rule and candidate policy were fixed before A outcomes. Every outer fold excludes the held parent plus any overlapping same-gene parent. All alpha selection, scaling, response means and nuisance effects use only remaining training parents. No random SNP split was used.

## Every model and parent

| model | spearman | spearman_ci_low | spearman_ci_high | mse | mae | strict_sign_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| delta1 | 0.035198 | 0.012912 | 0.070704 | 0.041627 | 0.144425 | 0.924300 |
| delta2 | 0.090805 | 0.028932 | 0.194905 | 0.041482 | 0.144323 | 0.924300 |
| delta3 | 0.067389 | 0.023898 | 0.114956 | 0.042166 | 0.146015 | 0.924300 |
| delta_AU | 0.030871 | -0.014204 | 0.071067 | 0.041809 | 0.144633 | 0.924300 |
| kmer123 | 0.070382 | 0.028332 | 0.118913 | 0.042125 | 0.145971 | 0.924300 |
| no_change | 0.000000 | 0.000000 | 0.000000 | 0.108605 | 0.294357 | 0.000000 |
| position | 0.092991 | 0.064363 | 0.136385 | 0.041447 | 0.144153 | 0.924300 |
| simple_full | 0.089149 | 0.060283 | 0.133999 | 0.041495 | 0.144277 | 0.924300 |
| simple_full_delta2 | 0.102266 | 0.043663 | 0.177122 | 0.041359 | 0.144094 | 0.924300 |
| simple_full_delta2_delta3 | 0.080715 | 0.036140 | 0.120091 | 0.042090 | 0.145857 | 0.924300 |
| substitution | 0.017474 | -0.005749 | 0.059281 | 0.041797 | 0.144665 | 0.924300 |
| substitution_composition | 0.016074 | -0.007927 | 0.059275 | 0.041797 | 0.144671 | 0.924300 |
| substitution_position | 0.089136 | 0.060238 | 0.133999 | 0.041495 | 0.144277 | 0.924300 |
| training_mean | 0.000000 | 0.000000 | 0.000000 | 0.041749 | 0.144606 | 0.924300 |

| parent_id | position | simple_full | simple_full_delta2 | 2mer_increment |
| --- | --- | --- | --- | --- |
| slc1a2.1_3281_3381 | 0.185063 | 0.154575 | 0.134719 | -0.019856 |
| slc1a2.1_3641_3721 | -0.002446 | -0.007263 | -0.043478 | -0.036215 |
| slc1a2.1_3781_3841 | 0.116780 | 0.094207 | 0.059362 | -0.034845 |
| slc1a2.1_4181_4281 | 0.060031 | 0.082015 | 0.208517 | 0.126501 |
| sparc_1041_1121 | 0.143527 | 0.150750 | 0.178157 | 0.027407 |
| sparc_661_761 | 0.091752 | 0.139415 | 0.166930 | 0.027514 |
| sparc_901_981 | 0.056226 | 0.010340 | 0.011658 | 0.001319 |

The primary uses substitution, composition, position and Δ2-mer features; `simple_full` uses the same controls without Δ2-mer. Parent nuisance indicators are centered using training rows; unknown parents have zero indicators. Training parents have equal total weight. Ridge alpha [1,10,100] is selected by mean inner parent MSE with overlap exclusion. Coefficients, scaler parameters, alpha decisions and fold membership are retained in `test_b_fits.json`, `test_b_inner_selection.csv` and `test_b_fold_assignments.json`.

The strong-success checks for positive primary rho and candidate regret passed. The primary rank-advantage check failed. More complex 3-mer/combined controls did not provide a basis to override this failure. Model ranking after reveal is descriptive, never a new winner selection.

## Prespecified two-gene sensitivity

| held_gene | model | spearman | mse |
| --- | --- | --- | --- |
| slc1a2.1 | simple_full | 0.071638 | 0.039468 |
| slc1a2.1 | simple_full_delta2 | 0.123674 | 0.038807 |
| sparc | simple_full | 0.099720 | 0.046621 |
| sparc | simple_full_delta2 | 0.150148 | 0.046264 |

These fixed-alpha10 predictions train on the other gene only. Both gene-level average primary correlations are positive, but there are only two gene folds and they do not supply a reliable population interval or rescue the primary test. Full per-parent results remain in `leave_gene_out_parent_metrics.csv`.

Candidate selection is more promising than whole-list ranking: primary regret 0.371947 versus simple baseline 0.488527 and uniform 0.500000. This is separately reported with the small number of decisions and uncertainty limitations. Full predictions: `artifacts/generalization_20260926/GSE330741_leave_parent_out_predictions.csv`.
