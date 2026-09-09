# FinalShot controls — consolidated status

FINAL RESULT CONSOLIDATION — WITH INTEGRITY QUALIFICATIONS

## RBP-permutation control

Retained rank gain 107.97%, regret gain 78.84%; control still meets both Gate A thresholds. Necessity fails.

## Delta-RBP shuffle control

Retained rank gain 130.13%, regret gain 100.28%; control still meets both Gate A thresholds. Necessity fails. The delta donor construction cycles unequal-size units and is not a bijective row shuffle.

## Cell-context-shuffle control

| model | rank_context_value | regret_context_value |
| --- | --- | --- |
| cell_swap_M1 | 0.011063 | 0.032349 |
| cell_swap_M2 | 0.017619 | 0.031393 |
| cell_swap_M3 | 0.054011 | 0.031748 |
| cell_swap_nested | 0.034666 | 0.037565 |

M1 is reused unchanged because it contains no expression features.

## Parent-binding ablation

Knockout gain: rank +0.056341363, regret +0.035829318. Rank improves and roughly 89.36% of regret gain survives; aggregate necessity is not established.

## Trans-interaction ablation

Gate H fails. M3 minus trans-knockout crossed-cell gain: rank +0.003888, regret +0.001199; insufficient for the frozen thresholds. Trans context is not supported for retention.

## Stability ablation

Not applicable: no stability block was admitted. Gate I is neither pass nor fail.

## Measurement-head ablation

Head randomization worsens pooled MSE 1.232723→1.789378 and Spearman 0.317235→0.068879. Equal-head MSE worsens but Spearman improves 0.155036→0.204898. Pre-head scores are unchanged by head reassignment. The added pooled-plus-macro conjunction was not an original frozen criterion; report the mixed evidence.

## Evidence against edit-size shortcuts

Not established sufficiently for the compiler claim. Delta-RBP edit-size R-squared is 0.652844 in Moffatt and 0.864634 in TDP; Mikl is -0.341258. Matched Mikl estimates have a protocol qualification and identity/delta necessity fails. Predictive gain alone is not mechanistic evidence.

See finalshot_integrity_review.md for limitations of the control implementations. No threshold was changed after results.
