# RNAddress development results

Generated before the three locked N-zip parents were opened. Astrocyte outcomes remain sealed.

## Assay reliability and target definition

The 12 development parents contain 3,540 SNVs. The preregistered binary threshold resolved to **0.676 log2 localization units**. Only 17.3% of SNVs are within that threshold, 10.4% exceed it in the increase direction, and 72.4% exceed it in the decrease direction. Effects are strongly asymmetric, so rank percentile and regret remain primary.

WT-versus-shScramble negative-control agreement is modest (Spearman 0.163; MAE 0.515). This is not a true technical replicate and does not justify a hard statistical noise ceiling.

## Outer leave-one-parent-out results

| Method | Rank percentile | Normalized regret | Spearman | Success@1 | Success@3 | Success@5 |
|---|---:|---:|---:|---:|---:|---:|
| pairwise_rank | 0.636 | 0.452 | 0.186 | 0.458 | 0.458 | 0.542 |
| nzip_mikl_joint | 0.572 | 0.440 | 0.145 | 0.417 | 0.458 | 0.458 |
| retrieval | 0.561 | 0.492 | 0.127 | 0.500 | 0.500 | 0.542 |
| local_histgb | 0.548 | 0.483 | 0.079 | 0.458 | 0.500 | 0.542 |
| local_elastic | 0.535 | 0.480 | 0.133 | 0.375 | 0.500 | 0.500 |
| forward_extratrees | 0.521 | 0.490 | 0.135 | 0.417 | 0.458 | 0.500 |
| intervention_extratrees | 0.520 | 0.490 | 0.181 | 0.333 | 0.417 | 0.542 |
| local_ridge | 0.505 | 0.512 | 0.130 | 0.375 | 0.458 | 0.500 |
| substitution_mean | 0.503 | 0.493 | 0.103 | 0.375 | 0.458 | 0.458 |
| intervention_plus_mikl_prior | 0.503 | 0.496 | 0.191 | 0.375 | 0.458 | 0.583 |
| motif_delta | 0.471 | 0.478 | 0.059 | 0.417 | 0.500 | 0.500 |
| mikl_only | 0.456 | 0.500 | 0.030 | 0.375 | 0.458 | 0.500 |


Pairwise ranking is selected because its macro rank percentile is **0.636**, versus 0.561 for retrieval and 0.521 for forward-model exhaustive search. Its normalized regret is 0.452, versus 0.492 and 0.490 respectively.

The pairwise-minus-retrieval rank-percentile gain is 0.075, with parent-bootstrap 95% CI [-0.069, 0.222]. Versus forward search, the gain is 0.115, CI [-0.045, 0.263]. These intervals cross zero: the development advantage is promising but not confirmatory.

Pairwise ranking beats retrieval on 6 parents, loses on 5, and ties on 1. The gain is not restricted to one or two parents, but heterogeneity is substantial. Binary Success@3 is 0.458, slightly below retrieval's 0.500; continuous ranking, not thresholded success, drives selection as preregistered.

## Mikl ablation

- Mikl-only transfer: rank percentile 0.456; below random expectation 0.5.
- Joint N-zip+Mikl training: 0.572; useful signal, but below pairwise N-zip ranking.
- N-zip intervention forest alone: 0.520.
- The same forest with a Mikl prior: 0.503; no benefit.

Mikl therefore does not enter the selected primary model. Its multi-base intervention distribution is not treated as homogeneous with N-zip SNVs.

## Development verdict

**PROMISING, NOT YET CONFIRMED.** Pairwise intervention ranking clears random and simple substitution baselines and improves the primary metric over retrieval and strong forward search. Parent-bootstrap uncertainty remains wide, and thresholded Success@K does not dominate retrieval. The frozen three-parent N-zip result is required before authorizing external reveal.

All runtime-driven deviations are disclosed in `reports/preregistration_deviations.md`. No hyperparameter was selected from aggregate performance; fixed grid-center configurations were used for all outer folds.
