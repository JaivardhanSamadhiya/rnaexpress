# Small-edit final synthesis

26 September 2026. **Claim level B: strict within-assay prediction and candidate ranking.** The original pair-model primary test remains negative. A prespecified simple 2-mer comparator retains quantitative signal, while the existing 1–3-mer model gives the lowest candidate-regret point estimate. This is one previously exposed SRLE experiment, not independent biological confirmation, a mechanism, or proof of novelty.

The centerpiece is a complete held-out demonstration: **parent local sequence + measured candidate two-position edits → frozen predicted effects → candidate ranks → a forced recommendation for each requested direction**. Every candidate and failure is retained in [all_candidate_recommendations.csv](../../artifacts/srle_synthesis_20260926/all_candidate_recommendations.csv). The deterministic [command-line prototype](../../predict_edit_candidates.py) replays the demonstrated domain; it does not generate or score new biological designs.

## 1. What exactly constitutes a small edit?

An exchange of two unequal bases at two positions within a six-nucleotide local window. All 1,744 directed links preserve the A/C/G/T count vector exactly. These are not single-nucleotide variants and not six changed bases. Stored T identifiers denote the existing RNA U/T encoding. Full reporter/physical clone sequences are not established row by row. There are 592 local anchors within **one HBB biological reporter context**, not 592 independent genes.

Dinucleotide counts change for 1,657 links but remain identical for **87/1,744 (4.99%)**. Trinucleotide counts remain identical for two links. The 2-mer model necessarily predicts zero for edits with identical 2-mer counts, even when measured effects are nonzero. Exact counts, spans and positional neighborhoods for all endpoints are in [edit_features.csv](../../artifacts/srle_synthesis_20260926/edit_features.csv).

| parent → edit | positions | Δ1-mer | Δ2-mer | published Δ | rep1 Δ | rep2 Δ |
| --- | --- | --- | --- | --- | --- | --- |
| AATATC → ATAATC | 2;3 | all zero | all zero | 0.3450 | 0.3136 | 0.2231 |
| AAAACT → AAAATC | 5;6 | all zero | AC -1, AT +1, CT -1, TC +1 | 0.2521 | 0.2783 | 0.2666 |
| AAAGTC → AAATGC | 4;5 | all zero | AG -1, AT +1, GC +1, GT -1, TC -1, TG +1 | 0.4041 | -0.4433 | -0.5862 |
| AGCACT → GACACT | 1;2 | all zero | AC +1, AG -1, GA +1, GC -1 | 0.0516 | 0.1686 | 0.2510 |

The first two examples are the lexical first zero/nonzero Δ2-mer cases; the additional examples follow the predetermined replicate-regret selection rule. They were not chosen to make measured predictions look favorable.

## 2. Can its localization-related effect be predicted?

Yes, **partly within the defined SRLE task**. The strict-purge 2-mer model reduces published edit-effect MSE by **10.1929%**, descriptive 95% interval **1.0011%–19.9936%**; RMSE **0.367918** versus zero-change **0.388236**. Pearson r is **0.344919** (interval **0.243952–0.448959**), and strict non-tie direction accuracy is **58.6583%**. This is modest predictive accuracy, not accurate prediction of every edit. Tied 2-mer predictions count as incorrect for strict sign accuracy; the separately frozen tie-half ranking accuracy is about 61.15%.

The fresh process reconstructed **141 training partitions, 846 fixed Ridge fits and all 17,955 predictions with maximum difference 0**. Commits `0023b01` and `e5b9288`, all 41 prior bundle files and the old archive hash matched. All 82 original scoped tests passed. The historical **27.0429%** improvement is for **absolute score under the original sequence split**, not the strict-purge edit-effect estimand. [Clean replay receipt](../../results/srle_synthesis_20260926/clean_replay_receipt.json).

## 3. How much does sequence order improve beyond composition?

