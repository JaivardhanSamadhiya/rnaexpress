# RNAddress v2.5 published Mikl-XGBoost transfer results

The preregistered 20-feature calibration was evaluated by strict leave-one-parent-out prediction over all 15 N-zip parents. TDP-43 locked outcomes and astrocyte outcomes remained sealed.

## Result

| Model | Macro rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| Factorized fixed reference | 0.662 | 0.400 | 0.104 |
| Mikl-XGBoost calibrated | 0.621 | 0.434 | 0.128 |
| SpliceBERT v2.2 reference | 0.617 | 0.436 | 0.194 |
| Metadata-only | 0.612 | 0.438 | 0.111 |
| Strongest forward model | 0.560 | 0.439 | 0.099 |
| Mikl-XGBoost zero-shot | 0.492 | 0.504 | 0.034 |
| Shuffled edit | 0.468 | 0.509 | -0.018 |

## Gate verdict

The calibrated candidate passed the required gain over the strongest forward model, positive gain after removing its two best parent gains and the shuffled-edit control. It failed:

- absolute rank percentile: 0.620807 < 0.630;
- metadata gain: 0.008438 < 0.020;
- improvement count: fewer than 9/15 parents versus the strongest forward model.

The primary gate failed, so the shuffled-label control was not run. No validation-lock prediction or outcome was opened.

## Interpretation

The published external classifier alone does not rank N-zip SNVs: its zero-shot score is near chance. Its calibrated features do improve over metadata and v2.2's contextual model, but not by the preregistered margin. This supports retaining the two frozen probability deltas as complementary development features; it does not authorize presenting v2.5 as a validated inverse-design model.
