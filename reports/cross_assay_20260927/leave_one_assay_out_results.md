# Leave-one-assay-out development results

**NO-GO. No model passed the frozen cross-assay development gate. No new independent resource was searched or opened.** The descriptive comparison leader is `interaction_3`; this label does not make it an externally validated or selected deployment model.

These are reused, exposed benchmarks. Four study-level holdouts contain 26,258 measurements, but biological breadth is strongly unequal: SRLE one HBB reporter, astrocytes two genes, Moffatt six parents/genes, and Mikl 187 genes. Both cell lines/reporters remain inside their original study. Primary aggregation gives studies and biological components equal weight; thousands of candidates are not independent biological replications.

The data, feature and model grid, candidate eligibility, thresholds, selection composite and gate were committed at `d6a0623` before this comparison. All fitted coefficients, feature scaling, direction and feasibility heads for each held study use only the allowed other studies, with cross-study gene/exact-allele purging. Held-out residual contributions are exactly zero. There was no target calibration, direction flip, hyperparameter search or new-source access.

## Primary cohort

| dataset | rows | parents | decision_sets | genes | components |
| --- | --- | --- | --- | --- | --- |
| astrocyte_gse330741 | 3984 | 7 | 7 | 2 | 2 |
| mikl_gse173098 | 13781 | 2417 | 4825 | 187 | 187 |
| moffatt_gse334718 | 6749 | 6 | 12 | 6 | 6 |
| srle | 1744 | 592 | 592 | 1 | 1 |

## Every model in every held study