The 10.19% reduction is beyond composition/no change; composition cancels exactly for these edits. Constituent replicate targets give 2-mer MSE reductions of **13.9472%** and **15.2826%**, from the same frozen published-score fits. They are consistency checks within the same experiment.

The fixed new controls were frozen in commit `f875a02`, with no retries: shuffled-position 2-mers give **−3.2240%** improvement (−9.1651% to 2.6038%); deterministic random 16-dimensional features give **−0.9427%** (−2.8894% to 1.0230%). All 32 within-training-composition label permutations are retained: their improvements range from **-10.50% to 2.43%**, mean **-2.62%**; none reaches the real 2-mer point estimate. These controls support useful sequence-order structure. The limited null batch is not a calibrated confirmatory permutation test. A position permutation retains other order information; permuting feature names and weights together is only an identity and was checked numerically. [Controls](../../results/srle_synthesis_20260926/control_metrics.csv), [paired contrasts](../../results/srle_synthesis_20260926/control_paired_comparisons.csv).

## 4. Why does the simple 2-mer model generalize when the pair model fails?

The evidence is **consistent with a lower-dimensional, more stable representation**, but does not identify a unique causal explanation. The 2-mer representation pools 16 adjacency counts; the pair representation uses 264 position/additive-interaction features. Under the identical fixed alpha and training-only scaling, the pair model's effect MSE is **59.6241% worse than no change** (29.9225%–88.4242% worse), RMSE **0.490507**, with calibration slope **0.224** versus **0.725** for 2-mers. Its purged magnitudes are too dispersed. Shrinking training sets and withholding composition both change the problem; this audit does not isolate either cause or prove overfitting as a biological mechanism.

The 1–3-mer model also fails quantitative MSE against zero (about **24.2% worse**) despite useful ranks. Magnitude accuracy and ranking utility are different tasks. No shrinkage rescue, recalibration, feature elimination or replacement primary model was fitted.

| model | effect RMSE | MSE gain vs zero | mean regret | wrong: published | wrong: both replicates |
| --- | --- | --- | --- | --- | --- |
| 1mer | 0.3882 | 0.0000 | 0.5000 | 0.5000 | 0.3838 |
| 2mer | 0.3679 | 0.1019 | 0.3528 | 0.4038 | 0.2980 |
| 3mer | 0.4275 | -0.2122 | 0.3786 | 0.4326 | 0.2838 |
| composition | 0.3882 | 0.0000 | 0.5000 | 0.5000 | 0.3838 |
| kmer123 | 0.4327 | -0.2422 | 0.3197 | 0.4026 | 0.2668 |
| position_additive | 0.3935 | -0.0276 | 0.4322 | 0.4587 | 0.3351 |
| position_pair | 0.4905 | -0.5962 | 0.3848 | 0.4456 | 0.2818 |
| uniform | not estimable | not estimable | 0.5000 | 0.5000 | 0.3774 |

Model comparison uses unchanged frozen headline estimates. The 2-mer versus 1–3-mer paired regret advantage is not established: the 1–3-mer point advantage **0.03309** has interval **−0.04124 to 0.11191** after orienting the original contrast toward 1–3-mer. Its wrong-both point advantage **0.03122** also has an interval crossing zero. Thus the default 1–3-mer demonstration is a transparent practical choice from prior ranking point estimates, not proven unique superiority. [Model comparison](../../results/srle_synthesis_20260926/model_comparison.csv).

## 5. Does it survive removal of closely related training sequences?

Yes at the frozen tested separation. Entire composition classes and every original training sequence within nucleotide-count L1 distance ≤4 of each held class are removed; original test sequences never enter training. Exact Hamming and global Levenshtein audits find nearest distance **3 for all 855 scored sequences**. This rules out distance-1/2 training neighbors but cannot test a distance-3-to-4-to-5 gradient: none exists in this cohort.

