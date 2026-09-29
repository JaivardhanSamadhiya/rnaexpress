# Ranking-relevant support refinement

This additional descriptive check was motivated by the first diagnostic: several assays had 100% candidate-level range flags. It is explicitly post-diagnostic, not a newly preregistered result or a gate.

In a linear utility score, a feature constant across all candidates of one parent adds the same number to every candidate and cannot change their ordering. Therefore each original range flag is intersected with a within-parent nonzero-range mask for that saved feature. Parent-context interactions remain separate feature columns: they can vary even when their parent factor is constant. This is a necessary relevance check, not a proof that all retained shifts cause a model error. Aggregate with the original component/context/candidate weights.

| dataset | model | any_feature_outside_training_range | ranking_active_feature_outside_training_range |
| --- | --- | --- | --- |
| astrocyte_gse330741 | metadata | 1.0000 | 0.0211 |
| astrocyte_gse330741 | composition | 1.0000 | 0.0211 |
| astrocyte_gse330741 | kmer123 | 1.0000 | 0.0211 |
| astrocyte_gse330741 | interaction_3 | 1.0000 | 0.0233 |
| astrocyte_gse330741 | interaction_full | 1.0000 | 0.0211 |
| mikl_gse173098 | metadata | 0.0190 | 0.0190 |
| mikl_gse173098 | composition | 0.0482 | 0.0477 |
| mikl_gse173098 | kmer123 | 0.2935 | 0.2754 |
| mikl_gse173098 | interaction_3 | 0.4946 | 0.4925 |
| mikl_gse173098 | interaction_full | 0.8286 | 0.8074 |
| moffatt_gse334718 | metadata | 1.0000 | 0.0000 |
| moffatt_gse334718 | composition | 1.0000 | 0.0000 |
| moffatt_gse334718 | kmer123 | 1.0000 | 0.0043 |
| moffatt_gse334718 | interaction_3 | 1.0000 | 0.0299 |
| moffatt_gse334718 | interaction_full | 1.0000 | 0.0549 |
| srle | metadata | 1.0000 | 0.3964 |
| srle | composition | 1.0000 | 0.3964 |
| srle | kmer123 | 1.0000 | 0.3964 |
| srle | interaction_3 | 1.0000 | 0.3964 |
| srle | interaction_full | 1.0000 | 0.3995 |

The large unqualified range flags must not be presented as proof of severe ranking-domain mismatch. Neither qualified nor unqualified flags measure how far a candidate lies outside the training joint distribution, and coordinate-wise range coverage cannot establish adequate joint support. Detailed affected dimensions remain in `ranking_active_support_features.csv`. No model or threshold changed, and no new outcome source was opened.
