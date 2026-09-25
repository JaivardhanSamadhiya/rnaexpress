# Independent review of fixed-choice risk aggregates

24 September 2026. AI-authored technical audit, not student submission prose.
This review read only the completed diagnostic's result JSON and its anonymous
per-class `groups` and `pairs` CSV exports under `results/research_20260921`.
No source decision rows, sequence identities, new outcomes or raw reads were
opened; no models were fitted and no choices or thresholds were changed.

## Verification

An independent arithmetic implementation using Python's standard-library CSV,
`math.fsum` and explicit linear-interpolation quantiles reproduced all 152
reported summary statistics and their 304 interval endpoints. Maximum absolute
difference across 456 comparisons was 3.3306690738754696e-16. NumPy 1.26.4 was
used solely to reproduce the specified PCG64/default_rng(20260921) bootstrap
indices: 2,000 draws of 60 composition classes, shared across all summaries.

Both CSV SHA-256 values match the result JSON. There are 960 per-replicate class
rows and 480 paired-class rows. Keys are unique; every class has the same parent
count across model, direction and replicate; class counts sum to 592 parents.
All positive/negative/tie partitions sum to one. Paired positive and negative
fractions do not exceed their individual-replicate margins; paired minimum means
do not exceed either individual-replicate mean. Thresholded fractions are bounded
by their corresponding sign fractions, and reported mean losses are nonnegative.

These checks verify the exported aggregation and arithmetic. Anonymous tables
cannot independently prove the original row-level identity matching; that was
checked separately in the pre-execution source review. No such identity claim is
inferred from marginal arithmetic alone.

## Interpretation of the position-pair policy

Percentages below are equal-composition-class averages of within-class fractions,
not unweighted percentages of the 592 parents.

| Requested direction | Mean directed change, replicate 1 / 2 | Negative directed change, replicate 1 / 2 | Positive in both | Negative in both |
| --- | ---: | ---: | ---: | ---: |
| Decrease NRS | 0.13154 / 0.12426 | 33.54% / 36.28% | 50.96% | 20.78% |
| Increase NRS | 0.09990 / 0.11498 | 33.96% / 32.63% | 56.98% | 23.57% |

Both direction-specific means are positive in each constituent replicate, while
substantial fractions of fixed choices move away from the requested direction.
Thus the earlier positive symmetric average does not imply reliable improvement
for every parent. The two direction means recombine to 0.11571673922291159 and
0.11961739041267011 in the respective replicates. The execution result reports
agreement with the archived bidirectional means within 2.78e-17; this review
independently recombined the anonymous aggregates but did not reopen the earlier
archive to repeat that separate historical comparison.

"Negative directed change" means movement away from the requested NRS direction.
For an increase request it means NRS decreased; for a decrease request it means
NRS increased. It is not evidence of biological harm, toxicity, disease risk or
an adverse cellular phenotype. NRS is the assay score, not the cellular fraction
of RNA in a compartment.

The class-weighted mean of the smaller of the two changes is 0.03678 for decrease
requests, with descriptive interval [0.00250, 0.07823], and 0.01297 for increase
requests, with interval [-0.03851, 0.05661]. This statistic is the average observed
minimum across two constituent replicates. It is not a lower confidence bound,
a guarantee for a future experiment or a worst-case biological effect.

The fixed 0.1 log2-score threshold is descriptive, not a validated threshold of
biological importance. All intervals remain conditional on existing training and
fixed decisions; no multiple-comparison significance selection is supported.
The shared experimental provenance prevents independent-confirmation claims.
All other models, unfavorable results and earlier failed gates remain part of
the evidence record. This audit changes no gate or frozen artifact.