Feature space varies. For edits whose minimum endpoint nearest-training 2-mer count L1 distance is **4**, gain is **6.51%** (−3.53% to 18.59%; 1,146 links, 55 classes); at distance **6**, gain is **16.24%** (4.22%–25.38%; 598 links, 46 classes). This does not indicate concentration only in the feature-nearest stratum. It is descriptive, with overlapping class support and no posthoc threshold. Feature-range extrapolation likewise is not a reliable error flag here. [Exact distances](../../artifacts/srle_synthesis_20260926/nearest_training_sequences.csv), [strata](../../results/srle_synthesis_20260926/similarity_performance.csv).

## 6. Can the model rank candidate edits?

Yes within all **592 original anchor sets, 2–7 candidates each**, evaluated separately for increase/decrease: **1,184 decisions per model**. Frozen scores are ranked without individual outcomes; lexical candidate ties are unchanged. The exported table contains all three original evaluation schemes, all seven models plus uniform selection probabilities: **83,712 candidate/direction/model/split rows**, including the **27,904 strict-purge rows**. It includes changed positions, predictions, measured effects, ranks, both direction flags, replicate directions, Δ2-mer counts and strict-training distances. Distances are explicitly missing for non-strict schemes rather than attaching the wrong training set.

The prototype supports the complete original candidate sets for 592 anchors, kmer123 by default and 2mer as an option. It verifies every score difference against frozen coefficients and reproduces **2,368/2,368** strict choices across the two models. It rejects new parents, candidate additions, subsets, invalid edits and duplicate U/T-normalized entries. It has no sequence-level outcomes in the runtime bundle and no individually calibrated confidence. This is a bounded frozen-prediction replay interface, not general inference on new RNAs. Four command-line demos include successes and failures under the fixed example rule. [Demo outputs and revealed measurements](../../results/srle_synthesis_20260926/prototype_demo_outcomes.csv).

## 7. How much better is ranking than uniform choice?

Class-balanced published regret is **0.319668** for 1–3-mers versus exact uniform **0.500000**: absolute gain **0.180332**, interval **0.120141–0.240978**, or a descriptive 36.1% reduction in regret. The 2-mer mean is **0.352753**, gain **0.147247** (0.086084–0.204776). Regret uses each measured candidate range; 0 is best and 1 worst within the set. It is not physical effect size.

For 1–3-mers, best-candidate recovery is **59.47%**, and **68.05%** of decisions beat their own exact uniform expected regret after class balancing. The decision-weighted median regret is **0**, but the 75th and 90th percentiles are **1**. The full distribution therefore matters. Top-three recovery is **87.12%** versus uniform **70.10%**, restricted to the **308 decisions / 30 classes with >3 candidates**; it is not evaluated trivially on smaller sets. Size and fixed effect-magnitude strata retain all denominators. Means/intervals are class-balanced; pooled quantiles explicitly give each decision equal mass. [Summary](../../results/srle_synthesis_20260926/recommendation_summary.csv), [distributions](../../results/srle_synthesis_20260926/regret_distribution.csv), [metric denominators](../../results/srle_synthesis_20260926/recommendation_metric_denominators.csv).

## 8. How often does a recommendation move the wrong way?

The default 1–3-mer selector is wrong against the **published target in 40.26%** of decisions. It moves the wrong way in **both raw-derived constituent replicates in 26.6826%** (22.8363%–30.4732%). These are different targets and must not be substituted for one another. Uniform wrong-both risk is **37.74%**. For 2-mers it is **29.80%**, and for the failed magnitude pair model **28.18%**. Ranking improvements do not make an edit reliably safe. No difficult candidate sets were removed.

## 9. How much failure is attributable to replicate disagreement?

The data cannot causally apportion failure into measurement noise and model error. Constituent edit effects correlate **r=0.7443**, Spearman **0.7214**; signs agree on **77.41% of links** or **75.53% class-balanced**. Within-set rank correlation averages **0.5507** by class. The preferred candidate differs between replicates in **29.30%** of decisions (23.88%–34.94%). Larger published effects (>0.5) have higher edge sign agreement, **87.13%**, than ≤0.1 effects, **72.68%**; this is diagnostic, not a filter.

