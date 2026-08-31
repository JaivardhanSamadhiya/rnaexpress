# RNAddress v4 Phase B decision-set audit

Audit date: 2026-08-31

Frozen Phase A commit: `36e836ea1dfd0d20b688cb0b77f914aa9964955c`

## Decision unit

RNAddress Phase B treats a decision as choosing among experimentally measured interventions for one biologically actionable target landscape with a comparable outcome scale. The source-specific keys are fixed before modeling:

- Mikl: `dataset + assay + reporter + cell context + gene`.
- TDP-43: `dataset + assay + reporter + cell context + gene`.
- Moffatt: `dataset + assay family + reporter + cell context + biological parent element`.

Exact `parent_id` remains attached to every candidate and is the immutable leakage group. Mikl and TDP decision landscapes may contain multiple local parent windows from the same target gene; this is intentional because the actionable decision is which measured local intervention to apply to that gene. Moffatt has dense variants of a common 260-nt parent and is therefore parent-defined.

Grouping TDP only by exact local parent would create 4,566 one-candidate sets and make selection undefined. The gene-landscape definition preserves biological actionability without pretending that different local parent windows are identical.

## Frozen eligibility and utility

- Minimum finite measured candidates: **5**.
- Effect range must be strictly positive.
- Base decision set is evaluated twice, for requested increase and requested decrease.
- Directional utility is `s × measured_effect`, with `s=+1` for increase and `s=-1` for decrease.
- Normalized regret is `(best utility - selected utility) / (maximum utility - minimum utility)`.
- A candidate is prospectively “good” when its normalized regret is at most **0.10**.
- Outcome-derived ranks, ranges, and regret are labels/metrics only and never input features.

## Scale

| Source | All base sets | Eligible base sets | Eligible candidate rows | Minimum | Median | Mean | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mikl | 448 | 378 | 23,616 | 5 | 36 | 62.48 | 661 |
| TDP-43 | 16 | 16 | 4,566 | 6 | 274.5 | 285.38 | 788 |
| Moffatt | 53 | 51 | 65,026 | 26 | 1,160 | 1,275.02 | 3,485 |
| Total | 517 | **445** | **93,208** | 5 | — | — | 3,485 |

The 445 base sets create **890 directional decision tasks**. They contain 248 case-folded gene labels and all 10,406 Phase A exact parent contexts.

Mikl has an increasing candidate in 376 eligible sets and a decreasing candidate in all 378. TDP has both directions in all 16 sets. Moffatt has an increasing candidate in all 51 and a decreasing candidate in 50.

## Weighting and independence

Evaluation macro-averages first over base decision sets, then over independent biological units, direction, and source. Every source receives equal weight in cross-source model selection. Moffatt's 65,026 candidate rows cannot outweigh Mikl's hundreds of genes.

Training may process candidate rows, but each decision-set loss is weighted equally within source, and each source is weighted equally in the global objective. All outcomes, reporters, and variants from a held biological unit remain held out together.

## Integrity

The construction script reads only the Phase A certified Mikl, TDP, and Moffatt truth layer. It computes exact changed positions, changed blocks, span, mean position, reference/alternate subsequences, and operation lengths from aligned source sequences. No N-zip or Astrocyte path is present.

Machine outputs:

- `results/v4_phaseB/phaseB_candidates.csv.gz`
- `results/v4_phaseB/decision_set_summary.csv`
- `results/v4_phaseB/decision_set_audit.json`
- `results/v4_phaseB/decision_set_manifest.json`
