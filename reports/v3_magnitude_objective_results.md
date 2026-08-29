# RNAddress v3 Phase 3 magnitude-objective results

## Verdict

Direct magnitude learning did **not** fix the compiler regret problem. The strongest development model improved normalized regret from `0.427252` to `0.409814`, an improvement of only `0.017438` versus the frozen `0.030` requirement, and remained above the `0.397` ceiling.

## Candidate results

| Candidate | Rank percentile | Normalized regret | Selected utility | Oracle top-5 | Near oracle | Selection score |
|---|---:|---:|---:|---:|---:|---:|
| v2.6 historical | 0.635752 | 0.427252 | 0.313164 | 0.033 | 0.133 | 0.493217 |
| Contextual magnitude | 0.530753 | 0.494896 | 0.116851 | 0.033 | 0.067 | 0.422292 |
| Rank+magnitude stack | 0.591853 | 0.451681 | 0.365610 | 0.033 | 0.100 | 0.464912 |
| Pruned mechanism C3 | 0.629796 | 0.411812 | 0.463377 | 0.000 | 0.100 | 0.489274 |
| Pruned mechanism + extreme | 0.658966 | 0.409814 | 0.470729 | 0.000 | 0.100 | 0.503100 |

The explicit extreme head raised rank percentile by `0.029169` but recovered the exact oracle in the top five for `0/30` decisions. It therefore improved the frozen composite score without solving extreme-edit recovery.

## Mechanistic ablations

Removing motif interactions improved the C3 selection score from `0.463671` to `0.489274`, so motif interactions were dropped. Removing the stability auxiliary reduced score to `0.435010` and worsened regret to `0.469449`; stability therefore survived its grouped ablation. Parent-state interactions also survived because their removal reduced score to `0.451582`. Local accessibility did not show an independent positive contribution in its full-block removal test, and no unplanned joint-pruning search was performed.

Measurement-aware targets were not feasible because deterministic construct-linked replicate uncertainty could not be reconstructed without inventing standard errors.
