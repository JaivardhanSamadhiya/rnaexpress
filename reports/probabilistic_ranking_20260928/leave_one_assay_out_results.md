# Whole-study probabilistic-supervision comparison

**NO-GO: no primary probabilistic supervision method passed the frozen decision gate.**

All studies are exposed development data. Biological breadth is unequal: one SRLE reporter, two astrocyte genes, six Moffatt parent/gene groups, and 187 Mikl genes. Variant counts do not supply independent biological experiments. The prior cross-assay NO-GO is unchanged.

The protocol was committed at `1c1f387`, and the executable/data prefit freeze at `033c316`, before comparative fits. All original whole-study and held-parent train/test hashes were retained. H0 coefficients reproduced the historical interaction_3 fits; all 26,258 held-study scores and 10,872 selected decisions were checked against the original baseline. P1/P2/P3 retain the same 246 features, latent utility, regularization, pair samples and biological weighting. No held-study measurements enter targets, noise, fitting or scaling.

## Primary controlled comparison

| model | dataset | regret | wrong_direction | avoidable_wrong | pairwise_accuracy | spearman | correct_direction | best_recovery | top5_best_recovery | variant_weighted_regret |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H0 | astrocyte_gse330741 | 0.46987 | 0.50000 | 0.50000 | 0.49632 | -0.01102 | 0.50000 | 0.00000 | 0.00000 | 0.46712 |
| H0 | mikl_gse173098 | 0.51718 | 0.50610 | 0.19812 | 0.48250 | -0.03517 | 0.49168 | 0.42371 | 0.99509 | 0.49634 |
| H0 | moffatt_gse334718 | 0.44851 | 0.41667 | 0.41667 | 0.51795 | 0.05397 | 0.58333 | 0.04167 | 0.04167 | 0.43786 |
| H0 | srle | 0.51734 | 0.51098 | 0.26689 | 0.48358 | -0.03780 | 0.48902 | 0.35980 | 0.99662 | 0.52227 |
| P1 | astrocyte_gse330741 | 0.50756 | 0.50000 | 0.50000 | 0.50237 | 0.00798 | 0.50000 | 0.00000 | 0.00000 | 0.51026 |
| P1 | mikl_gse173098 | 0.50433 | 0.50297 | 0.19503 | 0.49351 | -0.01131 | 0.49491 | 0.43651 | 0.99530 | 0.49399 |
| P1 | moffatt_gse334718 | 0.47178 | 0.37500 | 0.37500 | 0.51348 | 0.03992 | 0.62500 | 0.04167 | 0.04167 | 0.47736 |
| P1 | srle | 0.52857 | 0.51014 | 0.26605 | 0.47851 | -0.04545 | 0.48986 | 0.35220 | 0.99409 | 0.53548 |
| P2 | astrocyte_gse330741 | 0.50756 | 0.50000 | 0.50000 | 0.50224 | 0.00767 | 0.50000 | 0.00000 | 0.00000 | 0.51026 |
| P2 | mikl_gse173098 | 0.50461 | 0.50769 | 0.19974 | 0.49322 | -0.01201 | 0.49023 | 0.43620 | 0.99632 | 0.49223 |
| P2 | moffatt_gse334718 | 0.48371 | 0.37500 | 0.37500 | 0.51519 | 0.04526 | 0.62500 | 0.04167 | 0.04167 | 0.49267 |
| P2 | srle | 0.52700 | 0.50676 | 0.26267 | 0.47676 | -0.05042 | 0.49324 | 0.34797 | 0.99493 | 0.52945 |
| P3 | astrocyte_gse330741 | 0.51389 | 0.50000 | 0.50000 | 0.50280 | 0.00860 | 0.50000 | 0.00000 | 0.00000 | 0.51751 |
| P3 | mikl_gse173098 | 0.50138 | 0.49864 | 0.19069 | 0.49715 | -0.00598 | 0.49925 | 0.43931 | 0.99534 | 0.49112 |
| P3 | moffatt_gse334718 | 0.46474 | 0.41667 | 0.41667 | 0.51337 | 0.03937 | 0.58333 | 0.00000 | 0.04167 | 0.47814 |
| P3 | srle | 0.47768 | 0.47466 | 0.23057 | 0.52284 | 0.04602 | 0.52534 | 0.39696 | 0.99578 | 0.48889 |

