# RNAddress v2.4 external-localization transfer results

The preregistered 64-component contextual compression plus metadata and six frozen external assay deltas was evaluated by strict leave-one-parent-out prediction over all 15 N-zip parents. TDP-43 locked outcomes and astrocyte outcomes remained sealed.

## Result

| Model | Macro rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| Factorized fixed reference | 0.662 | 0.400 | 0.104 |
| SpliceBERT v2.2 reference | 0.617 | 0.436 | 0.194 |
| Metadata-only | 0.612 | 0.438 | 0.111 |
| External-localization PCA ridge | 0.562 | 0.461 | 0.188 |
| Strongest forward model | 0.560 | 0.439 | 0.099 |
| Shuffled edit | 0.467 | 0.512 | -0.017 |

The candidate failed the absolute 0.630 criterion, both required baseline gains, the 9/15-parent criterion and the leave-two-best-parent robustness criterion. Only the shuffled-edit check passed. The conditional shuffled-label fit was therefore not run.

## Interpretation

The external heads had reproducible but weak held-out-gene signal in their source studies, yet their transfer through the compressed contextual model did not improve N-zip ranking. The result rejects this transfer architecture and does not authorize any validation-lock reveal. It does not erase the external-only source results, but those results cannot be presented as evidence that the model ranks minimal N-zip edits.

The outcome-independent N-zip absolute embedding cache has SHA-256 `506414ce034a143c7dd8205203673518295011219ad6946c7ff35c7f0c75827a7`; its exact sorted sequence key has SHA-256 `293164536165b63f9c8c3727765836e11867d1114ee1c781ddf2a5f127d210b68`.
