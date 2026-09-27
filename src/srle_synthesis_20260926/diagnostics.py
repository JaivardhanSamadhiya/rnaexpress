from .common import *
from src.srle_prediction_20260926.core import training_mask
from src.research_20260921.robustness import count_features
from .decompose import VOCAB

def run():
    source,effects,choices,fits,roster=load()
    a=roster.copy();a['replicates_same_sign']=sign(a.rep1_delta)==sign(a.rep2_delta)
    a['published_opposes_both']=a.replicates_same_sign&(sign(a.published_delta)!=sign(a.rep1_delta))
    a['published_agrees_rep1']=sign(a.published_delta)==sign(a.rep1_delta);a['published_agrees_rep2']=sign(a.published_delta)==sign(a.rep2_delta)
    csvsave(OUT/'target_agreement.csv',group_summary(a,['replicates_same_sign','published_opposes_both','published_agrees_rep1','published_agrees_rep2']))
    controls=pd.read_csv(ART/'control_predictions.csv',dtype={'group':str},float_precision='round_trip')
    primary=effects[effects.scheme.eq('purged_composition_holdout')&effects.model.eq('2mer')].set_index(['parent','candidate']).predicted_delta
    p=np.array([primary.loc[r.parent,r.candidate] for r in controls.itertuples()]);contrasts=[]
    for target in ('published','rep1','rep2'):
        y=controls[target+'_delta'].to_numpy()
        for name in controls.columns[6:]:
            t=pd.DataFrame({'group':controls.group,'model_loss':(p-y)**2,'control_loss':(controls[name]-y)**2,'zero_loss':y*y}).groupby('group').sum()
            ix=draws(len(t));v=1-t.model_loss.sum()/t.control_loss.sum();boot=1-t.model_loss.to_numpy()[ix].sum(1)/t.control_loss.to_numpy()[ix].sum(1)
            lo,hi=np.quantile(boot,[.025,.975]);contrasts.append({'target':target,'model':'2mer','control':name,'relative_mse_reduction':v,'ci_low':lo,'ci_high':hi,'groups':60,'edges':1744,'status':'paired descriptive class bootstrap; all controls retained'})
    csvsave(OUT/'control_paired_comparisons.csv',pd.DataFrame(contrasts))
    x=count_features(source.kmer.to_numpy())[:,4:20];rows=[]
    for fit in fits:
        train=training_mask(source,fit['scheme'],fit['held_group'])
        for j,feature in enumerate(VOCAB[2]):rows.append({'scheme':fit['scheme'],'held_group':fit['held_group'],'feature':feature,'training_n':int(train.sum()),'training_presence_frequency':np.mean(x[train,j]>0),'training_mean_count':x[train,j].mean(),'training_min_count':x[train,j].min(),'training_max_count':x[train,j].max()})
    csvsave(OUT/'coefficient_fold_feature_support.csv',pd.DataFrame(rows))
    d=pd.read_csv(ART/'recommendation_decisions.csv',dtype={'group':str});rows=[]
    for model,g in d.groupby('model'):
        for metric in ('published_regret','published_best_choice','top3_best_recovery','wrong_both'):
            finite=g[g[metric].notna()];rows.append({'model':model,'metric':metric,'decisions':len(finite),'composition_classes':finite.group.nunique(),'biological_contexts':1})
    csvsave(OUT/'recommendation_metric_denominators.csv',pd.DataFrame(rows))
    # Single table separates magnitude, ranking and directional risk with original intervals.
    pm=pd.read_csv(OLD/'prediction_metrics.csv');pc=pd.read_csv(OLD/'prediction_comparisons.csv');dm=pd.read_csv(OLD/'decision_metrics.csv');dc=pd.read_csv(OLD/'decision_comparisons.csv')
    rows=[]
    for model in sorted(d.model.unique()):
        dmrow=dm[dm.scheme.eq('purged_composition_holdout')&dm.model.eq(model)&dm.direction.eq(0)].iloc[0]
        row={'model':model,'regret':dmrow.published_regret,'regret_ci_low':dmrow.published_regret_ci_low,'regret_ci_high':dmrow.published_regret_ci_high,'wrong_direction':dmrow.published_wrong_direction,'wrong_both':dmrow.wrong_both,'wrong_both_ci_low':dmrow.wrong_both_ci_low,'wrong_both_ci_high':dmrow.wrong_both_ci_high}
        if model!='uniform':
            p=pm[pm.scheme.eq('purged_composition_holdout')&pm.model.eq(model)&pm.target.eq('published')&pm.kind.eq('edit_delta')].iloc[0]
            row.update(rmse=p.rmse,pearson=p.pearson,calibration_slope=p.calibration_slope)
            if model!='composition':
                q=pc[pc.scheme.eq('purged_composition_holdout')&pc.model.eq(model)&pc.comparator.eq('composition')&pc.target.eq('published')&pc.kind.eq('edit_delta')].iloc[0]
                row.update(mse_reduction=q.relative_mse_reduction,mse_reduction_ci_low=q.ci_low,mse_reduction_ci_high=q.ci_high)
            else:row.update(mse_reduction=0,mse_reduction_ci_low=0,mse_reduction_ci_high=0)
        rows.append(row)
    csvsave(OUT/'model_comparison.csv',pd.DataFrame(rows))
    csvsave(OUT/'recommender_paired_contrasts.csv',dc[dc.scheme.eq('purged_composition_holdout')&dc.direction.eq(0)&dc.model.eq('2mer')&dc.comparator.eq('kmer123')])
    aliases={
        'data/raw/PMC12864922_figure4':'TDP localization; source ID documented in reports/v3_tdp_source_data_audit.md',
        'data/raw/PMC12864922_supplementary':'TDP source; potentially protected EV5 members not opened',
        'data/raw/TaliaferroLab_OligoPools':'Existing design repository; identities cannot establish a new measured outcome experiment; members not opened',
        'data/raw/tdp43_mm10_gene_slices':'TDP sequence reference resource, not new measured experiment',
        'data/raw/finalshot_resource_audit':'Historical model/resource audit, no new measured cohort inferred',
        'data/raw/phaseB2_aux_audit':'Historical auxiliary resource audit; no new source admission',
        'data/external/RNAloc_MPRA':'Mikl design/mapping repository, already exposed GSE173098; reports/v2_5_mikl_xgboost_pretraining_protocol.md',
        'data/external/3utrbert':'Model weights/resources, not measured edit cohort',
        'data/external/splicebert':'Model weights/resources, not measured edit cohort',
        'data/external/transformers':'Software/model cache, not independently measured outcomes',
        'data/external/research_20260921':'Existing Faraway/Shukla/SRLE cached resources and provenance; no new archive opened',
        'data/external/mechanism_v2':'Existing resource audit and stability reads; stability not localization'
    }
    jsave(OUT/'local_directory_crosswalk.json',{'scope':'Safe top-level names plus existing reports; no raw archive contents or protected outcomes opened','aliases':aliases,'external_top_level_names':sorted(p.name for p in (ROOT/'data/external').iterdir() if p.is_dir()),'finding':'No additional admitted untouched experiment established; uninspected members remain unknown/protected, not silently certified absent'})
    print('Additional saved-prediction diagnostics complete')

if __name__=='__main__':run()
