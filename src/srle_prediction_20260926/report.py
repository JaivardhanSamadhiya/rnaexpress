from .core import *
from .evaluate import sufficient,calculate


def md(frame):
    def cell(v):
        if isinstance(v,(float,np.floating)):return f'{v:.4f}' if np.isfinite(v) else '—'
        return str(v).replace('|',' / ')
    return '\n'.join(['| '+' | '.join(frame.columns)+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+
        ['| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None)])


def run():
    m=pd.read_csv(OUT/'prediction_metrics.csv');c=pd.read_csv(OUT/'prediction_comparisons.csv')
    d=pd.read_csv(OUT/'decision_metrics.csv');v=pd.read_csv(OUT/'decision_comparisons.csv')
    pred=pd.read_csv(ART/'srle_heldout_predictions.csv',dtype={'group':str,'held_group':str})
    effect=pd.read_csv(OUT/'edit_effect_predictions.csv',dtype={'group':str})
    splits=pd.read_csv(OUT/'split_inventory.csv',dtype={'held_group':str})
    rows=[]
    for (scheme,held,model),g in pred.groupby(['scheme','held_group','model']):
        split=splits[(splits.scheme==scheme)&(splits.held_group==held)].iloc[0]
        for target,column in [('published','nrs'),('rep1','NRS1'),('rep2','NRS2')]:
            point=calculate(sufficient(g[column].to_numpy(),g.predicted_score.to_numpy()).sum(0,keepdims=True))
            rows.append({'kind':'score','scheme':scheme,'held_group':held,'model':model,'target':target,
                'train_sequences':split.train_sequences,'test_sequences':len(g),'test_groups':g.group.nunique(),
                **{key:float(values[0]) for key,values in point.items()},
                'ci_status':'see pooled cluster-bootstrap table' if held=='original_hash' else 'not estimable from one held statistical group; pooled CI reported separately'})
    csvsave(OUT/'split_performance.csv',pd.DataFrame(rows))
    report='''# SRLE small-edit prediction: frozen results

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

'''
    report+=md(m[(m.kind=='edit_delta')&(m.target=='published')][['scheme','model','mae','rmse','r2','pearson','spearman_descriptive','sign_accuracy_strict','balanced_accuracy_tie_half']])
    report+='''

Under the primary purged scheme, the pair model has RMSE **0.4905**, versus **0.3882** for composition/no-change; relative MSE reduction is **−59.6% [−88.4%, −29.9%]**. Its positive r=0.233 does not rescue its quantitative error. The fitted effect calibration slope is only about 0.224, consistent with overextended predictions in this test. No test-set recalibration was performed.

The prespecified **2-mer control** has RMSE **0.3679**, r **0.3449 [0.2440, 0.4490]**, and R² **0.1019**. Its direct-effect MSE reduction versus composition is **10.19% [1.00%, 19.99%]**. Because both endpoints have identical nucleotide composition, a positive effect prediction here requires sequence arrangement beyond overall base counts. This modest simple-model signal survives the declared close-neighbor purge; it is not evidence of a new molecular mechanism.

Purged effect metrics with uncertainty for the primary pair and the prespecified 2-mer control:

'''
    report+=md(m[(m.kind=='edit_delta')&(m.scheme=='purged_composition_holdout')&m.model.isin(['position_pair','2mer'])][['target','model','mae','rmse','rmse_ci_low','rmse_ci_high','pearson','pearson_ci_low','pearson_ci_high']])
    report+='''

Pair-model relative MSE reduction compared with composition and additive short k-mers (positive means better):

'''
    report+=md(c[(c.kind=='edit_delta')&(c.target=='published')&(c.model=='position_pair')&c.comparator.isin(['composition','kmer123'])][['scheme','comparator','relative_mse_reduction','ci_low','ci_high']])
    report+='''

Incremental comparisons under purging:

'''
    inc=c[(c.kind=='edit_delta')&(c.target=='published')&(c.scheme=='purged_composition_holdout')]
    inc=inc[((inc.model=='1mer')&(inc.comparator=='composition'))|((inc.model=='2mer')&(inc.comparator=='1mer'))|((inc.model=='3mer')&(inc.comparator=='2mer'))|((inc.model=='kmer123')&(inc.comparator=='2mer'))|((inc.model=='position_pair')&inc.comparator.isin(['3mer','kmer123']))]
    report+=md(inc[['model','comparator','relative_mse_reduction','ci_low','ci_high']])
    report+='''

Increasing feature complexity does not monotonically improve generalization. All pairwise comparisons, absolute-score metrics, R², calibration and intervals are in the full machine-readable tables. Constituent replicate improvements for the 2-mer control are **13.95% [6.58%, 20.52%]** and **15.28% [7.00%, 24.80%]**, on their own score scales. Those are consistency checks using the same original experiment.

## Analysis B: directions and choosing measured alternatives

Prediction ties receive half credit only in the explicitly labeled pairwise-ranking and balanced-accuracy metrics. Strict sign accuracy gives zero predictions no correct-direction credit. For example, purged 2-mer published-effect strict accuracy is **58.66%**, while tie-half pairwise accuracy is **61.15%**. Reporting the latter simply as sign accuracy would overstate the result.

Each model chooses a fixed candidate for each anchor and requested direction; that same choice is evaluated against both constituent replicates. Candidates are never reselected using measured values. Lexical model ties and exact uniform expected choice are different policies. Both requested directions are retained; there is no abstention or unchanged-parent option.

Candidate performance, averaging directions/anchors within each composition class and then classes equally:

'''
    report+=md(d[(d.direction==0)&d.model.isin(['position_pair','kmer123','2mer','uniform'])][['scheme','model','published_regret','published_correct_direction','published_wrong_direction','rep1_regret','rep2_regret','wrong_both']])
    report+='''

Under purging, the pair model still selects better than uniform on average: published regret **0.3848**, with improvement **0.1152 [0.0600, 0.1719]**. The 1–3-mer control has regret **0.3197**, improvement **0.1803 [0.1201, 0.2410]**, but is not a well-calibrated magnitude predictor in this split. Ranking and magnitude are distinct tasks. Pair versus 1–3-mer regret gain is **−0.0651 [−0.1381, 0.0073]**; pair superiority is not established.

Failures are substantial. The purged pair model chooses the wrong published-score direction **44.56%** of the time, and is wrong in **both** constituent replicates **28.18% [24.19%, 32.35%]**. Corresponding wrong-both rates are **26.68% [22.84%, 30.47%]** for 1–3-mers, **29.80% [25.92%, 33.64%]** for 2-mers, and **37.74% [35.23%, 40.00%]** for uniform expected choice. These class-weighted selected-choice rates are not the row-weighted sign-error rates of every candidate edge.

Separate requested directions, primary purged test:

'''
    report+=md(d[(d.scheme=='purged_composition_holdout')&d.direction.isin([-1,1])&d.model.isin(['position_pair','kmer123','2mer'])][['direction','model','published_correct_direction','published_wrong_direction','rep1_wrong_direction','rep2_wrong_direction','wrong_both']])
    report+='''

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
'''
    save(REPORT/'srle_small_edit_prediction_results.md',report.encode())
    claim='''# Final predictive claim: measured localized six-mer edits

**Within the SRLE HBB reporter experiment, measured localization-related consequences of composition-preserving six-nucleotide sequence swaps contain predictable sequence-order signal on held-out variants. A simple, prespecified 2-mer model retains a modest quantitative advantage after withholding composition groups and purging close training sequences. Candidate ranking remains useful on average, but wrong-direction choices are frequent.**

This is qualified **Claim 2**, limited to the observed assay and a fixed exploratory reanalysis of previously exposed data. It is not Claim 1 (unseen biological parent/context generalization). The original positional-pair model remains the prespecified primary model: it **fails** the strictest effect-magnitude comparison. The 2-mer finding is a prespecified control result, not a substituted primary success or independently confirmed winner. The constituent replicate checks are not independent biological validation.

1. **Can the consequences be predicted?** Partly, within this measured assay. In the strict purged test, 2-mer predicted versus measured published-score changes have Pearson r=**0.345 [0.244, 0.449]**, RMSE **0.368**, and R² **0.102**. That is a modest predictive signal, not dependable prediction for every edit. The primary pair model retains positive correlation but has RMSE **0.491** and negative R²; its quantitative predictions do not pass this test.

2. **How small are the edits?** The supported class is **composition-preserving six-nucleotide sequence swaps / localized six-mer edits**. The existing roster changes **two positions inside a six-nucleotide window**, by swapping unequal bases. It is neither a single-base substitution claim nor a claim of six changed bases. The exact positions and spans are recorded for every candidate pair.

3. **Does prediction work for unseen variants?** Yes, in this qualified within-assay sense. All scored sequences and both edit endpoints are absent from fitting. The strictest test also withholds their entire composition group and excludes every training sequence within two Hamming/global-Levenshtein edits of any member of that group. The 2-mer signal persists, while the more complex pair model's magnitude prediction deteriorates. These are previously exposed research data, not pristine external validation.

4. **Does it work for unseen parents/contexts?** That is **not established**. There is one biological HBB reporter context. The 592 local anchors and 60 candidate composition groups are not independent biological parent contexts. The experiment can test held-out local sequence groups, but cannot supply a train/test split across biological contexts. This unavailable test is not represented as a numeric failure or passed by changing the meaning of parent.

5. **How much better than composition?** The historical pair-model **absolute-score** error reduction reproduces at **27.042870575%**, with the original interval **20.45%–34.02%**. Its original **edit-change** error reduction is a different quantity: **23.91% [14.33%, 33.70%]**. Under the strict purge, the pair model is worse than composition/no-change; the 2-mer control improves edit-change MSE by **10.19% [1.00%, 19.99%]**. These are descriptive composition-cluster intervals in one experiment.

6. **How much better than short k-mer models?** A unique pair-model advantage is not established. Historically, additive 1–3-mers match the pair model's absolute-score performance. Under purging, the pair model has **28.5% greater published edit-change MSE** than 1–3-mers, and the 2-mer control is better still for magnitude. All models were fixed before new scoring. More complexity is not required for the supported sequence-order claim.

7. **Can predictions choose among candidate edits?** They improve the average choice among the already-measured candidates. Under purging, published-score regret is **0.385 pair / 0.320 additive 1–3-mer / 0.353 2-mer**, versus **0.500 uniform choice**. The pair-model improvement over uniform is **0.115 [0.060, 0.172]**; the 1–3-mer improvement is **0.180 [0.120, 0.241]**. This does not establish pair superiority over the short-mer control. Magnitude prediction and ranking are distinct: a model can rank usefully while exaggerating effect sizes.

8. **How often is the selected direction wrong?** In the purged test, the pair model is wrong against the published-score change in **44.6%** of choices. The same selected candidate is wrong in both constituent replicates in **28.2% [24.2%, 32.4%]** of choices. Wrong-both rates are **26.7%** for additive 1–3-mers, **29.8%** for 2-mers and **37.7%** for uniform expected choice. Rates average directions/anchors within composition classes, then classes equally; they are not probabilities calibrated for a new biological sample.

9. **How many independent biological/context units support this?** **One shared reporter context**, with two admitted constituent replicate pairs. The scored dataset has 855 variants in 70 composition groups, and the choice task has 1,744 overlapping directed links among 592 anchors in 60 composition groups. Those mathematical groups are useful resampling clusters, not 60 independent biological experiments. Thousands of predictions do not increase the number of independent contexts.

10. **What cannot be claimed?** Arbitrary RNA localization prediction; general single-nucleotide effects; unseen biological parent/context transfer; independent experimental validation; a unique complex-model advantage; a new molecular mechanism; verified complete raw-to-publication provenance; or a completely novel result based solely on this analysis. The data were previously exposed, confidence intervals condition on fixed fits, and multiple model comparisons are descriptive. No post-hoc model tuning, cohort filtering or reliability threshold was used to manufacture a success.

The localization-related endpoint is mutant-minus-anchor **NRS(log2FC)** for the published analysis, with fixed raw-derived log2 NRS differences evaluated separately in the constituent replicates. It is not silently renamed absolute cellular localization. Full per-row reporter sequences/physical clone identities are not established; they remain missing.

The [complete results](srle_small_edit_prediction_results.md), [frozen protocol](srle_small_edit_prediction_protocol.md), [all candidate rankings](../../artifacts/small_edit_20260925/srle_candidate_selection.csv), and [centerpiece figure](../../artifacts/small_edit_20260925/srle_small_edit_prediction_figure.png) retain both the positive signal and the failed primary magnitude comparison. Historical frozen results remain unchanged. **82 scoped tests pass; all saved predictions replay exactly.**
'''
    save(REPORT/'srle_final_predictive_claim.md',claim.encode())
    print({'reports_written':2,'per_split_performance_rows':len(rows)})


if __name__=='__main__':run()
