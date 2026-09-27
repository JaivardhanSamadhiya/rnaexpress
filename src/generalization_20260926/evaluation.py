"""Prefit-locked metrics and parent/overlap-aware uncertainty."""
from .common import *
from scipy.stats import spearmanr,rankdata
from functools import lru_cache
from math import comb

@lru_cache(None)
def bootstrap_indices(n):return np.random.default_rng(SEED).integers(0,n,(10000,n))

def cluster_stat(frame,value):
    t=frame.groupby('overlap_component')[value].agg(['sum','count']);ix=bootstrap_indices(len(t))
    if t['count'].sum()==0:return (np.nan,np.nan,np.nan)
    samples=t['sum'].to_numpy()[ix].sum(1)/t['count'].to_numpy()[ix].sum(1)
    return float(frame[value].mean()),*np.quantile(samples,[.025,.975]).tolist()

def signflip(frame,value):
    a=frame.groupby('overlap_component')[value].sum().to_numpy();obs=a.sum()/len(frame)
    signs=np.array(list(itertools.product([-1,1],repeat=len(a))));null=signs@a/len(frame)
    return float(np.mean(null>=obs-1e-12))

def correlations(y,p):
    assert np.ptp(y)>TOL,'Constant observed target: ranking branch stops'
    constant=np.ptp(p)<=TOL
    return (0. if constant else float(spearmanr(y,p).statistic),np.nan if constant else float(np.corrcoef(y,p)[0,1]),constant)

