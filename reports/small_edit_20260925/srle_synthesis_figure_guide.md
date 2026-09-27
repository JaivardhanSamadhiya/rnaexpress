# SRLE final figure guide

All plots use saved predictions and summaries, one biological context. PNG at 210 dpi and scalable SVG are supplied. Final layouts were visually inspected; Figure 1 text placement was corrected without changing data.

## figure01_task

Lexical first nonzero Δ2-mer example, not selected for outcome. DNA T encoding denotes the local RNA sequence. Only two positions change. Outcomes are revealed after frozen scoring; the original roster itself was historically coverage/outcome-conditioned.

[PNG](../../artifacts\srle_synthesis_20260926\figure01_task.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure01_task.svg)

## figure02_quantitative

All 1,744 directed links. Same axes expose pair-model overdispersion. Composition predicts zero effect. Fixed original held-out scores; no recalibration.

[PNG](../../artifacts\srle_synthesis_20260926\figure02_quantitative.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure02_quantitative.svg)

## figure03_features_controls

Original 95% descriptive composition-class intervals. Every fixed label null displayed; jitter is deterministic display spacing, not data. Shuffled positions retain other order information and are a representation control.

[PNG](../../artifacts\srle_synthesis_20260926\figure03_features_controls.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure03_features_controls.svg)

## figure04_order_structure

Coefficient IQRs describe overlapping fits, not confidence intervals. Centering all 16 weights preserves predictions because Δ2-mer counts sum to zero. Contributions depend on representation and covariance; they are not mechanisms. Boundary/interaction decomposition is saved separately.

[PNG](../../artifacts\srle_synthesis_20260926\figure04_order_structure.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure04_order_structure.svg)

## figure05_recommendation

ECDFs weight decisions equally; uniform is the exact within-set candidate mixture. Mean/interval panel weights composition classes equally. These are different explicit weighting conventions; the pooled median is zero for both sequence selectors, but worst-choice mass remains.

[PNG](../../artifacts\srle_synthesis_20260926\figure05_recommendation.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure05_recommendation.svg)

## figure06_failures

Both directions, 1,184 decisions per selector. Correct/wrong published rates use the author target; wrong-both uses constituent raw replicates. The 16.6% forced-choice floor depends on the measured roster and does not establish a biological ceiling.

[PNG](../../artifacts\srle_synthesis_20260926\figure06_failures.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure06_failures.svg)

## figure07_similarity

Exact feature-distance levels, no selected cutoff. The 2-mer gain is 6.5% at distance 4 and 16.2% at distance 6. These correlated descriptive strata do not establish monotonic generalization, and sequence distances >3 are untested.

[PNG](../../artifacts\srle_synthesis_20260926\figure07_similarity.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure07_similarity.svg)

## figure08_examples

Predetermined median average replicate-regret examples within each correct-both/wrong-both direction subgroup. Selection was not optimized for the author aggregate, which can disagree with constituents. All candidates shown; a requested direction is not guaranteed by a forced ranking.

[PNG](../../artifacts\srle_synthesis_20260926\figure08_examples.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure08_examples.svg)

## figure09_confidence

All five prediction/design-only signals, both selectors, all five fixed coverages. Lexical ties can dominate coarse distance signals. Class composition changes with coverage; selected thresholds are not independently validated or deployed. Intervals and denominators are in confidence_coverage.csv.

[PNG](../../artifacts\srle_synthesis_20260926\figure09_confidence.png) · [SVG](../../artifacts\srle_synthesis_20260926\figure09_confidence.svg)

