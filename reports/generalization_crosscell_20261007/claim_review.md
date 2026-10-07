# Cross-cell estimand and candidate novelty review

7 October 2026. Read-only review of historical split code, published modeling descriptions, the prepared protocol and current metadata certificates. No new outcome dataset, target-label analysis or model fit was performed. This note does not change any protocol, feature, fold, threshold or frozen verdict.

## What the proposed split adds

The prior [FinalShot cell-transfer masks](D:/rnaexpress/src/analysis/run_finalshot_direct_transfers.py) use all Mikl source-cell rows and all target-cell rows. They prevent decision-set overlap and select settings with source biological folds, but do not remove tested target genes or their exact insert alleles from the outer source-cell fit. The [preserved results](D:/rnaexpress/reports/finalshot_transfer_results.md) failed the cell/reporter Gate E; that result is not revised here.

The new [split implementation](D:/rnaexpress/src/generalization_crosscell_20261007/splits.py) instead restricts fitting to one source cell and the two non-test gene folds. Global component purging and explicit original-gene/parent/mutant-insert checks exclude the tested target fold. Inner selection repeats the exclusions between the two remaining source folds. Concatenated source-only out-of-fold scores receive equal component weight, avoiding an unequal-fold selection artifact. Each of the 13,781 admitted rows gets one crossed-cell out-of-fold prediction; no target-cell measurement chooses a setting.

This is simultaneously **supervised gene holdout and cell holdout within one compatible projection assay**. It differs from transfer to another cell for genes already measured in the source. It does not hold out the entire study, assay technology, reporter family or species. Exact-insert exclusion is not a sequence-homology-cluster exclusion. A pretrained model may previously have seen natural sequences from a tested gene; “unseen gene” therefore refers to supervised localization fitting, not every pretraining exposure.

## Primary prior art prevents broad first claims

| Prior work | Established scope and implication |
|---|---|
| [Mikl et al., NAR 2022](https://doi.org/10.1093/nar/gkac806) | Already predicts novel reporter localization with XGBoost, four-mer counts and RBP scores, and tests aggregated 150-nt tile predictions on native transcripts. The stated held-out reporter split is a random 10% of unique variants; positive classes require enrichment in both CAD and Neuro-2a. It is not the newly proposed source-cell-only, tested-gene-excluded candidate-choice test. Do not call sequence-based neurite localization prediction novel. |
| [mRNABench author implementation](https://github.com/morrislab/mRNABench) | Already benchmarks genomic/RNA foundation embeddings with gene/homology-aware splits, RNA-localization and variant-effect tasks. Gene-disjoint evaluation and frozen embedding probes are existing methods, rather than a new algorithm invented here. |
| [TALE/SEERS primary preprint](https://www.biorxiv.org/content/10.1101/2025.06.09.658412v2.full) | Already models context-dependent synthetic 3′-UTR abundance/nuclear-cytoplasmic behavior and predicts paired SNV effects. Context-aware localization prediction and sequence-variant prioritization cannot be claimed as unprecedented. Its different operational endpoint does not supply confirmation of neurite candidate ordering. |
| [Unreviewed EukaUTR author repository](https://github.com/meilanglang/EukaUTR) | Describes transferable 3′-UTR representations and property-directed editing, with explicit interpretation limits. This is author-repository evidence, not a verified peer-reviewed performance claim. Foundation-model use and small UTR editing alone are insufficient novelty. No weights or data are admitted. |

The Mikl modeling description was checked in the pinned primary article cache, SHA256 `1d0b3a02d7097b1af0c215eb02073a3e12e97f53da559f7c46d84065f251c05c`. The other entries were checked against primary author pages/preprint text; no associated data or weights were downloaded. This is a targeted prior-art review, not proof that no other study has performed a similar crossed-cell decision benchmark.

An outcome-free future EukaUTR S1 audit could examine the authors' claimed exclusion of human/mouse/rat/zebrafish from first-stage pretraining, followed by synthetic CPU/memory feasibility. Code MIT licensing does not establish checkpoint/data licensing or download availability. Authors note substantial GC contribution to their predicted optimization; controls would need to address it. This idea is unadmitted and follows existing planned work.

## A defensible contribution, only if the gate passes

Candidate wording: **“Fixed sequence representations improve selection among small biological-insert variants for genes excluded from supervised training in a different mouse neuronal cell line, under a gene- and exact-insert-excluded, source-only selection protocol.”** The claim would name the representation that passes, both crossed cells, the original operational endpoint and the exposed-development status. It requires every frozen condition against both corrected base and source-selected additive 1–3-mer controls, plus the representation-specific information controls. A structure-versus-base gain alone does not identify structure information; a BERT-versus-base gain alone does not separate context from static pretrained lookup.

The possible novelty is an empirical result and reproducible decision benchmark for this particular two-factor holdout, with well-matched controls. The current proposal itself is not positive evidence. A passing exposed-data development filter does not erase the separate four-study NO-GO, establish statistical familywise significance across explored routes, certify prospective confirmation, or guarantee a novel biological mechanism or award-level result.

## Remaining claim boundaries

Measured candidate-minus-parent contrasts are operational localization outcomes. They are not calibrated probabilities or expected benefit for a new unmeasured edit. Both increase/decrease tasks remain; normalized regret measures relative choice quality within the tested finite candidate sets. Bootstrap uncertainty uses shared gene/component weights across cells, not independent variant or cell counts; 187 gene components are the relevant clustered scope.

The [reporter-context audit](D:/rnaexpress/reports/full_reporter_context_20261007/feasibility.md) independently establishes that Mikl WT and mutant synthesis/cloning constants differ and barcode records require care. Common reference/additive constants cancel in within-parent ranking, but nonlinear construct-context and candidate-barcode effects can remain. Thus “small variant” describes the admitted 150-nt biological insert, not a certified isolated change in the entire expressed reporter or an endogenous RNA-editing intervention. Full mature RNA, cell-specific RBP occupancy and transport mechanism remain unmeasured.

If no informed route passes, retain the failure and report the measured limits of transferable order. If one passes, preserve all failing routes and seek genuinely untouched compatible-endpoint confirmation before widening the claim. No favorable direction, gene subset, fold, assay or representation can be selected by revising the frozen gate.
