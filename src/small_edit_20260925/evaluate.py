"""Size-stratified effect/direction/decision metrics from fixed predictions."""
from .common import *
from .features import BASELINES
from scipy.stats import pearsonr,spearmanr,rankdata
from sklearn.metrics import roc_auc_score

MODELS=BASELINES+('primary',)


def corr(y,p,kind='pearson'):
    if len(y)<(2 if kind=='spearman' else 3) or np.ptp(y)==0 or np.ptp(p)==0: return np.nan
    return float((pearsonr if kind=='pearson' else spearmanr)(y,p).statistic)


def summary(v,seed=20260925):
    v=np.asarray(v,float); v=v[np.isfinite(v)]
    if not len(v): return (np.nan,np.nan,np.nan,0)
    rng=np.random.default_rng(seed); draws=rng.integers(0,len(v),(2000,len(v)))
    return (float(v.mean()),*np.quantile(v[draws].mean(1),[.025,.975]).tolist(),len(v))


def gene_metrics(g,p,prob):
    y=g.localization_change.to_numpy(float); nonzero=y!=0
    labels=y[nonzero]>0; call=prob[nonzero]>=.5
    result={'mse':float(np.mean((y-p)**2)),'mae':float(np.mean(np.abs(y-p))),
        'sign_accuracy':float(np.mean(np.sign(p[nonzero])==np.sign(y[nonzero]))) if nonzero.any() else np.nan,
        'probability_accuracy':float(np.mean(call==labels)) if nonzero.any() else np.nan,
        'brier':float(np.mean((prob[nonzero]-labels)**2)) if nonzero.any() else np.nan,
        'auroc':float(roc_auc_score(labels,prob[nonzero])) if len(set(labels))==2 else np.nan,
        'balanced_accuracy':float(np.mean([np.mean(call[labels]),np.mean(~call[~labels])])) if len(set(labels))==2 else np.nan,
        'pearson':corr(y,p),'spearman':corr(y,p,'spearman')}
    return result


def metric_tables(frame):
    records=[]; totals=[]; calibration=[]
    for (cell,b),part in frame.groupby(['cell_type','edit_size_band']):
        for model in MODELS:
            for gene,g in part.groupby('gene_name'):
                result=gene_metrics(g,g['pred_'+model].to_numpy(),g['prob_'+model].to_numpy())
                records.append({'context':cell,'edit_size_band':b,'model':model,'gene':gene,'rows':len(g),**result})
            y=part.localization_change.to_numpy(); p=part['pred_'+model].to_numpy(); prob=part['prob_'+model].to_numpy(); nz=y!=0
            w=1/part.groupby('gene_name').gene_name.transform('size').to_numpy()
            slope=float(np.cov(p,y,ddof=0)[0,1]/np.var(p)) if np.var(p)>0 else np.nan
            totals.append({'context':cell,'edit_size_band':b,'model':model,'rows':len(part),'genes':part.gene_name.nunique(),
                'global_pearson_descriptive':corr(y,p),'global_spearman_descriptive':corr(y,p,'spearman'),
                'global_gene_weighted_auroc_descriptive':float(roc_auc_score(y[nz]>0,prob[nz],sample_weight=w[nz])) if len(set(y[nz]>0))==2 else np.nan,
                'calibration_slope_descriptive':slope,'calibration_intercept_descriptive':float(y.mean()-slope*p.mean()) if np.isfinite(slope) else np.nan,
                'zero_observed_effects':int((~nz).sum())})
            for j in range(5):
                mask=nz&(prob>=j/5)&(prob<((j+1)/5) if j<4 else prob<=1)
                calibration.append({'context':cell,'edit_size_band':b,'model':model,'probability_bin':f'{j/5:.1f}-{(j+1)/5:.1f}',
                    'rows':int(mask.sum()),'mean_probability':float(np.average(prob[mask],weights=w[mask])) if mask.any() else np.nan,
                    'observed_positive_fraction':float(np.average(y[mask]>0,weights=w[mask])) if mask.any() else np.nan})
    genes=pd.DataFrame(records)
    aggregate=[]
    metrics=['mse','mae','sign_accuracy','probability_accuracy','brier','auroc','balanced_accuracy','pearson','spearman']
    for (cell,b,m),g in genes.groupby(['context','edit_size_band','model']):
        row={'context':cell,'edit_size_band':b,'model':m}
        for metric in metrics:
            v,lo,hi,n=summary(g[metric])
            row.update({metric:v,metric+'_ci_low':lo,metric+'_ci_high':hi,metric+'_eligible_genes':n})
        row.update(rmse=np.sqrt(row['mse']),rmse_ci_low=np.sqrt(row['mse_ci_low']),rmse_ci_high=np.sqrt(row['mse_ci_high']))
        aggregate.append(row)
    return genes,pd.DataFrame(aggregate),pd.DataFrame(totals),pd.DataFrame(calibration)


