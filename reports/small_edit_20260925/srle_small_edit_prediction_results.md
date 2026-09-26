# SRLE small-edit prediction: frozen results

**The admitted SRLE data contain predictive sequence-order signal for measured localized six-mer swaps. That signal is strongest for nearby held-out variants; a simple 2-mer control retains a modest quantitative advantage after whole-composition holdout and removal of close training sequences. The prespecified pair model fails the strictest quantitative-effect comparison, although candidate ranking remains useful on average.** No unseen biological parent/context claim is possible from one reporter context.

The protocol, evaluation code, cohorts and split geometry were frozen in commit **0023b01 before new fitting/scoring**. The freeze SHA-256 is `c2fd8b29803779b8be3189eda36f941cc6bde9638b27d4b48ff8fc0f70ef3ba9`. All sources had prior exposure; this is a fixed exploratory robustness analysis, not fresh independent confirmation. The pair model remains the prespecified primary model. The 2-mer result is a prespecified control finding, not a replacement primary endpoint or a winner established on an untouched test set. Reported intervals are descriptive and not adjusted for the multiple model comparisons.

## What is being predicted and how many units exist

The target is a **localization-related nuclear-retention score difference between two measured variants in the same SRLE HBB reporter experiment**. The edit class is **composition-preserving six-nucleotide sequence swaps / localized six-mer edits**. In the preserved candidate roster, each swap changes **two unequal-base positions within that six-nucleotide window**. It is not a six-base replacement or single-nucleotide edit. Changed-position spans range from 2 to 6 positions.

There are 4,096 unique measured local sequences, 855 original scored test sequences from 70 composition classes, and 1,744 directed candidate links among 592 anchors in 60 composition classes. Edges overlap and include reversals. The 592 anchors are not 592 independent biological parent RNAs. The admitted table has **one shared biological reporter context**, two constituent replicate pairs, no established distinct biological-family IDs and no established full reporter sequence per row. Unknown full sequences/physical clone IDs remain missing.

Published score and constituent raw-derived NRS1/NRS2 values are retained separately. Replicate agreement is within the same experiment, not independent biological validation. Full raw-to-published production provenance remains PARTIAL; this report does not continue that investigation.

The original cohort's count coverage and nonzero candidate-range conditions remain disclosed. No additional examples were excluded to improve performance. No new candidates outside the existing measured roster were created. [Observation inventory](../../artifacts/small_edit_20260925/srle_observation_inventory.csv).

## Historical result reproduced before the new comparison

The positional-pair model's original **absolute published-score squared-error reduction is 27.0428705752478%**, with the historical 95% composition-bootstrap interval **20.4506%–34.0206%**. Original composition, positional-pair, position-additive and 1–3-mer predictions replay exactly (maximum difference 0). The 1–3-mer model's corresponding historical reduction is **27.3663%**; pair versus 1–3-mer reduction is **−0.4453%**, interval **−5.5384% to 4.6764%**. A unique pair-model advantage is not established.

That 27.04% number measures **absolute score prediction**, not the error reduction of mutant-minus-anchor effects. For direct published-score changes on the 1,744 fixed candidate links, the original pair-model reduction is **23.9105%** (interval 14.3337%–33.7018%). Both quantities are retained with their correct denominators.

## Strongest feasible holdout and leakage checks

| Evaluation | Training sequences per fit | Scored cohort | Composition overlap | Closest permitted training sequence |
| --- | --- | --- | --- | --- |
| Original sequence holdout | 3,234 | Same 855 variants / 1,744 candidate links | 70 scored classes represented | One substitution can separate train/test |
| Whole-composition holdout | 3,089–3,231 | Same cohort, accumulated over 70 group fits | Zero | One substitution can separate train/test |
| Purged composition holdout, primary | 578–2,827 | Same cohort, accumulated over 70 group fits | Zero | At least 3 Hamming and global Levenshtein edits |
| Unseen biological parent/context | Unavailable | One reporter context only | Not testable | Not a numeric failure score |

