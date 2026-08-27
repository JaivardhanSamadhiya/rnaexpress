# Hostile internal audit

This analysis is post-lock and diagnostic. It cannot rescue the failed confirmatory gate. Astrocyte outcomes remain sealed.

## Fifteen-parent cross-fitted descriptive result

| Model | Rank percentile | Normalized regret | Spearman |
|---|---:|---:|---:|
| pairwise_rank | 0.622 | 0.458 | 0.158 |
| forward_extratrees | 0.542 | 0.476 | 0.127 |
| retrieval | 0.505 | 0.508 | 0.099 |
| pairwise_cluster_heldout | 0.619 | 0.436 | 0.147 |
| metadata_only | 0.612 | 0.438 | 0.111 |
| gc_only | 0.594 | 0.441 | 0.112 |
| shuffled_edit_identity | 0.528 | 0.493 | 0.012 |

Pairwise-minus-forward rank-percentile difference across all 15 parents: 0.080.
Removing its strongest supporting parent changes this to 0.049; removing its weakest changes it to 0.118.

The closest-parent 3-mer cosine similarity ranges from 0.501 to 0.919; exact duplicate parents: 0.

## Hostile verdict

The custom pairwise objective has a descriptive cross-fitted signal, but it did not beat the strong forward model on the untouched three-parent lock. Any claim that the custom algorithm is necessary is rejected. The scientifically defensible conclusion is that forward-model exhaustive search is currently at least as credible, while parent-level uncertainty remains large.
