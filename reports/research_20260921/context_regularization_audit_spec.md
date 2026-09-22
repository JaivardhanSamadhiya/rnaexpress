# Nested regularization audit, 22 September 2026

AI-authored exploratory diagnostic specified after the source-only learning
curve. It cannot change the failed original gate or open confirmation outcomes.

Use exactly the original source-only five component folds, three calibration
panels, fixed 64 attempted slots, eligibility and source models from the learning
curve. No original calibration/development/confirmation group may enter.

For target-only kmer, three-source stack and composition models, choose Ridge
alpha from [0.1,1,10,100,1000,10000] using leave-one-calibration-component-out
mean squared error, giving calibration components equal weight. Fit every scaler
within each inner training fold. Exact ties prefer the larger alpha. Then refit
using only that panel's available target labels, and predict outer test groups.
No evaluation labels enter preprocessing, hyperparameter selection or fitting.

Retain fixed-alpha stack/kmer and uncalibrated sibling predictions as controls.
Compare two-direction normalized regret using the same component/context/panel
aggregation as the learning curve; bootstrap components 5,000 times, seed 20260922.
Report every comparison and selected-alpha distribution. These intervals omit
full training-set uncertainty and are descriptive, not independent confirmation.
The purpose is to test whether baseline regularization explains apparent gains.