Every original test sequence stays outside every training pool. Purging excludes count vectors within L1 distance 4 of the complete held-out composition class, guaranteeing no training example within two edits of any class member. This checks a declared distance radius; it does not imply no motifs can be shared at all. Exact train/test overlap is zero. The complete six-mer graph at one-base connectivity has one component, so a fully disconnected component split would leave no meaningful train/test task.

Composition classes are statistical sequence groups, not biological families. The two harder evaluations withhold local sequence groups, not new genes or reporter backbones. Their smaller training pools also contribute to the performance gradient; the comparison does not isolate a causal effect of similarity alone. [Every split and mask](../../results/srle_prediction_20260926/split_inventory.csv) and [per-split performance](../../results/srle_prediction_20260926/split_performance.csv) are exported. A single held composition group cannot supply its own group-bootstrap interval; pooled intervals across groups are reported below rather than degenerate per-fold CIs.

## Analysis A: direct effect magnitude and sequence order

All models use the same fixed alpha=10 recipe and training-only scaling. Known composition classes use training means; an unseen class uses a training-only composition Ridge fallback. Order models predict residuals from the training composition means. The position-independent 1-mer residual is analytically zero, because each training class has centered residuals and constant base counts. Thus composition and 1-mer predictions coincide; this is expected information equivalence, not evidence against RNA base composition generally.

Direct published-score effects, all fixed models and holdout levels:

| scheme | model | mae | rmse | r2 | pearson | spearman_descriptive | sign_accuracy_strict | balanced_accuracy_tie_half |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| composition_holdout | 1mer | 0.3038 | 0.3882 | -0.0000 | — | — | 0.0000 | 0.5000 |
| composition_holdout | 2mer | 0.2752 | 0.3525 | 0.1757 | 0.4192 | 0.4140 | 0.6003 | 0.6253 |
| composition_holdout | 3mer | 0.2766 | 0.3525 | 0.1757 | 0.4225 | 0.4198 | 0.6290 | 0.6296 |
| composition_holdout | composition | 0.3038 | 0.3882 | -0.0000 | — | — | 0.0000 | 0.5000 |
| composition_holdout | kmer123 | 0.2724 | 0.3485 | 0.1944 | 0.4490 | 0.4545 | 0.6388 | 0.6393 |
| composition_holdout | position_additive | 0.2965 | 0.3813 | 0.0354 | 0.1931 | 0.2067 | 0.5900 | 0.5900 |
| composition_holdout | position_pair | 0.2618 | 0.3411 | 0.2280 | 0.4804 | 0.4892 | 0.6720 | 0.6720 |
| purged_composition_holdout | 1mer | 0.3038 | 0.3882 | -0.0000 | — | — | 0.0000 | 0.5000 |
| purged_composition_holdout | 2mer | 0.2862 | 0.3679 | 0.1019 | 0.3449 | 0.3470 | 0.5866 | 0.6115 |
| purged_composition_holdout | 3mer | 0.3362 | 0.4275 | -0.2122 | 0.2751 | 0.2810 | 0.6135 | 0.6141 |
| purged_composition_holdout | composition | 0.3038 | 0.3882 | -0.0000 | — | — | 0.0000 | 0.5000 |
| purged_composition_holdout | kmer123 | 0.3391 | 0.4327 | -0.2423 | 0.3050 | 0.3032 | 0.6216 | 0.6221 |
| purged_composition_holdout | position_additive | 0.3083 | 0.3935 | -0.0276 | 0.1025 | 0.1224 | 0.5464 | 0.5464 |
| purged_composition_holdout | position_pair | 0.3820 | 0.4905 | -0.5963 | 0.2329 | 0.2374 | 0.5757 | 0.5757 |
| sequence_holdout | 1mer | 0.3038 | 0.3882 | -0.0000 | — | — | 0.0000 | 0.5000 |
| sequence_holdout | 2mer | 0.2744 | 0.3514 | 0.1808 | 0.4256 | 0.4191 | 0.6032 | 0.6281 |
| sequence_holdout | 3mer | 0.2756 | 0.3509 | 0.1833 | 0.4302 | 0.4254 | 0.6313 | 0.6319 |
| sequence_holdout | composition | 0.3038 | 0.3882 | -0.0000 | — | — | 0.0000 | 0.5000 |
| sequence_holdout | kmer123 | 0.2708 | 0.3462 | 0.2050 | 0.4584 | 0.4634 | 0.6428 | 0.6433 |
| sequence_holdout | position_additive | 0.2962 | 0.3811 | 0.0364 | 0.1952 | 0.2088 | 0.5894 | 0.5894 |
| sequence_holdout | position_pair | 0.2598 | 0.3387 | 0.2391 | 0.4906 | 0.4996 | 0.6835 | 0.6835 |

