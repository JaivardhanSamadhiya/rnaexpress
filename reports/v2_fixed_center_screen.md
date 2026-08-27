# RNAddress v2 fixed-center development screen

This is a preregistered compute-screening pass, not the final nested development result. It was generated with strict leave-one-parent-out predictions over all 15 now-development N-zip parents. The original three-parent lock remains a historical FAIL; TDP-43 locked outcomes and Astrocyte outcomes remain sealed.

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| factorized context ranker | 0.662 | 0.400 | 0.104 |
| old linear pairwise rank | 0.622 | 0.458 | 0.158 |
| metadata only | 0.612 | 0.438 | 0.111 |
| GC only | 0.594 | 0.441 | 0.112 |
| context LambdaMART | 0.566 | 0.451 | 0.154 |
| forward LightGBM | 0.560 | 0.439 | 0.099 |
| forward ExtraTrees | 0.542 | 0.476 | 0.127 |
| shuffled edit identity | 0.509 | 0.483 | 0.002 |
| retrieval | 0.505 | 0.508 | 0.099 |

The factorized ranker passes the six screenable development criteria: absolute rank percentile, gain over strongest forward search, gain over metadata, number of improved parents, leave-two-best-parent sensitivity, and shuffled-edit collapse. The shuffled-label control and grouped inner hyperparameter selection remain mandatory before the TDP-43 lock can be opened.
