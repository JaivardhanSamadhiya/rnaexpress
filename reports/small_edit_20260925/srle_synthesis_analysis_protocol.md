# Fixed interpretation and recommendation analysis plan

26 September 2026; additive to commits 0023b01 and e5b9288. All SRLE outcomes and previous results are exposed. This is an exploratory interpretation and bounded software demonstration, not a new primary test. Preserve historical inputs, models, predictions, memberships and metrics. No external requests, new dataset discovery, provenance search, architecture search or rescue of the pair model.

## Reconstruction first

Compare every file changed by 0023b01/e5b9288 with its committed bytes; verify the complete 41-file SRLE evidence bundle. In a fresh interpreter and new output namespace, reconstruct all 141 fixed training partitions from the original input table with the unchanged model code, alpha=10 and original masks. Compare all 17,955 predictions with saved values to 1e-12. Independently recalculate the historical score reduction, strict-purge 2-mer effect reduction and original 2,000-group-bootstrap interval, primary pair failure, kmer123/uniform regret and wrong-both rate. Repeat only the 82 established scoped tests. This is a fixed reproduction, not a new model attempt.

## Exact edits and interpretation

Use every one of the original 1,744 links, 592 anchors and 60 candidate composition groups. Verify two changed positions, an exact unequal-base exchange, six-position window and identical base counts. Export endpoint and difference counts for 1-, 2- and 3-mers, positional neighborhoods and recorded score/replicate deltas. Count cases where delta 2-mer is zero; do not assume every swap changes adjacency counts. Examples: lexical first zero-delta-2-mer pair (if present), lexical first nonzero pair, then deterministic median examples.

For each saved purged fold, transform 2-mer weights into count units, beta_j=coefficient_j/scale_j. For each edit reconstruct the delta as sum(delta_count_j*beta_j). Intercepts, scaler centering and the shared composition baseline cancel. Export all 16 contributions, raw coefficients and fold identities. Also center beta across the 16 features for presentation; delta 2-mer counts sum to zero, so this gauge change preserves prediction. Quantify contribution concentration using absolute centered contributions; show raw attribution too. Coefficient medians/IQR/sign consistency across 70 held groups (and the 60 candidate groups) describe overlapping fitted models, not independent biological-population confidence intervals. Feature correlations/regularization prevent causal interpretation of coefficient size.

## Fixed order controls

Keep all original seven models. No-change and composition have identical predicted edit delta; no refit is needed. A feature-column renaming/permutation with correspondingly permuted weights must leave predictions unchanged and is not a null.

Run only the following new controls, on the same 60 purged candidate-group splits and the original published-score training residuals, with alpha=10 and training-only standardization:

1. Fixed position order [0,2,4,1,3,5] before 2-mer counting, consistently in training/testing. This preserves composition/dimension while replacing adjacent-base relationships. It still contains sequence-order information and is a representation control, not an independent biological null.
2. Sixteen deterministic standard-normal features per sequence from SHA-256-seeded generator (`srle-synthesis-random16-20260926|sequence`). This is a comparable-dimensional feature control without k-mer identity; no seed choice.
3. Thirty-two training-label permutations, all retained. Seeds 2026092600 through 2026092631. Permute residual labels only within each ORIGINAL TRAINING composition class, then apply the unchanged whole-class/purge exclusions; held-out outcomes never enter the shuffle. Preserve composition means. Fit only the original 2-mer representation. Report every null replicate and the null distribution; do not retry or pick a favorable seed, and do not interpret this limited control as a new confirmatory test.

Compare measured delta MSE and directional/ranking measures for published, replicate1 and replicate2 targets. Use paired resampling of the same 60 composition classes with seed 20260926 and 2,000 draws for descriptive loss contrasts. A control retaining signal does not disprove the real model; explain which information it retains. No adjustments of the frozen model follow these outcomes.

## Similarity and extrapolation

For each of the 855 held-out local sequences, use its original purged training mask. Compute exact nearest-training Hamming and global Levenshtein distances, composition-count L1 distance, 2-mer count L1/cosine distance and 3-mer count L1 distance. The full local window is the six-mer, so window Hamming is the same measure, not a second validation. Save nearest IDs and training counts. Also flag each feature outside training min/max and its excess; these are descriptive extrapolation checks, not calibrated uncertainty.

