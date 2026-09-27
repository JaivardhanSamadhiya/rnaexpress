# Generalizable predictor status

**NO-GO. No model passed the frozen cross-assay development gate. No new independent resource was searched or opened.** The strongest supported claim remains Level 1: strict within-SRLE small-edit prediction. This complete development study did not establish the requested Level 3 transfer.

This study tested the new hypothesis directly: multiple heterogeneous experiments jointly train relative candidate utility rather than a universal raw localization score. It used balanced pairwise preferences, simple controls, pooled/shared-plus-residual/meta-analytic models, parent×edit interactions, five context windows, whole-study/domain/family holdouts, and a restricted frozen-pretrained comparison. Direction and feasibility heads were separate from ranking. No future independent dataset influenced any choice.

These are reused, exposed benchmarks. Four study-level holdouts contain 26,258 measurements, but biological breadth is strongly unequal: SRLE one HBB reporter, astrocytes two genes, Moffatt six parents/genes, and Mikl 187 genes. Both cell lines/reporters remain inside their original study. Primary aggregation gives studies and biological components equal weight; thousands of candidates are not independent biological replications.

## Complete versus still missing

Completed: exposure/provenance admission, canonical exact edits and ranks, fixed feature/model/gate freeze, whole-study zero-target-fit predictions, grouped held-parent diagnostics, all candidate rankings, source-residual and feature heterogeneity analysis, feasible/avoidable failure accounting, fixed-threshold coverage-risk curves, numerical replay, figures and evidence packaging. Nothing in these stages supplies a new untouched biological confirmation.

Still missing: a model passing all development requirements and then a genuinely unexposed replicated candidate-edit experiment; broader independent biological contexts; accurate/calibrated direction uncertainty; complete near-sequence/paralog grouping; and complete raw-to-published measurement provenance for every source. No computational score proves novelty or guarantees a competition outcome.

## Descriptive candidate, not an approved substitute

The lowest-composite candidate is `interaction_3`. Its full per-study comparisons are:

| model | dataset | baseline | regret | regret_gain | avoidable_wrong | avoidable_wrong_worsening |
| --- | --- | --- | --- | --- | --- | --- |
| interaction_3 | astrocyte_gse330741 | uniform | 0.46987 | 0.03013 | 0.50000 | 0.00000 |
| interaction_3 | mikl_gse173098 | composition | 0.51718 | -0.02971 | 0.19812 | 0.01399 |
| interaction_3 | moffatt_gse334718 | uniform | 0.44851 | 0.05149 | 0.41667 | -0.08333 |
| interaction_3 | srle | uniform | 0.51734 | -0.01734 | 0.26689 | 0.01098 |

Do not suppress an assay where it is worse. A positive average or a favorable destination family cannot override failed distributed-benefit or harm checks. Prior negative tests remain informative development history, not evidence that no RNA-localization rule can exist.

## Fixed abstention behavior

| dataset | threshold | coverage | accepted_decisions | total_decisions | regret | wrong_direction | avoidable_wrong |
| --- | --- | --- | --- | --- | --- | --- | --- |
| astrocyte_gse330741 | 0.00000 | 1.00000 | 14 | 14 | 0.46987 | 0.50000 | 0.50000 |
| astrocyte_gse330741 | 0.80000 | 0.00000 | 0 | 14 |  |  |  |
| mikl_gse173098 | 0.00000 | 1.00000 | 9650 | 9650 | 0.51718 | 0.50610 | 0.19812 |
| mikl_gse173098 | 0.80000 | 0.02865 | 335 | 9650 | 0.46784 | 0.61416 | 0.26725 |
| moffatt_gse334718 | 0.00000 | 1.00000 | 24 | 24 | 0.44851 | 0.41667 | 0.41667 |
| moffatt_gse334718 | 0.80000 | 0.25000 | 6 | 24 | 0.38307 | 0.75000 | 0.75000 |
| srle | 0.00000 | 1.00000 | 1184 | 1184 | 0.51734 | 0.51098 | 0.26689 |
| srle | 0.80000 | 0.00000 | 0 | 1184 |  |  |  |

Threshold 0.8 was fixed before results, requiring both predicted candidate-set feasibility and selected-direction probability >=0.8. For the descriptive leader it accepted **zero astrocyte and SRLE decisions**, about **2.9% macro coverage in Mikl**, and **25% in Moffatt**. Conditional wrong-direction rates were about **61% and 75%** in the latter two studies, respectively. Thus the fixed policy does not demonstrate safer recommendations. Coverage is component-weighted; it is not necessarily the raw fraction of decisions. Overall wrong-direction rates retain all-candidates-wrong, avoidable errors, and neutral-only alternatives separately. No threshold was adjusted to conceal this failure.

## Interpretation and claim hierarchy

1. Strict SRLE prediction remains supported with its existing limits.
2. Held-parent signals in exposed assays are heterogeneous; optimistic within-assay fit does not establish representation generalization.
3. The new whole-assay development gate is **NO-GO**; selected generalizable model is **none**.
4. No untouched experiment was tested in this study.
5. No multiple-untouched-system claim is available.

Family-specific projection results are preserved as a narrower hypothesis, not proof of a shared biological mechanism. If endpoints need different rules, that is plausible biological heterogeneity; the current data cannot uniquely separate it from measurement noise, edit-generation differences or limited study diversity. Raw-effect pooling, source memorization and one-library dominance were avoided by design, yet those safeguards alone cannot create a transferable signal.

Ranking removes numerical-scale differences, but it does not remove endpoint-specific biology or noisy candidate ordering. Direction and feasibility additionally depend on a trustworthy WT zero, which within-parent rank training does not identify. The failed confidence policy makes that distinction concrete: knowing which candidate is relatively better is not equivalent to knowing whether it achieves the requested absolute direction.

## Next tasks and stopping boundary

1. Review the per-study failures and feature heterogeneity for a specific falsifiable deficiency; do not restart blind model/window/seed search.
2. Improve measurement and grouping evidence using only appropriately authorized provenance diagnostics, preserving this gate and every original result.
3. Resume new-resource discovery only after a distinct, justified architecture passes a prospectively fixed development gate. No discovery was run here, and no external dataset was spent.

## Preservation and audit

All 36 new prefit hashes, historical bundle members (93/119/70/41), and 33 preexisting modified tracked files remain unchanged. 288,838 scores and 119,592 selections replayed; 8 fresh model fits reproduced predictions; 20,474 cached embeddings were checked against exact source IDs. Eleven scoped tests passed. No money, scheduled tasks, broad pytest, quarantined N-zip/TDP EV5, or reserved SIRLOIN/Arora/Shukla outcomes were used.

All seven requested reports are in this directory. The six requested CSV artifacts, deterministic compressed large tables, raw features, coefficients/scalers/folds, diagnostics and figures are in the corresponding artifacts/results namespaces. See `reproducibility.md` and the delivery receipt. The requested research engineering goal remains unmet if the gate is NO-GO, even though this evaluation is complete.