## Strongest simple comparators preserved from the original grid

| dataset | model | regret | wrong_direction | avoidable_wrong |
| --- | --- | --- | --- | --- |
| astrocyte_gse330741 | uniform | 0.50000 | 0.50000 | 0.50000 |
| mikl_gse173098 | composition | 0.48747 | 0.49153 | 0.18414 |
| moffatt_gse334718 | uniform | 0.50000 | 0.50000 | 0.50000 |
| srle | uniform | 0.50000 | 0.50000 | 0.25591 |

## All fixed secondary comparisons

| model | dataset | regret | wrong_direction | avoidable_wrong | pairwise_accuracy | spearman |
| --- | --- | --- | --- | --- | --- | --- |
| H0_pairfree | astrocyte_gse330741 | 0.51876 | 0.56250 | 0.56250 | 0.49601 | -0.01123 |
| H0_pairfree | mikl_gse173098 | 0.50982 | 0.50606 | 0.19812 | 0.49182 | -0.01759 |
| H0_pairfree | moffatt_gse334718 | 0.44447 | 0.41667 | 0.41667 | 0.51762 | 0.05319 |
| H0_pairfree | srle | 0.51049 | 0.51351 | 0.26943 | 0.48842 | -0.02189 |
| Hraw | astrocyte_gse330741 | 0.49450 | 0.50000 | 0.50000 | 0.49914 | -0.00282 |
| Hraw | mikl_gse173098 | 0.50869 | 0.50392 | 0.19594 | 0.49048 | -0.01940 |
| Hraw | moffatt_gse334718 | 0.49043 | 0.45833 | 0.45833 | 0.50920 | 0.02739 |
| Hraw | srle | 0.48925 | 0.48564 | 0.24155 | 0.51226 | 0.02315 |
| P2_pairfree | astrocyte_gse330741 | 0.47925 | 0.43750 | 0.43750 | 0.50028 | 0.00167 |
| P2_pairfree | mikl_gse173098 | 0.50411 | 0.50603 | 0.19808 | 0.49502 | -0.01060 |
| P2_pairfree | moffatt_gse334718 | 0.48371 | 0.37500 | 0.37500 | 0.51465 | 0.04364 |
| P2_pairfree | srle | 0.51487 | 0.51436 | 0.27027 | 0.48509 | -0.02978 |
| P2_weighted | astrocyte_gse330741 | 0.50756 | 0.50000 | 0.50000 | 0.50254 | 0.00812 |
| P2_weighted | mikl_gse173098 | 0.50645 | 0.50657 | 0.19863 | 0.49156 | -0.01576 |
| P2_weighted | moffatt_gse334718 | 0.48754 | 0.37500 | 0.37500 | 0.51431 | 0.04258 |
| P2_weighted | srle | 0.52379 | 0.50591 | 0.26182 | 0.47907 | -0.04383 |
| P3_hetero | astrocyte_gse330741 | 0.48714 | 0.43750 | 0.43750 | 0.49961 | -0.00157 |
| P3_hetero | mikl_gse173098 | 0.49653 | 0.50575 | 0.19720 | 0.50275 | 0.00483 |
| P3_hetero | moffatt_gse334718 | 0.48387 | 0.41667 | 0.41667 | 0.51332 | 0.04007 |
| P3_hetero | srle | 0.46105 | 0.46537 | 0.22128 | 0.53764 | 0.07735 |
| Partial | astrocyte_gse330741 | 0.49292 | 0.41667 | 0.41667 | 0.49781 | -0.00556 |
| Partial | mikl_gse173098 | 0.52324 | 0.51087 | 0.20294 | 0.47595 | -0.04624 |
| Partial | moffatt_gse334718 | 0.49118 | 0.50000 | 0.50000 | 0.51192 | 0.03554 |
| Partial | srle | 0.47980 | 0.48311 | 0.23902 | 0.52056 | 0.04443 |

