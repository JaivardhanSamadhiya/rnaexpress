# TDP-43 v2 locked-gate results

The TDP-43 lock was revealed only after complete predictions, model artifacts, environment, source hashes and the evaluator were committed. The frozen custom method produced a strong aggregate result but the preregistered locked gate **failed**. Astrocyte outcomes therefore remain sealed.

## Aggregate results

| Model | Macro directional rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| nested contextual/external stack | 0.6749 | 0.3766 | 0.2922 |
| forward LightGBM | 0.6197 | 0.2938 | 0.2950 |
| motif/accessibility Ridge | 0.5441 | 0.3742 | 0.3216 |

The custom model exceeded the forward comparator by 0.0552 rank-percentile points and the motif/accessibility comparator by 0.1309. Its normalized regret was nevertheless worse than forward LightGBM, and its macro Spearman was slightly lower than both comparators; these secondary results are retained rather than hidden.

## Frozen gate checks

| Check | Result |
|---|---|
| macro directional rank percentile > 0.550 | PASS |
| positive gain over forward LightGBM | PASS |
| positive gain over motif/accessibility Ridge | PASS |
| positive within-gene Spearman in at least 3/4 genes | PASS |
| positive gain after removing the most favorable locked gene | **FAIL** |

Custom within-gene Spearman was positive for Fam160b2 (0.6979), Diras1 (0.6037) and Synj2bp (0.0364), and negative for Lars2 (-0.1692).

Relative to the strongest aggregate comparator, forward LightGBM, custom rank-percentile gains by gene were -0.0612 for Fam160b2, -0.1369 for Lars2, +0.1173 for Diras1 and +0.3018 for Synj2bp. Removing the most favorable gene, Synj2bp, leaves a mean gain of approximately -0.0269. The aggregate advantage is therefore too concentrated to pass the frozen heterogeneity safeguard.

## Disposition

This result supports context-conditioned ranking on average across the four held-out genes, but it does not satisfy the complete auxiliary lock. It cannot authorize Astrocyte reveal and cannot be relabeled as a pass. Any further model development is a new post-lock development cycle and requires a new, independent, prospectively frozen validation set before making confirmatory claims.
