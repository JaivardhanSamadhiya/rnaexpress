# Source-only budget diagnostic, 22 September 2026

AI-authored technical execution record. The original context-calibration discovery
gate failed: its advantage over the target-only kmer model had a confidence
interval crossing zero. Confirmation remains closed permanently for that failed
experiment; this diagnostic cannot reverse its verdict or authorize confirmation.

Use ONLY the 3,235 already-open source rows in 61 original source components.
Exclude all original calibration, development and confirmation groups. This is
explicit exploratory reuse, motivated by the uncertain low-budget result.

Make five fixed hash-ordered round-robin component folds. Per fold, use three
fixed, outcome-blind calibration panels, each with eight remaining components
having >=32 metadata rows; all other non-test components train source models.
Use nested attempted budgets 16,64,256 (2,8,32 rows/component). Missing outcomes
receive no replacement. Require >=max(10,budget/2) finite labels in >=6 components.

Reuse fixed standardized kmer Ridge source models (alpha=100) and calibration
fits (alpha=10). Compare three-source stacking with target-only kmer, composition,
uncalibrated sibling-context prediction and calibrated sibling prediction. Sibling
pairs are spliced/unspliced and circular/SCRcircular, established by the source
paper before our analysis. No model selection or hyperparameter search.

Reuse minimum-10-candidate, two-direction normalized regret and equal-component,
equal-context averaging. Collapse repeated calibration panels within component
before 5,000 component bootstrap draws (seed 20260922). Report all budgets and
baselines. Intervals are descriptive: overlapping training sets and shared fitted
models mean they do not capture full training-sample uncertainty. No new gate,
positive-subgroup promotion, holdout access, or novelty claim follows from them.

Purpose: determine whether more calibration labels are useful and whether a
simple biologically matched source explains any gain. This guides resource
allocation and may rule out unnecessary modeling complexity.
