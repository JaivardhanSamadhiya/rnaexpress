# Failure diagnosis on exposed data

The cross-assay development result remains **NO-GO**. No model was fitted, selected or retuned, and no independent resource was searched or opened. This diagnostic addresses repeatability, target-estimator agreement, edit-design support, and exact representation collisions. It does not establish which factor caused the failure.

## Replicate coverage

| dataset | contexts | contexts_with_replicates | candidate_rows | rows_with_two_replicates |
| --- | --- | --- | --- | --- |
| astrocyte_gse330741 | 7 | 7 | 3984 | 3984 |
| mikl_gse173098 | 4825 | 4825 | 13781 | 13781 |
| moffatt_gse334718 | 12 | 0 | 6749 | 0 |
| srle | 592 | 592 | 1744 | 1744 |

Moffatt lacks paired replicate contrasts in the admitted table; its reliability is unknown here, not zero. Astrocyte slots correspond to original labels 1–9 and 11–15. Missing values stay missing. Mikl and astrocyte raw contrasts differ from author-processed estimators; their repeatability is not a certified ceiling on the processed target. SRLE replicates belong to the same single reporter experiment as the original aggregate.

## Does candidate ordering repeat?

| dataset | ordering_agreement | spearman |
| --- | --- | --- |
| astrocyte_gse330741 | 0.5243 | 0.0720 |
| mikl_gse173098 | 0.5471 | 0.0976 |
| srle | 0.7826 | 0.6008 |

Ordering agreement omits pairs tied in either measurement. 0.5 is chance-like agreement, not a formal statistical null test. Every replicate pair was used; shared replicates and overlapping candidates are not independent replications. Context-level counts and missingness remain in the CSVs. Aggregation is equal parent within frozen component, then equal component within study. No significance/effect filter was used.

## Select using other replicates, evaluate in the omitted replicate

| dataset | regret | uniform_regret | wrong_direction | correct_direction |
| --- | --- | --- | --- | --- |
| astrocyte_gse330741 | 0.3518 | 0.5000 | 0.2902 | 0.7098 |
| mikl_gse173098 | 0.4333 | 0.5000 | 0.4688 | 0.5281 |
| srle | 0.1836 | 0.5000 | 0.3100 | 0.6900 |

This uses measured outcomes from other replicates and therefore is an outcome-informed repeatability benchmark, not a deployable sequence model. Candidate subsets require a finite held-out value and at least one finite remaining replicate, with two candidates and nonzero held-out range. The two requested directions are averaged. Selected raw effects can change sign because the WT contrast is uncertain. A poor result cannot prove that no sequence model can denoise the measurements.

## Processed outcome versus mean raw contrasts

| dataset | ordering_agreement | spearman |
| --- | --- | --- |
| astrocyte_gse330741 | 0.9496 | 0.9672 |
| mikl_gse173098 | 0.8772 | 0.7648 |
| srle | 1.0000 | 1.0000 |

These estimates share measurement information and are not validation. Disagreement is an estimator/provenance diagnostic; it does not automatically make the author estimator wrong.

## Training support under the original whole-study purge

