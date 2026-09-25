"""Render reports from every frozen score, including negative comparisons."""
from .common import *


def md(frame):
    def cell(v):
        if isinstance(v,(float,np.floating)):
            return '—' if not np.isfinite(v) else f'{v:.4f}'
        return str(v).replace('|',' / ')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+
        ['| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None)])


def link(name): return f'[{name}](../../results/small_edit_20260925/{name})'


def run():
    counts=pd.read_csv(OUT/'small_edit_size_counts.csv')
    sufficient=pd.read_csv(OUT/'small_edit_data_sufficiency.csv')
    pred=pd.read_csv(OUT/'small_edit_predictions.csv')
    metric=pd.read_csv(OUT/'effect_direction_metrics.csv')
    glob=pd.read_csv(OUT/'global_prediction_metrics.csv')
    decision=pd.read_csv(OUT/'decision_metrics.csv')
    comparisons=pd.read_csv(OUT/'paired_decision_comparisons.csv')
    losses=pd.read_csv(OUT/'paired_prediction_comparisons.csv')
    primary=metric[metric.model.eq('primary')]
    ranks=pd.read_csv(OUT/'small_edit_candidate_selection.csv')
    rows=pd.read_csv(OUT/'small_edit_decisions.csv.gz')
    parent_comparisons=[]
    for (context,band),group in rows.groupby(['context','edit_size_band']):
        averages=group.groupby(['parent','model']).regret.mean().unstack()
        for comparator in averages.columns.drop('primary'):
            gain=averages[comparator]-averages.primary
            parent_comparisons.append({'context':context,'edit_size_band':band,'comparator':comparator,'parent_contexts':len(gain),
                'fraction_parent_contexts_improved':float((gain>0).mean()),'fraction_tied':float((gain==0).mean()),
                'scope':'Descriptive parent fraction; parents within genes are not independent'})
    csvsave('parent_context_comparisons.csv',pd.DataFrame(parent_comparisons))
    foldrows=[]
    for (context,band,fold),g in pred.groupby(['cell_type','edit_size_band','biological_fold']):
        mse=g.assign(error=(g.localization_change-g.pred_primary)**2).groupby('gene_name').error.mean()
        foldrows.append({'context':context,'edit_size_band':band,'fold':fold,'rows':len(g),'genes':len(mse),'gene_balanced_rmse':float(np.sqrt(mse.mean()))})
    csvsave('fold_performance.csv',pd.DataFrame(foldrows))
    inventory='''# Small-edit dataset inventory

The objective is prediction of measured localization change caused by a small sequence edit. This inventory covers all **admitted local paired intervention resources**, plus documented exclusions. It is not an exhaustive survey of all public data. Discovery of additional datasets remains blocked by the earlier automatic approval review; no restricted or unadmitted outcomes were opened.

Tier 1 is one corresponding-coordinate substitution; Tier 2 is two or three; Tier 3 is four to six. The table always separates 1, 2, 3, 4–6 and >6. A count of changed bases does not establish a short contiguous edit: coordinate span is recorded separately. Global minimum unit-cost Levenshtein distance and a deterministic optimal alignment are also recorded. For repetitive sequences, minimum alignment can shift bases and differ from experimentally aligned substitution count; it does not redefine the physical intervention. All admitted pairs here have equal-length sequences; alignment insertion/deletion operations are not necessarily laboratory insertions/deletions.

## Complete admitted counts

Distinct pairs count each parent–mutant relationship once; context measurements count repeated reporters/cells separately. SRLE counts directed measured candidate edges, including overlapping/reverse links. Its 592 anchor sequences are within one HBB reporter, not 592 independent genes. Dataset parent/gene counts overlap between size rows and must not be summed.

'''
    inventory+=md(counts[['dataset','edit_size_band','distinct_parent_mutant_pairs','unique_parents','unique_genes','contexts','variant_context_measurements']])
    inventory+='''

## Measurement and exposure

- **Mikl GSE173098:** certified parent/test-insert pairs; author-processed mutant-minus-matched-WT log2(neurite/soma), measured in CAD and Neuro-2a. Three raw paired replicate deltas support diagnostics, but are not identical to the processed effect estimator. Absolute parent/mutant measurements absent from the common table remain missing; zero is not an imputed WT measurement. Full inventory has 11,900 variants across 224 genes. New fits use only the already-certified Phase-B fold cohort: per cell, **13 / 147 / 663 / 8,896** examples for 1 / 2 / 3 / 4–6 substitutions, representing **11 / 72 / 157 / 189 genes**. This is 19,438 held-out cell measurements, 9,719 distinct pairs. Outcomes and prior broad results were already exposed; nested grouping prevents current fit leakage but cannot make the source pristine confirmation.
- **Moffatt GSE334718:** author reference-normalized localization effects, with source-specific reporter/cell contexts and uncertainty fields. Absolute parent measurements are unavailable in the certified common table. Thousands of variants arise from only 2–8 parents/genes in the small-edit strata. WT-omitted sufficiency controls and source operation classes remain identified. Already development-exposed; inventory only in this frozen study, not an independent validation cohort.
- **TDP43 GSE288185 localization only:** 2,086 four-to-six-base paired substitutions from 16 genes, one mutant per exact parent and no candidate-choice groups. Paired localization effects are available, but replicate uncertainty is absent in this table. No stability data were accessed. Previously development-exposed; inventory only in this study.
- **SIRLOIN:** 227 original single-base variants from **two** parents. Only 223 have finite discovery-replicate 1/2 measurements; four missing rows remain in inventory and are not fabricated or fitted. Workbook headers identify nuclear/cytoplasmic **ratios**, not log2 ratios. WT subtraction is on that ratio scale. Frozen SRLE model differences are on a log-score scale, so correlation/ranking/sign are reported; MAE/RMSE would be uncalibrated and are omitted. No reserved replicate outcomes, target fitting, or recalibration were used.
- **SRLE:** the original 1,744 composition-preserving two-position swaps among 592 candidate anchors and 60 composition classes, within a single HBB reporter experiment. All endpoints come from the previously frozen evaluated roster; this is not every possible pairing among all 4,096 measured six-mers. Target is mutant-minus-anchor log2 nuclear-retention score. Two previously reconstructed raw replicates are scored separately; the source aggregate uses the same experiment. Exact sequence holdout does not establish independent parent or context holdout. Full raw-to-author-Table-5 provenance remains **PARTIAL**, as documented in the prior provenance report; exact table/prediction mapping and saved replicate arithmetic are verified.

## Data sufficiency and localization of edits

'''
    inventory+=md(counts[['dataset','edit_size_band','variants_per_parent_min','variants_per_parent_median','variants_per_parent_max','parent_contexts_with_2_candidates','span_le6_measurements']])
    inventory+='''

For Mikl, only 9,416 of 17,944 full-inventory four-to-six-base context measurements span <=6 positions. Thus the Mikl category is **four to six changed bases**, not uniformly a localized six-base edit. The model cohort is a subset of this inventory. After its fixed nonzero-range choice eligibility, it supplies no one-base choice sets; two-base choice has only four genes; three-base choice has 23 genes; four-to-six-base choice has 173 genes (2,176 CAD and 2,175 Neuro-2a parents).

The full sufficiency table reports effect variance, finite sample counts, parent structure, replicate information, and measurable-effect diagnostics for each source/context/tier. Mikl raw paired-effect repeatability is weak in the largest small-edit stratum: replicate Pearson averages **0.168 CAD / 0.122 Neuro-2a**; approximately **5.64% / 6.30%** of raw three-replicate paired t intervals exclude zero. These are diagnostics of raw paired deltas, not confidence intervals on author-processed effects, a proven prediction ceiling, or a filtering criterion. SRLE paired-swap effect replicate correlation is **0.744**. Where replicate uncertainty is unavailable, the clearly-measurable fraction is unknown, not zero.

'''
    inventory+=link('small_edit_data_sufficiency.csv')+' supplies all 50 context/tier rows, including variance and replicate diagnostics. '+link('minimum_distance_counts.csv')+' reports minimum-alignment distance counts separately.\n\n'
    inventory+='''## Exclusions and protected resources

N-zip remains quarantined; Astrocyte remains sealed; TDP EV5 stability remains forbidden. mutREL mutation-event semantics and Wen RNA/outcome mapping are unadmitted. Arora, context2022 and Shukla tiled alternatives do not supply an admitted small-mutant/reference lineage (Shukla also has unresolved raw/processed mapping). SEERS random inserts lack declared parent-mutant relationships; Faraway intron/barcode configurations are not admitted small RNA substitutions. External stability has the wrong endpoint and failed admission. No nearest-sequence parents were invented, no reserved outcome schemas were inspected, and none of these sources is silently counted as independent confirmation.

## Machine-readable deliverables

'''
    inventory+='; '.join(link(n) for n in ['small_edit_pairs.csv.gz','small_edit_size_counts.csv','inventory_receipt.json','mikl_existing_fold_eligible.csv.gz'])+'.\n\nThe pair inventory includes exact sequences, coordinate edits, alignment operations, size/span, localization change, measured parent/mutant values when available, reference semantics, replicate data, context, provenance, exposure and eligibility. Missing absolute measurements remain missing. Input SHA-256 hashes are pinned in the receipt.\n'
    save(REPORT/'small_edit_dataset_inventory.md',inventory.encode())
    results='''# Small-edit prediction results

**The strongest supported result is within-assay prediction of two-position SRLE swap effects. The stronger claim of useful small-edit prediction or selection for unseen parent genes is not supported by the new Mikl analysis.** Single-nucleotide generalization is not established.

This is one frozen exploratory analysis of already-exposed development data, not a replacement for any historical NO-GO gate. The protocol and all initial fitting/evaluation code were committed in **6e793d7 before fitting**. All ten inner selections chose delta 1–3-mer Ridge over the paired interaction representation. Each cell is fitted separately; outer genes, parents and exact alleles are held out, while biological contexts are seen. All <=6-base training examples are used, but every result is reported separately by size. There were no seed retries, architecture search, significance filtering, or new SRLE fits.

## Task A: quantitative localization change in held-out Mikl genes

Units are author-processed mutant-minus-WT log2(neurite/soma). RMSE and MAE are gene-balanced. The 95% intervals resample genes, condition on the fixed fitted models and splits, and omit refitting uncertainty. They do not restore independence from earlier source exposure.

'''
    results+=md(primary[['context','edit_size_band','rmse','rmse_ci_low','rmse_ci_high','mae','sign_accuracy']])
    results+='\n\nStrong simple comparisons (the complete results include every model, not just these):\n\n'
    table=metric[metric.model.isin(['primary','delta_AU','train_mean','no_change'])].pivot(index=['context','edit_size_band'],columns='model',values='rmse').reset_index()
    results+=md(table)
    results+='\n\nGlobal descriptive correlations and calibration of the selected prediction:\n\n'
    results+=md(glob[glob.model.eq('primary')][['context','edit_size_band','global_pearson_descriptive','global_spearman_descriptive','calibration_slope_descriptive']])
    results+='\n\nPaired gene-bootstrap MSE improvement over ΔAU (positive favors the selected model):\n\n'
    results+=md(losses[losses.comparator.eq('delta_AU')&losses.metric.eq('mse')][['context','edit_size_band','gain','ci_low','ci_high','eligible_genes']])
    results+='''

The four-to-six-base model has near-zero effect correlation and is worse than ΔAU in both cells by paired MSE intervals. Small improvements over zero prediction are not sufficient evidence of useful sequence-specific intervention prediction; a training mean is competitive. One-base estimates rest on only 11 genes/13 variants per cell.

## Task B: direction prediction

Logistic predictions use a fixed 0.5 threshold and the regression-selected feature family. AUROC below is the mean within eligible genes containing both observed signs. It is different from pooled/global AUROC. In the one-base stratum **only one gene qualifies**, so values of 0 or 1 are not evidence of decisive generalization. Quantitative-model sign accuracy above and logistic probability accuracy below are different measures.

'''
    results+=md(primary[['context','edit_size_band','auroc','auroc_ci_low','auroc_ci_high','auroc_eligible_genes','balanced_accuracy','probability_accuracy']])
    results+='''

For four-to-six-base edits, balanced accuracy is approximately **0.518 CAD / 0.515 Neuro-2a**. Global gene-weighted AUROC is **0.541 / 0.544**, versus **0.549 / 0.558** for ΔAU. The primary quantitative sign accuracy of 0.614 / 0.630 is below training-mean sign accuracy of 0.626 / 0.635; exceeding 0.5 alone mostly reflects sign imbalance. Fixed-bin probability calibration, Brier scores and all paired intervals are exported. Near-constant control correlations can be numerically unstable and are not used as success evidence.

## Task C: choosing among measured candidate edits

Candidates are compared only within the same exact parent, cell and size band. The model ranks without the held-out outcome; evaluation subsequently compares those ranks with measurements. Both desired directions are retained. All metrics first average directions and parents within gene, then genes equally. Normalized regret is zero for a best observed choice and one for a worst choice. Averaged across both directions, uniform selection has exactly **0.5 expected regret**. The lexical tie policy of constant predictors is not a stochastic uniform policy.

'''
    results+=md(decision[decision.model.eq('primary')][['context','edit_size_band','eligible_genes','regret','regret_ci_low','regret_ci_high','correct_direction','wrong_direction','best_choice','within_parent_rank_correlation']])
    results+='\n\nPaired comparison with ΔAU:\n\n'
    results+=md(comparisons[comparisons.comparator.eq('delta_AU')][['context','edit_size_band','regret_gain','regret_gain_ci_low','regret_gain_ci_high','fraction_genes_improved']])
    results+='''

No size/cell combination satisfies the frozen descriptive superiority criterion against all comparators. The largest cohorts have regret **0.504 / 0.503**, close to uniform, and wrong-direction choice rates of **48.4% / 48.7%**. There is no defensible general-purpose edit-selection demonstration here. No unchanged-parent/abstention option was added after observing outcomes. Top-three recovery is trivial when there are <=3 candidates; use the exported `top3_informative` metric for sets with >3. Two-base decisions have only four genes and cannot support breadth claims.

The complete candidate CSV contains every eligible parent sequence, measured candidate, exact coordinates, desired direction, predicted/measured rank, selected candidate and its direction success. Parent-level improvement fractions (descriptive; correlated within genes) and gene-level paired improvements are both exported. Failure plots retain all eligible parents rather than selected successes.

## Fixed secondary evidence: SRLE two-position swaps

The original SRLE aggregate/risk analyses replayed to floating-point precision, including all **9,472 original model/replicate/direction choices**. No SRLE fitting, new neighborhoods, new candidates or gate changes were performed. On the original 1,744 directed candidate links, differences of frozen short-mer scores predict measured mutant-minus-anchor log2 nuclear-retention changes:

| Metric | Replicate 1 | Replicate 2 |
| --- | --- | --- |
| Pearson r (95% composition-class bootstrap CI) | 0.609 [0.565, 0.649] | 0.597 [0.533, 0.664] |
| Spearman rho | 0.607 | 0.595 |
| MAE | 0.206 [0.188, 0.226] | 0.219 [0.199, 0.241] |
| RMSE | 0.272 [0.244, 0.301] | 0.294 [0.260, 0.328] |
| Composition/no-change RMSE | 0.344 | 0.366 |
| Sign accuracy | 0.731 [0.702, 0.760] | 0.703 [0.671, 0.733] |
| Score AUROC | 0.810 | 0.775 |

The positional-pair model is competitive (r **0.587 / 0.587**, RMSE **0.278 / 0.296**), but does not establish superiority over short k-mers. Composition-preserving swaps force composition-only change predictions to zero. This result demonstrates sequence-order information within the measured assay. It does not prove a new molecular mechanism or broad generalization.

Intervals resample 60 composition classes for row-weighted candidate-edge metrics; edges overlap and include reverse links. They are **not** confidence intervals across independent biological parents or independent experiments. Source training and these replicate measurements belong to the same reporter experiment. The original selected-choice risk remains: positional-pair choices were wrong in both replicates in **20.78% of decrease / 23.57% of increase** decisions, versus **25.13% / 22.11%** for k-mers (class-weighted). These selected-choice risks must not be confused with all-edge sign error. Full raw-to-author-Table-5 lineage is still partial.

## Fixed secondary evidence: SIRLOIN single-base edits

Only 223 finite variants from two parents can be scored. Frozen short-mer effect scores have Pearson r **0.072 / −0.077**, sign accuracy **0.498 / 0.453**, and score AUROC **0.484 / 0.421** in discovery replicates 1/2. Pair scores have r **0.124 / 0.006** and sign accuracy **0.529 / 0.466**. CCTCCC motif scores correlate **0.263 / 0.316**, but have many zero changes and do not establish a general model advantage. Existing selection-gate failure remains unchanged. Source log scores and target ratio changes are uncalibrated, so magnitude errors are deliberately not reported. Two parents do not support population bootstrap claims. This does not confirm single-base transfer.

## Interpretation and remaining research need

The new analysis tests the requested small-edit consequence directly. Its negative Mikl outcome is consistent with low paired-effect repeatability, limited independent single-base data, weak signal beyond composition, and unresolved parent/context interactions. These are explanations consistent with the evidence, not proven exclusive causes. Earlier positive broad Mikl direction summaries (including the historical approximately 0.705 value) used different significance-filtered/larger-edit and cell-aggregation estimands; they cannot be carried over to this unfiltered small-edit task.

Moffatt and TDP small subsets remain useful inventory resources, but their few independent genes, limited choice structure, prior exposure and frozen scope preclude treating them as new confirmation here. The next scientific advance needs a **new, independently admitted localization dataset with measured WT and multiple small mutants per independent parent, replicated paired outcomes, and compatible endpoint semantics**. Admission and evaluation rules must be fixed before reading its outcomes. Repeated fitting on the current evaluation data cannot provide that evidence.

## Figures and full outputs

'''
    figures=['01_predicted_vs_measured','02_performance_by_size','03_direction_prediction','04_selection_regret','05_all_baselines','06_per_parent_performance','07_failure_analysis']
    for name in figures: results+=f'- [{name}](../../results/small_edit_20260925/figures/{name}.png) ([SVG](../../results/small_edit_20260925/figures/{name}.svg))\n'
    results+='\n'
    for name in ['small_edit_predictions.csv','small_edit_candidate_selection.csv','small_edit_secondary_predictions.csv','secondary_candidate_selection.csv','effect_direction_metrics.csv','global_prediction_metrics.csv','direction_calibration.csv','paired_prediction_comparisons.csv','decision_metrics.csv','paired_decision_comparisons.csv','parent_context_comparisons.csv','fold_performance.csv','secondary_effect_direction_metrics.csv','secondary_decision_metrics.csv','srle_direct_effect_intervals.csv','verification_receipt.json']:
        results+='- '+link(name)+'\n'
    results+='\nSee [the frozen protocol](small_edit_prediction_protocol.md), [data inventory](small_edit_dataset_inventory.md), [final claim](small_edit_final_claim.md), and [reproduction instructions](reproduction.md). Nothing here changes prior failed gates or establishes novelty by itself.\n'
    save(REPORT/'small_edit_prediction_results.md',results.encode())


if __name__=='__main__': run()
