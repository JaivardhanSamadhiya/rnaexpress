# Calibration results

All studies are exposed development data. Biological breadth is unequal: one SRLE reporter, two astrocyte genes, six Moffatt parent/gene groups, and 187 Mikl genes. Variant counts do not supply independent biological experiments. The prior cross-assay NO-GO is unchanged.

Pairwise calibration concerns empirical replicate support for one candidate exceeding another. It is not the probability that an edit improves over WT or succeeds in a future biological system. Expected per-replicate Brier and cross-entropy use unsmoothed empirical votes; exact numerical ties receive half a vote. Both pair orientations are scored, with hierarchical pair weights. ECE uses ten fixed equal-width bins. Aggregate-only calibration in Moffatt cannot substitute for missing replicated calibration.

## Whole-study primary calibration

| model | dataset | endpoint | pairs | brier | log_loss | ece | sharpness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H0 | astrocyte_gse330741 | aggregate | 1792 | 0.25213 | 0.69751 | 0.03519 | 0.09791 |
| H0 | astrocyte_gse330741 | replicate | 1792 | 0.25429 | 0.70194 | 0.04982 | 0.09791 |
| P1 | astrocyte_gse330741 | aggregate | 1792 | 0.25097 | 0.69517 | 0.02629 | 0.09230 |
| P1 | astrocyte_gse330741 | replicate | 1792 | 0.25314 | 0.69959 | 0.04346 | 0.09230 |
| P2 | astrocyte_gse330741 | aggregate | 1792 | 0.25012 | 0.69341 | 0.01042 | 0.07096 |
| P2 | astrocyte_gse330741 | replicate | 1792 | 0.25175 | 0.69669 | 0.02929 | 0.07096 |
| P3 | astrocyte_gse330741 | aggregate | 1792 | 0.25048 | 0.69417 | 0.01684 | 0.08778 |
| P3 | astrocyte_gse330741 | replicate | 1792 | 0.25270 | 0.69868 | 0.03898 | 0.08778 |
| H0 | mikl_gse173098 | aggregate | 16677 | 0.28029 | 0.76535 | 0.14810 | 0.26157 |
| H0 | mikl_gse173098 | replicate | 16677 | 0.27625 | 0.75621 | 0.13483 | 0.26157 |
| P1 | mikl_gse173098 | aggregate | 16677 | 0.27474 | 0.75107 | 0.11949 | 0.22624 |
| P1 | mikl_gse173098 | replicate | 16677 | 0.27111 | 0.74281 | 0.11112 | 0.22624 |
| P2 | mikl_gse173098 | aggregate | 16677 | 0.26802 | 0.73332 | 0.10374 | 0.19405 |
| P2 | mikl_gse173098 | replicate | 16677 | 0.26513 | 0.72690 | 0.10076 | 0.19405 |
| P3 | mikl_gse173098 | aggregate | 16677 | 0.27536 | 0.75323 | 0.12099 | 0.23633 |
| P3 | mikl_gse173098 | replicate | 16677 | 0.27194 | 0.74527 | 0.11779 | 0.23633 |
| H0 | moffatt_gse334718 | aggregate | 3072 | 0.25929 | 0.71361 | 0.07233 | 0.18436 |
| P1 | moffatt_gse334718 | aggregate | 3072 | 0.25515 | 0.70400 | 0.05937 | 0.14283 |
| P2 | moffatt_gse334718 | aggregate | 3072 | 0.25167 | 0.69660 | 0.03413 | 0.10147 |
| P3 | moffatt_gse334718 | aggregate | 3072 | 0.25563 | 0.70503 | 0.06226 | 0.14926 |
| H0 | srle | aggregate | 2022 | 0.25807 | 0.70969 | 0.07825 | 0.12167 |
| H0 | srle | replicate | 2022 | 0.25766 | 0.70889 | 0.06981 | 0.12167 |
| P1 | srle | aggregate | 2022 | 0.25224 | 0.69765 | 0.04703 | 0.05108 |
| P1 | srle | replicate | 2022 | 0.25219 | 0.69755 | 0.04198 | 0.05108 |
| P2 | srle | aggregate | 2022 | 0.25190 | 0.69696 | 0.04782 | 0.04917 |
| P2 | srle | replicate | 2022 | 0.25183 | 0.69682 | 0.03754 | 0.04917 |
| P3 | srle | aggregate | 2022 | 0.25154 | 0.69630 | 0.01363 | 0.07294 |
| P3 | srle | replicate | 2022 | 0.25138 | 0.69597 | 0.01561 | 0.07294 |

## Frozen calibration claim check

| model | primary_selection_eligible | calibration_claim_gate_passes |
| --- | --- | --- |
| P1 | True | False |
| P2 | True | False |
| P3 | True | False |
| Hraw | False | False |
| P2_weighted | False | False |
| Partial | False | False |
| H0_pairfree | False | False |
| P2_pairfree | False | False |
| P3_hetero | False | False |

As an analytic postfit reference, constant probability 0.5 has Brier 0.25 and log loss log(2)=0.693147 under these scoring definitions. Every primary method is worse than that reference in every replicate-covered held study. Improvements over H0 therefore do not establish informative probability transfer. See `calibration_reference.md`; this reference changes no frozen gate.

The claim requires >=0.005 macro Brier improvement and >=0.01 log-loss improvement across the three replicate-covered assays, no Brier harm >0.01, and macro ECE<=0.05. Improvements in probability scoring do not establish better candidate selection. All secondary model and fold-specific metrics are retained in `calibration.csv`; reliability-bin values and weights are in `reliability_bins.csv`.

## Conditional conservative selection and abstention

Status: **NOT_RUN_CALIBRATION_REQUIREMENTS_NOT_MET**. Eligible methods: **none**.

| brier_gain | dataset | ece | logloss_gain | model | passes |
| --- | --- | --- | --- | --- | --- |
| 0.03494 | astrocyte_gse330741 | 0.05533 | 0.09362 | P1 | False |
| 0.01364 | mikl_gse173098 | 0.07396 | 0.03184 | P1 | False |
| 0.03565 | astrocyte_gse330741 | 0.05122 | 0.09515 | P2 | False |
| 0.01701 | mikl_gse173098 | 0.05499 | 0.03910 | P2 | False |
| 0.02424 | astrocyte_gse330741 | 0.10058 | 0.06902 | P3 | False |
| 0.01369 | mikl_gse173098 | 0.06673 | 0.03209 | P3 | False |

The held-parent criterion applies separately to astrocyte and Mikl; fold metrics are averaged by held component count, including fold-wise ECE. No threshold was relaxed after evaluation. The conservative policy and abstention were NOT RUN because the frozen calibration requirements failed. Pairwise probabilities do not identify absolute-benefit probability. The historical source-only direction head was held fixed across matched supervision methods, so its calibration cannot improve by construction; observed correct/wrong recommendations can still change with candidate ranking.
