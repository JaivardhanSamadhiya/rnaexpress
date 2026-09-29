from .common import *

def table(f):
    def fmt(v):return (f'{v:.5f}' if np.isfinite(v) else 'unavailable') if isinstance(v,(float,np.floating)) else str(v).replace('|',' / ')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(fmt(v) for v in row)+' |' for row in f.itertuples(index=False,name=None)])
def write(name,s):save(REP/name,(s.strip()+'\n').encode())

def run():
    frozen();gate=readj(OUT/'gate_verdict.json');v=readj(OUT/'verification_receipt.json');assert v['status']=='PASS';comp=pd.read_csv(ART/'model_comparison.csv');core=comp[comp.stage.eq('held_assay')];cal=pd.read_csv(ART/'calibration.csv');gains=pd.read_csv(OUT/'per_assay_gains.csv');conditional=readj(OUT/'conditional_policy_eligibility.json');raw=pd.read_csv(OUT/'matched_reproducibility_summary.csv');reliability=pd.read_csv(OUT/'reliability_gain_association.csv');verdict=pd.DataFrame([{k:z for k,z in r.items() if k!='checks'} for r in gate['models']]);base=pd.read_csv(OLD/'strongest_simple_envelope.csv');primary=core[core.model.isin(PRIMARY)]
    status='PASS for a separately frozen representation-combination experiment; no independent confirmation.' if gate['selected_model'] else 'NO-GO: no primary probabilistic supervision method passed the frozen decision gate.'
    caveat='All studies are exposed development data. Biological breadth is unequal: one SRLE reporter, two astrocyte genes, six Moffatt parent/gene groups, and 187 Mikl genes. Variant counts do not supply independent biological experiments. The prior cross-assay NO-GO is unchanged.'
    write('calibration_results.md',f'''# Calibration results

{caveat}

Pairwise calibration concerns empirical replicate support for one candidate exceeding another. It is not the probability that an edit improves over WT or succeeds in a future biological system. Expected per-replicate Brier and cross-entropy use unsmoothed empirical votes; exact numerical ties receive half a vote. Both pair orientations are scored, with hierarchical pair weights. ECE uses ten fixed equal-width bins. Aggregate-only calibration in Moffatt cannot substitute for missing replicated calibration.

## Whole-study primary calibration

{table(cal[cal.stage.eq('held_assay')&cal.model.isin(PRIMARY)][['model','dataset','endpoint','pairs','brier','log_loss','ece','sharpness']])}

## Frozen calibration claim check

{table(verdict[['model','primary_selection_eligible','calibration_claim_gate_passes']])}

As an analytic postfit reference, constant probability 0.5 has Brier 0.25 and log loss log(2)=0.693147 under these scoring definitions. Every primary method is worse than that reference in every replicate-covered held study. Improvements over H0 therefore do not establish informative probability transfer. See `calibration_reference.md`; this reference changes no frozen gate.

The claim requires >=0.005 macro Brier improvement and >=0.01 log-loss improvement across the three replicate-covered assays, no Brier harm >0.01, and macro ECE<=0.05. Improvements in probability scoring do not establish better candidate selection. All secondary model and fold-specific metrics are retained in `calibration.csv`; reliability-bin values and weights are in `reliability_bins.csv`.

## Conditional conservative selection and abstention

Status: **{conditional['status']}**. Eligible methods: **{', '.join(conditional['eligible_models']) or 'none'}**.

{table(pd.DataFrame(conditional['checks']))}

The held-parent criterion applies separately to astrocyte and Mikl; fold metrics are averaged by held component count, including fold-wise ECE. No threshold was relaxed after evaluation. {'The fixed maximin relative-preference policy was evaluated; see conditional_policy_decisions.csv.' if conditional['eligible_models'] else 'The conservative policy and abstention were NOT RUN because the frozen calibration requirements failed.'} Pairwise probabilities do not identify absolute-benefit probability. The historical source-only direction head was held fixed across matched supervision methods, so its calibration cannot improve by construction; observed correct/wrong recommendations can still change with candidate ranking.
''')
    write('cross_replicate_results.md',f'''# Measurement robustness and decision reproducibility

{caveat}

## Fit one replicate subset, evaluate the other

Alternating source slots define A/B, with both role directions retained. Models use only the training slots to construct labels and estimate noise. H0 in this diagnostic is hard training-replicate-mean preference; it is not the author aggregate that includes the evaluation subset. The same parents and sequences occur on both sides: these results test measurement robustness, not unseen biological contexts. SRLE and one Mikl orientation have only one training replicate, so P3 cannot identify within-pair variance and explicitly falls back to P2. Moffatt has no admitted paired contrasts and is ineligible.

{table(comp[comp.stage.eq('cross_replicate')][['model','dataset','regret','pairwise_accuracy','wrong_direction','avoidable_wrong']])}

The table averages both directions of replicate splitting at the parent/component level. Role-specific decisions and calibration remain in the complete CSVs.

## Same-target comparison with empirical cross-replicate decision reproducibility

{table(raw[raw.model.isin(PRIMARY)])}

Every comparison above uses the identical finite candidate subset and omitted raw replicate endpoint. Sequence models were fitted on other biological studies; the empirical reference selects using the other measured replicates of the test assay. This empirical reference is outcome-informed, not deployable, not a theoretical optimum and not independent confirmation. Its regret exactly reproduces the preceding failure audit. The fractional recovery uses a positive uniform-minus-replicate denominator and can be negative or exceed one. It never replaces primary aggregate-target regret, and is not computed by mixing raw-replicate and author-aggregate scales.
''')
    write('leave_one_assay_out_results.md',f'''# Whole-study probabilistic-supervision comparison

**{status}**

{caveat}

The protocol was committed at `1c1f387`, and the executable/data prefit freeze at `033c316`, before comparative fits. All original whole-study and held-parent train/test hashes were retained. H0 coefficients reproduced the historical interaction_3 fits; all 26,258 held-study scores and 10,872 selected decisions were checked against the original baseline. P1/P2/P3 retain the same 246 features, latent utility, regularization, pair samples and biological weighting. No held-study measurements enter targets, noise, fitting or scaling.

## Primary controlled comparison

{table(primary[['model','dataset','regret','wrong_direction','avoidable_wrong','pairwise_accuracy','spearman','correct_direction','best_recovery','top5_best_recovery','variant_weighted_regret']])}

## Strongest simple comparators preserved from the original grid

{table(base[['dataset','model','regret','wrong_direction','avoidable_wrong']])}

## All fixed secondary comparisons

{table(core[core.model.isin(SECONDARY)][['model','dataset','regret','wrong_direction','avoidable_wrong','pairwise_accuracy','spearman']])}

Hraw changes the estimator without soft supervision; P2_weighted isolates the declared reliability weighting; Partial deliberately removes uncertain training constraints and records its changed training cohort. H0_pairfree/P2_pairfree add the same 17 antisymmetric metadata wedges and use expected wins, while P3_hetero uses one source-trained measurement-noise head and probit probabilities. These are separately labeled secondary tests. They cannot rescue failure of the primary H0/P1/P2/P3 question, and no successful-looking secondary subgroup was promoted after results.

## Failure categories and ambiguity

{table(primary[['model','dataset','wrong_direction','avoidable_wrong','unavoidable_wrong','neutral_only_alternative_wrong','no_feasible_candidate','measurement_ambiguous_fraction','measurement_unavailable_fraction']])}

Overall wrong direction equals avoidable + all-candidates-wrong + neutral-only-alternative wrong direction. Measurement ambiguity is a separate overlapping diagnostic: no candidate has replicate posterior superiority >=0.9 against every alternative with >=2 common replicates. It never erases a measured error. Missing replicate support is UNAVAILABLE, not proof of ambiguity or reliability. A no-feasible-candidate set may contain neutral edits and is therefore not always an all-wrong set.

## Was the gain greater in noisier assays?

{table(reliability)}

This prespecified association has only three assays. It cannot prove a noise mechanism, supply a reliable population correlation, or select a model. Raw outcomes, complete probability predictions, candidate rankings and fold-wise calibration are preserved.
''')
    failed=pd.DataFrame([{'model':m['model'],'primary':m['primary_selection_eligible'],'failed_checks':'; '.join(k for k,z in m['checks'].items() if not z) or 'none'} for m in gate['models']])
    write('generalization_gate_verdict.md',f'''# Frozen generalization gate: {gate['status']}

**{status}** Selected method: **{gate['selected_model'] or 'NONE'}**.

{table(verdict)}

## Every failed condition

{table(failed)}

## Per-assay gains and harms

{table(gains)}

The gate requires macro regret <=0.468, improvement over the strongest simple envelope, distributed improvement over H0, specific Mikl/SRLE harm limits, bounded avoidable-wrong risk, nonconcentrated gains, and the fixed descriptive component-bootstrap check. No threshold was changed. The user reference 0.488 was used literally; historical H0 is approximately 0.488228. Four studies, one-component SRLE and already-exposed development constrain all uncertainty interpretations.

Only primary P1/P2/P3 methods are eligible for selection. Secondary checks are displayed but do not change the primary verdict. Prior cross-assay gate: **NO-GO, unchanged**. New independent-dataset discovery: **not allowed in this experiment**. A primary pass would authorize only a separately committed representation-combination experiment, which itself must succeed before considering another independent test.
''')
    macro_primary=primary.groupby('model')[['regret','avoidable_wrong','wrong_direction']].mean().reset_index();best=macro_primary[macro_primary.model.ne('H0')].sort_values(['regret','model']).iloc[0]
    interpretation=('Accounting for experimental preference uncertainty materially improved the prespecified cross-assay decision criteria on these exposed benchmarks. This is not independent biological generalization.' if gate['selected_model'] else 'The tested probabilistic targets did not remedy the universal-model failure sufficiently to pass the frozen gate. Hard labeling alone is therefore not a supported main explanation for that failure in this controlled experiment. This does not prove that label uncertainty has no role or rule out every possible uncertainty model.')
    claims=[{'claim':'Historical strict within-SRLE prediction','status':'PRESERVED_SUPPORTED','scope':'one reporter; Level 1'}, {'claim':'Historical cross-assay generation','status':'NO-GO_UNCHANGED','scope':'frozen old result'}, {'claim':'Probabilistic supervision improves required transfer','status':gate['status'],'scope':'exposed development; primary methods only'}, {'claim':'Selected supervision for separate representation combination','status':gate['selected_model'] or 'NONE','scope':'no automatic external validation'}, {'claim':'Pairwise calibration','status':'SEE_PER_METHOD_FROZEN_CHECK','scope':'empirical replicate preferences; not absolute benefit'}, {'claim':'Conditional conservative policy','status':conditional['status'],'scope':'relative preference only'}, {'claim':'Untouched validation','status':'NOT_RUN','scope':'no new independent resource opened'}];csvsave(ART/'evidence_ledger.csv',pd.DataFrame(claims))
    write('final_status.md',f'''# Probabilistic ranking: final status

**{status}** The generalizable RNA-localization edit predictor goal remains unconfirmed by an untouched biological experiment. The old NO-GO remains intact.

{interpretation}

Soft supervision reduced some probability errors relative to H0, but every primary model remained worse than a constant 0.5 prediction on held-out replicate Brier score and log loss. No primary model passed the probability-calibration claim gate. This distinction is documented in `calibration_reference.md` and does not change model selection.

## Main decision results

{table(macro_primary)}

Lowest macro regret among primary soft methods: `{best['model']}` ({best['regret']:.6f}); this is a descriptive label, not a selected model unless it passes every gate condition. Selected method: **{gate['selected_model'] or 'none'}**. Per-assay benefits and harms remain in `leave_one_assay_out_results.md` and the gate report.

## What is complete

Reconstructed 127,603 replicate records with explicit missingness; preserved the original candidate/pair/feature/split structure; ran matched H0/P1/P2/P3, held-parent checks, alternating cross-replicate tests, whole-study evaluation, and every fixed secondary control. Pairwise calibration, exact candidate ranking, measurement ambiguity, all wrong-direction categories, and matched raw-target reproducibility comparisons are delivered. Conditional policy status: **{conditional['status']}**. No absolute-benefit calibration claim is made.

The nine figure topics are covered by seven PNG/SVG figures and a contact sheet. All eight requested reports and seven CSV artifacts are included, together with exact fitted coefficients, scalers, source-noise parameters, per-fold training targets, rankings, probabilities, role-specific diagnostics and checksums.

## Verification

{v['probability_rows_replayed']:,} pair probabilities replayed from saved coefficients (maximum error {v['max_probability_error']:.3g}); {v['selected_decisions_independently_checked']:,} selected decisions and {v['macro_regret_checks']} study/model macro regrets independently checked. Four fresh P1 fits reproduced coefficients (maximum error {v['fresh_fit_max_coefficient_error']:.3g}); nine scoped tests passed. Historical H0 scores and choices reproduced. All {v['prefit_files_unchanged']} prefit hashes, prior 319/28-member bundles, and {v['unrelated_modified_files_unchanged']} preexisting modified tracked files remain unchanged.

## Limits and stopping boundary

{caveat} Moffatt has no admitted paired replicate deltas, so all main supervision methods fall back to its aggregate labels. Source raw-versus-processed estimator differences remain; Hraw provides an explicit control. Shared WT contrasts, correlated replicate labels, few independent systems and limited parent diversity constrain probability interpretation. Calibration against measured replicate support does not prove future biological calibration.

{'Next: freeze a separate representation-combination experiment before any fitting; no independent dataset search yet.' if gate['selected_model'] else 'Stop this generation. Do not vary priors, smoothing constants, uncertainty formulas, windows or seeds to obtain a pass. No new representation combination or independent-dataset search was started.'} Remaining explanations include endpoint-specific biology, inadequate transferable sequence/context information, limited source diversity and systematic measurement/provenance differences. This experiment narrows the supervision hypothesis; it does not uniquely identify the biological cause or establish novelty.

No money, downloads, scheduled tasks, broad pytest, or protected outcomes were used. See `reproducibility.md` and the delivery receipt for artifact reconstruction and exact execution provenance.
''')
    write('reproducibility.md',f'''# Reproduction

Protocol commit `1c1f387`; executable prefit freeze `033c316`. The authoritative prefit manifest pins 26 files including executable model, evaluation and gate code, all candidate/replicate tables and the original 246-feature arrays. Later verification, reporting and plotting scripts do not fit/select models or alter thresholds.

Use bundled Python `C:/Users/jaisa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` from `D:/rnaexpress`, with PYTHONDONTWRITEBYTECODE=1, PYTHONIOENCODING=utf-8, OPENBLAS_NUM_THREADS=2, OMP_NUM_THREADS=2. Existing local scientific and plotting runtimes are used; nothing was installed or downloaded.

Execution order: prepare, scoped tests, freeze/commit, run (held-parent, cross-replicate, primary whole-study, secondary whole-study), gate, verify, report, figures, package. The completed runner refuses overwrite. Per-fold fit and target files are immutable and can be reused after interruption. Do not rerun preparation/freeze to replace existing evidence.

Git contains deterministic gzip copies of large CSVs. Decompress a missing CSV to its named location and verify the prefit/delivery hash; never regenerate frozen measurements from a different estimator. `candidate_index.csv` joins features to exact interventions; data.npz contains the original float32 features and admitted raw replicate matrix. Fitted mean/scale, coefficient, wedge/noise parameters and source-only variance pools reproduce predictions. Pair orientation is given by left/right candidate IDs. Reverse probability is exactly one minus forward probability. Candidate rankings use latent utility for BT and expected pairwise wins for the declared pairfree/probit variant.

All model evaluation outcomes are exposed development data. The diagnostic role of every table is documented in the protocol. Package contents include derived data, not original protected workbooks, and do not constitute a standalone dependency environment. Historical raw-to-author provenance limitations remain.

Only the namespaced test command `-u -m src.probabilistic_ranking_20260928.test_scoped` is appropriate; never run unfiltered pytest. Verification receipts record both numerical replay and old-file preservation. Any rerun producing timing-bearing logs needs a separate output namespace rather than overwriting a receipt.
''')
    print('Reports and evidence ledger generated:',gate['status'],flush=True)
if __name__=='__main__':run()
