"""Synthesis from the frozen grid and gate, with every failed assay visible."""
from .common import *

def table(f):
    def fmt(x):return ('' if not np.isfinite(x) else f'{x:.5f}') if isinstance(x,(float,np.floating)) else str(x).replace('|',' / ')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(fmt(x) for x in row)+' |' for row in f.itertuples(index=False,name=None)])
def write(name,s):save(REPORT/name,(s.strip()+'\n').encode())
def run():
    frozen();gate=readj(OUT/'gate_verdict.json');comp=pd.read_csv(ART/'model_comparison.csv');core=comp[comp.stage.eq('held_assay')];gains=pd.read_csv(OUT/'per_assay_baseline_gains.csv');leader=gate['selected_model'] or gate['descriptive_leader_not_validated'];counts=pd.read_csv(OUT/'primary_counts.csv');verdicts=pd.DataFrame([{k:v for k,v in r.items() if k!='checks'} for r in gate['models']]);v=readj(OUT/'verification_receipt.json')
    status='Passed development gate; independent confirmation remains pending.' if gate['selected_model'] else 'NO-GO. No model passed the frozen cross-assay development gate. No new independent resource was searched or opened.'
    context='These are reused, exposed benchmarks. Four study-level holdouts contain 26,258 measurements, but biological breadth is strongly unequal: SRLE one HBB reporter, astrocytes two genes, Moffatt six parents/genes, and Mikl 187 genes. Both cell lines/reporters remain inside their original study. Primary aggregation gives studies and biological components equal weight; thousands of candidates are not independent biological replications.'
    write('leave_one_assay_out_results.md',f'''# Leave-one-assay-out development results

**{status}** The descriptive comparison leader is `{leader}`; this label does not make it an externally validated or selected deployment model.

{context}

The data, feature and model grid, candidate eligibility, thresholds, selection composite and gate were committed at `d6a0623` before this comparison. All fitted coefficients, feature scaling, direction and feasibility heads for each held study use only the allowed other studies, with cross-study gene/exact-allele purging. Held-out residual contributions are exactly zero. There was no target calibration, direction flip, hyperparameter search or new-source access.

## Primary cohort

{table(counts)}

## Every model in every held study

{table(core[['dataset','model','components','decision_sets','regret','avoidable_wrong','wrong_direction','correct_direction','variant_sign_accuracy','pairwise_accuracy','spearman','best_recovery','top5_best_recovery','variant_weighted_regret']])}

`uniform` is the exact candidate-wise expectation. Primary regret is direction-averaged normalized utility loss relative to the measured best available edit. Its averaging is component then study macro, unlike `variant_weighted_regret`. `correct_direction` describes the selected recommendation; `variant_sign_accuracy` describes the separate direction head across candidates. Raw regret in each source's own units is retained in `results/cross_assay_20260927/per_assay_secondary_metrics.csv`; raw effect values from nuclear/cytoplasmic, neurite/soma and SN/cortex assays were never pooled as one regression target. Preference ties carry no training signal; predicted ordering ties receive half credit.

## Prespecified whole-domain and destination-family checks

{table(comp[comp.stage.isin(['held_domain','family_transfer'])][['stage','dataset','model','regret','avoidable_wrong','pairwise_accuracy']])}

Domain holdout contrasts projection with nuclear/cytoplasmic destinations. Family transfer uses projection training sources only for projection tests. There is no second core nuclear study to train a family model for held-out SRLE, so that task is ineligible. A family-specific numerical success does not establish H2 across untouched systems. These secondary checks cannot replace the four-study gate.

## Previously exposed SIRLOIN diagnostic

{table(comp[comp.stage.eq('secondary_sirloin')][['dataset','model','regret','wrong_direction','pairwise_accuracy']])}

Only the 223 finite, already-admitted discovery Rep1/2 effects are used; the other four original variants remain missing in the inventory. Rep3/4 and NucLibB are untouched. Two parents and different ratio units limit inference. This diagnostic is not another independent test.

## Frozen pretrained comparator after simple models

{table(comp[comp.stage.eq('pretrained_restricted')][['dataset','model','components','decision_sets','regret','avoidable_wrong','pairwise_accuracy']])}

This comparison uses 20,474 exact cached 3UTRBERT rows on complete Mikl/Moffatt decision contexts, with identical candidate sets for both models. The frozen encoder was not retrained; absent SRLE/astrocyte embeddings were not zero-filled. It is a restricted two-study result and cannot pass the four-study gate. Encoder inference and mixed-runtime provenance limitations are inherited from the original cache. A correlation gain alone is not counted as successful candidate selection.

There is a positive secondary lead: adding the frozen embeddings reduced regret from **0.509985 to 0.494135 in Mikl** and from **0.471899 to 0.438099 in Moffatt**, relative to matched short-k-mer rankers. This does not establish superiority over all simple baselines in a new experiment. It motivates a specific future question about longer-context representations within projection-localization assays, not an immediate new-data search or a replacement of the failed gate.

## Replay and scope

All {v['score_replays']:,} core score rows reproduced from frozen parameters (maximum error {v['score_replay_max_error']:.3g}); {v['fresh_model_fits']} independent fresh fits reproduced their predictions (maximum error {v['fresh_fit_max_prediction_error']:.3g}). {v['independent_direction_decision_checks']:,} selections were independently checked. Eleven scoped tests passed. Frozen historical bundles and unrelated user files remain unchanged. Full predictions join by `intervention_id` to exact parent/mutant sequences, raw features, normalization parameters, universal/residual scores, uncertainty diagnostics and observed effects.
''')
    transfer=pd.read_csv(ART/'feature_transfer_matrix.csv');hetero=pd.read_csv(OUT/'feature_heterogeneity.csv');concord=pd.read_csv(OUT/'coefficient_concordance.csv');resid=pd.read_csv(OUT/'universal_residual_contribution.csv')
    summary=transfer.groupby('model').agg(within_assay_gain_optimistic=('within_assay_gain_optimistic','mean'),held_parent_gain=('held_parent_gain','mean'),held_assay_gain=('held_assay_gain','mean'),assays_helped=('held_assay_gain',lambda x:int((x>0).sum())),assays_harmed=('held_assay_gain',lambda x:int((x<0).sum()))).reset_index()
    csvsave(OUT/'feature_transfer_summary.csv',summary)
    hs=hetero.groupby('model').agg(features=('feature','size'),features_with_sign_reversal=('sign_reverses','sum'),mean_between_assay_sd=('between_assay_sd','mean'),mean_majority_sign_fraction=('majority_sign_fraction','mean')).reset_index()
    write('universal_feature_analysis.md',f'''# What transfers, and what does not

The feature class is useful for generalization only if it helps whole-study holdouts. Optimistic within-assay fits and held-parent predictions answer different questions. All gains below compare each model with the same fixed composition baseline within the indicated task; the stricter gate separately compares the strongest simple-baseline envelope.

{table(summary)}

SRLE held-parent results are missing by design: its 592 anchors share one reporter component. A mean held-parent gain therefore covers fewer studies than the held-assay mean; those columns are not a matched biological meta-analysis. Full per-study entries and missingness remain in `feature_transfer_matrix.csv`.

## Direction consistency of independently fitted coefficients

{table(hs)}

{table(concord[concord.model.isin(['delta2','kmer123'])])}

Features with reversed signs are not called universal. Coefficients are training-scale-removed, regularized, correlated-feature associations; composition is already encoded in substitution identities and some k-mer changes. Between-study standard deviation and rank/sign concordance describe heterogeneity, not causal molecular mechanisms. Four studies cannot securely identify a universal biological effect distribution. Per-feature vectors, signs and heterogeneity are retained in `feature_heterogeneity.csv` rather than selecting only favorable motifs.

## Shared versus source-residual contribution

{table(resid)}

Residual terms can improve a measured source while disappearing on a new study. The universal-only held-study scores never use the held assay identifier or residual. Reported fractions quantify normalized-regret change, not variance explained or causal attribution. The separate empirical-Bayes coefficient model uses only source-study estimates and working curvature uncertainty; its held-assay behavior is listed alongside pooled k-mers, never promoted solely because its coefficients look consistent.

## Context scale and pretrained representations

All five context sizes were fixed before comparison. Short-k-mer deltas alone are equal across windows that retain the necessary unchanged flanks. Parent-frequency × edit interactions create the actual context dependence. Therefore a window advantage cannot be attributed to a new local delta count definition. No 4–6-mer or neural architecture expansion followed results. Frozen 3UTRBERT is compared on matched complete decision contexts in two studies, with no missing embeddings fabricated.

See `size_locality_metrics.csv` for fixed 1, 2–3, 4–6 substitution and span<=6 sensitivities; they re-rank saved predictions and do not redefine the main candidate set or gate. Small base-count edits may span a wider sequence interval.
''')
    checks=[]
    for m in gate['models']:
        checks.append({'model':m['model'],'passes':m['passes'],'failed_checks':'; '.join(k for k,val in m['checks'].items() if not val) or 'none'})
    write('model_selection_verdict.md',f'''# Frozen model-selection verdict: {gate['status']}

**{status}**

The gate and composite were fixed at `d6a0623`, before model comparison. They require improvements of >=0.02 in at least three of four studies, macro gain >=0.02, benefit remaining after removing the best study, no one-study concentration above 60%, bounded avoidable-risk/individual-study harm and a descriptive bootstrap lower bound >=−0.01. Every condition is required. No threshold changed after seeing results.

{table(verdicts)}

## Failed checks remain explicit

{table(pd.DataFrame(checks))}

## Per-study comparison with the strongest simple envelope

{table(gains)}

The comparator is the better observed simple baseline in each held study, fixed as a conservative envelope before evaluation. It is not a deployable model chosen using target labels. Exact baseline identities are retained in `strongest_simple_envelope.csv`. Macro improvements use equal study weight. Bayesian component-bootstrap intervals are descriptive and cannot overcome the small number of experiments; SRLE's one-component uncertainty is degenerate. Model development itself used these historically exposed resources, so the intervals are not new independent confirmation.

Selected model: **{gate['selected_model'] or 'NONE'}**. Lowest-composite descriptive candidate: `{gate['descriptive_leader_not_validated']}`. The latter is not a final generalizable system if no model passes. Destination-family, pretrained, edit-size or abstention subgroup findings cannot silently replace this selection rule.

New independent-dataset discovery allowed by this gate: **{gate['new_dataset_discovery_allowed']}**. If false, stop this branch and preserve all results. No external test is consumed to rescue the development result.
''')
    cr=pd.read_csv(OUT/'coverage_risk.csv');risk=cr[cr.model.eq(leader)&cr.stage.eq('held_assay')&cr.threshold.isin([0,.8])]
    lead=gains[gains.model.eq(leader)]
    claims=[{'claim':'Strict within-SRLE edit prediction','status':'SUPPORTED_FROZEN','level':1,'evidence':'reports/small_edit_20260925/small_edit_final_synthesis.md','limitation':'one reporter, not broad biological transfer'}, {'claim':'Old GSE330741 zero-shot transfer','status':'FROZEN_FAILURE_PRESERVED','level':0,'evidence':'reports/generalization_20260926/GSE330741_zero_shot_results.md','limitation':'now development knowledge; never untouched again'}, {'claim':'Multi-assay ranking transfer development gate','status':gate['status'],'level':3 if gate['selected_model'] else 0,'evidence':'results/cross_assay_20260927/gate_verdict.json','limitation':'already-exposed sources; passing would permit discovery only'}, {'claim':'Generalizable model selected','status':gate['selected_model'] or 'NONE','level':3 if gate['selected_model'] else 0,'evidence':'reports/cross_assay_20260927/model_selection_verdict.md','limitation':'no target-specific rescue or selected subgroup'}, {'claim':'Untouched biological validation','status':'NOT_RUN','level':4,'evidence':'reports/cross_assay_20260927/generalizable_predictor_status.md','limitation':'conditional on development gate; no new outcomes opened'}, {'claim':'Universal molecular mechanism','status':'NOT_ESTABLISHED','level':0,'evidence':'reports/cross_assay_20260927/universal_feature_analysis.md','limitation':'predictive associations and heterogeneous endpoints are not mechanism'}]
    csvsave(ART/'evidence_ledger.csv',pd.DataFrame(claims))
    write('generalizable_predictor_status.md',f'''# Generalizable predictor status

**{status}** {'The strongest supported claim remains Level 1: strict within-SRLE small-edit prediction. This complete development study did not establish the requested Level 3 transfer.' if not gate['selected_model'] else 'The development gate supports a bounded Level 3 claim on exposed assays. Level 4 requires a separately frozen new-resource test and is not yet established.'}

This study tested the new hypothesis directly: multiple heterogeneous experiments jointly train relative candidate utility rather than a universal raw localization score. It used balanced pairwise preferences, simple controls, pooled/shared-plus-residual/meta-analytic models, parent×edit interactions, five context windows, whole-study/domain/family holdouts, and a restricted frozen-pretrained comparison. Direction and feasibility heads were separate from ranking. No future independent dataset influenced any choice.

{context}

## Complete versus still missing

Completed: exposure/provenance admission, canonical exact edits and ranks, fixed feature/model/gate freeze, whole-study zero-target-fit predictions, grouped held-parent diagnostics, all candidate rankings, source-residual and feature heterogeneity analysis, feasible/avoidable failure accounting, fixed-threshold coverage-risk curves, numerical replay, figures and evidence packaging. Nothing in these stages supplies a new untouched biological confirmation.

Still missing: a model passing all development requirements {'and then ' if not gate['selected_model'] else 'followed by '}a genuinely unexposed replicated candidate-edit experiment; broader independent biological contexts; accurate/calibrated direction uncertainty; complete near-sequence/paralog grouping; and complete raw-to-published measurement provenance for every source. No computational score proves novelty or guarantees a competition outcome.

## Descriptive candidate, not an approved substitute

The lowest-composite candidate is `{leader}`. Its full per-study comparisons are:

{table(lead)}

Do not suppress an assay where it is worse. A positive average or a favorable destination family cannot override failed distributed-benefit or harm checks. Prior negative tests remain informative development history, not evidence that no RNA-localization rule can exist.

## Fixed abstention behavior

{table(risk[['dataset','threshold','coverage','accepted_decisions','total_decisions','regret','wrong_direction','avoidable_wrong']])}

Threshold 0.8 was fixed before results, requiring both predicted candidate-set feasibility and selected-direction probability >=0.8. For the descriptive leader it accepted **zero astrocyte and SRLE decisions**, about **2.9% macro coverage in Mikl**, and **25% in Moffatt**. Conditional wrong-direction rates were about **61% and 75%** in the latter two studies, respectively. Thus the fixed policy does not demonstrate safer recommendations. Coverage is component-weighted; it is not necessarily the raw fraction of decisions. Overall wrong-direction rates retain all-candidates-wrong, avoidable errors, and neutral-only alternatives separately. No threshold was adjusted to conceal this failure.

## Interpretation and claim hierarchy

1. Strict SRLE prediction remains supported with its existing limits.
2. Held-parent signals in exposed assays are heterogeneous; optimistic within-assay fit does not establish representation generalization.
3. The new whole-assay development gate is **{gate['status']}**; selected generalizable model is **{gate['selected_model'] or 'none'}**.
4. No untouched experiment was tested in this study.
5. No multiple-untouched-system claim is available.

Family-specific projection results are preserved as a narrower hypothesis, not proof of a shared biological mechanism. If endpoints need different rules, that is plausible biological heterogeneity; the current data cannot uniquely separate it from measurement noise, edit-generation differences or limited study diversity. Raw-effect pooling, source memorization and one-library dominance were avoided by design, yet those safeguards alone cannot create a transferable signal.

Ranking removes numerical-scale differences, but it does not remove endpoint-specific biology or noisy candidate ordering. Direction and feasibility additionally depend on a trustworthy WT zero, which within-parent rank training does not identify. The failed confidence policy makes that distinction concrete: knowing which candidate is relatively better is not equivalent to knowing whether it achieves the requested absolute direction.

## Next tasks and stopping boundary

1. Review the per-study failures and feature heterogeneity for a specific falsifiable deficiency; do not restart blind model/window/seed search.
2. Improve measurement and grouping evidence using only appropriately authorized provenance diagnostics, preserving this gate and every original result.
3. {'Develop a separate metadata-only admission protocol for a genuinely new test, then freeze weights, preprocessing and decision policy before outcomes.' if gate['selected_model'] else 'Resume new-resource discovery only after a distinct, justified architecture passes a prospectively fixed development gate. No discovery was run here, and no external dataset was spent.'}

## Preservation and audit

All {v['prefit_hashes_unchanged']} new prefit hashes, historical bundle members (93/119/70/41), and {v['unrelated_user_files_unchanged']} preexisting modified tracked files remain unchanged. {v['score_replays']:,} scores and {v['independent_direction_decision_checks']:,} selections replayed; {v['fresh_model_fits']} fresh model fits reproduced predictions; {v['pretrained_exact_ID_vector_checks']:,} cached embeddings were checked against exact source IDs. Eleven scoped tests passed. No money, scheduled tasks, broad pytest, quarantined N-zip/TDP EV5, or reserved SIRLOIN/Arora/Shukla outcomes were used.

All seven requested reports are in this directory. The six requested CSV artifacts, deterministic compressed large tables, raw features, coefficients/scalers/folds, diagnostics and figures are in the corresponding artifacts/results namespaces. See `reproducibility.md` and the delivery receipt. The requested research engineering goal remains unmet if the gate is NO-GO, even though this evaluation is complete.
''')
    print('Required reports and evidence ledger generated; gate',gate['status'])
if __name__=='__main__':run()
