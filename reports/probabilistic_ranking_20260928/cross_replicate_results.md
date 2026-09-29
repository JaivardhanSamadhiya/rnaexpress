# Measurement robustness and decision reproducibility

All studies are exposed development data. Biological breadth is unequal: one SRLE reporter, two astrocyte genes, six Moffatt parent/gene groups, and 187 Mikl genes. Variant counts do not supply independent biological experiments. The prior cross-assay NO-GO is unchanged.

## Fit one replicate subset, evaluate the other

Alternating source slots define A/B, with both role directions retained. Models use only the training slots to construct labels and estimate noise. H0 in this diagnostic is hard training-replicate-mean preference; it is not the author aggregate that includes the evaluation subset. The same parents and sequences occur on both sides: these results test measurement robustness, not unseen biological contexts. SRLE and one Mikl orientation have only one training replicate, so P3 cannot identify within-pair variance and explicitly falls back to P2. Moffatt has no admitted paired contrasts and is ineligible.

| model | dataset | regret | pairwise_accuracy | wrong_direction | avoidable_wrong |
| --- | --- | --- | --- | --- | --- |
| H0 | astrocyte_gse330741 | 0.47547 | 0.52684 | 0.46875 | 0.42708 |
| H0 | mikl_gse173098 | 0.46448 | 0.53505 | 0.49116 | 0.20341 |
| H0 | srle | 0.19912 | 0.76205 | 0.32644 | 0.07981 |
| P1 | astrocyte_gse330741 | 0.41791 | 0.53455 | 0.39583 | 0.35417 |
| P1 | mikl_gse173098 | 0.46245 | 0.53715 | 0.48887 | 0.20129 |
| P1 | srle | 0.19912 | 0.76205 | 0.32644 | 0.07981 |
| P2 | astrocyte_gse330741 | 0.41791 | 0.53458 | 0.39583 | 0.35417 |
| P2 | mikl_gse173098 | 0.46145 | 0.53810 | 0.48799 | 0.20041 |
| P2 | srle | 0.19443 | 0.76621 | 0.32348 | 0.07686 |
| P3 | astrocyte_gse330741 | 0.45665 | 0.53100 | 0.50000 | 0.45833 |
| P3 | mikl_gse173098 | 0.45594 | 0.54402 | 0.48566 | 0.19838 |
| P3 | srle | 0.19443 | 0.76621 | 0.32348 | 0.07686 |

The table averages both directions of replicate splitting at the parent/component level. Role-specific decisions and calibration remain in the complete CSVs.

## Same-target comparison with empirical cross-replicate decision reproducibility

| stage | model | dataset | model_regret | uniform_regret | replicate_regret | wrong_direction | fraction_recovered |
| --- | --- | --- | --- | --- | --- | --- | --- |
| held_assay | H0 | astrocyte_gse330741 | 0.50183 | 0.50000 | 0.35181 | 0.48810 | -0.01233 |
| held_assay | H0 | mikl_gse173098 | 0.50353 | 0.50000 | 0.43333 | 0.50697 | -0.05296 |
| held_assay | H0 | srle | 0.51133 | 0.50000 | 0.18357 | 0.50802 | -0.03579 |
| held_assay | P1 | astrocyte_gse330741 | 0.50589 | 0.50000 | 0.35181 | 0.50149 | -0.03975 |
| held_assay | P1 | mikl_gse173098 | 0.49813 | 0.50000 | 0.43333 | 0.50017 | 0.02802 |
| held_assay | P1 | srle | 0.52705 | 0.50000 | 0.18357 | 0.49916 | -0.08548 |
| held_assay | P2 | astrocyte_gse330741 | 0.50589 | 0.50000 | 0.35181 | 0.50149 | -0.03975 |
| held_assay | P2 | mikl_gse173098 | 0.50451 | 0.50000 | 0.43333 | 0.50298 | -0.06759 |
| held_assay | P2 | srle | 0.52206 | 0.50000 | 0.18357 | 0.49873 | -0.06970 |
| held_assay | P3 | astrocyte_gse330741 | 0.50106 | 0.50000 | 0.35181 | 0.49256 | -0.00716 |
| held_assay | P3 | mikl_gse173098 | 0.49921 | 0.50000 | 0.43333 | 0.50176 | 0.01178 |
| held_assay | P3 | srle | 0.48224 | 0.50000 | 0.18357 | 0.47804 | 0.05612 |

Every comparison above uses the identical finite candidate subset and omitted raw replicate endpoint. Sequence models were fitted on other biological studies; the empirical reference selects using the other measured replicates of the test assay. This empirical reference is outcome-informed, not deployable, not a theoretical optimum and not independent confirmation. Its regret exactly reproduces the preceding failure audit. The fractional recovery uses a positive uniform-minus-replicate denominator and can be negative or exceed one. It never replaces primary aggregate-target regret, and is not computed by mixing raw-replicate and author-aggregate scales.
