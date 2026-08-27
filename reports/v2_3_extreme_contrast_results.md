# RNAddress v2.3 extreme-contrast results

The deterministic extreme-contrast ridge reused the exact v2.2 SpliceBERT feature matrix and was evaluated by strict leave-one-parent-out prediction over all 15 N-zip parents. TDP-43 locked outcomes and Astrocyte outcomes remained sealed.

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| factorized context, original fixed seed | 0.662 | 0.400 | 0.104 |
| SpliceBERT percentile ridge | 0.617 | 0.436 | 0.194 |
| metadata only | 0.612 | 0.438 | 0.111 |
| SpliceBERT extreme-contrast ridge | 0.581 | 0.464 | 0.172 |
| forward LightGBM | 0.560 | 0.439 | 0.099 |
| shuffled edit identity | 0.422 | 0.529 | -0.018 |

## Gate verdict

**FAIL.** Extreme-only fitting reduced rank percentile from the v2.2 candidate's 0.617 to 0.581 and failed the absolute threshold, both required baseline margins, and leave-two-best robustness. It improved on the strongest forward baseline for at least 9/15 parents and passed shuffled edit. Because the primary gate failed, the shuffled-label control was not run.

The frozen top/bottom-quartile objective is rejected. Its failure does not authorize post-hoc selection of a different quantile cutoff.

The TDP-43 and Astrocyte locks remain unopened. This failure does not supersede any earlier failed gate.
