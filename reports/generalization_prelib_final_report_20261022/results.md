# Verified PRELib binding result

**NO-GO under the original pooled-binding robustness criterion.** All399 fits completed and the independent numerical/score/target/gate replay passed. This closes the frozen experiment without a localization or novelty success.

All4054 edits,16 backgrounds and seven nominal lineages were retained. Original scientific source, three arms, weights, target definitions, nested folds, lambdas, tie policy and gates stayed unchanged. The explicitly approved operational adapter and current-Python provenance are recorded separately; no old runtime certificate was rewritten.

| Primary pooled PUM2 arm | Equal-lineage/equal-background MAE |
|---|---:|
| kmer84 | 0.473912642697 |
| kmer84_plus_releasedPUM2 | 0.465209212016 |
| kmer84_plus_duplicateTGT | 0.474378072188 |
| zero_effect | 0.459305919364 |

| Control | Relative MAE improvement | Improved lineages | Paired95% gain interval | Leave-best gain | Gate |
|---|---:|---:|---|---:|---|
| kmer84 | 1.837% | 5/7 | [-0.002897, 0.019052] | 0.005383 | NO-GO |
| kmer84_plus_duplicateTGT | 1.933% | 5/7 | [-0.002615, 0.019936] | 0.005675 | NO-GO |

The fixed PUM scalar adds feature variation outside the kmer span and modestly improves average error against both fitted controls. It helps5/7 lineages and retains positive mean gains in all17 alternative target views and after removing the best lineage. Those conditions passed, but the prespecified five-percent effect-size and positive bootstrap-lower-bound requirements failed against both controls. Target views share counts and are sensitivity analyses, not18 independent replications.

The descriptive zero-effect predictor is stronger on this primary MAE than the augmented model: error is higher by 0.005903293 (1.285%). This was not substituted as a new gate; it is an existing reported control that limits practical interpretation.

| Held lineage | Kmer MAE | Kmer+PUM MAE | Gain versus kmer |
|---|---:|---:|---:|
| AP1S1 | 0.433405 | 0.412502 | 0.020904 |
| HIAT1 | 1.000883 | 0.990323 | 0.010560 |
| IRF2BP1 | 0.302726 | 0.319268 | -0.016542 |
| MGEA5 | 0.377994 | 0.349366 | 0.028628 |
| NORAD | 0.539213 | 0.526637 | 0.012577 |
| PGBD4 | 0.361454 | 0.347191 | 0.014263 |
| SMARCA2 | 0.301712 | 0.311178 | -0.009466 |

IRF2BP1 and SMARCA2 worsen, while AP1S1,HIAT1,MGEA5,NORAD and PGBD4 improve relative to both fitted controls. Seven nominal lineages, rather than4054 independent genes, determine this uncertainty. The bootstrap covers fixed predictions across those observed lineages; it does not represent biological measurement, replicate pairing, refitting or new-study uncertainty. Matched lysate pairing remains unknown.

Independent replay checked399 models and231078 stored predictions without refitting; maximum score difference8.882e-16, maximum original-unit stationarity residual3.886e-16. All18 target views for both proteins and both primary control gates were replayed. The replay used separate arithmetic but the same root/runtime, not independent-agent execution. Within-menu ranking summaries remain descriptive and are not a localization test or a separate validated primary ranking gate.

Every approved stage stayed within hard process768MiB/job896MiB limits. All399 fits required18.344seconds and peak private memory154320896bytes(147.17MiB); the complete five-stage owned lifetimes sum to97.875seconds. Original guard boundaries were retained with the explicitly approved lower physical floor; every other worker guard stayed unchanged.

The original provisional verdict still carries its pending flag because that artifact is immutable. verified_final_status.json records the later completed replay and binds all stage receipts. Do not read the preserved old pending field as evidence that replay has not run.

Do not rescue this generation by dropping negative lineages, changing pseudocounts, fitting another PUM mode, tuning weights/lambdas or lowering thresholds. Fixed PUM binding physics and its association with PRELib already have prior art. The justified result is a small, insufficiently precise binding-model increment; it does not demonstrate small-edit localization generalization.

Next work remains the separately frozen joint known-cell implementation and its guarded selective loader/trainer. That experiment can test cell-dependent slopes under held-gene splits, while external biological-context generalization still needs an independently qualified intervention benchmark. The current literature search certified no new such benchmark.
