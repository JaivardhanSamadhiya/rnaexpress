# Parallel generalization results, 7 October 2026

**NO-GO under the unchanged strict development gate.** These are repeatedly exposed development experiments, not independent confirmation.

## Macro decisions

| model | regret | avoidable_wrong | wrong_direction |
| --- | --- | --- | --- |
| historical_H0 | 0.488228 | 0.345421 | 0.483436 |
| coverage | 0.507337 | 0.350666 | 0.488682 |
| endpoint | 0.480132 | 0.309500 | 0.447682 |
| mechanism | 0.503584 | 0.368514 | 0.506426 |
| representation | 0.495764 | 0.375978 | 0.513973 |
| scaling | 0.497810 | 0.344365 | 0.482380 |

## Held assay regret

| dataset | historical_H0 | scaling | representation | mechanism | coverage | endpoint |
| --- | --- | --- | --- | --- | --- | --- |
| astrocyte_gse330741 | 0.469872 | 0.509077 | 0.506374 | 0.542868 | 0.494785 | 0.488954 |
| mikl_gse173098 | 0.517184 | 0.517184 | 0.521102 | 0.516485 | 0.516559 | 0.491124 |
| moffatt_gse334718 | 0.448511 | 0.448511 | 0.498012 | 0.453903 | 0.461858 | 0.472921 |
| srle | 0.517344 | 0.516467 | 0.457567 | 0.501080 | 0.556146 | 0.467528 |

## Why settings are not target-selected

Each of the twenty outer track/assay models uses a configuration selected only by the three source-assay holdouts. Their input and biological exclusion hashes, inner scores and exact coefficients are retained. Four of the tracks use the same source observations; the endpoint track additionally uses 223 previously exposed SIRLOIN C1/C2 measurements for nuclear training only. Its gain, if any, cannot be assigned solely to endpoint conditioning. No target sign, motif, loss, penalty or window was chosen after outer results.

## Matched representation diagnostic

The scaling track chooses between two normalizations, so an additional pair-only short-feature comparator reuses the existing 36 inner fit scores and source-selects among exactly the three frozen pair-RMS penalties. Its four outer fits were separately frozen at `5a5e038` after the first results; this is a postfit descriptive control and cannot rescue or change the primary gate.

| model_control | dataset | regret_control | wrong_direction_control | avoidable_wrong_control | no_feasible_candidate_control | unavoidable_wrong_control | neutral_only_alternative_wrong_control | best_recovery_control | top5_best_recovery_control | pairwise_accuracy_control | model_enriched | regret_enriched | wrong_direction_enriched | avoidable_wrong_enriched | no_feasible_candidate_enriched | unavoidable_wrong_enriched | neutral_only_alternative_wrong_enriched | best_recovery_enriched | top5_best_recovery_enriched | pairwise_accuracy_enriched | enriched_track | regret_gain_enriched | avoidable_error_worsening_enriched |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| matched_pair_baseline | astrocyte_gse330741 | 0.506563 | 0.500000 | 0.500000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.493710 | representation | 0.506374 | 0.479167 | 0.479167 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.062500 | 0.506475 | representation | 0.000188 | -0.020833 |
| matched_pair_baseline | mikl_gse173098 | 0.516559 | 0.507655 | 0.199681 | 0.308930 | 0.306897 | 0.001076 | 0.423948 | 0.995073 | 0.482434 | representation | 0.521102 | 0.502684 | 0.194792 | 0.308930 | 0.306897 | 0.000995 | 0.419773 | 0.995609 | 0.479480 | representation | -0.004543 | -0.004890 |
| matched_pair_baseline | moffatt_gse334718 | 0.427401 | 0.375000 | 0.375000 | 0.000000 | 0.000000 | 0.000000 | 0.041667 | 0.041667 | 0.518498 | representation | 0.498012 | 0.583333 | 0.583333 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.041667 | 0.502635 | representation | -0.070611 | 0.208333 |
| matched_pair_baseline | srle | 0.516467 | 0.506757 | 0.262669 | 0.244088 | 0.244088 | 0.000000 | 0.362331 | 0.996622 | 0.486599 | representation | 0.457567 | 0.490709 | 0.246622 | 0.244088 | 0.244088 | 0.000000 | 0.410473 | 0.998311 | 0.541039 | representation | 0.058900 | -0.016047 |
| matched_pair_baseline | astrocyte_gse330741 | 0.506563 | 0.500000 | 0.500000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.493710 | mechanism | 0.542868 | 0.562500 | 0.562500 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.495962 | mechanism | -0.036306 | 0.062500 |
| matched_pair_baseline | mikl_gse173098 | 0.516559 | 0.507655 | 0.199681 | 0.308930 | 0.306897 | 0.001076 | 0.423948 | 0.995073 | 0.482434 | mechanism | 0.516485 | 0.504025 | 0.196466 | 0.308930 | 0.306897 | 0.000662 | 0.424409 | 0.996289 | 0.484472 | mechanism | 0.000074 | -0.003215 |
| matched_pair_baseline | moffatt_gse334718 | 0.427401 | 0.375000 | 0.375000 | 0.000000 | 0.000000 | 0.000000 | 0.041667 | 0.041667 | 0.518498 | mechanism | 0.453903 | 0.458333 | 0.458333 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.041667 | 0.520037 | mechanism | -0.026502 | 0.083333 |
| matched_pair_baseline | srle | 0.516467 | 0.506757 | 0.262669 | 0.244088 | 0.244088 | 0.000000 | 0.362331 | 0.996622 | 0.486599 | mechanism | 0.501080 | 0.500845 | 0.256757 | 0.244088 | 0.244088 | 0.000000 | 0.373311 | 0.995777 | 0.497225 | mechanism | 0.015387 | -0.005912 |

