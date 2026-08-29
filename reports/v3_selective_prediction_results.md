# RNAddress v3 Phase 3 selective-prediction results

## Verdict

The frozen five-signal confidence score did **not** reliably predict recommendation failure. Confidence versus normalized regret had Spearman rho `-0.117961` (required at most `-0.20`). At 60% coverage, regret improved by only `0.004970` (required at least `0.030`), and regret was not monotonic from 100% to 80% to 60% coverage.

## Coverage curve

| Coverage | Decisions | Rank percentile | Normalized regret | Selected utility | Meaningful-effect rate | Near-oracle rate |
|---:|---:|---:|---:|---:|---:|---:|
| 100% | 30 | 0.658966 | 0.409814 | 0.470729 | 0.433 | 0.100 |
| 80% | 24 | 0.682542 | 0.414839 | 0.661891 | 0.458 | 0.083 |
| 60% | 18 | 0.738451 | 0.404844 | 0.614619 | 0.389 | 0.111 |
| 40% | 12 | 0.718854 | 0.405457 | 0.864856 | 0.417 | 0.167 |

The score used only outcome-free nested signals: rank–magnitude disagreement, base–extreme disagreement, nearest-training-parent contextual distance, top-1/top-2 score margin, and three-seed score standard deviation. Each was converted to an outer-training empirical support percentile and averaged without learned weights. No Astrocyte threshold was selected.

The 80% subset increased selected utility but slightly worsened regret; 60% improved rank substantially but not regret enough; 40% was reported as required but was not used to rescue the failed gate. Abstention is therefore not retained as a validated Phase 3 safeguard.