| dataset | model | components | decision_sets | regret | avoidable_wrong | wrong_direction | correct_direction | variant_sign_accuracy | pairwise_accuracy | spearman | best_recovery | top5_best_recovery | variant_weighted_regret |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| astrocyte_gse330741 | composition | 2 | 7 | 0.50528 | 0.58333 | 0.58333 | 0.41667 | 0.92155 | 0.48751 | -0.03860 | 0.00000 | 0.00000 | 0.50718 |
| mikl_gse173098 | composition | 187 | 4825 | 0.48747 | 0.18414 | 0.49153 | 0.50637 | 0.37845 | 0.50896 | 0.01951 | 0.44951 | 0.99509 | 0.48925 |
| moffatt_gse334718 | composition | 6 | 12 | 0.51395 | 0.54167 | 0.54167 | 0.45833 | 0.22830 | 0.50744 | 0.02196 | 0.00000 | 0.04167 | 0.50248 |
| srle | composition | 1 | 592 | 0.52096 | 0.26267 | 0.50676 | 0.49324 | 0.50095 | 0.48392 | -0.03425 | 0.36149 | 0.99831 | 0.51681 |
| astrocyte_gse330741 | delta2 | 2 | 7 | 0.49229 | 0.52083 | 0.52083 | 0.47917 | 0.92111 | 0.50174 | 0.00516 | 0.00000 | 0.00000 | 0.48636 |
| mikl_gse173098 | delta2 | 187 | 4825 | 0.52245 | 0.19667 | 0.50525 | 0.49328 | 0.38391 | 0.47402 | -0.05054 | 0.41592 | 0.99469 | 0.49995 |
| moffatt_gse334718 | delta2 | 6 | 12 | 0.54921 | 0.50000 | 0.50000 | 0.50000 | 0.38896 | 0.49687 | -0.00884 | 0.00000 | 0.00000 | 0.57059 |
| srle | delta2 | 1 | 592 | 0.52283 | 0.26689 | 0.51098 | 0.48902 | 0.50095 | 0.48452 | -0.03663 | 0.35642 | 0.99747 | 0.52123 |
| astrocyte_gse330741 | hierarchical | 2 | 7 | 0.53427 | 0.50000 | 0.50000 | 0.50000 | 0.91453 | 0.50173 | 0.00478 | 0.00000 | 0.00000 | 0.53454 |
| mikl_gse173098 | hierarchical | 187 | 4825 | 0.52818 | 0.19959 | 0.50750 | 0.49031 | 0.38317 | 0.47089 | -0.05640 | 0.41268 | 0.99590 | 0.50429 |
| moffatt_gse334718 | hierarchical | 6 | 12 | 0.48521 | 0.45833 | 0.45833 | 0.54167 | 0.43639 | 0.50486 | 0.01395 | 0.00000 | 0.04167 | 0.48865 |
| srle | hierarchical | 1 | 592 | 0.52406 | 0.26605 | 0.51014 | 0.48986 | 0.50095 | 0.48085 | -0.04132 | 0.35811 | 0.99662 | 0.52444 |
| astrocyte_gse330741 | interaction_10 | 2 | 7 | 0.47869 | 0.47917 | 0.47917 | 0.52083 | 0.88369 | 0.49784 | -0.00684 | 0.00000 | 0.00000 | 0.48669 |
| mikl_gse173098 | interaction_10 | 187 | 4825 | 0.49777 | 0.18665 | 0.49468 | 0.50337 | 0.39210 | 0.50038 | 0.00297 | 0.44199 | 0.99514 | 0.49920 |
| moffatt_gse334718 | interaction_10 | 6 | 12 | 0.47453 | 0.33333 | 0.33333 | 0.66667 | 0.44599 | 0.50803 | 0.02422 | 0.00000 | 0.00000 | 0.48947 |
| srle | interaction_10 | 1 | 592 | 0.53095 | 0.28209 | 0.52618 | 0.47382 | 0.50095 | 0.47250 | -0.05898 | 0.35473 | 0.99662 | 0.53561 |
| astrocyte_gse330741 | interaction_25 | 2 | 7 | 0.53228 | 0.43750 | 0.43750 | 0.56250 | 0.88692 | 0.49346 | -0.01965 | 0.00000 | 0.00000 | 0.53555 |
| mikl_gse173098 | interaction_25 | 187 | 4825 | 0.51057 | 0.20196 | 0.50995 | 0.48789 | 0.39149 | 0.48801 | -0.02374 | 0.42973 | 0.99500 | 0.50070 |
| moffatt_gse334718 | interaction_25 | 6 | 12 | 0.46913 | 0.41667 | 0.41667 | 0.58333 | 0.45104 | 0.50769 | 0.02276 | 0.00000 | 0.00000 | 0.47872 |
| srle | interaction_25 | 1 | 592 | 0.53968 | 0.27872 | 0.52280 | 0.47720 | 0.50095 | 0.46289 | -0.08019 | 0.34206 | 0.99662 | 0.54054 |
| astrocyte_gse330741 | interaction_3 | 2 | 7 | 0.46987 | 0.50000 | 0.50000 | 0.50000 | 0.88873 | 0.49632 | -0.01102 | 0.00000 | 0.00000 | 0.46712 |
| mikl_gse173098 | interaction_3 | 187 | 4825 | 0.51718 | 0.19812 | 0.50610 | 0.49168 | 0.39209 | 0.48250 | -0.03517 | 0.42371 | 0.99509 | 0.49634 |
| moffatt_gse334718 | interaction_3 | 6 | 12 | 0.44851 | 0.41667 | 0.41667 | 0.58333 | 0.45463 | 0.51795 | 0.05397 | 0.04167 | 0.04167 | 0.43786 |
| srle | interaction_3 | 1 | 592 | 0.51734 | 0.26689 | 0.51098 | 0.48902 | 0.50095 | 0.48358 | -0.03780 | 0.35980 | 0.99662 | 0.52227 |
| astrocyte_gse330741 | interaction_50 | 2 | 7 | 0.52588 | 0.41667 | 0.41667 | 0.58333 | 0.88876 | 0.49271 | -0.02253 | 0.00000 | 0.00000 | 0.53389 |
| mikl_gse173098 | interaction_50 | 187 | 4825 | 0.51394 | 0.19806 | 0.50546 | 0.49229 | 0.39140 | 0.48313 | -0.03187 | 0.42523 | 0.99446 | 0.50943 |
| moffatt_gse334718 | interaction_50 | 6 | 12 | 0.44931 | 0.41667 | 0.41667 | 0.58333 | 0.43340 | 0.51649 | 0.04918 | 0.00000 | 0.00000 | 0.45765 |
| srle | interaction_50 | 1 | 592 | 0.52669 | 0.27534 | 0.51943 | 0.48057 | 0.50095 | 0.47680 | -0.05306 | 0.35473 | 0.99578 | 0.53198 |
| astrocyte_gse330741 | interaction_full | 2 | 7 | 0.53150 | 0.50000 | 0.50000 | 0.50000 | 0.89418 | 0.49762 | -0.00730 | 0.00000 | 0.00000 | 0.53454 |
| mikl_gse173098 | interaction_full | 187 | 4825 | 0.53321 | 0.20559 | 0.51316 | 0.48456 | 0.39887 | 0.46689 | -0.06709 | 0.40730 | 0.99567 | 0.50281 |
| moffatt_gse334718 | interaction_full | 6 | 12 | 0.47429 | 0.45833 | 0.45833 | 0.54167 | 0.43245 | 0.51941 | 0.05733 | 0.00000 | 0.00000 | 0.47799 |
| srle | interaction_full | 1 | 592 | 0.52684 | 0.27534 | 0.51943 | 0.48057 | 0.50095 | 0.47596 | -0.05232 | 0.35642 | 0.99662 | 0.53137 |
| astrocyte_gse330741 | kmer123 | 2 | 7 | 0.52683 | 0.56250 | 0.56250 | 0.43750 | 0.91453 | 0.50041 | 0.00057 | 0.00000 | 0.00000 | 0.52910 |
| mikl_gse173098 | kmer123 | 187 | 4825 | 0.52435 | 0.19277 | 0.50133 | 0.49714 | 0.38317 | 0.47407 | -0.05200 | 0.41440 | 0.99541 | 0.49943 |
| moffatt_gse334718 | kmer123 | 6 | 12 | 0.50504 | 0.54167 | 0.54167 | 0.45833 | 0.43639 | 0.50539 | 0.01551 | 0.00000 | 0.04167 | 0.50002 |
| srle | kmer123 | 1 | 592 | 0.52582 | 0.27111 | 0.51520 | 0.48480 | 0.50095 | 0.47865 | -0.04697 | 0.35557 | 0.99662 | 0.52623 |
| astrocyte_gse330741 | meta_shrink | 2 | 7 | 0.55585 | 0.56250 | 0.56250 | 0.43750 | 0.91453 | 0.49474 | -0.01554 | 0.00000 | 0.00000 | 0.54975 |
| mikl_gse173098 | meta_shrink | 187 | 4825 | 0.51554 | 0.19535 | 0.50393 | 0.49460 | 0.38317 | 0.48336 | -0.03291 | 0.42558 | 0.99572 | 0.49864 |
| moffatt_gse334718 | meta_shrink | 6 | 12 | 0.42472 | 0.45833 | 0.45833 | 0.54167 | 0.43639 | 0.50612 | 0.01831 | 0.00000 | 0.00000 | 0.40583 |
| srle | meta_shrink | 1 | 592 | 0.53509 | 0.26774 | 0.51182 | 0.48818 | 0.50095 | 0.47081 | -0.06074 | 0.35051 | 0.99578 | 0.53337 |
| astrocyte_gse330741 | metadata | 2 | 7 | 0.50528 | 0.58333 | 0.58333 | 0.41667 | 0.92155 | 0.48808 | -0.03712 | 0.00000 | 0.00000 | 0.50718 |
| mikl_gse173098 | metadata | 187 | 4825 | 0.49254 | 0.18740 | 0.49524 | 0.50266 | 0.37845 | 0.50437 | 0.00939 | 0.44447 | 0.99533 | 0.49139 |
| moffatt_gse334718 | metadata | 6 | 12 | 0.51395 | 0.54167 | 0.54167 | 0.45833 | 0.22315 | 0.50712 | 0.02099 | 0.00000 | 0.04167 | 0.50248 |
| srle | metadata | 1 | 592 | 0.52096 | 0.26267 | 0.50676 | 0.49324 | 0.50095 | 0.48392 | -0.03425 | 0.36149 | 0.99831 | 0.51681 |
| astrocyte_gse330741 | uniform | 2 | 7 | 0.50000 | 0.50000 | 0.50000 | 0.50000 | 0.92155 | 0.50000 | 0.00000 | 0.00176 | 0.00879 | 0.50000 |
| mikl_gse173098 | uniform | 187 | 4825 | 0.50000 | 0.19103 | 0.49905 | 0.49905 | 0.37845 | 0.50000 | 0.00000 | 0.43969 | 0.99638 | 0.50000 |
| moffatt_gse334718 | uniform | 6 | 12 | 0.50000 | 0.50000 | 0.50000 | 0.50000 | 0.83749 | 0.50000 | 0.00000 | 0.00212 | 0.01062 | 0.50000 |
| srle | uniform | 1 | 592 | 0.50000 | 0.25591 | 0.50000 | 0.50000 | 0.49905 | 0.50000 | 0.00000 | 0.37825 | 0.99586 | 0.50000 |