Attach endpoint minima/maxima to all 1,744 edits. Report effect error/relative MSE improvement against the exact integer distance levels, with group counts and cluster intervals when >=5 groups; otherwise mark intervals insufficient. Use continuous descriptive associations too. If a distance is constant, state that no performance gradient can be estimated. Do not invent favorable distance thresholds after inspecting scores.

## Failures, reliability and recommendation

Use the original strict-purge predictions and all candidate sets. Export per-edit feature/distance/error records. Preset magnitude bins: <=0.1, 0.1–0.25, 0.25–0.5, >0.5, for measured and predicted magnitude and replicate disagreement. Retain every example. Analyze direction success/failure, dinucleotide changes, composition groups, count-range extrapolation and candidate size descriptively; no post-hoc filter changes the primary metric.

Use NRS1/NRS2 as constituents of the same experiment. Report delta Pearson/Spearman/sign agreement, within-parent candidate-rank agreement, and lexical best-candidate identity agreement for both requested directions. Evaluate replicate1-selected choices on replicate2 and vice versa as **reliability benchmarks**, not independent validation or an absolute ceiling.

For each parent/direction, compute whether a both-correct candidate exists, whether any candidate avoids wrong-both, and whether every candidate is wrong-both. Partition the frozen recommender's wrong-both choices into (a) a both-correct alternative existed, (b) another non-wrong-both alternative existed but none both-correct, and (c) every candidate was wrong-both. This quantifies avoidable errors under the measured roster and forced-choice limitations; it does not causally attribute all error to measurement noise. No abstention/reference option is retroactively added.

Export every candidate with endpoint changes, all frozen models, both directions, ranks and measurement outcomes. Keep exact uniform expectations as distributions/selection probabilities rather than pretending a random seed is the policy. Summarize class-balanced means and bootstrap intervals, raw-decision median/quantiles (explicitly descriptive), best recovery, meaningful top3 only for >3 candidates, and fraction of decisions better than their exact uniform expected regret. Stratify by candidate count and fixed effect bins, retaining denominators. Existing 2mer/kmer123/pair comparisons remain paired and all negative findings remain visible.

## Confidence analysis — exploratory only

For 2mer and kmer123, retain exactly 100/80/60/40/20% of the original parent/direction units ranked by each prespecified prediction/design-only signal: larger top-two predicted margin; larger desired-direction predicted change; smaller 2mer-versus-3mer disagreement on the selected candidate; smaller nearest-training 2-mer distance (using the worse endpoint); and fewer out-of-range count features. Break signal ties lexically by parent then direction. Thresholds use held-out covariates/predictions to achieve fixed coverage, never outcomes. These are exploratory risk-coverage curves, not development-calibrated or independently validated abstention thresholds. Report all five signals/all coverages and group counts, even if nonmonotonic or adverse. No curve winner becomes a deployed confidence guarantee.

## Prototype and local context audit

Use kmer123 as the default ranking demonstration based on the already-known frozen point estimates, with 2mer available for quantitative comparison. This is not a new model selection or proof of unique superiority. The prototype replays frozen predictions for complete original measured candidate sets only, verifies them against saved coefficients, refuses new/out-of-roster tasks, and contains no experimental outcomes in its runtime bundle. It supplies cohort risk with explicit non-individual scope; no confidence threshold is deployed. Normalize U/T identifiers consistently and require a valid six-mer, equal composition and an exact two-position swap.

Audit known local manifests/exposure inventories and permitted metadata only. Classify all known sources; do not open protected outcome files or unknown supplementary members. A second cell or replicate from already-exposed data is not independent confirmation. If no untouched admitted resource qualifies, document the scoped local finding, not a global absence. No external request is authorized.

## Figures, evidence and stopping

Produce eight saved-output figures covering task/edit geometry, strict quantitative predictions including pair failure, all feature controls, coefficient/contribution stability, recommendation regret distribution, directional/joint risk, similarity gradients, and four examples. Example rule for the default kmer123 recommender: separately for increase/decrease, median average replicate regret among correct-both choices and among wrong-both choices; tie parent then selected sequence lexically. No hand-picked favorites.

Create one evidence table with targets, units, models, metrics, intervals, exposure/split status, one biological context and artifact pointers. Final synthesis answers all 15 requested questions and distinguishes predictive structure from mechanism. Stop after the frozen interpretation/control batch, saved-output analyses, bounded prototype, verification and deliverables. New code may be added for reporting after the analysis plan; no scientific choice is revised based on a favorable result.
