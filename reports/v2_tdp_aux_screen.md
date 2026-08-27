# RNAddress v2 TDP-43 auxiliary screen

The shared-context multitask candidate used only the 12 permitted TDP-43 development genes and strict N-zip leave-one-parent-out folds. The four TDP-43 locked genes and all Astrocyte outcomes remained sealed.

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| factorized context, N-zip only | 0.662 | 0.400 | 0.104 |
| metadata only | 0.612 | 0.438 | 0.111 |
| forward LightGBM | 0.560 | 0.439 | 0.099 |
| factorized context + TDP-43 auxiliary | 0.504 | 0.480 | 0.048 |

Verdict: the multi-base TDP-43 task causes negative transfer to N-zip SNV recommendation and is dropped from the primary model. The dataset remains valuable as a separate held-out-gene auxiliary test only if a later development method earns access to its lock.