Under the primary purged scheme, the pair model has RMSE **0.4905**, versus **0.3882** for composition/no-change; relative MSE reduction is **−59.6% [−88.4%, −29.9%]**. Its positive r=0.233 does not rescue its quantitative error. The fitted effect calibration slope is only about 0.224, consistent with overextended predictions in this test. No test-set recalibration was performed.

The prespecified **2-mer control** has RMSE **0.3679**, r **0.3449 [0.2440, 0.4490]**, and R² **0.1019**. Its direct-effect MSE reduction versus composition is **10.19% [1.00%, 19.99%]**. Because both endpoints have identical nucleotide composition, a positive effect prediction here requires sequence arrangement beyond overall base counts. This modest simple-model signal survives the declared close-neighbor purge; it is not evidence of a new molecular mechanism.

Purged effect metrics with uncertainty for the primary pair and the prespecified 2-mer control:

| target | model | mae | rmse | rmse_ci_low | rmse_ci_high | pearson | pearson_ci_low | pearson_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| published | 2mer | 0.2862 | 0.3679 | 0.3352 | 0.4010 | 0.3449 | 0.2440 | 0.4490 |
| published | position_pair | 0.3820 | 0.4905 | 0.4353 | 0.5424 | 0.2329 | 0.1391 | 0.3252 |
| rep1 | 2mer | 0.2470 | 0.3187 | 0.2921 | 0.3523 | 0.3984 | 0.3314 | 0.4575 |
| rep1 | position_pair | 0.3467 | 0.4491 | 0.3997 | 0.4954 | 0.2855 | 0.2037 | 0.3523 |
| rep2 | 2mer | 0.2548 | 0.3367 | 0.2995 | 0.3755 | 0.4037 | 0.3070 | 0.4995 |
| rep2 | position_pair | 0.3486 | 0.4544 | 0.4032 | 0.5043 | 0.3054 | 0.1786 | 0.4137 |

Pair-model relative MSE reduction compared with composition and additive short k-mers (positive means better):

| scheme | comparator | relative_mse_reduction | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| composition_holdout | composition | 0.2280 | 0.1300 | 0.3292 |
| composition_holdout | kmer123 | 0.0417 | -0.0138 | 0.0977 |
| purged_composition_holdout | composition | -0.5962 | -0.8842 | -0.2992 |
| purged_composition_holdout | kmer123 | -0.2850 | -0.4672 | -0.1049 |
| sequence_holdout | composition | 0.2391 | 0.1433 | 0.3370 |
| sequence_holdout | kmer123 | 0.0429 | -0.0105 | 0.0994 |

Incremental comparisons under purging:

| model | comparator | relative_mse_reduction | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| 1mer | composition | 0.0000 | 0.0000 | 0.0000 |
| 2mer | 1mer | 0.1019 | 0.0100 | 0.1999 |
| 3mer | 2mer | -0.3498 | -0.4966 | -0.2040 |
| kmer123 | 2mer | -0.3832 | -0.5686 | -0.2150 |
| position_pair | 3mer | -0.3168 | -0.5378 | -0.1019 |
| position_pair | kmer123 | -0.2850 | -0.4672 | -0.1049 |

Increasing feature complexity does not monotonically improve generalization. All pairwise comparisons, absolute-score metrics, R², calibration and intervals are in the full machine-readable tables. Constituent replicate improvements for the 2-mer control are **13.95% [6.58%, 20.52%]** and **15.28% [7.00%, 24.80%]**, on their own score scales. Those are consistency checks using the same original experiment.

## Analysis B: directions and choosing measured alternatives