| dataset | unsupported_edit_size | parent_length_outside_training_range | any_feature_outside_training_range | any_unlearnable_constant_feature | model | training_rows | test_rows | train_constant_dimensions | unsupported_constant_dimensions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| astrocyte_gse330741 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | metadata | 22274 | 3984 | 0 | 0 |
| astrocyte_gse330741 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | composition | 22274 | 3984 | 0 | 0 |
| astrocyte_gse330741 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | kmer123 | 22274 | 3984 | 0 | 0 |
| astrocyte_gse330741 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | interaction_3 | 22274 | 3984 | 0 | 0 |
| astrocyte_gse330741 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | interaction_full | 22274 | 3984 | 0 | 0 |
| mikl_gse173098 | 0.0000 | 0.0000 | 0.0190 | 0.0000 | metadata | 11796 | 13781 | 0 | 0 |
| mikl_gse173098 | 0.0000 | 0.0000 | 0.0482 | 0.0000 | composition | 11796 | 13781 | 0 | 0 |
| mikl_gse173098 | 0.0000 | 0.0000 | 0.2935 | 0.0000 | kmer123 | 11796 | 13781 | 0 | 0 |
| mikl_gse173098 | 0.0000 | 0.0000 | 0.4946 | 0.0000 | interaction_3 | 11796 | 13781 | 0 | 0 |
| mikl_gse173098 | 0.0000 | 0.0000 | 0.8286 | 0.0000 | interaction_full | 11796 | 13781 | 0 | 0 |
| moffatt_gse334718 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | metadata | 19267 | 6749 | 0 | 0 |
| moffatt_gse334718 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | composition | 19267 | 6749 | 0 | 0 |
| moffatt_gse334718 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | kmer123 | 19267 | 6749 | 0 | 0 |
| moffatt_gse334718 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | interaction_3 | 19267 | 6749 | 0 | 0 |
| moffatt_gse334718 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | interaction_full | 19267 | 6749 | 0 | 0 |
| srle | 0.0000 | 1.0000 | 1.0000 | 0.0000 | metadata | 24514 | 1744 | 0 | 0 |
| srle | 0.0000 | 1.0000 | 1.0000 | 0.0000 | composition | 24514 | 1744 | 0 | 0 |
| srle | 0.0000 | 1.0000 | 1.0000 | 0.0000 | kmer123 | 24514 | 1744 | 0 | 0 |
| srle | 0.0000 | 1.0000 | 1.0000 | 0.0000 | interaction_3 | 24514 | 1744 | 0 | 0 |
| srle | 0.0000 | 1.0000 | 1.0000 | 0.0000 | interaction_full | 24514 | 1744 | 0 | 0 |

Fractions are component-macro candidate fractions. A constant training feature has no estimable ranking coefficient in these standardized regularized linear fits. An out-of-range feature signals extrapolation, not inevitable failure; it may be irrelevant to within-parent ranking. Length and edit-size shifts confound study, intervention design and biological domain. Every unsupported feature is listed in `unsupported_dimensions.csv`.

## Exact representation collisions

| dataset | collision_candidate_fraction | optimistic_feature_only_regret_bound | model |
| --- | --- | --- | --- |
| astrocyte_gse330741 | 0.0000 | 0.0000 | composition |
| mikl_gse173098 | 0.0002 | 0.0001 | composition |
| moffatt_gse334718 | 0.0285 | 0.0000 | composition |
| srle | 0.0000 | 0.0000 | composition |
| astrocyte_gse330741 | 0.0000 | 0.0000 | interaction_3 |
| mikl_gse173098 | 0.0000 | 0.0000 | interaction_3 |
| moffatt_gse334718 | 0.0005 | 0.0000 | interaction_3 |
| srle | 0.0000 | 0.0000 | interaction_3 |
| astrocyte_gse330741 | 0.0000 | 0.0000 | interaction_full |
| mikl_gse173098 | 0.0000 | 0.0000 | interaction_full |
| moffatt_gse334718 | 0.0005 | 0.0000 | interaction_full |
| srle | 0.0000 | 0.0000 | interaction_full |
| astrocyte_gse330741 | 0.0000 | 0.0000 | kmer123 |
| mikl_gse173098 | 0.0000 | 0.0000 | kmer123 |
| moffatt_gse334718 | 0.0005 | 0.0000 | kmer123 |
| srle | 0.0000 | 0.0000 | kmer123 |
| astrocyte_gse330741 | 0.0000 | 0.0000 | metadata |
| mikl_gse173098 | 0.0002 | 0.0001 | metadata |
| moffatt_gse334718 | 0.0285 | 0.0000 | metadata |
| srle | 0.0000 | 0.0000 | metadata |

Identical vectors cannot distinguish candidates without using extra information. The optimistic bound allows outcome-informed selection of the best feature-equivalence group separately for every parent and random selection within the group. A near-zero bound means exact collisions do not explain failure by themselves; it does not demonstrate that a fitted linear model can achieve the bound. Float32 equality matches the saved model inputs. More approximate similarity and related-sequence grouping remain unaudited.

## Interpretation boundary

These measurements can identify a specific deficiency to investigate, but cannot justify retroactively changing the failed gate, filtering noisy candidates into a favorable test, claiming universality, or consuming a new untouched resource. Separate biology, sampling noise, estimator choices and model misspecification remain possible explanations. A future proposal must state which deficiency it addresses and how that claim can fail.

All previous files are preserved. Only the new `failure_audit_20260928` namespaces are written. See `verification_receipt.json` for source hashes, preservation and analytic checks. No paid resources, new datasets, broad pytest, or protected outcomes were used.
