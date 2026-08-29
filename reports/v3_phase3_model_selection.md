# RNAddress v3 Phase 3 model selection

## Decision

# NO-GO

The development-best architecture was `remove_motif_interactions_plus_extreme`, but it failed frozen gate sections B_material_regret_improvement, E_extreme_recovery, F_distribution, G_controls, H_seed_stability, J_uncertainty. It is **not** strong enough to justify spending the untouched Astrocyte benchmark.

## Best candidate

The model uses the pinned 3UTRBERT 3-mer representation with CLS, global, affected-3-mer and radius-10 mutant-minus-parent deltas plus the frozen edit vector; the pruned mechanistic block; nested Ridge rank regression; nested Ridge/Huber raw-magnitude prediction; an outer-cross-fitted rank/magnitude stack; and direction-specific top-decile extreme logistic heads. Evaluation was outer leave-one-parent-out with all learned choices nested inside the 14 training parents.

It reached rank percentile `0.658966`, normalized regret `0.409814`, selected utility `0.470729`, near-oracle recovery `0.100`, and mean oracle rank `98.667`. Exact oracle recovery was top-1 `0.000`, top-3 `0.000`, and top-5 `0.000`—all `0/30`.

## Why it was the development best

It preserved rank and beat the strongest fair forward comparator `forward_3utrbert_absolute_ridge` on rank, regret and selected utility. It also beat metadata shortcuts and passed the two frozen complexity comparisons: pruned mechanism over contextual rank+magnitude, and extreme head over pruned mechanism.

## Why it was rejected

The regret gain over v2.6 was only `0.017438` instead of `0.030`. Oracle top-5 remained `0/30`, near-oracle recovery was `3/30` rather than at least `6/30`, and mean oracle rank was `98.667` rather than at most `90`. Although 9/15 parents improved and median parent gain was positive, removing the best one or two parents made mean gain negative. The shuffled-label control rank was `0.545317`, above the `0.530` ceiling. Seeds 20260829/30 improved regret by only `0.012182`. Confidence failed gate J.

## What changed from v2.6

v3 explicitly separated broad rank, raw effect magnitude, rare extreme-benefit probability and support estimation. It added parent × edit × mechanism interactions and TDP-derived sequence-only stability auxiliary supervision while keeping N-zip as the sole final SNV calibration task. This improved rank and selected utility but did not make experimentally best or near-best edit discovery reliable enough.

## Representation question

3UTRBERT won the matched benchmark with score `0.482005` versus `0.447238` for SpliceBERT. The combined delta-plus-edit rank model reached `0.678263`; parent-only was `0.500000`, mutant-only `0.487106`, global delta `0.584634`, and local delta `0.581827`. Explicit intervention representation was essential.

## Magnitude, extreme and mechanism questions

Direct magnitude alone failed. Rank+magnitude stacking also underperformed v2.6. Pruning motif interactions revealed a useful mechanism block, and the stability and parent-state families survived grouped ablation, but local accessibility did not show an independent gain. The extreme head improved rank/composite score yet found no exact oracle in the top five. TDP stability was auxiliary development evidence only, never independent validation, and no measured stability is required at inference.

## Uncertainty question

The frozen multi-signal confidence score did not pass its predictive or selective-regret criteria. Coverage results are reported without selecting an Astrocyte threshold.

## Integrity and stop

Astrocyte outcomes were not inspected, analyzed, recorded or used for v3 development; the inherited historical test that programmatically loaded the complete worksheet remains disclosed. The sealed Moffatt archive was not listed, opened, extracted or used. All 30 tests in nine files passed when each file ran in a clean process. Monolithic Windows pytest collection is not usable because combined import order intermittently causes a native ViennaRNA DLL initialization/access-violation failure; the standalone ViennaRNA import and all six v3 tests pass. Phase 3 stops here: no Astrocyte preregistration, predictions, reveal, Moffatt inspection, external-validation claim or UI work is authorized.