Hraw changes the estimator without soft supervision; P2_weighted isolates the declared reliability weighting; Partial deliberately removes uncertain training constraints and records its changed training cohort. H0_pairfree/P2_pairfree add the same 17 antisymmetric metadata wedges and use expected wins, while P3_hetero uses one source-trained measurement-noise head and probit probabilities. These are separately labeled secondary tests. They cannot rescue failure of the primary H0/P1/P2/P3 question, and no successful-looking secondary subgroup was promoted after results.

## Failure categories and ambiguity

| model | dataset | wrong_direction | avoidable_wrong | unavoidable_wrong | neutral_only_alternative_wrong | no_feasible_candidate | measurement_ambiguous_fraction | measurement_unavailable_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H0 | astrocyte_gse330741 | 0.50000 | 0.50000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 | 0.00000 |
| H0 | mikl_gse173098 | 0.50610 | 0.19812 | 0.30690 | 0.00108 | 0.30893 | 0.73441 | 0.00000 |
| H0 | moffatt_gse334718 | 0.41667 | 0.41667 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 |
| H0 | srle | 0.51098 | 0.26689 | 0.24409 | 0.00000 | 0.24409 | 0.29223 | 0.00000 |
| P1 | astrocyte_gse330741 | 0.50000 | 0.50000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 | 0.00000 |
| P1 | mikl_gse173098 | 0.50297 | 0.19503 | 0.30690 | 0.00105 | 0.30893 | 0.73441 | 0.00000 |
| P1 | moffatt_gse334718 | 0.37500 | 0.37500 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 |
| P1 | srle | 0.51014 | 0.26605 | 0.24409 | 0.00000 | 0.24409 | 0.29223 | 0.00000 |
| P2 | astrocyte_gse330741 | 0.50000 | 0.50000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 | 0.00000 |
| P2 | mikl_gse173098 | 0.50769 | 0.19974 | 0.30690 | 0.00105 | 0.30893 | 0.73441 | 0.00000 |
| P2 | moffatt_gse334718 | 0.37500 | 0.37500 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 |
| P2 | srle | 0.50676 | 0.26267 | 0.24409 | 0.00000 | 0.24409 | 0.29223 | 0.00000 |
| P3 | astrocyte_gse330741 | 0.50000 | 0.50000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 | 0.00000 |
| P3 | mikl_gse173098 | 0.49864 | 0.19069 | 0.30690 | 0.00105 | 0.30893 | 0.73441 | 0.00000 |
| P3 | moffatt_gse334718 | 0.41667 | 0.41667 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 1.00000 |
| P3 | srle | 0.47466 | 0.23057 | 0.24409 | 0.00000 | 0.24409 | 0.29223 | 0.00000 |

Overall wrong direction equals avoidable + all-candidates-wrong + neutral-only-alternative wrong direction. Measurement ambiguity is a separate overlapping diagnostic: no candidate has replicate posterior superiority >=0.9 against every alternative with >=2 common replicates. It never erases a measured error. Missing replicate support is UNAVAILABLE, not proof of ambiguity or reliability. A no-feasible-candidate set may contain neutral edits and is therefore not always an all-wrong set.

## Was the gain greater in noisier assays?

| model | assays | reliability_vs_gain_spearman | interpretation |
| --- | --- | --- | --- |
| P1 | 3 | 0.50000 | prespecified descriptive n=3 association, not mechanism or selection criterion |
| P2 | 3 | 0.50000 | prespecified descriptive n=3 association, not mechanism or selection criterion |
| P3 | 3 | 1.00000 | prespecified descriptive n=3 association, not mechanism or selection criterion |

This prespecified association has only three assays. It cannot prove a noise mechanism, supply a reliable population correlation, or select a model. Raw outcomes, complete probability predictions, candidate rankings and fold-wise calibration are preserved.