def evaluate(frame,predictions,stage,primary,baselines):
    models=list(predictions.columns);metrics=[];decisions=[];ranks=[]
    for parent,g in frame.groupby('parent_id'):
        g=g.sort_values('element');ix=g.index.to_numpy();y=g.observed_delta.to_numpy();n=len(g)
        assert np.ptp(y)>TOL and n>=100
        common={'stage':stage,'parent_id':parent,'gene':g.gene.iloc[0],'overlap_component':g.overlap_component.iloc[0],'snps':n}
        for model in models:
            p=predictions.loc[ix,model].to_numpy();rho,r,const=correlations(y,p)
            metrics.append({**common,'model':model,'spearman':rho,'pearson':r,'constant_prediction':const,'mse':float(np.mean((p-y)**2)),'mae':float(np.mean(abs(p-y))),'strict_sign_accuracy':float(np.mean(sign(p[sign(y)!=0])==sign(y[sign(y)!=0]))),'observed_mean':y.mean(),'observed_sd':y.std()})
            for direction in (-1,1):
                truth=direction*y;score=direction*p;order=np.argsort(-score,kind='stable');chosen=int(order[0]);prank=np.empty(n,int);prank[order]=np.arange(1,n+1)
                m=int((truth==truth.max()).sum());regret=(truth.max()-truth)/np.ptp(truth);mr=rankdata(-truth,method='min')
                better=truth>TOL;worse=truth<-TOL
                d={**common,'model':model,'direction':direction,'selected':g.element.iloc[chosen],'predicted_delta':p[chosen],'observed_delta':y[chosen],'regret':regret[chosen],'correct_direction':float(better[chosen]),'wrong_direction':float(worse[chosen]),'best_recovery':float(mr[chosen]==1),'top5_best_recovery':float(np.any(mr[order[:5]]==1))}
                decisions.append(d)
                if model==models[0]:
                    decisions.append({**common,'model':'uniform','direction':direction,'selected':'exact_uniform_expectation','predicted_delta':np.nan,'observed_delta':y.mean(),'regret':regret.mean(),'correct_direction':better.mean(),'wrong_direction':worse.mean(),'best_recovery':m/n,'top5_best_recovery':1-comb(n-m,5)/comb(n,5) if n-m>=5 else 1.})
                for j,row in enumerate(g.itertuples()):ranks.append({**common,'model':model,'direction':direction,'element':row.element,'position':row.edit_position_1based,'reference_nt':row.reference_nt,'alternate_nt':row.alternate_nt,'predicted_delta':p[j],'observed_delta':y[j],'predicted_rank':int(prank[j]),'measured_rank':float(mr[j]),'selected':j==chosen,'regret':regret[j],'qc_status':row.qc_status})
    metrics=pd.DataFrame(metrics);decisions=pd.DataFrame(decisions);ranks=pd.DataFrame(ranks)
    csvsave(OUT/(stage+'_parent_metrics.csv'),metrics);csvsave(OUT/(stage+'_decisions.csv'),decisions)
    csvsave(ART/(stage+'_candidate_rankings.csv'),ranks)
    summary=[]
    for model,g in metrics.groupby('model'):
        row={'stage':stage,'model':model,'parents':len(g),'genes':g.gene.nunique(),'overlap_components':g.overlap_component.nunique(),'snps':g.snps.sum()}
        for metric in ('spearman','pearson','mse','mae','strict_sign_accuracy'):
            v,lo,hi=cluster_stat(g,metric);row.update({metric:v,metric+'_ci_low':lo,metric+'_ci_high':hi})
        summary.append(row)
    summary=pd.DataFrame(summary);csvsave(OUT/(stage+'_metrics.csv'),summary)
    choice=decisions.groupby(['model','parent_id','gene','overlap_component'],as_index=False)[['regret','correct_direction','wrong_direction','best_recovery','top5_best_recovery']].mean()
    ds=[]
    for model,g in choice.groupby('model'):
        row={'stage':stage,'model':model,'parents':len(g),'genes':g.gene.nunique(),'overlap_components':g.overlap_component.nunique()}
        for metric in ('regret','correct_direction','wrong_direction','best_recovery','top5_best_recovery'):
            v,lo,hi=cluster_stat(g,metric);row.update({metric:v,metric+'_ci_low':lo,metric+'_ci_high':hi})
        ds.append(row)
    ds=pd.DataFrame(ds);csvsave(OUT/(stage+'_decision_metrics.csv'),ds)
    contrasts=[]
    mp=metrics[metrics.model.eq(primary)].set_index('parent_id');dp=choice[choice.model.eq(primary)].set_index('parent_id')
    for base in models:
        if base==primary:continue
        b=metrics[metrics.model.eq(base)].set_index('parent_id').loc[mp.index]
        for field in ('spearman','mse'):
            g=mp[['overlap_component']].copy();g['gain']=(mp[field]-b[field]) if field=='spearman' else (b[field]-mp[field])
            value,lo,hi=cluster_stat(g,'gain');contrasts.append({'stage':stage,'primary':primary,'baseline':base,'metric':field+'_gain','estimate':value,'ci_low':lo,'ci_high':hi,'one_sided_block_signflip_p':signflip(g,'gain'),'fraction_parents_improved':float((g.gain>TOL).mean())})
    for base in ['uniform']+[m for m in models if m!=primary]:
        b=choice[choice.model.eq(base)].set_index('parent_id').loc[dp.index]
        for field in ('regret','wrong_direction'):
            g=dp[['overlap_component']].copy();g['gain']=b[field]-dp[field]
            value,lo,hi=cluster_stat(g,'gain');contrasts.append({'stage':stage,'primary':primary,'baseline':base,'metric':field+'_gain','estimate':value,'ci_low':lo,'ci_high':hi,'one_sided_block_signflip_p':signflip(g,'gain'),'fraction_parents_improved':float((g.gain>TOL).mean())})
    contrasts=pd.DataFrame(contrasts);csvsave(OUT/(stage+'_contrasts.csv'),contrasts)
    gate={};p=summary[summary.model.eq(primary)].iloc[0]
    gate['positive_primary_rho']=bool(p.spearman>0 and p.spearman_ci_low>0)
    for base in baselines:
        c=contrasts[contrasts.baseline.eq(base)&contrasts.metric.eq('spearman_gain')].iloc[0]
        gate['rank_advantage_'+base]=bool(c.estimate>0 and c.ci_low>0 and c.one_sided_block_signflip_p<=.05)
    for base in (['uniform'] if stage=='test_a' else ['uniform','simple_full']):
        c=contrasts[contrasts.baseline.eq(base)&contrasts.metric.eq('regret_gain')].iloc[0]
        wrong=contrasts[contrasts.baseline.eq(base)&contrasts.metric.eq('wrong_direction_gain')].iloc[0]
        gate['candidate_superiority_'+base]=bool(c.estimate>=.02 and c.ci_low>0 and c.fraction_parents_improved>.5 and wrong.estimate>=-TOL)
    verdict={'stage':stage,'primary':primary,'strong_success':all(gate.values()),'checks':gate,'parents':len(mp),'genes':mp.gene.nunique(),'overlap_components':mp.overlap_component.nunique(),'snps':int(mp.snps.sum()),'exposure':'PARTIALLY EXPOSED; no untouched-confirmation claim','interpretation':'strong bounded signal' if all(gate.values()) else ('partial/uncertain signal' if p.spearman>0 else 'zero/negative primary signal'),'test_b_run_allowed':stage=='test_a' and not all(gate.values())}
    jsave(OUT/(stage+'_verdict.json'),verdict)
    print(stage,verdict);print(summary[['model','spearman','spearman_ci_low','spearman_ci_high']].to_string(index=False))
    return metrics,decisions,ranks