def decisions(frame):
    rows=[]; ranked=[]
    for (cell,b,parent),g in frame.groupby(['cell_type','edit_size_band','parent_id']):
        if g.mutant_id.nunique()<2: continue
        g=g.sort_values(['mutant_sequence','mutant_id']).reset_index(drop=True)
        y=g.localization_change.to_numpy()
        if np.ptp(y)<=0: continue
        for sign in (-1,1):
            truth=sign*y; span=np.ptp(truth)
            uniform=(truth.max()-truth.mean())/span
            for model in MODELS:
                p=sign*g['pred_'+model].to_numpy()
                index=int(np.argmax(p)); value=truth[index]
                rank=float(rankdata(-truth,method='min')[index])
                rows.append({'context':cell,'edit_size_band':b,'parent':parent,'gene':g.gene_name.iloc[0],
                    'fold':int(g.biological_fold.iloc[0]),'direction':sign,'model':model,'candidates':len(g),
                    'selected_id':g.mutant_id.iloc[index],'measured_effect':float(y[index]),'predicted_effect':float(g['pred_'+model].iloc[index]),
                    'regret':float((truth.max()-value)/span),'uniform_regret':float(uniform),
                    'correct_direction':float(value>0),'wrong_direction':float(value<0),'zero_change':float(value==0),
                    'best_choice':float(value==truth.max()),'top3':float(rank<=min(3,len(g))),
                    'top3_informative':float(rank<=3) if len(g)>3 else np.nan,
                    'within_parent_rank_correlation':corr(y,g['pred_'+model].to_numpy(),'spearman'),
                    'unit_status':'held-out gene; previously exposed development source'})
            order=np.argsort(-sign*g.pred_primary.to_numpy(),kind='stable')
            pranks=np.empty(len(g),int); pranks[order]=np.arange(1,len(g)+1)
            yranks=rankdata(-truth,method='min')
            for i,r in g.iterrows():
                ranked.append({'parent':parent,'gene':r.gene_name,'edit':r.mutant_id,'parent_sequence':r.parent_sequence,
                    'mutant_sequence':r.mutant_sequence,'edit_positions':r.edit_positions,'edit_size_band':b,
                    'context':cell,'direction':sign,'fold':int(r.biological_fold),'measured_effect':r.localization_change,
                    'predicted_effect':r.pred_primary,'predicted_rank':int(pranks[i]),'measured_rank':float(yranks[i]),
                    'selected':bool(pranks[i]==1),'selected_correct_direction':bool(truth[i]>0) if pranks[i]==1 else '',
                    'status':'within exact parent; gene held out; source reused'})
    return pd.DataFrame(rows),pd.DataFrame(ranked)


