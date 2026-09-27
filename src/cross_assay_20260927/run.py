"""Execute only the committed development grid, preserving every fold."""
from .common import *
from .models import fit,predict,purge
from .feasibility import fit_feasibility,predict_feasibility
from .metrics import evaluate,aggregate
import gzip,io

def load():
    f=pd.read_csv(ART/'canonical_interventions.csv',low_memory=False);ix=pd.read_csv(OUT/'model_row_index.csv')
    f=f.set_index('intervention_id').loc[ix.intervention_id].reset_index()
    data=np.load(ART/'features.npz');return f,{k:data[k].astype(float) for k in data.files}
def safe_id(text):return hashlib.sha256(text.encode()).hexdigest()[:16]
def run():
    frozen();assert not (OUT/'run_complete.json').exists(),'Preserve completed study'
    frame,xs=load();cfg=config();core=frame.primary_eligible.to_numpy();studies=cfg['core_studies'];models=cfg['models']
    all_decisions=[];rankings=[];prediction_rows=[];folds=[];failures=[];feature_effects=[]
    def job(stage,held,train,test,names,custom=None):
        if not test.any():return
        if stage!='within_assay':train=purge(frame,train,test)
        tr=frame.loc[train].reset_index(drop=True);te=frame.loc[test].reset_index(drop=True)
        if len(tr)==0 or tr.parent_context_id.nunique()<2:
            failures.append({'stage':stage,'held':held,'status':'INELIGIBLE','reason':'No disjoint multi-context training pool','test_rows':len(te)});return
        fold=safe_id(stage+'|'+held);fp=OUT/'fits'/('feasibility_'+fold+'.json')
        fm=readj(fp) if fp.exists() else fit_feasibility(tr,xs['feasibility'][train]);jsave(fp,fm)
        feas=predict_feasibility(fm,te,xs['feasibility'][test])
        folds.append({'fold_id':fold,'stage':stage,'held':held,'training_rows':len(tr),'test_rows':len(te),'training_studies':sorted(tr.dataset.unique()),'test_studies':sorted(te.dataset.unique()),'training_components':sorted(tr.biological_component.unique()),'test_components':sorted(te.biological_component.unique()),'training_ids_sha256':hashlib.sha256('|'.join(tr.intervention_id).encode()).hexdigest(),'test_ids_sha256':hashlib.sha256('|'.join(te.intervention_id).encode()).hexdigest(),'self_evaluation_only':stage=='within_assay'})
        # Uniform is an exact expectation, not a stochastic selected edit.
        dr,rr=evaluate(te,np.zeros(len(te)),np.full(len(te),.5),feas,stage,'uniform',held);all_decisions.extend(dr)
        for name in names:
            if custom and name in custom:matrix,kind=custom[name]
            else:feature,kind=models[name];matrix=xs[feature]
            path=OUT/'fits'/(fold+'_'+name+'.json')
            model=readj(path) if path.exists() else fit(tr,matrix[train],kind)
            jsave(path,model);universal,residual,prob=predict(model,matrix[test],te.dataset.to_numpy())
            if stage in ('held_assay','held_domain','family_transfer','secondary_sirloin','pretrained_restricted'):assert np.all(residual==0),'Held study residual leakage'
            score=universal+residual
            dr,rr=evaluate(te,score,prob,feas,stage,name,held);all_decisions.extend(dr);rankings.extend(rr)
            if name=='hierarchical' and stage in ('within_assay','held_parent'):
                dr,_=evaluate(te,universal,prob,feas,stage,'hierarchical_universal_only',held);all_decisions.extend(dr)
            if stage=='within_assay':
                # Independent per-study coefficients, removed training scale; source outcomes exposed.
                beta=(np.array(model['universal_beta'])+np.array(model['residual_beta'].get(held,np.zeros(len(model['scale'])))))/model['scale']
                feature_effects.extend({'dataset':held,'model':name,'feature_index':i,'coefficient':float(v)} for i,v in enumerate(beta))
            if stage in ('held_assay','secondary_sirloin','held_domain','family_transfer','pretrained_restricted'):
                z=(matrix[test]-model['mean'])/model['scale'];distance=np.sqrt(np.mean(z*z,axis=1))
                prediction_rows.extend({'stage':stage,'model':name,'held':held,'fold_id':fold,'intervention_id':r.intervention_id,'dataset':r.dataset,'parent_context_id':r.parent_context_id,'universal_score':float(universal[i]),'assay_residual':float(residual[i]),'final_score':float(score[i]),'direction_probability':float(prob[i]),'training_standardized_distance':float(distance[i]),'observed_effect':float(r.measured_delta),'observed_within_parent_rank':float(r.within_parent_rank)} for i,r in enumerate(te.itertuples()))
            print(stage,held,name,'complete',flush=True)
    # The core outer predictions are produced before any secondary task.
    for study in studies:job('held_assay',study,core&frame.dataset.ne(study).to_numpy(),core&frame.dataset.eq(study).to_numpy(),list(models))
    # Complete labels and source residual contributions are development diagnostics only.
    for study in studies:
        same=core&frame.dataset.eq(study).to_numpy();job('within_assay',study,same,same,list(models))
        if frame.loc[same].biological_component.nunique()<2:
            failures.append({'stage':'held_parent','held':study,'status':'INELIGIBLE','reason':'one biological context; no independent parent holdout'});continue
        for fold in sorted(frame.loc[same,'held_parent_fold'].unique()):
            test=same&frame.held_parent_fold.eq(fold).to_numpy();train=same&~frame.held_parent_fold.eq(fold).to_numpy();job('held_parent',study+':fold'+str(fold),train,test,list(models))
    compact=['kmer123','hierarchical','interaction_10']
    for domain in sorted(frame.loc[core,'endpoint_class'].unique()):job('held_domain',domain,core&frame.endpoint_class.ne(domain).to_numpy(),core&frame.endpoint_class.eq(domain).to_numpy(),compact)
    for study in studies:
        test=core&frame.dataset.eq(study).to_numpy();domain=frame.loc[test,'endpoint_class'].iloc[0]
        job('family_transfer',study,core&frame.dataset.ne(study).to_numpy()&frame.endpoint_class.eq(domain).to_numpy(),test,compact)
    sirloin=frame.dataset.eq('sirloin').to_numpy();job('secondary_sirloin','sirloin',core,sirloin,compact)
    # Frozen encoder is available for two studies only. Full decision contexts are matched.
    bert=np.load(ART/'pretrained_covered.npz');covered=np.zeros(len(frame),bool);covered[bert['indices']]=True
    emb=np.full((len(frame),128),np.nan);emb[bert['indices']]=bert['values'];hybrid=np.column_stack([xs['kmer123'],emb])
    for study in ['mikl_gse173098','moffatt_gse334718']:
        train=core&covered&frame.dataset.ne(study).to_numpy();test=core&covered&frame.dataset.eq(study).to_numpy()
        assert np.isfinite(hybrid[train|test]).all()
        job('pretrained_restricted',study,train,test,['matched_kmer123','frozen_bert_plus_kmer'],{'matched_kmer123':(xs['kmer123'],'pooled'),'frozen_bert_plus_kmer':(hybrid,'pooled')})
    dec=pd.DataFrame(all_decisions);pred=pd.DataFrame(prediction_rows);ranks=pd.DataFrame(rankings)
    csvsave(OUT/'decision_metrics.csv',dec);csvsave(ART/'model_comparison.csv',aggregate(dec))
    csvsave(ART/'leave_one_assay_out_predictions.csv',pred[pred.stage.eq('held_assay')]);csvsave(ART/'candidate_rankings.csv',ranks)
    save(ART/'leave_one_assay_out_predictions.csv.gz',gzip.compress((ART/'leave_one_assay_out_predictions.csv').read_bytes(),mtime=0));save(ART/'candidate_rankings.csv.gz',gzip.compress((ART/'candidate_rankings.csv').read_bytes(),mtime=0))
    csvsave(ART/'secondary_predictions.csv',pred[~pred.stage.eq('held_assay')]);csvsave(OUT/'feature_effects.csv',pd.DataFrame(feature_effects));jsave(OUT/'fold_manifest.json',folds);jsave(OUT/'ineligible_tasks.json',failures)
    jsave(OUT/'run_complete.json',{'status':'PASS','decision_rows':len(dec),'held_assay_predictions':int(pred.stage.eq('held_assay').sum()),'rank_rows':len(ranks),'folds':len(folds),'ineligible_tasks':failures,'no_independent_validation':True,'no_new_source_outcomes':True})
    print('Development grid complete; gate remains to be calculated from saved results.',flush=True)
if __name__=='__main__':run()
