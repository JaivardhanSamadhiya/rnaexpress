# RNAddress v2.6 nested contextual/external stack results

The frozen v2.6 development gate **passed**. TDP-43 locked outcomes and Astrocyte outcomes remained sealed throughout this analysis.

## Frozen candidate

The selected candidate was `nested_context_external_stack`: a strict outer leave-one-parent-out stack with inner leave-one-parent-out SpliceBERT contextual predictions, 18 outcome-blind edit metadata features, and two frozen Mikl XGBoost localization-head deltas. The contextual and meta Ridge penalties remained fixed at their feature dimensions, 2,638 and 21.

## Primary results

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| nested contextual/external stack | 0.6358 | 0.4273 | 0.1999 |
| Mikl XGBoost calibrated | 0.6208 | 0.4340 | 0.1281 |
| metadata only | 0.6124 | 0.4376 | 0.1112 |
| forward LightGBM | 0.5604 | 0.4387 | 0.0986 |
| shuffled edit identity | 0.4971 | 0.5111 | -0.0266 |
| full nested shuffled-label control | 0.5072 | 0.4840 | -0.0398 |

The candidate gained 0.0754 over the strongest forward model and 0.0234 over metadata only. It improved over the strongest forward model on at least 9 of 15 parents, and the mean gain remained positive after removing the two most favorable parents.

## Gate disposition

All seven frozen checks passed:

1. macro directional rank percentile at least 0.630;
2. gain over strongest forward search at least 0.030;
3. gain over metadata only at least 0.020;
4. improvement on at least 9 of 15 parents;
5. positive gain after removing the two best parents;
6. shuffled edit identity no higher than 0.540; and
7. full nested shuffled-label control no higher than 0.530.

This authorizes generation and freezing of all 1,006 TDP-43 lock predictions. It does not reveal or imply any TDP-43 lock result, and it does not authorize the Astrocyte reveal unless the separately frozen TDP-43 gate also passes.
