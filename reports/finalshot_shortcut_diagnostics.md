# FinalShot nuisance predictability and parent-binding ablation

Completed 9 September 2026. These analyses use the existing frozen biological
folds; no localization model, feature family, fold, or gate was changed.

## Edit-size and intervention-class probes

The 721 delta-RBP features were used to predict log1p(edit cost) with weighted
Ridge (alpha 100), and intervention class with class-balanced multinomial
logistic regression (C 0.1). Scaling and fitting used training rows only.
All ten representation-by-fold logistic fits converged, no biological unit
overlapped training and test, and no test class was unseen in training.

| Source | Delta-RBP size R-squared | Geometry size R-squared |
|---|---:|---:|
| Mikl | -0.341258 | 0.999505 |
| Moffatt | 0.652844 | 0.999236 |
| TDP | 0.864634 | 0.999906 |

The geometry block explicitly contains edit cost and intervention class. Its
near-perfect results are positive controls, not independent evidence of a
learned biological relationship. Delta-RBP features encode substantial edit-size
information in Moffatt and TDP, but generalize poorly for this probe in Mikl.
These correlations do not establish that every localization gain is caused by
edit size. Conversely, localization gains cannot by themselves exclude that
explanation. Frozen matched-stratum and mechanism-breaking tests are necessary.

Class macro-F1 is reported using the same seven-label universe for every source,
including absent labels as zero. Thus a single-class source's perfect score is
1/7, not 1. Delta-RBP versus geometry scores are Mikl 0.139249 vs 0.142857,
Moffatt 0.327490 vs 0.714286, and TDP 0.137858 vs 0.142857. Do not read these
source-specific numbers as conventional macro-F1 over only locally observed
classes. They remain descriptive; no success threshold was introduced.

The numerical iteration cap (2,000), solver, and global-label reporting
convention were specified during implementation before probe results, not in
the original September 2 protocol. They are disclosed implementation details,
not newly frozen scientific gates.

## Parent-binding knockout

All five outer folds and their nested family selection completed. Removing the
two parent-binding summaries and their context interactions gives rank gain
0.056341 and regret gain 0.035829 over geometry, compared with 0.042294 and
0.040094 for the observed nested predictor. The ablation selects M3, M3, M3,
M1, M2 across outer folds 0–4.

The knockout improves rank and retains about 89.36% of the regret gain. This
does not support necessity of the parent-binding block for the aggregate result.
Because both models undergo nested selection, it is a pipeline-level ablation,
not a causal effect estimate for an individual coefficient.

## Source, direction, and coefficient diagnostics

`results/finalshot/directional_source_diagnostics.csv` reports every frozen edit
band separately by source and requested direction, plus all observed TDP and
Moffatt intervention classes and class-by-band groups. These are descriptive
subgroup results, not independently validated subgroup discoveries. They do
not amount to exact continuous-geometry matching of TDP interventions.

A separate September 9 descriptive check matches all 28 geometry features
exactly within existing TDP decision sets. It yields 150 two-candidate pairs
(300 rows, six parents): rank/regret gains are both approximately -0.023422 for
decrease and +0.155516 for increase. Geometry predictions tie within each pair;
the comparison is against the frozen candidate-ID tie breaker. This check is
not a newly frozen gate, does not identify direct TARDBP binding, and does not
establish a validated directional effect. Details and eligibility are in
`tdp_exact_geometry_summary.json` and `tdp_exact_geometry_audit.csv`.

`rbp_group_stability.csv` summarizes group selection across five outer folds.
For M3, a fold counts as selected only when all three seeds select the group;
its norm is the seed median. `rbp_coefficient_direction_stability.csv` reports
the direction of each individual standardized feature coefficient, separating
base terms from expression interactions. Seed-median signs are aggregated
across folds, without assigning one sign to an entire multi-feature RBP group.
These summaries cannot identify causal RBPs, especially with the failed
RBP-identity necessity control and correlated normalized profile features.

Machine-readable provenance, predictions, convergence audits, and scores are
in `shortcut_summary.json`, `shortcut_fold_audit.csv`, the two
`shortcut_predictions_*.csv.gz` files, and `parent_binding_summary.json` under
`results/finalshot/`. Only the three certified development sources were used.
