"""Evidence-indexed synthesis of saved results; no fitting or outcome filtering."""
from .common import *

def table(frame):
    def fmt(x):
        if isinstance(x,(float,np.floating)):return f'{x:.4f}' if np.isfinite(x) else 'not estimable'
        return str(x).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(map(str,frame.columns))+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))+'\n'

def run():
    replay=readj(OUT/'clean_replay_receipt.json');decomp=readj(OUT/'decomposition_receipt.json');control=readj(OUT/'control_summary_receipt.json')
    summary=pd.read_csv(OUT/'recommendation_summary.csv').set_index('model');model=pd.read_csv(OUT/'model_comparison.csv');cov=pd.read_csv(OUT/'confidence_coverage.csv')
    reliability=pd.read_csv(OUT/'replicate_effect_reliability.csv');bench=pd.read_csv(OUT/'replicate_choice_summary.csv');rank=pd.read_csv(OUT/'replicate_rank_summary.csv').iloc[0]
    k=summary.loc['kmer123'];two=summary.loc['2mer'];evidence=[]
    def add(claim,metric,value,low=np.nan,high=np.nan,model_name='',baseline='',target='published Δ NRS',n=1744,groups=60,path='',status='frozen exploratory result',split='purged composition holdout',unit='directed candidate link',limits='Overlapping links; one reporter; previously exposed data; partial source provenance'):
        evidence.append({'claim':claim,'dataset':'SRLE','target':target,'edit_class':'composition-preserving two-position exchange in six-nt window','model':model_name,'baseline':baseline,'metric':metric,'estimate':value,'ci_low':low,'ci_high':high,'interval_type':'95% descriptive composition-class bootstrap' if np.isfinite(low) else 'not estimated / descriptive identity','evaluation_split':split,'observations':n,'observation_unit':unit,'statistical_resampling_groups':groups,'independent_biological_contexts':1,'independent_groups_note':'Composition classes are statistical resampling units, not independently sampled reporter contexts','frozen_exploratory_status':status,'independent_confirmation':False,'limitations':limits,'artifact_path':path})
    add('Historical absolute-score improvement reproduced','relative_mse_reduction',replay['historical_score_error_reduction'],.20450599534555075,.3402062272618836,'position_pair','composition','absolute published NRS',855,70,'results/srle_synthesis_20260926/clean_replay_receipt.json',split='original sequence holdout',unit='held-out six-mer')
    pm=pd.read_csv(OLD/'prediction_metrics.csv');pc=pd.read_csv(OLD/'prediction_comparisons.csv')
    for r in model.itertuples():
        if r.model!='uniform':
            add('Strict-purge quantitative prediction','relative_mse_reduction',r.mse_reduction,r.mse_reduction_ci_low,r.mse_reduction_ci_high,r.model,'composition / no change',path='results/srle_prediction_20260926/prediction_comparisons.csv')
            row=pm[pm.scheme.eq('purged_composition_holdout')&pm.model.eq(r.model)&pm.kind.eq('edit_delta')&pm.target.eq('published')].iloc[0]
            for metric in ('rmse','mae','pearson','sign_accuracy_strict','calibration_slope'):
                add('Strict-purge quantitative diagnostic',metric,row[metric],row[metric+'_ci_low'],row[metric+'_ci_high'],r.model,path='results/srle_prediction_20260926/prediction_metrics.csv')
        s=summary.loc[r.model]
        den=pd.read_csv(OUT/'recommendation_metric_denominators.csv');d=den[den.model.eq(r.model)].set_index('metric')
        for metric in ('published_regret','published_correct_direction','published_wrong_direction','wrong_both','published_best_choice','beats_uniform','top3_best_recovery'):
            n,groups=(int(d.loc[metric,'decisions']),int(d.loc[metric,'composition_classes'])) if metric in d.index else (1184,60)
            add('Candidate recommendation',metric,s[metric],s[metric+'_ci_low'],s[metric+'_ci_high'],r.model,'uniform expectation',n=n,groups=groups,path='results/srle_synthesis_20260926/recommendation_summary.csv',status='saved-prediction exploratory summary',unit='parent × requested direction')
    for target in ('rep1','rep2'):
        r=pc[pc.scheme.eq('purged_composition_holdout')&pc.model.eq('2mer')&pc.comparator.eq('composition')&pc.kind.eq('edit_delta')&pc.target.eq(target)].iloc[0]
        add('Constituent measurement consistency','relative_mse_reduction',r.relative_mse_reduction,r.ci_low,r.ci_high,'2mer','no change',target,n=1744,path='results/srle_prediction_20260926/prediction_comparisons.csv',limits='Same experiment constituents; not independent validation')
    for r in pd.read_csv(OUT/'control_metrics.csv').itertuples():add('Fixed order/null controls','relative_mse_reduction',r.mse_improvement,r.ci_low,r.ci_high,r.control,'no change',r.target,path='results/srle_synthesis_20260926/control_metrics.csv',status='fixed exploratory control batch f875a02')
    for field in ('wrong_both_correct_alternative','wrong_both_ambiguous_alternative','wrong_both_unavoidable'):
        add('Partition of selector failures',field,k[field],k[field+'_ci_low'],k[field+'_ci_high'],'kmer123',target='constituent replicate directions',n=1184,path='results/srle_synthesis_20260926/recommendation_summary.csv',status='exploratory decomposition',unit='parent × direction')
    for r in bench.itertuples():
        for metric in ('regret','correct_direction','wrong_both'):
            add('Replicate measurement-reliability benchmark',metric,getattr(r,metric),getattr(r,metric+'_ci_low'),getattr(r,metric+'_ci_high'),r.benchmark,target='other constituent replicate',n=1184,path='results/srle_synthesis_20260926/replicate_choice_summary.csv',status='exploratory benchmark, not ceiling',unit='parent × direction')
    for r in cov.itertuples():
        for metric in ('published_regret','published_correct_direction','wrong_both'):
            add(f'Confidence signal {r.signal}, coverage {r.requested_coverage:.0%}',metric,getattr(r,metric),getattr(r,metric+'_ci_low'),getattr(r,metric+'_ci_high'),r.model,n=int(r.rows),groups=int(r.statistical_groups),path='results/srle_synthesis_20260926/confidence_coverage.csv',status='exploratory; not calibrated/deployed',unit='retained parent × direction',limits='Prediction-only coverage cutoffs; changed group mix; lexical ties; no independent threshold validation')
    add('Base composition is unchanged','nonzero_delta_1mer_edges',0,path='results/srle_synthesis_20260926/decomposition_receipt.json',status='exact identity audit')
    add('Some swaps preserve dinucleotide counts','zero_delta_2mer_edges',87,path='results/srle_synthesis_20260926/decomposition_receipt.json',status='exact identity audit')
    add('Contributions concentrate in CA/AC/TC/CT','top4_absolute_centered_contribution_share',decomp['top4_absolute_centered_contribution_share'],model_name='2mer',path='results/srle_synthesis_20260926/contribution_summary.csv',status='descriptive noncausal attribution')
    add('Minimum sequence distance after purge','nearest_hamming_distance',3,n=855,groups=70,path='artifacts/srle_synthesis_20260926/nearest_training_sequences.csv',status='exact distance audit',unit='held-out local sequence')
    for r in pd.read_csv(OUT/'similarity_performance.csv').query("model=='2mer' and distance_metric=='minimum_nearest_2mer_l1'").itertuples():
        add(f'Feature-distance stratum {r.distance:g}','relative_mse_reduction',r.mse_improvement_vs_no_change,r.ci_low,r.ci_high,'2mer','no change',n=r.edges,groups=r.groups,path='results/srle_synthesis_20260926/similarity_performance.csv',status='descriptive exact-distance stratum')
    agree=pd.read_csv(OUT/'target_agreement.csv').iloc[0]
    add('Published target can oppose both constituents','published_opposes_both',agree.published_opposes_both,agree.published_opposes_both_ci_low,agree.published_opposes_both_ci_high,path='results/srle_synthesis_20260926/target_agreement.csv',status='descriptive target disagreement')
    add('Constituent effect correlation','pearson',float(reliability[reliability.magnitude_bin.eq('all')].pearson.iloc[0]),path='results/srle_synthesis_20260926/replicate_effect_reliability.csv',status='descriptive edge-weighted correlation')
    add('Replicate preferred candidate differs','preferred_differs',rank.preferred_differs,rank.preferred_differs_ci_low,rank.preferred_differs_ci_high,n=1184,path='results/srle_synthesis_20260926/replicate_rank_summary.csv',status='exploratory reliability',unit='parent × direction')
    add('No admitted untouched local context','qualifying_untouched_resources',0,n=16,groups=0,path='results/srle_synthesis_20260926/local_resource_audit.csv',status='metadata/exposure audit',split='not an evaluation',unit='catalogued resource',limits='Known local resource scope; protected/unknown members unopened; no global absence claim')
    csvsave(OUT/'final_evidence_table.csv',pd.DataFrame(evidence))
    # Four concrete edits, fixed algebraic examples plus previously selected demos.
    features=pd.read_csv(ART/'edit_features.csv',dtype={'group':str});examples=pd.read_csv(OUT/'edit_examples.csv',dtype={'group':str})
    demo=pd.read_csv(OUT/'prototype_demo_outcomes.csv');extra=[]
    for r in demo.iloc[:2].itertuples():extra.append(features[features.parent.eq(r.parent)&features.candidate.eq(r.selected)].iloc[0])
    examples=pd.concat([examples,pd.DataFrame(extra)],ignore_index=True);er=[]
    for r in examples.to_dict('records'):
        changes=', '.join(f'{c.rsplit("_",1)[1]} {r[c]:+g}' for c in examples if c.startswith('delta_2mer_') and r[c]!=0) or 'all zero'
        er.append({'parent → edit':r['parent']+' → '+r['candidate'],'positions':r['changed_positions_1based'],'Δ1-mer':'all zero','Δ2-mer':changes,'published Δ':r['published_delta'],'rep1 Δ':r['rep1_delta'],'rep2 Δ':r['rep2_delta']})
    display=model[['model','rmse','mse_reduction','regret','wrong_direction','wrong_both']].copy();display.columns=['model','effect RMSE','MSE gain vs zero','mean regret','wrong: published','wrong: both replicates']
    selected_cov=cov[cov.requested_coverage.eq(.2)][['model','signal','rows','statistical_groups','published_regret','wrong_both']].copy()
    local=pd.read_csv(OUT/'local_resource_audit.csv')[['resource','classification','qualification_reason']]
    report=f'''# Small-edit final synthesis

26 September 2026. **Claim level B: strict within-assay prediction and candidate ranking.** The original pair-model primary test remains negative. A prespecified simple 2-mer comparator retains quantitative signal, while the existing 1–3-mer model gives the lowest candidate-regret point estimate. This is one previously exposed SRLE experiment, not independent biological confirmation, a mechanism, or proof of novelty.

The centerpiece is a complete held-out demonstration: **parent local sequence + measured candidate two-position edits → frozen predicted effects → candidate ranks → a forced recommendation for each requested direction**. Every candidate and failure is retained in [all_candidate_recommendations.csv](../../artifacts/srle_synthesis_20260926/all_candidate_recommendations.csv). The deterministic [command-line prototype](../../predict_edit_candidates.py) replays the demonstrated domain; it does not generate or score new biological designs.

## 1. What exactly constitutes a small edit?

An exchange of two unequal bases at two positions within a six-nucleotide local window. All 1,744 directed links preserve the A/C/G/T count vector exactly. These are not single-nucleotide variants and not six changed bases. Stored T identifiers denote the existing RNA U/T encoding. Full reporter/physical clone sequences are not established row by row. There are 592 local anchors within **one HBB biological reporter context**, not 592 independent genes.

Dinucleotide counts change for 1,657 links but remain identical for **87/1,744 (4.99%)**. Trinucleotide counts remain identical for two links. The 2-mer model necessarily predicts zero for edits with identical 2-mer counts, even when measured effects are nonzero. Exact counts, spans and positional neighborhoods for all endpoints are in [edit_features.csv](../../artifacts/srle_synthesis_20260926/edit_features.csv).

{table(pd.DataFrame(er))}
The first two examples are the lexical first zero/nonzero Δ2-mer cases; the additional examples follow the predetermined replicate-regret selection rule. They were not chosen to make measured predictions look favorable.

## 2. Can its localization-related effect be predicted?

Yes, **partly within the defined SRLE task**. The strict-purge 2-mer model reduces published edit-effect MSE by **10.1929%**, descriptive 95% interval **1.0011%–19.9936%**; RMSE **0.367918** versus zero-change **0.388236**. Pearson r is **0.344919** (interval **0.243952–0.448959**), and strict non-tie direction accuracy is **58.6583%**. This is modest predictive accuracy, not accurate prediction of every edit. Tied 2-mer predictions count as incorrect for strict sign accuracy; the separately frozen tie-half ranking accuracy is about 61.15%.

The fresh process reconstructed **141 training partitions, 846 fixed Ridge fits and all 17,955 predictions with maximum difference 0**. Commits `0023b01` and `e5b9288`, all 41 prior bundle files and the old archive hash matched. All 82 original scoped tests passed. The historical **27.0429%** improvement is for **absolute score under the original sequence split**, not the strict-purge edit-effect estimand. [Clean replay receipt](../../results/srle_synthesis_20260926/clean_replay_receipt.json).

## 3. How much does sequence order improve beyond composition?

The 10.19% reduction is beyond composition/no change; composition cancels exactly for these edits. Constituent replicate targets give 2-mer MSE reductions of **13.9472%** and **15.2826%**, from the same frozen published-score fits. They are consistency checks within the same experiment.

The fixed new controls were frozen in commit `f875a02`, with no retries: shuffled-position 2-mers give **−3.2240%** improvement (−9.1651% to 2.6038%); deterministic random 16-dimensional features give **−0.9427%** (−2.8894% to 1.0230%). All 32 within-training-composition label permutations are retained: their improvements range from **{control['label_null_mse_gain_min']:.2%} to {control['label_null_mse_gain_max']:.2%}**, mean **{control['label_null_mse_gain_mean']:.2%}**; none reaches the real 2-mer point estimate. These controls support useful sequence-order structure. The limited null batch is not a calibrated confirmatory permutation test. A position permutation retains other order information; permuting feature names and weights together is only an identity and was checked numerically. [Controls](../../results/srle_synthesis_20260926/control_metrics.csv), [paired contrasts](../../results/srle_synthesis_20260926/control_paired_comparisons.csv).

## 4. Why does the simple 2-mer model generalize when the pair model fails?

The evidence is **consistent with a lower-dimensional, more stable representation**, but does not identify a unique causal explanation. The 2-mer representation pools 16 adjacency counts; the pair representation uses 264 position/additive-interaction features. Under the identical fixed alpha and training-only scaling, the pair model's effect MSE is **59.6241% worse than no change** (29.9225%–88.4242% worse), RMSE **0.490507**, with calibration slope **0.224** versus **0.725** for 2-mers. Its purged magnitudes are too dispersed. Shrinking training sets and withholding composition both change the problem; this audit does not isolate either cause or prove overfitting as a biological mechanism.

The 1–3-mer model also fails quantitative MSE against zero (about **24.2% worse**) despite useful ranks. Magnitude accuracy and ranking utility are different tasks. No shrinkage rescue, recalibration, feature elimination or replacement primary model was fitted.

{table(display)}
Model comparison uses unchanged frozen headline estimates. The 2-mer versus 1–3-mer paired regret advantage is not established: the 1–3-mer point advantage **0.03309** has interval **−0.04124 to 0.11191** after orienting the original contrast toward 1–3-mer. Its wrong-both point advantage **0.03122** also has an interval crossing zero. Thus the default 1–3-mer demonstration is a transparent practical choice from prior ranking point estimates, not proven unique superiority. [Model comparison](../../results/srle_synthesis_20260926/model_comparison.csv).

## 5. Does it survive removal of closely related training sequences?

Yes at the frozen tested separation. Entire composition classes and every original training sequence within nucleotide-count L1 distance ≤4 of each held class are removed; original test sequences never enter training. Exact Hamming and global Levenshtein audits find nearest distance **3 for all 855 scored sequences**. This rules out distance-1/2 training neighbors but cannot test a distance-3-to-4-to-5 gradient: none exists in this cohort.

Feature space varies. For edits whose minimum endpoint nearest-training 2-mer count L1 distance is **4**, gain is **6.51%** (−3.53% to 18.59%; 1,146 links, 55 classes); at distance **6**, gain is **16.24%** (4.22%–25.38%; 598 links, 46 classes). This does not indicate concentration only in the feature-nearest stratum. It is descriptive, with overlapping class support and no posthoc threshold. Feature-range extrapolation likewise is not a reliable error flag here. [Exact distances](../../artifacts/srle_synthesis_20260926/nearest_training_sequences.csv), [strata](../../results/srle_synthesis_20260926/similarity_performance.csv).

## 6. Can the model rank candidate edits?

Yes within all **592 original anchor sets, 2–7 candidates each**, evaluated separately for increase/decrease: **1,184 decisions per model**. Frozen scores are ranked without individual outcomes; lexical candidate ties are unchanged. The exported table contains all three original evaluation schemes, all seven models plus uniform selection probabilities: **83,712 candidate/direction/model/split rows**, including the **27,904 strict-purge rows**. It includes changed positions, predictions, measured effects, ranks, both direction flags, replicate directions, Δ2-mer counts and strict-training distances. Distances are explicitly missing for non-strict schemes rather than attaching the wrong training set.

The prototype supports the complete original candidate sets for 592 anchors, kmer123 by default and 2mer as an option. It verifies every score difference against frozen coefficients and reproduces **2,368/2,368** strict choices across the two models. It rejects new parents, candidate additions, subsets, invalid edits and duplicate U/T-normalized entries. It has no sequence-level outcomes in the runtime bundle and no individually calibrated confidence. This is a bounded frozen-prediction replay interface, not general inference on new RNAs. Four command-line demos include successes and failures under the fixed example rule. [Demo outputs and revealed measurements](../../results/srle_synthesis_20260926/prototype_demo_outcomes.csv).

## 7. How much better is ranking than uniform choice?

Class-balanced published regret is **0.319668** for 1–3-mers versus exact uniform **0.500000**: absolute gain **0.180332**, interval **0.120141–0.240978**, or a descriptive 36.1% reduction in regret. The 2-mer mean is **0.352753**, gain **0.147247** (0.086084–0.204776). Regret uses each measured candidate range; 0 is best and 1 worst within the set. It is not physical effect size.

For 1–3-mers, best-candidate recovery is **{k.published_best_choice:.2%}**, and **{k.beats_uniform:.2%}** of decisions beat their own exact uniform expected regret after class balancing. The decision-weighted median regret is **0**, but the 75th and 90th percentiles are **1**. The full distribution therefore matters. Top-three recovery is **{k.top3_best_recovery:.2%}** versus uniform **70.10%**, restricted to the **308 decisions / 30 classes with >3 candidates**; it is not evaluated trivially on smaller sets. Size and fixed effect-magnitude strata retain all denominators. Means/intervals are class-balanced; pooled quantiles explicitly give each decision equal mass. [Summary](../../results/srle_synthesis_20260926/recommendation_summary.csv), [distributions](../../results/srle_synthesis_20260926/regret_distribution.csv), [metric denominators](../../results/srle_synthesis_20260926/recommendation_metric_denominators.csv).

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

{table(selected_cov)}
These subsets change class composition; 20% means 237 decisions rather than the same independent biological groups. Their cutoffs use predictions/covariates, not outcomes, but this remains exposed exploratory threshold assessment. Do not deploy the best-looking curve as a confidence guarantee. The interface reports only cohort risk and “not individually calibrated.” All intermediate coverages and descriptive intervals are in [confidence_coverage.csv](../../results/srle_synthesis_20260926/confidence_coverage.csv).

## 11. Which sequence features drive successful predictions?

The frozen prediction equals **Σ Δdinucleotide_count × coefficient/scale**; intercepts, centering and the common composition baseline cancel. Reconstruction error is ≤**1.67×10⁻¹⁶**. In the explicitly centered coefficient representation, CA/AC/TC/CT account for **62.96%** of absolute contributions; their coefficient signs are stable across all 70 purged folds (CA/CT negative, AC/TC positive). Several small coefficients change signs, so not all 16 features are equally stable. Fold medians/IQRs describe overlapping fits, not independent uncertainty. Feature frequency, per-fold support, every contribution and conditional success/failure association are exported.

An additional documented algebraic audit separates dinucleotide weights into row/column additive terms and interaction terms. Under equal composition, additive terms reduce exactly to first/last-position contributions. About **29.32%** of summed absolute component magnitude is endpoint-encoded and **70.68%** is interaction contribution in this decomposition. Endpoint-only descriptive MSE gain is **0.43%** and interaction-component gain **10.72%**; these correlated components are not separately validated/retrained predictors. The full frozen model stays unchanged. This suggests the useful order signal is not explained solely by terminal base identity, while avoiding a claim that dinucleotide counts represent only internal adjacency.

Failure strata show 2-mer strict sign accuracy **47.16%** for |measured effect|≤0.1 versus **76.05%** above 0.5, while absolute error is larger for big effects. Among the 14 links with |predicted effect|>0.5, strict accuracy is 85.71%, leaving high-magnitude failures; this tiny group is not a validated confidence cohort. Every composition, candidate size, change span, dinucleotide stratum and feature extrapolation record remains available. No small-effect or failing group is dropped. [Contributions](../../artifacts/srle_synthesis_20260926/dinucleotide_contributions.csv), [boundary identity](../../results/srle_synthesis_20260926/boundary_component_diagnostics.csv), [failures](../../results/srle_synthesis_20260926/failure_strata.csv).

## 12. Are these features predictive or mechanistic?

**Predictive and associative sequence-order structure.** Correlated features, regularization, shared reporter context and coefficient gauge prevent causal attribution from coefficient size. This does not establish an RBP mechanism, causal dinucleotide code, universal localization grammar or intervention behavior outside the measured assay. Mechanistic confirmation and independent novelty assessment are missing; neither follows from a positive bootstrap interval.

## 13. Does it generalize to a second biological context?

**Not established.** The metadata-only audit covers the complete existing 16-resource exposure/admission catalog, the central 14-row acquisition manifest, 203-row file inventory, small-edit inventories and safe directory-name/report cross-checks. No admitted untouched qualifying second experiment was identified. No new archive, unknown/protected member, reserved outcome or external URL was opened. The directory crosswalk explicitly preserves unknown/protected status; this is not a claim that no such dataset exists globally.

{table(local)}
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
'''
    save(REPORT/'small_edit_final_synthesis.md',report.encode('utf-8'))
    captions=readj(OUT/'figure_captions.json');guide='# SRLE final figure guide\n\nAll plots use saved predictions and summaries, one biological context. PNG at 210 dpi and scalable SVG are supplied. Final layouts were visually inspected; Figure 1 text placement was corrected without changing data.\n\n'
    for r in captions:guide+=f'## {r["figure"]}\n\n{r["caption"]}\n\n[PNG](../../{r["png"]}) · [SVG](../../{r["svg"]})\n\n'
    save(REPORT/'srle_synthesis_figure_guide.md',guide.encode())
    print('Wrote 15-question synthesis and',len(evidence),'evidence rows')

if __name__=='__main__':run()
