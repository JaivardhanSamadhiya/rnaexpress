"""Prespecified descriptive diagnostics from saved frozen predictions."""
from .common import *
from .metrics import evaluate,aggregate
from scipy.stats import spearmanr

def run():
    frozen();f=pd.read_csv(OUT/'decision_metrics.csv');comp=pd.read_csv(ART/'model_comparison.csv');schema=readj(OUT/'feature_schema.json')['columns'];effects=pd.read_csv(OUT/'feature_effects.csv')
    rows=[];concord=[]
    for model in ('metadata','composition','delta2','kmer123','interaction_10'):
        e=effects[effects.model.eq(model)].pivot(index='feature_index',columns='dataset',values='coefficient')
        for i,row in e.iterrows():
            nonzero=row.abs()>1e-12;signs=np.sign(row[nonzero]);counts=signs.value_counts();agreement=counts.max()/len(signs) if len(signs) else np.nan
            rows.append({'model':model,'feature':schema[model][i],'mean_effect':row.mean(),'between_assay_sd':row.std(),'positive_studies':int((row>1e-12).sum()),'negative_studies':int((row<-1e-12).sum()),'nonzero_studies':int(nonzero.sum()),'majority_sign_fraction':agreement,'sign_reverses':bool((row>1e-12).any() and (row<-1e-12).any()),**row.to_dict()})
        for a,b in itertools.combinations(e.columns,2):
            keep=(e[a].abs()>1e-12)&(e[b].abs()>1e-12)
            concord.append({'model':model,'study_a':a,'study_b':b,'features_both_nonzero':int(keep.sum()),'sign_concordance':float((np.sign(e.loc[keep,a])==np.sign(e.loc[keep,b])).mean()),'coefficient_rank_concordance':float(spearmanr(e[a],e[b]).statistic),'interpretation':'descriptive independently fitted exposed studies; coefficients are confounded/regularized, not mechanisms'})
    csvsave(OUT/'feature_heterogeneity.csv',pd.DataFrame(rows));csvsave(OUT/'coefficient_concordance.csv',pd.DataFrame(concord))
    residual=[]
    for (stage,study),g in comp[comp.model.isin(['hierarchical','hierarchical_universal_only'])].groupby(['stage','dataset']):
        if g.model.nunique()==2:
            s=g.set_index('model');a=s.loc['hierarchical'];b=s.loc['hierarchical_universal_only'];residual.append({'stage':stage,'dataset':study,'full_score_regret':a.regret,'universal_only_regret':b.regret,'residual_regret_gain':b.regret-a.regret,'fraction_universal_regret_removed':(b.regret-a.regret)/b.regret if b.regret else np.nan,'interpretation':'predictive contribution on exposed within-assay/held-parent data, not variance or causal attribution'})
    csvsave(OUT/'universal_residual_contribution.csv',pd.DataFrame(residual))
    calibration=[]
    for (stage,model,study),g in f[f.stage.eq('held_assay')&~f.model.eq('uniform')].groupby(['stage','model','dataset']):
        g=g.copy();g['brier']=(g.candidate_set_feasibility_probability-g.feasible)**2;u=g.groupby('biological_component')[['brier','feasible']].mean()
        calibration.append({'model':model,'dataset':study,'feasibility_brier':u.brier.mean(),'always_feasible_brier':(1-u.feasible).mean(),'feasible_fraction':u.feasible.mean(),'warning':'candidate-set probabilities are not externally calibrated'})
    csvsave(OUT/'feasibility_diagnostics.csv',pd.DataFrame(calibration))
    # Fixed edit-size/locality sensitivities; existing predictions only, no refitting.
    pred=pd.read_csv(ART/'leave_one_assay_out_predictions.csv');canon=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False).set_index('intervention_id');subrows=[]
    for (study,model),p in pred.groupby(['dataset','model']):
        g=canon.loc[p.intervention_id].reset_index();g['score']=p.final_score.to_numpy();g['prob']=p.direction_probability.to_numpy()
        filters={'1':g.substitution_count.eq(1),'2-3':g.substitution_count.between(2,3),'4-6':g.substitution_count.between(4,6),'span_le6':g.physical_edit_span.le(6)}
        for label,mask in filters.items():
            sub=g[mask].copy();sizes=sub.groupby('parent_context_id').measured_delta.transform('size');spread=sub.groupby('parent_context_id').measured_delta.transform(lambda x:x.max()-x.min());sub=sub[sizes.ge(2)&spread.gt(1e-12)].reset_index(drop=True)
            if len(sub):
                r,_=evaluate(sub,sub.score.to_numpy(),sub.prob.to_numpy(),{},'sensitivity_'+label,model,study);subrows.extend(r)
                if model=='composition':
                    r,_=evaluate(sub,np.zeros(len(sub)),np.full(len(sub),.5),{},'sensitivity_'+label,'uniform',study);subrows.extend(r)
    sr=pd.DataFrame(subrows);csvsave(OUT/'size_locality_metrics.csv',aggregate(sr));save(OUT/'size_locality_decisions.csv.gz',__import__('gzip').compress(sr.to_csv(index=False,lineterminator='\n').encode(),mtime=0))
    # Failure accounting includes neutral-only alternatives as a third explicit category.
    failure=f.groupby(['stage','model','dataset','biological_component'])[['wrong_direction','unavoidable_wrong','avoidable_wrong','neutral_only_alternative_wrong']].mean().groupby(['stage','model','dataset']).mean().reset_index()
    assert np.allclose(failure.wrong_direction,failure.unavoidable_wrong+failure.avoidable_wrong+failure.neutral_only_alternative_wrong,atol=1e-12)
    csvsave(OUT/'failure_decomposition.csv',failure)
    source_metrics=f.groupby(['stage','model','dataset','biological_component'])[['raw_regret','variant_sign_accuracy','candidate_set_feasibility_probability','feasible']].mean().groupby(['stage','model','dataset']).mean().reset_index()
    csvsave(OUT/'per_assay_secondary_metrics.csv',source_metrics)
    print('Feature, residual, feasibility, edit-size/locality and failure diagnostics complete.')
if __name__=='__main__':run()
