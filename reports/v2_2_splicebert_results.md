# RNAddress v2.2 SpliceBERT contextual-delta results

The official frozen `SpliceBERT.1024nt` checkpoint generated an outcome-blind 4,395 × 2,638 feature matrix (SHA-256 `eeaca4d2c7362877755e850a8bc08fa3e3088c64ffd69fadff72ef409c1165e74`). The deterministic percentile-ridge candidate was evaluated by strict leave-one-parent-out prediction over all 15 N-zip parents. TDP-43 locked outcomes and Astrocyte outcomes remained sealed.

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| factorized context, original fixed seed | 0.662 | 0.400 | 0.104 |
| SpliceBERT contextual-delta ridge | 0.617 | 0.436 | 0.194 |
| metadata only | 0.612 | 0.438 | 0.111 |
| forward LightGBM | 0.560 | 0.439 | 0.099 |
| shuffled edit identity | 0.484 | 0.513 | -0.023 |

## Gate verdict

**FAIL.** The candidate missed the absolute rank-percentile threshold (0.617 versus 0.630) and the required metadata margin (+0.004 versus +0.020). It passed the forward-model margin, improved on at least 9/15 parents, retained positive gain after removing its two best parents, and passed shuffled edit. Because the primary gate failed, the shuffled-label control was not run.

The substantially improved global Spearman correlation, combined with insufficient top-choice rank, indicates that the pretrained contextual representation contains transferable ordering signal but that pointwise percentile regression allocates too much loss to middle-ranked candidates for this inverse-design objective. This is a development diagnosis, not confirmatory evidence.

The TDP-43 and Astrocyte locks remain unopened. This failure does not supersede any earlier failed gate.
