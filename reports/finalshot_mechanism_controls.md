# RNAddress FinalShot mechanism-breaking controls

## Frozen analysis

Both mandatory Gate G controls were retrained through the same frozen nested
M1/M2/M3 procedure used by the primary analysis. Model-family selection was
performed independently inside each outer fold from training-only inner-fold
metrics. Evaluation remained paired to M0 on identical held-out decision tasks.
The fixed control seed was 42017.

The RBP-identity permutation retained all 93,208 candidate rows. The
delta-RBP shuffle retained 92,846 rows and excluded 362 sparse rows exactly as
specified: shuffling was restricted to strata with at least two biological
units and five rows, and no looser rematching was introduced.

## Gate G results

| Control | Rank gain observed | Rank gain after break | Rank retained | Regret gain observed | Regret gain after break | Regret retained | Mean retained | Gate A still met | Gate G control pass |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| RBP identity permutation | +0.04229 | +0.04566 | 107.97% | +0.04009 | +0.03161 | 78.84% | 93.40% | Yes | No |
| Delta-RBP intervention permutation | +0.03977 | +0.05176 | 130.13% | +0.03897 | +0.03907 | 100.28% | 115.20% | Yes | No |

Neither control eliminated half of the observed gain in either Gate A metric.
Both controls also independently retained enough performance to satisfy both
Gate A thresholds. Therefore **Gate G fails** under every required clause.

The result is mechanistically decisive: the observed ranking advantage does
not require stable biological RBP channel identity or the intervention-specific
delta-RBP assignment represented by the frozen model. The surviving signal may
reflect generic distributional summaries, geometry-correlated structure, or
another shortcut, but it cannot support the claimed RBP-specific mechanism.

## Integrity statement

No N-zip outcome was accessed and no Astrocyte outcome or sequence data was
accessed. Frozen features, folds, model grids, selection rules, control
definitions, seeds, and gate thresholds were not altered after observing the
results.
