from .common import *
from .models import fit_all_inputs,fit_method
from .evaluate import decisions,calibration,ambiguity,summarize,conditional_eligibility
from src.cross_assay_20260927.models import purge
from src.cross_assay_20260927.run import safe_id

def run():
    frozen();assert not (OUT/'run_complete.json').exists(),'Preserve completed generation'
    frame,x,r,pairs=load();core=np.ones(len(frame),bool);oldfolds={ (f['stage'],f['held']):f for f in readj(OLD/'fold_manifest.json')};oldpred=pd.read_csv(OA/'leave_one_assay_out_predictions.csv',usecols=['model','dataset','intervention_id','final_score'],float_precision='round_trip');oldpred=oldpred[oldpred.model.eq('interaction_3')].set_index('intervention_id');amb=ambiguity(frame,r)
    old_dec=pd.read_csv(OLD/'decision_metrics.csv',usecols=['stage','model','parent_context_id','direction','selected_id','regret'],float_precision='round_trip');old_dec=old_dec[old_dec.stage.eq('held_assay')&old_dec.model.eq('interaction_3')].set_index(['parent_context_id','direction'])
    all_dec=[];rank=[];raw=[];pol=[];pred=[];cals=[];bins=[];probrows=[];folds=[];replays=[];conditional={'eligible_models':[]}
    def job(stage,held,train,test,names,slots=None,testslots=None):
        nonlocal all_dec,rank,raw,pol,pred,cals,bins,probrows
        if stage!='cross_replicate':train=purge(frame,train,test)
        tr=frame[train];te=frame[test].copy();assert len(tr)>0
        fold=safe_id(stage+'|'+held);training_hash=hashlib.sha256('|'.join(tr.intervention_id).encode()).hexdigest();test_hash=hashlib.sha256('|'.join(te.intervention_id).encode()).hexdigest()
        if stage in ('held_parent','held_assay'):
            old=oldfolds[stage,held];assert training_hash==old['training_ids_sha256'] and test_hash==old['test_ids_sha256']
        if stage=='cross_replicate':
            values=r[test][:,testslots];count=np.isfinite(values).sum(1);te['measured_delta']=np.divide(np.nansum(values,axis=1),count,out=np.full(len(te),np.nan),where=count>0)
            valid_contexts=te.groupby('parent_context_id').measured_delta.agg(['count','min','max']);allowed=valid_contexts[(valid_contexts['count']>=2)&((valid_contexts['max']-valid_contexts['min'])>TOL)].index;te=te[np.isfinite(te.measured_delta)&te.parent_context_id.isin(allowed)]
        inp=fit_all_inputs(frame,x,r,pairs,train,rep_slots=slots,crossrep=stage=='cross_replicate')
        folds.append({'stage':stage,'held':held,'fold_id':fold,'training_ids_sha256':training_hash,'test_ids_sha256':test_hash,'training_components':sorted(tr.biological_component.unique()),'test_components':sorted(te.biological_component.unique()),'training_replicate_slots':slots,'evaluation_replicate_slots':testslots,'context_holdout':stage!='cross_replicate'})
        for name in names:
            path=OUT/'fits'/(fold+'_'+name+'.json')
            if path.exists():m=readj(path)
            else:
                m,targets=fit_method(inp,name);jsave(path,m);save(OUT/'training_targets'/(fold+'_'+name+'.csv.gz'),gzip.compress(targets.to_csv(index=False,lineterminator='\n').encode(),mtime=0))
            d,rr,rawr,policy,pr,scores=decisions(te,x,r,m,stage,held,amb,replicate_diagnostic=stage=='held_assay',conditional_policy=stage=='held_assay' and name in conditional['eligible_models'])
            ca,bi,pp=calibration(te,x,r,pairs,m,stage,held,rep_slots=testslots,save_pairs=stage=='held_assay')
            for v in ca:v['components']=te.biological_component.nunique()
            all_dec.extend(d);rank.extend(rr);raw.extend(rawr);pol.extend(policy);pred.extend(pr);cals.extend(ca);bins.extend(bi);probrows.extend(pp)
            if name=='H0' and stage in ('held_assay','held_parent'):
                oldmodel=readj(OLD/'fits'/(fold+'_interaction_3.json'));error=float(np.max(abs(np.array(oldmodel['universal_beta'])-np.array(m['beta']))));assert error<1e-10,(held,error)
                if stage=='held_assay':
                    ids=te.intervention_id;actual=np.array([scores[i] for i in te.index]);err=float(np.max(abs(actual-oldpred.loc[ids,'final_score'].to_numpy())));assert err<1e-9
                    for choice in d:
                        previous=old_dec.loc[choice['parent_context_id'],choice['direction']];assert choice['selected_id']==previous.selected_id;assert abs(choice['regret']-previous.regret)<1e-12
                    replays.append({'study':held,'coefficient_error':error,'score_error':err,'rows':len(te),'selected_decisions_identical':len(d)})
            print(stage,held,name,'complete',flush=True)
    for study in STUDIES:
        same=frame.dataset.eq(study).to_numpy()
        if frame.loc[same].biological_component.nunique()<2:continue
        for fold in sorted(frame.loc[same,'held_parent_fold'].unique()):job('held_parent',study+':fold'+str(fold),same&~frame.held_parent_fold.eq(fold).to_numpy(),same&frame.held_parent_fold.eq(fold).to_numpy(),PRIMARY)
    conditional=conditional_eligibility(pd.DataFrame(cals));jsave(OUT/'conditional_policy_eligibility.json',conditional)
    csvsave(OUT/'held_parent_sanity.csv',summarize(pd.DataFrame(all_dec)))
    for study,nr in [(STUDIES[0],14),(STUDIES[1],3),('srle',2)]:
        same=frame.dataset.eq(study).to_numpy();a=list(range(0,nr,2));b=list(range(1,nr,2))
        for tag,slots,testslots in [('A_to_B',a,b),('B_to_A',b,a)]:job('cross_replicate',study+':'+tag,same,same,PRIMARY,slots,testslots)
    for study in STUDIES:
        test=frame.dataset.eq(study).to_numpy();job('held_assay',study,~test,test,PRIMARY)
    # Primary comparison complete before separate fixed secondary models.
    for study in STUDIES:
        test=frame.dataset.eq(study).to_numpy();job('held_assay',study,~test,test,SECONDARY)
    dec=pd.DataFrame(all_dec);csvsave(OUT/'decision_metrics.csv',dec,True);csvsave(ART/'model_comparison.csv',summarize(dec));csvsave(ART/'candidate_rankings.csv',pd.DataFrame(rank),True);csvsave(ART/'pairwise_probabilities.csv',pd.DataFrame(probrows),True);csvsave(ART/'calibration.csv',pd.DataFrame(cals));csvsave(OUT/'reliability_bins.csv',pd.DataFrame(bins));csvsave(OUT/'predictions.csv',pd.DataFrame(pred),True);csvsave(OUT/'matched_raw_replicate_decisions.csv',pd.DataFrame(raw),True)
    if pol:csvsave(OUT/'conditional_policy_decisions.csv',pd.DataFrame(pol))
    jsave(OUT/'fold_manifest.json',folds);jsave(OUT/'historical_H0_replay.json',replays);jsave(OUT/'run_complete.json',{'status':'PASS','fits':len(list((OUT/'fits').glob('*.json'))),'fold_jobs':len(folds),'candidate_rank_rows':len(rank),'probability_rows':len(probrows),'decision_rows':len(dec),'raw_replicate_decisions':len(raw),'new_independent_data':False,'primary_models':PRIMARY,'secondary_models':SECONDARY})
    print('All prespecified comparisons complete. Gate pending.',flush=True)
if __name__=='__main__':run()
