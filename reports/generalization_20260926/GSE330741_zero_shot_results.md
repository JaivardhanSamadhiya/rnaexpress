# GSE330741 zero-shot result: criterion failed

The frozen SRLE predictor did **not** establish zero-shot biological transfer. Its mean parent Spearman is **0.050952 [−0.003111, 0.138983]**. The composition baseline is 0.067368; the paired primary-minus-composition advantage is **−0.016416 [−0.041437, 0.027042]**, exact one-sided block sign-flip p=0.78125. No sign reversal, recalibration, model replacement or outcome filtering followed this result.

All external results use 3,984 verified SNPs, seven 190-nt parents, five nonoverlap components and two genes (Slc1a2 and Sparc). The author-retained design has 14 matched biological replicate labels (three-cortex pools), with 11–14 positive matched pairs per admitted variant. Technical sequencing lanes are not biological replicates. Intervals below are descriptive 95% component-bootstrap intervals, not evidence of thousands of independent biological contexts. Historical exposure is PARTIALLY EXPOSED.

Protocols, implementation and source-only predictions were frozen in `0b100d3`; access marker `5ae6d4a` preceded reveal. Once-run A outcomes were preserved at `1ff9bc2` before conditional B. The UTC/local-time typographical error in the marker is disclosed in `execution_notes.md`; the timestamped JSON and git ancestry establish the order.

## All frozen quantitative models

| model | spearman | spearman_ci_low | spearman_ci_high | mse | mae | strict_sign_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| no_change | 0.000000 | 0.000000 | 0.000000 | 0.108605 | 0.294357 | 0.000000 |
| srle_2mer_full | 0.050952 | -0.003111 | 0.138983 | 0.113653 | 0.288553 | 0.536384 |
| srle_2mer_order_only | 0.010476 | -0.033826 | 0.078255 | 0.112533 | 0.290086 | 0.507745 |
| srle_3mer_full | 0.067453 | -0.004099 | 0.170791 | 0.124624 | 0.298885 | 0.530579 |
| srle_composition | 0.067368 | 0.028806 | 0.130896 | 0.111443 | 0.292800 | 0.525123 |
| srle_delta_AU | 0.030871 | -0.014204 | 0.071067 | 0.110094 | 0.291976 | 0.359974 |
| srle_kmer123_full | 0.071847 | -0.001640 | 0.177573 | 0.123296 | 0.298359 | 0.527082 |
| srle_substitution | 0.067368 | 0.028806 | 0.130896 | 0.111620 | 0.292818 | 0.525123 |

The frozen source composition and substitution models induce identical within-parent rank ordering here, despite differing predicted magnitudes. Their matching correlations do not provide two independent biological corroborations. `no_change` has undefined mathematical correlation; the prespecified operational no-ranking score is 0. All k-mer controls are secondary; their somewhat higher average correlations cannot replace the primary.

## Every parent

| parent_id | srle_2mer_full | srle_composition |
| --- | --- | --- |
| slc1a2.1_3281_3381 | 0.051985 | 0.047956 |
| slc1a2.1_3641_3721 | -0.062706 | -0.010715 |
| slc1a2.1_3781_3841 | -0.011944 | 0.038606 |
| slc1a2.1_4181_4281 | 0.147073 | 0.073282 |
| sparc_1041_1121 | 0.121355 | 0.118721 |
| sparc_661_761 | 0.174393 | 0.194824 |
| sparc_901_981 | -0.063494 | 0.008901 |

The primary is positive for four parents and negative for three. Short k-mer representation alone does not explain a general cross-assay effect: the isolated 2-mer component has mean rho 0.010476. Composition accounts for at least as much of the observed rank signal as the full frozen primary.

## Candidate choice and interpretation

The primary candidate regret is **0.446733 [0.403957, 0.488083]**, versus uniform 0.500000. Paired improvement is 0.053267 [0.011917, 0.096043], with six of seven parents improving after averaging both requested directions. Wrong-direction selection remains 7/14 (50%); the composition baseline has 6/14 (42.9%). Neither the selected candidate nor the top-five shortlist recovered the measured best edit for this primary in any of the 14 decisions. These are positive secondary regret results with important practical limits, and they do not override failed primary/baseline gates.

SRLE measures nuclear retention in a human reporter; this target measures mutant-minus-WT synaptoneurosome/cortex enrichment in mouse astrocytes. Sequence length, mutation class, parent background and measurement normalization also differ. Those differences are plausible explanations for weak transfer, not causes identified by this analysis. No claim of molecular mechanism follows.

## Mapping and endpoint provenance

All 3,984 eligible variants map exactly to one SNP and their matched 190-nt WT. The predeclared 569 poor-cloning-group variants are retained as exclusions; no new QC exclusions occurred. The primary uses published normalized `snin_ctxin_logFC(mutant) − snin_ctxin_logFC(WT)`. Reconstructed paired log2(CPM+1) contrasts correlate with the primary at 0.891–0.996 across parents, with mean absolute discrepancies 0.013–0.067. This is corroboration, not exact author REML reproduction; full raw-count-to-coefficient reconstruction remains uncertified.

Full predictions/features/QC: `artifacts/generalization_20260926/GSE330741_zero_shot_predictions.csv`. All per-parent metrics, baseline contrasts and uncertainty are in `results/generalization_20260926/test_a_*.csv`. Outcome source: [official study supplement](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142395/); assay metadata: [GEO GSE330741](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE330741).
