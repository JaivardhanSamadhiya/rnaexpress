"""Fixed SRLE/SIRLOIN model differences; no fit, sign search or new candidates."""
from .common import *
from .evaluate import corr,summary
from src.research_20260921.sirloin_transfer import window_mean,motif_count
from src.research_20260921.srle_risk_replay import replay
from src.research_20260921.srle_aggregate_replay import replay as swap_replay
from sklearn.metrics import roc_auc_score

RESEARCH=ROOT/'results/research_20260921'


def run():
    inv=readj(OUT/'inventory_receipt.json')
    if sha256(OUT/'small_edit_pairs.csv.gz')!=inv['outputs']['small_edit_pairs.csv.gz']: raise ValueError('Inventory changed')
    frame=pd.read_csv(OUT/'small_edit_pairs.csv.gz')
    source=pd.read_csv(RESEARCH/'robustness_predictions.csv').set_index('kmer')
    sirloin=pd.read_csv(RESEARCH/'sirloin_transfer_predictions.csv').set_index('id')
    output=[]
    for dataset in ('srle','sirloin'):
        for r in frame[frame.dataset.eq(dataset)].itertuples():
            if not np.isfinite(r.localization_change): continue
            effects=np.array([float(x) for x in r.replicate_delta_values.split(';')])
            if not np.isfinite(effects).all(): continue
            if dataset=='srle':
                predictions={m:float(source.loc[r.mutant_id,m]-source.loc[r.parent_id,m]) for m in ('composition','position_additive','position_pair','kmer123')}
                group=r.composition; mutation_class='two_position_swap'
            else:
                lookups={'srle_kmer123':source.kmer123.to_dict(),'srle_pair':source.position_pair.to_dict(),'srle_measured':source.nrs.to_dict()}
                predictions={m:float(sirloin.loc[r.mutant_id,m]-window_mean(r.parent_sequence,lookup)) for m,lookup in lookups.items()}
                predictions.update({m:float(sirloin.loc[r.mutant_id,m]-motif_count(r.parent_sequence,motif)) for m,motif in [('ccc','CCC'),('cctccc','CCTCCC')]})
                predictions['composition']=0.
                group=r.parent_id; mutation_class=sirloin.loc[r.mutant_id,'mutation']
            for rep,effect in enumerate(effects,1):
                for model,delta in predictions.items():
                    output.append({'dataset':dataset,'parent':r.parent_id,'edit':r.mutant_id,'parent_sequence':r.parent_sequence,
                        'mutant_sequence':r.mutant_sequence,'edit_positions':r.edit_positions,'edit_size_band':r.edit_size_band,
                        'replicate':rep,'group':group,'mutation_class':mutation_class,'model':model,
                        'measured_effect':float(effect),'predicted_score_difference':delta,
                        'predicted_effect':delta if dataset=='srle' else np.nan,'predicted_direction':int(np.sign(delta)),
                        'predicted_probability':np.nan,'magnitude_comparable':dataset=='srle',
                        'measurement_units':'log2 NRS difference' if dataset=='srle' else 'Nuc/Cyto ratio difference',
                        'score_units':'source NRS log2 difference' if model not in ('ccc','cctccc','composition') else 'motif count / tie score',
                        'fold_status':'original exact-sequence holdout in one shared reporter' if dataset=='srle' else 'original source-only external discovery; exposed now; two parents',
                        'uncertainty_scope':'composition classes conditional on one experiment' if dataset=='srle' else 'two biological parents; descriptive only'})
    predictions=pd.DataFrame(output); csvsave('small_edit_secondary_predictions.csv',predictions)
    global_rows=[]; choices=[]
    for (dataset,rep,model),g in predictions.groupby(['dataset','replicate','model']):
        y=g.measured_effect.to_numpy(); p=g.predicted_score_difference.to_numpy(); mask=y!=0
        global_rows.append({'dataset':dataset,'replicate':rep,'model':model,'pairs':len(g),
            'pearson':corr(y,p),'spearman':corr(y,p,'spearman'),
            'sign_accuracy':float(np.mean(np.sign(y[mask])==np.sign(p[mask]))),
            'direction_auroc_score':float(roc_auc_score(y[mask]>0,p[mask])) if len(set(y[mask]>0))==2 else np.nan,
            'mae':float(np.mean(np.abs(y-p))) if dataset=='srle' else np.nan,
            'rmse':float(np.sqrt(np.mean((y-p)**2))) if dataset=='srle' else np.nan,
            'magnitude_limitation':'same score units; descriptive repeated experiment' if dataset=='srle' else 'source log score and target ratio differences not calibrated; magnitude metrics omitted'})
        for (parent,mutation),h in g.groupby(['parent','mutation_class']):
            minimum=2 if dataset=='srle' else 5
            if len(h)<minimum or np.ptp(h.measured_effect)==0: continue
            h=h.sort_values(['mutant_sequence','edit']).reset_index(drop=True)
            for direction in (-1,1):
                truth=direction*h.measured_effect.to_numpy(); score=direction*h.predicted_score_difference.to_numpy()
                i=int(np.argmax(score)); value=float(truth[i]); span=float(np.ptp(truth))
                choices.append({'dataset':dataset,'replicate':rep,'model':model,'parent':parent,'mutation_class':mutation,
                    'group':h.group.iloc[0],'direction':direction,'selected_id':h.edit.iloc[i],'candidate_count':len(h),
                    'directed_measured_effect':value,'regret':float((truth.max()-value)/span),
                    'uniform_regret':float((truth.max()-truth.mean())/span),'correct_direction':float(value>0),
                    'wrong_direction':float(value<0),'best_choice':float(value==truth.max())})
    choice=pd.DataFrame(choices)
    csvsave('secondary_effect_direction_metrics.csv',pd.DataFrame(global_rows))
    csvsave('secondary_candidate_selection.csv',choice)
    means=choice.groupby(['dataset','replicate','model','group'])[['regret','uniform_regret','correct_direction','wrong_direction','best_choice']].mean().reset_index()
    summaries=[]
    for (dataset,rep,model),g in means.groupby(['dataset','replicate','model']):
        row={'dataset':dataset,'replicate':rep,'model':model,'groups':len(g)}
        for metric in ('regret','uniform_regret','correct_direction','wrong_direction','best_choice'):
            value,lo,hi,n=summary(g[metric]); row[metric]=value
            row[metric+'_ci_low']=lo if dataset=='srle' else np.nan
            row[metric+'_ci_high']=hi if dataset=='srle' else np.nan
        row['uncertainty_scope']='conditional composition-class bootstrap' if dataset=='srle' else 'no biological population interval from two parents'
        summaries.append(row)
    csvsave('secondary_decision_metrics.csv',pd.DataFrame(summaries))
    # Verify identical previously selected IDs rather than merely similar summaries.
    saved=pd.read_csv(RESEARCH/'raw_swap_evaluation.csv')
    check=choice[choice.dataset.eq('srle')].merge(saved,left_on=['parent','replicate','model','direction'],right_on=['parent','replicate','model','direction'],validate='one_to_one')
    if len(check)!=len(saved) or not (check.selected_id==check.selected).all(): raise ValueError('Frozen SRLE choices differ')
    if np.max(np.abs((check.uniform_regret-check.regret)-check.regret_gain))>1e-12: raise ValueError('Frozen regret differs')
    replay1=swap_replay(RESEARCH/'srle_aggregate_replay_20260924')
    replay2=replay(RESEARCH/'srle_risk_replay_20260924')
    jsave('secondary_receipt.json',{'status':'PASS','models_fit':0,'new_candidates':0,'frozen_srle_choices_verified':len(check),
        'srle_aggregate_replay_max_error':replay1['max_absolute_difference'],'srle_risk_replay_max_error':replay2['max_absolute_discrepancy'],
        'sirloin_magnitude_metrics':'not reported: source log score vs target ratio scale; no target calibration',
        'rows':len(predictions),'script_sha256':sha256(__file__)})
    print(pd.DataFrame(global_rows).to_string(index=False),flush=True)


if __name__=='__main__': run()