Using one replicate to choose and the other to evaluate gives mean regrets **0.21280 / 0.21200** and wrong-both rates **18.33% / 18.39%**. These are same-experiment measurement-reliability benchmarks, not an achievable biological ceiling or a deployable sequence predictor.

The 1–3-mer **26.68% wrong-both** partitions exactly into:

- **16.62 percentage points:** every available candidate is wrong in both replicates; no forced selector can avoid failure in those measured sets.
- **5.24 points:** another candidate avoids wrong-both, though none is correct in both.
- **4.83 points:** a both-correct alternative exists and the model misses it.

Thus about 62.3% of its wrong-both mass occurs in forced-choice-infeasible sets, while **10.07 percentage points are avoidable under the measured roster**. This does not make the other errors “just noise.” Adding an unchanged-parent option or abstention would change the task and needs a separate prospective protocol.

The published effect opposes both agreeing constituents on **16.72%** of class-balanced links. The deterministic examples visibly expose this discrepancy. Raw-to-author-table provenance remains **PARTIAL**; do not assume the published target is the exact average of these two reconstructions or interchange their truth labels. [Reliability](../../results/srle_synthesis_20260926/replicate_effect_reliability.csv), [target agreement](../../results/srle_synthesis_20260926/target_agreement.csv), [failure partition](../../results/srle_synthesis_20260926/recommendation_summary.csv).

## 10. Can confidence identify unsafe recommendations?

Some prediction-only signals identify lower-risk subsets, but **no validated abstention rule exists**. All five frozen signals and all 100/80/60/40/20% coverages are reported; ties use the fixed lexical rule. For 1–3-mers, retaining the top 20% by desired-direction predicted effect lowers wrong-both from **26.68% to 11.76%**, but published regret worsens from **0.320 to 0.355**. By margin, 20% coverage gives risk **16.99%** and regret **0.363**. Model agreement does not consistently help. Coarse distance signals have only two or three levels, so lexical ties can determine many retained decisions.

| model | signal | rows | statistical_groups | published_regret | wrong_both |
| --- | --- | --- | --- | --- | --- |
| 2mer | signal_margin | 237.0000 | 29.0000 | 0.2453 | 0.2004 |
| 2mer | signal_directional_effect | 237.0000 | 23.0000 | 0.2800 | 0.1244 |
| 2mer | signal_model_agreement | 237.0000 | 49.0000 | 0.3068 | 0.2961 |
| 2mer | signal_feature_distance | 237.0000 | 39.0000 | 0.3380 | 0.2362 |
| 2mer | signal_extrapolation | 237.0000 | 34.0000 | 0.3498 | 0.2902 |
| kmer123 | signal_margin | 237.0000 | 36.0000 | 0.3631 | 0.1699 |
| kmer123 | signal_directional_effect | 237.0000 | 31.0000 | 0.3549 | 0.1176 |
| kmer123 | signal_model_agreement | 237.0000 | 47.0000 | 0.3121 | 0.2759 |
| kmer123 | signal_feature_distance | 237.0000 | 40.0000 | 0.2599 | 0.2109 |
| kmer123 | signal_extrapolation | 237.0000 | 35.0000 | 0.2862 | 0.2965 |

These subsets change class composition; 20% means 237 decisions rather than the same independent biological groups. Their cutoffs use predictions/covariates, not outcomes, but this remains exposed exploratory threshold assessment. Do not deploy the best-looking curve as a confidence guarantee. The interface reports only cohort risk and “not individually calibrated.” All intermediate coverages and descriptive intervals are in [confidence_coverage.csv](../../results/srle_synthesis_20260926/confidence_coverage.csv).

## 11. Which sequence features drive successful predictions?