Prediction ties receive half credit only in the explicitly labeled pairwise-ranking and balanced-accuracy metrics. Strict sign accuracy gives zero predictions no correct-direction credit. For example, purged 2-mer published-effect strict accuracy is **58.66%**, while tie-half pairwise accuracy is **61.15%**. Reporting the latter simply as sign accuracy would overstate the result.

Each model chooses a fixed candidate for each anchor and requested direction; that same choice is evaluated against both constituent replicates. Candidates are never reselected using measured values. Lexical model ties and exact uniform expected choice are different policies. Both requested directions are retained; there is no abstention or unchanged-parent option.

Candidate performance, averaging directions/anchors within each composition class and then classes equally:

| scheme | model | published_regret | published_correct_direction | published_wrong_direction | rep1_regret | rep2_regret | wrong_both |
| --- | --- | --- | --- | --- | --- | --- | --- |
| composition_holdout | 2mer | 0.3180 | 0.6133 | 0.3867 | 0.3080 | 0.3000 | 0.2689 |
| composition_holdout | kmer123 | 0.3036 | 0.6080 | 0.3920 | 0.2811 | 0.2757 | 0.2328 |
| composition_holdout | position_pair | 0.2748 | 0.6404 | 0.3596 | 0.2692 | 0.2435 | 0.2223 |
| composition_holdout | uniform | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.3774 |
| purged_composition_holdout | 2mer | 0.3528 | 0.5962 | 0.4038 | 0.3743 | 0.3617 | 0.2980 |
| purged_composition_holdout | kmer123 | 0.3197 | 0.5974 | 0.4026 | 0.3268 | 0.3352 | 0.2668 |
| purged_composition_holdout | position_pair | 0.3848 | 0.5544 | 0.4456 | 0.3691 | 0.3363 | 0.2818 |
| purged_composition_holdout | uniform | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.3774 |
| sequence_holdout | 2mer | 0.3156 | 0.6154 | 0.3846 | 0.3046 | 0.2962 | 0.2681 |
| sequence_holdout | kmer123 | 0.2962 | 0.6146 | 0.3854 | 0.2801 | 0.2787 | 0.2362 |
| sequence_holdout | position_pair | 0.2748 | 0.6389 | 0.3611 | 0.2690 | 0.2466 | 0.2218 |
| sequence_holdout | uniform | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0.3774 |

Under purging, the pair model still selects better than uniform on average: published regret **0.3848**, with improvement **0.1152 [0.0600, 0.1719]**. The 1–3-mer control has regret **0.3197**, improvement **0.1803 [0.1201, 0.2410]**, but is not a well-calibrated magnitude predictor in this split. Ranking and magnitude are distinct tasks. Pair versus 1–3-mer regret gain is **−0.0651 [−0.1381, 0.0073]**; pair superiority is not established.

Failures are substantial. The purged pair model chooses the wrong published-score direction **44.56%** of the time, and is wrong in **both** constituent replicates **28.18% [24.19%, 32.35%]**. Corresponding wrong-both rates are **26.68% [22.84%, 30.47%]** for 1–3-mers, **29.80% [25.92%, 33.64%]** for 2-mers, and **37.74% [35.23%, 40.00%]** for uniform expected choice. These class-weighted selected-choice rates are not the row-weighted sign-error rates of every candidate edge.

Separate requested directions, primary purged test:

| direction | model | published_correct_direction | published_wrong_direction | rep1_wrong_direction | rep2_wrong_direction | wrong_both |
| --- | --- | --- | --- | --- | --- | --- |
| -1 | 2mer | 0.6073 | 0.3927 | 0.4415 | 0.4541 | 0.3321 |
| -1 | kmer123 | 0.6105 | 0.3895 | 0.3891 | 0.4180 | 0.2789 |
| -1 | position_pair | 0.5613 | 0.4387 | 0.4000 | 0.4615 | 0.3011 |
| 1 | 2mer | 0.5852 | 0.4148 | 0.4065 | 0.3767 | 0.2640 |
| 1 | kmer123 | 0.5843 | 0.4157 | 0.3715 | 0.3721 | 0.2548 |
| 1 | position_pair | 0.5475 | 0.4525 | 0.3722 | 0.3878 | 0.2625 |