## Context and annotation audit

The outcome-free reporter audit verifies 20-base flanks on each side of the SRLE six-mer (a 46-nt local synthesis template), while full mature reporter RNA remains uncertified. Published SRLE methods identify HEK293T; the historical canonical cell field says MCF7. That annotation is preserved as historical evidence and must not be used as a factual cell descriptor in future contextual models. None of the five current utilities uses that cell field, so the mismatch does not numerically invalidate their rankings. See reporter_context_audit.md.

Exact paired-context diagnostics cover 6,880 Mikl edits across 187 genes and 2,586 Moffatt edits across six genes. Gene-macro pair-order agreement is approximately .5343 and .5492. Some Mikl preferences oppose despite the fixed replicate-support diagnostic; this identifies ambiguity for identical sequence inputs, but cannot distinguish biological context from measurement/provenance artifacts. These postfit diagnostics do not choose a model or relax its gate. See context_diagnostic.md.

## Pair supervision coverage

| policy | dataset | candidate_rows | directly_supervised_candidates | fraction |
| --- | --- | --- | --- | --- |
| connected | astrocyte_gse330741 | 3984 | 3984 | 1.000000 |
| connected | mikl_gse173098 | 13781 | 13781 | 1.000000 |
| connected | moffatt_gse334718 | 6749 | 6749 | 1.000000 |
| connected | srle | 1744 | 1744 | 1.000000 |
| historical | astrocyte_gse330741 | 3984 | 2382 | 0.597892 |
| historical | mikl_gse173098 | 13781 | 13781 | 1.000000 |
| historical | moffatt_gse334718 | 6749 | 3840 | 0.568973 |
| historical | srle | 1744 | 1744 | 1.000000 |

The coverage-oriented roster is sampled without labels; exact training ties are then omitted. The table reports actual non-tied training participation, not a guarantee of a connected labeled graph. Increased coverage is not proof that a learned predictor transfers.

## Verification and limits

284 fit checkpoints; 131,290 scores replayed (maximum error 0); 54,360 selections/regrets/wrong-direction decisions independently reconstructed. The historical 10,872 H0 choices/regrets reproduced. All 45 unique prefit hashes, prior bundles and 33 pre-existing modified files remain unchanged. Twenty-eight new scoped tests and nine prior scoped tests passed. The freeze command's initial path count included two repeated entries; the authoritative manifest contains 45 unique paths, all verified.

Mikl contains most independent genes; Astrocyte contains two, Moffatt six, SRLE one reporter. All four are spent development sources; auxiliary nuclear diversity is only two parents. SRLE has no admitted full HBB reporter sequence in these inputs. Ratio endpoints and processing differ, source raw-to-author reconstruction is incomplete, and no new biological experiment was created. A failure is evidence about these fixed methods, not an impossibility theorem. A passing gate is a development filter, not a calibrated probability, causal mechanism, novelty claim or successful independent test.
