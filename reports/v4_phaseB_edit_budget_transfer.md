# RNAddress v4 Phase B edit-budget transfer

## Held-band curve

Equal-source/direction macro averages for the selected global head:

| Held edit band | Rank | Regret | Random regret | Good@1 | Good@3 | Good@5 |
|---|---:|---:|---:|---:|---:|---:|
| Exactly 1 nt | 0.5000 | 0.4898 | 0.5000 | 0.0000 | 0.0000 | 1.0000* |
| 2–5 nt | 0.5298 | 0.4896 | 0.5000 | 0.0461 | 0.1711 | 0.2694 |
| 6–10 nt | 0.5246 | 0.4811 | 0.5000 | 0.0866 | 0.2126 | 0.2983 |
| 11–25 nt | 0.5345 | 0.4645 | 0.5000 | 0.1441 | 0.2899 | 0.4141 |
| 26–50 nt | 0.5486 | 0.4863 | 0.5000 | 0.1732 | 0.3988 | 0.5673 |
| >50 nt | 0.6085 | 0.4185 | 0.5000 | 0.1952 | 0.2655 | 0.3837 |

`*` The exact-1-nt held-band contains only two decision sets from one biological unit and each has at most five candidates, making Good@5 trivially 1.0. It is not evidence of SNV transfer.

The curve weakens toward small edits. The >50-nt band has the clearest signal, while exact 1 nt is chance and 2–10 nt misses the frozen regret margin.

## Prespecified bridges

| Bridge | Rank | Regret | Random regret | Good@1 | Good@3 | Good@5 |
|---|---:|---:|---:|---:|---:|---:|
| Train excluding 1–5; test 1–5 | 0.5318 | 0.4880 | 0.5000 | 0.0464 | 0.1776 | 0.2757 |
| Train excluding 1–10; test 1–10 | 0.5471 | 0.4874 | 0.5000 | 0.0770 | 0.1423 | 0.2135 |

The frozen Gate E requires rank >0.52 and regret improvement over random ≥0.02 for both 2–5 and 1–10 regimes. Improvements are only 0.0104 and 0.0126, respectively. Gate E fails.

## Exact-SNV descriptive audit

Only 19 distinct exact-SNV interventions exist, and no exact-SNV-only decision set has at least five candidates. Therefore no exact-SNV gate is valid.

- Mikl: 13 unique SNVs / 26 assay rows; predicted-versus-observed rank-percentile Spearman -0.3993; mean absolute rank-percentile error 0.3701.
- Moffatt: 6 unique SNVs / 12 assay rows; Spearman 0.0035; mean absolute rank-percentile error 0.1556.

These descriptive values do not support exact-SNV transfer.

## Minimum-budget feasibility

Of 890 directional decision tasks, 888 (99.78%) contain multiple measured edit costs. Retrospective minimum-cost analysis is therefore feasible and is saved in `minimum_budget_feasibility.csv`. It remains an evaluation only; no generative minimum-budget model was trained. The present data do not justify an Astrocyte-scale exact-SNV claim.
