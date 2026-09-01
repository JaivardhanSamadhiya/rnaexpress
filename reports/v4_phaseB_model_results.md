# RNAddress v4 Phase B definitive model results

## Scope

The definitive cohort contains 93,208 assay rows in 445 eligible decision sets (890 directional tasks), 205 held-gene units and 8 held-parent-sequence units. All five outer folds hold out complete biological units. N-zip outcomes were not used and Astrocyte outcomes were not opened.

The frozen 3UTRBERT representation was used for every definitive model. The final embedding cache contains 62,665 exact parent/mutant pairs, has shape 62,665 × 384, and has SHA-256 `51912767e74dc19a06dadf6bab9f3022f11939f1cc537f024af148cc18f948d9`.

## Frozen candidate-family comparison

Values are equal-source means over requested increase and decrease. Lower normalized regret is better; higher rank and GoodSelection@3 are better.

| Model | Rank percentile | Normalized regret | GoodSelection@3 |
|---|---:|---:|---:|
| Hierarchical predict-then-rank | 0.5908 | **0.4265** | 0.2091 |
| Hierarchical pairwise ranker | **0.5991** | 0.4316 | **0.2134** |
| Hierarchical DFL | 0.5878 | 0.4311 | 0.1966 |

The frozen model-selection priority starts with normalized regret, then selected utility and shortlist quality. Hierarchical predict-then-rank therefore wins within the candidate family. Pairwise has higher rank but worse regret. DFL does not pass its separate decision-value gate and is dropped.

## Selected architecture

The selected model is a regularized hierarchical predict-then-rank model:

- frozen 3UTRBERT parent representation;
- contextual parent-to-mutant delta and explicit edit geometry;
- global Ridge head with `alpha=100` and no source identifier;
- assay-context residual Ridge heads with `alpha=100` for seen-assay evaluation;
- residual set to zero for every unseen-source/assay transfer test.

The global-only and hierarchical models are both retained in the result archive. No foundation-model fine-tuning occurred.

## Direction-level performance

| Direction | Rank | Regret | Selected normalized utility | Selected assay utility | Good@1 | Good@3 | Good@5 | Oracle recovery |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Decrease | 0.6565 | 0.3954 | 0.6046 | 0.5021 | 0.0866 | 0.2740 | 0.3674 | 0.0176 |
| Increase | 0.5252 | 0.4576 | 0.5424 | 0.1953 | 0.0910 | 0.1441 | 0.2228 | 0.0209 |

## Held-biological-unit results

| Source/direction | Units | Rank | Regret | Selected normalized utility | Selected assay utility | Good@1 | Good@3 | Good@5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mikl decrease | 189 genes | 0.4923 | 0.5259 | 0.4742 | 0.1539 | 0.0794 | 0.2090 | 0.3413 |
| Mikl increase | 189 genes | 0.5247 | 0.4609 | 0.5391 | -0.0755 | 0.0952 | 0.2407 | 0.3519 |
| TDP decrease | 16 genes | 0.6916 | 0.4551 | 0.5449 | 0.7610 | 0.0000 | 0.3125 | 0.3750 |
| TDP increase | 16 genes | 0.5099 | 0.3799 | 0.6201 | -0.1528 | 0.1250 | 0.1250 | 0.2500 |
| Moffatt decrease | 8 parent sequences | 0.7855 | 0.2053 | 0.7947 | 0.5914 | 0.1804 | 0.3006 | 0.3859 |
| Moffatt increase | 8 parent sequences | 0.5409 | 0.5322 | 0.4678 | 0.8141 | 0.0528 | 0.0667 | 0.0667 |

Mikl decrease is at chance and Moffatt increase has poor regret/shortlist behavior. The pooled appearance is therefore direction- and source-dependent rather than a uniformly transferable compiler.

## Strongest conventional comparator and Gate A/B

The strongest frozen conventional comparator is `ridge_metadata_only`, not a contextual RNA representation. Its equal-source aggregate rank/regret are 0.5960/0.4218, versus 0.5908/0.4265 for the selected model. Thus selected-model gains are -0.0052 rank and -0.0047 regret (a loss). Selected Good@3 and Good@5 improve by 0.0125 and 0.0224, but Good@1 falls by 0.0155 and the primary regret criterion is worse.

Against this comparator, regret gains are -0.0178 Mikl, +0.0139 Moffatt, and -0.0102 TDP. Across 213 independent biological units, median gain is -0.0068, 46.95% improve, leave-best-unit-out mean gain is -0.0184, and the paired bootstrap 95% interval is [-0.0391, 0.0061]. Gates A and B fail.

## Decision-focused value

DFL regret/Good@3 gains versus predict-then-rank are:

- Mikl: -0.0003 / +0.0115;
- Moffatt: +0.0101 / -0.0072;
- TDP: -0.0235 / -0.0417.

No source satisfies the frozen joint DFL improvement rule. Gate G fails, so the ordinary predict-then-rank model is retained.

Machine-readable sources: `results/v4_phaseB/model_aggregate_metrics.csv`, `model_biological_unit_metrics.csv`, `model_set_metrics.csv.gz`, `model_selection.json`, and `outer_candidate_scores.npz`.
