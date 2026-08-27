# RNAddress v2.1 stability-ensemble results

All 15 N-zip parents were evaluated by strict leave-one-parent-out prediction using the seven seeds frozen in `reports/v2_1_stability_preregistration.md`. Each seed was rank-normalized within the held-out parent and the seven ranks were averaged without selection or weighting. TDP-43 locked outcomes and Astrocyte outcomes remained sealed.

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| factorized context, original fixed seed | 0.662 | 0.400 | 0.104 |
| metadata only | 0.612 | 0.438 | 0.111 |
| factorized context, seven-seed ensemble | 0.575 | 0.491 | 0.122 |
| forward LightGBM | 0.560 | 0.439 | 0.099 |
| shuffled edit identity | 0.526 | 0.494 | -0.004 |

## Gate verdict

**FAIL.** The ensemble failed the absolute 0.630 threshold, the 0.030 forward-model margin, the 0.020 metadata margin, and positive gain after removing the two best parents. It improved on the strongest forward baseline for at least 9/15 parents and passed the shuffled-edit bound. Because the primary gate failed, the expensive shuffled-label ensemble was not run.

Individual frozen seeds ranged from 0.551 to 0.662 rank percentile. The ensemble's lower top-choice performance despite slightly higher global Spearman correlation shows that optimization variance is not a sufficient explanation or rescue for inverse-design selection. The original favorable seed cannot be promoted as confirmatory evidence.

The TDP-43 and Astrocyte locks remain unopened. This failure does not supersede any earlier failed gate.
