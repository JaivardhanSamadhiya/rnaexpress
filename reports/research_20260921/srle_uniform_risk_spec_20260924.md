# Exact uniform-candidate reference for fixed-choice risk

Post hoc comparator audit, specified after the existing risk findings and before
this reference was computed. No new gate, selector, threshold, outcome opening
or independent confirmation is created. Original choices and findings remain.

## Purpose and scope

The fixed-choice risk report uses a deterministic lexical composition baseline.
It is not a uniformly randomized choice. Neither 50% per-replicate benefit nor
25% benefit in both replicates is automatically the chance level for these
measured, correlated candidate sets. Compute the exact relevant expectation.

Use only already-open saved records: raw_replication_scores.csv,
robustness_predictions.csv (sequence identifiers and test membership only),
robustness_swap_predictions.csv, raw_swap_evaluation.csv, and the committed
anonymous fixed-choice risk exports/result. Verify their existing hashes and
freeze all code, tests, dependencies and this specification before execution.
Do not reopen the source workbook, raw reads, external or protected data.

## Cohort reconstruction without new sequence design

Identify eligible test sequences from the original saved partition, requiring
the original two train and two test sequences per exact composition class.
For each originally retained parent, identify its candidates among these existing
measured identifiers by identical composition and Hamming distance exactly two.
For equal-length strings with identical composition, two differing positions
necessarily exchange unequal bases; this independently reconstructs single swaps.
Generate no new sequences and export no sequence recommendations or identities.

Check original candidate counts, saved selected membership and exact saved
choice identity for every model/direction. Verify all candidates and parents
pass the old raw-count eligibility rule, the retained cohort is exactly 592
parents in 60 classes, and every saved per-replicate directed change and regret
gain reconstructs within 1e-12. Preserve the old zero-range and coverage scope;
do not add or remove parents after inspecting the new comparator.

## Exact reference and comparisons

For each retained parent and requested direction, uniformly weight its distinct
original candidates. A single candidate identity is held fixed across both
replicates. Evaluate each candidate's directed parent-relative changes, using
the existing risk definitions, 1e-12 numerical tie tolerance and 0.1 descriptive
log2-score scale. Compute nonlinear quantities (sign indicators, thresholded
indicators, loss, paired sign categories, and the smaller change) per candidate
BEFORE averaging. Do not take the minimum or classify the average change.

Average candidates within each parent, parents within composition class, then
the 60 classes equally. Never pool all candidates across parents, and never draw
independent candidate identities for the two replicates. Exact enumeration adds
no Monte Carlo selection noise. The reference still forces a swap; it is not an
abstention option or a model trained to improve the published results.

Retain all seven per-replicate and five paired metrics from the risk audit, for
both directions and every model. Report reference values and paired class-level
**model minus uniform** contrasts, always using that literal subtraction. Positive
contrasts favor the model for mean change and benefit fractions; negative
contrasts favor the model for wrong-direction fractions and mean loss. Numerical
ties and replicate disagreements have no assigned superiority criterion.

Use the original sorted class order and common NumPy default_rng(20260921)
bootstrap indices: 2,000 draws of 60 classes. Descriptive 95% intervals use linear
quantiles and condition on the already-fitted models and experiment. No p-values,
multiple-comparison significance selection, new pass/fail gate, threshold search
or model retuning. Export anonymous class metrics and every summary.

After this missing-comparator check, stop expanding same-data diagnostics merely
to obtain a stronger positive. It cannot resolve independent validation or the
missing original Table 5 production chain. Original closed outcomes stay closed.
