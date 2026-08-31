# RNAddress v4 Phase A intervention taxonomy

## Design principle

The taxonomy describes physical sequence operations and experimental context; it is not inferred from favorable outcomes. Every record retains exact parent and child sequences, changed bases, insertion/deletion lengths when applicable, changed fraction, operation-aware edit cost, source mechanism, parent grouping, and assay-specific outcomes.

## Certified operation classes

| Dataset | Operation class | Count | Cost semantics |
| --- | --- | ---: | --- |
| Mikl | motif random replacement | 11,900 | exact changed bases inside source-declared motif occurrences |
| TDP-43 | UG-rich motif complement replacement | 4,566 | exact changed bases |
| Moffatt | sufficiency background replacement | 9,462 | removed parent bases + inserted inactive-padding bases |
| Moffatt | necessity deletion with inactive padding | 3,328 | deleted bases + inserted padding bases |
| Moffatt | random substitution | 14,235 | exact changed bases |
| Moffatt | regional shuffle | 10,539 | exact changed bases after shuffling |
| Moffatt | SHAPE structure perturbation | 8,728 | exact changed bases in structure-directed design |

## Edit-cost tiers

The primary cost is continuous. Tiers are descriptive strata anchored to actual source operations and are not used to choose outcomes or architectures:

| Tier | Cost | Certified count | Interpretation |
| --- | ---: | ---: | --- |
| Exact SNV | 1 | 19 | one changed base |
| Small local edit | 2–5 | 15,993 | short substitutions or perturbations |
| Motif-scale edit | 6–12 | 14,719 | typical short RBP/motif window scale |
| Regional edit | 13–99 | 17,641 | multi-motif or structural region |
| Large element edit | ≥100 | 14,386 | broad replacement/deletion/shuffle or large motif complement |

The counts sum to 62,758 certified interventions. For necessity and sufficiency, tier assignment uses operation-aware edit cost; exact Hamming distance can be smaller because the fixed-length inactive padding may coincidentally match parent bases.

## Dataset-specific distributions

- Mikl: changed bases 1–40, median 5; 13 exact SNVs, 6,414 small, 5,252 motif-scale, and 221 regional edits.
- TDP-43: changed bases 5–179, median 7; 1,716 small, 1,555 motif-scale, 1,154 regional, and 141 large edits.
- Moffatt: Hamming distance 1–249, median 48; operation cost 1–510, median 40; six exact SNVs, 7,863 small, 7,912 motif-scale, 16,266 regional, and 14,245 large edits.

## Direction is not an intervention class

Increase/decrease is an observed assay-specific response, never an edit label. The same physical operation can increase localization in one reporter or cell line and decrease it in another. Direction must therefore be represented by assay-specific outcomes and evaluated separately.

Mikl and TDP are decrease-heavy; Moffatt's finite GFP and Firefly outcomes are increase-heavy. This inversion is direct evidence against a single pooled scalar target.

## Minimum-budget implication

The empirical data support a future constrained objective such as:

`minimize edit_cost subject to a direction-specific predicted localization gain and calibrated risk threshold`.

Support is strong for **small through large budgets**, because 48,372 interventions have cost at most 99 and all major operation families are represented. Support is weak for an exact-SNV-only claim: there are only 19 exact SNVs, and six of those come from one Moffatt parent. Phase B may condition on exact continuous cost and evaluate shortlist regret by budget, but it must not claim broad SNV competence before the sealed prospective benchmark.

## Recommended hierarchy

1. Preserve continuous edit cost in every model and report.
2. Use tiers only for stratified evaluation and minimum-budget candidate sets.
3. Preserve operation class as conditioning metadata, not as a substitute for exact sequence deltas.
4. Group all variants by biological parent; add exact-parent-sequence and gene-held-out sensitivity analyses.
5. Report direction, magnitude, uncertainty, and selection regret separately by assay, operation, and budget.
