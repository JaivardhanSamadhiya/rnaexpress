from .common import *
from scipy.stats import spearmanr,kendalltau
from math import comb

def pair_accuracy(y,p):
    n=len(y);total=n*(n-1)/2
    ty=sum(v*(v-1)/2 for v in pd.Series(y).value_counts());tp=sum(v*(v-1)/2 for v in pd.Series(p).value_counts())
    if total==ty:return np.nan
    if total==tp:return .5
    tau=kendalltau(y,p).statistic
    return .5+.5*tau*np.sqrt((total-ty)*(total-tp))/(total-ty)

def evaluate(frame,score,prob,feasible,stage,model,held):
    rows=[];ranking=[]
    for context,g in frame.groupby('parent_context_id',sort=True):
        g=g.sort_values('intervention_id');ix=g.index.to_numpy();y=g.measured_delta.to_numpy();p=score[ix];n=len(g);assert n>=2 and np.ptp(y)>0
        pair=pair_accuracy(y,p);rho=0 if np.ptp(p)<=1e-12 else float(spearmanr(y,p).statistic)
        for direction in (-1,1):
            truth=direction*y;pred=direction*p;order=np.argsort(-pred,kind='stable');j=order[0];pr=np.empty(n,int);pr[order]=np.arange(1,n+1)
            regret=(truth.max()-truth)/np.ptp(truth);valid=truth>1e-12;wrong=truth<-1e-12;best=truth==truth.max();k=min(5,n)
            feasible_truth=bool(valid.any());confidence=float(prob[ix[j]] if direction==1 else 1-prob[ix[j]])
            fp=float(feasible.get((context,direction),np.nan));abstain_conf=min(confidence,fp) if np.isfinite(fp) else confidence
            row={'stage':stage,'model':model,'held':held,'dataset':g.dataset.iloc[0],'endpoint_class':g.endpoint_class.iloc[0],'biological_component':g.biological_component.iloc[0],'gene_transcript':g.gene_transcript.iloc[0],'parent_context_id':context,'direction':direction,'candidates':n,'selected_id':g.intervention_id.iloc[j],'selected_edit_size':g.substitution_count.iloc[j],'regret':float(regret[j]),'raw_regret':float(truth.max()-truth[j]),'wrong_direction':float(wrong[j]),'correct_direction':float(valid[j]),'feasible':float(feasible_truth),'no_feasible_candidate':float(not feasible_truth),'unavoidable_wrong':float(wrong[j] and not feasible_truth),'avoidable_wrong':float(wrong[j] and feasible_truth),'best_recovery':float(best[j]),'top5_best_recovery':float(best[order[:k]].any()),'pairwise_accuracy':pair,'spearman':rho,'variant_sign_accuracy':float(np.mean((prob[ix]>=.5)==(y>0))),'selected_direction_probability':confidence,'candidate_set_feasibility_probability':fp,'abstention_confidence':abstain_conf,'fixed_abstention_accept':bool(abstain_conf>=.8),'ranking_margin':float(pred[order[0]]-pred[order[1]]),'observed_effect':float(y[j]),'predicted_score':float(p[j])}
            row['unavoidable_wrong']=float(wrong[j] and wrong.all())
            row['neutral_only_alternative_wrong']=float(wrong[j] and not feasible_truth and not wrong.all())
            if model=='uniform':
                row.update(selected_id='exact_expectation',selected_edit_size=float(g.substitution_count.mean()),regret=float(regret.mean()),raw_regret=float((truth.max()-truth).mean()),wrong_direction=float(wrong.mean()),correct_direction=float(valid.mean()),unavoidable_wrong=float(wrong.mean() if not feasible_truth else 0),avoidable_wrong=float(wrong.mean() if feasible_truth else 0),best_recovery=float(best.mean()),top5_best_recovery=float(1-comb(n-int(best.sum()),k)/comb(n,k)) if n-int(best.sum())>=k else 1.,selected_direction_probability=np.nan,fixed_abstention_accept=False)
                row['unavoidable_wrong']=float(wrong.mean() if wrong.all() else 0.)
                row['neutral_only_alternative_wrong']=float(wrong.mean() if not feasible_truth and not wrong.all() else 0.)
            rows.append(row)
            if stage in ('held_assay','secondary_sirloin','held_domain','family_transfer','pretrained_restricted'):
                ranking.extend({'stage':stage,'model':model,'held':held,'intervention_id':g.intervention_id.iloc[t],'parent_context_id':context,'dataset':g.dataset.iloc[0],'direction':direction,'rank':int(pr[t]),'score':float(pred[t]),'measured_delta':float(y[t]),'regret':float(regret[t]),'selected':bool(t==j)} for t in range(n))
    return rows,ranking

FIELDS=['regret','wrong_direction','avoidable_wrong','unavoidable_wrong','correct_direction','best_recovery','top5_best_recovery','pairwise_accuracy','spearman','variant_sign_accuracy','no_feasible_candidate']
def aggregate(decisions):
    rows=[]
    for (stage,model,dataset),g in decisions.groupby(['stage','model','dataset']):
        unit=g.groupby('biological_component')[FIELDS].mean();w=g.candidates.to_numpy()
        rows.append({'stage':stage,'model':model,'dataset':dataset,'components':len(unit),'decision_sets':g.parent_context_id.nunique(),'decisions':len(g),**{f:float(unit[f].mean()) for f in FIELDS},'variant_weighted_regret':float(np.average(g.regret,weights=w)),'variant_weighted_pairwise_accuracy':float(np.average(g.pairwise_accuracy,weights=w))})
    return pd.DataFrame(rows)