`uniform` is the exact candidate-wise expectation. Primary regret is direction-averaged normalized utility loss relative to the measured best available edit. Its averaging is component then study macro, unlike `variant_weighted_regret`. `correct_direction` describes the selected recommendation; `variant_sign_accuracy` describes the separate direction head across candidates. Raw regret in each source's own units is retained in `results/cross_assay_20260927/per_assay_secondary_metrics.csv`; raw effect values from nuclear/cytoplasmic, neurite/soma and SN/cortex assays were never pooled as one regression target. Preference ties carry no training signal; predicted ordering ties receive half credit.

## Prespecified whole-domain and destination-family checks

| stage | dataset | model | regret | avoidable_wrong | pairwise_accuracy |
| --- | --- | --- | --- | --- | --- |
| family_transfer | astrocyte_gse330741 | hierarchical | 0.49634 | 0.50000 | 0.49696 |
| family_transfer | mikl_gse173098 | hierarchical | 0.51357 | 0.18756 | 0.48624 |
| family_transfer | moffatt_gse334718 | hierarchical | 0.45690 | 0.41667 | 0.51387 |
| family_transfer | astrocyte_gse330741 | interaction_10 | 0.44830 | 0.41667 | 0.49903 |
| family_transfer | mikl_gse173098 | interaction_10 | 0.48918 | 0.18614 | 0.51022 |
| family_transfer | moffatt_gse334718 | interaction_10 | 0.46811 | 0.41667 | 0.51170 |
| family_transfer | astrocyte_gse330741 | kmer123 | 0.49634 | 0.50000 | 0.49613 |
| family_transfer | mikl_gse173098 | kmer123 | 0.50217 | 0.18651 | 0.49500 |
| family_transfer | moffatt_gse334718 | kmer123 | 0.46940 | 0.50000 | 0.51197 |
| family_transfer | astrocyte_gse330741 | uniform | 0.50000 | 0.50000 | 0.50000 |
| family_transfer | mikl_gse173098 | uniform | 0.50000 | 0.19103 | 0.50000 |
| family_transfer | moffatt_gse334718 | uniform | 0.50000 | 0.50000 | 0.50000 |
| held_domain | astrocyte_gse330741 | hierarchical | 0.54601 | 0.50000 | 0.50408 |
| held_domain | mikl_gse173098 | hierarchical | 0.50877 | 0.19241 | 0.49340 |
| held_domain | moffatt_gse334718 | hierarchical | 0.48452 | 0.54167 | 0.50150 |
| held_domain | srle | hierarchical | 0.52406 | 0.26605 | 0.48085 |
| held_domain | astrocyte_gse330741 | interaction_10 | 0.59170 | 0.64583 | 0.49774 |
| held_domain | mikl_gse173098 | interaction_10 | 0.50317 | 0.19094 | 0.49743 |
| held_domain | moffatt_gse334718 | interaction_10 | 0.52429 | 0.54167 | 0.50930 |
| held_domain | srle | interaction_10 | 0.53095 | 0.28209 | 0.47250 |
| held_domain | astrocyte_gse330741 | kmer123 | 0.49352 | 0.43750 | 0.50419 |
| held_domain | mikl_gse173098 | kmer123 | 0.50857 | 0.19249 | 0.49367 |
| held_domain | moffatt_gse334718 | kmer123 | 0.48452 | 0.54167 | 0.50151 |
| held_domain | srle | kmer123 | 0.52582 | 0.27111 | 0.47865 |
| held_domain | astrocyte_gse330741 | uniform | 0.50000 | 0.50000 | 0.50000 |
| held_domain | mikl_gse173098 | uniform | 0.50000 | 0.19103 | 0.50000 |
| held_domain | moffatt_gse334718 | uniform | 0.50000 | 0.50000 | 0.50000 |
| held_domain | srle | uniform | 0.50000 | 0.25591 | 0.50000 |