def summarize_decisions(rows):
    cols=['regret','uniform_regret','correct_direction','wrong_direction','zero_change','best_choice','top3','top3_informative','within_parent_rank_correlation']
    genes=rows.groupby(['context','edit_size_band','model','gene'])[cols].mean().reset_index()
    result=[]; contrasts=[]
    for (cell,b,model),g in genes.groupby(['context','edit_size_band','model']):
        row={'context':cell,'edit_size_band':b,'model':model,'eligible_genes':len(g)}
        for metric in cols:
            v,lo,hi,n=summary(g[metric]); row.update({metric:v,metric+'_ci_low':lo,metric+'_ci_high':hi,metric+'_eligible_genes':n})
        result.append(row)
    for (cell,b),g in genes.groupby(['context','edit_size_band']):
        primary=g[g.model.eq('primary')].set_index('gene')
        for model in BASELINES:
            base=g[g.model.eq(model)].set_index('gene').loc[primary.index]
            gain=base.regret-primary.regret
            value,lo,hi,n=summary(gain)
            wrong=primary.wrong_direction-base.wrong_direction
            w,wlo,whi,_=summary(wrong)
            contrasts.append({'context':cell,'edit_size_band':b,'comparator':model,'eligible_genes':n,
                'regret_gain':value,'regret_gain_ci_low':lo,'regret_gain_ci_high':hi,
                'fraction_genes_improved':float((gain>0).mean()),
                'wrong_direction_increase':w,'wrong_direction_ci_low':wlo,'wrong_direction_ci_high':whi,
                'descriptive_criterion_met':bool(n>=20 and lo>0 and value>=.02 and (gain>0).mean()>.5 and w<=0)})
    return genes,pd.DataFrame(result),pd.DataFrame(contrasts)


def run():
    receipt=readj(OUT/'prediction_receipt.json')
    if sha256(OUT/'small_edit_predictions.csv')!=receipt['prediction_sha256']: raise ValueError('Predictions changed')
    frame=pd.read_csv(OUT/'small_edit_predictions.csv')
    genes,metrics,global_metrics,calibration=metric_tables(frame)
    rows,ranks=decisions(frame)
    decision_genes,decision_metrics,contrasts=summarize_decisions(rows)
    for name,table in [('effect_direction_gene_metrics.csv',genes),('effect_direction_metrics.csv',metrics),
        ('global_prediction_metrics.csv',global_metrics),('direction_calibration.csv',calibration),
        ('small_edit_decisions.csv.gz',rows),('small_edit_candidate_selection.csv',ranks),
        ('decision_gene_metrics.csv',decision_genes),('decision_metrics.csv',decision_metrics),('paired_decision_comparisons.csv',contrasts)]: csvsave(name,table)
    differences=[]
    for (cell,b),g in genes.groupby(['context','edit_size_band']):
        primary=g[g.model.eq('primary')].set_index('gene')
        for model in BASELINES:
            baseline=g[g.model.eq(model)].set_index('gene').loc[primary.index]
            for metric in ('mse','mae','brier','sign_accuracy','auroc','balanced_accuracy'):
                # Positive is favorable for primary in each named comparison.
                diff=(baseline[metric]-primary[metric]) if metric in ('mse','mae','brier') else (primary[metric]-baseline[metric])
                v,lo,hi,n=summary(diff)
                differences.append({'context':cell,'edit_size_band':b,'comparator':model,'metric':metric,'gain':v,'ci_low':lo,'ci_high':hi,'eligible_genes':n})
    csvsave('paired_prediction_comparisons.csv',pd.DataFrame(differences))
    jsave('evaluation_receipt.json',{'status':'PASS','prediction_rows':len(frame),'candidate_rank_rows':len(ranks),
        'decision_rows_all_models':len(rows),'prediction_freeze_sha256':sha256(OUT/'prediction_freeze.json'),
        'primary_results':metrics[metrics.model.eq('primary')].to_dict('records'),
        'primary_decision_results':decision_metrics[decision_metrics.model.eq('primary')].to_dict('records'),
        'claim_status':'Exploratory reused-development evidence; report every size/context separately; no independent confirmation',
        'all_comparator_decision_flags':contrasts.groupby(['context','edit_size_band']).descriptive_criterion_met.all().reset_index().to_dict('records')})
    print(metrics[metrics.model.isin(['primary','no_change','delta_AU','delta123','paired'])][['context','edit_size_band','model','rmse','mae','sign_accuracy','auroc']].to_string(index=False),flush=True)
    print(decision_metrics[decision_metrics.model.eq('primary')][['context','edit_size_band','eligible_genes','regret','correct_direction','wrong_direction']].to_string(index=False),flush=True)


if __name__=='__main__': run()
