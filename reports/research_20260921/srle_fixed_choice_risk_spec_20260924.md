# Fixed-choice direction and consistency audit

Written 24 September 2026 after the aggregate results and methods review were
known, before computing these diagnostic summaries. This is a post hoc audit
of already-open saved records, not independent confirmation or a new gate.

## Input and boundary

Use only results/research_20260921/raw_swap_evaluation.csv, SHA-256
7aff528234b2dff858d4d87fad4dbeee8fe709a8c4fe343705955ab3d2e46a69.
It contains fixed choices for 592 parent six-mers, four models, two directions
and two previously reconstructed constituent replicates (9,472 rows). Verify
the earlier checkpoint hash, balanced keys, and unchanged selected identifiers
between replicates. Do not reopen source workbooks, raw reads, reserved labels,
or training code; do not refit, select alternatives, optimize thresholds or
create an abstention policy. Do not output sequence identifiers.

## Why this audit is needed

For direction d, the saved directed change is d times (selected NRS - parent NRS).
The mean across the two directions equals (NRS of the upward choice minus NRS
of the downward choice)/2. The parent cancels. Thus a positive two-direction
average does not establish that both choices improve over their own parent.
This audit separates the directions and measures harmful choices explicitly.

## Fixed descriptive summaries

For each model, direction and replicate, calculate the following within each
composition class and then weight the 60 classes equally:

- Mean directed NRS change.
- Fraction of parent decisions with positive, negative or numerically tied
  directed change. Use tolerance 1e-12 solely for numerical ties, not a biological
  improvement threshold. Negative means movement away from the requested target.
- Mean loss counting beneficial/tied choices as zero: mean(max(-change, 0)).
- Fraction with benefit of at least 0.1 log2-score units, and fraction with harm
  of at least 0.1 log2-score units. This is a fixed descriptive scale, not a gate
  or a validated biological-importance threshold; do not choose it from results.

Match identical fixed decisions across replicates. For each model and direction,
report the equally weighted fractions positive in both, negative in both,
strictly opposite signs, and the remainder involving numerical ties. Also report
the class-weighted mean of the smaller of the two directed changes. These are
consistency diagnostics in constituent experiments, not new independent tests.

Bootstrap whole composition classes with exactly the existing sorted class order,
NumPy default_rng(20260921), 2,000 samples of 60 classes. Use the same draws for
every model/direction/replicate. Report descriptive 95% linear-quantile intervals
for all summaries; no p-values, significance selection or pass/fail declaration.
Intervals omit full training uncertainty and share the training experiment.

Export anonymous per-class metrics and full summaries, preserving all models and
directions even if unfavorable. Record source, spec, code and output hashes.
Check that the direction-specific mean changes recombine to the previously
archived two-direction means within 1e-12. Original records remain unchanged.