Domain holdout contrasts projection with nuclear/cytoplasmic destinations. Family transfer uses projection training sources only for projection tests. There is no second core nuclear study to train a family model for held-out SRLE, so that task is ineligible. A family-specific numerical success does not establish H2 across untouched systems. These secondary checks cannot replace the four-study gate.

## Previously exposed SIRLOIN diagnostic

| dataset | model | regret | wrong_direction | pairwise_accuracy |
| --- | --- | --- | --- | --- |
| sirloin | hierarchical | 0.40395 | 0.25000 | 0.54495 |
| sirloin | interaction_10 | 0.44317 | 0.50000 | 0.55966 |
| sirloin | kmer123 | 0.41160 | 0.25000 | 0.55709 |
| sirloin | uniform | 0.50000 | 0.50000 | 0.50000 |

Only the 223 finite, already-admitted discovery Rep1/2 effects are used; the other four original variants remain missing in the inventory. Rep3/4 and NucLibB are untouched. Two parents and different ratio units limit inference. This diagnostic is not another independent test.

## Frozen pretrained comparator after simple models

| dataset | model | components | decision_sets | regret | avoidable_wrong | pairwise_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| mikl_gse173098 | frozen_bert_plus_kmer | 177 | 4799 | 0.49414 | 0.19157 | 0.50396 |
| moffatt_gse334718 | frozen_bert_plus_kmer | 6 | 12 | 0.43810 | 0.41667 | 0.51615 |
| mikl_gse173098 | matched_kmer123 | 177 | 4799 | 0.50999 | 0.20030 | 0.49003 |
| moffatt_gse334718 | matched_kmer123 | 6 | 12 | 0.47190 | 0.41667 | 0.50918 |
| mikl_gse173098 | uniform | 177 | 4799 | 0.50000 | 0.19476 | 0.50000 |
| moffatt_gse334718 | uniform | 6 | 12 | 0.50000 | 0.50000 | 0.50000 |

This comparison uses 20,474 exact cached 3UTRBERT rows on complete Mikl/Moffatt decision contexts, with identical candidate sets for both models. The frozen encoder was not retrained; absent SRLE/astrocyte embeddings were not zero-filled. It is a restricted two-study result and cannot pass the four-study gate. Encoder inference and mixed-runtime provenance limitations are inherited from the original cache. A correlation gain alone is not counted as successful candidate selection.

There is a positive secondary lead: adding the frozen embeddings reduced regret from **0.509985 to 0.494135 in Mikl** and from **0.471899 to 0.438099 in Moffatt**, relative to matched short-k-mer rankers. This does not establish superiority over all simple baselines in a new experiment. It motivates a specific future question about longer-context representations within projection-localization assays, not an immediate new-data search or a replacement of the failed gate.

## Replay and scope

All 288,838 core score rows reproduced from frozen parameters (maximum error 0); 8 independent fresh fits reproduced their predictions (maximum error 0). 119,592 selections were independently checked. Eleven scoped tests passed. Frozen historical bundles and unrelated user files remain unchanged. Full predictions join by `intervention_id` to exact parent/mutant sequences, raw features, normalization parameters, universal/residual scores, uncertainty diagnostics and observed effects.