The frozen prediction equals **Σ Δdinucleotide_count × coefficient/scale**; intercepts, centering and the common composition baseline cancel. Reconstruction error is ≤**1.67×10⁻¹⁶**. In the explicitly centered coefficient representation, CA/AC/TC/CT account for **62.96%** of absolute contributions; their coefficient signs are stable across all 70 purged folds (CA/CT negative, AC/TC positive). Several small coefficients change signs, so not all 16 features are equally stable. Fold medians/IQRs describe overlapping fits, not independent uncertainty. Feature frequency, per-fold support, every contribution and conditional success/failure association are exported.

An additional documented algebraic audit separates dinucleotide weights into row/column additive terms and interaction terms. Under equal composition, additive terms reduce exactly to first/last-position contributions. About **29.32%** of summed absolute component magnitude is endpoint-encoded and **70.68%** is interaction contribution in this decomposition. Endpoint-only descriptive MSE gain is **0.43%** and interaction-component gain **10.72%**; these correlated components are not separately validated/retrained predictors. The full frozen model stays unchanged. This suggests the useful order signal is not explained solely by terminal base identity, while avoiding a claim that dinucleotide counts represent only internal adjacency.

Failure strata show 2-mer strict sign accuracy **47.16%** for |measured effect|≤0.1 versus **76.05%** above 0.5, while absolute error is larger for big effects. Among the 14 links with |predicted effect|>0.5, strict accuracy is 85.71%, leaving high-magnitude failures; this tiny group is not a validated confidence cohort. Every composition, candidate size, change span, dinucleotide stratum and feature extrapolation record remains available. No small-effect or failing group is dropped. [Contributions](../../artifacts/srle_synthesis_20260926/dinucleotide_contributions.csv), [boundary identity](../../results/srle_synthesis_20260926/boundary_component_diagnostics.csv), [failures](../../results/srle_synthesis_20260926/failure_strata.csv).

## 12. Are these features predictive or mechanistic?

**Predictive and associative sequence-order structure.** Correlated features, regularization, shared reporter context and coefficient gauge prevent causal attribution from coefficient size. This does not establish an RBP mechanism, causal dinucleotide code, universal localization grammar or intervention behavior outside the measured assay. Mechanistic confirmation and independent novelty assessment are missing; neither follows from a positive bootstrap interval.

## 13. Does it generalize to a second biological context?

**Not established.** The metadata-only audit covers the complete existing 16-resource exposure/admission catalog, the central 14-row acquisition manifest, 203-row file inventory, small-edit inventories and safe directory-name/report cross-checks. No admitted untouched qualifying second experiment was identified. No new archive, unknown/protected member, reserved outcome or external URL was opened. The directory crosswalk explicitly preserves unknown/protected status; this is not a claim that no such dataset exists globally.

| resource | classification | qualification_reason |
| --- | --- | --- |
| SRLE | ALREADY EXPOSED | One reporter, original source; no independent context |
| N-zip | RESERVED / DO NOT OPEN | Quarantined uncertified truth; no outcome access |
| Mikl | ALREADY EXPOSED | True paired small edits in CAD/N2A; extensive development exposure |
| Moffatt | ALREADY EXPOSED | Paired small edits, few parents; prior development/lock exposure |
| TDP localization | ALREADY EXPOSED | Previously analyzed localization; one mutant per exact parent, no decision sets; EV5 stability stays closed |
| Astrocyte | RESERVED / DO NOT OPEN | Sealed, prior influence not established absent; cannot presume pristine |
| Arora | ALREADY EXPOSED | Tiled alternatives do not establish small-edit parent lineage; reserved replicates remain closed |
| SIRLOIN | ALREADY EXPOSED | Two SNV parents; discovery replicates used; reserved replicates not a new context |
| RNA-context | ALREADY EXPOSED | Fragments across contexts, no admitted small-mutant lineage; prior model influence |
| Shukla | PROVENANCE INSUFFICIENT | Tiled alternatives and unresolved raw/processed mapping; already exposed permitted subset |
| SEERS | PROVENANCE INSUFFICIENT | Random inserts lack parent-mutant lineage; prior screen exposure and inadequate groups |
| Faraway | ALREADY EXPOSED | Intron/configuration/barcode changes, not admitted pure small RNA substitutions |
| mutREL | PROVENANCE INSUFFICIENT | Mutation-event counts do not establish isolated mutant genotypes; numeric outcomes unopened |
| Wen speckle | PROVENANCE INSUFFICIENT | Unresolved transcribed RNA/outcome mapping; different endpoint; numeric outcomes unopened |
| External stability | DOES NOT QUALIFY | RNA decay is not localization; exposed and admission failed |
| Pretrained model resources | DOES NOT QUALIFY | Models/embeddings are not independently measured parent-edit outcomes |

