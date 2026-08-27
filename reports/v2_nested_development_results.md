# RNAddress v2 nested development results

All 15 N-zip parents are development data because the original lock was spent. These are nested out-of-parent predictions, not a new confirmatory lock. TDP-43 locked outcomes and Astrocyte outcomes remained sealed.

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| factorized_context_fixed | 0.662 | 0.400 | 0.104 |
| metadata_only | 0.612 | 0.438 | 0.111 |
| gc_only | 0.594 | 0.441 | 0.112 |
| factorized_context_nested | 0.588 | 0.448 | 0.100 |
| forward_lightgbm | 0.560 | 0.439 | 0.099 |
| forward_extratrees | 0.542 | 0.476 | 0.127 |
| shuffled_edit_identity | 0.509 | 0.483 | 0.002 |

Development gate: **FAIL**.

The original three-parent result remains a FAIL and is not superseded.
