# RNAddress v4 Phase B2 nuisance decomposition

Definitive run date: 2026-09-01

## Definition and leakage control

Phase B2 retained the raw assay-scale localization effect and defined the residual target as `r_i = y_i - G^{-i}(geometry_i)`. `G^{-i}` was fit without the complete biological fold containing row i. The geometry input contained the frozen edit-cost, edit-fraction, operation, position/span, composition, intervention-class and edit-tier fields and no language-model state.

Two prespecified nuisance models were evaluated inside every outer-training cohort: global geometry Ridge and global geometry plus assay-context residual Ridge. Source-specific nuisance won six of ten direction-fold selections; global nuisance won four. Leave-source-out, cell and reporter transfers used global nuisance only and never used a target-context residual.

The audit contains 80 inner cross-fit records: two nuisance levels × four inner folds × ten outer direction-folds. Every record has zero biological-unit overlap. The definitive candidate archive has 186,416 direction-specific rows, and all full and nuisance scores are finite.

## Outer nuisance performance

| Source | Direction | Rank | Normalized regret | Good@3 |
|---|---:|---:|---:|---:|
| Mikl | decrease | 0.5489 | 0.4873 | 0.2011 |
| Mikl | increase | 0.5566 | 0.4488 | 0.2593 |
| Moffatt | decrease | 0.7563 | 0.2336 | 0.2960 |
| Moffatt | increase | 0.5861 | 0.5237 | 0.0567 |
| TDP-43 | decrease | 0.7654 | 0.4214 | 0.1875 |
| TDP-43 | increase | 0.4690 | 0.3590 | 0.2500 |
| Equal source/direction mean | — | **0.6137** | **0.4123** | **0.2084** |

The selected full context models reached rank 0.6328 and regret 0.4112. Thus overall ContextValue was only +0.0191 rank and +0.0011 regret. This narrowly missed the rank branch of Gate A (`0.020`) and was far below the regret branch (`0.010`).

Machine records: `results/v4_phaseB2/nuisance_crossfit_audit.csv`, `primary_candidate_predictions.csv.gz`, `primary_aggregate_metrics.csv`, and `development_gates.json`.