All **73,248 candidate-ranking rows** are saved, representing 1,744 edges × 7 models × 3 schemes × 2 requested directions. They include measured/predicted values and changes, all ranks, selected indicators and constituent outcomes. Uniform choice is evaluated analytically, not represented by a fictitious selected candidate. All **9,472** archived model/replicate/direction choice identities reproduce exactly.

## Failures and interpretation

The frozen primary-model diagnostics show published-effect directional errors near **48.7% for |Δ|<=0.1**, decreasing to **32.0% for |Δ|>0.5**; absolute error increases for larger effects. The greatest replicate-difference bin (>0.5) has approximately **51.0%** direction error, but lower bins are not monotonic. CCC presence changes error little in this cohort (about 42.4% absent versus 42.2% present). C-count and span strata vary, often with few groups; they are descriptive and do not establish causal determinants or reliable filtering rules.

Candidate Hamming distance is always two; there is only one biological context. Their influence cannot be estimated here. Overlapping neighborhood effects and replicate disagreement remain visible. No effect-size/motif/reliability threshold was used to remove difficult examples. Figure examples follow the predeclared median and median-wrong-both rules and retain the primary pair model even though a simpler model predicts magnitude better under purging.

## Claim and limits

The strongest supported wording is **qualified Claim 2**: within this SRLE reporter experiment, measured consequences of localized composition-preserving six-mer swaps contain predictable sequence-order signal on held-out variants. A prespecified 2-mer control retains a modest quantitative advantage in the purged composition-group test; multiple models retain candidate-ranking utility, with substantial direction failures. The prespecified pair model does not pass the strict quantitative comparison, and a complex-model advantage is not established.

Claim 1 (new biological parent/context generalization) is structurally untestable here. Claim 2 does not turn 60 mathematical composition groups into independent biological experiments. The bootstrap intervals condition on one experiment, fixed fits and an already-exposed cohort; no new confirmation or completely novel mechanism is claimed. This is direct predictive evidence about measured variant differences, not arbitrary RNA engineering reliability.

## Verification and deliverables

All **17,955 held-out sequence/model/scheme predictions** replay from saved coefficients with maximum difference **0**. All **24,864 deterministic candidate decisions** replay; metric recomputation using independent library functions differs by at most **8.9e-16**. **82 scoped tests pass**. Old freeze manifests and all 70 prior evidence-bundle files remain unchanged. No unfiltered pytest was run. The new evaluation trained once; no seeds, models or cohorts were revised after these results.

- [Frozen protocol](srle_small_edit_prediction_protocol.md)
- [Plain-language final claim: ten questions](srle_final_predictive_claim.md)
- [Held-out predictions](../../artifacts/small_edit_20260925/srle_heldout_predictions.csv)
- [Every candidate ranking](../../artifacts/small_edit_20260925/srle_candidate_selection.csv) and [requested filename alias](../../artifacts/small_edit_20260925/heldout_candidate_predictions.csv)
- [Centerpiece PNG](../../artifacts/small_edit_20260925/srle_small_edit_prediction_figure.png) / [SVG](../../artifacts/small_edit_20260925/srle_small_edit_prediction_figure.svg)
- [Prediction metrics](../../results/srle_prediction_20260926/prediction_metrics.csv) / [paired comparisons](../../results/srle_prediction_20260926/prediction_comparisons.csv)
- [Decision metrics](../../results/srle_prediction_20260926/decision_metrics.csv) / [paired comparisons](../../results/srle_prediction_20260926/decision_comparisons.csv)
- [Failure diagnostics](../../results/srle_prediction_20260926/failure_analysis.csv) / [fixed-rule examples](../../results/srle_prediction_20260926/example_choices.csv)
- [Verification receipt](../../results/srle_prediction_20260926/verification_receipt.json)

Reproduction uses bundled Codex Python and `src.srle_prediction_20260926`; coefficients/scalers, original masks and hashes are saved. The output writer preserves existing bytes and refuses changed overwrites. Do not rerun `freeze` or fit alternative models in this study namespace. A replay may need a separate copied output directory because elapsed-time test logs are intentionally immutable. This analysis closes the specified fixed comparison; its limits do not justify a test-set rescue search.