The strict SRLE split, another constituent replicate, or already-used CAD/N2A measurements cannot become fresh biological confirmation. Part 14's conditional external test was therefore not triggered. [Local audit](../../results/srle_synthesis_20260926/local_resource_audit.csv), [metadata receipt](../../results/srle_synthesis_20260926/local_audit_receipt.json), [directory crosswalk](../../results/srle_synthesis_20260926/local_directory_crosswalk.json).

## 14. Exactly what evidence is missing?

An untouched, independently generated, localization-compatible experiment with authoritative parent→small-mutant relationships, unambiguous transcribed sequences/measurement mapping, multiple measured alternatives per parent, replicated effects, and enough independent biological groups. The existing breadth admission requirement is ≥20 eligible biological/gene groups, plus a source-specific frozen endpoint/scale, roster, predictor, baselines, uncertainty and success rule before outcome access. More overlapping SRLE links or a new split cannot supply this.

Also missing: full raw-to-author-table provenance, independently calibrated recommendation risk, a prospective unchanged-parent/abstention policy, mechanistic evidence and an independent novelty assessment. No amount of new architecture search on the same exposed assay resolves those gaps. The user has no wet lab access and permits no spending; no purchase or paid compute occurred. Existing discovery restrictions remain in force. [Admission contract](independent_confirmation_admission.md).

The next three tasks, in order, are: **(1)** use this frozen package to write the central within-SRLE prediction/recommendation result with its negative controls and failure rates; **(2)** have the evidence and raw/aggregate target discrepancy independently reviewed without reopening protected outcomes; **(3)** only if a legitimately available resource passes the existing admission rules, freeze and conduct one independent-context test. Task 3 is conditional, not an authorization to resume blocked discovery or a scheduled job.

## 15. Strongest defensible scientific claim

**Level B:** Within this previously exposed SRLE assay, localization-related consequences of composition-preserving two-position edits are partly predictable from local sequence-order information after withholding composition groups and removing training sequences within two edits. The simple prespecified 2-mer comparator retains a modest quantitative benefit. Sequence-based ranking of finite measured candidate sets improves over uniform choice, but substantial wrong-direction risk remains.

The original pair-model primary quantitative test is negative. The result is exploratory, conditional on the historically eligible measured roster and one biological reporter context. Independent generalization, mechanistic explanation, universal editing utility and complete novelty are **not established**.

## Reproducibility and delivery

[Reproduction specification](srle_synthesis_reproducibility.md) documents exact inputs, criteria, splits, models, seeds, formulas and execution. [Final evidence table](../../results/srle_synthesis_20260926/final_evidence_table.csv) records every major metric with units, intervals, grouping, exposure and artifact pointers. [Figure guide](srle_synthesis_figure_guide.md) links eight required figures and one confidence supplement. [Prototype guide](srle_candidate_prototype.md) provides exact commands and limitations. The final package receipt records all new file hashes and verification, separately from all preserved old bundles.

Do not touch frozen historical NO-GO results, original SRLE protocol/predictions/coefficients/rosters, existing evidence bundles, N-zip, sealed Astrocyte, TDP EV5 stability, reserved SIRLOIN/Arora/context/Shukla/Faraway outcomes, unadmitted mutREL/Wen outcomes, or unrelated user edits. Do not run unfiltered pytest, spend money, create scheduled tasks, fit a confidence rule to these held-out outcomes, or claim new biological validation.
