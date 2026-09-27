"""Report saved results; no model selection or new outcome access."""
from .common import *

def table(frame):
    def fmt(x):
        if isinstance(x,(float,np.floating)):return '' if not np.isfinite(x) else f'{x:.6f}'
        return str(x).replace('|',' / ')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+['| '+' | '.join(fmt(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)])
def write(name,text):save(REPORT/name,(text.strip()+'\n').encode())

def run():
    assert_frozen();a=pd.read_csv(OUT/'test_a_metrics.csv');b=pd.read_csv(OUT/'test_b_metrics.csv')
    ap=pd.read_csv(OUT/'test_a_parent_metrics.csv');bp=pd.read_csv(OUT/'test_b_parent_metrics.csv')
    ac=pd.read_csv(OUT/'test_a_contrasts.csv');bc=pd.read_csv(OUT/'test_b_contrasts.csv')
    ad=pd.read_csv(OUT/'test_a_decision_metrics.csv');bd=pd.read_csv(OUT/'test_b_decision_metrics.csv')
    da=pd.read_csv(OUT/'test_a_decisions.csv');db=pd.read_csv(OUT/'test_b_decisions.csv')
    mapped=pd.read_csv(ART/'GSE330741_mapped_outcomes.csv');eligible=mapped[mapped.qc_status.eq('VERIFIED')]
    context='All external results use 3,984 verified SNPs, seven 190-nt parents, five nonoverlap components and two genes (Slc1a2 and Sparc). The author-retained design has 14 matched biological replicate labels (three-cortex pools), with 11–14 positive matched pairs per admitted variant. Technical sequencing lanes are not biological replicates. Intervals below are descriptive 95% component-bootstrap intervals, not evidence of thousands of independent biological contexts. Historical exposure is PARTIALLY EXPOSED.'
    lineage='Protocols, implementation and source-only predictions were frozen in `0b100d3`; access marker `5ae6d4a` preceded reveal. Once-run A outcomes were preserved at `1ff9bc2` before conditional B. The UTC/local-time typographical error in the marker is disclosed in `execution_notes.md`; the timestamped JSON and git ancestry establish the order.'
    aa=ap[ap.model.isin(['srle_2mer_full','srle_composition'])].pivot(index='parent_id',columns='model',values='spearman').reset_index()
    write('GSE330741_zero_shot_results.md',f'''# GSE330741 zero-shot result: criterion failed

The frozen SRLE predictor did **not** establish zero-shot biological transfer. Its mean parent Spearman is **0.050952 [−0.003111, 0.138983]**. The composition baseline is 0.067368; the paired primary-minus-composition advantage is **−0.016416 [−0.041437, 0.027042]**, exact one-sided block sign-flip p=0.78125. No sign reversal, recalibration, model replacement or outcome filtering followed this result.

{context}

{lineage}

## All frozen quantitative models

{table(a[['model','spearman','spearman_ci_low','spearman_ci_high','mse','mae','strict_sign_accuracy']])}

The frozen source composition and substitution models induce identical within-parent rank ordering here, despite differing predicted magnitudes. Their matching correlations do not provide two independent biological corroborations. `no_change` has undefined mathematical correlation; the prespecified operational no-ranking score is 0. All k-mer controls are secondary; their somewhat higher average correlations cannot replace the primary.

## Every parent

{table(aa)}

The primary is positive for four parents and negative for three. Short k-mer representation alone does not explain a general cross-assay effect: the isolated 2-mer component has mean rho 0.010476. Composition accounts for at least as much of the observed rank signal as the full frozen primary.

## Candidate choice and interpretation

The primary candidate regret is **0.446733 [0.403957, 0.488083]**, versus uniform 0.500000. Paired improvement is 0.053267 [0.011917, 0.096043], with six of seven parents improving after averaging both requested directions. Wrong-direction selection remains 7/14 (50%); the composition baseline has 6/14 (42.9%). Neither the selected candidate nor the top-five shortlist recovered the measured best edit for this primary in any of the 14 decisions. These are positive secondary regret results with important practical limits, and they do not override failed primary/baseline gates.

SRLE measures nuclear retention in a human reporter; this target measures mutant-minus-WT synaptoneurosome/cortex enrichment in mouse astrocytes. Sequence length, mutation class, parent background and measurement normalization also differ. Those differences are plausible explanations for weak transfer, not causes identified by this analysis. No claim of molecular mechanism follows.

## Mapping and endpoint provenance

All 3,984 eligible variants map exactly to one SNP and their matched 190-nt WT. The predeclared 569 poor-cloning-group variants are retained as exclusions; no new QC exclusions occurred. The primary uses published normalized `snin_ctxin_logFC(mutant) − snin_ctxin_logFC(WT)`. Reconstructed paired log2(CPM+1) contrasts correlate with the primary at 0.891–0.996 across parents, with mean absolute discrepancies 0.013–0.067. This is corroboration, not exact author REML reproduction; full raw-count-to-coefficient reconstruction remains uncertified.

Full predictions/features/QC: `artifacts/generalization_20260926/GSE330741_zero_shot_predictions.csv`. All per-parent metrics, baseline contrasts and uncertainty are in `results/generalization_20260926/test_a_*.csv`. Outcome source: [official study supplement](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142395/); assay metadata: [GEO GSE330741](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE330741).
''')
    bb=bp[bp.model.isin(['simple_full','simple_full_delta2','position'])].pivot(index='parent_id',columns='model',values='spearman').reset_index()
    bb['2mer_increment']=bb.simple_full_delta2-bb.simple_full
    gene=pd.read_csv(OUT/'leave_gene_out_parent_metrics.csv');gs=gene.groupby(['held_gene','model'],as_index=False)[['spearman','mse']].mean()
    write('GSE330741_leave_parent_out_results.md',f'''# Held-parent method replication: partial signal, criterion failed

The primary model predicts held-parent SNP ranks weakly positively, but **the frozen test does not establish incremental sequence-order generalization**. Mean parent rho is **0.102266 [0.043663, 0.177122]** versus simple baseline 0.089149. The paired increment is **0.013118 [−0.022045, 0.067958]**, exact one-sided block sign-flip p=0.3125. Four of seven parents improve. Position alone reaches 0.092991; the primary's increment over position is also uncertain.

{context}

B is target-assay training with independent held-parent prediction, not zero-shot validation. Its entire model family, selection rule and candidate policy were fixed before A outcomes. Every outer fold excludes the held parent plus any overlapping same-gene parent. All alpha selection, scaling, response means and nuisance effects use only remaining training parents. No random SNP split was used.

## Every model and parent

{table(b[['model','spearman','spearman_ci_low','spearman_ci_high','mse','mae','strict_sign_accuracy']])}

{table(bb)}

The primary uses substitution, composition, position and Δ2-mer features; `simple_full` uses the same controls without Δ2-mer. Parent nuisance indicators are centered using training rows; unknown parents have zero indicators. Training parents have equal total weight. Ridge alpha [1,10,100] is selected by mean inner parent MSE with overlap exclusion. Coefficients, scaler parameters, alpha decisions and fold membership are retained in `test_b_fits.json`, `test_b_inner_selection.csv` and `test_b_fold_assignments.json`.

The strong-success checks for positive primary rho and candidate regret passed. The primary rank-advantage check failed. More complex 3-mer/combined controls did not provide a basis to override this failure. Model ranking after reveal is descriptive, never a new winner selection.

## Prespecified two-gene sensitivity

{table(gs)}

These fixed-alpha10 predictions train on the other gene only. Both gene-level average primary correlations are positive, but there are only two gene folds and they do not supply a reliable population interval or rescue the primary test. Full per-parent results remain in `leave_gene_out_parent_metrics.csv`.

Candidate selection is more promising than whole-list ranking: primary regret 0.371947 versus simple baseline 0.488527 and uniform 0.500000. This is separately reported with the small number of decisions and uncertainty limitations. Full predictions: `artifacts/generalization_20260926/GSE330741_leave_parent_out_predictions.csv`.
''')
    decision_summary=pd.concat([ad,bd],ignore_index=True)
    primary_decisions=pd.concat([da[da.model.eq('srle_2mer_full')],db[db.model.eq('simple_full_delta2')]],ignore_index=True)
    csvsave(OUT/'primary_selected_candidates.csv',primary_decisions)
    allr=pd.concat([pd.read_csv(ART/'test_a_candidate_rankings.csv'),pd.read_csv(ART/'test_b_candidate_rankings.csv')],ignore_index=True)
    csvsave(ART/'GSE330741_candidate_rankings.csv',allr)
    truth=[]
    for parent,g in eligible.groupby('parent_id'):
        truth.append({'parent_id':parent,'min_effect':g.observed_delta.min(),'max_effect':g.observed_delta.max(),'positive_fraction':(g.observed_delta>TOL).mean(),'negative_fraction':(g.observed_delta<-TOL).mean(),'diagnostic_scope':'descriptive candidate feasibility after reveal; never used for eligibility'})
    truth=pd.DataFrame(truth);csvsave(OUT/'candidate_direction_feasibility.csv',truth)
    write('GSE330741_candidate_selection_results.md',f'''# Candidate-edit selection: promising secondary result

The frozen held-parent primary chose lower-regret edits than uniform choice for **all seven parents**, averaging both directions. Regret was **0.371947 [0.316664, 0.413107]**, versus simple baseline 0.488527 and uniform 0.500000. Wrong-direction selections fell from 8/14 for the simple baseline to **5/14** for the primary (uniform expectation 7/14). This is a predeclared secondary result; the failed rank-advantage primary criterion remains failed.

{context}

Every QC-eligible SNP is ranked for each held parent. The 14 decisions per model are seven parents × two directions, not 14 independent biological experiments. Five nonoverlap components determine uncertainty. Predictions are formed without that parent's measurements in fitting or selection; no outcome-selected candidate subset or abstention is used. Ties use lexical element ID.

## All baselines and sequence models

{table(decision_summary[['stage','model','regret','regret_ci_low','regret_ci_high','wrong_direction','best_recovery','top5_best_recovery']])}

Uniform expectations are exact, not a lucky random seed. Averaging symmetric increase/decrease tasks makes uniform normalized regret exactly 0.5 and uniform wrong direction 0.5 when no candidate is zero. These values are not a universal single-direction biological baseline.

For B, paired regret gain versus uniform is 0.128053 [0.086893, 0.183336], exact block p=0.03125. Gain versus simple_full is 0.116581 [0.047518, 0.193414], but exact block p=0.0625. The positive bootstrap interval and non-significant exact comparison differ because only five blocks exist; report both. The prespecified candidate gate did not require this latter p-value, but that choice cannot justify a stronger confirmatory claim. Five of seven parents beat simple_full. The primary recovered no exact measured best edit, including within top-five shortlists (0/14 for both).

## Every frozen primary choice, including failures

{table(primary_decisions[['stage','parent_id','direction','selected','predicted_delta','observed_delta','regret','wrong_direction']])}

Direction +1 seeks increased SN/cortex enrichment; −1 seeks decreased enrichment. Wrong direction concerns the sign of the selected author's mutant-minus-WT effect. It is **not** the SRLE metric “wrong in both constituent replicates,” and those rates must not be equated. Replicate contrast columns are retained for transparent inspection, not used to choose candidates after reveal.

## Observed candidate feasibility (descriptive only)

{table(truth[['parent_id','min_effect','max_effect','positive_fraction','negative_fraction']])}

The candidate effects are mostly positive relative to WT, so predicting positive signs can yield high variant sign accuracy without strong ranking or a reliable decrease recommendation. Shared WT measurement error can shift all effects for a parent. This explains why high sign accuracy and lower regret cannot substitute for comparison against the fixed simple controls. No outcome-centering or new abstention rule was introduced.

`GSE330741_candidate_rankings.csv` contains all {len(allr):,} parent/model/direction/candidate rows for A and B. The unchanged prefit A predictions and held-parent B predictions are separately preserved. The result supports a bounded candidate-ranking signal in this exposed, small-parent setting; it does not establish a generally reliable RNA-edit design tool.
''')
    agreement=pd.read_csv(OUT/'cross_assay_coefficient_agreement.csv');mean=agreement[agreement.held_parent.eq('mean_outer_coefficients')]
    ledger=[
      {'claim':'Strict SRLE within-assay small-edit prediction','level':1,'status':'SUPPORTED_FROZEN','estimate':.10192902960964512,'ci_low':.010011286575468549,'ci_high':.19993585473201866,'unit':'composition classes; one HBB reporter','evidence':'reports/small_edit_20260925/small_edit_final_synthesis.md','limitation':'not cross-assay biological validation'},
      {'claim':'Zero-shot exact parameter transfer','level':3,'status':'FROZEN_CRITERION_FAILED','estimate':.0509517690598591,'ci_low':-.003111489927903363,'ci_high':.13898328115162234,'unit':'7 parents / 5 components / 2 genes','evidence':'results/generalization_20260926/test_a_verdict.json','limitation':'composition baseline higher; partial historical exposure'},
      {'claim':'Held-parent incremental 2mer representation replication','level':2,'status':'FROZEN_CRITERION_FAILED','estimate':.013117806820935298,'ci_low':-.022045457775887754,'ci_high':.06795832421444009,'unit':'7 parents / 5 components / 2 genes','evidence':'results/generalization_20260926/test_b_contrasts.csv','limitation':'position/simple controls explain most rank signal'},
      {'claim':'Held-parent candidate regret improvement versus uniform','level':2,'status':'POSITIVE_PRESPECIFIED_SECONDARY','estimate':.12805305734166256,'ci_low':.08689264971448028,'ci_high':.18333635523066572,'unit':'7 parents / 14 directional decisions / 5 components','evidence':'results/generalization_20260926/test_b_decision_metrics.csv','limitation':'does not override primary failure; 5/14 wrong direction'},
      {'claim':'Shared molecular mechanism','level':0,'status':'NOT_ESTABLISHED','estimate':np.nan,'ci_low':np.nan,'ci_high':np.nan,'unit':'different biological endpoints','evidence':'results/generalization_20260926/cross_assay_coefficient_agreement.csv','limitation':'predictive feature agreement is not causal mechanism'},
      {'claim':'Third untouched GSE334718 system','level':4,'status':'INELIGIBLE_EXPOSED','estimate':np.nan,'ci_low':np.nan,'ci_high':np.nan,'unit':'historically unsealed v4 development data','evidence':'reports/generalization_20260926/GSE334718_admission.md','limitation':'cannot regain untouched status'}]
    csvsave(ART/'generalization_evidence_ledger.csv',pd.DataFrame(ledger))
    verify=readj(OUT/'verification_receipt.json')
    write('generalization_final_synthesis.md',f'''# Generalization synthesis

**The strongest fully supported claim remains Level 1: strict within-SRLE small-edit prediction.** The newly frozen external study produced a useful candidate-regret signal, but neither zero-shot transfer nor the primary incremental sequence-order replication criterion passed. We should preserve the candidate result as positive secondary evidence and avoid upgrading the overall claim.

| Question | Result | Interpretation |
| --- | --- | --- |
| Existing SRLE result preserved? | 10.19% edit-effect MSE gain, descriptive interval 1.00–19.99%; regret 0.320 vs 0.500 | Yes, one reporter context; frozen result unchanged |
| Exact SRLE coefficients transfer? | Mean parent rho 0.051 [−0.003, 0.139]; composition baseline 0.067 | No strong zero-shot transfer demonstrated |
| Same order representation adds beyond simple controls? | B rho 0.102; paired increment 0.013 [−0.022, 0.068], exact p=0.3125 | Weak/heterogeneous incremental evidence; criterion failed |
| Held-parent candidate choice useful? | Regret 0.372 vs simple 0.489 and uniform 0.500; 5/14 wrong direction | Positive predeclared secondary signal; not a reliable general design tool |
| Third untouched dataset available here? | GSE334718 explicitly unsealed in August for development | No; independent-test branch stopped |

{context}

## What was completed

Verified original frozen SRLE bundles; audited official metadata and historical exposure; reconstructed the 190-nt SNV design and author endpoint; committed protocols, source coefficients and every source-only prediction before reveal; mapped all 3,984 eligible outcomes; ran A once; preserved its failed primary result; executed the previously fixed nested overlap-purged B study; ranked every candidate in both directions; performed the fixed two-gene and coefficient checks; audited GSE334718 without reopening its outcomes; independently replayed predictions and metrics; produced reproducible reports, figures and the evidence ledger.

{lineage}

All 37 prefit hashes remain unchanged. Fresh reconstruction of **84 outer model fits exactly reproduced their predictions** (maximum numerical error {verify['max_prediction_replay_error']:.1f}); 4,553 source-only predictions, 154 parent/model metrics, 308 selected-candidate decisions and two primary uncertainty calculations were checked independently. Twelve scoped tests passed. Original bundles with 119, 70 and 41 manifest members and their ZIP hashes are unchanged. No spending, new scheduled task, protected dataset opening, broad model search or unfiltered pytest occurred.

## Why each generalization approach fell short

**A, direct source parameter transfer:** the primary had a small uncertain rank correlation and underperformed composition/substitution ranking. Its 2-mer-only component was weaker still. The difference in compartment endpoint, species/cell type, parent length, and substitution versus composition-preserving exchange could explain the mismatch, but the experiment does not isolate these explanations. Candidate regret improved but wrong-direction frequency did not.

**B, local representation replication:** fitting in astrocytes produced positive held-parent ranks and useful extreme-candidate ordering, yet simple position/substitution controls captured most whole-list rank signal. Adding 2-mers helped four parents and hurt three; the paired increment is uncertain. The stronger candidate result is concentrated at the ranked extremes and does not prove a robust improvement throughout the candidate list. Its exact simple-baseline regret p=0.0625 also reflects the tiny block count. The isolated Δ2-mer model's regret was 0.510, so adjacency alone was not a successful candidate recommender.

**More complex frozen controls:** 3-mer and 1–3-mer variants did not supply a coherent strong-transfer result, and were not promoted after reveal. This study does not justify more architecture/hyperparameter search against these same outcomes.

**GSE334718 as untouched third system:** historical outcome-driven development disqualifies it. Its exact-SNP breadth is also sparse. Relabeling exposed data would not add independent evidence.

## Representation, parameters and mechanism are different claims

{table(mean[['gauge','pearson','cosine','sign_concordance','permutation_p_positive']])}

The mean held-parent isolated-2mer coefficient vector is negatively correlated with SRLE after grand-mean removal (r=−0.471). Removing row/column additive composition terms yields positive interaction concordance (r=0.457), but the fixed descriptive feature-label permutation p=0.0913 is uncertain. Correlated features, overlapping training fits and only two genes make these conditional coefficient diagnostics, not independent mechanism tests. Neither flipping the transferred sign nor extracting a favorable coefficient subset is permitted. Exact parameter transfer is not established; representation reuse shows partial evidence; a shared molecular mechanism is not demonstrated.

## Claim hierarchy

1. **Level 1 — supported:** strict within-SRLE small-edit prediction, with the original composition/similarity controls and limitations.
2. **Level 2 — incomplete:** independently collected astrocyte data show weak held-parent ranks and a positive candidate-regret secondary result, but the frozen primary incremental-order criterion failed. State this as partial evidence, not completed method validation.
3. **Level 3 — not established:** exact source coefficients did not pass the frozen zero-shot test.
4. **Level 4 — not established:** no independent three-system candidate-edit validation exists.

## What remains missing and the next three tasks

1. Finish a reproducible paper/presentation around the existing SRLE result, the protected external test, its limits, and the positive secondary candidate result. Keep the failed primary results prominent; neither novelty nor competition success is established by a score.
2. Resolve measurement provenance before stronger direction claims: exact raw-count/author-REML reproduction, WT measurement uncertainty, complete sample pedigree and transcript versions. A separate diagnostic protocol may address these, but must preserve the present endpoint and verdicts. The paired-CPM corroboration here is not full pipeline certification.
3. Seek a genuinely new, unexposed computational validation resource with more independent parent genes and measured small-edit alternatives, only under a distinct admission/prefit protocol. More searches or fits on these already opened datasets cannot convert the failed test into independent confirmation. This task deliberately stopped at its prescribed boundary.

## Do not touch and confidence gaps

Do not alter the SRLE source fits/results/bundles; the 37-file GSE330741 prefit manifest; A/B outcomes, predictions, metrics or failures; the exposure classifications; historical failed RNAddress gates; N-zip/TDP EV5 and other reserved data; or unrelated user modifications. Do not flip A signs, select another primary after reveal, discard weak parents, retune candidate rules, spend money or create scheduled tasks.

Confidence is high in exact sequence mapping, preservation and numerical replay. It is limited by historical partial exposure (the three original printed rows are unidentified), five nonoverlap components nested within two genes, partially shared samples/WT references, endpoint mismatch, lack of full author-pipeline replay, and no wet-lab validation. Bootstrap/sign-flip assumptions across components remain approximate because common genes and experimental pools create additional dependence. Public availability and primary-source provenance do not by themselves prove biological validity or novelty.

## Deliverables

The eight requested reports are in `reports/generalization_20260926/`. Predictions, all candidate ranks and `generalization_evidence_ledger.csv` are in `artifacts/generalization_20260926/`. Protocol/configuration, complete baseline/parent tables, fitted parameters, provenance and verification receipts are in `results/generalization_20260926/`. `src/generalization_20260926/figures.py` renders the figures from saved results; `verify.py` replays the frozen outputs without scientific model selection. See `reproducibility.md` for safe reproduction and the archive receipt for hashes.
''')
    print('Required result reports, candidate rankings and evidence ledger generated.')

if __name__=='__main__':run()
