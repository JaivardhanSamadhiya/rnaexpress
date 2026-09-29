# A specific follow-up hypothesis, not an active validation protocol

The prior four-study gate remains NO-GO. The diagnostic shows that raw replicate-level candidate ordering can be weak while choosing candidates with other replicates still improves over uniform selection. This motivates testing whether the hard preference target is discarding reliability information. It does not demonstrate that this explains failed sequence-model transfer.

**Falsifiable hypothesis:** a fixed sequence representation trained on replicated preference probabilities will transfer better than the same representation trained on a single deterministic preference label, because inconsistent source preferences exert less directional pressure on the fitted coefficients.

For an allowed training pair A/B, define q as the fraction of common finite replicate contrasts in which A exceeds B, with a half vote for a tie. Minimize logistic cross-entropy against q. This is an empirical vote fraction, not a calibrated posterior probability or a confidence interval. Do not infer certainty from three replicates, and do not treat repeated candidate pairs or shared WT contrasts as independent biological observations.

A meaningful comparison must include all three label constructions on identical candidates, features, pair samples, folds and loss weights:

1. The existing hard author/aggregate preference.
2. Hard preference from the mean admitted raw replicate contrast.
3. Soft preference from the replicate votes.

Arm 2 is essential: otherwise a difference caused by changing the outcome estimator could be misattributed to uncertainty handling. For missing paired replicate data, notably Moffatt, retain the original author label in all arms and disclose that the source supplies no uncertainty contrast. Do not fabricate replicates or select only reliable-looking candidates. Freeze treatment of missing shared replicates before execution.

Use one existing short-k-mer representation, fixed regularization and the original study/component/context balancing; do not combine this question with a new architecture or window search. Hold out entire assays with the original gene/allele purge. **No held-out replicate, reliability estimate or outcome may influence fitting, preprocessing or pair weighting.** Evaluate every original candidate and all four original study endpoints. Comparisons use the original strongest-simple baseline envelope and unchanged four-study gate. Keep the author-processed primary target, with raw-repeatability diagnostics explicitly secondary.

Evidence against this hypothesis would be no distributed held-study improvement over the hard-author arm, no benefit beyond the hard-raw-mean arm, or continued failure of the original gate. Improved source fit alone is insufficient. Source replicate weighting cannot cure absent parent context, endpoint-specific mechanisms, systematic measurement biases or insufficient biological diversity.

This document is a proposal only: no such models were fitted in this diagnostic, no new development gate was declared passed, and no independent-dataset search was authorized by a result. A separate committed executable protocol is needed before that comparison. Any eventual development success would still require genuinely untouched confirmation.
